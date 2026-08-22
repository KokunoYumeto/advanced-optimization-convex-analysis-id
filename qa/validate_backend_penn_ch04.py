#!/usr/bin/env python3
"""Deterministically validate the Penn MATH 555 Chapter 4 backend admission."""

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
PROPOSED_LEDGER_PATH = ROOT / "qa" / "PENN_CH04_PROPOSED_LEDGER.jsonl"
COMPONENT_RIGHTS_PATH = ROOT / "00_control" / "COMPONENT_RIGHTS.csv"
COVERAGE_OVERLAP_PATH = ROOT / "00_control" / "COVERAGE_OVERLAP.md"

WORKFLOW = "o015-penn-ch04-backend-v1"
RECORDED_AT = "2026-08-22T20:00:00Z"
RECORD_SCHEMA = "o015-modular-backend-record"

BASELINE_COUNT = 973
BASELINE_RECORD_SET_SHA256 = (
    "a53d556fe87bab226e120d7df3611b15e38cabb3defb19e850d481dd72058f9c"
)
BASELINE_ARTIFACT_COUNT = 112
BASELINE_ARTIFACT_RECORD_SET_SHA256 = (
    "19fdb6a76dc593ce7cb5504b6551931602c7b88e968d4c01e306e2536ef64176"
)
BASELINE_SEMANTIC_COUNT = 861
BASELINE_SEMANTIC_RECORD_SET_SHA256 = (
    "e20bb942a17185bfcabbc0e0377ce3608697530162664ebe06fba4400ec706a9"
)
BASELINE_IMMUTABLE_ARTIFACT_COUNT = 109
BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256 = (
    "0694bc4785d8712429c783002f0940d61c3832c32de8b8fc5fc436c128ca21e1"
)

AUTHORIZED_REFRESH_SPECS: dict[str, tuple[str, int, str]] = {
    "artifact.o015.adverse-ledger": (
        "00_control/ADVERSE_LEDGER.jsonl",
        83238,
        "333f870c4383532fcf01a390c8b2321fca2e8b54d5ca6fa857d5d028ce65f8c0",
    ),
    "artifact.o015.component-rights": (
        "00_control/COMPONENT_RIGHTS.csv",
        19534,
        "0f1273adbbc71a82186e3f5a1ed0fa2b5d9084c688bdcb01a9dc56095349f80e",
    ),
    "artifact.o015.coverage-overlap": (
        "00_control/COVERAGE_OVERLAP.md",
        5096,
        "6887732e1212829f2466edd3aedc4b363dd8b06f65a10001a8e41e2f7611087b",
    ),
}

SOURCE_PATH = "authority/penn-state/source/ClassNotes/Section4.tex"
TARGET_PATH = "source/id-ID/penn-04-pencarian-garis-hampiran-dan-konvergensi-id.tex"
WRAPPER_PATH = "source/id-ID/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex"
UNIT_ID = "unit.penn.v1.ch04"
RESOURCE_ID = "resource.penn.math555-nonlinear-programming"
SOURCE_EDITION_ID = "edition.penn.math555.source-v1-0"
TARGET_EDITION_ID = "edition.penn.math555.id-id.v1"
EXPECTED_EVENT_IDS = [f"O015-PENN-ADV-{number:04d}" for number in range(25, 38)]
EXPECTED_SOURCE_RANGES = [
    (1, 74),
    (75, 124),
    (125, 206),
    (207, 243),
    (244, 331),
    (332, 363),
    (364, 469),
]
EXPECTED_TARGET_RANGES = [
    (3, 82),
    (85, 138),
    (141, 234),
    (237, 275),
    (278, 421),
    (424, 467),
    (470, 613),
]

EXPECTED_CH04_ENTITY_COUNTS: dict[str, int] = {
    "artifact": 17,
    "asset": 5,
    "concept": 14,
    "correction": 13,
    "learning_surface": 7,
    "qa_event": 14,
    "relation": 53,
    "rights": 10,
    "segment": 7,
    "term": 14,
    "unit": 1,
}

