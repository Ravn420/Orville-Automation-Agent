"""Accessible, text-first status announcements for GUI workflow updates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .gui_state import WORKFLOW_STATE_COPY, state_message


@dataclass(frozen=True)
class AccessibleStatus:
    state: str
    role: str
    live: str
    text: str
    color_independent: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state, "role": self.role, "live": self.live, "text": self.text, "color_independent": self.color_independent}


def accessible_status(state: str, *, urgent: bool = False) -> AccessibleStatus:
    normalized = state.strip().lower()
    if normalized not in WORKFLOW_STATE_COPY:
        normalized = "failed"
    return AccessibleStatus(normalized, "alert" if urgent else "status", "assertive" if urgent else "polite", state_message(normalized))
