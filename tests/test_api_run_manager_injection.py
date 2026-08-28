from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from orville_core.api import create_app
from orville_core.run_manager import RunManager


pytest.importorskip("fastapi")


class RecordingRunManager:
    def __init__(self):
        self.calls = []

    def execute(self, graph, *, context, run_id, streaming=False):
        self.calls.append((run_id, streaming))
        return None

    def request_cancel(self, run_id):
        self.calls.append((run_id, "cancel"))


def test_api_injects_supplied_run_manager():
    with TemporaryDirectory() as directory:
        manager = RecordingRunManager()
        app = create_app(checkpoint_dir=Path(directory), api_token="secret", run_manager=manager)

        assert app.state.run_manager is manager
        assert app.state.orchestration_engine is not None
        assert app.state.provider_registry is not None


def test_api_defaults_to_run_manager_with_provider_backed_handlers():
    with TemporaryDirectory() as directory:
        app = create_app(checkpoint_dir=Path(directory), api_token="secret")

        assert isinstance(app.state.run_manager, RunManager)
        handlers = app.state.orchestration_engine.handlers
        assert handlers["intake.objective"].__module__ == "orville_core.integration"
        assert handlers["intake.objective.streaming"].__module__ == "orville_core.integration"
