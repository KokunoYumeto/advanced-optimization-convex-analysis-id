#!/usr/bin/env python3
"""Independent, fail-closed validation of the MIT L09 backend admission.

The validator accepts either the canonical backend or an explicitly staged pair.
It reconstructs the protected 1,957-record L08 baseline byte for byte, validates
the complete 142-record L09 projection against current source and QA evidence,
and writes the only authoritative L09 backend-validation receipt atomically.
"""

from __future__ import annotations

import argparse
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
RECEIPT_PATH = ROOT / "qa/MIT_L09_BACKEND_VALIDATION.json"

RECORDED_AT = "2026-08-24T12:00:00Z"
WORKFLOW = "o015-mit-l09-backend-v1"
UNIT_ID = "unit.mit.ocw-6.253.l09"
SOURCE_PAGES = list(range(50, 64))

BASELINE_COUNT = 1_957
BASELINE_JSONL = (1_441_643, "0779f8bc03d437da72adafe2daf99c820d5849f0e14b630a0c3bd6f512b10085")
BASELINE_CSV = (1_727_978, "ed209ae9325d27b5e1360b59804833e91ab014c821741f2f52badfc5f0eda836")
BASELINE_ID_SET_SHA256 = "0a83c8e41324ebb19a9473b61dffc3091330e66d5b6ebba5a46f0079df20c749"
BASELINE_RECORD_SET_SHA256 = "7e127fc2e2fe3e300af69a7127337786fa551cf181caa1d0a31a836212434864"
EXPECTED_NEW_COUNT = 142
EXPECTED_ENTITY_COUNTS = Counter({
    "unit": 1,
    "segment": 14,
    "learning_surface": 28,
    "correction": 8,
    "artifact": 19,
    "qa_event": 17,
    "relation": 55,
})

PAGE_ITEMS = {50: 4, 51: 3, 52: 1, 53: 1, 54: 5, 55: 3, 56: 1, 57: 2, 58: 3, 59: 5, 60: 4, 61: 3, 62: 1, 63: 5}
PAGE_NESTED = {50: 0, 51: 0, 52: 5, 53: 0, 54: 0, 55: 2, 56: 2, 57: 0, 58: 3, 59: 0, 60: 2, 61: 3, 62: 0, 63: 0}
PAGE_DISPLAYS = {50: 0, 51: 1, 52: 2, 53: 2, 54: 2, 55: 0, 56: 2, 57: 0, 58: 2, 59: 4, 60: 0, 61: 0, 62: 3, 63: 1}
FIGURE_PANELS = {51: 1, 53: 1, 54: 1, 55: 1, 57: 6, 58: 1, 60: 1}
EXAMPLES = {(58, 3), (63, 4)}

SOURCE_TEXT_FINGERPRINTS = {
    50: (289, "595b3d566a6d820573632a5dc853afb2c0cf8474fab8693a57d84ff33335ae63"),
    51: (628, "29ea48091d0c0854adeefc2cee9ff13514e0d0f8e764102e4cef02cd43346a4c"),
    52: (761, "8c6f781da342b06c073fc28c3c3e709e6806da27fc41b7af41bb1a75bdc4b00e"),
    53: (1_111, "d3d5afc97dd3e68df351ea9c9bf650ef22211e423973655d5e5bf7e9730c8166"),
    54: (980, "7f38485ab8f3487a4048bacc110fa6a137c39f3bfd034fcda3133c39b378594c"),
    55: (968, "b0e4296e764c3f5599b607b8a4ec4847627c349db28c45fa9ae534a3a34aa2fa"),
    56: (665, "d6a4b532b62933feb3f40d77eb4abadc212bd984a1ed0c27da756677bcc4c147"),
    57: (1_667, "a34def3e962e6d71573a7a45dc48ac594c792bcbc87d77d1720daaa9f1e4d6ac"),
    58: (902, "6203cc3ebafa733f38fa3c753f5c99af25620209cb4beeaa2f88ff9ed122e947"),
    59: (942, "ca166a557ed87c168774a5ecc542aef74009fa53a199b0ab700633b3c56cc363"),
    60: (876, "218eb580f08974fa64649727fd0a03e1425967c58e097ac43b2713329450c10e"),
    61: (809, "a96ceb4046bb0bc9b5aa3f3afbab02ed758a9a377afc99249f8f188ce20bce1f"),
    62: (1_048, "62f283dd5015d2ea7a9302a225d7813d7f0a399330d0cbf8ae3b236d4239ad91"),
    63: (852, "c404f9420102103e3ff43757dcdeecf99a9ddf4947c0d5f08c27ee17166fe314"),
    64: (305, "20de895948a7967b9f1a52b44d4a6d4fafa26b8744b23ef9bb459aa566d69766"),
}
SOURCE_RENDER_FINGERPRINTS = {
    50: (21_450, "5dceaf64ba215ff48af8175a2249d5cc11246aca4e1d3964539c323cff5f95a2"),
    51: (56_137, "b66a1dea301d7ba61d1abb544feeba31172617f6db8997f8d19258cf6dd5dedf"),
    52: (48_320, "54053898ab67c83fa74fc713a421ca1308d8e23b612bf60f9a5b23f36417674f"),
    53: (50_988, "72b29cb179a539b9d3f973efc6bdc9a22dacc68c3081e500b26f9fe57ca4c9e2"),
    54: (60_911, "2e03eb3734ffaf54a20e789d5affec335bdbd0db3486551d7907162120a9ee07"),
    55: (45_344, "6614da5d3cc2d9435f2bfa8c983340451c6a0ae736c894e26e142b91fcb37c00"),
    56: (39_493, "3ed8df60ebea27f3ef26c8c86ded32c7ffb4f73f008bcb8d8ed7151ee5d40498"),
    57: (47_145, "2dbd1d5483caabaf9865eb5924cd030cb41d286e7ed23e1ffa02f4e771911951"),
    58: (66_756, "4643b578e2f2e6d3d00b3be73413b47ddfffb7bc0d284f4970c44823b393990f"),
    59: (47_022, "fe6b81f453ac1bff8bfc6c0b338d01e29e2a9d6acb0a53e3d3c1ead70aca0adb"),
    60: (55_850, "68be066aa2204a4456402c1bb3d7d566af90cc0353ad7854222e88e5a4eda64e"),
    61: (51_495, "c4f424c4994aeceeda78449be3465641ebb169756e77fc0433a1c16505b212ff"),
    62: (58_017, "1a6e724fcd9122a3a0cb93266ecda17d23c73a3bce690ada94ad2da92bb6604e"),
    63: (52_338, "083a06d31cac9f55addfbd7b29376cdc83f10f8e355eea98e8269174b10d6acc"),
}

