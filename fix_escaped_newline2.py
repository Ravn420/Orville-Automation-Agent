#!/usr/bin/env python3
"""Fix the escaped newline in __repr__ method"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the escaped newline
for i, line in enumerate(lines):
    if 'return f"EndpointMonitor(config={self.config!r}, initialized={self._initialized})"""\\n' in line:
        # Replace the escaped newline with a real newline
        lines[i] = line.replace('"""\\n', '"""\n')
        print(f'Fixed line {i+1}: {repr(lines[i])}')
        break

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed escaped newline in __repr__ method')
