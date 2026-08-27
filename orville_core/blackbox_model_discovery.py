"""Credential-free Blackbox model discovery and manual fallback contract.

The module only normalizes caller-supplied discovery metadata. It performs no
network requests and never accepts, stores, or returns API-key material.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .blackbox_contract import BlackboxApiKeyContract, BlackboxContractError


class BlackboxModelDiscoveryError(ValueError):
    """Raised when model discovery metadata violates the local safety contract."""


@dataclass(frozen=True)
class BlackboxModelDiscoveryResult:
    """Normalized model catalog, including a safe manual fallback state."""

    base_url: str
    endpoint_family: str
    models: tuple[str, ...]
    active_model: str
    discovery_supported: bool
    manual_model_entry: bool
    status: str
    reason: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "endpoint_family": self.endpoint_family,
            "models": list(self.models),
            "active_model": self.active_model,
            "discovery_supported": self.discovery_supported,
            "manual_model_entry": self.manual_model_entry,
            "status": self.status,
            "reason": self.reason,
            "credential_returned": False,
        }


class BlackboxModelDiscovery:
    """Normalize a Blackbox `/models` response without making external calls."""

    def discover(
        self,
        *,
        base_url: str,
        model: str,
        response_payload: object | None = None,
        discovery_supported: bool = True,
    ) -> BlackboxModelDiscoveryResult:
        try:
            normalized_url = BlackboxApiKeyContract(base_url=base_url, model=model).validate()
        except BlackboxContractError as exc:
            raise BlackboxModelDiscoveryError(str(exc)) from exc

        active_model = model.strip()
        endpoint_family = "enterprise" if normalized_url.split("//", 1)[1].split("/", 1)[0].lower() == "enterprise.blackbox.ai" else "public"
        if not discovery_supported or response_payload is None:
            return self._manual(normalized_url, endpoint_family, active_model, "model discovery unavailable; manual model entry is required")

        discovered = self._extract_models(response_payload)
        if not discovered:
            return self._manual(normalized_url, endpoint_family, active_model, "provider returned no usable models; manual model entry is required")
        if active_model not in discovered:
            active_model = discovered[0]
        return BlackboxModelDiscoveryResult(normalized_url, endpoint_family, tuple(discovered), active_model, True, True, "ok")

    @staticmethod
    def _extract_models(payload: object) -> list[str]:
        if not isinstance(payload, dict):
            return []
        raw_models = payload.get("data")
        if not isinstance(raw_models, list):
            raw_models = payload.get("models")
        if not isinstance(raw_models, list):
            return []
        result: list[str] = []
        for item in raw_models:
            value = item.get("id") if isinstance(item, dict) else item
            if isinstance(value, str):
                value = value.strip()
                if value and len(value) <= 240 and "\n" not in value and value not in result:
                    result.append(value)
        return result

    @staticmethod
    def _manual(base_url: str, endpoint_family: str, model: str, reason: str) -> BlackboxModelDiscoveryResult:
        return BlackboxModelDiscoveryResult(base_url, endpoint_family, (model,), model, False, True, "manual_required", reason)


def discover_blackbox_models(**kwargs: Any) -> dict[str, Any]:
    """Return the public discovery result for callers that prefer a mapping."""
    return BlackboxModelDiscovery().discover(**kwargs).public()


__all__ = [
    "BlackboxModelDiscovery",
    "BlackboxModelDiscoveryError",
    "BlackboxModelDiscoveryResult",
    "discover_blackbox_models",
]


# End of module.

