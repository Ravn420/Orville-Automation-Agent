Start-Sleep -Seconds 20
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Output '=== DOCKER SERVER ==='
& docker version --format '{{.Server.Version}}'
Write-Output '=== HTTPS ==='
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path (Get-Location) 'check-https-bounded.ps1')
