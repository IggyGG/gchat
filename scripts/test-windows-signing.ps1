# Native import regression; disposable PFX only, never release key material.
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:GCHAT_ISOLATED_SIGNING_WORKER -ne '1') {
    throw 'Signing import fixture requires the isolated release worker'
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Use a fresh fixture output directory' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$Temporary = Join-Path $env:RUNNER_TEMP ('gchat-signing-fixture-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Temporary | Out-Null
$Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
& icacls.exe $Temporary /inheritance:r /grant:r ('*' + $Sid + ':(OI)(CI)F') | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not restrict fixture key directory' }
$Helper = Join-Path $PSScriptRoot 'windows-signing.ps1'
$Publication = Join-Path $Temporary 'publication.json'
$PreviousBase64 = $env:WINDOWS_CERTIFICATE_BASE64
$PreviousPassword = $env:WINDOWS_CERTIFICATE_PASSWORD
$Password = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
$SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$Pin = $null
$Report = [ordered]@{ schema=1; scope='disposable_pfx_import_cleanup'; passed=$false;
    release_qualified=$false; checks=[ordered]@{};
    helper_sha256=(Get-FileHash -LiteralPath $Helper -Algorithm SHA256).Hash.ToLowerInvariant() }
function Store-Inventory {
    return @(Get-ChildItem Cert:\CurrentUser\My, Cert:\CurrentUser\Root, Cert:\LocalMachine\Root,
        Cert:\CurrentUser\TrustedPublisher, Cert:\LocalMachine\TrustedPublisher |
        ForEach-Object { $_.PSParentPath + '/' + $_.Thumbprint } | Sort-Object)
}
$Before = Store-Inventory
function Invoke-Helper([string]$Action, [string]$Case) {
    $ErrorActionPreference = 'Continue'
    $State = Join-Path $OutputDirectory $Case
    $Output = (& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File $Helper `
        -Action $Action -StateDirectory $State -Publication $Publication 2>&1 | Out-String)
    $Code = $LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $OutputDirectory ($Case + '-' + $Action + '.log')), $Output)
    return $Code
}
function Assert-Clean([string]$Case, [bool]$Imported) {
    $Cleanup = Get-Content -Raw (Join-Path (Join-Path $OutputDirectory $Case) 'cleanup.json') | ConvertFrom-Json
    if ($Cleanup.imported -ne $Imported -or -not $Cleanup.private_key_removed -or
        -not $Cleanup.pfx_removed -or -not $Cleanup.my_store_restored -or
        -not $Cleanup.persistent_trust_stores_unchanged) { throw "Incomplete cleanup: $Case" }
}
try {
    $Certificate = New-SelfSignedCertificate -Type CodeSigningCert -Subject ('CN=GChat import fixture ' + [Guid]::NewGuid().ToString('N')) `
        -CertStoreLocation Cert:\CurrentUser\My -KeyAlgorithm RSA -KeyLength 2048 -HashAlgorithm SHA256 `
        -KeyExportPolicy Exportable -NotBefore (Get-Date).AddMinutes(-5) -NotAfter (Get-Date).AddHours(1)
    $Pin = $Certificate.Thumbprint
    $LeafSha = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($Certificate.RawData)).Replace('-', '').ToLowerInvariant()
    $Pfx = Join-Path $Temporary 'fixture.pfx'
    Export-PfxCertificate -Cert $Certificate -FilePath $Pfx -Password $SecurePassword -CryptoAlgorithmOption AES256_SHA256 | Out-Null
    $env:WINDOWS_CERTIFICATE_BASE64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($Pfx))
    $env:WINDOWS_CERTIFICATE_PASSWORD = $Password
    Remove-Item -LiteralPath ('Cert:\CurrentUser\My\' + $Pin) -DeleteKey -Force
    Remove-Item -LiteralPath $Pfx -Force
    $Config = @{ signing_policy='self-signed'; publisher_identities=@{ windows=@{
        certificate_fingerprint=$Pin; certificate_sha256=$LeafSha } } }
    [IO.File]::WriteAllText($Publication, ($Config | ConvertTo-Json -Depth 6))

    $ImportCode = Invoke-Helper 'Import' 'valid'
    $CleanupCode = Invoke-Helper 'Cleanup' 'valid'
    if ($ImportCode -ne 0 -or $CleanupCode -ne 0) { throw 'Valid disposable PFX import/cleanup failed; inspect retained fixture logs' }
    Assert-Clean 'valid' $true
    $Report.checks.valid_password_import_and_cleanup = $true

    $env:WINDOWS_CERTIFICATE_PASSWORD = 'deliberately-wrong-fixture-password'
    if ((Invoke-Helper 'Import' 'wrong-password') -eq 0) { throw 'Wrong PFX password was accepted' }
    $null = Invoke-Helper 'Cleanup' 'wrong-password'
    Assert-Clean 'wrong-password' $false
    $Report.checks.wrong_password_refused_without_store_change = $true

    $env:WINDOWS_CERTIFICATE_PASSWORD = $Password
    $Config.publisher_identities.windows.certificate_fingerprint = '0' * 40
    [IO.File]::WriteAllText($Publication, ($Config | ConvertTo-Json -Depth 6))
    if ((Invoke-Helper 'Import' 'wrong-pin') -eq 0) { throw 'Wrong certificate pin was accepted' }
    $null = Invoke-Helper 'Cleanup' 'wrong-pin'
    Assert-Clean 'wrong-pin' $false
    $Report.checks.wrong_pin_refused_without_store_change = $true
    $Report.passed = $true
} catch {
    $Report.error = $_.Exception.Message
} finally {
    if ($Pin -and (Test-Path ('Cert:\CurrentUser\My\' + $Pin))) {
        Remove-Item -LiteralPath ('Cert:\CurrentUser\My\' + $Pin) -DeleteKey -Force
    }
    $env:WINDOWS_CERTIFICATE_BASE64 = $PreviousBase64
    $env:WINDOWS_CERTIFICATE_PASSWORD = $PreviousPassword
    $SecurePassword.Dispose()
    Remove-Item -LiteralPath $Temporary -Recurse -Force
    $Report.checks.temporary_material_removed = -not (Test-Path -LiteralPath $Temporary)
    $Report.checks.certificate_stores_restored = ((Store-Inventory) -join ',') -eq ($Before -join ',')
    if (-not $Report.checks.temporary_material_removed -or -not $Report.checks.certificate_stores_restored) { $Report.passed = $false }
    [IO.File]::WriteAllText((Join-Path $OutputDirectory 'report.json'), ($Report | ConvertTo-Json -Depth 6))
}
if (-not $Report.passed) { throw 'Disposable signer import fixture failed; retain report.json' }
Write-Output 'Disposable PFX import, wrong-password/pin refusal and store cleanup passed'
exit 0
