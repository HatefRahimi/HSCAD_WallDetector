---
description: Audit split and metric code for leakage, then send it to GPT for adversarial review
---

Audit the evaluation code. This is the highest-stakes code in the repository: leakage
here invalidates every downstream claim in the thesis.

## Step 1: your own audit

Read `AGENTS.md` §2 (frozen evaluation protocol), then examine the split and metric code
under `src/`. Check specifically:

- Is the split **by drawing**, never by element within a drawing?
- Is the split by **customer / drafting office** where that information exists?
- Is the split deterministic and seeded, so the same drawings land in the same fold
  across runs?
- Can any drawing appear in both train and test through a duplicate, a near-duplicate, a
  revision of the same plan, or a file copied under two names?
- Is any normalization, scaling, or feature statistic computed over the full dataset
  before splitting?
- Are precision/recall/F1 computed per element, over the wall class, with an explicit
  definition of what counts as a positive?
- For the raster branch: is pixel output mapped back to vector elements **before**
  comparison with the GNN? Is that mapping documented?
- Are doors/windows reported separately rather than folded into the wall metric?

Report findings as a list, each with a file and line reference.

## Step 2: adversarial review by GPT

Then run:

```
/codex:adversarial-review
```

with focus text along these lines:

> Audit this evaluation code for train/test leakage. The split must be by drawing and
> ideally by customer. Look for: near-duplicate drawings across folds, dataset-wide
> statistics computed before the split, non-deterministic splitting, and any place where
> the per-element metric definition differs between the graph branch and the raster
> branch. Assume the author has missed something and find it.

## Step 3

Summarize both audits together, flag any disagreement between them, and propose the
specific fixes. Do not apply fixes without asking; this code is frozen by the brief, so
any change requires a decision record via `/log`.
