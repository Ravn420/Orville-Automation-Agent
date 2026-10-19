import os
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'

from orville_core import RuntimeHealth

health = RuntimeHealth()
print("Cloud environment detected:", health._detect_cloud_environment())

report = health.run()
cloud_check = next((c for c in report['checks'] if c['name'] == 'cloud-environment'), None)
print("Cloud check:", cloud_check)
print("Available:", cloud_check['available'] if cloud_check else 'None')
