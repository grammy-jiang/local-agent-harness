# ADR-003 — DRY Consolidation: Conventions, PR Checklist, and Network-Egress Rule

**Date:** 2026-05-08  
**Status:** Accepted  

---

## Context

After the fixes documented in ADR-001 and ADR-002, a second-pass audit of a
freshly initialised repository (`local-agent-harness init`) revealed further
duplication across overlay files and the `AGENTS.md` spine.

The audit was performed by initialising an empty repository and comparing the
content of every generated config file line-by-line.

---

## Findings

### Finding 1 — Six Copilot-specific guidance bullets belong in `AGENTS.md`

`.github/copilot-instructions.md` (`_COPILOT_INSTRUCTIONS`) contained six
bullets under `## Copilot-specific guidance` that are universal development
rules, not Copilot-specific behaviour:

```markdown
- Always run the test suite and linter after every change.
- Never push directly to `main`; open a pull request.
- Keep pull requests small and focused; split unrelated changes into separate PRs.
- Include tests for every new function and every bug fix.
- When generating new code, match the style and patterns already in use.
- If a change requires a dependency update, call it out explicitly in the PR description.
```

These rules apply equally to Claude Code and Codex CLI sessions.  Placing them
only in the Copilot overlay means the other two agents never see them.  All
three agents read `AGENTS.md` (Copilot and Codex natively; Claude Code via
`@AGENTS.md` import), so `AGENTS.md` is the correct single home.

### Finding 2 — Three `general.instructions.md` bullets belong in `AGENTS.md`

`.github/instructions/general.instructions.md` (`_COPILOT_GENERAL_INSTRUCTIONS`)
had a "Specific rules" block:

```markdown
- Keep functions small and single-purpose.
- Add or update tests whenever you change behaviour.
- Prefer explicit error handling over silent failures.
```

These are code-style conventions shared by all agents. They belong in
`AGENTS.md § Conventions`, not in a Copilot path-scoped instruction file that
Claude Code and Codex never read.

### Finding 3 — Network-egress rule duplicates HC5

`.codex/INSTRUCTIONS.md` (`_CODEX_INSTRUCTIONS`) stated:

```markdown
- Sandbox: devcontainer; network egress denied by default.
```

`AGENTS.md § Security and Hard Constraints` already contains:

```markdown
- **HC5** — Network egress denied by default; allowlist documented in `AGENTS.md`.
```

Restating the same constraint in the Codex overlay creates two places to
maintain and risks silent drift if the wording ever diverges.

### Finding 4 — Claude Code out-of-scope stop condition duplicates `AGENTS.md`

`CLAUDE.md` (`_CLAUDE_MD`) contained two `### Stop conditions` bullets:

1. "If a tool call fails 3× consecutively → stop and ask the user." — genuinely
   Claude-specific (consecutive failure detection).
2. "If `accept-edits` mode writes outside the declared scope → abort and revert,
   then report what happened." — semantically identical to `AGENTS.md § Stop
   Conditions`: "Out-of-scope write: abort + revert + report."

The second bullet was a disguised duplicate.

### Finding 5 — Asset templates diverged from Python source (ADR-002 regression)

ADR-002 removed `## Stop conditions` from `_COPILOT_INSTRUCTIONS` and
`_CODEX_INSTRUCTIONS` in `runtime_overlay.py`, but the corresponding asset
templates (`copilot-cli.tmpl` and `codex.config.tmpl`) were **not updated**.
Both templates still contained the full `## Stop conditions` block:

```markdown
## Stop conditions

- Doom-loop: if the same tool is called 5× with similar args, stop and ask.
- Out-of-scope write: abort + revert + report.
```

Since the skill AI reads these templates for guidance, they were misleading
about the actual generated output.

---

## Decision

Apply DRY uniformly: every rule that is not genuinely runtime-specific belongs
in `AGENTS.md` and must appear **nowhere else**.

### 1. Add shared rules to `AGENTS.md` (Python + template)

Expand `AGENTS.md § Conventions` with:

```markdown
- Keep functions small and single-purpose.
- Match the existing code style and patterns already in use.
- Prefer explicit error handling over silent failures.
- Run the test suite and linter after every change.
- Never push directly to `main`; always open a pull request.
```

Expand `AGENTS.md § PR Checklist` with:

- Item 1: "add tests for every new function and every bug fix" (appended to
  "All tests pass").
- Item 4: "call out any dependency changes explicitly" (appended to PR
  description item).
- New item 5: "Keep PRs small and focused; split unrelated changes into separate
  PRs."
- Old item 5 renumbered to item 6.

### 2. Clear `_COPILOT_INSTRUCTIONS` of shared content

