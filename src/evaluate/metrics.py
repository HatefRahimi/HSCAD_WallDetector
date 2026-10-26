"""Per-element precision, recall and F1 (decision 0009).

FROZEN: changing anything here needs a decision record first (CODING.md section 15).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

OTHER = "other"
SCORED_KINDS = frozenset({"line", "arc", "circle", "ellipse"})


def class_of(semantic_id: int | None, classes: Mapping[str, Iterable[int]]) -> str:
    """The evaluated class of one element, or `other`."""
    if semantic_id is None:
        return OTHER
    for name, ids in classes.items():
        if semantic_id in ids:
            return name
    return OTHER


@dataclass(frozen=True)
class ClassScores:
    """Counts for one class and the scores derived from them."""

    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p = self.precision
        r = self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


def score(true: Iterable[str], predicted: Iterable[str], classes: Iterable[str]) -> dict:
    """Pooled scores per class over paired true and predicted labels."""
    names = list(classes)
    counts = {name: [0, 0, 0] for name in names}  # tp, fp, fn

    pairs = 0
    for t, p in zip(true, predicted, strict=True):
        pairs += 1
        if t == p:
            if t in counts:
                counts[t][0] += 1
            continue
        if p in counts:
            counts[p][1] += 1
        if t in counts:
            counts[t][2] += 1

    if pairs == 0:
        raise ValueError("nothing to score")

    return {name: ClassScores(*counts[name]) for name in names}
