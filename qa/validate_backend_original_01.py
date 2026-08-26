#!/usr/bin/env python3
"""Independently validate the additive Original-01 backend closure.

This validator does not import the generator.  It independently freezes the
live Original-01 source and lab evidence, rediscovers all segment and semantic
surface ranges, recomputes the stable-ID and relation topology, proves exact
recovery of the protected 3,585-record backend, checks JSONL/CSV losslessness,
and performs two deterministic generator regenerations.
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
RECEIPT_PATH = ROOT / "qa" / "ORIGINAL_01_BACKEND_VALIDATION.json"
GENERATOR = ROOT / "qa" / "extend_backend_original_01.py"

WORKFLOW = "o015-original-01-backend-v1"
BASE = "d90.orig.v1.tr01"
RESOURCE_ID = f"{BASE}.resource"
EDITION_ID = f"{BASE}.edition.id-id"
UNIT_ID = f"{BASE}.unit"
CONTENT_RIGHTS_ID = f"{BASE}.rights.content.cc-by-sa-4-0"
SCAFFOLD_RIGHTS_ID = f"{BASE}.rights.wrapper-mixed"
TOOLING_RIGHTS_ID = f"{BASE}.rights.tooling"

SCHEMA_IDENTITY = (
    3_092,
    "1166cbffe6016044430fe003e4981b1a3a537be7c115f0b646168a1936ab5ad0",
)
BASELINE_COUNT = 3_585
BASELINE_JSONL = (
    2_724_813,
    "fd8e7f3a13cbc17784b7f9b6a39f83344124ec381b98a34bf8095935c5c054fb",
)
BASELINE_CSV = (
    3_267_489,
    "56004e9095adc61950b89c9e6f6959e6dc0f33d5211d4b67f4f1277216245c72",
)
BASELINE_ID_SET_SHA256 = "24a32c1bc5c62f22e0f8b7f5c596189b2dad1c0733a161970b7e158e7ab70923"
BASELINE_ID_ORDER_SHA256 = "718098412e56cb591595cc683ed9e6380f67bf441f367b8f6d257d1c2ea76945"
BASELINE_RECORD_SET_SHA256 = "c92934da552517c0780cdc48a66657f560ead0c38e74428db08a95a765cc72be"
BASELINE_LINE_SEQUENCE_SHA256 = "91953bdf4f3f2ec2ce8108cb9a0909fc5f493e664489e26f8c6871ede41113ad"

SOURCE = "source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
WRAPPER = "source/id-ID/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
LAB_CODE = "labs/original-01/stochastic-composite-lab.py"
LAB_JSON = "labs/original-01/results.json"
LAB_CSV = "labs/original-01/results.csv"
LAB_SVG = "labs/original-01/objective-gap.svg"
BACKEND_GENERATOR = "qa/extend_backend_original_01.py"
BACKEND_VALIDATOR = "qa/validate_backend_original_01.py"

FROZEN_IDENTITIES = {
    SOURCE: (27_431, "db677ca6bab274a5db3e356fc996cef3bb00fb67770a90984460aa265fabcf26"),
    WRAPPER: (5_311, "d632765baf270a7a7c1b39f051d83c1d76dd3ccc04457fb1b4b92088ffdd9322"),
    LAB_CODE: (13_655, "21a0df89524b34916d1f659636bf8f92a5730efb7e263e0fbd7393e6f2c936fd"),
    LAB_JSON: (2_432, "86ff701a51d091ee74c110917cb1888c6e7448489207e6ee1372753bd1e4c447"),
    LAB_CSV: (4_189, "61a6591ad7d1b41230a086482314448871f3697954d4c84133a7a5f4f775d37c"),
    LAB_SVG: (86_616, "87c772d901ee734356981ee35f19fc3c3ae47fea6f11528edbee6d015a3f2830"),
}

ARTIFACT_SUFFIX_PATHS = {
    "source-body": SOURCE,
    "source-wrapper": WRAPPER,
    "lab-code": LAB_CODE,
    "lab-results-json": LAB_JSON,
    "lab-results-csv": LAB_CSV,
    "lab-results-svg": LAB_SVG,
    "backend-generator": BACKEND_GENERATOR,
    "backend-validator": BACKEND_VALIDATOR,
}

SEGMENT_DEFS = (
    (1, "% OR01-S001 | lapisan asli: tujuan, batas, dan notasi", "stochastic-composite-model"),
    (2, "% OR01-S002 | lapisan asli: gradien proksimal stokastik", "stochastic-proximal-gradient"),
    (3, "% OR01-S003 | lapisan asli: minibatch", "minibatch-variance"),
    (4, "% OR01-S004 | lapisan asli: geometri cermin", "stochastic-mirror-descent"),
    (5, "% OR01-S005 | lapisan asli: penghubung reduksi varians", "proximal-saga-bridge"),
    (6, "% OR01-S006 | lapisan asli: laboratorium", "reproducible-stochastic-lab"),
    (7, "% OR01-S007 | lapisan asli: latihan, petunjuk, solusi", "worked-stochastic-composite-exercises"),
    (8, "% OR01-S008 | lapisan asli: peta asumsi dan rujukan", "assumption-and-provenance-map"),
)
TOPIC_DEFS = (
    ("stochastic-composite-model", (), 1),
    ("stochastic-proximal-gradient", ("stochastic-composite-model",), 2),
    ("minibatch-variance", ("stochastic-proximal-gradient",), 3),
    ("stochastic-mirror-descent", ("stochastic-composite-model",), 4),
    ("proximal-saga-bridge", ("stochastic-proximal-gradient", "minibatch-variance"), 5),
    ("reproducible-stochastic-lab", ("stochastic-proximal-gradient", "minibatch-variance", "proximal-saga-bridge"), 6),
    ("worked-stochastic-composite-exercises", ("stochastic-proximal-gradient", "stochastic-mirror-descent", "proximal-saga-bridge"), 7),
    ("assumption-and-provenance-map", (), 8),
)
PRESENT_SURFACES = {
    "chapter": 1,
    "section": 9,
    "subsection": 1,
    "definition": 3,
    "algorithm": 2,
    "lemma": 2,
    "theorem": 2,
    "proposition": 2,
    "corollary": 1,
    "proof": 7,
    "equation": 40,
    "exercise": 6,
    "hint": 6,
    "solution": 6,
    "lab": 1,
}
QA_SUFFIXES = {
    "source-freeze",
    "segment-binding",
    "semantic-surfaces",
    "lab-results",
    "rights-provenance",
    "backend-integration",
}
ENVIRONMENT_SURFACE = {
    "lemma": "lemma",
    "theorem": "theorem",
    "prop": "proposition",
    "proposition": "proposition",
    "cor": "corollary",
    "corollary": "corollary",
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
DEFINITION_RANGES = ((20, 24), (167, 173), (243, 247))

TOKEN = re.compile(r"\\(?P<kind>begin|end)\{(?P<env>[^}]+)\}")
HEADING = re.compile(r"^\\(?P<kind>chapter|section|subsection)\*?\{(?P<title>.+)\}$")
HINT_OR_SOLUTION = re.compile(r"^\\textbf\{(?P<label>Petunjuk bertahap|Solusi lengkap)\.\}")


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"required Original-01 artifact is missing: {relative}")
    raw = path.read_bytes()
    if not raw:
        raise ValueError(f"required Original-01 artifact is empty: {relative}")
    return len(raw), digest(raw)


def normalized_slice(relative: str, first: int, last: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if first < 1 or last < first or last > len(lines):
        raise ValueError(f"invalid normalized slice {relative}:{first}-{last}")
    raw = ("\n".join(lines[first - 1 : last]) + "\n").encode("utf-8")
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


def validate_evidence() -> dict[str, Any]:
    for path, identity in FROZEN_IDENTITIES.items():
        if file_info(path) != identity:
            raise ValueError(f"frozen Original-01 identity differs: {path}")
    for path in (BACKEND_GENERATOR, BACKEND_VALIDATOR):
        file_info(path)

    source_lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    if len(source_lines) != 700:
        raise ValueError("Original-01 source line count differs")
    source_text = "\n".join(source_lines)
    if not any(line.strip() == r"\item jalankan skrip tanpa mengubah benih acak dan verifikasikan konfigurasi" for line in source_lines):
        raise ValueError("configuration-verification wording differs")
    if "hash konfigurasi" in source_text:
        raise ValueError("superseded configuration-hash wording remains")
    if (
        source_text.count(r"Lema~\ref") != 2
        or source_text.count(r"Proposisi~\ref") != 1
        or r"Lemma~\ref" in source_text
        or r"Proposition~\ref" in source_text
    ):
        raise ValueError("final Indonesian manual cross-reference wording differs")

    wrapper = (ROOT / WRAPPER).read_text(encoding="utf-8")
    identity_wrapper_markers = (
        f"% unit-id: {UNIT_ID}",
        "% target-edition-id: d90.orig.v1.tr01.edition.id-ID",
        "% authorship: independent coursebook completion layer",
        r"\input{original-01-metode-stokastik-komposit-cermin-minibatch-id}",
    )
    evidence_wrapper_markers = (
        "Creative Commons Attribution-ShareAlike 4.0 International",
        "Creative Commons Attribution 4.0 International",
        r"\texttt{shinybook.cls}",
        r"\texttt{macros-id.tex}",
        "Christian Clason",
        "OpenAI Codex gpt-5.6-sol, Ultra",
    )
    if any(wrapper.count(marker) != 1 for marker in identity_wrapper_markers) or any(marker not in wrapper for marker in evidence_wrapper_markers):
        raise ValueError("wrapper identity, rights, or provenance marker differs")

    lab = json.loads((ROOT / LAB_JSON).read_text(encoding="utf-8"))
    if (
        lab.get("schema") != "o015-original-01-stochastic-composite-lab-v1"
        or lab.get("result") != "pass"
        or lab.get("row_count") != 38
        or lab.get("configuration", {}).get("seed") != 20260825
        or lab.get("configuration", {}).get("component_gradient_budget") != 3840
        or lab.get("configuration", {}).get("minibatch_size") != 16
        or lab.get("network_access") is not False
        or lab.get("upstream_contact") is not False
    ):
        raise ValueError("lab JSON closure differs")
    if (lab.get("csv", {}).get("bytes"), lab.get("csv", {}).get("sha256")) != file_info(LAB_CSV):
        raise ValueError("lab JSON does not bind current CSV")
    if (lab.get("svg", {}).get("bytes"), lab.get("svg", {}).get("sha256")) != file_info(LAB_SVG):
        raise ValueError("lab JSON does not bind current SVG")
    if lab.get("svg", {}).get("redundant_with_accessible_tables") is not True:
        raise ValueError("lab SVG accessibility redundancy marker differs")

    reader = csv.DictReader(io.StringIO((ROOT / LAB_CSV).read_text(encoding="utf-8")))
    expected_columns = [
        "method",
        "component_gradient_evaluations",
        "epochs",
        "objective",
        "objective_gap",
        "prox_gradient_mapping_norm",
        "nonzero_coordinates",
        "direction_variance_trace",
    ]
    if reader.fieldnames != expected_columns:
        raise ValueError("lab CSV columns differ")
    rows = list(reader)
    if len(rows) != 38 or Counter(row["method"] for row in rows) != Counter({"prox_sgd_b1": 13, "prox_minibatch_b16": 13, "prox_saga": 12}):
        raise ValueError("lab CSV row/method census differs")
    for method, final in lab.get("final_rows", {}).items():
        terminal = max((row for row in rows if row["method"] == method), key=lambda row: int(row["component_gradient_evaluations"]))
        if int(terminal["component_gradient_evaluations"]) != 3840:
            raise ValueError(f"lab budget differs for {method}")
        if float(terminal["objective_gap"]) != final["objective_gap"] or int(terminal["nonzero_coordinates"]) != final["nonzero_coordinates"]:
            raise ValueError(f"lab terminal result differs for {method}")
    return {"lab": lab, "rows": rows}


def discover_segments() -> list[dict[str, Any]]:
    lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    marker_map = {marker: (number, topic) for number, marker, topic in SEGMENT_DEFS}
    found: list[tuple[int, int, str, str]] = []
    for line_number, line in enumerate(lines, 1):
        if line in marker_map:
            number, topic = marker_map[line]
            found.append((line_number, number, topic, line))
    if [number for _, number, _, _ in found] != list(range(1, 9)):
        raise ValueError("Original-01 eight-marker closure differs")
    segments: list[dict[str, Any]] = []
    for index, (start, number, topic, marker) in enumerate(found):
        segment_id = f"{BASE}.seg{number:04d}"
        if start >= len(lines) or lines[start] != f"% segment-id: {segment_id}":
            raise ValueError(f"stable segment marker differs: {segment_id}")
        end = found[index + 1][0] - 1 if index + 1 < len(found) else len(lines)
        segments.append({"id": segment_id, "number": number, "topic_id": f"{BASE}.topic.{topic}", "start": start, "end": end, "marker": marker})
    return segments


def segment_for_line(segments: list[dict[str, Any]], line_number: int) -> dict[str, Any]:
    matches = [segment for segment in segments if segment["start"] <= line_number <= segment["end"]]
    if len(matches) != 1:
        raise ValueError(f"source line {line_number} belongs to {len(matches)} segments")
    return matches[0]


def discover_surfaces(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    candidates: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    exercises: list[tuple[int, int]] = []
    for number, raw in enumerate(lines, 1):
        line = re.sub(r"(?<!\\)%.*", "", raw).strip()
        heading = HEADING.fullmatch(line)
        if heading:
            candidates.append({"surface_type": heading.group("kind"), "environment": "latex-heading", "start": number, "end": number})
        for token in TOKEN.finditer(line):
            environment = token.group("env")
            if token.group("kind") == "begin":
                stack.append((environment, number))
                continue
            if not stack or stack[-1][0] != environment:
                raise ValueError(f"unbalanced {environment} at {SOURCE}:{number}")
            opened, start = stack.pop()
            if opened in ENVIRONMENT_SURFACE:
                candidates.append({"surface_type": ENVIRONMENT_SURFACE[opened], "environment": opened, "start": start, "end": number})
                if opened == "exercise":
                    exercises.append((start, number))
            elif opened == "quote" and re.search(r"\\textbf\{Algoritma [12]:", "\n".join(lines[start - 1 : number])):
                candidates.append({"surface_type": "algorithm", "environment": "quote-algorithm", "start": start, "end": number})
    if stack:
        raise ValueError("unclosed TeX environment")

    for start, end in DEFINITION_RANGES:
        candidates.append({"surface_type": "definition", "environment": "prose-definition", "start": start, "end": end})

    for start, end in sorted(exercises):
        markers: list[tuple[int, str]] = []
        for number in range(start, end + 1):
            match = HINT_OR_SOLUTION.match(re.sub(r"(?<!\\)%.*", "", lines[number - 1]).strip())
            if match:
                markers.append((number, "hint" if match.group("label") == "Petunjuk bertahap" else "solution"))
        if [kind for _, kind in markers] != ["hint", "solution"]:
            raise ValueError(f"exercise at line {start} lacks its pair")
        hint_start = markers[0][0]
        solution_start = markers[1][0]
        hint_end = solution_start - 1
        while hint_end > hint_start and not lines[hint_end - 1].strip():
            hint_end -= 1
        candidates.append({"surface_type": "hint", "environment": "latex-bold-heading", "start": hint_start, "end": hint_end})
        candidates.append({"surface_type": "solution", "environment": "latex-bold-heading", "start": solution_start, "end": end})

    lab_start = segments[5]["start"] + 2
    lab_end = segments[5]["end"]
    while lab_end > lab_start and not lines[lab_end - 1].strip():
        lab_end -= 1
    candidates.append({"surface_type": "lab", "environment": "coursebook-lab", "start": lab_start, "end": lab_end})

    counts = Counter(item["surface_type"] for item in candidates)
    if counts != Counter(PRESENT_SURFACES):
        raise ValueError(f"present-surface census differs: {dict(counts)}")
    counters: Counter[str] = Counter()
    result: list[dict[str, Any]] = []
    for item in sorted(candidates, key=lambda value: (value["start"], value["end"], value["surface_type"], value["environment"])):
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


def expected_relation_map(segments: list[dict[str, Any]], surfaces: list[dict[str, Any]]) -> dict[str, tuple[str, str, str]]:
    relations: dict[str, tuple[str, str, str]] = {
        f"{BASE}.relation.course-contains-unit": ("contains", "course.d90.advanced-optimization-convex-analysis", UNIT_ID),
        f"{BASE}.relation.becker-b03-precedes-original-01": ("precedes", "d90.becker.98ed693.b03.unit", UNIT_ID),
        f"{BASE}.relation.resource-contains-edition": ("contains", RESOURCE_ID, EDITION_ID),
        f"{BASE}.relation.edition-contains-unit": ("contains", EDITION_ID, UNIT_ID),
        f"{BASE}.relation.source-wrapper-adapts-source-body": ("adapts", f"{BASE}.artifact.source-wrapper", f"{BASE}.artifact.source-body"),
        f"{BASE}.relation.lab-code-illustrates-lab": ("illustrates", f"{BASE}.artifact.lab-code", f"{BASE}.lab.0001"),
        f"{BASE}.relation.lab-results-json-illustrates-lab": ("illustrates", f"{BASE}.artifact.lab-results-json", f"{BASE}.lab.0001"),
        f"{BASE}.relation.lab-results-csv-illustrates-lab": ("illustrates", f"{BASE}.artifact.lab-results-csv", f"{BASE}.lab.0001"),
        f"{BASE}.relation.lab-results-svg-illustrates-lab": ("illustrates", f"{BASE}.artifact.lab-results-svg", f"{BASE}.lab.0001"),
    }
    for segment in segments:
        relations[f"{BASE}.relation.unit-contains-seg{segment['number']:04d}"] = ("contains", UNIT_ID, segment["id"])
    for slug, prerequisites, _ in TOPIC_DEFS:
        topic_id = f"{BASE}.topic.{slug}"
        relations[f"{BASE}.relation.unit-contains-topic-{slug}"] = ("contains", UNIT_ID, topic_id)
        for prerequisite in prerequisites:
            relations[f"{BASE}.relation.topic-{slug}-prerequisite-{prerequisite}"] = ("prerequisite", topic_id, f"{BASE}.topic.{prerequisite}")
    for surface in surfaces:
        suffix = surface["id"].removeprefix(f"{BASE}.").replace(".", "-")
        relations[f"{BASE}.relation.unit-contains-{suffix}"] = ("contains", UNIT_ID, surface["id"])
        relation_type = "defines" if surface["surface_type"] == "definition" else "exercises" if surface["surface_type"] in {"exercise", "hint", "solution"} else "illustrates"
        relations[f"{BASE}.relation.{suffix}-to-topic"] = (relation_type, surface["id"], surface["topic_id"])
    for number in range(1, 7):
        relations[f"{BASE}.relation.hint-{number:04d}-depends-on-exercise-{number:04d}"] = ("depends-on", f"{BASE}.hint.{number:04d}", f"{BASE}.exercise.{number:04d}")
        relations[f"{BASE}.relation.solution-{number:04d}-depends-on-exercise-{number:04d}"] = ("depends-on", f"{BASE}.solution.{number:04d}", f"{BASE}.exercise.{number:04d}")
    proof_targets = (
        f"{BASE}.lemma.0001",
        f"{BASE}.theorem.0001",
        f"{BASE}.proposition.0001",
        f"{BASE}.proposition.0002",
        f"{BASE}.lemma.0002",
        f"{BASE}.theorem.0002",
        f"{BASE}.corollary.0001",
    )
    for number, target in enumerate(proof_targets, 1):
        suffix = f"proof-{number:04d}-proves-{target.rsplit('.', 2)[-2]}-{target.rsplit('.', 1)[-1]}"
        relations[f"{BASE}.relation.{suffix}"] = ("proves", f"{BASE}.proof.{number:04d}", target)
    return relations


def expected_ids(segments: list[dict[str, Any]], surfaces: list[dict[str, Any]]) -> set[str]:
    result = {RESOURCE_ID, EDITION_ID, UNIT_ID, CONTENT_RIGHTS_ID, SCAFFOLD_RIGHTS_ID, TOOLING_RIGHTS_ID}
    result.update(f"{BASE}.topic.{slug}" for slug, _, _ in TOPIC_DEFS)
    result.update(segment["id"] for segment in segments)
    result.update(surface["id"] for surface in surfaces)
    result.update(f"{BASE}.artifact.{suffix}" for suffix in ARTIFACT_SUFFIX_PATHS)
    result.update(f"{BASE}.qa.{suffix}" for suffix in QA_SUFFIXES)
    result.update(expected_relation_map(segments, surfaces))
    return result


def validate_dataset(jsonl_path: Path, csv_path: Path) -> dict[str, Any]:
    schema = assert_schema_identity()
    evidence = validate_evidence()
    segments = discover_segments()
    surface_specs = discover_surfaces(segments)

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
    if (len(baseline_jsonl), digest(baseline_jsonl)) != BASELINE_JSONL:
        raise ValueError("workflow stripping does not recover exact protected JSONL")
    if (len(baseline_csv), digest(baseline_csv)) != BASELINE_CSV:
        raise ValueError("workflow stripping does not recover exact protected CSV")
    if line_sequence(baseline_jsonl) != BASELINE_LINE_SEQUENCE_SHA256:
        raise ValueError("protected JSONL line sequence differs")
    baseline = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    new = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    if (
        len(baseline) != BASELINE_COUNT
        or id_set(baseline) != BASELINE_ID_SET_SHA256
        or id_order(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("protected baseline set/order differs")

    expected = expected_ids(segments, surface_specs)
    new_ids = {record["id"] for record in new}
    if new_ids != expected:
        raise ValueError(f"Original-01 stable-ID set differs; missing={sorted(expected-new_ids)}, extra={sorted(new_ids-expected)}")
    relation_map = expected_relation_map(segments, surface_specs)
    expected_counts = Counter(
        {
            "resource": 1,
            "edition": 1,
            "unit": 1,
            "concept": 8,
            "segment": 8,
            "learning_surface": sum(PRESENT_SURFACES.values()),
            "rights": 3,
            "artifact": len(ARTIFACT_SUFFIX_PATHS),
            "qa_event": len(QA_SUFFIXES),
            "relation": len(relation_map),
        }
    )
    if Counter(record["entity_type"] for record in new) != expected_counts:
        raise ValueError("Original-01 entity topology differs")

    by_id = {record["id"]: record for record in records}
    resource = by_id[RESOURCE_ID]
    edition = by_id[EDITION_ID]
    unit = by_id[UNIT_ID]
    if resource.get("rights_id") != CONTENT_RIGHTS_ID or resource.get("content_origin") != "independently authored original coursebook completion layer":
        raise ValueError("Original-01 resource provenance differs")
    if edition.get("resource_id") != RESOURCE_ID or edition.get("declared_wrapper_edition_id") != "d90.orig.v1.tr01.edition.id-ID":
        raise ValueError("Original-01 edition normalization differs")
    if unit.get("edition_id") != EDITION_ID or unit.get("order") != 4 or unit.get("source_locator") != f"{SOURCE}:1-700":
        raise ValueError("Original-01 unit topology differs")

    source_lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    for segment in segments:
        record = by_id[segment["id"]]
        expected_identity = normalized_slice(SOURCE, segment["start"], segment["end"])
        if (
            record.get("order") != segment["number"]
            or record.get("source_path") != SOURCE
            or record.get("target_path") != SOURCE
            or record.get("source_line_start") != segment["start"]
            or record.get("source_line_end") != segment["end"]
            or record.get("target_line_start") != segment["start"]
            or record.get("target_line_end") != segment["end"]
            or (record.get("source_content_bytes"), record.get("source_content_sha256")) != expected_identity
            or (record.get("target_content_bytes"), record.get("target_content_sha256")) != expected_identity
            or record.get("concept_ids") != [segment["topic_id"]]
        ):
            raise ValueError(f"segment binding differs: {segment['id']}")
        if source_lines[segment["start"] - 1] != segment["marker"] or source_lines[segment["start"]] != f"% segment-id: {segment['id']}":
            raise ValueError(f"segment marker differs: {segment['id']}")

    for slug, prerequisites, number in TOPIC_DEFS:
        topic = by_id[f"{BASE}.topic.{slug}"]
        if topic.get("prerequisite_ids") != [f"{BASE}.topic.{item}" for item in prerequisites] or topic.get("related_segment_ids") != [f"{BASE}.seg{number:04d}"]:
            raise ValueError(f"topic topology differs: {slug}")

    discovered = {surface["id"]: surface for surface in surface_specs}
    surface_records = [record for record in new if record["entity_type"] == "learning_surface"]
    if Counter(record["surface_type"] for record in surface_records) != Counter(PRESENT_SURFACES):
        raise ValueError("stored semantic-surface census differs")
    for record in surface_records:
        item = discovered[record["id"]]
        if (
            record.get("presence") != "present"
            or record.get("target_line_start") != item["start"]
            or record.get("target_line_end") != item["end"]
            or record.get("latex_environment") != item["environment"]
            or record.get("related_segment_ids") != [item["segment_id"]]
            or record.get("concept_ids") != [item["topic_id"]]
            or (record.get("target_content_bytes"), record.get("target_content_sha256")) != normalized_slice(SOURCE, item["start"], item["end"])
        ):
            raise ValueError(f"surface binding differs: {record['id']}")
    lab_surface = by_id[f"{BASE}.lab.0001"]
    if lab_surface.get("input_artifact_ids") != [f"{BASE}.artifact.lab-code"] or lab_surface.get("evidence_artifact_id") != f"{BASE}.artifact.lab-results-json":
        raise ValueError("lab surface artifact binding differs")

    artifacts = [record for record in new if record["entity_type"] == "artifact"]
    expected_artifact_map = {f"{BASE}.artifact.{suffix}": path for suffix, path in ARTIFACT_SUFFIX_PATHS.items()}
    if {record["id"]: record["path"] for record in artifacts} != expected_artifact_map:
        raise ValueError("artifact path map differs")
    for artifact in artifacts:
        if file_info(artifact["path"]) != (artifact["bytes"], artifact["sha256"]):
            raise ValueError(f"artifact binds stale bytes: {artifact['id']}")

    rights = {record["id"]: record for record in new if record["entity_type"] == "rights"}
    if set(rights) != {CONTENT_RIGHTS_ID, SCAFFOLD_RIGHTS_ID, TOOLING_RIGHTS_ID} or "CC BY-SA 4.0" not in rights[CONTENT_RIGHTS_ID].get("rights_expression", ""):
        raise ValueError("rights closure differs")
    if rights[CONTENT_RIGHTS_ID].get("content_origin") != "independent original writing and code; cited works are mathematical witnesses only":
        raise ValueError("rights provenance differs")
    scaffold = rights[SCAFFOLD_RIGHTS_ID]
    handling = set(scaffold.get("required_handling", []))
    if (
        "Habring-bundled shinybook.cls" not in scaffold.get("rights_expression", "")
        or "preserve Habring attribution and CC BY 4.0" not in handling
        or "preserve Christian Clason template credit" not in handling
    ):
        raise ValueError("mixed wrapper/scaffold rights closure differs")
    if by_id[f"{BASE}.artifact.source-wrapper"].get("rights_id") != SCAFFOLD_RIGHTS_ID:
        raise ValueError("wrapper artifact does not point to mixed scaffold rights")

    qa = [record for record in new if record["entity_type"] == "qa_event"]
    if {record["id"] for record in qa} != {f"{BASE}.qa.{suffix}" for suffix in QA_SUFFIXES} or any(record.get("status") != "passed" or record.get("result") != "pass" for record in qa):
        raise ValueError("QA-event closure differs")

    for relation_id, expected_triple in relation_map.items():
        relation = by_id[relation_id]
        triple = (relation.get("relation_type"), relation.get("source_id"), relation.get("target_id"))
        if triple != expected_triple:
            raise ValueError(f"relation differs: {relation_id}")

    ordered_new = sorted(new, key=lambda record: (rank[record["entity_type"]], record["id"]))
    return {
        "records": records,
        "new": new,
        "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
        "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new).items())),
        "new_id_set_sha256": id_set(new),
        "new_id_order_sha256": id_order(ordered_new),
        "new_record_set_sha256": record_set(new),
        "final_id_set_sha256": id_set(records),
        "final_id_order_sha256": id_order(records),
        "final_record_set_sha256": record_set(records),
        "final_line_sequence_sha256": line_sequence(jsonl_raw),
        "baseline_jsonl_recovered": {"bytes": len(baseline_jsonl), "sha256": digest(baseline_jsonl), "line_sequence_sha256": line_sequence(baseline_jsonl)},
        "baseline_csv_recovered": {"bytes": len(baseline_csv), "sha256": digest(baseline_csv)},
        "segments": segments,
        "surfaces": surface_specs,
        "relation_count": len(relation_map),
        "lab": evidence["lab"],
    }


def validation_identity(validated: dict[str, Any]) -> dict[str, Any]:
    return {
        "records": len(validated["records"]),
        "new_records": len(validated["new"]),
        "jsonl": validated["jsonl"],
        "csv": validated["csv"],
        "new_id_set_sha256": validated["new_id_set_sha256"],
        "new_record_set_sha256": validated["new_record_set_sha256"],
        "final_id_set_sha256": validated["final_id_set_sha256"],
        "final_record_set_sha256": validated["final_record_set_sha256"],
    }


def deterministic_regeneration(jsonl_path: Path, csv_path: Path) -> list[dict[str, Any]]:
    identities: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="original-01-backend-validation-") as temporary:
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
        raise ValueError("two Original-01 deterministic regeneration runs differ")
    if identities[0]["jsonl"] != {"bytes": jsonl_path.stat().st_size, "sha256": digest(jsonl_path.read_bytes())}:
        raise ValueError("regenerated Original-01 JSONL differs from validated input")
    if identities[0]["csv"] != {"bytes": csv_path.stat().st_size, "sha256": digest(csv_path.read_bytes())}:
        raise ValueError("regenerated Original-01 CSV differs from validated input")
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
    parser.add_argument("--skip-regeneration", action="store_true", help="skip the two-run generator proof")
    args = parser.parse_args()
    canonical_flags = (args.input_jsonl.resolve() == JSONL_PATH.resolve(), args.input_csv.resolve() == CSV_PATH.resolve())
    if canonical_flags[0] != canonical_flags[1]:
        parser.error("--input-jsonl and --input-csv must both be canonical or both staged")

    first = validate_dataset(args.input_jsonl, args.input_csv)
    second = validate_dataset(args.input_jsonl, args.input_csv)
    first_identity = validation_identity(first)
    second_identity = validation_identity(second)
    if first_identity != second_identity:
        raise ValueError("two independent validator passes differ")
    regenerations = [] if args.skip_regeneration else deterministic_regeneration(args.input_jsonl, args.input_csv)
    canonical_backend = all(canonical_flags)
    surface_counts = Counter(item["surface_type"] for item in first["surfaces"])
    receipt = {
        "schema": "o015-original-01-backend-validation-v1",
        "validated_at": "2026-08-25T23:55:00Z",
        "result": "pass",
        "errors": [],
        "workflow": WORKFLOW,
        "commands": {
            "canonical_generation": "python qa/extend_backend_original_01.py --write-canonical",
            "staging": "python qa/extend_backend_original_01.py --output-dir <dir>",
            "validation": "python qa/validate_backend_original_01.py",
        },
        "schema_constraint": {
            "schema_changed": False,
            "schema_bytes": SCHEMA_IDENTITY[0],
            "schema_sha256": SCHEMA_IDENTITY[1],
            "additive_records_only": True,
            "note": "Global sorting means the old file is not a literal prefix; workflow stripping proves every protected JSONL line and CSV row remains byte-identical and in the same relative order.",
        },
        "protected_baseline": {
            "records": BASELINE_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1], "line_sequence_sha256": BASELINE_LINE_SEQUENCE_SHA256},
            "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "id_order_sha256": BASELINE_ID_ORDER_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "recovered_jsonl": first["baseline_jsonl_recovered"],
            "recovered_csv": first["baseline_csv_recovered"],
            "record_bytes_and_relative_order_stable": True,
        },
        "admission": {
            "canonical_backend_written": canonical_backend,
            "disposition": "validated_canonical_backend" if canonical_backend else "validated_staged_projection",
            "namespace": f"{BASE}.*",
            "new_records": len(first["new"]),
            "new_entity_counts": first["new_entity_counts"],
            "new_id_set_sha256": first["new_id_set_sha256"],
            "new_id_order_sha256": first["new_id_order_sha256"],
            "new_record_set_sha256": first["new_record_set_sha256"],
            "final_records": len(first["records"]),
            "final_id_set_sha256": first["final_id_set_sha256"],
            "final_id_order_sha256": first["final_id_order_sha256"],
            "final_record_set_sha256": first["final_record_set_sha256"],
            "final_line_sequence_sha256": first["final_line_sequence_sha256"],
            "jsonl": first["jsonl"],
            "csv": first["csv"],
        },
        "source_and_topology": {
            "source": {"path": SOURCE, "bytes": FROZEN_IDENTITIES[SOURCE][0], "sha256": FROZEN_IDENTITIES[SOURCE][1], "physical_lines": 700},
            "unit_id": UNIT_ID,
            "segments": len(first["segments"]),
            "segment_ranges": [f"{item['start']}-{item['end']}" for item in first["segments"]],
            "topics": len(TOPIC_DEFS),
            "present_surfaces": len(first["surfaces"]),
            "present_surface_counts": dict(sorted(surface_counts.items())),
            "exercise_hint_solution_sets": 6,
            "relation_count": first["relation_count"],
            "live_wording_repairs_bound": ["configuration verification", "Lema", "Proposisi"],
        },
        "lab": {
            "schema": first["lab"]["schema"],
            "result": first["lab"]["result"],
            "row_count": first["lab"]["row_count"],
            "component_gradient_budget": first["lab"]["configuration"]["component_gradient_budget"],
            "methods": sorted(first["lab"]["final_rows"]),
            "artifacts": {path: {"bytes": identity[0], "sha256": identity[1]} for path, identity in FROZEN_IDENTITIES.items() if path.startswith("labs/")},
            "network_access": False,
            "upstream_contact": False,
        },
        "independent_validation": {
            "passes_required": 2,
            "passes_completed": 2,
            "identities": [{"run": 1, **first_identity}, {"run": 2, **second_identity}],
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
