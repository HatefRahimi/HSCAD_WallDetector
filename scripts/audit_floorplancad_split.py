#!/usr/bin/env python3
"""Measure how far the official FloorPlanCAD train/test split shares sources.

File names are <prefix>-<index>.svg. This counts crops per prefix and how many test
prefixes also occur in train. Reads file names only, not file contents.

Usage:
    python scripts/audit_floorplancad_split.py --config configs/default.yaml
"""

from __future__ import annotations

import argparse
import statistics
from collections import Counter
from pathlib import Path

import yaml

from log_run import log_run


def _prefixes(root: Path, splits: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for split in splits:
        for svg in (root / split).glob("*.svg"):
            counts[svg.stem.split("-")[0]] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    dataset = config["public"]["floorplancad"]
    root = Path(dataset["root"])

    train = _prefixes(root, dataset["train_splits"])
    test = _prefixes(root, dataset["test_splits"])
    shared = set(train) & set(test)

    crops_per_prefix = list((train + test).values())
    test_files = sum(test.values())
    test_files_shared = sum(count for prefix, count in test.items() if prefix in shared)

    metrics = {
        "train_files": sum(train.values()),
        "test_files": test_files,
        "train_prefixes": len(train),
        "test_prefixes": len(test),
        "all_prefixes": len(set(train) | set(test)),
        "test_prefixes_also_in_train": len(shared),
        "test_files_with_prefix_in_train": test_files_shared,
        "test_file_fraction_with_prefix_in_train": round(test_files_shared / test_files, 4),
        "crops_per_prefix_min": min(crops_per_prefix),
        "crops_per_prefix_median": statistics.median(crops_per_prefix),
        "crops_per_prefix_max": max(crops_per_prefix),
    }

    log_run(
        name="floorplancad-split-audit",
        config={"config_file": args.config, "floorplancad": dataset},
        metrics=metrics,
        notes="Prefix overlap between official FloorPlanCAD train and test splits.",
    )
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
