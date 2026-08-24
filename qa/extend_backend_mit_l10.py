#!/usr/bin/env python3
"""Deterministically add MIT 6.253 Lecture 6 (pages 64-85) to the backend.

The admitted 2,099-record L09 backend is byte protected.  Re-running this
tool removes only records owned by ``o015-mit-l10-backend-v1``, reconstructs
the exact protected baseline, regenerates the L10 projection, and proves that
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

RECORDED_AT = "2026-08-24T15:00:00Z"
WORKFLOW = "o015-mit-l10-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 2_099
BASELINE_JSONL = (1_577_079, "b483dfba003cd9fb422055c7836f62dd326575afcfc9b3c0a9a54aa6e1ad7ef8")
BASELINE_CSV = (1_886_451, "297629b3d20bd51bafd50cd5ecd0de70bd397b603a572e45083ca61b247f2574")
BASELINE_ID_SET_SHA256 = "316351a09581ac2bf8640e6d4ca76c8924a013b39aa4e03b074252aca427d209"
BASELINE_ID_ORDER_SHA256 = "0b353161f3a53734566e12f82eeeed09d306d11543b4ac6a060312506cb005da"
BASELINE_RECORD_SET_SHA256 = "4447a2fa4766ceee9c3c87374e38648dfd3e25c6fee30ba23191615700e482ff"
BASELINE_RECORD_LINE_SEQUENCE_SHA256 = "3fa0a11ba4fcb40974aff31158a50c7124da95e0ec3e58e5f3218b40ba8d0db1"

EXPECTED_NEW_RECORD_COUNT = 225
EXPECTED_ENTITY_COUNTS = Counter({
    "unit": 1,
    "segment": 22,
    "learning_surface": 60,
    "correction": 11,
    "artifact": 19,
    "qa_event": 17,
    "relation": 95,
})

MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L10_UNIT_ID = "unit.mit.ocw-6.253.l10"
SOURCE_PAGES = list(range(64, 86))

PAGE_ITEMS = {
    64: 4, 65: 2, 66: 2, 67: 3, 68: 6, 69: 3, 70: 3, 71: 6,
    72: 4, 73: 5, 74: 2, 75: 3, 76: 4, 77: 2, 78: 3, 79: 3,
    80: 3, 81: 3, 82: 2, 83: 2, 84: 2, 85: 3,
}
PAGE_NESTED = {
    64: 2, 65: 0, 66: 2, 67: 0, 68: 1, 69: 0, 70: 0, 71: 3,
    72: 0, 73: 0, 74: 2, 75: 2, 76: 0, 77: 0, 78: 2, 79: 0,
    80: 0, 81: 0, 82: 0, 83: 0, 84: 0, 85: 0,
}
PAGE_DISPLAYS = {
    64: 0, 65: 2, 66: 1, 67: 1, 68: 2, 69: 2, 70: 1, 71: 0,
    72: 3, 73: 0, 74: 0, 75: 5, 76: 2, 77: 4, 78: 2, 79: 1,
    80: 6, 81: 2, 82: 1, 83: 2, 84: 3, 85: 1,
}
PAGE_TITLES = {
    64: "Lecture 6 outline",
    65: "role of closed set intersections I",
    66: "role of closed set intersections II",
    67: "closure under linear transformation",
    68: "role of closed set intersections III",
    69: "partial minimization visualization",
    70: "partial minimization theorem",
    71: "refined-analysis summary",
    72: "asymptotic sequences",
    73: "retractive sequences",
    74: "set intersection theorem I",
    75: "set intersection theorem II",
    76: "necessity of retractivity",
    77: "linear and quadratic programming",
    78: "closure under linear transformation",
    79: "necessity of retractivity for linear images",
    80: "closedness of vector sums",
    81: "hyperplanes",
    82: "separating and supporting visualization",
    83: "supporting hyperplane theorem",
    84: "separating hyperplane theorem",
    85: "strict separation theorem",
}

# (source page, figure index) -> (panel count, semantic label)
FIGURES = {
    (65, 1): (1, "nested sublevel intersections and attainment"),
    (66, 1): (1, "linear-image preimage intersection"),
    (67, 1): (1, "closedness proof under a linear transformation"),
    (69, 1): (2, "partial-minimization attainment comparison"),
    (70, 1): (2, "compactness and partial-minimization profiles"),
    (72, 1): (1, "asymptotic sequence and limiting direction"),
    (73, 1): (2, "retractive and nonretractive set sequences"),
    (74, 1): (1, "minimum-norm asymptotic proof geometry"),
    (76, 1): (2, "polyhedral and nonretractive intersections"),
    (78, 1): (1, "nested preimages and a linear-image limit"),
    (79, 1): (2, "closed and nonclosed projected images"),
    (81, 1): (1, "hyperplane normal and associated halfspaces"),
    (82, 1): (2, "separating and supporting hyperplanes"),
    (82, 2): (2, "strict-separation geometry"),
    (83, 1): (1, "supporting-hyperplane limit construction"),
    (85, 1): (2, "strict-separation nearest-point construction"),
}

# record suffix -> (page, source anchor suffix, label, optional panel)
EXAMPLES = {
    "p069.i002": (69, "i002", "partial-minimization counterexample", None),
    "p079.f001.a": (79, "f001", "retractive polyhedral linear-image example", "a"),
    "p079.f001.b": (79, "f001", "nonretractive nonclosed linear-image example", "b"),
}

MIT_PDF = "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
MIT_CENSUS = "00_control/MIT_L10_LECTURE_6_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/MIT_L10_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-10-lecture-6-closed-intersections-hyperplanes-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.md"
MIT_HTML = "output/html/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.pdf"
MIT_CSS = "source/id-ID/mit-l10.css"
MIT_PREAMBLE = "source/id-ID/mit-l10-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l10-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l10-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l10-after-body.html"
MIT_BUILDER = "qa/build_mit_l10.py"
MIT_VALIDATOR = "qa/validate_mit_l10.py"
MIT_REPORT = "qa/MIT_L10_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L10_BROWSER_QA.json"
MIT_VISUAL_QA = "qa/MIT_L10_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L10_INDEPENDENT_REREVIEW.md"
MIT_BACKEND_GENERATOR = "qa/extend_backend_mit_l10.py"
MIT_BACKEND_VALIDATOR = "qa/validate_backend_mit_l10.py"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
CENSUS_IDENTITY = (17_483, "ab8c8ce397df3b57f1ae426687fba2b14d51313c7a6b4596369eae07116fb13e")
LEDGER_IDENTITY = (7_453, "72a8a2da79ea31e2587e42e5e6f54ec4662a749717d5c9c6119c707beef094ee")
WITNESS_IDENTITY = (43_575, "0dfe2c694fad607cef6c37ea7e84a0da359cedee6dc0bf023010f9c8a647c455")
TARGET_IDENTITY = (45_994, "be2dd29422f5e14ce26315258e772143335475cc2ee9c0d6bfc25f2ff05c8a53")
HTML_IDENTITY = (169_871, "2c3e0e72e535b181880b4e52cbc112c7d2fc393b8f5636e091ff517ed76f2038")
PDF_IDENTITY = (133_787, "3b01d57e8e8a7d7887f36cfdc205d1b68d1d007a152bd8e0cd75479628e1abc0")

CANONICAL_BUILD_COMMAND = (
    "python qa/build_mit_l10.py --html-output "
    "output/html/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.html "
    "--pdf-output output/pdf/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.pdf"
)
RECEIPT_BUILD_COMMAND = "python qa/build_mit_l10.py --html-output <html> --pdf-output <pdf>"
EXPECTED_EVENT_IDS = tuple(f"O015-MIT-SEM-{number:04d}" for number in range(20, 31))
CORRECTION_SPECS = {
    "O015-MIT-SEM-0020": ([65, 68, 70], "function-type arrows"),
    "O015-MIT-SEM-0021": ([67, 78], "missing noun in the convex-set description"),
    "O015-MIT-SEM-0022": ([70, 77], "minimizer point versus minimum-value terminology"),
    "O015-MIT-SEM-0023": ([67, 78], "nonnested proof neighborhoods"),
    "O015-MIT-SEM-0024": ([71], "duplicated word in the refined-analysis summary"),
    "O015-MIT-SEM-0025": ([72], "missing article in the asymptotic-sequence definition"),
    "O015-MIT-SEM-0026": ([76], "misspelled nonretractive label"),
    "O015-MIT-SEM-0027": ([78], "proof scope for the retractive-set case"),
    "O015-MIT-SEM-0028": ([81], "missing grammatical relations in hyperplane definitions"),
    "O015-MIT-SEM-0029": ([84], "reversed set-difference label"),
    "O015-MIT-SEM-0030": ([68], "unbound projection variable"),
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
        raise ValueError("stripped record set/order differs from the protected L09 baseline")
    return baseline, stripped_jsonl, stripped_csv


def parse_census_fingerprints() -> dict[int, tuple[int, str, int, str]]:
    if file_info(MIT_CENSUS) != CENSUS_IDENTITY:
        raise ValueError("L10 boundary census identity differs")
    pattern = re.compile(
        r"^\| (\d+)(?: \(delimiter only\))? \| ([\d,]+) \| `([0-9a-f]{64})` "
        r"\| ([\d,]+) \| `([0-9a-f]{64})` \|$"
    )
    result: dict[int, tuple[int, str, int, str]] = {}
    for line in (ROOT / MIT_CENSUS).read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            page = int(match.group(1))
            result[page] = (
                int(match.group(2).replace(",", "")), match.group(3),
                int(match.group(4).replace(",", "")), match.group(5),
            )
    if set(result) != set(range(64, 87)):
        raise ValueError("L10 census page-fingerprint set differs")
    return result


def ledger_events() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if file_info(MIT_LEDGER) != LEDGER_IDENTITY:
        raise ValueError("L10 correction snapshot identity differs")
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), start=1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id not in EXPECTED_EVENT_IDS or event_id in result:
            raise ValueError(f"unexpected or duplicate L10 correction event: {event_id}")
        required = {"authority", "source", "surface", "source_issue", "target_action", "class"}
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
    if tuple(sorted(result)) != EXPECTED_EVENT_IDS:
        raise ValueError("L10 correction event set differs")
    return result


def identity_tuple(record: dict[str, Any]) -> tuple[int, str]:
    return int(record.get("bytes", -1)), str(record.get("sha256", ""))


def validate_source_topology() -> dict[str, Any]:
    if file_info(MIT_PDF) != SOURCE_PDF_IDENTITY:
        raise ValueError("MIT authority PDF identity differs")
    if file_info(MIT_WITNESS) != WITNESS_IDENTITY or file_info(MIT_TARGET) != TARGET_IDENTITY:
        raise ValueError("L10 canonical semantic-source identity differs")
    expected_pages = {f"d90-mit-l10-p{page:03d}" for page in SOURCE_PAGES}
    expected_items = {
        f"d90-mit-l10-p{page:03d}-i{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)
    }
    expected_displays = {
        f"d90-mit-l10-p{page:03d}-d{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    }
    expected_figures = {
        f"d90-mit-l10-p{page:03d}-f{index:03d}" for page, index in FIGURES
    }
    patterns = {
        "pages": re.compile(r"^::: \{\.source-page #(d90-mit-l10-p\d{3})\b", re.M),
        "items": re.compile(r"^::: \{\.source-item #(d90-mit-l10-p\d{3}-i\d{3})\b", re.M),
        "displays": re.compile(r"^\s*::: \{\.source-display #(d90-mit-l10-p\d{3}-d\d{3})\b", re.M),
        "figures": re.compile(r"^::: \{\.source-figure #(d90-mit-l10-p\d{3}-f\d{3})\b", re.M),
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
        raise ValueError("L10 deterministic reader identity differs")
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    visual = json.loads((ROOT / MIT_VISUAL_QA).read_text(encoding="utf-8"))
    boundary = report.get("boundary", {})
    expected_boundary = {
        "source_pdf_pages": SOURCE_PAGES, "source_pages": 22,
        "next_source_page": 86, "next_heading": "LECTURE 7 - LECTURE OUTLINE",
        "source_items": 70, "source_display_wrappers": 41,
        "display_formula_blocks": 41, "source_figures": 16,
        "source_figure_panels": 24, "copied_source_graphics": 0,
        "exercises": 0, "hints": 0, "answers": 0, "solutions": 0,
        "code_surfaces": 0, "interactive_surfaces": 0,
    }
    if report.get("result") != "pass" or report.get("errors") not in ([], None) or boundary != expected_boundary:
        raise ValueError("L10 validation receipt boundary is not a strict pass")
    if report.get("model_identification") != "OpenAI Codex gpt-5.6-sol, Ultra":
        raise ValueError("L10 model identification differs")
    formulas = report.get("formula_inventory", {})
    if formulas.get("witness", {}).get("display_blocks") != 41 or formulas.get("target", {}).get("display_blocks") != 41:
        raise ValueError("L10 formula inventory differs")
    build = report.get("build", {})
    expected_reader = {"html": list(HTML_IDENTITY), "pdf": list(PDF_IDENTITY)}
    if (
        build.get("command") != RECEIPT_BUILD_COMMAND
        or build.get("deterministic_rebuilds") != 2
        or build.get("expected") != expected_reader
        or build.get("rebuild_identities") != [expected_reader, expected_reader]
    ):
        raise ValueError("L10 deterministic build evidence differs")
    if identity_tuple(build.get("canonical", {}).get("html", {})) != HTML_IDENTITY or identity_tuple(build.get("canonical", {}).get("pdf", {})) != PDF_IDENTITY:
        raise ValueError("L10 canonical reader binding differs")
    html = report.get("html", {})
    if any(html.get(name) != value for name, value in {
        "lang": "id-ID", "source_pages": 22, "source_items": 70,
        "source_displays": 41, "source_figures": 16,
        "display_math_nodes": 41, "images": 0, "media_or_embeds": 0,
        "form_controls": 0, "duplicate_ids": [], "unresolved_fragments": [],
    }.items()):
        raise ValueError("L10 HTML topology differs")
    pdf = report.get("pdf", {})
    if (
        pdf.get("pages") != 10
        or pdf.get("searchable_text_chars") != 22196
        or pdf.get("searchable_chars_per_page")
        != [1501, 2546, 2339, 2625, 2749, 2036, 1889, 2066, 2628, 1817]
        or pdf.get("to_unicode_all_fonts") is not True
        or pdf.get("images") != 0
        or pdf.get("encrypted") is not False
    ):
        raise ValueError("L10 PDF topology differs")
    if browser.get("result") != "pass" or identity_tuple(browser.get("artifact", {})) != HTML_IDENTITY:
        raise ValueError("L10 browser evidence differs")
    if visual.get("result") != "pass" or identity_tuple(visual.get("artifact", {})) != PDF_IDENTITY:
        raise ValueError("L10 visual evidence differs")
    if visual.get("render", {}).get("pages_inspected") != list(range(1, 11)):
        raise ValueError("L10 visual evidence does not cover every reader page")
    rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
    if "PASS — no open P1, P2, or P3 findings" not in rereview:
        raise ValueError("L10 independent rereview disposition differs")
    for digest in (WITNESS_IDENTITY[1], TARGET_IDENTITY[1], HTML_IDENTITY[1], PDF_IDENTITY[1]):
        if digest not in rereview:
            raise ValueError("L10 independent rereview binds stale canonical bytes")
    return report, browser, visual


def expected_ids() -> set[str]:
    result = {MIT_L10_UNIT_ID}
    result.update(f"d90.mit.ocw-6.253.l10.p{page:03d}" for page in SOURCE_PAGES)
    result.update(
        f"surface.mit.l10.formula.p{page:03d}.d{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    )
    result.update(
        f"surface.mit.l10.figure-description.p{page:03d}.f{index:03d}"
        for page, index in FIGURES
    )
    result.update(f"surface.mit.l10.example.{suffix}" for suffix in EXAMPLES)
    result.update(f"correction.o015-mit-sem-{number:04d}" for number in range(20, 31))
    result.update({
        "artifact.mit.l10.boundary-census", "artifact.mit.l10.semantic-witness",
        "artifact.mit.l10.target-source", "artifact.mit.l10.target-html",
        "artifact.mit.l10.target-pdf", "artifact.mit.l10.builder",
        "artifact.mit.l10.validator", "artifact.mit.l10.validation",
        "artifact.mit.l10.browser-qa", "artifact.mit.l10.visual-qa",
        "artifact.mit.l10.independent-rereview", "artifact.mit.l10.correction-snapshot",
        "artifact.mit.l10.css", "artifact.mit.l10.pdf-preamble",
        "artifact.mit.l10.pdf-filter", "artifact.mit.l10.before-body",
        "artifact.mit.l10.after-body", "artifact.o015.backend-generator-mit-l10",
        "artifact.o015.backend-validator-mit-l10",
    })
    qa_suffixes = {
        "source-freeze", "semantic-reconstruction", "topology", "formulas", "figures",
        "corrections", "build", "html", "browser", "pdf", "visual",
        "semantic-rereview", "accessibility", "language", "rights",
        "csv-losslessness", "backend-integration",
    }
    result.update(f"qa.o015.mit-l10.{suffix}" for suffix in qa_suffixes)
    core_relations = {
        "work-contains-l10", "witness-edition-contains-l10", "target-edition-contains-l10",
        "l09-precedes-l10", "witness-adapts-authority-pdf-l10",
        "target-translates-witness-l10", "html-adapts-target-l10",
        "pdf-adapts-target-l10", "browser-qa-depends-on-html-l10",
        "visual-qa-depends-on-pdf-l10", "validation-depends-on-browser-qa-l10",
        "validation-depends-on-visual-qa-l10", "rereview-depends-on-target-l10",
    }
    result.update(f"relation.mit.{suffix}" for suffix in core_relations)
    result.update(f"relation.mit.l10-contains-p{page:03d}" for page in SOURCE_PAGES)
    result.update(
        f"relation.mit.l10-formula-p{page:03d}-d{index:03d}-illustrates-segment"
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    )
    result.update(
        f"relation.mit.l10-figure-p{page:03d}-f{index:03d}-illustrates-segment"
        for page, index in FIGURES
    )
    result.update(
        f"relation.mit.l10-example-{suffix.replace('.', '-')}-exercises-segment"
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
        raise ValueError(f"static L10 ID contract has {len(ids)} IDs, expected {EXPECTED_NEW_RECORD_COUNT}")
    collisions = sorted(ids & {record["id"] for record in baseline})
    if collisions:
        raise ValueError(f"L10 stable-ID collisions: {collisions}")
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

    segment_ids = {page: f"d90.mit.ocw-6.253.l10.p{page:03d}" for page in SOURCE_PAGES}
    item_ids = [
        f"d90-mit-l10-p{page:03d}-i{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)
    ]
    display_pairs = [
        (page, index) for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    ]
    figure_pairs = list(FIGURES)
    html = report["html"]
    pdf = report["pdf"]

    unit = common("unit", MIT_L10_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 10,
        "source_local_id": "lecture-6-pages-64-85",
        "source_local_label": "Lecture 6 - Closed Intersections, Closure, and Hyperplanes",
        "target_local_label": "Kuliah 6 - Irisan Tertutup, Ketertutupan, dan Hiperbidang",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": SOURCE_PAGES,
        "next_source_page": 86,
        "next_source_heading": "LECTURE 7 - LECTURE OUTLINE",
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 70,
        "nested_source_item_count": 14,
        "source_item_ids": item_ids,
        "target_item_ids": item_ids,
        "source_display_count": 41,
        "source_display_ids": [f"d90-mit-l10-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "target_display_ids": [f"d90-mit-l10-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "source_figure_count": 16,
        "source_figure_ids": [f"d90-mit-l10-p{page:03d}-f{index:03d}" for page, index in figure_pairs],
        "target_figure_ids": [f"d90-mit-l10-p{page:03d}-f{index:03d}" for page, index in figure_pairs],
        "source_figure_panel_count": 24,
        "explicit_example_count": 3,
        "explicit_example_ids": [f"surface.mit.l10.example.{suffix}" for suffix in EXAMPLES],
        "exercise_count": 0, "hint_count": 0, "answer_count": 0,
        "solution_count": 0, "code_surface_count": 0,
        "interactive_surface_count": 0, "copied_source_graphics": 0,
        "correction_event_ids": list(EXPECTED_EVENT_IDS),
        "canonical_build_command": CANONICAL_BUILD_COMMAND,
    })
    add(unit)

    for order, page in enumerate(SOURCE_PAGES, start=1):
        anchor = f"d90-mit-l10-p{page:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        text_bytes, text_hash, render_bytes, render_hash = fingerprints[page]
        figures_on_page = [(index, FIGURES[(page, index)]) for p, index in figure_pairs if p == page]
        record = common("segment", segment_ids[page], "visually_checked")
        record.update({
            "unit_id": MIT_L10_UNIT_ID, "order": order,
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
            "explicit_example_count": sum(1 for value in EXAMPLES.values() if value[0] == page),
            "anchor_mapping_rule": "identical d90-mit-l10 stable anchor preserved from witness to target",
        })
        add(record)

    for global_order, (page, index) in enumerate(display_pairs, start=1):
        anchor = f"d90-mit-l10-p{page:03d}-d{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l10.formula.p{page:03d}.d{index:03d}", "present")
        record.update({
            "unit_id": MIT_L10_UNIT_ID, "surface_type": "display_formula", "presence": "present",
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
        anchor = f"d90-mit-l10-p{page:03d}-f{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l10.figure-description.p{page:03d}.f{index:03d}", "present_with_limitation")
        record.update({
            "unit_id": MIT_L10_UNIT_ID, "surface_type": "semantic_figure_description",
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
        anchor = f"d90-mit-l10-p{page:03d}-{anchor_suffix}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l10.example.{suffix}", "present")
        record.update({
            "unit_id": MIT_L10_UNIT_ID, "surface_type": "worked_example", "presence": "present",
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
            "affected_unit_ids": [MIT_L10_UNIT_ID],
            "affected_segment_ids": [segment_ids[page] for page in pages],
            "source_path": MIT_PDF, "source_pdf_pages": pages,
            "source_locator": f"complete-notes PDF page(s) {', '.join(map(str, pages))}; {locator_label}",
            "witness_locators": [f"{MIT_WITNESS}#d90-mit-l10-p{page:03d}" for page in pages],
            "target_locators": [f"{MIT_TARGET}#d90-mit-l10-p{page:03d}" for page in pages],
            "surface": event["surface"], "source_issue": event["source_issue"],
            "target_action": event["target_action"], "correction_class": event["class"],
            "disposition": "applied_in_admitted_reader",
            "shared_ledger_state": "immutable_boundary_snapshot",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.mit.l10.correction-snapshot",
            **binding,
        })
        add(record)

    pdf_pages = int(pdf["pages"])
    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l10.boundary-census", "boundary_census", MIT_CENSUS, "rights.o015-mit-pilot-build-qa", {"source_pdf_pages": SOURCE_PAGES, "next_source_page": 86}),
        ("artifact.mit.l10.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"locale": "en", "source_pdf_pages": SOURCE_PAGES, "official_editable_source": False, "source_item_count": 70, "source_display_count": 41, "source_figure_description_count": 16}),
        ("artifact.mit.l10.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": SOURCE_PAGES, "source_item_count": 70, "nested_source_item_count": 14, "source_display_count": 41, "source_figure_description_count": 16, "explicit_example_count": 3, "correction_event_ids": list(EXPECTED_EVENT_IDS)}),
        ("artifact.mit.l10.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "MathML", "source_pages": 22, "source_displays": 41, "source_figures": 16, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l10.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": pdf_pages, "page_size": "A4", "tagged": False, "searchable": True, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l10.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5 and LuaLaTeX", "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND}),
        ("artifact.mit.l10.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l10.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass", "errors": []}),
        ("artifact.mit.l10.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "live_viewport_measurement": True}),
        ("artifact.mit.l10.visual-qa", "visual_qa_report", MIT_VISUAL_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "pages": pdf_pages}),
        ("artifact.mit.l10.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.mit.l10.correction-snapshot", "correction_ledger_snapshot", MIT_LEDGER, "rights.o015-mit-pilot-build-qa", {"source_event_ids": list(EXPECTED_EVENT_IDS), "immutable_boundary_snapshot": True, "event_bindings": [events[event_id][1] for event_id in EXPECTED_EVENT_IDS]}),
        ("artifact.mit.l10.css", "html_stylesheet", MIT_CSS, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l10.pdf-preamble", "pdf_preamble", MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l10.pdf-filter", "pandoc_lua_filter", MIT_FILTER, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l10.before-body", "html_include", MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l10.after-body", "html_include", MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.o015.backend-generator-mit-l10", "backend_generator", MIT_BACKEND_GENERATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "protected_baseline_record_count": BASELINE_RECORD_COUNT}),
        ("artifact.o015.backend-validator-mit-l10", "backend_validator", MIT_BACKEND_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "deterministic_regeneration_runs_required": 2}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    correction_ids = [f"correction.o015-mit-sem-{number:04d}" for number in range(20, 31)]
    render_hashes = [item["sha256"] for item in pdf.get("render_identities", [])]
    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l10.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.complete-notes-pdf", "artifact.mit.l10.boundary-census", "artifact.mit.l10.semantic-witness"], "authority_pdf_pages": 340, "boundary_pages": SOURCE_PAGES, "next_source_page": 86, "next_source_page_text_sha256": fingerprints[86][1]}),
        ("qa.o015.mit-l10.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l10.semantic-witness", "artifact.mit.l10.target-source", "artifact.mit.l10.validation"], "official_editable_source": False, "source_items": 70, "nested_source_items": 14, "source_figures": 16, "source_figure_panels": 24, "explicit_examples": 3}),
        ("qa.o015.mit-l10.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l10.validation", "artifact.mit.l10.boundary-census"], "source_page_map": [[page, page] for page in SOURCE_PAGES], "item_counts": {str(page): PAGE_ITEMS[page] for page in SOURCE_PAGES}, "nested_item_counts": {str(page): PAGE_NESTED[page] for page in SOURCE_PAGES}, "display_counts": {str(page): PAGE_DISPLAYS[page] for page in SOURCE_PAGES}, "figure_panel_counts": {str(page): sum(spec[0] for (p, _), spec in FIGURES.items() if p == page) for page in SOURCE_PAGES}, "example_counts": {str(page): sum(1 for value in EXAMPLES.values() if value[0] == page) for page in SOURCE_PAGES}}),
        ("qa.o015.mit-l10.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l10.semantic-witness", "artifact.mit.l10.target-source", "artifact.mit.l10.validation", "artifact.mit.l10.independent-rereview"], "source_math_nodes": int(html["math_nodes"]), "target_math_nodes": int(html["math_nodes"]), "display_formulas": 41, "formula_sequence_match": True}),
        ("qa.o015.mit-l10.figures", "figure_description_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l10.semantic-witness", "artifact.mit.l10.target-source", "artifact.mit.l10.validation", "artifact.mit.l10.visual-qa"], "source_figure_blocks": 16, "source_figure_panels": 24, "semantic_figure_descriptions": 16, "copied_source_graphics": 0, "reader_images": 0}),
        ("qa.o015.mit-l10.corrections", "correction_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l10.correction-snapshot", "artifact.mit.l10.semantic-witness", "artifact.mit.l10.target-source", "artifact.mit.l10.validation", "artifact.mit.l10.independent-rereview"], "source_event_ids": list(EXPECTED_EVENT_IDS), "correction_record_ids": correction_ids, "silent_normalization": False}),
        ("qa.o015.mit-l10.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l10.builder", "artifact.mit.l10.target-html", "artifact.mit.l10.target-pdf", "artifact.mit.l10.validation"], "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND, "deterministic_rebuilds": 2, "html_sha256": HTML_IDENTITY[1], "pdf_sha256": PDF_IDENTITY[1], "toolchain": "Pandoc HTML5 and LuaLaTeX"}),
        ("qa.o015.mit-l10.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l10.target-html", "artifact.mit.l10.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": html["headings"], "math_nodes": int(html["math_nodes"]), "display_math_nodes": 41, "images": 0, "source_pages": 22, "source_items": 70, "source_figures": 16, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l10.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l10.browser-qa", "artifact.mit.l10.target-html"], "desktop_viewport": browser["desktop"]["viewport_css_px"], "mobile_viewport": browser["mobile"]["viewport_css_px"], "horizontal_overflow": False, "display_math_overflow": False, "live_measurement": True, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l10.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l10.target-pdf", "artifact.mit.l10.validation"], "pages": pdf_pages, "page_size": "A4", "lang": "id-ID", "searchable": True, "tagged": False, "images": 0, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l10.visual", "visual", "pass", {"witness_artifact_ids": ["artifact.mit.l10.visual-qa", "artifact.mit.l10.target-pdf"], "pages": pdf_pages, "all_pages_visually_inspected": True, "render_tool": "pdftoppm", "render_sha256": render_hashes}),
        ("qa.o015.mit-l10.semantic-rereview", "independent_semantic_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l10.independent-rereview", "artifact.mit.l10.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l10.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l10.target-html", "artifact.mit.l10.target-pdf", "artifact.mit.l10.browser-qa", "artifact.mit.l10.visual-qa"], "primary_surface": "semantic_html", "html_static_structure_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"], "human_review_is_release_gate": False}),
        ("qa.o015.mit-l10.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "human_review_is_release_gate": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded; this is evidence, not a hold."}),
        ("qa.o015.mit-l10.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l10.boundary-census", "artifact.mit.l10.semantic-witness", "artifact.mit.l10.target-source"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa", "o015-mit-l01-backend-tooling"], "source_graphics_in_boundary": 16, "source_figure_panels": 24, "source_graphics_redistributed": 0, "semantic_figure_descriptions": 16, "license": "CC BY-NC-SA 4.0", "change_event_ids": list(EXPECTED_EVENT_IDS), "non_endorsement": True}),
        ("qa.o015.mit-l10.csv-losslessness", "csv_losslessness", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l10", "artifact.o015.backend-validator-mit-l10"], "projection": "record_json is canonical JSON for each JSONL record", "utf8_strict": True, "row_order_matches_jsonl": True}),
        ("qa.o015.mit-l10.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l10", "artifact.o015.backend-validator-mit-l10", "artifact.o015.source-authority", "artifact.o015.component-rights"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_baseline_reconstruction_required": True, "deterministic_regeneration_runs_required": 2}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        status = "passed" if result == "pass" else result
        record = common("qa_event", record_id, status)
        record.update({"event_type": event_type, "result": result, "unit_id": MIT_L10_UNIT_ID, **extra})
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l10", "contains", MIT_ROOT_UNIT_ID, MIT_L10_UNIT_ID, "Tenth admitted MIT source-order boundary, complete-notes pages 64-85."),
        ("relation.mit.witness-edition-contains-l10", "contains", MIT_WITNESS_EDITION_ID, MIT_L10_UNIT_ID, "Page-addressed English semantic witness for pages 64-85."),
        ("relation.mit.target-edition-contains-l10", "contains", MIT_TARGET_EDITION_ID, MIT_L10_UNIT_ID, "Built Indonesian semantic derivative for pages 64-85."),
        ("relation.mit.l09-precedes-l10", "precedes", "unit.mit.ocw-6.253.l09", MIT_L10_UNIT_ID, "Source order advances from Lecture 5 pages 50-63 to Lecture 6 pages 64-85."),
        ("relation.mit.witness-adapts-authority-pdf-l10", "adapts", "artifact.mit.l10.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes PDF pages 64-85."),
        ("relation.mit.target-translates-witness-l10", "translates", "artifact.mit.l10.target-source", "artifact.mit.l10.semantic-witness", "Page/list/formula translation with disclosed corrections O015-MIT-SEM-0020 through 0030."),
        ("relation.mit.html-adapts-target-l10", "adapts", "artifact.mit.l10.target-html", "artifact.mit.l10.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l10", "adapts", "artifact.mit.l10.target-pdf", "artifact.mit.l10.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.browser-qa-depends-on-html-l10", "depends-on", "artifact.mit.l10.browser-qa", "artifact.mit.l10.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.visual-qa-depends-on-pdf-l10", "depends-on", "artifact.mit.l10.visual-qa", "artifact.mit.l10.target-pdf", "Rendered all-page visual QA evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l10", "depends-on", "artifact.mit.l10.validation", "artifact.mit.l10.browser-qa", "Validation is supplemented by current browser evidence."),
        ("relation.mit.validation-depends-on-visual-qa-l10", "depends-on", "artifact.mit.l10.validation", "artifact.mit.l10.visual-qa", "Validation is supplemented by current visual evidence."),
        ("relation.mit.rereview-depends-on-target-l10", "depends-on", "artifact.mit.l10.independent-rereview", "artifact.mit.l10.target-source", "Independent semantic rereview binds the admitted target and readers."),
    ]
    for page in SOURCE_PAGES:
        relation_specs.append((f"relation.mit.l10-contains-p{page:03d}", "contains", MIT_L10_UNIT_ID, segment_ids[page], f"Lecture 6 contains source page {page}."))
    for page, index in display_pairs:
        relation_specs.append((f"relation.mit.l10-formula-p{page:03d}-d{index:03d}-illustrates-segment", "illustrates", f"surface.mit.l10.formula.p{page:03d}.d{index:03d}", segment_ids[page], f"{PAGE_TITLES[page]} display {index}."))
    for page, index in figure_pairs:
        relation_specs.append((f"relation.mit.l10-figure-p{page:03d}-f{index:03d}-illustrates-segment", "illustrates", f"surface.mit.l10.figure-description.p{page:03d}.f{index:03d}", segment_ids[page], FIGURES[(page, index)][1] + "."))
    for suffix, (page, _, label, _) in EXAMPLES.items():
        relation_specs.append((f"relation.mit.l10-example-{suffix.replace('.', '-')}-exercises-segment", "exercises", f"surface.mit.l10.example.{suffix}", segment_ids[page], label + "."))
    for relation_id, relation_type, source_id, target_id, note in relation_specs:
        relation = common("relation", relation_id, "current")
        relation.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        add(relation)

    expected = expected_ids()
    if new_ids != expected:
        raise ValueError(f"generated L10 ID set differs; missing={sorted(expected-new_ids)}, extra={sorted(new_ids-expected)}")
    if len(new_records) != EXPECTED_NEW_RECORD_COUNT or Counter(record["entity_type"] for record in new_records) != EXPECTED_ENTITY_COUNTS:
        raise ValueError("generated L10 entity topology differs from the 225-record contract")

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
            with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{destination.name}.mit-l10-", suffix=".stage", dir=destination.parent, delete=False) as handle:
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
