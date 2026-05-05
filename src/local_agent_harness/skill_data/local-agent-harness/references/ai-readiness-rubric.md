# AI-Readiness Rubric

Five axes, 0–5 each, total 25. Computed by `scripts/assess_repo.py` and
recorded in `.agent/eval/readiness.md`. Monotonic: a harness change must not
reduce the score on any axis.

## Axis 1 — Agent config (0–5)

| Score | Criteria |
|---|---|
| 0 | No agent-aware files. |
| 1 | `AGENTS.md` present, even minimal. |
| 2 | `AGENTS.md` + `GROUNDING.md` present. |
| 3 | + at least one runtime overlay (CLAUDE.md, codex.config, etc.). |
| 4 | + `.skills/` directory with ≥ 1 `SKILL.md`. |
| 5 | + manifest regression suite green. |

## Axis 2 — Documentation (0–5)

| Score | Criteria |
|---|---|
| 0 | No README. |
| 1 | README exists. |
| 2 | + contributor / setup section. |
| 3 | + decision log (`docs/decisions/` or equivalent). |
| 4 | + per-module docs or API docs generated. |
| 5 | + agent-facing context map (what agents should read first). |

## Axis 3 — CI/CD (0–5)

| Score | Criteria |
|---|---|
| 0 | No CI. |
| 1 | CI runs lint or tests. |
| 2 | CI runs lint + tests. |
| 3 | + secrets scan + branch protection. |
| 4 | + governance workflow (manifest non-relaxation check). |
| 5 | + AI-readiness regression gate. |

## Axis 4 — Code structure (0–5)

| Score | Criteria |
|---|---|
| 0 | Single-file repo or unstructured. |
| 1 | `src/` (or equivalent) layout. |
| 2 | + `tests/` mirror. |
| 3 | + module boundaries documented. |
| 4 | + dependency graph clean (no cycles). |
| 5 | + maintainability checks in CI. |

## Axis 5 — Security (0–5)

| Score | Criteria |
|---|---|
| 0 | No checks. |
| 1 | `.gitignore` excludes secrets and logs. |
| 2 | + `gitleaks` (or equivalent) in pre-commit. |
| 3 | + dependency scanner. |
| 4 | + SAST. |
| 5 | + sandbox enforced (devcontainer / docker / E2B) and red-data
classification respected in logs. |

## Stage gates

| Stage | Minimum total | Per-axis minimum |
|---|---|---|
| S0 → S1 | 5 | 1 on each axis |
| S1 → S2 | 12 | 2 on each axis |
| S2 → S3 | 18 | 3 on each axis |
| S3 stable | 22 | 4 on each axis |
