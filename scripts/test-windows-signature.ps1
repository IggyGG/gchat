# Native regression check; generates disposable test keys, never release keys.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Directory = Join-Path ([IO.Path]::GetTempPath()) ('gchat-signature-test-' + [Guid]::NewGuid().ToString('N'))
$Certificates = @()
$PreviousWorker = $env:GCHAT_ISOLATED_SIGNING_WORKER
$Report = [ordered]@{ kind='native_signing_verifier_fixture'; release_qualified=$false; passed=$false; checks=@{} }
$RootsBefore = @(Get-ChildItem Cert:\CurrentUser\Root, Cert:\LocalMachine\Root | ForEach-Object { $_.Thumbprint } | Sort-Object)

function Verify-Artifact([string]$Artifact, [string]$Pin, [bool]$Preview = $true) {
    $ErrorActionPreference = 'Continue'
    $Arguments = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'RemoteSigned', '-File',
        (Join-Path $PSScriptRoot 'verify-windows-signature.ps1'), '-Artifact', $Artifact, '-Thumbprint', $Pin)
    if ($Preview) { $Arguments += '-SelfSignedPreview' }
    $Output = (& powershell.exe @Arguments 2>&1 | Out-String)
    return @{code=$LASTEXITCODE; output=$Output}
}

try {
    New-Item -ItemType Directory -Path $Directory | Out-Null
    $Source = Join-Path $Directory 'unsigned.exe'
    Add-Type -TypeDefinition 'public class PreviewSignatureFixture { public static void Main() {} }' -OutputAssembly $Source -OutputType ConsoleApplication
    $Certificate = New-SelfSignedCertificate -Type CodeSigningCert -Subject ('CN=GChat temporary verifier test ' + [Guid]::NewGuid().ToString('N')) -CertStoreLocation Cert:\CurrentUser\My -KeyAlgorithm RSA -KeyLength 2048 -HashAlgorithm SHA256 -KeyExportPolicy NonExportable -NotBefore (Get-Date).AddMinutes(-5) -NotAfter (Get-Date).AddHours(1)
    $Certificates += $Certificate
    $Artifact = Join-Path $Directory 'signed.exe'
    Copy-Item -LiteralPath $Source -Destination $Artifact
    $Signed = Set-AuthenticodeSignature -LiteralPath $Artifact -Certificate $Certificate -HashAlgorithm SHA256
    if ($Signed.SignerCertificate.Thumbprint -ne $Certificate.Thumbprint) { throw 'Test PE signing failed' }
    $env:GCHAT_ISOLATED_SIGNING_WORKER = '1'
    $Result = Verify-Artifact $Artifact $Certificate.Thumbprint
    if ($Result.code -ne 0) { throw ('Valid pinned signature rejected: ' + $Result.output) }
    $Report.checks.valid_pinned_signature = $true

    $Changed = Join-Path $Directory 'changed.exe'
    $Bytes = [IO.File]::ReadAllBytes($Artifact)
    $Bytes[64] = $Bytes[64] -bxor 1
    [IO.File]::WriteAllBytes($Changed, $Bytes)
    $Result = Verify-Artifact $Changed $Certificate.Thumbprint
    if ($Result.code -eq 0 -or $Result.output -notmatch 'Pinned Authenticode verification failed') { throw 'Modified PE did not fail native integrity verification' }
    $Report.checks.modified_pe_rejected = $true

    $Result = Verify-Artifact $Artifact ('0' * 40)
    if ($Result.code -eq 0 -or $Result.output -notmatch 'Unexpected Windows publisher certificate') { throw 'Wrong certificate pin did not fail' }
    $Report.checks.wrong_pin_rejected = $true
    $Result = Verify-Artifact $Source $Certificate.Thumbprint
    if ($Result.code -eq 0 -or $Result.output -notmatch 'no signer certificate') { throw 'Unsigned PE did not fail' }
    $Report.checks.unsigned_pe_rejected = $true
    $Result = Verify-Artifact $Artifact $Certificate.Thumbprint $false
    if ($Result.code -eq 0 -or $Result.output -notmatch 'not trusted') { throw 'Preview signature accepted as publicly trusted' }
    $Report.checks.public_trust_not_claimed = $true

    $env:GCHAT_ISOLATED_SIGNING_WORKER = '0'
    $Result = Verify-Artifact $Artifact $Certificate.Thumbprint
    if ($Result.code -eq 0 -or $Result.output -notmatch 'isolated signing worker') { throw 'Nonisolated worker did not fail' }
    $Report.checks.isolated_worker_required = $true
    $env:GCHAT_ISOLATED_SIGNING_WORKER = '1'

    # Windows refuses to sign with an already expired certificate. Sign while
    # valid, then wait for expiry without changing the worker's clock.
    $Expired = New-SelfSignedCertificate -Type CodeSigningCert -Subject ('CN=GChat expired verifier test ' + [Guid]::NewGuid().ToString('N')) -CertStoreLocation Cert:\CurrentUser\My -KeyAlgorithm RSA -KeyLength 2048 -HashAlgorithm SHA256 -KeyExportPolicy NonExportable -NotBefore (Get-Date).AddMinutes(-5) -NotAfter (Get-Date).AddSeconds(30)
    $Certificates += $Expired
    $ExpiredArtifact = Join-Path $Directory 'expired.exe'
    Copy-Item -LiteralPath $Source -Destination $ExpiredArtifact
    $Signed = Set-AuthenticodeSignature -LiteralPath $ExpiredArtifact -Certificate $Expired -HashAlgorithm SHA256
    if ($Signed.SignerCertificate.Thumbprint -ne $Expired.Thumbprint) { throw 'Expired test PE was not signed' }
    $Result = Verify-Artifact $ExpiredArtifact $Expired.Thumbprint
    if ($Result.code -ne 0) { throw 'Short-lived signer was not valid before expiry' }
    $WaitSeconds = [Math]::Ceiling(($Expired.NotAfter - (Get-Date)).TotalSeconds) + 1
    if ($WaitSeconds -gt 0) { Start-Sleep -Seconds $WaitSeconds }
    $Result = Verify-Artifact $ExpiredArtifact $Expired.Thumbprint
    if ($Result.code -eq 0 -or $Result.output -notmatch 'Pinned Authenticode verification failed') { throw 'Expired pinned signer did not fail' }
    $Report.checks.expired_signer_rejected = $true
    $Report.passed = $true
} catch {
    $Report.error = $_.Exception.Message
} finally {
    foreach ($Certificate in $Certificates) {
        Remove-Item -LiteralPath ('Cert:\CurrentUser\My\' + $Certificate.Thumbprint) -DeleteKey -Force
    }
    $Report.checks.test_private_keys_removed = @($Certificates | Where-Object { Test-Path ('Cert:\CurrentUser\My\' + $_.Thumbprint) }).Count -eq 0
    $RootsAfter = @(Get-ChildItem Cert:\CurrentUser\Root, Cert:\LocalMachine\Root | ForEach-Object { $_.Thumbprint } | Sort-Object)
    $Report.checks.persistent_trust_stores_unchanged = ($RootsBefore -join ',') -eq ($RootsAfter -join ',')
    if (-not $Report.checks.test_private_keys_removed -or -not $Report.checks.persistent_trust_stores_unchanged) { $Report.passed = $false }
    $env:GCHAT_ISOLATED_SIGNING_WORKER = $PreviousWorker
    if (Test-Path -LiteralPath $Directory) { Remove-Item -LiteralPath $Directory -Recurse -Force }
    $Report.verifier_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'verify-windows-signature.ps1') -Algorithm SHA256).Hash.ToLower()
    $Report.native_verifier_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'PreviewAuthenticode.cs') -Algorithm SHA256).Hash.ToLower()
    $Report | ConvertTo-Json -Depth 4
}
if (-not $Report.passed) { exit 1 }
