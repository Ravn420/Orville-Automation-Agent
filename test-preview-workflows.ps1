$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $line.Substring('ORVILLE_API_TOKEN='.Length)
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
function Get-Json($method, $path, $body = $null) {
  $params = @{ Method=$method; Uri=("http://127.0.0.1:8787" + $path); Headers=$headers; UseBasicParsing=$true }
  if ($null -ne $body) { $params.Body = ($body | ConvertTo-Json -Depth 10) }
  return Invoke-RestMethod @params
}
$health = Get-Json GET '/api/v1/health'
$state = Get-Json GET '/api/v1/state'
$artifacts = Get-Json GET '/api/v1/artifacts'
$created = Get-Json POST '/api/v1/objectives' @{ objective='Preview integration verification'; deliverables=@('Verify local preview connection'); acceptance_criteria=@('Health is authenticated'); risk_level='normal'; environment=@{target_environment='local'} }
$runId = $created.run_id
$run = Get-Json GET ("/api/v1/runs/$runId")
$events = Get-Json GET ("/api/v1/runs/$runId/events")
$firstTask = $created.task_ids[0]
$approval = Get-Json POST ("/api/v1/runs/$runId/tasks/$firstTask/approval") @{ approved = $true }
$cancel = Get-Json POST ("/api/v1/runs/$runId/cancel")
Write-Output "HEALTH=$($health.status)"
Write-Output "STATE_PROJECT=$($state.project_id)"
Write-Output "ARTIFACTS_COUNT=$($artifacts.artifacts.Count)"
Write-Output "OBJECTIVE_RUN_CREATED=$([bool]$runId)"
Write-Output "RUN_LOADED=$([bool]$run.run_id)"
Write-Output "EVENTS_LOADED=$([bool]($null -ne $events.events))"
Write-Output "APPROVAL_STATUS=$($approval.status)"
Write-Output "CANCEL_STATUS=$($cancel.status)"
