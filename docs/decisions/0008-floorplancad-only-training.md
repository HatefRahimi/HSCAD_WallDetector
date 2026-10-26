---
id: 0008
date: 2026-10-26
title: Train on FloorPlanCAD only; use archive drawings for testing after conversion
status: accepted
supersedes: 0003
superseded-by:
runs: []
---

## Context

Decision 0003 planned three stages, including training on the archive on the company
machine. The author decided to treat FloorPlanCAD as the only training source and to
use archive drawings, converted to the FloorPlanCAD format, for testing only.

## Options considered

- **A:** Keep 0003: train on FloorPlanCAD and on the archive, then measure transfer.
- **B:** Train on FloorPlanCAD only. Archive drawings are converted to SVG or PNG and
  serve as an external test set.

## Decision

Option B, by decision of the author.

## Evidence

Judgement, not measurement. Training needs no company data and no company hardware,
and every training result is reproducible from public data.

## Consequences

- The question the thesis answers shifts from learning from the archive to how well a
  model learned from public drawings carries over to industrial ones. The research
  question in AGENTS.md is the author's to restate.
- Features and models may only use what a conversion from DWG can reproduce: the
  FloorPlanCAD element kinds, crop size and layer groups.
- The HSCAD redraw matching remains the route to archive test labels.

## Still unresolved

- How archive drawings are converted, and how their labels are obtained.
- Licence compatibility of FloorPlanCAD with the industry partnership (from 0003).
