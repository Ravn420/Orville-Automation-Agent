"""Local connector connection management for the standalone Windows release.

The catalog is descriptive metadata; provider-specific OAuth applications and
credentials remain user-owned. Secrets are protected with Windows DPAPI and
never returned by API responses. The store supports generic bearer/API-key
connections and OAuth2 authorization-code + PKCE flows when the user supplies
the provider's official endpoints.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class ConnectorConnectionError(RuntimeError):
    """Raised for invalid or unsafe connector connection operations."""


def _protect(value: str) -> str:
    raw = value.encode("utf-8")
    if os.name != "nt":
        raise ConnectorConnectionError("Protected connector credential storage requires Windows DPAPI")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    crypt = ctypes.windll.crypt32
    kernel = ctypes.windll.kernel32
    source = DATA_BLOB(len(raw), ctypes.cast(ctypes.create_string_buffer(raw), ctypes.POINTER(ctypes.c_byte)))
    target = DATA_BLOB()
    if not crypt.CryptProtectData(ctypes.byref(source), "Orville connector credential", None, None, None, 0, ctypes.byref(target)):
        raise ConnectorConnectionError("Windows DPAPI could not protect the connector credential")
    try:
        protected = ctypes.string_at(target.pbData, target.cbData)
    finally:
        kernel.LocalFree(target.pbData)
    return base64.b64encode(protected).decode("ascii")


def _unprotect(value: str) -> str:
    raw = base64.b64decode(value.encode("ascii"), validate=True)
    if os.name != "nt":
        raise ConnectorConnectionError("Protected connector credential storage requires Windows DPAPI")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    crypt = ctypes.windll.crypt32
    kernel = ctypes.windll.kernel32
    source = DATA_BLOB(len(raw), ctypes.cast(ctypes.create_string_buffer(raw), ctypes.POINTER(ctypes.c_byte)))
    target = DATA_BLOB()
    description = ctypes.c_wchar_p()
    if not crypt.CryptUnprotectData(ctypes.byref(source), ctypes.byref(description), None, None, None, 0, ctypes.byref(target)):
        raise ConnectorConnectionError("Windows DPAPI could not unlock the connector credential")
    try:
        return ctypes.string_at(target.pbData, target.cbData).decode("utf-8")
    finally:
        kernel.LocalFree(target.pbData)
        if description:
            kernel.LocalFree(description)


def _valid_uid(uid: str) -> bool:
    return bool(uid) and len(uid) <= 160 and all(char.isalnum() or char in "_.:-" for char in uid)


def _safe_http_url(value: str, *, allow_local: bool = False) -> str:
    parsed = urllib.parse.urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.fragment:
        raise ConnectorConnectionError("Connector URLs must be credential-free HTTP(S) URLs")
    host = (parsed.hostname or "").lower()
    if not allow_local and host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        raise ConnectorConnectionError("Local connector URLs require explicit local approval")
    return value.strip().rstrip("/")


@dataclass
class ConnectorConnection:
    uid: str
    display_name: str
    auth_type: str
    credential_header: str
    base_url: str
    status: str
    scopes: list[str]
    connected_at: float | None = None
    expires_at: float | None = None
    last_error: str | None = None
    operation_count: int = 0
    _secret: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    token_url: str | None = None
    auth_url: str | None = None
    redirect_uri: str | None = None
    state: str | None = None
    code_verifier: str | None = None
    refresh_token: str | None = None
    revoke_url: str | None = None

    def public(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("_secret", "client_secret", "state", "code_verifier", "refresh_token"):
            result.pop(key, None)
        result["has_credential"] = bool(self._secret)
        result["has_refresh_token"] = bool(self.refresh_token)
        result["revoke_configured"] = bool(self.revoke_url)
        return result


class ConnectorConnectionStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._records: dict[str, ConnectorConnection] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for raw in payload.get("connections", []):
            if not isinstance(raw, dict) or not raw.get("uid"):
                continue
            record = ConnectorConnection(**{key: raw.get(key) for key in ConnectorConnection.__dataclass_fields__ if key in raw})
            self._records[record.uid] = record

    def _save(self) -> None:
        payload = {"version": 1, "connections": [asdict(record) for record in self._records.values()], "updated_at": time.time()}
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def list_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [record.public() for record in sorted(self._records.values(), key=lambda item: item.display_name.lower())]

    def get(self, uid: str) -> ConnectorConnection | None:
        with self._lock:
            return self._records.get(uid)

    def connect_manual(self, *, uid: str, display_name: str, auth_type: str, credential_header: str, base_url: str, credential: str, scopes: list[str], allow_local: bool = False) -> dict[str, Any]:
        if not _valid_uid(uid):
            raise ConnectorConnectionError("invalid connector UID")
        if auth_type not in {"api_key", "bearer"}:
            raise ConnectorConnectionError("manual authentication must use api_key or bearer")
        if not credential_header or not all(char.isalnum() or char == "-" for char in credential_header):
            raise ConnectorConnectionError("credential header must contain only letters, numbers, and hyphens")
        if not credential.strip():
            raise ConnectorConnectionError("a connector credential is required")
        normalized_url = _safe_http_url(base_url, allow_local=allow_local)
        with self._lock:
            current = self._records.get(uid)
            record = ConnectorConnection(uid, display_name.strip() or uid, auth_type, credential_header.strip(), normalized_url, "connected", list(scopes), time.time(), _secret=_protect(credential.strip()), operation_count=current.operation_count if current else 0)
            self._records[uid] = record
            self._save()
            return record.public()

    def begin_oauth(self, *, uid: str, display_name: str, base_url: str, auth_url: str, token_url: str, client_id: str, client_secret: str | None, scopes: list[str], redirect_uri: str, revoke_url: str | None = None, allow_local: bool = False) -> dict[str, Any]:
        if not _valid_uid(uid):
            raise ConnectorConnectionError("invalid connector UID")
        if not client_id.strip():
            raise ConnectorConnectionError("OAuth client ID is required")
        normalized_base = _safe_http_url(base_url, allow_local=allow_local)
        normalized_auth = _safe_http_url(auth_url, allow_local=allow_local)
        normalized_token = _safe_http_url(token_url, allow_local=allow_local)
        normalized_revoke = _safe_http_url(revoke_url, allow_local=allow_local) if revoke_url else None
        parsed_redirect = urllib.parse.urlparse(redirect_uri)
        if parsed_redirect.scheme != "http" or parsed_redirect.hostname not in {"127.0.0.1", "localhost"}:
            raise ConnectorConnectionError("OAuth redirect URI must point to the local Orville callback")
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        query = urllib.parse.urlencode({"response_type": "code", "client_id": client_id.strip(), "redirect_uri": redirect_uri, "scope": " ".join(scopes), "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})
        authorization_url = f"{normalized_auth}{'&' if '?' in normalized_auth else '?'}{query}"
        with self._lock:
            record = ConnectorConnection(uid=uid, display_name=display_name.strip() or uid, auth_type="oauth2", credential_header="Authorization", base_url=normalized_base, status="authorization_required", scopes=list(scopes), client_id=client_id.strip(), client_secret=_protect(client_secret.strip()) if client_secret else None, token_url=normalized_token, auth_url=normalized_auth, redirect_uri=redirect_uri, state=state, code_verifier=verifier, revoke_url=normalized_revoke)
            self._records[uid] = record
            self._save()
            return {"connection": record.public(), "authorization_url": authorization_url}

    def complete_oauth(self, uid: str, code: str, state: str) -> dict[str, Any]:
        with self._lock:
            record = self._records.get(uid)
            if record is None or record.auth_type != "oauth2":
                raise ConnectorConnectionError("OAuth connection was not started")
            if not record.state or not secrets.compare_digest(record.state, state):
                raise ConnectorConnectionError("OAuth state validation failed")
            client_secret = _unprotect(record.client_secret) if record.client_secret else ""
            payload = {"grant_type": "authorization_code", "code": code, "redirect_uri": record.redirect_uri, "client_id": record.client_id, "code_verifier": record.code_verifier}
            if client_secret:
                payload["client_secret"] = client_secret
            request = urllib.request.Request(record.token_url or "", data=urllib.parse.urlencode(payload).encode(), headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Orville-Connector-Bridge/1"}, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    token_payload = json.loads(response.read(100_000).decode("utf-8"))
            except Exception as exc:
                record.status = "error"
                record.last_error = f"OAuth token exchange failed: {type(exc).__name__}"
                self._save()
                raise ConnectorConnectionError("OAuth token exchange failed; check provider settings") from exc
            access_token = token_payload.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise ConnectorConnectionError("OAuth provider did not return an access token")
            record._secret = _protect(access_token)
            refresh_token = token_payload.get("refresh_token")
            if isinstance(refresh_token, str) and refresh_token:
                record.refresh_token = _protect(refresh_token)
            record.status = "connected"
            record.connected_at = time.time()
            record.expires_at = time.time() + float(token_payload.get("expires_in", 0) or 0) if token_payload.get("expires_in") else None
            record.state = None
            record.code_verifier = None
            record.last_error = None
            self._save()
            return record.public()

    def refresh(self, uid: str) -> dict[str, Any]:
        with self._lock:
            record = self._records.get(uid)
            if record is None or record.auth_type != "oauth2" or not record.refresh_token:
                raise ConnectorConnectionError("connector has no refresh token")
            refresh_token = _unprotect(record.refresh_token)
            client_secret = _unprotect(record.client_secret) if record.client_secret else ""
            payload = {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": record.client_id or ""}
            if client_secret:
                payload["client_secret"] = client_secret
            request = urllib.request.Request(record.token_url or "", data=urllib.parse.urlencode(payload).encode(), headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Orville-Connector-Bridge/1"}, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    token_payload = json.loads(response.read(100_000).decode("utf-8"))
            except Exception as exc:
                record.status = "reauthorization_required"
                record.last_error = f"OAuth refresh failed: {type(exc).__name__}"
                self._save()
                raise ConnectorConnectionError("OAuth refresh failed; sign in again") from exc
            access_token = token_payload.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise ConnectorConnectionError("OAuth refresh did not return an access token")
            record._secret = _protect(access_token)
            replacement = token_payload.get("refresh_token")
            if isinstance(replacement, str) and replacement:
                record.refresh_token = _protect(replacement)
            record.status = "connected"
            record.expires_at = time.time() + float(token_payload.get("expires_in", 0) or 0) if token_payload.get("expires_in") else None
            record.last_error = None
            self._save()
            return record.public()

    def revoke(self, uid: str) -> bool:
        with self._lock:
            record = self._records.get(uid)
            if record is None:
                return False
            if record.revoke_url and record._secret:
                token = _unprotect(record._secret)
                payload = {"token": token, "client_id": record.client_id or ""}
                if record.client_secret:
                    payload["client_secret"] = _unprotect(record.client_secret)
                request = urllib.request.Request(record.revoke_url, data=urllib.parse.urlencode(payload).encode(), headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Orville-Connector-Bridge/1"}, method="POST")
                try:
                    with urllib.request.urlopen(request, timeout=20):
                        pass
                except Exception as exc:
                    record.last_error = f"provider revocation failed: {type(exc).__name__}"
                    self._save()
                    raise ConnectorConnectionError("provider revocation failed; local connection retained") from exc
            del self._records[uid]
            self._save()
            return True

    def disconnect(self, uid: str) -> bool:
        with self._lock:
            if uid not in self._records:
                return False
            del self._records[uid]
            self._save()
            return True

    def credential(self, uid: str) -> tuple[ConnectorConnection, str]:
        with self._lock:
            record = self._records.get(uid)
            if record is None or record.status != "connected" or not record._secret:
                raise ConnectorConnectionError("connector requires sign-in before invocation")
            return record, _unprotect(record._secret)

    def mark_operation(self, uid: str) -> None:
        with self._lock:
            if uid in self._records:
                self._records[uid].operation_count += 1
                self._save()
