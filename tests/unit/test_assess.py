from pathlib import Path

from local_agent_harness.core import assess_repo


def test_empty_repo_is_S0(empty_repo: Path) -> None:
    result = assess_repo.detect(empty_repo)
    assert result["stage"] == "S0"
    assert result["axes"]["agent_config"] == 0
    assert result["total"] == 0


def test_with_readme_only(empty_repo: Path) -> None:
    (empty_repo / "README.md").write_text("# x\n")
    result = assess_repo.detect(empty_repo)
    assert result["stage"] == "S0"
    assert result["axes"]["documentation"] >= 1
