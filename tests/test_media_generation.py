"""Comprehensive tests for media generation infrastructure."""

from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

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
    MediaGenerator,
    MediaModality,
    OpenAIImageGenerator,
    ProviderCapability,
    StabilityImageGenerator,
    VIDEO_FORMATS,
    create_media_generation_service,
)
from orville_core.media_provenance import MediaAsset, MediaProvenanceStore
from orville_core.media_validation import MediaValidationPolicy
from orville_core.providers import ModelCapabilities, ProviderConfig, ProviderError


class TestMediaFormatSpec(unittest.TestCase):
    """Tests for MediaFormatSpec dataclass."""

    def test_image_format_spec_creation(self) -> None:
        spec = MediaFormatSpec("png", "image/png", supports_transparency=True)
        self.assertEqual(spec.extension, "png")
        self.assertEqual(spec.mime_type, "image/png")
        self.assertTrue(spec.supports_transparency)
        self.assertEqual(spec.max_size_bytes, 250 * 1024 * 1024)

    def test_format_spec_to_dict(self) -> None:
        spec = MediaFormatSpec("jpg", "image/jpeg")
        result = spec.to_dict()
        self.assertEqual(result["extension"], "jpg")
        self.assertEqual(result["mime_type"], "image/jpeg")
        self.assertFalse(result["supports_transparency"])


class TestGenerationOptions(unittest.TestCase):
    """Tests for GenerationOptions dataclass."""

    def test_default_options(self) -> None:
        opts = GenerationOptions()
        self.assertEqual(opts.format, "png")
        self.assertEqual(opts.quality, "standard")
        self.assertIsNone(opts.width)
        self.assertIsNone(opts.height)

    def test_custom_options(self) -> None:
        opts = GenerationOptions(
            width=1024,
            height=768,
            format="jpg",
            quality="high",
            seed=42,
            negative_prompt="blurry",
        )
        self.assertEqual(opts.width, 1024)
        self.assertEqual(opts.height, 768)
        self.assertEqual(opts.format, "jpg")
        self.assertEqual(opts.quality, "high")
        self.assertEqual(opts.seed, 42)
        self.assertEqual(opts.negative_prompt, "blurry")

    def test_invalid_format_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            GenerationOptions(format="invalid")
        self.assertIn("unsupported format", str(ctx.exception))

    def test_invalid_quality_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            GenerationOptions(quality="ultra")
        self.assertIn("quality must be", str(ctx.exception))

    def test_to_dict_includes_additional_params(self) -> None:
        opts = GenerationOptions(
            additional_params={"custom_key": "custom_value"}
        )
        result = opts.to_dict()
        self.assertEqual(result["custom_key"], "custom_value")


class TestMediaModality(unittest.TestCase):
    """Tests for MediaModality enum."""

    def test_modality_values(self) -> None:
        self.assertEqual(MediaModality.IMAGE.value, "image")
        self.assertEqual(MediaModality.AUDIO.value, "audio")
        self.assertEqual(MediaModality.VIDEO.value, "video")

    def test_modality_from_string(self) -> None:
        self.assertEqual(MediaModality("image"), MediaModality.IMAGE)
        self.assertEqual(MediaModality("audio"), MediaModality.AUDIO)
        self.assertEqual(MediaModality("video"), MediaModality.VIDEO)


