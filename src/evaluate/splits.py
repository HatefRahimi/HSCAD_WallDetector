"""Train, validation and test folds for FloorPlanCAD (decisions 0006 and 0007).

FROZEN: changing anything here needs a decision record first (CODING.md section 15).
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass

FOLDS = ("train", "val", "test")


@dataclass(frozen=True)
class Drawing:
    """The identity of one parsed file, as far as splitting needs it."""

    drawing_id: str  # <folder>/<stem>
    source: str  # <namespace>/<prefix>
    sha256: str


def group_of(drawings: list[Drawing]) -> dict[str, str]:
    """Map each drawing to its group: sources linked by an identical file are merged."""
    parent = {d.source: d.source for d in drawings}

    def find(source: str) -> str:
        while parent[source] != source:
            parent[source] = parent[parent[source]]
            source = parent[source]
        return source

    first_source_of_content: dict[str, str] = {}
    for drawing in sorted(drawings, key=lambda d: d.drawing_id):
        first = first_source_of_content.setdefault(drawing.sha256, drawing.source)
        a = find(first)
        b = find(drawing.source)
        if a != b:
            # Smaller ID becomes the root, so group names do not depend on input order.
            parent[max(a, b)] = min(a, b)

    return {d.drawing_id: find(d.source) for d in drawings}


def deduplicate(drawings: list[Drawing]) -> list[Drawing]:
    """Keep one drawing per distinct content: the one with the smallest drawing ID."""
    kept: dict[str, Drawing] = {}
    for drawing in sorted(drawings, key=lambda d: d.drawing_id):
        kept.setdefault(drawing.sha256, drawing)
    return sorted(kept.values(), key=lambda d: d.drawing_id)


def assign_folds(
    drawings: list[Drawing],
    seed: int,
    test_fraction: float,
    val_fraction: float,
) -> dict[str, str]:
    """Fold of every deduplicated drawing. Whole groups only; fractions count drawings."""
    if test_fraction < 0 or val_fraction < 0 or test_fraction + val_fraction >= 1:
        raise ValueError(f"bad fractions: test {test_fraction}, val {val_fraction}")

    groups = group_of(drawings)
    unique = deduplicate(drawings)

    members: dict[str, list[str]] = defaultdict(list)
    for drawing in unique:
        members[groups[drawing.drawing_id]].append(drawing.drawing_id)

    order = sorted(members)
    random.Random(seed).shuffle(order)

    targets = {
        "test": math.ceil(test_fraction * len(unique)),
        "val": math.ceil(val_fraction * len(unique)),
    }
    filled = {"test": 0, "val": 0}

    fold_of: dict[str, str] = {}
    for group in order:
        fold = "train"
        for candidate in ("test", "val"):
            if filled[candidate] < targets[candidate]:
                fold = candidate
                break

        if fold != "train":
            filled[fold] += len(members[group])
        for drawing_id in members[group]:
            fold_of[drawing_id] = fold

    return fold_of
