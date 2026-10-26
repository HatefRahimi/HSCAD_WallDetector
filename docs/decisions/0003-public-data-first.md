---
id: 0003
date: 2026-10-26
title: Develop on FloorPlanCAD first, then the archive, then transfer between them
status: superseded
supersedes:
superseded-by: 0008
runs: []
---

## Context

The archive cannot be read by agents and can only be processed on the company machine.
The pipeline still has to be built and debugged somewhere, and the thesis needs results
that others can reproduce. FloorPlanCAD is a public set of CAD floor plans with a label
on every vector element, which is the same task.

## Options considered

- **A:** Build directly against the archive, debugging only through aggregate reports
  from the company machine.
- **B:** Train on FloorPlanCAD only and test on the archive.
- **C:** Three stages: develop and benchmark on FloorPlanCAD; run the same pipeline on
  the archive; then measure transfer (FloorPlanCAD only, archive only, FloorPlanCAD
  pretraining with archive fine-tuning), all evaluated on held-out archive drawings.

## Decision

Option C. FloorPlanCAD is the development set and a pretraining source; the claims of
the thesis about the archive rest on held-out archive drawings.

## Evidence

Judgement, not measurement. A is rejected because every bug would cost a round trip to
the company machine, with no agent able to see the data. B is rejected because a low
score on the archive could not be attributed: domain (Chinese residential and
commercial plans versus European medical facilities), scale (normalised crops versus
whole plans in real units) and label source (manual annotation versus HSCAD redraw
matching) all differ at once. C separates these and turns the domain gap into a
measured quantity that bears on sub-question 1.

## Consequences

- One element format with two readers: SVG (FloorPlanCAD) now, DWG (archive) later.
  Everything after reading is shared and is tested on public data first.
- Features must not depend on absolute units.
- The layer-name ablation of sub-question 2 can be run first on FloorPlanCAD, whose SVGs
  keep the original layer names.
- FloorPlanCAD annotations are CC BY-NC 4.0 and its authors do not own the drawings.

## Still unresolved

- Whether the non-commercial licence is compatible with the industry partnership,
  in particular for any model used by Siemens Healthineers. To be checked with the
  supervisors.
- Whether archive test labels can be hand-verified for a small set of drawings, so
  that archive results are not measured against the noise of the matching step.
- Which `semantic-id` values in the downloaded release name which classes. The release
  uses `semantic-id`, not the `semanticId` of the original distribution, and the ID
  tables published with other code do not match its layer names.
