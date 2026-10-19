# Connector Management System

## Overview

The Connector Management System provides a comprehensive framework for managing Orville connectors, including configuration, validation, dependency management, and versioning. This system is part of Phase 3.2 (Connector Management) and builds upon the existing connector infrastructure.

## Architecture

The system is organized into four main components:

1. **Configuration File Format** - JSON/YAML format for connector manifests
2. **Configuration Loader and Validator** - Load and validate configurations
3. **Dependency Management** - Track and resolve connector dependencies
4. **Versioning Support** - Semver-based versioning for connectors

## Configuration File Format

### File Structure

Connector configurations are stored in JSON or YAML format with the following structure:

```json
{
  "version": "1.0.0",
  "manifests": {
    "github": {
      "uid": "github",
      "display_name": "GitHub",
      "version": "1.0.0",
      "description": "GitHub API connector",
      "status": "operational",
      "auth_type": "bearer",
      "base_url": "https://api.github.com",
      "scopes": ["repo", "user", "read:org"],
      "operations": [
        {
          "name": "issues.list",
          "method": "GET",
          "description": "List issues in a repository",
          "parameters": {
            "owner": {"type": "string", "required": true},
            "repo": {"type": "string", "required": true}
          },
          "returns": {"type": "array", "items": {"type": "object"}},
          "risk_class": "read",
          "sensitive": false,
          "deprecated": false,
          "version": "1.0.0"
        }
      ],
      "dependencies": [],
      "risk_class": "read",
      "owner_id": "local",
      "task_id": null,
      "metadata": {},
      "created_at": 1697235200.0,
      "updated_at": 1697235200.0
    }
  },
  "connections": {
    "github": {
      "uid": "github",
      "display_name": "GitHub",
      "auth_type": "bearer",
      "credential_header": "Authorization",
      "base_url": "https://api.github.com",
      "status": "connected",
      "scopes": ["repo", "user", "read:org"],
      "connected_at": 1697235200.0,
      "operation_count": 0,
      "has_credential": true,
      "has_refresh_token": false,
      "revoke_configured": false
    }
  },
  "defaults": {
    "user": {
      "default": "github"
    },
    "project": {},
    "task": {}
  },
  "created_at": 1697235200.0,
  "updated_at": 1697235200.0
}
```

### YAML Example

```yaml
version: "1.0.0"
manifests:
  github:
    uid: github
    display_name: GitHub
    version: "1.0.0"
    description: GitHub API connector
    status: operational
    auth_type: bearer
    base_url: https://api.github.com
    scopes:
      - repo
      - user
      - read:org
    operations:
      - name: issues.list
        method: GET
        description: List issues in a repository
        parameters:
          owner:
            type: string
            required: true
          repo:
            type: string
            required: true
        returns:
          type: array
          items:
            type: object
        risk_class: read
        sensitive: false
        deprecated: false
        version: "1.0.0"
    dependencies: []
    risk_class: read
    owner_id: local
    task_id: null
    metadata: {}
    created_at: 1697235200.0
    updated_at: 1697235200.0
connections: {}
defaults:
  user:
    default: github
  project: {}
  task: {}
created_at: 1697235200.0
updated_at: 1697235200.0
```

## Connector Manifest

### Fields

- **uid** (string, required): Unique identifier for the connector. Must match pattern: `^[a-z0-9]([a-z0-9-_.]*[a-z0-9])?$`
- **display_name** (string, required): Human-readable name. Must contain only letters, numbers, spaces, hyphens, underscores, and dots
- **version** (string, required): Semantic version in format `X.Y.Z`
- **description** (string, required): Description of the connector
- **status** (string, optional): Connector status. Default: `configuration_required`
  - `configuration_required`: Connector needs configuration
  - `operational`: Connector is fully operational
  - `degraded`: Connector is partially functional
  - `unavailable`: Connector is unavailable
  - `error`: Connector has an error
- **auth_type** (string, optional): Authentication type
  - `api_key`: API key authentication
  - `bearer`: Bearer token authentication
  - `oauth2`: OAuth2 authentication
