"""Digest-bound attestation verification with local trust management.

The verifier accepts detached JSON in-toto/DSSE-shaped envelopes and uses the
optional ``cryptography`` package for Ed25519 verification. Trust changes are
explicit, persisted, and approval-gated. No downloaded code is executed.
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class AttestationPolicy:
    """Trust policy applied to a detached attestation."""

    mode: str = "optional"
    trusted_issuers: frozenset[str] = frozenset()
    trusted_identities: frozenset[str] = frozenset()
    require_predicate_type: str | None = None

    def validate(self) -> None:
        if self.mode not in {"off", "optional", "required", "required_tuf"}:
            raise ValueError("attestation mode must be off, optional, required, or required_tuf")


@dataclass(frozen=True)
class AttestationRecord:
    subject_digest: str
    predicate_type: str
    issuer: str
    identity: str | None
    signed_at: str | None
    expires_at: str | None
    source_uri: str | None
    verification_method: str
    verification_status: str
    policy_id: str
    predicate: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"subject_digest": self.subject_digest, "predicate_type": self.predicate_type, "issuer": self.issuer, "identity": self.identity, "signed_at": self.signed_at, "expires_at": self.expires_at, "source_uri": self.source_uri, "verification_method": self.verification_method, "verification_status": self.verification_status, "policy_id": self.policy_id, "predicate": dict(self.predicate)}


class AttestationError(ValueError):
    """Raised when an attestation is malformed or fails a required policy."""


class TrustStore:
    """Small JSON trust store with explicit bootstrap, rotation, and revocation."""

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser().resolve()
        self._data: dict[str, Any] = {"version": 1, "keys": {}}
        if self.path.exists():
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict) or loaded.get("version") != 1 or not isinstance(loaded.get("keys"), dict):
                raise AttestationError("trust store has an unsupported format")
            self._data = loaded

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(self._data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    @classmethod
    def bootstrap(cls, path: Path, roots: Mapping[str, str], *, approved: bool = False) -> "TrustStore":
        if not approved:
            raise AttestationError("trust-store bootstrap requires explicit approval")
        store = cls(path)
        for issuer, public_key in roots.items():
            if not issuer or not public_key:
                raise AttestationError("trust-store roots require issuer and public key")
            store._data["keys"][issuer] = {"public_key": public_key, "active": True, "version": 1, "rotated_at": datetime.now(UTC).isoformat()}
        store._save()
        return store

    def rotate(self, issuer: str, public_key: str, *, approved: bool = False) -> None:
        if not approved:
            raise AttestationError("trust-key rotation requires explicit approval")
        if not issuer or not public_key:
            raise AttestationError("trust-key rotation requires issuer and public key")
        previous = self._data["keys"].get(issuer, {})
        self._data["keys"][issuer] = {"public_key": public_key, "active": True, "version": int(previous.get("version", 0)) + 1, "previous_public_key": previous.get("public_key"), "rotated_at": datetime.now(UTC).isoformat()}
        self._save()

    def revoke(self, issuer: str, *, approved: bool = False) -> None:
        if not approved:
            raise AttestationError("trust-key revocation requires explicit approval")
        entry = self._data["keys"].get(issuer)
        if not entry:
            raise AttestationError("cannot revoke an unknown trust key")
        entry["active"] = False
        entry["revoked_at"] = datetime.now(UTC).isoformat()
        self._save()

    def resolve_public_key(self, issuer: str) -> str:
        entry = self._data["keys"].get(issuer)
        if not entry or not entry.get("active"):
            raise AttestationError("attestation issuer has no active trusted key")
        return str(entry["public_key"])

    def issuers(self) -> tuple[str, ...]:
        return tuple(sorted(issuer for issuer, entry in self._data["keys"].items() if entry.get("active")))


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _policy_id(policy: AttestationPolicy) -> str:
    material = json.dumps({"mode": policy.mode, "issuers": sorted(policy.trusted_issuers), "identities": sorted(policy.trusted_identities), "predicate": policy.require_predicate_type}, sort_keys=True).encode()
    return sha256(material).hexdigest()[:16]


def _payload(envelope: Mapping[str, Any]) -> tuple[Any, str]:
    payload = envelope.get("payload")
    if isinstance(payload, str) and envelope.get("payload_encoding") == "base64":
        payload = json.loads(base64.b64decode(payload).decode("utf-8"))
    method = "cosign-in-toto-dsse" if envelope.get("payloadType") or envelope.get("signatures") else "ed25519-dsse"
    if payload is None:
        raise AttestationError("attestation payload is missing")
    return payload, method


def verify_cosign_attestation(*, subject_ref: str, key_path: Path, policy_path: Path | None = None, executable: str | None = None, timeout_seconds: int = 30) -> Mapping[str, Any]:
    """Run a locally installed Cosign verifier without shell or network defaults.

    The caller must provide a reviewed key and subject reference. The returned
    JSON is still passed through :func:`verify_attestation` for digest and policy
    binding; a successful process exit alone is never considered sufficient.
    """

    if not subject_ref or not key_path.is_file():
        raise AttestationError("Cosign verification requires a subject reference and existing key file")
    cosign = executable or shutil.which("cosign")
    if not cosign:
        raise AttestationError("Cosign executable is unavailable")
    argv = [cosign, "verify-attestation", "--key", str(key_path), "--output", "json"]
    if policy_path is not None:
        if not policy_path.is_file():
            raise AttestationError("Cosign policy file does not exist")
        argv.extend(("--policy", str(policy_path)))
    argv.append(subject_ref)
    try:
        completed = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AttestationError(f"Cosign verification could not complete: {exc}") from exc
    if completed.returncode != 0:
        raise AttestationError("Cosign rejected the attestation")
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AttestationError("Cosign returned malformed JSON") from exc
    if not isinstance(value, Mapping):
        raise AttestationError("Cosign returned an unsupported attestation shape")
    return value


def verify_attestation(*, envelope: Mapping[str, Any] | None, subject_digest: str, policy: AttestationPolicy, trust_store: TrustStore | None = None) -> AttestationRecord:
    """Verify an in-toto/DSSE-shaped envelope against a model digest and policy."""

    policy.validate()
    policy_id = _policy_id(policy)
    if policy.mode == "off" and not envelope:
        return AttestationRecord(subject_digest, "", "", None, None, None, None, "disabled", "unverified", policy_id)
    if not envelope:
        status = "unverified" if policy.mode == "optional" else "rejected"
        record = AttestationRecord(subject_digest, "", "", None, None, None, None, "detached-json", status, policy_id)
        if policy.mode in {"required", "required_tuf"}:
            raise AttestationError("required attestation is missing")
        return record
    subject = str(envelope.get("subject_digest", ""))
    issuer = str(envelope.get("issuer", ""))
    identity = str(envelope.get("identity")) if envelope.get("identity") is not None else None
    predicate_type = str(envelope.get("predicate_type") or envelope.get("predicateType") or "")
    signature = str(envelope.get("signature") or ((envelope.get("signatures") or [{}])[0].get("sig", "")))
    public_key = str(envelope.get("public_key", ""))
    signed_payload: Any = None
    method = "detached-json"
    try:
        if subject != subject_digest:
            raise AttestationError("attestation subject digest does not match model checksum")
        signed_payload, method = _payload(envelope)
        if policy.trusted_issuers and issuer not in policy.trusted_issuers:
            raise AttestationError("attestation issuer is not trusted by the active policy")
        if policy.trusted_identities and identity not in policy.trusted_identities:
            raise AttestationError("attestation identity is not trusted by the active policy")
        if policy.require_predicate_type and predicate_type != policy.require_predicate_type:
            raise AttestationError("attestation predicate type is not accepted by the active policy")
        expires = _parse_time(str(envelope.get("expires_at"))) if envelope.get("expires_at") else None
        if expires and expires <= datetime.now(UTC):
            raise AttestationError("attestation has expired")
        if trust_store is not None:
            trusted_key = trust_store.resolve_public_key(issuer)
            if public_key and public_key != trusted_key:
                raise AttestationError("attestation public key does not match the trusted issuer key")
            public_key = trusted_key
        if not signature or not public_key:
            raise AttestationError("attestation signature or trusted public key is missing")
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        except ImportError as exc:
            raise AttestationError("cryptography package is unavailable for attestation verification") from exc
        message = json.dumps(signed_payload, sort_keys=True, separators=(",", ":")).encode()
        Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key)).verify(base64.b64decode(signature), message)
        status = "verified"
    except (ValueError, TypeError, AttestationError) as exc:
        record = AttestationRecord(subject_digest, predicate_type, issuer, identity, envelope.get("signed_at"), envelope.get("expires_at"), envelope.get("source_uri"), method, "rejected", policy_id, signed_payload if isinstance(signed_payload, Mapping) else {})
        if policy.mode in {"required", "required_tuf"}:
            raise AttestationError(str(exc)) from exc
        return record
    return AttestationRecord(subject_digest, predicate_type, issuer, identity, envelope.get("signed_at"), envelope.get("expires_at"), envelope.get("source_uri"), method, status, policy_id, signed_payload if isinstance(signed_payload, Mapping) else {})
