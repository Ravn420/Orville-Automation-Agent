# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(SPECPATH)
novnc_dir = project_root / "orville" / "gui" / "novnc"

# Bundle data files that get_base_path() resolves at runtime.
datas = [
    (str(project_root / "icon.ico"), "."),
    (str(project_root / ".env.production"), "."),
    # Loaded by orville_core.catalog_adapters.load_catalog at API startup
    (str(project_root / "orville_core" / "connector_catalog.json"), "orville_core"),
]
if novnc_dir.exists():
    datas.append((str(novnc_dir), "orville/gui/novnc"))

a = Analysis(
    ['windows_gui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Local API server spawned via multiprocessing -> start_api()
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "fastapi",
        "starlette",
        "pydantic",
        "anyio",
        # Orville core modules imported lazily / by the API factory
        "orville_core.api",
        "orville_core.gui_state",
        "orville_core.migrations",
        # noVNC WebSocket bridge
        "websockify",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Orville-GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
