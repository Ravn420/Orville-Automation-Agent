# Isolated Behavioral Evaluation

Orville evaluates generated software through declared behavioral acceptance cases rather than source-text similarity. `orville_core.behavioral_evaluation.evaluate_generated_software` copies a candidate into a temporary directory, hashes the candidate tree, runs each argument-list command without a shell, enforces a bounded timeout, and checks exit status plus required and forbidden paths.

## Reproducibility contract

Each result records the candidate SHA-256, exact commands, Python version, timeout and output limits, shell policy, and temporary-copy isolation mode. Output is bounded and the candidate copy is removed after evaluation. Tests should use synthetic local fixtures and local dependencies; no credentials or external services are required.

## Acceptance-case example

```python
from orville_core.behavioral_evaluation import BehavioralAcceptanceCase, evaluate_generated_software

result = evaluate_generated_software(
    "generated-project",
    [BehavioralAcceptanceCase(
        name="smoke",
        command=("python", "-m", "generated_project"),
        required_paths=("generated_project/output.json",),
        forbidden_paths=("secrets.txt",),
    )],
)
assert result.passed
```

The evaluator deliberately does not claim operating-system, container, network, dependency-installation, or adversarial sandbox isolation. Those controls remain deployment-owned and should be supplied by a stronger sandbox adapter when required. Behavioral results are evidence for acceptance, not a security certification.


## Repository-level coding evaluations

`CodingEvaluationSpec` models a realistic issue identifier, a reviewable unified-diff patch, an optional dependency-installation command, a focused test command, and a broader regression command. `evaluate_coding_change` copies the candidate repository into a temporary workspace, applies the patch with `git apply --whitespace=error`, runs the dependency and test stages without a shell, and returns separate checks plus SHA-256 metadata for the patch and base candidate.

The dependency command is optional and must be a local, synthetic, or otherwise policy-approved command. The evaluator does not download packages, use credentials, or enable network access by itself. A failed patch, dependency installation, focused test, or regression check stops later stages and produces a failed result rather than silently accepting a partial evaluation.
