"""Application boundary for digest-bound attestation verification.

The service converts verifier results and failures into a stable, redacted
activation-evidence record. Callers such as model validation, activation, API
handlers, and the GUI should use this boundary instead of invoking the
cryptographic verifier directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from .attestations import AttestationError, AttestationPolicy, TrustStore, verify_attestation


@dataclass(frozen=True)
class ActivationAttestationEvidence:
    """Persistable, secret-free evidence attached to one model activation."""

    subject_digest: str
    policy_id: str
    policy_mode: str
    verification_status: str
    verification_method: str
    diagnostic_code: str | None
    diagnostic_message: str | None
    issuer: str | None
    identity: str | None
    predicate_type: str | None
    signed_at: str | None
    expires_at: str | None
    source_uri: str | None
    verified_at: str
    stale: bool = False
    trust_root_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_digest": self.subject_digest,
            "policy_id": self.policy_id,
            "policy_mode": self.policy_mode,
            "verification_status": self.verification_status,
            "verification_method": self.verification_method,
            "diagnostic_code": self.diagnostic_code,
            "diagnostic_message": self.diagnostic_message,
            "issuer": self.issuer,
            "identity": self.identity,
            "predicate_type": self.predicate_type,
            "signed_at": self.signed_at,
            "expires_at": self.expires_at,
            "source_uri": self.source_uri,
            "verified_at": self.verified_at,
            "stale": self.stale,
            "trust_root_id": self.trust_root_id,
        }


class AttestationVerificationService:
    """Single application boundary for validation and activation evidence."""

    def __init__(self, trust_store: TrustStore | None = None) -> None:
        self.trust_store = trust_store

    @staticmethod
    def _policy(mode: str, policy_id: str | None = None) -> tuple[AttestationPolicy, str]:
        policy = AttestationPolicy(mode=mode)
        policy.validate()
        material = {
            "mode": policy.mode,
            "issuers": sorted(policy.trusted_issuers),
            "identities": sorted(policy.trusted_identities),
            "predicate": policy.require_predicate_type,
        }
        import hashlib
        import json
        computed = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()[:16]
        if policy_id and policy_id != computed:
            raise AttestationError("attestation policy identifier does not match policy contents")
        return policy, computed

    def verify(
        self,
        *,
        subject_digest: str,
        envelope: Mapping[str, Any] | None,
        policy_mode: str = "optional",
        policy_id: str | None = None,
        trust_root_id: str | None = None,
    ) -> ActivationAttestationEvidence:
        """Verify one model attestation and return stable activation evidence."""

        now = datetime.now(UTC).isoformat()
        try:
            policy, computed_policy_id = self._policy(policy_mode, policy_id)
            record = verify_attestation(
                envelope=envelope,
                subject_digest=subject_digest,
                policy=policy,
                trust_store=self.trust_store,
            )
            diagnostic_code = None
            diagnostic_message = None
            if record.verification_status != "verified":
                diagnostic_code = "attestation_missing" if not envelope else "attestation_unverified"
                diagnostic_message = f"attestation status is {record.verification_status}"
            return ActivationAttestationEvidence(
                subject_digest=subject_digest,
                policy_id=computed_policy_id,
                policy_mode=policy.mode,
                verification_status=record.verification_status,
                verification_method=record.verification_method,
                diagnostic_code=diagnostic_code,
                diagnostic_message=diagnostic_message,
                issuer=record.issuer or None,
                identity=record.identity,
                predicate_type=record.predicate_type or None,
                signed_at=record.signed_at,
                expires_at=record.expires_at,
                source_uri=record.source_uri,
                verified_at=now,
                trust_root_id=trust_root_id,
            )
        except AttestationError as exc:
            message = str(exc)
            code = "attestation_digest_mismatch" if "digest" in message else "attestation_rejected"
            if "missing" in message:
                code = "attestation_missing"
            if "expired" in message:
                code = "attestation_expired"
            if "trusted key" in message or "trust" in message:
                code = "trust_root_unavailable"
            computed = policy_id or self._policy(policy_mode)[1]
            return ActivationAttestationEvidence(
                subject_digest=subject_digest,
                policy_id=computed,
                policy_mode=policy_mode,
                verification_status="rejected",
                verification_method="detached-json",
                diagnostic_code=code,
                diagnostic_message=message,
                issuer=None,
                identity=None,
                predicate_type=None,
                signed_at=None,
                expires_at=None,
                source_uri=None,
                verified_at=now,
                trust_root_id=trust_root_id,
            )

    @staticmethod
    def activation_allowed(evidence: ActivationAttestationEvidence) -> bool:
        """Return whether evidence satisfies the selected activation policy."""

        if evidence.policy_mode in {"required", "required_tuf"}:
            return evidence.verification_status == "verified" and not evidence.stale
        return evidence.verification_status != "rejected" or evidence.policy_mode in {"off", "optional"}

    @staticmethod
    def invalidate(evidence: Mapping[str, Any], *, reason: str = "attestation_policy_changed") -> dict[str, Any]:
        """Mark persisted activation evidence stale without deleting its audit trail."""

        updated = dict(evidence)
        updated["stale"] = True
        updated["diagnostic_code"] = reason
        updated["diagnostic_message"] = reason
        return updated
