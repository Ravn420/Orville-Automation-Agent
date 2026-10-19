import re

with open('tests/test_endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences of the old patch location with the new one
content = content.replace(
    'orville_core.endpoint_probe.probe_endpoint',
    'orville_core.endpoint_health.probe_endpoint'
)

# Replace all mock response objects to include reachable attribute
content = content.replace(
    'type("Response", (), {"status": 200})()',
    'type("Response", (), {"status": 200, "reachable": True})()'
)

with open('tests/test_endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated patch locations and mock responses')
