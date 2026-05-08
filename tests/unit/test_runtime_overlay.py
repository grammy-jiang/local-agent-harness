"""Tests for core.runtime_overlay — agent-specific config file generation."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from local_agent_harness.core import runtime_overlay


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_info() -> dict:
    return {
        "stack": [],
        "install_cmds": [],
        "build_cmds": [],
        "test_cmds": [],
        "lint_cmds": [],
        "format_cmds": [],
        "style_hints": [],
        "branch_pattern": "agent/<task-slug>",
        "commit_style": "Conventional Commits",
    }


# ---------------------------------------------------------------------------
# _write_if_missing
# ---------------------------------------------------------------------------


def test_write_if_missing_creates_file(tmp_path: Path) -> None:
    dest = tmp_path / "sub" / "file.txt"
    msg = runtime_overlay._write_if_missing(dest, "hello", dry=False)
    assert dest.read_text() == "hello"
    assert "rendered:" in msg


def test_write_if_missing_skips_existing(tmp_path: Path) -> None:
    dest = tmp_path / "file.txt"
    dest.write_text("original")
    msg = runtime_overlay._write_if_missing(dest, "new", dry=False)
    assert dest.read_text() == "original"
    assert "skip" in msg


def test_write_if_missing_dry_run(tmp_path: Path) -> None:
    dest = tmp_path / "file.txt"
    msg = runtime_overlay._write_if_missing(dest, "content", dry=True)
    assert not dest.exists()
    assert "would render:" in msg


# ---------------------------------------------------------------------------
# _build_claude_settings
# ---------------------------------------------------------------------------


def test_build_claude_settings_empty_info() -> None:
    info = _empty_info()
    content = runtime_overlay._build_claude_settings(info)
    data = json.loads(content)
    assert "$schema" in data
    assert "permissions" in data
    assert isinstance(data["permissions"]["allow"], list)
    assert isinstance(data["permissions"]["deny"], list)


def test_build_claude_settings_with_commands() -> None:
    info = _empty_info()
    info["test_cmds"] = ["pytest tests/"]
    info["lint_cmds"] = ["ruff check src"]
    content = runtime_overlay._build_claude_settings(info)
    data = json.loads(content)
    allow = data["permissions"]["allow"]
    assert "Bash(pytest *)" in allow
    assert "Bash(ruff *)" in allow


def test_build_claude_settings_no_duplicates() -> None:
    info = _empty_info()
    info["lint_cmds"] = ["ruff check src"]
    info["format_cmds"] = ["ruff format src"]  # same base command
    content = runtime_overlay._build_claude_settings(info)
    data = json.loads(content)
    allow = data["permissions"]["allow"]
    assert allow.count("Bash(ruff *)") == 1


def test_build_claude_settings_always_includes_git() -> None:
    info = _empty_info()
    content = runtime_overlay._build_claude_settings(info)
    data = json.loads(content)
    allow = data["permissions"]["allow"]
    assert "Bash(git status *)" in allow
    assert "Bash(git commit *)" in allow


def test_build_claude_settings_denies_sensitive() -> None:
    info = _empty_info()
    content = runtime_overlay._build_claude_settings(info)
    data = json.loads(content)
    deny = data["permissions"]["deny"]
    assert "Read(./.env)" in deny
    assert "Bash(curl *)" in deny


# ---------------------------------------------------------------------------
# render_claude_code
# ---------------------------------------------------------------------------


def test_render_claude_code_creates_files(tmp_path: Path) -> None:
    with patch.object(
        runtime_overlay._agents_builder, "detect_project_info", return_value=_empty_info()
    ):
        msgs = runtime_overlay.render_claude_code(tmp_path, dry=False)
    assert len(msgs) == 2
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".claude" / "settings.json").exists()
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "@AGENTS.md" in content


def test_render_claude_code_dry_run(tmp_path: Path) -> None:
    with patch.object(
        runtime_overlay._agents_builder, "detect_project_info", return_value=_empty_info()
    ):
        msgs = runtime_overlay.render_claude_code(tmp_path, dry=True)
    assert not (tmp_path / "CLAUDE.md").exists()
    assert all("would render:" in m for m in msgs)


def test_render_claude_code_skips_existing(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("existing")
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{}")
    with patch.object(
        runtime_overlay._agents_builder, "detect_project_info", return_value=_empty_info()
    ):
        msgs = runtime_overlay.render_claude_code(tmp_path, dry=False)
    assert all("skip" in m for m in msgs)
    assert (tmp_path / "CLAUDE.md").read_text() == "existing"


def test_render_claude_code_settings_valid_json(tmp_path: Path) -> None:
    with patch.object(
        runtime_overlay._agents_builder, "detect_project_info", return_value=_empty_info()
    ):
        runtime_overlay.render_claude_code(tmp_path, dry=False)
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert "permissions" in data


# ---------------------------------------------------------------------------
# render_copilot
# ---------------------------------------------------------------------------


def test_render_copilot_creates_files(tmp_path: Path) -> None:
    msgs = runtime_overlay.render_copilot(tmp_path, dry=False)
    assert len(msgs) == 2
    instructions = tmp_path / ".github" / "copilot-instructions.md"
    general = tmp_path / ".github" / "instructions" / "general.instructions.md"
    assert instructions.exists()
    assert general.exists()
    assert "AGENTS.md" in instructions.read_text()
    assert "applyTo" in general.read_text()


def test_render_copilot_dry_run(tmp_path: Path) -> None:
    msgs = runtime_overlay.render_copilot(tmp_path, dry=True)
    assert not (tmp_path / ".github").exists()
    assert all("would render:" in m for m in msgs)


def test_render_copilot_skips_existing(tmp_path: Path) -> None:
    gh = tmp_path / ".github"
    gh.mkdir()
    instr = gh / "copilot-instructions.md"
    instr.write_text("custom")
    msgs = runtime_overlay.render_copilot(tmp_path, dry=False)
    # First file skipped, second created
    assert "skip" in msgs[0]
    assert instr.read_text() == "custom"


def test_render_copilot_references_agents_md(tmp_path: Path) -> None:
    runtime_overlay.render_copilot(tmp_path, dry=False)
    content = (tmp_path / ".github" / "copilot-instructions.md").read_text()
    assert "AGENTS.md" in content


# ---------------------------------------------------------------------------
# render_codex
# ---------------------------------------------------------------------------


def test_render_codex_creates_file(tmp_path: Path) -> None:
    msgs = runtime_overlay.render_codex(tmp_path, dry=False)
    assert len(msgs) == 1
    path = tmp_path / ".codex" / "INSTRUCTIONS.md"
    assert path.exists()
    assert "AGENTS.md" in path.read_text()


def test_render_codex_dry_run(tmp_path: Path) -> None:
    msgs = runtime_overlay.render_codex(tmp_path, dry=True)
    assert not (tmp_path / ".codex").exists()
    assert "would render:" in msgs[0]


def test_render_codex_skips_existing(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir()
    f = tmp_path / ".codex" / "INSTRUCTIONS.md"
    f.write_text("custom")
    msgs = runtime_overlay.render_codex(tmp_path, dry=False)
    assert "skip" in msgs[0]
    assert f.read_text() == "custom"


# ---------------------------------------------------------------------------
# render_runtime dispatcher
# ---------------------------------------------------------------------------


def test_render_runtime_claude_code(tmp_path: Path) -> None:
    with patch.object(
        runtime_overlay._agents_builder, "detect_project_info", return_value=_empty_info()
    ):
        msgs = runtime_overlay.render_runtime("claude-code", tmp_path, dry=True)
    assert len(msgs) == 2


def test_render_runtime_copilot_cli(tmp_path: Path) -> None:
    msgs = runtime_overlay.render_runtime("copilot-cli", tmp_path, dry=True)
    assert len(msgs) == 2


def test_render_runtime_codex_cli(tmp_path: Path) -> None:
    msgs = runtime_overlay.render_runtime("codex-cli", tmp_path, dry=True)
    assert len(msgs) == 1


def test_render_runtime_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown runtime"):
        runtime_overlay.render_runtime("unknown-agent", Path("/tmp"), dry=True)


# ---------------------------------------------------------------------------
# Integration: scaffold cmd_init calls render_runtime for each selected rt
# ---------------------------------------------------------------------------


def test_scaffold_cmd_init_calls_overlay(tmp_path: Path) -> None:
    """cmd_init with runtimes should produce overlay files."""
    from unittest.mock import patch as p
    import local_agent_harness.core.scaffold_manifests as sm

    called_runtimes: list[str] = []

    def fake_render(rt: str, repo: Path, dry: bool) -> list[str]:
        called_runtimes.append(rt)
        return [f"fake: {rt}"]

    with (
        p.object(sm._agents_builder, "update_agents_md", return_value="ok"),
        p.object(sm._gitignore, "render_gitignore", return_value="ok"),
        p.object(sm._precommit, "render_precommit", return_value="ok"),
        p.object(sm._runtime_overlay, "render_runtime", side_effect=fake_render),
        p("builtins.print"),
    ):
        rc = sm.cmd_init(tmp_path, "S0", ["claude-code", "copilot-cli"], dry=True)

    assert rc == 0
    assert "claude-code" in called_runtimes
    assert "copilot-cli" in called_runtimes
