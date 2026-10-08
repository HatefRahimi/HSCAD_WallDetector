---
description: Review a thesis chapter against the style guide and the evidence rubric
argument-hint: <chapter> e.g. method
---

Review the chapter: **$ARGUMENTS**

## Step 1 — your own review

Read `STYLE.md` and `AGENTS.md`, then read the chapter file(s) under `thesis/chapters/`.

Check every paragraph against this rubric:

1. **Traceability.** Does every factual claim trace to a decision record, a run ID, or a
   `\cite{}` key that exists in `references.bib`? List any sentence that does not.
2. **Numbers.** Is any number typed inline instead of coming from
   `\input{../results/tables/...}`? List each one — these are errors regardless of
   whether the value is correct.
3. **Overreach.** Does any sentence claim more than was measured? Flag claims of
   generalization, superiority, or causation that the runs do not support.
4. **Style.** Violations of `STYLE.md`: wrong tense, inconsistent terminology, banned
   words, hedging stacks, figure references not using `\ref`.
5. **Structure.** Paragraphs carrying more than one idea; sections that open by
   restating their own title; limitations deferred to a catch-all instead of appearing
   where the result does.
6. **Open markers.** List all remaining `\todo{}` markers.

Report as a list with line references. Do not rewrite yet.

## Step 2 — adversarial review by GPT

Run:

```
/codex:adversarial-review
```

with focus text along these lines:

> Review this thesis chapter as a skeptical examiner. For each claim, ask what evidence
> supports it and whether the stated evidence actually supports that strength of claim.
> Flag anything that reads as fluent but unsupported, any result presented without its
> limitation, and any place where a weaker claim would be defensible but the stronger one
> is made. Do not comment on prose style.

## Step 3

Present both reviews together, grouped by severity: unsupported claims first, then typed
numbers, then style. Ask me which to fix before changing anything.
