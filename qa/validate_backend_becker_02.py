#!/usr/bin/env python3
"""Independently validate the additive Becker-02 backend admission."""

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
RECEIPT_PATH = ROOT / "qa" / "BECKER_02_BACKEND_VALIDATION.json"
GENERATOR = ROOT / "qa" / "extend_backend_becker_02.py"

WORKFLOW = "o015-becker-02-backend-v1"
BASE = "d90.becker.98ed693.b02"
UNIT_ID = f"{BASE}.unit"
BASELINE_COUNT = 3_320
BASELINE_JSONL = (
    2_552_754,
    "48292d9ab6f8917e914f8ad9d07e0be99b8c1eeb1f3a3f38be36600728ab6f67",
)
BASELINE_CSV = (
    3_054_550,
    "baf7e3c11cd10e636cdf61f3f469954f6f0e072a49f2e6528186e3ba4231810f",
)
BASELINE_ID_SET_SHA256 = "037a51692fa7c7e07bd46d2b17d2504bd8d59c674b32baffdb88dd097065fa5e"
BASELINE_ID_ORDER_SHA256 = "7a9f4695de16c1308e38bf4679215f69729ca3bc4a9c972071fbbdfc45e017bb"
BASELINE_RECORD_SET_SHA256 = "d1e4814426ca899ce40a9158441345893ba857cb73e5bff2af47f77ab528e454"
BASELINE_LINE_SEQUENCE_SHA256 = "870d9e772c561784c1ea428b410d8c7bbc1a2ed3a6e60af13a3cac4fb5d076f5"

COMMIT = "98ed6930084c435ba0f675f7646ced1f2fd8729e"
AUTHORITY = (
    "authority/becker/extract/"
    f"convex-optimization-class-{COMMIT}/TypedNotes/APPM5720Notes.tex"
)
WITNESS = "source/en/becker-02-douglas-rachford-source.tex"
TARGET = "source/id-ID/becker-02-pemisahan-douglas-rachford-id.tex"
WRAPPER = "source/id-ID/D90-BECKER-02-pemisahan-douglas-rachford-id.tex"
BOUNDARY = "qa/BECKER_02_SOURCE_BOUNDARY.json"
EXTRACTOR = "qa/extract_becker_douglas_rachford_source.py"
PDF_BUILDER = "qa/build_becker_douglas_rachford_pdf.py"
PDF_REPORT = "qa/BECKER_02_PDF_BUILD.json"
PDF = "output/pdf/D90-BECKER-02-pemisahan-douglas-rachford-id.pdf"
HTML_BUILDER = "qa/build_becker_douglas_rachford_html.py"
HTML_REPORT = "qa/BECKER_02_HTML_BUILD.json"
HTML = "output/html/D90-BECKER-02-pemisahan-douglas-rachford-id.html"
MATH_VALIDATOR = "qa/validate_becker_douglas_rachford_math.py"
MATH_REPORT = "qa/BECKER_02_MATH_VALIDATION.json"
BACKEND_GENERATOR = "qa/extend_backend_becker_02.py"
BACKEND_VALIDATOR = "qa/validate_backend_becker_02.py"

