"""Manifest loader for every catalogued connector.

A catalog entry is not marked operational until a provider-specific API contract,
authentication flow, and invocation handler are registered. Unknown services are
still represented as configuration-required adapters rather than being silently
omitted or falsely advertised as connected.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class CatalogAdapter:
    connector_id: str
    display_name: str
    description: str
    catalog_enabled: bool
    support_state: str = "configuration_required"
    auth_types: tuple[str, ...] = ("oauth2", "api_key", "bearer", "custom")
    operations: tuple[dict[str, Any], ...] = ()
    documentation_url: str | None = None

    def status(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "display_name": self.display_name,
            "description": self.description,
            "catalog_enabled": self.catalog_enabled,
            "support_state": self.support_state,
            "auth_types": list(self.auth_types),
            "operations": list(self.operations),
            "documentation_url": self.documentation_url,
        }


def load_catalog(path: str | Path | None = None) -> tuple[CatalogAdapter, ...]:
    catalog_path = Path(path) if path else Path(__file__).with_name("connector_catalog.json")
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("connector catalog must be a list")
    adapters: list[CatalogAdapter] = []
    seen: set[str] = set()
    for item in payload:
        connector_id = str(item.get("uid", "")).strip()
        name = str(item.get("name", "")).strip()
        if not connector_id or not name or connector_id in seen:
            raise ValueError("connector catalog contains missing or duplicate identity")
        seen.add(connector_id)
        adapters.append(CatalogAdapter(connector_id, name, str(item.get("brief", "")), bool(item.get("enabled", False))))
    return tuple(adapters)


def catalog_summary(adapters: tuple[CatalogAdapter, ...]) -> dict[str, int]:
    return {
        "total": len(adapters),
        "catalog_enabled": sum(item.catalog_enabled for item in adapters),
        "configuration_required": sum(item.support_state == "configuration_required" for item in adapters),
        "operational": sum(item.support_state == "operational" for item in adapters),
    }
