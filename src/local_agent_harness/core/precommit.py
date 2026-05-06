#!/usr/bin/env python3
"""Generate a .pre-commit-config.yaml for a repository.

Strategy:
  1. Detect languages / frameworks present in the repo.
  2. Build a config with:
     - universal hooks (whitespace, merge-conflicts, large-files, gitleaks)
     - language-specific lint / format hooks
  3. Add a global ``exclude`` regex that covers generated files and
     repository files that should not be linted (.gitignore, lock files, etc.).
"""
from __future__ import annotations

import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

#: file-system signal → set of "language" tags
_SIGNAL_LANG: list[tuple[str, str]] = [
    ("pyproject.toml", "python"),
    ("setup.py",       "python"),
    ("setup.cfg",      "python"),
    ("requirements.txt", "python"),
    (".py",            "python"),
    ("package.json",   "javascript"),
    (".js",            "javascript"),
    (".ts",            "typescript"),
    (".tsx",           "typescript"),
    (".jsx",           "javascript"),
    ("go.mod",         "go"),
    (".go",            "go"),
    ("Cargo.toml",     "rust"),
    (".rs",            "rust"),
    ("pom.xml",        "java"),
    ("build.gradle",   "java"),
    (".java",          "java"),
    (".sh",            "shell"),
    (".bash",          "shell"),
    (".md",            "markdown"),
    (".yaml",          "yaml"),
    (".yml",           "yaml"),
    (".tf",            "terraform"),
    (".rb",            "ruby"),
    ("Gemfile",        "ruby"),
]


def detect_languages(repo: Path) -> set[str]:
    """Return the set of language tags detected in *repo*."""
    found: set[str] = set()
    entries: list[str] = []
    try:
        for name in os.listdir(repo):
            entries.append(name)
            sub = repo / name
            if sub.is_dir() and not name.startswith("."):
                try:
                    for subname in os.listdir(sub):
                        entries.append(subname)
                except OSError:
                    pass
    except OSError:
        pass

    entry_set = {e.lower() for e in entries}
    for signal, lang in _SIGNAL_LANG:
        low = signal.lower()
        if low in entry_set:
            found.add(lang)
            continue
        if low.startswith(".") and any(e.endswith(low) for e in entry_set):
            found.add(lang)
    return found


# ---------------------------------------------------------------------------
# Hook catalog
# ---------------------------------------------------------------------------

# Each entry: (repo_url, rev, list_of_hook_configs)
# hook_config is a dict; rendered as YAML indented under the repo entry.

_UNIVERSAL_HOOKS = """\
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: end-of-file-fixer
        exclude: \\.gitignore$
      - id: trailing-whitespace
        exclude: \\.gitignore$
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: check-merge-conflict
      - id: check-yaml
      - id: check-json
      - id: check-toml
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.23.3
    hooks:
      - id: gitleaks"""

_LANG_HOOKS: dict[str, str] = {
    "python": """\
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0
    hooks:
      - id: mypy
        additional_dependencies: ["mypy>=1.10"]""",

    "javascript": """\
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        exclude: \\.gitignore$""",

    "typescript": """\
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        exclude: \\.gitignore$""",

    "go": """\
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-fmt
      - id: go-vet""",

    "rust": """\
  - repo: https://github.com/doublify/pre-commit-rust
    rev: v1.0
    hooks:
      - id: fmt
      - id: cargo-check""",

    "shell": """\
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.10.0.1
    hooks:
      - id: shellcheck""",

    "markdown": """\
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.44.0
    hooks:
      - id: markdownlint
        args: ["--disable", "MD013"]
        exclude: \\.gitignore$""",

    "yaml": """\
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.37.0
    hooks:
      - id: yamllint
        args: ["-d", "{extends: relaxed, rules: {line-length: {max: 120}}}"]
        exclude: \\.gitignore$""",

    "terraform": """\
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.99.4
    hooks:
      - id: terraform_fmt""",

    "ruby": """\
  - repo: https://github.com/rubocop/rubocop
    rev: v1.75.5
    hooks:
      - id: rubocop""",
}

# Paths / patterns that should be globally excluded from hooks
_GLOBAL_EXCLUDE_PATTERNS = [
    r"\.gitignore$",             # managed by local-agent-harness
    r"(^|/)dist/",
    r"(^|/)build/",
    r"(^|/)\.venv/",
    r"(^|/)venv/",
    r"(^|/)node_modules/",
    r"(^|/)\.agent/logs/",
    r".*\.lock$",                # lock files
    r".*\.min\.(js|css)$",       # minified assets
]

_GLOBAL_EXCLUDE = "(?x)^(\n  " + " |\n  ".join(_GLOBAL_EXCLUDE_PATTERNS) + "\n)$"


def build_precommit_config(languages: set[str]) -> str:
    """Return a .pre-commit-config.yaml string for the given *languages*."""
    lines: list[str] = [
        "# .pre-commit-config.yaml — generated by local-agent-harness",
        "# Run: pre-commit install  (first time)",
        "# Run: pre-commit run --all-files  (manually)",
        "#",
        "# .gitignore is intentionally excluded from whitespace/formatting hooks",
        "# because it is managed by local-agent-harness and may contain",
        "# machine-generated sections.",
        "",
        f"exclude: '{re.escape(_GLOBAL_EXCLUDE_PATTERNS[0])}'",
        "",
        "repos:",
        _UNIVERSAL_HOOKS,
    ]

    # deduplicate: js + ts → only render prettier once
    rendered: set[str] = set()
    for lang in sorted(languages):
        hook_block = _LANG_HOOKS.get(lang)
        if hook_block and lang not in rendered:
            # skip typescript-specific prettier if javascript already added it
            if lang == "typescript" and "javascript" in rendered:
                rendered.add(lang)
                continue
            lines.append(hook_block)
            rendered.add(lang)

    return "\n".join(lines) + "\n"


def render_precommit(repo: Path, dry: bool) -> str:
    """Write (or preview) a .pre-commit-config.yaml for *repo*."""
    dest = repo / ".pre-commit-config.yaml"
    if dest.exists():
        return "pre-commit: skip (exists)"
    languages = detect_languages(repo)
    if dry:
        return f"pre-commit: would create (languages={sorted(languages)})"
    content = build_precommit_config(languages)
    dest.write_text(content, encoding="utf-8")
    return f"pre-commit: created (languages={sorted(languages)})"


if __name__ == "__main__":  # pragma: no cover
    import sys
    import argparse

    ap = argparse.ArgumentParser(description="Generate .pre-commit-config.yaml")
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    repo = a.repo.resolve()
    print(render_precommit(repo, a.dry_run))
    sys.exit(0)
