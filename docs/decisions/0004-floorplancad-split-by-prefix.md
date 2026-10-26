---
id: 0004
date: 2026-10-26
title: Split FloorPlanCAD by file-name prefix, not by the official split
status: superseded
supersedes:
superseded-by: 0006
runs: [2026-10-26-floorplancad-split-audit]
---

## Context

FloorPlanCAD files are crops named `<prefix>-<index>.svg`. AGENTS.md §2 requires a
held-out split by drawing, and by customer or drafting office where possible. The
official train and test folders had to be checked against that rule before any result
is measured on them.

## Options considered

- **A:** Use the official train/test folders.
- **B:** Pool all files and split by prefix with a fixed seed.

## Decision

Option B. Every prefix lies wholly in train, validation or test. The official folders
are ignored for evaluation.

## Evidence

Run `2026-10-26-floorplancad-split-audit`: nearly all official test prefixes also occur
in train, and nearly all official test files have a prefix that occurs in train
(`test_prefixes_also_in_train`, `test_file_fraction_with_prefix_in_train`). Crops per
prefix range widely (`crops_per_prefix_*`). Crops sharing a prefix also share a
layer-naming vocabulary, which fits a common project or drafting office; this was
observed on a handful of files, not measured.

## Consequences

- Results are not directly comparable with numbers published on the official split.
  Any such comparison in the thesis must say so.
- Subsets are drawn as whole prefixes, never as single crops.
- The split seed lives in `configs/default.yaml`.

## Still unresolved

- Whether one prefix is one drawing or one project of several drawings. Either way the
  split keeps it together; the answer only changes how the grouping is described.
