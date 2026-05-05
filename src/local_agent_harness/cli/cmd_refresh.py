from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer

from local_agent_harness.core import assess_repo, scaffold_manifests


def run(
    repo: Path = typer.Option(Path("."), "--repo", help="Repository path."),
    stage: Optional[str] = typer.Option(None, "--stage", help="Override stage (S0|S1|S2|S3)."),
    runtime: List[str] = typer.Option([], "--runtime", help="Runtime overlay(s) to render."),
    apply: bool = typer.Option(False, "--apply", help="Actually write changes (default is dry-run)."),
) -> None:
    repo = repo.resolve()
    if not repo.exists():
        typer.echo(f"error: {repo} does not exist", err=True)
        raise typer.Exit(code=2)
    if stage is None:
        stage = assess_repo.detect(repo)["stage"]
    rc = scaffold_manifests.cmd_refresh(repo, stage, list(runtime), apply, dry=not apply)
    raise typer.Exit(code=rc)
