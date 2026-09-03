"""Management of extension installation, permissions, and persistence."""

from __future__ import annotations
import json
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from orville_core.extensions import ExtensionRegistry, PermissionSet
from orville_core.extension_loader import ExtensionLoader

logger = logging.getLogger("orville.extensions.manager")

class ExtensionManager:
    """Handles the high-level lifecycle of extensions: install, uninstall, and permissions."""

    def __init__(
        self,
        registry: ExtensionRegistry,
        extensions_dir: Path,
        config_dir: Path
    ):
        self.registry = registry
        self.extensions_dir = extensions_dir
        self.config_dir = config_dir
        self.loader = ExtensionLoader(registry, extensions_dir)

        self.state_file = config_dir / "extensions_state.json"
        self.permissions_file = config_dir / "extensions_permissions.json"

        self.installed_extensions: Dict[str, Dict[str, Any]] = self._load_state()
        self.granted_permissions: Dict[str, Dict[str, Any]] = self._load_permissions()

    def _load_state(self) -> Dict[str, Dict[str, Any]]:
        if not self.state_file.exists():
            return {}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load extension state: {e}")
            return {}

    def _load_permissions(self) -> Dict[str, Dict[str, Any]]:
        if not self.permissions_file.exists():
            return {}
        try:
            with open(self.permissions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load extension permissions: {e}")
            return {}

    def _save_state(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.installed_extensions, f, indent=2)

    def _save_permissions(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.permissions_file, "w", encoding="utf-8") as f:
            json.dump(self.granted_permissions, f, indent=2)

    def install_from_archive(self, archive_path: Path) -> str:
        """Installs an extension from a .orv or .zip archive."""
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        # Extract to a temporary location first to validate manifest
        temp_extract = self.extensions_dir / f"temp_{archive_path.stem}"
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract)

            manifest_path = temp_extract / "manifest.json"
            if not manifest_path.exists():
                raise ValueError("Invalid extension: manifest.json missing")

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            ext_id = manifest["id"]
            final_path = self.extensions_dir / ext_id

            if final_path.exists():
                shutil.rmtree(final_path)

            shutil.move(str(temp_extract), str(final_path))

            # Update state
            self.installed_extensions[ext_id] = {
                "name": manifest["name"],
                "version": manifest["version"],
                "enabled": False,
                "installed_at": archive_path.stat().st_mtime
            }
            self._save_state()

            return ext_id
        finally:
            if temp_extract.exists():
                shutil.rmtree(temp_extract, ignore_errors=True)

    def grant_permissions(self, extension_id: str, permissions: Dict[str, Any]) -> None:
        """Explicitly grants permissions to an extension."""
        self.granted_permissions[extension_id] = permissions
        self._save_permissions()

    def enable_extension(self, extension_id: str) -> bool:
        """Enables an extension and loads it into the registry."""
        if extension_id not in self.installed_extensions:
            logger.error(f"Extension {extension_id} is not installed")
            return False

        # Resolve permissions
        perm_data = self.granted_permissions.get(extension_id, {})
        granted = PermissionSet(
            tools=frozenset(perm_data.get("tools", [])),
            network_hosts=frozenset(perm_data.get("network_hosts", [])),
            scopes=frozenset(perm_data.get("scopes", []))
        )

        # Use loader to activate
        if self.loader.load_extension(extension_id):
            self.installed_extensions[extension_id]["enabled"] = True
            self._save_state()
            return True

        return False

    def disable_extension(self, extension_id: str) -> bool:
        """Disables and unloads an extension."""
        if self.loader.unload_extension(extension_id):
            if extension_id in self.installed_extensions:
                self.installed_extensions[extension_id]["enabled"] = False
                self._save_state()
            return True
        return False

    def uninstall_extension(self, extension_id: str) -> bool:
        """Completely removes an extension from the system."""
        self.disable_extension(extension_id)

        ext_path = self.extensions_dir / extension_id
        if ext_path.exists():
            shutil.rmtree(ext_path)

        if extension_id in self.installed_extensions:
            del self.installed_extensions[extension_id]
            self._save_state()

        if extension_id in self.granted_permissions:
            del self.granted_permissions[extension_id]
            self._save_permissions()

        return True

    def list_installed(self) -> List[Dict[str, Any]]:
        """Returns a list of all installed extensions and their status."""
        return [
            {"id": eid, **data}
            for eid, data in self.installed_extensions.items()
        ]
