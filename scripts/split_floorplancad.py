#!/usr/bin/env python3
"""Assign FloorPlanCAD drawings to folds once and store the result in a run directory.

Run from the repository root, after scripts.parse_floorplancad:
    python -m scripts.split_floorplancad --config configs/default.yaml

Writes runs/<run_id>/split.csv (drawing_id, sha256, group, fold). Experiments load that
file by run ID instead of recomputing the split (decision 0007).
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import yaml

from scripts.log_run import log_run
from src.evaluate.splits import FOLDS, Drawing, assign_folds, group_of
from src.parsing import cache


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    dataset = config["public"]["floorplancad"]
    split = config["split"]
    cache_dir = Path(dataset["cache"])

    manifest = pq.read_table(cache_dir / f"manifest-v{cache.READER_VERSION}.parquet")
    rows = [r for r in manifest.to_pylist() if r["status"] != "failed"]
    drawings = [Drawing(r["drawing_id"], r["source"], r["sha256"]) for r in rows]

    folds = assign_folds(
        drawings,
        seed=split["seed"],
        test_fraction=split["test_fraction"],
        val_fraction=split["val_fraction"],
    )
    groups = group_of(drawings)
    sha_of = {d.drawing_id: d.sha256 for d in drawings}

    metrics: dict[str, float | int] = {"drawings_excluded_failed": manifest.num_rows - len(rows)}
    elements: Counter[str] = Counter()
    class_elements: Counter[tuple[str, str]] = Counter()
    for drawing_id, fold in folds.items():
        table = cache.load(cache_dir, sha_of[drawing_id])
        elements[fold] += table.num_rows
        ids = table.column("semantic_id")
        for name, values in dataset["classes"].items():
            class_elements[(fold, name)] += (
                pc.sum(pc.is_in(ids, value_set=pa.array(values, type=ids.type))).as_py() or 0
            )

    for fold in FOLDS:
        members = [d for d, f in folds.items() if f == fold]
        metrics[f"{fold}_drawings"] = len(members)
        metrics[f"{fold}_groups"] = len({groups[d] for d in members})
        metrics[f"{fold}_elements"] = elements[fold]
        for name in dataset["classes"]:
            count = class_elements[(fold, name)]
            metrics[f"{fold}_{name}_elements"] = count
            metrics[f"{fold}_{name}_share"] = round(count / elements[fold], 4)

    run_dir = log_run(
        name="floorplancad-split",
        config={"config_file": args.config, "split": split, "floorplancad": dataset},
        metrics=metrics,
        notes="Frozen FloorPlanCAD folds by source group (decisions 0006, 0007).",
    )
    with open(run_dir / "split.csv", "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["drawing_id", "sha256", "group", "fold"])
        for drawing_id in sorted(folds):
            writer.writerow([drawing_id, sha_of[drawing_id], groups[drawing_id], folds[drawing_id]])

    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
