#!/usr/bin/env python3
"""Independent fail-closed validation for the MIT L06 backend admission."""

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
REPORT_PATH = ROOT / "qa/MIT_L06_BACKEND_VALIDATION.json"

RECORDED_AT = "2026-08-23T23:00:00Z"
WORKFLOW = "o015-mit-l06-backend-v1"
BASELINE_COUNT = 1605
BASELINE_JSONL = (1_142_443, "30c6f3257d481136995acd7947a725da003c4ab2ea2e9049de53a23fa681658b")
BASELINE_CSV = (1_373_874, "f66227edc14e953b44d833b87b0373f76d87bf04fdd32d2f50552597915746e3")
BASELINE_ID_SET = "174b5f03bf72f9cbab07f05950c56021a96917b143e8680c05050bb0dfe9d6e1"
BASELINE_RECORD_SET = "afbc446ca325c5aabe8549b5e0cd5fed2b1865c9433a406cb499ab12145d097f"

UNIT_ID = "unit.mit.ocw-6.253.l06"
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
MIT_BROWSER = "qa/MIT_L06_BROWSER_QA.json"
MIT_VISUAL = "qa/MIT_L06_VISUAL_QA.json"
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
    MIT_BROWSER: (1_584, "b98ac5b2ea7df5b5d7b1263595b777269db1acc9c996fe7135a338366fb2d64d"),
    MIT_VISUAL: (2_342, "9643896538a3704626d100c3775e3329bf082feda0e981977593f7ff6d25c680"),
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

DISPLAY_PAIRS = [
    (page, index)
    for page in SOURCE_PAGES for index in range(1, PAGE_DISPLAYS[page] + 1)
]
SEGMENT_IDS = {f"d90.mit.ocw-6.253.l06.p{page:03d}" for page in SOURCE_PAGES}
FORMULA_IDS = {
    f"surface.mit.l06.formula.p{page:03d}.d{index:03d}" for page, index in DISPLAY_PAIRS
}
FIGURE_IDS = {
    f"surface.mit.l06.figure-description.p{page:03d}.f001" for page in FIGURE_PANELS
}
CORRECTION_IDS = {"correction.o015-mit-sem-0005", "correction.o015-mit-sem-0006"}

