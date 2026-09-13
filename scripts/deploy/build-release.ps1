param(
    [string]$Version = "0.1.0",
    [switch]$PortableOnly
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dist = Join-Path $root "dist"
$release = Join-Path $root "release"
$portable = Join-Path $release "Orville-Portable-$Version"
if (-not (Test-Path (Join-Path $dist "Orville-Signal-Room.exe"))) { throw "Build dist\Orville-Signal-Room.exe first." }
Remove-Item -Recurse -Force $release -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $portable | Out-Null
New-Item -ItemType Directory -Path (Join-Path $portable "data") | Out-Null
Copy-Item -Recurse -Force (Join-Path $dist "*") $portable
if (Test-Path (Join-Path $root "browser_extension")) { Copy-Item -Recurse -Force (Join-Path $root "browser_extension") $portable }
foreach ($doc in @("CONNECTOR_BRIDGE.md", "ORVILLE_SIGNAL_ROOM_RUN.md", "RELEASE_HARDENING.md")) { if (Test-Path (Join-Path $root $doc)) { Copy-Item -Force (Join-Path $root $doc) $portable } }
New-Item -ItemType File -Path (Join-Path $portable "ORVILLE_PORTABLE_MODE.txt") | Out-Null
$portableEnv = Join-Path $portable "data\.env.production"
if (Test-Path $portableEnv) { Add-Content -Path $portableEnv -Value "ORVILLE_PORTABLE=1" -Encoding UTF8 } else { Set-Content -Path $portableEnv -Value "ORVILLE_PORTABLE=1" -Encoding UTF8 }
@"
Orville portable release $Version

Run Orville-Signal-Room.exe. User data is stored in this folder because portable mode is enabled by the launcher environment.
"@ | Set-Content (Join-Path $portable "PORTABLE-README.txt") -Encoding UTF8
$zip = Join-Path $release "Orville-Portable-$Version.zip"
Compress-Archive -Path (Join-Path $portable "*") -DestinationPath $zip -CompressionLevel Optimal
if (-not $PortableOnly) {
    Copy-Item (Join-Path $root "install-orville.ps1") $release
}
Write-Output "Portable archive: $zip"
if (-not $PortableOnly) { Write-Output "Installer script: $(Join-Path $release 'install-orville.ps1')" }
