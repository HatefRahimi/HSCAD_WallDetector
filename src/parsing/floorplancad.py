"""Parse the FloorPlanCAD release into the element cache and describe every file."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa

from src.parsing import cache
from src.parsing.elements import to_table
from src.parsing.svg import read_svg

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ManifestRow:
    """What happened to one file."""

    drawing_id: str  # <folder>/<stem>; stems alone repeat across folders
    folder: str
    source: str  # <namespace>/<prefix>, see decision 0006
    sha256: str
    status: str  # parsed | cached | failed
    reason: str | None
    elements: int
    labelled: int


def list_drawings(root: Path, folders: list[str]) -> list[tuple[str, Path]]:
    """Every SVG of the given folders, in a fixed order."""
    drawings = []
    for folder in folders:
        for path in sorted((root / folder).glob("*.svg")):
            drawings.append((folder, path))
    return drawings


def parse_drawing(folder: str, path: Path, namespace: str, cache_dir: Path) -> ManifestRow:
    """Parse one file through the cache. Never raises for a bad file; reports it instead."""
    digest = cache.content_hash(path)
    identity = {
        "drawing_id": f"{folder}/{path.stem}",
        "folder": folder,
        "source": f"{namespace}/{path.stem.split('-')[0]}",
        "sha256": digest,
    }

    table = cache.load(cache_dir, digest)
    status = "cached"
    if table is None:
        try:
            table = to_table(read_svg(path))
        except (ET.ParseError, ValueError, TypeError) as error:
            reason = f"{type(error).__name__}: {error}"
            log.warning("failed %s: %s", identity["drawing_id"], reason)
            return ManifestRow(**identity, status="failed", reason=reason, elements=0, labelled=0)

        cache.store(cache_dir, digest, table)
        status = "parsed"

    return ManifestRow(
        **identity,
        status=status,
        reason=None,
        elements=table.num_rows,
        labelled=_labelled(table),
    )


def parse_all(
    root: Path,
    folders: list[str],
    namespaces: dict[str, str],
    cache_dir: Path,
    limit: int | None = None,
    progress_every: int = 500,
) -> list[ManifestRow]:
    """Parse every drawing; rerunning resumes, since finished files come from the cache."""
    drawings = list_drawings(root, folders)
    if limit is not None:
        drawings = drawings[:limit]

    rows = []
    for count, (folder, path) in enumerate(drawings, start=1):
        rows.append(parse_drawing(folder, path, namespaces[folder], cache_dir))
        if count % progress_every == 0:
            log.info("%d / %d drawings", count, len(drawings))

    return rows


def _labelled(table: pa.Table) -> int:
    """Elements that carry a semantic id."""
    return table.num_rows - table.column("semantic_id").null_count
