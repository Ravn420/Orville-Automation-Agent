"""Focused evidence tests for the observability and release-readiness slice."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orville_core.evaluation import evaluate_output
from orville_core.observability import JsonlTraceRecorder
from orville_core.production_metrics import HealthSummary
from orville_core.release_thresholds import ReleaseThresholds, evaluate_release_thresholds
from orville_core.security import SecretRedactor


ROOT = Path(__file__).resolve().parents[1]


def _summary(**overrides: object) -> HealthSummary:
    values = {
        "tenant_id": "test-tenant",
        "cohort": "canary",
        "release_id": "release-test",
        "sample_count": 10,
        "requests": 100.0,
        "errors": 2.0,
        "error_rate": 0.02,
        "latency_mean_ms": 100.0,
        "latency_p95_ms": 500.0,
        "saturation_mean": 0.40,
        "business_health": 0.95,
        "security_findings": 0.0,
        "release_quality": 0.98,
        "observed_at": 1.0,
    }
    values.update(overrides)
    return HealthSummary(**values)


def test_trace_recorder_persists_jsonl_and_redacts_sensitive_attributes(tmp_path: Path) -> None:
    path = tmp_path / "traces" / "run.jsonl"
    recorder = JsonlTraceRecorder(path, SecretRedactor())
    recorder.record("trace-1", "run.completed", {"api_key": "synthetic-secret", "status": "completed"})
    records = recorder.read()
    assert len(records) == 1
    assert records[0].attributes["api_key"] != "synthetic-secret"
    raw = path.read_text(encoding="utf-8")
    assert "synthetic-secret" not in raw
    assert json.loads(raw)["trace_id"] == "trace-1"


def test_evaluation_fixture_manifest_and_security_fixture_are_retained() -> None:
    manifest = json.loads((ROOT / "tests/fixtures/regressions/manifest.json").read_text(encoding="utf-8"))
    fixture_ids = {item["id"] for item in manifest["fixtures"]}
    assert {"scheduled-retry-same-slot", "workflow-dry-run-mutation", "nested-secret-redaction"} <= fixture_ids
    assert evaluate_output("safe output", ["safe output"]).passed
    assert SecretRedactor().redact({"authorization": "Bearer synthetic-token"})["authorization"] != "Bearer synthetic-token"


def test_release_thresholds_pass_and_fail_closed() -> None:
    decision = evaluate_release_thresholds(_summary())
    assert decision.passed is True
    assert all(decision.checks.values())
    failed = evaluate_release_thresholds(_summary(security_findings=1.0))
    assert failed.passed is False
    assert failed.checks["security_findings"] is False
    with pytest.raises(ValueError, match="max_error_rate"):
        ReleaseThresholds(max_error_rate=2).validate()
