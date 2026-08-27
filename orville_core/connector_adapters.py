"""Provider-neutral connector adapter registry and safe generic HTTP adapter."""
from __future__ import annotations
import json
import mimetypes
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from .security import NetworkPolicy, SecretRedactor
from .provider_mcp_security import InvocationSecurityContext, ProviderMcpSecurityError, no_redirect_opener, reject_credential_values, validate_remote_endpoint

_EMPTY_SCHEMA = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}


def _open_connector_request(request: Request, *, timeout: float):
    return no_redirect_opener().open(request, timeout=timeout)

@dataclass(frozen=True)
class OperationSpec:
    operation_id: str
    label: str
    method: str = "GET"
    path: str = "/"
    risk_class: str = "read"
    input_schema: dict[str, Any] = field(default_factory=lambda: dict(_EMPTY_SCHEMA))
    enabled: bool = True
    output_schema: dict[str, Any] = field(default_factory=lambda: dict(_EMPTY_SCHEMA))
    pagination: dict[str, Any] = field(default_factory=dict)
    transfer: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ConnectorManifest:
    connector_id: str
    display_name: str
    auth_type: str
    documentation_url: str
    operations: tuple[OperationSpec, ...]
    supported: bool = False
    notes: str = ""
    version: str = "1.0.0"
    capabilities: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()
    limits: dict[str, Any] = field(default_factory=lambda: {"timeout_seconds": 30, "max_response_bytes": 5_000_000})
    support_state: str | None = None

    def __post_init__(self) -> None:
        if self.support_state is None:
            object.__setattr__(self, "support_state", "operational" if self.supported else "configuration_required")

@dataclass(frozen=True)
class AdapterResult:
    success: bool
    status_code: int | None
    data: Any
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

class ConnectorAdapterError(ValueError):
    pass


@dataclass(frozen=True)
class ConnectorTransferRequest:
    """Validated transfer intent passed to connector adapters."""

    direction: str
    path: str
    mime_type: str | None = None

    def validate(self) -> None:
        if self.direction not in {"upload", "download"}:
            raise ConnectorAdapterError("transfer direction must be upload or download")
        if not self.path.strip() or "\x00" in self.path:
            raise ConnectorAdapterError("transfer path is required and must not contain NUL bytes")


class FileTransferPolicy:
    """Constrain connector file operations to an approved local root."""

    def __init__(self, root: str | Path, *, max_bytes: int = 25_000_000, allowed_mime_types: set[str] | frozenset[str] | None = None) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max(1, min(int(max_bytes), 100_000_000))
        self.allowed_mime_types = frozenset(allowed_mime_types or ())

    def prepare(self, request: ConnectorTransferRequest) -> tuple[Path, bytes | None, str | None]:
        """Resolve a transfer request without permitting path escape or partial writes."""
        request.validate()
        if request.direction == "upload":
            path, body, mime_type = self.read_upload(request.path, mime_type=request.mime_type)
            return path, body, mime_type
        path, _partial = self.prepare_download(request.path)
        return path, None, None

    def resolve(self, candidate: str | Path, *, must_exist: bool) -> Path:
        path = Path(candidate).expanduser()
        resolved = path.resolve(strict=must_exist)
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ConnectorAdapterError("file path is outside the approved connector root") from exc
        if must_exist and not resolved.is_file():
            raise ConnectorAdapterError("file path must reference a regular file")
        return resolved

    def read_upload(self, candidate: str | Path, *, mime_type: str | None = None) -> tuple[Path, bytes, str]:
        path = self.resolve(candidate, must_exist=True)
        size = path.stat().st_size
        if size > self.max_bytes:
            raise ConnectorAdapterError("upload exceeds configured file-size limit")
        detected = mime_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if self.allowed_mime_types and detected not in self.allowed_mime_types:
            raise ConnectorAdapterError("upload MIME type is not allowed")
        return path, path.read_bytes(), detected

    def prepare_download(self, candidate: str | Path) -> tuple[Path, Path]:
        path = self.resolve(candidate, must_exist=False)
        if path.exists() and path.is_dir():
            raise ConnectorAdapterError("download destination must be a file")
        return path, path.with_name(path.name + ".part")

