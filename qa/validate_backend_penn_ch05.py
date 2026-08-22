#!/usr/bin/env python3
"""Deterministically validate the Penn MATH 555 Chapter 5 backend admission."""

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
PROPOSED_LEDGER_PATH = ROOT / "qa" / "PENN_CH05_PROPOSED_LEDGER.jsonl"
COMPONENT_RIGHTS_PATH = ROOT / "00_control" / "COMPONENT_RIGHTS.csv"
COVERAGE_OVERLAP_PATH = ROOT / "00_control" / "COVERAGE_OVERLAP.md"

WORKFLOW = "o015-penn-ch05-backend-v1"
RECORDED_AT = "2026-08-22T22:30:00Z"
RECORD_SCHEMA = "o015-modular-backend-record"

BASELINE_COUNT = 1128
BASELINE_RECORD_SET_SHA256 = (
    "23ffc42f0fa6b19a828154db74bdda2a0fa99e860f7615c918f4c7a3787f2edb"
)
BASELINE_ARTIFACT_COUNT = 129
BASELINE_ARTIFACT_RECORD_SET_SHA256 = (
    "ed4acc7a5315a752347901bc5057a7dec1d09f777dc3c6b315c7fa8be2476392"
)
BASELINE_SEMANTIC_COUNT = 999
BASELINE_SEMANTIC_RECORD_SET_SHA256 = (
    "971333c796eeb036b59cc1ff5ce6c0ce5bfa2836e5ab4d7f4176d4aeea0b5d97"
)
BASELINE_IMMUTABLE_ARTIFACT_COUNT = 126
BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256 = (
    "68c89eb4dd196935f8b60d9f3eccc32a4ae61530503d189bb4ca3903bd9061c0"
)

AUTHORIZED_REFRESH_SPECS: dict[str, tuple[str, int, str]] = {
    "artifact.o015.adverse-ledger": (
        "00_control/ADVERSE_LEDGER.jsonl",
        93480,
        "c8d87cd7958e9beba30372e1fc70df7fe992970db780d8757c061854fb9075f0",
    ),
    "artifact.o015.component-rights": (
        "00_control/COMPONENT_RIGHTS.csv",
        23258,
        "51e08f77f709a945c8e53948ee466d7d06e75e469ef7fef4d7d269fc895e37e9",
    ),
    "artifact.o015.coverage-overlap": (
        "00_control/COVERAGE_OVERLAP.md",
        5997,
        "4e47d255c94d404b68f347464302475edf76da2a21824afa9ccda50cf9618560",
    ),
}

SOURCE_PATH = "authority/penn-state/source/ClassNotes/Section5.tex"
TARGET_PATH = "source/id-ID/penn-05-metode-newton-dan-koreksi-id.tex"
WRAPPER_PATH = "source/id-ID/D90-PENN-05-metode-newton-dan-koreksi-id.tex"
UNIT_ID = "unit.penn.v1.ch05"
RESOURCE_ID = "resource.penn.math555-nonlinear-programming"
SOURCE_EDITION_ID = "edition.penn.math555.source-v1-0"
TARGET_EDITION_ID = "edition.penn.math555.id-id.v1"
EXPECTED_EVENT_IDS = [f"O015-PENN-ADV-{number:04d}" for number in range(38, 50)]
EXPECTED_SOURCE_RANGES = [(1, 38), (39, 74), (75, 148), (149, 178), (179, 206), (207, 277), (278, 317)]
EXPECTED_TARGET_RANGES = [(3, 57), (60, 102), (105, 207), (210, 239), (242, 277), (280, 354), (357, 400)]

EXPECTED_CH05_ENTITY_COUNTS: dict[str, int] = {
    "artifact": 17,
    "asset": 4,
    "concept": 14,
    "correction": 12,
    "learning_surface": 8,
    "qa_event": 14,
    "relation": 53,
    "rights": 11,
    "segment": 7,
    "term": 14,
    "unit": 1,
}

