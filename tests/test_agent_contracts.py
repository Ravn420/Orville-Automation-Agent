import pytest

from orville_core import (
    AgentHandoffEnvelope,
    ContractError,
    ResearchBrief,
    ResearchFinding,
    ResearchOutput,
    SourceEvidence,
)


def source(source_id="official"):
    return SourceEvidence(source_id, "https://example.test/source", "Example source", quality="official")


def test_research_output_requires_minimum_sources_and_resolves_citations():
    brief = ResearchBrief("Assess an API", minimum_sources=2, require_primary_sources=True)
    first = source("official")
    second = SourceEvidence("secondary", "https://example.test/secondary", "Secondary source")
    finding = ResearchFinding("f-1", "The API is documented.", ("official",), certainty="high", facts=("The source contains API documentation.",))
    with pytest.raises(ContractError, match="minimum source count"):
        ResearchOutput(brief, (first,), (finding,))
    output = ResearchOutput(brief, (first, second), (finding,))
    assert output.to_dict()["findings"][0]["source_ids"] == ["official"]


def test_research_finding_requires_citations_and_separated_content():
    with pytest.raises(ContractError, match="at least one source"):
        ResearchFinding("f-1", "Unsupported claim", ())
    with pytest.raises(ContractError, match="separate facts or analysis"):
        ResearchFinding("f-2", "Unstructured claim", ("official",))


def test_code_synthesis_output_requires_complete_runnable_deliverables():
    from orville_core import CodeSynthesisOutput

    output = CodeSynthesisOutput(
        objective="Add relay support",
        target_runtime="Python 3.10+",
        changed_files=("orville_core/relay.py",),
        dependencies=("fastapi",),
        setup_instructions=("pip install -e .[api]",),
        tests=("python -m pytest -q",),
        documentation_blocks=("Configuration",),
    )
    assert output.to_dict()["target_runtime"] == "Python 3.10+"


def test_code_synthesis_output_rejects_unsafe_paths_and_missing_validation():
    from orville_core import CodeSynthesisOutput

    with pytest.raises(ContractError, match="relative workspace"):
        CodeSynthesisOutput("objective", "Python", ("../secret.txt",), setup_instructions=("run",), tests=("test",))
    with pytest.raises(ContractError, match="validation tests"):
        CodeSynthesisOutput("objective", "Python", ("src/main.py",), setup_instructions=("run",))


def test_ide_inspection_report_captures_repository_impact_analysis():
    from orville_core import IDEInspectionReport

    report = IDEInspectionReport(
        repository_root="Orville",
        inspected_paths=("orville_core/api.py", "tests/test_api.py"),
        entry_points=("orville_core/api.py",),
        dependency_edges=(("api.py", "providers.py"),),
        configuration_files=("pyproject.toml",),
        shared_interfaces=("ProviderConfig",),
        impact_findings=("Provider changes affect API registration.",),
    )
    assert report.to_dict()["dependency_edges"] == [["api.py", "providers.py"]]


def test_ide_inspection_report_rejects_unsafe_paths():
    from orville_core import IDEInspectionReport

    with pytest.raises(ContractError, match="relative workspace"):
        IDEInspectionReport("Orville", ("../outside.py",))


def test_refactor_plan_requires_impact_analysis_and_validation():
    from orville_core import RefactorPlan

    plan = RefactorPlan(
        objective="Refactor provider registration",
        affected_files=("orville_core/api.py",),
        shared_interfaces=("ProviderRegistry",),
        preserved_behaviors=("Existing providers remain selectable.",),
        impact_findings=("API bootstrap and provider health routes are affected.",),
        validation_commands=("python -m pytest -q",),
        rollback_plan="Revert the isolated commit.",
    )
    assert plan.to_dict()["behavior_change_requested"] is False


def test_refactor_plan_rejects_missing_preservation_or_impact_details():
    from orville_core import RefactorPlan

    with pytest.raises(ContractError, match="preserved behaviors"):
        RefactorPlan("Refactor", ("src/main.py",), validation_commands=("test",))
    with pytest.raises(ContractError, match="impact findings"):
        RefactorPlan("Refactor", ("src/main.py",), shared_interfaces=("API",), preserved_behaviors=("Compatibility",), validation_commands=("test",))


def test_prototype_spec_requires_runnable_state_and_hardening_path():
    from orville_core import PrototypeSpec

    spec = PrototypeSpec(
        objective="Prototype relay dashboard",
        minimum_runnable_state=("Application starts", "Health route responds"),
        accepted_shortcuts=("In-memory state",),
        prohibited_shortcuts=("Embedded production credential",),
        local_run_commands=("python -m app",),
        smoke_test_commands=("curl /health",),
        debugging_handoff=("Include logs and reproduction steps",),
        hardening_steps=("Replace in-memory state", "Add production auth"),
    )
    assert spec.to_dict()["minimum_runnable_state"]


