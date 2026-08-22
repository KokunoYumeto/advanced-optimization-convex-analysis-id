#!/usr/bin/env python3
"""Validate the O015 backend after the Penn MATH 555 Chapter 3 extension."""

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
SHARED_LEDGER_PATH = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
WORKFLOW = "o015-penn-ch03-backend-v1"
RECORDED_AT = "2026-08-22T18:05:00Z"
RECORD_SCHEMA = "o015-modular-backend-record"

BASELINE_COUNT = 793
BASELINE_RECORD_SET_SHA256 = (
    "7588bdc2e110564bd420e5bcf7bd1737b3f91dd50eabfa213eaa12fa757bfe4f"
)
BASELINE_ARTIFACT_COUNT = 95
BASELINE_ARTIFACT_RECORD_SET_SHA256 = (
    "f44e59696d16d26c1794c91dcd3d875ad84b5358e54c17dbff93845c929ad11e"
)
BASELINE_SEMANTIC_COUNT = 698
BASELINE_SEMANTIC_RECORD_SET_SHA256 = (
    "41fd7e0f51828f4c70f9f56a8ab424ad1ee944bb3f02ba5a654ff059bbeab878"
)

SOURCE_PATH = "authority/penn-state/source/ClassNotes/Section3.tex"
TARGET_PATH = "source/id-ID/penn-03-pendakian-gradien-dan-pencarian-garis-id.tex"
UNIT_ID = "unit.penn.v1.ch03"
EXPECTED_EVENT_IDS = [f"O015-PENN-ADV-{number:04d}" for number in range(4, 25)]
EXPECTED_SOURCE_RANGES = [
    (1, 47),
    (48, 80),
    (81, 160),
    (161, 224),
    (225, 312),
    (313, 404),
    (405, 452),
    (453, 608),
]

# Filled with the exact closure emitted by extend_backend_penn_ch03.py.  These
# values intentionally exclude the immutable 793-record baseline.
EXPECTED_PENN_ENTITY_COUNTS: dict[str, int] = {
    "artifact": 17,
    "asset": 4,
    "concept": 14,
    "correction": 21,
    "edition": 2,
    "learning_surface": 19,
    "qa_event": 12,
    "relation": 59,
    "resource": 1,
    "rights": 7,
    "segment": 8,
    "term": 14,
    "unit": 2,
}

errors: list[str] = []


def error(message: str) -> None:
    errors.append(message)


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_set_sha256(record_set: list[dict[str, Any]]) -> str:
    payload = "".join(
        canonical_json(record) + "\n"
        for record in sorted(record_set, key=lambda item: item["id"])
    ).encode("utf-8")
    return sha256(payload)


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
    key=lambda record: (
        entity_rank.get(record.get("entity_type"), 10_000),
        record.get("id", ""),
    ),
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
if csv_bytes != csv_buffer.getvalue().encode("utf-8"):
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
    if record.get("schema_version") != schema.get("schema_version"):
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
    if (
        record.get("entity_type") == "relation"
        and record.get("relation_type") not in schema.get("relation_types", [])
    ):
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

# The workflow marker is the exclusive Penn-extension ownership boundary.
penn_records = [
    record for record in records if record.get("responsible_workflow") == WORKFLOW
]
baseline_records = [
    record for record in records if record.get("responsible_workflow") != WORKFLOW
]
if len(baseline_records) != BASELINE_COUNT:
    error(f"immutable baseline has {len(baseline_records)} records, expected {BASELINE_COUNT}")
if record_set_sha256(baseline_records) != BASELINE_RECORD_SET_SHA256:
    error("immutable 793-record baseline differs")

baseline_artifacts = [
    record for record in baseline_records if record.get("entity_type") == "artifact"
]
baseline_semantic = [
    record for record in baseline_records if record.get("entity_type") != "artifact"
]
if len(baseline_artifacts) != BASELINE_ARTIFACT_COUNT:
    error("immutable baseline artifact count differs")
if record_set_sha256(baseline_artifacts) != BASELINE_ARTIFACT_RECORD_SET_SHA256:
    error("immutable baseline artifact IDs/hashes differ")
if len(baseline_semantic) != BASELINE_SEMANTIC_COUNT:
    error("immutable baseline semantic count differs")
if record_set_sha256(baseline_semantic) != BASELINE_SEMANTIC_RECORD_SET_SHA256:
    error("immutable baseline semantic records differ")

for record in penn_records:
    if record.get("recorded_at") != RECORDED_AT:
        error(f"{record.get('id')}: wrong deterministic recorded_at")

penn_entity_counts = dict(
    sorted(Counter(record.get("entity_type") for record in penn_records).items())
)
if EXPECTED_PENN_ENTITY_COUNTS and penn_entity_counts != EXPECTED_PENN_ENTITY_COUNTS:
    error(
        "Penn entity closure differs: "
        f"expected {EXPECTED_PENN_ENTITY_COUNTS}, found {penn_entity_counts}"
    )

