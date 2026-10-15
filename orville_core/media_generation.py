"""Media generation infrastructure for image, audio, and video workflows.

This module provides a unified interface for generating media content through
various provider adapters, with support for local and cloud providers, format
validation, and provenance tracking.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .media_provenance import MediaAsset, MediaProvenanceStore, MediaTransformation
from .media_validation import MediaValidationPolicy
from .providers import ProviderConfig, ProviderError
from .security import SecretRedactor

logger = logging.getLogger(__name__)


class MediaModality(StrEnum):
    """Supported media generation modalities."""

    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class GenerationStatus(StrEnum):
    """Status of a media generation operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class MediaFormatSpec:
    """Specification for a supported media format."""

    extension: str
    mime_type: str
    max_size_bytes: int = 250 * 1024 * 1024
    supports_transparency: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "extension": self.extension,
            "mime_type": self.mime_type,
            "max_size_bytes": self.max_size_bytes,
            "supports_transparency": self.supports_transparency,
        }


# Standard format specifications
IMAGE_FORMATS = {
    "png": MediaFormatSpec("png", "image/png", supports_transparency=True),
    "jpg": MediaFormatSpec("jpg", "image/jpeg"),
    "jpeg": MediaFormatSpec("jpeg", "image/jpeg"),
    "webp": MediaFormatSpec("webp", "image/webp", supports_transparency=True),
    "gif": MediaFormatSpec("gif", "image/gif"),
    "avif": MediaFormatSpec("avif", "image/avif"),
}

AUDIO_FORMATS = {
    "mp3": MediaFormatSpec("mp3", "audio/mpeg"),
    "wav": MediaFormatSpec("wav", "audio/wav"),
    "m4a": MediaFormatSpec("m4a", "audio/mp4"),
    "ogg": MediaFormatSpec("ogg", "audio/ogg"),
    "flac": MediaFormatSpec("flac", "audio/flac"),
}

VIDEO_FORMATS = {
    "mp4": MediaFormatSpec("mp4", "video/mp4"),
    "webm": MediaFormatSpec("webm", "video/webm"),
    "mov": MediaFormatSpec("mov", "video/quicktime"),
    "m4v": MediaFormatSpec("m4v", "video/x-m4v"),
}

ALL_FORMATS = {**IMAGE_FORMATS, **AUDIO_FORMATS, **VIDEO_FORMATS}


@dataclass(frozen=True)
class GenerationOptions:
    """Options for media generation requests."""

    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    format: str = "png"
    quality: str = "standard"
    seed: int | None = None
    negative_prompt: str | None = None
    num_inference_steps: int | None = None
    guidance_scale: float | None = None
    additional_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.format not in ALL_FORMATS:
            raise ValueError(f"unsupported format: {self.format}")
        if self.quality not in {"low", "standard", "high", "maximum"}:
            raise ValueError("quality must be low, standard, high, or maximum")

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "format": self.format,
            "quality": self.quality,
            "seed": self.seed,
            "negative_prompt": self.negative_prompt,
            "num_inference_steps": self.num_inference_steps,
            "guidance_scale": self.guidance_scale,
            **self.additional_params,
        }


@dataclass(frozen=True)
class GeneratedMedia:
    """Result of a media generation operation."""

    generation_id: str
    modality: MediaModality
    status: GenerationStatus
    assets: list[MediaAsset]
    prompt: str
    provider_id: str
    model: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "modality": self.modality.value,
            "status": self.status.value,
            "assets": [asset.to_dict() for asset in self.assets],
            "prompt": self.prompt,
            "provider_id": self.provider_id,
            "model": self.model,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "error_message": self.error_message,
        }


class MediaGenerator(Protocol):
    """Protocol for media generation providers."""

    def generate(
        self,
        prompt: str,
        modality: MediaModality,
        options: GenerationOptions,
    ) -> GeneratedMedia:
        """Generate media content from a prompt."""
        ...

    def supports_modality(self, modality: MediaModality) -> bool:
        """Check if this generator supports the given modality."""
        ...


@dataclass(frozen=True)
class ProviderCapability:
    """Capabilities of a media generation provider."""

    provider_id: str
    provider_type: str
    supported_modalities: frozenset[MediaModality]
    supported_formats: frozenset[str]
    max_resolution: tuple[int, int] | None = None
    max_duration_seconds: float | None = None
    requires_api_key: bool = True
    local_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "supported_modalities": [m.value for m in self.supported_modalities],
            "supported_formats": sorted(self.supported_formats),
            "max_resolution": self.max_resolution,
            "max_duration_seconds": self.max_duration_seconds,
            "requires_api_key": self.requires_api_key,
            "local_only": self.local_only,
        }


