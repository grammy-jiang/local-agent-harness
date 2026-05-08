# ADR-002 — DRY Overlay Deduplication: Stop Conditions and Secrets Rule

**Date:** 2026-05-08  
**Status:** Accepted  

---

## Context

After the fixes documented in ADR-001, the harness generated three runtime
overlay files — `CLAUDE.md`, `.github/copilot-instructions.md`, and
`.codex/INSTRUCTIONS.md` — each containing instructions for their respective
AI coding agents.

A review of the generated content across a freshly initialised repository
revealed two categories of duplication:

### Duplication 1 — Identical `## Stop conditions` in two overlays

Both `.github/copilot-instructions.md` and `.codex/INSTRUCTIONS.md` contained
an **identical** `## Stop conditions` block:

```markdown
## Stop conditions

- Doom-loop: if the same tool is called 5× with similar args, stop and ask.
- Out-of-scope write: abort + revert + report.
```

These rules govern agent behaviour that is universal — not specific to either
Copilot or Codex. Having them duplicated across two files means:

- Any future edit must be made in two places (brittle).
- The copy in one file can silently drift from the copy in the other.
- Both Copilot and Codex already read `AGENTS.md` natively (see ADR-001
  findings table), so any shared behavioural rule belongs in `AGENTS.md`.

Note: `CLAUDE.md` has a different, Claude-specific `### Stop conditions` block
(tool call fails 3×, `accept-edits` scope violations). Those rules are
genuinely Claude-specific and were not touched.

### Duplication 2 — Secrets rule in `general.instructions.md` shadows HC1

`.github/instructions/general.instructions.md` contained:

```markdown
- Do not commit secrets, credentials, or environment-variable values.
```

This rule is semantically identical to HC1 in `AGENTS.md`:

```markdown
- **HC1** — No plaintext secrets in repository, prompts, logs, or commits.
```

Since GitHub Copilot reads `AGENTS.md` natively, every Copilot session already
receives HC1 directly. The duplicate rule in `general.instructions.md` adds
noise, creates a second place to maintain, and could diverge from HC1 in
future edits.

---

## Decision

Apply the DRY principle uniformly across all overlay templates.

### 1. Move shared stop conditions to `AGENTS.md`

Add a `## Stop Conditions` section to the `AGENTS.md` static template in
`agents_builder.py`:

```markdown
## Stop Conditions

Applies to all runtimes:

- Doom-loop: if the same tool is called 5× with similar args, stop and ask.
- Out-of-scope write: abort + revert + report.
```

Every agent that reads `AGENTS.md` (Copilot natively, Codex natively, Claude
Code via `@AGENTS.md` import) now receives these rules exactly once.

### 2. Remove `## Stop conditions` from the two overlay templates

Replace the duplicated block in `_COPILOT_INSTRUCTIONS` and
`_CODEX_INSTRUCTIONS` (both in `runtime_overlay.py`) with a comment:

```markdown
<!-- Stop conditions are defined in AGENTS.md (shared spine). -->
```

`CLAUDE.md`'s `### Stop conditions` is retained as-is because it documents
Claude-specific failure modes (consecutive tool-call retries, `accept-edits`
scope violations) that are not covered by the shared rules.

### 3. Remove the duplicate secrets rule from `general.instructions.md`

Remove "Do not commit secrets, credentials, or environment-variable values."
from `_COPILOT_GENERAL_INSTRUCTIONS` and replace with a comment referencing HC1.

### 4. Update drift anchors in `diff_manifests.py`

- Remove `"Stop conditions"` from the required anchors for `codex-cli` and
  `copilot-cli` overlays (the section no longer exists in those files).
- Add `"Stop Conditions"` to the required anchors for `AGENTS.md` so drift
  detection enforces the new section's presence.

---

## Consequences

### Positive

- **Single source of truth:** shared stop conditions live in `AGENTS.md` only.
  Any future wording change requires one edit.
- **No redundancy:** `general.instructions.md` no longer restates HC1.
- **Drift detection is consistent:** `diff_manifests` checks that
  `AGENTS.md` contains `Stop Conditions`; overlay staleness checks no longer
  look for a section that does not exist.
- **All 207 unit and integration tests pass** with no modifications to test
  files (no test asserted the presence of the removed content).

### Negative / Trade-offs

- Existing repos that were initialised with the old templates will have
  `## Stop conditions` in their overlay files but not in `AGENTS.md`. Running
  `local-agent-harness check` will report `AGENTS.md` as **stale** (missing
  `Stop Conditions` anchor). Running `local-agent-harness refresh --apply`
  will update `AGENTS.md` and leave the now-harmless comment in the overlays.

---

## Files Changed

| File | Change |
|---|---|
| `src/local_agent_harness/core/agents_builder.py` | Added `## Stop Conditions` section to `build_agents_md()` static block |
| `src/local_agent_harness/core/runtime_overlay.py` | Removed `## Stop conditions` from `_COPILOT_INSTRUCTIONS` and `_CODEX_INSTRUCTIONS`; removed duplicate secrets rule from `_COPILOT_GENERAL_INSTRUCTIONS` |
| `src/local_agent_harness/core/diff_manifests.py` | Removed `"Stop conditions"` from `codex-cli` and `copilot-cli` overlay anchors; added `"Stop Conditions"` to `AGENTS.md` required anchors |

---

## How Each Runtime Now Receives the Stop Conditions

| Runtime | Config file loaded | How stop conditions arrive |
|---|---|---|
| **Claude Code** | `CLAUDE.md` → `@AGENTS.md` import | Via `AGENTS.md § Stop Conditions` (inlined at startup) |
| **GitHub Copilot** | `AGENTS.md` (native) + `copilot-instructions.md` | Via `AGENTS.md § Stop Conditions` (native read) |
| **Codex CLI** | `AGENTS.md` (native) + `.codex/INSTRUCTIONS.md` | Via `AGENTS.md § Stop Conditions` (native read) |

The runtime-specific overlays retain only content that is genuinely
runtime-specific and cannot live in `AGENTS.md`.
