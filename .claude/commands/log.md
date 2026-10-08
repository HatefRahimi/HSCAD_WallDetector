---
description: Append a decision record for this work session
---

Write a new decision record capturing what was decided in this session.

Steps:

1. Read `AGENTS.md` §4 so you follow the recording rules.
2. Look at `docs/decisions/` and pick the next sequential number (`NNNN`).
3. Review what actually happened this session: `git diff`, `git log --oneline -10`, and
   any new entries under `runs/`.
4. Copy `docs/decisions/TEMPLATE.md` to `docs/decisions/NNNN-<short-slug>.md` and fill it.

Rules:

- Record only what was **decided**, with the evidence that supported it. Not a narrative
  of the session.
- Every supporting number must cite a run ID from `runs/`. If a claim has no run behind
  it, write it as an open question instead, under "Still unresolved".
- If this decision supersedes an earlier record, add `Supersedes: NNNN` in the front
  matter and add `Superseded-by: NNNN` to the old one. Never edit the old record's body.
- Do not invent rationale. If you do not know why a choice was made, ask me.
- Keep it short. A decision record that runs past one screen is usually two decisions.
