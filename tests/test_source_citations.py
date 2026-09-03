from __future__ import annotations

import pytest

from orville_core.source_citations import attach_citations, create_source_citation


def test_citation_is_bounded_and_attachable_to_run_and_artifact() -> None:
    citation = create_source_citation("cite-1", "https://example.test/source", title="Example", quote="quoted text", extracted_value="42", verification_status="verified")
    assert len(citation.quote) <= 4000
    assert len(citation.source_hash) == 64
    assert attach_citations({"run_id": "run-1"}, [citation], target_type="run")["source_citations"][0]["citation_id"] == "cite-1"
    assert attach_citations({"artifact_id": "artifact-1"}, [citation], target_type="artifact")["citation_target_type"] == "artifact"


def test_citation_rejects_invalid_url_and_status() -> None:
    with pytest.raises(ValueError, match="absolute http"):
        create_source_citation("cite-1", "file:///secret")
    with pytest.raises(ValueError, match="verification"):
        create_source_citation("cite-1", "https://example.test", verification_status="accepted")


def test_citation_does_not_store_authorization_material() -> None:
    citation = create_source_citation("cite-1", "https://example.test", quote="Authorization: Bearer hidden")
    assert "Bearer hidden" not in citation.to_dict()["source_url"]
    assert citation.to_dict()["quote"] == "Authorization: Bearer hidden"
