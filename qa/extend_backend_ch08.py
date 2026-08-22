#!/usr/bin/env python3
"""Deterministically extend the O015 backend through Habring Chapter 8.

The exact 595-record Chapter 3--7 backend is the semantic baseline.  On a
rerun, this script removes only its own Chapter 8 closure, re-proves every
frozen Chapter 8 witness, adds that closure again, refreshes live artifact
identities, and writes the canonical JSONL/lossless CSV pair.  No pre-Chapter
8 semantic record may change; the only admitted baseline changes are current
hash/byte refreshes for explicitly enumerated artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "backend" / "backend_schema.json"
JSONL_PATH = ROOT / "backend" / "records.jsonl"
CSV_PATH = ROOT / "backend" / "records.csv"
LEDGER_PATH = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
PROPOSED_LEDGER_PATH = ROOT / "qa" / "CHAPTER08_PROPOSED_LEDGER.jsonl"
STRUCTURE_REPORT_PATH = ROOT / "qa" / "STOCHASTIC_STRUCTURE_REPORT.json"
SOLVER_RESULTS_PATH = ROOT / "qa" / "STOCHASTIC_SOLVER_RESULTS.json"

RECORDED_AT = "2026-08-22T09:00:00Z"
WORKFLOW = "o015-habring-ch08-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

SOURCE_PATH = "authority/habring/source-v1/stochastic.tex"
TARGET_PATH = "source/id-ID/habring-08-penurunan-gradien-stokastik-id.tex"
WRAPPER_PATH = "source/id-ID/D90-HAB-08-penurunan-gradien-stokastik-id.tex"
OUTPUT_PDF_PATH = "output/pdf/D90-HAB-08-penurunan-gradien-stokastik-id.pdf"
TEXT_PATH = "qa/D90-HAB-08-penurunan-gradien-stokastik-id.txt"
BUILD_LOG_PATH = "build/habring-unit-08-id/D90-HAB-08-penurunan-gradien-stokastik-id.log"
WORKLOG_PATH = "qa/CHAPTER08_WORKLOG.md"

EXPECTED_SOURCE_SHA256 = "610d11b59d8dfabbbbe6fbc509a0f9ac1727540458c67f8cd3b7bab49566a07d"
EXPECTED_TARGET_SHA256 = "f610aaec91aa9b76582f251458da65d25cc37a933a51da478cad13ee16e5a344"
EXPECTED_WRAPPER_SHA256 = "d00ea41830af388c227a1054025f049a9315da6f41675573965042d320eb7428"
EXPECTED_PDF_SHA256 = "c1ed028667c5df3fd0a837807e2a17bf7a9e1fa3170938853c9a96b9670fa86a"
EXPECTED_BUILD_LOG_SHA256 = "59609048d4930761a5de52f05aa65f80cf3da36dc7f64bd624c1ec539e64702c"
EXPECTED_TEXT_SHA256 = "8556e8138248e163bff23d1778e1d2d782d7c0b3bfa6c1c4df5adaed439a05c6"
EXPECTED_STRUCTURE_REPORT_SHA256 = "d44495208072e4555011dce4cf6155d434bc526574614d2683b8a97484f730dc"
EXPECTED_FORMULA_MANIFEST_SHA256 = "2f9632d02071ded0c84d54ca17af019137cecfe18245d94a7e9243449c0e9fe9"
EXPECTED_SOLVER_RESULTS_SHA256 = "3b78aa1140a08cf811493f37496b10c2955f02bec570385dcde6480f37578f22"
EXPECTED_PROPOSED_LEDGER_SHA256 = "a815d0211da31b21a25a3f9fd8a2c1ec5fcc7da5e7a62c980f75df40ae65d45d"
EXPECTED_INTEGRATED_LEDGER_SHA256 = "605105da173eae1d55b272a5de9dd2c15669beeb0cbe2326976205337a01ebbd"
EXPECTED_WORKLOG_SHA256 = "ee7c755141c5fefa7054dde2f8aba7ae4e81a77672795d42afc69841916757b9"
EXPECTED_AUDIT_SOURCE_SHA256 = "d6a201efc1489fd8220510408bb65cf3cb56d5603b130f46287c6ec8f5be905e"
EXPECTED_SOLVER_SOURCE_SHA256 = "ef05e828b83ab285e5ba090dc27753cd758d5c3e1697f9c138b57bf052a7006e"
EXPECTED_LEDGER_IDS = [f"O015-HAB-ADV-{number:04d}" for number in range(76, 84)]

GENERATED_CONCEPT_IDS = {
    "concept.finite-sum-optimization",
    "concept.stochastic-subgradient-oracle",
    "concept.stochastic-gradient-descent",
    "concept.conditional-stochastic-oracle",
    "concept.projected-stochastic-gradient-descent",
    "concept.stochastic-best-iterate-bound",
    "concept.stochastic-step-size-condition",
}
GENERATED_TERM_IDS = {
    "term.finite-sum-problem",
    "term.stochastic-gradient-estimator",
    "term.stochastic-gradient-descent",
    "term.iid",
    "term.filtration",
    "term.conditional-expectation",
    "term.conditional-variance",
    "term.projected-stochastic-gradient-descent",
}
GENERATED_EXACT_IDS = {
    "unit.habring.v1.ch08",
    "rights.o015-habring-ch08-source",
    "rights.o015-habring-id-ch08",
    "rights.o015-stochastic-solver-validation",
    "relation.unit.root-contains-ch08",
    "relation.unit.ch07-precedes-ch08",
    "artifact.o015.backend-generator-ch08",
}
ALLOWED_BASELINE_ARTIFACT_REFRESH_IDS = {
    "artifact.o015.adverse-ledger",
    "artifact.o015.component-rights",
    "artifact.o015.coverage-overlap",
    "artifact.o015.backend-validator",
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
    if record_id in GENERATED_CONCEPT_IDS | GENERATED_TERM_IDS | GENERATED_EXACT_IDS:
        return True
    prefixes = (
        "d90.hab.v1.ch08.",
        "surface.habring.v1.ch08.",
        "qa.o015.ch08.",
        "relation.unit.ch08-",
        "relation.segment.ch08-",
    )
    if record_id.startswith(prefixes):
        return True
    if record_id.startswith("artifact.habring.") and record_id.endswith("-ch08"):
        return True
    if record_id.startswith("correction.o015-hab-adv-"):
        return 76 <= int(record_id.rsplit("-", 1)[1]) <= 83
    return False


schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
existing_records = [
    json.loads(line)
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
records = [record for record in existing_records if not is_generated(record)]
if len(records) != 595:
    raise ValueError(f"Chapter 7 baseline has {len(records)} records, expected 595")
if any(record.get("unit_id") == "unit.habring.v1.ch08" for record in records):
    raise ValueError("Chapter 7 baseline unexpectedly retains a Chapter 8 unit reference")
baseline_records = [dict(record) for record in records]
baseline_by_id = {record["id"]: canonical_json(record) for record in baseline_records}
baseline_ids = set(baseline_by_id)
generated_ids: set[str] = set()


def add(record: dict[str, Any]) -> None:
    record_id = record["id"]
    if record_id in baseline_ids or record_id in generated_ids:
        raise ValueError(f"stable-ID collision while adding Chapter 8: {record_id}")
    generated_ids.add(record_id)
    records.append(record)


# Prove the complete frozen Chapter 8 evidence closure.
structure = json.loads(STRUCTURE_REPORT_PATH.read_text(encoding="utf-8"))
solver = json.loads(SOLVER_RESULTS_PATH.read_text(encoding="utf-8"))
if structure.get("result") != "pass" or structure.get("failures") != []:
    raise ValueError("Chapter 8 structure report is not a clean pass")
identities = structure.get("identities", {})
if identities.get("source", {}).get("sha256") != EXPECTED_SOURCE_SHA256:
    raise ValueError("Chapter 8 authority hash differs from admitted evidence")
if identities.get("target", {}).get("sha256") != EXPECTED_TARGET_SHA256:
    raise ValueError("Chapter 8 target hash differs from admitted evidence")
if identities.get("wrapper", {}).get("sha256") != EXPECTED_WRAPPER_SHA256:
    raise ValueError("Chapter 8 wrapper hash differs from admitted evidence")
topology = structure.get("environment_topology", {})
if topology.get("count") != 24:
    raise ValueError("Chapter 8 environment closure differs from 24")
if topology.get("counts_by_name") != {
    "aligned": 5,
    "cases": 2,
    "equation": 15,
    "proof": 1,
    "theorem": 1,
}:
    raise ValueError("Chapter 8 environment counts differ")
if not topology.get("ordered_begin_equal") or not topology.get("ordered_end_equal"):
    raise ValueError("Chapter 8 ordered environment topology differs")
if structure.get("stable_segment_ids") != [
    f"d90.hab.v1.ch08.seg{order:04d}" for order in range(1, 4)
]:
    raise ValueError("Chapter 8 segment closure differs from three stable IDs")
if structure.get("labels") != {
    "source": ["stochastic:eq:gradient"],
    "target": ["stochastic:eq:gradient"],
}:
    raise ValueError("Chapter 8 label closure differs")
if structure.get("eqrefs") != {
    "source": ["stochastic:eq:gradient"],
    "target": ["stochastic:eq:gradient"],
}:
    raise ValueError("Chapter 8 eqref closure differs")
other = structure.get("other_surface_topology", {})
for surface in (
    "citations",
    "external_assets",
    "figures",
    "footnotes",
    "items",
    "sections",
    "source_inputs",
):
    if other.get(surface) != {"source": 0, "target": 0}:
        raise ValueError(f"Chapter 8 {surface} closure differs from zero")
if not structure.get("source_marker_closure", {}).get(
    "all_nonblank_source_lines_covered_exactly_once"
):
    raise ValueError("Chapter 8 source-line closure is incomplete")
formula = structure.get("formula_delta_manifest", {})
if formula.get("sha256") != EXPECTED_FORMULA_MANIFEST_SHA256:
    raise ValueError("Chapter 8 formula-delta manifest differs")
if not formula.get("all_substantive_deltas_proposed_ledger_bound"):
    raise ValueError("Chapter 8 contains an unbound substantive formula delta")
for field, expected in {
    "source_formula_count": 38,
    "target_formula_count": 61,
    "delta_block_count": 7,
    "substantive_delta_block_count": 7,
}.items():
    if formula.get(field) != expected:
        raise ValueError(f"Chapter 8 formula closure has wrong {field}")
review = structure.get("independent_review", {})
if review.get("severity_counts") != {"P1": 0, "P2": 0, "P3": 0}:
    raise ValueError("Chapter 8 independent review is not P1=P2=P3=0")
proposal = structure.get("proposed_ledger", {})
if proposal.get("ids_in_order") != EXPECTED_LEDGER_IDS or not proposal.get(
    "exact_event_closure"
):
    raise ValueError("Chapter 8 proposed correction closure differs")
if solver.get("status") != "PASS":
    raise ValueError("Chapter 8 stochastic validator is not a pass")
summary = solver.get("summary", {})
if summary.get("gate_count") != 24 or summary.get("passed_gate_count") != 24:
    raise ValueError("Chapter 8 stochastic validator does not pass 24/24 gates")
if summary.get("failed_gate_count") != 0:
    raise ValueError("Chapter 8 stochastic validator reports a failed gate")

expected_files = {
    SOURCE_PATH: (4665, EXPECTED_SOURCE_SHA256),
    TARGET_PATH: (6378, EXPECTED_TARGET_SHA256),
    WRAPPER_PATH: (5129, EXPECTED_WRAPPER_SHA256),
    OUTPUT_PDF_PATH: (346785, EXPECTED_PDF_SHA256),
    BUILD_LOG_PATH: (98530, EXPECTED_BUILD_LOG_SHA256),
    TEXT_PATH: (13751, EXPECTED_TEXT_SHA256),
    "qa/STOCHASTIC_STRUCTURE_REPORT.json": (12202, EXPECTED_STRUCTURE_REPORT_SHA256),
    "qa/STOCHASTIC_FORMULA_DELTA_MANIFEST.json": (24702, EXPECTED_FORMULA_MANIFEST_SHA256),
    "qa/STOCHASTIC_SOLVER_RESULTS.json": (21107, EXPECTED_SOLVER_RESULTS_SHA256),
    "qa/CHAPTER08_PROPOSED_LEDGER.jsonl": (5188, EXPECTED_PROPOSED_LEDGER_SHA256),
    "00_control/ADVERSE_LEDGER.jsonl": (48760, EXPECTED_INTEGRATED_LEDGER_SHA256),
    WORKLOG_PATH: (7780, EXPECTED_WORKLOG_SHA256),
    "qa/audit_stochastic_unit.py": (29112, EXPECTED_AUDIT_SOURCE_SHA256),
    "qa/validate_stochastic_unit.py": (18417, EXPECTED_SOLVER_SOURCE_SHA256),
}
for relative, expected in expected_files.items():
    if file_info(relative) != expected:
        raise ValueError(f"Chapter 8 frozen artifact differs: {relative}")

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
        raise ValueError(f"Chapter 8 build log contains forbidden diagnostic: {forbidden}")
if "Output written on" not in build_log or "(8 pages" not in build_log:
    raise ValueError("Chapter 8 build log does not prove an eight-page output")

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
    raise ValueError("Chapter 8 proposed ledger order differs")
for event_id in EXPECTED_LEDGER_IDS:
    if integrated_by_id.get(event_id) != proposal_by_id[event_id]:
        raise ValueError(f"integrated correction differs from proposal: {event_id}")


# Component-specific source, derivative, and open-validation rights.
for record_id, component_id, path, status, notes in [
    (
        "rights.o015-habring-ch08-source",
        "o015-habring-ch08-text",
        SOURCE_PATH,
        "admitted",
        "Chapter 8 authority source; all eight mathematical corrections are explicit records.",
    ),
    (
        "rights.o015-habring-id-ch08",
        "o015-habring-id-unit-08",
        TARGET_PATH,
        "derivative",
        "Independent id-ID translation of Chapter 8 and its standalone wrapper.",
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

solver_right = common("rights", "rights.o015-stochastic-solver-validation", "admitted")
solver_right.update(
    {
        "component_id": "o015-solver-validation-08",
        "path": "qa/validate_stochastic_unit.py",
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": "qa/validate_stochastic_unit.py",
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with results", "no proprietary runtime"],
        "notes": "Exact-arithmetic projected-SGD witnesses and negative controls.",
    }
)
add(solver_right)


unit = common("unit", "unit.habring.v1.ch08", "built")
unit.update(
    {
        "edition_id": "edition.habring.convex-optimization.id-id.v1",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "parent_id": "unit.habring.v1",
        "unit_kind": "chapter",
        "order": 8,
        "source_local_id": "chapter-8",
        "source_local_label": "8 — Stochastic Gradient Descent",
        "target_local_label": "8 — Penurunan Gradien Stokastik",
        "source_locator": f"{SOURCE_PATH}:1-107",
        "target_locator": f"{TARGET_PATH}:1-133",
        "rights_id": "rights.o015-habring-id-ch08",
        "translation_state": "built",
    }
)
add(unit)


concept_specs = [
    ("concept.finite-sum-optimization", "finite-sum optimization objective", []),
    ("concept.stochastic-subgradient-oracle", "unbiased stochastic subgradient oracle", ["concept.subgradient"]),
    ("concept.stochastic-gradient-descent", "stochastic gradient descent", ["concept.stochastic-subgradient-oracle"]),
    ("concept.conditional-stochastic-oracle", "conditionally unbiased bounded-variance stochastic oracle", ["concept.stochastic-subgradient-oracle"]),
    ("concept.projected-stochastic-gradient-descent", "projected stochastic gradient descent", ["concept.stochastic-gradient-descent", "concept.metric-projection"]),
    ("concept.stochastic-best-iterate-bound", "expected best-iterate bound for projected stochastic subgradient descent", ["concept.projected-stochastic-gradient-descent", "concept.best-iterate-rate", "concept.conditional-stochastic-oracle"]),
    ("concept.stochastic-step-size-condition", "stochastic best-iterate step-size condition", ["concept.diminishing-step-size"]),
]
for concept_id, label, prerequisites in concept_specs:
    concept = common("concept", concept_id, "current")
    concept.update(
        {
            "canonical_label": label,
            "prerequisite_ids": prerequisites,
            "domain": "stochastic convex optimization",
        }
    )
    add(concept)

term_specs = [
    ("term.finite-sum-problem", "concept.finite-sum-optimization", "finite-sum problem", "masalah jumlah hingga", [], 1),
    ("term.stochastic-gradient-estimator", "concept.stochastic-subgradient-oracle", "unbiased stochastic gradient estimate", "estimasi gradien stokastik tak bias", [], 1),
    ("term.stochastic-gradient-descent", "concept.stochastic-gradient-descent", "stochastic gradient descent", "penurunan gradien stokastik", ["SGD"], 1),
    ("term.iid", "concept.stochastic-gradient-descent", "independent and identically distributed", "saling bebas dan berdistribusi identik", ["iid"], 1),
    ("term.filtration", "concept.conditional-stochastic-oracle", "filtration", "filtrasi", [], 2),
    ("term.conditional-expectation", "concept.conditional-stochastic-oracle", "conditional expectation", "ekspektasi bersyarat", [], 2),
    ("term.conditional-variance", "concept.conditional-stochastic-oracle", "conditional variance", "varians bersyarat", [], 2),
    ("term.projected-stochastic-gradient-descent", "concept.projected-stochastic-gradient-descent", "projected stochastic gradient descent", "penurunan gradien stokastik terproyeksi", ["SGD terproyeksi"], 2),
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
            "scope": "stochastic convex optimization",
            "register": "formal",
            "evidence_segment_ids": [f"d90.hab.v1.ch08.seg{segment_order:04d}"],
            "examples": [preferred],
            "rights_id": "rights.o015-habring-id-ch08",
        }
    )
    add(term)


segment_specs = [
    (1, 1, 34, 3, 37, "Finite-sum motivation, sampling, and unbiasedness", "Motivasi jumlah hingga, pengambilan sampel, dan ketakbiasan", ["concept.finite-sum-optimization", "concept.stochastic-subgradient-oracle", "concept.stochastic-gradient-descent"]),
    (2, 36, 50, 41, 63, "Projected-SGD theorem and stochastic assumptions", "Teorema SGD terproyeksi dan asumsi stokastik", ["concept.conditional-stochastic-oracle", "concept.projected-stochastic-gradient-descent", "concept.stochastic-step-size-condition", "concept.stochastic-best-iterate-bound"]),
    (3, 51, 107, 67, 133, "Conditional recursion, telescoping, and best-iterate convergence", "Rekurensi bersyarat, penjumlahan teleskopik, dan konvergensi iterat terbaik", ["concept.conditional-stochastic-oracle", "concept.projected-stochastic-gradient-descent", "concept.stochastic-best-iterate-bound", "concept.stochastic-step-size-condition"]),
]
for order, s_start, s_end, t_start, t_end, source_label, target_label, concept_ids in segment_specs:
    segment_id = f"d90.hab.v1.ch08.seg{order:04d}"
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, s_start, s_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, t_start, t_end)
    segment = common("segment", segment_id, "current")
    segment.update(
        {
            "unit_id": "unit.habring.v1.ch08",
            "order": order,
            "source_local_id": f"chapter-8-lines-{s_start}-{s_end}",
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
            "rights_id": "rights.o015-habring-id-ch08",
            "evidence_event_ids": [
                "qa.o015.ch08.structure",
                "qa.o015.ch08.formula-delta",
                "qa.o015.ch08.solver",
                "qa.o015.ch08.build",
                "qa.o015.ch08.math-rereview",
                "qa.o015.ch08.visual",
                "qa.o015.ch08.accessibility",
            ],
        }
    )
    add(segment)


# The authority has no exercises, hints, answers, solutions, or assets.
for surface_type in ("exercise", "hint", "answer", "solution", "asset"):
    surface = common(
        "learning_surface",
        f"surface.habring.v1.ch08.{surface_type}-inventory",
        "source_absent",
    )
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch08",
            "surface_type": surface_type,
            "presence": "absent",
            "count": 0,
            "absence_evidence": "qa/STOCHASTIC_STRUCTURE_REPORT.json",
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
            "rights_id": "rights.o015-habring-id-ch08",
        }
    )
    add(surface)


correction_specs = {
    76: (13, 34, [1]),
    77: (36, 59, [2, 3]),
    78: (42, 75, [2, 3]),
    79: (37, 106, [2, 3]),
    80: (60, 75, [3]),
    81: (83, 88, [3]),
    82: (37, 106, [2, 3]),
    83: (17, 73, [1, 2, 3]),
}
for number in range(76, 84):
    event_id = f"O015-HAB-ADV-{number:04d}"
    event = integrated_by_id[event_id]
    source_start, source_end, segment_orders = correction_specs[number]
    correction = common("correction", f"correction.o015-hab-adv-{number:04d}", "applied")
    correction.update(
        {
            "source_event_id": event_id,
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "affected_unit_ids": ["unit.habring.v1.ch08"],
            "affected_segment_ids": [
                f"d90.hab.v1.ch08.seg{order:04d}" for order in segment_orders
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


for record in [
    artifact("artifact.habring.source-ch08", "source_tex", SOURCE_PATH, source_edition_id="edition.habring.convex-optimization.arxiv-2607-11664v1", rights_id="rights.o015-habring-ch08-source"),
    artifact("artifact.habring.target-ch08", "target_tex", TARGET_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch08"),
    artifact("artifact.habring.target-wrapper-ch08", "target_tex", WRAPPER_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch08"),
    artifact("artifact.habring.structure-report-ch08", "qa_report", "qa/STOCHASTIC_STRUCTURE_REPORT.json", toolchain="qa/audit_stochastic_unit.py", formula_delta_manifest_sha256=EXPECTED_FORMULA_MANIFEST_SHA256),
    artifact("artifact.habring.formula-manifest-ch08", "qa_report", "qa/STOCHASTIC_FORMULA_DELTA_MANIFEST.json", toolchain="qa/audit_stochastic_unit.py"),
    artifact("artifact.habring.structure-audit-ch08", "qa_source", "qa/audit_stochastic_unit.py", toolchain="Python 3 standard library"),
    artifact("artifact.habring.solver-results-ch08", "qa_report", "qa/STOCHASTIC_SOLVER_RESULTS.json", toolchain="Python 3.13.9 exact arithmetic", rights_id="rights.o015-stochastic-solver-validation"),
    artifact("artifact.habring.solver-validator-ch08", "qa_source", "qa/validate_stochastic_unit.py", toolchain="Python 3.13.9 exact arithmetic", rights_id="rights.o015-stochastic-solver-validation"),
    artifact("artifact.habring.proposed-ledger-ch08", "correction_proposal", "qa/CHAPTER08_PROPOSED_LEDGER.jsonl", source_artifact_id="artifact.habring.source-ch08"),
    artifact("artifact.habring.worklog-ch08", "qa_receipt", WORKLOG_PATH, source_artifact_id="artifact.habring.source-ch08"),
    artifact("artifact.habring.build-log-ch08", "build_receipt", BUILD_LOG_PATH, build_event_id="qa.o015.ch08.build", toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber"),
    artifact("artifact.habring.target-pdf-ch08", "reader_pdf", OUTPUT_PDF_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch08", pages=8, build_event_id="qa.o015.ch08.build", toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber", accessibility="searchable id-ID PDF; untagged", input_artifact_ids=["artifact.habring.target-wrapper-ch08", "artifact.habring.target-ch08", "artifact.habring.target-macros", "artifact.habring.target-class", "artifact.habring.references-bib"]),
    artifact("artifact.habring.target-text-ch08", "qa_extract", TEXT_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", source_artifact_id="artifact.habring.target-pdf-ch08"),
    artifact("artifact.o015.backend-generator-ch08", "qa_source", "qa/extend_backend_ch08.py", toolchain="Python 3 standard library"),
]:
    add(record)


qa_specs = [
    {"id": "qa.o015.ch08.source-freeze", "status": "pass", "event_type": "source", "result": "pass", "witness_artifact_ids": ["artifact.habring.source-ch08"], "authority_id": "o015-habring-arxiv-2607.11664v1", "source_sha256": EXPECTED_SOURCE_SHA256},
    {"id": "qa.o015.ch08.structure", "status": "pass", "event_type": "topology", "result": "pass", "witness_artifact_ids": ["artifact.habring.structure-report-ch08"], "environment_topology_equal": True, "environment_count": 24, "environment_counts": topology["counts_by_name"], "failures": [], "segment_count": 3, "label_occurrences_preserved": 1, "eqref_occurrences_preserved": 1, "citations": 0, "figures": 0, "assets": 0, "footnotes": 0, "exercises": 0, "hints": 0, "answers": 0, "solutions": 0},
    {"id": "qa.o015.ch08.formula-delta", "status": "pass", "event_type": "mathematics", "result": "pass", "witness_artifact_ids": ["artifact.habring.structure-report-ch08", "artifact.habring.formula-manifest-ch08", "artifact.habring.proposed-ledger-ch08"], "formula_delta_manifest_sha256": EXPECTED_FORMULA_MANIFEST_SHA256, "source_formula_surfaces": 38, "target_formula_surfaces": 61, "formula_delta_blocks": 7, "substantive_formula_delta_blocks": 7, "correction_events": 8, "disposition": "Every substantive mathematical delta is correction-ledger bound."},
    {"id": "qa.o015.ch08.solver", "status": "pass", "event_type": "computation", "result": "pass", "witness_artifact_ids": ["artifact.habring.solver-results-ch08", "artifact.habring.solver-validator-ch08"], "checks": ["finite-sum normalization and missing-N negative control", "conditional mean, variance, and second moment", "projection and one-step recurrence", "ten exact best-iterate cases", "extra-Q_K asymptotic negative control", "24 live gates"], "python": "3.13.9", "arithmetic": "fractions.Fraction exact arithmetic plus deterministic floating asymptotic witnesses"},
    {"id": "qa.o015.ch08.build", "status": "pass", "event_type": "build", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-pdf-ch08", "artifact.habring.build-log-ch08"], "toolchain": "pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber", "pages": 8, "page_size": "A4", "deterministic_rebuild": "byte-identical", "errors": [], "undefined_references": 0, "multiply_defined_labels": 0, "replacement_glyphs": 0, "overfull_boxes": 0, "underfull_boxes": 0},
    {"id": "qa.o015.ch08.visual", "status": "pass", "event_type": "visual", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-pdf-ch08"], "pages_inspected": 8, "method": "All pages rendered and inspected against the frozen PDF bytes.", "findings": []},
    {"id": "qa.o015.ch08.accessibility", "status": "pass_with_limitation", "event_type": "accessibility", "result": "pass_with_limitation", "witness_artifact_ids": ["artifact.habring.target-pdf-ch08", "artifact.habring.target-text-ch08"], "checks": ["PDF language metadata is id-ID.", "PDF is unencrypted and searchable.", "Text extraction is retained as an exact artifact.", "No figures require alternative text in this chapter."], "limitations": ["PDF is untagged."]},
    {"id": "qa.o015.ch08.math-rereview", "status": "pass", "event_type": "mathematics", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-ch08", "artifact.habring.structure-report-ch08", "artifact.habring.solver-results-ch08"], "verified_at": RECORDED_AT, "target_sha256": EXPECTED_TARGET_SHA256, "review_outcome": {"p1": 0, "p2": 0, "p3": 0}, "scope": "Independent source/target/wrapper/ledger rereview of the complete stochastic-gradient chapter."},
    {"id": "qa.o015.ch08.language", "status": "not_recorded", "event_type": "language", "result": "not_recorded", "witness_artifact_ids": [], "gap": "No independent Indonesian language review is recorded."},
]
for spec in qa_specs:
    qa = common("qa_event", spec["id"], spec["status"])
    qa.update(
        {
            "unit_id": "unit.habring.v1.ch08",
            **{key: value for key, value in spec.items() if key not in {"id", "status"}},
        }
    )
    add(qa)


relation_specs: list[tuple[str, str, str, str, str]] = [
    ("relation.unit.root-contains-ch08", "contains", "unit.habring.v1", "unit.habring.v1.ch08", "Source Chapter 8."),
    ("relation.unit.ch07-precedes-ch08", "precedes", "unit.habring.v1.ch07", "unit.habring.v1.ch08", "Contiguous admitted source order."),
    ("relation.unit.ch08-depends-on-ch04", "depends-on", "unit.habring.v1.ch08", "unit.habring.v1.ch04", "Projected stochastic descent reuses metric projection and best-iterate analysis."),
    ("relation.unit.ch08-prerequisite-subgradient", "prerequisite", "unit.habring.v1.ch08", "concept.subgradient", "The oracle mean is a convex subgradient."),
    ("relation.unit.ch08-prerequisite-projection", "prerequisite", "unit.habring.v1.ch08", "concept.metric-projection", "The iteration projects onto a nonempty closed convex set."),
    ("relation.unit.ch08-prerequisite-best-iterate", "prerequisite", "unit.habring.v1.ch08", "concept.best-iterate-rate", "The proof uses a weighted best-iterate estimate."),
]
for order in range(1, 4):
    relation_specs.append((f"relation.unit.ch08-contains-seg{order:04d}", "contains", "unit.habring.v1.ch08", f"d90.hab.v1.ch08.seg{order:04d}", "Ordered reader-facing translation segment."))
relation_specs.extend(
    [
        ("relation.segment.ch08-seg0001-defines-finite-sum", "defines", "d90.hab.v1.ch08.seg0001", "concept.finite-sum-optimization", "Normalized finite-sum learning objective."),
        ("relation.segment.ch08-seg0001-defines-stochastic-oracle", "defines", "d90.hab.v1.ch08.seg0001", "concept.stochastic-subgradient-oracle", "Uniform component sampling gives an unbiased oracle."),
        ("relation.segment.ch08-seg0001-defines-sgd", "defines", "d90.hab.v1.ch08.seg0001", "concept.stochastic-gradient-descent", "Basic stochastic update."),
        ("relation.segment.ch08-seg0002-defines-conditional-oracle", "defines", "d90.hab.v1.ch08.seg0002", "concept.conditional-stochastic-oracle", "Filtration-conditioned unbiasedness and variance."),
        ("relation.segment.ch08-seg0002-defines-projected-sgd", "defines", "d90.hab.v1.ch08.seg0002", "concept.projected-stochastic-gradient-descent", "Well-posed projected stochastic iteration."),
        ("relation.segment.ch08-seg0002-defines-step-condition", "defines", "d90.hab.v1.ch08.seg0002", "concept.stochastic-step-size-condition", "Divergent step sum and vanishing squared-step ratio."),
        ("relation.segment.ch08-seg0003-proves-best-iterate", "proves", "d90.hab.v1.ch08.seg0003", "concept.stochastic-best-iterate-bound", "Conditional recurrence, telescoping, and expected convergence."),
        ("relation.segment.ch08-seg0003-depends-on-projection", "depends-on", "d90.hab.v1.ch08.seg0003", "concept.metric-projection", "Nonexpansiveness initiates the recurrence."),
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
    add(relation)


# Refresh every artifact to its live bytes.  Only four exact baseline artifact
# IDs may differ; every non-artifact and every other pre-Chapter 8 record must
# remain byte-for-byte canonical-identical.
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
unexpected_changed_ids = sorted(
    set(changed_baseline_ids) - ALLOWED_BASELINE_ARTIFACT_REFRESH_IDS
)
if missing_baseline_ids or unexpected_changed_ids:
    raise ValueError(
        "Chapter 8 extension changed the pre-Chapter 8 baseline: "
        f"missing={missing_baseline_ids}, unexpected_changed={unexpected_changed_ids}"
    )
for record_id in changed_baseline_ids:
    if next(record for record in records if record["id"] == record_id).get("entity_type") != "artifact":
        raise ValueError(f"semantic baseline record changed: {record_id}")

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
segment_counts = Counter(
    record["unit_id"] for record in records if record["entity_type"] == "segment"
)
print(
    json.dumps(
        {
            "added_entity_counts": dict(sorted(added_counts.items())),
            "added_record_count": len(generated_ids),
            "baseline_comparison": {
                "allowed_artifact_refresh_ids": sorted(ALLOWED_BASELINE_ARTIFACT_REFRESH_IDS),
                "baseline_record_count": len(baseline_records),
                "changed_artifact_ids": changed_baseline_ids,
                "missing_record_ids": missing_baseline_ids,
                "preserved_semantic_record_count": sum(
                    record["entity_type"] != "artifact" for record in baseline_records
                ),
                "preserved_record_count_excluding_live_artifact_refreshes": len(baseline_ids) - len(changed_baseline_ids),
                "result": "pass",
                "unexpected_changed_record_ids": unexpected_changed_ids,
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
            "segment_distribution": dict(sorted(segment_counts.items())),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
