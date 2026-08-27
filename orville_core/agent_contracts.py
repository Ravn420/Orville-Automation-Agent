"""Structured contracts for specialized Orville agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urlparse


class ContractError(ValueError):
    """Raised when an agent contract is incomplete or inconsistent."""


WORKLOAD_TYPES = frozenset({
    "one_shot",
    "recurring",
    "event_triggered",
    "webhook_driven",
    "persistent_service",
})


@dataclass(frozen=True)
class WorkloadClassification:
    """Deterministic workload class and operational requirements."""

    workload_type: str
    reason: str
    required_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.workload_type not in WORKLOAD_TYPES:
            raise ContractError("unsupported workload type")
        if not self.reason.strip():
            raise ContractError("workload classification reason must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "workload_type": self.workload_type,
            "reason": self.reason,
            "required_fields": list(self.required_fields),
        }


@dataclass(frozen=True)
class SourceEvidence:
    source_id: str
    locator: str
    title: str
    source_type: str = "web"
    quality: str = "secondary"
    retrieved_at: str | None = None
    excerpt: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.title.strip():
            raise ContractError("source_id and title must be non-empty")
        if urlparse(self.locator).scheme not in {"http", "https", "file"}:
            raise ContractError("source locator must use http, https, or file")
        if self.quality not in {"primary", "official", "secondary", "tertiary", "user-provided"}:
            raise ContractError("unsupported source quality")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "locator": self.locator,
            "title": self.title,
            "source_type": self.source_type,
            "quality": self.quality,
            "retrieved_at": self.retrieved_at,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class ResearchBrief:
    objective: str
    questions: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    minimum_sources: int = 2
    require_primary_sources: bool = False

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ContractError("research objective must not be empty")
        if self.minimum_sources < 1:
            raise ContractError("minimum_sources must be positive")


@dataclass(frozen=True)
class ResearchFinding:
    finding_id: str
    statement: str
    source_ids: tuple[str, ...]
    certainty: str = "medium"
    facts: tuple[str, ...] = ()
    analysis: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.finding_id.strip() or not self.statement.strip():
            raise ContractError("finding_id and statement must be non-empty")
        if not self.source_ids:
            raise ContractError("every material finding must cite at least one source")
        if self.certainty not in {"high", "medium", "low", "unknown"}:
            raise ContractError("certainty must be high, medium, low, or unknown")
        if not self.facts and not self.analysis:
            raise ContractError("finding must separate facts or analysis")

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "statement": self.statement,
            "source_ids": list(self.source_ids),
            "certainty": self.certainty,
            "facts": list(self.facts),
            "analysis": list(self.analysis),
            "assumptions": list(self.assumptions),
            "recommendations": list(self.recommendations),
        }


@dataclass(frozen=True)
class ResearchOutput:
    brief: ResearchBrief
    sources: tuple[SourceEvidence, ...]
    findings: tuple[ResearchFinding, ...]
    limitations: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        source_ids = {source.source_id for source in self.sources}
        if len(source_ids) != len(self.sources):
            raise ContractError("source IDs must be unique")
        if len(self.sources) < self.brief.minimum_sources:
            raise ContractError("research output does not meet minimum source count")
        if self.brief.require_primary_sources and not any(source.quality in {"primary", "official"} for source in self.sources):
            raise ContractError("research output requires at least one primary or official source")
        for finding in self.findings:
            missing = set(finding.source_ids) - source_ids
            if missing:
                raise ContractError(f"finding cites unknown sources: {sorted(missing)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "brief": {
                "objective": self.brief.objective,
                "questions": list(self.brief.questions),
                "scope": list(self.brief.scope),
                "constraints": list(self.brief.constraints),
                "minimum_sources": self.brief.minimum_sources,
                "require_primary_sources": self.brief.require_primary_sources,
            },
            "sources": [source.to_dict() for source in self.sources],
            "findings": [finding.to_dict() for finding in self.findings],
            "limitations": list(self.limitations),
            "unresolved_questions": list(self.unresolved_questions),
        }


@dataclass(frozen=True)
class CodeSynthesisOutput:
    objective: str
    target_runtime: str
    changed_files: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    configuration: tuple[str, ...] = ()
    setup_instructions: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    documentation_blocks: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.objective.strip() or not self.target_runtime.strip():
            raise ContractError("code objective and target runtime must be non-empty")
        if not self.changed_files:
            raise ContractError("code output must list changed files")
        if any(not path.strip() or path.startswith(("/", "\\")) or ".." in path.replace("\\", "/").split("/") for path in self.changed_files):
            raise ContractError("changed files must be relative workspace paths")
        if not self.tests:
            raise ContractError("code output must include validation tests or commands")
        if not self.setup_instructions:
            raise ContractError("code output must include setup instructions")

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "target_runtime": self.target_runtime,
            "changed_files": list(self.changed_files),
            "dependencies": list(self.dependencies),
            "configuration": list(self.configuration),
            "setup_instructions": list(self.setup_instructions),
            "tests": list(self.tests),
            "documentation_blocks": list(self.documentation_blocks),
            "known_limitations": list(self.known_limitations),
        }


@dataclass(frozen=True)
class IDEInspectionReport:
    repository_root: str
    inspected_paths: tuple[str, ...]
    entry_points: tuple[str, ...] = ()
    dependency_edges: tuple[tuple[str, str], ...] = ()
    configuration_files: tuple[str, ...] = ()
    shared_interfaces: tuple[str, ...] = ()
    impact_findings: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.repository_root.strip() or not self.inspected_paths:
            raise ContractError("repository root and inspected paths must be provided")
        paths = self.inspected_paths + self.entry_points + self.configuration_files
        if any(not path.strip() or path.startswith(("/", "\\")) or ".." in path.replace("\\", "/").split("/") for path in paths):
            raise ContractError("inspection paths must be relative workspace paths")
        for edge in self.dependency_edges:
            if len(edge) != 2 or not all(edge):
                raise ContractError("dependency edges must contain source and target")

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository_root": self.repository_root,
            "inspected_paths": list(self.inspected_paths),
            "entry_points": list(self.entry_points),
            "dependency_edges": [list(edge) for edge in self.dependency_edges],
            "configuration_files": list(self.configuration_files),
            "shared_interfaces": list(self.shared_interfaces),
            "impact_findings": list(self.impact_findings),
            "risks": list(self.risks),
        }


@dataclass(frozen=True)
class RefactorPlan:
    objective: str
    affected_files: tuple[str, ...]
    shared_interfaces: tuple[str, ...] = ()
    behavior_change_requested: bool = False
    preserved_behaviors: tuple[str, ...] = ()
    impact_findings: tuple[str, ...] = ()
    validation_commands: tuple[str, ...] = ()
    rollback_plan: str = ""

    def __post_init__(self) -> None:
        if not self.objective.strip() or not self.affected_files:
            raise ContractError("refactor objective and affected files must be provided")
        if any(not path.strip() or path.startswith(("/", "\\")) or ".." in path.replace("\\", "/").split("/") for path in self.affected_files):
            raise ContractError("refactor files must be relative workspace paths")
        if self.shared_interfaces and not self.impact_findings:
            raise ContractError("shared-interface changes require impact findings")
        if not self.behavior_change_requested and not self.preserved_behaviors:
            raise ContractError("behavior-preserving refactors must list preserved behaviors")
        if not self.validation_commands:
            raise ContractError("refactor plan must include validation commands")

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "affected_files": list(self.affected_files),
            "shared_interfaces": list(self.shared_interfaces),
            "behavior_change_requested": self.behavior_change_requested,
            "preserved_behaviors": list(self.preserved_behaviors),
            "impact_findings": list(self.impact_findings),
            "validation_commands": list(self.validation_commands),
            "rollback_plan": self.rollback_plan,
        }


@dataclass(frozen=True)
class PrototypeSpec:
    objective: str
    minimum_runnable_state: tuple[str, ...]
    accepted_shortcuts: tuple[str, ...] = ()
    prohibited_shortcuts: tuple[str, ...] = ()
    local_run_commands: tuple[str, ...] = ()
    smoke_test_commands: tuple[str, ...] = ()
    debugging_handoff: tuple[str, ...] = ()
    hardening_steps: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.objective.strip() or not self.minimum_runnable_state:
            raise ContractError("prototype objective and minimum runnable state are required")
        if not self.local_run_commands or not self.smoke_test_commands:
            raise ContractError("prototype must define local run and smoke-test commands")
        if not self.hardening_steps:
            raise ContractError("prototype must define a production-hardening path")
        overlap = set(self.accepted_shortcuts) & set(self.prohibited_shortcuts)
        if overlap:
            raise ContractError(f"shortcut cannot be both accepted and prohibited: {sorted(overlap)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "minimum_runnable_state": list(self.minimum_runnable_state),
            "accepted_shortcuts": list(self.accepted_shortcuts),
            "prohibited_shortcuts": list(self.prohibited_shortcuts),
            "local_run_commands": list(self.local_run_commands),
            "smoke_test_commands": list(self.smoke_test_commands),
            "debugging_handoff": list(self.debugging_handoff),
            "hardening_steps": list(self.hardening_steps),
        }


@dataclass(frozen=True)
class AutomationSpec:
    objective: str
    trigger_type: str
    trigger_config: dict[str, Any] = field(default_factory=dict)
    retry_limit: int = 0
    idempotency_key: str | None = None
    notification_targets: tuple[str, ...] = ()
    rollback_steps: tuple[str, ...] = ()
    connector_ids: tuple[str, ...] = ()
    requires_persistent_runtime: bool = False
    sensitive_action: bool = False
    approval_required: bool = False
    health_checks: tuple[str, ...] = ()
    workload_type: str | None = None

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ContractError("automation objective must not be empty")
        if self.trigger_type not in {"manual", "schedule", "webhook", "event", "data", "task_event"}:
            raise ContractError("unsupported automation trigger type")
        if self.retry_limit < 0:
            raise ContractError("retry_limit must not be negative")
        if self.trigger_type == "schedule" and not self.trigger_config.get("expression"):
            raise ContractError("schedule automation requires an expression")
        if self.trigger_type in {"webhook", "event"} and not self.trigger_config.get("source"):
            raise ContractError("event automation requires a source")
        if self.sensitive_action and not self.approval_required:
            raise ContractError("sensitive automation requires approval")
        if self.requires_persistent_runtime and not self.health_checks:
            raise ContractError("persistent automation requires health checks")
        if self.workload_type is not None and self.workload_type not in WORKLOAD_TYPES:
            raise ContractError("unsupported workload type")

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "trigger_type": self.trigger_type,
            "trigger_config": dict(self.trigger_config),
            "retry_limit": self.retry_limit,
            "idempotency_key": self.idempotency_key,
            "notification_targets": list(self.notification_targets),
            "rollback_steps": list(self.rollback_steps),
            "connector_ids": list(self.connector_ids),
            "requires_persistent_runtime": self.requires_persistent_runtime,
            "sensitive_action": self.sensitive_action,
            "approval_required": self.approval_required,
            "health_checks": list(self.health_checks),
            "workload_type": self.workload_type,
        }


def classify_workload(spec: AutomationSpec | Mapping[str, Any]) -> WorkloadClassification:
    """Classify an automation specification without executing or scheduling it."""
    if isinstance(spec, AutomationSpec):
        values: Mapping[str, Any] = {
            "trigger_type": spec.trigger_type,
            "trigger_config": spec.trigger_config,
            "requires_persistent_runtime": spec.requires_persistent_runtime,
            "workload_type": getattr(spec, "workload_type", None),
        }
    else:
        values = spec
    trigger_type = str(values.get("trigger_type") or "").strip().lower()
    config = values.get("trigger_config") or {}
    if not isinstance(config, Mapping):
        raise ContractError("trigger_config must be a mapping")
    explicit = values.get("workload_type")
    explicit_type = str(explicit).strip().lower() if explicit is not None else None
    if explicit_type and explicit_type not in WORKLOAD_TYPES:
        raise ContractError("unsupported workload type")
    persistent = bool(values.get("requires_persistent_runtime")) or bool(config.get("persistent_service"))
    if persistent:
        inferred = "persistent_service"
        reason = "requires a persistent runtime or service lifecycle"
    elif trigger_type == "schedule":
        inferred = "recurring"
        reason = "a schedule trigger repeats work according to an expression or interval"
    elif trigger_type == "webhook":
        inferred = "webhook_driven"
        reason = "an inbound webhook initiates each run"
    elif trigger_type in {"event", "data", "connector", "task_event"}:
        inferred = "event_triggered"
        reason = "an external or task event initiates each run"
    elif trigger_type in {"", "manual"}:
        inferred = "one_shot"
        reason = "a manual or unspecified trigger represents an individual run"
    else:
        raise ContractError("unsupported trigger type for workload classification")
    if explicit_type and explicit_type != inferred:
        raise ContractError("workload type conflicts with trigger or runtime requirements")
    selected = explicit_type or inferred
    required = {
        "one_shot": ("objective",),
        "recurring": ("schedule expression or interval", "idempotency key"),
        "event_triggered": ("event source", "deduplication key"),
        "webhook_driven": ("webhook source", "signature policy", "replay protection"),
        "persistent_service": ("health checks", "restart policy", "shutdown behavior"),
    }[selected]
    return WorkloadClassification(selected, reason, required)


@dataclass(frozen=True)
class EmbeddingIndexSpec:
    index_id: str
    version: int
    dimension: int
    max_batch_size: int = 64
    migration_from: int | None = None
    migration_strategy: str | None = None

    def __post_init__(self) -> None:
        if not self.index_id.strip() or self.version < 1 or self.dimension < 1 or self.max_batch_size < 1:
            raise ContractError("embedding index ID, version, dimension, and batch size must be positive")
        if self.migration_from is not None:
            if self.migration_from >= self.version:
                raise ContractError("migration_from must reference an older index version")
            if not self.migration_strategy or not self.migration_strategy.strip():
                raise ContractError("embedding migrations require a strategy")

    def validate_vectors(self, vectors: list[list[float]]) -> None:
        if len(vectors) > self.max_batch_size:
            raise ContractError(f"embedding batch exceeds max_batch_size ({self.max_batch_size})")
        if any(len(vector) != self.dimension for vector in vectors):
            raise ContractError(f"embedding vector dimension must be {self.dimension}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "index_id": self.index_id,
            "version": self.version,
            "dimension": self.dimension,
            "max_batch_size": self.max_batch_size,
            "migration_from": self.migration_from,
            "migration_strategy": self.migration_strategy,
        }


@dataclass(frozen=True)
class StreamPolicy:
    max_buffer_chars: int = 1_000_000
    cancellation_key: str = "cancel_requested"
    reconnect_attempts: int = 0
    checkpoint_every_chunks: int = 10
    preserve_partial_output: bool = True

    def __post_init__(self) -> None:
        if self.max_buffer_chars < 1 or self.reconnect_attempts < 0 or self.checkpoint_every_chunks < 1:
            raise ContractError("stream policy limits must be positive and reconnect attempts cannot be negative")
        if not self.cancellation_key.strip():
            raise ContractError("stream cancellation key must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_buffer_chars": self.max_buffer_chars,
            "cancellation_key": self.cancellation_key,
            "reconnect_attempts": self.reconnect_attempts,
            "checkpoint_every_chunks": self.checkpoint_every_chunks,
            "preserve_partial_output": self.preserve_partial_output,
        }


@dataclass(frozen=True)
class VerificationSpec:
    task_id: str
    acceptance_criteria: tuple[str, ...] = ()
    required_evidence_types: tuple[str, ...] = ()
    source_checks: tuple[str, ...] = ()
    artifact_checks: tuple[str, ...] = ()
    visual_checks: tuple[str, ...] = ()
    independent_verifier: str = "verification"
    severity_if_failed: str = "high"

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.independent_verifier.strip():
            raise ContractError("verification task and independent verifier are required")
        allowed = {"test", "source", "artifact", "visual", "security", "manual"}
        unknown = set(self.required_evidence_types) - allowed
        if unknown:
            raise ContractError(f"unsupported evidence types: {sorted(unknown)}")
        if "source" in self.required_evidence_types and not self.source_checks:
            raise ContractError("source evidence requires source checks")
        if "artifact" in self.required_evidence_types and not self.artifact_checks:
            raise ContractError("artifact evidence requires artifact checks")
        if "visual" in self.required_evidence_types and not self.visual_checks:
            raise ContractError("visual evidence requires visual checks")
        if self.severity_if_failed not in {"low", "medium", "high", "critical"}:
            raise ContractError("invalid verification failure severity")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "acceptance_criteria": list(self.acceptance_criteria),
            "required_evidence_types": list(self.required_evidence_types),
            "source_checks": list(self.source_checks),
            "artifact_checks": list(self.artifact_checks),
            "visual_checks": list(self.visual_checks),
            "independent_verifier": self.independent_verifier,
            "severity_if_failed": self.severity_if_failed,
        }


@dataclass(frozen=True)
class AgentHandoffEnvelope:
    task_id: str
    from_agent: str
    to_agent: str
    objective: str
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_outputs: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = ()
    status: str = "ready"

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.task_id, self.from_agent, self.to_agent, self.objective)):
            raise ContractError("handoff identity and objective must be non-empty")
        if self.status not in {"planned", "ready", "blocked", "completed", "rejected"}:
            raise ContractError("unsupported handoff status")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "objective": self.objective,
            "inputs": dict(self.inputs),
            "expected_outputs": list(self.expected_outputs),
            "acceptance_criteria": list(self.acceptance_criteria),
            "known_limitations": list(self.known_limitations),
            "status": self.status,
        }
