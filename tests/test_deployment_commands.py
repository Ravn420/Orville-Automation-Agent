from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy.ps1"
DOC = ROOT / "docs" / "DEPLOYMENT_TARGET_COMMANDS.md"


class DeploymentCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = SCRIPT.read_text(encoding="utf-8")
        self.doc = DOC.read_text(encoding="utf-8")

    def test_all_supported_targets_are_declared_and_documented(self) -> None:
        targets = ("sandbox", "web-hosting", "attached-desktop", "persistent-computing")
        for target in targets:
            self.assertIn(target, self.script)
            self.assertIn(target, self.doc)
        self.assertIn("ValidateSet", self.script)

    def test_deployment_is_dry_run_by_default_and_execute_is_explicit(self) -> None:
        self.assertIn("[switch]$Execute", self.script)
        self.assertIn("if (-not $Execute)", self.script)
        self.assertIn("No external deployment was executed", self.script)
        self.assertIn("without `-Execute`", self.doc)
        self.assertIn("does not create credentials", self.doc)

    def test_target_commands_preserve_existing_boundaries(self) -> None:
        for marker in ("tools/project_checks.py", "docker-compose.yml", "build-release.ps1", "install-orville.ps1"):
            self.assertIn(marker, self.script)
        self.assertIn("Compose commands", self.doc)
        self.assertIn("release-hardening", self.doc)
        self.assertIn("persistent services", self.doc)


if __name__ == "__main__":
    unittest.main()
