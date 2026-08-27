"""Safe, read-only repository inspection for the IDE Agent."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .agent_contracts import IDEInspectionReport


class IDEInspector:
    def __init__(self, repository_root: str | Path, *, max_file_bytes: int = 2_000_000) -> None:
        self.root = Path(repository_root).expanduser().resolve()
        self.max_file_bytes = max_file_bytes
        if not self.root.is_dir():
            raise ValueError("repository root must be a directory")

    def inspect(self) -> IDEInspectionReport:
        paths: list[str] = []
        entries: list[str] = []
        configs: list[str] = []
        edges: set[tuple[str, str]] = set()
        shared: set[str] = set()
        risks: list[str] = []
        ignored = {".git", ".venv", "node_modules", "__pycache__", ".orville"}
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or any(part in ignored for part in path.relative_to(self.root).parts):
                continue
            try:
                relative = path.relative_to(self.root).as_posix()
                if path.stat().st_size > self.max_file_bytes:
                    risks.append(f"skipped large file: {relative}")
                    continue
            except OSError:
                risks.append(f"unreadable metadata: {path.name}")
                continue
            paths.append(relative)
            name = path.name.lower()
            if name in {"pyproject.toml", "package.json", "package-lock.json", "pnpm-lock.yaml", "requirements.txt", ".env.example", "dockerfile"} or name.endswith((".toml", ".yaml", ".yml", ".ini")):
                configs.append(relative)
            if name in {"readme.md", "main.py", "app.py", "server.py", "cli.py", "index.ts", "index.js", "dockerfile"} or path.parent == self.root and name.startswith(("start-", "launch-")):
                entries.append(relative)
            if path.suffix == ".py":
                self._inspect_python(path, relative, edges, shared, risks)
        return IDEInspectionReport(str(self.root), tuple(paths or ["."]), tuple(sorted(set(entries))), tuple(sorted(edges)), tuple(sorted(set(configs))), tuple(sorted(shared)), tuple(), tuple(sorted(set(risks))))

    def _inspect_python(self, path: Path, relative: str, edges: set[tuple[str, str]], shared: set[str], risks: list[str]) -> None:
        try:
            if path.stat().st_size > self.max_file_bytes:
                return
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=relative)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            risks.append(f"python inspection failed for {relative}: {type(exc).__name__}")
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                edges.update((relative, alias.name) for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                edges.add((relative, node.module))
            elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.lower() in {"api", "main", "run", "create_app", "provider", "router", "handler"} or "interface" in node.name.lower():
                    shared.add(f"{relative}:{node.name}")


def inspect_repository(repository_root: str | Path) -> IDEInspectionReport:
    return IDEInspector(repository_root).inspect()
