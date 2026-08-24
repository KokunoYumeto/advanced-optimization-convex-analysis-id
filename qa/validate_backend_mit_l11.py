#!/usr/bin/env python3
"""Independently validate the additive MIT Lecture 7 backend admission."""

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
RECEIPT_PATH = ROOT / "qa/MIT_L11_BACKEND_VALIDATION.json"
GENERATOR = ROOT / "qa/extend_backend_mit_l11.py"

WORKFLOW = "o015-mit-l11-backend-v1"
UNIT_ID = "unit.mit.ocw-6.253.l11"
SOURCE_PAGES = list(range(86, 98))
BASELINE_COUNT = 2_324
BASELINE_JSONL = (1_797_378, "d8694c14afa0933132504c32ea6e2e5862606f913d4b6626bffd35b2bfbee75c")
BASELINE_CSV = (2_144_290, "fb9c84063bf976ddf5e2e15f435617c1cca346eebfd08051d9927a34ffcba367")
BASELINE_ID_SET_SHA256 = "47e46b474fa854ecfc4adbc658c0fa1d6e449f4c6aefa2e1284c1f9807d9c108"
BASELINE_ID_ORDER_SHA256 = "d8dd895a08136ab98001076b59de2312881b6610dc3f50b7cceb4368dc940de2"
BASELINE_RECORD_SET_SHA256 = "a7c2de2ad5f362e40b026d905ce90fc8117095ed40c2a1f12a0a36767a698675"
EXPECTED_NEW_COUNT = 148
EXPECTED_ENTITY_COUNTS = Counter({
    "unit": 1, "segment": 12, "learning_surface": 32, "correction": 10,
    "artifact": 19, "qa_event": 17, "relation": 57,
})

PAGE_ITEMS = {86: 6, 87: 3, 88: 3, 89: 4, 90: 4, 91: 2,
              92: 1, 93: 5, 94: 1, 95: 1, 96: 3, 97: 3}
PAGE_NESTED = {86: 1, 87: 0, 88: 1, 89: 0, 90: 3, 91: 0,
               92: 1, 93: 0, 94: 0, 95: 0, 96: 0, 97: 2}
PAGE_DISPLAYS = {86: 0, 87: 1, 88: 2, 89: 0, 90: 1, 91: 2,
                 92: 1, 93: 3, 94: 2, 95: 4, 96: 1, 97: 4}
FIGURES = {
    (87, 1): 3, (88, 1): 2, (89, 1): 2, (91, 1): 1,
    (92, 1): 6, (94, 1): 1, (96, 1): 1,
}
EXAMPLES = {
    "p092.f001.a": (92, "f001"),
    "p092.f001.b": (92, "f001"),
    "p092.f001.c": (92, "f001"),
    "p097": (97, None),
}
WORKED_EXAMPLE_SUFFIXES = tuple(suffix for suffix in EXAMPLES if suffix != "p097")
COUNTEREXAMPLE_SUFFIXES = ("p097",)
CORRECTION_PAGES = {
    "O015-MIT-SEM-0034": [88],
    "O015-MIT-SEM-0035": [89],
    "O015-MIT-SEM-0036": [90],
    "O015-MIT-SEM-0037": [91],
    "O015-MIT-SEM-0040": [91, 95],
    "O015-MIT-SEM-0031": [92],
    "O015-MIT-SEM-0038": [93],
    "O015-MIT-SEM-0039": [94],
    "O015-MIT-SEM-0032": [96],
    "O015-MIT-SEM-0033": [97],
}
EXPECTED_EVENT_IDS = tuple(CORRECTION_PAGES)

WITNESS = "source/en/mit-11-lecture-7-separation-conjugacy-semantic-witness.md"
TARGET = "source/id-ID/mit-11-kuliah-7-pemisahan-dan-konjugasi-id.md"
LEDGER = "00_control/MIT_L11_CORRECTION_SNAPSHOT.jsonl"
EXPECTED_FILE_IDENTITIES = {
    WITNESS: (23_801, "625efb8801d24c270d2bf851bf1c7fb27cb307146742d7cbddc00b5cb5873c8c"),
    TARGET: (25_023, "f908901609e1a1e6091734b55ba63b980f491dd5a5e4e813621816cbceb1c32b"),
    "output/html/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.html": (96_216, "19dd1f9aeb65e951089a4501fefa65761448f86f21ee7024ccfde9a71e5b988d"),
    "output/pdf/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.pdf": (89_771, "82d39fa34f8e743204ba88b3b91f50d4a549bb7b0b79e529ed0bec1a51f16bc8"),
    "00_control/MIT_L11_LECTURE_7_BOUNDARY_CENSUS.md": (5_840, "6586e3feb4463da884027c778a70c0f066b48d2948c38d1ba9a80ebde98c6f6a"),
    LEDGER: (15_532, "8acc411765e4d5e29f9e89447c26f2b37f00110d43ac2b0043c0762ed070a016"),
}

