#!/usr/bin/env python3
"""Add the reader-admitted MIT 6.253 Lecture 3 boundary (pages 29-38).

The admitted 1,714-record L06 backend is a protected byte-for-byte baseline.
This workflow removes only its own prior projection, proves that exact baseline
has been reconstructed, and deterministically recreates the L07 projection.
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

RECORDED_AT = "2026-08-24T02:00:00Z"
WORKFLOW = "o015-mit-l07-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 1714
BASELINE_JSONL = (1_231_983, "9ad375756d2ee3159acf760f5d68084d2921e665cf993e2aaa6514f1e710337e")
BASELINE_CSV = (1_480_312, "f5c81e38ee9d1b4e9d2bcc7632603266fcf271b9b8c6454e99ba3e4b0041f72f")
BASELINE_ID_SET_SHA256 = "c3b38e218f00ed53325121b06d715a5e60993a2745cdf7888c75f8879ac4f57b"
BASELINE_RECORD_SET_SHA256 = "7953fb9b891b531cf87a19b447158dce2852d8e33ce7ae160fdcab78d0d8a419"

MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L07_UNIT_ID = "unit.mit.ocw-6.253.l07"
SOURCE_PAGES = list(range(29, 39))
PAGE_ITEMS = {29: 3, 30: 1, 31: 0, 32: 1, 33: 1, 34: 1, 35: 6, 36: 1, 37: 0, 38: 2}
PAGE_NESTED = {29: 0, 30: 2, 31: 0, 32: 0, 33: 2, 34: 3, 35: 3, 36: 2, 37: 2, 38: 0}
PAGE_DISPLAYS = {29: 0, 30: 1, 31: 0, 32: 3, 33: 3, 34: 2, 35: 0, 36: 0, 37: 2, 38: 2}
FIGURE_PANELS = {30: 1, 31: 2, 36: 2, 37: 1}
DISPLAY_LABELS = {
    (30, 1): "first-order inequality characterizing differentiable convexity",
    (32, 1): "variational first-order optimality condition",
    (32, 2): "sufficiency inequality for the optimality condition",
    (32, 3): "one-sided directional-derivative necessity limit",
    (33, 1): "squared-distance projection objective",
    (33, 2): "Euclidean projection characterization",
    (33, 3): "projection proof optimality condition",
    (34, 1): "second-order mean-value expansion",
    (34, 2): "Hessian-derived first-order lower bound",
    (37, 1): "linear-dependence identity",
    (37, 2): "Caratheodory coefficient-reduction combination",
    (38, 1): "bounded coefficient-vector sequence",
    (38, 2): "coefficient-vector limit point",
}
FIGURE_LABELS = {
    30: "differentiable convex function and supporting tangent line",
    31: "two-panel first-order convexity proof ideas",
    36: "two-panel cone and convex-hull representations",
    37: "Caratheodory lifting diagram",
}
SOURCE_TEXT_FINGERPRINTS = {
    29: (221, "c15536202c7266b03878d0c26e7eb7f16fd66914dc8f1e3130a6bda4331a2a86"),
    30: (594, "9d98e3ccc8484700cfb18da53d957f3e76baec9eafdce7c7f32a8830cf403085"),
    31: (970, "6e0c1295f1123cf1f21a00eaa7a56dffdae5687012636037ad4af3b135fa6a88"),
    32: (1070, "839ab088b6e14506263f00c7c16f1ef7305e4b064a056206b39676a1f9381b4d"),
    33: (613, "0fd72c6f78ea30001a3090e3d53b852b29e61ad6892bcc44150934d20417c085"),
    34: (1083, "7c31d76eb0766e97a33bec9c2e788bbdb1a22019a3058ad13e00babb8ecfaeaf"),
    35: (1034, "cd5b3f0e30c9fa5662ba24784ff87ea2dc73cf909f406cdab776791688812604"),
    36: (792, "2b49f0fe0cd826f7abd9fee09cf1491ac082e7601b6b5c9573e9da508fb82872"),
    37: (1200, "1eef14b9a3c143879b7567e2c4ea128562251801f0dd006688dafbb564c0425c"),
    38: (1215, "2861b4fec0e91b47654e551a8336f4805b20befd1cad2aa5e1035ca500145c5f"),
    39: (266, "7eea461ea346ad1d4f43be4350ca2597d2efe0270b41967307600a521de03b05"),
}
SOURCE_RENDER_FINGERPRINTS = {
    29: (17903, "872877e2ff62bc5d5d9bb85f7b4d5edaed3f17264ed09761e554c0a817d069ff"),
    30: (39867, "329aa8b412ab4cd518d5c2b498e38f4b5d2d40dacffd7f7fc21cddd9b526b213"),
    31: (45202, "cd6588795ed19cc9d1983147710c8307e66ea62518aff9a0eab9142990ee9c9f"),
    32: (48903, "cc339aecef0eabe0ffc9a47de60b352602e8b5a5625b6437c3a6c61774ae5bbe"),
    33: (38638, "b79d9053c7afb765ff09c8eabf18114868c17d72184bfaed8d1c7bbefe66ddf9"),
    34: (64608, "cdde1e5749e0ee9f8a3ddaa57d77dc5869c93b2b4a22f3261be851a99c8b953a"),
    35: (63392, "a1564c4f84e82775d113117248045eddc2a4a09072e861a77bf469ac409f723a"),
    36: (49842, "324d2ac71cdf17df23ff68324a8f3e2cb13d740c00f1625439706913acade773"),
    37: (60537, "d3c6a498344390bae6ed6e6feaca1c98fd1d0ae290591902fedc6b70c66c35af"),
    38: (58700, "8099d5e33bdf3ac9a9c18fdadf9bac05ebca415f45d0ae0ef2be2a241003be75"),
}

MIT_PDF = "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
MIT_CENSUS = "00_control/MIT_L07_LECTURE_3_PAGES_029-038_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/MIT_L07_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-07-lecture-3-differentiable-convex-functions-caratheodory-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.md"
MIT_HTML = "output/html/D90-MIT-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.pdf"
MIT_CSS = "source/id-ID/mit-l07.css"
MIT_PREAMBLE = "source/id-ID/mit-l07-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l07-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l07-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l07-after-body.html"
MIT_BUILDER = "qa/build_mit_l07.py"
MIT_VALIDATOR = "qa/validate_mit_l07.py"
MIT_REPORT = "qa/MIT_L07_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L07_BROWSER_QA.json"
MIT_VISUAL_QA = "qa/MIT_L07_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L07_INDEPENDENT_REREVIEW.md"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
LEDGER_IDENTITY = (1_490, "eba6c2039e1f893287921d72f5169e14861d95955acd7c6682e59cabcd030084")
CANONICAL_BUILD_COMMAND = (
    "python qa/build_mit_l07.py --html-output "
    "output/html/D90-MIT-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.html "
    "--pdf-output output/pdf/D90-MIT-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.pdf"
)
RECEIPT_BUILD_COMMAND = "python qa/build_mit_l07.py --html-output <html> --pdf-output <pdf>"
FINAL_READER_IDENTITIES = {
    MIT_CENSUS: (11_013, "3c7400bdd092cffe358e852e5304091bfd53b10fb36d366f558e1b0f9c8bee2f"),
    MIT_WITNESS: (13_879, "ab9fb12728b53c0369094a347827aa40d74332b811976b8e0733caf245bce18b"),
    MIT_TARGET: (16_518, "b1554fcb455bb43ecd72aa4c4e0f70d6d502c885009ba5e6a799e639e69441dd"),
    MIT_CSS: (2_777, "4f5bb04dc8f30c5e383fc901dea1817168446ad6f6761e21a8dfdd9fb961ab1b"),
    MIT_PREAMBLE: (1_499, "11dc4cdb79b1b1cffba021c2571451edac343a8763769552e9d1cb846ca1b6e0"),
    MIT_FILTER: (302, "2a39c4aeb5b6587e4ff7db483f130cb88c8fdbc74f9e83f8fd939d37f6e75421"),
    MIT_BEFORE_BODY: (96, "1e979724f5ee0f65feda5442d9307df710a3f2d8203f5d7051b390dc42ce61b7"),
    MIT_AFTER_BODY: (176, "ce35e12f0a05dda23a0f55e9b5dfb1f26e5f4c8d3b1c7439ac401227366580b9"),
    MIT_BUILDER: (4_115, "d777599f7529449c5c10a130afd32a1e67338ae7edf19b0dca00fdbd91724d01"),
    MIT_VALIDATOR: (28_883, "9dd39156c3591c0a771cc894ac5085fb5c787b5a472b722be24eb4d84c2d16ca"),
    MIT_REPORT: (8_176, "c076f79323c21186ceab5cbb56a128c71a31c67aa55b635f1eeebe313b4bd7e1"),
    MIT_BROWSER_QA: (2_468, "f29fdb2086693efe892ac0a0d346fa19c7d57de8371d7ccc0317edaf6e8bf9d7"),
    MIT_VISUAL_QA: (2_472, "1caf7ebc941616122adade72ecc7efbf68e9b8a9499290f0782bf2e11e0cadd2"),
    MIT_REREVIEW: (4_136, "d5f0bfc23b7a9b74d30570de9b2bd058c0ded84b51414b7b0b929349764ea86d"),
    MIT_HTML: (77_399, "cc3b4f665d5f0b4cb9e26245ec0cce71658c6c0b3e5e07cee3fcabfb43df5e13"),
    MIT_READER_PDF: (75_885, "2c7b4defaa56578f628c048dc4f17ee06b61f2bc33122b172af5539a5dae2eec"),
    MIT_LEDGER: LEDGER_IDENTITY,
}

EXPECTED_LEDGER_EVENTS = {
    "O015-MIT-SEM-0007": {
        "event_id": "O015-MIT-SEM-0007",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF pages 30, 32, and 34; source/en/mit-07-lecture-3-differentiable-convex-functions-caratheodory-semantic-witness.md",
        "surface": "Function-type arrows in Lecture 3",
        "source_issue": "Three declarations use the element-mapping arrow in expressions that state only a function's domain and codomain, repeating the determined notation issue in earlier lectures.",
        "target_action": "Preserved the printed mapsto arrows in the English semantic witness, normalized them to right arrows in the learner-facing Indonesian type declarations, and disclosed the correction in the edition notice.",
        "class": "determined_notation_correction",
    },
    "O015-MIT-SEM-0008": {
        "event_id": "O015-MIT-SEM-0008",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF page 33; source/en/mit-07-lecture-3-differentiable-convex-functions-caratheodory-semantic-witness.md",
        "surface": "Projection theorem minimizing point",
        "source_issue": "The printed statement says there exists a unique minimum of the squared-distance function but then denotes the projection point; the object asserted unique is the minimizer, not the scalar minimum value.",
        "target_action": "Preserved the printed wording in the English semantic witness, translated the learner-facing statement as a unique minimizing point, and disclosed the determined semantic terminology correction in the edition notice.",
        "class": "determined_semantic_terminology_correction",
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
        raise ValueError(f"{context} JSONL is not the protected 1,714-record baseline")
    if (len(csv_bytes), sha256(csv_bytes)) != BASELINE_CSV:
        raise ValueError(f"{context} CSV is not the protected 1,714-record baseline")


def stage_backend(jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    staged: list[Path] = []
    try:
        for destination, data in ((JSONL_PATH, jsonl_bytes), (CSV_PATH, csv_bytes)):
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.mit-l07-", suffix=".stage", dir=BACKEND, delete=False
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
        raise ValueError("L07 correction snapshot identity differs")
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), start=1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id not in EXPECTED_LEDGER_EVENTS or event_id in result:
            raise ValueError(f"unexpected or duplicate event in L07 snapshot: {event_id}")
        if event != EXPECTED_LEDGER_EVENTS[event_id]:
            raise ValueError(f"{event_id} differs from the admitted exact event")
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
    if set(result) != set(EXPECTED_LEDGER_EVENTS):
        raise ValueError("L07 correction snapshot event set differs")
    return result


def load_qa_evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    visual = json.loads((ROOT / MIT_VISUAL_QA).read_text(encoding="utf-8"))
    expected_boundary = {
        "copied_source_graphics": 0,
        "nested_items": 14,
        "next_heading": "LECTURE 4 - LECTURE OUTLINE",
        "next_source_page": 39,
        "source_displays": 13,
        "source_figure_panels": 6,
        "source_figures": 4,
        "source_items": 16,
        "source_pdf_pages": SOURCE_PAGES,
    }
    if report.get("result") != "pass" or report.get("errors") != [] or report.get("boundary") != expected_boundary:
        raise ValueError("MIT L07 content validation receipt differs")
    if report.get("formula_sequence_match") is not True:
        raise ValueError("MIT L07 formula sequence is not validated")
    if report.get("source_page_text_sha256") != {str(page): identity[1] for page, identity in SOURCE_TEXT_FINGERPRINTS.items()}:
        raise ValueError("MIT L07 source-page text fingerprints differ")
    pair = [file_info(MIT_HTML)[1], file_info(MIT_READER_PDF)[1]]
    build = report.get("build", {})
    if build.get("command") != RECEIPT_BUILD_COMMAND or build.get("deterministic_rebuilds") != 2 or build.get("rebuild_hashes") != [pair, pair]:
        raise ValueError("MIT L07 deterministic-build evidence differs")
    if browser.get("result") != "pass" or visual.get("result") != "pass":
        raise ValueError("MIT L07 browser/visual evidence is not passing")
    if (browser.get("surface", {}).get("bytes"), browser.get("surface", {}).get("sha256")) != file_info(MIT_HTML):
        raise ValueError("MIT L07 browser receipt binds stale HTML")
    if (visual.get("surface", {}).get("bytes"), visual.get("surface", {}).get("sha256")) != file_info(MIT_READER_PDF):
        raise ValueError("MIT L07 visual receipt binds stale PDF")
    if report.get("pdf", {}).get("render_sha256") != [item["sha256"] for item in visual.get("render", {}).get("files", [])]:
        raise ValueError("MIT L07 render hash sequence differs between receipts")
    for item in report.get("files", {}).values():
        path = item.get("path")
        if path and file_info(path) != (item.get("bytes"), item.get("sha256")):
            raise ValueError(f"MIT L07 validation receipt binds stale bytes: {path}")
    rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
    for path in (MIT_TARGET, MIT_HTML, MIT_READER_PDF):
        if file_info(path)[1] not in rereview:
            raise ValueError(f"MIT L07 independent rereview does not bind {path}")
    if "P1=0, P2=0, P3=0" not in rereview:
        raise ValueError("MIT L07 independent rereview severity disposition differs")
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
    if len(records) != len(incoming_records):
        assert_raw_baseline(strip_workflow_jsonl(incoming_jsonl), strip_workflow_csv(incoming_csv), "workflow-stripped incoming")
    else:
        assert_raw_baseline(incoming_jsonl, incoming_csv, "incoming")
    if len(records) != BASELINE_RECORD_COUNT or id_set_sha256(records) != BASELINE_ID_SET_SHA256 or record_set_sha256(records) != BASELINE_RECORD_SET_SHA256:
        raise ValueError("stripped backend record set differs from protected baseline")

    baseline_ids = {record["id"] for record in records}
    new_records: list[dict[str, Any]] = []
    new_ids: set[str] = set()

    def add(record: dict[str, Any]) -> None:
        if record["id"] in baseline_ids or record["id"] in new_ids:
            raise ValueError(f"stable-ID collision: {record['id']}")
        new_ids.add(record["id"])
        new_records.append(record)

    segment_ids = {page: f"d90.mit.ocw-6.253.l07.p{page:03d}" for page in SOURCE_PAGES}
    source_items = [f"src-mit-l07-p{page:03d}-i{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)]
    target_items = [item.replace("src-mit-", "d90-mit-", 1) for item in source_items]
    display_pairs = [(page, index) for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)]

    unit = common("unit", MIT_L07_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 7,
        "source_local_id": "lecture-3-pages-29-38",
        "source_local_label": "Lecture 3 - Differentiable Convex Functions and Caratheodory",
        "target_local_label": "Kuliah 3 - Fungsi Konveks Terdiferensialkan dan Caratheodory",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": SOURCE_PAGES,
        "next_source_page": 39,
        "next_source_heading": "LECTURE 4 - LECTURE OUTLINE",
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 16,
        "nested_source_item_count": 14,
        "source_item_ids": source_items,
        "target_item_ids": target_items,
        "source_display_count": 13,
        "source_display_ids": [f"src-mit-l07-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "target_display_ids": [f"d90-mit-l07-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "source_figure_count": 4,
        "source_figure_ids": [f"src-mit-l07-p{page:03d}-f001" for page in FIGURE_PANELS],
        "target_figure_ids": [f"d90-mit-l07-p{page:03d}-f001" for page in FIGURE_PANELS],
        "source_figure_panel_count": 6,
        "copied_source_graphics": 0,
        "correction_event_ids": sorted(EXPECTED_LEDGER_EVENTS),
        "canonical_build_command": CANONICAL_BUILD_COMMAND,
    })
    add(unit)

    for order, page in enumerate(SOURCE_PAGES, start=1):
        source_anchor = f"src-mit-l07-p{page:03d}"
        target_anchor = f"d90-mit-l07-p{page:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
        record = common("segment", segment_ids[page], "visually_checked")
        record.update({
            "unit_id": MIT_L07_UNIT_ID,
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
        source_anchor = f"src-mit-l07-p{page:03d}-d{index:03d}"
        target_anchor = f"d90-mit-l07-p{page:03d}-d{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
        record = common("learning_surface", f"surface.mit.l07.formula.p{page:03d}.d{index:03d}", "present")
        record.update({
            "unit_id": MIT_L07_UNIT_ID,
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
        add(record)

    for page, panel_count in FIGURE_PANELS.items():
        source_anchor = f"src-mit-l07-p{page:03d}-f001"
        target_anchor = f"d90-mit-l07-p{page:03d}-f001"
        source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
        record = common("learning_surface", f"surface.mit.l07.figure-description.p{page:03d}.f001", "present_with_limitation")
        record.update({
            "unit_id": MIT_L07_UNIT_ID,
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
        "O015-MIT-SEM-0007": {
            "record_id": "correction.o015-mit-sem-0007",
            "pages": [30, 32, 34],
            "source_locator": "complete-notes PDF pages 30, 32, and 34; function type declarations",
            "item_anchors": ["p030-i001", "p032-i001", "p034-i001"],
        },
        "O015-MIT-SEM-0008": {
            "record_id": "correction.o015-mit-sem-0008",
            "pages": [33],
            "source_locator": "complete-notes PDF page 33; projection theorem minimizing object",
            "item_anchors": ["p033-i001"],
        },
    }
    for event_id, spec in correction_specs.items():
        event, binding = events[event_id]
        correction = common("correction", spec["record_id"], "applied_in_admitted_reader")
        correction.update({
            "source_event_id": event_id,
            "source_edition_id": MIT_SOURCE_EDITION_ID,
            "affected_unit_ids": [MIT_L07_UNIT_ID],
            "affected_segment_ids": [segment_ids[page] for page in spec["pages"]],
            "source_path": MIT_PDF,
            "source_pdf_pages": spec["pages"],
            "source_locator": spec["source_locator"],
            "witness_locators": [f"{MIT_WITNESS}#src-mit-l07-{anchor}" for anchor in spec["item_anchors"]],
            "target_locators": [f"{MIT_TARGET}#d90-mit-l07-{anchor}" for anchor in spec["item_anchors"]],
            "surface": event["surface"],
            "source_issue": event["source_issue"],
            "target_action": event["target_action"],
            "correction_class": event["class"],
            "disposition": "applied_in_admitted_reader",
            "shared_ledger_state": "immutable_boundary_snapshot",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.mit.l07.correction-snapshot",
            **binding,
        })
        add(correction)

    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l07.boundary-census", "boundary_census", MIT_CENSUS, "rights.o015-mit-pilot-build-qa", {"source_pdf_pages": SOURCE_PAGES, "next_source_page": 39}),
        ("artifact.mit.l07.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"source_pdf_pages": SOURCE_PAGES, "official_editable_source": False, "source_item_count": 16, "nested_source_item_count": 14, "source_display_count": 13, "source_figure_description_count": 4}),
        ("artifact.mit.l07.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": SOURCE_PAGES, "source_item_count": 16, "nested_source_item_count": 14, "source_display_count": 13, "source_figure_description_count": 4, "correction_event_ids": sorted(EXPECTED_LEDGER_EVENTS)}),
        ("artifact.mit.l07.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "MathML", "source_pages": 10, "source_displays": 13, "source_figures": 4, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l07.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": 4, "page_size": "A4", "tagged": False, "searchable": True, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l07.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5 and LuaLaTeX", "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND}),
        ("artifact.mit.l07.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l07.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass", "errors": []}),
        ("artifact.mit.l07.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "live_viewport_measurement": True}),
        ("artifact.mit.l07.visual-qa", "visual_qa_report", MIT_VISUAL_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "pages": 4}),
        ("artifact.mit.l07.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.mit.l07.correction-snapshot", "correction_ledger_snapshot", MIT_LEDGER, "rights.o015-mit-pilot-build-qa", {"source_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "immutable_boundary_snapshot": True, "event_bindings": [events[event_id][1] for event_id in sorted(events)]}),
        ("artifact.mit.l07.css", "html_stylesheet", MIT_CSS, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l07.pdf-preamble", "pdf_preamble", MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l07.pdf-filter", "pandoc_lua_filter", MIT_FILTER, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l07.before-body", "html_include", MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l07.after-body", "html_include", MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.o015.backend-generator-mit-l07", "backend_generator", "qa/extend_backend_mit_l07.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "protected_baseline_record_count": BASELINE_RECORD_COUNT}),
        ("artifact.o015.backend-validator-mit-l07", "backend_validator", "qa/validate_backend_mit_l07.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "independent_validation_runs_required": 2}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l07.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.complete-notes-pdf", "artifact.mit.l07.boundary-census", "artifact.mit.l07.semantic-witness"], "authority_pdf_pages": 340, "boundary_pages": SOURCE_PAGES, "next_source_page": 39, "next_source_page_text_sha256": SOURCE_TEXT_FINGERPRINTS[39][1]}),
        ("qa.o015.mit-l07.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l07.semantic-witness", "artifact.mit.l07.target-source", "artifact.mit.l07.validation"], "official_editable_source": False, "source_items": 16, "nested_source_items": 14, "source_figures": 4}),
        ("qa.o015.mit-l07.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l07.validation", "artifact.mit.l07.boundary-census"], "source_page_map": [[page, page] for page in SOURCE_PAGES], "item_counts": {str(page): PAGE_ITEMS[page] for page in SOURCE_PAGES}, "nested_item_counts": {str(page): PAGE_NESTED[page] for page in SOURCE_PAGES}, "display_counts": {str(page): PAGE_DISPLAYS[page] for page in SOURCE_PAGES}, "figure_panel_counts": {str(page): FIGURE_PANELS.get(page, 0) for page in SOURCE_PAGES}}),
        ("qa.o015.mit-l07.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l07.semantic-witness", "artifact.mit.l07.target-source", "artifact.mit.l07.validation", "artifact.mit.l07.independent-rereview"], "source_math_nodes": 195, "target_math_nodes": 195, "display_formulas": 13, "formula_sequence_match": True}),
        ("qa.o015.mit-l07.figures", "figure_description_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l07.semantic-witness", "artifact.mit.l07.target-source", "artifact.mit.l07.validation", "artifact.mit.l07.visual-qa"], "source_figure_blocks": 4, "source_figure_panels": 6, "semantic_figure_descriptions": 4, "copied_source_graphics": 0, "reader_images": 0}),
        ("qa.o015.mit-l07.corrections", "correction_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l07.correction-snapshot", "artifact.mit.l07.semantic-witness", "artifact.mit.l07.target-source", "artifact.mit.l07.validation", "artifact.mit.l07.independent-rereview"], "source_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "correction_record_ids": ["correction.o015-mit-sem-0007", "correction.o015-mit-sem-0008"], "silent_normalization": False}),
        ("qa.o015.mit-l07.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l07.builder", "artifact.mit.l07.target-html", "artifact.mit.l07.target-pdf", "artifact.mit.l07.validation"], "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND, "deterministic_rebuilds": 2, "html_sha256": file_info(MIT_HTML)[1], "pdf_sha256": file_info(MIT_READER_PDF)[1], "toolchain": "Pandoc HTML5 and LuaLaTeX"}),
        ("qa.o015.mit-l07.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l07.target-html", "artifact.mit.l07.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": {"h1": 1, "h2": 11}, "math_nodes": 195, "display_math_nodes": 13, "images": 0, "source_pages": 10, "source_items": 16, "source_figures": 4, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l07.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l07.browser-qa", "artifact.mit.l07.target-html"], "desktop_viewport": [1280, 720], "mobile_viewport": [390, 844], "horizontal_overflow": False, "display_math_overflow": False, "live_measurement": True, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l07.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l07.target-pdf", "artifact.mit.l07.validation"], "pages": 4, "page_size": "A4", "lang": "id-ID", "searchable": True, "tagged": False, "images": 0, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l07.visual", "visual", "pass", {"witness_artifact_ids": ["artifact.mit.l07.visual-qa", "artifact.mit.l07.target-pdf"], "pages": 4, "all_pages_visually_inspected": True, "render_tool": "pdftoppm", "render_sha256": report["pdf"]["render_sha256"]}),
        ("qa.o015.mit-l07.semantic-rereview", "independent_semantic_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l07.independent-rereview", "artifact.mit.l07.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l07.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l07.target-html", "artifact.mit.l07.target-pdf", "artifact.mit.l07.browser-qa", "artifact.mit.l07.visual-qa"], "primary_surface": "semantic_html", "html_static_structure_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"], "human_review_is_release_gate": False}),
        ("qa.o015.mit-l07.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "human_review_is_release_gate": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded; this is evidence, not a hold."}),
        ("qa.o015.mit-l07.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l07.boundary-census", "artifact.mit.l07.semantic-witness", "artifact.mit.l07.target-source"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa", "o015-mit-l01-backend-tooling"], "source_graphics_in_boundary": 4, "source_graphics_redistributed": 0, "semantic_figure_descriptions": 4, "license": "CC BY-NC-SA 4.0", "change_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "non_endorsement": True}),
        ("qa.o015.mit-l07.csv-losslessness", "csv_losslessness", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l07", "artifact.o015.backend-validator-mit-l07"], "projection": "record_json is canonical JSON for each JSONL record", "utf8_strict": True, "row_order_matches_jsonl": True}),
        ("qa.o015.mit-l07.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l07", "artifact.o015.backend-validator-mit-l07", "artifact.o015.source-authority", "artifact.o015.component-rights"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_baseline_reconstruction_required": True, "independent_validation_runs_required": 2}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        status = "passed" if result == "pass" else result
        record = common("qa_event", record_id, status)
        record.update({"event_type": event_type, "result": result, "unit_id": MIT_L07_UNIT_ID, **extra})
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l07", "contains", MIT_ROOT_UNIT_ID, MIT_L07_UNIT_ID, "Seventh admitted MIT source-order boundary, complete-notes pages 29-38."),
        ("relation.mit.witness-edition-contains-l07", "contains", MIT_WITNESS_EDITION_ID, MIT_L07_UNIT_ID, "Page-addressed English semantic witness for pages 29-38."),
        ("relation.mit.target-edition-contains-l07", "contains", MIT_TARGET_EDITION_ID, MIT_L07_UNIT_ID, "Built Indonesian semantic derivative for pages 29-38."),
        ("relation.mit.l06-precedes-l07", "precedes", "unit.mit.ocw-6.253.l06", MIT_L07_UNIT_ID, "Source order advances from Lecture 2 pages 20-28 to Lecture 3 pages 29-38."),
        ("relation.mit.witness-adapts-authority-pdf-l07", "adapts", "artifact.mit.l07.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes PDF pages 29-38."),
        ("relation.mit.target-translates-witness-l07", "translates", "artifact.mit.l07.target-source", "artifact.mit.l07.semantic-witness", "Page/list/formula translation with disclosed corrections O015-MIT-SEM-0007 and 0008."),
        ("relation.mit.html-adapts-target-l07", "adapts", "artifact.mit.l07.target-html", "artifact.mit.l07.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l07", "adapts", "artifact.mit.l07.target-pdf", "artifact.mit.l07.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.browser-qa-depends-on-html-l07", "depends-on", "artifact.mit.l07.browser-qa", "artifact.mit.l07.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.visual-qa-depends-on-pdf-l07", "depends-on", "artifact.mit.l07.visual-qa", "artifact.mit.l07.target-pdf", "Rendered four-page visual QA evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l07", "depends-on", "artifact.mit.l07.validation", "artifact.mit.l07.browser-qa", "Validation receipt incorporates browser evidence."),
        ("relation.mit.validation-depends-on-visual-qa-l07", "depends-on", "artifact.mit.l07.validation", "artifact.mit.l07.visual-qa", "Validation receipt incorporates visual evidence."),
        ("relation.mit.rereview-depends-on-target-l07", "depends-on", "artifact.mit.l07.independent-rereview", "artifact.mit.l07.target-source", "Independent semantic rereview binds the admitted target source and readers."),
    ]
    for page in SOURCE_PAGES:
        relation_specs.append((f"relation.mit.l07-contains-p{page:03d}", "contains", MIT_L07_UNIT_ID, segment_ids[page], f"Lecture 3 contains source page {page}."))
    for page, index in display_pairs:
        relation_specs.append((f"relation.mit.l07-formula-p{page:03d}-d{index:03d}-illustrates-segment", "illustrates", f"surface.mit.l07.formula.p{page:03d}.d{index:03d}", segment_ids[page], DISPLAY_LABELS[(page, index)] + "."))
    for page in FIGURE_PANELS:
        relation_specs.append((f"relation.mit.l07-figure-p{page:03d}-illustrates-segment", "illustrates", f"surface.mit.l07.figure-description.p{page:03d}.f001", segment_ids[page], FIGURE_LABELS[page] + "."))
    for relation_id, relation_type, source_id, target_id, note in relation_specs:
        relation = common("relation", relation_id, "current")
        relation.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        add(relation)

    all_ids = baseline_ids | new_ids
    for record in new_records:
        for field in schema.get("reference_fields", []):
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")

    records.extend(new_records)
    entity_rank = {name: index for index, name in enumerate(schema["entity_order"])}
    records.sort(key=lambda record: (entity_rank[record["entity_type"]], record["id"]))
    jsonl_bytes = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    csv_buffer = io.StringIO(newline="")
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(["schema", "schema_version", "entity_type", "id", "record_json"])
    for record in records:
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)])
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    stage_backend(jsonl_bytes, csv_bytes)

    output = {
        "workflow": WORKFLOW,
        "protected_baseline_record_count": BASELINE_RECORD_COUNT,
        "new_record_count": len(new_records),
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
        "new_id_set_sha256": sha256(("\n".join(sorted(new_ids)) + "\n").encode("utf-8")),
        "final_record_count": len(records),
        "jsonl": {"bytes": len(jsonl_bytes), "sha256": sha256(jsonl_bytes)},
        "csv": {"bytes": len(csv_bytes), "sha256": sha256(csv_bytes)},
        "correction_snapshot": {"bytes": LEDGER_IDENTITY[0], "sha256": LEDGER_IDENTITY[1]},
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
