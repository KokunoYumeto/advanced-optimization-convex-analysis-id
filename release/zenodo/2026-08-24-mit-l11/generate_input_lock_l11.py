#!/usr/bin/env python3
"""Freeze MIT-L11 inputs only after canonical backend/control finalization.

This generator is local and fail-closed. It performs no network, credential,
Git, publication, backend, or control mutation. The deliberately absent final
config must be created from the adjacent template after the canonical backend
admission and all prepublication controls have reached their final bytes.
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
CONFIG_PATH = HERE / "release-config-mit-l11.json"
LOCK_PATH = HERE / "release-input-lock-mit-l11.json"
SOURCE_PAGES = list(range(86, 98))
NEXT_SOURCE_PAGE = 98
NEXT_SOURCE_HEADING = "LECTURE 8 - LECTURE OUTLINE"
EXPECTED_EVENTS = [
    "O015-MIT-SEM-0034",
    "O015-MIT-SEM-0035",
    "O015-MIT-SEM-0036",
    "O015-MIT-SEM-0037",
    "O015-MIT-SEM-0040",
    "O015-MIT-SEM-0031",
    "O015-MIT-SEM-0038",
    "O015-MIT-SEM-0039",
    "O015-MIT-SEM-0032",
    "O015-MIT-SEM-0033",
]

MATERIAL_PATHS = [
    "00_control/MIT_L11_CORRECTION_SNAPSHOT.jsonl",
    "00_control/MIT_L11_LECTURE_7_BOUNDARY_CENSUS.md",
    "backend/records.csv",
    "backend/records.jsonl",
    "output/html/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.html",
    "output/pdf/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.pdf",
    "qa/MIT_L11_BACKEND_VALIDATION.json",
    "qa/MIT_L11_BROWSER_QA.json",
    "qa/MIT_L11_INDEPENDENT_REREVIEW.md",
    "qa/MIT_L11_VALIDATION.json",
    "qa/MIT_L11_VISUAL_QA.json",
    "qa/build_mit_l11.py",
    "qa/extend_backend_mit_l11.py",
    "qa/validate_backend_mit_l11.py",
    "qa/validate_mit_l11.py",
    "source/en/mit-11-lecture-7-separation-conjugacy-semantic-witness.md",
    "source/id-ID/mit-11-kuliah-7-pemisahan-dan-konjugasi-id.md",
    "source/id-ID/mit-l11-after-body.html",
    "source/id-ID/mit-l11-before-body.html",
    "source/id-ID/mit-l11-pdf-filter.lua",
    "source/id-ID/mit-l11-preamble.tex",
    "source/id-ID/mit-l11.css",
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
    if identity(path) != expected:
        raise RuntimeError(f"{label} differs from supplied final identity: {path}")


def load_config(*, verify_live_controls: bool = True) -> dict:
    if not CONFIG_PATH.is_file():
        raise RuntimeError(
            "release-config-mit-l11.json is deliberately absent; supply final "
            "canonical-backend counts/hashes and prepublication control hashes first"
        )
    config = read_json(CONFIG_PATH)
    boundary = config.get("boundary", {})
    if (
        config.get("schema") != "o015-mit-l11-release-config-v1"
        or config.get("parent_record_id") != "22077419"
        or config.get("parent_record_doi") != "10.5281/zenodo.22077419"
        or config.get("concept_id") != "22059741"
        or config.get("concept_doi") != "10.5281/zenodo.22059741"
        or boundary.get("source_pages") != SOURCE_PAGES
        or boundary.get("next_source_page") != NEXT_SOURCE_PAGE
        or boundary.get("next_source_heading") != NEXT_SOURCE_HEADING
        or config.get("expected_inherited_file_count") != 90
        or config.get("expected_addition_file_count") != 8
        or config.get("expected_release_file_count") != 98
        or config.get("status") != "partial"
    ):
        raise RuntimeError("L11 config has a different lineage, boundary, count, or status")

    backend = config.get("backend", {})
    counts = [backend.get("protected_record_count"), backend.get("new_record_count"), backend.get("record_count")]
    if any(not isinstance(value, int) or value <= 0 for value in counts) or counts[0] + counts[1] != counts[2]:
        raise RuntimeError("final positive backend counts are absent or inconsistent")
    require_identity(ROOT / "backend/records.jsonl", backend.get("jsonl"), "backend JSONL")
    require_identity(ROOT / "backend/records.csv", backend.get("csv"), "backend CSV")
    require_identity(ROOT / "qa/MIT_L11_BACKEND_VALIDATION.json", backend.get("validation"), "backend validation")

    controls = config.get("controls")
    if not isinstance(controls, dict) or set(controls) != set(CONTROL_PATHS):
        raise RuntimeError("config must supply exactly the ten required prepublication controls")
    for relative in CONTROL_PATHS:
        if not valid_identity(controls[relative]):
            raise RuntimeError(f"control {relative} identity is absent or not final")
        if verify_live_controls:
            require_identity(ROOT / relative, controls[relative], f"control {relative}")
    return config


def validate_closure(config: dict) -> None:
    content = read_json(ROOT / "qa/MIT_L11_VALIDATION.json")
    backend = read_json(ROOT / "qa/MIT_L11_BACKEND_VALIDATION.json")
    boundary = content.get("boundary", {})
    if (
        content.get("schema") != "o015-mit-l11-validation-v1"
        or content.get("result") != "pass"
        or content.get("errors") != []
        or content.get("release_ready") is not True
        or boundary.get("source_pdf_pages") != SOURCE_PAGES
        or boundary.get("next_source_page") != NEXT_SOURCE_PAGE
        or boundary.get("next_heading") != NEXT_SOURCE_HEADING
        or boundary.get("source_pages") != 12
        or boundary.get("source_items") != 36
        or boundary.get("source_display_wrappers") != 21
        or boundary.get("display_formula_blocks") != 21
        or boundary.get("source_figures") != 7
        or boundary.get("source_figure_panels") != 16
        or boundary.get("copied_source_graphics") != 0
        or any(boundary.get(key) != 0 for key in ("exercises", "hints", "answers", "solutions", "code_surfaces", "interactive_surfaces"))
    ):
        raise RuntimeError("L11 reader closure has not passed the frozen Lecture 7 boundary")

    expected = config["backend"]
    admission = backend.get("admission", {})
    regeneration = backend.get("deterministic_regeneration", {})
    identities = regeneration.get("identities", [])
    if (
        backend.get("schema") != "o015-mit-l11-backend-validation-v1"
        or backend.get("result") != "pass"
        or backend.get("errors") != []
        or backend.get("protected_baseline", {}).get("records") != expected["protected_record_count"]
        or backend.get("protected_baseline", {}).get("record_bytes_and_relative_order_stable") is not True
        or admission.get("canonical_backend_written") is not True
        or admission.get("disposition") != "validated_canonical_backend"
        or admission.get("new_records") != expected["new_record_count"]
        or admission.get("final_records") != expected["record_count"]
        or admission.get("jsonl") != expected["jsonl"]
        or admission.get("csv") != expected["csv"]
        or backend.get("topology", {}).get("source_pages") != SOURCE_PAGES
        or backend.get("topology", {}).get("segments") != 12
        or backend.get("topology", {}).get("semantic_items") != 36
        or backend.get("topology", {}).get("nested_items") != 8
        or backend.get("topology", {}).get("display_surfaces") != 21
        or backend.get("topology", {}).get("figure_blocks") != 7
        or backend.get("topology", {}).get("figure_panels") != 16
        or backend.get("topology", {}).get("worked_examples") != 3
        or backend.get("topology", {}).get("counterexamples") != 1
        or backend.get("topology", {}).get("correction_event_ids") != EXPECTED_EVENTS
        or regeneration.get("runs_required") != 2
        or regeneration.get("runs_completed") != 2
        or regeneration.get("input_dataset_match") is not True
        or len(identities) != 2
        or any(item.get("jsonl") != expected["jsonl"] or item.get("csv") != expected["csv"] for item in identities)
        or backend.get("schema_constraint", {}).get("schema_changed") is not False
    ):
        raise RuntimeError("L11 canonical backend closure does not match the supplied transition")


def make_lock() -> dict:
    config = load_config()
    validate_closure(config)
    paths = sorted(set(MATERIAL_PATHS + CONTROL_PATHS))
    missing = [relative for relative in paths if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError("missing release inputs:\n" + "\n".join(missing))
    files = {relative: identity(ROOT / relative) for relative in paths}
    return {
        "schema": "o015-mit-l11-release-input-lock-v1",
        "boundary": {"source_pages": SOURCE_PAGES, "next_source_page": NEXT_SOURCE_PAGE, "next_source_heading": NEXT_SOURCE_HEADING},
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
            raise RuntimeError("existing L11 input lock differs from validated final bytes")
    else:
        with tempfile.NamedTemporaryFile(prefix=".mit-l11-lock-", suffix=".json", dir=HERE, delete=False) as handle:
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
