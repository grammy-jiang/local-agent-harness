from __future__ import annotations

import sys
from pathlib import Path

import pytest

from local_agent_harness.core import redaction_smoke


def test_scan_clean_repo_returns_no_findings(empty_repo: Path) -> None:
    (empty_repo / "README.md").write_text("hello world\n")
    assert redaction_smoke.scan(empty_repo) == []


def test_scan_detects_aws_key(empty_repo: Path) -> None:
    (empty_repo / "leak.md").write_text("AKIA" + "A" * 16 + "\n")
    findings = redaction_smoke.scan(empty_repo)
    assert findings
    assert findings[0][0].name == "leak.md"


def test_scan_detects_github_pat(empty_repo: Path) -> None:
    (empty_repo / "x.yml").write_text("ghp_" + "a" * 36 + "\n")
    assert redaction_smoke.scan(empty_repo)


def test_scan_skips_large_files(empty_repo: Path) -> None:
    big = empty_repo / "big.md"
    big.write_text("ghp_" + "a" * 36 + "\n" + ("x" * 600_000))
    # Even though it contains a token, file > 512KB is skipped
    assert redaction_smoke.scan(empty_repo) == []


def test_scan_skips_skip_dirs(empty_repo: Path) -> None:
    (empty_repo / ".venv").mkdir()
    (empty_repo / ".venv" / "leak.md").write_text("ghp_" + "a" * 36 + "\n")
    assert redaction_smoke.scan(empty_repo) == []


def test_scan_skips_unreadable_files(empty_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = empty_repo / "x.md"
    target.write_text("hello")
    real_read = Path.read_text

    def boom(self: Path, *a, **k):  # type: ignore[no-untyped-def]
        if self == target:
            raise OSError("boom")
        return real_read(self, *a, **k)

    monkeypatch.setattr(Path, "read_text", boom)
    assert redaction_smoke.scan(empty_repo) == []


def test_check_logs_ignored_true(empty_repo: Path) -> None:
    (empty_repo / ".gitignore").write_text(".agent/\n.env\n")
    assert redaction_smoke.check_logs_ignored(empty_repo) is True


def test_check_logs_ignored_partial_false(empty_repo: Path) -> None:
    (empty_repo / ".gitignore").write_text(".agent/\n")
    assert redaction_smoke.check_logs_ignored(empty_repo) is False


def test_check_logs_ignored_no_file(empty_repo: Path) -> None:
    assert redaction_smoke.check_logs_ignored(empty_repo) is False


def test_main_pass_clean(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (empty_repo / ".gitignore").write_text(".agent/\n.env\n")
    rc = _run_main(redaction_smoke, ["--repo", str(empty_repo)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "[PASS]" in out


def test_main_fail_with_finding(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (empty_repo / ".gitignore").write_text(".agent/\n.env\n")
    (empty_repo / "leak.md").write_text("ghp_" + "x" * 36 + "\n")
    rc = _run_main(redaction_smoke, ["--repo", str(empty_repo)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL" in out


def test_main_fail_when_gitignore_missing(
    empty_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = _run_main(redaction_smoke, ["--repo", str(empty_repo)])
    out = capsys.readouterr().out
    assert rc == 1
    assert ".gitignore" in out


def _run_main(module, argv: list[str]) -> int:
    saved = sys.argv
    sys.argv = [module.__name__, *argv]
    try:
        return module.main()
    finally:
        sys.argv = saved
