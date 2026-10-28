#!/usr/bin/env python3
"""Train the per-element gradient-boosting baseline on the frozen FloorPlanCAD split.

Run from the repository root:
    python -m scripts.train_baseline --config configs/default.yaml [--test]

Validation scores are always reported. Test scores only with --test, for a model whose
settings are final.
"""

from __future__ import annotations

import argparse
import csv
import logging
import pickle
from collections import defaultdict
from pathlib import Path

import yaml
from sklearn.ensemble import HistGradientBoostingClassifier

from scripts.log_run import REPO_ROOT, log_run
from src.evaluate.metrics import score
from src.graph.dataset import Fold, build_features, load_fold
from src.graph.features import FEATURE_NAMES, FEATURES_VERSION
from src.parsing import cache

log = logging.getLogger(__name__)


def read_folds(split_run: str) -> dict[str, list[tuple[str, str]]]:
    """(drawing_id, sha256) pairs per fold of a frozen split run."""
    folds: dict[str, list[tuple[str, str]]] = defaultdict(list)
    with open(REPO_ROOT / "runs" / split_run / "split.csv", newline="") as handle:
        for row in csv.DictReader(handle):
            folds[row["fold"]].append((row["drawing_id"], row["sha256"]))
    return folds


def _fold_scores(name: str, model: HistGradientBoostingClassifier, fold: Fold, classes) -> dict:
    """Pooled per-class scores of one fold, flattened for metrics.json."""
    predicted = model.predict(fold.features)
    true_names = [fold.class_names[i] for i in fold.labels]
    predicted_names = [fold.class_names[i] for i in predicted]

    out: dict[str, float | int] = {f"{name}_elements": len(true_names)}
    for cls, s in score(true_names, predicted_names, classes).items():
        out[f"{name}_{cls}_precision"] = round(s.precision, 4)
        out[f"{name}_{cls}_recall"] = round(s.recall, 4)
        out[f"{name}_{cls}_f1"] = round(s.f1, 4)
        out[f"{name}_{cls}_tp"] = s.tp
        out[f"{name}_{cls}_fp"] = s.fp
        out[f"{name}_{cls}_fn"] = s.fn
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--test", action="store_true", help="also score the test fold")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    dataset = config["public"]["floorplancad"]
    settings = config["baseline"]
    cache_dir = Path(dataset["cache"])
    classes = dataset["classes"]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(cache_dir / "train_baseline.log"), logging.StreamHandler()],
    )

    folds = read_folds(config["split"]["floorplancad_run"])
    all_digests = [digest for members in folds.values() for _, digest in members]
    build_features(cache_dir, all_digests, workers=settings["workers"])

    train = load_fold(cache_dir, folds["train"], classes)
    val = load_fold(cache_dir, folds["val"], classes)
    log.info("train %s, val %s", train.features.shape, val.features.shape)

    model = HistGradientBoostingClassifier(
        learning_rate=settings["learning_rate"],
        max_iter=settings["max_iter"],
        max_leaf_nodes=settings["max_leaf_nodes"],
        min_samples_leaf=settings["min_samples_leaf"],
        l2_regularization=settings["l2_regularization"],
        early_stopping=True,
        n_iter_no_change=settings["n_iter_no_change"],
        random_state=settings["seed"],
        verbose=1,
    )
    model.fit(train.features, train.labels, X_val=val.features, y_val=val.labels)

    metrics: dict[str, float | int] = {
        "iterations": int(model.n_iter_),
        "train_elements": len(train.labels),
    }
    metrics.update(_fold_scores("val", model, val, classes))
    if args.test:
        test = load_fold(cache_dir, folds["test"], classes)
        metrics.update(_fold_scores("test", model, test, classes))

    run_dir = log_run(
        name="baseline-hgb",
        config={
            "config_file": args.config,
            "baseline": settings,
            "split_run": config["split"]["floorplancad_run"],
            "classes": classes,
            "features": FEATURE_NAMES,
            "features_version": FEATURES_VERSION,
            "reader_version": cache.READER_VERSION,
            "scored_test": args.test,
        },
        metrics=metrics,
        notes="Gradient boosting per element on geometric features; no layer names.",
    )

    model_dir = cache_dir / "models"
    model_dir.mkdir(exist_ok=True)
    with open(model_dir / f"{run_dir.name}.pkl", "wb") as handle:
        pickle.dump(model, handle)

    for key, value in metrics.items():
        log.info("%s: %s", key, value)


if __name__ == "__main__":
    main()
