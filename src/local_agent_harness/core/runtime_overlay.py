#!/usr/bin/env python3
"""Generate agent-specific runtime overlay files for each AI coding assistant.

DRY principle
-------------
``AGENTS.md`` (repository root) is the **single source of truth** for build
commands, test commands, conventions, and scope boundaries.  Every
overlay file either imports ``AGENTS.md`` directly (Claude Code), explicitly
references it (GitHub Copilot), or defers to it completely (Codex).

Supported runtimes
------------------
* ``claude-code``   → ``CLAUDE.md`` (with ``@AGENTS.md`` import) +
                      ``.claude/settings.json`` (project permissions)
* ``copilot-cli``   → ``.github/copilot-instructions.md`` (repo-wide) +
                      ``.github/instructions/general.instructions.md``
* ``codex-cli``     → ``.codex/INSTRUCTIONS.md`` (pointer to AGENTS.md)

None of these functions overwrite a file that already exists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import agents_builder as _agents_builder
from ._paths import assets_dir as _assets_dir

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
- Denied by default: `curl`, `wget`, secrets files, `.env*`
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
- If `accept-edits` mode writes outside the declared scope → abort and
  revert, then report what happened.
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

# GitHub Copilot does not support @import syntax, so we reference AGENTS.md
# explicitly and add Copilot-specific guidance after the pointer.
_COPILOT_INSTRUCTIONS = """\
<!-- .github/copilot-instructions.md                                          -->
<!-- Repository-wide custom instructions for GitHub Copilot                   -->
<!-- Docs: https://docs.github.com/en/copilot/customizing-copilot             -->
<!--                                                                           -->
<!-- DRY principle: AGENTS.md (repo root) is the single source of truth for   -->
<!-- build commands, test commands, conventions, and scope boundaries.         -->
<!-- This file adds Copilot-specific pointers and supplements only.            -->

## Primary instructions: AGENTS.md

The complete agent instructions are in **`AGENTS.md`** at the repository root.
Read it before making any change.  It contains:

- Build and test commands
- Coding conventions and style rules
- Scope boundary (which paths may be written)
- Security and data-classification policies
- PR checklist

## Copilot-specific guidance

- Always run the test suite and linter after every change (commands in
  `AGENTS.md § Testing` and `AGENTS.md § Lint and Format`).
- Never push directly to `main`; open a pull request.
- Follow the commit message convention documented in `AGENTS.md`.
- Keep pull requests small and focused; split unrelated changes into separate
  PRs.
- Include tests for every new function and every bug fix.
- When generating new code, match the style and patterns already in use.
- If a change requires a dependency update, call it out explicitly in the PR
  description.
"""

_COPILOT_GENERAL_INSTRUCTIONS = """\
---
applyTo: "**"
---

<!-- .github/instructions/general.instructions.md                         -->
<!-- Path-specific instruction applied to every file in this repository.   -->

Follow the conventions in `AGENTS.md` (repository root) for all files.

Specific rules:
- Keep functions small and single-purpose.
- Add or update tests whenever you change behaviour.
- Do not commit secrets, credentials, or environment-variable values.
- Prefer explicit error handling over silent failures.
"""


def render_copilot(repo: Path, dry: bool) -> list[str]:
    """Create ``.github/copilot-instructions.md`` and a general path instruction."""
    return [
        _write_if_missing(
            repo / ".github" / "copilot-instructions.md",
            _COPILOT_INSTRUCTIONS,
            dry,
        ),
        _write_if_missing(
            repo / ".github" / "instructions" / "general.instructions.md",
            _COPILOT_GENERAL_INSTRUCTIONS,
            dry,
        ),
    ]


# ---------------------------------------------------------------------------
# OpenAI Codex CLI
# ---------------------------------------------------------------------------

# Codex CLI reads AGENTS.md natively (agents.md standard).
# We create .codex/INSTRUCTIONS.md purely as a "what to edit" guide for
# humans who open the .codex/ folder.
_CODEX_INSTRUCTIONS = """\
# Codex CLI — project context

OpenAI Codex CLI reads **`AGENTS.md`** (repository root) automatically.

**Do not duplicate instructions here.**  Edit `AGENTS.md` instead.

For Codex CLI–specific runtime settings (model, approval mode, sandbox
configuration), see the [Codex documentation](https://developers.openai.com/codex).

## Quick reference

| What to change            | Where to change it       |
|---------------------------|--------------------------|
| Build / test / lint cmds  | `AGENTS.md`              |
| Coding conventions        | `AGENTS.md`              |
| Scope boundary            | `AGENTS.md`              |
| Model / approval mode     | `~/.codex/config.toml`   |
| Project-level MCP servers | (Codex does not support) |
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
