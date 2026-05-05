# Memory Governance

Source: engineering guide §8 + research report §6.

## Three tiers

| Tier | Lifetime | Storage | Promotion gate |
|---|---|---|---|
| Session | one run | `.agent/logs/<run>.jsonl` (append-only) | n/a |
| Project | repo lifetime | `.agent/memory/*.json` (schema-grounded) | passes manifest regression + human review |
| Skill library | cross-repo | `.skills/*.SKILL.md` | causal evidence + held-out eval |

## Schema-grounded memory (S2+)

Do not store prose memory. Store records with explicit schemas:

```json
{
  "id": "mem-2026-05-05-001",
  "kind": "fact|state|relation|absence|decision",
  "subject": "<entity>",
  "predicate": "<relation>",
  "object": "<value or entity>",
  "evidence": ["<file:line>", "<commit>"],
  "confidence": 0.0,
  "created_at": "<iso8601>",
  "expires_at": "<iso8601 | null>"
}
```

## Promotion rules

1. A memory is **causally useful** — tied to an observable outcome
   (test pass, bug fixed, regression caught).
2. Promotion requires a held-out eval (S3) or at least one verified replay
   (S2).
3. Demotion is automatic on contradiction.
4. Read filters apply per task: not every memory is loaded every session.

## Anti-patterns
- Free-form journal memories.
- Memory as a substitute for tests.
- Promoting on a single success.
- Loading the entire memory store every turn.
