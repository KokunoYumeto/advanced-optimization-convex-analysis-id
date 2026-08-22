#!/usr/bin/env python3
"""Add the provisional Penn MATH 555 Chapter 3 closure to the O015 backend.

This extension deliberately treats the already validated 793-record Habring
backend as immutable.  On every run it removes only the stable IDs owned by
this script, proves the remaining stable-ID-sorted record set byte-for-byte,
then reconstructs the Penn closure from frozen local evidence.
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
SHARED_LEDGER_PATH = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"

RECORDED_AT = "2026-08-22T18:05:00Z"
WORKFLOW = "o015-penn-ch03-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 793
ORIGINAL_BASELINE_RECORD_SET_SHA256 = (
    "c062c9a5ea2460e33eb2b71520899ea4f7002f4d2bee428dd88715ac726d7180"
)
REFRESHED_BASELINE_RECORD_SET_SHA256 = (
    "7588bdc2e110564bd420e5bcf7bd1737b3f91dd50eabfa213eaa12fa757bfe4f"
)
BASELINE_SEMANTIC_RECORD_SET_SHA256 = (
    "41fd7e0f51828f4c70f9f56a8ab424ad1ee944bb3f02ba5a654ff059bbeab878"
)
BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256 = (
    "f96a83ed135d53f60eefae4323714d2bc1497959d6de5c2816d39631c63c9548"
)
LIVE_LEDGER_IDENTITY = (
    73183,
    "d356801c960c9fe59bb53eb6475c4d3b265288cc36df5c130a4777a56e44831e",
)

SOURCE_PATH = "authority/penn-state/source/ClassNotes/Section3.tex"
TARGET_PATH = "source/id-ID/penn-03-pendakian-gradien-dan-pencarian-garis-id.tex"
WRAPPER_PATH = "source/id-ID/D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.tex"
BIB_PATH = "source/id-ID/references-penn-ch03-id.bbl"
PDF_PATH = "output/pdf/D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.pdf"
LOG_PATH = "build/penn-unit-03-id/D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.log"
TEXT_PATH = "qa/D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.txt"
AUDIT_SOURCE_PATH = "qa/audit_penn_ch03_unit.py"
STRUCTURE_REPORT_PATH = "qa/PENN_CH03_STRUCTURE_REPORT.json"
FORMULA_MANIFEST_PATH = "qa/PENN_CH03_FORMULA_DELTA_MANIFEST.json"
PROPOSED_LEDGER_PATH = "qa/PENN_CH03_PROPOSED_LEDGER.jsonl"
SOLVER_SOURCE_PATH = "qa/validate_penn_ch03_unit.py"
SOLVER_RESULTS_PATH = "qa/PENN_CH03_SOLVER_RESULTS.json"

SOURCE_EDITION_ID = "edition.penn.math555.source-v1-0"
TARGET_EDITION_ID = "edition.penn.math555.id-id.v1"
ROOT_UNIT_ID = "unit.penn.v1"
UNIT_ID = "unit.penn.v1.ch03"
SOURCE_RIGHTS_ID = "rights.o015-penn-ch03-source"
TARGET_RIGHTS_ID = "rights.o015-penn-id-ch03"

EXPECTED_PROPOSAL_IDS = [
    f"O015-PENN-ADV-{number:04d}" for number in range(4, 25)
]

FROZEN_FILES: dict[str, tuple[int, str]] = {
    SOURCE_PATH: (
        41715,
        "d4ae6142e2366b12575eafddc833df067518af114e9816187668cc367be43010",
    ),
    TARGET_PATH: (
        44364,
        "7c75d0ae56a5a912d561d91ece607f088a4ff4f3de4dbc3396ce40d6d7d6a229",
    ),
    WRAPPER_PATH: (
        8203,
        "0876d121d417ef4f73f308eac62056a55499628af44713e06246315852dcfa38",
    ),
    BIB_PATH: (
        852,
        "d3e645c03298c14fee272d44b5d471a81d31aec60a95d4f568b4923edde63867",
    ),
    PDF_PATH: (
        515851,
        "e1be82d06572c51b403608cd9595cc5adf2dc64cfa93f53001eba94e48f77e3e",
    ),
    LOG_PATH: (
        27077,
        "2702aa4b756fec32557368a144ddfe9a91f32363e034cefea9956034178a74f6",
    ),
    TEXT_PATH: (
        47464,
        "9880848f06e2f1104a88213f3a9f7629db87c6cc8bf0b515281cf553ed1895bc",
    ),
    PROPOSED_LEDGER_PATH: (
        14813,
        "80aa5a3f7b4f46c7dfe01f58f6f68555c9aeaeb91d0877eaf27cbb447c4a67fa",
    ),
    "authority/penn-state/Math555_SRC.zip": (
        23909024,
        "1958af9417aa7cd057f321c3c6f71a8c02349fb1d32da75f6bad05eb66286a0e",
    ),
    "authority/penn-state/Math555.pdf": (
        4776722,
        "f7b99401af875333f3becb591eebf61fac81280768537c20b8a1264d578cb4ff",
    ),
    "authority/penn-state/source/ClassNotes/Figures/DichotomousSearch.pdf": (
        101202,
        "ccdc24742cbb4b908b740c34940cf84f314994e3bdb6b815edf902eb98be32e4",
    ),
    "authority/penn-state/source/ClassNotes/Figures/GoldenRatioProof.pdf": (
        81307,
        "ad405a95c466ca65670c0be53cb54667846106ac03ffa9c86bf4248daf6cbb32",
    ),
    "authority/penn-state/source/ClassNotes/Figures/GoldenSectionFail.pdf": (
        9913,
        "5abd708847cf98662f12645172e9b3390420d0263840ac3d7def776ffad07868",
    ),
    "authority/penn-state/source/ClassNotes/Figures/NonConcave.pdf": (
        9733,
        "bc17c66377f01fc567639fd745f436d80ccedebc50824aba2b5d0ed470bc7c64",
    ),
    "source/id-ID/figures/DichotomousSearch.pdf": (
        101202,
        "ccdc24742cbb4b908b740c34940cf84f314994e3bdb6b815edf902eb98be32e4",
    ),
    "source/id-ID/figures/GoldenRatioProof.pdf": (
        81307,
        "ad405a95c466ca65670c0be53cb54667846106ac03ffa9c86bf4248daf6cbb32",
    ),
    "source/id-ID/figures/GoldenSectionFail.pdf": (
        9913,
        "5abd708847cf98662f12645172e9b3390420d0263840ac3d7def776ffad07868",
    ),
    "source/id-ID/figures/NonConcave.pdf": (
        9733,
        "bc17c66377f01fc567639fd745f436d80ccedebc50824aba2b5d0ed470bc7c64",
    ),
}


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = "".join(
        canonical_json(record) + "\n"
        for record in sorted(records, key=lambda item: item["id"])
    ).encode("utf-8")
    return sha256(payload)


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
    record_id: str, artifact_kind: str, path: str, **extra: Any
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


CONCEPT_SPECS: list[tuple[str, str, list[str], str]] = [
    ("concept.penn.gradient-ascent", "gradient ascent", ["concept.gradient"], "smooth numerical optimization"),
    ("concept.penn.ascent-direction", "ascent direction", ["concept.gradient"], "smooth numerical optimization"),
    ("concept.penn.exact-line-search", "exact line search", ["concept.penn.ascent-direction"], "smooth numerical optimization"),
    ("concept.penn.quadratic-interpolation", "quadratic interpolation of three samples", [], "one-dimensional optimization"),
    ("concept.penn.maximum-bracketing", "bracketing a one-dimensional maximizer", ["concept.penn.quadratic-interpolation"], "one-dimensional optimization"),
    ("concept.penn.unimodal-line-search", "strict and weak unimodality in line search", [], "one-dimensional optimization"),
    ("concept.penn.dichotomous-search", "dichotomous interval search", ["concept.penn.maximum-bracketing"], "one-dimensional optimization"),
    ("concept.penn.golden-section-search", "golden-section interval search", ["concept.penn.unimodal-line-search"], "one-dimensional optimization"),
    ("concept.penn.bisection-search", "derivative-sign bisection search", ["concept.penn.unimodal-line-search"], "one-dimensional optimization"),
    ("concept.penn.strong-concavity-distance-bound", "optimizer-distance bound from strong concavity", ["concept.strong-convexity"], "one-dimensional optimization"),
    ("concept.penn.one-dimensional-newton", "one-dimensional Newton iteration for maximization", ["concept.gradient"], "smooth numerical optimization"),
    ("concept.penn.contraction-mapping", "contraction mapping and fixed-point convergence", [], "numerical analysis"),
    ("concept.penn.convergence-order", "Q-order of convergence", [], "numerical analysis"),
    ("concept.penn.newton-quadratic-convergence", "local quadratic convergence of Newton iteration at a simple root", ["concept.penn.one-dimensional-newton", "concept.penn.convergence-order"], "numerical analysis"),
]

TERM_SPECS: list[tuple[str, str, str, str, int, list[str]]] = [
    ("term.penn.gradient-ascent", "concept.penn.gradient-ascent", "gradient ascent", "pendakian gradien", 1, []),
    ("term.penn.ascent-direction", "concept.penn.ascent-direction", "ascent direction", "arah naik", 2, []),
    ("term.penn.exact-line-search", "concept.penn.exact-line-search", "exact line search", "pencarian garis eksak", 2, []),
    ("term.penn.quadratic-interpolation", "concept.penn.quadratic-interpolation", "quadratic interpolation", "interpolasi kuadratik", 3, []),
    ("term.penn.maximum-bracketing", "concept.penn.maximum-bracketing", "maximum bracketing", "pengurungan maksimum", 3, []),
    ("term.penn.unimodal-function", "concept.penn.unimodal-line-search", "unimodal function", "fungsi unimodal", 3, ["fungsi bermodus tunggal"]),
    ("term.penn.dichotomous-search", "concept.penn.dichotomous-search", "dichotomous search", "pencarian dikotomis", 4, []),
    ("term.penn.golden-section-search", "concept.penn.golden-section-search", "golden-section search", "pencarian bagian emas", 5, []),
    ("term.penn.bisection-search", "concept.penn.bisection-search", "bisection search", "pencarian biseksi", 6, []),
    ("term.penn.strong-concavity", "concept.penn.strong-concavity-distance-bound", "strong concavity", "kekonkavan kuat", 6, []),
    ("term.penn.newton-method", "concept.penn.one-dimensional-newton", "Newton's method", "metode Newton", 7, []),
    ("term.penn.contraction-mapping", "concept.penn.contraction-mapping", "contraction mapping", "pemetaan kontraksi", 8, []),
    ("term.penn.convergence-order", "concept.penn.convergence-order", "order of convergence", "laju konvergensi", 8, ["orde konvergensi"]),
    ("term.penn.quadratic-convergence", "concept.penn.newton-quadratic-convergence", "quadratic convergence", "konvergensi kuadratik", 8, []),
]

SEGMENT_SPECS: list[tuple[int, int, int, str, str, list[str]]] = [
    (1, 1, 47, "Basic ascent algorithm", "Algoritma pendakian dasar", ["concept.penn.gradient-ascent"]),
    (2, 48, 80, "Ascent directions and exact line search", "Arah naik dan pencarian garis eksak", ["concept.penn.ascent-direction", "concept.penn.exact-line-search"]),
    (3, 81, 160, "Maximum bracketing", "Pengurungan maksimum", ["concept.penn.quadratic-interpolation", "concept.penn.maximum-bracketing", "concept.penn.unimodal-line-search"]),
    (4, 161, 224, "Dichotomous search", "Pencarian dikotomis", ["concept.penn.dichotomous-search"]),
    (5, 225, 312, "Golden-section search", "Pencarian bagian emas", ["concept.penn.golden-section-search", "concept.penn.unimodal-line-search"]),
    (6, 313, 404, "Bisection search", "Pencarian biseksi", ["concept.penn.bisection-search", "concept.penn.strong-concavity-distance-bound"]),
    (7, 405, 452, "One-dimensional Newton method", "Metode Newton satu dimensi", ["concept.penn.one-dimensional-newton"]),
    (8, 453, 608, "Newton convergence", "Konvergensi metode Newton", ["concept.penn.contraction-mapping", "concept.penn.convergence-order", "concept.penn.newton-quadratic-convergence"]),
]

ALGORITHM_SPECS: list[tuple[str, int, int, int, int, str, str, str]] = [
    ("surface.penn.v1.ch03.algorithm01", 13, 28, 17, 34, "translated_source_pseudocode", "concept.penn.gradient-ascent", "Modified gradient-ascent algorithm"),
    ("surface.penn.v1.ch03.bridge01", 114, 114, 122, 132, "independent_replacement_for_excluded_maple", "concept.penn.quadratic-interpolation", "Quadratic turning point"),
    ("surface.penn.v1.ch03.bridge02", 122, 128, 137, 149, "independent_replacement_for_excluded_maple", "concept.penn.maximum-bracketing", "Safeguarded parabolic bracketing"),
    ("surface.penn.v1.ch03.bridge03", 165, 171, 192, 202, "independent_replacement_for_excluded_maple", "concept.penn.dichotomous-search", "Dichotomous search"),
    ("surface.penn.v1.ch03.bridge04", 275, 281, 309, 319, "independent_replacement_for_excluded_maple", "concept.penn.golden-section-search", "Golden-section search"),
    ("surface.penn.v1.ch03.bridge05", 326, 332, 366, 378, "independent_replacement_for_excluded_maple", "concept.penn.bisection-search", "Bisection search"),
    ("surface.penn.v1.ch03.bridge06", 420, 426, 443, 455, "independent_replacement_for_excluded_maple", "concept.penn.one-dimensional-newton", "One-dimensional Newton method"),
]

ASSET_SPECS: list[tuple[str, str, str, int, str]] = [
    ("asset.penn.v1.ch03.dichotomous-search", "DichotomousSearch.pdf", "concept.penn.dichotomous-search", 4, "Dichotomous interval geometry"),
    ("asset.penn.v1.ch03.golden-ratio-proof", "GoldenRatioProof.pdf", "concept.penn.golden-section-search", 5, "Golden-ratio interval geometry"),
    ("asset.penn.v1.ch03.golden-section-failure", "GoldenSectionFail.pdf", "concept.penn.unimodal-line-search", 5, "Weak-unimodality plateau tie failure"),
    ("asset.penn.v1.ch03.nonconcave-example", "NonConcave.pdf", "concept.penn.dichotomous-search", 4, "Nonconcave line-search example"),
]


GENERATED_CONCEPT_IDS = {item[0] for item in CONCEPT_SPECS}
GENERATED_TERM_IDS = {item[0] for item in TERM_SPECS}
GENERATED_EXACT_IDS = {
    "resource.penn.math555-nonlinear-programming",
    SOURCE_EDITION_ID,
    TARGET_EDITION_ID,
    ROOT_UNIT_ID,
    UNIT_ID,
    SOURCE_RIGHTS_ID,
    TARGET_RIGHTS_ID,
    "rights.o015-penn-ch03-figures",
    "rights.o015-penn-ch03-bibliography",
    "rights.o015-penn-ch03-bridges",
    "rights.o015-penn-ch03-maple-excluded",
    "rights.o015-penn-ch03-audit",
    "artifact.o015.backend-generator-penn-ch03",
    "artifact.o015.backend-validator-penn-ch03",
}


def is_generated(record: dict[str, Any]) -> bool:
    record_id = record.get("id", "")
    if record_id in GENERATED_CONCEPT_IDS | GENERATED_TERM_IDS | GENERATED_EXACT_IDS:
        return True
    return record_id.startswith(
        (
            "d90.penn.v1.ch03.",
            "surface.penn.v1.ch03.",
            "asset.penn.v1.ch03.",
            "correction.o015-penn-adv-",
            "relation.penn.",
            "qa.o015.penn-ch03.",
            "artifact.penn.",
        )
    )


for relative, expected in FROZEN_FILES.items():
    actual = file_info(relative)
    if actual != expected:
        raise ValueError(
            f"frozen Penn artifact differs: {relative}: expected {expected}, found {actual}"
        )

schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
existing_records = [
    json.loads(line)
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
records = [record for record in existing_records if not is_generated(record)]
if len(records) != BASELINE_RECORD_COUNT:
    raise ValueError(
        f"immutable Habring baseline has {len(records)} records, expected {BASELINE_RECORD_COUNT}"
    )
incoming_baseline_sha256 = record_set_sha256(records)
if incoming_baseline_sha256 not in {
    ORIGINAL_BASELINE_RECORD_SET_SHA256,
    REFRESHED_BASELINE_RECORD_SET_SHA256,
}:
    raise ValueError("793-record baseline differs beyond the enumerated ledger refresh")
baseline_semantic = [
    record for record in records if record.get("entity_type") != "artifact"
]
if record_set_sha256(baseline_semantic) != BASELINE_SEMANTIC_RECORD_SET_SHA256:
    raise ValueError("immutable 698-record semantic baseline differs")
baseline_immutable_artifacts = [
    record
    for record in records
    if record.get("entity_type") == "artifact"
    and record.get("id") != "artifact.o015.adverse-ledger"
]
if (
    len(baseline_immutable_artifacts) != 94
    or record_set_sha256(baseline_immutable_artifacts)
    != BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256
):
    raise ValueError("immutable 94-record baseline artifact set differs")
ledger_artifact = next(
    (record for record in records if record.get("id") == "artifact.o015.adverse-ledger"),
    None,
)
if ledger_artifact is None:
    raise ValueError("baseline lacks artifact.o015.adverse-ledger")
if file_info("00_control/ADVERSE_LEDGER.jsonl") != LIVE_LEDGER_IDENTITY:
    raise ValueError("live admitted correction ledger identity differs")
baseline_refreshed_ids: list[str] = []
if (ledger_artifact.get("bytes"), ledger_artifact.get("sha256")) != LIVE_LEDGER_IDENTITY:
    baseline_refreshed_ids.append("artifact.o015.adverse-ledger")
ledger_artifact["bytes"], ledger_artifact["sha256"] = LIVE_LEDGER_IDENTITY
if record_set_sha256(records) != REFRESHED_BASELINE_RECORD_SET_SHA256:
    raise ValueError("baseline ledger refresh produced an unexpected record set")

baseline_by_id = {record["id"]: canonical_json(record) for record in records}
baseline_ids = set(baseline_by_id)
generated_ids: set[str] = set()


def add(record: dict[str, Any]) -> None:
    record_id = record["id"]
    if record_id in baseline_ids or record_id in generated_ids:
        raise ValueError(f"stable-ID collision while adding Penn Chapter 3: {record_id}")
    generated_ids.add(record_id)
    records.append(record)


source_text = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
target_text = (ROOT / TARGET_PATH).read_text(encoding="utf-8")
wrapper_text = (ROOT / WRAPPER_PATH).read_text(encoding="utf-8")
log_text = (ROOT / LOG_PATH).read_text(encoding="utf-8", errors="replace")
structure_report = json.loads((ROOT / STRUCTURE_REPORT_PATH).read_text(encoding="utf-8"))
formula_manifest = json.loads((ROOT / FORMULA_MANIFEST_PATH).read_text(encoding="utf-8"))
proposal_records = [
    json.loads(line)
    for line in (ROOT / PROPOSED_LEDGER_PATH).read_text(encoding="utf-8").splitlines()
    if line
]
proposal_ids = [record.get("event_id") for record in proposal_records]
if proposal_ids != EXPECTED_PROPOSAL_IDS:
    raise ValueError(
        f"Penn proposal IDs must be exactly {EXPECTED_PROPOSAL_IDS}; found {proposal_ids}"
    )
if len(set(proposal_ids)) != len(proposal_ids):
    raise ValueError("duplicate Penn proposal event ID")

shared_ledger_records = [
    json.loads(line)
    for line in SHARED_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
shared_by_event = {
    record.get("event_id"): record
    for record in shared_ledger_records
    if isinstance(record.get("event_id"), str)
}
shared_collisions = sorted(set(proposal_ids).intersection(shared_by_event))
if shared_collisions not in ([], EXPECTED_PROPOSAL_IDS):
    raise ValueError(f"partial or conflicting shared-ledger integration: {shared_collisions}")
ledger_integrated = shared_collisions == EXPECTED_PROPOSAL_IDS
if ledger_integrated:
    for proposal in proposal_records:
        if shared_by_event[proposal["event_id"]] != proposal:
            raise ValueError(
                f"shared ledger differs from proposal for {proposal['event_id']}"
            )

audit_failures = [
    check.get("check", "unnamed")
    for check in structure_report.get("checks", [])
    if check.get("status") != "PASS"
]
audit_pass = (
    structure_report.get("admission_status") == "PASS" and not audit_failures
)

solver_available = (ROOT / SOLVER_SOURCE_PATH).is_file() and (
    ROOT / SOLVER_RESULTS_PATH
).is_file()
solver_results: dict[str, Any] = {}
solver_pass = False
if solver_available:
    solver_results = json.loads((ROOT / SOLVER_RESULTS_PATH).read_text(encoding="utf-8"))
    solver_pass = (
        str(solver_results.get("result") or solver_results.get("status", "")).lower()
        == "pass"
    )

candidate_ready = audit_pass and solver_pass and ledger_integrated
admission_state = (
    "candidate_ready_for_root_admission"
    if candidate_ready
    else "provisional_audit_or_solver_pending"
)

if "CC BY-NC-SA 3.0 US" not in wrapper_text:
    raise ValueError("Penn wrapper lacks exact CC BY-NC-SA 3.0 US notice")
if "tidak disahkan" not in wrapper_text.lower() and "bukan" not in wrapper_text.lower():
    raise ValueError("Penn wrapper lacks an Indonesian non-endorsement notice")
if source_text.count(r"\lstinputlisting") != 6:
    raise ValueError("Penn source must expose exactly six excluded listing calls")
if r"\lstinputlisting" in target_text or "Code/" in target_text:
    raise ValueError("Penn target unexpectedly retains a legacy code dependency")

output_match = re.search(r"Output written on .*?\((\d+) pages?", log_text, re.DOTALL)
pdf_pages = int(output_match.group(1)) if output_match else 0
build_blockers = [
    pattern
    for pattern in (
        "LaTeX Error",
        "Undefined control sequence",
        "There were undefined references",
        "Citation `",
        "Overfull \\hbox",
        "Underfull \\hbox",
    )
    if pattern in log_text
]
build_pass = pdf_pages == 20 and not build_blockers

# Resource and editions.
resource = common(
    "resource", "resource.penn.math555-nonlinear-programming", "source_admitted"
)
resource.update(
    {
        "title": "Nonlinear Programming",
        "creator": "Christopher Griffin",
        "contributors": ["Simon Miller", "Douglas Mercer"],
        "official_record": "https://sites.psu.edu/griffinch/lecture_notes/",
        "official_pdf_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555.pdf",
        "official_source_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "rights_id": SOURCE_RIGHTS_ID,
        "authority_record_id": "o015-penn-math555-v1.0-source",
        "scope_note": "Smooth numerical-optimization donor; Chapter 9 LP material remains excluded as O018 overlap.",
    }
)
add(resource)

edition = common("edition", SOURCE_EDITION_ID, "source_frozen")
edition.update(
    {
        "resource_id": resource["id"],
        "edition_kind": "immutable_local_source_archive",
        "version": "editable source 1.0",
        "language": "en",
        "rights_id": SOURCE_RIGHTS_ID,
        "authority_url": resource["official_source_url"],
        "source_archive": {
            "path": "authority/penn-state/Math555_SRC.zip",
            "bytes": FROZEN_FILES["authority/penn-state/Math555_SRC.zip"][0],
            "sha256": FROZEN_FILES["authority/penn-state/Math555_SRC.zip"][1],
        },
        "public_pdf_witness": {
            "version": "1.0.1",
            "path": "authority/penn-state/Math555.pdf",
            "bytes": FROZEN_FILES["authority/penn-state/Math555.pdf"][0],
            "sha256": FROZEN_FILES["authority/penn-state/Math555.pdf"][1],
        },
        "source_caveat": "The editable archive is v1.0; the public PDF is v1.0.1 and is only a correction witness.",
    }
)
add(edition)

edition = common(
    "edition", TARGET_EDITION_ID, "built" if build_pass else "provisional"
)
edition.update(
    {
        "resource_id": resource["id"],
        "edition_kind": "derivative",
        "version": "working id-ID Chapter 3",
        "language": "id",
        "locale": "id-ID",
        "source_edition_id": SOURCE_EDITION_ID,
        "rights_id": TARGET_RIGHTS_ID,
        "translation_state": "built" if build_pass else "mathematically_reviewed",
        "attribution_url": resource["official_record"],
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "non_endorsement": "Independent Indonesian derivative; no endorsement by Christopher Griffin or Penn State University is implied.",
        "publication_state": "unpublished_working_edition",
        "admission_state": admission_state,
    }
)
add(edition)

unit = common("unit", ROOT_UNIT_ID, "provisional")
unit.update(
    {
        "edition_id": SOURCE_EDITION_ID,
        "source_edition_id": SOURCE_EDITION_ID,
        "target_edition_id": TARGET_EDITION_ID,
        "unit_kind": "work",
        "order": 2,
        "source_local_id": "work-root",
        "source_local_label": "Nonlinear Programming",
        "target_local_label": "Pemrograman Nonlinear",
        "rights_id": SOURCE_RIGHTS_ID,
        "admission_state": admission_state,
    }
)
add(unit)

unit = common("unit", UNIT_ID, "built" if build_pass else "provisional")
unit.update(
    {
        "edition_id": SOURCE_EDITION_ID,
        "source_edition_id": SOURCE_EDITION_ID,
        "target_edition_id": TARGET_EDITION_ID,
        "parent_id": ROOT_UNIT_ID,
        "unit_kind": "chapter",
        "order": 3,
        "source_local_id": "Section3",
        "source_local_label": "Introduction to Gradient Ascent and Line Search Methods",
        "target_local_label": "Pengantar Pendakian Gradien dan Metode Pencarian Garis",
        "source_locator": f"{SOURCE_PATH}:1-608",
        "target_locator": f"{TARGET_PATH}:1-646",
        "rights_id": TARGET_RIGHTS_ID,
        "translation_state": "built" if build_pass else "mathematically_reviewed",
        "admission_state": admission_state,
        "next_source_order_unit": "Section4.tex:1",
    }
)
add(unit)

# Component rights.  The source license is admitted; the chapter binding is
# provisional until the independent mathematical audit and open-solver gate pass.
rights_specs: list[dict[str, Any]] = [
    {
        "id": SOURCE_RIGHTS_ID,
        "status": "admitted",
        "component_id": "o015-penn-text",
        "path": SOURCE_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/lecture_notes/",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["attribution", "identify changes", "noncommercial use", "ShareAlike", "license link", "no implied endorsement"],
        "notes": "Editable source archive version 1.0.",
    },
    {
        "id": TARGET_RIGHTS_ID,
        "status": "derivative",
        "component_id": "o015-penn-id-ch03",
        "path": TARGET_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/lecture_notes/",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["attribute Christopher Griffin", "identify Indonesian translation and corrections", "noncommercial use", "ShareAlike", "license link", "no implied endorsement"],
        "notes": "Complete Chapter 3 candidate and standalone wrapper.",
    },
    {
        "id": "rights.o015-penn-ch03-figures",
        "status": "admitted_with_source_level_notice",
        "component_id": "o015-penn-ch03-figures",
        "path": "source/id-ID/figures",
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US source-archive-level evidence",
        "authority_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["retain exact bytes", "attribute source work", "include under derivative ShareAlike terms"],
        "notes": "Four PDF figures are byte-identical source-archive copies.",
    },
    {
        "id": "rights.o015-penn-ch03-bibliography",
        "status": "adapted_with_caveat",
        "component_id": "o015-penn-ch03-bibliography",
        "path": BIB_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["retain attribution", "identify bounded excerpt", "preserve opaque bundled bibliography evidence"],
        "notes": "Five-entry unit-local excerpt from the bundled Math555.bbl; bibliography databases are absent.",
    },
    {
        "id": "rights.o015-penn-ch03-bridges",
        "status": "project_authored_derivative_component",
        "component_id": "o015-penn-ch03-bridges",
        "path": TARGET_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-authored pseudocode distributed within the CC BY-NC-SA 3.0 US derivative",
        "authority_url": TARGET_PATH,
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": False,
        "required_handling": ["identify independent authorship", "do not claim code identity with Maple source", "retain ShareAlike derivative terms"],
        "notes": "Six independent pseudocode bridges replace excluded Maple listings.",
    },
    {
        "id": "rights.o015-penn-ch03-maple-excluded",
        "status": "excluded",
        "component_id": "o015-penn-maple",
        "path": "authority/penn-state/source/ClassNotes/Code",
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "unclear/external",
        "authority_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["do not translate", "do not redistribute as admitted code", "replace only with independently authored open pseudocode"],
        "notes": "Exactly six source listing calls are excluded from the derivative closure.",
    },
    {
        "id": "rights.o015-penn-ch03-audit",
        "status": "project_local",
        "component_id": "o015-penn-ch03-audit",
        "path": AUDIT_SOURCE_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code and evidence",
        "authority_url": AUDIT_SOURCE_PATH,
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with results", "retain frozen authority hashes", "use open runtimes"],
        "notes": "Independent structural, formula-delta, and numerical validation surfaces.",
    },
]
for spec in rights_specs:
    rights = common("rights", spec.pop("id"), spec.pop("status"))
    rights.update(spec)
    add(rights)

# Concepts and terminology.
for record_id, label, prerequisites, domain in CONCEPT_SPECS:
    concept = common("concept", record_id, "current")
    concept.update(
        {
            "canonical_label": label,
            "prerequisite_ids": prerequisites,
            "domain": domain,
        }
    )
    add(concept)

for record_id, concept_id, source_term, preferred, segment_order, rejected in TERM_SPECS:
    term = common("term", record_id, "accepted")
    term.update(
        {
            "concept_id": concept_id,
            "locale": "id-ID",
            "source_term": source_term,
            "preferred": preferred,
            "variants": [],
            "rejected_forms": rejected,
            "scope": "smooth and one-dimensional numerical optimization",
            "register": "formal",
            "evidence_segment_ids": [f"d90.penn.v1.ch03.seg{segment_order:04d}"],
            "examples": [preferred],
            "rights_id": TARGET_RIGHTS_ID,
        }
    )
    add(term)

# Segment locators are anchored to marker lines in the target but exclude the
# marker and the next segment's source-range comment from their content hash.
target_lines = target_text.splitlines()
marker_pattern = re.compile(r"^% segment-id: (d90\.penn\.v1\.ch03\.seg\d{4})$")
markers = [
    (line_number, match.group(1))
    for line_number, line in enumerate(target_lines, start=1)
    if (match := marker_pattern.fullmatch(line))
]
expected_marker_ids = [f"d90.penn.v1.ch03.seg{order:04d}" for order in range(1, 9)]
if [item[1] for item in markers] != expected_marker_ids:
    raise ValueError("target segment marker closure/order differs")

segment_records: dict[int, dict[str, Any]] = {}
for index, (order, source_start, source_end, source_label, target_label, concept_ids) in enumerate(SEGMENT_SPECS):
    marker_line, record_id = markers[index]
    target_start = marker_line + 1
    target_end = len(target_lines) if index == len(markers) - 1 else markers[index + 1][0] - 2
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, source_start, source_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, target_start, target_end)
    segment = common("segment", record_id, "current")
    segment.update(
        {
            "unit_id": UNIT_ID,
            "order": order,
            "source_local_id": f"Section3-lines-{source_start}-{source_end}",
            "source_local_label": source_label,
            "target_local_label": target_label,
            "source_edition_id": SOURCE_EDITION_ID,
            "source_language": "en",
            "source_path": SOURCE_PATH,
            "source_locator": f"{SOURCE_PATH}:{source_start}-{source_end}",
            "source_line_start": source_start,
            "source_line_end": source_end,
            "source_bytes": source_bytes,
            "source_content_sha256": source_digest,
            "target_edition_id": TARGET_EDITION_ID,
            "target_language": "id",
            "target_locale": "id-ID",
            "target_path": TARGET_PATH,
            "target_locator": f"{TARGET_PATH}:{target_start}-{target_end}",
            "target_line_start": target_start,
            "target_line_end": target_end,
            "target_bytes": target_bytes,
            "target_content_sha256": target_digest,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "built" if build_pass else "mathematically_reviewed",
            "structural_review_state": "passed" if audit_pass else "provisional_audit_failed_or_pending",
            "mathematical_review_state": "passed" if audit_pass and solver_pass else "provisional_audit_or_solver_pending",
            "language_review_state": "not_recorded",
            "concept_ids": concept_ids,
            "rights_id": TARGET_RIGHTS_ID,
            "evidence_event_ids": [
                "qa.o015.penn-ch03.structure",
                "qa.o015.penn-ch03.formula-delta",
                "qa.o015.penn-ch03.corrections",
                "qa.o015.penn-ch03.solver",
                "qa.o015.penn-ch03.build",
            ],
        }
    )
    segment_records[order] = segment
    add(segment)


def find_environment_spans(text: str, environment: str) -> list[tuple[int, int]]:
    begin = rf"\begin{{{environment}}}"
    end = rf"\end{{{environment}}}"
    starts: list[int] = []
    spans: list[tuple[int, int]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if begin in line:
            starts.append(number)
        if end in line:
            if not starts:
                raise ValueError(f"unbalanced {environment} end at line {number}")
            spans.append((starts.pop(), number))
    if starts:
        raise ValueError(f"unbalanced {environment} begins at {starts}")
    return spans


source_exercises = find_environment_spans(source_text, "exercise")
target_exercises = find_environment_spans(target_text, "exercise")
if len(source_exercises) != 12 or len(target_exercises) != 12:
    raise ValueError(
        f"exercise closure differs: source={len(source_exercises)}, target={len(target_exercises)}"
    )
exercise_concepts = [
    "concept.penn.quadratic-interpolation",
    "concept.penn.maximum-bracketing",
    "concept.penn.maximum-bracketing",
    "concept.penn.dichotomous-search",
    "concept.penn.dichotomous-search",
    "concept.penn.golden-section-search",
    "concept.penn.bisection-search",
    "concept.penn.strong-concavity-distance-bound",
    "concept.penn.bisection-search",
    "concept.penn.one-dimensional-newton",
    "concept.penn.one-dimensional-newton",
    "concept.penn.newton-quadratic-convergence",
]
for order, ((source_start, source_end), (target_start, target_end), concept_id) in enumerate(
    zip(source_exercises, target_exercises, exercise_concepts), start=1
):
    segment_order = next(
        segment_order
        for segment_order, start, end, *_ in SEGMENT_SPECS
        if start <= source_start <= end
    )
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, source_start, source_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, target_start, target_end)
    surface = common(
        "learning_surface", f"surface.penn.v1.ch03.exercise{order:02d}", "present"
    )
    surface.update(
        {
            "unit_id": UNIT_ID,
            "surface_type": "exercise_prompt",
            "presence": "present",
            "order": order,
            "source_local_id": f"exercise{order:02d}",
            "source_local_label": f"Source-order exercise {order}",
            "target_local_label": f"Latihan urutan sumber {order}",
            "related_segment_ids": [f"d90.penn.v1.ch03.seg{segment_order:04d}"],
            "concept_id": concept_id,
            "source_path": SOURCE_PATH,
            "source_line_start": source_start,
            "source_line_end": source_end,
            "source_locator": f"{SOURCE_PATH}:{source_start}-{source_end}",
            "source_bytes": source_bytes,
            "source_content_sha256": source_digest,
            "target_path": TARGET_PATH,
            "target_line_start": target_start,
            "target_line_end": target_end,
            "target_locator": f"{TARGET_PATH}:{target_start}-{target_end}",
            "target_bytes": target_bytes,
            "target_content_sha256": target_digest,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "built",
            "rights_id": TARGET_RIGHTS_ID,
            "hint_state": "absent_in_source",
            "answer_state": "absent_in_source",
            "solution_state": "absent_in_source_and_target",
        }
    )
    add(surface)

for order, (record_id, source_start, source_end, target_start, target_end, disposition, concept_id, label) in enumerate(ALGORITHM_SPECS, start=1):
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, source_start, source_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, target_start, target_end)
    segment_order = next(
        segment_order
        for segment_order, start, end, *_ in SEGMENT_SPECS
        if start <= source_start <= end
    )
    surface = common("learning_surface", record_id, "present")
    surface.update(
        {
            "unit_id": UNIT_ID,
            "surface_type": "algorithm_pseudocode",
            "presence": "present",
            "order": order,
            "source_local_id": f"algorithm-surface-{order:02d}",
            "source_local_label": label,
            "target_local_label": label,
            "related_segment_ids": [f"d90.penn.v1.ch03.seg{segment_order:04d}"],
            "concept_id": concept_id,
            "source_path": SOURCE_PATH,
            "source_line_start": source_start,
            "source_line_end": source_end,
            "source_locator": f"{SOURCE_PATH}:{source_start}-{source_end}",
            "source_bytes": source_bytes,
            "source_content_sha256": source_digest,
            "target_path": TARGET_PATH,
            "target_line_start": target_start,
            "target_line_end": target_end,
            "target_locator": f"{TARGET_PATH}:{target_start}-{target_end}",
            "target_bytes": target_bytes,
            "target_content_sha256": target_digest,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "translation_state": "built",
            "rights_id": TARGET_RIGHTS_ID if order == 1 else "rights.o015-penn-ch03-bridges",
            "disposition": disposition,
            "excluded_source_component_rights_id": None if order == 1 else "rights.o015-penn-ch03-maple-excluded",
        }
    )
    add(surface)

# Exact source/target assets.
for record_id, filename, concept_id, segment_order, description in ASSET_SPECS:
    source_relative = f"authority/penn-state/source/ClassNotes/Figures/{filename}"
    target_relative = f"source/id-ID/figures/{filename}"
    source_bytes, source_digest = file_info(source_relative)
    target_bytes, target_digest = file_info(target_relative)
    if (source_bytes, source_digest) != (target_bytes, target_digest):
        raise ValueError(f"Penn figure is not byte-identical: {filename}")
    asset_record = common("asset", record_id, "current")
    asset_record.update(
        {
            "asset_kind": "vector_pdf_figure",
            "source_edition_id": SOURCE_EDITION_ID,
            "target_edition_id": TARGET_EDITION_ID,
            "source_path": source_relative,
            "source_bytes": source_bytes,
            "source_sha256": source_digest,
            "target_path": target_relative,
            "target_bytes": target_bytes,
            "target_sha256": target_digest,
            "rights_id": "rights.o015-penn-ch03-figures",
            "related_segment_ids": [f"d90.penn.v1.ch03.seg{segment_order:04d}"],
            "concept_id": concept_id,
            "adaptation": "byte-identical source-archive copy; Indonesian caption remains in the translated TeX",
            "accessibility_description": description,
        }
    )
    add(asset_record)

# Proposed correction records.  They remain proposal-bound until root admission.
for event in proposal_records:
    event_id = event["event_id"]
    matches = [
        (int(start), int(end))
        for start, end in re.findall(r"(\d+)-(\d+)", event.get("source", ""))
    ]
    if event_id == "O015-PENN-ADV-0013":
        # The ledger correctly cites the five external output files rather than
        # pretending they are Section3 text.  These are their exact five input
        # call sites in the frozen chapter.
        matches = [(144, 146), (220, 220), (307, 307), (402, 402)]
    if not matches:
        raise ValueError(f"{event_id}: no Section3 source locator")
    source_start = min(item[0] for item in matches)
    source_end = max(item[1] for item in matches)
    affected = [
        f"d90.penn.v1.ch03.seg{order:04d}"
        for order, start, end, *_ in SEGMENT_SPECS
        if not (source_end < start or source_start > end)
    ]
    correction = common(
        "correction",
        "correction." + event_id.lower(),
        "applied_in_provisional_candidate",
    )
    correction.update(
        {
            "source_event_id": event_id,
            "source_edition_id": SOURCE_EDITION_ID,
            "affected_unit_ids": [UNIT_ID],
            "affected_segment_ids": affected,
            "source_path": SOURCE_PATH,
            "source_line_start": source_start,
            "source_line_end": source_end,
            "source_locator": event["source"],
            "surface": event["surface"],
            "source_issue": event["source_issue"],
            "target_action": event["target_action"],
            "correction_class": event["class"],
            "disposition": "applied_in_candidate",
            "shared_ledger_state": "integrated" if ledger_integrated else "proposed_not_integrated",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.o015.adverse-ledger",
            "proposal_artifact_id": "artifact.penn.proposed-ledger-ch03",
        }
    )
    add(correction)

# Artifacts.  Audit and solver outputs are never treated as authority for source
# text; they are reproducible evidence linked to the frozen inputs.
artifact_records = [
    artifact("artifact.penn.authority-archive", "source_archive", "authority/penn-state/Math555_SRC.zip", source_edition_id=SOURCE_EDITION_ID),
    artifact("artifact.penn.authority-pdf", "authority_pdf_witness", "authority/penn-state/Math555.pdf", source_edition_id=SOURCE_EDITION_ID, pages=187),
    artifact("artifact.penn.source-ch03", "source_tex", SOURCE_PATH, source_edition_id=SOURCE_EDITION_ID),
    artifact("artifact.penn.target-ch03", "target_tex", TARGET_PATH, source_artifact_id="artifact.penn.source-ch03", target_edition_id=TARGET_EDITION_ID, rights_id=TARGET_RIGHTS_ID),
    artifact("artifact.penn.target-wrapper-ch03", "reader_wrapper_tex", WRAPPER_PATH, target_edition_id=TARGET_EDITION_ID, rights_id=TARGET_RIGHTS_ID, input_artifact_ids=["artifact.penn.target-ch03", "artifact.penn.local-bibliography-ch03"]),
    artifact("artifact.penn.local-bibliography-ch03", "bounded_bibliography_excerpt", BIB_PATH, source_artifact_id="artifact.penn.authority-archive", target_edition_id=TARGET_EDITION_ID, rights_id="rights.o015-penn-ch03-bibliography"),
    artifact("artifact.penn.target-pdf-ch03", "reader_pdf", PDF_PATH, target_edition_id=TARGET_EDITION_ID, rights_id=TARGET_RIGHTS_ID, pages=pdf_pages, build_event_id="qa.o015.penn-ch03.build", accessibility="searchable id-ID PDF; untagged; embedded source-figure fonts include resources without ToUnicode", input_artifact_ids=["artifact.penn.target-wrapper-ch03", "artifact.penn.target-ch03", "artifact.penn.local-bibliography-ch03"]),
    artifact("artifact.penn.build-log-ch03", "build_log", LOG_PATH, target_edition_id=TARGET_EDITION_ID, source_artifact_id="artifact.penn.target-wrapper-ch03"),
    artifact("artifact.penn.target-text-ch03", "qa_extract", TEXT_PATH, target_edition_id=TARGET_EDITION_ID, source_artifact_id="artifact.penn.target-pdf-ch03"),
    artifact("artifact.penn.audit-source-ch03", "qa_source", AUDIT_SOURCE_PATH, rights_id="rights.o015-penn-ch03-audit", toolchain="Python 3 standard library"),
    artifact("artifact.penn.structure-report-ch03", "qa_report", STRUCTURE_REPORT_PATH, source_artifact_id="artifact.penn.audit-source-ch03"),
    artifact("artifact.penn.formula-manifest-ch03", "qa_report", FORMULA_MANIFEST_PATH, source_artifact_id="artifact.penn.audit-source-ch03"),
    artifact("artifact.penn.proposed-ledger-ch03", "proposed_correction_ledger", PROPOSED_LEDGER_PATH, source_artifact_id="artifact.penn.source-ch03"),
    artifact("artifact.o015.backend-generator-penn-ch03", "qa_source", "qa/extend_backend_penn_ch03.py", toolchain="Python 3 standard library"),
    artifact("artifact.o015.backend-validator-penn-ch03", "backend_validator", "qa/validate_backend_penn_ch03.py", toolchain="Python 3 standard library"),
]
if solver_available:
    artifact_records.extend(
        [
            artifact("artifact.penn.solver-validator-ch03", "qa_source", SOLVER_SOURCE_PATH, rights_id="rights.o015-penn-ch03-audit", toolchain="Python / NumPy / SciPy"),
            artifact("artifact.penn.solver-results-ch03", "qa_report", SOLVER_RESULTS_PATH, source_artifact_id="artifact.penn.solver-validator-ch03"),
        ]
    )
for record in artifact_records:
    add(record)

# QA events expose the still-open gates instead of silently promoting the unit.
qa_specs: list[dict[str, Any]] = [
    {
        "id": "qa.o015.penn-ch03.source-freeze",
        "status": "pass",
        "event_type": "source",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.source-ch03", "artifact.penn.authority-archive", "artifact.penn.authority-pdf"],
        "authority_id": "o015-penn-math555-v1.0-source",
        "source_sha256": FROZEN_FILES[SOURCE_PATH][1],
        "edition_distinction": "editable v1.0 is the text authority; public PDF v1.0.1 is a correction witness",
    },
    {
        "id": "qa.o015.penn-ch03.structure",
        "status": "pass" if audit_pass else "fail",
        "event_type": "topology",
        "result": "pass" if audit_pass else "fail",
        "witness_artifact_ids": ["artifact.penn.structure-report-ch03"],
        "audit_admission_status": structure_report.get("admission_status"),
        "failed_checks": audit_failures,
        "segment_count": 8,
        "source_lines": 608,
        "target_lines": 646,
    },
    {
        "id": "qa.o015.penn-ch03.formula-delta",
        "status": "pass" if audit_pass else "provisional",
        "event_type": "mathematics",
        "result": "pass" if audit_pass else "provisional",
        "witness_artifact_ids": ["artifact.penn.formula-manifest-ch03", "artifact.penn.proposed-ledger-ch03"],
        "formula_manifest_schema": formula_manifest.get("schema"),
        "correction_event_count": len(proposal_records),
    },
    {
        "id": "qa.o015.penn-ch03.corrections",
        "status": "pass_proposed" if not ledger_integrated else "pass",
        "event_type": "correction_ledger",
        "result": "pass_proposed" if not ledger_integrated else "pass",
        "witness_artifact_ids": ["artifact.penn.proposed-ledger-ch03", "artifact.o015.adverse-ledger"],
        "event_ids": proposal_ids,
        "shared_ledger_state": "integrated" if ledger_integrated else "proposed_not_integrated",
        "collision_count": 0,
    },
    {
        "id": "qa.o015.penn-ch03.algorithms",
        "status": "pass",
        "event_type": "code_surface",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.target-ch03"],
        "source_algorithm_surface_count": 7,
        "excluded_maple_listing_count": 6,
        "independent_replacement_count": 6,
        "retained_legacy_dependency_count": 0,
    },
    {
        "id": "qa.o015.penn-ch03.exercises",
        "status": "pass",
        "event_type": "learning_surface",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.structure-report-ch03"],
        "exercise_count": 12,
        "hint_count": 0,
        "answer_count": 0,
        "solution_count": 0,
    },
    {
        "id": "qa.o015.penn-ch03.solver",
        "status": "pass" if solver_pass else "not_recorded",
        "event_type": "computation",
        "result": "pass" if solver_pass else "not_recorded",
        "witness_artifact_ids": ["artifact.penn.solver-results-ch03", "artifact.penn.solver-validator-ch03"] if solver_available else [],
        "checks": solver_results.get("checks", []),
        "gap": None if solver_available else "Independent open-solver result is not yet present.",
    },
    {
        "id": "qa.o015.penn-ch03.build",
        "status": "pass" if build_pass else "fail",
        "event_type": "build",
        "result": "pass" if build_pass else "fail",
        "witness_artifact_ids": ["artifact.penn.target-pdf-ch03", "artifact.penn.build-log-ch03"],
        "pages": pdf_pages,
        "page_size": "A4",
        "errors": build_blockers,
        "deterministic_rebuild": "byte-identical per canonical/repro build evidence",
    },
    {
        "id": "qa.o015.penn-ch03.visual",
        "status": "not_recorded",
        "event_type": "visual",
        "result": "not_recorded",
        "witness_artifact_ids": ["artifact.penn.target-pdf-ch03"],
        "gap": "No standalone machine-readable visual-QA receipt is in the Penn candidate closure.",
    },
    {
        "id": "qa.o015.penn-ch03.accessibility",
        "status": "pass_with_limitation",
        "event_type": "accessibility",
        "result": "pass_with_limitation",
        "witness_artifact_ids": ["artifact.penn.target-pdf-ch03", "artifact.penn.target-text-ch03"],
        "checks": ["PDF language metadata is id-ID", "PDF is unencrypted and searchable", "all 20 pages expose text", "exact text extraction retained"],
        "limitations": ["PDF is untagged", "embedded source-figure fonts include resources without ToUnicode"],
    },
    {
        "id": "qa.o015.penn-ch03.math-rereview",
        "status": "pass" if audit_pass else "fail",
        "event_type": "mathematics",
        "result": "pass" if audit_pass else "fail",
        "witness_artifact_ids": ["artifact.penn.target-ch03", "artifact.penn.structure-report-ch03", "artifact.penn.formula-manifest-ch03"],
        "failed_checks": audit_failures,
        "scope": "Independent source/target/proposal rereview of all repaired Chapter 3 surfaces.",
    },
    {
        "id": "qa.o015.penn-ch03.language",
        "status": "not_recorded",
        "event_type": "language",
        "result": "not_recorded",
        "witness_artifact_ids": [],
        "gap": "No independent Indonesian language review is recorded.",
    },
]
for spec in qa_specs:
    qa = common("qa_event", spec.pop("id"), spec.pop("status"))
    qa.update({"unit_id": UNIT_ID, **spec})
    add(qa)

# Relations make the cross-resource sequence and every reader surface explicit.
relation_specs: list[tuple[str, str, str, str, str]] = [
    ("relation.penn.course-contains-work", "contains", "course.d90.advanced-optimization-convex-analysis", ROOT_UNIT_ID, "Penn is the smooth numerical-optimization donor."),
    ("relation.penn.work-contains-ch03", "contains", ROOT_UNIT_ID, UNIT_ID, "Complete source Section3.tex."),
    ("relation.penn.habring-ch09-precedes-ch03", "precedes", "unit.habring.v1.ch09", UNIT_ID, "Production cursor crosses from the admitted Habring module to the Penn donor."),
    ("relation.penn.ch03-depends-on-gradient", "depends-on", UNIT_ID, "concept.gradient", "Gradient and differentiability are prerequisites."),
]
for order in range(1, 9):
    relation_specs.append((f"relation.penn.ch03-contains-seg{order:04d}", "contains", UNIT_ID, f"d90.penn.v1.ch03.seg{order:04d}", "Ordered contiguous translation segment."))
for order, *_, concept_ids in SEGMENT_SPECS:
    for concept_id in concept_ids:
        suffix = concept_id.removeprefix("concept.penn.")
        relation_specs.append((f"relation.penn.seg{order:04d}-defines-{suffix}", "defines", f"d90.penn.v1.ch03.seg{order:04d}", concept_id, "Primary source-linked concept surface."))
for order, concept_id in enumerate(exercise_concepts, start=1):
    relation_specs.append((f"relation.penn.exercise{order:02d}-exercises-{concept_id.removeprefix('concept.penn.')}", "exercises", f"surface.penn.v1.ch03.exercise{order:02d}", concept_id, "Source-order exercise prompt."))
for record_id, *_, concept_id, label in ALGORITHM_SPECS:
    relation_specs.append((f"relation.penn.{record_id.rsplit('.', 1)[-1]}-illustrates-{concept_id.removeprefix('concept.penn.')}", "illustrates", record_id, concept_id, label))
for asset_id, _, concept_id, _, description in ASSET_SPECS:
    relation_specs.append((f"relation.penn.{asset_id.rsplit('.', 1)[-1]}-illustrates-{concept_id.removeprefix('concept.penn.')}", "illustrates", asset_id, concept_id, description))
relation_specs.extend(
    [
        ("relation.penn.target-translates-source", "translates", "artifact.penn.target-ch03", "artifact.penn.source-ch03", "Complete contiguous id-ID translation candidate."),
        ("relation.penn.wrapper-contains-target", "contains", "artifact.penn.target-wrapper-ch03", "artifact.penn.target-ch03", "Standalone licensed reader wrapper."),
        ("relation.penn.pdf-depends-on-wrapper", "depends-on", "artifact.penn.target-pdf-ch03", "artifact.penn.target-wrapper-ch03", "Reproducible reader build input."),
        ("relation.penn.pdf-depends-on-bibliography", "depends-on", "artifact.penn.target-pdf-ch03", "artifact.penn.local-bibliography-ch03", "Five-entry bounded bibliography excerpt."),
        ("relation.penn.text-adapts-pdf", "adapts", "artifact.penn.target-text-ch03", "artifact.penn.target-pdf-ch03", "Searchability and accessibility witness."),
        ("relation.penn.bibliography-adapts-archive", "adapts", "artifact.penn.local-bibliography-ch03", "artifact.penn.authority-archive", "Exact five-entry excerpt from bundled Math555.bbl."),
        ("relation.penn.structure-depends-on-audit", "depends-on", "artifact.penn.structure-report-ch03", "artifact.penn.audit-source-ch03", "Deterministic structural audit output."),
        ("relation.penn.formula-depends-on-audit", "depends-on", "artifact.penn.formula-manifest-ch03", "artifact.penn.audit-source-ch03", "Deterministic formula-delta output."),
    ]
)
if solver_available:
    relation_specs.append(("relation.penn.solver-results-depend-on-validator", "depends-on", "artifact.penn.solver-results-ch03", "artifact.penn.solver-validator-ch03", "Deterministic open-solver output."))

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

# The immutable baseline is compared again after construction.  No baseline
# artifact is refreshed, even if a live control file changes concurrently.
final_by_id = {record["id"]: canonical_json(record) for record in records}
missing_baseline_ids = sorted(baseline_ids - set(final_by_id))
changed_baseline_ids = sorted(
    record_id
    for record_id in baseline_ids
    if final_by_id.get(record_id) != baseline_by_id[record_id]
)
if missing_baseline_ids or changed_baseline_ids:
    raise ValueError(
        "Penn extension changed immutable Habring baseline: "
        f"missing={missing_baseline_ids}, changed={changed_baseline_ids}"
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

added_records = [record for record in records if record["id"] in generated_ids]
report = {
    "admission_state": admission_state,
    "audit_pass": audit_pass,
    "audit_failures": audit_failures,
    "baseline_comparison": {
        "baseline_record_count": len(baseline_ids),
        "baseline_record_set_sha256": record_set_sha256(
            [record for record in records if record["id"] in baseline_ids]
        ),
        "changed_record_ids": changed_baseline_ids,
        "enumerated_live_artifact_refresh_ids": baseline_refreshed_ids,
        "incoming_record_set_sha256": incoming_baseline_sha256,
        "missing_record_ids": missing_baseline_ids,
        "result": "pass",
    },
    "csv": {
        "bytes": file_info("backend/records.csv")[0],
        "sha256": file_info("backend/records.csv")[1],
    },
    "entity_counts": dict(sorted(Counter(record["entity_type"] for record in records).items())),
    "jsonl": {
        "bytes": file_info("backend/records.jsonl")[0],
        "sha256": file_info("backend/records.jsonl")[1],
    },
    "ledger_integrated": ledger_integrated,
    "penn_added_entity_counts": dict(sorted(Counter(record["entity_type"] for record in added_records).items())),
    "penn_added_record_count": len(added_records),
    "penn_record_set_sha256": record_set_sha256(added_records),
    "record_count": len(records),
    "solver_available": solver_available,
    "solver_pass": solver_pass,
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
