"""Per-element geometric features for the baseline classifier.

Everything is computed inside one drawing, in the drawing's own units, from geometry
alone: no layer names, no colours, no labels. Text contributes only its position.
"""

from __future__ import annotations

import math

import numpy as np
import pyarrow as pa

from src.evaluate.metrics import SCORED_KINDS

FEATURES_VERSION = 1

KIND_CODES = {"line": 0, "arc": 1, "circle": 2, "ellipse": 3}
CROP_SIZE = 100.0
BORDER_TOLERANCE = 1e-6
TOUCH = 0.02  # endpoints closer than this are connected
COLLINEAR_GAP = 0.01
PARALLEL_COS = math.cos(math.radians(3.0))
PERPENDICULAR_COS = math.sin(math.radians(3.0))
MIN_OVERLAP = 0.3  # share of the shorter line that a parallel partner must cover
RADII = (1.0, 3.0, 10.0)
NONE = 10.0  # stands in for "nothing within reach" in distance features
REACH = 10.0  # no feature looks further than this
SEARCH_MARGIN = REACH  # candidates compared per chunk; must be at least REACH
CHUNK = 128
CELL = 5.0  # grid cell for the spatial processing order

FEATURE_NAMES = [
    "kind_line",
    "kind_arc",
    "kind_circle",
    "kind_ellipse",
    "length",
    "log_length",
    "relative_length",
    "chord",
    "orientation_sin2",
    "orientation_cos2",
    "axis_deviation_deg",
    "radius",
    "sweep_deg",
    "radius_ratio",
    "endpoints_on_border",
    *(f"neighbours_within_{r:g}" for r in RADII),
    "arcs_within_3",
    "nearest_arc",
    "texts_within_3",
    "partner_gap",
    "second_partner_gap",
    "partners_within_3",
    "partners_within_10",
    "partner_length_ratio",
    "collinear_within_3",
    "perpendicular_touching",
    "endpoint_degree_min",
    "endpoint_degree_max",
    "drawing_log_elements",
    "drawing_median_line_length",
]


def geometric_rows(table: pa.Table) -> np.ndarray:
    """Indices of the elements that are scored and get features."""
    kinds = table.column("kind").to_pylist()
    return np.array([i for i, k in enumerate(kinds) if k in SCORED_KINDS], dtype=np.int64)


def element_features(table: pa.Table) -> np.ndarray:
    """Feature matrix, one row per geometric element in table order, float32."""
    rows = geometric_rows(table)
    columns = {name: _column(table, name)[rows] for name in ("x0", "y0", "x1", "y1", "cx", "cy")}
    columns.update({name: _column(table, name)[rows] for name in ("rx", "ry")})
    kinds = np.array(table.column("kind").to_pylist(), dtype=object)[rows]
    large_arc = np.array([bool(v) for v in table.column("large_arc").to_pylist()], dtype=bool)[rows]

    p0, p1 = _endpoints(kinds, columns)
    if np.isnan(p0).any() or np.isnan(p1).any():
        raise ValueError("geometric element without coordinates")
    n = len(rows)
    if n == 0:
        return np.zeros((0, len(FEATURE_NAMES)), dtype=np.float32)

    chord = np.linalg.norm(p1 - p0, axis=1)
    is_line = kinds == "line"
    is_arc = kinds == "arc"
    radius = np.where(np.isnan(columns["rx"]), 0.0, columns["rx"])
    sweep = _sweep(chord, radius, large_arc, is_arc)
    length = _length(kinds, chord, radius, sweep, columns)

    line_lengths = length[is_line]
    median_line = float(np.median(line_lengths)) if line_lengths.size else 1.0
    median_line = max(median_line, 1e-9)

    direction = np.zeros_like(p0)
    has_direction = chord > 1e-9
    direction[has_direction] = (p1 - p0)[has_direction] / chord[has_direction, None]
    angle = np.degrees(np.arctan2(direction[:, 1], direction[:, 0])) % 180.0
    axis_deviation = np.minimum(angle % 90.0, 90.0 - angle % 90.0)

    on_border = _on_border(p0).astype(np.float32) + _on_border(p1).astype(np.float32)
    on_border[~(is_line | is_arc)] = 0.0

    texts = _text_points(table)
    context = _context(p0, p1, direction, length, is_line, is_arc, texts)

    out = np.zeros((n, len(FEATURE_NAMES)), dtype=np.float64)
    codes = np.array([KIND_CODES[k] for k in kinds])
    out[np.arange(n), codes] = 1.0
    col = {name: i for i, name in enumerate(FEATURE_NAMES)}
    out[:, col["length"]] = length
    out[:, col["log_length"]] = np.log10(length + 1e-6)
    out[:, col["relative_length"]] = length / median_line
    out[:, col["chord"]] = chord
    out[:, col["orientation_sin2"]] = np.where(has_direction, np.sin(np.radians(2 * angle)), 0)
    out[:, col["orientation_cos2"]] = np.where(has_direction, np.cos(np.radians(2 * angle)), 0)
    out[:, col["axis_deviation_deg"]] = np.where(has_direction, axis_deviation, -1.0)
    out[:, col["radius"]] = radius
    out[:, col["sweep_deg"]] = np.degrees(sweep)
    ry = np.where(np.isnan(columns["ry"]), 0.0, columns["ry"])
    out[:, col["radius_ratio"]] = np.where(radius > 0, ry / np.maximum(radius, 1e-9), 0.0)
    out[:, col["endpoints_on_border"]] = on_border
    for name, values in context.items():
        out[:, col[name]] = values
    out[:, col["drawing_log_elements"]] = math.log10(n)
    out[:, col["drawing_median_line_length"]] = median_line

    return out.astype(np.float32)


