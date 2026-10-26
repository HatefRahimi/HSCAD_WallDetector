from __future__ import annotations

import random

import pytest

from src.evaluate.splits import Drawing, assign_folds, deduplicate, group_of


def _drawing(folder: str, namespace: str, prefix: str, index: int, content: str) -> Drawing:
    return Drawing(
        drawing_id=f"{folder}/{prefix}-{index:04d}",
        source=f"{namespace}/{prefix}",
        sha256=content,
    )


def _dataset(seed: int = 0) -> list[Drawing]:
    """Sources of varying size in two namespaces, plus copies that link sources."""
    rng = random.Random(seed)
    drawings = []
    for n in range(60):
        prefix = f"{n:04d}"
        for i in range(rng.randint(1, 30)):
            drawings.append(_drawing("train-00", "a", prefix, i, f"a-{prefix}-{i}"))
        for i in range(rng.randint(1, 30)):
            folder = "test-00" if i % 3 == 0 else "train-01"
            drawings.append(_drawing(folder, "b", prefix, i, f"b-{prefix}-{i}"))

    # Copies: a/0007-0000 reappears in namespace b under another prefix and index,
    # and b/0011-0000 reappears inside namespace b under prefix 0042.
    drawings.append(_drawing("test-00", "b", "0050", 900, "a-0007-0"))
    drawings.append(_drawing("train-01", "b", "0042", 901, "b-0011-0"))
    return drawings


def test_group_of_merges_sources_that_share_a_file() -> None:
    drawings = [
        _drawing("train-00", "a", "0001", 1, "x"),
        _drawing("train-00", "a", "0002", 1, "y"),
        _drawing("test-00", "b", "0009", 1, "x"),
        _drawing("test-00", "b", "0009", 2, "z"),
    ]

    groups = group_of(drawings)

    assert groups["train-00/0001-0001"] == groups["test-00/0009-0001"]
    assert groups["test-00/0009-0002"] == groups["train-00/0001-0001"]
    assert groups["train-00/0002-0001"] != groups["train-00/0001-0001"]


def test_deduplicate_keeps_the_smallest_drawing_id() -> None:
    drawings = [
        _drawing("train-01", "b", "0003", 1, "x"),
        _drawing("test-00", "b", "0004", 1, "x"),
        _drawing("train-00", "a", "0001", 1, "y"),
    ]

    kept = deduplicate(drawings)

    assert [d.drawing_id for d in kept] == ["test-00/0004-0001", "train-00/0001-0001"]


def test_same_seed_gives_the_same_folds_and_another_seed_does_not() -> None:
    drawings = _dataset()

    first = assign_folds(drawings, seed=7, test_fraction=0.2, val_fraction=0.1)
    again = assign_folds(drawings, seed=7, test_fraction=0.2, val_fraction=0.1)
    other = assign_folds(drawings, seed=8, test_fraction=0.2, val_fraction=0.1)

    assert first == again
    assert first != other


def test_input_order_does_not_change_the_folds() -> None:
    drawings = _dataset()
    shuffled = drawings[:]
    random.Random(1).shuffle(shuffled)

    assert assign_folds(drawings, 7, 0.2, 0.1) == assign_folds(shuffled, 7, 0.2, 0.1)


def test_no_group_and_no_drawing_spans_two_folds() -> None:
    drawings = _dataset()
    groups = group_of(drawings)

    folds = assign_folds(drawings, seed=7, test_fraction=0.2, val_fraction=0.1)

    fold_of_group: dict[str, set[str]] = {}
    for drawing_id, fold in folds.items():
        fold_of_group.setdefault(groups[drawing_id], set()).add(fold)
    assert all(len(f) == 1 for f in fold_of_group.values())


def test_copies_land_in_one_fold_and_appear_once() -> None:
    drawings = _dataset()

    folds = assign_folds(drawings, seed=7, test_fraction=0.2, val_fraction=0.1)

    # Each content appears once among the assigned drawings.
    contents = [d.sha256 for d in drawings if d.drawing_id in folds]
    assert len(contents) == len(set(contents))
    # Sources linked by a copy share a fold, across namespaces too.
    for linked in ({"a/0007", "b/0050"}, {"b/0011", "b/0042"}):
        members = [d for d in drawings if d.source in linked and d.drawing_id in folds]
        assert {d.source for d in members} == linked
        assert len({folds[d.drawing_id] for d in members}) == 1


def test_every_distinct_content_is_assigned_exactly_once() -> None:
    drawings = _dataset()

    folds = assign_folds(drawings, seed=7, test_fraction=0.2, val_fraction=0.1)

    assert set(folds) == {d.drawing_id for d in deduplicate(drawings)}
    assert set(folds.values()) == {"train", "val", "test"}


def test_fold_sizes_overshoot_by_at_most_one_group() -> None:
    drawings = _dataset()
    groups = group_of(drawings)
    unique = deduplicate(drawings)
    largest = max(sum(1 for d in unique if groups[d.drawing_id] == g) for g in set(groups.values()))

    folds = assign_folds(drawings, seed=7, test_fraction=0.2, val_fraction=0.1)

    sizes = {fold: sum(1 for f in folds.values() if f == fold) for fold in ("test", "val")}
    assert 0.2 * len(unique) <= sizes["test"] < 0.2 * len(unique) + largest
    assert 0.1 * len(unique) <= sizes["val"] < 0.1 * len(unique) + largest


@pytest.mark.parametrize("test_fraction, val_fraction", [(-0.1, 0.1), (0.5, 0.5), (0.2, -0.1)])
def test_rejects_impossible_fractions(test_fraction: float, val_fraction: float) -> None:
    with pytest.raises(ValueError):
        assign_folds(_dataset(), 7, test_fraction, val_fraction)
