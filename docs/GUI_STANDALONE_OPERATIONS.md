# Standalone GUI Operations Guide

## Summary

Orville's current reference GUI is a native Windows control center backed by the local Orville API. It can run, build, package, update, and deploy without Manus; Manus-specific adapters are optional and the minimum standalone path uses local Python services, local storage, and configured local or user-approved providers.

> The GUI is a client of Orville capabilities. It does not own orchestration state, credentials, authorization decisions, or external side effects.

## Requirements and boundaries

| Requirement | Minimum | Notes |
|---|---|---|
| Operating system | Windows 10/11 supported desktop environment | Tkinter is required for source execution; WebView2 is used by the packaged Signal Room launcher when available. |
| Python | 3.10 or newer | Use Python 3.12 when available for the project’s primary development environment. |
| Build tools | PowerShell, pip, and PyInstaller for packaged GUI builds | Docker is required only for the containerized backend deployment path. |
| Optional services | Ollama, another local endpoint, or an explicitly configured provider | No provider credential is required for the local demonstration. |
| Runtime data | `%LOCALAPPDATA%\Orville\data` in installed mode, or `data\` beside the executable in portable mode | Keep mutable state outside source control. |

Credentials must be supplied only through the approved protected environment or credential store. Never place credentials in the repository, GUI fields that persist raw values, screenshots, logs, release archives, or packaged binaries. External actions, publication, deployment, connector mutation, and account changes remain approval-gated.

## 1. Run from source

### 1.1 Create an isolated environment

From the repository root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[api]"
```

Install development and optional capabilities only when needed:

```powershell
python -m pip install -e ".[dev]"
python -m pip install -e ".[browser]"
python -m pip install -e ".[media]"
```

Do not install optional dependencies merely because a provider or connector mentions them. Select the minimum set required by the target workflow and record the selection in the release evidence.

### 1.2 Run the deterministic local workflow

```powershell
python examples\basic_run.py
```

This path exercises the standalone task graph and checkpoint behavior without requiring Manus or a live provider.

### 1.3 Run the desktop GUI

```powershell
python windows_gui.py
```

The source GUI uses the local Orville API contract. If an API service is required by the selected workflow, start it in a separate PowerShell session:

```powershell
$env:ORVILLE_API_TOKEN = '<value supplied through a protected environment mechanism>'
python -m orville_core.api
```

Use a protected runtime mechanism for the token. Do not copy a real token into shell history, documentation, source files, or logs. The GUI should remain usable for local drafts, local model workflows, and saved review state when cloud providers or connectors are unavailable.

## 2. Build and validate

Run the source-level checks before packaging:

```powershell
python -m compileall -q orville_core tests examples tools windows_gui.py
python -m pytest -q
python -m unittest discover -s tests -q
python tools\signal_room_checks.py webui
python tools\release_gate.py
```

The release gate compiles the core and GUI, executes the configured regression and security checks, and builds a disposable wheel. A failure stops packaging until the failure is triaged. Live provider, browser, deployment, and production checks must be labeled separately from credential-free local validation.

## 3. Package a Windows GUI release

The packaged GUI is built from `Orville-Signal-Room.spec` and produces `dist\Orville-Signal-Room.exe`:

```powershell
pyinstaller.exe --noconfirm --clean Orville-Signal-Room.spec
```

Create the portable archive and installer-ready directory:

```powershell
.\build-release.ps1 -Version 0.1.0
```

For a portable-only archive:

```powershell
.\build-release.ps1 -Version 0.1.0 -PortableOnly
```

Expected outputs are:

```text
release\Orville-Portable-0.1.0\
release\Orville-Portable-0.1.0.zip
release\install-orville.ps1
```

The packaging script copies the executable, browser extension when present, supporting operation documents, and a portable data directory. It writes `ORVILLE_PORTABLE=1` into the portable data environment. Do not place `.env.production` with real credentials inside the archive.

## 4. Install and update

### 4.1 Portable mode

