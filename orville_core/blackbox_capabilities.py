"""Credential-free capability negotiation for Blackbox endpoint families."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


BLACKBOX_CAPABILITIES = frozenset({"chat", "streaming", "tool_calling", "multimodal_generation", "embeddings", "agent_tasks", "github_operations", "remote_task_resumption"})


class BlackboxCapabilityError(ValueError):
    """Raised when capability negotiation metadata is invalid."""


@dataclass(frozen=True)
class BlackboxCapabilityResult:
    endpoint_family: str
    model: str
    account_plan: str
    supported: frozenset[str]
    unavailable_reasons: dict[str, str]

    def public(self) -> dict[str, object]:
        return {
            "endpoint_family": self.endpoint_family,
            "model": self.model,
            "account_plan": self.account_plan,
            "supported": sorted(self.supported),
            "unavailable": dict(sorted(self.unavailable_reasons.items())),
            "credential_configured": False,
        }


class BlackboxCapabilityNegotiator:
    """Expose only capabilities supported by endpoint, plan, and explicit metadata."""

    _PLAN_RANK = {"unknown": 0, "free": 1, "pro": 2, "enterprise": 3}

    def negotiate(self, *, base_url: str, model: str, account_plan: str = "unknown", advertised: set[str] | frozenset[str] = frozenset()) -> BlackboxCapabilityResult:
        parsed = urlparse(base_url.rstrip("/"))
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment or host not in {"api.blackbox.ai", "enterprise.blackbox.ai"}:
            raise BlackboxCapabilityError("Blackbox endpoint family must use a documented HTTPS host")
        if not model.strip():
            raise BlackboxCapabilityError("Blackbox model identifier is required")
        plan = account_plan.lower().strip() or "unknown"
        if plan not in self._PLAN_RANK:
            raise BlackboxCapabilityError("unsupported Blackbox account plan")
        unknown = set(advertised) - BLACKBOX_CAPABILITIES
        if unknown:
            raise BlackboxCapabilityError(f"unknown Blackbox capabilities: {sorted(unknown)}")
        family = "enterprise" if host == "enterprise.blackbox.ai" else "standard"
        supported: set[str] = set()
        reasons: dict[str, str] = {}
        for capability in BLACKBOX_CAPABILITIES:
            if capability not in advertised:
                reasons[capability] = "not advertised by the selected endpoint"
                continue
            if capability in {"agent_tasks", "github_operations", "remote_task_resumption"} and family != "enterprise" and self._PLAN_RANK[plan] < self._PLAN_RANK["pro"]:
                reasons[capability] = "requires a documented Agent API endpoint and eligible account plan"
                continue
            supported.add(capability)
        return BlackboxCapabilityResult(family, model, plan, frozenset(supported), reasons)
