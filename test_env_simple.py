"""Simple test to verify environment variable detection."""
import os

# Set environment variable before importing the module
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'

# Now import the module
from orville_core import RuntimeHealth

# Check if the environment variable is accessible
print(f"AWS_ACCESS_KEY_ID in os.environ: {'AWS_ACCESS_KEY_ID' in os.environ}")
print(f"os.getenv('AWS_ACCESS_KEY_ID'): {os.getenv('AWS_ACCESS_KEY_ID')}")

# Run the health check
report = RuntimeHealth(check_environment=True).run()
cloud_check = next((c for c in report["checks"] if c["name"] == "cloud-environment"), None)
print(f"Cloud environment check: {cloud_check}")
print(f"Available: {cloud_check['available']}")
print(f"Version: {cloud_check['version']}")
