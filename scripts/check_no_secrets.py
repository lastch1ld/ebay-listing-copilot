#!/usr/bin/env python3
"""Fail if tracked files contain credential patterns or private runtime files.

Scans files tracked by Git (respecting .gitignore) for eBay/OpenAI key
patterns, bearer tokens, private keys, non-example .env files, SQLite
files, and upload directories. A line containing the literal marker
SAFE_FAKE_CREDENTIAL is treated as an intentional fictional fixture and
is skipped.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SAFE_MARKER = "SAFE_FAKE_CREDENTIAL"

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("eBay OAuth token", re.compile(r"v\^1\.1#[A-Za-z0-9+/=]{20,}")),
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("Generic bearer token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

FORBIDDEN_PATH_PATTERNS = [
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)\.env\.[^/]+$"),
    re.compile(r"\.sqlite3?$"),
    re.compile(r"(^|/)uploads/"),
]


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def check_path(path: str) -> str | None:
    if path.endswith(".env.example"):
        return None
    for pattern in FORBIDDEN_PATH_PATTERNS:
        if pattern.search(path):
            return f"forbidden tracked path: {path}"
    return None


def check_contents(path: str) -> list[str]:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    problems: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if SAFE_MARKER in line:
            continue
        for label, pattern in PATTERNS:
            if pattern.search(line):
                problems.append(f"{path}:{line_number}: possible {label}")
    return problems


def main() -> int:
    problems: list[str] = []
    for path in tracked_files():
        path_problem = check_path(path)
        if path_problem:
            problems.append(path_problem)
            continue
        problems.extend(check_contents(path))

    if problems:
        print("Potential secrets or private runtime files found:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("No tracked secrets or private runtime files found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
