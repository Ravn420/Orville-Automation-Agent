"""Focused tests for local dependency and supply-chain review."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from orville_core import SupplyChainReview, review_downloaded_file
from orville_core.security import SecurityViolation


def _fixture_file(tmp_path: Path, name: str = "package.whl") -> tuple[Path, str]:
    path = tmp_path / "review" / name
    path.parent.mkdir()
    path.write_bytes(b"synthetic package content")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_approved_package_requires_matching_checksum_and_provenance(tmp_path: Path) -> None:
    path, digest = _fixture_file(tmp_path)
    review = review_downloaded_file(path, kind="package", allowed_roots=(path.parent,), expected_sha256=digest, provenance="fixture://package-1")
    assert isinstance(review, SupplyChainReview)
    assert review.status == "approved"
    assert review.execution_allowed is True
    assert review.sha256 == digest
    assert review.metadata == {"content_read_for_hash_only": True, "network_accessed": False}


def test_missing_or_mismatched_integrity_evidence_blocks_use(tmp_path: Path) -> None:
    path, digest = _fixture_file(tmp_path)
    missing = review_downloaded_file(path, kind="artifact", allowed_roots=(path.parent,), provenance="fixture://artifact")
    assert missing.status == "blocked"
    assert missing.execution_allowed is False
    assert "checksum is required" in missing.findings[0]
    mismatch = review_downloaded_file(path, kind="package", allowed_roots=(path.parent,), expected_sha256="0" * 64, provenance="fixture://package")
    assert mismatch.status == "blocked"
    assert any("does not match" in finding for finding in mismatch.findings)
    assert digest not in mismatch.findings


def test_scripts_require_independent_review_and_never_execute(tmp_path: Path) -> None:
    path, digest = _fixture_file(tmp_path, "tool.py")
    pending = review_downloaded_file(path, kind="script", allowed_roots=(path.parent,), expected_sha256=digest, provenance="fixture://tool")
    assert pending.status == "blocked"
    assert pending.execution_allowed is False
    assert "independent review" in pending.findings[0]
    approved = review_downloaded_file(path, kind="script", allowed_roots=(path.parent,), expected_sha256=digest, provenance="fixture://tool", reviewed=True)
    assert approved.status == "approved"
    assert approved.execution_allowed is True


def test_outside_root_and_invalid_kind_fail_closed(tmp_path: Path) -> None:
    path, _ = _fixture_file(tmp_path)
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    with pytest.raises(SecurityViolation):
        review_downloaded_file(outside, kind="artifact", allowed_roots=(path.parent,))
    with pytest.raises(ValueError):
        review_downloaded_file(path, kind="unknown", allowed_roots=(path.parent,))
