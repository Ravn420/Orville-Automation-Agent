"""Windows launcher for the unchanged Orville API and CLI."""
from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


def load_env() -> None:
    """Load simple KEY=value settings from a sibling .env.production file."""
    candidates = [Path(sys.executable).resolve().parent / ".env.production", Path.cwd() / ".env.production"]
    for path in candidates:
        if path.exists():
            for raw in path.read_text(encoding="utf-8-sig").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
            return


def open_docs() -> None:
    time.sleep(2)
    webbrowser.open(
        f"http://127.0.0.1:{os.getenv('ORVILLE_API_PORT', '8787')}/docs",
        new=2,
    )


def main() -> int:
    load_env()
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        from orville_core.cli import main as cli_main
        return cli_main(sys.argv[2:])
    threading.Thread(target=open_docs, daemon=True).start()
    from orville_core.api import main as api_main
    api_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
