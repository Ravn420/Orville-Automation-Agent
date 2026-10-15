#!/usr/bin/env python3
"""Add missing closing quote to __repr__ method"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the __repr__ method and add the closing quote
for i, line in enumerate(lines):
    if 'def __repr__(self) -> str:' in line:
        # Check if the next line has the docstring
        if i+1 < len(lines) and '"""Return string representation of the monitor."""' in lines[i+1]:
            # Add the closing quote at the end of the return statement
            if i+2 < len(lines) and 'return f"EndpointMonitor(config={self.config!r}, initialized={self._initialized})"' in lines[i+2]:
                # Add the closing quote
                lines[i+2] = lines[i+2].rstrip() + '\"\"\"\\n'
                print(f'Fixed line {i+2}: {repr(lines[i+2])}')
                break

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Added closing quote to __repr__ method')
