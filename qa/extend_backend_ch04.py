#!/usr/bin/env python3
"""Idempotently extend the O015 backend through Habring Chapter 4."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "backend" / "backend_schema.json"
JSONL_PATH = ROOT / "backend" / "records.jsonl"
CSV_PATH = ROOT / "backend" / "records.csv"
LEDGER_PATH = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
RECORDED_AT = "2026-08-21T17:04:02Z"
WORKFLOW = "o015-first-unit-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def normalized_slice(relative: str, start: int, end: int) -> tuple[int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid slice {relative}:{start}-{end}")
    data = (("\n".join(lines[start - 1 : end])) + "\n").encode("utf-8")
    return len(data), sha256(data)


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), sha256(data)


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


schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
records = [
    json.loads(line)
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()
    if line
]


# Remove a prior Chapter 4 extension so rerunning this script is byte-stable.
generated_exact_ids = {
    "unit.habring.v1.ch04",
    "relation.unit.root-contains-ch04",
    "relation.unit.ch03-precedes-ch04",
    "relation.unit.ch04-depends-on-ch03",
    "rights.o015-habring-ch04-source",
    "rights.o015-habring-id-ch04",
    "rights.o015-projected-subgradient-solver-validation",
    "artifact.habring.references-bib",
}
generated_concepts = {
    "concept.metric-projection",
    "concept.nonexpansive-mapping",
    "concept.projected-subgradient-method",
    "concept.fundamental-projected-subgradient-inequality",
    "concept.subgradient-norm-bound",
    "concept.polyak-step-size",
    "concept.best-iterate-rate",
    "concept.diminishing-step-size",
    "concept.strong-convexity",
}
generated_terms = {
    "term.metric-projection",
    "term.nonexpansive",
    "term.projected-subgradient-method",
    "term.polyak-step-size",
    "term.best-iterate",
    "term.diminishing-step-size",
    "term.strongly-convex",
}


def is_generated(record: dict[str, Any]) -> bool:
    record_id = record["id"]
    return (
        record_id in generated_exact_ids
        or record_id in generated_concepts
        or record_id in generated_terms
        or record_id.startswith("d90.hab.v1.ch04.")
        or record_id.startswith("surface.habring.v1.ch04.")
        or record_id.startswith("correction.o015-hab-adv-00")
        and 19 <= int(record_id.rsplit("-", 1)[1]) <= 27
        or record_id.startswith("relation.unit.ch04-")
        or record_id.startswith("relation.segment.ch04-")
        or record_id.startswith("relation.surface.ch04-")
        or record_id.startswith("qa.o015.ch04.")
        or record_id.startswith("artifact.habring.")
        and record_id.endswith("-ch04")
    )


records = [record for record in records if not is_generated(record)]
by_id = {record["id"]: record for record in records}


# Refresh Chapter 3 statuses now supported by the admitted QA evidence.
for record in records:
    if (
        record["entity_type"] == "segment"
        and record.get("unit_id") == "unit.habring.v1.ch03"
    ):
        record["mathematical_review_state"] = (
            "correction_audited_solver_checked_independent_rereview_passed"
        )
        evidence = list(record.get("evidence_event_ids", []))
        for event_id in (
            "qa.o015.ch03.math-rereview",
            "qa.o015.ch03.visual",
        ):
            if event_id not in evidence:
                evidence.append(event_id)
        record["evidence_event_ids"] = evidence

ch03_math = by_id["qa.o015.ch03.math-rereview"]
ch03_math["status"] = "pass"
ch03_math["result"] = "pass"
ch03_math.pop("gap", None)
ch03_math["verified_at"] = RECORDED_AT
ch03_math["review_outcome"] = {"p1": 0, "p2": 0, "p3": 0}
ch03_math["scope"] = (
    "Independent final mathematical rereview of the complete translated unit."
)

ch03_visual = by_id["qa.o015.ch03.visual"]
ch03_visual["status"] = "pass"
ch03_visual["result"] = "pass"
ch03_visual["witness_artifact_ids"] = ["artifact.habring.target-pdf"]
ch03_visual.pop("gap", None)
ch03_visual["verified_at"] = RECORDED_AT
ch03_visual["pages_inspected"] = 15
ch03_visual["method"] = "Page-by-page rendered visual review."
ch03_visual["findings"] = []

by_id["qa.o015.ch03.build"]["pages"] = 15
by_id["artifact.habring.target-pdf"]["pages"] = 15


# Rights records for the additional source, derivative, and solver code.
right_source = common(
    "rights", "rights.o015-habring-ch04-source", "admitted"
)
right_source.update(
    {
        "component_id": "o015-habring-ch04-source",
        "path": "authority/habring/source-v1/projected_subgradient_method.tex",
        "source_authority_id": "o015-habring-arxiv-2607.11664v1",
        "rights_expression": "CC BY 4.0",
        "authority_url": "https://arxiv.org/abs/2607.11664v1",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "translation_permitted": True,
        "required_handling": [
            "attribution",
            "license link",
            "change notice",
            "no implied endorsement",
        ],
        "notes": "Chapter 4 source; corrections are explicit records.",
    }
)
records.append(right_source)

right_target = common("rights", "rights.o015-habring-id-ch04", "derivative")
right_target.update(
    {
        "component_id": "o015-habring-id-ch04",
        "path": "source/id-ID/habring-04-metode-subgradien-terproyeksi-id.tex",
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
        "notes": "Independent id-ID translation of Chapter 4.",
    }
)
records.append(right_target)

right_solver = common(
    "rights",
    "rights.o015-projected-subgradient-solver-validation",
    "admitted",
)
right_solver.update(
    {
        "component_id": "o015-projected-subgradient-solver-validation",
        "path": "qa/validate_projected_subgradient_unit.py",
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": "qa/validate_projected_subgradient_unit.py",
        "license_url": None,
        "translation_permitted": False,
        "required_handling": [
            "ship source with results",
            "no proprietary runtime",
        ],
        "notes": "Uses NumPy/SciPy and the open SLSQP implementation.",
    }
)
records.append(right_solver)


# Chapter 4 unit.
unit = common("unit", "unit.habring.v1.ch04", "built")
unit.update(
    {
        "edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "parent_id": "unit.habring.v1",
        "unit_kind": "chapter",
        "order": 4,
        "source_local_id": "chapter-4",
        "source_local_label": "4 — Projected subgradient descent",
        "target_local_label": "4 — Penurunan subgradien terproyeksi",
        "source_locator": (
            "authority/habring/source-v1/"
            "projected_subgradient_method.tex:1-291"
        ),
        "target_locator": (
            "source/id-ID/"
            "habring-04-metode-subgradien-terproyeksi-id.tex:1-355"
        ),
        "rights_id": "rights.o015-habring-id-ch04",
        "translation_state": "built",
        "next_source_order_unit": "Chapter 5 — Proximal gradient method",
    }
)
records.append(unit)


# Concepts and their accepted Indonesian terminology.
concept_specs = [
    (
        "concept.metric-projection",
        "metric projection onto a closed convex set",
        ["concept.hilbert-space"],
    ),
    (
        "concept.nonexpansive-mapping",
        "nonexpansive mapping",
        ["concept.metric-projection"],
    ),
    (
        "concept.projected-subgradient-method",
        "projected subgradient method",
        ["concept.convex-subdifferential", "concept.metric-projection"],
    ),
    (
        "concept.fundamental-projected-subgradient-inequality",
        "fundamental projected-subgradient inequality",
        ["concept.projected-subgradient-method", "concept.subgradient"],
    ),
    (
        "concept.subgradient-norm-bound",
        "bound on selected subgradient norms",
        ["concept.convex-subdifferential"],
    ),
    (
        "concept.polyak-step-size",
        "Polyak step-size rule",
        [
            "concept.fundamental-projected-subgradient-inequality",
            "concept.subgradient-norm-bound",
        ],
    ),
    (
        "concept.best-iterate-rate",
        "best-iterate convergence rate",
        [
            "concept.fundamental-projected-subgradient-inequality",
            "concept.subgradient-norm-bound",
        ],
    ),
    (
        "concept.diminishing-step-size",
        "diminishing step-size convergence",
        [
            "concept.fundamental-projected-subgradient-inequality",
            "concept.subgradient-norm-bound",
        ],
    ),
    (
        "concept.strong-convexity",
        "strong convexity",
        ["concept.convex-function"],
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
    (
        "term.metric-projection",
        "concept.metric-projection",
        "metric projection",
        "proyeksi metrik",
        ["proyeksi pada himpunan konveks"],
        "d90.hab.v1.ch04.seg0002",
    ),
    (
        "term.nonexpansive",
        "concept.nonexpansive-mapping",
        "nonexpansive",
        "tak ekspansif",
        ["non-ekspansif"],
        "d90.hab.v1.ch04.seg0004",
    ),
    (
        "term.projected-subgradient-method",
        "concept.projected-subgradient-method",
        "projected subgradient method",
        "metode subgradien terproyeksi",
        [],
        "d90.hab.v1.ch04.seg0003",
    ),
    (
        "term.polyak-step-size",
        "concept.polyak-step-size",
        "Polyak step-size rule",
        "aturan ukuran langkah Polyak",
        ["aturan langkah Polyak"],
        "d90.hab.v1.ch04.seg0006",
    ),
    (
        "term.best-iterate",
        "concept.best-iterate-rate",
        "best iterate",
        "iterasi terbaik",
        [],
        "d90.hab.v1.ch04.seg0006",
    ),
    (
        "term.diminishing-step-size",
        "concept.diminishing-step-size",
        "diminishing step size",
        "ukuran langkah menurun",
        ["ukuran langkah yang mengecil"],
        "d90.hab.v1.ch04.seg0007",
    ),
    (
        "term.strongly-convex",
        "concept.strong-convexity",
        "strongly convex",
        "konveks kuat",
        [],
        "d90.hab.v1.ch04.seg0008",
    ),
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
            "rights_id": "rights.o015-habring-id-ch04",
        }
    )
    records.append(term)


# Eight contiguous reader-facing segments.
source_path = (
    "authority/habring/source-v1/projected_subgradient_method.tex"
)
target_path = (
    "source/id-ID/habring-04-metode-subgradien-terproyeksi-id.tex"
)
segment_specs = [
    (
        1,
        2,
        22,
        4,
        26,
        "Constrained setup and motivation",
        [
            "concept.constrained-convex-optimality",
            "concept.indicator-function",
            "concept.projected-subgradient-method",
        ],
    ),
    (
        2,
        24,
        59,
        29,
        67,
        "Projection theorem in a Hilbert space",
        ["concept.hilbert-space", "concept.metric-projection"],
    ),
    (
        3,
        60,
        107,
        70,
        124,
        "Projected iteration and projection characterization",
        [
            "concept.metric-projection",
            "concept.projected-subgradient-method",
        ],
    ),
    (
        4,
        110,
        133,
        127,
        151,
        "Nonexpansiveness of metric projection",
        ["concept.metric-projection", "concept.nonexpansive-mapping"],
    ),
    (
        5,
        136,
        154,
        154,
        173,
        "Fundamental projected-subgradient inequality",
        [
            "concept.fundamental-projected-subgradient-inequality",
            "concept.projected-subgradient-method",
        ],
    ),
    (
        6,
        155,
        200,
        176,
        230,
        "Polyak step size and best-iterate rate",
        [
            "concept.polyak-step-size",
            "concept.subgradient-norm-bound",
            "concept.best-iterate-rate",
        ],
    ),
    (
        7,
        202,
        237,
        233,
        280,
        "Complexity and general step-size convergence",
        [
            "concept.diminishing-step-size",
            "concept.best-iterate-rate",
        ],
    ),
    (
        8,
        239,
        291,
        283,
        355,
        "Strongly convex convergence rates",
        [
            "concept.strong-convexity",
            "concept.subgradient-norm-bound",
            "concept.best-iterate-rate",
        ],
    ),
]
for order, s_start, s_end, t_start, t_end, label, concept_ids in segment_specs:
    segment_id = f"d90.hab.v1.ch04.seg{order:04d}"
    source_bytes, source_digest = normalized_slice(source_path, s_start, s_end)
    target_bytes, target_digest = normalized_slice(target_path, t_start, t_end)
    segment = common("segment", segment_id, "current")
    segment.update(
        {
            "unit_id": "unit.habring.v1.ch04",
            "order": order,
            "source_local_id": f"chapter-4-lines-{s_start}-{s_end}",
            "source_local_label": label,
            "source_edition_id": (
                "edition.habring.convex-optimization.arxiv-2607-11664v1"
            ),
            "source_language": "en",
            "source_path": source_path,
            "source_locator": f"{source_path}:{s_start}-{s_end}",
            "source_line_start": s_start,
            "source_line_end": s_end,
            "source_bytes": source_bytes,
            "source_content_sha256": source_digest,
            "target_edition_id": (
                "edition.habring.convex-optimization.id-id.v1"
            ),
            "target_language": "id",
            "target_locale": "id-ID",
            "target_path": target_path,
            "target_locator": f"{target_path}:{t_start}-{t_end}",
            "target_line_start": t_start,
            "target_line_end": t_end,
            "target_bytes": target_bytes,
            "target_content_sha256": target_digest,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "built",
            "structural_review_state": "passed",
            "mathematical_review_state": (
                "correction_audited_solver_checked_"
                "independent_rereview_passed"
            ),
            "language_review_state": "not_recorded",
            "concept_ids": concept_ids,
            "rights_id": "rights.o015-habring-id-ch04",
            "evidence_event_ids": [
                "qa.o015.ch04.structure",
                "qa.o015.ch04.build",
                "qa.o015.ch04.math-rereview",
                "qa.o015.ch04.visual",
            ],
        }
    )
    records.append(segment)


# Exercise, hint, answer, and solution surfaces.
exercise_specs = [
    (
        1,
        106,
        106,
        123,
        123,
        "Projection onto a subspace",
        ["d90.hab.v1.ch04.seg0003"],
        "concept.metric-projection",
    ),
    (
        2,
        188,
        188,
        182,
        182,
        "Global Lipschitz continuity bounds subgradient norms",
        ["d90.hab.v1.ch04.seg0006"],
        "concept.subgradient-norm-bound",
    ),
]
for order, s_start, s_end, t_start, t_end, label, segment_ids, concept_id in exercise_specs:
    source_bytes, source_digest = normalized_slice(source_path, s_start, s_end)
    target_bytes, target_digest = normalized_slice(target_path, t_start, t_end)
    surface_id = f"surface.habring.v1.ch04.exercise{order:02d}"
    surface = common("learning_surface", surface_id, "present")
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch04",
            "surface_type": "exercise",
            "presence": "present",
            "order": order,
            "source_local_id": f"chapter-4-informal-exercise-{order}",
            "source_local_label": label,
            "target_local_label": label,
            "related_segment_ids": segment_ids,
            "concept_id": concept_id,
            "source_path": source_path,
            "source_line_start": s_start,
            "source_line_end": s_end,
            "source_locator": f"{source_path}:{s_start}-{s_end}",
            "source_bytes": source_bytes,
            "source_content_sha256": source_digest,
            "target_path": target_path,
            "target_line_start": t_start,
            "target_line_end": t_end,
            "target_locator": f"{target_path}:{t_start}-{t_end}",
            "target_bytes": target_bytes,
            "target_content_sha256": target_digest,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "hint_state": "absent_in_source",
            "answer_state": "absent_in_source",
            "solution_state": "absent_in_source",
            "translation_state": "built",
            "rights_id": "rights.o015-habring-id-ch04",
        }
    )
    records.append(surface)

for surface_type in ("hint", "answer", "solution"):
    surface = common(
        "learning_surface",
        f"surface.habring.v1.ch04.{surface_type}-inventory",
        "source_absent",
    )
    surface.update(
        {
            "unit_id": "unit.habring.v1.ch04",
            "surface_type": surface_type,
            "presence": "absent",
            "count": 0,
            "absence_evidence": (
                "00_control/SOURCE_AUTHORITY.json learning_surfaces "
                "for o015-habring-arxiv-2607.11664v1"
            ),
            "source_edition_id": (
                "edition.habring.convex-optimization.arxiv-2607-11664v1"
            ),
            "target_edition_id": (
                "edition.habring.convex-optimization.id-id.v1"
            ),
            "rights_id": "rights.o015-habring-id-ch04",
        }
    )
    records.append(surface)


# Convert Chapter 4 adverse-ledger entries into explicit correction records.
ledger = [
    json.loads(line)
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
events = {
    entry["event_id"]: entry
    for entry in ledger
    if entry.get("event_id", "").startswith("O015-HAB-ADV-")
}
affected_segments = {
    19: ["d90.hab.v1.ch04.seg0001"],
    20: ["d90.hab.v1.ch04.seg0002", "d90.hab.v1.ch04.seg0003"],
    21: ["d90.hab.v1.ch04.seg0003", "d90.hab.v1.ch04.seg0004"],
    22: ["d90.hab.v1.ch04.seg0005"],
    23: [
        "d90.hab.v1.ch04.seg0006",
        "d90.hab.v1.ch04.seg0007",
        "d90.hab.v1.ch04.seg0008",
    ],
    24: ["d90.hab.v1.ch04.seg0006"],
    25: ["d90.hab.v1.ch04.seg0007"],
    26: ["d90.hab.v1.ch04.seg0008"],
    27: ["d90.hab.v1.ch04.seg0003", "d90.hab.v1.ch04.seg0008"],
}
for number in range(19, 28):
    event_id = f"O015-HAB-ADV-{number:04d}"
    if event_id not in events:
        raise ValueError(f"missing ledger event {event_id}")
    event = events[event_id]
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
            "source_edition_id": (
                "edition.habring.convex-optimization.arxiv-2607-11664v1"
            ),
            "affected_unit_ids": ["unit.habring.v1.ch04"],
            "affected_segment_ids": affected_segments[number],
            "source_path": (
                "authority/habring/source-v1/" + source_relative
            ),
            "source_line_start": min(numbers),
            "source_line_end": max(numbers),
            "source_locator": (
                "authority/habring/source-v1/" + locator
            ),
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


# Durable artifacts for the Chapter 4 reader and its reproducibility evidence.
records.extend(
    [
        artifact(
            "artifact.habring.source-ch04",
            "source_tex",
            source_path,
            source_edition_id=(
                "edition.habring.convex-optimization.arxiv-2607-11664v1"
            ),
            rights_id="rights.o015-habring-ch04-source",
        ),
        artifact(
            "artifact.habring.target-ch04",
            "target_tex",
            target_path,
            target_edition_id=(
                "edition.habring.convex-optimization.id-id.v1"
            ),
            rights_id="rights.o015-habring-id-ch04",
        ),
        artifact(
            "artifact.habring.target-wrapper-ch04",
            "target_tex",
            "source/id-ID/"
            "D90-HAB-04-metode-subgradien-terproyeksi-id.tex",
            target_edition_id=(
                "edition.habring.convex-optimization.id-id.v1"
            ),
            rights_id="rights.o015-habring-id-ch04",
        ),
        artifact(
            "artifact.habring.references-bib",
            "build_dependency",
            "authority/habring/source-v1/references.bib",
            source_edition_id=(
                "edition.habring.convex-optimization.arxiv-2607-11664v1"
            ),
            rights_id="rights.o015-habring-ch04-source",
        ),
        artifact(
            "artifact.habring.structure-report-ch04",
            "qa_report",
            "qa/PROJECTED_SUBGRADIENT_STRUCTURE_REPORT.json",
            toolchain="qa/audit_projected_subgradient_unit.py",
            formula_delta_manifest_sha256=(
                "d0453330d42781afffe1e1b7ad3d5a663533509f43a754f9958785b9646171b4"
            ),
        ),
        artifact(
            "artifact.habring.structure-audit-ch04",
            "qa_source",
            "qa/audit_projected_subgradient_unit.py",
            toolchain="Python 3 standard library",
        ),
        artifact(
            "artifact.habring.solver-results-ch04",
            "qa_report",
            "qa/PROJECTED_SUBGRADIENT_SOLVER_RESULTS.json",
            toolchain=(
                "Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1"
            ),
            rights_id=(
                "rights.o015-projected-subgradient-solver-validation"
            ),
        ),
        artifact(
            "artifact.habring.solver-validator-ch04",
            "qa_source",
            "qa/validate_projected_subgradient_unit.py",
            toolchain=(
                "Python 3.13.9 / NumPy 2.4.4 / SciPy 1.17.1"
            ),
            rights_id=(
                "rights.o015-projected-subgradient-solver-validation"
            ),
        ),
        artifact(
            "artifact.habring.build-log-ch04",
            "build_receipt",
            "build/habring-unit-04-id/"
            "D90-HAB-04-metode-subgradien-terproyeksi-id.log",
            build_event_id="qa.o015.ch04.build",
            toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / Biber",
        ),
        artifact(
            "artifact.habring.target-pdf-ch04",
            "reader_pdf",
            "build/habring-unit-04-id/"
            "D90-HAB-04-metode-subgradien-terproyeksi-id.pdf",
            target_edition_id=(
                "edition.habring.convex-optimization.id-id.v1"
            ),
            rights_id="rights.o015-habring-id-ch04",
            pages=13,
            build_event_id="qa.o015.ch04.build",
            toolchain="pdfTeX 1.40.29 / MiKTeX 26.5 / Biber",
            input_artifact_ids=[
                "artifact.habring.target-wrapper-ch04",
                "artifact.habring.target-ch04",
                "artifact.habring.target-macros",
                "artifact.habring.target-class",
                "artifact.habring.references-bib",
            ],
        ),
        artifact(
            "artifact.habring.target-text-ch04",
            "qa_extract",
            "qa/D90-HAB-04-metode-subgradien-terproyeksi-id.txt",
            target_edition_id=(
                "edition.habring.convex-optimization.id-id.v1"
            ),
            source_artifact_id="artifact.habring.target-pdf-ch04",
        ),
    ]
)


# Chapter 4 QA events. The independent mathematical rereview passes; the
# independent language review remains an explicit gap.
qa_specs = [
    {
        "id": "qa.o015.ch04.source-freeze",
        "status": "pass",
        "event_type": "source",
        "result": "pass",
        "witness_artifact_ids": ["artifact.habring.source-ch04"],
        "authority_id": "o015-habring-arxiv-2607.11664v1",
        "source_sha256": (
            "44ac28a0f0b67fed4855f7ed91089fab52f77804115f2a06201bff98437bd8da"
        ),
    },
    {
        "id": "qa.o015.ch04.structure",
        "status": "pass",
        "event_type": "topology",
        "result": "pass",
        "witness_artifact_ids": [
            "artifact.habring.structure-report-ch04"
        ],
        "environment_topology_equal": True,
        "environment_count": 67,
        "failures": [],
        "segment_count": 8,
        "labels_preserved": 4,
        "footnotes_preserved": 3,
        "citations_preserved": 1,
    },
    {
        "id": "qa.o015.ch04.formula-delta",
        "status": "pass",
        "event_type": "mathematics",
        "result": "pass",
        "witness_artifact_ids": [
            "artifact.habring.structure-report-ch04"
        ],
        "formula_delta_manifest_sha256": (
            "d0453330d42781afffe1e1b7ad3d5a663533509f43a754f9958785b9646171b4"
        ),
        "source_formula_surfaces": 140,
        "target_formula_surfaces": 169,
        "formula_delta_blocks": 40,
        "disposition": (
            "All substantive mathematical deltas are correction-ledger bound."
        ),
    },
    {
        "id": "qa.o015.ch04.solver",
        "status": "pass",
        "event_type": "computation",
        "result": "pass",
        "witness_artifact_ids": [
            "artifact.habring.solver-results-ch04",
            "artifact.habring.solver-validator-ch04",
        ],
        "checks": [
            "512 projection variational-inequality and nonexpansiveness tests",
            "Polyak and general step schedules on a constrained nonsmooth objective",
            "strongly convex epigraph problem solved with scipy.optimize.minimize(method='SLSQP')",
        ],
        "python": "3.13.9",
        "numpy": "2.4.4",
        "scipy": "1.17.1",
    },
    {
        "id": "qa.o015.ch04.build",
        "status": "pass",
        "event_type": "build",
        "result": "pass",
        "witness_artifact_ids": [
            "artifact.habring.target-pdf-ch04",
            "artifact.habring.build-log-ch04",
        ],
        "toolchain": "pdfTeX 1.40.29 / MiKTeX 26.5 / Biber",
        "pages": 13,
        "warnings": [
            "biblatex Indonesian language module unavailable",
            "glossaries/tracklang Indonesian module unavailable",
        ],
        "errors": [],
    },
    {
        "id": "qa.o015.ch04.visual",
        "status": "pass",
        "event_type": "visual",
        "result": "pass",
        "witness_artifact_ids": ["artifact.habring.target-pdf-ch04"],
        "pages_inspected": 13,
        "method": (
            "All pages rendered at 120 dpi and inspected; pages 4, 8, and 11 "
            "also inspected at full size."
        ),
        "findings": [],
    },
    {
        "id": "qa.o015.ch04.accessibility",
        "status": "pass_with_limitation",
        "event_type": "accessibility",
        "result": "pass_with_limitation",
        "witness_artifact_ids": [
            "artifact.habring.target-pdf-ch04",
            "artifact.habring.target-text-ch04",
        ],
        "checks": [
            "PDF language metadata is id-ID.",
            "Text extraction produced 13,866 characters.",
            "No figures require alternative text in this chapter.",
        ],
        "limitations": ["PDF is untagged."],
    },
    {
        "id": "qa.o015.ch04.math-rereview",
        "status": "pass",
        "event_type": "mathematics",
        "result": "pass",
        "witness_artifact_ids": [
            "artifact.habring.target-ch04",
            "artifact.habring.structure-report-ch04",
            "artifact.habring.solver-results-ch04",
        ],
        "verified_at": RECORDED_AT,
        "target_sha256": (
            "29fdc330007009bd765a17ca1dcd0cf130ff802312ebb402bf03413da5f96a7d"
        ),
        "review_outcome": {"p1": 0, "p2": 0, "p3": 0},
        "scope": (
            "Independent final mathematical rereview of the complete "
            "translated Chapter 4 unit."
        ),
    },
    {
        "id": "qa.o015.ch04.language",
        "status": "not_recorded",
        "event_type": "language",
        "result": "not_recorded",
        "witness_artifact_ids": [],
        "gap": "No independent Indonesian language review is recorded.",
    },
]
for spec in qa_specs:
    qa = common("qa_event", spec.pop("id"), spec.pop("status"))
    qa.update({"unit_id": "unit.habring.v1.ch04", **spec})
    records.append(qa)


# Unit hierarchy, sequence, concept topology, and exercise relations.
relation_specs: list[tuple[str, str, str, str, str]] = [
    (
        "relation.unit.root-contains-ch04",
        "contains",
        "unit.habring.v1",
        "unit.habring.v1.ch04",
        "Source Chapter 4.",
    ),
    (
        "relation.unit.ch03-precedes-ch04",
        "precedes",
        "unit.habring.v1.ch03",
        "unit.habring.v1.ch04",
        "Contiguous source order.",
    ),
    (
        "relation.unit.ch04-depends-on-ch03",
        "depends-on",
        "unit.habring.v1.ch04",
        "unit.habring.v1.ch03",
        "Projected subgradient descent uses Chapter 3 subgradients.",
    ),
    (
        "relation.unit.ch04-prerequisite-hilbert-space",
        "prerequisite",
        "unit.habring.v1.ch04",
        "concept.hilbert-space",
        "Projection theorem ambient-space prerequisite.",
    ),
    (
        "relation.unit.ch04-prerequisite-subdifferential",
        "prerequisite",
        "unit.habring.v1.ch04",
        "concept.convex-subdifferential",
        "Algorithmic subgradient prerequisite.",
    ),
]
for order in range(1, 9):
    relation_specs.append(
        (
            f"relation.unit.ch04-contains-seg{order:04d}",
            "contains",
            "unit.habring.v1.ch04",
            f"d90.hab.v1.ch04.seg{order:04d}",
            "Ordered reader-facing translation segment.",
        )
    )
relation_specs.extend(
    [
        (
            "relation.segment.ch04-seg0001-illustrates-constrained-optimality",
            "illustrates",
            "d90.hab.v1.ch04.seg0001",
            "concept.constrained-convex-optimality",
            "Indicator reformulation motivates the projected method.",
        ),
        (
            "relation.segment.ch04-seg0002-proves-metric-projection",
            "proves",
            "d90.hab.v1.ch04.seg0002",
            "concept.metric-projection",
            "Existence and uniqueness in a real Hilbert space.",
        ),
        (
            "relation.segment.ch04-seg0003-defines-projected-method",
            "defines",
            "d90.hab.v1.ch04.seg0003",
            "concept.projected-subgradient-method",
            "Projected subgradient iteration.",
        ),
        (
            "relation.segment.ch04-seg0003-proves-projection-characterization",
            "proves",
            "d90.hab.v1.ch04.seg0003",
            "concept.metric-projection",
            "Variational characterization of projection.",
        ),
        (
            "relation.segment.ch04-seg0004-proves-nonexpansive",
            "proves",
            "d90.hab.v1.ch04.seg0004",
            "concept.nonexpansive-mapping",
            "Metric projection is one-Lipschitz.",
        ),
        (
            "relation.segment.ch04-seg0005-proves-fundamental",
            "proves",
            "d90.hab.v1.ch04.seg0005",
            "concept.fundamental-projected-subgradient-inequality",
            "Core recursive estimate.",
        ),
        (
            "relation.segment.ch04-seg0006-defines-polyak",
            "defines",
            "d90.hab.v1.ch04.seg0006",
            "concept.polyak-step-size",
            "Polyak rule with the zero-subgradient case.",
        ),
        (
            "relation.segment.ch04-seg0006-proves-best-iterate",
            "proves",
            "d90.hab.v1.ch04.seg0006",
            "concept.best-iterate-rate",
            "Corrected inverse-square-root rate.",
        ),
        (
            "relation.segment.ch04-seg0007-defines-diminishing",
            "defines",
            "d90.hab.v1.ch04.seg0007",
            "concept.diminishing-step-size",
            "General positive-step convergence condition.",
        ),
        (
            "relation.segment.ch04-seg0008-proves-strongly-convex-rate",
            "proves",
            "d90.hab.v1.ch04.seg0008",
            "concept.best-iterate-rate",
            "Corrected strongly convex value and iterate rates.",
        ),
        (
            "relation.surface.ch04-exercise01-exercises-projection",
            "exercises",
            "surface.habring.v1.ch04.exercise01",
            "concept.metric-projection",
            "Subspace equality case.",
        ),
        (
            "relation.surface.ch04-exercise02-exercises-subgradient-bound",
            "exercises",
            "surface.habring.v1.ch04.exercise02",
            "concept.subgradient-norm-bound",
            "Global Lipschitz sufficient condition.",
        ),
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


# Refresh hashes for all previously registered artifacts whose bytes may have
# changed during the Chapter 4 evidence pass (notably ledger and validator).
for record in records:
    if record.get("entity_type") != "artifact":
        continue
    path = ROOT / record["path"]
    if not path.is_file():
        raise FileNotFoundError(path)
    data = path.read_bytes()
    record["bytes"] = len(data)
    record["sha256"] = sha256(data)


# Deterministic entity/id order and byte-stable JSONL/CSV projection.
entity_rank = {
    entity_type: rank
    for rank, entity_type in enumerate(schema["entity_order"])
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
