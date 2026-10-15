#!/usr/bin/env python3
"""Fix all syntax errors in endpoint_monitor.py"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the __del__ method docstring
content = content.replace(
    '"""Ensure connection is closed when object is destroyed."""\n        if self._initialized:\n            self.close()',
    '"""Ensure connection is closed when object is destroyed."""\n        if self._initialized:\n            self.close()\n\n    def __repr__(self) -> str:\n        """Return string representation of the monitor."""\n        return f"EndpointMonitor(config={self.config!r}, initialized={self._initialized})"'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed all syntax errors in endpoint_monitor.py')
