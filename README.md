# local-agent-harness

Maturity-aware harness manager for local AI coding agents (Claude Code,
Codex CLI, GitHub Copilot CLI, Cursor).

`local-agent-harness` makes a repository ready for AI-agent-assisted
development from two directions:

1. **Make the agent work better.** Generate `AGENTS.md` / `GROUNDING.md`,
   per-runtime overlays (`CLAUDE.md`, `.codex/config`,
   `.github/copilot-cli.md`, `.cursor/rules`), tool DAGs, permission
   ladders, governed memory, and cost/context budgets.
2. **Make the repository ready.** Render sandbox/devcontainer,
   `.pre-commit-config.yaml`, verify CI, governance CI, secrets/SAST/dep
   scans, and a machine-readable AI-readiness score.

The harness *evolves with the repo*. A blank S0 skeleton receives a
minimal kit; a mature S3 codebase gets the full set of governance gates.

## Install

```bash
pipx install local-agent-harness
local-agent-harness setup        # install the bundled skill into ~/.claude, ~/.copilot, ~/.codex
```

`setup` only installs into agent skill roots whose parent directory
already exists. Override with `--target PATH` (repeatable) to install
into project-local locations like `.github/skills/`.

## Usage

```bash
local-agent-harness assess                 # detect maturity stage + AI-readiness score
local-agent-harness check                  # audit manifests for drift (read-only)
local-agent-harness init  --runtime claude-code --runtime copilot-cli
local-agent-harness refresh --apply        # rewrite stale manifests (backups written)
local-agent-harness report --out .agent/readiness.md
local-agent-harness validate               # regression + redaction smoke checks
```

Three modes:

| Mode      | Writes? | Use when |
|-----------|---------|----------|
| `check`   | no      | Audit-only — CI gate or quick diagnosis. |
| `init`    | yes     | Render *missing* manifests; never overwrites. |
| `refresh` | yes (with `--apply`) | Back up + rewrite *stale or relaxed* manifests. |

## Stages (S0 → S3)

| Stage | Repo signal                                  | Default kit                           |
|-------|----------------------------------------------|---------------------------------------|
| S0    | empty / no source / no tests / no CI         | AGENTS.md, GROUNDING.md, plan.md      |
| S1    | source + tests OR CI                         | + pre-commit, devcontainer, verify CI |
| S2    | source + tests + CI                          | + governance CI, redaction smoke      |
| S3    | + tags/releases                              | + readiness gate, no-regression check |

## License

MIT