def test_prototype_spec_rejects_conflicting_shortcut_policy():
    from orville_core import PrototypeSpec

    with pytest.raises(ContractError, match="both accepted and prohibited"):
        PrototypeSpec("Prototype", ("Starts",), accepted_shortcuts=("mock",), prohibited_shortcuts=("mock",), local_run_commands=("run",), smoke_test_commands=("test",), hardening_steps=("harden",))


def test_automation_spec_requires_trigger_and_safety_controls():
    from orville_core import AutomationSpec

    spec = AutomationSpec(
        objective="Run a scheduled health check",
        trigger_type="schedule",
        trigger_config={"expression": "0 * * * *"},
        retry_limit=2,
        idempotency_key="health-check",
        notification_targets=("operator",),
        rollback_steps=("Disable schedule",),
        requires_persistent_runtime=True,
        health_checks=("/health returns 200",),
    )
    assert spec.to_dict()["retry_limit"] == 2


def test_automation_spec_rejects_unsafe_or_incomplete_execution():
    from orville_core import AutomationSpec

    with pytest.raises(ContractError, match="schedule automation"):
        AutomationSpec("Schedule", "schedule")
    with pytest.raises(ContractError, match="sensitive automation"):
        AutomationSpec("Send message", "manual", sensitive_action=True)
    with pytest.raises(ContractError, match="health checks"):
        AutomationSpec("Worker", "event", trigger_config={"source": "webhook"}, requires_persistent_runtime=True)


def test_verification_spec_requires_evidence_details_by_type():
    from orville_core import VerificationSpec

    spec = VerificationSpec(
        task_id="artifact-1",
        acceptance_criteria=("Artifact exists",),
        required_evidence_types=("test", "source", "artifact", "visual"),
        source_checks=("Verify citations resolve",),
        artifact_checks=("Verify checksum",),
        visual_checks=("Verify layout at desktop width",),
        independent_verifier="verification",
    )
    assert spec.to_dict()["required_evidence_types"][-1] == "visual"


def test_verification_spec_rejects_missing_type_specific_checks():
    from orville_core import VerificationSpec

    with pytest.raises(ContractError, match="source checks"):
        VerificationSpec("task", required_evidence_types=("source",))
    with pytest.raises(ContractError, match="artifact checks"):
        VerificationSpec("task", required_evidence_types=("artifact",))
    with pytest.raises(ContractError, match="visual checks"):
        VerificationSpec("task", required_evidence_types=("visual",))


def test_stream_policy_captures_backpressure_cancellation_reconnect_and_checkpoint_rules():
    from orville_core import StreamPolicy

    policy = StreamPolicy(max_buffer_chars=1000, cancellation_key="cancel_requested", reconnect_attempts=2, checkpoint_every_chunks=5, preserve_partial_output=True)
    assert policy.to_dict()["reconnect_attempts"] == 2


def test_stream_policy_rejects_invalid_limits():
    from orville_core import StreamPolicy

    with pytest.raises(ContractError, match="limits"):
        StreamPolicy(max_buffer_chars=0)
    with pytest.raises(ContractError, match="limits"):
        StreamPolicy(reconnect_attempts=-1)


def test_embedding_index_spec_validates_version_dimensions_and_batches():
    from orville_core import EmbeddingIndexSpec

    spec = EmbeddingIndexSpec("docs", version=2, dimension=3, max_batch_size=2, migration_from=1, migration_strategy="re-embed")
    spec.validate_vectors([[1.0, 2.0, 3.0]])
    with pytest.raises(ContractError, match="dimension"):
        spec.validate_vectors([[1.0, 2.0]])
    with pytest.raises(ContractError, match="max_batch_size"):
        spec.validate_vectors([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])


def test_embedding_index_spec_requires_migration_strategy():
    from orville_core import EmbeddingIndexSpec

    with pytest.raises(ContractError, match="migration"):
        EmbeddingIndexSpec("docs", version=2, dimension=3, migration_from=1)


def test_source_and_handoff_validation_rejects_unsafe_or_incomplete_contracts():
    with pytest.raises(ContractError, match="locator"):
        SourceEvidence("bad", "ftp://example.test", "Bad source")
    with pytest.raises(ContractError, match="identity"):
        AgentHandoffEnvelope("", "research", "code", "handoff")
    handoff = AgentHandoffEnvelope("task-1", "research", "verification", "Review evidence", expected_outputs=("report",))
    assert handoff.to_dict()["status"] == "ready"
