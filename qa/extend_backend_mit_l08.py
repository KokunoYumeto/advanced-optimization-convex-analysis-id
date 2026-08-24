#!/usr/bin/env python3
"""Add the reader-admitted MIT 6.253 Lecture 4 boundary (pages 39-49).

The admitted 1,820-record L07 backend is a protected byte-for-byte baseline.
This workflow removes only its own prior projection, proves that exact baseline
has been reconstructed, and deterministically recreates the L08 projection.
It refuses to mutate the backend until the reader, browser, visual, and clean
independent semantic-rereview evidence all exist and bind the current bytes.
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

RECORDED_AT = "2026-08-24T03:00:00Z"
WORKFLOW = "o015-mit-l08-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 1820
BASELINE_JSONL = (1_321_559, "1f6384b25937765bdd32e9ae59d68ac11772c15ddd250861d7d051742ad43843")
BASELINE_CSV = (1_586_211, "a6986c21e9757dd1750dd5e515e9038a973ecbeeae22db07d99ff81ea3f92985")
BASELINE_ID_SET_SHA256 = "18e876349873e4e0579cf45c539392e798486dbcb8e4be8a6ebfe1d912f873c6"
BASELINE_RECORD_SET_SHA256 = "5dbe23efc914bb90e6949470cf20b9be5981df4345576a1c3846fdb765012091"

MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L08_UNIT_ID = "unit.mit.ocw-6.253.l08"
SOURCE_PAGES = list(range(39, 50))
PAGE_ITEMS = {39: 4, 40: 5, 41: 1, 42: 2, 43: 4, 44: 1, 45: 1, 46: 2, 47: 1, 48: 2, 49: 4}
PAGE_NESTED = {39: 0, 40: 0, 41: 2, 42: 0, 43: 3, 44: 5, 45: 2, 46: 2, 47: 0, 48: 0, 49: 2}
PAGE_DISPLAYS = {39: 0, 40: 0, 41: 1, 42: 1, 43: 0, 44: 1, 45: 1, 46: 7, 47: 6, 48: 4, 49: 5}
FIGURE_PANELS = {40: 1, 41: 1, 42: 1, 44: 1, 48: 1}
DISPLAY_LABELS = {
    (41, 1): "positive-coordinate simplex subset used to prove nonempty relative interior",
    (42, 1): "concavity inequality along a prolonged segment",
    (44, 1): "relative-interior segment point",
    (45, 1): "general failures of image commutation for interior and closure",
    (46, 1): "relative interior of a vector sum",
    (46, 2): "closure inclusion for a vector sum",
    (46, 3): "bounded-set closure equality for a vector sum",
    (46, 4): "general relative-interior and closure intersection inclusions",
    (46, 5): "qualified relative-interior and closure intersection equalities",
    (46, 6): "closed-half-line intersection counterexample",
    (46, 7): "open-half-line intersection counterexample",
    (47, 1): "fiber of a convex set over x",
    (47, 2): "projected domain of nonempty fibers",
    (47, 3): "relative interior through projected fibers",
    (47, 4): "projection of the relative interior",
    (47, 5): "union decomposition of the relative interior by fibers",
    (47, 6): "relative interior of a fiber intersection",
    (48, 1): "normalized direction sequences",
    (48, 2): "upper convexity bound for the approaching sequence",
    (48, 3): "lower convexity bound through the opposite direction",
    (48, 4): "limsup estimates for the scaled corner values",
    (49, 1): "epigraph definition of function closure",
    (49, 2): "epigraph definition of convex closure",
    (49, 3): "equality of the three infima",
    (49, 4): "agreement with a convex function on relative interior of its domain",
    (49, 5): "one-sided limit formula for function closure",
}
FIGURE_LABELS = {
    40: "relative-interior line-segment principle",
    41: "positive-coordinate simplex construction inside a convex set",
    42: "interior minimum of a concave function",
    44: "closure and relative-interior segment construction",
    48: "unit-cube continuity construction",
}
SOURCE_TEXT_FINGERPRINTS = {
    39: (266, "7eea461ea346ad1d4f43be4350ca2597d2efe0270b41967307600a521de03b05"),
    40: (837, "85ff891678a524893f8cbacc5bf4cdd6d4540883d8d125ce415778b5d621dba5"),
    41: (1111, "0ea583c7109ed83a96c11d143aed939d5c18a07d5bdb74c537e22db1c3aa2939"),
    42: (821, "7120ed092593e2c64d5c8e52176ad37c646273e9c36a652a250d3710812d7c1c"),
    43: (779, "b71f771dd0b2736dc5d00bd36335bd9abcf2d1eccd5eb79df851804d2ac6fd75"),
    44: (979, "82c443c774d394a23127c0d66fd829f7f99a83e622e97a7b8e255db03c0d2d48"),
    45: (995, "c09764878d0d0d4f40ed91d6e5e5e32ddf432fc8e1fb84a5181f3aba365e1d47"),
    46: (820, "fd2317415e96c5b3cc51f944443b79f9a641725636fb482cbca3aa88e6d7f22c"),
    47: (968, "7f2b12088c43f11512cf5a5a8fe52beebc3c7b3a12051c5508fb8a25119eee34"),
    48: (1236, "6c8b085e04ccf58dae618b1ec85941d2db0dac71061cb02a9280cefc4e19c186"),
    49: (1413, "7b72fddf12936390ab46902418129de1fade11640cb7d65662277608b2f9d30a"),
    50: (289, "595b3d566a6d820573632a5dc853afb2c0cf8474fab8693a57d84ff33335ae63"),
}
SOURCE_RENDER_FINGERPRINTS = {
    39: (20561, "c5ffc7dfd5deaaeaf56597902f042fb531c63b5ab71f54fdc90ae624b8f38058"),
    40: (66533, "d50b834428c96184f920c572d15a7f1466e7845ec865a6ca77c8f143fee27234"),
    41: (63220, "b14884440cdbed75bc1d85b24781d61f307b3c4afbf68ae637a03f930a287aac"),
    42: (49746, "8aa7eac7d60a41fa9572c393ac04c897a0bae166539bbc632341ecba64e4f174"),
    43: (45343, "6acd12d261f1357fec724159fa8c4884ecf196a41e45d192762c05ec99234c1c"),
    44: (52575, "ad3721ea465a84e39b31147a596d36e9f269a9c455826ac4461e242dbbc78f18"),
    45: (64378, "730d9660db020777dd3abb5c80560b0c9a8b60b82da033dd768b52d580683aae"),
    46: (45494, "3ab5c51e539bc44695cf3f34ccb2dd68f8ef687c44b3e0d15d9a55b8d721df56"),
    47: (45331, "4373e8f76345f119ae561cf685305dbaf390692544f152d5bba235a1f4f16fc2"),
    48: (55671, "0a7fd72211de66560ff20f6198301e201a2e69d293604655fc79daf5242177b5"),
    49: (58998, "18af53a1bfb81f88b8e08189d6c8c35adcaa90dfaa716ad2a8b5a5c5ee07b061"),
}

MIT_PDF = "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
MIT_CENSUS = "00_control/MIT_L08_LECTURE_4_BOUNDARY_CENSUS.md"
MIT_LEDGER = "00_control/MIT_L08_CORRECTION_SNAPSHOT.jsonl"
MIT_WITNESS = "source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.md"
MIT_HTML = "output/html/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.pdf"
MIT_CSS = "source/id-ID/mit-l08.css"
MIT_PREAMBLE = "source/id-ID/mit-l08-preamble.tex"
MIT_FILTER = "source/id-ID/mit-l08-pdf-filter.lua"
MIT_BEFORE_BODY = "source/id-ID/mit-l08-before-body.html"
MIT_AFTER_BODY = "source/id-ID/mit-l08-after-body.html"
MIT_BUILDER = "qa/build_mit_l08.py"
MIT_VALIDATOR = "qa/validate_mit_l08.py"
MIT_REPORT = "qa/MIT_L08_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L08_BROWSER_QA.json"
MIT_VISUAL_QA = "qa/MIT_L08_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L08_INDEPENDENT_REREVIEW.md"

SOURCE_PDF_IDENTITY = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
LEDGER_IDENTITY = (2_347, "d99f8df4e722a9c98368bb169df17aa41d21754766b9ee19747a52569b40cb17")
CANONICAL_BUILD_COMMAND = (
    "python qa/build_mit_l08.py --html-output "
    "output/html/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.html "
    "--pdf-output output/pdf/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.pdf"
)
RECEIPT_BUILD_COMMAND = "python qa/build_mit_l08.py --html-output <html> --pdf-output <pdf>"

EXPECTED_LEDGER_EVENTS = {
    "O015-MIT-SEM-0009": {
        "event_id": "O015-MIT-SEM-0009",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF pages 42, 48, and 49; source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md",
        "surface": "Function-type arrows in Lecture 4",
        "source_issue": "Three declarations use the element-mapping arrow in expressions that state only a function's domain and codomain, repeating the determined notation issue in earlier lectures.",
        "target_action": "Preserved the printed mapsto arrows in the English semantic witness, normalized them to right arrows in the learner-facing Indonesian type declarations, and disclosed the correction in the edition notice.",
        "class": "determined_notation_correction",
    },
    "O015-MIT-SEM-0010": {
        "event_id": "O015-MIT-SEM-0010",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF page 43; source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md",
        "surface": "Commutation of relative interior and closure with linear inverse images",
        "source_issue": "The summary states the inverse-image commutation rules without the required feasibility qualification; in general both can fail when the linear map's range misses the relative interior of the target convex set.",
        "target_action": "Retained the source claim in the English witness, but qualified the learner-facing rule by A inverse of ri C nonempty, equivalently range A intersect ri C nonempty, and disclosed the scope correction in the edition notice.",
        "class": "determined_missing_hypothesis_correction",
    },
    "O015-MIT-SEM-0011": {
        "event_id": "O015-MIT-SEM-0011",
        "authority": "o015-mit-ocw-6.253-spring-2012",
        "source": "complete-notes PDF page 45; source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md",
        "surface": "Geometric intuition for a linear image of a relative ball",
        "source_issue": "The proof intuition says a general linear map sends spheres within C onto spheres within A C, but nonsimilarity linear maps produce ellipsoids or degenerate images rather than spheres.",
        "target_action": "Preserved the printed intuition in the English witness and replaced it in the learner-facing edition with the correct relative-neighborhood statement: the image of a relative neighborhood is a relative neighborhood in the image affine hull and contains an appropriate relative ball.",
        "class": "determined_geometric_intuition_correction",
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
        raise ValueError(f"{context} JSONL is not the protected 1,820-record baseline")
    if (len(csv_bytes), sha256(csv_bytes)) != BASELINE_CSV:
        raise ValueError(f"{context} CSV is not the protected 1,820-record baseline")


def stage_backend(jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    staged: list[Path] = []
    try:
        for destination, data in ((JSONL_PATH, jsonl_bytes), (CSV_PATH, csv_bytes)):
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.mit-l08-", suffix=".stage", dir=BACKEND, delete=False
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
        raise ValueError("L08 correction snapshot identity differs")
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), start=1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id not in EXPECTED_LEDGER_EVENTS or event_id in result:
            raise ValueError(f"unexpected or duplicate event in L08 snapshot: {event_id}")
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
        raise ValueError("L08 correction snapshot event set differs")
    return result


def load_qa_evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    visual = json.loads((ROOT / MIT_VISUAL_QA).read_text(encoding="utf-8"))
    expected_boundary = {
        "copied_source_graphics": 0,
        "nested_items": 16,
        "next_heading": "LECTURE 5 - LECTURE OUTLINE",
        "next_source_page": 50,
        "source_displays": 26,
        "source_figure_panels": 5,
        "source_figures": 5,
        "source_items": 27,
        "source_pdf_pages": SOURCE_PAGES,
    }
    boundary = report.get("boundary", {})
    if report.get("result") != "pass" or report.get("errors") != [] or any(boundary.get(key) != value for key, value in expected_boundary.items()):
        raise ValueError("MIT L08 content validation receipt differs")
    formula_inventory = report.get("formula_inventory", {})
    if (
        formula_inventory.get("witness_display_blocks") != 26
        or formula_inventory.get("target_display_blocks") != 26
        or not re.fullmatch(r"[0-9a-f]{64}", str(formula_inventory.get("witness_sequence_sha256", "")))
        or not re.fullmatch(r"[0-9a-f]{64}", str(formula_inventory.get("target_sequence_sha256", "")))
    ):
        raise ValueError("MIT L08 formula inventory is not validated")
    expected_text = {str(page): identity[1] for page, identity in SOURCE_TEXT_FINGERPRINTS.items()}
    if report.get("source_page_text_sha256") != expected_text:
        raise ValueError("MIT L08 source-page text fingerprints differ")
    html_identity = file_info(MIT_HTML)
    pdf_identity = file_info(MIT_READER_PDF)
    build = report.get("build", {})
    if build.get("command") != RECEIPT_BUILD_COMMAND or build.get("deterministic_rebuilds") != 2:
        raise ValueError("MIT L08 deterministic-build receipt differs")
    expected_build = {"html": list(html_identity), "pdf": list(pdf_identity)}
    if build.get("expected") != expected_build:
        raise ValueError("MIT L08 expected build identities differ")
    canonical_build = build.get("canonical", {})
    if (
        (canonical_build.get("html", {}).get("bytes"), canonical_build.get("html", {}).get("sha256")) != html_identity
        or (canonical_build.get("pdf", {}).get("bytes"), canonical_build.get("pdf", {}).get("sha256")) != pdf_identity
        or canonical_build.get("status") != "bound"
    ):
        raise ValueError("MIT L08 canonical build binding differs")
    expected_rebuild = [{"html": list(html_identity), "pdf": list(pdf_identity)}] * 2
    if build.get("rebuild_identities") != expected_rebuild:
        raise ValueError("MIT L08 deterministic-build hash sequence differs")
    html = report.get("html", {})
    if (
        html.get("lang") != "id-ID"
        or html.get("source_pages") != 11
        or html.get("source_items") != 27
        or html.get("source_displays") != 26
        or html.get("source_figures") != 5
        or html.get("display_math_nodes") != 26
        or html.get("images") != 0
        or html.get("duplicate_ids") != []
        or html.get("unresolved_fragments") != []
    ):
        raise ValueError("MIT L08 HTML topology differs")
    pdf = report.get("pdf", {})
    if pdf.get("pages", 0) < 1 or pdf.get("page_size") != "A4" or pdf.get("searchable") is not True or pdf.get("tagged") is not False or pdf.get("images") != 0:
        raise ValueError("MIT L08 PDF topology differs")
    if browser.get("result") != "pass" or visual.get("inspection", {}).get("result") != "pass":
        raise ValueError("MIT L08 browser/visual evidence is not passing")
    if (browser.get("build", {}).get("html_bytes"), browser.get("build", {}).get("html_sha256")) != html_identity:
        raise ValueError("MIT L08 browser receipt binds stale HTML")
    if (visual.get("pdf", {}).get("bytes"), visual.get("pdf", {}).get("sha256")) != pdf_identity:
        raise ValueError("MIT L08 visual receipt binds stale PDF")
    if report.get("pdf", {}).get("render_sha256") != [item["sha256"] for item in visual.get("renders", [])]:
        raise ValueError("MIT L08 render hash sequence differs between receipts")
    for item in report.get("files", []):
        path = item.get("path")
        if path and file_info(path) != (item.get("bytes"), item.get("sha256")):
            raise ValueError(f"MIT L08 validation receipt binds stale bytes: {path}")
    rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
    for path in (MIT_CENSUS, MIT_WITNESS, MIT_TARGET):
        if file_info(path)[1] not in rereview:
            raise ValueError(f"MIT L08 independent rereview does not bind {path}")
    if not re.search(r"P1\s*=\s*0\s*,\s*P2\s*=\s*0\s*,\s*P3\s*=\s*0", rereview):
        raise ValueError("MIT L08 independent rereview severity disposition differs")
    return report, browser, visual


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema":
        raise ValueError("backend schema identity differs")
    if file_info(MIT_PDF) != SOURCE_PDF_IDENTITY:
        raise ValueError("MIT authority PDF identity differs")
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

    segment_ids = {page: f"d90.mit.ocw-6.253.l08.p{page:03d}" for page in SOURCE_PAGES}
    item_ids = [f"d90-mit-l08-p{page:03d}-i{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)]
    display_pairs = [(page, index) for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)]
    html = report["html"]
    pdf = report["pdf"]

    unit = common("unit", MIT_L08_UNIT_ID, "visually_checked")
    unit.update({
        "edition_id": MIT_TARGET_EDITION_ID,
        "unit_kind": "lecture_topic",
        "order": 8,
        "source_local_id": "lecture-4-pages-39-49",
        "source_local_label": "Lecture 4 - Relative Interior, Closure, and Continuity",
        "target_local_label": "Kuliah 4 - Interior Relatif, Penutupan, dan Kontinuitas",
        "rights_id": "rights.o015-mit-id-pilot",
        "source_edition_id": MIT_WITNESS_EDITION_ID,
        "target_edition_id": MIT_TARGET_EDITION_ID,
        "source_pdf_pages": SOURCE_PAGES,
        "next_source_page": 50,
        "next_source_heading": "LECTURE 5 - LECTURE OUTLINE",
        "translation_state": "visually_checked",
        "parent_id": MIT_ROOT_UNIT_ID,
        "source_item_count": 27,
        "nested_source_item_count": 16,
        "source_item_ids": item_ids,
        "target_item_ids": item_ids,
        "source_display_count": 26,
        "source_display_ids": [f"d90-mit-l08-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "target_display_ids": [f"d90-mit-l08-p{page:03d}-d{index:03d}" for page, index in display_pairs],
        "source_figure_count": 5,
        "source_figure_ids": [f"d90-mit-l08-p{page:03d}-f001" for page in FIGURE_PANELS],
        "target_figure_ids": [f"d90-mit-l08-p{page:03d}-f001" for page in FIGURE_PANELS],
        "source_figure_panel_count": 5,
        "copied_source_graphics": 0,
        "correction_event_ids": sorted(EXPECTED_LEDGER_EVENTS),
        "canonical_build_command": CANONICAL_BUILD_COMMAND,
    })
    add(unit)

    for order, page in enumerate(SOURCE_PAGES, start=1):
        anchor = f"d90-mit-l08-p{page:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("segment", segment_ids[page], "visually_checked")
        record.update({
            "unit_id": MIT_L08_UNIT_ID,
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
            "anchor_mapping_rule": "identical d90-mit-l08 stable anchor preserved from witness to target",
        })
        add(record)

    for global_order, (page, index) in enumerate(display_pairs, start=1):
        anchor = f"d90-mit-l08-p{page:03d}-d{index:03d}"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l08.formula.p{page:03d}.d{index:03d}", "present")
        record.update({
            "unit_id": MIT_L08_UNIT_ID,
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
        anchor = f"d90-mit-l08-p{page:03d}-f001"
        source_slice = fenced_div_slice(MIT_WITNESS, anchor)
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        record = common("learning_surface", f"surface.mit.l08.figure-description.p{page:03d}.f001", "present_with_limitation")
        record.update({
            "unit_id": MIT_L08_UNIT_ID,
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

    correction_specs = {
        "O015-MIT-SEM-0009": {
            "record_id": "correction.o015-mit-sem-0009",
            "pages": [42, 48, 49],
            "source_locator": "complete-notes PDF pages 42, 48, and 49; function type declarations",
            "anchors": ["p042-i001", "p048-i001", "p049-i001", "p049-i003", "p049-i004"],
        },
        "O015-MIT-SEM-0010": {
            "record_id": "correction.o015-mit-sem-0010",
            "pages": [43],
            "source_locator": "complete-notes PDF page 43; inverse-image commutation summary",
            "anchors": ["p043-i002"],
        },
        "O015-MIT-SEM-0011": {
            "record_id": "correction.o015-mit-sem-0011",
            "pages": [45],
            "source_locator": "complete-notes PDF page 45; geometric proof intuition",
            "anchors": ["p045"],
        },
    }
    for event_id, spec in correction_specs.items():
        event, binding = events[event_id]
        correction = common("correction", spec["record_id"], "applied_in_admitted_reader")
        correction.update({
            "source_event_id": event_id,
            "source_edition_id": MIT_SOURCE_EDITION_ID,
            "affected_unit_ids": [MIT_L08_UNIT_ID],
            "affected_segment_ids": [segment_ids[page] for page in spec["pages"]],
            "source_path": MIT_PDF,
            "source_pdf_pages": spec["pages"],
            "source_locator": spec["source_locator"],
            "witness_locators": [f"{MIT_WITNESS}#d90-mit-l08-{anchor}" for anchor in spec["anchors"]],
            "target_locators": [f"{MIT_TARGET}#d90-mit-l08-{anchor}" for anchor in spec["anchors"]],
            "surface": event["surface"],
            "source_issue": event["source_issue"],
            "target_action": event["target_action"],
            "correction_class": event["class"],
            "disposition": "applied_in_admitted_reader",
            "shared_ledger_state": "immutable_boundary_snapshot",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.mit.l08.correction-snapshot",
            **binding,
        })
        add(correction)

    artifact_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("artifact.mit.l08.boundary-census", "boundary_census", MIT_CENSUS, "rights.o015-mit-pilot-build-qa", {"source_pdf_pages": SOURCE_PAGES, "next_source_page": 50}),
        ("artifact.mit.l08.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, "rights.o015-mit-semantic-witness", {"source_pdf_pages": SOURCE_PAGES, "official_editable_source": False, "source_item_count": 27, "nested_source_item_count": 16, "source_display_count": 26, "source_figure_description_count": 5}),
        ("artifact.mit.l08.target-source", "semantic_translation_source", MIT_TARGET, "rights.o015-mit-id-pilot", {"locale": "id-ID", "source_pdf_pages": SOURCE_PAGES, "source_item_count": 27, "nested_source_item_count": 16, "source_display_count": 26, "source_figure_description_count": 5, "correction_event_ids": sorted(EXPECTED_LEDGER_EVENTS)}),
        ("artifact.mit.l08.target-html", "semantic_html_reader", MIT_HTML, "rights.o015-mit-id-pilot", {"locale": "id-ID", "math_format": "MathML", "source_pages": 11, "source_displays": 26, "source_figures": 5, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l08.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, "rights.o015-mit-id-pilot", {"locale": "id-ID", "pages": pdf["pages"], "page_size": "A4", "tagged": False, "searchable": True, "images": 0, "canonical_build_command": CANONICAL_BUILD_COMMAND}),
        ("artifact.mit.l08.builder", "deterministic_builder", MIT_BUILDER, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Pandoc HTML5 and LuaLaTeX", "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND}),
        ("artifact.mit.l08.validator", "validation_script", MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library plus pypdf"}),
        ("artifact.mit.l08.validation", "validation_report", MIT_REPORT, "rights.o015-mit-pilot-build-qa", {"result": "pass", "errors": []}),
        ("artifact.mit.l08.browser-qa", "browser_qa_report", MIT_BROWSER_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "live_viewport_measurement": True}),
        ("artifact.mit.l08.visual-qa", "visual_qa_report", MIT_VISUAL_QA, "rights.o015-mit-pilot-build-qa", {"result": "pass", "pages": pdf["pages"]}),
        ("artifact.mit.l08.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, "rights.o015-mit-pilot-build-qa", {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}, "human_native_speaker_review": False}),
        ("artifact.mit.l08.correction-snapshot", "correction_ledger_snapshot", MIT_LEDGER, "rights.o015-mit-pilot-build-qa", {"source_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "immutable_boundary_snapshot": True, "event_bindings": [events[event_id][1] for event_id in sorted(events)]}),
        ("artifact.mit.l08.css", "html_stylesheet", MIT_CSS, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l08.pdf-preamble", "pdf_preamble", MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l08.pdf-filter", "pandoc_lua_filter", MIT_FILTER, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l08.before-body", "html_include", MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.mit.l08.after-body", "html_include", MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling", {}),
        ("artifact.o015.backend-generator-mit-l08", "backend_generator", "qa/extend_backend_mit_l08.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "protected_baseline_record_count": BASELINE_RECORD_COUNT}),
        ("artifact.o015.backend-validator-mit-l08", "backend_validator", "qa/validate_backend_mit_l08.py", "rights.o015-mit-l01-backend-tooling", {"toolchain": "Python 3 standard library", "independent_validation_runs_required": 2}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    math_nodes = html["math_nodes"]
    pdf_pages = pdf["pages"]
    correction_ids = [f"correction.o015-mit-sem-{number:04d}" for number in range(9, 12)]
    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l08.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.mit.complete-notes-pdf", "artifact.mit.l08.boundary-census", "artifact.mit.l08.semantic-witness"], "authority_pdf_pages": 340, "boundary_pages": SOURCE_PAGES, "next_source_page": 50, "next_source_page_text_sha256": SOURCE_TEXT_FINGERPRINTS[50][1]}),
        ("qa.o015.mit-l08.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l08.semantic-witness", "artifact.mit.l08.target-source", "artifact.mit.l08.validation"], "official_editable_source": False, "source_items": 27, "nested_source_items": 16, "source_figures": 5}),
        ("qa.o015.mit-l08.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l08.validation", "artifact.mit.l08.boundary-census"], "source_page_map": [[page, page] for page in SOURCE_PAGES], "item_counts": {str(page): PAGE_ITEMS[page] for page in SOURCE_PAGES}, "nested_item_counts": {str(page): PAGE_NESTED[page] for page in SOURCE_PAGES}, "display_counts": {str(page): PAGE_DISPLAYS[page] for page in SOURCE_PAGES}, "figure_panel_counts": {str(page): FIGURE_PANELS.get(page, 0) for page in SOURCE_PAGES}}),
        ("qa.o015.mit-l08.formulas", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l08.semantic-witness", "artifact.mit.l08.target-source", "artifact.mit.l08.validation", "artifact.mit.l08.independent-rereview"], "source_math_nodes": math_nodes, "target_math_nodes": math_nodes, "display_formulas": 26, "formula_sequence_match": True}),
        ("qa.o015.mit-l08.figures", "figure_description_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l08.semantic-witness", "artifact.mit.l08.target-source", "artifact.mit.l08.validation", "artifact.mit.l08.visual-qa"], "source_figure_blocks": 5, "source_figure_panels": 5, "semantic_figure_descriptions": 5, "copied_source_graphics": 0, "reader_images": 0}),
        ("qa.o015.mit-l08.corrections", "correction_integrity", "pass", {"witness_artifact_ids": ["artifact.mit.l08.correction-snapshot", "artifact.mit.l08.semantic-witness", "artifact.mit.l08.target-source", "artifact.mit.l08.validation", "artifact.mit.l08.independent-rereview"], "source_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "correction_record_ids": correction_ids, "silent_normalization": False}),
        ("qa.o015.mit-l08.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l08.builder", "artifact.mit.l08.target-html", "artifact.mit.l08.target-pdf", "artifact.mit.l08.validation"], "canonical_build_command": CANONICAL_BUILD_COMMAND, "receipt_command_template": RECEIPT_BUILD_COMMAND, "deterministic_rebuilds": 2, "html_sha256": file_info(MIT_HTML)[1], "pdf_sha256": file_info(MIT_READER_PDF)[1], "toolchain": "Pandoc HTML5 and LuaLaTeX"}),
        ("qa.o015.mit-l08.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l08.target-html", "artifact.mit.l08.validation"], "lang": "id-ID", "main_landmarks": 1, "headings": html["headings"], "math_nodes": math_nodes, "display_math_nodes": 26, "images": 0, "source_pages": 11, "source_items": 27, "source_figures": 5, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l08.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l08.browser-qa", "artifact.mit.l08.target-html"], "desktop_viewport": [1280, 720], "mobile_viewport": [390, 844], "horizontal_overflow": False, "display_math_overflow": False, "live_measurement": True, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l08.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l08.target-pdf", "artifact.mit.l08.validation"], "pages": pdf_pages, "page_size": "A4", "lang": "id-ID", "searchable": True, "tagged": False, "images": 0, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l08.visual", "visual", "pass", {"witness_artifact_ids": ["artifact.mit.l08.visual-qa", "artifact.mit.l08.target-pdf"], "pages": pdf_pages, "all_pages_visually_inspected": True, "render_tool": "pdftoppm", "render_sha256": pdf["render_sha256"]}),
        ("qa.o015.mit-l08.semantic-rereview", "independent_semantic_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l08.independent-rereview", "artifact.mit.l08.validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l08.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l08.target-html", "artifact.mit.l08.target-pdf", "artifact.mit.l08.browser-qa", "artifact.mit.l08.visual-qa"], "primary_surface": "semantic_html", "html_static_structure_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"], "human_review_is_release_gate": False}),
        ("qa.o015.mit-l08.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "human_review_is_release_gate": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded; this is evidence, not a hold."}),
        ("qa.o015.mit-l08.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l08.boundary-census", "artifact.mit.l08.semantic-witness", "artifact.mit.l08.target-source"], "component_ids": ["o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa", "o015-mit-l01-backend-tooling"], "source_graphics_in_boundary": 5, "source_graphics_redistributed": 0, "semantic_figure_descriptions": 5, "license": "CC BY-NC-SA 4.0", "change_event_ids": sorted(EXPECTED_LEDGER_EVENTS), "non_endorsement": True}),
        ("qa.o015.mit-l08.csv-losslessness", "csv_losslessness", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l08", "artifact.o015.backend-validator-mit-l08"], "projection": "record_json is canonical JSON for each JSONL record", "utf8_strict": True, "row_order_matches_jsonl": True}),
        ("qa.o015.mit-l08.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l08", "artifact.o015.backend-validator-mit-l08", "artifact.o015.source-authority", "artifact.o015.component-rights"], "protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_baseline_reconstruction_required": True, "independent_validation_runs_required": 2}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        status = "passed" if result == "pass" else result
        record = common("qa_event", record_id, status)
        record.update({"event_type": event_type, "result": result, "unit_id": MIT_L08_UNIT_ID, **extra})
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.work-contains-l08", "contains", MIT_ROOT_UNIT_ID, MIT_L08_UNIT_ID, "Eighth admitted MIT source-order boundary, complete-notes pages 39-49."),
        ("relation.mit.witness-edition-contains-l08", "contains", MIT_WITNESS_EDITION_ID, MIT_L08_UNIT_ID, "Page-addressed English semantic witness for pages 39-49."),
        ("relation.mit.target-edition-contains-l08", "contains", MIT_TARGET_EDITION_ID, MIT_L08_UNIT_ID, "Built Indonesian semantic derivative for pages 39-49."),
        ("relation.mit.l07-precedes-l08", "precedes", "unit.mit.ocw-6.253.l07", MIT_L08_UNIT_ID, "Source order advances from Lecture 3 pages 29-38 to Lecture 4 pages 39-49."),
        ("relation.mit.witness-adapts-authority-pdf-l08", "adapts", "artifact.mit.l08.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes PDF pages 39-49."),
        ("relation.mit.target-translates-witness-l08", "translates", "artifact.mit.l08.target-source", "artifact.mit.l08.semantic-witness", "Page/list/formula translation with disclosed corrections O015-MIT-SEM-0009 through 0011."),
        ("relation.mit.html-adapts-target-l08", "adapts", "artifact.mit.l08.target-html", "artifact.mit.l08.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target-l08", "adapts", "artifact.mit.l08.target-pdf", "artifact.mit.l08.target-source", "Deterministic A4 reflowed PDF build."),
        ("relation.mit.browser-qa-depends-on-html-l08", "depends-on", "artifact.mit.l08.browser-qa", "artifact.mit.l08.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.visual-qa-depends-on-pdf-l08", "depends-on", "artifact.mit.l08.visual-qa", "artifact.mit.l08.target-pdf", "Rendered visual QA evidence."),
        ("relation.mit.validation-depends-on-browser-qa-l08", "depends-on", "artifact.mit.l08.validation", "artifact.mit.l08.browser-qa", "Validation receipt incorporates browser evidence."),
        ("relation.mit.validation-depends-on-visual-qa-l08", "depends-on", "artifact.mit.l08.validation", "artifact.mit.l08.visual-qa", "Validation receipt incorporates visual evidence."),
        ("relation.mit.rereview-depends-on-target-l08", "depends-on", "artifact.mit.l08.independent-rereview", "artifact.mit.l08.target-source", "Independent semantic rereview binds the admitted target source and readers."),
    ]
    for page in SOURCE_PAGES:
        relation_specs.append((f"relation.mit.l08-contains-p{page:03d}", "contains", MIT_L08_UNIT_ID, segment_ids[page], f"Lecture 4 contains source page {page}."))
    for page, index in display_pairs:
        relation_specs.append((f"relation.mit.l08-formula-p{page:03d}-d{index:03d}-illustrates-segment", "illustrates", f"surface.mit.l08.formula.p{page:03d}.d{index:03d}", segment_ids[page], DISPLAY_LABELS[(page, index)] + "."))
    for page in FIGURE_PANELS:
        relation_specs.append((f"relation.mit.l08-figure-p{page:03d}-illustrates-segment", "illustrates", f"surface.mit.l08.figure-description.p{page:03d}.f001", segment_ids[page], FIGURE_LABELS[page] + "."))
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

    expected_entity_counts = Counter({"unit": 1, "segment": 11, "learning_surface": 31, "correction": 3, "artifact": 19, "qa_event": 17, "relation": 55})
    if Counter(record["entity_type"] for record in new_records) != expected_entity_counts or len(new_records) != 137:
        raise ValueError("L08 generated topology differs from the admitted 137-record contract")

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
