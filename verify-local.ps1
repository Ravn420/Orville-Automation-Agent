$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Start-Sleep -Seconds 5
docker compose ps
docker compose logs --no-color --tail=40 api proxy
$line = Get-Content -LiteralPath '.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' } | Select-Object -First 1
$token = ($line -split '=', 2)[1]
Write-Output '--- HEALTH ---'
& curl.exe -k -sS -w "`nHTTP_STATUS=%{http_code}`n" -H "Authorization: Bearer $token" https://localhost/api/v1/health
