$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$token = ((Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }) -replace '^ORVILLE_API_TOKEN=', '').Trim()
$base = 'http://127.0.0.1:8787'
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
$providerPayload = @{ provider_id='mock-stream'; provider_type='openai-compatible-local'; model='mock-code-model'; base_url='http://127.0.0.1:11436/v1'; capabilities=@('text','code','streaming','structured_output','tool_calling') }
Invoke-RestMethod -Method Post -Uri "$base/api/v1/providers" -Headers $headers -Body ($providerPayload | ConvertTo-Json) | Out-Null
$objectivePayload = @{ objective='Create a small Python utility and show the implementation as it is generated'; deliverables=@('Complete Python implementation','Test instructions'); acceptance_criteria=@('orville live code'); risk_level='normal'; generation_mode='agentic'; provider_id='mock-stream'; environment=@{ target_environment='local' } }
$created = Invoke-RestMethod -Method Post -Uri "$base/api/v1/objectives" -Headers $headers -Body ($objectivePayload | ConvertTo-Json)
$started = Invoke-RestMethod -Method Post -Uri "$base/api/v1/objectives/$($created.run_id)/execute" -Headers $headers -Body ((@{ context=@{ stream=$true } } | ConvertTo-Json))
$events = @()
$status = 'running'
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Milliseconds 250
  $run = Invoke-RestMethod -Method Get -Uri "$base/api/v1/runs/$($created.run_id)" -Headers $headers
  $events = $run.events
  $status = $run.run_status
  if ($status -in @('completed','failed','blocked','cancelled')) { break }
}
$delta = @($events | Where-Object { $_.event_type -eq 'model_output_delta' })
$artifacts = Invoke-RestMethod -Method Get -Uri "$base/api/v1/artifacts" -Headers $headers
Invoke-RestMethod -Method Delete -Uri "$base/api/v1/providers/mock-stream" -Headers $headers | Out-Null
Write-Output "RUN_ID=$($created.run_id)"
Write-Output "TASK_ERROR=$($run.graph.tasks[0].error)"
Write-Output "EVENT_TYPES=$((@($events | ForEach-Object { $_.event_type }) -join ',') )"
Write-Output "RUN_STATUS=$status"
Write-Output "STREAM_STARTED=$($started.streaming)"
Write-Output "DELTA_EVENTS=$($delta.Count)"
Write-Output "GENERATED_TEXT_PRESENT=$([bool]($delta[-1].details.text))"
Write-Output "GENERATED_ARTIFACT_PRESENT=$([bool]($artifacts.artifacts | Where-Object { $_.relative_path -like '*generated*' -and $_.relative_path -like "*$($created.run_id)*" }))"
if ($status -ne 'completed' -or $delta.Count -lt 1 -or -not ($artifacts.artifacts | Where-Object { $_.relative_path -like '*generated*' -and $_.relative_path -like "*$($created.run_id)*" })) { throw 'Agentic code streaming regression failed' }
