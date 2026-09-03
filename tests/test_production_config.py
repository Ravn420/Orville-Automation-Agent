from __future__ import annotations

import pytest

from orville_core.production_config import ProductionBoundaryConfig


def _valid() -> ProductionBoundaryConfig:
    return ProductionBoundaryConfig("https://identity.example.test", frozenset({"run:read", "run:execute"}), True, ("https://app.example.test",), "deployment-secret-ref", "https://audit.example.test/events")


def test_valid_production_boundary_passes() -> None:
    _valid().validate()


@pytest.mark.parametrize("field,value", [("identity_issuer", "http://identity.example.test"), ("cors_origins", ("*",)), ("secret_reference", "sk-live-value")])
def test_unsafe_production_boundary_fails_closed(field: str, value: object) -> None:
    values = _valid().__dict__
    values[field] = value
    with pytest.raises(ValueError):
        ProductionBoundaryConfig(**values).validate()
