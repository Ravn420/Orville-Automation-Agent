"""Durable connector default resolution for user, project, and task scopes."""
from __future__ import annotations
import json
import threading
import time
from pathlib import Path
from typing import Any

class ConnectorDefaultsError(ValueError):
    pass

class ConnectorDefaultsStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._values: dict[str, dict[str, str]] = {"user": {}, "project": {}, "task": {}}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for scope in self._values:
            values = payload.get(scope, {})
            if isinstance(values, dict):
                self._values[scope] = {str(key): str(value) for key, value in values.items() if str(key).strip() and str(value).strip()}

    def _save(self) -> None:
        payload = {"version": 1, **self._values, "updated_at": time.time()}
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp.replace(self.path)

    @staticmethod
    def _scope(scope: str) -> str:
        normalized = scope.strip().lower()
        if normalized not in {"user", "project", "task"}:
            raise ConnectorDefaultsError("scope must be user, project, or task")
        return normalized

    def set(self, scope: str, scope_id: str, connector_uid: str) -> dict[str, Any]:
        normalized_scope = self._scope(scope)
        scope_key = scope_id.strip() or "default" if normalized_scope == "user" else scope_id.strip()
        if not scope_key or len(scope_key) > 200:
            raise ConnectorDefaultsError("scope ID is required")
        if not connector_uid.strip() or len(connector_uid) > 160:
            raise ConnectorDefaultsError("connector UID is required")
        with self._lock:
            self._values[normalized_scope][scope_key] = connector_uid.strip()
            self._save()
            return {"scope": normalized_scope, "scope_id": scope_key, "connector_uid": connector_uid.strip()}

    def clear(self, scope: str, scope_id: str) -> bool:
        normalized_scope = self._scope(scope)
        scope_key = scope_id.strip() or "default" if normalized_scope == "user" else scope_id.strip()
        with self._lock:
            removed = self._values[normalized_scope].pop(scope_key, None) is not None
            if removed:
                self._save()
            return removed

    def list(self) -> list[dict[str, str]]:
        with self._lock:
            return [{"scope": scope, "scope_id": scope_id, "connector_uid": uid} for scope, values in self._values.items() for scope_id, uid in sorted(values.items())]

    def resolve(self, *, task_id: str | None = None, project_id: str | None = None, user_id: str = "default", explicit: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            if explicit and explicit.strip():
                return {"connector_uid": explicit.strip(), "source": "explicit"}
            candidates = [("task", task_id), ("project", project_id), ("user", user_id or "default")]
            for scope, scope_id in candidates:
                if scope_id and self._values[scope].get(scope_id):
                    return {"connector_uid": self._values[scope][scope_id], "source": scope, "scope_id": scope_id}
            return None
