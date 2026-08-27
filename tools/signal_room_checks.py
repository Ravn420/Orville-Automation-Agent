"""Static smoke, accessibility, and contrast checks for the bundled Signal Room UI."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _luminance(rgb: tuple[int, int, int]) -> float:
    values = []
    for channel in rgb:
        value = channel / 255
        values.append(value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def _contrast(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    light = max(_luminance(foreground), _luminance(background))
    dark = min(_luminance(foreground), _luminance(background))
    return (light + 0.05) / (dark + 0.05)


def _hex(value: str) -> tuple[int, int, int] | None:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    if len(value) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return None
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def audit_ui(root: Path) -> tuple[list[str], list[str]]:
    index = root / "index.html"
    css_files = list((root / "assets").glob("*.css"))
    if not index.is_file():
        return ["missing webui/index.html"], []
    html = index.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []
    for marker, message in ((r'<html\s+lang=["\']en', "missing English document language"), (r"<title>[^<]+</title>", "missing document title"), (r"name=[\"']viewport[\"']", "missing viewport metadata"), (r"<script[^>]+type=[\"']module[\"']", "missing module application script")):
        if not re.search(marker, html, re.IGNORECASE):
            errors.append(message)
    if not css_files:
        errors.append("missing bundled stylesheet")
    css = "\n".join(path.read_text(encoding="utf-8") for path in css_files)
    if "prefers-reduced-motion" not in css:
        errors.append("missing prefers-reduced-motion rule")
    if not re.search(r":focus(?:-visible)?\s*\{", css):
        errors.append("missing visible focus rule")
    pairs = re.findall(r"color:\s*(#[0-9a-fA-F]{6})[^}]*background(?:-color)?:\s*(#[0-9a-fA-F]{6})", css, re.IGNORECASE | re.DOTALL)
    for foreground_value, background_value in pairs:
        foreground, background = _hex(foreground_value), _hex(background_value)
        if foreground and background and _contrast(foreground, background) < 4.5:
            warnings.append(f"foreground {foreground_value} and background {background_value} fail WCAG AA normal-text contrast")
    return errors, warnings


def check_ui(root: Path) -> list[str]:
    """Return blocking UI smoke/accessibility failures; contrast findings are reported separately."""
    errors, _warnings = audit_ui(root)
    return errors


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0]).resolve() if argv else Path(__file__).resolve().parents[1] / "webui"
    errors, warnings = audit_ui(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: Signal Room smoke and accessibility checks ({root})")
    for warning in warnings:
        print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
