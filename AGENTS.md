# AGENTS

Project-scoped policy for AI coding agents working in this repository.
Specializes — never relaxes — the constraints in `GROUNDING.md`.

## Runtime

| Field | Value |
|---|---|
| Primary CLI | `<claude-code | codex-cli | copilot-cli | cursor>` |
| CLI version | `<x.y.z>` |
| Model family | `<e.g. claude-opus-4.7>` |
| Default permission mode | `<read-only | plan | default | accept-edits>` |
| Sandbox | `<devcontainer | docker | host>` |
| Maturity stage | `<S0 | S1 | S2 | S3>` |

## Success Definition

A task is complete when:

1. All tests in `<test-runner>` pass.
2. Linter and formatter are clean.
3. No new secrets, SAST, or dependency findings.
4. PR description summarizes the change, risks, and verification evidence.
5. `plan.md` decisions log is appended for every non-trivial decision.

## Assessment Rubric

Reviewers grade on:

- Correctness — explicit tests cover the change.
- Maintainability — dependency, responsibility, reuse, testability,
  side-effect isolation.
- Tests — added or updated; flaky tests are not allowed.
- Security — no widened attack surface; least-privilege preserved.
- Cost — within the budget below.
- Documentation — public API, README, and decision logs updated.

## Scope Boundary

| Action | Allowed scope |
|---|---|
| Read | entire repo |
| Edit | `src/`, `tests/`, `docs/`, `.agent/plan.md` |
| Create | within edit scope |
| Delete | requires human approval |
| Execute | commands listed in `.agent/policies/commands.allowlist` |
| Network | denied by default; see `policies/network.allowlist` |

## Data Classification

Inherits `GROUNDING.md`. This project additionally treats:

- `<path/to/sensitive>` as Red.
- `<path/to/internal>` as Amber.

## Quality Gate (merge-blocking)

- CI workflow `verify.yml` green.
- CI workflow `governance.yml` green.
- Manifest regression suite green.
- One human reviewer approval.
- Branch protection enforced on `main`.

## Cost and Context Policy

| Budget | Value |
|---|---|
| Max turns per session | `<e.g. 40>` |
| Token cap (input+output) | `<e.g. 200k>` |
| Wall-clock cap | `<e.g. 60 min>` |
| Command cap | `<e.g. 100>` |
| Compaction trigger | `<e.g. 70 % of cap>` |

## PR Evidence

Every agent-authored PR must include:

- Link to the session JSONL under `.agent/logs/`.
- The `plan.md` rendered at submit time.
- DryRUN predictions (if applicable).
- Verification output (`verify.yml` summary).
- Readiness delta (`.agent/eval/readiness.md` before/after).
