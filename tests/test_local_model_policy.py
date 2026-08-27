from pathlib import Path

import pytest

from orville_core import LocalModelExecutionPolicy, LocalModelPolicyError


def test_local_model_policy_restricts_paths_and_defaults_to_no_network(tmp_path):
    policy = LocalModelExecutionPolicy((tmp_path,))
    assert policy.network_enabled is False
    assert policy.validate_path(tmp_path / "model.gguf") == (tmp_path / "model.gguf").resolve()
    with pytest.raises(LocalModelPolicyError, match="outside allowed roots"):
        policy.validate_path(tmp_path.parent / "outside.gguf")


def test_local_model_policy_rejects_scripts_and_invalid_limits(tmp_path):
    with pytest.raises(LocalModelPolicyError, match="scripts"):
        LocalModelExecutionPolicy((Path(tmp_path),), allow_scripts=True)
    with pytest.raises(LocalModelPolicyError, match="resource limits"):
        LocalModelExecutionPolicy((Path(tmp_path),), max_memory_mb=0)
    with pytest.raises(LocalModelPolicyError, match="resource limits"):
        LocalModelExecutionPolicy((Path(tmp_path),), max_disk_mb=0)
    with pytest.raises(LocalModelPolicyError, match="resource limits"):
        LocalModelExecutionPolicy((Path(tmp_path),), max_concurrency=0)
