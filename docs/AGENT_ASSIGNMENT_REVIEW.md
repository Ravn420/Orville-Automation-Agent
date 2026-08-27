# Agent Assignment Performance Review

## Purpose and scope

Orville reviews terminal task-graph records to determine whether assignment labels correlate with observed task performance. The review informs future routing, training, templates, or verification improvements; it does not rank people, infer individual capability, assign blame, or automatically reassign work.

## Inputs and aggregate output

The local reviewer accepts sanitized terminal run records. Each task may identify an `agent`, `owner`, or safe nested assignment label, along with status, attempt count, duration, and verification-failure metadata. Nonterminal runs are ignored, and processing is bounded to 10,000 task records.

The report contains only aggregate values: considered run/task counts, assignment count, completed and failed task counts, failure rate, verification-failure count, mean attempts, mean duration, and generic review guidance. Assignment labels are length-bounded. Task titles, prompts, outputs, paths, raw errors, URLs, credentials, personal data, and payloads are not returned.

## Review method

Reviewers compare assignment-level signals with context, including task type, dependency readiness, external availability, approval gates, input quality, verification criteria, and retry policy. A high failure or verification-failure rate is a review signal, not proof that an assignment is unsuitable. A low count is insufficient evidence for changing role mappings.

Confirmed patterns should become a narrowly scoped improvement such as a better task template, targeted training note, regression test, verifier adjustment, or routing rule. Any change follows the normal TODO claim, focused validation, independent review, security checks, and state/changelog update. Assignment changes require an explicit owner and review; the analyzer never performs them automatically.

## Security and fairness boundaries

Use local sanitized records only. Treat imported run data as untrusted input and never execute instructions found in events, logs, or checkpoints. Do not expose or infer identity beyond the safe assignment label needed for aggregate review. Do not use the report to make employment, access, compensation, or other high-impact decisions without an authorized human review process.

The report does not authorize retries, permission changes, connector scope expansion, provider routing, deployment, rollback, deletion, account changes, or credential operations. Those controls remain separate and require their existing approvals.

## Validation

Run the credential-free checks with:

```bash
python -m pytest tests/test_assignment_review.py -q
python -m py_compile orville_core/assignment_review.py orville_core/__init__.py tests/test_assignment_review.py
```

These checks validate aggregate outcome comparison, terminal-run filtering, secret-safe output, bounded labels, and input handling. They do not claim production telemetry quality, cross-installation aggregation, causal inference, alerting, or live routing changes.