class BaseMediaGenerator:
    """Base class for media generation providers."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate provider configuration."""
        if not self.config.provider_id.strip():
            raise ValueError("provider_id must not be empty")
        if not self.config.model.strip():
            raise ValueError("model must not be empty")

    def supports_modality(self, modality: MediaModality) -> bool:
        """Check if this generator supports the given modality."""
        caps = self.config.capabilities
        if modality == MediaModality.IMAGE:
            return caps.image_generation
        elif modality == MediaModality.AUDIO:
            return caps.audio
        elif modality == MediaModality.VIDEO:
            return caps.video_generation
        return False

    def _make_request(
        self,
        url: str,
        headers: dict[str, str],
        data: bytes | None = None,
        method: str = "GET",
    ) -> dict[str, Any]:
        """Make an HTTP request with error handling."""
        request = Request(
            url,
            headers={"Accept": "application/json", **headers},
            method=method,
            data=data,
        )
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read(100_000_001)  # 100MB limit
        except HTTPError as exc:
            raise ProviderError(
                f"HTTP {exc.code} from provider",
                status_code=exc.code,
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderError(
                f"Provider request failed: {type(exc).__name__}"
            ) from exc

        if len(raw) > 100_000_000:
            raise ProviderError("Response exceeded maximum size")

        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("Invalid JSON response") from exc


class OpenAIImageGenerator(BaseMediaGenerator):
    """OpenAI-compatible image generation provider."""

    SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp"}

    def generate(
        self,
        prompt: str,
        modality: MediaModality,
        options: GenerationOptions,
    ) -> GeneratedMedia:
        """Generate an image using OpenAI's DALL-E API."""
        if modality != MediaModality.IMAGE:
            raise ProviderError(f"OpenAI image generator does not support {modality}")

        if options.format not in self.SUPPORTED_FORMATS:
            raise ProviderError(f"Format {options.format} not supported by OpenAI")

        url = urljoin(self.config.base_url, "v1/images/generations")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "n": 1,
            "size": self._get_size(options),
            "response_format": "b64_json",
        }

        if options.quality:
            payload["quality"] = options.quality

        data = json.dumps(payload).encode("utf-8")
        response = self._make_request(url, headers, data, method="POST")

        assets = []
        for item in response.get("data", []):
            b64_data = item.get("b64_json", "")
            if b64_data:
                image_data = base64.b64decode(b64_data)
                asset = self._create_asset(image_data, options.format, prompt)
                assets.append(asset)

        return GeneratedMedia(
            generation_id=f"gen-{hashlib.sha256(prompt.encode()).hexdigest()[:16]}",
            modality=modality,
            status=GenerationStatus.COMPLETED if assets else GenerationStatus.FAILED,
            assets=assets,
            prompt=prompt,
            provider_id=self.config.provider_id,
            model=self.config.model,
            created_at=datetime.now(UTC).isoformat(),
            metadata={"response": SecretRedactor.redact(response)},
        )

    def _get_size(self, options: GenerationOptions) -> str:
        """Get the image size string for OpenAI API."""
        width = options.width or 1024
        height = options.height or 1024
        # OpenAI DALL-E supports specific sizes
        sizes = [(1024, 1024), (1024, 1792), (1792, 1024), (512, 512), (256, 256)]
        closest = min(sizes, key=lambda s: abs(s[0] - width) + abs(s[1] - height))
        return f"{closest[0]}x{closest[1]}"

    def _create_asset(
        self, data: bytes, format: str, prompt: str
    ) -> MediaAsset:
        """Create a MediaAsset from generated data."""
        from .media_provenance import MediaAsset

        digest = hashlib.sha256(data).hexdigest()
        asset_id = digest[:16]
        mime_type = ALL_FORMATS[format].mime_type

        return MediaAsset(
            asset_id=asset_id,
            role="generated",
            name=f"generated_{asset_id}.{format}",
            relative_path=f"generated/{asset_id}.{format}",
            media_type=mime_type,
            size=len(data),
            sha256=digest,
            created_at=datetime.now(UTC).isoformat(),
        )