- **base_url** (string, optional): Base URL for the connector API
- **scopes** (array, optional): Required scopes for the connector
- **operations** (array, optional): List of supported operations
- **dependencies** (array, optional): List of dependent connector UIDs
- **risk_class** (string, optional): Risk classification. Default: `read`
  - `read`: Read-only operations
  - `write`: Write operations
  - `sensitive`: Sensitive operations
  - `critical`: Critical operations
- **owner_id** (string, optional): Owner identifier. Default: `local`
- **task_id** (string, optional): Task ID if connector is task-specific
- **metadata** (object, optional): Additional metadata
- **created_at** (float, optional): Creation timestamp
- **updated_at** (float, optional): Last update timestamp

### Connector Operation

Each operation in the `operations` array has the following fields:

- **name** (string, required): Operation name
- **method** (string, required): HTTP method (GET, POST, PUT, PATCH, DELETE)
- **description** (string, required): Operation description
- **parameters** (object, optional): Request parameters schema
- **returns** (object, optional): Response schema
- **risk_class** (string, optional): Risk classification. Default: `read`
- **sensitive** (boolean, optional): Whether operation is sensitive. Default: `false`
- **deprecated** (boolean, optional): Whether operation is deprecated. Default: `false`
- **version** (string, optional): Operation version. Default: `1.0.0`

## Configuration Loader

The `ConnectorConfigLoader` class handles loading and saving connector configurations:

```python
from orville_core.connector_config import ConnectorConfigLoader

loader = ConnectorConfigLoader("path/to/connector-config.json")
config = loader.load()  # Load existing config or create new
loader.save(config)     # Save config to file
```

### Validation

The loader validates configurations on load:

```python
errors = loader.validate_file()  # Validate without loading
if errors:
    print("Validation errors:", errors)
```

## Configuration Manager

The `ConnectorConfigManager` class provides high-level operations:

```python
from orville_core.connector_config import ConnectorConfigManager

manager = ConnectorConfigManager("path/to/connector-config.json")

# List all manifests
manifests = manager.list_manifests()

# Get a specific manifest
manifest = manager.get_manifest("github")

# Add a new manifest
manifest = ConnectorManifest(
    uid="new-connector",
    display_name="New Connector",
    version="1.0.0",
    description="A new connector",
    base_url="https://api.example.com",
    auth_type=ConnectorAuthType.BEARER,
)
errors = manager.add_manifest(manifest)

# Remove a manifest
manager.remove_manifest("github")

# Get dependencies
deps = manager.get_dependencies("main-connector")

# Resolve all dependencies
resolved = manager.resolve_dependencies(["main-connector", "dep1"])

# Get version information
info = manager.get_version_info("github")

# Get version info for all connectors
all_info = manager.get_all_version_info()

# Update status
manager.update_status("github", ConnectorStatus.OPERATIONAL)

# Validate all
errors = manager.validate_all()
```

## Dependency Management

The system supports dependency tracking and resolution:

```python
# Define dependencies in manifest
manifest = ConnectorManifest(
    uid="main",
    display_name="Main Connector",
    version="1.0.0",
    description="Main connector",
    dependencies=["dep1", "dep2"],  # Declare dependencies
)

# Get all dependencies
deps = manager.get_dependencies("main")
# Returns: [dep1, dep2, ...]

# Resolve dependencies for multiple connectors
resolved = manager.resolve_dependencies(["main", "dep1"])
# Returns: [main, dep1, dep2, ...] (all unique)
```

### Circular Dependency Detection

The system automatically detects circular dependencies:

```python
# This will fail validation
manifest = ConnectorManifest(
    uid="a",
    display_name="A",
    version="1.0.0",
    description="A",
    dependencies=["b"],
)
manifest2 = ConnectorManifest(
    uid="b",
    display_name="B",
    version="1.0.0",
    description="B",
    dependencies=["a"],  # Circular!
)
```

## Versioning

The system uses semantic versioning (semver) for connectors:

