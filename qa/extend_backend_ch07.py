#!/usr/bin/env python3
"""Idempotently extend the O015 stable-ID backend through Habring Chapter 7.

The Chapter 6 generator is the deterministic baseline.  This extension
rebuilds that baseline, proves the frozen Chapter 7 evidence, adds only the
Chapter 7 closure, preserves every baseline record byte-for-byte, and writes
the lossless JSONL/CSV pair.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_GENERATOR = ROOT / "qa" / "extend_backend_ch06.py"
SCHEMA_PATH = ROOT / "backend" / "backend_schema.json"
JSONL_PATH = ROOT / "backend" / "records.jsonl"
CSV_PATH = ROOT / "backend" / "records.csv"
LEDGER_PATH = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
PROPOSED_LEDGER_PATH = ROOT / "qa" / "CHAPTER07_PROPOSED_LEDGER.jsonl"
STRUCTURE_REPORT_PATH = ROOT / "qa" / "DUALITY_STRUCTURE_REPORT.json"
SOLVER_RESULTS_PATH = ROOT / "qa" / "DUALITY_SOLVER_RESULTS.json"

RECORDED_AT = "2026-08-22T08:15:00Z"
WORKFLOW = "o015-habring-ch07-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

SOURCE_PATH = "authority/habring/source-v1/duality.tex"
TARGET_PATH = "source/id-ID/habring-07-dualitas-id.tex"
WRAPPER_PATH = "source/id-ID/D90-HAB-07-dualitas-id.tex"
OUTPUT_PDF_PATH = "output/pdf/D90-HAB-07-dualitas-id.pdf"
TEXT_PATH = "qa/D90-HAB-07-dualitas-id.txt"
BUILD_LOG_PATH = "build/habring-unit-07-id/D90-HAB-07-dualitas-id.log"
WORKLOG_PATH = "qa/CHAPTER07_WORKLOG.md"

EXPECTED_SOURCE_SHA256 = "0b112dee2582813cec5629c02df1dda329f690f944b60f4694b1c5762129bea9"
EXPECTED_TARGET_SHA256 = "11e9ad614f7ac4e3107e78bc3bed03a6d4acfe22f2a65fca26433b0ae3209fd9"
EXPECTED_WRAPPER_SHA256 = "3b6e710e37c07cc9ec82ca919451c313c52fa762d58c7b01c6792a78a0098797"
EXPECTED_PDF_SHA256 = "c4354e1e1366bdb20cebb9c6eca26fba172d6d82a6ad22dd9e2e470da2baeb6e"
EXPECTED_BUILD_LOG_SHA256 = "795b594b1c78e0a0769fe6b7f292fea0d6ddc81a054cad00a4d857da0cab217d"
EXPECTED_TEXT_SHA256 = "b473c80434a35ec607c6a9b9da3dcc31e3d5a3a233ae1f7da72293a87d65a544"
EXPECTED_STRUCTURE_REPORT_SHA256 = "fd909b00e4274a31c9e9c707cbb9039d5e03233876d0c0094c66c1049802307f"
EXPECTED_FORMULA_MANIFEST_SHA256 = "fe72e72d0223117a0b34727d235ced9b6bf2af17cf48154e6b670d2ce75d89fb"
EXPECTED_SOLVER_RESULTS_SHA256 = "9ceeadd90b4868f600241301813a8f24c1d1279690abc8cbf96baa3faf62f3c3"
EXPECTED_PROPOSED_LEDGER_SHA256 = "57dbba9afdee2fc453dde9fbb97621c1a6897ff5377c1ec6a210827a8dce675d"
EXPECTED_INTEGRATED_LEDGER_SHA256 = "0673ba83dc3f481583a67b72f3c53b9ea7de4eefb01c94ef653696a7c79c0594"
EXPECTED_WORKLOG_SHA256 = "35ff60e24abc6550aa21745b9522811e7a084ab1f6ff481226f278deabe84c45"
EXPECTED_AUDIT_SOURCE_SHA256 = "4e29ad8cc208ab35f35e8dfc2bb323343977e7badcaed7aa7d8cfa75392cf35b"
EXPECTED_SOLVER_SOURCE_SHA256 = "127bed94abe4b506ebd999a46ea71b31457f2f4cc65c7fdd7cd4efcc60569c5b"
EXPECTED_LEDGER_IDS = [f"O015-HAB-ADV-{number:04d}" for number in range(50, 76)]
GENERATED_CONCEPT_IDS = {
    "concept.fenchel-conjugate",
    "concept.support-function",
    "concept.fenchel-inequality",
    "concept.biconjugate",
    "concept.fenchel-moreau-theorem",
    "concept.gamma-regularization",
    "concept.fenchel-subgradient-equivalence",
    "concept.moreau-decomposition",
    "concept.fenchel-rockafellar-duality",
    "concept.saddle-point",
    "concept.primal-dual-gap",
    "concept.arrow-hurwicz-method",
    "concept.pdhg",
    "concept.pdhg-one-step-inequality",
    "concept.pdhg-ergodic-rate",
    "concept.augmented-lagrangian",
    "concept.admm",
    "concept.admm-stationarity",
    "concept.admm-lyapunov-function",
    "concept.admm-convergence",
}
GENERATED_TERM_IDS = {
    "term.fenchel-conjugate",
    "term.support-function",
    "term.fenchel-inequality",
    "term.biconjugate",
    "term.gamma-regularization",
    "term.moreau-identity",
    "term.fenchel-rockafellar-duality",
    "term.strong-duality",
    "term.saddle-point",
    "term.primal-dual-gap",
    "term.arrow-hurwicz-method",
    "term.primal-dual-hybrid-gradient",
    "term.chambolle-pock-method",
    "term.ergodic-average",
    "term.augmented-lagrangian",
    "term.admm",
    "term.primal-residual",
    "term.lyapunov-functional",
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


def is_generated(record: dict[str, Any]) -> bool:
    record_id = record["id"]
    return (
        record_id in GENERATED_CONCEPT_IDS
        or record_id in GENERATED_TERM_IDS
        or record_id == "unit.habring.v1.ch07"
        or record_id.startswith("d90.hab.v1.ch07.")
        or record_id.startswith("surface.habring.v1.ch07.")
        or record_id.startswith("qa.o015.ch07.")
        or record_id.startswith("relation.unit.ch07-")
        or record_id.startswith("relation.segment.ch07-")
        or record_id.startswith("relation.surface.ch07-")
        or record_id.startswith("artifact.habring.")
        and record_id.endswith("-ch07")
        or record_id in {
            "rights.o015-habring-ch07-source",
            "rights.o015-habring-id-ch07",
            "rights.o015-duality-solver-validation",
            "relation.unit.root-contains-ch07",
            "relation.unit.ch06-precedes-ch07",
            "artifact.o015.backend-generator-ch07",
        }
        or record_id.startswith("correction.o015-hab-adv-")
        and 50 <= int(record_id.rsplit("-", 1)[1]) <= 75
    )


# Reconstruct the admitted Chapter 3--6 baseline on the first extension.  On
# idempotent reruns, remove this generator's exact closure in memory; the final
# artifact-refresh pass still incorporates every legitimate live control hash.
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
existing_records = [
    json.loads(line)
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
if any(is_generated(record) for record in existing_records):
    records = [record for record in existing_records if not is_generated(record)]
else:
    subprocess.run(
        [sys.executable, str(BASE_GENERATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    records = [
        json.loads(line)
        for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]

# The Chapter 6 baseline must be complete and contain no Chapter 7 record.
if len(records) != 449:
    raise ValueError(f"Chapter 6 baseline has {len(records)} records, expected 449")
if any(is_generated(record) for record in records):
    raise ValueError("Chapter 6 baseline unexpectedly contains Chapter 7 records")

baseline_records = [dict(record) for record in records]
baseline_by_id = {record["id"]: canonical_json(record) for record in baseline_records}
baseline_ids = set(baseline_by_id)
generated_ids: set[str] = set()


def add(record: dict[str, Any]) -> None:
    record_id = record["id"]
    if record_id in baseline_ids or record_id in generated_ids:
        raise ValueError(f"stable-ID collision while adding Chapter 7: {record_id}")
    generated_ids.add(record_id)
    records.append(record)


# Prove that every frozen Chapter 7 witness still has its admitted identity.
structure = json.loads(STRUCTURE_REPORT_PATH.read_text(encoding="utf-8"))
solver = json.loads(SOLVER_RESULTS_PATH.read_text(encoding="utf-8"))
if structure.get("result") != "pass" or structure.get("failures") != []:
    raise ValueError("Chapter 7 structure report is not a clean pass")
if structure.get("source", {}).get("sha256") != EXPECTED_SOURCE_SHA256:
    raise ValueError("Chapter 7 authority hash differs from admitted evidence")
if structure.get("target", {}).get("sha256") != EXPECTED_TARGET_SHA256:
    raise ValueError("Chapter 7 target hash differs from admitted evidence")
topology = structure.get("environment_topology", {})
if topology.get("count") != 148:
    raise ValueError("Chapter 7 environment closure differs from 148")
if not topology.get("ordered_begin_equal") or not topology.get("ordered_end_equal"):
    raise ValueError("Chapter 7 ordered environment topology differs")
if structure.get("stable_segment_ids") != [
    f"d90.hab.v1.ch07.seg{order:04d}" for order in range(1, 12)
]:
    raise ValueError("Chapter 7 segment closure differs from 11 stable IDs")
labels = structure.get("labels", {})
if len(labels.get("source", [])) != 24 or len(labels.get("target", [])) != 24:
    raise ValueError("Chapter 7 label occurrence closure differs from 24")
if not labels.get("only_final_duplicate_remapped") or not labels.get("target_unique"):
    raise ValueError("Chapter 7 duplicate-label correction is not closed")
references = structure.get("references", {})
source_refs = references.get("source", {})
target_refs = references.get("target", {})
for command, count in {"Cref": 1, "cref": 3, "eqref": 21, "ref": 9}.items():
    if len(source_refs.get(command, [])) != count or len(target_refs.get(command, [])) != count:
        raise ValueError(f"Chapter 7 {command} occurrence closure differs from {count}")
for command in ("Cref", "cref", "ref"):
    if source_refs.get(command) != target_refs.get(command):
        raise ValueError(f"Chapter 7 {command} order differs")
if source_refs.get("eqref", [])[:-1] != target_refs.get("eqref", [])[:-1]:
    raise ValueError("Chapter 7 eqref order differs before the deliberate final remap")
if target_refs.get("eqref", [])[-1:] != ["duality:eq:proof_admm7"]:
    raise ValueError("Chapter 7 final eqref does not use the unique remap")
if structure.get("citations", {}).get("source") != ["beck2017first", "chambolle2011first"]:
    raise ValueError("Chapter 7 source citation closure differs")
if structure.get("citations", {}).get("target") != ["beck2017first", "chambolle2011first"]:
    raise ValueError("Chapter 7 target citation closure differs")
other = structure.get("other_surface_topology", {})
if other.get("external_assets") != {"source": 0, "target": 0}:
    raise ValueError("Chapter 7 external-asset closure differs from zero")
if other.get("figure_environments") != {"source": 0, "target": 0}:
    raise ValueError("Chapter 7 figure closure differs from zero")
if other.get("source_inputs") != {"source": 0, "target": 0}:
    raise ValueError("Chapter 7 input closure differs from zero")
if other.get("footnotes") != {"source": 1, "target": 1}:
    raise ValueError("Chapter 7 footnote closure differs from one")
formula = structure.get("formula_delta_manifest", {})
if formula.get("sha256") != EXPECTED_FORMULA_MANIFEST_SHA256:
    raise ValueError("Chapter 7 formula-delta manifest differs")
if not formula.get("all_substantive_deltas_ledger_bound"):
    raise ValueError("Chapter 7 contains an unbound substantive formula delta")
if formula.get("source_formula_count") != 254 or formula.get("target_formula_count") != 296:
    raise ValueError("Chapter 7 formula-surface closure differs")
if formula.get("delta_block_count") != 49 or formula.get("substantive_delta_block_count") != 43:
    raise ValueError("Chapter 7 formula-delta block closure differs")
proposal = structure.get("proposed_ledger", {})
if proposal.get("required_ids") != EXPECTED_LEDGER_IDS:
    raise ValueError("Chapter 7 proposed correction ID closure differs")
if proposal.get("missing_ids") != [] or proposal.get("extra_ids") != []:
    raise ValueError("Chapter 7 proposed correction ledger is not exact")
integrated = structure.get("integrated_ledger", {})
if integrated.get("missing_required_ids") != []:
    raise ValueError("Chapter 7 integrated ledger is incomplete")
if not integrated.get("exact_required_records_match_proposal"):
    raise ValueError("Chapter 7 integrated ledger differs from the proposal")
if solver.get("result") != "PASS":
    raise ValueError("Chapter 7 solver report is not a pass")
for check_name, check in solver.get("checks", {}).items():
    if check.get("result") != "PASS":
        raise ValueError(f"Chapter 7 solver subcheck is not a pass: {check_name}")
live_surfaces = solver.get("checks", {}).get("live_target_correction_surfaces", {})
if live_surfaces.get("required_surface_count") != 30:
    raise ValueError("Chapter 7 live target gate differs from 30 surfaces")
if not all(live_surfaces.get("required_surfaces_present", {}).values()):
    raise ValueError("Chapter 7 live target gate has a missing surface")

expected_files = {
    SOURCE_PATH: (30761, EXPECTED_SOURCE_SHA256),
    TARGET_PATH: (35428, EXPECTED_TARGET_SHA256),
    WRAPPER_PATH: (8615, EXPECTED_WRAPPER_SHA256),
    OUTPUT_PDF_PATH: (445733, EXPECTED_PDF_SHA256),
    BUILD_LOG_PATH: (105821, EXPECTED_BUILD_LOG_SHA256),
    TEXT_PATH: (53128, EXPECTED_TEXT_SHA256),
    "qa/DUALITY_STRUCTURE_REPORT.json": (32121, EXPECTED_STRUCTURE_REPORT_SHA256),
    "qa/DUALITY_FORMULA_DELTA_MANIFEST.json": (81046, EXPECTED_FORMULA_MANIFEST_SHA256),
    "qa/DUALITY_SOLVER_RESULTS.json": (10830, EXPECTED_SOLVER_RESULTS_SHA256),
    "qa/CHAPTER07_PROPOSED_LEDGER.jsonl": (15830, EXPECTED_PROPOSED_LEDGER_SHA256),
    "00_control/ADVERSE_LEDGER.jsonl": (43572, EXPECTED_INTEGRATED_LEDGER_SHA256),
    WORKLOG_PATH: (12235, EXPECTED_WORKLOG_SHA256),
    "qa/audit_duality_unit.py": (36689, EXPECTED_AUDIT_SOURCE_SHA256),
    "qa/validate_duality_unit.py": (45213, EXPECTED_SOLVER_SOURCE_SHA256),
}
for relative, expected in expected_files.items():
    if file_info(relative) != expected:
        raise ValueError(f"Chapter 7 frozen artifact differs: {relative}")

build_log = (ROOT / BUILD_LOG_PATH).read_text(encoding="utf-8", errors="replace")
for forbidden in (
    "! LaTeX Error:",
    "undefined references",
    "multiply defined",
    "Overfull \\hbox",
    "Underfull \\hbox",
    "Missing character:",
    "Rerun to get",
):
    if forbidden in build_log:
        raise ValueError(f"Chapter 7 build log contains forbidden diagnostic: {forbidden}")
if "Output written on" not in build_log or "(21 pages" not in build_log:
    raise ValueError("Chapter 7 build log does not prove a 21-page output")

proposed_events = [
    json.loads(line)
    for line in PROPOSED_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
integrated_events = [
    json.loads(line)
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
proposal_by_id = {entry["event_id"]: entry for entry in proposed_events}
integrated_by_id = {entry["event_id"]: entry for entry in integrated_events}
if list(proposal_by_id) != EXPECTED_LEDGER_IDS:
    raise ValueError("Chapter 7 proposed ledger order differs")
for event_id in EXPECTED_LEDGER_IDS:
    if integrated_by_id.get(event_id) != proposal_by_id[event_id]:
        raise ValueError(f"integrated correction differs from proposal: {event_id}")


# Component-specific rights.
for record_id, component_id, path, status, notes in [
    (
        "rights.o015-habring-ch07-source",
        "o015-habring-ch07-text",
        SOURCE_PATH,
        "admitted",
        "Chapter 7 authority source; all mathematical corrections are explicit records.",
    ),
    (
        "rights.o015-habring-id-ch07",
        "o015-habring-id-unit-07",
        TARGET_PATH,
        "derivative",
        "Independent id-ID translation of Chapter 7 and its standalone wrapper.",
    ),
]:
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
    add(right)

solver_right = common("rights", "rights.o015-duality-solver-validation", "admitted")
solver_right.update(
    {
        "component_id": "o015-solver-validation-07",
        "path": "qa/validate_duality_unit.py",
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": "qa/validate_duality_unit.py",
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with results", "no proprietary runtime"],
        "notes": "Uses NumPy/SciPy and open solvers for Fenchel, Moreau, PDHG, and ADMM witnesses.",
    }
)
add(solver_right)


# Chapter 7 unit.
unit = common("unit", "unit.habring.v1.ch07", "built")
unit.update(
    {
        "edition_id": "edition.habring.convex-optimization.id-id.v1",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "parent_id": "unit.habring.v1",
        "unit_kind": "chapter",
        "order": 7,
        "source_local_id": "chapter-7",
        "source_local_label": "7 — Duality",
        "target_local_label": "7 — Dualitas",
        "source_locator": f"{SOURCE_PATH}:1-597",
        "target_locator": f"{TARGET_PATH}:1-632",
        "rights_id": "rights.o015-habring-id-ch07",
        "translation_state": "built",
    }
)
add(unit)


# Locale-neutral concepts and accepted id-ID terminology.
concept_specs = [
    ("concept.fenchel-conjugate", "Fenchel or convex conjugate", ["concept.proper-convex-function", "concept.dual-norm"]),
    ("concept.support-function", "support function of a nonempty convex set", ["concept.indicator-function", "concept.fenchel-conjugate"]),
    ("concept.fenchel-inequality", "Fenchel inequality", ["concept.fenchel-conjugate"]),
    ("concept.biconjugate", "Fenchel biconjugate", ["concept.fenchel-conjugate"]),
    ("concept.fenchel-moreau-theorem", "Fenchel–Moreau biconjugation theorem", ["concept.biconjugate", "concept.hahn-banach-separation", "concept.lower-semicontinuity"]),
    ("concept.gamma-regularization", "greatest lower-semicontinuous convex minorant or Gamma regularization", ["concept.fenchel-moreau-theorem"]),
    ("concept.fenchel-subgradient-equivalence", "Fenchel equality and conjugate-subgradient equivalence", ["concept.fenchel-inequality", "concept.convex-subdifferential"]),
    ("concept.moreau-decomposition", "Moreau proximal decomposition including its scaled form", ["concept.fenchel-subgradient-equivalence", "concept.proximal-operator"]),
    ("concept.fenchel-rockafellar-duality", "Fenchel–Rockafellar strong duality", ["concept.fenchel-moreau-theorem", "concept.subdifferential-calculus"]),
    ("concept.saddle-point", "convex-concave saddle point", ["concept.fenchel-rockafellar-duality"]),
    ("concept.primal-dual-gap", "primal–dual optimality gap", ["concept.saddle-point"]),
    ("concept.arrow-hurwicz-method", "Arrow–Hurwicz primal–dual proximal method", ["concept.saddle-point", "concept.proximal-operator"]),
    ("concept.pdhg", "primal–dual hybrid gradient or Chambolle–Pock method", ["concept.arrow-hurwicz-method", "concept.moreau-decomposition"]),
    ("concept.pdhg-one-step-inequality", "fundamental one-step PDHG saddle estimate", ["concept.pdhg", "concept.strong-convexity"]),
    ("concept.pdhg-ergodic-rate", "ergodic O(1/N) PDHG saddle-gap bound", ["concept.pdhg-one-step-inequality"]),
    ("concept.augmented-lagrangian", "augmented Lagrangian for a linear equality constraint", ["concept.saddle-point"]),
    ("concept.admm", "alternating direction method of multipliers", ["concept.augmented-lagrangian", "concept.proximal-operator"]),
    ("concept.admm-stationarity", "blockwise ADMM optimality and multiplier stationarity", ["concept.admm", "concept.convex-subdifferential"]),
    ("concept.admm-lyapunov-function", "ADMM Lyapunov functional and descent inequality", ["concept.admm-stationarity"]),
    ("concept.admm-convergence", "ADMM residual and objective-value convergence", ["concept.admm-lyapunov-function"]),
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
    add(concept)

term_specs = [
    ("term.fenchel-conjugate", "concept.fenchel-conjugate", "Fenchel/convex conjugate", "konjugat Fenchel/konveks", [], 1),
    ("term.support-function", "concept.support-function", "support function", "fungsi pendukung", [], 1),
    ("term.fenchel-inequality", "concept.fenchel-inequality", "Fenchel inequality", "ketaksamaan Fenchel", [], 2),
    ("term.biconjugate", "concept.biconjugate", "biconjugate", "bikonjugat", [], 2),
    ("term.gamma-regularization", "concept.gamma-regularization", "Gamma regularization", "regularisasi Gamma", ["regularisasi Γ"], 3),
    ("term.moreau-identity", "concept.moreau-decomposition", "Moreau identity", "identitas Moreau", ["dekomposisi Moreau"], 4),
    ("term.fenchel-rockafellar-duality", "concept.fenchel-rockafellar-duality", "Fenchel–Rockafellar duality", "dualitas Fenchel–Rockafellar", [], 5),
    ("term.strong-duality", "concept.fenchel-rockafellar-duality", "strong duality", "dualitas kuat", [], 5),
    ("term.saddle-point", "concept.saddle-point", "saddle point", "titik pelana", [], 6),
    ("term.primal-dual-gap", "concept.primal-dual-gap", "primal-dual gap", "kesenjangan primal–dual", [], 6),
    ("term.arrow-hurwicz-method", "concept.arrow-hurwicz-method", "Arrow–Hurwicz method", "metode Arrow–Hurwicz", [], 7),
    ("term.primal-dual-hybrid-gradient", "concept.pdhg", "primal-dual hybrid gradient", "gradien hibrida primal–dual", ["PDHG"], 7),
    ("term.chambolle-pock-method", "concept.pdhg", "Chambolle–Pock method", "metode Chambolle–Pock", ["PDHG"], 7),
    ("term.ergodic-average", "concept.pdhg-ergodic-rate", "ergodic average", "rerata ergodik", [], 8),
    ("term.augmented-lagrangian", "concept.augmented-lagrangian", "augmented Lagrangian", "Lagrangian teraugmentasi", [], 9),
    ("term.admm", "concept.admm", "alternating direction method of multipliers", "metode pengali arah bergantian", ["ADMM"], 9),
    ("term.primal-residual", "concept.admm-convergence", "primal residual", "residu primal", ["residu"], 10),
    ("term.lyapunov-functional", "concept.admm-lyapunov-function", "Lyapunov functional", "fungsional Lyapunov", [], 10),
]
for term_id, concept_id, source_term, preferred, variants, segment_order in term_specs:
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
            "evidence_segment_ids": [f"d90.hab.v1.ch07.seg{segment_order:04d}"],
            "examples": [preferred],
            "rights_id": "rights.o015-habring-id-ch07",
        }
    )
    add(term)


# Eleven exact, contiguous reader-facing segments.
segment_specs = [
    (1, 1, 24, 3, 27, "Fenchel conjugate definition and examples", "Definisi dan contoh konjugat Fenchel", ["concept.fenchel-conjugate", "concept.support-function"]),
    (2, 25, 60, 29, 65, "Conjugate properness, Fenchel inequality, and biconjugation", "Properitas konjugat, ketaksamaan Fenchel, dan bikonjugasi", ["concept.fenchel-conjugate", "concept.fenchel-inequality", "concept.biconjugate"]),
    (3, 61, 141, 67, 150, "Biconjugate inequality, Fenchel–Moreau, and Gamma regularization", "Ketaksamaan bikonjugat, Fenchel–Moreau, dan regularisasi Gamma", ["concept.biconjugate", "concept.fenchel-moreau-theorem", "concept.gamma-regularization"]),
    (4, 142, 186, 152, 197, "Conjugate subgradients and Moreau identity", "Subgradien konjugat dan identitas Moreau", ["concept.fenchel-subgradient-equivalence", "concept.moreau-decomposition"]),
    (5, 187, 247, 199, 262, "Fenchel–Rockafellar theorem and proof", "Teorema dan bukti Fenchel–Rockafellar", ["concept.fenchel-rockafellar-duality"]),
    (6, 248, 277, 264, 294, "Primal, dual, saddle, and gap formulations", "Formulasi primal, dual, titik pelana, dan kesenjangan", ["concept.saddle-point", "concept.primal-dual-gap", "concept.moreau-decomposition"]),
    (7, 278, 335, 296, 353, "Arrow–Hurwicz and PDHG derivation", "Penurunan metode Arrow–Hurwicz dan PDHG", ["concept.arrow-hurwicz-method", "concept.pdhg"]),
    (8, 336, 394, 355, 425, "PDHG one-step estimate and ergodic convergence", "Taksiran satu langkah dan konvergensi ergodik PDHG", ["concept.pdhg-one-step-inequality", "concept.pdhg-ergodic-rate"]),
    (9, 395, 432, 427, 462, "Augmented Lagrangian, ADMM updates, and stationarity", "Lagrangian teraugmentasi, pembaruan ADMM, dan stasioneritas", ["concept.augmented-lagrangian", "concept.admm", "concept.admm-stationarity"]),
    (10, 433, 502, 464, 534, "ADMM convergence theorem and proof steps 1–2", "Teorema konvergensi ADMM dan langkah bukti 1–2", ["concept.admm-convergence", "concept.admm-stationarity", "concept.admm-lyapunov-function"]),
    (11, 503, 597, 536, 632, "ADMM Lyapunov descent and convergence conclusion", "Penurunan Lyapunov dan simpulan konvergensi ADMM", ["concept.admm-lyapunov-function", "concept.admm-convergence"]),
]
for order, s_start, s_end, t_start, t_end, source_label, target_label, concept_ids in segment_specs:
    segment_id = f"d90.hab.v1.ch07.seg{order:04d}"
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, s_start, s_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, t_start, t_end)
    segment = common("segment", segment_id, "current")
    segment.update(
        {
            "unit_id": "unit.habring.v1.ch07",
            "order": order,
            "source_local_id": f"chapter-7-lines-{s_start}-{s_end}",
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
            "rights_id": "rights.o015-habring-id-ch07",
            "evidence_event_ids": [
                "qa.o015.ch07.structure",
                "qa.o015.ch07.formula-delta",
                "qa.o015.ch07.solver",
                "qa.o015.ch07.build",
                "qa.o015.ch07.math-rereview",
                "qa.o015.ch07.visual",
                "qa.o015.ch07.accessibility",
            ],
        }
    )
    add(segment)


# Five source self-study prompts are all retained visibly in Indonesian.
prompt_specs = [
    (1, 47, 47, 50, 50, 2, "Lower-semicontinuity of the conjugate", "Semikontinuitas bawah konjugat", "concept.fenchel-conjugate"),
    (2, 57, 57, 60, 60, 2, "Proof of Fenchel inequality", "Bukti ketaksamaan Fenchel", "concept.fenchel-inequality"),
    (3, 185, 185, 195, 195, 4, "Well-posedness of the proximal maps in Moreau identity", "Keterdefinisian pemetaan proksimal dalam identitas Moreau", "concept.moreau-decomposition"),
    (4, 276, 276, 292, 292, 6, "Primal-dual gap lemma", "Lema kesenjangan primal–dual", "concept.primal-dual-gap"),
    (5, 411, 411, 441, 441, 9, "Equivalence of constrained and augmented-Lagrangian problems", "Ekuivalensi masalah berkendala dan Lagrangian teraugmentasi", "concept.augmented-lagrangian"),
]
for order, s_start, s_end, t_start, t_end, segment_order, source_label, target_label, concept_id in prompt_specs:
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, s_start, s_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, t_start, t_end)
    prompt = common("learning_surface", f"surface.habring.v1.ch07.prompt{order:02d}", "present")
    prompt.update(
        {
            "unit_id": "unit.habring.v1.ch07",
            "surface_type": "exercise_prompt",
            "presence": "present",
            "order": order,
            "source_local_id": f"chapter-7-prompt-{order}",
            "source_local_label": source_label,
            "target_local_label": target_label,
            "related_segment_ids": [f"d90.hab.v1.ch07.seg{segment_order:04d}"],
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
            "disposition": "retained_visible_self_study_prompt",
            "hint_state": "absent_in_source",
            "answer_state": "absent_in_source",
            "solution_state": "absent_in_source",
            "translation_state": "built",
            "rights_id": "rights.o015-habring-id-ch07",
        }
    )
    add(prompt)

for surface_type in ("hint", "answer", "solution"):
    surface = common(
        "learning_surface",
        f"surface.habring.v1.ch07.{surface_type}-inventory",
        "source_absent",
    )
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch07",
            "surface_type": surface_type,
            "presence": "absent",
            "count": 0,
            "absence_evidence": "qa/DUALITY_STRUCTURE_REPORT.json",
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
            "rights_id": "rights.o015-habring-id-ch07",
        }
    )
    add(surface)


# Convert the exact Chapter 7 adverse-ledger closure to correction records.
correction_specs = {
    50: (16, 20, [1]),
    51: (26, 47, [2]),
    52: (62, 125, [3]),
    53: (178, 185, [4]),
    54: (260, 263, [6]),
    55: (320, 355, [7, 8]),
    56: (361, 392, [8]),
    57: (413, 431, [9]),
    58: (489, 500, [10]),
    59: (503, 580, [11]),
    60: (590, 596, [11]),
    61: (529, 596, [11]),
    62: (25, 596, [2, 3, 5, 9, 10, 11]),
    63: (1, 597, list(range(1, 12))),
    64: (6, 435, [1, 3, 4, 5, 8, 9, 10]),
    65: (131, 140, [3]),
    66: (214, 227, [5]),
    67: (254, 404, [6, 9]),
    68: (258, 258, [6]),
    69: (337, 364, [8]),
    70: (397, 597, [9, 10, 11]),
    71: (18, 18, [1]),
    72: (90, 94, [3]),
    73: (361, 394, [8]),
    74: (337, 358, [8]),
    75: (60, 140, [2, 3]),
}
for number in range(50, 76):
    event_id = f"O015-HAB-ADV-{number:04d}"
    event = integrated_by_id[event_id]
    source_start, source_end, segment_orders = correction_specs[number]
    correction = common("correction", f"correction.o015-hab-adv-{number:04d}", "applied")
    correction.update(
        {
            "source_event_id": event_id,
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "affected_unit_ids": ["unit.habring.v1.ch07"],
            "affected_segment_ids": [
                f"d90.hab.v1.ch07.seg{order:04d}" for order in segment_orders
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
    add(correction)


# Chapter 7 artifacts and their exact byte identities.
for record in [
    artifact("artifact.habring.source-ch07", "source_tex", SOURCE_PATH, source_edition_id="edition.habring.convex-optimization.arxiv-2607-11664v1", rights_id="rights.o015-habring-ch07-source"),
    artifact("artifact.habring.target-ch07", "target_tex", TARGET_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch07"),
    artifact("artifact.habring.target-wrapper-ch07", "target_tex", WRAPPER_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch07"),
    artifact("artifact.habring.structure-report-ch07", "qa_report", "qa/DUALITY_STRUCTURE_REPORT.json", toolchain="qa/audit_duality_unit.py", formula_delta_manifest_sha256=EXPECTED_FORMULA_MANIFEST_SHA256),
    artifact("artifact.habring.formula-manifest-ch07", "qa_report", "qa/DUALITY_FORMULA_DELTA_MANIFEST.json", toolchain="qa/audit_duality_unit.py"),
    artifact("artifact.habring.structure-audit-ch07", "qa_source", "qa/audit_duality_unit.py", toolchain="Python 3 standard library"),
    artifact("artifact.habring.solver-results-ch07", "qa_report", "qa/DUALITY_SOLVER_RESULTS.json", toolchain="Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1", rights_id="rights.o015-duality-solver-validation"),
    artifact("artifact.habring.solver-validator-ch07", "qa_source", "qa/validate_duality_unit.py", toolchain="Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1", rights_id="rights.o015-duality-solver-validation"),
    artifact("artifact.habring.proposed-ledger-ch07", "correction_proposal", "qa/CHAPTER07_PROPOSED_LEDGER.jsonl", source_artifact_id="artifact.habring.source-ch07"),
    artifact("artifact.habring.worklog-ch07", "qa_receipt", WORKLOG_PATH, source_artifact_id="artifact.habring.source-ch07"),
    artifact("artifact.habring.build-log-ch07", "build_receipt", BUILD_LOG_PATH, build_event_id="qa.o015.ch07.build", toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber"),
    artifact("artifact.habring.target-pdf-ch07", "reader_pdf", OUTPUT_PDF_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch07", pages=21, build_event_id="qa.o015.ch07.build", toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber", accessibility="searchable id-ID PDF; untagged", input_artifact_ids=["artifact.habring.target-wrapper-ch07", "artifact.habring.target-ch07", "artifact.habring.target-macros", "artifact.habring.target-class", "artifact.habring.references-bib"]),
    artifact("artifact.habring.target-text-ch07", "qa_extract", TEXT_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", source_artifact_id="artifact.habring.target-pdf-ch07"),
    artifact("artifact.o015.backend-generator-ch07", "qa_source", "qa/extend_backend_ch07.py", toolchain="Python 3 standard library"),
]:
    add(record)


# Nine-event Chapter 7 evidence topology; language review remains not recorded.
qa_specs = [
    {"id": "qa.o015.ch07.source-freeze", "status": "pass", "event_type": "source", "result": "pass", "witness_artifact_ids": ["artifact.habring.source-ch07"], "authority_id": "o015-habring-arxiv-2607.11664v1", "source_sha256": EXPECTED_SOURCE_SHA256},
    {"id": "qa.o015.ch07.structure", "status": "pass", "event_type": "topology", "result": "pass", "witness_artifact_ids": ["artifact.habring.structure-report-ch07"], "environment_topology_equal": True, "environment_count": 148, "environment_counts": topology["counts_by_name"], "failures": [], "segment_count": 11, "label_occurrences": 24, "target_unique_labels": 24, "Cref_occurrences_preserved": 1, "cref_occurrences_preserved": 3, "eqref_occurrences_preserved": 21, "ref_occurrences_preserved": 9, "citations_preserved": 2, "footnotes_preserved": 1, "reader_prompts_preserved": 5, "figures": 0, "assets": 0, "inputs": 0, "duplicate_label_disposition": "final source duplicate remapped to duality:eq:proof_admm7 with its reference in lockstep"},
    {"id": "qa.o015.ch07.formula-delta", "status": "pass", "event_type": "mathematics", "result": "pass", "witness_artifact_ids": ["artifact.habring.structure-report-ch07", "artifact.habring.formula-manifest-ch07", "artifact.habring.proposed-ledger-ch07"], "formula_delta_manifest_sha256": EXPECTED_FORMULA_MANIFEST_SHA256, "source_formula_surfaces": 254, "target_formula_surfaces": 296, "formula_delta_blocks": 49, "substantive_formula_delta_blocks": 43, "correction_events": 26, "disposition": "All substantive mathematical deltas are correction-ledger bound."},
    {"id": "qa.o015.ch07.solver", "status": "pass", "event_type": "computation", "result": "pass", "witness_artifact_ids": ["artifact.habring.solver-results-ch07", "artifact.habring.solver-validator-ch07"], "checks": ["Fenchel conjugacy and subgradient equivalence", "scaled Moreau decomposition", "independent Fenchel–Rockafellar primal and dual solves", "PDHG one-step estimate and convergence with negative controls", "ADMM residual and objective convergence with negative controls", "30 live target correction and stable-ID surfaces"], "python": "3.13.9", "numpy": "2.4.4", "scipy": "1.17.1"},
    {"id": "qa.o015.ch07.build", "status": "pass", "event_type": "build", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-pdf-ch07", "artifact.habring.build-log-ch07"], "toolchain": "pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber", "pages": 21, "page_size": "A4", "deterministic_rebuild": "byte-identical", "errors": [], "undefined_references": 0, "multiply_defined_labels": 0, "replacement_glyphs": 0, "overfull_boxes": 0, "underfull_boxes": 0},
    {"id": "qa.o015.ch07.visual", "status": "pass", "event_type": "visual", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-pdf-ch07"], "pages_inspected": 21, "method": "All pages rendered and inspected after two byte-identical fixed-epoch builds; repaired page 7 was re-rendered at 180 dpi.", "findings": [], "repaired_finding": "Proof heading and first custom implication label are on separate lines on physical page 7."},
    {"id": "qa.o015.ch07.accessibility", "status": "pass_with_limitation", "event_type": "accessibility", "result": "pass_with_limitation", "witness_artifact_ids": ["artifact.habring.target-pdf-ch07", "artifact.habring.target-text-ch07"], "checks": ["PDF language metadata is id-ID.", "PDF is unencrypted and searchable.", "Text extraction is retained as an exact artifact.", "No figures require alternative text in this chapter."], "limitations": ["PDF is untagged."]},
    {"id": "qa.o015.ch07.math-rereview", "status": "pass", "event_type": "mathematics", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-ch07", "artifact.habring.structure-report-ch07", "artifact.habring.solver-results-ch07"], "verified_at": RECORDED_AT, "target_sha256": EXPECTED_TARGET_SHA256, "review_outcome": {"p1": 0, "p2": 0, "p3": 0}, "scope": "Independent full target/source/wrapper/ledger rereview, followed by an exact layout-only delta rereview."},
    {"id": "qa.o015.ch07.language", "status": "not_recorded", "event_type": "language", "result": "not_recorded", "witness_artifact_ids": [], "gap": "No independent Indonesian language review is recorded."},
]
for spec in qa_specs:
    qa = common("qa_event", spec["id"], spec["status"])
    qa.update(
        {
            "unit_id": "unit.habring.v1.ch07",
            **{key: value for key, value in spec.items() if key not in {"id", "status"}},
        }
    )
    add(qa)


# Unit hierarchy, source order, dependencies, concept topology, and prompts.
relation_specs: list[tuple[str, str, str, str, str]] = [
    ("relation.unit.root-contains-ch07", "contains", "unit.habring.v1", "unit.habring.v1.ch07", "Source Chapter 7."),
    ("relation.unit.ch06-precedes-ch07", "precedes", "unit.habring.v1.ch06", "unit.habring.v1.ch07", "Contiguous admitted source order."),
    ("relation.unit.ch07-depends-on-ch05", "depends-on", "unit.habring.v1.ch07", "unit.habring.v1.ch05", "Moreau, PDHG, and ADMM use proximal and subdifferential constructions."),
    ("relation.unit.ch07-prerequisite-subdifferential", "prerequisite", "unit.habring.v1.ch07", "concept.subdifferential-calculus", "Fenchel equality and optimality calculus prerequisite."),
    ("relation.unit.ch07-prerequisite-separation", "prerequisite", "unit.habring.v1.ch07", "concept.hahn-banach-separation", "Fenchel–Moreau proof prerequisite."),
    ("relation.unit.ch07-prerequisite-proximal", "prerequisite", "unit.habring.v1.ch07", "concept.proximal-operator", "Moreau, PDHG, and ADMM prerequisite."),
]
for order in range(1, 12):
    relation_specs.append((f"relation.unit.ch07-contains-seg{order:04d}", "contains", "unit.habring.v1.ch07", f"d90.hab.v1.ch07.seg{order:04d}", "Ordered reader-facing translation segment."))
relation_specs.extend(
    [
        ("relation.segment.ch07-seg0001-defines-fenchel-conjugate", "defines", "d90.hab.v1.ch07.seg0001", "concept.fenchel-conjugate", "Typed definition and standard examples."),
        ("relation.segment.ch07-seg0001-defines-support-function", "defines", "d90.hab.v1.ch07.seg0001", "concept.support-function", "Indicator-function conjugate example."),
        ("relation.segment.ch07-seg0002-proves-fenchel-inequality", "proves", "d90.hab.v1.ch07.seg0002", "concept.fenchel-inequality", "Fenchel inequality and biconjugate setup."),
        ("relation.segment.ch07-seg0003-proves-fenchel-moreau", "proves", "d90.hab.v1.ch07.seg0003", "concept.fenchel-moreau-theorem", "Finite-dimensional separation proof."),
        ("relation.segment.ch07-seg0003-defines-gamma-regularization", "defines", "d90.hab.v1.ch07.seg0003", "concept.gamma-regularization", "Greatest-minorant characterization with empty-family convention."),
        ("relation.segment.ch07-seg0004-proves-subgradient-equivalence", "proves", "d90.hab.v1.ch07.seg0004", "concept.fenchel-subgradient-equivalence", "Three equivalent Fenchel/subgradient statements."),
        ("relation.segment.ch07-seg0004-proves-moreau", "proves", "d90.hab.v1.ch07.seg0004", "concept.moreau-decomposition", "Moreau identity from conjugate subgradients."),
        ("relation.segment.ch07-seg0005-proves-fenchel-rockafellar", "proves", "d90.hab.v1.ch07.seg0005", "concept.fenchel-rockafellar-duality", "Strong-duality and attainment proof under qualification."),
        ("relation.segment.ch07-seg0006-defines-primal-dual-gap", "defines", "d90.hab.v1.ch07.seg0006", "concept.primal-dual-gap", "Typed primal-dual and saddle-gap formulation."),
        ("relation.segment.ch07-seg0007-defines-pdhg", "defines", "d90.hab.v1.ch07.seg0007", "concept.pdhg", "Symmetric preconditioned primal-dual update."),
        ("relation.segment.ch07-seg0008-proves-pdhg-rate", "proves", "d90.hab.v1.ch07.seg0008", "concept.pdhg-ergodic-rate", "Telescoping one-step estimate and Jensen averaging."),
        ("relation.segment.ch07-seg0009-defines-admm", "defines", "d90.hab.v1.ch07.seg0009", "concept.admm", "Alternating augmented-Lagrangian updates."),
        ("relation.segment.ch07-seg0010-defines-admm-convergence", "defines", "d90.hab.v1.ch07.seg0010", "concept.admm-convergence", "Residual and objective-value convergence theorem."),
        ("relation.segment.ch07-seg0011-proves-admm-convergence", "proves", "d90.hab.v1.ch07.seg0011", "concept.admm-convergence", "Corrected Lyapunov descent and objective squeeze."),
    ]
)
for order, _, _, _, _, _, _, _, concept_id in prompt_specs:
    relation_specs.append(
        (
            f"relation.surface.ch07-prompt{order:02d}-exercises-{concept_id.removeprefix('concept.')}",
            "exercises",
            f"surface.habring.v1.ch07.prompt{order:02d}",
            concept_id,
            "Retained source self-study prompt.",
        )
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
    add(relation)


# Refresh artifact identities, prove baseline preservation, then emit canonical exports.
for record in records:
    if record.get("entity_type") != "artifact":
        continue
    path = ROOT / record["path"]
    if not path.is_file():
        raise FileNotFoundError(path)
    data = path.read_bytes()
    record["bytes"] = len(data)
    record["sha256"] = sha256(data)

final_by_id = {record["id"]: canonical_json(record) for record in records}
missing_baseline_ids = sorted(baseline_ids - set(final_by_id))
changed_baseline_ids = sorted(
    record_id
    for record_id in baseline_ids
    if final_by_id.get(record_id) != baseline_by_id[record_id]
)
if missing_baseline_ids or changed_baseline_ids:
    raise ValueError(
        "Chapter 7 extension changed its freshly reconstructed baseline: "
        f"missing={missing_baseline_ids}, changed={changed_baseline_ids}"
    )

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

baseline_counts = Counter(record["entity_type"] for record in baseline_records)
added_counts = Counter(
    record["entity_type"] for record in records if record["id"] in generated_ids
)
total_counts = Counter(record["entity_type"] for record in records)
print(
    json.dumps(
        {
            "added_entity_counts": dict(sorted(added_counts.items())),
            "added_record_count": len(generated_ids),
            "baseline_comparison": {
                "baseline_record_count": len(baseline_records),
                "changed_record_ids": changed_baseline_ids,
                "missing_record_ids": missing_baseline_ids,
                "preserved_record_count": len(baseline_ids),
                "result": "pass",
            },
            "baseline_entity_counts": dict(sorted(baseline_counts.items())),
            "csv": {
                "bytes": file_info("backend/records.csv")[0],
                "sha256": file_info("backend/records.csv")[1],
            },
            "entity_counts": dict(sorted(total_counts.items())),
            "jsonl": {
                "bytes": file_info("backend/records.jsonl")[0],
                "sha256": file_info("backend/records.jsonl")[1],
            },
            "record_count": len(records),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
