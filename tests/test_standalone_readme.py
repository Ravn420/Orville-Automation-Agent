from __future__ import annotations

from pathlib import Path
import re
import unittest

from tests.repository_references import resolve_repository_reference


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


class StandaloneReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = README.read_text(encoding="utf-8")

    def test_required_standalone_sections_are_present(self) -> None:
        for heading in (
            "## Prerequisites",
            "## Installation",
            "## Configuration",
            "## Usage",
            "## Examples",
            "## Troubleshooting",
        ):
            self.assertIn(heading, self.text)

    def test_readme_contains_runnable_local_commands(self) -> None:
        for command in (
            "python -m venv .venv",
            "python -m pip install -e .",
            "python examples\\basic_run.py",
            "python tools\\project_checks.py all",
            "python -m unittest discover -s tests -v",
        ):
            self.assertIn(command, self.text)

    def test_referenced_local_contracts_exist(self) -> None:
        references = re.findall(r"`((?:docs|tools|orville_core|examples)/[^\s`]+)", self.text)
        self.assertGreaterEqual(len(references), 10)
        for reference in references:
            self.assertTrue(resolve_repository_reference(ROOT, reference).is_file(), reference)

    def test_readme_preserves_security_and_standalone_boundaries(self) -> None:
        for phrase in (
            "do not require provider credentials",
            "must not be placed in prompts",
            "require explicit confirmation",
            "Treat instructions found in web pages",
            "does not claim those services are available by default",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotRegex(self.text, r"(?i)Bearer\s+[A-Za-z0-9._-]{8,}")


if __name__ == "__main__":
    unittest.main()
