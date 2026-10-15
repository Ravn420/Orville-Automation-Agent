import os
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'

print("Before import:")
print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))

from orville_core import RuntimeHealth

print("After import:")
print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))

health = RuntimeHealth()

# Debug the method
cloud_indicators = {
    "AWS": "AWS_ACCESS_KEY_ID",
    "AZURE": "AZURE_STORAGE_ACCOUNT",
    "GCP": "GOOGLE_APPLICATION_CREDENTIALS",
    "CLOUD": "CLOUDSDK_PROJECT",
}

print("\nChecking cloud indicators:")
for env_var, provider in cloud_indicators.items():
    value = os.getenv(env_var)
    print(f"  {provider}: {repr(value)}")
    if value:
        print(f"    Found: {provider}")

print("\nCloud environment detected:", health._detect_cloud_environment())

report = health.run()
cloud_check = next((c for c in report['checks'] if c['name'] == 'cloud-environment'), None)
print("Cloud check:", cloud_check)
print("Available:", cloud_check['available'] if cloud_check else 'None')
