#!/usr/bin/env python3
"""Build and update AGENTS.md for a repository.

Follows the agents.md open standard (https://agents.md/):
  AGENTS.md is a "README for agents" — a predictable place for the
  context and instructions AI coding agents need to work on a project.

Strategy:
  1. Detect project info: build/test/lint commands, code style, tech stack.
  2. Generate AGENTS.md with practical sections (setup, testing, conventions)
     plus inlined hard constraints (HC1-HC6) in the Security section.
  3. On subsequent runs, refresh only the auto-generated sections (those
     between sentinel comments) while preserving human edits.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Auto-section sentinels
# ---------------------------------------------------------------------------

_BEGIN = "<!-- local-agent-harness:auto:begin -->"
_END = "<!-- local-agent-harness:auto:end -->"

# ---------------------------------------------------------------------------
# Project info detection
# ---------------------------------------------------------------------------


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""


def detect_project_info(repo: Path) -> dict[str, Any]:
    """Detect build / test / lint commands and style hints from *repo*."""
    info: dict[str, Any] = {
        "stack": [],
        "install_cmds": [],
        "build_cmds": [],
        "test_cmds": [],
        "lint_cmds": [],
        "format_cmds": [],
        "style_hints": [],
        "branch_pattern": "agent/<task-slug>",
        "commit_style": "Conventional Commits",
    }

    # --- Python / pyproject.toml ---
    pp = repo / "pyproject.toml"
    if pp.exists():
        text = _read(pp)
        info["stack"].append("Python")

        # build backend
        if "uv_build" in text or "uv" in text:
            info["install_cmds"].append("pip install -e '.[dev]'  # or: uv sync")
        else:
            info["install_cmds"].append("pip install -e '.[dev]'")

        # test runner
        if "pytest" in text:
            cov_match = re.search(r"--cov-fail-under=(\d+)", text)
            cov = cov_match.group(1) if cov_match else None
            info["test_cmds"].append(f"pytest{'  # --cov-fail-under=' + cov if cov else ''}")
            info["test_cmds"].append("pytest path/to/test_file.py::test_function_name")

        # linter
        if "ruff" in text:
            line_match = re.search(r"line-length\s*=\s*(\d+)", text)
            ll = line_match.group(1) if line_match else "88"
            info["lint_cmds"].append("ruff check src tests")
            info["format_cmds"].append("ruff format src tests")
            info["style_hints"].append(f"Line length: {ll}")
        if "[tool.mypy]" in text:
            strict = "strict = true" in text
            info["lint_cmds"].append("mypy src" + ("  # strict mode" if strict else ""))
            if strict:
                info["style_hints"].append("mypy --strict enforced on src/")
        # Python version
        pyver_match = re.search(r'target-version\s*=\s*"(py\d+)"', text)
        if pyver_match:
            info["style_hints"].append(f"Target Python: {pyver_match.group(1)}")
        # Conventional Commits from pyproject.toml or repo conventions
        if "Conventional Commits" in text:
            info["commit_style"] = "Conventional Commits"

    # --- Node / package.json ---
    pkg = repo / "package.json"
    if pkg.exists():
        import json

        try:
            data = json.loads(_read(pkg))
        except Exception:
            data = {}
        info["stack"].append("Node.js")
        scripts = data.get("scripts", {})
        pm = (
            "pnpm"
            if (repo / "pnpm-lock.yaml").exists()
            else ("yarn" if (repo / "yarn.lock").exists() else "npm")
        )
        if "install" not in [c.split()[0] for c in info["install_cmds"]]:
            info["install_cmds"].append(f"{pm} install")
        for key in ("build", "compile"):
            if key in scripts:
                info["build_cmds"].append(f"{pm} run {key}")
        for key in ("test", "test:unit", "test:ci"):
            if key in scripts:
                info["test_cmds"].append(f"{pm} run {key}")
        for key in ("lint", "lint:fix"):
            if key in scripts:
                info["lint_cmds"].append(f"{pm} run {key}")
        for key in ("format", "fmt"):
            if key in scripts:
                info["format_cmds"].append(f"{pm} run {key}")

    # --- Go ---
    go_mod = repo / "go.mod"
    if go_mod.exists():
        info["stack"].append("Go")
        info["test_cmds"].append("go test ./...")
        info["lint_cmds"].append("go vet ./...")
        info["build_cmds"].append("go build ./...")

    # --- Rust ---
    cargo = repo / "Cargo.toml"
    if cargo.exists():
        info["stack"].append("Rust")
        info["install_cmds"].append("cargo build")
        info["test_cmds"].append("cargo test")
        info["lint_cmds"].append("cargo clippy -- -D warnings")
        info["format_cmds"].append("cargo fmt")

    # --- Makefile / Justfile ---
    for runner_file in ("Makefile", "makefile", "Justfile"):
        if (repo / runner_file).exists():
            info["build_cmds"].insert(0, f"# see {runner_file} for available tasks")

    return info


# ---------------------------------------------------------------------------
# AGENTS.md content generation
# ---------------------------------------------------------------------------


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.rstrip()}\n"


def _cmds_block(cmds: list[str]) -> str:
    if not cmds:
        return "_No commands detected — add them here._\n"
    return "```bash\n" + "\n".join(cmds) + "\n```\n"


def _build_auto_block(info: dict[str, Any]) -> str:
    """Return the auto-section block string (includes sentinels)."""
    stack_str = ", ".join(info["stack"]) if info["stack"] else "general"
    parts: list[str] = [f"<!-- stack: {stack_str} -->"]

    if info["install_cmds"]:
        parts.append(_section("Setup", _cmds_block(info["install_cmds"])))
    if info["build_cmds"]:
        parts.append(_section("Build", _cmds_block(info["build_cmds"])))

    test_body = (
        _cmds_block(info["test_cmds"])
        if info["test_cmds"]
        else "_No test commands detected — add them here._\n"
    )
    parts.append(_section("Testing", test_body))

    lint_cmds = info["lint_cmds"] + info["format_cmds"]
    if lint_cmds:
        parts.append(_section("Lint and Format", _cmds_block(lint_cmds)))

    if info["style_hints"]:
        hints_body = "\n".join(f"- {h}" for h in info["style_hints"]) + "\n"
        parts.append(_section("Code Style", hints_body))

    return _BEGIN + "\n" + "\n".join(parts) + "\n" + _END


def build_agents_md(repo: Path, info: dict[str, Any]) -> str:
    """Return the full AGENTS.md content for *repo* using detected *info*."""
    auto_block = _build_auto_block(info)
    branch = info.get("branch_pattern", "agent/<task-slug>")
    commit = info.get("commit_style", "Conventional Commits")
    static_block = (
        "## Conventions\n\n"
        f"- Branch naming: `{branch}`\n"
        f"- Commit style: {commit}\n"
        "- `from __future__ import annotations` at the top of every Python file.\n"
        "\n"
        "## Scope Boundary\n\n"
        "| Action | Allowed scope |\n"
        "|---|---|\n"
        "| Read   | entire repo |\n"
        "| Edit   | `src/`, `tests/`, `docs/`, `.agent/plan.md` |\n"
        "| Create | within edit scope |\n"
        "| Delete | requires human approval |\n"
        "| Execute | see `.agent/policies/commands.allowlist` |\n"
        "| Network | denied by default |\n"
        "\n"
        "## Security and Hard Constraints\n\n"
        "All hard constraints may never be relaxed.\n\n"
        "- **HC1** \u2014 No plaintext secrets in repository, prompts, logs, or commits.\n"
        "- **HC2** \u2014 No writes outside the repository working tree.\n"
        "- **HC3** \u2014 Destructive commands require explicit human approval.\n"
        "- **HC4** \u2014 Irreversible operations may be authored but never executed by the agent.\n"
        "- **HC5** \u2014 Network egress denied by default; allowlist documented in `AGENTS.md`.\n"
        "- **HC6** \u2014 Red-class data (secrets, PII) never enters prompts, tool args, or logs.\n\n"
        "Use `gitleaks` pre-commit hook.  Run `local-agent-harness validate` before every PR.\n"
        "\n"
        "## PR Checklist\n\n"
        "1. All tests pass.\n"
        "2. Linter and formatter clean.\n"
        "3. No new secrets or SAST findings.\n"
        "4. PR description: change summary, risks, verification evidence.\n"
        "5. Append a `Decisions log` entry in `.agent/plan.md` for non-trivial choices.\n"
    )
    return (
        "# AGENTS.md\n\n"
        "> Agent instructions for this repository.\n"
        "> See also: `.agent/plan.md` (session plan).\n\n"
        + auto_block
        + "\n\n"
        + static_block
    )


# ---------------------------------------------------------------------------
# Render / update
# ---------------------------------------------------------------------------


def update_agents_md(repo: Path, dry: bool) -> str:
    """Create or refresh the auto-generated sections of AGENTS.md."""
    dest = repo / "AGENTS.md"
    info = detect_project_info(repo)
    new_auto = _build_auto_block(info)

    if dest.exists():
        current = dest.read_text(encoding="utf-8", errors="ignore")
        if _BEGIN in current and _END in current:
            updated = re.sub(
                re.escape(_BEGIN) + r".*?" + re.escape(_END),
                new_auto,
                current,
                flags=re.DOTALL,
            )
            if updated == current:
                return "AGENTS.md: auto-sections up to date"
            if dry:
                return "AGENTS.md: would refresh auto-sections"
            dest.write_text(updated, encoding="utf-8")
            return "AGENTS.md: refreshed auto-sections"
        else:
            # Existing file without our sentinels — prepend the auto block
            if dry:
                return "AGENTS.md: would prepend auto-sections (no sentinels found)"
            dest.write_text(new_auto + "\n\n" + current, encoding="utf-8")
            return "AGENTS.md: prepended auto-sections"
    else:
        if dry:
            return "AGENTS.md: would create"
        dest.write_text(build_agents_md(repo, info), encoding="utf-8")
        return "AGENTS.md: created"


if __name__ == "__main__":  # pragma: no cover
    import sys
    import argparse

    ap = argparse.ArgumentParser(description="Build/update AGENTS.md")
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    repo = a.repo.resolve()
    print(update_agents_md(repo, a.dry_run))
    sys.exit(0)
