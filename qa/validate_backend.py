#!/usr/bin/env python3
"""Validate the deterministic O015 modular backend exports."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
RECORD_SCHEMA = "o015-modular-backend-record"


errors: list[str] = []


def error(message: str) -> None:
    errors.append(message)


def read_utf8_lf(path: Path) -> tuple[bytes, str]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        error(f"cannot read {path}: {exc}")
        return b"", ""
    if data.startswith(b"\xef\xbb\xbf"):
        error(f"UTF-8 BOM is forbidden: {path}")
    if b"\r" in data:
        error(f"non-LF newline found: {path}")
    if data and not data.endswith(b"\n"):
        error(f"missing final newline: {path}")
    try:
        return data, data.decode("utf-8")
    except UnicodeDecodeError as exc:
        error(f"invalid UTF-8 in {path}: {exc}")
        return data, ""


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_path(relative: str) -> Path | None:
    candidate = (ROOT / relative).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        error(f"path escapes lane root: {relative}")
        return None
    return candidate


def normalized_slice(relative: str, start: int, end: int) -> bytes:
    path = local_path(relative)
    if path is None:
        return b""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        error(f"cannot read segment file {relative}: {exc}")
        return b""
    if start < 1 or end < start or end > len(lines):
        error(f"invalid line slice {relative}:{start}-{end}; file has {len(lines)} lines")
        return b""
    return (("\n".join(lines[start - 1 : end])) + "\n").encode("utf-8")


schema_bytes, schema_text = read_utf8_lf(SCHEMA_PATH)
try:
    schema = json.loads(schema_text)
except json.JSONDecodeError as exc:
    error(f"invalid schema JSON: {exc}")
    schema = {}

if schema.get("schema") != "o015-modular-backend-schema":
    error("wrong backend schema name")
schema_version = schema.get("schema_version")
if not isinstance(schema_version, str):
    error("missing schema version")

jsonl_bytes, jsonl_text = read_utf8_lf(JSONL_PATH)
records: list[dict[str, Any]] = []
for line_number, line in enumerate(jsonl_text.splitlines(), start=1):
    if not line:
        error(f"blank JSONL record at line {line_number}")
        continue
    try:
        record = json.loads(line)
    except json.JSONDecodeError as exc:
        error(f"invalid JSONL at line {line_number}: {exc}")
        continue
    if not isinstance(record, dict):
        error(f"JSONL line {line_number} is not an object")
        continue
    if line != canonical_json(record):
        error(f"noncanonical JSON serialization at line {line_number}")
    records.append(record)

entity_order = schema.get("entity_order", [])
entity_rank = {name: index for index, name in enumerate(entity_order)}
expected_order = sorted(
    records,
    key=lambda record: (entity_rank.get(record.get("entity_type"), 10_000), record.get("id", "")),
)
if records != expected_order:
    error("JSONL records are not in deterministic entity/id order")

expected_jsonl = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
if jsonl_bytes != expected_jsonl:
    error("JSONL does not round-trip byte-for-byte")

csv_bytes, csv_text = read_utf8_lf(CSV_PATH)
csv_records: list[dict[str, Any]] = []
try:
    reader = csv.DictReader(io.StringIO(csv_text, newline=""))
    if reader.fieldnames != schema.get("csv_columns"):
        error(f"wrong CSV columns: {reader.fieldnames}")
    for row_number, row in enumerate(reader, start=2):
        try:
            record = json.loads(row.get("record_json", ""))
        except json.JSONDecodeError as exc:
            error(f"invalid record_json at CSV row {row_number}: {exc}")
            continue
        for field in ("schema", "schema_version", "entity_type", "id"):
            if row.get(field) != str(record.get(field, "")):
                error(f"CSV projection mismatch for {field} at row {row_number}")
        csv_records.append(record)
except csv.Error as exc:
    error(f"invalid CSV: {exc}")

if csv_records != records:
    error("CSV lossless projection does not round-trip to JSONL records")

csv_buffer = io.StringIO(newline="")
writer = csv.writer(csv_buffer, lineterminator="\n")
writer.writerow(schema.get("csv_columns", []))
for record in records:
    writer.writerow(
        [
            record.get("schema", ""),
            record.get("schema_version", ""),
            record.get("entity_type", ""),
            record.get("id", ""),
            canonical_json(record),
        ]
    )
expected_csv = csv_buffer.getvalue().encode("utf-8")
if csv_bytes != expected_csv:
    error("CSV is not the deterministic projection of records.jsonl")

id_pattern = re.compile(schema.get("id_pattern", r"$."))
required_common = schema.get("required_common", [])
required_by_entity = schema.get("required_by_entity", {})
ids: dict[str, dict[str, Any]] = {}
for index, record in enumerate(records, start=1):
    record_id = record.get("id")
    entity_type = record.get("entity_type")
    for field in required_common:
        if field not in record:
            error(f"{record_id or index}: missing common field {field}")
    if record.get("schema") != RECORD_SCHEMA:
        error(f"{record_id or index}: wrong record schema")
    if record.get("schema_version") != schema_version:
        error(f"{record_id or index}: wrong schema version")
    if entity_type not in entity_order:
        error(f"{record_id or index}: unknown entity type {entity_type}")
    for field in required_by_entity.get(entity_type, []):
        if field not in record:
            error(f"{record_id or index}: missing {entity_type} field {field}")
    if not isinstance(record_id, str) or not id_pattern.fullmatch(record_id):
        error(f"invalid stable ID: {record_id!r}")
    elif record_id in ids:
        error(f"duplicate stable ID: {record_id}")
    else:
        ids[record_id] = record

reference_fields = set(schema.get("reference_fields", []))
for record in records:
    for field in reference_fields.intersection(record):
        value = record[field]
        references = value if isinstance(value, list) else [value]
        for reference in references:
            if reference is None:
                continue
            if not isinstance(reference, str) or reference not in ids:
                error(f"{record.get('id')}: unresolved {field} reference {reference!r}")

for record in records:
    if record.get("entity_type") == "relation" and record.get("relation_type") not in schema.get("relation_types", []):
        error(f"{record.get('id')}: invalid relation type {record.get('relation_type')}")

for record in records:
    if record.get("entity_type") != "unit":
        continue
    seen: set[str] = set()
    parent_id = record.get("parent_id")
    while parent_id is not None:
        if parent_id in seen:
            error(f"unit hierarchy cycle at {record.get('id')}")
            break
        seen.add(parent_id)
        parent = ids.get(parent_id)
        parent_id = parent.get("parent_id") if parent else None

segments = [record for record in records if record.get("entity_type") == "segment"]
expected_segment_counts = {
    "unit.habring.v1.ch03": 11,
    "unit.habring.v1.ch04": 8,
    "unit.habring.v1.ch05": 8,
}
segments_by_unit: dict[str, list[dict[str, Any]]] = {}
for segment in segments:
    segments_by_unit.setdefault(segment.get("unit_id", ""), []).append(segment)
actual_segment_counts = {
    unit_id: len(unit_segments)
    for unit_id, unit_segments in sorted(segments_by_unit.items())
}
if actual_segment_counts != expected_segment_counts:
    error(
        "wrong segment closure: "
        f"expected {expected_segment_counts}, found {actual_segment_counts}"
    )
for unit_id, unit_segments in segments_by_unit.items():
    unit_segments.sort(key=lambda record: record.get("order", 0))
    segment_orders = [record.get("order") for record in unit_segments]
    expected_orders = list(range(1, len(unit_segments) + 1))
    if segment_orders != expected_orders:
        error(
            f"{unit_id}: segment order is not contiguous "
            f"1..{len(unit_segments)}: {segment_orders}"
        )

# Each admitted unit has the same nine-event evidence topology.  Expected
# results are data-driven because Chapter 3 predates the explicit untagged-PDF
# limitation used by Chapters 4--5.
admitted_unit_closure = {
    "unit.habring.v1.ch03": {
        "qa_prefix": "qa.o015.ch03",
        "accessibility_result": "pass",
        "correction_range": range(1, 19),
    },
    "unit.habring.v1.ch04": {
        "qa_prefix": "qa.o015.ch04",
        "accessibility_result": "pass_with_limitation",
        "correction_range": range(19, 28),
    },
    "unit.habring.v1.ch05": {
        "qa_prefix": "qa.o015.ch05",
        "accessibility_result": "pass_with_limitation",
        "correction_range": range(28, 39),
    },
}
qa_suffixes = {
    "accessibility",
    "build",
    "formula-delta",
    "language",
    "math-rereview",
    "solver",
    "source-freeze",
    "structure",
    "visual",
}
for unit_id, closure in admitted_unit_closure.items():
    prefix = closure["qa_prefix"]
    expected_qa_ids = {f"{prefix}.{suffix}" for suffix in qa_suffixes}
    actual_qa_ids = {
        record["id"]
        for record in records
        if record.get("entity_type") == "qa_event"
        and record.get("unit_id") == unit_id
    }
    if actual_qa_ids != expected_qa_ids:
        error(
            f"{unit_id}: wrong QA event closure: "
            f"expected {sorted(expected_qa_ids)}, found {sorted(actual_qa_ids)}"
        )
    language = ids.get(f"{prefix}.language", {})
    if language.get("status") != "not_recorded" or language.get("result") != "not_recorded":
        error(f"{unit_id}: language review must remain not_recorded")
    accessibility = ids.get(f"{prefix}.accessibility", {})
    if accessibility.get("result") != closure["accessibility_result"]:
        error(
            f"{unit_id}: wrong accessibility result: "
            f"{accessibility.get('result')!r}"
        )
    math_review = ids.get(f"{prefix}.math-rereview", {})
    if math_review.get("result") != "pass":
        error(f"{unit_id}: independent mathematical rereview is not a pass")
    if math_review.get("review_outcome") != {"p1": 0, "p2": 0, "p3": 0}:
        error(f"{unit_id}: mathematical rereview does not prove P1=P2=P3=0")

    expected_correction_ids = {
        f"correction.o015-hab-adv-{number:04d}"
        for number in closure["correction_range"]
    }
    actual_correction_ids = {
        record["id"]
        for record in records
        if record.get("entity_type") == "correction"
        and unit_id in record.get("affected_unit_ids", [])
    }
    if actual_correction_ids != expected_correction_ids:
        error(
            f"{unit_id}: wrong correction closure: "
            f"expected {sorted(expected_correction_ids)}, "
            f"found {sorted(actual_correction_ids)}"
        )

for segment in segments_by_unit.get("unit.habring.v1.ch05", []):
    if segment.get("language_review_state") != "not_recorded":
        error(f"{segment.get('id')}: language review must remain not_recorded")
    if segment.get("mathematical_review_state") != (
        "correction_audited_solver_checked_independent_rereview_passed"
    ):
        error(f"{segment.get('id')}: incomplete mathematical review state")

required_ch05_ids = {
    "artifact.habring.source-ch05",
    "artifact.habring.target-ch05",
    "artifact.habring.target-wrapper-ch05",
    "artifact.habring.structure-report-ch05",
    "artifact.habring.structure-audit-ch05",
    "artifact.habring.solver-results-ch05",
    "artifact.habring.solver-validator-ch05",
    "artifact.habring.build-log-ch05",
    "artifact.habring.target-pdf-ch05",
    "artifact.habring.target-text-ch05",
    "artifact.o015.backend-generator-ch05",
    "rights.o015-habring-ch05-source",
    "rights.o015-habring-id-ch05",
    "rights.o015-proximal-gradient-solver-validation",
    "surface.habring.v1.ch05.prompt01",
    "surface.habring.v1.ch05.prompt02",
    "surface.habring.v1.ch05.prompt03",
    "surface.habring.v1.ch05.hint-inventory",
    "surface.habring.v1.ch05.answer-inventory",
    "surface.habring.v1.ch05.solution-inventory",
}
for required_id in sorted(required_ch05_ids):
    if required_id not in ids:
        error(f"Chapter 5 closure is missing {required_id}")

ch05_pdf = ids.get("artifact.habring.target-pdf-ch05", {})
if ch05_pdf.get("pages") != 15:
    error("Chapter 5 PDF artifact does not record 15 pages")
if ch05_pdf.get("accessibility") != "searchable id-ID PDF; untagged":
    error("Chapter 5 PDF accessibility limitation is not explicit")

translation_states = set(schema.get("translation_states", []))
for segment in segments:
    if segment.get("translation_state") not in translation_states:
        error(f"{segment.get('id')}: invalid translation state")
    for side in ("source", "target"):
        content = normalized_slice(
            segment[f"{side}_path"],
            segment[f"{side}_line_start"],
            segment[f"{side}_line_end"],
        )
        if len(content) != segment.get(f"{side}_bytes"):
            error(f"{segment.get('id')}: {side} slice byte count mismatch")
        if sha256(content) != segment.get(f"{side}_content_sha256"):
            error(f"{segment.get('id')}: {side} slice hash mismatch")

segments_by_target: dict[str, list[dict[str, Any]]] = {}
for segment in segments:
    segments_by_target.setdefault(segment["target_path"], []).append(segment)
for target_relative, target_segments in sorted(segments_by_target.items()):
    target_segments.sort(key=lambda record: record.get("order", 0))
    target_path = local_path(target_relative)
    if target_path is None:
        continue
    try:
        target_lines = target_path.read_text(encoding="utf-8").splitlines()
        marker_re = re.compile(r"^% segment-id: (\S+)$")
        markers = [
            (number, match.group(1))
            for number, line in enumerate(target_lines, start=1)
            if (match := marker_re.fullmatch(line))
        ]
        expected_ids = [segment["id"] for segment in target_segments]
        if [marker_id for _, marker_id in markers] != expected_ids:
            error(
                f"{target_relative}: target segment markers do not match "
                "backend IDs/order"
            )
        for (marker_line, marker_id), segment in zip(markers, target_segments):
            if marker_id == segment["id"] and marker_line + 1 != segment["target_line_start"]:
                error(f"{marker_id}: target locator does not begin after its marker")
    except (OSError, UnicodeDecodeError) as exc:
        error(f"cannot validate target markers in {target_relative}: {exc}")

for record in records:
    if record.get("entity_type") == "learning_surface" and record.get("presence") == "present":
        for side in ("source", "target"):
            content = normalized_slice(record[f"{side}_path"], record[f"{side}_line_start"], record[f"{side}_line_end"])
            if sha256(content) != record.get(f"{side}_content_sha256"):
                error(f"{record.get('id')}: {side} learning-surface hash mismatch")

for record in records:
    if record.get("entity_type") != "asset":
        continue
    for side in ("source", "target"):
        path = local_path(record[f"{side}_path"])
        if path is None:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            error(f"cannot read asset {path}: {exc}")
            continue
        if len(data) != record.get(f"{side}_bytes"):
            error(f"{record.get('id')}: {side} asset byte count mismatch")
        if sha256(data) != record.get(f"{side}_sha256"):
            error(f"{record.get('id')}: {side} asset hash mismatch")

for record in records:
    if record.get("entity_type") != "artifact":
        continue
    path = local_path(record["path"])
    if path is None:
        continue
    try:
        data = path.read_bytes()
    except OSError as exc:
        error(f"cannot read artifact {path}: {exc}")
        continue
    if len(data) != record.get("bytes"):
        error(f"{record.get('id')}: artifact byte count mismatch")
    if sha256(data) != record.get("sha256"):
        error(f"{record.get('id')}: artifact hash mismatch")

entity_counts = Counter(record.get("entity_type") for record in records)
report = {
    "csv_bytes": len(csv_bytes),
    "csv_sha256": sha256(csv_bytes),
    "entity_counts": dict(sorted(entity_counts.items())),
    "errors": errors,
    "jsonl_bytes": len(jsonl_bytes),
    "jsonl_sha256": sha256(jsonl_bytes),
    "record_count": len(records),
    "result": "pass" if not errors else "fail",
    "schema_bytes": len(schema_bytes),
    "schema_sha256": sha256(schema_bytes),
    "schema_version": schema_version,
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
sys.exit(0 if not errors else 1)
