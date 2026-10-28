#!/usr/bin/env python3
"""Break down a baseline model's validation errors and draw a few drawings.

Run from the repository root:
    python -m scripts.analyze_errors --config configs/default.yaml \
        --model-run 2026-10-28-baseline-hgb

Only the validation fold is used. Counts go to a run record. The drawings are
written as SVG to the cache, outside the repository, because they reproduce
dataset content.
"""

from __future__ import annotations

import argparse
import logging
import math
import pickle
from collections import Counter
from itertools import pairwise
from pathlib import Path

import numpy as np
import yaml

from scripts.log_run import log_run
from scripts.train_baseline import read_folds
from src.graph.dataset import NO_LABEL, feature_path, load_fold
from src.graph.features import FEATURE_NAMES, NONE, geometric_rows
from src.parsing import cache

log = logging.getLogger(__name__)

COL = {name: i for i, name in enumerate(FEATURE_NAMES)}
LENGTH_EDGES = (0.0, 1.0, 3.0, 10.0, 30.0, math.inf)
MIN_WALLS_PER_DRAWING = 50  # drawings with fewer true walls are too small to rank
DRAWINGS_PER_GROUP = 3
TOP_SOURCES = 10

# Colours of the drawings: wall outcome first, everything else muted.
CORRECT_WALL = "#2e7d32"
MISSED_WALL = "#d32f2f"
FALSE_WALL = "#1565c0"
OTHER = "#b0b0b0"
SVG_HEADER = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="1000" height="1000">'
    '<rect width="100" height="100" fill="white"/>'
)


def _facets(features: np.ndarray) -> dict[str, np.ndarray]:
    """Boolean masks that split the elements by one geometric property each."""
    facets = {
        f"kind_{kind}": features[:, COL[f"kind_{kind}"]] == 1
        for kind in ("line", "arc", "circle", "ellipse")
    }
    length = features[:, COL["length"]]
    for low, high in pairwise(LENGTH_EDGES):
        facets[f"length_{low:g}_to_{high:g}"] = (length >= low) & (length < high)

    on_border = features[:, COL["endpoints_on_border"]] > 0
    facets["on_border"] = on_border
    facets["off_border"] = ~on_border
    with_partner = features[:, COL["partner_gap"]] < NONE
    facets["with_partner"] = with_partner
    facets["without_partner"] = ~with_partner
    facets["isolated"] = features[:, COL["endpoint_degree_max"]] == 0
    return facets


def _breakdown(true: np.ndarray, predicted: np.ndarray, facets: dict[str, np.ndarray]) -> dict:
    """Recall, precision and share of all misses and false alarms, per facet, for one class."""
    total_fn = int((true & ~predicted).sum())
    total_fp = int((~true & predicted).sum())
    out = {}
    for name, mask in facets.items():
        tp = int((true & predicted & mask).sum())
        fn = int((true & ~predicted & mask).sum())
        fp = int((~true & predicted & mask).sum())
        out[name] = {
            "support": tp + fn,
            "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
            "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
            "share_of_misses": round(fn / total_fn, 4) if total_fn else 0.0,
            "share_of_false_alarms": round(fp / total_fp, 4) if total_fp else 0.0,
        }
    return out


def _per_drawing_wall_f1(true: np.ndarray, predicted: np.ndarray, drawing: np.ndarray):
    """Wall F1 and true wall count of every drawing, indexed by drawing number."""
    count = np.bincount(drawing)
    tp = np.bincount(drawing, weights=true & predicted, minlength=len(count))
    fn = np.bincount(drawing, weights=true & ~predicted, minlength=len(count))
    fp = np.bincount(drawing, weights=~true & predicted, minlength=len(count))
    denominator = 2 * tp + fn + fp
    f1 = np.divide(2 * tp, denominator, out=np.zeros_like(tp), where=denominator > 0)
    return f1, (tp + fn).astype(np.int64)


def _element_svg(kind: str, row: dict, colour: str, width: float) -> str:
    stroke = f'fill="none" stroke="{colour}" stroke-width="{width}"'
    if kind == "line":
        return (
            f'<line x1="{row["x0"]}" y1="{row["y0"]}" x2="{row["x1"]}" y2="{row["y1"]}" {stroke}/>'
        )
    if kind == "arc":
        large, sweep = int(bool(row["large_arc"])), int(bool(row["sweep"]))
        return (
            f'<path d="M {row["x0"]} {row["y0"]} A {row["rx"]} {row["ry"]} 0 {large} {sweep} '
            f'{row["x1"]} {row["y1"]}" {stroke}/>'
        )
    rotation = row["rotation"] or 0.0
    return (
        f'<ellipse cx="{row["cx"]}" cy="{row["cy"]}" rx="{row["rx"]}" ry="{row["ry"]}" '
        f'transform="rotate({rotation} {row["cx"]} {row["cy"]})" {stroke}/>'
    )


