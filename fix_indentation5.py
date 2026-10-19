#!/usr/bin/env python3
"""Fix indentation error in _persist_report"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation
content = content.replace(
    '                    ))\n\n                    # Add to history\n                    self._conn.execute("""',
    '                    ))\n\n                # Add to history\n                self._conn.execute("""'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed indentation error in _persist_report')
