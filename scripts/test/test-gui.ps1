$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Get-Process -Name 'Orville','Orville-GUI' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$proc = Start-Process -FilePath '.\dist\Orville-GUI.exe' -WorkingDirectory (Join-Path (Get-Location) 'dist') -PassThru
try {
    $live = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if (-not $live) { throw 'GUI process exited before verification.' }
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        $probe = & curl.exe -sS -o NUL -w '%{http_code}' http://127.0.0.1:8787/docs 2>$null
        if ($probe -eq '200') { $ready = $true; break }
    }
    if (-not $ready) { throw 'GUI backend did not expose /docs within 30 seconds.' }
    Write-Output "PROCESS_ID=$($live.Id)"
    Write-Output "RESPONDING=$($live.Responding)"
    Write-Output "WINDOW_TITLE=$($live.MainWindowTitle)"
    $docs = & curl.exe -sS -o NUL -w '%{http_code}' http://127.0.0.1:8787/docs
    $unauth = & curl.exe -sS -o NUL -w '%{http_code}' http://127.0.0.1:8787/api/v1/health
    Write-Output "DOCS_STATUS=$docs"
    Write-Output "UNAUTH_HEALTH_STATUS=$unauth"
    if ($docs -ne '200' -or $unauth -ne '401') { throw 'GUI backend checks failed.' }
}
finally {
    if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) { & taskkill.exe /PID $proc.Id /T /F | Out-Null }
}
