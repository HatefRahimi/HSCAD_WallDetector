"""Read one FloorPlanCAD SVG into elements.

The release has a fixed shape: layer groups (`<g inkscape:label=...>`) directly under the
root, each holding paths, circles, ellipses and text. Every path is a single line
(`M x,y L x,y`) or a single elliptical arc (`M x,y A rx,ry rotation large,sweep x,y`).
Anything else raises ValueError, so a format change shows up as a failed file instead
of silently missing geometry.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from src.parsing.elements import Element

_SVG = "{http://www.w3.org/2000/svg}"
_LAYER_LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"

_NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_SEP = r"[\s,]+"
_LINE = re.compile(rf"^M\s*({_NUMBER}){_SEP}({_NUMBER})\s*L\s*({_NUMBER}){_SEP}({_NUMBER})$")
_ARC = re.compile(
    rf"^M\s*({_NUMBER}){_SEP}({_NUMBER})\s*A\s*({_NUMBER}){_SEP}({_NUMBER}){_SEP}"
    rf"({_NUMBER}){_SEP}([01]){_SEP}([01]){_SEP}({_NUMBER}){_SEP}({_NUMBER})$"
)
_ROTATE = re.compile(rf"^rotate\(\s*({_NUMBER})(?:{_SEP}({_NUMBER}){_SEP}({_NUMBER}))?\s*\)$")
_PIVOT_TOLERANCE = 1e-6


def read_svg(path: Path) -> list[Element]:
    """Return every element of one SVG in document order."""
    root = ET.parse(path).getroot()

    elements = []
    for child in root:
        if child.tag == f"{_SVG}g":
            layer = child.get(_LAYER_LABEL, "")
            for item in child:
                elements.append(_read_item(item, layer))
        else:
            elements.append(_read_item(child, ""))

    return elements


def _read_item(item: ET.Element, layer: str) -> Element:
    """Dispatch on the tag of one drawable element."""
    tag = item.tag.removeprefix(_SVG)
    common = {
        "layer": layer,
        "stroke": item.get("stroke"),
        "semantic_id": _optional_int(item.get("semantic-id")),
        "instance_id": _optional_int(item.get("instance-id")),
    }

    if tag == "path":
        return _read_path(item.get("d", ""), common)
    if tag == "circle":
        radius = float(item.get("r"))
        return Element(
            kind="circle",
            cx=float(item.get("cx")),
            cy=float(item.get("cy")),
            rx=radius,
            ry=radius,
            **common,
        )
    if tag == "ellipse":
        cx = float(item.get("cx"))
        cy = float(item.get("cy"))
        return Element(
            kind="ellipse",
            cx=cx,
            cy=cy,
            rx=float(item.get("rx")),
            ry=float(item.get("ry")),
            rotation=_rotation(item, cx, cy),
            **common,
        )
    if tag == "text":
        x = float(item.get("x"))
        y = float(item.get("y"))
        return Element(
            kind="text",
            x0=x,
            y0=y,
            rotation=_rotation(item, x, y),
            text="".join(item.itertext()).strip(),
            font_size=float(item.get("font-size")),
            **common,
        )

    raise ValueError(f"unsupported element <{tag}>")


def _read_path(d: str, common: dict) -> Element:
    """Parse a single-segment path: one line or one arc."""
    d = d.strip()

    line = _LINE.match(d)
    if line:
        x0, y0, x1, y1 = (float(v) for v in line.groups())
        return Element(kind="line", x0=x0, y0=y0, x1=x1, y1=y1, **common)

    arc = _ARC.match(d)
    if arc:
        x0, y0, rx, ry, rotation, large_arc, sweep, x1, y1 = arc.groups()
        return Element(
            kind="arc",
            x0=float(x0),
            y0=float(y0),
            x1=float(x1),
            y1=float(y1),
            rx=float(rx),
            ry=float(ry),
            rotation=float(rotation),
            large_arc=large_arc == "1",
            sweep=sweep == "1",
            **common,
        )

    raise ValueError(f"unsupported path data {d[:80]!r}")


def _rotation(item: ET.Element, pivot_x: float, pivot_y: float) -> float:
    """Angle of a `rotate(...)` transform about the element's own anchor, 0 if none."""
    transform = item.get("transform")
    if transform is None:
        return 0.0

    match = _ROTATE.match(transform.strip())
    if match is None:
        raise ValueError(f"unsupported transform {transform!r}")

    angle, px, py = match.groups()
    if px is not None:
        off_x = abs(float(px) - pivot_x) > _PIVOT_TOLERANCE
        off_y = abs(float(py) - pivot_y) > _PIVOT_TOLERANCE
        if off_x or off_y:
            raise ValueError(f"rotation pivot is not the element anchor: {transform!r}")

    return float(angle)


def _optional_int(value: str | None) -> int | None:
    """Parse an optional integer attribute."""
    if value is None:
        return None
    return int(value)
