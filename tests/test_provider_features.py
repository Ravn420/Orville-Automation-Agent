import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orville_core.provider_features import PrivacyRoutingPolicy, PrivacyRoutingPolicyStore, discover_provider_models, redacted_provider_export
from orville_core.providers import ModelCapabilities, ProviderConfig


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit=None):
        return self.payload


class _Provider:
    def __init__(self, config):
        self.config = config


class ProviderFeatureTests(unittest.TestCase):
    def test_ollama_discovery_returns_model_ids(self):
        config = ProviderConfig("local", "ollama", "old", "http://127.0.0.1:11434")
        with patch("orville_core.provider_features.urlopen", return_value=_Response({"models": [{"name": "llama3.2", "size": 10}]})):
            result = discover_provider_models(config)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["models"][0]["id"], "llama3.2")

    def test_openai_compatible_discovery_does_not_return_key(self):
        config = ProviderConfig("cloud", "openai-compatible", "old", "https://example.test/v1", api_key="synthetic-secret")
        with patch("orville_core.provider_features.urlopen", return_value=_Response({"data": [{"id": "model-a"}]})) as opened:
            result = discover_provider_models(config)
        self.assertEqual(result["models"][0]["id"], "model-a")
        self.assertNotIn("synthetic-secret", json.dumps(result))
        self.assertNotIn("synthetic-secret", opened.call_args.args[0].full_url)

    def test_privacy_policy_persists_and_restricts_local(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PrivacyRoutingPolicyStore(Path(directory) / "policy.json")
            stored = store.set(PrivacyRoutingPolicy("restricted", ["local"], False))
            self.assertTrue(stored["local_only"])
            reloaded = PrivacyRoutingPolicyStore(Path(directory) / "policy.json")
            self.assertTrue(reloaded.get("restricted").local_only)

    def test_redacted_export_contains_no_provider_secret(self):
        config = ProviderConfig("cloud", "gemini", "model", "https://example.test", api_key="synthetic-secret", capabilities=ModelCapabilities(text=True))
        with tempfile.TemporaryDirectory() as directory:
            policies = PrivacyRoutingPolicyStore(Path(directory) / "policy.json")
            exported = redacted_provider_export([_Provider(config)], policies)
        serialized = json.dumps(exported)
        self.assertFalse(exported["secrets_included"])
        self.assertNotIn("synthetic-secret", serialized)
        self.assertFalse(exported["providers"][0]["api_key_configured"] is False)
        self.assertNotIn("api_key", exported["providers"][0])


if __name__ == "__main__":
    unittest.main()

    def test_discovery_catalog_persists_and_switches_active_model(self):
        from orville_core.provider_features import DiscoveryCatalogStore
        with tempfile.TemporaryDirectory() as directory:
            store = DiscoveryCatalogStore(Path(directory) / "catalog.json")
            store.record("local", {"provider_type": "ollama", "models": [{"id": "a"}, {"id": "b"}], "count": 2, "status": "ok"})
            selected = store.set_active("local", "b")
            self.assertEqual(selected["active_model"], "b")
            self.assertEqual(DiscoveryCatalogStore(Path(directory) / "catalog.json").get("local")["active_model"], "b")

    def test_provider_rate_limit_accounts_calls(self):
        from orville_core.provider_features import ProviderRateLimitStore
        with tempfile.TemporaryDirectory() as directory:
            store = ProviderRateLimitStore(Path(directory) / "usage.db")
            store.set_limit("local", 60, max_calls=1, max_tokens=100)
            self.assertEqual(store.admit("local")[0], True)
            self.assertEqual(store.admit("local")[0], False)
            self.assertEqual(store.snapshot("local")["calls_used"], 1)

    def test_remote_policy_store_falls_back_without_leaking_token(self):
        from orville_core.provider_features import RemotePolicyStore
        with tempfile.TemporaryDirectory() as directory:
            local = PrivacyRoutingPolicyStore(Path(directory) / "policy.json")
            remote = RemotePolicyStore(local, "https://policy.example.test", "synthetic-token")
            with patch("orville_core.provider_features.urlopen", side_effect=OSError("offline")):
                result = remote.save(PrivacyRoutingPolicy("cloud_approved", ["cloud"], False))
            self.assertFalse(result["remote_synced"])
            self.assertNotIn("synthetic-token", json.dumps(result))
            self.assertNotIn("synthetic-token", json.dumps(remote.status()))

    def test_remote_catalog_federation_is_tenant_scoped_and_falls_back(self):
        from orville_core.provider_features import DiscoveryCatalogStore, RemoteCatalogStore
        with tempfile.TemporaryDirectory() as directory:
            local = DiscoveryCatalogStore(Path(directory) / "catalog.json")
            local.record("local", {"provider_type": "ollama", "models": [{"id": "a"}], "count": 1, "status": "ok"})
            remote = RemoteCatalogStore(local, "https://catalog.example.test", "synthetic-token", "tenant-a")
            self.assertEqual(remote.status()["tenant_id"], "tenant-a")
            with patch("orville_core.provider_features.urlopen", side_effect=OSError("offline")):
                result = remote.sync()
            self.assertFalse(result["remote_synced"])
            self.assertEqual(result["catalogs"][0]["provider_id"], "local")

    def test_policy_backup_is_checksum_named_and_restorable_data_is_secret_free(self):
        from orville_core.provider_features import DiscoveryCatalogStore, PolicyBackupStore
        with tempfile.TemporaryDirectory() as directory:
            policies = PrivacyRoutingPolicyStore(Path(directory) / "policy.json")
            policies.set(PrivacyRoutingPolicy("local_only", ["local"], True))
            catalogs = DiscoveryCatalogStore(Path(directory) / "catalog.json")
            catalogs.record("local", {"provider_type": "ollama", "models": [{"id": "a"}], "count": 1, "status": "ok"})
            backup = PolicyBackupStore(Path(directory) / "backups").create(policies, catalogs)
            self.assertRegex(backup["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(Path(backup["path"]).exists())
            self.assertNotIn("api_key", Path(backup["path"]).read_text(encoding="utf-8"))
