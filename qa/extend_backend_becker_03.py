#!/usr/bin/env python3
"""Deterministically append the Becker-03 variance-reduction backend records.

The protected input is the exact 3,430-record backend through Becker-02.
Every record owned by this workflow uses d90.becker.98ed693.b03.*. A rerun
strips only that workflow, proves exact recovery of the protected JSONL/CSV,
validates final B03 evidence, and produces a canonical additive projection.

The current B03 target contains five durable segment markers. Semantic
surfaces are discovered from the frozen target body, including textual hint
and complete-solution surfaces. Missing or incomplete final evidence is a hard
failure. Canonical files change only with --write-canonical.
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
RECEIPT_PATH = ROOT / "qa" / "BECKER_03_BACKEND_EXTENSION.json"

RECORDED_AT = "2026-08-25T16:00:00Z"
WORKFLOW = "o015-becker-03-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"
BASE = "d90.becker.98ed693.b03"

SCHEMA_IDENTITY = (
    3_092,
    "1166cbffe6016044430fe003e4981b1a3a537be7c115f0b646168a1936ab5ad0",
)
BASELINE_RECORD_COUNT = 3_430
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
AUTHORITY_TEX = (
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
GENERATOR = "qa/extend_backend_becker_03.py"
VALIDATOR = "qa/validate_backend_becker_03.py"

SOURCE_RIGHTS_ID = f"{BASE}.rights.source.mit"
TARGET_RIGHTS_ID = f"{BASE}.rights.target.mixed"
TOOLING_RIGHTS_ID = f"{BASE}.rights.tooling"
RESOURCE_ID = f"{BASE}.resource"
SOURCE_EDITION_ID = f"{BASE}.edition.source"
TARGET_EDITION_ID = f"{BASE}.edition.target"
UNIT_ID = f"{BASE}.unit"

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

ARTIFACT_SUFFIX_PATHS = {
    "authority-tex": AUTHORITY_TEX,
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
    "backend-generator": GENERATOR,
    "backend-validator": VALIDATOR,
}

SEGMENT_SPECS = [
    {
        "id": f"{BASE}.seg0001",
        "marker": "% B03-S001 | APPM5720Notes.tex baris 2971-2972",
        "source_ranges": [(2971, 2972)],
        "source_label": "SAA finite-sum model",
        "target_label": "Model jumlah hingga SAA",
        "topic_slug": "finite-sum-saa",
        "content_origin": "translated_and_notationally_normalized",
    },
    {
        "id": f"{BASE}.seg0002",
        "marker": "% B03-S002 | APPM5720Notes.tex baris 2974-2981",
        "source_ranges": [(2974, 2981)],
        "source_label": "SAGA gradient table and update",
        "target_label": "Tabel gradien dan pembaruan SAGA",
        "topic_slug": "saga-estimator",
        "content_origin": "translated_corrected_and_expanded",
    },
    {
        "id": f"{BASE}.seg0003",
        "marker": "% B03-S003 | penghubung matematis mandiri untuk baris 2974-2981",
        "source_ranges": [(2974, 2981)],
        "source_label": "SAGA control-variate context",
        "target_label": "Penghubung ketakbiasan dan identitas varians",
        "topic_slug": "variance-reduction-mechanism",
        "content_origin": "independent_mathematical_connector",
    },
    {
        "id": f"{BASE}.seg0004",
        "marker": "% B03-S004 | APPM5720Notes.tex baris 2982-2988 dengan hipotesis diperbaiki",
        "source_ranges": [(2982, 2988)],
        "source_label": "Linear convergence and averaged iterates",
        "target_label": "Laju SAGA bersyarat dan iterat rata-rata",
        "topic_slug": "saga-convergence-and-averaging",
        "content_origin": "translated_with_corrected_hypotheses",
    },
    {
        "id": f"{BASE}.seg0005",
        "marker": "% B03-S005 | latihan, petunjuk, dan solusi mandiri",
        "source_ranges": [(2971, 2988)],
        "source_label": "Variance-reduction unit context; no donor exercises",
        "target_label": "Latihan, petunjuk, dan solusi mandiri",
        "topic_slug": "variance-reduction-practice",
        "content_origin": "independent_assessment_material",
    },
]

TOPIC_SPECS = [
    {
        "slug": "finite-sum-saa",
        "canonical_label": "finite-sum sample-average approximation objective",
        "target_label": "objektif aproksimasi rata-rata sampel berbentuk jumlah hingga",
        "segment": 1,
        "prerequisites": [],
    },
    {
        "slug": "saga-estimator",
        "canonical_label": "SAGA stored-gradient control-variate estimator",
        "target_label": "penaksir peubah-kontrol SAGA dengan gradien tersimpan",
        "segment": 2,
        "prerequisites": ["finite-sum-saa"],
    },
    {
        "slug": "variance-reduction-mechanism",
        "canonical_label": "conditional unbiasedness and SAGA variance identity",
        "target_label": "ketakbiasan bersyarat dan identitas varians SAGA",
        "segment": 3,
        "prerequisites": ["saga-estimator"],
    },
    {
        "slug": "saga-convergence-and-averaging",
        "canonical_label": "assumption-qualified SAGA convergence and iterate averaging",
        "target_label": "konvergensi SAGA bersyarat dan perataan iterat",
        "segment": 4,
        "prerequisites": ["saga-estimator", "variance-reduction-mechanism"],
    },
    {
        "slug": "variance-reduction-practice",
        "canonical_label": "worked variance-reduction exercises",
        "target_label": "latihan reduksi varians dengan petunjuk dan solusi",
        "segment": 5,
        "prerequisites": ["variance-reduction-mechanism"],
    },
]

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
EXPECTED_PRESENT_SURFACE_COUNTS = Counter(
    {
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
)
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


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"required final Becker-03 artifact is missing: {relative}")
    raw = path.read_bytes()
    if not raw:
        raise ValueError(f"required final Becker-03 artifact is empty: {relative}")
    return len(raw), sha256(raw)


def normalized_slice(relative: str, start: int, end: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid normalized slice {relative}:{start}-{end}")
    raw = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
    return len(raw), sha256(raw)


def normalized_ranges(
    relative: str, ranges: list[tuple[int, int]]
) -> tuple[int, str, list[dict[str, Any]]]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    pieces: list[str] = []
    records: list[dict[str, Any]] = []
    for start, end in ranges:
        if start < 1 or end < start or end > len(lines):
            raise ValueError(f"invalid source range {relative}:{start}-{end}")
        raw = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
        pieces.append(raw.decode("utf-8"))
        records.append(
            {
                "first_line": start,
                "last_line": end,
                "line_count": end - start + 1,
                "bytes": len(raw),
                "sha256": sha256(raw),
                "normalization": "utf8-lf-final-newline",
            }
        )
    combined = "".join(pieces).encode("utf-8")
    return len(combined), sha256(combined), records


def id_set_sha256(records: list[dict[str, Any]]) -> str:
    return sha256(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def id_order_sha256(records: list[dict[str, Any]]) -> str:
    return sha256(("\n".join(record["id"] for record in records) + "\n").encode("utf-8"))


def record_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "\n".join(
        canonical_json(record) for record in sorted(records, key=lambda item: item["id"])
    ) + "\n"
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


def assert_schema_identity() -> dict[str, Any]:
    if file_info("backend/backend_schema.json") != SCHEMA_IDENTITY:
        raise ValueError("backend schema bytes differ from the protected v1.0.0 schema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema" or schema.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("backend schema identity fields differ")
    return schema


def assert_workflow_namespace_closure(records: list[dict[str, Any]]) -> None:
    for record in records:
        owned = record.get("responsible_workflow") == WORKFLOW
        namespaced = str(record.get("id", "")).startswith(f"{BASE}.")
        if owned != namespaced:
            raise ValueError(f"workflow/namespace ownership differs for {record.get('id')}")


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


def load_baseline(input_jsonl: Path, input_csv: Path) -> tuple[list[dict[str, Any]], bytes, bytes]:
    incoming_jsonl = input_jsonl.read_bytes()
    incoming_csv = input_csv.read_bytes()
    records = [json.loads(line) for line in incoming_jsonl.decode("utf-8").splitlines() if line]
    rows = list(csv.DictReader(io.StringIO(incoming_csv.decode("utf-8"))))
    if [json.loads(row["record_json"]) for row in rows] != records:
        raise ValueError("incoming CSV projection differs from JSONL")
    if len({record["id"] for record in records}) != len(records):
        raise ValueError("incoming backend has duplicate IDs")
    assert_workflow_namespace_closure(records)
    baseline = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    baseline_jsonl = strip_workflow_jsonl(incoming_jsonl)
    baseline_csv = strip_workflow_csv(incoming_csv)
    if (len(baseline_jsonl), sha256(baseline_jsonl)) != BASELINE_JSONL:
        raise ValueError("workflow-stripped JSONL differs from protected Becker-02 backend")
    if (len(baseline_csv), sha256(baseline_csv)) != BASELINE_CSV:
        raise ValueError("workflow-stripped CSV differs from protected Becker-02 backend")
    if line_sequence_sha256(baseline_jsonl) != BASELINE_LINE_SEQUENCE_SHA256:
        raise ValueError("protected JSONL line-byte sequence differs")
    if (
        len(baseline) != BASELINE_RECORD_COUNT
        or id_set_sha256(baseline) != BASELINE_ID_SET_SHA256
        or id_order_sha256(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set_sha256(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("protected Becker-02 record set/order differs")
    return baseline, baseline_jsonl, baseline_csv


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


def require_report_bindings(report: dict[str, Any], paths: list[str], label: str) -> None:
    identities = reported_identities(report)
    for relative in paths:
        size, digest = file_info(relative)
        if (relative, size, digest) not in identities:
            raise ValueError(f"{label} does not bind current bytes: {relative}")


def validate_wrapper() -> None:
    text = (ROOT / WRAPPER).read_text(encoding="utf-8")
    required = (
        f"% unit-id: {UNIT_ID}",
        f"% source-edition-id: {SOURCE_EDITION_ID}",
        f"% target-edition-id: {TARGET_EDITION_ID}",
        "\\input{becker-03-reduksi-varians-id}",
    )
    missing = [item for item in required if text.count(item) != 1]
    if missing:
        raise ValueError(f"Becker-03 wrapper identity/input closure differs: {missing}")


def validate_final_evidence() -> dict[str, Any]:
    for relative in ARTIFACT_SUFFIX_PATHS.values():
        file_info(relative)
    if file_info(AUTHORITY_TEX) != AUTHORITY_IDENTITY:
        raise ValueError("Becker-03 frozen authority identity differs")
    if file_info(WITNESS) != WITNESS_IDENTITY:
        raise ValueError("Becker-03 source-witness identity differs")
    if normalized_slice(AUTHORITY_TEX, 2971, 2988) != SOURCE_SLICE_IDENTITY:
        raise ValueError("Becker-03 admitted authority slice differs")
    witness_lines = (ROOT / WITNESS).read_text(encoding="utf-8").splitlines()
    authority_lines = (ROOT / AUTHORITY_TEX).read_text(encoding="utf-8").splitlines()
    if (
        witness_lines[0] != "% BEGIN variance-reduction | frozen lines 2971-2988"
        or witness_lines[-1] != "% END variance-reduction"
        or witness_lines[1:-1] != authority_lines[2970:2988]
    ):
        raise ValueError("Becker-03 witness interior differs from the authority slice")
    validate_wrapper()

    boundary = json.loads((ROOT / BOUNDARY).read_text(encoding="utf-8"))
    if (
        boundary.get("schema") != "o015-becker-03-source-boundary-v1"
        or boundary.get("result") != "pass"
        or boundary.get("upstream_contact") is not False
    ):
        raise ValueError("Becker-03 source boundary is not a strict pass")
    authority = boundary.get("authority", {})
    if (
        authority.get("commit") != COMMIT
        or authority.get("source_path") != AUTHORITY_TEX
        or authority.get("source_sha256") != AUTHORITY_IDENTITY[1]
        or authority.get("license") != "MIT"
    ):
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
    if (
        combined.get("path") != WITNESS
        or (combined.get("bytes"), combined.get("sha256")) != WITNESS_IDENTITY
        or combined.get("exact_expected_byte_match") is not True
        or combined.get("interior_exact_source_slice_match") is not True
    ):
        raise ValueError("Becker-03 source-witness boundary binding differs")

    pdf = json.loads((ROOT / PDF_REPORT).read_text(encoding="utf-8"))
    pdf_artifact = pdf.get("artifact", {})
    pdf_identity = file_info(PDF)
    if (
        pdf.get("schema") != "o015-becker-03-pdf-build-v1"
        or pdf.get("result") != "pass"
        or pdf.get("byte_identical_clean_builds") is not True
        or pdf.get("canonical_copy_exact_match") is not True
        or pdf.get("upstream_contact") is not False
        or pdf_artifact.get("path") != PDF
        or (pdf_artifact.get("bytes"), pdf_artifact.get("sha256")) != pdf_identity
        or not isinstance(pdf_artifact.get("pages"), int)
        or pdf_artifact.get("pages", 0) <= 0
        or pdf_artifact.get("language") != "id-ID"
        or pdf_artifact.get("encrypted") is not False
        or pdf_artifact.get("missing_markers") != []
    ):
        raise ValueError("Becker-03 PDF evidence differs")
    require_report_bindings(pdf, [TARGET, WRAPPER, WITNESS, EXTRACTOR, BOUNDARY, PDF], "PDF report")

    html = json.loads((ROOT / HTML_REPORT).read_text(encoding="utf-8"))
    html_artifact = html.get("artifact", {})
    byte_identical = html.get("byte_identical_clean_builds") is True or html.get("byte_identical_builds") is True
    if (
        html.get("schema") != "o015-becker-03-html-build-v1"
        or html.get("result") != "pass"
        or not byte_identical
        or html.get("upstream_contact") is not False
        or html_artifact.get("path") != HTML
        or (html_artifact.get("bytes"), html_artifact.get("sha256")) != file_info(HTML)
        or html_artifact.get("failures", []) != []
    ):
        raise ValueError("Becker-03 HTML evidence differs")
    require_report_bindings(html, [TARGET, WRAPPER, WITNESS, HTML], "HTML report")

    math = json.loads((ROOT / MATH_REPORT).read_text(encoding="utf-8"))
    math_result = str(math.get("result", math.get("status", ""))).casefold()
    if (
        math.get("schema") != "o015-becker-03-open-math-validation-v1"
        or math_result != "pass"
        or math.get("failures", []) != []
        or math.get("scope", {}).get("upstream_contact") is not False
    ):
        raise ValueError("Becker-03 mathematical validation is not a strict pass")
    require_report_bindings(math, [WITNESS, TARGET, WRAPPER, MATH_VALIDATOR], "math report")
    gate_count = math.get("gate_count", math.get("check_count"))
    if not isinstance(gate_count, int) or gate_count <= 0:
        raise ValueError("Becker-03 math report lacks a positive gate count")
    return {"boundary": boundary, "pdf": pdf, "html": html, "math": math}


def parse_segments() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    marker_to_spec = {spec["marker"]: spec for spec in SEGMENT_SPECS}
    markers = [(number, marker_to_spec[line]) for number, line in enumerate(lines, 1) if line in marker_to_spec]
    if [spec["id"] for _, spec in markers] != [spec["id"] for spec in SEGMENT_SPECS]:
        raise ValueError("Becker-03 target segment-marker closure differs")
    if len({number for number, _ in markers}) != len(SEGMENT_SPECS):
        raise ValueError("Becker-03 target has duplicate segment markers")

    parsed: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for index, (marker_line, declared) in enumerate(markers, 1):
        if marker_line >= len(lines) or lines[marker_line] != f"% segment-id: {declared['id']}":
            raise ValueError(f"stable segment ID missing after {TARGET}:{marker_line}")
        target_end = markers[index][0] - 1 if index < len(markers) else len(lines)
        source_bytes, source_digest, range_records = normalized_ranges(AUTHORITY_TEX, declared["source_ranges"])
        target_bytes, target_digest = normalized_slice(TARGET, marker_line, target_end)
        spec = {**declared, "order": index, "target_start": marker_line, "target_end": target_end}
        parsed.append(spec)
        record = common("segment", declared["id"], "current")
        record.update(
            {
                "unit_id": UNIT_ID,
                "order": index,
                "source_local_id": f"becker-b03-source-segment-{index:04d}",
                "source_local_label": declared["source_label"],
                "target_local_label": declared["target_label"],
                "source_edition_id": SOURCE_EDITION_ID,
                "target_edition_id": TARGET_EDITION_ID,
                "source_language": "en",
                "target_language": "id",
                "target_locale": "id-ID",
                "source_path": AUTHORITY_TEX,
                "source_line_start": min(start for start, _ in declared["source_ranges"]),
                "source_line_end": max(end for _, end in declared["source_ranges"]),
                "source_locator": "; ".join(f"{AUTHORITY_TEX}:{start}-{end}" for start, end in declared["source_ranges"]),
                "source_ranges": range_records,
                "source_range_count": len(declared["source_ranges"]),
                "source_content_bytes": source_bytes,
                "source_content_sha256": source_digest,
                "target_path": TARGET,
                "target_line_start": marker_line,
                "target_line_end": target_end,
                "target_locator": f"{TARGET}:{marker_line}-{target_end}",
                "target_content_bytes": target_bytes,
                "target_content_sha256": target_digest,
                "hash_normalization": "utf8-lf-final-newline",
                "translation_state": "built",
                "structural_review_state": "passed",
                "mathematical_review_state": "open_math_validation_passed",
                "content_origin": declared["content_origin"],
                "concept_ids": [f"{BASE}.topic.{declared['topic_slug']}"],
                "rights_id": TARGET_RIGHTS_ID,
            }
        )
        records.append(record)
    return parsed, records


TOKEN = re.compile(r"\\(?P<kind>begin|end)\{(?P<env>[^}]+)\}")
HEADING = re.compile(r"^\\(?P<kind>chapter|section|subsection)\*?\{(?P<title>.+)\}$")
TEXT_SURFACE = re.compile(r"^\\noindent\\textbf\{(?P<label>Petunjuk|Solusi lengkap)\.\}(?:\\par)?$")


def strip_tex_comment(line: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", line)


def segment_for_target_line(specs: list[dict[str, Any]], line_number: int) -> dict[str, Any]:
    matches = [spec for spec in specs if spec["target_start"] <= line_number <= spec["target_end"]]
    if len(matches) != 1:
        raise ValueError(f"target line {line_number} has {len(matches)} Becker-03 segments")
    return matches[0]


def discover_present_surfaces(segment_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    found: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    text_markers: list[tuple[int, str]] = []
    exercise_starts: list[int] = []
    for line_number, raw in enumerate(lines, 1):
        line = strip_tex_comment(raw).strip()
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
        text_match = TEXT_SURFACE.fullmatch(line)
        if text_match:
            surface_type = "hint" if text_match.group("label") == "Petunjuk" else "solution"
            text_markers.append((line_number, surface_type))
        for match in TOKEN.finditer(line):
            kind = match.group("kind")
            environment = match.group("env")
            if kind == "begin":
                stack.append((environment, line_number))
                if environment == "exercise":
                    exercise_starts.append(line_number)
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

    boundaries = sorted(set([number for number, _ in text_markers] + exercise_starts + [len(lines) + 1]))
    for start, surface_type in text_markers:
        end = min(number for number in boundaries if number > start) - 1
        while end > start and not lines[end - 1].strip():
            end -= 1
        found.append(
            {
                "surface_type": surface_type,
                "environment": "latex-bold-heading",
                "start": start,
                "end": end,
            }
        )

    counts = Counter(item["surface_type"] for item in found)
    if counts != EXPECTED_PRESENT_SURFACE_COUNTS:
        raise ValueError(f"Becker-03 semantic surface topology differs: {dict(counts)}")
    counters: Counter[str] = Counter()
    result: list[dict[str, Any]] = []
    for item in sorted(found, key=lambda value: (value["start"], value["end"], value["surface_type"], value["environment"])):
        counters[item["surface_type"]] += 1
        segment = segment_for_target_line(segment_specs, item["start"])
        result.append(
            {
                **item,
                "id": f"{BASE}.{item['surface_type']}.{counters[item['surface_type']]:04d}",
                "segment_id": segment["id"],
                "topic_id": f"{BASE}.topic.{segment['topic_slug']}",
            }
        )
    return result


def surface_records(segment_specs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = (ROOT / TARGET).read_text(encoding="utf-8").splitlines()
    specs = discover_present_surfaces(segment_specs)
    records: list[dict[str, Any]] = []
    for item in specs:
        content_bytes, content_digest = normalized_slice(TARGET, item["start"], item["end"])
        content = "\n".join(lines[item["start"] - 1 : item["end"]])
        record = common("learning_surface", item["id"], "current")
        record.update(
            {
                "unit_id": UNIT_ID,
                "surface_type": item["surface_type"],
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
                "related_segment_ids": [item["segment_id"]],
                "concept_ids": [item["topic_id"]],
                "latex_labels": re.findall(r"\\label\{([^}]+)\}", content),
                "rights_id": TARGET_RIGHTS_ID,
            }
        )
        if "title" in item:
            record["surface_label"] = item["title"]
        records.append(record)

    authority_lines = (ROOT / AUTHORITY_TEX).read_text(encoding="utf-8").splitlines()
    donor_scope = "\n".join(authority_lines[2970:2988])
    target_counts = Counter(item["surface_type"] for item in specs)
    donor_patterns = {
        "exercise": r"\\begin\{exercises?\}",
        "hint": r"\\begin\{hints?\}|\\textbf\{Hint",
        "answer": r"\\begin\{answers?\}|\\textbf\{Answer",
        "solution": r"\\begin\{solutions?\}|\\textbf\{Solution",
    }
    for kind in SOURCE_ABSENT_SURFACES:
        if re.search(donor_patterns[kind], donor_scope, flags=re.IGNORECASE):
            raise ValueError(f"donor {kind} surface unexpectedly present")
        record = common("learning_surface", f"{BASE}.source.{kind}.closure", "source_absent")
        record.update(
            {
                "unit_id": UNIT_ID,
                "surface_type": kind,
                "presence": "absent",
                "count": 0,
                "absence_scope": "formal or explicitly labelled surfaces in authority lines 2971-2988",
                "source_edition_id": SOURCE_EDITION_ID,
                "target_edition_id": TARGET_EDITION_ID,
                "target_presence": target_counts.get(kind, 0) > 0,
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
            "Becker APPM5720Notes variance-reduction donor slice",
            AUTHORITY_TEX,
            "MIT License",
            f"https://github.com/stephenbeckr/convex-optimization-class/blob/{COMMIT}/LICENSE",
            "https://opensource.org/license/mit",
            ["preserve copyright and permission notice", "credit Stephen Becker and Mitchell Krock", "state modifications and no implied endorsement"],
        ),
        (
            TARGET_RIGHTS_ID,
            "admitted_with_separate_component_terms",
            "Becker B03 Indonesian derivative",
            f"{TARGET} + {WRAPPER}",
            "MIT for donor material; CC BY-SA 4.0 for independent Indonesian translation, corrections, connective material, exercises, hints, and solutions",
            WRAPPER,
            "https://creativecommons.org/licenses/by-sa/4.0/",
            ["preserve MIT notice for donor portions", "attribute source and typed-notes credits", "ShareAlike the independent derivative layer", "identify translation and corrections", "state non-endorsement"],
        ),
        (
            TOOLING_RIGHTS_ID,
            "admitted",
            "Becker B03 extraction, build, validation, and backend tooling",
            f"{EXTRACTOR} + {PDF_BUILDER} + {HTML_BUILDER} + {MATH_VALIDATOR} + {GENERATOR} + {VALIDATOR}",
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
                "source_authority_id": "becker-convex-optimization-class-98ed693" if record_id == SOURCE_RIGHTS_ID else "lane-authored-derivative-or-tooling",
                "rights_expression": expression,
                "authority_url": authority,
                "license_url": license_url,
                "translation_permitted": record_id != TOOLING_RIGHTS_ID,
                "required_handling": handling,
            }
        )
        records.append(record)
    return records


def architecture_records(target_line_count: int) -> list[dict[str, Any]]:
    resource = common("resource", RESOURCE_ID, "source_admitted")
    resource.update(
        {
            "title": "Convex Optimization Class — APPM 5720 Typed Notes",
            "creator": "Stephen Becker",
            "contributors": ["Mitchell Krock (typed notes)"],
            "official_record": "https://github.com/stephenbeckr/convex-optimization-class",
            "official_source_url": f"https://github.com/stephenbeckr/convex-optimization-class/tree/{COMMIT}/TypedNotes",
            "rights_id": SOURCE_RIGHTS_ID,
            "curriculum_role": "bounded variance-reduction supplement",
            "scope_exclusion": "all source material outside APPM5720Notes.tex lines 2971-2988",
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
            "authority_url": f"https://github.com/stephenbeckr/convex-optimization-class/commit/{COMMIT}",
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
            "version": "becker-b03-id-ID-v1",
            "language": "id",
            "locale": "id-ID",
            "source_edition_id": SOURCE_EDITION_ID,
            "translation_state": "built",
            "publication_state": "local_validated_unit",
            "non_endorsement": "Independent Indonesian derivative; no endorsement by source authors, cited researchers, or institutions is implied.",
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
            "order": 3,
            "source_local_id": "becker-appm5720-variance-reduction-b03",
            "source_local_label": "Variance Reduced Methods for SAA",
            "target_local_label": "Reduksi Varians untuk SAA",
            "source_locator": f"{AUTHORITY_TEX}:2971-2988",
            "target_locator": f"{TARGET}:1-{target_line_count}",
            "translation_state": "built",
            "rights_id": TARGET_RIGHTS_ID,
            "curriculum_role": "finite variance-reduction and SAGA supplement",
            "source_assessment_closure": "no exercises, hints, answers, or solutions in the admitted donor range",
            "target_assessment_material": "two independent exercises with hints and complete solutions",
        }
    )
    return [resource, source, target, unit]


def topic_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in TOPIC_SPECS:
        record = common("concept", f"{BASE}.topic.{spec['slug']}", "current")
        record.update(
            {
                "canonical_label": spec["canonical_label"],
                "target_label_id_id": spec["target_label"],
                "domain": "stochastic finite-sum convex optimization",
                "prerequisite_ids": [f"{BASE}.topic.{slug}" for slug in spec["prerequisites"]],
                "related_segment_ids": [f"{BASE}.seg{spec['segment']:04d}"],
                "source_edition_id": SOURCE_EDITION_ID,
                "target_edition_id": TARGET_EDITION_ID,
                "rights_id": TARGET_RIGHTS_ID,
            }
        )
        records.append(record)
    return records


def artifact_record(suffix: str, kind: str, path: str, rights_id: str, **extra: Any) -> dict[str, Any]:
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


def artifact_records(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    pdf_artifact = evidence["pdf"]["artifact"]
    html_artifact = evidence["html"]["artifact"]
    math_gate_count = evidence["math"].get("gate_count", evidence["math"].get("check_count"))
    return [
        artifact_record("authority-tex", "frozen_authority_tex", AUTHORITY_TEX, SOURCE_RIGHTS_ID, source_commit=COMMIT, source_local_path="TypedNotes/APPM5720Notes.tex"),
        artifact_record("source-witness", "selected_source_witness", WITNESS, SOURCE_RIGHTS_ID),
        artifact_record("target-body", "translated_tex_body", TARGET, TARGET_RIGHTS_ID),
        artifact_record("target-wrapper", "reader_tex_wrapper", WRAPPER, TARGET_RIGHTS_ID),
        artifact_record("source-boundary", "source_boundary_manifest", BOUNDARY, TOOLING_RIGHTS_ID, selected_range_count=1),
        artifact_record("extractor", "qa_source", EXTRACTOR, TOOLING_RIGHTS_ID),
        artifact_record("pdf-builder", "build_source", PDF_BUILDER, TOOLING_RIGHTS_ID),
        artifact_record("pdf-build-report", "build_receipt", PDF_REPORT, TOOLING_RIGHTS_ID),
        artifact_record("pdf-reader", "reader_pdf", PDF, TARGET_RIGHTS_ID, pages=pdf_artifact["pages"], language="id-ID", deterministic_builds=2),
        artifact_record("html-builder", "build_source", HTML_BUILDER, TOOLING_RIGHTS_ID),
        artifact_record("html-build-report", "build_receipt", HTML_REPORT, TOOLING_RIGHTS_ID),
        artifact_record("html-reader", "responsive_html_reader", HTML, TARGET_RIGHTS_ID, language="id-ID", deterministic_builds=2, math_display_count=html_artifact.get("math_display_count"), math_inline_count=html_artifact.get("math_inline_count")),
        artifact_record("math-validator", "qa_source", MATH_VALIDATOR, TOOLING_RIGHTS_ID),
        artifact_record("math-validation-report", "computation_receipt", MATH_REPORT, TOOLING_RIGHTS_ID, gate_count=math_gate_count),
        artifact_record("backend-generator", "backend_generator", GENERATOR, TOOLING_RIGHTS_ID),
        artifact_record("backend-validator", "backend_validator", VALIDATOR, TOOLING_RIGHTS_ID),
    ]


def qa_records(segment_records: list[dict[str, Any]], surfaces: list[dict[str, Any]], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    present = [record for record in surfaces if record["presence"] == "present"]
    html_artifact = evidence["html"]["artifact"]
    math_gate_count = evidence["math"].get("gate_count", evidence["math"].get("check_count"))
    specs = [
        ("source-freeze", "source_freeze", [f"{BASE}.artifact.authority-tex", f"{BASE}.artifact.source-boundary"], {"source_commit": COMMIT, "source_sha256": AUTHORITY_IDENTITY[1], "selected_range_count": 1, "selected_source_lines": "2971-2988"}),
        ("segment-binding", "stable_id_binding", [f"{BASE}.artifact.source-witness", f"{BASE}.artifact.target-body"], {"segment_count": len(segment_records), "segment_ids": [record["id"] for record in segment_records], "source_and_target_slices_hashed": True, "independent_derivative_segments_explicit": True}),
        ("semantic-surfaces", "structure_and_mathematics", [f"{BASE}.artifact.target-body"], {"present_surface_count": len(present), "surface_counts": dict(sorted(Counter(record["surface_type"] for record in present).items())), "topic_count": len(TOPIC_SPECS), "source_absence_records": len(SOURCE_ABSENT_SURFACES), "target_exercise_count": sum(record["surface_type"] == "exercise" for record in present), "target_hint_count": sum(record["surface_type"] == "hint" for record in present), "target_solution_count": sum(record["surface_type"] == "solution" for record in present)}),
        ("pdf-build", "build", [f"{BASE}.artifact.pdf-builder", f"{BASE}.artifact.pdf-build-report", f"{BASE}.artifact.pdf-reader"], {"canonical_build_command": "python qa/build_becker_variance_reduction_pdf.py", "deterministic_rebuilds": 2, "byte_identical": True, "pages": evidence["pdf"]["artifact"]["pages"], "pdf_sha256": evidence["pdf"]["artifact"]["sha256"]}),
        ("html-build", "html_build", [f"{BASE}.artifact.html-builder", f"{BASE}.artifact.html-build-report", f"{BASE}.artifact.html-reader"], {"canonical_build_command": "python qa/build_becker_variance_reduction_html.py", "deterministic_rebuilds": 2, "byte_identical": True, "math_display_count": html_artifact.get("math_display_count"), "math_inline_count": html_artifact.get("math_inline_count"), "html_sha256": html_artifact["sha256"]}),
        ("math-validation", "computation", [f"{BASE}.artifact.math-validator", f"{BASE}.artifact.math-validation-report", f"{BASE}.artifact.target-body"], {"gate_count": math_gate_count, "all_gates_passed": True, "randomness": "none", "numerical_witnesses_are_not_proofs": True}),
        ("rights", "rights", [f"{BASE}.artifact.authority-tex", f"{BASE}.artifact.target-wrapper", f"{BASE}.artifact.pdf-reader"], {"donor_license": "MIT", "derivative_layer_license": "CC BY-SA 4.0", "component_terms_separate": True, "independent_exercises_identified": True, "non_endorsement": True}),
        ("backend-integration", "backend_integrity", [f"{BASE}.artifact.backend-generator", f"{BASE}.artifact.backend-validator"], {"protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_record_bytes_and_relative_order_preserved": True, "new_id_namespace": f"{BASE}.*", "collision_count": 0, "deterministic_regeneration_runs_required": 2}),
    ]
    records: list[dict[str, Any]] = []
    for suffix, event_type, witnesses, extra in specs:
        record = common("qa_event", f"{BASE}.qa.{suffix}", "passed")
        record.update({"event_type": event_type, "result": "pass", "affected_unit_ids": [UNIT_ID], "witness_artifact_ids": witnesses, **extra})
        records.append(record)
    return records


def relation_records(segment_records: list[dict[str, Any]], surface_specs: list[dict[str, Any]], surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs: list[tuple[str, str, str, str, str]] = [
        ("course-contains-unit", "contains", "course.d90.advanced-optimization-convex-analysis", UNIT_ID, "D90 bounded Becker variance-reduction supplement."),
        ("b02-precedes-b03", "precedes", "d90.becker.98ed693.b02.unit", UNIT_ID, "The Douglas--Rachford supplement precedes the variance-reduction supplement."),
        ("resource-contains-source-edition", "contains", RESOURCE_ID, SOURCE_EDITION_ID, "Frozen source edition."),
        ("resource-contains-target-edition", "contains", RESOURCE_ID, TARGET_EDITION_ID, "Independent Indonesian derivative edition."),
        ("target-translates-witness", "translates", f"{BASE}.artifact.target-body", f"{BASE}.artifact.source-witness", "Target derives from the exact selected source witness with explicit independent additions."),
        ("wrapper-adapts-target", "adapts", f"{BASE}.artifact.target-wrapper", f"{BASE}.artifact.target-body", "Standalone reader wrapper."),
        ("pdf-adapts-wrapper", "adapts", f"{BASE}.artifact.pdf-reader", f"{BASE}.artifact.target-wrapper", "Deterministic PDF reader."),
        ("html-adapts-target", "adapts", f"{BASE}.artifact.html-reader", f"{BASE}.artifact.target-body", "Deterministic responsive HTML reader."),
    ]
    for record in segment_records:
        specs.append((f"unit-contains-{record['id'].rsplit('.', 1)[1]}", "contains", UNIT_ID, record["id"], "Ordered stable source/target segment."))
    for topic in TOPIC_SPECS:
        topic_id = f"{BASE}.topic.{topic['slug']}"
        specs.append((f"unit-contains-topic-{topic['slug']}", "contains", UNIT_ID, topic_id, "Locale-neutral mathematical topic."))
    for record in surfaces:
        suffix = record["id"].removeprefix(f"{BASE}.").replace(".", "-")
        specs.append((f"unit-contains-{suffix}", "contains", UNIT_ID, record["id"], "Target learning surface or explicit donor-absence closure."))
    for surface in surface_specs:
        relation_type = "proves" if surface["surface_type"] in {"theorem", "proposition", "proof"} else "exercises" if surface["surface_type"] in {"exercise", "hint", "solution"} else "illustrates"
        suffix = surface["id"].removeprefix(f"{BASE}.").replace(".", "-")
        specs.append((f"{suffix}-to-topic", relation_type, surface["id"], surface["topic_id"], "Exact target surface bound to its primary mathematical topic."))
    present_ids = {surface["id"] for surface in surface_specs}
    for number in (1, 2):
        exercise_id = f"{BASE}.exercise.{number:04d}"
        hint_id = f"{BASE}.hint.{number:04d}"
        solution_id = f"{BASE}.solution.{number:04d}"
        required = {exercise_id, hint_id, solution_id}
        if not required <= present_ids:
            raise ValueError(f"missing exercise/hint/solution pairing for Becker-03 item {number}")
        specs.append((f"hint-{number:04d}-depends-on-exercise-{number:04d}", "depends-on", hint_id, exercise_id, "Explicit hint-to-exercise pairing."))
        specs.append((f"solution-{number:04d}-depends-on-exercise-{number:04d}", "depends-on", solution_id, exercise_id, "Explicit complete-solution-to-exercise pairing."))
    records: list[dict[str, Any]] = []
    for suffix, relation_type, source_id, target_id, note in specs:
        record = common("relation", f"{BASE}.relation.{suffix}", "current")
        record.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        records.append(record)
    return records


def generate_records(baseline: list[dict[str, Any]], evidence: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, Any]]:
    segment_specs, segments = parse_segments()
    present_specs, surfaces = surface_records(segment_specs)
    target_line_count = len((ROOT / TARGET).read_text(encoding="utf-8").splitlines())
    relations = relation_records(segments, present_specs, surfaces)
    new_records = architecture_records(target_line_count) + topic_records() + segments + surfaces + rights_records() + artifact_records(evidence) + qa_records(segments, surfaces, evidence) + relations
    baseline_ids = {record["id"] for record in baseline}
    new_ids = [record["id"] for record in new_records]
    if any(not record_id.startswith(f"{BASE}.") for record_id in new_ids):
        raise ValueError("generated ID escaped the Becker-03 namespace")
    if len(new_ids) != len(set(new_ids)):
        duplicates = sorted(item for item, count in Counter(new_ids).items() if count > 1)
        raise ValueError(f"generated duplicate IDs: {duplicates}")
    collisions = sorted(baseline_ids & set(new_ids))
    if collisions:
        raise ValueError(f"generated IDs collide with baseline: {collisions}")
    all_ids = baseline_ids | set(new_ids)
    id_pattern = re.compile(schema["id_pattern"])
    for record in new_records:
        if not id_pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid generated ID: {record['id']}")
        if record["entity_type"] not in schema["entity_order"]:
            raise ValueError(f"unknown generated entity type: {record['entity_type']}")
        required = schema["required_common"] + schema["required_by_entity"].get(record["entity_type"], [])
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"{record['id']} missing required fields {missing}")
        if record["entity_type"] == "relation" and record["relation_type"] not in schema["relation_types"]:
            raise ValueError(f"invalid generated relation type: {record['id']}")
        if "translation_state" in record and record["translation_state"] not in schema["translation_states"]:
            raise ValueError(f"invalid generated translation state: {record['id']}")
        for field in schema.get("reference_fields", []):
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")
    expected_counts = Counter(
        {
            "resource": 1,
            "edition": 2,
            "unit": 1,
            "concept": len(TOPIC_SPECS),
            "segment": len(SEGMENT_SPECS),
            "learning_surface": len(surfaces),
            "rights": 3,
            "artifact": len(ARTIFACT_SUFFIX_PATHS),
            "qa_event": len(QA_SUFFIXES),
            "relation": len(relations),
        }
    )
    if Counter(record["entity_type"] for record in new_records) != expected_counts:
        raise ValueError("Becker-03 generated entity topology differs")
    return new_records


def ordered_records(records: list[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    rank = {name: index for index, name in enumerate(schema["entity_order"])}
    return sorted(records, key=lambda record: (rank[record["entity_type"]], record["id"]))


def serialize(records: list[dict[str, Any]], schema: dict[str, Any]) -> tuple[bytes, bytes]:
    ordered = ordered_records(records, schema)
    jsonl = "".join(canonical_json(record) + "\n" for record in ordered).encode("utf-8")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(schema["csv_columns"])
    for record in ordered:
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)])
    return jsonl, buffer.getvalue().encode("utf-8")


def assert_baseline_preserved(output_jsonl: bytes, output_csv: bytes, baseline_jsonl: bytes, baseline_csv: bytes) -> None:
    if strip_workflow_jsonl(output_jsonl) != baseline_jsonl:
        raise ValueError("generated JSONL changes baseline record bytes or relative order")
    if strip_workflow_csv(output_csv) != baseline_csv:
        raise ValueError("generated CSV changes baseline row bytes or relative order")


def atomic_write(path: Path, data: bytes, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}.{label}-", suffix=".stage", dir=path.parent, delete=False) as handle:
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


def atomic_write_pair(output_jsonl: Path, output_csv: Path, jsonl: bytes, csv_data: bytes) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    try:
        for destination, data in ((output_jsonl, jsonl), (output_csv, csv_data)):
            with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{destination.name}.becker-b03-", suffix=".stage", dir=destination.parent, delete=False) as handle:
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


def make_result(mode: str, new_records: list[dict[str, Any]], all_records: list[dict[str, Any]], jsonl: bytes, csv_data: bytes, schema: dict[str, Any], output_jsonl: Path | None, output_csv: Path | None) -> dict[str, Any]:
    ordered = ordered_records(all_records, schema)
    present = [record for record in new_records if record["entity_type"] == "learning_surface" and record.get("presence") == "present"]
    target_size, target_digest = file_info(TARGET)
    return {
        "schema": "o015-becker-03-backend-extension-receipt-v1",
        "result": "pass",
        "workflow": WORKFLOW,
        "write_mode": mode,
        "namespace": f"{BASE}.*",
        "collision_count": 0,
        "schema_identity": {"bytes": SCHEMA_IDENTITY[0], "sha256": SCHEMA_IDENTITY[1], "schema_changed": False},
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
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
        "new_id_set_sha256": id_set_sha256(new_records),
        "new_record_set_sha256": record_set_sha256(new_records),
        "final_record_count": len(all_records),
        "final_id_set_sha256": id_set_sha256(all_records),
        "final_id_order_sha256": id_order_sha256(ordered),
        "final_record_set_sha256": record_set_sha256(all_records),
        "jsonl": {"bytes": len(jsonl), "sha256": sha256(jsonl)},
        "csv": {"bytes": len(csv_data), "sha256": sha256(csv_data)},
        "source_commit": COMMIT,
        "source_range": {"first_line": 2971, "last_line": 2988, "line_count": 18, "bytes": SOURCE_SLICE_IDENTITY[0], "sha256": SOURCE_SLICE_IDENTITY[1]},
        "target": {"path": TARGET, "bytes": target_size, "sha256": target_digest, "physical_lines": len((ROOT / TARGET).read_text(encoding="utf-8").splitlines())},
        "segment_count": len(SEGMENT_SPECS),
        "topic_count": len(TOPIC_SPECS),
        "present_surface_counts": dict(sorted(Counter(record["surface_type"] for record in present).items())),
        "source_absence_closure_count": len(SOURCE_ABSENT_SURFACES),
        "output_jsonl": output_jsonl.relative_to(ROOT).as_posix() if output_jsonl and output_jsonl.is_relative_to(ROOT) else str(output_jsonl) if output_jsonl else None,
        "output_csv": output_csv.relative_to(ROOT).as_posix() if output_csv and output_csv.is_relative_to(ROOT) else str(output_csv) if output_csv else None,
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

    schema = assert_schema_identity()
    evidence = validate_final_evidence()
    baseline, baseline_jsonl, baseline_csv = load_baseline(args.input_jsonl, args.input_csv)
    new_records = generate_records(baseline, evidence, schema)
    all_records = baseline + new_records
    jsonl, csv_data = serialize(all_records, schema)
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

    result = make_result(mode, new_records, all_records, jsonl, csv_data, schema, output_jsonl, output_csv)
    if args.write_canonical:
        payload = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        atomic_write(RECEIPT_PATH, payload, "receipt")
        if RECEIPT_PATH.read_bytes() != payload:
            raise ValueError("canonical receipt readback differs")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
