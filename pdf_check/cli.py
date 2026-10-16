"""Read-only CLI for the two books' compiled locator JSON catalogs.

The bundled catalog is the default. To use another catalog directory, set
PDF_CHECK_CATALOG_ROOT or pass --catalog-root explicitly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


BOOK_IDS = ("cvaa2e", "dip4e")
DATA_VERSION = "3"
# Default works after global pip installation and from any working directory.
CATALOG_ROOT = Path(__file__).resolve().parent / "catalog"


class LocatorError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise LocatorError("CATALOG_UNAVAILABLE", f"Index file not found: {path}")
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LocatorError("CATALOG_INVALID", f"Cannot read index {path}: {exc}") from exc
    if not isinstance(result, dict):
        raise LocatorError("CATALOG_INVALID", f"Index is not a JSON object: {path}")
    return result


def check_version(obj: dict[str, Any], source: Path) -> None:
    if str(obj.get("data_version")) != DATA_VERSION:
        raise LocatorError(
            "CATALOG_VERSION_MISMATCH",
            f"Expected data_version {DATA_VERSION} in {source}, got {obj.get('data_version')!r}",
        )


def load_index(root: Path, book_id: str, kind: str) -> dict[str, Any]:
    path = root / book_id / f"compiled_{kind}_index.json"
    index = read_json(path)
    check_version(index, path)
    if index.get("book", {}).get("book_id") != book_id:
        raise LocatorError("CATALOG_INVALID", f"book_id mismatch in {path}")
    return index


def find_record(
    root: Path, book_id: str, kind: str, record_id: str
) -> dict[str, Any]:
    index = load_index(root, book_id, kind)
    shard_key = "section_shards" if kind == "locator" else "exercise_shards"
    records_key = "sections" if kind == "locator" else "exercises"
    id_key = "section_id" if kind == "locator" else "exercise_id"
    not_found = "SECTION_NOT_FOUND" if kind == "locator" else "EXERCISE_NOT_FOUND"
    shards = index.get(shard_key)
    if not isinstance(shards, list) or not shards:
        raise LocatorError("CATALOG_INVALID", f"Missing {shard_key} for {book_id}")

    for shard_name in shards:
        relative_path = Path(shard_name)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise LocatorError("CATALOG_INVALID", f"Invalid shard path: {shard_name}")
        shard_path = root / book_id / relative_path
        shard = read_json(shard_path)
        check_version(shard, shard_path)
        records = shard.get(records_key)
        if not isinstance(records, dict):
            raise LocatorError("CATALOG_INVALID", f"Missing {records_key} in {shard_path}")
        record = records.get(record_id)
        if record is None:
            continue
        if record.get("book_id") != book_id or record.get(id_key) != record_id:
            raise LocatorError("CATALOG_INVALID", f"Record identity mismatch in {shard_path}")
        check_version(record, shard_path)
        return record
    raise LocatorError(not_found, f"{book_id}: {kind} ID {record_id!r} does not exist")


def list_exercises(root: Path, book_id: str, chapter_id: str) -> dict[str, Any]:
    index = load_index(root, book_id, "exercise")
    chapters = index.get("chapters")
    if not isinstance(chapters, dict):
        raise LocatorError("EXERCISE_CATALOG_UNAVAILABLE", f"No chapter list for {book_id}")
    chapter = chapters.get(chapter_id)
    if chapter is None:
        raise LocatorError("CHAPTER_NOT_FOUND", f"{book_id}: chapter {chapter_id!r} not found")
    if chapter.get("book_id") != book_id or chapter.get("chapter_id") != chapter_id:
        raise LocatorError("CATALOG_INVALID", f"Chapter identity mismatch: {chapter_id}")
    check_version(chapter, root / book_id / "compiled_exercise_index.json")
    return chapter


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Look up textbook Section / Exercise page plans from compiled JSON indexes"
    )
    parser.add_argument("--book", required=True, choices=BOOK_IDS)
    parser.add_argument(
        "--catalog-root",
        type=Path,
        default=Path(os.environ.get("PDF_CHECK_CATALOG_ROOT", str(CATALOG_ROOT))),
        help="Directory containing cvaa2e/ and dip4e/ (default: bundled catalog)",
    )
    command = parser.add_subparsers(dest="kind", required=True)
    for name in ("section", "exercise", "list"):
        sub = command.add_parser(name)
        sub.add_argument("id", help="Section ID, Exercise ID, or chapter ID")
    args = parser.parse_args()

    try:
        root = args.catalog_root.expanduser().resolve()
        if args.kind == "section":
            result = find_record(root, args.book, "locator", args.id)
        elif args.kind == "exercise":
            result = find_record(root, args.book, "exercise", args.id)
        else:
            result = list_exercises(root, args.book, args.id)
    except LocatorError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": str(exc)}}, ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
