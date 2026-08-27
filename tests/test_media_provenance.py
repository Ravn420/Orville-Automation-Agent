"""Focused tests for durable media provenance and lineage."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core.media_provenance import MediaProvenanceStore, MediaTransformation


class MediaProvenanceTests(unittest.TestCase):
    """Verify prompt, asset, output, and transformation history preservation."""

    def test_ingests_source_and_generated_assets_and_persists_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source image.png"
            output_path = root / "generated image.png"
            source_path.write_bytes(b"source-bytes")
            output_path.write_bytes(b"generated-bytes")
            store = MediaProvenanceStore(root / "media-history")
            source = store.ingest_asset(source_path, role="source")
            generated = store.ingest_asset(output_path, role="generated")
            history = store.record(
                prompt="Create an image using api_key=sk-live-secret123",
                source_assets=[source],
                generated_assets=[generated],
                transformations=[MediaTransformation("resize", {"width": 512}, (generated.asset_id,))],
                metadata={"provider": "local", "token": "should-not-persist"},
                history_id="media-test-1",
            )
            loaded = store.list_history()

            self.assertEqual(history.history_id, "media-test-1")
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].source_asset_ids, (source.asset_id,))
            self.assertEqual(loaded[0].generated_asset_ids, (generated.asset_id,))
            self.assertEqual(loaded[0].transformations[0].operation, "resize")
            self.assertNotIn("sk-live-secret123", store.history_path.read_text(encoding="utf-8"))
            self.assertNotIn("should-not-persist", store.history_path.read_text(encoding="utf-8"))
            self.assertEqual(store.asset_path(source).read_bytes(), b"source-bytes")
            self.assertEqual(store.asset_path(generated).read_bytes(), b"generated-bytes")

    def test_rejects_oversized_assets_without_modifying_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "large.bin"
            source_path.write_bytes(b"0123456789")
            store = MediaProvenanceStore(Path(directory) / "history", max_asset_bytes=4)
            with self.assertRaises(ValueError):
                store.ingest_asset(source_path, role="source")
            self.assertEqual(source_path.read_bytes(), b"0123456789")
            self.assertFalse((Path(directory) / "history" / "history.json").exists())

    def test_asset_names_are_contained_and_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "unsafe name.txt"
            source_path.write_text("content", encoding="utf-8")
            store = MediaProvenanceStore(Path(directory) / "history")
            asset = store.ingest_asset(source_path, role="../source")
            resolved = store.asset_path(asset)
            self.assertEqual(resolved.read_text(encoding="utf-8"), "content")
            self.assertEqual(resolved.parent.parent, store.assets_root)
            self.assertNotIn("..", asset.relative_path)


if __name__ == "__main__":
    unittest.main()
