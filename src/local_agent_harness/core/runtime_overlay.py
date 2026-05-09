#!/usr/bin/env python3
"""Generate agent-specific runtime overlay files for each AI coding assistant.

DRY principle
-------------
``AGENTS.md`` is the single source of truth for **behavioral rules**:
hard constraints, scope boundaries, stop conditions, and PR checklist.
Every runtime overlay either imports AGENTS.md directly (Claude Code) or
defers to it (Codex, Copilot).

``copilot-instructions.md`` serves a different purpose: **project context**
for all GitHub Copilot features (Chat, Code Review, Cloud Agent).  It
describes what the project is, how to build/test/validate it, and where
things live — not how the agent should behave.  See:
  references/copilot-instructions-standard.md

Supported runtimes
------------------
* ``claude-code``   → ``CLAUDE.md`` (with ``@AGENTS.md`` import) +
                      ``.claude/settings.json`` (project permissions)
* ``copilot-cli``   → ``.github/copilot-instructions.md`` (project context)
* ``codex-cli``     → ``.codex/INSTRUCTIONS.md`` (Codex-specific supplements)

None of these functions overwrite a file that already exists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import agents_builder as _agents_builder

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _write_if_missing(path: Path, content: str, dry: bool) -> str:
    """Write *content* to *path* if it does not yet exist."""
    if path.exists():
        return f"skip (exists): {path}"
    if dry:
        return f"would render: {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"rendered: {path}"


# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------

# CLAUDE.md uses Claude Code's @path/to/file import syntax so the shared
# AGENTS.md content is loaded automatically — no duplication required.
_CLAUDE_MD = """\
# CLAUDE.md — Claude Code project instructions

<!-- DRY: shared build commands, conventions, and scope boundary live in  -->
<!-- AGENTS.md.  This file imports it and adds Claude Code-only settings. -->

@AGENTS.md

<!-- claude-code-only: begin -->
## Claude Code–specific behaviour

### Permission ladder
- Default mode: `default`  (switch to `plan` for risky changes)
- Allowed tools: `Read`, `Glob`, `Grep`, `Edit`, `Bash` (allow-listed in
  `.claude/settings.json`)
- Denied tools and paths: see `.claude/settings.json` (authoritative; do not duplicate here)
- MCP servers: none configured by default — add to `.mcp.json`

### When to enter Plan mode
Activate Plan mode (propose before writing) for:
cross-cutting refactors, dependency upgrades, schema / DB migrations, and
any request containing the words *refactor*, *upgrade*, *migrate*, or
*redesign*.

### Compaction
Compact at 70 % of context window.
Always retain: `AGENTS.md`, current `plan.md`, last 5 tool calls, open diff.

