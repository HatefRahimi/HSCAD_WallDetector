from __future__ import annotations

import math
import random

import numpy as np
import pytest

from src.graph import features
from src.graph.features import FEATURE_NAMES, NONE, element_features
from src.parsing.elements import Element, to_table

COL = {name: i for i, name in enumerate(FEATURE_NAMES)}


def _line(x0: float, y0: float, x1: float, y1: float) -> Element:
    return Element(kind="line", layer="", x0=x0, y0=y0, x1=x1, y1=y1)


def _features(*elements: Element) -> np.ndarray:
    return element_features(to_table(list(elements)))


def test_a_wall_pair_finds_each_other() -> None:
    f = _features(_line(10, 10, 20, 10), _line(10, 12, 20, 12), _line(50, 50, 50, 60))

    assert f[0, COL["partner_gap"]] == pytest.approx(2.0)
    assert f[1, COL["partner_gap"]] == pytest.approx(2.0)
    assert f[0, COL["partner_length_ratio"]] == pytest.approx(1.0)
    assert f[0, COL["partners_within_3"]] == 1
    assert f[2, COL["partner_gap"]] == NONE
    assert f[2, COL["partners_within_10"]] == 0


def test_partners_must_overlap_and_collinear_lines_are_not_partners() -> None:
    f = _features(_line(0, 0, 10, 0), _line(30, 2, 40, 2), _line(11, 0, 20, 0))

    assert f[0, COL["partner_gap"]] == NONE  # parallel at gap 2, but no overlap
    assert f[0, COL["collinear_within_3"]] == 1  # the continuation at gap 1 along


def test_quarter_arc_has_sweep_and_length() -> None:
    arc = Element(
        kind="arc", layer="", x0=5, y0=0, x1=0, y1=5, rx=5, ry=5, large_arc=False, sweep=True
    )

    f = _features(arc)

    assert f[0, COL["kind_arc"]] == 1
    assert f[0, COL["sweep_deg"]] == pytest.approx(90.0, abs=1e-3)
    assert f[0, COL["length"]] == pytest.approx(5 * math.pi / 2, rel=1e-5)
    assert f[0, COL["radius"]] == 5


def test_corner_contacts_and_border() -> None:
    f = _features(_line(40, 40, 50, 40), _line(50, 40, 50, 30), _line(90, 70, 100, 70))

    assert f[0, COL["endpoint_degree_max"]] == 1
    assert f[0, COL["endpoint_degree_min"]] == 0
    assert f[0, COL["perpendicular_touching"]] == 1
    assert f[2, COL["endpoints_on_border"]] == 1
    assert f[0, COL["endpoints_on_border"]] == 0


def test_text_counts_only_by_position_and_is_not_scored() -> None:
    text = Element(kind="text", layer="", x0=15, y0=11, text="M1021", font_size=2)

    f = _features(_line(10, 10, 20, 10), text)

    assert f.shape == (1, len(FEATURE_NAMES))
    assert f[0, COL["texts_within_3"]] == 1


def test_search_margin_never_changes_features(monkeypatch: pytest.MonkeyPatch) -> None:
    rng = random.Random(3)
    elements = []
    for _ in range(400):
        x, y = rng.uniform(0, 100), rng.uniform(0, 100)
        if rng.random() < 0.5:
            elements.append(_line(x, y, x + rng.choice([0, 1]) * rng.uniform(1, 40), y + 2))
        else:
            elements.append(_line(x, y, x, y + rng.uniform(1, 40)))
    table = to_table(elements)

    restricted = element_features(table)
    monkeypatch.setattr(features, "SEARCH_MARGIN", 1e9)
    exhaustive = element_features(table)

    np.testing.assert_array_equal(restricted, exhaustive)


def test_missing_coordinates_are_an_error() -> None:
    with pytest.raises(ValueError):
        _features(Element(kind="line", layer="", x0=0, x1=1))
