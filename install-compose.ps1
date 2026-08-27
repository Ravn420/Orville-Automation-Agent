$ErrorActionPreference = 'Stop'
$dir = Join-Path $env:USERPROFILE '.docker\cli-plugins'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$target = Join-Path $dir 'docker-compose.exe'
$url = 'https://github.com/docker/compose/releases/download/v5.5.0/docker-compose-windows-x86_64.exe'
Invoke-WebRequest -Uri $url -OutFile $target
Write-Output "Installed $target"
