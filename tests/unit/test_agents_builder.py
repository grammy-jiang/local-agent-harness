from __future__ import annotations

import json
from pathlib import Path

from local_agent_harness.core import agents_builder


def test_detect_project_info_empty(empty_repo: Path) -> None:
    info = agents_builder.detect_project_info(empty_repo)
    assert "stack" in info
    assert "test_cmds" in info
    assert isinstance(info["stack"], list)


def test_detect_python_project(empty_repo: Path) -> None:
    (empty_repo / "pyproject.toml").write_text(
        "[project]\nname = 'myapp'\n\n"
        "[tool.pytest.ini_options]\ntestpaths=['tests']\naddopts='--cov-fail-under=90'\n\n"
        "[tool.ruff]\nline-length = 100\n\n"
        "[tool.mypy]\nstrict = true\n"
    )
    info = agents_builder.detect_project_info(empty_repo)
    assert "Python" in info["stack"]
    assert any("pytest" in c for c in info["test_cmds"])
    assert any("90" in c for c in info["test_cmds"])
    assert any("ruff" in c for c in info["lint_cmds"])
    assert any("100" in h for h in info["style_hints"])
    assert any("strict" in h for h in info["style_hints"])


def test_detect_python_uv(empty_repo: Path) -> None:
    (empty_repo / "pyproject.toml").write_text(
        "[project]\nname = 'myapp'\n\n[build-system]\nrequires=['hatchling']\n"
        "[tool.uv]\ndev-dependencies = []\n"
    )
    info = agents_builder.detect_project_info(empty_repo)
    assert "Python" in info["stack"]
    assert any("uv sync" in c for c in info["install_cmds"])


def test_detect_python_target_version(empty_repo: Path) -> None:
    (empty_repo / "pyproject.toml").write_text(
        "[project]\nname = 'x'\n\n[tool.ruff]\ntarget-version = \"py311\"\nline-length = 88\n"
    )
    info = agents_builder.detect_project_info(empty_repo)
    assert any("py311" in h for h in info["style_hints"])


def test_detect_python_grounding_reads(empty_repo: Path) -> None:
    (empty_repo / "pyproject.toml").write_text("[project]\nname='x'\n")
    (empty_repo / "GROUNDING.md").write_text("Use Conventional Commits.\nBranch: agent/foo\n")
    info = agents_builder.detect_project_info(empty_repo)
    assert info["commit_style"] == "Conventional Commits"
    assert info["branch_pattern"] == "agent/<task-slug>"


def test_detect_node_project(empty_repo: Path) -> None:
    pkg = {
        "scripts": {"test": "jest", "lint": "eslint src"},
        "devDependencies": {},
    }
    (empty_repo / "package.json").write_text(json.dumps(pkg))
    info = agents_builder.detect_project_info(empty_repo)
    assert "Node.js" in info["stack"]
    assert any("test" in c for c in info["test_cmds"])


def test_detect_node_build_lint_format(empty_repo: Path) -> None:
    pkg = {
        "scripts": {
            "build": "tsc",
            "lint:fix": "eslint --fix src",
            "fmt": "prettier --write .",
        }
    }
    (empty_repo / "package.json").write_text(json.dumps(pkg))
    info = agents_builder.detect_project_info(empty_repo)
    assert any("build" in c for c in info["build_cmds"])
    assert any("lint:fix" in c for c in info["lint_cmds"])
    assert any("fmt" in c for c in info["format_cmds"])


def test_detect_node_invalid_json(empty_repo: Path) -> None:
    (empty_repo / "package.json").write_text("not json")
    info = agents_builder.detect_project_info(empty_repo)
    assert "Node.js" in info["stack"]


def test_detect_go_project(empty_repo: Path) -> None:
    (empty_repo / "go.mod").write_text("module example.com/app\n\ngo 1.21\n")
    info = agents_builder.detect_project_info(empty_repo)
    assert "Go" in info["stack"]
    assert any("go test" in c for c in info["test_cmds"])


def test_detect_rust_project(empty_repo: Path) -> None:
    (empty_repo / "Cargo.toml").write_text("[package]\nname = 'myapp'\nversion = '0.1.0'\n")
    info = agents_builder.detect_project_info(empty_repo)
    assert "Rust" in info["stack"]
    assert any("cargo test" in c for c in info["test_cmds"])
    assert any("cargo clippy" in c for c in info["lint_cmds"])


