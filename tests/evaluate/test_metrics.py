from __future__ import annotations

import pytest

from src.evaluate.metrics import ClassScores, class_of, score

CLASSES = {"wall": [1], "door": [3, 4, 5, 6, 7, 8], "window": [9, 10, 11, 12]}


def test_class_of_maps_ids_and_falls_back_to_other() -> None:
    assert class_of(1, CLASSES) == "wall"
    assert class_of(4, CLASSES) == "door"
    assert class_of(12, CLASSES) == "window"
    assert class_of(2, CLASSES) == "other"
    assert class_of(None, CLASSES) == "other"


def test_scores_match_a_hand_computed_example() -> None:
    true = ["wall", "wall", "wall", "wall", "door", "door", "other", "other", "window"]
    pred = ["wall", "wall", "wall", "other", "door", "wall", "wall", "other", "other"]
    # wall:   TP 3 (first three), FP 2 (door->wall, other->wall), FN 1 (wall->other)
    # door:   TP 1, FP 0, FN 1 (door->wall)
    # window: TP 0, FP 0, FN 1

    scores = score(true, pred, ["wall", "door", "window"])

    assert scores["wall"] == ClassScores(tp=3, fp=2, fn=1)
    assert scores["wall"].precision == pytest.approx(3 / 5)
    assert scores["wall"].recall == pytest.approx(3 / 4)
    assert scores["wall"].f1 == pytest.approx(2 * (3 / 5) * (3 / 4) / (3 / 5 + 3 / 4))
    assert scores["door"] == ClassScores(tp=1, fp=0, fn=1)
    assert (scores["door"].precision, scores["door"].recall) == (1.0, 0.5)
    assert scores["window"] == ClassScores(tp=0, fp=0, fn=1)


def test_empty_denominators_score_zero() -> None:
    scores = ClassScores(tp=0, fp=0, fn=0)

    assert (scores.precision, scores.recall, scores.f1) == (0.0, 0.0, 0.0)


def test_mismatched_lengths_and_empty_input_are_errors() -> None:
    with pytest.raises(ValueError):
        score(["wall"], ["wall", "other"], ["wall"])
    with pytest.raises(ValueError):
        score([], [], ["wall"])
