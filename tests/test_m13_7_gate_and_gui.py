from pathlib import Path

from orville_core import run_security_gate


def test_security_gate_consumes_all_required_results(tmp_path):
    for name in ("sandbox.py", "attestations.py", "tuf_metadata.py"):
        path = tmp_path / "orville_core" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic", encoding="utf-8")
    passed = run_security_gate(
        root=tmp_path,
        sandbox_available=True,
        required_attestation_verified=True,
        dependency_names=("json",),
        audit_evidence_present=True,
    )
    assert passed.passed is True
    failed = run_security_gate(
        root=tmp_path,
        sandbox_available=False,
        required_attestation_verified=False,
        dependency_names=("module_that_does_not_exist",),
        audit_evidence_present=False,
    )
    assert failed.passed is False
    assert len(failed.diagnostics) == 4


def test_security_gate_requires_security_sources(tmp_path):
    result = run_security_gate(
        root=tmp_path,
        sandbox_available=True,
        required_attestation_verified=True,
        dependency_names=(),
        audit_evidence_present=True,
    )
    assert result.checks["security_sources_present"] is False
    assert result.passed is False
