#!/usr/bin/env python3
"""Independent read-only validator for the additive MIT L04 backend closure."""

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
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
SCHEMA_PATH = BACKEND / "backend_schema.json"
REPORT_PATH = ROOT / "qa/MIT_L04_BACKEND_VALIDATION.json"
EXTENSION_PATH = ROOT / "qa/extend_backend_mit_l04.py"
WORKFLOW = "o015-mit-l04-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_COUNT = 1495
BASELINE_JSONL = (1_076_672, "61422fc3d0a1dfa3fed57f3710ae0ffbefb48b8b45957c25ed7455d3a9bd05e7")
BASELINE_CSV = (1_293_072, "146f9a251bcd6b7c9938debc5e9b3f8d680cb51b6d6309bc9a85c90269d22f82")
BASELINE_ID_SET = "0bd88fee9666181e30211465d7e4674f9f90022cee68eb02e21d6419279482b5"
BASELINE_RECORD_SET = "8b9fc6f5aafad76c2df350d3142ff05aefeaba97034b5136db080e2ac08e2b1c"

MIT_PDF = "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
MIT_WITNESS = "source/en/mit-04-rise-algorithmic-era-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-04-kebangkitan-era-algoritmik-id.md"
MIT_HTML = "output/html/D90-MIT-04-kebangkitan-era-algoritmik-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-04-kebangkitan-era-algoritmik-id.pdf"
MIT_REPORT = "qa/MIT_L04_VALIDATION.json"
MIT_BROWSER = "qa/MIT_L04_BROWSER_QA.json"
MIT_VISUAL = "qa/MIT_L04_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L04_INDEPENDENT_REREVIEW.md"
MIT_SEGMENT = "d90.mit.ocw-6.253.l04.p015"
MIT_UNIT = "unit.mit.ocw-6.253.l04"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")

