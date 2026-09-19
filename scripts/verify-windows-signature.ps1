param([Parameter(Mandatory=$true)][string]$Artifact, [Parameter(Mandatory=$true)][string]$Thumbprint)
$ErrorActionPreference = 'Stop'
$Signature = Get-AuthenticodeSignature -LiteralPath $Artifact
if ($Signature.Status -ne 'Valid') { throw 'Windows signature is not trusted' }
if ($Signature.SignerCertificate.Thumbprint -ne $Thumbprint) { throw 'Unexpected Windows publisher certificate' }
if ($null -eq $Signature.TimeStamperCertificate) { throw 'Windows signature has no trusted timestamp' }
Write-Output 'Authenticode publisher and timestamp verified'
