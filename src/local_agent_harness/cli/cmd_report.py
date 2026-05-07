from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from local_agent_harness.core import assess_repo, readiness_report


def run(
    repo: Path = typer.Option(Path("."), "--repo", help="Repository path."),
    out: Optional[Path] = typer.Option(
        None, "--out", help="Write report to this path (default stdout)."
    ),
    check_no_regression: Optional[Path] = typer.Option(
        None,
        "--check-no-regression",
        help="Compare a fresh assessment against an existing readiness file; fail on per-axis regressions.",
    ),
) -> None:
    repo = repo.resolve()
    if not repo.exists():
        typer.echo(f"error: {repo} does not exist", err=True)
        raise typer.Exit(code=2)
    result = assess_repo.detect(repo)

    if check_no_regression:
        prev_text = check_no_regression.read_text(encoding="utf-8")
        prev = readiness_report.parse_machine_block(prev_text)
        if prev is None:
            typer.echo("error: previous readiness file has no machine block", err=True)
            raise typer.Exit(code=2)
        regressed = []
        for axis, score in result["axes"].items():
            old = int(prev.get(axis, 0))
            if score < old:
                regressed.append(f"{axis}: {old} -> {score}")
        if regressed:
            for line in regressed:
                typer.echo(f"REGRESSION {line}", err=True)
            raise typer.Exit(code=1)
        typer.echo("OK no regression")
        return

    text = readiness_report.render_report(result, repo)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        typer.echo(f"wrote {out}")
    else:
        typer.echo(text)
