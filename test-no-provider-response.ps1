$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$line = Get-Content '.\.env.production' | Where-Object { $_ -match '^ORVILLE_API_TOKEN=' }
$token = $line.Substring('ORVILLE_API_TOKEN='.Length).Trim()
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
$objective = @{ objective='No provider regression check'; deliverables=@(); acceptance_criteria=@(); risk_level='normal'; environment=@{ target_environment='local' } }
$created = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8787/api/v1/objectives' -Headers $headers -Body ($objective | ConvertTo-Json)
try {
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8787/api/v1/objectives/$($created.run_id)/execute" -Headers $headers -Body ((@{ context=@{} } | ConvertTo-Json)) | Out-Null
  Write-Output 'UNEXPECTED_EXECUTION_SUCCESS'
} catch {
  $status = $_.Exception.Response.StatusCode.value__
  Write-Output "NO_PROVIDER_STATUS=$status"
}
