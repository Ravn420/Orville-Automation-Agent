import json
from pathlib import Path
import re

from orville_core.evaluation_datasets import EXPECTED_TASK_TYPES, load_evaluation_catalog


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "evaluation-datasets.json"
EXPECTED_TYPES = {
    "planning",
    "code_generation",
    "debugging",
    "refactoring",
    "research",
    "gui_workflows",
    "model_import",
}
SECRET_PATTERNS = (
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"sk-[A-Za-z0-9]{20,}",
    r"AIza[0-9A-Za-z_-]{30,}",
    r"BEGIN [A-Z ]*PRIVATE KEY",
    r"Bearer\s+[A-Za-z0-9._-]{20,}",
)


def test_loader_accepts_the_committed_catalog():
    datasets = load_evaluation_catalog(CATALOG)
    assert len(datasets) == 7
    assert sum(len(dataset.golden_cases) for dataset in datasets) == 14


def test_catalog_covers_required_task_types_with_stable_cases():
    parsed = load_evaluation_catalog(CATALOG)
    assert {dataset.task_type for dataset in parsed} == EXPECTED_TASK_TYPES
    assert sum(len(dataset.golden_cases) for dataset in parsed) == 14

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["schema_version"] == "1.0"
    datasets = catalog["datasets"]
    assert {dataset["task_type"] for dataset in datasets} == EXPECTED_TYPES
    assert len({dataset["id"] for dataset in datasets}) == len(datasets)

    case_ids = []
    for dataset in datasets:
        cases = dataset["golden_cases"]
        assert len(cases) >= 2
        assert dataset["id"].replace("-", "_") == dataset["task_type"]
        for case in cases:
            case_ids.append(case["id"])
            assert case["prompt"]
            assert case["required_behaviors"]
            assert case["prohibited_behaviors"]
            assert case["oracle"]["artifact"]
            assert case["oracle"]["must_include"]
    assert len(case_ids) == len(set(case_ids))


def test_catalog_is_synthetic_and_secret_free():
    text = CATALOG.read_text(encoding="utf-8")
    assert not any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SECRET_PATTERNS)
    catalog = json.loads(text)
    assert "external credentials" in catalog["governance"]["source_policy"]
    assert "temporary" in catalog["governance"]["execution_policy"]
    assert "uncertain" in catalog["governance"]["scoring_policy"]


def test_each_dataset_has_task_specific_safety_boundaries():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    joined = {
        dataset["task_type"]: " ".join(
            item
            for case in dataset["golden_cases"]
            for item in case["required_behaviors"] + case["prohibited_behaviors"]
        ).lower()
        for dataset in catalog["datasets"]
    }
    assert "approval" in joined["planning"]
    assert "redaction" in joined["code_generation"]
    assert "reproduction" in joined["debugging"]
    assert "compatibility" in joined["refactoring"]
    assert "citation" in joined["research"] or "source" in joined["research"]
    assert "accessibility" in joined["gui_workflows"]
    assert "checksum" in joined["model_import"]