```python
# Valid versions
valid_versions = ["1.0.0", "2.1.3", "10.0.0"]

# Invalid versions
invalid_versions = ["1", "1.0", "invalid", "1.0.0-beta", "1.0.0+build"]

# Version information
info = manager.get_version_info("github")
# Returns:
# {
#   "uid": "github",
#   "display_name": "GitHub",
#   "version": "1.0.0",
#   "status": "operational",
#   "auth_type": "bearer",
#   "base_url": "https://api.github.com",
#   "has_connection": true,
#   "connection_status": "connected",
#   "operation_count": 10,
#   "dependency_count": 0,
#   "created_at": 1697235200.0,
#   "updated_at": 1697235200.0
# }
```

## CLI Commands

### List Connectors

```bash
orville connectors list
```

Output:
```
Found 2 connector(s):
  - GitHub (github) v1.0.0
    Status: operational
    Operations: 10
    Dependencies: 0

  - Slack (slack) v1.0.0
    Status: operational
    Operations: 5
    Dependencies: 0
```

### Get Connector Info

```bash
orville connectors get github
```

Output:
```
Connector: GitHub (github)
Version: 1.0.0
Status: operational
Description: GitHub API connector
Base URL: https://api.github.com
Auth Type: bearer
Scopes: repo, user, read:org
Operations: 10
  - issues.list (GET) - List issues in a repository
  - issues.get (GET) - Get a single issue
  - issues.create (POST) - Create a new issue
  ...
Dependencies: []
Risk Class: read
Owner: local
```

### Add Connector

```bash
orville connectors add my-connector "My Connector" 1.0.0 "A custom connector" \
  --base-url https://api.example.com \
  --auth-type bearer \
  --scopes read write \
  --risk-class write \
  --operation issues.list GET \
  --operation issues.create POST \
  --dependency dep1
```

### Update Connector Status

```bash
orville connectors update github operational
```

### Remove Connector

```bash
orville connectors remove github
```

### Validate Configuration

```bash
orville connectors validate
```

Output:
```json
{
  "status": "valid",
  "message": "All connectors are valid"
}
```

### Show Version Info

```bash
orville connectors version
```

Output:
```
Version information for 2 connector(s):
  - GitHub (github) v1.0.0
    Status: operational
    Operations: 10
    Dependencies: 0

  - Slack (slack) v1.0.0
    Status: operational
    Operations: 5
    Dependencies: 0
```

### Show Dependencies

```bash
orville connectors dependencies main-connector
```

Output:
```
Dependencies for main-connector:
  - Dependency 1 (dep1) v1.0.0
    Status: operational

  - Dependency 2 (dep2) v1.0.0
    Status: operational
```

## Error Handling

The system provides detailed error messages for validation failures:

```python
# Invalid manifest
manifest = ConnectorManifest(
    uid="invalid-uid!",
    display_name="Test",
    version="1.0.0",
    description="Test",
)
errors = manifest.validate()
# Returns: ["Invalid connector UID: invalid-uid! Must match pattern: ^[a-z0-9]([a-z0-9-_.]*[a-z0-9])?$"]
```

## Best Practices

1. **Use descriptive UIDs**: Choose UIDs that clearly identify the connector
2. **Follow semver**: Use semantic versioning for all connectors
3. **Document operations**: Provide clear descriptions for all operations
4. **Set appropriate risk classes**: Classify operations correctly
5. **Declare dependencies**: Explicitly declare all dependencies
6. **Validate before deployment**: Always validate configurations before deployment
7. **Use JSON output**: For programmatic access, use `--json` flag

## Integration with Existing System

The connector management system integrates seamlessly with:

- **Connector Connections**: Manages connection records and credentials
- **Connector Defaults**: Resolves default connectors for user/project/task scopes
- **Connector Adapters**: Works with existing adapter infrastructure
- **Connector Health**: Can be extended to track health status
- **Connector Policy**: Can enforce policies on connector usage

## Future Enhancements

Potential future enhancements:

1. **Configuration Templates**: Support for connector templates
2. **Configuration Diffing**: Compare configuration versions
3. **Configuration Rollback**: Rollback to previous configurations
4. **Configuration Export/Import**: Export configurations for backup
5. **Configuration Validation Rules**: Custom validation rules
6. **Connector Marketplace**: Share and discover connector configurations
7. **Configuration Auditing**: Track configuration changes
8. **Configuration Version History**: Store version history of configurations
