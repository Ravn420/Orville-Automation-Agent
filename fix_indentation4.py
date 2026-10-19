#!/usr/bin/env python3
"""Fix indentation error in _persist_report"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation
content = content.replace(
    '                    # Trim history\n                    self._conn.execute("""\n                        DELETE FROM endpoint_health_history\n                        WHERE id NOT IN (\n                            SELECT id FROM endpoint_health_history\n                            WHERE endpoint_url = ?\n                            ORDER BY id DESC\n                            LIMIT ?\n                        )\n                    """, (url, self.config.max_history_entries))\n\n                # Update config\n                self._conn.execute("""',
    '                    # Trim history\n                    self._conn.execute("""\n                        DELETE FROM endpoint_health_history\n                        WHERE id NOT IN (\n                            SELECT id FROM endpoint_health_history\n                            WHERE endpoint_url = ?\n                            ORDER BY id DESC\n                            LIMIT ?\n                        )\n                    """, (url, self.config.max_history_entries))\n\n            # Update config\n            self._conn.execute("""'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed indentation error in _persist_report')
