# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Orville GUI with proper packaging for frozen executables.

Key fixes:
- Includes get_base_path() helper for frozen app path resolution
- Bundles websockify and noVNC assets
- Includes .env.production file
- Properly handles multiprocessing.freeze_support()

Usage:
    pyinstaller --noconfirm --clean Orville-GUI-Final-Fixed.spec
"""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

block_cipher = None

a = Analysis(
    ['windows_gui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include .env.production if it exists
        ('.env.production', '.'),
        # Include icon
        ('icon.ico', '.'),
        # Include noVNC web assets for browser/VNC integration
        ('orville/gui/novnc', 'orville/gui/novnc'),
        # Include connector catalog
        ('orville_core/connector_catalog.json', 'orville_core'),
    ],
    hiddenimports=[
        # Ensure websockify is included
        'websockify',
        'websockify.websocketproxy',
        # Ensure all orville_core modules are included
        'orville_core',
        'orville_core.api',
        'orville_core.gui_state',
        'orville_core.inprocess_client',
        'orville_core.engine',
        'orville_core.providers',
        'orville_core.routing',
        'orville_core.workflow',
        'orville_core.checkpoint',
        'orville_core.persistence',
        'orville_core.artifacts',
        'orville_core.memory',
        'orville_core.extensions',
        'orville_core.integration',
        'orville_core.models',
        'orville_core.security',
        'orville_core.attestations',
        'orville_core.platform',
        'orville_core.automation',
        'orville_core.governance',
        'orville_core.preview',
        'orville_core.research_data',
        'orville_core.identity',
        'orville_core.adapters',
        'orville_core.secrets_audit',
        'orville_core.scheduler',
        'orville_core.preview_runtime',
        'orville_core.readiness',
        'orville_core.config',
        'orville_core.workspace',
        'orville_core.browser',
        'orville_core.hub_models',
        'orville_core.model_runtime',
        'orville_core.local_models',
        'orville_core.connector_bridge',
        'orville_core.provider_mcp_security',
        'orville_core.connector_connections',
        'orville_core.connector_defaults',
        'orville_core.provider_presets',
        'orville_core.task_threads',
        'orville_core.agent_runtime',
        'orville_core.skills',
        'orville_core.connector_adapters',
        'orville_core.connector_governance',
        'orville_core.usage_health',
        'orville_core.browser_relay',
        'orville_core.catalog_adapters',
        'orville_core.openapi_discovery',
        'orville_core.cloud_relay',
        'orville_core.blackbox_contract',
        'orville_core.blackbox_capabilities',
        'orville_core.blackbox_model_discovery',
        'orville_core.cloud_onboarding',
        'orville_core.provider_features',
        'orville_core.canary',
        'orville_core.run_manager',
        # FastAPI and dependencies
        'fastapi',
        'uvicorn',
        'pydantic',
        'starlette',
        'anyio',
        # Cryptography
        'cryptography',
        'cryptography.fernet',
        # HTTP
        'requests',
        'urllib3',
        # JSON
        'json',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Orville',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
