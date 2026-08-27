# Repository-Level Coding Evaluations

## Purpose

`tools/run_repository_coding_evaluations.py` evaluates realistic code changes in disposable repository fixtures. The harness is intentionally separate from text-only generation checks: it starts from a known failing issue, installs the declared dependency manifest offline, verifies and applies a golden patch, runs focused tests, compiles the fixture, and runs the regression command.

The registry is `config/repository-coding-evaluations.json`. It currently contains two synthetic cases:

| Case | Realistic issue | Golden behavior |
|---|---|---|
| `cache-key-bug` | Different namespaces collide when they use the same cache key | Include the namespace in the cache key and preserve same-namespace round trips |
| `path-boundary` | An exporter can write outside its approved root through traversal | Resolve the root and destination, reject escapes, and write only inside the root |

## Execution contract

The evaluator creates a temporary workspace for each case and never mutates the fixture or the repository during a run. It copies the fixture, installs `requirements.txt` with `pip --no-index --no-deps`, and sets `PYTHONPATH` only to the disposable workspace and dependency target. The current fixtures are standard-library-only; the install step proves that the dependency manifest is syntactically consumable without reaching a package index.

The baseline focused test must fail. This proves that the issue is meaningful and that the golden patch is not being tested against an already-fixed fixture. The evaluator then performs a patch dry run, applies the patch, runs the focused tests, compiles the fixture, and runs its regression command. A case passes only when the baseline fails as expected, the patch applies cleanly, and every post-patch check exits successfully.

## Safety and reproducibility

The registry is local and synthetic. Network access, credentials, external side effects, and production resources are forbidden. Commands are executed without a shell, and fixture commands are restricted to Python module invocations. Patch paths and fixture paths must remain inside the repository. Results redact temporary workspace paths and may be written to `tmp/` for local review; transient result files are not release evidence unless explicitly retained as sanitized artifacts.

The JSON result includes the registry version, case status, commands, exit codes, timeout state, and redacted stdout/stderr. It must not contain credentials, bearer tokens, cookies, private keys, customer data, or unbounded model transcripts.

## Validation command

Run the evaluator from the repository root:

```bash
python3 tools/run_repository_coding_evaluations.py
```

Run the focused contract tests:

```bash
python3 -m pytest -q tests/test_repository_coding_evaluations.py
```

Then run Python compilation and the broader regression suite. A successful local result does not claim that generated software is safe for production, that external dependencies are available, or that deployment and live provider checks have passed. Those are separate roadmap requirements.
