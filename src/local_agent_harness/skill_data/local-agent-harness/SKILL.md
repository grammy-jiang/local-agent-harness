---
name: local-agent-harness
description: Manage the local AI-coding-agent harness for any repository — empty, partially configured, or fully mature. Detects the repo's maturity stage (S0 greenfield → S3 production), audits existing manifests for drift (missing sections, relaxed constraints, stale overlays), and applies a stage-appropriate harness covering both the agent (AGENTS.md with inlined HC1–HC6 hard constraints, plan.md, tool DAG, permission ladder, governed memory, cost/context budgets, runtime overlays for Claude Code / Codex CLI / Copilot CLI) and the repo (sandbox/devcontainer, pre-commit, verify CI on GitHub Actions, governance CI, secrets/SAST/dep scans, AI-readiness score). Use when the user says "make this repo agent-ready", "bootstrap AGENTS.md", "audit our agent setup", "score AI-readiness", "refresh the harness", "check whether AGENTS.md is up to date", or "evolve the harness as the repo grows". Three modes — check (read-only audit), init (render missing artifacts; never overwrites), refresh (back up + rewrite stale artifacts).
---

# local-agent-harness

A maturity-aware harness manager for local AI coding agents. It works on
**any starting state** of the repository:

| Repo state | Direction A (agent) state | What this skill does |
|---|---|---|
| empty / new | none | `init` — render the S0 spine |
| has code, no agent config | none | `init` — render manifests + overlays |
| has code + partial agent config | partial | `check` then `refresh` the stale parts |
| has code + full agent config | full | `check` and report "no action needed" |
| has code + drifted/relaxed config | full but drifted | `check` flags drift; `refresh` repairs |

The two directions:

- **Direction A — make the agent better:** manifests (AGENTS.md, GROUNDING.md,
  plan.md), runtime overlays, tool DAG, permission ladder, governed memory,
  cost/context budgets.
- **Direction B — make the repo ready:** sandbox, branch policy, pre-commit,
  verification CI, governance CI, secrets/SAST/dep scans, AI-readiness score.

The harness evolves with the repo's stage (S0–S3) and is **monotonic** — higher
layers may specialize but never relax lower-layer constraints.

## When to use

- "Make this repo ready for Claude Code / Codex CLI / Copilot CLI."
- "Audit the AGENTS.md / GROUNDING.md / CLAUDE.md we already have."
- "Check whether the harness is up to date."
- "Refresh the agent configuration after a tooling upgrade."
- "Score AI-readiness."
- "Evolve the harness as the repo grows."

## When NOT to use

- Pure code refactors with no agent-readiness intent.
- Generic CI/CD setup unrelated to AI agents.
- Authoring application code.

## Inputs the agent should gather

1. The **repository path** (default: cwd).
2. The **target runtime(s)** — any of `claude-code`, `codex-cli`,
   `copilot-cli` (auto-detected from existing files; otherwise ask).
3. The **operating mode** — `check`, `init`, or `refresh` (default: start
   with `check`).
4. The **direction** to optimize — A, B, or both (default: both).

If the `local-agent-harness` CLI is not yet installed, instruct the user
to run `pipx install local-agent-harness` before invoking the skill.

## Workflow

The workflow always **classifies first, acts second**. There is no
"bootstrap-only" path.

### Step 1 — Assess the repo and detect drift

> The `local-agent-harness` CLI must be installed first. The recommended
> install path is `pipx install local-agent-harness`. All commands below
> assume the CLI is on `$PATH`.

```bash
local-agent-harness assess --repo <path> --json
local-agent-harness check  --repo <path>
```

`assess` reports stage (S0/S1/S2/S3) and a 5-axis AI-readiness score.
`check` classifies every expected artifact as one of:

- **missing** — needs `init`.
- **stale** — exists but missing required sections / anchors; needs `refresh`.
- **relaxed** — exists but contains language that relaxes a hard
  constraint (e.g., `disable gitleaks`, `bypass permissions`); **blocks
  refresh** until resolved manually.
- **out-of-stage** — required by the detected stage but absent.

If `local-agent-harness check` exits 0 with no drift, you are done —
report the clean state to the user. Non-zero exit codes:

- `1` — drift detected (`missing`, `stale`, or `out_of_stage` items).
- `2` — `relaxed` items detected; refresh is **blocked** until cleared.

### Step 2 — Confirm runtime(s) and direction

If runtimes were not auto-detected (no `CLAUDE.md`, no `.codex/config`, etc.),
ask once which to render. Default to both directions.

### Step 3 — Choose mode and act

Pick the mode based on the assessment in Step 1:

| Drift report says… | Use mode |
|---|---|
| only `missing` items | `init` |
| any `stale` items | `refresh` |
| any `relaxed` items | **stop** and report; refuse to refresh until cleared |
| nothing | done |

Run:

```bash
# render artifacts that don't exist yet (never overwrites)
local-agent-harness init --repo <path> \
  [--stage S0|S1|S2|S3] \
  [--runtime claude-code] [--runtime codex-cli] ...

# audit-only; non-zero exit on any drift; suitable for CI
local-agent-harness check --repo <path>

# back up stale files to <file>.bak and rewrite from current templates
# (without --apply this is plan-only — show the user what would change)
local-agent-harness refresh --repo <path>
local-agent-harness refresh --repo <path> --apply
```

