from __future__ import annotations

import json
from pathlib import Path

import typer

from local_agent_harness.core import assess_repo


def run(
    repo: Path = typer.Option(Path("."), "--repo", help="Repository path."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    repo = repo.resolve()
    if not repo.exists():
        typer.echo(f"error: {repo} does not exist", err=True)
        raise typer.Exit(code=2)
    result = assess_repo.detect(repo)
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
        return
    typer.echo(f"Repository: {repo}")
    typer.echo(f"Stage:      {result['stage']}")
    typer.echo(f"Total:      {result['total']} / 25")
    for k, v in result["axes"].items():
        typer.echo(f"  {k:16s} {v}/5")
    if result["detected_runtimes"]:
        typer.echo(f"Runtimes:   {', '.join(result['detected_runtimes'])}")
    if result["missing_artifacts"]:
        typer.echo("Missing:")
        for m in result["missing_artifacts"]:
            typer.echo(f"  - {m}")
