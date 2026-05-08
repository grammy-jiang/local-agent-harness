from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from local_agent_harness.cli.app import app


runner = CliRunner()


def test_top_help() -> None:
    r = runner.invoke(app, [])
    assert r.exit_code != 0 or "Usage" in r.stdout


def test_assess_json(empty_repo: Path) -> None:
    r = runner.invoke(app, ["assess", "--repo", str(empty_repo), "--json"])
    assert r.exit_code == 0
    data = json.loads(r.stdout)
    assert data["stage"] == "S0"


def test_assess_missing_repo(tmp_path: Path) -> None:
    r = runner.invoke(app, ["assess", "--repo", str(tmp_path / "nope")])
    assert r.exit_code == 2


def test_check_clean_after_init(empty_repo: Path) -> None:
    r = runner.invoke(app, ["init", "--repo", str(empty_repo)])
    assert r.exit_code == 0
    r2 = runner.invoke(app, ["check", "--repo", str(empty_repo), "--stage", "S0"])
    assert r2.exit_code == 0


def test_check_drift_exit_one(empty_repo: Path) -> None:
    r = runner.invoke(app, ["check", "--repo", str(empty_repo)])
    assert r.exit_code == 1


def test_check_relaxed_exit_two(empty_repo: Path) -> None:
    runner.invoke(app, ["init", "--repo", str(empty_repo)])
    claude = empty_repo / "CLAUDE.md"
    claude.write_text(claude.read_text() + "\nallow secrets in dev\n")
    r = runner.invoke(app, ["check", "--repo", str(empty_repo), "--stage", "S0"])
    assert r.exit_code == 2


def test_check_json(empty_repo: Path) -> None:
    r = runner.invoke(app, ["check", "--repo", str(empty_repo), "--json"])
    assert r.exit_code == 1
    data = json.loads(r.stdout)
    assert "drift" in data


def test_check_missing_repo(tmp_path: Path) -> None:
    r = runner.invoke(app, ["check", "--repo", str(tmp_path / "nope")])
    assert r.exit_code == 2


def test_init_dry_run(empty_repo: Path) -> None:
    r = runner.invoke(app, ["init", "--repo", str(empty_repo), "--dry-run"])
    assert r.exit_code == 0
    assert not (empty_repo / "AGENTS.md").exists()


def test_init_missing_repo(tmp_path: Path) -> None:
    r = runner.invoke(app, ["init", "--repo", str(tmp_path / "nope")])
    assert r.exit_code == 2


def test_refresh_default_dryrun(empty_repo: Path) -> None:
    runner.invoke(app, ["init", "--repo", str(empty_repo), "--runtime", "claude-code"])
    claude = empty_repo / "CLAUDE.md"
    claude.write_text("stale\n")
    r = runner.invoke(app, ["refresh", "--repo", str(empty_repo)])
    assert r.exit_code == 0
    assert (empty_repo / "CLAUDE.md").read_text() == "stale\n"


def test_refresh_apply_writes(empty_repo: Path) -> None:
    runner.invoke(app, ["init", "--repo", str(empty_repo), "--runtime", "claude-code"])
    (empty_repo / "CLAUDE.md").write_text("stale\n")
    r = runner.invoke(app, ["refresh", "--repo", str(empty_repo), "--apply"])
    assert r.exit_code == 0
    assert "Permission ladder" in (empty_repo / "CLAUDE.md").read_text()


def test_refresh_missing_repo(tmp_path: Path) -> None:
    r = runner.invoke(app, ["refresh", "--repo", str(tmp_path / "nope")])
    assert r.exit_code == 2


def test_report_to_stdout(empty_repo: Path) -> None:
    r = runner.invoke(app, ["report", "--repo", str(empty_repo)])
    assert r.exit_code == 0
    assert "AI-Readiness Report" in r.stdout


