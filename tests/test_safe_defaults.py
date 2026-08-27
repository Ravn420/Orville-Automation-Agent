"""Focused validation for safe settings defaults and advanced overrides."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "config" / "settings-defaults.example.json"
CONTRACT_PATH = ROOT / "docs" / "SAFE_DEFAULTS_AND_ADVANCED_SETTINGS.md"


class SafeDefaultsTests(unittest.TestCase):
    """Verify safe defaults are bounded, overridable, and secret-free."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_defaults_cover_all_requested_settings_areas(self) -> None:
        defaults = self.profile["defaults"]
        for key in (
            "provider",
            "model",
            "privacy_routing",
            "artifact_path",
            "temporary_path",
            "max_concurrency",
            "task_timeout_seconds",
            "schedule_mode",
            "notification_events",
            "theme",
            "motion",
        ):
            self.assertIn(key, defaults)
        self.assertEqual(defaults["privacy_routing"], "local_only")
        self.assertEqual(defaults["schedule_mode"], "manual")
        self.assertEqual(defaults["max_concurrency"], 2)
        self.assertEqual(defaults["task_timeout_seconds"], 1800)

    def test_advanced_settings_are_optional_and_safe(self) -> None:
        advanced = self.profile["advanced"]
        self.assertIsNone(advanced["credential_reference"])
        self.assertIsNone(advanced["endpoint_url"])
        self.assertEqual(advanced["notification_targets"], [])
        rules = self.profile["rules"]
        for key in (
            "advanced_settings_hidden_by_default",
            "unknown_values_fail_closed",
            "secrets_excluded_from_defaults",
            "external_actions_require_approval",
            "reset_is_non_destructive",
            "defaults_are_overridable",
        ):
            self.assertTrue(rules[key])
        for phrase in (
            "approved per-run value",
            "approved project value",
            "explicitly saved user value",
            "then the safe default",
            "fail closed",
            "reset-to-default",
            "protected reference",
        ):
            self.assertIn(phrase, self.contract)

    def test_contract_covers_security_and_requested_advanced_areas(self) -> None:
        for phrase in (
            "Provider and model",
            "Privacy routing",
            "Storage",
            "Resource limits",
            "Schedules",
            "Notifications",
            "Theme and motion",
            "Telemetry",
            "Advanced settings disclosure",
            "approval-gated",
            "non-destructive",
            "raw exceptions",
            "secret-bearing URLs",
        ):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.contract + json.dumps(self.profile),
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
