from __future__ import annotations

import re
import subprocess
from pathlib import Path

PATTERNS = {
    "private-key": re.compile(r"BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY"),
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github-token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "openai-style-key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "bearer-token": re.compile(r"Bearer\s+[A-Za-z0-9._~-]{20,}"),
    "password-assignment": re.compile(r"password\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.I),
}

tracked = subprocess.check_output(["git", "ls-files", "-z"], text=False).split(b"\0")
findings: list[tuple[str, str]] = []
for raw in tracked:
    if not raw:
        continue
    path = Path(raw.decode("utf-8", "surrogateescape"))
    try:
        data = path.read_bytes()
    except OSError:
        continue
    if b"\0" in data:
        continue
    text = data.decode("utf-8", "ignore")
    for name, pattern in PATTERNS.items():
        if pattern.search(text):
            findings.append((name, str(path)))
for name, path in findings:
    print(f"{name}\t{path}")
print(f"SCAN_FILES={len([item for item in tracked if item])}")
print(f"FINDINGS={len(findings)}")
raise SystemExit(1 if findings else 0)
