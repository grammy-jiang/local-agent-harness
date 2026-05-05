from __future__ import annotations

import sys
from pathlib import Path

import pytest

from local_agent_harness.core import assess_repo, readiness_report


def test_render_report_has_sentinel_and_machine_block(empty_repo: Path) -> None:
    res = assess_repo.detect(empty_repo)
    text = readiness_report.render_report(res, empty_repo)
    assert readiness_report.SENTINEL in text
    assert "stage=S0" in text
    assert "AI-Readiness Report" in text


def test_render_report_lists_missing_artifacts(empty_repo: Path) -> None:
    res = assess_repo.detect(empty_repo)
    text = readiness_report.render_report(res, empty_repo)
    assert "GROUNDING.md" in text


def test_render_report_no_missing(empty_repo: Path) -> None:
    res = assess_repo.detect(empty_repo)
    res = dict(res)
    res["missing_artifacts"] = []
    text = readiness_report.render_report(res, empty_repo)
    assert "(none)" in text


def test_parse_machine_block_round_trip(empty_repo: Path) -> None:
    res = assess_repo.detect(empty_repo)
    text = readiness_report.render_report(res, empty_repo)
    parsed = readiness_report.parse_machine_block(text)
    assert parsed is not None
    assert parsed["stage"] == "S0"
    assert int(parsed["agent_config"]) == res["axes"]["agent_config"]


def test_parse_machine_block_returns_none_without_sentinel() -> None:
    assert readiness_report.parse_machine_block("# nothing here") is None


def test_parse_machine_block_legacy_sentinel() -> None:
    text = "<!-- harness-bootstrap:readiness:v1 -->\n```\nstage=S1\ntotal=7\n```\n"
    parsed = readiness_report.parse_machine_block(text)
    assert parsed == {"stage": "S1", "total": "7"}


def test_parse_machine_block_no_block(empty_repo: Path) -> None:
    text = readiness_report.SENTINEL + "\n# only header\n"
    assert readiness_report.parse_machine_block(text) is None


def test_main_writes_file(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run_main(readiness_report, ["--repo", str(empty_repo)])
    assert rc == 0
    assert (empty_repo / ".agent" / "eval" / "readiness.md").exists()


def test_main_no_regression_clean(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # First run creates baseline
    _run_main(readiness_report, ["--repo", str(empty_repo)])
    capsys.readouterr()
    # Second run with --check-no-regression should pass (no change)
    rc = _run_main(readiness_report, ["--repo", str(empty_repo), "--check-no-regression"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "no regression" in out


def test_main_no_regression_detects_drop(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Build state with documentation=1 (README only)
    (empty_repo / "README.md").write_text("# x\n")
    _run_main(readiness_report, ["--repo", str(empty_repo)])
    capsys.readouterr()
    # Remove README -> documentation drops to 0
    (empty_repo / "README.md").unlink()
    rc = _run_main(readiness_report, ["--repo", str(empty_repo), "--check-no-regression"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "regressed" in err
    assert "documentation" in err


def test_main_no_regression_first_run_no_prev(empty_repo: Path) -> None:
    # No prior file → check-no-regression should still succeed (prev is None)
    rc = _run_main(readiness_report, ["--repo", str(empty_repo), "--check-no-regression"])
    assert rc == 0


def _run_main(module, argv: list[str]) -> int:
    saved = sys.argv
    sys.argv = [module.__name__, *argv]
    try:
        return module.main()
    finally:
        sys.argv = saved


def test_main_no_regression_handles_int_parse_failure(empty_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-int values in machine block should be ignored, not crash."""
    out_dir = empty_repo / ".agent" / "eval"
    out_dir.mkdir(parents=True)
    (out_dir / "readiness.md").write_text(
        readiness_report.SENTINEL + "\n```\nstage=S0\nagent_config=oops\n```\n"
    )
    rc = _run_main(readiness_report, ["--repo", str(empty_repo), "--check-no-regression"])
    assert rc == 0
