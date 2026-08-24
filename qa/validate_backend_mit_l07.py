#!/usr/bin/env python3
"""Independent fail-closed validation of the MIT L07 backend admission."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
RECEIPT_PATH = ROOT / "qa/MIT_L07_BACKEND_VALIDATION.json"

RECORDED_AT = "2026-08-24T02:00:00Z"
WORKFLOW = "o015-mit-l07-backend-v1"
UNIT_ID = "unit.mit.ocw-6.253.l07"
SOURCE_PAGES = list(range(29, 39))
BASELINE_COUNT = 1714
BASELINE_JSONL = (1_231_983, "9ad375756d2ee3159acf760f5d68084d2921e665cf993e2aaa6514f1e710337e")
BASELINE_CSV = (1_480_312, "f5c81e38ee9d1b4e9d2bcc7632603266fcf271b9b8c6454e99ba3e4b0041f72f")
BASELINE_ID_SET_SHA256 = "c3b38e218f00ed53325121b06d715a5e60993a2745cdf7888c75f8879ac4f57b"
BASELINE_RECORD_SET_SHA256 = "7953fb9b891b531cf87a19b447158dce2852d8e33ce7ae160fdcab78d0d8a419"

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
MIT_BROWSER = "qa/MIT_L07_BROWSER_QA.json"
MIT_VISUAL = "qa/MIT_L07_VISUAL_QA.json"
MIT_REREVIEW = "qa/MIT_L07_INDEPENDENT_REREVIEW.md"
MIT_BACKEND_GENERATOR = "qa/extend_backend_mit_l07.py"
MIT_BACKEND_VALIDATOR = "qa/validate_backend_mit_l07.py"

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
    MIT_BROWSER: (2_468, "f29fdb2086693efe892ac0a0d346fa19c7d57de8371d7ccc0317edaf6e8bf9d7"),
    MIT_VISUAL: (2_472, "1caf7ebc941616122adade72ecc7efbf68e9b8a9499290f0782bf2e11e0cadd2"),
    MIT_REREVIEW: (4_136, "d5f0bfc23b7a9b74d30570de9b2bd058c0ded84b51414b7b0b929349764ea86d"),
    MIT_HTML: (77_399, "cc3b4f665d5f0b4cb9e26245ec0cce71658c6c0b3e5e07cee3fcabfb43df5e13"),
    MIT_READER_PDF: (75_885, "2c7b4defaa56578f628c048dc4f17ee06b61f2bc33122b172af5539a5dae2eec"),
    MIT_LEDGER: LEDGER_IDENTITY,
}
EXPECTED_EVENTS = {
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

ARTIFACTS = {
    "artifact.mit.l07.boundary-census": (MIT_CENSUS, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l07.semantic-witness": (MIT_WITNESS, "rights.o015-mit-semantic-witness"),
    "artifact.mit.l07.target-source": (MIT_TARGET, "rights.o015-mit-id-pilot"),
    "artifact.mit.l07.target-html": (MIT_HTML, "rights.o015-mit-id-pilot"),
    "artifact.mit.l07.target-pdf": (MIT_READER_PDF, "rights.o015-mit-id-pilot"),
    "artifact.mit.l07.builder": (MIT_BUILDER, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l07.validator": (MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l07.validation": (MIT_REPORT, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l07.browser-qa": (MIT_BROWSER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l07.visual-qa": (MIT_VISUAL, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l07.independent-rereview": (MIT_REREVIEW, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l07.correction-snapshot": (MIT_LEDGER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l07.css": (MIT_CSS, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l07.pdf-preamble": (MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l07.pdf-filter": (MIT_FILTER, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l07.before-body": (MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l07.after-body": (MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-generator-mit-l07": (MIT_BACKEND_GENERATOR, "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-validator-mit-l07": (MIT_BACKEND_VALIDATOR, "rights.o015-mit-l01-backend-tooling"),
}
QA_IDS = {
    "qa.o015.mit-l07.source-freeze",
    "qa.o015.mit-l07.semantic-reconstruction",
    "qa.o015.mit-l07.topology",
    "qa.o015.mit-l07.formulas",
    "qa.o015.mit-l07.figures",
    "qa.o015.mit-l07.corrections",
    "qa.o015.mit-l07.build",
    "qa.o015.mit-l07.html",
    "qa.o015.mit-l07.browser",
    "qa.o015.mit-l07.pdf",
    "qa.o015.mit-l07.visual",
    "qa.o015.mit-l07.semantic-rereview",
    "qa.o015.mit-l07.accessibility",
    "qa.o015.mit-l07.language",
    "qa.o015.mit-l07.rights",
    "qa.o015.mit-l07.csv-losslessness",
    "qa.o015.mit-l07.backend-integration",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), digest(data)


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def id_set(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def record_set(records: list[dict[str, Any]]) -> str:
    return digest("".join(canonical(record) + "\n" for record in sorted(records, key=lambda item: item["id"])).encode("utf-8"))


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
        raise ValueError(f"unclosed fenced div #{anchor}")
    payload = ("\n".join(lines[start:end + 1]) + "\n").encode("utf-8")
    return start + 1, end + 1, len(payload), digest(payload)


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


def ledger_events() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    if file_info(MIT_LEDGER) != LEDGER_IDENTITY:
        raise ValueError("L07 correction snapshot identity differs")
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_number, raw_line in enumerate((ROOT / MIT_LEDGER).read_bytes().splitlines(keepends=True), start=1):
        event = json.loads(raw_line.decode("utf-8"))
        event_id = event.get("event_id")
        if event_id not in EXPECTED_EVENTS or event_id in result or event != EXPECTED_EVENTS[event_id]:
            raise ValueError(f"correction snapshot event differs: {event_id}")
        result[event_id] = (event, {
            "ledger_path": MIT_LEDGER,
            "raw_line_start": line_number,
            "raw_line_end": line_number,
            "raw_line_bytes": len(raw_line),
            "raw_line_sha256": digest(raw_line),
            "raw_line_newline": "crlf" if raw_line.endswith(b"\r\n") else "lf" if raw_line.endswith(b"\n") else "none",
            "canonical_event_sha256": digest(canonical(event).encode("utf-8")),
        })
    if set(result) != set(EXPECTED_EVENTS):
        raise ValueError("correction snapshot event set differs")
    return result


def expected_ids() -> set[str]:
    ids = {UNIT_ID}
    ids.update(f"d90.mit.ocw-6.253.l07.p{page:03d}" for page in SOURCE_PAGES)
    ids.update(f"surface.mit.l07.formula.p{page:03d}.d{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1))
    ids.update(f"surface.mit.l07.figure-description.p{page:03d}.f001" for page in FIGURE_PANELS)
    ids.update({"correction.o015-mit-sem-0007", "correction.o015-mit-sem-0008"})
    ids.update(ARTIFACTS)
    ids.update(QA_IDS)
    ids.update({
        "relation.mit.work-contains-l07",
        "relation.mit.witness-edition-contains-l07",
        "relation.mit.target-edition-contains-l07",
        "relation.mit.l06-precedes-l07",
        "relation.mit.witness-adapts-authority-pdf-l07",
        "relation.mit.target-translates-witness-l07",
        "relation.mit.html-adapts-target-l07",
        "relation.mit.pdf-adapts-target-l07",
        "relation.mit.browser-qa-depends-on-html-l07",
        "relation.mit.visual-qa-depends-on-pdf-l07",
        "relation.mit.validation-depends-on-browser-qa-l07",
        "relation.mit.validation-depends-on-visual-qa-l07",
        "relation.mit.rereview-depends-on-target-l07",
    })
    ids.update(f"relation.mit.l07-contains-p{page:03d}" for page in SOURCE_PAGES)
    ids.update(f"relation.mit.l07-formula-p{page:03d}-d{index:03d}-illustrates-segment" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1))
    ids.update(f"relation.mit.l07-figure-p{page:03d}-illustrates-segment" for page in FIGURE_PANELS)
    return ids


def main() -> int:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    schema: dict[str, Any] = {}
    records: list[dict[str, Any]] = []
    rows: list[dict[str, str]] = []
    raw_jsonl = b""
    raw_csv = b""
    baseline_records: list[dict[str, Any]] = []
    events: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        check(schema.get("schema") == "o015-modular-backend-schema", "backend schema identity differs")
        raw_jsonl = JSONL_PATH.read_bytes()
        raw_csv = CSV_PATH.read_bytes()
        records = [json.loads(line) for line in raw_jsonl.decode("utf-8", errors="strict").splitlines() if line]
        rows = list(csv.DictReader(io.StringIO(raw_csv.decode("utf-8", errors="strict"))))
        check([json.loads(row["record_json"]) for row in rows] == records, "CSV projection differs from JSONL")
        check(len({record.get("id") for record in records}) == len(records), "backend contains duplicate IDs")
        check(all(canonical(record).encode("utf-8") + b"\n" == line for record, line in zip(records, raw_jsonl.splitlines(keepends=True))), "JSONL is not canonical one-record-per-line JSON")
        entity_rank = {name: index for index, name in enumerate(schema.get("entity_order", []))}
        check(records == sorted(records, key=lambda record: (entity_rank[record["entity_type"]], record["id"])), "backend order differs from schema order then stable ID")
        stripped_jsonl = strip_workflow_jsonl(raw_jsonl)
        stripped_csv = strip_workflow_csv(raw_csv)
        check((len(stripped_jsonl), digest(stripped_jsonl)) == BASELINE_JSONL, "protected JSONL baseline is not reconstructed byte-for-byte")
        check((len(stripped_csv), digest(stripped_csv)) == BASELINE_CSV, "protected CSV baseline is not reconstructed byte-for-byte")
        baseline_records = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
        check(len(baseline_records) == BASELINE_COUNT, "protected baseline record count differs")
        check(id_set(baseline_records) == BASELINE_ID_SET_SHA256, "protected baseline ID-set hash differs")
        check(record_set(baseline_records) == BASELINE_RECORD_SET_SHA256, "protected baseline record-set hash differs")
        workflow_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
        check({record["id"] for record in workflow_records} == expected_ids(), "L07 workflow stable-ID set differs")
        check(len(workflow_records) == 106, f"L07 workflow record count differs: {len(workflow_records)}")
        check(Counter(record["entity_type"] for record in workflow_records) == Counter({"unit": 1, "segment": 10, "learning_surface": 17, "correction": 2, "artifact": 19, "qa_event": 17, "relation": 40}), "L07 entity-type counts differ")
    except Exception as exc:
        errors.append(f"backend load/baseline check failed: {exc}")

    by_id = {record.get("id"): record for record in records}
    new_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    for record in new_records:
        check(record.get("schema") == "o015-modular-backend-record" and record.get("schema_version") == "1.0.0", f"{record.get('id')}: common schema differs")
        check(record.get("recorded_at") == RECORDED_AT, f"{record.get('id')}: recorded_at differs")
        for field in schema.get("required_common", []):
            check(field in record, f"{record.get('id')}: missing common field {field}")
        for field in schema.get("required_by_entity", {}).get(record.get("entity_type"), []):
            check(field in record, f"{record.get('id')}: missing entity field {field}")
        check(bool(re.fullmatch(schema.get("id_pattern", r".*"), record.get("id", ""))), f"{record.get('id')}: stable ID pattern differs")
        for field in schema.get("reference_fields", []):
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                check(value in by_id, f"{record.get('id')}: dangling {field}={value}")

    unit = by_id.get(UNIT_ID, {})
    check(unit.get("entity_type") == "unit" and unit.get("order") == 7, "L07 unit identity/order differs")
    check(unit.get("source_pdf_pages") == SOURCE_PAGES and unit.get("next_source_page") == 39, "L07 unit boundary differs")
    check((unit.get("source_item_count"), unit.get("nested_source_item_count"), unit.get("source_display_count"), unit.get("source_figure_count"), unit.get("source_figure_panel_count"), unit.get("copied_source_graphics")) == (16, 14, 13, 4, 6, 0), "L07 unit topology differs")
    check(unit.get("correction_event_ids") == sorted(EXPECTED_EVENTS), "L07 unit correction IDs differ")
    check(unit.get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "L07 unit build command differs")

    formula_order = 0
    for order, page in enumerate(SOURCE_PAGES, start=1):
        segment_id = f"d90.mit.ocw-6.253.l07.p{page:03d}"
        segment = by_id.get(segment_id, {})
        source_anchor = f"src-mit-l07-p{page:03d}"
        target_anchor = f"d90-mit-l07-p{page:03d}"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
            target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
            check((segment.get("source_line_start"), segment.get("source_line_end"), segment.get("source_bytes"), segment.get("source_content_sha256")) == source_slice, f"{segment_id}: source slice differs")
            check((segment.get("target_line_start"), segment.get("target_line_end"), segment.get("target_bytes"), segment.get("target_content_sha256")) == target_slice, f"{segment_id}: target slice differs")
        except Exception as exc:
            errors.append(f"{segment_id}: slice check failed: {exc}")
        check(segment.get("unit_id") == UNIT_ID and segment.get("order") == order, f"{segment_id}: unit/order differs")
        check(segment.get("source_anchor") == source_anchor and segment.get("target_anchor") == target_anchor, f"{segment_id}: anchor mapping differs")
        check((segment.get("source_page_text_bytes"), segment.get("source_page_text_sha256")) == SOURCE_TEXT_FINGERPRINTS[page], f"{segment_id}: source text fingerprint differs")
        check((segment.get("source_page_render_bytes"), segment.get("source_page_render_sha256")) == SOURCE_RENDER_FINGERPRINTS[page], f"{segment_id}: source render fingerprint differs")
        check((segment.get("source_item_count"), segment.get("nested_source_item_count"), segment.get("source_display_count"), segment.get("source_figure_count"), segment.get("source_figure_panel_count")) == (PAGE_ITEMS[page], PAGE_NESTED[page], PAGE_DISPLAYS[page], 1 if page in FIGURE_PANELS else 0, FIGURE_PANELS.get(page, 0)), f"{segment_id}: page topology differs")
        for index in range(1, PAGE_DISPLAYS[page] + 1):
            formula_order += 1
            formula_id = f"surface.mit.l07.formula.p{page:03d}.d{index:03d}"
            surface = by_id.get(formula_id, {})
            s_anchor = f"src-mit-l07-p{page:03d}-d{index:03d}"
            t_anchor = f"d90-mit-l07-p{page:03d}-d{index:03d}"
            try:
                s_slice = fenced_div_slice(MIT_WITNESS, s_anchor)
                t_slice = fenced_div_slice(MIT_TARGET, t_anchor)
                check((surface.get("source_line_start"), surface.get("source_line_end"), surface.get("source_bytes"), surface.get("source_content_sha256")) == s_slice, f"{formula_id}: source slice differs")
                check((surface.get("target_line_start"), surface.get("target_line_end"), surface.get("target_bytes"), surface.get("target_content_sha256")) == t_slice, f"{formula_id}: target slice differs")
            except Exception as exc:
                errors.append(f"{formula_id}: slice check failed: {exc}")
            check((surface.get("unit_id"), surface.get("surface_type"), surface.get("presence")) == (UNIT_ID, "display_formula", "present"), f"{formula_id}: surface semantics differ")
            check((surface.get("formula_sequence_order"), surface.get("page_formula_order"), surface.get("formula_label")) == (formula_order, index, DISPLAY_LABELS[(page, index)]), f"{formula_id}: formula ordering/label differs")
            check(surface.get("related_segment_ids") == [segment_id] and surface.get("formula_sequence_match") is True, f"{formula_id}: segment/formula validation binding differs")
        if page in FIGURE_PANELS:
            figure_id = f"surface.mit.l07.figure-description.p{page:03d}.f001"
            surface = by_id.get(figure_id, {})
            s_anchor = f"src-mit-l07-p{page:03d}-f001"
            t_anchor = f"d90-mit-l07-p{page:03d}-f001"
            try:
                s_slice = fenced_div_slice(MIT_WITNESS, s_anchor)
                t_slice = fenced_div_slice(MIT_TARGET, t_anchor)
                check((surface.get("source_line_start"), surface.get("source_line_end"), surface.get("source_bytes"), surface.get("source_content_sha256")) == s_slice, f"{figure_id}: source slice differs")
                check((surface.get("target_line_start"), surface.get("target_line_end"), surface.get("target_bytes"), surface.get("target_content_sha256")) == t_slice, f"{figure_id}: target slice differs")
            except Exception as exc:
                errors.append(f"{figure_id}: slice check failed: {exc}")
            check((surface.get("surface_type"), surface.get("presence"), surface.get("panel_count")) == ("semantic_figure_description", "present_with_limitation", FIGURE_PANELS[page]), f"{figure_id}: figure semantics differ")
            check(surface.get("figure_label") == FIGURE_LABELS[page] and surface.get("copied_source_graphic_bytes") == 0 and surface.get("semantic_description_preserved") is True, f"{figure_id}: figure rights/description differs")
    check(formula_order == 13, "formula sequence count differs")

    try:
        events = ledger_events()
        correction_specs = {
            "O015-MIT-SEM-0007": ([30, 32, 34], "correction.o015-mit-sem-0007"),
            "O015-MIT-SEM-0008": ([33], "correction.o015-mit-sem-0008"),
        }
        for event_id, (pages, correction_id) in correction_specs.items():
            event, binding = events[event_id]
            correction = by_id.get(correction_id, {})
            check(correction.get("source_event_id") == event_id, f"{correction_id}: source event differs")
            check(correction.get("affected_unit_ids") == [UNIT_ID], f"{correction_id}: unit binding differs")
            check(correction.get("affected_segment_ids") == [f"d90.mit.ocw-6.253.l07.p{page:03d}" for page in pages], f"{correction_id}: segment binding differs")
            check(correction.get("source_pdf_pages") == pages, f"{correction_id}: page binding differs")
            check(correction.get("surface") == event["surface"] and correction.get("source_issue") == event["source_issue"] and correction.get("target_action") == event["target_action"], f"{correction_id}: correction content differs")
            check(correction.get("correction_class") == event["class"], f"{correction_id}: correction class differs")
            check(correction.get("evidence_artifact_id") == "artifact.mit.l07.correction-snapshot", f"{correction_id}: evidence artifact differs")
            for field, value in binding.items():
                check(correction.get(field) == value, f"{correction_id}: {field} differs")
    except Exception as exc:
        errors.append(f"correction evidence check failed: {exc}")

    try:
        check(file_info(MIT_PDF) == SOURCE_PDF_IDENTITY, "authority PDF identity differs")
    except Exception as exc:
        errors.append(f"authority PDF check failed: {exc}")
    for path, expected in FINAL_READER_IDENTITIES.items():
        try:
            check(file_info(path) == expected, f"final reader identity differs: {path}")
        except Exception as exc:
            errors.append(f"final reader identity check failed for {path}: {exc}")
    for artifact_id, (path, rights_id) in ARTIFACTS.items():
        artifact = by_id.get(artifact_id, {})
        check(artifact.get("entity_type") == "artifact", f"missing artifact {artifact_id}")
        try:
            check(file_info(path) == (artifact.get("bytes"), artifact.get("sha256")), f"{artifact_id}: stale artifact bytes")
        except Exception as exc:
            errors.append(f"{artifact_id}: artifact identity check failed: {exc}")
        check(artifact.get("path") == path and artifact.get("rights_id") == rights_id, f"{artifact_id}: path/rights binding differs")
    check(by_id.get("artifact.mit.l07.correction-snapshot", {}).get("event_bindings") == [events[event_id][1] for event_id in sorted(events)] if events else False, "correction snapshot artifact bindings differ")
    check(by_id.get("artifact.mit.l07.builder", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "builder artifact command differs")
    check(by_id.get("artifact.mit.l07.target-html", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "HTML artifact command differs")
    check(by_id.get("artifact.mit.l07.target-pdf", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "PDF artifact command differs")

    for rights_id in ("rights.o015-mit-semantic-witness", "rights.o015-mit-id-pilot", "rights.o015-mit-pilot-build-qa", "rights.o015-mit-l01-backend-tooling"):
        check(by_id.get(rights_id, {}).get("entity_type") == "rights", f"missing inherited rights record {rights_id}")
    check(by_id.get("qa.o015.mit-l07.rights", {}).get("license") == "CC BY-NC-SA 4.0", "L07 rights QA license differs")
    check(by_id.get("qa.o015.mit-l07.rights", {}).get("source_graphics_redistributed") == 0, "L07 rights QA claims source graphics")
    check(by_id.get("qa.o015.mit-l07.formulas", {}).get("display_formulas") == 13, "formula QA count differs")
    check(by_id.get("qa.o015.mit-l07.figures", {}).get("semantic_figure_descriptions") == 4, "figure QA count differs")
    check(by_id.get("qa.o015.mit-l07.corrections", {}).get("source_event_ids") == sorted(EXPECTED_EVENTS), "correction QA event set differs")
    check(by_id.get("qa.o015.mit-l07.semantic-rereview", {}).get("remaining_defects") == {"P1": 0, "P2": 0, "P3": 0}, "semantic rereview QA disposition differs")
    check(by_id.get("qa.o015.mit-l07.accessibility", {}).get("human_review_is_release_gate") is False, "accessibility QA encodes a human review gate")
    check(by_id.get("qa.o015.mit-l07.language", {}).get("human_review_is_release_gate") is False, "language QA encodes a human review gate")
    check(by_id.get("qa.o015.mit-l07.csv-losslessness", {}).get("row_order_matches_jsonl") is True, "CSV losslessness QA differs")
    check(by_id.get("qa.o015.mit-l07.backend-integration", {}).get("independent_validation_runs_required") == 2, "independent-validation contract differs")

    relations = [record for record in new_records if record.get("entity_type") == "relation"]
    triples = [(record.get("relation_type"), record.get("source_id"), record.get("target_id")) for record in relations]
    check(len(relations) == 40 and len(triples) == len(set(triples)), "L07 relation count or triple uniqueness differs")
    essential_relations = {
        "relation.mit.work-contains-l07": ("contains", "unit.mit.ocw-6.253.spring-2012", UNIT_ID),
        "relation.mit.l06-precedes-l07": ("precedes", "unit.mit.ocw-6.253.l06", UNIT_ID),
        "relation.mit.target-translates-witness-l07": ("translates", "artifact.mit.l07.target-source", "artifact.mit.l07.semantic-witness"),
        "relation.mit.html-adapts-target-l07": ("adapts", "artifact.mit.l07.target-html", "artifact.mit.l07.target-source"),
        "relation.mit.pdf-adapts-target-l07": ("adapts", "artifact.mit.l07.target-pdf", "artifact.mit.l07.target-source"),
        "relation.mit.rereview-depends-on-target-l07": ("depends-on", "artifact.mit.l07.independent-rereview", "artifact.mit.l07.target-source"),
    }
    for relation_id, expected in essential_relations.items():
        relation = by_id.get(relation_id, {})
        check((relation.get("relation_type"), relation.get("source_id"), relation.get("target_id")) == expected, f"{relation_id}: relation triple differs")

    try:
        content = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
        browser = json.loads((ROOT / MIT_BROWSER).read_text(encoding="utf-8"))
        visual = json.loads((ROOT / MIT_VISUAL).read_text(encoding="utf-8"))
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
        check(content.get("result") == "pass" and content.get("errors") == [], "MIT L07 content validation is not passing")
        check(content.get("boundary") == expected_boundary, "MIT L07 content boundary differs")
        check(content.get("formula_sequence_match") is True, "MIT L07 formula sequence differs")
        check(content.get("source_page_text_sha256") == {str(page): identity[1] for page, identity in SOURCE_TEXT_FINGERPRINTS.items()}, "MIT L07 source-page hashes differ")
        pair = [file_info(MIT_HTML)[1], file_info(MIT_READER_PDF)[1]]
        build = content.get("build", {})
        check(build.get("command") == RECEIPT_BUILD_COMMAND and build.get("deterministic_rebuilds") == 2 and build.get("rebuild_hashes") == [pair, pair], "MIT L07 deterministic build evidence differs")
        check(content.get("html", {}).get("source_pages") == 10 and content.get("html", {}).get("source_displays") == 13 and content.get("html", {}).get("source_figures") == 4, "MIT L07 HTML topology differs")
        check(content.get("pdf", {}).get("pages") == 4 and content.get("pdf", {}).get("tagged") is False and content.get("pdf", {}).get("images") == 0, "MIT L07 PDF topology differs")
        check(browser.get("result") == "pass" and (browser.get("surface", {}).get("bytes"), browser.get("surface", {}).get("sha256")) == file_info(MIT_HTML), "MIT L07 browser QA evidence differs")
        check(visual.get("result") == "pass" and (visual.get("surface", {}).get("bytes"), visual.get("surface", {}).get("sha256")) == file_info(MIT_READER_PDF), "MIT L07 visual QA evidence differs")
        check(content.get("pdf", {}).get("render_sha256") == [item["sha256"] for item in visual.get("render", {}).get("files", [])], "MIT L07 render hash sequence differs")
        for item in content.get("files", {}).values():
            path = item.get("path")
            if path:
                check(file_info(path) == (item.get("bytes"), item.get("sha256")), f"MIT L07 content receipt binds stale file {path}")
        rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
        for path in (MIT_TARGET, MIT_HTML, MIT_READER_PDF):
            check(file_info(path)[1] in rereview, f"MIT L07 independent rereview does not bind {path}")
        check("P1=0, P2=0, P3=0" in rereview, "MIT L07 independent rereview severity differs")
    except Exception as exc:
        errors.append(f"content QA receipt check failed: {exc}")

    canonical_paths = {
        "authority_pdf": MIT_PDF,
        "boundary_census": MIT_CENSUS,
        "witness": MIT_WITNESS,
        "target": MIT_TARGET,
        "html": MIT_HTML,
        "pdf": MIT_READER_PDF,
        "builder": MIT_BUILDER,
        "content_validator": MIT_VALIDATOR,
        "content_validation": MIT_REPORT,
        "browser_qa": MIT_BROWSER,
        "visual_qa": MIT_VISUAL,
        "independent_rereview": MIT_REREVIEW,
        "correction_snapshot": MIT_LEDGER,
        "backend_generator": MIT_BACKEND_GENERATOR,
        "backend_validator": MIT_BACKEND_VALIDATOR,
    }
    identities: dict[str, Any] = {}
    for name, path in canonical_paths.items():
        try:
            size, file_hash = file_info(path)
            identities[name] = {"path": path, "bytes": size, "sha256": file_hash}
        except Exception as exc:
            identities[name] = {"path": path, "error": str(exc)}

    new_counts = dict(sorted(Counter(record.get("entity_type") for record in new_records).items()))
    stripped_jsonl = strip_workflow_jsonl(raw_jsonl) if raw_jsonl else b""
    stripped_csv = strip_workflow_csv(raw_csv) if raw_csv else b""
    receipt = {
        "schema": "o015-mit-l07-backend-validation-v1",
        "recorded_at": RECORDED_AT,
        "workflow": WORKFLOW,
        "result": "pass" if not errors else "fail",
        "protected_baseline": {
            "record_count": BASELINE_COUNT,
            "jsonl": {"bytes": len(stripped_jsonl), "sha256": digest(stripped_jsonl) if stripped_jsonl else None, "expected": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]}},
            "csv": {"bytes": len(stripped_csv), "sha256": digest(stripped_csv) if stripped_csv else None, "expected": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]}},
            "id_set_sha256": id_set(baseline_records) if baseline_records else None,
            "record_set_sha256": record_set(baseline_records) if baseline_records else None,
            "preserved_record_count": len(baseline_records),
            "raw_bytes_reconstructed_exactly": (len(stripped_jsonl), digest(stripped_jsonl) if stripped_jsonl else None) == BASELINE_JSONL and (len(stripped_csv), digest(stripped_csv) if stripped_csv else None) == BASELINE_CSV,
        },
        "admission": {
            "unit_id": UNIT_ID,
            "segment_ids": [f"d90.mit.ocw-6.253.l07.p{page:03d}" for page in SOURCE_PAGES],
            "formula_surface_ids": [f"surface.mit.l07.formula.p{page:03d}.d{index:03d}" for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)],
            "figure_description_surface_ids": [f"surface.mit.l07.figure-description.p{page:03d}.f001" for page in FIGURE_PANELS],
            "correction_ids": ["correction.o015-mit-sem-0007", "correction.o015-mit-sem-0008"],
            "top_level_items": 16,
            "nested_items": 14,
            "display_formulas": 13,
            "figure_descriptions": 4,
            "figure_panels": 6,
            "copied_source_graphics": 0,
            "canonical_build_command": CANONICAL_BUILD_COMMAND,
            "new_record_count": len(new_records),
            "new_entity_counts": new_counts,
            "new_id_set_sha256": digest(("\n".join(sorted(record["id"] for record in new_records)) + "\n").encode("utf-8")) if new_records else None,
        },
        "final_backend": {
            "record_count": len(records),
            "jsonl": {"bytes": len(raw_jsonl), "sha256": digest(raw_jsonl) if raw_jsonl else None},
            "csv": {"bytes": len(raw_csv), "sha256": digest(raw_csv) if raw_csv else None},
            "id_set_sha256": id_set(records) if records else None,
            "record_set_sha256": record_set(records) if records else None,
            "csv_projection_lossless": bool(rows and len(rows) == len(records) and [json.loads(row["record_json"]) for row in rows] == records),
        },
        "correction_snapshot": {
            "path": MIT_LEDGER,
            "bytes": LEDGER_IDENTITY[0],
            "sha256": LEDGER_IDENTITY[1],
            "event_bindings": {event_id: binding for event_id, (_, binding) in sorted(events.items())},
        },
        "canonical_artifacts": identities,
        "independent_validation_runs_required": 2,
        "errors": errors,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
