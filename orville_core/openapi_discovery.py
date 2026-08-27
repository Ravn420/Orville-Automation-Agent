"""Fail-closed OpenAPI discovery for user-owned connector endpoints."""
from __future__ import annotations
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from .connector_adapters import OperationSpec
from .security import NetworkPolicy

_SAFE_OPERATION_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
_ALLOWED_METHODS = {"get", "post", "put", "patch", "delete"}

def discover_openapi(base_url: str, headers: dict[str, str], *, allowed_hosts: set[str] | frozenset[str], allow_private: bool = False, timeout_seconds: float = 10, max_bytes: int = 1_000_000, max_operations: int = 120) -> tuple[OperationSpec, ...]:
    parsed = urlparse(base_url.rstrip("/"))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("OpenAPI base URL must be HTTP(S) with a hostname")
    policy = NetworkPolicy(frozenset(host.lower() for host in allowed_hosts), allow_private=allow_private)
    policy.check_host(parsed.hostname)
    document: dict[str, Any] | None = None
    last_error: Exception | None = None
    for suffix in ("/openapi.json", "/openapi.yaml"):
        if suffix.endswith(".yaml"):
            continue
        url = urljoin(base_url.rstrip("/") + "/", suffix.lstrip("/"))
        try:
            with urlopen(Request(url, headers={**headers, "Accept": "application/json", "User-Agent": "Orville-Connector-Bridge/1"}), timeout=timeout_seconds) as response:
                raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("OpenAPI document exceeds configured limit")
            candidate = json.loads(raw.decode("utf-8"))
            if isinstance(candidate, dict) and isinstance(candidate.get("paths"), dict):
                document = candidate
                break
            raise ValueError("OpenAPI document has no valid paths object")
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    if document is None:
        raise ValueError(f"OpenAPI discovery failed: {type(last_error).__name__ if last_error else 'unavailable'}")
    operations: list[OperationSpec] = []
    seen: set[str] = set()
    for path, path_item in document["paths"].items():
        if not isinstance(path, str) or not path.startswith("/") or "//" in path or len(path) > 300 or not isinstance(path_item, dict):
            continue
        for method, raw_operation in path_item.items():
            method_lower = str(method).lower()
            if method_lower not in _ALLOWED_METHODS or not isinstance(raw_operation, dict):
                continue
            operation_id = str(raw_operation.get("operationId") or f"{method_lower}:{path}").replace("/", ".").replace("{", "").replace("}", "")
            operation_id = operation_id[:120]
            if not _SAFE_OPERATION_ID.match(operation_id) or operation_id in seen:
                continue
            seen.add(operation_id)
            risk = "read" if method_lower == "get" else "critical" if method_lower == "delete" else "write"
            if bool(raw_operation.get("x-orville-sensitive")):
                risk = "sensitive"
            schema: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}
            request_body = raw_operation.get("requestBody")
            if isinstance(request_body, dict):
                content = request_body.get("content")
                if isinstance(content, dict):
                    app_json = content.get("application/json")
                    if isinstance(app_json, dict) and isinstance(app_json.get("schema"), dict):
                        schema = app_json["schema"]
            pagination: dict[str, Any] = {}
            parameters = raw_operation.get("parameters")
            if isinstance(parameters, list):
                names = {str(item.get("name")) for item in parameters if isinstance(item, dict)}
                if names & {"page", "page_size", "limit", "cursor", "next_cursor", "offset"}:
                    pagination = {"parameter_names": sorted(names & {"page", "page_size", "limit", "cursor", "next_cursor", "offset"})}
            operations.append(OperationSpec(operation_id=operation_id, label=str(raw_operation.get("summary") or raw_operation.get("description") or operation_id)[:240], method=method_lower.upper(), path=path, risk_class=risk, input_schema=schema, output_schema={"type": "object"}, pagination=pagination))
            if len(operations) >= max_operations:
                return tuple(operations)
    return tuple(operations)
