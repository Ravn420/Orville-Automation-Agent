$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $line.Substring('ORVILLE_API_TOKEN='.Length).Trim()
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Method Delete -Uri 'http://127.0.0.1:8787/api/v1/providers/mock-local' -Headers $headers | Out-Null
$lines = netstat -ano | Select-String ':11435' | Select-String 'LISTENING'
foreach ($line in $lines) {
  $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
  $listenerPid = [int]$parts[-1]
  if ($listenerPid -gt 0) { Stop-Process -Id $listenerPid -Force -ErrorAction SilentlyContinue }
}
Write-Output 'MOCK_PROVIDER_CLEANED'
