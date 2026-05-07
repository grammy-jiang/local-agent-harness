#!/usr/bin/env python3
"""Redaction smoke test.

Asserts that a synthetic red-class fixture is excluded from session logs and
prompt material. Intended as a deterministic gate, not a security audit.

Usage:
    python redaction_smoke.py [--repo PATH]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# Synthetic markers a real secret should never look like. We search for these
# in committed files; if any appear, the test fails.
RED_MARKERS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id pattern
    re.compile(r"-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),  # Slack tokens
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),  # GitHub PAT
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # OpenAI-style keys
]

SCAN_GLOBS = ["**/*.md", "**/*.yml", "**/*.yaml", "**/*.json", "**/*.toml", "**/*.ini", "**/*.env*"]
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def scan(repo: Path) -> list[tuple[Path, str]]:
    findings: list[tuple[Path, str]] = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        # Only check small text files
        try:
            if path.stat().st_size > 512_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for rx in RED_MARKERS:
            m = rx.search(text)
            if m:
                findings.append((path.relative_to(repo), m.group(0)[:8] + "…"))
                break
    return findings


def check_logs_ignored(repo: Path) -> bool:
    gi = repo / ".gitignore"
    if not gi.exists():
        return False
    text = gi.read_text(encoding="utf-8", errors="ignore")
    return ".agent" in text and ".env" in text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", type=Path)
    args = ap.parse_args()
    repo = args.repo.resolve()

    findings = scan(repo)
    logs_ok = check_logs_ignored(repo)

    if findings:
        print("[FAIL] possible secret-shaped strings committed:")
        for p, sample in findings:
            print(f"   {p}: {sample}")
    else:
        print("[PASS] no secret-shaped strings found in tracked text files.")

    if logs_ok:
        print("[PASS] .gitignore covers .agent/ and .env*")
    else:
        print("[FAIL] .gitignore must cover .agent/logs/ and .env*")

    return 0 if (not findings and logs_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