def test_detect_makefile(empty_repo: Path) -> None:
    (empty_repo / "Makefile").write_text("all:\n\techo hi\n")
    info = agents_builder.detect_project_info(empty_repo)
    assert any("Makefile" in c for c in info["build_cmds"])


def test_git_function(tmp_path: Path) -> None:
    # _git should return empty string on failure without raising
    result = agents_builder._git(tmp_path, "log", "--oneline")
    assert isinstance(result, str)


def test_build_agents_md_contains_required_sections(empty_repo: Path) -> None:
    info = agents_builder.detect_project_info(empty_repo)
    content = agents_builder.build_agents_md(empty_repo, info)
    assert "# AGENTS.md" in content
    assert "Testing" in content
    assert "Scope Boundary" in content
    assert agents_builder._BEGIN in content
    assert agents_builder._END in content


def test_build_auto_block_with_install_and_lint(empty_repo: Path) -> None:
    (empty_repo / "pyproject.toml").write_text(
        "[project]\nname='x'\n\n[tool.ruff]\nline-length=88\n"
    )
    info = agents_builder.detect_project_info(empty_repo)
    block = agents_builder._build_auto_block(info)
    assert "Setup" in block
    assert "Lint and Format" in block


def test_update_agents_md_creates_file(empty_repo: Path) -> None:
    msg = agents_builder.update_agents_md(empty_repo, dry=False)
    assert (empty_repo / "AGENTS.md").exists()
    assert "created" in msg


def test_update_agents_md_dry_run(empty_repo: Path) -> None:
    msg = agents_builder.update_agents_md(empty_repo, dry=True)
    assert not (empty_repo / "AGENTS.md").exists()
    assert "would create" in msg


def test_update_agents_md_refreshes_auto_sections(empty_repo: Path) -> None:
    # First create
    agents_builder.update_agents_md(empty_repo, dry=False)
    # Add a pyproject.toml to change detected info
    (empty_repo / "pyproject.toml").write_text(
        "[project]\nname='x'\n\n[tool.ruff]\nline-length=88\n"
    )
    msg = agents_builder.update_agents_md(empty_repo, dry=False)
    content = (empty_repo / "AGENTS.md").read_text()
    assert "Python" in content
    assert "refreshed" in msg or "up to date" in msg


def test_update_agents_md_dry_refresh(empty_repo: Path) -> None:
    # Create, then ask for dry refresh of something that would change
    agents_builder.update_agents_md(empty_repo, dry=False)
    (empty_repo / "pyproject.toml").write_text(
        "[project]\nname='x'\n\n[tool.ruff]\nline-length=88\n"
    )
    msg = agents_builder.update_agents_md(empty_repo, dry=True)
    assert "would refresh" in msg or "up to date" in msg


def test_update_agents_md_preserves_human_content(empty_repo: Path) -> None:
    initial = (
        f"{agents_builder._BEGIN}\n"
        "<!-- stack: general -->\n"
        f"{agents_builder._END}\n\n"
        "## Human section\n\nKeep this!\n"
    )
    (empty_repo / "AGENTS.md").write_text(initial)
    agents_builder.update_agents_md(empty_repo, dry=False)
    content = (empty_repo / "AGENTS.md").read_text()
    assert "Keep this!" in content


def test_update_agents_md_prepends_to_existing_no_sentinels(empty_repo: Path) -> None:
    (empty_repo / "AGENTS.md").write_text("# Old AGENTS.md\n\nSome content.\n")
    msg = agents_builder.update_agents_md(empty_repo, dry=False)
    content = (empty_repo / "AGENTS.md").read_text()
    assert agents_builder._BEGIN in content
    assert "Old AGENTS.md" in content
    assert "prepended" in msg


def test_update_agents_md_dry_prepend(empty_repo: Path) -> None:
    (empty_repo / "AGENTS.md").write_text("# Old AGENTS.md\n\nSome content.\n")
    msg = agents_builder.update_agents_md(empty_repo, dry=True)
    # Dry run: file should not be modified
    content = (empty_repo / "AGENTS.md").read_text()
    assert agents_builder._BEGIN not in content
    assert "would prepend" in msg


def test_update_agents_md_idempotent(empty_repo: Path) -> None:
    agents_builder.update_agents_md(empty_repo, dry=False)
    content_before = (empty_repo / "AGENTS.md").read_text()
    agents_builder.update_agents_md(empty_repo, dry=False)
    content_after = (empty_repo / "AGENTS.md").read_text()
    assert content_before == content_after
