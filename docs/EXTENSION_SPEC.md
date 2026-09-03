# Orville Extension Specification v1.0

This document defines the structure and requirements for Orville extensions.

## 1. Package Structure
An extension is a directory or a `.orv` (zip) archive containing:
- `manifest.json`: Metadata and declarations.
- `permissions.json`: Requested access levels.
- `main.py`: The entry point for the extension.
- `lib/`: (Optional) Supporting Python modules.
- `assets/`: (Optional) Static assets.

## 2. Manifest Specification (`manifest.json`)
```json
{
  "id": "com.example.git-helper",
  "name": "Git Helper",
  "version": "1.0.0",
  "description": "Adds advanced git analysis skills to Orville",
  "author": "Example Corp",
  "entry_point": "main.py",
  "provides": {
    "skills": ["git_analyze_diff", "git_summarize_commit"],
    "connectors": ["github_api"],
    "hooks": ["on_task_complete"]
  },
  "dependencies": {
    "python": ">=3.12",
    "packages": ["GitPython==3.1.43"]
  }
}
```

## 3. Permissions Specification (`permissions.json`)
Extensions must declare their needs to be granted by the user.
```json
{
  "network": ["api.github.com", "github.com"],
  "filesystem": ["read:workspace", "write:artifacts"],
  "scopes": ["user:email", "repo:status"],
  "tools": ["shell_execute", "http_request"]
}
```

## 4. Entry Point Contract (`main.py`)
The `main.py` must implement the `OrvilleExtension` interface.

```python
from orville_core.extensions import ExtensionContext, Skill, Connector

class OrvilleExtension:
    def activate(self, context: ExtensionContext):
        """Called when the extension is loaded."""
        # Register skills
        context.register_skill(
            skill_id="git_analyze_diff",
            instructions="Analyzes git diffs for logic errors",
            handler=self.handle_analyze_diff
        )

    def deactivate(self, context: ExtensionContext):
        """Called when the extension is disabled/uninstalled."""
        pass

    def handle_analyze_diff(self, payload: dict) -> dict:
        # Implementation logic
        return {"analysis": "No errors found"}
```
