#!/usr/bin/env python3
"""Fix database connection handling in EndpointMonitor"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add _conn attribute to __init__
content = content.replace(
    'self._monitor = EndpointHealthMonitor(\n            environment="persistent",\n            check_interval_seconds=config.check_interval_seconds,\n            failure_threshold=config.failure_threshold,\n            success_threshold=config.success_threshold,\n            probe_timeout_seconds=config.probe_timeout_seconds,\n        )\n        self._initialized = False',
    'self._monitor = EndpointHealthMonitor(\n            environment="persistent",\n            check_interval_seconds=config.check_interval_seconds,\n            failure_threshold=config.failure_threshold,\n            success_threshold=config.success_threshold,\n            probe_timeout_seconds=config.probe_timeout_seconds,\n        )\n        self._conn: Optional[sqlite3.Connection] = None\n        self._initialized = False'
)

# Fix initialize() to store connection
content = content.replace(
    'conn = sqlite3.connect(self.config.database_path)\n        try:\n            conn.execute("""',
    'self._conn = sqlite3.connect(self.config.database_path)\n        try:\n            self._conn.execute("""'
)

# Fix all conn.execute calls to use self._conn
content = content.replace(
    'conn.execute("""',
    'self._conn.execute("""'
)

# Fix conn.commit() to use self._conn
content = content.replace(
    'conn.commit()',
    'self._conn.commit()'
)

# Fix conn.rollback() to use self._conn
content = content.replace(
    'conn.rollback()',
    'self._conn.rollback()'
)

# Fix conn.close() to use self._conn
content = content.replace(
    'conn.close()',
    'self._conn.close()'
)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed database connection handling in EndpointMonitor')
