#!/usr/bin/env python3
"""Deterministically add MIT 6.253 Lecture 7 (pages 86-97) to the backend.

The admitted 2,324-record L10 backend is byte protected.  Re-running this
tool removes only records owned by ``o015-mit-l11-backend-v1``, reconstructs
the exact protected baseline, regenerates the L11 projection, and proves that
every pre-existing record retains its canonical bytes and relative order.
Canonical replacement occurs only with ``--write-canonical``.
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

RECORDED_AT = "2026-08-24T19:00:00Z"
WORKFLOW = "o015-mit-l11-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 2_324
BASELINE_JSONL = (1_797_378, "d8694c14afa0933132504c32ea6e2e5862606f913d4b6626bffd35b2bfbee75c")
BASELINE_CSV = (2_144_290, "fb9c84063bf976ddf5e2e15f435617c1cca346eebfd08051d9927a34ffcba367")
BASELINE_ID_SET_SHA256 = "47e46b474fa854ecfc4adbc658c0fa1d6e449f4c6aefa2e1284c1f9807d9c108"
BASELINE_ID_ORDER_SHA256 = "d8dd895a08136ab98001076b59de2312881b6610dc3f50b7cceb4368dc940de2"
BASELINE_RECORD_SET_SHA256 = "a7c2de2ad5f362e40b026d905ce90fc8117095ed40c2a1f12a0a36767a698675"
BASELINE_RECORD_LINE_SEQUENCE_SHA256 = "53ab04d6956ec2f08977e914e8cd92ce5d3576985b8f8de8ff8d341c608239c4"

EXPECTED_NEW_RECORD_COUNT = 148
EXPECTED_ENTITY_COUNTS = Counter({
    "unit": 1,
    "segment": 12,
    "learning_surface": 32,
    "correction": 10,
    "artifact": 19,
    "qa_event": 17,
    "relation": 57,
})

MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L11_UNIT_ID = "unit.mit.ocw-6.253.l11"
SOURCE_PAGES = list(range(86, 98))

PAGE_ITEMS = {86: 6, 87: 3, 88: 3, 89: 4, 90: 4, 91: 2,
              92: 1, 93: 5, 94: 1, 95: 1, 96: 3, 97: 3}
PAGE_NESTED = {86: 1, 87: 0, 88: 1, 89: 0, 90: 3, 91: 0,
               92: 1, 93: 0, 94: 0, 95: 0, 96: 0, 97: 2}
PAGE_DISPLAYS = {86: 0, 87: 1, 88: 2, 89: 0, 90: 1, 91: 2,
                 92: 1, 93: 3, 94: 2, 95: 4, 96: 1, 97: 4}
PAGE_TITLES = {
    86: "Lecture 7 outline",
    87: "additional separation theorems",
    88: "proper polyhedral separation",
    89: "nonvertical hyperplanes",
    90: "nonvertical hyperplane theorem",
    91: "conjugate convex functions",
    92: "conjugate examples",
    93: "conjugate of the conjugate",
    94: "conjugacy theorem visualization",
    95: "conjugacy theorem",
    96: "proof of the conjugacy theorem",
    97: "improper-function counterexample",
}

# (source page, figure index) -> (panel count, semantic label)
FIGURES = {
    (87, 1): (3, "proper-separation configurations"),
    (88, 1): (2, "polyhedral versus smooth proper separation"),
    (89, 1): (2, "nonvertical and vertical hyperplanes"),
    (91, 1): (1, "supporting lower bound and conjugate intercept"),
    (92, 1): (6, "three function-and-conjugate example pairs"),
    (94, 1): (1, "conjugacy and biconjugate envelope geometry"),
    (96, 1): (1, "strict-separator proof geometry with corrected intercept signs"),
}

# record suffix -> (page, source anchor suffix, label, optional panel)
EXAMPLES = {
    "p092.f001.a": (92, "f001", "affine function and point-supported conjugate", "a"),
    "p092.f001.b": (92, "f001", "absolute value and interval-indicator conjugate", "b"),
    "p092.f001.c": (92, "f001", "positive quadratic and reciprocal-curvature conjugate", "c"),
    "p097": (97, None, "closed convex improper-function counterexample", None),
}
WORKED_EXAMPLE_SUFFIXES = tuple(suffix for suffix in EXAMPLES if suffix != "p097")
COUNTEREXAMPLE_SUFFIXES = ("p097",)

MIT_PDF = "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
MIT_CENSUS = "00_control/MIT_L11_LECTURE_7_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/MIT_L11_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-11-lecture-7-separation-conjugacy-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-11-kuliah-7-pemisahan-dan-konjugasi-id.md"
MIT_HTML = "output/html/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.pdf"
MIT_CSS = "source/id-ID/mit-l11.css"
MIT_PREAMBLE = "source/id-ID/mit-l11-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l11-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l11-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l11-after-body.html"
MIT_BUILDER = "qa/build_mit_l11.py"
MIT_VALIDATOR = "qa/validate_mit_l11.py"
MIT_REPORT = "qa/MIT_L11_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L11_BROWSER_QA.json"
MIT_VISUAL_QA = "qa/MIT_L11_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L11_INDEPENDENT_REREVIEW.md"
MIT_BACKEND_GENERATOR = "qa/extend_backend_mit_l11.py"
MIT_BACKEND_VALIDATOR = "qa/validate_backend_mit_l11.py"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
CENSUS_IDENTITY = (5_840, "6586e3feb4463da884027c778a70c0f066b48d2948c38d1ba9a80ebde98c6f6a")
LEDGER_IDENTITY = (15_532, "8acc411765e4d5e29f9e89447c26f2b37f00110d43ac2b0043c0762ed070a016")
WITNESS_IDENTITY = (23_801, "625efb8801d24c270d2bf851bf1c7fb27cb307146742d7cbddc00b5cb5873c8c")
TARGET_IDENTITY = (25_023, "f908901609e1a1e6091734b55ba63b980f491dd5a5e4e813621816cbceb1c32b")
HTML_IDENTITY = (96_216, "19dd1f9aeb65e951089a4501fefa65761448f86f21ee7024ccfde9a71e5b988d")
PDF_IDENTITY = (89_771, "82d39fa34f8e743204ba88b3b91f50d4a549bb7b0b79e529ed0bec1a51f16bc8")

CANONICAL_BUILD_COMMAND = (
    "python qa/build_mit_l11.py --html-output "
    "output/html/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.html "
    "--pdf-output output/pdf/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.pdf"
)
RECEIPT_BUILD_COMMAND = "python qa/build_mit_l11.py --html-output <html> --pdf-output <pdf>"
EXPECTED_EVENT_IDS = (
    "O015-MIT-SEM-0034", "O015-MIT-SEM-0035", "O015-MIT-SEM-0036",
    "O015-MIT-SEM-0037", "O015-MIT-SEM-0040", "O015-MIT-SEM-0031",
    "O015-MIT-SEM-0038", "O015-MIT-SEM-0039", "O015-MIT-SEM-0032",
    "O015-MIT-SEM-0033",
)
CORRECTION_SPECS = {
    "O015-MIT-SEM-0034": ([88], "unwarranted nonpolyhedral description"),
    "O015-MIT-SEM-0035": ([89], "ambiguous vertical-line phrase"),
    "O015-MIT-SEM-0036": ([90], "suppressed epsilon sign and margin argument"),
    "O015-MIT-SEM-0037": ([91], "supporting terminology without attainment"),
    "O015-MIT-SEM-0040": ([91, 95], "function-type mapsto arrows"),
    "O015-MIT-SEM-0031": ([92], "missing positive quadratic parameter assumption"),
    "O015-MIT-SEM-0038": ([93], "affine functions called linear"),
    "O015-MIT-SEM-0039": ([94], "visual general-case ambiguity"),
    "O015-MIT-SEM-0032": ([96], "sign-defective geometric proof"),
    "O015-MIT-SEM-0033": ([97], "scalar-vector domain and codomain mismatch"),
}

# Tool-specific authority page witnesses, produced one page per invocation with
# Poppler pdftotext 24.04.0 (-layout -enc UTF-8) and MuPDF mutool 1.23.0
# (draw -F png -c gray -r 96).  The whole-PDF identity remains authoritative.
PAGE_FINGERPRINTS = {
    86: (258, "5bb20e6003c022244d8baeae9365ca1e85571b9021b7ebbca76bfb0068ac4288", 21720, "3480b3e1a2f9ea11078d7ffd2f1ccf2191bfb27d6d841a69f83b1148db65621b"),
    87: (934, "6d34b9c20adbcab3d9b94f51255e380495c884082496d49333063ffa56b0d7a6", 55190, "53d6d945b1e3af1eeb2b5df192c6b704ae9e245af3ff38fba06275bd44ae39c2"),
    88: (918, "2f2b8d01a7f09944b217e000a71b24dd0b77258159ef40a5f697dbd5eaa16fe4", 56877, "b1a6de188dc858109ba12085ede619102f0d614c6d4d8c7e81394a3efd90673c"),
    89: (980, "7a386ae891bcf77999b700d0561b5d9b05b61ddc2742c5aeeaf6ec6a7d3597ff", 53769, "3a5e327f3168ba8bd85897d1dc7f039e210dda04e2c8d4b5eb9968779a7c41f9"),
    90: (1148, "f998269d35b74761acae48995eaf7e10c461e1b7d030105a3c3fea2a8465d7b1", 63453, "9392b6c8521fa7960f5e348f8c6bbd37aa58006da6a61a7e0cf698430dc5de68"),
    91: (871, "21fec334f9e91b1d6b25fe29c80078d1c650ca0dbb05e6696e2065b8b101f70e", 53802, "299ffc0691979d1824087c34a65262f07f9db9263e6a254e19af0bcc90f77363"),
    92: (1150, "f670d867bbc0bcf5f2fb85148b6aef06f5d32961c8ab1985d392e2d59a006f47", 28991, "4a2bbf0954ab94323206933be26df53658bad4a5ec450bea4a33d54f261622d5"),
    93: (740, "7abcde78433beca5672e4b117c096e3a69cd8e9a4f0d37705b6c3f380dd83bca", 40704, "fdd9898e0004ab7d56a0269594f11431210755b03e1cdec7caf38f449f100d18"),
    94: (1185, "e09d900a215c55ae6f3b96f1b66d312c0b73fc372df5908cbaf6ab0cc09701c4", 46386, "f878f160f7ffd7c785717e9ae1b0a72a2d44b5253bee4b9111b2bda3c589a8df"),
    95: (841, "77d25710689b28c92637366a852b0adc2a9dd1cbaefd60675961a4f3cbecfa11", 41463, "5822f46c0b24d0e95027d2801ed1f113d49e38c7a7061dbc00b6833648822fef"),
    96: (1370, "d9768a6d5c70120083db44722b2430942a6bfcded41baa053bd58dbc0cb59f0e", 63569, "133117e2352bf96a9c27f70860ecf2469f892e39a70caa50bbda7518c2c0831d"),
    97: (539, "d91b7761241b77874e9a3b2a85b8e702a068a0583b70946f52ad64089ff53c1f", 24306, "0c93aa07834281be7c97375459816817a479cf21c1a6a8a6688428057fb9cffb"),
    98: (247, "089e122ba925acf0cb958abb5cc7a1949a0074e421f1317d94d5567e07a53247", 20783, "3770e1e76f47890c521590681468d186498501f39ddc0e8195a2bfd261b1bc3d"),
}


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    data = path.read_bytes()
    return len(data), sha256(data)


def id_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "\n".join(sorted(record["id"] for record in records)) + "\n"
    return sha256(payload.encode("utf-8"))


def id_order_sha256(records: list[dict[str, Any]]) -> str:
    payload = "\n".join(record["id"] for record in records) + "\n"
    return sha256(payload.encode("utf-8"))


def record_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "".join(
        canonical_json(record) + "\n" for record in sorted(records, key=lambda item: item["id"])
    )
    return sha256(payload.encode("utf-8"))


def record_line_sequence_sha256(raw: bytes) -> str:
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


def artifact(record_id: str, kind: str, path: str, rights_id: str, **extra: Any) -> dict[str, Any]:
    size, digest = file_info(path)
    record = common("artifact", record_id, "current")
    record.update({
        "artifact_kind": kind,
        "path": path,
        "bytes": size,
        "sha256": digest,
        "hash_algorithm": "sha256-raw-bytes",
        "rights_id": rights_id,
        **extra,
    })
    return record


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.strip().startswith("::: {") and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
    ]
    if len(starts) != 1:
        raise ValueError(f"expected one fenced div #{anchor} in {relative}, found {len(starts)}")
    start = starts[0]
    depth = 0
    end = -1
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("::: {"):
            depth += 1
        elif stripped == ":::":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end < start:
        raise ValueError(f"unclosed fenced div #{anchor} in {relative}")
    payload = ("\n".join(lines[start:end + 1]) + "\n").encode("utf-8")
    return start + 1, end + 1, len(payload), sha256(payload)


def strip_workflow_jsonl(raw: bytes) -> bytes:
    return b"".join(
        line for line in raw.splitlines(keepends=True)
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


def assert_raw_baseline(jsonl_bytes: bytes, csv_bytes: bytes, context: str) -> None:
    if (len(jsonl_bytes), sha256(jsonl_bytes)) != BASELINE_JSONL:
        raise ValueError(f"{context} JSONL is not the protected 2,099-record baseline")
    if (len(csv_bytes), sha256(csv_bytes)) != BASELINE_CSV:
        raise ValueError(f"{context} CSV is not the protected 2,099-record baseline")
    if record_line_sequence_sha256(jsonl_bytes) != BASELINE_RECORD_LINE_SEQUENCE_SHA256:
        raise ValueError(f"{context} record-line byte sequence differs")


def load_baseline(input_jsonl: Path, input_csv: Path) -> tuple[list[dict[str, Any]], bytes, bytes]:
    incoming_jsonl = input_jsonl.read_bytes()
    incoming_csv = input_csv.read_bytes()
    incoming_records = [json.loads(line) for line in incoming_jsonl.decode("utf-8").splitlines() if line]
    rows = list(csv.DictReader(io.StringIO(incoming_csv.decode("utf-8", errors="strict"))))
    if [json.loads(row["record_json"]) for row in rows] != incoming_records:
        raise ValueError("incoming CSV projection differs from JSONL")
    if len({record["id"] for record in incoming_records}) != len(incoming_records):
        raise ValueError("incoming backend has duplicate IDs")
    baseline = [record for record in incoming_records if record.get("responsible_workflow") != WORKFLOW]
    stripped_jsonl = strip_workflow_jsonl(incoming_jsonl)
    stripped_csv = strip_workflow_csv(incoming_csv)
    assert_raw_baseline(stripped_jsonl, stripped_csv, "workflow-stripped incoming")
    if (
        len(baseline) != BASELINE_RECORD_COUNT
        or id_set_sha256(baseline) != BASELINE_ID_SET_SHA256
        or id_order_sha256(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set_sha256(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("stripped record set/order differs from the protected L10 baseline")
    return baseline, stripped_jsonl, stripped_csv


def parse_census_fingerprints() -> dict[int, tuple[int, str, int, str]]:
    if file_info(MIT_CENSUS) != CENSUS_IDENTITY:
        raise ValueError("L11 boundary census identity differs")
    census = (ROOT / MIT_CENSUS).read_text(encoding="utf-8")
    required = (
        "pages 86-97 inclusive", "page 98 begins `LECTURE 8 / LECTURE OUTLINE`",
        "| **Total** | **12 source pages** | **28** | **21** | **7** | **16** |",
        SOURCE_PDF_IDENTITY[1],
    )
    if any(fragment not in census for fragment in required):
        raise ValueError("L11 census boundary/topology statement differs")
    if set(PAGE_FINGERPRINTS) != set(range(86, 99)):
        raise ValueError("L11 authority page-fingerprint set differs")
    return dict(PAGE_FINGERPRINTS)


def ledger_events() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if file_info(MIT_LEDGER) != LEDGER_IDENTITY:
        raise ValueError("L11 correction snapshot identity differs")
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), start=1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id not in EXPECTED_EVENT_IDS or event_id in result:
            raise ValueError(f"unexpected or duplicate L11 correction event: {event_id}")
        required = {
            "authority", "authority_file", "source", "witness", "target", "surface",
            "source_issue", "target_action", "class", "project_authorship", "rights",
        }
        if any(not event.get(field) for field in required):
            raise ValueError(f"{event_id} lacks required correction evidence")
        newline = "crlf" if raw_line.endswith(b"\r\n") else "lf" if raw_line.endswith(b"\n") else "none"
        binding = {
            "ledger_path": MIT_LEDGER,
            "raw_line_start": line_number,
            "raw_line_end": line_number,
            "raw_line_bytes": len(raw_line),
            "raw_line_sha256": sha256(raw_line),
            "raw_line_newline": newline,
            "canonical_event_sha256": sha256(canonical_json(event).encode("utf-8")),
        }
        result[event_id] = (event, binding)
    if tuple(result) != EXPECTED_EVENT_IDS:
        raise ValueError("L11 correction event set differs")
    return result


def identity_tuple(record: dict[str, Any]) -> tuple[int, str]:
    return int(record.get("bytes", -1)), str(record.get("sha256", ""))


def validate_source_topology() -> dict[str, Any]:
    if file_info(MIT_PDF) != SOURCE_PDF_IDENTITY:
        raise ValueError("MIT authority PDF identity differs")
    if file_info(MIT_WITNESS) != WITNESS_IDENTITY or file_info(MIT_TARGET) != TARGET_IDENTITY:
        raise ValueError("L11 canonical semantic-source identity differs")
    expected_pages = {f"d90-mit-l11-p{page:03d}" for page in SOURCE_PAGES}
    expected_items = {
        f"d90-mit-l11-p{page:03d}-i{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)
    }
    expected_displays = {
        f"d90-mit-l11-p{page:03d}-d{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    }
    expected_figures = {
        f"d90-mit-l11-p{page:03d}-f{index:03d}" for page, index in FIGURES
    }
    patterns = {
        "pages": re.compile(r"^::: \{\.source-page #(d90-mit-l11-p\d{3})\b", re.M),
        "items": re.compile(r"^::: \{\.source-item #(d90-mit-l11-p\d{3}-i\d{3})\b", re.M),
        "displays": re.compile(r"^\s*::: \{\.source-display #(d90-mit-l11-p\d{3}-d\d{3})\b", re.M),
        "figures": re.compile(r"^::: \{\.source-figure #(d90-mit-l11-p\d{3}-f\d{3})\b", re.M),
    }
    expected = {
        "pages": expected_pages, "items": expected_items,
        "displays": expected_displays, "figures": expected_figures,
    }
    for relative in (MIT_WITNESS, MIT_TARGET):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for name, pattern in patterns.items():
            found = pattern.findall(text)
            if len(found) != len(set(found)) or set(found) != expected[name]:
                raise ValueError(f"{relative} {name} topology differs")
    return {
        "pages": len(expected_pages), "items": len(expected_items),
        "displays": len(expected_displays), "figures": len(expected_figures),
        "panels": sum(value[0] for value in FIGURES.values()),
    }


def load_reader_evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if file_info(MIT_HTML) != HTML_IDENTITY or file_info(MIT_READER_PDF) != PDF_IDENTITY:
        raise ValueError("L11 deterministic reader identity differs")
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    visual = json.loads((ROOT / MIT_VISUAL_QA).read_text(encoding="utf-8"))
    boundary = report.get("boundary", {})
    expected_boundary = {
        "source_pdf_pages": SOURCE_PAGES, "source_pages": 12,
        "next_source_page": 98, "next_heading": "LECTURE 8 - LECTURE OUTLINE",
        "source_items": 36, "source_display_wrappers": 21,
        "display_formula_blocks": 21, "source_figures": 7,
        "source_figure_panels": 16, "copied_source_graphics": 0,
        "exercises": 0, "hints": 0, "answers": 0, "solutions": 0,
        "code_surfaces": 0, "interactive_surfaces": 0,
    }
    if (
        report.get("result") != "pass" or report.get("errors") not in ([], None)
        or report.get("stage") != "strict-final" or report.get("release_ready") is not True
        or boundary != expected_boundary
    ):
        raise ValueError("L11 validation receipt boundary is not a strict pass")
    if report.get("model_identification") != "OpenAI Codex gpt-5.6-sol, Ultra":
        raise ValueError("L11 model identification differs")
    formulas = report.get("formula_inventory", {})
    if formulas.get("witness", {}).get("display_blocks") != 21 or formulas.get("target", {}).get("display_blocks") != 21:
        raise ValueError("L11 formula inventory differs")
    build = report.get("build", {})
    expected_reader = {"html": list(HTML_IDENTITY), "pdf": list(PDF_IDENTITY)}
    if (
        build.get("command") != RECEIPT_BUILD_COMMAND
        or build.get("deterministic_rebuilds") != 2
        or build.get("expected") != expected_reader
        or build.get("rebuild_identities") != [expected_reader, expected_reader]
    ):
        raise ValueError("L11 deterministic build evidence differs")
    if identity_tuple(build.get("canonical", {}).get("html", {})) != HTML_IDENTITY or identity_tuple(build.get("canonical", {}).get("pdf", {})) != PDF_IDENTITY:
        raise ValueError("L11 canonical reader binding differs")
    html = report.get("html", {})
    if any(html.get(name) != value for name, value in {
        "lang": "id-ID", "source_pages": 12, "source_items": 36,
        "source_displays": 21, "source_figures": 7,
        "display_math_nodes": 21, "images": 0, "media_or_embeds": 0,
        "form_controls": 0, "duplicate_ids": [], "unresolved_fragments": [],
    }.items()):
        raise ValueError("L11 HTML topology differs")
    pdf = report.get("pdf", {})
    if (
        pdf.get("pages") != 6
        or pdf.get("searchable_text_chars") != 12048
        or pdf.get("searchable_chars_per_page")
        != [1830, 2404, 3318, 1618, 2090, 788]
        or pdf.get("to_unicode_all_fonts") is not True
        or pdf.get("images") != 0
        or pdf.get("encrypted") is not False
    ):
        raise ValueError("L11 PDF topology differs")
    if browser.get("result") != "pass" or identity_tuple(browser.get("artifact", {})) != HTML_IDENTITY:
        raise ValueError("L11 browser evidence differs")
    if visual.get("result") != "pass" or identity_tuple(visual.get("artifact", {})) != PDF_IDENTITY:
        raise ValueError("L11 visual evidence differs")
    rendered_pages = [entry.get("page") for entry in visual.get("render", {}).get("pages", [])]
    if rendered_pages != list(range(1, 7)):
        raise ValueError("L11 visual evidence does not cover every reader page")
    rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
    if "Independent rereview result: PASS" not in rereview:
        raise ValueError("L11 independent rereview disposition differs")
    for digest in (WITNESS_IDENTITY[1], TARGET_IDENTITY[1]):
        if digest not in rereview:
            raise ValueError("L11 independent rereview binds stale canonical bytes")
    return report, browser, visual


def expected_ids() -> set[str]:
    result = {MIT_L11_UNIT_ID}
    result.update(f"d90.mit.ocw-6.253.l11.p{page:03d}" for page in SOURCE_PAGES)
    result.update(
        f"surface.mit.l11.formula.p{page:03d}.d{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    )
    result.update(
        f"surface.mit.l11.figure-description.p{page:03d}.f{index:03d}"
        for page, index in FIGURES
    )
    result.update(f"surface.mit.l11.example.{suffix}" for suffix in EXAMPLES)
    result.update(f"correction.{event_id.lower()}" for event_id in EXPECTED_EVENT_IDS)
    result.update({
        "artifact.mit.l11.boundary-census", "artifact.mit.l11.semantic-witness",
        "artifact.mit.l11.target-source", "artifact.mit.l11.target-html",
        "artifact.mit.l11.target-pdf", "artifact.mit.l11.builder",
        "artifact.mit.l11.validator", "artifact.mit.l11.validation",
        "artifact.mit.l11.browser-qa", "artifact.mit.l11.visual-qa",
        "artifact.mit.l11.independent-rereview", "artifact.mit.l11.correction-snapshot",
        "artifact.mit.l11.css", "artifact.mit.l11.pdf-preamble",
        "artifact.mit.l11.pdf-filter", "artifact.mit.l11.before-body",
        "artifact.mit.l11.after-body", "artifact.o015.backend-generator-mit-l11",
        "artifact.o015.backend-validator-mit-l11",
    })
    qa_suffixes = {
        "source-freeze", "semantic-reconstruction", "topology", "formulas", "figures",
        "corrections", "build", "html", "browser", "pdf", "visual",
        "semantic-rereview", "accessibility", "language", "rights",
        "csv-losslessness", "backend-integration",
    }
    result.update(f"qa.o015.mit-l11.{suffix}" for suffix in qa_suffixes)
    core_relations = {
        "work-contains-l11", "witness-edition-contains-l11", "target-edition-contains-l11",
        "l10-precedes-l11", "witness-adapts-authority-pdf-l11",
        "target-translates-witness-l11", "html-adapts-target-l11",
        "pdf-adapts-target-l11", "browser-qa-depends-on-html-l11",
        "visual-qa-depends-on-pdf-l11", "validation-depends-on-browser-qa-l11",
        "validation-depends-on-visual-qa-l11", "rereview-depends-on-target-l11",
    }
    result.update(f"relation.mit.{suffix}" for suffix in core_relations)
    result.update(f"relation.mit.l11-contains-p{page:03d}" for page in SOURCE_PAGES)
    result.update(
        f"relation.mit.l11-formula-p{page:03d}-d{index:03d}-illustrates-segment"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    )
    result.update(
        f"relation.mit.l11-figure-p{page:03d}-f{index:03d}-illustrates-segment"
        for page, index in FIGURES
    )
    result.update(
        f"relation.mit.l11-example-{suffix.replace('.', '-')}-exercises-segment"
        for suffix in EXAMPLES
    )
    return result


def static_preflight(input_jsonl: Path, input_csv: Path) -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema" or "precedes" not in schema.get("relation_types", []):
        raise ValueError("backend schema does not admit the additive precedes relation")
    baseline, _, _ = load_baseline(input_jsonl, input_csv)
    topology = validate_source_topology()
    parse_census_fingerprints()
    events = ledger_events()
    ids = expected_ids()
    if len(ids) != EXPECTED_NEW_RECORD_COUNT:
        raise ValueError(f"static L11 ID contract has {len(ids)} IDs, expected {EXPECTED_NEW_RECORD_COUNT}")
    collisions = sorted(ids & {record["id"] for record in baseline})
    if collisions:
        raise ValueError(f"L11 stable-ID collisions: {collisions}")
    return {
        "result": "pass", "workflow": WORKFLOW,
        "protected_baseline_record_count": len(baseline),
        "expected_new_record_count": len(ids),
        "expected_final_record_count": len(baseline) + len(ids),
        "source_pages": SOURCE_PAGES, "topology": topology,
        "corrections": len(events),
        "new_id_set_sha256": sha256(("\n".join(sorted(ids)) + "\n").encode("utf-8")),
    }


def generate_records(
    baseline: list[dict[str, Any]], report: dict[str, Any],
    browser: dict[str, Any], visual: dict[str, Any],
    events: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    fingerprints: dict[int, tuple[int, str, int, str]],
) -> list[dict[str, Any]]:
    baseline_ids = {record["id"] for record in baseline}
    new_records: list[dict[str, Any]] = []
    new_ids: set[str] = set()

    def add(record: dict[str, Any]) -> None:
        if record["id"] in baseline_ids or record["id"] in new_ids:
            raise ValueError(f"stable-ID collision: {record['id']}")
        new_ids.add(record["id"])
        new_records.append(record)

    segment_ids = {page: f"d90.mit.ocw-6.253.l11.p{page:03d}" for page in SOURCE_PAGES}
    item_ids = [
        f"d90-mit-l11-p{page:03d}-i{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)
    ]
    display_pairs = [
        (page, index) for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    ]
    figure_pairs = list(FIGURES)
    html = report["html"]
    pdf = report["pdf"]

    unit = common("unit", MIT_L11_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 11,
        "source_local_id": "lecture-7-pages-86-97",
        "source_local_label": "Lecture 7 - Separation, Nonvertical Hyperplanes, and Conjugacy",
        "target_local_label": "Kuliah 7 - Pemisahan, Hiperbidang Nonvertikal, dan Konjugasi",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": SOURCE_PAGES,
        "next_source_page": 98,
        "next_source_heading": "LECTURE 8 - LECTURE OUTLINE",
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 36,
        "nested_source_item_count": 8,
        "source_item_ids": item_ids,
        "target_item_ids": item_ids,
        "source_display_count": 21,
        "source_display_ids": [f"d90-mit-l11-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "target_display_ids": [f"d90-mit-l11-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "source_figure_count": 7,
        "source_figure_ids": [f"d90-mit-l11-p{page:03d}-f{index:03d}" for page, index in figure_pairs],
        "target_figure_ids": [f"d90-mit-l11-p{page:03d}-f{index:03d}" for page, index in figure_pairs],
        "source_figure_panel_count": 16,
        "worked_example_count": len(WORKED_EXAMPLE_SUFFIXES),
        "worked_example_ids": [f"surface.mit.l11.example.{suffix}" for suffix in WORKED_EXAMPLE_SUFFIXES],
        "counterexample_count": len(COUNTEREXAMPLE_SUFFIXES),
        "counterexample_ids": [f"surface.mit.l11.example.{suffix}" for suffix in COUNTEREXAMPLE_SUFFIXES],
        "exercise_count": 0, "hint_count": 0, "answer_count": 0,
        "solution_count": 0, "code_surface_count": 0,
        "interactive_surface_count": 0, "copied_source_graphics": 0,
        "correction_event_ids": list(EXPECTED_EVENT_IDS),
        "canonical_build_command": CANONICAL_BUILD_COMMAND,
    })
    add(unit)

    for order, page in enumerate(SOURCE_PAGES, start=1):
        anchor = f"d90-mit-l11-p{page:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        text_bytes, text_hash, render_bytes, render_hash = fingerprints[page]
        figures_on_page = [(index, FIGURES[(page, index)]) for p, index in figure_pairs if p == page]
        record = common("segment", segment_ids[page], "visually_checked")
        record.update({
            "unit_id": MIT_L11_UNIT_ID, "order": order,
            "source_edition_id": MIT_WITNESS_EDITION_ID,
            "target_edition_id": MIT_TARGET_EDITION_ID,
            "source_path": MIT_WITNESS, "source_line_start": source_slice[0],
            "source_line_end": source_slice[1], "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3], "source_anchor": anchor,
            "source_item_ids": [f"{anchor}-i{index:03d}" for index in range(1, PAGE_ITEMS[page] + 1)],
            "target_path": MIT_TARGET, "target_line_start": target_slice[0],
            "target_line_end": target_slice[1], "target_bytes": target_slice[2],
            "target_content_sha256": target_slice[3], "target_anchor": anchor,
            "target_item_ids": [f"{anchor}-i{index:03d}" for index in range(1, PAGE_ITEMS[page] + 1)],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "visually_checked", "rights_id": "rights.o015-mit-id-pilot",
            "source_pdf_path": MIT_PDF, "source_pdf_page": page,
            "source_pdf_sha256": SOURCE_PDF_IDENTITY[1], "source_pdf_pages_total": 340,
            "source_page_text_bytes": text_bytes, "source_page_text_sha256": text_hash,
            "source_page_render_bytes": render_bytes, "source_page_render_sha256": render_hash,
            "source_page_render_method": "MuPDF mutool 1.23.0 draw -F png -c gray -r 96",
            "source_item_count": PAGE_ITEMS[page],
            "nested_source_item_count": PAGE_NESTED[page],
            "source_display_count": PAGE_DISPLAYS[page],
            "source_figure_count": len(figures_on_page),
            "source_figure_panel_count": sum(spec[0] for _, spec in figures_on_page),
            "worked_example_count": sum(1 for suffix in WORKED_EXAMPLE_SUFFIXES if EXAMPLES[suffix][0] == page),
            "counterexample_count": sum(1 for suffix in COUNTEREXAMPLE_SUFFIXES if EXAMPLES[suffix][0] == page),
            "anchor_mapping_rule": "identical d90-mit-l11 stable anchor preserved from witness to target",
        })
        add(record)

    for global_order, (page, index) in enumerate(display_pairs, start=1):
        anchor = f"d90-mit-l11-p{page:03d}-d{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l11.formula.p{page:03d}.d{index:03d}", "present")
        record.update({
            "unit_id": MIT_L11_UNIT_ID, "surface_type": "display_formula", "presence": "present",
            "formula_sequence_order": global_order, "page_formula_order": index,
            "formula_label": f"{PAGE_TITLES[page]}: display {index}",
            "source_pdf_page": page, "related_segment_ids": [segment_ids[page]],
            "source_path": MIT_WITNESS, "source_anchor": anchor,
            "source_line_start": source_slice[0], "source_line_end": source_slice[1],
            "source_bytes": source_slice[2], "source_content_sha256": source_slice[3],
            "target_path": MIT_TARGET, "target_anchor": anchor,
            "target_line_start": target_slice[0], "target_line_end": target_slice[1],
            "target_bytes": target_slice[2], "target_content_sha256": target_slice[3],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "formula_sequence_match": True, "rights_id": "rights.o015-mit-id-pilot",
        })
        add(record)

    for page, index in figure_pairs:
        panels, label = FIGURES[(page, index)]
        anchor = f"d90-mit-l11-p{page:03d}-f{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l11.figure-description.p{page:03d}.f{index:03d}", "present_with_limitation")
        record.update({
            "unit_id": MIT_L11_UNIT_ID, "surface_type": "semantic_figure_description",
            "presence": "present_with_limitation", "figure_label": label,
            "source_pdf_page": page, "panel_count": panels,
            "related_segment_ids": [segment_ids[page]],
            "source_path": MIT_WITNESS, "source_anchor": anchor,
            "source_line_start": source_slice[0], "source_line_end": source_slice[1],
            "source_bytes": source_slice[2], "source_content_sha256": source_slice[3],
            "target_path": MIT_TARGET, "target_anchor": anchor,
            "target_line_start": target_slice[0], "target_line_end": target_slice[1],
            "target_bytes": target_slice[2], "target_content_sha256": target_slice[3],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "source_graphic_disposition": "omitted-source-graphic",
            "semantic_description_preserved": True, "copied_source_graphic_bytes": 0,
            "rights_id": "rights.o015-mit-id-pilot",
        })
        add(record)

    for sequence_order, (suffix, (page, anchor_suffix, label, panel)) in enumerate(EXAMPLES.items(), start=1):
        anchor = (
            f"d90-mit-l11-p{page:03d}"
            if anchor_suffix is None else f"d90-mit-l11-p{page:03d}-{anchor_suffix}"
        )
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l11.example.{suffix}", "present")
        record.update({
            "unit_id": MIT_L11_UNIT_ID,
            "surface_type": "counterexample" if suffix in COUNTEREXAMPLE_SUFFIXES else "worked_example",
            "presence": "present",
            "example_sequence_order": sequence_order, "example_label": label,
            "source_pdf_page": page, "related_segment_ids": [segment_ids[page]],
            "source_path": MIT_WITNESS, "source_anchor": anchor,
            "source_line_start": source_slice[0], "source_line_end": source_slice[1],
            "source_bytes": source_slice[2], "source_content_sha256": source_slice[3],
            "target_path": MIT_TARGET, "target_anchor": anchor,
            "target_line_start": target_slice[0], "target_line_end": target_slice[1],
            "target_bytes": target_slice[2], "target_content_sha256": target_slice[3],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "rights_id": "rights.o015-mit-id-pilot",
        })
        if panel is not None:
            record["source_figure_panel"] = panel
        add(record)

    for event_id in EXPECTED_EVENT_IDS:
        event, binding = events[event_id]
        pages, locator_label = CORRECTION_SPECS[event_id]
        number = int(event_id.rsplit("-", 1)[1])
        record = common("correction", f"correction.o015-mit-sem-{number:04d}", "applied_in_admitted_reader")
        record.update({
            "source_event_id": event_id, "source_edition_id": MIT_SOURCE_EDITION_ID,
            "affected_unit_ids": [MIT_L11_UNIT_ID],
            "affected_segment_ids": [segment_ids[page] for page in pages],
            "source_path": MIT_PDF, "source_pdf_pages": pages,
            "source_locator": f"complete-notes PDF page(s) {', '.join(map(str, pages))}; {locator_label}",
            "witness_locators": [f"{MIT_WITNESS}#d90-mit-l11-p{page:03d}" for page in pages],
            "target_locators": [f"{MIT_TARGET}#d90-mit-l11-p{page:03d}" for page in pages],
            "surface": event["surface"], "source_issue": event["source_issue"],
            "target_action": event["target_action"], "correction_class": event["class"],
            "project_authorship": event["project_authorship"],
            "rights_statement": event["rights"],
            "disposition": "applied_in_admitted_reader",
            "shared_ledger_state": "immutable_boundary_snapshot",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.mit.l11.correction-snapshot",
            **binding,
        })
        add(record)

    pdf_pages = int(pdf["pages"])
    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l11.boundary-census", "boundary_census", MIT_CENSUS, "rights.o015-mit-pilot-build-qa", {"source_pdf_pages": SOURCE_PAGES, "next_source_page": 98}),
        ("artifact.mit.l11.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"locale": "en", "source_pdf_pages": SOURCE_PAGES, "official_editable_source": False, "source_item_count": 36, "source_display_count": 21, "source_figure_description_count": 7}),
        ("artifact.mit.l11.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": SOURCE_PAGES, "source_item_count": 36, "nested_source_item_count": 8, "source_display_count": 21, "source_figure_description_count": 7, "worked_example_count": 3, "counterexample_count": 1, "correction_event_ids": list(EXPECTED_EVENT_IDS)}),
        ("artifact.mit.l11.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "MathML", "source_pages": 12, "source_displays": 21, "source_figures": 7, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l11.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": pdf_pages, "page_size": "A4", "tagged": False, "searchable": True, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l11.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5 and LuaLaTeX", "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND}),
        ("artifact.mit.l11.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l11.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass", "errors": []}),
        ("artifact.mit.l11.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "live_viewport_measurement": True}),
        ("artifact.mit.l11.visual-qa", "visual_qa_report", MIT_VISUAL_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "pages": pdf_pages}),
        ("artifact.mit.l11.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.mit.l11.correction-snapshot", "correction_ledger_snapshot", MIT_LEDGER, "rights.o015-mit-pilot-build-qa", {"source_event_ids": list(EXPECTED_EVENT_IDS), "immutable_boundary_snapshot": True, "event_bindings": [events[event_id][1] for event_id in EXPECTED_EVENT_IDS]}),
        ("artifact.mit.l11.css", "html_stylesheet", MIT_CSS, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l11.pdf-preamble", "pdf_preamble", MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l11.pdf-filter", "pandoc_lua_filter", MIT_FILTER, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l11.before-body", "html_include", MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l11.after-body", "html_include", MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.o015.backend-generator-mit-l11", "backend_generator", MIT_BACKEND_GENERATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "protected_baseline_record_count": BASELINE_RECORD_COUNT}),
        ("artifact.o015.backend-validator-mit-l11", "backend_validator", MIT_BACKEND_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "deterministic_regeneration_runs_required": 2}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    correction_ids = [f"correction.{event_id.lower()}" for event_id in EXPECTED_EVENT_IDS]
    render_hashes = [item["sha256"] for item in visual.get("render", {}).get("pages", [])]
    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l11.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.complete-notes-pdf", "artifact.mit.l11.boundary-census", "artifact.mit.l11.semantic-witness"], "authority_pdf_pages": 340, "boundary_pages": SOURCE_PAGES, "next_source_page": 98, "next_source_page_text_sha256": fingerprints[98][1]}),
        ("qa.o015.mit-l11.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l11.semantic-witness", "artifact.mit.l11.target-source", "artifact.mit.l11.validation"], "official_editable_source": False, "source_items": 36, "nested_source_items": 8, "source_figures": 7, "source_figure_panels": 16, "worked_examples": 3, "counterexamples": 1}),
        ("qa.o015.mit-l11.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l11.validation", "artifact.mit.l11.boundary-census"], "source_page_map": [[page, page] for page in SOURCE_PAGES], "item_counts": {str(page): PAGE_ITEMS[page] for page in SOURCE_PAGES}, "nested_item_counts": {str(page): PAGE_NESTED[page] for page in SOURCE_PAGES}, "display_counts": {str(page): PAGE_DISPLAYS[page] for page in SOURCE_PAGES}, "figure_panel_counts": {str(page): sum(spec[0] for (p, _), spec in FIGURES.items() if p == page) for page in SOURCE_PAGES}, "worked_example_counts": {str(page): sum(1 for suffix in WORKED_EXAMPLE_SUFFIXES if EXAMPLES[suffix][0] == page) for page in SOURCE_PAGES}, "counterexample_counts": {str(page): sum(1 for suffix in COUNTEREXAMPLE_SUFFIXES if EXAMPLES[suffix][0] == page) for page in SOURCE_PAGES}}),
        ("qa.o015.mit-l11.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l11.semantic-witness", "artifact.mit.l11.target-source", "artifact.mit.l11.validation", "artifact.mit.l11.independent-rereview"], "source_math_nodes": int(html["math_nodes"]), "target_math_nodes": int(html["math_nodes"]), "display_formulas": 21, "formula_sequence_match": False, "intentional_differences_disclosed": True}),
        ("qa.o015.mit-l11.figures", "figure_description_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l11.semantic-witness", "artifact.mit.l11.target-source", "artifact.mit.l11.validation", "artifact.mit.l11.visual-qa"], "source_figure_blocks": 7, "source_figure_panels": 16, "semantic_figure_descriptions": 7, "copied_source_graphics": 0, "reader_images": 0}),
        ("qa.o015.mit-l11.corrections", "correction_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l11.correction-snapshot", "artifact.mit.l11.semantic-witness", "artifact.mit.l11.target-source", "artifact.mit.l11.validation", "artifact.mit.l11.independent-rereview"], "source_event_ids": list(EXPECTED_EVENT_IDS), "correction_record_ids": correction_ids, "silent_normalization": False}),
        ("qa.o015.mit-l11.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l11.builder", "artifact.mit.l11.target-html", "artifact.mit.l11.target-pdf", "artifact.mit.l11.validation"], "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND, "deterministic_rebuilds": 2, "html_sha256": HTML_IDENTITY[1], "pdf_sha256": PDF_IDENTITY[1], "toolchain": "Pandoc HTML5 and LuaLaTeX"}),
        ("qa.o015.mit-l11.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l11.target-html", "artifact.mit.l11.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": html["headings"], "math_nodes": int(html["math_nodes"]), "display_math_nodes": 21, "images": 0, "source_pages": 12, "source_items": 36, "source_figures": 7, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l11.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l11.browser-qa", "artifact.mit.l11.target-html"], "desktop_viewport": browser["desktop"]["viewport"], "mobile_viewport": browser["mobile"]["viewport"], "horizontal_overflow": False, "display_math_overflow": False, "live_measurement": True, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l11.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l11.target-pdf", "artifact.mit.l11.validation"], "pages": pdf_pages, "page_size": "A4", "lang": "id-ID", "searchable": True, "tagged": False, "images": 0, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l11.visual", "visual", "pass", {"witness_artifact_ids": ["artifact.mit.l11.visual-qa", "artifact.mit.l11.target-pdf"], "pages": pdf_pages, "all_pages_visually_inspected": True, "render_tool": "pdftoppm", "render_sha256": render_hashes}),
        ("qa.o015.mit-l11.semantic-rereview", "independent_semantic_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l11.independent-rereview", "artifact.mit.l11.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l11.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l11.target-html", "artifact.mit.l11.target-pdf", "artifact.mit.l11.browser-qa", "artifact.mit.l11.visual-qa"], "primary_surface": "semantic_html", "html_static_structure_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"], "human_review_is_release_gate": False}),
        ("qa.o015.mit-l11.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "human_review_is_release_gate": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded; this is evidence, not a hold."}),
        ("qa.o015.mit-l11.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l11.boundary-census", "artifact.mit.l11.semantic-witness", "artifact.mit.l11.target-source"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa", "o015-mit-l01-backend-tooling"], "source_graphics_in_boundary": 7, "source_figure_panels": 16, "source_graphics_redistributed": 0, "semantic_figure_descriptions": 7, "license": "CC BY-NC-SA 4.0", "change_event_ids": list(EXPECTED_EVENT_IDS), "non_endorsement": True}),
        ("qa.o015.mit-l11.csv-losslessness", "csv_losslessness", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l11", "artifact.o015.backend-validator-mit-l11"], "projection": "record_json is canonical JSON for each JSONL record", "utf8_strict": True, "row_order_matches_jsonl": True}),
        ("qa.o015.mit-l11.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l11", "artifact.o015.backend-validator-mit-l11", "artifact.o015.source-authority", "artifact.o015.component-rights"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_baseline_reconstruction_required": True, "deterministic_regeneration_runs_required": 2}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        status = "passed" if result == "pass" else result
        record = common("qa_event", record_id, status)
        record.update({"event_type": event_type, "result": result, "unit_id": MIT_L11_UNIT_ID, **extra})
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l11", "contains", MIT_ROOT_UNIT_ID, MIT_L11_UNIT_ID, "Eleventh admitted MIT source-order boundary, complete-notes pages 86-97."),
        ("relation.mit.witness-edition-contains-l11", "contains", MIT_WITNESS_EDITION_ID, MIT_L11_UNIT_ID, "Page-addressed English semantic witness for pages 86-97."),
        ("relation.mit.target-edition-contains-l11", "contains", MIT_TARGET_EDITION_ID, MIT_L11_UNIT_ID, "Built Indonesian semantic derivative for pages 86-97."),
        ("relation.mit.l10-precedes-l11", "precedes", "unit.mit.ocw-6.253.l10", MIT_L11_UNIT_ID, "Source order advances from Lecture 6 pages 64-85 to Lecture 7 pages 86-97."),
        ("relation.mit.witness-adapts-authority-pdf-l11", "adapts", "artifact.mit.l11.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes PDF pages 86-97."),
        ("relation.mit.target-translates-witness-l11", "translates", "artifact.mit.l11.target-source", "artifact.mit.l11.semantic-witness", "Page/list/formula translation with ten disclosed correction events bound by the L11 snapshot."),
        ("relation.mit.html-adapts-target-l11", "adapts", "artifact.mit.l11.target-html", "artifact.mit.l11.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l11", "adapts", "artifact.mit.l11.target-pdf", "artifact.mit.l11.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.browser-qa-depends-on-html-l11", "depends-on", "artifact.mit.l11.browser-qa", "artifact.mit.l11.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.visual-qa-depends-on-pdf-l11", "depends-on", "artifact.mit.l11.visual-qa", "artifact.mit.l11.target-pdf", "Rendered all-page visual QA evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l11", "depends-on", "artifact.mit.l11.validation", "artifact.mit.l11.browser-qa", "Validation is supplemented by current browser evidence."),
        ("relation.mit.validation-depends-on-visual-qa-l11", "depends-on", "artifact.mit.l11.validation", "artifact.mit.l11.visual-qa", "Validation is supplemented by current visual evidence."),
        ("relation.mit.rereview-depends-on-target-l11", "depends-on", "artifact.mit.l11.independent-rereview", "artifact.mit.l11.target-source", "Independent semantic rereview binds the admitted target and readers."),
    ]
    for page in SOURCE_PAGES:
        relation_specs.append((f"relation.mit.l11-contains-p{page:03d}", "contains", MIT_L11_UNIT_ID, segment_ids[page], f"Lecture 7 contains source page {page}."))
    for page, index in display_pairs:
        relation_specs.append((f"relation.mit.l11-formula-p{page:03d}-d{index:03d}-illustrates-segment", "illustrates", f"surface.mit.l11.formula.p{page:03d}.d{index:03d}", segment_ids[page], f"{PAGE_TITLES[page]} display {index}."))
    for page, index in figure_pairs:
        relation_specs.append((f"relation.mit.l11-figure-p{page:03d}-f{index:03d}-illustrates-segment", "illustrates", f"surface.mit.l11.figure-description.p{page:03d}.f{index:03d}", segment_ids[page], FIGURES[(page, index)][1] + "."))
    for suffix, (page, _, label, _) in EXAMPLES.items():
        relation_specs.append((f"relation.mit.l11-example-{suffix.replace('.', '-')}-exercises-segment", "exercises", f"surface.mit.l11.example.{suffix}", segment_ids[page], label + "."))
    for relation_id, relation_type, source_id, target_id, note in relation_specs:
        relation = common("relation", relation_id, "current")
        relation.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        add(relation)

    expected = expected_ids()
    if new_ids != expected:
        raise ValueError(f"generated L11 ID set differs; missing={sorted(expected-new_ids)}, extra={sorted(new_ids-expected)}")
    if len(new_records) != EXPECTED_NEW_RECORD_COUNT or Counter(record["entity_type"] for record in new_records) != EXPECTED_ENTITY_COUNTS:
        raise ValueError("generated L11 entity topology differs from the 148-record contract")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    all_ids = baseline_ids | new_ids
    for record in new_records:
        for field in schema.get("reference_fields", []):
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")
    return new_records


def serialize(records: list[dict[str, Any]]) -> tuple[bytes, bytes]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    entity_rank = {name: index for index, name in enumerate(schema["entity_order"])}
    ordered = sorted(records, key=lambda record: (entity_rank[record["entity_type"]], record["id"]))
    jsonl_bytes = "".join(canonical_json(record) + "\n" for record in ordered).encode("utf-8")
    csv_buffer = io.StringIO(newline="")
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(["schema", "schema_version", "entity_type", "id", "record_json"])
    for record in ordered:
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)])
    return jsonl_bytes, csv_buffer.getvalue().encode("utf-8")


def assert_baseline_preserved(output_jsonl: bytes, output_csv: bytes, baseline_jsonl: bytes, baseline_csv: bytes) -> None:
    if strip_workflow_jsonl(output_jsonl) != baseline_jsonl:
        raise ValueError("generated JSONL changes pre-existing record bytes or relative order")
    if strip_workflow_csv(output_csv) != baseline_csv:
        raise ValueError("generated CSV changes pre-existing row bytes or relative order")


def atomic_write_pair(output_jsonl: Path, output_csv: Path, jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    try:
        for destination, data in ((output_jsonl, jsonl_bytes), (output_csv, csv_bytes)):
            with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{destination.name}.mit-l11-", suffix=".stage", dir=destination.parent, delete=False) as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append(Path(handle.name))
        if staged[0].read_bytes() != jsonl_bytes or staged[1].read_bytes() != csv_bytes:
            raise ValueError("staged backend readback differs")
        os.replace(staged[0], output_jsonl)
        staged.pop(0)
        os.replace(staged[0], output_csv)
        staged.pop(0)
    finally:
        for path in staged:
            path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, default=JSONL_PATH)
    parser.add_argument("--input-csv", type=Path, default=CSV_PATH)
    parser.add_argument("--output-dir", type=Path, help="stage records.jsonl and records.csv here")
    parser.add_argument("--write-canonical", action="store_true", help="explicitly replace canonical backend files")
    parser.add_argument("--preflight", action="store_true", help="validate static source/topology/baseline only")
    args = parser.parse_args()
    if args.output_dir and args.write_canonical:
        parser.error("--output-dir and --write-canonical are mutually exclusive")

    preflight = static_preflight(args.input_jsonl, args.input_csv)
    if args.preflight:
        print(json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    report, browser, visual = load_reader_evidence()
    events = ledger_events()
    fingerprints = parse_census_fingerprints()
    baseline, baseline_jsonl, baseline_csv = load_baseline(args.input_jsonl, args.input_csv)
    new_records = generate_records(baseline, report, browser, visual, events, fingerprints)
    all_records = baseline + new_records
    jsonl_bytes, csv_bytes = serialize(all_records)
    assert_baseline_preserved(jsonl_bytes, csv_bytes, baseline_jsonl, baseline_csv)

    output_jsonl: Path | None = None
    output_csv: Path | None = None
    if args.output_dir:
        output_jsonl = args.output_dir / "records.jsonl"
        output_csv = args.output_dir / "records.csv"
    elif args.write_canonical:
        output_jsonl = JSONL_PATH
        output_csv = CSV_PATH
    if output_jsonl and output_csv:
        atomic_write_pair(output_jsonl, output_csv, jsonl_bytes, csv_bytes)

    result = {
        "result": "pass", "workflow": WORKFLOW,
        "write_mode": "canonical" if args.write_canonical else "staged" if args.output_dir else "dry-run",
        "protected_baseline_record_count": BASELINE_RECORD_COUNT,
        "protected_baseline_record_bytes_and_order_stable": True,
        "new_record_count": len(new_records),
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
        "new_id_set_sha256": id_set_sha256(new_records),
        "final_record_count": len(all_records),
        "final_id_set_sha256": id_set_sha256(all_records),
        "final_record_set_sha256": record_set_sha256(all_records),
        "jsonl": {"bytes": len(jsonl_bytes), "sha256": sha256(jsonl_bytes)},
        "csv": {"bytes": len(csv_bytes), "sha256": sha256(csv_bytes)},
        "output_jsonl": str(output_jsonl) if output_jsonl else None,
        "output_csv": str(output_csv) if output_csv else None,
        "correction_snapshot": {"bytes": LEDGER_IDENTITY[0], "sha256": LEDGER_IDENTITY[1]},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
