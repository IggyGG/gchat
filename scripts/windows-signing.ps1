param(
    [Parameter(Mandatory=$true)][ValidateSet('Import', 'Cleanup')][string]$Action,
    [Parameter(Mandatory=$true)][string]$StateDirectory,
    [string]$Publication = (Join-Path $PSScriptRoot '../release/publication.json')
)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:GCHAT_ISOLATED_SIGNING_WORKER -ne '1') {
    throw 'Signing-key import is restricted to the isolated release worker'
}
$StateDirectory = [IO.Path]::GetFullPath($StateDirectory)
$StatePath = Join-Path $StateDirectory 'state.json'
function Write-Receipt([string]$Path, $Value) {
    [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
}
function File-Reference([string]$Path) {
    $Item = Get-Item -LiteralPath $Path
    return @{ path=$Item.FullName; size=$Item.Length;
        sha256=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$Harness = File-Reference $PSCommandPath
function My-Certificates {
    return @(Get-ChildItem Cert:\CurrentUser\My | ForEach-Object { $_.Thumbprint } | Sort-Object)
}
function Trust-Certificates {
    return @(Get-ChildItem Cert:\CurrentUser\Root, Cert:\LocalMachine\Root,
        Cert:\CurrentUser\TrustedPublisher, Cert:\LocalMachine\TrustedPublisher |
        ForEach-Object { $_.PSParentPath + '/' + $_.Thumbprint } | Sort-Object)
}
if ($Action -eq 'Cleanup') {
    if (-not (Test-Path -LiteralPath $StatePath)) { Write-Output 'No signing import was started'; exit 0 }
    $State = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
    $Result = [ordered]@{ schema=1; scope='isolated_current_user_signer_cleanup'; passed=$false;
        harness=$Harness;
        certificate_fingerprint=$State.certificate_fingerprint; imported=$State.imported;
        private_key_removed=$false; pfx_removed=$false; my_store_restored=$false;
        persistent_trust_stores_unchanged=$false }
    try {
        if ($State.import_permitted -and $State.certificate_fingerprint -notin $State.my_before) {
            $CertificatePath = 'Cert:\CurrentUser\My\' + $State.certificate_fingerprint
            if (Test-Path -LiteralPath $CertificatePath) {
                Remove-Item -LiteralPath $CertificatePath -DeleteKey -Force
            }
        }
        if ($State.pfx_path -and (Test-Path -LiteralPath $State.pfx_path)) {
            Remove-Item -LiteralPath $State.pfx_path -Force
        }
        $Result.private_key_removed = -not (Test-Path ('Cert:\CurrentUser\My\' + $State.certificate_fingerprint))
        $Result.pfx_removed = -not (Test-Path -LiteralPath $State.pfx_path)
        $Result.my_store_restored = ((My-Certificates) -join ',') -eq ($State.my_before -join ',')
        $Result.persistent_trust_stores_unchanged = ((Trust-Certificates) -join ',') -eq ($State.trust_before -join ',')
        $Result.passed = ($State.imported -and $Result.private_key_removed -and $Result.pfx_removed -and
                          $Result.my_store_restored -and $Result.persistent_trust_stores_unchanged)
    } catch {
        $Result.error = $_.Exception.Message
    } finally {
        Write-Receipt (Join-Path $StateDirectory 'cleanup.json') $Result
    }
    if (-not $Result.passed) { throw 'Signing-key cleanup did not pass; retain cleanup.json' }
    Write-Output 'Pinned private key removed; user certificate and persistent trust stores restored'
    exit 0
}
if (Test-Path -LiteralPath $StateDirectory) { throw 'Use a fresh signing-state directory' }
New-Item -ItemType Directory -Path $StateDirectory | Out-Null
$Config = Get-Content -Raw -LiteralPath $Publication | ConvertFrom-Json
if ($Config.signing_policy -notin @('self-signed', 'self-signed-preview')) {
    throw 'This worker currently implements only the configured pinned self-signed policy'
}
$Identity = $Config.publisher_identities.windows
$Pin = $Identity.certificate_fingerprint.Replace(' ', '').ToUpperInvariant()
if ($Pin -notmatch '^[A-F0-9]{40}$') { throw 'Publication has no SHA-1 Authenticode certificate pin' }
$MyBefore = My-Certificates
$KeyDirectory = Join-Path $env:RUNNER_TEMP ('gchat-pfx-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $KeyDirectory | Out-Null
$PfxPath = Join-Path $KeyDirectory 'signer.pfx'
$State = [ordered]@{ schema=1; certificate_fingerprint=$Pin; my_before=@($MyBefore);
    trust_before=@(Trust-Certificates); pfx_path=$PfxPath; import_permitted=$false; imported=$false }
Write-Receipt $StatePath $State
$Password = $null
$Collection = [Security.Cryptography.X509Certificates.X509Certificate2Collection]::new()
try {
    if ($Pin -in $MyBefore) { throw 'Pinned key already exists; refuse to take ownership of another key' }
    if (-not $env:WINDOWS_CERTIFICATE_BASE64 -or -not $env:WINDOWS_CERTIFICATE_PASSWORD) {
        throw 'Protected WINDOWS_CERTIFICATE_BASE64 and WINDOWS_CERTIFICATE_PASSWORD are required'
    }
    $Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    & icacls.exe $KeyDirectory /inheritance:r /grant:r ('*' + $Sid + ':(OI)(CI)F') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not restrict signing-key directory permissions' }
    [IO.File]::WriteAllBytes($PfxPath, [Convert]::FromBase64String($env:WINDOWS_CERTIFICATE_BASE64))
    $Password = ConvertTo-SecureString $env:WINDOWS_CERTIFICATE_PASSWORD -AsPlainText -Force
    $Collection.Import([IO.File]::ReadAllBytes($PfxPath), $Password,
        [Security.Cryptography.X509Certificates.X509KeyStorageFlags]::EphemeralKeySet)
    if ($Collection.Count -ne 1 -or -not $Collection[0].HasPrivateKey -or
        $Collection[0].Thumbprint -ne $Pin -or $Collection[0].Subject -ne $Collection[0].Issuer) {
        throw 'Protected PFX must contain only the existing pinned self-issued signing identity'
    }
    $LeafSha = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($Collection[0].RawData)).Replace('-', '').ToLowerInvariant()
    if ($Identity.certificate_sha256 -and $LeafSha -ne $Identity.certificate_sha256.ToLowerInvariant()) {
        throw 'Protected PFX leaf bytes differ from the publication SHA-256 pin'
    }
    if ($Collection[0].NotBefore -gt (Get-Date) -or $Collection[0].NotAfter -le (Get-Date)) {
        throw 'Pinned signing certificate is outside its validity period'
    }
    $State.import_permitted = $true
    Write-Receipt $StatePath $State
    $Imported = @(Import-PfxCertificate -FilePath $PfxPath -CertStoreLocation Cert:\CurrentUser\My -Password $Password)
    if ($Imported.Count -ne 1 -or $Imported[0].Thumbprint -ne $Pin -or -not $Imported[0].HasPrivateKey) {
        throw 'CurrentUser/My import did not return the exact pinned private identity'
    }
    $State.imported = $true
    Write-Receipt $StatePath $State
    Write-Receipt (Join-Path $StateDirectory 'import.json') ([ordered]@{
        schema=1; scope='isolated_current_user_signer_import'; passed=$true;
        harness=$Harness; publication=(File-Reference $Publication);
        certificate_fingerprint=$Pin; certificate_sha256=$LeafSha;
        store='CurrentUser/My'; persistent_trust_stores_unchanged=(((Trust-Certificates) -join ',') -eq ($State.trust_before -join ','))
    })
    [IO.File]::AppendAllText($env:GITHUB_ENV, 'WINDOWS_CERTIFICATE_THUMBPRINT=' + $Pin + "`n", [Text.UTF8Encoding]::new($false))
    Write-Output 'Existing pinned signing identity imported into CurrentUser/My'
} finally {
    foreach ($Certificate in $Collection) { $Certificate.Reset() }
    if ($null -ne $Password) { $Password.Dispose() }
    if (Test-Path -LiteralPath $PfxPath) { Remove-Item -LiteralPath $PfxPath -Force }
    if (Test-Path -LiteralPath $KeyDirectory) { Remove-Item -LiteralPath $KeyDirectory -Force }
}
