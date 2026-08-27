from __future__ import annotations

import pytest

from orville_core.connector_governance import ConnectorGovernanceError, ConnectorMutationPolicy, ConnectorMutationRequest


def test_connector_mutation_requires_concrete_requirement_and_approval() -> None:
    policy = ConnectorMutationPolicy()
    with pytest.raises(ConnectorGovernanceError, match="concrete project requirement"):
        policy.validate(ConnectorMutationRequest("github", "connect", approved=True, approval_reference="approval-1"))
    with pytest.raises(ConnectorGovernanceError, match="explicit approval"):
        policy.validate(ConnectorMutationRequest("github", "connect", "Orville issue sync", approval_reference="approval-1"))


def test_connector_mutation_accepts_metadata_only_approval_reference() -> None:
    policy = ConnectorMutationPolicy()
    policy.validate(ConnectorMutationRequest("github", "connect", "Orville issue sync", approved=True, approval_reference="approval-2026-08-27-1"))


def test_connector_mutation_rejects_missing_connector_id() -> None:
    with pytest.raises(ConnectorGovernanceError, match="connector UID"):
        ConnectorMutationPolicy().validate(ConnectorMutationRequest("", "connect", "Orville issue sync", approved=True, approval_reference="approval-1"))
