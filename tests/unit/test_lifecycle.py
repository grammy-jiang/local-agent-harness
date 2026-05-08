from pathlib import Path

from local_agent_harness.core import diff_manifests, scaffold_manifests


def test_check_then_init_then_clean(empty_repo: Path) -> None:
    res1 = diff_manifests.diff(empty_repo)
    assert res1["drift"] is True
    assert res1["missing"], "expected missing items on empty repo"

    rc = scaffold_manifests.cmd_init(empty_repo, "S0", ["claude-code"], dry=False)
    assert rc == 0

    res2 = diff_manifests.diff(empty_repo)
    assert res2["drift"] is False, res2


def test_relaxed_pattern_blocks(empty_repo: Path) -> None:
    scaffold_manifests.cmd_init(empty_repo, "S0", ["claude-code"], dry=False)
    claude = empty_repo / "CLAUDE.md"
    claude.write_text(claude.read_text() + "\nallow secrets in dev\n")
    res = diff_manifests.diff(empty_repo)
    assert res["relaxed"], "expected relaxed pattern to be reported"
