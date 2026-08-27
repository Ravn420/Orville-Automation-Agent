"""Focused validation for the build, test, and preview automation contract."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "project_checks.py"
DOC_PATH = ROOT / "docs" / "BUILD_TEST_PREVIEW.md"


class ProjectChecksTests(unittest.TestCase):
    """Verify automation commands and safety boundaries remain documented."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.documentation = DOC_PATH.read_text(encoding="utf-8")

    def test_entrypoint_exposes_all_check_modes(self) -> None:
        for mode in ("build", "test", "preview", "all"):
            self.assertIn(f'"{mode}"', self.script)
            self.assertIn(f"project_checks.py {mode}", self.documentation)
        self.assertIn("--api-smoke", self.script)
        self.assertIn("project_checks.py all", self.documentation)

    def test_build_and_test_commands_are_reproducible(self) -> None:
        for command in (
            '"compileall"',
            '"pip"',
            '"wheel"',
            '"pytest"',
            '"--no-deps"',
        ):
            self.assertIn(command, self.script)
        self.assertIn("tmp/project-check-wheels/", self.documentation)
        self.assertIn("complete `pytest` suite", self.documentation)

    def test_preview_defaults_to_local_credential_free_checks(self) -> None:
        self.assertIn('"tools/signal_room_checks.py"', self.script)
        self.assertIn('"webui"', self.script)
        self.assertIn("credential-free", self.documentation)
        self.assertIn("127.0.0.1:8787", self.documentation)
        self.assertIn("do not publish content", self.documentation)

    def test_optional_api_smoke_requires_existing_local_configuration(self) -> None:
        self.assertIn(".env.production", self.script)
        self.assertIn("ORVILLE_API_TOKEN", self.documentation)
        self.assertIn("credential was requested or generated", self.script)
        self.assertIn("Never commit `.env.production`", self.documentation)


if __name__ == "__main__":
    unittest.main()