def provider_default_headers(connector_id: str) -> dict[str, str]:
    """Return non-secret protocol headers for known providers."""
    defaults = {"User-Agent": "Orville-Connector-Bridge/1"}
    if connector_id == "github":
        defaults.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    elif connector_id == "slack":
        defaults.update({"Accept": "application/json"})
    elif connector_id.startswith("google-"):
        defaults.update({"Accept": "application/json"})
    elif connector_id == "microsoft-outlook":
        defaults.update({"Accept": "application/json", "ConsistencyLevel": "eventual"})
    elif connector_id == "stripe":
        defaults.update({"Accept": "application/json"})
    return defaults


class ConnectorAdapterRegistry:
    def __init__(self) -> None:
        self._manifests: dict[str, ConnectorManifest] = {}
        self._handlers: dict[str, Callable[[OperationSpec, dict[str, Any]], AdapterResult]] = {}

    def register(self, manifest: ConnectorManifest, handler: Callable[[OperationSpec, dict[str, Any]], AdapterResult] | None = None) -> ConnectorManifest:
        if not manifest.connector_id.strip():
            raise ConnectorAdapterError("connector manifest requires an id")
        if any(item.risk_class not in {"read", "write", "sensitive", "critical"} for item in manifest.operations):
            raise ConnectorAdapterError("invalid operation risk class")
        self._manifests[manifest.connector_id] = manifest
        if handler:
            self._handlers[manifest.connector_id] = handler
        return manifest

    def get(self, connector_id: str) -> ConnectorManifest:
        try:
            return self._manifests[connector_id]
        except KeyError as exc:
            raise KeyError(f"connector adapter not registered: {connector_id}") from exc

    def list(self, *, supported_only: bool = False) -> tuple[ConnectorManifest, ...]:
        values = tuple(self._manifests.values())
        return tuple(item for item in values if item.supported) if supported_only else values

    def operations(self, connector_id: str) -> tuple[OperationSpec, ...]:
        return self.get(connector_id).operations

    def invoke(self, connector_id: str, operation_id: str, arguments: dict[str, Any], *, approved: bool = False, security_context: InvocationSecurityContext | None = None) -> AdapterResult:
        manifest = self.get(connector_id)
        operation = next((item for item in manifest.operations if item.operation_id == operation_id and item.enabled), None)
        if operation is None:
            raise ConnectorAdapterError(f"operation not available: {connector_id}/{operation_id}")
        if operation.risk_class in {"sensitive", "critical"} and not approved:
            raise PermissionError(f"operation requires explicit approval: {operation_id}")
        reject_credential_values(arguments)
        if security_context is not None:
            try:
                security_context.check_provider(connector_id)
                if operation.risk_class in {"write", "sensitive", "critical"}:
                    security_context.require_external_action(operation_id)
                else:
                    security_context.check_tool(operation_id)
            except ProviderMcpSecurityError as exc:
                raise PermissionError(str(exc)) from exc
        handler = self._handlers.get(connector_id)
        if handler is None:
            return AdapterResult(False, None, None, "provider-specific adapter is not configured")
        return handler(operation, arguments)

