#!/usr/bin/env python3
"""Fix the escaped newline in __repr__ method"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the escaped newline
content = content.replace(
    '"""Return string representation of the monitor."""\\n        return f',
    '"""Return string representation of the monitor."""\n        return f'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed escaped newline in __repr__ method')
