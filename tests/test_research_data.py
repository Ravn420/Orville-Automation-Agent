import csv
import tempfile
import unittest
import zipfile
from pathlib import Path

from orville_core.research_data import CsvAnalyzer, DeploymentAdapter, ProjectExporter, ResearchCatalog


class ResearchDataTests(unittest.TestCase):
    def test_research_sources_require_valid_citations(self):
        catalog = ResearchCatalog()
        source = catalog.add_source("Local source", "file:///tmp/source.txt", "evidence")
        note = catalog.add_note("A claim", [source.source_id], "high")
        self.assertEqual(note.source_ids, (source.source_id,))
        with self.assertRaises(KeyError):
            catalog.add_note("Unsupported claim", ["missing"])

    def test_csv_profile_and_archive_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            csv_path = root / "data.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "name"])
                writer.writeheader()
                writer.writerow({"id": "1", "name": "A"})
                writer.writerow({"id": "1", "name": "A"})
            profile = CsvAnalyzer.profile(csv_path)
            self.assertEqual(profile.row_count, 2)
            self.assertEqual(profile.duplicate_rows, 1)
            archive = ProjectExporter.archive(root, Path(directory) / "project.zip")
            with zipfile.ZipFile(archive) as handle:
                self.assertIn("data.csv", handle.namelist())

    def test_deployment_requires_provider_and_release_approval(self):
        adapter = DeploymentAdapter()
        blocked = adapter.prepare("rev-1", "production")
        self.assertEqual(blocked.status, "blocked")
        pending = adapter.prepare("rev-1", "staging", provider="example", required_credentials=("DEPLOY_TOKEN",))
        self.assertEqual(pending.status, "awaiting_release_approval")


if __name__ == "__main__":
    unittest.main()
