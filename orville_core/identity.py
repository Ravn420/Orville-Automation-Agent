"""Project membership, role authorization, and durable identity contracts."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ProjectRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


_ROLE_ACTIONS: dict[ProjectRole, frozenset[str]] = {
    ProjectRole.OWNER: frozenset({"read", "plan", "execute", "approve", "publish", "manage_members", "manage_integrations"}),
    ProjectRole.ADMIN: frozenset({"read", "plan", "execute", "approve", "publish", "manage_members", "manage_integrations"}),
    ProjectRole.DEVELOPER: frozenset({"read", "plan", "execute"}),
    ProjectRole.REVIEWER: frozenset({"read", "plan", "approve"}),
    ProjectRole.VIEWER: frozenset({"read"}),
}


@dataclass(frozen=True)
class ProjectMember:
    project_id: str
    actor_id: str
    role: ProjectRole
    status: str = "active"
    invited_by: str | None = None


class MembershipDirectory:
    def __init__(self) -> None:
        self._members: dict[tuple[str, str], ProjectMember] = {}

    def add(self, project_id: str, actor_id: str, role: ProjectRole, *, invited_by: str | None = None) -> ProjectMember:
        if not project_id or not actor_id:
            raise ValueError("project_id and actor_id are required")
        member = ProjectMember(project_id, actor_id, role, "active", invited_by)
        self._members[(project_id, actor_id)] = member
        return member

    def get(self, project_id: str, actor_id: str) -> ProjectMember:
        try:
            member = self._members[(project_id, actor_id)]
        except KeyError as exc:
            raise PermissionError("actor is not a project member") from exc
        if member.status != "active":
            raise PermissionError("project membership is not active")
        return member

    def authorize(self, project_id: str, actor_id: str, action: str) -> ProjectMember:
        member = self.get(project_id, actor_id)
        if action not in _ROLE_ACTIONS[member.role]:
            raise PermissionError(f"role {member.role.value} cannot perform action: {action}")
        return member

    def list_members(self, project_id: str) -> tuple[ProjectMember, ...]:
        return tuple(member for (current_project, _), member in self._members.items() if current_project == project_id)


class SQLiteMembershipDirectory:
    """Durable project membership store with fail-closed authorization."""

    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = self._connect()
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS project_members (
                project_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                invited_by TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(project_id, actor_id)
            )""")
        finally:
            db.close()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def add(self, project_id: str, actor_id: str, role: ProjectRole, *, invited_by: str | None = None, status: str = "active") -> ProjectMember:
        if not project_id or not actor_id:
            raise ValueError("project_id and actor_id are required")
        member = ProjectMember(project_id, actor_id, role, status, invited_by)
        db = self._connect()
        try:
            db.execute("INSERT INTO project_members(project_id, actor_id, role, status, invited_by) VALUES (?, ?, ?, ?, ?) ON CONFLICT(project_id, actor_id) DO UPDATE SET role=excluded.role, status=excluded.status, invited_by=excluded.invited_by", (project_id, actor_id, role.value, status, invited_by))
        finally:
            db.close()
        return member

    def revoke(self, project_id: str, actor_id: str) -> None:
        db = self._connect()
        try:
            db.execute("UPDATE project_members SET status = 'revoked' WHERE project_id = ? AND actor_id = ?", (project_id, actor_id))
        finally:
            db.close()

    def get(self, project_id: str, actor_id: str) -> ProjectMember:
        db = self._connect()
        try:
            row = db.execute("SELECT project_id, actor_id, role, status, invited_by FROM project_members WHERE project_id = ? AND actor_id = ?", (project_id, actor_id)).fetchone()
        finally:
            db.close()
        if row is None:
            raise PermissionError("actor is not a project member")
        member = ProjectMember(row["project_id"], row["actor_id"], ProjectRole(row["role"]), row["status"], row["invited_by"])
        if member.status != "active":
            raise PermissionError("project membership is not active")
        return member

    def authorize(self, project_id: str, actor_id: str, action: str) -> ProjectMember:
        member = self.get(project_id, actor_id)
        if action not in _ROLE_ACTIONS[member.role]:
            raise PermissionError(f"role {member.role.value} cannot perform action: {action}")
        return member

    def list_members(self, project_id: str) -> tuple[ProjectMember, ...]:
        db = self._connect()
        try:
            rows = db.execute("SELECT project_id, actor_id, role, status, invited_by FROM project_members WHERE project_id = ? ORDER BY actor_id", (project_id,)).fetchall()
        finally:
            db.close()
        return tuple(ProjectMember(row["project_id"], row["actor_id"], ProjectRole(row["role"]), row["status"], row["invited_by"]) for row in rows)
