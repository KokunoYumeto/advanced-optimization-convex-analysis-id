#!/usr/bin/env python3
"""Stage the additive MIT 6.253 Lecture 5 backend projection (pages 50-63).

The 1,957-record L08 backend is a byte-protected baseline.  This generator
removes only its own prior L09 projection, proves exact baseline
reconstruction, validates the complete reader evidence, and deterministically
builds the L09 projection.  It does not overwrite the canonical backend unless
``--write-canonical`` is supplied explicitly; use ``--output-dir`` for staged
admission.  ``--preflight`` validates authority, topology, anchors, corrections,
and the protected baseline without requiring the final reader QA receipts.
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

RECORDED_AT = "2026-08-24T12:00:00Z"
WORKFLOW = "o015-mit-l09-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 1_957
BASELINE_JSONL = (1_441_643, "0779f8bc03d437da72adafe2daf99c820d5849f0e14b630a0c3bd6f512b10085")
BASELINE_CSV = (1_727_978, "ed209ae9325d27b5e1360b59804833e91ab014c821741f2f52badfc5f0eda836")
BASELINE_ID_SET_SHA256 = "0a83c8e41324ebb19a9473b61dffc3091330e66d5b6ebba5a46f0079df20c749"
BASELINE_RECORD_SET_SHA256 = "7e127fc2e2fe3e300af69a7127337786fa551cf181caa1d0a31a836212434864"

EXPECTED_NEW_RECORD_COUNT = 142
EXPECTED_ENTITY_COUNTS = Counter({
    "unit": 1,
    "segment": 14,
    "learning_surface": 28,
    "correction": 8,
    "artifact": 19,
    "qa_event": 17,
    "relation": 55,
})

MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L09_UNIT_ID = "unit.mit.ocw-6.253.l09"
SOURCE_PAGES = list(range(50, 64))

PAGE_ITEMS = {50: 4, 51: 3, 52: 1, 53: 1, 54: 5, 55: 3, 56: 1, 57: 2, 58: 3, 59: 5, 60: 4, 61: 3, 62: 1, 63: 5}
PAGE_NESTED = {50: 0, 51: 0, 52: 5, 53: 0, 54: 0, 55: 2, 56: 2, 57: 0, 58: 3, 59: 0, 60: 2, 61: 3, 62: 0, 63: 0}
PAGE_DISPLAYS = {50: 0, 51: 1, 52: 2, 53: 2, 54: 2, 55: 0, 56: 2, 57: 0, 58: 2, 59: 4, 60: 0, 61: 0, 62: 3, 63: 1}
FIGURE_PANELS = {51: 1, 53: 1, 54: 1, 55: 1, 57: 6, 58: 1, 60: 1}
EXAMPLES = {(58, 3): "positive-semidefinite quadratic recession and constancy cones", (63, 4): "positive-definite quadratic existence and uniqueness application"}

DISPLAY_LABELS = {
    (51, 1): "defining condition for a recession direction of a convex set",
    (52, 1): "recession cone of a binary intersection",
    (52, 2): "recession cone of an arbitrary nonempty intersection",
    (53, 1): "normalized sequence definitions in the proof of part (b)",
    (53, 2): "segment decomposition and convergence of the normalized directions",
    (54, 1): "lineality space as the two-sided recession cone",
    (54, 2): "orthogonal Minkowski decomposition by the lineality space",
    (56, 1): "common recession cone of all nonempty sublevel sets",
    (56, 2): "horizontal epigraph recession directions",
    (58, 1): "positive-semidefinite quadratic example",
    (58, 2): "recession cone and constancy space of the quadratic example",
    (59, 1): "recession and constancy spaces through the recession function and epigraph",
    (59, 2): "secant-slope supremum and limit formula",
    (59, 3): "gradient-limit formula for a differentiable convex function",
    (59, 4): "sum and pointwise-supremum recession-function calculus",
    (62, 1): "nested constrained sublevel sets approaching the optimal value",
    (62, 2): "minimizer set as an intersection of constrained sublevel sets",
    (62, 3): "convex existence and compactness criterion",
    (63, 1): "proper sum of closed proper convex functions",
}

FIGURE_LABELS = {
    51: "recession cone of a convex set",
    53: "geometric construction in the proof of the recession cone theorem",
    54: "lineality and orthogonal decomposition",
    55: "epigraph, sublevel sets, and recession directions",
    57: "six asymptotic descent behaviors of a convex function",
    58: "common recession cone of nested sublevel sets",
    60: "convexity chord argument for local and global minimizers",
}

SOURCE_TEXT_FINGERPRINTS = {
    50: (289, "595b3d566a6d820573632a5dc853afb2c0cf8474fab8693a57d84ff33335ae63"),
    51: (628, "29ea48091d0c0854adeefc2cee9ff13514e0d0f8e764102e4cef02cd43346a4c"),
    52: (761, "8c6f781da342b06c073fc28c3c3e709e6806da27fc41b7af41bb1a75bdc4b00e"),
    53: (1_111, "d3d5afc97dd3e68df351ea9c9bf650ef22211e423973655d5e5bf7e9730c8166"),
    54: (980, "7f38485ab8f3487a4048bacc110fa6a137c39f3bfd034fcda3133c39b378594c"),
    55: (968, "b0e4296e764c3f5599b607b8a4ec4847627c349db28c45fa9ae534a3a34aa2fa"),
    56: (665, "d6a4b532b62933feb3f40d77eb4abadc212bd984a1ed0c27da756677bcc4c147"),
    57: (1_667, "a34def3e962e6d71573a7a45dc48ac594c792bcbc87d77d1720daaa9f1e4d6ac"),
    58: (902, "6203cc3ebafa733f38fa3c753f5c99af25620209cb4beeaa2f88ff9ed122e947"),
    59: (942, "ca166a557ed87c168774a5ecc542aef74009fa53a199b0ab700633b3c56cc363"),
    60: (876, "218eb580f08974fa64649727fd0a03e1425967c58e097ac43b2713329450c10e"),
    61: (809, "a96ceb4046bb0bc9b5aa3f3afbab02ed758a9a377afc99249f8f188ce20bce1f"),
    62: (1_048, "62f283dd5015d2ea7a9302a225d7813d7f0a399330d0cbf8ae3b236d4239ad91"),
    63: (852, "c404f9420102103e3ff43757dcdeecf99a9ddf4947c0d5f08c27ee17166fe314"),
    64: (305, "20de895948a7967b9f1a52b44d4a6d4fafa26b8744b23ef9bb459aa566d69766"),
}

SOURCE_RENDER_FINGERPRINTS = {
    50: (21_450, "5dceaf64ba215ff48af8175a2249d5cc11246aca4e1d3964539c323cff5f95a2"),
    51: (56_137, "b66a1dea301d7ba61d1abb544feeba31172617f6db8997f8d19258cf6dd5dedf"),
    52: (48_320, "54053898ab67c83fa74fc713a421ca1308d8e23b612bf60f9a5b23f36417674f"),
    53: (50_988, "72b29cb179a539b9d3f973efc6bdc9a22dacc68c3081e500b26f9fe57ca4c9e2"),
    54: (60_911, "2e03eb3734ffaf54a20e789d5affec335bdbd0db3486551d7907162120a9ee07"),
    55: (45_344, "6614da5d3cc2d9435f2bfa8c983340451c6a0ae736c894e26e142b91fcb37c00"),
    56: (39_493, "3ed8df60ebea27f3ef26c8c86ded32c7ffb4f73f008bcb8d8ed7151ee5d40498"),
    57: (47_145, "2dbd1d5483caabaf9865eb5924cd030cb41d286e7ed23e1ffa02f4e771911951"),
    58: (66_756, "4643b578e2f2e6d3d00b3be73413b47ddfffb7bc0d284f4970c44823b393990f"),
    59: (47_022, "fe6b81f453ac1bff8bfc6c0b338d01e29e2a9d6acb0a53e3d3c1ead70aca0adb"),
    60: (55_850, "68be066aa2204a4456402c1bb3d7d566af90cc0353ad7854222e88e5a4eda64e"),
    61: (51_495, "c4f424c4994aeceeda78449be3465641ebb169756e77fc0433a1c16505b212ff"),
    62: (58_017, "1a6e724fcd9122a3a0cb93266ecda17d23c73a3bce690ada94ad2da92bb6604e"),
    63: (52_338, "083a06d31cac9f55addfbd7b29376cdc83f10f8e355eea98e8269174b10d6acc"),
}

MIT_PDF = "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
MIT_CENSUS = "00_control/MIT_L09_LECTURE_5_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/MIT_L09_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-09-lecture-5-recession-minima-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-09-kuliah-5-resesi-dan-minimum-id.md"
MIT_HTML = "output/html/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.pdf"
MIT_CSS = "source/id-ID/mit-l09.css"
MIT_PREAMBLE = "source/id-ID/mit-l09-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l09-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l09-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l09-after-body.html"
MIT_BUILDER = "qa/build_mit_l09.py"
MIT_VALIDATOR = "qa/validate_mit_l09.py"
MIT_REPORT = "qa/MIT_L09_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L09_BROWSER_QA.json"
MIT_VISUAL_QA = "qa/MIT_L09_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L09_INDEPENDENT_REREVIEW.md"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
CENSUS_IDENTITY = (19_753, "e4357023e0c2a6d4478adb904e9fec2789bc616f56bfba07d05789f74cc0cd85")
LEDGER_IDENTITY = (5_506, "e5ef98e4218d768cd51053e08d55c5ef44a44afa26237be652152eecd1052acc")
CANONICAL_BUILD_COMMAND = (
    "python qa/build_mit_l09.py --html-output "
    "output/html/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.html "
    "--pdf-output output/pdf/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.pdf"
)
RECEIPT_BUILD_COMMAND = "python qa/build_mit_l09.py --html-output <html> --pdf-output <pdf>"
EXPECTED_EVENT_IDS = tuple(f"O015-MIT-SEM-{number:04d}" for number in range(12, 20))

CORRECTION_SPECS = {
    "O015-MIT-SEM-0012": ([56, 58, 59, 60, 61, 62, 63], "function-type declarations"),
    "O015-MIT-SEM-0013": ([55], "monotonic behavior along a recession direction"),
    "O015-MIT-SEM-0014": ([57], "direction symbol below the six descent panels"),
    "O015-MIT-SEM-0015": ([59], "set-builder expression connecting recession cones"),
    "O015-MIT-SEM-0016": ([60], "local-minimizer radius quantifier"),
    "O015-MIT-SEM-0017": ([61], "feasibility in the extended Weierstrass theorem"),
    "O015-MIT-SEM-0018": ([61], "constrained-sublevel-set proof shorthand"),
    "O015-MIT-SEM-0019": ([60, 61, 62, 63], "minimizer point versus minimum value terminology"),
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
        raise ValueError(f"{context} JSONL is not the protected 1,957-record baseline")
    if (len(csv_bytes), sha256(csv_bytes)) != BASELINE_CSV:
        raise ValueError(f"{context} CSV is not the protected 1,957-record baseline")


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
        or record_set_sha256(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("stripped record set differs from the protected L08 baseline")
    return baseline, stripped_jsonl, stripped_csv


def ledger_events() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if file_info(MIT_LEDGER) != LEDGER_IDENTITY:
        raise ValueError("L09 correction snapshot identity differs")
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), start=1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id not in EXPECTED_EVENT_IDS or event_id in result:
            raise ValueError(f"unexpected or duplicate L09 correction event: {event_id}")
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
        raise ValueError("L09 correction event set differs")
    return result


def identity_tuple(record: dict[str, Any]) -> tuple[int, str]:
    return int(record.get("bytes", -1)), str(record.get("sha256", ""))


def load_qa_evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    visual = json.loads((ROOT / MIT_VISUAL_QA).read_text(encoding="utf-8"))
    expected_boundary = {
        "source_pdf_pages": SOURCE_PAGES,
        "next_source_page": 64,
        "next_heading": "LECTURE 6 - LECTURE OUTLINE",
        "source_items": 41,
        "nested_items": 17,
        "source_displays": 19,
        "source_figures": 7,
        "source_figure_panels": 12,
        "examples": 2,
        "copied_source_graphics": 0,
        "exercises": 0,
        "hints": 0,
        "answers": 0,
        "solutions": 0,
        "code_surfaces": 0,
        "interactive_surfaces": 0,
    }
    if report.get("result") != "pass" or report.get("errors") != [] or report.get("boundary") != expected_boundary:
        raise ValueError("MIT L09 content validation receipt is not a strict pass")
    if report.get("model_identification") != "OpenAI Codex gpt-5.6-sol, Ultra":
        raise ValueError("MIT L09 model identification differs")
    formulas = report.get("formula_inventory", {})
    if (
        formulas.get("witness_display_blocks") != 19
        or formulas.get("target_display_blocks") != 19
        or not re.fullmatch(r"[0-9a-f]{64}", str(formulas.get("witness_sequence_sha256", "")))
        or not re.fullmatch(r"[0-9a-f]{64}", str(formulas.get("target_sequence_sha256", "")))
    ):
        raise ValueError("MIT L09 formula inventory differs")
    authority = report.get("authority", {})
    expected_text = {str(page): value[1] for page, value in SOURCE_TEXT_FINGERPRINTS.items()}
    expected_bytes = {str(page): value[0] for page, value in SOURCE_TEXT_FINGERPRINTS.items()}
    if authority.get("source_page_text_sha256") != expected_text or authority.get("source_page_text_bytes") != expected_bytes:
        raise ValueError("MIT L09 source-page fingerprints differ")
    build = report.get("build", {})
    if build.get("command") != RECEIPT_BUILD_COMMAND or build.get("deterministic_rebuilds") != 2:
        raise ValueError("MIT L09 deterministic build contract differs")
    html_identity = file_info(MIT_HTML)
    pdf_identity = file_info(MIT_READER_PDF)
    rebuilds = build.get("rebuild_identities", [])
    expected_rebuild = {"html": list(html_identity), "pdf": list(pdf_identity)}
    if build.get("expected") != expected_rebuild:
        raise ValueError("MIT L09 expected build identities differ from canonical reader bytes")
    if rebuilds != [expected_rebuild, expected_rebuild]:
        raise ValueError("MIT L09 rebuild identities differ from canonical reader bytes")
    canonical = build.get("canonical", {})
    if canonical.get("status") != "bound" or identity_tuple(canonical.get("html", {})) != html_identity or identity_tuple(canonical.get("pdf", {})) != pdf_identity:
        raise ValueError("MIT L09 canonical build binding differs")
    html = report.get("html", {})
    if (
        html.get("lang") != "id-ID"
        or html.get("source_pages") != 14
        or html.get("source_items") != 41
        or html.get("source_displays") != 19
        or html.get("source_figures") != 7
        or html.get("display_math_nodes") != 19
        or html.get("images") != 0
        or html.get("media_or_embeds") != 0
        or html.get("form_controls") != 0
        or html.get("duplicate_ids") != []
        or html.get("unresolved_fragments") != []
    ):
        raise ValueError("MIT L09 HTML topology differs")
    pdf = report.get("pdf", {})
    page_boxes = pdf.get("page_size_points", [])
    if (
        pdf.get("pages", 0) < 1
        or len(page_boxes) != pdf.get("pages")
        or any(not isinstance(box, list) or len(box) != 2 or abs(float(box[0]) - 595.276) > 0.01 or abs(float(box[1]) - 841.89) > 0.01 for box in page_boxes)
        or pdf.get("searchable") is not True
        or pdf.get("tagged") is not False
        or pdf.get("images") != 0
        or pdf.get("encrypted") is not False
        or pdf.get("to_unicode_all_fonts") is not True
    ):
        raise ValueError("MIT L09 PDF topology differs")
    evidence = report.get("evidence", {})
    if evidence.get("stage") != "strict-final" or any(evidence.get(name, {}).get("status") != "validated" for name in ("browser", "visual", "rereview")):
        raise ValueError("MIT L09 strict-final evidence is incomplete")
    if browser.get("result") != "pass" or visual.get("result") != "pass":
        raise ValueError("MIT L09 browser or visual evidence is not passing")
    if (browser.get("html", {}).get("bytes"), browser.get("html", {}).get("sha256")) != html_identity:
        raise ValueError("MIT L09 browser receipt binds stale HTML")
    if (visual.get("pdf", {}).get("bytes"), visual.get("pdf", {}).get("sha256")) != pdf_identity:
        raise ValueError("MIT L09 visual receipt binds stale PDF")
    if visual.get("render", {}).get("all_pages_inspected") is not True:
        raise ValueError("MIT L09 visual receipt does not record all-page inspection")
    visual_renders = visual.get("render", {}).get("pages", [])
    if visual_renders != pdf.get("render_identities") or build.get("expected_render_identities") != visual_renders:
        raise ValueError("MIT L09 render identities differ across validation and visual receipts")
    for item in report.get("files", []):
        path = item.get("path")
        if path and file_info(path) != identity_tuple(item):
            raise ValueError(f"MIT L09 validation receipt binds stale bytes: {path}")
    rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
    for path in (MIT_CENSUS, MIT_WITNESS, MIT_TARGET):
        if file_info(path)[1] not in rereview:
            raise ValueError(f"MIT L09 independent rereview does not bind {path}")
    if not re.search(r"P1\s*=\s*0\s*,\s*P2\s*=\s*0\s*,\s*P3\s*=\s*0", rereview):
        raise ValueError("MIT L09 independent rereview severity differs")
    return report, browser, visual


def expected_ids() -> set[str]:
    result = {MIT_L09_UNIT_ID}
    result.update(f"d90.mit.ocw-6.253.l09.p{page:03d}" for page in SOURCE_PAGES)
    result.update(f"surface.mit.l09.formula.p{page:03d}.d{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1))
    result.update(f"surface.mit.l09.figure-description.p{page:03d}.f001" for page in FIGURE_PANELS)
    result.update(f"surface.mit.l09.example.p{page:03d}.i{index:03d}" for page, index in EXAMPLES)
    result.update(f"correction.o015-mit-sem-{number:04d}" for number in range(12, 20))
    result.update({
        "artifact.mit.l09.boundary-census", "artifact.mit.l09.semantic-witness",
        "artifact.mit.l09.target-source", "artifact.mit.l09.target-html",
        "artifact.mit.l09.target-pdf", "artifact.mit.l09.builder",
        "artifact.mit.l09.validator", "artifact.mit.l09.validation",
        "artifact.mit.l09.browser-qa", "artifact.mit.l09.visual-qa",
        "artifact.mit.l09.independent-rereview", "artifact.mit.l09.correction-snapshot",
        "artifact.mit.l09.css", "artifact.mit.l09.pdf-preamble",
        "artifact.mit.l09.pdf-filter", "artifact.mit.l09.before-body",
        "artifact.mit.l09.after-body", "artifact.o015.backend-generator-mit-l09",
        "artifact.o015.backend-validator-mit-l09",
    })
    qa_suffixes = {
        "source-freeze", "semantic-reconstruction", "topology", "formulas", "figures",
        "corrections", "build", "html", "browser", "pdf", "visual", "semantic-rereview",
        "accessibility", "language", "rights", "csv-losslessness", "backend-integration",
    }
    result.update(f"qa.o015.mit-l09.{suffix}" for suffix in qa_suffixes)
    core_relations = {
        "work-contains-l09", "witness-edition-contains-l09", "target-edition-contains-l09",
        "l08-precedes-l09", "witness-adapts-authority-pdf-l09", "target-translates-witness-l09",
        "html-adapts-target-l09", "pdf-adapts-target-l09", "browser-qa-depends-on-html-l09",
        "visual-qa-depends-on-pdf-l09", "validation-depends-on-browser-qa-l09",
        "validation-depends-on-visual-qa-l09", "rereview-depends-on-target-l09",
    }
    result.update(f"relation.mit.{suffix}" for suffix in core_relations)
    result.update(f"relation.mit.l09-contains-p{page:03d}" for page in SOURCE_PAGES)
    result.update(f"relation.mit.l09-formula-p{page:03d}-d{index:03d}-illustrates-segment" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1))
    result.update(f"relation.mit.l09-figure-p{page:03d}-illustrates-segment" for page in FIGURE_PANELS)
    result.update(f"relation.mit.l09-example-p{page:03d}-exercises-segment" for page, _ in EXAMPLES)
    return result


def static_preflight(input_jsonl: Path, input_csv: Path) -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema":
        raise ValueError("backend schema identity differs")
    if file_info(MIT_PDF) != SOURCE_PDF_IDENTITY or file_info(MIT_CENSUS) != CENSUS_IDENTITY:
        raise ValueError("MIT authority or L09 census identity differs")
    baseline, _, _ = load_baseline(input_jsonl, input_csv)
    events = ledger_events()
    anchors = []
    for page in SOURCE_PAGES:
        anchors.append(f"d90-mit-l09-p{page:03d}")
        anchors.extend(f"d90-mit-l09-p{page:03d}-d{index:03d}" for index in range(1, PAGE_DISPLAYS[page] + 1))
        if page in FIGURE_PANELS:
            anchors.append(f"d90-mit-l09-p{page:03d}-f001")
    anchors.extend(f"d90-mit-l09-p{page:03d}-i{index:03d}" for page, index in EXAMPLES)
    for anchor in anchors:
        fenced_div_slice(MIT_WITNESS, anchor)
        fenced_div_slice(MIT_TARGET, anchor)
    ids = expected_ids()
    if len(ids) != EXPECTED_NEW_RECORD_COUNT:
        raise ValueError(f"static L09 ID contract has {len(ids)} IDs, expected {EXPECTED_NEW_RECORD_COUNT}")
    collisions = sorted(ids & {record["id"] for record in baseline})
    if collisions:
        raise ValueError(f"L09 stable-ID collisions: {collisions}")
    return {
        "result": "pass",
        "workflow": WORKFLOW,
        "protected_baseline_record_count": len(baseline),
        "expected_new_record_count": len(ids),
        "expected_final_record_count": len(baseline) + len(ids),
        "source_pages": SOURCE_PAGES,
        "topology": {
            "top_level_items": sum(PAGE_ITEMS.values()),
            "nested_items": sum(PAGE_NESTED.values()),
            "display_surfaces": sum(PAGE_DISPLAYS.values()),
            "figure_blocks": len(FIGURE_PANELS),
            "figure_panels": sum(FIGURE_PANELS.values()),
            "examples": len(EXAMPLES),
            "corrections": len(events),
        },
        "new_id_set_sha256": sha256(("\n".join(sorted(ids)) + "\n").encode("utf-8")),
        "pending_final_evidence": [path for path in (MIT_REPORT, MIT_BROWSER_QA, MIT_VISUAL_QA) if not (ROOT / path).is_file()],
    }


def generate_records(baseline: list[dict[str, Any]], report: dict[str, Any], browser: dict[str, Any], visual: dict[str, Any], events: dict[str, tuple[dict[str, Any], dict[str, Any]]]) -> list[dict[str, Any]]:
    baseline_ids = {record["id"] for record in baseline}
    new_records: list[dict[str, Any]] = []
    new_ids: set[str] = set()

    def add(record: dict[str, Any]) -> None:
        if record["id"] in baseline_ids or record["id"] in new_ids:
            raise ValueError(f"stable-ID collision: {record['id']}")
        new_ids.add(record["id"])
        new_records.append(record)

    segment_ids = {page: f"d90.mit.ocw-6.253.l09.p{page:03d}" for page in SOURCE_PAGES}
    item_ids = [f"d90-mit-l09-p{page:03d}-i{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)]
    display_pairs = [(page, index) for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)]
    html = report["html"]
    pdf = report["pdf"]

    unit = common("unit", MIT_L09_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 9,
        "source_local_id": "lecture-5-pages-50-63",
        "source_local_label": "Lecture 5 - Recession, Lineality, and Existence of Minima",
        "target_local_label": "Kuliah 5 - Resesi, Kelinieran, dan Eksistensi Peminimum",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": SOURCE_PAGES,
        "next_source_page": 64,
        "next_source_heading": "LECTURE 6 - LECTURE OUTLINE",
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 41,
        "nested_source_item_count": 17,
        "source_item_ids": item_ids,
        "target_item_ids": item_ids,
        "source_display_count": 19,
        "source_display_ids": [f"d90-mit-l09-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "target_display_ids": [f"d90-mit-l09-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "source_figure_count": 7,
        "source_figure_ids": [f"d90-mit-l09-p{page:03d}-f001" for page in FIGURE_PANELS],
        "target_figure_ids": [f"d90-mit-l09-p{page:03d}-f001" for page in FIGURE_PANELS],
        "source_figure_panel_count": 12,
        "explicit_example_count": 2,
        "explicit_example_ids": [f"d90-mit-l09-p{page:03d}-i{index:03d}" for page, index in EXAMPLES],
        "exercise_count": 0,
        "hint_count": 0,
        "answer_count": 0,
        "solution_count": 0,
        "code_surface_count": 0,
        "interactive_surface_count": 0,
        "copied_source_graphics": 0,
        "correction_event_ids": list(EXPECTED_EVENT_IDS),
        "canonical_build_command": CANONICAL_BUILD_COMMAND,
    })
    add(unit)

    for order, page in enumerate(SOURCE_PAGES, start=1):
        anchor = f"d90-mit-l09-p{page:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("segment", segment_ids[page], "visually_checked")
        record.update({
            "unit_id": MIT_L09_UNIT_ID,
            "order": order,
            "source_edition_id": MIT_WITNESS_EDITION_ID,
            "target_edition_id": MIT_TARGET_EDITION_ID,
            "source_path": MIT_WITNESS,
            "source_line_start": source_slice[0],
            "source_line_end": source_slice[1],
            "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3],
            "source_anchor": anchor,
            "source_item_ids": [f"{anchor}-i{index:03d}" for index in range(1, PAGE_ITEMS[page] + 1)],
            "target_path": MIT_TARGET,
            "target_line_start": target_slice[0],
            "target_line_end": target_slice[1],
            "target_bytes": target_slice[2],
            "target_content_sha256": target_slice[3],
            "target_anchor": anchor,
            "target_item_ids": [f"{anchor}-i{index:03d}" for index in range(1, PAGE_ITEMS[page] + 1)],
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
            "explicit_example_count": sum(1 for example_page, _ in EXAMPLES if example_page == page),
            "anchor_mapping_rule": "identical d90-mit-l09 stable anchor preserved from witness to target",
        })
        add(record)

    for global_order, (page, index) in enumerate(display_pairs, start=1):
        anchor = f"d90-mit-l09-p{page:03d}-d{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l09.formula.p{page:03d}.d{index:03d}", "present")
        record.update({
            "unit_id": MIT_L09_UNIT_ID,
            "surface_type": "display_formula",
            "presence": "present",
            "formula_sequence_order": global_order,
            "page_formula_order": index,
            "formula_label": DISPLAY_LABELS[(page, index)],
            "source_pdf_page": page,
            "related_segment_ids": [segment_ids[page]],
            "source_path": MIT_WITNESS,
            "source_anchor": anchor,
            "source_line_start": source_slice[0],
            "source_line_end": source_slice[1],
            "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3],
            "target_path": MIT_TARGET,
            "target_anchor": anchor,
            "target_line_start": target_slice[0],
            "target_line_end": target_slice[1],
            "target_bytes": target_slice[2],
            "target_content_sha256": target_slice[3],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "formula_sequence_match": True,
            "rights_id": "rights.o015-mit-id-pilot",
        })
        add(record)

    for page, panel_count in FIGURE_PANELS.items():
        anchor = f"d90-mit-l09-p{page:03d}-f001"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l09.figure-description.p{page:03d}.f001", "present_with_limitation")
        record.update({
            "unit_id": MIT_L09_UNIT_ID,
            "surface_type": "semantic_figure_description",
            "presence": "present_with_limitation",
            "figure_label": FIGURE_LABELS[page],
            "source_pdf_page": page,
            "panel_count": panel_count,
            "related_segment_ids": [segment_ids[page]],
            "source_path": MIT_WITNESS,
            "source_anchor": anchor,
            "source_line_start": source_slice[0],
            "source_line_end": source_slice[1],
            "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3],
            "target_path": MIT_TARGET,
            "target_anchor": anchor,
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

    for global_order, ((page, index), label) in enumerate(EXAMPLES.items(), start=1):
        anchor = f"d90-mit-l09-p{page:03d}-i{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l09.example.p{page:03d}.i{index:03d}", "present")
        record.update({
            "unit_id": MIT_L09_UNIT_ID,
            "surface_type": "worked_example",
            "presence": "present",
            "example_sequence_order": global_order,
            "example_label": label,
            "source_pdf_page": page,
            "related_segment_ids": [segment_ids[page]],
            "source_path": MIT_WITNESS,
            "source_anchor": anchor,
            "source_line_start": source_slice[0],
            "source_line_end": source_slice[1],
            "source_bytes": source_slice[2],
            "source_content_sha256": source_slice[3],
            "target_path": MIT_TARGET,
            "target_anchor": anchor,
            "target_line_start": target_slice[0],
            "target_line_end": target_slice[1],
            "target_bytes": target_slice[2],
            "target_content_sha256": target_slice[3],
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "rights_id": "rights.o015-mit-id-pilot",
        })
        add(record)

    for event_id, (pages, locator) in CORRECTION_SPECS.items():
        event, binding = events[event_id]
        number = int(event_id.rsplit("-", 1)[1])
        correction = common("correction", f"correction.o015-mit-sem-{number:04d}", "applied_in_admitted_reader")
        correction.update({
            "source_event_id": event_id,
            "source_edition_id": MIT_SOURCE_EDITION_ID,
            "affected_unit_ids": [MIT_L09_UNIT_ID],
            "affected_segment_ids": [segment_ids[page] for page in pages],
            "source_path": MIT_PDF,
            "source_pdf_pages": pages,
            "source_locator": f"complete-notes PDF page{'s' if len(pages) > 1 else ''} {', '.join(map(str, pages))}; {locator}",
            "witness_locators": [f"{MIT_WITNESS}#d90-mit-l09-p{page:03d}" for page in pages],
            "target_locators": [f"{MIT_TARGET}#d90-mit-l09-p{page:03d}" for page in pages],
            "surface": event["surface"],
            "source_issue": event["source_issue"],
            "target_action": event["target_action"],
            "correction_class": event["class"],
            "disposition": "applied_in_admitted_reader",
            "shared_ledger_state": "immutable_boundary_snapshot",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.mit.l09.correction-snapshot",
            **binding,
        })
        add(correction)

    pdf_pages = int(pdf["pages"])
    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l09.boundary-census", "boundary_census", MIT_CENSUS, "rights.o015-mit-pilot-build-qa", {"source_pdf_pages": SOURCE_PAGES, "next_source_page": 64}),
        ("artifact.mit.l09.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"source_pdf_pages": SOURCE_PAGES, "official_editable_source": False, "source_item_count": 41, "nested_source_item_count": 17, "source_display_count": 19, "source_figure_description_count": 7, "explicit_example_count": 2}),
        ("artifact.mit.l09.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": SOURCE_PAGES, "source_item_count": 41, "nested_source_item_count": 17, "source_display_count": 19, "source_figure_description_count": 7, "explicit_example_count": 2, "correction_event_ids": list(EXPECTED_EVENT_IDS)}),
        ("artifact.mit.l09.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "MathML", "source_pages": 14, "source_displays": 19, "source_figures": 7, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l09.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": pdf_pages, "page_size": "A4", "tagged": False, "searchable": True, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l09.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5 and LuaLaTeX", "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND}),
        ("artifact.mit.l09.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l09.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass", "errors": []}),
        ("artifact.mit.l09.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "live_viewport_measurement": True}),
        ("artifact.mit.l09.visual-qa", "visual_qa_report", MIT_VISUAL_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "pages": pdf_pages}),
        ("artifact.mit.l09.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.mit.l09.correction-snapshot", "correction_ledger_snapshot", MIT_LEDGER, "rights.o015-mit-pilot-build-qa", {"source_event_ids": list(EXPECTED_EVENT_IDS), "immutable_boundary_snapshot": True, "event_bindings": [events[event_id][1] for event_id in EXPECTED_EVENT_IDS]}),
        ("artifact.mit.l09.css", "html_stylesheet", MIT_CSS, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l09.pdf-preamble", "pdf_preamble", MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l09.pdf-filter", "pandoc_lua_filter", MIT_FILTER, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l09.before-body", "html_include", MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l09.after-body", "html_include", MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.o015.backend-generator-mit-l09", "backend_generator", "qa/extend_backend_mit_l09.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "protected_baseline_record_count": BASELINE_RECORD_COUNT}),
        ("artifact.o015.backend-validator-mit-l09", "backend_validator", "qa/validate_backend_mit_l09.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "independent_validation_runs_required": 2}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    math_nodes = int(html["math_nodes"])
    correction_ids = [f"correction.o015-mit-sem-{number:04d}" for number in range(12, 20)]
    render_hashes = [item["sha256"] for item in pdf.get("render_identities", [])]
    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l09.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.complete-notes-pdf", "artifact.mit.l09.boundary-census", "artifact.mit.l09.semantic-witness"], "authority_pdf_pages": 340, "boundary_pages": SOURCE_PAGES, "next_source_page": 64, "next_source_page_text_sha256": SOURCE_TEXT_FINGERPRINTS[64][1]}),
        ("qa.o015.mit-l09.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l09.semantic-witness", "artifact.mit.l09.target-source", "artifact.mit.l09.validation"], "official_editable_source": False, "source_items": 41, "nested_source_items": 17, "source_figures": 7, "source_figure_panels": 12, "explicit_examples": 2}),
        ("qa.o015.mit-l09.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l09.validation", "artifact.mit.l09.boundary-census"], "source_page_map": [[page, page] for page in SOURCE_PAGES], "item_counts": {str(page): PAGE_ITEMS[page] for page in SOURCE_PAGES}, "nested_item_counts": {str(page): PAGE_NESTED[page] for page in SOURCE_PAGES}, "display_counts": {str(page): PAGE_DISPLAYS[page] for page in SOURCE_PAGES}, "figure_panel_counts": {str(page): FIGURE_PANELS.get(page, 0) for page in SOURCE_PAGES}, "example_counts": {str(page): sum(1 for example_page, _ in EXAMPLES if example_page == page) for page in SOURCE_PAGES}}),
        ("qa.o015.mit-l09.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l09.semantic-witness", "artifact.mit.l09.target-source", "artifact.mit.l09.validation", "artifact.mit.l09.independent-rereview"], "source_math_nodes": math_nodes, "target_math_nodes": math_nodes, "display_formulas": 19, "formula_sequence_match": True}),
        ("qa.o015.mit-l09.figures", "figure_description_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l09.semantic-witness", "artifact.mit.l09.target-source", "artifact.mit.l09.validation", "artifact.mit.l09.visual-qa"], "source_figure_blocks": 7, "source_figure_panels": 12, "semantic_figure_descriptions": 7, "copied_source_graphics": 0, "reader_images": 0}),
        ("qa.o015.mit-l09.corrections", "correction_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l09.correction-snapshot", "artifact.mit.l09.semantic-witness", "artifact.mit.l09.target-source", "artifact.mit.l09.validation", "artifact.mit.l09.independent-rereview"], "source_event_ids": list(EXPECTED_EVENT_IDS), "correction_record_ids": correction_ids, "silent_normalization": False}),
        ("qa.o015.mit-l09.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l09.builder", "artifact.mit.l09.target-html", "artifact.mit.l09.target-pdf", "artifact.mit.l09.validation"], "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND, "deterministic_rebuilds": 2, "html_sha256": file_info(MIT_HTML)[1], "pdf_sha256": file_info(MIT_READER_PDF)[1], "toolchain": "Pandoc HTML5 and LuaLaTeX"}),
        ("qa.o015.mit-l09.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l09.target-html", "artifact.mit.l09.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": html["headings"], "math_nodes": math_nodes, "display_math_nodes": 19, "images": 0, "source_pages": 14, "source_items": 41, "source_figures": 7, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l09.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l09.browser-qa", "artifact.mit.l09.target-html"], "desktop_viewport": [1280, 720], "mobile_viewport": [390, 844], "horizontal_overflow": False, "display_math_overflow": False, "live_measurement": True, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l09.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l09.target-pdf", "artifact.mit.l09.validation"], "pages": pdf_pages, "page_size": "A4", "lang": "id-ID", "searchable": True, "tagged": False, "images": 0, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l09.visual", "visual", "pass", {"witness_artifact_ids": ["artifact.mit.l09.visual-qa", "artifact.mit.l09.target-pdf"], "pages": pdf_pages, "all_pages_visually_inspected": True, "render_tool": "pdftoppm", "render_sha256": render_hashes}),
        ("qa.o015.mit-l09.semantic-rereview", "independent_semantic_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l09.independent-rereview", "artifact.mit.l09.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l09.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l09.target-html", "artifact.mit.l09.target-pdf", "artifact.mit.l09.browser-qa", "artifact.mit.l09.visual-qa"], "primary_surface": "semantic_html", "html_static_structure_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"], "human_review_is_release_gate": False}),
        ("qa.o015.mit-l09.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "human_review_is_release_gate": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded; this is evidence, not a hold."}),
        ("qa.o015.mit-l09.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l09.boundary-census", "artifact.mit.l09.semantic-witness", "artifact.mit.l09.target-source"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa", "o015-mit-l01-backend-tooling"], "source_graphics_in_boundary": 7, "source_figure_panels": 12, "source_graphics_redistributed": 0, "semantic_figure_descriptions": 7, "license": "CC BY-NC-SA 4.0", "change_event_ids": list(EXPECTED_EVENT_IDS), "non_endorsement": True}),
        ("qa.o015.mit-l09.csv-losslessness", "csv_losslessness", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l09", "artifact.o015.backend-validator-mit-l09"], "projection": "record_json is canonical JSON for each JSONL record", "utf8_strict": True, "row_order_matches_jsonl": True}),
        ("qa.o015.mit-l09.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l09", "artifact.o015.backend-validator-mit-l09", "artifact.o015.source-authority", "artifact.o015.component-rights"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_baseline_reconstruction_required": True, "independent_validation_runs_required": 2}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        status = "passed" if result == "pass" else result
        record = common("qa_event", record_id, status)
        record.update({"event_type": event_type, "result": result, "unit_id": MIT_L09_UNIT_ID, **extra})
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l09", "contains", MIT_ROOT_UNIT_ID, MIT_L09_UNIT_ID, "Ninth admitted MIT source-order boundary, complete-notes pages 50-63."),
        ("relation.mit.witness-edition-contains-l09", "contains", MIT_WITNESS_EDITION_ID, MIT_L09_UNIT_ID, "Page-addressed English semantic witness for pages 50-63."),
        ("relation.mit.target-edition-contains-l09", "contains", MIT_TARGET_EDITION_ID, MIT_L09_UNIT_ID, "Built Indonesian semantic derivative for pages 50-63."),
        ("relation.mit.l08-precedes-l09", "precedes", "unit.mit.ocw-6.253.l08", MIT_L09_UNIT_ID, "Source order advances from Lecture 4 pages 39-49 to Lecture 5 pages 50-63."),
        ("relation.mit.witness-adapts-authority-pdf-l09", "adapts", "artifact.mit.l09.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes PDF pages 50-63."),
        ("relation.mit.target-translates-witness-l09", "translates", "artifact.mit.l09.target-source", "artifact.mit.l09.semantic-witness", "Page/list/formula translation with disclosed corrections O015-MIT-SEM-0012 through 0019."),
        ("relation.mit.html-adapts-target-l09", "adapts", "artifact.mit.l09.target-html", "artifact.mit.l09.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l09", "adapts", "artifact.mit.l09.target-pdf", "artifact.mit.l09.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.browser-qa-depends-on-html-l09", "depends-on", "artifact.mit.l09.browser-qa", "artifact.mit.l09.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.visual-qa-depends-on-pdf-l09", "depends-on", "artifact.mit.l09.visual-qa", "artifact.mit.l09.target-pdf", "Rendered visual QA evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l09", "depends-on", "artifact.mit.l09.validation", "artifact.mit.l09.browser-qa", "Validation receipt incorporates browser evidence."),
        ("relation.mit.validation-depends-on-visual-qa-l09", "depends-on", "artifact.mit.l09.validation", "artifact.mit.l09.visual-qa", "Validation receipt incorporates visual evidence."),
        ("relation.mit.rereview-depends-on-target-l09", "depends-on", "artifact.mit.l09.independent-rereview", "artifact.mit.l09.target-source", "Independent semantic rereview binds the admitted target source and readers."),
    ]
    for page in SOURCE_PAGES:
        relation_specs.append((f"relation.mit.l09-contains-p{page:03d}", "contains", MIT_L09_UNIT_ID, segment_ids[page], f"Lecture 5 contains source page {page}."))
    for page, index in display_pairs:
        relation_specs.append((f"relation.mit.l09-formula-p{page:03d}-d{index:03d}-illustrates-segment", "illustrates", f"surface.mit.l09.formula.p{page:03d}.d{index:03d}", segment_ids[page], DISPLAY_LABELS[(page, index)] + "."))
    for page in FIGURE_PANELS:
        relation_specs.append((f"relation.mit.l09-figure-p{page:03d}-illustrates-segment", "illustrates", f"surface.mit.l09.figure-description.p{page:03d}.f001", segment_ids[page], FIGURE_LABELS[page] + "."))
    for page, index in EXAMPLES:
        relation_specs.append((f"relation.mit.l09-example-p{page:03d}-exercises-segment", "exercises", f"surface.mit.l09.example.p{page:03d}.i{index:03d}", segment_ids[page], EXAMPLES[(page, index)] + "."))
    for relation_id, relation_type, source_id, target_id, note in relation_specs:
        relation = common("relation", relation_id, "current")
        relation.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        add(relation)

    expected = expected_ids()
    if new_ids != expected:
        raise ValueError(f"generated L09 ID set differs; missing={sorted(expected-new_ids)}, extra={sorted(new_ids-expected)}")
    if len(new_records) != EXPECTED_NEW_RECORD_COUNT or Counter(record["entity_type"] for record in new_records) != EXPECTED_ENTITY_COUNTS:
        raise ValueError("generated L09 entity topology differs from the 142-record contract")

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
    records = sorted(records, key=lambda record: (entity_rank[record["entity_type"]], record["id"]))
    jsonl_bytes = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    csv_buffer = io.StringIO(newline="")
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(["schema", "schema_version", "entity_type", "id", "record_json"])
    for record in records:
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)])
    return jsonl_bytes, csv_buffer.getvalue().encode("utf-8")


def atomic_write_pair(output_jsonl: Path, output_csv: Path, jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    try:
        for destination, data in ((output_jsonl, jsonl_bytes), (output_csv, csv_bytes)):
            with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{destination.name}.mit-l09-", suffix=".stage", dir=destination.parent, delete=False) as handle:
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
    parser.add_argument("--preflight", action="store_true", help="validate static authority/topology/baseline only")
    args = parser.parse_args()
    if args.output_dir and args.write_canonical:
        parser.error("--output-dir and --write-canonical are mutually exclusive")

    preflight = static_preflight(args.input_jsonl, args.input_csv)
    if args.preflight:
        print(json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    report, browser, visual = load_qa_evidence()
    events = ledger_events()
    baseline, _, _ = load_baseline(args.input_jsonl, args.input_csv)
    new_records = generate_records(baseline, report, browser, visual, events)
    all_records = baseline + new_records
    jsonl_bytes, csv_bytes = serialize(all_records)

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
        "result": "pass",
        "workflow": WORKFLOW,
        "write_mode": "canonical" if args.write_canonical else "staged" if args.output_dir else "dry-run",
        "protected_baseline_record_count": BASELINE_RECORD_COUNT,
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
