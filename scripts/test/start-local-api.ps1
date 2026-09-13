$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Get-Process -Name 'Orville-GUI','Orville' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
$old = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*Orville*' }
$old | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
$proc = Start-Process -FilePath 'python' -ArgumentList 'windows_launcher.py' -WorkingDirectory (Get-Location) -PassThru
Start-Sleep -Seconds 4
Write-Output "API_PROCESS_ID=$($proc.Id)"
Write-Output "API_PROCESS_RUNNING=$(-not $proc.HasExited)"
