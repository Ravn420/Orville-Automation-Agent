# Evaluation Datasets and Golden Cases

## Purpose

This document defines the local, reproducible evaluation registry for Orville’s task-specific behavior. The machine-readable source is `config/evaluation-datasets.json`. It provides one evaluation suite for each of the seven roadmap areas: planning, code generation, debugging, refactoring, research, GUI workflows, and model import.

The registry is a **behavioral acceptance contract**, not a text-similarity benchmark. A candidate output is evaluated against structured must-include and must-not-include expectations, safety boundaries, and task-specific acceptance criteria. Exact wording may vary when the required behavior and evidence remain intact.

## Dataset design

Each suite contains synthetic local cases only. Cases do not use customer data, external credentials, production endpoints, or destructive side effects. The default execution policy is deterministic: temperature is zero, a seed is required, network access is disabled unless a case explicitly declares a local fixture, and high-impact actions remain approval-gated.

| Suite | What it measures | Golden-case themes |
|---|---|---|
| Planning | Dependency-aware decomposition, assumptions, risk, and acceptance criteria | Ordered local workflow; ambiguous deletion/publication request |
| Code generation | Runtime completeness, typed contracts, tests, and security boundaries | Bounded JSON endpoint; path-safe export |
| Debugging | Reproduction, root-cause isolation, minimal repair, and regression evidence | Stale state after restart; coverage overhead |
| Refactoring | Caller impact, compatibility, security-invariant preservation, and migration clarity | Shared path validation; consolidated secret redaction |
| Research | Source quality, citation integrity, fact/analysis separation, and uncertainty | Primary-source summary; conflicting source records |
| GUI workflows | Visible state, approval safety, accessibility, recovery, and redaction | Publish review flow; worker pause/resume |
| Model import | Safe formats, non-execution, provenance, taxonomy, compatibility, and resources | Safetensors directory with script sidecar; adapter base-model mismatch |

## Golden-case contract

Every case has a stable ID, a prompt, a list of required behaviors, a list of prohibited behaviors, and suite-level acceptance criteria. A future runner should record the suite ID, case ID, registry version, execution seed, model/provider version, redacted input and output references, each assertion result, and the final disposition. It must not store secrets, raw credentials, private paths, or unbounded model transcripts.

A case passes only when all required behaviors are observed and no prohibited behavior occurs. A missing required field, ambiguous authorization, unsupported claim, unsafe side effect, or failed safety boundary is a failure or review outcome; it is never converted into a pass by semantic similarity.

## Selection and reporting

Evaluation selection must be deterministic and visible. A run should select an explicit suite and case allowlist, or use the full registry version in stable suite-ID and case-ID order. The result must explain skipped cases, including whether a prerequisite, runtime, provider, or approval was unavailable. The registry is intentionally small and synthetic; it is a smoke and contract layer, not a claim of statistical coverage of all model behavior.

Minimum result fields are:

| Field | Requirement |
|---|---|
| `registry_id` and `version` | Identify the exact evaluation definition |
| `suite_id` and `case_id` | Identify the task-specific contract |
| `seed` and runtime identity | Support reproducibility without storing secrets |
| Assertion outcomes | Show each required and prohibited behavior result |
| Safety disposition | `pass`, `fail`, `blocked`, or `review` |
| Evidence references | Point to redacted logs or structured artifacts only |
| Limitations | Record unavailable providers, runtimes, tools, or human review |

## Safety boundaries

The dataset must not be used to authorize a real deployment, publication, deletion, purchase, transfer, account change, credential change, or external message. GUI cases may describe those actions, but the golden expectation is that the action remains pending until an explicit, scoped, unexpired approval is recorded. Model-import cases may inventory scripts or hooks, but they must never execute them.

Research cases must use supplied local source records or explicitly declared fixtures. They must not reward invented citations or unsupported current claims. Code-generation and debugging cases must not pass merely because a response sounds plausible: tests, typed contracts, reproduction steps, and known limitations are part of the golden behavior.

## Validation procedure

Run the registry schema and content checks first, followed by the focused suite for any changed evaluator or case. Run Python compilation for changed Python modules, then the broader regression suite when feasible. Preserve the command, result count, warnings, and limitations in the task evidence. Keep the registry and this document synchronized whenever a suite or case is added, removed, or materially changed.

## Known limitations

The current registry defines two synthetic cases per suite and does not measure model calibration, multilingual behavior, adversarial breadth, statistical significance, or production traffic. It does not replace isolated software evaluation, repository-level coding benchmarks, trace observability, or live deployment acceptance. Those concerns remain separate roadmap items and must not be claimed complete by passing this registry.
