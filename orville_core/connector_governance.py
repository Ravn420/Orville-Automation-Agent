"""Governance checks for connector configuration mutations.

Connector changes are rejected unless the caller identifies a concrete project
requirement. Sensitive account changes additionally require an explicit approval
reference; the reference is metadata only and never contains a credential.
"""

from __future__ import annotations

from dataclasses import dataclass


class ConnectorGovernanceError(PermissionError):
    """Raised when a connector mutation lacks a concrete requirement or approval."""


@dataclass(frozen=True)
class ConnectorMutationRequest:
    connector_uid: str
    operation: str
    project_requirement: str = ""
    approved: bool = False
    approval_reference: str = ""


class ConnectorMutationPolicy:
    def validate(self, request: ConnectorMutationRequest) -> None:
        if not request.connector_uid.strip():
            raise ConnectorGovernanceError("connector UID is required")
        if not request.project_requirement.strip():
            raise ConnectorGovernanceError("connector mutation requires a concrete project requirement")
        if not request.approved:
            raise ConnectorGovernanceError("connector mutation requires explicit approval")
        if request.operation in {"connect", "refresh", "revoke", "disconnect", "default"} and not request.approval_reference.strip():
            raise ConnectorGovernanceError("connector mutation requires a non-secret approval reference")
