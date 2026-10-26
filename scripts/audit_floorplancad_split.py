#!/usr/bin/env python3
"""Measure how far the official FloorPlanCAD train/test split shares sources.

File names are <prefix>-<index>.svg, but prefix numbering is not global: folders listed
under one namespace in the config share a numbering. Evidence for that comes from
layer names: crops of one source reuse the same layer vocabulary. Exact duplicate files
are found by content hash.

Usage:
    python scripts/audit_floorplancad_split.py --config configs/default.yaml
"""

from __future__ import annotations

import argparse
import hashlib
import random
import re
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import yaml
from log_run import log_run

LAYER_LABEL = re.compile(rb'inkscape:label="([^"]*)"')
PAIR_SAMPLES = 2000


def _jaccard(a: set[bytes], b: set[bytes]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _find(parent: dict[str, str], key: str) -> str:
    while parent[key] != key:
        parent[key] = parent[parent[key]]
        key = parent[key]
    return key


def _group_sizes(group_of: dict[str, str]) -> list[int]:
    """Files per source group."""
    counts: dict[str, int] = defaultdict(int)
    for group in group_of.values():
        counts[group] += 1
    return list(counts.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    dataset = config["public"]["floorplancad"]
    namespaces = dataset["prefix_namespaces"]
    root = Path(dataset["root"])
    rng = random.Random(config["split"]["seed"])

    # (folder, prefix) -> layer vocabulary; file -> content hash
    vocabulary: dict[tuple[str, str], set[bytes]] = defaultdict(set)
    digest_of: dict[str, str] = {}
    files_of_digest: dict[str, list[str]] = defaultdict(list)
    for folder in dataset["splits"]:
        for svg in sorted((root / folder).glob("*.svg")):
            data = svg.read_bytes()
            prefix = svg.stem.split("-")[0]
            vocabulary[(folder, prefix)].update(LAYER_LABEL.findall(data))
            name = f"{folder}/{svg.stem}"
            digest = hashlib.sha256(data).hexdigest()
            digest_of[name] = digest
            files_of_digest[digest].append(name)

    metrics: dict[str, float | int] = {}

    # Same prefix in two folders: as alike as one source, or as alike as random pairs?
    for a, b in combinations(dataset["splits"], 2):
        prefixes_a = [p for f, p in vocabulary if f == a]
        prefixes_b = [p for f, p in vocabulary if f == b]
        shared = sorted(set(prefixes_a) & set(prefixes_b))
        same = [_jaccard(vocabulary[(a, p)], vocabulary[(b, p)]) for p in shared]
        rand = [
            _jaccard(
                vocabulary[(a, rng.choice(prefixes_a))], vocabulary[(b, rng.choice(prefixes_b))]
            )
            for _ in range(PAIR_SAMPLES)
        ]
        key = f"{a}_vs_{b}"
        metrics[f"{key}_shared_prefixes"] = len(shared)
        metrics[f"{key}_same_prefix_layer_jaccard"] = round(statistics.mean(same), 4)
        metrics[f"{key}_random_pair_layer_jaccard"] = round(statistics.mean(rand), 4)

    # Exact duplicates.
    duplicate_groups = [names for names in files_of_digest.values() if len(names) > 1]
    test_folders = set(dataset["test_splits"])
    across_split = [
        names
        for names in duplicate_groups
        if {n.split("/")[0] in test_folders for n in names} == {True, False}
    ]
    metrics["files"] = len(digest_of)
    metrics["distinct_contents"] = len(files_of_digest)
    metrics["duplicate_content_groups"] = len(duplicate_groups)
    metrics["duplicate_groups_across_train_and_test"] = len(across_split)

    # Source groups: (namespace, prefix), merged when they share an identical file.
    parent: dict[str, str] = {}
    source_of: dict[str, str] = {}
    for name in digest_of:
        folder, stem = name.split("/")
        source = f"{namespaces[folder]}/{stem.split('-')[0]}"
        source_of[name] = source
        parent.setdefault(source, source)
    for names in duplicate_groups:
        first = _find(parent, source_of[names[0]])
        for other in names[1:]:
            parent[_find(parent, source_of[other])] = first

    group_of = {name: _find(parent, source) for name, source in source_of.items()}
    train_groups = {g for n, g in group_of.items() if n.split("/")[0] not in test_folders}
    test_names = [n for n in group_of if n.split("/")[0] in test_folders]
    test_in_train = [n for n in test_names if group_of[n] in train_groups]
    sizes = _group_sizes(group_of)

    metrics["sources"] = len(parent)
    metrics["groups"] = len(set(group_of.values()))
    metrics["test_files"] = len(test_names)
    metrics["test_files_with_group_in_train"] = len(test_in_train)
    metrics["test_file_fraction_with_group_in_train"] = round(
        len(test_in_train) / len(test_names), 4
    )
    metrics["files_per_group_median"] = statistics.median(sizes)
    metrics["files_per_group_max"] = max(sizes)

    log_run(
        name="floorplancad-split-audit",
        config={
            "config_file": args.config,
            "floorplancad": dataset,
            "seed": config["split"]["seed"],
        },
        metrics=metrics,
        notes="Namespace-aware prefix overlap and exact duplicates in the official split.",
    )
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