class GenericHttpAdapter:
    def __init__(self, base_url: str, headers: dict[str, str], *, allowed_hosts: set[str] | frozenset[str], allow_private: bool = False, timeout_seconds: float = 30, max_response_bytes: int = 5_000_000, max_retries: int = 2, backoff_seconds: float = 0.25, file_policy: FileTransferPolicy | None = None) -> None:
        try:
            self.base_url = validate_remote_endpoint(base_url, allowed_hosts=frozenset(allowed_hosts), allow_private=allow_private, allowed_ports=frozenset(range(1, 65536)) if allow_private else frozenset({80, 443}))
        except (ProviderMcpSecurityError, ValueError) as exc:
            raise ConnectorAdapterError(str(exc)) from exc
        self.headers = dict(headers)
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.max_retries = max(0, min(int(max_retries), 5))
        self.backoff_seconds = max(0.05, min(float(backoff_seconds), 10.0))
        self.policy = NetworkPolicy(frozenset(host.lower() for host in allowed_hosts), allow_private=allow_private)
        self.file_policy = file_policy

    @staticmethod
    def _pagination_meta(value: Any, operation: OperationSpec) -> dict[str, Any]:
        if not operation.pagination:
            return {}
        meta: dict[str, Any] = {"configured": dict(operation.pagination)}
        if isinstance(value, dict):
            next_value = value.get("next_cursor") or value.get("next_page") or value.get("next")
            if isinstance(value.get("links"), dict):
                next_value = next_value or value["links"].get("next")
            if next_value is not None:
                meta["next"] = next_value
            if "has_more" in value:
                meta["has_more"] = bool(value["has_more"])
            for key in ("page", "page_size", "total", "count"):
                if key in value:
                    meta[key] = value[key]
        return meta

    def __call__(self, operation: OperationSpec, arguments: dict[str, Any]) -> AdapterResult:
        method = operation.method.upper()
        try:
            path = operation.path.format(**{key: str(value) for key, value in arguments.items() if isinstance(value, (str, int, float))})
            url = f"{self.base_url}/{path.lstrip('/')}"
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ConnectorAdapterError("connector URL must use HTTP(S) with a hostname")
            self.policy.check_host(parsed.hostname)
            headers = dict(self.headers)
            body = None
            transfer_direction = str(operation.transfer.get("direction", "")).lower()
            download_target: tuple[Path, Path] | None = None
            if transfer_direction == "upload":
                if self.file_policy is None or not arguments.get("file_path"):
                    raise ConnectorAdapterError("upload operation requires a configured file policy and file_path")
                _, body, content_type = self.file_policy.read_upload(str(arguments["file_path"]), mime_type=arguments.get("mime_type"))
                headers.setdefault("Content-Type", content_type)
            elif transfer_direction == "download":
                if self.file_policy is None or not arguments.get("download_path"):
                    raise ConnectorAdapterError("download operation requires a configured file policy and download_path")
                download_target = self.file_policy.prepare_download(str(arguments["download_path"]))
            elif method in {"POST", "PUT", "PATCH", "DELETE"}:
                body = json.dumps(arguments).encode()
                headers.setdefault("Content-Type", "application/json")
            elif operation.pagination:
                query = {key: value for key, value in arguments.items() if key not in operation.input_schema.get("properties", {}) or key in {"page", "cursor", "limit", "offset"}}
                if query:
                    from urllib.parse import urlencode
                    separator = "&" if "?" in url else "?"
                    url = f"{url}{separator}{urlencode(query, doseq=True)}"
            request = Request(url, data=body, headers=headers, method=method)
            for attempt in range(self.max_retries + 1):
                try:
                    with _open_connector_request(request, timeout=self.timeout_seconds) as response:
                        raw = response.read(self.max_response_bytes + 1)
                        if download_target is not None:
                            if len(raw) > self.file_policy.max_bytes:  # type: ignore[union-attr]
                                return AdapterResult(False, response.status, None, "download exceeds configured file-size limit", {"attempt": attempt + 1})
                            destination, partial = download_target
                            partial.write_bytes(raw)
                            os.replace(partial, destination)
                            return AdapterResult(True, response.status, {"path": str(destination), "bytes": len(raw)}, meta={"attempt": attempt + 1, "transfer": "download"})
                        if len(raw) > self.max_response_bytes:
                            return AdapterResult(False, response.status, None, "connector response exceeds configured limit", {"attempt": attempt + 1})
                        text = raw.decode("utf-8", errors="replace")
                        try:
                            value: Any = json.loads(text)
                        except json.JSONDecodeError:
                            value = text
                        return AdapterResult(True, response.status, SecretRedactor.redact(value), meta={"attempt": attempt + 1, "pagination": self._pagination_meta(value, operation)})
                except HTTPError as exc:
                    retryable = exc.code in {408, 425, 429} or 500 <= exc.code <= 599
                    if not retryable or attempt >= self.max_retries:
                        retry_after = exc.headers.get("Retry-After") if exc.headers else None
                        meta = {"attempt": attempt + 1}
                        if retry_after:
                            meta["retry_after"] = retry_after
                        return AdapterResult(False, exc.code, None, f"connector returned HTTP {exc.code}", meta)
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    delay = float(retry_after) if retry_after and retry_after.replace('.', '', 1).isdigit() else self.backoff_seconds * (2 ** attempt)
                    time.sleep(min(delay, 10.0))
                except (URLError, TimeoutError) as exc:
                    if attempt >= self.max_retries:
                        return AdapterResult(False, None, None, str(exc)[:500], {"attempt": attempt + 1})
                    time.sleep(min(self.backoff_seconds * (2 ** attempt), 10.0))
        except (ConnectorAdapterError, ValueError) as exc:
            return AdapterResult(False, None, None, str(exc)[:500])

