from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import typer

from local_agent_harness.core import assess_repo, scaffold_manifests

_AVAILABLE_RUNTIMES = ["copilot-cli", "claude-code", "codex-cli", "cursor"]
_RUNTIME_LABELS = {
    "copilot-cli": "GitHub Copilot CLI  (.github/copilot-cli.md)",
    "claude-code":  "Claude Code         (CLAUDE.md)",
    "codex-cli":    "OpenAI Codex CLI    (.codex/config)",
    "cursor":       "Cursor              (.cursor/rules)",
}


def _prompt_runtimes() -> list[str]:
    """Interactive numbered-list prompt for runtime selection.

    Returns an empty list when stdin is not a TTY (e.g. in CI).
    """
    if not sys.stdin.isatty():
        return []
    typer.echo("\nWhich AI agent runtimes should be configured?")
    typer.echo("(Enter numbers separated by commas, 'all', or press Enter to skip)\n")
    for i, key in enumerate(_AVAILABLE_RUNTIMES, 1):
        typer.echo(f"  {i}. {_RUNTIME_LABELS[key]}")
    typer.echo()
    raw = typer.prompt("Selection", default="").strip()
    if not raw:
        return []
    if raw.lower() == "all":
        return list(_AVAILABLE_RUNTIMES)
    selected: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(_AVAILABLE_RUNTIMES):
                selected.append(_AVAILABLE_RUNTIMES[idx])
        elif part in _AVAILABLE_RUNTIMES:
            selected.append(part)
    return selected


def run(
    repo: Path = typer.Option(Path("."), "--repo", help="Repository path."),
    stage: Optional[str] = typer.Option(None, "--stage", help="Override stage (S0|S1|S2|S3)."),
    runtime: List[str] = typer.Option(
        [],
        "--runtime",
        help=(
            "Runtime overlay(s) to render: copilot-cli|claude-code|codex-cli|cursor. "
            "Omit to be prompted interactively (when stdin is a TTY)."
        ),
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be written."),
) -> None:
    repo = repo.resolve()
    if not repo.exists():
        typer.echo(f"error: {repo} does not exist", err=True)
        raise typer.Exit(code=2)
    if stage is None:
        stage = assess_repo.detect(repo)["stage"]
    runtimes = list(runtime) if runtime else _prompt_runtimes()
    rc = scaffold_manifests.cmd_init(repo, stage, runtimes, dry_run)
    raise typer.Exit(code=rc)