def _draw(cache_dir: Path, digest: str, true: np.ndarray, predicted: np.ndarray, path: Path):
    """Write one drawing as SVG, coloured by wall outcome."""
    table = cache.load(cache_dir, digest)
    rows = geometric_rows(table).tolist()
    data = table.to_pylist()
    parts = [SVG_HEADER]
    # Muted elements first, so the coloured outcomes are drawn on top.
    order = sorted(range(len(rows)), key=lambda i: bool(true[i] or predicted[i]))
    for i in order:
        if true[i] and predicted[i]:
            colour, width = CORRECT_WALL, 0.25
        elif true[i]:
            colour, width = MISSED_WALL, 0.35
        elif predicted[i]:
            colour, width = FALSE_WALL, 0.35
        else:
            colour, width = OTHER, 0.1
        row = data[rows[i]]
        parts.append(_element_svg(row["kind"], row, colour, width))
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--model-run", required=True, help="run ID of the trained model")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    dataset = config["public"]["floorplancad"]
    cache_dir = Path(dataset["cache"])
    classes = dataset["classes"]
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with open(cache_dir / "models" / f"{args.model_run}.pkl", "rb") as handle:
        model = pickle.load(handle)

    drawings = read_folds(config["split"]["floorplancad_run"])["val"]
    val = load_fold(cache_dir, drawings, classes)
    predicted = model.predict(val.features)
    semantic_ids = np.concatenate(
        [np.load(feature_path(cache_dir, digest))["semantic_ids"] for _, digest in drawings]
    )
    names = val.class_names
    log.info("val %s", val.features.shape)

    metrics: dict = {"elements": len(val.labels), "drawings": len(drawings)}
    metrics["confusion"] = {
        f"{names[t]}_as_{names[p]}": int(((val.labels == t) & (predicted == p)).sum())
        for t in range(len(names))
        for p in range(len(names))
    }

    facets = _facets(val.features)
    for index, name in enumerate(names[1:], 1):
        true, hit = val.labels == index, predicted == index
        metrics[f"{name}_by_facet"] = _breakdown(true, hit, facets)

    wall = names.index("wall")
    true_wall, predicted_wall = val.labels == wall, predicted == wall
    false_wall_sources = Counter(semantic_ids[~true_wall & predicted_wall].tolist())
    metrics["false_wall_semantic_ids"] = {
        ("none" if sid == NO_LABEL else str(sid)): count
        for sid, count in false_wall_sources.most_common(TOP_SOURCES)
    }

    f1, walls = _per_drawing_wall_f1(true_wall, predicted_wall, val.drawing)
    ranked = np.flatnonzero(walls >= MIN_WALLS_PER_DRAWING)
    ranked = ranked[np.lexsort((ranked, f1[ranked]))]
    misses = np.bincount(val.drawing, weights=true_wall & ~predicted_wall)
    worst_tenth = ranked[: max(1, len(ranked) // 10)]
    metrics["per_drawing_wall_f1"] = {
        "drawings_ranked": len(ranked),
        "min_walls": MIN_WALLS_PER_DRAWING,
        **{f"p{q}": round(float(np.percentile(f1[ranked], q)), 4) for q in (10, 25, 50, 75, 90)},
        "worst_tenth_share_of_misses": round(float(misses[worst_tenth].sum() / misses.sum()), 4),
    }

    middle = len(ranked) // 2
    chosen = {
        "worst": ranked[:DRAWINGS_PER_GROUP],
        "median": ranked[middle : middle + DRAWINGS_PER_GROUP],
    }
    metrics["drawn"] = {
        group: {drawings[i][0]: round(float(f1[i]), 4) for i in numbers}
        for group, numbers in chosen.items()
    }

    run_dir = log_run(
        name="baseline-errors",
        config={
            "config_file": args.config,
            "model_run": args.model_run,
            "fold": "val",
            "length_edges": [str(edge) for edge in LENGTH_EDGES],
            "min_walls_per_drawing": MIN_WALLS_PER_DRAWING,
        },
        metrics=metrics,
        notes="Validation error breakdown of the gradient-boosting baseline.",
    )

    out_dir = cache_dir / "error-drawings" / run_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    for group, numbers in chosen.items():
        for i in numbers:
            drawing_id, digest = drawings[i]
            mask = val.drawing == i
            name = f"{group}-{drawing_id.replace('/', '_')}.svg"
            _draw(cache_dir, digest, true_wall[mask], predicted_wall[mask], out_dir / name)
    log.info("drawings written to %s", out_dir)


if __name__ == "__main__":
    main()
