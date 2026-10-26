# Archive conventions and parser requirements

Working notes for engineering. Not a thesis source: anything here that the thesis needs
must first be confirmed and written up as a decision record.

## Where labels can come from

Each archive DWG may hold the customer's original drawing next to an HSCAD redraw of
the same plan. The redraw uses fixed layer names, so it can act as weak supervision for
the customer geometry:

| Class | HSCAD layers (case-insensitive) |
|---|---|
| wall | `A_Walls`, `A_Wall` |
| door | `A_Doors`, `A_Door` |
| window | `A_Windows`, `A_Window`, `A_Openings` |

HSCAD layers that are neither labels nor customer geometry, by prefix: `L08_`, `L90_`,
`L80_`, `Border_`, `Defpoints`, `-INFO-`, `A_Annotations`, `A_Ceiling`, `A_Floor`,
`A_Slab`, `A_MassElements`, `A_Wall_Mounted`, `A_Shielding`, `A_Columns`.

To confirm: whether this list is complete, and how often a drawing has a redraw at all.

## Requirements for the parser

- Explode block references recursively; doors and windows usually live in blocks.
- Read `$INSUNITS` and normalise to one unit; any distance threshold depends on it.
- Transform OCS entities (arcs, circles, lightweight polylines) with extrusion (0,0,-1).
- Lengths of polylines must include bulge arcs.
- Keep hatches and solid fills with geometry; wall fills are a likely signal.
- Keep raw layer name, colour, lineweight and linetype; resolve ByLayer and ByBlock.
- Catch failures per drawing, capture reader notifications, write a manifest.
- No file paths or customer names in the output; key drawings by an anonymised ID.
- No features and no labels in the parser; both belong to the Python side.

## Requirements for labelling and features

- Label assignment is a separate, configurable step, and reports its own noise
  (distribution of match distances, unmatched label geometry).
- The same neighbourhood definition is used for training and for prediction.
- Splits are by drawing or customer, never by entity (AGENTS.md §2).
