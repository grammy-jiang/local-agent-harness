# agents.md Standard Reference

> Source: https://agents.md/ — bundled at package build time so no
> runtime download is needed.  Review periodically against the live spec.

## What is AGENTS.md?

AGENTS.md is a simple, open format for guiding AI coding agents.
Think of it as a **README for agents**: a dedicated, predictable place
to provide the context and instructions that help AI coding agents work
on your project.

AGENTS.md complements README.md by containing the extra, sometimes
detailed context coding agents need — build steps, tests, and
conventions that might clutter a README or aren't relevant to human
contributors.

It is stewarded by the [Agentic AI Foundation](https://aaif.io) under
the Linux Foundation and is used by over 60 000 open-source projects.

## Supported Agents (as of 2025)

- OpenAI Codex / ChatGPT
- GitHub Copilot CLI
- Claude Code (Anthropic)
- Cursor
- Amp (Sourcegraph)
- Jules (Google)
- Factory
- Aider (`read: AGENTS.md` in `.aider.conf.yml`)
- Gemini CLI (`context.fileName` in `.gemini/settings.json`)

## Format

Plain Markdown.  No required fields, no schema.

### Recommended sections

```markdown
# AGENTS.md

## Setup
- Install deps: `pnpm install`
- Start dev server: `pnpm dev`

## Testing
- Run full suite: `pnpm test`
- Run single test: `pnpm vitest run -t "<test name>"`
- Fix all errors before merging.

## Code style
- TypeScript strict mode
- Single quotes, no semicolons
- Functional patterns preferred

## PR instructions
- Title format: `[package] Title`
- Always run lint + tests before committing.
```

### Key rules

1. **Closest file wins.** In a monorepo, the AGENTS.md nearest to the
   edited file takes precedence.  Explicit user chat prompts override
   all AGENTS.md files.
2. **Agents execute commands.** If you list build/test commands, the
   agent will attempt to run them and fix failures before finishing.
3. **Living document.** Update it as the project evolves.

## FAQ

**Are there required fields?** No. Use any headings you like.

**What if instructions conflict?** Closest AGENTS.md to the edited
file wins; user prompt overrides everything.

**How do I migrate AGENT.md → AGENTS.md?**
```bash
mv AGENT.md AGENTS.md && ln -s AGENTS.md AGENT.md
```

**How do I configure Aider?**
```yaml
# .aider.conf.yml
read: AGENTS.md
```

**How do I configure Gemini CLI?**
```json
{ "context": { "fileName": "AGENTS.md" } }
```
