#!/usr/bin/env python3
"""Remove duplicate conn.execute statement"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove the duplicate conn.execute statement
for i, line in enumerate(lines):
    if 'conn.execute("""' in line and i > 0 and 'conn.execute("""' in lines[i-1]:
        # Remove this line
        lines[i] = ''
        print(f'Removed duplicate line {i+1}: {repr(line)}')
        break

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Removed duplicate conn.execute statement')
