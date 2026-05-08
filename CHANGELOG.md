# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
