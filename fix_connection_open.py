#!/usr/bin/env python3
"""Fix database connection handling to keep connection open"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix initialize() to not close the connection
content = content.replace(
    '        finally:\n            self._conn.close()\n            self._conn = None\n\n        self._initialized = True',
    '        finally:\n            # Connection is kept open for subsequent operations\n            pass\n\n        self._initialized = True'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed database connection handling to keep connection open')
