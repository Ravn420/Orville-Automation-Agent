# Orville Media Workflow Guide

## Overview

The Orville Media Workflow system provides comprehensive capabilities for generating, validating, and tracking media assets. This guide covers the complete media lifecycle from generation through provenance tracking.

## Table of Contents

1. [Media Capabilities](#media-capabilities)
2. [Generation Workflow](#generation-workflow)
3. [Validation Procedures](#validation-procedures)
4. [Provenance Tracking](#provenance-tracking)
5. [API Usage](#api-usage)
6. [Troubleshooting](#troubleshooting)

## Media Capabilities

### Supported Media Types

| Modality | Formats | Description |
|----------|---------|-------------|
| Image | PNG, JPG, GIF, WEBP | Static image generation |
| Audio | MP3, WAV | Audio synthesis and generation |
| Video | MP4, WEBM | Video generation and editing |

### Generation Providers

The system supports multiple generation providers:

- **OpenAI**: DALL-E for images, GPT-4 for audio
- **Stability AI**: Stable Diffusion for images
- **Local**: On-premise models for privacy-sensitive workloads

## Generation Workflow

### Basic Image Generation

```python
from orville_core.media_generation import GenerationOptions
from orville_core.api import create_app
from fastapi.testclient import TestClient

# Create generation options
options = GenerationOptions(
    width=1024,
    height=768,
    format="png",
    quality="high"
)

# Via API
app = create_app(api_token="your-token")
client = TestClient(app)

response = client.post(
    "/api/v1/media/generate",
    headers={"Authorization": "Bearer your-token"},
    json={
        "modality": "image",
        "prompt": "A serene mountain landscape at sunset",
        "options": {
            "width": 1024,
            "height": 768,
            "format": "png"
        }
    }
)

result = response.json()
media_id = result["id"]
```

### Multi-Modality Generation

```python
# Generate multiple media types in a single workflow
response = client.post(
    "/api/v1/media/generate",
    headers={"Authorization": "Bearer your-token"},
    json={
        "modality": "image",
        "prompt": "A futuristic cityscape",
        "options": {
            "width": 1920,
            "height": 1080,
            "format": "png",
            "variations": 3
        }
    }
)
```

### Provider Selection

```python
# Specify preferred provider
response = client.post(
    "/api/v1/media/generate",
    headers={"Authorization": "Bearer your-token"},
    json={
        "modality": "image",
        "prompt": "Abstract art",
        "provider": "stability",  # or "openai", "local"
        "options": {"width": 1024, "height": 1024}
    }
)
```

## Validation Procedures

### File Validation

```python
from orville_core.media_validation import (
    validate_media,
    MediaValidationPolicy,
    validate_file_integrity,
    validate_content_safety
)
from pathlib import Path

# Create validation policy
policy = MediaValidationPolicy(
    modality="image",
    allowed_formats=frozenset({"png", "jpg", "webp"}),
    min_width=256,
    max_width=4096,
    min_height=256,
    max_height=4096,
    max_bytes=10 * 1024 * 1024,  # 10MB
    require_license=True,
    require_rights_holder=True
)

# Validate a file
result = validate_media(Path("generated_image.png"), policy=policy)

if result.valid:
    print("File is valid")
    print(f"Format: {result.format_specific.format}")
    print(f"Dimensions: {result.format_specific.width}x{result.format_specific.height}")
else:
    print("Validation failed:")
    for diagnostic in result.diagnostics:
        print(f"  - {diagnostic}")
```

### Content Safety Check

```python
# Check content safety
safety_result = validate_content_safety(Path("image.png"))

if safety_result.level == ContentSafetyLevel.SAFE:
    print("Content is safe")
elif safety_result.level == ContentSafetyLevel.WARNING:
    print("Content has warnings:", safety_result.warnings)
else:
    print("Content flagged:", safety_result.flags)
```

### File Integrity

```python
# Verify file integrity with checksum
integrity_result = validate_file_integrity(
    Path("image.png"),
    compute_checksum=True
)

if integrity_result.valid:
    print(f"SHA256: {integrity_result.checksum_sha256}")
    print(f"Format detected: {integrity_result.format_detected}")
```

## Provenance Tracking

### Recording Generation History

```python
from orville_core.media_provenance import (
    MediaProvenanceStore,
    MediaAsset,
    LicenseTerms,
    LicenseType,
    GenerationMetadata,
    GenerationSource
)
from datetime import datetime, UTC

# Initialize store
store = MediaProvenanceStore("/path/to/provenance/storage")

# Create asset record
asset = MediaAsset(
    asset_id="asset-001",
    role="generated",
    name="landscape.png",
    relative_path="generated/landscape.png",
    media_type="image/png",
    size=1024000,
    sha256="abc123...",
    created_at=datetime.now(UTC).isoformat()
)

# Define license terms
license_terms = LicenseTerms(
    license_type=LicenseType.CC_BY_SA,
    holder="Your Organization",
    attribution_required=True,
    commercial_use_allowed=True,
    modification_allowed=True,
    share_alike=True
)

# Record generation
record = store.record(
    prompt="A serene mountain landscape at sunset",
    source_assets=[],  # No source assets for AI generation
    generated_assets=[asset],
    generation_metadata=GenerationMetadata(
        generation_id="gen-001",
        source=GenerationSource.AI_GENERATED,
        model="dall-e-3",
        provider_id="openai",
        parameters={"width": 1024, "height": 768}
    ),
    license_terms=license_terms
)

print(f"Recorded with history ID: {record.history_id}")
```

### Verifying Provenance

```python
# List all history records
for record in store.list_history():
    print(f"History ID: {record.history_id}")
    print(f"Prompt: {record.prompt}")
    print(f"Created: {record.created_at}")
    print(f"Assets: {len(record.generated_assets)}")

# Verify integrity
is_valid = record.verify_integrity()
print(f"Integrity check: {'PASSED' if is_valid else 'FAILED'}")
```

### Rights Verification

```python
from orville_core.media_provenance import RightsVerification, RightsStatus

# Record rights verification
verification = RightsVerification(
    verification_id="verify-001",
    asset_id="asset-001",
    status=RightsStatus.VERIFIED,
    verified_by="legal-team",
    verified_at=datetime.now(UTC).isoformat(),
    verification_method="manual_review",
    notes="All rights confirmed"
)

store.record_verification(verification)

# List verifications for an asset
for v in store.list_verifications("asset-001"):
    print(f"Status: {v.status.value}")
    print(f"Verified by: {v.verified_by}")
    print(f"Date: {v.verified_at}")
```

## API Usage

### Authentication

All media API endpoints require authentication via Bearer token:

```bash
curl -X POST "http://localhost:8000/api/v1/media/generate" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "modality": "image",
    "prompt": "A futuristic cityscape",
    "options": {"width": 1024, "height": 768}
  }'
```

### Endpoints

#### Generate Media

```http
POST /api/v1/media/generate
```

Request body:
```json
{
  "modality": "image",
  "prompt": "Description of desired media",
  "provider": "openai",
  "options": {
    "width": 1024,
    "height": 768,
    "format": "png",
    "quality": "high"
  }
}
```

#### Validate Media

```http
POST /api/v1/media/validate
```

Request body:
```json
{
  "file_path": "/path/to/media.png",
  "policy": {
    "modality": "image",
    "allowed_formats": ["png", "jpg"],
    "max_bytes": 10485760
  }
}
```

#### Get Media

```http
GET /api/v1/media/{media_id}
```

#### Get Provenance

```http
GET /api/v1/media/{media_id}/provenance
```

#### Verify Media

```http
POST /api/v1/media/{media_id}/verify
```

### Response Formats

#### Successful Generation

```json
{
  "id": "media-001",
  "modality": "image",
  "status": "completed",
  "url": "/media/media-001.png",
  "metadata": {
    "width": 1024,
    "height": 768,
    "format": "png"
  }
}
```

#### Validation Result

```json
{
  "valid": true,
  "format": "png",
  "width": 1024,
  "height": 768,
  "size": 1024000,
  "checksum": "sha256:abc123...",
  "diagnostics": []
}
```

## Troubleshooting

### Common Issues

#### Generation Failures

**Issue**: `400 Bad Request` on generation

**Solutions**:
- Verify the modality is supported (image, audio, video)
- Check that prompt is not empty
- Ensure options match the modality requirements
- Verify API token is valid

```python
# Debug generation issues
response = client.post("/api/v1/media/generate", ...)
if response.status_code != 200:
    print(f"Error: {response.json()}")
```

#### Validation Failures

**Issue**: File validation fails unexpectedly

**Solutions**:
- Check file format matches declared format
- Verify file is not corrupted
- Ensure file size is within policy limits
- Check magic numbers match expected format

```python
# Debug validation
result = validate_media(file_path, policy=policy)
if not result.valid:
    for diag in result.diagnostics:
        print(f"Diagnostic: {diag}")
```

#### Provenance Issues

**Issue**: Cannot record or retrieve provenance

**Solutions**:
- Verify storage directory exists and is writable
- Check asset IDs are unique
- Ensure all required fields are provided
- Verify JSON serialization of metadata

```python
# Debug provenance
import traceback
try:
    store.record(...)
except Exception as e:
    traceback.print_exc()
```

### Performance Tuning

#### Batch Validation

For large batches, use concurrent validation:

```python
from concurrent.futures import ThreadPoolExecutor

def validate_file(file_path):
    return validate_media(file_path, policy=policy)

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(validate_file, file_paths))
```

#### Provenance Storage

For high-volume operations:
- Use SSD storage for provenance database
- Enable compression for large media files
- Implement cleanup policies for old records
- Consider sharding for very large deployments

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 400 | Invalid request | Check request parameters |
| 401 | Unauthorized | Verify API token |
| 404 | Media not found | Check media ID |
| 422 | Validation error | Review validation policy |
| 500 | Server error | Check server logs |

### Logging

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Orville uses standard Python logging
logger = logging.getLogger("orville.media")
logger.setLevel(logging.DEBUG)
```

## Best Practices

1. **Always validate** media before storage
2. **Record provenance** for all generated media
3. **Use appropriate licenses** for your use case
4. **Implement retry logic** for generation failures
5. **Monitor validation** metrics for quality assurance
6. **Backup provenance** data regularly
7. **Test with small batches** before large operations

## Examples

### Complete Workflow Example

```python
"""Complete media workflow example."""
from orville_core.media_generation import GenerationOptions
from orville_core.media_validation import validate_media, MediaValidationPolicy
from orville_core.media_provenance import (
    MediaProvenanceStore, MediaAsset, LicenseTerms,
    LicenseType, GenerationMetadata, GenerationSource
)
from orville_core.api import create_app
from fastapi.testclient import TestClient
from pathlib import Path
from datetime import datetime, UTC
import hashlib

# 1. Generate media
app = create_app(api_token="demo-token")
client = TestClient(app)

response = client.post(
    "/api/v1/media/generate",
    headers={"Authorization": "Bearer demo-token"},
    json={
        "modality": "image",
        "prompt": "A beautiful sunset over mountains",
        "options": {"width": 1024, "height": 768, "format": "png"}
    }
)

if response.status_code == 200:
    result = response.json()
    media_id = result["id"]
    media_path = Path(result["url"])

    # 2. Validate media
    policy = MediaValidationPolicy(
        modality="image",
        allowed_formats=frozenset({"png"}),
        min_width=512,
        max_width=2048,
        min_height=512,
        max_height=2048
    )

    validation = validate_media(media_path, policy=policy)

    if validation.valid:
        # 3. Record provenance
        store = MediaProvenanceStore("./provenance")

        content = media_path.read_bytes()
        asset = MediaAsset(
            asset_id=media_id,
            role="generated",
            name=media_path.name,
            relative_path=str(media_path),
            media_type="image/png",
            size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            created_at=datetime.now(UTC).isoformat()
        )

        store.record(
            prompt="A beautiful sunset over mountains",
            source_assets=[],
            generated_assets=[asset],
            generation_metadata=GenerationMetadata(
                generation_id=f"gen-{media_id}",
                source=GenerationSource.AI_GENERATED,
                model="dall-e-3",
                provider_id="openai",
                parameters={"width": 1024, "height": 768}
            ),
            license_terms=LicenseTerms(
                license_type=LicenseType.CC_BY,
                holder="Demo User",
                attribution_required=True
            )
        )

        print(f"Successfully processed media: {media_id}")
    else:
        print(f"Validation failed: {validation.diagnostics}")
else:
    print(f"Generation failed: {response.json()}")
```

---

For more information, see:
- [API Reference](API_REFERENCE.md)
- [Media Runbook](MEDIA_RUNBOOK.md)
- [Architecture Documentation](ARCHITECTURE.md)
