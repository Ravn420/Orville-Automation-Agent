"""Risk registry component.

A minimal implementation that records risk entries and serialises them to JSON.
This acts as a placeholder for the future comprehensive risk‑management
framework.  It is intentionally lightweight to avoid pulling in external
dependencies and to keep tests fast.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

import json

__all__ = ["Risk", "RiskRegistry"]


@dataclass
class Risk:
    """A single risk entry.

    Parameters
    ----------
    id:
        Unique identifier for the risk.  In a real system this might be a UUID
        or a human‑readable short string.
    owner:
        The person or group responsible for mitigating the risk.
    description:
        Textual description, used for logging and reporting.
    likelihood:
        One of ``"low"``, ``"medium"`` or ``"high"``.
    impact:
        Same scale as likelihood.
    mitigation:
        Brief text describing the mitigation plan.
    residual:
        Mitigation outcome – ``"none"``, ``"partial"`` or ``"none"``.
    review_date:
        ISO‑8601 date when the risk should next be reviewed.
    evidence_file:
        Optional path to a supporting document that can be stored
        separately.  The registry only stores the path.
    """

    id: str
    owner: str
    description: str
    likelihood: str
    impact: str
    mitigation: str
    residual: str
    review_date: str
    evidence_file: str | None = None

    def validate(self) -> None:
        valid_levels = {"low", "medium", "high"}
        if self.likelihood not in valid_levels:
            raise ValueError("likelihood must be one of %r" % valid_levels)
        if self.impact not in valid_levels:
            raise ValueError("impact must be one of %r" % valid_levels)
        # Basic ISO date check – a full ISO validator is overkill here
        try:
            datetime.fromisoformat(self.review_date)
        except Exception as exc:  # pragma: no cover
            raise ValueError("review_date must be ISO‑8601 date") from exc

    def to_dict(self) -> dict:
        self.validate()
        return asdict(self)


class RiskRegistry:
    """Simple persistence layer for risks.

    The registry writes a JSON array to a file on ``commit``.  Since the
    repository is small, each ``commit`` overwrites the file; there is no
    versioning or diff support.
    """

    def __init__(self, path: Path | str = "risky.json") -> None:
        self._path = Path(path)
        self._risks: List[Risk] = []

    @property
    def risks(self) -> Iterable[Risk]:
        return iter(self._risks)

    def add(self, risk: Risk) -> None:
        risk.validate()
        self._risks.append(risk)

    def commit(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([r.to_dict() for r in self._risks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self) -> None:
        if not self._path.exists():
            self._risks = []
            return
        data = json.loads(self._path.read_text(encoding="utf-8"))
        self._risks = [Risk(**item) for item in data]

    def snapshot(self) -> Dict[str, List[dict]]:
        return {"risks": [r.to_dict() for r in self._risks]}