PAGE_FINGERPRINTS = {
    86: (258, "5bb20e6003c022244d8baeae9365ca1e85571b9021b7ebbca76bfb0068ac4288", 21720, "3480b3e1a2f9ea11078d7ffd2f1ccf2191bfb27d6d841a69f83b1148db65621b"),
    87: (934, "6d34b9c20adbcab3d9b94f51255e380495c884082496d49333063ffa56b0d7a6", 55190, "53d6d945b1e3af1eeb2b5df192c6b704ae9e245af3ff38fba06275bd44ae39c2"),
    88: (918, "2f2b8d01a7f09944b217e000a71b24dd0b77258159ef40a5f697dbd5eaa16fe4", 56877, "b1a6de188dc858109ba12085ede619102f0d614c6d4d8c7e81394a3efd90673c"),
    89: (980, "7a386ae891bcf77999b700d0561b5d9b05b61ddc2742c5aeeaf6ec6a7d3597ff", 53769, "3a5e327f3168ba8bd85897d1dc7f039e210dda04e2c8d4b5eb9968779a7c41f9"),
    90: (1148, "f998269d35b74761acae48995eaf7e10c461e1b7d030105a3c3fea2a8465d7b1", 63453, "9392b6c8521fa7960f5e348f8c6bbd37aa58006da6a61a7e0cf698430dc5de68"),
    91: (871, "21fec334f9e91b1d6b25fe29c80078d1c650ca0dbb05e6696e2065b8b101f70e", 53802, "299ffc0691979d1824087c34a65262f07f9db9263e6a254e19af0bcc90f77363"),
    92: (1150, "f670d867bbc0bcf5f2fb85148b6aef06f5d32961c8ab1985d392e2d59a006f47", 28991, "4a2bbf0954ab94323206933be26df53658bad4a5ec450bea4a33d54f261622d5"),
    93: (740, "7abcde78433beca5672e4b117c096e3a69cd8e9a4f0d37705b6c3f380dd83bca", 40704, "fdd9898e0004ab7d56a0269594f11431210755b03e1cdec7caf38f449f100d18"),
    94: (1185, "e09d900a215c55ae6f3b96f1b66d312c0b73fc372df5908cbaf6ab0cc09701c4", 46386, "f878f160f7ffd7c785717e9ae1b0a72a2d44b5253bee4b9111b2bda3c589a8df"),
    95: (841, "77d25710689b28c92637366a852b0adc2a9dd1cbaefd60675961a4f3cbecfa11", 41463, "5822f46c0b24d0e95027d2801ed1f113d49e38c7a7061dbc00b6833648822fef"),
    96: (1370, "d9768a6d5c70120083db44722b2430942a6bfcded41baa053bd58dbc0cb59f0e", 63569, "133117e2352bf96a9c27f70860ecf2469f892e39a70caa50bbda7518c2c0831d"),
    97: (539, "d91b7761241b77874e9a3b2a85b8e702a068a0583b70946f52ad64089ff53c1f", 24306, "0c93aa07834281be7c97375459816817a479cf21c1a6a8a6688428057fb9cffb"),
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
    result.update(f"d90.mit.ocw-6.253.l11.p{page:03d}" for page in SOURCE_PAGES)
    result.update(
        f"surface.mit.l11.formula.p{page:03d}.d{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    )
    result.update(
        f"surface.mit.l11.figure-description.p{page:03d}.f{index:03d}"
        for page, index in FIGURES
    )
    result.update(f"surface.mit.l11.example.{suffix}" for suffix in EXAMPLES)
    result.update(f"correction.{event_id.lower()}" for event_id in EXPECTED_EVENT_IDS)
    result.update({
        "artifact.mit.l11.boundary-census", "artifact.mit.l11.semantic-witness",
        "artifact.mit.l11.target-source", "artifact.mit.l11.target-html",
        "artifact.mit.l11.target-pdf", "artifact.mit.l11.builder",
        "artifact.mit.l11.validator", "artifact.mit.l11.validation",
        "artifact.mit.l11.browser-qa", "artifact.mit.l11.visual-qa",
        "artifact.mit.l11.independent-rereview", "artifact.mit.l11.correction-snapshot",
        "artifact.mit.l11.css", "artifact.mit.l11.pdf-preamble",
        "artifact.mit.l11.pdf-filter", "artifact.mit.l11.before-body",
        "artifact.mit.l11.after-body", "artifact.o015.backend-generator-mit-l11",
        "artifact.o015.backend-validator-mit-l11",
    })
    qa_suffixes = {
        "source-freeze", "semantic-reconstruction", "topology", "formulas", "figures",
        "corrections", "build", "html", "browser", "pdf", "visual",
        "semantic-rereview", "accessibility", "language", "rights",
        "csv-losslessness", "backend-integration",
    }
    result.update(f"qa.o015.mit-l11.{suffix}" for suffix in qa_suffixes)
    core = {
        "work-contains-l11", "witness-edition-contains-l11", "target-edition-contains-l11",
        "l10-precedes-l11", "witness-adapts-authority-pdf-l11",
        "target-translates-witness-l11", "html-adapts-target-l11",
        "pdf-adapts-target-l11", "browser-qa-depends-on-html-l11",
        "visual-qa-depends-on-pdf-l11", "validation-depends-on-browser-qa-l11",
        "validation-depends-on-visual-qa-l11", "rereview-depends-on-target-l11",
    }
    result.update(f"relation.mit.{suffix}" for suffix in core)
    result.update(f"relation.mit.l11-contains-p{page:03d}" for page in SOURCE_PAGES)
    result.update(
        f"relation.mit.l11-formula-p{page:03d}-d{index:03d}-illustrates-segment"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    )
    result.update(
        f"relation.mit.l11-figure-p{page:03d}-f{index:03d}-illustrates-segment"
        for page, index in FIGURES
    )
    result.update(
        f"relation.mit.l11-example-{suffix.replace('.', '-')}-exercises-segment"
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
        raise ValueError("workflow stripping does not recover exact L10 backend bytes")
    baseline = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    new = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    if (
        len(baseline) != BASELINE_COUNT or id_set(baseline) != BASELINE_ID_SET_SHA256
        or id_order(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("protected baseline record bytes/order/set differ")
    if len(new) != EXPECTED_NEW_COUNT or Counter(record["entity_type"] for record in new) != EXPECTED_ENTITY_COUNTS:
        raise ValueError("L11 entity topology differs")
    if {record["id"] for record in new} != expected_ids():
        raise ValueError("L11 stable-ID set differs")

    by_id = {record["id"]: record for record in records}
    unit = by_id[UNIT_ID]
    if (
        unit.get("order") != 11 or unit.get("source_pdf_pages") != SOURCE_PAGES
        or unit.get("next_source_page") != 98 or unit.get("source_item_count") != 36
        or unit.get("nested_source_item_count") != 8 or unit.get("source_display_count") != 21
        or unit.get("source_figure_count") != 7 or unit.get("source_figure_panel_count") != 16
        or unit.get("worked_example_count") != 3 or unit.get("counterexample_count") != 1
    ):
        raise ValueError("L11 unit topology differs")
    predecessor = by_id["relation.mit.l10-precedes-l11"]
    if (predecessor["relation_type"], predecessor["source_id"], predecessor["target_id"]) != ("precedes", "unit.mit.ocw-6.253.l10", UNIT_ID):
        raise ValueError("L10-to-L11 predecessor relation differs")

    segments = [record for record in new if record["entity_type"] == "segment"]
    segments.sort(key=lambda record: record["order"])
    for order, page in enumerate(SOURCE_PAGES, start=1):
        record = segments[order - 1]
        anchor = f"d90-mit-l11-p{page:03d}"
        if record["id"] != f"d90.mit.ocw-6.253.l11.p{page:03d}" or record["source_pdf_page"] != page:
            raise ValueError("L11 segment order/page mapping differs")
        source_slice = fenced_slice(WITNESS, anchor)
        target_slice = fenced_slice(TARGET, anchor)
        if tuple(record[name] for name in ("source_line_start", "source_line_end", "source_bytes", "source_content_sha256")) != source_slice:
            raise ValueError(f"source segment locator differs on page {page}")
        if tuple(record[name] for name in ("target_line_start", "target_line_end", "target_bytes", "target_content_sha256")) != target_slice:
            raise ValueError(f"target segment locator differs on page {page}")
        if record["source_item_count"] != PAGE_ITEMS[page] or record["nested_source_item_count"] != PAGE_NESTED[page] or record["source_display_count"] != PAGE_DISPLAYS[page]:
            raise ValueError(f"segment topology differs on page {page}")
        page_fingerprint = tuple(record[name] for name in (
            "source_page_text_bytes", "source_page_text_sha256",
            "source_page_render_bytes", "source_page_render_sha256",
        ))
        if page_fingerprint != PAGE_FINGERPRINTS[page]:
            raise ValueError(f"authority page fingerprint differs on page {page}")
        if record.get("source_pdf_sha256") != "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181":
            raise ValueError(f"authority PDF binding differs on page {page}")

    formulas = [record for record in new if record.get("surface_type") == "display_formula"]
    figures = [record for record in new if record.get("surface_type") == "semantic_figure_description"]
    worked_examples = [record for record in new if record.get("surface_type") == "worked_example"]
    counterexamples = [record for record in new if record.get("surface_type") == "counterexample"]
    examples = worked_examples + counterexamples
    if len(formulas) != 21 or len(figures) != 7 or len(worked_examples) != 3 or len(counterexamples) != 1 or sum(record["panel_count"] for record in figures) != 16:
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
        expected_segments = [f"d90.mit.ocw-6.253.l11.p{page:03d}" for page in CORRECTION_PAGES[event["event_id"]]]
        if record["affected_segment_ids"] != expected_segments:
            raise ValueError(f"affected correction segments differ: {event['event_id']}")
        if (
            record["source_issue"] != event["source_issue"]
            or record["target_action"] != event["target_action"]
            or record.get("project_authorship") != event["project_authorship"]
            or record.get("rights_statement") != event["rights"]
        ):
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
    with tempfile.TemporaryDirectory(prefix="mit-l11-backend-validation-") as temporary:
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
        raise ValueError("regenerated JSONL differs from validated input")
    if identities[0]["csv"] != {"bytes": csv_path.stat().st_size, "sha256": digest(csv_path.read_bytes())}:
        raise ValueError("regenerated CSV differs from validated input")
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

    canonical_path_flags = (
        args.input_jsonl.resolve() == JSONL_PATH.resolve(),
        args.input_csv.resolve() == CSV_PATH.resolve(),
    )
    if canonical_path_flags[0] != canonical_path_flags[1]:
        parser.error("--input-jsonl and --input-csv must both be canonical or both be staged")
    canonical_backend_written = all(canonical_path_flags)

    validated = validate_dataset(args.input_jsonl, args.input_csv)
    regenerations = [] if args.skip_regeneration else deterministic_regeneration(args.input_jsonl, args.input_csv)
    receipt = {
        "schema": "o015-mit-l11-backend-validation-v1",
        "validated_at": "2026-08-24T19:00:00Z",
        "result": "pass", "errors": [], "workflow": WORKFLOW,
        "commands": {
            "staging": "python qa/extend_backend_mit_l11.py --output-dir <dir>",
            "validation_template": "python qa/validate_backend_mit_l11.py --input-jsonl <jsonl> --input-csv <csv> --receipt <receipt>",
            "regeneration_template": "python qa/extend_backend_mit_l11.py --input-jsonl <jsonl> --input-csv <csv> --output-dir <dir>",
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
            "canonical_backend_written": canonical_backend_written,
            "disposition": "validated_canonical_backend" if canonical_backend_written else "validated_staged_projection",
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
            "segments": 12, "semantic_items": 36, "nested_items": 8,
            "display_surfaces": 21, "figure_blocks": 7, "figure_panels": 16,
            "worked_examples": 3, "counterexamples": 1, "corrections": 10,
            "correction_event_ids": list(EXPECTED_EVENT_IDS),
            "predecessor_relation": "relation.mit.l10-precedes-l11",
        },
        "deterministic_regeneration": {
            "runs_required": 2, "runs_completed": len(regenerations),
            "input_dataset_match": not args.skip_regeneration,
            "identities": regenerations,
        },
    }
    write_receipt(args.receipt, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
