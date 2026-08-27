$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$token = ((Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }) -replace '^ORVILLE_API_TOKEN=', '').Trim()
$base = 'http://127.0.0.1:8787'
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
$types = @('openai','openrouter','groq','together','deepseek','mistral','xai','perplexity','anthropic','stable-horde','openai-compatible-local')
$registered = @()
foreach ($type in $types) {
  $id = "coverage-$type"
  $payload = @{ provider_id=$id; provider_type=$type; model='test-model'; base_url= if ($type -eq 'stable-horde') { 'https://stablehorde.net/api' } elseif ($type -eq 'openai-compatible-local') { 'http://127.0.0.1:8000/v1' } elseif ($type -eq 'anthropic') { 'https://api.anthropic.com/v1' } else { 'https://api.example.com/v1' }; api_key='not-real'; capabilities=@('text','code','streaming'); headers=@{'X-Test-Route'='orville'} }
  $result = Invoke-RestMethod -Method Post -Uri "$base/api/v1/providers" -Headers $headers -Body ($payload | ConvertTo-Json)
  $registered += $result.provider
}
$list = Invoke-RestMethod -Method Get -Uri "$base/api/v1/providers" -Headers $headers
foreach ($provider in $registered) { Invoke-RestMethod -Method Delete -Uri "$base/api/v1/providers/$($provider.provider_id)" -Headers $headers | Out-Null }
Write-Output "REGISTERED_COUNT=$($registered.Count)"
Write-Output "STABLE_HORDE_TYPE=$($registered | Where-Object { $_.provider_id -eq 'coverage-stable-horde' } | Select-Object -ExpandProperty provider_type)"
Write-Output "ANTHROPIC_TYPE=$($registered | Where-Object { $_.provider_id -eq 'coverage-anthropic' } | Select-Object -ExpandProperty provider_type)"
Write-Output "CUSTOM_HEADER_REDACTED=$([bool](($registered | Where-Object { $_.provider_id -eq 'coverage-openrouter' }).custom_headers -contains 'X-Test-Route'))"
Write-Output "API_KEY_NOT_RETURNED=$([bool](-not (($registered | ConvertTo-Json) -match 'not-real')))"
if ($registered.Count -ne $types.Count) { throw 'Expanded provider registration count mismatch' }
