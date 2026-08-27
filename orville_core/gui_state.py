"""Pure, bounded presentation-state helpers shared by the desktop UI and local tools.

This module deliberately avoids GUI toolkit imports so state, redaction, and dashboard
aggregation rules remain testable on headless or minimal runtime environments.
"""
from __future__ import annotations

import re
from typing import Mapping


SENSITIVE_DISPLAY_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "password",
    "private_key",
    "prompt",
    "objective",
    "source",
    "path",
    "local_path",
    "storage_root",
    "token",
    "secret",
}


def _redact_display_text(value: str) -> str:
    """Remove credential-like values and local paths before presentation."""
    if ":\\" in value or "/Users/" in value or "/home/" in value or value.startswith("\\\\"):
        return "[redacted-local-path]"
    patterns = (
        (r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [redacted]"),
        (r"(?i)(?:sk|key|token)[-_][A-Za-z0-9._-]{8,}", "[redacted-secret]"),
        (r"(?i)(?:[A-Z]:\\|/Users/|/home/|\\\\)", "[redacted-local-path]"),
    )
    for pattern, replacement in patterns:
        value = re.sub(pattern, replacement, value)
    return value


def safe_display_value(value: object, key: str | None = None) -> object:
    """Return bounded presentation data while hiding secrets, prompts, and local paths."""
    if key and key.lower() in SENSITIVE_DISPLAY_KEYS:
        return "[redacted for interface safety]"
    if isinstance(value, dict):
        return {str(item_key): safe_display_value(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [safe_display_value(item) for item in value[:80]]
    if isinstance(value, str):
        return _redact_display_text(value[:4000])
    return value


WORKFLOW_STATE_COPY = {
    "loading": ("Loading", "Loading the latest workflow information.", "Wait briefly or refresh."),
    "empty": ("Nothing to show", "No matching workflow data is available yet.", "Start a workflow or enter a different run ID."),
    "offline": ("Offline", "The local Orville service could not be reached.", "Start the local service and try again."),
    "blocked": ("Blocked", "This workflow is waiting for approval or a required condition.", "Review the reason before continuing."),
    "failed": ("Could not complete", "The workflow could not complete this operation.", "Review the safe details and retry when appropriate."),
    "partial": ("Partially complete", "Some workflow steps finished while others need attention.", "Review completed and remaining steps."),
    "long_running": ("Still working", "This workflow is taking longer than usual and remains active.", "Keep monitoring or review the available controls."),
    "ready": ("Ready", "The workflow is available for review or action.", "Choose the next permitted action."),
}


DEPENDENCY_STATE_COPY = {
    "cloud_unavailable": (
        "Cloud provider unavailable",
        "The selected cloud provider cannot be reached or is not configured.",
        ("Continue with a local provider", "Save the draft", "Retry"),
    ),
    "local_endpoint_unavailable": (
        "Local endpoint unavailable",
        "The configured local model service could not be reached.",
        ("Start or check the local service", "Choose another local model", "Retry"),
    ),
    "connector_unavailable": (
        "Connector unavailable",
        "This connector is disabled, disconnected, or temporarily unavailable.",
        ("Review connector status", "Continue without the connector", "Retry"),
    ),
    "runtime_unavailable": (
        "Model runtime unavailable",
        "The selected model runtime is missing or cannot activate this model.",
        ("Choose a compatible model", "Save the task for later", "Review diagnostics"),
    ),
}


def classify_dependency_state(result: object) -> str:
    """Return a stable dependency state without exposing provider details."""
    if not isinstance(result, dict):
        return "runtime_unavailable"
    kind = str(result.get("dependency") or result.get("kind") or "").lower()
    status = str(result.get("status") or "").lower()
    if kind in {"cloud", "cloud_provider", "provider"}:
        return "cloud_unavailable"
    if kind in {"local", "local_endpoint", "endpoint"}:
        return "local_endpoint_unavailable"
    if kind in {"connector", "integration"}:
        return "connector_unavailable"
    if kind in {"runtime", "model_runtime", "model"}:
        return "runtime_unavailable"
    if status in {"provider_unavailable", "cloud_unavailable"}:
        return "cloud_unavailable"
    if status in {"endpoint_unavailable", "local_unavailable"}:
        return "local_endpoint_unavailable"
    if status in {"connector_unavailable", "disconnected"}:
        return "connector_unavailable"
    return "runtime_unavailable"


def dependency_state_message(state: str) -> str:
    """Format safe title, explanation, and recovery actions for a dependency state."""
    title, explanation, actions = DEPENDENCY_STATE_COPY.get(
        state, DEPENDENCY_STATE_COPY["runtime_unavailable"]
    )
    return f"{title}\n{explanation}\nNext: {'; '.join(actions)}"


def classify_workflow_state(result: object) -> str:
    """Return one stable, user-facing state without exposing raw provider details."""
    if not isinstance(result, dict) or result.get("error"):
        return "offline"
    tasks = result.get("graph", {}).get("tasks", []) if isinstance(result.get("graph"), dict) else []
    status = str(result.get("run_status") or "").lower()
    if status in {"waiting_approval", "blocked", "paused"}:
        return "blocked"
    if status in {"running", "queued", "pending", "in_progress"}:
        return "long_running"
    if not tasks:
        return "empty"
    statuses = [str(task.get("status") or "").lower() for task in tasks if isinstance(task, dict)]
    failed = sum(item in {"failed", "error"} for item in statuses)
    if failed and failed < len(statuses):
        return "partial"
    if statuses and failed == len(statuses):
        return "failed"
    return "ready"


def state_message(state: str) -> str:
    """Format a concise state title, explanation, and recovery/action hint."""
    title, explanation, action = WORKFLOW_STATE_COPY.get(state, WORKFLOW_STATE_COPY["failed"])
    return f"{title}\n{explanation}\nNext: {action}"


def dashboard_values(results: Mapping[str, object]) -> dict[str, str]:
    """Reduce API responses to bounded dashboard-card values without raw payloads."""
    health = results.get("health") if isinstance(results.get("health"), dict) else {}
    state = results.get("state") if isinstance(results.get("state"), dict) else {}
    providers = results.get("providers") if isinstance(results.get("providers"), dict) else {}
    artifacts = results.get("artifacts") if isinstance(results.get("artifacts"), dict) else {}
    tasks = state.get("tasks") or state.get("active_tasks") or []
    runs = state.get("runs") or state.get("recent_runs") or []
    failures = state.get("failures") or state.get("errors") or []
    provider_items = providers.get("providers") or []
    artifact_items = artifacts.get("artifacts") or []
    return {
        "active": str(len(tasks)) if isinstance(tasks, list) else "—",
        "runs": str(len(runs)) if isinstance(runs, list) else "—",
        "models": str(len(provider_items)) if isinstance(provider_items, list) else "—",
        "health": "ONLINE" if health.get("status") == "ok" else "CHECK",
        "failures": str(len(failures)) if isinstance(failures, list) else "—",
        "artifacts": str(len(artifact_items)) if isinstance(artifact_items, list) else "—",
    }