EXPECTED_CONCEPT_IDS = {
    "concept.penn.armijo-rule",
    "concept.penn.curvature-condition",
    "concept.penn.wolfe-conditions",
    "concept.penn.backtracking-line-search",
    "concept.penn.gradient-related-directions",
    "concept.penn.line-search-stationarity",
    "concept.penn.scaled-gradient-direction",
    "concept.penn.fixed-step-convergence-failure",
    "concept.penn.capture-theorem",
    "concept.penn.kantorovich-inequality",
    "concept.penn.exact-gradient-ascent-rate",
    "concept.penn.spectral-conditioning",
    "concept.penn.eventual-unit-step",
    "concept.penn.superlinear-convergence",
}
EXPECTED_TERM_IDS = {
    "term.penn." + record_id.removeprefix("concept.penn.")
    for record_id in EXPECTED_CONCEPT_IDS
}
EXPECTED_RIGHTS_IDS = {
    "rights.o015-penn-ch04-source",
    "rights.o015-penn-id-ch04",
    "rights.o015-penn-ch04-wrapper",
    "rights.o015-penn-ch04-figures",
    "rights.o015-penn-ch04-bibliography",
    "rights.o015-penn-ch04-bridges",
    "rights.o015-penn-ch04-maple-excluded",
    "rights.o015-penn-ch04-audit",
    "rights.o015-penn-ch04-solver",
    "rights.o015-penn-ch04-visual",
}
EXPECTED_COMPONENT_IDS = {
    "o015-penn-ch04-text",
    "o015-penn-ch04-figures",
    "o015-penn-id-unit-04",
    "o015-penn-id-wrapper-04",
    "o015-penn-local-bbl-04",
    "o015-penn-original-bridges-04",
    "o015-solver-validation-penn-04",
    "o015-structural-audit-penn-04",
    "o015-visual-qa-penn-04",
    "o015-penn-maple",
}
EXPECTED_ASSET_IDS = {
    "asset.penn.v1.ch04.three-d-cos",
    "asset.penn.v1.ch04.wolfe-phi",
    "asset.penn.v1.ch04.wolfe-regions",
    "asset.penn.v1.ch04.convergence-failure",
    "asset.penn.v1.ch04.gradient-ascent-output",
}
EXPECTED_ARTIFACT_IDS = {
    "artifact.penn.source-ch04",
    "artifact.penn.target-ch04",
    "artifact.penn.target-wrapper-ch04",
    "artifact.penn.local-bibliography-ch04",
    "artifact.penn.target-pdf-ch04",
    "artifact.penn.build-log-ch04",
    "artifact.penn.target-text-ch04",
    "artifact.penn.audit-source-ch04",
    "artifact.penn.structure-report-ch04",
    "artifact.penn.formula-manifest-ch04",
    "artifact.penn.proposed-ledger-ch04",
    "artifact.penn.solver-validator-ch04",
    "artifact.penn.solver-results-ch04",
    "artifact.penn.visual-qa-ch04",
    "artifact.penn.source-audit-ch04",
    "artifact.o015.backend-generator-penn-ch04",
    "artifact.o015.backend-validator-penn-ch04",
}
EXPECTED_QA_SUFFIXES = {
    "accessibility",
    "algorithms",
    "build",
    "corrections",
    "exercises",
    "formula-delta",
    "language",
    "math-rereview",
    "overlap",
    "rights",
    "solver",
    "source-freeze",
    "structure",
    "visual",
}

