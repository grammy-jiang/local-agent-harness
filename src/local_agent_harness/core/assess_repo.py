#!/usr/bin/env python3
"""Detect maturity stage and AI-readiness score for a repository.

Usage:
    python assess_repo.py [--repo PATH] [--json]

Stdlib + git only. Soft-detects optional tools via PATH.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _exists(repo: Path, *parts: str) -> bool:
    return (repo.joinpath(*parts)).exists()


def _git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""


def _count_source_files(repo: Path) -> int:
    exts = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".rb",
        ".cs",
        ".cpp",
        ".c",
        ".swift",
        ".scala",
    }
    n = 0
    for root, dirs, files in os.walk(repo):
        # prune common noise
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {".git", "node_modules", ".venv", "venv", "dist", "build", "target", ".agent"}
        ]
        for f in files:
            if Path(f).suffix in exts:
                n += 1
                if n > 1000:
                    return n
    return n


def detect(repo: Path) -> dict:
    has_agents = _exists(repo, "AGENTS.md")
    has_grounding = _exists(repo, "GROUNDING.md")
    has_readme = any(_exists(repo, n) for n in ["README.md", "README.rst", "README"])
    has_ci = (
        _exists(repo, ".github", "workflows")
        or _exists(repo, ".gitlab-ci.yml")
        or _exists(repo, ".circleci", "config.yml")
    )
    has_tests = _exists(repo, "tests") or _exists(repo, "test") or _exists(repo, "__tests__")
    has_src = _exists(repo, "src") or _exists(repo, "lib") or _exists(repo, "app")
    has_devc = _exists(repo, ".devcontainer", "devcontainer.json") or _exists(
        repo, ".devcontainer.json"
    )
    has_precommit = _exists(repo, ".pre-commit-config.yaml") or _exists(
        repo, ".pre-commit-config.yml"
    )
    has_skills = _exists(repo, ".skills")
    has_governance = _exists(repo, ".github", "workflows", "governance.yml")
    has_overlays = any(
        _exists(repo, n)
        for n in ["CLAUDE.md", ".codex/config", ".github/copilot-cli.md", ".cursor/rules"]
    )
    has_logs_ignored = False
    gi = repo / ".gitignore"
    if gi.exists():
        try:
            text = gi.read_text(encoding="utf-8", errors="ignore")
            has_logs_ignored = ".agent" in text or ".env" in text
        except Exception:
            pass

    # Soft tool detection
    tool = lambda name: shutil.which(name) is not None
    has_gitleaks = tool("gitleaks")
    has_semgrep = tool("semgrep")
    has_pip_audit = tool("pip-audit") or tool("osv-scanner")

    src_files = _count_source_files(repo)
    has_tags = bool(_git(repo, "tag", "-l"))

    # Per-axis 0-5 (see references/ai-readiness-rubric.md)
    axes = {}
    # Agent config
    a = 0
    if has_agents:
        a += 1
    if has_agents and has_grounding:
        a = max(a, 2)
    if a >= 2 and has_overlays:
        a = 3
    if a >= 3 and has_skills:
        a = 4
    if a >= 4 and _exists(repo, "scripts", "manifest_regression.py"):
        a = 5
    axes["agent_config"] = a

    # Documentation
    d = 0
    if has_readme:
        d = 1
    if d >= 1 and (repo / "CONTRIBUTING.md").exists():
        d = 2
    if d >= 2 and ((repo / "docs" / "decisions").exists() or (repo / "ADR").exists()):
        d = 3
    if d >= 3 and (repo / "docs").exists():
        d = 4
    if d >= 4 and has_agents:
        d = 5
    axes["documentation"] = d

    # CI/CD
    c = 0
    if has_ci:
        c = 1
    if c >= 1 and has_tests:
        c = 2
    if c >= 2 and (has_precommit or has_gitleaks):
        c = 3
    if c >= 3 and has_governance:
        c = 4
    if c >= 4 and _exists(repo, "scripts", "readiness_report.py"):
        c = 5
    axes["ci_cd"] = c

    # Code structure
    s = 0
    if has_src or src_files >= 1:
        s = 1
    if s >= 1 and has_tests:
        s = 2
    if s >= 2 and has_readme:
        s = 3
    # heuristics for 4-5 are weak from outside; keep conservative
    if s >= 3 and has_agents:
        s = 4
    if s >= 4 and has_governance:
        s = 5
    axes["code_structure"] = s

    # Security
    sec = 0
    if has_logs_ignored:
        sec = 1
    if sec >= 1 and (has_precommit and has_gitleaks):
        sec = 2
    if sec >= 2 and has_pip_audit:
        sec = 3
    if sec >= 3 and has_semgrep:
        sec = 4
    if sec >= 4 and has_devc:
        sec = 5
    axes["security"] = sec

    total = sum(axes.values())

    # Stage determination
    if src_files == 0 and not has_tests and not has_ci:
        stage = "S0"
    elif (not has_tests) or (not has_ci):
        stage = "S1"
    elif not has_tags:
        stage = "S2"
    else:
        stage = "S3"

    # Stage gate floors (from rubric)
    floors = {"S0": 0, "S1": 5, "S2": 12, "S3": 18}
    if total < floors[stage]:
        # Score does not yet meet the stage floor; report stage but flag gap.
        pass

    detected_runtimes = []
    if (repo / "CLAUDE.md").exists():
        detected_runtimes.append("claude-code")
    if (repo / ".codex" / "config").exists():
        detected_runtimes.append("codex-cli")
    if (repo / ".github" / "copilot-cli.md").exists():
        detected_runtimes.append("copilot-cli")
    if (repo / ".cursor" / "rules").exists():
        detected_runtimes.append("cursor")

    missing = []
    if not has_grounding:
        missing.append("GROUNDING.md")
    if not has_agents:
        missing.append("AGENTS.md")
    if not has_devc:
        missing.append(".devcontainer/devcontainer.json")
    if not has_precommit:
        missing.append(".pre-commit-config.yaml")
    if not has_ci:
        missing.append(".github/workflows/verify.yml")
    if not has_governance:
        missing.append(".github/workflows/governance.yml")
    if not has_skills:
        missing.append(".skills/")
    if not has_logs_ignored:
        missing.append(".gitignore (.agent/, .env*)")

    return {
        "stage": stage,
        "axes": axes,
        "total": total,
        "detected_runtimes": detected_runtimes,
        "missing_artifacts": missing,
        "signals": {
            "source_files": src_files,
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_tags": has_tags,
            "has_agents": has_agents,
            "has_grounding": has_grounding,
            "has_devcontainer": has_devc,
            "has_pre_commit": has_precommit,
            "has_governance": has_governance,
            "has_skills_dir": has_skills,
            "soft_tools": {
                "gitleaks": has_gitleaks,
                "semgrep": has_semgrep,
                "pip_audit_or_osv": has_pip_audit,
            },
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()
    if not repo.exists():
        print(f"error: {repo} does not exist", file=sys.stderr)
        return 2
    result = detect(repo)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Repository: {repo}")
        print(f"Stage:      {result['stage']}")
        print(f"Total:      {result['total']} / 25")
        for k, v in result["axes"].items():
            print(f"  {k:16s} {v}/5")
        if result["detected_runtimes"]:
            print(f"Runtimes:   {', '.join(result['detected_runtimes'])}")
        if result["missing_artifacts"]:
            print("Missing:")
            for m in result["missing_artifacts"]:
                print(f"  - {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
