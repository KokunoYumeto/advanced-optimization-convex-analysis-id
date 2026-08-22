#!/usr/bin/env python3
"""Idempotently extend the O015 stable-ID backend through Habring Chapter 6.

The Chapter 5 generator is the deterministic baseline.  This extension
rebuilds that baseline, proves the frozen Chapter 6 evidence, replaces only
Chapter 6 records, and writes the lossless JSONL/CSV pair.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_GENERATOR = ROOT / "qa" / "extend_backend_ch05.py"
SCHEMA_PATH = ROOT / "backend" / "backend_schema.json"
JSONL_PATH = ROOT / "backend" / "records.jsonl"
CSV_PATH = ROOT / "backend" / "records.csv"
LEDGER_PATH = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
STRUCTURE_REPORT_PATH = ROOT / "qa" / "ACCELERATION_STRUCTURE_REPORT.json"
SOLVER_RESULTS_PATH = ROOT / "qa" / "ACCELERATION_SOLVER_RESULTS.json"

RECORDED_AT = "2026-08-22T06:30:00Z"
WORKFLOW = "o015-habring-ch06-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

SOURCE_PATH = "authority/habring/source-v1/acceleration.tex"
TARGET_PATH = "source/id-ID/habring-06-akselerasi-id.tex"
WRAPPER_PATH = "source/id-ID/D90-HAB-06-akselerasi-id.tex"
OUTPUT_PDF_PATH = "output/pdf/D90-HAB-06-akselerasi-id.pdf"
TEXT_PATH = "qa/D90-HAB-06-akselerasi-id.txt"
BUILD_LOG_PATH = "build/habring-unit-06-id/D90-HAB-06-akselerasi-id.log"

EXPECTED_SOURCE_SHA256 = "2ff1e10e9421c0fe01a09140e3e230cb2d3728c30c572bb6ca5513b229f1e605"
EXPECTED_TARGET_SHA256 = "b1e27d912bc94722ec1c33257598c074eec8a6f5bf81f43b8946f85b48f4c35a"
EXPECTED_WRAPPER_SHA256 = "46903dd6b6ff8c845624931d37d9b24fd37cd89f0bf77601ba11539c59dfd5b9"
EXPECTED_PDF_SHA256 = "cb9edf46d8d2582591ad3114f9a2b316073825dfd48079d12560793ad4bca0a0"
EXPECTED_BUILD_LOG_SHA256 = "0775c19ecd2e8356e7b33bd50c30871f233e0c7d05dd703ba2ec19a4f7f560f0"
EXPECTED_TEXT_SHA256 = "d2679e94ce7e44cdcf183b17e73295b5b5093a1612b2460c0c6ecba512431cda"
EXPECTED_STRUCTURE_REPORT_SHA256 = "e82f254fb7e69d498162ffcdfb70fe7d4929556351f892872bb8e65da3715b4b"
EXPECTED_SOLVER_RESULTS_SHA256 = "135ded1ed0f4f3ca70616822d8856a85d3747458c9ca6e765dab72a11d3b88f0"
EXPECTED_FORMULA_MANIFEST_SHA256 = "886d80e0a759977c0c176d9b97e595b4c3515ecd52446a8c8b714146a9be3f4a"
EXPECTED_LEDGER_IDS = [f"O015-HAB-ADV-{number:04d}" for number in range(39, 50)]
GENERATED_CONCEPT_IDS = {
    "concept.first-order-complexity-lower-bound",
    "concept.gradient-flow",
    "concept.polyak-heavy-ball-method",
    "concept.inertial-gradient-step",
    "concept.spectral-radius",
    "concept.gelfand-spectral-radius-formula",
    "concept.spectral-radius-stability",
    "concept.heavy-ball-linearization",
    "concept.schur-jury-stability",
    "concept.heavy-ball-local-convergence",
    "concept.heavy-ball-minimax-parameters",
    "concept.nesterov-acceleration",
    "concept.fista",
    "concept.fista-momentum-sequence",
    "concept.fundamental-proximal-gradient-inequality",
    "concept.fista-rate",
}
GENERATED_TERM_IDS = {
    "term.first-order-method",
    "term.gradient-flow",
    "term.polyak-heavy-ball-method",
    "term.inertia-term",
    "term.spectral-radius",
    "term.jordan-normal-form",
    "term.schur-jury-criterion",
    "term.worst-case-spectral-radius",
    "term.nesterov-acceleration",
    "term.fista",
    "term.fast-proximal-gradient-method",
    "term.inertia-parameter",
    "term.fundamental-proximal-gradient-inequality",
}


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), sha256(data)


def normalized_slice(relative: str, start: int, end: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid slice {relative}:{start}-{end}")
    data = (("\n".join(lines[start - 1 : end])) + "\n").encode("utf-8")
    return len(data), sha256(data)


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


def artifact(record_id: str, artifact_kind: str, path: str, **extra: Any) -> dict[str, Any]:
    size, digest = file_info(path)
    record = common("artifact", record_id, "current")
    record.update(
        {
            "artifact_kind": artifact_kind,
            "path": path,
            "bytes": size,
            "sha256": digest,
            "hash_algorithm": "sha256-raw-bytes",
        }
    )
    record.update(extra)
    return record


# Reconstruct the admitted Chapter 3--5 baseline before extending it.
subprocess.run(
    [sys.executable, str(BASE_GENERATOR)],
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
)

schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
records = [
    json.loads(line)
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()
    if line
]


# Prove that every frozen Chapter 6 witness still has its admitted identity.
structure = json.loads(STRUCTURE_REPORT_PATH.read_text(encoding="utf-8"))
solver = json.loads(SOLVER_RESULTS_PATH.read_text(encoding="utf-8"))
if structure.get("result") != "pass" or structure.get("failures") != []:
    raise ValueError("Chapter 6 structure report is not a clean pass")
if structure.get("source", {}).get("sha256") != EXPECTED_SOURCE_SHA256:
    raise ValueError("Chapter 6 authority hash differs from admitted evidence")
if structure.get("target", {}).get("sha256") != EXPECTED_TARGET_SHA256:
    raise ValueError("Chapter 6 target hash differs from admitted evidence")
if structure.get("environment_count") != 99:
    raise ValueError("Chapter 6 environment closure differs from 99")
if not structure.get("environment_topology_equal"):
    raise ValueError("Chapter 6 ordered environment topology is not equal")
if structure.get("source_labels") != structure.get("target_labels") or len(
    structure.get("target_labels", [])
) != 7:
    raise ValueError("Chapter 6 seven-label closure differs")
if structure.get("segments") != [
    f"d90.hab.v1.ch06.seg{order:04d}" for order in range(1, 13)
]:
    raise ValueError("Chapter 6 segment closure differs from 12 stable IDs")
references = structure.get("cross_references", {})
if references.get("cref_count") != 4 or references.get("eqref_count") != 4:
    raise ValueError("Chapter 6 cross-reference closure differs from 4 cref + 4 eqref")
if references.get("source_cref") != references.get("target_cref"):
    raise ValueError("Chapter 6 cref order differs")
if references.get("source_eqref") != references.get("target_eqref"):
    raise ValueError("Chapter 6 eqref order differs")
if structure.get("formula_delta_manifest_sha256") != EXPECTED_FORMULA_MANIFEST_SHA256:
    raise ValueError("Chapter 6 formula-delta manifest differs")
if structure.get("required_correction_event_count") != 11:
    raise ValueError("Chapter 6 correction-event count differs")
ledger_closure = structure.get("integrated_ledger", {})
if ledger_closure.get("required_ids") != EXPECTED_LEDGER_IDS:
    raise ValueError("Chapter 6 correction-ledger ID closure differs")
if not ledger_closure.get("exact_records_match_proposal"):
    raise ValueError("Chapter 6 integrated ledger does not match the proposal")
for counts in structure.get("absent_surface_counts", {}).values():
    if counts != {"source": 0, "target": 0}:
        raise ValueError("Chapter 6 contains a forbidden citation/media/input surface")
if solver.get("result") != "PASS":
    raise ValueError("Chapter 6 solver report is not a pass")
for check in solver.get("checks", {}).values():
    if check.get("result") != "PASS":
        raise ValueError("Chapter 6 solver subcheck is not a pass")

expected_files = {
    SOURCE_PATH: (18873, EXPECTED_SOURCE_SHA256),
    TARGET_PATH: (24690, EXPECTED_TARGET_SHA256),
    WRAPPER_PATH: (5491, EXPECTED_WRAPPER_SHA256),
    OUTPUT_PDF_PATH: (392662, EXPECTED_PDF_SHA256),
    BUILD_LOG_PATH: (97942, EXPECTED_BUILD_LOG_SHA256),
    TEXT_PATH: (37033, EXPECTED_TEXT_SHA256),
    "qa/ACCELERATION_STRUCTURE_REPORT.json": (37873, EXPECTED_STRUCTURE_REPORT_SHA256),
    "qa/ACCELERATION_SOLVER_RESULTS.json": (37060, EXPECTED_SOLVER_RESULTS_SHA256),
}
for relative, expected in expected_files.items():
    if file_info(relative) != expected:
        raise ValueError(f"Chapter 6 frozen artifact differs: {relative}")

build_log = (ROOT / BUILD_LOG_PATH).read_text(encoding="utf-8", errors="replace")
for forbidden in ("! LaTeX Error:", "undefined references", "Missing character:"):
    if forbidden in build_log:
        raise ValueError(f"Chapter 6 build log contains forbidden diagnostic: {forbidden}")
if "Output written on" not in build_log or "(15 pages" not in build_log:
    raise ValueError("Chapter 6 build log does not prove a 15-page output")


# Baseline reconstruction already removes later records; this narrow filter is
# retained so the extension is idempotent even if its baseline policy changes.
def is_generated(record: dict[str, Any]) -> bool:
    record_id = record["id"]
    return (
        record_id in GENERATED_CONCEPT_IDS
        or record_id in GENERATED_TERM_IDS
        or record_id == "unit.habring.v1.ch06"
        or record_id.startswith("d90.hab.v1.ch06.")
        or record_id.startswith("surface.habring.v1.ch06.")
        or record_id.startswith("qa.o015.ch06.")
        or record_id.startswith("relation.unit.ch06-")
        or record_id.startswith("relation.segment.ch06-")
        or record_id.startswith("relation.surface.ch06-")
        or record_id.startswith("artifact.habring.")
        and record_id.endswith("-ch06")
        or record_id in {
            "rights.o015-habring-ch06-source",
            "rights.o015-habring-id-ch06",
            "rights.o015-acceleration-solver-validation",
            "relation.unit.root-contains-ch06",
            "relation.unit.ch05-precedes-ch06",
            "artifact.o015.backend-generator-ch06",
        }
        or record_id.startswith("correction.o015-hab-adv-")
        and 39 <= int(record_id.rsplit("-", 1)[1]) <= 49
    )


records = [record for record in records if not is_generated(record)]


# Component-specific rights.
rights_specs = [
    (
        "rights.o015-habring-ch06-source",
        "o015-habring-ch06-text",
        SOURCE_PATH,
        "admitted",
        "Chapter 6 authority source; corrections are explicit records.",
        True,
    ),
    (
        "rights.o015-habring-id-ch06",
        "o015-habring-id-unit-06",
        TARGET_PATH,
        "derivative",
        "Independent id-ID translation of Chapter 6 and its standalone wrapper.",
        True,
    ),
]
for record_id, component_id, path, status, notes, translation_permitted in rights_specs:
    right = common("rights", record_id, status)
    right.update(
        {
            "component_id": component_id,
            "path": path,
            "source_authority_id": "o015-habring-arxiv-2607.11664v1",
            "rights_expression": "CC BY 4.0",
            "authority_url": "https://arxiv.org/abs/2607.11664v1",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "translation_permitted": translation_permitted,
            "required_handling": [
                "attribute Andreas Habring",
                "link CC BY 4.0",
                "identify translation and corrections",
                "no implied endorsement",
            ],
            "notes": notes,
        }
    )
    records.append(right)

solver_right = common("rights", "rights.o015-acceleration-solver-validation", "admitted")
solver_right.update(
    {
        "component_id": "o015-solver-validation-06",
        "path": "qa/validate_acceleration_unit.py",
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": "qa/validate_acceleration_unit.py",
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with results", "no proprietary runtime"],
        "notes": "Uses NumPy/SciPy and open SLSQP for Chapter 6 computations.",
    }
)
records.append(solver_right)


# Chapter 6 unit.
unit = common("unit", "unit.habring.v1.ch06", "built")
unit.update(
    {
        "edition_id": "edition.habring.convex-optimization.id-id.v1",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "parent_id": "unit.habring.v1",
        "unit_kind": "chapter",
        "order": 6,
        "source_local_id": "chapter-6",
        "source_local_label": "6 — Acceleration",
        "target_local_label": "6 — Akselerasi",
        "source_locator": f"{SOURCE_PATH}:1-404",
        "target_locator": f"{TARGET_PATH}:1-539",
        "rights_id": "rights.o015-habring-id-ch06",
        "translation_state": "built",
    }
)
records.append(unit)


# Locale-neutral concepts and accepted id-ID terminology.
concept_specs = [
    ("concept.first-order-complexity-lower-bound", "finite-step lower bound for first-order smooth convex optimization", ["concept.gradient"]),
    ("concept.gradient-flow", "gradient-flow differential equation", ["concept.gradient"]),
    ("concept.polyak-heavy-ball-method", "Polyak heavy-ball inertial gradient method", ["concept.gradient-flow", "concept.gradient"]),
    ("concept.inertial-gradient-step", "gradient step with an inertial displacement", ["concept.gradient"]),
    ("concept.spectral-radius", "spectral radius of a finite-dimensional linear operator", []),
    ("concept.gelfand-spectral-radius-formula", "Gelfand spectral-radius formula", ["concept.spectral-radius"]),
    ("concept.spectral-radius-stability", "spectral-radius characterization of discrete linear stability", ["concept.gelfand-spectral-radius-formula"]),
    ("concept.heavy-ball-linearization", "two-state heavy-ball linearization at a stationary minimizer", ["concept.polyak-heavy-ball-method", "concept.spectral-radius-stability"]),
    ("concept.schur-jury-stability", "Schur–Jury stability criterion for a real monic quadratic", ["concept.spectral-radius"]),
    ("concept.heavy-ball-local-convergence", "local geometric convergence of heavy ball near a positive-definite stationary minimizer", ["concept.heavy-ball-linearization", "concept.schur-jury-stability", "concept.strong-convexity"]),
    ("concept.heavy-ball-minimax-parameters", "minimax heavy-ball spectral-radius parameters over a curvature interval", ["concept.heavy-ball-local-convergence", "concept.schur-jury-stability"]),
    ("concept.nesterov-acceleration", "Nesterov-type inertial acceleration", ["concept.proximal-gradient-method"]),
    ("concept.fista", "fast iterative shrinkage-thresholding algorithm", ["concept.nesterov-acceleration", "concept.proximal-gradient-method"]),
    ("concept.fista-momentum-sequence", "FISTA momentum sequence and its linear lower bound", ["concept.fista"]),
    ("concept.fundamental-proximal-gradient-inequality", "fundamental proximal-gradient three-point inequality", ["concept.proximal-gradient-method", "concept.l-smoothness-descent-lemma"]),
    ("concept.fista-rate", "O(1/k^2) FISTA objective-value rate", ["concept.fista-momentum-sequence", "concept.fundamental-proximal-gradient-inequality"]),
]
for concept_id, label, prerequisites in concept_specs:
    concept = common("concept", concept_id, "current")
    concept.update(
        {
            "canonical_label": label,
            "prerequisite_ids": prerequisites,
            "domain": "convex and nonsmooth optimization",
        }
    )
    records.append(concept)

term_specs = [
    ("term.first-order-method", "concept.first-order-complexity-lower-bound", "first-order method", "metode orde pertama", [], "d90.hab.v1.ch06.seg0001"),
    ("term.gradient-flow", "concept.gradient-flow", "gradient flow", "aliran gradien", [], "d90.hab.v1.ch06.seg0002"),
    ("term.polyak-heavy-ball-method", "concept.polyak-heavy-ball-method", "Polyak's heavy ball method", "metode bola berat Polyak", [], "d90.hab.v1.ch06.seg0002"),
    ("term.inertia-term", "concept.inertial-gradient-step", "inertia term", "suku inersia", [], "d90.hab.v1.ch06.seg0002"),
    ("term.spectral-radius", "concept.spectral-radius", "spectral radius", "radius spektral", [], "d90.hab.v1.ch06.seg0003"),
    ("term.jordan-normal-form", "concept.gelfand-spectral-radius-formula", "Jordan normal form", "bentuk normal Jordan", [], "d90.hab.v1.ch06.seg0003"),
    ("term.schur-jury-criterion", "concept.schur-jury-stability", "Schur–Jury criterion", "kriteria Schur–Jury", [], "d90.hab.v1.ch06.seg0007"),
    ("term.worst-case-spectral-radius", "concept.heavy-ball-minimax-parameters", "worst-case spectral radius", "radius spektral kasus terburuk", [], "d90.hab.v1.ch06.seg0007"),
    ("term.nesterov-acceleration", "concept.nesterov-acceleration", "Nesterov acceleration", "akselerasi Nesterov", [], "d90.hab.v1.ch06.seg0008"),
    ("term.fista", "concept.fista", "fast iterative shrinkage-thresholding algorithm", "FISTA", ["algoritma penyusutan-ambang iteratif cepat"], "d90.hab.v1.ch06.seg0008"),
    ("term.fast-proximal-gradient-method", "concept.fista", "fast proximal gradient method", "metode gradien proksimal cepat", [], "d90.hab.v1.ch06.seg0008"),
    ("term.inertia-parameter", "concept.fista-momentum-sequence", "inertia parameter", "parameter inersia", [], "d90.hab.v1.ch06.seg0008"),
    ("term.fundamental-proximal-gradient-inequality", "concept.fundamental-proximal-gradient-inequality", "fundamental prox-grad inequality", "ketaksamaan fundamental gradien proksimal", [], "d90.hab.v1.ch06.seg0010"),
]
for term_id, concept_id, source_term, preferred, variants, segment_id in term_specs:
    term = common("term", term_id, "accepted")
    term.update(
        {
            "concept_id": concept_id,
            "locale": "id-ID",
            "source_term": source_term,
            "preferred": preferred,
            "variants": variants,
            "rejected_forms": [],
            "scope": "convex and nonsmooth optimization",
            "register": "formal",
            "evidence_segment_ids": [segment_id],
            "examples": [preferred],
            "rights_id": "rights.o015-habring-id-ch06",
        }
    )
    records.append(term)


# Twelve exact, contiguous reader-facing segments.
segment_specs = [
    (1, 2, 11, 4, 12, "First-order lower bound", "Batas bawah orde pertama", ["concept.first-order-complexity-lower-bound"]),
    (2, 13, 46, 15, 48, "Heavy-ball motivation and update", "Motivasi dan pembaruan bola berat", ["concept.gradient-flow", "concept.polyak-heavy-ball-method", "concept.inertial-gradient-step"]),
    (3, 47, 116, 51, 122, "Gelfand spectral-radius formula", "Rumus radius spektral Gelfand", ["concept.spectral-radius", "concept.gelfand-spectral-radius-formula"]),
    (4, 118, 133, 125, 140, "Spectral-radius stability corollary", "Korolari kestabilan radius spektral", ["concept.spectral-radius-stability"]),
    (5, 135, 152, 143, 172, "Heavy-ball local convergence theorem", "Teorema konvergensi lokal bola berat", ["concept.heavy-ball-local-convergence", "concept.heavy-ball-minimax-parameters"]),
    (6, 153, 224, 175, 257, "Exact state recurrence and linearization", "Rekurensi keadaan eksak dan linearisasi", ["concept.heavy-ball-linearization"]),
    (7, 225, 259, 260, 330, "Characteristic roots, local stability, and minimax parameters", "Akar karakteristik, kestabilan lokal, dan parameter minimaks", ["concept.schur-jury-stability", "concept.heavy-ball-local-convergence", "concept.heavy-ball-minimax-parameters"]),
    (8, 261, 275, 333, 347, "Nesterov acceleration and FISTA update", "Akselerasi Nesterov dan pembaruan FISTA", ["concept.nesterov-acceleration", "concept.fista"]),
    (9, 277, 289, 350, 365, "FISTA momentum sequence", "Barisan momentum FISTA", ["concept.fista-momentum-sequence"]),
    (10, 291, 332, 368, 424, "Fundamental proximal-gradient inequality", "Ketaksamaan fundamental gradien proksimal", ["concept.fundamental-proximal-gradient-inequality"]),
    (11, 333, 339, 427, 435, "FISTA convergence theorem", "Teorema konvergensi FISTA", ["concept.fista-rate"]),
    (12, 340, 404, 438, 539, "FISTA energy proof and O(1/k^2) rate", "Bukti energi FISTA dan laju O(1/k^2)", ["concept.fista-rate", "concept.fundamental-proximal-gradient-inequality"]),
]
for order, s_start, s_end, t_start, t_end, source_label, target_label, concept_ids in segment_specs:
    segment_id = f"d90.hab.v1.ch06.seg{order:04d}"
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, s_start, s_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, t_start, t_end)
    segment = common("segment", segment_id, "current")
    segment.update(
        {
            "unit_id": "unit.habring.v1.ch06",
            "order": order,
            "source_local_id": f"chapter-6-lines-{s_start}-{s_end}",
            "source_local_label": source_label,
            "target_local_label": target_label,
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "source_language": "en",
            "source_path": SOURCE_PATH,
            "source_locator": f"{SOURCE_PATH}:{s_start}-{s_end}",
            "source_line_start": s_start,
            "source_line_end": s_end,
            "source_bytes": source_bytes,
            "source_content_sha256": source_digest,
            "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
            "target_language": "id",
            "target_locale": "id-ID",
            "target_path": TARGET_PATH,
            "target_locator": f"{TARGET_PATH}:{t_start}-{t_end}",
            "target_line_start": t_start,
            "target_line_end": t_end,
            "target_bytes": target_bytes,
            "target_content_sha256": target_digest,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "built",
            "structural_review_state": "passed",
            "mathematical_review_state": "correction_audited_solver_checked_independent_rereview_passed",
            "language_review_state": "not_recorded",
            "concept_ids": concept_ids,
            "rights_id": "rights.o015-habring-id-ch06",
            "evidence_event_ids": [
                "qa.o015.ch06.structure",
                "qa.o015.ch06.formula-delta",
                "qa.o015.ch06.solver",
                "qa.o015.ch06.build",
                "qa.o015.ch06.math-rereview",
                "qa.o015.ch06.visual",
                "qa.o015.ch06.accessibility",
            ],
        }
    )
    records.append(segment)


# The source's commented editorial exercise is retained as a rendered prompt.
source_bytes, source_digest = normalized_slice(SOURCE_PATH, 259, 259)
target_bytes, target_digest = normalized_slice(TARGET_PATH, 329, 330)
prompt = common("learning_surface", "surface.habring.v1.ch06.prompt01", "present")
prompt.update(
    {
        "unit_id": "unit.habring.v1.ch06",
        "surface_type": "verification_prompt",
        "presence": "present",
        "order": 1,
        "source_local_id": "chapter-6-informal-prompt-1",
        "source_local_label": "Local convergence and optimal-parameter verification exercise",
        "target_local_label": "Latihan verifikasi kestabilan dan parameter minimaks",
        "related_segment_ids": ["d90.hab.v1.ch06.seg0007"],
        "concept_id": "concept.heavy-ball-minimax-parameters",
        "source_path": SOURCE_PATH,
        "source_line_start": 259,
        "source_line_end": 259,
        "source_locator": f"{SOURCE_PATH}:259-259",
        "source_bytes": source_bytes,
        "source_content_sha256": source_digest,
        "target_path": TARGET_PATH,
        "target_line_start": 329,
        "target_line_end": 330,
        "target_locator": f"{TARGET_PATH}:329-330",
        "target_bytes": target_bytes,
        "target_content_sha256": target_digest,
        "hash_normalization": "sha256-utf8-lf-final-newline",
        "disposition": "promoted_source_editorial_todo_to_rendered_self_study_verification_prompt",
        "hint_state": "absent_in_source",
        "answer_state": "absent_in_source",
        "solution_state": "absent_in_source",
        "translation_state": "built",
        "rights_id": "rights.o015-habring-id-ch06",
    }
)
records.append(prompt)

for surface_type in ("hint", "answer", "solution"):
    surface = common(
        "learning_surface",
        f"surface.habring.v1.ch06.{surface_type}-inventory",
        "source_absent",
    )
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch06",
            "surface_type": surface_type,
            "presence": "absent",
            "count": 0,
            "absence_evidence": "qa/ACCELERATION_STRUCTURE_REPORT.json",
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
            "rights_id": "rights.o015-habring-id-ch06",
        }
    )
    records.append(surface)


# Convert the exact Chapter 6 adverse-ledger closure to correction records.
ledger = [
    json.loads(line)
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
events = {entry["event_id"]: entry for entry in ledger}
correction_specs = {
    39: (3, 10, [1]),
    40: (49, 116, [3]),
    41: (118, 133, [4]),
    42: (137, 152, [5]),
    43: (153, 224, [6]),
    44: (225, 256, [7]),
    45: (137, 259, [5, 7]),
    46: (261, 275, [8]),
    47: (291, 332, [10]),
    48: (333, 404, [11, 12]),
    49: (33, 338, [2, 3, 4, 8, 10, 11]),
}
for number in range(39, 50):
    event_id = f"O015-HAB-ADV-{number:04d}"
    event = events.get(event_id)
    if event is None:
        raise ValueError(f"missing ledger event {event_id}")
    source_start, source_end, segment_orders = correction_specs[number]
    correction = common("correction", f"correction.o015-hab-adv-{number:04d}", "applied")
    correction.update(
        {
            "source_event_id": event_id,
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "affected_unit_ids": ["unit.habring.v1.ch06"],
            "affected_segment_ids": [
                f"d90.hab.v1.ch06.seg{order:04d}" for order in segment_orders
            ],
            "source_path": SOURCE_PATH,
            "source_line_start": source_start,
            "source_line_end": source_end,
            "source_locator": f"{SOURCE_PATH}:{source_start}-{source_end}",
            "surface": event["surface"],
            "source_issue": event["source_issue"],
            "target_action": event["target_action"],
            "correction_class": event["class"],
            "disposition": "applied",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.o015.adverse-ledger",
        }
    )
    records.append(correction)


# Chapter 6 artifacts and their exact byte identities.
records.extend(
    [
        artifact("artifact.habring.source-ch06", "source_tex", SOURCE_PATH, source_edition_id="edition.habring.convex-optimization.arxiv-2607-11664v1", rights_id="rights.o015-habring-ch06-source"),
        artifact("artifact.habring.target-ch06", "target_tex", TARGET_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch06"),
        artifact("artifact.habring.target-wrapper-ch06", "target_tex", WRAPPER_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch06"),
        artifact("artifact.habring.structure-report-ch06", "qa_report", "qa/ACCELERATION_STRUCTURE_REPORT.json", toolchain="qa/audit_acceleration_unit.py", formula_delta_manifest_sha256=EXPECTED_FORMULA_MANIFEST_SHA256),
        artifact("artifact.habring.structure-audit-ch06", "qa_source", "qa/audit_acceleration_unit.py", toolchain="Python 3 standard library"),
        artifact("artifact.habring.solver-results-ch06", "qa_report", "qa/ACCELERATION_SOLVER_RESULTS.json", toolchain="Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1", rights_id="rights.o015-acceleration-solver-validation"),
        artifact("artifact.habring.solver-validator-ch06", "qa_source", "qa/validate_acceleration_unit.py", toolchain="Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1", rights_id="rights.o015-acceleration-solver-validation"),
        artifact("artifact.habring.build-log-ch06", "build_receipt", BUILD_LOG_PATH, build_event_id="qa.o015.ch06.build", toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber"),
        artifact("artifact.habring.target-pdf-ch06", "reader_pdf", OUTPUT_PDF_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch06", pages=15, build_event_id="qa.o015.ch06.build", toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber", accessibility="searchable id-ID PDF; untagged", input_artifact_ids=["artifact.habring.target-wrapper-ch06", "artifact.habring.target-ch06", "artifact.habring.target-macros", "artifact.habring.target-class", "artifact.habring.references-bib"]),
        artifact("artifact.habring.target-text-ch06", "qa_extract", TEXT_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", source_artifact_id="artifact.habring.target-pdf-ch06"),
        artifact("artifact.o015.backend-generator-ch06", "qa_source", "qa/extend_backend_ch06.py", toolchain="Python 3 standard library"),
    ]
)


# Nine-event Chapter 6 evidence topology; language review remains not recorded.
qa_specs = [
    {"id": "qa.o015.ch06.source-freeze", "status": "pass", "event_type": "source", "result": "pass", "witness_artifact_ids": ["artifact.habring.source-ch06"], "authority_id": "o015-habring-arxiv-2607.11664v1", "source_sha256": EXPECTED_SOURCE_SHA256},
    {"id": "qa.o015.ch06.structure", "status": "pass", "event_type": "topology", "result": "pass", "witness_artifact_ids": ["artifact.habring.structure-report-ch06"], "environment_topology_equal": True, "environment_count": 99, "environment_counts": structure["environment_counts"], "failures": [], "segment_count": 12, "label_occurrences_preserved": 7, "cref_occurrences_preserved": 4, "eqref_occurrences_preserved": 4, "informal_prompts_preserved": 1, "citations": 0, "figures": 0, "assets": 0, "footnotes": 0, "inputs": 0},
    {"id": "qa.o015.ch06.formula-delta", "status": "pass", "event_type": "mathematics", "result": "pass", "witness_artifact_ids": ["artifact.habring.structure-report-ch06"], "formula_delta_manifest_sha256": EXPECTED_FORMULA_MANIFEST_SHA256, "source_formula_surfaces": 166, "target_formula_surfaces": 241, "formula_delta_blocks": 32, "correction_events": 11, "required_correction_surfaces": 47, "disposition": "All substantive mathematical deltas are correction-ledger bound."},
    {"id": "qa.o015.ch06.solver", "status": "pass", "event_type": "computation", "result": "pass", "witness_artifact_ids": ["artifact.habring.solver-results-ch06", "artifact.habring.solver-validator-ch06"], "checks": ["Gelfand formula including the zero-radius nilpotent branch", "heavy-ball companion roots, Schur–Jury stability, and minimax parameters", "FISTA fundamental inequality, Lyapunov monotonicity, and explicit O(1/k^2) bound"], "python": "3.13.9", "numpy": "2.4.4", "scipy": "1.17.1"},
    {"id": "qa.o015.ch06.build", "status": "pass", "event_type": "build", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-pdf-ch06", "artifact.habring.build-log-ch06"], "toolchain": "pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber", "pages": 15, "page_size": "A4", "deterministic_rebuild": "byte-identical", "errors": [], "undefined_references": 0, "replacement_glyphs": 0, "contained_overfull_math_boxes_pt": [7.08029, 2.99966]},
    {"id": "qa.o015.ch06.visual", "status": "pass", "event_type": "visual", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-pdf-ch06"], "pages_inspected": 15, "method": "All latest pages rendered and contact/full-page inspected after two byte-identical fixed-epoch builds.", "localization_check": "Equation cross-reference names render in Indonesian.", "findings": [], "contained_non_clipping_math_overfull_boxes": 2},
    {"id": "qa.o015.ch06.accessibility", "status": "pass_with_limitation", "event_type": "accessibility", "result": "pass_with_limitation", "witness_artifact_ids": ["artifact.habring.target-pdf-ch06", "artifact.habring.target-text-ch06"], "checks": ["PDF language metadata is id-ID.", "PDF is unencrypted and searchable.", "Text extraction is retained as an exact artifact.", "No figures require alternative text in this chapter."], "limitations": ["PDF is untagged."]},
    {"id": "qa.o015.ch06.math-rereview", "status": "pass", "event_type": "mathematics", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-ch06", "artifact.habring.structure-report-ch06", "artifact.habring.solver-results-ch06"], "verified_at": RECORDED_AT, "target_sha256": EXPECTED_TARGET_SHA256, "review_outcome": {"p1": 0, "p2": 0, "p3": 0}, "scope": "Independent final delta rereview of the corrected lower bound, heavy-ball minimax proof, and exact structural/reference closure."},
    {"id": "qa.o015.ch06.language", "status": "not_recorded", "event_type": "language", "result": "not_recorded", "witness_artifact_ids": [], "gap": "No independent Indonesian language review is recorded."},
]
for spec in qa_specs:
    qa = common("qa_event", spec["id"], spec["status"])
    qa.update(
        {
            "unit_id": "unit.habring.v1.ch06",
            **{key: value for key, value in spec.items() if key not in {"id", "status"}},
        }
    )
    records.append(qa)


# Unit hierarchy, source order, dependencies, concept topology, and prompt.
relation_specs: list[tuple[str, str, str, str, str]] = [
    ("relation.unit.root-contains-ch06", "contains", "unit.habring.v1", "unit.habring.v1.ch06", "Source Chapter 6."),
    ("relation.unit.ch05-precedes-ch06", "precedes", "unit.habring.v1.ch05", "unit.habring.v1.ch06", "Contiguous admitted source order."),
    ("relation.unit.ch06-depends-on-ch05", "depends-on", "unit.habring.v1.ch06", "unit.habring.v1.ch05", "FISTA accelerates the proximal-gradient construction."),
    ("relation.unit.ch06-prerequisite-gradient", "prerequisite", "unit.habring.v1.ch06", "concept.gradient", "Gradient-flow and inertial-gradient prerequisite."),
    ("relation.unit.ch06-prerequisite-strong-convexity", "prerequisite", "unit.habring.v1.ch06", "concept.strong-convexity", "Heavy-ball curvature prerequisite."),
    ("relation.unit.ch06-prerequisite-proximal-gradient", "prerequisite", "unit.habring.v1.ch06", "concept.proximal-gradient-method", "FISTA prerequisite."),
]
for order in range(1, 13):
    relation_specs.append((f"relation.unit.ch06-contains-seg{order:04d}", "contains", "unit.habring.v1.ch06", f"d90.hab.v1.ch06.seg{order:04d}", "Ordered reader-facing translation segment."))
relation_specs.extend(
    [
        ("relation.segment.ch06-seg0001-proves-first-order-lower-bound", "proves", "d90.hab.v1.ch06.seg0001", "concept.first-order-complexity-lower-bound", "Finite-step smooth-convex lower bound."),
        ("relation.segment.ch06-seg0002-defines-heavy-ball", "defines", "d90.hab.v1.ch06.seg0002", "concept.polyak-heavy-ball-method", "ODE motivation and inertial update."),
        ("relation.segment.ch06-seg0003-proves-gelfand", "proves", "d90.hab.v1.ch06.seg0003", "concept.gelfand-spectral-radius-formula", "Complex Jordan proof with nilpotent branch."),
        ("relation.segment.ch06-seg0004-proves-spectral-stability", "proves", "d90.hab.v1.ch06.seg0004", "concept.spectral-radius-stability", "Equivalence and finite-prefix geometric bound."),
        ("relation.segment.ch06-seg0005-defines-heavy-ball-rate", "defines", "d90.hab.v1.ch06.seg0005", "concept.heavy-ball-local-convergence", "Local convergence theorem and rate."),
        ("relation.segment.ch06-seg0006-defines-heavy-ball-linearization", "defines", "d90.hab.v1.ch06.seg0006", "concept.heavy-ball-linearization", "Exact state recurrence and Hessian remainder."),
        ("relation.segment.ch06-seg0007-proves-heavy-ball-local-convergence", "proves", "d90.hab.v1.ch06.seg0007", "concept.heavy-ball-local-convergence", "Schur–Jury and equivalent-norm perturbation proof."),
        ("relation.segment.ch06-seg0007-proves-heavy-ball-minimax", "proves", "d90.hab.v1.ch06.seg0007", "concept.heavy-ball-minimax-parameters", "Scaled Schur–Jury lower bound and equality case."),
        ("relation.segment.ch06-seg0008-defines-fista", "defines", "d90.hab.v1.ch06.seg0008", "concept.fista", "Composite assumptions and indexed update."),
        ("relation.segment.ch06-seg0009-proves-fista-momentum-bound", "proves", "d90.hab.v1.ch06.seg0009", "concept.fista-momentum-sequence", "Inductive lower bound on t_k."),
        ("relation.segment.ch06-seg0010-proves-fundamental-inequality", "proves", "d90.hab.v1.ch06.seg0010", "concept.fundamental-proximal-gradient-inequality", "Strongly convex surrogate proof."),
        ("relation.segment.ch06-seg0011-defines-fista-rate", "defines", "d90.hab.v1.ch06.seg0011", "concept.fista-rate", "Explicit initialization-dependent rate."),
        ("relation.segment.ch06-seg0012-proves-fista-rate", "proves", "d90.hab.v1.ch06.seg0012", "concept.fista-rate", "Energy telescoping proof."),
        ("relation.surface.ch06-prompt01-exercises-heavy-ball-minimax", "exercises", "surface.habring.v1.ch06.prompt01", "concept.heavy-ball-minimax-parameters", "Rendered verification of Schur–Jury and endpoint parameters."),
    ]
)
for record_id, relation_type, source_id, target_id, note in relation_specs:
    relation = common("relation", record_id, "current")
    relation.update(
        {
            "relation_type": relation_type,
            "source_id": source_id,
            "target_id": target_id,
            "note": note,
        }
    )
    records.append(relation)


# Refresh artifact identities, then emit canonical deterministic exports.
for record in records:
    if record.get("entity_type") != "artifact":
        continue
    path = ROOT / record["path"]
    if not path.is_file():
        raise FileNotFoundError(path)
    data = path.read_bytes()
    record["bytes"] = len(data)
    record["sha256"] = sha256(data)

entity_rank = {entity_type: rank for rank, entity_type in enumerate(schema["entity_order"])}
records.sort(
    key=lambda record: (
        entity_rank.get(record["entity_type"], 10_000),
        record["id"],
    )
)
JSONL_PATH.write_text(
    "".join(canonical_json(record) + "\n" for record in records),
    encoding="utf-8",
    newline="\n",
)
with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(schema["csv_columns"])
    for record in records:
        writer.writerow(
            [
                record["schema"],
                record["schema_version"],
                record["entity_type"],
                record["id"],
                canonical_json(record),
            ]
        )

print(
    json.dumps(
        {
            "record_count": len(records),
            "jsonl": {
                "bytes": file_info("backend/records.jsonl")[0],
                "sha256": file_info("backend/records.jsonl")[1],
            },
            "csv": {
                "bytes": file_info("backend/records.csv")[0],
                "sha256": file_info("backend/records.csv")[1],
            },
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