def priority_manifests() -> tuple[ConnectorManifest, ...]:
    read = dict(_EMPTY_SCHEMA)
    return (
        ConnectorManifest("github", "GitHub", "oauth2", "https://docs.github.com/en/rest", (OperationSpec("get_repository", "Get repository", path="/repos/{owner}/{repo}", input_schema={"type":"object","properties":{"owner":{"type":"string"},"repo":{"type":"string"}},"required":["owner","repo"],"additionalProperties":False}), OperationSpec("create_issue", "Create issue", "POST", "/repos/{owner}/{repo}/issues", "sensitive", {"type":"object","properties":{"owner":{"type":"string"},"repo":{"type":"string"},"title":{"type":"string"},"body":{"type":"string"}},"required":["owner","repo","title","body"],"additionalProperties":False})), True),
        ConnectorManifest("slack", "Slack", "oauth2", "https://api.slack.com/web", (OperationSpec("list_channels", "List channels", path="/conversations.list", input_schema=read), OperationSpec("send_message", "Send message", "POST", "/chat.postMessage", "sensitive", {"type":"object","properties":{"channel":{"type":"string"},"text":{"type":"string"}},"required":["channel","text"],"additionalProperties":False})), True),
        ConnectorManifest("notion", "Notion", "oauth2", "https://developers.notion.com/reference/intro", (OperationSpec("search", "Search pages", "POST", "/v1/search", input_schema={"type":"object","properties":{"query":{"type":"string"}},"required":["query"],"additionalProperties":False}), OperationSpec("update_page", "Update page", "PATCH", "/v1/pages/{page_id}", "sensitive", {"type":"object","properties":{"page_id":{"type":"string"},"properties":{"type":"object"}},"required":["page_id","properties"],"additionalProperties":False})), True),
        ConnectorManifest("google-gmail", "Gmail", "oauth2", "https://developers.google.com/gmail/api", (OperationSpec("list_messages", "List messages", path="/gmail/v1/users/me/messages", input_schema=read), OperationSpec("send_message", "Send email", "POST", "/gmail/v1/users/me/messages/send", "critical", {"type":"object","properties":{"raw":{"type":"string"}},"required":["raw"],"additionalProperties":False})), True),
        ConnectorManifest("google-calendar", "Google Calendar", "oauth2", "https://developers.google.com/calendar/api", (OperationSpec("list_events", "List events", path="/calendar/v3/calendars/primary/events", input_schema=read), OperationSpec("create_event", "Create event", "POST", "/calendar/v3/calendars/primary/events", "sensitive", {"type":"object","properties":{"summary":{"type":"string"},"start":{"type":"string"},"end":{"type":"string"}},"required":["summary","start","end"],"additionalProperties":False})), True),
        ConnectorManifest("microsoft-outlook", "Outlook Mail", "oauth2", "https://learn.microsoft.com/graph/api/resources/mail-api-overview", (OperationSpec("list_messages", "List messages", path="/v1.0/me/messages", input_schema=read), OperationSpec("send_message", "Send email", "POST", "/v1.0/me/sendMail", "critical", {"type":"object","properties":{"message":{"type":"object"}},"required":["message"],"additionalProperties":False})), True),
        ConnectorManifest("stripe", "Stripe", "api_key", "https://docs.stripe.com/api", (OperationSpec("list_customers", "List customers", path="/v1/customers", input_schema=read), OperationSpec("create_payment", "Create payment", "POST", "/v1/payment_intents", "critical", {"type":"object","properties":{"amount":{"type":"integer"},"currency":{"type":"string"}},"required":["amount","currency"],"additionalProperties":False})), True, "Use read-only mode until payment actions are approved."),
        ConnectorManifest("hubspot", "HubSpot", "oauth2", "https://developers.hubspot.com/docs/api/overview", (OperationSpec("list_contacts", "List contacts", path="/crm/v3/objects/contacts", input_schema=read), OperationSpec("create_contact", "Create contact", "POST", "/crm/v3/objects/contacts", "sensitive", {"type":"object","properties":{"properties":{"type":"object"}},"required":["properties"],"additionalProperties":False})), True),
        ConnectorManifest("n8n", "n8n", "api_key", "https://docs.n8n.io/api/", (OperationSpec("list_workflows", "List workflows", path="/api/v1/workflows", input_schema=read), OperationSpec("execute_workflow", "Execute workflow", "POST", "/api/v1/workflows/{workflow_id}/run", "critical", {"type":"object","properties":{"workflow_id":{"type":"string"},"data":{"type":"object"}},"required":["workflow_id","data"],"additionalProperties":False})), True),
    )