MIT_PDF = "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
MIT_CENSUS = "00_control/MIT_L09_LECTURE_5_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/MIT_L09_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-09-lecture-5-recession-minima-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-09-kuliah-5-resesi-dan-minimum-id.md"
MIT_HTML = "output/html/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.pdf"
MIT_REPORT = "qa/MIT_L09_VALIDATION.json"
MIT_BROWSER = "qa/MIT_L09_BROWSER_QA.json"
MIT_VISUAL = "qa/MIT_L09_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L09_INDEPENDENT_REREVIEW.md"
MIT_BACKEND_GENERATOR = "qa/extend_backend_mit_l09.py"
MIT_BACKEND_VALIDATOR = "qa/validate_backend_mit_l09.py"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
CENSUS_IDENTITY = (19_753, "e4357023e0c2a6d4478adb904e9fec2789bc616f56bfba07d05789f74cc0cd85")
LEDGER_IDENTITY = (5_506, "e5ef98e4218d768cd51053e08d55c5ef44a44afa26237be652152eecd1052acc")
HTML_IDENTITY = (118_805, "1dcbb699a620a00c05e39ca6c28d6e40c408b1b70bdc2a4678d634654ed771c9")
PDF_IDENTITY = (101_797, "34b8b184a90a5da04ac421b6b8d73840cef4b43bb43a49b01fdc65c1b1e04721")
RECEIPT_BUILD_COMMAND = "python qa/build_mit_l09.py --html-output <html> --pdf-output <pdf>"
CANONICAL_BUILD_COMMAND = (
    "python qa/build_mit_l09.py --html-output "
    "output/html/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.html "
    "--pdf-output output/pdf/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.pdf"
)
EXPECTED_EVENT_IDS = tuple(f"O015-MIT-SEM-{number:04d}" for number in range(12, 20))
CORRECTION_PAGES = {
    "O015-MIT-SEM-0012": [56, 58, 59, 60, 61, 62, 63],
    "O015-MIT-SEM-0013": [55],
    "O015-MIT-SEM-0014": [57],
    "O015-MIT-SEM-0015": [59],
    "O015-MIT-SEM-0016": [60],
    "O015-MIT-SEM-0017": [61],
    "O015-MIT-SEM-0018": [61],
    "O015-MIT-SEM-0019": [60, 61, 62, 63],
}

