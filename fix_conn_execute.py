#!/usr/bin/env python3
"""Fix conn.execute to self._conn.execute"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the conn.execute to self._conn.execute
content = content.replace(
    'conn.execute("""',
    'self._conn.execute("""'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed conn.execute to self._conn.execute')
