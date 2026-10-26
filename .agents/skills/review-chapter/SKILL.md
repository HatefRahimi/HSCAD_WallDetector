---
name: review-chapter
description: Review a thesis chapter as a skeptical examiner, checking traceability of every claim and conformance to the language DNA. Use when asked to review, critique, or check a chapter under thesis/chapters/.
---

# Review a thesis chapter

Read `STYLE.md` and `AGENTS.md` first, then the chapter file(s).

## Rubric

1. **Traceability.** Does every factual claim trace to a decision record, a run ID, or a
   `\cite{}` key present in `references.bib`? List each sentence that does not.
2. **Numbers.** Any number typed inline rather than `\input` from `results/tables/`?
   Each is an error regardless of whether the value is correct.
3. **Overreach.** Any sentence claiming more than was measured (generalization,
   superiority, causation) that the runs do not support?
4. **Language DNA.** Violations of `STYLE.md`: first person, em-dashes, banned words,
   wrong tense, inconsistent terminology, uniform sentence length where the fingerprint
   in §2 calls for variation.
5. **Structure.** Paragraphs with more than one idea; sections opening by restating their
   title; limitations deferred to a catch-all.
6. **Open markers.** List remaining `\todo{}`.

## Stance

Review as a skeptical examiner. For each claim ask what evidence supports it and whether
that evidence supports *that strength* of claim. Flag anything fluent but unsupported,
and any result presented without its limitation. Assume something has been missed.

## Output

A list with line references, grouped by severity: unsupported claims first, then typed
numbers, then style. Do not rewrite. Do not commit.
