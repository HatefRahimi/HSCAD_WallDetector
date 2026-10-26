---
description: Delegate drafting of a thesis section to GPT, then review what comes back
argument-hint: <chapter/section> e.g. method/labeling
---

Draft the thesis section: **$ARGUMENTS**

GPT is the writer for this thesis (`AGENTS.md` §6). Your job here is to prepare the
material, delegate the drafting, and review the result, not to write the prose yourself.

## Step 1: prepare

Read `STYLE.md` and `AGENTS.md`. Then gather what the section needs and report it to me
in plain text:

- which decision records under `docs/decisions/` are relevant
- which run IDs under `runs/` provide the numbers
- which tables under `results/tables/` exist, and which are missing
- any contradiction between decision records that must be resolved before drafting

If a needed table does not exist yet, say so. Do not fabricate the number.

## Step 2: delegate

Run:

```
/codex:delegate
```

instructing it to use its `draft-section` skill on **$ARGUMENTS**, and naming the
specific decision records, run IDs and tables you identified in step 1.

## Step 3: review what comes back

Review the draft against `STYLE.md` §8, specifically:

- first person anywhere outside the acknowledgements (must be none)
- em-dashes (must be none)
- sentence-length variation, or flat uniform length (a generated-prose tell)
- any number typed inline instead of `\input`
- any `\cite` key not in `references.bib`
- any claim without a `% source:` comment tracing it

Then run `python3 scripts/check_citations.py`.

Report findings and ask before fixing. Do not commit.

## If GPT is unavailable

Say so and stop. Do not quietly draft it yourself. The point of the split is that the
drafting agent and the reviewing agent are different.
