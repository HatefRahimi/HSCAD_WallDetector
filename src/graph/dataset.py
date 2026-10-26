"""Feature matrices per fold, built from the element cache and cached per drawing."""

from __future__ import annotations

import logging
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.evaluate.metrics import OTHER, class_of
from src.graph.features import FEATURES_VERSION, element_features, geometric_rows
from src.parsing import cache

log = logging.getLogger(__name__)

NO_LABEL = -1
MAX_SEMANTIC_ID = 255  # the release uses 1 to 35


@dataclass(frozen=True)
class Fold:
    """Features and labels of one fold, with the drawing each row came from."""

    features: np.ndarray  # (elements, features) float32
    labels: np.ndarray  # (elements,) int8, index into class_names
    drawing: np.ndarray  # (elements,) int32, index into drawing_ids
    drawing_ids: list[str]
    class_names: list[str]


def feature_path(cache_dir: Path, digest: str) -> Path:
    """Where the features of one distinct content live."""
    return cache_dir / f"features-v{FEATURES_VERSION}" / digest[:2] / f"{digest}.npz"


def _build_one(args: tuple[Path, str]) -> str:
    """Compute and store the features of one drawing unless they exist already."""
    cache_dir, digest = args
    path = feature_path(cache_dir, digest)
    if path.exists():
        return digest

    table = cache.load(cache_dir, digest)
    rows = geometric_rows(table)
    semantic = np.array(table.column("semantic_id").to_pylist(), dtype=object)[rows]
    semantic_ids = np.array([NO_LABEL if s is None else s for s in semantic], dtype=np.int16)

    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial.npz")
    np.savez(partial, features=element_features(table), semantic_ids=semantic_ids)
    os.replace(partial, path)
    return digest


def build_features(
    cache_dir: Path, digests: list[str], workers: int, progress_every: int = 500
) -> None:
    """Compute missing features in parallel; rerunning resumes where it stopped."""
    todo = sorted({d for d in digests if not feature_path(cache_dir, d).exists()})
    log.info("features: %d of %d drawings to compute", len(todo), len(set(digests)))

    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
        for count, _ in enumerate(pool.map(_build_one, [(cache_dir, d) for d in todo]), 1):
            if count % progress_every == 0:
                log.info("features: %d / %d", count, len(todo))


def load_fold(
    cache_dir: Path, drawings: list[tuple[str, str]], classes: dict[str, list[int]]
) -> Fold:
    """Stack the cached features of (drawing_id, sha256) pairs into one fold."""
    class_names = [OTHER, *classes]
    index_of = {name: i for i, name in enumerate(class_names)}
    # Lookup by semantic id + 1, so slot 0 is "no label"; built from the frozen class_of.
    lookup = np.array(
        [index_of[class_of(None, classes)]]
        + [index_of[class_of(i, classes)] for i in range(MAX_SEMANTIC_ID + 1)],
        dtype=np.int8,
    )

    features, labels, origin = [], [], []
    for number, (_, digest) in enumerate(drawings):
        stored = np.load(feature_path(cache_dir, digest))
        semantic_ids = stored["semantic_ids"].astype(np.int32)
        if semantic_ids.max(initial=NO_LABEL) > MAX_SEMANTIC_ID:
            raise ValueError(f"semantic id above {MAX_SEMANTIC_ID} in {digest}")
        features.append(stored["features"])
        labels.append(lookup[semantic_ids + 1])
        origin.append(np.full(len(stored["semantic_ids"]), number, dtype=np.int32))

    return Fold(
        features=np.concatenate(features),
        labels=np.concatenate(labels),
        drawing=np.concatenate(origin),
        drawing_ids=[drawing_id for drawing_id, _ in drawings],
        class_names=class_names,
    )
