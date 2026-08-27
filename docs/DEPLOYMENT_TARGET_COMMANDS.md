# Deployment Target Commands

## Purpose

`deploy.ps1` is the target-specific deployment entry point for Orville. It supports sandbox validation, web hosting, attached desktop packaging/installation, and persistent computing. The script is **dry-run by default**. It prints the commands it would run and performs no build, installation, container, network, or external deployment action unless `-Execute` is supplied after the target has been reviewed and approved.

## Target matrix

| Target | Command | Operation |
|---|---|---|
| Sandbox | `powershell -NoProfile -File .\deploy.ps1 -Target sandbox` | Runs local project checks in dry-run mode; with `-Execute`, runs `tools/project_checks.py all`. |
| Web hosting | `powershell -NoProfile -File .\deploy.ps1 -Target web-hosting` | Reviews `docker-compose.yml` in dry-run mode; with `-Execute`, validates and starts the Compose web deployment. |
| Attached desktop | `powershell -NoProfile -File .\deploy.ps1 -Target attached-desktop -Version 0.1.0` | Prints packaging and installation steps; with `-Execute`, runs the existing release builder and installer. |
| Persistent computing | `powershell -NoProfile -File .\deploy.ps1 -Target persistent-computing` | Reviews Compose configuration in dry-run mode; with `-Execute`, starts the persistent Compose workload with orphan cleanup. |

## Procedure

1. Run the target command without `-Execute` and review its output.
2. Confirm the target is permitted by the execution-target decision contract and that required environment variables are available through protected runtime storage.
3. Run the relevant build, security, release-hardening, and triage checks before execution.
4. Obtain any required approval for installation, network exposure, persistent services, or external side effects.
5. Re-run the exact command with `-Execute` in the approved environment.
6. Capture only secret-free command output and perform the target-specific smoke test.
7. Record version, target, artifact path, operator, validation evidence, and rollback reference.

## Boundaries

The script does not create credentials, discover endpoints, upload artifacts, change DNS, open firewall ports, or bypass release gates. The Compose commands require Docker and an explicitly configured environment. The desktop path uses the repository's existing `build-release.ps1` and `install-orville.ps1`; review their release-hardening requirements before execution. Sandbox mode validates locally and does not create a persistent deployment. Persistent computing requires an approved host, bounded resources, protected data paths, health checks, and a shutdown/rollback procedure.

## Validation

From the repository root:

```powershell
python -m unittest tests.test_deployment_commands -v
powershell -NoProfile -Command "[System.Management.Automation.Language.Parser]::ParseFile('deploy.ps1',[ref]$null,[ref]$null) | Out-Null"
```

These checks are local and credential-free. A syntax check does not prove that Docker, Windows packaging, a host, provider access, or production permissions are available.
