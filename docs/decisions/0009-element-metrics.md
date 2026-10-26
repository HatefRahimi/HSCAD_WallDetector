---
id: 0009
date: 2026-10-26
title: Score wall, door and window per element, pooled over the test fold
status: accepted
supersedes:
superseded-by:
runs: []
---

## Context

AGENTS.md §2 fixes per-element precision, recall and F1 for walls, with doors and
windows reported separately. It does not fix which elements are scored, how classes
are derived from labels, or how scores are aggregated over drawings.

## Options considered

- **A:** Score every element, text included; average scores per drawing.
- **B:** Score geometric elements only (line, arc, circle, ellipse); pool all test
  elements, then compute each class's scores once.

## Decision

Option B. An element's true class is wall, door or window if its `semantic-id` is in
that class's list in the config, otherwise `other`, including elements without a label.
For each class: precision = TP / (TP + FP), recall = TP / (TP + FN), F1 their harmonic
mean, with each defined as 0 when its denominator is 0.

## Evidence

Judgement, not measurement. Text elements carry no labels in the release, so scoring
them only adds trivial negatives. Pooling weights every element equally; averaging per
drawing would let small crops with a handful of walls swing the result.

## Consequences

- Any model must output one class per geometric element. A raster model is scored only
  after its pixels are mapped back to elements (AGENTS.md §2).
- Per-drawing scores may be reported in addition, never instead.

## Still unresolved

- Whether curtain wall (id 2) joins the wall class (from 0005).