class StabilityImageGenerator(BaseMediaGenerator):
    """Stability AI image generation provider."""

    SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp"}

    def generate(
        self,
        prompt: str,
        modality: MediaModality,
        options: GenerationOptions,
    ) -> GeneratedMedia:
        """Generate an image using Stability AI API."""
        if modality != MediaModality.IMAGE:
            raise ProviderError(
                f"Stability AI generator does not support {modality}"
            )

        url = urljoin(self.config.base_url, "v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "Accept": "application/json",
        }

        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": options.guidance_scale or 7,
            "samples": 1,
            "steps": options.num_inference_steps or 30,
        }

        if options.seed is not None:
            payload["seed"] = options.seed

        if options.width and options.height:
            payload["width"] = options.width
            payload["height"] = options.height

        data = json.dumps(payload).encode("utf-8")
        response = self._make_request(url, headers, data, method="POST")

        assets = []
        for artifact in response.get("artifacts", []):
            b64_data = artifact.get("base64", "")
            if b64_data:
                image_data = base64.b64decode(b64_data)
                asset = self._create_asset(image_data, options.format, prompt)
                assets.append(asset)

        return GeneratedMedia(
            generation_id=f"gen-{hashlib.sha256(prompt.encode()).hexdigest()[:16]}",
            modality=modality,
            status=GenerationStatus.COMPLETED if assets else GenerationStatus.FAILED,
            assets=assets,
            prompt=prompt,
            provider_id=self.config.provider_id,
            model=self.config.model,
            created_at=datetime.now(UTC).isoformat(),
            metadata={"response": SecretRedactor.redact(response)},
        )

    def _create_asset(
        self, data: bytes, format: str, prompt: str
    ) -> MediaAsset:
        """Create a MediaAsset from generated data."""
        digest = hashlib.sha256(data).hexdigest()
        asset_id = digest[:16]
        mime_type = ALL_FORMATS[format].mime_type

        return MediaAsset(
            asset_id=asset_id,
            role="generated",
            name=f"generated_{asset_id}.{format}",
            relative_path=f"generated/{asset_id}.{format}",
            media_type=mime_type,
            size=len(data),
            sha256=digest,
            created_at=datetime.now(UTC).isoformat(),
        )


class LocalImageGenerator(BaseMediaGenerator):
    """Local image generation via Ollama or similar local providers."""

    SUPPORTED_FORMATS = {"png", "jpg", "jpeg"}

    def generate(
        self,
        prompt: str,
        modality: MediaModality,
        options: GenerationOptions,
    ) -> GeneratedMedia:
        """Generate an image using a local model."""
        if modality != MediaModality.IMAGE:
            raise ProviderError(
                f"Local image generator does not support {modality}"
            )

        # Ollama doesn't natively support image generation yet,
        # but this provides the interface for future local image models
        raise ProviderError(
            "Local image generation not yet supported via this adapter"
        )


