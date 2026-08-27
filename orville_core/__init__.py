"""Standalone Orville orchestration primitives."""

from .checkpoint import CheckpointStore
from .persistence import SQLiteCheckpointStore
from .circuit_state import SQLiteCircuitStateStore
from .engine import ExecutionResult, OrchestrationEngine
from .local_models import LocalModelCatalog, LocalModelRecord
from .hub_models import HubModelError, HuggingFaceHubClient, MachineCapabilities, detect_machine_capabilities
from .models import Checkpoint, Event, OperationCheckpoint, RunStatus, TaskGraph, TaskNode, TaskStatus
from .routing import ProviderRouter, RoutingAttempt, RoutingRequest, RoutingResult, validate_endpoint
from .integration import model_task_handler, verify_output
from .workflow import AgentDefinition, AgentHandoff, AgentRegistry, ProjectState, SoftwareObjective, TaskIntake, VerificationRecord, classify_sensitive_domains, default_agent_registry, sensitive_domain_safety
from .agent_contracts import AgentHandoffEnvelope, AutomationSpec, CodeSynthesisOutput, ContractError, EmbeddingIndexSpec, IDEInspectionReport, PrototypeSpec, RefactorPlan, ResearchBrief, ResearchFinding, ResearchOutput, SourceEvidence, StreamPolicy, VerificationSpec, WorkloadClassification, classify_workload
from .security import FilesystemPolicy, LeastPrivilegePolicy, NetworkPolicy, SecretRedactor, SecurityViolation, ToolPolicy, require_dry_run
from .supply_chain import SupplyChainReview, review_downloaded_file
from .recovery import RecoveryVerification, build_rollback_plan, verify_recovery_evidence
from .failure_patterns import FailurePattern, review_completed_task_graphs
from .observability import JsonlTraceRecorder, TraceRecord
from .run_observability import RunObservabilityRecord, RunObservabilityRecorder, elapsed_ms
from .sandbox import SandboxError, SandboxExecutor, SandboxPlan, SandboxPolicy, SandboxResult, SandboxUnavailable, UnavailableSandboxExecutor
from .sandbox_adapters import LinuxBubblewrapExecutor, WindowsSandboxExecutor, discover_sandbox_adapters
from .tuf_metadata import TufRepositoryVerifier, TufVerificationError
from .attestations import AttestationError, AttestationPolicy, AttestationRecord, TrustStore, verify_attestation, verify_cosign_attestation
from .attestation_service import ActivationAttestationEvidence, AttestationVerificationService
from .canary_policy import CanaryCohort, CanaryPolicy, CanaryPolicyError, HealthThresholds, RollbackLimits
from .security_release_gate import SecurityGateResult, run_security_gate
from .canary_controller import CanaryState, DurableCanaryController, HealthDecision, HealthEvaluator, HealthWindow
from .worker_protocol import WorkerRequest, WorkerResponse, decode_message, encode_message
from .local_execution import LocalModelExecutionError, LocalModelExecutionService, execute_local_model
from .artifacts import ArtifactRecord, ArtifactStore
from .media_provenance import MediaAsset, MediaHistoryRecord, MediaProvenanceStore, MediaTransformation
from .media_validation import MediaValidationPolicy, MediaValidationResult, validate_media
from .document_verification import DocumentVerificationPolicy, DocumentVerificationResult, verify_document
from .evaluation import EvaluationCheck, EvaluationResult, evaluate_output
from .runtime_health import HealthCheck, RuntimeHealth
from .connector_health import ConnectorHealth, ConnectorHealthError, ConnectorInventory
from .connector_policy import ConnectorAuthPolicy, ConnectorPolicyError
from .endpoint_config import EndpointConfigError, LocalModelSpec, ProviderEndpointSpec
from .local_model_policy import LocalModelExecutionPolicy, LocalModelPolicyError
from .workspace_locks import BranchChange, MergeDecision, WorkspaceLease, WorkspaceLeaseError, WorkspaceLeaseRegistry, reconcile_branch_changes
from .ide_inspector import IDEInspector, inspect_repository
from .endpoint_probe import EndpointProbeResult, probe_endpoint, validate_endpoint_url
from .connector_adapters import ConnectorTransferRequest
from .cloud_relay import BlackboxFallbackPolicy, FallbackDecision
from .blackbox_contract import BlackboxApiKeyContract, BlackboxContractError, validate_blackbox_error_payload
from .blackbox_capabilities import BlackboxCapabilityError, BlackboxCapabilityNegotiator, BlackboxCapabilityResult
from .blackbox_model_discovery import BlackboxModelDiscovery, BlackboxModelDiscoveryError, BlackboxModelDiscoveryResult, discover_blackbox_models
from .cloud_onboarding import initial_cloud_onboarding
from .connector_capability import CapabilityCallResult, ConnectorCapabilityAudit
from .connector_governance import ConnectorGovernanceError, ConnectorMutationPolicy, ConnectorMutationRequest
try:
    from .api import create_app
except RuntimeError:  # optional API dependencies
    create_app = None
from .providers import (
    CustomLocalAdapter,
    GeminiAdapter,
    HuggingFaceAdapter,
    JsonHttpClient,
    EmbeddingResponse,
    LLMRequest,
    MediaRequest,
    MediaResponse,
    LLMResponse,
    ModelCapabilities,
    OllamaAdapter,
    StableHordeAdapter,
    ProviderConfig,
    ProviderError,
    ProviderRegistry,
    StreamChunk,
    create_provider,
)

