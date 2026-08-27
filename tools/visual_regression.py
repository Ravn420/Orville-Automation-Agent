"""Deterministic structural visual-regression checks for Orville GUI assets.

This checker intentionally avoids screenshots and browser credentials. It fingerprints
reviewed design tokens and critical mockup structure so changes require an explicit
baseline update and review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "tests" / "fixtures" / "visual_regression_baseline.json"


class _MarkupFingerprint(HTMLParser):
    """Collect stable semantic structure without text or attribute noise."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.roles: list[str] = []
        self.labels: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        attributes = dict(attrs)
        if attributes.get("role"):
            self.roles.append(str(attributes["role"]))
        if attributes.get("aria-label"):
            self.labels.append(str(attributes["aria-label"]))


def _sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def collect_snapshot(root: Path = ROOT) -> dict[str, Any]:
    """Return a stable review snapshot for the design system and critical screen."""
    design = json.loads((root / "config" / "design-system.example.json").read_text(encoding="utf-8"))
    markup = _MarkupFingerprint()
    markup.feed((root / "docs" / "mockups" / "orville-control-center.html").read_text(encoding="utf-8"))
    required_tokens = {
        "typography": design.get("typography"),
        "color_roles": sorted((design.get("color", {}) or {}).keys()),
        "spacing": design.get("spacing"),
        "breakpoints": design.get("responsive", {}).get("breakpoints") if isinstance(design.get("responsive"), dict) else None,
        "motion": design.get("motion"),
    }
    structure = {
        "tags": markup.tags,
        "roles": sorted(markup.roles),
        "aria_labels": sorted(markup.labels),
        "required_markers": sorted(marker for marker in ("prefers-reduced-motion", "max-width:980px", "max-width:790px", "data-theme", "aria-pressed") if marker in (root / "docs" / "mockups" / "orville-control-center.html").read_text(encoding="utf-8")),
    }
    return {
        "schema": 1,
        "design_hash": _sha256(required_tokens),
        "structure_hash": _sha256(structure),
        "design": required_tokens,
        "structure": structure,
    }


def check_baseline(baseline_path: Path = DEFAULT_BASELINE, root: Path = ROOT) -> tuple[bool, dict[str, Any], str]:
    """Compare the current snapshot with the reviewed baseline."""
    current = collect_snapshot(root)
    expected = json.loads(baseline_path.read_text(encoding="utf-8"))
    if current == expected:
        return True, current, "visual regression baseline passed"
    return False, current, "visual regression changed; review and explicitly update the baseline"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Orville visual-regression baseline")
    parser.add_argument("command", choices=("snapshot", "check"))
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    args = parser.parse_args()
    if args.command == "snapshot":
        print(json.dumps(collect_snapshot(), indent=2, sort_keys=True))
        return 0
    passed, _current, message = check_baseline(args.baseline)
    print(message)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
