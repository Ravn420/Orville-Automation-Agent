"""Validated enterprise deployment-readiness contracts for M14.1.

This module records environment ownership, tenant boundaries, data classes,
recovery objectives, escalation paths, and rollback authority without storing
credentials or provider secrets. It is configuration-only and performs no
external provisioning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


class EnterpriseReadinessError(ValueError):
    """Raised when an enterprise readiness declaration is unsafe or incomplete."""


@dataclass(frozen=True)
class RecoveryObjectives:
    """Bounded recovery targets expressed in seconds."""

    rto_seconds: int
    rpo_seconds: int

    def validate(self) -> None:
        if not 1 <= self.rto_seconds <= 30 * 24 * 3600:
            raise EnterpriseReadinessError("rto_seconds must be between 1 second and 30 days")
        if not 0 <= self.rpo_seconds <= 30 * 24 * 3600:
            raise EnterpriseReadinessError("rpo_seconds must be between 0 seconds and 30 days")
        if self.rpo_seconds > self.rto_seconds:
            raise EnterpriseReadinessError("rpo_seconds cannot exceed rto_seconds")


@dataclass(frozen=True)
class ResponsibilityMatrix:
    """Named operational owners for critical enterprise actions."""

    security_owner: str
    platform_owner: str
    deployment_owner: str
    data_owner: str
    rollback_authority: str
    escalation_channel: str

    def validate(self) -> None:
        values = (self.security_owner, self.platform_owner, self.deployment_owner, self.data_owner, self.rollback_authority, self.escalation_channel)
        if any(not value.strip() for value in values):
            raise EnterpriseReadinessError("all responsibility and escalation fields are required")


@dataclass(frozen=True)
class EnterpriseEnvironment:
    """Tenant and platform declaration required before production operations."""

    environment_id: str
    tenant_id: str
    region: str
    platform: str
    data_classes: tuple[str, ...] = ()
    allowed_networks: tuple[str, ...] = ()
    objectives: RecoveryObjectives = field(default_factory=lambda: RecoveryObjectives(3600, 900))
    responsibilities: ResponsibilityMatrix = field(default_factory=lambda: ResponsibilityMatrix("", "", "", "", "", ""))
    production: bool = False

    def validate(self) -> None:
        if not self.environment_id.strip() or not self.tenant_id.strip() or not self.region.strip() or not self.platform.strip():
            raise EnterpriseReadinessError("environment_id, tenant_id, region, and platform are required")
        if any(char in self.tenant_id for char in "\\/\n\r\t"):
            raise EnterpriseReadinessError("tenant_id contains unsafe path/control characters")
        if not self.data_classes:
            raise EnterpriseReadinessError("at least one data class is required")
        if any(not item.strip() for item in self.data_classes):
            raise EnterpriseReadinessError("data_classes cannot contain empty values")
        self.objectives.validate()
        self.responsibilities.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": "orville.enterprise.environment",
            "environment_id": self.environment_id,
            "tenant_id": self.tenant_id,
            "region": self.region,
            "platform": self.platform,
            "data_classes": list(self.data_classes),
            "allowed_networks": list(self.allowed_networks),
            "recovery": {"rto_seconds": self.objectives.rto_seconds, "rpo_seconds": self.objectives.rpo_seconds},
            "responsibilities": {
                "security_owner": self.responsibilities.security_owner,
                "platform_owner": self.responsibilities.platform_owner,
                "deployment_owner": self.responsibilities.deployment_owner,
                "data_owner": self.responsibilities.data_owner,
                "rollback_authority": self.responsibilities.rollback_authority,
                "escalation_channel": self.responsibilities.escalation_channel,
            },
            "production": self.production,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EnterpriseEnvironment":
        try:
            recovery = data.get("recovery", {})
            responsibility = data.get("responsibilities", {})
            result = cls(
                environment_id=str(data.get("environment_id", "")),
                tenant_id=str(data.get("tenant_id", "")),
                region=str(data.get("region", "")),
                platform=str(data.get("platform", "")),
                data_classes=tuple(str(item) for item in data.get("data_classes", [])),
                allowed_networks=tuple(str(item) for item in data.get("allowed_networks", [])),
                objectives=RecoveryObjectives(int(recovery.get("rto_seconds", 0)), int(recovery.get("rpo_seconds", -1))),
                responsibilities=ResponsibilityMatrix(
                    str(responsibility.get("security_owner", "")), str(responsibility.get("platform_owner", "")),
                    str(responsibility.get("deployment_owner", "")), str(responsibility.get("data_owner", "")),
                    str(responsibility.get("rollback_authority", "")), str(responsibility.get("escalation_channel", "")),
                ),
                production=bool(data.get("production", False)),
            )
        except (TypeError, ValueError) as exc:
            raise EnterpriseReadinessError(f"invalid enterprise environment shape: {exc}") from exc
        result.validate()
        return result