ARTIFACTS: dict[str, tuple[str, str]] = {
    "artifact.mit.l06.boundary-census": (MIT_CENSUS, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l06.semantic-witness": (MIT_WITNESS, "rights.o015-mit-semantic-witness"),
    "artifact.mit.l06.target-source": (MIT_TARGET, "rights.o015-mit-id-pilot"),
    "artifact.mit.l06.target-html": (MIT_HTML, "rights.o015-mit-id-pilot"),
    "artifact.mit.l06.target-pdf": (MIT_READER_PDF, "rights.o015-mit-id-pilot"),
    "artifact.mit.l06.builder": (MIT_BUILDER, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l06.validator": (MIT_VALIDATOR, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l06.validation": (MIT_REPORT, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l06.browser-qa": (MIT_BROWSER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l06.visual-qa": (MIT_VISUAL, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l06.independent-rereview": (MIT_REREVIEW, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l06.adverse-ledger": (MIT_LEDGER, "rights.o015-mit-pilot-build-qa"),
    "artifact.mit.l06.css": (MIT_CSS, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l06.pdf-preamble": (MIT_PREAMBLE, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l06.pdf-filter": (MIT_FILTER, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l06.before-body": (MIT_BEFORE_BODY, "rights.o015-mit-l01-backend-tooling"),
    "artifact.mit.l06.after-body": (MIT_AFTER_BODY, "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-generator-mit-l06": ("qa/extend_backend_mit_l06.py", "rights.o015-mit-l01-backend-tooling"),
    "artifact.o015.backend-validator-mit-l06": ("qa/validate_backend_mit_l06.py", "rights.o015-mit-l01-backend-tooling"),
}

QA_IDS = {
    f"qa.o015.mit-l06.{name}"
    for name in (
        "source-freeze",
        "semantic-reconstruction",
        "topology",
        "formulas",
        "figures",
        "corrections",
        "build",
        "html",
        "browser",
        "pdf",
        "visual",
        "accessibility",
        "semantic-rereview",
        "language",
        "rights",
        "csv-losslessness",
        "backend-integration",
    )
}

BASE_RELATIONS: dict[str, tuple[str, str, str]] = {
    "relation.mit.work-contains-l06": ("contains", "unit.mit.ocw-6.253.spring-2012", UNIT_ID),
    "relation.mit.witness-edition-contains-l06": ("contains", "edition.mit.ocw-6.253.spring-2012.semantic-witness-en", UNIT_ID),
    "relation.mit.target-edition-contains-l06": ("contains", "edition.mit.ocw-6.253.id-id.pilot-v1", UNIT_ID),
    "relation.mit.witness-adapts-authority-pdf-l06": ("adapts", "artifact.mit.l06.semantic-witness", "artifact.mit.complete-notes-pdf"),
    "relation.mit.target-translates-witness-l06": ("translates", "artifact.mit.l06.target-source", "artifact.mit.l06.semantic-witness"),
    "relation.mit.html-adapts-target-l06": ("adapts", "artifact.mit.l06.target-html", "artifact.mit.l06.target-source"),
    "relation.mit.pdf-adapts-target-l06": ("adapts", "artifact.mit.l06.target-pdf", "artifact.mit.l06.target-source"),
    "relation.mit.browser-qa-depends-on-html-l06": ("depends-on", "artifact.mit.l06.browser-qa", "artifact.mit.l06.target-html"),
    "relation.mit.visual-qa-depends-on-pdf-l06": ("depends-on", "artifact.mit.l06.visual-qa", "artifact.mit.l06.target-pdf"),
    "relation.mit.validation-depends-on-browser-qa-l06": ("depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.browser-qa"),
    "relation.mit.validation-depends-on-visual-qa-l06": ("depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.visual-qa"),
    "relation.mit.validation-depends-on-rereview-l06": ("depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.independent-rereview"),
    "relation.mit.validation-depends-on-boundary-l06": ("depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.boundary-census"),
    "relation.mit.validation-depends-on-ledger-l06": ("depends-on", "artifact.mit.l06.validation", "artifact.mit.l06.adverse-ledger"),
    "relation.mit.backend-generator-depends-on-validation-l06": ("depends-on", "artifact.o015.backend-generator-mit-l06", "artifact.mit.l06.validation"),
    "relation.mit.backend-validator-depends-on-generator-l06": ("depends-on", "artifact.o015.backend-validator-mit-l06", "artifact.o015.backend-generator-mit-l06"),
}
EXPECTED_RELATIONS = dict(BASE_RELATIONS)
for _page in SOURCE_PAGES:
    EXPECTED_RELATIONS[f"relation.mit.l06.contains-p{_page:03d}"] = (
        "contains", UNIT_ID, f"d90.mit.ocw-6.253.l06.p{_page:03d}"
    )
for _page, _index in DISPLAY_PAIRS:
    EXPECTED_RELATIONS[f"relation.mit.l06.formula-p{_page:03d}-d{_index:03d}-depends-on-p{_page:03d}"] = (
        "depends-on",
        f"surface.mit.l06.formula.p{_page:03d}.d{_index:03d}",
        f"d90.mit.ocw-6.253.l06.p{_page:03d}",
    )
for _page in FIGURE_PANELS:
    EXPECTED_RELATIONS[f"relation.mit.l06.figure-description-p{_page:03d}-f001-illustrates-p{_page:03d}"] = (
        "illustrates",
        f"surface.mit.l06.figure-description.p{_page:03d}.f001",
        f"d90.mit.ocw-6.253.l06.p{_page:03d}",
    )
for _suffix in ("0005", "0006"):
    EXPECTED_RELATIONS[f"relation.mit.l06.correction-{_suffix}-depends-on-ledger"] = (
        "depends-on", f"correction.o015-mit-sem-{_suffix}", "artifact.mit.l06.adverse-ledger"
    )

EXPECTED_NEW_IDS = (
    {UNIT_ID}
    | SEGMENT_IDS
    | FORMULA_IDS
    | FIGURE_IDS
    | CORRECTION_IDS
    | set(ARTIFACTS)
    | QA_IDS
    | set(EXPECTED_RELATIONS)
)
EXPECTED_NEW_ENTITY_COUNTS = {
    "artifact": 19,
    "correction": 2,
    "learning_surface": 17,
    "qa_event": 17,
    "relation": 44,
    "segment": 9,
    "unit": 1,
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
    payload = "".join(canonical(record) + "\n" for record in sorted(records, key=lambda item: item["id"]))
    return digest(payload.encode("utf-8"))


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.strip().startswith("::: {") and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
    ]
    if len(starts) != 1:
        raise ValueError(f"{relative} #{anchor}: expected one fenced div, found {len(starts)}")
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
        raise ValueError(f"{relative} #{anchor}: unclosed fenced div")
    payload = ("\n".join(lines[start : end + 1]) + "\n").encode("utf-8")
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


def semantic_anchor_inventory(relative: str, prefix: str) -> list[str]:
    text = (ROOT / relative).read_text(encoding="utf-8")
    pattern = rf"#({re.escape(prefix)}-p\d{{3}}(?:-[idf]\d{{3}})?)(?:\s|\}})"
    return re.findall(pattern, text)


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
            matches[event_id].append((event, {
                "ledger_path": MIT_LEDGER,
                "raw_line_start": line_number,
                "raw_line_end": line_number,
                "raw_line_bytes": len(raw_line),
                "raw_line_sha256": digest(raw_line),
                "raw_line_newline": newline,
                "canonical_event_sha256": digest(canonical(event).encode("utf-8")),
            }))
    result: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for event_id, found in matches.items():
        if len(found) != 1:
            raise ValueError(f"expected one {event_id} event, found {len(found)}")
        event, binding = found[0]
        if event != EXPECTED_LEDGER_EVENTS[event_id]:
            raise ValueError(f"{event_id} differs from exact expected event")
        result[event_id] = (event, binding)
    return result


def main() -> int:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        raw_jsonl = JSONL_PATH.read_bytes()
        raw_csv = CSV_PATH.read_bytes()
        records = [json.loads(line) for line in raw_jsonl.decode("utf-8").splitlines() if line]
    except Exception as exc:
        errors.append(f"backend load failed: {exc}")
        schema, raw_jsonl, raw_csv, records = {}, b"", b"", []

    ids = [record.get("id") for record in records]
    by_id = {record.get("id"): record for record in records}
    new_records = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    baseline_records = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    check(schema.get("schema") == "o015-modular-backend-schema", "backend schema identity differs")
    check(len(EXPECTED_NEW_IDS) == 109, "validator expected-ID declaration is not 109 records")
    check(len(records) == BASELINE_COUNT + len(EXPECTED_NEW_IDS), f"record count {len(records)} differs")
    check(len(ids) == len(set(ids)), "duplicate backend IDs")
    check(len(new_records) == len(EXPECTED_NEW_IDS), "L06 new-record count differs")
    check({record["id"] for record in new_records} == EXPECTED_NEW_IDS, "L06 stable-ID set differs")
    check(
        dict(sorted(Counter(record.get("entity_type") for record in new_records).items())) == EXPECTED_NEW_ENTITY_COUNTS,
        "L06 new-entity counts differ",
    )
    check(len(baseline_records) == BASELINE_COUNT, "protected baseline record count differs")
    check(id_set(baseline_records) == BASELINE_ID_SET, "protected baseline ID-set hash differs")
    check(record_set(baseline_records) == BASELINE_RECORD_SET, "protected baseline record-set hash differs")

    stripped_jsonl = b""
    stripped_csv = b""
    try:
        stripped_jsonl = strip_workflow_jsonl(raw_jsonl)
        stripped_csv = strip_workflow_csv(raw_csv)
        check((len(stripped_jsonl), digest(stripped_jsonl)) == BASELINE_JSONL, "raw JSONL baseline reconstruction differs")
        check((len(stripped_csv), digest(stripped_csv)) == BASELINE_CSV, "raw CSV baseline reconstruction differs")
    except Exception as exc:
        errors.append(f"raw baseline reconstruction failed: {exc}")

    rank = {name: index for index, name in enumerate(schema.get("entity_order", []))}
    check(
        records == sorted(records, key=lambda record: (rank.get(record.get("entity_type"), 999), record.get("id", ""))),
        "JSONL order is not deterministic",
    )
    try:
        rows = list(csv.DictReader(io.StringIO(raw_csv.decode("utf-8", errors="strict"))))
        check(list(rows[0]) == schema.get("csv_columns"), "CSV header differs from schema")
        check([json.loads(row["record_json"]) for row in rows] == records, "CSV projection does not round-trip losslessly")
    except Exception as exc:
        errors.append(f"CSV parse failed: {exc}")

    refs = set(schema.get("reference_fields", []))
    for record in records:
        entity_type = record.get("entity_type")
        for field in schema.get("required_common", []) + schema.get("required_by_entity", {}).get(entity_type, []):
            check(field in record, f"{record.get('id')}: missing required {field}")
        for field in refs:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for target in values:
                if isinstance(target, str):
                    check(target in by_id, f"{record.get('id')}: unresolved {field} -> {target}")

    expected_source_items = [
        f"src-mit-l06-p{page:03d}-i{index:03d}"
        for page in SOURCE_PAGES for index in range(1, PAGE_ITEMS[page] + 1)
    ]
    expected_target_items = [item.replace("src-mit-", "d90-mit-", 1) for item in expected_source_items]
    expected_source_displays = [f"src-mit-l06-p{page:03d}-d{index:03d}" for page, index in DISPLAY_PAIRS]
    expected_target_displays = [item.replace("src-mit-", "d90-mit-", 1) for item in expected_source_displays]
    expected_source_figures = [f"src-mit-l06-p{page:03d}-f001" for page in FIGURE_PANELS]
    expected_target_figures = [item.replace("src-mit-", "d90-mit-", 1) for item in expected_source_figures]
    expected_source_anchors = (
        [f"src-mit-l06-p{page:03d}" for page in SOURCE_PAGES]
        + expected_source_items + expected_source_displays + expected_source_figures
    )
    expected_target_anchors = (
        [f"d90-mit-l06-p{page:03d}" for page in SOURCE_PAGES]
        + expected_target_items + expected_target_displays + expected_target_figures
    )
    try:
        source_inventory = semantic_anchor_inventory(MIT_WITNESS, "src-mit-l06")
        target_inventory = semantic_anchor_inventory(MIT_TARGET, "d90-mit-l06")
        check(set(source_inventory) == set(expected_source_anchors), "English witness semantic-anchor set differs")
        check(set(target_inventory) == set(expected_target_anchors), "Indonesian target semantic-anchor set differs")
        check(len(source_inventory) == len(set(source_inventory)) == 58, "English witness semantic anchors are not 58 unique IDs")
        check(len(target_inventory) == len(set(target_inventory)) == 58, "Indonesian target semantic anchors are not 58 unique IDs")
    except Exception as exc:
        errors.append(f"semantic-anchor inventory failed: {exc}")

    unit = by_id.get(UNIT_ID, {})
    check(unit.get("order") == 6 and unit.get("source_pdf_pages") == SOURCE_PAGES, "L06 unit order/page boundary differs")
    check(unit.get("parent_id") == "unit.mit.ocw-6.253.spring-2012", "L06 parent differs")
    check(unit.get("next_source_page") == 29 and unit.get("next_source_heading") == "LECTURE 3 - LECTURE OUTLINE", "L06 next cursor differs")
    check(unit.get("source_item_count") == 32 and unit.get("nested_source_item_count") == 17, "L06 item topology differs")
    check(unit.get("source_item_ids") == expected_source_items and unit.get("target_item_ids") == expected_target_items, "L06 item IDs differ")
    check(unit.get("source_display_ids") == expected_source_displays and unit.get("target_display_ids") == expected_target_displays, "L06 display IDs differ")
    check(unit.get("source_figure_ids") == expected_source_figures and unit.get("target_figure_ids") == expected_target_figures, "L06 figure IDs differ")
    check(unit.get("source_display_count") == 12 and unit.get("source_figure_count") == 5 and unit.get("source_figure_panel_count") == 10, "L06 display/figure topology differs")
    check(unit.get("copied_source_graphics") == 0, "L06 unit claims copied source graphics")
    check(unit.get("correction_event_ids") == sorted(EXPECTED_LEDGER_EVENTS), "L06 correction summary differs")
    check(unit.get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "L06 unit build command differs")

    for order, page in enumerate(SOURCE_PAGES, start=1):
        segment_id = f"d90.mit.ocw-6.253.l06.p{page:03d}"
        segment = by_id.get(segment_id, {})
        source_anchor = f"src-mit-l06-p{page:03d}"
        target_anchor = f"d90-mit-l06-p{page:03d}"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
            target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
            check((segment.get("source_line_start"), segment.get("source_line_end"), segment.get("source_bytes"), segment.get("source_content_sha256")) == source_slice, f"{segment_id}: source page-slice binding differs")
            check((segment.get("target_line_start"), segment.get("target_line_end"), segment.get("target_bytes"), segment.get("target_content_sha256")) == target_slice, f"{segment_id}: target page-slice binding differs")
        except Exception as exc:
            errors.append(f"{segment_id}: page-slice check failed: {exc}")
        check(segment.get("unit_id") == UNIT_ID and segment.get("order") == order, f"{segment_id}: order/unit differs")
        check(segment.get("source_pdf_page") == page and segment.get("source_pdf_sha256") == SOURCE_PDF_IDENTITY[1], f"{segment_id}: authority binding differs")
        check((segment.get("source_page_text_bytes"), segment.get("source_page_text_sha256")) == SOURCE_TEXT_FINGERPRINTS[page], f"{segment_id}: source text fingerprint differs")
        check((segment.get("source_page_render_bytes"), segment.get("source_page_render_sha256")) == SOURCE_RENDER_FINGERPRINTS[page], f"{segment_id}: source render fingerprint differs")
        check(segment.get("source_item_count") == PAGE_ITEMS[page] and segment.get("nested_source_item_count") == PAGE_NESTED[page], f"{segment_id}: item counts differ")
        check(segment.get("source_display_count") == PAGE_DISPLAYS[page], f"{segment_id}: display count differs")
        check(segment.get("source_figure_count") == (1 if page in FIGURE_PANELS else 0), f"{segment_id}: figure count differs")
        check(segment.get("source_figure_panel_count") == FIGURE_PANELS.get(page, 0), f"{segment_id}: figure-panel count differs")

    for global_order, (page, index) in enumerate(DISPLAY_PAIRS, start=1):
        surface_id = f"surface.mit.l06.formula.p{page:03d}.d{index:03d}"
        surface = by_id.get(surface_id, {})
        source_anchor = f"src-mit-l06-p{page:03d}-d{index:03d}"
        target_anchor = f"d90-mit-l06-p{page:03d}-d{index:03d}"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
            target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
            check((surface.get("source_line_start"), surface.get("source_line_end"), surface.get("source_bytes"), surface.get("source_content_sha256")) == source_slice, f"{surface_id}: source formula-slice binding differs")
            check((surface.get("target_line_start"), surface.get("target_line_end"), surface.get("target_bytes"), surface.get("target_content_sha256")) == target_slice, f"{surface_id}: target formula-slice binding differs")
        except Exception as exc:
            errors.append(f"{surface_id}: formula-slice check failed: {exc}")
        check(surface.get("surface_type") == "display_formula" and surface.get("presence") == "present", f"{surface_id}: surface semantics differ")
        check(surface.get("unit_id") == UNIT_ID and surface.get("related_segment_ids") == [f"d90.mit.ocw-6.253.l06.p{page:03d}"], f"{surface_id}: unit/segment binding differs")
        check(surface.get("formula_sequence_order") == global_order and surface.get("page_formula_order") == index, f"{surface_id}: formula order differs")
        check(surface.get("formula_label") == DISPLAY_LABELS[(page, index)] and surface.get("formula_sequence_match") is True, f"{surface_id}: formula label/sequence result differs")
        expected_literal = {"source": "or", "target": "atau"} if (page, index) == (26, 2) else None
        check(surface.get("literal_language_normalization") == expected_literal, f"{surface_id}: literal normalization differs")

    for page, panel_count in FIGURE_PANELS.items():
        surface_id = f"surface.mit.l06.figure-description.p{page:03d}.f001"
        surface = by_id.get(surface_id, {})
        source_anchor = f"src-mit-l06-p{page:03d}-f001"
        target_anchor = f"d90-mit-l06-p{page:03d}-f001"
        try:
            source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
            target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
            check((surface.get("source_line_start"), surface.get("source_line_end"), surface.get("source_bytes"), surface.get("source_content_sha256")) == source_slice, f"{surface_id}: source figure-description binding differs")
            check((surface.get("target_line_start"), surface.get("target_line_end"), surface.get("target_bytes"), surface.get("target_content_sha256")) == target_slice, f"{surface_id}: target figure-description binding differs")
        except Exception as exc:
            errors.append(f"{surface_id}: figure-description check failed: {exc}")
        check(surface.get("surface_type") == "semantic_figure_description" and surface.get("presence") == "present_with_limitation", f"{surface_id}: surface semantics differ")
        check(surface.get("figure_label") == FIGURE_LABELS[page] and surface.get("panel_count") == panel_count, f"{surface_id}: figure label/panel count differs")
        check(surface.get("source_graphic_disposition") == "omitted-source-graphic" and surface.get("copied_source_graphic_bytes") == 0, f"{surface_id}: omitted-graphic disposition differs")

    event_bindings: dict[str, Any] = {}
    try:
        events = ledger_events()
        event_bindings = {event_id: binding for event_id, (_, binding) in events.items()}
        correction_pages = {"O015-MIT-SEM-0005": [23, 24, 25, 26, 28], "O015-MIT-SEM-0006": [23]}
        for event_id, pages in correction_pages.items():
            suffix = event_id.rsplit("-", 1)[-1].lower()
            correction_id = f"correction.o015-mit-sem-{suffix}"
            correction = by_id.get(correction_id, {})
            event, binding = events[event_id]
            check(correction.get("source_event_id") == event_id, f"{correction_id}: event ID differs")
            check(correction.get("affected_unit_ids") == [UNIT_ID], f"{correction_id}: unit binding differs")
            check(correction.get("affected_segment_ids") == [f"d90.mit.ocw-6.253.l06.p{page:03d}" for page in pages], f"{correction_id}: segment binding differs")
            check(correction.get("source_pdf_pages") == pages, f"{correction_id}: source pages differ")
            check(correction.get("surface") == event["surface"] and correction.get("source_issue") == event["source_issue"] and correction.get("target_action") == event["target_action"], f"{correction_id}: event content differs")
            check(correction.get("correction_class") == event["class"], f"{correction_id}: correction class differs")
            check(correction.get("evidence_artifact_id") == "artifact.mit.l06.adverse-ledger", f"{correction_id}: ledger evidence differs")
            for field, expected in binding.items():
                check(correction.get(field) == expected, f"{correction_id}: {field} differs")
    except Exception as exc:
        errors.append(f"correction evidence check failed: {exc}")

    try:
        check(file_info(MIT_PDF) == SOURCE_PDF_IDENTITY, "authority PDF identity differs")
    except Exception as exc:
        errors.append(f"authority PDF check failed: {exc}")
    for path, expected_identity in FINAL_READER_IDENTITIES.items():
        try:
            check(file_info(path) == expected_identity, f"final reader identity differs: {path}")
        except Exception as exc:
            errors.append(f"final reader identity check failed for {path}: {exc}")
    for artifact_id, (path, rights_id) in ARTIFACTS.items():
        artifact = by_id.get(artifact_id)
        check(artifact is not None, f"missing artifact {artifact_id}")
        if artifact is None:
            continue
        try:
            check(file_info(path) == (artifact.get("bytes"), artifact.get("sha256")), f"{artifact_id}: stale artifact bytes")
        except Exception as exc:
            errors.append(f"{artifact_id}: artifact check failed: {exc}")
        check(artifact.get("path") == path, f"{artifact_id}: path differs")
        check(artifact.get("rights_id") == rights_id, f"{artifact_id}: rights binding differs")
    check(by_id.get("artifact.mit.l06.builder", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "builder artifact command differs")
    check(by_id.get("artifact.mit.l06.target-html", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "HTML artifact command differs")
    check(by_id.get("artifact.mit.l06.target-pdf", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "PDF artifact command differs")
    check(by_id.get("artifact.mit.l06.adverse-ledger", {}).get("event_bindings") == [event_bindings[event_id] for event_id in sorted(event_bindings)], "ledger artifact event bindings differ")

    for rights_id in (
        "rights.o015-mit-semantic-witness",
        "rights.o015-mit-id-pilot",
        "rights.o015-mit-pilot-build-qa",
        "rights.o015-mit-l01-backend-tooling",
    ):
        check(by_id.get(rights_id, {}).get("entity_type") == "rights", f"missing rights record {rights_id}")
    check(by_id.get("qa.o015.mit-l06.rights", {}).get("license") == "CC BY-NC-SA 4.0", "L06 rights QA license differs")
    check(by_id.get("qa.o015.mit-l06.rights", {}).get("source_graphics_redistributed") == 0, "L06 rights QA claims source graphics")
    check(by_id.get("qa.o015.mit-l06.formulas", {}).get("display_formulas") == 12, "formula QA count differs")
    check(by_id.get("qa.o015.mit-l06.figures", {}).get("semantic_figure_descriptions") == 5, "figure QA count differs")
    check(by_id.get("qa.o015.mit-l06.corrections", {}).get("source_event_ids") == sorted(EXPECTED_LEDGER_EVENTS), "correction QA event set differs")
    check(by_id.get("qa.o015.mit-l06.build", {}).get("canonical_build_command") == CANONICAL_BUILD_COMMAND, "build QA command differs")
    check(by_id.get("qa.o015.mit-l06.csv-losslessness", {}).get("row_order_matches_jsonl") is True, "CSV QA result differs")
    check(by_id.get("qa.o015.mit-l06.backend-integration", {}).get("independent_validation_runs_required") == 2, "independent-validation contract differs")

    new_relations = [record for record in new_records if record.get("entity_type") == "relation"]
    triples = [(record.get("relation_type"), record.get("source_id"), record.get("target_id")) for record in new_relations]
    check(len(triples) == len(set(triples)), "duplicate L06 relation triple")
    for relation_id, expected in EXPECTED_RELATIONS.items():
        relation = by_id.get(relation_id, {})
        check((relation.get("relation_type"), relation.get("source_id"), relation.get("target_id")) == expected, f"{relation_id}: relation triple differs")

    try:
        content = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
        browser = json.loads((ROOT / MIT_BROWSER).read_text(encoding="utf-8"))
        visual = json.loads((ROOT / MIT_VISUAL).read_text(encoding="utf-8"))
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
        check(content.get("result") == "pass" and content.get("errors") == [], "MIT L06 content validation is not passing")
        check(content.get("boundary") == expected_boundary, "MIT L06 content boundary differs")
        check(content.get("formula_sequence_match") is True, "MIT L06 formula sequence differs")
        check(content.get("source_page_text_sha256") == {str(page): value[1] for page, value in SOURCE_TEXT_FINGERPRINTS.items()}, "MIT L06 source-page hashes differ")
        build = content.get("build", {})
        expected_build_pair = [file_info(MIT_HTML)[1], file_info(MIT_READER_PDF)[1]]
        check(build.get("command") == RECEIPT_BUILD_COMMAND, "content receipt build command differs")
        check(build.get("deterministic_rebuilds") == 2 and build.get("rebuild_hashes") == [expected_build_pair, expected_build_pair], "deterministic build evidence differs")
        check(content.get("html", {}).get("source_pages") == 9 and content.get("html", {}).get("source_displays") == 12 and content.get("html", {}).get("source_figures") == 5, "L06 HTML topology differs")
        check(content.get("pdf", {}).get("pages") == 4 and content.get("pdf", {}).get("tagged") is False and content.get("pdf", {}).get("images") == 0, "L06 PDF topology differs")
        check(browser.get("result") == "pass" and (browser.get("html", {}).get("bytes"), browser.get("html", {}).get("sha256")) == file_info(MIT_HTML), "browser QA evidence differs")
        check(visual.get("result") == "pass" and (visual.get("surface", {}).get("bytes"), visual.get("surface", {}).get("sha256")) == file_info(MIT_READER_PDF), "visual QA evidence differs")
        check(content.get("pdf", {}).get("render_sha256") == [item["sha256"] for item in visual.get("render", {}).get("files", [])], "render-hash sequence differs")
        for item in content.get("files", {}).values():
            path = item.get("path")
            if path:
                check(file_info(path) == (item.get("bytes"), item.get("sha256")), f"content receipt binds stale file {path}")
        rereview = (ROOT / MIT_REREVIEW).read_text(encoding="utf-8")
        for path in (MIT_TARGET, MIT_HTML, MIT_READER_PDF):
            check(file_info(path)[1] in rereview, f"independent rereview does not bind {path}")
        check("P1=0, P2=0, P3=0" in rereview, "independent rereview severity differs")
    except Exception as exc:
        errors.append(f"QA receipt load failed: {exc}")

    canonical_paths = {
        "authority_pdf": MIT_PDF,
        "boundary_census": MIT_CENSUS,
        "witness": MIT_WITNESS,
        "target": MIT_TARGET,
        "html": MIT_HTML,
        "pdf": MIT_READER_PDF,
        "css": MIT_CSS,
        "pdf_preamble": MIT_PREAMBLE,
        "pdf_filter": MIT_FILTER,
        "before_body": MIT_BEFORE_BODY,
        "after_body": MIT_AFTER_BODY,
        "builder": MIT_BUILDER,
        "content_validator": MIT_VALIDATOR,
        "content_validation": MIT_REPORT,
        "browser_qa": MIT_BROWSER,
        "visual_qa": MIT_VISUAL,
        "independent_rereview": MIT_REREVIEW,
        "adverse_ledger": MIT_LEDGER,
        "backend_generator": "qa/extend_backend_mit_l06.py",
        "backend_validator": "qa/validate_backend_mit_l06.py",
    }
    identities: dict[str, Any] = {}
    for name, path in canonical_paths.items():
        try:
            size, file_hash = file_info(path)
            identities[name] = {"path": path, "bytes": size, "sha256": file_hash}
        except Exception as exc:
            identities[name] = {"path": path, "error": str(exc)}

    new_counts = dict(sorted(Counter(record.get("entity_type") for record in new_records).items()))
    receipt = {
        "schema": "o015-mit-l06-backend-validation-v1",
        "recorded_at": RECORDED_AT,
        "workflow": WORKFLOW,
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
            "segment_ids": sorted(SEGMENT_IDS),
            "formula_surface_ids": sorted(FORMULA_IDS),
            "figure_description_surface_ids": sorted(FIGURE_IDS),
            "correction_ids": sorted(CORRECTION_IDS),
            "top_level_items": 32,
            "nested_items": 17,
            "display_formulas": 12,
            "figure_descriptions": 5,
            "copied_source_graphics": 0,
            "canonical_build_command": CANONICAL_BUILD_COMMAND,
            "new_record_count": len(new_records),
            "new_entity_counts": new_counts,
            "new_ids_sha256": digest(("\n".join(sorted(EXPECTED_NEW_IDS)) + "\n").encode("utf-8")),
        },
        "backend": {
            "record_count": len(records),
            "jsonl": {"bytes": len(raw_jsonl), "sha256": digest(raw_jsonl)},
            "csv": {"bytes": len(raw_csv), "sha256": digest(raw_csv)},
            "csv_round_trip_lossless": not any("CSV" in error for error in errors),
        },
        "ledger_event_bindings": event_bindings,
        "canonical_identities": identities,
        "independent_validation": {
            "required_consecutive_processes": 2,
            "receipt_is_deterministic": True,
        },
        "limitations": [
            "PDF is searchable but untagged.",
            "Independent human/native-speaker Indonesian review is not recorded.",
            "Five source graphics are represented only by text descriptions; no source graphic bytes are redistributed.",
        ],
        "errors": errors,
        "result": "pass" if not errors else "fail",
    }
    REPORT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
