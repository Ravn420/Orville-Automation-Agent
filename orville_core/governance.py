"""Security, evaluation, analytics, and recovery contracts for Orville."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class SecurityFinding:
    finding_id: str
    project_id: str
    rule: str
    severity: str
    message: str
    path: str | None = None
    status: str = "open"
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class Metric:
    metric_id: str
    project_id: str
    name: str
    value: float
    dimensions: dict[str, str] = field(default_factory=dict)
    recorded_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class EvaluationRun:
    evaluation_id: str
    project_id: str
    suite_name: str
    passed: bool
    score: float
    checks: tuple[dict[str, Any], ...] = ()
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class ReleaseRecord:
    release_id: str
    project_id: str
    revision_id: str
    environment: str
    approver: str
    validation_passed: bool
    security_passed: bool
    rollback_target: str | None
    status: str = "recorded"
    created_at: str = field(default_factory=_now)


class GovernanceStore:
    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = self._connect()
        try:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS security_findings (finding_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, rule TEXT NOT NULL, severity TEXT NOT NULL, message TEXT NOT NULL, path TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS metrics (metric_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, value REAL NOT NULL, dimensions TEXT NOT NULL, recorded_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS evaluation_runs (evaluation_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, suite_name TEXT NOT NULL, passed INTEGER NOT NULL, score REAL NOT NULL, checks TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS releases (release_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, revision_id TEXT NOT NULL, environment TEXT NOT NULL, approver TEXT NOT NULL, validation_passed INTEGER NOT NULL, security_passed INTEGER NOT NULL, rollback_target TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL);
            """)
        finally:
            db.close()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    @staticmethod
    def _id(prefix: str, *parts: str) -> str:
        return f"{prefix}-" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]

    def record_finding(self, project_id: str, rule: str, severity: str, message: str, path: str | None = None) -> SecurityFinding:
        finding = SecurityFinding(self._id("finding", project_id, rule, message, path or ""), project_id, rule, severity, message, path)
        db = self._connect()
        try:
            db.execute("INSERT OR REPLACE INTO security_findings VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tuple(finding.__dict__.values()))
        finally:
            db.close()
        return finding

    def record_metric(self, project_id: str, name: str, value: float, dimensions: dict[str, str] | None = None) -> Metric:
        metric = Metric(self._id("metric", project_id, name, _now()), project_id, name, float(value), dimensions or {})
        db = self._connect()
        try:
            db.execute("INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?)", (metric.metric_id, metric.project_id, metric.name, metric.value, json.dumps(metric.dimensions), metric.recorded_at))
        finally:
            db.close()
        return metric

    def run_evaluation(self, project_id: str, suite_name: str, checks: list[dict[str, Any]]) -> EvaluationRun:
        passed_checks = [check for check in checks if bool(check.get("passed"))]
        score = len(passed_checks) / len(checks) if checks else 1.0
        evaluation = EvaluationRun(self._id("evaluation", project_id, suite_name, _now()), project_id, suite_name, score == 1.0, score, tuple(checks))
        db = self._connect()
        try:
            db.execute("INSERT INTO evaluation_runs VALUES (?, ?, ?, ?, ?, ?, ?)", (evaluation.evaluation_id, evaluation.project_id, evaluation.suite_name, int(evaluation.passed), evaluation.score, json.dumps(list(evaluation.checks)), evaluation.created_at))
        finally:
            db.close()
        return evaluation

    def record_release(self, project_id: str, revision_id: str, environment: str, approver: str, validation_passed: bool, security_passed: bool, rollback_target: str | None) -> ReleaseRecord:
        if not validation_passed or not security_passed:
            raise PermissionError("release requires passing validation and security gates")
        release = ReleaseRecord(self._id("release", project_id, revision_id, environment), project_id, revision_id, environment, approver, validation_passed, security_passed, rollback_target)
        db = self._connect()
        try:
            db.execute("INSERT INTO releases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(release.__dict__.values()))
        finally:
            db.close()
        return release

    def list_findings(self, project_id: str) -> list[SecurityFinding]:
        db = self._connect()
        try:
            rows = db.execute("SELECT * FROM security_findings WHERE project_id = ? ORDER BY created_at DESC", (project_id,)).fetchall()
        finally:
            db.close()
        return [SecurityFinding(**dict(row)) for row in rows]