FROZEN_IDENTITIES: dict[str, tuple[int, str]] = {
    AUTHORITY: (
        130_911,
        "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8",
    ),
    WITNESS: (
        1_358,
        "fdc368741a0a88eb9d21c69d655ac6ce1b44571c2d49c6a3302e3efc4673594b",
    ),
    TARGET: (
        4_915,
        "2d0e7d64d8226954640013caecd1cacfb3c60d2ae75a27f130f97e900a20464a",
    ),
    WRAPPER: (
        7_134,
        "23fd130a5e644801ccb2374450ec07744c9e68dff003c295f3b127d9a9b90955",
    ),
    BOUNDARY: (
        1_773,
        "06cd220dee304ad6e33ec66109d4e7e1a8c0d41e221770634b280850000ca10f",
    ),
    EXTRACTOR: (
        5_843,
        "d1e509892b4392275c06b8e9ca9e5d1a466ca01afb902e57799631a2d12467ef",
    ),
    PDF_BUILDER: (
        8_561,
        "b645f6e663ae9d088f4ad367033c6d2f15aac884e217a7f7f594ee4782f0e75b",
    ),
    PDF_REPORT: (
        4_942,
        "a6d8ee690768e343dc0157d7528478ee8dcdadb56af0ce9fab713fccae9b697e",
    ),
    PDF: (
        458_915,
        "32e26d96a0878ad2a5e798a099759eb4351cbe728a2d2b912757ebc402e49794",
    ),
    HTML_BUILDER: (
        15_206,
        "2e1876653476da791768bdaf0d46c2b7dd9f6e5291e57e9e7835ebe9d00c3e3b",
    ),
    HTML_REPORT: (
        4_575,
        "db3f89b93196197840b7c8ce710a3a9ebe6b354c35092c19ed9167e296f7d380",
    ),
    HTML: (
        18_370,
        "ff42d60d3bdce967341f69932a07cb85af868b3f4bb02a10f8beb627198719fe",
    ),
    MATH_VALIDATOR: (
        16_128,
        "ae98a652bbe25a35ead53ca724fc9b1029c9258fcf4961f9dc24d6e0b9bb6bbd",
    ),
    MATH_REPORT: (
        9_486,
        "bbfc499b2f6046c4db3c1a3327aac5fe6432030077f4de27915cd2c2fdb836ad",
    ),
}

TOPIC_SLUGS = (
    "composite-primal-dual",
    "proximal-resolvent",
    "douglas-rachford-iteration",
    "shadow-limit-optimality",
    "fixed-point-optimality",
    "admm-dual-link",
)
SEGMENT_RANGES = (
    (1, 2750, 2769, 1, 62),
    (2, 2771, 2790, 63, 120),
    (3, 2792, 2797, 121, 130),
)
PRESENT_SURFACES = {
    "chapter": 1,
    "section": 2,
    "theorem": 1,
    "proof": 1,
    "equation": 10,
}
ABSENT_SURFACES = ("exercise", "hint", "answer", "solution")
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
EXPECTED_ENTITY_COUNTS = Counter(
    {
        "resource": 1,
        "edition": 2,
        "unit": 1,
        "concept": 6,
        "segment": 3,
        "learning_surface": 19,
        "rights": 3,
        "artifact": 16,
        "qa_event": 8,
        "relation": 51,
    }
)
EXPECTED_NEW_COUNT = sum(EXPECTED_ENTITY_COUNTS.values())


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    raw = path.read_bytes()
    return len(raw), digest(raw)


def id_set(records: list[dict[str, Any]]) -> str:
    return digest(
        ("\n".join(sorted(record["id"] for record in records)) + "\n").encode(
            "utf-8"
        )
    )


def id_order(records: list[dict[str, Any]]) -> str:
    return digest(
        ("\n".join(record["id"] for record in records) + "\n").encode("utf-8")
    )


def record_set(records: list[dict[str, Any]]) -> str:
    payload = "".join(
        canonical(record) + "\n"
        for record in sorted(records, key=lambda item: item["id"])
    )
    return digest(payload.encode("utf-8"))


def line_sequence(raw: bytes) -> str:
    hashes = [digest(line) for line in raw.splitlines(keepends=True)]
    return digest(("\n".join(hashes) + "\n").encode("utf-8"))


