# Runtime Overlays

`AGENTS.md` is the portable behavioral spine — hard constraints, scope
boundary, stop conditions, PR checklist.  Each runtime adds an overlay that
either **imports** AGENTS.md (Claude Code) or **defers** to it (Codex,
Copilot).  Overlays may specialize but never relax AGENTS.md constraints.

## Key distinction: AGENTS.md vs. copilot-instructions.md

These two files serve **different purposes** for GitHub Copilot:

| File | Purpose | Scope |
|---|---|---|
| `AGENTS.md` | **Behavioral rules** — hard constraints, scope boundary, stop conditions, PR checklist | All AI agents (Copilot, Claude Code, Codex, Cursor, etc.) |
| `.github/copilot-instructions.md` | **Project context** — what the repo is, how to build/test/validate, project layout, tech stack | All Copilot features: Chat, Code Review, Cloud Agent |

`AGENTS.md` tells the agent *how to behave*.
`copilot-instructions.md` tells Copilot *what the project is*.

Do not duplicate content between them:
- Conventions, security constraints, scope, and PR checklist → **AGENTS.md only**
- Repository overview, build commands, project layout, tech stack → **copilot-instructions.md only**

Reference: `references/copilot-instructions-standard.md`

## Claude Code — `CLAUDE.md`

File: `CLAUDE.md` (repo root)

- Uses `@AGENTS.md` import syntax to inline the behavioral spine.
- Adds Claude Code-only settings: plan mode triggers, compaction policy,
  3× consecutive-fail stop condition.
- Tool permissions enforced by `.claude/settings.json` (authoritative).

## OpenAI Codex CLI — `.codex/INSTRUCTIONS.md`

File: `.codex/INSTRUCTIONS.md`

- Codex reads `AGENTS.md` natively; this file adds only Codex-specific
  supplements (approval mode, max turns, sandbox pointer, log path).
- `approval_mode = "suggest"` is the recommended default.
- Sandbox = devcontainer; network deny by default.

## GitHub Copilot — `.github/copilot-instructions.md`

File: `.github/copilot-instructions.md`

- Applied to **all** Copilot requests in the repository context: Chat,
  Code Review, and Cloud Agent.
- Contains project context (overview, layout, build/test commands, tech
  stack) so Copilot can answer questions and review code without exploring
  the repo from scratch each time.
- Behavioral rules are **not** repeated here — Copilot reads `AGENTS.md`
  natively for agent tasks.
- The `## Copilot-specific guidance` section is the designated place for
  any Copilot-only supplements (e.g., code review focus areas).

## Cross-runtime contract

1. All overlays must not relax any hard constraint from `AGENTS.md`.
2. All overlays must respect the path allowlist from `AGENTS.md`.
3. All overlays must enable session logging into `.agent/logs/`.
4. `governance.yml` must reject overlay diffs that remove HCs.
