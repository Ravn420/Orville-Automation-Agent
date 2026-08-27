import pytest

from orville_core import EndpointConfigError, LocalModelSpec, ProviderEndpointSpec


def test_provider_endpoint_spec_accepts_safe_reference_and_redacts_configuration():
    spec = ProviderEndpointSpec("blackbox", "Blackbox", "cloud-relay", "https://relay.example.test/v1", "model", "openai-compatible", api_key_reference="secret://blackbox")
    assert spec.redacted()["api_key_reference"] == "secret://blackbox"


def test_provider_endpoint_spec_rejects_unsafe_urls_and_raw_credentials():
    with pytest.raises(EndpointConfigError, match="HTTP"):
        ProviderEndpointSpec("x", "X", "cloud", "ftp://example.test", "model", "openai")
    with pytest.raises(EndpointConfigError, match="fragment"):
        ProviderEndpointSpec("x", "X", "cloud", "https://example.test/#unsafe", "model", "openai")
    with pytest.raises(EndpointConfigError, match="reference"):
        ProviderEndpointSpec("x", "X", "cloud", "https://example.test", "model", "openai", api_key_reference="Bearer secret")


def test_local_model_spec_validates_checksum_and_metadata():
    spec = LocalModelSpec("model", "/models/model.gguf", "a" * 64, "gguf", architecture="llama", quantization="Q4", runtime="ollama", capabilities=("text",), license_name="MIT", validation_status="valid")
    assert spec.redacted()["checksum_sha256"] == "a" * 64
    with pytest.raises(EndpointConfigError, match="64-character"):
        LocalModelSpec("model", "/models/model.gguf", "bad", "gguf")
