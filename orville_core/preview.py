"""Revision-pinned preview and visual-context contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Preview:
    preview_id: str
    revision_id: str
    root: str
    route: str = "/"
    viewport: str = "desktop"
    status: str = "ready"
    url: str | None = None


@dataclass(frozen=True)
class ElementContext:
    element_id: str
    route: str
    component: str | None
    source_file: str | None
    line_start: int | None
    line_end: int | None
    selector: str
    computed_styles: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class StylePatch:
    property: str
    value: str
    previous_value: str | None = None


@dataclass(frozen=True)
class SmokeReport:
    preview_id: str
    passed: bool
    route: str
    viewport: str
    console_errors: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()


class PreviewManager:
    ALLOWED_VIEWPORTS = frozenset({"desktop", "mobile", "tablet"})

    def create(self, preview_id: str, revision_id: str, root: str | Path, *, route: str = "/", viewport: str = "desktop") -> Preview:
        if viewport not in self.ALLOWED_VIEWPORTS:
            raise ValueError(f"unsupported viewport: {viewport}")
        root_path = Path(root).expanduser().resolve()
        if not root_path.is_dir():
            raise FileNotFoundError(str(root_path))
        if not route.startswith("/"):
            raise ValueError("route must start with '/'")
        return Preview(preview_id, revision_id, str(root_path), route, viewport)

    def select_element(self, *, element_id: str, route: str, selector: str, component: str | None = None, source_file: str | None = None, line_start: int | None = None, line_end: int | None = None, computed_styles: dict[str, str] | None = None) -> ElementContext:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", element_id):
            raise ValueError("element_id contains unsupported characters")
        if not selector.strip():
            raise ValueError("selector must not be empty")
        return ElementContext(element_id, route, component, source_file, line_start, line_end, selector, computed_styles or {})

    def style_patch(self, context: ElementContext, property: str, value: str) -> StylePatch:
        allowed = {"color", "background-color", "font-size", "font-weight", "margin", "padding", "border-radius", "border", "display", "gap", "width", "height", "text-align"}
        if property not in allowed:
            raise ValueError(f"style property requires agent review: {property}")
        if not value.strip() or ";" in value or "url(" in value.lower():
            raise ValueError("style value is not a safe deterministic value")
        return StylePatch(property, value.strip(), context.computed_styles.get(property))

    def smoke_report(self, preview: Preview, *, console_errors: list[str] | None = None, steps: list[str] | None = None) -> SmokeReport:
        errors = tuple(console_errors or [])
        return SmokeReport(preview.preview_id, not errors, preview.route, preview.viewport, errors, tuple(steps or ["preview opened", "route selected"]))
