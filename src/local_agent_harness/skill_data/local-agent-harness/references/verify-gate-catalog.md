# Verify-Before-Commit Gate Catalog

Source: engineering guide §6.

Apply gates in order. Earlier gates fail fast.

| # | Gate | Stage | Tool examples |
|---|---|---|---|
| 1 | Format / lint | S0+ | `ruff`, `black`, `prettier`, `gofmt` |
| 2 | Type check | S1+ | `mypy`, `pyright`, `tsc`, `go vet` |
| 3 | Unit tests | S1+ | `pytest`, `jest`, `go test` |
| 4 | Secrets scan | S0+ | `gitleaks`, `trufflehog` |
| 5 | Dependency scan | S2+ | `pip-audit`, `npm audit`, `osv-scanner` |
| 6 | SAST | S2+ | `semgrep`, `bandit`, `codeql` |
| 7 | Domain invariants | S2+ | repo-specific scripts |
| 8 | Maintainability | S2+ | `radon`, `eslint --rule`, custom |
| 9 | Manifest regression | S2+ | `scripts/manifest_regression.py` |
| 10 | Redaction smoke | S1+ | `scripts/redaction_smoke.py` |
| 11 | Formal / neuro-symbolic | S3 | TLA+, Alloy, neuro-symbolic guards |
| 12 | Adversarial sweep | S3 | FlashRT-style on tool surface |
| 13 | AI-readiness regression | S2+ | `scripts/readiness_report.py --check-no-regression` |

## DryRUN contract

Before edits, the agent records in `plan.md`:

- files it will touch
- tests it will run
- expected diff size
- expected risk

After edits, reality is compared to predictions. Large divergence triggers a
review.

## Authorship and provenance

- Every commit on an agent branch is signed.
- PR description links the session JSONL and `plan.md`.
- Branch protection requires at least one human reviewer.
