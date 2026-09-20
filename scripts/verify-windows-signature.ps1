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
# WinVerifyTrust checks the PE digest and signature using process-local trust.
# No persistent trust store is changed, including on headless signing workers.
if ($env:GCHAT_ISOLATED_SIGNING_WORKER -ne '1') { throw 'Self-signed verification requires an isolated signing worker' }
if ($Signature.SignerCertificate.Subject -ne $Signature.SignerCertificate.Issuer) { throw 'Preview certificate is not self-issued' }
if ($null -ne $Signature.TimeStamperCertificate) { throw 'Preview verification requires an untimestamped signature' }
Add-Type -Path (Join-Path $PSScriptRoot 'PreviewAuthenticode.cs')
[PreviewAuthenticode]::Verify((Resolve-Path -LiteralPath $Artifact).ProviderPath, $Signature.SignerCertificate)
Write-Output 'Authenticode integrity verified against pinned preview certificate; public trust is not established'
