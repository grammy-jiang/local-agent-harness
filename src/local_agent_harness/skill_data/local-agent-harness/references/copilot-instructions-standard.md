# GitHub Copilot — Repository Custom Instructions Standard

> Source: https://docs.github.com/en/copilot/how-tos/copilot-on-github/
> customize-copilot/add-custom-instructions/add-repository-instructions
>
> Bundled at package build time so no runtime fetch is needed.
> Review periodically against the live documentation.

## What is `.github/copilot-instructions.md`?

Repository-wide custom instructions that provide GitHub Copilot with
**project-specific context and guidance**.  These instructions are
automatically added to every Copilot request made in the context of the
repository.

They are used by:
- **Copilot Chat** (github.com/copilot, IDE chat panels)
- **Copilot code review** (pull request review suggestions)
- **Copilot cloud agent** (autonomous coding agent on GitHub)

## What belongs here — vs. AGENTS.md

| Content | File |
|---|---|
| Repository overview (what the project does) | `copilot-instructions.md` |
| Tech stack (languages, frameworks, runtimes) | `copilot-instructions.md` |
| Project layout (where key files live) | `copilot-instructions.md` |
| Build, test, lint commands + sequences | `copilot-instructions.md` |
| CI/CD validation steps | `copilot-instructions.md` |
| Hard constraints (HC1–HC6) | **AGENTS.md** |
| Scope boundary | **AGENTS.md** |
| Stop conditions | **AGENTS.md** |
| PR checklist | **AGENTS.md** |
| Commit/branch conventions | **AGENTS.md** |

Do not duplicate content between the two files.

## Recommended sections (from GitHub docs)

```markdown
# Repository Overview

Brief description of what the repository does.

## Tech Stack

Languages, frameworks, target runtimes, and versions in use.

## Project Layout

Key directories and files with brief annotations.

## Build & Validation Commands

For each of: bootstrap, build, test, run, lint — the exact command
sequence, validated to work, with any ordering dependencies noted.
Include environment setup steps that are required but not obvious.

## Copilot-specific guidance

Copilot-only supplements such as code review focus areas,
response preferences, or path-specific notes.
```

## Key rules from the GitHub docs

1. **Instructions length:** Keep under ~2 pages (≈ 8 000 tokens).
   Longer instructions are truncated.

2. **Not task-specific:** Instructions must be general — they apply to
   *all* requests in the repo, not to a specific task.

3. **Validated commands:** Document commands you have actually run and
   confirmed work.  Note ordering, preconditions, and timing for slow
   commands.

4. **Priority order:** Personal instructions > repository instructions >
   organization instructions.  All relevant sets are provided to Copilot.

5. **Path-specific instructions:** For per-file-type guidance, use
   `.github/instructions/NAME.instructions.md` files with a frontmatter
   `applyTo:` glob (supported by code review and cloud agent only).

6. **Agent instructions vs. context instructions:**
   - `AGENTS.md` = behavioral rules for AI agents (any runtime).
   - `copilot-instructions.md` = project context for all Copilot features.

## Relationship to AGENTS.md

GitHub Copilot reads `AGENTS.md` natively for agentic tasks (cloud agent,
autonomous coding).  The `copilot-instructions.md` file provides *additional*
context that applies to non-agent Copilot features (Chat, Code Review) where
`AGENTS.md` is not automatically loaded.

The two files are **complementary, not redundant**:
- `AGENTS.md` → agent behavior (what the agent may/must do)
- `copilot-instructions.md` → project knowledge (what the project is)
