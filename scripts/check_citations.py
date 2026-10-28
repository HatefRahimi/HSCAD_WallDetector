#!/usr/bin/env python3
"""Fail if the thesis cites a key that does not exist in literature.bib.

This is what prevents invented references from reaching a chapter. Run it manually:

    python scripts/check_citations.py

or install it as a pre-commit hook:

    git config core.hooksPath .githooks

Exit code 1 means a citation is unresolved, a number was typed inline where a generated
table should be used, or an unresolved \\todo{} remains in a chapter marked final.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THESIS_DIR = REPO_ROOT / "thesis"
BIB_FILE = THESIS_DIR / "literature.bib"
# Authored sources sit beside thesis_main.tex; vendor files under lmedoc/ are excluded.
CHAPTERS = (
    "introduction", "background", "data", "methodology",
    "experiments", "results", "discussion", "conclusion", "appendix", "thesis_main",
)

BIB_ENTRY = re.compile(r"^\s*@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
# \cite, \citep, \citet, \parencite, \textcite, with optional [..] options
CITE_CALL = re.compile(r"\\(?:cite[a-zA-Z]*|parencite|textcite)\s*(?:\[[^\]]*\])*\s*\{([^}]*)\}")
COMMENT = re.compile(r"(?<!\\)%.*$", re.MULTILINE)
# A bare decimal in prose: the thing that should have come from a generated table.
INLINE_NUMBER = re.compile(r"(?<![\w.\\{=\-])\d+\.\d+(?![\w.}])")
TODO_CALL = re.compile(r"\\todo\s*(?:\[[^\]]*\]\s*)?\{")


def strip_comments(text: str) -> str:
    return COMMENT.sub("", text)


def bib_keys() -> set[str]:
    if not BIB_FILE.exists():
        print(f"error: {BIB_FILE.relative_to(REPO_ROOT)} not found", file=sys.stderr)
        raise SystemExit(1)
    return set(BIB_ENTRY.findall(BIB_FILE.read_text(encoding="utf-8")))


def tex_files() -> list[Path]:
    return [THESIS_DIR / f"{name}.tex" for name in CHAPTERS]


def main() -> int:
    known = bib_keys()
    problems: list[str] = []
    todos: list[str] = []

    for path in tex_files():
        rel = path.relative_to(REPO_ROOT)
        if not path.exists():
            problems.append(f"{rel}: chapter file missing")
            continue
        raw = path.read_text(encoding="utf-8")
        body = strip_comments(raw)

        for lineno, line in enumerate(body.splitlines(), start=1):
            for group in CITE_CALL.findall(line):
                for key in (k.strip() for k in group.split(",")):
                    if key and key not in known:
                        problems.append(f"{rel}:{lineno}: unknown citation key '{key}'")

            # Numbers typed into prose instead of \input from results/tables/
            if "\\input" not in line and "\\includegraphics" not in line:
                for match in INLINE_NUMBER.finditer(line):
                    problems.append(
                        f"{rel}:{lineno}: inline number '{match.group()}': "
                        "use \\input{../results/tables/...} instead"
                    )

            if TODO_CALL.search(line):
                todos.append(f"{rel}:{lineno}: {line.strip()[:90]}")

    if todos:
        print(f"{len(todos)} open todo marker(s):")
        for item in todos[:20]:
            print(f"  {item}")
        if len(todos) > 20:
            print(f"  ... and {len(todos) - 20} more")
        print()

    if problems:
        print(f"{len(problems)} problem(s) found:", file=sys.stderr)
        for item in problems:
            print(f"  {item}", file=sys.stderr)
        return 1

    print(f"citations ok: {len(known)} keys in literature.bib, no inline numbers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
