"""Best-effort offline checks for accidentally included secrets and private data.

This is a hygiene gate, not a guarantee. Human review remains mandatory.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".log", ".pyc", ".p12", ".pfx", ".pem", ".key", ".zip", ".7z"}
FORBIDDEN_FOLDERS = {".git", ".venv", "__pycache__", "data", "logs", "reports"}
EXCLUDE = {Path(__file__).resolve()}
PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{30,}\b"),
    re.compile(r"(?i)\b[A-Z]:\\(?:Users|Program Files|Documents|Projects)\\[^\s]+"),
]


def audit(root: Path = ROOT) -> list[str]:
    findings = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if p.is_symlink():
            findings.append(f"symlink: {rel}")
            continue
        if any(x in FORBIDDEN_FOLDERS for x in rel.parts):
            findings.append(f"unexpected folder: {rel}")
            continue
        if not p.is_file():
            continue
        if p.suffix.lower() in BINARY_SUFFIXES or p.name == ".env":
            findings.append(f"unexpected file: {rel}")
            continue
        if p.resolve() in EXCLUDE:
            continue
        try:
            data = p.read_bytes()
            if b"\x00" in data:
                findings.append(f"binary content: {rel}")
                continue
            value = data.decode("utf-8")
        except (UnicodeDecodeError, OSError):
            findings.append(f"unreadable file: {rel}")
            continue
        for index, rule in enumerate(PATTERNS, 1):
            if rule.search(value):
                findings.append(f"possible sensitive pattern {index}: {rel}")
    return findings


if __name__ == "__main__":
    errors = audit()
    if errors:
        for issue in errors:
            print(issue)
        sys.exit(1)
    print("Package hygiene check: PASS (heuristic; manual review still needed)")
