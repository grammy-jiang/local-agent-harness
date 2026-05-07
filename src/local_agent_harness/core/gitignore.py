#!/usr/bin/env python3
"""Generate a .gitignore for a repository.

Strategy:
  1. Detect the tech stack from the repo's files and config.
  2. Download the gitignore template from https://www.toptal.com/developers/gitignore
     (toptal/gitignore API). Falls back to a minimal bundled default if offline.
  3. Append harness-specific paths that must always be excluded.
"""

from __future__ import annotations

import os
import urllib.request
import urllib.error
from pathlib import Path


# ---------------------------------------------------------------------------
# Stack detection
# ---------------------------------------------------------------------------

# (file/dir name or extension, gitignore.io keyword)
_SIGNAL_KEYWORDS: list[tuple[str, str]] = [
    # languages / runtime
    ("pyproject.toml", "python"),
    ("setup.py", "python"),
    ("setup.cfg", "python"),
    ("requirements.txt", "python"),
    (".py", "python"),
    ("package.json", "node"),
    (".js", "node"),
    (".ts", "node"),
    (".tsx", "react"),
    (".jsx", "react"),
    ("go.mod", "go"),
    (".go", "go"),
    ("Cargo.toml", "rust"),
    (".rs", "rust"),
    ("pom.xml", "java"),
    ("build.gradle", "java"),
    (".java", "java"),
    (".kt", "kotlin"),
    ("Gemfile", "ruby"),
    (".rb", "ruby"),
    (".tf", "terraform"),
    (".swift", "swift"),
    (".cs", "csharp"),
    (".cpp", "c++"),
    (".c", "c"),
    # IDEs / editors
    (".vscode", "visualstudiocode"),
    (".idea", "jetbrains"),
    (".vim", "vim"),
    # environment managers
    (".venv", "virtualenv"),
    ("venv", "virtualenv"),
    (".python-version", "pyenv"),
    # notebooks
    (".ipynb", "jupyternotebooks"),
    # build / infra
    ("Dockerfile", "docker"),
    ("docker-compose.yml", "docker"),
    (".sh", "linux"),
    # OS — always included
]

_OS_KEYWORDS = ["linux", "macos", "windows"]
_ALWAYS_KEYWORDS = ["git"]


def detect_stack_keywords(repo: Path) -> list[str]:
    """Return a deduplicated list of gitignore.io keywords for *repo*."""
    found: set[str] = set(_ALWAYS_KEYWORDS)

    # Walk the tree (shallow: only top-level + one level deep to be fast)
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

    for signal, keyword in _SIGNAL_KEYWORDS:
        low = signal.lower()
        # exact filename match
        if low in entry_set:
            found.add(keyword)
            continue
        # extension match
        if low.startswith(".") and any(e.endswith(low) for e in entry_set):
            found.add(keyword)

    # Add OS keywords (they produce few noise entries; always useful)
    found.update(_OS_KEYWORDS)

    # Remove duplicate sub-sets: 'react' implies 'node'
    if "react" in found:
        found.add("node")

    return sorted(found)


# ---------------------------------------------------------------------------
# Template download
# ---------------------------------------------------------------------------

_API_URL = "https://www.toptal.com/developers/gitignore/api/{keywords}"
_TIMEOUT = 10  # seconds

_MINIMAL_FALLBACK = """\
# Minimal fallback .gitignore (generated offline)
*.pyc
__pycache__/
*.egg-info/
dist/
build/
.eggs/
*.so
*.dylib
node_modules/
.DS_Store
Thumbs.db
*.log
"""


def fetch_gitignore_template(keywords: list[str]) -> str:
    """Download a gitignore template for *keywords* from the toptal API.

    Returns the downloaded text, or the minimal fallback on any network error.
    """
    if not keywords:
        return _MINIMAL_FALLBACK
    url = _API_URL.format(keywords=",".join(keywords))
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            return str(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return _MINIMAL_FALLBACK


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

_HARNESS_BLOCK_MARKER = "# local-agent-harness (do not edit below this line)"

_HARNESS_LINES = [
    ".agent/logs/",
    ".agent/eval/",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
]


def render_gitignore(repo: Path, dry: bool) -> str:
    """Write (or preview) a .gitignore for *repo*.

    If a .gitignore already exists and was written by us (contains our marker),
    it is left untouched so user edits above the marker are preserved.

    If it does not exist, we download a fresh template and write it.
    If it exists without our marker, we append the harness block.
    """
    gi = repo / ".gitignore"

    if gi.exists():
        existing = gi.read_text(encoding="utf-8", errors="ignore")
        if _HARNESS_BLOCK_MARKER in existing:
            return "gitignore: already managed — skipping"
        # File exists but no harness block → just append
        needed = [ln for ln in _HARNESS_LINES if ln not in existing]
        if not needed:
            return "gitignore: already covers harness paths"
        block = f"\n{_HARNESS_BLOCK_MARKER}\n" + "\n".join(needed) + "\n"
        if dry:
            return f"gitignore: would append harness block ({len(needed)} lines)"
        with gi.open("a", encoding="utf-8") as fh:
            fh.write(block)
        return f"gitignore: appended harness block ({len(needed)} lines)"

    # New .gitignore
    keywords = detect_stack_keywords(repo)
    if dry:
        return f"gitignore: would create from toptal template (keywords={keywords})"
    template = fetch_gitignore_template(keywords)
    block = f"\n{_HARNESS_BLOCK_MARKER}\n" + "\n".join(_HARNESS_LINES) + "\n"
    gi.write_text(template + block, encoding="utf-8")
    return f"gitignore: created (keywords={keywords})"


if __name__ == "__main__":  # pragma: no cover
    import sys
    import argparse

    ap = argparse.ArgumentParser(description="Generate .gitignore")
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    repo = a.repo.resolve()
    print(render_gitignore(repo, a.dry_run))
    sys.exit(0)
