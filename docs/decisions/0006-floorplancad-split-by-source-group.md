---
id: 0006
date: 2026-10-26
title: Split FloorPlanCAD by source group and drop exact duplicates
status: accepted
supersedes: 0004
superseded-by:
runs: [2026-10-26-floorplancad-split-audit-2]
---

## Context

Decision 0004 treated a file-name prefix as one source across all folders. File names
repeat across folders with different content, so prefix numbering is not global, and
the evidence of 0004 counted coincidences of numbering as shared sources. The dataset
also contains byte-identical files under different names and folders.

## Options considered

- **A:** Keep 0004: one group per prefix across all folders.
- **B:** A source is (numbering namespace, prefix). Sources that share an identical
  file merge into one group. Exact copies are dropped, keeping one.

## Decision

Option B. `train-00` is one namespace; `train-01` and `test-00` share the other, as set
in `configs/default.yaml`. Every group lies wholly in train, validation or test.

## Evidence

Run `2026-10-26-floorplancad-split-audit-2`:

- A prefix in `train-00` and the same prefix in another folder share layer names no
  more than random pairs do (`train-00_vs_*_layer_jaccard`). Between `train-01` and
  `test-00` the same prefix shares far more than random pairs do
  (`train-01_vs_test-00_*_layer_jaccard`).
- Identical files occur in groups, many of them across train and test
  (`duplicate_content_groups`, `duplicate_groups_across_train_and_test`).
- Under the grouping of option B, nearly all official test files belong to a group
  that also has files in train (`test_file_fraction_with_group_in_train`).

The conclusion of 0004 holds: the official split leaks by source. Its evidence for
`train-00` did not.

## Consequences

- Identity of a drawing is `<folder>/<stem>`, never the stem alone.
- The deduplicated set is what every split and every count is drawn from.
- Near-duplicates (overlapping but not identical crops across groups) are not caught.

## Still unresolved

- Whether near-duplicates across groups exist in numbers that matter, for example
  crops of one building filed under two prefixes with different cropping.
