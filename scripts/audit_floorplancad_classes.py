#!/usr/bin/env python3
"""Check which FloorPlanCAD semantic-id values sit on which kind of CAD layer.

The release gives class numbers but no names. Layer names were written by the original
drafters, independently of the annotation, so the share of an id's elements that sit
on wall, door, window or stair layers is evidence for what the id means.

Usage:
    python scripts/audit_floorplancad_classes.py --config configs/default.yaml
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from log_run import log_run

SVG = "{http://www.w3.org/2000/svg}"
LAYER_LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"

# Substrings of an upper-cased layer name, English and Chinese drafting conventions.
LAYER_KINDS = {
    "wall": ("WALL", "墙"),
    "door": ("DOOR", "门"),
    "window": ("WIN", "窗"),
    "stair": ("STAIR", "梯"),
}


def _layer_kind(layer: str) -> str:
    upper = layer.upper()
    for kind, words in LAYER_KINDS.items():
        if any(word in upper for word in words):
            return kind
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    dataset = config["public"]["floorplancad"]
    root = Path(dataset["root"])

    per_id: dict[int, Counter[str]] = defaultdict(Counter)
    files = 0
    failed = 0
    for split in dataset["splits"]:
        for svg in sorted((root / split).glob("*.svg")):
            try:
                tree = ET.parse(svg)
            except ET.ParseError:
                failed += 1
                continue

            files += 1
            for group in tree.getroot().iter(f"{SVG}g"):
                kind = _layer_kind(group.get(LAYER_LABEL, ""))
                for path in group.iter(f"{SVG}path"):
                    semantic_id = path.get("semantic-id")
                    if semantic_id is None:
                        continue
                    per_id[int(semantic_id)][kind] += 1

    metrics: dict[str, float | int] = {"files": files, "files_failed": failed}
    for semantic_id in sorted(per_id):
        counts = per_id[semantic_id]
        total = sum(counts.values())
        metrics[f"id{semantic_id:02d}_elements"] = total
        for kind in (*LAYER_KINDS, "other"):
            metrics[f"id{semantic_id:02d}_{kind}_layer_share"] = round(counts[kind] / total, 4)

    log_run(
        name="floorplancad-class-audit",
        config={"config_file": args.config, "floorplancad": dataset, "layer_kinds": LAYER_KINDS},
        metrics=metrics,
        notes="Share of each semantic-id's elements per layer-name kind, all splits.",
    )
    print(f"files: {files}, failed: {failed}")
    for semantic_id in sorted(per_id):
        shares = ", ".join(
            f"{kind} {metrics[f'id{semantic_id:02d}_{kind}_layer_share']:.0%}"
            for kind in (*LAYER_KINDS, "other")
        )
        print(f"id {semantic_id:>2}  n={metrics[f'id{semantic_id:02d}_elements']:>7}  {shares}")


if __name__ == "__main__":
    main()
