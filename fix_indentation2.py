#!/usr/bin/env python3
"""Fix indentation error in _persist_report"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation
content = content.replace(
    'raise EndpointMonitorPersistenceError("Database connection not initialized")\n            conn = self._conn\n\n        # Update current health\n                for url, health in report.endpoints.items():',
    'raise EndpointMonitorPersistenceError("Database connection not initialized")\n            conn = self._conn\n\n        # Update current health\n        for url, health in report.endpoints.items():'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed indentation error in _persist_report')
