$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Remove-Item '.\exe-out.log','.\exe-err.log' -Force -ErrorAction SilentlyContinue
$proc = Start-Process -FilePath '.\dist\Orville.exe' -WorkingDirectory (Get-Location) -RedirectStandardOutput '.\exe-out.log' -RedirectStandardError '.\exe-err.log' -PassThru
Start-Sleep -Seconds 8
Write-Output "PID=$($proc.Id)"
Write-Output "HAS_EXITED=$($proc.HasExited)"
if ($proc.HasExited) { Write-Output "EXIT_CODE=$($proc.ExitCode)" }
Write-Output '=== OUT ==='
Get-Content '.\exe-out.log' -ErrorAction SilentlyContinue
Write-Output '=== ERR ==='
Get-Content '.\exe-err.log' -ErrorAction SilentlyContinue
Write-Output '=== PORT ==='
Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue
if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
