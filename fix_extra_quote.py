#!/usr/bin/env python3
"""Fix the extra quote in __repr__ method"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the __repr__ method docstring - remove extra quote
for i, line in enumerate(lines):
    if 'return f"EndpointMonitor(config={self.config!r}, initialized={self._initialized})""""' in line:
        # Remove the extra quote
        lines[i] = line.replace('""""', '"""')
        print(f'Fixed line {i+1}: {repr(lines[i])}')
        break

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed extra quote')
