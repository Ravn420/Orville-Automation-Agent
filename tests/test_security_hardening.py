from pathlib import Path

import pytest

from orville_core.attestations import AttestationError, AttestationPolicy, verify_attestation
from orville_core.sandbox import SandboxPolicy, SandboxUnavailable, UnavailableSandboxExecutor, SandboxPlan


def test_sandbox_plan_rejects_shell_strings_and_secret_environment():
    policy = SandboxPolicy(allowed_environment=frozenset({"LANG", "API_KEY"}))
    with pytest.raises(ValueError, match="argv"):
        SandboxPlan.from_request({"run_id": "r1", "command": "python model.py", "model_path": "C:/model", "scratch_path": "C:/scratch", "output_path": "C:/out", "model_checksum": "sha256:x"}, policy)
    with pytest.raises(ValueError, match="credential-like"):
        SandboxPlan.from_request({"run_id": "r1", "command": ["python", "-V"], "model_path": "C:/model", "scratch_path": "C:/scratch", "output_path": "C:/out", "model_checksum": "sha256:x", "environment": {"API_KEY": "secret"}}, policy)


def test_unavailable_sandbox_fails_closed():
    plan = SandboxPlan(
        run_id="r1",
        command=("python", "-V"),
        model_path=Path("C:/model"),
        scratch_path=Path("C:/scratch"),
        output_path=Path("C:/out"),
        policy=SandboxPolicy(),
        model_checksum="sha256:x",
    )
    with pytest.raises(SandboxUnavailable):
        UnavailableSandboxExecutor().run(plan)


def test_required_attestation_fails_closed_when_missing_or_wrong_digest():
    policy = AttestationPolicy(mode="required", trusted_issuers=frozenset({"issuer"}))
    with pytest.raises(AttestationError, match="missing"):
        verify_attestation(envelope=None, subject_digest="sha256:x", policy=policy)
    with pytest.raises(AttestationError, match="digest"):
        verify_attestation(envelope={"subject_digest": "sha256:y", "issuer": "issuer"}, subject_digest="sha256:x", policy=policy)


def test_optional_attestation_is_reported_without_being_treated_as_verified():
    result = verify_attestation(envelope={"subject_digest": "sha256:x", "issuer": "issuer"}, subject_digest="sha256:x", policy=AttestationPolicy(mode="optional"))
    assert result.verification_status == "rejected"
    assert result.policy_id


def test_trust_store_bootstrap_rotation_and_revocation_are_approval_gated(tmp_path: Path):
    from orville_core.attestations import TrustStore

    path = tmp_path / "trust.json"
    with pytest.raises(AttestationError, match="approval"):
        TrustStore.bootstrap(path, {"issuer": "a"})
    store = TrustStore.bootstrap(path, {"issuer": "a"}, approved=True)
    assert store.issuers() == ("issuer",)
    with pytest.raises(AttestationError, match="approval"):
        store.rotate("issuer", "b")
    store.rotate("issuer", "b", approved=True)
    assert store.resolve_public_key("issuer") == "b"
    store.revoke("issuer", approved=True)
    assert store.issuers() == ()
    with pytest.raises(AttestationError, match="active"):
        store.resolve_public_key("issuer")


def test_platform_adapters_never_claim_unavailable_runtime_is_ready(tmp_path: Path):
    from orville_core.sandbox_adapters import LinuxBubblewrapExecutor, WindowsSandboxExecutor, discover_sandbox_adapters

    adapters = discover_sandbox_adapters()
    assert set(adapters) == {"linux_bubblewrap", "windows_sandbox"}
    if not LinuxBubblewrapExecutor(executable="missing-bwrap").available():
        with pytest.raises(SandboxUnavailable):
            LinuxBubblewrapExecutor(executable="missing-bwrap").build_argv(
                SandboxPlan("r1", ("python", "-V"), Path("C:/model"), tmp_path / "scratch", tmp_path / "out", SandboxPolicy(), "sha256:x")
            )
    windows = WindowsSandboxExecutor(executable="missing-windows-sandbox")
    plan = SandboxPlan("r1", ("worker.exe", "--model", "C:/model"), Path("C:/model"), tmp_path / "scratch", tmp_path / "out", SandboxPolicy(), "sha256:x")
    config = windows.build_config(plan, tmp_path / "worker.wsb")
    assert "<Networking>Disable</Networking>" in config.read_text(encoding="utf-8")
    assert "<ReadOnly>true</ReadOnly>" in config.read_text(encoding="utf-8")


def test_tuf_bootstrap_and_rotation_require_explicit_approval(tmp_path: Path):
    from orville_core.tuf_metadata import TufRepositoryVerifier, TufVerificationError

    root = {"signed": {"_type": "root", "version": 1, "expires": "2099-01-01T00:00:00Z", "keys": {}, "roles": {"root": {"keyids": [], "threshold": 1}}}, "signatures": {}}
    with pytest.raises(TufVerificationError, match="approval"):
        TufRepositoryVerifier.bootstrap(tmp_path / "root.json", root)
    verifier = TufRepositoryVerifier(root)
    with pytest.raises(TufVerificationError, match="approval"):
        verifier.rotate_root(root)


def test_tuf_target_integrity_fails_closed(tmp_path: Path):
    from orville_core.tuf_metadata import TufRepositoryVerifier, TufVerificationError

    target = tmp_path / "model.gguf"
    target.write_bytes(b"model")
    metadata = {"signed": {"targets": {"model.gguf": {"length": 999, "hashes": {"sha256": "0" * 64}}}}}
    verifier = TufRepositoryVerifier({"signed": {"version": 1}})
    with pytest.raises(TufVerificationError, match="length"):
        verifier.verify_target(target, "model.gguf", metadata)
    metadata["signed"]["targets"]["model.gguf"]["length"] = target.stat().st_size
    with pytest.raises(TufVerificationError, match="sha256"):
        verifier.verify_target(target, "model.gguf", metadata)
