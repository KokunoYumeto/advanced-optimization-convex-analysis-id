#!/usr/bin/env python3
"""Generate the frozen MIT-L08 release-input lock from validated final bytes.

The generator is local and fail-closed. It performs no network, credential,
Git, publication, or mutable-control operation. It refuses to write a lock
until the reader and backend validation receipts both pass and bind the
expected Lecture 4 boundary and 1,820 + 137 backend transition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCK_PATH = HERE / "release-input-lock-mit-l08.json"
SOURCE_PAGES = list(range(39, 50))
NEXT_SOURCE_PAGE = 50
PROTECTED_BACKEND_RECORD_COUNT = 1820
NEW_BACKEND_RECORD_COUNT = 137
BACKEND_RECORD_COUNT = 1957

LOCKED_PATHS = [
    "00_control/MIT_L08_CORRECTION_SNAPSHOT.jsonl",
    "00_control/MIT_L08_LECTURE_4_BOUNDARY_CENSUS.md",
    "backend/records.csv",
    "backend/records.jsonl",
    "output/html/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.html",
    "output/pdf/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.pdf",
    "qa/MIT_L08_BACKEND_VALIDATION.json",
    "qa/MIT_L08_BROWSER_QA.json",
    "qa/MIT_L08_INDEPENDENT_REREVIEW.md",
    "qa/MIT_L08_VALIDATION.json",
    "qa/MIT_L08_VISUAL_QA.json",
    "qa/build_mit_l08.py",
    "qa/extend_backend_mit_l08.py",
    "qa/validate_backend_mit_l08.py",
    "qa/validate_mit_l08.py",
    "source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md",
    "source/id-ID/mit-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.md",
    "source/id-ID/mit-l08-after-body.html",
    "source/id-ID/mit-l08-before-body.html",
    "source/id-ID/mit-l08-pdf-filter.lua",
    "source/id-ID/mit-l08-preamble.tex",
    "source/id-ID/mit-l08.css",
]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def validate_closure() -> None:
    content = read_json(ROOT / "qa/MIT_L08_VALIDATION.json")
    backend = read_json(ROOT / "qa/MIT_L08_BACKEND_VALIDATION.json")
    if (
        content.get("result") != "pass"
        or content.get("errors") != []
        or content.get("boundary", {}).get("source_pdf_pages") != SOURCE_PAGES
        or content.get("boundary", {}).get("next_source_page") != NEXT_SOURCE_PAGE
        or content.get("boundary", {}).get("source_items") != 27
        or content.get("boundary", {}).get("nested_items") != 16
        or content.get("boundary", {}).get("source_displays") != 26
        or content.get("boundary", {}).get("source_figures") != 5
        or content.get("boundary", {}).get("source_figure_panels") != 5
        or content.get("boundary", {}).get("copied_source_graphics") != 0
    ):
        raise RuntimeError("L08 reader closure has not passed the frozen boundary")
    if (
        backend.get("schema") != "o015-mit-l08-backend-validation-v1"
        or backend.get("result") != "pass"
        or backend.get("errors") != []
        or backend.get("protected_baseline", {}).get("record_count") != PROTECTED_BACKEND_RECORD_COUNT
        or backend.get("protected_baseline", {}).get("raw_reconstruction_passed") is not True
        or backend.get("admission", {}).get("new_record_count") != NEW_BACKEND_RECORD_COUNT
        or backend.get("admission", {}).get("expected_new_record_count") != NEW_BACKEND_RECORD_COUNT
        or backend.get("final_backend", {}).get("record_count") != BACKEND_RECORD_COUNT
        or backend.get("final_backend", {}).get("csv_projection_lossless") is not True
        or backend.get("final_backend", {}).get("references_closed") is not True
        or backend.get("independent_validation_runs_required") != 2
    ):
        raise RuntimeError("L08 backend closure has not passed the 1,820 + 137 transition")


def make_lock() -> dict:
    validate_closure()
    missing = [relative for relative in LOCKED_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError("missing release inputs:\n" + "\n".join(missing))
    files = {
        relative: {"bytes": (ROOT / relative).stat().st_size, "sha256": digest(ROOT / relative)}
        for relative in sorted(LOCKED_PATHS)
    }
    return {
        "schema": "o015-mit-l08-release-input-lock-v1",
        "boundary": {
            "source_pages": SOURCE_PAGES,
            "next_source_page": NEXT_SOURCE_PAGE,
            "next_source_heading": "LECTURE 5 - LECTURE OUTLINE",
        },
        "backend_record_count": BACKEND_RECORD_COUNT,
        "protected_backend_record_count": PROTECTED_BACKEND_RECORD_COUNT,
        "new_backend_record_count": NEW_BACKEND_RECORD_COUNT,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify an existing lock without rewriting it")
    args = parser.parse_args()
    lock = make_lock()
    payload = (json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if args.check:
        if not LOCK_PATH.is_file() or LOCK_PATH.read_bytes() != payload:
            raise RuntimeError("existing L08 input lock differs from current validated final bytes")
    else:
        HERE.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".mit-l08-lock-", suffix=".json", dir=HERE, delete=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            staged = Path(handle.name)
        try:
            os.replace(staged, LOCK_PATH)
        finally:
            staged.unlink(missing_ok=True)
    print(json.dumps({"result": "pass", "path": str(LOCK_PATH), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "locked_files": len(lock["files"])}, indent=2))


if __name__ == "__main__":
    main()
