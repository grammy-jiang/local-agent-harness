# GitHub Copilot Instructions

## Build, Test, and Lint

```bash
# Install in editable mode with dev dependencies
pip install -e '.[dev]'

# Lint (ruff, line-length 100, target py3.11)
ruff check src tests

# Type-check (mypy strict)
mypy src/local_agent_harness

# Run all tests (95% coverage threshold enforced)
pytest --cov=local_agent_harness --cov-fail-under=95

# Run a single test
pytest tests/unit/test_scaffold.py::test_init_dry_run_does_not_write

# Run only unit or integration tests
pytest tests/unit/
pytest tests/integration/
```

Pre-commit hooks (`gitleaks`, `ruff`, file hygiene) are configured in `.pre-commit-config.yaml`.

## Architecture

The tool is a Python CLI (`typer`) that manages AI-agent harness files for repositories. It operates in three modes—`check` (read-only audit), `init` (render missing files), `refresh` (backup + rewrite stale files with `--apply`)—and scales its output to the repo's maturity stage (S0 → S3).

```
src/local_agent_harness/
├── cli/
│   ├── app.py            # Typer app wiring all cmd_*.py subcommands
│   └── cmd_*.py          # One module per CLI subcommand
├── core/
│   ├── assess_repo.py    # Detect stage (S0–S3) + score 5 axes (0–5 each, max 25)
│   ├── diff_manifests.py # Detect drift: missing / stale / relaxed / out-of-stage
│   ├── scaffold_manifests.py  # Render .tmpl templates into the target repo
│   ├── manifest_regression.py # Invariant assertions on rendered manifests
│   ├── readiness_report.py    # Machine-readable AI-readiness report
│   ├── redaction_smoke.py     # Verify no Red-class data leaks in manifests
│   └── _paths.py         # Locate bundled skill_data via importlib.resources
└── skill_data/local-agent-harness/
    ├── SKILL.md
    ├── assets/           # .tmpl template files for every manifest
    │   ├── AGENTS.md.tmpl, GROUNDING.md.tmpl, plan.md.tmpl
    │   ├── ci/, devcontainer.json.tmpl, pre-commit-config.yaml.tmpl
    │   └── runtime-overlays/  # CLAUDE.md, .codex/config, copilot-cli, cursor
    └── references/       # Markdown reference docs (rubric, anti-patterns, etc.)
```

**Data flow**: CLI commands call `core/` functions. `scaffold_manifests` reads templates from `skill_data/local-agent-harness/assets/` (located via `_paths.assets_dir()`), delegates stage detection to `assess_repo.detect()`, and drift detection to `diff_manifests`. Core modules also double as standalone scripts with `argparse` + `if __name__ == "__main__"`.

## Key Conventions

### Python style
- Every file starts with `from __future__ import annotations`.
- `mypy --strict` is enforced on `src/`. Tests are excluded from strict typing.
- `ruff` ignores `E701` (multiple statements on one line) and `E731` (lambda assignment); several `core/` files also ignore `E402` (import order) because of the `_paths` bootstrapping pattern.

### Template system
- Templates live in `skill_data/local-agent-harness/assets/` as `.tmpl` files.
- `_paths.assets_dir()` locates them via `importlib.resources` — works in both editable and wheel installs.
- Adding a new manifest: add the `.tmpl`, register it in `scaffold_manifests.py` (`CORE_FILES`, `STAGE_INFRA`, or `RUNTIME_OVERLAYS`), and add anchor strings to the `TARGETS` list in `diff_manifests.py`.

### Stage / maturity model
- `assess_repo.detect()` assigns S0–S3 based on source files, tests, CI, and tags.
- Stage gates control which templates are rendered; S0 = minimal kit, S3 = full governance.
- Five readiness axes: `agent_config`, `documentation`, `ci_cd`, `code_structure`, `security` — each 0–5; total max 25.

### Test fixtures (`tests/conftest.py`)
- `empty_repo` — creates a temporary `git init` directory; use for scaffold/check tests.
- `isolated_skill_root` — monkeypatches `_paths.skill_data_root` so tests can freely mutate asset copies without corrupting the packaged source.
- `_protect_skill_data` (session-scoped, autouse) — snapshots and restores `skill_data/` if tests accidentally delete it.

### CI gates
- `verify.yml` — lint → unit tests (≥95% coverage) → gitleaks secrets scan → manifest regression.
- `governance.yml` — asserts `AGENTS.md`/`GROUNDING.md` present; blocks PRs that remove `HC*` hard-constraint lines from `GROUNDING.md`; checks AI-readiness does not regress.
- Both workflows must be green to merge.

### Commit and branch conventions (from `GROUNDING.md` / `AGENTS.md`)
- Branch naming: `agent/<task-slug>`.
- Commit style: Conventional Commits.
- `GROUNDING.md` hard constraints (`HC1`–`HC6`) may never be removed; changes require a dedicated PR.
