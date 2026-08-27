"""Focused contract tests for unavailable connector and website behavior."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "GRACEFUL_DEGRADATION.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def test_degraded_document_defines_stable_dependency_states_and_safe_responses() -> None:
    text = _read()
    for state in ("connector_unavailable", "website_unavailable", "provider_unavailable", "partial_dependency", "offline"):
        assert state in text
    for term in ("save a resumable draft", "local/manual alternative", "safe recovery action", "plain-language explanation"):
        assert term in text


def test_degraded_document_preserves_state_and_blocks_unsafe_fallbacks() -> None:
    text = _read()
    for term in ("objective", "task graph", "checkpoint", "local artifacts", "transformation history", "blocked", "partial"):
        assert term in text
    for term in ("must not silently switch accounts", "bypass authentication", "same privacy class", "permission check"):
        assert term in text


def test_degraded_document_defines_bounded_retries_partial_evidence_and_security() -> None:
    text = _read()
    for term in ("Retries are bounded", "idempotency key", "Partial results", "Independent verification", "authorization headers", "session cookies", "explicit scope-matched approval"):
        assert term in text
    assert "Live connector recovery" in text
