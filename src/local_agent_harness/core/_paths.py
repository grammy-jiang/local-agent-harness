"""Locate packaged skill data (assets/, references/, SKILL.md).

The package ships a copy of the skill under
``local_agent_harness/skill_data/local-agent-harness/``. This module finds
the assets directory whether installed as a wheel or used in editable mode.
"""
from __future__ import annotations

import importlib.resources
from pathlib import Path

_SKILL_NAME = "local-agent-harness"


def skill_data_root() -> Path:
    """Return the directory containing SKILL.md / assets/ / references/."""
    ref = importlib.resources.files("local_agent_harness") / "skill_data" / _SKILL_NAME
    p = Path(str(ref))
    if not p.is_dir():
        raise RuntimeError(f"skill_data not found at {p}")
    return p


def assets_dir() -> Path:
    return skill_data_root() / "assets"


def references_dir() -> Path:
    return skill_data_root() / "references"
