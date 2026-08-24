#!/usr/bin/env python3
"""Add the reader-validated MIT 6.253 Lecture 2 boundary (pages 20-28).

The admitted 1,605-record backend is a protected byte-for-byte baseline.  This
workflow adds only L06 records.  A rerun removes only this workflow, proves the
original JSONL and CSV baseline bytes were reconstructed exactly, and then
recreates the same deterministic stable-ID projection.
"""

from __future__ import annotations

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

RECORDED_AT = "2026-08-23T23:00:00Z"
WORKFLOW = "o015-mit-l06-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 1605
BASELINE_JSONL = (1_142_443, "30c6f3257d481136995acd7947a725da003c4ab2ea2e9049de53a23fa681658b")
BASELINE_CSV = (1_373_874, "f66227edc14e953b44d833b87b0373f76d87bf04fdd32d2f50552597915746e3")
BASELINE_ID_SET_SHA256 = "174b5f03bf72f9cbab07f05950c56021a96917b143e8680c05050bb0dfe9d6e1"
BASELINE_RECORD_SET_SHA256 = "afbc446ca325c5aabe8549b5e0cd5fed2b1865c9433a406cb499ab12145d097f"

MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L06_UNIT_ID = "unit.mit.ocw-6.253.l06"
SOURCE_PAGES = list(range(20, 29))
PAGE_ITEMS = {20: 4, 21: 6, 22: 3, 23: 2, 24: 5, 25: 4, 26: 3, 27: 3, 28: 2}
PAGE_NESTED = {20: 0, 21: 4, 22: 3, 23: 0, 24: 0, 25: 3, 26: 4, 27: 0, 28: 3}
PAGE_DISPLAYS = {20: 0, 21: 1, 22: 2, 23: 1, 24: 2, 25: 1, 26: 2, 27: 0, 28: 3}
FIGURE_PANELS = {22: 4, 23: 1, 24: 2, 25: 1, 27: 2}
DISPLAY_LABELS = {
    (21, 1): "tuple representation",
    (22, 1): "line-segment convexity condition",
    (22, 2): "polyhedral-set representation",
    (23, 1): "defining convexity inequality",
    (24, 1): "epigraph definition",
    (24, 2): "effective-domain definition",
    (25, 1): "lower-semicontinuity proof inequality chain",
    (26, 1): "zero function on the open interval",
    (26, 2): "piecewise extended-real-valued function",
    (28, 1): "positive weighted-sum construction",
    (28, 2): "linear-composition construction",
    (28, 3): "pointwise-supremum construction",
}
FIGURE_LABELS = {
    22: "four-panel convex and nonconvex set comparison",
    23: "convex-function chord-test graph",
    24: "two-panel epigraph comparison",
    25: "epigraph and sublevel-set graph",
    27: "two-panel proper and improper function comparison",
}
SOURCE_TEXT_FINGERPRINTS = {
    20: (228, "5abd5fe7dee510eda6bfd683928d0c1e166d4f0fdf9a5c254371e152c21771a2"),
    21: (953, "23a0470c2ed9f1863f6fe10dc94122033b5e453a2dd41c33ede2f75f4ea42089"),
    22: (923, "57b10e80d12a6ff7413cfa6bb426f39fb9e05999abf55c4ee6e4001b9e7291b5"),
    23: (1139, "8108fb7eee4a4d68c31773cd7cda8edb0d2be6b1bde30faa3ef18284f7ed246e"),
    24: (1370, "1a3e5ff5f45dc7c12aacc6d98694fe74094134b9f73c1b8fc476924bd255fd9e"),
    25: (1052, "8ac931a9adaa5310118c79931050e629cfdc0ce7d29d5e5ed1731fbc27dceed2"),
    26: (1060, "cbe98d957ab8491d5ca06f96eab748f3da6e67b7b05fd500470eb4b16e82ba43"),
    27: (788, "9ebd0cd52cd11d1e6e1804ea8ef15a783c5c1d62d6c1dedd9f45ae1cb7b038c7"),
    28: (897, "ef86e6eac19001b1fc98a35d1b12b6c15734cb655228f0deaea6f33f592b2823"),
    29: (221, "c15536202c7266b03878d0c26e7eb7f16fd66914dc8f1e3130a6bda4331a2a86"),
}
SOURCE_RENDER_FINGERPRINTS = {
    20: (18551, "8fdbec5f3964f3b37f20cd8019c1f6faf10ac602e5dca094d164332cf2671e76"),
    21: (54197, "424b55e6e49185f97840a48eaa812a98fa2ec07f400c20d506388c372c1585b1"),
    22: (56498, "fdd34c8218708534337f633698413f26e92154715490a7e9a0b16bfa845faa3b"),
    23: (62144, "dfd714c82b19fa8d902881d78c92d194d14e522906fdb24fefbf050901a05433"),
    24: (74754, "78ebb805d3137b3ef1f07ff2f5584b17356fee535fbce114042351443d6a1234"),
    25: (59764, "172236ccd585df0ff51cf6ca1a3f2d94764f09f575d834ad0d6e4bb76fa2ac70"),
    26: (56236, "ceacef29117b4516c3fc1bd3cfd52799dcb25aa5a04472160d7c9ee25321dad5"),
    27: (41254, "6d8e5c52b9db15e1aa89db60f6faf12b80be27b175e6d4dfd85bf5b9e78162af"),
    28: (53351, "3411fbb3a5a9fc273d807a92e705dc1b02d38e2a7a21e2843d264380d7fb74a7"),
    29: (17903, "872877e2ff62bc5d5d9bb85f7b4d5edaed3f17264ed09761e554c0a817d069ff"),
}

