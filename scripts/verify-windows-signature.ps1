param([Parameter(Mandatory=$true)][string]$Artifact, [Parameter(Mandatory=$true)][string]$Thumbprint, [switch]$SelfSignedPreview)
$ErrorActionPreference = 'Stop'
$Signature = Get-AuthenticodeSignature -LiteralPath $Artifact
if ($null -eq $Signature.SignerCertificate) { throw 'Windows signature has no signer certificate' }
if ($Signature.SignerCertificate.Thumbprint -ne $Thumbprint) { throw 'Unexpected Windows publisher certificate' }
if (-not $SelfSignedPreview) {
    if ($Signature.Status -ne 'Valid') { throw 'Windows signature is not trusted' }
    if ($null -eq $Signature.TimeStamperCertificate) { throw 'Windows signature has no trusted timestamp' }
    Write-Output 'Authenticode publisher and timestamp verified'
    exit 0
}

# This is a native build-runner verification step, never an installer action.
# WinVerifyTrust must check the PE digest, not just expose a matching certificate.
# Temporarily trust exactly the pinned self-signed leaf and always remove our
# insertion. Existing certificates are left intact. Run on an isolated worker.
if ($env:GCHAT_ISOLATED_SIGNING_WORKER -ne '1') { throw 'Self-signed verification requires an isolated signing worker' }
if ($Signature.SignerCertificate.Subject -ne $Signature.SignerCertificate.Issuer) { throw 'Preview certificate is not self-issued' }
$RootPath = 'Cert:\CurrentUser\Root\' + $Thumbprint
$Existing = Test-Path -LiteralPath $RootPath
$Store = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root', 'CurrentUser')
try {
    $Store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
    if (-not $Existing) { $Store.Add($Signature.SignerCertificate) }
    $Verified = Get-AuthenticodeSignature -LiteralPath $Artifact
    if ($Verified.Status -ne 'Valid' -or $Verified.SignerCertificate.Thumbprint -ne $Thumbprint) {
        throw 'Self-signed Authenticode integrity verification failed'
    }
    Write-Output 'Authenticode integrity verified against pinned preview certificate; public trust is not established'
} finally {
    if (-not $Existing) { $Store.Remove($Signature.SignerCertificate) }
    $Store.Close()
}