BASE_RELATION_IDS = {
    "relation.penn.ch04.resource-contains-source-edition",
    "relation.penn.ch04.resource-contains-target-edition",
    "relation.penn.ch04.source-edition-contains-unit",
    "relation.penn.ch04.target-edition-contains-unit",
    "relation.penn.ch04.work-contains-unit",
    "relation.penn.ch04.ch03-precedes-ch04",
    "relation.penn.ch04.depends-on-gradient",
    "relation.penn.ch04.depends-on-gradient-ascent",
    "relation.penn.ch04.target-translates-source",
    "relation.penn.ch04.wrapper-contains-target",
    "relation.penn.ch04.pdf-depends-on-wrapper",
    "relation.penn.ch04.pdf-depends-on-bibliography",
    "relation.penn.ch04.text-adapts-pdf",
    "relation.penn.ch04.bibliography-adapts-archive",
    "relation.penn.ch04.structure-depends-on-audit",
    "relation.penn.ch04.formula-depends-on-audit",
    "relation.penn.ch04.solver-results-depend-on-validator",
    "relation.penn.ch04.visual-depends-on-pdf",
    "relation.penn.ch04.source-audit-depends-on-structure",
    "relation.penn.ch04.source-audit-depends-on-visual",
}
DEFINITION_RELATIONS = [
    (1, "armijo-rule"),
    (1, "curvature-condition"),
    (1, "wolfe-conditions"),
    (2, "backtracking-line-search"),
    (3, "gradient-related-directions"),
    (3, "line-search-stationarity"),
    (3, "scaled-gradient-direction"),
    (4, "fixed-step-convergence-failure"),
    (4, "capture-theorem"),
    (5, "kantorovich-inequality"),
    (5, "exact-gradient-ascent-rate"),
    (5, "spectral-conditioning"),
    (7, "eventual-unit-step"),
    (7, "superlinear-convergence"),
]
EXERCISE_RELATION_SUFFIXES = [
    "line-search-stationarity",
    "scaled-gradient-direction",
    "kantorovich-inequality",
    "backtracking-line-search",
]
EXPECTED_RELATION_IDS = set(BASE_RELATION_IDS)
EXPECTED_RELATION_IDS.update(
    f"relation.penn.ch04.contains-seg{order:04d}" for order in range(1, 8)
)
EXPECTED_RELATION_IDS.update(
    f"relation.penn.ch04.seg{order:04d}-defines-{suffix}"
    for order, suffix in DEFINITION_RELATIONS
)
EXPECTED_RELATION_IDS.update(
    f"relation.penn.ch04.exercise{order:02d}-exercises-{suffix}"
    for order, suffix in enumerate(EXERCISE_RELATION_SUFFIXES, start=1)
)
EXPECTED_RELATION_IDS.update(
    {
        "relation.penn.ch04.bridge01-illustrates-backtracking-line-search",
        "relation.penn.ch04.bridge02-illustrates-gradient-ascent",
        "relation.penn.ch04.bridge03-illustrates-gradient-ascent",
        "relation.penn.ch04.three-d-cos-illustrates-wolfe-conditions",
        "relation.penn.ch04.wolfe-phi-illustrates-wolfe-conditions",
        "relation.penn.ch04.wolfe-regions-illustrates-wolfe-conditions",
        "relation.penn.ch04.convergence-failure-illustrates-fixed-step-convergence-failure",
        "relation.penn.ch04.gradient-ascent-output-illustrates-spectral-conditioning",
    }
)

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

expected_jsonl = "".join(canonical_json(record) + "\n" for record in records).encode(
    "utf-8"
)
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

ch04_records = [
    record for record in records if record.get("responsible_workflow") == WORKFLOW
]
baseline_records = [
    record for record in records if record.get("responsible_workflow") != WORKFLOW
]
if len(baseline_records) != BASELINE_COUNT:
    error(f"immutable baseline has {len(baseline_records)} records, expected {BASELINE_COUNT}")
if record_set_sha256(baseline_records) != BASELINE_RECORD_SET_SHA256:
    error("immutable refreshed 973-record baseline differs")

baseline_artifacts = [
    record for record in baseline_records if record.get("entity_type") == "artifact"
]
baseline_semantic = [
    record for record in baseline_records if record.get("entity_type") != "artifact"
]
immutable_baseline_artifacts = [
    record
    for record in baseline_artifacts
    if record.get("id") not in AUTHORIZED_REFRESH_SPECS
]
if len(baseline_artifacts) != BASELINE_ARTIFACT_COUNT:
    error("refreshed baseline artifact count differs")
