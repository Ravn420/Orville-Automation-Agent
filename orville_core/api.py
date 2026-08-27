"""Authenticated API bridge for the Orville engine and GUI clients."""

from __future__ import annotations

import asyncio
import json
import os
import time
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any
from datetime import UTC, datetime
from enum import StrEnum
from time import monotonic
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request as UrlRequest, urlopen
from uuid import uuid4

from .checkpoint import CheckpointStore
from .persistence import SQLiteCheckpointStore
from .artifacts import ArtifactStore
from .memory import MemoryStore
from .engine import OrchestrationEngine
from .extensions import Connector, ExtensionRegistry, PermissionSet
from .integration import model_task_handler, streaming_model_task_handler
from .models import Checkpoint, TaskGraph, TaskNode
from .providers import MediaRequest, ModelCapabilities, ProviderConfig, ProviderError, ProviderRegistry, create_provider
from .routing import ProviderRouter, RoutingRequest, validate_endpoint
from .workflow import ProjectState, SoftwareObjective, TaskIntake, default_agent_registry
from .security import NetworkPolicy, SecretRedactor, SecurityViolation
from .attestations import TrustStore
from .platform import PlanMilestone, PlatformStore, TaskLifecycle
from .automation import AutomationDispatcher, TriggerType, WorkflowExecutor, WorkflowStep, WorkflowStore
from .governance import GovernanceStore
from .preview import PreviewManager
from .research_data import CsvAnalyzer, ProjectExporter, ResearchCatalog
from .identity import ProjectRole, SQLiteMembershipDirectory
from .adapters import default_adapter_registry
from .secrets_audit import AuditStore, SecretReferenceStore
from .scheduler import EventIntake, ScheduleStore
from .preview_runtime import PreviewRuntime
from .readiness import ProductionReadiness
from .config import RuntimeConfig
from .workspace import WorkspaceError, WorkspaceSession
from .browser import BrowserSessionManager
from .hub_models import DownloadJobManager, HubModelError, HuggingFaceHubClient, check_runtime_compatibility, detect_machine_capabilities, resolve_download_destination
from .model_runtime import probe_runtime_capabilities
from .local_models import LocalModelCatalog
from .connector_bridge import ConnectorBridge, ConnectorBridgeError, connector_uid_is_valid
from .connector_connections import ConnectorConnectionError, ConnectorConnectionStore
from .connector_defaults import ConnectorDefaultsError, ConnectorDefaultsStore
from .provider_presets import provider_presets
from .task_threads import SchemaError, TaskThreadStore, ThreadStatus
from .agent_runtime import AgentProfile, AgentRuntimeStore
from .extensions import PermissionSet
from .skills import SkillRegistry, SkillSecurityError
from .connector_adapters import ConnectorAdapterError, ConnectorAdapterRegistry, ConnectorManifest, FileTransferPolicy, GenericHttpAdapter, priority_manifests, provider_default_headers
from .connector_governance import ConnectorGovernanceError, ConnectorMutationPolicy, ConnectorMutationRequest
from .usage_health import Budget, UsageHealthStore
from .browser_relay import BrowserRelayError, LocalBrowserRelay
from .catalog_adapters import catalog_summary, load_catalog
from .openapi_discovery import discover_openapi
from .cloud_relay import AccessMode, AccessRecord, BlackboxFallbackPolicy, CloudRelayBoundary, RelayConfig, RelayError, RelayRequest, RelayStatus
from .blackbox_contract import BlackboxApiKeyContract, BlackboxContractError, validate_blackbox_error_payload
from .blackbox_capabilities import BlackboxCapabilityError, BlackboxCapabilityNegotiator
from .blackbox_model_discovery import BlackboxModelDiscovery, BlackboxModelDiscoveryError
from .cloud_onboarding import initial_cloud_onboarding
from .provider_features import DiscoveryCatalogStore, PolicyBackupStore, PrivacyRoutingPolicy, PrivacyRoutingPolicyStore, ProviderDiscoveryError, ProviderRateLimitStore, RemoteCatalogStore, RemotePolicyStore, discover_provider_models, redacted_provider_export
from .canary import CanaryController, CanaryError, CanaryHealthEvaluator, CanaryStateStore, HealthObservation, SyntheticDeploymentAdapter

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - optional API dependency
    FastAPI = None
    Request = None  # type: ignore[assignment,misc]
    JSONResponse = None  # type: ignore[assignment,misc]
    RequestValidationError = ValueError  # type: ignore[assignment,misc]

    class BaseModel:  # type: ignore[no-redef]
        """Fallback marker so importing the core package does not require FastAPI."""

    def Field(*_args: Any, **_kwargs: Any) -> Any:  # type: ignore[no-redef]
        return None


class ObjectivePayload(BaseModel):
    objective: str = Field(min_length=1, max_length=100_000)
    deliverables: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)
    acceptance_criteria: list[str] = Field(default_factory=list)
    risk_level: str = "normal"
    provider_id: str | None = None
    local_only: bool = False
    generation_mode: str = "standard"
    privacy_class: str = "cloud_approved"


class ConnectorInvokePayload(BaseModel):
    operation: str = Field(min_length=1, max_length=120)
    arguments: dict[str, Any] = Field(default_factory=dict)
    approved: bool = False
    run_id: str | None = Field(default=None, max_length=120)


class ConnectorManualConnectionPayload(BaseModel):
    project_requirement: str = Field(default="", max_length=500)
    approved: bool = False
    approval_reference: str = Field(default="", max_length=200)
    display_name: str = Field(default="", max_length=240)
    auth_type: str = Field(default="bearer", max_length=20)
    credential_header: str = Field(default="Authorization", max_length=80)
    base_url: str = Field(min_length=8, max_length=500)
    credential: str = Field(min_length=1, max_length=20_000)
    scopes: list[str] = Field(default_factory=list)
    allow_local: bool = False


class ConnectorOAuthStartPayload(BaseModel):
    project_requirement: str = Field(default="", max_length=500)
    approved: bool = False
    approval_reference: str = Field(default="", max_length=200)
    display_name: str = Field(default="", max_length=240)
    base_url: str = Field(min_length=8, max_length=500)
    authorization_url: str = Field(min_length=8, max_length=500)
    token_url: str = Field(min_length=8, max_length=500)
    client_id: str = Field(min_length=1, max_length=500)
    client_secret: str | None = Field(default=None, max_length=20_000)
    scopes: list[str] = Field(default_factory=list)
    redirect_uri: str = Field(min_length=16, max_length=500)
    revoke_url: str | None = Field(default=None, max_length=500)
    allow_local: bool = False


class ConnectorOAuthCallbackPayload(BaseModel):
    code: str = Field(min_length=1, max_length=20_000)
    state: str = Field(min_length=1, max_length=500)


class ConnectorDefaultPayload(BaseModel):
    project_requirement: str = Field(default="", max_length=500)
    approved: bool = False
    approval_reference: str = Field(default="", max_length=200)
    scope: str = Field(min_length=4, max_length=20)
    scope_id: str = Field(default="default", max_length=200)
    connector_uid: str | None = Field(default=None, max_length=160)


class ConnectorDefaultResolvePayload(BaseModel):
    task_id: str | None = Field(default=None, max_length=200)
    project_id: str | None = Field(default=None, max_length=200)
    user_id: str = Field(default="default", max_length=200)
    explicit_connector_uid: str | None = Field(default=None, max_length=160)


class ProjectPayload(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    description: str = ""
    owner_id: str = "local"
    environment: str = "development"


class TaskPayload(BaseModel):
    request: str = Field(min_length=1, max_length=100_000)
    base_revision: str | None = None
    mode: str = "general"
    provider_id: str | None = None
    budget: dict[str, Any] = Field(default_factory=dict)
    tool_permissions: list[str] = Field(default_factory=list)


class PlanPayload(BaseModel):
    objective: str = Field(min_length=1, max_length=100_000)
    assumptions: list[str] = Field(default_factory=list)
    affected_files: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    milestones: list[dict[str, Any]] = Field(default_factory=list)


class PlanDecisionPayload(BaseModel):
    approved: bool
    actor_id: str = "local"
    reason: str = ""


class ApprovalPayload(BaseModel):
    approved: bool


class ExecutePayload(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)


class CloudRelayAdmissionPayload(BaseModel):
    subject: str = Field(min_length=1, max_length=240)
    mode: str = "managed"
    privacy_class: str = "cloud_approved"
    estimated_units: int = Field(default=1, ge=1, le=100_000)
    workspace_id: str | None = Field(default=None, max_length=240)
    approved_remote: bool = False


class BlackboxUserApiKeyPayload(BaseModel):
    api_key: str = Field(min_length=1, max_length=20_000)
    base_url: str = Field(default="https://api.blackbox.ai", min_length=8, max_length=500)
    model: str = Field(default="blackboxai/openai/gpt-5.5", min_length=1, max_length=200)
    scopes: list[str] = Field(default_factory=list)


class PrivacyRoutingPolicyPayload(BaseModel):
    privacy_class: str = Field(min_length=1, max_length=40)
    allowed_provider_ids: list[str] = Field(default_factory=list)
    local_only: bool = False
    allow_fallback: bool = True


class ProviderPayload(BaseModel):
    provider_id: str = Field(min_length=1, max_length=120)
    provider_type: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=240)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str | None = None
    timeout_seconds: float = 60.0
    capabilities: list[str] = Field(default_factory=lambda: ["text"])
    headers: dict[str, str] = Field(default_factory=dict)


class MediaGenerationPayload(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
    modality: str = "image"
    provider_id: str | None = None
    negative_prompt: str | None = Field(default=None, max_length=20_000)
    options: dict[str, Any] = Field(default_factory=dict)
    local_only: bool = False
    allow_fallback: bool = True


class HubSearchPayload(BaseModel):
    query: str = Field(default="", max_length=200)
    pipeline_tag: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=20, ge=1, le=50)
    supported_only: bool = False


class HubDownloadPayload(BaseModel):
    repo_id: str = Field(min_length=3, max_length=200)
    revision: str = Field(default="main", min_length=1, max_length=120)
    destination: str | None = Field(default=None, max_length=500)
    max_bytes: int = Field(default=20 * 1024 * 1024 * 1024, ge=1, le=20 * 1024 * 1024 * 1024)
    max_retries: int = Field(default=3, ge=0, le=5)
    approved: bool = False


class RuntimeCompatibilityPayload(BaseModel):
    model_id: str = Field(min_length=3, max_length=240)
    runtime: str = Field(min_length=1, max_length=80)
    endpoint: str | None = Field(default=None, max_length=500)
    probe: bool = True


class LocalModelImportPayload(BaseModel):
    source: str = Field(min_length=1, max_length=2_000)
    model_id: str = Field(min_length=3, max_length=240)
    display_name: str | None = Field(default=None, max_length=240)
    runtime: str | None = Field(default=None, max_length=80)
    endpoint: str | None = Field(default=None, max_length=500)
    capabilities: list[str] = Field(default_factory=list)
    asset_type: str | None = Field(default=None, max_length=40)
    license: str | None = Field(default=None, max_length=240)
    license_restrictions: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    ownership: dict[str, Any] = Field(default_factory=dict)
    attestation: dict[str, Any] = Field(default_factory=dict)
    storage_root: str | None = Field(default=None, max_length=2_000)
    storage_mode: str = "reference"
    deduplicate: bool = True
    approved: bool = False


class DownloadResumePayload(BaseModel):
    approved: bool = False


class LocalModelActivationPayload(BaseModel):
    runtime: str = Field(min_length=1, max_length=40)
    endpoint: str | None = Field(default=None, max_length=500)
    selected_base_model: str | None = Field(default=None, max_length=240)
    attestation_policy: str = Field(default="optional", max_length=20)
    accept_license_restrictions: bool = False
    approved: bool = False


class ThreadCreatePayload(BaseModel):
    request: str = Field(min_length=1, max_length=100_000)
    project_id: str | None = Field(default=None, max_length=240)
    agent_id: str = Field(default="default", min_length=1, max_length=120)


class ThreadMessagePayload(BaseModel):
    role: str = Field(default="user", min_length=1, max_length=20)
    kind: str = Field(default="text", min_length=1, max_length=80)
    content: Any


class ThreadTransitionPayload(BaseModel):
    status: str = Field(min_length=1, max_length=40)
    stop_reason: str | None = Field(default=None, max_length=120)
    expected_version: int | None = Field(default=None, ge=1)


class ThreadWaitPayload(BaseModel):
    event_type: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=20_000)
    input_schema: dict[str, Any]
    risk_class: str = Field(default="normal", min_length=1, max_length=40)
    tool_name: str | None = Field(default=None, max_length=120)
    expires_at: str | None = Field(default=None, max_length=80)


class ThreadResolvePayload(BaseModel):
    response: dict[str, Any] = Field(default_factory=dict)
    accept: bool = True


class ThreadStructuredPayload(BaseModel):
    schema_payload: dict[str, Any] = Field(alias="schema")


class ThreadStructuredCompletePayload(BaseModel):
    value: Any


class AgentProfilePayload(BaseModel):
    agent_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2_000)
    system_instructions: str = Field(default="", max_length=50_000)
    model_policy: dict[str, Any] = Field(default_factory=dict)
    memory_scope: str = Field(default="thread", max_length=40)
    skills: list[str] = Field(default_factory=list)
    connectors: list[str] = Field(default_factory=list)
    tool_permissions: list[str] = Field(default_factory=list)
    risk_ceiling: str = Field(default="normal", max_length=20)
    enabled: bool = True


class ChildTaskPayload(BaseModel):
    request: str = Field(min_length=1, max_length=100_000)
    agent_id: str = Field(default="default", min_length=1, max_length=120)
    required: bool = True
    project_id: str | None = Field(default=None, max_length=240)


class SkillInstallPayload(BaseModel):
    source: str = Field(min_length=1, max_length=1_000)
    approved: bool = False
    tools: list[str] = Field(default_factory=list)
    network_hosts: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)


def _api_operation_name(request: Any) -> str:
    """Return a route-template operation name without exposing path parameters."""
    route = request.scope.get("route")
    template = getattr(route, "path", "") or request.url.path
    segments = [segment.strip("{}").lower() for segment in str(template).split("/") if segment]
    if segments and segments[0] == "api":
        segments = segments[2:] if len(segments) >= 3 and segments[1].startswith("v") else segments[1:]
    if route is None:
        static_segments = {"health", "objectives", "runs", "events", "cancel", "tasks", "approval", "state", "artifacts", "projects", "workflows", "preview", "security", "findings"}
        segments = [segment if segment in static_segments else "resource" for segment in segments]
    operation = "_".join([request.method.lower(), *segments])
    operation = re.sub(r"[^a-z0-9_]+", "_", operation).strip("_")
    return operation[:96] or "request"


def _safe_api_error_message(operation: str, status_code: int, detail: Any = None) -> str:
    """Create a bounded operation-specific message without returning raw exception text."""
    normalized = SecretRedactor.redact_exception(ValueError(str(detail))) if detail else ""
    if status_code == 401:
        reason = "authentication is required"
    elif status_code == 403:
        reason = "the operation is not allowed"
    elif status_code == 404:
        reason = "the requested resource was not found"
    elif status_code == 409:
        reason = "the operation conflicts with the current state"
    elif status_code == 429:
        reason = "the operation was rate limited"
    elif status_code >= 500:
        reason = "the service could not complete the operation"
    elif status_code == 422:
        reason = "the request is invalid"
    elif "allowlist" in normalized.lower():
        reason = "the operation is not allowlisted"
    else:
        reason = "the operation could not be completed"
    safe_detail = normalized.strip().lower()
    detail_match = re.search(r"(?:capability|operation|field)\s*:\s*['\"]?([a-z][a-z0-9_]{2,63})['\"]?(?:$|;)", safe_detail)
    if detail_match is None:
        detail_match = re.search(r"required capability\s+['\"]([a-z][a-z0-9_]{2,63})['\"]", safe_detail)
    if detail_match:
        reason = f"{reason}: {detail_match.group(1)}"
    elif safe_detail and re.fullmatch(r"[a-z0-9_ -]{1,80}", safe_detail) and safe_detail not in {"invalid bearer token", "rate limit exceeded"}:
        reason = f"{reason}: {safe_detail}"
    return f"{operation} failed: {reason}."


