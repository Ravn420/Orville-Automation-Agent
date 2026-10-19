#!/usr/bin/env python3
"""Fix all syntax errors in endpoint_monitor.py"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the __repr__ method docstring
for i, line in enumerate(lines):
    if 'def __repr__(self) -> str:' in line:
        # Check if the next line has the docstring
        if i+1 < len(lines) and '\"\"\"Return string representation of the monitor.\"\"\"' in lines[i+1]:
            # Add the closing quote
            lines[i+1] = lines[i+1].rstrip() + '\"\"\"\\n'
            print(f'Fixed line {i+1}: {repr(lines[i+1])}')
            break

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed __repr__ method')
