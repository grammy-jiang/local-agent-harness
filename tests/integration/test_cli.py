from pathlib import Path

from typer.testing import CliRunner

from local_agent_harness.cli.app import app


runner = CliRunner()


def test_version() -> None:
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0
    assert "local-agent-harness" in r.stdout


def test_setup_list(tmp_path: Path) -> None:
    r = runner.invoke(app, ["setup", "--list", "--target", str(tmp_path / "x")])
    assert r.exit_code == 0
    assert "source:" in r.stdout
    assert str(tmp_path / "x") in r.stdout


def test_setup_to_target(tmp_path: Path) -> None:
    target = tmp_path / "skill"
    r = runner.invoke(app, ["setup", "--target", str(target)])
    assert r.exit_code == 0, r.stdout
    assert (target / "SKILL.md").exists()
    assert (target / "assets").is_dir()
    assert (target / "references").is_dir()


def test_assess_empty(empty_repo: Path) -> None:
    r = runner.invoke(app, ["assess", "--repo", str(empty_repo)])
    assert r.exit_code == 0
    assert "Stage:      S0" in r.stdout


def test_init_then_check(empty_repo: Path) -> None:
    r = runner.invoke(app, ["init", "--repo", str(empty_repo), "--runtime", "claude-code"])
    assert r.exit_code == 0
    r = runner.invoke(app, ["check", "--repo", str(empty_repo)])
    assert r.exit_code == 0
