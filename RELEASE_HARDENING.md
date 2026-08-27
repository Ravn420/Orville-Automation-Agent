# Orville Windows Release Hardening

## Release behavior

The existing Signal Room React interface is packaged unchanged as static web assets. `Orville-Signal-Room.exe` starts the local FastAPI control plane and serves the same GUI inside a native WebView2 window when available. If WebView2 or its Python shell dependency is unavailable, the launcher falls back to the system browser without changing the frontend.

The launcher uses `127.0.0.1` only. It prefers API port `8787` and frontend port `3000`, but selects free local ports when those are occupied. The chosen ports and runtime URL are written to `%LOCALAPPDATA%\Orville\data\runtime-state.json`.

## Data safety

Installed releases store mutable data under `%LOCALAPPDATA%\Orville\data`, including tasks, artifacts, model catalogs, model files, browser state, logs, and configuration. The first upgraded release copies legacy `dist\data` state into this location without deleting the original files. A versioned `schema-version.json` ledger and non-destructive SQLite backup directory support future migrations.

Portable releases set `ORVILLE_PORTABLE=1` in their local data environment and keep mutable state beside the portable executable. Use the generated `release\Orville-Portable-0.1.0.zip` for this mode.

## Build outputs

Run `pyinstaller.exe --noconfirm --clean Orville-Signal-Room.spec` to build the executable. Run `build-release.ps1 -Version 0.1.0` to create the portable ZIP and installer-ready directory. The supplied `install-orville.ps1` installs program files under `%LOCALAPPDATA%\Programs\Orville`, creates a desktop shortcut, and leaves user data under `%LOCALAPPDATA%\Orville`.

The supplied `sign-release.ps1` prepares Authenticode signing but requires the user’s own certificate, password, Windows SDK `signtool.exe`, and timestamp policy. No certificate or private key is embedded in the project.

## Reliability controls

A Windows file lock prevents duplicate application instances. A duplicate launch attempts to focus an existing native window and exits without starting another API or frontend server. Clean shutdown closes the static server and signals Uvicorn to stop. Startup failures are written to `launcher-error.log`; runtime ports, process ID, and lifecycle status are written to `runtime-state.json`.

## Validation completed

The backend regression suite passed with 124 tests. Python compilation passed. The final executable build completed successfully. Packaged validation passed for native/default startup, browser-fallback startup, UI root HTTP 200, API docs HTTP 200, unauthenticated API HTTP 401, dynamic runtime-state creation, and duplicate-launch blocking. Portable archive generation produced a 62 MB ZIP and the installer script was included.
