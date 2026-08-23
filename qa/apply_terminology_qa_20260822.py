#!/usr/bin/env python3
"""Apply the bounded Indonesian terminology QA to the O015 backend.

The transaction is idempotent: it modifies only enumerated term records and
adds a finite terminology-evidence closure. All unrelated records must remain
byte-identical at the canonical-record level.
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

RECORDED_AT = "2026-08-22T23:45:00Z"
WORKFLOW = "o015-indonesian-terminology-qa-20260822"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_JSONL_SHA256 = (
    "e57a457d20edfcf772f38f7dd9dfdd3368530d785bbf5b71179b90784b8130f9"
)
BASELINE_CSV_SHA256 = (
    "e2ca8f3b58dc74e208a579ff1b55997d0e5e202f49c2b018edce6358b7492c2f"
)
BASELINE_RECORD_COUNT = 1283

QA_LOG = "00_control/INDONESIAN_TERMINOLOGY_QA_20260822.md"
PROVENANCE = "PROVENANCE.md"
LANDING = (
    "authority/comparator/indonesian-terminology/"
    "caturiyati-lestari-2011/landing.html"
)
PDF = (
    "authority/comparator/indonesian-terminology/"
    "caturiyati-lestari-2011/M-45-Caturiyati.pdf"
)

FROZEN_WITNESSES = {
    LANDING: (
        21286,
        "088f79135da630d7230e7e7d656163bd4e47d4aff1a569235e10532b8d9bd620",
    ),
    PDF: (
        204675,
        "02055e84a12d3179e0fe845ce8f0a38ca7c09fc0159781136642a668ca5df73c",
    ),
}


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
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


for relative, expected in FROZEN_WITNESSES.items():
    actual = file_info(relative)
    if actual != expected:
        raise ValueError(f"terminology witness mismatch: {relative}: {actual} != {expected}")

schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
incoming_jsonl = JSONL_PATH.read_bytes()
incoming_csv = CSV_PATH.read_bytes()
records = [
    json.loads(line)
    for line in incoming_jsonl.decode("utf-8").splitlines()
    if line.strip()
]

if len({record["id"] for record in records}) != len(records):
    raise ValueError("duplicate record IDs in incoming backend")

incoming_by_id = {record["id"]: record for record in records}
already_applied = "qa.o015.terminology-qa-20260822" in incoming_by_id
if not already_applied:
    if len(records) != BASELINE_RECORD_COUNT:
        raise ValueError(f"unexpected incoming record count: {len(records)}")
    if sha256(incoming_jsonl) != BASELINE_JSONL_SHA256:
        raise ValueError("incoming JSONL is not the frozen ten-unit baseline")
    if sha256(incoming_csv) != BASELINE_CSV_SHA256:
        raise ValueError("incoming CSV is not the frozen ten-unit baseline")

artifact_refreshes = {
    "artifact.penn.build-log-ch04": "build/penn-unit-04-id/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.log",
    "artifact.penn.build-log-ch05": "build/penn-unit-05-id/D90-PENN-05-metode-newton-dan-koreksi-id.log",
    "artifact.penn.target-pdf-ch04": "output/pdf/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf",
    "artifact.penn.target-pdf-ch05": "output/pdf/D90-PENN-05-metode-newton-dan-koreksi-id.pdf",
    "artifact.penn.target-text-ch04": "qa/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.txt",
    "artifact.penn.target-text-ch05": "qa/D90-PENN-05-metode-newton-dan-koreksi-id.txt",
    "artifact.penn.target-wrapper-ch04": "source/id-ID/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex",
    "artifact.penn.target-wrapper-ch05": "source/id-ID/D90-PENN-05-metode-newton-dan-koreksi-id.tex",
    "artifact.penn.visual-qa-ch04": "qa/PENN_CH04_VISUAL_QA.json",
    "artifact.penn.visual-qa-ch05": "qa/PENN_CH05_VISUAL_QA.json",
}
allowed_updates = {
    "term.composite-objective",
    "term.supporting-hyperplane",
    *artifact_refreshes,
}
preserved_before = {
    record_id: canonical_json(record)
    for record_id, record in incoming_by_id.items()
    if record_id not in allowed_updates
    and not record_id.startswith("concept.terminology-")
    and not record_id.startswith("term.terminology-")
    and record_id
    not in {
        "rights.o015-terminology-qa",
        "rights.o015-uny-terminology-witness",
        "artifact.o015.terminology-qa-log-20260822",
        "artifact.o015.model-provenance",
        "artifact.o015.terminology-qa-generator-20260822",
        "artifact.o015.terminology-qa-validator-20260822",
        "artifact.o015.uny-terminology-landing-2011",
        "artifact.o015.uny-terminology-pdf-2011",
        "qa.o015.terminology-qa-20260822",
    }
}

records = [
    record
    for record in records
    if record["id"]
    not in {
        "concept.terminology-affine-map",
        "concept.terminology-feasible-set",
        "concept.terminology-mathematical-inequality",
        "concept.terminology-objective-function",
        "term.terminology-affine",
        "term.terminology-feasible",
        "term.terminology-inequality",
        "term.terminology-objective-function",
        "rights.o015-terminology-qa",
        "rights.o015-uny-terminology-witness",
        "artifact.o015.terminology-qa-log-20260822",
        "artifact.o015.model-provenance",
        "artifact.o015.terminology-qa-generator-20260822",
        "artifact.o015.terminology-qa-validator-20260822",
        "artifact.o015.uny-terminology-landing-2011",
        "artifact.o015.uny-terminology-pdf-2011",
        "qa.o015.terminology-qa-20260822",
    }
]
by_id = {record["id"]: record for record in records}

composite = by_id["term.composite-objective"]
composite["variants"] = ["fungsi tujuan komposit"]
composite["terminology_qa"] = "00_control/INDONESIAN_TERMINOLOGY_QA_20260822.md"

supporting = by_id["term.supporting-hyperplane"]
supporting["variants"] = ["bidang hiper penyokong", "bidang hiper pendukung"]
supporting["terminology_qa"] = "00_control/INDONESIAN_TERMINOLOGY_QA_20260822.md"

for record_id, path in artifact_refreshes.items():
    record = by_id[record_id]
    size, digest = file_info(path)
    record["bytes"] = size
    record["sha256"] = digest
    record["terminology_qa"] = "00_control/INDONESIAN_TERMINOLOGY_QA_20260822.md"

new_records: list[dict[str, Any]] = []

concept_specs = [
    ("concept.terminology-affine-map", "affine map or affine set"),
    ("concept.terminology-feasible-set", "feasible point and feasible set"),
    ("concept.terminology-mathematical-inequality", "mathematical inequality"),
    ("concept.terminology-objective-function", "optimization objective function"),
]
for record_id, label in concept_specs:
    record = common("concept", record_id, "current")
    record.update(
        {
            "canonical_label": label,
            "domain": "convex analysis and continuous optimization terminology",
            "evidence_artifact_id": "artifact.o015.terminology-qa-log-20260822",
        }
    )
    new_records.append(record)

term_specs = [
    (
        "term.terminology-affine",
        "concept.terminology-affine-map",
        "affine",
        "afin",
        ["affine"],
        [],
        ["d90.hab.v1.ch07.seg0002"],
        "Use the normalized Indonesian form in running prose; preserve source spelling in quotations or bibliographic titles.",
    ),
    (
        "term.terminology-feasible",
        "concept.terminology-feasible-set",
        "feasible",
        "layak",
        [],
        [],
        ["d90.hab.v1.ch09.seg0008"],
        "Use for points, sets, constraints, and problems that satisfy the stated constraints.",
    ),
    (
        "term.terminology-inequality",
        "concept.terminology-mathematical-inequality",
        "inequality",
        "ketaksamaan",
        ["pertidaksamaan"],
        [],
        ["d90.hab.v1.ch07.seg0002"],
        "The variant is accepted; the preferred form matches the representative UNY comparator and the dominant O015 usage.",
    ),
    (
        "term.terminology-objective-function",
        "concept.terminology-objective-function",
        "objective function",
        "fungsi tujuan",
        ["fungsi objektif", "objektif", "fungsi biaya"],
        [],
        ["d90.hab.v1.ch07.seg0010", "d90.hab.v1.ch09.seg0003"],
        "Use fungsi biaya only when the objective is specifically a cost; compact objektif remains acceptable when its noun role is unambiguous.",
    ),
]
for record_id, concept_id, source_term, preferred, variants, rejected, evidence, note in term_specs:
    record = common("term", record_id, "accepted")
    record.update(
        {
            "concept_id": concept_id,
            "locale": "id-ID",
            "source_term": source_term,
            "preferred": preferred,
            "variants": variants,
            "rejected_forms": rejected,
            "scope": "convex analysis and continuous optimization",
            "register": "formal",
            "evidence_segment_ids": evidence,
            "examples": [preferred],
            "usage_note": note,
            "rights_id": "rights.o015-terminology-qa",
            "evidence_artifact_id": "artifact.o015.terminology-qa-log-20260822",
        }
    )
    new_records.append(record)

rights = common("rights", "rights.o015-terminology-qa", "current")
rights.update(
    {
        "component_id": "o015-indonesian-terminology-qa-metadata",
        "rights_expression": "project-local terminology QA metadata",
        "authority_url": "00_control/INDONESIAN_TERMINOLOGY_QA_20260822.md",
        "reuse_status": "project-authored evidence and terminology decisions",
    }
)
new_records.append(rights)

rights = common("rights", "rights.o015-uny-terminology-witness", "current")
rights.update(
    {
        "component_id": "caturiyati-lestari-2011-terminology-witness",
        "rights_expression": "no open license identified; local evidence only",
        "authority_url": "https://eprints.uny.ac.id/7164/",
        "reuse_status": "not admitted and not redistributed",
    }
)
new_records.append(rights)

artifact_specs = [
    (
        "artifact.o015.terminology-qa-log-20260822",
        "terminology_qa_report",
        QA_LOG,
        "rights.o015-terminology-qa",
        {},
    ),
    (
        "artifact.o015.model-provenance",
        "provenance_note",
        PROVENANCE,
        "rights.o015-terminology-qa",
        {"model_identification": "OpenAI Codex gpt-5.6-sol, Ultra"},
    ),
    (
        "artifact.o015.terminology-qa-generator-20260822",
        "backend_generator",
        "qa/apply_terminology_qa_20260822.py",
        "rights.o015-terminology-qa",
        {"toolchain": "Python 3 standard library"},
    ),
    (
        "artifact.o015.terminology-qa-validator-20260822",
        "backend_validator",
        "qa/validate_terminology_qa_20260822.py",
        "rights.o015-terminology-qa",
        {"toolchain": "Python 3 standard library plus Poppler pdfinfo"},
    ),
    (
        "artifact.o015.uny-terminology-landing-2011",
        "local_terminology_witness_landing",
        LANDING,
        "rights.o015-uny-terminology-witness",
        {"official_url": "https://eprints.uny.ac.id/7164/", "distribution_state": "excluded"},
    ),
    (
        "artifact.o015.uny-terminology-pdf-2011",
        "local_terminology_witness_pdf",
        PDF,
        "rights.o015-uny-terminology-witness",
        {
            "official_url": "https://eprints.uny.ac.id/7164/1/M-45%20-%20Caturiyati.pdf",
            "pages": 8,
            "distribution_state": "excluded",
        },
    ),
]
for record_id, kind, path, rights_id, extra in artifact_specs:
    size, digest = file_info(path)
    record = common("artifact", record_id, "current")
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
    new_records.append(record)

qa_event = common("qa_event", "qa.o015.terminology-qa-20260822", "passed")
qa_event.update(
    {
        "event_type": "indonesian_field_terminology_comparison",
        "result": "pass_with_non_arxiv_fallback",
        "witness_artifact_ids": [
            "artifact.o015.terminology-qa-log-20260822",
            "artifact.o015.uny-terminology-landing-2011",
            "artifact.o015.uny-terminology-pdf-2011",
            "artifact.penn.visual-qa-ch04",
            "artifact.penn.visual-qa-ch05",
        ],
        "model_provenance_artifact_id": "artifact.o015.model-provenance",
        "arxiv_exact_query_results": {
            "optimisasi konveks": 0,
            "optimasi konveks": 0,
            "subgradien": 0,
        },
        "propagation_result": "four isolated pertidaksamaan occurrences normalized to ketaksamaan; all other differences registered as accepted variants",
    }
)
new_records.append(qa_event)

records.extend(new_records)
if len({record["id"] for record in records}) != len(records):
    raise ValueError("duplicate record IDs after terminology transaction")

final_by_id = {record["id"]: canonical_json(record) for record in records}
changed_unrelated = sorted(
    record_id
    for record_id, before in preserved_before.items()
    if final_by_id.get(record_id) != before
)
missing_unrelated = sorted(set(preserved_before) - set(final_by_id))
if changed_unrelated or missing_unrelated:
    raise ValueError(
        f"unrelated backend records changed: changed={changed_unrelated}; missing={missing_unrelated}"
    )

entity_rank = {entity_type: rank for rank, entity_type in enumerate(schema["entity_order"])}
records.sort(key=lambda record: (entity_rank[record["entity_type"]], record["id"]))
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

report = {
    "already_applied_on_entry": already_applied,
    "baseline_record_count": BASELINE_RECORD_COUNT,
    "changed_existing_record_ids": sorted(allowed_updates),
    "entity_counts": dict(sorted(Counter(record["entity_type"] for record in records).items())),
    "jsonl": {"bytes": file_info("backend/records.jsonl")[0], "sha256": file_info("backend/records.jsonl")[1]},
    "csv": {"bytes": file_info("backend/records.csv")[0], "sha256": file_info("backend/records.csv")[1]},
    "new_record_ids": sorted(record["id"] for record in new_records),
    "record_count": len(records),
    "result": "pass",
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
