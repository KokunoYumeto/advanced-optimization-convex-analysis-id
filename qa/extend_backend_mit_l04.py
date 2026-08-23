#!/usr/bin/env python3
"""Add the bounded MIT 6.253 page-15 closure to the modular backend.

The 1,495-record L02 boundary is a protected byte-for-byte baseline.  This
script adds only the page-15 unit, page segment, inline-math surface,
page-addressed artifacts, QA events, and relations.  Reruns remove and
reconstruct only this workflow's own records; every other record is checked
by canonical record-set hash before replacement.
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

RECORDED_AT = "2026-08-23T20:30:00Z"
WORKFLOW = "o015-mit-l04-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 1495
BASELINE_JSONL = (1_076_672, "61422fc3d0a1dfa3fed57f3710ae0ffbefb48b8b45957c25ed7455d3a9bd05e7")
BASELINE_CSV = (1_293_072, "146f9a251bcd6b7c9938debc5e9b3f8d680cb51b6d6309bc9a85c90269d22f82")
BASELINE_ID_SET_SHA256 = "0bd88fee9666181e30211465d7e4674f9f90022cee68eb02e21d6419279482b5"
BASELINE_RECORD_SET_SHA256 = "8b9fc6f5aafad76c2df350d3142ff05aefeaba97034b5136db080e2ac08e2b1c"

COURSE_ID = "course.d90.advanced-optimization-convex-analysis"
MIT_RESOURCE_ID = "resource.mit.ocw-6.253-convex-analysis-optimization"
MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L04_UNIT_ID = "unit.mit.ocw-6.253.l04"
MIT_L04_SEGMENT_ID = "d90.mit.ocw-6.253.l04.p015"
MIT_INLINE_SURFACE_ID = "surface.mit.l04.inline-math-ell-one"

MIT_PDF = (
    "authority/mit-ocw-6.253/course-archive/static_resources/"
    "6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
)
MIT_WITNESS = "source/en/mit-04-rise-algorithmic-era-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-04-kebangkitan-era-algoritmik-id.md"
MIT_HTML = "output/html/D90-MIT-04-kebangkitan-era-algoritmik-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-04-kebangkitan-era-algoritmik-id.pdf"
MIT_BUILDER = "qa/build_mit_l04.py"
MIT_VALIDATOR = "qa/validate_mit_l04.py"
MIT_REPORT = "qa/MIT_L04_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L04_BROWSER_QA.json"
MIT_VISUAL_QA = "qa/MIT_L04_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L04_INDEPENDENT_REREVIEW.md"
MIT_CSS = "source/id-ID/mit-l02.css"
MIT_PREAMBLE = "source/id-ID/mit-l04-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l03-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l04-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l03-after-body.html"

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


def artifact(record_id: str, kind: str, path: str, rights_id: str | None = None, **extra: Any) -> dict[str, Any]:
    size, digest = file_info(path)
    result = common("artifact", record_id, "current")
    result.update({
        "artifact_kind": kind,
        "path": path,
        "bytes": size,
        "sha256": digest,
        "hash_algorithm": "sha256-raw-bytes",
    })
    if rights_id is not None:
        result["rights_id"] = rights_id
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


def stage_backend(jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    staged: list[Path] = []
    try:
        for destination, data in ((JSONL_PATH, jsonl_bytes), (CSV_PATH, csv_bytes)):
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.mit-l04-", suffix=".stage", dir=BACKEND, delete=False
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


def load_qa_evidence() -> dict[str, Any]:
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    visual = json.loads((ROOT / MIT_VISUAL_QA).read_text(encoding="utf-8"))
    expected_boundary = {
        "source_pdf_pages": [15], "next_source_page": 16, "source_items": 6,
        "nested_bullets": 12, "source_figures": 0, "source_displays": 0,
        "inline_math_surfaces": 1,
    }
    if report.get("result") not in {"pass", "pass_with_limitation"} or report.get("errors") != []:
        raise ValueError("MIT L04 validation report is not passing")
    if report.get("boundary") != expected_boundary:
        raise ValueError("MIT L04 validation boundary differs")
    if browser.get("result") not in {"pass", "pass_with_limitation"} or visual.get("result") != "pass":
        raise ValueError("MIT L04 browser/visual evidence differs")
    for item in report.get("files", {}).values():
        path = item.get("path")
        if path:
            if file_info(path) != (item.get("bytes"), item.get("sha256")):
                raise ValueError(f"MIT L04 report binds stale bytes: {path}")
    return report


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema":
        raise ValueError("backend schema identity differs")
    if file_info(MIT_PDF) != SOURCE_PDF_IDENTITY:
        raise ValueError("MIT authority PDF identity differs")
    load_qa_evidence()

    incoming_jsonl = JSONL_PATH.read_bytes()
    incoming_csv = CSV_PATH.read_bytes()
    incoming_records = [json.loads(line) for line in incoming_jsonl.decode("utf-8").splitlines() if line]
    if len({record["id"] for record in incoming_records}) != len(incoming_records):
        raise ValueError("incoming backend has duplicate IDs")
    records = [record for record in incoming_records if record.get("responsible_workflow") != WORKFLOW]
    already_applied = len(records) != len(incoming_records)
    if not already_applied:
        if (len(incoming_jsonl), sha256(incoming_jsonl)) != BASELINE_JSONL:
            raise ValueError("incoming JSONL is not the protected 1,495-record baseline")
        if (len(incoming_csv), sha256(incoming_csv)) != BASELINE_CSV:
            raise ValueError("incoming CSV is not the protected baseline")
    if (
        len(records) != BASELINE_RECORD_COUNT
        or id_set_sha256(records) != BASELINE_ID_SET_SHA256
        or record_set_sha256(records) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("stripped backend baseline differs from protected byte-for-byte boundary")

    baseline_ids = {record["id"] for record in records}
    new_records: list[dict[str, Any]] = []
    new_ids: set[str] = set()

    def add(record: dict[str, Any]) -> None:
        if record["id"] in baseline_ids or record["id"] in new_ids:
            raise ValueError(f"stable-ID collision: {record['id']}")
        new_ids.add(record["id"])
        new_records.append(record)

    source_start, source_end, source_bytes, source_hash = fenced_div_slice(MIT_WITNESS, "src-mit-l04-p015")
    target_start, target_end, target_bytes, target_hash = fenced_div_slice(MIT_TARGET, "d90-mit-l04-p015")

    unit = common("unit", MIT_L04_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 4,
        "source_local_id": "lecture-1-page-15",
        "source_local_label": "Lecture 1 - The Rise of the Algorithmic Era",
        "target_local_label": "Kuliah 1 - Kebangkitan Era Algoritmik",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": [15],
        "next_source_page": 16,
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 6,
        "nested_source_bullet_count": 12,
        "source_figure_count": 0,
        "source_display_count": 0,
        "inline_math_surface_count": 1,
    })
    add(unit)

    segment = common("segment", MIT_L04_SEGMENT_ID, "visually_checked")
    segment.update({
        "unit_id": MIT_L04_UNIT_ID,
        "order": 1,
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_path": MIT_WITNESS,
        "source_line_start": source_start,
        "source_line_end": source_end,
        "source_bytes": source_bytes,
        "source_content_sha256": source_hash,
        "source_anchor": "src-mit-l04-p015",
        "target_path": MIT_TARGET,
        "target_line_start": target_start,
        "target_line_end": target_end,
        "target_bytes": target_bytes,
        "target_content_sha256": target_hash,
        "target_anchor": "d90-mit-l04-p015",
        "hash_normalization": "sha256-utf8-lf-final-newline",
        "translation_state": "visually_checked",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_pdf_path": MIT_PDF,
        "source_pdf_page": 15,
        "source_pdf_sha256": SOURCE_PDF_IDENTITY[1],
        "source_pdf_pages_total": 340,
        "source_item_count": 6,
        "nested_source_bullet_count": 12,
        "source_figure_count": 0,
        "source_display_count": 0,
        "inline_math_surface_count": 1,
        "anchor_mapping_rule": "replace src-mit- prefix with d90-mit- prefix",
    })
    add(segment)

    surface = common("learning_surface", MIT_INLINE_SURFACE_ID, "present")
    surface.update({
        "unit_id": MIT_L04_UNIT_ID,
        "surface_type": "inline_math",
        "presence": "present",
        "related_segment_ids": [MIT_L04_SEGMENT_ID],
        "source_locator": f"{MIT_WITNESS}#src-mit-l04-p015-i006",
        "target_locator": f"{MIT_TARGET}#d90-mit-l04-p015-i006",
        "notation": "\\ell_1",
        "source_math_nodes": 1,
        "target_math_nodes": 1,
        "math_format": "Pandoc math source; MathML HTML; searchable PDF",
        "accessibility_note": "Italic ell with subscript one is retained as semantic mathematical notation.",
    })
    add(surface)

    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l04.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"source_pdf_pages": [15], "official_editable_source": False, "source_item_count": 6, "nested_source_bullet_count": 12}),
        ("artifact.mit.l04.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": [15], "source_item_count": 6, "nested_source_bullet_count": 12}),
        ("artifact.mit.l04.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "MathML", "source_pages": 1}),
        ("artifact.mit.l04.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": 2, "page_size": "A4", "tagged": False, "searchable": True}),
        ("artifact.mit.l04.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5/MathML and LuaLaTeX"}),
        ("artifact.mit.l04.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l04.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass"}),
        ("artifact.mit.l04.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "live_viewport_measurement": True}),
        ("artifact.mit.l04.visual-qa", "visual_qa_report", MIT_VISUAL_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "pages": 2}),
        ("artifact.mit.l04.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.mit.l04.css", "html_stylesheet", MIT_CSS, "rights.o015-mit-l01-backend-tooling", {"shared_build_dependency": True}),
        ("artifact.mit.l04.pdf-preamble", "pdf_preamble", MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l04.pdf-filter", "pandoc_lua_filter", MIT_FILTER, "rights.o015-mit-l01-backend-tooling", {"shared_build_dependency": True}),
        ("artifact.mit.l04.before-body", "html_include", MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l04.after-body", "html_include", MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling", {"shared_build_dependency": True}),
        ("artifact.o015.backend-generator-mit-l04", "backend_generator", "qa/extend_backend_mit_l04.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library"}),
        ("artifact.o015.backend-validator-mit-l04", "backend_validator", "qa/validate_backend_mit_l04.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library"}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l04.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.complete-notes-pdf", "artifact.mit.l04.semantic-witness"], "authority_pdf_pages": 340, "boundary_pages": [15], "next_source_page": 16}),
        ("qa.o015.mit-l04.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l04.semantic-witness", "artifact.mit.l04.target-source", "artifact.mit.l04.validation"], "official_editable_source": False, "source_items": 6, "nested_source_bullets": 12, "source_figures": 0}),
        ("qa.o015.mit-l04.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l04.validation", "artifact.mit.l04.semantic-witness"], "source_page_map": [[15, 15]], "item_counts": {"15": 6}, "nested_source_bullets": 12, "figures": 0, "source_displays": 0, "inline_math_surfaces": 1}),
        ("qa.o015.mit-l04.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l04.validation", "artifact.mit.l04.independent-rereview"], "source_math_nodes": 1, "target_math_nodes": 1, "display_formulas": 0, "inline_math_surface_ids": [MIT_INLINE_SURFACE_ID]}),
        ("qa.o015.mit-l04.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l04.builder", "artifact.mit.l04.target-html", "artifact.mit.l04.target-pdf", "artifact.mit.l04.validation"], "deterministic_rebuilds": 2, "html_sha256": file_info(MIT_HTML)[1], "pdf_sha256": file_info(MIT_READER_PDF)[1], "toolchain": "Pandoc HTML5/MathML and LuaLaTeX"}),
        ("qa.o015.mit-l04.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l04.target-html", "artifact.mit.l04.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": {"h1": 1, "h2": 3}, "inline_math_nodes": 3, "display_mathml_nodes": 0, "images": 0, "source_pages": 1, "source_items": 6, "source_figures": 0, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l04.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l04.browser-qa", "artifact.mit.l04.target-html"], "desktop_viewport": [1280, 720], "mobile_viewport": [390, 844], "horizontal_overflow": False, "live_measurement": True, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l04.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l04.target-pdf", "artifact.mit.l04.validation"], "pages": 2, "page_size": "A4", "lang": "id-ID", "searchable": True, "fonts_with_tounicode": True, "tagged": False, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l04.visual", "visual", "pass", {"witness_artifact_ids": ["artifact.mit.l04.visual-qa", "artifact.mit.l04.target-pdf"], "pages": 2, "all_pages_visually_inspected": True, "render_tool": "pdftoppm"}),
        ("qa.o015.mit-l04.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l04.target-html", "artifact.mit.l04.target-pdf", "artifact.mit.l04.browser-qa", "artifact.mit.l04.visual-qa"], "primary_surface": "semantic_html", "html_static_structure_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"]}),
        ("qa.o015.mit-l04.math-rereview", "independent_mathematical_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l04.independent-rereview", "artifact.mit.l04.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l04.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded."}),
        ("qa.o015.mit-l04.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l04.semantic-witness"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa"], "source_graphics_in_boundary": 0, "license": "CC BY-NC-SA 4.0", "non_endorsement": True}),
        ("qa.o015.mit-l04.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l04", "artifact.o015.backend-validator-mit-l04", "artifact.o015.source-authority", "artifact.o015.component-rights", "artifact.o015.adverse-ledger"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1]}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        record = common("qa_event", record_id, "passed" if result == "pass" else result)
        record.update({"event_type": event_type, "result": result, "unit_id": MIT_L04_UNIT_ID, **extra})
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l04", "contains", MIT_ROOT_UNIT_ID, MIT_L04_UNIT_ID, "Fourth admitted MIT page boundary in source order."),
        ("relation.mit.witness-edition-contains-l04", "contains", MIT_WITNESS_EDITION_ID, MIT_L04_UNIT_ID, "Page-addressed English semantic witness for complete-notes page 15."),
        ("relation.mit.target-edition-contains-l04", "contains", MIT_TARGET_EDITION_ID, MIT_L04_UNIT_ID, "Built Indonesian semantic derivative for complete-notes page 15."),
        ("relation.mit.l04.contains-p015", "contains", MIT_L04_UNIT_ID, MIT_L04_SEGMENT_ID, "One page-addressed semantic segment."),
        ("relation.mit.witness-adapts-authority-pdf-l04", "adapts", "artifact.mit.l04.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes PDF page 15."),
        ("relation.mit.target-translates-witness-l04", "translates", "artifact.mit.l04.target-source", "artifact.mit.l04.semantic-witness", "One-to-one page/list translation preserving the inline ell-sub-one notation."),
        ("relation.mit.html-adapts-target-l04", "adapts", "artifact.mit.l04.target-html", "artifact.mit.l04.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l04", "adapts", "artifact.mit.l04.target-pdf", "artifact.mit.l04.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.inline-math-depends-on-segment-l04", "depends-on", MIT_INLINE_SURFACE_ID, MIT_L04_SEGMENT_ID, "Inline ell-sub-one math surface is located in the final source item."),
        ("relation.mit.browser-qa-depends-on-html-l04", "depends-on", "artifact.mit.l04.browser-qa", "artifact.mit.l04.target-html", "Static DOM browser QA evidence."),
        ("relation.mit.visual-qa-depends-on-pdf-l04", "depends-on", "artifact.mit.l04.visual-qa", "artifact.mit.l04.target-pdf", "Rendered page visual QA evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l04", "depends-on", "artifact.mit.l04.validation", "artifact.mit.l04.browser-qa", "Validation binds browser evidence."),
        ("relation.mit.validation-depends-on-visual-qa-l04", "depends-on", "artifact.mit.l04.validation", "artifact.mit.l04.visual-qa", "Validation binds rendered visual evidence."),
        ("relation.mit.validation-depends-on-rereview-l04", "depends-on", "artifact.mit.l04.validation", "artifact.mit.l04.independent-rereview", "Validation binds independent rereview."),
    ]
    relation_triples: set[tuple[str, str, str]] = set()
    for record_id, relation_type, source_id, target_id, note in relation_specs:
        triple = (relation_type, source_id, target_id)
        if triple in relation_triples:
            raise ValueError(f"duplicate relation triple: {triple}")
        relation_triples.add(triple)
        record = common("relation", record_id, "current")
        record.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        add(record)

    records.extend(new_records)
    by_id = {record["id"]: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate IDs after L04 extension")
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
    stage_backend(jsonl_bytes, csv_bytes)

    report_out = {
        "already_applied_on_entry": already_applied,
        "protected_baseline": {"record_count": BASELINE_RECORD_COUNT, "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]}, "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]}, "id_set_sha256": BASELINE_ID_SET_SHA256, "record_set_sha256": BASELINE_RECORD_SET_SHA256},
        "new_record_count": len(new_records),
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
        "new_ids": sorted(new_ids),
        "new_ids_sha256": sha256(("\n".join(sorted(new_ids)) + "\n").encode("utf-8")),
        "record_count": len(records),
        "entity_counts": dict(sorted(Counter(record["entity_type"] for record in records).items())),
        "jsonl": {"bytes": len(jsonl_bytes), "sha256": sha256(jsonl_bytes)},
        "csv": {"bytes": len(csv_bytes), "sha256": sha256(csv_bytes)},
        "page_segment_id": MIT_L04_SEGMENT_ID,
        "result": "pass",
    }
    print(json.dumps(report_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
