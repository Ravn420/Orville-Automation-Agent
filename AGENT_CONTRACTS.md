# Orville Agent Contracts

## Research Agent

The Research Agent receives a `ResearchBrief` containing an objective, research questions, scope, constraints, minimum source count, and whether primary or official evidence is required.

Each retrieved source is represented by `SourceEvidence`. A source must have a stable identifier, an HTTP, HTTPS, or local locator, a title, and an explicit quality classification. Supported quality classes are `primary`, `official`, `secondary`, `tertiary`, and `user-provided`.

Each material result is represented by `ResearchFinding`. A finding must cite one or more source identifiers and separate facts, analysis, assumptions, recommendations, and certainty. `ResearchOutput` validates that source identifiers are unique, the minimum source count is met, required primary evidence is present, and every citation resolves to a supplied source.

## Handoff

`AgentHandoffEnvelope` is the provider-neutral handoff format between specialist agents. It contains the task identifier, source and destination agents, objective, inputs, expected outputs, acceptance criteria, known limitations, and lifecycle status.

## Example

```python
from orville_core import ResearchBrief, ResearchFinding, ResearchOutput, SourceEvidence

brief = ResearchBrief(
    objective="Compare supported authentication methods",
    minimum_sources=2,
    require_primary_sources=True,
)
sources = (
    SourceEvidence("official-docs", "https://example.test/docs", "Official documentation", quality="official"),
    SourceEvidence("independent-review", "https://example.test/review", "Independent review"),
)
finding = ResearchFinding(
    "auth-1",
    "The documented API requires a bearer credential.",
    ("official-docs",),
    certainty="high",
    facts=("The official documentation shows a bearer credential.",),
    assumptions=("The public documentation is current.",),
)
output = ResearchOutput(brief, sources, (finding,))
```

## Validation

Run:

```text
python -m pytest tests/test_agent_contracts.py tests/test_workflow.py tests/test_orchestration.py -q
```

The contract tests verify minimum source counts, primary-source requirements, citation resolution, source locator validation, separated finding content, and handoff identity validation.
