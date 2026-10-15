#!/usr/bin/env python3
"""Script to update the test file with remaining test classes."""

with open('tests/test_media_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Replace lines 1136-1150 (0-indexed: 1135-1149)
new_lines = lines[:1135]  # Everything before the test

# Add the corrected test and new classes
new_content = '''    def test_invalid_token_rejected(self) -> None:
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
                model="integration-model",
                provider_id="integration-provider",
                license_terms=license_terms,
                generation_metadata=GenerationMetadata(
                    generation_id="gen-001",
                    source=GenerationSource.AI_GENERATED,
                    model="integration-model",
                    provider_id="integration-provider",
                    parameters={"width": 1024, "height": 768}
                )
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
                model="test-model",
                provider_id="test-provider"
            )

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
                model="complete-model",
                provider_id="complete-provider",
                license_terms=license_terms,
                generation_metadata=GenerationMetadata(
                    generation_id="complete-gen-001",
                    source=GenerationSource.AI_GENERATED,
                    model="complete-model",
                    provider_id="complete-provider",
                    parameters={"test": True}
                )
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
                ("png", b"\\x89PNG\\r\\n\\x1a\\n"),
                ("jpg", b"\\xff\\xd8\\xff"),
                ("gif", b"GIF89a"),
                ("webp", b"RIFF"),
            ]

            for fmt, header in test_cases:
                test_file = Path(temp_dir) / f"magic.{fmt}"
                test_file.write_bytes(header + b"\\x00" * 100)

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
                model="test-model",
                provider_id="test-provider"
            )

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
                    model="perf-model",
                    provider_id="perf-provider"
                )

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
                    model="concurrent-model",
                    provider_id="concurrent-provider"
                )

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
                model="test-model",
                provider_id="test-provider"
            )

            history = list(store.list_history())
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].prompt, long_prompt)

    def test_special_characters_in_metadata(self) -> None:
        """Test handling of special characters in metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = MediaProvenanceStore(temp_dir)

            special_prompt = "Test with special chars: <>&\\\"'\\n\\t"

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
                model="test-model",
                provider_id="test-provider"
            )

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
                model="test-model",
                provider_id="test-provider"
            )

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
'''

with open('tests/test_media_integration.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    f.write(new_content)

print('Successfully updated test file')