class TestGenerationStatus(unittest.TestCase):
    """Tests for GenerationStatus enum."""

    def test_status_values(self) -> None:
        self.assertEqual(GenerationStatus.PENDING.value, "pending")
        self.assertEqual(GenerationStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(GenerationStatus.COMPLETED.value, "completed")
        self.assertEqual(GenerationStatus.FAILED.value, "failed")
        self.assertEqual(GenerationStatus.CANCELLED.value, "cancelled")


class TestFormatRegistries(unittest.TestCase):
    """Tests for format registry constants."""

    def test_image_formats(self) -> None:
        self.assertIn("png", IMAGE_FORMATS)
        self.assertIn("jpg", IMAGE_FORMATS)
        self.assertIn("jpeg", IMAGE_FORMATS)
        self.assertIn("webp", IMAGE_FORMATS)
        self.assertIn("gif", IMAGE_FORMATS)
        self.assertIn("avif", IMAGE_FORMATS)

    def test_audio_formats(self) -> None:
        self.assertIn("mp3", AUDIO_FORMATS)
        self.assertIn("wav", AUDIO_FORMATS)
        self.assertIn("m4a", AUDIO_FORMATS)
        self.assertIn("ogg", AUDIO_FORMATS)
        self.assertIn("flac", AUDIO_FORMATS)

    def test_video_formats(self) -> None:
        self.assertIn("mp4", VIDEO_FORMATS)
        self.assertIn("webm", VIDEO_FORMATS)
        self.assertIn("mov", VIDEO_FORMATS)
        self.assertIn("m4v", VIDEO_FORMATS)

    def test_all_formats_combined(self) -> None:
        total = len(IMAGE_FORMATS) + len(AUDIO_FORMATS) + len(VIDEO_FORMATS)
        self.assertEqual(len(ALL_FORMATS), total)


class TestBaseMediaGenerator(unittest.TestCase):
    """Tests for BaseMediaGenerator class."""

    def setUp(self) -> None:
        self.config = ProviderConfig(
            provider_id="test-provider",
            provider_type="test",
            model="test-model",
            base_url="https://api.test.com",
            api_key="test-key",
            capabilities=ModelCapabilities(
                image_generation=True,
                audio=True,
                video_generation=True,
            ),
        )

    def test_validates_config_on_init(self) -> None:
        generator = BaseMediaGenerator(self.config)
        self.assertEqual(generator.config.provider_id, "test-provider")

    def test_empty_provider_id_raises(self) -> None:
        # ProviderConfig validates before generator, so we test the error message
        with self.assertRaises(ValueError) as ctx:
            ProviderConfig(
                provider_id="",
                provider_type="test",
                model="test-model",
                base_url="https://api.test.com",
            )
        self.assertIn("must not be empty", str(ctx.exception))

    def test_supports_modality_image(self) -> None:
        generator = BaseMediaGenerator(self.config)
        self.assertTrue(generator.supports_modality(MediaModality.IMAGE))

    def test_supports_modality_audio(self) -> None:
        generator = BaseMediaGenerator(self.config)
        self.assertTrue(generator.supports_modality(MediaModality.AUDIO))

    def test_supports_modality_video(self) -> None:
        generator = BaseMediaGenerator(self.config)
        self.assertTrue(generator.supports_modality(MediaModality.VIDEO))

    def test_does_not_support_disabled_modality(self) -> None:
        config = ProviderConfig(
            provider_id="test-provider",
            provider_type="test",
            model="test-model",
            base_url="https://api.test.com",
            capabilities=ModelCapabilities(image_generation=False),
        )
        generator = BaseMediaGenerator(config)
        self.assertFalse(generator.supports_modality(MediaModality.IMAGE))


class TestOpenAIImageGenerator(unittest.TestCase):
    """Tests for OpenAIImageGenerator class."""

    def setUp(self) -> None:
        self.config = ProviderConfig(
            provider_id="openai-test",
            provider_type="openai",
            model="dall-e-3",
            base_url="https://api.openai.com",
            api_key="test-api-key",
            capabilities=ModelCapabilities(image_generation=True),
        )
        self.generator = OpenAIImageGenerator(self.config)

    def test_supports_image_modality(self) -> None:
        self.assertTrue(self.generator.supports_modality(MediaModality.IMAGE))

    def test_does_not_support_audio(self) -> None:
        self.assertFalse(self.generator.supports_modality(MediaModality.AUDIO))

    def test_does_not_support_video(self) -> None:
        self.assertFalse(self.generator.supports_modality(MediaModality.VIDEO))

    @patch("orville_core.media_generation.BaseMediaGenerator._make_request")
    def test_generate_image_success(self, mock_request: Mock) -> None:
        # Mock successful response
        image_data = b"fake-image-data"
        mock_request.return_value = {
            "data": [{"b64_json": base64.b64encode(image_data).decode()}]
        }

        options = GenerationOptions(format="png", width=1024, height=1024)
        result = self.generator.generate(
            "A beautiful sunset", MediaModality.IMAGE, options
        )

        self.assertEqual(result.status, GenerationStatus.COMPLETED)
        self.assertEqual(result.modality, MediaModality.IMAGE)
        self.assertEqual(result.provider_id, "openai-test")
        self.assertEqual(result.model, "dall-e-3")
        self.assertEqual(len(result.assets), 1)
        self.assertEqual(result.assets[0].size, len(image_data))

    @patch("orville_core.media_generation.BaseMediaGenerator._make_request")
    def test_generate_image_no_data(self, mock_request: Mock) -> None:
        mock_request.return_value = {"data": []}

        options = GenerationOptions()
        result = self.generator.generate("Test prompt", MediaModality.IMAGE, options)

        self.assertEqual(result.status, GenerationStatus.FAILED)
        self.assertEqual(len(result.assets), 0)

    def test_unsupported_modality_raises(self) -> None:
        options = GenerationOptions()
        with self.assertRaises(ProviderError) as ctx:
            self.generator.generate("Test", MediaModality.AUDIO, options)
        self.assertIn("does not support", str(ctx.exception))

    def test_unsupported_format_raises(self) -> None:
        # OpenAI doesn't support all formats
        with self.assertRaises(ProviderError):
            options = GenerationOptions(format="gif")
            self.generator.generate("Test", MediaModality.IMAGE, options)

    def test_get_size_returns_valid_size(self) -> None:
        options = GenerationOptions(width=1024, height=1024)
        size = self.generator._get_size(options)
        self.assertEqual(size, "1024x1024")

    def test_get_size_defaults_to_1024(self) -> None:
        options = GenerationOptions()
        size = self.generator._get_size(options)
        self.assertEqual(size, "1024x1024")


class TestStabilityImageGenerator(unittest.TestCase):
    """Tests for StabilityImageGenerator class."""

    def setUp(self) -> None:
        self.config = ProviderConfig(
            provider_id="stability-test",
            provider_type="stability",
            model="stable-diffusion-xl",
            base_url="https://api.stability.ai",
            api_key="test-api-key",
            capabilities=ModelCapabilities(image_generation=True),
        )
        self.generator = StabilityImageGenerator(self.config)

    @patch("orville_core.media_generation.BaseMediaGenerator._make_request")
    def test_generate_image_success(self, mock_request: Mock) -> None:
        image_data = b"fake-stability-image"
        mock_request.return_value = {
            "artifacts": [{"base64": base64.b64encode(image_data).decode()}]
        }

        options = GenerationOptions(
            format="png",
            seed=42,
            guidance_scale=7.5,
            num_inference_steps=50,
        )
        result = self.generator.generate(
            "A futuristic city", MediaModality.IMAGE, options
        )

        self.assertEqual(result.status, GenerationStatus.COMPLETED)
        self.assertEqual(len(result.assets), 1)

    @patch("orville_core.media_generation.BaseMediaGenerator._make_request")
    def test_generate_with_custom_dimensions(self, mock_request: Mock) -> None:
        mock_request.return_value = {"artifacts": []}

        options = GenerationOptions(width=512, height=768)
        self.generator.generate("Test", MediaModality.IMAGE, options)

        # Verify the request was made with correct dimensions
        call_args = mock_request.call_args
        payload = json.loads(call_args[0][2].decode())
        self.assertEqual(payload["width"], 512)
        self.assertEqual(payload["height"], 768)


class TestLocalImageGenerator(unittest.TestCase):
    """Tests for LocalImageGenerator class."""

    def setUp(self) -> None:
        self.config = ProviderConfig(
            provider_id="local-test",
            provider_type="ollama",
            model="llava",
            base_url="http://localhost:11434",
            capabilities=ModelCapabilities(image_generation=True),
        )
        self.generator = LocalImageGenerator(self.config)

    def test_raises_not_implemented(self) -> None:
        options = GenerationOptions()
        with self.assertRaises(ProviderError) as ctx:
            self.generator.generate("Test", MediaModality.IMAGE, options)
        self.assertIn("not yet supported", str(ctx.exception))


class TestMediaGenerationService(unittest.TestCase):
    """Tests for MediaGenerationService class."""

    def setUp(self) -> None:
        self.service = MediaGenerationService(validation_enabled=True)
        self.mock_generator = MagicMock(spec=MediaGenerator)
        self.mock_generator.supports_modality.return_value = True

    def test_register_generator(self) -> None:
        self.service.register_generator("test-provider", self.mock_generator)
        self.assertIn("test-provider", self.service.generators)

    def test_create_generator_openai(self) -> None:
        config = ProviderConfig(
            provider_id="openai",
            provider_type="openai",
            model="dall-e-3",
            base_url="https://api.openai.com",
        )
        generator = self.service.create_generator(config)
        self.assertIsInstance(generator, OpenAIImageGenerator)

    def test_create_generator_stability(self) -> None:
        config = ProviderConfig(
            provider_id="stability",
            provider_type="stability",
            model="sd-xl",
            base_url="https://api.stability.ai",
        )
        generator = self.service.create_generator(config)
        self.assertIsInstance(generator, StabilityImageGenerator)

    def test_create_generator_local(self) -> None:
        config = ProviderConfig(
            provider_id="ollama",
            provider_type="ollama",
            model="llava",
            base_url="http://localhost:11434",
        )
        generator = self.service.create_generator(config)
        self.assertIsInstance(generator, LocalImageGenerator)

    def test_generate_unregistered_provider_raises(self) -> None:
        with self.assertRaises(ProviderError) as ctx:
            self.service.generate(
                "Test prompt", MediaModality.IMAGE, "unknown-provider"
            )
        self.assertIn("No generator registered", str(ctx.exception))

    def test_generate_unsupported_modality_raises(self) -> None:
        self.mock_generator.supports_modality.return_value = False
        self.service.register_generator("test", self.mock_generator)

        with self.assertRaises(ProviderError) as ctx:
            self.service.generate("Test", MediaModality.VIDEO, "test")
        self.assertIn("does not support", str(ctx.exception))

    def test_generate_success(self) -> None:
        from orville_core.media_generation import GeneratedMedia

        mock_result = GeneratedMedia(
            generation_id="test-123",
            modality=MediaModality.IMAGE,
            status=GenerationStatus.COMPLETED,
            assets=[],
            prompt="Test",
            provider_id="test",
            model="test-model",
            created_at="2024-01-01T00:00:00",
        )
        self.mock_generator.generate.return_value = mock_result
        self.service.register_generator("test", self.mock_generator)

        result = self.service.generate("Test prompt", MediaModality.IMAGE, "test")

        self.assertEqual(result.generation_id, "test-123")
        self.mock_generator.generate.assert_called_once()

    def test_generate_records_to_history(self) -> None:
        from orville_core.media_generation import GeneratedMedia

        mock_result = GeneratedMedia(
            generation_id="test-123",
            modality=MediaModality.IMAGE,
            status=GenerationStatus.COMPLETED,
            assets=[],
            prompt="Test",
            provider_id="test",
            model="test-model",
            created_at="2024-01-01T00:00:00",
        )
        self.mock_generator.generate.return_value = mock_result
        self.service.register_generator("test", self.mock_generator)

        self.service.generate("Test", MediaModality.IMAGE, "test")
        history = self.service.get_generation_history()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].generation_id, "test-123")

    def test_get_generation_history_filtered_by_modality(self) -> None:
        from orville_core.media_generation import GeneratedMedia

        self.service._generation_history = [
            GeneratedMedia(
                generation_id="img-1",
                modality=MediaModality.IMAGE,
                status=GenerationStatus.COMPLETED,
                assets=[],
                prompt="Image",
                provider_id="test",
                model="model",
                created_at="2024-01-01T00:00:00",
            ),
            GeneratedMedia(
                generation_id="audio-1",
                modality=MediaModality.AUDIO,
                status=GenerationStatus.COMPLETED,
                assets=[],
                prompt="Audio",
                provider_id="test",
                model="model",
                created_at="2024-01-01T00:00:00",
            ),
        ]

        image_history = self.service.get_generation_history(MediaModality.IMAGE)
        self.assertEqual(len(image_history), 1)
        self.assertEqual(image_history[0].generation_id, "img-1")

    def test_generate_with_string_modality(self) -> None:
        mock_result = MagicMock()
        mock_result.status = GenerationStatus.COMPLETED
        mock_result.assets = []
        self.mock_generator.generate.return_value = mock_result
        self.service.register_generator("test", self.mock_generator)

        result = self.service.generate("Test", "image", "test")
        self.assertIsNotNone(result)

    def test_generate_handles_exception(self) -> None:
        self.mock_generator.generate.side_effect = Exception("Generation failed")
        self.service.register_generator("test", self.mock_generator)

        result = self.service.generate("Test", MediaModality.IMAGE, "test")

        self.assertEqual(result.status, GenerationStatus.FAILED)
        self.assertEqual(result.error_message, "Generation failed")

    def test_list_capabilities_empty(self) -> None:
        capabilities = self.service.list_capabilities()
        self.assertEqual(capabilities, [])

    def test_list_capabilities_with_generators(self) -> None:
        config = ProviderConfig(
            provider_id="test",
            provider_type="openai",
            model="dall-e-3",
            base_url="https://api.openai.com",
            capabilities=ModelCapabilities(image_generation=True, audio=True),
            privacy_mode="local_only",
        )
        generator = OpenAIImageGenerator(config)
        self.service.register_generator("test", generator)

        capabilities = self.service.list_capabilities()
        self.assertEqual(len(capabilities), 1)
        self.assertEqual(capabilities[0].provider_id, "test")
        self.assertTrue(capabilities[0].local_only)