# Exact source identity and record topology.
source_data = (ROOT / SOURCE_PATH).read_bytes()
target_data = (ROOT / TARGET_PATH).read_bytes()
if (len(source_data), sha256(source_data)) != (
    41715,
    "d4ae6142e2366b12575eafddc833df067518af114e9816187668cc367be43010",
):
    error("Penn Chapter 3 source identity differs")
if (len(target_data), sha256(target_data)) != (
    44364,
    "7c75d0ae56a5a912d561d91ece607f088a4ff4f3de4dbc3396ce40d6d7d6a229",
):
    error("Penn Chapter 3 target identity differs")

segments = sorted(
    [
        record
        for record in penn_records
        if record.get("entity_type") == "segment" and record.get("unit_id") == UNIT_ID
    ],
    key=lambda item: item.get("order", 0),
)
if [record.get("order") for record in segments] != list(range(1, 9)):
    error("Penn segment order is not exactly 1..8")
if [
    (record.get("source_line_start"), record.get("source_line_end"))
    for record in segments
] != EXPECTED_SOURCE_RANGES:
    error("Penn source segment partition differs")
if segments and (segments[0].get("source_line_start"), segments[-1].get("source_line_end")) != (1, 608):
    error("Penn source segment closure is not Section3.tex lines 1..608")

for segment in segments:
    for side in ("source", "target"):
        content = normalized_slice(
            segment[f"{side}_path"],
            segment[f"{side}_line_start"],
            segment[f"{side}_line_end"],
        )
        if len(content) != segment.get(f"{side}_bytes"):
            error(f"{segment.get('id')}: {side} segment byte count mismatch")
        if sha256(content) != segment.get(f"{side}_content_sha256"):
            error(f"{segment.get('id')}: {side} segment hash mismatch")

target_lines = target_data.decode("utf-8").splitlines()
marker_pattern = re.compile(r"^% segment-id: (d90\.penn\.v1\.ch03\.seg\d{4})$")
markers = [
    (number, match.group(1))
    for number, line in enumerate(target_lines, start=1)
    if (match := marker_pattern.fullmatch(line))
]
if [item[1] for item in markers] != [record.get("id") for record in segments]:
    error("Penn target marker IDs/order differ from segment records")
for (marker_line, marker_id), segment in zip(markers, segments):
    if marker_id == segment.get("id") and marker_line + 1 != segment.get("target_line_start"):
        error(f"{marker_id}: target locator does not begin after marker")

learning_surfaces = [
    record for record in penn_records if record.get("entity_type") == "learning_surface"
]
exercise_surfaces = [
    record for record in learning_surfaces if record.get("surface_type") == "exercise_prompt"
]
algorithm_surfaces = [
    record
    for record in learning_surfaces
    if record.get("surface_type") == "algorithm_pseudocode"
]
if len(exercise_surfaces) != 12:
    error(f"Penn exercise surface count is {len(exercise_surfaces)}, expected 12")
if len(algorithm_surfaces) != 7:
    error(f"Penn algorithm surface count is {len(algorithm_surfaces)}, expected 7")
if sum(record.get("disposition") == "independent_replacement_for_excluded_maple" for record in algorithm_surfaces) != 6:
    error("Penn algorithm closure does not contain exactly six independent Maple replacements")

for surface in learning_surfaces:
    for side in ("source", "target"):
        content = normalized_slice(
            surface[f"{side}_path"],
            surface[f"{side}_line_start"],
            surface[f"{side}_line_end"],
        )
        if len(content) != surface.get(f"{side}_bytes"):
            error(f"{surface.get('id')}: {side} learning-surface byte count mismatch")
        if sha256(content) != surface.get(f"{side}_content_sha256"):
            error(f"{surface.get('id')}: {side} learning-surface hash mismatch")

assets = [record for record in penn_records if record.get("entity_type") == "asset"]
if len(assets) != 4:
    error(f"Penn asset count is {len(assets)}, expected 4")
for asset in assets:
    identities: list[tuple[int, str]] = []
    for side in ("source", "target"):
        path = local_path(asset[f"{side}_path"])
        if path is None:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            error(f"cannot read asset {path}: {exc}")
            continue
        identity = (len(data), sha256(data))
        identities.append(identity)
        if identity != (asset.get(f"{side}_bytes"), asset.get(f"{side}_sha256")):
            error(f"{asset.get('id')}: {side} asset identity mismatch")
    if len(identities) == 2 and identities[0] != identities[1]:
        error(f"{asset.get('id')}: source and target assets are not byte-identical")

corrections = [
    record for record in penn_records if record.get("entity_type") == "correction"
]
if [record.get("source_event_id") for record in sorted(corrections, key=lambda item: item.get("source_event_id", ""))] != EXPECTED_EVENT_IDS:
    error("Penn correction event closure is not exactly O015-PENN-ADV-0004..0024")
