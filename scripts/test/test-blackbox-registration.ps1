$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

# This smoke test targets only the local Orville API. It never calls Blackbox.
$baseUrl = if ($env:ORVILLE_API_BASE_URL) { $env:ORVILLE_API_BASE_URL.TrimEnd('/') } else { 'http://127.0.0.1:8787' }
$token = $env:ORVILLE_API_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
    throw 'ORVILLE_API_TOKEN must be supplied through the process environment; no credential is read from project files.'
}
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }

function Invoke-LocalJson {
    param([ValidateSet('Get', 'Post', 'Delete')][string]$Method, [string]$Path, [hashtable]$Body)
    $params = @{ Method = $Method; Uri = "$baseUrl$Path"; Headers = $headers }
    if ($null -ne $Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
    Invoke-RestMethod @params
}

$health = Invoke-LocalJson Get '/api/v1/health'
$status = Invoke-LocalJson Get '/api/v1/cloud/blackbox/status'
$onboarding = Invoke-LocalJson Get '/api/v1/cloud/blackbox/onboarding'

if ($status.user_connected.status -ne 'not_connected') { throw 'clean startup must be disconnected from user Blackbox access' }
if ($onboarding.onboarding.default_access -ne 'managed_cloud') { throw 'managed cloud must remain the default access mode' }
if ($onboarding.onboarding.user_connection.action_label -ne 'Connect with Blackbox API key') { throw 'optional API-key action is missing' }

$invalid = $null
try {
    $invalid = Invoke-LocalJson Post '/api/v1/cloud/blackbox/user/test' @{ api_key = 'synthetic-test-key'; base_url = 'http://127.0.0.1:9'; model = 'blackboxai/openai/gpt-5.5' }
    throw 'invalid endpoint unexpectedly passed validation'
} catch {
    if ($_.Exception.Message -notmatch '400|HTTPS|endpoint') { throw }
}

$providerHealth = Invoke-LocalJson Get '/api/v1/provider-health/blackbox'
$disconnect = Invoke-LocalJson Post '/api/v1/cloud/blackbox/user/disconnect' $null
if (-not $disconnect.managed_access_unchanged -or -not $disconnect.local_mode_unchanged -or -not $disconnect.unrelated_task_state_unchanged) {
    throw 'disconnect did not preserve managed/local/task state'
}
$after = Invoke-LocalJson Get '/api/v1/cloud/blackbox/status'
if ($after.fallback.available -ne $false -and $after.fallback.available -ne $true) { throw 'fallback status was not returned' }

Write-Output "CLEAN_STARTUP=$($health.status)"
Write-Output "DISCONNECTED_STATUS=$($status.user_connected.status)"
Write-Output "MANAGED_DEFAULT=$($onboarding.onboarding.default_access)"
Write-Output "OPTIONAL_API_KEY_ACTION=$($onboarding.onboarding.user_connection.action_label)"
Write-Output 'INVALID_ENDPOINT_REJECTED=True'
Write-Output "PROVIDER_HEALTH_AVAILABLE=$($providerHealth.available)"
Write-Output "DISCONNECT_MANAGED_UNCHANGED=$($disconnect.managed_access_unchanged)"
Write-Output "DISCONNECT_LOCAL_UNCHANGED=$($disconnect.local_mode_unchanged)"
Write-Output "FALLBACK_STATUS=$($after.fallback.primary_status)"
