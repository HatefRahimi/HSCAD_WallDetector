"""Content-addressed cache of parsed drawings, one Parquet file per distinct file content."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

# Bump when the reader's output changes. Entries of older versions are then ignored.
READER_VERSION = 1


def content_hash(path: Path) -> str:
    """SHA-256 of the file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry_path(cache_dir: Path, digest: str) -> Path:
    """Where the parsed table for one content hash lives."""
    return cache_dir / f"v{READER_VERSION}" / digest[:2] / f"{digest}.parquet"


def load(cache_dir: Path, digest: str) -> pa.Table | None:
    """The cached table for this content, or None if it was never parsed."""
    path = entry_path(cache_dir, digest)
    if not path.exists():
        return None
    return pq.read_table(path)


def store(cache_dir: Path, digest: str, table: pa.Table) -> None:
    """Write atomically, so an interrupted run never leaves a half-written entry."""
    path = entry_path(cache_dir, digest)
    path.parent.mkdir(parents=True, exist_ok=True)

    partial = path.with_suffix(".partial")
    pq.write_table(table, partial)
    os.replace(partial, path)
