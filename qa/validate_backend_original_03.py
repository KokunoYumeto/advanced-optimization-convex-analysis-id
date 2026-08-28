#!/usr/bin/env python3
"""Independent validator for the D90 MIT-L03/Original-03 backend closure."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
SCHEMA_PATH = BACKEND / "backend_schema.json"
BUILD_RECEIPT_PATH = ROOT / "qa/ORIGINAL_03_BACKEND_BUILD.json"
VALIDATION_PATH = ROOT / "qa/ORIGINAL_03_BACKEND_VALIDATION.json"
GENERATOR = ROOT / "qa/extend_backend_original_03.py"

WORKFLOW = "o015-original-03-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"
COURSE_ID = "course.d90.advanced-optimization-convex-analysis"
BASELINE_JSONL_SHA256 = "52efa90b75fecfa61498bd60ec530045d5cb08c921b6149735f1c6aaa3305439"
BASELINE_CSV_SHA256 = "2f1963d415772229eb8a2d017a7aea847c7cf205c94afc8810b8cdbd89f8343c"
SCHEMA_SHA256 = "1166cbffe6016044430fe003e4981b1a3a537be7c115f0b646168a1936ab5ad0"

OLD_COURSE: dict[str, Any] = {
    "schema": RECORD_SCHEMA,
    "schema_version": SCHEMA_VERSION,
    "entity_type": "course",
    "id": COURSE_ID,
    "recorded_at": "2026-08-21T10:54:38Z",
    "responsible_workflow": "o015-first-unit-backend-v1",
    "status": "active",
    "program_id": "program.d90.id-id",
    "role": "D90",
    "title": "Analisis Optimisasi Lanjut dan Konveks",
    "prerequisite_ids": ["concept.convex-function", "concept.epigraph", "concept.frechet-derivative", "concept.hilbert-space"],
    "scope_note": "O015 excludes LP/IP, simplex, finite-dimensional LP duality, and OR modeling already owned by O018.",
    "source_spine_unit_ids": ["unit.mit.ocw-6.253.spring-2012", "unit.habring.v1", "unit.penn.v1", "unit.royer.stochastic-gradient.2023-2024"],
    "source_spine_note": "MIT is the selected primary theory spine; Habring supplies the modern convex/nonsmooth module; Penn supplies smooth numerical optimization; Royer supplies the stochastic-gradient component.",
}
NEW_COURSE = dict(OLD_COURSE)
NEW_COURSE.update(
    {
        "source_spine_unit_ids": ["unit.habring.v1"],
        "source_spine_note": (
            "Habring arXiv 2607.11664v1 is the canonical public-editable structured spine. "
            "The bounded Becker TeX modules and finite Original layers close nonduplicative gaps. "
            "MIT OCW 6.253, Penn Math 555, and Royer remain separately licensed companions and "
            "are not the canonical editable spine."
        ),
    }
)

MODULE_NAMES = [
    "00-peta-asesmen-id.tex",
    "01-diagnostik-prasyarat-id.tex",
    "02-set-soal-dasar-konveks-id.tex",
    "03-set-soal-metode-proksimal-id.tex",
    "04-set-soal-dualitas-kkt-id.tex",
    "05-set-soal-metode-stokastik-id.tex",
    "06-set-soal-operator-monoton-id.tex",
    "07-set-soal-transportasi-dan-sintesis-id.tex",
    "08-rubrik-pembuktian-id.tex",
    "09-ujian-tengah-id.tex",
    "10-ujian-akhir-id.tex",
    "11-laboratorium-globalisasi-newton-id.tex",
    "12-laboratorium-transportasi-entropik-id.tex",
    "13-proyek-kapstone-masalah-invers-komposit-id.tex",
]
MODULE_PATHS = [f"source/id-ID/original-03/{name}" for name in MODULE_NAMES]

SPECIAL_BINDINGS = {
    "d90.orig.v1.tr03.lab.0003": "orig03:lab:globalisasi-newton",
    "d90.orig.v1.tr03.lab.hint.0003": "orig03:lab:hint:0003",
    "d90.orig.v1.tr03.lab.answer.0003": "orig03:lab:answer:0003",
    "d90.orig.v1.tr03.lab.solution.0003": "orig03:lab:solution:0003",
    "d90.orig.v1.tr03.lab.0004": "orig03:lab:transportasi-entropik",
    "d90.orig.v1.tr03.lab.hint.0004": "orig03:lab:hint:0004",
    "d90.orig.v1.tr03.lab.answer.0004": "orig03:lab:answer:0004",
    "d90.orig.v1.tr03.lab.solution.0004": "orig03:lab:solution:0004",
    "d90.orig.v1.tr03.capstone.0001": "orig03:capstone:invers-komposit",
    "d90.orig.v1.tr03.capstone.unit": "orig03:capstone:unit",
    **{f"d90.orig.v1.tr03.capstone.milestone.{number:04d}": f"orig03:capstone:milestone:{number:04d}" for number in range(1, 8)},
    "d90.orig.v1.tr03.capstone.hint.0001": "orig03:capstone:hint:0001",
    "d90.orig.v1.tr03.capstone.answer.0001": "orig03:capstone:answer:0001",
    "d90.orig.v1.tr03.capstone.solution.0001": "orig03:capstone:solution:0001",
}

MIT_ARTIFACT_SUFFIXES = [
    "semantic-witness", "target-source", "target-html", "target-pdf", "builder", "validator",
    "validation", "browser-qa", "independent-rereview", "css", "pdf-preamble", "before-body",
    "after-body", "pdf-filter",
]
MIT_SURFACE_SUFFIXES = [
    "answer-inventory", "exercise-inventory", "figure-inventory", "hint-inventory",
    "reflowed-pdf", "semantic-html", "solution-inventory",
]


def canonical(value: Any) -> str:
    # v1 record canonicalization is insertion-order preserving.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> dict[str, Any]:
    data = (ROOT / relative).read_bytes()
    return {"path": relative, "bytes": len(data), "sha256": digest(data)}


def text(relative: str) -> str:
    data = (ROOT / relative).read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"BOM in {relative}")
    value = data.decode("utf-8")
    if "\r" in value:
        raise ValueError(f"non-LF line endings in {relative}")
    return value


def normalized(relative: str) -> tuple[int, int, str]:
    lines = text(relative).splitlines()
    data = ("\n".join(lines) + "\n").encode("utf-8")
    return len(lines), len(data), digest(data)


def parse_jsonl(raw: bytes) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    value = raw.decode("utf-8")
    if "\r" in value:
        raise ValueError("JSONL is not LF-only")
    lines = value.splitlines()
    records = [json.loads(line) for line in lines]
    if any(not line or line != canonical(record) for line, record in zip(lines, records, strict=True)):
        raise ValueError("JSONL is blank or noncanonical")
    return records, {record["id"]: (line + "\n").encode("utf-8") for line, record in zip(lines, records, strict=True)}


def parse_csv(raw: bytes, schema: dict[str, Any]) -> list[dict[str, Any]]:
    value = raw.decode("utf-8")
    if "\r" in value:
        raise ValueError("CSV is not LF-only")
    reader = csv.DictReader(io.StringIO(value, newline=""))
    if reader.fieldnames != schema["csv_columns"]:
        raise ValueError("CSV header differs from schema")
    records = []
    for row in reader:
        record = json.loads(row["record_json"])
        if any(row[field] != str(record[field]) for field in ("schema", "schema_version", "entity_type", "id")):
            raise ValueError(f"CSV projection mismatch for {record.get('id')}")
        records.append(record)
    return records


def ordered(records: Iterable[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    rank = {name: index for index, name in enumerate(schema["entity_order"])}
    return sorted(records, key=lambda record: (rank[record["entity_type"]], record["id"]))


def serialize(records: Iterable[dict[str, Any]], schema: dict[str, Any]) -> tuple[bytes, bytes]:
    items = ordered(records, schema)
    jsonl = "".join(canonical(record) + "\n" for record in items).encode("utf-8")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(schema["csv_columns"])
    for record in items:
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical(record)])
    return jsonl, buffer.getvalue().encode("utf-8")


def full_id(raw: str) -> str:
    return raw if raw.startswith("d90.orig.v1.tr03.") else "d90.orig.v1.tr03." + raw


def expected_label(stable_id: str) -> str:
    return "orig03:" + stable_id.removeprefix("d90.orig.v1.tr03.").replace(".", ":")


def independently_derive_bindings() -> tuple[dict[str, dict[str, Any]], set[str], int]:
    all_labels: dict[str, tuple[str, int]] = {}
    occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    label_pattern = re.compile(r"\\label\{([^}]+)\}")
    stable_patterns = [re.compile(r"^% ORIG03-STABLE-ID:\s*(\S+)\s*$"), re.compile(r"^% stable-id:\s*(\S+)\s*$")]
    assessment_map_pattern = re.compile(r"^% ORIG03-ASSESSMENT-MAP-ID:\s*(\S+)\s*$")
    header_pattern = re.compile(r"^% (?:lab-id|lab-hint-id|lab-answer-id|lab-solution-id|capstone-id|capstone-unit-id|capstone-milestone-id|capstone-hint-id|capstone-answer-id|capstone-solution-id):\s*(\S+)\s*$")

    for relative in ["source/id-ID/original-03-penutupan-kursus-id.tex", *MODULE_PATHS]:
        lines = text(relative).splitlines()
        for line_number, line in enumerate(lines, start=1):
            for match in label_pattern.finditer(line):
                label = match.group(1)
                if label in all_labels:
                    raise ValueError(f"duplicate Original-03 label {label}")
                all_labels[label] = (relative, line_number)
        if relative.endswith("00-peta-asesmen-id.tex"):
            for line_number, line in enumerate(lines, start=1):
                match = assessment_map_pattern.match(line)
                if match:
                    occurrences[full_id(match.group(1))].append({"kind": "index", "path": relative, "line": line_number})
            continue
        if relative.endswith(("11-laboratorium-globalisasi-newton-id.tex", "12-laboratorium-transportasi-entropik-id.tex", "13-proyek-kapstone-masalah-invers-komposit-id.tex")):
            headers = []
            for line_number, line in enumerate(lines, start=1):
                match = header_pattern.match(line)
                if match:
                    headers.append(match.group(1))
                    occurrences[match.group(1)].append({"kind": "comment", "path": relative, "line": line_number})
            expected_headers = sorted(stable_id for stable_id, label in SPECIAL_BINDINGS.items() if all_labels.get(label, (None, 0))[0] == relative)
            if sorted(headers) != expected_headers:
                raise ValueError(f"special binding headers differ in {relative}")
            continue
        positions: list[tuple[int, str]] = []
        for index, line in enumerate(lines):
            for pattern in stable_patterns:
                match = pattern.match(line)
                if match:
                    positions.append((index, full_id(match.group(1))))
                    break
        for number, (index, stable_id) in enumerate(positions):
            stop = positions[number + 1][0] if number + 1 < len(positions) else len(lines)
            candidates = [(match.group(1), cursor + 1) for cursor in range(index + 1, stop) for match in label_pattern.finditer(lines[cursor])]
            if candidates != [(expected_label(stable_id), candidates[0][1] if candidates else -1)]:
                raise ValueError(f"non-bijective stable binding for {stable_id} in {relative}")
            label, label_line = candidates[0]
            occurrences[stable_id].append({"kind": "definition", "path": relative, "line": index + 1, "label": label, "label_line": label_line})

    for stable_id, label in SPECIAL_BINDINGS.items():
        if label not in all_labels:
            raise ValueError(f"missing repaired label {label}")
        relative, line_number = all_labels[label]
        occurrences[stable_id].append({"kind": "definition", "path": relative, "line": line_number, "label": label, "label_line": line_number})

    result: dict[str, dict[str, Any]] = {}
    for stable_id, items in occurrences.items():
        definitions = [item for item in items if item["kind"] == "definition"]
        label_set = {item["label"] for item in definitions}
        wanted = SPECIAL_BINDINGS.get(stable_id, expected_label(stable_id))
        if label_set != {wanted}:
            raise ValueError(f"stable ID {stable_id} has label set {label_set}, wanted {wanted}")
        first = definitions[0]
        result[stable_id] = {"label": wanted, "path": first["path"], "label_line": first["label_line"], "index_occurrences": sum(item["kind"] == "index" for item in items)}
    index_ids = {stable_id for stable_id, items in occurrences.items() if any(item["kind"] == "index" for item in items)}
    if len(result) != 438 or len(index_ids) != 54 or not index_ids.issubset(result):
        raise ValueError(f"stable-ID closure differs: definitions={len(result)}, index={len(index_ids)}")
    return result, set(all_labels), len(index_ids)


def fixed_added_ids() -> set[str]:
    ids = {
        "unit.mit.ocw-6.253.l03",
        "d90.mit.ocw-6.253.l03.p014",
        *[f"surface.mit.l03.{suffix}" for suffix in MIT_SURFACE_SUFFIXES],
        "relation.mit.l03.parent-contains-unit",
        "relation.mit.l03.contains-p014",
        "relation.mit.l03.l02-precedes",
        "relation.mit.l03.precedes-l04",
        *[f"artifact.mit.l03.{suffix}" for suffix in MIT_ARTIFACT_SUFFIXES],
        "qa.o015.mit-l03.source-freeze",
        "qa.o015.mit-l03.build",
        "qa.o015.mit-l03.semantic-overlay",
        "qa.o015.mit-l03.accessibility",
        "d90.orig.v1.tr03.resource",
        "d90.orig.v1.tr03.edition.id-id",
        "d90.orig.v1.tr03.unit",
        "d90.orig.v1.tr03.rights.content.cc-by-sa-4-0",
        "d90.orig.v1.tr03.rights.tooling",
        *[f"d90.orig.v1.tr03.seg{index:04d}" for index in range(1, 15)],
        "d90.orig.v1.tr03.artifact.source-aggregator",
        *[f"d90.orig.v1.tr03.artifact.module-{index:02d}" for index in range(14)],
        *[
            f"d90.orig.v1.tr03.artifact.{base}-{suffix}"
            for base in ("globalisasi-newton", "transportasi-entropik", "kapstone-invers-komposit")
            for suffix in ("code", "results-json", "results-csv", "results-svg")
        ],
        "d90.orig.v1.tr03.artifact.backend-generator",
        "d90.orig.v1.tr03.artifact.backend-validator",
        "d90.orig.v1.tr03.relation.course-contains-unit",
        "d90.orig.v1.tr03.relation.edition-contains-unit",
        *[f"d90.orig.v1.tr03.relation.unit-contains-seg{index:04d}" for index in range(1, 15)],
        "d90.orig.v1.tr03.qa.stable-id-binding",
        "d90.orig.v1.tr03.qa.computation",
        "d90.orig.v1.tr03.qa.rights-o018-firewall",
        "d90.orig.v1.tr03.qa.source-freeze",
        "d90.orig.v1.tr03.qa.backend-integration",
        "correction.o015.course-canonical-editable-spine",
    }
    return ids


def validate() -> dict[str, Any]:
    schema_info = file_info("backend/backend_schema.json")
    if schema_info["bytes"] != 3092 or schema_info["sha256"] != SCHEMA_SHA256:
        raise ValueError("backend schema identity changed")
    schema = json.loads(text("backend/backend_schema.json"))
    jsonl_raw, csv_raw = JSONL_PATH.read_bytes(), CSV_PATH.read_bytes()
    records, final_lines = parse_jsonl(jsonl_raw)
    csv_records = parse_csv(csv_raw, schema)
    if records != csv_records:
        raise ValueError("JSONL/CSV record equality failed")
    expected_jsonl, expected_csv = serialize(records, schema)
    if jsonl_raw != expected_jsonl or csv_raw != expected_csv:
        raise ValueError("backend files are not deterministic canonical serializations")
    if records != ordered(records, schema):
        raise ValueError("backend sort order failed")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate backend stable IDs")
    by_id = {record["id"]: record for record in records}

    id_pattern = re.compile(schema["id_pattern"])
    for record in records:
        for field in schema["required_common"]:
            if field not in record:
                raise ValueError(f"{record['id']} lacks {field}")
        if record["schema"] != RECORD_SCHEMA or record["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"{record['id']} has wrong record schema")
        if record["entity_type"] not in schema["entity_order"] or not id_pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid backend record {record['id']}")
        for field in schema["required_by_entity"].get(record["entity_type"], []):
            if field not in record:
                raise ValueError(f"{record['id']} lacks required field {field}")
        for field in schema["reference_fields"]:
            if field in record:
                values = record[field] if isinstance(record[field], list) else [record[field]]
                for value in values:
                    if value is not None and value not in by_id:
                        raise ValueError(f"{record['id']} dangling {field}: {value}")
        if record["entity_type"] == "relation" and record["relation_type"] not in schema["relation_types"]:
            raise ValueError(f"invalid relation type in {record['id']}")

    workflow_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    baseline_records = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    corrected = by_id.get(COURSE_ID)
    if corrected != NEW_COURSE:
        raise ValueError("course correction is not the exact authorized value")
    recovered = [dict(OLD_COURSE) if record["id"] == COURSE_ID else record for record in baseline_records]
    baseline_jsonl, baseline_csv = serialize(recovered, schema)
    if len(recovered) != 4338 or len(baseline_jsonl) != 3183459 or len(baseline_csv) != 3839894:
        raise ValueError("recovered baseline counts/bytes differ")
    if digest(baseline_jsonl) != BASELINE_JSONL_SHA256 or digest(baseline_csv) != BASELINE_CSV_SHA256:
        raise ValueError("recovered protected baseline hashes differ")
    _, baseline_lines = parse_jsonl(baseline_jsonl)
    protected_ids = [record["id"] for record in recovered if record["id"] != COURSE_ID]
    if any(final_lines[record_id] != baseline_lines[record_id] for record_id in protected_ids):
        raise ValueError("a protected JSONL record line changed")
    expected_protected_order = [record["id"] for record in ordered(recovered, schema) if record["id"] != COURSE_ID]
    actual_protected_order = [record["id"] for record in records if record["id"] in set(protected_ids)]
    if actual_protected_order != expected_protected_order:
        raise ValueError("protected relative order changed")
    changed_keys = sorted(key for key in set(OLD_COURSE) | set(NEW_COURSE) if OLD_COURSE.get(key) != NEW_COURSE.get(key))
    if changed_keys != ["source_spine_note", "source_spine_unit_ids"]:
        raise ValueError(f"course correction changed unexpected fields: {changed_keys}")

    bindings, labels, index_count = independently_derive_bindings()
    expected_added = fixed_added_ids() | set(bindings)
    actual_added = {record["id"] for record in workflow_records}
    if actual_added != expected_added:
        raise ValueError(f"added-ID set differs: missing={sorted(expected_added-actual_added)[:20]}, extra={sorted(actual_added-expected_added)[:20]}")
    if len(actual_added) != 539:
        raise ValueError(f"added record count differs: {len(actual_added)}")
    for stable_id, binding in bindings.items():
        record = by_id[stable_id]
        if record["entity_type"] != "learning_surface" or record["latex_label"] != binding["label"] or record["source_path"] != binding["path"]:
            raise ValueError(f"backend stable binding differs for {stable_id}")
        if stable_id in SPECIAL_BINDINGS and record.get("repaired_comment_only_binding") is not True:
            raise ValueError(f"repaired binding flag missing for {stable_id}")

    for index, relative in enumerate(MODULE_PATHS, start=1):
        segment = by_id[f"d90.orig.v1.tr03.seg{index:04d}"]
        lines, byte_count, sha = normalized(relative)
        if segment["source_path"] != relative or segment["source_line_end"] != lines or segment["source_content_bytes"] != byte_count or segment["source_content_sha256"] != sha:
            raise ValueError(f"Original-03 segment binding differs for {relative}")
    mit_segment = by_id["d90.mit.ocw-6.253.l03.p014"]
    for side, relative in (("source", "source/en/mit-03-modern-view-semantic-witness.md"), ("target", "source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md")):
        lines, byte_count, sha = normalized(relative)
        if mit_segment[f"{side}_path"] != relative or mit_segment[f"{side}_line_end"] != lines or mit_segment[f"{side}_content_bytes"] != byte_count or mit_segment[f"{side}_content_sha256"] != sha:
            raise ValueError(f"MIT-L03 {side} segment binding differs")

    artifact_count = 0
    for record in workflow_records:
        if record["entity_type"] != "artifact":
            continue
        artifact_count += 1
        path = ROOT / record["path"]
        if not path.is_file():
            raise ValueError(f"missing added artifact {record['path']}")
        data = path.read_bytes()
        if len(data) != record["bytes"] or digest(data) != record["sha256"]:
            raise ValueError(f"artifact byte/hash mismatch: {record['id']}")
    if artifact_count != 43:
        raise ValueError(f"added artifact count differs: {artifact_count}")

    mit_receipt = json.loads(text("qa/MIT_L03_VALIDATION.json"))
    for key, relative in {
        "witness": "source/en/mit-03-modern-view-semantic-witness.md",
        "target": "source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md",
        "html": "output/html/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.html",
        "pdf": "output/pdf/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.pdf",
    }.items():
        actual = file_info(relative)
        expected = mit_receipt["files"][key]
        if actual["bytes"] != expected["bytes"] or actual["sha256"] != expected["sha256"]:
            raise ValueError(f"MIT-L03 existing byte changed: {relative}")

    for base in ("globalisasi-newton", "transportasi-entropik", "kapstone-invers-komposit"):
        payload = json.loads(text(f"labs/original-03/{base}-results.json"))
        certificates = payload.get("validation", {}).get("certificates", payload.get("certificates", {}))
        if payload.get("result") != "pass" or not certificates or not all(certificates.values()):
            raise ValueError(f"computation certificate failure: {base}")

    for record in workflow_records:
        if not record["id"].startswith("d90.orig.v1.tr03."):
            continue
        strings: list[str] = []
        stack: list[Any] = [record]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
            elif isinstance(value, str):
                strings.append(value)
        if any(re.fullmatch(r"(?:course|unit|edition|resource|d90)\.o018(?:[.-].*)?", value.lower()) for value in strings):
            raise ValueError(f"O018 identifier leaked into {record['id']}")

    expected_added_counts = {
        "artifact": 43,
        "correction": 1,
        "edition": 1,
        "learning_surface": 445,
        "qa_event": 9,
        "relation": 20,
        "resource": 1,
        "rights": 2,
        "segment": 15,
        "unit": 2,
    }
    actual_added_counts = dict(sorted(Counter(record["entity_type"] for record in workflow_records).items()))
    if actual_added_counts != expected_added_counts:
        raise ValueError(f"added entity counts differ: {actual_added_counts}")
    expected_final_counts = {
        "artifact": 489, "asset": 24, "concept": 176, "correction": 248, "course": 1,
        "edition": 17, "learning_surface": 1247, "program": 1, "qa_event": 323,
        "relation": 1837, "resource": 10, "rights": 93, "segment": 248, "term": 127, "unit": 36,
    }
    final_counts = dict(sorted(Counter(record["entity_type"] for record in records).items()))
    if final_counts != expected_final_counts or len(records) != 4877:
        raise ValueError(f"final entity closure differs: count={len(records)}, entities={final_counts}")

    build_receipt = json.loads(text("qa/ORIGINAL_03_BACKEND_BUILD.json"))
    if build_receipt.get("result") != "pass" or build_receipt["admission"]["jsonl"]["sha256"] != digest(jsonl_raw) or build_receipt["admission"]["csv"]["sha256"] != digest(csv_raw):
        raise ValueError("generator receipt does not bind the canonical backend")
    correction_record = by_id["correction.o015.course-canonical-editable-spine"]
    old_hash = digest(canonical(OLD_COURSE).encode("utf-8"))
    new_hash = digest(canonical(NEW_COURSE).encode("utf-8"))
    if correction_record["old_record_sha256"] != old_hash or correction_record["new_record_sha256"] != new_hash:
        raise ValueError("course correction record hashes differ")

    regeneration: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="o015-original03-backend-") as temporary:
        temp_root = Path(temporary)
        for run in (1, 2):
            output = temp_root / f"run-{run}"
            completed = subprocess.run(
                [sys.executable, str(GENERATOR), "--output-dir", str(output)],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if completed.returncode:
                raise ValueError(f"deterministic regeneration {run} failed: {completed.stdout[-2000:]}")
            receipt = json.loads(completed.stdout)
            run_jsonl = (output / "records.jsonl").read_bytes()
            run_csv = (output / "records.csv").read_bytes()
            if run_jsonl != jsonl_raw or run_csv != csv_raw:
                raise ValueError(f"deterministic regeneration {run} differs from canonical backend")
            regeneration.append({"run": run, "result": receipt["result"], "jsonl": {"bytes": len(run_jsonl), "sha256": digest(run_jsonl)}, "csv": {"bytes": len(run_csv), "sha256": digest(run_csv)}})
    if regeneration[0]["jsonl"] != regeneration[1]["jsonl"] or regeneration[0]["csv"] != regeneration[1]["csv"]:
        raise ValueError("two deterministic regenerations differ")

    return {
        "schema": "o015-original-03-backend-validation-v1",
        "workflow": WORKFLOW,
        "validated_at": "2026-08-27T23:15:00Z",
        "result": "pass",
        "errors": [],
        "schema_identity": schema_info | {"schema_changed": False},
        "protected_baseline": {
            "prior_records": 4338,
            "protected_records_byte_identical": 4337,
            "corrected_records": 1,
            "jsonl": {"bytes": len(baseline_jsonl), "sha256": digest(baseline_jsonl)},
            "csv": {"bytes": len(baseline_csv), "sha256": digest(baseline_csv)},
            "jsonl_line_and_csv_row_bytes_preserved_except_course": True,
            "relative_order_preserved": True,
        },
        "course_correction": {
            "record_id": COURSE_ID,
            "changed_fields": changed_keys,
            "old_record_sha256": old_hash,
            "new_record_sha256": new_hash,
            "correction_record_id": correction_record["id"],
        },
        "mit_l03_overlay": {
            "unit": "unit.mit.ocw-6.253.l03",
            "segment": "d90.mit.ocw-6.253.l03.p014",
            "source_page": 14,
            "source_and_reader_byte_identity": "pass",
            "records": 31,
        },
        "original_03": {
            "module_count": 14,
            "segment_count": 14,
            "stable_id_bindings": len(bindings),
            "assessment_index_bindings": index_count,
            "repaired_comment_only_bindings": len(SPECIAL_BINDINGS),
            "latex_labels": len(labels),
            "o018_firewall": "pass",
            "computation_components": 3,
        },
        "backend": {
            "records": len(records),
            "added_records": len(workflow_records),
            "added_entity_counts": actual_added_counts,
            "final_entity_counts": final_counts,
            "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
            "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
            "jsonl_csv_lossless_equality": True,
        },
        "deterministic_regeneration": {"runs_required": 2, "runs_completed": 2, "canonical_match": True, "runs": regeneration},
        "build_receipt": file_info("qa/ORIGINAL_03_BACKEND_BUILD.json"),
    }


def main() -> int:
    try:
        report = validate()
    except Exception as exc:
        report = {
            "schema": "o015-original-03-backend-validation-v1",
            "workflow": WORKFLOW,
            "validated_at": "2026-08-27T23:15:00Z",
            "result": "fail",
            "errors": [str(exc)],
        }
        VALIDATION_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 1
    VALIDATION_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
