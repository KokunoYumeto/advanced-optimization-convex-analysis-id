#!/usr/bin/env python3
"""Validate deterministic O015 backend exports through Habring Chapter 9."""

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


def record_set_sha256(record_set: list[dict[str, Any]]) -> str:
    """Hash a stable-ID-sorted set of canonical records."""

    payload = "".join(
        canonical_json(record) + "\n"
        for record in sorted(record_set, key=lambda item: item["id"])
    ).encode("utf-8")
    return sha256(payload)


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


def read_json_object(relative: str) -> dict[str, Any]:
    path = local_path(relative)
    if path is None:
        return {}
    _, text = read_utf8_lf(path)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        error(f"invalid JSON object {relative}: {exc}")
        return {}
    if not isinstance(value, dict):
        error(f"JSON witness is not an object: {relative}")
        return {}
    return value


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

# The Chapter 9 extension is permitted to add only this exact semantic closure.
# Re-hashing the filtered Chapter 3--8 baseline makes the validator independent
# of the generator's own baseline-preservation assertion.
generated_ch09_concept_ids = {
    "concept.measurable-probability-space",
    "concept.pushforward-measure",
    "concept.monge-optimal-transport",
    "concept.transport-coupling",
    "concept.kantorovich-optimal-transport",
    "concept.kantorovich-existence",
    "concept.wasserstein-distance",
    "concept.kantorovich-duality",
    "concept.discrete-optimal-transport",
    "concept.entropic-optimal-transport",
    "concept.entropic-plan-factorization",
    "concept.sinkhorn-knopp-algorithm",
}
generated_ch09_term_ids = {
    "term.optimal-transport",
    "term.pushforward-measure",
    "term.monge-optimal-transport",
    "term.kantorovich-optimal-transport",
    "term.transport-plan",
    "term.coupling",
    "term.wasserstein-distance",
    "term.kantorovich-duality",
    "term.transport-polytope",
    "term.entropic-regularization",
    "term.gibbs-kernel",
    "term.sinkhorn-knopp-algorithm",
}
generated_ch09_exact_ids = {
    "unit.habring.v1.ch09",
    "rights.o015-habring-ch09-source",
    "rights.o015-habring-id-ch09",
    "rights.o015-habring-ch09-inline-tikz",
    "rights.o015-habring-ch09-local-bibliography",
    "rights.o015-optimal-transport-solver-validation",
    "relation.unit.root-contains-ch09",
    "relation.unit.ch08-precedes-ch09",
    "artifact.o015.backend-generator-ch09",
    "asset.habring.v1.ch09.transport-map-tikz",
    "asset.habring.v1.ch09.local-bibliography",
}
baseline_refresh_artifact_ids = {
    "artifact.o015.adverse-ledger",
    "artifact.o015.component-rights",
    "artifact.o015.coverage-overlap",
    "artifact.o015.backend-validator",
}


def is_generated_ch09(record: dict[str, Any]) -> bool:
    record_id = record.get("id", "")
    if record_id in (
        generated_ch09_concept_ids
        | generated_ch09_term_ids
        | generated_ch09_exact_ids
    ):
        return True
    if record_id.startswith(
        (
            "d90.hab.v1.ch09.",
            "surface.habring.v1.ch09.",
            "qa.o015.ch09.",
            "relation.unit.ch09-",
            "relation.segment.ch09-",
            "relation.surface.ch09-",
            "relation.artifact.ch09-",
        )
    ):
        return True
    if record_id.startswith("artifact.habring.") and record_id.endswith("-ch09"):
        return True
    if record_id.startswith("correction.o015-hab-adv-"):
        suffix = record_id.rsplit("-", 1)[-1]
        return suffix.isdigit() and 84 <= int(suffix) <= 96
    return False


ch09_records = [record for record in records if is_generated_ch09(record)]
baseline_records = [record for record in records if not is_generated_ch09(record)]
if len(ch09_records) != 123:
    error(f"Chapter 9 closure has {len(ch09_records)} records, expected 123")
if len(baseline_records) != 670:
    error(f"pre-Chapter 9 baseline has {len(baseline_records)} records, expected 670")
for record in ch09_records:
    if record.get("recorded_at") != "2026-08-22T16:45:00Z":
        error(f"{record.get('id')}: wrong deterministic Chapter 9 recorded_at")
    if record.get("responsible_workflow") != "o015-habring-ch09-backend-v1":
        error(f"{record.get('id')}: wrong Chapter 9 responsible workflow")

expected_ch09_added_counts = {
    "artifact": 15,
    "asset": 2,
    "concept": 12,
    "correction": 13,
    "learning_surface": 6,
    "qa_event": 10,
    "relation": 38,
    "rights": 5,
    "segment": 9,
    "term": 12,
    "unit": 1,
}
actual_ch09_added_counts = dict(
    sorted(Counter(record.get("entity_type") for record in ch09_records).items())
)
if actual_ch09_added_counts != expected_ch09_added_counts:
    error(
        "wrong Chapter 9 entity closure: "
        f"expected {expected_ch09_added_counts}, found {actual_ch09_added_counts}"
    )

baseline_semantic_records = [
    record for record in baseline_records if record.get("entity_type") != "artifact"
]
if len(baseline_semantic_records) != 590:
    error("pre-Chapter 9 semantic baseline does not contain 590 records")
if record_set_sha256(baseline_semantic_records) != (
    "2bc20fde0fe93ae57ab9c7fbd0f78d3c36267f4381371cd0146ebdca382481cd"
):
    error("pre-Chapter 9 semantic baseline differs from the admitted 590-record set")

baseline_immutable_artifacts = [
    record
    for record in baseline_records
    if record.get("entity_type") == "artifact"
    and record.get("id") not in baseline_refresh_artifact_ids
]
if len(baseline_immutable_artifacts) != 76:
    error("pre-Chapter 9 immutable artifact baseline does not contain 76 records")
if record_set_sha256(baseline_immutable_artifacts) != (
    "58c9a07db46856b4934e6adb4edeb0231b0308f885fdd284a320e1df20d7cc84"
):
    error("pre-Chapter 9 immutable artifact records were changed")

baseline_refresh_artifacts = [
    record
    for record in baseline_records
    if record.get("id") in baseline_refresh_artifact_ids
]
if {record.get("id") for record in baseline_refresh_artifacts} != baseline_refresh_artifact_ids:
    error("pre-Chapter 9 refreshable artifact closure differs")
baseline_refresh_skeletons: list[dict[str, Any]] = []
for record in baseline_refresh_artifacts:
    skeleton = dict(record)
    skeleton.pop("bytes", None)
    skeleton.pop("sha256", None)
    baseline_refresh_skeletons.append(skeleton)
if record_set_sha256(baseline_refresh_skeletons) != (
    "9c541a5c609c1a8ed8512b01baead858d94a29ad5f18084f773c698c4ac62dc4"
):
    error("pre-Chapter 9 refreshable artifact metadata changed beyond bytes/SHA-256")

