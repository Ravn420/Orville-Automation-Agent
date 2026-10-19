#!/usr/bin/env python3
"""Fix _persist_report to use self._conn instead of creating a new connection"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix _persist_report to use self._conn
content = content.replace(
    'def _persist_report(self, report: EndpointHealthReport) -> None:\n        """Persist health report to database."""\n        try:\n            with sqlite3.connect(self.config.database_path) as conn:',
    'def _persist_report(self, report: EndpointHealthReport) -> None:\n        """Persist health report to database."""\n        try:\n            if self._conn is None:\n                raise EndpointMonitorPersistenceError("Database connection not initialized")\n            conn = self._conn'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed _persist_report to use self._conn')
