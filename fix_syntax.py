#!/usr/bin/env python3
"""Fix syntax error in endpoint_monitor.py"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and fix the missing closing quote
# The issue is on line 448: """Close the monitor and release resources."""
# It should be: """Close the monitor and release resources."""
# But it's missing the closing quote

# Let's find the exact pattern
import re
pattern = r'("""Close the monitor and release resources\.\")\n        self\._initialized = False'
replacement = r'\1\n        self._initialized = False\n\n    def __del__(self) -> None:'

content = re.sub(pattern, replacement, content)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed syntax error in endpoint_monitor.py')
