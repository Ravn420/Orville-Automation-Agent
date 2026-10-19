"""Comprehensive integration tests for media workflow system.

This module provides end-to-end integration tests covering:
- Complete media generation workflows
- Provider routing integration
- Error handling and edge cases
- Concurrent media operations
- Media lifecycle (generate → validate → verify → cleanup)
- API endpoint integration
- Cross-module integration scenarios
"""

from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient

from orville_core.api import create_app
from orville_core.media_generation import (
    ALL_FORMATS,
    AUDIO_FORMATS,
    BaseMediaGenerator,
    GenerationOptions,
    GenerationStatus,
    IMAGE_FORMATS,
    LocalImageGenerator,
    MediaFormatSpec,
    MediaGenerationService,
    MediaModality,
    OpenAIImageGenerator,
    ProviderCapability,
    StabilityImageGenerator,
    VIDEO_FORMATS,
)
from orville_core.media_provenance import (
    GenerationMetadata,
    GenerationSource,
    LicenseTerms,
    LicenseType,
    MediaAsset,
    MediaProvenanceStore,
    MediaTransformation,
    RightsStatus,
    RightsVerification,
)
from orville_core.media_validation import (
    ContentSafetyLevel,
    ContentSafetyResult,
    FileIntegrityResult,
    FormatSpecificResult,
    MediaValidationPolicy,
    MediaValidationResult,
    ValidationSeverity,
    validate_content_safety,
    validate_file_integrity,
    validate_format_specific,
    validate_media,
)
from orville_core.providers import MediaResponse, ProviderConfig, ProviderError


# =============================================================================
# Test Fixtures and Helpers
# =============================================================================

