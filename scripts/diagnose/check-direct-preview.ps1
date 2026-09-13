$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $line.Substring('ORVILLE_API_TOKEN='.Length)
$health = & curl.exe --max-time 10 -sS -o NUL -w '%{http_code}' -H "Authorization: Bearer $token" http://127.0.0.1:8787/api/v1/health 2>$null
Write-Output "DIRECT_HEALTH=$health"
$headers = & curl.exe --max-time 10 -sS -D - -o NUL -X OPTIONS http://127.0.0.1:8787/api/v1/health -H 'Origin: https://3000-ipbwyvn1om9kapfum1vzf-e1ebbe7e.sg1.manus.computer' -H 'Access-Control-Request-Method: GET' -H 'Access-Control-Request-Headers: authorization,content-type' 2>$null
$headers | Select-String -Pattern 'access-control-allow-origin|access-control-allow-methods|access-control-allow-headers' -CaseSensitive:$false