if record_set_sha256(baseline_artifacts) != BASELINE_ARTIFACT_RECORD_SET_SHA256:
    error("refreshed baseline artifact record set differs")
if len(baseline_semantic) != BASELINE_SEMANTIC_COUNT:
    error("immutable baseline semantic count differs")
if record_set_sha256(baseline_semantic) != BASELINE_SEMANTIC_RECORD_SET_SHA256:
    error("immutable baseline semantic records differ")
if len(immutable_baseline_artifacts) != BASELINE_IMMUTABLE_ARTIFACT_COUNT:
    error("immutable non-refreshed artifact count differs")
if (
    record_set_sha256(immutable_baseline_artifacts)
    != BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256
):
    error("immutable non-refreshed artifact records differ")

for record_id, (path, size, digest) in AUTHORIZED_REFRESH_SPECS.items():
    record = ids.get(record_id, {})
    if (
        record.get("path"),
        record.get("bytes"),
        record.get("sha256"),
    ) != (path, size, digest):
        error(f"{record_id}: enumerated live binding differs")
    local = local_path(path)
    if local is not None:
        try:
            data = local.read_bytes()
        except OSError as exc:
            error(f"{record_id}: cannot read live control: {exc}")
        else:
            if (len(data), sha256(data)) != (size, digest):
                error(f"{record_id}: live control bytes differ")

for record in ch04_records:
    if record.get("recorded_at") != RECORDED_AT:
        error(f"{record.get('id')}: wrong deterministic recorded_at")

ch04_entity_counts = dict(
    sorted(Counter(record.get("entity_type") for record in ch04_records).items())
)
if ch04_entity_counts != EXPECTED_CH04_ENTITY_COUNTS:
    error(
        "Chapter 4 entity closure differs: "
        f"expected {EXPECTED_CH04_ENTITY_COUNTS}, found {ch04_entity_counts}"
    )

if len(records) != BASELINE_COUNT + sum(EXPECTED_CH04_ENTITY_COUNTS.values()):
    error("total backend record count differs")

# Resource/edition closure is reused without rewriting its semantic records.
for record_id in (RESOURCE_ID, SOURCE_EDITION_ID, TARGET_EDITION_ID, "unit.penn.v1"):
    if record_id not in ids:
        error(f"missing reused Penn resource/edition record {record_id}")
    elif ids[record_id].get("responsible_workflow") == WORKFLOW:
        error(f"{record_id}: Chapter 4 improperly rewrote a pre-existing semantic record")

source_path = local_path(SOURCE_PATH)
target_path = local_path(TARGET_PATH)
source_data = source_path.read_bytes() if source_path and source_path.is_file() else b""
target_data = target_path.read_bytes() if target_path and target_path.is_file() else b""
if (len(source_data), sha256(source_data)) != (
    34684,
    "76113034709b5914fa920076f2e882ccf30157e78ce5bdf4593a5d39af1886d5",
):
    error("Penn Chapter 4 source identity differs")
if (len(target_data), sha256(target_data)) != (
    33313,
    "c5c0f09d38454177e61c2a97c9beef07771d5f4f715cc7a4a81a871ff54ced8f",
):
    error("Penn Chapter 4 target identity differs")

segments = sorted(
    [
        record
        for record in ch04_records
        if record.get("entity_type") == "segment" and record.get("unit_id") == UNIT_ID
    ],
    key=lambda item: item.get("order", 0),
)
if [record.get("order") for record in segments] != list(range(1, 8)):
    error("Chapter 4 segment order is not exactly 1..7")
if [
    (record.get("source_line_start"), record.get("source_line_end"))
    for record in segments
] != EXPECTED_SOURCE_RANGES:
    error("Chapter 4 source segment partition differs")
if [
    (record.get("target_line_start"), record.get("target_line_end"))
    for record in segments
] != EXPECTED_TARGET_RANGES:
    error("Chapter 4 target segment partition differs")
if segments and (
    segments[0].get("source_line_start"),
    segments[-1].get("source_line_end"),
) != (1, 469):
    error("Chapter 4 source segment closure is not lines 1..469")

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

