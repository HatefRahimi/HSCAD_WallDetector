from __future__ import annotations

from pathlib import Path

from src.parsing import cache
from src.parsing.floorplancad import parse_all

GOOD = (
    '<svg xmlns="http://www.w3.org/2000/svg" '
    'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">'
    '<g inkscape:label="WALL"><path d="M 0,0 L 1,1" semantic-id="1"/>'
    '<path d="M 0,1 L 1,2"/></g></svg>'
)
NAMESPACES = {"train-01": "b", "test-00": "b"}


def _dataset(tmp_path: Path) -> Path:
    root = tmp_path / "datasets"
    (root / "train-01").mkdir(parents=True)
    (root / "test-00").mkdir()
    (root / "train-01" / "0001-0001.svg").write_text(GOOD, encoding="utf-8")
    (root / "test-00" / "0001-0001.svg").write_text(GOOD, encoding="utf-8")
    (root / "test-00" / "0002-0001.svg").write_text("<svg><unclosed></svg>", encoding="utf-8")
    return root


def test_reports_every_file_and_keeps_going_after_a_bad_one(tmp_path: Path) -> None:
    root = _dataset(tmp_path)

    rows = parse_all(root, ["train-01", "test-00"], NAMESPACES, tmp_path / "cache")

    by_id = {row.drawing_id: row for row in rows}
    assert set(by_id) == {"train-01/0001-0001", "test-00/0001-0001", "test-00/0002-0001"}
    assert by_id["train-01/0001-0001"].status == "parsed"
    assert (by_id["train-01/0001-0001"].elements, by_id["train-01/0001-0001"].labelled) == (2, 1)
    assert by_id["test-00/0002-0001"].status == "failed"
    assert by_id["test-00/0002-0001"].reason.startswith("ParseError")
    assert by_id["test-00/0001-0001"].source == "b/0001"


def test_identical_content_is_parsed_once(tmp_path: Path) -> None:
    root = _dataset(tmp_path)

    rows = parse_all(root, ["train-01", "test-00"], NAMESPACES, tmp_path / "cache")

    by_id = {row.drawing_id: row for row in rows}
    assert by_id["test-00/0001-0001"].status == "cached"
    assert by_id["test-00/0001-0001"].sha256 == by_id["train-01/0001-0001"].sha256


def test_rerun_resumes_from_cache_and_changed_content_is_reparsed(tmp_path: Path) -> None:
    root = _dataset(tmp_path)
    cache_dir = tmp_path / "cache"
    parse_all(root, ["train-01"], NAMESPACES, cache_dir)

    (row,) = parse_all(root, ["train-01"], NAMESPACES, cache_dir)
    assert row.status == "cached"

    changed = GOOD.replace("M 0,0 L 1,1", "M 0,0 L 5,5")
    (root / "train-01" / "0001-0001.svg").write_text(changed, encoding="utf-8")
    (row,) = parse_all(root, ["train-01"], NAMESPACES, cache_dir)
    assert row.status == "parsed"
    assert cache.load(cache_dir, row.sha256).column("x1").to_pylist() == [5.0, 1.0]
