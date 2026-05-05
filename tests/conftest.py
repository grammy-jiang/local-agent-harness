from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def empty_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path
