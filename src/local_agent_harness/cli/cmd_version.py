from __future__ import annotations

import typer

from local_agent_harness import __version__


def run() -> None:
    typer.echo(f"local-agent-harness {__version__}")
