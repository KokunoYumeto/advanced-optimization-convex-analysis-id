#!/usr/bin/env python3
"""Deterministically append the first Becker supplement to the O015 backend.

The protected input is the exact 3,096-record backend through Habring Chapters
1--2.  Every record owned by this workflow uses the locale-neutral namespace
``d90.becker.98ed693.b01.*``.  A rerun strips only this workflow's records,
reconstructs the protected baseline byte for byte, checks all source and target
bindings, rejects ID collisions, and regenerates the same JSONL/CSV projection.

Canonical files change only with ``--write-canonical``.  That mode also writes
the deterministic QA receipt ``qa/BECKER_01_BACKEND_EXTENSION.json``.
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
RECEIPT_PATH = ROOT / "qa" / "BECKER_01_BACKEND_EXTENSION.json"

RECORDED_AT = "2026-08-25T10:45:00Z"
WORKFLOW = "o015-becker-01-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"
BASE = "d90.becker.98ed693.b01"

BASELINE_RECORD_COUNT = 3_096
BASELINE_JSONL = (
    2_408_339,
    "21f19a4c56276b0abb677c58d9deb23d512e033b7a0f26c241ed9feb72891667",
)
BASELINE_CSV = (
    2_875_457,
    "f3561b09cf15ae2bdd5fc84ee7d464abc720be04d92715200002518e63f4ee2f",
)
BASELINE_ID_SET_SHA256 = "485526ff222b7e84f6e5232775e6186345a4b10b3c44751e7deff4577bcae4f0"
BASELINE_ID_ORDER_SHA256 = "a3afa1645b1a570d6322ef1bb3d5718f9b802f526b9a61a8632ef8909ada3fbf"
BASELINE_RECORD_SET_SHA256 = "b0757ffa96ccaba79aa3fe770e35310cd46afa2175b48bf1ab7e9e28edf7dd2e"
BASELINE_LINE_SEQUENCE_SHA256 = "45258ce6f4d6e8cd70c625038c726bb6044f0f85a7237e8cc23f77400233a502"

COMMIT = "98ed6930084c435ba0f675f7646ced1f2fd8729e"
AUTHORITY_TEX = (
    "authority/becker/extract/"
    f"convex-optimization-class-{COMMIT}/TypedNotes/APPM5720Notes.tex"
)
WITNESS = "source/en/becker-01-lagrange-slater-kkt-source.tex"
TARGET = "source/id-ID/becker-01-dualitas-lagrange-slater-kkt-id.tex"
WRAPPER = "source/id-ID/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex"
BOUNDARY = "qa/BECKER_01_SOURCE_BOUNDARY.json"
EXTRACTOR = "qa/extract_becker_lagrange_kkt_source.py"
PDF_BUILDER = "qa/build_becker_lagrange_kkt_pdf.py"
PDF_REPORT = "qa/BECKER_01_PDF_BUILD.json"
PDF = "output/pdf/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.pdf"
HTML_BUILDER = "qa/build_becker_lagrange_kkt_html.py"
HTML_REPORT = "qa/BECKER_01_HTML_BUILD.json"
HTML = "output/html/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html"
MATH_VALIDATOR = "qa/validate_becker_lagrange_kkt_math.py"
MATH_REPORT = "qa/BECKER_01_MATH_VALIDATION.json"
PDF_VISUAL_REPORT = "qa/BECKER_01_PDF_VISUAL_QA.json"
BROWSER_VISUAL_REPORT = "qa/BECKER_01_BROWSER_VISUAL_QA.json"
GENERATOR = "qa/extend_backend_becker_01.py"

SOURCE_RIGHTS_ID = f"{BASE}.rights.source.mit"
TARGET_RIGHTS_ID = f"{BASE}.rights.target.mixed"
TOOLING_RIGHTS_ID = f"{BASE}.rights.tooling"
RESOURCE_ID = f"{BASE}.resource"
SOURCE_EDITION_ID = f"{BASE}.edition.source"
TARGET_EDITION_ID = f"{BASE}.edition.target"
UNIT_ID = f"{BASE}.unit"

FROZEN_IDENTITIES = {
    AUTHORITY_TEX: (
        130_911,
        "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8",
    ),
    WITNESS: (
        12_294,
        "20335c054393ea43d8912046b6dbfa07f6018f9e16b889e4cd0f66abc064d565",
    ),
    TARGET: (
        12_924,
        "ad656aa517ff418cc1529d2c2c62c602ea95aa2a4dbff9cf1f3f336f26e574ce",
    ),
    WRAPPER: (
        7_330,
        "85903fa4ac1975acd38bbadcd543a954257d7f8eba7552e3ee482bd12b8da04d",
    ),
    BOUNDARY: (
        2_383,
        "abe1c8c46c5e3c94f489e8e81447587d075d55c643f10e6c2f5065349da32da2",
    ),
    EXTRACTOR: (
        4_321,
        "22bb37e886fee84fa6ad10e4f1de504a81983a4a6c9c759dd240509f6e75617b",
    ),
    PDF_BUILDER: (
        7_091,
        "9e9717074e0bcba231c47666cfffbc6e8158908fce1523f2ada3cb58800668b0",
    ),
    PDF_REPORT: (
        3_868,
        "e1ae5997f3901e504e000a9f6c35eb439da17a8419594e7d0d678e3a886207ed",
    ),
    PDF: (
        487_534,
        "c698444856fd01e1ee306d7e3dbca31992f8bb4cf7b4a4cf106ea678be83e615",
    ),
    HTML_BUILDER: (
        13_016,
        "4b90a31aee65bdf39aaeff2de28c1e55b25c9ba42b43ddfffc1a36a38d497b09",
    ),
    HTML_REPORT: (
        699,
        "d6b152f6d7f9da95e274b328623c59f391adb1b12edb122aafede04f1062606d",
    ),
    HTML: (
        30_131,
        "b4a762b10746d394be714177669ad1d5e9903aa04933e8ff4791a179dd0377c0",
    ),
    MATH_VALIDATOR: (
        22_090,
        "7e2c2e370454e7cab486fd02ee722608185d81ebf6b027da992cf4de97bcf7b3",
    ),
    MATH_REPORT: (
        13_799,
        "ed11bcc47d9545b1b8c47ac0ca1aca8b9f27cc23331c4389aeabde7cdaed790b",
    ),
    PDF_VISUAL_REPORT: (
        1_723,
        "6c068de1d31d382f016de4f41949a936005ef8fcdd137721fe93ba9901104fea",
    ),
    BROWSER_VISUAL_REPORT: (
        2_187,
        "6206858c25bcf9dc3f0caaaccaa96d29dd2cdf496e020771663c91f617d09dc7",
    ),
}

# Segment 2 intentionally binds two disjoint admitted source ranges.  The
# bounding source_line_start/end fields satisfy the generic schema; the exact
# source_ranges and their hashes are authoritative and exclude lines 1406--1413.
SEGMENT_SPECS = [
    {
        "id": f"{BASE}.seg0001",
        "source_ranges": [(1263, 1321)],
        "source_label": "Lagrangian and weak duality",
        "target_label": "Lagrangian dan dualitas lemah",
    },
    {
        "id": f"{BASE}.seg0002",
        "source_ranges": [(1398, 1405), (1414, 1470)],
        "source_label": "Slater condition and strong-duality geometry",
        "target_label": "Kondisi Slater dan geometri dualitas kuat",
    },
    {
        "id": f"{BASE}.seg0003",
        "source_ranges": [(1472, 1499)],
        "source_label": "Saddle interpretation and constrained-penalized link",
        "target_label": "Interpretasi titik pelana dan kaitan kendala-penalti",
    },
    {
        "id": f"{BASE}.seg0004",
        "source_ranges": [(1652, 1726)],
        "source_label": "KKT core and l1-ball projection",
        "target_label": "Inti KKT dan proyeksi bola l1",
    },
    {
        "id": f"{BASE}.seg0005",
        "source_ranges": [(1731, 1743)],
        "source_label": "Equality-constrained quadratic KKT system",
        "target_label": "Sistem KKT kuadratik berkendala kesamaan",
    },
]

TOPIC_SPECS = [
    {
        "slug": "primal-lagrangian",
        "canonical_label": "primal minimization problem and Lagrangian",
        "target_label": "masalah minimisasi primal dan Lagrangian",
        "segments": [1],
        "prerequisites": [],
    },
    {
        "slug": "lagrange-dual",
        "canonical_label": "Lagrange dual function and dual problem",
        "target_label": "fungsi dual dan masalah dual Lagrange",
        "segments": [1],
        "prerequisites": ["primal-lagrangian"],
    },
    {
        "slug": "weak-duality",
        "canonical_label": "weak Lagrange duality",
        "target_label": "dualitas lemah Lagrange",
        "segments": [1],
        "prerequisites": ["lagrange-dual"],
    },
    {
        "slug": "slater-strong-duality",
        "canonical_label": "Slater constraint qualification and strong duality",
        "target_label": "kualifikasi kendala Slater dan dualitas kuat",
        "segments": [2],
        "prerequisites": ["weak-duality"],
    },
    {
        "slug": "lagrangian-saddle-point",
        "canonical_label": "Lagrangian saddle-point characterization",
        "target_label": "karakterisasi titik pelana Lagrangian",
        "segments": [3],
        "prerequisites": ["weak-duality"],
    },
    {
        "slug": "constraint-penalty-equivalence",
        "canonical_label": "constraint-penalty equivalence through an optimal multiplier",
        "target_label": "ekuivalensi kendala-penalti melalui pengali optimum",
        "segments": [3],
        "prerequisites": ["primal-lagrangian"],
    },
    {
        "slug": "kkt-conditions",
        "canonical_label": "Karush-Kuhn-Tucker optimality conditions",
        "target_label": "kondisi optimalitas Karush-Kuhn-Tucker",
        "segments": [4, 5],
        "prerequisites": ["slater-strong-duality", "primal-lagrangian"],
    },
    {
        "slug": "l1-ball-projection",
        "canonical_label": "Euclidean projection onto an l1 ball by soft thresholding",
        "target_label": "proyeksi Euklides pada bola l1 dengan ambang lunak",
        "segments": [4],
        "prerequisites": ["kkt-conditions"],
    },
    {
        "slug": "equality-constrained-quadratic-program",
        "canonical_label": "KKT system for an equality-constrained convex quadratic program",
        "target_label": "sistem KKT untuk program kuadratik konveks berkendala kesamaan",
        "segments": [5],
        "prerequisites": ["kkt-conditions"],
    },
]

EXAMPLE_SPECS = [
    (129, 148, "semidefinite-degeneracy", "Degenerate semidefinite primal attainment"),
    (205, 224, "l1-constraint-penalty", "l1 constrained and penalized formulations"),
    (284, 323, "l1-ball-projection", "Projection onto an l1 ball"),
    (326, 348, "equality-qp", "Equality-constrained convex quadratic program"),
]

ENVIRONMENT_SURFACE = {
    "defn": "definition",
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
        "section": 4,
        "subsection": 2,
        "definition": 5,
        "theorem": 5,
        "proof": 2,
        "equation": 26,
        "example": 4,
    }
)
EXPECTED_ENTITY_COUNTS = Counter(
    {
        "resource": 1,
        "edition": 2,
        "unit": 1,
        "concept": 9,
        "segment": 5,
        "learning_surface": 53,
        "rights": 3,
        "artifact": 17,
        "qa_event": 10,
        "relation": 123,
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
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    chunks: list[bytes] = []
    records: list[dict[str, Any]] = []
    for start, end in ranges:
        if start < 1 or end < start or end > len(lines):
            raise ValueError(f"invalid range {relative}:{start}-{end}")
        chunk = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
        chunks.append(chunk)
        records.append(
            {
                "line_start": start,
                "line_end": end,
                "bytes": len(chunk),
                "sha256": sha256(chunk),
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
        raise ValueError(f"{context}: JSONL differs from protected baseline")
    if (len(csv_raw), sha256(csv_raw)) != BASELINE_CSV:
        raise ValueError(f"{context}: CSV differs from protected baseline")
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


def validate_frozen_identities() -> dict[str, Any]:
    for relative, expected in FROZEN_IDENTITIES.items():
        if file_info(relative) != expected:
            raise ValueError(f"frozen identity differs: {relative}")

    boundary = json.loads((ROOT / BOUNDARY).read_text(encoding="utf-8"))
    if boundary.get("result") != "pass":
        raise ValueError("source-boundary manifest is not a pass")
    authority = boundary.get("authority", {})
    if (
        authority.get("commit") != COMMIT
        or authority.get("source_path") != "TypedNotes/APPM5720Notes.tex"
        or authority.get("source_sha256") != FROZEN_IDENTITIES[AUTHORITY_TEX][1]
        or authority.get("license") != "MIT"
    ):
        raise ValueError("source-boundary authority differs")
    selected = {
        item["id"]: (item["first_line"], item["last_line"], item["sha256"])
        for item in boundary.get("selected_ranges", [])
    }
    expected_selected: dict[str, tuple[int, int, str]] = {}
    authority_lines = (ROOT / AUTHORITY_TEX).read_text(encoding="utf-8").splitlines()
    for stable_id, start, end in (
        ("lagrangian-weak-duality", 1263, 1321),
        ("slater-statement", 1398, 1405),
        ("slater-geometry-and-saddle", 1414, 1499),
        ("kkt-core", 1652, 1726),
        ("equality-qp-kkt-system", 1731, 1743),
    ):
        raw = ("\n".join(authority_lines[start - 1 : end]) + "\n").encode("utf-8")
        expected_selected[stable_id] = (start, end, sha256(raw))
    if selected != expected_selected:
        raise ValueError("source-boundary selected-range closure differs")
    if boundary.get("combined_witness", {}).get("sha256") != FROZEN_IDENTITIES[WITNESS][1]:
        raise ValueError("combined source witness differs from boundary")
    if boundary.get("upstream_contact") is not False:
        raise ValueError("source-boundary upstream-contact state differs")

    report = json.loads((ROOT / PDF_REPORT).read_text(encoding="utf-8"))
    if report.get("result") != "pass" or report.get("byte_identical_clean_builds") is not True:
        raise ValueError("PDF report lacks two clean byte-identical builds")
    artifact_report = report.get("artifact", {})
    if (
        artifact_report.get("path") != PDF
        or (artifact_report.get("bytes"), artifact_report.get("sha256"))
        != FROZEN_IDENTITIES[PDF]
        or artifact_report.get("pages") != 12
        or artifact_report.get("language") != "id-ID"
        or artifact_report.get("encrypted") is not False
        or artifact_report.get("missing_markers") != []
    ):
        raise ValueError("PDF report does not bind the current reader")
    expected_inputs = {
        path: digest
        for path, (_, digest) in FROZEN_IDENTITIES.items()
        if path in {TARGET, WRAPPER, BOUNDARY}
    }
    reported_inputs = {item["path"]: item["sha256"] for item in report.get("inputs", [])}
    if any(reported_inputs.get(path) != digest for path, digest in expected_inputs.items()):
        raise ValueError("PDF report input binding differs")

    html = json.loads((ROOT / HTML_REPORT).read_text(encoding="utf-8"))
    html_artifact = html.get("artifact", {})
    if (
        html.get("result") != "pass"
        or html.get("byte_identical_builds") is not True
        or html_artifact.get("path") != HTML
        or (html_artifact.get("bytes"), html_artifact.get("sha256"))
        != FROZEN_IDENTITIES[HTML]
        or html_artifact.get("failures") != []
        or html_artifact.get("math_display_count") != 26
        or html_artifact.get("fragment_links") != 15
    ):
        raise ValueError("HTML report does not bind the current deterministic reader")
    html_inputs = {item["path"]: item["sha256"] for item in html.get("inputs", [])}
    if html_inputs.get(TARGET) != FROZEN_IDENTITIES[TARGET][1]:
        raise ValueError("HTML report target binding differs")

    math = json.loads((ROOT / MATH_REPORT).read_text(encoding="utf-8"))
    if (
        math.get("status") != "PASS"
        or math.get("failures") != []
        or math.get("gate_count") != 10
        or any(gate.get("pass") is not True for gate in math.get("gates", []))
    ):
        raise ValueError("open-math validation report does not prove its ten-gate closure")
    math_inputs = math.get("inputs", {})
    for key, relative in (
        ("source_boundary", BOUNDARY),
        ("target", TARGET),
        ("wrapper", WRAPPER),
        ("validator", MATH_VALIDATOR),
    ):
        reported = math_inputs.get(key, {})
        if (
            reported.get("path") != relative
            or (reported.get("bytes"), reported.get("sha256"))
            != FROZEN_IDENTITIES[relative]
        ):
            raise ValueError(f"open-math input binding differs: {relative}")

    pdf_visual = json.loads((ROOT / PDF_VISUAL_REPORT).read_text(encoding="utf-8"))
    pdf_visual_artifact = pdf_visual.get("artifact", {})
    visual_checks = pdf_visual.get("visual_checks", {})
    if (
        pdf_visual.get("result") != "pass"
        or pdf_visual_artifact.get("path") != PDF
        or (pdf_visual_artifact.get("bytes"), pdf_visual_artifact.get("sha256"))
        != FROZEN_IDENTITIES[PDF]
        or pdf_visual_artifact.get("pages") != 12
        or pdf_visual.get("render", {}).get("rendered_pages") != 12
        or pdf_visual.get("render", {}).get("pages_inspected") != "1-12"
        or any(visual_checks.get(key) != 0 for key in (
            "clipped_text", "overlap", "broken_glyphs", "orphan_or_nearly_empty_pages"
        ))
    ):
        raise ValueError("PDF visual receipt does not bind the current final reader")

    browser = json.loads((ROOT / BROWSER_VISUAL_REPORT).read_text(encoding="utf-8"))
    browser_artifact = browser.get("artifact", {})
    viewports = browser.get("viewports", [])
    if (
        browser.get("result") != "pass"
        or browser_artifact.get("path") != HTML
        or (browser_artifact.get("bytes"), browser_artifact.get("sha256"))
        != FROZEN_IDENTITIES[HTML]
        or len(viewports) != 3
        or any(viewport.get("page_level_horizontal_overflow") is not False for viewport in viewports)
        or browser.get("fragment_links", {}).get("unresolved") != 0
        or browser.get("console_warnings_or_errors") != 0
        or browser.get("inherited_credit_markers", {}).get(
            "boyd_and_vandenberghe_visible_occurrences"
        ) != 2
        or browser.get("inherited_credit_markers", {}).get(
            "bertsekas_visible_occurrences"
        ) != 2
    ):
        raise ValueError("browser visual receipt does not bind the current final HTML")
    return {
        "boundary": boundary,
        "pdf": report,
        "html": html,
        "math": math,
        "pdf_visual": pdf_visual,
        "browser_visual": browser,
    }


SEGMENT_HEADER = re.compile(
    r"^% B01-S(?P<number>\d{3}) \| APPM5720Notes\.tex baris .+$"
)


def parse_segments() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    if len(lines) != 348:
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
        raise ValueError("target stable segment ID closure differs")

    specs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    topics_by_segment = {
        index: [f"{BASE}.topic.{topic['slug']}" for topic in TOPIC_SPECS if index in topic["segments"]]
        for index in range(1, 6)
    }
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
                "source_local_id": f"becker-b01-source-segment-{index:04d}",
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
                "concept_ids": topics_by_segment[index],
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
    if line_number >= 326:
        slug = "equality-constrained-quadratic-program"
    elif line_number >= 284:
        slug = "l1-ball-projection"
    elif line_number >= 226:
        slug = "kkt-conditions"
    elif line_number >= 205:
        slug = "constraint-penalty-equivalence"
    elif line_number >= 174:
        slug = "lagrangian-saddle-point"
    elif line_number >= 105:
        slug = "slater-strong-duality"
    elif line_number >= 76:
        slug = "weak-duality"
    elif line_number >= 51:
        slug = "lagrange-dual"
    else:
        slug = "primal-lagrangian"
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

    expected_example_starts = {
        129: "Kondisi Slater bersifat cukup, bukan perlu.",
        205: "Sebagai contoh, pertimbangkan",
        284: r"\subsection{Contoh: proyeksi pada bola $\ell^1$}",
        326: r"\subsection{Contoh: masalah kuadratik dengan kendala kesamaan}",
    }
    for start, end, slug, title in EXAMPLE_SPECS:
        if not lines[start - 1].startswith(expected_example_starts[start]):
            raise ValueError(f"manual example anchor differs at {TARGET}:{start}")
        found.append(
            {
                "surface_type": "example",
                "environment": "semantic-prose-range",
                "start": start,
                "end": end,
                "example_slug": slug,
                "title": title,
            }
        )

    if Counter(item["surface_type"] for item in found) != EXPECTED_PRESENT_SURFACE_COUNTS:
        raise ValueError(
            "Becker 01 semantic surface topology differs: "
            f"{dict(Counter(item['surface_type'] for item in found))}"
        )

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
        if "example_slug" in item:
            record["source_local_id"] = item["example_slug"]
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
            "Becker APPM5720Notes donor slices",
            AUTHORITY_TEX,
            "MIT License",
            "https://github.com/stephenbeckr/convex-optimization-class/blob/"
            f"{COMMIT}/LICENSE",
            "https://opensource.org/license/mit",
            [
                "preserve the copyright and permission notice",
                "credit Stephen Becker and Mitchell Krock's typed-notes contribution",
                "state modifications and no implied endorsement",
            ],
        ),
        (
            TARGET_RIGHTS_ID,
            "admitted_with_separate_component_terms",
            "Becker B01 Indonesian derivative",
            f"{TARGET} + {WRAPPER}",
            "MIT for donor material; CC BY-SA 4.0 for the independent Indonesian translation, corrections, and connective material",
            WRAPPER,
            "https://creativecommons.org/licenses/by-sa/4.0/",
            [
                "preserve the complete MIT notice for donor portions",
                "attribute source and typed-notes credit",
                "attribute and ShareAlike the independent derivative layer",
                "identify translation and corrections",
                "state non-endorsement",
            ],
        ),
        (
            TOOLING_RIGHTS_ID,
            "admitted",
            "Becker B01 extraction, build, and backend tooling",
            (
                f"{EXTRACTOR} + {PDF_BUILDER} + {HTML_BUILDER} + "
                f"{MATH_VALIDATOR} + {GENERATOR}"
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
            "curriculum_role": "bounded nonduplicative KKT and Slater supplement",
            "scope_exclusion": "adjacent linear-programming duality belongs to O018",
        }
    )

    source = common("edition", SOURCE_EDITION_ID, "source_frozen")
    source.update(
        {
            "edition_kind": "immutable_commit_source_slices",
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
            "version": "becker-b01-id-ID-v1",
            "language": "id",
            "locale": "id-ID",
            "source_edition_id": SOURCE_EDITION_ID,
            "translation_state": "built",
            "publication_state": "local_validated_unit",
            "non_endorsement": "Independent Indonesian derivative; no endorsement by source authors or institutions is implied.",
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
            "order": 1,
            "source_local_id": "becker-appm5720-selected-ranges-b01",
            "source_local_label": "Lagrange Duality, Slater, and KKT",
            "target_local_label": "Dualitas Lagrange, Slater, dan KKT",
            "source_locator": (
                f"{AUTHORITY_TEX}:1263-1321,1398-1405,1414-1499,1652-1726,1731-1743"
            ),
            "target_locator": f"{TARGET}:1-348",
            "translation_state": "built",
            "rights_id": TARGET_RIGHTS_ID,
            "curriculum_role": "finite KKT-Slater-Lagrangian closure supplement",
            "exercise_closure": "no formal exercises, hints, answers, or solutions in admitted source ranges",
        }
    )
    return [resource, source, target, unit]


def topic_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in TOPIC_SPECS:
        record_id = f"{BASE}.topic.{spec['slug']}"
        prerequisites = [
            item if item.startswith("concept.") else f"{BASE}.topic.{item}"
            for item in spec["prerequisites"]
        ]
        record = common("concept", record_id, "current")
        record.update(
            {
                "canonical_label": spec["canonical_label"],
                "target_label_id_id": spec["target_label"],
                "domain": "convex optimization and constrained optimality",
                "prerequisite_ids": prerequisites,
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
            selected_range_count=len(evidence["boundary"]["selected_ranges"]),
        ),
        artifact("extractor", "qa_source", EXTRACTOR, TOOLING_RIGHTS_ID),
        artifact("pdf-builder", "build_source", PDF_BUILDER, TOOLING_RIGHTS_ID),
        artifact(
            "pdf-build-report",
            "build_receipt",
            PDF_REPORT,
            TOOLING_RIGHTS_ID,
        ),
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
        artifact(
            "html-build-report",
            "build_receipt",
            HTML_REPORT,
            TOOLING_RIGHTS_ID,
        ),
        artifact(
            "html-reader",
            "responsive_html_reader",
            HTML,
            TARGET_RIGHTS_ID,
            language="id-ID",
            deterministic_builds=2,
            math_display_count=evidence["html"]["artifact"]["math_display_count"],
            math_inline_count=evidence["html"]["artifact"]["math_inline_count"],
        ),
        artifact("math-validator", "qa_source", MATH_VALIDATOR, TOOLING_RIGHTS_ID),
        artifact(
            "math-validation-report",
            "computation_receipt",
            MATH_REPORT,
            TOOLING_RIGHTS_ID,
            gate_count=evidence["math"]["gate_count"],
        ),
        artifact(
            "pdf-visual-report",
            "visual_qa_receipt",
            PDF_VISUAL_REPORT,
            TOOLING_RIGHTS_ID,
        ),
        artifact(
            "browser-visual-report",
            "browser_qa_receipt",
            BROWSER_VISUAL_REPORT,
            TOOLING_RIGHTS_ID,
        ),
        artifact("backend-generator", "backend_generator", GENERATOR, TOOLING_RIGHTS_ID),
    ]


def qa_records(
    segment_records: list[dict[str, Any]],
    surface_records: list[dict[str, Any]],
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    present = [record for record in surface_records if record["presence"] == "present"]
    specs = [
        (
            "source-freeze",
            "source_freeze",
            [f"{BASE}.artifact.authority-tex", f"{BASE}.artifact.source-boundary"],
            {
                "source_commit": COMMIT,
                "source_sha256": FROZEN_IDENTITIES[AUTHORITY_TEX][1],
                "selected_range_count": 5,
                "explicit_o018_exclusions_preserved": True,
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
                "canonical_build_command": "python qa/build_becker_lagrange_kkt_pdf.py",
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
                "canonical_build_command": "python qa/build_becker_lagrange_kkt_html.py",
                "deterministic_rebuilds": 2,
                "byte_identical": True,
                "math_display_count": evidence["html"]["artifact"]["math_display_count"],
                "math_inline_count": evidence["html"]["artifact"]["math_inline_count"],
                "fragment_links": evidence["html"]["artifact"]["fragment_links"],
                "html_sha256": evidence["html"]["artifact"]["sha256"],
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
                "gate_count": evidence["math"]["gate_count"],
                "all_gates_passed": True,
                "randomness": evidence["math"]["determinism"]["randomness"],
                "numerical_witnesses_are_not_proofs": True,
            },
        ),
        (
            "pdf-visual",
            "visual_qa",
            [
                f"{BASE}.artifact.pdf-reader",
                f"{BASE}.artifact.pdf-visual-report",
            ],
            {
                "pages_rendered_and_inspected": 12,
                "clipped_text": 0,
                "overlap": 0,
                "broken_glyphs": 0,
                "orphan_or_nearly_empty_pages": 0,
                "accessibility_caveat": "PDF is searchable and carries id-ID language metadata but is untagged; use semantic HTML for reflow.",
            },
        ),
        (
            "browser-visual",
            "browser_qa",
            [
                f"{BASE}.artifact.html-reader",
                f"{BASE}.artifact.browser-visual-report",
            ],
            {
                "viewports": 3,
                "page_level_horizontal_overflow": False,
                "unresolved_fragment_links": 0,
                "console_warnings_or_errors": 0,
                "inherited_credit_markers_visible": True,
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
                "source_and_typed_notes_credit_preserved": True,
                "non_endorsement": True,
            },
        ),
        (
            "backend-integration",
            "backend_integrity",
            [f"{BASE}.artifact.backend-generator"],
            {
                "protected_baseline_record_count": BASELINE_RECORD_COUNT,
                "protected_baseline_jsonl_sha256": BASELINE_JSONL[1],
                "protected_baseline_csv_sha256": BASELINE_CSV[1],
                "raw_record_bytes_and_relative_order_preserved": True,
                "new_id_namespace": f"{BASE}.*",
                "collision_count": 0,
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


def relation_records(
    segment_records: list[dict[str, Any]],
    surface_specs: list[dict[str, Any]],
    surface_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs: list[tuple[str, str, str, str, str]] = [
        (
            "course-contains-unit",
            "contains",
            "course.d90.advanced-optimization-convex-analysis",
            UNIT_ID,
            "D90 bounded Becker supplement.",
        ),
        ("resource-contains-source-edition", "contains", RESOURCE_ID, SOURCE_EDITION_ID, "Frozen source edition."),
        ("resource-contains-target-edition", "contains", RESOURCE_ID, TARGET_EDITION_ID, "Independent Indonesian derivative edition."),
        ("target-translates-witness", "translates", f"{BASE}.artifact.target-body", f"{BASE}.artifact.source-witness", "The target translates the exact selected source witness."),
        ("wrapper-adapts-target", "adapts", f"{BASE}.artifact.target-wrapper", f"{BASE}.artifact.target-body", "Standalone reader wrapper."),
        ("pdf-adapts-wrapper", "adapts", f"{BASE}.artifact.pdf-reader", f"{BASE}.artifact.target-wrapper", "Deterministic PDF reader."),
        ("html-adapts-target", "adapts", f"{BASE}.artifact.html-reader", f"{BASE}.artifact.target-body", "Deterministic responsive semantic HTML reader."),
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
            "definition": "defines",
            "theorem": "proves",
            "proof": "proves",
            "example": "illustrates",
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

    records: list[dict[str, Any]] = []
    for suffix, relation_type, source_id, target_id, note in specs:
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
        raise ValueError("generated ID escaped the Becker B01 namespace")
    if len(new_ids) != len(set(new_ids)):
        duplicates = sorted(item for item, count in Counter(new_ids).items() if count > 1)
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
        required = schema["required_common"] + schema["required_by_entity"].get(
            record["entity_type"], []
        )
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"{record['id']} missing required fields {missing}")
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
            f"new record count {len(new_records)} differs from {EXPECTED_NEW_RECORD_COUNT}"
        )
    if counts != EXPECTED_ENTITY_COUNTS:
        raise ValueError(f"new entity topology differs: {dict(counts)}")
    return new_records


def serialize(records: list[dict[str, Any]]) -> tuple[bytes, bytes]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    entity_rank = {name: index for index, name in enumerate(schema["entity_order"])}
    ordered = sorted(
        records, key=lambda record: (entity_rank[record["entity_type"]], record["id"])
    )
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
                prefix=f".{destination.name}.becker-b01-",
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
    return {
        "schema": "o015-becker-01-backend-extension-receipt-v1",
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
        "final_id_order_sha256": id_order_sha256(all_records),
        "final_record_set_sha256": record_set_sha256(all_records),
        "jsonl": {"bytes": len(jsonl), "sha256": sha256(jsonl)},
        "csv": {"bytes": len(csv_data), "sha256": sha256(csv_data)},
        "source_commit": COMMIT,
        "target": {
            "path": TARGET,
            "bytes": FROZEN_IDENTITIES[TARGET][0],
            "sha256": FROZEN_IDENTITIES[TARGET][1],
            "physical_lines": 348,
        },
        "reader_and_qa_bindings": {
            "pdf_sha256": FROZEN_IDENTITIES[PDF][1],
            "html_sha256": FROZEN_IDENTITIES[HTML][1],
            "math_report_sha256": FROZEN_IDENTITIES[MATH_REPORT][1],
            "pdf_visual_report_sha256": FROZEN_IDENTITIES[PDF_VISUAL_REPORT][1],
            "browser_visual_report_sha256": FROZEN_IDENTITIES[BROWSER_VISUAL_REPORT][1],
        },
        "segment_count": 5,
        "present_surface_counts": dict(sorted(EXPECTED_PRESENT_SURFACE_COUNTS.items())),
        "absent_surface_closure_count": 4,
        "topic_count": len(TOPIC_SPECS),
        "output_jsonl": output_jsonl.relative_to(ROOT).as_posix() if output_jsonl else None,
        "output_csv": output_csv.relative_to(ROOT).as_posix() if output_csv else None,
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
        parser.error("--output-dir, --write-canonical, and --preflight are mutually exclusive")

    evidence = validate_frozen_identities()
    baseline, baseline_jsonl, baseline_csv = load_baseline(args.input_jsonl, args.input_csv)
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
        receipt = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        atomic_write(RECEIPT_PATH, receipt, "receipt")
        if RECEIPT_PATH.read_bytes() != receipt:
            raise ValueError("canonical receipt readback differs")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
