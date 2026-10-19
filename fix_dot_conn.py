#!/usr/bin/env python3
"""Fix the ._conn issue"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the ._conn issue
content = content.replace(
    '._conn.execute("""',
    'self._conn.execute("""'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed ._conn issue')
