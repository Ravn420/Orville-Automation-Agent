import json

import pytest

from orville_core import CanaryPolicy, CanaryPolicyError, LocalModelCatalog


def test_canary_policy_example_is_valid(tmp_path):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "policy_version": 1,
                "policy_id": "test-v1",
                "release_id": "release-a",
                "rollback_target": "release-known-good",
                "cohorts": [
                    {"name": "internal", "traffic_percent": 1, "hold_seconds": 30},
                    {"name": "full", "traffic_percent": 100, "hold_seconds": 30},
                ],
                "health": {"min_samples": 10},
                "rollback": {},
                "max_hold_seconds": 60,
                "approval_mode": "per_step",
                "observation_window_seconds": 30,
                "require_fresh_health_decision": True,
            }
        )
    )
    policy = CanaryPolicy.from_dict(json.loads(policy_path.read_text()))
    assert policy.to_dict()["cohorts"][-1]["traffic_percent"] == 100


def test_canary_policy_rejects_unbounded_or_non_monotonic_rules():
    with pytest.raises(CanaryPolicyError, match="monotonically"):
        CanaryPolicy.from_dict(
            {
                "policy_version": 1,
                "policy_id": "bad",
                "release_id": "release",
                "rollback_target": "known-good",
                "cohorts": [
                    {"name": "a", "traffic_percent": 50, "hold_seconds": 1},
                    {"name": "b", "traffic_percent": 25, "hold_seconds": 1},
                    {"name": "c", "traffic_percent": 100, "hold_seconds": 1},
                ],
                "max_hold_seconds": 10,
                "observation_window_seconds": 1,
                "require_fresh_health_decision": True,
            }
        )


def test_activation_persists_optional_attestation_evidence(tmp_path):
    asset = tmp_path / "model.gguf"
    asset.write_bytes(b"synthetic model")
    catalog = LocalModelCatalog(tmp_path / "catalog.json")
    catalog.import_model(asset, model_id="demo", runtime="ollama")
    activated = catalog.activate("demo", endpoint="http://localhost:11434", attestation_policy="optional")
    assert activated.status == "active"
    assert activated.activation_evidence["policy_mode"] == "optional"
    assert activated.activation_evidence["subject_digest"] == activated.checksum_sha256
    reloaded = LocalModelCatalog(tmp_path / "catalog.json").get("demo")
    assert reloaded.activation_evidence["verification_status"] == "unverified"


def test_required_attestation_blocks_activation(tmp_path):
    asset = tmp_path / "model.gguf"
    asset.write_bytes(b"synthetic model")
    catalog = LocalModelCatalog(tmp_path / "catalog.json")
    catalog.import_model(asset, model_id="demo", runtime="ollama")
    with pytest.raises(ValueError, match="failed validation"):
        catalog.activate("demo", attestation_policy="required")
