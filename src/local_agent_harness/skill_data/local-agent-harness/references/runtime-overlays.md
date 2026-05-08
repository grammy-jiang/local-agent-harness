# Runtime Overlays

`AGENTS.md` + `GROUNDING.md` is the portable spine. Each runtime adds an
overlay that **specializes** behavior; overlays may not relax `GROUNDING.md`.

## Claude Code — `CLAUDE.md`
- Plan mode for non-trivial work.
- Skills lazy-loaded from `.skills/`.
- Compaction at 70 % context.

## OpenAI Codex CLI — `.codex/config`
- `approval_mode = "suggest"` is the recommended default.
- Sandbox = devcontainer; network deny by default.
- `paths.write_allow` mirrors `AGENTS.md` scope.

## GitHub Copilot CLI — `.github/copilot-cli.md`
- Confirm before destructive actions.
- Sandbox required for untrusted repos.
- Doom-loop detection: same tool 5× ⇒ stop.

## Cross-runtime contract
1. All overlays must reference `AGENTS.md` and `GROUNDING.md` by path.
2. All overlays must respect the path allowlist.
3. All overlays must enable session logging into `.agent/logs/`.
4. `governance.yml` must reject overlay diffs that remove HCs.
