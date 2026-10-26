---
name: audit-eval
description: Audit split and metric code for train/test leakage and for metric mismatch between the graph and raster branches. Use when asked to audit, check, or review evaluation, splitting, or metric code.
---

# Audit the evaluation code

This is the highest-stakes code in the repository. Leakage here invalidates every
downstream claim in the thesis. Read `AGENTS.md` §2 (frozen protocol) first.

## Check specifically

- Is the split **by drawing**, never by element within a drawing?
- Is it by **customer / drafting office** where that information exists?
- Is it deterministic and seeded, so the same drawings land in the same fold across runs?
- Can a drawing appear in both train and test via a duplicate, a near-duplicate, a
  revision of the same plan, or a file copied under two names?
- Is any normalization, scaling, or feature statistic computed over the full dataset
  **before** splitting?
- Are precision/recall/F1 per element, over the wall class, with an explicit definition
  of what counts as a positive?
- For the raster branch: is pixel output mapped back to vector elements **before**
  comparison with the graph branch? Is that mapping documented?
- Are doors and windows reported separately rather than folded into the wall metric?

## Stance

Assume the author has missed something and find it. Report each finding with a file and
line reference.

## Output

Findings list, then the specific fixes you would make. Do not apply fixes; this code is
frozen by the brief, and any change requires a decision record.
