"""Comprehensive tests for media provenance, licensing, and rights management functionality."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from orville_core.media_provenance import (
    GenerationMetadata,
    GenerationSource,
    LicenseTerms,
    LicenseType,
    MediaAsset,
    MediaHistoryRecord,
    MediaProvenanceStore,
    MediaTransformation,
    ProvenanceExportFormat,
    RightsStatus,
    RightsVerification,
)


class MediaProvenanceTests(unittest.TestCase):
    """Basic provenance tests."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = MediaProvenanceStore(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_store_initialization(self) -> None:
        """Test that MediaProvenanceStore initializes correctly."""
        self.assertTrue(self.store.root.exists())
        self.assertTrue(self.store.assets_root.exists())
        self.assertEqual(self.store.max_asset_bytes, 250 * 1024 * 1024)

    def test_store_initialization_with_custom_max_bytes(self) -> None:
        """Test store initialization with custom max asset bytes."""
        store = MediaProvenanceStore(self.temp_dir.name, max_asset_bytes=1024)
        self.assertEqual(store.max_asset_bytes, 1024)

    def test_store_initialization_invalid_max_bytes(self) -> None:
        """Test that store raises ValueError for invalid max_asset_bytes."""
        with self.assertRaises(ValueError):
            MediaProvenanceStore(self.temp_dir.name, max_asset_bytes=0)
        with self.assertRaises(ValueError):
            MediaProvenanceStore(self.temp_dir.name, max_asset_bytes=-1)


class LicenseManagementTests(unittest.TestCase):
    """License functionality tests."""

    def test_license_terms_creation(self) -> None:
        """Test creating LicenseTerms with all fields."""
        license_terms = LicenseTerms(
            license_type=LicenseType.CC_BY,
            holder="Test Holder",
            holder_contact="test@example.com",
            attribution_required=True,
            attribution_text="Attribution text",
            commercial_use_allowed=True,
            modification_allowed=True,
            share_alike_required=False,
            expiration_date=None,
            territory_restrictions=["US", "UK"],
            usage_restrictions=["No political use"],
            custom_terms=None,
            license_url="https://example.com/license",
            registration_number="REG123",
        )
        self.assertEqual(license_terms.license_type, LicenseType.CC_BY)
        self.assertEqual(license_terms.holder, "Test Holder")
        self.assertTrue(license_terms.attribution_required)

    def test_license_terms_to_dict(self) -> None:
        """Test LicenseTerms serialization to dict."""
        license_terms = LicenseTerms(
            license_type=LicenseType.MIT,
            holder="MIT Holder",
        )
        data = license_terms.to_dict()
        self.assertEqual(data["license_type"], "mit")
        self.assertEqual(data["holder"], "MIT Holder")
        self.assertIn("attribution_required", data)

    def test_license_terms_from_dict(self) -> None:
        """Test LicenseTerms deserialization from dict."""
        data = {
            "license_type": "apache-2.0",
            "holder": "Apache Holder",
            "attribution_required": False,
            "commercial_use_allowed": True,
        }
        license_terms = LicenseTerms.from_dict(data)
        self.assertEqual(license_terms.license_type, LicenseType.APACHE_2)
        self.assertEqual(license_terms.holder, "Apache Holder")

    def test_license_is_valid_at_perpetual(self) -> None:
        """Test that licenses without expiration are always valid."""
        license_terms = LicenseTerms(
            license_type=LicenseType.CC_BY,
            holder="Holder",
            expiration_date=None,
        )
        self.assertTrue(license_terms.is_valid_at())
        self.assertTrue(license_terms.is_valid_at(datetime.now(UTC)))

    def test_license_is_valid_at_with_expiration(self) -> None:
        """Test license validity with expiration date."""
        future_date = (datetime.now(UTC) + timedelta(days=30)).isoformat()
        past_date = (datetime.now(UTC) - timedelta(days=30)).isoformat()

        valid_license = LicenseTerms(
            license_type=LicenseType.CC_BY,
            holder="Holder",
            expiration_date=future_date,
        )
        expired_license = LicenseTerms(
            license_type=LicenseType.CC_BY,
            holder="Holder",
            expiration_date=past_date,
        )

        self.assertTrue(valid_license.is_valid_at())
        self.assertFalse(expired_license.is_valid_at())

    def test_cc0_always_valid(self) -> None:
        """Test that CC0 license is always valid regardless of expiration."""
        past_date = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        cc0_license = LicenseTerms(
            license_type=LicenseType.CC0,
            holder="Holder",
            expiration_date=past_date,
        )
        self.assertTrue(cc0_license.is_valid_at())