ARTIFACTS = {
    "artifact.mit.l09.boundary-census": (MIT_CENSUS, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l09.semantic-witness": (MIT_WITNESS, "rights.o015-mit-semantic-witness"),
    "artifact.mit.l09.target-source": (MIT_TARGET, "rights.o015-mit-id-pilot"),
    "artifact.mit.l09.target-html": (MIT_HTML, "rights.o015-mit-id-pilot"),
    "artifact.mit.l09.target-pdf": (MIT_READER_PDF, "rights.o015-mit-id-pilot"),
    "artifact.mit.l09.builder": ("qa/build_mit_l09.py", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l09.validator": ("qa/validate_mit_l09.py", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l09.validation": (MIT_REPORT, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l09.browser-qa": (MIT_BROWSER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l09.visual-qa": (MIT_VISUAL, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l09.independent-rereview": (MIT_REREVIEW, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l09.correction-snapshot": (MIT_LEDGER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l09.css": ("source/id-ID/mit-l09.css", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l09.pdf-preamble": ("source/id-ID/mit-l09-preamble.tex", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l09.pdf-filter": ("source/id-ID/mit-l09-pdf-filter.lua", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l09.before-body": ("source/id-ID/mit-l09-before-body.html", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l09.after-body": ("source/id-ID/mit-l09-after-body.html", "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-generator-mit-l09": (MIT_BACKEND_GENERATOR, "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-validator-mit-l09": (MIT_BACKEND_VALIDATOR, "rights.o015-mit-l01-backend-tooling"),
}
QA_IDS = {f"qa.o015.mit-l09.{suffix}" for suffix in (
    "source-freeze", "semantic-reconstruction", "topology", "formulas", "figures",
    "corrections", "build", "html", "browser", "pdf", "visual", "semantic-rereview",
    "accessibility", "language", "rights", "csv-losslessness", "backend-integration",
)}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), digest(data)


def id_set(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def record_set(records: list[dict[str, Any]]) -> str:
    data = "".join(canonical(record) + "\n" for record in sorted(records, key=lambda item: item["id"]))
    return digest(data.encode("utf-8"))


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip().startswith("::: {") and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)]
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
    return b"".join(line for line in raw.splitlines(keepends=True) if json.loads(line.decode("utf-8")).get("responsible_workflow") != WORKFLOW)


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


def ledger_events() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if file_info(MIT_LEDGER) != LEDGER_IDENTITY:
        raise ValueError("L09 correction snapshot identity differs")
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), 1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id not in EXPECTED_EVENT_IDS or event_id in result:
            raise ValueError(f"unexpected or duplicate correction event: {event_id}")
        if any(not event.get(field) for field in ("authority", "source", "surface", "source_issue", "target_action", "class")):
            raise ValueError(f"{event_id}: incomplete correction evidence")
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
    if tuple(sorted(result)) != EXPECTED_EVENT_IDS:
        raise ValueError("L09 correction event set differs")
    return result


def expected_ids() -> set[str]:
    ids = {UNIT_ID}
    ids.update(f"d90.mit.ocw-6.253.l09.p{page:03d}" for page in SOURCE_PAGES)
    ids.update(f"surface.mit.l09.formula.p{page:03d}.d{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1))
    ids.update(f"surface.mit.l09.figure-description.p{page:03d}.f001" for page in FIGURE_PANELS)
    ids.update(f"surface.mit.l09.example.p{page:03d}.i{index:03d}" for page, index in EXAMPLES)
    ids.update(f"correction.o015-mit-sem-{number:04d}" for number in range(12, 20))
    ids.update(ARTIFACTS)
    ids.update(QA_IDS)
    core = {
        "work-contains-l09", "witness-edition-contains-l09", "target-edition-contains-l09",
        "l08-precedes-l09", "witness-adapts-authority-pdf-l09", "target-translates-witness-l09",
        "html-adapts-target-l09", "pdf-adapts-target-l09", "browser-qa-depends-on-html-l09",
        "visual-qa-depends-on-pdf-l09", "validation-depends-on-browser-qa-l09",
        "validation-depends-on-visual-qa-l09", "rereview-depends-on-target-l09",
    }
    ids.update(f"relation.mit.{suffix}" for suffix in core)
    ids.update(f"relation.mit.l09-contains-p{page:03d}" for page in SOURCE_PAGES)
    ids.update(f"relation.mit.l09-formula-p{page:03d}-d{index:03d}-illustrates-segment" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1))
    ids.update(f"relation.mit.l09-figure-p{page:03d}-illustrates-segment" for page in FIGURE_PANELS)
    ids.update(f"relation.mit.l09-example-p{page:03d}-exercises-segment" for page, _ in EXAMPLES)
    return ids


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}.", suffix=".stage", dir=path.parent, delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        staged = Path(handle.name)
    try:
        if staged.read_bytes() != payload:
            raise ValueError("staged backend receipt readback differs")
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, default=JSONL_PATH)
    parser.add_argument("--input-csv", type=Path, default=CSV_PATH)
    parser.add_argument("--receipt", type=Path, default=RECEIPT_PATH)
    args = parser.parse_args()
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonl_raw = args.input_jsonl.read_bytes()
        csv_raw = args.input_csv.read_bytes()
        records = [json.loads(line) for line in jsonl_raw.decode("utf-8", errors="strict").splitlines() if line]
        rows = list(csv.DictReader(io.StringIO(csv_raw.decode("utf-8", errors="strict"))))
        row_records = [json.loads(row["record_json"]) for row in rows]
    except Exception as exc:
        receipt = {"schema": "o015-mit-l09-backend-validation-v1", "recorded_at": RECORDED_AT, "result": "fail", "errors": [f"backend parse failed: {exc}"], "workflow": WORKFLOW}
        write_receipt(args.receipt, receipt)
        print(json.dumps({"result": "fail", "errors": 1, "receipt": str(args.receipt)}, sort_keys=True))
        return 1

    check(schema.get("schema") == "o015-modular-backend-schema", "backend schema identity differs")
    check(row_records == records, "CSV record_json projection differs from JSONL")
    check(len(records) == BASELINE_COUNT + EXPECTED_NEW_COUNT, f"final record count differs: {len(records)}")
    check(len({record.get("id") for record in records}) == len(records), "duplicate stable IDs")
    entity_rank = {name: index for index, name in enumerate(schema.get("entity_order", []))}
    try:
        check(records == sorted(records, key=lambda record: (entity_rank[record["entity_type"]], record["id"])), "backend record order differs")
    except Exception as exc:
        errors.append(f"backend ordering check failed: {exc}")

    workflow_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    baseline_records = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    expected = expected_ids()
    check(len(expected) == EXPECTED_NEW_COUNT, "validator stable-ID contract count differs")
    check({record.get("id") for record in workflow_records} == expected, "L09 workflow stable-ID set differs")
    check(len(workflow_records) == EXPECTED_NEW_COUNT, f"L09 workflow record count differs: {len(workflow_records)}")
    check(Counter(record.get("entity_type") for record in workflow_records) == EXPECTED_ENTITY_COUNTS, "L09 entity-type counts differ")
    check(all(record.get("recorded_at") == RECORDED_AT for record in workflow_records), "L09 recorded_at values differ")
    check(len(baseline_records) == BASELINE_COUNT, "protected baseline record count differs")
    check(id_set(baseline_records) == BASELINE_ID_SET_SHA256, "protected baseline ID-set hash differs")
    check(record_set(baseline_records) == BASELINE_RECORD_SET_SHA256, "protected baseline record-set hash differs")
    try:
        stripped_jsonl = strip_workflow_jsonl(jsonl_raw)
        stripped_csv = strip_workflow_csv(csv_raw)
        check((len(stripped_jsonl), digest(stripped_jsonl)) == BASELINE_JSONL, "raw JSONL baseline reconstruction differs")
        check((len(stripped_csv), digest(stripped_csv)) == BASELINE_CSV, "raw CSV baseline reconstruction differs")
    except Exception as exc:
        errors.append(f"raw baseline reconstruction failed: {exc}")

    by_id = {record.get("id"): record for record in records}
    try:
        id_pattern = re.compile(schema["id_pattern"])
        for record in records:
            record_id = record.get("id")
            check(record.get("schema") == "o015-modular-backend-record", f"{record_id}: record schema differs")
            check(record.get("schema_version") == "1.0.0", f"{record_id}: schema version differs")
            check(isinstance(record_id, str) and bool(id_pattern.fullmatch(record_id)), f"{record_id}: invalid ID")
            for field in schema.get("required_common", []):
                check(field in record, f"{record_id}: missing common field {field}")
            for field in schema.get("required_by_entity", {}).get(record.get("entity_type"), []):
                check(field in record, f"{record_id}: missing required field {field}")
            for field in schema.get("reference_fields", []):
                if field not in record:
                    continue
                values = record[field] if isinstance(record[field], list) else [record[field]]
                for value in values:
                    check(value in by_id, f"{record_id}: dangling {field} {value}")
    except Exception as exc:
        errors.append(f"schema/reference validation failed: {exc}")

    unit = by_id.get(UNIT_ID, {})
    check(unit.get("entity_type") == "unit" and unit.get("order") == 9, "L09 unit identity/order differs")
    check(unit.get("source_pdf_pages") == SOURCE_PAGES and unit.get("next_source_page") == 64, "L09 unit boundary differs")
    check((unit.get("source_item_count"), unit.get("nested_source_item_count"), unit.get("source_display_count"), unit.get("source_figure_count"), unit.get("source_figure_panel_count"), unit.get("explicit_example_count"), unit.get("copied_source_graphics")) == (41, 17, 19, 7, 12, 2, 0), "L09 unit topology differs")
    check(unit.get("correction_event_ids") == list(EXPECTED_EVENT_IDS), "L09 unit correction IDs differ")
    check(unit.get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "L09 unit build command differs")

    for order, page in enumerate(SOURCE_PAGES, 1):
        record_id = f"d90.mit.ocw-6.253.l09.p{page:03d}"
        segment = by_id.get(record_id, {})
        anchor = f"d90-mit-l09-p{page:03d}"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, anchor)
            target_slice = fenced_div_slice(MIT_TARGET, anchor)
            check((segment.get("source_line_start"), segment.get("source_line_end"), segment.get("source_bytes"), segment.get("source_content_sha256")) == source_slice, f"{record_id}: witness slice differs")
            check((segment.get("target_line_start"), segment.get("target_line_end"), segment.get("target_bytes"), segment.get("target_content_sha256")) == target_slice, f"{record_id}: target slice differs")
        except Exception as exc:
            errors.append(str(exc))
        check(segment.get("order") == order and segment.get("source_pdf_page") == page, f"{record_id}: page/order differs")
        check(segment.get("source_anchor") == anchor and segment.get("target_anchor") == anchor, f"{record_id}: anchors differ")
        check((segment.get("source_item_count"), segment.get("nested_source_item_count"), segment.get("source_display_count")) == (PAGE_ITEMS[page], PAGE_NESTED[page], PAGE_DISPLAYS[page]), f"{record_id}: item/display topology differs")
        check((segment.get("source_figure_count"), segment.get("source_figure_panel_count"), segment.get("explicit_example_count")) == (1 if page in FIGURE_PANELS else 0, FIGURE_PANELS.get(page, 0), sum(1 for p, _ in EXAMPLES if p == page)), f"{record_id}: figure/example topology differs")
        check((segment.get("source_page_text_bytes"), segment.get("source_page_text_sha256")) == SOURCE_TEXT_FINGERPRINTS[page], f"{record_id}: source text fingerprint differs")
        check((segment.get("source_page_render_bytes"), segment.get("source_page_render_sha256")) == SOURCE_RENDER_FINGERPRINTS[page], f"{record_id}: source render fingerprint differs")

    formula_order = 0
    for page in SOURCE_PAGES:
        for index in range(1, PAGE_DISPLAYS[page] + 1):
            formula_order += 1
            record_id = f"surface.mit.l09.formula.p{page:03d}.d{index:03d}"
            record = by_id.get(record_id, {})
            anchor = f"d90-mit-l09-p{page:03d}-d{index:03d}"
            try:
                source_slice = fenced_div_slice(MIT_WITNESS, anchor)
                target_slice = fenced_div_slice(MIT_TARGET, anchor)
                check((record.get("source_line_start"), record.get("source_line_end"), record.get("source_bytes"), record.get("source_content_sha256")) == source_slice, f"{record_id}: witness slice differs")
                check((record.get("target_line_start"), record.get("target_line_end"), record.get("target_bytes"), record.get("target_content_sha256")) == target_slice, f"{record_id}: target slice differs")
            except Exception as exc:
                errors.append(str(exc))
            check(record.get("surface_type") == "display_formula" and record.get("formula_sequence_order") == formula_order and record.get("page_formula_order") == index and record.get("formula_sequence_match") is True, f"{record_id}: formula topology differs")

    for page, panel_count in FIGURE_PANELS.items():
        record_id = f"surface.mit.l09.figure-description.p{page:03d}.f001"
        record = by_id.get(record_id, {})
        anchor = f"d90-mit-l09-p{page:03d}-f001"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, anchor)
            target_slice = fenced_div_slice(MIT_TARGET, anchor)
            check((record.get("source_line_start"), record.get("source_line_end"), record.get("source_bytes"), record.get("source_content_sha256")) == source_slice, f"{record_id}: witness slice differs")
            check((record.get("target_line_start"), record.get("target_line_end"), record.get("target_bytes"), record.get("target_content_sha256")) == target_slice, f"{record_id}: target slice differs")
        except Exception as exc:
            errors.append(str(exc))
        check(record.get("surface_type") == "semantic_figure_description" and record.get("panel_count") == panel_count and record.get("copied_source_graphic_bytes") == 0 and record.get("semantic_description_preserved") is True, f"{record_id}: figure disposition differs")

    for order, (page, index) in enumerate(sorted(EXAMPLES), 1):
        record_id = f"surface.mit.l09.example.p{page:03d}.i{index:03d}"
        record = by_id.get(record_id, {})
        anchor = f"d90-mit-l09-p{page:03d}-i{index:03d}"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, anchor)
            target_slice = fenced_div_slice(MIT_TARGET, anchor)
            check((record.get("source_line_start"), record.get("source_line_end"), record.get("source_bytes"), record.get("source_content_sha256")) == source_slice, f"{record_id}: witness slice differs")
            check((record.get("target_line_start"), record.get("target_line_end"), record.get("target_bytes"), record.get("target_content_sha256")) == target_slice, f"{record_id}: target slice differs")
        except Exception as exc:
            errors.append(str(exc))
        check(record.get("surface_type") == "worked_example" and record.get("example_sequence_order") == order, f"{record_id}: example topology differs")

    try:
        events = ledger_events()
    except Exception as exc:
        errors.append(str(exc))
        events = {}
    for event_id, pages in CORRECTION_PAGES.items():
        number = int(event_id.rsplit("-", 1)[1])
        record_id = f"correction.o015-mit-sem-{number:04d}"
        record = by_id.get(record_id, {})
        check(record.get("source_event_id") == event_id, f"{record_id}: source event differs")
        check(record.get("affected_segment_ids") == [f"d90.mit.ocw-6.253.l09.p{page:03d}" for page in pages], f"{record_id}: segment binding differs")
        check(record.get("source_pdf_pages") == pages and record.get("evidence_artifact_id") == "artifact.mit.l09.correction-snapshot", f"{record_id}: source/evidence binding differs")
        if event_id in events:
            event, binding = events[event_id]
            for field in ("surface", "source_issue", "target_action"):
                check(record.get(field) == event[field], f"{record_id}: {field} differs")
            for field, value in binding.items():
                check(record.get(field) == value, f"{record_id}: binding {field} differs")

    for artifact_id, (path, rights_id) in ARTIFACTS.items():
        record = by_id.get(artifact_id, {})
        check(record.get("entity_type") == "artifact", f"{artifact_id}: missing artifact")
        check(record.get("path") == path and record.get("rights_id") == rights_id, f"{artifact_id}: path/rights differs")
        try:
            check((record.get("bytes"), record.get("sha256")) == file_info(path), f"{artifact_id}: stale artifact identity")
        except Exception as exc:
            errors.append(f"{artifact_id}: {exc}")
    check(file_info(MIT_PDF) == SOURCE_PDF_IDENTITY, "MIT authority PDF identity differs")
    check(file_info(MIT_CENSUS) == CENSUS_IDENTITY, "MIT L09 census identity differs")
    check(file_info(MIT_HTML) == HTML_IDENTITY, "MIT L09 HTML identity differs")
    check(file_info(MIT_READER_PDF) == PDF_IDENTITY, "MIT L09 PDF identity differs")
    if events:
        check(by_id.get("artifact.mit.l09.correction-snapshot", {}).get("event_bindings") == [events[event_id][1] for event_id in EXPECTED_EVENT_IDS], "correction snapshot artifact bindings differ")

    for qa_id in QA_IDS:
        check(by_id.get(qa_id, {}).get("entity_type") == "qa_event", f"{qa_id}: missing QA event")
    check(by_id.get("qa.o015.mit-l09.rights", {}).get("license") == "CC BY-NC-SA 4.0", "L09 rights license differs")
    check(by_id.get("qa.o015.mit-l09.rights", {}).get("source_graphics_redistributed") == 0, "L09 rights QA claims copied graphics")
    check(by_id.get("qa.o015.mit-l09.formulas", {}).get("display_formulas") == 19, "L09 formula QA count differs")
    check(by_id.get("qa.o015.mit-l09.figures", {}).get("source_figure_panels") == 12, "L09 figure-panel QA count differs")
    check(by_id.get("qa.o015.mit-l09.corrections", {}).get("source_event_ids") == list(EXPECTED_EVENT_IDS), "L09 correction QA set differs")
    check(by_id.get("qa.o015.mit-l09.semantic-rereview", {}).get("remaining_defects") == {"P1": 0, "P2": 0, "P3": 0}, "L09 semantic rereview disposition differs")
    check(by_id.get("qa.o015.mit-l09.accessibility", {}).get("human_review_is_release_gate") is False, "accessibility QA encodes a human gate")
    check(by_id.get("qa.o015.mit-l09.language", {}).get("human_review_is_release_gate") is False, "language QA encodes a human gate")
    check(by_id.get("qa.o015.mit-l09.csv-losslessness", {}).get("row_order_matches_jsonl") is True, "CSV losslessness QA differs")
    check(by_id.get("qa.o015.mit-l09.backend-integration", {}).get("independent_validation_runs_required") == 2, "independent-validation contract differs")

    relations = [record for record in workflow_records if record.get("entity_type") == "relation"]
    triples = [(record.get("relation_type"), record.get("source_id"), record.get("target_id")) for record in relations]
    check(len(relations) == 55 and len(triples) == len(set(triples)), "L09 relation count or triple uniqueness differs")
    critical = {
        "relation.mit.work-contains-l09": ("contains", "unit.mit.ocw-6.253.spring-2012", UNIT_ID),
        "relation.mit.l08-precedes-l09": ("precedes", "unit.mit.ocw-6.253.l08", UNIT_ID),
        "relation.mit.target-translates-witness-l09": ("translates", "artifact.mit.l09.target-source", "artifact.mit.l09.semantic-witness"),
        "relation.mit.html-adapts-target-l09": ("adapts", "artifact.mit.l09.target-html", "artifact.mit.l09.target-source"),
        "relation.mit.pdf-adapts-target-l09": ("adapts", "artifact.mit.l09.target-pdf", "artifact.mit.l09.target-source"),
        "relation.mit.rereview-depends-on-target-l09": ("depends-on", "artifact.mit.l09.independent-rereview", "artifact.mit.l09.target-source"),
    }
    for relation_id, triple in critical.items():
        record = by_id.get(relation_id, {})
        check((record.get("relation_type"), record.get("source_id"), record.get("target_id")) == triple, f"{relation_id}: relation differs")

    try:
        content = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
        browser = json.loads((ROOT / MIT_BROWSER).read_text(encoding="utf-8"))
        visual = json.loads((ROOT / MIT_VISUAL).read_text(encoding="utf-8"))
        check(content.get("result") == "pass" and content.get("errors") == [] and content.get("model_identification") == "OpenAI Codex gpt-5.6-sol, Ultra", "MIT L09 content validation differs")
        boundary = content.get("boundary", {})
        expected_boundary = {"source_pdf_pages": SOURCE_PAGES, "next_source_page": 64, "next_heading": "LECTURE 6 - LECTURE OUTLINE", "source_items": 41, "nested_items": 17, "source_displays": 19, "source_figures": 7, "source_figure_panels": 12, "examples": 2, "copied_source_graphics": 0, "exercises": 0, "hints": 0, "answers": 0, "solutions": 0, "code_surfaces": 0, "interactive_surfaces": 0}
        check(boundary == expected_boundary, "MIT L09 content boundary differs")
        formulas = content.get("formula_inventory", {})
        check(formulas.get("witness_display_blocks") == 19 and formulas.get("target_display_blocks") == 19, "MIT L09 formula inventory count differs")
        authority = content.get("authority", {})
        check(authority.get("source_page_text_sha256") == {str(page): value[1] for page, value in SOURCE_TEXT_FINGERPRINTS.items()}, "MIT L09 source-page hash map differs")
        check(authority.get("source_page_text_bytes") == {str(page): value[0] for page, value in SOURCE_TEXT_FINGERPRINTS.items()}, "MIT L09 source-page byte map differs")
        build = content.get("build", {})
        expected_build = {"html": list(HTML_IDENTITY), "pdf": list(PDF_IDENTITY)}
        check(build.get("command") == RECEIPT_BUILD_COMMAND and build.get("deterministic_rebuilds") == 2 and build.get("expected") == expected_build and build.get("rebuild_identities") == [expected_build, expected_build], "MIT L09 deterministic build evidence differs")
        canonical_build = build.get("canonical", {})
        check(canonical_build.get("status") == "bound" and (canonical_build.get("html", {}).get("bytes"), canonical_build.get("html", {}).get("sha256")) == HTML_IDENTITY and (canonical_build.get("pdf", {}).get("bytes"), canonical_build.get("pdf", {}).get("sha256")) == PDF_IDENTITY, "MIT L09 canonical build binding differs")
        html = content.get("html", {})
        check((html.get("lang"), html.get("source_pages"), html.get("source_items"), html.get("source_displays"), html.get("source_figures"), html.get("display_math_nodes"), html.get("images"), html.get("media_or_embeds"), html.get("form_controls"), html.get("duplicate_ids"), html.get("unresolved_fragments")) == ("id-ID", 14, 41, 19, 7, 19, 0, 0, 0, [], []), "MIT L09 HTML topology differs")
        pdf = content.get("pdf", {})
        boxes = pdf.get("page_size_points", [])
        check(pdf.get("pages") == 7 and len(boxes) == 7 and all(abs(float(box[0]) - 595.276) <= 0.01 and abs(float(box[1]) - 841.89) <= 0.01 for box in boxes) and pdf.get("searchable") is True and pdf.get("tagged") is False and pdf.get("images") == 0 and pdf.get("encrypted") is False and pdf.get("to_unicode_all_fonts") is True, "MIT L09 PDF topology differs")
        evidence = content.get("evidence", {})
        check(evidence.get("stage") == "strict-final" and all(evidence.get(name, {}).get("status") == "validated" for name in ("browser", "visual", "rereview")), "MIT L09 strict-final evidence differs")
        check(browser.get("result") == "pass" and (browser.get("html", {}).get("bytes"), browser.get("html", {}).get("sha256")) == HTML_IDENTITY, "MIT L09 browser evidence differs")
        check(browser.get("desktop", {}).get("horizontal_overflow") == 0 and browser.get("mobile", {}).get("horizontal_overflow") == 0 and browser.get("mobile", {}).get("uncontained_math_overflow") == 0, "MIT L09 browser reflow evidence differs")
        check(visual.get("result") == "pass" and (visual.get("pdf", {}).get("bytes"), visual.get("pdf", {}).get("sha256")) == PDF_IDENTITY and visual.get("render", {}).get("all_pages_inspected") is True, "MIT L09 visual evidence differs")
        renders = visual.get("render", {}).get("pages", [])
        check(pdf.get("render_identities") == renders and build.get("expected_render_identities") == renders, "MIT L09 render identity sequence differs")
        for item in content.get("files", []):
            path = item.get("path")
            if path:
                check(file_info(path) == (item.get("bytes"), item.get("sha256")), f"MIT L09 content receipt binds stale file {path}")
        rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
        for path in (MIT_CENSUS, MIT_WITNESS, MIT_TARGET):
            check(file_info(path)[1] in rereview, f"MIT L09 rereview does not bind {path}")
        check(bool(re.search(r"P1\s*=\s*0\s*,\s*P2\s*=\s*0\s*,\s*P3\s*=\s*0", rereview)), "MIT L09 rereview severity differs")
    except Exception as exc:
        errors.append(f"reader evidence validation failed: {exc}")

    receipt = {
        "schema": "o015-mit-l09-backend-validation-v1",
        "recorded_at": RECORDED_AT,
        "result": "pass" if not errors else "fail",
        "errors": errors,
        "workflow": WORKFLOW,
        "input": {"jsonl": str(args.input_jsonl), "csv": str(args.input_csv)},
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
            "expected_new_record_count": EXPECTED_NEW_COUNT,
            "new_entity_counts": dict(sorted(Counter(record.get("entity_type") for record in workflow_records).items())),
            "new_id_set_sha256": digest(("\n".join(sorted(expected)) + "\n").encode("utf-8")),
            "segment_ids": [f"d90.mit.ocw-6.253.l09.p{page:03d}" for page in SOURCE_PAGES],
            "formula_surface_ids": [f"surface.mit.l09.formula.p{page:03d}.d{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)],
            "figure_description_surface_ids": [f"surface.mit.l09.figure-description.p{page:03d}.f001" for page in FIGURE_PANELS],
            "example_surface_ids": [f"surface.mit.l09.example.p{page:03d}.i{index:03d}" for page, index in sorted(EXAMPLES)],
            "correction_record_ids": [f"correction.o015-mit-sem-{number:04d}" for number in range(12, 20)],
            "artifact_ids": sorted(ARTIFACTS),
            "qa_event_ids": sorted(QA_IDS),
            "relation_count": len(relations),
            "topology": {"pages": 14, "top_level_items": 41, "nested_items": 17, "display_surfaces": 19, "figure_blocks": 7, "figure_panels": 12, "examples": 2, "corrections": 8},
        },
        "final_backend": {
            "record_count": len(records),
            "entity_counts": dict(sorted(Counter(record.get("entity_type") for record in records).items())),
            "id_set_sha256": id_set(records),
            "record_set_sha256": record_set(records),
            "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
            "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
            "csv_projection_lossless": row_records == records,
            "references_closed": not any("dangling" in error for error in errors),
        },
        "correction_snapshot": {"bytes": LEDGER_IDENTITY[0], "sha256": LEDGER_IDENTITY[1], "event_ids": list(EXPECTED_EVENT_IDS)},
        "reader_bindings": {
            "target": {"path": MIT_TARGET, "bytes": file_info(MIT_TARGET)[0], "sha256": file_info(MIT_TARGET)[1]},
            "html": {"path": MIT_HTML, "bytes": HTML_IDENTITY[0], "sha256": HTML_IDENTITY[1]},
            "pdf": {"path": MIT_READER_PDF, "bytes": PDF_IDENTITY[0], "sha256": PDF_IDENTITY[1]},
            "rereview": {"path": MIT_REREVIEW, "bytes": file_info(MIT_REREVIEW)[0], "sha256": file_info(MIT_REREVIEW)[1]},
        },
        "independent_validation_runs_required": 2,
    }
    write_receipt(args.receipt, receipt)
    print(json.dumps({
        "result": receipt["result"],
        "errors": len(errors),
        "new_records": len(workflow_records),
        "final_records": len(records),
        "jsonl_sha256": digest(jsonl_raw),
        "csv_sha256": digest(csv_raw),
        "receipt": str(args.receipt),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
