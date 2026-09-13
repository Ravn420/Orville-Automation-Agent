"""Windows executable entrypoint for the existing Orville CLI."""
from orville_core.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
