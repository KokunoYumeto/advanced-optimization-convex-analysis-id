#!/usr/bin/env python3
"""Independent fail-closed validation of the MIT L08 backend admission."""

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
RECEIPT_PATH = ROOT / "qa/MIT_L08_BACKEND_VALIDATION.json"

RECORDED_AT = "2026-08-24T03:00:00Z"
WORKFLOW = "o015-mit-l08-backend-v1"
UNIT_ID = "unit.mit.ocw-6.253.l08"
SOURCE_PAGES = list(range(39, 50))
BASELINE_COUNT = 1820
BASELINE_JSONL = (1_321_559, "1f6384b25937765bdd32e9ae59d68ac11772c15ddd250861d7d051742ad43843")
BASELINE_CSV = (1_586_211, "a6986c21e9757dd1750dd5e515e9038a973ecbeeae22db07d99ff81ea3f92985")
BASELINE_ID_SET_SHA256 = "18e876349873e4e0579cf45c539392e798486dbcb8e4be8a6ebfe1d912f873c6"
BASELINE_RECORD_SET_SHA256 = "5dbe23efc914bb90e6949470cf20b9be5981df4345576a1c3846fdb765012091"

PAGE_ITEMS = {39: 4, 40: 5, 41: 1, 42: 2, 43: 4, 44: 1, 45: 1, 46: 2, 47: 1, 48: 2, 49: 4}
PAGE_NESTED = {39: 0, 40: 0, 41: 2, 42: 0, 43: 3, 44: 5, 45: 2, 46: 2, 47: 0, 48: 0, 49: 2}
PAGE_DISPLAYS = {39: 0, 40: 0, 41: 1, 42: 1, 43: 0, 44: 1, 45: 1, 46: 7, 47: 6, 48: 4, 49: 5}
FIGURE_PANELS = {40: 1, 41: 1, 42: 1, 44: 1, 48: 1}
SOURCE_TEXT_FINGERPRINTS = {
    39: "7eea461ea346ad1d4f43be4350ca2597d2efe0270b41967307600a521de03b05",
    40: "85ff891678a524893f8cbacc5bf4cdd6d4540883d8d125ce415778b5d621dba5",
    41: "0ea583c7109ed83a96c11d143aed939d5c18a07d5bdb74c537e22db1c3aa2939",
    42: "7120ed092593e2c64d5c8e52176ad37c646273e9c36a652a250d3710812d7c1c",
    43: "b71f771dd0b2736dc5d00bd36335bd9abcf2d1eccd5eb79df851804d2ac6fd75",
    44: "82c443c774d394a23127c0d66fd829f7f99a83e622e97a7b8e255db03c0d2d48",
    45: "c09764878d0d0d4f40ed91d6e5e5e32ddf432fc8e1fb84a5181f3aba365e1d47",
    46: "fd2317415e96c5b3cc51f944443b79f9a641725636fb482cbca3aa88e6d7f22c",
    47: "7f2b12088c43f11512cf5a5a8fe52beebc3c7b3a12051c5508fb8a25119eee34",
    48: "6c8b085e04ccf58dae618b1ec85941d2db0dac71061cb02a9280cefc4e19c186",
    49: "7b72fddf12936390ab46902418129de1fade11640cb7d65662277608b2f9d30a",
    50: "595b3d566a6d820573632a5dc853afb2c0cf8474fab8693a57d84ff33335ae63",
}

MIT_PDF = "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
MIT_CENSUS = "00_control/MIT_L08_LECTURE_4_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/MIT_L08_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.md"
MIT_HTML = "output/html/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.pdf"
MIT_CSS = "source/id-ID/mit-l08.css"
MIT_PREAMBLE = "source/id-ID/mit-l08-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l08-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l08-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l08-after-body.html"
MIT_BUILDER = "qa/build_mit_l08.py"
MIT_VALIDATOR = "qa/validate_mit_l08.py"
MIT_REPORT = "qa/MIT_L08_VALIDATION.json"
MIT_BROWSER = "qa/MIT_L08_BROWSER_QA.json"
MIT_VISUAL = "qa/MIT_L08_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L08_INDEPENDENT_REREVIEW.md"
MIT_BACKEND_GENERATOR = "qa/extend_backend_mit_l08.py"
MIT_BACKEND_VALIDATOR = "qa/validate_backend_mit_l08.py"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
LEDGER_IDENTITY = (2_347, "d99f8df4e722a9c98368bb169df17aa41d21754766b9ee19747a52569b40cb17")
RECEIPT_BUILD_COMMAND = "python qa/build_mit_l08.py --html-output <html> --pdf-output <pdf>"
CANONICAL_BUILD_COMMAND = (
    "python qa/build_mit_l08.py --html-output "
    "output/html/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.html "
    "--pdf-output output/pdf/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.pdf"
)

