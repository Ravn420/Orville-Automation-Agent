"""Reviewed deployment-provider boundary for production canary operations.

The adapter wraps a provider-specific backend while keeping provider credentials
outside the orchestration process contract. It enforces operation allowlists,
bounded execution time, idempotent operation keys, release/traffic validation,
dry-run behavior, and redacted status snapshots. The wrapped backend must own
credential acquisition and must not return credential material.
"""
from __future__ import annotations

import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from .canary import CanaryError, DeploymentAdapter
from .secrets_audit import SecretScanner


class DeploymentProviderBackend(Protocol):
    def deploy(self, release_id: str, rollback_target: str) -> None: ...
    def set_traffic(self, release_id: str, traffic_percent: int) -> None: ...
    def pause(self, release_id: str) -> None: ...
    def rollback(self, release_id: str, rollback_target: str) -> None: ...
    def status(self, release_id: str) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class ProviderOperation:
    operation_id: str
    action: str
    release_id: str
    outcome: str
    dry_run: bool


class ReviewedDeploymentAdapter(DeploymentAdapter):
    """Fail-closed, provider-neutral adapter suitable for reviewed integration."""

    _ACTIONS = frozenset({"deploy", "set_traffic", "pause", "rollback", "status"})

    def __init__(self, backend: DeploymentProviderBackend, *, provider_id: str, credential_reference: str, timeout_seconds: float = 30.0, dry_run: bool = True) -> None:
        if not provider_id.strip() or not credential_reference.strip():
            raise ValueError("provider_id and a protected credential reference are required")
        if SecretScanner.find(credential_reference):
            raise ValueError("credential_reference must be a reference identifier, not credential material")
        if timeout_seconds <= 0 or timeout_seconds > 300:
            raise ValueError("timeout_seconds must be in (0, 300]")
        self.backend = backend
        self.provider_id = provider_id
        self.credential_reference = credential_reference
        self.timeout_seconds = timeout_seconds
        self.dry_run = dry_run
        self._lock = threading.RLock()
        self._completed: dict[str, ProviderOperation] = {}
        self._last: ProviderOperation | None = None

    @staticmethod
    def _validate_release(release_id: str) -> None:
        if not release_id or len(release_id) > 256 or any(ch in release_id for ch in "\r\n"):
            raise CanaryError("invalid release identifier")

    @staticmethod
    def _validate_traffic(traffic_percent: int) -> None:
        if isinstance(traffic_percent, bool) or not 0 <= traffic_percent <= 100:
            raise CanaryError("traffic_percent must be between 0 and 100")

    def _operation(self, action: str, release_id: str, arguments: Mapping[str, Any], call: Callable[[], None] | None) -> ProviderOperation:
        if action not in self._ACTIONS:
            raise CanaryError("unsupported deployment operation")
        self._validate_release(release_id)
        payload = json.dumps({"provider": self.provider_id, "action": action, "release": release_id, "arguments": dict(arguments)}, sort_keys=True)
        operation_id = "deploy-op-" + hashlib.sha256(payload.encode()).hexdigest()[:20]
        with self._lock:
            previous = self._completed.get(operation_id)
            if previous is not None:
                return previous
        if self.dry_run:
            operation = ProviderOperation(operation_id, action, release_id, "dry_run", True)
        else:
            if call is None:
                raise CanaryError("provider operation has no backend call")
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call)
                try:
                    future.result(timeout=self.timeout_seconds)
                except FutureTimeout as exc:
                    future.cancel()
                    raise CanaryError(f"deployment provider operation timed out: {action}") from exc
                except Exception as exc:
                    raise CanaryError(f"deployment provider operation failed: {action}") from exc
            operation = ProviderOperation(operation_id, action, release_id, "completed", False)
        with self._lock:
            self._completed[operation_id] = operation
            self._last = operation
        return operation

    def deploy(self, release_id: str, rollback_target: str) -> None:
        self._validate_release(rollback_target)
        self._operation("deploy", release_id, {"rollback_target": rollback_target}, lambda: self.backend.deploy(release_id, rollback_target))

    def set_traffic(self, release_id: str, traffic_percent: int) -> None:
        self._validate_traffic(traffic_percent)
        self._operation("set_traffic", release_id, {"traffic_percent": traffic_percent}, lambda: self.backend.set_traffic(release_id, traffic_percent))

    def pause(self, release_id: str) -> None:
        self._operation("pause", release_id, {}, lambda: self.backend.pause(release_id))

    def rollback(self, release_id: str, rollback_target: str) -> None:
        self._validate_release(rollback_target)
        self._operation("rollback", release_id, {"rollback_target": rollback_target}, lambda: self.backend.rollback(release_id, rollback_target))

    def status(self, release_id: str) -> Mapping[str, Any]:
        self._validate_release(release_id)
        if self.dry_run:
            result: Mapping[str, Any] = {"status": "dry_run", "provider_id": self.provider_id, "release_id": release_id}
        else:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.backend.status, release_id)
                try:
                    result = future.result(timeout=self.timeout_seconds)
                except FutureTimeout as exc:
                    future.cancel()
                    raise CanaryError("deployment provider status timed out") from exc
                except Exception as exc:
                    raise CanaryError("deployment provider status failed") from exc
            if not isinstance(result, Mapping):
                raise CanaryError("deployment provider returned invalid status")
            result = dict(result)
        safe = SecretScanner.redact(dict(result))
        return {"provider_id": self.provider_id, "release_id": release_id, **safe}

    def operation_history(self) -> tuple[ProviderOperation, ...]:
        with self._lock:
            return tuple(self._completed.values())
