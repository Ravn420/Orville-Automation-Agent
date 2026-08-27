# Versioning and Release Notes

## Version source of truth

Orville uses **Semantic Versioning 2.0.0** for distributable releases. The authoritative package version is the `[project].version` field in `pyproject.toml`; release directories, archive names, installer metadata, and release notes must use the same `MAJOR.MINOR.PATCH` value. The current repository baseline is **0.1.0**.

A release version is immutable after publication. Corrections to release documentation use a new patch version or an explicitly dated documentation correction; an already-published package must not be silently relabeled.

| Version component | Increment when |
|---|---|
| Major | A supported contract or compatibility boundary changes in a way that requires user migration. |
| Minor | Backward-compatible functionality, supported target, provider capability, or workflow is added. |
| Patch | A backward-compatible defect, security, documentation, packaging, or reliability correction is released. |

Pre-release identifiers such as `0.2.0-rc.1` may be used for release candidates. They must not be presented as stable releases, and each candidate must retain its own validation evidence.

## Release checklist

Before assigning a version, the release owner records the source revision, package version, target profile, configuration schema version, dependency changes, migration requirements, security review status, and operator approval where applicable. The release must pass compilation, focused and full tests where feasible, the standalone release gate, and target-specific smoke checks. Generated archives and checksums are retained under the `release/` boundary; temporary build output is disposable.

Secrets, API keys, bearer tokens, private certificates, cookies, personal data, and unredacted logs are never included in release notes, archives, checksums, screenshots, or validation evidence. Provider and deployment claims must identify whether they are locally validated, documented-only, or deployment-owned.

## Release-note structure

Each release note uses the following order:

1. **Release identity:** version, date, maturity, supported targets, and compatibility summary.
2. **Added:** new user-visible capabilities and supported integrations.
3. **Changed:** behavior, defaults, schemas, APIs, or operational controls that changed.
4. **Fixed:** corrected defects and affected workflows.
5. **Security and privacy:** redaction, approval, boundary, or dependency changes without secret values.
6. **Validation:** exact reproducible commands and result counts, with environment limitations.
7. **Upgrade and rollback:** data migrations, configuration changes, backup requirements, and rollback constraints.
8. **Known limitations:** unvalidated providers, platform-specific gaps, and deployment-owned work.

Release notes describe user impact and migration action, not internal implementation speculation. Every material claim must point to a retained test, document, artifact, or operator record.

## Current release baseline

`RELEASE_NOTES.md` records the 0.1.0 baseline. It is a local release record, not a claim that all deployment targets have been promoted to production. The current baseline supports the standalone package and documented Windows and container targets; live provider operations and production promotion remain environment-specific.

## Upgrade and rollback rules

Operators must back up runtime data before an upgrade, verify the backup, review configuration changes, run the release checks, and preserve the previous known-good version until post-upgrade health and smoke checks pass. SQLite-backed deployments must not be scaled beyond one API replica without a separately validated storage design. Rollback restores the previously approved version and compatible configuration under the approval-gated delivery runbook; it does not delete current logs, databases, credentials, backups, or release evidence.
