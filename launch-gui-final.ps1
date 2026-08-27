$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Get-Process -Name 'Orville-GUI','Orville' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
$proc = Start-Process -FilePath '.\dist\Orville-GUI.exe' -WorkingDirectory (Join-Path (Get-Location) 'dist') -PassThru
$code = '000'
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    $code = & curl.exe -sS -o NUL -w '%{http_code}' http://127.0.0.1:8787/docs 2>$null
    if ($code -eq '200') { break }
}
Write-Output "GUI_PROCESS_ID=$($proc.Id)"
Write-Output "GUI_PROCESS_RESPONDING=$((Get-Process -Id $proc.Id).Responding)"
Write-Output "DOCS_STATUS=$code"
Write-Output "GUI_LEFT_RUNNING=$(-not $proc.HasExited)"