target_lines = target_data.decode("utf-8").splitlines() if target_data else []
marker_pattern = re.compile(r"^% segment-id: (d90\.penn\.v1\.ch04\.seg\d{4})$")
markers = [
    (number, match.group(1))
    for number, line in enumerate(target_lines, start=1)
    if (match := marker_pattern.fullmatch(line))
]
if [item[1] for item in markers] != [record.get("id") for record in segments]:
    error("Chapter 4 target marker IDs/order differ from segment records")
for (marker_line, marker_id), segment in zip(markers, segments):
    if marker_id == segment.get("id") and marker_line + 1 != segment.get(
        "target_line_start"
    ):
        error(f"{marker_id}: target locator does not begin after marker")

concept_ids = {
    record["id"]
    for record in ch04_records
    if record.get("entity_type") == "concept"
}
term_ids = {
    record["id"] for record in ch04_records if record.get("entity_type") == "term"
}
if concept_ids != EXPECTED_CONCEPT_IDS:
    error("Chapter 4 concept stable-ID closure differs")
if term_ids != EXPECTED_TERM_IDS:
    error("Chapter 4 term stable-ID closure differs")

learning_surfaces = [
    record for record in ch04_records if record.get("entity_type") == "learning_surface"
]
exercise_surfaces = sorted(
    [record for record in learning_surfaces if record.get("surface_type") == "exercise_prompt"],
    key=lambda item: item.get("order", 0),
)
algorithm_surfaces = sorted(
    [record for record in learning_surfaces if record.get("surface_type") == "algorithm_pseudocode"],
    key=lambda item: item.get("order", 0),
)
if [record.get("order") for record in exercise_surfaces] != [1, 2, 3, 4]:
    error("Chapter 4 exercise learning-surface order/count differs")
if [record.get("order") for record in algorithm_surfaces] != [1, 2, 3]:
    error("Chapter 4 algorithm learning-surface order/count differs")
if any(
    record.get("disposition") != "independent_replacement_for_excluded_maple"
    for record in algorithm_surfaces
):
    error("Chapter 4 algorithm closure does not exclusively use independent replacements")
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

assets = [record for record in ch04_records if record.get("entity_type") == "asset"]
if {record["id"] for record in assets} != EXPECTED_ASSET_IDS:
    error("Chapter 4 asset stable-ID closure differs")
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

rights_records = [
    record for record in ch04_records if record.get("entity_type") == "rights"
]
if {record["id"] for record in rights_records} != EXPECTED_RIGHTS_IDS:
    error("Chapter 4 rights stable-ID closure differs")
if {record.get("component_id") for record in rights_records} != EXPECTED_COMPONENT_IDS:
    error("Chapter 4 rights component closure differs")
maple_rights = ids.get("rights.o015-penn-ch04-maple-excluded", {})
if (
    maple_rights.get("status") != "excluded"
    or maple_rights.get("translation_permitted") is not False
):
    error("Chapter 4 excluded Maple rights record differs")

try:
    with COMPONENT_RIGHTS_PATH.open("r", encoding="utf-8", newline="") as handle:
        component_rows = list(csv.DictReader(handle))
    component_by_id = {row.get("component_id"): row for row in component_rows}
    if not EXPECTED_COMPONENT_IDS.issubset(component_by_id):
        error("live component-rights table lacks Chapter 4 closure rows")
    if component_by_id.get("o015-penn-maple", {}).get("status") != "excluded":
        error("live component-rights table does not exclude Penn Maple")
except (OSError, csv.Error) as exc:
    error(f"cannot validate live component-rights table: {exc}")

corrections = sorted(
    [record for record in ch04_records if record.get("entity_type") == "correction"],
    key=lambda item: item.get("source_event_id", ""),
)
if [record.get("source_event_id") for record in corrections] != EXPECTED_EVENT_IDS:
    error("Chapter 4 correction event closure is not exactly 0025..0037")
try:
    proposed_records = [
        json.loads(line)
        for line in PROPOSED_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]
