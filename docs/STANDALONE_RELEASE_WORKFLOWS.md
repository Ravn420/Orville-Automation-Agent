# Standalone Release Workflows

Orville can be packaged, installed, upgraded, migrated, rolled back, and deployed without Manus-specific services. The workflow entry point is `tools/standalone_release.py`; existing target deployment validation remains in `deploy.ps1`.

## Requirements

Use Python 3.12 or a compatible Python version supported by `pyproject.toml`. Build operations require the local `build` package. API deployment targets additionally require Docker Compose or the target-specific runtime described by `deploy.ps1`. Credentials and production endpoints are never required for local package, migration, or rollback planning.

## Plan-first commands

Every action is plan-only unless `--execute` is explicitly supplied.

```text
python tools/standalone_release.py package --root . --version 0.1.0 --json
python tools/standalone_release.py migrate --config config/settings.json --json
python tools/standalone_release.py install --destination ./release/install --json
python tools/standalone_release.py upgrade --version 0.1.1 --destination ./release/install --json
python tools/standalone_release.py rollback --backup ./release/backups/1.0.0-... --destination ./release/rollback --json
python tools/standalone_release.py deploy --target sandbox --json
```

Review the generated plan before execution. Package, migration, install, and upgrade execution use explicit local paths. Deployment execution delegates to `deploy.ps1`, which performs target preflight and post-deployment smoke validation.

## Packaging and installation

Build a wheel into `release/` only after reviewing the plan:

```text
python tools/standalone_release.py package --root . --version 0.1.0 --execute
python -m pip install --upgrade --target ./release/install ./release/orville_core-*.whl
```

The package exposes the `orville`, `orville-api`, and `orville-python-mcp` entry points. Optional capabilities are isolated under the `api`, `browser`, `media`, `security`, and `dev` extras in `pyproject.toml`.

## Configuration migration

Configuration migrations are forward-only and deterministic. Version 0 is migrated to version 1 by adding bounded `storage`, `providers`, and local-first `privacy` defaults. The original file is not modified by plan mode; execute mode writes a temporary file and atomically replaces the destination. Secrets must remain in approved environment variables or protected secret references and must not be placed in example or migrated configuration files.

```text
python tools/standalone_release.py migrate --config ./config/settings.json --destination ./release/settings.v1.json --execute
```

## Upgrade and rollback

Before an upgrade, create a versioned copy of the configured data directory with `backup_directory`. Restore is intentionally limited to a named backup and an empty destination. Existing data is never overwritten by rollback. Production rollback requires the applicable deployment approval gate and a post-restore health check; this local workflow provides the deterministic file-level primitive and plan evidence only.

## Deployment targets

`deploy.ps1` supports `sandbox`, `web-hosting`, `attached-desktop`, and `persistent-computing`. It is dry-run by default and calls preflight validation before the target-specific action. Pass `-Execute` only after reviewing the target, path, credentials, and approval requirements. Web and persistent targets additionally run authenticated smoke checks after startup when their local service is available.

## Validation

```text
python -m pytest tests/test_standalone_release.py -q
python -m py_compile tools/standalone_release.py
python tools/standalone_release.py package --root . --version 0.1.0 --json
```

The focused tests cover plan-only defaults, forward-only migration, backup isolation, and refusal to restore over non-empty destinations. No external deployment, credential use, account change, deletion, or production mutation is part of these checks.
