#!/usr/bin/env python3
"""Deterministically admit Penn MATH 555 Chapter 4 into the O015 backend.

The pre-existing 973-record backend is immutable except for three explicitly
enumerated control-artifact bindings whose live files were expanded by the
already completed Chapter 4 control admission. The script proves that exact
baseline, refreshes only those three byte/hash pairs, and reconstructs its own
Chapter 4 closure deterministically on every run.
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
COMPONENT_RIGHTS_PATH = ROOT / "00_control" / "COMPONENT_RIGHTS.csv"
COVERAGE_OVERLAP_PATH = ROOT / "00_control" / "COVERAGE_OVERLAP.md"

RECORDED_AT = "2026-08-22T20:00:00Z"
WORKFLOW = "o015-penn-ch04-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 973
ORIGINAL_BASELINE_RECORD_SET_SHA256 = (
    "d0143e1352db9fc87b8bf5b842f34f30e682074ff7a91c98c2e83140e090bb5d"
)
PREVIOUS_REFRESHED_BASELINE_RECORD_SET_SHA256 = (
    "5890737b773b0583124a3bd26b82b46d8b149c6addfb14263416bdc0f6271200"
)
REFRESHED_BASELINE_RECORD_SET_SHA256 = (
    "a53d556fe87bab226e120d7df3611b15e38cabb3defb19e850d481dd72058f9c"
)
BASELINE_SEMANTIC_COUNT = 861
BASELINE_SEMANTIC_RECORD_SET_SHA256 = (
    "e20bb942a17185bfcabbc0e0377ce3608697530162664ebe06fba4400ec706a9"
)
BASELINE_IMMUTABLE_ARTIFACT_COUNT = 109
BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256 = (
    "0694bc4785d8712429c783002f0940d61c3832c32de8b8fc5fc436c128ca21e1"
)

REFRESH_SPECS: dict[str, tuple[str, int, str]] = {
    "artifact.o015.adverse-ledger": (
        "00_control/ADVERSE_LEDGER.jsonl",
        83238,
        "333f870c4383532fcf01a390c8b2321fca2e8b54d5ca6fa857d5d028ce65f8c0",
    ),
    "artifact.o015.component-rights": (
        "00_control/COMPONENT_RIGHTS.csv",
        19534,
        "0f1273adbbc71a82186e3f5a1ed0fa2b5d9084c688bdcb01a9dc56095349f80e",
    ),
    "artifact.o015.coverage-overlap": (
        "00_control/COVERAGE_OVERLAP.md",
        5096,
        "6887732e1212829f2466edd3aedc4b363dd8b06f65a10001a8e41e2f7611087b",
    ),
}

SOURCE_PATH = "authority/penn-state/source/ClassNotes/Section4.tex"
TARGET_PATH = "source/id-ID/penn-04-pencarian-garis-hampiran-dan-konvergensi-id.tex"
WRAPPER_PATH = "source/id-ID/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex"
BIB_PATH = "source/id-ID/references-penn-ch04-id.bbl"
PDF_PATH = "output/pdf/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf"
LOG_PATH = "build/penn-unit-04-id/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.log"
TEXT_PATH = "qa/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.txt"
AUDIT_SOURCE_PATH = "qa/audit_penn_ch04_candidate.py"
STRUCTURE_REPORT_PATH = "qa/PENN_CH04_STRUCTURE_REPORT.json"
FORMULA_MANIFEST_PATH = "qa/PENN_CH04_FORMULA_DELTA_MANIFEST.json"
PROPOSED_LEDGER_PATH = "qa/PENN_CH04_PROPOSED_LEDGER.jsonl"
SOLVER_SOURCE_PATH = "qa/validate_penn_ch04_math.py"
SOLVER_RESULTS_PATH = "qa/PENN_CH04_SOLVER_RESULTS.json"
VISUAL_QA_PATH = "qa/PENN_CH04_VISUAL_QA.json"
SOURCE_AUDIT_PATH = "00_control/PENN_CH04_SOURCE_AUDIT.md"

RESOURCE_ID = "resource.penn.math555-nonlinear-programming"
SOURCE_EDITION_ID = "edition.penn.math555.source-v1-0"
TARGET_EDITION_ID = "edition.penn.math555.id-id.v1"
ROOT_UNIT_ID = "unit.penn.v1"
PREVIOUS_UNIT_ID = "unit.penn.v1.ch03"
UNIT_ID = "unit.penn.v1.ch04"
SOURCE_RIGHTS_ID = "rights.o015-penn-ch04-source"
TARGET_RIGHTS_ID = "rights.o015-penn-id-ch04"

EXPECTED_PROPOSAL_IDS = [
    f"O015-PENN-ADV-{number:04d}" for number in range(25, 38)
]

FROZEN_FILES: dict[str, tuple[int, str]] = {
    SOURCE_PATH: (
        34684,
        "76113034709b5914fa920076f2e882ccf30157e78ce5bdf4593a5d39af1886d5",
    ),
    TARGET_PATH: (
        33313,
        "c5c0f09d38454177e61c2a97c9beef07771d5f4f715cc7a4a81a871ff54ced8f",
    ),
    WRAPPER_PATH: (
        8018,
        "b40ac7e4e1ee69afd0f7f82dbfc9042c6df79c1aaf2ccca78ec9e639b2030edc",
    ),
    BIB_PATH: (
        625,
        "037e62878f1a562314a33054da8f4df4e49c029bbad31c2ec75066cd3e1a99f3",
    ),
    PDF_PATH: (
        847350,
        "c0f283aa7d70eba05de6a35c98bc0aa55f3177ab40702bf7eed5de45a7b6ab8a",
    ),
    LOG_PATH: (
        27564,
        "f247633a55e47a6fc002899bc9dbd24128f0949e39cc2954f78164411c301174",
    ),
    TEXT_PATH: (
        26421,
        "3ee30d8a4948910d40d8f61bec87a8e36e29f1934c6000dab1d9a8c96f5e518f",
    ),
    AUDIT_SOURCE_PATH: (
        33499,
        "aec0ca750c3de504f5c6f8b9a95217c1d5cda2111a5a697442caadaae952c256",
    ),
    STRUCTURE_REPORT_PATH: (
        39127,
        "c43e0195fc7da99590efd17b83ace3ca6a5721bc5156e86d2121a877b85e2c0a",
    ),
    FORMULA_MANIFEST_PATH: (
        65651,
        "fe7aa0bbd5cab4ff50cdf855a3bcf3c73f6ad0e007e2ce2033369cf54ed4a65e",
    ),
    PROPOSED_LEDGER_PATH: (
        10055,
        "fa9c5c0b097b7349a959ca6c1c9c797fc0ed2ea61e91148badec62bb239b7bbd",
    ),
    SOLVER_SOURCE_PATH: (
        13339,
        "6f2ebf4a462043d327b5eb8c7e238808b6098aea2c193eab66cfa43794cd4bc4",
    ),
    SOLVER_RESULTS_PATH: (
        5523,
        "44c2b1a2509775e182e38b125f6c25ca49eb2f7e23e68ec2fce6878bf7704dd2",
    ),
    VISUAL_QA_PATH: (
        1808,
        "e700d08476f7aaa018ca31687d2eea2e8a50729599f760d300dd5b6f89211e70",
    ),
    SOURCE_AUDIT_PATH: (
        10296,
        "c1b491d742ac61347a24367409e4c95a6ed222de6043688ce5b9cb1fc5ce84a0",
    ),
    "authority/penn-state/Math555_SRC.zip": (
        23909024,
        "1958af9417aa7cd057f321c3c6f71a8c02349fb1d32da75f6bad05eb66286a0e",
    ),
    "authority/penn-state/Math555.pdf": (
        4776722,
        "f7b99401af875333f3becb591eebf61fac81280768537c20b8a1264d578cb4ff",
    ),
}

FIGURE_IDENTITIES: dict[str, tuple[int, str]] = {
    "ThreeDCos.pdf": (
        234150,
        "e14dc949d3fd7cd7d0593f0352567aa9ac6e66423886113929df9c7feb2eace5",
    ),
    "WolfePhiOfT.pdf": (
        16923,
        "221447efe0da804b341570bf3877c842199dd6052b7029eb70cf2edf1aab9a09",
    ),
    "WolfeConditionsIllustrated.pdf": (
        163565,
        "b3d2c7c62a79e6bf74ec62089afc773f631f1c62d67e2f8bfd58fb4a078796ec",
    ),
    "ConvergenceFailure.pdf": (
        11302,
        "fc5f89515414dcbc704e718e6de62b0bb15785b645bd669c98254dd058a16836",
    ),
    "GradientAscentOut.pdf": (
        110472,
        "31cdba8ed1818564289fba9c2c279b48cd0bddc347097261ae8df572953eecc4",
    ),
}
for _filename, _identity in FIGURE_IDENTITIES.items():
    FROZEN_FILES[
        f"authority/penn-state/source/ClassNotes/Figures/{_filename}"
    ] = _identity
    FROZEN_FILES[f"source/id-ID/figures/{_filename}"] = _identity


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_set_sha256(record_set: list[dict[str, Any]]) -> str:
    payload = "".join(
        canonical_json(record) + "\n"
        for record in sorted(record_set, key=lambda item: item["id"])
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
    ("concept.penn.armijo-rule", "Armijo sufficient-increase rule", ["concept.penn.ascent-direction"], "smooth numerical optimization"),
    ("concept.penn.curvature-condition", "ascent-form curvature condition", ["concept.penn.ascent-direction"], "smooth numerical optimization"),
    ("concept.penn.wolfe-conditions", "Wolfe conditions for ascent", ["concept.penn.armijo-rule", "concept.penn.curvature-condition"], "smooth numerical optimization"),
    ("concept.penn.backtracking-line-search", "Armijo backtracking line search", ["concept.penn.armijo-rule"], "smooth numerical optimization"),
    ("concept.penn.gradient-related-directions", "gradient-related direction sequence", ["concept.penn.ascent-direction"], "smooth numerical optimization"),
    ("concept.penn.line-search-stationarity", "stationarity under safeguarded line search", ["concept.penn.backtracking-line-search", "concept.penn.gradient-related-directions"], "smooth numerical optimization"),
    ("concept.penn.scaled-gradient-direction", "uniformly scaled gradient direction", ["concept.penn.gradient-related-directions"], "smooth numerical optimization"),
    ("concept.penn.fixed-step-convergence-failure", "fixed-step gradient-ascent convergence failure", ["concept.penn.gradient-ascent"], "smooth numerical optimization"),
    ("concept.penn.capture-theorem", "capture theorem for convergent ascent methods", ["concept.penn.line-search-stationarity"], "smooth numerical optimization"),
    ("concept.penn.kantorovich-inequality", "Kantorovich inequality", ["concept.strong-convexity"], "numerical linear algebra"),
    ("concept.penn.exact-gradient-ascent-rate", "exact-gradient-ascent convergence rate", ["concept.penn.gradient-ascent", "concept.penn.kantorovich-inequality"], "smooth numerical optimization"),
    ("concept.penn.spectral-conditioning", "spectral conditioning and convergence factor", ["concept.penn.kantorovich-inequality"], "numerical linear algebra"),
    ("concept.penn.eventual-unit-step", "eventual acceptance of unit steps", ["concept.penn.backtracking-line-search"], "smooth numerical optimization"),
    ("concept.penn.superlinear-convergence", "superlinear convergence of basic ascent iterations", ["concept.penn.eventual-unit-step", "concept.penn.convergence-order"], "numerical analysis"),
]

TERM_SPECS: list[tuple[str, str, str, str, int, list[str]]] = [
    ("term.penn.armijo-rule", "concept.penn.armijo-rule", "Armijo rule", "aturan Armijo", 1, []),
    ("term.penn.curvature-condition", "concept.penn.curvature-condition", "curvature condition", "syarat kelengkungan", 1, []),
    ("term.penn.wolfe-conditions", "concept.penn.wolfe-conditions", "Wolfe conditions", "syarat Wolfe", 1, []),
    ("term.penn.backtracking-line-search", "concept.penn.backtracking-line-search", "backtracking line search", "pencarian garis pelacakan mundur", 2, []),
    ("term.penn.gradient-related-directions", "concept.penn.gradient-related-directions", "gradient related", "berkaitan dengan gradien", 3, []),
    ("term.penn.line-search-stationarity", "concept.penn.line-search-stationarity", "stationary point", "titik stasioner", 3, []),
    ("term.penn.scaled-gradient-direction", "concept.penn.scaled-gradient-direction", "scaled gradient direction", "arah gradien berskala", 3, []),
    ("term.penn.fixed-step-convergence-failure", "concept.penn.fixed-step-convergence-failure", "convergence failure", "kegagalan konvergensi", 4, []),
    ("term.penn.capture-theorem", "concept.penn.capture-theorem", "capture theorem", "teorema penangkapan", 4, []),
    ("term.penn.kantorovich-inequality", "concept.penn.kantorovich-inequality", "Kantorovich inequality", "ketaksamaan Kantorovich", 5, []),
    ("term.penn.exact-gradient-ascent-rate", "concept.penn.exact-gradient-ascent-rate", "exact gradient-ascent rate", "laju pendakian gradien eksak", 5, []),
    ("term.penn.spectral-conditioning", "concept.penn.spectral-conditioning", "spectral condition number", "bilangan kondisi spektral", 5, []),
    ("term.penn.eventual-unit-step", "concept.penn.eventual-unit-step", "eventual unit step", "langkah satuan pada akhirnya", 7, []),
    ("term.penn.superlinear-convergence", "concept.penn.superlinear-convergence", "superlinear convergence", "konvergensi superlinear", 7, []),
]

SEGMENT_SPECS: list[tuple[int, int, int, str, str, list[str]]] = [
    (1, 1, 74, "Wolfe conditions and radial example", "Syarat Wolfe dan contoh radial", ["concept.penn.armijo-rule", "concept.penn.curvature-condition", "concept.penn.wolfe-conditions"]),
    (2, 75, 124, "Existence of Wolfe steps and Armijo backtracking", "Keberadaan langkah Wolfe dan pelacakan mundur Armijo", ["concept.penn.wolfe-conditions", "concept.penn.backtracking-line-search"]),
    (3, 125, 206, "Gradient-related directions and stationarity", "Arah berkaitan dengan gradien dan kestasioneran", ["concept.penn.gradient-related-directions", "concept.penn.line-search-stationarity", "concept.penn.scaled-gradient-direction"]),
    (4, 207, 243, "Convergence failure and capture theorem", "Kegagalan konvergensi dan teorema penangkapan", ["concept.penn.fixed-step-convergence-failure", "concept.penn.capture-theorem"]),
    (5, 244, 331, "Exact-gradient rate and Kantorovich inequality", "Laju gradien eksak dan ketaksamaan Kantorovich", ["concept.penn.kantorovich-inequality", "concept.penn.exact-gradient-ascent-rate", "concept.penn.spectral-conditioning"]),
    (6, 332, 363, "Gradient-ascent implementation and quadratic example", "Implementasi pendakian gradien dan contoh kuadratik", ["concept.penn.exact-gradient-ascent-rate", "concept.penn.spectral-conditioning"]),
    (7, 364, 469, "Eventual unit steps and superlinear convergence", "Langkah satuan pada akhirnya dan konvergensi superlinear", ["concept.penn.eventual-unit-step", "concept.penn.superlinear-convergence"]),
]

SEGMENT_DEFINITION_SPECS: list[tuple[int, str]] = [
    (1, "concept.penn.armijo-rule"),
    (1, "concept.penn.curvature-condition"),
    (1, "concept.penn.wolfe-conditions"),
    (2, "concept.penn.backtracking-line-search"),
    (3, "concept.penn.gradient-related-directions"),
    (3, "concept.penn.line-search-stationarity"),
    (3, "concept.penn.scaled-gradient-direction"),
    (4, "concept.penn.fixed-step-convergence-failure"),
    (4, "concept.penn.capture-theorem"),
    (5, "concept.penn.kantorovich-inequality"),
    (5, "concept.penn.exact-gradient-ascent-rate"),
    (5, "concept.penn.spectral-conditioning"),
    (7, "concept.penn.eventual-unit-step"),
    (7, "concept.penn.superlinear-convergence"),
]

EXERCISE_CONCEPTS = [
    "concept.penn.line-search-stationarity",
    "concept.penn.scaled-gradient-direction",
    "concept.penn.kantorovich-inequality",
    "concept.penn.backtracking-line-search",
]

ALGORITHM_SPECS: list[tuple[str, str, str]] = [
    ("surface.penn.v1.ch04.bridge01", "concept.penn.backtracking-line-search", "Independent Armijo backtracking pseudocode"),
    ("surface.penn.v1.ch04.bridge02", "concept.penn.gradient-ascent", "Independent gradient-ascent pseudocode, part 1"),
    ("surface.penn.v1.ch04.bridge03", "concept.penn.gradient-ascent", "Independent gradient-ascent pseudocode, part 2"),
]

ASSET_SPECS: list[tuple[str, str, str, int, str]] = [
    ("asset.penn.v1.ch04.three-d-cos", "ThreeDCos.pdf", "concept.penn.wolfe-conditions", 1, "Three-dimensional radial objective with its maximum at the origin."),
    ("asset.penn.v1.ch04.wolfe-phi", "WolfePhiOfT.pdf", "concept.penn.wolfe-conditions", 1, "One-dimensional line restriction approaching and passing a maximum."),
    ("asset.penn.v1.ch04.wolfe-regions", "WolfeConditionsIllustrated.pdf", "concept.penn.wolfe-conditions", 1, "Intersection of Armijo and curvature acceptance regions."),
    ("asset.penn.v1.ch04.convergence-failure", "ConvergenceFailure.pdf", "concept.penn.fixed-step-convergence-failure", 4, "Alternating fixed-step ascent iterates that do not approach stationarity."),
    ("asset.penn.v1.ch04.gradient-ascent-output", "GradientAscentOut.pdf", "concept.penn.spectral-conditioning", 6, "Zig-zagging exact-gradient-ascent path on an ill-conditioned quadratic."),
]

GENERATED_CONCEPT_IDS = {item[0] for item in CONCEPT_SPECS}
GENERATED_TERM_IDS = {item[0] for item in TERM_SPECS}
GENERATED_EXACT_IDS = {
    UNIT_ID,
    SOURCE_RIGHTS_ID,
    TARGET_RIGHTS_ID,
    "rights.o015-penn-ch04-wrapper",
    "rights.o015-penn-ch04-figures",
    "rights.o015-penn-ch04-bibliography",
    "rights.o015-penn-ch04-bridges",
    "rights.o015-penn-ch04-maple-excluded",
    "rights.o015-penn-ch04-audit",
    "rights.o015-penn-ch04-solver",
    "rights.o015-penn-ch04-visual",
    "artifact.o015.backend-generator-penn-ch04",
    "artifact.o015.backend-validator-penn-ch04",
}


def is_generated(record: dict[str, Any]) -> bool:
    record_id = record.get("id", "")
    if record.get("responsible_workflow") == WORKFLOW:
        return True
    if record_id in GENERATED_CONCEPT_IDS | GENERATED_TERM_IDS | GENERATED_EXACT_IDS:
        return True
    return record_id.startswith(
        (
            "d90.penn.v1.ch04.",
            "surface.penn.v1.ch04.",
            "asset.penn.v1.ch04.",
            "qa.o015.penn-ch04.",
            "relation.penn.ch04.",
        )
    ) or record_id in {
        f"correction.o015-penn-adv-{number:04d}" for number in range(25, 38)
    } or (
        record_id.startswith("artifact.penn.") and record_id.endswith("-ch04")
    )


for relative, expected in FROZEN_FILES.items():
    actual = file_info(relative)
    if actual != expected:
        raise ValueError(
            f"frozen Penn Chapter 4 artifact differs: {relative}: "
            f"expected {expected}, found {actual}"
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
        f"pre-Chapter-4 baseline has {len(records)} records, "
        f"expected {BASELINE_RECORD_COUNT}"
    )

incoming_baseline_sha256 = record_set_sha256(records)
if incoming_baseline_sha256 not in {
    ORIGINAL_BASELINE_RECORD_SET_SHA256,
    PREVIOUS_REFRESHED_BASELINE_RECORD_SET_SHA256,
    REFRESHED_BASELINE_RECORD_SET_SHA256,
}:
    raise ValueError("pre-Chapter-4 baseline differs beyond the enumerated refresh")

baseline_semantic = [
    record for record in records if record.get("entity_type") != "artifact"
]
if (
    len(baseline_semantic) != BASELINE_SEMANTIC_COUNT
    or record_set_sha256(baseline_semantic)
    != BASELINE_SEMANTIC_RECORD_SET_SHA256
):
    raise ValueError("immutable 861-record semantic baseline differs")

refresh_ids = set(REFRESH_SPECS)
baseline_immutable_artifacts = [
    record
    for record in records
    if record.get("entity_type") == "artifact"
    and record.get("id") not in refresh_ids
]
if (
    len(baseline_immutable_artifacts) != BASELINE_IMMUTABLE_ARTIFACT_COUNT
    or record_set_sha256(baseline_immutable_artifacts)
    != BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256
):
    raise ValueError("immutable 109-record baseline artifact set differs")

baseline_by_record_id = {record["id"]: record for record in records}
for record_id, (path, size, digest) in REFRESH_SPECS.items():
    record = baseline_by_record_id.get(record_id)
    if record is None or record.get("entity_type") != "artifact":
        raise ValueError(f"baseline lacks refreshable artifact {record_id}")
    if record.get("path") != path:
        raise ValueError(f"{record_id}: protected path binding differs")
    if file_info(path) != (size, digest):
        raise ValueError(f"{record_id}: live control identity differs")

live_artifact_mismatch_ids: list[str] = []
for record in records:
    if record.get("entity_type") != "artifact":
        continue
    path = ROOT / record["path"]
    if not path.is_file():
        raise ValueError(f"baseline artifact path is missing: {record['id']}: {path}")
    actual = file_info(record["path"])
    recorded = (record.get("bytes"), record.get("sha256"))
    if actual != recorded:
        live_artifact_mismatch_ids.append(record["id"])

if incoming_baseline_sha256 == ORIGINAL_BASELINE_RECORD_SET_SHA256:
    expected_incoming_mismatches = sorted(refresh_ids)
elif incoming_baseline_sha256 == PREVIOUS_REFRESHED_BASELINE_RECORD_SET_SHA256:
    expected_incoming_mismatches = ["artifact.o015.component-rights"]
else:
    expected_incoming_mismatches = []
if sorted(live_artifact_mismatch_ids) != expected_incoming_mismatches:
    raise ValueError(
        "live baseline artifact mismatches differ from the enumerated transaction: "
        f"expected={expected_incoming_mismatches}, "
        f"found={sorted(live_artifact_mismatch_ids)}"
    )

baseline_refreshed_ids: list[str] = []
for record_id, (_, size, digest) in REFRESH_SPECS.items():
    record = baseline_by_record_id[record_id]
    if (record.get("bytes"), record.get("sha256")) != (size, digest):
        baseline_refreshed_ids.append(record_id)
    record["bytes"] = size
    record["sha256"] = digest

if record_set_sha256(records) != REFRESHED_BASELINE_RECORD_SET_SHA256:
    raise ValueError("enumerated control-artifact refresh produced an unexpected baseline")

baseline_by_id = {record["id"]: canonical_json(record) for record in records}
baseline_ids = set(baseline_by_id)
required_baseline_ids = {
    RESOURCE_ID,
    SOURCE_EDITION_ID,
    TARGET_EDITION_ID,
    ROOT_UNIT_ID,
    PREVIOUS_UNIT_ID,
    "course.d90.advanced-optimization-convex-analysis",
    "concept.gradient",
    "concept.strong-convexity",
    "concept.penn.ascent-direction",
    "concept.penn.gradient-ascent",
    "concept.penn.convergence-order",
    "artifact.penn.authority-archive",
    "artifact.penn.authority-pdf",
    "artifact.o015.source-authority",
    *refresh_ids,
}
missing_required_baseline = sorted(required_baseline_ids - baseline_ids)
if missing_required_baseline:
    raise ValueError(
        f"Chapter 4 resource/edition prerequisite closure is missing: "
        f"{missing_required_baseline}"
    )

generated_ids: set[str] = set()


def add(record: dict[str, Any]) -> None:
    record_id = record["id"]
    if record_id in baseline_ids or record_id in generated_ids:
        raise ValueError(f"stable-ID collision while adding Penn Chapter 4: {record_id}")
    generated_ids.add(record_id)
    records.append(record)


source_text = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
target_text = (ROOT / TARGET_PATH).read_text(encoding="utf-8")
wrapper_text = (ROOT / WRAPPER_PATH).read_text(encoding="utf-8")
log_text = (ROOT / LOG_PATH).read_text(encoding="utf-8", errors="replace")
structure_report = json.loads(
    (ROOT / STRUCTURE_REPORT_PATH).read_text(encoding="utf-8")
)
formula_manifest = json.loads(
    (ROOT / FORMULA_MANIFEST_PATH).read_text(encoding="utf-8")
)
solver_results = json.loads(
    (ROOT / SOLVER_RESULTS_PATH).read_text(encoding="utf-8")
)
visual_qa = json.loads((ROOT / VISUAL_QA_PATH).read_text(encoding="utf-8"))
proposal_records = [
    json.loads(line)
    for line in (ROOT / PROPOSED_LEDGER_PATH).read_text(encoding="utf-8").splitlines()
    if line
]
proposal_ids = [record.get("event_id") for record in proposal_records]
if proposal_ids != EXPECTED_PROPOSAL_IDS or len(set(proposal_ids)) != 13:
    raise ValueError("Penn Chapter 4 proposal event closure differs")

shared_ledger_records = [
    json.loads(line)
    for line in SHARED_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
if len({record.get("event_id") for record in shared_ledger_records}) != len(
    shared_ledger_records
):
    raise ValueError("shared adverse ledger contains duplicate event IDs")
if shared_ledger_records[-len(proposal_records) :] != proposal_records:
    raise ValueError("Penn Chapter 4 proposals are not the exact shared-ledger tail")
ledger_integrated = True

with COMPONENT_RIGHTS_PATH.open("r", encoding="utf-8", newline="") as handle:
    rights_rows = list(csv.DictReader(handle))
rights_by_component = {row["component_id"]: row for row in rights_rows}
required_component_ids = {
    "o015-penn-ch04-text",
    "o015-penn-ch04-figures",
    "o015-penn-id-unit-04",
    "o015-penn-id-wrapper-04",
    "o015-penn-local-bbl-04",
    "o015-penn-original-bridges-04",
    "o015-solver-validation-penn-04",
    "o015-structural-audit-penn-04",
    "o015-visual-qa-penn-04",
    "o015-penn-maple",
}
if not required_component_ids.issubset(rights_by_component):
    raise ValueError("Chapter 4 component-rights row closure differs")
if rights_by_component["o015-penn-maple"]["status"] != "excluded":
    raise ValueError("Penn Maple component is not excluded")
component_rights_pass = True

coverage_text = COVERAGE_OVERLAP_PATH.read_text(encoding="utf-8")
coverage_overlap_pass = all(
    phrase in coverage_text
    for phrase in (
        "Penn Chapters 3 and 4 are now admitted.",
        "Chapter 4 supplies Wolfe/Armijo inexact line search",
        "does not duplicate O018",
        "active source-order cursor is Penn Chapter 5",
    )
)
if not coverage_overlap_pass:
    raise ValueError("Chapter 4 O018 non-overlap closure differs")

audit_pass = (
    structure_report.get("status") == "PASS"
    and structure_report.get("failures") == []
    and all(gate.get("pass") is True for gate in structure_report.get("gates", []))
)
formula_pass = (
    formula_manifest.get("status") == "PASS"
    and formula_manifest.get("failures") == []
    and formula_manifest.get("formula_pair_count") == 66
    and formula_manifest.get("determined_formula_pair_count") == 26
    and sorted(formula_manifest.get("event_coverage", {})) == EXPECTED_PROPOSAL_IDS
)
solver_pass = (
    solver_results.get("status") == "PASS"
    and solver_results.get("failures") == []
    and len(solver_results.get("gates", [])) == 12
    and all(gate.get("pass") is True for gate in solver_results.get("gates", []))
)
visual_pass = (
    visual_qa.get("status") == "PASS"
    and visual_qa.get("pdf", {}).get("pages") == 17
    and visual_qa.get("accessibility", {}).get("searchable_nonempty_pages") == 17
    and all(
        value == 0
        for value in visual_qa.get("inspection", {}).get("checks", {}).values()
    )
)

if "CC BY-NC-SA 3.0 US" not in wrapper_text:
    raise ValueError("Penn Chapter 4 wrapper lacks the exact license notice")
if "tidak" not in wrapper_text.lower() or "mendukung" not in wrapper_text.lower():
    raise ValueError("Penn Chapter 4 wrapper lacks non-endorsement language")
if source_text.count(r"\lstinputlisting") != 3:
    raise ValueError("Penn Chapter 4 source must expose exactly three listing calls")
if r"\lstinputlisting" in target_text or "Code/" in target_text:
    raise ValueError("Penn Chapter 4 target retains an excluded code dependency")

output_match = re.search(r"Output written on .*?\((\d+) pages?", log_text, re.DOTALL)
pdf_pages = int(output_match.group(1)) if output_match else 0
build_blockers = [
    pattern
    for pattern in (
        "LaTeX Error",
        "Undefined control sequence",
        "There were undefined references",
        "Citation " + chr(96),
        "Overfull \\hbox",
        "Underfull \\hbox",
        "Missing character",
        "Rerun to get cross-references right",
    )
    if pattern in log_text
]
build_pass = pdf_pages == 17 and not build_blockers

if not all(
    (
        audit_pass,
        formula_pass,
        solver_pass,
        visual_pass,
        build_pass,
        ledger_integrated,
        component_rights_pass,
        coverage_overlap_pass,
    )
):
    raise ValueError("Penn Chapter 4 admission gates are not all closed")
admission_state = "admitted_reader"

# Work-level resource and editions are pre-existing immutable semantic records.
unit = common("unit", UNIT_ID, "built")
unit.update(
    {
        "edition_id": SOURCE_EDITION_ID,
        "source_edition_id": SOURCE_EDITION_ID,
        "target_edition_id": TARGET_EDITION_ID,
        "parent_id": ROOT_UNIT_ID,
        "unit_kind": "chapter",
        "order": 4,
        "source_local_id": "Section4",
        "source_local_label": "Approximate Line Search and Convergence of Gradient Ascent",
        "target_local_label": "Pencarian Garis Hampiran dan Konvergensi Pendakian Gradien",
        "source_locator": f"{SOURCE_PATH}:1-469",
        "target_locator": f"{TARGET_PATH}:1-613",
        "rights_id": TARGET_RIGHTS_ID,
        "translation_state": "built",
        "admission_state": admission_state,
        "publication_state": "unpublished_working_edition",
        "next_source_order_unit": "Section5.tex:1",
    }
)
add(unit)

rights_specs: list[dict[str, Any]] = [
    {
        "id": SOURCE_RIGHTS_ID, "status": "admitted",
        "component_id": "o015-penn-ch04-text", "path": SOURCE_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/lecture_notes/",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["attribution", "identify changes", "noncommercial use", "ShareAlike", "license link", "no implied endorsement"],
        "notes": "Complete frozen Chapter 4 source from editable archive v1.0.",
    },
    {
        "id": TARGET_RIGHTS_ID, "status": "derivative",
        "component_id": "o015-penn-id-unit-04", "path": TARGET_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/lecture_notes/",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["attribute Griffin, Miller, Mercer, and Penn source", "identify Indonesian translation and corrections", "noncommercial use", "ShareAlike", "license link", "no implied endorsement"],
        "notes": "Complete admitted Chapter 4 Indonesian derivative.",
    },
    {
        "id": "rights.o015-penn-ch04-wrapper", "status": "derivative",
        "component_id": "o015-penn-id-wrapper-04", "path": WRAPPER_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/lecture_notes/",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["retain attribution", "retain correction appendix", "retain non-endorsement", "retain ShareAlike"],
        "notes": "Standalone reader wrapper with bounded prerequisite labels.",
    },
    {
        "id": "rights.o015-penn-ch04-figures", "status": "admitted_with_source_level_notice",
        "component_id": "o015-penn-ch04-figures", "path": "source/id-ID/figures",
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US source-archive-level evidence",
        "authority_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["retain exact bytes", "attribute source work", "include under derivative ShareAlike terms"],
        "notes": "Five PDF figures are byte-identical source-archive copies.",
    },
    {
        "id": "rights.o015-penn-ch04-bibliography", "status": "adapted_with_caveat",
        "component_id": "o015-penn-local-bbl-04", "path": BIB_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["retain attribution", "identify bounded excerpt", "preserve opaque bundled bibliography evidence"],
        "notes": "Exact one-entry Bert99 excerpt; source bibliography databases are absent.",
    },
    {
        "id": "rights.o015-penn-ch04-bridges", "status": "project_authored_derivative_component",
        "component_id": "o015-penn-original-bridges-04", "path": TARGET_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "original bridge material inside CC BY-NC-SA 3.0 US derivative",
        "authority_url": TARGET_PATH,
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": False,
        "required_handling": ["identify independent authorship", "do not claim code identity with Maple source", "retain ShareAlike derivative terms"],
        "notes": "Three independent pseudocode surfaces replace excluded Maple listings.",
    },
    {
        "id": "rights.o015-penn-ch04-maple-excluded", "status": "excluded",
        "component_id": "o015-penn-maple",
        "path": "authority/penn-state/source/ClassNotes/Code",
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "unclear/external",
        "authority_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "license_url": None, "translation_permitted": False,
        "required_handling": ["do not translate", "do not redistribute as admitted code", "replace only with independently authored pseudocode"],
        "notes": "BackTrace.mpl and both GradientAscent Maple listings remain excluded.",
    },
    {
        "id": "rights.o015-penn-ch04-audit", "status": "project_local",
        "component_id": "o015-structural-audit-penn-04", "path": AUDIT_SOURCE_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": AUDIT_SOURCE_PATH, "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with report and formula-delta manifest", "retain frozen authority hashes"],
        "notes": "Deterministic structural, formula-delta, and independent rereview evidence.",
    },
    {
        "id": "rights.o015-penn-ch04-solver", "status": "project_local",
        "component_id": "o015-solver-validation-penn-04", "path": SOLVER_SOURCE_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": SOLVER_SOURCE_PATH, "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with deterministic result", "use open runtime"],
        "notes": "Twelve fail-closed open numerical gates.",
    },
    {
        "id": "rights.o015-penn-ch04-visual", "status": "project_local",
        "component_id": "o015-visual-qa-penn-04", "path": VISUAL_QA_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local QA evidence",
        "authority_url": VISUAL_QA_PATH, "license_url": None,
        "translation_permitted": False,
        "required_handling": ["retain deterministic render identity", "do not claim tagged PDF"],
        "notes": "All-page visual and accessibility limitation receipt.",
    },
]
for spec in rights_specs:
    rights = common("rights", spec["id"], spec["status"])
    rights.update({key: value for key, value in spec.items() if key not in {"id", "status"}})
    add(rights)

for record_id, label, prerequisites, domain in CONCEPT_SPECS:
    concept = common("concept", record_id, "current")
    concept.update(
        {"canonical_label": label, "prerequisite_ids": prerequisites, "domain": domain}
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
            "scope": "smooth numerical optimization and convergence analysis",
            "register": "formal",
            "evidence_segment_ids": [f"d90.penn.v1.ch04.seg{segment_order:04d}"],
            "examples": [preferred],
            "rights_id": TARGET_RIGHTS_ID,
        }
    )
    add(term)

target_lines = target_text.splitlines()
marker_pattern = re.compile(r"^% segment-id: (d90\.penn\.v1\.ch04\.seg\d{4})$")
markers = [
    (line_number, match.group(1))
    for line_number, line in enumerate(target_lines, start=1)
    if (match := marker_pattern.fullmatch(line))
]
expected_marker_ids = [f"d90.penn.v1.ch04.seg{order:04d}" for order in range(1, 8)]
if [item[1] for item in markers] != expected_marker_ids:
    raise ValueError("Chapter 4 target segment marker closure/order differs")

for index, (
    order,
    source_start,
    source_end,
    source_label,
    target_label,
    concept_ids,
) in enumerate(SEGMENT_SPECS):
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
            "source_local_id": f"Section4-lines-{source_start}-{source_end}",
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
            "translation_state": "built",
            "structural_review_state": "passed",
            "mathematical_review_state": "passed",
            "language_review_state": "not_recorded",
            "concept_ids": concept_ids,
            "rights_id": TARGET_RIGHTS_ID,
            "evidence_event_ids": [
                "qa.o015.penn-ch04.structure",
                "qa.o015.penn-ch04.formula-delta",
                "qa.o015.penn-ch04.corrections",
                "qa.o015.penn-ch04.solver",
                "qa.o015.penn-ch04.build",
                "qa.o015.penn-ch04.visual",
                "qa.o015.penn-ch04.rights",
                "qa.o015.penn-ch04.overlap",
            ],
        }
    )
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
if len(source_exercises) != 4 or len(target_exercises) != 4:
    raise ValueError("Chapter 4 exercise closure differs")
for order, (
    (source_start, source_end),
    (target_start, target_end),
    concept_id,
) in enumerate(zip(source_exercises, target_exercises, EXERCISE_CONCEPTS), start=1):
    segment_order = next(
        segment_order
        for segment_order, start, end, *_ in SEGMENT_SPECS
        if start <= source_start <= end
    )
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, source_start, source_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, target_start, target_end)
    surface = common("learning_surface", f"surface.penn.v1.ch04.exercise{order:02d}", "present")
    surface.update(
        {
            "unit_id": UNIT_ID,
            "surface_type": "exercise_prompt",
            "presence": "present",
            "order": order,
            "source_local_id": f"exercise{order:02d}",
            "source_local_label": f"Source-order exercise {order}",
            "target_local_label": f"Latihan urutan sumber {order}",
            "related_segment_ids": [f"d90.penn.v1.ch04.seg{segment_order:04d}"],
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

source_algorithms = sorted(
    find_environment_spans(source_text, "algorithm")
    + find_environment_spans(source_text, "cgalgorithm")
)
target_algorithms = sorted(
    find_environment_spans(target_text, "algorithm")
    + find_environment_spans(target_text, "cgalgorithm")
)
if len(source_algorithms) != 3 or len(target_algorithms) != 3:
    raise ValueError("Chapter 4 algorithm surface closure differs")
for order, (
    (source_start, source_end),
    (target_start, target_end),
    (record_id, concept_id, label),
) in enumerate(zip(source_algorithms, target_algorithms, ALGORITHM_SPECS), start=1):
    segment_order = next(
        segment_order
        for segment_order, start, end, *_ in SEGMENT_SPECS
        if start <= source_start <= end
    )
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, source_start, source_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, target_start, target_end)
    surface = common("learning_surface", record_id, "present")
    surface.update(
        {
            "unit_id": UNIT_ID,
            "surface_type": "algorithm_pseudocode",
            "presence": "present",
            "order": order,
            "source_local_id": f"excluded-maple-surface-{order:02d}",
            "source_local_label": label,
            "target_local_label": label,
            "related_segment_ids": [f"d90.penn.v1.ch04.seg{segment_order:04d}"],
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
            "rights_id": "rights.o015-penn-ch04-bridges",
            "disposition": "independent_replacement_for_excluded_maple",
            "excluded_source_component_rights_id": "rights.o015-penn-ch04-maple-excluded",
        }
    )
    add(surface)

for record_id, filename, concept_id, segment_order, description in ASSET_SPECS:
    source_relative = f"authority/penn-state/source/ClassNotes/Figures/{filename}"
    target_relative = f"source/id-ID/figures/{filename}"
    source_bytes, source_digest = file_info(source_relative)
    target_bytes, target_digest = file_info(target_relative)
    if (source_bytes, source_digest) != (target_bytes, target_digest):
        raise ValueError(f"Penn Chapter 4 figure is not byte-identical: {filename}")
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
            "rights_id": "rights.o015-penn-ch04-figures",
            "related_segment_ids": [f"d90.penn.v1.ch04.seg{segment_order:04d}"],
            "concept_id": concept_id,
            "adaptation": "byte-identical source-archive copy; Indonesian caption is in the translated TeX",
            "accessibility_description": description,
        }
    )
    add(asset_record)

for event in proposal_records:
    ranges = [
        (int(start), int(end))
        for start, end in re.findall(r"(\d+)-(\d+)", event.get("source", ""))
    ]
    if not ranges:
        raise ValueError(f"{event['event_id']}: no Section4 source locator")
    affected = [
        f"d90.penn.v1.ch04.seg{order:04d}"
        for order, segment_start, segment_end, *_ in SEGMENT_SPECS
        if any(
            not (range_end < segment_start or range_start > segment_end)
            for range_start, range_end in ranges
        )
    ]
    correction = common(
        "correction",
        "correction." + event["event_id"].lower(),
        "applied_in_admitted_reader",
    )
    correction.update(
        {
            "source_event_id": event["event_id"],
            "source_edition_id": SOURCE_EDITION_ID,
            "affected_unit_ids": [UNIT_ID],
            "affected_segment_ids": affected,
            "source_path": SOURCE_PATH,
            "source_line_start": min(start for start, _ in ranges),
            "source_line_end": max(end for _, end in ranges),
            "source_locator": event["source"],
            "surface": event["surface"],
            "source_issue": event["source_issue"],
            "target_action": event["target_action"],
            "correction_class": event["class"],
            "disposition": "applied_in_admitted_reader",
            "shared_ledger_state": "integrated",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.o015.adverse-ledger",
            "proposal_artifact_id": "artifact.penn.proposed-ledger-ch04",
        }
    )
    add(correction)

artifact_records = [
    artifact("artifact.penn.source-ch04", "source_tex", SOURCE_PATH, source_edition_id=SOURCE_EDITION_ID, rights_id=SOURCE_RIGHTS_ID),
    artifact("artifact.penn.target-ch04", "target_tex", TARGET_PATH, source_artifact_id="artifact.penn.source-ch04", target_edition_id=TARGET_EDITION_ID, rights_id=TARGET_RIGHTS_ID),
    artifact("artifact.penn.target-wrapper-ch04", "reader_wrapper_tex", WRAPPER_PATH, target_edition_id=TARGET_EDITION_ID, rights_id="rights.o015-penn-ch04-wrapper", input_artifact_ids=["artifact.penn.target-ch04", "artifact.penn.local-bibliography-ch04"]),
    artifact("artifact.penn.local-bibliography-ch04", "bounded_bibliography_excerpt", BIB_PATH, source_artifact_id="artifact.penn.authority-archive", target_edition_id=TARGET_EDITION_ID, rights_id="rights.o015-penn-ch04-bibliography"),
    artifact("artifact.penn.target-pdf-ch04", "reader_pdf", PDF_PATH, target_edition_id=TARGET_EDITION_ID, rights_id=TARGET_RIGHTS_ID, pages=pdf_pages, build_event_id="qa.o015.penn-ch04.build", accessibility="searchable 17-page id-ID PDF; untagged; ten inherited vector-figure font resources lack ToUnicode", input_artifact_ids=["artifact.penn.target-wrapper-ch04", "artifact.penn.target-ch04", "artifact.penn.local-bibliography-ch04"]),
    artifact("artifact.penn.build-log-ch04", "build_log", LOG_PATH, target_edition_id=TARGET_EDITION_ID, source_artifact_id="artifact.penn.target-wrapper-ch04"),
    artifact("artifact.penn.target-text-ch04", "qa_extract", TEXT_PATH, target_edition_id=TARGET_EDITION_ID, source_artifact_id="artifact.penn.target-pdf-ch04"),
    artifact("artifact.penn.audit-source-ch04", "qa_source", AUDIT_SOURCE_PATH, rights_id="rights.o015-penn-ch04-audit", toolchain="Python 3 standard library"),
    artifact("artifact.penn.structure-report-ch04", "qa_report", STRUCTURE_REPORT_PATH, source_artifact_id="artifact.penn.audit-source-ch04"),
    artifact("artifact.penn.formula-manifest-ch04", "qa_report", FORMULA_MANIFEST_PATH, source_artifact_id="artifact.penn.audit-source-ch04"),
    artifact("artifact.penn.proposed-ledger-ch04", "proposed_correction_ledger", PROPOSED_LEDGER_PATH, source_artifact_id="artifact.penn.source-ch04"),
    artifact("artifact.penn.solver-validator-ch04", "qa_source", SOLVER_SOURCE_PATH, rights_id="rights.o015-penn-ch04-solver", toolchain="Python / NumPy"),
    artifact("artifact.penn.solver-results-ch04", "qa_report", SOLVER_RESULTS_PATH, source_artifact_id="artifact.penn.solver-validator-ch04"),
    artifact("artifact.penn.visual-qa-ch04", "qa_report", VISUAL_QA_PATH, source_artifact_id="artifact.penn.target-pdf-ch04", rights_id="rights.o015-penn-ch04-visual"),
    artifact("artifact.penn.source-audit-ch04", "admission_audit", SOURCE_AUDIT_PATH, source_artifact_id="artifact.penn.source-ch04", rights_id="rights.o015-penn-ch04-audit"),
    artifact("artifact.o015.backend-generator-penn-ch04", "qa_source", "qa/extend_backend_penn_ch04.py", toolchain="Python 3 standard library"),
    artifact("artifact.o015.backend-validator-penn-ch04", "backend_validator", "qa/validate_backend_penn_ch04.py", toolchain="Python 3 standard library"),
]
for record in artifact_records:
    add(record)

qa_specs: list[dict[str, Any]] = [
    {
        "id": "qa.o015.penn-ch04.source-freeze", "status": "pass",
        "event_type": "source", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.source-ch04", "artifact.penn.authority-archive", "artifact.penn.authority-pdf", "artifact.o015.source-authority"],
        "authority_id": "o015-penn-math555-v1.0-source",
        "source_sha256": FROZEN_FILES[SOURCE_PATH][1],
        "edition_distinction": "editable v1.0 is text authority; public v1.0.1 PDF is a correction witness",
    },
    {
        "id": "qa.o015.penn-ch04.structure", "status": "pass",
        "event_type": "topology", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.structure-report-ch04"],
        "segment_count": 7, "source_lines": 469, "target_lines": 613,
        "ordered_environment_count": 112, "label_count": 32,
    },
    {
        "id": "qa.o015.penn-ch04.formula-delta", "status": "pass",
        "event_type": "mathematics", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.formula-manifest-ch04", "artifact.penn.proposed-ledger-ch04"],
        "formula_pair_count": 66, "determined_formula_pair_count": 26,
        "correction_event_count": 13,
    },
    {
        "id": "qa.o015.penn-ch04.corrections", "status": "pass",
        "event_type": "correction_ledger", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.proposed-ledger-ch04", "artifact.o015.adverse-ledger"],
        "event_ids": proposal_ids, "shared_ledger_state": "integrated",
        "shared_ledger_tail_exact": True, "collision_count": 0,
    },
    {
        "id": "qa.o015.penn-ch04.algorithms", "status": "pass",
        "event_type": "code_surface", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.target-ch04", "artifact.penn.structure-report-ch04"],
        "source_algorithm_surface_count": 3, "excluded_maple_listing_count": 3,
        "independent_replacement_count": 3, "retained_legacy_dependency_count": 0,
    },
    {
        "id": "qa.o015.penn-ch04.exercises", "status": "pass",
        "event_type": "learning_surface", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.structure-report-ch04"],
        "exercise_count": 4, "hint_count": 0, "answer_count": 0,
        "solution_count": 0,
    },
    {
        "id": "qa.o015.penn-ch04.solver", "status": "pass",
        "event_type": "computation", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.solver-results-ch04", "artifact.penn.solver-validator-ch04"],
        "gate_count": 12, "failed_gate_count": 0,
    },
    {
        "id": "qa.o015.penn-ch04.build", "status": "pass",
        "event_type": "build", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.target-pdf-ch04", "artifact.penn.build-log-ch04"],
        "pages": pdf_pages, "page_size": "A4", "errors": build_blockers,
        "deterministic_rebuild": "byte-identical fixed-epoch builds",
    },
    {
        "id": "qa.o015.penn-ch04.visual", "status": "pass",
        "event_type": "visual", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.visual-qa-ch04", "artifact.penn.target-pdf-ch04"],
        "inspected_pages": [1, 17], "blank_or_broken_page_count": 0,
    },
    {
        "id": "qa.o015.penn-ch04.accessibility", "status": "pass_with_limitation",
        "event_type": "accessibility", "result": "pass_with_limitation",
        "witness_artifact_ids": ["artifact.penn.visual-qa-ch04", "artifact.penn.target-pdf-ch04", "artifact.penn.target-text-ch04"],
        "checks": ["PDF language metadata is id-ID", "all 17 pages expose text", "PDF has no forms or JavaScript"],
        "limitations": ["PDF is untagged", "ten inherited vector-figure font resources lack ToUnicode"],
    },
    {
        "id": "qa.o015.penn-ch04.math-rereview", "status": "pass",
        "event_type": "mathematics", "result": "pass",
        "witness_artifact_ids": ["artifact.penn.target-ch04", "artifact.penn.structure-report-ch04", "artifact.penn.formula-manifest-ch04", "artifact.penn.solver-results-ch04"],
        "remaining_defects": {"P1": 0, "P2": 0, "P3": 0},
        "scope": "Independent source/target/proposal rereview of all repaired Chapter 4 surfaces.",
    },
    {
        "id": "qa.o015.penn-ch04.language", "status": "not_recorded",
        "event_type": "language", "result": "not_recorded",
        "witness_artifact_ids": [],
        "gap": "No separate independent Indonesian language-review receipt is recorded.",
    },
    {
        "id": "qa.o015.penn-ch04.rights", "status": "pass",
        "event_type": "rights", "result": "pass",
        "witness_artifact_ids": ["artifact.o015.component-rights", "artifact.penn.source-audit-ch04"],
        "component_ids": sorted(required_component_ids),
        "excluded_component_ids": ["o015-penn-maple"],
    },
    {
        "id": "qa.o015.penn-ch04.overlap", "status": "pass",
        "event_type": "coverage", "result": "pass",
        "witness_artifact_ids": ["artifact.o015.coverage-overlap", "artifact.penn.source-audit-ch04"],
        "excluded_lane": "O018", "next_source_order_cursor": "Section5.tex:1",
    },
]
for spec in qa_specs:
    qa = common("qa_event", spec["id"], spec["status"])
    qa.update(
        {
            "unit_id": UNIT_ID,
            **{key: value for key, value in spec.items() if key not in {"id", "status"}},
        }
    )
    add(qa)

relation_specs: list[tuple[str, str, str, str, str]] = [
    ("relation.penn.ch04.resource-contains-source-edition", "contains", RESOURCE_ID, SOURCE_EDITION_ID, "Frozen editable Penn work edition."),
    ("relation.penn.ch04.resource-contains-target-edition", "contains", RESOURCE_ID, TARGET_EDITION_ID, "Working Indonesian derivative edition."),
    ("relation.penn.ch04.source-edition-contains-unit", "contains", SOURCE_EDITION_ID, UNIT_ID, "Complete Section4 source unit."),
    ("relation.penn.ch04.target-edition-contains-unit", "contains", TARGET_EDITION_ID, UNIT_ID, "Complete Chapter 4 Indonesian reader unit."),
    ("relation.penn.ch04.work-contains-unit", "contains", ROOT_UNIT_ID, UNIT_ID, "Complete source-order Chapter 4."),
    ("relation.penn.ch04.ch03-precedes-ch04", "precedes", PREVIOUS_UNIT_ID, UNIT_ID, "Penn source-order continuation."),
    ("relation.penn.ch04.depends-on-gradient", "depends-on", UNIT_ID, "concept.gradient", "Differentiability and the gradient are prerequisites."),
    ("relation.penn.ch04.depends-on-gradient-ascent", "depends-on", UNIT_ID, "concept.penn.gradient-ascent", "Chapter 3 gradient ascent is the algorithmic prerequisite."),
    ("relation.penn.ch04.target-translates-source", "translates", "artifact.penn.target-ch04", "artifact.penn.source-ch04", "Complete contiguous id-ID translation."),
    ("relation.penn.ch04.wrapper-contains-target", "contains", "artifact.penn.target-wrapper-ch04", "artifact.penn.target-ch04", "Standalone licensed reader wrapper."),
    ("relation.penn.ch04.pdf-depends-on-wrapper", "depends-on", "artifact.penn.target-pdf-ch04", "artifact.penn.target-wrapper-ch04", "Deterministic reader build input."),
    ("relation.penn.ch04.pdf-depends-on-bibliography", "depends-on", "artifact.penn.target-pdf-ch04", "artifact.penn.local-bibliography-ch04", "Exact one-entry bibliography excerpt."),
    ("relation.penn.ch04.text-adapts-pdf", "adapts", "artifact.penn.target-text-ch04", "artifact.penn.target-pdf-ch04", "Searchability and accessibility witness."),
    ("relation.penn.ch04.bibliography-adapts-archive", "adapts", "artifact.penn.local-bibliography-ch04", "artifact.penn.authority-archive", "Exact Bert99 excerpt from bundled Math555.bbl."),
    ("relation.penn.ch04.structure-depends-on-audit", "depends-on", "artifact.penn.structure-report-ch04", "artifact.penn.audit-source-ch04", "Deterministic structural audit output."),
    ("relation.penn.ch04.formula-depends-on-audit", "depends-on", "artifact.penn.formula-manifest-ch04", "artifact.penn.audit-source-ch04", "Deterministic formula-delta output."),
    ("relation.penn.ch04.solver-results-depend-on-validator", "depends-on", "artifact.penn.solver-results-ch04", "artifact.penn.solver-validator-ch04", "Deterministic open numerical output."),
    ("relation.penn.ch04.visual-depends-on-pdf", "depends-on", "artifact.penn.visual-qa-ch04", "artifact.penn.target-pdf-ch04", "All-page render and inspection receipt."),
    ("relation.penn.ch04.source-audit-depends-on-structure", "depends-on", "artifact.penn.source-audit-ch04", "artifact.penn.structure-report-ch04", "Final admission source audit."),
    ("relation.penn.ch04.source-audit-depends-on-visual", "depends-on", "artifact.penn.source-audit-ch04", "artifact.penn.visual-qa-ch04", "Final admission visual evidence."),
]
for order in range(1, 8):
    relation_specs.append(
        (f"relation.penn.ch04.contains-seg{order:04d}", "contains", UNIT_ID, f"d90.penn.v1.ch04.seg{order:04d}", "Ordered contiguous translation segment.")
    )
for segment_order, concept_id in SEGMENT_DEFINITION_SPECS:
    suffix = concept_id.removeprefix("concept.penn.")
    relation_specs.append(
        (f"relation.penn.ch04.seg{segment_order:04d}-defines-{suffix}", "defines", f"d90.penn.v1.ch04.seg{segment_order:04d}", concept_id, "Primary source-linked concept surface.")
    )
for order, concept_id in enumerate(EXERCISE_CONCEPTS, start=1):
    relation_specs.append(
        (f"relation.penn.ch04.exercise{order:02d}-exercises-{concept_id.removeprefix('concept.penn.')}", "exercises", f"surface.penn.v1.ch04.exercise{order:02d}", concept_id, "Source-order exercise prompt.")
    )
for record_id, concept_id, label in ALGORITHM_SPECS:
    relation_specs.append(
        (f"relation.penn.ch04.{record_id.rsplit('.', 1)[-1]}-illustrates-{concept_id.removeprefix('concept.penn.')}", "illustrates", record_id, concept_id, label)
    )
for asset_id, _, concept_id, _, description in ASSET_SPECS:
    relation_specs.append(
        (f"relation.penn.ch04.{asset_id.rsplit('.', 1)[-1]}-illustrates-{concept_id.removeprefix('concept.penn.')}", "illustrates", asset_id, concept_id, description)
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

final_by_id = {record["id"]: canonical_json(record) for record in records}
missing_baseline_ids = sorted(baseline_ids - set(final_by_id))
changed_baseline_ids = sorted(
    record_id
    for record_id in baseline_ids
    if final_by_id.get(record_id) != baseline_by_id[record_id]
)
if missing_baseline_ids or changed_baseline_ids:
    raise ValueError(
        "Chapter 4 extension changed the refreshed baseline: "
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
    "baseline_comparison": {
        "baseline_record_count": len(baseline_ids),
        "baseline_record_set_sha256": record_set_sha256(
            [record for record in records if record["id"] in baseline_ids]
        ),
        "changed_record_ids_after_refresh": changed_baseline_ids,
        "enumerated_live_artifact_refresh_ids": sorted(baseline_refreshed_ids),
        "incoming_live_artifact_mismatch_ids": sorted(live_artifact_mismatch_ids),
        "incoming_record_set_sha256": incoming_baseline_sha256,
        "missing_record_ids": missing_baseline_ids,
        "result": "pass",
        "semantic_record_count": len(baseline_semantic),
        "semantic_record_set_sha256": record_set_sha256(baseline_semantic),
    },
    "csv": {
        "bytes": file_info("backend/records.csv")[0],
        "sha256": file_info("backend/records.csv")[1],
    },
    "entity_counts": dict(
        sorted(Counter(record["entity_type"] for record in records).items())
    ),
    "jsonl": {
        "bytes": file_info("backend/records.jsonl")[0],
        "sha256": file_info("backend/records.jsonl")[1],
    },
    "penn_ch04_added_entity_counts": dict(
        sorted(Counter(record["entity_type"] for record in added_records).items())
    ),
    "penn_ch04_added_record_count": len(added_records),
    "penn_ch04_record_set_sha256": record_set_sha256(added_records),
    "record_count": len(records),
    "resource_edition_reuse_ids": [RESOURCE_ID, SOURCE_EDITION_ID, TARGET_EDITION_ID],
    "segment_count": 7,
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
