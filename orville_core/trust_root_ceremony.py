"""Approval-gated production trust-root ceremony workflow.

The workflow validates a signed TUF root, requires an independently supplied
canonical digest, records operator approvals and evidence atomically, and
supports rotation/revocation metadata without storing credentials. It never
contacts a remote service or promotes a root automatically.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .tuf_metadata import TufRepositoryVerifier, TufVerificationError


class TrustRootCeremonyError(ValueError):
    """Raised when a production trust-root ceremony cannot proceed safely."""


def canonical_digest(root: Mapping[str, Any]) -> str:
    """Return the pinned digest representation used by the ceremony."""
    canonical = json.dumps(root, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class CeremonyApproval:
    operator_id: str
    approval_reference: str
    approved_at: str
    out_of_band_digest: str
    reason: str

    def validate(self) -> None:
        if not self.operator_id.strip() or not self.approval_reference.strip() or not self.reason.strip():
            raise TrustRootCeremonyError("operator_id, approval_reference, and reason are required")
        if len(self.out_of_band_digest) != 64 or any(char not in "0123456789abcdefABCDEF" for char in self.out_of_band_digest):
            raise TrustRootCeremonyError("out_of_band_digest must be a SHA-256 hex digest")
        try:
            datetime.fromisoformat(self.approved_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise TrustRootCeremonyError("approved_at must be an ISO-8601 timestamp") from exc


class ProductionTrustRootCeremony:
    """Prepare and commit trust-root changes only with explicit evidence."""

    def __init__(self, trust_store_path: str | Path, evidence_path: str | Path) -> None:
        self.trust_store_path = Path(trust_store_path).expanduser().resolve()
        self.evidence_path = Path(evidence_path).expanduser().resolve()

    def _write_atomic(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def _record(self, action: str, status: str, root: Mapping[str, Any], approval: CeremonyApproval, previous_digest: str | None = None) -> dict[str, Any]:
        approval.validate()
        digest = canonical_digest(root)
        if digest.lower() != approval.out_of_band_digest.lower():
            raise TrustRootCeremonyError("root digest does not match the independent out-of-band digest")
        signed = root.get("signed") if isinstance(root, Mapping) else None
        version = int(signed.get("version", 0)) if isinstance(signed, Mapping) else 0
        evidence = {
            "schema": "orville.production-trust-root-ceremony",
            "action": action,
            "status": status,
            "root_version": version,
            "root_sha256": digest,
            "previous_root_sha256": previous_digest,
            "operator_id": approval.operator_id,
            "approval_reference": approval.approval_reference,
            "approved_at": approval.approved_at,
            "reason": approval.reason,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        self._write_atomic(self.evidence_path, evidence)
        return evidence

    def bootstrap(self, root: Mapping[str, Any], approval: CeremonyApproval) -> dict[str, Any]:
        if self.trust_store_path.exists():
            raise TrustRootCeremonyError("trust root already exists; use rotate for an existing store")
        approval.validate()
        try:
            TufRepositoryVerifier.bootstrap(self.trust_store_path, root, approved=True, expected_sha256=approval.out_of_band_digest)
        except (OSError, ValueError, TufVerificationError) as exc:
            raise TrustRootCeremonyError(str(exc)) from exc
        return self._record("bootstrap", "committed", root, approval)

    def rotate(self, root: Mapping[str, Any], approval: CeremonyApproval) -> dict[str, Any]:
        if not self.trust_store_path.exists():
            raise TrustRootCeremonyError("cannot rotate a missing trust root; bootstrap first")
        approval.validate()
        try:
            verifier = TufRepositoryVerifier.load(self.trust_store_path)
            previous_digest = canonical_digest(verifier.root_metadata)
            verifier.rotate_root(root, approved=True)
            self._write_atomic(self.trust_store_path, verifier.root_metadata)
        except (OSError, ValueError, TufVerificationError) as exc:
            raise TrustRootCeremonyError(str(exc)) from exc
        return self._record("rotate", "committed", root, approval, previous_digest)

    def revoke(self, approval: CeremonyApproval, reason: str) -> dict[str, Any]:
        if not self.trust_store_path.exists():
            raise TrustRootCeremonyError("cannot revoke a missing trust root")
        approval.validate()
        if not reason.strip():
            raise TrustRootCeremonyError("revocation reason is required")
        current = json.loads(self.trust_store_path.read_text(encoding="utf-8"))
        digest = canonical_digest(current)
        if digest.lower() != approval.out_of_band_digest.lower():
            raise TrustRootCeremonyError("revocation digest does not match the independent out-of-band digest")
        record = self._record("revoke", "recorded", current, approval)
        record["revocation_reason"] = reason
        self._write_atomic(self.evidence_path, record)
        return record

    def status(self) -> dict[str, Any]:
        if not self.evidence_path.exists():
            return {"status": "not_initialized", "trust_store_exists": self.trust_store_path.exists()}
        evidence = json.loads(self.evidence_path.read_text(encoding="utf-8"))
        return {"status": evidence.get("status", "unknown"), "action": evidence.get("action"), "root_version": evidence.get("root_version"), "root_sha256": evidence.get("root_sha256"), "trust_store_exists": self.trust_store_path.exists()}
