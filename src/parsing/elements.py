"""The element table: one row per drawing primitive, the format every reader produces."""

from __future__ import annotations

from dataclasses import dataclass, fields

import pyarrow as pa

KINDS = ("line", "arc", "circle", "ellipse", "text")

# Coordinates are kept exactly as in the source file. For SVG that means y points down.
# Which columns are set depends on the kind; the rest are null.
SCHEMA = pa.schema(
    [
        pa.field("element_index", pa.int32(), nullable=False),  # document order
        pa.field("kind", pa.string(), nullable=False),
        pa.field("layer", pa.string(), nullable=False),
        pa.field("x0", pa.float64()),  # line and arc start, text anchor
        pa.field("y0", pa.float64()),
        pa.field("x1", pa.float64()),  # line and arc end
        pa.field("y1", pa.float64()),
        pa.field("cx", pa.float64()),  # circle and ellipse centre
        pa.field("cy", pa.float64()),
        pa.field("rx", pa.float64()),  # arc, circle and ellipse radii
        pa.field("ry", pa.float64()),
        pa.field("rotation", pa.float64()),  # degrees, as written in the source
        pa.field("large_arc", pa.bool_()),
        pa.field("sweep", pa.bool_()),
        pa.field("text", pa.string()),
        pa.field("font_size", pa.float64()),
        pa.field("stroke", pa.string()),
        pa.field("semantic_id", pa.int16()),
        pa.field("instance_id", pa.int32()),
    ]
)


@dataclass(frozen=True)
class Element:
    """One primitive of a drawing."""

    kind: str
    layer: str
    x0: float | None = None
    y0: float | None = None
    x1: float | None = None
    y1: float | None = None
    cx: float | None = None
    cy: float | None = None
    rx: float | None = None
    ry: float | None = None
    rotation: float | None = None
    large_arc: bool | None = None
    sweep: bool | None = None
    text: str | None = None
    font_size: float | None = None
    stroke: str | None = None
    semantic_id: int | None = None
    instance_id: int | None = None


_ELEMENT_FIELDS = [field.name for field in fields(Element)]


def to_table(elements: list[Element]) -> pa.Table:
    """Convert elements to an Arrow table with the shared schema."""
    columns: dict[str, list] = {name: [] for name in SCHEMA.names}
    for index, element in enumerate(elements):
        columns["element_index"].append(index)
        for name in _ELEMENT_FIELDS:
            columns[name].append(getattr(element, name))

    return pa.Table.from_pydict(columns, schema=SCHEMA)
