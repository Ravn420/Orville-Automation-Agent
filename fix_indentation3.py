#!/usr/bin/env python3
"""Fix indentation error in _persist_report"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation
content = content.replace(
    '"""Persist health report to database."""\n        try:\n            if self._conn is None:\n                raise EndpointMonitorPersistenceError("Database connection not initialized")\n            conn = self._conn\n\n        # Update current health\n        for url, health in report.endpoints.items():\n                    self._conn.execute("""',
    '"""Persist health report to database."""\n        try:\n            if self._conn is None:\n                raise EndpointMonitorPersistenceError("Database connection not initialized")\n            conn = self._conn\n\n            # Update current health\n            for url, health in report.endpoints.items():\n                self._conn.execute("""'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed indentation error in _persist_report')
