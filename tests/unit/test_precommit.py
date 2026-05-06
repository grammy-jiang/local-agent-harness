from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from local_agent_harness.core import precommit


def test_detect_languages_empty(tmp_path: Path) -> None:
    langs = precommit.detect_languages(tmp_path)
    assert isinstance(langs, set)


def test_detect_python(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    langs = precommit.detect_languages(tmp_path)
    assert "python" in langs


def test_detect_yaml(tmp_path: Path) -> None:
    (tmp_path / "config.yaml").write_text("key: value\n")
    langs = precommit.detect_languages(tmp_path)
    assert "yaml" in langs


def test_detect_shell(tmp_path: Path) -> None:
    (tmp_path / "run.sh").write_text("#!/bin/bash\n")
    langs = precommit.detect_languages(tmp_path)
    assert "shell" in langs


def test_detect_markdown(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Hi\n")
    langs = precommit.detect_languages(tmp_path)
    assert "markdown" in langs


def test_detect_languages_oserror_fallback(tmp_path: Path) -> None:
    with patch("os.listdir", side_effect=OSError("denied")):
        langs = precommit.detect_languages(tmp_path)
    assert isinstance(langs, set)


def test_detect_languages_with_subdir(tmp_path: Path) -> None:
    subdir = tmp_path / "src"
    subdir.mkdir()
    (subdir / "app.py").write_text("# python\n")
    langs = precommit.detect_languages(tmp_path)
    assert "python" in langs


def test_build_precommit_config_universal(tmp_path: Path) -> None:
    cfg = precommit.build_precommit_config(set())
    assert "gitleaks" in cfg
    assert "end-of-file-fixer" in cfg
    assert "pre-commit/pre-commit-hooks" in cfg


def test_build_precommit_config_python() -> None:
    cfg = precommit.build_precommit_config({"python"})
    assert "ruff" in cfg
    assert "mypy" in cfg


def test_build_precommit_config_gitignore_excluded() -> None:
    cfg = precommit.build_precommit_config({"python"})
    assert ".gitignore" in cfg


def test_build_precommit_config_no_duplicate_prettier() -> None:
    cfg = precommit.build_precommit_config({"javascript", "typescript"})
    assert cfg.count("prettier") >= 1
    assert cfg.count("- id: prettier") <= 1


def test_render_precommit_creates_file(empty_repo: Path) -> None:
    msg = precommit.render_precommit(empty_repo, dry=False)
    dest = empty_repo / ".pre-commit-config.yaml"
    assert dest.exists()
    assert "gitleaks" in dest.read_text()
    assert "created" in msg


def test_render_precommit_dry_run(empty_repo: Path) -> None:
    msg = precommit.render_precommit(empty_repo, dry=True)
    assert not (empty_repo / ".pre-commit-config.yaml").exists()
    assert "would create" in msg


def test_render_precommit_skips_existing(empty_repo: Path) -> None:
    (empty_repo / ".pre-commit-config.yaml").write_text("# custom\n")
    msg = precommit.render_precommit(empty_repo, dry=False)
    assert "skip" in msg
    assert (empty_repo / ".pre-commit-config.yaml").read_text() == "# custom\n"


def test_render_precommit_python_repo(empty_repo: Path) -> None:
    (empty_repo / "pyproject.toml").write_text("[project]\n")
    precommit.render_precommit(empty_repo, dry=False)
    text = (empty_repo / ".pre-commit-config.yaml").read_text()
    assert "ruff" in text
