#!/usr/bin/env python3
"""Add the MIT 6.253 pages 6--13 boundary to the modular backend.

This is deliberately an additive, fail-closed extension.  The existing
1,430 records (including the L01 pilot and all other O015 lanes) are treated
as a protected baseline.  A rerun removes and reconstructs only records whose
``responsible_workflow`` is this script's finite L02 workflow.  No existing
record is rewritten or deleted, and the two backend files are replaced only
after all references and byte bindings validate.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"

RECORDED_AT = "2026-08-23T19:05:00Z"
WORKFLOW = "o015-mit-l02-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

# The protected input is the public L01/Royer backend boundary.  These
# identities are intentionally explicit so an accidental concurrent mutation
# fails closed instead of being silently incorporated into L02.
BASELINE_RECORD_COUNT = 1430
BASELINE_JSONL = (1_036_556, "ebf44ca94323584e40b548ce36da560899e39a1e76ed2c993a0786b4ee7c4a2b")
BASELINE_CSV = (1_244_072, "bc73abb3457cacc10423c1785a0db70a9007fdef8ac0a2be1de48d25d389fdf5")
BASELINE_ID_SET_SHA256 = "783c884b58e5f6a78616cd435f2fbda7bca01dd3ad499e762203774e871ca518"
BASELINE_RECORD_SET_SHA256 = "d55dd39b0cbce33d7c5933bf7bec986661259663f148ff7687ebc65caa018d7c"

COURSE_ID = "course.d90.advanced-optimization-convex-analysis"
MIT_RESOURCE_ID = "resource.mit.ocw-6.253-convex-analysis-optimization"
MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L02_UNIT_ID = "unit.mit.ocw-6.253.l02"

MIT_PDF = (
    "authority/mit-ocw-6.253/course-archive/static_resources/"
    "6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
)
MIT_WITNESS = "source/en/mit-02-duality-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-02-dualitas-dan-perilaku-pengecualian-id.md"
MIT_HTML = "output/html/D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.pdf"
MIT_BUILDER = "qa/build_mit_l02.py"
MIT_VALIDATOR = "qa/validate_mit_l02.py"
MIT_REPORT = "qa/MIT_L02_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L02_BROWSER_QA.json"
MIT_REREVIEW = "qa/MIT_L02_INDEPENDENT_REREVIEW.md"
MIT_CENSUS = "00_control/MIT_L02_BOUNDARY_CENSUS.md"

L02_SOURCE_PAGES = list(range(6, 14))
PAGE_ITEM_COUNTS = {6: 3, 7: 3, 8: 2, 9: 1, 10: 4, 11: 2, 12: 0, 13: 4}
PAGE_NESTED_COUNTS = {6: 0, 7: 0, 8: 0, 9: 2, 10: 4, 11: 0, 12: 0, 13: 1}
FIGURE_PAGES = [6, 7, 8, 9, 11, 12, 13]
SOURCE_PDF_BYTES = 8_030_116
SOURCE_PDF_SHA256 = "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    data = path.read_bytes()
    return len(data), sha256(data)


def id_set_sha256(records: list[dict[str, Any]]) -> str:
    return sha256(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def record_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "".join(canonical_json(record) + "\n" for record in sorted(records, key=lambda item: item["id"]))
    return sha256(payload.encode("utf-8"))


def common(entity_type: str, record_id: str, status: str) -> dict[str, Any]:
    return {
        "schema": RECORD_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "entity_type": entity_type,
        "id": record_id,
        "recorded_at": RECORDED_AT,
        "responsible_workflow": WORKFLOW,
        "status": status,
    }


def artifact(record_id: str, kind: str, path: str, rights_id: str | None = None, **extra: Any) -> dict[str, Any]:
    size, digest = file_info(path)
    record = common("artifact", record_id, "current")
    record.update({
        "artifact_kind": kind,
        "path": path,
        "bytes": size,
        "sha256": digest,
        "hash_algorithm": "sha256-raw-bytes",
    })
    if rights_id is not None:
        record["rights_id"] = rights_id
    record.update(extra)
    return record


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    """Return one fenced-div's 1-based lines, byte length, and UTF-8 hash."""

    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if line.strip().startswith("::: {")
        and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
    ]
    if len(starts) != 1:
        raise ValueError(f"expected one fenced div #{anchor} in {relative}, found {len(starts)}")
    start = starts[0]
    depth = 0
    end = -1
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("::: {"):
            depth += 1
        elif stripped == ":::":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end < start:
        raise ValueError(f"unclosed fenced div #{anchor} in {relative}")
    data = ("\n".join(lines[start : end + 1]) + "\n").encode("utf-8")
    return start + 1, end + 1, len(data), sha256(data)


