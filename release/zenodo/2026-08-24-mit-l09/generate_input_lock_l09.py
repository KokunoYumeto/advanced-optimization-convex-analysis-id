#!/usr/bin/env python3
"""Freeze validated MIT-L09 inputs only after final backend/control supply.

This is a local, fail-closed generator.  It performs no network, credential,
Git, publication, or control mutation.  The deliberately absent
``release-config-mit-l09.json`` must be created from the adjacent template only
after the backend admission and pre-publication controls are final.  Every
supplied identity is checked against the live byte stream before a lock is
written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONFIG_PATH = HERE / "release-config-mit-l09.json"
LOCK_PATH = HERE / "release-input-lock-mit-l09.json"
SOURCE_PAGES = list(range(50, 64))
NEXT_SOURCE_PAGE = 64
NEXT_SOURCE_HEADING = "LECTURE 6 - LECTURE OUTLINE"

MATERIAL_PATHS = [
    "00_control/MIT_L09_CORRECTION_SNAPSHOT.jsonl",
    "00_control/MIT_L09_LECTURE_5_BOUNDARY_CENSUS.md",
    "backend/records.csv",
    "backend/records.jsonl",
    "output/html/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.html",
    "output/pdf/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.pdf",
    "qa/MIT_L09_BACKEND_VALIDATION.json",
    "qa/MIT_L09_BROWSER_QA.json",
    "qa/MIT_L09_INDEPENDENT_REREVIEW.md",
    "qa/MIT_L09_VALIDATION.json",
    "qa/MIT_L09_VISUAL_QA.json",
    "qa/build_mit_l09.py",
    "qa/extend_backend_mit_l09.py",
    "qa/validate_backend_mit_l09.py",
    "qa/validate_mit_l09.py",
    "source/en/mit-09-lecture-5-recession-minima-semantic-witness.md",
    "source/id-ID/mit-09-kuliah-5-resesi-dan-minimum-id.md",
    "source/id-ID/mit-l09-after-body.html",
    "source/id-ID/mit-l09-before-body.html",
    "source/id-ID/mit-l09-pdf-filter.lua",
    "source/id-ID/mit-l09-preamble.tex",
    "source/id-ID/mit-l09.css",
]

CONTROL_PATHS = [
    "00_control/CURRENT_GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/CURRENT_CURSOR.md",
    "00_control/SOURCE_AUTHORITY.json",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/DECISION_LOG.md",
    "00_control/ADVERSE_LEDGER.jsonl",
    "00_control/BUILD_AND_QA.md",
    "00_control/PUBLICATION_RECEIPTS.md",
]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def valid_identity(value: object) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("bytes"), int)
        and value["bytes"] > 0
        and isinstance(value.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is not None
    )


def require_identity(path: Path, expected: object, label: str) -> None:
    if not valid_identity(expected):
        raise RuntimeError(f"{label} identity is absent or not final")
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = identity(path)
    if observed != expected:
        raise RuntimeError(f"{label} differs from supplied final identity: {path}")


def load_config(*, verify_live_controls: bool = True) -> dict:
    if not CONFIG_PATH.is_file():
        raise RuntimeError(
            "release-config-mit-l09.json is deliberately absent; supply final "
            "backend counts/hashes and pre-publication control hashes first"
        )
    config = read_json(CONFIG_PATH)
    boundary = config.get("boundary", {})
    if (
        config.get("schema") != "o015-mit-l09-release-config-v1"
        or config.get("parent_record_id") != "22074528"
        or config.get("parent_record_doi") != "10.5281/zenodo.22074528"
        or config.get("concept_id") != "22059741"
        or config.get("concept_doi") != "10.5281/zenodo.22059741"
        or boundary.get("source_pages") != SOURCE_PAGES
        or boundary.get("next_source_page") != NEXT_SOURCE_PAGE
        or boundary.get("next_source_heading") != NEXT_SOURCE_HEADING
        or config.get("expected_inherited_file_count") != 74
        or config.get("expected_addition_file_count") != 8
        or config.get("expected_release_file_count") != 82
        or config.get("status") != "partial"
    ):
        raise RuntimeError("L09 release config has a different lineage, boundary, count, or status")

    backend = config.get("backend", {})
    counts = [
        backend.get("protected_record_count"),
        backend.get("new_record_count"),
        backend.get("record_count"),
    ]
    if (
        any(not isinstance(value, int) or value <= 0 for value in counts)
        or counts[0] + counts[1] != counts[2]
    ):
        raise RuntimeError("final positive backend counts are absent or inconsistent")
    require_identity(ROOT / "backend/records.jsonl", backend.get("jsonl"), "backend JSONL")
    require_identity(ROOT / "backend/records.csv", backend.get("csv"), "backend CSV")
    require_identity(
        ROOT / "qa/MIT_L09_BACKEND_VALIDATION.json",
        backend.get("validation"),
        "backend validation",
    )

    controls = config.get("controls")
    if not isinstance(controls, dict) or set(controls) != set(CONTROL_PATHS):
        raise RuntimeError("config must supply exactly the ten required pre-publication controls")
    for relative in CONTROL_PATHS:
        if not valid_identity(controls[relative]):
            raise RuntimeError(f"control {relative} identity is absent or not final")
        if verify_live_controls:
            require_identity(ROOT / relative, controls[relative], f"control {relative}")
    return config


def validate_closure(config: dict) -> None:
    content = read_json(ROOT / "qa/MIT_L09_VALIDATION.json")
    backend = read_json(ROOT / "qa/MIT_L09_BACKEND_VALIDATION.json")
    boundary = content.get("boundary", {})
    if (
        content.get("schema") != "o015-mit-l09-validation-v1"
        or content.get("result") != "pass"
        or content.get("errors") != []
        or content.get("release_ready") is not True
        or boundary.get("source_pdf_pages") != SOURCE_PAGES
        or boundary.get("next_source_page") != NEXT_SOURCE_PAGE
        or boundary.get("next_heading") != NEXT_SOURCE_HEADING
        or boundary.get("source_items") != 41
        or boundary.get("nested_items") != 17
        or boundary.get("source_displays") != 19
        or boundary.get("source_figures") != 7
        or boundary.get("source_figure_panels") != 12
        or boundary.get("examples") != 2
        or boundary.get("copied_source_graphics") != 0
    ):
        raise RuntimeError("L09 reader closure has not passed the frozen Lecture 5 boundary")

    expected = config["backend"]
    expected_segments = [f"d90.mit.ocw-6.253.l09.p{page:03d}" for page in SOURCE_PAGES]
    if (
        backend.get("schema") != "o015-mit-l09-backend-validation-v1"
        or backend.get("result") != "pass"
        or backend.get("errors") != []
        or backend.get("protected_baseline", {}).get("record_count")
        != expected["protected_record_count"]
        or backend.get("protected_baseline", {}).get("raw_reconstruction_passed") is not True
        or backend.get("admission", {}).get("new_record_count") != expected["new_record_count"]
        or backend.get("admission", {}).get("expected_new_record_count")
        != expected["new_record_count"]
        or backend.get("admission", {}).get("segment_ids") != expected_segments
        or backend.get("final_backend", {}).get("record_count") != expected["record_count"]
        or backend.get("final_backend", {}).get("csv_projection_lossless") is not True
        or backend.get("final_backend", {}).get("references_closed") is not True
        or backend.get("independent_validation_runs_required") != 2
    ):
        raise RuntimeError("L09 backend closure does not match the supplied final transition")


def make_lock() -> dict:
    config = load_config()
    validate_closure(config)
    paths = sorted(set(MATERIAL_PATHS + CONTROL_PATHS))
    missing = [relative for relative in paths if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError("missing release inputs:\n" + "\n".join(missing))
    files = {relative: identity(ROOT / relative) for relative in paths}
    return {
        "schema": "o015-mit-l09-release-input-lock-v1",
        "boundary": {
            "source_pages": SOURCE_PAGES,
            "next_source_page": NEXT_SOURCE_PAGE,
            "next_source_heading": NEXT_SOURCE_HEADING,
        },
        "backend_record_count": config["backend"]["record_count"],
        "protected_backend_record_count": config["backend"]["protected_record_count"],
        "new_backend_record_count": config["backend"]["new_record_count"],
        "material_file_count": len(MATERIAL_PATHS),
        "control_file_count": len(CONTROL_PATHS),
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
            raise RuntimeError("existing L09 input lock differs from validated final bytes")
    else:
        with tempfile.NamedTemporaryFile(prefix=".mit-l09-lock-", suffix=".json", dir=HERE, delete=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            staged = Path(handle.name)
        try:
            os.replace(staged, LOCK_PATH)
        finally:
            staged.unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "result": "pass",
                "path": str(LOCK_PATH),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "locked_files": len(lock["files"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