class RightsVerificationTests(unittest.TestCase):
    """Rights verification tests."""

    def test_rights_verification_creation(self) -> None:
        """Test creating RightsVerification with all fields."""
        verification = RightsVerification(
            verification_id="verify-123",
            asset_id="asset-456",
            status=RightsStatus.VERIFIED,
            verified_by="Test Verifier",
            verified_at=datetime.now(UTC).isoformat(),
            verification_method="manual_review",
            evidence_urls=["https://example.com/evidence"],
            notes="Verified successfully",
            dispute_info=None,
        )
        self.assertEqual(verification.verification_id, "verify-123")
        self.assertEqual(verification.status, RightsStatus.VERIFIED)

    def test_rights_verification_to_from_dict(self) -> None:
        """Test RightsVerification serialization roundtrip."""
        original = RightsVerification(
            verification_id="verify-789",
            asset_id="asset-abc",
            status=RightsStatus.PENDING,
        )
        data = original.to_dict()
        restored = RightsVerification.from_dict(data)
        self.assertEqual(restored.verification_id, original.verification_id)
        self.assertEqual(restored.status, original.status)
        self.assertEqual(restored.asset_id, original.asset_id)


class GenerationMetadataTests(unittest.TestCase):
    """Generation metadata tests."""

    def test_generation_metadata_creation(self) -> None:
        """Test creating GenerationMetadata with all fields."""
        metadata = GenerationMetadata(
            generation_id="gen-123",
            source=GenerationSource.AI_GENERATED,
            prompt="A beautiful sunset",
            prompt_hash="abc123hash",
            model="dall-e-3",
            provider_id="openai",
            negative_prompt="blurry, low quality",
            model_version="v1.0",
            parameters={"style": "photorealistic"},
            seed=42,
            inference_steps=50,
            guidance_scale=7.5,
            resolution=(1024, 1024),
            duration_seconds=None,
            generation_time_ms=5000,
            generated_at=datetime.now(UTC).isoformat(),
            hardware_info={"gpu": "A100"},
            software_version="1.0.0",
        )
        self.assertEqual(metadata.generation_id, "gen-123")
        self.assertEqual(metadata.source, GenerationSource.AI_GENERATED)
        self.assertEqual(metadata.prompt, "A beautiful sunset")

    def test_generation_metadata_to_from_dict(self) -> None:
        """Test GenerationMetadata serialization roundtrip."""
        original = GenerationMetadata(
            generation_id="gen-456",
            source=GenerationSource.HUMAN_CREATED,
            prompt="Test prompt",
            prompt_hash="hash123",
            model="manual",
            provider_id="local",
        )
        data = original.to_dict()
        restored = GenerationMetadata.from_dict(data)
        self.assertEqual(restored.generation_id, original.generation_id)
        self.assertEqual(restored.source, original.source)
        self.assertEqual(restored.prompt, original.prompt)

    def test_compute_integrity_hash(self) -> None:
        """Test integrity hash computation for generation metadata."""
        metadata = GenerationMetadata(
            generation_id="gen-789",
            source=GenerationSource.AI_GENERATED,
            prompt="Test",
            prompt_hash="hash",
            model="model-v1",
            provider_id="provider",
            parameters={"key": "value"},
            seed=123,
        )
        hash1 = metadata.compute_integrity_hash()
        hash2 = metadata.compute_integrity_hash()
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex length