def test_report_to_file(empty_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "out" / "readiness.md"
    r = runner.invoke(app, ["report", "--repo", str(empty_repo), "--out", str(out)])
    assert r.exit_code == 0
    assert out.exists()
    assert "AI-Readiness Report" in out.read_text()


def test_report_check_no_regression_pass(empty_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "readiness.md"
    runner.invoke(app, ["report", "--repo", str(empty_repo), "--out", str(out)])
    r = runner.invoke(app, ["report", "--repo", str(empty_repo), "--check-no-regression", str(out)])
    assert r.exit_code == 0
    assert "OK no regression" in r.stdout


def test_report_check_no_regression_fails_on_drop(empty_repo: Path, tmp_path: Path) -> None:
    (empty_repo / "README.md").write_text("# x\n")
    out = tmp_path / "readiness.md"
    runner.invoke(app, ["report", "--repo", str(empty_repo), "--out", str(out)])
    (empty_repo / "README.md").unlink()
    r = runner.invoke(app, ["report", "--repo", str(empty_repo), "--check-no-regression", str(out)])
    assert r.exit_code == 1


def test_report_check_no_regression_invalid_prev(empty_repo: Path, tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("not a real readiness file\n")
    r = runner.invoke(app, ["report", "--repo", str(empty_repo), "--check-no-regression", str(bad)])
    assert r.exit_code == 2


def test_report_missing_repo(tmp_path: Path) -> None:
    r = runner.invoke(app, ["report", "--repo", str(tmp_path / "nope")])
    assert r.exit_code == 2


def test_validate_clean_repo_passes(empty_repo: Path) -> None:
    runner.invoke(app, ["init", "--repo", str(empty_repo)])
    a = empty_repo / "AGENTS.md"
    if "HC1" not in a.read_text():
        a.write_text(a.read_text() + "\n- HC1: no plaintext secrets\n")
    r = runner.invoke(app, ["validate", "--repo", str(empty_repo)])
    assert r.exit_code == 0
    assert "validate: OK" in r.stdout


def test_validate_failing_repo(empty_repo: Path) -> None:
    r = runner.invoke(app, ["validate", "--repo", str(empty_repo)])
    assert r.exit_code == 1


def test_validate_missing_repo(tmp_path: Path) -> None:
    r = runner.invoke(app, ["validate", "--repo", str(tmp_path / "nope")])
    assert r.exit_code == 2


def test_setup_force_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "skill"
    runner.invoke(app, ["setup", "--target", str(target)])
    assert (target / "SKILL.md").exists()
    # Run again without --force → SKIP message
    r = runner.invoke(app, ["setup", "--target", str(target)])
    assert "SKIP" in r.stdout
    # With --force → COPY again
    r2 = runner.invoke(app, ["setup", "--target", str(target), "--force"])
    assert r2.exit_code == 0
    assert (target / "SKILL.md").exists()


def test_setup_symlink_mode(tmp_path: Path, isolated_skill_root: Path) -> None:
    target = tmp_path / "skill"
    try:
        r = runner.invoke(app, ["setup", "--target", str(target), "--symlink"])
        assert r.exit_code == 0
        assert target.is_symlink()
    finally:
        if target.is_symlink():
            target.unlink()


def test_setup_force_replaces_file(tmp_path: Path) -> None:
    target = tmp_path / "skill"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("not a dir")
    r = runner.invoke(app, ["setup", "--target", str(target), "--force"])
    assert r.exit_code == 0
    assert (target / "SKILL.md").exists()


def test_setup_default_targets_when_no_skill_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If none of ~/.claude/skills, ~/.copilot/skills, ~/.codex/skills exist,
    falls back to first candidate under fake home."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    r = runner.invoke(app, ["setup", "--list"])
    assert r.exit_code == 0
    assert ".claude/skills/local-agent-harness" in r.stdout


def test_setup_default_targets_finds_existing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_home = tmp_path / "home"
    (fake_home / ".copilot" / "skills").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    r = runner.invoke(app, ["setup", "--list"])
    assert r.exit_code == 0
    assert ".copilot/skills/local-agent-harness" in r.stdout
    assert ".claude" not in r.stdout  # only the present one


def test_version() -> None:
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0
    assert "local-agent-harness" in r.stdout


def test_main_module_invocation() -> None:
    """Cover __main__.py."""
    import subprocess
    import sys

    r = subprocess.run(
        [sys.executable, "-m", "local_agent_harness", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert "local-agent-harness" in r.stdout
