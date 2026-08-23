#!/usr/bin/env python3
"""Add the MIT 6.253 pages 16-19 course-orientation closure.

The admitted 1,543-record backend is a protected byte-for-byte baseline.  This
workflow adds one L05 unit, four page-addressed segments, explicit source-link
surfaces, correction O015-MIT-SEM-0004, canonical artifacts, QA events, and
relations.  Reruns strip only this workflow and must reconstruct the original
JSONL and CSV baseline bytes exactly before replacement.
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

RECORDED_AT = "2026-08-23T22:00:00Z"
WORKFLOW = "o015-mit-l05-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 1543
BASELINE_JSONL = (1_102_706, "92f6b805a83361f29a830b8c37b1c52f3468cb420d10b9a3a810cf0f8ac20645")
BASELINE_CSV = (1_325_476, "fedc1855df37e006e52ba76d99af2ee132accfa3b416519c39c036454f378a7d")
BASELINE_ID_SET_SHA256 = "7ebf6de13fc7bbe8ae8993f24a01d31e63b9bdc31b9758510f3961a81d103774"
BASELINE_RECORD_SET_SHA256 = "26ef92dc4ac4c1c6dd29396ae5b85795ba67d4d078377aee891abbf337c7c84a"

MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L05_UNIT_ID = "unit.mit.ocw-6.253.l05"
MIT_SOURCE_PAGES = [16, 17, 18, 19]
PAGE_ITEM_COUNTS = {16: 3, 17: 3, 18: 4, 19: 6}
PAGE_NESTED_COUNTS = {16: 7, 17: 12, 18: 7, 19: 0}
SOURCE_URIS = [
    "http://www.athenasc.com/convexduality.html",
    "http://www.stanford.edu/~boyd/cvxbook/",
]

MIT_PDF = (
    "authority/mit-ocw-6.253/course-archive/static_resources/"
    "6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
)
MIT_CENSUS = "00_control/MIT_L05_P16_19_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/ADVERSE_LEDGER.jsonl"
MIT_CORRECTION_SNAPSHOT = "00_control/MIT_L05_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-05-course-orientation-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-05-orientasi-kursus-id.md"
MIT_HTML = "output/html/D90-MIT-05-orientasi-kursus-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-05-orientasi-kursus-id.pdf"
MIT_CSS = "source/id-ID/mit-l05.css"
MIT_PREAMBLE = "source/id-ID/mit-l05-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l03-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l05-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l03-after-body.html"
MIT_BUILDER = "qa/build_mit_l05.py"
MIT_VALIDATOR = "qa/validate_mit_l05.py"
MIT_REPORT = "qa/MIT_L05_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L05_BROWSER_QA.json"
MIT_VISUAL_QA = "qa/MIT_L05_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L05_INDEPENDENT_REREVIEW.md"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")


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


def artifact(record_id: str, kind: str, path: str, rights_id: str, **extra: Any) -> dict[str, Any]:
    size, digest = file_info(path)
    result = common("artifact", record_id, "current")
    result.update({
        "artifact_kind": kind,
        "path": path,
        "bytes": size,
        "sha256": digest,
        "hash_algorithm": "sha256-raw-bytes",
        "rights_id": rights_id,
    })
    result.update(extra)
    return result


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.strip().startswith("::: {") and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
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


def strip_workflow_jsonl(raw: bytes) -> bytes:
    kept: list[bytes] = []
    for line in raw.splitlines(keepends=True):
        record = json.loads(line.decode("utf-8"))
        if record.get("responsible_workflow") != WORKFLOW:
            kept.append(line)
    return b"".join(kept)


def strip_workflow_csv(raw: bytes) -> bytes:
    lines = raw.splitlines(keepends=True)
    if not lines:
        raise ValueError("backend CSV is empty")
    kept = [lines[0]]
    for line in lines[1:]:
        row = next(csv.reader(io.StringIO(line.decode("utf-8"))))
        if len(row) != 5:
            raise ValueError("backend CSV row width differs")
        record = json.loads(row[4])
        if record.get("responsible_workflow") != WORKFLOW:
            kept.append(line)
    return b"".join(kept)


def assert_raw_baseline(jsonl_bytes: bytes, csv_bytes: bytes, context: str) -> None:
    if (len(jsonl_bytes), sha256(jsonl_bytes)) != BASELINE_JSONL:
        raise ValueError(f"{context} JSONL is not the protected 1,543-record baseline")
    if (len(csv_bytes), sha256(csv_bytes)) != BASELINE_CSV:
        raise ValueError(f"{context} CSV is not the protected 1,543-record baseline")


def stage_backend(jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    staged: list[Path] = []
    try:
        for destination, data in ((JSONL_PATH, jsonl_bytes), (CSV_PATH, csv_bytes)):
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.mit-l05-", suffix=".stage", dir=BACKEND, delete=False
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


def ledger_event() -> tuple[dict[str, Any], str]:
    matches = []
    for raw_line in (ROOT / MIT_CORRECTION_SNAPSHOT).read_text(encoding="utf-8").splitlines():
        if not raw_line:
            continue
        event = json.loads(raw_line)
        if event.get("event_id") == "O015-MIT-SEM-0004":
            matches.append(event)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one O015-MIT-SEM-0004 ledger event, found {len(matches)}")
    event = matches[0]
    expected = {
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "surface": "Author surname in the course-outline bibliography",
        "class": "determined_name_correction",
    }
    for field, value in expected.items():
        if event.get(field) != value:
            raise ValueError(f"O015-MIT-SEM-0004 {field} differs")
    live_matches = []
    for raw_line in (ROOT / MIT_LEDGER).read_text(encoding="utf-8").splitlines():
        if raw_line:
            live_event = json.loads(raw_line)
            if live_event.get("event_id") == "O015-MIT-SEM-0004":
                live_matches.append(live_event)
    if live_matches != [event]:
        raise ValueError("live O015-MIT-SEM-0004 event differs from its immutable snapshot")
    return event, sha256(canonical_json(event).encode("utf-8"))


def load_qa_evidence() -> dict[str, Any]:
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    visual = json.loads((ROOT / MIT_VISUAL_QA).read_text(encoding="utf-8"))
    expected_boundary = {
        "source_pdf_pages": MIT_SOURCE_PAGES,
        "next_source_page": 20,
        "next_heading": "LECTURE 2",
        "source_headings": [
            "METHODOLOGICAL TRENDS",
            "COURSE OUTLINE",
            "WHAT TO EXPECT FROM THIS COURSE",
            "A NOTE ON THESE SLIDES",
        ],
        "source_items": 16,
        "nested_bullets": 26,
        "source_figures": 0,
        "source_displays": 0,
        "inline_math_surfaces": 0,
        "source_uris": SOURCE_URIS,
    }
    if report.get("result") != "pass" or report.get("errors") != []:
        raise ValueError("MIT L05 validation report is not passing")
    if report.get("boundary") != expected_boundary:
        raise ValueError("MIT L05 validation boundary differs")
    if browser.get("result") != "pass" or visual.get("result") != "pass":
        raise ValueError("MIT L05 browser/visual evidence differs")
    for item in report.get("files", {}).values():
        path = item.get("path")
        if path and file_info(path) != (item.get("bytes"), item.get("sha256")):
            raise ValueError(f"MIT L05 report binds stale bytes: {path}")
    return report


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema":
        raise ValueError("backend schema identity differs")
    if file_info(MIT_PDF) != SOURCE_PDF_IDENTITY:
        raise ValueError("MIT authority PDF identity differs")
    load_qa_evidence()
    correction_event, correction_event_hash = ledger_event()

    incoming_jsonl = JSONL_PATH.read_bytes()
    incoming_csv = CSV_PATH.read_bytes()
    incoming_records = [json.loads(line) for line in incoming_jsonl.decode("utf-8").splitlines() if line]
    incoming_rows = list(csv.DictReader(io.StringIO(incoming_csv.decode("utf-8", errors="strict"))))
    if [json.loads(row["record_json"]) for row in incoming_rows] != incoming_records:
        raise ValueError("incoming CSV projection differs from JSONL")
    if len({record["id"] for record in incoming_records}) != len(incoming_records):
        raise ValueError("incoming backend has duplicate IDs")

    records = [record for record in incoming_records if record.get("responsible_workflow") != WORKFLOW]
    already_applied = len(records) != len(incoming_records)
    if already_applied:
        assert_raw_baseline(
            strip_workflow_jsonl(incoming_jsonl),
            strip_workflow_csv(incoming_csv),
            "workflow-stripped incoming",
        )
    else:
        assert_raw_baseline(incoming_jsonl, incoming_csv, "incoming")
    if (
        len(records) != BASELINE_RECORD_COUNT
        or id_set_sha256(records) != BASELINE_ID_SET_SHA256
        or record_set_sha256(records) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("stripped backend record set differs from protected baseline")

    baseline_ids = {record["id"] for record in records}
    new_records: list[dict[str, Any]] = []
    new_ids: set[str] = set()

    def add(record: dict[str, Any]) -> None:
        if record["id"] in baseline_ids or record["id"] in new_ids:
            raise ValueError(f"stable-ID collision: {record['id']}")
        new_ids.add(record["id"])
        new_records.append(record)

    segment_ids = [f"d90.mit.ocw-6.253.l05.p{page:03d}" for page in MIT_SOURCE_PAGES]
    all_source_items = [
        f"src-mit-l05-p{page:03d}-i{index:03d}"
        for page in MIT_SOURCE_PAGES for index in range(1, PAGE_ITEM_COUNTS[page] + 1)
    ]
    all_target_items = [item.replace("src-mit-", "d90-mit-", 1) for item in all_source_items]

    unit = common("unit", MIT_L05_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 5,
        "source_local_id": "lecture-1-pages-16-19",
        "source_local_label": "Lecture 1 - Closing Course Orientation",
        "target_local_label": "Kuliah 1 - Penutup Orientasi Kursus",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": MIT_SOURCE_PAGES,
        "next_source_page": 20,
        "next_source_heading": "LECTURE 2",
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 16,
        "nested_source_bullet_count": 26,
        "source_item_ids": all_source_items,
        "target_item_ids": all_target_items,
        "source_heading_count": 4,
        "source_figure_count": 0,
        "source_display_count": 0,
        "inline_math_surface_count": 0,
        "active_uri_count": 2,
        "correction_event_ids": ["O015-MIT-SEM-0004"],
    })
    add(unit)

    for order, page in enumerate(MIT_SOURCE_PAGES, start=1):
        source_anchor = f"src-mit-l05-p{page:03d}"
        target_anchor = f"d90-mit-l05-p{page:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
        record = common("segment", segment_ids[order - 1], "visually_checked")
        page_source_items = [f"{source_anchor}-i{index:03d}" for index in range(1, PAGE_ITEM_COUNTS[page] + 1)]
        page_target_items = [f"{target_anchor}-i{index:03d}" for index in range(1, PAGE_ITEM_COUNTS[page] + 1)]
        record.update({
            "unit_id": MIT_L05_UNIT_ID,
            "order": order,
            "source_edition_id": MIT_WITNESS_EDITION_ID,
            "target_edition_id": MIT_TARGET_EDITION_ID,
            "source_path": MIT_WITNESS,
            "source_line_start": source_slice[0],
            "source_line_end": source_slice[1],
            "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3],
            "source_anchor": source_anchor,
            "source_item_ids": page_source_items,
            "target_path": MIT_TARGET,
            "target_line_start": target_slice[0],
            "target_line_end": target_slice[1],
            "target_bytes": target_slice[2],
            "target_content_sha256": target_slice[3],
            "target_anchor": target_anchor,
            "target_item_ids": page_target_items,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "visually_checked",
            "rights_id": "rights.o015-mit-id-pilot",
            "source_pdf_path": MIT_PDF,
            "source_pdf_page": page,
            "source_pdf_sha256": SOURCE_PDF_IDENTITY[1],
            "source_pdf_pages_total": 340,
            "source_item_count": PAGE_ITEM_COUNTS[page],
            "nested_source_bullet_count": PAGE_NESTED_COUNTS[page],
            "source_figure_count": 0,
            "source_display_count": 0,
            "inline_math_surface_count": 0,
            "source_uri_count": 2 if page == 17 else 0,
            "source_uris": SOURCE_URIS if page == 17 else [],
            "anchor_mapping_rule": "replace src-mit- prefix with d90-mit- prefix",
        })
        add(record)

    # The only positive interactive surfaces in this boundary are its two
    # source hyperlinks.  Absence of exercises, figures, mathematics, and code
    # is retained in the census, unit topology, and QA records rather than
    # expanded into artificial content records.
    surface_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("surface.mit.l05.external-link-athena", "external_link", "present", "present", {"related_segment_ids": [segment_ids[1]], "source_locator": f"{MIT_WITNESS}#src-mit-l05-p017-i001", "target_locator": f"{MIT_TARGET}#d90-mit-l05-p017-i001", "uri": SOURCE_URIS[0], "source_pdf_page": 17}),
        ("surface.mit.l05.external-link-stanford", "external_link", "present", "present", {"related_segment_ids": [segment_ids[1]], "source_locator": f"{MIT_WITNESS}#src-mit-l05-p017-i002", "target_locator": f"{MIT_TARGET}#d90-mit-l05-p017-i002", "uri": SOURCE_URIS[1], "source_pdf_page": 17}),
    ]
    for record_id, surface_type, presence, status, extra in surface_specs:
        record = common("learning_surface", record_id, status)
        record.update({"unit_id": MIT_L05_UNIT_ID, "surface_type": surface_type, "presence": presence, **extra})
        add(record)

    correction = common("correction", "correction.o015-mit-sem-0004", "applied_in_admitted_reader")
    correction.update({
        "source_event_id": "O015-MIT-SEM-0004",
        "source_edition_id": MIT_SOURCE_EDITION_ID,
        "affected_unit_ids": [MIT_L05_UNIT_ID],
        "affected_segment_ids": [segment_ids[1]],
        "source_path": MIT_PDF,
        "source_pdf_page": 17,
        "source_locator": "complete-notes PDF page 17; course-outline bibliography",
        "witness_locator": f"{MIT_WITNESS}#src-mit-l05-p017-i002",
        "target_locator": f"{MIT_TARGET}#d90-mit-l05-p017-i002",
        "surface": correction_event["surface"],
        "source_issue": correction_event["source_issue"],
        "target_action": correction_event["target_action"],
        "correction_class": correction_event["class"],
        "disposition": "applied_in_admitted_reader",
        "shared_ledger_state": "integrated",
        "upstream_report_disposition": "not_submitted",
        "ledger_path": MIT_LEDGER,
        "source_event_record_sha256": correction_event_hash,
        "evidence_artifact_id": "artifact.mit.l05.adverse-ledger-snapshot",
    })
    add(correction)

    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l05.boundary-census", "boundary_census", MIT_CENSUS, "rights.o015-mit-pilot-build-qa", {"source_pdf_pages": MIT_SOURCE_PAGES, "next_source_page": 20}),
        ("artifact.mit.l05.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"source_pdf_pages": MIT_SOURCE_PAGES, "official_editable_source": False, "source_item_count": 16, "nested_source_bullet_count": 26, "source_uri_count": 2}),
        ("artifact.mit.l05.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": MIT_SOURCE_PAGES, "source_item_count": 16, "nested_source_bullet_count": 26, "correction_event_ids": ["O015-MIT-SEM-0004"]}),
        ("artifact.mit.l05.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "none", "source_pages": 4, "external_uri_count": 2}),
        ("artifact.mit.l05.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": 3, "page_size": "A4", "tagged": False, "searchable": True, "external_uri_count": 2}),
        ("artifact.mit.l05.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5 and LuaLaTeX"}),
        ("artifact.mit.l05.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l05.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass"}),
        ("artifact.mit.l05.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "live_viewport_measurement": True}),
        ("artifact.mit.l05.visual-qa", "visual_qa_report", MIT_VISUAL_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "pages": 3}),
        ("artifact.mit.l05.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.mit.l05.adverse-ledger-snapshot", "correction_ledger_snapshot", MIT_CORRECTION_SNAPSHOT, "rights.o015-mit-pilot-build-qa", {"source_event_ids": ["O015-MIT-SEM-0004"], "snapshot_scope": "single immutable correction event"}),
        ("artifact.mit.l05.css", "html_stylesheet", MIT_CSS, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l05.pdf-preamble", "pdf_preamble", MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l05.pdf-filter", "pandoc_lua_filter", MIT_FILTER, "rights.o015-mit-l01-backend-tooling", {"shared_build_dependency": True}),
        ("artifact.mit.l05.before-body", "html_include", MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l05.after-body", "html_include", MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling", {"shared_build_dependency": True}),
        ("artifact.o015.backend-generator-mit-l05", "backend_generator", "qa/extend_backend_mit_l05.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library"}),
        ("artifact.o015.backend-validator-mit-l05", "backend_validator", "qa/validate_backend_mit_l05.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library"}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l05.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.complete-notes-pdf", "artifact.mit.l05.boundary-census", "artifact.mit.l05.semantic-witness"], "authority_pdf_pages": 340, "boundary_pages": MIT_SOURCE_PAGES, "next_source_page": 20}),
        ("qa.o015.mit-l05.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l05.semantic-witness", "artifact.mit.l05.target-source", "artifact.mit.l05.validation"], "official_editable_source": False, "source_items": 16, "nested_source_bullets": 26, "source_figures": 0}),
        ("qa.o015.mit-l05.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l05.validation", "artifact.mit.l05.boundary-census"], "source_page_map": [[page, page] for page in MIT_SOURCE_PAGES], "item_counts": {str(page): PAGE_ITEM_COUNTS[page] for page in MIT_SOURCE_PAGES}, "nested_item_counts": {str(page): PAGE_NESTED_COUNTS[page] for page in MIT_SOURCE_PAGES}, "source_items": 16, "nested_source_bullets": 26, "figures": 0, "source_displays": 0, "inline_math_surfaces": 0}),
        ("qa.o015.mit-l05.links", "external_links", "pass", {"witness_artifact_ids": ["artifact.mit.l05.semantic-witness", "artifact.mit.l05.target-source", "artifact.mit.l05.target-html", "artifact.mit.l05.target-pdf", "artifact.mit.l05.validation"], "source_pdf_page": 17, "unique_source_uris": SOURCE_URIS, "source_annotation_count": 2, "preserved_in_html": True, "preserved_in_pdf": True}),
        ("qa.o015.mit-l05.correction", "correction_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l05.adverse-ledger-snapshot", "artifact.mit.l05.semantic-witness", "artifact.mit.l05.target-source", "artifact.mit.l05.independent-rereview", "artifact.mit.l05.validation"], "source_event_ids": ["O015-MIT-SEM-0004"], "correction_record_ids": ["correction.o015-mit-sem-0004"], "silent_normalization": False}),
        ("qa.o015.mit-l05.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l05.validation", "artifact.mit.l05.independent-rereview"], "source_math_nodes": 0, "target_math_nodes": 0, "display_formulas": 0, "inline_math_surfaces": 0}),
        ("qa.o015.mit-l05.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l05.builder", "artifact.mit.l05.target-html", "artifact.mit.l05.target-pdf", "artifact.mit.l05.validation"], "deterministic_rebuilds": 2, "html_sha256": file_info(MIT_HTML)[1], "pdf_sha256": file_info(MIT_READER_PDF)[1], "toolchain": "Pandoc HTML5 and LuaLaTeX"}),
        ("qa.o015.mit-l05.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l05.target-html", "artifact.mit.l05.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": {"h1": 1, "h2": 6}, "math_nodes": 0, "images": 0, "source_pages": 4, "source_items": 16, "source_figures": 0, "external_uri_count": 2, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l05.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l05.browser-qa", "artifact.mit.l05.target-html"], "desktop_viewport": [1280, 720], "mobile_viewport": [390, 844], "horizontal_overflow": False, "live_measurement": True, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l05.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l05.target-pdf", "artifact.mit.l05.validation"], "pages": 3, "page_size": "A4", "lang": "id-ID", "searchable": True, "tagged": False, "all_pages_visually_inspected": True, "external_uris_preserved": True}),
        ("qa.o015.mit-l05.visual", "visual", "pass", {"witness_artifact_ids": ["artifact.mit.l05.visual-qa", "artifact.mit.l05.target-pdf"], "pages": 3, "all_pages_visually_inspected": True, "render_tool": "pdftoppm"}),
        ("qa.o015.mit-l05.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l05.target-html", "artifact.mit.l05.target-pdf", "artifact.mit.l05.browser-qa", "artifact.mit.l05.visual-qa"], "primary_surface": "semantic_html", "html_static_structure_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"]}),
        ("qa.o015.mit-l05.semantic-rereview", "independent_semantic_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l05.independent-rereview", "artifact.mit.l05.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l05.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded."}),
        ("qa.o015.mit-l05.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l05.boundary-census", "artifact.mit.l05.semantic-witness", "artifact.mit.l05.target-source"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa", "o015-mit-l01-backend-tooling"], "source_graphics_in_boundary": 0, "license": "CC BY-NC-SA 4.0", "change_event_ids": ["O015-MIT-SEM-0004"], "non_endorsement": True}),
        ("qa.o015.mit-l05.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l05", "artifact.o015.backend-validator-mit-l05", "artifact.o015.source-authority", "artifact.o015.component-rights"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_baseline_reconstruction_required": True}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        status = "passed" if result == "pass" else result
        record = common("qa_event", record_id, status)
        record.update({"event_type": event_type, "result": result, "unit_id": MIT_L05_UNIT_ID, **extra})
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l05", "contains", MIT_ROOT_UNIT_ID, MIT_L05_UNIT_ID, "Fifth admitted MIT source-order boundary, complete-notes pages 16-19."),
        ("relation.mit.witness-edition-contains-l05", "contains", MIT_WITNESS_EDITION_ID, MIT_L05_UNIT_ID, "Page-addressed English semantic witness for pages 16-19."),
        ("relation.mit.target-edition-contains-l05", "contains", MIT_TARGET_EDITION_ID, MIT_L05_UNIT_ID, "Built Indonesian semantic derivative for pages 16-19."),
        ("relation.mit.witness-adapts-authority-pdf-l05", "adapts", "artifact.mit.l05.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes PDF pages 16-19."),
        ("relation.mit.target-translates-witness-l05", "translates", "artifact.mit.l05.target-source", "artifact.mit.l05.semantic-witness", "One-to-one page/list translation with disclosed name correction O015-MIT-SEM-0004."),
        ("relation.mit.html-adapts-target-l05", "adapts", "artifact.mit.l05.target-html", "artifact.mit.l05.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l05", "adapts", "artifact.mit.l05.target-pdf", "artifact.mit.l05.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.external-link-athena-depends-on-p017-l05", "depends-on", "surface.mit.l05.external-link-athena", segment_ids[1], "Athena supplementary-material URI occurs on source page 17."),
        ("relation.mit.external-link-stanford-depends-on-p017-l05", "depends-on", "surface.mit.l05.external-link-stanford", segment_ids[1], "Stanford book URI occurs on source page 17."),
        ("relation.mit.browser-qa-depends-on-html-l05", "depends-on", "artifact.mit.l05.browser-qa", "artifact.mit.l05.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.visual-qa-depends-on-pdf-l05", "depends-on", "artifact.mit.l05.visual-qa", "artifact.mit.l05.target-pdf", "Rendered three-page visual QA evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l05", "depends-on", "artifact.mit.l05.validation", "artifact.mit.l05.browser-qa", "Validation binds browser evidence."),
        ("relation.mit.validation-depends-on-visual-qa-l05", "depends-on", "artifact.mit.l05.validation", "artifact.mit.l05.visual-qa", "Validation binds rendered visual evidence."),
        ("relation.mit.validation-depends-on-rereview-l05", "depends-on", "artifact.mit.l05.validation", "artifact.mit.l05.independent-rereview", "Validation binds independent rereview."),
        ("relation.mit.validation-depends-on-boundary-l05", "depends-on", "artifact.mit.l05.validation", "artifact.mit.l05.boundary-census", "Validation binds the frozen pages 16-19 boundary."),
    ]
    for page, segment_id in zip(MIT_SOURCE_PAGES, segment_ids):
        relation_specs.append((f"relation.mit.l05.contains-p{page:03d}", "contains", MIT_L05_UNIT_ID, segment_id, "Ordered one-page semantic segment."))

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
    by_id = {record["id"]: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate IDs after L05 extension")
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
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)])
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    assert_raw_baseline(strip_workflow_jsonl(jsonl_bytes), strip_workflow_csv(csv_bytes), "workflow-stripped output")
    stage_backend(jsonl_bytes, csv_bytes)
    if JSONL_PATH.read_bytes() != jsonl_bytes or CSV_PATH.read_bytes() != csv_bytes:
        raise ValueError("backend readback differs after replacement")

    report_out = {
        "already_applied_on_entry": already_applied,
        "protected_baseline": {
            "record_count": BASELINE_RECORD_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]},
            "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "raw_bytes_reconstructed_exactly": True,
        },
        "new_record_count": len(new_records),
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
        "new_ids_sha256": sha256(("\n".join(sorted(new_ids)) + "\n").encode("utf-8")),
        "record_count": len(records),
        "jsonl": {"bytes": len(jsonl_bytes), "sha256": sha256(jsonl_bytes)},
        "csv": {"bytes": len(csv_bytes), "sha256": sha256(csv_bytes)},
        "unit_id": MIT_L05_UNIT_ID,
        "segment_ids": segment_ids,
        "top_level_items": len(all_source_items),
        "nested_bullets": sum(PAGE_NESTED_COUNTS.values()),
        "source_uris": SOURCE_URIS,
        "correction_id": "correction.o015-mit-sem-0004",
        "result": "pass",
    }
    print(json.dumps(report_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
