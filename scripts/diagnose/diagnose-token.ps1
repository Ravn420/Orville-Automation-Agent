$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $line.Substring('ORVILLE_API_TOKEN='.Length).Trim()
$sha = [System.Security.Cryptography.SHA256]::Create()
$hash = (($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($token)) | ForEach-Object { $_.ToString('x2') }) -join '')
$code = & curl.exe --max-time 10 -sS -o NUL -w '%{http_code}' -H "Authorization: Bearer $token" http://127.0.0.1:8787/api/v1/health 2>$null
Write-Output "TOKEN_LENGTH=$($token.Length)"
Write-Output "TOKEN_SHA256=$hash"
Write-Output "CONFIGURED_TOKEN_HEALTH=$code"
