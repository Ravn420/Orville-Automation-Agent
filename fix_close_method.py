with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the close method and add the missing closing quote
content = content.replace(
    '        """Close the monitor and release resources."""\n        self._initialized = False\n\n    def __del__',
    '        """Close the monitor and release resources."""\n        self._initialized = False\n\n    def __del__'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed')
