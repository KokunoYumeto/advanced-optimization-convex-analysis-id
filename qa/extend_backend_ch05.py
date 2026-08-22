#!/usr/bin/env python3
"""Idempotently extend the O015 stable-ID backend through Habring Chapter 5.

The Chapter 4 generator remains the deterministic baseline.  This extension
rebuilds that baseline, proves the admitted Chapter 5 evidence, replaces only
previously generated Chapter 5 records, and writes the lossless JSONL/CSV pair.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_GENERATOR = ROOT / "qa" / "extend_backend_ch04.py"
SCHEMA_PATH = ROOT / "backend" / "backend_schema.json"
JSONL_PATH = ROOT / "backend" / "records.jsonl"
CSV_PATH = ROOT / "backend" / "records.csv"
LEDGER_PATH = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
BUILD_QA_PATH = ROOT / "00_control" / "BUILD_AND_QA.md"
COMPONENT_RIGHTS_PATH = ROOT / "00_control" / "COMPONENT_RIGHTS.csv"
STRUCTURE_REPORT_PATH = ROOT / "qa" / "PROXIMAL_GRADIENT_STRUCTURE_REPORT.json"
SOLVER_RESULTS_PATH = ROOT / "qa" / "PROXIMAL_GRADIENT_SOLVER_RESULTS.json"
RECORDED_AT = "2026-08-22T05:42:27Z"
WORKFLOW = "o015-habring-ch05-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

SOURCE_PATH = "authority/habring/source-v1/proximal_gradient.tex"
TARGET_PATH = "source/id-ID/habring-05-metode-gradien-proksimal-id.tex"
WRAPPER_PATH = "source/id-ID/D90-HAB-05-metode-gradien-proksimal-id.tex"
OUTPUT_PDF_PATH = "output/pdf/D90-HAB-05-metode-gradien-proksimal-id.pdf"
TEXT_PATH = "qa/D90-HAB-05-metode-gradien-proksimal-id.txt"
BUILD_LOG_PATH = "build/habring-unit-05-id/D90-HAB-05-metode-gradien-proksimal-id.log"

EXPECTED_SOURCE_SHA256 = "59d5694742f0e2f9f46da0c1418b5fe0ff18521c49078ed29c843b6e8c701f6e"
EXPECTED_TARGET_SHA256 = "1292f09d375ff0e0ff12e7c87e673596400bb94f228db70d49f9a517b1678691"
EXPECTED_WRAPPER_SHA256 = "8c67641de7ebf2e06afefa2309c09823e78a4d3d5dbba89a28536392d82c359d"
EXPECTED_PDF_SHA256 = "6f8aa99f6d0395f3c732ed64d2b5cadd5d95ff2195e2504e959d31a3c010731d"
EXPECTED_FORMULA_MANIFEST_SHA256 = "3b910b86e304b2ba472df7fbf642db5928824ee999b551cc60f287b2c5705a3c"


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


def artifact(
    record_id: str,
    artifact_kind: str,
    path: str,
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
        }
    )
    record.update(extra)
    return record


# Reconstruct the already-admitted Chapter 3--4 baseline before extending it.
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


# Prove that the Chapter 5 evidence currently on disk is the admitted evidence.
structure = json.loads(STRUCTURE_REPORT_PATH.read_text(encoding="utf-8"))
solver = json.loads(SOLVER_RESULTS_PATH.read_text(encoding="utf-8"))
if structure.get("result") != "pass":
    raise ValueError("Chapter 5 structure report is not a pass")
if structure.get("source", {}).get("sha256") != EXPECTED_SOURCE_SHA256:
    raise ValueError("Chapter 5 authority hash differs from admitted evidence")
if structure.get("target", {}).get("sha256") != EXPECTED_TARGET_SHA256:
    raise ValueError("Chapter 5 target hash differs from admitted evidence")
if structure.get("environment_count") != 78:
    raise ValueError("Chapter 5 environment closure differs from 78")
if structure.get("segments") != [
    f"d90.hab.v1.ch05.seg{order:04d}" for order in range(1, 9)
]:
    raise ValueError("Chapter 5 segment closure differs from the eight stable IDs")
if structure.get("formula_delta_manifest_sha256") != EXPECTED_FORMULA_MANIFEST_SHA256:
    raise ValueError("Chapter 5 formula-delta manifest differs from admitted evidence")
if structure.get("correction_ledger_ids") != [
    f"O015-HAB-ADV-{number:04d}" for number in range(28, 39)
]:
    raise ValueError("Chapter 5 correction-ledger closure differs")
if solver.get("result") != "PASS":
    raise ValueError("Chapter 5 solver report is not a pass")
if file_info(SOURCE_PATH) != (18464, EXPECTED_SOURCE_SHA256):
    raise ValueError("Chapter 5 authority bytes differ")
if file_info(TARGET_PATH) != (20575, EXPECTED_TARGET_SHA256):
    raise ValueError("Chapter 5 target bytes differ")
if file_info(WRAPPER_PATH) != (4817, EXPECTED_WRAPPER_SHA256):
    raise ValueError("Chapter 5 wrapper bytes differ")
if file_info(OUTPUT_PDF_PATH) != (473685, EXPECTED_PDF_SHA256):
    raise ValueError("Chapter 5 output PDF bytes differ")

build_qa = BUILD_QA_PATH.read_text(encoding="utf-8")
for required_surface in (
    "Unit: Habring Chapter 5",
    "Admission: PASS",
    "P1=0, P2=0, P3=0",
    "Independent Indonesian language review remains `not_recorded`.",
    "It is not tagged",
):
    if required_surface not in build_qa:
        raise ValueError(f"missing Chapter 5 admission evidence: {required_surface}")

with COMPONENT_RIGHTS_PATH.open(encoding="utf-8", newline="") as handle:
    component_rights_ids = {row[0] for row in csv.reader(handle) if row}
for required_right in (
    "o015-habring-ch05-text",
    "o015-habring-id-unit-05",
    "o015-habring-id-wrapper-05",
    "o015-solver-validation-05",
):
    if required_right not in component_rights_ids:
        raise ValueError(f"missing Chapter 5 component-rights row: {required_right}")


# Remove only prior records generated by this Chapter 5 extension.
generated_concepts = {
    "concept.composite-convex-optimization",
    "concept.euclidean-shrinkage",
    "concept.gradient-mapping",
    "concept.implicit-subgradient-step",
    "concept.l-smoothness-descent-lemma",
    "concept.moreau-envelope",
    "concept.moreau-smoothing",
    "concept.proximal-computation-rules",
    "concept.proximal-gradient-fixed-point",
    "concept.proximal-gradient-method",
    "concept.proximal-gradient-rate",
    "concept.proximal-operator",
    "concept.soft-thresholding",
}
generated_terms = {
    "term.composite-objective",
    "term.euclidean-shrinkage",
    "term.gradient-mapping",
    "term.implicit-step",
    "term.l-smooth",
    "term.moreau-envelope",
    "term.prox",
    "term.proximal-gradient-method",
    "term.proximal-operator",
    "term.soft-thresholding",
}
generated_exact_ids = {
    "unit.habring.v1.ch05",
    "rights.o015-habring-ch05-source",
    "rights.o015-habring-id-ch05",
    "rights.o015-proximal-gradient-solver-validation",
    "relation.unit.root-contains-ch05",
    "relation.unit.ch04-precedes-ch05",
    "relation.unit.ch05-depends-on-ch03",
    "relation.unit.ch05-depends-on-ch04",
    "relation.unit.ch05-prerequisite-lower-semicontinuity",
    "relation.unit.ch05-prerequisite-subdifferential",
    "artifact.o015.backend-generator-ch05",
}


def is_generated(record: dict[str, Any]) -> bool:
    record_id = record["id"]
    return (
        record_id in generated_concepts
        or record_id in generated_terms
        or record_id in generated_exact_ids
        or record_id.startswith("d90.hab.v1.ch05.")
        or record_id.startswith("surface.habring.v1.ch05.")
        or record_id.startswith("qa.o015.ch05.")
        or record_id.startswith("relation.unit.ch05-")
        or record_id.startswith("relation.segment.ch05-")
        or record_id.startswith("relation.surface.ch05-")
        or record_id.startswith("artifact.habring.")
        and record_id.endswith("-ch05")
        or record_id.startswith("correction.o015-hab-adv-")
        and 28 <= int(record_id.rsplit("-", 1)[1]) <= 38
    )


records = [record for record in records if not is_generated(record)]


# Component-specific rights.
rights_specs = [
    (
        "rights.o015-habring-ch05-source",
        "o015-habring-ch05-text",
        SOURCE_PATH,
        "admitted",
        "Chapter 5 authority source; corrections are explicit records.",
    ),
    (
        "rights.o015-habring-id-ch05",
        "o015-habring-id-unit-05",
        TARGET_PATH,
        "derivative",
        "Independent id-ID translation of Chapter 5 and its standalone wrapper.",
    ),
]
for record_id, component_id, path, status, notes in rights_specs:
    right = common("rights", record_id, status)
    right.update(
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
    records.append(right)

solver_right = common(
    "rights",
    "rights.o015-proximal-gradient-solver-validation",
    "admitted",
)
solver_right.update(
    {
        "component_id": "o015-solver-validation-05",
        "path": "qa/validate_proximal_gradient_unit.py",
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": "qa/validate_proximal_gradient_unit.py",
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with results", "no proprietary runtime"],
        "notes": "Uses NumPy/SciPy and open SLSQP for Chapter 5 computations.",
    }
)
records.append(solver_right)


# Chapter 5 unit.
unit = common("unit", "unit.habring.v1.ch05", "built")
unit.update(
    {
        "edition_id": "edition.habring.convex-optimization.id-id.v1",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "parent_id": "unit.habring.v1",
        "unit_kind": "chapter",
        "order": 5,
        "source_local_id": "chapter-5",
        "source_local_label": "5 — Proximal Gradient Methods",
        "target_local_label": "5 — Metode gradien proksimal",
        "source_locator": f"{SOURCE_PATH}:1-336",
        "target_locator": f"{TARGET_PATH}:1-394",
        "rights_id": "rights.o015-habring-id-ch05",
        "translation_state": "built",
        "next_source_order_unit": "Chapter 6 — Duality",
    }
)
records.append(unit)


# Locale-neutral concepts and accepted id-ID terminology.
concept_specs = [
    (
        "concept.proximal-operator",
        "proximal operator of a proper lower-semicontinuous convex function",
        ["concept.proper-convex-function", "concept.lower-semicontinuity", "concept.convex-subdifferential"],
    ),
    (
        "concept.implicit-subgradient-step",
        "implicit subgradient step",
        ["concept.convex-subdifferential"],
    ),
    (
        "concept.composite-convex-optimization",
        "composite convex minimization",
        ["concept.convex-function", "concept.proper-convex-function"],
    ),
    (
        "concept.proximal-gradient-method",
        "proximal gradient or forward-backward method",
        ["concept.proximal-operator", "concept.gradient", "concept.composite-convex-optimization"],
    ),
    (
        "concept.proximal-gradient-fixed-point",
        "proximal-gradient fixed-point optimality",
        ["concept.proximal-gradient-method", "concept.fermat-optimality"],
    ),
    (
        "concept.moreau-envelope",
        "Moreau envelope",
        ["concept.proximal-operator"],
    ),
    (
        "concept.soft-thresholding",
        "coordinatewise soft-thresholding proximal map",
        ["concept.proximal-operator"],
    ),
    (
        "concept.euclidean-shrinkage",
        "Euclidean norm shrinkage proximal map",
        ["concept.proximal-operator"],
    ),
    (
        "concept.proximal-computation-rules",
        "calculus rules for proximal mappings",
        ["concept.proximal-operator"],
    ),
    (
        "concept.moreau-smoothing",
        "differentiability and gradient Lipschitz continuity of the Moreau envelope",
        ["concept.moreau-envelope", "concept.nonexpansive-mapping"],
    ),
    (
        "concept.l-smoothness-descent-lemma",
        "quadratic upper bound for an L-smooth function",
        ["concept.gradient"],
    ),
    (
        "concept.gradient-mapping",
        "proximal-gradient mapping",
        ["concept.proximal-gradient-method"],
    ),
    (
        "concept.proximal-gradient-rate",
        "O(1/n) proximal-gradient value rate and full-sequence convergence",
        ["concept.gradient-mapping", "concept.l-smoothness-descent-lemma"],
    ),
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
    ("term.proximal-operator", "concept.proximal-operator", "proximal operator", "operator proksimal", ["pemetaan proksimal"], "d90.hab.v1.ch05.seg0001"),
    ("term.prox", "concept.proximal-operator", "prox", "proks", [], "d90.hab.v1.ch05.seg0001"),
    ("term.implicit-step", "concept.implicit-subgradient-step", "implicit step", "langkah implisit", [], "d90.hab.v1.ch05.seg0001"),
    ("term.composite-objective", "concept.composite-convex-optimization", "composite objective", "objektif komposit", [], "d90.hab.v1.ch05.seg0003"),
    ("term.proximal-gradient-method", "concept.proximal-gradient-method", "proximal gradient method", "metode gradien proksimal", [], "d90.hab.v1.ch05.seg0003"),
    ("term.moreau-envelope", "concept.moreau-envelope", "Moreau envelope", "selubung Moreau", [], "d90.hab.v1.ch05.seg0004"),
    ("term.soft-thresholding", "concept.soft-thresholding", "soft thresholding", "ambang lunak", ["pengambangan lunak"], "d90.hab.v1.ch05.seg0004"),
    ("term.euclidean-shrinkage", "concept.euclidean-shrinkage", "Euclidean shrinkage", "penyusutan Euklides", [], "d90.hab.v1.ch05.seg0006"),
    ("term.l-smooth", "concept.l-smoothness-descent-lemma", "L-smooth", "L-halus", [], "d90.hab.v1.ch05.seg0007"),
    ("term.gradient-mapping", "concept.gradient-mapping", "gradient mapping", "pemetaan gradien", [], "d90.hab.v1.ch05.seg0007"),
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
            "rights_id": "rights.o015-habring-id-ch05",
        }
    )
    records.append(term)


# Eight exact, contiguous reader-facing segments.
segment_specs = [
    (1, 2, 35, 4, 36, "Implicit step and proximal operator", "Langkah implisit dan operator proksimal", ["concept.implicit-subgradient-step", "concept.proximal-operator"]),
    (2, 36, 76, 38, 66, "Existence, uniqueness, and optimality of the prox", "Eksistensi, keunikan, dan optimalitas proks", ["concept.proximal-operator", "concept.lower-semicontinuity"]),
    (3, 77, 103, 68, 105, "Composite minimization, forward-backward update, and fixed points", "Minimisasi komposit, pembaruan maju–mundur, dan titik tetap", ["concept.composite-convex-optimization", "concept.proximal-gradient-method", "concept.proximal-gradient-fixed-point"]),
    (4, 104, 144, 107, 160, "Moreau envelope and basic proximal examples", "Selubung Moreau dan contoh proksimal dasar", ["concept.moreau-envelope", "concept.metric-projection", "concept.soft-thresholding"]),
    (5, 145, 157, 162, 173, "Proximal computation rules", "Aturan komputasi proksimal", ["concept.proximal-computation-rules"]),
    (6, 158, 239, 175, 274, "Moreau smoothing and proximal-map examples", "Penghalusan Moreau dan contoh pemetaan proksimal", ["concept.moreau-smoothing", "concept.nonexpansive-mapping", "concept.soft-thresholding", "concept.euclidean-shrinkage"]),
    (7, 240, 268, 276, 307, "Smoothness descent lemma and gradient mapping", "Lemma penurunan kehalusan dan pemetaan gradien", ["concept.l-smoothness-descent-lemma", "concept.gradient-mapping"]),
    (8, 269, 336, 309, 394, "Proximal-gradient rate and full-sequence convergence", "Laju gradien proksimal dan konvergensi seluruh barisan", ["concept.proximal-gradient-rate", "concept.gradient-mapping", "concept.composite-convex-optimization"]),
]
for order, s_start, s_end, t_start, t_end, source_label, target_label, concept_ids in segment_specs:
    segment_id = f"d90.hab.v1.ch05.seg{order:04d}"
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, s_start, s_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, t_start, t_end)
    segment = common("segment", segment_id, "current")
    segment.update(
        {
            "unit_id": "unit.habring.v1.ch05",
            "order": order,
            "source_local_id": f"chapter-5-lines-{s_start}-{s_end}",
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
            "rights_id": "rights.o015-habring-id-ch05",
            "evidence_event_ids": [
                "qa.o015.ch05.structure",
                "qa.o015.ch05.formula-delta",
                "qa.o015.ch05.solver",
                "qa.o015.ch05.build",
                "qa.o015.ch05.math-rereview",
                "qa.o015.ch05.visual",
                "qa.o015.ch05.accessibility",
            ],
        }
    )
    records.append(segment)


# Preserve all three source learner prompts and their exact target dispositions.
prompt_specs = [
    (1, "reasoning_prompt", 49, 49, 52, 52, "Why the proximal objective is coercive", "Mengapa objektif proksimal bersifat koersif", "d90.hab.v1.ch05.seg0002", "concept.proximal-operator", "retained_as_informal_reasoning_prompt"),
    (2, "exercise", 111, 111, 124, 124, "Moreau-envelope value identity", "Identitas nilai selubung Moreau", "d90.hab.v1.ch05.seg0004", "concept.moreau-envelope", "retained_and_scaffolded_as_self_study_exercise"),
    (3, "verification_prompt", 235, 235, 272, 272, "Projection and norm proximal mappings", "Pemetaan proksimal proyeksi dan norma", "d90.hab.v1.ch05.seg0006", "concept.proximal-operator", "completed_placeholder_and_retained_verification_prompt"),
]
for order, surface_type, s_start, s_end, t_start, t_end, source_label, target_label, segment_id, concept_id, disposition in prompt_specs:
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, s_start, s_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, t_start, t_end)
    surface = common(
        "learning_surface",
        f"surface.habring.v1.ch05.prompt{order:02d}",
        "present",
    )
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch05",
            "surface_type": surface_type,
            "presence": "present",
            "order": order,
            "source_local_id": f"chapter-5-informal-prompt-{order}",
            "source_local_label": source_label,
            "target_local_label": target_label,
            "related_segment_ids": [segment_id],
            "concept_id": concept_id,
            "source_path": SOURCE_PATH,
            "source_line_start": s_start,
            "source_line_end": s_end,
            "source_locator": f"{SOURCE_PATH}:{s_start}-{s_end}",
            "source_bytes": source_bytes,
            "source_content_sha256": source_digest,
            "target_path": TARGET_PATH,
            "target_line_start": t_start,
            "target_line_end": t_end,
            "target_locator": f"{TARGET_PATH}:{t_start}-{t_end}",
            "target_bytes": target_bytes,
            "target_content_sha256": target_digest,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "disposition": disposition,
            "hint_state": "absent_in_source",
            "answer_state": "absent_in_source",
            "solution_state": "absent_in_source",
            "translation_state": "built",
            "rights_id": "rights.o015-habring-id-ch05",
        }
    )
    records.append(surface)

for surface_type in ("hint", "answer", "solution"):
    surface = common(
        "learning_surface",
        f"surface.habring.v1.ch05.{surface_type}-inventory",
        "source_absent",
    )
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch05",
            "surface_type": surface_type,
            "presence": "absent",
            "count": 0,
            "absence_evidence": "qa/PROXIMAL_GRADIENT_STRUCTURE_REPORT.json",
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
            "rights_id": "rights.o015-habring-id-ch05",
        }
    )
    records.append(surface)


# Convert the exact Chapter 5 adverse-ledger closure to correction records.
ledger = [
    json.loads(line)
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
events = {entry["event_id"]: entry for entry in ledger}
affected_segments = {
    28: ["d90.hab.v1.ch05.seg0001"],
    29: ["d90.hab.v1.ch05.seg0002"],
    30: ["d90.hab.v1.ch05.seg0003"],
    31: ["d90.hab.v1.ch05.seg0004"],
    32: ["d90.hab.v1.ch05.seg0004"],
    33: ["d90.hab.v1.ch05.seg0005"],
    34: ["d90.hab.v1.ch05.seg0006"],
    35: ["d90.hab.v1.ch05.seg0006"],
    36: ["d90.hab.v1.ch05.seg0006"],
    37: ["d90.hab.v1.ch05.seg0008"],
    38: ["d90.hab.v1.ch05.seg0002", "d90.hab.v1.ch05.seg0006"],
}
for number in range(28, 39):
    event_id = f"O015-HAB-ADV-{number:04d}"
    event = events.get(event_id)
    if event is None:
        raise ValueError(f"missing ledger event {event_id}")
    locator = event["source"]
    source_relative, _, line_text = locator.partition(":")
    numbers = [int(value) for value in re.findall(r"\d+", line_text)]
    if not numbers:
        raise ValueError(f"missing source line locator in {event_id}")
    correction = common(
        "correction",
        f"correction.o015-hab-adv-{number:04d}",
        "applied",
    )
    correction.update(
        {
            "source_event_id": event_id,
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "affected_unit_ids": ["unit.habring.v1.ch05"],
            "affected_segment_ids": affected_segments[number],
            "source_path": f"authority/habring/source-v1/{source_relative}",
            "source_line_start": min(numbers),
            "source_line_end": max(numbers),
            "source_locator": f"authority/habring/source-v1/{locator}",
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


# Chapter 5 artifacts and their exact byte identities.
records.extend(
    [
        artifact(
            "artifact.habring.source-ch05",
            "source_tex",
            SOURCE_PATH,
            source_edition_id="edition.habring.convex-optimization.arxiv-2607-11664v1",
            rights_id="rights.o015-habring-ch05-source",
        ),
        artifact(
            "artifact.habring.target-ch05",
            "target_tex",
            TARGET_PATH,
            target_edition_id="edition.habring.convex-optimization.id-id.v1",
            rights_id="rights.o015-habring-id-ch05",
        ),
        artifact(
            "artifact.habring.target-wrapper-ch05",
            "target_tex",
            WRAPPER_PATH,
            target_edition_id="edition.habring.convex-optimization.id-id.v1",
            rights_id="rights.o015-habring-id-ch05",
        ),
        artifact(
            "artifact.habring.structure-report-ch05",
            "qa_report",
            "qa/PROXIMAL_GRADIENT_STRUCTURE_REPORT.json",
            toolchain="qa/audit_proximal_gradient_unit.py",
            formula_delta_manifest_sha256=EXPECTED_FORMULA_MANIFEST_SHA256,
        ),
        artifact(
            "artifact.habring.structure-audit-ch05",
            "qa_source",
            "qa/audit_proximal_gradient_unit.py",
            toolchain="Python 3 standard library",
        ),
        artifact(
            "artifact.habring.solver-results-ch05",
            "qa_report",
            "qa/PROXIMAL_GRADIENT_SOLVER_RESULTS.json",
            toolchain="Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1",
            rights_id="rights.o015-proximal-gradient-solver-validation",
        ),
        artifact(
            "artifact.habring.solver-validator-ch05",
            "qa_source",
            "qa/validate_proximal_gradient_unit.py",
            toolchain="Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1",
            rights_id="rights.o015-proximal-gradient-solver-validation",
        ),
        artifact(
            "artifact.habring.build-log-ch05",
            "build_receipt",
            BUILD_LOG_PATH,
            build_event_id="qa.o015.ch05.build",
            toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber",
        ),
        artifact(
            "artifact.habring.target-pdf-ch05",
            "reader_pdf",
            OUTPUT_PDF_PATH,
            target_edition_id="edition.habring.convex-optimization.id-id.v1",
            rights_id="rights.o015-habring-id-ch05",
            pages=15,
            build_event_id="qa.o015.ch05.build",
            toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber",
            accessibility="searchable id-ID PDF; untagged",
            input_artifact_ids=[
                "artifact.habring.target-wrapper-ch05",
                "artifact.habring.target-ch05",
                "artifact.habring.target-macros",
                "artifact.habring.target-class",
                "artifact.habring.references-bib",
            ],
        ),
        artifact(
            "artifact.habring.target-text-ch05",
            "qa_extract",
            TEXT_PATH,
            target_edition_id="edition.habring.convex-optimization.id-id.v1",
            source_artifact_id="artifact.habring.target-pdf-ch05",
        ),
        artifact(
            "artifact.o015.backend-generator-ch05",
            "qa_source",
            "qa/extend_backend_ch05.py",
            toolchain="Python 3 standard library",
        ),
    ]
)


# Chapter 5 QA events.  Language review intentionally remains not_recorded.
qa_specs = [
    {
        "id": "qa.o015.ch05.source-freeze",
        "status": "pass",
        "event_type": "source",
        "result": "pass",
        "witness_artifact_ids": ["artifact.habring.source-ch05"],
        "authority_id": "o015-habring-arxiv-2607.11664v1",
        "source_sha256": EXPECTED_SOURCE_SHA256,
    },
    {
        "id": "qa.o015.ch05.structure",
        "status": "pass",
        "event_type": "topology",
        "result": "pass",
        "witness_artifact_ids": ["artifact.habring.structure-report-ch05"],
        "environment_topology_equal": True,
        "environment_count": 78,
        "environment_counts": structure["environment_counts"],
        "failures": [],
        "segment_count": 8,
        "label_occurrences_preserved": 9,
        "label_remaps": structure["label_remaps"],
        "citations_preserved": 1,
        "informal_prompts_preserved": 3,
        "unnumbered_displays_preserved": 1,
        "figures": 0,
        "footnotes": 0,
        "inputs": 0,
    },
    {
        "id": "qa.o015.ch05.formula-delta",
        "status": "pass",
        "event_type": "mathematics",
        "result": "pass",
        "witness_artifact_ids": ["artifact.habring.structure-report-ch05"],
        "formula_delta_manifest_sha256": EXPECTED_FORMULA_MANIFEST_SHA256,
        "source_formula_surfaces": 162,
        "target_formula_surfaces": 188,
        "formula_delta_blocks": 38,
        "disposition": "All substantive mathematical deltas are correction-ledger bound.",
    },
    {
        "id": "qa.o015.ch05.solver",
        "status": "pass",
        "event_type": "computation",
        "result": "pass",
        "witness_artifact_ids": [
            "artifact.habring.solver-results-ch05",
            "artifact.habring.solver-validator-ch05",
        ],
        "checks": [
            "projection prox against independent SLSQP",
            "soft thresholding and Euclidean shrinkage against independent open solvers",
            "Moreau gradient against centered finite differences",
            "proximal-gradient descent, telescoping, monotonicity, and O(1/n) bounds",
        ],
        "python": "3.13.9",
        "numpy": "2.4.4",
        "scipy": "1.17.1",
    },
    {
        "id": "qa.o015.ch05.build",
        "status": "pass",
        "event_type": "build",
        "result": "pass",
        "witness_artifact_ids": [
            "artifact.habring.target-pdf-ch05",
            "artifact.habring.build-log-ch05",
        ],
        "toolchain": "pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber",
        "pages": 15,
        "deterministic_rebuild": "byte-identical",
        "errors": [],
    },
    {
        "id": "qa.o015.ch05.visual",
        "status": "pass",
        "event_type": "visual",
        "result": "pass",
        "witness_artifact_ids": ["artifact.habring.target-pdf-ch05"],
        "pages_inspected": 15,
        "method": "All pages rendered at 120 dpi and inspected; selected mathematical and correction surfaces also inspected at full size.",
        "findings": [],
    },
    {
        "id": "qa.o015.ch05.accessibility",
        "status": "pass_with_limitation",
        "event_type": "accessibility",
        "result": "pass_with_limitation",
        "witness_artifact_ids": [
            "artifact.habring.target-pdf-ch05",
            "artifact.habring.target-text-ch05",
        ],
        "checks": [
            "PDF language metadata is id-ID.",
            "PDF is unencrypted and searchable.",
            "Text extraction is retained as an exact artifact.",
            "No figures require alternative text in this chapter.",
        ],
        "limitations": ["PDF is untagged."],
    },
    {
        "id": "qa.o015.ch05.math-rereview",
        "status": "pass",
        "event_type": "mathematics",
        "result": "pass",
        "witness_artifact_ids": [
            "artifact.habring.target-ch05",
            "artifact.habring.structure-report-ch05",
            "artifact.habring.solver-results-ch05",
        ],
        "verified_at": RECORDED_AT,
        "target_sha256": EXPECTED_TARGET_SHA256,
        "review_outcome": {"p1": 0, "p2": 0, "p3": 0},
        "scope": "Independent final mathematical rereview of the complete translated Chapter 5 unit.",
    },
    {
        "id": "qa.o015.ch05.language",
        "status": "not_recorded",
        "event_type": "language",
        "result": "not_recorded",
        "witness_artifact_ids": [],
        "gap": "No independent Indonesian language review is recorded.",
    },
]
for spec in qa_specs:
    record_id = spec["id"]
    status = spec["status"]
    qa = common("qa_event", record_id, status)
    qa.update(
        {
            "unit_id": "unit.habring.v1.ch05",
            **{key: value for key, value in spec.items() if key not in {"id", "status"}},
        }
    )
    records.append(qa)


# Unit hierarchy, source order, dependencies, concept topology, and prompts.
relation_specs: list[tuple[str, str, str, str, str]] = [
    ("relation.unit.root-contains-ch05", "contains", "unit.habring.v1", "unit.habring.v1.ch05", "Source Chapter 5."),
    ("relation.unit.ch04-precedes-ch05", "precedes", "unit.habring.v1.ch04", "unit.habring.v1.ch05", "Contiguous admitted source order."),
    ("relation.unit.ch05-depends-on-ch03", "depends-on", "unit.habring.v1.ch05", "unit.habring.v1.ch03", "Proximal optimality uses Chapter 3 subdifferentials."),
    ("relation.unit.ch05-depends-on-ch04", "depends-on", "unit.habring.v1.ch05", "unit.habring.v1.ch04", "Projection is a central proximal-map example."),
    ("relation.unit.ch05-prerequisite-lower-semicontinuity", "prerequisite", "unit.habring.v1.ch05", "concept.lower-semicontinuity", "Existence and envelope prerequisite."),
    ("relation.unit.ch05-prerequisite-subdifferential", "prerequisite", "unit.habring.v1.ch05", "concept.convex-subdifferential", "Optimality and monotonicity prerequisite."),
]
for order in range(1, 9):
    relation_specs.append(
        (
            f"relation.unit.ch05-contains-seg{order:04d}",
            "contains",
            "unit.habring.v1.ch05",
            f"d90.hab.v1.ch05.seg{order:04d}",
            "Ordered reader-facing translation segment.",
        )
    )
relation_specs.extend(
    [
        ("relation.segment.ch05-seg0001-defines-proximal-operator", "defines", "d90.hab.v1.ch05.seg0001", "concept.proximal-operator", "Implicit optimality motivates the proximal map."),
        ("relation.segment.ch05-seg0002-proves-proximal-wellposedness", "proves", "d90.hab.v1.ch05.seg0002", "concept.proximal-operator", "Existence, uniqueness, and optimality characterization."),
        ("relation.segment.ch05-seg0003-defines-proximal-gradient", "defines", "d90.hab.v1.ch05.seg0003", "concept.proximal-gradient-method", "Forward-backward update."),
        ("relation.segment.ch05-seg0003-proves-fixed-point-optimality", "proves", "d90.hab.v1.ch05.seg0003", "concept.proximal-gradient-fixed-point", "Fixed points are exactly composite minimizers."),
        ("relation.segment.ch05-seg0004-defines-moreau-envelope", "defines", "d90.hab.v1.ch05.seg0004", "concept.moreau-envelope", "Infimal-convolution value function and examples."),
        ("relation.segment.ch05-seg0005-proves-proximal-rules", "proves", "d90.hab.v1.ch05.seg0005", "concept.proximal-computation-rules", "Six finite-dimensional prox rules."),
        ("relation.segment.ch05-seg0006-proves-moreau-smoothing", "proves", "d90.hab.v1.ch05.seg0006", "concept.moreau-smoothing", "Convexity, differentiability, and Lipschitz gradient."),
        ("relation.segment.ch05-seg0007-proves-descent-lemma", "proves", "d90.hab.v1.ch05.seg0007", "concept.l-smoothness-descent-lemma", "Quadratic upper model for an L-smooth function."),
        ("relation.segment.ch05-seg0007-defines-gradient-mapping", "defines", "d90.hab.v1.ch05.seg0007", "concept.gradient-mapping", "Proximal-gradient mapping notation."),
        ("relation.segment.ch05-seg0008-proves-rate", "proves", "d90.hab.v1.ch05.seg0008", "concept.proximal-gradient-rate", "Corrected O(1/n) rate and full-sequence convergence."),
        ("relation.surface.ch05-prompt01-exercises-proximal-operator", "exercises", "surface.habring.v1.ch05.prompt01", "concept.proximal-operator", "Coercivity reasoning prompt."),
        ("relation.surface.ch05-prompt02-exercises-moreau-envelope", "exercises", "surface.habring.v1.ch05.prompt02", "concept.moreau-envelope", "Envelope attainment/value exercise."),
        ("relation.surface.ch05-prompt03-exercises-proximal-maps", "exercises", "surface.habring.v1.ch05.prompt03", "concept.proximal-operator", "Projection and norm-prox verification prompt."),
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


# Refresh only artifact byte identities; all other existing records stay exact.
for record in records:
    if record.get("entity_type") != "artifact":
        continue
    path = ROOT / record["path"]
    if not path.is_file():
        raise FileNotFoundError(path)
    data = path.read_bytes()
    record["bytes"] = len(data)
    record["sha256"] = sha256(data)


entity_rank = {
    entity_type: rank for rank, entity_type in enumerate(schema["entity_order"])
}
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
