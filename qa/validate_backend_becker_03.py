#!/usr/bin/env python3
"""Independently validate the additive Becker-03 backend admission.

This validator intentionally does not import the Becker-03 generator. It
recomputes evidence bindings, segment and semantic-surface topology, stable-ID
closure, the exact 3,430-record baseline recovery, and two-run regeneration.
Missing final B03 artifacts or receipts are hard failures.
"""

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
RECEIPT_PATH = ROOT / "qa" / "BECKER_03_BACKEND_VALIDATION.json"
GENERATOR = ROOT / "qa" / "extend_backend_becker_03.py"

WORKFLOW = "o015-becker-03-backend-v1"
BASE = "d90.becker.98ed693.b03"
UNIT_ID = f"{BASE}.unit"
SOURCE_EDITION_ID = f"{BASE}.edition.source"
TARGET_EDITION_ID = f"{BASE}.edition.target"

SCHEMA_IDENTITY = (
    3_092,
    "1166cbffe6016044430fe003e4981b1a3a537be7c115f0b646168a1936ab5ad0",
)
BASELINE_COUNT = 3_430
BASELINE_JSONL = (
    2_623_909,
    "6943678e867b5f72a509e1dbc57dcdbc61c79cc7ced3828fc3b8da999dff3ae6",
)
BASELINE_CSV = (
    3_142_537,
    "4e3249844a4948f02522c300ff69d313cabda2768d23f7f6f674b9c25ae08f97",
)
BASELINE_ID_SET_SHA256 = "2049edb1e0d183bb6fb96f4fda97b3a9cced7a404f4a32ecd2a52cca50175f8f"
BASELINE_ID_ORDER_SHA256 = "5fbb8bc4f9ef7d70bb7062a3ade0dbedb8bd0f6ca14c154eb7d4df2572216ff0"
BASELINE_RECORD_SET_SHA256 = "2d1b24aeadd13b165463e9e6e987b5ccc418b46b937b6d28d8ccb38246964768"
BASELINE_LINE_SEQUENCE_SHA256 = "0969a6be2816f4c8c0fb38d43af8925cbb7867dd685786000273b6a0a4a6edc2"

COMMIT = "98ed6930084c435ba0f675f7646ced1f2fd8729e"
AUTHORITY = (
    "authority/becker/extract/"
    f"convex-optimization-class-{COMMIT}/TypedNotes/APPM5720Notes.tex"
)
WITNESS = "source/en/becker-03-variance-reduction-source.tex"
TARGET = "source/id-ID/becker-03-reduksi-varians-id.tex"
WRAPPER = "source/id-ID/D90-BECKER-03-reduksi-varians-id.tex"
BOUNDARY = "qa/BECKER_03_SOURCE_BOUNDARY.json"
EXTRACTOR = "qa/extract_becker_variance_reduction_source.py"
PDF_BUILDER = "qa/build_becker_variance_reduction_pdf.py"
PDF_REPORT = "qa/BECKER_03_PDF_BUILD.json"
PDF = "output/pdf/D90-BECKER-03-reduksi-varians-id.pdf"
HTML_BUILDER = "qa/build_becker_variance_reduction_html.py"
HTML_REPORT = "qa/BECKER_03_HTML_BUILD.json"
HTML = "output/html/D90-BECKER-03-reduksi-varians-id.html"
MATH_VALIDATOR = "qa/validate_becker_variance_reduction_math.py"
MATH_REPORT = "qa/BECKER_03_MATH_VALIDATION.json"
BACKEND_GENERATOR = "qa/extend_backend_becker_03.py"
BACKEND_VALIDATOR = "qa/validate_backend_becker_03.py"

AUTHORITY_IDENTITY = (
    130_911,
    "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8",
)
WITNESS_IDENTITY = (
    977,
    "66f243b97cd379b73d217c6a3e424db688f8ace246852cb24f78108c53186607",
)
SOURCE_SLICE_IDENTITY = (
    900,
    "b81634bf07565fcf8d2774bea7b96e565e5fdd76cf5e782c5e4eb6fb3268c5ed",
)

