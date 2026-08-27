from __future__ import annotations

import json
from datetime import datetime
import re
import os
import sys
import threading
import urllib.error
import urllib.request
from urllib.parse import quote
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


# Orville desktop control center. The API contract and workflow actions remain unchanged;
# this module intentionally limits changes to presentation and interaction structure.

SENSITIVE_DISPLAY_KEYS = {"api_key", "apikey", "authorization", "bearer", "cookie", "password", "private_key", "prompt", "objective", "source", "path", "local_path", "storage_root", "token", "secret"}


def _redact_display_text(value: str) -> str:
    """Remove credential-like values and local paths before text reaches a widget."""
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
    """Return bounded UI data while hiding secrets, prompts, and filesystem paths."""
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

GUI_ENGINE_ACTIONS = {
    "create_run": ("POST", "/api/v1/objectives", "objective"),
    "execute_run": ("POST", "/api/v1/objectives/{run_id}/execute", "stream"),
    "pause_monitor": ("LOCAL", None, None),
    "resume_run": ("POST", "/api/v1/objectives/{run_id}/execute", "stream"),
    "cancel_run": ("POST", "/api/v1/runs/{run_id}/cancel", None),
    "approve_task": ("POST", "/api/v1/runs/{run_id}/tasks/{task_id}/approval", "approved"),
    "retry_run": ("POST", "/api/v1/objectives/{run_id}/execute", "stream"),
    "checkpoint": ("GET", "/api/v1/runs/{run_id}", None),
    "verification": ("GET", "/api/v1/runs/{run_id}", None),
    "artifact_list": ("GET", "/api/v1/artifacts", None),
}


def build_engine_action_request(action: str, run_id: str | None = None, task_id: str | None = None) -> tuple[str, str, dict | None]:
    """Build the authenticated GUI-to-engine request for a supported action.

    The two read projections named ``checkpoint`` and ``verification`` intentionally
    use the persisted run endpoint because the current engine owns both records.
    ``pause_monitor`` is a local UI operation; the backend has no run-pause endpoint.
    """
    if action not in GUI_ENGINE_ACTIONS:
        raise ValueError(f"unsupported GUI engine action: {action}")
    method, template, payload_key = GUI_ENGINE_ACTIONS[action]
    if method == "LOCAL":
        return method, "", None
    if "{run_id}" in template and not str(run_id or "").strip():
        raise ValueError(f"{action} requires a run_id")
    if "{task_id}" in template and not str(task_id or "").strip():
        raise ValueError(f"{action} requires a task_id")
    path = template.format(run_id=quote(str(run_id), safe=""), task_id=quote(str(task_id), safe=""))
    if action in {"execute_run", "resume_run", "retry_run"}:
        return method, path, {"context": {"stream": True}}
    if action == "approve_task":
        return method, path, {"approved": True}
    return method, path, None


def load_env() -> None:
    for path in (
        Path(sys.executable).resolve().parent / ".env.production",
        Path(__file__).resolve().parent / ".env.production",
        Path.cwd() / ".env.production",
    ):
        if path.exists():
            for raw in path.read_text(encoding="utf-8-sig").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
            return


def start_api() -> None:
    import uvicorn
    from orville_core.api import create_app

    host = os.getenv("ORVILLE_API_HOST", "127.0.0.1")
    port = int(os.getenv("ORVILLE_API_PORT", "8787"))
    uvicorn.run(create_app, factory=True, host=host, port=port, log_level="warning")