MIT_PDF = (
    "authority/mit-ocw-6.253/course-archive/static_resources/"
    "6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
)
MIT_CENSUS = "00_control/MIT_L06_LECTURE_2_PAGES_020-028_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/MIT_L06_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-06-lecture-2-convex-foundations-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-06-kuliah-2-landasan-konveks-id.md"
MIT_HTML = "output/html/D90-MIT-06-kuliah-2-landasan-konveks-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-06-kuliah-2-landasan-konveks-id.pdf"
MIT_CSS = "source/id-ID/mit-l06.css"
MIT_PREAMBLE = "source/id-ID/mit-l06-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l06-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l06-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l06-after-body.html"
MIT_BUILDER = "qa/build_mit_l06.py"
MIT_VALIDATOR = "qa/validate_mit_l06.py"
MIT_REPORT = "qa/MIT_L06_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L06_BROWSER_QA.json"
MIT_VISUAL_QA = "qa/MIT_L06_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L06_INDEPENDENT_REREVIEW.md"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
LEDGER_IDENTITY = (1_406, "4049f5ed333489bc0b8942e91ae3ab05f43677f13de1e532d544d7691724737f")
CANONICAL_BUILD_COMMAND = (
    "python qa/build_mit_l06.py "
    "--html-output output/html/D90-MIT-06-kuliah-2-landasan-konveks-id.html "
    "--pdf-output output/pdf/D90-MIT-06-kuliah-2-landasan-konveks-id.pdf"
)
RECEIPT_BUILD_COMMAND = "python qa/build_mit_l06.py --html-output <html> --pdf-output <pdf>"
FINAL_READER_IDENTITIES = {
    MIT_WITNESS: (15_594, "a8094ad892a90a20d271e961504fb418b1ea241859b072cf5ba56317783b809a"),
    MIT_TARGET: (17_772, "a9e8b353adddc4919b6244e27df4365a33e74d4b034b9d99fff6eb3f93e0b23e"),
    MIT_PREAMBLE: (1_499, "a561a9dccaf4997e1a82064bf09ad20baf07f85e50441f1b11cfbd31c3993f6a"),
    MIT_HTML: (70_446, "94275af59592c64e7c8ae55fc384b721b2863a22ee328c33dc3b1d5a1e0af9a6"),
    MIT_READER_PDF: (74_235, "84ce42542ed58e102c736dacc02b69cf16ab264a577d689d2fe5f7a24ba37d75"),
    MIT_BROWSER_QA: (1_584, "b98ac5b2ea7df5b5d7b1263595b777269db1acc9c996fe7135a338366fb2d64d"),
    MIT_VISUAL_QA: (2_342, "9643896538a3704626d100c3775e3329bf082feda0e981977593f7ff6d25c680"),
    MIT_REREVIEW: (4_104, "dab732ea3b5096ee9d186775aca9064781e0026e15ea8943c2c8e637e6a64afb"),
    MIT_REPORT: (6_086, "6a8eab2cb69bf1403a8da3f9fbcc40f482c4b9a18e3ebbba24ac82ccee989257"),
    MIT_VALIDATOR: (25_152, "88ef1aa2e81c7a31b1a044e28e42805d53da90930aab5cca3eb776db7a01370e"),
}

