#!/usr/bin/env python3
"""Parse FloorPlanCAD into the element cache, write a manifest, and log a data report.

Run from the repository root, as a module:
    python -m scripts.parse_floorplancad --config configs/default.yaml

Rerunning resumes: files already in the cache are not parsed again.
"""

from __future__ import annotations

import argparse
import logging
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import yaml

from scripts.log_run import log_run
from src.parsing import cache
from src.parsing.floorplancad import ManifestRow, parse_all


def _setup_logging(cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(cache_dir / "parse.log"), logging.StreamHandler()],
    )


def _report(rows: list[ManifestRow], cache_dir: Path, classes: dict[str, list[int]]) -> dict:
    """Aggregate counts over every distinct parsed content."""
    statuses = Counter(row.status for row in rows)
    reasons = Counter(row.reason.split(":")[0] for row in rows if row.status == "failed")

    kinds: Counter[str] = Counter()
    semantic_ids: Counter[int] = Counter()
    seen = set()
    for row in rows:
        if row.status == "failed" or row.sha256 in seen:
            continue
        seen.add(row.sha256)

        table = cache.load(cache_dir, row.sha256)
        for item in pc.value_counts(table.column("kind")).to_pylist():
            kinds[item["values"]] += item["counts"]
        for item in pc.value_counts(table.column("semantic_id")).to_pylist():
            if item["values"] is not None:
                semantic_ids[item["values"]] += item["counts"]

    report = {
        "files": len(rows),
        "files_parsed": statuses["parsed"],
        "files_cached": statuses["cached"],
        "files_failed": statuses["failed"],
        "distinct_contents_parsed": len(seen),
        "sources": len({row.source for row in rows}),
        "elements_distinct_contents": sum(kinds.values()),
        "labelled_elements_distinct_contents": sum(semantic_ids.values()),
    }
    for kind, count in sorted(kinds.items()):
        report[f"elements_{kind}"] = count
    for name, ids in classes.items():
        report[f"elements_{name}"] = sum(semantic_ids[i] for i in ids)
    for reason, count in sorted(reasons.items()):
        report[f"failed_{reason}"] = count
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    dataset = config["public"]["floorplancad"]
    cache_dir = Path(dataset["cache"])
    _setup_logging(cache_dir)

    rows = parse_all(
        root=Path(dataset["root"]),
        folders=dataset["splits"],
        namespaces=dataset["prefix_namespaces"],
        cache_dir=cache_dir,
        limit=dataset["limit"],
    )

    manifest = pa.Table.from_pylist([asdict(row) for row in rows])
    pq.write_table(manifest, cache_dir / f"manifest-v{cache.READER_VERSION}.parquet")

    report = _report(rows, cache_dir, dataset["classes"])
    log_run(
        name="floorplancad-parse",
        config={
            "config_file": args.config,
            "floorplancad": dataset,
            "reader_version": cache.READER_VERSION,
        },
        metrics=report,
        notes="Parse of FloorPlanCAD SVGs into the element cache; counts over distinct files.",
    )
    for key, value in report.items():
        logging.info("%s: %s", key, value)


if __name__ == "__main__":
    main()
