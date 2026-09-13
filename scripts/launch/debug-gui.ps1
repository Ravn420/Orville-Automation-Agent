$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Remove-Item gui-debug-out.log,gui-debug-err.log -Force -ErrorAction SilentlyContinue
$p = Start-Process -FilePath 'python' -ArgumentList 'windows_gui.py' -WorkingDirectory (Get-Location) -RedirectStandardOutput 'gui-debug-out.log' -RedirectStandardError 'gui-debug-err.log' -PassThru
Start-Sleep -Seconds 8
Write-Output "PROCESS_ID=$($p.Id)"
Get-Process -Id $p.Id -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Responding,MainWindowTitle
Write-Output '=== ERROR ==='
Get-Content gui-debug-err.log -ErrorAction SilentlyContinue
Write-Output '=== OUT ==='
Get-Content gui-debug-out.log -ErrorAction SilentlyContinue
Write-Output '=== PORT ==='
Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
