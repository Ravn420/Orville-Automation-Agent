"""Focused contract checks for supported deployment targets and runtime variables."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "DEPLOYMENT_TARGETS_AND_ENVIRONMENT.md"
ENV_TEMPLATE = ROOT / ".env.example"


def _document() -> str:
    return DOC.read_text(encoding="utf-8")


def _env_names() -> set[str]:
    return set(re.findall(r"^([A-Z][A-Z0-9_]+)=", ENV_TEMPLATE.read_text(encoding="utf-8"), re.MULTILINE))


def test_supported_target_matrix_covers_local_windows_portable_and_compose() -> None:
    document = _document()
    for target in (
        "Local Python process",
        "Windows installed release",
        "Windows portable release",
        "Docker Compose small-team topology",
        "Disposable container check",
    ):
        assert target in document
    assert "Kubernetes" in document and "serverless" in document
    assert "does **not** claim" in document


def test_runtime_variables_are_documented_and_match_template() -> None:
    document = _document()
    documented = set(re.findall(r"`(ORVILLE_[A-Z0-9_]+|GEMINI_API_KEY|OLLAMA_BASE_URL|OLLAMA_MODEL)`", document))
    template_names = _env_names()
    assert {"ORVILLE_API_TOKEN", "ORVILLE_API_HOST", "ORVILLE_API_PORT", "ORVILLE_STORAGE", "ORVILLE_DB_PATH", "ORVILLE_ALLOWED_ORIGINS", "ORVILLE_REQUESTS_PER_MINUTE"} <= documented
    assert documented <= template_names


def test_secret_and_production_boundaries_are_explicit() -> None:
    document = _document()
    assert "`ORVILLE_API_TOKEN` is the only mandatory process variable" in document
    assert "must never be committed" in document
    assert "credential belongs only on the relay server" in document
    assert "inject secrets through the deployment secret manager" in document
    assert "avoid scaling SQLite-backed API processes beyond one replica" in document
