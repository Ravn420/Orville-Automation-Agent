"""Dynamic loader for Orville extensions."""

from __future__ import annotations
import importlib.util
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from orville_core.extensions import ExtensionRegistry, ExtensionContext, PermissionSet

logger = logging.getLogger("orville.extensions.loader")

class ExtensionLoader:
    """Handles the discovery and dynamic loading of Python-based extensions."""
    
    def __init__(self, registry: ExtensionRegistry, extensions_dir: Path):
        self.registry = registry
        self.extensions_dir = extensions_dir
        self.loaded_extensions: Dict[str, Any] = {}
        self.extensions_dir.mkdir(parents=True, exist_ok=True)

    def load_extension(self, extension_id: str | Path) -> bool:
        """
        Loads a specific extension from the extensions directory.
        If extension_id is a Path, it loads from that path.
        """
        ext_path = Path(extension_id) if isinstance(extension_id, Path) else self.extensions_dir / extension_id
        
        if not ext_path.exists() or not ext_path.is_dir():
            logger.error(f"Extension path not found: {ext_path}")
            return False

        manifest_path = ext_path / "manifest.json"
        if not manifest_path.exists():
            logger.error(f"Manifest missing for extension at {ext_path}")
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            entry_point_file = manifest.get("entry_point", "main.py")
            module_path = ext_path / entry_point_file
            
            if not module_path.exists():
                logger.error(f"Entry point {entry_point_file} not found at {ext_path}")
                return False

            # Dynamic import
            spec = importlib.util.spec_from_file_location(
                f"orville_ext_{manifest['id']}", 
                module_path
            )
            if spec is None or spec.loader is None:
                logger.error(f"Could not create spec for {module_path}")
                return False
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for the OrvilleExtension class
            ext_class = getattr(module, "OrvilleExtension", None)
            if ext_class is None:
                logger.error(f"Extension {manifest['id']} does not implement OrvilleExtension class")
                return False

            # Instantiate and activate
            instance = ext_class()
            
            # For now, we use a default PermissionSet. 
            # In the Manager phase, this will be replaced by user-granted permissions.
            granted = PermissionSet(
                tools=frozenset(["shell_execute", "http_request"]),
                network_hosts=frozenset(),
                scopes=frozenset()
            )
            
            context = ExtensionContext(self.registry, granted)
            instance.activate(context)
            
            self.loaded_extensions[manifest["id"]] = instance
            logger.info(f"Successfully loaded extension: {manifest['name']} ({manifest['id']})")
            return True

        except Exception as e:
            logger.exception(f"Failed to load extension at {ext_path}: {e}")
            return False

    def load_all(self) -> int:
        """Discovers and loads all valid extensions in the extensions directory."""
        count = 0
        for item in self.extensions_dir.iterdir():
            if item.is_dir():
                if self.load_extension(item):
                    count += 1
        return count

    def unload_extension(self, extension_id: str) -> bool:
        """Unloads an extension and calls its deactivate method."""
        instance = self.loaded_extensions.get(extension_id)
        if not instance:
            return False
            
        try:
            # We don't have a full context for deactivation yet, 
            # but we can pass a dummy or the last known context.
            instance.deactivate(None) 
            del self.loaded_extensions[extension_id]
            return True
        except Exception as e:
            logger.error(f"Error unloading extension {extension_id}: {e}")
            return False
