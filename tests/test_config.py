import unittest

from orville_core.config import RuntimeConfig


class ConfigTests(unittest.TestCase):
    def test_valid_configuration_is_parsed_without_exposing_token(self):
        config = RuntimeConfig.from_environment({"ORVILLE_API_TOKEN": "test-token", "ORVILLE_API_PORT": "9000", "ORVILLE_STORAGE": "json", "ORVILLE_ALLOWED_ORIGINS": "http://localhost:3000,https://example.test"})
        self.assertEqual(config.port, 9000)
        self.assertEqual(config.storage, "json")
        self.assertNotIn("test-token", str(config.redacted()))

    def test_invalid_or_placeholder_configuration_fails_closed(self):
        with self.assertRaises(ValueError):
            RuntimeConfig.from_environment({"ORVILLE_API_TOKEN": "replace-with-a-high-entropy-secret"})
        with self.assertRaises(ValueError):
            RuntimeConfig.from_environment({"ORVILLE_API_TOKEN": "token", "ORVILLE_API_PORT": "70000"})
        with self.assertRaises(ValueError):
            RuntimeConfig.from_environment({"ORVILLE_API_TOKEN": "token", "ORVILLE_STORAGE": "redis"})
        with self.assertRaises(ValueError):
            RuntimeConfig.from_environment({"ORVILLE_API_TOKEN": "token", "ORVILLE_ALLOWED_ORIGINS": ""})

    def test_generated_token_has_minimum_length(self):
        token = RuntimeConfig.generate_token()
        self.assertGreaterEqual(len(token), 16)
        with self.assertRaises(ValueError):
            RuntimeConfig.generate_token(8)


if __name__ == "__main__":
    unittest.main()
