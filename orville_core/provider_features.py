"""Provider discovery, durable privacy routing, and redacted configuration export."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import sqlite3
import threading
from datetime import UTC, datetime

PRIVACY_CLASSES = {"local_only", "cloud_approved", "restricted"}
LOCAL_PROVIDER_TYPES = {"ollama", "custom-local", "custom-local-ollama", "ollama-compatible", "openai-compatible-local", "llama-cpp", "transformers"}


class ProviderDiscoveryError(ValueError):
    """Raised when a provider model catalog cannot be safely retrieved."""


def _request_json(url: str, *, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", **headers}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
    except HTTPError as exc:
        raise ProviderDiscoveryError(f"provider returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ProviderDiscoveryError(f"provider discovery unavailable: {type(exc).__name__}") from exc
    if len(raw) > 2_000_000:
        raise ProviderDiscoveryError("provider model catalog exceeded the safety limit")
    try:
        value = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderDiscoveryError("provider returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ProviderDiscoveryError("provider model catalog must be an object")
    return value


def discover_provider_models(config: Any) -> dict[str, Any]:
    """Discover model identifiers without exposing credentials in URLs or results."""
    provider_type = str(config.provider_type).lower().replace("_", "-")
    base_url = str(config.base_url).rstrip("/") + "/"
    headers = dict(getattr(config, "headers", {}) or {})
    if config.api_key:
        headers.setdefault("Authorization", f"Bearer {config.api_key}")
        if provider_type in {"gemini", "google"}:
            headers["x-goog-api-key"] = config.api_key
            headers.pop("Authorization", None)
    if provider_type in LOCAL_PROVIDER_TYPES or provider_type == "ollama":
        payload = _request_json(urljoin(base_url, "api/tags"), headers=headers, timeout=config.timeout_seconds)
        models = [{"id": item.get("name"), "name": item.get("name"), "modified_at": item.get("modified_at"), "size": item.get("size")} for item in payload.get("models", []) if isinstance(item, dict) and item.get("name")]
    elif provider_type in {"openai-compatible", "openai", "blackbox", "blackbox-relay", "managed-blackbox"}:
        payload = _request_json(urljoin(base_url, "models"), headers=headers, timeout=config.timeout_seconds)
        models = [{"id": item.get("id"), "name": item.get("id"), "owned_by": item.get("owned_by")} for item in payload.get("data", []) if isinstance(item, dict) and item.get("id")]
    elif provider_type in {"gemini", "google"}:
        payload = _request_json(urljoin(base_url, "v1beta/models"), headers=headers, timeout=config.timeout_seconds)
        models = [{"id": item.get("name"), "name": item.get("displayName") or item.get("name"), "supported_generation_methods": item.get("supportedGenerationMethods", [])} for item in payload.get("models", []) if isinstance(item, dict) and item.get("name")]
    else:
        return {"provider_id": config.provider_id, "provider_type": provider_type, "discovery_supported": False, "manual_model_entry": True, "models": [], "status": "manual_required"}
    return {"provider_id": config.provider_id, "provider_type": provider_type, "discovery_supported": True, "manual_model_entry": True, "models": models, "count": len(models), "status": "ok"}


@dataclass
class PrivacyRoutingPolicy:
    """Durable routing policy for each privacy class."""
    privacy_class: str
    allowed_provider_ids: list[str]
    local_only: bool
    allow_fallback: bool = True

    def __post_init__(self) -> None:
        if self.privacy_class not in PRIVACY_CLASSES:
            raise ValueError(f"privacy_class must be one of {sorted(PRIVACY_CLASSES)}")
        if self.privacy_class in {"local_only", "restricted"}:
            self.local_only = True
        self.allowed_provider_ids = sorted(set(str(item) for item in self.allowed_provider_ids if str(item).strip()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PrivacyRoutingPolicyStore:
    """Atomic JSON store containing no credentials or prompt data."""
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.policies: dict[str, PrivacyRoutingPolicy] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            for item in payload.get("policies", []):
                policy = PrivacyRoutingPolicy(**item)
                self.policies[policy.privacy_class] = policy
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.policies = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                json.dump({"schema_version": 1, "policies": [item.to_dict() for item in self.policies.values()]}, stream, indent=2, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def set(self, policy: PrivacyRoutingPolicy) -> dict[str, Any]:
        self.policies[policy.privacy_class] = policy
        self._save()
        return policy.to_dict()

    def list(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.policies.values()]

    def get(self, privacy_class: str) -> PrivacyRoutingPolicy | None:
        return self.policies.get(privacy_class)


class DiscoveryCatalogStore:
    """Atomic JSON catalog for discovered model IDs and active selections."""
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.catalog: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        if self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                self.catalog = dict(payload.get("providers", {}))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                self.catalog = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                json.dump({"schema_version": 1, "providers": self.catalog}, stream, indent=2, sort_keys=True)
                stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

    def record(self, provider_id: str, result: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            return self._record_locked(provider_id, result)

    def _record_locked(self, provider_id: str, result: dict[str, Any]) -> dict[str, Any]:
        previous = self.catalog.get(provider_id, {})
        entry = {"provider_id": provider_id, "provider_type": result.get("provider_type"), "models": result.get("models", []), "count": result.get("count", 0), "status": result.get("status"), "discovery_supported": bool(result.get("discovery_supported", False)), "manual_model_entry": bool(result.get("manual_model_entry", True)), "discovered_at": datetime.now(UTC).isoformat(), "active_model": previous.get("active_model")}
        self.catalog[provider_id] = entry
        self._save()
        return entry

    def get(self, provider_id: str) -> dict[str, Any] | None:
        return self.catalog.get(provider_id)

    def set_active(self, provider_id: str, model: str) -> dict[str, Any]:
        with self._lock:
            return self._set_active_locked(provider_id, model)

    def _set_active_locked(self, provider_id: str, model: str) -> dict[str, Any]:
        entry = self.catalog.get(provider_id)
        if not entry:
            raise KeyError(f"no discovery catalog for provider: {provider_id}")
        known = {str(item.get("id")) for item in entry.get("models", []) if isinstance(item, dict)}
        if model not in known:
            raise ValueError("model is not present in the provider discovery catalog")
        entry["active_model"] = model
        entry["selected_at"] = datetime.now(UTC).isoformat()
        self._save()
        return entry


class ProviderRateLimitStore:
    """SQLite-backed fixed-window provider call/token accounting."""
    def __init__(self, database: str | Path) -> None:
        self.database = Path(database); self.database.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database) as db:
            db.execute("CREATE TABLE IF NOT EXISTS provider_rate_limits (provider_id TEXT PRIMARY KEY, window_seconds INTEGER NOT NULL, max_calls INTEGER NOT NULL, max_tokens INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS provider_rate_events (provider_id TEXT NOT NULL, recorded_at REAL NOT NULL, calls INTEGER NOT NULL, tokens INTEGER NOT NULL)")

    def set_limit(self, provider_id: str, window_seconds: int, max_calls: int = -1, max_tokens: int = -1) -> dict[str, Any]:
        if window_seconds < 1 or max_calls < -1 or max_tokens < -1: raise ValueError("invalid provider rate limit")
        with sqlite3.connect(self.database) as db:
            db.execute("INSERT INTO provider_rate_limits VALUES (?, ?, ?, ?) ON CONFLICT(provider_id) DO UPDATE SET window_seconds=excluded.window_seconds, max_calls=excluded.max_calls, max_tokens=excluded.max_tokens", (provider_id, window_seconds, max_calls, max_tokens))
        return self.snapshot(provider_id)

    def admit(self, provider_id: str, calls: int = 1, tokens: int = 0) -> tuple[bool, str]:
        now = datetime.now(UTC).timestamp()
        with sqlite3.connect(self.database, timeout=30, isolation_level="IMMEDIATE") as db:
            limit = db.execute("SELECT window_seconds, max_calls, max_tokens FROM provider_rate_limits WHERE provider_id=?", (provider_id,)).fetchone()
            if not limit: return True, "no provider rate limit configured"
            window, max_calls, max_tokens = limit
            db.execute("DELETE FROM provider_rate_events WHERE recorded_at < ?", (now - window,))
            used = db.execute("SELECT COALESCE(SUM(calls),0), COALESCE(SUM(tokens),0) FROM provider_rate_events WHERE provider_id=? AND recorded_at>=?", (provider_id, now - window)).fetchone()
            if max_calls >= 0 and used[0] + calls > max_calls: return False, "provider call rate limit exceeded"
            if max_tokens >= 0 and used[1] + tokens > max_tokens: return False, "provider token rate limit exceeded"
            db.execute("INSERT INTO provider_rate_events VALUES (?, ?, ?, ?)", (provider_id, now, calls, tokens))
        return True, "within provider rate limit"

    def snapshot(self, provider_id: str) -> dict[str, Any]:
        now = datetime.now(UTC).timestamp()
        with sqlite3.connect(self.database) as db:
            limit = db.execute("SELECT window_seconds, max_calls, max_tokens FROM provider_rate_limits WHERE provider_id=?", (provider_id,)).fetchone()
            if not limit: return {"provider_id": provider_id, "configured": False}
            used = db.execute("SELECT COALESCE(SUM(calls),0), COALESCE(SUM(tokens),0) FROM provider_rate_events WHERE provider_id=? AND recorded_at>=?", (provider_id, now - limit[0])).fetchone()
        return {"provider_id": provider_id, "configured": True, "window_seconds": limit[0], "max_calls": limit[1], "max_tokens": limit[2], "calls_used": used[0], "tokens_used": used[1]}


class RemoteCatalogStore:
    """Tenant-scoped remote discovery catalog federation with local fallback."""
    def __init__(self, local: DiscoveryCatalogStore, url: str | None = None, token: str | None = None, tenant_id: str | None = None) -> None:
        self.local = local; self.url = (url or "").rstrip("/"); self.token = token or ""; self.tenant_id = (tenant_id or "").strip()

    @property
    def configured(self) -> bool: return bool(self.url and self.token and self.tenant_id)

    def status(self) -> dict[str, Any]:
        return {"configured": self.configured, "endpoint": self.url or None, "tenant_id": self.tenant_id or None, "credential_configured": bool(self.token), "fallback": "local_json"}

    def sync(self) -> dict[str, Any]:
        if not self.configured: return {"source": "local", "remote_synced": False, "catalogs": list(self.local.catalog.values())}
        request = Request(f"{self.url}/v1/tenants/{self.tenant_id}/catalogs/providers", method="GET", headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"})
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read(2_000_000).decode("utf-8"))
            catalogs = payload.get("catalogs", []) if isinstance(payload, dict) else []
            for entry in catalogs:
                if isinstance(entry, dict) and entry.get("provider_id"):
                    self.local.catalog[str(entry["provider_id"])] = entry
            self.local._save()
            return {"source": "remote", "remote_synced": True, "catalogs": list(self.local.catalog.values())}
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {"source": "local", "remote_synced": False, "catalogs": list(self.local.catalog.values()), "remote_error": "unavailable"}

    def publish(self, provider_id: str) -> dict[str, Any]:
        catalog = self.local.get(provider_id)
        if catalog is None: raise KeyError(f"provider discovery catalog not found: {provider_id}")
        if not self.configured: return {"source": "local", "remote_synced": False, "catalog": catalog}
        request = Request(f"{self.url}/v1/tenants/{self.tenant_id}/catalogs/providers/{provider_id}", data=json.dumps(catalog).encode(), method="PUT", headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=10) as response: response.read(100_000)
            return {"source": "remote", "remote_synced": True, "catalog": catalog}
        except (HTTPError, URLError, TimeoutError, OSError):
            return {"source": "local", "remote_synced": False, "catalog": catalog, "remote_error": "unavailable"}


class PolicyBackupStore:
    """Checksum-verified policy snapshots for disaster recovery."""
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)

    def create(self, policies: PrivacyRoutingPolicyStore, catalogs: DiscoveryCatalogStore) -> dict[str, Any]:
        payload = {"schema_version": 1, "created_at": datetime.now(UTC).isoformat(), "privacy_policies": policies.list(), "discovery_catalogs": list(catalogs.catalog.values())}
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        import hashlib
        digest = hashlib.sha256(body).hexdigest()
        destination = self.directory / f"policy-backup-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{digest[:12]}.json"
        temporary = destination.with_suffix(".tmp")
        temporary.write_bytes(body); os.replace(temporary, destination)
        return {"path": str(destination), "sha256": digest, "bytes": len(body), "created_at": payload["created_at"]}

    def list(self) -> list[dict[str, Any]]:
        return [{"path": str(path), "bytes": path.stat().st_size} for path in sorted(self.directory.glob("policy-backup-*.json"))]


class RemotePolicyStore:
    """Enterprise HTTP policy store with explicit local fallback."""
    def __init__(self, local: PrivacyRoutingPolicyStore, url: str | None = None, token: str | None = None) -> None:
        self.local = local; self.url = (url or "").rstrip("/"); self.token = token or ""

    @property
    def configured(self) -> bool: return bool(self.url and self.token)

    def status(self) -> dict[str, Any]:
        return {"configured": self.configured, "endpoint": self.url or None, "credential_configured": bool(self.token), "fallback": "local_json"}

    def load(self) -> dict[str, Any]:
        if not self.configured:
            return {"policies": self.local.list(), "source": "local", "remote_synced": False}
        request = Request(self.url + "/v1/policies/privacy", method="GET", headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"})
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read(500_000).decode("utf-8"))
            policies = payload.get("policies", []) if isinstance(payload, dict) else []
            for item in policies:
                self.local.set(PrivacyRoutingPolicy(**item))
            return {"policies": self.local.list(), "source": "remote", "remote_synced": True}
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            return {"policies": self.local.list(), "source": "local", "remote_synced": False, "remote_error": "unavailable"}

    def save(self, policy: PrivacyRoutingPolicy) -> dict[str, Any]:
        local = self.local.set(policy)
        if not self.configured: return {"policy": local, "source": "local", "remote_synced": False}
        request = Request(self.url + "/v1/policies/privacy/" + policy.privacy_class, data=json.dumps(local).encode(), method="PUT", headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=10) as response: response.read(100_000)
            return {"policy": local, "source": "remote", "remote_synced": True}
        except (HTTPError, URLError, TimeoutError, OSError):
            return {"policy": local, "source": "local", "remote_synced": False, "remote_error": "unavailable"}


def redacted_provider_export(providers: list[Any], policies: PrivacyRoutingPolicyStore, catalogs: DiscoveryCatalogStore | None = None) -> dict[str, Any]:
    """Build a portable export containing only non-secret provider metadata."""
    return {"schema_version": 1, "providers": [provider.config.redacted() for provider in providers], "privacy_policies": policies.list(), "discovery_catalogs": list(catalogs.catalog.values()) if catalogs else [], "secrets_included": False}