class TestMediaGenerationServiceWithProvenance(unittest.TestCase):
    """Tests for MediaGenerationService with provenance tracking."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.provenance_root = Path(self.temp_dir) / "provenance"
        self.provenance_store = MediaProvenanceStore(self.provenance_root)
        self.service = MediaGenerationService(
            provenance_store=self.provenance_store,
            validation_enabled=True,
        )

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_records_provenance(self) -> None:
        from orville_core.media_generation import GeneratedMedia

        mock_generator = MagicMock(spec=MediaGenerator)
        mock_generator.supports_modality.return_value = True

        # Create a mock asset
        mock_asset = MediaAsset(
            asset_id="test-asset-123",
            role="generated",
            name="test.png",
            relative_path="generated/test.png",
            media_type="image/png",
            size=1000,
            sha256="abc123",
            created_at="2024-01-01T00:00:00",
        )

        mock_result = GeneratedMedia(
            generation_id="test-123",
            modality=MediaModality.IMAGE,
            status=GenerationStatus.COMPLETED,
            assets=[mock_asset],
            prompt="Test prompt",
            provider_id="test",
            model="test-model",
            created_at="2024-01-01T00:00:00",
        )
        mock_generator.generate.return_value = mock_result
        self.service.register_generator("test", mock_generator)

        self.service.generate("Test prompt", MediaModality.IMAGE, "test")

        # Verify provenance was recorded
        history = self.provenance_store.list_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].prompt, "Test prompt")


class TestCreateMediaGenerationService(unittest.TestCase):
    """Tests for the factory function."""

    def test_create_without_provenance(self) -> None:
        service = create_media_generation_service()
        self.assertIsNone(service.provenance_store)

    def test_create_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = create_media_generation_service(provenance_root=temp_dir)
            self.assertIsNotNone(service.provenance_store)

    def test_create_with_validation_disabled(self) -> None:
        service = create_media_generation_service(validation_enabled=False)
        self.assertFalse(service.validation_enabled)


class TestProviderCapability(unittest.TestCase):
    """Tests for ProviderCapability dataclass."""

    def test_capability_creation(self) -> None:
        cap = ProviderCapability(
            provider_id="test",
            provider_type="openai",
            supported_modalities=frozenset([MediaModality.IMAGE]),
            supported_formats=frozenset(["png", "jpg"]),
            max_resolution=(1024, 1024),
            max_duration_seconds=60.0,
            requires_api_key=True,
            local_only=False,
        )
        self.assertEqual(cap.provider_id, "test")
        self.assertEqual(cap.max_resolution, (1024, 1024))

    def test_capability_to_dict(self) -> None:
        cap = ProviderCapability(
            provider_id="test",
            provider_type="local",
            supported_modalities=frozenset([MediaModality.IMAGE, MediaModality.AUDIO]),
            supported_formats=frozenset(["png"]),
            local_only=True,
        )
        result = cap.to_dict()
        self.assertEqual(result["provider_id"], "test")
        self.assertIn("image", result["supported_modalities"])
        self.assertIn("audio", result["supported_modalities"])
        self.assertTrue(result["local_only"])


class TestIntegrationPatterns(unittest.TestCase):
    """Integration-style tests following project patterns."""

    def test_full_generation_workflow(self) -> None:
        """Test a complete generation workflow with all components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create service with provenance
            service = create_media_generation_service(
                provenance_root=temp_dir,
                validation_enabled=True,
            )

            # Create and register a mock generator
            mock_generator = MagicMock(spec=MediaGenerator)
            mock_generator.supports_modality.return_value = True

            mock_asset = MediaAsset(
                asset_id="gen-123",
                role="generated",
                name="output.png",
                relative_path="generated/output.png",
                media_type="image/png",
                size=5000,
                sha256="def456",
                created_at="2024-01-01T00:00:00",
            )

            from orville_core.media_generation import GeneratedMedia

            mock_result = GeneratedMedia(
                generation_id="workflow-test",
                modality=MediaModality.IMAGE,
                status=GenerationStatus.COMPLETED,
                assets=[mock_asset],
                prompt="A serene landscape",
                provider_id="test-provider",
                model="test-model",
                created_at="2024-01-01T00:00:00",
                metadata={"seed": 42},
            )
            mock_generator.generate.return_value = mock_result

            service.register_generator("test-provider", mock_generator)

            # Execute generation
            options = GenerationOptions(
                width=1024,
                height=768,
                format="png",
                quality="high",
            )
            result = service.generate(
                prompt="A serene landscape",
                modality=MediaModality.IMAGE,
                provider_id="test-provider",
                options=options,
                metadata={"workflow": "integration-test"},
            )

            # Verify results
            self.assertEqual(result.status, GenerationStatus.COMPLETED)
            self.assertEqual(len(result.assets), 1)

            # Verify history
            history = service.get_generation_history()
            self.assertEqual(len(history), 1)

            # Verify provenance
            provenance = service.provenance_store.list_history()
            self.assertEqual(len(provenance), 1)

    def test_error_handling_workflow(self) -> None:
        """Test error handling in generation workflow."""
        service = create_media_generation_service()

        mock_generator = MagicMock(spec=MediaGenerator)
        mock_generator.supports_modality.return_value = True
        mock_generator.generate.side_effect = ProviderError("API rate limit exceeded")

        service.register_generator("failing-provider", mock_generator)

        result = service.generate(
            prompt="Test",
            modality=MediaModality.IMAGE,
            provider_id="failing-provider",
        )

        self.assertEqual(result.status, GenerationStatus.FAILED)
        self.assertIn("rate limit", result.error_message)

    def test_modality_routing(self) -> None:
        """Test that different modalities route correctly."""
        service = create_media_generation_service()

        # Create separate generators for each modality
        image_gen = MagicMock(spec=MediaGenerator)
        image_gen.supports_modality = lambda m: m == MediaModality.IMAGE

        audio_gen = MagicMock(spec=MediaGenerator)
        audio_gen.supports_modality = lambda m: m == MediaModality.AUDIO

        service.register_generator("image-provider", image_gen)
        service.register_generator("audio-provider", audio_gen)

        from orville_core.media_generation import GeneratedMedia

        # Mock returns
        image_result = GeneratedMedia(
            generation_id="img-1",
            modality=MediaModality.IMAGE,
            status=GenerationStatus.COMPLETED,
            assets=[],
            prompt="Image",
            provider_id="image-provider",
            model="img-model",
            created_at="2024-01-01T00:00:00",
        )
        audio_result = GeneratedMedia(
            generation_id="aud-1",
            modality=MediaModality.AUDIO,
            status=GenerationStatus.COMPLETED,
            assets=[],
            prompt="Audio",
            provider_id="audio-provider",
            model="aud-model",
            created_at="2024-01-01T00:00:00",
        )

        image_gen.generate.return_value = image_result
        audio_gen.generate.return_value = audio_result

        # Test image generation
        img = service.generate("Create image", MediaModality.IMAGE, "image-provider")
        self.assertEqual(img.modality, MediaModality.IMAGE)

        # Test audio generation
        aud = service.generate("Create audio", MediaModality.AUDIO, "audio-provider")
        self.assertEqual(aud.modality, MediaModality.AUDIO)


if __name__ == "__main__":
    unittest.main()
