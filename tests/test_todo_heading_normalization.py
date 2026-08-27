from pathlib import Path
import re


TODO = Path(__file__).parents[1] / "TODO.md"


def _headings() -> list[str]:
    return [line.strip() for line in TODO.read_text(encoding="utf-8").splitlines() if line.startswith("## ")]


def test_primary_phase_headings_use_unique_sequential_section_numbers() -> None:
    headings = _headings()
    expected = [
        "## 5. Phase 0 — Governance and Project State",
        "## 6. Phase 1 — Orchestration Core",
        "## 7. Phase 2 — Agent Contracts",
        "## 8. Phase 3 — Environment and Integration Reliability",
        "## 9. Phase 4 — Code Generation and Delivery Pipeline",
        "## 10. Phase 5 — Research and Evidence Workflows",
        "## 11. Phase 6 — Web, Mobile, Media, and Document Workflows",
        "## 11A. Phase 6A — Graphical User Interface",
        "## 12. Phase 7 — Automation, Scheduling, and Persistent Execution",
        "## 13. Phase 8 — Security and Safety",
        "## 14. Phase 9 — Testing and Quality System",
        "## 15. Phase 10 — Deployment and Operations",
        "## 16. Phase 11 — Documentation and User Experience",
        "## 17. Phase 12 — Continuous Improvement",
    ]
    phase_headings = [heading for heading in headings if re.match(r"^## (?:\d+|\d+A)\. Phase (?:\d+|\d+A) ", heading)]
    assert phase_headings == expected
    assert len(phase_headings) == len(set(phase_headings))


def test_phase_subheadings_match_their_normalized_parent() -> None:
    lines = TODO.read_text(encoding="utf-8").splitlines()
    gui_subheadings = [line.strip() for line in lines if line.startswith("### 11A.")]
    document_subheadings = [line.strip() for line in lines if re.match(r"^### 11\.\d+ ", line)]
    assert gui_subheadings == [
        "### 11A.1 Product experience and visual design",
        "### 11A.2 Core GUI workflows",
        "### 11A.3 Usability, accessibility, and responsive behavior",
        "### 11A.4 GUI engineering and quality",
    ]
    assert document_subheadings == [
        "### 11.1 Web and mobile",
        "### 11.2 Image, audio, and video",
        "### 11.3 Documents and presentations",
    ]


def test_heading_normalization_item_is_complete() -> None:
    text = TODO.read_text(encoding="utf-8")
    assert re.search(r"- \[-?x?\] Renumber and normalize duplicated or inconsistent phase headings", text)