except (OSError, json.JSONDecodeError) as exc:
    error(f"cannot read Chapter 4 proposed ledger: {exc}")
    proposed_records = []
if [record.get("event_id") for record in proposed_records] != EXPECTED_EVENT_IDS:
    error("Chapter 4 proposed-ledger event closure differs")
proposal_by_id = {record.get("event_id"): record for record in proposed_records}
for correction in corrections:
    event_id = correction.get("source_event_id")
    proposal = proposal_by_id.get(event_id, {})
    if correction.get("evidence_artifact_id") != "artifact.o015.adverse-ledger":
        error(f"{correction.get('id')}: correction is not shared-ledger-bound")
    if correction.get("proposal_artifact_id") != "artifact.penn.proposed-ledger-ch04":
        error(f"{correction.get('id')}: correction lacks proposal provenance")
    if correction.get("shared_ledger_state") != "integrated":
        error(f"{correction.get('id')}: correction integration state differs")
    if correction.get("disposition") != "applied_in_admitted_reader":
        error(f"{correction.get('id')}: correction disposition differs")
    if not correction.get("affected_segment_ids"):
        error(f"{correction.get('id')}: no affected segment binding")
    for correction_field, proposal_field in (
        ("source_locator", "source"),
        ("surface", "surface"),
        ("source_issue", "source_issue"),
        ("target_action", "target_action"),
        ("correction_class", "class"),
    ):
        if correction.get(correction_field) != proposal.get(proposal_field):
            error(f"{correction.get('id')}: proposal field {proposal_field} differs")

try:
    shared_records = [
        json.loads(line)
        for line in SHARED_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]
    if len({record.get("event_id") for record in shared_records}) != len(shared_records):
        error("shared adverse ledger has duplicate event IDs")
    if proposed_records and shared_records[-len(proposed_records) :] != proposed_records:
        error("Chapter 4 proposed records are not the exact shared-ledger tail")
except (OSError, json.JSONDecodeError) as exc:
    error(f"cannot validate shared adverse ledger: {exc}")

artifact_records = [
    record for record in ch04_records if record.get("entity_type") == "artifact"
]
if {record["id"] for record in artifact_records} != EXPECTED_ARTIFACT_IDS:
    error("Chapter 4 artifact stable-ID closure differs")

# Every artifact record, baseline and Chapter 4, is now bound to live bytes.
for record in [*baseline_artifacts, *artifact_records]:
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

qa_records = [
    record for record in ch04_records if record.get("entity_type") == "qa_event"
]
actual_qa_suffixes = {
    record["id"].removeprefix("qa.o015.penn-ch04.") for record in qa_records
}
if actual_qa_suffixes != EXPECTED_QA_SUFFIXES:
    error("Chapter 4 QA stable-ID closure differs")
qa_by_suffix = {
    record["id"].removeprefix("qa.o015.penn-ch04."): record
    for record in qa_records
}
for suffix in EXPECTED_QA_SUFFIXES - {"language", "accessibility"}:
    if qa_by_suffix.get(suffix, {}).get("result") != "pass":
        error(f"Chapter 4 {suffix} QA is not pass")
if qa_by_suffix.get("language", {}).get("result") != "not_recorded":
    error("Chapter 4 language-review gap is not explicit")
if qa_by_suffix.get("accessibility", {}).get("result") != "pass_with_limitation":
    error("Chapter 4 accessibility limitation is not explicit")

relation_records = [
    record for record in ch04_records if record.get("entity_type") == "relation"
]
if {record["id"] for record in relation_records} != EXPECTED_RELATION_IDS:
    error("Chapter 4 relation stable-ID closure differs")

chapter_unit = ids.get(UNIT_ID, {})
expected_unit_fields = {
    "parent_id": "unit.penn.v1",
    "order": 4,
    "edition_id": SOURCE_EDITION_ID,
    "source_edition_id": SOURCE_EDITION_ID,
    "target_edition_id": TARGET_EDITION_ID,
    "rights_id": "rights.o015-penn-id-ch04",
    "admission_state": "admitted_reader",
    "translation_state": "built",
    "publication_state": "unpublished_working_edition",
    "next_source_order_unit": "Section5.tex:1",
}
for field, expected in expected_unit_fields.items():
    if chapter_unit.get(field) != expected:
        error(f"{UNIT_ID}: {field} differs")

