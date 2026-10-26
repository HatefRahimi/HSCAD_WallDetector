from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.graph.dataset import build_features, load_fold
from src.parsing import cache
from src.parsing.elements import Element, to_table

CLASSES = {"wall": [1], "door": [3, 4], "window": [9]}


def _store(cache_dir: Path, digest: str, elements: list[Element]) -> None:
    cache.store(cache_dir, digest, to_table(elements))


def test_labels_follow_the_class_mapping_and_skip_text(tmp_path: Path) -> None:
    elements = [
        Element(kind="line", layer="", x0=0, y0=0, x1=1, y1=0, semantic_id=1),
        Element(kind="text", layer="", x0=0, y0=0, text="A", font_size=1),
        Element(kind="line", layer="", x0=0, y0=2, x1=1, y1=2, semantic_id=4),
        Element(kind="line", layer="", x0=0, y0=4, x1=1, y1=4, semantic_id=2),
        Element(kind="circle", layer="", cx=5, cy=5, rx=1, ry=1),
    ]
    _store(tmp_path, "ab" * 32, elements)
    _store(tmp_path, "cd" * 32, elements[:1])

    build_features(tmp_path, ["ab" * 32, "cd" * 32], workers=1)
    fold = load_fold(tmp_path, [("x/1", "ab" * 32), ("y/2", "cd" * 32)], CLASSES)

    assert fold.class_names == ["other", "wall", "door", "window"]
    names = [fold.class_names[i] for i in fold.labels]
    assert names == ["wall", "door", "other", "other", "wall"]
    assert fold.drawing.tolist() == [0, 0, 0, 0, 1]
    assert fold.features.shape[0] == 5
    assert fold.features.dtype == np.float32


def test_unknown_large_semantic_id_is_an_error(tmp_path: Path) -> None:
    _store(
        tmp_path,
        "ef" * 32,
        [Element(kind="line", layer="", x0=0, y0=0, x1=1, y1=0, semantic_id=300)],
    )
    build_features(tmp_path, ["ef" * 32], workers=1)

    with pytest.raises(ValueError):
        load_fold(tmp_path, [("x/1", "ef" * 32)], CLASSES)
