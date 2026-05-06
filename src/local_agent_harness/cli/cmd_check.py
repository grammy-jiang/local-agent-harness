from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from local_agent_harness.core import agents_builder, diff_manifests


def run(
    repo: Path = typer.Option(Path("."), "--repo", help="Repository path."),
    stage: Optional[str] = typer.Option(None, "--stage", help="Override stage (S0|S1|S2|S3)."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON."),
) -> None:
    repo = repo.resolve()
    if not repo.exists():
        typer.echo(f"error: {repo} does not exist", err=True)
        raise typer.Exit(code=2)
    # Always refresh AGENTS.md auto-sections on check
    agents_builder.update_agents_md(repo, dry=False)
    result = diff_manifests.diff(repo, stage=stage)
    if json_output:
        import json
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        diff_manifests._print_human(result)
    if result.get("relaxed"):
        raise typer.Exit(code=2)
    if result.get("drift"):
        raise typer.Exit(code=1)
