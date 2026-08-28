#!/usr/bin/env python3
"""Close the D90 backend with MIT-L03 and the Original-03 assessment layer.

The migration is intentionally fail-closed.  It reconstructs and verifies the
exact 4,338-record Original-02 baseline, changes only the stale course record,
derives every Original-03 learning-surface binding from the live TeX, and then
adds the missing MIT-L03 and Original-03 records.  Re-running this script on an
already extended backend first recovers the exact protected baseline.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
RECEIPT_PATH = ROOT / "qa/ORIGINAL_03_BACKEND_BUILD.json"

WORKFLOW = "o015-original-03-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"
RECORDED_AT = "2026-08-27T22:30:00Z"
COURSE_ID = "course.d90.advanced-optimization-convex-analysis"

BASELINE = {
    "records": 4338,
    "jsonl_bytes": 3183459,
    "jsonl_sha256": "52efa90b75fecfa61498bd60ec530045d5cb08c921b6149735f1c6aaa3305439",
    "csv_bytes": 3839894,
    "csv_sha256": "2f1963d415772229eb8a2d017a7aea847c7cf205c94afc8810b8cdbd89f8343c",
}
SCHEMA_IDENTITY = {
    "bytes": 3092,
    "sha256": "1166cbffe6016044430fe003e4981b1a3a537be7c115f0b646168a1936ab5ad0",
}

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
    "prerequisite_ids": [
        "concept.convex-function",
        "concept.epigraph",
        "concept.frechet-derivative",
        "concept.hilbert-space",
    ],
    "scope_note": "O015 excludes LP/IP, simplex, finite-dimensional LP duality, and OR modeling already owned by O018.",
    "source_spine_unit_ids": [
        "unit.mit.ocw-6.253.spring-2012",
        "unit.habring.v1",
        "unit.penn.v1",
        "unit.royer.stochastic-gradient.2023-2024",
    ],
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
AGGREGATOR_PATH = "source/id-ID/original-03-penutupan-kursus-id.tex"

LAB_BASES = [
    "globalisasi-newton",
    "transportasi-entropik",
    "kapstone-invers-komposit",
]
LAB_PATHS = [
    f"labs/original-03/{base}{suffix}"
    for base in LAB_BASES
    for suffix in (".py", "-results.json", "-results.csv", ".svg")
]

MIT_FILES: list[tuple[str, str, str]] = [
    ("semantic-witness", "semantic_transcription_witness", "source/en/mit-03-modern-view-semantic-witness.md"),
    ("target-source", "semantic_translation_source", "source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md"),
    ("target-html", "semantic_html_reader", "output/html/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.html"),
    ("target-pdf", "reflowed_pdf_reader", "output/pdf/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.pdf"),
    ("builder", "deterministic_builder", "qa/build_mit_l03.py"),
    ("validator", "validation_script", "qa/validate_mit_l03.py"),
    ("validation", "validation_report", "qa/MIT_L03_VALIDATION.json"),
    ("browser-qa", "browser_qa_report", "qa/MIT_L03_BROWSER_QA.json"),
    ("independent-rereview", "independent_semantic_rereview", "qa/MIT_L03_INDEPENDENT_REREVIEW.md"),
    ("css", "html_stylesheet", "source/id-ID/mit-l02.css"),
    ("pdf-preamble", "pdf_preamble", "source/id-ID/mit-l03-preamble.tex"),
    ("before-body", "html_include", "source/id-ID/mit-l03-before-body.html"),
    ("after-body", "html_include", "source/id-ID/mit-l03-after-body.html"),
    ("pdf-filter", "pandoc_lua_filter", "source/id-ID/mit-l03-pdf-filter.lua"),
]

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
    **{
        f"d90.orig.v1.tr03.capstone.milestone.{number:04d}": f"orig03:capstone:milestone:{number:04d}"
        for number in range(1, 8)
    },
    "d90.orig.v1.tr03.capstone.hint.0001": "orig03:capstone:hint:0001",
    "d90.orig.v1.tr03.capstone.answer.0001": "orig03:capstone:answer:0001",
    "d90.orig.v1.tr03.capstone.solution.0001": "orig03:capstone:solution:0001",
}


def canonical(record: Any) -> str:
    # The v1 backend's canonical form preserves insertion order; all prior
    # generators intentionally serialize without sort_keys.
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    if not path.is_file():
        raise ValueError(f"required file missing: {relative}")
    data = path.read_bytes()
    return {"path": relative, "bytes": len(data), "sha256": digest(data)}


def read_text(relative: str) -> str:
    data = (ROOT / relative).read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"UTF-8 BOM is not permitted: {relative}")
    text = data.decode("utf-8")
    if "\r" in text:
        raise ValueError(f"non-LF line endings: {relative}")
    return text


def normalized_full_file(relative: str) -> tuple[int, int, str]:
    text = read_text(relative)
    lines = text.splitlines()
    normalized = ("\n".join(lines) + "\n").encode("utf-8")
    return len(lines), len(normalized), digest(normalized)


def common(entity_type: str, record_id: str, status: str = "current") -> dict[str, Any]:
    return {
        "schema": RECORD_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "entity_type": entity_type,
        "id": record_id,
        "recorded_at": RECORDED_AT,
        "responsible_workflow": WORKFLOW,
        "status": status,
    }


def id_set_sha(records: Iterable[dict[str, Any]]) -> str:
    return digest(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def id_order_sha(records: Iterable[dict[str, Any]]) -> str:
    return digest(("\n".join(record["id"] for record in records) + "\n").encode("utf-8"))


def record_set_sha(records: Iterable[dict[str, Any]]) -> str:
    return digest(("\n".join(canonical(record) for record in sorted(records, key=lambda item: item["id"])) + "\n").encode("utf-8"))


def parse_jsonl(raw: bytes) -> list[dict[str, Any]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"backend JSONL is not UTF-8: {exc}") from exc
    if "\r" in text:
        raise ValueError("backend JSONL is not LF-only")
    lines = text.splitlines()
    if any(not line for line in lines):
        raise ValueError("blank backend JSONL line")
    records = [json.loads(line) for line in lines]
    if any(line != canonical(record) for line, record in zip(lines, records, strict=True)):
        raise ValueError("backend JSONL contains noncanonical record serialization")
    return records


def parse_csv(raw: bytes, schema: dict[str, Any]) -> list[dict[str, Any]]:
    text = raw.decode("utf-8")
    if "\r" in text:
        raise ValueError("backend CSV is not LF-only")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != schema["csv_columns"]:
        raise ValueError("backend CSV columns differ from schema")
    records: list[dict[str, Any]] = []
    for row in reader:
        record = json.loads(row["record_json"])
        for field in ("schema", "schema_version", "entity_type", "id"):
            if row[field] != str(record[field]):
                raise ValueError(f"CSV projection mismatch for {record.get('id')} field {field}")
        records.append(record)
    return records


def ordered(records: Iterable[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    rank = {name: index for index, name in enumerate(schema["entity_order"])}
    return sorted(records, key=lambda record: (rank[record["entity_type"]], record["id"]))


def serialize(records: Iterable[dict[str, Any]], schema: dict[str, Any]) -> tuple[bytes, bytes]:
    items = ordered(records, schema)
    jsonl = ("".join(canonical(record) + "\n" for record in items)).encode("utf-8")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(schema["csv_columns"])
    for record in items:
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical(record)])
    return jsonl, buffer.getvalue().encode("utf-8")


def assert_schema() -> dict[str, Any]:
    info = file_info("backend/backend_schema.json")
    if {"bytes": info["bytes"], "sha256": info["sha256"]} != SCHEMA_IDENTITY:
        raise ValueError(f"backend schema identity changed: {info}")
    schema = json.loads((ROOT / info["path"]).read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema" or schema.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("backend schema identity fields changed")
    return schema


def recover_baseline(schema: dict[str, Any]) -> tuple[list[dict[str, Any]], bytes, bytes, dict[str, Any]]:
    input_jsonl = JSONL_PATH.read_bytes()
    input_csv = CSV_PATH.read_bytes()
    records = parse_jsonl(input_jsonl)
    if parse_csv(input_csv, schema) != records:
        raise ValueError("input JSONL/CSV datasets are not equal")

    recovered: list[dict[str, Any]] = []
    seen_course = 0
    for record in records:
        if record.get("responsible_workflow") == WORKFLOW:
            continue
        if record["id"] == COURSE_ID:
            seen_course += 1
            if record not in (OLD_COURSE, NEW_COURSE):
                raise ValueError("course record is neither the protected old value nor the authorized correction")
            recovered.append(dict(OLD_COURSE))
        else:
            recovered.append(record)
    if seen_course != 1:
        raise ValueError(f"expected one course record, found {seen_course}")

    recovered_jsonl, recovered_csv = serialize(recovered, schema)
    identity = {
        "records": len(recovered),
        "jsonl_bytes": len(recovered_jsonl),
        "jsonl_sha256": digest(recovered_jsonl),
        "csv_bytes": len(recovered_csv),
        "csv_sha256": digest(recovered_csv),
    }
    if identity != BASELINE:
        raise ValueError(f"cannot reconstruct the protected Original-02 baseline: {identity}")
    return recovered, recovered_jsonl, recovered_csv, {
        "input_records": len(records),
        "input_jsonl_sha256": digest(input_jsonl),
        "input_csv_sha256": digest(input_csv),
        "recovered": identity,
    }


def full_stable_id(raw: str) -> str:
    raw = raw.strip()
    return raw if raw.startswith("d90.orig.v1.tr03.") else f"d90.orig.v1.tr03.{raw}"


def expected_label(stable_id: str) -> str:
    suffix = stable_id.removeprefix("d90.orig.v1.tr03.")
    return "orig03:" + suffix.replace(".", ":")


def label_inventory() -> tuple[dict[str, tuple[str, int]], dict[str, list[dict[str, Any]]]]:
    labels: dict[str, tuple[str, int]] = {}
    occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    label_pattern = re.compile(r"\\label\{([^}]+)\}")
    stable_patterns = [
        re.compile(r"^% ORIG03-STABLE-ID:\s*(\S+)\s*$"),
        re.compile(r"^% stable-id:\s*(\S+)\s*$"),
    ]
    assessment_map_pattern = re.compile(
        r"^% ORIG03-ASSESSMENT-MAP-ID:\s*(\S+)\s*$"
    )
    header_pattern = re.compile(
        r"^% (?:lab-id|lab-hint-id|lab-answer-id|lab-solution-id|capstone-id|capstone-unit-id|capstone-milestone-id|capstone-hint-id|capstone-answer-id|capstone-solution-id):\s*(\S+)\s*$"
    )

    for relative in [AGGREGATOR_PATH, *MODULE_PATHS]:
        lines = read_text(relative).splitlines()
        for line_number, line in enumerate(lines, start=1):
            for match in label_pattern.finditer(line):
                label = match.group(1)
                if label in labels:
                    raise ValueError(f"duplicate Original-03 LaTeX label {label}: {labels[label]} and {(relative, line_number)}")
                labels[label] = (relative, line_number)

        if relative.endswith("00-peta-asesmen-id.tex"):
            for line_number, line in enumerate(lines, start=1):
                match = assessment_map_pattern.match(line)
                if match:
                    occurrences[full_stable_id(match.group(1))].append(
                        {"role": "assessment_index", "path": relative, "line": line_number}
                    )
            continue

        if relative.endswith(("11-laboratorium-globalisasi-newton-id.tex", "12-laboratorium-transportasi-entropik-id.tex", "13-proyek-kapstone-masalah-invers-komposit-id.tex")):
            found_headers: set[str] = set()
            for line_number, line in enumerate(lines, start=1):
                match = header_pattern.match(line)
                if match:
                    stable_id = match.group(1)
                    found_headers.add(stable_id)
                    occurrences[stable_id].append({"role": "definition_comment", "path": relative, "line": line_number})
            expected_here = {stable_id for stable_id, label in SPECIAL_BINDINGS.items() if labels.get(label, (None, 0))[0] == relative}
            if found_headers != expected_here:
                raise ValueError(
                    f"special stable-ID header set differs in {relative}: missing={sorted(expected_here-found_headers)}, extra={sorted(found_headers-expected_here)}"
                )
            continue

        stable_positions: list[tuple[int, str]] = []
        for index, line in enumerate(lines):
            match = next((pattern.match(line) for pattern in stable_patterns if pattern.match(line)), None)
            if match:
                stable_positions.append((index, full_stable_id(match.group(1))))
        for position, (index, stable_id) in enumerate(stable_positions):
            stop = stable_positions[position + 1][0] if position + 1 < len(stable_positions) else len(lines)
            found: list[tuple[str, int]] = []
            for candidate_index in range(index + 1, stop):
                found.extend((match.group(1), candidate_index + 1) for match in label_pattern.finditer(lines[candidate_index]))
            if len(found) != 1:
                raise ValueError(f"{relative}:{index+1} stable ID {stable_id} has {len(found)} following labels before the next stable ID")
            label, label_line = found[0]
            if label != expected_label(stable_id):
                raise ValueError(f"stable-ID/label mismatch at {relative}:{index+1}: {stable_id} -> {label}, expected {expected_label(stable_id)}")
            occurrences[stable_id].append(
                {
                    "role": "definition_comment",
                    "path": relative,
                    "line": index + 1,
                    "label": label,
                    "label_line": label_line,
                }
            )

    if len(SPECIAL_BINDINGS) != 20:
        raise ValueError("the repaired special-binding contract must contain exactly 20 stable IDs")
    for stable_id, label in SPECIAL_BINDINGS.items():
        if label not in labels:
            raise ValueError(f"repaired stable ID lacks exact label: {stable_id} -> {label}")
        path, label_line = labels[label]
        occurrences[stable_id].append(
            {"role": "definition_label", "path": path, "line": label_line, "label": label, "label_line": label_line}
        )

    definitions: dict[str, list[dict[str, Any]]] = {}
    for stable_id, items in occurrences.items():
        definition_items = [item for item in items if item["role"] in {"definition_comment", "definition_label"}]
        defining_labels = {item.get("label") for item in definition_items if item.get("label")}
        if stable_id in SPECIAL_BINDINGS:
            expected = SPECIAL_BINDINGS[stable_id]
            if defining_labels != {expected}:
                raise ValueError(f"special stable ID {stable_id} does not bind exactly to {expected}")
        else:
            if defining_labels != {expected_label(stable_id)}:
                raise ValueError(f"stable ID {stable_id} has invalid defining label set {defining_labels}")
        definitions[stable_id] = items

    index_ids = {
        stable_id for stable_id, items in occurrences.items() if any(item["role"] == "assessment_index" for item in items)
    }
    if len(index_ids) != 54 or not index_ids.issubset(definitions):
        raise ValueError(f"assessment map must index exactly 54 defined prompt IDs, found {len(index_ids)}")
    if len(definitions) != 438:
        raise ValueError(f"Original-03 stable-ID closure changed: expected 438 definitions, found {len(definitions)}")
    return labels, definitions


def surface_type(stable_id: str) -> str:
    suffix = stable_id.removeprefix("d90.orig.v1.tr03.")
    parts = suffix.split(".")
    if "milestone" in parts:
        return "capstone_milestone"
    if suffix.startswith("rubric.proof."):
        return "proof_rubric"
    if suffix.startswith("capstone.unit"):
        return "capstone_project_unit"
    if suffix.startswith("capstone.") and suffix.endswith(".0001") and not any(word in parts for word in ("hint", "answer", "solution")):
        return "capstone_project"
    if suffix.startswith("lab.") and len(parts) == 2:
        return "computational_lab"
    token = parts[-2] if parts[-1].isdigit() else parts[-1]
    return {
        "problem": "exercise_group",
        "exercise": "exercise",
        "prompt": "assessment_prompt",
        "hint1": "hint_stage_1",
        "hint2": "hint_stage_2",
        "hint": "hint",
        "answer": "short_answer",
        "solution": "complete_solution",
    }.get(token, "assessment_surface")


def segment_id_for_path(relative: str) -> str:
    name = Path(relative).name
    try:
        index = MODULE_NAMES.index(name) + 1
    except ValueError as exc:
        raise ValueError(f"not an Original-03 module: {relative}") from exc
    return f"d90.orig.v1.tr03.seg{index:04d}"


def source_evidence() -> dict[str, Any]:
    aggregator = read_text(AGGREGATOR_PATH)
    inputs = re.findall(r"\\input\{original-03/([^}]+)\}", aggregator)
    expected_inputs = [name.removesuffix(".tex") for name in MODULE_NAMES]
    if inputs != expected_inputs:
        raise ValueError(f"Original-03 aggregator input order differs: {inputs}")
    if "% unit-id: d90.orig.v1.tr03.unit" not in aggregator or "% target-edition-id: d90.orig.v1.tr03.edition.id-ID" not in aggregator:
        raise ValueError("Original-03 aggregator identity comments are missing")
    if "CC BY-SA 4.0" not in aggregator:
        raise ValueError("Original-03 aggregator license declaration is missing")
    if "O018" not in aggregator or "program linear" not in aggregator or "simpleks" not in aggregator:
        raise ValueError("Original-03 aggregator lacks the explicit O018 firewall declaration")

    labels, definitions = label_inventory()
    segments: list[dict[str, Any]] = []
    for order, relative in enumerate(MODULE_PATHS, start=1):
        lines, content_bytes, content_sha = normalized_full_file(relative)
        text = read_text(relative)
        declared = re.search(r"^% (?:ORIG03-SEGMENT-ID|segment-id):\s*(d90\.orig\.v1\.tr03\.seg\d{4})\s*$", text, re.MULTILINE)
        expected = f"d90.orig.v1.tr03.seg{order:04d}"
        if not declared or declared.group(1) != expected:
            raise ValueError(f"{relative} does not declare exact segment ID {expected}")
        segments.append(
            {
                "id": expected,
                "order": order,
                "path": relative,
                "lines": lines,
                "content_bytes": content_bytes,
                "content_sha256": content_sha,
                "title": re.search(r"\\section\{([^}]+)\}", text).group(1),
            }
        )

    lab_evidence: dict[str, Any] = {}
    for base in LAB_BASES:
        json_path = f"labs/original-03/{base}-results.json"
        csv_path = f"labs/original-03/{base}-results.csv"
        svg_path = f"labs/original-03/{base}.svg"
        payload = json.loads(read_text(json_path))
        certificates = payload.get("validation", {}).get("certificates", payload.get("certificates", {}))
        if payload.get("result") != "pass" or not certificates or not all(certificates.values()):
            raise ValueError(f"lab/capstone certificate failure in {json_path}")
        rows = list(csv.DictReader(io.StringIO(read_text(csv_path), newline="")))
        if not rows or not rows[0]:
            raise ValueError(f"empty accessible computation table: {csv_path}")
        if "<svg" not in read_text(svg_path):
            raise ValueError(f"invalid SVG artifact: {svg_path}")
        lab_evidence[base] = {
            "schema": payload.get("schema"),
            "certificate_count": len(certificates),
            "csv_rows": len(rows),
            "result": payload.get("result"),
        }

    return {
        "aggregator": file_info(AGGREGATOR_PATH),
        "segments": segments,
        "labels": labels,
        "definitions": definitions,
        "lab": lab_evidence,
    }


def validate_mit_evidence() -> dict[str, Any]:
    receipt = json.loads(read_text("qa/MIT_L03_VALIDATION.json"))
    if receipt.get("result") != "pass" or receipt.get("boundary", {}).get("source_pdf_pages") != [14]:
        raise ValueError("MIT-L03 validation receipt does not prove the exact page-14 boundary")
    expected = {
        "source/en/mit-03-modern-view-semantic-witness.md": receipt["files"]["witness"],
        "source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md": receipt["files"]["target"],
        "output/html/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.html": receipt["files"]["html"],
        "output/pdf/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.pdf": receipt["files"]["pdf"],
    }
    for relative, recorded in expected.items():
        actual = file_info(relative)
        if actual["bytes"] != recorded["bytes"] or actual["sha256"] != recorded["sha256"]:
            raise ValueError(f"MIT-L03 live byte identity differs from its validation receipt: {relative}")
    source = read_text("source/en/mit-03-modern-view-semantic-witness.md")
    target = read_text("source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md")
    source_ids = sorted(set(re.findall(r"#(src-mit-l03-[a-z0-9-]+)", source)))
    target_ids = sorted(set(re.findall(r"#(d90-mit-l03-[a-z0-9-]+)", target)))
    mapped = sorted(value.replace("src-mit-", "d90-mit-") for value in source_ids)
    target_only = sorted(set(target_ids) - set(mapped))
    if not set(mapped).issubset(target_ids) or target_only != ["d90-mit-l03-edition-notice"]:
        raise ValueError("MIT-L03 source-to-target anchor map is not bijective apart from the declared target edition notice")
    return {
        "receipt": receipt,
        "source_ids": source_ids,
        "target_ids": target_ids,
        "files": [file_info(path) for _, _, path in MIT_FILES],
    }


def artifact_record(record_id: str, kind: str, path: str, rights_id: str, **extra: Any) -> dict[str, Any]:
    info = file_info(path)
    return common("artifact", record_id) | {
        "artifact_kind": kind,
        "path": path,
        "bytes": info["bytes"],
        "sha256": info["sha256"],
        "hash_algorithm": "sha256-raw-bytes",
        "rights_id": rights_id,
        **extra,
    }


def mit_records(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    receipt = evidence["receipt"]
    unit_id = "unit.mit.ocw-6.253.l03"
    segment_id = "d90.mit.ocw-6.253.l03.p014"
    source_path = "source/en/mit-03-modern-view-semantic-witness.md"
    target_path = "source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md"
    source_lines, source_bytes, source_sha = normalized_full_file(source_path)
    target_lines, target_bytes, target_sha = normalized_full_file(target_path)

    records: list[dict[str, Any]] = [
        common("unit", unit_id, "visually_checked")
        | {
            "edition_id": "edition.mit.ocw-6.253.id-id.pilot-v1",
            "unit_kind": "lecture_topic",
            "order": 3,
            "source_local_id": "lecture-1-page-14",
            "source_local_label": "Lecture 1 - Modern View of Convex Optimization",
            "target_local_label": "Kuliah 1 - Pandangan Modern tentang Optimisasi Konveks",
            "rights_id": "rights.o015-mit-id-pilot",
            "source_edition_id": "edition.mit.ocw-6.253.spring-2012.semantic-witness-en",
            "target_edition_id": "edition.mit.ocw-6.253.id-id.pilot-v1",
            "source_pdf_pages": [14],
            "next_source_page": 15,
            "translation_state": "visually_checked",
            "parent_id": "unit.mit.ocw-6.253.spring-2012",
            "source_item_count": 2,
            "nested_source_bullet_count": 6,
            "source_figure_count": 2,
            "source_display_count": 0,
            "curriculum_role": "separately licensed companion; not canonical editable spine",
        },
        common("segment", segment_id, "visually_checked")
        | {
            "unit_id": unit_id,
            "order": 1,
            "source_edition_id": "edition.mit.ocw-6.253.spring-2012.semantic-witness-en",
            "target_edition_id": "edition.mit.ocw-6.253.id-id.pilot-v1",
            "source_path": source_path,
            "source_line_start": 1,
            "source_line_end": source_lines,
            "source_content_bytes": source_bytes,
            "source_content_sha256": source_sha,
            "source_anchor": "src-mit-l03-p014",
            "target_path": target_path,
            "target_line_start": 1,
            "target_line_end": target_lines,
            "target_content_bytes": target_bytes,
            "target_content_sha256": target_sha,
            "target_anchor": "d90-mit-l03-p014",
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "visually_checked",
            "rights_id": "rights.o015-mit-id-pilot",
            "source_pdf_path": "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf",
            "source_pdf_page": 14,
            "source_pdf_sha256": receipt["files"]["source_pdf"]["sha256"],
            "source_pdf_pages_total": 340,
            "source_item_count": 2,
            "nested_source_bullet_count": 6,
            "source_figure_count": 2,
            "source_display_count": 0,
            "anchor_mapping_rule": "replace src-mit- prefix with d90-mit- prefix",
        },
    ]

    surfaces = [
        ("answer-inventory", "answer", "source_absent", "absent", {"count": 0}),
        ("exercise-inventory", "exercise", "source_absent", "absent", {"count": 0}),
        ("figure-inventory", "source_figure_inventory", "present_with_limitation", "present_with_limitation", {"count": 2, "omitted_source_graphics": True, "semantic_descriptions": True}),
        ("hint-inventory", "hint", "source_absent", "absent", {"count": 0}),
        ("reflowed-pdf", "reflowed_pdf_reader", "present_with_limitation", "present_with_limitation", {"artifact_id": "artifact.mit.l03.target-pdf", "pages": 2, "searchable": True, "tagged": False}),
        ("semantic-html", "semantic_html_reader", "present", "present", {"artifact_id": "artifact.mit.l03.target-html", "primary_accessible_surface": True, "lang": "id-ID"}),
        ("solution-inventory", "solution", "source_absent", "absent", {"count": 0}),
    ]
    for suffix, kind, status, presence, extra in surfaces:
        records.append(common("learning_surface", f"surface.mit.l03.{suffix}", status) | {"unit_id": unit_id, "surface_type": kind, "presence": presence, **extra})

    relations = [
        ("relation.mit.l03.parent-contains-unit", "contains", "unit.mit.ocw-6.253.spring-2012", unit_id),
        ("relation.mit.l03.contains-p014", "contains", unit_id, segment_id),
        ("relation.mit.l03.l02-precedes", "precedes", "unit.mit.ocw-6.253.l02", unit_id),
        ("relation.mit.l03.precedes-l04", "precedes", unit_id, "unit.mit.ocw-6.253.l04"),
    ]
    for record_id, relation_type, source_id, target_id in relations:
        records.append(common("relation", record_id) | {"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": "Recovered missing MIT-L03 backend overlay without altering source or reader bytes."})

    for suffix, kind, path in MIT_FILES:
        rights_id = (
            "rights.o015-mit-semantic-witness"
            if suffix == "semantic-witness"
            else "rights.o015-mit-id-pilot"
            if suffix in {"target-source", "target-html", "target-pdf"}
            else "rights.o015-mit-pilot-build-qa"
            if suffix in {"validation", "browser-qa", "independent-rereview"}
            else "rights.o015-mit-l01-backend-tooling"
        )
        extra: dict[str, Any] = {}
        if suffix in {"semantic-witness", "target-source"}:
            extra.update({"source_pdf_pages": [14], "source_figure_count": 2})
        if suffix == "target-html":
            extra.update({"locale": "id-ID", "math_format": "MathML", "source_pages": 1})
        if suffix == "target-pdf":
            extra.update({"locale": "id-ID", "pages": 2, "page_size": "A4", "tagged": False, "searchable": True})
        if suffix == "validation":
            extra["result"] = "pass"
        records.append(artifact_record(f"artifact.mit.l03.{suffix}", kind, path, rights_id, **extra))

    qa_specs = [
        ("source-freeze", "source_freeze", ["artifact.mit.complete-notes-pdf", "artifact.mit.l03.semantic-witness"], {"boundary_pages": [14], "next_source_page": 15}),
        ("build", "build", ["artifact.mit.l03.builder", "artifact.mit.l03.target-html", "artifact.mit.l03.target-pdf", "artifact.mit.l03.validation"], {"deterministic_rebuilds": 2, "html_sha256": receipt["files"]["html"]["sha256"], "pdf_sha256": receipt["files"]["pdf"]["sha256"]}),
        ("semantic-overlay", "semantic_reconstruction", ["artifact.mit.l03.semantic-witness", "artifact.mit.l03.target-source", "artifact.mit.l03.validation"], {"source_items": 2, "source_figures": 2, "official_editable_source": False}),
        ("accessibility", "accessibility", ["artifact.mit.l03.target-html", "artifact.mit.l03.target-pdf", "artifact.mit.l03.browser-qa"], {"primary_surface": "semantic_html", "html_reflow_passed": True, "pdf_searchable": True, "pdf_tagged": False}),
    ]
    for suffix, event_type, witnesses, extra in qa_specs:
        records.append(common("qa_event", f"qa.o015.mit-l03.{suffix}", "passed") | {"event_type": event_type, "result": "pass", "affected_unit_ids": [unit_id], "witness_artifact_ids": witnesses, **extra})
    return records


def original_records(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    rights_content = "d90.orig.v1.tr03.rights.content.cc-by-sa-4-0"
    rights_tooling = "d90.orig.v1.tr03.rights.tooling"
    unit_id = "d90.orig.v1.tr03.unit"
    edition_id = "d90.orig.v1.tr03.edition.id-id"
    records: list[dict[str, Any]] = [
        common("resource", "d90.orig.v1.tr03.resource", "source_admitted")
        | {
            "title": "Asesmen, Laboratorium, dan Proyek Penutup",
            "creator": "Independent Indonesian coursebook completion layer",
            "official_record": AGGREGATOR_PATH,
            "rights_id": rights_content,
            "language": "id",
            "locale": "id-ID",
            "content_origin": "independently authored original coursebook completion layer",
            "mathematical_witnesses_only": True,
            "non_endorsement": True,
        },
        common("edition", edition_id, "built")
        | {
            "edition_kind": "independent_original_coursebook_assessment_and_lab_module",
            "resource_id": "d90.orig.v1.tr03.resource",
            "rights_id": rights_content,
            "version": "original-03-id-ID-v1",
            "language": "id",
            "locale": "id-ID",
            "translation_state": "built",
            "source_artifact_id": "d90.orig.v1.tr03.artifact.source-aggregator",
            "publication_state": "local_validated_unit",
        },
        common("unit", unit_id, "built")
        | {
            "edition_id": edition_id,
            "target_edition_id": edition_id,
            "course_id": COURSE_ID,
            "unit_kind": "finite_original_course_closure",
            "order": 6,
            "source_local_label": "Original-03 cumulative assessment, proof rubrics, laboratories, and capstone",
            "target_local_label": "Asesmen, Laboratorium, dan Proyek Penutup",
            "source_locator": AGGREGATOR_PATH,
            "target_locator": AGGREGATOR_PATH,
            "translation_state": "built",
            "rights_id": rights_content,
            "curriculum_role": "finite self-study and assessment closure after Original-02",
            "assessment_material": "diagnostic, six problem sets, proof rubrics, midterm, final, staged hints, short answers, and complete solutions",
            "lab_material": "two deterministic advanced labs and one deterministic capstone with accessible JSON/CSV/SVG results",
            "o018_firewall": "excludes LP/IP, simplex, finite-dimensional LP duality, network optimization, and OR modeling",
        },
        common("rights", rights_content, "admitted")
        | {
            "component_id": "d90.orig.v1.tr03.content-labs-capstone",
            "path": f"{AGGREGATOR_PATH} + source/id-ID/original-03 + labs/original-03",
            "rights_expression": "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
            "authority_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "content_origin": "independent original writing, assessments, solutions, code, and synthetic data",
            "required_handling": ["attribute the independent completion layer", "preserve ShareAlike", "preserve cited mathematical witnesses", "state non-endorsement"],
        },
        common("rights", rights_tooling, "admitted")
        | {
            "component_id": "d90.orig.v1.tr03.backend-tooling",
            "path": "qa/extend_backend_original_03.py + qa/validate_backend_original_03.py",
            "rights_expression": "project-local deterministic backend validation tooling",
            "authority_url": "qa/extend_backend_original_03.py",
            "required_handling": ["keep source with generated records", "preserve deterministic validation evidence"],
        },
    ]

    for item in evidence["segments"]:
        records.append(
            common("segment", item["id"])
            | {
                "unit_id": unit_id,
                "order": item["order"],
                "source_local_id": f"original-03-segment-{item['order']:04d}",
                "source_local_label": item["title"],
                "target_local_label": item["title"],
                "source_edition_id": edition_id,
                "target_edition_id": edition_id,
                "source_language": "id",
                "target_language": "id",
                "target_locale": "id-ID",
                "source_path": item["path"],
                "source_line_start": 1,
                "source_line_end": item["lines"],
                "source_locator": f"{item['path']}:1-{item['lines']}",
                "source_content_bytes": item["content_bytes"],
                "source_content_sha256": item["content_sha256"],
                "target_path": item["path"],
                "target_line_start": 1,
                "target_line_end": item["lines"],
                "target_locator": f"{item['path']}:1-{item['lines']}",
                "target_content_bytes": item["content_bytes"],
                "target_content_sha256": item["content_sha256"],
                "hash_normalization": "utf8-lf-final-newline",
                "translation_state": "built",
                "content_origin": "independently_authored_original_id-ID",
                "rights_id": rights_content,
            }
        )

    for stable_id, occurrences in sorted(evidence["definitions"].items()):
        definition = next(item for item in occurrences if item.get("label"))
        record = common("learning_surface", stable_id, "present") | {
            "unit_id": unit_id,
            "surface_type": surface_type(stable_id),
            "presence": "present",
            "latex_label": definition["label"],
            "source_path": definition["path"],
            "source_line": definition["line"],
            "label_line": definition["label_line"],
            "related_segment_ids": [segment_id_for_path(definition["path"])],
            "rights_id": rights_content,
            "stable_id_binding": "exact",
        }
        index_occurrences = [item for item in occurrences if item["role"] == "assessment_index"]
        if index_occurrences:
            record["assessment_index_occurrences"] = index_occurrences
        if stable_id in SPECIAL_BINDINGS:
            record["repaired_comment_only_binding"] = True
        records.append(record)

    records.append(artifact_record("d90.orig.v1.tr03.artifact.source-aggregator", "original_tex_aggregator", AGGREGATOR_PATH, rights_content, language="id-ID", module_count=14))
    for index, relative in enumerate(MODULE_PATHS):
        lines, _, _ = normalized_full_file(relative)
        records.append(artifact_record(f"d90.orig.v1.tr03.artifact.module-{index:02d}", "original_tex_module", relative, rights_content, language="id-ID", physical_lines=lines, segment_id=f"d90.orig.v1.tr03.seg{index+1:04d}"))
    for base in LAB_BASES:
        records.extend(
            [
                artifact_record(f"d90.orig.v1.tr03.artifact.{base}-code", "open_computation_source", f"labs/original-03/{base}.py", rights_content, deterministic=True),
                artifact_record(f"d90.orig.v1.tr03.artifact.{base}-results-json", "accessible_computation_result_json", f"labs/original-03/{base}-results.json", rights_content, result="pass", certificate_count=evidence["lab"][base]["certificate_count"]),
                artifact_record(f"d90.orig.v1.tr03.artifact.{base}-results-csv", "accessible_computation_result_csv", f"labs/original-03/{base}-results.csv", rights_content, row_count=evidence["lab"][base]["csv_rows"]),
                artifact_record(f"d90.orig.v1.tr03.artifact.{base}-results-svg", "redundant_computation_plot_svg", f"labs/original-03/{base}.svg", rights_content, redundant_with_accessible_csv=True),
            ]
        )
    records.extend(
        [
            artifact_record("d90.orig.v1.tr03.artifact.backend-generator", "backend_generator", "qa/extend_backend_original_03.py", rights_tooling),
            artifact_record("d90.orig.v1.tr03.artifact.backend-validator", "backend_validator", "qa/validate_backend_original_03.py", rights_tooling),
        ]
    )

    relations = [
        ("d90.orig.v1.tr03.relation.course-contains-unit", COURSE_ID, unit_id),
        ("d90.orig.v1.tr03.relation.edition-contains-unit", edition_id, unit_id),
        *[(f"d90.orig.v1.tr03.relation.unit-contains-seg{index:04d}", unit_id, f"d90.orig.v1.tr03.seg{index:04d}") for index in range(1, 15)],
    ]
    for record_id, source_id, target_id in relations:
        records.append(common("relation", record_id) | {"relation_type": "contains", "source_id": source_id, "target_id": target_id, "note": "Original-03 course-closure topology."})

    records.extend(
        [
            common("qa_event", "d90.orig.v1.tr03.qa.stable-id-binding", "passed")
            | {
                "event_type": "stable_id_binding",
                "result": "pass",
                "affected_unit_ids": [unit_id],
                "witness_artifact_ids": [f"d90.orig.v1.tr03.artifact.module-{index:02d}" for index in range(14)],
                "stable_id_count": len(evidence["definitions"]),
                "repaired_comment_only_binding_count": len(SPECIAL_BINDINGS),
                "assessment_index_count": 54,
                "duplicate_latex_labels": 0,
            },
            common("qa_event", "d90.orig.v1.tr03.qa.computation", "passed")
            | {
                "event_type": "open_computation",
                "result": "pass",
                "affected_unit_ids": [unit_id],
                "witness_artifact_ids": [f"d90.orig.v1.tr03.artifact.{base}-results-json" for base in LAB_BASES],
                "component_results": evidence["lab"],
                "all_certificates_true": True,
            },
            common("qa_event", "d90.orig.v1.tr03.qa.rights-o018-firewall", "passed")
            | {
                "event_type": "rights_and_nonoverlap",
                "result": "pass",
                "affected_unit_ids": [unit_id],
                "witness_artifact_ids": ["d90.orig.v1.tr03.artifact.source-aggregator"],
                "rights_expression": "CC BY-SA 4.0 for independent Original-03 text, solutions, code, and synthetic data",
                "o018_ids_or_references": 0,
                "o018_firewall_declared": True,
                "non_endorsement": True,
            },
            common("qa_event", "d90.orig.v1.tr03.qa.source-freeze", "passed")
            | {
                "event_type": "source_freeze",
                "result": "pass",
                "affected_unit_ids": [unit_id],
                "witness_artifact_ids": ["d90.orig.v1.tr03.artifact.source-aggregator", *[f"d90.orig.v1.tr03.artifact.module-{index:02d}" for index in range(14)]],
                "module_count": 14,
                "segment_count": 14,
            },
        ]
    )
    return records


def correction_records() -> list[dict[str, Any]]:
    old_hash = digest(canonical(OLD_COURSE).encode("utf-8"))
    new_hash = digest(canonical(NEW_COURSE).encode("utf-8"))
    return [
        common("correction", "correction.o015.course-canonical-editable-spine", "applied")
        | {
            "affected_segment_ids": [],
            "affected_unit_ids": ["unit.habring.v1", "unit.mit.ocw-6.253.spring-2012"],
            "source_event_id": "d90.orig.v1.tr03.qa.backend-integration",
            "source_issue": "The protected course record called MIT OCW the selected primary spine although the final architecture requires a public-editable canonical spine.",
            "target_action": "Replace only source_spine_unit_ids and source_spine_note so Habring v1 is canonical and MIT/Penn/Royer remain companions.",
            "upstream_report_disposition": "not_applicable_project_metadata_only",
            "corrected_record_id": COURSE_ID,
            "old_record_sha256": old_hash,
            "new_record_sha256": new_hash,
            "changed_fields": {
                "source_spine_unit_ids": {"old": OLD_COURSE["source_spine_unit_ids"], "new": NEW_COURSE["source_spine_unit_ids"]},
                "source_spine_note": {"old": OLD_COURSE["source_spine_note"], "new": NEW_COURSE["source_spine_note"]},
            },
        }
    ]


def integration_qa_record(protected_jsonl_sha: str, protected_csv_sha: str, added_count: int) -> dict[str, Any]:
    return common("qa_event", "d90.orig.v1.tr03.qa.backend-integration", "passed") | {
        "event_type": "backend_integrity",
        "result": "pass",
        "affected_unit_ids": ["unit.mit.ocw-6.253.l03", "d90.orig.v1.tr03.unit"],
        "witness_artifact_ids": ["d90.orig.v1.tr03.artifact.backend-generator", "d90.orig.v1.tr03.artifact.backend-validator"],
        "protected_prior_record_count": 4337,
        "corrected_prior_record_count": 1,
        "added_record_count": added_count,
        "protected_baseline_jsonl_sha256": protected_jsonl_sha,
        "protected_baseline_csv_sha256": protected_csv_sha,
        "raw_record_bytes_and_relative_order_preserved_except_course": True,
        "jsonl_csv_lossless_equality": True,
        "deterministic_regeneration_runs_required": 2,
    }


def validate_records(records: list[dict[str, Any]], schema: dict[str, Any], baseline: list[dict[str, Any]]) -> None:
    if records != ordered(records, schema):
        raise ValueError("records are not in deterministic entity/id order")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        duplicates = [record_id for record_id, count in Counter(ids).items() if count > 1]
        raise ValueError(f"duplicate backend IDs: {duplicates[:20]}")
    id_pattern = re.compile(schema["id_pattern"])
    by_id = {record["id"]: record for record in records}
    for record in records:
        for field in schema["required_common"]:
            if field not in record:
                raise ValueError(f"{record['id']} lacks common field {field}")
        if record["schema"] != RECORD_SCHEMA or record["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"{record['id']} has wrong record schema")
        if record["entity_type"] not in schema["entity_order"] or not id_pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid entity or stable ID: {record['id']}")
        for field in schema["required_by_entity"].get(record["entity_type"], []):
            if field not in record:
                raise ValueError(f"{record['id']} lacks required {record['entity_type']} field {field}")
        for field in schema["reference_fields"]:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value is not None and value not in by_id:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")
        if record["entity_type"] == "relation" and record["relation_type"] not in schema["relation_types"]:
            raise ValueError(f"{record['id']} has invalid relation type")

    baseline_by_id = {record["id"]: record for record in baseline}
    for record_id, old_record in baseline_by_id.items():
        if record_id == COURSE_ID:
            if by_id[record_id] != NEW_COURSE:
                raise ValueError("authorized course correction is not exact")
        elif by_id.get(record_id) != old_record:
            raise ValueError(f"protected baseline record changed: {record_id}")
    protected_order = [record["id"] for record in records if record["id"] in baseline_by_id and record["id"] != COURSE_ID]
    expected_order = [record["id"] for record in ordered(baseline, schema) if record["id"] != COURSE_ID]
    if protected_order != expected_order:
        raise ValueError("protected prior-record relative order changed")

    for record in records:
        if record["entity_type"] == "artifact" and record.get("responsible_workflow") == WORKFLOW:
            path = ROOT / record["path"]
            if path.is_file():
                data = path.read_bytes()
                if len(data) != record["bytes"] or digest(data) != record["sha256"]:
                    raise ValueError(f"artifact binding changed: {record['id']}")
        if record["entity_type"] == "segment" and record.get("responsible_workflow") == WORKFLOW:
            _, content_bytes, content_sha = normalized_full_file(record["source_path"])
            if record["source_content_bytes"] != content_bytes or record["source_content_sha256"] != content_sha:
                raise ValueError(f"source segment binding changed: {record['id']}")

    for record in records:
        if record.get("responsible_workflow") != WORKFLOW:
            continue
        blob = canonical(record).lower()
        if record["id"].startswith("d90.orig.v1.tr03.") and ('"o018.' in blob or '"course.o018' in blob or '"unit.o018' in blob):
            raise ValueError(f"O018 stable-ID leakage into Original-03 record: {record['id']}")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def build(output_jsonl: Path, output_csv: Path, write_receipt: bool) -> dict[str, Any]:
    schema = assert_schema()
    baseline, baseline_jsonl, baseline_csv, recovery = recover_baseline(schema)
    original_evidence = source_evidence()
    mit_evidence = validate_mit_evidence()

    additions = mit_records(mit_evidence) + original_records(original_evidence) + correction_records()
    additions.append(integration_qa_record(digest(baseline_jsonl), digest(baseline_csv), len(additions) + 1))
    baseline_corrected = [dict(NEW_COURSE) if record["id"] == COURSE_ID else record for record in baseline]
    final_records = ordered([*baseline_corrected, *additions], schema)
    validate_records(final_records, schema, baseline)
    output_jsonl_bytes, output_csv_bytes = serialize(final_records, schema)
    if parse_jsonl(output_jsonl_bytes) != parse_csv(output_csv_bytes, schema):
        raise ValueError("generated JSONL/CSV lossless equality failed")

    old_hash = digest(canonical(OLD_COURSE).encode("utf-8"))
    new_hash = digest(canonical(NEW_COURSE).encode("utf-8"))
    added = [record for record in final_records if record.get("responsible_workflow") == WORKFLOW]
    protected = [record for record in baseline if record["id"] != COURSE_ID]
    receipt: dict[str, Any] = {
        "schema": "o015-original-03-backend-extension-v1",
        "workflow": WORKFLOW,
        "result": "pass",
        "write_mode": "canonical" if write_receipt else "staging",
        "schema_identity": SCHEMA_IDENTITY | {"schema_changed": False},
        "input_recovery": recovery,
        "protected_baseline": {
            "records": BASELINE["records"],
            "protected_records_byte_identical": len(protected),
            "corrected_records": 1,
            "jsonl": {"bytes": len(baseline_jsonl), "sha256": digest(baseline_jsonl)},
            "csv": {"bytes": len(baseline_csv), "sha256": digest(baseline_csv)},
            "protected_id_order_sha256": id_order_sha(protected),
            "protected_record_set_sha256": record_set_sha(protected),
            "raw_record_bytes_and_relative_order_preserved_except_course": True,
        },
        "course_correction": {
            "record_id": COURSE_ID,
            "old_record_sha256": old_hash,
            "new_record_sha256": new_hash,
            "changed_field_count": 2,
            "changed_fields": {
                key: {
                    "old": OLD_COURSE[key],
                    "new": NEW_COURSE[key],
                    "old_value_sha256": digest(canonical(OLD_COURSE[key]).encode("utf-8")),
                    "new_value_sha256": digest(canonical(NEW_COURSE[key]).encode("utf-8")),
                }
                for key in ("source_spine_unit_ids", "source_spine_note")
            },
        },
        "mit_l03_overlay": {
            "unit_id": "unit.mit.ocw-6.253.l03",
            "segment_id": "d90.mit.ocw-6.253.l03.p014",
            "source_page": 14,
            "source_and_reader_bytes_unchanged": True,
            "anchor_bindings": len(mit_evidence["source_ids"]),
            "files": mit_evidence["files"],
        },
        "original_03": {
            "unit_id": "d90.orig.v1.tr03.unit",
            "module_count": 14,
            "segment_count": 14,
            "stable_id_bindings": len(original_evidence["definitions"]),
            "repaired_comment_only_bindings": len(SPECIAL_BINDINGS),
            "assessment_index_bindings": 54,
            "latex_label_count": len(original_evidence["labels"]),
            "lab_components": original_evidence["lab"],
            "o018_firewall": "pass",
        },
        "admission": {
            "prior_records": len(baseline),
            "protected_records": len(protected),
            "corrected_records": 1,
            "added_records": len(added),
            "added_entity_counts": dict(sorted(Counter(record["entity_type"] for record in added).items())),
            "final_records": len(final_records),
            "jsonl": {"bytes": len(output_jsonl_bytes), "sha256": digest(output_jsonl_bytes)},
            "csv": {"bytes": len(output_csv_bytes), "sha256": digest(output_csv_bytes)},
            "final_id_set_sha256": id_set_sha(final_records),
            "final_id_order_sha256": id_order_sha(final_records),
            "final_record_set_sha256": record_set_sha(final_records),
            "added_id_set_sha256": id_set_sha(added),
            "added_record_set_sha256": record_set_sha(added),
            "jsonl_csv_lossless_equality": True,
        },
        "inputs": [
            file_info(AGGREGATOR_PATH),
            *[file_info(path) for path in MODULE_PATHS],
            *[file_info(path) for path in LAB_PATHS],
            file_info("qa/extend_backend_original_03.py"),
            file_info("qa/validate_backend_original_03.py"),
        ],
    }

    atomic_write(output_jsonl, output_jsonl_bytes)
    atomic_write(output_csv, output_csv_bytes)
    if write_receipt:
        atomic_write(RECEIPT_PATH, (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write-canonical", action="store_true")
    mode.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.write_canonical:
        output_jsonl, output_csv, canonical_mode = JSONL_PATH, CSV_PATH, True
    else:
        output_dir = args.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_jsonl, output_csv, canonical_mode = output_dir / "records.jsonl", output_dir / "records.csv", False
    try:
        receipt = build(output_jsonl, output_csv, canonical_mode)
    except Exception as exc:
        print(json.dumps({"schema": "o015-original-03-backend-extension-v1", "result": "fail", "error": str(exc)}, ensure_ascii=False, indent=2, sort_keys=True))
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