L02_ARTIFACTS = {
    "artifact.mit.l04.semantic-witness": (MIT_WITNESS, "rights.o015-mit-semantic-witness"),
    "artifact.mit.l04.target-source": (MIT_TARGET, "rights.o015-mit-id-pilot"),
    "artifact.mit.l04.target-html": (MIT_HTML, "rights.o015-mit-id-pilot"),
    "artifact.mit.l04.target-pdf": (MIT_READER_PDF, "rights.o015-mit-id-pilot"),
    "artifact.mit.l04.builder": ("qa/build_mit_l04.py", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l04.validator": ("qa/validate_mit_l04.py", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l04.validation": (MIT_REPORT, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l04.browser-qa": (MIT_BROWSER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l04.visual-qa": (MIT_VISUAL, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l04.independent-rereview": (MIT_REREVIEW, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l04.css": ("source/id-ID/mit-l02.css", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l04.pdf-preamble": ("source/id-ID/mit-l04-preamble.tex", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l04.pdf-filter": ("source/id-ID/mit-l03-pdf-filter.lua", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l04.before-body": ("source/id-ID/mit-l04-before-body.html", "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l04.after-body": ("source/id-ID/mit-l03-after-body.html", "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-generator-mit-l04": ("qa/extend_backend_mit_l04.py", "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-validator-mit-l04": ("qa/validate_backend_mit_l04.py", "rights.o015-mit-l01-backend-tooling"),
}
L02_QA = {
    f"qa.o015.mit-l04.{name}"
    for name in (
        "source-freeze", "semantic-reconstruction", "topology", "formulas", "build", "html",
        "browser", "pdf", "visual", "accessibility", "math-rereview", "language", "rights", "backend-integration",
    )
}
L02_RELATIONS = {
    "relation.mit.work-contains-l04", "relation.mit.witness-edition-contains-l04",
    "relation.mit.target-edition-contains-l04", "relation.mit.l04.contains-p015",
    "relation.mit.witness-adapts-authority-pdf-l04", "relation.mit.target-translates-witness-l04",
    "relation.mit.html-adapts-target-l04", "relation.mit.pdf-adapts-target-l04",
    "relation.mit.inline-math-depends-on-segment-l04", "relation.mit.browser-qa-depends-on-html-l04",
    "relation.mit.visual-qa-depends-on-pdf-l04", "relation.mit.validation-depends-on-browser-qa-l04",
    "relation.mit.validation-depends-on-visual-qa-l04", "relation.mit.validation-depends-on-rereview-l04",
}
EXPECTED_NEW_IDS = {MIT_UNIT, MIT_SEGMENT, "surface.mit.l04.inline-math-ell-one"} | set(L02_ARTIFACTS) | L02_QA | L02_RELATIONS


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
    return digest("".join(canonical(record) + "\n" for record in sorted(records, key=lambda item: item["id"])).encode("utf-8"))


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().startswith("::: {") and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)]
    if len(starts) != 1:
        raise ValueError(f"{relative} #{anchor}: expected one fenced div, found {len(starts)}")
    start = starts[0]
    depth = 0
    end = -1
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("::: {"):
            depth += 1
        elif stripped == ":::":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end < start:
        raise ValueError(f"{relative} #{anchor}: unclosed fenced div")
    payload = ("\n".join(lines[start : end + 1]) + "\n").encode("utf-8")
    return start + 1, end + 1, len(payload), digest(payload)


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
    check(len(records) == BASELINE_COUNT + len(EXPECTED_NEW_IDS), f"record count {len(records)} differs")
    check(len(ids) == len(set(ids)), "duplicate backend IDs")
    check(len(new_records) == len(EXPECTED_NEW_IDS), "L04 new-record count differs")
    check({record["id"] for record in new_records} == EXPECTED_NEW_IDS, "L04 stable-ID set differs")
    check(len(baseline_records) == BASELINE_COUNT, "protected baseline count differs")
    check(id_set(baseline_records) == BASELINE_ID_SET, "protected baseline ID-set hash differs")
    check(record_set(baseline_records) == BASELINE_RECORD_SET, "protected baseline record-set hash differs")
    check(len(raw_jsonl) > BASELINE_JSONL[0] and len(raw_csv) > BASELINE_CSV[0], "backend did not grow beyond baseline")

    rank = {name: index for index, name in enumerate(schema.get("entity_order", []))}
    check(records == sorted(records, key=lambda record: (rank.get(record.get("entity_type"), 999), record.get("id", ""))), "JSONL order is not deterministic")
    try:
        rows = list(csv.DictReader(io.StringIO(raw_csv.decode("utf-8", errors="strict"))))
        projected = [json.loads(row["record_json"]) for row in rows]
        check(projected == records, "CSV projection does not round-trip")
    except Exception as exc:
        errors.append(f"CSV parse failed: {exc}")

    refs = set(schema.get("reference_fields", []))
    for record in records:
        for field in schema.get("required_common", []) + schema.get("required_by_entity", {}).get(record.get("entity_type"), []):
            check(field in record, f"{record.get('id')}: missing required {field}")
        for field in refs:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for target in values:
                if isinstance(target, str):
                    check(target in by_id, f"{record.get('id')}: unresolved {field} -> {target}")

    segment = by_id.get(MIT_SEGMENT, {})
    try:
        source = fenced_div_slice(MIT_WITNESS, "src-mit-l04-p015")
        target = fenced_div_slice(MIT_TARGET, "d90-mit-l04-p015")
        check((segment.get("source_line_start"), segment.get("source_line_end"), segment.get("source_bytes"), segment.get("source_content_sha256")) == source, "L04 source page slice binding differs")
        check((segment.get("target_line_start"), segment.get("target_line_end"), segment.get("target_bytes"), segment.get("target_content_sha256")) == target, "L04 target page slice binding differs")
    except Exception as exc:
        errors.append(f"L04 page slice check failed: {exc}")
    check(segment.get("source_pdf_page") == 15 and segment.get("source_pdf_sha256") == SOURCE_PDF_IDENTITY[1], "L04 source PDF binding differs")
    check(segment.get("source_item_count") == 6 and segment.get("nested_source_bullet_count") == 12, "L04 topology counts differ")
    check(segment.get("source_figure_count") == 0 and segment.get("source_display_count") == 0 and segment.get("inline_math_surface_count") == 1, "L04 surface counts differ")

    surface = by_id.get("surface.mit.l04.inline-math-ell-one", {})
    check(surface.get("surface_type") == "inline_math" and surface.get("presence") == "present", "inline math surface differs")
    check(surface.get("related_segment_ids") == [MIT_SEGMENT], "inline math segment relation differs")
    check(surface.get("notation") == "\\ell_1" and surface.get("source_math_nodes") == 1 and surface.get("target_math_nodes") == 1, "inline math identity differs")

    for record_id, (path, rights_id) in L02_ARTIFACTS.items():
        record = by_id.get(record_id)
        check(record is not None, f"missing artifact {record_id}")
        if record is None:
            continue
        try:
            check(file_info(path) == (record.get("bytes"), record.get("sha256")), f"{record_id}: stale artifact bytes")
        except Exception as exc:
            errors.append(f"{record_id}: artifact check failed: {exc}")
        check(record.get("path") == path and record.get("rights_id") == rights_id, f"{record_id}: path/rights binding differs")

    try:
        qa = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
        browser = json.loads((ROOT / MIT_BROWSER).read_text(encoding="utf-8"))
        visual = json.loads((ROOT / MIT_VISUAL).read_text(encoding="utf-8"))
        check(qa.get("result") in {"pass", "pass_with_limitation"} and qa.get("errors") == [], "MIT L04 validation report is not passing")
        check(browser.get("result") in {"pass", "pass_with_limitation"} and browser.get("html", {}).get("sha256") == file_info(MIT_HTML)[1], "browser QA evidence differs")
        check(visual.get("result") == "pass" and visual.get("surface", {}).get("sha256") == file_info(MIT_READER_PDF)[1], "visual QA evidence differs")
    except Exception as exc:
        errors.append(f"QA receipt load failed: {exc}")

    counts = dict(sorted(Counter(record.get("entity_type") for record in new_records).items()))
    receipt = {
        "schema": "o015-mit-l04-backend-validation-v1",
        "recorded_at": "2026-08-23T20:30:00Z",
        "workflow": WORKFLOW,
        "protected_baseline": {"record_count": BASELINE_COUNT, "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]}, "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]}, "id_set_sha256": BASELINE_ID_SET, "record_set_sha256": BASELINE_RECORD_SET},
        "new_record_count": len(new_records),
        "new_entity_counts": counts,
        "new_ids": sorted(EXPECTED_NEW_IDS),
        "new_ids_sha256": digest(("\n".join(sorted(EXPECTED_NEW_IDS)) + "\n").encode("utf-8")),
        "backend": {"record_count": len(records), "jsonl": {"bytes": len(raw_jsonl), "sha256": digest(raw_jsonl)}, "csv": {"bytes": len(raw_csv), "sha256": digest(raw_csv)}},
        "page_segment": {"id": MIT_SEGMENT, "source_pdf_page": 15, "source_items": 6, "nested_bullets": 12, "inline_math_surface": "surface.mit.l04.inline-math-ell-one"},
        "extension_script": {"path": "qa/extend_backend_mit_l04.py", "bytes": file_info("qa/extend_backend_mit_l04.py")[0], "sha256": file_info("qa/extend_backend_mit_l04.py")[1]},
        "validator_script": {"path": "qa/validate_backend_mit_l04.py", "bytes": file_info("qa/validate_backend_mit_l04.py")[0], "sha256": file_info("qa/validate_backend_mit_l04.py")[1]},
        "artifact_bindings": {record_id: {"path": by_id[record_id]["path"], "bytes": by_id[record_id]["bytes"], "sha256": by_id[record_id]["sha256"]} for record_id in sorted(L02_ARTIFACTS) if record_id in by_id},
        "errors": errors,
        "result": "pass" if not errors else "fail",
    }
    REPORT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
