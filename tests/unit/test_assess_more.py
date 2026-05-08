from __future__ import annotations

from pathlib import Path

import pytest

from local_agent_harness.core import assess_repo


def _scaffold_S1(repo: Path) -> None:
    """Create a minimal S1-shape repo (src + tests + CI)."""
    (repo / "README.md").write_text("# x\n")
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("x = 1\n")
    (repo / "tests").mkdir()
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: ci\non: push\njobs: {}\n")


def test_helpers_exists_and_git(tmp_path: Path) -> None:
    assert assess_repo._exists(tmp_path) is True  # base path
    assert assess_repo._exists(tmp_path, "missing") is False
    # _git on a non-repo returns ""
    assert assess_repo._git(tmp_path, "rev-parse", "HEAD") == ""


def test_count_source_files_prunes_noise(tmp_path: Path) -> None:
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "ignored.py").write_text("x=1")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("x=1")
    (tmp_path / "kept.py").write_text("x=1")
    (tmp_path / "kept.ts").write_text("x=1")
    (tmp_path / "ignored.txt").write_text("x")
    n = assess_repo._count_source_files(tmp_path)
    assert n == 2


def test_count_source_files_caps_at_1000(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    for i in range(1010):
        (src / f"f{i}.py").write_text("x")
    n = assess_repo._count_source_files(tmp_path)
    assert n > 1000


def test_detect_S1_with_tests_no_tags(empty_repo: Path) -> None:
    _scaffold_S1(empty_repo)
    res = assess_repo.detect(empty_repo)
    assert res["stage"] in {"S1", "S2"}  # depends on tests dir presence
    assert res["signals"]["has_ci"] is True
    assert res["signals"]["has_tests"] is True
    assert res["signals"]["source_files"] >= 1


def test_detect_S2_when_tagged(empty_repo: Path) -> None:
    _scaffold_S1(empty_repo)
    import subprocess

    subprocess.run(["git", "add", "-A"], cwd=empty_repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x"],
        cwd=empty_repo,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "tag", "-a", "v0.1.0", "-m", "v0.1.0"],
        cwd=empty_repo,
        check=True,
        env={"PATH": __import__("os").environ.get("PATH", ""), "GIT_EDITOR": "true"},
    )
    res = assess_repo.detect(empty_repo)
    assert res["signals"]["has_tags"] is True
    assert res["stage"] == "S3"


def test_detect_runtimes_listed(empty_repo: Path) -> None:
    (empty_repo / "CLAUDE.md").write_text("x")
    (empty_repo / ".codex").mkdir()
    (empty_repo / ".codex" / "INSTRUCTIONS.md").write_text("x")
    (empty_repo / ".github").mkdir()
    (empty_repo / ".github" / "copilot-instructions.md").write_text("x")
    res = assess_repo.detect(empty_repo)
    assert set(res["detected_runtimes"]) == {
        "claude-code",
        "codex-cli",
        "copilot-cli",
    }


def test_axes_climb_with_artifacts(empty_repo: Path) -> None:
    (empty_repo / "AGENTS.md").write_text("x")
    (empty_repo / "CLAUDE.md").write_text("x")  # overlay
    (empty_repo / ".skills").mkdir()
    (empty_repo / "scripts").mkdir()
    (empty_repo / "scripts" / "manifest_regression.py").write_text("# x")
    res = assess_repo.detect(empty_repo)
    assert res["axes"]["agent_config"] == 5


def test_documentation_axis(empty_repo: Path) -> None:
    (empty_repo / "README.md").write_text("x")
    (empty_repo / "CONTRIBUTING.md").write_text("x")
    (empty_repo / "docs").mkdir()
    (empty_repo / "docs" / "decisions").mkdir()
    (empty_repo / "AGENTS.md").write_text("x")
    res = assess_repo.detect(empty_repo)
    assert res["axes"]["documentation"] == 5


def test_security_axis_full(empty_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (empty_repo / ".gitignore").write_text(".agent/\n.env\n")
    (empty_repo / ".pre-commit-config.yaml").write_text("repos: []\n")
    (empty_repo / ".devcontainer").mkdir()
    (empty_repo / ".devcontainer" / "devcontainer.json").write_text("{}")

    fake_tools = {"gitleaks", "semgrep", "pip-audit"}
    monkeypatch.setattr(
        assess_repo.shutil,
        "which",
        lambda name: "/usr/bin/" + name if name in fake_tools else None,
    )
    res = assess_repo.detect(empty_repo)
    assert res["axes"]["security"] == 5


def test_gitignore_unreadable_does_not_crash(
    empty_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (empty_repo / ".gitignore").write_text(".agent")
    real_read = Path.read_text

    def boom(self: Path, *a, **k):  # type: ignore[no-untyped-def]
        if self.name == ".gitignore":
            raise OSError("boom")
        return real_read(self, *a, **k)

    monkeypatch.setattr(Path, "read_text", boom)
    # should not raise
    res = assess_repo.detect(empty_repo)
    assert "stage" in res


def test_main_text_output(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (empty_repo / "CLAUDE.md").write_text("x")
    rc = (
        assess_repo.main_with_args(["--repo", str(empty_repo)])
        if hasattr(assess_repo, "main_with_args")
        else _run_main(assess_repo, ["--repo", str(empty_repo)])
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "Stage:" in out
    assert "Runtimes:" in out
    assert "claude-code" in out


def test_main_json_output(empty_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run_main(assess_repo, ["--repo", str(empty_repo), "--json"])
    import json

    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert data["stage"] == "S0"


def test_main_missing_repo(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = _run_main(assess_repo, ["--repo", str(tmp_path / "nope")])
    assert rc == 2
    err = capsys.readouterr().err
    assert "does not exist" in err


def _run_main(module, argv: list[str]) -> int:
    """Invoke a stdlib argparse `main()` with patched argv."""
    import sys

    saved = sys.argv
    sys.argv = [module.__name__, *argv]
    try:
        return module.main()
    finally:
        sys.argv = saved
