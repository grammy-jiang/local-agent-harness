#!/usr/bin/env python3
"""Drift detector — compare an existing repo against current harness templates.

Reports four kinds of drift:

1. **Missing**     — a template file has no counterpart in the repo.
2. **Stale**       — a counterpart exists but lacks required sections /
                     anchors that the current template defines.
3. **Relaxed**     — the file appears to relax a hard constraint or remove a
                     governance section.
4. **Out-of-stage**— the repo's detected stage demands an artifact that is
                     missing or under-specified.

Exit code 0 if no drift, 1 if drift, 2 on usage error. Intended to be run
periodically (CI or manual) and as part of the `check` mode of the
local-agent-harness skill.

Usage:
    python diff_manifests.py [--repo PATH] [--json] [--stage S0|S1|S2|S3]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
from ._paths import assets_dir as _assets_dir

ASSETS = _assets_dir()

from . import assess_repo  # type: ignore

# (template path under assets/, repo destination, list of required anchors
#  that must appear in the destination file for it to be considered "fresh",
#  minimum stage at which the artifact is required — S0 means always)
TARGETS = [
    (
        "GROUNDING.md.tmpl",
        "GROUNDING.md",
        ["Hard Constraints", "Convention Parameters", "Data Classification", "Enforcement"],
        "S0",
    ),
    (
        "AGENTS.md.tmpl",
        "AGENTS.md",
        [
            "Testing",
            "Scope Boundary",
            "Security",
            "PR Checklist",
        ],
        "S0",
    ),
    (
        "plan.md.tmpl",
        ".agent/plan.md.tmpl",
        ["Inputs", "Allowed scope", "Verification", "Decisions log"],
        "S0",
    ),
    ("devcontainer.json.tmpl", ".devcontainer/devcontainer.json", ["AGENT_SANDBOX"], "S0"),
    ("pre-commit-config.yaml.tmpl", ".pre-commit-config.yaml", ["gitleaks"], "S0"),
    (
        "ci/verify.yml.tmpl",
        ".github/workflows/verify.yml",
        ["gitleaks", "Manifest regression"],
        "S1",
    ),
    (
        "ci/governance.yml.tmpl",
        ".github/workflows/governance.yml",
        ["GROUNDING.md", "no-regression"],
        "S2",
    ),
    (
        "readiness-report.md.tmpl",
        ".agent/eval/readiness.md.tmpl",
        ["AI-Readiness Report", "Score"],
        "S0",
    ),
]

_STAGE_ORDER = {"S0": 0, "S1": 1, "S2": 2, "S3": 3}

OVERLAYS = {
    "claude-code": (
        "runtime-overlays/CLAUDE.md.tmpl",
        "CLAUDE.md",
        ["Permission ladder", "claude-code-only"],
    ),
    "codex-cli": ("runtime-overlays/codex.config.tmpl", ".codex/INSTRUCTIONS.md", ["AGENTS.md"]),
    "copilot-cli": (
        "runtime-overlays/copilot-cli.tmpl",
        ".github/copilot-instructions.md",
        ["AGENTS.md", "Copilot"],
    ),
    "cursor": ("runtime-overlays/cursor-rules.tmpl", ".cursor/rules", ["Always", "Never"]),
}

# patterns whose presence in any manifest signals a "relaxed" hard constraint
RELAX_PATTERNS = [
    re.compile(r"allow.{0,12}secret", re.IGNORECASE),
    re.compile(r"disable.{0,8}gitleaks", re.IGNORECASE),
    re.compile(r"skip.{0,8}verify", re.IGNORECASE),
    re.compile(r"bypass.{0,8}permissions", re.IGNORECASE),
]

# Stage gates: artifacts each stage requires
STAGE_REQUIREMENTS = {
    "S0": [
        "GROUNDING.md",
        "AGENTS.md",
        ".agent/plan.md.tmpl",
        ".devcontainer/devcontainer.json",
        ".pre-commit-config.yaml",
    ],
    "S1": [
        "GROUNDING.md",
        "AGENTS.md",
        ".agent/plan.md.tmpl",
        ".devcontainer/devcontainer.json",
        ".pre-commit-config.yaml",
        ".github/workflows/verify.yml",
        ".skills/",
    ],
    "S2": [
        "GROUNDING.md",
        "AGENTS.md",
        ".agent/plan.md.tmpl",
        ".devcontainer/devcontainer.json",
        ".pre-commit-config.yaml",
        ".github/workflows/verify.yml",
        ".github/workflows/governance.yml",
        ".skills/",
        ".agent/eval/readiness.md",
    ],
    "S3": [
        "GROUNDING.md",
        "AGENTS.md",
        ".agent/plan.md.tmpl",
        ".devcontainer/devcontainer.json",
        ".pre-commit-config.yaml",
        ".github/workflows/verify.yml",
        ".github/workflows/governance.yml",
        ".skills/",
        ".agent/eval/readiness.md",
    ],
}


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _detect_runtimes(repo: Path) -> list[str]:
    runtimes = []
    for r, (_, dest, _) in OVERLAYS.items():
        if (repo / dest).exists():
            runtimes.append(r)
    return runtimes


def diff(repo: Path, stage: str | None = None) -> dict:
    if stage is None:
        stage = assess_repo.detect(repo)["stage"]

    missing: list[dict] = []
    stale: list[dict] = []
    relaxed: list[dict] = []

    # core targets (filter by minimum required stage)
    cur_stage_n = _STAGE_ORDER[stage]
    for tmpl, dest, anchors, min_stage in TARGETS:
        if _STAGE_ORDER[min_stage] > cur_stage_n:
            continue
        dst_path = repo / dest
        if not dst_path.exists():
            missing.append({"path": dest, "template": tmpl})
            continue
        text = _read(dst_path)
        miss_anchors = [a for a in anchors if a.lower() not in text.lower()]
        if miss_anchors:
            stale.append({"path": dest, "missing_anchors": miss_anchors, "template": tmpl})
        for rx in RELAX_PATTERNS:
            if rx.search(text):
                relaxed.append({"path": dest, "pattern": rx.pattern})
                break

    # overlays — only check overlays that are actually present
    for runtime in _detect_runtimes(repo):
        tmpl, dest, anchors = OVERLAYS[runtime]
        text = _read(repo / dest)
        miss_anchors = [a for a in anchors if a.lower() not in text.lower()]
        if miss_anchors:
            stale.append(
                {
                    "path": dest,
                    "missing_anchors": miss_anchors,
                    "template": tmpl,
                    "runtime": runtime,
                }
            )
        for rx in RELAX_PATTERNS:
            if rx.search(text):
                relaxed.append({"path": dest, "pattern": rx.pattern, "runtime": runtime})
                break

    # stage requirements
    out_of_stage: list[dict] = []
    for required in STAGE_REQUIREMENTS.get(stage, []):
        rp = repo / required.rstrip("/")
        if not rp.exists():
            out_of_stage.append({"path": required, "required_for": stage})

    has_drift = bool(missing or stale or relaxed or out_of_stage)
    return {
        "stage": stage,
        "drift": has_drift,
        "missing": missing,
        "stale": stale,
        "relaxed": relaxed,
        "out_of_stage": out_of_stage,
        "detected_runtimes": _detect_runtimes(repo),
    }


def _print_human(result: dict) -> None:
    s = result["stage"]
    print(f"Stage: {s}")
    if not result["drift"]:
        print("[OK] no drift detected.")
        return
    if result["missing"]:
        print("\nMissing (init):")
        for m in result["missing"]:
            print(f"  - {m['path']}  ← assets/{m['template']}")
    if result["stale"]:
        print("\nStale (refresh):")
        for s_ in result["stale"]:
            anchors = ", ".join(s_["missing_anchors"])
            print(f"  - {s_['path']}: missing sections [{anchors}]")
    if result["relaxed"]:
        print("\nRelaxed (governance violation):")
        for r in result["relaxed"]:
            print(f"  - {r['path']}: matches /{r['pattern']}/")
    if result["out_of_stage"]:
        print(f"\nMissing for stage {s}:")
        for o in result["out_of_stage"]:
            print(f"  - {o['path']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--stage", choices=["S0", "S1", "S2", "S3"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()
    if not repo.exists():
        print(f"error: {repo} does not exist", file=sys.stderr)
        return 2
    result = diff(repo, args.stage)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_human(result)
    return 1 if result["drift"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
