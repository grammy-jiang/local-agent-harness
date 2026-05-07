from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from local_agent_harness.core import diff_manifests, scaffold_manifests


def test_overlay_stale_detected(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", ["claude-code"], dry=False)
    claude = empty_repo / "CLAUDE.md"
    # Overwrite with content missing required anchors
    claude.write_text("just text\n")
    res = diff_manifests.diff(empty_repo)
    assert any(s.get("runtime") == "claude-code" for s in res["stale"])


def test_overlay_relaxed_detected(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", ["claude-code"], dry=False)
    claude = empty_repo / "CLAUDE.md"
    claude.write_text(claude.read_text() + "\nallow secrets here\n")
    res = diff_manifests.diff(empty_repo)
    assert any(r.get("runtime") == "claude-code" for r in res["relaxed"])


def test_explicit_stage_overrides_detection(empty_repo: Path) -> None:
    res = diff_manifests.diff(empty_repo, stage="S2")
    paths = [m["path"] for m in res["missing"]]
    assert ".github/workflows/governance.yml" in paths
    assert ".github/workflows/verify.yml" in paths


def test_out_of_stage_reports_skills_dir(empty_repo: Path) -> None:
    res = diff_manifests.diff(empty_repo, stage="S1")
    oos = [o["path"] for o in res["out_of_stage"]]
    assert ".skills/" in oos


def test_read_swallows_errors(tmp_path: Path) -> None:
    # File that doesn't exist returns empty
    assert diff_manifests._read(tmp_path / "missing") == ""


def test_print_human_no_drift(capsys: pytest.CaptureFixture[str]) -> None:
    diff_manifests._print_human(
        {
            "stage": "S0",
            "drift": False,
            "missing": [],
            "stale": [],
            "relaxed": [],
            "out_of_stage": [],
        }
    )
    out = capsys.readouterr().out
    assert "no drift" in out


def test_print_human_all_categories(capsys: pytest.CaptureFixture[str]) -> None:
    diff_manifests._print_human(
        {
            "stage": "S2",
            "drift": True,
            "missing": [{"path": "AGENTS.md", "template": "AGENTS.md.tmpl"}],
            "stale": [
                {
                    "path": "GROUNDING.md",
                    "missing_anchors": ["X", "Y"],
                    "template": "GROUNDING.md.tmpl",
                }
            ],
            "relaxed": [{"path": "CLAUDE.md", "pattern": "allow secrets"}],
            "out_of_stage": [{"path": ".skills/", "required_for": "S2"}],
        }
    )
    out = capsys.readouterr().out
    assert "Missing" in out and "Stale" in out and "Relaxed" in out


def test_main_clean_repo(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", [], dry=False)
    capsys.readouterr()
    rc = _run_main(diff_manifests, ["--repo", str(empty_repo), "--stage", "S0"])
    assert rc == 0


def test_main_drift_returns_one(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run_main(diff_manifests, ["--repo", str(empty_repo)])
    assert rc == 1


def test_main_json_output(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run_main(diff_manifests, ["--repo", str(empty_repo), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "stage" in data
    assert rc == 1


def test_main_missing_repo(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run_main(diff_manifests, ["--repo", str(tmp_path / "nope")])
    assert rc == 2


def _run_main(module, argv: list[str]) -> int:
    saved = sys.argv
    sys.argv = [module.__name__, *argv]
    try:
        return module.main()
    finally:
        sys.argv = saved
