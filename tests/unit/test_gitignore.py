from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from local_agent_harness.core import gitignore


def test_detect_stack_keywords_empty(tmp_path: Path) -> None:
    kws = gitignore.detect_stack_keywords(tmp_path)
    # OS and git keywords always present
    assert "git" in kws
    assert "linux" in kws
    assert "macos" in kws


def test_detect_python(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    kws = gitignore.detect_stack_keywords(tmp_path)
    assert "python" in kws


def test_detect_node(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}\n")
    kws = gitignore.detect_stack_keywords(tmp_path)
    assert "node" in kws


def test_detect_react_implies_node(tmp_path: Path) -> None:
    (tmp_path / "app.tsx").write_text("// tsx\n")
    kws = gitignore.detect_stack_keywords(tmp_path)
    assert "react" in kws
    assert "node" in kws


def test_detect_vscode(tmp_path: Path) -> None:
    (tmp_path / ".vscode").mkdir()
    kws = gitignore.detect_stack_keywords(tmp_path)
    assert "visualstudiocode" in kws


def test_detect_keywords_with_subdir(tmp_path: Path) -> None:
    subdir = tmp_path / "src"
    subdir.mkdir()
    (subdir / "main.py").write_text("# python\n")
    kws = gitignore.detect_stack_keywords(tmp_path)
    # subdir scanning finds .py file extension → python keyword
    assert "python" in kws


def test_detect_keywords_oserror_on_listdir(tmp_path: Path) -> None:
    # Should not raise even if listdir raises
    with patch("os.listdir", side_effect=OSError("denied")):
        kws = gitignore.detect_stack_keywords(tmp_path)
    # Still returns base keywords
    assert "git" in kws


def test_render_gitignore_creates_file(empty_repo: Path) -> None:
    with patch.object(gitignore, "fetch_gitignore_template", return_value="# template\n"):
        msg = gitignore.render_gitignore(empty_repo, dry=False)
    gi = empty_repo / ".gitignore"
    assert gi.exists()
    text = gi.read_text()
    assert "# template" in text
    assert ".agent/logs/" in text
    assert "created" in msg


def test_render_gitignore_dry_run_no_file(empty_repo: Path) -> None:
    msg = gitignore.render_gitignore(empty_repo, dry=True)
    assert not (empty_repo / ".gitignore").exists()
    assert "would create" in msg


def test_render_gitignore_appends_to_existing(empty_repo: Path) -> None:
    (empty_repo / ".gitignore").write_text("*.pyc\n")
    msg = gitignore.render_gitignore(empty_repo, dry=False)
    text = (empty_repo / ".gitignore").read_text()
    assert ".agent/logs/" in text
    assert "appended" in msg


def test_render_gitignore_append_dry_run(empty_repo: Path) -> None:
    (empty_repo / ".gitignore").write_text("*.pyc\n")
    msg = gitignore.render_gitignore(empty_repo, dry=True)
    # File should NOT be modified in dry run
    assert (empty_repo / ".gitignore").read_text() == "*.pyc\n"
    assert "would append" in msg


def test_render_gitignore_idempotent_managed(empty_repo: Path) -> None:
    with patch.object(gitignore, "fetch_gitignore_template", return_value="# tmpl\n"):
        gitignore.render_gitignore(empty_repo, dry=False)
    msg = gitignore.render_gitignore(empty_repo, dry=False)
    assert "already managed" in msg


def test_render_gitignore_idempotent_covers_harness(empty_repo: Path) -> None:
    harness_content = "\n".join(gitignore._HARNESS_LINES) + "\n"
    (empty_repo / ".gitignore").write_text(harness_content)
    msg = gitignore.render_gitignore(empty_repo, dry=False)
    assert "already covers" in msg


def test_fetch_gitignore_template_fallback_on_error() -> None:
    with patch("urllib.request.urlopen", side_effect=OSError("network down")):
        result = gitignore.fetch_gitignore_template(["python"])
    assert "Minimal fallback" in result


def test_fetch_gitignore_template_empty_keywords() -> None:
    result = gitignore.fetch_gitignore_template([])
    assert "Minimal fallback" in result


def test_fetch_gitignore_template_success() -> None:
    class MockResp:
        def __enter__(self) -> "MockResp":
            return self
        def __exit__(self, *a: object) -> None:
            pass
        def read(self) -> bytes:
            return b"# python gitignore\n*.pyc\n"
    with patch("urllib.request.urlopen", return_value=MockResp()):
        result = gitignore.fetch_gitignore_template(["python"])
    assert "python gitignore" in result
