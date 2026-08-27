from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "GUI_STANDALONE_OPERATIONS.md"


class GuiStandaloneOperationsTests(unittest.TestCase):
    """Verify standalone GUI operations are documented and secret-safe."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.document = DOC_PATH.read_text(encoding="utf-8")

    def test_run_build_and_package_commands_are_documented(self) -> None:
        for phrase in (
            "python windows_gui.py",
            "python examples\\basic_run.py",
            "pyinstaller.exe --noconfirm --clean Orville-Signal-Room.spec",
            ".\\build-release.ps1 -Version 0.1.0",
            "release\\Orville-Portable-0.1.0.zip",
            "ORVILLE_PORTABLE=1",
        ):
            self.assertIn(phrase, self.document)

    def test_update_install_deploy_and_rollback_boundaries_are_documented(self) -> None:
        for phrase in (
            "Safe update sequence",
            "release\\install-orville.ps1",
            "%LOCALAPPDATA%\\Programs\\Orville",
            "%LOCALAPPDATA%\\Orville\\data",
            "docker compose --env-file .env.production config --quiet",
            "docker compose --env-file .env.production up -d --build",
            "database backup",
            "Rollback is approval-gated",
            "down --volumes",
        ):
            self.assertIn(phrase, self.document)

    def test_standalone_boundaries_and_validation_are_explicit(self) -> None:
        for phrase in (
            "without requiring Manus",
            "Manus-specific adapters are optional",
            "credential-free local validation",
            "must not embed server credentials",
            "preserve local drafts",
            "Known limitations",
            "Code signing",
            "live browser automation",
        ):
            self.assertIn(phrase, self.document)
        self.assertNotRegex(
            self.document,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
