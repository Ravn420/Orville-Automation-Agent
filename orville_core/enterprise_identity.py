"""Tenant-scoped enterprise identity and least-privilege authorization.

The module consumes claims from an already trusted identity gateway; it does
not implement OAuth, OIDC discovery, password handling, or token issuance.
Membership, revocation, and approval decisions are persisted locally with
fail-closed checks and secret-free audit metadata.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class EnterpriseAuthorizationError(PermissionError):
    """Raised when an identity cannot perform an action."""


@dataclass(frozen=True)
class IdentityClaims:
    actor_id: str
    tenant_id: str
    subject: str
    scopes: frozenset[str]
    issued_at: float
    expires_at: float
    session_id: str

    def validate(self, now: float | None = None) -> None:
        current = time.time() if now is None else now
        if not self.actor_id.strip() or not self.tenant_id.strip() or not self.subject.strip() or not self.session_id.strip():
            raise EnterpriseAuthorizationError("identity claims require actor, tenant, subject, and session identifiers")
        if any(char in self.tenant_id for char in "\\/\n\r\t"):
            raise EnterpriseAuthorizationError("tenant_id contains unsafe path/control characters")
        if self.expires_at <= self.issued_at or self.expires_at - self.issued_at > 24 * 3600:
            raise EnterpriseAuthorizationError("identity claim lifetime must be positive and at most 24 hours")
        if current < self.issued_at or current >= self.expires_at:
            raise EnterpriseAuthorizationError("identity claims are expired or not yet valid")


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    actor_id: str
    tenant_id: str
    action: str
    reason: str
    approval_reference: str | None = None


_ACTION_SCOPES: dict[str, frozenset[str]] = {
    "read": frozenset({"orville:read"}),
    "plan": frozenset({"orville:plan"}),
    "execute": frozenset({"orville:execute"}),
    "approve": frozenset({"orville:approve"}),
    "publish": frozenset({"orville:publish"}),
    "manage_members": frozenset({"orville:members:write"}),
    "manage_integrations": frozenset({"orville:integrations:write"}),
    "deploy_canary": frozenset({"orville:deploy"}),
    "manage_trust_roots": frozenset({"orville:trust-root:write"}),
}


class SQLiteEnterpriseAuthorizationStore:
    """Durable tenant membership, revocation, approvals, and audit decisions."""

    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tenant_members (
                    tenant_id TEXT NOT NULL, actor_id TEXT NOT NULL, scopes TEXT NOT NULL,
                    status TEXT NOT NULL, updated_at REAL NOT NULL,
                    PRIMARY KEY (tenant_id, actor_id)
                );
                CREATE TABLE IF NOT EXISTS identity_approvals (
                    approval_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, actor_id TEXT NOT NULL,
                    action TEXT NOT NULL, status TEXT NOT NULL, expires_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS identity_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL, action TEXT NOT NULL, outcome TEXT NOT NULL,
                    reason TEXT NOT NULL, created_at REAL NOT NULL
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level="IMMEDIATE")
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def grant(self, tenant_id: str, actor_id: str, scopes: Iterable[str]) -> None:
        normalized = sorted({scope.strip() for scope in scopes if scope.strip()})
        if not tenant_id.strip() or not actor_id.strip() or not normalized:
            raise ValueError("tenant_id, actor_id, and at least one scope are required")
        with self._connect() as db:
            db.execute("INSERT INTO tenant_members VALUES (?, ?, ?, 'active', ?) ON CONFLICT(tenant_id, actor_id) DO UPDATE SET scopes=excluded.scopes, status='active', updated_at=excluded.updated_at", (tenant_id, actor_id, " ".join(normalized), time.time()))

    def revoke(self, tenant_id: str, actor_id: str) -> None:
        with self._connect() as db:
            db.execute("UPDATE tenant_members SET status='revoked', updated_at=? WHERE tenant_id=? AND actor_id=?", (time.time(), tenant_id, actor_id))

    def approve(self, approval_id: str, tenant_id: str, actor_id: str, action: str, expires_at: float) -> None:
        if not approval_id.strip() or not action.strip() or expires_at <= time.time():
            raise ValueError("approval_id, action, and a future expiry are required")
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO identity_approvals VALUES (?, ?, ?, ?, 'approved', ?)", (approval_id, tenant_id, actor_id, action, expires_at))

    def authorize(self, claims: IdentityClaims, action: str, *, approval_reference: str | None = None, now: float | None = None) -> AuthorizationDecision:
        current = time.time() if now is None else now
        try:
            claims.validate(current)
            required = _ACTION_SCOPES.get(action)
            if required is None:
                raise EnterpriseAuthorizationError("action is not defined by the authorization policy")
            with self._connect() as db:
                member = db.execute("SELECT scopes, status FROM tenant_members WHERE tenant_id=? AND actor_id=?", (claims.tenant_id, claims.actor_id)).fetchone()
                if member is None or member["status"] != "active":
                    raise EnterpriseAuthorizationError("tenant membership is not active")
                member_scopes = set(str(member["scopes"]).split())
                if not required.issubset(member_scopes) or not required.issubset(claims.scopes):
                    raise EnterpriseAuthorizationError("least-privilege scope is missing")
                if action in {"approve", "publish", "deploy_canary", "manage_trust_roots"}:
                    if not approval_reference:
                        raise EnterpriseAuthorizationError("explicit approval reference is required")
                    approval = db.execute("SELECT status, expires_at, tenant_id, actor_id, action FROM identity_approvals WHERE approval_id=?", (approval_reference,)).fetchone()
                    if approval is None or approval["status"] != "approved" or float(approval["expires_at"]) <= current or approval["tenant_id"] != claims.tenant_id or approval["actor_id"] != claims.actor_id or approval["action"] != action:
                        raise EnterpriseAuthorizationError("approval is missing, expired, or mismatched")
            decision = AuthorizationDecision(True, claims.actor_id, claims.tenant_id, action, "authorized", approval_reference)
            self.audit(decision)
            return decision
        except EnterpriseAuthorizationError as exc:
            decision = AuthorizationDecision(False, claims.actor_id, claims.tenant_id, action, str(exc), approval_reference)
            self.audit(decision)
            raise

    def audit(self, decision: AuthorizationDecision) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO identity_audit(tenant_id, actor_id, action, outcome, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)", (decision.tenant_id, decision.actor_id, decision.action, "allowed" if decision.allowed else "denied", decision.reason, time.time()))

    def audit_events(self, tenant_id: str, actor_id: str | None = None) -> list[dict[str, object]]:
        with self._connect() as db:
            if actor_id:
                rows = db.execute("SELECT action, outcome, reason, created_at FROM identity_audit WHERE tenant_id=? AND actor_id=? ORDER BY id", (tenant_id, actor_id)).fetchall()
            else:
                rows = db.execute("SELECT action, outcome, reason, created_at FROM identity_audit WHERE tenant_id=? ORDER BY id", (tenant_id,)).fetchall()
        return [{"action": row[0], "outcome": row[1], "reason": row[2], "created_at": row[3]} for row in rows]
