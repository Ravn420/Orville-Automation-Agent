"""Adapter for bridging VS Code extensions to Orville.

This module provides the logic to translate VS Code's package.json manifests
and contribution points into Orville's Skill and Connector registry.
"""

from __future__ import annotations
import json
import logging
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from orville_core.extensions import Skill, Connector, PermissionSet

logger = logging.getLogger("orville.extensions.vscode")

class VSCodeAdapter:
    """Translates VS Code extension metadata into Orville extension definitions."""
    
    def __init__(self, marketplace_url: str = "https://open-vsx.org/api"):
        self.marketplace_url = marketplace_url

    def translate_manifest(self, package_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a VS Code package.json to an Orville manifest.json.
        
        Mapping Logic:
        - 'name' -> 'id' (converted to reverse-dns if possible)
        - 'displayName' -> 'name'
        - 'version' -> 'version'
        - 'contributes.commands' -> 'provides.skills'
        - 'contributes.configuration' -> 'provides.connectors' (if it defines external endpoints)
        """
        ext_id = package_json.get("name", "unknown-vscode-ext")
        display_name = package_json.get("displayName", ext_id)
        
        # Extract commands as potential skills
        contributions = package_json.get("contributes", {})
        commands = contributions.get("commands", [])
        
        # In VS Code, commands are often defined as a list of objects:
        # [{"command": "ext.doSomething", "title": "Do Something"}]
        skills = []
        for cmd in commands:
            if isinstance(cmd, dict):
                cmd_id = cmd.get("command")
                cmd_title = cmd.get("title", cmd_id)
                if cmd_id:
                    skills.append(cmd_id)
        
        # Map configuration as potential connector requirements
        connectors = []
        config = contributions.get("configuration", {})
        if isinstance(config, dict):
            for key in config.keys():
                if "url" in key.lower() or "endpoint" in key.lower():
                    connectors.append(f"connector_{key}")

        return {
            "id": f"vscode.{ext_id}",
            "name": display_name,
            "version": package_json.get("version", "0.0.0"),
            "description": package_json.get("description", ""),
            "entry_point": "vscode_bridge.py", # The bridge handler
            "provides": {
                "skills": skills,
                "connectors": connectors,
                "hooks": []
            }
        }

    def search_marketplace(self, query: str) -> List[Dict[str, Any]]:
        """Searches the Open VSX registry for compatible extensions."""
        try:
            response = requests.get(f"{self.marketplace_url}/extensions?query={query}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for ext in data.get("extensions", []):
                results.append({
                    "id": ext.get("name"),
                    "name": ext.get("displayName"),
                    "version": ext.get("version"),
                    "description": ext.get("description"),
                    "download_url": ext.get("downloadUrl")
                })
            return results
        except Exception as e:
            logger.error(f"Marketplace search failed: {e}")
            return []

    def fetch_extension_manifest(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """Fetches the package.json for a specific VS Code extension."""
        try:
            # Note: Open VSX provides metadata via API, but the actual package.json 
            # is inside the .vsix (which is a zip).
            response = requests.get(f"{self.marketplace_url}/extensions/{extension_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch manifest for {extension_id}: {e}")
            return None
