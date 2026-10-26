---
id: 0005
date: 2026-10-26
title: Map FloorPlanCAD semantic-id 1 to wall, 3 to 8 to door, 9 to 12 to window
status: accepted
supersedes:
superseded-by:
runs: [2026-10-26-floorplancad-class-audit]
---

## Context

The downloaded release labels elements with `semantic-id` numbers but ships no table
of names. The tables published with other code (SymPoint, CADTransformer) read a
`semanticId` attribute and put wall at 33; applied to this release they would label
walls as something else. This resolves the class question left open in 0003.

## Options considered

- **A:** Use the published table as is.
- **B:** Derive the mapping from this release: layer names for evidence, rendered
  crops for the classes that layer names cannot separate.

## Decision

Option B. Wall is id 1. Door is ids 3 to 8. Window is ids 9 to 12. All other ids,
including 2 (curtain wall), count as other. The mapping lives in `configs/default.yaml`.

## Evidence

Run `2026-10-26-floorplancad-class-audit`, all files: id 1 sits mainly on wall layers
(`id01_wall_layer_share`); ids 30 to 32 sit mainly on stair layers; furniture-range
ids sit on neither. Layer names do not separate doors from windows, since many
drawings keep both on one layer (`id03_*` to `id12_*` split between the two).

That split rests on inspection, not measurement: crops rendered with one id
highlighted show swing arcs for ids 3 and 4 and short wall inserts for id 9. The whole
pattern matches the published order with wall and curtain wall moved to ids 1 and 2
and every other class shifted up by two.

## Consequences

- Door and window results inherit the weaker evidence behind their ids; the thesis
  must say how the mapping was obtained.
- Id 5 (sliding door under the shifted order) sits mostly on window layers. It is the
  least certain member of the door group.

## Still unresolved

- Whether curtain wall (id 2) should count as wall. This depends on whether HSCAD
  walls in the archive include curtain walls, and is decided when archive labels are
  defined.
- Ids 33 to 35 are not identified. They are outside the evaluated classes.
