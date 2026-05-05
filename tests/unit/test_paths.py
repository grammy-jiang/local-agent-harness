from __future__ import annotations


import pytest

from local_agent_harness.core import _paths


def test_skill_data_root_returns_directory() -> None:
    p = _paths.skill_data_root()
    assert p.is_dir()
    assert (p / "SKILL.md").exists()


def test_assets_dir_exists() -> None:
    p = _paths.assets_dir()
    assert p.is_dir()
    assert (p / "AGENTS.md.tmpl").is_file()


def test_references_dir_exists() -> None:
    p = _paths.references_dir()
    assert p.is_dir()


def test_skill_data_root_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeRef:
        def __truediv__(self, _other: str) -> "_FakeRef":
            return self

        def __str__(self) -> str:
            return "/nonexistent/path/to/skill"

    monkeypatch.setattr(
        _paths.importlib.resources, "files", lambda _pkg: _FakeRef()
    )
    with pytest.raises(RuntimeError, match="skill_data not found"):
        _paths.skill_data_root()
