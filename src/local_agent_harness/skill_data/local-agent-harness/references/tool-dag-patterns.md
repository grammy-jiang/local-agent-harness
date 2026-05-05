# Tool DAG Patterns

Source: `harness-engineering-for-local-coding-agents-engineering-guide.md`
§5.3.

## Principle

Structural least privilege. Remove capabilities a node does not need; do not
rely on the model to refrain.

## Node types

| Node | Reads | Writes | Executes | Examples |
|---|---|---|---|---|
| Plan | yes | no | no | issue triage, design, refactor scoping |
| Search | yes | no | no | `rg`, `glob`, symbol/semantic search |
| Edit | yes | yes (allowlisted) | no | patches, `str_replace_editor` |
| Execute | yes | no | yes (allowlisted) | tests, formatters, build |
| Approve | n/a | n/a | n/a | human gate before destructive ops |

## DAG rules

1. Plan never holds Edit or Execute capability.
2. Edit never holds Execute capability.
3. Execute is allowlisted to a finite command set; destructive commands
   require an Approve hop.
4. Subagents inherit ⊆ parent capability (monotonic).
5. The Tool DAG is recorded in `.agent/policies/tool-dag.md` and verified by
   `manifest_regression.py`.

## Stage applicability

- S0: optional (single-node Plan only).
- S1: split Plan + Edit + Execute.
- S2: full DAG with Approve hop and per-tool allowlist.
- S3: + lifecycle hooks (pre/post tool) and lazy-load.
