#!/usr/bin/env python3
"""Independently validate the additive MIT Lecture 6 backend admission."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
RECEIPT_PATH = ROOT / "qa/MIT_L10_BACKEND_VALIDATION.json"
GENERATOR = ROOT / "qa/extend_backend_mit_l10.py"

WORKFLOW = "o015-mit-l10-backend-v1"
UNIT_ID = "unit.mit.ocw-6.253.l10"
SOURCE_PAGES = list(range(64, 86))
BASELINE_COUNT = 2_099
BASELINE_JSONL = (1_577_079, "b483dfba003cd9fb422055c7836f62dd326575afcfc9b3c0a9a54aa6e1ad7ef8")
BASELINE_CSV = (1_886_451, "297629b3d20bd51bafd50cd5ecd0de70bd397b603a572e45083ca61b247f2574")
BASELINE_ID_SET_SHA256 = "316351a09581ac2bf8640e6d4ca76c8924a013b39aa4e03b074252aca427d209"
BASELINE_ID_ORDER_SHA256 = "0b353161f3a53734566e12f82eeeed09d306d11543b4ac6a060312506cb005da"
BASELINE_RECORD_SET_SHA256 = "4447a2fa4766ceee9c3c87374e38648dfd3e25c6fee30ba23191615700e482ff"
EXPECTED_NEW_COUNT = 225
EXPECTED_ENTITY_COUNTS = Counter({
    "unit": 1, "segment": 22, "learning_surface": 60, "correction": 11,
    "artifact": 19, "qa_event": 17, "relation": 95,
})

PAGE_ITEMS = {
    64: 4, 65: 2, 66: 2, 67: 3, 68: 6, 69: 3, 70: 3, 71: 6,
    72: 4, 73: 5, 74: 2, 75: 3, 76: 4, 77: 2, 78: 3, 79: 3,
    80: 3, 81: 3, 82: 2, 83: 2, 84: 2, 85: 3,
}
PAGE_NESTED = {
    64: 2, 65: 0, 66: 2, 67: 0, 68: 1, 69: 0, 70: 0, 71: 3,
    72: 0, 73: 0, 74: 2, 75: 2, 76: 0, 77: 0, 78: 2, 79: 0,
    80: 0, 81: 0, 82: 0, 83: 0, 84: 0, 85: 0,
}
PAGE_DISPLAYS = {
    64: 0, 65: 2, 66: 1, 67: 1, 68: 2, 69: 2, 70: 1, 71: 0,
    72: 3, 73: 0, 74: 0, 75: 5, 76: 2, 77: 4, 78: 2, 79: 1,
    80: 6, 81: 2, 82: 1, 83: 2, 84: 3, 85: 1,
}
FIGURES = {
    (65, 1): 1, (66, 1): 1, (67, 1): 1, (69, 1): 2,
    (70, 1): 2, (72, 1): 1, (73, 1): 2, (74, 1): 1,
    (76, 1): 2, (78, 1): 1, (79, 1): 2, (81, 1): 1,
    (82, 1): 2, (82, 2): 2, (83, 1): 1, (85, 1): 2,
}
EXAMPLES = {
    "p069.i002": (69, "i002"),
    "p079.f001.a": (79, "f001"),
    "p079.f001.b": (79, "f001"),
}
CORRECTION_PAGES = {
    "O015-MIT-SEM-0020": [65, 68, 70],
    "O015-MIT-SEM-0021": [67, 78],
    "O015-MIT-SEM-0022": [70, 77],
    "O015-MIT-SEM-0023": [67, 78],
    "O015-MIT-SEM-0024": [71],
    "O015-MIT-SEM-0025": [72],
    "O015-MIT-SEM-0026": [76],
    "O015-MIT-SEM-0027": [78],
    "O015-MIT-SEM-0028": [81],
    "O015-MIT-SEM-0029": [84],
    "O015-MIT-SEM-0030": [68],
}
EXPECTED_EVENT_IDS = tuple(CORRECTION_PAGES)

WITNESS = "source/en/mit-10-lecture-6-closed-intersections-hyperplanes-semantic-witness.md"
TARGET = "source/id-ID/mit-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.md"
LEDGER = "00_control/MIT_L10_CORRECTION_SNAPSHOT.jsonl"
EXPECTED_FILE_IDENTITIES = {
    WITNESS: (43_575, "0dfe2c694fad607cef6c37ea7e84a0da359cedee6dc0bf023010f9c8a647c455"),
    TARGET: (45_994, "be2dd29422f5e14ce26315258e772143335475cc2ee9c0d6bfc25f2ff05c8a53"),
    "output/html/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.html": (169_871, "2c3e0e72e535b181880b4e52cbc112c7d2fc393b8f5636e091ff517ed76f2038"),
    "output/pdf/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.pdf": (133_787, "3b01d57e8e8a7d7887f36cfdc205d1b68d1d007a152bd8e0cd75479628e1abc0"),
    "00_control/MIT_L10_LECTURE_6_BOUNDARY_CENSUS.md": (17_483, "ab8c8ce397df3b57f1ae426687fba2b14d51313c7a6b4596369eae07116fb13e"),
    LEDGER: (7_453, "72a8a2da79ea31e2587e42e5e6f54ec4662a749717d5c9c6119c707beef094ee"),
}


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), digest(data)


def id_set(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def id_order(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(record["id"] for record in records) + "\n").encode("utf-8"))


def record_set(records: list[dict[str, Any]]) -> str:
    payload = "".join(canonical(record) + "\n" for record in sorted(records, key=lambda item: item["id"]))
    return digest(payload.encode("utf-8"))


def strip_jsonl(raw: bytes) -> bytes:
    return b"".join(
        line for line in raw.splitlines(keepends=True)
        if json.loads(line.decode("utf-8")).get("responsible_workflow") != WORKFLOW
    )


def strip_csv(raw: bytes) -> bytes:
    lines = raw.splitlines(keepends=True)
    kept = [lines[0]]
    for line in lines[1:]:
        row = next(csv.reader(io.StringIO(line.decode("utf-8"))))
        if len(row) != 5:
            raise ValueError("CSV row width differs")
        if json.loads(row[4]).get("responsible_workflow") != WORKFLOW:
            kept.append(line)
    return b"".join(kept)


def fenced_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.strip().startswith("::: {") and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
    ]
    if len(starts) != 1:
        raise ValueError(f"expected one #{anchor} in {relative}, found {len(starts)}")
    start = starts[0]
    depth = 0
    for end in range(start, len(lines)):
        stripped = lines[end].strip()
        if stripped.startswith("::: {"):
            depth += 1
        elif stripped == ":::":
            depth -= 1
            if depth == 0:
                payload = ("\n".join(lines[start:end + 1]) + "\n").encode("utf-8")
                return start + 1, end + 1, len(payload), digest(payload)
    raise ValueError(f"unclosed #{anchor} in {relative}")


def expected_ids() -> set[str]:
    result = {UNIT_ID}
    result.update(f"d90.mit.ocw-6.253.l10.p{page:03d}" for page in SOURCE_PAGES)
    result.update(
        f"surface.mit.l10.formula.p{page:03d}.d{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    )
    result.update(
        f"surface.mit.l10.figure-description.p{page:03d}.f{index:03d}"
        for page, index in FIGURES
    )
    result.update(f"surface.mit.l10.example.{suffix}" for suffix in EXAMPLES)
    result.update(f"correction.o015-mit-sem-{number:04d}" for number in range(20, 31))
    result.update({
        "artifact.mit.l10.boundary-census", "artifact.mit.l10.semantic-witness",
        "artifact.mit.l10.target-source", "artifact.mit.l10.target-html",
        "artifact.mit.l10.target-pdf", "artifact.mit.l10.builder",
        "artifact.mit.l10.validator", "artifact.mit.l10.validation",
        "artifact.mit.l10.browser-qa", "artifact.mit.l10.visual-qa",
        "artifact.mit.l10.independent-rereview", "artifact.mit.l10.correction-snapshot",
        "artifact.mit.l10.css", "artifact.mit.l10.pdf-preamble",
        "artifact.mit.l10.pdf-filter", "artifact.mit.l10.before-body",
        "artifact.mit.l10.after-body", "artifact.o015.backend-generator-mit-l10",
        "artifact.o015.backend-validator-mit-l10",
    })
    qa_suffixes = {
        "source-freeze", "semantic-reconstruction", "topology", "formulas", "figures",
        "corrections", "build", "html", "browser", "pdf", "visual",
        "semantic-rereview", "accessibility", "language", "rights",
        "csv-losslessness", "backend-integration",
    }
    result.update(f"qa.o015.mit-l10.{suffix}" for suffix in qa_suffixes)
    core = {
        "work-contains-l10", "witness-edition-contains-l10", "target-edition-contains-l10",
        "l09-precedes-l10", "witness-adapts-authority-pdf-l10",
        "target-translates-witness-l10", "html-adapts-target-l10",
        "pdf-adapts-target-l10", "browser-qa-depends-on-html-l10",
        "visual-qa-depends-on-pdf-l10", "validation-depends-on-browser-qa-l10",
        "validation-depends-on-visual-qa-l10", "rereview-depends-on-target-l10",
    }
    result.update(f"relation.mit.{suffix}" for suffix in core)
    result.update(f"relation.mit.l10-contains-p{page:03d}" for page in SOURCE_PAGES)
    result.update(
        f"relation.mit.l10-formula-p{page:03d}-d{index:03d}-illustrates-segment"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    )
    result.update(
        f"relation.mit.l10-figure-p{page:03d}-f{index:03d}-illustrates-segment"
        for page, index in FIGURES
    )
    result.update(
        f"relation.mit.l10-example-{suffix.replace('.', '-')}-exercises-segment"
        for suffix in EXAMPLES
    )
    return result


def validate_dataset(jsonl_path: Path, csv_path: Path) -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonl_raw = jsonl_path.read_bytes()
    csv_raw = csv_path.read_bytes()
    records = [json.loads(line) for line in jsonl_raw.decode("utf-8", errors="strict").splitlines() if line]
    lines = jsonl_raw.splitlines(keepends=True)
    if len(lines) != len(records) or any(line != (canonical(record) + "\n").encode("utf-8") for line, record in zip(lines, records)):
        raise ValueError("JSONL is not canonical compact UTF-8 with LF terminators")
    if len({record["id"] for record in records}) != len(records):
        raise ValueError("duplicate backend IDs")

    reader = csv.DictReader(io.StringIO(csv_raw.decode("utf-8", errors="strict")))
    expected_columns = ["schema", "schema_version", "entity_type", "id", "record_json"]
    if reader.fieldnames != expected_columns:
        raise ValueError("CSV header differs")
    rows = list(reader)
    if len(rows) != len(records):
        raise ValueError("CSV row count differs")
    for row, record in zip(rows, records):
        if json.loads(row["record_json"]) != record:
            raise ValueError(f"CSV record_json differs for {record['id']}")
        if [row[name] for name in expected_columns[:4]] != [record[name] for name in expected_columns[:4]]:
            raise ValueError(f"CSV identity columns differ for {record['id']}")

    rank = {name: index for index, name in enumerate(schema["entity_order"])}
    if records != sorted(records, key=lambda record: (rank[record["entity_type"]], record["id"])):
        raise ValueError("global entity/id order differs")
    id_pattern = re.compile(schema["id_pattern"])
    all_ids = {record["id"] for record in records}
    for record in records:
        missing = [field for field in schema["required_common"] if field not in record]
        missing.extend(field for field in schema["required_by_entity"].get(record["entity_type"], []) if field not in record)
        if missing:
            raise ValueError(f"{record['id']} lacks required fields {missing}")
        if not id_pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid stable ID {record['id']}")
        if record["entity_type"] not in rank:
            raise ValueError(f"unknown entity type {record['entity_type']}")
        if record["entity_type"] == "relation" and record["relation_type"] not in schema["relation_types"]:
            raise ValueError(f"invalid relation type in {record['id']}")
        if "translation_state" in record and record["translation_state"] not in schema["translation_states"]:
            raise ValueError(f"invalid translation state in {record['id']}")
        for field in schema["reference_fields"]:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")

    baseline_jsonl = strip_jsonl(jsonl_raw)
    baseline_csv = strip_csv(csv_raw)
    if (len(baseline_jsonl), digest(baseline_jsonl)) != BASELINE_JSONL or (len(baseline_csv), digest(baseline_csv)) != BASELINE_CSV:
        raise ValueError("workflow stripping does not recover exact L09 backend bytes")
    baseline = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    new = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    if (
        len(baseline) != BASELINE_COUNT or id_set(baseline) != BASELINE_ID_SET_SHA256
        or id_order(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("protected baseline record bytes/order/set differ")
    if len(new) != EXPECTED_NEW_COUNT or Counter(record["entity_type"] for record in new) != EXPECTED_ENTITY_COUNTS:
        raise ValueError("L10 entity topology differs")
    if {record["id"] for record in new} != expected_ids():
        raise ValueError("L10 stable-ID set differs")

    by_id = {record["id"]: record for record in records}
    unit = by_id[UNIT_ID]
    if (
        unit.get("order") != 10 or unit.get("source_pdf_pages") != SOURCE_PAGES
        or unit.get("next_source_page") != 86 or unit.get("source_item_count") != 70
        or unit.get("nested_source_item_count") != 14 or unit.get("source_display_count") != 41
        or unit.get("source_figure_count") != 16 or unit.get("source_figure_panel_count") != 24
        or unit.get("explicit_example_count") != 3
    ):
        raise ValueError("L10 unit topology differs")
    predecessor = by_id["relation.mit.l09-precedes-l10"]
    if (predecessor["relation_type"], predecessor["source_id"], predecessor["target_id"]) != ("precedes", "unit.mit.ocw-6.253.l09", UNIT_ID):
        raise ValueError("L09-to-L10 predecessor relation differs")

    segments = [record for record in new if record["entity_type"] == "segment"]
    segments.sort(key=lambda record: record["order"])
    for order, page in enumerate(SOURCE_PAGES, start=1):
        record = segments[order - 1]
        anchor = f"d90-mit-l10-p{page:03d}"
        if record["id"] != f"d90.mit.ocw-6.253.l10.p{page:03d}" or record["source_pdf_page"] != page:
            raise ValueError("L10 segment order/page mapping differs")
        source_slice = fenced_slice(WITNESS, anchor)
        target_slice = fenced_slice(TARGET, anchor)
        if tuple(record[name] for name in ("source_line_start", "source_line_end", "source_bytes", "source_content_sha256")) != source_slice:
            raise ValueError(f"source segment locator differs on page {page}")
        if tuple(record[name] for name in ("target_line_start", "target_line_end", "target_bytes", "target_content_sha256")) != target_slice:
            raise ValueError(f"target segment locator differs on page {page}")
        if record["source_item_count"] != PAGE_ITEMS[page] or record["nested_source_item_count"] != PAGE_NESTED[page] or record["source_display_count"] != PAGE_DISPLAYS[page]:
            raise ValueError(f"segment topology differs on page {page}")

    formulas = [record for record in new if record.get("surface_type") == "display_formula"]
    figures = [record for record in new if record.get("surface_type") == "semantic_figure_description"]
    examples = [record for record in new if record.get("surface_type") == "worked_example"]
    if len(formulas) != 41 or len(figures) != 16 or len(examples) != 3 or sum(record["panel_count"] for record in figures) != 24:
        raise ValueError("learning-surface topology differs")
    for record in formulas + figures + examples:
        source_slice = fenced_slice(WITNESS, record["source_anchor"])
        target_slice = fenced_slice(TARGET, record["target_anchor"])
        if tuple(record[name] for name in ("source_line_start", "source_line_end", "source_bytes", "source_content_sha256")) != source_slice:
            raise ValueError(f"source surface locator differs: {record['id']}")
        if tuple(record[name] for name in ("target_line_start", "target_line_end", "target_bytes", "target_content_sha256")) != target_slice:
            raise ValueError(f"target surface locator differs: {record['id']}")

    ledger_lines = (ROOT / LEDGER).read_bytes().splitlines(keepends=True)
    ledger_events = [json.loads(line.decode("utf-8")) for line in ledger_lines]
    if tuple(event["event_id"] for event in ledger_events) != EXPECTED_EVENT_IDS:
        raise ValueError("correction snapshot ID sequence differs")
    corrections = [record for record in new if record["entity_type"] == "correction"]
    correction_by_event = {record["source_event_id"]: record for record in corrections}
    for line_number, (raw_line, event) in enumerate(zip(ledger_lines, ledger_events), start=1):
        record = correction_by_event[event["event_id"]]
        expected_segments = [f"d90.mit.ocw-6.253.l10.p{page:03d}" for page in CORRECTION_PAGES[event["event_id"]]]
        if record["affected_segment_ids"] != expected_segments:
            raise ValueError(f"affected correction segments differ: {event['event_id']}")
        if record["source_issue"] != event["source_issue"] or record["target_action"] != event["target_action"]:
            raise ValueError(f"correction evidence differs: {event['event_id']}")
        if record["raw_line_start"] != line_number or record["raw_line_bytes"] != len(raw_line) or record["raw_line_sha256"] != digest(raw_line):
            raise ValueError(f"correction raw-line binding differs: {event['event_id']}")

    artifacts = [record for record in new if record["entity_type"] == "artifact"]
    for record in artifacts:
        if file_info(record["path"]) != (record["bytes"], record["sha256"]):
            raise ValueError(f"artifact binds stale bytes: {record['id']}")
    for relative, expected in EXPECTED_FILE_IDENTITIES.items():
        if file_info(relative) != expected:
            raise ValueError(f"final source/artifact identity differs: {relative}")

    return {
        "records": records, "new": new,
        "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
        "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new).items())),
        "new_id_set_sha256": id_set(new),
        "final_id_set_sha256": id_set(records),
        "final_record_set_sha256": record_set(records),
    }


def deterministic_regeneration(jsonl_path: Path, csv_path: Path) -> list[dict[str, Any]]:
    identities: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="mit-l10-backend-validation-") as temporary:
        root = Path(temporary)
        for run in (1, 2):
            output_dir = root / f"run-{run}"
            command = [
                sys.executable, str(GENERATOR), "--input-jsonl", str(jsonl_path),
                "--input-csv", str(csv_path), "--output-dir", str(output_dir),
            ]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            if completed.returncode != 0:
                raise ValueError(f"deterministic regeneration run {run} failed: {completed.stderr or completed.stdout}")
            entry = {
                "run": run,
                "jsonl": {"bytes": (output_dir / "records.jsonl").stat().st_size, "sha256": digest((output_dir / "records.jsonl").read_bytes())},
                "csv": {"bytes": (output_dir / "records.csv").stat().st_size, "sha256": digest((output_dir / "records.csv").read_bytes())},
            }
            identities.append(entry)
    if identities[0]["jsonl"] != identities[1]["jsonl"] or identities[0]["csv"] != identities[1]["csv"]:
        raise ValueError("two deterministic regeneration runs differ")
    if identities[0]["jsonl"] != {"bytes": jsonl_path.stat().st_size, "sha256": digest(jsonl_path.read_bytes())}:
        raise ValueError("regenerated JSONL differs from canonical")
    if identities[0]["csv"] != {"bytes": csv_path.stat().st_size, "sha256": digest(csv_path.read_bytes())}:
        raise ValueError("regenerated CSV differs from canonical")
    return identities


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}.", suffix=".stage", dir=path.parent, delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        staged = Path(handle.name)
    try:
        if staged.read_bytes() != payload:
            raise ValueError("validation receipt staged readback differs")
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, default=JSONL_PATH)
    parser.add_argument("--input-csv", type=Path, default=CSV_PATH)
    parser.add_argument("--receipt", type=Path, default=RECEIPT_PATH)
    parser.add_argument("--skip-regeneration", action="store_true", help="skip the two-run regeneration proof")
    args = parser.parse_args()

    validated = validate_dataset(args.input_jsonl, args.input_csv)
    regenerations = [] if args.skip_regeneration else deterministic_regeneration(args.input_jsonl, args.input_csv)
    receipt = {
        "schema": "o015-mit-l10-backend-validation-v1",
        "validated_at": "2026-08-24T15:00:00Z",
        "result": "pass", "errors": [], "workflow": WORKFLOW,
        "commands": {
            "admission": "python qa/extend_backend_mit_l10.py --write-canonical",
            "validation": "python qa/validate_backend_mit_l10.py",
            "regeneration_template": "python qa/extend_backend_mit_l10.py --input-jsonl <jsonl> --input-csv <csv> --output-dir <dir>",
        },
        "schema_constraint": {
            "schema_changed": False,
            "precedes_relation_supported": True,
            "note": "The existing metadata schema admits an additive relation record; global entity/id sorting means the old whole file is not a literal prefix, so stability is proved by exact workflow stripping and ordered-record recovery.",
        },
        "protected_baseline": {
            "records": BASELINE_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]},
            "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "id_order_sha256": BASELINE_ID_ORDER_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "record_bytes_and_relative_order_stable": True,
        },
        "admission": {
            "new_records": len(validated["new"]),
            "new_entity_counts": validated["new_entity_counts"],
            "new_id_set_sha256": validated["new_id_set_sha256"],
            "final_records": len(validated["records"]),
            "final_id_set_sha256": validated["final_id_set_sha256"],
            "final_record_set_sha256": validated["final_record_set_sha256"],
            "jsonl": validated["jsonl"], "csv": validated["csv"],
        },
        "topology": {
            "unit_id": UNIT_ID, "source_pages": SOURCE_PAGES,
            "segments": 22, "top_level_items": 70, "nested_items": 14,
            "display_surfaces": 41, "figure_blocks": 16, "figure_panels": 24,
            "worked_examples": 3, "corrections": 11,
            "correction_event_ids": list(EXPECTED_EVENT_IDS),
            "predecessor_relation": "relation.mit.l09-precedes-l10",
        },
        "deterministic_regeneration": {
            "runs_required": 2, "runs_completed": len(regenerations),
            "canonical_match": not args.skip_regeneration,
            "identities": regenerations,
        },
    }
    write_receipt(args.receipt, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
