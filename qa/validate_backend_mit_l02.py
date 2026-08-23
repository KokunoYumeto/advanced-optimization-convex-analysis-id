#!/usr/bin/env python3
"""Independent read-only validator for the additive MIT L02 backend closure.

The validator deliberately does not import the extension generator.  It
reconstructs the protected baseline identity, expected L02 stable-ID set,
lossless CSV projection, reference closure, page-addressed segment hashes,
and every L02 artifact binding.  It writes one small sanitized receipt at
``qa/MIT_L02_BACKEND_VALIDATION.json`` and exits non-zero on any discrepancy.
"""

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
REPORT_PATH = ROOT / "qa/MIT_L02_BACKEND_VALIDATION.json"
EXTENSION_PATH = ROOT / "qa/extend_backend_mit_l02.py"
WORKFLOW = "o015-mit-l02-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_COUNT = 1430
BASELINE_JSONL = (1_036_556, "ebf44ca94323584e40b548ce36da560899e39a1e76ed2c993a0786b4ee7c4a2b")
BASELINE_CSV = (1_244_072, "bc73abb3457cacc10423c1785a0db70a9007fdef8ac0a2be1de48d25d389fdf5")
BASELINE_ID_SET = "783c884b58e5f6a78616cd435f2fbda7bca01dd3ad499e762203774e871ca518"
BASELINE_RECORD_SET = "d55dd39b0cbce33d7c5933bf7bec986661259663f148ff7687ebc65caa018d7c"

MIT_PDF = (
    "authority/mit-ocw-6.253/course-archive/static_resources/"
    "6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
)
MIT_WITNESS = "source/en/mit-02-duality-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-02-dualitas-dan-perilaku-pengecualian-id.md"
MIT_HTML = "output/html/D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.html"
MIT_PDF_READER = "output/pdf/D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.pdf"
MIT_REPORT = "qa/MIT_L02_VALIDATION.json"
MIT_BROWSER = "qa/MIT_L02_BROWSER_QA.json"
MIT_REREVIEW = "qa/MIT_L02_INDEPENDENT_REREVIEW.md"
MIT_CENSUS = "00_control/MIT_L02_BOUNDARY_CENSUS.md"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
PAGES = list(range(6, 14))
ITEM_COUNTS = {6: 3, 7: 3, 8: 2, 9: 1, 10: 4, 11: 2, 12: 0, 13: 4}
NESTED_COUNTS = {6: 0, 7: 0, 8: 0, 9: 2, 10: 4, 11: 0, 12: 0, 13: 1}
FIGURE_PAGES = {6, 7, 8, 9, 11, 12, 13}

