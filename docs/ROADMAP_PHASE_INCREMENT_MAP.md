# Roadmap phase and implementation-increment map

The roadmap uses broad phase headings to group related capability families. Implementation increments are tracked separately so completed provider work is not confused with environment reliability or media work.

| Broad phase | Broad label | Implementation increment | Scope |
|---|---|---|---|
| Phase 2 | Agent Contracts | Phase 2.7 — Model Provider Integration | Provider-neutral cloud and local model adapters, capability metadata, and routing contracts. |
| Phase 3 | Environment and Integration Reliability | Phase 3.1 — Runtime health | Runtime readiness and health checks. |
| Phase 3 | Environment and Integration Reliability | Phase 3.2 — Connector management | Connector configuration and boundary controls. |
| Phase 3 | Environment and Integration Reliability | Phase 3.3 — Cloud and Local Model Endpoints | Endpoint validation and environment-specific integration reliability. |
| Phase 6 | Web, Mobile, Media, and Document Workflows | Phase 6.2 — Image, audio, and video | Media generation, validation, provenance, and visual verification. |

Broad phase labels describe capability families and are not implementation tasks. Provider work is tracked under Phase 2.7, while media work is tracked under Phase 6.2. Phase 3 increments remain reliability-focused and must not be relabeled as provider or media implementation work.

The machine-readable source is `config/roadmap-phase-increments.json`. The acceptance checks are in `tests/test_roadmap_phase_increments.py` and complement the normalized heading checks in `tests/test_todo_heading_normalization.py`.
