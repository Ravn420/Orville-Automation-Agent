"""Project workflow contracts: state, intake, agents, handoffs, and verification."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from .models import TaskGraph, TaskNode


def _now() -> str:
    return datetime.now(UTC).isoformat()


class AtomicJsonFile:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, payload: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        with temporary.open("w+b") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(self.path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))


@dataclass
class ProjectState:
    project_id: str
    objective: str
    scope: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    active_phase: str = "initialized"
    blockers: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=_now)

    def save(self, path: str | Path) -> None:
        AtomicJsonFile(path).save(asdict(self))

    @classmethod
    def load(cls, path: str | Path) -> "ProjectState":
        return cls(**AtomicJsonFile(path).load())


@dataclass(frozen=True)
class SoftwareObjective:
    objective: str
    deliverables: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    target_environment: str = "unspecified"
    risk_level: str = "normal"
    acceptance_criteria: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective must not be empty")
        if self.risk_level not in {"low", "normal", "high", "critical"}:
            raise ValueError("risk_level must be low, normal, high, or critical")


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    role: str
    capabilities: tuple[str, ...]
    description: str = ""
    verifier: bool = False


@dataclass(frozen=True)
class AgentHandoff:
    handoff_id: str
    task_id: str
    from_agent: str
    to_agent: str
    objective: str
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_outputs: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationRecord:
    verification_id: str
    task_id: str
    verifier_agent: str
    passed: bool
    checks: tuple[dict[str, Any], ...] = ()
    defects: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    verified_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SENSITIVE_DECISION_DOMAINS: dict[str, tuple[str, ...]] = {
    "medical": ("medical", "symptom", "diagnos", "prescrib", "medication", "dosage", "treatment"),
    "legal": ("legal", "lawsuit", "litigation", "contract", "court", "attorney"),
    "tax": ("tax", "taxes", "tax return", "deduction", "irs"),
    "financial": ("financial", "invest", "investment", "loan", "mortgage", "stock", "portfolio", "bank"),
    "insurance": ("insurance", "policy claim", "coverage", "premium"),
    "real_estate": ("real estate", "property purchase", "home purchase", "rental agreement", "landlord"),
    "gambling": ("gambling", "bet", "betting", "casino", "wager", "odds"),
    "major_life_decision": ("divorce", "separation", "婚", "relocation", "move abroad", "major life", "end relationship"),
}

_SENSITIVE_ACTION_TERMS = ("diagnose", "prescribe", "file", "sign", "buy", "sell", "invest", "trade", "bet", "submit", "represent me", "decide for me")


def classify_sensitive_domains(text: str) -> tuple[str, ...]:
    """Return stable sensitive-decision domains detected in objective text."""
    normalized = text.lower()
    return tuple(name for name, terms in SENSITIVE_DECISION_DOMAINS.items() if any(term in normalized for term in terms))


def sensitive_domain_safety(text: str, *, risk_level: str = "normal") -> dict[str, Any]:
    """Build safe-handling metadata without providing domain advice or taking action."""
    domains = classify_sensitive_domains(text)
    action_requested = any(term in text.lower() for term in _SENSITIVE_ACTION_TERMS)
    return {
        "domains": list(domains),
        "detected": bool(domains),
        "informational_only": bool(domains),
        "professional_review_required": bool(domains),
        "action_confirmation_required": bool(domains and (action_requested or risk_level in {"high", "critical"})),
        "prohibited_behavior": ["diagnosis", "legal representation", "personalized financial instruction", "placing bets", "autonomous filing, signing, purchasing, or account changes"],
        "safe_resolution": "Provide general information, state uncertainty, recommend an appropriately qualified professional, and obtain explicit approval before any consequential action." if domains else "No sensitive decision domain detected.",
    }


class TaskIntake:
    """Normalize a user objective into a validated graph skeleton."""

    @staticmethod
    def classify(objective: str) -> str:
        text = objective.lower()
        categories = {
            "web_development": ("website", "web app", "frontend", "backend"),
            "coding": ("code", "software", "application", "program", "api", "task manager", "manager"),
            "automation": ("automate", "workflow", "schedule", "webhook"),
            "research": ("research", "investigate", "compare", "analyze"),
            "media_generation": ("image", "video", "audio", "music"),
            "document_production": ("report", "document", "presentation", "slides"),
            "deployment": ("deploy", "release", "production", "hosting"),
        }
        matches = [name for name, terms in categories.items() if any(term in text for term in terms)]
        return matches[0] if len(matches) == 1 else ("mixed" if matches else "general")

    @staticmethod
    def clarification_questions(objective: SoftwareObjective) -> list[str]:
        questions = []
        if not objective.deliverables:
            questions.append("What exact deliverables should be produced?")
        if not objective.acceptance_criteria:
            questions.append("How will the result be accepted or tested?")
        if objective.target_environment == "unspecified":
            questions.append("What runtime, operating system, or deployment environment is required?")
        return questions

    @classmethod
    def clarification_gate(cls, objective: SoftwareObjective) -> dict[str, Any]:
        """Return deterministic clarification requirements without performing actions.

        Missing planning details are warnings. Sensitive objectives, explicit
        contradictions, and high-risk requests are hard gates until a user or
        authorized project instruction resolves them.
        """
        text = objective.objective.lower()
        questions = cls.clarification_questions(objective)
        warnings = list(questions)
        hard_gates: list[str] = []
        safety = sensitive_domain_safety(objective.objective, risk_level=objective.risk_level)
        if safety["detected"]:
            warnings.append("Sensitive decision domain detected; keep output informational and recommend qualified professional review.")
            if safety["action_confirmation_required"]:
                hard_gates.append("Sensitive decision action requires explicit approval, professional review, and confirmation of the exact consequence.")
        sensitive_terms = ("post", "publish", "buy", "purchase", "pay", "delete", "destroy", "deploy", "send", "email", "sign in", "credential", "password", "api key")
        if any(term in text for term in sensitive_terms):
            hard_gates.append("Sensitive external, credential, financial, publication, deployment, or destructive action requires explicit approval.")
        if objective.risk_level in {"high", "critical"} and not objective.acceptance_criteria:
            hard_gates.append("High-risk objectives require acceptance criteria before execution.")
        contradiction_pairs = (("local only", "cloud"), ("offline", "internet"), ("do not modify", "modify"), ("no sign in", "sign in"))
        for left, right in contradiction_pairs:
            if left in text and right in text:
                hard_gates.append(f"Conflicting constraints detected: '{left}' and '{right}'.")
        return {"required": bool(hard_gates), "warnings": warnings, "hard_gates": hard_gates, "questions": questions, "safety": safety, "resolution": "Provide answers or explicit approval before executing gated actions." if hard_gates else "Proceed with recorded assumptions; clarification can be supplied before execution."}

    @classmethod
    def normalize(cls, payload: SoftwareObjective | dict[str, Any]) -> SoftwareObjective:
        if isinstance(payload, SoftwareObjective):
            return payload
        allowed = {field for field in SoftwareObjective.__dataclass_fields__}
        return SoftwareObjective(**{key: value for key, value in payload.items() if key in allowed})

    @classmethod
    def to_graph(cls, payload: SoftwareObjective | dict[str, Any]) -> TaskGraph:
        objective = cls.normalize(payload)
        task = TaskNode(
            task_id="intake.objective",
            title="Process software objective",
            handler="intake.objective",
            inputs={"objective": objective.objective, "deliverables": objective.deliverables, "constraints": objective.constraints, "acceptance_criteria": objective.acceptance_criteria},
        )
        task.inputs["classification"] = cls.classify(objective.objective)
        task.inputs["clarification_questions"] = cls.clarification_questions(objective)
        task.inputs["clarification_gate"] = cls.clarification_gate(objective)
        return TaskGraph(graph_id=f"objective-{hashlib.sha256(objective.objective.encode()).hexdigest()[:12]}", name="Normalized software objective", tasks=[task])


class AgentRegistry:
    def __init__(self, agents: list[AgentDefinition] | None = None) -> None:
        self._agents: dict[str, AgentDefinition] = {}
        for agent in agents or []:
            self.register(agent)

    def register(self, agent: AgentDefinition) -> None:
        if not agent.agent_id.strip():
            raise ValueError("agent_id must not be empty")
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> AgentDefinition:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"agent not registered: {agent_id}") from exc

    def select(self, capability: str, *, verifier: bool = False) -> AgentDefinition:
        for agent in self._agents.values():
            if agent.verifier == verifier and capability in agent.capabilities:
                return agent
        raise LookupError(f"no agent supports capability: {capability}")

    def list(self) -> tuple[AgentDefinition, ...]:
        return tuple(self._agents.values())


def default_agent_registry() -> AgentRegistry:
    return AgentRegistry([
        AgentDefinition("research", "Research Agent", ("research", "fact-checking", "api-docs")),
        AgentDefinition("code", "Code Synthesis Agent", ("coding", "refactoring", "testing")),
        AgentDefinition("ide", "IDE Agent", ("architecture", "repository-analysis", "integration")),
        AgentDefinition("prototype", "Prototype Agent", ("prototyping", "debugging", "smoke-testing")),
        AgentDefinition("automation", "Automation Agent", ("automation", "scheduling", "connectors")),
        AgentDefinition("orchestration", "Orchestration Agent", ("planning", "delegation", "integration")),
        AgentDefinition("verification", "Verification Agent", ("verification", "acceptance-testing", "security-testing"), verifier=True),
    ])