L02_UNIT = "unit.mit.ocw-6.253.l02"
L02_SEGMENTS = {f"d90.mit.ocw-6.253.l02.p{page:03d}" for page in PAGES}
L02_SURFACES = {
    "surface.mit.l02.exercise-inventory",
    "surface.mit.l02.hint-inventory",
    "surface.mit.l02.answer-inventory",
    "surface.mit.l02.solution-inventory",
    "surface.mit.l02.semantic-html",
    "surface.mit.l02.reflowed-pdf",
    "surface.mit.l02.figure-inventory",
}
L02_ARTIFACTS = {
    "artifact.mit.l02.boundary-census",
    "artifact.mit.l02.semantic-witness",
    "artifact.mit.l02.target-source",
    "artifact.mit.l02.target-html",
    "artifact.mit.l02.target-pdf",
    "artifact.mit.l02.builder",
    "artifact.mit.l02.css",
    "artifact.mit.l02.pdf-preamble",
    "artifact.mit.l02.pdf-filter",
    "artifact.mit.l02.before-body",
    "artifact.mit.l02.after-body",
    "artifact.mit.l02.validator",
    "artifact.mit.l02.validation",
    "artifact.mit.l02.browser-qa",
    "artifact.mit.l02.independent-rereview",
    "artifact.o015.backend-generator-mit-l02",
    "artifact.o015.backend-validator-mit-l02",
}
L02_QA = {
    f"qa.o015.mit-l02.{name}"
    for name in (
        "source-freeze",
        "semantic-reconstruction",
        "topology",
        "formulas",
        "build",
        "html",
        "browser",
        "pdf",
        "accessibility",
        "math-rereview",
        "language",
        "rights",
        "backend-integration",
    )
}
L02_RELATIONS = {
    "relation.mit.work-contains-l02",
    "relation.mit.witness-edition-contains-l02",
    "relation.mit.target-edition-contains-l02",
    "relation.mit.witness-adapts-authority-pdf-l02",
    "relation.mit.target-translates-witness-l02",
    "relation.mit.html-adapts-target-l02",
    "relation.mit.pdf-adapts-target-l02",
    "relation.mit.browser-qa-depends-on-html-l02",
    "relation.mit.validation-depends-on-browser-qa-l02",
    "relation.mit.validation-depends-on-rereview-l02",
    "relation.mit.validation-depends-on-boundary-l02",
    *(f"relation.mit.l02.contains-p{page:03d}" for page in PAGES),
}
EXPECTED_NEW_IDS = {L02_UNIT} | L02_SEGMENTS | L02_SURFACES | L02_ARTIFACTS | L02_QA | L02_RELATIONS


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
        i for i, line in enumerate(lines)
        if line.strip().startswith("::: {") and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
    ]
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
        incoming_jsonl = JSONL_PATH.read_bytes()
        incoming_csv = CSV_PATH.read_bytes()
        records = [json.loads(line) for line in incoming_jsonl.decode("utf-8").splitlines() if line]
    except Exception as exc:  # pragma: no cover - receipt should explain setup failures
        errors.append(f"backend load failed: {exc}")
        records = []
        schema = {}
        incoming_jsonl = b""
        incoming_csv = b""

    ids = [record.get("id") for record in records]
    by_id = {record.get("id"): record for record in records}
    new_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    baseline_records = [record for record in records if record.get("responsible_workflow") != WORKFLOW]

    check(len(records) == BASELINE_COUNT + len(EXPECTED_NEW_IDS), f"record count {len(records)} != {BASELINE_COUNT + len(EXPECTED_NEW_IDS)}")
    check(len(ids) == len(set(ids)), "duplicate record IDs")
    check(len(new_records) == len(EXPECTED_NEW_IDS), f"L02 record count {len(new_records)} != {len(EXPECTED_NEW_IDS)}")
    check({record["id"] for record in new_records} == EXPECTED_NEW_IDS, "L02 stable-ID set differs")
    check(len(baseline_records) == BASELINE_COUNT, "protected baseline record count differs")
    check(id_set(baseline_records) == BASELINE_ID_SET, "protected baseline ID-set hash differs")
    check(record_set(baseline_records) == BASELINE_RECORD_SET, "protected baseline record-set hash differs")

    check(len(incoming_jsonl) > BASELINE_JSONL[0], "JSONL did not grow beyond protected baseline")
    check(len(incoming_csv) > BASELINE_CSV[0], "CSV did not grow beyond protected baseline")
    entity_rank = {name: i for i, name in enumerate(schema.get("entity_order", []))}
    expected_order = sorted(records, key=lambda record: (entity_rank.get(record.get("entity_type"), 999), record.get("id", "")))
    check(records == expected_order, "JSONL deterministic entity/id order differs")

    # CSV must be a lossless, deterministic projection of JSONL.
    try:
        rows = list(csv.DictReader(io.StringIO(incoming_csv.decode("utf-8", errors="strict"))))
        projected = []
        for row in rows:
            check(row.get("schema") == RECORD_SCHEMA and row.get("schema_version") == SCHEMA_VERSION, f"CSV schema row differs: {row.get('id')}")
            projected.append(json.loads(row["record_json"]))
        check(projected == records, "CSV record_json projection does not round-trip")
    except Exception as exc:
        errors.append(f"CSV parse failed: {exc}")

    # Generic required-field and reference closure checks.
    references = set(schema.get("reference_fields", []))
    for record in records:
        entity_type = record.get("entity_type")
        for field in schema.get("required_common", []) + schema.get("required_by_entity", {}).get(entity_type, []):
            check(field in record, f"{record.get('id')}: missing required {field}")
        for field in references:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for target in values:
                if isinstance(target, str):
                    check(target in by_id, f"{record.get('id')}: unresolved {field} -> {target}")

    # Segment identities are independently recomputed from the page-addressed
    # witness/target fences, not merely copied from the extension script.
    for page in PAGES:
        segment_id = f"d90.mit.ocw-6.253.l02.p{page:03d}"
        segment = by_id.get(segment_id, {})
        try:
            source = fenced_div_slice(MIT_WITNESS, f"src-mit-l02-p{page:03d}")
            target = fenced_div_slice(MIT_TARGET, f"d90-mit-l02-p{page:03d}")
            check((segment.get("source_line_start"), segment.get("source_line_end"), segment.get("source_bytes"), segment.get("source_content_sha256")) == source, f"{segment_id}: source fence binding differs")
            check((segment.get("target_line_start"), segment.get("target_line_end"), segment.get("target_bytes"), segment.get("target_content_sha256")) == target, f"{segment_id}: target fence binding differs")
        except Exception as exc:
            errors.append(f"{segment_id}: fence check failed: {exc}")
        check(segment.get("source_pdf_page") == page, f"{segment_id}: source PDF page differs")
        check(segment.get("source_pdf_sha256") == SOURCE_PDF_IDENTITY[1], f"{segment_id}: source PDF hash differs")
        check(segment.get("source_item_count") == ITEM_COUNTS[page], f"{segment_id}: item count differs")
        check(segment.get("nested_source_bullet_count") == NESTED_COUNTS[page], f"{segment_id}: nested-list count differs")
        check(segment.get("source_figure_count") == (1 if page in FIGURE_PAGES else 0), f"{segment_id}: figure count differs")
        check(segment.get("source_display_count") == (1 if page == 9 else 0), f"{segment_id}: display count differs")

    # Every L02 artifact record must bind current bytes; the target validator
    # and browser report must also bind the canonical reader files.
    for record_id in L02_ARTIFACTS:
        artifact = by_id.get(record_id)
        check(artifact is not None, f"missing artifact record {record_id}")
        if artifact is None:
            continue
        path = artifact.get("path")
        try:
            check(file_info(path) == (artifact.get("bytes"), artifact.get("sha256")), f"{record_id}: stale artifact bytes")
        except Exception as exc:
            errors.append(f"{record_id}: artifact path check failed: {exc}")
    try:
        report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
        browser = json.loads((ROOT / MIT_BROWSER).read_text(encoding="utf-8"))
        check(report.get("result") == "pass" and report.get("errors") == [], "L02 validation report is not passing")
        check(browser.get("result") == "pass" and browser.get("console_warnings_or_errors") == [], "L02 browser QA is not passing")
        check(browser.get("surface", {}).get("sha256") == file_info(MIT_HTML)[1], "browser QA does not bind canonical HTML")
        for path, key in ((MIT_WITNESS, "witness"), (MIT_TARGET, "target"), (MIT_HTML, "html"), (MIT_PDF_READER, "pdf"), (MIT_BROWSER, "browser_qa"), (MIT_REREVIEW, "rereview")):
            check(report.get("files", {}).get(key, {}).get("sha256") == file_info(path)[1], f"L02 validation report stale for {path}")
    except Exception as exc:
        errors.append(f"L02 QA receipt load failed: {exc}")

    new_entity_counts = dict(sorted(Counter(record.get("entity_type") for record in new_records).items()))
    report_out = {
        "schema": "o015-mit-l02-backend-validation-v1",
        "recorded_at": "2026-08-23T19:05:00Z",
        "workflow": WORKFLOW,
        "protected_baseline": {"record_count": BASELINE_COUNT, "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]}, "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]}, "id_set_sha256": BASELINE_ID_SET, "record_set_sha256": BASELINE_RECORD_SET},
        "new_record_count": len(new_records),
        "new_entity_counts": new_entity_counts,
        "new_ids": sorted(EXPECTED_NEW_IDS),
        "new_ids_sha256": digest(("\n".join(sorted(EXPECTED_NEW_IDS)) + "\n").encode("utf-8")),
        "backend": {"record_count": len(records), "jsonl": {"bytes": len(incoming_jsonl), "sha256": digest(incoming_jsonl)}, "csv": {"bytes": len(incoming_csv), "sha256": digest(incoming_csv)}},
        "segment_count": len(L02_SEGMENTS),
        "source_pdf": {"path": MIT_PDF, "bytes": file_info(MIT_PDF)[0], "sha256": file_info(MIT_PDF)[1], "pages": PAGES},
        "extension_script": {"path": "qa/extend_backend_mit_l02.py", "bytes": file_info("qa/extend_backend_mit_l02.py")[0], "sha256": file_info("qa/extend_backend_mit_l02.py")[1]},
        "validator_script": {"path": "qa/validate_backend_mit_l02.py", "bytes": file_info("qa/validate_backend_mit_l02.py")[0], "sha256": file_info("qa/validate_backend_mit_l02.py")[1]},
        "artifact_bindings": {
            record_id: {"path": by_id[record_id]["path"], "bytes": by_id[record_id]["bytes"], "sha256": by_id[record_id]["sha256"]}
            for record_id in sorted(L02_ARTIFACTS)
        },
        "errors": errors,
        "result": "pass" if not errors else "fail",
    }
    REPORT_PATH.write_text(json.dumps(report_out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
