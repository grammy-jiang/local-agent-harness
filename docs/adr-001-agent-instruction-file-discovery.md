# ADR-001 — How AI Agents Discover Instruction Files

**Date:** 2026-05-08  
**Status:** Accepted  
**Commits:** `be70c6a`, `1c77acb`

---

## Context

The `local-agent-harness` skill generates a set of instruction files intended
to ground AI coding agents with project conventions, hard constraints (HC1–HC6),
scope boundaries, and security policies.  Before commit `1c77acb`, the harness
produced two top-level files:

| File | Intended purpose |
|---|---|
| `AGENTS.md` | Primary instruction file for GitHub Copilot and Codex CLI |
| `GROUNDING.md` | Hard constraints (HC1–HC6) |

A review of official documentation for each agent revealed that this design
had a critical flaw: **`GROUNDING.md` was never read by any agent
automatically**, and `CLAUDE.md` was only generated when `--runtime
claude-code` was explicitly passed.

---

## Investigation: How Each Agent Reads Instructions

### Claude Code

**Discovery mechanism:** Claude Code looks for `CLAUDE.md` (or
`.claude/CLAUDE.md`) at session start.  It walks up the directory tree and
loads every `CLAUDE.md` it finds, with files closer to the working directory
taking precedence.

**Key feature — `@path` imports:** `CLAUDE.md` supports an `@path/to/file`
directive that causes Claude Code to load the referenced file at startup,
effectively inlining it into the context window.  This is the only way to
make Claude Code aware of `AGENTS.md` — without an `@AGENTS.md` import in
`CLAUDE.md`, Claude Code receives no project instructions.

**Does it read `AGENTS.md` directly?** No — only if explicitly imported via
`@AGENTS.md` in `CLAUDE.md`.  
**Does it read `GROUNDING.md` directly?** No.

---

### GitHub Copilot (coding agent)

**Discovery mechanism:** Copilot reads `AGENTS.md` natively, walking the
directory tree from the root down to the current working directory.  It also
reads `.github/copilot-instructions.md` for repository-wide context (this is
the "repo custom instructions" feature).

**Does it read `AGENTS.md` directly?** Yes.  
**Does it read `GROUNDING.md` directly?** No — only if cross-referenced as
plain text inside `AGENTS.md`, which no agent interprets as a load directive.

---

### OpenAI Codex CLI

**Discovery mechanism:** Codex CLI reads `AGENTS.md` natively.  It builds an
instruction chain: `~/.codex/AGENTS.md` → each directory from the repo root
down to the CWD.  Files closer to the CWD take precedence.  It also reads
`.codex/INSTRUCTIONS.md` for repo-scoped overlay settings.

**Does it read `AGENTS.md` directly?** Yes.  
**Does it read `GROUNDING.md` directly?** No.

---

## Findings Summary

| File | Claude Code | Copilot | Codex CLI |
|---|---|---|---|
| `CLAUDE.md` (with `@AGENTS.md`) | ✅ loaded at startup | ❌ ignored | ❌ ignored |
| `AGENTS.md` | ❌ not auto-loaded | ✅ native | ✅ native |
| `GROUNDING.md` | ❌ never read | ❌ never read | ❌ never read |
| `.github/copilot-instructions.md` | ❌ | ✅ repo instructions | ❌ |
| `.codex/INSTRUCTIONS.md` | ❌ | ❌ | ✅ overlay |

**Result:** HC1–HC6 hard constraints, stored only in `GROUNDING.md`, were
invisible to every agent.

---

## Bugs Found in `local-agent-harness`

### Bug B1 — Wrong overlay detection paths in `assess_repo.py`

`assess_repo.detect()` checked for the following files to determine which
runtimes were configured:

| What it checked | What actually exists |
|---|---|
| `.codex/config` | `.codex/INSTRUCTIONS.md` |
| `.github/copilot-cli.md` | `.github/copilot-instructions.md` |

As a result, `detected_runtimes` was always empty even after overlay files
were created, causing the readiness score to under-report, and making the
`--mode refresh` path unable to auto-detect existing runtimes.

The same wrong paths appeared in `manifest_regression.py`'s overlay check.

### Bug B2 — `scaffold_manifests.main()` never created runtime overlays by default

`main()` (the argparse CLI entry point) passed `args.runtime` directly to
`cmd_init()`.  `args.runtime` defaults to `[]` when `--runtime` is omitted.
No fallback logic existed, so on a fresh `local-agent-harness init` run with
no flags, **zero overlay files were created** — `CLAUDE.md`,
`.codex/INSTRUCTIONS.md`, and `.github/copilot-instructions.md` were all
absent.  Consequently, Claude Code received no instructions at all.

The Typer CLI (`cmd_init.run()`) had the same problem: when stdin is not a
TTY (CI, test runners, scripted invocations), `_prompt_runtimes()` returns
`[]` and the same zero-overlay outcome occurred.

### Bug B3 — `GROUNDING.md` was a dead file

`GROUNDING.md` was the canonical location for HC1–HC6 hard constraints, but:

