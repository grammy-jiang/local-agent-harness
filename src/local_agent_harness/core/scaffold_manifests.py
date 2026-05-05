#!/usr/bin/env python3
"""Render and synchronize harness manifests.

Three modes:

* ``init``     — render any missing artifacts. Existing files are never
                 overwritten. (Default. Equivalent to the original
                 bootstrap behavior.)
* ``refresh``  — for *stale* artifacts (those missing required anchors
                 according to ``diff_manifests``), back up the original to
                 ``<file>.bak`` and rewrite from the current template.
                 Requires ``--apply`` to actually write; without it, prints
                 a plan only.
* ``check``    — never writes. Prints drift and exits non-zero on any
                 drift. Suitable for CI.

The skill works on **any state** of the repository: empty, partially
configured, or fully mature. Run with ``--mode check`` first to see what
needs attention.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
from ._paths import assets_dir as _assets_dir
ASSETS = _assets_dir()

from . import diff_manifests  # type: ignore
from . import assess_repo  # type: ignore

CORE_FILES = [
    ("GROUNDING.md.tmpl", "GROUNDING.md"),
    ("AGENTS.md.tmpl", "AGENTS.md"),
]

AGENT_DIR_FILES = [
    ("plan.md.tmpl", ".agent/plan.md.tmpl"),
    ("readiness-report.md.tmpl", ".agent/eval/readiness.md.tmpl"),
]

DEVCONTAINER = ("devcontainer.json.tmpl", ".devcontainer/devcontainer.json")
PRECOMMIT    = ("pre-commit-config.yaml.tmpl", ".pre-commit-config.yaml")
CI_VERIFY    = ("ci/verify.yml.tmpl", ".github/workflows/verify.yml")
CI_GOV       = ("ci/governance.yml.tmpl", ".github/workflows/governance.yml")

RUNTIME_OVERLAYS = {
    "claude-code": ("runtime-overlays/CLAUDE.md.tmpl", "CLAUDE.md"),
    "codex-cli":   ("runtime-overlays/codex.config.tmpl", ".codex/config"),
    "copilot-cli": ("runtime-overlays/copilot-cli.tmpl", ".github/copilot-cli.md"),
    "cursor":      ("runtime-overlays/cursor-rules.tmpl", ".cursor/rules"),
}

STAGE_INFRA = {
    "S0": [DEVCONTAINER, PRECOMMIT],
    "S1": [DEVCONTAINER, PRECOMMIT, CI_VERIFY],
    "S2": [DEVCONTAINER, PRECOMMIT, CI_VERIFY, CI_GOV],
    "S3": [DEVCONTAINER, PRECOMMIT, CI_VERIFY, CI_GOV],
}

GITIGNORE_LINES = [".agent/logs/", ".env", ".env.*", "*.pem", "*.key"]


def _render_missing(src: Path, dst: Path, dry: bool) -> str:
    if dst.exists():
        return f"skip (exists): {dst}"
    if dry:
        return f"would render: {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return f"rendered: {dst}"


def _refresh_stale(src: Path, dst: Path, apply: bool, dry: bool) -> str:
    if not dst.exists():
        return f"missing (use --mode init): {dst}"
    if dry or not apply:
        return f"would refresh (backup + rewrite): {dst}"
    bak = dst.with_suffix(dst.suffix + ".bak")
    if bak.exists():
        bak.unlink()
    shutil.copyfile(dst, bak)
    shutil.copyfile(src, dst)
    return f"refreshed (backup at {bak.name}): {dst}"


def _update_gitignore(repo: Path, dry: bool) -> str:
    gi = repo / ".gitignore"
    existing = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
    needed = [ln for ln in GITIGNORE_LINES if ln not in existing]
    if not needed:
        return "gitignore: already covers .agent/ and secrets"
    block = "\n# local-agent-harness\n" + "\n".join(needed) + "\n"
    if dry:
        return f"would append to .gitignore: {needed}"
    with gi.open("a", encoding="utf-8") as f:
        f.write(block)
    return f"appended to .gitignore: {needed}"


def _planned_targets(stage: str, runtimes: list[str]) -> list[tuple[str, str]]:
    items = list(CORE_FILES) + list(AGENT_DIR_FILES) + list(STAGE_INFRA[stage])
    for r in runtimes:
        items.append(RUNTIME_OVERLAYS[r])
    return items


def cmd_init(repo: Path, stage: str, runtimes: list[str], dry: bool) -> int:
    actions: list[str] = []
    for src, dst in _planned_targets(stage, runtimes):
        actions.append(_render_missing(ASSETS / src, repo / dst, dry))
    if stage in {"S1", "S2", "S3"}:
        skills_dir = repo / ".skills"
        if not skills_dir.exists():
            if dry:
                actions.append(f"would create: {skills_dir}/")
            else:
                skills_dir.mkdir(parents=True, exist_ok=True)
                (skills_dir / "_template.SKILL.md").write_text(
                    (ASSETS / "repo-skill.SKILL.md.tmpl").read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                actions.append(f"created: {skills_dir}/_template.SKILL.md")
    actions.append(_update_gitignore(repo, dry))
    for a in actions:
        print(a)
    return 0


def cmd_refresh(repo: Path, stage: str, runtimes: list[str], apply: bool, dry: bool) -> int:
    drift = diff_manifests.diff(repo, stage=stage)
    stale_paths   = {s["path"]: s.get("template") for s in drift["stale"]}
    missing_paths = {m["path"]: m["template"]     for m in drift["missing"]}

    if drift["relaxed"]:
        print("BLOCKED: governance violations detected; resolve manually before refresh:")
        for r in drift["relaxed"]:
            print(f"  - {r['path']}: matches /{r['pattern']}/")
        return 2

    if not stale_paths and not missing_paths:
        print("no drift; nothing to refresh.")
        return 0

    actions: list[str] = []
    for dest, tmpl in stale_paths.items():
        if tmpl is None:
            continue
        actions.append(_refresh_stale(ASSETS / tmpl, repo / dest, apply, dry))
    for dest, tmpl in missing_paths.items():
        actions.append(_render_missing(ASSETS / tmpl, repo / dest, dry or not apply))

    if not apply and not dry:
        print("plan only; re-run with --apply to write changes.")
    for a in actions:
        print(a)
    return 0


def cmd_check(repo: Path, stage: str) -> int:
    result = diff_manifests.diff(repo, stage=stage)
    diff_manifests._print_human(result)
    return 1 if result["drift"] else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--mode", choices=["init", "refresh", "check"], default="init")
    ap.add_argument("--runtime", action="append", default=[],
                    choices=sorted(RUNTIME_OVERLAYS))
    ap.add_argument("--stage", choices=["S0", "S1", "S2", "S3"])
    ap.add_argument("--apply", action="store_true",
                    help="for --mode refresh: actually write files (otherwise plan only)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repo = args.repo.resolve()
    if not repo.exists():
        print(f"error: {repo} does not exist", file=sys.stderr)
        return 2

    stage = args.stage or assess_repo.detect(repo)["stage"]
    print(f"# local-agent-harness mode={args.mode} stage={stage} repo={repo}")

    if args.mode == "init":
        return cmd_init(repo, stage, args.runtime, args.dry_run)
    if args.mode == "refresh":
        return cmd_refresh(repo, stage, args.runtime, args.apply, args.dry_run)
    if args.mode == "check":
        return cmd_check(repo, stage)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
