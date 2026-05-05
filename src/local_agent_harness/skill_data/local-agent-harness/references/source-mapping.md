# Source Mapping

Each recommendation in this skill traces back to the two authoritative
documents in the research vault. Use Obsidian wiki-links inside the vault.

## Primary sources
- [[harness-engineering-for-local-coding-agents-engineering-guide]] — the
  operational guide; most §3–§12 recommendations map here.
- [[harness-engineering-for-local-coding-agents-research-report]] — the
  evidence base; 13-layer architecture and confidence annotations.
- [[harness-engineering-of-ai-agents-research-report]] — broad 120-paper
  synthesis; the upstream of both local docs.

## Mapping table

| Skill artifact | Source section |
|---|---|
| `references/stages.md` | guide §3, §12 (roadmap) |
| `references/ai-readiness-rubric.md` | guide §7.5 (AI-readiness score) |
| `references/tool-dag-patterns.md` | guide §5 |
| `references/memory-governance.md` | guide §8; report §6 |
| `references/verify-gate-catalog.md` | guide §6 |
| `references/runtime-overlays.md` | guide §4 |
| `references/manifest-anti-patterns.md` | guide §4.6 |
| `assets/GROUNDING.md.tmpl` | guide §4.2, Appendix A.1 |
| `assets/AGENTS.md.tmpl` | guide §4.3, Appendix A.2 |
| `assets/plan.md.tmpl` | guide §4.5, Appendix A.4 |
| `assets/ci/governance.yml.tmpl` | guide §4 (monotonic policy), §11 |
| `scripts/manifest_regression.py` | guide §4.7 (TDAD) |
| `scripts/redaction_smoke.py` | guide §1.1 (Safe), §11.3 |
| `scripts/readiness_report.py` | guide §7.5 |

## Evidence anchors used
- ALARA (tool-set scaling) → tool DAG enforcement.
- GTA-2 (harness as independent variable) → eval discipline.
- AER non-identifiability → telemetry-first.
- SAFE / SAVER / SEVerA → verification before commit.
- TDAD → manifest regression suite.
- ObjectGraph (.og) → optional token-saving manifest encoding (S3).
- FlashRT → adversarial sweep at S3.
- Schema-Grounded Memory → memory tier 2.