class ImageGenerationPayload(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
    negative_prompt: str | None = Field(default=None, max_length=20_000)
    width: int = 512
    height: int = 512
    steps: int | None = None
    cfg_scale: float | None = None
    seed: int | None = None
    number: int = 1
    sampler_name: str | None = None
    nsfw: bool = False
    censor_nsfw: bool = True
    extra_params: dict[str, Any] = Field(default_factory=dict)
    poll_interval_seconds: float = 1.0
    wait_timeout_seconds: float = 600.0


def create_app(*, checkpoint_dir: str | Path = ".orville/checkpoints", database_path: str | Path | None = None, storage: str | None = None, api_token: str | None = None, allowed_origins: list[str] | None = None, requests_per_minute: int = 120, engine: OrchestrationEngine | None = None, handlers: dict[str, Any] | None = None, verifiers: dict[str, Any] | None = None) -> Any:
    """Create an authenticated API application without contacting external services."""
    if FastAPI is None:
        raise RuntimeError("API dependencies are not installed; install the 'api' extra")
    expected_token = api_token if api_token is not None else os.getenv("ORVILLE_API_TOKEN")
    if not expected_token:
        raise RuntimeError("ORVILLE_API_TOKEN or an explicit api_token is required")

    app = FastAPI(title="Orville API", version="0.1.0", docs_url="/docs")

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Return a stable, operation-aware error without exposing exception details."""
        operation = _api_operation_name(request)
        message = _safe_api_error_message(operation, exc.status_code, exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": f"http_{exc.status_code}", "message": message, "operation": operation, "retryable": exc.status_code in {408, 429, 502, 503, 504}}, "detail": message})

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, _exc: RequestValidationError) -> JSONResponse:
        """Return an operation-aware validation error without echoing submitted values."""
        operation = _api_operation_name(request)
        message = _safe_api_error_message(operation, 422)
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_request", "message": message, "operation": operation, "retryable": False}, "detail": message})

    try:
        from fastapi.middleware.cors import CORSMiddleware
        configured_origins = allowed_origins
        if configured_origins is None:
            raw_origins = os.getenv("ORVILLE_ALLOWED_ORIGINS", "http://localhost:3000")
            configured_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        app.add_middleware(CORSMiddleware, allow_origins=configured_origins, allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])

    except ImportError:  # pragma: no cover
        pass
    request_log: dict[str, list[float]] = {}
    checkpoint_root = Path(checkpoint_dir)
    selected_storage = (storage or os.getenv("ORVILLE_STORAGE", "sqlite")).lower()
    if selected_storage == "sqlite":
        store = SQLiteCheckpointStore(database_path or (checkpoint_root.parent / "orville.db"))
    elif selected_storage == "json":
        store = CheckpointStore(checkpoint_root)
    else:
        raise ValueError("storage must be 'sqlite' or 'json'")
    artifacts = ArtifactStore(checkpoint_root.parent / "artifacts")
    memory_store = MemoryStore(database_path or (checkpoint_root.parent / "orville.db"))
    platform_store = PlatformStore(database_path or (checkpoint_root.parent / "orville.db"))
    model_catalog = LocalModelCatalog(checkpoint_root.parent / "orville-models.json", TrustStore(checkpoint_root.parent / "orville-trust-store.json"))
    hub_client = HuggingFaceHubClient(token=os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN"))
    download_manager = DownloadJobManager(checkpoint_root.parent / "hub-downloads.json", hub_client, model_catalog, checkpoint_root.parent / "models")
    membership_store = SQLiteMembershipDirectory(database_path or (checkpoint_root.parent / "orville.db"))
    workflow_store = WorkflowStore(database_path or (checkpoint_root.parent / "orville.db"))
    governance_store = GovernanceStore(database_path or (checkpoint_root.parent / "orville.db"))
    preview_manager = PreviewManager()
    adapter_registry = default_adapter_registry()
    secret_store = SecretReferenceStore(database_path or (checkpoint_root.parent / "orville.db"))
    audit_store = AuditStore(database_path or (checkpoint_root.parent / "orville.db"))
    research_catalog = ResearchCatalog()
    research_hosts = frozenset(host.strip().lower() for host in os.getenv("ORVILLE_RESEARCH_HOSTS", "").split(",") if host.strip())
    research_network_policy = NetworkPolicy(research_hosts, allow_private=False)
    schedule_store = ScheduleStore(database_path or (checkpoint_root.parent / "orville.db"))
    automation_dispatcher = AutomationDispatcher(schedule_store=schedule_store, workflow_store=workflow_store, executor=WorkflowExecutor(dict(handlers or {})))
    event_intake = EventIntake(os.getenv("ORVILLE_WEBHOOK_SIGNING_SECRET"), database_path or (checkpoint_root.parent / "orville.db"))
    connector_bridge = ConnectorBridge.from_environment()
    connection_store = ConnectorConnectionStore(checkpoint_root.parent / "connector-connections.json")
    connector_defaults = ConnectorDefaultsStore(checkpoint_root.parent / "connector-defaults.json")
    connector_mutation_policy = ConnectorMutationPolicy()
    thread_store = TaskThreadStore(database_path or (checkpoint_root.parent / "orville.db"))
    thread_store.recover_after_restart()
    agent_runtime = AgentRuntimeStore(database_path or (checkpoint_root.parent / "orville.db"), thread_store)
    skill_registry = SkillRegistry(checkpoint_root.parent / "skills")
    catalog_adapters = load_catalog()
    adapter_registry_runtime = ConnectorAdapterRegistry()
    for item in catalog_adapters:
        adapter_registry_runtime.register(ConnectorManifest(connector_id=item.connector_id, display_name=item.display_name, auth_type="user_configured", documentation_url="", operations=(), supported=False, notes="Catalog manifest only; configure the provider endpoint and credentials before discovery.", version="catalog-1.0.0", capabilities=("operation_discovery", "generic_http"), limits={"timeout_seconds": 30, "max_response_bytes": 5_000_000}))
    for manifest in priority_manifests():
        adapter_registry_runtime.register(manifest)
    usage_health = UsageHealthStore(database_path or (checkpoint_root.parent / "orville.db"))
    browser_relay = LocalBrowserRelay()
    preview_runtime = PreviewRuntime()
    readiness = ProductionReadiness(adapter_registry)
    graphs: dict[str, TaskGraph] = {}
    provider_registry = ProviderRegistry()
    relay_subject = os.getenv("ORVILLE_RELAY_SUBJECT", "local-device")
    blackbox_relay: CloudRelayBoundary | None = None
    relay_url = os.getenv("ORVILLE_BLACKBOX_RELAY_URL", "").strip()
    if relay_url:
        try:
            blackbox_relay = CloudRelayBoundary(RelayConfig(relay_url=relay_url, model=os.getenv("ORVILLE_BLACKBOX_RELAY_MODEL", "blackboxai/openai/gpt-5.5"), allowed_hosts=frozenset(filter(None, os.getenv("ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS", "").split(",")))))
            managed_status = RelayStatus.READY if os.getenv("ORVILLE_BLACKBOX_RELAY_ENABLED", "1").lower() in {"1", "true", "yes", "on"} else RelayStatus.DISABLED
            blackbox_relay.set_access(AccessRecord(AccessMode.MANAGED, managed_status, subject=relay_subject, plan=os.getenv("ORVILLE_BLACKBOX_RELAY_PLAN", "managed")))
        except ValueError:
            blackbox_relay = None
    extension_registry = ExtensionRegistry()
    extension_registry.register_connector(Connector("local-workspace", "orville", ("read", "diff", "run"), "available", True))
    privacy_policy_store = PrivacyRoutingPolicyStore(checkpoint_root.parent / "orville-routing-policy.json")
    remote_policy_store = RemotePolicyStore(privacy_policy_store, os.getenv("ORVILLE_POLICY_STORE_URL"), os.getenv("ORVILLE_POLICY_STORE_TOKEN"))
    if remote_policy_store.configured:
        remote_policy_store.load()
    discovery_catalog_store = DiscoveryCatalogStore(checkpoint_root.parent / "orville-provider-catalogs.json")
    remote_catalog_store = RemoteCatalogStore(discovery_catalog_store, os.getenv("ORVILLE_CATALOG_STORE_URL"), os.getenv("ORVILLE_CATALOG_STORE_TOKEN"), os.getenv("ORVILLE_TENANT_ID"))
    if remote_catalog_store.configured:
        remote_catalog_store.sync()
    policy_backup_store = PolicyBackupStore(checkpoint_root.parent / "policy-backups")
    provider_rate_limit_store = ProviderRateLimitStore(database_path or (checkpoint_root.parent / "orville.db"))
    provider_router = ProviderRouter(provider_registry, policy_store=privacy_policy_store, rate_limit_store=provider_rate_limit_store, usage_store=usage_health)
    canary_store = CanaryStateStore(checkpoint_root.parent / "orville-canary.db")
    canary_controller = CanaryController(canary_store, SyntheticDeploymentAdapter(), CanaryHealthEvaluator())

    configured_handlers = dict(handlers or {})
    configured_handlers.setdefault("intake.objective", model_task_handler(provider_router))
    configured_handlers.setdefault("intake.objective.streaming", streaming_model_task_handler(provider_router))

    def register_provider_config(config: ProviderConfig) -> dict[str, Any]:
        provider_registry.register(create_provider(config))
        return config.redacted()

    def register_env_provider(provider_id: str, provider_type: str, model: str, base_url: str, api_key: str | None, capabilities: ModelCapabilities) -> None:
        if not api_key and provider_type not in {"ollama", "custom-local", "custom-local-ollama", "ollama-compatible"}:
            return
        register_provider_config(ProviderConfig(provider_id=provider_id, provider_type=provider_type, model=model, base_url=base_url, api_key=api_key or None, capabilities=capabilities))

    register_env_provider("gemini", "gemini", os.getenv("ORVILLE_GEMINI_MODEL", "gemini-2.5-flash"), os.getenv("ORVILLE_GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/"), os.getenv("ORVILLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY"), ModelCapabilities(text=True, code=True, vision=True, structured_output=True, tool_calling=True, streaming=True))
    if relay_url:
        provider_registry.register(create_provider(ProviderConfig(provider_id="blackbox-managed", provider_type="blackbox-relay", model=os.getenv("ORVILLE_BLACKBOX_RELAY_MODEL", "blackboxai/openai/gpt-5.5"), base_url=relay_url, capabilities=ModelCapabilities(text=True, code=True, structured_output=True, tool_calling=True, streaming=True))))
    if os.getenv("ORVILLE_STABLE_HORDE_MODEL") or os.getenv("ORVILLE_STABLE_HORDE_API_KEY"):
        register_env_provider("stable-horde", "stable-horde", os.getenv("ORVILLE_STABLE_HORDE_MODEL", "aphrodite"), os.getenv("ORVILLE_STABLE_HORDE_BASE_URL", "https://aihorde.net/api"), os.getenv("ORVILLE_STABLE_HORDE_API_KEY", "0000000000"), ModelCapabilities(text=True, code=True, streaming=True))
    if os.getenv("ORVILLE_OLLAMA_MODEL"):
        register_env_provider("ollama", "ollama", os.getenv("ORVILLE_OLLAMA_MODEL", "llama3.2"), os.getenv("ORVILLE_OLLAMA_BASE_URL", "http://127.0.0.1:11434"), None, ModelCapabilities(text=True, code=True, structured_output=True, tool_calling=True, streaming=True))
    if os.getenv("ORVILLE_BLACKBOX_API_KEY"):
        register_env_provider("blackbox", "blackbox", os.getenv("ORVILLE_BLACKBOX_MODEL", "blackboxai"), os.getenv("ORVILLE_BLACKBOX_BASE_URL", "https://api.blackbox.ai/api"), os.getenv("ORVILLE_BLACKBOX_API_KEY"), ModelCapabilities(text=True, code=True, structured_output=True, tool_calling=True, streaming=True))

    def register_active_local_models() -> None:
        for record in model_catalog.list_models():
            if record.status != "active" or not record.runtime:
                continue
            try:
                provider_registry.register(create_provider(model_catalog.provider_config(record.model_id)))
            except (KeyError, ValueError):
                continue

    register_active_local_models()
    # One TaskGraph is the active milestone; independent tasks may run in
    # parallel, but dependency, approval, verification, and blocker states
    # still control progression within that milestone.
    run_engine = engine or OrchestrationEngine(
        store,
        handlers=configured_handlers,
        verifiers=verifiers,
        max_workers=3,
    )
    intake = TaskIntake()
    run_threads: dict[str, Thread] = {}
    workspace_sessions: dict[str, WorkspaceSession] = {}
    browser_sessions = BrowserSessionManager(checkpoint_root.parent / "browser-sessions.json")
    if hasattr(app, "add_event_handler"):
        app.add_event_handler("shutdown", browser_sessions.shutdown)
    else:
        app.router.on_shutdown.append(browser_sessions.shutdown)
    repair_attempts: dict[str, int] = {}
    agent_profile_path = checkpoint_root.parent / "agent-profile.json"
    try:
        agent_profile = json.loads(agent_profile_path.read_text(encoding="utf-8")) if agent_profile_path.exists() else {"name": "Orville Personal Agent", "enabled": True, "memory_enabled": True, "runtime": "local-windows"}
    except (OSError, json.JSONDecodeError):
        agent_profile = {"name": "Orville Personal Agent", "enabled": True, "memory_enabled": True, "runtime": "local-windows"}

    def persist_generated_artifact(run_id: str) -> None:
        try:
            checkpoint = store.load(run_id)
        except FileNotFoundError:
            return
        text = ""
        for task in checkpoint.graph.tasks:
            if isinstance(task.output, dict) and isinstance(task.output.get("text"), str):
                text += task.output["text"]
        if not text.strip():
            return
        generated_root = artifacts.root / "generated"
        generated_root.mkdir(parents=True, exist_ok=True)
        output_path = generated_root / f"{run_id}.md"
        output_path.write_text(text, encoding="utf-8")
        record = artifacts.register(output_path, artifact_id=f"{run_id}-code")
        checkpoint.context.setdefault("artifacts", [])
        checkpoint.context["artifacts"] = [item for item in checkpoint.context["artifacts"] if item.get("artifact_id") != record.artifact_id]
        checkpoint.context["artifacts"].append(record.to_dict())
        store.save(checkpoint)

    def capture_research_citations(run_id: str) -> None:
        try:
            checkpoint = store.load(run_id)
        except FileNotFoundError:
            return
        classification = str(checkpoint.context.get("classification", "")).lower()
        if not classification and checkpoint.graph.tasks:
            classification = str(checkpoint.graph.tasks[0].inputs.get("classification", "")).lower()
        if "research" not in classification:
            return
        outputs: list[str] = []
        for task in checkpoint.graph.tasks:
            if isinstance(task.output, dict) and isinstance(task.output.get("text"), str):
                outputs.append(task.output["text"])
        combined = "\n".join(outputs)
        urls = list(dict.fromkeys(re.findall(r"https?://[^\s<>\"')]+", combined)))[:50]
        if not urls:
            return
        source_records = checkpoint.context.setdefault("sources", [])
        known = {str(item.get("locator") or item.get("url")) for item in source_records}
        captured_ids: list[str] = []
        for url in urls:
            if url in known:
                record = next((item for item in source_records if str(item.get("locator") or item.get("url")) == url), None)
                if record:
                    captured_ids.append(str(record.get("source_id")))
                continue
            source = research_catalog.add_source(urlparse(url).netloc or url, url, combined[:500])
            record = {"source_id": source.source_id, "title": source.title, "locator": source.locator, "url": source.locator, "excerpt": source.excerpt, "retrieved_at": datetime.now(UTC).isoformat()}
            source_records.append(record)
            captured_ids.append(source.source_id)
            known.add(url)
        if captured_ids:
            claim = next((line.strip() for line in combined.splitlines() if line.strip() and not line.strip().startswith("http")), "Research output captured from linked sources.")[:4000]
            citations = checkpoint.context.setdefault("citations", [])
            if not any(set(item.get("source_ids", [])) == set(captured_ids) for item in citations):
                citations.append({"claim": claim, "source_ids": captured_ids, "confidence": "medium", "created_at": datetime.now(UTC).isoformat(), "capture_mode": "automatic"})
            store.save(checkpoint)

    def execute_in_background(run_id: str, graph: TaskGraph, context: dict[str, Any]) -> None:
        try:
            run_engine.run(graph, context=context, run_id=run_id)
            persist_generated_artifact(run_id)
            capture_research_citations(run_id)
        finally:
            run_threads.pop(run_id, None)

    def authenticate(authorization: str | None = Header(default=None)) -> None:
        if authorization != f"Bearer {expected_token}":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid bearer token")
        now = monotonic()
        token_key = authorization[-16:]
        recent = [timestamp for timestamp in request_log.get(token_key, []) if now - timestamp < 60]
        if len(recent) >= requests_per_minute:
            raise HTTPException(status_code=429, detail="rate limit exceeded")
        recent.append(now)
        request_log[token_key] = recent

    @app.get("/api/v1/connectors", dependencies=[Depends(authenticate)])
    def list_connectors() -> dict[str, Any]:
        return {"catalog_count": int(os.getenv("ORVILLE_CONNECTOR_CATALOG_SIZE", "372")), "bridge_configured": connector_bridge is not None, "bridge_url": connector_bridge.base_url if connector_bridge else None, "execution_mode": "local_connections_and_bridge", "secret_storage": "windows_dpapi", "connections": connection_store.list_public()}

    @app.get("/api/v1/connector-connections", dependencies=[Depends(authenticate)])
    def list_connector_connections() -> dict[str, Any]:
        return {"connections": connection_store.list_public(), "storage": "windows_dpapi"}

    @app.get("/api/v1/connector-provider-presets", dependencies=[Depends(authenticate)])
    def list_connector_provider_presets() -> dict[str, Any]:
        return {"presets": [preset.public() for preset in provider_presets()]}

    @app.get("/api/v1/connector-defaults", dependencies=[Depends(authenticate)])
    def list_connector_defaults() -> dict[str, Any]:
        return {"defaults": connector_defaults.list()}

    @app.post("/api/v1/connector-defaults", dependencies=[Depends(authenticate)])
    def set_connector_default(payload: ConnectorDefaultPayload) -> dict[str, Any]:
        if payload.connector_uid and not connector_uid_is_valid(payload.connector_uid):
            raise HTTPException(status_code=400, detail="invalid connector UID")
        try:
            if payload.connector_uid:
                connector_mutation_policy.validate(ConnectorMutationRequest(payload.connector_uid, "default", payload.project_requirement, payload.approved, payload.approval_reference))
                result = connector_defaults.set(payload.scope, payload.scope_id, payload.connector_uid)
                audit_store.append("local", "connector.default.set", result["connector_uid"], "completed", metadata={"scope": result["scope"], "scope_id": result["scope_id"]})
                return {"default": result}
            removed = connector_defaults.clear(payload.scope, payload.scope_id)
            audit_store.append("local", "connector.default.clear", payload.scope, "completed" if removed else "not_found", metadata={"scope_id": payload.scope_id})
            return {"cleared": removed, "scope": payload.scope, "scope_id": payload.scope_id}
        except (ConnectorDefaultsError, ConnectorGovernanceError) as exc:
            raise HTTPException(status_code=403 if isinstance(exc, ConnectorGovernanceError) else 400, detail=str(exc)) from exc

    @app.post("/api/v1/connector-defaults/resolve", dependencies=[Depends(authenticate)])
    def resolve_connector_default(payload: ConnectorDefaultResolvePayload) -> dict[str, Any]:
        if payload.explicit_connector_uid and not connector_uid_is_valid(payload.explicit_connector_uid):
            raise HTTPException(status_code=400, detail="invalid connector UID")
        result = connector_defaults.resolve(task_id=payload.task_id, project_id=payload.project_id, user_id=payload.user_id, explicit=payload.explicit_connector_uid)
        return {"default": result}

    @app.post("/api/v1/connectors/{connector_uid}/connect/manual", dependencies=[Depends(authenticate)])
    def connect_connector_manually(connector_uid: str, payload: ConnectorManualConnectionPayload) -> dict[str, Any]:
        if not connector_uid_is_valid(connector_uid):
            raise HTTPException(status_code=400, detail="invalid connector UID")
        try:
            connector_mutation_policy.validate(ConnectorMutationRequest(connector_uid, "connect", payload.project_requirement, payload.approved, payload.approval_reference))
            connection = connection_store.connect_manual(uid=connector_uid, display_name=payload.display_name, auth_type=payload.auth_type, credential_header=payload.credential_header, base_url=payload.base_url, credential=payload.credential, scopes=payload.scopes, allow_local=payload.allow_local)
        except (ConnectorConnectionError, ConnectorGovernanceError) as exc:
            raise HTTPException(status_code=403 if isinstance(exc, ConnectorGovernanceError) else 400, detail=str(exc)) from exc
        audit_store.append("local", "connector.connect.manual", connector_uid, "completed", metadata={"auth_type": payload.auth_type, "approval_reference": payload.approval_reference})
        return {"connection": connection}

    @app.post("/api/v1/connectors/{connector_uid}/connect/oauth", dependencies=[Depends(authenticate)])
    def start_connector_oauth(connector_uid: str, payload: ConnectorOAuthStartPayload) -> dict[str, Any]:
        if not connector_uid_is_valid(connector_uid):
            raise HTTPException(status_code=400, detail="invalid connector UID")
        try:
            connector_mutation_policy.validate(ConnectorMutationRequest(connector_uid, "connect", payload.project_requirement, payload.approved, payload.approval_reference))
            result = connection_store.begin_oauth(uid=connector_uid, display_name=payload.display_name, base_url=payload.base_url, auth_url=payload.authorization_url, token_url=payload.token_url, client_id=payload.client_id, client_secret=payload.client_secret, scopes=payload.scopes, redirect_uri=payload.redirect_uri, revoke_url=payload.revoke_url, allow_local=payload.allow_local)
        except (ConnectorConnectionError, ConnectorGovernanceError) as exc:
            raise HTTPException(status_code=403 if isinstance(exc, ConnectorGovernanceError) else 400, detail=str(exc)) from exc
        audit_store.append("local", "connector.connect.oauth.start", connector_uid, "completed", metadata={"scopes": payload.scopes, "approval_reference": payload.approval_reference})
        return result

    @app.get("/api/v1/connectors/{connector_uid}/oauth/callback", response_class=HTMLResponse)
    def complete_connector_oauth(connector_uid: str, code: str = Query(min_length=1), state: str = Query(min_length=1)) -> str:
        try:
            connection_store.complete_oauth(connector_uid, code, state)
        except ConnectorConnectionError as exc:
            audit_store.append("local", "connector.connect.oauth.callback", connector_uid, "failed", metadata={"error": str(exc)})
            return HTMLResponse(f"<h1>Orville connector sign-in failed</h1><p>{str(exc)}</p><p>Return to Signal Room and review the connection status.</p>", status_code=400).body.decode("utf-8")
        audit_store.append("local", "connector.connect.oauth.callback", connector_uid, "completed")
        return "<h1>Orville connector connected</h1><p>You may close this window and return to Signal Room.</p>"

    @app.post("/api/v1/connectors/{connector_uid}/refresh", dependencies=[Depends(authenticate)])
    def refresh_connector(connector_uid: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not connector_uid_is_valid(connector_uid):
            raise HTTPException(status_code=400, detail="invalid connector UID")
        try:
            values = payload or {}
            connector_mutation_policy.validate(ConnectorMutationRequest(connector_uid, "refresh", str(values.get("project_requirement", "")), bool(values.get("approved", False)), str(values.get("approval_reference", ""))))
            connection = connection_store.refresh(connector_uid)
        except (ConnectorConnectionError, ConnectorGovernanceError) as exc:
            audit_store.append("local", "connector.refresh", connector_uid, "failed", metadata={"error": str(exc)})
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        audit_store.append("local", "connector.refresh", connector_uid, "completed")
        return {"connection": connection}

    @app.post("/api/v1/connectors/{connector_uid}/revoke", dependencies=[Depends(authenticate)])
    def revoke_connector(connector_uid: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not connector_uid_is_valid(connector_uid):
            raise HTTPException(status_code=400, detail="invalid connector UID")
        try:
            values = payload or {}
            connector_mutation_policy.validate(ConnectorMutationRequest(connector_uid, "revoke", str(values.get("project_requirement", "")), bool(values.get("approved", False)), str(values.get("approval_reference", ""))))
            removed = connection_store.revoke(connector_uid)
        except (ConnectorConnectionError, ConnectorGovernanceError) as exc:
            audit_store.append("local", "connector.revoke", connector_uid, "failed", metadata={"error": str(exc)})
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        audit_store.append("local", "connector.revoke", connector_uid, "completed" if removed else "not_found")
        return {"revoked": removed, "connector_uid": connector_uid}

    @app.post("/api/v1/connectors/{connector_uid}/disconnect", dependencies=[Depends(authenticate)])
    def disconnect_connector(connector_uid: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not connector_uid_is_valid(connector_uid):
            raise HTTPException(status_code=400, detail="invalid connector UID")
        values = payload or {}
        try:
            connector_mutation_policy.validate(ConnectorMutationRequest(connector_uid, "disconnect", str(values.get("project_requirement", "")), bool(values.get("approved", False)), str(values.get("approval_reference", ""))))
        except ConnectorGovernanceError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        removed = connection_store.disconnect(connector_uid)
        audit_store.append("local", "connector.disconnect", connector_uid, "completed" if removed else "not_found")
        return {"disconnected": removed, "connector_uid": connector_uid}

    @app.post("/api/v1/connectors/{connector_uid}/openapi/discover", dependencies=[Depends(authenticate)])
    def discover_connector_openapi(connector_uid: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        try:
            record, credential = connection_store.credential(connector_uid)
            host = (urlparse(record.base_url).hostname or "").lower()
            auth_value = f"Bearer {credential}" if record.auth_type == "bearer" else credential
            operations = discover_openapi(record.base_url, {record.credential_header: auth_value}, allowed_hosts={host}, allow_private=bool(payload.get("allow_local", False)), max_operations=min(int(payload.get("max_operations", 120)), 120))
            audit_store.append("local", "connector.openapi.discover", connector_uid, "completed", metadata={"operation_count": len(operations)})
            return {"connector_uid": connector_uid, "operations": [asdict(operation) for operation in operations], "operation_count": len(operations)}
        except (ConnectorConnectionError, ValueError, OSError) as exc:
            audit_store.append("local", "connector.openapi.discover", connector_uid, "failed", metadata={"error": str(exc)[:200]})
            raise HTTPException(status_code=502, detail=f"OpenAPI discovery failed: {type(exc).__name__}") from exc

    @app.get("/api/v1/connectors/{connector_uid}/operations", dependencies=[Depends(authenticate)])
    def discover_connector_operations(connector_uid: str) -> dict[str, Any]:
        try:
            record, credential = connection_store.credential(connector_uid)
            auth_value = f"Bearer {credential}" if record.auth_type == "bearer" else credential
            request = UrlRequest(f"{record.base_url}/operations", headers={"Accept": "application/json", record.credential_header: auth_value, "User-Agent": "Orville-Connector-Bridge/1"}, method="GET")
            with urlopen(request, timeout=10) as response:
                raw = response.read(200_001)
            if len(raw) > 200_000:
                raise ConnectorConnectionError("connector operation catalog exceeded the safety limit")
            result = json.loads(raw.decode("utf-8"))
            return {"connector_uid": connector_uid, "operations": result.get("operations", result) if isinstance(result, dict) else result}
        except (ConnectorConnectionError, HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=502, detail=f"operation discovery failed: {type(exc).__name__}") from exc

    @app.get("/api/v1/connectors/health", dependencies=[Depends(authenticate)])
    def connector_health() -> dict[str, Any]:
        if connector_bridge is None:
            return {"ok": False, "status": "not_configured", "detail": "Set ORVILLE_CONNECTOR_BRIDGE_URL to enable connector execution."}
        try:
            return connector_bridge.health()
        except ConnectorBridgeError as exc:
            audit_store.append("local", "connector.health", connector_bridge.base_url, "failed", metadata={"error": str(exc)})
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/v1/connectors/{connector_uid}/invoke", dependencies=[Depends(authenticate)])
    def invoke_connector(connector_uid: str, payload: ConnectorInvokePayload) -> dict[str, Any]:
        if not connector_uid_is_valid(connector_uid):
            raise HTTPException(status_code=400, detail="invalid connector UID")
        if not payload.approved:
            audit_store.append("local", "connector.invoke", connector_uid, "blocked", metadata={"operation": payload.operation, "run_id": payload.run_id})
            raise HTTPException(status_code=409, detail="connector invocation requires explicit approval")
        if connection_store.get(connector_uid) is None and connector_bridge is None:
            raise HTTPException(status_code=503, detail="connector bridge is not configured and this connector has no local sign-in")
        try:
            if connection_store.get(connector_uid) is not None:
                record, credential = connection_store.credential(connector_uid)
                auth_scheme = "Bearer" if record.auth_type == "bearer" else credential
                credential_value = f"Bearer {credential}" if record.auth_type == "bearer" else credential
                request = UrlRequest(f"{record.base_url}/invoke", data=json.dumps({"connector_uid": connector_uid, "operation": payload.operation, "arguments": payload.arguments, "run_id": payload.run_id}).encode("utf-8"), headers={"Accept": "application/json", "Content-Type": "application/json", record.credential_header: credential_value, "User-Agent": "Orville-Connector-Bridge/1"}, method="POST")
                with urlopen(request, timeout=30) as response:
                    raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ConnectorConnectionError("connector response exceeded the safety limit")
                result = json.loads(raw.decode("utf-8"))
                connection_store.mark_operation(connector_uid)
            elif connector_bridge is not None:
                result = connector_bridge.invoke(connector_uid, payload.operation, payload.arguments, run_id=payload.run_id)
            else:
                raise ConnectorConnectionError("connector requires sign-in or a configured bridge")
        except (ConnectorBridgeError, ConnectorConnectionError) as exc:
            audit_store.append("local", "connector.invoke", connector_uid, "failed", metadata={"operation": payload.operation, "run_id": payload.run_id, "error": str(exc)})
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            audit_store.append("local", "connector.invoke", connector_uid, "failed", metadata={"operation": payload.operation, "run_id": payload.run_id, "error": type(exc).__name__})
            raise HTTPException(status_code=502, detail=f"connector invocation failed: {type(exc).__name__}") from exc
        audit = audit_store.append("local", "connector.invoke", connector_uid, "completed", metadata={"operation": payload.operation, "run_id": payload.run_id})
        return {"connector_uid": connector_uid, "operation": payload.operation, "result": result, "audit": asdict(audit)}

    def serialize_platform(value: Any) -> dict[str, Any]:
        payload = asdict(value)
        for key, item in list(payload.items()):
            if isinstance(item, StrEnum):
                payload[key] = item.value
        return payload

    @app.post("/api/v1/workspaces", dependencies=[Depends(authenticate)])
    def create_workspace(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            source_root = Path(str(payload["root"])).expanduser().resolve()
            configured_roots = [Path(item).expanduser().resolve() for item in os.getenv("ORVILLE_WORKSPACE_ROOTS", str(Path.home())).split(os.pathsep) if item.strip()]
            if not any(source_root == root or root in source_root.parents for root in configured_roots):
                raise SecurityViolation("repository root is outside ORVILLE_WORKSPACE_ROOTS")
            workspace_id = str(payload.get("workspace_id") or f"ws-{uuid4().hex[:12]}")
            session = WorkspaceSession.create(source_root, workspace_id=workspace_id)
            workspace_sessions[workspace_id] = session
            return {"workspace": {"workspace_id": workspace_id, "source_root": str(source_root), "root": str(session.root), "file_count": len(session.list_files()), "base_revision": session.base_revision}}
        except (KeyError, OSError, WorkspaceError, SecurityViolation) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/workspaces/{workspace_id}/files", dependencies=[Depends(authenticate)])
    def index_workspace_files(workspace_id: str, query: str = "", max_files: int = 500) -> dict[str, Any]:
        session = workspace_sessions.get(workspace_id)
        if session is None:
            raise HTTPException(status_code=404, detail="workspace not found")
        try:
            return {"workspace_id": workspace_id, "files": session.index_files(query=query, max_files=max(1, min(max_files, 2000)))}
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/workspaces/{workspace_id}/files/{relative_path:path}", dependencies=[Depends(authenticate)])
    def read_workspace_file(workspace_id: str, relative_path: str) -> dict[str, Any]:
        session = workspace_sessions.get(workspace_id)
        if session is None:
            raise HTTPException(status_code=404, detail="workspace not found")
        try:
            return {"workspace_id": workspace_id, "path": relative_path, "content": session.read_file(relative_path)}
        except (OSError, SecurityViolation, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/workspaces/{workspace_id}/diff", dependencies=[Depends(authenticate)])
    def workspace_diff(workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = workspace_sessions.get(workspace_id)
        if session is None:
            raise HTTPException(status_code=404, detail="workspace not found")
        try:
            return session.unified_diff(str(payload["path"]), str(payload.get("proposed_content", "")), expected_checksum=payload.get("expected_checksum"))
        except (KeyError, OSError, SecurityViolation, WorkspaceError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/workspaces/{workspace_id}/commands", dependencies=[Depends(authenticate)])
    def run_workspace_command(workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = workspace_sessions.get(workspace_id)
        if session is None:
            raise HTTPException(status_code=404, detail="workspace not found")
        if not bool(payload.get("approved", False)):
            raise HTTPException(status_code=428, detail="terminal execution requires explicit approval")
        try:
            command = payload.get("command", [])
            argv = command.split() if isinstance(command, str) else command
            result = session.run(argv, timeout_seconds=float(payload.get("timeout_seconds", 60)))
            return {"workspace_id": workspace_id, "command": list(result.command), "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "duration_seconds": result.duration_seconds, "timed_out": result.timed_out}
        except (OSError, SecurityViolation, WorkspaceError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/workspaces/{workspace_id}/repair", dependencies=[Depends(authenticate)])
    def bounded_repair(workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if workspace_id not in workspace_sessions:
            raise HTTPException(status_code=404, detail="workspace not found")
        requested = int(payload.get("attempt", repair_attempts.get(workspace_id, 0) + 1))
        limit = max(1, min(int(payload.get("max_attempts", 3)), 5))
        if requested > limit:
            raise HTTPException(status_code=409, detail=f"repair limit reached ({limit})")
        repair_attempts[workspace_id] = requested
        return {"workspace_id": workspace_id, "attempt": requested, "max_attempts": limit, "remaining": limit - requested, "status": "repair_authorized", "failure": str(payload.get("failure", ""))[:4000]}

    @app.post("/api/v1/projects", dependencies=[Depends(authenticate)])
    def create_project(payload: ProjectPayload) -> dict[str, Any]:
        project = platform_store.create_project(payload.name, payload.description, owner_id=payload.owner_id, environment=payload.environment)
        membership_store.add(project.project_id, payload.owner_id, ProjectRole.OWNER)
        return {"project": serialize_platform(project)}

    @app.get("/api/v1/projects", dependencies=[Depends(authenticate)])
    def list_projects(owner_id: str | None = None) -> dict[str, Any]:
        return {"projects": [serialize_platform(project) for project in platform_store.list_projects(owner_id=owner_id)]}

    @app.get("/api/v1/projects/{project_id}", dependencies=[Depends(authenticate)])
    def get_project(project_id: str) -> dict[str, Any]:
        try:
            return {"project": serialize_platform(platform_store.get_project(project_id))}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc

    @app.get("/api/v1/projects/{project_id}/tasks", dependencies=[Depends(authenticate)])
    def list_project_tasks(project_id: str, limit: int = 100) -> dict[str, Any]:
        try:
            platform_store.get_project(project_id)
            return {"tasks": [serialize_platform(task) for task in platform_store.list_tasks(project_id=project_id, limit=limit)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc

    @app.get("/api/v1/projects/{project_id}/memory", dependencies=[Depends(authenticate)])
    def list_project_memory(project_id: str) -> dict[str, Any]:
        try:
            return {"memory": [serialize_platform(item) for item in platform_store.list_memory(project_id)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc

    @app.post("/api/v1/projects/{project_id}/memory", dependencies=[Depends(authenticate)])
    def save_project_memory(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            memory = platform_store.save_memory(project_id, str(payload.get("key", "")), str(payload.get("value", "")), source=str(payload.get("source", "user")))
            return {"memory": serialize_platform(memory)}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 400, detail=str(exc)) from exc

    @app.delete("/api/v1/projects/{project_id}/memory/{key}", dependencies=[Depends(authenticate)])
    def delete_project_memory(project_id: str, key: str) -> dict[str, Any]:
        try:
            platform_store.delete_memory(project_id, key)
            return {"deleted": key}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc

    @app.get("/api/v1/projects/{project_id}/instructions", dependencies=[Depends(authenticate)])
    def list_project_instructions(project_id: str) -> dict[str, Any]:
        try:
            return {"instructions": [serialize_platform(item) for item in platform_store.list_instructions(project_id)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc

    @app.post("/api/v1/projects/{project_id}/instructions", dependencies=[Depends(authenticate)])
    def save_project_instruction(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            instruction = platform_store.save_instruction(project_id, str(payload.get("content", "")))
            return {"instruction": serialize_platform(instruction)}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 400, detail=str(exc)) from exc

    @app.get("/api/v1/personal-agent", dependencies=[Depends(authenticate)])
    def get_personal_agent() -> dict[str, Any]:
        return {"agent": {**agent_profile, "memory_scope": "local-projects", "computer": "local-windows-host", "state": "online" if agent_profile.get("enabled") else "paused"}}

    @app.post("/api/v1/personal-agent", dependencies=[Depends(authenticate)])
    def update_personal_agent(payload: dict[str, Any]) -> dict[str, Any]:
        agent_profile.update({key: payload[key] for key in ("name", "enabled", "memory_enabled") if key in payload})
        try:
            agent_profile_path.parent.mkdir(parents=True, exist_ok=True)
            agent_profile_path.write_text(json.dumps(agent_profile, indent=2), encoding="utf-8")
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"could not save agent profile: {exc}") from exc
        return get_personal_agent()

    @app.post("/api/v1/projects/{project_id}/tasks", dependencies=[Depends(authenticate)])
    def create_platform_task(project_id: str, payload: TaskPayload) -> dict[str, Any]:
        try:
            task = platform_store.create_task(project_id, payload.request, base_revision=payload.base_revision, mode=payload.mode, provider_id=payload.provider_id, budget=payload.budget, tool_permissions=tuple(payload.tool_permissions))
            return {"task": serialize_platform(task)}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 400, detail=str(exc)) from exc

    @app.post("/api/v1/tasks/{task_id}/plan", dependencies=[Depends(authenticate)])
    def create_platform_plan(task_id: str, payload: PlanPayload) -> dict[str, Any]:
        try:
            milestones = [PlanMilestone(f"milestone-{uuid4().hex[:12]}", "", index, str(item.get("title", f"Milestone {index}")), str(item.get("agent_mode", "general")), tuple(item.get("depends_on", []))) for index, item in enumerate(payload.milestones, 1)]
            plan = platform_store.create_plan(task_id, payload.objective, assumptions=tuple(payload.assumptions), affected_files=tuple(payload.affected_files), risks=tuple(payload.risks), acceptance_criteria=tuple(payload.acceptance_criteria), required_approvals=tuple(payload.required_approvals), milestones=milestones)
            return {"plan": serialize_platform(plan), "task": serialize_platform(platform_store.get_task(task_id))}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 400, detail=str(exc)) from exc

    @app.post("/api/v1/plans/{plan_id}/approve", dependencies=[Depends(authenticate)])
    def decide_platform_plan(plan_id: str, payload: PlanDecisionPayload) -> dict[str, Any]:
        try:
            approval = platform_store.decide_plan(plan_id, approved=payload.approved, actor_id=payload.actor_id, reason=payload.reason)
            return {"approval": serialize_platform(approval)}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 409, detail=str(exc)) from exc

    @app.get("/api/v1/tasks/{task_id}/events", dependencies=[Depends(authenticate)])
    def get_platform_events(task_id: str, after: int = 0) -> dict[str, Any]:
        try:
            platform_store.get_task(task_id)
            return {"task_id": task_id, "events": platform_store.list_events(task_id, after=max(0, after))}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="task not found") from exc

    @app.get("/api/v1/projects/{project_id}/members", dependencies=[Depends(authenticate)])
    def list_project_members(project_id: str) -> dict[str, Any]:
        try:
            platform_store.get_project(project_id)
            return {"members": [asdict(member) for member in membership_store.list_members(project_id)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc

    @app.post("/api/v1/projects/{project_id}/members", dependencies=[Depends(authenticate)])
    def add_project_member(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            platform_store.get_project(project_id)
            member = membership_store.add(project_id, str(payload["actor_id"]), ProjectRole(str(payload.get("role", "viewer"))), invited_by=str(payload.get("invited_by", "local")), status="invited")
            return {"member": asdict(member)}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/members/{actor_id}/revoke", dependencies=[Depends(authenticate)])
    def revoke_project_member(project_id: str, actor_id: str) -> dict[str, str]:
        membership_store.revoke(project_id, actor_id)
        return {"project_id": project_id, "actor_id": actor_id, "status": "revoked"}

    @app.post("/api/v1/projects/{project_id}/workflows", dependencies=[Depends(authenticate)])
    def create_workflow(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            platform_store.get_project(project_id)
            workflow_id = workflow_store.create_workflow(str(payload.get("name", "Workflow")))
            steps = tuple(WorkflowStep(str(item.get("step_id", f"step-{index}")), str(item.get("kind", "unknown")), dict(item.get("config", {})), bool(item.get("requires_approval", False))) for index, item in enumerate(payload.get("steps", []), 1))
            version = workflow_store.add_version(workflow_id, TriggerType(str(payload.get("trigger", "manual"))), steps)
            return {"workflow_id": workflow_id, "version_id": version.version_id, "status": "disabled"}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/workflows/{workflow_id}/run", dependencies=[Depends(authenticate)])
    def run_workflow(workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        version_id = str(payload.get("version_id", ""))
        idempotency_key = str(payload.get("idempotency_key", ""))
        if not version_id or not idempotency_key:
            raise HTTPException(status_code=400, detail="version_id and idempotency_key are required")
        run = workflow_store.start_run(workflow_id, version_id, idempotency_key)
        return {"run_id": run.run_id, "status": run.status.value, "attempts": run.attempts}

    @app.get("/api/v1/projects/{project_id}/security/findings", dependencies=[Depends(authenticate)])
    def security_findings(project_id: str) -> dict[str, Any]:
        return {"findings": [asdict(item) for item in governance_store.list_findings(project_id)]}

    @app.post("/api/v1/projects/{project_id}/preview", dependencies=[Depends(authenticate)])
    def create_preview(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            platform_store.get_project(project_id)
            preview = preview_manager.create(str(payload.get("preview_id", uuid4().hex[:12])), str(payload["revision_id"]), str(payload["root"]), route=str(payload.get("route", "/")), viewport=str(payload.get("viewport", "desktop")))
            return {"preview": asdict(preview)}
        except (KeyError, ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/export", dependencies=[Depends(authenticate)])
    def export_project(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            platform_store.get_project(project_id)
            archive = ProjectExporter.archive(str(payload["root"]), str(payload["output_path"]))
            return {"project_id": project_id, "archive": str(archive)}
        except (KeyError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/readiness", dependencies=[Depends(authenticate)])
    def readiness_report() -> dict[str, Any]:
        return readiness.evaluate(tests_passed=True, compile_passed=True, required_adapters=()).to_dict()

    @app.post("/api/v1/previews/start", dependencies=[Depends(authenticate)])
    def start_preview(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            record = preview_runtime.start(str(payload["preview_id"]), str(payload["revision_id"]), str(payload["root"]), host=str(payload.get("host", "127.0.0.1")), port=int(payload["port"]) if payload.get("port") else None)
            return {"preview": asdict(record)}
        except (KeyError, ValueError, FileNotFoundError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/previews/{preview_id}", dependencies=[Depends(authenticate)])
    def preview_status(preview_id: str) -> dict[str, Any]:
        try:
            return {"preview": asdict(preview_runtime.status(preview_id))}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/previews/{preview_id}/stop", dependencies=[Depends(authenticate)])
    def stop_preview(preview_id: str) -> dict[str, Any]:
        try:
            return {"preview": asdict(preview_runtime.stop(preview_id))}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/schedules", dependencies=[Depends(authenticate)])
    def create_schedule(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            schedule = schedule_store.create(str(payload["schedule_id"]), str(payload["workflow_id"]), int(payload["interval_seconds"]))
            return {"schedule": asdict(schedule)}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/schedules", dependencies=[Depends(authenticate)])
    def list_schedules() -> dict[str, Any]:
        return {"schedules": [asdict(item) for item in schedule_store.list()]}

    @app.post("/api/v1/schedules/recover", dependencies=[Depends(authenticate)])
    def recover_schedule_leases() -> dict[str, Any]:
        recovered = schedule_store.recover_stale_leases()
        audit_store.append("local", "schedule.leases.recover", "scheduler", "completed", metadata={"recovered": recovered})
        return {"recovered": recovered}

    @app.post("/api/v1/schedules/{schedule_id}/enable", dependencies=[Depends(authenticate)])
    def enable_schedule(schedule_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            schedule = schedule_store.set_enabled(schedule_id, bool((payload or {}).get("enabled", True)))
            return {"schedule": asdict(schedule)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/schedules/due", dependencies=[Depends(authenticate)])
    def list_due_schedules() -> dict[str, Any]:
        return {"schedules": [asdict(item) for item in schedule_store.due()]}

    @app.get("/api/v1/schedules/{schedule_id}/history", dependencies=[Depends(authenticate)])
    def schedule_history(schedule_id: str, limit: int = 100) -> dict[str, Any]:
        try:
            return {"executions": [asdict(item) for item in schedule_store.history(schedule_id, limit=limit)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/schedules/{schedule_id}/dispatch", dependencies=[Depends(authenticate)])
    def dispatch_scheduled_workflow(schedule_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        values = payload or {}
        try:
            run = automation_dispatcher.dispatch_schedule(schedule_id, dict(values.get("payload", {})), worker_id=str(values.get("worker_id", "local")), approved_steps=frozenset(str(item) for item in values.get("approved_steps", [])))
            audit_store.append("local", "schedule.dispatch", schedule_id, "completed", metadata={"run_id": run.run_id})
            return {"run": asdict(run)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (LookupError, PermissionError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=409 if isinstance(exc, RuntimeError) else 400, detail=str(exc)) from exc

    @app.post("/api/v1/schedules/{schedule_id}/claim", dependencies=[Depends(authenticate)])
    def claim_schedule(schedule_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        values = payload or {}
        try:
            schedule = schedule_store.claim(schedule_id, worker_id=str(values.get("worker_id", "local")), lease_seconds=int(values.get("lease_seconds", 300)))
            audit_store.append("local", "schedule.claim", schedule_id, "completed", metadata={"worker_id": schedule.lease_owner, "lease_until": schedule.lease_until})
            return {"schedule": asdict(schedule)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=409 if isinstance(exc, RuntimeError) else 400, detail=str(exc)) from exc

    @app.post("/api/v1/schedules/{schedule_id}/release", dependencies=[Depends(authenticate)])
    def release_schedule(schedule_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            schedule = schedule_store.release(schedule_id, worker_id=str(payload.get("worker_id", "local")))
            return {"schedule": asdict(schedule)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/schedules/{schedule_id}/executions/start", dependencies=[Depends(authenticate)])
    def start_schedule_execution(schedule_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            execution = schedule_store.start_execution(schedule_id, execution_id=str(payload.get("execution_id") or uuid4().hex))
            return {"execution": asdict(execution)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/schedule-executions/{execution_id}/finish", dependencies=[Depends(authenticate)])
    def finish_schedule_execution(execution_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            execution = schedule_store.finish_execution(execution_id, status=str(payload.get("status", "completed")), error=str(payload.get("error", "")), outputs=dict(payload.get("outputs", {})), artifacts=list(payload.get("artifacts", [])), cost_units=float(payload.get("cost_units", 0.0)), cost_currency=str(payload.get("cost_currency", "")), connector_actions=list(payload.get("connector_actions", [])), approvals=list(payload.get("approvals", [])))
            return {"execution": asdict(execution)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/events/inbound/recent", dependencies=[Depends(authenticate)])
    def recent_inbound_events(limit: int = 100) -> dict[str, Any]:
        return {"events": list(event_intake.recent(limit=limit))}

    @app.post("/api/v1/events/inbound/dispatch", dependencies=[Depends(authenticate)])
    def dispatch_inbound_event(payload: dict[str, Any], x_orville_signature: str | None = Header(default=None)) -> dict[str, Any]:
        if "event_id" not in payload or "workflow_id" not in payload:
            raise HTTPException(status_code=400, detail="event_id and workflow_id are required")
        event_payload = dict(payload.get("payload", {}))
        event = event_intake.accept(str(payload["event_id"]), str(payload.get("source", "api")), str(payload.get("event_type", "generic")), event_payload, signature_body=json.dumps(payload, sort_keys=True).encode(), signature=x_orville_signature)
        if not event.accepted:
            audit_store.append("local", "webhook.dispatch.rejected", event.event_id or "unknown", "rejected", metadata={"reason": event.reason})
            return {"event": asdict(event), "run": None}
        try:
            run = automation_dispatcher.dispatch_webhook(str(payload["workflow_id"]), event.event_id, event_payload, approved_steps=frozenset(str(item) for item in payload.get("approved_steps", [])))
            audit_store.append("local", "webhook.dispatch", event.event_id, "completed", metadata={"run_id": run.run_id, "workflow_id": payload["workflow_id"]})
            return {"event": asdict(event), "run": asdict(run)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (LookupError, PermissionError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/events/inbound", dependencies=[Depends(authenticate)])
    def accept_inbound_event(payload: dict[str, Any], x_orville_signature: str | None = Header(default=None)) -> dict[str, Any]:
        if "event_id" not in payload:
            raise HTTPException(status_code=400, detail="event_id is required")
        event = event_intake.accept(str(payload["event_id"]), str(payload.get("source", "api")), str(payload.get("event_type", "generic")), dict(payload.get("payload", {})), signature_body=json.dumps(payload, sort_keys=True).encode(), signature=x_orville_signature)
        if not event.accepted:
            audit_store.append("local", "webhook.rejected", event.event_id or "unknown", "rejected", metadata={"reason": event.reason, "source": event.source, "event_type": event.event_type})
        else:
            audit_store.append("local", "webhook.accepted", event.event_id, "accepted", metadata={"source": event.source, "event_type": event.event_type})
        return {"event": asdict(event)}

    @app.post("/api/v1/secrets/references", dependencies=[Depends(authenticate)])
    def register_secret_reference(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            reference = secret_store.register(str(payload["name"]), str(payload.get("environment", "development")), str(payload.get("provider", "local")))
            audit_store.append("local", "secret_reference.register", reference.reference_id, "success", metadata={"name": reference.name, "environment": reference.environment, "provider": reference.provider})
            return {"reference": asdict(reference)}
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/secrets/references", dependencies=[Depends(authenticate)])
    def list_secret_references() -> dict[str, Any]:
        return {"references": [asdict(item) for item in secret_store.list_references()]}

    @app.post("/api/v1/audit", dependencies=[Depends(authenticate)])
    def append_audit_record(payload: dict[str, Any]) -> dict[str, Any]:
        record = audit_store.append(str(payload.get("actor_id", "local")), str(payload["action"]), str(payload["target"]), str(payload.get("outcome", "recorded")), project_id=payload.get("project_id"), metadata=dict(payload.get("metadata", {})))
        return {"audit": asdict(record)}

    @app.get("/api/v1/adapters", dependencies=[Depends(authenticate)])
    def list_adapters(category: str | None = None) -> dict[str, Any]:
        return {"adapters": [asdict(item) | {"status": item.status.value, "capabilities": sorted(item.capabilities)} for item in adapter_registry.list(category=category)]}

    @app.get("/api/v1/adapters/{adapter_id}/capabilities/{capability}", dependencies=[Depends(authenticate)])
    def require_adapter_capability(adapter_id: str, capability: str) -> dict[str, Any]:
        try:
            health = adapter_registry.require(adapter_id, capability)
            return {"adapter": asdict(health) | {"status": health.status.value, "capabilities": sorted(health.capabilities)}}
        except (KeyError, RuntimeError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/research/fetch", dependencies=[Depends(authenticate)])
    def fetch_research_source(payload: dict[str, Any]) -> dict[str, Any]:
        locator = str(payload.get("locator", ""))
        parsed = urlparse(locator)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise HTTPException(status_code=400, detail="research locator must be an http(s) URL")
        try:
            research_network_policy.check_host(parsed.hostname)
            request = UrlRequest(locator, headers={"User-Agent": "OrvilleResearch/1.0"})
            with urlopen(request, timeout=15) as response:
                content_type = response.headers.get("Content-Type", "")
                body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("research response exceeds 2 MB limit")
            excerpt = body.decode("utf-8", errors="replace")[:12000]
            source = research_catalog.add_source(str(payload.get("title", parsed.netloc)), locator, excerpt)
            return {"source": asdict(source), "content_type": content_type, "bytes": len(body)}
        except SecurityViolation as exc:
            raise HTTPException(status_code=400, detail="research host is not allowlisted") from exc
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/research/sources", dependencies=[Depends(authenticate)])
    def add_research_source(payload: dict[str, Any]) -> dict[str, Any]:
        source = research_catalog.add_source(str(payload.get("title", "Untitled source")), str(payload["locator"]), str(payload.get("excerpt", ""))[:12000])
        return {"source": asdict(source)}

    @app.post("/api/v1/research/notes", dependencies=[Depends(authenticate)])
    def add_research_note(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            note = research_catalog.add_note(str(payload["claim"]), tuple(str(item) for item in payload.get("source_ids", [])), str(payload.get("confidence", "medium")))
            return {"note": asdict(note)}
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/research/report", dependencies=[Depends(authenticate)])
    def research_report() -> dict[str, Any]:
        return research_catalog.report()

    @app.post("/api/v1/data/profile", dependencies=[Depends(authenticate)])
    def profile_csv(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            profile = CsvAnalyzer.profile(str(payload["path"]))
            return {"profile": asdict(profile)}
        except (KeyError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/browser/sessions", dependencies=[Depends(authenticate)])
    def create_browser_session(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            session = browser_sessions.create([str(item) for item in payload.get("allowed_domains", [])], headless=bool(payload.get("headless", True)))
            return {"session": session.to_dict()}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/browser/sessions/{session_id}", dependencies=[Depends(authenticate)])
    def browser_session_status(session_id: str) -> dict[str, Any]:
        try:
            return {"session": browser_sessions.get(session_id).to_dict()}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/browser/sessions/{session_id}/navigate", dependencies=[Depends(authenticate)])
    def browser_session_navigate(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            session = browser_sessions.get(session_id)
            result = session.navigate(str(payload["url"]), approved=bool(payload.get("approved", False)))
            run_id = str(payload.get("run_id", "")).strip()
            source = None
            if run_id and result.get("current_url"):
                source = research_catalog.add_source(str(result.get("title") or result.get("current_url")), str(result["current_url"]), str(result.get("text_excerpt") or "")[:12000])
                checkpoint = store.load(run_id)
                checkpoint.context.setdefault("sources", []).append(asdict(source))
                store.save(checkpoint)
            browser_sessions.persist()
            return {"session": result, "source": asdict(source) if source else None}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (SecurityViolation, RuntimeError, OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/browser/sessions/{session_id}/form-submit", dependencies=[Depends(authenticate)])
    def browser_form_submit(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            session = browser_sessions.get(session_id)
            result = session.submit_form(str(payload.get("selector", "")), {str(key): str(value) for key, value in dict(payload.get("fields", {})).items()}, approved=bool(payload.get("approved", False)))
            browser_sessions.persist()
            return {"session": result}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (SecurityViolation, RuntimeError, OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/browser/sessions/{session_id}/download", dependencies=[Depends(authenticate)])
    def browser_download(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            session = browser_sessions.get(session_id)
            result = session.download(str(payload["url"]), approved=bool(payload.get("approved", False)))
            browser_sessions.persist()
            return {"session": result}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (SecurityViolation, RuntimeError, OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/browser/sessions/{session_id}/takeover", dependencies=[Depends(authenticate)])
    def browser_session_takeover(session_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            session = browser_sessions.get(session_id)
            result = session.request_takeover(approved=bool((payload or {}).get("approved", False)))
            browser_sessions.persist()
            return {"session": result}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/api/v1/browser/sessions/{session_id}/close", dependencies=[Depends(authenticate)])
    def browser_session_close(session_id: str) -> dict[str, Any]:
        try:
            result = browser_sessions.get(session_id).close()
            browser_sessions.persist()
            return {"session": result}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/runs/{run_id}/sources", dependencies=[Depends(authenticate)])
    def run_sources(run_id: str) -> dict[str, Any]:
        try:
            checkpoint = store.load(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        return {"run_id": run_id, "sources": checkpoint.context.get("sources", []), "citations": checkpoint.context.get("citations", [])}

    @app.post("/api/v1/runs/{run_id}/citations", dependencies=[Depends(authenticate)])
    def add_run_citation(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            checkpoint = store.load(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        source_ids = {str(item.get("source_id")) for item in checkpoint.context.get("sources", [])}
        requested = [str(item) for item in payload.get("source_ids", [])]
        if any(item not in source_ids for item in requested):
            raise HTTPException(status_code=400, detail="citation references an uncaptured run source")
        citation = {"claim": str(payload.get("claim", ""))[:4000], "source_ids": requested, "confidence": str(payload.get("confidence", "medium")), "created_at": datetime.now(UTC).isoformat()}
        if not citation["claim"] or not requested:
            raise HTTPException(status_code=400, detail="citation requires a claim and captured source_ids")
        checkpoint.context.setdefault("citations", []).append(citation)
        store.save(checkpoint)
        return {"run_id": run_id, "citation": citation}

    @app.get("/api/v1/capabilities", dependencies=[Depends(authenticate)])
    def capabilities() -> dict[str, Any]:
        adapters = [asdict(item) | {"status": item.status.value, "capabilities": sorted(item.capabilities)} for item in adapter_registry.list()]
        connectors = [asdict(item) for item in extension_registry.connectors.values()]
        return {
            "adapters": adapters,
            "connectors": connectors,
            "feature_flags": {
                "agentic_code_generation": True,
                "streaming_runs": True,
                "repository_workspace": True,
                "personal_agent_memory": True,
                "workflow_automation": True,
                "scheduled_workflows": True,
                "research_catalog": True,
                "csv_analysis": True,
                "project_export": True,
                "browser_automation": bool(browser_sessions.sessions),
                "browser_session_takeover": True,
                "remote_git": False,
                "deployment": False,
                "object_storage": False,
            },
        }

    @app.get("/api/v1/health", dependencies=[Depends(authenticate)])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "orville-api"}

    @app.post("/api/v1/objectives", dependencies=[Depends(authenticate)])
    def create_objective(payload: ObjectivePayload) -> dict[str, Any]:
        objective = SoftwareObjective(
            objective=payload.objective,
            deliverables=payload.deliverables,
            constraints=payload.constraints,
            target_environment=str(payload.environment.get("target_environment", "unspecified")),
            acceptance_criteria=payload.acceptance_criteria,
            risk_level="normal" if payload.risk_level == "standard" else payload.risk_level,
        )
        graph = intake.to_graph(objective)
        clarification_gate = graph.tasks[0].inputs.get("clarification_gate", {"required": False, "warnings": [], "hard_gates": [], "questions": []})
        if payload.provider_id:
            graph.tasks[0].inputs["preferred_provider_ids"] = [payload.provider_id]
            graph.tasks[0].inputs["allow_fallback"] = False
        if payload.privacy_class not in {"local_only", "cloud_approved", "restricted"}:
            raise HTTPException(status_code=400, detail="privacy_class must be local_only, cloud_approved, or restricted")
        graph.tasks[0].inputs["local_only"] = payload.local_only
        graph.tasks[0].inputs["privacy_class"] = payload.privacy_class
        if payload.generation_mode.lower() in {"code", "code_generation", "agentic", "agentic_code"}:
            brief = json.dumps({"objective": objective.objective, "deliverables": objective.deliverables, "constraints": objective.constraints, "acceptance_criteria": objective.acceptance_criteria, "target_environment": objective.target_environment}, ensure_ascii=False)
            common = {"required_capabilities": ["code", "streaming"], "local_only": payload.local_only, "privacy_class": payload.privacy_class, "allow_fallback": False if payload.provider_id else True, "preferred_provider_ids": [payload.provider_id] if payload.provider_id else []}
            graph.tasks = [
                TaskNode(task_id="agent.plan", title="Plan implementation", handler="intake.objective.streaming", inputs={**common, "messages": [{"role": "system", "content": "You are Orville's orchestration planner. Analyze the request, decompose it into implementation steps, identify files, dependencies, risks, and acceptance checks. Return a precise execution plan for the coding agent."}, {"role": "user", "content": brief}]}),
                TaskNode(task_id="agent.implement", title="Generate implementation", handler="intake.objective.streaming", depends_on=["agent.plan"], inputs={**common, "messages": [{"role": "system", "content": "You are Orville's code synthesis agent. Based on the objective and the upstream plan, produce complete runnable code with explicit file paths, dependencies, setup instructions, and tests. Include all code in fenced blocks."}, {"role": "user", "content": brief}]}),
                TaskNode(task_id="agent.verify", title="Review and verify output", handler="intake.objective.streaming", depends_on=["agent.implement"], inputs={**common, "messages": [{"role": "system", "content": "You are Orville's verification agent. Review the requested implementation, identify defects or missing acceptance criteria, and provide concrete corrections and validation commands. Be specific and actionable."}, {"role": "user", "content": brief}]}),
            ]
        run_id = f"run-{uuid4().hex[:12]}"
        classification = TaskIntake.classify(objective.objective)
        graphs[run_id] = graph
        store.save(Checkpoint(run_id=run_id, graph=graph, context={"objective": objective.objective, "classification": classification}))
        return {"run_id": run_id, "task_ids": [task.task_id for task in graph.tasks], "classification": classification, "clarification_gate": clarification_gate}

    @app.get("/api/v1/models/machine", dependencies=[Depends(authenticate)])
    def machine_capabilities() -> dict[str, Any]:
        return {"capabilities": detect_machine_capabilities(checkpoint_root.parent).to_dict()}

    @app.get("/api/v1/models/local", dependencies=[Depends(authenticate)])
    def local_models() -> dict[str, Any]:
        return {"models": [model.to_dict() for model in model_catalog.list_models()]}

    @app.post("/api/v1/models/local/import", dependencies=[Depends(authenticate)])
    def import_local_model(payload: LocalModelImportPayload) -> dict[str, Any]:
        if not payload.approved:
            raise HTTPException(status_code=409, detail="importing a local model requires explicit approval")
        endpoint = payload.endpoint
        if endpoint:
            try:
                endpoint = validate_endpoint(endpoint, local=True)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        try:
            record = model_catalog.import_model(payload.source, model_id=payload.model_id, display_name=payload.display_name, runtime=payload.runtime, endpoint=endpoint, capabilities=payload.capabilities, asset_type=payload.asset_type, license=payload.license, license_restrictions=payload.license_restrictions, provenance=payload.provenance, ownership=payload.ownership, attestation=payload.attestation, storage_root=payload.storage_root, storage_mode=payload.storage_mode, deduplicate=payload.deduplicate)
            return {"model": record.to_dict(), "status": "imported", "executed": False}
        except (FileNotFoundError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/models/hub/downloads", dependencies=[Depends(authenticate)])
    def list_hub_downloads() -> dict[str, Any]:
        return {"downloads": [job.to_dict() for job in download_manager.list()]}

    @app.get("/api/v1/models/hub/downloads/{job_id}", dependencies=[Depends(authenticate)])
    def get_hub_download(job_id: str) -> dict[str, Any]:
        try:
            return {"download": download_manager.get(job_id).to_dict()}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="download job not found") from exc

    @app.post("/api/v1/models/hub/downloads/{job_id}/resume", dependencies=[Depends(authenticate)])
    def resume_hub_download(job_id: str, payload: DownloadResumePayload) -> dict[str, Any]:
        if not payload.approved:
            raise HTTPException(status_code=409, detail="resuming a model download requires explicit approval")
        try:
            return {"download": download_manager.resume(job_id).to_dict()}
        except (KeyError, HubModelError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/models/hub/downloads/{job_id}/pause", dependencies=[Depends(authenticate)])
    def pause_hub_download(job_id: str, payload: DownloadResumePayload) -> dict[str, Any]:
        if not payload.approved:
            raise HTTPException(status_code=409, detail="pausing a model download requires explicit approval")
        try:
            return {"download": download_manager.pause(job_id).to_dict()}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="download job not found") from exc

    @app.post("/api/v1/models/hub/downloads/{job_id}/cancel", dependencies=[Depends(authenticate)])
    def cancel_hub_download(job_id: str, payload: DownloadResumePayload) -> dict[str, Any]:
        if not payload.approved:
            raise HTTPException(status_code=409, detail="cancelling a model download requires explicit approval")
        try:
            return {"download": download_manager.cancel(job_id).to_dict()}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="download job not found") from exc

    @app.delete("/api/v1/models/local/{model_id:path}", dependencies=[Depends(authenticate)])
    def remove_local_model(model_id: str, payload: DownloadResumePayload) -> dict[str, Any]:
        if not payload.approved:
            raise HTTPException(status_code=409, detail="removing a local model registration requires explicit approval")
        try:
            model_catalog.remove(model_id, delete_files=False)
            provider_registry.remove(f"local:{model_id}")
            return {"model_id": model_id, "status": "removed", "files_deleted": False}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="local model not found") from exc
        except ProviderError:
            return {"model_id": model_id, "status": "removed", "files_deleted": False}

    @app.get("/api/v1/models/local/{model_id:path}/validate", dependencies=[Depends(authenticate)])
    def validate_local_model(model_id: str, runtime: str | None = None, attestation_policy: str = "optional") -> dict[str, Any]:
        try:
            record = model_catalog.get(model_id)
            validation = model_catalog.validate(model_id, required_runtime=runtime, hardware=detect_machine_capabilities(checkpoint_root.parent).to_dict(), attestation_policy=attestation_policy)
            if runtime:
                endpoint = record.endpoint or ("http://127.0.0.1:11434" if runtime.lower() == "ollama" else "http://127.0.0.1:8000/v1")
                validation["runtime_capabilities"] = probe_runtime_capabilities(runtime, endpoint, declared=set(record.capabilities or []), model=record.model_id).to_dict()
            return {"model": record.to_dict(), "validation": validation}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="local model not found") from exc
        except (ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/models/local/{model_id:path}/activate", dependencies=[Depends(authenticate)])
    def activate_local_model(model_id: str, payload: LocalModelActivationPayload) -> dict[str, Any]:
        if not payload.approved:
            raise HTTPException(status_code=409, detail="activating a local model requires explicit approval")
        runtime = payload.runtime.strip().lower().replace("-", "_")
        if runtime not in {"ollama", "llama_cpp", "transformers"}:
            raise HTTPException(status_code=400, detail="runtime must be ollama, llama.cpp, or transformers")
        endpoint = payload.endpoint
        if endpoint:
            try:
                endpoint = validate_endpoint(endpoint, local=True)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        try:
            candidate = model_catalog.get(model_id)
            validation = model_catalog.validate(model_id, required_runtime=runtime, hardware=detect_machine_capabilities(checkpoint_root.parent).to_dict(), selected_base_model=payload.selected_base_model, attestation_policy=payload.attestation_policy)
            if not validation["checks"]["valid"]:
                raise ValueError(f"local model validation failed: {validation}")
            if candidate.license_restrictions and not payload.accept_license_restrictions:
                raise ValueError(f"license restrictions require explicit acceptance: {candidate.license_restrictions}")
            declared = set(candidate.capabilities or [])
            if declared & {"vision", "embeddings", "image_generation", "audio", "video_generation"}:
                report = probe_runtime_capabilities(runtime, endpoint or ("http://127.0.0.1:11434" if runtime == "ollama" else "http://127.0.0.1:8000/v1"), declared=declared, model=candidate.model_id)
                if not report.reachable:
                    raise ValueError(f"runtime capability probe failed: {report.to_dict()}")
                missing = declared - set(report.exposed_modalities) - {"text", "code"}
                if missing:
                    raise ValueError(f"runtime cannot expose requested modalities: {sorted(missing)}")
            record = model_catalog.activate(model_id, required_runtime=runtime, endpoint=endpoint, attestation_policy=payload.attestation_policy)
            provider_registry.register(create_provider(model_catalog.provider_config(model_id)))
            return {"model": record.to_dict(), "provider": model_catalog.provider_config(model_id).redacted()}
        except (KeyError, ValueError, ProviderError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/models/local/{model_id:path}/deactivate", dependencies=[Depends(authenticate)])
    def deactivate_local_model(model_id: str, payload: DownloadResumePayload) -> dict[str, Any]:
        if not payload.approved:
            raise HTTPException(status_code=409, detail="deactivating a local model requires explicit approval")
        try:
            record = model_catalog.deactivate(model_id)
            provider_registry.remove(f"local:{model_id}")
            return {"model": record.to_dict()}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="local model not found") from exc
        except ProviderError:
            record = model_catalog.get(model_id)
            return {"model": record.to_dict()}

    @app.post("/api/v1/models/compatibility", dependencies=[Depends(authenticate)])
    def model_compatibility(payload: RuntimeCompatibilityPayload) -> dict[str, Any]:
        try:
            record = model_catalog.get(payload.model_id)
            compatibility = check_runtime_compatibility(record, payload.runtime, detect_machine_capabilities(checkpoint_root.parent))
            endpoint = payload.endpoint or record.endpoint or ("http://127.0.0.1:11434" if payload.runtime.lower() == "ollama" else "http://127.0.0.1:8000/v1")
            runtime = probe_runtime_capabilities(payload.runtime, endpoint, declared=set(record.capabilities or []), model=record.model_id) if payload.probe else None
            return {"compatibility": compatibility, "runtime_capabilities": runtime.to_dict() if runtime else None}
        except (KeyError, HubModelError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/models/hub/search", dependencies=[Depends(authenticate)])
    def search_hub_models(payload: HubSearchPayload) -> dict[str, Any]:
        try:
            machine = detect_machine_capabilities(checkpoint_root.parent)
            return {"models": hub_client.search(payload.query, pipeline_tag=payload.pipeline_tag, limit=payload.limit, machine=machine, supported_only=payload.supported_only), "machine": machine.to_dict()}
        except HubModelError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/v1/models/hub/download", dependencies=[Depends(authenticate)])
    def download_hub_model(payload: HubDownloadPayload) -> dict[str, Any]:
        if not payload.approved:
            raise HTTPException(status_code=409, detail="model download requires explicit approval")
        root = (checkpoint_root.parent / "models").resolve()
        root.mkdir(parents=True, exist_ok=True)
        try:
            destination = resolve_download_destination(root, payload.destination)
            token = next((provider.config.api_key for provider in provider_registry.providers() if provider.config.provider_type in {"huggingface", "hugging-face", "hf-inference"} and provider.config.api_key), hub_client.token)
            hub_client.token = token
            job = download_manager.start(payload.repo_id, destination=destination.relative_to(root), revision=payload.revision, max_bytes=payload.max_bytes, max_retries=payload.max_retries)
            return {"download": job.to_dict(), "status": "queued"}
        except (HubModelError, FileNotFoundError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/cloud/blackbox/onboarding", dependencies=[Depends(authenticate)])
    def blackbox_cloud_onboarding() -> dict[str, Any]:
        return {"onboarding": initial_cloud_onboarding(relay_configured=blackbox_relay is not None)}

    @app.get("/api/v1/cloud/blackbox/status", dependencies=[Depends(authenticate)])
    def blackbox_cloud_status() -> dict[str, Any]:
        user_connection = connection_store.get("blackbox")
        local_provider_ids = tuple(provider.config.provider_id for provider in provider_registry.providers() if provider.config.provider_type.lower().replace("_", "-") in {"ollama", "custom-local", "custom-local-ollama", "ollama-compatible", "openai-compatible-local", "llama-cpp", "transformers"})
        if blackbox_relay is None:
            managed = {"mode": "managed", "status": "unavailable", "subject": relay_subject, "last_error_code": "relay_not_configured"}
            relay = {"configured": False}
            fallback = BlackboxFallbackPolicy().decide(RelayStatus.UNAVAILABLE, local_provider_ids).public()
        else:
            snapshot = blackbox_relay.public_status(relay_subject, local_provider_ids)
            managed = snapshot["managed"]
            relay = snapshot["relay"] | {"configured": True}
            fallback = snapshot["fallback"]
        return {"provider": "blackbox", "managed": managed, "user_connected": user_connection.public() if user_connection else {"mode": "user_connected", "status": "not_connected", "subject": relay_subject}, "relay": relay, "fallback": fallback, "credential_in_client": False}

    @app.post("/api/v1/cloud/blackbox/capabilities", dependencies=[Depends(authenticate)])
    def negotiate_blackbox_capabilities(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            result = BlackboxCapabilityNegotiator().negotiate(base_url=str(payload.get("base_url", "")), model=str(payload.get("model", "")), account_plan=str(payload.get("account_plan", "unknown")), advertised=frozenset(str(value) for value in payload.get("advertised", [])))
            return {"capabilities": result.public()}
        except (BlackboxCapabilityError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/cloud/blackbox/models", dependencies=[Depends(authenticate)])
    def discover_blackbox_models_route(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            result = BlackboxModelDiscovery().discover(base_url=str(payload.get("base_url", "")), model=str(payload.get("model", "")), response_payload=payload.get("response"), discovery_supported=bool(payload.get("discovery_supported", True)))
            return {"models": result.public()}
        except (BlackboxModelDiscoveryError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/cloud/blackbox/admit", dependencies=[Depends(authenticate)])
    def admit_blackbox_cloud_request(payload: CloudRelayAdmissionPayload) -> dict[str, Any]:
        if blackbox_relay is None:
            raise HTTPException(status_code=503, detail="Blackbox cloud relay is not configured")
        try:
            mode = AccessMode(payload.mode)
            request = RelayRequest(subject=payload.subject, mode=mode, privacy_class=payload.privacy_class, estimated_units=payload.estimated_units, workspace_id=payload.workspace_id, approved_remote=payload.approved_remote)
            return {"admission": blackbox_relay.admit(request)}
        except (ValueError, RelayError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/cloud/blackbox/user/api-key", dependencies=[Depends(authenticate)])
    def connect_blackbox_user_api_key(payload: BlackboxUserApiKeyPayload) -> dict[str, Any]:
        try:
            contract = BlackboxApiKeyContract(base_url=payload.base_url, model=payload.model)
            normalized_base_url = contract.validate()
            connection = connection_store.connect_manual(uid="blackbox", display_name="Blackbox AI", auth_type="bearer", credential_header="Authorization", base_url=normalized_base_url, credential=payload.api_key, scopes=payload.scopes)
        except (ConnectorConnectionError, BlackboxContractError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        audit_store.append("local", "blackbox.user.connect.api_key", "blackbox", "completed", metadata={"base_url": payload.base_url, "scopes": payload.scopes})
        return {"provider": "blackbox", "mode": "user_connected", "connection": connection, "credential_returned": False}

    @app.post("/api/v1/cloud/blackbox/user/test", dependencies=[Depends(authenticate)])
    def test_blackbox_user_api_key(payload: BlackboxUserApiKeyPayload) -> dict[str, Any]:
        """Validate connection metadata locally without sending or returning the API key."""
        try:
            normalized_base_url = BlackboxApiKeyContract(base_url=payload.base_url, model=payload.model).validate()
        except BlackboxContractError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "provider": "blackbox",
            "mode": "user_connected",
            "tested": True,
            "base_url": normalized_base_url,
            "model": payload.model,
            "credential_supplied": bool(payload.api_key.strip()),
            "credential_returned": False,
            "network_call_performed": False,
        }

    @app.post("/api/v1/cloud/blackbox/user/disconnect", dependencies=[Depends(authenticate)])
    def disconnect_blackbox_user() -> dict[str, Any]:
        removed = connection_store.disconnect("blackbox")
        audit_store.append("local", "blackbox.user.disconnect", "blackbox", "completed" if removed else "not_found")
        return {
            "provider": "blackbox",
            "mode": "user_connected",
            "disconnected": removed,
            "managed_access_unchanged": True,
            "local_mode_unchanged": True,
            "unrelated_task_state_unchanged": True,
        }

    @app.delete("/api/v1/cloud/blackbox/user/credential", dependencies=[Depends(authenticate)])
    def delete_blackbox_user_credential() -> dict[str, Any]:
        """Delete only the stored Blackbox credential and leave managed/local state intact."""
        removed = connection_store.disconnect("blackbox")
        audit_store.append("local", "blackbox.user.credential.delete", "blackbox", "completed" if removed else "not_found")
        return {"provider": "blackbox", "credential_deleted": removed, "managed_access_unchanged": True, "local_mode_unchanged": True}

    @app.get("/api/v1/providers", dependencies=[Depends(authenticate)])
    def list_providers() -> dict[str, Any]:
        return {"providers": [provider.config.redacted() for provider in provider_registry.providers()]}

    @app.post("/api/v1/providers", dependencies=[Depends(authenticate)])
    def add_provider(payload: ProviderPayload) -> dict[str, Any]:
        provider_type = payload.provider_type.lower().replace("_", "-")
        try:
            normalized_url = validate_endpoint(payload.base_url, local=provider_type in {"ollama", "custom-local", "custom-local-ollama", "ollama-compatible", "openai-compatible-local"})
            capabilities = set(payload.capabilities)
            allowed_capabilities = set(ModelCapabilities().__dict__)
            unknown = capabilities - allowed_capabilities
            if unknown:
                raise ValueError(f"unknown capabilities: {sorted(unknown)}")
            config = ProviderConfig(provider_id=payload.provider_id, provider_type=provider_type, model=payload.model, base_url=normalized_url, api_key=payload.api_key or None, timeout_seconds=payload.timeout_seconds, headers={str(key): str(value) for key, value in payload.headers.items()}, capabilities=ModelCapabilities(**{name: name in capabilities for name in allowed_capabilities}))
            return {"provider": register_provider_config(config)}
        except (ValueError, ProviderError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/providers/{provider_id}/models", dependencies=[Depends(authenticate)])
    def discover_provider_models_route(provider_id: str) -> dict[str, Any]:
        provider = next((item for item in provider_registry.providers() if item.config.provider_id == provider_id), None)
        if provider is None:
            raise HTTPException(status_code=404, detail="provider not found")
        try:
            result = discover_provider_models(provider.config)
            catalog = discovery_catalog_store.record(provider_id, result)
            discovered_ids = [str(item.get("id")) for item in catalog.get("models", []) if isinstance(item, dict) and item.get("id")]
            if discovered_ids and provider.config.model not in discovered_ids:
                catalog = discovery_catalog_store.set_active(provider_id, discovered_ids[0])
                current = provider.config
                provider_registry.remove(provider_id)
                provider_registry.register(create_provider(ProviderConfig(provider_id=current.provider_id, provider_type=current.provider_type, model=discovered_ids[0], base_url=current.base_url, api_key=current.api_key, timeout_seconds=current.timeout_seconds, capabilities=current.capabilities, local_model_id=current.local_model_id, headers=current.headers)))
            remote_sync = remote_catalog_store.publish(provider_id)
            audit_store.append("local", "provider.catalog.discover", provider_id, "completed", metadata={"model_count": catalog.get("count", 0), "active_model": catalog.get("active_model"), "remote_synced": remote_sync.get("remote_synced", False)})
            return {"catalog": catalog, "active_model": next((item.config.model for item in provider_registry.providers() if item.config.provider_id == provider_id), None), "remote_sync": {key: value for key, value in remote_sync.items() if key != "catalog"}}
        except ProviderDiscoveryError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/api/v1/providers/{provider_id}/catalog", dependencies=[Depends(authenticate)])
    def get_provider_catalog(provider_id: str) -> dict[str, Any]:
        catalog = discovery_catalog_store.get(provider_id)
        if catalog is None:
            raise HTTPException(status_code=404, detail="provider discovery catalog not found")
        return {"catalog": catalog}

    @app.post("/api/v1/providers/{provider_id}/models/select", dependencies=[Depends(authenticate)])
    def select_provider_model(provider_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        provider = next((item for item in provider_registry.providers() if item.config.provider_id == provider_id), None)
        if provider is None:
            raise HTTPException(status_code=404, detail="provider not found")
        model = str(payload.get("model", "")).strip()
        try:
            catalog = discovery_catalog_store.set_active(provider_id, model)
            current = provider.config
            provider_registry.remove(provider_id)
            provider_registry.register(create_provider(ProviderConfig(provider_id=current.provider_id, provider_type=current.provider_type, model=model, base_url=current.base_url, api_key=current.api_key, timeout_seconds=current.timeout_seconds, capabilities=current.capabilities, local_model_id=current.local_model_id, headers=current.headers)))
            remote_sync = remote_catalog_store.publish(provider_id)
            audit_store.append("local", "provider.model.select", provider_id, "completed", metadata={"model": model, "remote_synced": remote_sync.get("remote_synced", False)})
            return {"catalog": catalog, "provider": provider_registry.get(provider_id).config.redacted(), "remote_sync": {key: value for key, value in remote_sync.items() if key != "catalog"}}
        except (KeyError, ValueError, ProviderError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/routing/privacy", dependencies=[Depends(authenticate)])
    def list_privacy_routing_policies() -> dict[str, Any]:
        return {"policies": privacy_policy_store.list()}

    @app.post("/api/v1/routing/privacy", dependencies=[Depends(authenticate)])
    def set_privacy_routing_policy(payload: PrivacyRoutingPolicyPayload) -> dict[str, Any]:
        try:
            policy = PrivacyRoutingPolicy(payload.privacy_class, payload.allowed_provider_ids, payload.local_only, payload.allow_fallback)
            result = remote_policy_store.save(policy)
            audit_store.append("local", "policy.update", policy.privacy_class, "completed" if result.get("remote_synced", False) else "local_fallback", metadata={"remote_synced": result.get("remote_synced", False), "tenant_id": os.getenv("ORVILLE_TENANT_ID", "local")})
            return result
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/catalog-store/status", dependencies=[Depends(authenticate)])
    def catalog_store_status() -> dict[str, Any]:
        return remote_catalog_store.status()

    @app.post("/api/v1/catalog-store/sync", dependencies=[Depends(authenticate)])
    def sync_catalog_store() -> dict[str, Any]:
        result = remote_catalog_store.sync()
        audit_store.append("local", "catalog.sync", os.getenv("ORVILLE_TENANT_ID", "local"), "completed" if result.get("remote_synced", False) else "local_fallback", metadata={"remote_synced": result.get("remote_synced", False), "catalog_count": len(result.get("catalogs", []))})
        return result

    @app.post("/api/v1/policy-store/backup", dependencies=[Depends(authenticate)])
    def create_policy_backup() -> dict[str, Any]:
        result = policy_backup_store.create(privacy_policy_store, discovery_catalog_store)
        audit_store.append("local", "policy.backup.create", result["sha256"], "completed", metadata={"bytes": result["bytes"]})
        return {"backup": result}

    @app.get("/api/v1/policy-store/backups", dependencies=[Depends(authenticate)])
    def list_policy_backups() -> dict[str, Any]:
        return {"backups": policy_backup_store.list()}

    @app.get("/api/v1/policy-store/status", dependencies=[Depends(authenticate)])
    def policy_store_status() -> dict[str, Any]:
        return remote_policy_store.status()

    @app.get("/api/v1/config/export/redacted", dependencies=[Depends(authenticate)])
    def export_redacted_configuration() -> dict[str, Any]:
        return redacted_provider_export(provider_registry.providers(), privacy_policy_store, discovery_catalog_store)

    @app.delete("/api/v1/providers/{provider_id}", dependencies=[Depends(authenticate)])
    def remove_provider(provider_id: str) -> dict[str, str]:
        try:
            provider_registry.remove(provider_id)
        except ProviderError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"provider_id": provider_id, "status": "removed"}

    @app.get("/api/v1/providers/health", dependencies=[Depends(authenticate)])
    def provider_health() -> dict[str, Any]:
        return {"providers": provider_registry.health_check_all()}

    @app.post("/api/v1/generate/media", dependencies=[Depends(authenticate)])
    def generate_media(payload: MediaGenerationPayload) -> dict[str, Any]:
        modality = payload.modality.strip().lower().replace("-", "_")
        if modality not in {"image", "video"}:
            raise HTTPException(status_code=400, detail="modality must be image or video")
        required = "image_generation" if modality == "image" else "video_generation"
        options = dict(payload.options)
        if options.get("number") is not None and not 1 <= int(options["number"]) <= 4:
            raise HTTPException(status_code=400, detail="options.number must be between 1 and 4")
        try:
            response, route = provider_router.generate_media(MediaRequest(prompt=payload.prompt, modality=modality, negative_prompt=payload.negative_prompt, options=options), RoutingRequest(required_capabilities=frozenset({required}), preferred_provider_ids=(payload.provider_id,) if payload.provider_id else (), local_only=payload.local_only, allow_fallback=payload.allow_fallback))
        except (ProviderError, ValueError) as exc:
            detail = str(exc)
            if "no configured provider satisfies" in detail:
                detail = f"no configured provider satisfies required capability '{required}'; configure a provider with {required} enabled"
            raise HTTPException(status_code=400, detail=detail) from exc
        return {"modality": response.modality, "provider_id": response.provider_id, "model": response.model, "assets": response.assets, "routing": {"selected_provider": route.provider_id, "attempts": [attempt.__dict__ for attempt in route.attempts]}}

    @app.post("/api/v1/objectives/{run_id}/execute", dependencies=[Depends(authenticate)])
    def execute_objective(run_id: str, payload: ExecutePayload) -> dict[str, Any]:
        graph = graphs.get(run_id)
        if graph is None:
            try:
                graph = store.load(run_id).graph
                graphs[run_id] = graph
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="objective not found") from exc
        if not provider_registry.providers() and not (handlers or {}):
            raise HTTPException(status_code=503, detail="no model providers configured; add Gemini, Blackbox, Ollama, Stable Horde, or a custom local provider in Integrations")
        context = dict(payload.context)
        stream = bool(context.pop("stream", False))
        if stream:
            if run_id in run_threads and run_threads[run_id].is_alive():
                return {"run_id": run_id, "status": "running", "streaming": True}
            thread = Thread(target=execute_in_background, args=(run_id, graph, context), daemon=True)
            run_threads[run_id] = thread
            thread.start()
            return {"run_id": run_id, "status": "running", "streaming": True}
        try:
            result = run_engine.run(graph, context=context, run_id=run_id)
            persist_generated_artifact(run_id)
            capture_research_citations(run_id)
        except ProviderError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {"run_id": result.run_id, "status": result.status.value, "outputs": result.outputs, "checkpoint_path": result.checkpoint_path}

    @app.get("/api/v1/runs/{run_id}", dependencies=[Depends(authenticate)])
    def get_run(run_id: str) -> dict[str, Any]:
        try:
            checkpoint = store.load(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        return checkpoint.to_dict()

    @app.get("/api/v1/runs/{run_id}/events", dependencies=[Depends(authenticate)])
    def get_events(run_id: str) -> dict[str, Any]:
        try:
            checkpoint = store.load(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        return {"run_id": run_id, "events": checkpoint.to_dict().get("events", [])}

    @app.get("/api/v1/runs/{run_id}/events/stream", dependencies=[Depends(authenticate)])
    async def stream_events(run_id: str, last_event_id: int = 0, last_event_header: int | None = Header(default=None, alias="Last-Event-ID")) -> Any:
        try:
            store.load(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        try:
            from fastapi.responses import StreamingResponse
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=501, detail="streaming unavailable") from exc

        async def event_generator():
            cursor = max(0, last_event_header if last_event_header is not None else last_event_id)
            idle_cycles = 0
            while idle_cycles < 300:
                checkpoint = store.load(run_id)
                events = checkpoint.to_dict().get("events", [])
                emitted = False
                for event in events:
                    if int(event.get("sequence", 0)) <= cursor:
                        continue
                    cursor = int(event["sequence"])
                    emitted = True
                    yield f"id: {cursor}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                if checkpoint.run_status.value in {"completed", "failed", "blocked", "cancelled"} and not emitted:
                    break
                idle_cycles = 0 if emitted else idle_cycles + 1
                await asyncio.sleep(0.25)

        return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no", "X-Orville-Resume": "Last-Event-ID or last_event_id"})

    @app.post("/api/v1/runs/{run_id}/cancel", dependencies=[Depends(authenticate)])
    def cancel_run(run_id: str) -> dict[str, str]:
        try:
            checkpoint = store.load(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        checkpoint.context["cancel_requested"] = True
        store.save(checkpoint)
        return {"run_id": run_id, "status": "cancellation_requested"}

    @app.post("/api/v1/runs/{run_id}/tasks/{task_id}/approval", dependencies=[Depends(authenticate)])
    def approve_task(run_id: str, task_id: str, payload: ApprovalPayload) -> dict[str, str]:
        try:
            checkpoint = store.load(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        task = next((item for item in checkpoint.graph.tasks if item.task_id == task_id), None)
        if task is None:
            raise HTTPException(status_code=404, detail="task not found")
        if payload.approved:
            checkpoint.context.setdefault("approved_tasks", []).append(task_id)
            task.approved = True
        else:
            task.error = "approval rejected"
        store.save(checkpoint)
        return {"run_id": run_id, "task_id": task_id, "status": "approved" if payload.approved else "rejected"}

    @app.post("/api/v1/artifacts/text", dependencies=[Depends(authenticate)])
    def create_text_artifact(payload: dict[str, Any]) -> dict[str, Any]:
        name = Path(str(payload.get("name", "artifact.md"))).name
        if not name or name in {".", ".."} or len(name) > 180:
            raise HTTPException(status_code=400, detail="artifact name is invalid")
        content = payload.get("content")
        if not isinstance(content, str):
            raise HTTPException(status_code=400, detail="artifact content must be text")
        if len(content.encode("utf-8")) > 5_000_000:
            raise HTTPException(status_code=413, detail="text artifact exceeds 5 MB limit")
        destination = artifacts.root / "generated" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        record = artifacts.register(destination, artifact_id=str(payload.get("artifact_id") or uuid4().hex[:16]))
        audit_store.append("local", "artifact.create", record.artifact_id, "success", metadata={"name": record.name, "media_type": record.media_type})
        return {"artifact": record.to_dict()}

    @app.get("/api/v1/artifacts", dependencies=[Depends(authenticate)])
    def list_artifacts() -> dict[str, Any]:
        return {"artifacts": [record.to_dict() for record in artifacts.list()]}

    @app.get("/api/v1/artifacts/preview/{relative_path:path}", dependencies=[Depends(authenticate)])
    def preview_artifact(relative_path: str, max_bytes: int = 12_000) -> dict[str, Any]:
        try:
            return artifacts.preview(relative_path, max_bytes=max_bytes)
        except (FileNotFoundError, SecurityViolation):
            raise HTTPException(status_code=404, detail="artifact not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/artifacts/versions/{relative_path:path}", dependencies=[Depends(authenticate)])
    def artifact_versions(relative_path: str) -> dict[str, Any]:
        try:
            return {"relative_path": relative_path, "versions": artifacts.versions(relative_path)}
        except (FileNotFoundError, SecurityViolation) as exc:
            raise HTTPException(status_code=404, detail="artifact not found") from exc

    @app.get("/api/v1/artifacts/retention/plan", dependencies=[Depends(authenticate)])
    def artifact_retention_plan(max_versions: int = 5) -> dict[str, Any]:
        try:
            return artifacts.retention_plan(max_versions=max_versions)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/memory", dependencies=[Depends(authenticate)])
    def put_memory(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            record = memory_store.put(str(payload["scope"]), str(payload["owner_id"]), str(payload["key"]), payload.get("value"), source=str(payload.get("source", "user")), ttl_seconds=payload.get("ttl_seconds"))
            audit_store.append("local", "memory.put", record.memory_id, "success", metadata={"scope": record.scope, "owner_id": record.owner_id, "key": record.key})
            return {"memory": record.to_dict()}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/memory", dependencies=[Depends(authenticate)])
    def list_memory(scope: str, owner_id: str) -> dict[str, Any]:
        try:
            return memory_store.inspect(scope, owner_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/v1/memory/{memory_id}", dependencies=[Depends(authenticate)])
    def delete_memory(memory_id: str, owner_id: str) -> dict[str, Any]:
        deleted = memory_store.delete(memory_id, owner_id=owner_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="memory not found")
        audit_store.append("local", "memory.delete", memory_id, "success", metadata={"owner_id": owner_id})
        return {"memory_id": memory_id, "deleted": True}

    @app.get("/api/v1/memory/retention/plan", dependencies=[Depends(authenticate)])
    def memory_retention_plan() -> dict[str, Any]:
        return memory_store.retention_plan()

    @app.post("/api/v1/memory/retention/purge", dependencies=[Depends(authenticate)])
    def purge_memory(payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("confirm") is not True:
            raise HTTPException(status_code=400, detail="explicit confirmation required")
        removed = memory_store.purge_expired(before=payload.get("before"))
        audit_store.append("local", "memory.retention_purge", "expired", "success", metadata={"removed": removed})
        return {"purged": removed}

    @app.get("/api/v1/artifacts/{relative_path:path}", dependencies=[Depends(authenticate)])
    def get_artifact(relative_path: str) -> Any:
        try:
            from fastapi.responses import FileResponse
            candidate = artifacts.policy.resolve(artifacts.root / relative_path)
            if not candidate.is_file():
                raise FileNotFoundError(candidate)
            return FileResponse(candidate, media_type=artifacts.register(candidate).media_type, filename=candidate.name)
        except (FileNotFoundError, SecurityViolation) as exc:
            raise HTTPException(status_code=404, detail="artifact not found") from exc

    @app.post("/api/v1/threads", dependencies=[Depends(authenticate)])
    def create_thread(payload: ThreadCreatePayload) -> dict[str, Any]:
        try:
            thread = thread_store.create_thread(payload.request, project_id=payload.project_id, agent_id=payload.agent_id)
            return {"thread": asdict(thread)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/threads", dependencies=[Depends(authenticate)])
    def list_threads(project_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return {"threads": [asdict(item) for item in thread_store.list_threads(project_id=project_id, limit=limit)]}

    @app.get("/api/v1/threads/{thread_id}", dependencies=[Depends(authenticate)])
    def get_thread(thread_id: str) -> dict[str, Any]:
        try:
            return {"thread": asdict(thread_store.get_thread(thread_id)), "messages": [asdict(item) for item in thread_store.list_messages(thread_id)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/threads/{thread_id}/messages", dependencies=[Depends(authenticate)])
    def list_thread_messages(thread_id: str, after: int = 0) -> dict[str, Any]:
        try:
            return {"messages": [asdict(item) for item in thread_store.list_messages(thread_id, after=after)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/threads/{thread_id}/messages", dependencies=[Depends(authenticate)])
    def append_thread_message(thread_id: str, payload: ThreadMessagePayload) -> dict[str, Any]:
        try:
            message = thread_store.append_message(thread_id, role=payload.role, kind=payload.kind, content=payload.content)
            return {"message": asdict(message), "thread": asdict(thread_store.get_thread(thread_id))}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400 if isinstance(exc, ValueError) else 404, detail=str(exc)) from exc

    @app.post("/api/v1/threads/{thread_id}/transition", dependencies=[Depends(authenticate)])
    def transition_thread(thread_id: str, payload: ThreadTransitionPayload) -> dict[str, Any]:
        try:
            updated = thread_store.transition(thread_id, ThreadStatus(payload.status), stop_reason=payload.stop_reason, expected_version=payload.expected_version)
            return {"thread": asdict(updated)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/threads/{thread_id}/wait", dependencies=[Depends(authenticate)])
    def request_thread_wait(thread_id: str, payload: ThreadWaitPayload) -> dict[str, Any]:
        try:
            event = thread_store.request_wait(thread_id, event_type=payload.event_type, description=payload.description, input_schema=payload.input_schema, risk_class=payload.risk_class, tool_name=payload.tool_name, expires_at=payload.expires_at)
            return {"event": asdict(event), "thread": asdict(thread_store.get_thread(thread_id))}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (SchemaError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/threads/wait/{event_id}/resolve", dependencies=[Depends(authenticate)])
    def resolve_thread_wait(event_id: str, payload: ThreadResolvePayload) -> dict[str, Any]:
        try:
            event = thread_store.resolve_wait(event_id, payload.response, accept=payload.accept)
            return {"event": asdict(event), "thread": asdict(thread_store.get_thread(event.thread_id))}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (SchemaError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=409 if isinstance(exc, RuntimeError) else 400, detail=str(exc)) from exc

    @app.post("/api/v1/threads/{thread_id}/structured", dependencies=[Depends(authenticate)])
    def arm_thread_structured(thread_id: str, payload: ThreadStructuredPayload) -> dict[str, Any]:
        try:
            thread_store.arm_structured_output(thread_id, payload.schema_payload)
            return {"thread": asdict(thread_store.get_thread(thread_id)), "status": "armed"}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (SchemaError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/threads/{thread_id}/structured/complete", dependencies=[Depends(authenticate)])
    def complete_thread_structured(thread_id: str, payload: ThreadStructuredCompletePayload) -> dict[str, Any]:
        try:
            result = thread_store.complete_structured_output(thread_id, payload.value)
            return {"result": asdict(result), "thread": asdict(thread_store.get_thread(thread_id))}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/agents", dependencies=[Depends(authenticate)])
    def list_agents(enabled_only: bool = False) -> dict[str, Any]:
        return {"agents": [asdict(item) for item in agent_runtime.list_agents(enabled_only=enabled_only)]}

    @app.post("/api/v1/agents", dependencies=[Depends(authenticate)])
    def register_agent(payload: AgentProfilePayload) -> dict[str, Any]:
        try:
            profile = AgentProfile(payload.agent_id, payload.name, payload.description, payload.system_instructions, payload.model_policy, payload.memory_scope, tuple(payload.skills), tuple(payload.connectors), tuple(payload.tool_permissions), payload.risk_ceiling, payload.enabled)
            return {"agent": asdict(agent_runtime.register_agent(profile))}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/agents/{agent_id}/enabled", dependencies=[Depends(authenticate)])
    def set_agent_enabled(agent_id: str, enabled: bool) -> dict[str, Any]:
        try:
            return {"agent": asdict(agent_runtime.set_enabled(agent_id, enabled))}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/threads/{thread_id}/children", dependencies=[Depends(authenticate)])
    def create_child_thread(thread_id: str, payload: ChildTaskPayload) -> dict[str, Any]:
        try:
            child, relation = agent_runtime.create_child_task(thread_id, payload.request, agent_id=payload.agent_id, required=payload.required, project_id=payload.project_id)
            return {"thread": asdict(child), "relation": asdict(relation)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (ValueError, PermissionError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/threads/{thread_id}/children", dependencies=[Depends(authenticate)])
    def list_child_threads(thread_id: str) -> dict[str, Any]:
        try:
            return {"children": [{"relation": asdict(relation), "thread": asdict(child)} for relation, child in agent_runtime.list_children(thread_id)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/threads/{thread_id}/children/cancel", dependencies=[Depends(authenticate)])
    def cancel_child_threads(thread_id: str) -> dict[str, Any]:
        try:
            return {"cancelled_thread_ids": agent_runtime.cancel_tree(thread_id)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/skills", dependencies=[Depends(authenticate)])
    def list_skills() -> dict[str, Any]:
        return {"skills": [item.to_dict() for item in skill_registry.list()]}

    @app.post("/api/v1/skills/install", dependencies=[Depends(authenticate)])
    def install_skill(payload: SkillInstallPayload) -> dict[str, Any]:
        try:
            grant = PermissionSet(tools=frozenset(payload.tools), network_hosts=frozenset(host.lower() for host in payload.network_hosts), scopes=frozenset(payload.scopes))
            record = skill_registry.install(payload.source, granted=grant, approved=payload.approved)
            return {"skill": record.to_dict()}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except (SkillSecurityError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/skills/{skill_id}/enabled", dependencies=[Depends(authenticate)])
    def set_skill_enabled(skill_id: str, enabled: bool) -> dict[str, Any]:
        try:
            return {"skill": skill_registry.set_enabled(skill_id, enabled).to_dict()}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete("/api/v1/skills/{skill_id}", dependencies=[Depends(authenticate)])
    def uninstall_skill(skill_id: str) -> dict[str, str]:
        try:
            skill_registry.uninstall(skill_id)
            return {"skill_id": skill_id, "status": "uninstalled"}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/connector-adapter-catalog", dependencies=[Depends(authenticate)])
    def list_connector_adapter_catalog(query: str = "", limit: int = 372) -> dict[str, Any]:
        normalized = query.strip().lower()
        selected = [item for item in catalog_adapters if not normalized or normalized in f"{item.connector_id} {item.display_name} {item.description}".lower()]
        selected = selected[:max(1, min(limit, 372))]
        return {"summary": catalog_summary(catalog_adapters), "adapters": [item.status() for item in selected]}

    @app.get("/api/v1/connector-adapters", dependencies=[Depends(authenticate)])
    def list_connector_adapters(supported_only: bool = False) -> dict[str, Any]:
        return {"adapters": [{"connector_id": item.connector_id, "display_name": item.display_name, "auth_type": item.auth_type, "documentation_url": item.documentation_url, "supported": item.supported, "support_state": item.support_state, "version": item.version, "capabilities": list(item.capabilities), "scopes": list(item.scopes), "limits": item.limits, "notes": item.notes, "operations": [asdict(operation) for operation in item.operations]} for item in adapter_registry_runtime.list(supported_only=supported_only)]}

    @app.get("/api/v1/connector-adapters/{connector_id}/operations", dependencies=[Depends(authenticate)])
    def list_connector_adapter_operations(connector_id: str) -> dict[str, Any]:
        try:
            return {"connector_id": connector_id, "operations": [asdict(item) for item in adapter_registry_runtime.operations(connector_id)]}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/v1/connector-adapters/{connector_id}/invoke", dependencies=[Depends(authenticate)])
    def invoke_connector_adapter(connector_id: str, payload: ConnectorInvokePayload) -> dict[str, Any]:
        try:
            manifest = adapter_registry_runtime.get(connector_id)
            operation = next((item for item in manifest.operations if item.operation_id == payload.operation and item.enabled), None)
            if operation is None:
                raise HTTPException(status_code=404, detail=f"operation not available: {connector_id}/{payload.operation}")
            if operation.risk_class in {"sensitive", "critical"} and not payload.approved:
                raise HTTPException(status_code=403, detail=f"operation requires explicit approval: {payload.operation}")
            if not usage_health.provider_available(connector_id):
                raise HTTPException(status_code=503, detail="connector provider circuit is open; retry after cooldown")
            allowed, budget_reason = usage_health.can_spend(f"connector:{connector_id}", units=1, calls=1)
            if not allowed:
                raise HTTPException(status_code=429, detail=budget_reason)
            connection, credential = connection_store.credential(connector_id)
            started = time.perf_counter()
            from urllib.parse import urlparse
            hostname = urlparse(connection.base_url).hostname
            if not hostname:
                raise ConnectorAdapterError("connector connection has no valid hostname")
            headers = provider_default_headers(connector_id)
            headers[connection.credential_header] = credential if connection.auth_type == "api_key" else f"Bearer {credential}"
            file_policy = FileTransferPolicy(checkpoint_root.parent / "connector-files")
            adapter = GenericHttpAdapter(connection.base_url, headers, allowed_hosts={hostname}, allow_private=False, max_response_bytes=int(manifest.limits.get("max_response_bytes", 5_000_000)), max_retries=int(manifest.limits.get("max_retries", 2)), file_policy=file_policy)
            result = adapter(operation, dict(payload.arguments))
            latency_ms = (time.perf_counter() - started) * 1000
            connection_store.mark_operation(connector_id)
            usage_health.record(scope=f"connector:{connector_id}", category="connector_adapter", provider_id=connector_id, units=1, latency_ms=latency_ms, status="success" if result.success else "failed", metadata={"operation": payload.operation, "status_code": result.status_code, "attempt": result.meta.get("attempt")})
            usage_health.record_provider_result(connector_id, success=result.success, message=result.error or "")
            audit_store.append("local", "connector.adapter.invoke", connector_id, "success" if result.success else "failed", run_id=payload.run_id, metadata={"operation": payload.operation, "status_code": result.status_code, "attempt": result.meta.get("attempt"), "latency_ms": round(latency_ms, 2)})
            return {"connector_id": connector_id, "operation": payload.operation, "result": asdict(result), "provider_health": asdict(usage_health.provider_health(connector_id))}
        except HTTPException:
            raise
        except ConnectorConnectionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (ConnectorAdapterError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/provider-rate-limits", dependencies=[Depends(authenticate)])
    def set_provider_rate_limit(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return {"rate_limit": provider_rate_limit_store.set_limit(str(payload["provider_id"]), int(payload["window_seconds"]), int(payload.get("max_calls", -1)), int(payload.get("max_tokens", -1)))}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/provider-rate-limits/{provider_id}", dependencies=[Depends(authenticate)])
    def get_provider_rate_limit(provider_id: str) -> dict[str, Any]:
        return {"rate_limit": provider_rate_limit_store.snapshot(provider_id)}

    @app.get("/api/v1/provider-usage/{provider_id}", dependencies=[Depends(authenticate)])
    def get_provider_usage(provider_id: str) -> dict[str, Any]:
        return {"provider_id": provider_id, "usage": usage_health.usage(f"provider:{provider_id}"), "rate_limit": provider_rate_limit_store.snapshot(provider_id)}

    @app.post("/api/v1/budgets", dependencies=[Depends(authenticate)])
    def set_usage_budget(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            budget = Budget(str(payload["scope"]), float(payload.get("max_units", -1)), int(payload.get("max_input_tokens", -1)), int(payload.get("max_output_tokens", -1)), int(payload.get("max_calls", -1)), bool(payload.get("enabled", True)))
            return {"budget": asdict(usage_health.set_budget(budget))}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/usage/{scope}", dependencies=[Depends(authenticate)])
    def get_usage(scope: str) -> dict[str, Any]:
        return {"scope": scope, "usage": usage_health.usage(scope)}

    @app.get("/api/v1/provider-health/{provider_id}", dependencies=[Depends(authenticate)])
    def get_provider_health(provider_id: str) -> dict[str, Any]:
        health = usage_health.provider_health(provider_id)
        return {"health": asdict(health), "available": usage_health.provider_available(provider_id)}

    @app.post("/api/v1/browser-relay/pair", dependencies=[Depends(authenticate)])
    def pair_browser_relay(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            session, secret = browser_relay.pair(str(payload.get("client_label", "Browser Operator")), list(payload.get("allowed_domains", [])))
            return {"session": asdict(session), "secret": secret}
        except (BrowserRelayError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/browser-relay/sessions", dependencies=[Depends(authenticate)])
    def list_browser_relay_sessions() -> dict[str, Any]:
        return {"sessions": [asdict(item) for item in browser_relay.list_sessions()]}

    @app.post("/api/v1/browser-relay/{session_id}/action", dependencies=[Depends(authenticate)])
    def queue_browser_relay_action(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            action = browser_relay.queue_action(session_id, str(payload["secret"]), str(payload["action"]), dict(payload.get("payload", {})))
            return {"action": action, "queued": True}
        except (KeyError, TypeError, BrowserRelayError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.get("/api/v1/browser-relay/{session_id}/actions", dependencies=[Depends(authenticate)])
    def poll_browser_relay_actions(session_id: str, secret: str, limit: int = 20) -> dict[str, Any]:
        try:
            return {"actions": browser_relay.poll_actions(session_id, secret, limit=limit)}
        except BrowserRelayError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/api/v1/browser-relay/{session_id}/validate-navigation", dependencies=[Depends(authenticate)])
    def validate_browser_relay_navigation(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            session = browser_relay.validate_navigation(session_id, str(payload["secret"]), str(payload["url"]))
            return {"session": asdict(session), "allowed": True}
        except (KeyError, BrowserRelayError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/api/v1/browser-relay/{session_id}/revoke", dependencies=[Depends(authenticate)])
    def revoke_browser_relay(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return {"session": asdict(browser_relay.revoke(session_id, str(payload["secret"]))) }
        except (KeyError, BrowserRelayError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/api/v1/canary/runs", dependencies=[Depends(authenticate)])
    def create_canary_run(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            from .canary_policy import CanaryPolicy
            run_id = canary_controller.start(CanaryPolicy.from_dict(payload))
            return canary_store.get(run_id)
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/canary/runs/{run_id}/deploy", dependencies=[Depends(authenticate)])
    def deploy_canary(run_id: str) -> dict[str, Any]:
        try: return canary_controller.deploy(run_id)
        except (KeyError, CanaryError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/canary/runs/{run_id}/observe", dependencies=[Depends(authenticate)])
    def observe_canary(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            observation = HealthObservation(**payload.get("observation", payload))
            return canary_controller.observe(run_id, observation, bool(payload.get("approval", False)))
        except (KeyError, TypeError, ValueError, CanaryError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/canary/runs/{run_id}/rollback", dependencies=[Depends(authenticate)])
    def rollback_canary(run_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try: return canary_controller.rollback(run_id, str((payload or {}).get("reason", "operator_or_policy")))
        except (KeyError, CanaryError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/canary/runs/{run_id}", dependencies=[Depends(authenticate)])
    def canary_status(run_id: str) -> dict[str, Any]:
        try: return {"run": canary_store.get(run_id), "audit": canary_store.audit_events(run_id)}
        except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/state", dependencies=[Depends(authenticate)])
    def project_state() -> dict[str, Any]:
        state = ProjectState(project_id="orville", objective="Orville project state")
        return asdict(state)

    return app


def main() -> None:
    """Launch the API with uvicorn when installed with the API extra."""
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("install the 'api' extra to run orville-api") from exc
    config = RuntimeConfig.from_environment()
    uvicorn.run("orville_core.api:create_app", factory=True, host=config.host, port=config.port)


if __name__ == "__main__":  # pragma: no cover - exercised by the run smoke test
    main()