__all__ = [
    "Checkpoint",
    "OperationCheckpoint",
    "CheckpointStore",
    "SQLiteCheckpointStore",
    "SQLiteCircuitStateStore",
    "Event",
    "ExecutionResult",
    "OrchestrationEngine",
    "LocalModelCatalog",
    "LocalModelRecord",
    "HubModelError",
    "HuggingFaceHubClient",
    "MachineCapabilities",
    "detect_machine_capabilities",
    "CustomLocalAdapter",
    "GeminiAdapter",
    "HuggingFaceAdapter",
    "JsonHttpClient",
    "EmbeddingResponse",
    "LLMRequest",
    "MediaRequest",
    "MediaResponse",
    "LLMResponse",
    "ModelCapabilities",
    "StreamChunk",
    "OllamaAdapter",
    "StableHordeAdapter",
    "ProviderConfig",
    "ProviderError",
    "ProviderRegistry",
    "create_provider",
    "ProviderRouter",
    "RoutingAttempt",
    "RoutingRequest",
    "RoutingResult",
    "validate_endpoint",
    "model_task_handler",
    "verify_output",
    "AgentDefinition",
    "AgentHandoff",
    "AgentRegistry",
    "ProjectState",
    "SoftwareObjective",
    "TaskIntake",
    "VerificationRecord",
    "default_agent_registry",
    "classify_sensitive_domains",
    "sensitive_domain_safety",
    "AgentHandoffEnvelope",
    "AutomationSpec",
    "CodeSynthesisOutput",
    "IDEInspectionReport",
    "RefactorPlan",
    "PrototypeSpec",
    "ContractError",
    "ResearchBrief",
    "ResearchFinding",
    "ResearchOutput",
    "SourceEvidence",
    "EmbeddingIndexSpec",
    "StreamPolicy",
    "VerificationSpec",
    "WorkloadClassification",
    "classify_workload",
    "FilesystemPolicy",
    "LeastPrivilegePolicy",
    "NetworkPolicy",
    "SecretRedactor",
    "SecurityViolation",
    "ToolPolicy",
    "require_dry_run",
    "SupplyChainReview",
    "review_downloaded_file",
    "RecoveryVerification",
    "build_rollback_plan",
    "verify_recovery_evidence",
    "FailurePattern",
    "review_completed_task_graphs",
    "create_app",
    "JsonlTraceRecorder",
    "TraceRecord",
    "RunObservabilityRecord",
    "RunObservabilityRecorder",
    "elapsed_ms",
    "SandboxError",
    "SandboxExecutor",
    "SandboxPlan",
    "SandboxPolicy",
    "SandboxResult",
    "SandboxUnavailable",
    "UnavailableSandboxExecutor",
    "LinuxBubblewrapExecutor",
    "WindowsSandboxExecutor",
    "discover_sandbox_adapters",
    "TufRepositoryVerifier",
    "TufVerificationError",
    "AttestationError",
    "AttestationPolicy",
    "AttestationRecord",
    "TrustStore",
    "verify_attestation",
    "verify_cosign_attestation",
    "ActivationAttestationEvidence",
    "AttestationVerificationService",
    "CanaryCohort",
    "CanaryPolicy",
    "CanaryPolicyError",
    "HealthThresholds",
    "RollbackLimits",
    "SecurityGateResult",
    "run_security_gate",
    "CanaryState",
    "DurableCanaryController",
    "HealthDecision",
    "HealthEvaluator",
    "HealthWindow",
    "WorkerRequest",
    "WorkerResponse",
    "decode_message",
    "encode_message",
    "LocalModelExecutionError",
    "LocalModelExecutionService",
    "execute_local_model",
    "ArtifactRecord",
    "ArtifactStore",
    "MediaAsset",
    "MediaHistoryRecord",
    "MediaProvenanceStore",
    "MediaTransformation",
    "MediaValidationPolicy",
    "MediaValidationResult",
    "validate_media",
    "DocumentVerificationPolicy",
    "DocumentVerificationResult",
    "verify_document",
    "EvaluationCheck",
    "EvaluationResult",
    "evaluate_output",
    "HealthCheck",
    "RuntimeHealth",
    "ConnectorHealth",
    "ConnectorHealthError",
    "ConnectorInventory",
    "ConnectorAuthPolicy",
    "ConnectorPolicyError",
    "EndpointConfigError",
    "LocalModelSpec",
    "ProviderEndpointSpec",
    "LocalModelExecutionPolicy",
    "LocalModelPolicyError",
    "BranchChange",
    "MergeDecision",
    "WorkspaceLease",
    "WorkspaceLeaseError",
    "WorkspaceLeaseRegistry",
    "reconcile_branch_changes",
    "IDEInspector",
    "inspect_repository",
    "EndpointProbeResult",
    "probe_endpoint",
    "validate_endpoint_url",
    "ConnectorTransferRequest",
    "CapabilityCallResult",
    "ConnectorCapabilityAudit",
    "ConnectorGovernanceError",
    "ConnectorMutationPolicy",
    "ConnectorMutationRequest",
    "BlackboxFallbackPolicy",
    "FallbackDecision",
    "BlackboxApiKeyContract",
    "BlackboxContractError",
    "validate_blackbox_error_payload",
    "BlackboxCapabilityError",
    "BlackboxCapabilityNegotiator",
    "BlackboxCapabilityResult",
    "BlackboxModelDiscovery",
    "BlackboxModelDiscoveryError",
    "BlackboxModelDiscoveryResult",
    "discover_blackbox_models",
    "initial_cloud_onboarding",
    "RunStatus",
    "TaskGraph",
    "TaskNode",
    "TaskStatus",
]