TOPIC_SLUGS = (
    "finite-sum-saa",
    "saga-estimator",
    "variance-reduction-mechanism",
    "saga-convergence-and-averaging",
    "variance-reduction-practice",
)
TOPIC_PREREQUISITES = {
    "finite-sum-saa": (),
    "saga-estimator": ("finite-sum-saa",),
    "variance-reduction-mechanism": ("saga-estimator",),
    "saga-convergence-and-averaging": ("saga-estimator", "variance-reduction-mechanism"),
    "variance-reduction-practice": ("variance-reduction-mechanism",),
}
SEGMENT_DEFS = (
    (1, "% B03-S001 | APPM5720Notes.tex baris 2971-2972", 2971, 2972, "finite-sum-saa"),
    (2, "% B03-S002 | APPM5720Notes.tex baris 2974-2981", 2974, 2981, "saga-estimator"),
    (3, "% B03-S003 | penghubung matematis mandiri untuk baris 2974-2981", 2974, 2981, "variance-reduction-mechanism"),
    (4, "% B03-S004 | APPM5720Notes.tex baris 2982-2988 dengan hipotesis diperbaiki", 2982, 2988, "saga-convergence-and-averaging"),
    (5, "% B03-S005 | latihan, petunjuk, dan solusi mandiri", 2971, 2988, "variance-reduction-practice"),
)
PRESENT_SURFACES = {
    "chapter": 1,
    "section": 4,
    "theorem": 1,
    "proposition": 1,
    "proof": 1,
    "equation": 14,
    "exercise": 2,
    "hint": 2,
    "solution": 2,
}
SOURCE_ABSENT_SURFACES = ("exercise", "hint", "answer", "solution")
QA_SUFFIXES = {
    "source-freeze",
    "segment-binding",
    "semantic-surfaces",
    "pdf-build",
    "html-build",
    "math-validation",
    "rights",
    "backend-integration",
}
ARTIFACT_SUFFIX_PATHS = {
    "authority-tex": AUTHORITY,
    "source-witness": WITNESS,
    "target-body": TARGET,
    "target-wrapper": WRAPPER,
    "source-boundary": BOUNDARY,
    "extractor": EXTRACTOR,
    "pdf-builder": PDF_BUILDER,
    "pdf-build-report": PDF_REPORT,
    "pdf-reader": PDF,
    "html-builder": HTML_BUILDER,
    "html-build-report": HTML_REPORT,
    "html-reader": HTML,
    "math-validator": MATH_VALIDATOR,
    "math-validation-report": MATH_REPORT,
    "backend-generator": BACKEND_GENERATOR,
    "backend-validator": BACKEND_VALIDATOR,
}

ENVIRONMENT_SURFACE = {
    "theorem": "theorem",
    "thrm": "theorem",
    "prop": "proposition",
    "proposition": "proposition",
    "proof": "proof",
    "exercise": "exercise",
    "equation": "equation",
    "equation*": "equation",
    "multline": "equation",
    "multline*": "equation",
    "align": "equation",
    "align*": "equation",
    "gather": "equation",
    "gather*": "equation",
}
TOKEN = re.compile(r"\\(?P<kind>begin|end)\{(?P<env>[^}]+)\}")
HEADING = re.compile(r"^\\(?P<kind>chapter|section|subsection)\*?\{(?P<title>.+)\}$")
TEXT_SURFACE = re.compile(r"^\\noindent\\textbf\{(?P<label>Petunjuk|Solusi lengkap)\.\}(?:\\par)?$")


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"required final Becker-03 artifact is missing: {relative}")
    raw = path.read_bytes()
    if not raw:
        raise ValueError(f"required final Becker-03 artifact is empty: {relative}")
    return len(raw), digest(raw)


