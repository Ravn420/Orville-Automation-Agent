from __future__ import annotations

from orville_core.catalog_adapters import catalog_summary, load_catalog


def test_full_catalog_is_represented_and_not_falsely_operational():
    adapters = load_catalog()
    summary = catalog_summary(adapters)
    assert summary["total"] == 372
    assert summary["configuration_required"] == 372
    assert summary["operational"] == 0
    assert len({item.connector_id for item in adapters}) == 372


def test_catalog_loader_supports_custom_fixture_and_preserves_metadata(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text('[{"uid":"fixture","name":"Fixture Service","brief":"Test service","enabled":true}]', encoding="utf-8")
    adapters = load_catalog(path)
    assert adapters[0].connector_id == "fixture"
    assert adapters[0].catalog_enabled is True
    assert adapters[0].status()["support_state"] == "configuration_required"