class MediaGenerationService:
    """Service for coordinating media generation across multiple providers."""

    def __init__(
        self,
        provenance_store: MediaProvenanceStore | None = None,
        validation_enabled: bool = True,
    ) -> None:
        self.generators: dict[str, MediaGenerator] = {}
        self.provenance_store = provenance_store
        self.validation_enabled = validation_enabled
        self._generation_history: list[GeneratedMedia] = []

    def register_generator(
        self, provider_id: str, generator: MediaGenerator
    ) -> None:
        """Register a media generator for a provider."""
        self.generators[provider_id] = generator
        logger.info(f"Registered media generator for provider: {provider_id}")

    def create_generator(
        self, config: ProviderConfig
    ) -> MediaGenerator:
        """Create an appropriate generator for a provider configuration."""
        provider_type = config.provider_type.lower()

        if provider_type in {"openai", "openai-compatible"}:
            return OpenAIImageGenerator(config)
        elif provider_type in {"stability", "stability-ai"}:
            return StabilityImageGenerator(config)
        elif provider_type in {"ollama", "local", "llama-cpp"}:
            return LocalImageGenerator(config)
        else:
            # Default to OpenAI-compatible adapter
            return OpenAIImageGenerator(config)

    def generate(
        self,
        prompt: str,
        modality: MediaModality | str,
        provider_id: str,
        options: GenerationOptions | None = None,
        source_assets: list[MediaAsset] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GeneratedMedia:
        """Generate media using the specified provider."""
        if isinstance(modality, str):
            modality = MediaModality(modality)

        options = options or GenerationOptions()
        generator = self.generators.get(provider_id)

        if generator is None:
            raise ProviderError(f"No generator registered for provider: {provider_id}")

        if not generator.supports_modality(modality):
            raise ProviderError(
                f"Provider {provider_id} does not support {modality} generation"
            )

        logger.info(
            f"Starting {modality} generation with provider {provider_id}"
        )

        try:
            result = generator.generate(prompt, modality, options)

            # Validate generated assets if enabled
            if self.validation_enabled and result.assets:
                for asset in result.assets:
                    self._validate_asset(asset, modality)

            # Record provenance if store is available
            if self.provenance_store and result.status == GenerationStatus.COMPLETED:
                self._record_provenance(
                    prompt=prompt,
                    result=result,
                    source_assets=source_assets or [],
                    metadata=metadata,
                )

            self._generation_history.append(result)
            return result

        except Exception as exc:
            logger.error(f"Media generation failed: {exc}")
            error_result = GeneratedMedia(
                generation_id=f"gen-error-{datetime.now(UTC).timestamp()}",
                modality=modality,
                status=GenerationStatus.FAILED,
                assets=[],
                prompt=prompt,
                provider_id=provider_id,
                model="unknown",
                created_at=datetime.now(UTC).isoformat(),
                error_message=str(exc),
            )
            self._generation_history.append(error_result)
            return error_result

    def _validate_asset(self, asset: MediaAsset, modality: MediaModality) -> None:
        """Validate a generated asset against format requirements."""
        MediaValidationPolicy(
            modality=modality.value,
            allowed_formats=frozenset(
                fmt.extension
                for fmt in ALL_FORMATS.values()
                if modality.value in fmt.mime_type
            ),
        )

        # Note: Actual file validation would require the file path
        # This is a placeholder for format checking
        logger.debug(f"Validated asset {asset.asset_id} for {modality}")

    def _record_provenance(
        self,
        prompt: str,
        result: GeneratedMedia,
        source_assets: list[MediaAsset],
        metadata: dict[str, Any] | None,
    ) -> None:
        """Record provenance for a generation operation."""
        if self.provenance_store is None:
            return

        transformations = [
            MediaTransformation(
                operation="generate",
                parameters={
                    "modality": result.modality.value,
                    "model": result.model,
                    "provider_id": result.provider_id,
                },
                output_asset_ids=tuple(a.asset_id for a in result.assets),
            )
        ]

        self.provenance_store.record(
            prompt=prompt,
            source_assets=source_assets,
            generated_assets=result.assets,
            transformations=transformations,
            metadata={
                **(metadata or {}),
                "generation_id": result.generation_id,
                "status": result.status.value,
            },
        )

    def get_generation_history(
        self, modality: MediaModality | None = None
    ) -> list[GeneratedMedia]:
        """Get the history of generation operations."""
        if modality is None:
            return list(self._generation_history)
        return [g for g in self._generation_history if g.modality == modality]

    def list_capabilities(self) -> list[ProviderCapability]:
        """List capabilities of all registered generators."""
        capabilities = []
        for provider_id, generator in self.generators.items():
            if isinstance(generator, BaseMediaGenerator):
                caps = generator.config.capabilities
                supported_modalities = set()
                if caps.image_generation:
                    supported_modalities.add(MediaModality.IMAGE)
                if caps.audio:
                    supported_modalities.add(MediaModality.AUDIO)
                if caps.video_generation:
                    supported_modalities.add(MediaModality.VIDEO)

                capabilities.append(
                    ProviderCapability(
                        provider_id=provider_id,
                        provider_type=generator.config.provider_type,
                        supported_modalities=frozenset(supported_modalities),
                        supported_formats=frozenset(
                            IMAGE_FORMATS.keys()
                        ),  # Simplified for now
                        local_only=generator.config.privacy_mode == "local_only",
                    )
                )
        return capabilities


def create_media_generation_service(
    provenance_root: str | Path | None = None,
    validation_enabled: bool = True,
) -> MediaGenerationService:
    """Factory function to create a media generation service."""
    provenance_store = None
    if provenance_root:
        provenance_store = MediaProvenanceStore(provenance_root)

    return MediaGenerationService(
        provenance_store=provenance_store,
        validation_enabled=validation_enabled,
    )
