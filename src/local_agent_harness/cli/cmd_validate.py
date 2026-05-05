from __future__ import annotations

from pathlib import Path

import typer

from local_agent_harness.core import manifest_regression, redaction_smoke


def run(
    repo: Path = typer.Option(Path("."), "--repo", help="Repository path."),
) -> None:
    repo = repo.resolve()
    if not repo.exists():
        typer.echo(f"error: {repo} does not exist", err=True)
        raise typer.Exit(code=2)

    typer.echo("== manifest regression ==")
    results = manifest_regression.check(repo)
    failed = 0
    for name, ok, msg in results:
        marker = "PASS" if ok else "FAIL"
        typer.echo(f"  [{marker}] {name}: {msg}")
        if not ok:
            failed += 1

    typer.echo("== redaction smoke ==")
    findings = redaction_smoke.scan(repo)
    for path, kind in findings:
        typer.echo(f"  HIT {kind}: {path}")
    logs_ok = redaction_smoke.check_logs_ignored(repo)
    typer.echo(f"  .agent/.env in .gitignore: {'yes' if logs_ok else 'no'}")

    if failed or findings or not logs_ok:
        raise typer.Exit(code=1)
    typer.echo("validate: OK")
