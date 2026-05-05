# Manifest Anti-Patterns

Source: engineering guide §4.6.

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| "Be careful" as the only policy | Not enforceable, not auditable | Replace with checks and gates. |
| Runtime-only policy (no `AGENTS.md`) | Non-portable across CLIs | Put shared policy in `AGENTS.md`; overlays only specialize. |
| Secrets embedded in manifests | Repeated model exposure | Use variable names + redaction rules. |
| Redirect-only manifests ("see wiki") | Agent cannot resolve offline | Vendor required policy text. |
| Monolithic mega-skill files | Tool/context bloat | Split by task; expose only selected skills. |
| `GROUNDING.md` edited inline by agent | Hard constraints can erode silently | Require dedicated PR + governance gate. |
| Overlay relaxes a hard constraint | Defeats monotonic composition | `governance.yml` must reject the diff. |
| Memory as freeform journal | Cannot be queried, cannot expire | Schema-grounded records (see `memory-governance.md`). |
| No `plan.md` before edits | No DryRUN, no decision audit | Make `plan.md` a precondition for Edit nodes. |
| Tool DAG with Plan→Execute edge | Plan node escalates capability | Forbid in `tool-dag-patterns.md`. |
