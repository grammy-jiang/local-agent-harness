# AGENTS.md

> Agent instructions for this repository.
> See also: `.agent/plan.md` (session plan).

<!-- local-agent-harness:auto:begin -->
<!-- stack: Python -->

## Setup

```bash
pip install -e '.[dev]'  # or: uv sync
```

## Build

```bash
# see pyproject.toml for available tasks
uv build
```

## Testing

```bash
pytest  # --cov-fail-under=95
pytest path/to/test_file.py::test_function_name
```

## Lint and Format

```bash
ruff check src tests
```

<!-- local-agent-harness:auto:end -->

## Conventions

- Branch naming: `agent/<task-slug>`
- Commit style: Conventional Commits
- `from __future__ import annotations` at the top of every Python file.

## Scope Boundary

| Action | Allowed scope |
|---|---|
| Read   | entire repo |
| Edit   | `src/`, `tests/`, `docs/`, `.agent/plan.md` |
| Create | within edit scope |
| Delete | requires human approval |
| Execute | `ruff`, `pytest`, `uv`, `git diff/status/log/add/commit/push` |
| Network | denied by default |

## Security

- HC1: No plaintext secrets, credentials, or tokens in source, logs, or prompts.
- HC2: Never write to paths outside the declared edit scope without human approval.
- HC3: Do not disable or bypass `gitleaks`, `ruff`, or the CI gate.
- HC4: No new network calls from src/ without explicit human approval.
- HC5: Test coverage must not drop below 95 % (`--cov-fail-under=95`).
- HC6: All hard constraints are monotonic — overlays may specialise but never relax them.

See `.claude/settings.json` for the tool allow/deny list.

## PR Checklist

1. All tests pass (`pytest --cov-fail-under=95`).
2. Linter clean (`ruff check src tests`).
3. No new secrets or SAST findings (`gitleaks`).
4. Version bumped in `pyproject.toml`; `CHANGELOG.md` entry added.
5. PR description: change summary, risks, and verification evidence.
6. Append a `Decisions log` entry in `.agent/plan.md` for non-trivial choices.
