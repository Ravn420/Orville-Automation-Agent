$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$lines = netstat -ano | Select-String ':8787' | Select-String 'LISTENING'
foreach ($line in $lines) {
  $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
  $listenerPid = [int]$parts[-1]
  if ($listenerPid -gt 0) { Stop-Process -Id $listenerPid -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Seconds 2
$proc = Start-Process -FilePath 'python' -ArgumentList 'windows_launcher.py' -WorkingDirectory (Get-Location) -PassThru
Start-Sleep -Seconds 5
$running = -not $proc.HasExited
Write-Output "API_PROCESS_ID=$($proc.Id)"
Write-Output "API_PROCESS_RUNNING=$running"
