# Claude Code instructions

Read `AGENTS.md` first — it is the project brief and the single source of truth.
Read `STYLE.md` before writing any word that goes into `thesis/`.

## Non-negotiable

- Never read, open, or summarize anything under `data/`. See the data boundary in AGENTS.md §3.
- Never type a number into LaTeX. Numbers come from `results/tables/*.tex` via `\input{}`.
- Every claim needs a decision record, a run ID, or an existing bib key. Otherwise: `\todo{}`.
- Prefer small, targeted edits over regenerating whole files.
- Explain the *why* behind an architectural choice before implementing it.

## Commit trailers

Add `Assisted-by: Claude` to commits you help produce.