EXPECTED_EVENTS = {
    "O015-MIT-SEM-0009": {
        "event_id": "O015-MIT-SEM-0009",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF pages 42, 48, and 49; source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md",
        "surface": "Function-type arrows in Lecture 4",
        "source_issue": "Three declarations use the element-mapping arrow in expressions that state only a function's domain and codomain, repeating the determined notation issue in earlier lectures.",
        "target_action": "Preserved the printed mapsto arrows in the English semantic witness, normalized them to right arrows in the learner-facing Indonesian type declarations, and disclosed the correction in the edition notice.",
        "class": "determined_notation_correction",
    },
    "O015-MIT-SEM-0010": {
        "event_id": "O015-MIT-SEM-0010",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF page 43; source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md",
        "surface": "Commutation of relative interior and closure with linear inverse images",
        "source_issue": "The summary states the inverse-image commutation rules without the required feasibility qualification; in general both can fail when the linear map's range misses the relative interior of the target convex set.",
        "target_action": "Retained the source claim in the English witness, but qualified the learner-facing rule by A inverse of ri C nonempty, equivalently range A intersect ri C nonempty, and disclosed the scope correction in the edition notice.",
        "class": "determined_missing_hypothesis_correction",
    },
    "O015-MIT-SEM-0011": {
        "event_id": "O015-MIT-SEM-0011",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF page 45; source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md",
        "surface": "Geometric intuition for a linear image of a relative ball",
        "source_issue": "The proof intuition says a general linear map sends spheres within C onto spheres within A C, but nonsimilarity linear maps produce ellipsoids or degenerate images rather than spheres.",
        "target_action": "Preserved the printed intuition in the English witness and replaced it in the learner-facing edition with the correct relative-neighborhood statement: the image of a relative neighborhood is a relative neighborhood in the image affine hull and contains an appropriate relative ball.",
        "class": "determined_geometric_intuition_correction",
    },
}

