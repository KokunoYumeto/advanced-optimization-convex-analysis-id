#!/usr/bin/env python3
"""Deterministically admit Habring's preface and Chapters 1--2.

The protected input is the 2,472-record backend through MIT Lecture 11.  A
rerun removes only records owned by ``o015-habring-ch01-ch02-backend-v1``,
reconstructs that exact baseline, and regenerates the locale-neutral Habring
projection.  Canonical replacement occurs only with ``--write-canonical``.
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

RECORDED_AT = "2026-08-25T00:15:00Z"
WORKFLOW = "o015-habring-ch01-ch02-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 2_472
BASELINE_JSONL = (
    1_942_530,
    "b6a49365c69c6ce3d524fe658e16763a036661daf46d0dc8e8182bfff5e58a78",
)
BASELINE_CSV = (
    2_313_694,
    "8bbcb8d978d90073462fb966ab368b59cf226c794cf338060706dfccbee9ea66",
)
BASELINE_ID_SET_SHA256 = "14bfd29f686f2452a4b59881240f7ae1db7b87fc9ca8c44e3f703372e5b07c46"
BASELINE_ID_ORDER_SHA256 = "569c92dbb5186e3c0f208e9f08ebe581c25203c64aa80bef4e4d16102202d339"
BASELINE_RECORD_SET_SHA256 = "74f0dc0f3f2a15e4bcb17ec1a3870d1db0e464663f8d9adf5b2df1a0d020314e"
BASELINE_LINE_SEQUENCE_SHA256 = "db797d6eab5b7582d7ca4c3f3f8d717cea2c173700d7dc24224d79e3341f4e04"

SOURCE_EDITION_ID = "edition.habring.convex-optimization.arxiv-2607-11664v1"
TARGET_EDITION_ID = "edition.habring.convex-optimization.id-id.v1"
ROOT_UNIT_ID = "unit.habring.v1"

TARGETS = {
    "ch01": "source/id-ID/habring-01-prasyarat-id.tex",
    "ch02": "source/id-ID/habring-02-konveksitas-id.tex",
}
UNITS = {
    "ch01": "unit.habring.v1.ch01",
    "ch02": "unit.habring.v1.ch02",
}
SOURCE_RIGHTS = {
    "ch01": "rights.o015-habring-ch01-source",
    "ch02": "rights.o015-habring-ch02-source",
}
TARGET_RIGHTS = {
    "ch01": "rights.o015-habring-derivative-ch01",
    "ch02": "rights.o015-habring-derivative-ch02",
}

WRAPPER = "source/id-ID/D90-HAB-01-02-prasyarat-dan-konveksitas-id.tex"
UNIT_PDF = "output/pdf/D90-HAB-01-02-prasyarat-dan-konveksitas-id.pdf"
FULL_HTML = "output/html/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html"
FULL_READER = "output/pdf/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf"
TEXT_EXTRACT = "qa/D90-HAB-01-02-prasyarat-dan-konveksitas-id.txt"
UNIT_BUILD_REPORT = "qa/HABRING_CH01_CH02_BUILD.json"
FULL_HTML_REPORT = "qa/HABRING_FULL_HTML_BUILD.json"
FULL_READER_REPORT = "qa/HABRING_FULL_READER_BUILD.json"
SOLVER_REPORT = "qa/HABRING_CH01_CH02_SOLVER_RESULTS.json"
CORRECTION_SNAPSHOTS = (
    "qa/HABRING_CH01_CH02_PROPOSED_LEDGER.jsonl",
    "qa/HABRING_CH02_PROPOSED_LEDGER.jsonl",
)
FULL_EPUB = "output/epub/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub"
FULL_EPUB_REPORT = "qa/HABRING_FULL_EPUB_BUILD.json"

GENERATOR = "qa/extend_backend_habring_ch01_ch02.py"
VALIDATOR = "qa/validate_backend_habring_ch01_ch02.py"

FROZEN_IDENTITIES = {
    "authority/habring/source-v1/preface.tex": (
        492,
        "d6ec9d0522446fc65f3868d0b7cd1d221462c3099fbd0b2d6ea412ab53315967",
    ),
    "authority/habring/source-v1/preliminaries.tex": (
        26_946,
        "8c1e4bdad36f2dcb57867c475afa5adce12a3951fc650e8667f2e4d82d3b569d",
    ),
    "authority/habring/source-v1/convexity.tex": (
        29_947,
        "e5cf93ad93cb2064bdff6c1ea200f20b4eb94351127185a01d678c3fb5a662b8",
    ),
    TARGETS["ch01"]: (
        31_009,
        "6ed957c8bf654608e8d572b2f0368478a4dc185ba51c150ea9dee36bb62868e7",
    ),
    TARGETS["ch02"]: (
        42_828,
        "99a992f36756cb64f82d21cfcaf68fdaee8b8dd61ef2b007322d9d2623989f22",
    ),
    WRAPPER: (
        5_357,
        "301d45dc305ee86f439ed1056a62b47199f3439d88ba66436f127a5cee0e35b2",
    ),
    UNIT_PDF: (
        720_624,
        "5fc51737b0ec2d2342e93c0a53a997cd1f81a3df2d15415ef5fdd9c2c4a9dbdf",
    ),
    FULL_READER: (
        3_779_312,
        "da2b421b97efce4e3d7b8cf6be9938d17b7768b9c6bcb4846b09b9c692b34c41",
    ),
    TEXT_EXTRACT: (
        59_808,
        "8e2f3d0e9555a138faeffada4e6fd07baf66d96055c018cf7b3554fbfe5491b0",
    ),
    SOLVER_REPORT: (
        6_909,
        "3debf7f8875c1dc5ce89f8c163f0cd349edb62849e861719aa80bd6931009587",
    ),
    CORRECTION_SNAPSHOTS[0]: (
        12_339,
        "ceb880ccc6d5fadccd622662cb41886fa851c58a20e782fc0245d61092e92aff",
    ),
    CORRECTION_SNAPSHOTS[1]: (
        29_034,
        "585e2f40004c3b31cc766c46acdd86f939bcb4bba33dc024448a660ae44fdc78",
    ),
    "source/id-ID/figures/discontinuous_function.png": (
        20_911,
        "fc5b5b3135eb726c58ef8e299751d310dfc363f7d31d7c28930ad018388397fa",
    ),
    "source/id-ID/figures/lsc_function.png": (
        20_904,
        "2edde214506a703a0e40d5e32a1df5ae50809c0698cec2a3d7cd248647010547",
    ),
    "source/id-ID/figures/sets.png": (
        36_071,
        "08bc716590267148f90b4dc45dc62e3959713b573b809c81c08967ab8cecda2e",
    ),
    "source/id-ID/figures/balls.png": (
        14_419,
        "637e5a503469918640b6a8eb3971e74ae4d3778b5ef73808493ce2ceef2f0a31",
    ),
    "source/id-ID/figures/convex_fct.png": (
        31_570,
        "c0844bf6b3732883d2faff403179ec3eb74ebe867f3ae68cc98ac192c70d373b",
    ),
}

EXPECTED_SEGMENT_IDS = {
    "ch01": [f"d90.hab.v1.ch01.seg{index:04d}" for index in range(1, 9)],
    "ch02": [f"d90.hab.v1.ch02.seg{index:04d}" for index in range(1, 18)],
}
EXPECTED_CORRECTION_IDS = [f"O015-HAB-ADV-{number:04d}" for number in range(97, 162)]
EXPECTED_SURFACE_COUNTS = {
    "ch01": Counter(
        {
            "formula": 51,
            "definition": 17,
            "proof": 12,
            "theorem": 8,
            "example": 5,
            "exercise": 3,
            "lemma": 3,
            "remark": 2,
            "corollary": 2,
            "figure": 1,
        }
    ),
    "ch02": Counter(
        {
            "formula": 65,
            "proof": 15,
            "theorem": 9,
            "lemma": 7,
            "figure": 7,
            "definition": 6,
            "example": 5,
            "proposition": 1,
        }
    ),
}

ENVIRONMENT_SURFACE = {
    "defn": "definition",
    "theorem": "theorem",
    "lemma": "lemma",
    "cor": "corollary",
    "prop": "proposition",
    "example": "example",
    "exercise": "exercise",
    "rem": "remark",
    "figure": "figure",
    "proof": "proof",
    "equation": "formula",
    "equation*": "formula",
    "gather": "formula",
    "gather*": "formula",
    "align": "formula",
    "align*": "formula",
}

EXPECTED_NEW_RECORD_COUNT = 624
EXPECTED_ENTITY_COUNTS: Counter[str] = Counter(
    {
        "unit": 2,
        "segment": 25,
        "learning_surface": 225,
        "asset": 5,
        "rights": 8,
        "correction": 65,
        "artifact": 25,
        "qa_event": 11,
        "relation": 258,
    }
)


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


def normalized_slice(relative: str, start: int, end: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid slice {relative}:{start}-{end}")
    data = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
    return len(data), sha256(data)


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
    record_id: str,
    artifact_kind: str,
    path: str,
    rights_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    size, digest = file_info(path)
    record = common("artifact", record_id, "current")
    record.update(
        {
            "artifact_kind": artifact_kind,
            "path": path,
            "bytes": size,
            "sha256": digest,
            "hash_algorithm": "sha256-raw-bytes",
            **extra,
        }
    )
    if rights_id is not None:
        record["rights_id"] = rights_id
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
        raise ValueError(f"{context}: JSONL differs from protected 2,472-record baseline")
    if (len(csv_raw), sha256(csv_raw)) != BASELINE_CSV:
        raise ValueError(f"{context}: CSV differs from protected 2,472-record baseline")
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


def validate_frozen_identities() -> None:
    for relative, expected in FROZEN_IDENTITIES.items():
        if file_info(relative) != expected:
            raise ValueError(f"frozen identity differs: {relative}")
    for target, source in (
        (
            "source/id-ID/figures/discontinuous_function.png",
            "authority/habring/source-v1/figures/discontinuous_function.png",
        ),
        (
            "source/id-ID/figures/lsc_function.png",
            "authority/habring/source-v1/figures/lsc_function.png",
        ),
        (
            "source/id-ID/figures/sets.png",
            "authority/habring/source-v1/figures/sets.png",
        ),
        (
            "source/id-ID/figures/balls.png",
            "authority/habring/source-v1/figures/balls.png",
        ),
        (
            "source/id-ID/figures/convex_fct.png",
            "authority/habring/source-v1/figures/convex_fct.png",
        ),
    ):
        if file_info(target) != file_info(source):
            raise ValueError(f"inherited figure is not an exact copy: {target}")


def load_build_evidence() -> dict[str, Any]:
    unit = json.loads((ROOT / UNIT_BUILD_REPORT).read_text(encoding="utf-8"))
    html = json.loads((ROOT / FULL_HTML_REPORT).read_text(encoding="utf-8"))
    reader = json.loads((ROOT / FULL_READER_REPORT).read_text(encoding="utf-8"))
    epub = json.loads((ROOT / FULL_EPUB_REPORT).read_text(encoding="utf-8"))
    solver = json.loads((ROOT / SOLVER_REPORT).read_text(encoding="utf-8"))

    for label, report in (
        ("unit", unit),
        ("html", html),
        ("reader", reader),
        ("epub", epub),
    ):
        if report.get("result") != "pass":
            raise ValueError(f"{label} build report is not a pass")
        determinism = report.get("determinism", {})
        if determinism.get("builds") != 2 or determinism.get("byte_identical") is not True:
            raise ValueError(f"{label} build lacks two byte-identical builds")
    if solver.get("result") != "pass" or solver.get("gate_count") != 32:
        raise ValueError("solver report does not prove its 32-gate closure")
    if any(gate.get("pass") is not True for gate in solver.get("gates", [])):
        raise ValueError("solver report contains a failed gate")
    if solver.get("negative_control_count") != 9 or any(
        control.get("pass") is not True
        for control in solver.get("negative_controls", [])
    ):
        raise ValueError("solver negative-control closure differs")

    bindings = (
        (unit["artifact"], UNIT_PDF),
        (unit["wrapper"], WRAPPER),
        (unit["text_extract"], TEXT_EXTRACT),
        (html["artifact"], FULL_HTML),
        (reader["artifact"], FULL_READER),
        (epub["artifact"], FULL_EPUB),
    )
    for reported, relative in bindings:
        if reported.get("path") != relative:
            raise ValueError(f"build report path differs for {relative}")
        if (reported.get("bytes"), reported.get("sha256")) != file_info(relative):
            raise ValueError(f"build report does not bind current bytes: {relative}")

    expected_inputs = {path: digest for path, (_, digest) in FROZEN_IDENTITIES.items()}
    for report in (unit, html, epub):
        for item in report.get("inputs", []):
            path = item["path"]
            if path in expected_inputs and item.get("sha256") != expected_inputs[path]:
                raise ValueError(f"build input hash differs: {path}")
    if unit["artifact"].get("pages") != 36:
        raise ValueError("unit reader page count differs from 36")
    if reader["artifact"].get("pages") != 139:
        raise ValueError("full reader page count differs from 139")
    if html["artifact"].get("embedded_image_count") != 5:
        raise ValueError("full HTML does not bind all five inherited raster figures")
    if (
        epub["artifact"].get("mathml_count") != 2_206
        or epub["artifact"].get("manifest_resource_closure") is not True
        or epub["artifact"].get("unresolved_internal_references") != []
        or epub["artifact"].get("xml_parse_failures") != []
    ):
        raise ValueError("EPUB semantic/resource closure differs")
    return {
        "unit": unit,
        "html": html,
        "reader": reader,
        "epub": epub,
        "solver": solver,
    }


SEGMENT_HEADER = re.compile(
    r"^% H(?P<chapter>\d{2})-S(?P<number>\d{3}) \| sumber "
    r"(?P<path>\S+) baris (?P<start>\d+)--(?P<end>\d+)$"
)


def parse_segments() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for chapter, target_path in TARGETS.items():
        lines = (ROOT / target_path).read_text(encoding="utf-8").splitlines()
        headers: list[dict[str, Any]] = []
        for line_number, line in enumerate(lines, start=1):
            match = SEGMENT_HEADER.fullmatch(line)
            if not match:
                continue
            if line_number >= len(lines) or not lines[line_number].startswith("% segment-id: "):
                raise ValueError(f"segment marker missing after {target_path}:{line_number}")
            segment_id = lines[line_number].split(": ", 1)[1]
            headers.append(
                {
                    "chapter": chapter,
                    "marker_line": line_number,
                    "source_path": match.group("path"),
                    "source_start": int(match.group("start")),
                    "source_end": int(match.group("end")),
                    "id": segment_id,
                }
            )
        if [item["id"] for item in headers] != EXPECTED_SEGMENT_IDS[chapter]:
            raise ValueError(f"{chapter} stable segment closure differs")
        for index, spec in enumerate(headers):
            spec["order"] = index + 1
            spec["target_path"] = target_path
            spec["target_start"] = 1 if index == 0 else spec["marker_line"]
            spec["target_end"] = (
                headers[index + 1]["marker_line"] - 1
                if index + 1 < len(headers)
                else len(lines)
            )
            specs.append(spec)

            source_bytes, source_digest = normalized_slice(
                spec["source_path"], spec["source_start"], spec["source_end"]
            )
            target_bytes, target_digest = normalized_slice(
                target_path, spec["target_start"], spec["target_end"]
            )
            record = common("segment", spec["id"], "current")
            record.update(
                {
                    "unit_id": UNITS[chapter],
                    "order": index + 1,
                    "source_edition_id": SOURCE_EDITION_ID,
                    "target_edition_id": TARGET_EDITION_ID,
                    "source_path": spec["source_path"],
                    "source_line_start": spec["source_start"],
                    "source_line_end": spec["source_end"],
                    "source_locator": (
                        f"{spec['source_path']}:{spec['source_start']}-{spec['source_end']}"
                    ),
                    "source_content_bytes": source_bytes,
                    "source_content_sha256": source_digest,
                    "target_path": target_path,
                    "target_line_start": spec["target_start"],
                    "target_line_end": spec["target_end"],
                    "target_locator": (
                        f"{target_path}:{spec['target_start']}-{spec['target_end']}"
                    ),
                    "target_content_bytes": target_bytes,
                    "target_content_sha256": target_digest,
                    "hash_normalization": "utf8-lf-final-newline",
                    "translation_state": "built",
                    "mathematical_review_state": "correction_audited_and_solver_checked",
                    "rights_id": TARGET_RIGHTS[chapter],
                }
            )
            records.append(record)
    if len(records) != 25:
        raise ValueError("segment count differs from 25")
    return specs, records


TOKEN = re.compile(r"\\(?P<kind>begin|end)\{(?P<env>[^}]+)\}")


def strip_tex_comment(line: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", line)


def segment_for_target_line(
    specs: list[dict[str, Any]], chapter: str, line_number: int
) -> str:
    matches = [
        spec["id"]
        for spec in specs
        if spec["chapter"] == chapter
        and spec["target_start"] <= line_number <= spec["target_end"]
    ]
    if len(matches) != 1:
        raise ValueError(f"target line {chapter}:{line_number} has {len(matches)} segments")
    return matches[0]


def parse_surfaces(
    specs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    surface_specs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for chapter, target_path in TARGETS.items():
        lines = (ROOT / target_path).read_text(encoding="utf-8").splitlines()
        stack: list[tuple[str, int]] = []
        found: list[dict[str, Any]] = []
        bracket_start: int | None = None
        for line_number, raw_line in enumerate(lines, start=1):
            line = strip_tex_comment(raw_line)
            bracket_tokens = sorted(
                [
                    (match.start(), match.group(0))
                    for match in re.finditer(r"(?<!\\)\\(?:\[|\])", line)
                ],
                key=lambda item: item[0],
            )
            for _, token in bracket_tokens:
                if token == r"\[":
                    if bracket_start is not None:
                        raise ValueError(f"nested bracket display at {target_path}:{line_number}")
                    bracket_start = line_number
                else:
                    if bracket_start is None:
                        raise ValueError(f"orphan bracket display end at {target_path}:{line_number}")
                    found.append(
                        {
                            "surface_type": "formula",
                            "environment": "bracket-display",
                            "start": bracket_start,
                            "end": line_number,
                        }
                    )
                    bracket_start = None

            for match in TOKEN.finditer(line):
                kind = match.group("kind")
                env = match.group("env")
                if kind == "begin":
                    stack.append((env, line_number))
                    continue
                if not stack or stack[-1][0] != env:
                    raise ValueError(f"unbalanced {env} at {target_path}:{line_number}")
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
        if stack or bracket_start is not None:
            raise ValueError(f"unclosed environment/display in {target_path}")
        if Counter(item["surface_type"] for item in found) != EXPECTED_SURFACE_COUNTS[chapter]:
            raise ValueError(f"{chapter} semantic/math surface topology differs")

        counters: Counter[str] = Counter()
        for item in sorted(found, key=lambda value: (value["start"], value["end"], value["environment"])):
            surface_type = item["surface_type"]
            counters[surface_type] += 1
            surface_id = (
                f"surface.habring.v1.{chapter}.{surface_type}.{counters[surface_type]:04d}"
            )
            segment_id = segment_for_target_line(specs, chapter, item["start"])
            content_bytes, content_digest = normalized_slice(
                target_path, item["start"], item["end"]
            )
            content = "\n".join(lines[item["start"] - 1 : item["end"]])
            labels = re.findall(r"\\label\{([^}]+)\}", content)
            spec = {
                **item,
                "id": surface_id,
                "chapter": chapter,
                "segment_id": segment_id,
            }
            surface_specs.append(spec)
            record = common("learning_surface", surface_id, "current")
            record.update(
                {
                    "unit_id": UNITS[chapter],
                    "surface_type": surface_type,
                    "presence": "present",
                    "count": 1,
                    "latex_environment": item["environment"],
                    "target_edition_id": TARGET_EDITION_ID,
                    "target_path": target_path,
                    "target_line_start": item["start"],
                    "target_line_end": item["end"],
                    "target_content_bytes": content_bytes,
                    "target_content_sha256": content_digest,
                    "hash_normalization": "utf8-lf-final-newline",
                    "related_segment_ids": [segment_id],
                    "latex_labels": labels,
                    "rights_id": TARGET_RIGHTS[chapter],
                }
            )
            records.append(record)

        source_scope_paths = (
            [
                "authority/habring/source-v1/preface.tex",
                "authority/habring/source-v1/preliminaries.tex",
            ]
            if chapter == "ch01"
            else ["authority/habring/source-v1/convexity.tex"]
        )
        source_scope = "\n".join(
            (ROOT / path).read_text(encoding="utf-8") for path in source_scope_paths
        )
        target_scope = "\n".join(lines)
        for absent in ("hint", "answer", "solution"):
            environment_pattern = re.compile(rf"\\begin\{{{absent}s?\}}")
            if environment_pattern.search(source_scope) or environment_pattern.search(target_scope):
                raise ValueError(f"{chapter} unexpectedly contains a formal {absent} environment")
            record_id = f"surface.habring.v1.{chapter}.{absent}-closure"
            record = common("learning_surface", record_id, "source_absent")
            record.update(
                {
                    "unit_id": UNITS[chapter],
                    "surface_type": absent,
                    "presence": "absent",
                    "count": 0,
                    "absence_scope": "formal source environments in the admitted chapter",
                    "source_edition_id": SOURCE_EDITION_ID,
                    "target_edition_id": TARGET_EDITION_ID,
                    "rights_id": TARGET_RIGHTS[chapter],
                }
            )
            records.append(record)
    return surface_specs, records


def rights_records() -> list[dict[str, Any]]:
    specs = [
        (
            "rights.o015-habring-ch01-source",
            "o015-habring-ch01-source",
            "authority/habring/source-v1/preface.tex + authority/habring/source-v1/preliminaries.tex",
            "admitted",
            "Preface and Chapter 1 authority TeX.",
        ),
        (
            "rights.o015-habring-ch02-source",
            "o015-habring-ch02-source",
            "authority/habring/source-v1/convexity.tex",
            "admitted",
            "Chapter 2 authority TeX.",
        ),
        (
            "rights.o015-habring-derivative-ch01",
            "o015-habring-derivative-ch01",
            TARGETS["ch01"],
            "derivative",
            "Independent id-ID translation of the preface and Chapter 1.",
        ),
        (
            "rights.o015-habring-derivative-ch02",
            "o015-habring-derivative-ch02",
            TARGETS["ch02"],
            "derivative",
            "Independent id-ID translation of Chapter 2.",
        ),
        (
            "rights.o015-habring-ch01-raster-figures",
            "o015-habring-ch01-raster-figures",
            "authority/habring/source-v1/figures/discontinuous_function.png + authority/habring/source-v1/figures/lsc_function.png",
            "admitted_with_notice",
            "Exact inherited raster bytes; the arXiv submission supplies component-level CC BY 4.0 evidence and no separate embedded notice.",
        ),
        (
            "rights.o015-habring-ch02-raster-figures",
            "o015-habring-ch02-raster-figures",
            "authority/habring/source-v1/figures/sets.png + authority/habring/source-v1/figures/balls.png + authority/habring/source-v1/figures/convex_fct.png",
            "admitted_with_notice",
            "Exact inherited raster bytes; the arXiv submission supplies component-level CC BY 4.0 evidence and no separate embedded notice.",
        ),
        (
            "rights.o015-habring-reader-ch01-ch09",
            "o015-habring-reader-ch01-ch09",
            f"{UNIT_PDF} + {FULL_HTML} + {FULL_READER} + {FULL_EPUB}",
            "derivative",
            "Reader builds contain only Habring CC BY 4.0 source and the independently localized derivative.",
        ),
    ]
    records: list[dict[str, Any]] = []
    for record_id, component_id, path, status, notes in specs:
        record = common("rights", record_id, status)
        record.update(
            {
                "component_id": component_id,
                "path": path,
                "source_authority_id": "o015-habring-arxiv-2607.11664v1",
                "rights_expression": "CC BY 4.0",
                "authority_url": "https://arxiv.org/abs/2607.11664v1",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "translation_permitted": True,
                "required_handling": [
                    "attribute Andreas Habring",
                    "link CC BY 4.0",
                    "identify translation and corrections",
                    "no implied endorsement",
                ],
                "notes": notes,
            }
        )
        records.append(record)

    tooling = common(
        "rights", "rights.o015-habring-ch01-ch02-tooling", "admitted"
    )
    tooling.update(
        {
            "component_id": "o015-habring-ch01-ch02-tooling",
            "path": "qa/build_habring_ch01_ch02.py + qa/build_habring_full_html.py + qa/build_habring_full_reader.py + qa/build_habring_full_epub.py + qa/validate_habring_ch01_ch02_math.py + qa/extend_backend_habring_ch01_ch02.py + qa/validate_backend_habring_ch01_ch02.py",
            "source_authority_id": "lane-authored",
            "rights_expression": "project-local build and validation code",
            "authority_url": GENERATOR,
            "license_url": None,
            "translation_permitted": False,
            "required_handling": ["ship source with results", "use open toolchains"],
            "notes": "Deterministic build, computation, and backend tooling; not part of Habring's authored mathematical text.",
        }
    )
    records.append(tooling)
    return records


def unit_records() -> list[dict[str, Any]]:
    specs = [
        (
            "ch01",
            1,
            "chapter-1-with-preface",
            "Preface and 1 — Preliminaries",
            "Prakata dan 1 — Prasyarat",
            "authority/habring/source-v1/preface.tex:1-8; authority/habring/source-v1/preliminaries.tex:1-530",
            1,
            14,
            "Chapter 2 — Convexity",
        ),
        (
            "ch02",
            2,
            "chapter-2",
            "2 — Convexity",
            "2 — Kekonveksan",
            "authority/habring/source-v1/convexity.tex:1-699",
            15,
            29,
            "Chapter 3 — Subgradients",
        ),
    ]
    records: list[dict[str, Any]] = []
    for chapter, order, local_id, source_label, target_label, locator, p0, p1, next_unit in specs:
        target_lines = len((ROOT / TARGETS[chapter]).read_text(encoding="utf-8").splitlines())
        record = common("unit", UNITS[chapter], "built")
        record.update(
            {
                "edition_id": TARGET_EDITION_ID,
                "source_edition_id": SOURCE_EDITION_ID,
                "target_edition_id": TARGET_EDITION_ID,
                "parent_id": ROOT_UNIT_ID,
                "unit_kind": "chapter_with_preface" if chapter == "ch01" else "chapter",
                "order": order,
                "source_local_id": local_id,
                "source_local_label": source_label,
                "target_local_label": target_label,
                "source_locator": locator,
                "target_locator": f"{TARGETS[chapter]}:1-{target_lines}",
                "printed_page_start": p0,
                "printed_page_end": p1,
                "rights_id": TARGET_RIGHTS[chapter],
                "translation_state": "built",
                "next_source_order_unit": next_unit,
            }
        )
        records.append(record)
    return records


def asset_records() -> list[dict[str, Any]]:
    specs = [
        ("ch01", "discontinuous-function", "discontinuous_function.png"),
        ("ch01", "lower-semicontinuous-function", "lsc_function.png"),
        ("ch02", "convex-sets", "sets.png"),
        ("ch02", "norm-balls", "balls.png"),
        ("ch02", "convex-function", "convex_fct.png"),
    ]
    records: list[dict[str, Any]] = []
    for chapter, suffix, filename in specs:
        source = f"authority/habring/source-v1/figures/{filename}"
        target = f"source/id-ID/figures/{filename}"
        source_size, source_digest = file_info(source)
        target_size, target_digest = file_info(target)
        record = common("asset", f"asset.habring.v1.{chapter}.{suffix}", "current")
        record.update(
            {
                "asset_kind": "raster_figure",
                "unit_id": UNITS[chapter],
                "source_path": source,
                "source_bytes": source_size,
                "source_sha256": source_digest,
                "target_path": target,
                "target_bytes": target_size,
                "target_sha256": target_digest,
                "hash_algorithm": "sha256-raw-bytes",
                "derivative_state": "exact_copy",
                "rights_id": (
                    "rights.o015-habring-ch01-raster-figures"
                    if chapter == "ch01"
                    else "rights.o015-habring-ch02-raster-figures"
                ),
            }
        )
        records.append(record)
    return records


def correction_records(
    segment_specs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    events: list[tuple[str, int, bytes, dict[str, Any]]] = []
    for snapshot in CORRECTION_SNAPSHOTS:
        lines = (ROOT / snapshot).read_bytes().splitlines(keepends=True)
        for line_number, raw in enumerate(lines, start=1):
            event = json.loads(raw.decode("utf-8"))
            events.append((snapshot, line_number, raw, event))
    if [event["event_id"] for _, _, _, event in events] != EXPECTED_CORRECTION_IDS:
        raise ValueError("correction snapshot event closure differs from 0097--0161")

    for snapshot, line_number, raw, event in events:
        event_id = event["event_id"]
        source_locator = event.get("source")
        if not isinstance(source_locator, str) or ":" not in source_locator:
            raise ValueError(f"{event_id} lacks a source locator")
        source_name, line_part = source_locator.split(":", 1)
        source_path = f"authority/habring/source-v1/{source_name}"
        numbers = [int(value) for value in re.findall(r"\d+", line_part)]
        if not numbers:
            raise ValueError(f"{event_id} source locator lacks a line")
        source_start, source_end = min(numbers), max(numbers)
        affected = [
            spec["id"]
            for spec in segment_specs
            if spec["source_path"] == source_path
            and not (source_end < spec["source_start"] or source_start > spec["source_end"])
        ]
        if not affected:
            raise ValueError(f"{event_id} does not intersect an admitted segment")
        unit_ids = sorted({UNITS[spec["chapter"]] for spec in segment_specs if spec["id"] in affected})
        correction_id = f"correction.{event_id.lower()}"
        evidence_artifact_id = (
            "artifact.habring.correction-snapshot-ch01"
            if snapshot == CORRECTION_SNAPSHOTS[0]
            else "artifact.habring.correction-snapshot-ch02"
        )
        record = common("correction", correction_id, "applied")
        record.update(
            {
                "source_event_id": event_id,
                "source_edition_id": SOURCE_EDITION_ID,
                "affected_unit_ids": unit_ids,
                "affected_segment_ids": affected,
                "source_path": source_path,
                "source_line_start": source_start,
                "source_line_end": source_end,
                "source_locator": f"{source_path}:{line_part}",
                "surface": event["surface"],
                "source_issue": event["source_issue"],
                "target_action": event["target_action"],
                "correction_class": event["class"],
                "project_authorship": event.get("project_authorship"),
                "rights": event.get("rights"),
                "disposition": "applied",
                "upstream_report_disposition": "not_submitted",
                "evidence_artifact_id": evidence_artifact_id,
                "ledger_binding": {
                    "path": snapshot,
                    "line": line_number,
                    "raw_line_bytes": len(raw),
                    "raw_line_sha256": sha256(raw),
                    "canonical_event_sha256": sha256(canonical_json(event).encode("utf-8")),
                },
            }
        )
        records.append(record)
        bindings.append(
            {"event_id": event_id, "record_id": correction_id, "segments": affected}
        )
    return bindings, records


def artifact_records(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    reader_inputs = [
        "artifact.habring.target-pdf-ch01-ch02",
        "artifact.habring.target-pdf",
        "artifact.habring.target-pdf-ch04",
        "artifact.habring.target-pdf-ch05",
        "artifact.habring.target-pdf-ch06",
        "artifact.habring.target-pdf-ch07",
        "artifact.habring.target-pdf-ch08",
        "artifact.habring.target-pdf-ch09",
    ]
    html_inputs = [
        "artifact.habring.target-ch01",
        "artifact.habring.target-ch02",
        "artifact.habring.target-ch03",
        "artifact.habring.target-ch04",
        "artifact.habring.target-ch05",
        "artifact.habring.target-ch06",
        "artifact.habring.target-ch07",
        "artifact.habring.target-ch08",
        "artifact.habring.target-ch09",
    ]
    return [
        artifact(
            "artifact.habring.source-preface",
            "source_tex",
            "authority/habring/source-v1/preface.tex",
            SOURCE_RIGHTS["ch01"],
            source_edition_id=SOURCE_EDITION_ID,
        ),
        artifact(
            "artifact.habring.source-ch01",
            "source_tex",
            "authority/habring/source-v1/preliminaries.tex",
            SOURCE_RIGHTS["ch01"],
            source_edition_id=SOURCE_EDITION_ID,
        ),
        artifact(
            "artifact.habring.source-ch02",
            "source_tex",
            "authority/habring/source-v1/convexity.tex",
            SOURCE_RIGHTS["ch02"],
            source_edition_id=SOURCE_EDITION_ID,
        ),
        artifact(
            "artifact.habring.target-ch01",
            "target_tex",
            TARGETS["ch01"],
            TARGET_RIGHTS["ch01"],
            target_edition_id=TARGET_EDITION_ID,
            input_artifact_ids=["artifact.habring.source-preface", "artifact.habring.source-ch01"],
        ),
        artifact(
            "artifact.habring.target-ch02",
            "target_tex",
            TARGETS["ch02"],
            TARGET_RIGHTS["ch02"],
            target_edition_id=TARGET_EDITION_ID,
            source_artifact_id="artifact.habring.source-ch02",
        ),
        artifact(
            "artifact.habring.target-wrapper-ch01-ch02",
            "reader_wrapper_tex",
            WRAPPER,
            "rights.o015-habring-reader-ch01-ch09",
            target_edition_id=TARGET_EDITION_ID,
            input_artifact_ids=["artifact.habring.target-ch01", "artifact.habring.target-ch02"],
        ),
        artifact(
            "artifact.habring.target-pdf-ch01-ch02",
            "reader_pdf",
            UNIT_PDF,
            "rights.o015-habring-reader-ch01-ch09",
            target_edition_id=TARGET_EDITION_ID,
            pages=evidence["unit"]["artifact"]["pages"],
            catalog_lang=evidence["unit"]["artifact"]["catalog_lang"],
            build_event_id="qa.o015.habring-ch01-ch02.build",
            accessibility="searchable id-ID PDF; untagged",
            input_artifact_ids=[
                "artifact.habring.target-wrapper-ch01-ch02",
                "artifact.habring.target-ch01",
                "artifact.habring.target-ch02",
                "artifact.habring.target-macros",
                "artifact.habring.target-class",
            ],
        ),
        artifact(
            "artifact.habring.target-html-ch01-ch09",
            "reader_html",
            FULL_HTML,
            "rights.o015-habring-reader-ch01-ch09",
            target_edition_id=TARGET_EDITION_ID,
            build_event_id="qa.o015.habring-ch01-ch02.full-html",
            lang="id-ID",
            accessibility="responsive semantic HTML with embedded raster resources and MathJax markup",
            input_artifact_ids=html_inputs,
        ),
        artifact(
            "artifact.habring.target-pdf-ch01-ch09",
            "reader_pdf",
            FULL_READER,
            "rights.o015-habring-reader-ch01-ch09",
            target_edition_id=TARGET_EDITION_ID,
            pages=evidence["reader"]["artifact"]["pages"],
            catalog_lang=evidence["reader"]["artifact"]["catalog_lang"],
            build_event_id="qa.o015.habring-ch01-ch02.full-reader",
            accessibility="searchable id-ID PDF; untagged composite reader",
            input_artifact_ids=reader_inputs,
        ),
        artifact(
            "artifact.habring.target-epub-ch01-ch09",
            "reader_epub",
            FULL_EPUB,
            "rights.o015-habring-reader-ch01-ch09",
            target_edition_id=TARGET_EDITION_ID,
            build_event_id="qa.o015.habring-ch01-ch02.full-epub",
            accessibility="EPUB 3 with MathML, navigation, nonempty raster alternatives, and textual TikZ fallbacks",
            input_artifact_ids=html_inputs,
            mathml_count=evidence["epub"]["artifact"]["mathml_count"],
            manifest_resource_closure=evidence["epub"]["artifact"]["manifest_resource_closure"],
        ),
        artifact(
            "artifact.habring.target-text-ch01-ch02",
            "qa_extract",
            TEXT_EXTRACT,
            "rights.o015-habring-reader-ch01-ch09",
            target_edition_id=TARGET_EDITION_ID,
            source_artifact_id="artifact.habring.target-pdf-ch01-ch02",
        ),
        artifact("artifact.habring.build-report-ch01-ch02", "build_receipt", UNIT_BUILD_REPORT),
        artifact("artifact.habring.full-html-build-report", "build_receipt", FULL_HTML_REPORT),
        artifact("artifact.habring.full-reader-build-report", "build_receipt", FULL_READER_REPORT),
        artifact("artifact.habring.full-epub-build-report", "build_receipt", FULL_EPUB_REPORT),
        artifact(
            "artifact.habring.solver-results-ch01-ch02",
            "qa_report",
            SOLVER_REPORT,
            "rights.o015-habring-ch01-ch02-tooling",
            toolchain="Python / NumPy",
        ),
        artifact(
            "artifact.habring.solver-validator-ch01-ch02",
            "qa_source",
            "qa/validate_habring_ch01_ch02_math.py",
            "rights.o015-habring-ch01-ch02-tooling",
            toolchain="Python / NumPy",
        ),
        artifact(
            "artifact.habring.builder-ch01-ch02",
            "qa_source",
            "qa/build_habring_ch01_ch02.py",
            "rights.o015-habring-ch01-ch02-tooling",
            toolchain="Python / latexmk / pdfTeX",
        ),
        artifact(
            "artifact.habring.full-html-builder",
            "qa_source",
            "qa/build_habring_full_html.py",
            "rights.o015-habring-ch01-ch02-tooling",
            toolchain="Python / Pandoc",
        ),
        artifact(
            "artifact.habring.full-reader-builder",
            "qa_source",
            "qa/build_habring_full_reader.py",
            "rights.o015-habring-ch01-ch02-tooling",
            toolchain="Python / pypdf / ReportLab",
        ),
        artifact(
            "artifact.habring.full-epub-builder",
            "qa_source",
            "qa/build_habring_full_epub.py",
            "rights.o015-habring-ch01-ch02-tooling",
            toolchain="Python / Pandoc / EPUB 3",
        ),
        artifact(
            "artifact.habring.correction-snapshot-ch01",
            "correction_ledger_snapshot",
            CORRECTION_SNAPSHOTS[0],
            "rights.o015-habring-ch01-ch02-tooling",
            event_ids=EXPECTED_CORRECTION_IDS[:25],
        ),
        artifact(
            "artifact.habring.correction-snapshot-ch02",
            "correction_ledger_snapshot",
            CORRECTION_SNAPSHOTS[1],
            "rights.o015-habring-ch01-ch02-tooling",
            event_ids=EXPECTED_CORRECTION_IDS[25:],
        ),
        artifact(
            "artifact.o015.backend-generator-habring-ch01-ch02",
            "backend_generator",
            GENERATOR,
            "rights.o015-habring-ch01-ch02-tooling",
            toolchain="Python 3 standard library",
            protected_baseline_record_count=BASELINE_RECORD_COUNT,
        ),
        artifact(
            "artifact.o015.backend-validator-habring-ch01-ch02",
            "backend_validator",
            VALIDATOR,
            "rights.o015-habring-ch01-ch02-tooling",
            toolchain="Python 3 standard library",
            deterministic_regeneration_runs_required=2,
        ),
    ]


def qa_records(
    evidence: dict[str, Any],
    segment_records: list[dict[str, Any]],
    surface_records: list[dict[str, Any]],
    correction_bindings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    present_surfaces = [record for record in surface_records if record["presence"] == "present"]
    surface_counts = Counter(record["surface_type"] for record in present_surfaces)
    correction_ids = [binding["record_id"] for binding in correction_bindings]
    specs = [
        (
            "qa.o015.habring-ch01-ch02.source-freeze",
            "source_freeze",
            "pass",
            ["artifact.habring.source-preface", "artifact.habring.source-ch01", "artifact.habring.source-ch02"],
            {
                "source_edition_id": SOURCE_EDITION_ID,
                "source_archive_sha256": "d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748",
                "authority_tex_sha256": {
                    "preface": FROZEN_IDENTITIES["authority/habring/source-v1/preface.tex"][1],
                    "preliminaries": FROZEN_IDENTITIES["authority/habring/source-v1/preliminaries.tex"][1],
                    "convexity": FROZEN_IDENTITIES["authority/habring/source-v1/convexity.tex"][1],
                },
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.segment-binding",
            "stable_id_binding",
            "pass",
            ["artifact.habring.target-ch01", "artifact.habring.target-ch02"],
            {
                "segment_count": len(segment_records),
                "segment_ids": [record["id"] for record in segment_records],
                "source_and_target_slices_hashed": True,
                "hash_normalization": "utf8-lf-final-newline",
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.content-surfaces",
            "structure_and_mathematics",
            "pass",
            ["artifact.habring.target-ch01", "artifact.habring.target-ch02"],
            {
                "present_surface_count": len(present_surfaces),
                "surface_counts": dict(sorted(surface_counts.items())),
                "formal_hint_answer_solution_closures": 6,
                "surface_slices_hashed": True,
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.corrections",
            "correction_integrity",
            "pass",
            [
                "artifact.habring.correction-snapshot-ch01",
                "artifact.habring.correction-snapshot-ch02",
                "artifact.habring.target-ch01",
                "artifact.habring.target-ch02",
            ],
            {
                "source_event_ids": EXPECTED_CORRECTION_IDS,
                "correction_record_ids": correction_ids,
                "ledger_line_bindings_hashed": True,
                "silent_normalization": False,
                "upstream_contact": False,
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.solver",
            "computation",
            "pass",
            ["artifact.habring.solver-results-ch01-ch02", "artifact.habring.solver-validator-ch01-ch02"],
            {
                "gate_count": evidence["solver"]["gate_count"],
                "negative_control_count": evidence["solver"]["negative_control_count"],
                "seed": evidence["solver"]["seed"],
                "numpy": evidence["solver"]["python_stack"]["numpy"],
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.build",
            "build",
            "pass",
            ["artifact.habring.builder-ch01-ch02", "artifact.habring.build-report-ch01-ch02", "artifact.habring.target-pdf-ch01-ch02"],
            {
                "canonical_build_command": "python qa/build_habring_ch01_ch02.py",
                "deterministic_rebuilds": 2,
                "byte_identical": True,
                "pages": evidence["unit"]["artifact"]["pages"],
                "pdf_sha256": evidence["unit"]["artifact"]["sha256"],
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.full-html",
            "html_build",
            "pass",
            ["artifact.habring.full-html-builder", "artifact.habring.full-html-build-report", "artifact.habring.target-html-ch01-ch09"],
            {
                "canonical_build_command": "python qa/build_habring_full_html.py",
                "deterministic_rebuilds": 2,
                "byte_identical": True,
                "lang": "id-ID",
                "embedded_image_count": evidence["html"]["artifact"]["embedded_image_count"],
                "math_inline_count": evidence["html"]["artifact"]["math_inline_count"],
                "math_display_count": evidence["html"]["artifact"]["math_display_count"],
                "html_sha256": evidence["html"]["artifact"]["sha256"],
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.full-reader",
            "composite_reader_build",
            "pass",
            ["artifact.habring.full-reader-builder", "artifact.habring.full-reader-build-report", "artifact.habring.target-pdf-ch01-ch09"],
            {
                "canonical_build_command": "python qa/build_habring_full_reader.py",
                "deterministic_rebuilds": 2,
                "byte_identical": True,
                "pages": evidence["reader"]["artifact"]["pages"],
                "outline_entries": evidence["reader"]["artifact"]["outline_entries"],
                "pdf_sha256": evidence["reader"]["artifact"]["sha256"],
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.full-epub",
            "epub_build",
            "pass",
            [
                "artifact.habring.full-epub-builder",
                "artifact.habring.full-epub-build-report",
                "artifact.habring.target-epub-ch01-ch09",
            ],
            {
                "canonical_build_command": "python qa/build_habring_full_epub.py",
                "deterministic_rebuilds": 2,
                "byte_identical": True,
                "mathml_count": evidence["epub"]["artifact"]["mathml_count"],
                "navigation_link_count": evidence["epub"]["artifact"]["navigation_link_count"],
                "nonempty_image_alt_count": evidence["epub"]["artifact"]["nonempty_image_alt_count"],
                "tikz_figure_fallback_count": evidence["epub"]["artifact"]["tikz_figure_fallback_count"],
                "epub_sha256": evidence["epub"]["artifact"]["sha256"],
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.rights",
            "rights",
            "pass",
            [
                "artifact.habring.source-preface",
                "artifact.habring.source-ch01",
                "artifact.habring.source-ch02",
                "artifact.habring.correction-snapshot-ch01",
                "artifact.habring.correction-snapshot-ch02",
            ],
            {
                "license": "CC BY 4.0",
                "source_author": "Andreas Habring",
                "translation_and_corrections_disclosed": True,
                "non_endorsement": True,
                "inherited_raster_assets": 5,
                "inherited_raster_assets_exact_copy": True,
            },
        ),
        (
            "qa.o015.habring-ch01-ch02.backend-integration",
            "backend_integrity",
            "pass",
            ["artifact.o015.backend-generator-habring-ch01-ch02", "artifact.o015.backend-validator-habring-ch01-ch02"],
            {
                "protected_baseline_record_count": BASELINE_RECORD_COUNT,
                "protected_baseline_jsonl_sha256": BASELINE_JSONL[1],
                "protected_baseline_csv_sha256": BASELINE_CSV[1],
                "raw_record_bytes_and_relative_order_preserved": True,
                "deterministic_regeneration_runs_required": 2,
            },
        ),
    ]
    records: list[dict[str, Any]] = []
    for record_id, event_type, result, witnesses, extra in specs:
        record = common("qa_event", record_id, "passed")
        record.update(
            {
                "event_type": event_type,
                "result": result,
                "affected_unit_ids": [UNITS["ch01"], UNITS["ch02"]],
                "witness_artifact_ids": witnesses,
                **extra,
            }
        )
        records.append(record)
    return records


def relation_records(
    surface_specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs: list[tuple[str, str, str, str, str]] = [
        ("relation.unit.root-contains-ch01", "contains", ROOT_UNIT_ID, UNITS["ch01"], "Source preface and Chapter 1."),
        ("relation.unit.root-contains-ch02", "contains", ROOT_UNIT_ID, UNITS["ch02"], "Source Chapter 2."),
        ("relation.unit.ch01-precedes-ch02", "precedes", UNITS["ch01"], UNITS["ch02"], "Contiguous source order."),
        ("relation.unit.ch02-precedes-ch03", "precedes", UNITS["ch02"], "unit.habring.v1.ch03", "Contiguous source order."),
        ("relation.habring.target-ch01-translates-preface", "translates", "artifact.habring.target-ch01", "artifact.habring.source-preface", "The target includes the translated preface."),
        ("relation.habring.target-ch01-translates-preliminaries", "translates", "artifact.habring.target-ch01", "artifact.habring.source-ch01", "The target includes translated Chapter 1."),
        ("relation.habring.target-ch02-translates-convexity", "translates", "artifact.habring.target-ch02", "artifact.habring.source-ch02", "The target translates Chapter 2."),
        ("relation.habring.unit-pdf-adapts-ch01", "adapts", "artifact.habring.target-pdf-ch01-ch02", "artifact.habring.target-ch01", "Deterministic unit reader."),
        ("relation.habring.unit-pdf-adapts-ch02", "adapts", "artifact.habring.target-pdf-ch01-ch02", "artifact.habring.target-ch02", "Deterministic unit reader."),
        ("relation.habring.full-html-adapts-ch01", "adapts", "artifact.habring.target-html-ch01-ch09", "artifact.habring.target-ch01", "Full responsive reader includes Chapter 1."),
        ("relation.habring.full-html-adapts-ch02", "adapts", "artifact.habring.target-html-ch01-ch09", "artifact.habring.target-ch02", "Full responsive reader includes Chapter 2."),
        ("relation.habring.full-reader-adapts-unit-pdf", "adapts", "artifact.habring.target-pdf-ch01-ch09", "artifact.habring.target-pdf-ch01-ch02", "Full PDF reader begins with this unit."),
        ("relation.habring.full-epub-adapts-ch01", "adapts", "artifact.habring.target-epub-ch01-ch09", "artifact.habring.target-ch01", "Full EPUB reader includes Chapter 1."),
        ("relation.habring.full-epub-adapts-ch02", "adapts", "artifact.habring.target-epub-ch01-ch09", "artifact.habring.target-ch02", "Full EPUB reader includes Chapter 2."),
    ]
    for chapter in ("ch01", "ch02"):
        for segment_id in EXPECTED_SEGMENT_IDS[chapter]:
            specs.append(
                (
                    f"relation.unit.{chapter}-contains-{segment_id.rsplit('.', 1)[1]}",
                    "contains",
                    UNITS[chapter],
                    segment_id,
                    "Ordered stable reader-facing segment.",
                )
            )
    for surface in surface_specs:
        relation_type = "exercises" if surface["surface_type"] == "exercise" else "illustrates"
        suffix = surface["id"].split(f"surface.habring.v1.{surface['chapter']}.", 1)[1]
        specs.append(
            (
                f"relation.surface.{surface['chapter']}-{suffix.replace('.', '-')}-to-segment",
                relation_type,
                surface["id"],
                surface["segment_id"],
                "Exact target TeX surface bound to its stable segment.",
            )
        )

    records: list[dict[str, Any]] = []
    for record_id, relation_type, source_id, target_id, note in specs:
        record = common("relation", record_id, "current")
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
    correction_bindings, corrections = correction_records(segment_specs)

    new_records = (
        unit_records()
        + segments
        + surfaces
        + asset_records()
        + rights_records()
        + corrections
        + artifact_records(evidence)
        + qa_records(evidence, segments, surfaces, correction_bindings)
        + relation_records(surface_specs)
    )
    new_ids = [record["id"] for record in new_records]
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
    if EXPECTED_NEW_RECORD_COUNT and len(new_records) != EXPECTED_NEW_RECORD_COUNT:
        raise ValueError(
            f"new record count {len(new_records)} differs from {EXPECTED_NEW_RECORD_COUNT}"
        )
    if EXPECTED_ENTITY_COUNTS and counts != EXPECTED_ENTITY_COUNTS:
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
                prefix=f".{destination.name}.habring-ch01-ch02-",
                suffix=".stage",
                dir=destination.parent,
                delete=False,
            ) as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append(Path(handle.name))
        if staged[0].read_bytes() != jsonl or staged[1].read_bytes() != csv_data:
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
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--write-canonical", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.output_dir and args.write_canonical:
        parser.error("--output-dir and --write-canonical are mutually exclusive")

    validate_frozen_identities()
    evidence = load_build_evidence()
    baseline, baseline_jsonl, baseline_csv = load_baseline(args.input_jsonl, args.input_csv)
    new_records = generate_records(baseline, evidence)
    all_records = baseline + new_records
    jsonl, csv_data = serialize(all_records)
    assert_baseline_preserved(jsonl, csv_data, baseline_jsonl, baseline_csv)

    if args.preflight:
        mode = "preflight"
        output_jsonl = None
        output_csv = None
    elif args.output_dir:
        mode = "staged"
        output_jsonl = args.output_dir / "records.jsonl"
        output_csv = args.output_dir / "records.csv"
        atomic_write_pair(output_jsonl, output_csv, jsonl, csv_data)
    elif args.write_canonical:
        mode = "canonical"
        output_jsonl = JSONL_PATH
        output_csv = CSV_PATH
        atomic_write_pair(output_jsonl, output_csv, jsonl, csv_data)
    else:
        mode = "dry-run"
        output_jsonl = None
        output_csv = None

    result = {
        "result": "pass",
        "workflow": WORKFLOW,
        "write_mode": mode,
        "protected_baseline_record_count": BASELINE_RECORD_COUNT,
        "protected_baseline_record_bytes_and_order_stable": True,
        "new_record_count": len(new_records),
        "new_entity_counts": dict(
            sorted(Counter(record["entity_type"] for record in new_records).items())
        ),
        "new_id_set_sha256": id_set_sha256(new_records),
        "final_record_count": len(all_records),
        "final_id_set_sha256": id_set_sha256(all_records),
        "final_record_set_sha256": record_set_sha256(all_records),
        "jsonl": {"bytes": len(jsonl), "sha256": sha256(jsonl)},
        "csv": {"bytes": len(csv_data), "sha256": sha256(csv_data)},
        "output_jsonl": str(output_jsonl) if output_jsonl else None,
        "output_csv": str(output_csv) if output_csv else None,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
