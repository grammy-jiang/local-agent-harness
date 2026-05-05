from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from local_agent_harness.core import _paths


@pytest.fixture
def empty_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


@pytest.fixture(scope="session", autouse=True)
def _protect_skill_data(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Guard against tests/cleanup that may follow symlinks into the
    packaged ``skill_data`` directory and delete real source files.

    Snapshots the directory at session start and restores it at session
    end if any expected file went missing.
    """
    src = _paths.skill_data_root()
    snap = tmp_path_factory.mktemp("skill_data_snapshot") / "skill_data"
    shutil.copytree(src, snap)
    yield
    if not src.exists() or not (src / "SKILL.md").exists():
        if src.exists():
            shutil.rmtree(src)
        shutil.copytree(snap, src)


@pytest.fixture
def isolated_skill_root(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return a copy of skill_data the test can freely symlink/mutate
    without endangering the packaged assets.
    """
    src = _paths.skill_data_root()
    fake = tmp_path_factory.mktemp("isolated_skill") / "local-agent-harness"
    shutil.copytree(src, fake)
    monkeypatch.setattr(_paths, "skill_data_root", lambda: fake)
    monkeypatch.setattr(
        "local_agent_harness.cli.cmd_setup.skill_data_root", lambda: fake
    )
    return fake
