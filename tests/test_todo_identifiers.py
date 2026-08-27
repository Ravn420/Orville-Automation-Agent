from pathlib import Path
import re

from tools.assign_todo_ids import assign_ids


TODO = Path(__file__).parents[1] / "TODO.md"
ID = re.compile(r"<!-- task-id:(TODO-[0-9a-f]{12}) -->")
CHECKLIST = re.compile(r"^- \[(?: |-|x|!|~)\] .+<!-- task-id:TODO-[0-9a-f]{12} -->$")


def test_every_checklist_item_has_a_unique_machine_readable_id() -> None:
    lines = TODO.read_text(encoding="utf-8").splitlines()
    checklist = [line for line in lines if CHECKLIST.match(line)]
    identifiers = [ID.search(line).group(1) for line in checklist if ID.search(line)]
    assert len(checklist) > 0
    assert len(identifiers) == len(checklist)
    assert len(identifiers) == len(set(identifiers))
    assert all(ID.search(line) for line in checklist)


def test_identifier_generation_is_idempotent() -> None:
    source = TODO.read_text(encoding="utf-8")
    updated, changed = assign_ids(source)
    assert changed == 0
    assert updated == source


def test_identifier_generation_preserves_status_markers_and_text() -> None:
    source = "- [!] blocked task\n- [-] active task\n- [x] done task\n"
    updated, changed = assign_ids(source)
    assert changed == 3
    assert "- [!] blocked task" in updated
    assert "- [-] active task" in updated
    assert "- [x] done task" in updated
    assert len(ID.findall(updated)) == 3


def test_identifier_generation_preserves_marker_with_completion_evidence() -> None:
    source = "- [x] Completed. <!-- task-id:TODO-0123456789ab --> Focused tests passed.\n"
    updated, changed = assign_ids(source)
    assert changed == 0
    assert updated == source
