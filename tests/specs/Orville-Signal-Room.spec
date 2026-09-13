# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(SPECPATH)
webui = project_root / "webui"
browser_extension = project_root / "browser_extension"

a = Analysis(
    [str(project_root / "signal_room_launcher.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(webui), "webui"), (str(browser_extension), "browser_extension"), (str(project_root / "orville_core" / "connector_catalog.json"), "orville_core")],
    hiddenimports=[
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "orville_core.api",
        "orville_core.browser",
        "orville_core.migrations",
        "webview",
        "bottle",
        "proxy_tools",
        "pythonnet",
        "clr_loader",
        "orville_core.platform",
        "orville_core.research_data",
        "orville_core.task_threads",
        "orville_core.agent_runtime",
        "orville_core.skills",
        "orville_core.connector_adapters",
        "orville_core.browser_relay",
        "orville_core.usage_health",
        "orville_core.wide_research",
        "huggingface_hub",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Orville-Signal-Room",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
