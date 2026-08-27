"""Validate the release wheel outside the repository source tree."""

from __future__ import annotations

import importlib.metadata

from orville_core.api import create_app
from orville_core.browser_relay import LocalBrowserRelay
from orville_core.engine import OrchestrationEngine
from orville_core.preview_runtime import PreviewRuntime


def main() -> None:
    app = create_app(api_token="release-validation-token")
    relay = LocalBrowserRelay(ttl_seconds=60)
    runtime = PreviewRuntime()
    engine = OrchestrationEngine
    assert app is not None
    assert relay is not None
    assert runtime is not None
    assert engine.__name__ == "OrchestrationEngine"
    print(f"orville-core {importlib.metadata.version('orville-core')} distribution imports passed")


if __name__ == "__main__":
    main()