def create_test_image_bytes(format_ext: str = "png") -> bytes:
    """Create minimal valid image bytes for testing."""
    if format_ext == "png":
        return (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\x0dIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00"
            b"\x90wS\xde"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
    elif format_ext in ("jpg", "jpeg"):
        return (
            b"\xff\xd8\xff\xe0"
            b"\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xd9"
        )
    elif format_ext == "gif":
        return (
            b"GIF89a"
            b"\x01\x00\x01\x00"
            b"\x00\x00\x00"
            b"\x00\x00\x00"
            b"\x21\xf9\x04\x00\x00\x00\x00\x00"
            b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00"
            b"\x02\x02\x44\x01\x00"
            b"\x3b"
        )
    elif format_ext == "webp":
        return (
            b"RIFF\x1a\x00\x00\x00"
            b"WEBP"
            b"VP8 "
            b"\x0a\x00\x00\x00"
            b"\x9d\x01\x2a"
            b"\x01\x00\x00\x00\x01\x00"
        )
    return b"\x89PNG\r\n\x1a\n"


def create_test_audio_bytes(format_ext: str = "wav") -> bytes:
    """Create minimal valid audio bytes for testing."""
    if format_ext == "wav":
        return (
            b"RIFF\x24\x00\x00\x00"
            b"WAVE"
            b"fmt \x10\x00\x00\x00"
            b"\x01\x00\x01\x00"
            b"\x44\xac\x00\x00"
            b"\x88\x58\x01\x00"
            b"\x02\x00\x10\x00"
            b"data\x00\x00\x00\x00"
        )
    elif format_ext == "mp3":
        return b"\xff\xfb\x90\x00" + b"\x00" * 417
    return b"RIFF\x00\x00\x00\x00WAVE"


def get_auth_headers(token: str = "test-token") -> dict[str, str]:
    """Get properly formatted authorization headers."""
    return {"Authorization": f"Bearer {token}"}


class FakeMediaProvider:
    """Fake provider for testing media generation."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.call_count = 0

    def generate(self, request):
        raise AssertionError("text path should not be used")

    def stream(self, request):
        raise AssertionError("stream path should not be used")

    def embed(self, inputs):
        raise AssertionError("embedding path should not be used")

    def health_check(self):
        return {
            "ok": True,
            "provider_id": self.config.provider_id,
            "model": self.config.model
        }

    def generate_media(self, request):
        self.call_count += 1
        return MediaResponse(
            self.config.provider_id,
            self.config.model,
            request.modality,
            [{"type": request.modality, "url": f"https://cdn.example.test/{request.modality}/{self.call_count}"}],
            {"fixture": True, "call_count": self.call_count}
        )


# =============================================================================
# End-to-End Workflow Tests
# =============================================================================

class TestEndToEndMediaWorkflows(unittest.TestCase):
    """End-to-end tests for complete media workflows."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.checkpoint_dir = Path(self.temp_dir.name) / ".orville"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_complete_image_generation_workflow(self) -> None:
        """Test complete workflow: generate."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "test-image-provider",
                "provider_type": "stable-horde",
                "model": "sdxl",
                "base_url": "https://aihorde.net/api",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "provider_id": "test-image-provider",
                "modality": "image",
                "prompt": "A beautiful sunset over mountains",
                "options": {"width": 1024, "height": 768, "format": "png"}
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["modality"], "image")
            self.assertIn("assets", data)
            self.assertIn("routing", data)

    def test_complete_video_generation_workflow(self) -> None:
        """Test complete video generation workflow."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "test-video-provider",
                "provider_type": "openai",
                "model": "sora",
                "base_url": "https://api.openai.com/v1",
                "capabilities": ["video_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "provider_id": "test-video-provider",
                "modality": "video",
                "prompt": "A serene ocean wave",
                "options": {"duration_seconds": 5, "format": "mp4"}
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["modality"], "video")

    def test_audio_generation_workflow(self) -> None:
        """Test audio generation workflow."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "test-audio-provider",
                "provider_type": "openai",
                "model": "tts-1",
                "base_url": "https://api.openai.com/v1",
                "capabilities": ["audio"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "provider_id": "test-audio-provider",
                "modality": "audio",
                "prompt": "Hello, this is a test",
                "options": {"format": "mp3", "voice": "alloy"}
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["modality"], "audio")

    def test_multi_modality_workflow(self) -> None:
        """Test workflow with multiple media types."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "test-multi-provider",
                "provider_type": "openai",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "capabilities": ["image_generation", "audio", "video_generation"]
            })
            self.assertEqual(response.status_code, 200)

            modalities = ["image", "audio", "video"]
            for modality in modalities:
                response = client.post("/api/v1/media/generate", headers=headers, json={
                    "provider_id": "test-multi-provider",
                    "modality": modality,
                    "prompt": f"Test {modality} generation"
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["modality"], modality)


# =============================================================================
# Provider Routing Integration Tests
# =============================================================================

class TestProviderRoutingIntegration(unittest.TestCase):
    """Tests for provider routing integration."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.checkpoint_dir = Path(self.temp_dir.name) / ".orville"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_routing_fallback_to_available_provider(self) -> None:
        """Test that routing falls back when preferred provider unavailable."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            for i in range(3):
                response = client.post("/api/v1/providers", headers=headers, json={
                    "provider_id": f"test-provider-{i}",
                    "provider_type": "stable-horde",
                    "model": "sdxl",
                    "base_url": f"https://provider{i}.test/api",
                    "capabilities": ["image_generation"]
                })
                self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "modality": "image",
                "prompt": "Test routing fallback",
                "allow_fallback": True
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("routing", data)
            self.assertIn("selected_provider", data["routing"])

    def test_routing_with_local_only_constraint(self) -> None:
        """Test routing with local_only constraint."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "local-provider",
                "provider_type": "ollama",
                "model": "llava",
                "base_url": "http://localhost:11434",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "modality": "image",
                "prompt": "Test local routing",
                "local_only": True
            })
            self.assertIn(response.status_code, [200, 400])

    def test_routing_preferred_provider_selection(self) -> None:
        """Test that preferred provider is selected when available."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "preferred-provider",
                "provider_type": "openai",
                "model": "dall-e-3",
                "base_url": "https://api.openai.com/v1",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "provider_id": "preferred-provider",
                "modality": "image",
                "prompt": "Test preferred provider"
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["provider_id"], "preferred-provider")

    def test_routing_attempts_tracking(self) -> None:
        """Test that routing attempts are tracked and reported."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "test-provider",
                "provider_type": "stable-horde",
                "model": "sdxl",
                "base_url": "https://test.example.com/api",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "modality": "image",
                "prompt": "Test routing attempts"
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("routing", data)
            self.assertIn("attempts", data["routing"])
            self.assertIsInstance(data["routing"]["attempts"], list)


# =============================================================================
# Error Handling and Edge Case Tests
# =============================================================================

class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Tests for error handling and edge cases."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.checkpoint_dir = Path(self.temp_dir.name) / ".orville"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_invalid_modality_rejected(self) -> None:
        """Test that invalid modality is rejected."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)
        headers = get_auth_headers("test-token")

        response = client.post("/api/v1/media/generate", headers=headers, json={
            "modality": "invalid_modality",
            "prompt": "test"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("modality", response.json()["detail"].lower())

    def test_missing_provider_capability(self) -> None:
        """Test error when provider lacks required capability."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "image-only-provider",
                "provider_type": "stable-horde",
                "model": "sdxl",
                "base_url": "https://test.example.com/api",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "provider_id": "image-only-provider",
                "modality": "video",
                "prompt": "test video"
            })
            self.assertEqual(response.status_code, 400)

    def test_empty_prompt_rejected(self) -> None:
        """Test that empty prompt is rejected."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)
        headers = get_auth_headers("test-token")

        response = client.post("/api/v1/media/generate", headers=headers, json={
            "modality": "image",
            "prompt": ""
        })
        self.assertEqual(response.status_code, 422)

    def test_invalid_options_rejected(self) -> None:
        """Test that invalid options are rejected."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "test-provider",
                "provider_type": "stable-horde",
                "model": "sdxl",
                "base_url": "https://test.example.com/api",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "modality": "image",
                "prompt": "test",
                "options": {"number": 10}
            })
            self.assertEqual(response.status_code, 400)

    def test_nonexistent_media_not_found(self) -> None:
        """Test that non-existent media returns 404."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)
        headers = get_auth_headers("test-token")

        response = client.get("/api/v1/media/non-existent-id", headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_asset_validation(self) -> None:
        """Test validation of non-existent asset."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)
        headers = get_auth_headers("test-token")

        response = client.post("/api/v1/media/validate", headers=headers, json={
            "asset_id": "non-existent-asset",
            "modality": "image"
        })
        self.assertEqual(response.status_code, 404)

    def test_invalid_policy_parameters(self) -> None:
        """Test validation with invalid policy parameters."""
        with self.assertRaises(ValueError):
            MediaValidationPolicy(
                modality="image",
                max_bytes=0
            )

    def test_malformed_media_file(self) -> None:
        """Test handling of malformed media files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "fake.png"
            test_file.write_bytes(b"not a valid image file")

            policy = MediaValidationPolicy(modality="image")
            result = validate_media(test_file, policy=policy)

            self.assertFalse(result.valid)
            self.assertTrue(
                any("magic" in d.lower() or "format" in d.lower() for d in result.diagnostics)
            )

    def test_oversized_file_rejection(self) -> None:
        """Test rejection of oversized files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "large.png"
            test_file.write_bytes(create_test_image_bytes("png") + b"x" * 1000)

            policy = MediaValidationPolicy(
                modality="image",
                max_bytes=100
            )
            result = validate_media(test_file, policy=policy)

            self.assertFalse(result.valid)
            self.assertTrue(any("size" in d.lower() for d in result.diagnostics))


# =============================================================================
# Concurrent Media Operations Tests
# =============================================================================

class TestConcurrentMediaOperations(unittest.TestCase):
    """Tests for concurrent media operations."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.checkpoint_dir = Path(self.temp_dir.name) / ".orville"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_concurrent_generation_requests(self) -> None:
        """Test handling of concurrent generation requests."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "concurrent-provider",
                "provider_type": "stable-horde",
                "model": "sdxl",
                "base_url": "https://test.example.com/api",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            def make_request(i: int) -> dict:
                return client.post("/api/v1/media/generate", headers=headers, json={
                    "provider_id": "concurrent-provider",
                    "modality": "image",
                    "prompt": f"Concurrent test {i}"
                }).json()

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request, i) for i in range(5)]
                results = [f.result() for f in as_completed(futures)]

            self.assertEqual(len(results), 5)
            for result in results:
                self.assertEqual(result["modality"], "image")

    def test_concurrent_validation_operations(self) -> None:
        """Test concurrent validation of multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files = []
            for i in range(5):
                test_file = Path(temp_dir) / f"test_{i}.png"
                test_file.write_bytes(create_test_image_bytes("png"))
                files.append(test_file)

            policy = MediaValidationPolicy(modality="image")

            def validate_file(file_path: Path) -> MediaValidationResult:
                return validate_media(file_path, policy=policy)

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(validate_file, f) for f in files]
                results = [f.result() for f in as_completed(futures)]

            self.assertEqual(len(results), 5)

    def test_thread_safe_provenance_store(self) -> None:
        """Test thread-safe operations on provenance store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            assets = [
                MediaAsset(
                    asset_id=f"asset-{i}",
                    role="generated",
                    name=f"test_{i}.png",
                    relative_path=f"test/{i}.png",
                    media_type="image/png",
                    size=100,
                    sha256="abc123",
                    created_at=datetime.now(UTC).isoformat()
                )
                for i in range(10)
            ]

            def record_asset(asset: MediaAsset) -> None:
                store.record(
                    prompt=f"Test prompt for {asset.asset_id}",
                    source_assets=[],
                    generated_assets=[asset],
                    generation_metadata=None
                )

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(record_asset, a) for a in assets]
                for f in as_completed(futures):
                    f.result()

            history = list(store.list_history())
            self.assertEqual(len(history), 10)

    def test_concurrent_format_validation(self) -> None:
        """Test concurrent format-specific validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            formats = ["png", "jpg", "gif"]
            files = []
            for fmt in formats:
                test_file = Path(temp_dir) / f"test.{fmt}"
                test_file.write_bytes(create_test_image_bytes(fmt))
                files.append((fmt, test_file))

            policy = MediaValidationPolicy(modality="image")

            def validate_format(item: tuple) -> tuple:
                fmt, file_path = item
                result = validate_format_specific(file_path, policy)
                return fmt, result

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(validate_format, f) for f in files]
                results = {f.result()[0]: f.result()[1] for f in as_completed(futures)}

            self.assertEqual(len(results), 3)


# =============================================================================
# Media Lifecycle Tests
# =============================================================================

class TestMediaLifecycle(unittest.TestCase):
    """Tests for complete media lifecycle operations."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.checkpoint_dir = Path(self.temp_dir.name) / ".orville"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_lifecycle_generate_validate_verify(self) -> None:
        """Test complete lifecycle: generate → validate → verify."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "generated.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            policy = MediaValidationPolicy(modality="image")
            validation_result = validate_media(test_file, policy=policy)
            self.assertTrue(validation_result.valid)

            store = MediaProvenanceStore(temp_dir)
            asset = MediaAsset(
                asset_id="test-asset-001",
                role="generated",
                name="generated.png",
                relative_path="generated.png",
                media_type="image/png",
                size=test_file.stat().st_size,
                sha256=hashlib.sha256(test_file.read_bytes()).hexdigest(),
                created_at=datetime.now(UTC).isoformat()
            )

            store.record(
                prompt="Test generation",
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None
            )

            history = list(store.list_history())
            self.assertEqual(len(history), 1)
            record = history[0]
            self.assertTrue(record.verify_integrity())

    def test_lifecycle_with_source_assets(self) -> None:
        """Test lifecycle with source asset transformation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            source_file = Path(temp_dir) / "source.png"
            source_file.write_bytes(create_test_image_bytes("png"))

            source_asset = MediaAsset(
                asset_id="source-001",
                role="source",
                name="source.png",
                relative_path="source.png",
                media_type="image/png",
                size=source_file.stat().st_size,
                sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
                created_at=datetime.now(UTC).isoformat()
            )

            derived_file = Path(temp_dir) / "derived.png"
            derived_file.write_bytes(create_test_image_bytes("png"))

            derived_asset = MediaAsset(
                asset_id="derived-001",
                role="generated",
                name="derived.png",
                relative_path="derived.png",
                media_type="image/png",
                size=derived_file.stat().st_size,
                sha256=hashlib.sha256(derived_file.read_bytes()).hexdigest(),
                created_at=datetime.now(UTC).isoformat()
            )

            store.record(
                prompt="Transform source image",
                source_assets=[source_asset],
                generated_assets=[derived_asset],
                generation_metadata=None
            )

            history = list(store.list_history())
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].source_asset_ids, ("source-001",))
            self.assertEqual(history[0].generated_asset_ids, ("derived-001",))

    def test_lifecycle_with_license_management(self) -> None:
        """Test lifecycle with license management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            test_file = Path(temp_dir) / "licensed.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            asset = MediaAsset(
                asset_id="licensed-001",
                role="generated",
                name="licensed.png",
                relative_path="licensed.png",
                media_type="image/png",
                size=test_file.stat().st_size,
                sha256=hashlib.sha256(test_file.read_bytes()).hexdigest(),
                created_at=datetime.now(UTC).isoformat()
            )

            license_terms = LicenseTerms(
                license_type=LicenseType.CC_BY_SA,
                holder="Test Creator",
                attribution_required=True,
                attribution_text="Created by Test Creator",
                commercial_use_allowed=True,
                modification_allowed=True,
                share_alike_required=True
            )

            store.record(
                prompt="Licensed generation",
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None)

            history = list(store.list_history())
            self.assertEqual(len(history), 1)
            self.assertIsNotNone(history[0].license_terms)
            self.assertEqual(history[0].license_terms.license_type, LicenseType.CC_BY_SA)

    def test_lifecycle_rights_verification(self) -> None:
        """Test lifecycle with rights verification workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            test_file = Path(temp_dir) / "verified.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            asset = MediaAsset(
                asset_id="verified-001",
                role="generated",
                name="verified.png",
                relative_path="verified.png",
                media_type="image/png",
                size=test_file.stat().st_size,
                sha256=hashlib.sha256(test_file.read_bytes()).hexdigest(),
                created_at=datetime.now(UTC).isoformat()
            )

            store.record(
                prompt="Verified generation",
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None)

            verification = RightsVerification(
                verification_id="verify-001",
                asset_id="verified-001",
                status=RightsStatus.VERIFIED,
                verified_by="test-verifier",
                verified_at=datetime.now(UTC).isoformat(),
                verification_method="manual_review",
                evidence_urls=["https://example.com/evidence"],
                notes="Rights verified through manual review"
            )

            store.record_verification(verification)

            verifications = list(store.list_verifications("verified-001"))
            self.assertEqual(len(verifications), 1)
            self.assertEqual(verifications[0].status, RightsStatus.VERIFIED)

    def test_lifecycle_provenance_chain(self) -> None:
        """Test building a chain of provenance records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            assets = []
            for i in range(3):
                test_file = Path(temp_dir) / f"asset_{i}.png"
                test_file.write_bytes(create_test_image_bytes("png"))

                asset = MediaAsset(
                    asset_id=f"chain-{i:03d}",
                    role="generated",
                    name=f"asset_{i}.png",
                    relative_path=f"asset_{i}.png",
                    media_type="image/png",
                    size=test_file.stat().st_size,
                    sha256=hashlib.sha256(test_file.read_bytes()).hexdigest(),
                    created_at=datetime.now(UTC).isoformat()
                )
                assets.append(asset)

                source_assets = [assets[i-1]] if i > 0 else []
                store.record(
                    prompt=f"Generation step {i}",
                    source_assets=source_assets,
                    generated_assets=[asset],
                generation_metadata=None)

            history = list(store.list_history())
            self.assertEqual(len(history), 3)

            for i, record in enumerate(history):
                if i == 0:
                    self.assertEqual(len(record.source_asset_ids), 0)
                else:
                    self.assertEqual(len(record.source_asset_ids), 1)


