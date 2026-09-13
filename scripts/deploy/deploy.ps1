[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("sandbox", "web-hosting", "attached-desktop", "persistent-computing")]
    [string]$Target,
    [string]$Version = "0.1.0",
    [switch]$Execute
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-DeploymentStep {
    param([string]$FilePath, [string[]]$Arguments)
    $display = "$FilePath $($Arguments -join ' ')".Trim()
    if (-not $Execute) {
        Write-Output "DRY-RUN [$Target]: $display"
        return
    }
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Deployment step failed: $display" }
}

$validation = Join-Path $root "tools\deployment_validation.py"
Invoke-DeploymentStep "python" @($validation, "preflight", "--target", $Target, "--root", $root)

switch ($Target) {
    "sandbox" {
        Invoke-DeploymentStep "python" @("tools/project_checks.py", "all")
        Write-Output "Sandbox target is validated locally; no persistent deployment is performed."
    }
    "web-hosting" {
        $compose = Join-Path $root "docker-compose.yml"
        if (-not (Test-Path $compose)) { throw "docker-compose.yml is required for web-hosting." }
        Invoke-DeploymentStep "docker" @("compose", "-f", $compose, "config")
        Invoke-DeploymentStep "docker" @("compose", "-f", $compose, "up", "-d", "--build")
        Invoke-DeploymentStep "python" @($validation, "smoke", "--url", "http://127.0.0.1", "--path", "/docs")
    }
    "attached-desktop" {
        Invoke-DeploymentStep "powershell" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $root "build-release.ps1"), "-Version", $Version)
        Invoke-DeploymentStep "powershell" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $root "install-orville.ps1"))
    }
    "persistent-computing" {
        $compose = Join-Path $root "docker-compose.yml"
        if (-not (Test-Path $compose)) { throw "docker-compose.yml is required for persistent-computing." }
        Invoke-DeploymentStep "docker" @("compose", "-f", $compose, "config")
        Invoke-DeploymentStep "docker" @("compose", "-f", $compose, "up", "-d", "--build", "--remove-orphans")
        Invoke-DeploymentStep "python" @($validation, "smoke", "--url", "http://127.0.0.1", "--path", "/docs")
    }
}

if (-not $Execute) {
    Write-Output "No external deployment was executed. Re-run with -Execute only after reviewing the target and approval requirements."
}