def stage_backend(jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    staged: list[Path] = []
    try:
        for destination, data in ((JSONL_PATH, jsonl_bytes), (CSV_PATH, csv_bytes)):
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{destination.name}.mit-l02-",
                suffix=".stage",
                dir=BACKEND,
                delete=False,
            ) as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append(Path(handle.name))
        if staged[0].read_bytes() != jsonl_bytes or staged[1].read_bytes() != csv_bytes:
            raise ValueError("staged backend readback differs before replacement")
        os.replace(staged[0], JSONL_PATH)
        staged.pop(0)
        os.replace(staged[0], CSV_PATH)
        staged.pop(0)
    finally:
        for path in staged:
            path.unlink(missing_ok=True)


def load_report_and_check() -> dict[str, Any]:
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    if report.get("result") != "pass" or report.get("errors") != []:
        raise ValueError("MIT L02 validation report is not passing")
    if browser.get("result") != "pass" or browser.get("console_warnings_or_errors") != []:
        raise ValueError("MIT L02 browser QA is not passing")
    if report.get("boundary") != {
        "source_pdf_pages": L02_SOURCE_PAGES,
        "next_topic_starts_source_page": 14,
        "source_items": 19,
        "source_figures": 7,
        "source_displays": 1,
        "nested_source_lists": 7,
        "target_math_nodes": 61,
    }:
        raise ValueError("MIT L02 validation boundary differs")
    for item in report["files"].values():
        path = item.get("path")
        if path and path != MIT_PDF and file_info(path) != (item["bytes"], item["sha256"]):
            raise ValueError(f"MIT L02 report binds stale bytes: {path}")
    return report


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema":
        raise ValueError("backend schema identity differs")
    if file_info(MIT_PDF) != (SOURCE_PDF_BYTES, SOURCE_PDF_SHA256):
        raise ValueError("MIT authority PDF identity differs")
    report = load_report_and_check()

    incoming_jsonl = JSONL_PATH.read_bytes()
    incoming_csv = CSV_PATH.read_bytes()
    incoming_records = [json.loads(line) for line in incoming_jsonl.decode("utf-8").splitlines() if line]
    if len({record["id"] for record in incoming_records}) != len(incoming_records):
        raise ValueError("incoming backend has duplicate IDs")
    records = [record for record in incoming_records if record.get("responsible_workflow") != WORKFLOW]
    already_applied = len(records) != len(incoming_records)
    # On a first run, the input must be exactly the last published backend
    # boundary.  On reruns, stripping our own records must restore that byte
    # and ID boundary, preventing accidental loss of another lane's records.
    if not already_applied:
        if (len(incoming_jsonl), sha256(incoming_jsonl)) != BASELINE_JSONL:
            raise ValueError("incoming JSONL is not the protected 1,430-record baseline")
        if (len(CSV_PATH.read_bytes()), sha256(CSV_PATH.read_bytes())) != BASELINE_CSV:
            raise ValueError("incoming CSV is not the protected baseline")
    if (
        len(records) != BASELINE_RECORD_COUNT
        or id_set_sha256(records) != BASELINE_ID_SET_SHA256
        or record_set_sha256(records) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("stripped backend baseline differs from the protected boundary")

    existing_ids = {record["id"] for record in records}
    new_records: list[dict[str, Any]] = []
    new_ids: set[str] = set()

    def add(record: dict[str, Any]) -> None:
        record_id = record["id"]
        if record_id in existing_ids or record_id in new_ids:
            raise ValueError(f"stable-ID collision: {record_id}")
        new_ids.add(record_id)
        new_records.append(record)

    # The contiguous source-order unit and its page-addressed segments.
    unit = common("unit", MIT_L02_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 2,
        "source_local_id": "lecture-1-topic-2-pages-6-13",
        "source_local_label": "Lecture 1 - Duality through Exceptional Behavior",
        "target_local_label": "Kuliah 1 - Dualitas hingga Perilaku Pengecualian",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": L02_SOURCE_PAGES,
        "next_source_page": 14,
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 19,
        "source_figure_count": 7,
        "source_display_count": 1,
    })
    add(unit)

    segment_ids: list[str] = []
    for order, page in enumerate(L02_SOURCE_PAGES, start=1):
        source_anchor = f"src-mit-l02-p{page:03d}"
        target_anchor = f"d90-mit-l02-p{page:03d}"
        source_start, source_end, source_bytes, source_hash = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_start, target_end, target_bytes, target_hash = fenced_div_slice(MIT_TARGET, target_anchor)
        record_id = f"d90.mit.ocw-6.253.l02.p{page:03d}"
        segment_ids.append(record_id)
        record = common("segment", record_id, "visually_checked")
        record.update({
            "unit_id": MIT_L02_UNIT_ID,
            "order": order,
            "source_edition_id": MIT_WITNESS_EDITION_ID,
            "target_edition_id": MIT_TARGET_EDITION_ID,
            "source_path": MIT_WITNESS,
            "source_line_start": source_start,
            "source_line_end": source_end,
            "source_bytes": source_bytes,
            "source_content_sha256": source_hash,
            "source_anchor": source_anchor,
            "target_path": MIT_TARGET,
            "target_line_start": target_start,
            "target_line_end": target_end,
            "target_bytes": target_bytes,
            "target_content_sha256": target_hash,
            "target_anchor": target_anchor,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "visually_checked",
            "rights_id": "rights.o015-mit-id-pilot",
            "source_pdf_path": MIT_PDF,
            "source_pdf_page": page,
            "source_pdf_sha256": SOURCE_PDF_SHA256,
            "source_pdf_pages_total": 340,
            "source_item_count": PAGE_ITEM_COUNTS[page],
            "nested_source_bullet_count": PAGE_NESTED_COUNTS[page],
            "source_figure_count": 1 if page in FIGURE_PAGES else 0,
            "source_display_count": 1 if page == 9 else 0,
            "anchor_mapping_rule": "replace src-mit- prefix with d90-mit- prefix",
        })
        add(record)

    # Learning-surface absence is explicit: these pages contain no exercises,
    # hints, answers, or solutions, while the semantic HTML reader is primary.
    surface_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("surface.mit.l02.exercise-inventory", "exercise", "absent", "source_absent", {"count": 0, "absence_evidence": MIT_CENSUS}),
        ("surface.mit.l02.hint-inventory", "hint", "absent", "source_absent", {"count": 0, "absence_evidence": MIT_CENSUS}),
        ("surface.mit.l02.answer-inventory", "answer", "absent", "source_absent", {"count": 0, "absence_evidence": MIT_CENSUS}),
        ("surface.mit.l02.solution-inventory", "solution", "absent", "source_absent", {"count": 0, "absence_evidence": MIT_CENSUS}),
        ("surface.mit.l02.semantic-html", "semantic_html_reader", "present", "present", {"artifact_id": "artifact.mit.l02.target-html", "primary_accessible_surface": True, "lang": "id-ID"}),
        ("surface.mit.l02.reflowed-pdf", "reflowed_pdf_reader", "present_with_limitation", "present_with_limitation", {"artifact_id": "artifact.mit.l02.target-pdf", "pages": 5, "searchable": True, "tagged": False}),
        ("surface.mit.l02.figure-inventory", "source_figure_inventory", "present_with_limitation", "present_with_limitation", {"count": 7, "omitted_source_graphics": True, "semantic_descriptions": True, "rights_evidence": "Athena permission-only graphics are not redistributed."}),
    ]
    for record_id, surface_type, presence, status, extra in surface_specs:
        record = common("learning_surface", record_id, status)
        record.update({"unit_id": MIT_L02_UNIT_ID, "surface_type": surface_type, "presence": presence, **extra})
        add(record)

    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l02.boundary-census", "boundary_census", MIT_CENSUS, "rights.o015-mit-pilot-build-qa", {"source_pdf_pages": L02_SOURCE_PAGES, "next_topic_starts_page": 14}),
        ("artifact.mit.l02.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"source_pdf_pages": L02_SOURCE_PAGES, "official_editable_source": False, "source_figure_count": 7}),
        ("artifact.mit.l02.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": L02_SOURCE_PAGES, "source_figure_count": 7}),
        ("artifact.mit.l02.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "MathML", "source_pages": 8}),
        ("artifact.mit.l02.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": 5, "page_size": "A4", "tagged": False, "searchable": True}),
        ("artifact.mit.l02.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5/MathML and LuaLaTeX"}),
        ("artifact.mit.l02.css", "html_stylesheet", "source/id-ID/mit-l02.css", "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l02.pdf-preamble", "pdf_preamble", "source/id-ID/mit-l02-preamble.tex", "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l02.pdf-filter", "pandoc_lua_filter", "source/id-ID/mit-l02-pdf-filter.lua", "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l02.before-body", "html_include", "source/id-ID/mit-l02-before-body.html", "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l02.after-body", "html_include", "source/id-ID/mit-l02-after-body.html", "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l02.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l02.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass"}),
        ("artifact.mit.l02.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "desktop_mobile": True}),
        ("artifact.mit.l02.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.o015.backend-generator-mit-l02", "backend_generator", "qa/extend_backend_mit_l02.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library"}),
        ("artifact.o015.backend-validator-mit-l02", "backend_validator", "qa/validate_backend_mit_l02.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library"}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l02.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.l02.boundary-census", "artifact.mit.complete-notes-pdf"], "authority_pdf_pages": 340, "boundary_pages": L02_SOURCE_PAGES, "next_topic_starts_page": 14}),
        ("qa.o015.mit-l02.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l02.semantic-witness", "artifact.mit.l02.target-source", "artifact.mit.l02.validation"], "official_editable_source": False, "source_items": 19, "source_figures": 7}),
        ("qa.o015.mit-l02.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l02.validation", "artifact.mit.l02.boundary-census"], "source_page_map": [[p, p] for p in L02_SOURCE_PAGES], "item_counts": {str(k): v for k, v in PAGE_ITEM_COUNTS.items()}, "nested_source_bullets": 7, "figures": 7, "source_displays": 1}),
        ("qa.o015.mit-l02.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l02.validation", "artifact.mit.l02.independent-rereview"], "source_math_nodes": 61, "target_math_nodes": 61, "display_formulas": 6, "correction_event_ids": []}),
        ("qa.o015.mit-l02.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l02.builder", "artifact.mit.l02.target-html", "artifact.mit.l02.target-pdf", "artifact.mit.l02.validation"], "deterministic_rebuilds": 2, "html_sha256": file_info(MIT_HTML)[1], "pdf_sha256": file_info(MIT_READER_PDF)[1], "toolchain": "Pandoc HTML5/MathML and LuaLaTeX"}),
        ("qa.o015.mit-l02.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l02.target-html", "artifact.mit.l02.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": {"h1": 1, "h2": 10}, "mathml_nodes": 61, "display_mathml_nodes": 6, "images": 0, "source_pages": 8, "source_items": 19, "source_figures": 7, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l02.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l02.browser-qa", "artifact.mit.l02.target-html"], "desktop_viewport": [1280, 720], "mobile_viewport": [390, 844], "horizontal_overflow": False, "display_math_overflow": False, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l02.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l02.target-pdf", "artifact.mit.l02.validation"], "pages": 5, "page_size": "A4", "lang": "id-ID", "searchable": True, "fonts_with_tounicode": True, "tagged": False, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l02.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l02.target-html", "artifact.mit.l02.target-pdf", "artifact.mit.l02.browser-qa"], "primary_surface": "semantic_html", "html_reflow_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "permission-gated source graphics are represented semantically", "independent human/native-speaker Indonesian review is not recorded"]}),
        ("qa.o015.mit-l02.math-rereview", "independent_mathematical_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l02.independent-rereview", "artifact.mit.l02.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l02.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded."}),
        ("qa.o015.mit-l02.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l02.boundary-census"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa"], "athena_figures_in_boundary": 0, "athena_component_status": "excluded", "semantic_figure_descriptions": 7}),
        ("qa.o015.mit-l02.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l02", "artifact.o015.backend-validator-mit-l02", "artifact.o015.source-authority", "artifact.o015.component-rights", "artifact.o015.adverse-ledger"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1]}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        record = common("qa_event", record_id, "passed" if result == "pass" else result)
        record.update({"event_type": event_type, "result": result, **extra})
        record["unit_id"] = MIT_L02_UNIT_ID
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l02", "contains", MIT_ROOT_UNIT_ID, MIT_L02_UNIT_ID, "Second admitted MIT topic boundary, pages 6-13."),
        ("relation.mit.witness-edition-contains-l02", "contains", MIT_WITNESS_EDITION_ID, MIT_L02_UNIT_ID, "Page-addressed English semantic witness for pages 6-13."),
        ("relation.mit.target-edition-contains-l02", "contains", MIT_TARGET_EDITION_ID, MIT_L02_UNIT_ID, "Built Indonesian semantic derivative for pages 6-13."),
        ("relation.mit.witness-adapts-authority-pdf-l02", "adapts", "artifact.mit.l02.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes pages 6-13."),
        ("relation.mit.target-translates-witness-l02", "translates", "artifact.mit.l02.target-source", "artifact.mit.l02.semantic-witness", "One-to-one page/item translation with seven omitted-graphic descriptions."),
        ("relation.mit.html-adapts-target-l02", "adapts", "artifact.mit.l02.target-html", "artifact.mit.l02.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l02", "adapts", "artifact.mit.l02.target-pdf", "artifact.mit.l02.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.browser-qa-depends-on-html-l02", "depends-on", "artifact.mit.l02.browser-qa", "artifact.mit.l02.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l02", "depends-on", "artifact.mit.l02.validation", "artifact.mit.l02.browser-qa", "Validation binds browser evidence."),
        ("relation.mit.validation-depends-on-rereview-l02", "depends-on", "artifact.mit.l02.validation", "artifact.mit.l02.independent-rereview", "Validation binds independent rereview."),
        ("relation.mit.validation-depends-on-boundary-l02", "depends-on", "artifact.mit.l02.validation", "artifact.mit.l02.boundary-census", "Validation binds the frozen page boundary."),
    ]
    for page, segment_id in zip(L02_SOURCE_PAGES, segment_ids):
        relation_specs.append((f"relation.mit.l02.contains-p{page:03d}", "contains", MIT_L02_UNIT_ID, segment_id, "Ordered one-page semantic segment."))
    relation_triples: set[tuple[str, str, str]] = set()
    for record_id, relation_type, source_id, target_id, note in relation_specs:
        triple = (relation_type, source_id, target_id)
        if triple in relation_triples:
            raise ValueError(f"duplicate new relation triple: {triple}")
        relation_triples.add(triple)
        record = common("relation", record_id, "current")
        record.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        add(record)

    records.extend(new_records)
    if len({record["id"] for record in records}) != len(records):
        raise ValueError("duplicate record IDs after L02 extension")
    by_id = {record["id"]: record for record in records}
    for record in records:
        for field in schema["required_common"] + schema["required_by_entity"].get(record["entity_type"], []):
            if field not in record:
                raise ValueError(f"{record['id']}: missing required field {field}")
        for field in schema["reference_fields"]:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for target in values:
                if isinstance(target, str) and target not in by_id:
                    raise ValueError(f"{record['id']}: unresolved {field} -> {target}")

    entity_rank = {entity_type: rank for rank, entity_type in enumerate(schema["entity_order"])}
    records.sort(key=lambda record: (entity_rank[record["entity_type"]], record["id"]))
    jsonl_bytes = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    csv_buffer = io.StringIO(newline="")
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(schema["csv_columns"])
    for record in records:
        writer.writerow([
            record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)
        ])
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    stage_backend(jsonl_bytes, csv_bytes)

    report_out = {
        "already_applied_on_entry": already_applied,
        "protected_baseline": {"record_count": BASELINE_RECORD_COUNT, "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]}, "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]}, "id_set_sha256": BASELINE_ID_SET_SHA256, "record_set_sha256": BASELINE_RECORD_SET_SHA256},
        "new_record_count": len(new_records),
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
        "new_ids_sha256": sha256(("\n".join(sorted(new_ids)) + "\n").encode("utf-8")),
        "record_count": len(records),
        "entity_counts": dict(sorted(Counter(record["entity_type"] for record in records).items())),
        "jsonl": {"bytes": len(jsonl_bytes), "sha256": sha256(jsonl_bytes)},
        "csv": {"bytes": len(csv_bytes), "sha256": sha256(csv_bytes)},
        "segment_ids": segment_ids,
        "result": "pass",
    }
    print(json.dumps(report_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