class OrvilleWindow(tk.Tk):
    """Responsive desktop workspace for the existing Orville API bridge."""

    BG = "#f5f5f3"
    SIDEBAR = "#ebeae7"
    SURFACE = "#ffffff"
    TEXT = "#171717"
    MUTED = "#777873"
    BORDER = "#deded9"
    ACCENT = "#8b5cf6"
    SUCCESS = "#247a4b"
    WARNING = "#9a6700"
    DANGER = "#b42318"

    def __init__(self) -> None:
        super().__init__()
        self.title("Orville — Control Center")
        self.geometry("1240x760")
        self.minsize(720, 520)
        self.configure(bg=self.BG)
        self.base_url = f"http://127.0.0.1:{os.getenv('ORVILLE_API_PORT', '8787')}"
        self.token = os.getenv("ORVILLE_API_TOKEN", "")
        self.sidebar_visible = True
        self.context_visible = True
        self._placeholder = "Describe an objective for Orville…"
        self._build_styles()
        self._build_ui()
        self.bind("<Configure>", self._on_resize)
        self._configure_accessibility()
        self.after(300, self._wait_for_api)

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=self.BG)
        style.configure("Sidebar.TFrame", background=self.SIDEBAR)
        style.configure("Surface.TFrame", background=self.SURFACE)
        style.configure("Top.TFrame", background=self.SURFACE)
        style.configure("Title.TLabel", background=self.SURFACE, foreground=self.TEXT, font=("Segoe UI", 17, "bold"))
        style.configure("Subtitle.TLabel", background=self.SURFACE, foreground=self.MUTED, font=("Segoe UI", 9))
        style.configure("Section.TLabel", background=self.SIDEBAR, foreground=self.MUTED, font=("Segoe UI", 8, "bold"))
        style.configure("Nav.TButton", background=self.SIDEBAR, foreground=self.TEXT, borderwidth=0, padding=(10, 8), anchor="w", font=("Segoe UI", 9))
        style.map("Nav.TButton", background=[("active", "#e1e0dc")], foreground=[("disabled", "#aaa9a4")], relief=[("focus", "solid")], bordercolor=[("focus", self.ACCENT)])
        style.configure("Primary.TButton", background=self.TEXT, foreground="#ffffff", borderwidth=0, padding=(14, 9), font=("Segoe UI", 9, "bold"))
        style.map("Primary.TButton", background=[("active", "#343434"), ("pressed", "#050505"), ("disabled", "#b8b8b5")], relief=[("focus", "solid")], bordercolor=[("focus", self.ACCENT)])
        style.configure("Secondary.TButton", background=self.SURFACE, foreground=self.TEXT, bordercolor=self.BORDER, relief="solid", borderwidth=1, padding=(11, 8), font=("Segoe UI", 9))
        style.map("Secondary.TButton", background=[("active", "#f4f4f2"), ("pressed", "#eaeae7")], relief=[("focus", "solid")], bordercolor=[("focus", self.ACCENT)])
        style.configure("Quiet.TButton", background=self.SURFACE, foreground=self.MUTED, borderwidth=0, padding=(8, 7), font=("Segoe UI", 9))
        style.map("Quiet.TButton", foreground=[("active", self.TEXT)], relief=[("focus", "solid")], bordercolor=[("focus", self.ACCENT)])
        style.configure("Tab.TButton", background=self.SURFACE, foreground=self.MUTED, borderwidth=0, padding=(9, 6), font=("Segoe UI", 9))
        style.map("Tab.TButton", foreground=[("active", self.TEXT)], relief=[("focus", "solid")], bordercolor=[("focus", self.ACCENT)])
        style.map("TEntry", fieldbackground=[("focus", "#fbf9ff")], bordercolor=[("focus", self.ACCENT)])
        style.map("TCombobox", fieldbackground=[("focus", "#fbf9ff")], bordercolor=[("focus", self.ACCENT)])

    def _configure_accessibility(self) -> None:
        """Add predictable keyboard entry points and visible focus indication."""
        self.bind_all("<Alt-Key-1>", lambda _event: self._focus_composer())
        self.bind_all("<Alt-Key-2>", lambda _event: self.show_workflow_help())
        self.bind_all("<Escape>", lambda _event: self.focus_set())
        self.objective.configure(takefocus=True)
        self.output.configure(takefocus=True)
        self.context_text.configure(takefocus=True)
        for widget in (self.objective, self.output, self.context_text):
            widget.configure(highlightthickness=2, highlightbackground=self.BORDER, highlightcolor=self.ACCENT)
            widget.bind("<FocusIn>", lambda _event, control=widget: control.configure(highlightbackground=self.ACCENT))
            widget.bind("<FocusOut>", lambda _event, control=widget: control.configure(highlightbackground=self.BORDER))

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, style="Top.TFrame", padding=(18, 14))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(2, weight=1)
        ttk.Button(top, text="☰", style="Quiet.TButton", command=self.toggle_sidebar).grid(row=0, column=0, padx=(0, 8))
        brand = ttk.Frame(top, style="Top.TFrame")
        brand.grid(row=0, column=1, sticky="w")
        ttk.Label(brand, text="Orville", style="Title.TLabel").pack(anchor="w")
        ttk.Label(brand, text="Autonomous workspace", style="Subtitle.TLabel").pack(anchor="w")
        ttk.Label(top, text="LOCAL CONTROL CENTER", style="Subtitle.TLabel").grid(row=0, column=2, sticky="e", padx=14)
        self.connection_badge = tk.Label(top, text="●  STARTING", bg=self.SURFACE, fg=self.WARNING, font=("Segoe UI", 9, "bold"))
        self.connection_badge.grid(row=0, column=3, padx=10)
        ttk.Button(top, text="API docs", style="Secondary.TButton", command=lambda: webbrowser.open(self.base_url + "/docs")).grid(row=0, column=4, padx=(6, 0))
        ttk.Button(top, text="Exit", style="Quiet.TButton", command=self.destroy).grid(row=0, column=5, padx=(2, 0))

        self.workspace = ttk.Frame(self, style="App.TFrame", padding=(12, 0, 12, 12))
        self.workspace.grid(row=1, column=0, sticky="nsew")
        self.workspace.rowconfigure(0, weight=1)
        self.workspace.columnconfigure(1, weight=1)
        self.workspace.columnconfigure(0, minsize=210)
        self.workspace.columnconfigure(2, minsize=274)
        self._build_sidebar()
        self._build_center()
        self._build_context()

    def _build_sidebar(self) -> None:
        self.sidebar = ttk.Frame(self.workspace, style="Sidebar.TFrame", padding=(12, 16))
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.sidebar.rowconfigure(7, weight=1)
        ttk.Button(self.sidebar, text="＋  New objective", style="Primary.TButton", command=self._focus_composer).pack(fill="x", pady=(0, 22))
        for title, items in (("WORKSPACE", ("Overview", "Active tasks", "Recent activity", "Verification")), ("RESOURCES", ("Artifacts", "Integrations")), ("SYSTEM", ("Settings",))):
            ttk.Label(self.sidebar, text=title, style="Section.TLabel").pack(anchor="w", padx=10, pady=(7, 5))
            for item in items:
                command = self.open_execution_monitor if item in {"Active tasks", "Recent activity"} else self.open_verification_review if item == "Verification" else self.show_workflow_help if item == "Overview" else lambda name=item: self._write(f"{name} is available through the existing Orville workflow.")
                ttk.Button(self.sidebar, text="  " + item, style="Nav.TButton", command=command).pack(fill="x")
        ttk.Label(self.sidebar, text="LOCAL MODELS", style="Section.TLabel").pack(anchor="w", padx=10, pady=(18, 5))
        ttk.Button(self.sidebar, text="  Import model", style="Nav.TButton", command=self.import_local_model).pack(fill="x")
        ttk.Button(self.sidebar, text="  Model manager", style="Nav.TButton", command=self.open_model_manager).pack(fill="x")
        ttk.Button(self.sidebar, text="  Provider setup", style="Nav.TButton", command=self.open_provider_setup).pack(fill="x")
        account = tk.Frame(self.sidebar, bg=self.SIDEBAR)
        account.pack(side="bottom", fill="x", pady=(18, 0))
        tk.Label(account, text="●", bg=self.SIDEBAR, fg=self.ACCENT, font=("Segoe UI", 16)).pack(side="left", padx=(6, 8))
        tk.Label(account, text="Local operator\nOrville workspace", justify="left", bg=self.SIDEBAR, fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left")

    def _build_center(self) -> None:
        self.center = ttk.Frame(self.workspace, style="App.TFrame", padding=(2, 0))
        self.center.grid(row=0, column=1, sticky="nsew")
        self.center.rowconfigure(2, weight=1)
        self.center.columnconfigure(0, weight=1)
        heading = ttk.Frame(self.center, style="App.TFrame", padding=(10, 12, 10, 10))
        heading.grid(row=0, column=0, sticky="ew")
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="What would you like Orville to do?", foreground=self.TEXT, background=self.BG, font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(heading, text="Describe a goal in your own words. Orville will plan, work, and check the result.", foreground=self.MUTED, background=self.BG, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.task_status = tk.Label(heading, text="READY", bg="#e9f5ee", fg=self.SUCCESS, padx=9, pady=4, font=("Segoe UI", 8, "bold"))
        self.task_status.grid(row=0, column=1, rowspan=2, sticky="e")

        self._build_dashboard()

        ttk.Label(self.center, text="Objective workspace — Use Tab to move through controls; Alt+1 focuses the objective; Alt+2 opens workflow help.", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 4))
        conversation = tk.Frame(self.center, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        conversation.grid(row=2, column=0, sticky="nsew", padx=8)
        conversation.rowconfigure(0, weight=1)
        conversation.columnconfigure(0, weight=1)
        self.output = scrolledtext.ScrolledText(conversation, wrap="word", state="disabled", bg=self.SURFACE, fg=self.TEXT, insertbackground=self.TEXT, relief="flat", borderwidth=0, padx=24, pady=22, font=("Segoe UI", 10), spacing1=3, spacing3=7)
        self.output.grid(row=0, column=0, sticky="nsew")
        self.output.tag_configure("meta", foreground=self.MUTED, font=("Segoe UI", 9, "bold"))
        self.output.tag_configure("user", foreground=self.ACCENT, font=("Segoe UI", 9, "bold"))
        self._write("Orville is ready. Describe an objective to create a verified task workflow.", "meta")

        composer = tk.Frame(self.center, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        composer.grid(row=3, column=0, sticky="ew", padx=8, pady=(10, 0))
        composer.columnconfigure(0, weight=1)
        self.objective = tk.Text(composer, height=4, wrap="word", bg=self.SURFACE, fg=self.MUTED, insertbackground=self.TEXT, relief="flat", borderwidth=0, padx=14, pady=12, font=("Segoe UI", 10), takefocus=True)
        self.objective.grid(row=0, column=0, columnspan=3, sticky="ew")
        self._placeholder = "Tell Orville what you need, in your own words…"
        self.objective.insert("1.0", self._placeholder)
        self.objective.bind("<FocusIn>", self._clear_placeholder)
        self.objective.bind("<FocusOut>", self._restore_placeholder)
        toolbar = tk.Frame(composer, bg=self.SURFACE)
        toolbar.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10))
        ttk.Button(toolbar, text="＋ Attach", style="Quiet.TButton", command=lambda: self._write("Attachment selection is preserved for the configured workflow.")).pack(side="left")
        ttk.Button(toolbar, text="◈ Tools", style="Quiet.TButton", command=lambda: self._write("Configured orchestration tools remain available to the existing API.")).pack(side="left")
        ttk.Label(toolbar, text="Add files or details if helpful · Ctrl+Enter to start", foreground=self.MUTED, background=self.SURFACE, font=("Segoe UI", 8)).pack(side="left", padx=12)
        ttk.Button(composer, text="Send objective  →", style="Primary.TButton", command=self.create_objective).grid(row=1, column=2, sticky="e", padx=10, pady=(0, 10))
        self.objective.bind("<Control-Return>", lambda _event: self.create_objective())

    def show_workflow_help(self) -> None:
        """Explain the primary workflow in plain language without framework terms."""
        self._write("How Orville works\\n\\n1. Tell Orville what you need.\\n2. Orville prepares a plan and asks before sensitive actions.\\n3. Orville carries out the work and shows progress.\\n4. Review the result, evidence, and any remaining risks.\\n\\nYou do not need to know about agents, task graphs, providers, or APIs. Use Active tasks to follow work, Model manager to choose where it runs, and Verification to review the result.", "meta")

    def open_execution_monitor(self) -> None:
        """Open a bounded monitor for persisted run status and event history."""
        window = tk.Toplevel(self)
        window.title("Orville — Execution Monitor")
        window.geometry("980x620")
        window.minsize(760, 460)
        window.configure(bg=self.BG)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)
        ttk.Label(window, text="Execution monitor", style="Title.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))
        ttk.Label(window, text="Track progress, agents, tool events, elapsed time, and safe run controls.", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(42, 10))
        body = ttk.Frame(window, style="Surface.TFrame", padding=12)
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 14))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)
        run_id = tk.StringVar()
        summary = tk.StringVar(value=state_message("empty"))
        ttk.Label(body, text="Run ID", background=self.SURFACE, foreground=self.MUTED).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(body, textvariable=run_id, width=42).grid(row=0, column=1, sticky="ew")
        output = scrolledtext.ScrolledText(body, wrap="word", state="disabled", bg=self.SURFACE, fg=self.TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 9), padx=10, pady=10)
        output.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(12, 10))
        polling = {"enabled": True}

        def write_safe(text: str) -> None:
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert("1.0", text)
            output.configure(state="disabled")

        def show_run(result: object) -> None:
            state = classify_workflow_state(result)
            if state == "offline":
                summary.set(state_message(state))
                write_safe(state_message(state))
                return
            tasks = result.get("graph", {}).get("tasks", []) if isinstance(result.get("graph"), dict) else []
            events = result.get("events", []) if isinstance(result.get("events"), list) else []
            elapsed = "—"
            timestamps = []
            for event in events:
                if isinstance(event, dict):
                    raw_timestamp = event.get("timestamp") or event.get("created_at")
                    if raw_timestamp:
                        try:
                            timestamps.append(datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00")))
                        except ValueError:
                            continue
            if len(timestamps) >= 2:
                elapsed_seconds = max(0, int((max(timestamps) - min(timestamps)).total_seconds()))
                elapsed = f"{elapsed_seconds // 60}m {elapsed_seconds % 60}s"
            lines = [f"Run: {result.get('run_id', '—')}", f"Status: {result.get('run_status', '—')}", f"Tasks: {len(tasks)}", f"Elapsed: {elapsed}"]
            for task in tasks if isinstance(tasks, list) else []:
                if isinstance(task, dict):
                    failure = " · failed" if task.get("status") == "failed" else ""
                    lines.append(f"  {task.get('task_id', 'task')} — {task.get('status', 'unknown')} · attempts {task.get('attempts', 0)}{failure}")
            summary.set(state_message(state))
            write_safe("\\n".join(lines))
            self._manager_request(f"/api/v1/runs/{quote(str(result.get('run_id', '')), safe='')}/events", "GET", None, show_events)

        def show_events(result: object) -> None:
            if not isinstance(result, dict):
                return
            events = result.get("events", [])
            if not isinstance(events, list):
                write_safe(state_message("failed"))
                return
            if not events:
                output.configure(state="normal")
                output.insert("end", "\\n" + state_message("empty"))
                output.configure(state="disabled")
                return
            lines = [f"\\nEvents: {len(events)}"]
            for event in events[-80:]:
                if not isinstance(event, dict):
                    continue
                event_type = str(event.get("event_type", "event"))
                task_id = str(event.get("task_id") or "run")
                timestamp = str(event.get("timestamp", ""))[:19]
                lines.append(f"{timestamp}  {task_id}  {event_type}")
            output.configure(state="normal")
            output.insert("end", "\\n" + "\\n".join(lines))
            output.configure(state="disabled")

        def refresh() -> None:
            value = run_id.get().strip()
            if not value:
                summary.set(state_message("empty"))
                write_safe(state_message("empty"))
                return
            summary.set(state_message("loading"))
            self._manager_request(f"/api/v1/runs/{quote(value, safe='')}", "GET", None, show_run)

        def action_request(action: str, task_id: str | None = None, callback=None) -> None:
            value = run_id.get().strip()
            if not value:
                summary.set(state_message("empty"))
                return
            try:
                method, path, payload = build_engine_action_request(action, value, task_id)
            except ValueError as exc:
                summary.set(str(exc))
                return
            self._manager_request(path, method, payload, callback or (lambda _result: (refresh(), summary.set(f"{action.replace('_', ' ').title()} request submitted"))))

        def control(action: str) -> None:
            action_request(action)

        def resume_waiting_task() -> None:
            value = run_id.get().strip()
            if not value:
                return
            def approve_waiting(result: object) -> None:
                tasks = result.get("graph", {}).get("tasks", []) if isinstance(result, dict) and isinstance(result.get("graph"), dict) else []
                waiting = [task.get("task_id") for task in tasks if isinstance(task, dict) and task.get("status") == "waiting_approval"]
                if not waiting:
                    summary.set("No waiting approval task")
                    return
                action_request("approve_task", str(waiting[0]), lambda _result: (summary.set("Approval request submitted"), refresh()))
            self._manager_request(f"/api/v1/runs/{quote(value, safe='')}", "GET", None, approve_waiting)

        def toggle_pause() -> None:
            polling["enabled"] = not polling["enabled"]
            pause_button.configure(text="Resume monitor" if not polling["enabled"] else "Pause monitor")
            summary.set("MONITOR PAUSED" if not polling["enabled"] else "MONITORING")

        controls = ttk.Frame(body, style="Surface.TFrame")
        controls.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Button(controls, text="Refresh", style="Secondary.TButton", command=refresh).pack(side="left", padx=3)
        pause_button = ttk.Button(controls, text="Pause monitor", style="Secondary.TButton", command=toggle_pause)
        pause_button.pack(side="left", padx=3)
        ttk.Button(controls, text="Resume waiting task", style="Secondary.TButton", command=resume_waiting_task).pack(side="left", padx=3)
        ttk.Button(controls, text="Retry run", style="Secondary.TButton", command=lambda: control("retry_run")).pack(side="left", padx=3)
        ttk.Button(controls, text="Cancel run", style="Secondary.TButton", command=lambda: control("cancel_run")).pack(side="left", padx=3)
        ttk.Button(controls, text="Load checkpoint", style="Secondary.TButton", command=lambda: action_request("checkpoint")).pack(side="left", padx=3)
        ttk.Button(controls, text="Review verification", style="Secondary.TButton", command=lambda: action_request("verification")).pack(side="left", padx=3)
        ttk.Button(controls, text="List artifacts", style="Secondary.TButton", command=lambda: self._manager_request("/api/v1/artifacts", "GET", None, lambda result: (write_safe(json.dumps(safe_display_value(result), indent=2)), summary.set("Artifact list loaded")))).pack(side="left", padx=3)
        ttk.Label(body, textvariable=summary, background=self.SURFACE, foreground=self.MUTED, font=("Segoe UI", 8)).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        def tick() -> None:
            if window.winfo_exists():
                if polling["enabled"]:
                    refresh()
                window.after(1500, tick)

        refresh()
        tick()

    def open_verification_review(self) -> None:
        """Open a safe review view for persisted acceptance and verification evidence."""
        window = tk.Toplevel(self)
        window.title("Orville — Verification & Review")
        window.geometry("980x650")
        window.minsize(760, 480)
        window.configure(bg=self.BG)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)
        ttk.Label(window, text="Verification & review", style="Title.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))
        ttk.Label(window, text="Review acceptance criteria, evidence, visual checks, defects, residual risks, and approval state.", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(42, 10))
        body = ttk.Frame(window, style="Surface.TFrame", padding=12)
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 14))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)
        run_id = tk.StringVar()
        summary = tk.StringVar(value=state_message("empty"))
        ttk.Label(body, text="Run ID", background=self.SURFACE, foreground=self.MUTED).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(body, textvariable=run_id, width=42).grid(row=0, column=1, sticky="ew")
        output = scrolledtext.ScrolledText(body, wrap="word", state="disabled", bg=self.SURFACE, fg=self.TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 9), padx=10, pady=10)
        output.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(12, 10))

        def render(result: object) -> None:
            state = classify_workflow_state(result)
            if state == "offline":
                summary.set(state_message(state))
                output.configure(state="normal")
                output.delete("1.0", "end")
                output.insert("1.0", state_message(state))
                output.configure(state="disabled")
                return
            context = result.get("context") if isinstance(result.get("context"), dict) else {}
            graph = result.get("graph") if isinstance(result.get("graph"), dict) else {}
            tasks = graph.get("tasks") if isinstance(graph.get("tasks"), list) else []
            sections = (
                ("Acceptance criteria", context.get("acceptance_criteria") or context.get("objective") or "Not recorded"),
                ("Test results", context.get("verifications") or {"task_statuses": [task.get("status") for task in tasks if isinstance(task, dict)]}),
                ("Source evidence", context.get("citations") or context.get("source_evidence") or "Not recorded"),
                ("Visual checks", context.get("visual_checks") or "Not recorded"),
                ("Defects", context.get("defects") or [task.get("error") for task in tasks if isinstance(task, dict) and task.get("error")]),
                ("Residual risks", context.get("residual_risks") or context.get("risks") or "Not recorded"),
                ("Approval state", context.get("approval_state") or result.get("run_status") or "Not recorded"),
            )
            lines = [f"Run: {result.get('run_id', '—')}", f"Status: {result.get('run_status', '—')}", ""]
            for title, value in sections:
                lines.append(title)
                safe_value = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
                lines.append(safe_value[:4000])
                lines.append("")
            summary.set(state_message(state))
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert("1.0", "\\n".join(lines))
            output.configure(state="disabled")

        def refresh() -> None:
            value = run_id.get().strip()
            if not value:
                summary.set(state_message("empty"))
                output.configure(state="normal")
                output.delete("1.0", "end")
                output.insert("1.0", state_message("empty"))
                output.configure(state="disabled")
                return
            summary.set(state_message("loading"))
            self._manager_request(f"/api/v1/runs/{quote(value, safe='')}", "GET", None, render)

        controls = ttk.Frame(body, style="Surface.TFrame")
        controls.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Button(controls, text="Refresh review", style="Secondary.TButton", command=refresh).pack(side="left", padx=3)
        ttk.Label(body, textvariable=summary, background=self.SURFACE, foreground=self.MUTED, font=("Segoe UI", 8)).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        refresh()

    def _build_dashboard(self) -> None:
        """Build compact operational cards backed by existing read-only routes."""
        dashboard = ttk.Frame(self.center, style="App.TFrame", padding=(8, 0, 8, 8))
        dashboard.grid(row=1, column=0, sticky="ew")
        for column in range(3):
            dashboard.columnconfigure(column, weight=1)
        self.dashboard_vars = {key: tk.StringVar(value="—") for key in ("active", "runs", "models", "health", "failures", "artifacts")}
        self.dashboard_cards: list[tk.Frame] = []
        cards = (
            ("ACTIVE TASKS", "active", self.ACCENT),
            ("RECENT RUNS", "runs", self.TEXT),
            ("MODEL AVAILABILITY", "models", self.ACCENT),
            ("SYSTEM HEALTH", "health", self.SUCCESS),
            ("FAILURES", "failures", self.DANGER),
            ("GENERATED ARTIFACTS", "artifacts", self.TEXT),
        )
        for label, key, color in cards:
            card = tk.Frame(dashboard, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1, padx=12, pady=9)
            tk.Label(card, text=label, bg=self.SURFACE, fg=self.MUTED, font=("Segoe UI", 8, "bold"), anchor="w", justify="left", wraplength=180).pack(anchor="w", fill="x")
            tk.Label(card, textvariable=self.dashboard_vars[key], bg=self.SURFACE, fg=color, font=("Segoe UI", 15, "bold"), anchor="w").pack(anchor="w", pady=(3, 0))
            self.dashboard_cards.append(card)
        self.dashboard_refresh = ttk.Button(dashboard, text="Refresh dashboard", style="Quiet.TButton", command=self._refresh_dashboard)
        self.dashboard_refresh.grid(sticky="e", padx=4, pady=(2, 0))
        self._layout_dashboard(self.winfo_width())
        self.after(450, self._refresh_dashboard)

    def _layout_dashboard(self, width: int) -> None:
        """Reflow dashboard cards without clipping labels or hiding the primary task."""
        if not getattr(self, "dashboard_cards", None):
            return
        columns = 3 if width >= 1080 else 2 if width >= 790 else 1
        for column in range(3):
            self.center.columnconfigure(column, weight=0)
        dashboard = self.dashboard_cards[0].master
        for column in range(columns):
            dashboard.columnconfigure(column, weight=1)
        for card in self.dashboard_cards:
            card.grid_remove()
        for index, card in enumerate(self.dashboard_cards):
            card.grid(row=index // columns, column=index % columns, columnspan=1, sticky="ew", padx=4, pady=4)
        refresh_row = (len(self.dashboard_cards) + columns - 1) // columns
        self.dashboard_refresh.grid(row=refresh_row, column=0, columnspan=columns, sticky="e", padx=4, pady=(2, 0))

    def _refresh_dashboard(self) -> None:
        """Refresh dashboard cards without blocking the Tkinter event loop."""
        def worker() -> None:
            results: dict[str, object] = {}
            for key, path in (("health", "/api/v1/health"), ("state", "/api/v1/state"), ("providers", "/api/v1/providers"), ("artifacts", "/api/v1/artifacts")):
                try:
                    request = urllib.request.Request(self.base_url + path, headers={"Authorization": f"Bearer {self.token}"})
                    with urllib.request.urlopen(request, timeout=5) as response:
                        results[key] = json.loads(response.read().decode())
                except Exception:
                    results[key] = None
            self.after(0, lambda: self._update_dashboard(results))
        threading.Thread(target=worker, daemon=True).start()

    def _update_dashboard(self, results: dict[str, object]) -> None:
        """Render only bounded aggregate values; never display raw errors or payloads."""
        health = results.get("health") if isinstance(results.get("health"), dict) else {}
        state = results.get("state") if isinstance(results.get("state"), dict) else {}
        providers = results.get("providers") if isinstance(results.get("providers"), dict) else {}
        artifacts = results.get("artifacts") if isinstance(results.get("artifacts"), dict) else {}
        tasks = state.get("tasks") or state.get("active_tasks") or []
        runs = state.get("runs") or state.get("recent_runs") or []
        failures = state.get("failures") or state.get("errors") or []
        provider_items = providers.get("providers") or []
        artifact_items = artifacts.get("artifacts") or []
        self.dashboard_vars["active"].set(str(len(tasks)) if isinstance(tasks, list) else "—")
        self.dashboard_vars["runs"].set(str(len(runs)) if isinstance(runs, list) else "—")
        self.dashboard_vars["models"].set(str(len(provider_items)) if isinstance(provider_items, list) else "—")
        self.dashboard_vars["health"].set("ONLINE" if health.get("status") == "ok" else "CHECK")
        self.dashboard_vars["failures"].set(str(len(failures)) if isinstance(failures, list) else "—")
        self.dashboard_vars["artifacts"].set(str(len(artifact_items)) if isinstance(artifact_items, list) else "—")

    def _build_context(self) -> None:
        self.context = tk.Frame(self.workspace, bg=self.SURFACE, highlightbackground=self.BORDER, highlightthickness=1)
        self.context.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        self.context.rowconfigure(1, weight=1)
        self.context.columnconfigure(0, weight=1)
        tabs = tk.Frame(self.context, bg=self.SURFACE)
        tabs.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        for label, panel in (("Preview", "preview"), ("Files", "files"), ("Activity", "activity"), ("Details", "details")):
            ttk.Button(tabs, text=label, style="Tab.TButton", command=lambda value=panel: self._show_context(value)).pack(side="left")
        self.context_body = tk.Frame(self.context, bg=self.SURFACE)
        self.context_body.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        self.context_body.rowconfigure(0, weight=1)
        self.context_body.columnconfigure(0, weight=1)
        self.context_text = scrolledtext.ScrolledText(self.context_body, wrap="word", state="disabled", bg=self.SURFACE, fg=self.TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 9), padx=2, pady=4)
        self.context_text.grid(row=0, column=0, sticky="nsew")
        self._show_context("preview")

    def open_provider_setup(self) -> None:
        """Open the guided local/cloud provider setup and safe health-check window."""
        window = tk.Toplevel(self)
        window.title("Orville — Provider Setup")
        window.geometry("900x650")
        window.minsize(760, 520)
        window.configure(bg=self.BG)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)
        ttk.Label(window, text="Provider setup", style="Title.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))
        ttk.Label(window, text="Configure a user-supplied endpoint or API key. Secrets are sent only to the local Orville API and are never displayed.", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(42, 10))

        body = ttk.Frame(window, style="Surface.TFrame", padding=14)
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 14))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(8, weight=1)
        provider_type = tk.StringVar(value="ollama")
        provider_id = tk.StringVar(value="ollama-local")
        model = tk.StringVar(value="llama3.2")
        base_url = tk.StringVar(value="http://127.0.0.1:11434")
        api_key = tk.StringVar()
        timeout = tk.StringVar(value="60")
        capabilities = tk.StringVar(value="text,code")
        status = scrolledtext.ScrolledText(body, height=10, wrap="word", state="disabled", bg=self.SURFACE, fg=self.TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 9))
        advanced_widgets: list[tk.Widget] = []

        def row(label: str, variable: tk.StringVar, number: int, show: str | None = None, advanced: bool = False) -> None:
            label_widget = ttk.Label(body, text=label, background=self.SURFACE, foreground=self.MUTED)
            label_widget.grid(row=number, column=0, sticky="w", padx=(0, 10), pady=5)
            entry_widget = ttk.Entry(body, textvariable=variable, show=show or "", width=58)
            entry_widget.grid(row=number, column=1, sticky="ew", pady=5)
            if advanced:
                advanced_widgets.extend((label_widget, entry_widget))

        ttk.Label(body, text="Provider type", background=self.SURFACE, foreground=self.MUTED).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        provider_combo = ttk.Combobox(body, textvariable=provider_type, values=("ollama", "gemini", "openai_compatible", "anthropic"), state="readonly", width=55)
        provider_combo.grid(row=0, column=1, sticky="ew", pady=5)
        row("Provider ID", provider_id, 1, advanced=True)
        row("Model name", model, 2)
        row("Base URL", base_url, 3, advanced=True)
        row("API key (optional)", api_key, 4, show="•", advanced=True)
        row("Timeout seconds", timeout, 5, advanced=True)
        row("Capabilities (comma-separated)", capabilities, 6, advanced=True)
        privacy_label = ttk.Label(body, text="Privacy", background=self.SURFACE, foreground=self.MUTED)
        privacy_label.grid(row=7, column=0, sticky="w", padx=(0, 10), pady=5)
        privacy = tk.StringVar(value="cloud_approved")
        privacy_combo = ttk.Combobox(body, textvariable=privacy, values=("local_only", "cloud_approved", "restricted"), state="readonly", width=55)
        privacy_combo.grid(row=7, column=1, sticky="ew", pady=5)
        advanced_widgets.extend((privacy_label, privacy_combo))
        advanced_visible = tk.BooleanVar(value=False)

        def toggle_advanced() -> None:
            if advanced_visible.get():
                for widget in advanced_widgets:
                    widget.grid()
                disclosure.configure(text="Hide advanced options")
            else:
                for widget in advanced_widgets:
                    widget.grid_remove()
                disclosure.configure(text="Show advanced options")

        disclosure = ttk.Checkbutton(body, text="Show advanced options", variable=advanced_visible, command=toggle_advanced)
        disclosure.grid(row=8, column=0, columnspan=2, sticky="w", pady=(6, 2))
        status.grid(row=9, column=0, columnspan=2, sticky="nsew", pady=(12, 8))

        def show(result: object) -> None:
            status.configure(state="normal")
            status.delete("1.0", "end")
            status.insert("1.0", json.dumps(safe_display_value(result), indent=2, ensure_ascii=False))
            status.configure(state="disabled")

        def apply_defaults(_event: object = None) -> None:
            selected = provider_type.get()
            if selected == "ollama":
                provider_id.set("ollama-local"); base_url.set("http://127.0.0.1:11434"); model.set("llama3.2"); api_key.set("")
            elif selected == "gemini":
                provider_id.set("gemini"); base_url.set("https://generativelanguage.googleapis.com"); model.set("gemini-2.5-flash")
            elif selected == "anthropic":
                provider_id.set("anthropic"); base_url.set("https://api.anthropic.com"); model.set("claude-3-5-sonnet-latest")
            else:
                provider_id.set("openai-compatible"); base_url.set("http://127.0.0.1:8000/v1"); model.set("local-model")

        provider_combo.bind("<<ComboboxSelected>>", apply_defaults)

        def add_provider() -> None:
            try:
                timeout_value = float(timeout.get())
                if timeout_value <= 0:
                    raise ValueError("timeout must be positive")
            except ValueError as exc:
                show({"error": str(exc)})
                return
            payload = {"provider_id": provider_id.get().strip(), "provider_type": provider_type.get().strip(), "model": model.get().strip(), "base_url": base_url.get().strip(), "api_key": api_key.get() or None, "timeout_seconds": timeout_value, "capabilities": [item.strip() for item in capabilities.get().split(",") if item.strip()], "headers": {}}
            self._manager_request("/api/v1/providers", "POST", payload, show)
            api_key.set("")

        def refresh() -> None:
            self._manager_request("/api/v1/providers", "GET", None, show)

        def health() -> None:
            self._manager_request("/api/v1/providers/health", "GET", None, show)

        def discover() -> None:
            provider = quote(provider_id.get().strip(), safe="")
            self._manager_request(f"/api/v1/providers/{provider}/models", "GET", None, show)

        def save_policy() -> None:
            payload = {"privacy_class": privacy.get(), "allowed_provider_ids": [provider_id.get().strip()] if provider_id.get().strip() else [], "local_only": privacy.get() in {"local_only", "restricted"}, "allow_fallback": True}
            self._manager_request("/api/v1/routing/privacy", "POST", payload, show)

        def export_redacted() -> None:
            destination = filedialog.asksaveasfilename(title="Save redacted provider configuration", defaultextension=".json", filetypes=(("JSON files", "*.json"), ("All files", "*.*")), parent=window)
            if not destination:
                return
            def save_result(result: object) -> None:
                try:
                    Path(destination).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    show({"status": "exported", "path": destination, "secrets_included": result.get("secrets_included") if isinstance(result, dict) else None})
                except OSError as exc:
                    show({"error": f"export failed: {exc}"})
            self._manager_request("/api/v1/config/export/redacted", "GET", None, save_result)

        controls = ttk.Frame(body, style="Surface.TFrame")
        controls.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ttk.Button(controls, text="Save provider", style="Primary.TButton", command=add_provider).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Refresh providers", style="Secondary.TButton", command=refresh).pack(side="left", padx=3)
        ttk.Button(controls, text="Test provider health", style="Secondary.TButton", command=health).pack(side="left", padx=3)
        ttk.Button(controls, text="Discover models", style="Secondary.TButton", command=discover).pack(side="left", padx=3)
        ttk.Button(controls, text="Save privacy policy", style="Secondary.TButton", command=save_policy).pack(side="left", padx=3)
        ttk.Button(controls, text="Export redacted config", style="Secondary.TButton", command=export_redacted).pack(side="left", padx=3)
        ttk.Label(body, text="Privacy policy is persisted locally; it does not authorize remote transmission by itself. Advanced options stay hidden until requested.", background=self.SURFACE, foreground=self.MUTED, font=("Segoe UI", 8)).grid(row=11, column=0, columnspan=2, sticky="w", pady=(10, 0))
        toggle_advanced()
        refresh()

    def import_local_model(self) -> None:
        source = filedialog.askopenfilename(title="Select a model file")
        if not source:
            source = filedialog.askdirectory(title="Select a model directory")
        if not source:
            return
        storage_root = filedialog.askdirectory(title="Choose model storage location (Cancel keeps a reference)")
        model_id = Path(source).stem.replace(" ", "-")
        payload = {"source": source, "model_id": model_id, "storage_root": storage_root or None, "storage_mode": "copy" if storage_root else "reference", "deduplicate": True, "approved": True}
        self._request("/api/v1/models/local/import", method="POST", payload=payload)

    def open_model_manager(self) -> None:
        window = tk.Toplevel(self)
        window.title("Orville — Model Manager")
        window.geometry("980x620")
        window.minsize(760, 460)
        window.configure(bg=self.BG)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)
        ttk.Label(window, text="Model manager", style="Title.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))
        ttk.Label(window, text="Manage cloud providers, endpoint models, Ollama servers, and imported local files without exposing secrets.", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(42, 10))
        body = ttk.Frame(window, style="Surface.TFrame", padding=12)
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 14))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        columns = ("model_id", "status", "runtime", "capabilities", "license", "storage", "attestation")
        table = ttk.Treeview(body, columns=columns, show="headings", selectmode="browse")
        headings = {"model_id": "Model", "status": "Status", "runtime": "Runtime", "capabilities": "Capabilities", "license": "License", "storage": "Storage", "attestation": "Attestation"}
        widths = {"model_id": 170, "status": 80, "runtime": 110, "capabilities": 190, "license": 120, "storage": 90, "attestation": 110}
        for column in columns:
            table.heading(column, text=headings[column])
            table.column(column, width=widths[column], anchor="w")
        table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        table.configure(yscrollcommand=scrollbar.set)
        details = scrolledtext.ScrolledText(body, height=8, wrap="word", state="disabled", bg=self.SURFACE, fg=self.TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 9))
        details.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        controls = ttk.Frame(body, style="Surface.TFrame")
        controls.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        runtime = tk.StringVar(value="ollama")
        endpoint = tk.StringVar()
        ttk.Label(controls, text="Runtime", background=self.SURFACE, foreground=self.MUTED).pack(side="left", padx=(0, 5))
        ttk.Combobox(controls, textvariable=runtime, values=("ollama", "llama_cpp", "transformers", "openai_compatible_local"), state="readonly", width=22).pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Endpoint", background=self.SURFACE, foreground=self.MUTED).pack(side="left", padx=(0, 5))
        ttk.Entry(controls, textvariable=endpoint, width=30).pack(side="left", padx=(0, 8))
        license_accept = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls, text="Accept license restrictions", variable=license_accept).pack(side="left", padx=(0, 8))
        attestation_policy = tk.StringVar(value="optional")
        ttk.Label(controls, text="Attestation", background=self.SURFACE, foreground=self.MUTED).pack(side="left", padx=(0, 5))
        ttk.Combobox(controls, textvariable=attestation_policy, values=("off", "optional", "required", "required_tuf"), state="readonly", width=14).pack(side="left", padx=(0, 8))

        def selected_id() -> str | None:
            selection = table.selection()
            return str(table.item(selection[0], "values")[0]) if selection else None

        def render_details(_event: object = None) -> None:
            model_id = selected_id()
            if not model_id:
                return
            self._manager_request("/api/v1/models/local", "GET", None, lambda result: self._manager_show_selected(result, model_id, details, runtime, endpoint))

        table.bind("<<TreeviewSelect>>", render_details)

        def refresh() -> None:
            self._manager_request("/api/v1/models/local", "GET", None, lambda result: self._manager_fill_table(result, table))

        def validate() -> None:
            model_id = selected_id()
            if model_id:
                self._manager_request(f"/api/v1/models/local/{quote(model_id, safe='')}/validate?runtime={quote(runtime.get(), safe='')}&attestation_policy={quote(attestation_policy.get(), safe='')}", "GET", None, lambda result: self._manager_show_result(result, details))

        def activate() -> None:
            model_id = selected_id()
            if model_id:
                self._manager_request(f"/api/v1/models/local/{quote(model_id, safe='')}/activate", "POST", {"runtime": runtime.get(), "endpoint": endpoint.get() or None, "attestation_policy": attestation_policy.get(), "accept_license_restrictions": license_accept.get(), "approved": True}, lambda result: (self._manager_show_result(result, details), refresh()))

        def deactivate() -> None:
            model_id = selected_id()
            if model_id and messagebox.askyesno("Deactivate model", f"Deactivate {model_id}? The model files will remain untouched.", parent=window):
                self._manager_request(f"/api/v1/models/local/{quote(model_id, safe='')}/deactivate", "POST", {"approved": True}, lambda result: (self._manager_show_result(result, details), refresh()))

        def remove() -> None:
            model_id = selected_id()
            if model_id and messagebox.askyesno("Remove registration", f"Remove the catalog entry for {model_id}? No model files will be deleted.", parent=window):
                self._manager_request(f"/api/v1/models/local/{quote(model_id, safe='')}", "DELETE", {"approved": True}, lambda result: (self._manager_show_result(result, details), refresh()))

        for label, command in (("Refresh", refresh), ("Validate", validate), ("Activate", activate), ("Deactivate", deactivate), ("Remove registration", remove)):
            ttk.Button(controls, text=label, style="Secondary.TButton", command=command).pack(side="left", padx=3)
        ttk.Button(controls, text="Provider setup", style="Secondary.TButton", command=self.open_provider_setup).pack(side="left", padx=3)
        ttk.Button(controls, text="Import local model", style="Secondary.TButton", command=self.import_local_model).pack(side="left", padx=3)
        refresh()

    def _manager_request(self, path: str, method: str, payload: dict | None, callback) -> None:
        def worker() -> None:
            data = json.dumps(payload).encode() if payload is not None else None
            request = urllib.request.Request(self.base_url + path, data=data, method=method, headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(request, timeout=8) as response:
                    result = json.loads(response.read().decode())
                self.after(0, lambda: callback(result))
            except Exception:
                self.after(0, lambda: callback({"error": "The local operation could not be completed."}))
        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _manager_fill_table(result: object, table: ttk.Treeview) -> None:
        for item in table.get_children():
            table.delete(item)
        for model in (result.get("models", []) if isinstance(result, dict) else []):
            evidence = model.get("activation_evidence") or {}
            attestation_status = evidence.get("verification_status") or (model.get("attestation") and "present") or "unverified"
            table.insert("", "end", values=(model.get("model_id"), model.get("status"), model.get("runtime") or "—", ", ".join(model.get("capabilities") or []) or "—", model.get("license") or "—", model.get("storage_mode") or "reference", attestation_status))

    def _manager_show_selected(self, result: object, model_id: str, details: tk.Text, runtime: tk.StringVar, endpoint: tk.StringVar) -> None:
        model = next((item for item in result.get("models", []) if item.get("model_id") == model_id), None) if isinstance(result, dict) else None
        if not model:
            return
        runtime.set(model.get("runtime") or "ollama")
        endpoint.set("Configured endpoint (hidden)")
        self._manager_show_result({"model": model}, details)

    @staticmethod
    def _manager_show_result(result: object, details: tk.Text) -> None:
        text = json.dumps(safe_display_value(result), indent=2, ensure_ascii=False)
        details.configure(state="normal")
        details.delete("1.0", "end")
        details.insert("1.0", text)
        details.configure(state="disabled")

    def _show_context(self, panel: str) -> None:
        messages = {
            "preview": "Preview\n\nGenerated artifacts and task output will appear here when the existing workflow returns them.",
            "files": "Files\n\nNo artifact list loaded. Use “List Artifacts” to query the existing API.",
            "activity": "Activity\n\nTask events and API responses will be summarized here.",
            "details": "Details\n\nEndpoint\nConfigured runtime endpoint (hidden)\n\nAuthentication\nConfigured through protected runtime state",
        }
        self.context_text.configure(state="normal")
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", messages[panel])
        self.context_text.configure(state="disabled")

    def _on_resize(self, _event: tk.Event) -> None:
        width = self.winfo_width()
        if width < 980 and self.context_visible:
            self.context_visible = False
            self.context.grid_remove()
        elif width >= 980 and not self.context_visible:
            self.context_visible = True
            self.context.grid()
        if width < 790 and self.sidebar_visible:
            self.sidebar_visible = False
            self.sidebar.grid_remove()
        elif width >= 790 and not self.sidebar_visible:
            self.sidebar_visible = True
            self.sidebar.grid()
        self._layout_dashboard(width)

    def toggle_sidebar(self) -> None:
        self.sidebar_visible = not self.sidebar_visible
        (self.sidebar.grid if self.sidebar_visible else self.sidebar.grid_remove)()

    def _focus_composer(self) -> None:
        self.objective.focus_set()
        self._clear_placeholder()

    def _clear_placeholder(self, _event: tk.Event | None = None) -> None:
        if self.objective.get("1.0", "end").strip() == self._placeholder:
            self.objective.delete("1.0", "end")
            self.objective.configure(fg=self.TEXT)

    def _restore_placeholder(self, _event: tk.Event | None = None) -> None:
        if not self.objective.get("1.0", "end").strip():
            self.objective.insert("1.0", self._placeholder)
            self.objective.configure(fg=self.MUTED)

    def _write(self, value: object, tag: str | None = None) -> None:
        text = json.dumps(safe_display_value(value), indent=2, ensure_ascii=False) if not isinstance(value, str) else _redact_display_text(value)
        self.output.configure(state="normal")
        if tag:
            self.output.insert("end", text + "\n\n", tag)
        else:
            self.output.insert("end", text + "\n\n")
        self.output.see("end")
        self.output.configure(state="disabled")
        self.context_text.configure(state="normal")
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", text)
        self.context_text.configure(state="disabled")

    def _request(self, path: str, method: str = "GET", payload: dict | None = None) -> None:
        self.task_status.configure(text="WORKING", bg="#f4edff", fg=self.ACCENT)

        def worker() -> None:
            data = json.dumps(payload).encode() if payload is not None else None
            request = urllib.request.Request(self.base_url + path, data=data, method=method, headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(request, timeout=8) as response:
                    result = json.loads(response.read().decode())
                    self.after(0, lambda: self._request_succeeded(result))
            except urllib.error.HTTPError as exc:
                exc.read()
                self.after(0, lambda: self._request_failed(f"The objective request could not be completed (HTTP {exc.code})."))
            except Exception:
                self.after(0, lambda: self._request_failed("The objective request could not be completed. Check that the local Orville service is running, then try again."))

        threading.Thread(target=worker, daemon=True).start()

    def _request_succeeded(self, result: object) -> None:
        self.task_status.configure(text="COMPLETE", bg="#e9f5ee", fg=self.SUCCESS)
        self._write(result)

    def _request_failed(self, detail: str) -> None:
        self.task_status.configure(text="ATTENTION — action needs review", bg="#fff1f0", fg=self.DANGER)
        self._write(f"Unable to complete this action. {detail}\n\nRecovery: check the local service, review the objective, and try again.", "meta")
        self.objective.focus_set()

    def _wait_for_api(self) -> None:
        try:
            request = urllib.request.Request(self.base_url + "/api/v1/health", headers={"Authorization": f"Bearer {self.token}"})
            with urllib.request.urlopen(request, timeout=2):
                self.connection_badge.configure(text="●  ONLINE", fg=self.SUCCESS)
                self._write("Orville API is running.", "meta")
                return
        except Exception:
            self.after(500, self._wait_for_api)

    def health(self) -> None:
        self._request("/api/v1/health")

    def state(self) -> None:
        self._request("/api/v1/state")

    def artifacts(self) -> None:
        self._request("/api/v1/artifacts")

    def create_objective(self) -> None:
        text = self.objective.get("1.0", "end").strip()
        if not text or text == self._placeholder:
            messagebox.showwarning("Objective required", "Enter an objective before creating it.")
            return
        self._write("Objective submitted", "user")
        method, path, payload = build_engine_action_request("create_run")
        self._request(path, method, {"objective": text, **(payload or {})})
        self.objective.delete("1.0", "end")
        self._restore_placeholder()


def main() -> None:
    load_env()
    threading.Thread(target=start_api, daemon=True).start()
    app = OrvilleWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
