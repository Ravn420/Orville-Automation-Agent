"""Signal Room-safe projection for browser session controls."""
from __future__ import annotations

from typing import Any, Mapping


def browser_signal_room_projection(session: Mapping[str, Any]) -> dict[str, Any]:
    """Return UI-safe browser state; never expose handles, secrets, or raw payloads."""
    status = str(session.get("status", "unknown"))
    takeover_required = bool(session.get("takeover_required", False))
    actions = ["refresh", "close"]
    if takeover_required:
        actions.append("request_takeover")
    if status in {"active", "user_takeover"}:
        actions.extend(["extract", "screenshot"])
    return {"session_id": str(session.get("session_id", "")), "status": status, "current_url": session.get("current_url"), "title": session.get("title"), "takeover_required": takeover_required, "allowed_domains": list(session.get("allowed_domains", []))[:100], "available_actions": actions, "audit_count": min(len(session.get("audit", []) or []), 100)}


def validate_signal_room_action(action: str, *, approved: bool = False) -> None:
    if action not in {"refresh", "close", "request_takeover", "extract", "screenshot"}:
        raise ValueError("unsupported browser Signal Room action")
    if action == "request_takeover" and not approved:
        raise PermissionError("takeover action requires explicit approval")
