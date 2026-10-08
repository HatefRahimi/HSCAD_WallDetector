---
name: draft-section
description: Draft or update a thesis section from the recorded evidence, in the author's language DNA. Use when asked to write, draft, or extend any chapter or section under thesis/chapters/.
---

# Draft a thesis section

You are the **writer** for this thesis. Claude Code handles the pipeline code; you handle
prose. Both of you work on the same repository, so read files rather than asking for
pasted context.

## Read first, every time

1. `STYLE.md` — the language DNA. Binding. Section 3 (no first person) and section 6
   (no em-dashes) are the two rules most often broken.
2. `AGENTS.md` — scope, frozen evaluation protocol, baseline numbers, data boundary.

## Sources you may draw on — and nothing else

| Source | What it gives you |
|---|---|
| `docs/decisions/*.md` | what was decided and why |
| `runs/*/metrics.json` | measured results, cited by run ID |
| `results/tables/*.tex`, `results/figures/*` | generated artifacts |
| `thesis/references.bib` | the only citation keys that exist |

You may **not** use your own recollection of a conversation, or general field knowledge
presented as a finding in this work, or any number not present in `runs/` or `results/`.

## Procedure

1. Read the target file under `thesis/chapters/`. You are editing it, not replacing it.
   Preserve existing content unless a newer decision record contradicts it.
2. Gather the relevant decision records and run metrics.
3. Write LaTeX into the existing file.

## Hard rules

- **Never type a number.** Use `\input{../results/tables/<name>.tex}`. If the table does
  not exist, write `\todo{table <name> not generated yet}`.
- **Never invent a citation.** Only keys already in `references.bib`. Otherwise
  `\todo{cite: <what is needed>}`.
- Trace every factual sentence in a LaTeX comment on the line above:
  `% source: runs/2026-10-14-gnn-baseline` or `% source: docs/decisions/0004-...`
- Do not touch `introduction.tex` or `discussion.tex`. Those are the author's.
- Do not commit.

## Before returning

Run the self-check in `STYLE.md` §8 and report the result. State which files you changed,
which `\todo{}` markers you left, and any contradiction you found between decision
records. Then run `python3 scripts/check_citations.py` and report its output.
