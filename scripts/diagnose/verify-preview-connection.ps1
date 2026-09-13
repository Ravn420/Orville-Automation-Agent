$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Get-Process -Name 'Orville-GUI','Orville','python' -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*Orville*' -or $_.ProcessName -eq 'Orville-GUI' } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$envLines = Get-Content '.\.env.production'
$tokenLine = $envLines | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $tokenLine.Substring('ORVILLE_API_TOKEN='.Length)
$proc = Start-Process -FilePath 'python' -ArgumentList 'windows_launcher.py' -WorkingDirectory (Get-Location) -PassThru
try {
  $ready = $false
  for ($i=0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    $code = & curl.exe -sS -o NUL -w '%{http_code}' -H "Authorization: Bearer $token" http://127.0.0.1:8787/api/v1/health 2>$null
    if ($code -eq '200') { $ready = $true; break }
  }
  Write-Output "API_READY=$ready"
  $headers = & curl.exe -sS -D - -o NUL -X OPTIONS http://127.0.0.1:8787/api/v1/health -H 'Origin: https://3000-ipbwyvn1om9kapfum1vzf-e1ebbe7e.sg1.manus.computer' -H 'Access-Control-Request-Method: GET' -H 'Access-Control-Request-Headers: authorization,content-type'
  Write-Output '=== CORS HEADERS ==='
  $headers | Select-String -Pattern 'access-control-allow-origin|access-control-allow-methods|access-control-allow-headers' -CaseSensitive:$false
  Write-Output '=== HEALTH ==='
  curl.exe -sS -H "Authorization: Bearer $token" http://127.0.0.1:8787/api/v1/health
} finally {
  if ($proc -and (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
