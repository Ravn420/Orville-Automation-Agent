$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Output '=== COMPOSE STATUS ==='
docker compose ps
Write-Output '=== PORT OWNERS ==='
Get-NetTCPConnection -LocalPort 80,443,8787 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess
Write-Output '=== PROCESS NAMES ==='
Get-Process -Id (Get-NetTCPConnection -LocalPort 80,443,8787 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique) -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Path
Write-Output '=== HTTP ==='
& curl.exe -I -sS -w "HTTP_STATUS=%{http_code}`n" http://localhost/
Write-Output '=== HTTPS ==='
& curl.exe -k -I -sS -w "HTTPS_STATUS=%{http_code}`n" https://localhost/
Write-Output '=== AUTH HEALTH ==='
$line = Get-Content -LiteralPath '.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' } | Select-Object -First 1
$token = ($line -split '=', 2)[1]
& curl.exe -k -sS -w "`nHEALTH_STATUS=%{http_code}`n" -H "Authorization: Bearer $token" https://localhost/api/v1/health
Write-Output '=== LOGS ==='
docker compose logs --no-color --tail=80 api proxy
