#!/usr/bin/env python3
"""Deterministically append the finite Original-01 backend closure.

The protected input is the exact 3,585-record backend through Becker-03.
Every record owned by this workflow uses d90.orig.v1.tr01.*.  A rerun strips
only that namespace/workflow, proves exact recovery of the protected JSONL and
CSV bytes, rediscovers the eight source segments and all requested semantic
surfaces, validates the deterministic lab evidence, and emits a globally
sorted lossless JSONL/CSV projection.

Canonical backend files change only with --write-canonical.
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

RECORDED_AT = "2026-08-25T23:55:00Z"
WORKFLOW = "o015-original-01-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"
BASE = "d90.orig.v1.tr01"

SCHEMA_IDENTITY = (
    3_092,
    "1166cbffe6016044430fe003e4981b1a3a537be7c115f0b646168a1936ab5ad0",
)
BASELINE_RECORD_COUNT = 3_585
BASELINE_JSONL = (
    2_724_813,
    "fd8e7f3a13cbc17784b7f9b6a39f83344124ec381b98a34bf8095935c5c054fb",
)
BASELINE_CSV = (
    3_267_489,
    "56004e9095adc61950b89c9e6f6959e6dc0f33d5211d4b67f4f1277216245c72",
)
BASELINE_ID_SET_SHA256 = "24a32c1bc5c62f22e0f8b7f5c596189b2dad1c0733a161970b7e158e7ab70923"
BASELINE_ID_ORDER_SHA256 = "718098412e56cb591595cc683ed9e6380f67bf441f367b8f6d257d1c2ea76945"
BASELINE_RECORD_SET_SHA256 = "c92934da552517c0780cdc48a66657f560ead0c38e74428db08a95a765cc72be"
BASELINE_LINE_SEQUENCE_SHA256 = "91953bdf4f3f2ec2ce8108cb9a0909fc5f493e664489e26f8c6871ede41113ad"

SOURCE = "source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
WRAPPER = "source/id-ID/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
LAB_CODE = "labs/original-01/stochastic-composite-lab.py"
LAB_JSON = "labs/original-01/results.json"
LAB_CSV = "labs/original-01/results.csv"
LAB_SVG = "labs/original-01/objective-gap.svg"
GENERATOR = "qa/extend_backend_original_01.py"
VALIDATOR = "qa/validate_backend_original_01.py"

FROZEN_IDENTITIES = {
    SOURCE: (27_431, "db677ca6bab274a5db3e356fc996cef3bb00fb67770a90984460aa265fabcf26"),
    WRAPPER: (5_311, "d632765baf270a7a7c1b39f051d83c1d76dd3ccc04457fb1b4b92088ffdd9322"),
    LAB_CODE: (13_655, "21a0df89524b34916d1f659636bf8f92a5730efb7e263e0fbd7393e6f2c936fd"),
    LAB_JSON: (2_432, "86ff701a51d091ee74c110917cb1888c6e7448489207e6ee1372753bd1e4c447"),
    LAB_CSV: (4_189, "61a6591ad7d1b41230a086482314448871f3697954d4c84133a7a5f4f775d37c"),
    LAB_SVG: (86_616, "87c772d901ee734356981ee35f19fc3c3ae47fea6f11528edbee6d015a3f2830"),
}

RESOURCE_ID = f"{BASE}.resource"
EDITION_ID = f"{BASE}.edition.id-id"
UNIT_ID = f"{BASE}.unit"
CONTENT_RIGHTS_ID = f"{BASE}.rights.content.cc-by-sa-4-0"
SCAFFOLD_RIGHTS_ID = f"{BASE}.rights.wrapper-mixed"
TOOLING_RIGHTS_ID = f"{BASE}.rights.tooling"

ARTIFACT_SUFFIX_PATHS = {
    "source-body": SOURCE,
    "source-wrapper": WRAPPER,
    "lab-code": LAB_CODE,
    "lab-results-json": LAB_JSON,
    "lab-results-csv": LAB_CSV,
    "lab-results-svg": LAB_SVG,
    "backend-generator": GENERATOR,
    "backend-validator": VALIDATOR,
}

SEGMENT_SPECS = [
    {
        "number": 1,
        "marker": "% OR01-S001 | lapisan asli: tujuan, batas, dan notasi",
        "topic": "stochastic-composite-model",
        "label": "Tujuan, batas, notasi, dan model komposit stokastik",
    },
    {
        "number": 2,
        "marker": "% OR01-S002 | lapisan asli: gradien proksimal stokastik",
        "topic": "stochastic-proximal-gradient",
        "label": "Gradien proksimal stokastik dan batas ergodik",
    },
    {
        "number": 3,
        "marker": "% OR01-S003 | lapisan asli: minibatch",
        "topic": "minibatch-variance",
        "label": "Identitas varians minibatch dan biaya oracle",
    },
    {
        "number": 4,
        "marker": "% OR01-S004 | lapisan asli: geometri cermin",
        "topic": "stochastic-mirror-descent",
        "label": "Penurunan cermin stokastik dan geometri Bregman",
    },
    {
        "number": 5,
        "marker": "% OR01-S005 | lapisan asli: penghubung reduksi varians",
        "topic": "proximal-saga-bridge",
        "label": "Penghubung reduksi varians Prox-SAGA",
    },
    {
        "number": 6,
        "marker": "% OR01-S006 | lapisan asli: laboratorium",
        "topic": "reproducible-stochastic-lab",
        "label": "Laboratorium komputasi stokastik yang dapat direproduksi",
    },
    {
        "number": 7,
        "marker": "% OR01-S007 | lapisan asli: latihan, petunjuk, solusi",
        "topic": "worked-stochastic-composite-exercises",
        "label": "Latihan, petunjuk bertahap, dan solusi lengkap",
    },
    {
        "number": 8,
        "marker": "% OR01-S008 | lapisan asli: peta asumsi dan rujukan",
        "topic": "assumption-and-provenance-map",
        "label": "Peta asumsi, batas klaim, dan provenans",
    },
]

TOPIC_SPECS = [
    ("stochastic-composite-model", "stochastic composite optimization model and oracle", "model komposit dan oracle stokastik", (), 1),
    ("stochastic-proximal-gradient", "stochastic proximal-gradient method and ergodic bound", "metode gradien proksimal stokastik dan batas ergodik", ("stochastic-composite-model",), 2),
    ("minibatch-variance", "minibatch variance identities and oracle accounting", "identitas varians minibatch dan penghitungan oracle", ("stochastic-proximal-gradient",), 3),
    ("stochastic-mirror-descent", "stochastic mirror descent in Bregman geometry", "penurunan cermin stokastik dalam geometri Bregman", ("stochastic-composite-model",), 4),
    ("proximal-saga-bridge", "variance-reduced proximal SAGA bridge", "penghubung Prox-SAGA dengan reduksi varians", ("stochastic-proximal-gradient", "minibatch-variance"), 5),
    ("reproducible-stochastic-lab", "reproducible fixed-oracle-budget stochastic optimization lab", "laboratorium stokastik dengan anggaran oracle tetap", ("stochastic-proximal-gradient", "minibatch-variance", "proximal-saga-bridge"), 6),
    ("worked-stochastic-composite-exercises", "worked stochastic composite optimization exercises", "latihan optimisasi komposit stokastik dengan solusi", ("stochastic-proximal-gradient", "stochastic-mirror-descent", "proximal-saga-bridge"), 7),
    ("assumption-and-provenance-map", "assumption boundaries and mathematical provenance", "batas asumsi dan provenans matematis", (), 8),
]

ENVIRONMENT_SURFACE = {
    "lemma": "lemma",
    "theorem": "theorem",
    "prop": "proposition",
    "proposition": "proposition",
    "cor": "corollary",
    "corollary": "corollary",
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
        "section": 9,
        "subsection": 1,
        "definition": 3,
        "algorithm": 2,
        "lemma": 2,
        "theorem": 2,
        "proposition": 2,
        "corollary": 1,
        "proof": 7,
        "equation": 40,
        "exercise": 6,
        "hint": 6,
        "solution": 6,
        "lab": 1,
    }
)
DEFINITION_SPECS = (
    (20, 24, "Norma dual"),
    (167, 173, "Penaksir minibatch"),
    (243, 247, "Divergensi Bregman"),
)
QA_SUFFIXES = {
    "source-freeze",
    "segment-binding",
    "semantic-surfaces",
    "lab-results",
    "rights-provenance",
    "backend-integration",
}

TOKEN = re.compile(r"\\(?P<kind>begin|end)\{(?P<env>[^}]+)\}")
HEADING = re.compile(r"^\\(?P<kind>chapter|section|subsection)\*?\{(?P<title>.+)\}$")
TEXT_SURFACE = re.compile(r"^\\textbf\{(?P<label>Petunjuk bertahap|Solusi lengkap)\.\}")


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"required Original-01 artifact is missing: {relative}")
    raw = path.read_bytes()
    if not raw:
        raise ValueError(f"required Original-01 artifact is empty: {relative}")
    return len(raw), sha256(raw)


def normalized_slice(relative: str, start: int, end: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid normalized slice {relative}:{start}-{end}")
    raw = ("\n".join(lines[start - 1 : end]) + "\n").encode("utf-8")
    return len(raw), sha256(raw)


def id_set_sha256(records: list[dict[str, Any]]) -> str:
    return sha256(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def id_order_sha256(records: list[dict[str, Any]]) -> str:
    return sha256(("\n".join(record["id"] for record in records) + "\n").encode("utf-8"))


def record_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "\n".join(canonical_json(record) for record in sorted(records, key=lambda item: item["id"])) + "\n"
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
        raise ValueError("workflow-stripped JSONL differs from the protected 3,585-record backend")
    if (len(baseline_csv), sha256(baseline_csv)) != BASELINE_CSV:
        raise ValueError("workflow-stripped CSV differs from the protected 3,585-record backend")
    if line_sequence_sha256(baseline_jsonl) != BASELINE_LINE_SEQUENCE_SHA256:
        raise ValueError("protected JSONL line-byte sequence differs")
    if (
        len(baseline) != BASELINE_RECORD_COUNT
        or id_set_sha256(baseline) != BASELINE_ID_SET_SHA256
        or id_order_sha256(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set_sha256(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("protected baseline record set/order differs")
    return baseline, baseline_jsonl, baseline_csv


def validate_source_and_lab() -> dict[str, Any]:
    for relative, expected in FROZEN_IDENTITIES.items():
        if file_info(relative) != expected:
            raise ValueError(f"frozen Original-01 identity differs: {relative}")

    lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    if len(lines) != 700:
        raise ValueError("Original-01 source line count differs")
    if not any(line.strip() == r"\item jalankan skrip tanpa mengubah benih acak dan verifikasikan konfigurasi" for line in lines):
        raise ValueError("live configuration-verification wording differs at source line 434")
    if "hash konfigurasi" in "\n".join(lines):
        raise ValueError("superseded configuration-hash wording remains in the live source")

    wrapper = (ROOT / WRAPPER).read_text(encoding="utf-8")
    identity_wrapper_markers = (
        f"% unit-id: {UNIT_ID}",
        "% target-edition-id: d90.orig.v1.tr01.edition.id-ID",
        "% authorship: independent coursebook completion layer",
        r"\input{original-01-metode-stokastik-komposit-cermin-minibatch-id}",
    )
    evidence_wrapper_markers = (
        "Creative Commons Attribution-ShareAlike 4.0 International",
        "Creative Commons Attribution 4.0 International",
        r"\texttt{shinybook.cls}",
        r"\texttt{macros-id.tex}",
        "Christian Clason",
        "OpenAI Codex gpt-5.6-sol, Ultra",
    )
    if any(wrapper.count(marker) != 1 for marker in identity_wrapper_markers) or any(marker not in wrapper for marker in evidence_wrapper_markers):
        raise ValueError("Original-01 wrapper identity, rights, or provenance marker differs")

    payload = json.loads((ROOT / LAB_JSON).read_text(encoding="utf-8"))
    expected_configuration = {
        "component_gradient_budget": 3840,
        "dimension": 40,
        "epochs": 12,
        "l1_regularization": 0.03,
        "minibatch_size": 16,
        "noise_standard_deviation": 0.08,
        "samples": 320,
        "sampling": "with replacement for SGD/minibatch/SAGA index draws",
        "seed": 20260825,
        "true_nonzero_coordinates": 8,
    }
    if (
        payload.get("schema") != "o015-original-01-stochastic-composite-lab-v1"
        or payload.get("result") != "pass"
        or payload.get("configuration") != expected_configuration
        or payload.get("row_count") != 38
        or payload.get("network_access") is not False
        or payload.get("upstream_contact") is not False
    ):
        raise ValueError("Original-01 lab JSON closure differs")
    for key, path in (("csv", LAB_CSV), ("svg", LAB_SVG)):
        node = payload.get(key, {})
        if node.get("path") != Path(path).name or (node.get("bytes"), node.get("sha256")) != file_info(path):
            raise ValueError(f"Original-01 lab JSON does not bind {path}")
    if payload.get("svg", {}).get("redundant_with_accessible_tables") is not True:
        raise ValueError("Original-01 SVG accessibility redundancy marker differs")

    csv_rows = list(csv.DictReader(io.StringIO((ROOT / LAB_CSV).read_text(encoding="utf-8"))))
    expected_columns = [
        "method",
        "component_gradient_evaluations",
        "epochs",
        "objective",
        "objective_gap",
        "prox_gradient_mapping_norm",
        "nonzero_coordinates",
        "direction_variance_trace",
    ]
    if not csv_rows or list(csv_rows[0]) != expected_columns or len(csv_rows) != 38:
        raise ValueError("Original-01 lab CSV shape differs")
    counts = Counter(row["method"] for row in csv_rows)
    if counts != Counter({"prox_sgd_b1": 13, "prox_minibatch_b16": 13, "prox_saga": 12}):
        raise ValueError("Original-01 lab CSV method census differs")
    for method, final in payload["final_rows"].items():
        candidates = [row for row in csv_rows if row["method"] == method]
        terminal = max(candidates, key=lambda row: int(row["component_gradient_evaluations"]))
        if int(terminal["component_gradient_evaluations"]) != 3840:
            raise ValueError(f"terminal oracle budget differs for {method}")
        for key in ("objective", "objective_gap", "prox_gradient_mapping_norm", "direction_variance_trace"):
            if float(terminal[key]) != final[key]:
                raise ValueError(f"lab terminal {key} differs for {method}")
        if int(terminal["nonzero_coordinates"]) != final["nonzero_coordinates"]:
            raise ValueError(f"lab terminal sparsity differs for {method}")

    svg = (ROOT / LAB_SVG).read_text(encoding="utf-8")
    if "Kesenjangan objektif terhadap evaluasi gradien komponen" not in svg or "Grafik redundan" not in svg:
        raise ValueError("Original-01 SVG title/description differs")
    return {"lab": payload, "lab_rows": csv_rows}


def parse_segments() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    marker_map = {spec["marker"]: spec for spec in SEGMENT_SPECS}
    markers = [(number, marker_map[line]) for number, line in enumerate(lines, 1) if line in marker_map]
    if [spec["number"] for _, spec in markers] != list(range(1, 9)):
        raise ValueError("Original-01 eight-marker closure differs")
    parsed: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for index, (start, spec) in enumerate(markers):
        segment_id = f"{BASE}.seg{spec['number']:04d}"
        if start >= len(lines) or lines[start] != f"% segment-id: {segment_id}":
            raise ValueError(f"stable segment ID missing after {SOURCE}:{start}")
        end = markers[index + 1][0] - 1 if index + 1 < len(markers) else len(lines)
        content_bytes, content_digest = normalized_slice(SOURCE, start, end)
        item = {**spec, "id": segment_id, "start": start, "end": end}
        parsed.append(item)
        record = common("segment", segment_id, "current")
        record.update(
            {
                "unit_id": UNIT_ID,
                "order": spec["number"],
                "source_local_id": f"original-01-segment-{spec['number']:04d}",
                "source_local_label": spec["label"],
                "target_local_label": spec["label"],
                "source_edition_id": EDITION_ID,
                "target_edition_id": EDITION_ID,
                "source_language": "id",
                "target_language": "id",
                "target_locale": "id-ID",
                "source_path": SOURCE,
                "source_line_start": start,
                "source_line_end": end,
                "source_locator": f"{SOURCE}:{start}-{end}",
                "source_content_bytes": content_bytes,
                "source_content_sha256": content_digest,
                "target_path": SOURCE,
                "target_line_start": start,
                "target_line_end": end,
                "target_locator": f"{SOURCE}:{start}-{end}",
                "target_content_bytes": content_bytes,
                "target_content_sha256": content_digest,
                "hash_normalization": "utf8-lf-final-newline",
                "translation_state": "built",
                "content_origin": "independently_authored_original_id-ID",
                "concept_ids": [f"{BASE}.topic.{spec['topic']}"],
                "rights_id": CONTENT_RIGHTS_ID,
            }
        )
        records.append(record)
    return parsed, records


def strip_tex_comment(line: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", line)


def segment_for_line(segments: list[dict[str, Any]], line_number: int) -> dict[str, Any]:
    matches = [segment for segment in segments if segment["start"] <= line_number <= segment["end"]]
    if len(matches) != 1:
        raise ValueError(f"source line {line_number} belongs to {len(matches)} Original-01 segments")
    return matches[0]


def discover_present_surfaces(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    found: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    exercise_blocks: list[tuple[int, int]] = []

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
        for match in TOKEN.finditer(line):
            environment = match.group("env")
            if match.group("kind") == "begin":
                stack.append((environment, line_number))
                continue
            if not stack or stack[-1][0] != environment:
                raise ValueError(f"unbalanced {environment} at {SOURCE}:{line_number}")
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
                if opened == "exercise":
                    exercise_blocks.append((start, line_number))
            if opened == "quote":
                content = "\n".join(lines[start - 1 : line_number])
                if re.search(r"\\textbf\{Algoritma [12]:", content):
                    found.append(
                        {
                            "surface_type": "algorithm",
                            "environment": "quote-algorithm",
                            "start": start,
                            "end": line_number,
                        }
                    )
    if stack:
        raise ValueError(f"unclosed TeX environment in {SOURCE}: {stack[-1]}")

    for start, end, title in DEFINITION_SPECS:
        content = "\n".join(lines[start - 1 : end])
        if title.casefold().split()[0] not in content.casefold():
            raise ValueError(f"definition anchor differs at {SOURCE}:{start}-{end}")
        found.append(
            {
                "surface_type": "definition",
                "environment": "prose-definition",
                "start": start,
                "end": end,
                "title": title,
            }
        )

    for exercise_start, exercise_end in sorted(exercise_blocks):
        markers: list[tuple[int, str]] = []
        for number in range(exercise_start, exercise_end + 1):
            match = TEXT_SURFACE.match(strip_tex_comment(lines[number - 1]).strip())
            if match:
                markers.append((number, "hint" if match.group("label") == "Petunjuk bertahap" else "solution"))
        if [kind for _, kind in markers] != ["hint", "solution"]:
            raise ValueError(f"exercise at line {exercise_start} lacks one hint and one complete solution")
        hint_start, _ = markers[0]
        solution_start, _ = markers[1]
        hint_end = solution_start - 1
        while hint_end > hint_start and not lines[hint_end - 1].strip():
            hint_end -= 1
        found.append({"surface_type": "hint", "environment": "latex-bold-heading", "start": hint_start, "end": hint_end})
        found.append({"surface_type": "solution", "environment": "latex-bold-heading", "start": solution_start, "end": exercise_end})

    lab_segment = segments[5]
    lab_start = lab_segment["start"] + 2
    lab_end = lab_segment["end"]
    while lab_end > lab_start and not lines[lab_end - 1].strip():
        lab_end -= 1
    if not lines[lab_start - 1].startswith(r"\section{Laboratorium 1") or "Identitas lengkap dicatat" not in lines[lab_end - 1]:
        raise ValueError("Original-01 lab surface boundaries differ")
    found.append({"surface_type": "lab", "environment": "coursebook-lab", "start": lab_start, "end": lab_end, "title": "Laboratorium 1"})

    counts = Counter(item["surface_type"] for item in found)
    if counts != EXPECTED_PRESENT_SURFACE_COUNTS:
        raise ValueError(f"Original-01 semantic surface topology differs: {dict(counts)}")

    counters: Counter[str] = Counter()
    result: list[dict[str, Any]] = []
    for item in sorted(found, key=lambda value: (value["start"], value["end"], value["surface_type"], value["environment"])):
        counters[item["surface_type"]] += 1
        segment = segment_for_line(segments, item["start"])
        result.append(
            {
                **item,
                "id": f"{BASE}.{item['surface_type']}.{counters[item['surface_type']]:04d}",
                "segment_id": segment["id"],
                "topic_id": f"{BASE}.topic.{segment['topic']}",
            }
        )
    return result


def surface_records(segments: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    specs = discover_present_surfaces(segments)
    records: list[dict[str, Any]] = []
    for item in specs:
        content_bytes, content_digest = normalized_slice(SOURCE, item["start"], item["end"])
        content = "\n".join(lines[item["start"] - 1 : item["end"]])
        record = common("learning_surface", item["id"], "current")
        record.update(
            {
                "unit_id": UNIT_ID,
                "surface_type": item["surface_type"],
                "presence": "present",
                "count": 1,
                "latex_environment": item["environment"],
                "target_edition_id": EDITION_ID,
                "target_path": SOURCE,
                "target_line_start": item["start"],
                "target_line_end": item["end"],
                "target_content_bytes": content_bytes,
                "target_content_sha256": content_digest,
                "hash_normalization": "utf8-lf-final-newline",
                "related_segment_ids": [item["segment_id"]],
                "concept_ids": [item["topic_id"]],
                "latex_labels": re.findall(r"\\label\{([^}]+)\}", content),
                "rights_id": CONTENT_RIGHTS_ID,
            }
        )
        if "title" in item:
            record["surface_label"] = item["title"]
        if item["surface_type"] == "lab":
            record["input_artifact_ids"] = [f"{BASE}.artifact.lab-code"]
            record["evidence_artifact_id"] = f"{BASE}.artifact.lab-results-json"
            record["accessible_result_artifact_ids"] = [
                f"{BASE}.artifact.lab-results-json",
                f"{BASE}.artifact.lab-results-csv",
            ]
        records.append(record)
    return specs, records


def architecture_records() -> list[dict[str, Any]]:
    resource = common("resource", RESOURCE_ID, "source_admitted")
    resource.update(
        {
            "title": "Metode Stokastik Komposit, Cermin, dan Minibatch",
            "creator": "Independent Indonesian coursebook completion layer",
            "official_record": SOURCE,
            "rights_id": CONTENT_RIGHTS_ID,
            "language": "id",
            "locale": "id-ID",
            "content_origin": "independently authored original coursebook completion layer",
            "mathematical_witnesses_only": True,
            "non_endorsement": True,
        }
    )
    edition = common("edition", EDITION_ID, "built")
    edition.update(
        {
            "edition_kind": "independent_original_coursebook_module",
            "resource_id": RESOURCE_ID,
            "rights_id": CONTENT_RIGHTS_ID,
            "version": "original-01-id-ID-v1",
            "language": "id",
            "locale": "id-ID",
            "translation_state": "built",
            "source_artifact_id": f"{BASE}.artifact.source-body",
            "declared_wrapper_edition_id": "d90.orig.v1.tr01.edition.id-ID",
            "publication_state": "local_validated_unit",
        }
    )
    unit = common("unit", UNIT_ID, "built")
    unit.update(
        {
            "edition_id": EDITION_ID,
            "target_edition_id": EDITION_ID,
            "course_id": "course.d90.advanced-optimization-convex-analysis",
            "unit_kind": "finite_original_closure_tranche",
            "order": 4,
            "source_local_label": "Original-01 stochastic composite, mirror, and minibatch tranche",
            "target_local_label": "Metode Stokastik Komposit, Cermin, dan Minibatch",
            "source_locator": f"{SOURCE}:1-700",
            "target_locator": f"{SOURCE}:1-700",
            "translation_state": "built",
            "rights_id": CONTENT_RIGHTS_ID,
            "curriculum_role": "finite original closure after the three admitted Becker modules",
            "assessment_material": "six exercises with paired staged hints and complete solutions",
            "lab_material": "deterministic open-computation lab with accessible JSON and CSV results",
        }
    )
    return [resource, edition, unit]


def topic_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for slug, canonical_label, target_label, prerequisites, segment_number in TOPIC_SPECS:
        record = common("concept", f"{BASE}.topic.{slug}", "current")
        record.update(
            {
                "canonical_label": canonical_label,
                "target_label_id_id": target_label,
                "domain": "stochastic composite convex optimization",
                "prerequisite_ids": [f"{BASE}.topic.{item}" for item in prerequisites],
                "related_segment_ids": [f"{BASE}.seg{segment_number:04d}"],
                "source_edition_id": EDITION_ID,
                "target_edition_id": EDITION_ID,
                "rights_id": CONTENT_RIGHTS_ID,
            }
        )
        records.append(record)
    return records


def rights_records() -> list[dict[str, Any]]:
    content = common("rights", CONTENT_RIGHTS_ID, "admitted")
    content.update(
        {
            "component_id": "d90.orig.v1.tr01.content-and-lab",
            "path": f"{SOURCE} + labs/original-01",
            "rights_expression": "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
            "authority_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "content_origin": "independent original writing and code; cited works are mathematical witnesses only",
            "required_handling": ["attribute the independent completion layer", "preserve ShareAlike", "preserve mathematical citations", "state non-endorsement"],
        }
    )
    scaffold = common("rights", SCAFFOLD_RIGHTS_ID, "admitted")
    scaffold.update(
        {
            "component_id": "d90.orig.v1.tr01.wrapper-and-reader-scaffold",
            "path": f"{WRAPPER} + source/id-ID/shinybook.cls + source/id-ID/macros-id.tex",
            "rights_expression": "mixed rights: new wrapper wording CC BY-SA 4.0; exact Habring-bundled shinybook.cls and adapted Habring macros-id.tex CC BY 4.0",
            "authority_url": "https://arxiv.org/abs/2607.11664",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "content_origin": "lane-authored wrapper around separately governed Habring production components",
            "required_handling": [
                "limit CC BY-SA to new wrapper wording",
                "preserve Habring attribution and CC BY 4.0",
                "identify macros-id.tex as an adaptation",
                "preserve Christian Clason template credit",
                "state non-endorsement",
            ],
        }
    )
    tooling = common("rights", TOOLING_RIGHTS_ID, "admitted")
    tooling.update(
        {
            "component_id": "d90.orig.v1.tr01.backend-tooling",
            "path": f"{GENERATOR} + {VALIDATOR}",
            "rights_expression": "project-local deterministic backend validation tooling",
            "authority_url": GENERATOR,
            "required_handling": ["keep source with generated records", "preserve deterministic validation evidence"],
        }
    )
    return [content, scaffold, tooling]


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
    lab = evidence["lab"]
    return [
        artifact_record("source-body", "original_tex_body", SOURCE, CONTENT_RIGHTS_ID, language="id-ID", physical_lines=700),
        artifact_record("source-wrapper", "reader_tex_wrapper_and_provenance_notice", WRAPPER, SCAFFOLD_RIGHTS_ID, language="id-ID"),
        artifact_record("lab-code", "open_computation_lab_source", LAB_CODE, CONTENT_RIGHTS_ID, network_access=False, random_seed=20260825),
        artifact_record("lab-results-json", "accessible_computation_result_json", LAB_JSON, CONTENT_RIGHTS_ID, row_count=lab["row_count"]),
        artifact_record("lab-results-csv", "accessible_computation_result_csv", LAB_CSV, CONTENT_RIGHTS_ID, row_count=lab["row_count"]),
        artifact_record("lab-results-svg", "redundant_computation_plot_svg", LAB_SVG, CONTENT_RIGHTS_ID, redundant_with_accessible_tables=True),
        artifact_record("backend-generator", "backend_generator", GENERATOR, TOOLING_RIGHTS_ID),
        artifact_record("backend-validator", "backend_validator", VALIDATOR, TOOLING_RIGHTS_ID),
    ]


def qa_records(segments: list[dict[str, Any]], surfaces: list[dict[str, Any]], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    counts = Counter(record["surface_type"] for record in surfaces)
    specs = [
        (
            "source-freeze",
            "source_freeze",
            [f"{BASE}.artifact.source-body", f"{BASE}.artifact.source-wrapper"],
            {"source_bytes": FROZEN_IDENTITIES[SOURCE][0], "source_sha256": FROZEN_IDENTITIES[SOURCE][1], "live_wording_repair_bound": True},
        ),
        (
            "segment-binding",
            "stable_id_binding",
            [f"{BASE}.artifact.source-body"],
            {"segment_count": len(segments), "segment_ids": [record["id"] for record in segments], "source_and_target_slices_hashed": True},
        ),
        (
            "semantic-surfaces",
            "structure_and_mathematics",
            [f"{BASE}.artifact.source-body"],
            {"present_surface_count": len(surfaces), "surface_counts": dict(sorted(counts.items())), "exercise_hint_solution_sets": 6},
        ),
        (
            "lab-results",
            "open_computation",
            [f"{BASE}.artifact.lab-code", f"{BASE}.artifact.lab-results-json", f"{BASE}.artifact.lab-results-csv", f"{BASE}.artifact.lab-results-svg"],
            {"result": "pass", "row_count": evidence["lab"]["row_count"], "component_gradient_budget": 3840, "method_count": 3, "network_access": False},
        ),
        (
            "rights-provenance",
            "rights_and_provenance",
            [f"{BASE}.artifact.source-wrapper", f"{BASE}.artifact.source-body", f"{BASE}.artifact.lab-code"],
            {"rights_expression": "new Original-01 content CC BY-SA 4.0; Habring class and adapted macros CC BY 4.0", "independent_authorship_declared": True, "mathematical_witnesses_only": True, "inherited_scaffold_attributed": True, "christian_clason_template_credit_preserved": True, "non_endorsement": True, "production_provenance_declared": True},
        ),
        (
            "backend-integration",
            "backend_integrity",
            [f"{BASE}.artifact.backend-generator", f"{BASE}.artifact.backend-validator"],
            {"protected_baseline_record_count": BASELINE_RECORD_COUNT, "protected_baseline_jsonl_sha256": BASELINE_JSONL[1], "protected_baseline_csv_sha256": BASELINE_CSV[1], "raw_record_bytes_and_relative_order_preserved": True, "new_id_namespace": f"{BASE}.*", "collision_count": 0, "deterministic_regeneration_runs_required": 2},
        ),
    ]
    records: list[dict[str, Any]] = []
    for suffix, event_type, witnesses, extra in specs:
        record = common("qa_event", f"{BASE}.qa.{suffix}", "passed")
        record.update({"event_type": event_type, "result": "pass", "affected_unit_ids": [UNIT_ID], "witness_artifact_ids": witnesses, **extra})
        records.append(record)
    return records


def relation_specs(segments: list[dict[str, Any]], surface_specs: list[dict[str, Any]]) -> list[tuple[str, str, str, str, str]]:
    specs: list[tuple[str, str, str, str, str]] = [
        ("course-contains-unit", "contains", "course.d90.advanced-optimization-convex-analysis", UNIT_ID, "Course contains finite Original-01 closure tranche."),
        ("becker-b03-precedes-original-01", "precedes", "d90.becker.98ed693.b03.unit", UNIT_ID, "The admitted Becker variance-reduction module precedes this original connective tranche."),
        ("resource-contains-edition", "contains", RESOURCE_ID, EDITION_ID, "Original Indonesian edition."),
        ("edition-contains-unit", "contains", EDITION_ID, UNIT_ID, "Finite original closure unit."),
        ("source-wrapper-adapts-source-body", "adapts", f"{BASE}.artifact.source-wrapper", f"{BASE}.artifact.source-body", "Standalone reader wrapper and provenance notice."),
        ("lab-code-illustrates-lab", "illustrates", f"{BASE}.artifact.lab-code", f"{BASE}.lab.0001", "Executable lab implementation."),
        ("lab-results-json-illustrates-lab", "illustrates", f"{BASE}.artifact.lab-results-json", f"{BASE}.lab.0001", "Accessible structured result."),
        ("lab-results-csv-illustrates-lab", "illustrates", f"{BASE}.artifact.lab-results-csv", f"{BASE}.lab.0001", "Accessible tabular result."),
        ("lab-results-svg-illustrates-lab", "illustrates", f"{BASE}.artifact.lab-results-svg", f"{BASE}.lab.0001", "Redundant visual result."),
    ]
    for segment in segments:
        specs.append((f"unit-contains-seg{segment['number']:04d}", "contains", UNIT_ID, segment["id"], "Ordered original segment."))
    for slug, _, _, prerequisites, _ in TOPIC_SPECS:
        topic_id = f"{BASE}.topic.{slug}"
        specs.append((f"unit-contains-topic-{slug}", "contains", UNIT_ID, topic_id, "Locale-neutral mathematical concept."))
        for prerequisite in prerequisites:
            specs.append((f"topic-{slug}-prerequisite-{prerequisite}", "prerequisite", topic_id, f"{BASE}.topic.{prerequisite}", "Declared concept prerequisite."))
    for surface in surface_specs:
        suffix = surface["id"].removeprefix(f"{BASE}.").replace(".", "-")
        specs.append((f"unit-contains-{suffix}", "contains", UNIT_ID, surface["id"], "Bound source learning surface."))
        relation_type = "defines" if surface["surface_type"] == "definition" else "exercises" if surface["surface_type"] in {"exercise", "hint", "solution"} else "illustrates"
        specs.append((f"{suffix}-to-topic", relation_type, surface["id"], surface["topic_id"], "Surface bound to its primary concept."))

    present_ids = {surface["id"] for surface in surface_specs}
    for number in range(1, 7):
        exercise_id = f"{BASE}.exercise.{number:04d}"
        hint_id = f"{BASE}.hint.{number:04d}"
        solution_id = f"{BASE}.solution.{number:04d}"
        if not {exercise_id, hint_id, solution_id} <= present_ids:
            raise ValueError(f"missing exercise/hint/solution set {number}")
        specs.append((f"hint-{number:04d}-depends-on-exercise-{number:04d}", "depends-on", hint_id, exercise_id, "Paired staged hint."))
        specs.append((f"solution-{number:04d}-depends-on-exercise-{number:04d}", "depends-on", solution_id, exercise_id, "Paired complete solution."))

    proof_targets = (
        f"{BASE}.lemma.0001",
        f"{BASE}.theorem.0001",
        f"{BASE}.proposition.0001",
        f"{BASE}.proposition.0002",
        f"{BASE}.lemma.0002",
        f"{BASE}.theorem.0002",
        f"{BASE}.corollary.0001",
    )
    for number, target in enumerate(proof_targets, 1):
        proof_id = f"{BASE}.proof.{number:04d}"
        if proof_id not in present_ids or target not in present_ids:
            raise ValueError(f"missing proof pairing {number}")
        specs.append((f"proof-{number:04d}-proves-{target.rsplit('.', 2)[-2]}-{target.rsplit('.', 1)[-1]}", "proves", proof_id, target, "Explicit proof-to-statement pairing."))
    return specs


def relation_records(segments: list[dict[str, Any]], surface_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for suffix, relation_type, source_id, target_id, note in relation_specs(segments, surface_specs):
        record = common("relation", f"{BASE}.relation.{suffix}", "current")
        record.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        records.append(record)
    return records


def generate_records(baseline: list[dict[str, Any]], evidence: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, Any]]:
    segment_specs, segments = parse_segments()
    surface_specs, surfaces = surface_records(segment_specs)
    relations = relation_records(segment_specs, surface_specs)
    new_records = architecture_records() + topic_records() + segments + surfaces + rights_records() + artifact_records(evidence) + qa_records(segments, surfaces, evidence) + relations

    baseline_ids = {record["id"] for record in baseline}
    new_ids = [record["id"] for record in new_records]
    if any(not record_id.startswith(f"{BASE}.") for record_id in new_ids):
        raise ValueError("generated ID escaped the Original-01 namespace")
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
        for field in schema["reference_fields"]:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")

    expected_counts = Counter(
        {
            "resource": 1,
            "edition": 1,
            "unit": 1,
            "concept": len(TOPIC_SPECS),
            "segment": len(SEGMENT_SPECS),
            "learning_surface": sum(EXPECTED_PRESENT_SURFACE_COUNTS.values()),
            "rights": 3,
            "artifact": len(ARTIFACT_SUFFIX_PATHS),
            "qa_event": len(QA_SUFFIXES),
            "relation": len(relations),
        }
    )
    if Counter(record["entity_type"] for record in new_records) != expected_counts:
        raise ValueError("Original-01 generated entity topology differs")
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
        raise ValueError("generated JSONL changes protected record bytes or relative order")
    if strip_workflow_csv(output_csv) != baseline_csv:
        raise ValueError("generated CSV changes protected row bytes or relative order")


def atomic_write_pair(output_jsonl: Path, output_csv: Path, jsonl: bytes, csv_data: bytes) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    try:
        for destination, data in ((output_jsonl, jsonl), (output_csv, csv_data)):
            with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{destination.name}.original-01-", suffix=".stage", dir=destination.parent, delete=False) as handle:
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


def make_result(
    mode: str,
    new_records: list[dict[str, Any]],
    all_records: list[dict[str, Any]],
    jsonl: bytes,
    csv_data: bytes,
    schema: dict[str, Any],
    output_jsonl: Path | None,
    output_csv: Path | None,
) -> dict[str, Any]:
    ordered_all = ordered_records(all_records, schema)
    ordered_new = ordered_records(new_records, schema)
    surface_counts = Counter(record["surface_type"] for record in new_records if record["entity_type"] == "learning_surface")
    return {
        "schema": "o015-original-01-backend-extension-v1",
        "result": "pass",
        "workflow": WORKFLOW,
        "write_mode": mode,
        "namespace": f"{BASE}.*",
        "collision_count": 0,
        "schema_identity": {"bytes": SCHEMA_IDENTITY[0], "sha256": SCHEMA_IDENTITY[1], "schema_changed": False},
        "protected_baseline": {
            "record_count": BASELINE_RECORD_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1], "line_sequence_sha256": BASELINE_LINE_SEQUENCE_SHA256},
            "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "id_order_sha256": BASELINE_ID_ORDER_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "raw_record_bytes_and_relative_order_preserved": True,
        },
        "admission": {
            "new_records": len(new_records),
            "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
            "new_id_set_sha256": id_set_sha256(new_records),
            "new_id_order_sha256": id_order_sha256(ordered_new),
            "new_record_set_sha256": record_set_sha256(new_records),
            "final_records": len(all_records),
            "final_id_set_sha256": id_set_sha256(all_records),
            "final_id_order_sha256": id_order_sha256(ordered_all),
            "final_record_set_sha256": record_set_sha256(all_records),
            "final_line_sequence_sha256": line_sequence_sha256(jsonl),
            "jsonl": {"bytes": len(jsonl), "sha256": sha256(jsonl)},
            "csv": {"bytes": len(csv_data), "sha256": sha256(csv_data)},
        },
        "source": {"path": SOURCE, "bytes": FROZEN_IDENTITIES[SOURCE][0], "sha256": FROZEN_IDENTITIES[SOURCE][1], "physical_lines": 700},
        "topology": {"segments": 8, "topics": 8, "present_surfaces": sum(surface_counts.values()), "present_surface_counts": dict(sorted(surface_counts.items())), "exercise_hint_solution_sets": 6, "lab_artifacts": 4},
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
    evidence = validate_source_and_lab()
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
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
