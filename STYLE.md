# Language DNA

Binding for every word written into `thesis/`. Both agents read this before drafting.

This file is derived from measurements of the author's own proposal text, not from
generic academic-writing advice. Where a rule below seems unusual, it is unusual because
the author's writing is.

---

## 1. Voice samples (the most important part of this file)

Imitate these. A model matches a sample far better than it follows an adjective.

> The archive was built to be read by people, not interpreted by software. Layer names
> differ by customer, by language, and by drafting office; the geometry is often plain
> lines, arcs, and polylines with nothing marking what any of them represent; some
> drawings hide their entire content inside block references, and others use layer names
> that say little.

> Each one holds a decision an expert has already made: the customer's flat 2D lines and
> the planner's 3D objects sit in the same file, showing which lines were understood to
> be a wall and which were not. This means the drawings could serve as training data. In
> their current form, however, they cannot.

> The step is manual, takes time per project, and is repeated for every plan that
> arrives.

> Fixed rules and thresholds break on this kind of variation, which is what motivates a
> learned approach.

**What to notice and reproduce:**

- The subject is usually **the thing**, not the researcher. "The step is manual." "The
  archive was built to be read by people." Not "we observe that the step is manual."
- A long, clause-rich sentence is followed by a short flat one. The short sentence carries
  the point.
- Limitations are stated in the same plain register as results. No hedging apparatus.
- Concrete nouns throughout: lines, arcs, polylines, block references, drafting office.
- Colons and semicolons do real structural work, listing variants of one idea.

> **ADD YOUR OWN.** As you write chapters you are happy with, paste another paragraph
> here. This section should grow.

---

## 2. Measured fingerprint

Taken from the proposal body (41 sentences). Match this distribution; do not flatten it.

| Feature | Target | Note |
|---|---|---|
| Mean sentence length | ~25 words | Not a cap — an average |
| Median | ~22 words | |
| Short sentences (≤12 words) | ~15% of sentences | These carry the punchlines |
| Long sentences (≥30 words) | ~30% of sentences | Clause-rich, semicolon-linked |
| Variation | high (σ ≈ 12 words) | **The most imitable feature** |
| Semicolons | ~1 per 7 sentences | Used to list variants of one idea |
| Em-dashes | **zero** | Author does not use them. Use a full stop. |
| "we" / "I" | **zero** | See §3 |
| "however" | ≤1 per chapter | |
| "moreover", "furthermore", "novel" | **zero** | |

A model's default is uniform medium-length sentences. That flatness is the single most
recognizable sign of generated prose. Deliberately alternate long and short.

---

## 3. Person and agency — read carefully

The author's proposal uses **no first person at all**, singular or plural. Do not
introduce it.

Instead, the subject is the object of study, the method, or the thesis itself:

| Write | Not |
|---|---|
| The model is trained on held-out drawings. | We train the model on… |
| Label quality is treated as part of the research. | We treat label quality as… |
| The thesis has to answer this early. | In this thesis, we answer… |
| Two directions are available. | We considered two directions. |
| Wall generation is the natural starting point. | We chose wall generation because… |

This is **not** a licence for agentless passive that hides a decision. When a choice was
made and the reasoning matters, name the reasoning, not the chooser:

- Good: *Splitting by customer rather than by drawing tests generalization across
  drafting conventions.*
- Bad: *It was determined that splitting by customer was appropriate.*

Exception: the acknowledgements, where "I" is fine.

---

## 4. Hard rules

| Rule | Setting |
|---|---|
| Language | English |
| Spelling | **PICK ONE AND WRITE IT HERE:** British / American |
| Person | None (see §3) |
| Tense — methods | Past for what was done: *the model was trained on…* |
| Tense — results | Present for what the data shows: *precision drops on…* |
| Tense — related work | Present: *Zhang et al. propose…* |
| Tense — the archive/data | Present for what is true now: *layer names differ by customer* |
| Cross-references | `\cref{tab:x}`, `\cref{fig:x}`, `\cref{ch:x}`, `\cref{sec:x}`. cleveref prints the name itself, so never prefix it by hand: `Figure~\cref{...}` prints "Figure Figure 3". Do not use bare `Figure~\ref{...}` either; keep one mechanism. Never "the figure below" |
| Citations | `\cite{key}` only; key must exist in `literature.bib` |
| Numbers | Never typed inline. `\input{../results/tables/x.tex}` |
| Numbers in prose | `\num{}` and `\SI{}{}` (siunitx), never bare digits with hand-typed units |
| Tables | booktabs only: `\toprule`, `\midrule`, `\bottomrule`. No `\hline`, no vertical rules |
| Abbreviations | `\gls{}` / `\glspl{}` (glossaries-extra), defined in `abbreviations.tex`. Never type the short form by hand |

---

## 5. Terminology (consistent, never varied for elegance)

| Use | Not |
|---|---|
| drawing | plan, file, DWG (except for the file format itself) |
| entity | element (in code/data contexts), object, item |
| wall segment | wall piece, wall part |
| label recovery | annotation, labeling (for the recovery process) |
| held-out drawings | test set (prefer the explicit term on first use) |
| drafting office | drafting firm, design office |
| HSCAD | HsCAD, hscad |
| GraphSAGE | GraphSage, graphsage |
| planner | architect, designer |

---

## 6. Banned

- **Em-dashes.** The author uses none. Use a full stop or a semicolon.
- First person, outside the acknowledgements.
- Hedging stacks: "it could potentially be argued that it may possibly…"
- Hype: novel, powerful, cutting-edge, state-of-the-art (unless comparing against a named
  SOTA number), revolutionary, seamless, leverage (as a verb).
- Connective filler openers: Moreover, Furthermore, Additionally, Notably, Importantly.
- "In this thesis, we will…" — doubly banned (first person *and* filler).
- Agentless passive that hides a decision ("it was determined that…").
- Claims of generality beyond what was measured.
- Tricolon padding: three adjectives where one is accurate.

---

## 7. Structure conventions

- One idea per paragraph. A paragraph needing a semicolon to hold together is two
  paragraphs — note that this differs from sentence-level semicolon use, which is fine.
- Every section opens by saying what it establishes, not by restating its own title.
- Limitations appear in the section where the result appears, not only in a final
  catch-all.
- A term is defined once, at first use, in the chapter where it first matters.
- Paragraphs run 3–6 sentences. A one-sentence paragraph is allowed for emphasis, rarely.

---

## 8. Self-check before returning a draft

An agent must verify, and report, before handing back any section:

1. Did I use "we" or "I" anywhere outside the acknowledgements? (Must be no.)
2. Did I use an em-dash? (Must be no.)
3. Is my sentence-length variation close to §2, or is everything the same length?
4. Does every number come from `\input`?
5. Does every `\cite` key exist in `literature.bib`?
6. Did I use any banned word from §6?
