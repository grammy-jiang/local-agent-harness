from __future__ import annotations

import sys
from pathlib import Path

import pytest

from local_agent_harness.core import diff_manifests, scaffold_manifests


def test_init_dry_run_does_not_write(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=True)
    assert rc == 0
    out = capsys.readouterr().out
    # AGENTS.md now handled by agents_builder (would create)
    assert "AGENTS.md" in out
    assert not (empty_repo / "GROUNDING.md").exists()


def test_init_skips_existing_grounding(
    empty_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (empty_repo / "GROUNDING.md").write_text("preserved\n")
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    assert (empty_repo / "GROUNDING.md").read_text() == "preserved\n"
    out = capsys.readouterr().out
    assert "skip (exists)" in out


def test_init_creates_agents_md(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    agents = empty_repo / "AGENTS.md"
    assert agents.exists()
    text = agents.read_text()
    assert "AGENTS.md" in text


def test_init_agents_md_idempotent(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    capsys.readouterr()
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    out = capsys.readouterr().out
    # Second run: auto-sections are up to date
    assert "AGENTS.md" in out


def test_init_creates_skills_dir_at_S1(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S1", [], dry=False)
    assert (empty_repo / ".skills" / "_template.SKILL.md").exists()


def test_init_S1_dry_does_not_create_skills(
    empty_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S1", [], dry=True)
    out = capsys.readouterr().out
    assert "would create" in out
    assert not (empty_repo / ".skills").exists()


def test_init_writes_runtime_overlays(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", ["claude-code", "cursor"], dry=False)
    assert (empty_repo / "CLAUDE.md").exists()
    assert (empty_repo / ".cursor" / "rules").exists()


def test_gitignore_created_with_harness_block(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    gi = (empty_repo / ".gitignore").read_text()
    assert ".agent/logs/" in gi
    assert ".env" in gi


def test_gitignore_idempotent(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    capsys.readouterr()
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    out = capsys.readouterr().out
    # Second run: already managed
    assert "gitignore" in out


def test_gitignore_dry_run(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from local_agent_harness.core import gitignore

    msg = gitignore.render_gitignore(empty_repo, dry=True)
    assert "would create" in msg
    assert not (empty_repo / ".gitignore").exists()


def test_precommit_created(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    assert (empty_repo / ".pre-commit-config.yaml").exists()
    text = (empty_repo / ".pre-commit-config.yaml").read_text()
    assert "gitleaks" in text


def test_precommit_skipped_if_exists(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (empty_repo / ".pre-commit-config.yaml").write_text("# custom\n")
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    out = capsys.readouterr().out
    assert "pre-commit: skip" in out
    assert (empty_repo / ".pre-commit-config.yaml").read_text() == "# custom\n"


def test_refresh_no_drift(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    capsys.readouterr()
    rc = scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=False, dry=False)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no drift" in out


def test_refresh_blocked_on_relaxed(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    g = empty_repo / "GROUNDING.md"
    g.write_text(g.read_text() + "\nallow secrets here\n")
    capsys.readouterr()
    rc = scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=False, dry=False)
    out = capsys.readouterr().out
    assert rc == 2
    assert "BLOCKED" in out


def test_refresh_plan_only_message(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (empty_repo / "GROUNDING.md").write_text("just\n")
    rc = scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=False, dry=False)
    out = capsys.readouterr().out
    assert rc == 0
    assert "plan only" in out
    assert "would refresh" in out


def test_refresh_apply_writes_backup_and_template(empty_repo: Path) -> None:
    g = empty_repo / "GROUNDING.md"
    g.write_text("stale stub\n")
    rc = scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=True, dry=False)
    assert rc == 0
    bak = empty_repo / "GROUNDING.md.md.bak"
    assert bak.exists() or (empty_repo / "GROUNDING.md.bak").exists()
    new_text = g.read_text()
    assert "Hard Constraints" in new_text


def test_refresh_apply_overwrites_existing_backup(empty_repo: Path) -> None:
    g = empty_repo / "GROUNDING.md"
    g.write_text("stub one\n")
    scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=True, dry=False)
    g.write_text("stub two\n")
    rc = scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=True, dry=False)
    assert rc == 0


def test_refresh_renders_missing_when_apply(empty_repo: Path) -> None:
    (empty_repo / "GROUNDING.md").write_text("stale\n")
    rc = scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=True, dry=False)
    assert rc == 0
    assert (empty_repo / "AGENTS.md").exists()


def test_refresh_dry_shows_plan_without_writing(
    empty_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (empty_repo / "GROUNDING.md").write_text("stale\n")
    rc = scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=False, dry=True)
    out = capsys.readouterr().out
    assert rc == 0
    assert "would refresh" in out
    assert (empty_repo / "GROUNDING.md").read_text() == "stale\n"


def test_check_returns_one_on_drift(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = scaffold_manifests.cmd_check(empty_repo, "S0")
    assert rc == 1


def test_check_returns_zero_on_clean(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    capsys.readouterr()
    rc = scaffold_manifests.cmd_check(empty_repo, "S0")
    assert rc == 0


def test_main_init(empty_repo: Path) -> None:
    rc = _run_main(
        scaffold_manifests,
        ["--repo", str(empty_repo), "--mode", "init", "--runtime", "claude-code"],
    )
    assert rc == 0
    assert (empty_repo / "CLAUDE.md").exists()


def test_main_check_drift(empty_repo: Path) -> None:
    rc = _run_main(scaffold_manifests, ["--repo", str(empty_repo), "--mode", "check"])
    assert rc == 1


def test_main_refresh_no_apply(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    rc = _run_main(scaffold_manifests, ["--repo", str(empty_repo), "--mode", "refresh"])
    assert rc == 0


def test_main_missing_repo(tmp_path: Path) -> None:
    rc = _run_main(scaffold_manifests, ["--repo", str(tmp_path / "nope"), "--mode", "init"])
    assert rc == 2


def test_main_explicit_stage_passthrough(empty_repo: Path) -> None:
    rc = _run_main(
        scaffold_manifests, ["--repo", str(empty_repo), "--stage", "S0", "--mode", "init"]
    )
    assert rc == 0


def _run_main(module, argv: list[str]) -> int:
    saved = sys.argv
    sys.argv = [module.__name__, *argv]
    try:
        return module.main()
    finally:
        sys.argv = saved


def test_refresh_stale_missing_dst() -> None:
    msg = scaffold_manifests._refresh_stale(
        Path("/nonexistent/src"), Path("/nonexistent/dst"), apply=True, dry=False
    )
    assert "missing" in msg


def test_refresh_skips_when_template_none(
    empty_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`stale` entry without a 'template' key is filtered out."""

    fake_drift = {
        "stale": [{"path": "GROUNDING.md"}],  # no 'template' key → tmpl is None
        "missing": [],
        "relaxed": [],
    }
    monkeypatch.setattr(diff_manifests, "diff", lambda repo, stage=None: fake_drift)
    rc = scaffold_manifests.cmd_refresh(empty_repo, "S0", [], apply=True, dry=False)
    assert rc == 0
