from __future__ import annotations

import sys
from unittest.mock import patch

from local_agent_harness.cli.cmd_init import _prompt_runtimes, _AVAILABLE_RUNTIMES


def test_prompt_runtimes_non_tty_returns_empty() -> None:
    with patch.object(sys.stdin, "isatty", return_value=False):
        result = _prompt_runtimes()
    assert result == []


def test_prompt_runtimes_empty_selection(monkeypatch: object) -> None:
    with patch.object(sys.stdin, "isatty", return_value=True):
        with patch("typer.prompt", return_value=""):
            result = _prompt_runtimes()
    assert result == []


def test_prompt_runtimes_all(monkeypatch: object) -> None:
    with patch.object(sys.stdin, "isatty", return_value=True):
        with patch("typer.prompt", return_value="all"):
            result = _prompt_runtimes()
    assert result == list(_AVAILABLE_RUNTIMES)


def test_prompt_runtimes_by_number() -> None:
    with patch.object(sys.stdin, "isatty", return_value=True):
        with patch("typer.prompt", return_value="1,2"):
            result = _prompt_runtimes()
    assert result[0] == _AVAILABLE_RUNTIMES[0]
    assert result[1] == _AVAILABLE_RUNTIMES[1]


def test_prompt_runtimes_by_name() -> None:
    with patch.object(sys.stdin, "isatty", return_value=True):
        with patch("typer.prompt", return_value="claude-code"):
            result = _prompt_runtimes()
    assert "claude-code" in result


def test_prompt_runtimes_invalid_number_ignored() -> None:
    with patch.object(sys.stdin, "isatty", return_value=True):
        with patch("typer.prompt", return_value="99"):
            result = _prompt_runtimes()
    assert result == []
