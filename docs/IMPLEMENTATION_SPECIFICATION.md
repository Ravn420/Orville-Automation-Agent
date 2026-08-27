# Implementation Specification Standard

Every implementation request must begin with a written specification before source changes. The specification is the authoritative task contract and must identify the objective, assumptions, in-scope and out-of-scope behavior, affected components, data handling, security constraints, and user-visible effects.

## Required fields

| Field | Required content |
|---|---|
| Objective | One precise sentence describing the desired outcome. |
| Inputs | User inputs, configuration, files, external responses, and trust level. |
| Outputs | Files, API responses, UI states, artifacts, and side effects. |
| Interfaces | Modules, routes, schemas, commands, environment variables, and compatibility constraints. |
| Dependencies | Runtime packages, services, platform features, and project control files. |
| Risks | Security, privacy, reliability, portability, migration, and rollback risks. |
| Acceptance tests | Deterministic tests mapped to each acceptance criterion. |
| Validation | Focused tests, compilation, static checks, platform checks, and limitations. |

## Execution rule

The worker records the specification path in the task state before implementation, updates it when requirements change, and does not claim completion until every acceptance test passes. Sensitive values are represented by placeholders or references only; credentials, cookies, personal information, and private artifacts must never be included in a specification.
