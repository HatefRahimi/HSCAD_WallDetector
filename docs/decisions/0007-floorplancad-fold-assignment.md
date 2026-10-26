---
id: 0007
date: 2026-10-26
title: Assign FloorPlanCAD groups to folds by seeded shuffle and freeze the result
status: accepted
supersedes:
superseded-by:
runs: []
---

## Context

Decision 0006 fixed what a group is. It did not fix how groups are assigned to train,
validation and test, how the fold sizes are measured, or how later experiments get the
same split.

## Options considered

- **A:** Fractions over groups; every experiment recomputes the split from the config.
- **B:** Fractions over deduplicated drawings, filled group by group in a seeded random
  order; the split is computed once, written to a run directory, and loaded by every
  experiment from that run ID.

## Decision

Option B. Groups are sorted by ID, shuffled with `split.seed`, and added to test until
test holds at least `split.test_fraction` of the deduplicated drawings, then to
validation the same way; the rest is train. Of identical files, the copy with the
smallest drawing ID is kept. The resulting fold of every drawing is stored as
`split.csv` in a run directory.

## Evidence

Judgement, not measurement. Group sizes range widely (run
`2026-10-26-floorplancad-split-audit-2`, `files_per_group_*`), so fractions over groups
would make fold sizes depend on which groups the shuffle happens to draw. A stored
split cannot drift when the code that produced it changes later.

## Consequences

- Fold sizes overshoot their targets by at most one group.
- Experiments cite the split run ID; a new split means a new run and a new decision.
- Classes are not stratified. Their share per fold is reported with the split.

## Still unresolved

- Whether per-fold class shares differ enough to need stratification by group.