ARTIFACTS = {
    "artifact.mit.l08.boundary-census": (MIT_CENSUS, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l08.semantic-witness": (MIT_WITNESS, "rights.o015-mit-semantic-witness"),
    "artifact.mit.l08.target-source": (MIT_TARGET, "rights.o015-mit-id-pilot"),
    "artifact.mit.l08.target-html": (MIT_HTML, "rights.o015-mit-id-pilot"),
    "artifact.mit.l08.target-pdf": (MIT_READER_PDF, "rights.o015-mit-id-pilot"),
    "artifact.mit.l08.builder": (MIT_BUILDER, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l08.validator": (MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l08.validation": (MIT_REPORT, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l08.browser-qa": (MIT_BROWSER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l08.visual-qa": (MIT_VISUAL, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l08.independent-rereview": (MIT_REREVIEW, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l08.correction-snapshot": (MIT_LEDGER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l08.css": (MIT_CSS, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l08.pdf-preamble": (MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l08.pdf-filter": (MIT_FILTER, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l08.before-body": (MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l08.after-body": (MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-generator-mit-l08": (MIT_BACKEND_GENERATOR, "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-validator-mit-l08": (MIT_BACKEND_VALIDATOR, "rights.o015-mit-l01-backend-tooling"),
}
QA_IDS = {
    "qa.o015.mit-l08.source-freeze",
    "qa.o015.mit-l08.semantic-reconstruction",
    "qa.o015.mit-l08.topology",
    "qa.o015.mit-l08.formulas",
    "qa.o015.mit-l08.figures",
    "qa.o015.mit-l08.corrections",
    "qa.o015.mit-l08.build",
    "qa.o015.mit-l08.html",
    "qa.o015.mit-l08.browser",
    "qa.o015.mit-l08.pdf",
    "qa.o015.mit-l08.visual",
    "qa.o015.mit-l08.semantic-rereview",
    "qa.o015.mit-l08.accessibility",
    "qa.o015.mit-l08.language",
    "qa.o015.mit-l08.rights",
    "qa.o015.mit-l08.csv-losslessness",
    "qa.o015.mit-l08.backend-integration",
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
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("::: {"):
            depth += 1
        elif stripped == ":::":
            depth -= 1
            if depth == 0:
                payload = ("\n".join(lines[start:index + 1]) + "\n").encode("utf-8")
                return start + 1, index + 1, len(payload), digest(payload)
    raise ValueError(f"{relative} #{anchor}: unclosed fenced div")


def strip_workflow_jsonl(raw: bytes) -> bytes:
    return b"".join(
        line for line in raw.splitlines(keepends=True)
        if json.loads(line.decode("utf-8")).get("responsible_workflow") != WORKFLOW
    )


def strip_workflow_csv(raw: bytes) -> bytes:
    lines = raw.splitlines(keepends=True)
    kept = [lines[0]]
    for line in lines[1:]:
        row = next(csv.reader(io.StringIO(line.decode("utf-8"))))
        if len(row) != 5:
            raise ValueError("backend CSV row width differs")
        if json.loads(row[4]).get("responsible_workflow") != WORKFLOW:
            kept.append(line)
    return b"".join(kept)


def ledger_events() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if file_info(MIT_LEDGER) != LEDGER_IDENTITY:
        raise ValueError("L08 correction snapshot identity differs")
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), 1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id not in EXPECTED_EVENTS or event_id in result or event != EXPECTED_EVENTS[event_id]:
            raise ValueError(f"unexpected, duplicate, or changed correction event: {event_id}")
        newline = "crlf" if raw_line.endswith(b"\r\n") else "lf" if raw_line.endswith(b"\n") else "none"
        result[event_id] = (event, {
            "ledger_path": MIT_LEDGER,
            "raw_line_start": line_number,
            "raw_line_end": line_number,
            "raw_line_bytes": len(raw_line),
            "raw_line_sha256": digest(raw_line),
            "raw_line_newline": newline,
            "canonical_event_sha256": digest(canonical(event).encode("utf-8")),
        })
    if set(result) != set(EXPECTED_EVENTS):
        raise ValueError("correction event set differs")
    return result


def expected_ids() -> set[str]:
    ids = {UNIT_ID}
    ids.update(f"d90.mit.ocw-6.253.l08.p{page:03d}" for page in SOURCE_PAGES)
    ids.update(f"surface.mit.l08.formula.p{page:03d}.d{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1))
    ids.update(f"surface.mit.l08.figure-description.p{page:03d}.f001" for page in FIGURE_PANELS)
    ids.update(f"correction.o015-mit-sem-{number:04d}" for number in range(9, 12))
    ids.update(ARTIFACTS)
    ids.update(QA_IDS)
    ids.update({
        "relation.mit.work-contains-l08",
        "relation.mit.witness-edition-contains-l08",
        "relation.mit.target-edition-contains-l08",
        "relation.mit.l07-precedes-l08",
        "relation.mit.witness-adapts-authority-pdf-l08",
        "relation.mit.target-translates-witness-l08",
        "relation.mit.html-adapts-target-l08",
        "relation.mit.pdf-adapts-target-l08",
        "relation.mit.browser-qa-depends-on-html-l08",
        "relation.mit.visual-qa-depends-on-pdf-l08",
        "relation.mit.validation-depends-on-browser-qa-l08",
        "relation.mit.validation-depends-on-visual-qa-l08",
        "relation.mit.rereview-depends-on-target-l08",
    })
    ids.update(f"relation.mit.l08-contains-p{page:03d}" for page in SOURCE_PAGES)
    ids.update(f"relation.mit.l08-formula-p{page:03d}-d{index:03d}-illustrates-segment" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1))
    ids.update(f"relation.mit.l08-figure-p{page:03d}-illustrates-segment" for page in FIGURE_PANELS)
    return ids


def main() -> int:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonl_raw = JSONL_PATH.read_bytes()
    csv_raw = CSV_PATH.read_bytes()
    records = [json.loads(line) for line in jsonl_raw.decode("utf-8", errors="strict").splitlines() if line]
    rows = list(csv.DictReader(io.StringIO(csv_raw.decode("utf-8", errors="strict"))))
    row_records = [json.loads(row["record_json"]) for row in rows]
    check(schema.get("schema") == "o015-modular-backend-schema", "backend schema identity differs")
    check(row_records == records, "CSV record_json projection differs from JSONL")
    check(len(records) == 1957, f"final record count differs: {len(records)}")
    check(len({record.get("id") for record in records}) == len(records), "duplicate stable IDs")
    entity_rank = {name: index for index, name in enumerate(schema.get("entity_order", []))}
    check(records == sorted(records, key=lambda record: (entity_rank[record["entity_type"]], record["id"])), "backend record order differs")

    workflow_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    baseline_records = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    expected = expected_ids()
    check({record["id"] for record in workflow_records} == expected, "L08 workflow stable-ID set differs")
    check(len(workflow_records) == 137, f"L08 workflow record count differs: {len(workflow_records)}")
    check(
        Counter(record["entity_type"] for record in workflow_records)
        == Counter({"unit": 1, "segment": 11, "learning_surface": 31, "correction": 3, "artifact": 19, "qa_event": 17, "relation": 55}),
        "L08 entity-type counts differ",
    )
    check(all(record.get("recorded_at") == RECORDED_AT for record in workflow_records), "L08 recorded_at values differ")
    check(len(baseline_records) == BASELINE_COUNT, "protected baseline record count differs")
    check(id_set(baseline_records) == BASELINE_ID_SET_SHA256, "protected baseline ID-set hash differs")
    check(record_set(baseline_records) == BASELINE_RECORD_SET_SHA256, "protected baseline record-set hash differs")
    check((len(strip_workflow_jsonl(jsonl_raw)), digest(strip_workflow_jsonl(jsonl_raw))) == BASELINE_JSONL, "raw JSONL baseline reconstruction differs")
    check((len(strip_workflow_csv(csv_raw)), digest(strip_workflow_csv(csv_raw))) == BASELINE_CSV, "raw CSV baseline reconstruction differs")

    by_id = {record["id"]: record for record in records}
    id_pattern = re.compile(schema["id_pattern"])
    for record in records:
        check(record.get("schema") == "o015-modular-backend-record", f"{record.get('id')}: record schema differs")
        check(record.get("schema_version") == "1.0.0", f"{record.get('id')}: schema version differs")
        check(bool(id_pattern.fullmatch(record["id"])), f"{record.get('id')}: invalid ID")
        for field in schema.get("required_common", []):
            check(field in record, f"{record.get('id')}: missing common field {field}")
        for field in schema.get("required_by_entity", {}).get(record["entity_type"], []):
            check(field in record, f"{record.get('id')}: missing required field {field}")
        for field in schema.get("reference_fields", []):
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                check(value in by_id, f"{record['id']}: dangling {field} {value}")

    unit = by_id.get(UNIT_ID, {})
    check(unit.get("entity_type") == "unit" and unit.get("order") == 8, "L08 unit identity/order differs")
    check(unit.get("source_pdf_pages") == SOURCE_PAGES and unit.get("next_source_page") == 50, "L08 unit boundary differs")
    check(
        (
            unit.get("source_item_count"),
            unit.get("nested_source_item_count"),
            unit.get("source_display_count"),
            unit.get("source_figure_count"),
            unit.get("source_figure_panel_count"),
            unit.get("copied_source_graphics"),
        ) == (27, 16, 26, 5, 5, 0),
        "L08 unit topology differs",
    )
    check(unit.get("correction_event_ids") == sorted(EXPECTED_EVENTS), "L08 unit correction IDs differ")
    check(unit.get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "L08 unit build command differs")

    for order, page in enumerate(SOURCE_PAGES, 1):
        segment_id = f"d90.mit.ocw-6.253.l08.p{page:03d}"
        segment = by_id.get(segment_id, {})
        anchor = f"d90-mit-l08-p{page:03d}"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, anchor)
            target_slice = fenced_div_slice(MIT_TARGET, anchor)
        except Exception as exc:
            errors.append(str(exc))
            continue
        check(segment.get("order") == order and segment.get("source_pdf_page") == page, f"{segment_id}: page/order differs")
        check(segment.get("source_anchor") == anchor and segment.get("target_anchor") == anchor, f"{segment_id}: anchors differ")
        check((segment.get("source_line_start"), segment.get("source_line_end"), segment.get("source_bytes"), segment.get("source_content_sha256")) == source_slice, f"{segment_id}: witness slice differs")
        check((segment.get("target_line_start"), segment.get("target_line_end"), segment.get("target_bytes"), segment.get("target_content_sha256")) == target_slice, f"{segment_id}: target slice differs")
        check((segment.get("source_item_count"), segment.get("nested_source_item_count"), segment.get("source_display_count")) == (PAGE_ITEMS[page], PAGE_NESTED[page], PAGE_DISPLAYS[page]), f"{segment_id}: topology differs")
        check((segment.get("source_figure_count"), segment.get("source_figure_panel_count")) == (1 if page in FIGURE_PANELS else 0, FIGURE_PANELS.get(page, 0)), f"{segment_id}: figure topology differs")
        check(segment.get("source_page_text_sha256") == SOURCE_TEXT_FINGERPRINTS[page], f"{segment_id}: source text fingerprint differs")

    formula_records = [record for record in workflow_records if record.get("entity_type") == "learning_surface" and record.get("surface_type") == "display_formula"]
    check(len(formula_records) == 26, "formula surface count differs")
    for page in SOURCE_PAGES:
        for index in range(1, PAGE_DISPLAYS[page] + 1):
            record_id = f"surface.mit.l08.formula.p{page:03d}.d{index:03d}"
            record = by_id.get(record_id, {})
            anchor = f"d90-mit-l08-p{page:03d}-d{index:03d}"
            try:
                source_slice = fenced_div_slice(MIT_WITNESS, anchor)
                target_slice = fenced_div_slice(MIT_TARGET, anchor)
            except Exception as exc:
                errors.append(str(exc))
                continue
            check(record.get("source_anchor") == anchor and record.get("target_anchor") == anchor, f"{record_id}: anchors differ")
            check((record.get("source_line_start"), record.get("source_line_end"), record.get("source_bytes"), record.get("source_content_sha256")) == source_slice, f"{record_id}: witness slice differs")
            check((record.get("target_line_start"), record.get("target_line_end"), record.get("target_bytes"), record.get("target_content_sha256")) == target_slice, f"{record_id}: target slice differs")
            check(record.get("formula_sequence_match") is True, f"{record_id}: formula match differs")

    figure_records = [record for record in workflow_records if record.get("entity_type") == "learning_surface" and record.get("surface_type") == "semantic_figure_description"]
    check(len(figure_records) == 5, "figure-description surface count differs")
    for page in FIGURE_PANELS:
        record_id = f"surface.mit.l08.figure-description.p{page:03d}.f001"
        record = by_id.get(record_id, {})
        anchor = f"d90-mit-l08-p{page:03d}-f001"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, anchor)
            target_slice = fenced_div_slice(MIT_TARGET, anchor)
        except Exception as exc:
            errors.append(str(exc))
            continue
        check((record.get("source_line_start"), record.get("source_line_end"), record.get("source_bytes"), record.get("source_content_sha256")) == source_slice, f"{record_id}: witness slice differs")
        check((record.get("target_line_start"), record.get("target_line_end"), record.get("target_bytes"), record.get("target_content_sha256")) == target_slice, f"{record_id}: target slice differs")
        check(record.get("panel_count") == 1 and record.get("copied_source_graphic_bytes") == 0, f"{record_id}: figure disposition differs")

    try:
        events = ledger_events()
    except Exception as exc:
        errors.append(str(exc))
        events = {}
    correction_pages = {
        "O015-MIT-SEM-0009": ([42, 48, 49], "correction.o015-mit-sem-0009"),
        "O015-MIT-SEM-0010": ([43], "correction.o015-mit-sem-0010"),
        "O015-MIT-SEM-0011": ([45], "correction.o015-mit-sem-0011"),
    }
    for event_id, (pages, correction_id) in correction_pages.items():
        correction = by_id.get(correction_id, {})
        check(correction.get("source_event_id") == event_id, f"{correction_id}: source event differs")
        check(correction.get("affected_segment_ids") == [f"d90.mit.ocw-6.253.l08.p{page:03d}" for page in pages], f"{correction_id}: segment binding differs")
        check(correction.get("source_pdf_pages") == pages, f"{correction_id}: source pages differ")
        check(correction.get("evidence_artifact_id") == "artifact.mit.l08.correction-snapshot", f"{correction_id}: evidence artifact differs")
        if event_id in events:
            event, binding = events[event_id]
            check(correction.get("surface") == event["surface"], f"{correction_id}: surface differs")
            check(correction.get("source_issue") == event["source_issue"], f"{correction_id}: source issue differs")
            check(correction.get("target_action") == event["target_action"], f"{correction_id}: target action differs")
            for field, value in binding.items():
                check(correction.get(field) == value, f"{correction_id}: binding {field} differs")

    for artifact_id, (path, rights_id) in ARTIFACTS.items():
        record = by_id.get(artifact_id, {})
        check(record.get("entity_type") == "artifact", f"{artifact_id}: missing artifact")
        check(record.get("path") == path and record.get("rights_id") == rights_id, f"{artifact_id}: path/rights differs")
        try:
            identity = file_info(path)
            check((record.get("bytes"), record.get("sha256")) == identity, f"{artifact_id}: stale artifact identity")
        except Exception as exc:
            errors.append(f"{artifact_id}: {exc}")

    check(by_id.get("artifact.mit.l08.correction-snapshot", {}).get("event_bindings") == [events[event_id][1] for event_id in sorted(events)] if events else False, "correction snapshot artifact bindings differ")
    check(by_id.get("artifact.mit.l08.builder", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "builder artifact command differs")
    check(by_id.get("artifact.mit.l08.target-html", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "HTML artifact command differs")
    check(by_id.get("artifact.mit.l08.target-pdf", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "PDF artifact command differs")

    for qa_id in QA_IDS:
        check(by_id.get(qa_id, {}).get("entity_type") == "qa_event", f"{qa_id}: missing QA event")
    check(by_id.get("qa.o015.mit-l08.rights", {}).get("license") == "CC BY-NC-SA 4.0", "L08 rights QA license differs")
    check(by_id.get("qa.o015.mit-l08.rights", {}).get("source_graphics_redistributed") == 0, "L08 rights QA claims source graphics")
    check(by_id.get("qa.o015.mit-l08.formulas", {}).get("display_formulas") == 26, "formula QA count differs")
    check(by_id.get("qa.o015.mit-l08.figures", {}).get("semantic_figure_descriptions") == 5, "figure QA count differs")
    check(by_id.get("qa.o015.mit-l08.corrections", {}).get("source_event_ids") == sorted(EXPECTED_EVENTS), "correction QA event set differs")
    check(by_id.get("qa.o015.mit-l08.semantic-rereview", {}).get("remaining_defects") == {"P1": 0, "P2": 0, "P3": 0}, "semantic rereview QA disposition differs")
    check(by_id.get("qa.o015.mit-l08.accessibility", {}).get("human_review_is_release_gate") is False, "accessibility QA encodes a human review gate")
    check(by_id.get("qa.o015.mit-l08.language", {}).get("human_review_is_release_gate") is False, "language QA encodes a human review gate")
    check(by_id.get("qa.o015.mit-l08.csv-losslessness", {}).get("row_order_matches_jsonl") is True, "CSV losslessness QA differs")
    check(by_id.get("qa.o015.mit-l08.backend-integration", {}).get("independent_validation_runs_required") == 2, "independent-validation contract differs")

    relations = [record for record in workflow_records if record.get("entity_type") == "relation"]
    triples = [(record.get("relation_type"), record.get("source_id"), record.get("target_id")) for record in relations]
    check(len(relations) == 55 and len(triples) == len(set(triples)), "L08 relation count or triple uniqueness differs")
    critical_relations = {
        "relation.mit.work-contains-l08": ("contains", "unit.mit.ocw-6.253.spring-2012", UNIT_ID),
        "relation.mit.l07-precedes-l08": ("precedes", "unit.mit.ocw-6.253.l07", UNIT_ID),
        "relation.mit.target-translates-witness-l08": ("translates", "artifact.mit.l08.target-source", "artifact.mit.l08.semantic-witness"),
        "relation.mit.html-adapts-target-l08": ("adapts", "artifact.mit.l08.target-html", "artifact.mit.l08.target-source"),
        "relation.mit.pdf-adapts-target-l08": ("adapts", "artifact.mit.l08.target-pdf", "artifact.mit.l08.target-source"),
        "relation.mit.rereview-depends-on-target-l08": ("depends-on", "artifact.mit.l08.independent-rereview", "artifact.mit.l08.target-source"),
    }
    for relation_id, expected_triple in critical_relations.items():
        record = by_id.get(relation_id, {})
        check((record.get("relation_type"), record.get("source_id"), record.get("target_id")) == expected_triple, f"{relation_id}: relation differs")

    try:
        content = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
        browser = json.loads((ROOT / MIT_BROWSER).read_text(encoding="utf-8"))
        visual = json.loads((ROOT / MIT_VISUAL).read_text(encoding="utf-8"))
        expected_boundary = {
            "copied_source_graphics": 0,
            "nested_items": 16,
            "next_heading": "LECTURE 5 - LECTURE OUTLINE",
            "next_source_page": 50,
            "source_displays": 26,
            "source_figure_panels": 5,
            "source_figures": 5,
            "source_items": 27,
            "source_pdf_pages": SOURCE_PAGES,
        }
        check(content.get("result") == "pass" and content.get("errors") == [], "MIT L08 content validation is not passing")
        boundary = content.get("boundary", {})
        check(all(boundary.get(key) == value for key, value in expected_boundary.items()), "MIT L08 content boundary differs")
        formula_inventory = content.get("formula_inventory", {})
        check(formula_inventory.get("witness_display_blocks") == 26 and formula_inventory.get("target_display_blocks") == 26, "MIT L08 formula inventory count differs")
        check(bool(re.fullmatch(r"[0-9a-f]{64}", str(formula_inventory.get("witness_sequence_sha256", "")))) and bool(re.fullmatch(r"[0-9a-f]{64}", str(formula_inventory.get("target_sequence_sha256", "")))), "MIT L08 formula inventory hashes differ")
        check(content.get("source_page_text_sha256") == {str(page): value for page, value in SOURCE_TEXT_FINGERPRINTS.items()}, "MIT L08 source-page hashes differ")
        html_identity = file_info(MIT_HTML)
        pdf_identity = file_info(MIT_READER_PDF)
        build = content.get("build", {})
        expected_build = {"html": list(html_identity), "pdf": list(pdf_identity)}
        expected_rebuild = [{"html": list(html_identity), "pdf": list(pdf_identity)}] * 2
        canonical_build = build.get("canonical", {})
        check(build.get("command") == RECEIPT_BUILD_COMMAND and build.get("deterministic_rebuilds") == 2, "MIT L08 deterministic build command/count differs")
        check(build.get("expected") == expected_build and build.get("rebuild_identities") == expected_rebuild, "MIT L08 deterministic build identities differ")
        check((canonical_build.get("html", {}).get("bytes"), canonical_build.get("html", {}).get("sha256")) == html_identity and (canonical_build.get("pdf", {}).get("bytes"), canonical_build.get("pdf", {}).get("sha256")) == pdf_identity and canonical_build.get("status") == "bound", "MIT L08 canonical build binding differs")
        html = content.get("html", {})
        pdf = content.get("pdf", {})
        check((html.get("source_pages"), html.get("source_items"), html.get("source_displays"), html.get("source_figures"), html.get("display_math_nodes"), html.get("images")) == (11, 27, 26, 5, 26, 0), "MIT L08 HTML topology differs")
        check(pdf.get("pages", 0) >= 1 and pdf.get("page_size") == "A4" and pdf.get("tagged") is False and pdf.get("images") == 0, "MIT L08 PDF topology differs")
        check(browser.get("result") == "pass" and (browser.get("build", {}).get("html_bytes"), browser.get("build", {}).get("html_sha256")) == html_identity, "MIT L08 browser QA evidence differs")
        check(visual.get("inspection", {}).get("result") == "pass" and (visual.get("pdf", {}).get("bytes"), visual.get("pdf", {}).get("sha256")) == pdf_identity, "MIT L08 visual QA evidence differs")
        check(pdf.get("render_sha256") == [item["sha256"] for item in visual.get("renders", [])], "MIT L08 render hash sequence differs")
        for item in content.get("files", []):
            path = item.get("path")
            if path:
                check(file_info(path) == (item.get("bytes"), item.get("sha256")), f"MIT L08 content receipt binds stale file {path}")
        rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
        for path in (MIT_CENSUS, MIT_WITNESS, MIT_TARGET):
            check(file_info(path)[1] in rereview, f"MIT L08 independent rereview does not bind {path}")
        check(bool(re.search(r"P1\s*=\s*0\s*,\s*P2\s*=\s*0\s*,\s*P3\s*=\s*0", rereview)), "MIT L08 independent rereview severity differs")
        check(file_info(MIT_PDF) == SOURCE_PDF_IDENTITY, "MIT authority PDF identity differs")
    except Exception as exc:
        errors.append(f"reader evidence validation failed: {exc}")

    new_id_hash = digest(("\n".join(sorted(expected)) + "\n").encode("utf-8"))
    receipt = {
        "schema": "o015-mit-l08-backend-validation-v1",
        "recorded_at": RECORDED_AT,
        "result": "pass" if not errors else "fail",
        "errors": errors,
        "workflow": WORKFLOW,
        "protected_baseline": {
            "record_count": BASELINE_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]},
            "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "raw_reconstruction_passed": not any("baseline" in error.lower() for error in errors),
        },
        "admission": {
            "new_record_count": len(workflow_records),
            "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in workflow_records).items())),
            "new_id_set_sha256": new_id_hash,
            "expected_new_record_count": 137,
            "segment_ids": [f"d90.mit.ocw-6.253.l08.p{page:03d}" for page in SOURCE_PAGES],
            "formula_surface_ids": [f"surface.mit.l08.formula.p{page:03d}.d{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)],
            "figure_description_surface_ids": [f"surface.mit.l08.figure-description.p{page:03d}.f001" for page in FIGURE_PANELS],
            "correction_record_ids": [f"correction.o015-mit-sem-{number:04d}" for number in range(9, 12)],
            "artifact_ids": sorted(ARTIFACTS),
            "qa_event_ids": sorted(QA_IDS),
            "relation_count": len(relations),
        },
        "final_backend": {
            "record_count": len(records),
            "entity_counts": dict(sorted(Counter(record["entity_type"] for record in records).items())),
            "id_set_sha256": id_set(records),
            "record_set_sha256": record_set(records),
            "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
            "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
            "csv_projection_lossless": row_records == records,
            "references_closed": not any("dangling" in error for error in errors),
        },
        "correction_snapshot": {"bytes": LEDGER_IDENTITY[0], "sha256": LEDGER_IDENTITY[1], "event_ids": sorted(EXPECTED_EVENTS)},
        "reader_bindings": {
            "target": {"path": MIT_TARGET, "bytes": file_info(MIT_TARGET)[0], "sha256": file_info(MIT_TARGET)[1]} if (ROOT / MIT_TARGET).is_file() else None,
            "html": {"path": MIT_HTML, "bytes": file_info(MIT_HTML)[0], "sha256": file_info(MIT_HTML)[1]} if (ROOT / MIT_HTML).is_file() else None,
            "pdf": {"path": MIT_READER_PDF, "bytes": file_info(MIT_READER_PDF)[0], "sha256": file_info(MIT_READER_PDF)[1]} if (ROOT / MIT_READER_PDF).is_file() else None,
            "rereview": {"path": MIT_REREVIEW, "bytes": file_info(MIT_REREVIEW)[0], "sha256": file_info(MIT_REREVIEW)[1]} if (ROOT / MIT_REREVIEW).is_file() else None,
        },
        "independent_validation_runs_required": 2,
    }
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(mode="wb", prefix=".MIT_L08_BACKEND_VALIDATION.", suffix=".stage", dir=RECEIPT_PATH.parent, delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        staged = Path(handle.name)
    try:
        if staged.read_bytes() != payload:
            raise ValueError("staged backend receipt readback differs")
        os.replace(staged, RECEIPT_PATH)
    finally:
        staged.unlink(missing_ok=True)
    print(json.dumps({
        "result": receipt["result"],
        "errors": len(errors),
        "new_records": len(workflow_records),
        "final_records": len(records),
        "jsonl_sha256": digest(jsonl_raw),
        "csv_sha256": digest(csv_raw),
        "receipt": str(RECEIPT_PATH.relative_to(ROOT)).replace("\\", "/"),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
