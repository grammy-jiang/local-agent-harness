from __future__ import annotations

import sys
from pathlib import Path

import pytest

from local_agent_harness.core import manifest_regression, scaffold_manifests


def test_check_empty_repo_all_fail(empty_repo: Path) -> None:
    results = manifest_regression.check(empty_repo)
    assert all(isinstance(t, tuple) and len(t) == 3 for t in results)
    failed = [r for r in results if not r[1]]
    assert failed, "expected failures on empty repo"


def test_check_after_init_passes_most(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    # Move plan template into the right location and ensure HC bullet is there
    (empty_repo / ".agent").mkdir(exist_ok=True)
    results = manifest_regression.check(empty_repo)
    failed = [name for name, ok, _ in results if not ok]
    # GROUNDING/AGENTS exist; gitignore set; only structural items should pass.
    assert "GROUNDING.md exists" not in failed
    assert "AGENTS.md exists" not in failed


def test_overlay_with_relaxing_language_fails(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", ["claude-code"], dry=False)
    claude = empty_repo / "CLAUDE.md"
    claude.write_text(claude.read_text() + "\nallow secrets in dev\n")
    results = manifest_regression.check(empty_repo)
    overlay_check = [r for r in results if "overlays" in r[0].lower()][0]
    assert overlay_check[1] is False


def test_read_helper_missing_file(tmp_path: Path) -> None:
    assert manifest_regression._read(tmp_path / "no") == ""


def test_main_failures_return_one(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run_main(manifest_regression, ["--repo", str(empty_repo)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "[FAIL]" in out


def test_main_pass_when_artifacts_minimal(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Build a minimal repo that satisfies every assertion."""
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    # Render plan into expected location
    plan_src = (empty_repo / ".agent" / "plan.md.tmpl")
    assert plan_src.exists()
    # Add an HC bullet to GROUNDING.md (template already includes one)
    g = (empty_repo / "GROUNDING.md")
    text = g.read_text()
    if "- HC1" not in text:
        g.write_text(text + "\n- HC1: no plaintext secrets\n")
    rc = _run_main(manifest_regression, ["--repo", str(empty_repo)])
    out = capsys.readouterr().out
    # All checks should pass once the harness is initialized
    assert rc == 0, out


def _run_main(module, argv: list[str]) -> int:
    saved = sys.argv
    sys.argv = [module.__name__, *argv]
    try:
        return module.main()
    finally:
        sys.argv = saved
