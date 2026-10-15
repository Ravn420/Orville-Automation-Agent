import os
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'

print("Before import:")
print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))

from orville_core import RuntimeHealth

print("After import:")
print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))

health = RuntimeHealth()
print("Cloud environment detected:", health._detect_cloud_environment())

report = health.run()
cloud_check = next((c for c in report['checks'] if c['name'] == 'cloud-environment'), None)
print("Cloud check:", cloud_check)
print("Available:", cloud_check['available'] if cloud_check else 'None')
