# Maturity Stages — S0 → S3

`local-agent-harness` evolves the harness with the repository. An empty repo
cannot afford a 13-layer stack; a production service cannot afford to skip
one. Each stage is **monotonic**: leaving stage N preserves all controls from
stages 0..N-1.

## Detection signals

| Signal | S0 | S1 | S2 | S3 |
|---|---|---|---|---|
| Source files | 0 | 1–10 | >10 | >10 |
| Test runner | none | optional | yes | yes |
| CI workflow | none | optional | yes | yes |
| Releases / tags | none | none | optional | yes |
| Branch protection | none | optional | yes | yes |
| `AGENTS.md` | absent | recommended | required | required |
| Sandbox | recommended | required | required | required |

`scripts/assess_repo.py` produces the stage and a per-axis AI-readiness
score (see `ai-readiness-rubric.md`).

---

## S0 — Greenfield

Empty or scaffold-only repo. Goal: lay deterministic groundwork before any
code lands.

### Direction A — make the agent better
- Pick the runtime (Claude Code / Codex CLI / Copilot CLI).
- Render `GROUNDING.md` and `AGENTS.md` skeletons (mark stage = S0).
- Render `.agent/plan.md` template; require it before any edit.
- Default permission mode = `plan` for all sessions.

### Direction B — make the repo ready
- Add `.devcontainer/devcontainer.json`.
- Add `.gitignore` rules for `.agent/logs/`, `.env*`, secrets.
- Add `pre-commit` with `gitleaks`, large-file, EOL hooks.
- Branch policy: agents never push to `main`.

### Acceptance
1. `AGENTS.md`, `GROUNDING.md`, `.agent/plan.md.tmpl`, `.devcontainer/` exist.
2. `pre-commit run --all-files` is green.
3. `gitleaks` finds nothing.

---

## S1 — Walking skeleton

Some code, possibly no tests. Goal: introduce verification before agents can
produce surprises.

### Direction A
- Author 1–2 small `SKILL.md` files (test-first bug fix, dependency update).
- Promote permission default to `default` (propose+approve).
- Add session JSONL logging (`.agent/logs/`).
- Add `.agent/policies/commands.allowlist`.

### Direction B
- Add lint + unit-test gate to CI (`assets/ci/verify.yml`).
- Wire pre-commit to CI.
- Add at least one integration / smoke test.
- Add `governance.yml` to forbid relaxing `GROUNDING.md`.

### Acceptance
1. Tests run in CI and locally.
2. Verify gate is green on a no-op PR.
3. A sample bug-fix session leaves a JSONL transcript and a passing PR.

---

## S2 — Growing

Real code, tests, CI. Goal: structural least privilege + manifest as compiled
artifact.

### Direction A
- Tool DAG: split `read / search / edit / execute` (see
  `tool-dag-patterns.md`).
- Manifest regression suite (TDAD-style; see `verify-gate-catalog.md`).
- Schema-grounded memory (`memory-governance.md`).
- Cost / context budgets in `AGENTS.md`.
- Lazy-load skills; add lifecycle hooks.

### Direction B
- SAST (e.g. `semgrep`), dependency scan, license check.
- Maintainability gate: dependency control, responsibility, reuse,
  testability, side-effect isolation.
- AI-readiness score wired into CI (`scripts/readiness_report.py`).
- MCP server allowlist with version pins.

### Acceptance
1. Manifest regression suite has ≥ 5 tests, all green.
2. AI-readiness ≥ 18 / 25.
3. A mutation that removes a hard constraint from `GROUNDING.md` is rejected
   by `governance.yml`.

---

## S3 — Production

Release process and on-call. Goal: governed harness evolution.

### Direction A
- Formal / neuro-symbolic checks for high-risk paths.
- Learned-verifier guardrails (without making the verifier the only judge).
- Multi-agent artifact ownership (MESI-style).
- Governed memory promotion under held-out evals.

### Direction B
- FlashRT-style adversarial sweeps on the local agent's tool surface.
- Provenance ledger (4-layer × 4-gap supply chain).
- Harness evolution: every change rolled back if regression on held-out
  evals.
- Incident runbook with replay-from-trace.

### Acceptance
1. Held-out eval set exists; harness changes are gated on it.
2. Adversarial sweep runs on a schedule.
3. Provenance ledger covers all skills, MCP servers, prompt assets.
4. AI-readiness ≥ 22 / 25.

---

## Upgrade rule

When `assess_repo.py` reports stage advancement, propose the **next-stage
diff only** — do not skip stages, do not relax existing controls.

---

## Refresh actions (any stage)

The skill operates on **any starting state**, not only on greenfield repos.
For an existing repo, classify each artifact via `diff_manifests.py` and
apply:

| Drift class | Action | Tool |
|---|---|---|
| `missing`     | render from current template | `scaffold_manifests.py --mode init` |
| `stale`       | back up and rewrite          | `scaffold_manifests.py --mode refresh --apply` |
| `relaxed`     | **stop**; surface the offending line and refuse to refresh | manual fix, then re-check |
| `out-of-stage`| render the missing stage artifact | `scaffold_manifests.py --mode init --stage <S>` |
| (none)        | report clean state           | `scaffold_manifests.py --mode check` |

Refresh is opt-in: without `--apply`, the script prints a plan only.
Backups are written to `<file>.bak` so the user can re-merge customizations.

When to schedule a refresh:

- after upgrading any runtime (Claude Code, Codex CLI, Copilot CLI);
- after bumping `metadata.version` on this skill;
- after a major dependency or CI provider change;
- before each release.