EXPECTED_CONCEPT_IDS = {
    "concept.penn.multivariate-newton-direction",
    "concept.penn.pure-newton-method",
    "concept.penn.variable-step-newton",
    "concept.penn.indefinite-hessian-newton-failure",
    "concept.penn.induced-matrix-norm",
    "concept.penn.local-multivariate-newton-convergence",
    "concept.penn.newton-quadratic-error-bound",
    "concept.penn.gradient-newton-hybrid",
    "concept.penn.modified-cholesky",
    "concept.penn.positive-definite-hessian-surrogate",
    "concept.penn.triangular-newton-solve",
    "concept.penn.corrected-newton-method",
    "concept.penn.corrected-newton-stationarity",
    "concept.penn.eventual-uncorrected-newton",
}
EXPECTED_TERM_IDS = {
    "term.penn." + record_id.removeprefix("concept.penn.")
    for record_id in EXPECTED_CONCEPT_IDS
}
EXPECTED_RIGHTS_IDS = {
    "rights.o015-penn-ch05-source",
    "rights.o015-penn-id-ch05",
    "rights.o015-penn-ch05-wrapper",
    "rights.o015-penn-ch05-figures",
    "rights.o015-penn-ch05-bibliography",
    "rights.o015-penn-ch05-bridges",
    "rights.o015-penn-ch05-maple-excluded",
    "rights.o015-penn-ch05-audit",
    "rights.o015-penn-ch05-solver",
    "rights.o015-penn-ch05-rereview",
    "rights.o015-penn-ch05-visual",
}
EXPECTED_RIGHTS_COMPONENT_IDS = {
    "o015-penn-ch05-text",
    "o015-penn-id-unit-05",
    "o015-penn-id-wrapper-05",
    "o015-penn-ch05-figures",
    "o015-penn-local-bbl-05",
    "o015-penn-original-bridges-05",
    "o015-penn-maple",
    "o015-structural-audit-penn-05",
    "o015-solver-validation-penn-05",
    "o015-independent-rereview-penn-05",
    "o015-visual-qa-penn-05",
}
EXPECTED_LIVE_COMPONENT_IDS = EXPECTED_RIGHTS_COMPONENT_IDS | {"o015-backend-tooling"}
EXPECTED_ASSET_IDS = {
    "asset.penn.v1.ch05.newton-method",
    "asset.penn.v1.ch05.double-peak",
    "asset.penn.v1.ch05.gradient-newton-hybrid",
    "asset.penn.v1.ch05.modified-newton",
}
EXPECTED_ARTIFACT_IDS = {
    "artifact.penn.source-ch05",
    "artifact.penn.target-ch05",
    "artifact.penn.target-wrapper-ch05",
    "artifact.penn.local-bibliography-ch05",
    "artifact.penn.target-pdf-ch05",
    "artifact.penn.build-log-ch05",
    "artifact.penn.target-text-ch05",
    "artifact.penn.audit-source-ch05",
    "artifact.penn.structure-report-ch05",
    "artifact.penn.proposed-ledger-ch05",
    "artifact.penn.solver-validator-ch05",
    "artifact.penn.solver-results-ch05",
    "artifact.penn.visual-qa-ch05",
    "artifact.penn.independent-rereview-ch05",
    "artifact.penn.source-audit-ch05",
    "artifact.o015.backend-generator-penn-ch05",
    "artifact.o015.backend-validator-penn-ch05",
}
EXPECTED_QA_SUFFIXES = {
    "accessibility",
    "algorithms",
    "build",
    "corrections",
    "exercises",
    "formulas",
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
    "relation.penn.ch05.resource-contains-source-edition",
    "relation.penn.ch05.resource-contains-target-edition",
    "relation.penn.ch05.source-edition-contains-unit",
    "relation.penn.ch05.target-edition-contains-unit",
    "relation.penn.ch05.work-contains-unit",
    "relation.penn.ch05.ch04-precedes-ch05",
    "relation.penn.ch05.depends-on-gradient",
    "relation.penn.ch05.depends-on-line-search",
    "relation.penn.ch05.target-translates-source",
    "relation.penn.ch05.wrapper-contains-target",
    "relation.penn.ch05.pdf-depends-on-wrapper",
    "relation.penn.ch05.pdf-depends-on-bibliography",
    "relation.penn.ch05.text-adapts-pdf",
    "relation.penn.ch05.bibliography-adapts-archive",
    "relation.penn.ch05.structure-depends-on-audit",
    "relation.penn.ch05.solver-results-depend-on-validator",
    "relation.penn.ch05.visual-depends-on-pdf",
    "relation.penn.ch05.rereview-depends-on-target",
    "relation.penn.ch05.source-audit-depends-on-structure",
    "relation.penn.ch05.source-audit-depends-on-visual",
}
DEFINITION_RELATIONS = [
    (1, "multivariate-newton-direction"),
    (1, "pure-newton-method"),
    (1, "variable-step-newton"),
    (2, "indefinite-hessian-newton-failure"),
    (2, "induced-matrix-norm"),
    (3, "local-multivariate-newton-convergence"),
    (3, "newton-quadratic-error-bound"),
    (4, "gradient-newton-hybrid"),
    (5, "modified-cholesky"),
    (5, "positive-definite-hessian-surrogate"),
    (5, "triangular-newton-solve"),
    (6, "corrected-newton-method"),
    (7, "corrected-newton-stationarity"),
    (7, "eventual-uncorrected-newton"),
]
EXERCISE_RELATION_SUFFIXES = [
    "variable-step-newton",
    "indefinite-hessian-newton-failure",
    "gradient-newton-hybrid",
    "eventual-uncorrected-newton",
    "eventual-uncorrected-newton",
]
EXPECTED_RELATION_IDS = set(BASE_RELATION_IDS)
EXPECTED_RELATION_IDS.update(f"relation.penn.ch05.contains-seg{order:04d}" for order in range(1, 8))
EXPECTED_RELATION_IDS.update(
    f"relation.penn.ch05.seg{order:04d}-defines-{suffix}"
    for order, suffix in DEFINITION_RELATIONS
)
EXPECTED_RELATION_IDS.update(
    f"relation.penn.ch05.exercise{order:02d}-exercises-{suffix}"
    for order, suffix in enumerate(EXERCISE_RELATION_SUFFIXES, start=1)
)
EXPECTED_RELATION_IDS.update({
    "relation.penn.ch05.algorithm01-illustrates-variable-step-newton",
    "relation.penn.ch05.algorithm02-illustrates-modified-cholesky",
    "relation.penn.ch05.algorithm03-illustrates-corrected-newton-method",
    "relation.penn.ch05.newton-method-illustrates-pure-newton-method",
    "relation.penn.ch05.double-peak-illustrates-indefinite-hessian-newton-failure",
    "relation.penn.ch05.gradient-newton-hybrid-illustrates-gradient-newton-hybrid",
    "relation.penn.ch05.modified-newton-illustrates-corrected-newton-method",
})

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
expected_order = sorted(records, key=lambda record: (entity_rank.get(record.get("entity_type"), 10_000), record.get("id", "")))
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
    writer.writerow([record.get("schema", ""), record.get("schema_version", ""), record.get("entity_type", ""), record.get("id", ""), canonical_json(record)])
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

