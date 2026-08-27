param(
    [Parameter(Mandatory=$true)][string]$CertificatePath,
    [Parameter(Mandatory=$true)][string]$CertificatePassword,
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [string]$Executable = (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "dist\Orville-Signal-Room.exe")
)
$ErrorActionPreference = "Stop"
$signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
if (-not $signtool) { throw "signtool.exe was not found. Install the Windows SDK or provide signtool.exe on PATH." }
if (-not (Test-Path $CertificatePath)) { throw "Certificate file not found: $CertificatePath" }
if (-not (Test-Path $Executable)) { throw "Executable not found: $Executable" }
& $signtool.Source sign /fd SHA256 /f $CertificatePath /p $CertificatePassword /tr $TimestampUrl /td SHA256 $Executable
if ($LASTEXITCODE -ne 0) { throw "signtool failed with exit code $LASTEXITCODE" }
& $signtool.Source verify /pa /all $Executable
if ($LASTEXITCODE -ne 0) { throw "Signature verification failed." }
Write-Output "Signed and verified: $Executable"
