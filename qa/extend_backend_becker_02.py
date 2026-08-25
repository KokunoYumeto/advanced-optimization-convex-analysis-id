#!/usr/bin/env python3
"""Deterministically append the Becker-02 Douglas--Rachford backend records.

The protected input is the exact 3,320-record backend through Becker-01.
Every record owned by this workflow uses the locale-neutral namespace
d90.becker.98ed693.b02.*. A rerun strips only this workflow's records,
recovers the protected JSONL lines and CSV rows byte for byte, validates the
frozen Becker-02 source/build evidence, rejects collisions, and regenerates a
canonical globally sorted JSONL/CSV projection.

Canonical files change only with --write-canonical. That mode also writes the
deterministic receipt qa/BECKER_02_BACKEND_EXTENSION.json.
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
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
RECEIPT_PATH = ROOT / "qa" / "BECKER_02_BACKEND_EXTENSION.json"

RECORDED_AT = "2026-08-25T14:30:00Z"
WORKFLOW = "o015-becker-02-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"
BASE = "d90.becker.98ed693.b02"

BASELINE_RECORD_COUNT = 3_320
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
AUTHORITY_TEX = (
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
GENERATOR = "qa/extend_backend_becker_02.py"
VALIDATOR = "qa/validate_backend_becker_02.py"

SOURCE_RIGHTS_ID = f"{BASE}.rights.source.mit"
TARGET_RIGHTS_ID = f"{BASE}.rights.target.mixed"
TOOLING_RIGHTS_ID = f"{BASE}.rights.tooling"
RESOURCE_ID = f"{BASE}.resource"
SOURCE_EDITION_ID = f"{BASE}.edition.source"
TARGET_EDITION_ID = f"{BASE}.edition.target"
UNIT_ID = f"{BASE}.unit"

FROZEN_IDENTITIES: dict[str, tuple[int, str]] = {
    AUTHORITY_TEX: (
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

SEGMENT_SPECS = [
    {
        "id": f"{BASE}.seg0001",
        "source_ranges": [(2750, 2769)],
        "source_label": "Douglas--Rachford primal, dual, and iteration",
        "target_label": "Masalah primal--dual dan iterasi Douglas--Rachford",
        "topic_slugs": [
            "composite-primal-dual",
            "proximal-resolvent",
            "douglas-rachford-iteration",
        ],
    },
    {
        "id": f"{BASE}.seg0002",
        "source_ranges": [(2771, 2790)],
        "source_label": "Shadow limit and fixed-point motivation",
        "target_label": "Limit bayangan dan motivasi titik tetap",
        "topic_slugs": [
            "proximal-resolvent",
            "shadow-limit-optimality",
            "fixed-point-optimality",
        ],
    },
    {
        "id": f"{BASE}.seg0003",
        "source_ranges": [(2792, 2797)],
        "source_label": "Douglas--Rachford relation to ADMM",
        "target_label": "Hubungan Douglas--Rachford dengan ADMM",
        "topic_slugs": ["admm-dual-link"],
    },
]

TOPIC_SPECS = [
    {
        "slug": "composite-primal-dual",
        "canonical_label": "convex composite primal and Fenchel dual formulations",
        "target_label": "formulasi primal komposit konveks dan dual Fenchel",
        "segments": [1],
        "prerequisites": [],
    },
    {
        "slug": "proximal-resolvent",
        "canonical_label": "proximal mappings as resolvents of scaled subdifferentials",
        "target_label": "pemetaan proksimal sebagai resolven subdiferensial berskala",
        "segments": [1, 2],
        "prerequisites": ["composite-primal-dual"],
    },
    {
        "slug": "douglas-rachford-iteration",
        "canonical_label": "relaxed Douglas--Rachford splitting iteration",
        "target_label": "iterasi pemisahan Douglas--Rachford terelaksasi",
        "segments": [1],
        "prerequisites": ["proximal-resolvent"],
    },
    {
        "slug": "shadow-limit-optimality",
        "canonical_label": "primal optimality of a convergent Douglas--Rachford shadow",
        "target_label": "optimalitas primal limit bayangan Douglas--Rachford",
        "segments": [2],
        "prerequisites": ["douglas-rachford-iteration"],
    },
    {
        "slug": "fixed-point-optimality",
        "canonical_label": "fixed-point characterization through subgradient balance",
        "target_label": "karakterisasi titik tetap melalui keseimbangan subgradien",
        "segments": [2],
        "prerequisites": ["proximal-resolvent"],
    },
    {
        "slug": "admm-dual-link",
        "canonical_label": "ADMM as Douglas--Rachford splitting on a dual problem",
        "target_label": "ADMM sebagai pemisahan Douglas--Rachford pada masalah dual",
        "segments": [3],
        "prerequisites": ["douglas-rachford-iteration"],
    },
]

ENVIRONMENT_SURFACE = {
    "theorem": "theorem",
    "proof": "proof",
    "equation": "equation",
    "multline": "equation",
    "align": "equation",
    "gather": "equation",
}
EXPECTED_PRESENT_SURFACE_COUNTS = Counter(
    {
        "chapter": 1,
        "section": 2,
        "theorem": 1,
        "proof": 1,
        "equation": 10,
    }
)
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
EXPECTED_NEW_RECORD_COUNT = sum(EXPECTED_ENTITY_COUNTS.values())


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    raw = path.read_bytes()
    return len(raw), sha256(raw)


def normalized_slice(relative: str, start: int, end: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid slice {relative}:{start}-{end}")
    raw = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
    return len(raw), sha256(raw)


def normalized_ranges(
    relative: str, ranges: list[tuple[int, int]]
) -> tuple[int, str, list[dict[str, Any]]]:
    chunks: list[bytes] = []
    records: list[dict[str, Any]] = []
    for start, end in ranges:
        size, digest = normalized_slice(relative, start, end)
        lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
        chunk = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
        chunks.append(chunk)
        records.append(
            {
                "line_start": start,
                "line_end": end,
                "bytes": size,
                "sha256": digest,
            }
        )
    raw = b"".join(chunks)
    return len(raw), sha256(raw), records


def id_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "\n".join(sorted(record["id"] for record in records)) + "\n"
    return sha256(payload.encode("utf-8"))


def id_order_sha256(records: list[dict[str, Any]]) -> str:
    payload = "\n".join(record["id"] for record in records) + "\n"
    return sha256(payload.encode("utf-8"))


def record_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "".join(
        canonical_json(record) + "\n"
        for record in sorted(records, key=lambda item: item["id"])
    )
    return sha256(payload.encode("utf-8"))


def line_sequence_sha256(raw: bytes) -> str:
    line_hashes = [sha256(line) for line in raw.splitlines(keepends=True)]
    return sha256(("\n".join(line_hashes) + "\n").encode("utf-8"))


def common(entity_type: str, record_id: str, status: str) -> dict[str, Any]:
    return {
        "schema": RECORD_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "entity_type": entity_type,
        "id": record_id,
        "recorded_at": RECORDED_AT,
        "responsible_workflow": WORKFLOW,
        "status": status,
    }


def artifact(
    suffix: str,
    kind: str,
    path: str,
    rights_id: str,
    **extra: Any,
) -> dict[str, Any]:
    size, digest = file_info(path)
    record = common("artifact", f"{BASE}.artifact.{suffix}", "current")
    record.update(
        {
            "artifact_kind": kind,
            "path": path,
            "bytes": size,
            "sha256": digest,
            "hash_algorithm": "sha256-raw-bytes",
            "rights_id": rights_id,
            **extra,
        }
    )
    return record


def strip_workflow_jsonl(raw: bytes) -> bytes:
    return b"".join(
        line
        for line in raw.splitlines(keepends=True)
        if json.loads(line.decode("utf-8")).get("responsible_workflow") != WORKFLOW
    )


def strip_workflow_csv(raw: bytes) -> bytes:
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


def assert_raw_baseline(jsonl_raw: bytes, csv_raw: bytes, context: str) -> None:
    if (len(jsonl_raw), sha256(jsonl_raw)) != BASELINE_JSONL:
        raise ValueError(f"{context}: JSONL differs from protected Becker-01 backend")
    if (len(csv_raw), sha256(csv_raw)) != BASELINE_CSV:
        raise ValueError(f"{context}: CSV differs from protected Becker-01 backend")
    if line_sequence_sha256(jsonl_raw) != BASELINE_LINE_SEQUENCE_SHA256:
        raise ValueError(f"{context}: JSONL line-byte sequence differs")


def load_baseline(
    input_jsonl: Path, input_csv: Path
) -> tuple[list[dict[str, Any]], bytes, bytes]:
    incoming_jsonl = input_jsonl.read_bytes()
    incoming_csv = input_csv.read_bytes()
    incoming_records = [
        json.loads(line.decode("utf-8"))
        for line in incoming_jsonl.splitlines()
        if line
    ]
    rows = list(csv.DictReader(io.StringIO(incoming_csv.decode("utf-8"))))
    if [json.loads(row["record_json"]) for row in rows] != incoming_records:
        raise ValueError("incoming CSV projection differs from JSONL")
    if len({record["id"] for record in incoming_records}) != len(incoming_records):
        raise ValueError("incoming backend has duplicate IDs")

    baseline = [
        record
        for record in incoming_records
        if record.get("responsible_workflow") != WORKFLOW
    ]
    baseline_jsonl = strip_workflow_jsonl(incoming_jsonl)
    baseline_csv = strip_workflow_csv(incoming_csv)
    assert_raw_baseline(baseline_jsonl, baseline_csv, "workflow-stripped incoming")
    if (
        len(baseline) != BASELINE_RECORD_COUNT
        or id_set_sha256(baseline) != BASELINE_ID_SET_SHA256
        or id_order_sha256(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set_sha256(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("workflow-stripped record set/order differs from baseline")
    return baseline, baseline_jsonl, baseline_csv


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


def require_report_bindings(report: dict[str, Any], paths: list[str], label: str) -> None:
    identities = reported_identities(report)
    for relative in paths:
        size, digest = FROZEN_IDENTITIES[relative]
        if (relative, size, digest) not in identities:
            raise ValueError(f"{label} does not bind current bytes: {relative}")


def validate_frozen_identities() -> dict[str, Any]:
    pending = [
        relative
        for relative, (size, digest) in FROZEN_IDENTITIES.items()
        if size <= 0 or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ]
    if pending:
        raise ValueError(
            "Becker-02 source/build identity table is incomplete: " + ", ".join(pending)
        )
    for relative, expected in FROZEN_IDENTITIES.items():
        if file_info(relative) != expected:
            raise ValueError(f"frozen identity differs: {relative}")

    boundary = json.loads((ROOT / BOUNDARY).read_text(encoding="utf-8"))
    if (
        boundary.get("schema") != "o015-becker-02-source-boundary-v1"
        or boundary.get("result") != "pass"
        or boundary.get("upstream_contact") is not False
        or boundary.get("lp_material_imported") is not False
    ):
        raise ValueError("Becker-02 source boundary is not a strict pass")
    authority = boundary.get("authority", {})
    if (
        authority.get("commit") != COMMIT
        or authority.get("source_path") != AUTHORITY_TEX
        or authority.get("source_sha256") != FROZEN_IDENTITIES[AUTHORITY_TEX][1]
        or authority.get("license") != "MIT"
    ):
        raise ValueError("Becker-02 authority binding differs")
    selected = boundary.get("selected_ranges", [])
    selected_size, selected_digest = normalized_slice(AUTHORITY_TEX, 2750, 2797)
    if (
        len(selected) != 1
        or selected[0].get("id") != "douglas-rachford"
        or selected[0].get("first_line") != 2750
        or selected[0].get("last_line") != 2797
        or selected[0].get("line_count") != 48
        or (selected[0].get("bytes"), selected[0].get("sha256"))
        != (selected_size, selected_digest)
    ):
        raise ValueError("Becker-02 selected source range differs")
    witness = boundary.get("combined_witness", {})
    if (
        witness.get("path") != WITNESS
        or (witness.get("bytes"), witness.get("sha256"))
        != FROZEN_IDENTITIES[WITNESS]
        or witness.get("exact_expected_byte_match") is not True
        or witness.get("interior_exact_source_slice_match") is not True
    ):
        raise ValueError("Becker-02 source witness binding differs")
    witness_lines = (ROOT / WITNESS).read_text(encoding="utf-8").splitlines()
    authority_lines = (ROOT / AUTHORITY_TEX).read_text(encoding="utf-8").splitlines()
    if (
        witness_lines[0] != "% BEGIN douglas-rachford | frozen lines 2750-2797"
        or witness_lines[-1] != "% END douglas-rachford"
        or witness_lines[1:-1] != authority_lines[2749:2797]
    ):
        raise ValueError("Becker-02 witness interior differs from authority slice")

    pdf = json.loads((ROOT / PDF_REPORT).read_text(encoding="utf-8"))
    pdf_artifact = pdf.get("artifact", {})
    if (
        pdf.get("schema") != "o015-becker-02-pdf-build-v1"
        or pdf.get("result") != "pass"
        or pdf.get("byte_identical_clean_builds") is not True
        or pdf.get("canonical_copy_exact_match") is not True
        or pdf.get("upstream_contact") is not False
        or pdf_artifact.get("path") != PDF
        or (pdf_artifact.get("bytes"), pdf_artifact.get("sha256"))
        != FROZEN_IDENTITIES[PDF]
        or pdf_artifact.get("pages") != 9
        or pdf_artifact.get("language") != "id-ID"
        or pdf_artifact.get("encrypted") is not False
        or pdf_artifact.get("missing_markers") != []
    ):
        raise ValueError("Becker-02 PDF evidence differs")
    require_report_bindings(
        pdf, [TARGET, WRAPPER, WITNESS, EXTRACTOR, BOUNDARY, PDF], "PDF report"
    )

    html = json.loads((ROOT / HTML_REPORT).read_text(encoding="utf-8"))
    html_artifact = html.get("artifact", {})
    byte_identical = (
        html.get("byte_identical_clean_builds") is True
        or html.get("byte_identical_builds") is True
    )
    if (
        html.get("schema") != "o015-becker-02-html-build-v1"
        or html.get("result") != "pass"
        or not byte_identical
        or html.get("upstream_contact") is not False
        or html_artifact.get("path") != HTML
        or (html_artifact.get("bytes"), html_artifact.get("sha256"))
        != FROZEN_IDENTITIES[HTML]
        or html_artifact.get("failures", []) != []
    ):
        raise ValueError("Becker-02 HTML evidence differs")
    require_report_bindings(
        html, [TARGET, WRAPPER, WITNESS, HTML], "HTML report"
    )

    math = json.loads((ROOT / MATH_REPORT).read_text(encoding="utf-8"))
    math_result = str(math.get("result", math.get("status", ""))).casefold()
    if (
        math.get("schema") != "o015-becker-02-open-math-validation-v1"
        or math_result != "pass"
        or math.get("failures", []) != []
        or math.get("scope", {}).get("upstream_contact") is not False
    ):
        raise ValueError("Becker-02 mathematical validation is not a strict pass")
    require_report_bindings(
        math, [WITNESS, TARGET, WRAPPER, MATH_VALIDATOR], "math report"
    )
    gate_count = math.get("gate_count", math.get("check_count"))
    if not isinstance(gate_count, int) or gate_count <= 0:
        raise ValueError("Becker-02 math report lacks a positive gate count")
    return {"boundary": boundary, "pdf": pdf, "html": html, "math": math}


SEGMENT_HEADER = re.compile(
    r"^% B02-S(?P<number>\d{3}) \| APPM5720Notes\.tex baris .+$"
)


def parse_segments() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    if len(lines) != 130:
        raise ValueError(f"target physical line count differs: {len(lines)}")
    markers: list[tuple[int, str]] = []
    for line_number, line in enumerate(lines, start=1):
        match = SEGMENT_HEADER.fullmatch(line)
        if not match:
            continue
        if line_number >= len(lines) or not lines[line_number].startswith("% segment-id: "):
            raise ValueError(f"stable segment ID missing after {TARGET}:{line_number}")
        markers.append((line_number, lines[line_number].split(": ", 1)[1]))
    expected_ids = [spec["id"] for spec in SEGMENT_SPECS]
    if [item[1] for item in markers] != expected_ids:
        raise ValueError("Becker-02 target stable segment ID closure differs")

    specs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for index, (marker_line, segment_id) in enumerate(markers, start=1):
        declared = SEGMENT_SPECS[index - 1]
        target_start = marker_line
        target_end = markers[index][0] - 1 if index < len(markers) else len(lines)
        source_ranges = declared["source_ranges"]
        source_bytes, source_digest, range_records = normalized_ranges(
            AUTHORITY_TEX, source_ranges
        )
        target_bytes, target_digest = normalized_slice(TARGET, target_start, target_end)
        spec = {
            **declared,
            "order": index,
            "target_start": target_start,
            "target_end": target_end,
        }
        specs.append(spec)
        record = common("segment", segment_id, "current")
        record.update(
            {
                "unit_id": UNIT_ID,
                "order": index,
                "source_local_id": f"becker-b02-source-segment-{index:04d}",
                "source_local_label": declared["source_label"],
                "target_local_label": declared["target_label"],
                "source_edition_id": SOURCE_EDITION_ID,
                "target_edition_id": TARGET_EDITION_ID,
                "source_language": "en",
                "target_language": "id",
                "target_locale": "id-ID",
                "source_path": AUTHORITY_TEX,
                "source_line_start": min(item[0] for item in source_ranges),
                "source_line_end": max(item[1] for item in source_ranges),
                "source_locator": "; ".join(
                    f"{AUTHORITY_TEX}:{start}-{end}" for start, end in source_ranges
                ),
                "source_ranges": range_records,
                "source_range_count": len(source_ranges),
                "source_content_bytes": source_bytes,
                "source_content_sha256": source_digest,
                "target_path": TARGET,
                "target_line_start": target_start,
                "target_line_end": target_end,
                "target_locator": f"{TARGET}:{target_start}-{target_end}",
                "target_content_bytes": target_bytes,
                "target_content_sha256": target_digest,
                "hash_normalization": "utf8-lf-final-newline",
                "translation_state": "built",
                "structural_review_state": "passed",
                "mathematical_review_state": "open_math_validation_passed",
                "concept_ids": [
                    f"{BASE}.topic.{slug}" for slug in declared["topic_slugs"]
                ],
                "rights_id": TARGET_RIGHTS_ID,
            }
        )
        records.append(record)
    return specs, records


TOKEN = re.compile(r"\\(?P<kind>begin|end)\{(?P<env>[^}]+)\}")
HEADING = re.compile(r"^\\(?P<kind>chapter|section|subsection)\{(?P<title>.+)\}$")


def strip_tex_comment(line: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", line)


def segment_for_target_line(specs: list[dict[str, Any]], line_number: int) -> str:
    matches = [
        spec["id"]
        for spec in specs
        if spec["target_start"] <= line_number <= spec["target_end"]
    ]
    if len(matches) != 1:
        raise ValueError(f"target line {line_number} has {len(matches)} segments")
    return matches[0]


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


def parse_surfaces(
    segment_specs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    found: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = strip_tex_comment(raw_line).strip()
        heading = HEADING.fullmatch(line)
        if heading:
            found.append(
                {
                    "surface_type": heading.group("kind"),
                    "environment": "latex-heading",
                    "start": line_number,
                    "end": line_number,
                    "title": heading.group("title"),
                }
            )
        for match in TOKEN.finditer(line):
            kind = match.group("kind")
            environment = match.group("env")
            if kind == "begin":
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
        raise ValueError(f"unclosed TeX environment in {TARGET}: {stack[-1]}")
    counts = Counter(item["surface_type"] for item in found)
    if counts != EXPECTED_PRESENT_SURFACE_COUNTS:
        raise ValueError(f"Becker-02 semantic surface topology differs: {dict(counts)}")

    counters: Counter[str] = Counter()
    specs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for item in sorted(
        found,
        key=lambda value: (
            value["start"],
            value["end"],
            value["surface_type"],
            value["environment"],
        ),
    ):
        surface_type = item["surface_type"]
        counters[surface_type] += 1
        surface_id = f"{BASE}.{surface_type}.{counters[surface_type]:04d}"
        segment_id = segment_for_target_line(segment_specs, item["start"])
        content_bytes, content_digest = normalized_slice(TARGET, item["start"], item["end"])
        content = "\n".join(lines[item["start"] - 1 : item["end"]])
        topic_id = topic_for_line(item["start"])
        spec = {
            **item,
            "id": surface_id,
            "segment_id": segment_id,
            "topic_id": topic_id,
        }
        specs.append(spec)
        record = common("learning_surface", surface_id, "current")
        record.update(
            {
                "unit_id": UNIT_ID,
                "surface_type": surface_type,
                "presence": "present",
                "count": 1,
                "latex_environment": item["environment"],
                "target_edition_id": TARGET_EDITION_ID,
                "target_path": TARGET,
                "target_line_start": item["start"],
                "target_line_end": item["end"],
                "target_content_bytes": content_bytes,
                "target_content_sha256": content_digest,
                "hash_normalization": "utf8-lf-final-newline",
                "related_segment_ids": [segment_id],
                "concept_ids": [topic_id],
                "latex_labels": re.findall(r"\\label\{([^}]+)\}", content),
                "rights_id": TARGET_RIGHTS_ID,
            }
        )
        if "title" in item:
            record["surface_label"] = item["title"]
        records.append(record)

    authority_lines = (ROOT / AUTHORITY_TEX).read_text(encoding="utf-8").splitlines()
    source_scope = "\n".join(
        "\n".join(authority_lines[start - 1 : end])
        for spec in SEGMENT_SPECS
        for start, end in spec["source_ranges"]
    )
    target_scope = "\n".join(lines)
    for absent in ("exercise", "hint", "answer", "solution"):
        pattern = re.compile(rf"\\begin\{{{absent}s?\}}")
        if pattern.search(source_scope) or pattern.search(target_scope):
            raise ValueError(f"formal {absent} surface unexpectedly present")
        record = common(
            "learning_surface", f"{BASE}.{absent}.closure", "source_absent"
        )
        record.update(
            {
                "unit_id": UNIT_ID,
                "surface_type": absent,
                "presence": "absent",
                "count": 0,
                "absence_scope": "formal environments in the exact admitted source ranges",
                "source_edition_id": SOURCE_EDITION_ID,
                "target_edition_id": TARGET_EDITION_ID,
                "rights_id": TARGET_RIGHTS_ID,
            }
        )
        records.append(record)
    return specs, records


def rights_records() -> list[dict[str, Any]]:
    specs = [
        (
            SOURCE_RIGHTS_ID,
            "admitted",
            "Becker APPM5720Notes Douglas--Rachford donor slice",
            AUTHORITY_TEX,
            "MIT License",
            "https://github.com/stephenbeckr/convex-optimization-class/blob/"
            f"{COMMIT}/LICENSE",
            "https://opensource.org/license/mit",
            [
                "preserve the copyright and permission notice",
                "credit Stephen Becker and Mitchell Krock's typed-notes contribution",
                "preserve inherited Bauschke--Combettes and Lions--Mercier credit",
                "state modifications and no implied endorsement",
            ],
        ),
        (
            TARGET_RIGHTS_ID,
            "admitted_with_separate_component_terms",
            "Becker B02 Indonesian derivative",
            f"{TARGET} + {WRAPPER}",
            "MIT for donor material; CC BY-SA 4.0 for the independent Indonesian translation, corrections, and connective material",
            WRAPPER,
            "https://creativecommons.org/licenses/by-sa/4.0/",
            [
                "preserve the complete MIT notice for donor portions",
                "attribute source, typed-notes, and inherited donor credits",
                "attribute and ShareAlike the independent derivative layer",
                "identify translation and corrections",
                "state non-endorsement",
            ],
        ),
        (
            TOOLING_RIGHTS_ID,
            "admitted",
            "Becker B02 extraction, build, validation, and backend tooling",
            (
                f"{EXTRACTOR} + {PDF_BUILDER} + {HTML_BUILDER} + "
                f"{MATH_VALIDATOR} + {GENERATOR} + {VALIDATOR}"
            ),
            "project-local build and validation code",
            GENERATOR,
            None,
            ["ship source with results", "use open deterministic toolchains"],
        ),
    ]
    records: list[dict[str, Any]] = []
    for record_id, status, component, path, expression, authority, license_url, handling in specs:
        record = common("rights", record_id, status)
        record.update(
            {
                "component_id": component,
                "path": path,
                "source_authority_id": (
                    "becker-convex-optimization-class-98ed693"
                    if record_id == SOURCE_RIGHTS_ID
                    else "lane-authored-derivative-or-tooling"
                ),
                "rights_expression": expression,
                "authority_url": authority,
                "license_url": license_url,
                "translation_permitted": record_id != TOOLING_RIGHTS_ID,
                "required_handling": handling,
            }
        )
        records.append(record)
    return records


def architecture_records() -> list[dict[str, Any]]:
    resource = common("resource", RESOURCE_ID, "source_admitted")
    resource.update(
        {
            "title": "Convex Optimization Class — APPM 5720 Typed Notes",
            "creator": "Stephen Becker",
            "contributors": ["Mitchell Krock (typed notes)"],
            "official_record": "https://github.com/stephenbeckr/convex-optimization-class",
            "official_source_url": (
                "https://github.com/stephenbeckr/convex-optimization-class/tree/"
                f"{COMMIT}/TypedNotes"
            ),
            "rights_id": SOURCE_RIGHTS_ID,
            "curriculum_role": "bounded Douglas--Rachford splitting supplement",
            "scope_exclusion": (
                "adjacent ADMM and primal-dual-method sections are outside this unit"
            ),
        }
    )

    source = common("edition", SOURCE_EDITION_ID, "source_frozen")
    source.update(
        {
            "edition_kind": "immutable_commit_source_slice",
            "resource_id": RESOURCE_ID,
            "rights_id": SOURCE_RIGHTS_ID,
            "version": COMMIT,
            "language": "en",
            "source_artifact_id": f"{BASE}.artifact.authority-tex",
            "authority_url": (
                "https://github.com/stephenbeckr/convex-optimization-class/commit/"
                f"{COMMIT}"
            ),
            "editable_source_format": "LaTeX",
            "selected_ranges_manifest": BOUNDARY,
        }
    )

    target = common("edition", TARGET_EDITION_ID, "built")
    target.update(
        {
            "edition_kind": "independent_derivative_module",
            "resource_id": RESOURCE_ID,
            "rights_id": TARGET_RIGHTS_ID,
            "version": "becker-b02-id-ID-v1",
            "language": "id",
            "locale": "id-ID",
            "source_edition_id": SOURCE_EDITION_ID,
            "translation_state": "built",
            "publication_state": "local_validated_unit",
            "non_endorsement": (
                "Independent Indonesian derivative; no endorsement by source "
                "authors, inherited references, or institutions is implied."
            ),
        }
    )

    unit = common("unit", UNIT_ID, "built")
    unit.update(
        {
            "edition_id": TARGET_EDITION_ID,
            "source_edition_id": SOURCE_EDITION_ID,
            "target_edition_id": TARGET_EDITION_ID,
            "course_id": "course.d90.advanced-optimization-convex-analysis",
            "unit_kind": "bounded_supplement_module",
            "order": 2,
            "source_local_id": "becker-appm5720-douglas-rachford-b02",
            "source_local_label": "Douglas-Rachford",
            "target_local_label": "Pemisahan Douglas--Rachford",
            "source_locator": (
                f"{AUTHORITY_TEX}:2750-2769,2771-2790,2792-2797"
            ),
            "target_locator": f"{TARGET}:1-130",
            "translation_state": "built",
            "rights_id": TARGET_RIGHTS_ID,
            "curriculum_role": "finite Douglas--Rachford operator-splitting supplement",
            "exercise_closure": (
                "no formal exercises, hints, answers, or solutions in the admitted range"
            ),
        }
    )
    return [resource, source, target, unit]


def topic_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in TOPIC_SPECS:
        record_id = f"{BASE}.topic.{spec['slug']}"
        record = common("concept", record_id, "current")
        record.update(
            {
                "canonical_label": spec["canonical_label"],
                "target_label_id_id": spec["target_label"],
                "domain": "convex optimization and monotone operator splitting",
                "prerequisite_ids": [
                    f"{BASE}.topic.{item}" for item in spec["prerequisites"]
                ],
                "related_segment_ids": [
                    f"{BASE}.seg{index:04d}" for index in spec["segments"]
                ],
                "source_edition_id": SOURCE_EDITION_ID,
                "target_edition_id": TARGET_EDITION_ID,
                "rights_id": TARGET_RIGHTS_ID,
            }
        )
        records.append(record)
    return records


def artifact_records(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    html_artifact = evidence["html"]["artifact"]
    math_gate_count = evidence["math"].get(
        "gate_count", evidence["math"].get("check_count")
    )
    return [
        artifact(
            "authority-tex",
            "frozen_authority_tex",
            AUTHORITY_TEX,
            SOURCE_RIGHTS_ID,
            source_commit=COMMIT,
            source_local_path="TypedNotes/APPM5720Notes.tex",
        ),
        artifact("source-witness", "selected_source_witness", WITNESS, SOURCE_RIGHTS_ID),
        artifact("target-body", "translated_tex_body", TARGET, TARGET_RIGHTS_ID),
        artifact("target-wrapper", "reader_tex_wrapper", WRAPPER, TARGET_RIGHTS_ID),
        artifact(
            "source-boundary",
            "source_boundary_manifest",
            BOUNDARY,
            TOOLING_RIGHTS_ID,
            selected_range_count=1,
        ),
        artifact("extractor", "qa_source", EXTRACTOR, TOOLING_RIGHTS_ID),
        artifact("pdf-builder", "build_source", PDF_BUILDER, TOOLING_RIGHTS_ID),
        artifact("pdf-build-report", "build_receipt", PDF_REPORT, TOOLING_RIGHTS_ID),
        artifact(
            "pdf-reader",
            "reader_pdf",
            PDF,
            TARGET_RIGHTS_ID,
            pages=evidence["pdf"]["artifact"]["pages"],
            language="id-ID",
            deterministic_builds=2,
        ),
        artifact("html-builder", "build_source", HTML_BUILDER, TOOLING_RIGHTS_ID),
        artifact("html-build-report", "build_receipt", HTML_REPORT, TOOLING_RIGHTS_ID),
        artifact(
            "html-reader",
            "responsive_html_reader",
            HTML,
            TARGET_RIGHTS_ID,
            language="id-ID",
            deterministic_builds=2,
            math_display_count=html_artifact.get("math_display_count"),
            math_inline_count=html_artifact.get("math_inline_count"),
        ),
        artifact("math-validator", "qa_source", MATH_VALIDATOR, TOOLING_RIGHTS_ID),
        artifact(
            "math-validation-report",
            "computation_receipt",
            MATH_REPORT,
            TOOLING_RIGHTS_ID,
            gate_count=math_gate_count,
        ),
        artifact("backend-generator", "backend_generator", GENERATOR, TOOLING_RIGHTS_ID),
        artifact("backend-validator", "backend_validator", VALIDATOR, TOOLING_RIGHTS_ID),
    ]


def qa_records(
    segment_records: list[dict[str, Any]],
    surface_records: list[dict[str, Any]],
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    present = [record for record in surface_records if record["presence"] == "present"]
    html_artifact = evidence["html"]["artifact"]
    math_gate_count = evidence["math"].get(
        "gate_count", evidence["math"].get("check_count")
    )
    specs = [
        (
            "source-freeze",
            "source_freeze",
            [f"{BASE}.artifact.authority-tex", f"{BASE}.artifact.source-boundary"],
            {
                "source_commit": COMMIT,
                "source_sha256": FROZEN_IDENTITIES[AUTHORITY_TEX][1],
                "selected_range_count": 1,
                "explicit_adjacent_section_exclusions_preserved": True,
            },
        ),
        (
            "segment-binding",
            "stable_id_binding",
            [f"{BASE}.artifact.source-witness", f"{BASE}.artifact.target-body"],
            {
                "segment_count": len(segment_records),
                "segment_ids": [record["id"] for record in segment_records],
                "source_and_target_slices_hashed": True,
                "disjoint_source_ranges_explicit": True,
            },
        ),
        (
            "semantic-surfaces",
            "structure_and_mathematics",
            [f"{BASE}.artifact.target-body"],
            {
                "present_surface_count": len(present),
                "surface_counts": dict(
                    sorted(Counter(record["surface_type"] for record in present).items())
                ),
                "topic_count": len(TOPIC_SPECS),
                "formal_exercise_hint_answer_solution_surfaces": 0,
                "absence_records": 4,
            },
        ),
        (
            "pdf-build",
            "build",
            [
                f"{BASE}.artifact.pdf-builder",
                f"{BASE}.artifact.pdf-build-report",
                f"{BASE}.artifact.pdf-reader",
            ],
            {
                "canonical_build_command": (
                    "python qa/build_becker_douglas_rachford_pdf.py"
                ),
                "deterministic_rebuilds": 2,
                "byte_identical": True,
                "pages": evidence["pdf"]["artifact"]["pages"],
                "pdf_sha256": evidence["pdf"]["artifact"]["sha256"],
                "overfull_boxes": 0,
                "undefined_references": 0,
            },
        ),
        (
            "html-build",
            "html_build",
            [
                f"{BASE}.artifact.html-builder",
                f"{BASE}.artifact.html-build-report",
                f"{BASE}.artifact.html-reader",
            ],
            {
                "canonical_build_command": (
                    "python qa/build_becker_douglas_rachford_html.py"
                ),
                "deterministic_rebuilds": 2,
                "byte_identical": True,
                "math_display_count": html_artifact.get("math_display_count"),
                "math_inline_count": html_artifact.get("math_inline_count"),
                "fragment_links": html_artifact.get("fragment_links"),
                "html_sha256": html_artifact["sha256"],
            },
        ),
        (
            "math-validation",
            "computation",
            [
                f"{BASE}.artifact.math-validator",
                f"{BASE}.artifact.math-validation-report",
                f"{BASE}.artifact.target-body",
            ],
            {
                "gate_count": math_gate_count,
                "all_gates_passed": True,
                "randomness": "none",
                "numerical_witnesses_are_not_proofs": True,
            },
        ),
        (
            "rights",
            "rights",
            [
                f"{BASE}.artifact.authority-tex",
                f"{BASE}.artifact.target-wrapper",
                f"{BASE}.artifact.pdf-reader",
            ],
            {
                "donor_license": "MIT",
                "derivative_layer_license": "CC BY-SA 4.0",
                "component_terms_separate": True,
                "source_typed_notes_and_inherited_credits_preserved": True,
                "non_endorsement": True,
            },
        ),
        (
            "backend-integration",
            "backend_integrity",
            [
                f"{BASE}.artifact.backend-generator",
                f"{BASE}.artifact.backend-validator",
            ],
            {
                "protected_baseline_record_count": BASELINE_RECORD_COUNT,
                "protected_baseline_jsonl_sha256": BASELINE_JSONL[1],
                "protected_baseline_csv_sha256": BASELINE_CSV[1],
                "raw_record_bytes_and_relative_order_preserved": True,
                "new_id_namespace": f"{BASE}.*",
                "collision_count": 0,
                "deterministic_regeneration_runs_required": 2,
            },
        ),
    ]
    records: list[dict[str, Any]] = []
    for suffix, event_type, witnesses, extra in specs:
        record = common("qa_event", f"{BASE}.qa.{suffix}", "passed")
        record.update(
            {
                "event_type": event_type,
                "result": "pass",
                "affected_unit_ids": [UNIT_ID],
                "witness_artifact_ids": witnesses,
                **extra,
            }
        )
        records.append(record)
    return records


def relation_specs(
    segment_records: list[dict[str, Any]],
    surface_specs: list[dict[str, Any]],
    surface_records: list[dict[str, Any]],
) -> list[tuple[str, str, str, str, str]]:
    specs: list[tuple[str, str, str, str, str]] = [
        (
            "course-contains-unit",
            "contains",
            "course.d90.advanced-optimization-convex-analysis",
            UNIT_ID,
            "D90 bounded Becker Douglas--Rachford supplement.",
        ),
        (
            "b01-precedes-b02",
            "precedes",
            "d90.becker.98ed693.b01.unit",
            UNIT_ID,
            "The first Becker supplement precedes the second Becker supplement.",
        ),
        (
            "resource-contains-source-edition",
            "contains",
            RESOURCE_ID,
            SOURCE_EDITION_ID,
            "Frozen source edition.",
        ),
        (
            "resource-contains-target-edition",
            "contains",
            RESOURCE_ID,
            TARGET_EDITION_ID,
            "Independent Indonesian derivative edition.",
        ),
        (
            "target-translates-witness",
            "translates",
            f"{BASE}.artifact.target-body",
            f"{BASE}.artifact.source-witness",
            "The target translates the exact selected source witness.",
        ),
        (
            "wrapper-adapts-target",
            "adapts",
            f"{BASE}.artifact.target-wrapper",
            f"{BASE}.artifact.target-body",
            "Standalone reader wrapper.",
        ),
        (
            "pdf-adapts-wrapper",
            "adapts",
            f"{BASE}.artifact.pdf-reader",
            f"{BASE}.artifact.target-wrapper",
            "Deterministic PDF reader.",
        ),
        (
            "html-adapts-target",
            "adapts",
            f"{BASE}.artifact.html-reader",
            f"{BASE}.artifact.target-body",
            "Deterministic responsive semantic HTML reader.",
        ),
    ]
    for record in segment_records:
        specs.append(
            (
                f"unit-contains-{record['id'].rsplit('.', 1)[1]}",
                "contains",
                UNIT_ID,
                record["id"],
                "Ordered stable source/target segment.",
            )
        )
    for topic in TOPIC_SPECS:
        topic_id = f"{BASE}.topic.{topic['slug']}"
        specs.append(
            (
                f"unit-contains-topic-{topic['slug']}",
                "contains",
                UNIT_ID,
                topic_id,
                "Locale-neutral mathematical topic.",
            )
        )
    for record in surface_records:
        suffix = record["id"].removeprefix(f"{BASE}.").replace(".", "-")
        specs.append(
            (
                f"unit-contains-{suffix}",
                "contains",
                UNIT_ID,
                record["id"],
                "Reader learning surface or explicit source-absence closure.",
            )
        )
    for surface in surface_specs:
        relation_type = {
            "theorem": "proves",
            "proof": "proves",
            "equation": "illustrates",
            "chapter": "illustrates",
            "section": "illustrates",
            "subsection": "illustrates",
        }[surface["surface_type"]]
        suffix = surface["id"].removeprefix(f"{BASE}.").replace(".", "-")
        specs.append(
            (
                f"{suffix}-to-topic",
                relation_type,
                surface["id"],
                surface["topic_id"],
                "Exact target surface bound to its primary mathematical topic.",
            )
        )
    return specs


def relation_records(
    segment_records: list[dict[str, Any]],
    surface_specs: list[dict[str, Any]],
    surface_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for suffix, relation_type, source_id, target_id, note in relation_specs(
        segment_records, surface_specs, surface_records
    ):
        record = common("relation", f"{BASE}.relation.{suffix}", "current")
        record.update(
            {
                "relation_type": relation_type,
                "source_id": source_id,
                "target_id": target_id,
                "note": note,
            }
        )
        records.append(record)
    return records


def generate_records(
    baseline: list[dict[str, Any]], evidence: dict[str, Any]
) -> list[dict[str, Any]]:
    baseline_ids = {record["id"] for record in baseline}
    segment_specs, segments = parse_segments()
    surface_specs, surfaces = parse_surfaces(segment_specs)
    new_records = (
        architecture_records()
        + topic_records()
        + segments
        + surfaces
        + rights_records()
        + artifact_records(evidence)
        + qa_records(segments, surfaces, evidence)
        + relation_records(segments, surface_specs, surfaces)
    )
    new_ids = [record["id"] for record in new_records]
    if any(not record_id.startswith(f"{BASE}.") for record_id in new_ids):
        raise ValueError("generated ID escaped the Becker-02 namespace")
    if len(new_ids) != len(set(new_ids)):
        duplicates = sorted(
            item for item, count in Counter(new_ids).items() if count > 1
        )
        raise ValueError(f"generated duplicate IDs: {duplicates}")
    collisions = sorted(baseline_ids & set(new_ids))
    if collisions:
        raise ValueError(f"generated IDs collide with baseline: {collisions}")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    all_ids = baseline_ids | set(new_ids)
    id_pattern = re.compile(schema["id_pattern"])
    for record in new_records:
        if not id_pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid generated ID: {record['id']}")
        if record["entity_type"] not in schema["entity_order"]:
            raise ValueError(f"unknown generated entity type: {record['entity_type']}")
        required = schema["required_common"] + schema["required_by_entity"].get(
            record["entity_type"], []
        )
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"{record['id']} missing required fields {missing}")
        if (
            record["entity_type"] == "relation"
            and record["relation_type"] not in schema["relation_types"]
        ):
            raise ValueError(f"invalid generated relation type: {record['id']}")
        if (
            "translation_state" in record
            and record["translation_state"] not in schema["translation_states"]
        ):
            raise ValueError(f"invalid generated translation state: {record['id']}")
        for field in schema.get("reference_fields", []):
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")

    counts = Counter(record["entity_type"] for record in new_records)
    if len(new_records) != EXPECTED_NEW_RECORD_COUNT:
        raise ValueError(
            f"new record count {len(new_records)} differs from "
            f"{EXPECTED_NEW_RECORD_COUNT}"
        )
    if counts != EXPECTED_ENTITY_COUNTS:
        raise ValueError(f"new entity topology differs: {dict(counts)}")
    return new_records


def ordered_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    entity_rank = {
        name: index for index, name in enumerate(schema["entity_order"])
    }
    return sorted(
        records, key=lambda record: (entity_rank[record["entity_type"]], record["id"])
    )


def serialize(records: list[dict[str, Any]]) -> tuple[bytes, bytes]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    ordered = ordered_records(records)
    jsonl = "".join(canonical_json(record) + "\n" for record in ordered).encode("utf-8")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(schema["csv_columns"])
    for record in ordered:
        writer.writerow(
            [
                record["schema"],
                record["schema_version"],
                record["entity_type"],
                record["id"],
                canonical_json(record),
            ]
        )
    return jsonl, buffer.getvalue().encode("utf-8")


def assert_baseline_preserved(
    output_jsonl: bytes,
    output_csv: bytes,
    baseline_jsonl: bytes,
    baseline_csv: bytes,
) -> None:
    if strip_workflow_jsonl(output_jsonl) != baseline_jsonl:
        raise ValueError("generated JSONL changes baseline record bytes or relative order")
    if strip_workflow_csv(output_csv) != baseline_csv:
        raise ValueError("generated CSV changes baseline row bytes or relative order")


def atomic_write(path: Path, data: bytes, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.{label}-",
            suffix=".stage",
            dir=path.parent,
            delete=False,
        ) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            staged = Path(handle.name)
        if staged.read_bytes() != data:
            raise ValueError(f"staged readback differs for {path}")
        os.replace(staged, path)
        staged = None
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def atomic_write_pair(
    output_jsonl: Path, output_csv: Path, jsonl: bytes, csv_data: bytes
) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    try:
        for destination, data in ((output_jsonl, jsonl), (output_csv, csv_data)):
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{destination.name}.becker-b02-",
                suffix=".stage",
                dir=destination.parent,
                delete=False,
            ) as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append(Path(handle.name))
        if staged[0].read_bytes() != jsonl or staged[1].read_bytes() != csv_data:
            raise ValueError("staged backend pair readback differs")
        os.replace(staged[0], output_jsonl)
        staged.pop(0)
        os.replace(staged[0], output_csv)
        staged.pop(0)
    finally:
        for path in staged:
            path.unlink(missing_ok=True)


def make_result(
    mode: str,
    new_records: list[dict[str, Any]],
    all_records: list[dict[str, Any]],
    jsonl: bytes,
    csv_data: bytes,
    output_jsonl: Path | None,
    output_csv: Path | None,
) -> dict[str, Any]:
    ordered = ordered_records(all_records)
    return {
        "schema": "o015-becker-02-backend-extension-receipt-v1",
        "result": "pass",
        "workflow": WORKFLOW,
        "write_mode": mode,
        "namespace": f"{BASE}.*",
        "collision_count": 0,
        "protected_baseline": {
            "record_count": BASELINE_RECORD_COUNT,
            "jsonl_bytes": BASELINE_JSONL[0],
            "jsonl_sha256": BASELINE_JSONL[1],
            "csv_bytes": BASELINE_CSV[0],
            "csv_sha256": BASELINE_CSV[1],
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "id_order_sha256": BASELINE_ID_ORDER_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "line_sequence_sha256": BASELINE_LINE_SEQUENCE_SHA256,
            "raw_record_bytes_and_relative_order_preserved": True,
        },
        "new_record_count": len(new_records),
        "new_entity_counts": dict(
            sorted(Counter(record["entity_type"] for record in new_records).items())
        ),
        "new_id_set_sha256": id_set_sha256(new_records),
        "new_record_set_sha256": record_set_sha256(new_records),
        "final_record_count": len(all_records),
        "final_id_set_sha256": id_set_sha256(all_records),
        "final_id_order_sha256": id_order_sha256(ordered),
        "final_record_set_sha256": record_set_sha256(all_records),
        "jsonl": {"bytes": len(jsonl), "sha256": sha256(jsonl)},
        "csv": {"bytes": len(csv_data), "sha256": sha256(csv_data)},
        "source_commit": COMMIT,
        "target": {
            "path": TARGET,
            "bytes": FROZEN_IDENTITIES[TARGET][0],
            "sha256": FROZEN_IDENTITIES[TARGET][1],
            "physical_lines": 130,
        },
        "reader_and_qa_bindings": {
            "pdf_sha256": FROZEN_IDENTITIES[PDF][1],
            "html_sha256": FROZEN_IDENTITIES[HTML][1],
            "math_report_sha256": FROZEN_IDENTITIES[MATH_REPORT][1],
        },
        "segment_count": 3,
        "present_surface_counts": dict(
            sorted(EXPECTED_PRESENT_SURFACE_COUNTS.items())
        ),
        "absent_surface_closure_count": 4,
        "topic_count": len(TOPIC_SPECS),
        "output_jsonl": (
            output_jsonl.relative_to(ROOT).as_posix()
            if output_jsonl and output_jsonl.is_relative_to(ROOT)
            else str(output_jsonl) if output_jsonl else None
        ),
        "output_csv": (
            output_csv.relative_to(ROOT).as_posix()
            if output_csv and output_csv.is_relative_to(ROOT)
            else str(output_csv) if output_csv else None
        ),
        "upstream_contact": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, default=JSONL_PATH)
    parser.add_argument("--input-csv", type=Path, default=CSV_PATH)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--write-canonical", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if sum(bool(item) for item in (args.output_dir, args.write_canonical, args.preflight)) > 1:
        parser.error(
            "--output-dir, --write-canonical, and --preflight are mutually exclusive"
        )

    evidence = validate_frozen_identities()
    baseline, baseline_jsonl, baseline_csv = load_baseline(
        args.input_jsonl, args.input_csv
    )
    new_records = generate_records(baseline, evidence)
    all_records = baseline + new_records
    jsonl, csv_data = serialize(all_records)
    assert_baseline_preserved(jsonl, csv_data, baseline_jsonl, baseline_csv)

    if args.output_dir:
        mode = "staged"
        output_jsonl = args.output_dir / "records.jsonl"
        output_csv = args.output_dir / "records.csv"
        atomic_write_pair(output_jsonl, output_csv, jsonl, csv_data)
    elif args.write_canonical:
        mode = "canonical"
        output_jsonl = JSONL_PATH
        output_csv = CSV_PATH
        atomic_write_pair(output_jsonl, output_csv, jsonl, csv_data)
    elif args.preflight:
        mode = "preflight"
        output_jsonl = None
        output_csv = None
    else:
        mode = "dry-run"
        output_jsonl = None
        output_csv = None

    result = make_result(
        mode, new_records, all_records, jsonl, csv_data, output_jsonl, output_csv
    )
    if args.write_canonical:
        receipt = (
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        atomic_write(RECEIPT_PATH, receipt, "receipt")
        if RECEIPT_PATH.read_bytes() != receipt:
            raise ValueError("canonical receipt readback differs")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
