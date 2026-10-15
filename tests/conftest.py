"""Pytest configuration for Orville tests."""
import sys
from pathlib import Path

# Add the root directory to sys.path so tests can import from orville_core and tools
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    print(f"[pytest] Added ROOT to sys.path: {ROOT}", file=sys.stderr)

# Add the tests directory to sys.path so tests can import from tests.fixtures
TESTS_DIR = Path(__file__).resolve()
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
    print(f"[pytest] Added TESTS_DIR to sys.path: {TESTS_DIR}", file=sys.stderr)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with project-specific settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "browser: marks tests requiring browser automation"
    )
    config.addinivalue_line(
        "markers", "api: marks tests for API endpoints"
    )
    config.addinivalue_line(
        "markers", "gui: marks tests for GUI components"
    )
    config.addinivalue_line(
        "markers", "requires_api_token: marks tests that require an API token"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to apply markers based on test file names."""
    for item in items:
        # Add markers based on test file names
        if "browser" in item.nodeid:
            item.add_marker("browser")
        elif "api" in item.nodeid:
            item.add_marker("api")
        elif "gui" in item.nodeid:
            item.add_marker("gui")
        elif "integration" in item.nodeid or "acceptance" in item.nodeid:
            item.add_marker("integration")
        else:
            item.add_marker("unit")