if len({record.get("source_event_id") for record in corrections}) != 21:
    error("Penn correction event IDs are not unique")
for correction in corrections:
    if correction.get("evidence_artifact_id") != "artifact.o015.adverse-ledger":
        error(f"{correction.get('id')}: correction is not admitted-ledger-bound")
    if correction.get("proposal_artifact_id") != "artifact.penn.proposed-ledger-ch03":
        error(f"{correction.get('id')}: correction lacks proposal provenance")
    if not correction.get("affected_segment_ids"):
        error(f"{correction.get('id')}: no affected segment binding")

try:
    shared_records = [
        json.loads(line)
        for line in SHARED_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]
    shared_ids = [record.get("event_id") for record in shared_records]
    shared_penn = [event_id for event_id in EXPECTED_EVENT_IDS if event_id in shared_ids]
    if shared_penn not in ([], EXPECTED_EVENT_IDS):
        error(f"partial Penn correction integration in shared ledger: {shared_penn}")
except (OSError, json.JSONDecodeError) as exc:
    error(f"cannot validate shared ledger collision state: {exc}")

# Every Penn artifact is bound to live bytes; baseline artifacts are protected
# by their immutable record-set hash rather than refreshed or reinterpreted.
for record in penn_records:
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

required_qa_suffixes = {
    "accessibility",
    "algorithms",
    "build",
    "corrections",
    "exercises",
    "formula-delta",
    "language",
    "math-rereview",
    "solver",
    "source-freeze",
    "structure",
    "visual",
}
qa_records = [record for record in penn_records if record.get("entity_type") == "qa_event"]
actual_qa_suffixes = {
    record["id"].removeprefix("qa.o015.penn-ch03.") for record in qa_records
}
if actual_qa_suffixes != required_qa_suffixes:
    error(
        f"Penn QA closure differs: expected {sorted(required_qa_suffixes)}, found {sorted(actual_qa_suffixes)}"
    )
qa_by_suffix = {
    record["id"].removeprefix("qa.o015.penn-ch03."): record
    for record in qa_records
}
if qa_by_suffix.get("source-freeze", {}).get("result") != "pass":
    error("Penn source-freeze QA is not pass")
if qa_by_suffix.get("structure", {}).get("result") != "pass":
    error("Penn structural audit is not pass")
if qa_by_suffix.get("math-rereview", {}).get("result") != "pass":
    error("Penn independent mathematical rereview is not pass")
if qa_by_suffix.get("solver", {}).get("result") != "pass":
    error("Penn open-solver validation is not pass")
if qa_by_suffix.get("build", {}).get("result") != "pass":
    error("Penn build QA is not pass")
if qa_by_suffix.get("language", {}).get("result") != "not_recorded":
    error("Penn language-review gap is not explicit")
if qa_by_suffix.get("visual", {}).get("result") != "not_recorded":
    error("Penn standalone visual-receipt gap is not explicit")

target_edition = ids.get("edition.penn.math555.id-id.v1", {})
chapter_unit = ids.get(UNIT_ID, {})
for record in (target_edition, chapter_unit):
    if record.get("admission_state") != "candidate_ready_for_root_admission":
        error(f"{record.get('id')}: audit/solver-ready admission state not recorded")
if target_edition.get("publication_state") != "unpublished_working_edition":
    error("Penn target edition publication state is not explicitly unpublished")

source_text = source_data.decode("utf-8")
target_text = target_data.decode("utf-8")
if source_text.count(r"\lstinputlisting") != 6:
    error("Penn source no longer has exactly six listing calls")
if r"\lstinputlisting" in target_text or "Code/" in target_text:
    error("Penn target retains an excluded legacy code dependency")

report = {
    "baseline": {
        "artifact_record_count": len(baseline_artifacts),
        "artifact_record_set_sha256": record_set_sha256(baseline_artifacts),
        "record_count": len(baseline_records),
        "record_set_sha256": record_set_sha256(baseline_records),
        "semantic_record_count": len(baseline_semantic),
        "semantic_record_set_sha256": record_set_sha256(baseline_semantic),
        "unchanged": not any(
            message.startswith("immutable baseline") for message in errors
        ),
    },
    "csv_bytes": len(csv_bytes),
    "csv_sha256": sha256(csv_bytes),
    "entity_counts": dict(sorted(Counter(record.get("entity_type") for record in records).items())),
    "errors": errors,
    "jsonl_bytes": len(jsonl_bytes),
    "jsonl_sha256": sha256(jsonl_bytes),
    "penn_entity_counts": penn_entity_counts,
    "penn_record_count": len(penn_records),
    "penn_record_set_sha256": record_set_sha256(penn_records),
    "record_count": len(records),
    "result": "pass" if not errors else "fail",
    "schema_bytes": len(schema_bytes),
    "schema_sha256": sha256(schema_bytes),
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
sys.exit(0 if not errors else 1)
