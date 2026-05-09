# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.11] — 2026-05-09

### Fixed
- `runtime_overlay.py`: removed duplicate `.gitignore` managed-section
  warning from `_build_copilot_instructions` Notes section — the rule
  already lives in AGENTS.md `§ Conventions` (the authoritative location
  for behavioral constraints).

## [0.3.10] — 2026-05-09

### Fixed
- `runtime_overlay.py` / `copilot-cli.tmpl`: removed project build/test/lint
  commands from `copilot-instructions.md` (AGENTS.md is the authoritative
  source all runtimes read natively); only harness-specific validation commands
  remain in the Copilot file.
- `agents_builder.py`: `from __future__ import annotations` convention is now
  only added to AGENTS.md when Python is detected in the stack; non-Python
  repos no longer receive a Python-specific convention.
- `agents_builder.py` / `AGENTS.md.tmpl`: synced the programmatic static block
  with the template — richer HC3–HC6 descriptions, data classification table
  (Green/Amber/Red), and `.gitignore` managed-section note all now match.

## [0.3.9] — 2026-05-09

### Fixed
- `AGENTS.md.tmpl`: added `.gitignore` convention ("do not hand-edit the
  harness-managed section") — a behavioral constraint that belongs in the
  agent spine, not in project-context files.
- `copilot-cli.tmpl`: removed the same rule from the Notes section
  (was duplicated in the wrong file).

## [0.3.8] — 2026-05-09

### Changed
- `SKILL.md` Step 2: skill now probes `~/.claude`, `~/.copilot`, and
  `~/.codex` to detect installed AI agents before asking the user which
  runtimes to target. Zero dirs → fall back to repo detection; one dir →
  use silently; two or more → ask with all detected as default.
- `SKILL.md`: updated Example 1 to show machine-detection flow; added
  Example 5 (all three agents installed) illustrating the multi-agent
  confirmation prompt.

## [0.3.7] — 2026-05-09

### Fixed
- `agents_builder.py` / `AGENTS.md.tmpl`: removed `local-agent-harness
  validate` command from the Security section — build/validation commands
  belong in `copilot-instructions.md`, not the behavioral spine. The rule
  now states the obligation only, pointing to the commands file.
- `agents_builder.py` / `AGENTS.md.tmpl`: made AGENTS.md fully
  runtime-agnostic — removed the `copilot-instructions.md` pointer from
  the Security footer (AGENTS.md must not name a specific runtime's config
  file); changed `Applies to all runtimes` → `Applies to all agents` in
  the Stop Conditions section.

## [0.3.6] — 2026-05-09

### Added
- `runtime_overlay.py`: `_build_copilot_instructions()` now generates
  `.github/copilot-instructions.md` dynamically with project context
  (overview, repo layout, detected tech stack, build/test/lint commands,
  and harness validation commands) instead of a static placeholder.
- `references/copilot-instructions-standard.md`: new reference document
  explaining the AGENTS.md vs copilot-instructions.md distinction per
  GitHub Copilot docs.

### Fixed
- `references/runtime-overlays.md`: corrected wrong file paths
  (`.github/copilot-cli.md` → `.github/copilot-instructions.md`;
  `.codex/config` → `.codex/INSTRUCTIONS.md`); added table explaining
  the AGENTS.md / copilot-instructions.md split.
- `copilot-cli.tmpl`: updated static refresh template to match the new
  section structure.
- `SKILL.md`: added reference to `copilot-instructions-standard.md`.

## [0.3.5] — 2026-05-08

### Fixed
- `agents_builder.py`: removed duplicate `Network | denied by default` row
  from the Scope Boundary table; HC4 in the Security section is the
  authoritative declaration.
- `runtime_overlay.py` (`_CLAUDE_MD`): replaced inline deny list with a
  pointer to `.claude/settings.json` (the machine-enforceable source of
  truth).
- `runtime_overlay.py` (`render_copilot`): stopped generating
  `.github/instructions/general.instructions.md`; its sole content
  ("follow AGENTS.md") is redundant since Copilot reads `AGENTS.md`
  natively.
- Asset templates (`AGENTS.md.tmpl`, `CLAUDE.md.tmpl`) synced to match.

## [0.3.4] — 2026-05-08

### Changed
- `agents_builder.py`: expanded `## Conventions` with five shared rules
  (small functions, match style, explicit error handling, run tests, no
  direct pushes to `main`) and extended `## PR Checklist` (tests for every
  new fn/bug fix; call out dependency changes; keep PRs small).
- `runtime_overlay.py`: removed six shared bullets from
  `_COPILOT_INSTRUCTIONS`, three shared rules from
  `_COPILOT_GENERAL_INSTRUCTIONS`, duplicate HC5 line from
  `_CODEX_INSTRUCTIONS`, and the duplicate out-of-scope stop condition from
  `_CLAUDE_MD` — all now live in the AGENTS.md spine.
- Asset templates (`AGENTS.md.tmpl`, `copilot-cli.tmpl`,
  `codex.config.tmpl`, `CLAUDE.md.tmpl`) synced to match Python source
  (ADR-002 regression fix).

### Added
- ADR-003: documents the DRY consolidation of shared conventions and PR
  checklist items.

## [0.3.3] — 2026-05-08

### Changed
- `agents_builder.build_agents_md()`: added `## Stop Conditions` section to
  the shared AGENTS.md spine so every runtime picks it up automatically.
- `runtime_overlay.py`: removed duplicate `## Stop conditions` blocks from
  `_COPILOT_INSTRUCTIONS` and `_CODEX_INSTRUCTIONS`; replaced with a
  comment pointing to the AGENTS.md spine.
- `diff_manifests.py`: added `"Stop Conditions"` to AGENTS.md drift anchors;
  removed `"Stop conditions"` from Copilot and Codex overlay anchor lists.

### Added
- ADR-002: documents the DRY deduplication decision.

## [0.3.2] — 2026-05-08

### Fixed
- Copilot overlay (`_COPILOT_INSTRUCTIONS` / `copilot-cli.tmpl`): dropped
  the redundant "Primary instructions: AGENTS.md" block; Copilot reads
  `AGENTS.md` natively, so only Copilot-specific guidance is kept.
- Codex overlay (`_CODEX_INSTRUCTIONS` / `codex.config.tmpl`): replaced
  the placeholder "edit AGENTS.md instead" stub with real Codex runtime
  settings (`approval_mode`, `max_turns`, sandbox, transcripts path).
- `diff_manifests.py`: updated drift anchors to match new overlay content.
- `AGENTS.md` (repo's own): rewritten with `## Testing`, `## Security`
  (HC1–HC6), and `## PR Checklist` sections; removed stale placeholders.
- Removed unused `_assets_dir` import from `runtime_overlay.py`.
- ADR-001 updated with follow-up cleanup notes.

## [0.3.1] — 2026-05-08

### Fixed
- SKILL.md frontmatter `description` no longer mentions the removed
  `GROUNDING.md`; updated to reflect HC1–HC6 inlined into `AGENTS.md`.

## [0.3.0] — 2026-05-08

### Removed
- **`GROUNDING.md`** is no longer generated or required. Hard constraints
  (HC1–HC6) are now inlined directly into `AGENTS.md` so every AI agent
  that reads `AGENTS.md` picks them up without a separate file.

### Fixed
- `assess_repo.py` overlay-detection paths corrected:
  `.codex/config` → `.codex/INSTRUCTIONS.md` and
  `.github/copilot-cli.md` → `.github/copilot-instructions.md`.
- `cmd_init` / `scaffold_manifests.main()` now auto-detect existing overlay
  runtimes when `--runtime` is not supplied; fall back to all three
  (`claude-code`, `codex-cli`, `copilot-cli`) for greenfield repos.
- `manifest_regression.py` now verifies HC\* and secrets wording in
  `AGENTS.md` instead of the removed `GROUNDING.md`.
- `governance.yml.tmpl` updated to guard `AGENTS.md` instead of `GROUNDING.md`.

### Added
- ADR-001: documents the agent instruction-file discovery findings and the
  resulting path corrections.

## [0.2.1] — 2026-05-08

### Fixed
- `__version__` now reads from `importlib.metadata` so `pyproject.toml` is
  the single source of truth; the hardcoded stale string is gone.

## [0.2.0] — 2026-05-08

### Removed
- **Cursor runtime** dropped from all supported runtimes. `render_cursor`,
  `OVERLAYS["cursor"]`, and `.cursor/rules` are no longer generated or
  audited. Remove `cursor` from any `--runtime` invocations.
- GitLab CI (`.gitlab-ci.yml`) and CircleCI (`.circleci/config.yml`) no
  longer count as recognised CI in the maturity assessment — GitHub Actions
  (`.github/workflows/`) is now the only supported CI provider.

### Changed
- `pyproject.toml` description and keywords updated to drop Cursor / add
  GitHub Actions.
- All skill data docs and SKILL.md updated to remove Cursor references.

## [0.1.0] — Unreleased

### Added
- Initial release: package the `local-agent-harness` skill as a
  pipx-installable Python distribution.
- CLI: `setup`, `assess`, `check`, `init`, `refresh`, `report`,
  `validate`, `version`.
- Bundled skill data (`SKILL.md`, `assets/`, `references/`) discoverable
  via `importlib.resources`.
- `setup` auto-detects which agent skill roots exist
  (`~/.claude/skills`, `~/.copilot/skills`, `~/.codex/skills`) and only
  installs into those; `--target PATH` overrides.

### Publish notes

To publish to PyPI:

1. Configure a trusted publisher on PyPI for this repo and the
   `publish.yml` workflow (one-time): see
   <https://docs.pypi.org/trusted-publishers/>.
2. `git tag v0.1.0 && git push origin v0.1.0`.
3. Cut a GitHub release for that tag → `publish.yml` runs and uploads.

For a manual one-off publish:

```bash
uv build
uv publish    # uses UV_PUBLISH_TOKEN or trusted publisher
```