1. No agent loads it automatically (see findings table above).
2. The generated `CLAUDE.md` template imported only `@AGENTS.md`, not
   `@GROUNDING.md`.
3. `AGENTS.md` contained only a prose cross-reference ("see `GROUNDING.md`"),
   which no agent interprets as a load directive.

HC1–HC6 were therefore unreachable by all three agents.

---

## Decision

1. **Remove `GROUNDING.md`** as a separate artifact.  Inline HC1–HC6 directly
   into `AGENTS.md` (and `AGENTS.md.tmpl`) under a `## Security` section.
   Every agent that reads `AGENTS.md` now receives the hard constraints.

2. **Fix overlay detection paths** in `assess_repo.py` and
   `manifest_regression.py` to match the paths that `runtime_overlay.py`
   actually generates.

3. **Fix default-runtimes logic** in both `scaffold_manifests.main()` and
   `cmd_init.run()`:
   - First, call `diff_manifests._detect_runtimes(repo)` to find any overlays
     that already exist (for idempotent re-runs).
   - If none are found (greenfield repo), fall back to all three supported
     runtimes: `claude-code`, `codex-cli`, `copilot-cli`.
   - The `--mode refresh` path is intentionally **not** changed — refresh
     should only touch runtimes whose overlay files already exist.

4. **Update `governance.yml.tmpl`** to guard `AGENTS.md` (checking for HC
   marker removal) instead of `GROUNDING.md`.

---

## Consequences

### Positive

- All three agents now reliably receive HC1–HC6 on every session start.
- A plain `local-agent-harness init` (no flags) always produces a fully
  configured repo with overlays for all three runtimes.
- The readiness score correctly reflects which runtimes are configured.
- The `manifest_regression` suite validates HC markers against the file agents
  actually read.

### Negative / Trade-offs

- Existing repos that had a hand-maintained `GROUNDING.md` outside the harness
  will no longer have it regenerated.  The file should be deleted or its
  contents migrated into `AGENTS.md § Security`.
- `AGENTS.md` grows slightly longer.  Agents with tight context budgets should
  not be affected in practice; HC1–HC6 is fewer than 150 words.

---

## Files Changed (`1c77acb`)

| File | Change |
|---|---|
| `assets/GROUNDING.md.tmpl` | **Deleted** |
| `assets/AGENTS.md.tmpl` | HC1–HC6 inlined into `## Security`; header updated |
| `assets/ci/governance.yml.tmpl` | Guard `AGENTS.md` instead of `GROUNDING.md` |
| `core/agents_builder.py` | HC1–HC6 inlined; `GROUNDING.md` reads removed |
| `core/assess_repo.py` | Overlay paths fixed; `has_grounding` removed; `agent_config` score updated |
| `core/diff_manifests.py` | `GROUNDING.md` removed from TARGETS and STAGE_REQUIREMENTS |
| `core/manifest_regression.py` | Validate HC markers in `AGENTS.md`; correct overlay paths |
| `core/scaffold_manifests.py` | `GROUNDING.md` removed from `CORE_FILES`; default-runtimes fallback added |
| `cli/cmd_init.py` | Default-runtimes fallback added for non-interactive mode |
| `tests/**` | All GROUNDING.md references updated; `test_main_init_no_runtime_creates_all_overlays` added |

---

## Follow-up: Remove redundant "read AGENTS.md" prose from overlays

After the initial fixes, a further redundancy was identified: both
`.github/copilot-instructions.md` and `.codex/INSTRUCTIONS.md` contained
boilerplate telling the agent to read `AGENTS.md`.  Since both Copilot and
Codex already read `AGENTS.md` natively (see findings table), this prose was
noise at best and misleading at worst.

### What was removed

- **`.github/copilot-instructions.md`** (`_COPILOT_INSTRUCTIONS` / `copilot-cli.tmpl`):
  Removed "Primary instructions: AGENTS.md" section (the 5-bullet list
  summarising what is inside AGENTS.md).  The file now contains only
  Copilot-specific guidance and stop conditions.

- **`.codex/INSTRUCTIONS.md`** (`_CODEX_INSTRUCTIONS` / `codex.config.tmpl`):
  Replaced the placeholder "Codex reads AGENTS.md — edit that file instead"
  content with actual Codex-specific settings (approval mode, max turns,
  sandbox, transcript path) and stop conditions.

### Files changed (follow-up commit)

| File | Change |
|---|---|
| `core/runtime_overlay.py` | `_COPILOT_INSTRUCTIONS`: removed AGENTS.md pointer; `_CODEX_INSTRUCTIONS`: replaced placeholder with real Codex settings |
| `assets/runtime-overlays/copilot-cli.tmpl` | Synced to match `_COPILOT_INSTRUCTIONS` |
| `assets/runtime-overlays/codex.config.tmpl` | Synced to match `_CODEX_INSTRUCTIONS` (Markdown, not TOML) |
| `core/diff_manifests.py` | Drift anchors updated: codex `["Codex-specific settings", "Stop conditions"]`; copilot `["Copilot-specific guidance", "Stop conditions"]` |
