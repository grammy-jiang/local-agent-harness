#!/usr/bin/env python3
"""Write `.agent/eval/readiness.md` and optionally enforce no-regression.

Usage:
    python readiness_report.py [--repo PATH] [--check-no-regression]

When --check-no-regression is passed, the script compares the current score
to the previous score recorded under `<HARNESS_SENTINEL>` in
`.agent/eval/readiness.md` and exits non-zero if any axis dropped.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

# Reuse assess_repo's detector
from . import assess_repo  # type: ignore

SENTINEL = "<!-- local-agent-harness:readiness:v1 -->"
LEGACY_SENTINELS = ("<!-- harness-bootstrap:readiness:v1 -->",)


def render_report(result: dict, repo: Path) -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    axes = result["axes"]
    lines = [
        SENTINEL,
        "# AI-Readiness Report",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Repository | `{repo}` |",
        f"| Run timestamp | `{now}` |",
        f"| Detected stage | `{result['stage']}` |",
        f"| Detected runtimes | `{', '.join(result['detected_runtimes']) or 'none'}` |",
        "",
        "## Score (0–5 per axis)",
        "",
        "| Axis | Score |",
        "|---|---|",
        f"| Agent config | {axes['agent_config']} |",
        f"| Documentation | {axes['documentation']} |",
        f"| CI/CD | {axes['ci_cd']} |",
        f"| Code structure | {axes['code_structure']} |",
        f"| Security | {axes['security']} |",
        f"| **Total** | **{result['total']} / 25** |",
        "",
        "## Missing artifacts",
        "",
    ]
    if result["missing_artifacts"]:
        lines += [f"- {m}" for m in result["missing_artifacts"]]
    else:
        lines.append("- (none)")
    lines += [
        "",
        "## Machine block",
        "",
        "```",
        f"stage={result['stage']}",
        f"total={result['total']}",
        f"agent_config={axes['agent_config']}",
        f"documentation={axes['documentation']}",
        f"ci_cd={axes['ci_cd']}",
        f"code_structure={axes['code_structure']}",
        f"security={axes['security']}",
        "```",
        "",
    ]
    return "\n".join(lines) + "\n"


def parse_machine_block(text: str) -> dict | None:
    if SENTINEL not in text and not any(s in text for s in LEGACY_SENTINELS):
        return None
    m = re.search(r"```\n(stage=.*?)\n```", text, re.DOTALL)
    if not m:
        return None
    out: dict = {}
    for line in m.group(1).splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--check-no-regression", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()

    result = assess_repo.detect(repo)
    out_dir = repo / ".agent" / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "readiness.md"

    prev = parse_machine_block(out_path.read_text(encoding="utf-8")) if out_path.exists() else None

    out_path.write_text(render_report(result, repo), encoding="utf-8")
    print(f"wrote {out_path}")

    if args.check_no_regression and prev:
        regressed = []
        axes_keys = ["agent_config", "documentation", "ci_cd", "code_structure", "security"]
        for k in axes_keys:
            try:
                if int(result["axes"][k]) < int(prev.get(k, "0")):
                    regressed.append((k, prev.get(k), result["axes"][k]))
            except Exception:
                pass
        if regressed:
            print("AI-readiness regressed:", file=sys.stderr)
            for k, before, after in regressed:
                print(f"  {k}: {before} -> {after}", file=sys.stderr)
            return 1
        print("no regression vs previous report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