Extract the versioned ZIP to a user-controlled directory and run `Orville-Signal-Room.exe`. Portable mutable state remains in the release directory’s `data\` folder. Back up the entire `data\` directory before replacing the executable or migrating to another version.

### 4.2 Installed mode

Run the reviewed installer from an elevated PowerShell session:

```powershell
.\release\install-orville.ps1
```

Installed program files are placed under `%LOCALAPPDATA%\Programs\Orville` and a desktop shortcut is created. Mutable user data remains under `%LOCALAPPDATA%\Orville`; an update must not replace, delete, or reset that directory.

### 4.3 Safe update sequence

1. Record the current version, executable checksum, configuration schema version, and runtime-state location.
2. Close the GUI and confirm no Orville process is still serving the local API.
3. Back up `%LOCALAPPDATA%\Orville\data` or the portable `data\` directory, including SQLite files, checkpoints, artifacts, model catalogs, and logs.
4. Validate the new release in a disposable directory using the packaged startup, browser fallback, local UI, API health, and duplicate-launch checks.
5. Install or extract the new program files without deleting the backed-up data directory.
6. Start the new release and verify the runtime state, read-only project/checkpoint view, local model inventory, and a credential-free smoke workflow.
7. Retain the old executable and backup until the new release passes the agreed acceptance gates.

The supplied installer’s uninstall path removes program files and the shortcut but preserves `%LOCALAPPDATA%\Orville` data. Do not use broad deletion or volume-removal commands as part of an update.

## 5. Deploy the backend and GUI independently of Manus

For a small-team deployment, use the documented Docker Compose topology: private `api` service, Caddy proxy on ports 80/443, and persistent `orville-data` and `caddy-data` volumes. From a clean release checkout:

```powershell
docker build -t orville:local .
docker run --rm -p 8000:8000 --env-file .env.example orville:local
```

For an approved Compose promotion:

```powershell
docker compose --env-file .env.production config --quiet
docker compose --env-file .env.production up -d --build
docker compose --env-file .env.production ps
```

Before promotion, create and verify a database backup, review the effective non-secret configuration, confirm the API is not unintentionally public, and run the complete release checks. Verify the authenticated health route and the GUI root through the approved domain. Keep `.env.production` outside source control and inject secrets through the deployment secret manager.

The native GUI can be distributed separately from the API deployment. It connects to the configured local or approved API boundary; it must not embed server credentials or bypass API authorization. If the backend is unavailable, the GUI must show an actionable unavailable state and preserve local drafts, checkpoints, and evidence where applicable.

## 6. Rollback and recovery

Rollback is approval-gated. Preserve current logs, the failed release, the database backup, and release evidence. Stop promotion when a preflight, health, data-read, or smoke check fails. Restore the last approved executable/image and non-secret configuration, then verify health, read-only data access, GUI startup, and the smoke workflow. Do not use `docker compose down --volumes`, delete `%LOCALAPPDATA%\Orville`, or overwrite the only backup.

If a credential may have been exposed, rotate or revoke it through the approved credential manager before resuming service. Report only a safe operation identifier and error class in the GUI and release evidence.

## 7. Standalone release acceptance checklist

- [ ] Source GUI starts with `python windows_gui.py` in the supported Windows environment.
- [ ] The deterministic local workflow runs without Manus or external credentials.
- [ ] Compilation, regression, security, GUI smoke, and release-gate checks pass.
- [ ] PyInstaller creates `dist\Orville-Signal-Room.exe`.
- [ ] Portable packaging creates a versioned directory and ZIP without raw credentials.
- [ ] Installed and portable data locations are documented and backed up before update.
- [ ] Packaged startup, browser fallback, API health, runtime-state creation, and duplicate-launch behavior pass.
- [ ] Deployment configuration, health checks, backup, rollback, and evidence retention are complete.
- [ ] The GUI remains usable when Manus, cloud providers, connectors, or local endpoints are unavailable.

## Known limitations

The current guide documents the local Windows GUI and the existing Compose deployment path. Code signing, provider-specific production deployment, live browser automation, cloud-provider verification, and infrastructure-owned rollback evidence require the target environment and authorized operators. These are not silently claimed as completed by credential-free local validation.

## Related documents

- `docs/GUI_ARCHITECTURE_BOUNDARIES.md`
- `docs/GUI_TEST_STRATEGY.md`
- `docs/GUI_DEGRADED_AVAILABILITY.md`
- `docs/RELEASE_GATES.md`
- `release/Orville-Portable-0.1.0/RELEASE_HARDENING.md`
- `docs/DELIVERY_RUNBOOK.md`
