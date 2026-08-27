"""Localization-ready user-visible text resources.

Business logic should emit stable message keys and parameters. Presentation layers
resolve those keys through :class:`TextCatalog` instead of embedding user-visible
copy in orchestration or domain code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


DEFAULT_LOCALE = "en-US"


class TextCatalog:
    """Resolve stable text keys from locale resources with deterministic fallback."""

    def __init__(self, resources_dir: Path, locale: str = DEFAULT_LOCALE) -> None:
        self.resources_dir = resources_dir
        self.locale = locale
        self._messages = self._load(locale)
        self._fallback = self._load(DEFAULT_LOCALE) if locale != DEFAULT_LOCALE else self._messages

    def _load(self, locale: str) -> dict[str, str]:
        path = self.resources_dir / f"{locale}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        if not isinstance(payload, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in payload.items()
        ):
            raise ValueError(f"Invalid localization resource: {path.name}")
        return payload

    def text(self, key: str, parameters: Mapping[str, object] | None = None) -> str:
        """Return localized text, falling back safely when a translation is absent."""
        template = self._messages.get(key, self._fallback.get(key))
        if template is None:
            return key
        values = dict(parameters or {})
        try:
            return template.format_map(_SafeParameters(values))
        except (KeyError, ValueError):
            return template


class _SafeParameters(dict[str, object]):
    """Leave unknown placeholders visible instead of raising in user feedback."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def default_catalog(root: Path | None = None, locale: str = DEFAULT_LOCALE) -> TextCatalog:
    """Build a catalog from the repository's non-secret locale resources."""
    base = root or Path(__file__).resolve().parents[1]
    return TextCatalog(base / "config" / "locales", locale=locale)
