"""Minimal fail-closed TUF metadata verifier for model repositories.

The implementation verifies signed root, timestamp, snapshot, and targets
metadata, enforces expiry/version/hash/length checks, and never downloads or
executes repository content. It uses Ed25519 from the optional cryptography
package and is intentionally limited to the metadata needed for model targets.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


class TufVerificationError(ValueError):
    """Raised when TUF metadata cannot satisfy the active trust policy."""


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _decode(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise TufVerificationError("TUF signature or key is not valid base64") from exc


def _expiry(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError as exc:
        raise TufVerificationError("TUF metadata expiry is malformed") from exc


def _verify_signature(metadata: Mapping[str, Any], key: Mapping[str, Any], signature: str) -> None:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise TufVerificationError("cryptography package is unavailable for TUF verification") from exc
    public = ((key.get("keyval") or {}).get("public"))
    if not public or key.get("scheme") not in {"ed25519", "ed25519-sha256"}:
        raise TufVerificationError("unsupported TUF key scheme")
    try:
        Ed25519PublicKey.from_public_bytes(_decode(str(public))).verify(_decode(signature), _canonical(metadata["signed"]))
    except (KeyError, ValueError) as exc:
        raise TufVerificationError("TUF signature verification failed") from exc


def _verify_role(metadata: Mapping[str, Any], root: Mapping[str, Any], role_name: str) -> None:
    signed = metadata.get("signed")
    signatures = metadata.get("signatures")
    if not isinstance(signed, Mapping) or not isinstance(signatures, Mapping):
        raise TufVerificationError(f"{role_name} metadata is not a signed TUF envelope")
    role = ((root.get("signed") or {}).get("roles") or {}).get(role_name)
    if not isinstance(role, Mapping):
        raise TufVerificationError(f"TUF root does not define role {role_name}")
    keys = (root.get("signed") or {}).get("keys") or {}
    valid = 0
    for key_id in role.get("keyids", []):
        signature = signatures.get(key_id, {}).get("sig") if isinstance(signatures.get(key_id), Mapping) else None
        key = keys.get(key_id)
        if not signature or not isinstance(key, Mapping):
            continue
        try:
            _verify_signature(metadata, key, str(signature))
            valid += 1
        except TufVerificationError:
            continue
    if valid < int(role.get("threshold", 1)):
        raise TufVerificationError(f"TUF role {role_name} did not meet its signature threshold")


def _verify_metadata_file(path: Path, metadata: Mapping[str, Any], label: str) -> None:
    if not path.is_file():
        raise TufVerificationError(f"TUF {label} metadata file is missing")
    meta = metadata if isinstance(metadata, Mapping) else {}
    expected_length = meta.get("length")
    if expected_length is not None and path.stat().st_size != int(expected_length):
        raise TufVerificationError(f"TUF {label} metadata length does not match its parent metadata")
    expected_hash = ((meta.get("hashes") or {}).get("sha256"))
    if expected_hash:
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise TufVerificationError(f"TUF {label} metadata sha256 does not match its parent metadata")


def _check_freshness(signed: Mapping[str, Any], role_name: str, previous_version: int | None = None) -> None:
    if _expiry(str(signed.get("expires", ""))) <= datetime.now(UTC):
        raise TufVerificationError(f"TUF {role_name} metadata is expired")
    version = int(signed.get("version", 0))
    if version <= 0 or previous_version is not None and version < previous_version:
        raise TufVerificationError(f"TUF {role_name} metadata version rolled back")


@dataclass
class TufRepositoryVerifier:
    """Verify a local TUF metadata directory against a trusted root."""

    root_metadata: dict[str, Any]

    @classmethod
    def bootstrap(cls, path: Path, root_metadata: Mapping[str, Any], *, approved: bool = False, expected_sha256: str | None = None) -> "TufRepositoryVerifier":
        if not approved:
            raise TufVerificationError("TUF trust-root bootstrap requires explicit approval")
        root = json.loads(json.dumps(root_metadata))
        _verify_role(root, root, "root")
        if expected_sha256 and hashlib.sha256(_canonical(root)).hexdigest() != expected_sha256:
            raise TufVerificationError("TUF bootstrap root digest does not match the pinned digest")
        path = path.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(root, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)
        return cls(root)

    @classmethod
    def load(cls, path: Path) -> "TufRepositoryVerifier":
        root = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
        _verify_role(root, root, "root")
        return cls(root)

    def rotate_root(self, new_root: Mapping[str, Any], *, approved: bool = False) -> None:
        if not approved:
            raise TufVerificationError("TUF trust-root rotation requires explicit approval")
        _verify_role(new_root, self.root_metadata, "root")
        _verify_role(new_root, new_root, "root")
        old_version = int((self.root_metadata.get("signed") or {}).get("version", 0))
        new_version = int((new_root.get("signed") or {}).get("version", 0))
        if new_version <= old_version:
            raise TufVerificationError("TUF trust-root version must increase during rotation")
        self.root_metadata = json.loads(json.dumps(new_root))

    def verify_directory(self, directory: Path) -> dict[str, Any]:
        directory = directory.expanduser().resolve()
        timestamp = json.loads((directory / "timestamp.json").read_text(encoding="utf-8"))
        snapshot = json.loads((directory / "snapshot.json").read_text(encoding="utf-8"))
        targets = json.loads((directory / "targets.json").read_text(encoding="utf-8"))
        _verify_role(timestamp, self.root_metadata, "timestamp")
        _verify_role(snapshot, self.root_metadata, "snapshot")
        _verify_role(targets, self.root_metadata, "targets")
        _check_freshness(timestamp["signed"], "timestamp")
        _check_freshness(snapshot["signed"], "snapshot")
        _check_freshness(targets["signed"], "targets")
        snapshot_meta = timestamp["signed"].get("meta", {}).get("snapshot.json", {})
        targets_meta = snapshot["signed"].get("meta", {}).get("targets.json", {})
        _verify_metadata_file(directory / "snapshot.json", snapshot_meta, "snapshot")
        _verify_metadata_file(directory / "targets.json", targets_meta, "targets")
        if int(snapshot["signed"].get("version", 0)) != int(snapshot_meta.get("version", 0)):
            raise TufVerificationError("timestamp metadata does not match snapshot version")
        if int(targets["signed"].get("version", 0)) != int(targets_meta.get("version", 0)):
            raise TufVerificationError("snapshot metadata does not match targets version")
        return {"status": "verified", "root_version": self.root_metadata["signed"]["version"], "timestamp_version": timestamp["signed"]["version"], "snapshot_version": snapshot["signed"]["version"], "targets_version": targets["signed"]["version"]}

    def verify_target_from_directory(self, directory: Path, target_path: Path, target_name: str) -> dict[str, Any]:
        """Verify the complete root-to-target chain before checking model bytes."""

        chain = self.verify_directory(directory)
        targets_metadata = json.loads((directory.expanduser().resolve() / "targets.json").read_text(encoding="utf-8"))
        chain.update(self.verify_target(target_path, target_name, targets_metadata))
        return chain

    def verify_target(self, target_path: Path, target_name: str, targets_metadata: Mapping[str, Any]) -> dict[str, Any]:
        target = ((targets_metadata.get("signed") or {}).get("targets") or {}).get(target_name)
        if not isinstance(target, Mapping):
            raise TufVerificationError(f"TUF target is not listed: {target_name}")
        target_path = target_path.expanduser().resolve()
        if not target_path.is_file():
            raise TufVerificationError("TUF target file is missing")
        expected_length = target.get("length")
        if expected_length is not None and target_path.stat().st_size != int(expected_length):
            raise TufVerificationError("TUF target length does not match metadata")
        expected_hash = ((target.get("hashes") or {}).get("sha256"))
        actual_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
        if not expected_hash or actual_hash != expected_hash:
            raise TufVerificationError("TUF target sha256 does not match metadata")
        return {"status": "verified", "target": target_name, "sha256": actual_hash, "length": target_path.stat().st_size}
