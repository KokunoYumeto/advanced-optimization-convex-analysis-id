#!/usr/bin/env python3
"""Freeze validated MIT-L10 inputs only after final backend/control supply.

This is a local, fail-closed generator.  It performs no network, credential,
Git, publication, or control mutation.  The deliberately absent
``release-config-mit-l10.json`` must be created from the adjacent template only
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
CONFIG_PATH = HERE / "release-config-mit-l10.json"
LOCK_PATH = HERE / "release-input-lock-mit-l10.json"
SOURCE_PAGES = list(range(64, 86))
NEXT_SOURCE_PAGE = 86
NEXT_SOURCE_HEADING = "LECTURE 7 - LECTURE OUTLINE"

MATERIAL_PATHS = [
    "00_control/MIT_L10_CORRECTION_SNAPSHOT.jsonl",
    "00_control/MIT_L10_LECTURE_6_BOUNDARY_CENSUS.md",
    "backend/records.csv",
    "backend/records.jsonl",
    "output/html/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.html",
    "output/pdf/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.pdf",
    "qa/MIT_L10_BACKEND_VALIDATION.json",
    "qa/MIT_L10_BROWSER_QA.json",
    "qa/MIT_L10_INDEPENDENT_REREVIEW.md",
    "qa/MIT_L10_VALIDATION.json",
    "qa/MIT_L10_VISUAL_QA.json",
    "qa/build_mit_l10.py",
    "qa/extend_backend_mit_l10.py",
    "qa/validate_backend_mit_l10.py",
    "qa/validate_mit_l10.py",
    "source/en/mit-10-lecture-6-closed-intersections-hyperplanes-semantic-witness.md",
    "source/id-ID/mit-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.md",
    "source/id-ID/mit-l10-after-body.html",
    "source/id-ID/mit-l10-before-body.html",
    "source/id-ID/mit-l10-pdf-filter.lua",
    "source/id-ID/mit-l10-preamble.tex",
    "source/id-ID/mit-l10.css",
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
            "release-config-mit-l10.json is deliberately absent; supply final "
            "backend counts/hashes and pre-publication control hashes first"
        )
    config = read_json(CONFIG_PATH)
    boundary = config.get("boundary", {})
    if (
        config.get("schema") != "o015-mit-l10-release-config-v1"
        or config.get("parent_record_id") != "22076259"
        or config.get("parent_record_doi") != "10.5281/zenodo.22076259"
        or config.get("concept_id") != "22059741"
        or config.get("concept_doi") != "10.5281/zenodo.22059741"
        or boundary.get("source_pages") != SOURCE_PAGES
        or boundary.get("next_source_page") != NEXT_SOURCE_PAGE
        or boundary.get("next_source_heading") != NEXT_SOURCE_HEADING
        or config.get("expected_inherited_file_count") != 82
        or config.get("expected_addition_file_count") != 8
        or config.get("expected_release_file_count") != 90
        or config.get("status") != "partial"
    ):
        raise RuntimeError("L10 release config has a different lineage, boundary, count, or status")

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
        ROOT / "qa/MIT_L10_BACKEND_VALIDATION.json",
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
    content = read_json(ROOT / "qa/MIT_L10_VALIDATION.json")
    backend = read_json(ROOT / "qa/MIT_L10_BACKEND_VALIDATION.json")
    boundary = content.get("boundary", {})
    if (
        content.get("schema") != "o015-mit-l10-validation-v1"
        or content.get("result") != "pass"
        or content.get("errors") != []
        or content.get("release_ready") is not True
        or boundary.get("source_pdf_pages") != SOURCE_PAGES
        or boundary.get("next_source_page") != NEXT_SOURCE_PAGE
        or boundary.get("next_heading") != NEXT_SOURCE_HEADING
        or boundary.get("source_pages") != 22
        or boundary.get("source_items") != 70
        or boundary.get("source_display_wrappers") != 41
        or boundary.get("display_formula_blocks") != 41
        or boundary.get("source_figures") != 16
        or boundary.get("source_figure_panels") != 24
        or boundary.get("copied_source_graphics") != 0
    ):
        raise RuntimeError("L10 reader closure has not passed the frozen Lecture 6 boundary")

    expected = config["backend"]
    expected_corrections = [f"O015-MIT-SEM-{number:04d}" for number in range(20, 31)]
    if (
        backend.get("schema") != "o015-mit-l10-backend-validation-v1"
        or backend.get("result") != "pass"
        or backend.get("errors") != []
        or backend.get("protected_baseline", {}).get("records")
        != expected["protected_record_count"]
        or backend.get("protected_baseline", {}).get("record_bytes_and_relative_order_stable") is not True
        or backend.get("admission", {}).get("new_records") != expected["new_record_count"]
        or backend.get("admission", {}).get("final_records") != expected["record_count"]
        or backend.get("topology", {}).get("source_pages") != SOURCE_PAGES
        or backend.get("topology", {}).get("segments") != 22
        or backend.get("topology", {}).get("top_level_items") != 70
        or backend.get("topology", {}).get("nested_items") != 14
        or backend.get("topology", {}).get("display_surfaces") != 41
        or backend.get("topology", {}).get("figure_blocks") != 16
        or backend.get("topology", {}).get("figure_panels") != 24
        or backend.get("topology", {}).get("worked_examples") != 3
        or backend.get("topology", {}).get("correction_event_ids") != expected_corrections
        or backend.get("deterministic_regeneration", {}).get("runs_required") != 2
        or backend.get("deterministic_regeneration", {}).get("runs_completed") != 2
        or backend.get("deterministic_regeneration", {}).get("canonical_match") is not True
        or backend.get("schema_constraint", {}).get("schema_changed") is not False
    ):
        raise RuntimeError("L10 backend closure does not match the supplied final transition")
    for kind in ("jsonl", "csv"):
        if backend.get("admission", {}).get(kind) != expected[kind]:
            raise RuntimeError(f"L10 backend {kind} identity differs from supplied final transition")


def make_lock() -> dict:
    config = load_config()
    validate_closure(config)
    paths = sorted(set(MATERIAL_PATHS + CONTROL_PATHS))
    missing = [relative for relative in paths if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError("missing release inputs:\n" + "\n".join(missing))
    files = {relative: identity(ROOT / relative) for relative in paths}
    return {
        "schema": "o015-mit-l10-release-input-lock-v1",
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
            raise RuntimeError("existing L10 input lock differs from validated final bytes")
    else:
        with tempfile.NamedTemporaryFile(prefix=".mit-l10-lock-", suffix=".json", dir=HERE, delete=False) as handle:
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
