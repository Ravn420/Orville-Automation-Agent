$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $line.Substring('ORVILLE_API_TOKEN='.Length).Trim()
$headers = @{ Authorization = "Bearer $token" }
$result = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8787/api/v1/providers' -Headers $headers
$result | ConvertTo-Json -Depth 10