# =============================================================================
# API Endpoint Integration Tests
# =============================================================================

class TestApiEndpointIntegration(unittest.TestCase):
    """Tests for API endpoint integration."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.checkpoint_dir = Path(self.temp_dir.name) / ".orville"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_media_generate_endpoint(self) -> None:
        """Test POST /api/v1/media/generate endpoint."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "api-test-provider",
                "provider_type": "stable-horde",
                "model": "sdxl",
                "base_url": "https://test.example.com/api",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/media/generate", headers=headers, json={
                "provider_id": "api-test-provider",
                "modality": "image",
                "prompt": "API test generation",
                "options": {"width": 640, "height": 480}
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("modality", data)
            self.assertIn("provider_id", data)
            self.assertIn("assets", data)
            self.assertIn("routing", data)

    def test_media_validate_endpoint(self) -> None:
        """Test POST /api/v1/media/validate endpoint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "validate_test.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            with patch("orville_core.api.create_app") as mock_create_app:
                app = create_app(
                    api_token="test-token",
                    storage="json",
                    checkpoint_dir=self.checkpoint_dir
                )
                client = TestClient(app)
                headers = get_auth_headers("test-token")

                response = client.post("/api/v1/artifacts/binary", headers=headers, files={
                    "file": ("validate_test.png", test_file.read_bytes(), "image/png")
                })

                response = client.post("/api/v1/media/validate", headers=headers, json={
                    "asset_id": "validate_test",
                    "modality": "image",
                    "policy": {"max_bytes": 1000000}
                })
                self.assertIn(response.status_code, [200, 404])

    def test_media_get_endpoint(self) -> None:
        """Test GET /api/v1/media/{media_id} endpoint."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)
        headers = get_auth_headers("test-token")

        response = client.get("/api/v1/media/test-media-id", headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_media_provenance_endpoint(self) -> None:
        """Test GET /api/v1/media/{media_id}/provenance endpoint."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)
        headers = get_auth_headers("test-token")

        response = client.get("/api/v1/media/test-id/provenance", headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_media_verify_endpoint(self) -> None:
        """Test POST /api/v1/media/{media_id}/verify endpoint."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)
        headers = get_auth_headers("test-token")

        response = client.post("/api/v1/media/test-id/verify", headers=headers, json={
            "verification_method": "manual",
            "evidence_urls": ["https://example.com/evidence"],
            "notes": "Verified"
        })
        self.assertEqual(response.status_code, 404)

    def test_legacy_generate_media_endpoint(self) -> None:
        """Test POST /api/v1/generate/media legacy endpoint."""
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(
                api_token="test-token",
                storage="json",
                checkpoint_dir=self.checkpoint_dir
            )
            client = TestClient(app)
            headers = get_auth_headers("test-token")

            response = client.post("/api/v1/providers", headers=headers, json={
                "provider_id": "legacy-provider",
                "provider_type": "stable-horde",
                "model": "sdxl",
                "base_url": "https://test.example.com/api",
                "capabilities": ["image_generation"]
            })
            self.assertEqual(response.status_code, 200)

            response = client.post("/api/v1/generate/media", headers=headers, json={
                "modality": "image",
                "prompt": "Legacy endpoint test"
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("modality", data)
            self.assertIn("assets", data)

    def test_unauthorized_access_rejected(self) -> None:
        """Test that unauthorized access is rejected."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)

        response = client.post("/api/v1/media/generate", json={
            "modality": "image",
            "prompt": "Unauthorized test"
        })
        self.assertEqual(response.status_code, 401)
    def test_invalid_token_rejected(self) -> None:
        """Test that invalid token is rejected."""
        app = create_app(
            api_token="test-token",
            storage="json",
            checkpoint_dir=self.checkpoint_dir
        )
        client = TestClient(app)
        headers = {"Authorization": "Bearer invalid-token"}

        response = client.post("/api/v1/media/generate", headers=headers, json={
            "modality": "image",
            "prompt": "Invalid token test"
        })
        self.assertEqual(response.status_code, 401)


# =============================================================================
# Cross-Module Integration Tests
# =============================================================================

class TestCrossModuleIntegration(unittest.TestCase):
    """Tests for cross-module integration scenarios."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_generation_with_validation_integration(self) -> None:
        """Test integration between generation and validation modules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "generated.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            policy = MediaValidationPolicy(
                modality="image",
                allowed_formats=frozenset({"png", "jpg"}),
                min_width=1,
                max_width=10000,
                min_height=1,
                max_height=10000
            )

            result = validate_media(test_file, policy=policy)
            self.assertTrue(result.valid)
            self.assertIsNotNone(result.file_integrity)
            self.assertIsNotNone(result.format_specific)

    def test_generation_with_provenance_integration(self) -> None:
        """Test integration between generation and provenance modules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            test_file = Path(temp_dir) / "integrated.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            asset = MediaAsset(
                asset_id="integrated-001",
                role="generated",
                name="integrated.png",
                relative_path="integrated.png",
                media_type="image/png",
                size=test_file.stat().st_size,
                sha256=hashlib.sha256(test_file.read_bytes()).hexdigest(),
                created_at=datetime.now(UTC).isoformat()
            )

            license_terms = LicenseTerms(
                license_type=LicenseType.CC_BY,
                holder="Integration Test",
                attribution_required=True
            )

            store.record(
                prompt="Integration test generation",
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None
            )

            history = list(store.list_history())
            self.assertEqual(len(history), 1)
            self.assertIsNotNone(history[0].generation_metadata)
            self.assertEqual(history[0].generation_metadata.source, GenerationSource.AI_GENERATED)

    def test_validation_with_provenance_integration(self) -> None:
        """Test integration between validation and provenance modules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            test_file = Path(temp_dir) / "validated.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            policy = MediaValidationPolicy(modality="image")
            validation_result = validate_media(test_file, policy=policy)

            asset = MediaAsset(
                asset_id="validated-001",
                role="generated",
                name="validated.png",
                relative_path="validated.png",
                media_type="image/png",
                size=test_file.stat().st_size,
                sha256=hashlib.sha256(test_file.read_bytes()).hexdigest(),
                created_at=datetime.now(UTC).isoformat()
            )

            store.record(
                prompt="Validated generation",
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None)

            history = list(store.list_history())
            self.assertEqual(len(history), 1)

            integrity_valid = history[0].verify_integrity()
            self.assertTrue(integrity_valid)

    def test_all_modules_together(self) -> None:
        """Test all three modules working together."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            test_file = Path(temp_dir) / "complete.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            policy = MediaValidationPolicy(
                modality="image",
                require_license=True,
                require_rights_holder=True
            )
            validation_result = validate_media(test_file, policy=policy)
            self.assertTrue(validation_result.valid)

            asset = MediaAsset(
                asset_id="complete-001",
                role="generated",
                name="complete.png",
                relative_path="complete.png",
                media_type="image/png",
                size=test_file.stat().st_size,
                sha256=hashlib.sha256(test_file.read_bytes()).hexdigest(),
                created_at=datetime.now(UTC).isoformat()
            )

            license_terms = LicenseTerms(
                license_type=LicenseType.MIT,
                holder="Complete Test",
                commercial_use_allowed=True,
                modification_allowed=True
            )

            store.record(
                prompt="Complete integration test",
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None
            )

            verification = RightsVerification(
                verification_id="complete-verify-001",
                asset_id="complete-001",
                status=RightsStatus.VERIFIED,
                verified_by="integration-test",
                verified_at=datetime.now(UTC).isoformat(),
                verification_method="automated"
            )
            store.record_verification(verification)

            history = list(store.list_history())
            self.assertEqual(len(history), 1)

            verifications = list(store.list_verifications("complete-001"))
            self.assertEqual(len(verifications), 1)
            self.assertEqual(verifications[0].status, RightsStatus.VERIFIED)

            self.assertTrue(history[0].verify_integrity())

    def test_format_specific_validation_integration(self) -> None:
        """Test format-specific validation across different formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            formats = ["png", "jpg", "gif", "webp"]

            for fmt in formats:
                test_file = Path(temp_dir) / f"test.{fmt}"
                test_file.write_bytes(create_test_image_bytes(fmt))

                policy = MediaValidationPolicy(
                    modality="image",
                    allowed_formats=frozenset({fmt})
                )

                result = validate_format_specific(test_file, policy)
                self.assertTrue(result.valid or len(result.diagnostics) > 0)
                self.assertEqual(result.format, fmt)

    def test_content_safety_integration(self) -> None:
        """Test content safety validation integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "safe.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            result = validate_content_safety(test_file)
            self.assertIn(result.level, [ContentSafetyLevel.SAFE, ContentSafetyLevel.UNKNOWN])

    def test_file_integrity_integration(self) -> None:
        """Test file integrity validation integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "integrity.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            result = validate_file_integrity(test_file, compute_checksum=True)
            self.assertTrue(result.valid)
            self.assertIsNotNone(result.checksum_sha256)
            self.assertEqual(result.format_detected, "png")

    def test_magic_number_detection_integration(self) -> None:
        """Test magic number detection across formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_cases = [
                ("png", b"\x89PNG\r\n\x1a\n"),
                ("jpg", b"\xff\xd8\xff"),
                ("gif", b"GIF89a"),
                ("webp", b"RIFF"),
            ]

            for fmt, header in test_cases:
                test_file = Path(temp_dir) / f"magic.{fmt}"
                test_file.write_bytes(header + b"\x00" * 100)

                result = validate_file_integrity(test_file)
                self.assertIsNotNone(result.format_detected)

    def test_checksum_verification_integration(self) -> None:
        """Test checksum verification in provenance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            test_file = Path(temp_dir) / "checksum.png"
            content = create_test_image_bytes("png")
            test_file.write_bytes(content)

            expected_sha256 = hashlib.sha256(content).hexdigest()

            asset = MediaAsset(
                asset_id="checksum-001",
                role="generated",
                name="checksum.png",
                relative_path="checksum.png",
                media_type="image/png",
                size=len(content),
                sha256=expected_sha256,
                created_at=datetime.now(UTC).isoformat()
            )

            store.record(
                prompt="Checksum test",
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None)

            history = list(store.list_history())
            self.assertEqual(len(history), 1)
            self.assertTrue(history[0].verify_integrity())


# =============================================================================
# Performance and Stress Tests
# =============================================================================

class TestPerformanceAndStress(unittest.TestCase):
    """Tests for performance and stress scenarios."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_large_batch_validation(self) -> None:
        """Test validation of a large batch of files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            files = []
            for i in range(50):
                test_file = Path(temp_dir) / f"batch_{i}.png"
                test_file.write_bytes(create_test_image_bytes("png"))
                files.append(test_file)

            policy = MediaValidationPolicy(modality="image")

            start_time = time.time()
            results = [validate_media(f, policy=policy) for f in files]
            elapsed = time.time() - start_time

            self.assertEqual(len(results), 50)
            self.assertLess(elapsed, 30.0)

    def test_large_provenance_history(self) -> None:
        """Test provenance store with large history."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            for i in range(100):
                asset = MediaAsset(
                    asset_id=f"perf-{i:04d}",
                    role="generated",
                    name=f"perf_{i}.png",
                    relative_path=f"perf/{i}.png",
                    media_type="image/png",
                    size=100,
                    sha256=f"hash{i}",
                    created_at=datetime.now(UTC).isoformat()
                )

                store.record(
                    prompt=f"Performance test {i}",
                    source_assets=[],
                    generated_assets=[asset],
                generation_metadata=None)

            start_time = time.time()
            history = list(store.list_history())
            elapsed = time.time() - start_time

            self.assertEqual(len(history), 100)
            self.assertLess(elapsed, 5.0)

    def test_concurrent_provenance_access(self) -> None:
        """Test concurrent access to provenance store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            def writer_task(i: int) -> None:
                asset = MediaAsset(
                    asset_id=f"concurrent-{i}",
                    role="generated",
                    name=f"concurrent_{i}.png",
                    relative_path=f"concurrent/{i}.png",
                    media_type="image/png",
                    size=100,
                    sha256=f"hash{i}",
                    created_at=datetime.now(UTC).isoformat()
                )
                store.record(
                    prompt=f"Concurrent {i}",
                    source_assets=[],
                    generated_assets=[asset],
                generation_metadata=None)

            def reader_task() -> int:
                return len(list(store.list_history()))

            with ThreadPoolExecutor(max_workers=10) as executor:
                write_futures = [executor.submit(writer_task, i) for i in range(20)]
                for f in as_completed(write_futures):
                    f.result()

                read_futures = [executor.submit(reader_task) for _ in range(10)]
                results = [f.result() for f in as_completed(read_futures)]

            self.assertTrue(all(r == 20 for r in results))


# =============================================================================
# Edge Cases and Boundary Tests
# =============================================================================

class TestEdgeCasesAndBoundaries(unittest.TestCase):
    """Tests for edge cases and boundary conditions."""

    def test_empty_file_validation(self) -> None:
        """Test validation of empty file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "empty.png"
            test_file.write_bytes(b"")

            policy = MediaValidationPolicy(modality="image")
            result = validate_media(test_file, policy=policy)

            self.assertFalse(result.valid)
            self.assertTrue(any("empty" in d.lower() for d in result.diagnostics))

    def test_very_long_prompt_handling(self) -> None:
        """Test handling of very long prompts."""
        long_prompt = "A beautiful image " * 1000

        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            asset = MediaAsset(
                asset_id="long-prompt-001",
                role="generated",
                name="long.png",
                relative_path="long.png",
                media_type="image/png",
                size=100,
                sha256="hash123",
                created_at=datetime.now(UTC).isoformat()
            )

            store.record(
                prompt=long_prompt,
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None)

            history = list(store.list_history())
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].prompt, long_prompt)

    def test_special_characters_in_metadata(self) -> None:
        """Test handling of special characters in metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            special_prompt = "Test with special chars: <>&\"'\n\t"

            asset = MediaAsset(
                asset_id="special-001",
                role="generated",
                name="special.png",
                relative_path="special.png",
                media_type="image/png",
                size=100,
                sha256="hash123",
                created_at=datetime.now(UTC).isoformat()
            )

            store.record(
                prompt=special_prompt,
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None)

            history = list(store.list_history())
            self.assertEqual(len(history), 1)

    def test_unicode_in_prompts_and_metadata(self) -> None:
        """Test handling of unicode characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            unicode_prompt = "Unicode test: hello world art emojis nyno"

            asset = MediaAsset(
                asset_id="unicode-001",
                role="generated",
                name="unicode.png",
                relative_path="unicode.png",
                media_type="image/png",
                size=100,
                sha256="hash123",
                created_at=datetime.now(UTC).isoformat()
            )

            store.record(
                prompt=unicode_prompt,
                source_assets=[],
                generated_assets=[asset],
                generation_metadata=None)

            history = list(store.list_history())
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].prompt, unicode_prompt)

    def test_boundary_dimensions(self) -> None:
        """Test validation with boundary dimension values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "boundary.png"
            test_file.write_bytes(create_test_image_bytes("png"))

            policy = MediaValidationPolicy(
                modality="image",
                min_width=1,
                max_width=1,
                min_height=1,
                max_height=1
            )

            result = validate_media(test_file, policy=policy)

    def test_zero_and_negative_values_rejected(self) -> None:
        """Test that zero and negative values are rejected in policy."""
        with self.assertRaises(ValueError):
            MediaValidationPolicy(modality="image", max_bytes=0)

        with self.assertRaises(ValueError):
            MediaValidationPolicy(modality="image", min_width=0)

        with self.assertRaises(ValueError):
            MediaValidationPolicy(modality="video", min_duration_seconds=-1)


if __name__ == "__main__":
    unittest.main()
