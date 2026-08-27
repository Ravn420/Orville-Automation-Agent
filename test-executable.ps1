$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content -LiteralPath '.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' } | Select-Object -First 1
$token = ($line -split '=', 2)[1]
$port = 8787
Get-Process -Name Orville -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($existing) { throw "Port $port is already in use; stop other local API instances before executable test." }
$executable = Join-Path (Get-Location) 'dist\Orville-Signal-Room.exe'
if (-not (Test-Path -LiteralPath $executable)) { throw "Executable not found: $executable" }
$previousToken = $env:ORVILLE_API_TOKEN
$env:ORVILLE_API_TOKEN = $token
$proc = Start-Process -FilePath $executable -WorkingDirectory (Join-Path (Get-Location) 'dist') -PassThru
try {
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/docs" -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ready = $true; break } } catch {}
    }
    if (-not $ready) { throw 'Executable did not expose /docs within 30 seconds.' }
    $unauth = & curl.exe -sS -o NUL -w '%{http_code}' "http://127.0.0.1:$port/api/v1/health"
    $auth = & curl.exe -sS -o NUL -w '%{http_code}' -H "Authorization: Bearer $token" "http://127.0.0.1:$port/api/v1/health"
    $openapi = & curl.exe -sS -o NUL -w '%{http_code}' "http://127.0.0.1:$port/openapi.json"
    Write-Output "DOCS_STATUS=200"
    Write-Output "OPENAPI_STATUS=$openapi"
    Write-Output "UNAUTH_HEALTH_STATUS=$unauth"
    Write-Output "AUTH_HEALTH_STATUS=$auth"
    if ($openapi -ne '200' -or $unauth -ne '401' -or $auth -ne '200') { throw 'Executable integration checks failed.' }
}
finally {
    if (-not $proc.HasExited) { & taskkill.exe /PID $proc.Id /T /F | Out-Null }
    $env:ORVILLE_API_TOKEN = $previousToken
}