source_text = source_data.decode("utf-8") if source_data else ""
target_text = target_data.decode("utf-8") if target_data else ""
if source_text.count(r"\lstinputlisting") != 3:
    error("Chapter 4 source no longer has exactly three listing calls")
if r"\lstinputlisting" in target_text or "Code/" in target_text:
    error("Chapter 4 target retains an excluded legacy code dependency")
try:
    wrapper_text = (ROOT / WRAPPER_PATH).read_text(encoding="utf-8")
except (OSError, UnicodeDecodeError) as exc:
    error(f"cannot read Chapter 4 wrapper: {exc}")
    wrapper_text = ""
if "CC BY-NC-SA 3.0 US" not in wrapper_text:
    error("Chapter 4 wrapper lacks exact rights expression")
if "tidak" not in wrapper_text.lower() or "mendukung" not in wrapper_text.lower():
    error("Chapter 4 wrapper lacks non-endorsement notice")

for path, expected_status in (
    ("qa/PENN_CH04_STRUCTURE_REPORT.json", "PASS"),
    ("qa/PENN_CH04_FORMULA_DELTA_MANIFEST.json", "PASS"),
    ("qa/PENN_CH04_SOLVER_RESULTS.json", "PASS"),
    ("qa/PENN_CH04_VISUAL_QA.json", "PASS"),
):
    try:
        evidence = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        error(f"cannot validate {path}: {exc}")
        continue
    if evidence.get("status") != expected_status:
        error(f"{path}: status is not {expected_status}")
    if evidence.get("failures", []) != []:
        error(f"{path}: failures are not empty")

try:
    overlap_text = COVERAGE_OVERLAP_PATH.read_text(encoding="utf-8")
except (OSError, UnicodeDecodeError) as exc:
    error(f"cannot read coverage-overlap control: {exc}")
    overlap_text = ""
for phrase in (
    "Penn Chapters 3 and 4 are now admitted.",
    "Chapter 4 supplies Wolfe/Armijo inexact line search",
    "does not duplicate O018",
    "active source-order cursor is Penn Chapter 5",
):
    if phrase not in overlap_text:
        error(f"coverage-overlap control lacks required phrase: {phrase}")

report = {
    "authorized_refreshed_baseline_ids": sorted(AUTHORIZED_REFRESH_SPECS),
    "baseline": {
        "artifact_record_count": len(baseline_artifacts),
        "artifact_record_set_sha256": record_set_sha256(baseline_artifacts),
        "immutable_artifact_record_count": len(immutable_baseline_artifacts),
        "immutable_artifact_record_set_sha256": record_set_sha256(
            immutable_baseline_artifacts
        ),
        "record_count": len(baseline_records),
        "record_set_sha256": record_set_sha256(baseline_records),
        "semantic_record_count": len(baseline_semantic),
        "semantic_record_set_sha256": record_set_sha256(baseline_semantic),
        "unchanged": not any("baseline" in message for message in errors),
    },
    "csv_bytes": len(csv_bytes),
    "csv_sha256": sha256(csv_bytes),
    "entity_counts": dict(
        sorted(Counter(record.get("entity_type") for record in records).items())
    ),
    "errors": errors,
    "jsonl_bytes": len(jsonl_bytes),
    "jsonl_sha256": sha256(jsonl_bytes),
    "penn_ch04_entity_counts": ch04_entity_counts,
    "penn_ch04_record_count": len(ch04_records),
    "penn_ch04_record_set_sha256": record_set_sha256(ch04_records),
    "record_count": len(records),
    "result": "pass" if not errors else "fail",
    "schema_bytes": len(schema_bytes),
    "schema_sha256": sha256(schema_bytes),
    "segment_count": len(segments),
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
sys.exit(0 if not errors else 1)