If `--stage` is omitted, the CLI auto-detects the stage from the repo.
For `refresh --apply`, always show the user the planned diff first
(`refresh` without `--apply`) and request confirmation before
overwriting. Backups land at `<file>.bak`.

### Step 4 — Validate verification gates

```bash
local-agent-harness validate --repo <path>
```

`validate` runs both manifest-regression and redaction-smoke checks and
exits non-zero on any failure. If a check fails, fix the reported item;
do not bypass.

### Step 5 — Emit (or update) the readiness report

```bash
local-agent-harness report --repo <path> --out <path>/.agent/eval/readiness.md
local-agent-harness report --repo <path> --check-no-regression <path>/.agent/eval/readiness.md
```

The first command writes a readiness file with a parseable machine
block. The second compares the new score against the previous block per
axis and exits non-zero if any axis dropped (monotonicity).

### Step 6 — Iterate / schedule next check

If the stage advanced (e.g., the user added tests + CI between sessions),
propose the next-stage upgrade as a separate PR. Otherwise, recommend
re-running `--mode check` whenever:

- a runtime is upgraded (Claude Code, Codex CLI, Copilot CLI);
- a new template version of this skill is released (compare
  `metadata.version`);
- a major dependency or CI provider changes;
- before each release.

## Verification (skill-level acceptance)

The skill is not done until, for the target repo:

1. `local-agent-harness check --repo <path>` exits 0.
2. `local-agent-harness validate --repo <path>` exits 0.
3. A readiness file exists and `local-agent-harness report --check-no-regression`
   against it exits 0.
4. Re-running `local-agent-harness init` is a no-op (idempotent).

## Stop conditions

- **Secrets already committed:** stop. Ask the user to rotate and rewrite
  history before continuing. Do not silently fix.
- **`relaxed` drift detected:** stop. The repo contains language that
  weakens a hard constraint (e.g., disabling gitleaks). Surface the offending
  file and pattern; refuse to `refresh --apply` until cleared.
- **User asks to skip a stage** (e.g., S0 → S2): stop and explain
  monotonicity; offer S0 → S1 first.
- **Conflicting overlays:** if the runtime overlay would override a `GROUNDING.md`
  hard constraint, refuse and link `references/manifest-anti-patterns.md`.

## Examples

### Example 1 — Empty Python repo (init S0 → S1)
User: "Make this empty repo ready for Claude Code."
1. `local-agent-harness assess` → `stage=S0`.
2. `local-agent-harness check` → all required artifacts `missing`.
3. `local-agent-harness init --runtime claude-code` renders the spine.
4. `local-agent-harness validate` passes; readiness ≈ 6/25; next-stage
   list = add tests + CI.

### Example 2 — Node service with tests, AGENTS.md exists but stale (refresh)
User: "We use Codex CLI; check our agent setup."
1. `local-agent-harness assess` → `stage=S1`.
2. `local-agent-harness check` reports `AGENTS.md` is **stale** (missing
   `Cost and Context Policy` and `PR Evidence`), `.codex/config` is **stale**
   (missing `[paths]` section), `.github/workflows/verify.yml` is **missing**.
3. `local-agent-harness refresh` (plan only) shows two backups + one new
   file. After user confirmation, re-run with `--apply`.
4. `local-agent-harness validate` passes; report previous and new scores
   side-by-side.

### Example 3 — Production Go service, fully configured (check)
User: "Is our harness still current?"
1. `local-agent-harness assess` → `stage=S3`.
2. `local-agent-harness check` exits 0 → no drift.
3. Report "no action needed"; suggest next check after the next runtime
   upgrade.

### Example 4 — Repo with relaxed governance (blocked)
User: "Refresh our harness."
1. `local-agent-harness check` finds `disable gitleaks` in
   `.pre-commit-config.yaml` and exits with code 2.
2. Skill stops, prints the offending pattern and file, and refuses to
   `refresh --apply` until the user removes the relaxation.

## Troubleshooting

### "stale" but the file is correct for our project
Cause: a section name was localized or renamed. Fix: keep the canonical
section names from `assets/AGENTS.md.tmpl`; project-specific sections may be
appended below.

### `refresh --apply` overwrote my customizations
Cause: refresh rewrites stale files entirely. Backups are at `<file>.bak`.
Re-merge your customizations from the backup, then re-run
`local-agent-harness check`.

### Idempotency check fails
Cause: something wrote a file outside the harness path. Only
`local-agent-harness init`, `refresh`, and `report` are allowed to write.

### The score went down after a change
Cause: a manifest section was removed, or an overlay introduced HC-relaxing
language. The `governance.yml` workflow blocks this in CI;
`local-agent-harness report --check-no-regression` enforces it locally.

### Codex CLI / Copilot CLI does not pick up the overlay
Cause: file path or naming differs across versions. See
`references/runtime-overlays.md` for current paths.

## References

- `references/stages.md` — S0–S3 playbook with init / refresh actions per stage.
- `references/ai-readiness-rubric.md` — 5-axis scoring rules.
- `references/tool-dag-patterns.md` — read/search/edit/execute split.
- `references/memory-governance.md` — three tiers, schema-grounded.
- `references/verify-gate-catalog.md` — the gate sequence.
- `references/runtime-overlays.md` — Claude Code / Codex / Copilot paths.
- `references/manifest-anti-patterns.md` — relaxed-HC patterns and fixes.
- `references/source-mapping.md` — links to the research vault.