Replace the six bullets with a comment explaining they live in `AGENTS.md`.
Retain the `## Copilot-specific guidance` section heading (required by the
drift anchor) as a placeholder for future Copilot-only supplements.

### 3. Clear `_COPILOT_GENERAL_INSTRUCTIONS` of shared content

Remove "Specific rules" bullets. Keep the `applyTo: "**"` frontmatter and the
`AGENTS.md` reference line — the file's purpose is to ensure VS Code's Copilot
applies `AGENTS.md` conventions to every file context.

### 4. Remove the duplicate network-egress line from `_CODEX_INSTRUCTIONS`

Change:

```markdown
- Sandbox: devcontainer; network egress denied by default.
```

to:

```markdown
- Sandbox: devcontainer (see `.devcontainer/devcontainer.json`).
```

HC5 in `AGENTS.md` already covers the network policy.

### 5. Remove the duplicate stop condition from `_CLAUDE_MD`

Retain bullet 1 (consecutive failure — Claude-specific). Remove bullet 2
(out-of-scope write — duplicate of `AGENTS.md § Stop Conditions`). Replace with
a comment referencing the shared spine.

### 6. Sync asset templates with the Python source (regression fix)

Update all four templates to match their corresponding Python string constants:

- `copilot-cli.tmpl` — remove shared guidance bullets and the `## Stop
  conditions` block (matches `_COPILOT_INSTRUCTIONS`).
- `codex.config.tmpl` — update sandbox line and remove the `## Stop conditions`
  block (matches `_CODEX_INSTRUCTIONS`).
- `CLAUDE.md.tmpl` — remove duplicate stop condition (matches `_CLAUDE_MD`).
- `AGENTS.md.tmpl` — add new Conventions items, add `## Stop Conditions`
  section (previously missing from the template), expand PR Checklist.

---

## Consequences

### Positive

- **Single source of truth for all shared rules:** `AGENTS.md` is the only
  place where conventions, testing workflow, PR rules, and stop conditions live.
  Any future wording change requires one edit.
- **All three agents receive all shared rules:** Claude Code, Copilot, and Codex
  all read `AGENTS.md` — they all see the new Conventions and PR Checklist items.
- **Templates and Python source are back in sync:** the skill AI reads the same
  content as `local-agent-harness init` actually generates.
- **All 207 unit and integration tests pass** with no modifications to test
  files.

### Negative / Trade-offs

- Existing repos initialised before this change will have the old Copilot
  overlay (with the six bullets). Running `local-agent-harness check` will
  report `AGENTS.md` as **stale** (missing the new Conventions items) and
  `.github/copilot-instructions.md` as **stale** (anchor check now expects
  just the section heading with a comment). Running `local-agent-harness
  refresh --apply` will repair both.

---

## Files Changed

| File | Change |
|---|---|
| `src/.../core/agents_builder.py` | `build_agents_md()`: +5 Conventions items; PR Checklist items 1, 4 expanded; new item 5; item 5 renumbered to 6 |
| `src/.../core/runtime_overlay.py` | `_COPILOT_INSTRUCTIONS`: removed 6 shared bullets; `_COPILOT_GENERAL_INSTRUCTIONS`: removed 3 shared rules; `_CODEX_INSTRUCTIONS`: removed network-egress duplication; `_CLAUDE_MD`: removed duplicate out-of-scope stop condition |
| `assets/AGENTS.md.tmpl` | +5 Conventions items; added `## Stop Conditions` section (previously missing); PR Checklist expanded |
| `assets/runtime-overlays/copilot-cli.tmpl` | Removed 6 shared bullets and `## Stop conditions` block; section heading kept as placeholder |
| `assets/runtime-overlays/codex.config.tmpl` | Sandbox line updated; `## Stop conditions` block removed |
| `assets/runtime-overlays/CLAUDE.md.tmpl` | Duplicate out-of-scope stop condition removed |

---

## How Each Runtime Receives All Rules After This Change

| Rule category | `AGENTS.md` | `CLAUDE.md` | `copilot-instructions.md` | `.codex/INSTRUCTIONS.md` |
|---|---|---|---|---|
| HC1–HC6 hard constraints | ✅ | via `@AGENTS.md` | native read | native read |
| Stop Conditions (doom-loop, OOB write) | ✅ | via `@AGENTS.md` | native read | native read |
| Conventions (style, testing, PRs) | ✅ | via `@AGENTS.md` | native read | native read |
| PR Checklist (tests, small PRs, deps) | ✅ | via `@AGENTS.md` | native read | native read |
| Claude-specific stop (3× failure) | — | ✅ Claude-only | — | — |
| Codex approval mode / turn limit | — | — | — | ✅ Codex-only |
| Claude Plan mode / compaction | — | ✅ Claude-only | — | — |
