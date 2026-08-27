from pathlib import Path

import pytest

from orville_core.connector_defaults import ConnectorDefaultsError, ConnectorDefaultsStore


def test_default_resolution_prefers_explicit_then_task_project_user(tmp_path: Path):
    store = ConnectorDefaultsStore(tmp_path / "defaults.json")
    store.set("user", "default", "github")
    store.set("project", "project-1", "slack")
    store.set("task", "task-1", "notion")
    assert store.resolve(user_id="default", project_id="project-1", task_id="task-1")["connector_uid"] == "notion"
    assert store.resolve(user_id="default", project_id="project-1")["connector_uid"] == "slack"
    assert store.resolve(user_id="default", project_id="unknown")["connector_uid"] == "github"
    assert store.resolve(user_id="default", explicit="calendar")["source"] == "explicit"


def test_clear_and_restart_persistence(tmp_path: Path):
    path = tmp_path / "defaults.json"
    store = ConnectorDefaultsStore(path)
    store.set("project", "p1", "github")
    assert ConnectorDefaultsStore(path).resolve(project_id="p1")["connector_uid"] == "github"
    assert store.clear("project", "p1") is True
    assert ConnectorDefaultsStore(path).resolve(project_id="p1") is None
    assert store.clear("project", "p1") is False


def test_invalid_scope_and_missing_scope_id_are_rejected(tmp_path: Path):
    store = ConnectorDefaultsStore(tmp_path / "defaults.json")
    with pytest.raises(ConnectorDefaultsError):
        store.set("organization", "org", "github")
    with pytest.raises(ConnectorDefaultsError):
        store.set("project", "", "github")
    with pytest.raises(ConnectorDefaultsError):
        store.set("user", "default", "")