ch05_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
baseline_records = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
if len(baseline_records) != BASELINE_COUNT:
    error(f"immutable baseline has {len(baseline_records)} records, expected {BASELINE_COUNT}")
if record_set_sha256(baseline_records) != BASELINE_RECORD_SET_SHA256:
    error("immutable refreshed 1,128-record baseline differs")

baseline_artifacts = [record for record in baseline_records if record.get("entity_type") == "artifact"]
baseline_semantic = [record for record in baseline_records if record.get("entity_type") != "artifact"]
immutable_baseline_artifacts = [
    record for record in baseline_artifacts if record.get("id") not in AUTHORIZED_REFRESH_SPECS
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
if record_set_sha256(immutable_baseline_artifacts) != BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256:
    error("immutable non-refreshed artifact records differ")

for record_id, (path, size, digest) in AUTHORIZED_REFRESH_SPECS.items():
    record = ids.get(record_id, {})
    if (record.get("path"), record.get("bytes"), record.get("sha256")) != (path, size, digest):
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

for record in ch05_records:
    if record.get("recorded_at") != RECORDED_AT:
        error(f"{record.get('id')}: wrong deterministic recorded_at")

ch05_entity_counts = dict(sorted(Counter(record.get("entity_type") for record in ch05_records).items()))
if ch05_entity_counts != EXPECTED_CH05_ENTITY_COUNTS:
    error(f"Chapter 5 entity closure differs: expected {EXPECTED_CH05_ENTITY_COUNTS}, found {ch05_entity_counts}")
if len(records) != BASELINE_COUNT + sum(EXPECTED_CH05_ENTITY_COUNTS.values()):
    error("total backend record count differs")

for record_id in (RESOURCE_ID, SOURCE_EDITION_ID, TARGET_EDITION_ID, "unit.penn.v1"):
    if record_id not in ids:
        error(f"missing reused Penn resource/edition record {record_id}")
    elif ids[record_id].get("responsible_workflow") == WORKFLOW:
        error(f"{record_id}: Chapter 5 improperly rewrote a pre-existing semantic record")

source_path = local_path(SOURCE_PATH)
target_path = local_path(TARGET_PATH)
source_data = source_path.read_bytes() if source_path and source_path.is_file() else b""
target_data = target_path.read_bytes() if target_path and target_path.is_file() else b""
if (len(source_data), sha256(source_data)) != (22371, "15186b99be0913d83046e3e32eaf7a378d3a4fccd222219984b091ddf7f9a428"):
    error("Penn Chapter 5 source identity differs")
if (len(target_data), sha256(target_data)) != (27317, "0f6afd7da2268661124f967f299ac9df89bb6a8f5683b3e4e8fea32718a8549a"):
    error("Penn Chapter 5 target identity differs")

segments = sorted(
    [record for record in ch05_records if record.get("entity_type") == "segment" and record.get("unit_id") == UNIT_ID],
    key=lambda item: item.get("order", 0),
)
if [record.get("order") for record in segments] != list(range(1, 8)):
    error("Chapter 5 segment order is not exactly 1..7")
if [(record.get("source_line_start"), record.get("source_line_end")) for record in segments] != EXPECTED_SOURCE_RANGES:
    error("Chapter 5 source segment partition differs")
if [(record.get("target_line_start"), record.get("target_line_end")) for record in segments] != EXPECTED_TARGET_RANGES:
    error("Chapter 5 target segment partition differs")
if segments and (segments[0].get("source_line_start"), segments[-1].get("source_line_end")) != (1, 317):
    error("Chapter 5 source segment closure is not lines 1..317")
for segment in segments:
    for side in ("source", "target"):
        content = normalized_slice(segment[f"{side}_path"], segment[f"{side}_line_start"], segment[f"{side}_line_end"])
        if len(content) != segment.get(f"{side}_bytes"):
            error(f"{segment.get('id')}: {side} segment byte count mismatch")
        if sha256(content) != segment.get(f"{side}_content_sha256"):
            error(f"{segment.get('id')}: {side} segment hash mismatch")

target_lines = target_data.decode("utf-8").splitlines() if target_data else []
marker_pattern = re.compile(r"^% segment-id: (d90\.penn\.v1\.ch05\.seg\d{4})$")
markers = [
    (number, match.group(1))
    for number, line in enumerate(target_lines, start=1)
    if (match := marker_pattern.fullmatch(line))
]
if [item[1] for item in markers] != [record.get("id") for record in segments]:
    error("Chapter 5 target marker IDs/order differ from segment records")
for (marker_line, marker_id), segment in zip(markers, segments):
    if marker_id == segment.get("id") and marker_line + 1 != segment.get("target_line_start"):
        error(f"{marker_id}: target locator does not begin after marker")

concept_ids = {record["id"] for record in ch05_records if record.get("entity_type") == "concept"}
term_ids = {record["id"] for record in ch05_records if record.get("entity_type") == "term"}
if concept_ids != EXPECTED_CONCEPT_IDS:
    error("Chapter 5 concept stable-ID closure differs")
if term_ids != EXPECTED_TERM_IDS:
    error("Chapter 5 term stable-ID closure differs")

learning_surfaces = [record for record in ch05_records if record.get("entity_type") == "learning_surface"]
exercise_surfaces = sorted([record for record in learning_surfaces if record.get("surface_type") == "exercise_prompt"], key=lambda item: item.get("order", 0))
algorithm_surfaces = sorted([record for record in learning_surfaces if record.get("surface_type") == "algorithm_pseudocode"], key=lambda item: item.get("order", 0))
if [record.get("order") for record in exercise_surfaces] != [1, 2, 3, 4, 5]:
    error("Chapter 5 exercise learning-surface order/count differs")
if [record.get("order") for record in algorithm_surfaces] != [1, 2, 3]:
    error("Chapter 5 algorithm learning-surface order/count differs")
if sum(record.get("excluded_source_input_count", 0) for record in algorithm_surfaces) != 5:
    error("Chapter 5 excluded Maple input count differs")
if any(record.get("disposition") != "independent_replacement_for_excluded_maple" for record in algorithm_surfaces):
    error("Chapter 5 algorithm closure does not exclusively use independent replacements")
for surface in learning_surfaces:
    for side in ("source", "target"):
        content = normalized_slice(surface[f"{side}_path"], surface[f"{side}_line_start"], surface[f"{side}_line_end"])
        if len(content) != surface.get(f"{side}_bytes"):
            error(f"{surface.get('id')}: {side} learning-surface byte count mismatch")
        if sha256(content) != surface.get(f"{side}_content_sha256"):
            error(f"{surface.get('id')}: {side} learning-surface hash mismatch")

assets = [record for record in ch05_records if record.get("entity_type") == "asset"]
if {record["id"] for record in assets} != EXPECTED_ASSET_IDS:
    error("Chapter 5 asset stable-ID closure differs")
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

rights_records = [record for record in ch05_records if record.get("entity_type") == "rights"]
if {record["id"] for record in rights_records} != EXPECTED_RIGHTS_IDS:
    error("Chapter 5 rights stable-ID closure differs")
if {record.get("component_id") for record in rights_records} != EXPECTED_RIGHTS_COMPONENT_IDS:
    error("Chapter 5 rights component closure differs")
maple_rights = ids.get("rights.o015-penn-ch05-maple-excluded", {})
if maple_rights.get("status") != "excluded" or maple_rights.get("translation_permitted") is not False:
    error("Chapter 5 excluded Maple rights record differs")

try:
    with COMPONENT_RIGHTS_PATH.open("r", encoding="utf-8", newline="") as handle:
        component_rows = list(csv.DictReader(handle))
    component_by_id = {row.get("component_id"): row for row in component_rows}
    if not EXPECTED_LIVE_COMPONENT_IDS.issubset(component_by_id):
        error("live component-rights table lacks Chapter 5 closure rows")
    if component_by_id.get("o015-penn-maple", {}).get("status") != "excluded":
        error("live component-rights table does not exclude Penn Maple")
    if component_by_id.get("o015-backend-tooling", {}).get("path") != "qa/extend_backend_penn_ch05.py + qa/validate_backend_penn_ch05.py + earlier unit generators and validators":
        error("live component-rights table lacks exact Chapter 5 tooling binding")
except (OSError, csv.Error) as exc:
    error(f"cannot validate live component-rights table: {exc}")

corrections = sorted(
    [record for record in ch05_records if record.get("entity_type") == "correction"],
    key=lambda item: item.get("source_event_id", ""),
)
if [record.get("source_event_id") for record in corrections] != EXPECTED_EVENT_IDS:
    error("Chapter 5 correction event closure is not exactly 0038..0049")
try:
    proposed_records = [
        json.loads(line)
        for line in PROPOSED_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]
except (OSError, json.JSONDecodeError) as exc:
    error(f"cannot read Chapter 5 proposed ledger: {exc}")
    proposed_records = []
if [record.get("event_id") for record in proposed_records] != EXPECTED_EVENT_IDS:
    error("Chapter 5 proposed-ledger event closure differs")
proposal_by_id = {record.get("event_id"): record for record in proposed_records}
for correction in corrections:
    event_id = correction.get("source_event_id")
    proposal = proposal_by_id.get(event_id, {})
    if correction.get("evidence_artifact_id") != "artifact.o015.adverse-ledger":
        error(f"{correction.get('id')}: correction is not shared-ledger-bound")
    if correction.get("proposal_artifact_id") != "artifact.penn.proposed-ledger-ch05":
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
        error("Chapter 5 proposed records are not the exact shared-ledger tail")
except (OSError, json.JSONDecodeError) as exc:
    error(f"cannot validate shared adverse ledger: {exc}")

artifact_records = [record for record in ch05_records if record.get("entity_type") == "artifact"]
if {record["id"] for record in artifact_records} != EXPECTED_ARTIFACT_IDS:
    error("Chapter 5 artifact stable-ID closure differs")
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

qa_records = [record for record in ch05_records if record.get("entity_type") == "qa_event"]
actual_qa_suffixes = {record["id"].removeprefix("qa.o015.penn-ch05.") for record in qa_records}
if actual_qa_suffixes != EXPECTED_QA_SUFFIXES:
    error("Chapter 5 QA stable-ID closure differs")
qa_by_suffix = {record["id"].removeprefix("qa.o015.penn-ch05."): record for record in qa_records}
for suffix in EXPECTED_QA_SUFFIXES - {"language", "accessibility"}:
    if qa_by_suffix.get(suffix, {}).get("result") != "pass":
        error(f"Chapter 5 {suffix} QA is not pass")
if qa_by_suffix.get("language", {}).get("result") != "not_recorded":
    error("Chapter 5 language-review gap is not explicit")
if qa_by_suffix.get("accessibility", {}).get("result") != "pass_with_limitation":
    error("Chapter 5 accessibility limitation is not explicit")

relation_records = [record for record in ch05_records if record.get("entity_type") == "relation"]
if {record["id"] for record in relation_records} != EXPECTED_RELATION_IDS:
    error("Chapter 5 relation stable-ID closure differs")

chapter_unit = ids.get(UNIT_ID, {})
expected_unit_fields = {
    "parent_id": "unit.penn.v1",
    "order": 5,
    "edition_id": SOURCE_EDITION_ID,
    "source_edition_id": SOURCE_EDITION_ID,
    "target_edition_id": TARGET_EDITION_ID,
    "rights_id": "rights.o015-penn-id-ch05",
    "admission_state": "admitted_reader",
    "translation_state": "built",
    "publication_state": "unpublished_working_edition",
    "next_source_order_unit": "Section6.tex:1",
}
for field, expected in expected_unit_fields.items():
    if chapter_unit.get(field) != expected:
        error(f"{UNIT_ID}: {field} differs")

source_text = source_data.decode("utf-8") if source_data else ""
target_text = target_data.decode("utf-8") if target_data else ""
if source_text.count(r"\lstinputlisting") != 5:
    error("Chapter 5 source no longer has exactly five listing calls")
if r"\lstinputlisting" in target_text or "Code/" in target_text:
    error("Chapter 5 target retains an excluded legacy code dependency")
try:
    wrapper_text = (ROOT / WRAPPER_PATH).read_text(encoding="utf-8")
except (OSError, UnicodeDecodeError) as exc:
    error(f"cannot read Chapter 5 wrapper: {exc}")
    wrapper_text = ""
if "CC BY-NC-SA 3.0 US" not in wrapper_text:
    error("Chapter 5 wrapper lacks exact rights expression")
if "tidak" not in wrapper_text.lower() or "mendukung" not in wrapper_text.lower():
    error("Chapter 5 wrapper lacks non-endorsement notice")

try:
    structure = json.loads((ROOT / "qa/PENN_CH05_STRUCTURE_REPORT.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    error(f"cannot validate Chapter 5 structure report: {exc}")
    structure = {}
if structure.get("status") != "PASS" or structure.get("failures", []) != []:
    error("Chapter 5 structure report is not clean PASS")
if len(structure.get("gates", [])) != 17 or not all(gate.get("pass") is True for gate in structure.get("gates", [])):
    error("Chapter 5 structure report gate closure differs")
formula_inventory = structure.get("formula_inventory", {})
if len(formula_inventory.get("source", [])) != 35 or len(formula_inventory.get("target", [])) != 35:
    error("Chapter 5 displayed-formula inventory count differs")
if [item.get("environment") for item in formula_inventory.get("source", [])] != [item.get("environment") for item in formula_inventory.get("target", [])]:
    error("Chapter 5 displayed-formula environment sequence differs")

try:
    solver = json.loads((ROOT / "qa/PENN_CH05_SOLVER_RESULTS.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    error(f"cannot validate Chapter 5 solver result: {exc}")
    solver = {}
if solver.get("status") != "PASS" or solver.get("failures", []) != []:
    error("Chapter 5 solver result is not clean PASS")
if len(solver.get("gates", [])) != 7 or not all(gate.get("pass") is True for gate in solver.get("gates", [])):
    error("Chapter 5 solver gate closure differs")

try:
    visual = json.loads((ROOT / "qa/PENN_CH05_VISUAL_QA.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    error(f"cannot validate Chapter 5 visual result: {exc}")
    visual = {}
if visual.get("inspection", {}).get("result") != "pass":
    error("Chapter 5 visual receipt is not pass")
if visual.get("pdf", {}).get("pages") != 15 or visual.get("pdf", {}).get("searchable_pages") != 15:
    error("Chapter 5 visual/searchability page closure differs")
if visual.get("pdf", {}).get("font_resources_without_tounicode") != 0:
    error("Chapter 5 font Unicode-map closure differs")

try:
    rereview_text = (ROOT / "qa/PENN_CH05_INDEPENDENT_REREVIEW.md").read_text(encoding="utf-8")
except (OSError, UnicodeDecodeError) as exc:
    error(f"cannot validate Chapter 5 rereview: {exc}")
    rereview_text = ""
for phrase in ("Disposition: **PASS", "| Remaining after the narrow corrections below | 0 | 0 | 0 |"):
    if phrase not in rereview_text:
        error(f"Chapter 5 rereview lacks required phrase: {phrase}")

try:
    source_audit_text = (ROOT / "00_control/PENN_CH05_SOURCE_AUDIT.md").read_text(encoding="utf-8")
except (OSError, UnicodeDecodeError) as exc:
    error(f"cannot validate Chapter 5 source audit: {exc}")
    source_audit_text = ""
for phrase in ("Reader admission: PASS", "The lawful complete Chapter 5 reader passes"):
    if phrase not in source_audit_text:
        error(f"Chapter 5 source audit lacks required phrase: {phrase}")

try:
    log_text = (ROOT / "build/penn-unit-05-id/D90-PENN-05-metode-newton-dan-koreksi-id.log").read_text(encoding="utf-8", errors="replace")
except OSError as exc:
    error(f"cannot validate Chapter 5 build log: {exc}")
    log_text = ""
build_blockers = [
    pattern for pattern in (
        "LaTeX Error",
        "Undefined control sequence",
        "There were undefined references",
        "Citation " + chr(96),
        "Overfull \\hbox",
        "Missing character",
        "Rerun to get cross-references right",
    ) if pattern in log_text
]
output_match = re.search(r"Output written on .*?\((\d+) pages?", log_text, re.DOTALL)
if (int(output_match.group(1)) if output_match else 0) != 15:
    error("Chapter 5 build-log page count differs")
if build_blockers:
    error(f"Chapter 5 build blockers present: {build_blockers}")
if log_text.count("Underfull \\hbox") != 1 or "at lines 397--397" not in log_text:
    error("Chapter 5 accepted underfull-caption warning closure differs")

try:
    overlap_text = COVERAGE_OVERLAP_PATH.read_text(encoding="utf-8")
except (OSError, UnicodeDecodeError) as exc:
    error(f"cannot read coverage-overlap control: {exc}")
    overlap_text = ""
for phrase in (
    "Habring Chapters 3--9 and Penn Chapters 3--5 form an admitted optional numerical/modern-algorithm companion.",
    "Newton, globalization, and modified-Cholesky correction.",
    "O018 / D130 owns LP/MIP modelling",
    "Fourteen Penn Maple/legacy listing inputs encountered through Chapter 5 remain excluded",
    "No automatic Penn source-order expansion continues after the Chapter 5 preservation boundary.",
):
    if phrase not in overlap_text:
        error(f"coverage-overlap control lacks required phrase: {phrase}")

report = {
    "authorized_refreshed_baseline_ids": sorted(AUTHORIZED_REFRESH_SPECS),
    "baseline": {
        "artifact_record_count": len(baseline_artifacts),
        "artifact_record_set_sha256": record_set_sha256(baseline_artifacts),
        "immutable_artifact_record_count": len(immutable_baseline_artifacts),
        "immutable_artifact_record_set_sha256": record_set_sha256(immutable_baseline_artifacts),
        "record_count": len(baseline_records),
        "record_set_sha256": record_set_sha256(baseline_records),
        "semantic_record_count": len(baseline_semantic),
        "semantic_record_set_sha256": record_set_sha256(baseline_semantic),
        "unchanged": not any("baseline" in message for message in errors),
    },
    "csv_bytes": len(csv_bytes),
    "csv_sha256": sha256(csv_bytes),
    "entity_counts": dict(sorted(Counter(record.get("entity_type") for record in records).items())),
    "errors": errors,
    "jsonl_bytes": len(jsonl_bytes),
    "jsonl_sha256": sha256(jsonl_bytes),
    "penn_ch05_entity_counts": ch05_entity_counts,
    "penn_ch05_record_count": len(ch05_records),
    "penn_ch05_record_set_sha256": record_set_sha256(ch05_records),
    "record_count": len(records),
    "result": "pass" if not errors else "fail",
    "schema_bytes": len(schema_bytes),
    "schema_sha256": sha256(schema_bytes),
    "segment_count": len(segments),
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
sys.exit(0 if not errors else 1)
