"""Typer entry point wiring all subcommands."""

from __future__ import annotations

import typer

from . import (
    cmd_assess,
    cmd_check,
    cmd_init,
    cmd_refresh,
    cmd_report,
    cmd_setup,
    cmd_validate,
    cmd_version,
)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Maturity-aware harness manager for local AI coding agents.",
)

app.command("setup", help="Install the bundled skill into agent skill directories.")(cmd_setup.run)
app.command("assess", help="Detect maturity stage and AI-readiness score.")(cmd_assess.run)
app.command("check", help="Audit harness manifests for drift (read-only).")(cmd_check.run)
app.command("init", help="Render missing manifests at the appropriate stage.")(cmd_init.run)
app.command("refresh", help="Back up + rewrite stale/relaxed manifests (with --apply).")(
    cmd_refresh.run
)
app.command("report", help="Write a machine-readable AI-readiness report.")(cmd_report.run)
app.command("validate", help="Run manifest regression and redaction smoke checks.")(
    cmd_validate.run
)
app.command("version", help="Print version.")(cmd_version.run)


if __name__ == "__main__":
    app()
