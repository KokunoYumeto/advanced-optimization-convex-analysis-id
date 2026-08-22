#!/usr/bin/env python3
"""Deterministically extend the O015 backend through Habring Chapter 9.

The exact 670-record Chapter 3--8 backend is the semantic baseline.  On a
rerun, this script removes only its own Chapter 9 closure, re-proves every
frozen Chapter 9 witness, adds that closure again, refreshes live artifact
identities, and writes the canonical JSONL/lossless CSV pair.  No pre-Chapter
9 semantic record may change; the only admitted baseline changes are current
hash/byte refreshes for explicitly enumerated artifact/control records.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "backend" / "backend_schema.json"
JSONL_PATH = ROOT / "backend" / "records.jsonl"
CSV_PATH = ROOT / "backend" / "records.csv"
LEDGER_PATH = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
PROPOSED_LEDGER_PATH = ROOT / "qa" / "CHAPTER09_PROPOSED_LEDGER.jsonl"
STRUCTURE_REPORT_PATH = ROOT / "qa" / "OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json"
FORMULA_MANIFEST_PATH = ROOT / "qa" / "OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json"
SOLVER_RESULTS_PATH = ROOT / "qa" / "OPTIMAL_TRANSPORT_SOLVER_RESULTS.json"

RECORDED_AT = "2026-08-22T16:45:00Z"
WORKFLOW = "o015-habring-ch09-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

SOURCE_PATH = "authority/habring/source-v1/optimal_transport.tex"
TARGET_PATH = "source/id-ID/habring-09-transportasi-optimal-id.tex"
WRAPPER_PATH = "source/id-ID/D90-HAB-09-transportasi-optimal-id.tex"
OUTPUT_PDF_PATH = "output/pdf/D90-HAB-09-transportasi-optimal-id.pdf"
TEXT_PATH = "qa/D90-HAB-09-transportasi-optimal-id.txt"
BUILD_LOG_PATH = "build/habring-unit-09-id/D90-HAB-09-transportasi-optimal-id.log"
WORKLOG_PATH = "qa/CHAPTER09_WORKLOG.md"
AUDIT_SOURCE_PATH = "qa/audit_optimal_transport_unit.py"
SOLVER_SOURCE_PATH = "qa/validate_optimal_transport_unit.py"
LOCAL_BIB_PATH = "source/id-ID/references-ot-id.bib"
AUTHORITY_BIB_PATH = "authority/habring/source-v1/references.bib"

EXPECTED_SOURCE_SHA256 = "719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba"
EXPECTED_TARGET_SHA256 = "45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd"
EXPECTED_WRAPPER_SHA256 = "1e308a2bed0d1a6f5cdcff09cce932674cf32842a135bc88a5a34bc96c483ff6"
EXPECTED_LOCAL_BIB_SHA256 = "93611c4b6a753478c51c601e59ef6cd3e290677e2e2d25b104d5d3b74df03126"
EXPECTED_AUTHORITY_BIB_SHA256 = "e334d49a9df665d3cb5902f8874a24e44be601f26fafb07fa21406690e473f20"
EXPECTED_PDF_SHA256 = "edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214"
EXPECTED_BUILD_LOG_SHA256 = "2b083221c49f6fbdede8f541e68cd9129632a74168d7855c1ddc14c1bf48b3a4"
EXPECTED_SOLVER_RESULTS_SHA256 = "4f751c615f2d7f03622b1447b3985ad1d660bd4f758cf4c4fb61d4d384b4e7a0"
EXPECTED_PROPOSED_LEDGER_SHA256 = "643fde3fbe1409732ef2df8fdef52465e4df7a583fd9bbeb2137a6122f548add"
EXPECTED_INTEGRATED_LEDGER_SHA256 = "09a982c3e91f83655150f7ae29a6351cb071558ed14a36cbb3701d7f43e9d824"
EXPECTED_SOLVER_SOURCE_SHA256 = "e574ea3e7f924a3d1becb148162faec27ae715040665b06def284f11990500c0"
EXPECTED_STRUCTURE_REPORT_SHA256 = "eb8b194c01dd7610dcdb7325322765ab16b3ec9cf907d28f9463fa11692767aa"
EXPECTED_FORMULA_MANIFEST_SHA256 = "796e13fbf1f221139f0233d30b2464dfb026027eb5b9ce44b66b58c2f2e169ef"
EXPECTED_TEXT_SHA256 = "283864c3fc84d414ff721f128a0f10e4b61b4646c0f5edcd53551ee13f911859"
EXPECTED_WORKLOG_SHA256 = "0527b8b61dee2ffccd493e8331b7d57f592ba3ec9b5ef87226c15cb1a342e99e"
EXPECTED_AUDIT_SOURCE_SHA256 = "5c4c030ac4512a0b0785053c19b5ed2eb1a6d35bb4147cac6fe8842807c43a5c"

EXPECTED_LEDGER_IDS = [f"O015-HAB-ADV-{number:04d}" for number in range(84, 96)]
EXPECTED_ALL_LEDGER_IDS = EXPECTED_LEDGER_IDS + ["O015-HAB-ADV-0096"]
EXPECTED_SEGMENT_IDS = [f"d90.hab.v1.ch09.seg{order:04d}" for order in range(1, 10)]
EXPECTED_BIBLIOGRAPHY_EVENT = {
    "event_id": "O015-HAB-ADV-0096",
    "authority": "o015-habring-arxiv-2607.11664v1",
    "source": "references.bib",
    "surface": "Villani bibliography author metadata and rendered name",
    "source_issue": "The frozen bibliography records the sole-authored book as `Villani, Cédric and others`; BibLaTeX consequently renders the visible citation and bibliography name as `Villani andothers`, while the publisher's primary metadata identifies Cédric Villani as the sole author.",
    "target_action": "Kept the frozen authority file unchanged, supplied a unit-local corrected bibliography entry naming Cédric Villani as sole author and adding the publisher DOI, and bound the standalone wrapper to that corrected metadata.",
    "class": "determined_bibliographic_metadata_and_rendering_correction",
}

FROZEN_FILES: dict[str, tuple[int, str]] = {
    SOURCE_PATH: (15378, EXPECTED_SOURCE_SHA256),
    TARGET_PATH: (21252, EXPECTED_TARGET_SHA256),
    WRAPPER_PATH: (6822, EXPECTED_WRAPPER_SHA256),
    LOCAL_BIB_PATH: (306, EXPECTED_LOCAL_BIB_SHA256),
    AUTHORITY_BIB_PATH: (614, EXPECTED_AUTHORITY_BIB_SHA256),
    OUTPUT_PDF_PATH: (498244, EXPECTED_PDF_SHA256),
    BUILD_LOG_PATH: (103255, EXPECTED_BUILD_LOG_SHA256),
    TEXT_PATH: (30053, EXPECTED_TEXT_SHA256),
    "qa/OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json": (19924, EXPECTED_STRUCTURE_REPORT_SHA256),
    "qa/OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json": (79141, EXPECTED_FORMULA_MANIFEST_SHA256),
    "qa/OPTIMAL_TRANSPORT_SOLVER_RESULTS.json": (16970, EXPECTED_SOLVER_RESULTS_SHA256),
    "qa/CHAPTER09_PROPOSED_LEDGER.jsonl": (8840, EXPECTED_PROPOSED_LEDGER_SHA256),
    "00_control/ADVERSE_LEDGER.jsonl": (58370, EXPECTED_INTEGRATED_LEDGER_SHA256),
    WORKLOG_PATH: (9661, EXPECTED_WORKLOG_SHA256),
    AUDIT_SOURCE_PATH: (44280, EXPECTED_AUDIT_SOURCE_SHA256),
    SOLVER_SOURCE_PATH: (26029, EXPECTED_SOLVER_SOURCE_SHA256),
}

GENERATED_CONCEPT_IDS = {
    "concept.measurable-probability-space",
    "concept.pushforward-measure",
    "concept.monge-optimal-transport",
    "concept.transport-coupling",
    "concept.kantorovich-optimal-transport",
    "concept.kantorovich-existence",
    "concept.wasserstein-distance",
    "concept.kantorovich-duality",
    "concept.discrete-optimal-transport",
    "concept.entropic-optimal-transport",
    "concept.entropic-plan-factorization",
    "concept.sinkhorn-knopp-algorithm",
}
GENERATED_TERM_IDS = {
    "term.optimal-transport",
    "term.pushforward-measure",
    "term.monge-optimal-transport",
    "term.kantorovich-optimal-transport",
    "term.transport-plan",
    "term.coupling",
    "term.wasserstein-distance",
    "term.kantorovich-duality",
    "term.transport-polytope",
    "term.entropic-regularization",
    "term.gibbs-kernel",
    "term.sinkhorn-knopp-algorithm",
}
GENERATED_EXACT_IDS = {
    "unit.habring.v1.ch09",
    "rights.o015-habring-ch09-source",
    "rights.o015-habring-id-ch09",
    "rights.o015-habring-ch09-inline-tikz",
    "rights.o015-habring-ch09-local-bibliography",
    "rights.o015-optimal-transport-solver-validation",
    "relation.unit.root-contains-ch09",
    "relation.unit.ch08-precedes-ch09",
    "artifact.o015.backend-generator-ch09",
    "asset.habring.v1.ch09.transport-map-tikz",
    "asset.habring.v1.ch09.local-bibliography",
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
        "d90.hab.v1.ch09.",
        "surface.habring.v1.ch09.",
        "qa.o015.ch09.",
        "relation.unit.ch09-",
        "relation.segment.ch09-",
        "relation.surface.ch09-",
        "relation.artifact.ch09-",
    )
    if record_id.startswith(prefixes):
        return True
    if record_id.startswith("artifact.habring.") and record_id.endswith("-ch09"):
        return True
    if record_id.startswith("correction.o015-hab-adv-"):
        return 84 <= int(record_id.rsplit("-", 1)[1]) <= 96
    return False


def extract(pattern: str, text: str) -> list[str]:
    return [match.group(1) for match in re.finditer(pattern, text)]


schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
existing_records = [
    json.loads(line)
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
records = [record for record in existing_records if not is_generated(record)]
if len(records) != 670:
    raise ValueError(f"Chapter 8 baseline has {len(records)} records, expected 670")
if any(record.get("unit_id") == "unit.habring.v1.ch09" for record in records):
    raise ValueError("Chapter 8 baseline unexpectedly retains a Chapter 9 unit reference")
baseline_records = [dict(record) for record in records]
baseline_by_id = {record["id"]: canonical_json(record) for record in baseline_records}
baseline_ids = set(baseline_by_id)
generated_ids: set[str] = set()


def add(record: dict[str, Any]) -> None:
    record_id = record["id"]
    if record_id in baseline_ids or record_id in generated_ids:
        raise ValueError(f"stable-ID collision while adding Chapter 9: {record_id}")
    generated_ids.add(record_id)
    records.append(record)


# Prove every frozen file before constructing records.
for relative, expected in FROZEN_FILES.items():
    if file_info(relative) != expected:
        raise ValueError(f"Chapter 9 frozen artifact differs: {relative}")

source_text = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
target_text = (ROOT / TARGET_PATH).read_text(encoding="utf-8")
wrapper_text = (ROOT / WRAPPER_PATH).read_text(encoding="utf-8")
worklog_text = (ROOT / WORKLOG_PATH).read_text(encoding="utf-8")
for severity in ("P1", "P2", "P3"):
    if not re.search(rf"\b{severity}\s*(?:=|:)\s*0\b", worklog_text):
        raise ValueError(f"Chapter 9 worklog does not record {severity}=0")
if "independent" not in worklog_text.lower() and "independen" not in worklog_text.lower():
    raise ValueError("Chapter 9 worklog does not identify an independent rereview")

expected_environment_counts = {
    "aligned": 7,
    "cases": 3,
    "defn": 4,
    "enumerate": 1,
    "equation": 22,
    "figure": 1,
    "lemma": 1,
    "proof": 3,
    "quote": 1,
    "rem": 1,
    "theorem": 2,
    "tikzpicture": 1,
}
source_environments = extract(r"\\begin\{([^}]+)\}", source_text)
target_environments = extract(r"\\begin\{([^}]+)\}", target_text)
if source_environments != target_environments:
    raise ValueError("Chapter 9 ordered begin-environment topology differs")
if dict(sorted(Counter(source_environments).items())) != expected_environment_counts:
    raise ValueError("Chapter 9 begin-environment counts differ")
source_end_environments = extract(r"\\end\{([^}]+)\}", source_text)
target_end_environments = extract(r"\\end\{([^}]+)\}", target_text)
if source_end_environments != target_end_environments:
    raise ValueError("Chapter 9 ordered end-environment topology differs")

expected_labels = [
    "ot:fig:ot",
    "ot:eq:monge",
    "ot:eq:K_ot",
    "ot:eq:duality",
    "ot:eq:disc_entropic",
]
if extract(r"\\label\{([^}]+)\}", source_text) != expected_labels:
    raise ValueError("Chapter 9 source label closure differs")
if extract(r"\\label\{([^}]+)\}", target_text) != expected_labels:
    raise ValueError("Chapter 9 target label closure differs")
expected_source_eqrefs = [
    "ot:eq:K_ot",
    "ot:eq:monge",
    "ot:eq:K_ot",
    "ot:eq:K_ot",
    "ot:eq:K_ot",
    "ot:eq:duality",
    "ot:eq:K_ot",
    "ot:eq:disc_entropic",
]
expected_target_eqrefs = expected_source_eqrefs + ["ot:eq:disc_entropic"]
if extract(r"\\eqref\{([^}]+)\}", source_text) != expected_source_eqrefs:
    raise ValueError("Chapter 9 source eqref closure differs")
if extract(r"\\eqref\{([^}]+)\}", target_text) != expected_target_eqrefs:
    raise ValueError("Chapter 9 target eqref closure differs")
for pattern, expected_source, expected_target, surface in [
    (r"\\cref\{([^}]+)\}", ["chapter:duality"], ["chapter:duality"], "cref"),
    (r"\\cite(?:\[[^\]]*\])?\{([^}]+)\}", ["villani2009optimal"], ["villani2009optimal", "villani2009optimal"], "citation"),
]:
    if extract(pattern, source_text) != expected_source or extract(pattern, target_text) != expected_target:
        raise ValueError(f"Chapter 9 {surface} closure differs")
for pattern, expected, surface in [
    (r"\\footnote\{", 3, "footnote"),
    (r"\\gls\{", 14, "glossary"),
    (r"\\item(?:\s|\[)", 2, "item"),
]:
    if len(re.findall(pattern, source_text)) != expected or len(re.findall(pattern, target_text)) != expected:
        raise ValueError(f"Chapter 9 {surface} count differs")

segment_specs = [
    (1, 1, 15, 3, 17, "Measure notation and probability measures", "Notasi ukuran dan ukuran probabilitas", ["concept.measurable-probability-space"]),
    (2, 16, 75, 20, 83, "Monge and Kantorovich transport illustration", "Ilustrasi transportasi Monge dan Kantorovich", ["concept.monge-optimal-transport"]),
    (3, 77, 110, 86, 123, "Push-forward, Monge transport, and Kantorovich couplings", "Hasil dorong, transportasi Monge, dan kopling Kantorovich", ["concept.pushforward-measure", "concept.monge-optimal-transport", "concept.transport-coupling", "concept.kantorovich-optimal-transport"]),
    (4, 112, 130, 126, 147, "Existence of optimal plans and Wasserstein distance", "Eksistensi rencana optimal dan jarak Wasserstein", ["concept.kantorovich-existence", "concept.wasserstein-distance"]),
    (5, 131, 141, 150, 163, "Kantorovich duality theorem", "Teorema dualitas Kantorovich", ["concept.kantorovich-duality"]),
    (6, 142, 190, 166, 230, "Weak duality, marginal indicator, and strong-duality step", "Dualitas lemah, indikator marginal, dan langkah dualitas kuat", ["concept.kantorovich-duality", "concept.transport-coupling"]),
    (7, 192, 226, 233, 273, "Discrete transport and entropic regularization", "Transportasi diskret dan regularisasi entropik", ["concept.discrete-optimal-transport", "concept.entropic-optimal-transport"]),
    (8, 229, 256, 276, 333, "Existence, uniqueness, positivity, and Gibbs factorization", "Eksistensi, keunikan, positivitas, dan faktorisasi Gibbs", ["concept.entropic-optimal-transport", "concept.entropic-plan-factorization"]),
    (9, 257, 264, 336, 352, "Sinkhorn--Knopp scaling iteration and convergence", "Iterasi penskalaan Sinkhorn--Knopp dan konvergensi", ["concept.entropic-plan-factorization", "concept.sinkhorn-knopp-algorithm"]),
]
target_lines = target_text.splitlines()
markers = [
    (number, match.group(1))
    for number, line in enumerate(target_lines, start=1)
    if (match := re.fullmatch(r"% segment-id: (\S+)", line))
]
if [marker_id for _, marker_id in markers] != EXPECTED_SEGMENT_IDS:
    raise ValueError("Chapter 9 target segment markers differ")
for (marker_line, marker_id), spec in zip(markers, segment_specs):
    if marker_id != f"d90.hab.v1.ch09.seg{spec[0]:04d}" or marker_line + 1 != spec[3]:
        raise ValueError(f"Chapter 9 target marker/locator mismatch: {marker_id}")
source_lines = source_text.splitlines()
covered_source_lines = {
    number
    for _, start, end, *_ in segment_specs
    for number in range(start, end + 1)
}
uncovered_nonblank = [
    number
    for number, line in enumerate(source_lines, start=1)
    if line.strip() and number not in covered_source_lines
]
if uncovered_nonblank:
    raise ValueError(f"Chapter 9 source segment closure misses lines {uncovered_nonblank}")

for required_wrapper_surface in (
    "CC BY 4.0",
    "bukan karya resmi atau dukungan Andreas Habring maupun TU Graz",
    "O015-HAB-ADV-0084 sampai O015-HAB-ADV-0096",
    "\\include{habring-09-transportasi-optimal-id}",
    "\\addbibresource{references-ot-id.bib}",
    "pdflang={id-ID}",
):
    if required_wrapper_surface not in wrapper_text:
        raise ValueError(f"Chapter 9 wrapper misses required surface: {required_wrapper_surface}")

structure = json.loads(STRUCTURE_REPORT_PATH.read_text(encoding="utf-8"))
formula_manifest = json.loads(FORMULA_MANIFEST_PATH.read_text(encoding="utf-8"))
solver = json.loads(SOLVER_RESULTS_PATH.read_text(encoding="utf-8"))
if structure.get("result") != "pass" or structure.get("failures") != []:
    raise ValueError("Chapter 9 structure report is not a clean pass")
if structure.get("mode") != "strict" or structure.get("strict_ready") is not True:
    raise ValueError("Chapter 9 structure report is not strict-ready")
for failure_field in (
    "failure_count",
    "content_failure_count",
    "strict_only_failure_count",
):
    if structure.get(failure_field) != 0:
        raise ValueError(f"Chapter 9 structure report has nonzero {failure_field}")
for name, expected_hash in {
    "source": EXPECTED_SOURCE_SHA256,
    "target": EXPECTED_TARGET_SHA256,
    "wrapper": EXPECTED_WRAPPER_SHA256,
}.items():
    if structure.get(name, {}).get("sha256") != expected_hash:
        raise ValueError(f"Chapter 9 structure report has wrong {name} identity")
local_bibliography = structure.get("local_bibliography", {})
if local_bibliography.get("sha256") != EXPECTED_LOCAL_BIB_SHA256:
    raise ValueError("Chapter 9 structure report has wrong local bibliography identity")
if local_bibliography.get("gates") != {
    "publisher_doi_present": True,
    "single_expected_entry": True,
    "sole_author_corrected": True,
    "source_and_others_removed": True,
}:
    raise ValueError("Chapter 9 local bibliography gates differ")
if structure.get("stable_segment_ids") != EXPECTED_SEGMENT_IDS:
    raise ValueError("Chapter 9 structure report has wrong stable segment closure")
proposal = structure.get("proposed_ledger", {})
if proposal.get("ids_in_order") != EXPECTED_LEDGER_IDS:
    raise ValueError("Chapter 9 proposed correction closure differs")

formula = structure.get("formula_delta_manifest", {})
if formula.get("sha256") != EXPECTED_FORMULA_MANIFEST_SHA256:
    raise ValueError("Chapter 9 structure report points to the wrong formula manifest")
if file_info("qa/OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json")[1] != EXPECTED_FORMULA_MANIFEST_SHA256:
    raise ValueError("Chapter 9 formula-delta manifest hash differs")
if formula_manifest.get("result") not in (None, "pass"):
    raise ValueError("Chapter 9 formula-delta manifest is not a pass")
all_bound = formula.get("all_substantive_deltas_proposed_ledger_bound")
if all_bound is None:
    all_bound = formula.get("all_substantive_deltas_ledger_bound")
if all_bound is not True:
    raise ValueError("Chapter 9 contains an unbound substantive formula delta")
if formula.get("all_substantive_deltas_integrated_ledger_bound") is not True:
    raise ValueError("Chapter 9 contains a formula delta unbound from the integrated ledger")
for key in ("unbound_substantive_delta_block_ids", "incompletely_bound_substantive_delta_block_ids"):
    if formula.get(key, []) != []:
        raise ValueError(f"Chapter 9 formula closure has nonempty {key}")
used_ledger_ids = formula.get("used_ledger_event_ids")
if used_ledger_ids is not None and used_ledger_ids != EXPECTED_LEDGER_IDS:
    raise ValueError("Chapter 9 formula manifest does not use the exact correction closure")
for key in (
    "unbound_substantive_delta_block_ids",
    "proposal_incomplete_substantive_delta_block_ids",
    "integration_incomplete_substantive_delta_block_ids",
    "unused_required_ledger_event_ids",
):
    if formula_manifest.get(key) != []:
        raise ValueError(f"Chapter 9 frozen formula manifest has nonempty {key}")
if formula_manifest.get("required_ledger_event_ids") != EXPECTED_LEDGER_IDS:
    raise ValueError("Chapter 9 formula manifest has the wrong required correction closure")
if formula_manifest.get("used_ledger_event_ids") != EXPECTED_LEDGER_IDS:
    raise ValueError("Chapter 9 formula manifest has the wrong used correction closure")
for field in (
    "source_formula_count",
    "target_formula_count",
    "delta_block_count",
    "substantive_delta_block_count",
):
    if not isinstance(formula.get(field), int) or formula[field] <= 0:
        raise ValueError(f"Chapter 9 formula closure has invalid {field}")

if solver.get("status") != "PASS":
    raise ValueError("Chapter 9 optimal-transport validator is not a pass")
summary = solver.get("summary", {})
if summary.get("gate_count") != 41 or summary.get("passed_gate_count") != 41:
    raise ValueError("Chapter 9 optimal-transport validator does not pass 41/41 gates")
if summary.get("failed_gate_count") != 0 or summary.get("negative_control_count") != 4:
    raise ValueError("Chapter 9 optimal-transport validator has wrong gate closure")
finite_ot = solver.get("rectangular_finite_ot", {})
if finite_ot.get("passed") is not True or finite_ot.get("shape") != [3, 4]:
    raise ValueError("Chapter 9 rectangular finite OT witness differs")
if finite_ot.get("primal_objective") != 0.575 or finite_ot.get("duality_gap_absolute") != 0.0:
    raise ValueError("Chapter 9 finite OT primal/dual objective differs")
wasserstein = solver.get("wasserstein_two_special_case", {})
if wasserstein.get("passed") is not True or wasserstein.get("W2_squared") != 3.0:
    raise ValueError("Chapter 9 Wasserstein witness differs")
sinkhorn = solver.get("entropic_sinkhorn", {})
if sinkhorn.get("passed") is not True or sinkhorn.get("shape") != [3, 4]:
    raise ValueError("Chapter 9 Sinkhorn witness differs")
if sinkhorn.get("iterations") != 27 or sinkhorn.get("maximum_row_residual", 1.0) > 1e-12:
    raise ValueError("Chapter 9 Sinkhorn convergence witness differs")

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
        raise ValueError(f"Chapter 9 build log contains forbidden diagnostic: {forbidden}")
if "Output written on" not in build_log or "(15 pages" not in build_log:
    raise ValueError("Chapter 9 build log does not prove a fifteen-page output")

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
    raise ValueError("Chapter 9 proposed ledger order differs")
for event_id in EXPECTED_LEDGER_IDS:
    if integrated_by_id.get(event_id) != proposal_by_id[event_id]:
        raise ValueError(f"integrated correction differs from proposal: {event_id}")
if integrated_by_id.get("O015-HAB-ADV-0096") != EXPECTED_BIBLIOGRAPHY_EVENT:
    raise ValueError("integrated wrapper-only bibliography correction 0096 differs")
if len(integrated_events) != 99 or list(integrated_by_id)[-13:] != EXPECTED_ALL_LEDGER_IDS:
    raise ValueError("Chapter 9 integrated correction order/count differs")


# Component-specific source, derivative, inline-figure, and validation rights.
for record_id, component_id, path, status, notes in [
    (
        "rights.o015-habring-ch09-source",
        "o015-habring-ch09-text",
        SOURCE_PATH,
        "admitted",
        "Chapter 9 authority source; all twelve mathematical corrections are explicit records.",
    ),
    (
        "rights.o015-habring-id-ch09",
        "o015-habring-id-unit-09",
        TARGET_PATH,
        "derivative",
        "Independent id-ID translation of Chapter 9 and its standalone wrapper.",
    ),
    (
        "rights.o015-habring-ch09-inline-tikz",
        "o015-habring-ch09-transport-map-tikz",
        TARGET_PATH,
        "derivative",
        "Inline TikZ source retained and localized; target adds centering and proportional page-width scaling.",
    ),
    (
        "rights.o015-habring-ch09-local-bibliography",
        "o015-habring-ch09-local-bibliography",
        LOCAL_BIB_PATH,
        "derivative",
        "Unit-local corrected Villani metadata; frozen authority bibliography remains unchanged and correction event 0096 is explicit.",
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

solver_right = common("rights", "rights.o015-optimal-transport-solver-validation", "admitted")
solver_right.update(
    {
        "component_id": "o015-solver-validation-09",
        "path": SOLVER_SOURCE_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": SOLVER_SOURCE_PATH,
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with results", "use open solver runtime"],
        "notes": "SciPy/HiGHS finite-OT primal/dual witnesses, Wasserstein identity, Sinkhorn checks, and four negative controls.",
    }
)
add(solver_right)


unit = common("unit", "unit.habring.v1.ch09", "built")
unit.update(
    {
        "edition_id": "edition.habring.convex-optimization.id-id.v1",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "parent_id": "unit.habring.v1",
        "unit_kind": "chapter",
        "order": 9,
        "source_local_id": "chapter-9",
        "source_local_label": "9 — Excursion on Optimal Transport",
        "target_local_label": "9 — Selingan tentang Transportasi Optimal",
        "source_locator": f"{SOURCE_PATH}:1-264",
        "target_locator": f"{TARGET_PATH}:1-352",
        "rights_id": "rights.o015-habring-id-ch09",
        "translation_state": "built",
    }
)
add(unit)


concept_specs = [
    ("concept.measurable-probability-space", "measurable spaces and finite probability measures", []),
    ("concept.pushforward-measure", "push-forward of a probability measure", ["concept.measurable-probability-space"]),
    ("concept.monge-optimal-transport", "Monge optimal-transport problem", ["concept.pushforward-measure"]),
    ("concept.transport-coupling", "coupling and transport plan with fixed marginals", ["concept.measurable-probability-space"]),
    ("concept.kantorovich-optimal-transport", "Kantorovich optimal-transport problem", ["concept.transport-coupling"]),
    ("concept.kantorovich-existence", "existence of a Kantorovich minimizer on Polish spaces", ["concept.kantorovich-optimal-transport", "concept.lower-semicontinuity"]),
    ("concept.wasserstein-distance", "Wasserstein-p metric on finite-moment probability measures", ["concept.kantorovich-optimal-transport"]),
    ("concept.kantorovich-duality", "Kantorovich strong duality with bounded continuous potentials", ["concept.kantorovich-optimal-transport", "concept.fenchel-rockafellar-duality"]),
    ("concept.discrete-optimal-transport", "finite-dimensional discrete optimal transport", ["concept.kantorovich-optimal-transport"]),
    ("concept.entropic-optimal-transport", "entropically regularized discrete optimal transport", ["concept.discrete-optimal-transport", "concept.strong-convexity"]),
    ("concept.entropic-plan-factorization", "positive Gibbs-kernel factorization of the entropic plan", ["concept.entropic-optimal-transport"]),
    ("concept.sinkhorn-knopp-algorithm", "Sinkhorn--Knopp alternating scaling algorithm", ["concept.entropic-plan-factorization"]),
]
for concept_id, label, prerequisites in concept_specs:
    concept = common("concept", concept_id, "current")
    concept.update(
        {
            "canonical_label": label,
            "prerequisite_ids": prerequisites,
            "domain": "optimal transport and convex optimization",
        }
    )
    add(concept)

term_specs = [
    ("term.optimal-transport", "concept.kantorovich-optimal-transport", "optimal transport", "transportasi optimal", ["OT"], 1),
    ("term.pushforward-measure", "concept.pushforward-measure", "push-forward measure", "ukuran hasil dorong", ["ukuran push-forward"], 3),
    ("term.monge-optimal-transport", "concept.monge-optimal-transport", "Monge optimal transport", "transportasi optimal Monge", [], 3),
    ("term.kantorovich-optimal-transport", "concept.kantorovich-optimal-transport", "Kantorovich optimal transport", "transportasi optimal Kantorovich", [], 3),
    ("term.transport-plan", "concept.transport-coupling", "transport plan", "rencana transportasi", [], 3),
    ("term.coupling", "concept.transport-coupling", "coupling", "kopling", [], 3),
    ("term.wasserstein-distance", "concept.wasserstein-distance", "Wasserstein distance", "jarak Wasserstein", [], 4),
    ("term.kantorovich-duality", "concept.kantorovich-duality", "Kantorovich duality", "dualitas Kantorovich", [], 5),
    ("term.transport-polytope", "concept.discrete-optimal-transport", "transport polytope", "politop transportasi", [], 8),
    ("term.entropic-regularization", "concept.entropic-optimal-transport", "entropic regularization", "regularisasi entropik", [], 7),
    ("term.gibbs-kernel", "concept.entropic-plan-factorization", "Gibbs kernel", "kernel Gibbs", [], 8),
    ("term.sinkhorn-knopp-algorithm", "concept.sinkhorn-knopp-algorithm", "Sinkhorn--Knopp algorithm", "algoritme Sinkhorn--Knopp", ["Sinkhorn"], 9),
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
            "scope": "optimal transport and convex optimization",
            "register": "formal",
            "evidence_segment_ids": [f"d90.hab.v1.ch09.seg{segment_order:04d}"],
            "examples": [preferred],
            "rights_id": "rights.o015-habring-id-ch09",
        }
    )
    add(term)


for order, s_start, s_end, t_start, t_end, source_label, target_label, concept_ids in segment_specs:
    segment_id = f"d90.hab.v1.ch09.seg{order:04d}"
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, s_start, s_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, t_start, t_end)
    segment = common("segment", segment_id, "current")
    segment.update(
        {
            "unit_id": "unit.habring.v1.ch09",
            "order": order,
            "source_local_id": f"chapter-9-lines-{s_start}-{s_end}",
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
            "rights_id": "rights.o015-habring-id-ch09",
            "evidence_event_ids": [
                "qa.o015.ch09.structure",
                "qa.o015.ch09.formula-delta",
                "qa.o015.ch09.solver",
                "qa.o015.ch09.build",
                "qa.o015.ch09.math-rereview",
                "qa.o015.ch09.visual",
                "qa.o015.ch09.accessibility",
            ],
        }
    )
    add(segment)


# Figure/asset closure and the source's one informal exercise, resolved as an
# integrated proof under correction event 0094.
for surface_id, surface_type, order, s_start, s_end, t_start, t_end, source_label, target_label, segment_ids, concept_id, extra in [
    (
        "surface.habring.v1.ch09.figure01",
        "figure",
        1,
        18,
        75,
        22,
        82,
        "Optimal-transport map illustration",
        "Ilustrasi peta transportasi optimal",
        ["d90.hab.v1.ch09.seg0002"],
        "concept.monge-optimal-transport",
        {"asset_id": "asset.habring.v1.ch09.transport-map-tikz", "accessibility_description": "Dua kurva massa pada satu garis dasar dihubungkan oleh busur-busur monoton yang melukiskan peta hasil dorong dari alfa ke beta."},
    ),
    (
        "surface.habring.v1.ch09.exercise01",
        "exercise_prompt",
        1,
        237,
        237,
        283,
        332,
        "Uniqueness is left as an exercise",
        "Bukti terintegrasi tentang eksistensi, keunikan, positivitas, dan faktorisasi",
        ["d90.hab.v1.ch09.seg0008"],
        "concept.entropic-plan-factorization",
        {"disposition": "source_exercise_resolved_by_determined_integrated_proof", "hint_state": "absent_in_source", "answer_state": "absent_in_source", "solution_state": "present_in_target_as_integrated_proof", "correction_event_id": "O015-HAB-ADV-0094"},
    ),
    (
        "surface.habring.v1.ch09.solution01",
        "integrated_solution",
        1,
        237,
        237,
        283,
        332,
        "No source solution; only an exercise marker",
        "Bukti lengkap yang terintegrasi dalam lema",
        ["d90.hab.v1.ch09.seg0008"],
        "concept.entropic-plan-factorization",
        {"source_presence": "absent", "target_presence": "present", "origin": "determined correction and completion", "correction_event_id": "O015-HAB-ADV-0094"},
    ),
]:
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, s_start, s_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, t_start, t_end)
    surface = common("learning_surface", surface_id, "present")
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch09",
            "surface_type": surface_type,
            "presence": "present",
            "order": order,
            "source_local_id": surface_id.rsplit(".", 1)[1],
            "source_local_label": source_label,
            "target_local_label": target_label,
            "related_segment_ids": segment_ids,
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
            "translation_state": "built",
            "rights_id": "rights.o015-habring-id-ch09",
            **extra,
        }
    )
    add(surface)

for surface_type in ("hint", "answer"):
    surface = common(
        "learning_surface",
        f"surface.habring.v1.ch09.{surface_type}-inventory",
        "source_absent",
    )
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch09",
            "surface_type": surface_type,
            "presence": "absent",
            "count": 0,
            "absence_evidence": "qa/OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json",
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
            "rights_id": "rights.o015-habring-id-ch09",
        }
    )
    add(surface)

asset_inventory = common("learning_surface", "surface.habring.v1.ch09.asset-inventory", "present")
asset_inventory.update(
    {
        "unit_id": "unit.habring.v1.ch09",
        "surface_type": "asset",
        "presence": "present",
        "count": 2,
        "asset_ids": [
            "asset.habring.v1.ch09.transport-map-tikz",
            "asset.habring.v1.ch09.local-bibliography",
        ],
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "rights_id": "rights.o015-habring-ch09-inline-tikz",
    }
)
add(asset_inventory)

inline_asset = common("asset", "asset.habring.v1.ch09.transport-map-tikz", "current")
inline_asset.update(
    {
        "asset_kind": "inline_tikz_figure",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "source_path": SOURCE_PATH,
        "source_locator": f"{SOURCE_PATH}:18-75",
        "source_line_start": 18,
        "source_line_end": 75,
        "source_bytes": 15378,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "target_path": TARGET_PATH,
        "target_locator": f"{TARGET_PATH}:22-82",
        "target_line_start": 22,
        "target_line_end": 82,
        "target_bytes": 21252,
        "target_sha256": EXPECTED_TARGET_SHA256,
        "rights_id": "rights.o015-habring-ch09-inline-tikz",
        "related_segment_ids": ["d90.hab.v1.ch09.seg0002"],
        "adaptation": "Translated comments and visible labels; added centering and proportional text-width scaling.",
        "accessibility_description": "Dua kurva massa alfa dan beta pada satu sumbu, dengan busur-busur monoton yang menandai pemetaan T dan identitas T-sharp alfa sama dengan beta.",
    }
)
add(inline_asset)

local_bibliography_asset = common(
    "asset", "asset.habring.v1.ch09.local-bibliography", "current"
)
local_bibliography_asset.update(
    {
        "asset_kind": "localized_bibliography_metadata",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "source_path": AUTHORITY_BIB_PATH,
        "source_locator": f"{AUTHORITY_BIB_PATH}:20-26",
        "source_line_start": 20,
        "source_line_end": 26,
        "source_bytes": 614,
        "source_sha256": EXPECTED_AUTHORITY_BIB_SHA256,
        "target_path": LOCAL_BIB_PATH,
        "target_locator": f"{LOCAL_BIB_PATH}:1-9",
        "target_line_start": 1,
        "target_line_end": 9,
        "target_bytes": 306,
        "target_sha256": EXPECTED_LOCAL_BIB_SHA256,
        "rights_id": "rights.o015-habring-ch09-local-bibliography",
        "related_segment_ids": [],
        "adaptation": "Removed the erroneous `and others`, retained Cédric Villani as sole author, and added the publisher DOI.",
        "correction_event_id": "O015-HAB-ADV-0096",
        "provenance_caveat": "The frozen authority bibliography is preserved byte-for-byte; this corrected component is used only by the standalone Chapter 9 reader.",
    }
)
add(local_bibliography_asset)


correction_specs = {
    84: (8, 96, [1, 3]),
    85: (8, 14, [1]),
    86: (87, 92, [3]),
    87: (94, 94, [3]),
    88: (112, 118, [4]),
    89: (122, 129, [4]),
    90: (131, 141, [5]),
    91: (142, 190, [6]),
    92: (192, 215, [7]),
    93: (216, 226, [7]),
    94: (229, 256, [8]),
    95: (257, 264, [9]),
    96: (20, 26, []),
}
for number in range(84, 97):
    event_id = f"O015-HAB-ADV-{number:04d}"
    event = integrated_by_id[event_id]
    source_start, source_end, segment_orders = correction_specs[number]
    correction = common("correction", f"correction.o015-hab-adv-{number:04d}", "applied")
    correction.update(
        {
            "source_event_id": event_id,
            "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
            "affected_unit_ids": ["unit.habring.v1.ch09"],
            "affected_segment_ids": [
                f"d90.hab.v1.ch09.seg{order:04d}" for order in segment_orders
            ],
            "source_path": AUTHORITY_BIB_PATH if number == 96 else SOURCE_PATH,
            "source_line_start": source_start,
            "source_line_end": source_end,
            "source_locator": f"{AUTHORITY_BIB_PATH if number == 96 else SOURCE_PATH}:{source_start}-{source_end}",
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
    artifact("artifact.habring.source-ch09", "source_tex", SOURCE_PATH, source_edition_id="edition.habring.convex-optimization.arxiv-2607-11664v1", rights_id="rights.o015-habring-ch09-source"),
    artifact("artifact.habring.target-ch09", "target_tex", TARGET_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch09"),
    artifact("artifact.habring.target-wrapper-ch09", "target_tex", WRAPPER_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch09"),
    artifact("artifact.habring.local-bibliography-ch09", "bibliography_metadata", LOCAL_BIB_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", source_artifact_id="artifact.habring.references-bib", rights_id="rights.o015-habring-ch09-local-bibliography", correction_event_id="O015-HAB-ADV-0096"),
    artifact("artifact.habring.structure-report-ch09", "qa_report", "qa/OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json", toolchain=AUDIT_SOURCE_PATH, formula_delta_manifest_sha256=EXPECTED_FORMULA_MANIFEST_SHA256),
    artifact("artifact.habring.formula-manifest-ch09", "qa_report", "qa/OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json", toolchain=AUDIT_SOURCE_PATH),
    artifact("artifact.habring.structure-audit-ch09", "qa_source", AUDIT_SOURCE_PATH, toolchain="Python 3 standard library"),
    artifact("artifact.habring.solver-results-ch09", "qa_report", "qa/OPTIMAL_TRANSPORT_SOLVER_RESULTS.json", toolchain="Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1 / HiGHS", rights_id="rights.o015-optimal-transport-solver-validation"),
    artifact("artifact.habring.solver-validator-ch09", "qa_source", SOLVER_SOURCE_PATH, toolchain="Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1 / HiGHS", rights_id="rights.o015-optimal-transport-solver-validation"),
    artifact("artifact.habring.proposed-ledger-ch09", "correction_proposal", "qa/CHAPTER09_PROPOSED_LEDGER.jsonl", source_artifact_id="artifact.habring.source-ch09"),
    artifact("artifact.habring.worklog-ch09", "qa_receipt", WORKLOG_PATH, source_artifact_id="artifact.habring.source-ch09"),
    artifact("artifact.habring.build-log-ch09", "build_receipt", BUILD_LOG_PATH, build_event_id="qa.o015.ch09.build", toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber"),
    artifact("artifact.habring.target-pdf-ch09", "reader_pdf", OUTPUT_PDF_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", rights_id="rights.o015-habring-id-ch09", pages=15, build_event_id="qa.o015.ch09.build", toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber", accessibility="searchable id-ID PDF; untagged", input_artifact_ids=["artifact.habring.target-wrapper-ch09", "artifact.habring.target-ch09", "artifact.habring.target-macros", "artifact.habring.target-class", "artifact.habring.local-bibliography-ch09"]),
    artifact("artifact.habring.target-text-ch09", "qa_extract", TEXT_PATH, target_edition_id="edition.habring.convex-optimization.id-id.v1", source_artifact_id="artifact.habring.target-pdf-ch09"),
    artifact("artifact.o015.backend-generator-ch09", "qa_source", "qa/extend_backend_ch09.py", toolchain="Python 3 standard library"),
]:
    add(record)


qa_specs = [
    {"id": "qa.o015.ch09.source-freeze", "status": "pass", "event_type": "source", "result": "pass", "witness_artifact_ids": ["artifact.habring.source-ch09"], "authority_id": "o015-habring-arxiv-2607.11664v1", "source_sha256": EXPECTED_SOURCE_SHA256},
    {"id": "qa.o015.ch09.bibliography", "status": "pass", "event_type": "bibliography", "result": "pass", "witness_artifact_ids": ["artifact.habring.local-bibliography-ch09", "artifact.habring.structure-report-ch09"], "authority_bibliography_sha256": EXPECTED_AUTHORITY_BIB_SHA256, "local_bibliography_sha256": EXPECTED_LOCAL_BIB_SHA256, "correction_event_id": "O015-HAB-ADV-0096", "checks": ["frozen authority bibliography unchanged", "single local Villani entry", "sole author corrected", "publisher DOI present", "source and-others marker absent", "wrapper bound to local bibliography"]},
    {"id": "qa.o015.ch09.structure", "status": "pass", "event_type": "topology", "result": "pass", "witness_artifact_ids": ["artifact.habring.structure-report-ch09"], "environment_topology_equal": True, "environment_count": 47, "environment_counts": expected_environment_counts, "failures": [], "segment_count": 9, "label_occurrences_preserved": 5, "source_eqref_occurrences": 8, "target_eqref_occurrences": 9, "cref_occurrences_preserved": 1, "source_citations": 1, "target_citations": 2, "figures": 1, "inline_tikz_assets": 1, "footnotes": 3, "source_exercises": 1, "target_integrated_solutions": 1, "hints": 0, "answers": 0},
    {"id": "qa.o015.ch09.formula-delta", "status": "pass", "event_type": "mathematics", "result": "pass", "witness_artifact_ids": ["artifact.habring.structure-report-ch09", "artifact.habring.formula-manifest-ch09", "artifact.habring.proposed-ledger-ch09"], "formula_delta_manifest_sha256": EXPECTED_FORMULA_MANIFEST_SHA256, "source_formula_surfaces": formula["source_formula_count"], "target_formula_surfaces": formula["target_formula_count"], "formula_delta_blocks": formula["delta_block_count"], "substantive_formula_delta_blocks": formula["substantive_delta_block_count"], "mathematical_correction_events": 12, "total_chapter_correction_events": 13, "disposition": "Every substantive mathematical delta is correction-ledger bound; wrapper-only bibliography event 0096 is separately bound."},
    {"id": "qa.o015.ch09.solver", "status": "pass", "event_type": "computation", "result": "pass", "witness_artifact_ids": ["artifact.habring.solver-results-ch09", "artifact.habring.solver-validator-ch09"], "checks": ["rectangular 3x4 finite-OT primal/dual feasibility and zero duality gap", "Wasserstein-2 identity, symmetry, and known-value witness", "positive entropic Sinkhorn plan, marginals, factorization, KKT stationarity, scaling ambiguity, and strict convexity", "four malformed-source negative controls", "41 live gates"], "python": "3.13.9", "numpy": "2.4.4", "scipy": "1.17.1", "solver": "scipy.optimize.linprog(method='highs')"},
    {"id": "qa.o015.ch09.build", "status": "pass", "event_type": "build", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-pdf-ch09", "artifact.habring.build-log-ch09"], "toolchain": "pdfTeX 1.40.29 / MiKTeX 26.5 / latexmk 4.88 / Biber", "pages": 15, "page_size": "A4", "deterministic_rebuild": "byte-identical", "errors": [], "undefined_references": 0, "multiply_defined_labels": 0, "replacement_glyphs": 0, "overfull_boxes": 0, "underfull_boxes": 0},
    {"id": "qa.o015.ch09.visual", "status": "pass", "event_type": "visual", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-pdf-ch09"], "pages_inspected": 15, "method": "All pages rendered and inspected against the frozen PDF bytes; mathematical and Sinkhorn surfaces inspected at full size.", "findings": []},
    {"id": "qa.o015.ch09.accessibility", "status": "pass_with_limitation", "event_type": "accessibility", "result": "pass_with_limitation", "witness_artifact_ids": ["artifact.habring.target-pdf-ch09", "artifact.habring.target-text-ch09"], "checks": ["PDF language metadata is id-ID.", "PDF is unencrypted and searchable.", "Text extraction is retained as an exact artifact.", "The inline TikZ figure has an Indonesian accessibility description in the backend."], "limitations": ["PDF is untagged."]},
    {"id": "qa.o015.ch09.math-rereview", "status": "pass", "event_type": "mathematics", "result": "pass", "witness_artifact_ids": ["artifact.habring.target-ch09", "artifact.habring.structure-report-ch09", "artifact.habring.solver-results-ch09"], "verified_at": RECORDED_AT, "target_sha256": EXPECTED_TARGET_SHA256, "review_outcome": {"p1": 0, "p2": 0, "p3": 0}, "scope": "Independent source/target/wrapper/ledger rereview of the complete optimal-transport chapter."},
    {"id": "qa.o015.ch09.language", "status": "not_recorded", "event_type": "language", "result": "not_recorded", "witness_artifact_ids": [], "gap": "No independent Indonesian language review is recorded."},
]
for spec in qa_specs:
    qa = common("qa_event", spec["id"], spec["status"])
    qa.update(
        {
            "unit_id": "unit.habring.v1.ch09",
            **{key: value for key, value in spec.items() if key not in {"id", "status"}},
        }
    )
    add(qa)


relation_specs: list[tuple[str, str, str, str, str]] = [
    ("relation.unit.root-contains-ch09", "contains", "unit.habring.v1", "unit.habring.v1.ch09", "Source Chapter 9."),
    ("relation.unit.ch08-precedes-ch09", "precedes", "unit.habring.v1.ch08", "unit.habring.v1.ch09", "Contiguous admitted source order."),
    ("relation.unit.ch09-depends-on-ch07", "depends-on", "unit.habring.v1.ch09", "unit.habring.v1.ch07", "Kantorovich duality reuses the preceding duality chapter."),
    ("relation.unit.ch09-prerequisite-lower-semicontinuity", "prerequisite", "unit.habring.v1.ch09", "concept.lower-semicontinuity", "Existence and duality use lower-semicontinuity."),
    ("relation.unit.ch09-prerequisite-strong-convexity", "prerequisite", "unit.habring.v1.ch09", "concept.strong-convexity", "Strict convexity yields uniqueness of the entropic plan."),
]
for order in range(1, 10):
    relation_specs.append((f"relation.unit.ch09-contains-seg{order:04d}", "contains", "unit.habring.v1.ch09", f"d90.hab.v1.ch09.seg{order:04d}", "Ordered reader-facing translation segment."))
relation_specs.extend(
    [
        ("relation.segment.ch09-seg0001-defines-measures", "defines", "d90.hab.v1.ch09.seg0001", "concept.measurable-probability-space", "Measurable-space and finite-measure notation."),
        ("relation.segment.ch09-seg0003-defines-pushforward", "defines", "d90.hab.v1.ch09.seg0003", "concept.pushforward-measure", "Measurable push-forward definition."),
        ("relation.segment.ch09-seg0003-defines-monge", "defines", "d90.hab.v1.ch09.seg0003", "concept.monge-optimal-transport", "Monge infimum over measurable feasible maps."),
        ("relation.segment.ch09-seg0003-defines-coupling", "defines", "d90.hab.v1.ch09.seg0003", "concept.transport-coupling", "Transport plans with fixed marginals."),
        ("relation.segment.ch09-seg0003-defines-kantorovich", "defines", "d90.hab.v1.ch09.seg0003", "concept.kantorovich-optimal-transport", "Linear Kantorovich relaxation."),
        ("relation.segment.ch09-seg0004-proves-existence", "proves", "d90.hab.v1.ch09.seg0004", "concept.kantorovich-existence", "Tightness, Prokhorov compactness, and lower-semicontinuity."),
        ("relation.segment.ch09-seg0004-defines-wasserstein", "defines", "d90.hab.v1.ch09.seg0004", "concept.wasserstein-distance", "Wasserstein-p metric on P_p."),
        ("relation.segment.ch09-seg0005-defines-duality", "defines", "d90.hab.v1.ch09.seg0005", "concept.kantorovich-duality", "Strong-duality theorem and potential class."),
        ("relation.segment.ch09-seg0006-proves-duality", "proves", "d90.hab.v1.ch09.seg0006", "concept.kantorovich-duality", "Weak inequality, marginal indicator, and cited strong-duality exchange."),
        ("relation.segment.ch09-seg0007-defines-discrete-ot", "defines", "d90.hab.v1.ch09.seg0007", "concept.discrete-optimal-transport", "Rectangular transport matrix and typed marginal constraints."),
        ("relation.segment.ch09-seg0007-defines-entropic-ot", "defines", "d90.hab.v1.ch09.seg0007", "concept.entropic-optimal-transport", "Extended-valued entropy and positive regularization parameter."),
        ("relation.segment.ch09-seg0008-proves-factorization", "proves", "d90.hab.v1.ch09.seg0008", "concept.entropic-plan-factorization", "Existence, uniqueness, interiority, KKT, and scaling gauge."),
        ("relation.segment.ch09-seg0009-defines-sinkhorn", "defines", "d90.hab.v1.ch09.seg0009", "concept.sinkhorn-knopp-algorithm", "Positive initialized alternating scaling and plan convergence."),
        ("relation.surface.ch09-figure-illustrates-monge", "illustrates", "surface.habring.v1.ch09.figure01", "concept.monge-optimal-transport", "Inline TikZ transport-map illustration."),
        ("relation.surface.ch09-exercise-exercises-factorization", "exercises", "surface.habring.v1.ch09.exercise01", "concept.entropic-plan-factorization", "Source leaves uniqueness as an exercise."),
        ("relation.surface.ch09-solution-proves-factorization", "proves", "surface.habring.v1.ch09.solution01", "concept.entropic-plan-factorization", "Target supplies the correction-bound integrated proof."),
        ("relation.artifact.ch09-target-translates-source", "translates", "artifact.habring.target-ch09", "artifact.habring.source-ch09", "Complete contiguous id-ID translation."),
        ("relation.artifact.ch09-wrapper-contains-target", "contains", "artifact.habring.target-wrapper-ch09", "artifact.habring.target-ch09", "Standalone licensed reader wrapper."),
        ("relation.artifact.ch09-local-bibliography-adapts-authority", "adapts", "artifact.habring.local-bibliography-ch09", "artifact.habring.references-bib", "Unit-local correction of the sole Villani entry; authority bytes remain frozen."),
        ("relation.artifact.ch09-wrapper-depends-on-local-bibliography", "depends-on", "artifact.habring.target-wrapper-ch09", "artifact.habring.local-bibliography-ch09", "Standalone wrapper uses corrected local bibliography metadata."),
        ("relation.artifact.ch09-structure-depends-on-audit", "depends-on", "artifact.habring.structure-report-ch09", "artifact.habring.structure-audit-ch09", "Deterministic structural/formula audit output."),
        ("relation.artifact.ch09-solver-depends-on-validator", "depends-on", "artifact.habring.solver-results-ch09", "artifact.habring.solver-validator-ch09", "Deterministic open-solver validation output."),
        ("relation.artifact.ch09-pdf-depends-on-wrapper", "depends-on", "artifact.habring.target-pdf-ch09", "artifact.habring.target-wrapper-ch09", "Reproducible reader build input."),
        ("relation.artifact.ch09-text-adapts-pdf", "adapts", "artifact.habring.target-text-ch09", "artifact.habring.target-pdf-ch09", "Searchability/accessibility extraction witness."),
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
# IDs may differ; every non-artifact and every other pre-Chapter 9 record must
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
        "Chapter 9 extension changed the pre-Chapter 9 baseline: "
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