def _column(table: pa.Table, name: str) -> np.ndarray:
    """A float column with nulls as NaN."""
    return np.array(table.column(name).to_pylist(), dtype=np.float64)


def _endpoints(kinds: np.ndarray, c: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Segment ends: line and arc endpoints; circles and ellipses collapse to the centre."""
    pointlike = (kinds == "circle") | (kinds == "ellipse")
    x0 = np.where(pointlike, c["cx"], c["x0"])
    y0 = np.where(pointlike, c["cy"], c["y0"])
    x1 = np.where(pointlike, c["cx"], c["x1"])
    y1 = np.where(pointlike, c["cy"], c["y1"])
    return np.stack([x0, y0], axis=1), np.stack([x1, y1], axis=1)


def _sweep(chord: np.ndarray, radius: np.ndarray, large_arc: np.ndarray, is_arc: np.ndarray):
    """Opening angle of each arc in radians, 0 for other kinds."""
    half = np.arcsin(np.clip(chord / np.maximum(2 * radius, 1e-9), 0.0, 1.0))
    sweep = np.where(large_arc, 2 * math.pi - 2 * half, 2 * half)
    return np.where(is_arc, sweep, 0.0)


def _length(kinds, chord, radius, sweep, c) -> np.ndarray:
    """Drawn length: chord for lines, arc length, circumference, ellipse perimeter."""
    ry = np.where(np.isnan(c["ry"]), 0.0, c["ry"])
    return np.select(
        [kinds == "line", kinds == "arc", kinds == "circle", kinds == "ellipse"],
        [chord, radius * sweep, 2 * math.pi * radius, math.pi * (radius + ry)],
    )


def _on_border(points: np.ndarray) -> np.ndarray:
    """Whether a point lies on the crop edge, where the release cuts geometry."""
    near_low = np.abs(points) < BORDER_TOLERANCE
    near_high = np.abs(points - CROP_SIZE) < BORDER_TOLERANCE
    return (near_low | near_high).any(axis=1)


def _text_points(table: pa.Table) -> np.ndarray:
    """Anchor points of text elements."""
    kinds = table.column("kind").to_pylist()
    rows = [i for i, k in enumerate(kinds) if k == "text"]
    if not rows:
        return np.zeros((0, 2))
    x = _column(table, "x0")[rows]
    y = _column(table, "y0")[rows]
    return np.stack([x, y], axis=1)


def _point_to_segment(points: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Distances from points (..., 2) to segments a-b broadcast against them."""
    ab = b - a
    denom = np.sum(ab * ab, axis=-1)
    t = np.sum((points - a) * ab, axis=-1) / np.where(denom > 0, denom, 1.0)
    t = np.clip(np.where(denom > 0, t, 0.0), 0.0, 1.0)
    closest = a + t[..., None] * ab
    return np.linalg.norm(points - closest, axis=-1)


def _context(p0, p1, direction, length, is_line, is_arc, texts) -> dict[str, np.ndarray]:
    """Neighbourhood features, computed chunk by chunk against all elements."""
    n = len(p0)
    mid = (p0 + p1) / 2
    points = np.stack([p0, p1, mid], axis=1)  # (n, 3, 2)
    has_ends = is_line | is_arc
    low = np.minimum(p0, p1)
    high = np.maximum(p0, p1)

    # Chunks of spatially close elements only need candidates near the chunk.
    cell = np.floor(mid / CELL)
    order = np.lexsort((mid[:, 1], cell[:, 1], cell[:, 0]))

    result = {
        **{f"neighbours_within_{r:g}": np.zeros(n) for r in RADII},
        "arcs_within_3": np.zeros(n),
        "nearest_arc": np.full(n, NONE),
        "texts_within_3": np.zeros(n),
        "partner_gap": np.full(n, NONE),
        "second_partner_gap": np.full(n, NONE),
        "partners_within_3": np.zeros(n),
        "partners_within_10": np.zeros(n),
        "partner_length_ratio": np.zeros(n),
        "collinear_within_3": np.zeros(n),
        "perpendicular_touching": np.zeros(n),
        "endpoint_degree_min": np.zeros(n),
        "endpoint_degree_max": np.zeros(n),
    }

    for start in range(0, n, CHUNK):
        rows = order[start : start + CHUNK]
        box_low = low[rows].min(axis=0) - SEARCH_MARGIN
        box_high = high[rows].max(axis=0) + SEARCH_MARGIN
        cols = np.flatnonzero(((high >= box_low) & (low <= box_high)).all(axis=1))
        is_self = rows[:, None] == cols[None, :]
        a0 = p0[rows][:, None, :]
        a1 = p1[rows][:, None, :]

        # Segment distance: closest of the three sample points of either segment.
        from_rows = _point_to_segment(
            points[rows][:, :, None, :], p0[cols][None, None], p1[cols][None, None]
        )
        to_rows = _point_to_segment(
            points[cols][None, :, :, :], a0[:, :, None, :], a1[:, :, None, :]
        )
        distance = np.minimum(from_rows.min(axis=1), to_rows.min(axis=2))  # (chunk, cols)
        distance[is_self] = np.inf

        for r in RADII:
            result[f"neighbours_within_{r:g}"][rows] = (distance <= r).sum(axis=1)
        arc_distance = np.where(is_arc[cols][None, :], distance, np.inf)
        result["arcs_within_3"][rows] = (arc_distance <= 3.0).sum(axis=1)
        result["nearest_arc"][rows] = np.minimum(arc_distance.min(axis=1), NONE)

        near = texts[((texts >= box_low) & (texts <= box_high)).all(axis=1)]
        if len(near):
            text_distance = _point_to_segment(near[None, :, :], a0, a1)
            result["texts_within_3"][rows] = (text_distance <= 3.0).sum(axis=1)

        _line_pairs(result, rows, cols, is_self, p0, direction, length, is_line, distance)

        # Endpoint degree: other elements with an endpoint touching this endpoint.
        ends = np.stack([p0, p1], axis=1)  # (n, 2, 2)
        degrees = []
        for k in range(2):
            gap = np.linalg.norm(ends[cols][None] - ends[rows][:, k][:, None, None, :], axis=-1)
            touching = (gap.min(axis=2) <= TOUCH) & has_ends[cols][None, :] & ~is_self
            degrees.append(touching.sum(axis=1))
        degree = np.stack(degrees, axis=1)
        result["endpoint_degree_min"][rows] = np.where(has_ends[rows], degree.min(axis=1), 0)
        result["endpoint_degree_max"][rows] = np.where(has_ends[rows], degree.max(axis=1), 0)

    return result


def _line_pairs(result, rows, cols, is_self, p0, direction, length, is_line, distance) -> None:
    """Parallel partners, collinear continuations and perpendicular contacts of lines."""
    cos = np.abs(direction[rows] @ direction[cols].T)  # (chunk, cols)
    both_lines = is_line[rows][:, None] & is_line[cols][None, :] & ~is_self
    parallel = both_lines & (cos >= PARALLEL_COS)

    # Offset of the other line's endpoints from this line's axis, and their projection.
    u = direction[rows]
    rel0 = p0[cols][None, :, :] - p0[rows][:, None, :]
    rel1 = rel0 + (direction[cols] * length[cols][:, None])[None, :, :]
    cross0 = np.abs(rel0[..., 0] * u[:, None, 1] - rel0[..., 1] * u[:, None, 0])
    cross1 = np.abs(rel1[..., 0] * u[:, None, 1] - rel1[..., 1] * u[:, None, 0])
    gap = (cross0 + cross1) / 2
    t0 = np.sum(rel0 * u[:, None, :], axis=-1)
    t1 = np.sum(rel1 * u[:, None, :], axis=-1)
    lo = np.maximum(np.minimum(t0, t1), 0.0)
    hi = np.minimum(np.maximum(t0, t1), length[rows][:, None])
    shorter = np.minimum(length[rows][:, None], length[cols][None, :])
    overlap = np.clip(hi - lo, 0.0, None) / np.maximum(shorter, 1e-9)

    partner = parallel & (overlap >= MIN_OVERLAP) & (gap > COLLINEAR_GAP) & (gap <= REACH)
    partner_gap = np.where(partner, gap, np.inf)
    # Stable, so equal gaps resolve to the lowest element index however columns are cut.
    order = np.argsort(partner_gap, axis=1, kind="stable")
    first = partner_gap[np.arange(len(rows)), order[:, 0]]
    second = partner_gap[np.arange(len(rows)), order[:, 1]] if partner_gap.shape[1] > 1 else first
    result["partner_gap"][rows] = np.minimum(first, NONE)
    result["second_partner_gap"][rows] = np.minimum(second, NONE)
    result["partners_within_3"][rows] = (partner_gap <= 3.0).sum(axis=1)
    result["partners_within_10"][rows] = (partner_gap <= 10.0).sum(axis=1)
    found = np.isfinite(first)
    ratio = length[cols][order[:, 0]] / np.maximum(length[rows], 1e-9)
    result["partner_length_ratio"][rows] = np.where(found, ratio, 0.0)

    collinear = parallel & (gap <= COLLINEAR_GAP) & (distance <= 3.0)
    result["collinear_within_3"][rows] = collinear.sum(axis=1)
    perpendicular = both_lines & (cos <= PERPENDICULAR_COS) & (distance <= TOUCH)
    result["perpendicular_touching"][rows] = perpendicular.sum(axis=1)