def normalized_slice(relative: str, start: int, end: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid slice {relative}:{start}-{end}")
    raw = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
    return len(raw), digest(raw)


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


def topic_for_line(line_number: int) -> str:
    if line_number >= 123:
        slug = "admm-dual-link"
    elif line_number >= 98:
        slug = "fixed-point-optimality"
    elif line_number >= 65:
        slug = "shadow-limit-optimality"
    elif line_number >= 51:
        slug = "douglas-rachford-iteration"
    elif line_number >= 42:
        slug = "proximal-resolvent"
    else:
        slug = "composite-primal-dual"
    return f"{BASE}.topic.{slug}"


def segment_for_line(line_number: int) -> str:
    for number, _, _, start, end in SEGMENT_RANGES:
        if start <= line_number <= end:
            return f"{BASE}.seg{number:04d}"
    raise ValueError(f"target line {line_number} is outside Becker-02 segments")


TOKEN = re.compile(r"\\(?P<kind>begin|end)\{(?P<env>[^}]+)\}")
HEADING = re.compile(r"^\\(?P<kind>chapter|section|subsection)\{(?P<title>.+)\}$")
ENVIRONMENT_SURFACE = {
    "theorem": "theorem",
    "proof": "proof",
    "equation": "equation",
    "multline": "equation",
    "align": "equation",
    "gather": "equation",
}


def discover_present_surfaces() -> list[dict[str, Any]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    if len(lines) != 130:
        raise ValueError(f"target physical line count differs: {len(lines)}")
    found: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    for line_number, raw in enumerate(lines, start=1):
        line = re.sub(r"(?<!\\)%.*", "", raw).strip()
        heading = HEADING.fullmatch(line)
        if heading:
            found.append(
                {
                    "surface_type": heading.group("kind"),
                    "environment": "latex-heading",
                    "start": line_number,
                    "end": line_number,
                }
            )
        for match in TOKEN.finditer(line):
            environment = match.group("env")
            if match.group("kind") == "begin":
                stack.append((environment, line_number))
                continue
            if not stack or stack[-1][0] != environment:
                raise ValueError(f"unbalanced {environment} at {TARGET}:{line_number}")
            opened, start = stack.pop()
            if opened in ENVIRONMENT_SURFACE:
                found.append(
                    {
                        "surface_type": ENVIRONMENT_SURFACE[opened],
                        "environment": opened,
                        "start": start,
                        "end": line_number,
                    }
                )
    if stack:
        raise ValueError(f"unclosed TeX environment in {TARGET}")
    if Counter(item["surface_type"] for item in found) != Counter(PRESENT_SURFACES):
        raise ValueError("Becker-02 present-surface census differs")
    counters: Counter[str] = Counter()
    result: list[dict[str, Any]] = []
    for item in sorted(
        found,
        key=lambda value: (
            value["start"],
            value["end"],
            value["surface_type"],
            value["environment"],
        ),
    ):
        counters[item["surface_type"]] += 1
        result.append(
            {
                **item,
                "id": (
                    f"{BASE}.{item['surface_type']}."
                    f"{counters[item['surface_type']]:04d}"
                ),
                "segment_id": segment_for_line(item["start"]),
                "topic_id": topic_for_line(item["start"]),
            }
        )
    return result


def expected_surface_ids() -> set[str]:
    result = {
        f"{BASE}.{kind}.{number:04d}"
        for kind, count in PRESENT_SURFACES.items()
        for number in range(1, count + 1)
    }
    result.update(f"{BASE}.{kind}.closure" for kind in ABSENT_SURFACES)
    return result


def expected_relation_ids() -> set[str]:
    core = {
        "course-contains-unit",
        "b01-precedes-b02",
        "resource-contains-source-edition",
        "resource-contains-target-edition",
        "target-translates-witness",
        "wrapper-adapts-target",
        "pdf-adapts-wrapper",
        "html-adapts-target",
    }
    result = {f"{BASE}.relation.{suffix}" for suffix in core}
    result.update(
        f"{BASE}.relation.unit-contains-seg{number:04d}" for number in range(1, 4)
    )
    result.update(
        f"{BASE}.relation.unit-contains-topic-{slug}" for slug in TOPIC_SLUGS
    )
    for surface_id in expected_surface_ids():
        suffix = surface_id.removeprefix(f"{BASE}.").replace(".", "-")
        result.add(f"{BASE}.relation.unit-contains-{suffix}")
    for surface in discover_present_surfaces():
        suffix = surface["id"].removeprefix(f"{BASE}.").replace(".", "-")
        result.add(f"{BASE}.relation.{suffix}-to-topic")
    return result


def expected_ids() -> set[str]:
    result = {
        f"{BASE}.resource",
        f"{BASE}.edition.source",
        f"{BASE}.edition.target",
        UNIT_ID,
        f"{BASE}.rights.source.mit",
        f"{BASE}.rights.target.mixed",
        f"{BASE}.rights.tooling",
    }
    result.update(f"{BASE}.topic.{slug}" for slug in TOPIC_SLUGS)
    result.update(f"{BASE}.seg{number:04d}" for number in range(1, 4))
    result.update(expected_surface_ids())
    result.update(f"{BASE}.artifact.{suffix}" for suffix in ARTIFACT_SUFFIX_PATHS)
    result.update(f"{BASE}.qa.{suffix}" for suffix in QA_SUFFIXES)
    result.update(expected_relation_ids())
    return result


def reported_identities(value: Any) -> set[tuple[str, int, str]]:
    found: set[tuple[str, int, str]] = set()
    if isinstance(value, dict):
        if (
            isinstance(value.get("path"), str)
            and isinstance(value.get("bytes"), int)
            and isinstance(value.get("sha256"), str)
        ):
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
        size, sha = FROZEN_IDENTITIES[relative]
        if (relative, size, sha) not in identities:
            raise ValueError(f"{label} does not bind current bytes: {relative}")


def validate_evidence() -> None:
    pending = [
        relative
        for relative, (size, sha) in FROZEN_IDENTITIES.items()
        if size <= 0 or not re.fullmatch(r"[0-9a-f]{64}", sha)
    ]
    if pending:
        raise ValueError(
            "Becker-02 source/build identity table is incomplete: " + ", ".join(pending)
        )
    for relative, expected in FROZEN_IDENTITIES.items():
        if file_info(relative) != expected:
            raise ValueError(f"frozen identity differs: {relative}")

    boundary = json.loads((ROOT / BOUNDARY).read_text(encoding="utf-8"))
    authority = boundary.get("authority", {})
    selected = boundary.get("selected_ranges", [])
    selected_identity = normalized_slice(AUTHORITY, 2750, 2797)
    witness = boundary.get("combined_witness", {})
    if (
        boundary.get("schema") != "o015-becker-02-source-boundary-v1"
        or boundary.get("result") != "pass"
        or boundary.get("upstream_contact") is not False
        or boundary.get("lp_material_imported") is not False
        or authority.get("commit") != COMMIT
        or authority.get("source_path") != AUTHORITY
        or authority.get("source_sha256") != FROZEN_IDENTITIES[AUTHORITY][1]
        or len(selected) != 1
        or selected[0].get("first_line") != 2750
        or selected[0].get("last_line") != 2797
        or (selected[0].get("bytes"), selected[0].get("sha256"))
        != selected_identity
        or witness.get("path") != WITNESS
        or (witness.get("bytes"), witness.get("sha256"))
        != FROZEN_IDENTITIES[WITNESS]
        or witness.get("interior_exact_source_slice_match") is not True
    ):
        raise ValueError("Becker-02 source-boundary evidence differs")
    witness_lines = (ROOT / WITNESS).read_text(encoding="utf-8").splitlines()
    authority_lines = (ROOT / AUTHORITY).read_text(encoding="utf-8").splitlines()
    if witness_lines[1:-1] != authority_lines[2749:2797]:
        raise ValueError("Becker-02 witness interior differs from authority slice")

    pdf = json.loads((ROOT / PDF_REPORT).read_text(encoding="utf-8"))
    artifact = pdf.get("artifact", {})
    if (
        pdf.get("schema") != "o015-becker-02-pdf-build-v1"
        or pdf.get("result") != "pass"
        or pdf.get("byte_identical_clean_builds") is not True
        or pdf.get("canonical_copy_exact_match") is not True
        or pdf.get("upstream_contact") is not False
        or artifact.get("path") != PDF
        or (artifact.get("bytes"), artifact.get("sha256"))
        != FROZEN_IDENTITIES[PDF]
        or artifact.get("pages") != 9
        or artifact.get("language") != "id-ID"
        or artifact.get("encrypted") is not False
        or artifact.get("missing_markers") != []
    ):
        raise ValueError("Becker-02 PDF evidence differs")
    require_bindings(
        pdf, [TARGET, WRAPPER, WITNESS, EXTRACTOR, BOUNDARY, PDF], "PDF report"
    )

    html = json.loads((ROOT / HTML_REPORT).read_text(encoding="utf-8"))
    artifact = html.get("artifact", {})
    if (
        html.get("schema") != "o015-becker-02-html-build-v1"
        or html.get("result") != "pass"
        or (
            html.get("byte_identical_clean_builds") is not True
            and html.get("byte_identical_builds") is not True
        )
        or html.get("upstream_contact") is not False
        or artifact.get("path") != HTML
        or (artifact.get("bytes"), artifact.get("sha256"))
        != FROZEN_IDENTITIES[HTML]
        or artifact.get("failures", []) != []
    ):
        raise ValueError("Becker-02 HTML evidence differs")
    require_bindings(html, [TARGET, WRAPPER, WITNESS, HTML], "HTML report")

    math = json.loads((ROOT / MATH_REPORT).read_text(encoding="utf-8"))
    result = str(math.get("result", math.get("status", ""))).casefold()
    gates = math.get("gate_count", math.get("check_count"))
    if (
        math.get("schema") != "o015-becker-02-open-math-validation-v1"
        or result != "pass"
        or math.get("failures", []) != []
        or math.get("scope", {}).get("upstream_contact") is not False
        or not isinstance(gates, int)
        or gates <= 0
    ):
        raise ValueError("Becker-02 mathematical validation evidence differs")
    require_bindings(
        math, [WITNESS, TARGET, WRAPPER, MATH_VALIDATOR], "math report"
    )


def validate_dataset(jsonl_path: Path, csv_path: Path) -> dict[str, Any]:
    validate_evidence()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonl_raw = jsonl_path.read_bytes()
    csv_raw = csv_path.read_bytes()
    records = [
        json.loads(line)
        for line in jsonl_raw.decode("utf-8", errors="strict").splitlines()
        if line
    ]
    lines = jsonl_raw.splitlines(keepends=True)
    if (
        len(lines) != len(records)
        or any(
            line != (canonical(record) + "\n").encode("utf-8")
            for line, record in zip(lines, records)
        )
    ):
        raise ValueError("JSONL is not canonical compact UTF-8 with LF terminators")
    if len({record["id"] for record in records}) != len(records):
        raise ValueError("duplicate backend IDs")

    reader = csv.DictReader(io.StringIO(csv_raw.decode("utf-8", errors="strict")))
    expected_columns = [
        "schema",
        "schema_version",
        "entity_type",
        "id",
        "record_json",
    ]
    if reader.fieldnames != expected_columns:
        raise ValueError("CSV header differs")
    rows = list(reader)
    if len(rows) != len(records):
        raise ValueError("CSV row count differs")
    for row, record in zip(rows, records):
        if json.loads(row["record_json"]) != record:
            raise ValueError(f"CSV record_json differs for {record['id']}")
        if [row[name] for name in expected_columns[:4]] != [
            record[name] for name in expected_columns[:4]
        ]:
            raise ValueError(f"CSV identity columns differ for {record['id']}")

    rank = {name: index for index, name in enumerate(schema["entity_order"])}
    if records != sorted(
        records, key=lambda record: (rank[record["entity_type"]], record["id"])
    ):
        raise ValueError("global entity/id order differs")
    id_pattern = re.compile(schema["id_pattern"])
    all_ids = {record["id"] for record in records}
    for record in records:
        if record["entity_type"] not in rank:
            raise ValueError(f"unknown entity type {record['entity_type']}")
        missing = [
            field for field in schema["required_common"] if field not in record
        ]
        missing.extend(
            field
            for field in schema["required_by_entity"].get(record["entity_type"], [])
            if field not in record
        )
        if missing:
            raise ValueError(f"{record['id']} lacks required fields {missing}")
        if not id_pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid stable ID {record['id']}")
        if (
            record["entity_type"] == "relation"
            and record["relation_type"] not in schema["relation_types"]
        ):
            raise ValueError(f"invalid relation type in {record['id']}")
        if (
            "translation_state" in record
            and record["translation_state"] not in schema["translation_states"]
        ):
            raise ValueError(f"invalid translation state in {record['id']}")
        for field in schema["reference_fields"]:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")

    baseline_jsonl = strip_jsonl(jsonl_raw)
    baseline_csv = strip_csv(csv_raw)
    if (
        (len(baseline_jsonl), digest(baseline_jsonl)) != BASELINE_JSONL
        or (len(baseline_csv), digest(baseline_csv)) != BASELINE_CSV
        or line_sequence(baseline_jsonl) != BASELINE_LINE_SEQUENCE_SHA256
    ):
        raise ValueError("workflow stripping does not recover exact Becker-01 bytes")
    baseline = [
        record
        for record in records
        if record.get("responsible_workflow") != WORKFLOW
    ]
    new = [
        record
        for record in records
        if record.get("responsible_workflow") == WORKFLOW
    ]
    if (
        len(baseline) != BASELINE_COUNT
        or id_set(baseline) != BASELINE_ID_SET_SHA256
        or id_order(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("protected Becker-01 baseline record set/order differs")
    if (
        len(new) != EXPECTED_NEW_COUNT
        or Counter(record["entity_type"] for record in new)
        != EXPECTED_ENTITY_COUNTS
    ):
        raise ValueError("Becker-02 entity topology differs")
    if {record["id"] for record in new} != expected_ids():
        raise ValueError("Becker-02 stable-ID set differs")
    if any(not record["id"].startswith(f"{BASE}.") for record in new):
        raise ValueError("Becker-02 workflow record escaped its namespace")

    by_id = {record["id"]: record for record in records}
    unit = by_id[UNIT_ID]
    if (
        unit.get("order") != 2
        or unit.get("source_edition_id") != f"{BASE}.edition.source"
        or unit.get("target_edition_id") != f"{BASE}.edition.target"
        or unit.get("target_locator") != f"{TARGET}:1-130"
    ):
        raise ValueError("Becker-02 unit topology differs")

    target_lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    for number, source_start, source_end, target_start, target_end in SEGMENT_RANGES:
        segment_id = f"{BASE}.seg{number:04d}"
        record = by_id[segment_id]
        if (
            record.get("order") != number
            or record.get("source_path") != AUTHORITY
            or record.get("source_line_start") != source_start
            or record.get("source_line_end") != source_end
            or (
                record.get("source_content_bytes"),
                record.get("source_content_sha256"),
            )
            != normalized_slice(AUTHORITY, source_start, source_end)
            or record.get("target_path") != TARGET
            or record.get("target_line_start") != target_start
            or record.get("target_line_end") != target_end
            or (
                record.get("target_content_bytes"),
                record.get("target_content_sha256"),
            )
            != normalized_slice(TARGET, target_start, target_end)
        ):
            raise ValueError(f"Becker-02 segment binding differs: {segment_id}")
        if target_lines[target_start - 1] != (
            f"% B02-S{number:03d} | APPM5720Notes.tex baris "
            f"{source_start}-{source_end}"
        ):
            raise ValueError(f"Becker-02 segment marker differs: {segment_id}")
        if target_lines[target_start] != f"% segment-id: {segment_id}":
            raise ValueError(f"Becker-02 segment stable ID marker differs: {segment_id}")

    discovered = {item["id"]: item for item in discover_present_surfaces()}
    surfaces = [
        record for record in new if record["entity_type"] == "learning_surface"
    ]
    present = [record for record in surfaces if record.get("presence") == "present"]
    absent = [record for record in surfaces if record.get("presence") == "absent"]
    if Counter(record["surface_type"] for record in present) != Counter(PRESENT_SURFACES):
        raise ValueError("Becker-02 stored present-surface census differs")
    if {record["surface_type"] for record in absent} != set(ABSENT_SURFACES):
        raise ValueError("Becker-02 absence closure differs")
    for record in present:
        item = discovered[record["id"]]
        if (
            record.get("target_line_start") != item["start"]
            or record.get("target_line_end") != item["end"]
            or record.get("latex_environment") != item["environment"]
            or record.get("related_segment_ids") != [item["segment_id"]]
            or record.get("concept_ids") != [item["topic_id"]]
            or (
                record.get("target_content_bytes"),
                record.get("target_content_sha256"),
            )
            != normalized_slice(TARGET, item["start"], item["end"])
        ):
            raise ValueError(f"Becker-02 surface binding differs: {record['id']}")

    artifacts = [
        record for record in new if record["entity_type"] == "artifact"
    ]
    if {
        record["id"]: record["path"] for record in artifacts
    } != {
        f"{BASE}.artifact.{suffix}": path
        for suffix, path in ARTIFACT_SUFFIX_PATHS.items()
    }:
        raise ValueError("Becker-02 artifact path map differs")
    for record in artifacts:
        if file_info(record["path"]) != (record["bytes"], record["sha256"]):
            raise ValueError(f"artifact binds stale bytes: {record['id']}")

    qa_records = [record for record in new if record["entity_type"] == "qa_event"]
    if (
        {record["id"] for record in qa_records}
        != {f"{BASE}.qa.{suffix}" for suffix in QA_SUFFIXES}
        or any(
            record.get("result") != "pass" or record.get("status") != "passed"
            for record in qa_records
        )
    ):
        raise ValueError("Becker-02 QA-event closure differs")

    predecessor = by_id[f"{BASE}.relation.b01-precedes-b02"]
    if (
        predecessor.get("relation_type"),
        predecessor.get("source_id"),
        predecessor.get("target_id"),
    ) != ("precedes", "d90.becker.98ed693.b01.unit", UNIT_ID):
        raise ValueError("Becker-01 to Becker-02 predecessor relation differs")
    for number in range(1, 4):
        relation = by_id[f"{BASE}.relation.unit-contains-seg{number:04d}"]
        if (
            relation.get("relation_type"),
            relation.get("source_id"),
            relation.get("target_id"),
        ) != ("contains", UNIT_ID, f"{BASE}.seg{number:04d}"):
            raise ValueError("Becker-02 segment containment relation differs")
    for record in surfaces:
        suffix = record["id"].removeprefix(f"{BASE}.").replace(".", "-")
        relation = by_id[f"{BASE}.relation.unit-contains-{suffix}"]
        if (
            relation.get("relation_type"),
            relation.get("source_id"),
            relation.get("target_id"),
        ) != ("contains", UNIT_ID, record["id"]):
            raise ValueError(f"Becker-02 surface containment differs: {record['id']}")
    for record in present:
        suffix = record["id"].removeprefix(f"{BASE}.").replace(".", "-")
        relation = by_id[f"{BASE}.relation.{suffix}-to-topic"]
        expected_type = (
            "proves"
            if record["surface_type"] in {"theorem", "proof"}
            else "illustrates"
        )
        if (
            relation.get("relation_type"),
            relation.get("source_id"),
            relation.get("target_id"),
        ) != (expected_type, record["id"], record["concept_ids"][0]):
            raise ValueError(f"Becker-02 surface-topic relation differs: {record['id']}")

    return {
        "records": records,
        "new": new,
        "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
        "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
        "new_entity_counts": dict(
            sorted(Counter(record["entity_type"] for record in new).items())
        ),
        "new_id_set_sha256": id_set(new),
        "new_id_order_sha256": id_order(
            sorted(new, key=lambda record: (rank[record["entity_type"]], record["id"]))
        ),
        "new_record_set_sha256": record_set(new),
        "final_id_set_sha256": id_set(records),
        "final_id_order_sha256": id_order(records),
        "final_record_set_sha256": record_set(records),
        "final_line_sequence_sha256": line_sequence(jsonl_raw),
        "baseline_jsonl_recovered": {
            "bytes": len(baseline_jsonl),
            "sha256": digest(baseline_jsonl),
            "line_sequence_sha256": line_sequence(baseline_jsonl),
        },
        "baseline_csv_recovered": {
            "bytes": len(baseline_csv),
            "sha256": digest(baseline_csv),
        },
    }


def deterministic_regeneration(
    jsonl_path: Path, csv_path: Path
) -> list[dict[str, Any]]:
    identities: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(
        prefix="becker-b02-backend-validation-"
    ) as temporary:
        root = Path(temporary)
        for run in (1, 2):
            output_dir = root / f"run-{run}"
            command = [
                sys.executable,
                str(GENERATOR),
                "--input-jsonl",
                str(jsonl_path),
                "--input-csv",
                str(csv_path),
                "--output-dir",
                str(output_dir),
            ]
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            if completed.returncode != 0:
                raise ValueError(
                    f"deterministic regeneration run {run} failed: "
                    f"{completed.stderr or completed.stdout}"
                )
            jsonl_output = output_dir / "records.jsonl"
            csv_output = output_dir / "records.csv"
            identities.append(
                {
                    "run": run,
                    "jsonl": {
                        "bytes": jsonl_output.stat().st_size,
                        "sha256": digest(jsonl_output.read_bytes()),
                    },
                    "csv": {
                        "bytes": csv_output.stat().st_size,
                        "sha256": digest(csv_output.read_bytes()),
                    },
                }
            )
    if (
        identities[0]["jsonl"] != identities[1]["jsonl"]
        or identities[0]["csv"] != identities[1]["csv"]
    ):
        raise ValueError("two Becker-02 deterministic regeneration runs differ")
    if identities[0]["jsonl"] != {
        "bytes": jsonl_path.stat().st_size,
        "sha256": digest(jsonl_path.read_bytes()),
    }:
        raise ValueError("regenerated Becker-02 JSONL differs from validated input")
    if identities[0]["csv"] != {
        "bytes": csv_path.stat().st_size,
        "sha256": digest(csv_path.read_bytes()),
    }:
        raise ValueError("regenerated Becker-02 CSV differs from validated input")
    return identities


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".stage",
            dir=path.parent,
            delete=False,
        ) as handle:
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
    parser.add_argument(
        "--skip-regeneration", action="store_true", help="skip the two-run proof"
    )
    args = parser.parse_args()

    canonical_flags = (
        args.input_jsonl.resolve() == JSONL_PATH.resolve(),
        args.input_csv.resolve() == CSV_PATH.resolve(),
    )
    if canonical_flags[0] != canonical_flags[1]:
        parser.error(
            "--input-jsonl and --input-csv must both be canonical or both staged"
        )
    canonical_backend_written = all(canonical_flags)

    validated = validate_dataset(args.input_jsonl, args.input_csv)
    regenerations = (
        []
        if args.skip_regeneration
        else deterministic_regeneration(args.input_jsonl, args.input_csv)
    )
    receipt = {
        "schema": "o015-becker-02-backend-validation-v1",
        "validated_at": "2026-08-25T14:30:00Z",
        "result": "pass",
        "errors": [],
        "workflow": WORKFLOW,
        "commands": {
            "staging": "python qa/extend_backend_becker_02.py --output-dir <dir>",
            "validation_template": (
                "python qa/validate_backend_becker_02.py "
                "--input-jsonl <jsonl> --input-csv <csv> --receipt <receipt>"
            ),
            "regeneration_template": (
                "python qa/extend_backend_becker_02.py "
                "--input-jsonl <jsonl> --input-csv <csv> --output-dir <dir>"
            ),
        },
        "schema_constraint": {
            "schema_changed": False,
            "additive_records_only": True,
            "note": (
                "Global entity/id sorting means the old file is not a literal "
                "prefix; exact workflow stripping proves every prior JSONL line "
                "and CSV row remains byte-identical and in the same relative order."
            ),
        },
        "protected_baseline": {
            "records": BASELINE_COUNT,
            "jsonl": {
                "bytes": BASELINE_JSONL[0],
                "sha256": BASELINE_JSONL[1],
                "line_sequence_sha256": BASELINE_LINE_SEQUENCE_SHA256,
            },
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
            "disposition": (
                "validated_canonical_backend"
                if canonical_backend_written
                else "validated_staged_projection"
            ),
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
            "final_line_sequence_sha256": validated[
                "final_line_sequence_sha256"
            ],
            "jsonl": validated["jsonl"],
            "csv": validated["csv"],
        },
        "topology": {
            "unit_id": UNIT_ID,
            "segments": 3,
            "topics": 6,
            "present_surfaces": sum(PRESENT_SURFACES.values()),
            "present_surface_counts": PRESENT_SURFACES,
            "absence_closures": 4,
            "source_ranges": [
                f"{start}-{end}" for _, start, end, _, _ in SEGMENT_RANGES
            ],
            "predecessor_relation": f"{BASE}.relation.b01-precedes-b02",
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
