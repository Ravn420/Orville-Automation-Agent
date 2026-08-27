"""Durable, atomic JSON checkpoint storage for Orville runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .models import Checkpoint
from .security import SecretRedactor


class CheckpointStore:
    """Persist complete checkpoints using atomic replacement and fsync."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, run_id: str) -> Path:
        safe_id = "".join(char for char in run_id if char.isalnum() or char in "-_ .")
        safe_id = safe_id.strip().replace(" ", "_")
        if not safe_id or safe_id != run_id:
            raise ValueError("run_id contains unsupported path characters")
        return self.root / f"{safe_id}.json"

    def save(self, checkpoint: Checkpoint) -> Path:
        destination = self.path_for(checkpoint.run_id)
        payload = json.dumps(SecretRedactor.redact(checkpoint.to_dict()), indent=2, sort_keys=True, ensure_ascii=False)
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self.root, prefix=f".{destination.name}.", suffix=".tmp", delete=False
        ) as temporary:
            temporary.write(payload)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, destination)
            # Directory fsync is supported on POSIX filesystems but not on
            # Windows. The atomic os.replace above remains the durability
            # boundary on Windows.
            if os.name != "nt":
                directory_fd = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            temporary_path.unlink(missing_ok=True)
        return destination

    def load(self, run_id: str) -> Checkpoint:
        path = self.path_for(run_id)
        if not path.exists():
            raise FileNotFoundError(f"checkpoint not found for run {run_id}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"checkpoint is corrupt: {path}") from exc
        return Checkpoint.from_dict(data)

    def exists(self, run_id: str) -> bool:
        return self.path_for(run_id).exists()

    def list_run_ids(self) -> list[str]:
        return sorted(path.stem for path in self.root.glob("*.json"))
