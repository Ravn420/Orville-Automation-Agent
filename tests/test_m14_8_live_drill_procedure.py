"""Contract tests for the M14.8 approval-gated live-drill procedure."""

from __future__ import annotations

import re
from pathlib import Path


DOCUMENT = Path(__file__).resolve().parents[1] / "docs" / "M14_8_LIVE_DRILL_PROCEDURE.md"


def test_m14_8_procedure_defines_all_dependency_and_fault_gates() -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    for phrase in (
        "M14.2 trust root",
        "M14.3 sandbox",
        "M14.4 identity",
        "M14.5 secrets",
        "M14.6 deployment adapter",
        "M14.7 metrics",
        "Restart",
        "Duplicate event",
        "Partial failure",
        "Injected release-health fault",
        "Rollback failure",
        "Deterministic recovery",
    ):
        assert phrase in text


def test_m14_8_procedure_remains_non_production_and_approval_gated() -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    for phrase in (
        "This document authorizes neither deployment nor production traffic.",
        "All entries must be marked **complete**",
        "a missing owner, approval, telemetry source, rollback target, secret boundary, or evidence location stops the drill",
        "Never use production credentials, production tenants, production data, or a production traffic route",
        "no production action was performed",
    ):
        assert phrase in text
    assert not re.search(r"(?i)sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{8,}|api[_-]?key\s*=\s*[^\s,]+", text)


def test_m14_8_procedure_uses_supported_local_validation_commands() -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    for command in (
        "python tools/deployment_validation.py preflight --target",
        "python tools/m13_12_fault_runner.py --output logs/m13_12_fault_injection.json",
    ):
        assert command in text
