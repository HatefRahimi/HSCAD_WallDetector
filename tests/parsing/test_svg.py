from __future__ import annotations

from pathlib import Path

import pytest

from src.parsing.elements import SCHEMA, to_table
from src.parsing.svg import read_svg

HEADER = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<svg viewBox="0 0 100.0 100.0" xmlns="http://www.w3.org/2000/svg" '
    'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">\n'
)


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "0001-0001.svg"
    path.write_text(HEADER + body + "</svg>\n", encoding="utf-8")
    return path


def test_reads_every_kind_with_its_layer(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        '<g id="layerWALL" inkscape:groupmode="layer" inkscape:label="WALL">'
        '<path d="M 1.5,2.0 L 10.0,2.0" stroke="rgb(1,2,3)" semantic-id="1" instance-id="-1"/>'
        '<path d="M 0.0,10.0 A 5.0,5.0 0.0 0,1 5.0,15.0" stroke="rgb(0,0,0)"/>'
        "</g>"
        '<g id="layerX" inkscape:groupmode="layer" inkscape:label="门窗">'
        '<circle cx="3.0" cy="4.0" r="0.5" semantic-id="23" instance-id="7"/>'
        '<ellipse cx="8.0" cy="9.0" rx="2.0" ry="1.0" transform="rotate(-90.0,8.0,9.0)"/>'
        '<text x="20.0" y="30.0" font-size="2" transform="rotate(-0.0,20.0,30.0)">卧室</text>'
        "</g>",
    )

    line, arc, circle, ellipse, text = read_svg(path)

    assert (line.kind, line.layer, line.x0, line.y0, line.x1, line.y1) == (
        "line",
        "WALL",
        1.5,
        2.0,
        10.0,
        2.0,
    )
    assert (line.semantic_id, line.instance_id, line.stroke) == (1, -1, "rgb(1,2,3)")
    assert (arc.kind, arc.rx, arc.ry, arc.large_arc, arc.sweep) == ("arc", 5.0, 5.0, False, True)
    assert (arc.x1, arc.y1, arc.semantic_id) == (5.0, 15.0, None)
    assert (circle.kind, circle.layer, circle.rx, circle.ry) == ("circle", "门窗", 0.5, 0.5)
    assert (circle.semantic_id, circle.instance_id) == (23, 7)
    assert (ellipse.kind, ellipse.rotation, ellipse.rx, ellipse.ry) == ("ellipse", -90.0, 2.0, 1.0)
    assert (text.kind, text.text, text.x0, text.y0, text.font_size) == (
        "text",
        "卧室",
        20.0,
        30.0,
        2.0,
    )


def test_reads_exponent_notation(tmp_path: Path) -> None:
    path = _write(tmp_path, '<g inkscape:label="A"><path d="M 1e-05,2.5E+01 L 3,4"/></g>')

    (line,) = read_svg(path)

    assert (line.x0, line.y0, line.x1, line.y1) == (1e-05, 25.0, 3.0, 4.0)


@pytest.mark.parametrize(
    "body",
    [
        '<g inkscape:label="A"><path d="M 0,0 L 1,1 L 2,2"/></g>',
        '<g inkscape:label="A"><path d="M 0,0 C 1,1 2,2 3,3"/></g>',
        '<g inkscape:label="A"><polygon points="0,0 1,1"/></g>',
        '<g inkscape:label="A"><ellipse cx="1" cy="1" rx="1" ry="1" transform="scale(2)"/></g>',
        (
            '<g inkscape:label="A"><ellipse cx="1" cy="1" rx="1" ry="1" '
            'transform="rotate(30,5,5)"/></g>'
        ),
    ],
)
def test_rejects_what_it_cannot_represent(tmp_path: Path, body: str) -> None:
    path = _write(tmp_path, body)

    with pytest.raises(ValueError):
        read_svg(path)


def test_table_follows_schema_and_numbers_elements(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        '<g inkscape:label="A"><path d="M 0,0 L 1,1"/><circle cx="1" cy="1" r="1"/></g>',
    )

    table = to_table(read_svg(path))

    assert table.schema == SCHEMA
    assert table.column("element_index").to_pylist() == [0, 1]
    assert table.column("kind").to_pylist() == ["line", "circle"]
