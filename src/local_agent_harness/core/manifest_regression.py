#!/usr/bin/env python3
"""Manifest regression suite (TDAD-style).

Treats AGENTS.md and overlays as compiled artifacts. Asserts
invariants that should hold under any harness change.

Usage:
    python manifest_regression.py [--repo PATH]

Exit code 0 on pass, non-zero on failure. Prints a checklist.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def check(repo: Path) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []

    agents = _read(repo / "AGENTS.md")

    results.append(
        (
            "AGENTS.md exists",
            bool(agents),
            "Add AGENTS.md (use `local-agent-harness` skill).",
        )
    )

    # Hard constraints must be inlined in AGENTS.md (HC1-HC6)
    has_hc = bool(re.search(r"\bHC[0-9]+\b", agents))
    results.append(
        (
            "AGENTS.md declares hard constraints (HC*)",
            has_hc,
            "AGENTS.md must contain HC1..HCN bullets in the Security section.",
        )
    )

    secrets_hc = "secret" in agents.lower()
    results.append(
        (
            "AGENTS.md addresses secrets",
            secrets_hc,
            "Add an HC forbidding plaintext secrets to AGENTS.md.",
        )
    )

    # AGENTS.md required sections
    required_sections = [
        "Testing",
        "Scope Boundary",
        "Security",
        "PR Checklist",
    ]
    for sec in required_sections:
        results.append(
            (
                f"AGENTS.md has '{sec}' section",
                sec.lower() in agents.lower(),
                f"Add a '## {sec}' section to AGENTS.md.",
            )
        )

    # plan.md template available
    plan_tmpl = (repo / ".agent" / "plan.md.tmpl").exists()
    results.append(
        (
            ".agent/plan.md.tmpl exists",
            plan_tmpl,
            "Render plan.md.tmpl into .agent/.",
        )
    )

    # gitignore protects .agent/logs and secrets
    gi = _read(repo / ".gitignore")
    results.append(
        (
            ".gitignore covers .agent/logs and .env*",
            ".agent" in gi and ".env" in gi,
            "Append `.agent/logs/` and `.env*` to .gitignore.",
        )
    )

    # Overlays must not relax HCs
    bad = re.compile(r"allow.{0,12}secret|disable.{0,8}gitleaks|skip.{0,8}verify", re.IGNORECASE)
    overlay_paths = [
        repo / "CLAUDE.md",
        repo / ".codex" / "INSTRUCTIONS.md",
        repo / ".github" / "copilot-instructions.md",
    ]
    overlay_clean = True
    for op in overlay_paths:
        if op.exists() and bad.search(_read(op)):
            overlay_clean = False
    results.append(
        (
            "Runtime overlays do not relax hard constraints",
            overlay_clean,
            "Remove HC-relaxing language from overlays.",
        )
    )

    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", type=Path)
    args = ap.parse_args()
    repo = args.repo.resolve()
    results = check(repo)
    failed = 0
    for name, ok, fix in results:
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name}")
        if not ok:
            print(f"       fix: {fix}")
            failed += 1
    print(f"\n{len(results) - failed}/{len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
