from orville_core.provider_features import ProviderRateLimitStore
from pathlib import Path
import tempfile
import time

with tempfile.TemporaryDirectory() as directory:
    store = ProviderRateLimitStore(Path(directory) / "usage_unique.db")
    store.set_limit("local", 60, max_calls=1, max_tokens=100)
    print('First admit:', store.admit("local"))
    print('Second admit:', store.admit("local"))
    print('Snapshot:', store.snapshot("local"))