### Stop conditions
- If a tool call fails 3× consecutively → stop and ask the user.
<!-- Out-of-scope write behaviour is covered by AGENTS.md § Stop Conditions. -->
<!-- claude-code-only: end -->
"""


def _build_claude_settings(info: dict[str, Any]) -> str:
    """Return a ``.claude/settings.json`` string derived from *info*."""
    allow: list[str] = []

    # Allow detected project commands
    for cmd_list in (
        info.get("install_cmds", []),
        info.get("build_cmds", []),
        info.get("test_cmds", []),
        info.get("lint_cmds", []),
        info.get("format_cmds", []),
    ):
        for cmd in cmd_list:
            base = cmd.split()[0]
            entry = f"Bash({base} *)"
            if entry not in allow:
                allow.append(entry)

    # Always allow safe read-only git operations
    for entry in [
        "Bash(git diff *)",
        "Bash(git status *)",
        "Bash(git log *)",
        "Bash(git add *)",
        "Bash(git commit *)",
        "Bash(git push *)",
    ]:
        if entry not in allow:
            allow.append(entry)

    settings: dict[str, Any] = {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "permissions": {
            "allow": allow,
            "deny": [
                "Bash(curl *)",
                "Bash(wget *)",
                "Read(./.env)",
                "Read(./.env.*)",
                "Read(./secrets/**)",
            ],
        },
    }
    return json.dumps(settings, indent=2) + "\n"


def render_claude_code(repo: Path, dry: bool) -> list[str]:
    """Create ``CLAUDE.md`` and ``.claude/settings.json`` if missing."""
    info = _agents_builder.detect_project_info(repo)
    return [
        _write_if_missing(repo / "CLAUDE.md", _CLAUDE_MD, dry),
        _write_if_missing(
            repo / ".claude" / "settings.json",
            _build_claude_settings(info),
            dry,
        ),
    ]


# ---------------------------------------------------------------------------
# GitHub Copilot
# ---------------------------------------------------------------------------

# .github/copilot-instructions.md provides **project context** for all GitHub
# Copilot features (Chat, Code Review, Cloud Agent).  Behavioral rules
# (hard constraints, scope, stop conditions, PR checklist) all live in AGENTS.md.
# Reference: references/copilot-instructions-standard.md


def _repo_layout_tree(repo: Path) -> str:
    """Return a minimal top-level directory tree string for the repo."""
    _skip = {
        ".git", "__pycache__", ".mypy_cache", ".ruff_cache",
        ".pytest_cache", ".coverage", "dist", "build", ".eggs",
        ".venv", "node_modules", ".tox",
    }
    try:
        entries = sorted(
            [p for p in repo.iterdir() if p.name not in _skip],
            key=lambda p: (p.is_file(), p.name.lstrip(".")),
        )
    except PermissionError:
        return "."
    lines = ["."]
    for i, p in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(f"{connector}{p.name}{'/' if p.is_dir() else ''}")
    return "\n".join(lines)


def _build_copilot_instructions(repo: Path, info: dict[str, Any]) -> str:
    """Build .github/copilot-instructions.md content from detected project info.

    Follows the GitHub Copilot documentation:
    https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/
    add-custom-instructions/add-repository-instructions

    DRY note: project build/test/lint commands live in AGENTS.md (§Setup,
    §Testing, §Lint and Format auto-sections), which all agent runtimes read
    natively.  This file contains only project context (overview, layout,
    tech stack) and harness-validation commands that are unique to the
    Copilot workflow.  Do not repeat project commands here.
    """
    stack_str = (
        ", ".join(info["stack"])
        if info["stack"]
        else "Not yet determined — update this section when source code is added."
    )

    # Harness validation commands only — project build/test/lint are in AGENTS.md
    harness_cmds = [
        "# Agent harness",
        "local-agent-harness check --repo .",
        "local-agent-harness validate --repo .",
        "",
        "# Pre-commit",
        "pre-commit install       # first time only",
        "pre-commit run --all-files",
    ]
    cmds_block = "```bash\n" + "\n".join(harness_cmds) + "\n```"

    layout = _repo_layout_tree(repo)

    return (
        "# Repository Overview\n\n"
        "_TODO: add a brief description of what this repository does._\n\n"
        "## Tech Stack\n\n"
        f"{stack_str}\n\n"
        "## Project Layout\n\n"
        f"```\n{layout}\n```\n\n"
        "## Build & Validation Commands\n\n"
        "<!-- Project setup, build, test, and lint commands are in AGENTS.md\n"
        "     (§Setup, §Testing, §Lint and Format) — read natively by all agent\n"
        "     runtimes (Claude Code, Codex CLI, Copilot Cloud Agent). -->\n\n"
        f"{cmds_block}\n\n"
        "## Copilot-specific guidance\n\n"
        "<!-- Add Copilot-only supplements here as the project grows\n"
        "     (e.g., code review focus areas, chat response preferences).\n"
        "     Behavioral constraints, scope boundaries, stop conditions,\n"
        "     and PR checklist live in AGENTS.md. -->\n\n"
        "## Notes\n\n"
        "- `.agent/eval/` is gitignored; readiness reports are local only.\n"
    )


def render_copilot(repo: Path, dry: bool) -> list[str]:
    """Create ``.github/copilot-instructions.md`` if missing.

    Generates project-context content per the GitHub Copilot documentation.
    Behavioral rules (hard constraints, scope, PR checklist) are in AGENTS.md.
    """
    info = _agents_builder.detect_project_info(repo)
    return [
        _write_if_missing(
            repo / ".github" / "copilot-instructions.md",
            _build_copilot_instructions(repo, info),
            dry,
        ),
    ]


# ---------------------------------------------------------------------------
# OpenAI Codex CLI
# ---------------------------------------------------------------------------

# Codex CLI reads AGENTS.md natively.  This file adds only Codex-specific
# settings that cannot live in AGENTS.md.
_CODEX_INSTRUCTIONS = """\
<!-- .codex/INSTRUCTIONS.md                                                   -->
<!-- Codex CLI-specific supplements.  Codex reads AGENTS.md natively.         -->
<!-- This file adds only Codex CLI-specific behaviour.                         -->

## Codex-specific settings

- Default approval mode: `suggest` (confirm each edit before writing).
- Max turns per session: 40.
- Sandbox: devcontainer (see `.devcontainer/devcontainer.json`).
- Session transcripts: `.agent/logs/`.

<!-- Stop conditions are defined in AGENTS.md (shared spine). -->
"""


def render_codex(repo: Path, dry: bool) -> list[str]:
    """Create ``.codex/INSTRUCTIONS.md`` pointer if missing."""
    return [
        _write_if_missing(
            repo / ".codex" / "INSTRUCTIONS.md",
            _CODEX_INSTRUCTIONS,
            dry,
        ),
    ]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def render_runtime(runtime: str, repo: Path, dry: bool) -> list[str]:
    """Render overlay files for *runtime* in *repo*.

    Returns a list of human-readable action strings (one per file).
    Raises ``ValueError`` for unknown runtime keys.
    """
    if runtime == "claude-code":
        return render_claude_code(repo, dry)
    if runtime == "copilot-cli":
        return render_copilot(repo, dry)
    if runtime == "codex-cli":
        return render_codex(repo, dry)
    raise ValueError(f"Unknown runtime: {runtime!r}")


if __name__ == "__main__":  # pragma: no cover
    import sys

    _repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    for _rt in ["claude-code", "copilot-cli", "codex-cli"]:
        for _msg in render_runtime(_rt, _repo, dry=True):
            print(_msg)
