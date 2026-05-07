"""Install the bundled `local-agent-harness` skill into agent skill directories.

Default targets are the three known agent skill roots, but only those whose
parent directory already exists on disk:

* ``~/.claude/skills/local-agent-harness/``   (Claude Code)
* ``~/.copilot/skills/local-agent-harness/``  (GitHub Copilot CLI)
* ``~/.codex/skills/local-agent-harness/``    (Codex CLI)

Use ``--target PATH`` (repeatable) to install elsewhere, e.g. into a
project-local ``.github/skills/<name>/`` directory.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

import typer

from local_agent_harness.core._paths import skill_data_root

_SKILL_NAME = "local-agent-harness"


def _default_targets() -> list[Path]:
    """Return skill dirs whose *parent* (e.g. ~/.claude/skills) already exists.

    Falls back to ``~/.claude/skills/<name>`` if none exist, so first-time
    users on a fresh box still get a sensible default.
    """
    home = Path.home()
    candidates = [
        home / ".claude" / "skills",
        home / ".copilot" / "skills",
        home / ".codex" / "skills",
    ]
    existing = [p / _SKILL_NAME for p in candidates if p.is_dir()]
    if existing:
        return existing
    return [candidates[0] / _SKILL_NAME]


def _install(src: Path, dst: Path, *, symlink: bool, force: bool) -> str:
    if dst.exists() or dst.is_symlink():
        if not force:
            return f"SKIP {dst} (exists; use --force to overwrite)"
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if symlink:
        dst.symlink_to(src, target_is_directory=True)
        return f"LINK {dst} -> {src}"
    shutil.copytree(src, dst)
    return f"COPY {dst}"


def run(
    target: List[Path] = typer.Option(
        [],
        "--target",
        "-t",
        help=(
            "Destination directory for the skill (repeatable). "
            "Defaults to the existing agent skill roots: "
            "~/.claude/skills, ~/.copilot/skills, ~/.codex/skills."
        ),
    ),
    symlink: bool = typer.Option(
        False, "--symlink", help="Symlink instead of copying (good for development)."
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite the destination if it already exists."
    ),
    list_only: bool = typer.Option(
        False, "--list", help="Print the resolved targets and exit without writing."
    ),
) -> None:
    src = skill_data_root()
    targets = [t.expanduser().resolve() for t in target] if target else _default_targets()

    if list_only:
        typer.echo(f"source: {src}")
        for t in targets:
            typer.echo(f"target: {t}")
        return

    for t in targets:
        msg = _install(src, t, symlink=symlink, force=force)
        typer.echo(msg)
