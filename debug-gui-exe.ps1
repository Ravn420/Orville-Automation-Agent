$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Remove-Item gui-exe-out.log,gui-exe-err.log -Force -ErrorAction SilentlyContinue
$p = Start-Process -FilePath '.\dist\Orville-GUI-Debug.exe' -WorkingDirectory (Join-Path (Get-Location) 'dist') -RedirectStandardOutput (Join-Path (Get-Location) 'gui-exe-out.log') -RedirectStandardError (Join-Path (Get-Location) 'gui-exe-err.log') -PassThru
Start-Sleep -Seconds 8
Write-Output "PROCESS_ID=$($p.Id)"
Get-Process -Id $p.Id -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Responding,MainWindowTitle
Write-Output '=== ERROR ==='
Get-Content gui-exe-err.log -ErrorAction SilentlyContinue
Write-Output '=== OUT ==='
Get-Content gui-exe-out.log -ErrorAction SilentlyContinue
Write-Output '=== PORT ==='
Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