def normalized_slice(relative: str, start: int, end: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid normalized slice {relative}:{start}-{end}")
    raw = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
    return len(raw), digest(raw)


def id_set(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def id_order(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(record["id"] for record in records) + "\n").encode("utf-8"))


def record_set(records: list[dict[str, Any]]) -> str:
    payload = "\n".join(canonical(record) for record in sorted(records, key=lambda item: item["id"])) + "\n"
    return digest(payload.encode("utf-8"))


def line_sequence(raw: bytes) -> str:
    hashes = [digest(line) for line in raw.splitlines(keepends=True)]
    return digest(("\n".join(hashes) + "\n").encode("utf-8"))


def strip_jsonl(raw: bytes) -> bytes:
    return b"".join(
        line
        for line in raw.splitlines(keepends=True)
        if json.loads(line.decode("utf-8")).get("responsible_workflow") != WORKFLOW
    )


def strip_csv(raw: bytes) -> bytes:
    lines = raw.splitlines(keepends=True)
    if not lines:
        raise ValueError("backend CSV is empty")
    kept = [lines[0]]
    for line in lines[1:]:
        row = next(csv.reader(io.StringIO(line.decode("utf-8"))))
        if len(row) != 5:
            raise ValueError("backend CSV row width differs")
        if json.loads(row[4]).get("responsible_workflow") != WORKFLOW:
            kept.append(line)
    return b"".join(kept)


def assert_schema_identity() -> dict[str, Any]:
    if file_info("backend/backend_schema.json") != SCHEMA_IDENTITY:
        raise ValueError("backend schema bytes differ from protected v1.0.0 schema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema" or schema.get("schema_version") != "1.0.0":
        raise ValueError("backend schema identity fields differ")
    return schema


def reported_identities(value: Any) -> set[tuple[str, int, str]]:
    found: set[tuple[str, int, str]] = set()
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("bytes"), int) and isinstance(value.get("sha256"), str):
            found.add((value["path"], value["bytes"], value["sha256"]))
        for child in value.values():
            found.update(reported_identities(child))
    elif isinstance(value, list):
        for child in value:
            found.update(reported_identities(child))
    return found


def require_bindings(report: dict[str, Any], paths: list[str], label: str) -> None:
    identities = reported_identities(report)
    for relative in paths:
        size, sha = file_info(relative)
        if (relative, size, sha) not in identities:
            raise ValueError(f"{label} does not bind current bytes: {relative}")


def validate_evidence() -> dict[str, Any]:
    for relative in ARTIFACT_SUFFIX_PATHS.values():
        file_info(relative)
    if file_info(AUTHORITY) != AUTHORITY_IDENTITY:
        raise ValueError("Becker-03 frozen authority identity differs")
    if file_info(WITNESS) != WITNESS_IDENTITY:
        raise ValueError("Becker-03 source-witness identity differs")
    if normalized_slice(AUTHORITY, 2971, 2988) != SOURCE_SLICE_IDENTITY:
        raise ValueError("Becker-03 admitted authority slice differs")
    authority_lines = (ROOT / AUTHORITY).read_text(encoding="utf-8").splitlines()
    witness_lines = (ROOT / WITNESS).read_text(encoding="utf-8").splitlines()
    if (
        witness_lines[0] != "% BEGIN variance-reduction | frozen lines 2971-2988"
        or witness_lines[-1] != "% END variance-reduction"
        or witness_lines[1:-1] != authority_lines[2970:2988]
    ):
        raise ValueError("Becker-03 witness interior differs")
    wrapper = (ROOT / WRAPPER).read_text(encoding="utf-8")
    wrapper_markers = (
        f"% unit-id: {UNIT_ID}",
        f"% source-edition-id: {SOURCE_EDITION_ID}",
        f"% target-edition-id: {TARGET_EDITION_ID}",
        "\\input{becker-03-reduksi-varians-id}",
    )
    if any(wrapper.count(marker) != 1 for marker in wrapper_markers):
        raise ValueError("Becker-03 wrapper marker/input closure differs")

    boundary = json.loads((ROOT / BOUNDARY).read_text(encoding="utf-8"))
    if boundary.get("schema") != "o015-becker-03-source-boundary-v1" or boundary.get("result") != "pass" or boundary.get("upstream_contact") is not False:
        raise ValueError("Becker-03 source boundary is not a strict pass")
    authority = boundary.get("authority", {})
    if authority.get("commit") != COMMIT or authority.get("source_path") != AUTHORITY or authority.get("source_sha256") != AUTHORITY_IDENTITY[1] or authority.get("license") != "MIT":
        raise ValueError("Becker-03 authority binding differs")
    selected = boundary.get("selected_ranges", [])
    if (
        len(selected) != 1
        or selected[0].get("id") != "variance-reduction"
        or selected[0].get("first_line") != 2971
        or selected[0].get("last_line") != 2988
        or selected[0].get("line_count") != 18
        or (selected[0].get("bytes"), selected[0].get("sha256")) != SOURCE_SLICE_IDENTITY
    ):
        raise ValueError("Becker-03 selected source range differs")
    combined = boundary.get("combined_witness", {})
    if combined.get("path") != WITNESS or (combined.get("bytes"), combined.get("sha256")) != WITNESS_IDENTITY or combined.get("exact_expected_byte_match") is not True or combined.get("interior_exact_source_slice_match") is not True:
        raise ValueError("Becker-03 source-witness boundary binding differs")

    pdf = json.loads((ROOT / PDF_REPORT).read_text(encoding="utf-8"))
    pdf_artifact = pdf.get("artifact", {})
    if (
        pdf.get("schema") != "o015-becker-03-pdf-build-v1"
        or pdf.get("result") != "pass"
        or pdf.get("byte_identical_clean_builds") is not True
        or pdf.get("canonical_copy_exact_match") is not True
        or pdf.get("upstream_contact") is not False
        or pdf_artifact.get("path") != PDF
        or (pdf_artifact.get("bytes"), pdf_artifact.get("sha256")) != file_info(PDF)
        or not isinstance(pdf_artifact.get("pages"), int)
        or pdf_artifact.get("pages", 0) <= 0
        or pdf_artifact.get("language") != "id-ID"
        or pdf_artifact.get("encrypted") is not False
        or pdf_artifact.get("missing_markers") != []
    ):
        raise ValueError("Becker-03 PDF evidence differs")
    require_bindings(pdf, [TARGET, WRAPPER, WITNESS, EXTRACTOR, BOUNDARY, PDF], "PDF report")

    html = json.loads((ROOT / HTML_REPORT).read_text(encoding="utf-8"))
    html_artifact = html.get("artifact", {})
    byte_identical = html.get("byte_identical_clean_builds") is True or html.get("byte_identical_builds") is True
    if html.get("schema") != "o015-becker-03-html-build-v1" or html.get("result") != "pass" or not byte_identical or html.get("upstream_contact") is not False or html_artifact.get("path") != HTML or (html_artifact.get("bytes"), html_artifact.get("sha256")) != file_info(HTML) or html_artifact.get("failures", []) != []:
        raise ValueError("Becker-03 HTML evidence differs")
    require_bindings(html, [TARGET, WRAPPER, WITNESS, HTML], "HTML report")

    math = json.loads((ROOT / MATH_REPORT).read_text(encoding="utf-8"))
    math_result = str(math.get("result", math.get("status", ""))).casefold()
    if math.get("schema") != "o015-becker-03-open-math-validation-v1" or math_result != "pass" or math.get("failures", []) != [] or math.get("scope", {}).get("upstream_contact") is not False:
        raise ValueError("Becker-03 mathematical validation evidence differs")
    require_bindings(math, [WITNESS, TARGET, WRAPPER, MATH_VALIDATOR], "math report")
    gate_count = math.get("gate_count", math.get("check_count"))
    if not isinstance(gate_count, int) or gate_count <= 0:
        raise ValueError("Becker-03 math report lacks a positive gate count")
    return {"boundary": boundary, "pdf": pdf, "html": html, "math": math}


def discover_segments() -> list[dict[str, Any]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    marker_map = {marker: (number, source_start, source_end, topic) for number, marker, source_start, source_end, topic in SEGMENT_DEFS}
    found: list[tuple[int, int, int, int, str, str]] = []
    for target_line, line in enumerate(lines, 1):
        if line in marker_map:
            number, source_start, source_end, topic = marker_map[line]
            found.append((target_line, number, source_start, source_end, topic, line))
    if [item[1] for item in found] != list(range(1, 6)):
        raise ValueError("Becker-03 five-marker closure differs")
    result: list[dict[str, Any]] = []
    for index, (target_start, number, source_start, source_end, topic, marker) in enumerate(found):
        segment_id = f"{BASE}.seg{number:04d}"
        if target_start >= len(lines) or lines[target_start] != f"% segment-id: {segment_id}":
            raise ValueError(f"Becker-03 stable marker differs: {segment_id}")
        target_end = found[index + 1][0] - 1 if index + 1 < len(found) else len(lines)
        result.append(
            {
                "id": segment_id,
                "number": number,
                "marker": marker,
                "source_start": source_start,
                "source_end": source_end,
                "target_start": target_start,
                "target_end": target_end,
                "topic_id": f"{BASE}.topic.{topic}",
            }
        )
    return result


def segment_for_line(segments: list[dict[str, Any]], line_number: int) -> dict[str, Any]:
    matches = [segment for segment in segments if segment["target_start"] <= line_number <= segment["target_end"]]
    if len(matches) != 1:
        raise ValueError(f"target line {line_number} has {len(matches)} Becker-03 segments")
    return matches[0]


def discover_present_surfaces(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    found: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    text_markers: list[tuple[int, str]] = []
    exercise_starts: list[int] = []
    for line_number, raw in enumerate(lines, 1):
        line = re.sub(r"(?<!\\)%.*", "", raw).strip()
        heading = HEADING.fullmatch(line)
        if heading:
            found.append({"surface_type": heading.group("kind"), "environment": "latex-heading", "start": line_number, "end": line_number})
        text = TEXT_SURFACE.fullmatch(line)
        if text:
            text_markers.append((line_number, "hint" if text.group("label") == "Petunjuk" else "solution"))
        for match in TOKEN.finditer(line):
            environment = match.group("env")
            if match.group("kind") == "begin":
                stack.append((environment, line_number))
                if environment == "exercise":
                    exercise_starts.append(line_number)
                continue
            if not stack or stack[-1][0] != environment:
                raise ValueError(f"unbalanced {environment} at {TARGET}:{line_number}")
            opened, start = stack.pop()
            if opened in ENVIRONMENT_SURFACE:
                found.append({"surface_type": ENVIRONMENT_SURFACE[opened], "environment": opened, "start": start, "end": line_number})
    if stack:
        raise ValueError(f"unclosed TeX environment in {TARGET}")
    boundaries = sorted(set([number for number, _ in text_markers] + exercise_starts + [len(lines) + 1]))
    for start, surface_type in text_markers:
        end = min(number for number in boundaries if number > start) - 1
        while end > start and not lines[end - 1].strip():
            end -= 1
        found.append({"surface_type": surface_type, "environment": "latex-bold-heading", "start": start, "end": end})
    counts = Counter(item["surface_type"] for item in found)
    if counts != Counter(PRESENT_SURFACES):
        raise ValueError(f"Becker-03 present-surface census differs: {dict(counts)}")
    counters: Counter[str] = Counter()
    result: list[dict[str, Any]] = []
    for item in sorted(found, key=lambda value: (value["start"], value["end"], value["surface_type"], value["environment"])):
        counters[item["surface_type"]] += 1
        segment = segment_for_line(segments, item["start"])
        result.append(
            {
                **item,
                "id": f"{BASE}.{item['surface_type']}.{counters[item['surface_type']]:04d}",
                "segment_id": segment["id"],
                "topic_id": segment["topic_id"],
            }
        )
    return result


def expected_surface_ids(present: list[dict[str, Any]]) -> set[str]:
    result = {item["id"] for item in present}
    result.update(f"{BASE}.source.{kind}.closure" for kind in SOURCE_ABSENT_SURFACES)
    return result


def expected_relation_map(segments: list[dict[str, Any]], present: list[dict[str, Any]]) -> dict[str, tuple[str, str, str]]:
    relations = {
        f"{BASE}.relation.course-contains-unit": ("contains", "course.d90.advanced-optimization-convex-analysis", UNIT_ID),
        f"{BASE}.relation.b02-precedes-b03": ("precedes", "d90.becker.98ed693.b02.unit", UNIT_ID),
        f"{BASE}.relation.resource-contains-source-edition": ("contains", f"{BASE}.resource", SOURCE_EDITION_ID),
        f"{BASE}.relation.resource-contains-target-edition": ("contains", f"{BASE}.resource", TARGET_EDITION_ID),
        f"{BASE}.relation.target-translates-witness": ("translates", f"{BASE}.artifact.target-body", f"{BASE}.artifact.source-witness"),
        f"{BASE}.relation.wrapper-adapts-target": ("adapts", f"{BASE}.artifact.target-wrapper", f"{BASE}.artifact.target-body"),
        f"{BASE}.relation.pdf-adapts-wrapper": ("adapts", f"{BASE}.artifact.pdf-reader", f"{BASE}.artifact.target-wrapper"),
        f"{BASE}.relation.html-adapts-target": ("adapts", f"{BASE}.artifact.html-reader", f"{BASE}.artifact.target-body"),
    }
    for segment in segments:
        relations[f"{BASE}.relation.unit-contains-seg{segment['number']:04d}"] = ("contains", UNIT_ID, segment["id"])
    for slug in TOPIC_SLUGS:
        relations[f"{BASE}.relation.unit-contains-topic-{slug}"] = ("contains", UNIT_ID, f"{BASE}.topic.{slug}")
    all_surface_ids = expected_surface_ids(present)
    for surface_id in all_surface_ids:
        suffix = surface_id.removeprefix(f"{BASE}.").replace(".", "-")
        relations[f"{BASE}.relation.unit-contains-{suffix}"] = ("contains", UNIT_ID, surface_id)
    for surface in present:
        suffix = surface["id"].removeprefix(f"{BASE}.").replace(".", "-")
        relation_type = "proves" if surface["surface_type"] in {"theorem", "proposition", "proof"} else "exercises" if surface["surface_type"] in {"exercise", "hint", "solution"} else "illustrates"
        relations[f"{BASE}.relation.{suffix}-to-topic"] = (relation_type, surface["id"], surface["topic_id"])
    present_ids = {surface["id"] for surface in present}
    for number in (1, 2):
        exercise_id = f"{BASE}.exercise.{number:04d}"
        hint_id = f"{BASE}.hint.{number:04d}"
        solution_id = f"{BASE}.solution.{number:04d}"
        if not {exercise_id, hint_id, solution_id} <= present_ids:
            raise ValueError(f"missing exercise/hint/solution pairing for Becker-03 item {number}")
        relations[f"{BASE}.relation.hint-{number:04d}-depends-on-exercise-{number:04d}"] = ("depends-on", hint_id, exercise_id)
        relations[f"{BASE}.relation.solution-{number:04d}-depends-on-exercise-{number:04d}"] = ("depends-on", solution_id, exercise_id)
    return relations


def expected_ids(segments: list[dict[str, Any]], present: list[dict[str, Any]]) -> set[str]:
    result = {
        f"{BASE}.resource",
        SOURCE_EDITION_ID,
        TARGET_EDITION_ID,
        UNIT_ID,
        f"{BASE}.rights.source.mit",
        f"{BASE}.rights.target.mixed",
        f"{BASE}.rights.tooling",
    }
    result.update(f"{BASE}.topic.{slug}" for slug in TOPIC_SLUGS)
    result.update(segment["id"] for segment in segments)
    result.update(expected_surface_ids(present))
    result.update(f"{BASE}.artifact.{suffix}" for suffix in ARTIFACT_SUFFIX_PATHS)
    result.update(f"{BASE}.qa.{suffix}" for suffix in QA_SUFFIXES)
    result.update(expected_relation_map(segments, present))
    return result


def validate_dataset(jsonl_path: Path, csv_path: Path) -> dict[str, Any]:
    schema = assert_schema_identity()
    validate_evidence()
    segments = discover_segments()
    present_specs = discover_present_surfaces(segments)

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
    all_ids = {record["id"] for record in records}
    id_pattern = re.compile(schema["id_pattern"])
    for record in records:
        if record["entity_type"] not in rank:
            raise ValueError(f"unknown entity type {record['entity_type']}")
        missing = [field for field in schema["required_common"] + schema["required_by_entity"].get(record["entity_type"], []) if field not in record]
        if missing:
            raise ValueError(f"{record['id']} lacks required fields {missing}")
        if not id_pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid stable ID {record['id']}")
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

    for record in records:
        owned = record.get("responsible_workflow") == WORKFLOW
        namespaced = record["id"].startswith(f"{BASE}.")
        if owned != namespaced:
            raise ValueError(f"workflow/namespace ownership differs for {record['id']}")

    baseline_jsonl = strip_jsonl(jsonl_raw)
    baseline_csv = strip_csv(csv_raw)
    if (len(baseline_jsonl), digest(baseline_jsonl)) != BASELINE_JSONL or (len(baseline_csv), digest(baseline_csv)) != BASELINE_CSV or line_sequence(baseline_jsonl) != BASELINE_LINE_SEQUENCE_SHA256:
        raise ValueError("workflow stripping does not recover exact Becker-02 bytes")
    baseline = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    new = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    if len(baseline) != BASELINE_COUNT or id_set(baseline) != BASELINE_ID_SET_SHA256 or id_order(baseline) != BASELINE_ID_ORDER_SHA256 or record_set(baseline) != BASELINE_RECORD_SET_SHA256:
        raise ValueError("protected Becker-02 baseline record set/order differs")

    expected = expected_ids(segments, present_specs)
    if {record["id"] for record in new} != expected:
        missing = sorted(expected - {record["id"] for record in new})
        extra = sorted({record["id"] for record in new} - expected)
        raise ValueError(f"Becker-03 stable-ID set differs; missing={missing}, extra={extra}")
    expected_relations = expected_relation_map(segments, present_specs)
    expected_counts = Counter(
        {
            "resource": 1,
            "edition": 2,
            "unit": 1,
            "concept": len(TOPIC_SLUGS),
            "segment": len(segments),
            "learning_surface": len(present_specs) + len(SOURCE_ABSENT_SURFACES),
            "rights": 3,
            "artifact": len(ARTIFACT_SUFFIX_PATHS),
            "qa_event": len(QA_SUFFIXES),
            "relation": len(expected_relations),
        }
    )
    if Counter(record["entity_type"] for record in new) != expected_counts:
        raise ValueError("Becker-03 entity topology differs")

    by_id = {record["id"]: record for record in records}
    target_lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    unit = by_id[UNIT_ID]
    if unit.get("order") != 3 or unit.get("source_edition_id") != SOURCE_EDITION_ID or unit.get("target_edition_id") != TARGET_EDITION_ID or unit.get("target_locator") != f"{TARGET}:1-{len(target_lines)}":
        raise ValueError("Becker-03 unit topology differs")

    for segment in segments:
        record = by_id[segment["id"]]
        if (
            record.get("order") != segment["number"]
            or record.get("source_path") != AUTHORITY
            or record.get("source_line_start") != segment["source_start"]
            or record.get("source_line_end") != segment["source_end"]
            or (record.get("source_content_bytes"), record.get("source_content_sha256")) != normalized_slice(AUTHORITY, segment["source_start"], segment["source_end"])
            or record.get("target_path") != TARGET
            or record.get("target_line_start") != segment["target_start"]
            or record.get("target_line_end") != segment["target_end"]
            or (record.get("target_content_bytes"), record.get("target_content_sha256")) != normalized_slice(TARGET, segment["target_start"], segment["target_end"])
            or record.get("concept_ids") != [segment["topic_id"]]
        ):
            raise ValueError(f"Becker-03 segment binding differs: {segment['id']}")
        if target_lines[segment["target_start"] - 1] != segment["marker"] or target_lines[segment["target_start"]] != f"% segment-id: {segment['id']}":
            raise ValueError(f"Becker-03 segment marker differs: {segment['id']}")

    for number, slug in enumerate(TOPIC_SLUGS, 1):
        concept = by_id[f"{BASE}.topic.{slug}"]
        expected_prerequisites = [f"{BASE}.topic.{item}" for item in TOPIC_PREREQUISITES[slug]]
        if concept.get("prerequisite_ids") != expected_prerequisites or concept.get("related_segment_ids") != [f"{BASE}.seg{number:04d}"]:
            raise ValueError(f"Becker-03 topic topology differs: {slug}")

    discovered = {item["id"]: item for item in present_specs}
    surfaces = [record for record in new if record["entity_type"] == "learning_surface"]
    present_records = [record for record in surfaces if record.get("presence") == "present"]
    closure_records = [record for record in surfaces if record.get("presence") == "absent"]
    if Counter(record["surface_type"] for record in present_records) != Counter(PRESENT_SURFACES):
        raise ValueError("Becker-03 stored present-surface census differs")
    if {record["id"] for record in closure_records} != {f"{BASE}.source.{kind}.closure" for kind in SOURCE_ABSENT_SURFACES}:
        raise ValueError("Becker-03 donor absence closure differs")
    for record in present_records:
        item = discovered[record["id"]]
        if (
            record.get("target_line_start") != item["start"]
            or record.get("target_line_end") != item["end"]
            or record.get("latex_environment") != item["environment"]
            or record.get("related_segment_ids") != [item["segment_id"]]
            or record.get("concept_ids") != [item["topic_id"]]
            or (record.get("target_content_bytes"), record.get("target_content_sha256")) != normalized_slice(TARGET, item["start"], item["end"])
        ):
            raise ValueError(f"Becker-03 surface binding differs: {record['id']}")
    for kind in SOURCE_ABSENT_SURFACES:
        record = by_id[f"{BASE}.source.{kind}.closure"]
        if record.get("surface_type") != kind or record.get("count") != 0 or record.get("target_presence") != (PRESENT_SURFACES.get(kind, 0) > 0):
            raise ValueError(f"Becker-03 donor absence record differs: {kind}")

    artifacts = [record for record in new if record["entity_type"] == "artifact"]
    if {record["id"]: record["path"] for record in artifacts} != {f"{BASE}.artifact.{suffix}": path for suffix, path in ARTIFACT_SUFFIX_PATHS.items()}:
        raise ValueError("Becker-03 artifact path map differs")
    for record in artifacts:
        if file_info(record["path"]) != (record["bytes"], record["sha256"]):
            raise ValueError(f"artifact binds stale bytes: {record['id']}")

    qa_records = [record for record in new if record["entity_type"] == "qa_event"]
    if {record["id"] for record in qa_records} != {f"{BASE}.qa.{suffix}" for suffix in QA_SUFFIXES} or any(record.get("result") != "pass" or record.get("status") != "passed" for record in qa_records):
        raise ValueError("Becker-03 QA-event closure differs")

    for relation_id, expected_triple in expected_relations.items():
        relation = by_id[relation_id]
        triple = (relation.get("relation_type"), relation.get("source_id"), relation.get("target_id"))
        if triple != expected_triple:
            raise ValueError(f"Becker-03 relation differs: {relation_id}")

    return {
        "records": records,
        "new": new,
        "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
        "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new).items())),
        "new_id_set_sha256": id_set(new),
        "new_id_order_sha256": id_order(sorted(new, key=lambda record: (rank[record["entity_type"]], record["id"]))),
        "new_record_set_sha256": record_set(new),
        "final_id_set_sha256": id_set(records),
        "final_id_order_sha256": id_order(records),
        "final_record_set_sha256": record_set(records),
        "final_line_sequence_sha256": line_sequence(jsonl_raw),
        "baseline_jsonl_recovered": {"bytes": len(baseline_jsonl), "sha256": digest(baseline_jsonl), "line_sequence_sha256": line_sequence(baseline_jsonl)},
        "baseline_csv_recovered": {"bytes": len(baseline_csv), "sha256": digest(baseline_csv)},
        "segments": segments,
        "present_surfaces": present_specs,
    }


def deterministic_regeneration(jsonl_path: Path, csv_path: Path) -> list[dict[str, Any]]:
    identities: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="becker-b03-backend-validation-") as temporary:
        root = Path(temporary)
        for run in (1, 2):
            output_dir = root / f"run-{run}"
            command = [sys.executable, str(GENERATOR), "--input-jsonl", str(jsonl_path), "--input-csv", str(csv_path), "--output-dir", str(output_dir)]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
            if completed.returncode != 0:
                raise ValueError(f"deterministic regeneration run {run} failed: {completed.stderr or completed.stdout}")
            jsonl_output = output_dir / "records.jsonl"
            csv_output = output_dir / "records.csv"
            identities.append(
                {
                    "run": run,
                    "jsonl": {"bytes": jsonl_output.stat().st_size, "sha256": digest(jsonl_output.read_bytes())},
                    "csv": {"bytes": csv_output.stat().st_size, "sha256": digest(csv_output.read_bytes())},
                }
            )
    if identities[0]["jsonl"] != identities[1]["jsonl"] or identities[0]["csv"] != identities[1]["csv"]:
        raise ValueError("two Becker-03 deterministic regeneration runs differ")
    if identities[0]["jsonl"] != {"bytes": jsonl_path.stat().st_size, "sha256": digest(jsonl_path.read_bytes())}:
        raise ValueError("regenerated Becker-03 JSONL differs from validated input")
    if identities[0]["csv"] != {"bytes": csv_path.stat().st_size, "sha256": digest(csv_path.read_bytes())}:
        raise ValueError("regenerated Becker-03 CSV differs from validated input")
    return identities


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}.", suffix=".stage", dir=path.parent, delete=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            staged = Path(handle.name)
        if staged.read_bytes() != payload:
            raise ValueError("validation receipt staged readback differs")
        os.replace(staged, path)
        staged = None
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, default=JSONL_PATH)
    parser.add_argument("--input-csv", type=Path, default=CSV_PATH)
    parser.add_argument("--receipt", type=Path, default=RECEIPT_PATH)
    parser.add_argument("--skip-regeneration", action="store_true", help="skip the two-run proof")
    args = parser.parse_args()
    canonical_flags = (args.input_jsonl.resolve() == JSONL_PATH.resolve(), args.input_csv.resolve() == CSV_PATH.resolve())
    if canonical_flags[0] != canonical_flags[1]:
        parser.error("--input-jsonl and --input-csv must both be canonical or both staged")
    canonical_backend_written = all(canonical_flags)

    validated = validate_dataset(args.input_jsonl, args.input_csv)
    regenerations = [] if args.skip_regeneration else deterministic_regeneration(args.input_jsonl, args.input_csv)
    segments = validated["segments"]
    surfaces = validated["present_surfaces"]
    receipt = {
        "schema": "o015-becker-03-backend-validation-v1",
        "validated_at": "2026-08-25T16:00:00Z",
        "result": "pass",
        "errors": [],
        "workflow": WORKFLOW,
        "commands": {
            "staging": "python qa/extend_backend_becker_03.py --output-dir <dir>",
            "validation_template": "python qa/validate_backend_becker_03.py --input-jsonl <jsonl> --input-csv <csv> --receipt <receipt>",
            "regeneration_template": "python qa/extend_backend_becker_03.py --input-jsonl <jsonl> --input-csv <csv> --output-dir <dir>",
        },
        "schema_constraint": {
            "schema_changed": False,
            "schema_bytes": SCHEMA_IDENTITY[0],
            "schema_sha256": SCHEMA_IDENTITY[1],
            "additive_records_only": True,
            "note": "Global sorting means the old file is not a literal prefix; exact workflow stripping proves every prior JSONL line and CSV row remains byte-identical and in the same relative order.",
        },
        "protected_baseline": {
            "records": BASELINE_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1], "line_sequence_sha256": BASELINE_LINE_SEQUENCE_SHA256},
            "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "id_order_sha256": BASELINE_ID_ORDER_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "recovered_jsonl": validated["baseline_jsonl_recovered"],
            "recovered_csv": validated["baseline_csv_recovered"],
            "record_bytes_and_relative_order_stable": True,
        },
        "admission": {
            "canonical_backend_written": canonical_backend_written,
            "disposition": "validated_canonical_backend" if canonical_backend_written else "validated_staged_projection",
            "namespace": f"{BASE}.*",
            "new_records": len(validated["new"]),
            "new_entity_counts": validated["new_entity_counts"],
            "new_id_set_sha256": validated["new_id_set_sha256"],
            "new_id_order_sha256": validated["new_id_order_sha256"],
            "new_record_set_sha256": validated["new_record_set_sha256"],
            "final_records": len(validated["records"]),
            "final_id_set_sha256": validated["final_id_set_sha256"],
            "final_id_order_sha256": validated["final_id_order_sha256"],
            "final_record_set_sha256": validated["final_record_set_sha256"],
            "final_line_sequence_sha256": validated["final_line_sequence_sha256"],
            "jsonl": validated["jsonl"],
            "csv": validated["csv"],
        },
        "topology": {
            "unit_id": UNIT_ID,
            "segments": len(segments),
            "topics": len(TOPIC_SLUGS),
            "present_surfaces": len(surfaces),
            "present_surface_counts": dict(sorted(Counter(item["surface_type"] for item in surfaces).items())),
            "source_absence_closures": len(SOURCE_ABSENT_SURFACES),
            "source_range": "2971-2988",
            "target_segment_ranges": [f"{item['target_start']}-{item['target_end']}" for item in segments],
            "predecessor_relation": f"{BASE}.relation.b02-precedes-b03",
        },
        "deterministic_regeneration": {
            "runs_required": 2,
            "runs_completed": len(regenerations),
            "input_dataset_match": not args.skip_regeneration,
            "identities": regenerations,
        },
        "upstream_contact": False,
    }
    write_receipt(args.receipt, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
