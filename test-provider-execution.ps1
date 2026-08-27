$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $line.Substring('ORVILLE_API_TOKEN='.Length).Trim()
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
$base = 'http://127.0.0.1:8787'
$providerPayload = @{ provider_id='mock-local'; provider_type='openai-compatible-local'; model='mock-model'; base_url='http://127.0.0.1:11435/v1'; capabilities=@('text','code','structured_output','tool_calling') }
$provider = Invoke-RestMethod -Method Post -Uri "$base/api/v1/providers" -Headers $headers -Body ($providerPayload | ConvertTo-Json)
$objectivePayload = @{ objective='Verify provider-backed execution'; deliverables=@('Return a generated verification response'); acceptance_criteria=@('Mock provider verified'); risk_level='normal'; provider_id='mock-local'; environment=@{ target_environment='local' } }
$created = Invoke-RestMethod -Method Post -Uri "$base/api/v1/objectives" -Headers $headers -Body ($objectivePayload | ConvertTo-Json)
$executed = Invoke-RestMethod -Method Post -Uri "$base/api/v1/objectives/$($created.run_id)/execute" -Headers $headers -Body ((@{ context=@{} } | ConvertTo-Json))
$run = Invoke-RestMethod -Method Get -Uri "$base/api/v1/runs/$($created.run_id)" -Headers $headers
Write-Output "PROVIDER_ID=$($provider.provider.provider_id)"
Write-Output "PROVIDER_KEY_REDACTED=$($provider.provider.api_key_configured)"
Write-Output "RUN_ID=$($executed.run_id)"
Write-Output "RUN_STATUS=$($executed.status)"
Write-Output "OUTPUT_TEXT=$($executed.outputs.'intake.objective'.text)"
Write-Output "TASK_STATUS=$($run.graph.tasks[0].status)"
