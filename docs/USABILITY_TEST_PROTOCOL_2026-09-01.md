# First-Time-User Usability Test Protocol

**Related TODO:** `TODO-49e3f6d26ee8`
**Status:** Blocked pending participant access and executable GUI target
**Review date:** 2026-09-01

## Required sessions

Each participant must complete task creation, model setup, local model import, execution review, verification review, and artifact export without operator coaching. Record task completion, critical errors, hesitation points, recovery attempts, and whether the participant understood the next permitted action.

| Session | Required states | Success evidence |
|---|---|---|
| Task creation | Empty form, valid submission, invalid input, preserved input after error | Completion time, errors, and participant explanation of acceptance criteria |
| Model setup | Local endpoint, unavailable runtime, protected credential reference, recovery | Correct selection and safe recovery without exposing secrets |
| Local model import | Valid manifest, unsupported field, malformed file, cancellation | Import result, error comprehension, and no unsafe fallback |
| Execution review | Ready, running, blocked, partial, failed, completed | Correct interpretation of state and available controls |
| Verification review | Passing and failing acceptance evidence | Correct distinction between execution and verified completion |
| Artifact export | Available, unavailable, permission denied, download confirmation | Correct destination understanding and safe recovery |

## Analysis and privacy

Use a minimum of five participants per supported target class when feasible. Collect only task metrics and consented usability observations. Do not retain prompts, credentials, cookies, private files, raw provider responses, or identifiable recordings unless separately approved and redacted.

## Current limitation

The recovered checkout contains no executable GUI target and no participant or device-testing environment. This protocol is retained as the reproducible plan; no human usability results are claimed.
