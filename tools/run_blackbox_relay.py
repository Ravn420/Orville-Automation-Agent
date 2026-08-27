"""Run the Orville-managed Blackbox relay.

Required environment variables:
    BLACKBOX_API_KEY: server-side Blackbox credential
    ORVILLE_RELAY_CLIENT_TOKEN: token issued to Orville clients

Optional environment variables:
    BLACKBOX_BASE_URL, ORVILLE_RELAY_HOST, ORVILLE_RELAY_PORT,
    ORVILLE_RELAY_REQUESTS_PER_MINUTE
"""
from __future__ import annotations

import os

from orville_core.relay_server import create_relay_app


def main() -> None:
    import uvicorn

    app = create_relay_app(requests_per_minute=int(os.getenv("ORVILLE_RELAY_REQUESTS_PER_MINUTE", "60")))
    uvicorn.run(app, host=os.getenv("ORVILLE_RELAY_HOST", "127.0.0.1"), port=int(os.getenv("ORVILLE_RELAY_PORT", "8790")), log_level=os.getenv("ORVILLE_RELAY_LOG_LEVEL", "info"))


if __name__ == "__main__":
    main()