segments = [record for record in records if record.get("entity_type") == "segment"]
expected_segment_counts = {
    "unit.habring.v1.ch03": 11,
    "unit.habring.v1.ch04": 8,
    "unit.habring.v1.ch05": 8,
    "unit.habring.v1.ch06": 12,
    "unit.habring.v1.ch07": 11,
    "unit.habring.v1.ch08": 3,
    "unit.habring.v1.ch09": 9,
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

# Every admitted unit has the common nine-event evidence topology; Chapter 9
# additionally carries a dedicated corrected-bibliography event.  Expected
# accessibility results remain data-driven because Chapter 3 predates the
# explicit untagged-PDF limitation used by later units.
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
    "unit.habring.v1.ch06": {
        "qa_prefix": "qa.o015.ch06",
        "accessibility_result": "pass_with_limitation",
        "correction_range": range(39, 50),
    },
    "unit.habring.v1.ch07": {
        "qa_prefix": "qa.o015.ch07",
        "accessibility_result": "pass_with_limitation",
        "correction_range": range(50, 76),
    },
    "unit.habring.v1.ch08": {
        "qa_prefix": "qa.o015.ch08",
        "accessibility_result": "pass_with_limitation",
        "correction_range": range(76, 84),
    },
    "unit.habring.v1.ch09": {
        "qa_prefix": "qa.o015.ch09",
        "accessibility_result": "pass_with_limitation",
        "correction_range": range(84, 97),
        "extra_qa_suffixes": {"bibliography"},
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
    expected_qa_ids = {
        f"{prefix}.{suffix}"
        for suffix in qa_suffixes | closure.get("extra_qa_suffixes", set())
    }
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

for reviewed_unit_id in (
    "unit.habring.v1.ch05",
    "unit.habring.v1.ch06",
    "unit.habring.v1.ch07",
    "unit.habring.v1.ch08",
    "unit.habring.v1.ch09",
):
    for segment in segments_by_unit.get(reviewed_unit_id, []):
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

required_ch06_ids = {
    "unit.habring.v1.ch06",
    "artifact.habring.source-ch06",
    "artifact.habring.target-ch06",
    "artifact.habring.target-wrapper-ch06",
    "artifact.habring.structure-report-ch06",
    "artifact.habring.structure-audit-ch06",
    "artifact.habring.solver-results-ch06",
    "artifact.habring.solver-validator-ch06",
    "artifact.habring.build-log-ch06",
    "artifact.habring.target-pdf-ch06",
    "artifact.habring.target-text-ch06",
    "artifact.o015.backend-generator-ch06",
    "rights.o015-habring-ch06-source",
    "rights.o015-habring-id-ch06",
    "rights.o015-acceleration-solver-validation",
    "surface.habring.v1.ch06.prompt01",
    "surface.habring.v1.ch06.hint-inventory",
    "surface.habring.v1.ch06.answer-inventory",
    "surface.habring.v1.ch06.solution-inventory",
    "relation.unit.root-contains-ch06",
    "relation.unit.ch05-precedes-ch06",
    "relation.unit.ch06-depends-on-ch05",
    "relation.segment.ch06-seg0003-proves-gelfand",
    "relation.segment.ch06-seg0007-proves-heavy-ball-minimax",
    "relation.segment.ch06-seg0010-proves-fundamental-inequality",
    "relation.segment.ch06-seg0012-proves-fista-rate",
    "relation.surface.ch06-prompt01-exercises-heavy-ball-minimax",
}
expected_ch06_concepts = {
    "concept.first-order-complexity-lower-bound",
    "concept.gradient-flow",
    "concept.polyak-heavy-ball-method",
    "concept.inertial-gradient-step",
    "concept.spectral-radius",
    "concept.gelfand-spectral-radius-formula",
    "concept.spectral-radius-stability",
    "concept.heavy-ball-linearization",
    "concept.schur-jury-stability",
    "concept.heavy-ball-local-convergence",
    "concept.heavy-ball-minimax-parameters",
    "concept.nesterov-acceleration",
    "concept.fista",
    "concept.fista-momentum-sequence",
    "concept.fundamental-proximal-gradient-inequality",
    "concept.fista-rate",
}
expected_ch06_terms = {
    "term.first-order-method",
    "term.gradient-flow",
    "term.polyak-heavy-ball-method",
    "term.inertia-term",
    "term.spectral-radius",
    "term.jordan-normal-form",
    "term.schur-jury-criterion",
    "term.worst-case-spectral-radius",
    "term.nesterov-acceleration",
    "term.fista",
    "term.fast-proximal-gradient-method",
    "term.inertia-parameter",
    "term.fundamental-proximal-gradient-inequality",
}
for required_id in sorted(
    required_ch06_ids | expected_ch06_concepts | expected_ch06_terms
):
    if required_id not in ids:
        error(f"Chapter 6 closure is missing {required_id}")

expected_ch06_segment_concepts = {
    "d90.hab.v1.ch06.seg0001": ["concept.first-order-complexity-lower-bound"],
    "d90.hab.v1.ch06.seg0002": ["concept.gradient-flow", "concept.polyak-heavy-ball-method", "concept.inertial-gradient-step"],
    "d90.hab.v1.ch06.seg0003": ["concept.spectral-radius", "concept.gelfand-spectral-radius-formula"],
    "d90.hab.v1.ch06.seg0004": ["concept.spectral-radius-stability"],
    "d90.hab.v1.ch06.seg0005": ["concept.heavy-ball-local-convergence", "concept.heavy-ball-minimax-parameters"],
    "d90.hab.v1.ch06.seg0006": ["concept.heavy-ball-linearization"],
    "d90.hab.v1.ch06.seg0007": ["concept.schur-jury-stability", "concept.heavy-ball-local-convergence", "concept.heavy-ball-minimax-parameters"],
    "d90.hab.v1.ch06.seg0008": ["concept.nesterov-acceleration", "concept.fista"],
    "d90.hab.v1.ch06.seg0009": ["concept.fista-momentum-sequence"],
    "d90.hab.v1.ch06.seg0010": ["concept.fundamental-proximal-gradient-inequality"],
    "d90.hab.v1.ch06.seg0011": ["concept.fista-rate"],
    "d90.hab.v1.ch06.seg0012": ["concept.fista-rate", "concept.fundamental-proximal-gradient-inequality"],
}
for segment_id, expected_concepts in expected_ch06_segment_concepts.items():
    if ids.get(segment_id, {}).get("concept_ids") != expected_concepts:
        error(f"{segment_id}: wrong Chapter 6 concept closure")

expected_ch06_artifact_identities = {
    "artifact.habring.source-ch06": (18873, "2ff1e10e9421c0fe01a09140e3e230cb2d3728c30c572bb6ca5513b229f1e605"),
    "artifact.habring.target-ch06": (24690, "b1e27d912bc94722ec1c33257598c074eec8a6f5bf81f43b8946f85b48f4c35a"),
    "artifact.habring.target-wrapper-ch06": (5491, "46903dd6b6ff8c845624931d37d9b24fd37cd89f0bf77601ba11539c59dfd5b9"),
    "artifact.habring.structure-report-ch06": (37873, "e82f254fb7e69d498162ffcdfb70fe7d4929556351f892872bb8e65da3715b4b"),
    "artifact.habring.solver-results-ch06": (37060, "135ded1ed0f4f3ca70616822d8856a85d3747458c9ca6e765dab72a11d3b88f0"),
    "artifact.habring.build-log-ch06": (97942, "0775c19ecd2e8356e7b33bd50c30871f233e0c7d05dd703ba2ec19a4f7f560f0"),
    "artifact.habring.target-pdf-ch06": (392662, "cb9edf46d8d2582591ad3114f9a2b316073825dfd48079d12560793ad4bca0a0"),
    "artifact.habring.target-text-ch06": (37033, "d2679e94ce7e44cdcf183b17e73295b5b5093a1612b2460c0c6ecba512431cda"),
}
for artifact_id, (expected_bytes, expected_sha256) in expected_ch06_artifact_identities.items():
    artifact_record = ids.get(artifact_id, {})
    if artifact_record.get("bytes") != expected_bytes:
        error(f"{artifact_id}: wrong frozen byte count")
    if artifact_record.get("sha256") != expected_sha256:
        error(f"{artifact_id}: wrong frozen SHA-256")

ch06_structure = ids.get("qa.o015.ch06.structure", {})
for field, expected in {
    "environment_count": 99,
    "segment_count": 12,
    "label_occurrences_preserved": 7,
    "cref_occurrences_preserved": 4,
    "eqref_occurrences_preserved": 4,
}.items():
    if ch06_structure.get(field) != expected:
        error(f"Chapter 6 structure QA has wrong {field}")

ch06_formula = ids.get("qa.o015.ch06.formula-delta", {})
if ch06_formula.get("formula_delta_manifest_sha256") != (
    "886d80e0a759977c0c176d9b97e595b4c3515ecd52446a8c8b714146a9be3f4a"
):
    error("Chapter 6 formula-delta manifest is not the admitted manifest")
if ch06_formula.get("formula_delta_blocks") != 32:
    error("Chapter 6 formula-delta block count differs from 32")
if ch06_formula.get("correction_events") != 11:
    error("Chapter 6 formula QA does not close 11 corrections")

ch06_pdf = ids.get("artifact.habring.target-pdf-ch06", {})
if ch06_pdf.get("pages") != 15:
    error("Chapter 6 PDF artifact does not record 15 pages")
if ch06_pdf.get("accessibility") != "searchable id-ID PDF; untagged":
    error("Chapter 6 PDF accessibility limitation is not explicit")
ch06_build = ids.get("qa.o015.ch06.build", {})
if ch06_build.get("deterministic_rebuild") != "byte-identical":
    error("Chapter 6 build does not record a byte-identical rebuild")
ch06_visual = ids.get("qa.o015.ch06.visual", {})
if ch06_visual.get("localization_check") != (
    "Equation cross-reference names render in Indonesian."
):
    error("Chapter 6 visual QA does not close equation-reference localization")
ch06_prompt = ids.get("surface.habring.v1.ch06.prompt01", {})
if ch06_prompt.get("disposition") != (
    "promoted_source_editorial_todo_to_rendered_self_study_verification_prompt"
):
    error("Chapter 6 informal verification prompt disposition differs")

required_ch07_ids = {
    "unit.habring.v1.ch07",
    "artifact.habring.source-ch07",
    "artifact.habring.target-ch07",
    "artifact.habring.target-wrapper-ch07",
    "artifact.habring.structure-report-ch07",
    "artifact.habring.formula-manifest-ch07",
    "artifact.habring.structure-audit-ch07",
    "artifact.habring.solver-results-ch07",
    "artifact.habring.solver-validator-ch07",
    "artifact.habring.proposed-ledger-ch07",
    "artifact.habring.worklog-ch07",
    "artifact.habring.build-log-ch07",
    "artifact.habring.target-pdf-ch07",
    "artifact.habring.target-text-ch07",
    "artifact.o015.backend-generator-ch07",
    "rights.o015-habring-ch07-source",
    "rights.o015-habring-id-ch07",
    "rights.o015-duality-solver-validation",
    "relation.unit.root-contains-ch07",
    "relation.unit.ch06-precedes-ch07",
    "relation.unit.ch07-depends-on-ch05",
    "relation.segment.ch07-seg0003-proves-fenchel-moreau",
    "relation.segment.ch07-seg0005-proves-fenchel-rockafellar",
    "relation.segment.ch07-seg0008-proves-pdhg-rate",
    "relation.segment.ch07-seg0011-proves-admm-convergence",
}
required_ch07_ids.update(
    f"surface.habring.v1.ch07.prompt{order:02d}" for order in range(1, 6)
)
required_ch07_ids.update(
    f"surface.habring.v1.ch07.{surface_type}-inventory"
    for surface_type in ("hint", "answer", "solution")
)
expected_ch07_concepts = {
    "concept.fenchel-conjugate",
    "concept.support-function",
    "concept.fenchel-inequality",
    "concept.biconjugate",
    "concept.fenchel-moreau-theorem",
    "concept.gamma-regularization",
    "concept.fenchel-subgradient-equivalence",
    "concept.moreau-decomposition",
    "concept.fenchel-rockafellar-duality",
    "concept.saddle-point",
    "concept.primal-dual-gap",
    "concept.arrow-hurwicz-method",
    "concept.pdhg",
    "concept.pdhg-one-step-inequality",
    "concept.pdhg-ergodic-rate",
    "concept.augmented-lagrangian",
    "concept.admm",
    "concept.admm-stationarity",
    "concept.admm-lyapunov-function",
    "concept.admm-convergence",
}
expected_ch07_terms = {
    "term.fenchel-conjugate",
    "term.support-function",
    "term.fenchel-inequality",
    "term.biconjugate",
    "term.gamma-regularization",
    "term.moreau-identity",
    "term.fenchel-rockafellar-duality",
    "term.strong-duality",
    "term.saddle-point",
    "term.primal-dual-gap",
    "term.arrow-hurwicz-method",
    "term.primal-dual-hybrid-gradient",
    "term.chambolle-pock-method",
    "term.ergodic-average",
    "term.augmented-lagrangian",
    "term.admm",
    "term.primal-residual",
    "term.lyapunov-functional",
}
for required_id in sorted(
    required_ch07_ids | expected_ch07_concepts | expected_ch07_terms
):
    if required_id not in ids:
        error(f"Chapter 7 closure is missing {required_id}")

expected_ch07_segment_concepts = {
    "d90.hab.v1.ch07.seg0001": ["concept.fenchel-conjugate", "concept.support-function"],
    "d90.hab.v1.ch07.seg0002": ["concept.fenchel-conjugate", "concept.fenchel-inequality", "concept.biconjugate"],
    "d90.hab.v1.ch07.seg0003": ["concept.biconjugate", "concept.fenchel-moreau-theorem", "concept.gamma-regularization"],
    "d90.hab.v1.ch07.seg0004": ["concept.fenchel-subgradient-equivalence", "concept.moreau-decomposition"],
    "d90.hab.v1.ch07.seg0005": ["concept.fenchel-rockafellar-duality"],
    "d90.hab.v1.ch07.seg0006": ["concept.saddle-point", "concept.primal-dual-gap", "concept.moreau-decomposition"],
    "d90.hab.v1.ch07.seg0007": ["concept.arrow-hurwicz-method", "concept.pdhg"],
    "d90.hab.v1.ch07.seg0008": ["concept.pdhg-one-step-inequality", "concept.pdhg-ergodic-rate"],
    "d90.hab.v1.ch07.seg0009": ["concept.augmented-lagrangian", "concept.admm", "concept.admm-stationarity"],
    "d90.hab.v1.ch07.seg0010": ["concept.admm-convergence", "concept.admm-stationarity", "concept.admm-lyapunov-function"],
    "d90.hab.v1.ch07.seg0011": ["concept.admm-lyapunov-function", "concept.admm-convergence"],
}
for segment_id, expected_concepts in expected_ch07_segment_concepts.items():
    if ids.get(segment_id, {}).get("concept_ids") != expected_concepts:
        error(f"{segment_id}: wrong Chapter 7 concept closure")

expected_ch07_artifact_identities = {
    "artifact.habring.source-ch07": (30761, "0b112dee2582813cec5629c02df1dda329f690f944b60f4694b1c5762129bea9"),
    "artifact.habring.target-ch07": (35428, "11e9ad614f7ac4e3107e78bc3bed03a6d4acfe22f2a65fca26433b0ae3209fd9"),
    "artifact.habring.target-wrapper-ch07": (8615, "3b6e710e37c07cc9ec82ca919451c313c52fa762d58c7b01c6792a78a0098797"),
    "artifact.habring.structure-report-ch07": (32121, "fd909b00e4274a31c9e9c707cbb9039d5e03233876d0c0094c66c1049802307f"),
    "artifact.habring.formula-manifest-ch07": (81046, "fe72e72d0223117a0b34727d235ced9b6bf2af17cf48154e6b670d2ce75d89fb"),
    "artifact.habring.structure-audit-ch07": (36689, "4e29ad8cc208ab35f35e8dfc2bb323343977e7badcaed7aa7d8cfa75392cf35b"),
    "artifact.habring.solver-results-ch07": (10830, "9ceeadd90b4868f600241301813a8f24c1d1279690abc8cbf96baa3faf62f3c3"),
    "artifact.habring.solver-validator-ch07": (45213, "127bed94abe4b506ebd999a46ea71b31457f2f4cc65c7fdd7cd4efcc60569c5b"),
    "artifact.habring.proposed-ledger-ch07": (15830, "57dbba9afdee2fc453dde9fbb97621c1a6897ff5377c1ec6a210827a8dce675d"),
    "artifact.habring.worklog-ch07": (12235, "35ff60e24abc6550aa21745b9522811e7a084ab1f6ff481226f278deabe84c45"),
    "artifact.habring.build-log-ch07": (105821, "795b594b1c78e0a0769fe6b7f292fea0d6ddc81a054cad00a4d857da0cab217d"),
    "artifact.habring.target-pdf-ch07": (445733, "c4354e1e1366bdb20cebb9c6eca26fba172d6d82a6ad22dd9e2e470da2baeb6e"),
    "artifact.habring.target-text-ch07": (53128, "b473c80434a35ec607c6a9b9da3dcc31e3d5a3a233ae1f7da72293a87d65a544"),
}
for artifact_id, (expected_bytes, expected_sha256) in expected_ch07_artifact_identities.items():
    artifact_record = ids.get(artifact_id, {})
    if artifact_record.get("bytes") != expected_bytes:
        error(f"{artifact_id}: wrong frozen byte count")
    if artifact_record.get("sha256") != expected_sha256:
        error(f"{artifact_id}: wrong frozen SHA-256")

ch07_structure = ids.get("qa.o015.ch07.structure", {})
for field, expected in {
    "environment_count": 148,
    "segment_count": 11,
    "label_occurrences": 24,
    "target_unique_labels": 24,
    "Cref_occurrences_preserved": 1,
    "cref_occurrences_preserved": 3,
    "eqref_occurrences_preserved": 21,
    "ref_occurrences_preserved": 9,
    "citations_preserved": 2,
    "footnotes_preserved": 1,
    "reader_prompts_preserved": 5,
}.items():
    if ch07_structure.get(field) != expected:
        error(f"Chapter 7 structure QA has wrong {field}")

ch07_formula = ids.get("qa.o015.ch07.formula-delta", {})
if ch07_formula.get("formula_delta_manifest_sha256") != (
    "fe72e72d0223117a0b34727d235ced9b6bf2af17cf48154e6b670d2ce75d89fb"
):
    error("Chapter 7 formula-delta manifest is not the admitted manifest")
for field, expected in {
    "source_formula_surfaces": 254,
    "target_formula_surfaces": 296,
    "formula_delta_blocks": 49,
    "substantive_formula_delta_blocks": 43,
    "correction_events": 26,
}.items():
    if ch07_formula.get(field) != expected:
        error(f"Chapter 7 formula QA has wrong {field}")

ch07_pdf = ids.get("artifact.habring.target-pdf-ch07", {})
if ch07_pdf.get("pages") != 21:
    error("Chapter 7 PDF artifact does not record 21 pages")
if ch07_pdf.get("accessibility") != "searchable id-ID PDF; untagged":
    error("Chapter 7 PDF accessibility limitation is not explicit")
ch07_build = ids.get("qa.o015.ch07.build", {})
if ch07_build.get("deterministic_rebuild") != "byte-identical":
    error("Chapter 7 build does not record a byte-identical rebuild")
for field in (
    "errors",
    "undefined_references",
    "multiply_defined_labels",
    "replacement_glyphs",
    "overfull_boxes",
    "underfull_boxes",
):
    expected = [] if field == "errors" else 0
    if ch07_build.get(field) != expected:
        error(f"Chapter 7 build QA has wrong {field}")
for order in range(1, 6):
    prompt_id = f"surface.habring.v1.ch07.prompt{order:02d}"
    if ids.get(prompt_id, {}).get("disposition") != "retained_visible_self_study_prompt":
        error(f"{prompt_id}: wrong prompt disposition")

required_ch08_ids = {
    "unit.habring.v1.ch08",
    "artifact.habring.source-ch08",
    "artifact.habring.target-ch08",
    "artifact.habring.target-wrapper-ch08",
    "artifact.habring.structure-report-ch08",
    "artifact.habring.formula-manifest-ch08",
    "artifact.habring.structure-audit-ch08",
    "artifact.habring.solver-results-ch08",
    "artifact.habring.solver-validator-ch08",
    "artifact.habring.proposed-ledger-ch08",
    "artifact.habring.worklog-ch08",
    "artifact.habring.build-log-ch08",
    "artifact.habring.target-pdf-ch08",
    "artifact.habring.target-text-ch08",
    "artifact.o015.backend-generator-ch08",
    "rights.o015-habring-ch08-source",
    "rights.o015-habring-id-ch08",
    "rights.o015-stochastic-solver-validation",
    "relation.unit.root-contains-ch08",
    "relation.unit.ch07-precedes-ch08",
    "relation.unit.ch08-depends-on-ch04",
    "relation.segment.ch08-seg0001-defines-finite-sum",
    "relation.segment.ch08-seg0002-defines-conditional-oracle",
    "relation.segment.ch08-seg0003-proves-best-iterate",
}
required_ch08_ids.update(
    f"surface.habring.v1.ch08.{surface_type}-inventory"
    for surface_type in ("exercise", "hint", "answer", "solution", "asset")
)
expected_ch08_concepts = {
    "concept.finite-sum-optimization",
    "concept.stochastic-subgradient-oracle",
    "concept.stochastic-gradient-descent",
    "concept.conditional-stochastic-oracle",
    "concept.projected-stochastic-gradient-descent",
    "concept.stochastic-best-iterate-bound",
    "concept.stochastic-step-size-condition",
}
expected_ch08_terms = {
    "term.finite-sum-problem",
    "term.stochastic-gradient-estimator",
    "term.stochastic-gradient-descent",
    "term.iid",
    "term.filtration",
    "term.conditional-expectation",
    "term.conditional-variance",
    "term.projected-stochastic-gradient-descent",
}
for required_id in sorted(
    required_ch08_ids | expected_ch08_concepts | expected_ch08_terms
):
    if required_id not in ids:
        error(f"Chapter 8 closure is missing {required_id}")

expected_ch08_segment_concepts = {
    "d90.hab.v1.ch08.seg0001": [
        "concept.finite-sum-optimization",
        "concept.stochastic-subgradient-oracle",
        "concept.stochastic-gradient-descent",
    ],
    "d90.hab.v1.ch08.seg0002": [
        "concept.conditional-stochastic-oracle",
        "concept.projected-stochastic-gradient-descent",
        "concept.stochastic-step-size-condition",
        "concept.stochastic-best-iterate-bound",
    ],
    "d90.hab.v1.ch08.seg0003": [
        "concept.conditional-stochastic-oracle",
        "concept.projected-stochastic-gradient-descent",
        "concept.stochastic-best-iterate-bound",
        "concept.stochastic-step-size-condition",
    ],
}
for segment_id, expected_concepts in expected_ch08_segment_concepts.items():
    if ids.get(segment_id, {}).get("concept_ids") != expected_concepts:
        error(f"{segment_id}: wrong Chapter 8 concept closure")

expected_ch08_artifact_identities = {
    "artifact.habring.source-ch08": (4665, "610d11b59d8dfabbbbe6fbc509a0f9ac1727540458c67f8cd3b7bab49566a07d"),
    "artifact.habring.target-ch08": (6378, "f610aaec91aa9b76582f251458da65d25cc37a933a51da478cad13ee16e5a344"),
    "artifact.habring.target-wrapper-ch08": (5129, "d00ea41830af388c227a1054025f049a9315da6f41675573965042d320eb7428"),
    "artifact.habring.structure-report-ch08": (12202, "d44495208072e4555011dce4cf6155d434bc526574614d2683b8a97484f730dc"),
    "artifact.habring.formula-manifest-ch08": (24702, "2f9632d02071ded0c84d54ca17af019137cecfe18245d94a7e9243449c0e9fe9"),
    "artifact.habring.structure-audit-ch08": (29112, "d6a201efc1489fd8220510408bb65cf3cb56d5603b130f46287c6ec8f5be905e"),
    "artifact.habring.solver-results-ch08": (21107, "3b78aa1140a08cf811493f37496b10c2955f02bec570385dcde6480f37578f22"),
    "artifact.habring.solver-validator-ch08": (18417, "ef05e828b83ab285e5ba090dc27753cd758d5c3e1697f9c138b57bf052a7006e"),
    "artifact.habring.proposed-ledger-ch08": (5188, "a815d0211da31b21a25a3f9fd8a2c1ec5fcc7da5e7a62c980f75df40ae65d45d"),
    "artifact.habring.worklog-ch08": (7780, "ee7c755141c5fefa7054dde2f8aba7ae4e81a77672795d42afc69841916757b9"),
    "artifact.habring.build-log-ch08": (98530, "59609048d4930761a5de52f05aa65f80cf3da36dc7f64bd624c1ec539e64702c"),
    "artifact.habring.target-pdf-ch08": (346785, "c1ed028667c5df3fd0a837807e2a17bf7a9e1fa3170938853c9a96b9670fa86a"),
    "artifact.habring.target-text-ch08": (13751, "8556e8138248e163bff23d1778e1d2d782d7c0b3bfa6c1c4df5adaed439a05c6"),
}
for artifact_id, (expected_bytes, expected_sha256) in expected_ch08_artifact_identities.items():
    artifact_record = ids.get(artifact_id, {})
    if artifact_record.get("bytes") != expected_bytes:
        error(f"{artifact_id}: wrong frozen byte count")
    if artifact_record.get("sha256") != expected_sha256:
        error(f"{artifact_id}: wrong frozen SHA-256")

ch08_structure = ids.get("qa.o015.ch08.structure", {})
for field, expected in {
    "environment_count": 24,
    "segment_count": 3,
    "label_occurrences_preserved": 1,
    "eqref_occurrences_preserved": 1,
    "citations": 0,
    "figures": 0,
    "assets": 0,
    "footnotes": 0,
    "exercises": 0,
    "hints": 0,
    "answers": 0,
    "solutions": 0,
}.items():
    if ch08_structure.get(field) != expected:
        error(f"Chapter 8 structure QA has wrong {field}")
if ch08_structure.get("environment_counts") != {
    "aligned": 5,
    "cases": 2,
    "equation": 15,
    "proof": 1,
    "theorem": 1,
}:
    error("Chapter 8 structure QA has wrong environment counts")

ch08_formula = ids.get("qa.o015.ch08.formula-delta", {})
if ch08_formula.get("formula_delta_manifest_sha256") != (
    "2f9632d02071ded0c84d54ca17af019137cecfe18245d94a7e9243449c0e9fe9"
):
    error("Chapter 8 formula-delta manifest is not the admitted manifest")
for field, expected in {
    "source_formula_surfaces": 38,
    "target_formula_surfaces": 61,
    "formula_delta_blocks": 7,
    "substantive_formula_delta_blocks": 7,
    "correction_events": 8,
}.items():
    if ch08_formula.get(field) != expected:
        error(f"Chapter 8 formula QA has wrong {field}")

ch08_solver = ids.get("qa.o015.ch08.solver", {})
if ch08_solver.get("result") != "pass":
    error("Chapter 8 stochastic computation QA is not a pass")
ch08_pdf = ids.get("artifact.habring.target-pdf-ch08", {})
if ch08_pdf.get("pages") != 8:
    error("Chapter 8 PDF artifact does not record eight pages")
if ch08_pdf.get("accessibility") != "searchable id-ID PDF; untagged":
    error("Chapter 8 PDF accessibility limitation is not explicit")
ch08_build = ids.get("qa.o015.ch08.build", {})
if ch08_build.get("deterministic_rebuild") != "byte-identical":
    error("Chapter 8 build does not record a byte-identical rebuild")
for field in (
    "errors",
    "undefined_references",
    "multiply_defined_labels",
    "replacement_glyphs",
    "overfull_boxes",
    "underfull_boxes",
):
    expected = [] if field == "errors" else 0
    if ch08_build.get(field) != expected:
        error(f"Chapter 8 build QA has wrong {field}")
for surface_type in ("exercise", "hint", "answer", "solution", "asset"):
    surface_id = f"surface.habring.v1.ch08.{surface_type}-inventory"
    surface = ids.get(surface_id, {})
    if surface.get("presence") != "absent" or surface.get("count") != 0:
        error(f"{surface_id}: source absence is not explicit")

# Complete Chapter 9 closure: optimal transport, corrected bibliography,
# inline TikZ asset, resolved source exercise, and computation/build evidence.
required_ch09_ids = {
    "unit.habring.v1.ch09",
    "artifact.habring.source-ch09",
    "artifact.habring.target-ch09",
    "artifact.habring.target-wrapper-ch09",
    "artifact.habring.local-bibliography-ch09",
    "artifact.habring.structure-report-ch09",
    "artifact.habring.formula-manifest-ch09",
    "artifact.habring.structure-audit-ch09",
    "artifact.habring.solver-results-ch09",
    "artifact.habring.solver-validator-ch09",
    "artifact.habring.proposed-ledger-ch09",
    "artifact.habring.worklog-ch09",
    "artifact.habring.build-log-ch09",
    "artifact.habring.target-pdf-ch09",
    "artifact.habring.target-text-ch09",
    "artifact.o015.backend-generator-ch09",
    "rights.o015-habring-ch09-source",
    "rights.o015-habring-id-ch09",
    "rights.o015-habring-ch09-inline-tikz",
    "rights.o015-habring-ch09-local-bibliography",
    "rights.o015-optimal-transport-solver-validation",
    "asset.habring.v1.ch09.transport-map-tikz",
    "asset.habring.v1.ch09.local-bibliography",
    "surface.habring.v1.ch09.figure01",
    "surface.habring.v1.ch09.exercise01",
    "surface.habring.v1.ch09.solution01",
    "surface.habring.v1.ch09.hint-inventory",
    "surface.habring.v1.ch09.answer-inventory",
    "surface.habring.v1.ch09.asset-inventory",
}
expected_ch09_concepts = generated_ch09_concept_ids
expected_ch09_terms = generated_ch09_term_ids
for required_id in sorted(
    required_ch09_ids | expected_ch09_concepts | expected_ch09_terms
):
    if required_id not in ids:
        error(f"Chapter 9 closure is missing {required_id}")

expected_ch09_concept_prerequisites = {
    "concept.measurable-probability-space": [],
    "concept.pushforward-measure": ["concept.measurable-probability-space"],
    "concept.monge-optimal-transport": ["concept.pushforward-measure"],
    "concept.transport-coupling": ["concept.measurable-probability-space"],
    "concept.kantorovich-optimal-transport": ["concept.transport-coupling"],
    "concept.kantorovich-existence": [
        "concept.kantorovich-optimal-transport",
        "concept.lower-semicontinuity",
    ],
    "concept.wasserstein-distance": ["concept.kantorovich-optimal-transport"],
    "concept.kantorovich-duality": [
        "concept.kantorovich-optimal-transport",
        "concept.fenchel-rockafellar-duality",
    ],
    "concept.discrete-optimal-transport": ["concept.kantorovich-optimal-transport"],
    "concept.entropic-optimal-transport": [
        "concept.discrete-optimal-transport",
        "concept.strong-convexity",
    ],
    "concept.entropic-plan-factorization": ["concept.entropic-optimal-transport"],
    "concept.sinkhorn-knopp-algorithm": ["concept.entropic-plan-factorization"],
}
for concept_id, prerequisite_ids in expected_ch09_concept_prerequisites.items():
    concept = ids.get(concept_id, {})
    if concept.get("prerequisite_ids") != prerequisite_ids:
        error(f"{concept_id}: wrong prerequisite closure")
    if concept.get("domain") != "optimal transport and convex optimization":
        error(f"{concept_id}: wrong domain")

ch09_unit = ids.get("unit.habring.v1.ch09", {})
for field, expected in {
    "edition_id": "edition.habring.convex-optimization.id-id.v1",
    "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
    "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
    "parent_id": "unit.habring.v1",
    "unit_kind": "chapter",
    "order": 9,
    "source_local_id": "chapter-9",
    "source_local_label": "9 — Excursion on Optimal Transport",
    "target_local_label": "9 — Selingan tentang Transportasi Optimal",
    "source_locator": "authority/habring/source-v1/optimal_transport.tex:1-264",
    "target_locator": "source/id-ID/habring-09-transportasi-optimal-id.tex:1-352",
    "rights_id": "rights.o015-habring-id-ch09",
    "translation_state": "built",
}.items():
    if ch09_unit.get(field) != expected:
        error(f"Chapter 9 unit has wrong {field}")

expected_ch09_segment_concepts = {
    "d90.hab.v1.ch09.seg0001": ["concept.measurable-probability-space"],
    "d90.hab.v1.ch09.seg0002": ["concept.monge-optimal-transport"],
    "d90.hab.v1.ch09.seg0003": [
        "concept.pushforward-measure",
        "concept.monge-optimal-transport",
        "concept.transport-coupling",
        "concept.kantorovich-optimal-transport",
    ],
    "d90.hab.v1.ch09.seg0004": [
        "concept.kantorovich-existence",
        "concept.wasserstein-distance",
    ],
    "d90.hab.v1.ch09.seg0005": ["concept.kantorovich-duality"],
    "d90.hab.v1.ch09.seg0006": [
        "concept.kantorovich-duality",
        "concept.transport-coupling",
    ],
    "d90.hab.v1.ch09.seg0007": [
        "concept.discrete-optimal-transport",
        "concept.entropic-optimal-transport",
    ],
    "d90.hab.v1.ch09.seg0008": [
        "concept.entropic-optimal-transport",
        "concept.entropic-plan-factorization",
    ],
    "d90.hab.v1.ch09.seg0009": [
        "concept.entropic-plan-factorization",
        "concept.sinkhorn-knopp-algorithm",
    ],
}
expected_ch09_segment_ranges = {
    "d90.hab.v1.ch09.seg0001": (1, 15, 3, 17),
    "d90.hab.v1.ch09.seg0002": (16, 75, 20, 83),
    "d90.hab.v1.ch09.seg0003": (77, 110, 86, 123),
    "d90.hab.v1.ch09.seg0004": (112, 130, 126, 147),
    "d90.hab.v1.ch09.seg0005": (131, 141, 150, 163),
    "d90.hab.v1.ch09.seg0006": (142, 190, 166, 230),
    "d90.hab.v1.ch09.seg0007": (192, 226, 233, 273),
    "d90.hab.v1.ch09.seg0008": (229, 256, 276, 333),
    "d90.hab.v1.ch09.seg0009": (257, 264, 336, 352),
}
for segment_id, expected_concepts in expected_ch09_segment_concepts.items():
    segment = ids.get(segment_id, {})
    if segment.get("concept_ids") != expected_concepts:
        error(f"{segment_id}: wrong Chapter 9 concept closure")
    source_start, source_end, target_start, target_end = (
        expected_ch09_segment_ranges[segment_id]
    )
    for field, expected in {
        "source_path": "authority/habring/source-v1/optimal_transport.tex",
        "source_line_start": source_start,
        "source_line_end": source_end,
        "target_path": "source/id-ID/habring-09-transportasi-optimal-id.tex",
        "target_line_start": target_start,
        "target_line_end": target_end,
        "rights_id": "rights.o015-habring-id-ch09",
        "translation_state": "built",
        "structural_review_state": "passed",
        "mathematical_review_state": "correction_audited_solver_checked_independent_rereview_passed",
        "language_review_state": "not_recorded",
    }.items():
        if segment.get(field) != expected:
            error(f"{segment_id}: wrong {field}")

expected_ch09_term_evidence = {
    "term.optimal-transport": "d90.hab.v1.ch09.seg0001",
    "term.pushforward-measure": "d90.hab.v1.ch09.seg0003",
    "term.monge-optimal-transport": "d90.hab.v1.ch09.seg0003",
    "term.kantorovich-optimal-transport": "d90.hab.v1.ch09.seg0003",
    "term.transport-plan": "d90.hab.v1.ch09.seg0003",
    "term.coupling": "d90.hab.v1.ch09.seg0003",
    "term.wasserstein-distance": "d90.hab.v1.ch09.seg0004",
    "term.kantorovich-duality": "d90.hab.v1.ch09.seg0005",
    "term.transport-polytope": "d90.hab.v1.ch09.seg0008",
    "term.entropic-regularization": "d90.hab.v1.ch09.seg0007",
    "term.gibbs-kernel": "d90.hab.v1.ch09.seg0008",
    "term.sinkhorn-knopp-algorithm": "d90.hab.v1.ch09.seg0009",
}
expected_ch09_term_contracts = {
    "term.optimal-transport": ("concept.kantorovich-optimal-transport", "transportasi optimal"),
    "term.pushforward-measure": ("concept.pushforward-measure", "ukuran hasil dorong"),
    "term.monge-optimal-transport": ("concept.monge-optimal-transport", "transportasi optimal Monge"),
    "term.kantorovich-optimal-transport": ("concept.kantorovich-optimal-transport", "transportasi optimal Kantorovich"),
    "term.transport-plan": ("concept.transport-coupling", "rencana transportasi"),
    "term.coupling": ("concept.transport-coupling", "kopling"),
    "term.wasserstein-distance": ("concept.wasserstein-distance", "jarak Wasserstein"),
    "term.kantorovich-duality": ("concept.kantorovich-duality", "dualitas Kantorovich"),
    "term.transport-polytope": ("concept.discrete-optimal-transport", "politop transportasi"),
    "term.entropic-regularization": ("concept.entropic-optimal-transport", "regularisasi entropik"),
    "term.gibbs-kernel": ("concept.entropic-plan-factorization", "kernel Gibbs"),
    "term.sinkhorn-knopp-algorithm": ("concept.sinkhorn-knopp-algorithm", "algoritme Sinkhorn--Knopp"),
}
for term_id, segment_id in expected_ch09_term_evidence.items():
    term = ids.get(term_id, {})
    if term.get("evidence_segment_ids") != [segment_id]:
        error(f"{term_id}: wrong Chapter 9 evidence segment")
    if term.get("locale") != "id-ID" or term.get("rights_id") != "rights.o015-habring-id-ch09":
        error(f"{term_id}: wrong Chapter 9 locale/rights binding")
    concept_id, preferred = expected_ch09_term_contracts[term_id]
    if term.get("concept_id") != concept_id or term.get("preferred") != preferred:
        error(f"{term_id}: wrong concept/preferred-term binding")

expected_ch09_surface_ids = {
    "surface.habring.v1.ch09.figure01",
    "surface.habring.v1.ch09.exercise01",
    "surface.habring.v1.ch09.solution01",
    "surface.habring.v1.ch09.hint-inventory",
    "surface.habring.v1.ch09.answer-inventory",
    "surface.habring.v1.ch09.asset-inventory",
}
actual_ch09_surface_ids = {
    record["id"]
    for record in records
    if record.get("entity_type") == "learning_surface"
    and record.get("unit_id") == "unit.habring.v1.ch09"
}
if actual_ch09_surface_ids != expected_ch09_surface_ids:
    error("Chapter 9 learning-surface closure differs")

ch09_figure = ids.get("surface.habring.v1.ch09.figure01", {})
for field, expected in {
    "surface_type": "figure",
    "presence": "present",
    "source_line_start": 18,
    "source_line_end": 75,
    "target_line_start": 22,
    "target_line_end": 82,
    "asset_id": "asset.habring.v1.ch09.transport-map-tikz",
}.items():
    if ch09_figure.get(field) != expected:
        error(f"Chapter 9 figure surface has wrong {field}")
if not ch09_figure.get("accessibility_description"):
    error("Chapter 9 figure lacks its Indonesian accessibility description")

ch09_exercise = ids.get("surface.habring.v1.ch09.exercise01", {})
for field, expected in {
    "source_line_start": 237,
    "source_line_end": 237,
    "target_line_start": 283,
    "target_line_end": 332,
}.items():
    if ch09_exercise.get(field) != expected:
        error(f"Chapter 9 source exercise has wrong {field}")
if ch09_exercise.get("disposition") != (
    "source_exercise_resolved_by_determined_integrated_proof"
):
    error("Chapter 9 source exercise has wrong disposition")
if ch09_exercise.get("correction_event_id") != "O015-HAB-ADV-0094":
    error("Chapter 9 source exercise is not bound to correction 0094")
if ch09_exercise.get("hint_state") != "absent_in_source":
    error("Chapter 9 source exercise hint absence is not explicit")
if ch09_exercise.get("answer_state") != "absent_in_source":
    error("Chapter 9 source exercise answer absence is not explicit")
if ch09_exercise.get("solution_state") != "present_in_target_as_integrated_proof":
    error("Chapter 9 integrated solution is not explicit on the exercise")

ch09_solution = ids.get("surface.habring.v1.ch09.solution01", {})
for field, expected in {
    "surface_type": "integrated_solution",
    "presence": "present",
    "source_presence": "absent",
    "target_presence": "present",
    "origin": "determined correction and completion",
    "correction_event_id": "O015-HAB-ADV-0094",
    "source_line_start": 237,
    "source_line_end": 237,
    "target_line_start": 283,
    "target_line_end": 332,
}.items():
    if ch09_solution.get(field) != expected:
        error(f"Chapter 9 integrated solution has wrong {field}")

for surface_type in ("hint", "answer"):
    surface_id = f"surface.habring.v1.ch09.{surface_type}-inventory"
    surface = ids.get(surface_id, {})
    if surface.get("presence") != "absent" or surface.get("count") != 0:
        error(f"{surface_id}: source absence is not explicit")
ch09_asset_inventory = ids.get("surface.habring.v1.ch09.asset-inventory", {})
if ch09_asset_inventory.get("presence") != "present" or ch09_asset_inventory.get("count") != 2:
    error("Chapter 9 asset inventory does not record two present assets")
if ch09_asset_inventory.get("asset_ids") != [
    "asset.habring.v1.ch09.transport-map-tikz",
    "asset.habring.v1.ch09.local-bibliography",
]:
    error("Chapter 9 asset inventory has the wrong stable-ID closure")

ch09_tikz_asset = ids.get("asset.habring.v1.ch09.transport-map-tikz", {})
for field, expected in {
    "asset_kind": "inline_tikz_figure",
    "source_path": "authority/habring/source-v1/optimal_transport.tex",
    "source_line_start": 18,
    "source_line_end": 75,
    "target_path": "source/id-ID/habring-09-transportasi-optimal-id.tex",
    "target_line_start": 22,
    "target_line_end": 82,
    "rights_id": "rights.o015-habring-ch09-inline-tikz",
}.items():
    if ch09_tikz_asset.get(field) != expected:
        error(f"Chapter 9 inline TikZ asset has wrong {field}")
if "scaling" not in ch09_tikz_asset.get("adaptation", ""):
    error("Chapter 9 inline TikZ layout adaptation is not recorded")
if not ch09_tikz_asset.get("accessibility_description"):
    error("Chapter 9 inline TikZ asset lacks an accessibility description")
if ch09_tikz_asset.get("source_sha256") != (
    "719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba"
) or ch09_tikz_asset.get("target_sha256") != (
    "45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd"
):
    error("Chapter 9 inline TikZ asset has wrong source/target identity")

ch09_bibliography_asset = ids.get("asset.habring.v1.ch09.local-bibliography", {})
for field, expected in {
    "asset_kind": "localized_bibliography_metadata",
    "source_path": "authority/habring/source-v1/references.bib",
    "source_line_start": 20,
    "source_line_end": 26,
    "target_path": "source/id-ID/references-ot-id.bib",
    "target_line_start": 1,
    "target_line_end": 9,
    "rights_id": "rights.o015-habring-ch09-local-bibliography",
    "correction_event_id": "O015-HAB-ADV-0096",
}.items():
    if ch09_bibliography_asset.get(field) != expected:
        error(f"Chapter 9 local bibliography asset has wrong {field}")
if ch09_bibliography_asset.get("source_sha256") != (
    "e334d49a9df665d3cb5902f8874a24e44be601f26fafb07fa21406690e473f20"
) or ch09_bibliography_asset.get("target_sha256") != (
    "93611c4b6a753478c51c601e59ef6cd3e290677e2e2d25b104d5d3b74df03126"
):
    error("Chapter 9 local bibliography asset has wrong source/target identity")

expected_ch09_rights = {
    "rights.o015-habring-ch09-source": (
        "authority/habring/source-v1/optimal_transport.tex",
        "admitted",
        "CC BY 4.0",
        True,
    ),
    "rights.o015-habring-id-ch09": (
        "source/id-ID/habring-09-transportasi-optimal-id.tex",
        "derivative",
        "CC BY 4.0",
        True,
    ),
    "rights.o015-habring-ch09-inline-tikz": (
        "source/id-ID/habring-09-transportasi-optimal-id.tex",
        "derivative",
        "CC BY 4.0",
        True,
    ),
    "rights.o015-habring-ch09-local-bibliography": (
        "source/id-ID/references-ot-id.bib",
        "derivative",
        "CC BY 4.0",
        True,
    ),
    "rights.o015-optimal-transport-solver-validation": (
        "qa/validate_optimal_transport_unit.py",
        "admitted",
        "project-local validation code",
        False,
    ),
}
for right_id, (path, status, expression, permitted) in expected_ch09_rights.items():
    right = ids.get(right_id, {})
    for field, expected in {
        "path": path,
        "status": status,
        "rights_expression": expression,
        "translation_permitted": permitted,
    }.items():
        if right.get(field) != expected:
            error(f"{right_id}: wrong {field}")
    if expression == "CC BY 4.0":
        if right.get("authority_url") != "https://arxiv.org/abs/2607.11664v1":
            error(f"{right_id}: wrong source authority URL")
        if right.get("license_url") != "https://creativecommons.org/licenses/by/4.0/":
            error(f"{right_id}: wrong license URL")
        handling = set(right.get("required_handling", []))
        if "attribute Andreas Habring" not in handling or "no implied endorsement" not in handling:
            error(f"{right_id}: attribution/non-endorsement handling is incomplete")

expected_ch09_correction_ranges = {
    84: ("authority/habring/source-v1/optimal_transport.tex", 8, 96, [1, 3]),
    85: ("authority/habring/source-v1/optimal_transport.tex", 8, 14, [1]),
    86: ("authority/habring/source-v1/optimal_transport.tex", 87, 92, [3]),
    87: ("authority/habring/source-v1/optimal_transport.tex", 94, 94, [3]),
    88: ("authority/habring/source-v1/optimal_transport.tex", 112, 118, [4]),
    89: ("authority/habring/source-v1/optimal_transport.tex", 122, 129, [4]),
    90: ("authority/habring/source-v1/optimal_transport.tex", 131, 141, [5]),
    91: ("authority/habring/source-v1/optimal_transport.tex", 142, 190, [6]),
    92: ("authority/habring/source-v1/optimal_transport.tex", 192, 215, [7]),
    93: ("authority/habring/source-v1/optimal_transport.tex", 216, 226, [7]),
    94: ("authority/habring/source-v1/optimal_transport.tex", 229, 256, [8]),
    95: ("authority/habring/source-v1/optimal_transport.tex", 257, 264, [9]),
    96: ("authority/habring/source-v1/references.bib", 20, 26, []),
}
for number, (path, start, end, segment_orders) in expected_ch09_correction_ranges.items():
    correction_id = f"correction.o015-hab-adv-{number:04d}"
    correction = ids.get(correction_id, {})
    for field, expected in {
        "source_event_id": f"O015-HAB-ADV-{number:04d}",
        "affected_unit_ids": ["unit.habring.v1.ch09"],
        "affected_segment_ids": [
            f"d90.hab.v1.ch09.seg{order:04d}" for order in segment_orders
        ],
        "source_path": path,
        "source_line_start": start,
        "source_line_end": end,
        "status": "applied",
        "disposition": "applied",
        "upstream_report_disposition": "not_submitted",
        "evidence_artifact_id": "artifact.o015.adverse-ledger",
    }.items():
        if correction.get(field) != expected:
            error(f"{correction_id}: wrong {field}")

expected_ch09_artifact_contracts = {
    "artifact.habring.source-ch09": ("source_tex", "authority/habring/source-v1/optimal_transport.tex"),
    "artifact.habring.target-ch09": ("target_tex", "source/id-ID/habring-09-transportasi-optimal-id.tex"),
    "artifact.habring.target-wrapper-ch09": ("target_tex", "source/id-ID/D90-HAB-09-transportasi-optimal-id.tex"),
    "artifact.habring.local-bibliography-ch09": ("bibliography_metadata", "source/id-ID/references-ot-id.bib"),
    "artifact.habring.structure-report-ch09": ("qa_report", "qa/OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json"),
    "artifact.habring.formula-manifest-ch09": ("qa_report", "qa/OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json"),
    "artifact.habring.structure-audit-ch09": ("qa_source", "qa/audit_optimal_transport_unit.py"),
    "artifact.habring.solver-results-ch09": ("qa_report", "qa/OPTIMAL_TRANSPORT_SOLVER_RESULTS.json"),
    "artifact.habring.solver-validator-ch09": ("qa_source", "qa/validate_optimal_transport_unit.py"),
    "artifact.habring.proposed-ledger-ch09": ("correction_proposal", "qa/CHAPTER09_PROPOSED_LEDGER.jsonl"),
    "artifact.habring.worklog-ch09": ("qa_receipt", "qa/CHAPTER09_WORKLOG.md"),
    "artifact.habring.build-log-ch09": ("build_receipt", "build/habring-unit-09-id/D90-HAB-09-transportasi-optimal-id.log"),
    "artifact.habring.target-pdf-ch09": ("reader_pdf", "output/pdf/D90-HAB-09-transportasi-optimal-id.pdf"),
    "artifact.habring.target-text-ch09": ("qa_extract", "qa/D90-HAB-09-transportasi-optimal-id.txt"),
    "artifact.o015.backend-generator-ch09": ("qa_source", "qa/extend_backend_ch09.py"),
}
for artifact_id, (artifact_kind, path) in expected_ch09_artifact_contracts.items():
    artifact_record = ids.get(artifact_id, {})
    if artifact_record.get("artifact_kind") != artifact_kind:
        error(f"{artifact_id}: wrong artifact kind")
    if artifact_record.get("path") != path:
        error(f"{artifact_id}: wrong artifact path")

expected_ch09_artifact_identities = {
    "artifact.habring.source-ch09": (15378, "719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba"),
    "artifact.habring.target-ch09": (21252, "45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd"),
    "artifact.habring.target-wrapper-ch09": (6822, "1e308a2bed0d1a6f5cdcff09cce932674cf32842a135bc88a5a34bc96c483ff6"),
    "artifact.habring.local-bibliography-ch09": (306, "93611c4b6a753478c51c601e59ef6cd3e290677e2e2d25b104d5d3b74df03126"),
    "artifact.habring.structure-report-ch09": (19924, "eb8b194c01dd7610dcdb7325322765ab16b3ec9cf907d28f9463fa11692767aa"),
    "artifact.habring.formula-manifest-ch09": (79141, "796e13fbf1f221139f0233d30b2464dfb026027eb5b9ce44b66b58c2f2e169ef"),
    "artifact.habring.solver-results-ch09": (16970, "4f751c615f2d7f03622b1447b3985ad1d660bd4f758cf4c4fb61d4d384b4e7a0"),
    "artifact.habring.proposed-ledger-ch09": (8840, "643fde3fbe1409732ef2df8fdef52465e4df7a583fd9bbeb2137a6122f548add"),
    "artifact.habring.target-pdf-ch09": (498244, "edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214"),
    "artifact.habring.target-text-ch09": (30053, "283864c3fc84d414ff721f128a0f10e4b61b4646c0f5edcd53551ee13f911859"),
}
for artifact_id, (expected_bytes, expected_sha256) in expected_ch09_artifact_identities.items():
    artifact_record = ids.get(artifact_id, {})
    if artifact_record.get("bytes") != expected_bytes:
        error(f"{artifact_id}: wrong frozen byte count")
    if artifact_record.get("sha256") != expected_sha256:
        error(f"{artifact_id}: wrong frozen SHA-256")
if ids.get("artifact.habring.structure-report-ch09", {}).get(
    "formula_delta_manifest_sha256"
) != "796e13fbf1f221139f0233d30b2464dfb026027eb5b9ce44b66b58c2f2e169ef":
    error("Chapter 9 structure artifact is not bound to the admitted formula manifest")
if ids.get("artifact.o015.adverse-ledger", {}).get("sha256") != (
    "09a982c3e91f83655150f7ae29a6351cb071558ed14a36cbb3701d7f43e9d824"
):
    error("integrated adverse-ledger artifact is not the admitted Chapter 9 ledger")

ch09_structure = ids.get("qa.o015.ch09.structure", {})
for field, expected in {
    "environment_topology_equal": True,
    "environment_count": 47,
    "environment_counts": {
        "aligned": 7,
        "cases": 3,
        "defn": 4,
        "enumerate": 1,
        "equation": 22,
        "figure": 1,
        "lemma": 1,
        "proof": 3,
        "quote": 1,
        "rem": 1,
        "theorem": 2,
        "tikzpicture": 1,
    },
    "failures": [],
    "segment_count": 9,
    "label_occurrences_preserved": 5,
    "source_eqref_occurrences": 8,
    "target_eqref_occurrences": 9,
    "cref_occurrences_preserved": 1,
    "source_citations": 1,
    "target_citations": 2,
    "figures": 1,
    "inline_tikz_assets": 1,
    "footnotes": 3,
    "source_exercises": 1,
    "target_integrated_solutions": 1,
    "hints": 0,
    "answers": 0,
}.items():
    if ch09_structure.get(field) != expected:
        error(f"Chapter 9 structure QA has wrong {field}")

ch09_formula = ids.get("qa.o015.ch09.formula-delta", {})
for field, expected in {
    "formula_delta_manifest_sha256": "796e13fbf1f221139f0233d30b2464dfb026027eb5b9ce44b66b58c2f2e169ef",
    "source_formula_surfaces": 162,
    "target_formula_surfaces": 232,
    "formula_delta_blocks": 35,
    "substantive_formula_delta_blocks": 34,
    "mathematical_correction_events": 12,
    "total_chapter_correction_events": 13,
}.items():
    if ch09_formula.get(field) != expected:
        error(f"Chapter 9 formula QA has wrong {field}")

ch09_bibliography = ids.get("qa.o015.ch09.bibliography", {})
for field, expected in {
    "result": "pass",
    "authority_bibliography_sha256": "e334d49a9df665d3cb5902f8874a24e44be601f26fafb07fa21406690e473f20",
    "local_bibliography_sha256": "93611c4b6a753478c51c601e59ef6cd3e290677e2e2d25b104d5d3b74df03126",
    "correction_event_id": "O015-HAB-ADV-0096",
}.items():
    if ch09_bibliography.get(field) != expected:
        error(f"Chapter 9 bibliography QA has wrong {field}")

ch09_source_freeze = ids.get("qa.o015.ch09.source-freeze", {})
if ch09_source_freeze.get("source_sha256") != (
    "719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba"
):
    error("Chapter 9 source-freeze QA has wrong authority identity")
ch09_math_review = ids.get("qa.o015.ch09.math-rereview", {})
if ch09_math_review.get("target_sha256") != (
    "45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd"
):
    error("Chapter 9 mathematical rereview has wrong target identity")

ch09_solver = ids.get("qa.o015.ch09.solver", {})
if ch09_solver.get("result") != "pass":
    error("Chapter 9 optimal-transport computation QA is not a pass")
if "41 live gates" not in ch09_solver.get("checks", []):
    error("Chapter 9 computation QA does not bind all 41 live gates")

ch09_pdf = ids.get("artifact.habring.target-pdf-ch09", {})
if ch09_pdf.get("pages") != 15:
    error("Chapter 9 PDF artifact does not record fifteen pages")
if ch09_pdf.get("accessibility") != "searchable id-ID PDF; untagged":
    error("Chapter 9 PDF accessibility limitation is not explicit")
if ch09_pdf.get("input_artifact_ids") != [
    "artifact.habring.target-wrapper-ch09",
    "artifact.habring.target-ch09",
    "artifact.habring.target-macros",
    "artifact.habring.target-class",
    "artifact.habring.local-bibliography-ch09",
]:
    error("Chapter 9 PDF input closure differs")

ch09_build = ids.get("qa.o015.ch09.build", {})
if ch09_build.get("deterministic_rebuild") != "byte-identical":
    error("Chapter 9 build does not record a byte-identical rebuild")
for field in (
    "errors",
    "undefined_references",
    "multiply_defined_labels",
    "replacement_glyphs",
    "overfull_boxes",
    "underfull_boxes",
):
    expected = [] if field == "errors" else 0
    if ch09_build.get(field) != expected:
        error(f"Chapter 9 build QA has wrong {field}")
ch09_visual = ids.get("qa.o015.ch09.visual", {})
if ch09_visual.get("pages_inspected") != 15 or ch09_visual.get("findings") != []:
    error("Chapter 9 visual QA does not close all fifteen pages cleanly")
ch09_accessibility = ids.get("qa.o015.ch09.accessibility", {})
if ch09_accessibility.get("result") != "pass_with_limitation":
    error("Chapter 9 accessibility QA has wrong result")
if ch09_accessibility.get("limitations") != ["PDF is untagged."]:
    error("Chapter 9 untagged-PDF limitation is not explicit")

structure_report = read_json_object("qa/OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json")
formula_manifest = read_json_object("qa/OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json")
solver_results = read_json_object("qa/OPTIMAL_TRANSPORT_SOLVER_RESULTS.json")
_, ch09_worklog_text = read_utf8_lf(ROOT / "qa/CHAPTER09_WORKLOG.md")
for severity in ("P1", "P2", "P3"):
    if not re.search(rf"\b{severity}\s*(?:=|:)\s*0\b", ch09_worklog_text):
        error(f"Chapter 9 worklog does not record {severity}=0")
if "independent" not in ch09_worklog_text.lower() and "independen" not in ch09_worklog_text.lower():
    error("Chapter 9 worklog does not identify the independent rereview")
if structure_report.get("result") != "pass" or structure_report.get("failures") != []:
    error("Chapter 9 frozen structure report is not a clean pass")
if structure_report.get("mode") != "strict" or structure_report.get("strict_ready") is not True:
    error("Chapter 9 frozen structure report is not strict-ready")
for failure_field in ("failure_count", "content_failure_count", "strict_only_failure_count"):
    if structure_report.get(failure_field) != 0:
        error(f"Chapter 9 structure report has nonzero {failure_field}")
if structure_report.get("stable_segment_ids") != [
    f"d90.hab.v1.ch09.seg{order:04d}" for order in range(1, 10)
]:
    error("Chapter 9 structure report has wrong segment closure")
if structure_report.get("environment_topology", {}).get("count") != 47:
    error("Chapter 9 structure report has wrong environment count")
if structure_report.get("source_line_closure", {}).get("complete_nonblank_closure") is not True:
    error("Chapter 9 structure report does not cover every nonblank source line")
if structure_report.get("local_bibliography", {}).get("gates") != {
    "publisher_doi_present": True,
    "single_expected_entry": True,
    "sole_author_corrected": True,
    "source_and_others_removed": True,
}:
    error("Chapter 9 structure report has wrong bibliography gates")
if structure_report.get("wrapper_gates", {}).get("thirteen_correction_items") is not True:
    error("Chapter 9 wrapper report does not prove thirteen correction items")
if structure_report.get("wrapper_gates", {}).get("ttp_absent") is not True:
    error("Chapter 9 wrapper report does not prove TTP absence")

for field, expected in {
    "source_formula_count": 162,
    "target_formula_count": 232,
    "delta_block_count": 35,
    "substantive_delta_block_count": 34,
    "required_ledger_event_ids": [
        f"O015-HAB-ADV-{number:04d}" for number in range(84, 96)
    ],
    "used_ledger_event_ids": [
        f"O015-HAB-ADV-{number:04d}" for number in range(84, 96)
    ],
    "unbound_substantive_delta_block_ids": [],
    "proposal_incomplete_substantive_delta_block_ids": [],
    "integration_incomplete_substantive_delta_block_ids": [],
    "unused_required_ledger_event_ids": [],
    "all_substantive_deltas_proposed_ledger_bound": True,
    "all_substantive_deltas_integrated_ledger_bound": True,
}.items():
    if formula_manifest.get(field) != expected:
        error(f"Chapter 9 frozen formula manifest has wrong {field}")

if solver_results.get("status") != "PASS":
    error("Chapter 9 frozen solver result is not PASS")
solver_summary = solver_results.get("summary", {})
for field, expected in {
    "gate_count": 41,
    "passed_gate_count": 41,
    "failed_gate_count": 0,
    "negative_control_count": 4,
    "finite_ot_shape": [3, 4],
    "sinkhorn_iterations": 27,
}.items():
    if solver_summary.get(field) != expected:
        error(f"Chapter 9 frozen solver result has wrong {field}")
finite_ot = solver_results.get("rectangular_finite_ot", {})
if finite_ot.get("passed") is not True or finite_ot.get("shape") != [3, 4]:
    error("Chapter 9 finite rectangular OT witness differs")
if finite_ot.get("primal_objective") != 0.575 or finite_ot.get("duality_gap_absolute") != 0.0:
    error("Chapter 9 finite OT primal/dual objective differs")
wasserstein = solver_results.get("wasserstein_two_special_case", {})
if wasserstein.get("passed") is not True or wasserstein.get("W2_squared") != 3.0:
    error("Chapter 9 Wasserstein witness differs")
sinkhorn = solver_results.get("entropic_sinkhorn", {})
if sinkhorn.get("passed") is not True or sinkhorn.get("shape") != [3, 4]:
    error("Chapter 9 Sinkhorn witness differs")
if sinkhorn.get("iterations") != 27 or sinkhorn.get("maximum_row_residual", 1.0) > 1e-12:
    error("Chapter 9 Sinkhorn convergence witness differs")
solver_gates = solver_results.get("gates", [])
if len(solver_gates) != 41:
    error("Chapter 9 solver report does not contain exactly 41 gates")
if any(gate.get("passed") is not True for gate in solver_gates):
    error("Chapter 9 solver report contains a failed gate")

expected_ledger_ids = [f"O015-HAB-ADV-{number:04d}" for number in range(84, 96)]
proposal_path = local_path("qa/CHAPTER09_PROPOSED_LEDGER.jsonl")
ledger_path = local_path("00_control/ADVERSE_LEDGER.jsonl")
proposal_events: list[dict[str, Any]] = []
integrated_events: list[dict[str, Any]] = []
for path, destination, label in (
    (proposal_path, proposal_events, "Chapter 9 proposed ledger"),
    (ledger_path, integrated_events, "integrated adverse ledger"),
):
    if path is None:
        continue
    _, ledger_text = read_utf8_lf(path)
    for line_number, line in enumerate(ledger_text.splitlines(), start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            error(f"{label} has invalid JSON at line {line_number}: {exc}")
            continue
        if not isinstance(event, dict):
            error(f"{label} line {line_number} is not an object")
            continue
        destination.append(event)
proposal_by_id = {event.get("event_id"): event for event in proposal_events}
integrated_by_id = {event.get("event_id"): event for event in integrated_events}
if list(proposal_by_id) != expected_ledger_ids or len(proposal_events) != 12:
    error("Chapter 9 proposed correction ledger order/count differs")
for event_id in expected_ledger_ids:
    if integrated_by_id.get(event_id) != proposal_by_id.get(event_id):
        error(f"integrated correction differs from Chapter 9 proposal: {event_id}")
expected_bibliography_event = {
    "event_id": "O015-HAB-ADV-0096",
    "authority": "o015-habring-arxiv-2607.11664v1",
    "source": "references.bib",
    "surface": "Villani bibliography author metadata and rendered name",
    "source_issue": "The frozen bibliography records the sole-authored book as `Villani, Cédric and others`; BibLaTeX consequently renders the visible citation and bibliography name as `Villani andothers`, while the publisher's primary metadata identifies Cédric Villani as the sole author.",
    "target_action": "Kept the frozen authority file unchanged, supplied a unit-local corrected bibliography entry naming Cédric Villani as sole author and adding the publisher DOI, and bound the standalone wrapper to that corrected metadata.",
    "class": "determined_bibliographic_metadata_and_rendering_correction",
}
if integrated_by_id.get("O015-HAB-ADV-0096") != expected_bibliography_event:
    error("integrated bibliography correction 0096 differs")
if len(integrated_events) != 99 or [
    event.get("event_id") for event in integrated_events[-13:]
] != expected_ledger_ids + ["O015-HAB-ADV-0096"]:
    error("integrated Chapter 9 correction order/count differs")

_, wrapper_text = read_utf8_lf(
    ROOT / "source/id-ID/D90-HAB-09-transportasi-optimal-id.tex"
)
for required_wrapper_surface in (
    "CC BY 4.0",
    "bukan karya resmi atau dukungan Andreas Habring maupun TU Graz",
    "O015-HAB-ADV-0084 sampai O015-HAB-ADV-0096",
    "\\include{habring-09-transportasi-optimal-id}",
    "\\addbibresource{references-ot-id.bib}",
    "pdflang={id-ID}",
):
    if required_wrapper_surface not in wrapper_text:
        error(f"Chapter 9 wrapper misses required surface: {required_wrapper_surface}")
if "TTP" in wrapper_text or "Translation and Transcription Project" in wrapper_text:
    error("Chapter 9 wrapper contains a forbidden TTP title/prose mention")

_, local_bibliography_text = read_utf8_lf(ROOT / "source/id-ID/references-ot-id.bib")
if "Villani, C{\\'e}dric" not in local_bibliography_text:
    error("Chapter 9 local bibliography does not name Cédric Villani as sole author")
if "10.1007/978-3-540-71050-9" not in local_bibliography_text:
    error("Chapter 9 local bibliography lacks the publisher DOI")
if "and others" in local_bibliography_text:
    error("Chapter 9 local bibliography retains the erroneous and-others marker")

expected_ch09_relations: dict[str, tuple[str, str, str]] = {
    "relation.unit.root-contains-ch09": ("contains", "unit.habring.v1", "unit.habring.v1.ch09"),
    "relation.unit.ch08-precedes-ch09": ("precedes", "unit.habring.v1.ch08", "unit.habring.v1.ch09"),
    "relation.unit.ch09-depends-on-ch07": ("depends-on", "unit.habring.v1.ch09", "unit.habring.v1.ch07"),
    "relation.unit.ch09-prerequisite-lower-semicontinuity": ("prerequisite", "unit.habring.v1.ch09", "concept.lower-semicontinuity"),
    "relation.unit.ch09-prerequisite-strong-convexity": ("prerequisite", "unit.habring.v1.ch09", "concept.strong-convexity"),
}
for order in range(1, 10):
    expected_ch09_relations[f"relation.unit.ch09-contains-seg{order:04d}"] = (
        "contains",
        "unit.habring.v1.ch09",
        f"d90.hab.v1.ch09.seg{order:04d}",
    )
expected_ch09_relations.update(
    {
        "relation.segment.ch09-seg0001-defines-measures": ("defines", "d90.hab.v1.ch09.seg0001", "concept.measurable-probability-space"),
        "relation.segment.ch09-seg0003-defines-pushforward": ("defines", "d90.hab.v1.ch09.seg0003", "concept.pushforward-measure"),
        "relation.segment.ch09-seg0003-defines-monge": ("defines", "d90.hab.v1.ch09.seg0003", "concept.monge-optimal-transport"),
        "relation.segment.ch09-seg0003-defines-coupling": ("defines", "d90.hab.v1.ch09.seg0003", "concept.transport-coupling"),
        "relation.segment.ch09-seg0003-defines-kantorovich": ("defines", "d90.hab.v1.ch09.seg0003", "concept.kantorovich-optimal-transport"),
        "relation.segment.ch09-seg0004-proves-existence": ("proves", "d90.hab.v1.ch09.seg0004", "concept.kantorovich-existence"),
        "relation.segment.ch09-seg0004-defines-wasserstein": ("defines", "d90.hab.v1.ch09.seg0004", "concept.wasserstein-distance"),
        "relation.segment.ch09-seg0005-defines-duality": ("defines", "d90.hab.v1.ch09.seg0005", "concept.kantorovich-duality"),
        "relation.segment.ch09-seg0006-proves-duality": ("proves", "d90.hab.v1.ch09.seg0006", "concept.kantorovich-duality"),
        "relation.segment.ch09-seg0007-defines-discrete-ot": ("defines", "d90.hab.v1.ch09.seg0007", "concept.discrete-optimal-transport"),
        "relation.segment.ch09-seg0007-defines-entropic-ot": ("defines", "d90.hab.v1.ch09.seg0007", "concept.entropic-optimal-transport"),
        "relation.segment.ch09-seg0008-proves-factorization": ("proves", "d90.hab.v1.ch09.seg0008", "concept.entropic-plan-factorization"),
        "relation.segment.ch09-seg0009-defines-sinkhorn": ("defines", "d90.hab.v1.ch09.seg0009", "concept.sinkhorn-knopp-algorithm"),
        "relation.surface.ch09-figure-illustrates-monge": ("illustrates", "surface.habring.v1.ch09.figure01", "concept.monge-optimal-transport"),
        "relation.surface.ch09-exercise-exercises-factorization": ("exercises", "surface.habring.v1.ch09.exercise01", "concept.entropic-plan-factorization"),
        "relation.surface.ch09-solution-proves-factorization": ("proves", "surface.habring.v1.ch09.solution01", "concept.entropic-plan-factorization"),
        "relation.artifact.ch09-target-translates-source": ("translates", "artifact.habring.target-ch09", "artifact.habring.source-ch09"),
        "relation.artifact.ch09-wrapper-contains-target": ("contains", "artifact.habring.target-wrapper-ch09", "artifact.habring.target-ch09"),
        "relation.artifact.ch09-local-bibliography-adapts-authority": ("adapts", "artifact.habring.local-bibliography-ch09", "artifact.habring.references-bib"),
        "relation.artifact.ch09-wrapper-depends-on-local-bibliography": ("depends-on", "artifact.habring.target-wrapper-ch09", "artifact.habring.local-bibliography-ch09"),
        "relation.artifact.ch09-structure-depends-on-audit": ("depends-on", "artifact.habring.structure-report-ch09", "artifact.habring.structure-audit-ch09"),
        "relation.artifact.ch09-solver-depends-on-validator": ("depends-on", "artifact.habring.solver-results-ch09", "artifact.habring.solver-validator-ch09"),
        "relation.artifact.ch09-pdf-depends-on-wrapper": ("depends-on", "artifact.habring.target-pdf-ch09", "artifact.habring.target-wrapper-ch09"),
        "relation.artifact.ch09-text-adapts-pdf": ("adapts", "artifact.habring.target-text-ch09", "artifact.habring.target-pdf-ch09"),
    }
)
actual_ch09_relation_ids = {
    record["id"]
    for record in records
    if record.get("entity_type") == "relation" and is_generated_ch09(record)
}
if actual_ch09_relation_ids != set(expected_ch09_relations):
    error("Chapter 9 relation closure differs")
for relation_id, (relation_type, source_id, target_id) in expected_ch09_relations.items():
    relation = ids.get(relation_id, {})
    if (
        relation.get("relation_type"),
        relation.get("source_id"),
        relation.get("target_id"),
    ) != (relation_type, source_id, target_id):
        error(f"{relation_id}: wrong relation triple")

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
        locator_fields = {
            f"{side}_{suffix}"
            for side in ("source", "target")
            for suffix in ("path", "line_start", "line_end", "content_sha256")
        }
        present_locator_fields = locator_fields.intersection(record)
        if present_locator_fields and present_locator_fields != locator_fields:
            missing = sorted(locator_fields.difference(record))
            error(
                f"{record.get('id')}: partial learning-surface locator; "
                f"missing {missing}"
            )
            continue
        if present_locator_fields == locator_fields:
            for side in ("source", "target"):
                content = normalized_slice(
                    record[f"{side}_path"],
                    record[f"{side}_line_start"],
                    record[f"{side}_line_end"],
                )
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
expected_entity_counts = {
    "artifact": 95,
    "asset": 6,
    "concept": 94,
    "correction": 96,
    "course": 1,
    "edition": 2,
    "learning_surface": 38,
    "program": 1,
    "qa_event": 64,
    "relation": 217,
    "resource": 1,
    "rights": 27,
    "segment": 62,
    "term": 81,
    "unit": 8,
}
if len(records) != 793:
    error(f"seven-unit backend has {len(records)} records, expected 793")
if dict(sorted(entity_counts.items())) != expected_entity_counts:
    error(
        "seven-unit entity counts differ: "
        f"expected {expected_entity_counts}, found {dict(sorted(entity_counts.items()))}"
    )
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
