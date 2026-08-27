# Task-Specific Evaluation Datasets and Golden Cases

**Task ID:** `TODO-37bc97abee20`
**Catalog:** `config/evaluation-datasets.json`
**Status:** Local, synthetic, credential-free evaluation contract

## Purpose

This catalog provides reproducible golden cases for the seven task types that are central to Orville's roadmap: **planning, code generation, debugging, refactoring, research, GUI workflows, and model import**. Each dataset contains two synthetic cases with a prompt, required behaviors, prohibited behaviors, and an oracle describing the expected artifact and observable evidence.

The cases evaluate behavior and evidence rather than exact wording. They are deliberately small enough for deterministic local regression and do not require external providers, live accounts, personal data, downloaded models, or network access. The existing isolated behavioral evaluator can execute a candidate in a temporary copy when a case has executable checks; the catalog itself remains declarative so a future runner can choose task-appropriate adapters.

## Schema and scoring contract

Every catalog has a `schema_version`, a stable `catalog_id`, governance metadata, and a `datasets` array. Each dataset has a unique `id`, a normalized `task_type`, a description, and at least two `golden_cases`. Each case has a stable ID, synthetic prompt, required behaviors, prohibited behaviors, and an oracle with an expected artifact type and required evidence labels.

A case passes only when all required behaviors are evidenced and all prohibited behaviors are absent. A missing, ambiguous, or unverifiable claim is not a pass. The oracle is an acceptance contract, not a reference answer to copy. Implementations may use different valid designs while preserving the required safety and verification boundaries.

| Dataset | Case count | Primary acceptance focus |
| --- | ---: | --- |
| `planning` | 2 | Dependencies, assumptions, ownership, verification, recovery, and approval gates |
| `code-generation` | 2 | Complete runnable output, tests, interfaces, safe persistence, and offline behavior |
| `debugging` | 2 | Reproduction, root cause, bounded correction, regression coverage, and path safety |
| `refactoring` | 2 | Compatibility, single implementation, caller inventory, unknown handling, and limited diff |
| `research` | 2 | Traceable evidence, currentness, fact/analysis separation, uncertainty, and scope boundaries |
| `gui-workflows` | 2 | Accessibility, deterministic state transitions, degraded availability, approval, and preservation |
| `model-import` | 2 | Containment, format/integrity checks, metadata, capability diagnostics, and fail-closed activation |

## Operational use

Evaluation runs must use synthetic fixtures and a temporary workspace. Commands must be passed as argument lists rather than shell strings, with bounded timeout and output limits. Candidate hashes and result metadata may be retained, but raw candidate source, credentials, authorization headers, cookies, and unredacted logs must not be copied into evaluation evidence. Model-import cases must never execute model-supplied code, and GUI cases must not silently submit external actions.

The catalog is compatible with the repository's existing task templates and research-evidence policy. It does not claim live provider behavior, production performance, accessibility conformance across all environments, or attestation validity. Those require environment-specific evidence and independent review.

## Maintenance and review

Add a new case only when it represents a distinct failure mode or acceptance boundary. Preserve existing IDs once published, update the schema version for incompatible changes, and keep prompts and oracle fields synthetic and secret-free. A change to case semantics requires a focused fixture-validation test and an entry in `CHANGELOG.md`; a change to evaluator execution requires behavioral tests and a separate compatibility review.

The focused test `tests/test_evaluation_datasets.py` validates the catalog's structure, category coverage, uniqueness, secret-free content, and required safety fields. It does not execute provider calls or mutate external systems.
