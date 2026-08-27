[CmdletBinding()]
param(
    [string]$TaskName = 'Orville Manus Todo Worker'
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$Worker = Join-Path $Repo 'tools\orville_manus_worker.py'
$Python = (Get-Command py -ErrorAction SilentlyContinue).Source
if (-not $Python) { $Python = (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $Python) { throw 'Python was not found. Install Python 3.11+ and rerun this script.' }

$Action = New-ScheduledTaskAction -Execute $Python -Argument ('"{0}" --repo "{1}" --max-active 3 --max-retries 2 --lease-seconds 600' -f $Worker, $Repo)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds 50)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description 'Continues exactly three already-created Manus task threads for actionable Orville TODO items using the explicit Orville repository path; never creates new tasks. Uses bounded retries and heartbeat lease recovery.' -Force | Out-Null
Write-Output "Installed scheduled task: $TaskName"
Write-Output "Worker: $Worker"
Write-Output 'The worker reads MANUS_API_KEY from the process environment; no secret is written by this script.'
Write-Output ('Run python tools\\orville_manus_worker.py --repo "{0}" --dry-run --max-active 3 to inspect the three configured task slots without network calls.' -f $Repo)