EXPECTED_LEDGER_EVENTS = {
    "O015-MIT-SEM-0005": {
        "event_id": "O015-MIT-SEM-0005",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF pages 23-26 and 28; source/en/mit-06-lecture-2-convex-foundations-semantic-witness.md",
        "surface": "Function-type arrows in Lecture 2",
        "source_issue": "Several declarations use the element-mapping arrow in expressions that state only a function's domain and codomain, repeating the notation issue already observed on source page 4.",
        "target_action": "Preserved the printed mapsto arrows in the English semantic witness, normalized them to right arrows in the learner-facing Indonesian type declarations, and disclosed the recurring normalization in the edition notice.",
        "class": "determined_notation_correction",
    },
    "O015-MIT-SEM-0006": {
        "event_id": "O015-MIT-SEM-0006",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF page 23; source/en/mit-06-lecture-2-convex-foundations-semantic-witness.md",
        "surface": "Strict-convexity interpolation parameter",
        "source_issue": "Immediately after defining convexity with parameter alpha, the printed strict-convexity sentence switches to the Latin letter a even though it refers to the same interpolation parameter.",
        "target_action": "Preserved the printed a in the English semantic witness, used alpha in the learner-facing Indonesian sentence, and disclosed the determined symbol correction in the edition notice.",
        "class": "determined_notation_consistency_correction",
    },
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
    return sha256(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def record_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "".join(canonical_json(record) + "\n" for record in sorted(records, key=lambda item: item["id"]))
    return sha256(payload.encode("utf-8"))


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
    payload = ("\n".join(lines[start : end + 1]) + "\n").encode("utf-8")
    return start + 1, end + 1, len(payload), sha256(payload)


def strip_workflow_jsonl(raw: bytes) -> bytes:
    kept: list[bytes] = []
    for line in raw.splitlines(keepends=True):
        if json.loads(line.decode("utf-8")).get("responsible_workflow") != WORKFLOW:
            kept.append(line)
    return b"".join(kept)


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
        raise ValueError(f"{context} JSONL is not the protected 1,605-record baseline")
    if (len(csv_bytes), sha256(csv_bytes)) != BASELINE_CSV:
        raise ValueError(f"{context} CSV is not the protected 1,605-record baseline")


def stage_backend(jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    staged: list[Path] = []
    try:
        for destination, data in ((JSONL_PATH, jsonl_bytes), (CSV_PATH, csv_bytes)):
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.mit-l06-", suffix=".stage", dir=BACKEND, delete=False
            ) as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append(Path(handle.name))
        if staged[0].read_bytes() != jsonl_bytes or staged[1].read_bytes() != csv_bytes:
            raise ValueError("staged backend readback differs before replacement")
        os.replace(staged[0], JSONL_PATH)
        staged.pop(0)
        os.replace(staged[0], CSV_PATH)
        staged.pop(0)
    finally:
        for path in staged:
            path.unlink(missing_ok=True)


def ledger_events() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if file_info(MIT_LEDGER) != LEDGER_IDENTITY:
        raise ValueError("L06 correction snapshot identity differs")
    matches: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {
        event_id: [] for event_id in EXPECTED_LEDGER_EVENTS
    }
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), start=1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id in matches:
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
            matches[event_id].append((event, binding))
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for event_id, found in matches.items():
        if len(found) != 1:
            raise ValueError(f"expected exactly one {event_id} ledger event, found {len(found)}")
        event, binding = found[0]
        if event != EXPECTED_LEDGER_EVENTS[event_id]:
            raise ValueError(f"{event_id} differs from the admitted exact event")
        result[event_id] = (event, binding)
    return result


def load_qa_evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    visual = json.loads((ROOT / MIT_VISUAL_QA).read_text(encoding="utf-8"))
    expected_boundary = {
        "copied_source_graphics": 0,
        "nested_items": 17,
        "next_heading": "LECTURE 3 - LECTURE OUTLINE",
        "next_source_page": 29,
        "source_displays": 12,
        "source_figures": 5,
        "source_items": 32,
        "source_pdf_pages": SOURCE_PAGES,
    }
    if report.get("result") != "pass" or report.get("errors") != []:
        raise ValueError("MIT L06 validation report is not passing")
    if report.get("boundary") != expected_boundary:
        raise ValueError("MIT L06 validation boundary differs")
    if report.get("formula_sequence_match") is not True:
        raise ValueError("MIT L06 formula sequence is not validated")
    if report.get("source_page_text_sha256") != {
        str(page): identity[1] for page, identity in SOURCE_TEXT_FINGERPRINTS.items()
    }:
        raise ValueError("MIT L06 source-page text fingerprints differ")
    build = report.get("build", {})
    expected_build_pair = [file_info(MIT_HTML)[1], file_info(MIT_READER_PDF)[1]]
    if (
        build.get("command") != RECEIPT_BUILD_COMMAND
        or build.get("deterministic_rebuilds") != 2
        or build.get("rebuild_hashes") != [expected_build_pair, expected_build_pair]
        or [build.get("html_sha256"), build.get("pdf_sha256")] != expected_build_pair
    ):
        raise ValueError("MIT L06 deterministic-build evidence differs")
    if browser.get("result") != "pass" or visual.get("result") != "pass":
        raise ValueError("MIT L06 browser/visual evidence is not passing")
    if (browser.get("html", {}).get("bytes"), browser.get("html", {}).get("sha256")) != file_info(MIT_HTML):
        raise ValueError("MIT L06 browser receipt binds stale HTML")
    if (visual.get("surface", {}).get("bytes"), visual.get("surface", {}).get("sha256")) != file_info(MIT_READER_PDF):
        raise ValueError("MIT L06 visual receipt binds stale PDF")
    if report.get("pdf", {}).get("render_sha256") != [item["sha256"] for item in visual.get("render", {}).get("files", [])]:
        raise ValueError("MIT L06 render hash sequence differs between receipts")
    for item in report.get("files", {}).values():
        path = item.get("path")
        if path and file_info(path) != (item.get("bytes"), item.get("sha256")):
            raise ValueError(f"MIT L06 validation report binds stale bytes: {path}")
    rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
    for path in (MIT_TARGET, MIT_HTML, MIT_READER_PDF):
        if file_info(path)[1] not in rereview:
            raise ValueError(f"MIT L06 rereview does not bind {path}")
    if "P1=0, P2=0, P3=0" not in rereview:
        raise ValueError("MIT L06 rereview severity disposition differs")
    return report, browser, visual


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema":
        raise ValueError("backend schema identity differs")
    if file_info(MIT_PDF) != SOURCE_PDF_IDENTITY:
        raise ValueError("MIT authority PDF identity differs")
    for path, expected_identity in FINAL_READER_IDENTITIES.items():
        if file_info(path) != expected_identity:
            raise ValueError(f"final reader identity differs: {path}")
    report, browser, visual = load_qa_evidence()
    events = ledger_events()

    incoming_jsonl = JSONL_PATH.read_bytes()
    incoming_csv = CSV_PATH.read_bytes()
    incoming_records = [json.loads(line) for line in incoming_jsonl.decode("utf-8").splitlines() if line]
    incoming_rows = list(csv.DictReader(io.StringIO(incoming_csv.decode("utf-8", errors="strict"))))
    if [json.loads(row["record_json"]) for row in incoming_rows] != incoming_records:
        raise ValueError("incoming CSV projection differs from JSONL")
    if len({record["id"] for record in incoming_records}) != len(incoming_records):
        raise ValueError("incoming backend has duplicate IDs")

    records = [record for record in incoming_records if record.get("responsible_workflow") != WORKFLOW]
    already_applied = len(records) != len(incoming_records)
    if already_applied:
        assert_raw_baseline(strip_workflow_jsonl(incoming_jsonl), strip_workflow_csv(incoming_csv), "workflow-stripped incoming")
    else:
        assert_raw_baseline(incoming_jsonl, incoming_csv, "incoming")
    if (
        len(records) != BASELINE_RECORD_COUNT
        or id_set_sha256(records) != BASELINE_ID_SET_SHA256
        or record_set_sha256(records) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("stripped backend record set differs from protected baseline")

    baseline_ids = {record["id"] for record in records}
    new_records: list[dict[str, Any]] = []
    new_ids: set[str] = set()

    def add(record: dict[str, Any]) -> None:
        if record["id"] in baseline_ids or record["id"] in new_ids:
            raise ValueError(f"stable-ID collision: {record['id']}")
        new_ids.add(record["id"])
        new_records.append(record)

    segment_ids = {page: f"d90.mit.ocw-6.253.l06.p{page:03d}" for page in SOURCE_PAGES}
    source_items = [
        f"src-mit-l06-p{page:03d}-i{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)
    ]
    target_items = [item.replace("src-mit-", "d90-mit-", 1) for item in source_items]
    display_pairs = [
        (page, index)
        for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
    ]

    unit = common("unit", MIT_L06_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 6,
        "source_local_id": "lecture-2-pages-20-28",
        "source_local_label": "Lecture 2 - Convex Foundations",
        "target_local_label": "Kuliah 2 - Landasan Konveks",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": SOURCE_PAGES,
        "next_source_page": 29,
        "next_source_heading": "LECTURE 3 - LECTURE OUTLINE",
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 32,
        "nested_source_item_count": 17,
        "source_item_ids": source_items,
        "target_item_ids": target_items,
        "source_display_count": 12,
        "source_display_ids": [f"src-mit-l06-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "target_display_ids": [f"d90-mit-l06-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "source_figure_count": 5,
        "source_figure_ids": [f"src-mit-l06-p{page:03d}-f001" for page in FIGURE_PANELS],
        "target_figure_ids": [f"d90-mit-l06-p{page:03d}-f001" for page in FIGURE_PANELS],
        "source_figure_panel_count": sum(FIGURE_PANELS.values()),
        "copied_source_graphics": 0,
        "correction_event_ids": sorted(EXPECTED_LEDGER_EVENTS),
        "canonical_build_command": CANONICAL_BUILD_COMMAND,
    })
    add(unit)

    for order, page in enumerate(SOURCE_PAGES, start=1):
        source_anchor = f"src-mit-l06-p{page:03d}"
        target_anchor = f"d90-mit-l06-p{page:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
        record = common("segment", segment_ids[page], "visually_checked")
        record.update({
            "unit_id": MIT_L06_UNIT_ID,
            "order": order,
            "source_edition_id": MIT_WITNESS_EDITION_ID,
            "target_edition_id": MIT_TARGET_EDITION_ID,
            "source_path": MIT_WITNESS,
            "source_line_start": source_slice[0],
            "source_line_end": source_slice[1],
            "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3],
            "source_anchor": source_anchor,
            "source_item_ids": [f"{source_anchor}-i{index:03d}" for index in range(1, PAGE_ITEMS[page] + 1)],
            "target_path": MIT_TARGET,
            "target_line_start": target_slice[0],
            "target_line_end": target_slice[1],
            "target_bytes": target_slice[2],
            "target_content_sha256": target_slice[3],
            "target_anchor": target_anchor,
            "target_item_ids": [f"{target_anchor}-i{index:03d}" for index in range(1, PAGE_ITEMS[page] + 1)],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "visually_checked",
            "rights_id": "rights.o015-mit-id-pilot",
            "source_pdf_path": MIT_PDF,
            "source_pdf_page": page,
            "source_pdf_sha256": SOURCE_PDF_IDENTITY[1],
            "source_pdf_pages_total": 340,
            "source_page_text_bytes": SOURCE_TEXT_FINGERPRINTS[page][0],
            "source_page_text_sha256": SOURCE_TEXT_FINGERPRINTS[page][1],
            "source_page_render_bytes": SOURCE_RENDER_FINGERPRINTS[page][0],
            "source_page_render_sha256": SOURCE_RENDER_FINGERPRINTS[page][1],
            "source_page_render_method": "MuPDF mutool 1.23.0 draw -F png -c gray -r 96",
            "source_item_count": PAGE_ITEMS[page],
            "nested_source_item_count": PAGE_NESTED[page],
            "source_display_count": PAGE_DISPLAYS[page],
            "source_figure_count": 1 if page in FIGURE_PANELS else 0,
            "source_figure_panel_count": FIGURE_PANELS.get(page, 0),
            "anchor_mapping_rule": "replace src-mit- prefix with d90-mit- prefix",
        })
        add(record)

    for global_order, (page, index) in enumerate(display_pairs, start=1):
        source_anchor = f"src-mit-l06-p{page:03d}-d{index:03d}"
        target_anchor = f"d90-mit-l06-p{page:03d}-d{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
        record_id = f"surface.mit.l06.formula.p{page:03d}.d{index:03d}"
        record = common("learning_surface", record_id, "present")
        record.update({
            "unit_id": MIT_L06_UNIT_ID,
            "surface_type": "display_formula",
            "presence": "present",
            "formula_sequence_order": global_order,
            "page_formula_order": index,
            "formula_label": DISPLAY_LABELS[(page, index)],
            "source_pdf_page": page,
            "related_segment_ids": [segment_ids[page]],
            "source_path": MIT_WITNESS,
            "source_anchor": source_anchor,
            "source_line_start": source_slice[0],
            "source_line_end": source_slice[1],
            "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3],
            "target_path": MIT_TARGET,
            "target_anchor": target_anchor,
            "target_line_start": target_slice[0],
            "target_line_end": target_slice[1],
            "target_bytes": target_slice[2],
            "target_content_sha256": target_slice[3],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "formula_sequence_match": True,
            "rights_id": "rights.o015-mit-id-pilot",
        })
        if (page, index) == (26, 2):
            record["literal_language_normalization"] = {"source": "or", "target": "atau"}
        add(record)

    for page, panel_count in FIGURE_PANELS.items():
        source_anchor = f"src-mit-l06-p{page:03d}-f001"
        target_anchor = f"d90-mit-l06-p{page:03d}-f001"
        source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
        record_id = f"surface.mit.l06.figure-description.p{page:03d}.f001"
        record = common("learning_surface", record_id, "present_with_limitation")
        record.update({
            "unit_id": MIT_L06_UNIT_ID,
            "surface_type": "semantic_figure_description",
            "presence": "present_with_limitation",
            "figure_label": FIGURE_LABELS[page],
            "source_pdf_page": page,
            "panel_count": panel_count,
            "related_segment_ids": [segment_ids[page]],
            "source_path": MIT_WITNESS,
            "source_anchor": source_anchor,
            "source_line_start": source_slice[0],
            "source_line_end": source_slice[1],
            "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3],
            "target_path": MIT_TARGET,
            "target_anchor": target_anchor,
            "target_line_start": target_slice[0],
            "target_line_end": target_slice[1],
            "target_bytes": target_slice[2],
            "target_content_sha256": target_slice[3],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "source_graphic_disposition": "omitted-source-graphic",
            "semantic_description_preserved": True,
            "copied_source_graphic_bytes": 0,
            "rights_id": "rights.o015-mit-id-pilot",
        })
        add(record)

    correction_specs = {
        "O015-MIT-SEM-0005": {
            "record_id": "correction.o015-mit-sem-0005",
            "pages": [23, 24, 25, 26, 28],
            "source_locator": "complete-notes PDF pages 23-26 and 28; function type declarations",
            "witness_locators": [
                f"{MIT_WITNESS}#src-mit-l06-p023-i001",
                f"{MIT_WITNESS}#src-mit-l06-p024-i001",
                f"{MIT_WITNESS}#src-mit-l06-p025-i001",
                f"{MIT_WITNESS}#src-mit-l06-p026-i003",
                f"{MIT_WITNESS}#src-mit-l06-p028-i002",
            ],
            "target_locators": [
                f"{MIT_TARGET}#d90-mit-l06-p023-i001",
                f"{MIT_TARGET}#d90-mit-l06-p024-i001",
                f"{MIT_TARGET}#d90-mit-l06-p025-i001",
                f"{MIT_TARGET}#d90-mit-l06-p026-i003",
                f"{MIT_TARGET}#d90-mit-l06-p028-i002",
            ],
        },
        "O015-MIT-SEM-0006": {
            "record_id": "correction.o015-mit-sem-0006",
            "pages": [23],
            "source_locator": "complete-notes PDF page 23; strict-convexity sentence",
            "witness_locators": [f"{MIT_WITNESS}#src-mit-l06-p023-i001"],
            "target_locators": [f"{MIT_TARGET}#d90-mit-l06-p023-i001"],
        },
    }
    for event_id, spec in correction_specs.items():
        event, binding = events[event_id]
        correction = common("correction", spec["record_id"], "applied_in_admitted_reader")
        correction.update({
            "source_event_id": event_id,
            "source_edition_id": MIT_SOURCE_EDITION_ID,
            "affected_unit_ids": [MIT_L06_UNIT_ID],
            "affected_segment_ids": [segment_ids[page] for page in spec["pages"]],
            "source_path": MIT_PDF,
            "source_pdf_pages": spec["pages"],
            "source_locator": spec["source_locator"],
            "witness_locators": spec["witness_locators"],
            "target_locators": spec["target_locators"],
            "surface": event["surface"],
            "source_issue": event["source_issue"],
            "target_action": event["target_action"],
            "correction_class": event["class"],
            "disposition": "applied_in_admitted_reader",
            "shared_ledger_state": "integrated",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.mit.l06.adverse-ledger",
            **binding,
        })
        add(correction)

    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l06.boundary-census", "boundary_census", MIT_CENSUS, "rights.o015-mit-pilot-build-qa", {"source_pdf_pages": SOURCE_PAGES, "next_source_page": 29}),
        ("artifact.mit.l06.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"source_pdf_pages": SOURCE_PAGES, "official_editable_source": False, "source_item_count": 32, "nested_source_item_count": 17, "source_display_count": 12, "source_figure_description_count": 5}),
        ("artifact.mit.l06.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": SOURCE_PAGES, "source_item_count": 32, "nested_source_item_count": 17, "source_display_count": 12, "source_figure_description_count": 5, "correction_event_ids": sorted(EXPECTED_LEDGER_EVENTS)}),
        ("artifact.mit.l06.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "MathML", "source_pages": 9, "source_displays": 12, "source_figures": 5, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l06.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": 4, "page_size": "A4", "tagged": False, "searchable": True, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l06.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5 and LuaLaTeX", "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND}),
        ("artifact.mit.l06.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l06.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass", "errors": []}),
        ("artifact.mit.l06.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "live_viewport_measurement": True}),
        ("artifact.mit.l06.visual-qa", "visual_qa_report", MIT_VISUAL_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "pages": 4}),
        ("artifact.mit.l06.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.mit.l06.adverse-ledger", "correction_ledger", MIT_LEDGER, "rights.o015-mit-pilot-build-qa", {"source_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "ledger_identity_required": True, "event_bindings": [events[event_id][1] for event_id in sorted(events)]}),
        ("artifact.mit.l06.css", "html_stylesheet", MIT_CSS, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l06.pdf-preamble", "pdf_preamble", MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l06.pdf-filter", "pandoc_lua_filter", MIT_FILTER, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l06.before-body", "html_include", MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l06.after-body", "html_include", MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.o015.backend-generator-mit-l06", "backend_generator", "qa/extend_backend_mit_l06.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "protected_baseline_record_count": BASELINE_RECORD_COUNT}),
        ("artifact.o015.backend-validator-mit-l06", "backend_validator", "qa/validate_backend_mit_l06.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "independent_validation_runs_required": 2}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l06.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.complete-notes-pdf", "artifact.mit.l06.boundary-census", "artifact.mit.l06.semantic-witness"], "authority_pdf_pages": 340, "boundary_pages": SOURCE_PAGES, "next_source_page": 29, "next_source_page_text_sha256": SOURCE_TEXT_FINGERPRINTS[29][1]}),
        ("qa.o015.mit-l06.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l06.semantic-witness", "artifact.mit.l06.target-source", "artifact.mit.l06.validation"], "official_editable_source": False, "source_items": 32, "nested_source_items": 17, "source_figures": 5}),
        ("qa.o015.mit-l06.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l06.validation", "artifact.mit.l06.boundary-census"], "source_page_map": [[page, page] for page in SOURCE_PAGES], "item_counts": {str(page): PAGE_ITEMS[page] for page in SOURCE_PAGES}, "nested_item_counts": {str(page): PAGE_NESTED[page] for page in SOURCE_PAGES}, "display_counts": {str(page): PAGE_DISPLAYS[page] for page in SOURCE_PAGES}, "figure_panel_counts": {str(page): FIGURE_PANELS.get(page, 0) for page in SOURCE_PAGES}}),
        ("qa.o015.mit-l06.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l06.semantic-witness", "artifact.mit.l06.target-source", "artifact.mit.l06.validation", "artifact.mit.l06.independent-rereview"], "source_math_nodes": 151, "target_math_nodes": 151, "display_formulas": 12, "formula_sequence_match": True, "literal_language_normalization": {"source": "or", "target": "atau"}}),
        ("qa.o015.mit-l06.figures", "figure_description_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l06.semantic-witness", "artifact.mit.l06.target-source", "artifact.mit.l06.validation", "artifact.mit.l06.visual-qa"], "source_figure_blocks": 5, "source_figure_panels": 10, "semantic_figure_descriptions": 5, "copied_source_graphics": 0, "reader_images": 0}),
        ("qa.o015.mit-l06.corrections", "correction_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l06.adverse-ledger", "artifact.mit.l06.semantic-witness", "artifact.mit.l06.target-source", "artifact.mit.l06.independent-rereview", "artifact.mit.l06.validation"], "source_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "correction_record_ids": ["correction.o015-mit-sem-0005", "correction.o015-mit-sem-0006"], "silent_normalization": False}),
        ("qa.o015.mit-l06.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l06.builder", "artifact.mit.l06.target-html", "artifact.mit.l06.target-pdf", "artifact.mit.l06.validation"], "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND, "deterministic_rebuilds": 2, "html_sha256": file_info(MIT_HTML)[1], "pdf_sha256": file_info(MIT_READER_PDF)[1], "toolchain": "Pandoc HTML5 and LuaLaTeX"}),
        ("qa.o015.mit-l06.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l06.target-html", "artifact.mit.l06.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": {"h1": 1, "h2": 10}, "math_nodes": 151, "display_math_nodes": 12, "images": 0, "source_pages": 9, "source_items": 32, "source_figures": 5, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l06.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l06.browser-qa", "artifact.mit.l06.target-html"], "desktop_viewport": [1280, 720], "mobile_viewport": [390, 844], "horizontal_overflow": False, "display_math_overflow": False, "live_measurement": True, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l06.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l06.target-pdf", "artifact.mit.l06.validation"], "pages": 4, "page_size": "A4", "lang": "id-ID", "searchable": True, "tagged": False, "images": 0, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l06.visual", "visual", "pass", {"witness_artifact_ids": ["artifact.mit.l06.visual-qa", "artifact.mit.l06.target-pdf"], "pages": 4, "all_pages_visually_inspected": True, "render_tool": "pdftoppm", "render_sha256": report["pdf"]["render_sha256"]}),
        ("qa.o015.mit-l06.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l06.target-html", "artifact.mit.l06.target-pdf", "artifact.mit.l06.browser-qa", "artifact.mit.l06.visual-qa"], "primary_surface": "semantic_html", "html_static_structure_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"]}),
        ("qa.o015.mit-l06.semantic-rereview", "independent_semantic_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l06.independent-rereview", "artifact.mit.l06.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l06.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded."}),
        ("qa.o015.mit-l06.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l06.boundary-census", "artifact.mit.l06.semantic-witness", "artifact.mit.l06.target-source"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa", "o015-mit-l01-backend-tooling"], "source_graphics_in_boundary": 5, "source_graphics_redistributed": 0, "semantic_figure_descriptions": 5, "license": "CC BY-NC-SA 4.0", "change_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "non_endorsement": True}),
        ("qa.o015.mit-l06.csv-losslessness", "csv_losslessness", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l06", "artifact.o015.backend-validator-mit-l06"], "projection": "record_json is canonical JSON for each JSONL record", "utf8_strict": True, "row_order_matches_jsonl": True}),
        ("qa.o015.mit-l06.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l06", "artifact.o015.backend-validator-mit-l06", "artifact.o015.source-authority", "artifact.o015.component-rights"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_baseline_reconstruction_required": True, "independent_validation_runs_required": 2}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        status = "passed" if result == "pass" else result
        record = common("qa_event", record_id, status)
        record.update({"event_type": event_type, "result": result, "unit_id": MIT_L06_UNIT_ID, **extra})
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l06", "contains", MIT_ROOT_UNIT_ID, MIT_L06_UNIT_ID, "Sixth admitted MIT source-order boundary, complete-notes pages 20-28."),
        ("relation.mit.witness-edition-contains-l06", "contains", MIT_WITNESS_EDITION_ID, MIT_L06_UNIT_ID, "Page-addressed English semantic witness for pages 20-28."),
        ("relation.mit.target-edition-contains-l06", "contains", MIT_TARGET_EDITION_ID, MIT_L06_UNIT_ID, "Built Indonesian semantic derivative for pages 20-28."),
        ("relation.mit.witness-adapts-authority-pdf-l06", "adapts", "artifact.mit.l06.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes PDF pages 20-28."),
        ("relation.mit.target-translates-witness-l06", "translates", "artifact.mit.l06.target-source", "artifact.mit.l06.semantic-witness", "Page/list/formula translation with disclosed corrections O015-MIT-SEM-0005 and 0006."),
        ("relation.mit.html-adapts-target-l06", "adapts", "artifact.mit.l06.target-html", "artifact.mit.l06.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l06", "adapts", "artifact.mit.l06.target-pdf", "artifact.mit.l06.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.browser-qa-depends-on-html-l06", "depends-on", "artifact.mit.l06.browser-qa", "artifact.mit.l06.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.visual-qa-depends-on-pdf-l06", "depends-on", "artifact.mit.l06.visual-qa", "artifact.mit.l06.target-pdf", "Rendered four-page visual QA evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l06", "depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.browser-qa", "Validation binds browser evidence."),
        ("relation.mit.validation-depends-on-visual-qa-l06", "depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.visual-qa", "Validation binds rendered visual evidence."),
        ("relation.mit.validation-depends-on-rereview-l06", "depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.independent-rereview", "Validation binds independent rereview."),
        ("relation.mit.validation-depends-on-boundary-l06", "depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.boundary-census", "Validation binds the frozen pages 20-28 boundary."),
        ("relation.mit.validation-depends-on-ledger-l06", "depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.adverse-ledger", "Validation binds the two disclosed correction events."),
        ("relation.mit.backend-generator-depends-on-validation-l06", "depends-on", "artifact.o015.backend-generator-mit-l06", "artifact.mit.l06.validation", "Backend admission requires passing content QA."),
        ("relation.mit.backend-validator-depends-on-generator-l06", "depends-on", "artifact.o015.backend-validator-mit-l06", "artifact.o015.backend-generator-mit-l06", "Independent fail-closed validation of generated records."),
    ]
    for page in SOURCE_PAGES:
        relation_specs.append((f"relation.mit.l06.contains-p{page:03d}", "contains", MIT_L06_UNIT_ID, segment_ids[page], "Ordered one-page semantic segment."))
    for page, index in display_pairs:
        relation_specs.append((
            f"relation.mit.l06.formula-p{page:03d}-d{index:03d}-depends-on-p{page:03d}",
            "depends-on",
            f"surface.mit.l06.formula.p{page:03d}.d{index:03d}",
            segment_ids[page],
            "Exact source/target display block occurs in this page segment.",
        ))
    for page in FIGURE_PANELS:
        relation_specs.append((
            f"relation.mit.l06.figure-description-p{page:03d}-f001-illustrates-p{page:03d}",
            "illustrates",
            f"surface.mit.l06.figure-description.p{page:03d}.f001",
            segment_ids[page],
            "Text-only semantic description replaces the omitted source graphic.",
        ))
    for event_id in sorted(EXPECTED_LEDGER_EVENTS):
        suffix = event_id.rsplit("-", 1)[-1].lower()
        relation_specs.append((
            f"relation.mit.l06.correction-{suffix}-depends-on-ledger",
            "depends-on",
            f"correction.o015-mit-sem-{suffix}",
            "artifact.mit.l06.adverse-ledger",
            "Correction record is bound to the exact raw ledger event.",
        ))

    relation_triples: set[tuple[str, str, str]] = set()
    for record_id, relation_type, source_id, target_id, note in relation_specs:
        triple = (relation_type, source_id, target_id)
        if triple in relation_triples:
            raise ValueError(f"duplicate new relation triple: {triple}")
        relation_triples.add(triple)
        record = common("relation", record_id, "current")
        record.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        add(record)

    records.extend(new_records)
    by_id = {record["id"]: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate IDs after L06 extension")
    for record in records:
        for field in schema["required_common"] + schema["required_by_entity"].get(record["entity_type"], []):
            if field not in record:
                raise ValueError(f"{record['id']}: missing required field {field}")
        for field in schema["reference_fields"]:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for target in values:
                if isinstance(target, str) and target not in by_id:
                    raise ValueError(f"{record['id']}: unresolved {field} -> {target}")

    entity_rank = {entity_type: rank for rank, entity_type in enumerate(schema["entity_order"])}
    records.sort(key=lambda record: (entity_rank[record["entity_type"]], record["id"]))
    jsonl_bytes = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    csv_buffer = io.StringIO(newline="")
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(schema["csv_columns"])
    for record in records:
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)])
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    assert_raw_baseline(strip_workflow_jsonl(jsonl_bytes), strip_workflow_csv(csv_bytes), "workflow-stripped output")
    stage_backend(jsonl_bytes, csv_bytes)
    if JSONL_PATH.read_bytes() != jsonl_bytes or CSV_PATH.read_bytes() != csv_bytes:
        raise ValueError("backend readback differs after replacement")

    output = {
        "already_applied_on_entry": already_applied,
        "protected_baseline": {
            "record_count": BASELINE_RECORD_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]},
            "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "raw_bytes_reconstructed_exactly": True,
        },
        "new_record_count": len(new_records),
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
        "new_ids_sha256": sha256(("\n".join(sorted(new_ids)) + "\n").encode("utf-8")),
        "record_count": len(records),
        "jsonl": {"bytes": len(jsonl_bytes), "sha256": sha256(jsonl_bytes)},
        "csv": {"bytes": len(csv_bytes), "sha256": sha256(csv_bytes)},
        "unit_id": MIT_L06_UNIT_ID,
        "segment_count": len(segment_ids),
        "formula_count": len(display_pairs),
        "figure_description_count": len(FIGURE_PANELS),
        "correction_count": len(EXPECTED_LEDGER_EVENTS),
        "canonical_build_command": CANONICAL_BUILD_COMMAND,
        "result": "pass",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
