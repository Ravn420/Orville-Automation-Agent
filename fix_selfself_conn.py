#!/usr/bin/env python3
"""Fix the selfself._conn issue"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the selfself._conn issue
content = content.replace(
    'selfself._conn.execute("""',
    'self._conn.execute("""'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed selfself._conn issue')
