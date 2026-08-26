#!/usr/bin/env python3
"""Independently validate the additive Original-02 backend closure.

This validator does not import the generator.  It independently freezes the
live Original-02 source and lab evidence, rediscovers all segment and semantic
surface ranges, recomputes the stable-ID and relation topology, proves exact
recovery of the protected 3,943-record backend through Original-01, checks
JSONL/CSV losslessness, and performs two deterministic generator regenerations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"
RECEIPT_PATH = ROOT / "qa" / "ORIGINAL_02_BACKEND_VALIDATION.json"
EXTENSION_RECEIPT_PATH = ROOT / "qa" / "ORIGINAL_02_BACKEND_BUILD.json"
GENERATOR = ROOT / "qa" / "extend_backend_original_02.py"

WORKFLOW = "o015-original-02-backend-v1"
BASE = "d90.orig.v1.tr02"
RESOURCE_ID = f"{BASE}.resource"
EDITION_ID = f"{BASE}.edition.id-id"
UNIT_ID = f"{BASE}.unit"
CONTENT_RIGHTS_ID = f"{BASE}.rights.content.cc-by-sa-4-0"
SCAFFOLD_RIGHTS_ID = f"{BASE}.rights.wrapper-mixed"
TOOLING_RIGHTS_ID = f"{BASE}.rights.tooling"

SCHEMA_IDENTITY = (
    3_092,
    "1166cbffe6016044430fe003e4981b1a3a537be7c115f0b646168a1936ab5ad0",
)
BASELINE_COUNT = 3_943
BASELINE_JSONL = (
    2_941_125,
    "d829eb7641e04aff41529be436818514d88dc3b2961d2d23fbc12d1d6b9fc35f",
)
BASELINE_CSV = (
    3_537_781,
    "4fd14cad8d08b0e551bf8ce8d306fc8ee11751a9b66e1717b7f1a3c16a822ab4",
)
BASELINE_ID_SET_SHA256 = "a71d22270106e2fe9a48fe9cd6d13083dcb67608b98f93836ce5282fcd3c2877"
BASELINE_ID_ORDER_SHA256 = "c388136ac08c27377246a28faba7d305c05b3c5f6eb8a8fbf2a859d7f64ea7a7"
BASELINE_RECORD_SET_SHA256 = "cb024eb91a7c2c996a3fbcc8da3425183e70ed81debd6f4e87d2d19eac7028b6"
BASELINE_LINE_SEQUENCE_SHA256 = "8c591d614f95ecdd1bdb05a6dcc22b8c0685ce1e8b44be32694d49cf6cef6ba8"

SOURCE = "source/id-ID/original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
WRAPPER = "source/id-ID/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
LAB_CODE = "labs/original-02/monotone-splitting-lab.py"
LAB_JSON = "labs/original-02/results.json"
LAB_CSV = "labs/original-02/results.csv"
LAB_SVG = "labs/original-02/residual.svg"
BACKEND_GENERATOR = "qa/extend_backend_original_02.py"
BACKEND_VALIDATOR = "qa/validate_backend_original_02.py"
SOURCE_LINES = 744

FROZEN_IDENTITIES = {
    SOURCE: (28_028, "0f58d7785f281dd4e10ab3630d2f22a62b388ca98fd50b0e972e1cc89d847367"),
    WRAPPER: (5_476, "cf8dd0e4cc31d8409bb2d8f27e1a6373adf728ba93702aa01e1a398d73a65db3"),
    LAB_CODE: (17_904, "1d13f436644216104036be248ebb3ff0b1a9e45c856aef9229f17a5f26f3e119"),
    LAB_JSON: (13_503, "bc39d3363f02b904a27245bfe090cbf2153238a5a18ba8bf7cccbe1352672e81"),
    LAB_CSV: (4_228, "da8d09cce727c98b408fe719735574977266de1b58f95a742dcb60c5d163e243"),
    LAB_SVG: (9_538, "c7bdeeed813cf36999ae2748362e547fc23de2d5ae15c6131e3fc73edeba6fd5"),
}

ARTIFACT_SUFFIX_PATHS = {
    "source-body": SOURCE,
    "source-wrapper": WRAPPER,
    "lab-code": LAB_CODE,
    "lab-results-json": LAB_JSON,
    "lab-results-csv": LAB_CSV,
    "lab-results-svg": LAB_SVG,
    "backend-generator": BACKEND_GENERATOR,
    "backend-validator": BACKEND_VALIDATOR,
}

SEGMENT_DEFS = (
    (1, "% OR02-S001 | lapisan asli: masalah inklusi dan ketaksamaan variasional", "monotone-inclusion-model"),
    (2, "% OR02-S002 | lapisan asli: ketaksamaan variasional dan kerucut normal", "variational-inequality-normal-cone"),
    (3, "% OR02-S003 | lapisan asli: teorema Minty dan resolven", "maximal-monotone-resolvent"),
    (4, "% OR02-S004 | lapisan asli: metode titik proksimal", "proximal-point-method"),
    (5, "% OR02-S005 | lapisan asli: pemisahan maju--mundur", "forward-backward-extragradient"),
    (6, "% OR02-S006 | lapisan asli: Douglas--Rachford dalam bahasa operator", "douglas-rachford-operator"),
    (7, "% OR02-S007 | lapisan asli: diagnostik skew dan laboratorium", "skew-diagnostic-monotone-splitting-lab"),
    (8, "% OR02-S008 | lapisan asli: latihan, solusi, dan peta batas", "worked-monotone-inclusion-exercises-and-assumptions"),
)
TOPIC_DEFS = (
    ("monotone-inclusion-model", (), 1),
    ("variational-inequality-normal-cone", ("monotone-inclusion-model",), 2),
    ("maximal-monotone-resolvent", ("monotone-inclusion-model",), 3),
    ("proximal-point-method", ("maximal-monotone-resolvent",), 4),
    ("forward-backward-extragradient", ("variational-inequality-normal-cone", "maximal-monotone-resolvent"), 5),
    ("douglas-rachford-operator", ("maximal-monotone-resolvent",), 6),
    ("skew-diagnostic-monotone-splitting-lab", ("forward-backward-extragradient", "douglas-rachford-operator"), 7),
    ("worked-monotone-inclusion-exercises-and-assumptions", ("variational-inequality-normal-cone", "maximal-monotone-resolvent", "forward-backward-extragradient", "douglas-rachford-operator"), 8),
)
PRESENT_SURFACES = {
    "chapter": 1,
    "section": 10,
    "subsection": 2,
    "definition": 3,
    "theorem": 6,
    "lemma": 0,
    "proposition": 3,
    "corollary": 1,
    "proof": 10,
    "equation": 45,
    "exercise": 6,
    "hint": 6,
    "solution": 6,
    "lab": 1,
}
QA_SUFFIXES = {
    "source-freeze",
    "segment-binding",
    "semantic-surfaces",
    "lab-results",
    "rights-provenance",
    "backend-integration",
}
ENVIRONMENT_SURFACE = {
    "defn": "definition",
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

TOKEN = re.compile(r"\\(?P<kind>begin|end)\{(?P<env>[^}]+)\}")
HEADING = re.compile(r"^\\(?P<kind>chapter|section|subsection)\*?\{(?P<title>.+)\}$")
HINT_OR_SOLUTION = re.compile(r"^\\textbf\{(?P<label>Petunjuk bertahap|Solusi lengkap)\.\}")


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"required Original-02 artifact is missing: {relative}")
    raw = path.read_bytes()
    if not raw:
        raise ValueError(f"required Original-02 artifact is empty: {relative}")
    return len(raw), digest(raw)


def normalized_slice(relative: str, first: int, last: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if first < 1 or last < first or last > len(lines):
        raise ValueError(f"invalid normalized slice {relative}:{first}-{last}")
    raw = ("\n".join(lines[first - 1 : last]) + "\n").encode("utf-8")
    return len(raw), digest(raw)


def id_set(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(sorted(record["id"] for record in records)) + "\n").encode("utf-8"))


def id_order(records: list[dict[str, Any]]) -> str:
    return digest(("\n".join(record["id"] for record in records) + "\n").encode("utf-8"))


def record_set(records: list[dict[str, Any]]) -> str:
    payload = "\n".join(canonical(record) for record in sorted(records, key=lambda item: item["id"])) + "\n"
    return digest(payload.encode("utf-8"))


def line_sequence(raw: bytes) -> str:
    hashes = [digest(line) for line in raw.splitlines(keepends=True)]
    return digest(("\n".join(hashes) + "\n").encode("utf-8"))


def strip_jsonl(raw: bytes) -> bytes:
    return b"".join(
        line
        for line in raw.splitlines(keepends=True)
        if json.loads(line.decode("utf-8")).get("responsible_workflow") != WORKFLOW
    )


def strip_csv(raw: bytes) -> bytes:
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


def assert_schema_identity() -> dict[str, Any]:
    if file_info("backend/backend_schema.json") != SCHEMA_IDENTITY:
        raise ValueError("backend schema bytes differ from protected v1.0.0 schema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("schema") != "o015-modular-backend-schema" or schema.get("schema_version") != "1.0.0":
        raise ValueError("backend schema identity fields differ")
    return schema


def validate_evidence() -> dict[str, Any]:
    for path, identity in FROZEN_IDENTITIES.items():
        if file_info(path) != identity:
            raise ValueError(f"frozen Original-02 identity differs: {path}")
    for path in (BACKEND_GENERATOR, BACKEND_VALIDATOR):
        file_info(path)
    lab_code_text = (ROOT / LAB_CODE).read_text(encoding="utf-8")
    if any(re.search(rf"^\s*(?:from|import)\s+{module}\b", lab_code_text, re.MULTILINE) for module in ("requests", "urllib", "socket", "httpx")):
        raise ValueError("Original-02 lab unexpectedly imports a network client")

    source_lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    if len(source_lines) != SOURCE_LINES:
        raise ValueError("Original-02 source line count differs")
    source_text = "\n".join(source_lines)
    if not any(line.strip() == r"\item Jalankan konfigurasi beku dan cocokkan ringkasan JSON serta CSV." for line in source_lines):
        raise ValueError("configuration-verification wording differs")
    if (
        source_text.count(r"\begin{defn}") != 3
        or source_text.count(r"\begin{proof}") != 10
        or source_text.count(r"\begin{exercise}") != 6
        or source_text.count(r"\label{orig02:lab:monotone-splitting}") != 1
    ):
        raise ValueError("Original-02 semantic source markers differ")
    labels = re.findall(r"\\label\{([^}]+)\}", source_text)
    unescaped_dollars = len(re.findall(r"(?<!\\)\$", source_text))
    display_math = sum(source_text.count(rf"\begin{{{environment}}}") for environment in ("equation", "multline"))
    if len(labels) != 53 or len(set(labels)) != 53 or unescaped_dollars % 2 or display_math != 45 or unescaped_dollars // 2 + display_math != 294:
        raise ValueError("Original-02 label or mathematical-surface inventory differs")

    wrapper = (ROOT / WRAPPER).read_text(encoding="utf-8")
    identity_wrapper_markers = (
        f"% unit-id: {UNIT_ID}",
        "% target-edition-id: d90.orig.v1.tr02.edition.id-ID",
        "% authorship: independent coursebook completion layer",
        r"\input{original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id}",
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
        raise ValueError("wrapper identity, rights, or provenance marker differs")

    lab = json.loads((ROOT / LAB_JSON).read_text(encoding="utf-8"))
    expected_parameters = {
        "b": [1.2, -0.7],
        "checkpoints": [0, 1, 2, 5, 10, 20, 40, 80, 120, 200],
        "douglas_rachford_gamma": 0.7,
        "forward_backward_diagnostic_gamma": 0.9,
        "forward_backward_stable_gamma": 0.4,
        "iterations": 200,
        "lambda": 0.25,
        "mu": 1.0,
        "omega": 1.5,
        "x0": [2.5, -2.0],
        "y0": [2.5, -2.0],
    }
    if (
        lab.get("schema") != "o015-original-02-monotone-splitting-lab-v1"
        or lab.get("result") != "pass"
        or lab.get("parameters") != expected_parameters
        or lab.get("upstream_contact") is not False
    ):
        raise ValueError("lab JSON closure differs")
    theory = lab.get("theory", {})
    expected_beta = expected_parameters["mu"] / (expected_parameters["mu"] ** 2 + expected_parameters["omega"] ** 2)
    if (
        not math.isclose(float(theory.get("beta", math.nan)), expected_beta, rel_tol=0.0, abs_tol=1e-15)
        or not math.isclose(float(theory.get("forward_backward_upper_bound", math.nan)), 2.0 * expected_beta, rel_tol=0.0, abs_tol=1e-15)
        or theory.get("stable_step_inside_open_interval") is not True
        or theory.get("diagnostic_step_outside_proved_interval") is not True
    ):
        raise ValueError("lab theorem-bound evidence differs")
    reference = lab.get("reference", {})
    if (
        reference.get("method") != "complete_active_set_enumeration"
        or reference.get("pattern") != [1, -1]
        or reference.get("subgradient") != [1.0, -1.0]
        or float(reference.get("inclusion_residual", math.inf)) > 1e-14
    ):
        raise ValueError("lab reference-solution evidence differs")
    interpretation = lab.get("interpretation", {})
    if (
        interpretation.get("accepted_methods") != ["forward_backward_stable", "douglas_rachford"]
        or interpretation.get("diagnostic_only") != "forward_backward_outside_range"
        or not interpretation.get("claim_boundary")
    ):
        raise ValueError("lab interpretation boundary differs")
    skew = lab.get("pure_skew_diagnostic", {})
    skew_methods = skew.get("methods", {})
    if (
        skew.get("gamma") != 0.6
        or skew.get("steps") != 30
        or skew.get("initial") != [1.25, -0.75]
        or set(skew_methods) != {"forward", "extragradient", "resolvent"}
        or any(float(node.get("factor_absolute_error", math.inf)) > 1e-14 for node in skew_methods.values())
        or float(skew_methods["forward"].get("final_norm", 0.0)) <= float(skew.get("initial_norm", math.inf))
        or float(skew_methods["extragradient"].get("final_norm", math.inf)) >= float(skew.get("initial_norm", 0.0))
        or float(skew_methods["resolvent"].get("final_norm", math.inf)) >= float(skew.get("initial_norm", 0.0))
    ):
        raise ValueError("pure-skew diagnostic evidence differs")

    reader = csv.DictReader(io.StringIO((ROOT / LAB_CSV).read_text(encoding="utf-8")))
    expected_columns = [
        "method",
        "iteration",
        "x1",
        "x2",
        "norm",
        "error_to_reference",
        "fixed_point_residual",
        "inclusion_residual",
    ]
    if reader.fieldnames != expected_columns:
        raise ValueError("lab CSV columns differ")
    rows = list(reader)
    methods = {"forward_backward_stable", "forward_backward_outside_range", "douglas_rachford"}
    if len(rows) != 30 or Counter(row["method"] for row in rows) != Counter({method: 10 for method in methods}):
        raise ValueError("lab CSV row/method census differs")
    json_rows = lab.get("rows")
    if not isinstance(json_rows, list) or len(json_rows) != 30:
        raise ValueError("lab JSON row census differs")
    numeric_columns = expected_columns[1:]
    for csv_row, json_row in zip(rows, json_rows):
        if csv_row["method"] != json_row.get("method"):
            raise ValueError("lab CSV/JSON method projection differs")
        for key in numeric_columns:
            expected = int(csv_row[key]) if key == "iteration" else float(csv_row[key])
            if json_row.get(key) != expected:
                raise ValueError(f"lab CSV/JSON {key} projection differs")
    checkpoints = expected_parameters["checkpoints"]
    for method in sorted(methods):
        method_rows = [row for row in rows if row["method"] == method]
        if [int(row["iteration"]) for row in method_rows] != checkpoints:
            raise ValueError(f"lab checkpoints differ for {method}")
        terminal = method_rows[-1]
        final = lab.get("final", {}).get(method, {})
        if final.get("method") != method:
            raise ValueError(f"lab terminal method differs for {method}")
        for key in numeric_columns:
            expected = int(terminal[key]) if key == "iteration" else float(terminal[key])
            if final.get(key) != expected:
                raise ValueError(f"lab terminal {key} differs for {method}")
    if (
        float(lab["final"]["forward_backward_stable"]["inclusion_residual"]) > 1e-12
        or float(lab["final"]["douglas_rachford"]["inclusion_residual"]) > 1e-12
        or float(lab["final"]["forward_backward_outside_range"]["inclusion_residual"]) < 1e20
        or float(lab.get("resolvent_probe", {}).get("identity_error", math.inf)) > 1e-14
    ):
        raise ValueError("lab accepted/diagnostic residual boundary differs")

    svg = (ROOT / LAB_SVG).read_text(encoding="utf-8")
    required_svg_markers = (
        'role="img" aria-labelledby="title desc"',
        '<title id="title">Residu inklusi operator monoton</title>',
        '<desc id="desc">Perbandingan residu maju--mundur dengan langkah diterima, langkah di luar jaminan, dan Douglas--Rachford.</desc>',
    )
    if any(svg.count(marker) != 1 for marker in required_svg_markers):
        raise ValueError("lab SVG accessible title/description differs")
    return {"lab": lab, "rows": rows}


def discover_segments() -> list[dict[str, Any]]:
    lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    marker_map = {marker: (number, topic) for number, marker, topic in SEGMENT_DEFS}
    found: list[tuple[int, int, str, str]] = []
    for line_number, line in enumerate(lines, 1):
        if line in marker_map:
            number, topic = marker_map[line]
            found.append((line_number, number, topic, line))
    if [number for _, number, _, _ in found] != list(range(1, 9)):
        raise ValueError("Original-02 eight-marker closure differs")
    segments: list[dict[str, Any]] = []
    for index, (start, number, topic, marker) in enumerate(found):
        segment_id = f"{BASE}.seg{number:04d}"
        if start >= len(lines) or lines[start] != f"% segment-id: {segment_id}":
            raise ValueError(f"stable segment marker differs: {segment_id}")
        end = found[index + 1][0] - 1 if index + 1 < len(found) else len(lines)
        segments.append({"id": segment_id, "number": number, "topic_id": f"{BASE}.topic.{topic}", "start": start, "end": end, "marker": marker})
    return segments


def segment_for_line(segments: list[dict[str, Any]], line_number: int) -> dict[str, Any]:
    matches = [segment for segment in segments if segment["start"] <= line_number <= segment["end"]]
    if len(matches) != 1:
        raise ValueError(f"source line {line_number} belongs to {len(matches)} segments")
    return matches[0]


def discover_surfaces(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    candidates: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    exercises: list[tuple[int, int]] = []
    for number, raw in enumerate(lines, 1):
        line = re.sub(r"(?<!\\)%.*", "", raw).strip()
        heading = HEADING.fullmatch(line)
        if heading:
            candidates.append({"surface_type": heading.group("kind"), "environment": "latex-heading", "start": number, "end": number})
        for token in TOKEN.finditer(line):
            environment = token.group("env")
            if token.group("kind") == "begin":
                stack.append((environment, number))
                continue
            if not stack or stack[-1][0] != environment:
                raise ValueError(f"unbalanced {environment} at {SOURCE}:{number}")
            opened, start = stack.pop()
            if opened in ENVIRONMENT_SURFACE:
                candidates.append({"surface_type": ENVIRONMENT_SURFACE[opened], "environment": opened, "start": start, "end": number})
                if opened == "exercise":
                    exercises.append((start, number))
            elif opened == "quote" and re.search(r"\\textbf\{Algoritma [12]:", "\n".join(lines[start - 1 : number])):
                candidates.append({"surface_type": "algorithm", "environment": "quote-algorithm", "start": start, "end": number})
    if stack:
        raise ValueError("unclosed TeX environment")

    for start, end in sorted(exercises):
        markers: list[tuple[int, str]] = []
        for number in range(start, end + 1):
            match = HINT_OR_SOLUTION.match(re.sub(r"(?<!\\)%.*", "", lines[number - 1]).strip())
            if match:
                markers.append((number, "hint" if match.group("label") == "Petunjuk bertahap" else "solution"))
        if [kind for _, kind in markers] != ["hint", "solution"]:
            raise ValueError(f"exercise at line {start} lacks its pair")
        hint_start = markers[0][0]
        solution_start = markers[1][0]
        hint_end = solution_start - 1
        while hint_end > hint_start and not lines[hint_end - 1].strip():
            hint_end -= 1
        candidates.append({"surface_type": "hint", "environment": "latex-bold-heading", "start": hint_start, "end": hint_end})
        candidates.append({"surface_type": "solution", "environment": "latex-bold-heading", "start": solution_start, "end": end})

    lab_segment = segments[6]
    lab_candidates = [
        number
        for number in range(lab_segment["start"], lab_segment["end"] + 1)
        if lines[number - 1].startswith(r"\subsection*{Laboratorium 2:")
    ]
    if lab_candidates != [516]:
        raise ValueError("Original-02 laboratory subsection anchor differs")
    lab_start = lab_candidates[0]
    lab_end = lab_segment["end"]
    while lab_end > lab_start and not lines[lab_end - 1].strip():
        lab_end -= 1
    lab_text = "\n".join(lines[lab_start - 1 : lab_end])
    if (
        r"\label{orig02:lab:monotone-splitting}" not in lab_text
        or "Jalankan konfigurasi beku dan cocokkan ringkasan JSON serta CSV" not in lab_text
    ):
        raise ValueError("Original-02 laboratory surface boundaries differ")
    candidates.append({"surface_type": "lab", "environment": "coursebook-lab", "start": lab_start, "end": lab_end})

    counts = Counter(item["surface_type"] for item in candidates)
    if counts != Counter(PRESENT_SURFACES):
        raise ValueError(f"present-surface census differs: {dict(counts)}")
    counters: Counter[str] = Counter()
    result: list[dict[str, Any]] = []
    for item in sorted(candidates, key=lambda value: (value["start"], value["end"], value["surface_type"], value["environment"])):
        counters[item["surface_type"]] += 1
        segment = segment_for_line(segments, item["start"])
        result.append(
            {
                **item,
                "id": f"{BASE}.{item['surface_type']}.{counters[item['surface_type']]:04d}",
                "segment_id": segment["id"],
                "topic_id": segment["topic_id"],
            }
        )
    return result


def expected_relation_map(segments: list[dict[str, Any]], surfaces: list[dict[str, Any]]) -> dict[str, tuple[str, str, str]]:
    relations: dict[str, tuple[str, str, str]] = {
        f"{BASE}.relation.course-contains-unit": ("contains", "course.d90.advanced-optimization-convex-analysis", UNIT_ID),
        f"{BASE}.relation.original-01-precedes-original-02": ("precedes", "d90.orig.v1.tr01.unit", UNIT_ID),
        f"{BASE}.relation.resource-contains-edition": ("contains", RESOURCE_ID, EDITION_ID),
        f"{BASE}.relation.edition-contains-unit": ("contains", EDITION_ID, UNIT_ID),
        f"{BASE}.relation.source-wrapper-adapts-source-body": ("adapts", f"{BASE}.artifact.source-wrapper", f"{BASE}.artifact.source-body"),
        f"{BASE}.relation.lab-code-illustrates-lab": ("illustrates", f"{BASE}.artifact.lab-code", f"{BASE}.lab.0001"),
        f"{BASE}.relation.lab-results-json-illustrates-lab": ("illustrates", f"{BASE}.artifact.lab-results-json", f"{BASE}.lab.0001"),
        f"{BASE}.relation.lab-results-csv-illustrates-lab": ("illustrates", f"{BASE}.artifact.lab-results-csv", f"{BASE}.lab.0001"),
        f"{BASE}.relation.lab-results-svg-illustrates-lab": ("illustrates", f"{BASE}.artifact.lab-results-svg", f"{BASE}.lab.0001"),
    }
    for segment in segments:
        relations[f"{BASE}.relation.unit-contains-seg{segment['number']:04d}"] = ("contains", UNIT_ID, segment["id"])
    for slug, prerequisites, _ in TOPIC_DEFS:
        topic_id = f"{BASE}.topic.{slug}"
        relations[f"{BASE}.relation.unit-contains-topic-{slug}"] = ("contains", UNIT_ID, topic_id)
        for prerequisite in prerequisites:
            relations[f"{BASE}.relation.topic-{slug}-prerequisite-{prerequisite}"] = ("prerequisite", topic_id, f"{BASE}.topic.{prerequisite}")
    for surface in surfaces:
        suffix = surface["id"].removeprefix(f"{BASE}.").replace(".", "-")
        relations[f"{BASE}.relation.unit-contains-{suffix}"] = ("contains", UNIT_ID, surface["id"])
        relation_type = "defines" if surface["surface_type"] == "definition" else "exercises" if surface["surface_type"] in {"exercise", "hint", "solution"} else "illustrates"
        relations[f"{BASE}.relation.{suffix}-to-topic"] = (relation_type, surface["id"], surface["topic_id"])
    for number in range(1, 7):
        relations[f"{BASE}.relation.hint-{number:04d}-depends-on-exercise-{number:04d}"] = ("depends-on", f"{BASE}.hint.{number:04d}", f"{BASE}.exercise.{number:04d}")
        relations[f"{BASE}.relation.solution-{number:04d}-depends-on-exercise-{number:04d}"] = ("depends-on", f"{BASE}.solution.{number:04d}", f"{BASE}.exercise.{number:04d}")
    proof_targets = (
        f"{BASE}.proposition.0001",
        f"{BASE}.proposition.0002",
        f"{BASE}.proposition.0003",
        f"{BASE}.theorem.0001",
        f"{BASE}.theorem.0002",
        f"{BASE}.corollary.0001",
        f"{BASE}.theorem.0003",
        f"{BASE}.theorem.0004",
        f"{BASE}.theorem.0005",
        f"{BASE}.theorem.0006",
    )
    for number, target in enumerate(proof_targets, 1):
        suffix = f"proof-{number:04d}-proves-{target.rsplit('.', 2)[-2]}-{target.rsplit('.', 1)[-1]}"
        relations[f"{BASE}.relation.{suffix}"] = ("proves", f"{BASE}.proof.{number:04d}", target)
    return relations


def expected_ids(segments: list[dict[str, Any]], surfaces: list[dict[str, Any]]) -> set[str]:
    result = {RESOURCE_ID, EDITION_ID, UNIT_ID, CONTENT_RIGHTS_ID, SCAFFOLD_RIGHTS_ID, TOOLING_RIGHTS_ID}
    result.update(f"{BASE}.topic.{slug}" for slug, _, _ in TOPIC_DEFS)
    result.update(segment["id"] for segment in segments)
    result.update(surface["id"] for surface in surfaces)
    result.update(f"{BASE}.artifact.{suffix}" for suffix in ARTIFACT_SUFFIX_PATHS)
    result.update(f"{BASE}.qa.{suffix}" for suffix in QA_SUFFIXES)
    result.update(expected_relation_map(segments, surfaces))
    return result


def validate_dataset(jsonl_path: Path, csv_path: Path) -> dict[str, Any]:
    schema = assert_schema_identity()
    evidence = validate_evidence()
    segments = discover_segments()
    surface_specs = discover_surfaces(segments)

    jsonl_raw = jsonl_path.read_bytes()
    csv_raw = csv_path.read_bytes()
    records = [json.loads(line) for line in jsonl_raw.decode("utf-8", errors="strict").splitlines() if line]
    lines = jsonl_raw.splitlines(keepends=True)
    if len(lines) != len(records) or any(line != (canonical(record) + "\n").encode("utf-8") for line, record in zip(lines, records)):
        raise ValueError("JSONL is not canonical compact UTF-8 with LF terminators")
    if len({record["id"] for record in records}) != len(records):
        raise ValueError("duplicate backend IDs")

    reader = csv.DictReader(io.StringIO(csv_raw.decode("utf-8", errors="strict")))
    expected_columns = ["schema", "schema_version", "entity_type", "id", "record_json"]
    if reader.fieldnames != expected_columns:
        raise ValueError("CSV header differs")
    rows = list(reader)
    if len(rows) != len(records):
        raise ValueError("CSV row count differs")
    for row, record in zip(rows, records):
        if json.loads(row["record_json"]) != record:
            raise ValueError(f"CSV record_json differs for {record['id']}")
        if [row[name] for name in expected_columns[:4]] != [record[name] for name in expected_columns[:4]]:
            raise ValueError(f"CSV identity columns differ for {record['id']}")

    rank = {name: index for index, name in enumerate(schema["entity_order"])}
    if records != sorted(records, key=lambda record: (rank[record["entity_type"]], record["id"])):
        raise ValueError("global entity/id order differs")
    all_ids = {record["id"] for record in records}
    id_pattern = re.compile(schema["id_pattern"])
    for record in records:
        if record["entity_type"] not in rank:
            raise ValueError(f"unknown entity type {record['entity_type']}")
        missing = [field for field in schema["required_common"] + schema["required_by_entity"].get(record["entity_type"], []) if field not in record]
        if missing:
            raise ValueError(f"{record['id']} lacks required fields {missing}")
        if not id_pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid stable ID {record['id']}")
        if record["entity_type"] == "relation" and record["relation_type"] not in schema["relation_types"]:
            raise ValueError(f"invalid relation type in {record['id']}")
        if "translation_state" in record and record["translation_state"] not in schema["translation_states"]:
            raise ValueError(f"invalid translation state in {record['id']}")
        for field in schema["reference_fields"]:
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")

    for record in records:
        owned = record.get("responsible_workflow") == WORKFLOW
        namespaced = record["id"].startswith(f"{BASE}.")
        if owned != namespaced:
            raise ValueError(f"workflow/namespace ownership differs for {record['id']}")

    baseline_jsonl = strip_jsonl(jsonl_raw)
    baseline_csv = strip_csv(csv_raw)
    if (len(baseline_jsonl), digest(baseline_jsonl)) != BASELINE_JSONL:
        raise ValueError("workflow stripping does not recover exact protected JSONL")
    if (len(baseline_csv), digest(baseline_csv)) != BASELINE_CSV:
        raise ValueError("workflow stripping does not recover exact protected CSV")
    if line_sequence(baseline_jsonl) != BASELINE_LINE_SEQUENCE_SHA256:
        raise ValueError("protected JSONL line sequence differs")
    baseline = [record for record in records if record.get("responsible_workflow") != WORKFLOW]
    new = [record for record in records if record.get("responsible_workflow") == WORKFLOW]
    if (
        len(baseline) != BASELINE_COUNT
        or id_set(baseline) != BASELINE_ID_SET_SHA256
        or id_order(baseline) != BASELINE_ID_ORDER_SHA256
        or record_set(baseline) != BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("protected baseline set/order differs")

    expected = expected_ids(segments, surface_specs)
    new_ids = {record["id"] for record in new}
    if new_ids != expected:
        raise ValueError(f"Original-02 stable-ID set differs; missing={sorted(expected-new_ids)}, extra={sorted(new_ids-expected)}")
    relation_map = expected_relation_map(segments, surface_specs)
    expected_counts = Counter(
        {
            "resource": 1,
            "edition": 1,
            "unit": 1,
            "concept": 8,
            "segment": 8,
            "learning_surface": sum(PRESENT_SURFACES.values()),
            "rights": 3,
            "artifact": len(ARTIFACT_SUFFIX_PATHS),
            "qa_event": len(QA_SUFFIXES),
            "relation": len(relation_map),
        }
    )
    if Counter(record["entity_type"] for record in new) != expected_counts:
        raise ValueError("Original-02 entity topology differs")

    by_id = {record["id"]: record for record in records}
    resource = by_id[RESOURCE_ID]
    edition = by_id[EDITION_ID]
    unit = by_id[UNIT_ID]
    if (
        resource.get("title") != "Ketaksamaan Variasional, Operator Monoton, Resolven, dan Pemisahan"
        or resource.get("official_record") != SOURCE
        or resource.get("rights_id") != CONTENT_RIGHTS_ID
        or resource.get("language") != "id"
        or resource.get("locale") != "id-ID"
        or resource.get("content_origin") != "independently authored original coursebook completion layer"
        or resource.get("mathematical_witnesses_only") is not True
        or resource.get("non_endorsement") is not True
    ):
        raise ValueError("Original-02 resource provenance differs")
    if (
        edition.get("resource_id") != RESOURCE_ID
        or edition.get("rights_id") != CONTENT_RIGHTS_ID
        or edition.get("version") != "original-02-id-ID-v1"
        or edition.get("source_artifact_id") != f"{BASE}.artifact.source-body"
        or edition.get("declared_wrapper_edition_id") != "d90.orig.v1.tr02.edition.id-ID"
    ):
        raise ValueError("Original-02 edition normalization differs")
    if (
        unit.get("edition_id") != EDITION_ID
        or unit.get("target_edition_id") != EDITION_ID
        or unit.get("course_id") != "course.d90.advanced-optimization-convex-analysis"
        or unit.get("order") != 5
        or unit.get("source_locator") != f"{SOURCE}:1-{SOURCE_LINES}"
        or unit.get("target_locator") != f"{SOURCE}:1-{SOURCE_LINES}"
        or unit.get("rights_id") != CONTENT_RIGHTS_ID
    ):
        raise ValueError("Original-02 unit topology differs")

    source_lines = (ROOT / SOURCE).read_text(encoding="utf-8").splitlines()
    for segment in segments:
        record = by_id[segment["id"]]
        expected_identity = normalized_slice(SOURCE, segment["start"], segment["end"])
        if (
            record.get("order") != segment["number"]
            or record.get("source_path") != SOURCE
            or record.get("target_path") != SOURCE
            or record.get("source_line_start") != segment["start"]
            or record.get("source_line_end") != segment["end"]
            or record.get("target_line_start") != segment["start"]
            or record.get("target_line_end") != segment["end"]
            or (record.get("source_content_bytes"), record.get("source_content_sha256")) != expected_identity
            or (record.get("target_content_bytes"), record.get("target_content_sha256")) != expected_identity
            or record.get("concept_ids") != [segment["topic_id"]]
            or record.get("unit_id") != UNIT_ID
            or record.get("source_edition_id") != EDITION_ID
            or record.get("target_edition_id") != EDITION_ID
            or record.get("translation_state") != "built"
            or record.get("content_origin") != "independently_authored_original_id-ID"
            or record.get("rights_id") != CONTENT_RIGHTS_ID
        ):
            raise ValueError(f"segment binding differs: {segment['id']}")
        if source_lines[segment["start"] - 1] != segment["marker"] or source_lines[segment["start"]] != f"% segment-id: {segment['id']}":
            raise ValueError(f"segment marker differs: {segment['id']}")

    for slug, prerequisites, number in TOPIC_DEFS:
        topic = by_id[f"{BASE}.topic.{slug}"]
        if (
            topic.get("domain") != "monotone operator theory and variational inequalities"
            or topic.get("prerequisite_ids") != [f"{BASE}.topic.{item}" for item in prerequisites]
            or topic.get("related_segment_ids") != [f"{BASE}.seg{number:04d}"]
            or topic.get("source_edition_id") != EDITION_ID
            or topic.get("target_edition_id") != EDITION_ID
            or topic.get("rights_id") != CONTENT_RIGHTS_ID
        ):
            raise ValueError(f"topic topology differs: {slug}")

    discovered = {surface["id"]: surface for surface in surface_specs}
    surface_records = [record for record in new if record["entity_type"] == "learning_surface"]
    if Counter(record["surface_type"] for record in surface_records) != Counter(PRESENT_SURFACES):
        raise ValueError("stored semantic-surface census differs")
    for record in surface_records:
        item = discovered[record["id"]]
        if (
            record.get("presence") != "present"
            or record.get("target_line_start") != item["start"]
            or record.get("target_line_end") != item["end"]
            or record.get("latex_environment") != item["environment"]
            or record.get("related_segment_ids") != [item["segment_id"]]
            or record.get("concept_ids") != [item["topic_id"]]
            or (record.get("target_content_bytes"), record.get("target_content_sha256")) != normalized_slice(SOURCE, item["start"], item["end"])
            or record.get("unit_id") != UNIT_ID
            or record.get("target_edition_id") != EDITION_ID
            or record.get("target_path") != SOURCE
            or record.get("rights_id") != CONTENT_RIGHTS_ID
        ):
            raise ValueError(f"surface binding differs: {record['id']}")
    lab_surface = by_id[f"{BASE}.lab.0001"]
    if (
        lab_surface.get("target_line_start") != 516
        or lab_surface.get("target_line_end") != 562
        or lab_surface.get("related_segment_ids") != [f"{BASE}.seg0007"]
        or lab_surface.get("input_artifact_ids") != [f"{BASE}.artifact.lab-code"]
        or lab_surface.get("evidence_artifact_id") != f"{BASE}.artifact.lab-results-json"
        or lab_surface.get("accessible_result_artifact_ids") != [f"{BASE}.artifact.lab-results-json", f"{BASE}.artifact.lab-results-csv"]
    ):
        raise ValueError("lab surface artifact binding differs")

    artifacts = [record for record in new if record["entity_type"] == "artifact"]
    expected_artifact_map = {f"{BASE}.artifact.{suffix}": path for suffix, path in ARTIFACT_SUFFIX_PATHS.items()}
    if {record["id"]: record["path"] for record in artifacts} != expected_artifact_map:
        raise ValueError("artifact path map differs")
    for artifact in artifacts:
        if file_info(artifact["path"]) != (artifact["bytes"], artifact["sha256"]):
            raise ValueError(f"artifact binds stale bytes: {artifact['id']}")
    expected_artifact_rights = {
        f"{BASE}.artifact.source-body": CONTENT_RIGHTS_ID,
        f"{BASE}.artifact.source-wrapper": SCAFFOLD_RIGHTS_ID,
        f"{BASE}.artifact.lab-code": CONTENT_RIGHTS_ID,
        f"{BASE}.artifact.lab-results-json": CONTENT_RIGHTS_ID,
        f"{BASE}.artifact.lab-results-csv": CONTENT_RIGHTS_ID,
        f"{BASE}.artifact.lab-results-svg": CONTENT_RIGHTS_ID,
        f"{BASE}.artifact.backend-generator": TOOLING_RIGHTS_ID,
        f"{BASE}.artifact.backend-validator": TOOLING_RIGHTS_ID,
    }
    if {artifact["id"]: artifact.get("rights_id") for artifact in artifacts} != expected_artifact_rights:
        raise ValueError("artifact rights map differs")
    if (
        by_id[f"{BASE}.artifact.source-body"].get("physical_lines") != SOURCE_LINES
        or by_id[f"{BASE}.artifact.lab-code"].get("deterministic") is not True
        or by_id[f"{BASE}.artifact.lab-code"].get("declared_upstream_contact") is not False
        or by_id[f"{BASE}.artifact.lab-results-json"].get("row_count") != 30
        or by_id[f"{BASE}.artifact.lab-results-csv"].get("row_count") != 30
        or by_id[f"{BASE}.artifact.lab-results-svg"].get("redundant_with_accessible_csv") is not True
    ):
        raise ValueError("artifact semantic metadata differs")

    rights = {record["id"]: record for record in new if record["entity_type"] == "rights"}
    if set(rights) != {CONTENT_RIGHTS_ID, SCAFFOLD_RIGHTS_ID, TOOLING_RIGHTS_ID}:
        raise ValueError("rights closure differs")
    content_rights = rights[CONTENT_RIGHTS_ID]
    if (
        content_rights.get("component_id") != f"{BASE}.content-and-lab"
        or content_rights.get("path") != f"{SOURCE} + labs/original-02"
        or content_rights.get("rights_expression") != "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
        or content_rights.get("content_origin") != "independent original writing and code; cited works are mathematical witnesses only"
    ):
        raise ValueError("rights provenance differs")
    scaffold = rights[SCAFFOLD_RIGHTS_ID]
    handling = set(scaffold.get("required_handling", []))
    if (
        scaffold.get("component_id") != f"{BASE}.wrapper-and-reader-scaffold"
        or scaffold.get("path") != f"{WRAPPER} + source/id-ID/shinybook.cls + source/id-ID/macros-id.tex"
        or scaffold.get("rights_expression") != "mixed rights: new wrapper wording CC BY-SA 4.0; exact Habring-bundled shinybook.cls and adapted Habring macros-id.tex CC BY 4.0"
        or "preserve Habring attribution and CC BY 4.0" not in handling
        or "preserve Christian Clason template credit" not in handling
    ):
        raise ValueError("mixed wrapper/scaffold rights closure differs")
    tooling = rights[TOOLING_RIGHTS_ID]
    if (
        tooling.get("component_id") != f"{BASE}.backend-tooling"
        or tooling.get("path") != f"{BACKEND_GENERATOR} + {BACKEND_VALIDATOR}"
        or tooling.get("rights_expression") != "project-local deterministic backend validation tooling"
    ):
        raise ValueError("backend-tooling rights closure differs")

    qa = [record for record in new if record["entity_type"] == "qa_event"]
    if {record["id"] for record in qa} != {f"{BASE}.qa.{suffix}" for suffix in QA_SUFFIXES} or any(record.get("status") != "passed" or record.get("result") != "pass" for record in qa):
        raise ValueError("QA-event closure differs")
    qa_by_id = {record["id"]: record for record in qa}
    if (
        qa_by_id[f"{BASE}.qa.source-freeze"].get("source_bytes") != FROZEN_IDENTITIES[SOURCE][0]
        or qa_by_id[f"{BASE}.qa.source-freeze"].get("source_sha256") != FROZEN_IDENTITIES[SOURCE][1]
        or qa_by_id[f"{BASE}.qa.source-freeze"].get("source_label_count") != 53
        or qa_by_id[f"{BASE}.qa.source-freeze"].get("source_display_math_count") != 45
        or qa_by_id[f"{BASE}.qa.source-freeze"].get("source_math_surface_count") != 294
        or qa_by_id[f"{BASE}.qa.segment-binding"].get("segment_count") != 8
        or qa_by_id[f"{BASE}.qa.semantic-surfaces"].get("present_surface_count") != 100
        or qa_by_id[f"{BASE}.qa.lab-results"].get("row_count") != 30
        or qa_by_id[f"{BASE}.qa.lab-results"].get("method_count") != 3
        or qa_by_id[f"{BASE}.qa.lab-results"].get("upstream_contact") is not False
        or qa_by_id[f"{BASE}.qa.lab-results"].get("json_csv_rows_exact") is not True
        or qa_by_id[f"{BASE}.qa.lab-results"].get("svg_redundant_with_accessible_csv") is not True
        or qa_by_id[f"{BASE}.qa.backend-integration"].get("protected_baseline_record_count") != BASELINE_COUNT
    ):
        raise ValueError("QA-event evidence differs")

    for relation_id, expected_triple in relation_map.items():
        relation = by_id[relation_id]
        triple = (relation.get("relation_type"), relation.get("source_id"), relation.get("target_id"))
        if triple != expected_triple:
            raise ValueError(f"relation differs: {relation_id}")

    ordered_new = sorted(new, key=lambda record: (rank[record["entity_type"]], record["id"]))
    return {
        "records": records,
        "new": new,
        "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
        "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new).items())),
        "new_id_set_sha256": id_set(new),
        "new_id_order_sha256": id_order(ordered_new),
        "new_record_set_sha256": record_set(new),
        "final_id_set_sha256": id_set(records),
        "final_id_order_sha256": id_order(records),
        "final_record_set_sha256": record_set(records),
        "final_line_sequence_sha256": line_sequence(jsonl_raw),
        "baseline_jsonl_recovered": {"bytes": len(baseline_jsonl), "sha256": digest(baseline_jsonl), "line_sequence_sha256": line_sequence(baseline_jsonl)},
        "baseline_csv_recovered": {"bytes": len(baseline_csv), "sha256": digest(baseline_csv)},
        "segments": segments,
        "surfaces": surface_specs,
        "relation_count": len(relation_map),
        "lab": evidence["lab"],
    }


def validation_identity(validated: dict[str, Any]) -> dict[str, Any]:
    return {
        "records": len(validated["records"]),
        "new_records": len(validated["new"]),
        "jsonl": validated["jsonl"],
        "csv": validated["csv"],
        "new_id_set_sha256": validated["new_id_set_sha256"],
        "new_id_order_sha256": validated["new_id_order_sha256"],
        "new_record_set_sha256": validated["new_record_set_sha256"],
        "final_id_set_sha256": validated["final_id_set_sha256"],
        "final_id_order_sha256": validated["final_id_order_sha256"],
        "final_record_set_sha256": validated["final_record_set_sha256"],
        "final_line_sequence_sha256": validated["final_line_sequence_sha256"],
    }


def expected_extension_admission(validated: dict[str, Any]) -> dict[str, Any]:
    return {
        "new_records": len(validated["new"]),
        "new_entity_counts": validated["new_entity_counts"],
        "new_id_set_sha256": validated["new_id_set_sha256"],
        "new_id_order_sha256": validated["new_id_order_sha256"],
        "new_record_set_sha256": validated["new_record_set_sha256"],
        "final_records": len(validated["records"]),
        "final_id_set_sha256": validated["final_id_set_sha256"],
        "final_id_order_sha256": validated["final_id_order_sha256"],
        "final_record_set_sha256": validated["final_record_set_sha256"],
        "final_line_sequence_sha256": validated["final_line_sequence_sha256"],
        "jsonl": validated["jsonl"],
        "csv": validated["csv"],
    }


def expected_protected_baseline() -> dict[str, Any]:
    return {
        "record_count": BASELINE_COUNT,
        "jsonl": {
            "bytes": BASELINE_JSONL[0],
            "sha256": BASELINE_JSONL[1],
            "line_sequence_sha256": BASELINE_LINE_SEQUENCE_SHA256,
        },
        "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
        "id_set_sha256": BASELINE_ID_SET_SHA256,
        "id_order_sha256": BASELINE_ID_ORDER_SHA256,
        "record_set_sha256": BASELINE_RECORD_SET_SHA256,
        "raw_record_bytes_and_relative_order_preserved": True,
    }


def validate_generator_result(
    result: dict[str, Any],
    output_jsonl: Path,
    output_csv: Path,
    validated: dict[str, Any],
) -> dict[str, Any]:
    surface_counts = Counter(item["surface_type"] for item in validated["surfaces"])
    expected_inputs = [
        {"path": path, "bytes": file_info(path)[0], "sha256": file_info(path)[1]}
        for path in ARTIFACT_SUFFIX_PATHS.values()
    ]
    expected_source = {
        "path": SOURCE,
        "bytes": FROZEN_IDENTITIES[SOURCE][0],
        "sha256": FROZEN_IDENTITIES[SOURCE][1],
        "physical_lines": SOURCE_LINES,
        "label_count": 53,
        "display_math_count": 45,
        "math_surface_count": 294,
    }
    expected_lab = {
        "row_count": 30,
        "methods": ["forward_backward_stable", "forward_backward_outside_range", "douglas_rachford"],
        "upstream_contact": False,
    }
    expected_topology = {
        "segments": 8,
        "topics": 8,
        "present_surfaces": 100,
        "present_surface_counts": dict(sorted(surface_counts.items())),
        "exercise_hint_solution_sets": 6,
        "proof_statement_pairs": 10,
        "lab_segment": 7,
        "lab_artifacts": 4,
    }
    if (
        result.get("schema") != "o015-original-02-backend-extension-v1"
        or result.get("result") != "pass"
        or result.get("workflow") != WORKFLOW
        or result.get("write_mode") != "staged"
        or result.get("namespace") != f"{BASE}.*"
        or result.get("collision_count") != 0
        or result.get("schema_identity") != {"bytes": SCHEMA_IDENTITY[0], "sha256": SCHEMA_IDENTITY[1], "schema_changed": False}
        or result.get("protected_baseline") != expected_protected_baseline()
        or result.get("admission") != expected_extension_admission(validated)
        or result.get("inputs") != expected_inputs
        or result.get("source") != expected_source
        or result.get("lab") != expected_lab
        or result.get("topology") != expected_topology
    ):
        raise ValueError("generator stdout receipt differs from independently validated Original-02 closure")
    if Path(str(result.get("output_jsonl"))).resolve() != output_jsonl.resolve() or Path(str(result.get("output_csv"))).resolve() != output_csv.resolve():
        raise ValueError("generator stdout output paths differ from staged outputs")
    return {
        "schema": result["schema"],
        "result": result["result"],
        "workflow": result["workflow"],
        "write_mode": "validator-confirmed-staged-regeneration",
        "namespace": result["namespace"],
        "collision_count": result["collision_count"],
        "schema_identity": result["schema_identity"],
        "protected_baseline": result["protected_baseline"],
        "admission": result["admission"],
        "inputs": result["inputs"],
        "source": result["source"],
        "lab": result["lab"],
        "topology": result["topology"],
    }


def deterministic_regeneration(jsonl_path: Path, csv_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    identities: list[dict[str, Any]] = []
    extension_receipts: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="original-02-backend-validation-") as temporary:
        root = Path(temporary)
        for run in (1, 2):
            output_dir = root / f"run-{run}"
            command = [sys.executable, str(GENERATOR), "--input-jsonl", str(jsonl_path), "--input-csv", str(csv_path), "--output-dir", str(output_dir)]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
            if completed.returncode != 0:
                raise ValueError(f"deterministic regeneration run {run} failed: {completed.stderr or completed.stdout}")
            jsonl_output = output_dir / "records.jsonl"
            csv_output = output_dir / "records.csv"
            try:
                generator_result = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                raise ValueError(f"deterministic regeneration run {run} emitted invalid JSON") from exc
            staged_validation = validate_dataset(jsonl_output, csv_output)
            extension_receipts.append(validate_generator_result(generator_result, jsonl_output, csv_output, staged_validation))
            identities.append(
                {
                    "run": run,
                    "jsonl": {"bytes": jsonl_output.stat().st_size, "sha256": digest(jsonl_output.read_bytes())},
                    "csv": {"bytes": csv_output.stat().st_size, "sha256": digest(csv_output.read_bytes())},
                    "validated_identity": validation_identity(staged_validation),
                }
            )
    if identities[0]["jsonl"] != identities[1]["jsonl"] or identities[0]["csv"] != identities[1]["csv"]:
        raise ValueError("two Original-02 deterministic regeneration runs differ")
    if extension_receipts[0] != extension_receipts[1]:
        raise ValueError("two Original-02 generator stdout receipts differ after path sanitization")
    if identities[0]["jsonl"] != {"bytes": jsonl_path.stat().st_size, "sha256": digest(jsonl_path.read_bytes())}:
        raise ValueError("regenerated Original-02 JSONL differs from validated input")
    if identities[0]["csv"] != {"bytes": csv_path.stat().st_size, "sha256": digest(csv_path.read_bytes())}:
        raise ValueError("regenerated Original-02 CSV differs from validated input")
    return identities, extension_receipts[0]


def validate_extension_receipt(receipt: dict[str, Any], validated: dict[str, Any], require_canonical: bool) -> None:
    surface_counts = Counter(item["surface_type"] for item in validated["surfaces"])
    expected_core = {
        "schema": "o015-original-02-backend-extension-v1",
        "result": "pass",
        "workflow": WORKFLOW,
        "namespace": f"{BASE}.*",
        "collision_count": 0,
        "schema_identity": {"bytes": SCHEMA_IDENTITY[0], "sha256": SCHEMA_IDENTITY[1], "schema_changed": False},
        "protected_baseline": expected_protected_baseline(),
        "admission": expected_extension_admission(validated),
        "inputs": [
            {"path": path, "bytes": file_info(path)[0], "sha256": file_info(path)[1]}
            for path in ARTIFACT_SUFFIX_PATHS.values()
        ],
        "source": {
            "path": SOURCE,
            "bytes": FROZEN_IDENTITIES[SOURCE][0],
            "sha256": FROZEN_IDENTITIES[SOURCE][1],
            "physical_lines": SOURCE_LINES,
            "label_count": 53,
            "display_math_count": 45,
            "math_surface_count": 294,
        },
        "lab": {
            "row_count": 30,
            "methods": ["forward_backward_stable", "forward_backward_outside_range", "douglas_rachford"],
            "upstream_contact": False,
        },
        "topology": {
            "segments": 8,
            "topics": 8,
            "present_surfaces": 100,
            "present_surface_counts": dict(sorted(surface_counts.items())),
            "exercise_hint_solution_sets": 6,
            "proof_statement_pairs": 10,
            "lab_segment": 7,
            "lab_artifacts": 4,
        },
    }
    canonical_expected = {
        **expected_core,
        "write_mode": "canonical",
        "output_jsonl": "backend/records.jsonl",
        "output_csv": "backend/records.csv",
    }
    staged_expected = {**expected_core, "write_mode": "validator-confirmed-staged-regeneration"}
    allowed = [canonical_expected] if require_canonical else [canonical_expected, staged_expected]
    if receipt not in allowed:
        raise ValueError("Original-02 backend extension receipt differs from the independently validated dataset")


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}.", suffix=".stage", dir=path.parent, delete=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            staged = Path(handle.name)
        if staged.read_bytes() != payload:
            raise ValueError("validation receipt staged readback differs")
        os.replace(staged, path)
        staged = None
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, default=JSONL_PATH)
    parser.add_argument("--input-csv", type=Path, default=CSV_PATH)
    parser.add_argument("--receipt", type=Path, default=RECEIPT_PATH)
    parser.add_argument("--extension-receipt", type=Path, default=EXTENSION_RECEIPT_PATH)
    parser.add_argument("--skip-regeneration", action="store_true", help="skip the two-run generator proof")
    args = parser.parse_args()
    canonical_flags = (args.input_jsonl.resolve() == JSONL_PATH.resolve(), args.input_csv.resolve() == CSV_PATH.resolve())
    if canonical_flags[0] != canonical_flags[1]:
        parser.error("--input-jsonl and --input-csv must both be canonical or both staged")
    if args.receipt.resolve() == args.extension_receipt.resolve():
        parser.error("--receipt and --extension-receipt must differ")

    first = validate_dataset(args.input_jsonl, args.input_csv)
    second = validate_dataset(args.input_jsonl, args.input_csv)
    first_identity = validation_identity(first)
    second_identity = validation_identity(second)
    if first_identity != second_identity:
        raise ValueError("two independent validator passes differ")
    canonical_backend = all(canonical_flags)
    regenerated_extension: dict[str, Any] | None = None
    if args.skip_regeneration:
        regenerations: list[dict[str, Any]] = []
    else:
        regenerations, regenerated_extension = deterministic_regeneration(args.input_jsonl, args.input_csv)
    if args.extension_receipt.is_file():
        extension_receipt = json.loads(args.extension_receipt.read_text(encoding="utf-8"))
        validate_extension_receipt(extension_receipt, first, require_canonical=canonical_backend)
    elif canonical_backend or args.skip_regeneration:
        raise FileNotFoundError("canonical or regeneration-skipped validation requires the generator-emitted Original-02 backend extension receipt")
    else:
        if regenerated_extension is None:
            raise ValueError("staged validation lacks a regenerated extension receipt")
        extension_receipt = regenerated_extension
        validate_extension_receipt(extension_receipt, first, require_canonical=False)
        write_receipt(args.extension_receipt, extension_receipt)
    surface_counts = Counter(item["surface_type"] for item in first["surfaces"])
    receipt = {
        "schema": "o015-original-02-backend-validation-v1",
        "validated_at": "2026-08-26T04:30:00Z",
        "result": "pass",
        "errors": [],
        "workflow": WORKFLOW,
        "commands": {
            "canonical_generation": "python qa/extend_backend_original_02.py --write-canonical",
            "staging": "python qa/extend_backend_original_02.py --output-dir <dir>",
            "validation": "python qa/validate_backend_original_02.py",
        },
        "schema_constraint": {
            "schema_changed": False,
            "schema_bytes": SCHEMA_IDENTITY[0],
            "schema_sha256": SCHEMA_IDENTITY[1],
            "additive_records_only": True,
            "note": "Global sorting means the old file is not a literal prefix; workflow stripping proves every protected JSONL line and CSV row remains byte-identical and in the same relative order.",
        },
        "protected_baseline": {
            "records": BASELINE_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1], "line_sequence_sha256": BASELINE_LINE_SEQUENCE_SHA256},
            "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]},
            "id_set_sha256": BASELINE_ID_SET_SHA256,
            "id_order_sha256": BASELINE_ID_ORDER_SHA256,
            "record_set_sha256": BASELINE_RECORD_SET_SHA256,
            "recovered_jsonl": first["baseline_jsonl_recovered"],
            "recovered_csv": first["baseline_csv_recovered"],
            "record_bytes_and_relative_order_stable": True,
        },
        "admission": {
            "canonical_backend_written": canonical_backend,
            "disposition": "validated_canonical_backend" if canonical_backend else "validated_staged_projection",
            "namespace": f"{BASE}.*",
            "new_records": len(first["new"]),
            "new_entity_counts": first["new_entity_counts"],
            "new_id_set_sha256": first["new_id_set_sha256"],
            "new_id_order_sha256": first["new_id_order_sha256"],
            "new_record_set_sha256": first["new_record_set_sha256"],
            "final_records": len(first["records"]),
            "final_id_set_sha256": first["final_id_set_sha256"],
            "final_id_order_sha256": first["final_id_order_sha256"],
            "final_record_set_sha256": first["final_record_set_sha256"],
            "final_line_sequence_sha256": first["final_line_sequence_sha256"],
            "jsonl": first["jsonl"],
            "csv": first["csv"],
        },
        "source_and_topology": {
            "source": {"path": SOURCE, "bytes": FROZEN_IDENTITIES[SOURCE][0], "sha256": FROZEN_IDENTITIES[SOURCE][1], "physical_lines": SOURCE_LINES},
            "unit_id": UNIT_ID,
            "segments": len(first["segments"]),
            "segment_ranges": [f"{item['start']}-{item['end']}" for item in first["segments"]],
            "topics": len(TOPIC_DEFS),
            "present_surfaces": len(first["surfaces"]),
            "present_surface_counts": dict(sorted(surface_counts.items())),
            "exercise_hint_solution_sets": 6,
            "proof_statement_pairs": 10,
            "lab_surface_range": "516-562",
            "relation_count": first["relation_count"],
            "definition_discovery": "three live defn environments",
        },
        "lab": {
            "schema": first["lab"]["schema"],
            "result": first["lab"]["result"],
            "row_count": len(first["lab"]["rows"]),
            "methods": sorted(first["lab"]["final"]),
            "iterations": first["lab"]["parameters"]["iterations"],
            "checkpoints": first["lab"]["parameters"]["checkpoints"],
            "artifacts": {path: {"bytes": identity[0], "sha256": identity[1]} for path, identity in FROZEN_IDENTITIES.items() if path.startswith("labs/")},
            "upstream_contact": first["lab"]["upstream_contact"],
        },
        "independent_validation": {
            "passes_required": 2,
            "passes_completed": 2,
            "identities": [{"run": 1, **first_identity}, {"run": 2, **second_identity}],
        },
        "deterministic_regeneration": {
            "runs_required": 2,
            "runs_completed": len(regenerations),
            "input_dataset_match": not args.skip_regeneration,
            "generator_stdout_receipt_consistent": True,
            "identities": regenerations,
        },
        "extension_receipt": {
            "path": args.extension_receipt.relative_to(ROOT).as_posix() if args.extension_receipt.resolve().is_relative_to(ROOT.resolve()) else str(args.extension_receipt.resolve()),
            "bytes": args.extension_receipt.stat().st_size,
            "sha256": digest(args.extension_receipt.read_bytes()),
            "schema": extension_receipt["schema"],
        },
    }
    write_receipt(args.receipt, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
