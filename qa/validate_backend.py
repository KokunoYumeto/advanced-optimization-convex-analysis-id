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
    "unit.habring.v1.ch06": 12,
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
# limitation used by Chapters 4--6.
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

for reviewed_unit_id in ("unit.habring.v1.ch05", "unit.habring.v1.ch06"):
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