class MediaAssetProvenanceTests(unittest.TestCase):
    """Asset provenance tests."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = MediaProvenanceStore(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_media_asset_creation(self) -> None:
        """Test creating MediaAsset with all fields."""
        license_terms = LicenseTerms(
            license_type=LicenseType.CC_BY,
            holder="Test Holder",
        )
        generation_metadata = GenerationMetadata(
            generation_id="gen-123",
            source=GenerationSource.AI_GENERATED,
            prompt="Test prompt",
            prompt_hash="hash",
            model="model",
            provider_id="provider",
        )
        asset = MediaAsset(
            asset_id="asset-123",
            role="generated",
            name="test.png",
            relative_path="assets/generated/hash-test.png",
            media_type="image/png",
            size=1024,
            sha256="abcdef123456",
            created_at=datetime.now(UTC).isoformat(),
            generation_metadata=generation_metadata,
            license_terms=license_terms,
            rights_verification=None,
            parent_asset_ids=("parent-1", "parent-2"),
            provenance_chain_hash="chainhash123",
        )
        self.assertEqual(asset.asset_id, "asset-123")
        self.assertEqual(asset.role, "generated")
        self.assertEqual(asset.parent_asset_ids, ("parent-1", "parent-2"))

    def test_media_asset_to_from_dict(self) -> None:
        """Test MediaAsset serialization roundtrip."""
        license_terms = LicenseTerms(
            license_type=LicenseType.MIT,
            holder="MIT Holder",
        )
        asset = MediaAsset(
            asset_id="asset-456",
            role="source",
            name="source.jpg",
            relative_path="assets/source/hash-source.jpg",
            media_type="image/jpeg",
            size=2048,
            sha256="sha256hash",
            created_at=datetime.now(UTC).isoformat(),
            license_terms=license_terms,
        )
        data = asset.to_dict()
        restored = MediaAsset.from_dict(data)
        self.assertEqual(restored.asset_id, asset.asset_id)
        self.assertEqual(restored.license_terms.license_type, LicenseType.MIT)

    def test_compute_provenance_hash(self) -> None:
        """Test provenance hash computation."""
        asset = MediaAsset(
            asset_id="asset-789",
            role="generated",
            name="test.png",
            relative_path="assets/test.png",
            media_type="image/png",
            size=1024,
            sha256="sha256",
            created_at=datetime.now(UTC).isoformat(),
        )
        hash1 = asset.compute_provenance_hash()
        hash2 = asset.compute_provenance_hash()
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 32)  # Truncated hash length

    def test_is_rights_verified(self) -> None:
        """Test rights verification check."""
        verified_rights = RightsVerification(
            verification_id="v1",
            asset_id="a1",
            status=RightsStatus.VERIFIED,
        )
        unverified_rights = RightsVerification(
            verification_id="v2",
            asset_id="a2",
            status=RightsStatus.UNVERIFIED,
        )
        asset_verified = MediaAsset(
            asset_id="a1",
            role="generated",
            name="v.png",
            relative_path="v.png",
            media_type="image/png",
            size=100,
            sha256="sha",
            created_at=datetime.now(UTC).isoformat(),
            rights_verification=verified_rights,
        )
        asset_unverified = MediaAsset(
            asset_id="a2",
            role="generated",
            name="u.png",
            relative_path="u.png",
            media_type="image/png",
            size=100,
            sha256="sha",
            created_at=datetime.now(UTC).isoformat(),
            rights_verification=unverified_rights,
        )
        self.assertTrue(asset_verified.is_rights_verified())
        self.assertFalse(asset_unverified.is_rights_verified())

    def test_can_use_commercially_and_modify(self) -> None:
        """Test commercial use and modification checks."""
        cc_by_nc = LicenseTerms(
            license_type=LicenseType.CC_BY_NC,
            holder="Holder",
        )
        cc_by_nd = LicenseTerms(
            license_type=LicenseType.CC_BY_ND,
            holder="Holder",
        )
        cc_by = LicenseTerms(
            license_type=LicenseType.CC_BY,
            holder="Holder",
        )

        asset_nc = MediaAsset(
            asset_id="a1",
            role="generated",
            name="nc.png",
            relative_path="nc.png",
            media_type="image/png",
            size=100,
            sha256="sha",
            created_at=datetime.now(UTC).isoformat(),
            license_terms=cc_by_nc,
        )
        asset_nd = MediaAsset(
            asset_id="a2",
            role="generated",
            name="nd.png",
            relative_path="nd.png",
            media_type="image/png",
            size=100,
            sha256="sha",
            created_at=datetime.now(UTC).isoformat(),
            license_terms=cc_by_nd,
        )
        asset_by = MediaAsset(
            asset_id="a3",
            role="generated",
            name="by.png",
            relative_path="by.png",
            media_type="image/png",
            size=100,
            sha256="sha",
            created_at=datetime.now(UTC).isoformat(),
            license_terms=cc_by,
        )

        self.assertFalse(asset_nc.can_use_commercially())
        self.assertTrue(asset_by.can_use_commercially())
        self.assertFalse(asset_nd.can_modify())
        self.assertTrue(asset_by.can_modify())


class MediaTransformationTests(unittest.TestCase):
    """Transformation tests."""

    def test_transformation_creation(self) -> None:
        """Test creating MediaTransformation with all fields."""
        transformation = MediaTransformation(
            operation="resize",
            parameters={"width": 1024, "height": 768},
            output_asset_ids=("out-1", "out-2"),
            transformation_id="trans-123",
            performed_by="user@example.com",
            performed_at=datetime.now(UTC).isoformat(),
            software_version="v2.0",
            input_asset_ids=("in-1",),
            transformation_hash=None,  # Will be computed
        )
        self.assertEqual(transformation.operation, "resize")
        self.assertEqual(transformation.parameters["width"], 1024)
        self.assertIsNotNone(transformation.transformation_hash)

    def test_transformation_to_from_dict(self) -> None:
        """Test MediaTransformation serialization roundtrip."""
        original = MediaTransformation(
            operation="crop",
            parameters={"x": 0, "y": 0, "w": 100, "h": 100},
            output_asset_ids=("out-1",),
        )
        data = original.to_dict()
        restored = MediaTransformation.from_dict(data)
        self.assertEqual(restored.operation, original.operation)
        self.assertEqual(restored.parameters, original.parameters)

    def test_transformation_hash_computation(self) -> None:
        """Test that transformation hash is computed correctly."""
        t1 = MediaTransformation(
            operation="resize",
            parameters={"width": 100},
        )
        t2 = MediaTransformation(
            operation="resize",
            parameters={"width": 100},
        )
        t3 = MediaTransformation(
            operation="resize",
            parameters={"width": 200},
        )
        self.assertEqual(t1.transformation_hash, t2.transformation_hash)
        self.assertNotEqual(t1.transformation_hash, t3.transformation_hash)


class MediaHistoryRecordTests(unittest.TestCase):
    """History record tests."""

    def test_history_record_creation(self) -> None:
        """Test creating MediaHistoryRecord with all fields."""
        transformation = MediaTransformation(
            operation="generate",
            parameters={},
        )
        generation_metadata = GenerationMetadata(
            generation_id="gen-123",
            source=GenerationSource.AI_GENERATED,
            prompt="Test",
            prompt_hash="hash",
            model="model",
            provider_id="provider",
        )
        license_terms = LicenseTerms(
            license_type=LicenseType.CC_BY,
            holder="Holder",
        )
        rights_verification = RightsVerification(
            verification_id="v1",
            asset_id="a1",
            status=RightsStatus.VERIFIED,
        )

        record = MediaHistoryRecord(
            history_id="hist-123",
            prompt="A test prompt",
            prompt_sha256="sha256hash",
            source_asset_ids=("src-1",),
            generated_asset_ids=("gen-1", "gen-2"),
            transformations=(transformation,),
            created_at=datetime.now(UTC).isoformat(),
            metadata={"key": "value"},
            generation_metadata=generation_metadata,
            license_terms=license_terms,
            rights_verifications=(rights_verification,),
            provenance_chain_hash="chainhash",
            parent_history_ids=("parent-1",),
            signature="sig123",
        )
        self.assertEqual(record.history_id, "hist-123")
        self.assertEqual(len(record.transformations), 1)

    def test_history_record_to_from_dict(self) -> None:
        """Test MediaHistoryRecord serialization roundtrip."""
        transformation = MediaTransformation(operation="test", parameters={})
        record = MediaHistoryRecord(
            history_id="hist-456",
            prompt="Test prompt",
            prompt_sha256="hash",
            source_asset_ids=(),
            generated_asset_ids=("gen-1",),
            transformations=(transformation,),
            created_at=datetime.now(UTC).isoformat(),
        )
        data = record.to_dict()
        restored = MediaHistoryRecord.from_dict(data)
        self.assertEqual(restored.history_id, record.history_id)
        self.assertEqual(len(restored.transformations), 1)

    def test_compute_chain_hash(self) -> None:
        """Test chain hash computation."""
        record = MediaHistoryRecord(
            history_id="hist-789",
            prompt="Test",
            prompt_sha256="hash",
            source_asset_ids=("src-1",),
            generated_asset_ids=("gen-1",),
            transformations=(),
            created_at=datetime.now(UTC).isoformat(),
        )
        hash1 = record.compute_chain_hash()
        hash2 = record.compute_chain_hash()
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_verify_integrity(self) -> None:
        """Test integrity verification."""
        record = MediaHistoryRecord(
            history_id="hist-abc",
            prompt="Test",
            prompt_sha256="hash",
            source_asset_ids=(),
            generated_asset_ids=(),
            transformations=(),
            created_at=datetime.now(UTC).isoformat(),
        )
        # Without provenance_chain_hash, should return True
        self.assertTrue(record.verify_integrity())

        # With matching hash
        chain_hash = record.compute_chain_hash()
        record_with_hash = MediaHistoryRecord(
            history_id="hist-abc",
            prompt="Test",
            prompt_sha256="hash",
            source_asset_ids=(),
            generated_asset_ids=(),
            transformations=(),
            created_at=datetime.now(UTC).isoformat(),
            provenance_chain_hash=chain_hash,
        )
        self.assertTrue(record_with_hash.verify_integrity())


class ProvenanceStoreEnhancedTests(unittest.TestCase):
    """Store functionality tests."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = MediaProvenanceStore(self.temp_dir.name)
        # Create a test file
        self.test_file = Path(self.temp_dir.name) / "test_image.png"
        self.test_file.write_bytes(b"fake image data")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ingest_asset(self) -> None:
        """Test asset ingestion."""
        asset = self.store.ingest_asset(
            self.test_file,
            role="source",
            asset_id="test-asset-1",
        )
        self.assertEqual(asset.asset_id, "test-asset-1")
        self.assertEqual(asset.role, "source")
        self.assertTrue(asset.sha256)

    def test_ingest_asset_with_generation_metadata(self) -> None:
        """Test asset ingestion with generation metadata."""
        generation_metadata = GenerationMetadata(
            generation_id="gen-123",
            source=GenerationSource.AI_GENERATED,
            prompt="Test prompt",
            prompt_hash="hash",
            model="model",
            provider_id="provider",
        )
        asset = self.store.ingest_asset(
            self.test_file,
            role="generated",
            generation_metadata=generation_metadata,
        )
        self.assertIsNotNone(asset.generation_metadata)
        self.assertEqual(asset.generation_metadata.generation_id, "gen-123")

    def test_ingest_asset_with_license(self) -> None:
        """Test asset ingestion with license terms."""
        license_terms = LicenseTerms(
            license_type=LicenseType.CC_BY_SA,
            holder="Test Holder",
        )
        asset = self.store.ingest_asset(
            self.test_file,
            role="generated",
            license_terms=license_terms,
        )
        self.assertIsNotNone(asset.license_terms)
        self.assertEqual(asset.license_terms.license_type, LicenseType.CC_BY_SA)

    def test_ingest_asset_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for missing file."""
        with self.assertRaises(FileNotFoundError):
            self.store.ingest_asset("/nonexistent/file.png", role="source")

    def test_ingest_asset_too_large(self) -> None:
        """Test that ValueError is raised for oversized file."""
        store = MediaProvenanceStore(self.temp_dir.name, max_asset_bytes=10)
        with self.assertRaises(ValueError):
            store.ingest_asset(self.test_file, role="source")

    def test_record_creation(self) -> None:
        """Test history record creation."""
        asset = self.store.ingest_asset(self.test_file, role="source")
        record = self.store.record(
            prompt="Generate an image",
            source_assets=[asset],
            generated_assets=[asset],
        )
        self.assertIsNotNone(record.history_id)
        self.assertEqual(record.prompt, "Generate an image")

    def test_list_history(self) -> None:
        """Test listing history records."""
        asset = self.store.ingest_asset(self.test_file, role="source")
        self.store.record(
            prompt="Test prompt 1",
            source_assets=[asset],
            generated_assets=[asset],
        )
        self.store.record(
            prompt="Test prompt 2",
            source_assets=[asset],
            generated_assets=[asset],
        )
        history = self.store.list_history()
        self.assertEqual(len(history), 2)

    def test_get_record(self) -> None:
        """Test getting a specific record by ID."""
        asset = self.store.ingest_asset(self.test_file, role="source")
        record = self.store.record(
            prompt="Test prompt",
            source_assets=[asset],
            generated_assets=[asset],
        )
        retrieved = self.store.get_record(record.history_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.history_id, record.history_id)

    def test_get_record_not_found(self) -> None:
        """Test getting a non-existent record."""
        result = self.store.get_record("nonexistent-id")
        self.assertIsNone(result)

    def test_register_and_get_license(self) -> None:
        """Test license registration and retrieval."""
        license_terms = LicenseTerms(
            license_type=LicenseType.APACHE_2,
            holder="Apache Holder",
        )
        result = self.store.register_license("asset-123", license_terms)
        self.assertTrue(result)

        retrieved = self.store.get_license("asset-123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.license_type, LicenseType.APACHE_2)

    def test_verify_and_get_rights(self) -> None:
        """Test rights verification and retrieval."""
        verification = self.store.verify_rights(
            asset_id="asset-456",
            verified_by="Test Verifier",
            verification_method="manual",
            evidence_urls=["https://example.com/evidence"],
            notes="Verified",
        )
        self.assertEqual(verification.status, RightsStatus.VERIFIED)

        retrieved = self.store.get_rights_verification("asset-456")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.verified_by, "Test Verifier")

    def test_check_usage_rights(self) -> None:
        """Test usage rights checking."""
        license_terms = LicenseTerms(
            license_type=LicenseType.CC_BY_NC,
            holder="Holder",
        )
        self.store.register_license("asset-nc", license_terms)

        # Non-commercial use should be allowed
        result_nc = self.store.check_usage_rights("asset-nc", commercial=False)
        self.assertTrue(result_nc["allowed"])

        # Commercial use should not be allowed
        result_c = self.store.check_usage_rights("asset-nc", commercial=True)
        self.assertFalse(result_c["allowed"])
        self.assertIn("commercial", result_c["reason"].lower())

    def test_check_usage_rights_no_license(self) -> None:
        """Test usage rights checking when no license is registered."""
        result = self.store.check_usage_rights("unknown-asset", commercial=False)
        self.assertFalse(result["allowed"])
        self.assertIsNotNone(result["reason"])
        self.assertIn("no license", result["reason"].lower())


class LicenseTypeTests(unittest.TestCase):
    """License type enum tests."""

    def test_license_type_values(self) -> None:
        """Test that all expected license types exist."""
        self.assertEqual(LicenseType.CC0.value, "cc0")
        self.assertEqual(LicenseType.CC_BY.value, "cc-by")
        self.assertEqual(LicenseType.CC_BY_SA.value, "cc-by-sa")
        self.assertEqual(LicenseType.MIT.value, "mit")
        self.assertEqual(LicenseType.APACHE_2.value, "apache-2.0")
        self.assertEqual(LicenseType.PROPRIETARY.value, "proprietary")
        self.assertEqual(LicenseType.CUSTOM.value, "custom")
        self.assertEqual(LicenseType.UNKNOWN.value, "unknown")

    def test_license_type_from_string(self) -> None:
        """Test creating LicenseType from string values."""
        self.assertEqual(LicenseType("cc0"), LicenseType.CC0)
        self.assertEqual(LicenseType("mit"), LicenseType.MIT)
        self.assertEqual(LicenseType("proprietary"), LicenseType.PROPRIETARY)


class GenerationSourceTests(unittest.TestCase):
    """Generation source enum tests."""

    def test_generation_source_values(self) -> None:
        """Test that all expected generation sources exist."""
        self.assertEqual(GenerationSource.AI_GENERATED.value, "ai_generated")
        self.assertEqual(GenerationSource.AI_EDITED.value, "ai_edited")
        self.assertEqual(GenerationSource.HUMAN_CREATED.value, "human_created")
        self.assertEqual(GenerationSource.HYBRID.value, "hybrid")
        self.assertEqual(GenerationSource.UPLOADED.value, "uploaded")
        self.assertEqual(GenerationSource.DERIVATIVE.value, "derivative")

    def test_generation_source_from_string(self) -> None:
        """Test creating GenerationSource from string values."""
        self.assertEqual(GenerationSource("ai_generated"), GenerationSource.AI_GENERATED)
        self.assertEqual(GenerationSource("human_created"), GenerationSource.HUMAN_CREATED)
        self.assertEqual(GenerationSource("uploaded"), GenerationSource.UPLOADED)


class RightsStatusTests(unittest.TestCase):
    """Rights status enum tests."""

    def test_rights_status_values(self) -> None:
        """Test that all expected rights statuses exist."""
        self.assertEqual(RightsStatus.UNVERIFIED.value, "unverified")
        self.assertEqual(RightsStatus.PENDING.value, "pending")
        self.assertEqual(RightsStatus.VERIFIED.value, "verified")
        self.assertEqual(RightsStatus.DISPUTED.value, "disputed")
        self.assertEqual(RightsStatus.REVOKED.value, "revoked")
        self.assertEqual(RightsStatus.EXPIRED.value, "expired")


if __name__ == "__main__":
    unittest.main()
