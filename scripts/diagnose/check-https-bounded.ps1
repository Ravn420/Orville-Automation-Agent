$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $line.Substring('ORVILLE_API_TOKEN='.Length)
$code = & curl.exe --max-time 10 -k -sS -o NUL -w '%{http_code}' -H "Authorization: Bearer $token" https://127.0.0.1/api/v1/health 2>$null
Write-Output "HTTPS_HEALTH=$code"
