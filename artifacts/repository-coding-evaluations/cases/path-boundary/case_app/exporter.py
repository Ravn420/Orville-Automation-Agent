"""Small fixture application containing an intentional path-boundary defect."""

from pathlib import Path


def export_text(root: Path, relative_name: str, content: str) -> Path:
    """Write text beneath root and return the destination."""
    destination = root / relative_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination
