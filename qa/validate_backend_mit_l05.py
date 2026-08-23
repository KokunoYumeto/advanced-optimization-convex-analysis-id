#!/usr/bin/env python3
"""Fail-closed validation for the MIT L05 modular-backend admission."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
REPORT_PATH = ROOT / "qa/MIT_L05_BACKEND_VALIDATION.json"

RECORDED_AT = "2026-08-23T22:00:00Z"
WORKFLOW = "o015-mit-l05-backend-v1"
BASELINE_COUNT = 1543
BASELINE_JSONL = (1_102_706, "92f6b805a83361f29a830b8c37b1c52f3468cb420d10b9a3a810cf0f8ac20645")
BASELINE_CSV = (1_325_476, "fedc1855df37e006e52ba76d99af2ee132accfa3b416519c39c036454f378a7d")
BASELINE_ID_SET = "7ebf6de13fc7bbe8ae8993f24a01d31e63b9bdc31b9758510f3961a81d103774"
BASELINE_RECORD_SET = "26ef92dc4ac4c1c6dd29396ae5b85795ba67d4d078377aee891abbf337c7c84a"

UNIT_ID = "unit.mit.ocw-6.253.l05"
SOURCE_PAGES = [16, 17, 18, 19]
PAGE_ITEMS = {16: 3, 17: 3, 18: 4, 19: 6}
PAGE_NESTED = {16: 7, 17: 12, 18: 7, 19: 0}
SEGMENT_IDS = {f"d90.mit.ocw-6.253.l05.p{page:03d}" for page in SOURCE_PAGES}
SURFACE_IDS = {
    "surface.mit.l05.external-link-athena",
    "surface.mit.l05.external-link-stanford",
}
CORRECTION_ID = "correction.o015-mit-sem-0004"
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
MIT_BROWSER = "qa/MIT_L05_BROWSER_QA.json"
MIT_VISUAL = "qa/MIT_L05_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L05_INDEPENDENT_REREVIEW.md"
SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")

ARTIFACTS: dict[str, tuple[str, str]] = {
    "artifact.mit.l05.boundary-census": (MIT_CENSUS, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l05.semantic-witness": (MIT_WITNESS, "rights.o015-mit-semantic-witness"),
    "artifact.mit.l05.target-source": (MIT_TARGET, "rights.o015-mit-id-pilot"),
    "artifact.mit.l05.target-html": (MIT_HTML, "rights.o015-mit-id-pilot"),
    "artifact.mit.l05.target-pdf": (MIT_READER_PDF, "rights.o015-mit-id-pilot"),
    "artifact.mit.l05.builder": (MIT_BUILDER, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l05.validator": (MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l05.validation": (MIT_REPORT, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l05.browser-qa": (MIT_BROWSER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l05.visual-qa": (MIT_VISUAL, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l05.independent-rereview": (MIT_REREVIEW, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l05.adverse-ledger-snapshot": (MIT_CORRECTION_SNAPSHOT, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l05.css": (MIT_CSS, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l05.pdf-preamble": (MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l05.pdf-filter": (MIT_FILTER, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l05.before-body": (MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l05.after-body": (MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-generator-mit-l05": ("qa/extend_backend_mit_l05.py", "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-validator-mit-l05": ("qa/validate_backend_mit_l05.py", "rights.o015-mit-l01-backend-tooling"),
}

QA_IDS = {
    f"qa.o015.mit-l05.{name}"
    for name in (
        "source-freeze",
        "semantic-reconstruction",
        "topology",
        "links",
        "correction",
        "formulas",
        "build",
        "html",
        "browser",
        "pdf",
        "visual",
        "accessibility",
        "semantic-rereview",
        "language",
        "rights",
        "backend-integration",
    )
}

RELATION_IDS = {
    "relation.mit.work-contains-l05",
    "relation.mit.witness-edition-contains-l05",
    "relation.mit.target-edition-contains-l05",
    "relation.mit.witness-adapts-authority-pdf-l05",
    "relation.mit.target-translates-witness-l05",
    "relation.mit.html-adapts-target-l05",
    "relation.mit.pdf-adapts-target-l05",
    "relation.mit.external-link-athena-depends-on-p017-l05",
    "relation.mit.external-link-stanford-depends-on-p017-l05",
    "relation.mit.browser-qa-depends-on-html-l05",
    "relation.mit.visual-qa-depends-on-pdf-l05",
    "relation.mit.validation-depends-on-browser-qa-l05",
    "relation.mit.validation-depends-on-visual-qa-l05",
    "relation.mit.validation-depends-on-rereview-l05",
    "relation.mit.validation-depends-on-boundary-l05",
    "relation.mit.l05.contains-p016",
    "relation.mit.l05.contains-p017",
    "relation.mit.l05.contains-p018",
    "relation.mit.l05.contains-p019",
}

EXPECTED_NEW_IDS = {UNIT_ID, CORRECTION_ID} | SEGMENT_IDS | SURFACE_IDS | set(ARTIFACTS) | QA_IDS | RELATION_IDS
EXPECTED_NEW_ENTITY_COUNTS = {
    "artifact": 19,
    "correction": 1,
    "learning_surface": 2,
    "qa_event": 16,
    "relation": 19,
    "segment": 4,
    "unit": 1,
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), digest(data)


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def id_set(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def record_set(records: list[dict[str, Any]]) -> str:
    payload = "".join(canonical(record) + "\n" for record in sorted(records, key=lambda item: item["id"]))
    return digest(payload.encode("utf-8"))


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.strip().startswith("::: {") and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
    ]
    if len(starts) != 1:
        raise ValueError(f"{relative} #{anchor}: expected one fenced div, found {len(starts)}")
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
        raise ValueError(f"{relative} #{anchor}: unclosed fenced div")
    payload = ("\n".join(lines[start : end + 1]) + "\n").encode("utf-8")
    return start + 1, end + 1, len(payload), digest(payload)


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
        if json.loads(row[4]).get("responsible_workflow") != WORKFLOW:
            kept.append(line)
    return b"".join(kept)


def ledger_event() -> tuple[dict[str, Any], str]:
    matches = []
    for line in (ROOT / MIT_CORRECTION_SNAPSHOT).read_text(encoding="utf-8").splitlines():
        if line:
            event = json.loads(line)
            if event.get("event_id") == "O015-MIT-SEM-0004":
                matches.append(event)
    if len(matches) != 1:
        raise ValueError(f"expected one O015-MIT-SEM-0004 event, found {len(matches)}")
    event = matches[0]
    live_matches = []
    for line in (ROOT / MIT_LEDGER).read_text(encoding="utf-8").splitlines():
        if line:
            live_event = json.loads(line)
            if live_event.get("event_id") == "O015-MIT-SEM-0004":
                live_matches.append(live_event)
    if live_matches != [event]:
        raise ValueError("live O015-MIT-SEM-0004 event differs from its immutable snapshot")
    return event, digest(canonical(event).encode("utf-8"))


def main() -> int:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        raw_jsonl = JSONL_PATH.read_bytes()
        raw_csv = CSV_PATH.read_bytes()
        records = [json.loads(line) for line in raw_jsonl.decode("utf-8").splitlines() if line]
    except Exception as exc:
        errors.append(f"backend load failed: {exc}")
        schema, raw_jsonl, raw_csv, records = {}, b"", b"", []

    ids = [record.get("id") for record in records]
    by_id = {record.get("id"): record for record in records}
    new_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    baseline_records = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    check(schema.get("schema") == "o015-modular-backend-schema", "backend schema identity differs")
    check(len(EXPECTED_NEW_IDS) == 62, "validator expected-ID declaration is not 62 records")
    check(len(records) == BASELINE_COUNT + len(EXPECTED_NEW_IDS), f"record count {len(records)} differs")
    check(len(ids) == len(set(ids)), "duplicate backend IDs")
    check(len(new_records) == len(EXPECTED_NEW_IDS), "L05 new-record count differs")
    check({record["id"] for record in new_records} == EXPECTED_NEW_IDS, "L05 stable-ID set differs")
    check(
        dict(sorted(Counter(record.get("entity_type") for record in new_records).items())) == EXPECTED_NEW_ENTITY_COUNTS,
        "L05 new-entity counts differ",
    )
    check(len(baseline_records) == BASELINE_COUNT, "protected baseline record count differs")
    check(id_set(baseline_records) == BASELINE_ID_SET, "protected baseline ID-set hash differs")
    check(record_set(baseline_records) == BASELINE_RECORD_SET, "protected baseline record-set hash differs")

    stripped_jsonl = b""
    stripped_csv = b""
    try:
        stripped_jsonl = strip_workflow_jsonl(raw_jsonl)
        stripped_csv = strip_workflow_csv(raw_csv)
        check((len(stripped_jsonl), digest(stripped_jsonl)) == BASELINE_JSONL, "raw JSONL baseline reconstruction differs")
        check((len(stripped_csv), digest(stripped_csv)) == BASELINE_CSV, "raw CSV baseline reconstruction differs")
    except Exception as exc:
        errors.append(f"raw baseline reconstruction failed: {exc}")

    rank = {name: index for index, name in enumerate(schema.get("entity_order", []))}
    check(
        records == sorted(records, key=lambda record: (rank.get(record.get("entity_type"), 999), record.get("id", ""))),
        "JSONL order is not deterministic",
    )
    try:
        rows = list(csv.DictReader(io.StringIO(raw_csv.decode("utf-8", errors="strict"))))
        check([json.loads(row["record_json"]) for row in rows] == records, "CSV projection does not round-trip")
        check(list(rows[0]) == schema.get("csv_columns"), "CSV header differs from schema")
    except Exception as exc:
        errors.append(f"CSV parse failed: {exc}")

    refs = set(schema.get("reference_fields", []))
    for record in records:
        entity_type = record.get("entity_type")
        for field in schema.get("required_common", []) + schema.get("required_by_entity", {}).get(entity_type, []):
            check(field in record, f"{record.get('id')}: missing required {field}")
        for field in refs:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for target in values:
                if isinstance(target, str):
                    check(target in by_id, f"{record.get('id')}: unresolved {field} -> {target}")

    unit = by_id.get(UNIT_ID, {})
    expected_source_items = [
        f"src-mit-l05-p{page:03d}-i{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)
    ]
    expected_target_items = [item.replace("src-mit-", "d90-mit-", 1) for item in expected_source_items]
    check(unit.get("order") == 5 and unit.get("source_pdf_pages") == SOURCE_PAGES, "L05 unit order/page boundary differs")
    check(unit.get("parent_id") == "unit.mit.ocw-6.253.spring-2012", "L05 parent differs")
    check(unit.get("next_source_page") == 20 and unit.get("next_source_heading") == "LECTURE 2", "L05 next cursor differs")
    check(unit.get("source_item_count") == 16 and unit.get("nested_source_bullet_count") == 26, "L05 unit topology counts differ")
    check(unit.get("source_item_ids") == expected_source_items, "L05 unit source-item IDs differ")
    check(unit.get("target_item_ids") == expected_target_items, "L05 unit target-item IDs differ")
    check(unit.get("active_uri_count") == 2 and unit.get("correction_event_ids") == ["O015-MIT-SEM-0004"], "L05 URI/correction summary differs")
    check(
        unit.get("source_figure_count") == 0
        and unit.get("source_display_count") == 0
        and unit.get("inline_math_surface_count") == 0,
        "L05 absent-surface topology differs",
    )

    for order, page in enumerate(SOURCE_PAGES, start=1):
        segment_id = f"d90.mit.ocw-6.253.l05.p{page:03d}"
        segment = by_id.get(segment_id, {})
        source_anchor = f"src-mit-l05-p{page:03d}"
        target_anchor = f"d90-mit-l05-p{page:03d}"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
            target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
            check(
                (
                    segment.get("source_line_start"),
                    segment.get("source_line_end"),
                    segment.get("source_bytes"),
                    segment.get("source_content_sha256"),
                ) == source_slice,
                f"{segment_id}: source page-slice binding differs",
            )
            check(
                (
                    segment.get("target_line_start"),
                    segment.get("target_line_end"),
                    segment.get("target_bytes"),
                    segment.get("target_content_sha256"),
                ) == target_slice,
                f"{segment_id}: target page-slice binding differs",
            )
        except Exception as exc:
            errors.append(f"{segment_id}: page-slice check failed: {exc}")
        source_items = [f"{source_anchor}-i{index:03d}" for index in range(1, PAGE_ITEMS[page] + 1)]
        target_items = [f"{target_anchor}-i{index:03d}" for index in range(1, PAGE_ITEMS[page] + 1)]
        check(segment.get("unit_id") == UNIT_ID and segment.get("order") == order, f"{segment_id}: order/unit differs")
        check(segment.get("source_pdf_page") == page, f"{segment_id}: source PDF page differs")
        check(segment.get("source_pdf_sha256") == SOURCE_PDF_IDENTITY[1], f"{segment_id}: authority hash differs")
        check(segment.get("source_item_ids") == source_items and segment.get("target_item_ids") == target_items, f"{segment_id}: item anchors differ")
        check(segment.get("source_item_count") == PAGE_ITEMS[page], f"{segment_id}: top-level count differs")
        check(segment.get("nested_source_bullet_count") == PAGE_NESTED[page], f"{segment_id}: nested count differs")
        expected_uris = SOURCE_URIS if page == 17 else []
        check(segment.get("source_uris") == expected_uris and segment.get("source_uri_count") == len(expected_uris), f"{segment_id}: URI closure differs")

    link_expectations = {
        "surface.mit.l05.external-link-athena": (SOURCE_URIS[0], "i001"),
        "surface.mit.l05.external-link-stanford": (SOURCE_URIS[1], "i002"),
    }
    for surface_id, (uri, item_suffix) in link_expectations.items():
        surface = by_id.get(surface_id, {})
        check(surface.get("unit_id") == UNIT_ID, f"{surface_id}: unit differs")
        check(surface.get("surface_type") == "external_link" and surface.get("presence") == "present", f"{surface_id}: surface semantics differ")
        check(surface.get("uri") == uri, f"{surface_id}: URI differs")
        check(surface.get("related_segment_ids") == ["d90.mit.ocw-6.253.l05.p017"], f"{surface_id}: page relation differs")
        check(surface.get("source_locator", "").endswith(f"p017-{item_suffix}"), f"{surface_id}: source locator differs")
        check(surface.get("target_locator", "").endswith(f"p017-{item_suffix}"), f"{surface_id}: target locator differs")

    try:
        event, event_hash = ledger_event()
        correction = by_id.get(CORRECTION_ID, {})
        check(event.get("authority") == "o015-mit-ocw-6.253-spring-2012", "correction authority differs")
        check(event.get("class") == "determined_name_correction", "correction class in ledger differs")
        check(correction.get("source_event_id") == "O015-MIT-SEM-0004", "correction event ID differs")
        check(correction.get("affected_unit_ids") == [UNIT_ID], "correction unit binding differs")
        check(correction.get("affected_segment_ids") == ["d90.mit.ocw-6.253.l05.p017"], "correction segment binding differs")
        check(correction.get("source_issue") == event.get("source_issue"), "correction source issue differs from ledger")
        check(correction.get("target_action") == event.get("target_action"), "correction target action differs from ledger")
        check(correction.get("correction_class") == event.get("class"), "correction class differs from ledger")
        check(correction.get("source_event_record_sha256") == event_hash, "correction event hash differs")
        check(correction.get("evidence_artifact_id") == "artifact.mit.l05.adverse-ledger-snapshot", "correction snapshot evidence differs")
        check(correction.get("target_locator", "").endswith("#d90-mit-l05-p017-i002"), "correction target locator differs")
    except Exception as exc:
        errors.append(f"correction evidence check failed: {exc}")

    try:
        check(file_info(MIT_PDF) == SOURCE_PDF_IDENTITY, "authority PDF identity differs")
    except Exception as exc:
        errors.append(f"authority PDF check failed: {exc}")
    for artifact_id, (path, rights_id) in ARTIFACTS.items():
        artifact = by_id.get(artifact_id)
        check(artifact is not None, f"missing artifact {artifact_id}")
        if artifact is None:
            continue
        try:
            check(file_info(path) == (artifact.get("bytes"), artifact.get("sha256")), f"{artifact_id}: stale artifact bytes")
        except Exception as exc:
            errors.append(f"{artifact_id}: artifact check failed: {exc}")
        check(artifact.get("path") == path, f"{artifact_id}: path differs")
        check(artifact.get("rights_id") == rights_id, f"{artifact_id}: rights binding differs")

    rights_ids = {
        "rights.o015-mit-semantic-witness",
        "rights.o015-mit-id-pilot",
        "rights.o015-mit-pilot-build-qa",
        "rights.o015-mit-l01-backend-tooling",
    }
    for rights_id in rights_ids:
        check(by_id.get(rights_id, {}).get("entity_type") == "rights", f"missing rights record {rights_id}")
    check(by_id.get("rights.o015-mit-id-pilot", {}).get("rights_expression") == "CC BY-NC-SA 4.0 derivative", "MIT target rights expression differs")
    check(by_id.get("qa.o015.mit-l05.rights", {}).get("license") == "CC BY-NC-SA 4.0", "L05 rights QA license differs")
    check(by_id.get("qa.o015.mit-l05.rights", {}).get("change_event_ids") == ["O015-MIT-SEM-0004"], "L05 rights change marking differs")

    new_relations = [record for record in new_records if record.get("entity_type") == "relation"]
    relation_triples = [(record.get("relation_type"), record.get("source_id"), record.get("target_id")) for record in new_relations]
    check(len(relation_triples) == len(set(relation_triples)), "duplicate L05 relation triple")
    for page in SOURCE_PAGES:
        relation = by_id.get(f"relation.mit.l05.contains-p{page:03d}", {})
        check(
            (relation.get("relation_type"), relation.get("source_id"), relation.get("target_id"))
            == ("contains", UNIT_ID, f"d90.mit.ocw-6.253.l05.p{page:03d}"),
            f"page {page} containment relation differs",
        )
    check(
        by_id.get("relation.mit.target-translates-witness-l05", {}).get("target_id") == "artifact.mit.l05.semantic-witness",
        "target/witness translation relation differs",
    )

    try:
        content = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
        browser = json.loads((ROOT / MIT_BROWSER).read_text(encoding="utf-8"))
        visual = json.loads((ROOT / MIT_VISUAL).read_text(encoding="utf-8"))
        expected_boundary = {
            "source_pdf_pages": SOURCE_PAGES,
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
        check(content.get("result") == "pass" and content.get("errors") == [], "MIT L05 content validation is not passing")
        check(content.get("boundary") == expected_boundary, "MIT L05 content boundary differs")
        check(content.get("build", {}).get("deterministic_rebuilds") == 2, "L05 deterministic build count differs")
        check(content.get("html", {}).get("source_items") == 16 and content.get("html", {}).get("math") == 0, "L05 HTML topology differs")
        check(content.get("pdf", {}).get("pages") == 3 and content.get("pdf", {}).get("tagged") is False, "L05 PDF topology differs")
        check(browser.get("result") == "pass" and browser.get("html", {}).get("sha256") == file_info(MIT_HTML)[1], "browser QA evidence differs")
        check(visual.get("result") == "pass" and visual.get("surface", {}).get("sha256") == file_info(MIT_READER_PDF)[1], "visual QA evidence differs")
    except Exception as exc:
        errors.append(f"QA receipt load failed: {exc}")

    canonical_paths = {
        "authority_pdf": MIT_PDF,
        "witness": MIT_WITNESS,
        "target": MIT_TARGET,
        "html": MIT_HTML,
        "pdf": MIT_READER_PDF,
        "css": MIT_CSS,
        "builder": MIT_BUILDER,
        "content_validator": MIT_VALIDATOR,
        "content_validation": MIT_REPORT,
        "browser_qa": MIT_BROWSER,
        "visual_qa": MIT_VISUAL,
        "independent_rereview": MIT_REREVIEW,
        "ledger_snapshot": MIT_CORRECTION_SNAPSHOT,
        "backend_generator": "qa/extend_backend_mit_l05.py",
        "backend_validator": "qa/validate_backend_mit_l05.py",
    }
    identities: dict[str, Any] = {}
    for name, path in canonical_paths.items():
        try:
            size, file_hash = file_info(path)
            identities[name] = {"path": path, "bytes": size, "sha256": file_hash}
        except Exception as exc:
            identities[name] = {"path": path, "error": str(exc)}

    new_counts = dict(sorted(Counter(record.get("entity_type") for record in new_records).items()))
    receipt = {
        "schema": "o015-mit-l05-backend-validation-v1",
        "recorded_at": RECORDED_AT,
        "workflow": WORKFLOW,
        "protected_baseline": {
            "record_count": BASELINE_COUNT,
            "jsonl": {"bytes": len(stripped_jsonl), "sha256": digest(stripped_jsonl) if stripped_jsonl else None, "expected": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]}},
            "csv": {"bytes": len(stripped_csv), "sha256": digest(stripped_csv) if stripped_csv else None, "expected": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]}},
            "id_set_sha256": id_set(baseline_records) if baseline_records else None,
            "record_set_sha256": record_set(baseline_records) if baseline_records else None,
            "preserved_record_count": len(baseline_records),
            "raw_bytes_reconstructed_exactly": (len(stripped_jsonl), digest(stripped_jsonl) if stripped_jsonl else None) == BASELINE_JSONL and (len(stripped_csv), digest(stripped_csv) if stripped_csv else None) == BASELINE_CSV,
        },
        "admission": {
            "unit_id": UNIT_ID,
            "segment_ids": sorted(SEGMENT_IDS),
            "top_level_items": 16,
            "nested_bullets": 26,
            "external_uris": SOURCE_URIS,
            "correction_id": CORRECTION_ID,
            "new_record_count": len(new_records),
            "new_entity_counts": new_counts,
            "new_ids_sha256": digest(("\n".join(sorted(EXPECTED_NEW_IDS)) + "\n").encode("utf-8")),
        },
        "backend": {
            "record_count": len(records),
            "jsonl": {"bytes": len(raw_jsonl), "sha256": digest(raw_jsonl)},
            "csv": {"bytes": len(raw_csv), "sha256": digest(raw_csv)},
        },
        "canonical_identities": identities,
        "limitations": [
            "PDF is searchable but untagged.",
            "Independent human/native-speaker Indonesian review is not recorded.",
        ],
        "errors": errors,
        "result": "pass" if not errors else "fail",
    }
    REPORT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
