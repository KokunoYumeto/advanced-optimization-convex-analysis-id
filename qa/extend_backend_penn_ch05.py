#!/usr/bin/env python3
"""Deterministically admit Penn MATH 555 Chapter 5 into the O015 backend.

The pre-existing 1,128-record backend is immutable except for three explicitly
enumerated control-artifact byte bindings.  Shared Chapter 5 ledger, rights,
coverage, build, and QA admission precede this transaction; this script proves
those exact inputs and reconstructs only its own Chapter 5 closure on reruns.
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

RECORDED_AT = "2026-08-22T22:30:00Z"
WORKFLOW = "o015-penn-ch05-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 1128
ORIGINAL_BASELINE_RECORD_SET_SHA256 = (
    "9aa714128746bc35f6fbc9e1b18c9960c7119228c70e8ff5f79010931eb4ed29"
)
PRIOR_REFRESHED_BASELINE_RECORD_SET_SHA256 = (
    "efedb445aa2c566d401c00a5ac6eb12ff5747de28b678cf0659a1f1cb70b06e3"
)
REFRESHED_BASELINE_RECORD_SET_SHA256 = (
    "23ffc42f0fa6b19a828154db74bdda2a0fa99e860f7615c918f4c7a3787f2edb"
)
BASELINE_SEMANTIC_COUNT = 999
BASELINE_SEMANTIC_RECORD_SET_SHA256 = (
    "971333c796eeb036b59cc1ff5ce6c0ce5bfa2836e5ab4d7f4176d4aeea0b5d97"
)
BASELINE_IMMUTABLE_ARTIFACT_COUNT = 126
BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256 = (
    "68c89eb4dd196935f8b60d9f3eccc32a4ae61530503d189bb4ca3903bd9061c0"
)

REFRESH_SPECS: dict[str, tuple[str, int, str]] = {
    "artifact.o015.adverse-ledger": (
        "00_control/ADVERSE_LEDGER.jsonl",
        93480,
        "c8d87cd7958e9beba30372e1fc70df7fe992970db780d8757c061854fb9075f0",
    ),
    "artifact.o015.component-rights": (
        "00_control/COMPONENT_RIGHTS.csv",
        23258,
        "51e08f77f709a945c8e53948ee466d7d06e75e469ef7fef4d7d269fc895e37e9",
    ),
    "artifact.o015.coverage-overlap": (
        "00_control/COVERAGE_OVERLAP.md",
        5997,
        "4e47d255c94d404b68f347464302475edf76da2a21824afa9ccda50cf9618560",
    ),
}

SOURCE_PATH = "authority/penn-state/source/ClassNotes/Section5.tex"
TARGET_PATH = "source/id-ID/penn-05-metode-newton-dan-koreksi-id.tex"
WRAPPER_PATH = "source/id-ID/D90-PENN-05-metode-newton-dan-koreksi-id.tex"
BIB_PATH = "source/id-ID/references-penn-ch05-id.bbl"
PDF_PATH = "output/pdf/D90-PENN-05-metode-newton-dan-koreksi-id.pdf"
LOG_PATH = "build/penn-unit-05-id/D90-PENN-05-metode-newton-dan-koreksi-id.log"
TEXT_PATH = "qa/D90-PENN-05-metode-newton-dan-koreksi-id.txt"
AUDIT_SOURCE_PATH = "qa/audit_penn_ch05_candidate.py"
STRUCTURE_REPORT_PATH = "qa/PENN_CH05_STRUCTURE_REPORT.json"
PROPOSED_LEDGER_PATH = "qa/PENN_CH05_PROPOSED_LEDGER.jsonl"
SOLVER_SOURCE_PATH = "qa/validate_penn_ch05_math.py"
SOLVER_RESULTS_PATH = "qa/PENN_CH05_SOLVER_RESULTS.json"
VISUAL_QA_PATH = "qa/PENN_CH05_VISUAL_QA.json"
REREVIEW_PATH = "qa/PENN_CH05_INDEPENDENT_REREVIEW.md"
SOURCE_AUDIT_PATH = "00_control/PENN_CH05_SOURCE_AUDIT.md"

RESOURCE_ID = "resource.penn.math555-nonlinear-programming"
SOURCE_EDITION_ID = "edition.penn.math555.source-v1-0"
TARGET_EDITION_ID = "edition.penn.math555.id-id.v1"
ROOT_UNIT_ID = "unit.penn.v1"
PREVIOUS_UNIT_ID = "unit.penn.v1.ch04"
UNIT_ID = "unit.penn.v1.ch05"
SOURCE_RIGHTS_ID = "rights.o015-penn-ch05-source"
TARGET_RIGHTS_ID = "rights.o015-penn-id-ch05"

EXPECTED_PROPOSAL_IDS = [
    f"O015-PENN-ADV-{number:04d}" for number in range(38, 50)
]

FROZEN_FILES: dict[str, tuple[int, str]] = {
    SOURCE_PATH: (22371, "15186b99be0913d83046e3e32eaf7a378d3a4fccd222219984b091ddf7f9a428"),
    TARGET_PATH: (27317, "0f6afd7da2268661124f967f299ac9df89bb6a8f5683b3e4e8fea32718a8549a"),
    WRAPPER_PATH: (7230, "82450c4cdbe6de904c7cba1ee22922869f5d2e2caf19be69285092a5ea987e55"),
    BIB_PATH: (625, "037e62878f1a562314a33054da8f4df4e49c029bbad31c2ec75066cd3e1a99f3"),
    PDF_PATH: (2691780, "427db2c5a4428dfbe222d7e1d4f5c5349d4f78484a8593c412328fe94a7353c6"),
    LOG_PATH: (27062, "bb3e9416233d14400ced235b69eeb95f76e6347dfeabbfd2c06727b543aed8be"),
    TEXT_PATH: (29195, "78fc7ecf877b7707c6c33736210449d502bbc148b84994b65b0d2fc4791365d3"),
    AUDIT_SOURCE_PATH: (14118, "6964f467ee85f856fe0c28ef5628dc8c83f1140b764dfe4a03c95a84d28c6af4"),
    STRUCTURE_REPORT_PATH: (26392, "89757169df04a17c4e19bb72469aa6cd5ebb094e4c1298e3b8b78b44b3d9146a"),
    PROPOSED_LEDGER_PATH: (10242, "823ba2913a44c88d39c062f9fab847720e5637fd9dca75e4532de806bcd02d67"),
    SOLVER_SOURCE_PATH: (11053, "c1362699da1bfe8fc5ce791556c84255ba05049ab3506fc1891643ff8eb98af9"),
    SOLVER_RESULTS_PATH: (6242, "9c5905c0022a1a99f8064484cff40abff0b9435df133822b5e16fc2b0ac6401f"),
    VISUAL_QA_PATH: (2687, "3130aee988a10cf4fc4c2b3cfbdc494293142519c0c416d603a109704188bde4"),
    REREVIEW_PATH: (9373, "239e4d79f90c570ac95ceb22cab097b41980c308abb39f940fe66dbc5f7861dd"),
    SOURCE_AUDIT_PATH: (7227, "37e9667e41c17d1f3469f669b1bebd3b1a7104f6cc4d56a50177f887c226227a"),
    "authority/penn-state/Math555_SRC.zip": (23909024, "1958af9417aa7cd057f321c3c6f71a8c02349fb1d32da75f6bad05eb66286a0e"),
    "authority/penn-state/Math555.pdf": (4776722, "f7b99401af875333f3becb591eebf61fac81280768537c20b8a1264d578cb4ff"),
}

FIGURE_IDENTITIES: dict[str, tuple[int, str]] = {
    "NewtonsMethod.pdf": (123281, "94c86e8eaf669f51dfe4d63f3b6799c84fb7b2d4fc781c304541aa40bc0442b6"),
    "DoublePeak.pdf": (2138564, "0091677ffedeaed91d4746edd03439ebb586a02900c86b9d7b9693205019e6fa"),
    "GaussModifiedNewtonsMethod.pdf": (56347, "d59d49782969f5c55a49fde4ffc65e919019e5df06ebd70009457a1b508422c2"),
    "ModifiedNewton.pdf": (56339, "7b5a76196e5b535447bc39162d1f11d63e65a021381108f06ac85ab7738bc28f"),
}
for _filename, _identity in FIGURE_IDENTITIES.items():
    FROZEN_FILES[f"authority/penn-state/source/ClassNotes/Figures/{_filename}"] = _identity
    FROZEN_FILES[f"source/id-ID/figures/{_filename}"] = _identity

EXCLUDED_CODE_IDENTITIES: dict[str, tuple[int, str]] = {
    "NewtonsMethodGeneral-1.mpl": (1668, "918e74995875169a7cdc7557903cfdcf89b090ab4b555d6fe1ebff2096d6bd84"),
    "NewtonsMethodGeneral-2.mpl": (568, "8ad5ff5bf7ed6a2f2e35727ef6a93ae6a9a08473ad579d104ec25ae638c6ce83"),
    "ModifiedCholesky.mpl": (513, "a52e4706ceeb9b21a4e68f78bf7d48aa96d4e9b5d1fa4c499762d6509ddfad89"),
    "ModifiedNewtonsMethod-1.mpl": (1499, "8392a10e803d4b5219eacefe52f85621bdb6ee1ad2d65e78c474f3697da0a6d0"),
    "ModifiedNewtonsMethod-2.mpl": (929, "5b14d0dcb525888022339740fda447dd7e15f7cbe00cd4547663350eaf0c6cd4"),
}
for _filename, _identity in EXCLUDED_CODE_IDENTITIES.items():
    FROZEN_FILES[f"authority/penn-state/source/ClassNotes/Code/{_filename}"] = _identity


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


def artifact(record_id: str, artifact_kind: str, path: str, **extra: Any) -> dict[str, Any]:
    size, digest = file_info(path)
    record = common("artifact", record_id, "current")
    record.update({
        "artifact_kind": artifact_kind,
        "path": path,
        "bytes": size,
        "sha256": digest,
        "hash_algorithm": "sha256-raw-bytes",
    })
    record.update(extra)
    return record


CONCEPT_SPECS: list[tuple[str, str, list[str], str]] = [
    ("concept.penn.multivariate-newton-direction", "multivariate Newton direction for maximization", ["concept.gradient"], "smooth numerical optimization"),
    ("concept.penn.pure-newton-method", "pure multivariate Newton method", ["concept.penn.multivariate-newton-direction"], "smooth numerical optimization"),
    ("concept.penn.variable-step-newton", "variable-step Newton method", ["concept.penn.multivariate-newton-direction", "concept.penn.backtracking-line-search"], "smooth numerical optimization"),
    ("concept.penn.indefinite-hessian-newton-failure", "Newton-direction failure under an indefinite Hessian", ["concept.penn.multivariate-newton-direction"], "smooth numerical optimization"),
    ("concept.penn.induced-matrix-norm", "Euclidean induced matrix norm", [], "numerical linear algebra"),
    ("concept.penn.local-multivariate-newton-convergence", "local convergence of multivariate pure Newton iteration", ["concept.penn.pure-newton-method", "concept.penn.induced-matrix-norm"], "numerical analysis"),
    ("concept.penn.newton-quadratic-error-bound", "quadratic error bound for multivariate Newton iteration", ["concept.penn.local-multivariate-newton-convergence"], "numerical analysis"),
    ("concept.penn.gradient-newton-hybrid", "gradient-Newton globalization hybrid", ["concept.penn.gradient-ascent", "concept.penn.variable-step-newton"], "smooth numerical optimization"),
    ("concept.penn.modified-cholesky", "modified Cholesky factorization", [], "numerical linear algebra"),
    ("concept.penn.positive-definite-hessian-surrogate", "positive-definite surrogate for the negative Hessian", ["concept.penn.modified-cholesky"], "numerical linear algebra"),
    ("concept.penn.triangular-newton-solve", "triangular solves for a corrected Newton direction", ["concept.penn.positive-definite-hessian-surrogate"], "numerical linear algebra"),
    ("concept.penn.corrected-newton-method", "corrected Newton method", ["concept.penn.variable-step-newton", "concept.penn.modified-cholesky"], "smooth numerical optimization"),
    ("concept.penn.corrected-newton-stationarity", "stationarity of uniformly safeguarded corrected Newton iterates", ["concept.penn.corrected-newton-method", "concept.penn.gradient-related-directions"], "smooth numerical optimization"),
    ("concept.penn.eventual-uncorrected-newton", "eventual uncorrected Newton behavior", ["concept.penn.corrected-newton-method", "concept.penn.superlinear-convergence"], "numerical analysis"),
]

TERM_SPECS: list[tuple[str, str, str, str, int]] = [
    ("term.penn.multivariate-newton-direction", "concept.penn.multivariate-newton-direction", "multivariate Newton direction", "arah Newton multivariabel", 1),
    ("term.penn.pure-newton-method", "concept.penn.pure-newton-method", "pure Newton method", "metode Newton murni", 1),
    ("term.penn.variable-step-newton", "concept.penn.variable-step-newton", "variable-step Newton method", "metode Newton dengan panjang langkah variabel", 1),
    ("term.penn.indefinite-hessian-newton-failure", "concept.penn.indefinite-hessian-newton-failure", "indefinite-Hessian Newton failure", "kegagalan Newton akibat Hessian tak tentu", 2),
    ("term.penn.induced-matrix-norm", "concept.penn.induced-matrix-norm", "induced matrix norm", "norma matriks terinduksi", 2),
    ("term.penn.local-multivariate-newton-convergence", "concept.penn.local-multivariate-newton-convergence", "local multivariate Newton convergence", "konvergensi lokal Newton multivariabel", 3),
    ("term.penn.newton-quadratic-error-bound", "concept.penn.newton-quadratic-error-bound", "quadratic error bound", "taksiran galat kuadratik", 3),
    ("term.penn.gradient-newton-hybrid", "concept.penn.gradient-newton-hybrid", "gradient-Newton hybrid", "hibrida gradien--Newton", 4),
    ("term.penn.modified-cholesky", "concept.penn.modified-cholesky", "modified Cholesky factorization", "dekomposisi Cholesky termodifikasi", 5),
    ("term.penn.positive-definite-hessian-surrogate", "concept.penn.positive-definite-hessian-surrogate", "positive-definite Hessian surrogate", "pengganti Hessian definit positif", 5),
    ("term.penn.triangular-newton-solve", "concept.penn.triangular-newton-solve", "triangular solve", "penyelesaian segitiga", 5),
    ("term.penn.corrected-newton-method", "concept.penn.corrected-newton-method", "corrected Newton method", "metode Newton terkoreksi", 6),
    ("term.penn.corrected-newton-stationarity", "concept.penn.corrected-newton-stationarity", "corrected-Newton stationarity", "kestasioneran Newton terkoreksi", 7),
    ("term.penn.eventual-uncorrected-newton", "concept.penn.eventual-uncorrected-newton", "eventual uncorrected Newton behavior", "perilaku Newton tak terkoreksi pada akhirnya", 7),
]

SEGMENT_SPECS: list[tuple[int, int, int, str, str, list[str]]] = [
    (1, 1, 38, "Newton direction, variable-step algorithm, and quartic example", "Arah Newton, algoritma langkah variabel, dan contoh kuartik", ["concept.penn.multivariate-newton-direction", "concept.penn.pure-newton-method", "concept.penn.variable-step-newton"]),
    (2, 39, 74, "Indefinite-Hessian failure and induced matrix norm", "Kegagalan Hessian tak tentu dan norma matriks terinduksi", ["concept.penn.indefinite-hessian-newton-failure", "concept.penn.induced-matrix-norm"]),
    (3, 75, 148, "Local Newton convergence and quadratic error bound", "Konvergensi lokal Newton dan taksiran galat kuadratik", ["concept.penn.local-multivariate-newton-convergence", "concept.penn.newton-quadratic-error-bound"]),
    (4, 149, 178, "Gradient-Newton globalization hybrid", "Hibrida globalisasi gradien--Newton", ["concept.penn.gradient-newton-hybrid"]),
    (5, 179, 206, "Modified Cholesky and triangular direction solves", "Cholesky termodifikasi dan penyelesaian segitiga", ["concept.penn.modified-cholesky", "concept.penn.positive-definite-hessian-surrogate", "concept.penn.triangular-newton-solve"]),
    (6, 207, 277, "Corrected factor example and corrected Newton algorithm", "Contoh faktor terkoreksi dan algoritma Newton terkoreksi", ["concept.penn.modified-cholesky", "concept.penn.corrected-newton-method"]),
    (7, 278, 317, "Stationarity and eventual uncorrected superlinear behavior", "Kestasioneran dan perilaku superlinear tanpa koreksi pada akhirnya", ["concept.penn.corrected-newton-stationarity", "concept.penn.eventual-uncorrected-newton"]),
]

SEGMENT_DEFINITION_SPECS: list[tuple[int, str]] = [
    (1, "concept.penn.multivariate-newton-direction"),
    (1, "concept.penn.pure-newton-method"),
    (1, "concept.penn.variable-step-newton"),
    (2, "concept.penn.indefinite-hessian-newton-failure"),
    (2, "concept.penn.induced-matrix-norm"),
    (3, "concept.penn.local-multivariate-newton-convergence"),
    (3, "concept.penn.newton-quadratic-error-bound"),
    (4, "concept.penn.gradient-newton-hybrid"),
    (5, "concept.penn.modified-cholesky"),
    (5, "concept.penn.positive-definite-hessian-surrogate"),
    (5, "concept.penn.triangular-newton-solve"),
    (6, "concept.penn.corrected-newton-method"),
    (7, "concept.penn.corrected-newton-stationarity"),
    (7, "concept.penn.eventual-uncorrected-newton"),
]

EXERCISE_CONCEPTS = [
    "concept.penn.variable-step-newton",
    "concept.penn.indefinite-hessian-newton-failure",
    "concept.penn.gradient-newton-hybrid",
    "concept.penn.eventual-uncorrected-newton",
    "concept.penn.eventual-uncorrected-newton",
]

ALGORITHM_SPECS: list[tuple[str, str, str, tuple[int, ...], list[str]]] = [
    ("surface.penn.v1.ch05.algorithm01", "concept.penn.variable-step-newton", "Independent two-part variable-step Newton pseudocode", (0, 1), ["NewtonsMethodGeneral-1.mpl", "NewtonsMethodGeneral-2.mpl"]),
    ("surface.penn.v1.ch05.algorithm02", "concept.penn.modified-cholesky", "Independent modified-Cholesky pseudocode", (2,), ["ModifiedCholesky.mpl"]),
    ("surface.penn.v1.ch05.algorithm03", "concept.penn.corrected-newton-method", "Independent two-part corrected-Newton pseudocode", (3, 4), ["ModifiedNewtonsMethod-1.mpl", "ModifiedNewtonsMethod-2.mpl"]),
]

ASSET_SPECS: list[tuple[str, str, str, int, str]] = [
    ("asset.penn.v1.ch05.newton-method", "NewtonsMethod.pdf", "concept.penn.pure-newton-method", 1, "Pure-Newton path on a concave quartic objective."),
    ("asset.penn.v1.ch05.double-peak", "DoublePeak.pdf", "concept.penn.indefinite-hessian-newton-failure", 2, "Double-peak objective with maxima, a minimum, and saddle points."),
    ("asset.penn.v1.ch05.gradient-newton-hybrid", "GaussModifiedNewtonsMethod.pdf", "concept.penn.gradient-newton-hybrid", 4, "Gradient-Newton hybrid path to the positive-y maximum."),
    ("asset.penn.v1.ch05.modified-newton", "ModifiedNewton.pdf", "concept.penn.corrected-newton-method", 7, "Corrected-Newton path using a positive-definite Cholesky surrogate."),
]

GENERATED_CONCEPT_IDS = {item[0] for item in CONCEPT_SPECS}
GENERATED_TERM_IDS = {item[0] for item in TERM_SPECS}
GENERATED_EXACT_IDS = {
    UNIT_ID,
    SOURCE_RIGHTS_ID,
    TARGET_RIGHTS_ID,
    "rights.o015-penn-ch05-wrapper",
    "rights.o015-penn-ch05-figures",
    "rights.o015-penn-ch05-bibliography",
    "rights.o015-penn-ch05-bridges",
    "rights.o015-penn-ch05-maple-excluded",
    "rights.o015-penn-ch05-audit",
    "rights.o015-penn-ch05-solver",
    "rights.o015-penn-ch05-rereview",
    "rights.o015-penn-ch05-visual",
    "artifact.o015.backend-generator-penn-ch05",
    "artifact.o015.backend-validator-penn-ch05",
}


def is_generated(record: dict[str, Any]) -> bool:
    record_id = record.get("id", "")
    if record.get("responsible_workflow") == WORKFLOW:
        return True
    if record_id in GENERATED_CONCEPT_IDS | GENERATED_TERM_IDS | GENERATED_EXACT_IDS:
        return True
    return record_id.startswith((
        "d90.penn.v1.ch05.",
        "surface.penn.v1.ch05.",
        "asset.penn.v1.ch05.",
        "qa.o015.penn-ch05.",
        "relation.penn.ch05.",
    )) or record_id in {
        f"correction.o015-penn-adv-{number:04d}" for number in range(38, 50)
    } or (record_id.startswith("artifact.penn.") and record_id.endswith("-ch05"))


for relative, expected in FROZEN_FILES.items():
    actual = file_info(relative)
    if actual != expected:
        raise ValueError(
            f"frozen Penn Chapter 5 artifact differs: {relative}: "
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
        f"pre-Chapter-5 baseline has {len(records)} records, expected {BASELINE_RECORD_COUNT}"
    )

incoming_baseline_sha256 = record_set_sha256(records)
if incoming_baseline_sha256 not in {
    ORIGINAL_BASELINE_RECORD_SET_SHA256,
    PRIOR_REFRESHED_BASELINE_RECORD_SET_SHA256,
    REFRESHED_BASELINE_RECORD_SET_SHA256,
}:
    raise ValueError(
        "pre-Chapter-5 baseline differs beyond the enumerated refresh: "
        f"found {incoming_baseline_sha256}"
    )

baseline_semantic = [record for record in records if record.get("entity_type") != "artifact"]
if (
    len(baseline_semantic) != BASELINE_SEMANTIC_COUNT
    or record_set_sha256(baseline_semantic) != BASELINE_SEMANTIC_RECORD_SET_SHA256
):
    raise ValueError("immutable 999-record semantic baseline differs")

refresh_ids = set(REFRESH_SPECS)
baseline_immutable_artifacts = [
    record for record in records
    if record.get("entity_type") == "artifact" and record.get("id") not in refresh_ids
]
if (
    len(baseline_immutable_artifacts) != BASELINE_IMMUTABLE_ARTIFACT_COUNT
    or record_set_sha256(baseline_immutable_artifacts)
    != BASELINE_IMMUTABLE_ARTIFACT_RECORD_SET_SHA256
):
    raise ValueError("immutable 126-record baseline artifact set differs")

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
    if file_info(record["path"]) != (record.get("bytes"), record.get("sha256")):
        live_artifact_mismatch_ids.append(record["id"])

if incoming_baseline_sha256 == ORIGINAL_BASELINE_RECORD_SET_SHA256:
    expected_incoming_mismatches = sorted(refresh_ids)
elif incoming_baseline_sha256 == PRIOR_REFRESHED_BASELINE_RECORD_SET_SHA256:
    expected_incoming_mismatches = sorted(
        {
            "artifact.o015.component-rights",
            "artifact.o015.coverage-overlap",
        }
    )
else:
    expected_incoming_mismatches = []
if sorted(live_artifact_mismatch_ids) != expected_incoming_mismatches:
    raise ValueError(
        "live baseline artifact mismatches differ from the enumerated transaction: "
        f"expected={expected_incoming_mismatches}, found={sorted(live_artifact_mismatch_ids)}"
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
    "concept.penn.gradient-ascent",
    "concept.penn.backtracking-line-search",
    "concept.penn.gradient-related-directions",
    "concept.penn.superlinear-convergence",
    "artifact.penn.authority-archive",
    "artifact.penn.authority-pdf",
    "artifact.o015.source-authority",
    *refresh_ids,
}
missing_required_baseline = sorted(required_baseline_ids - baseline_ids)
if missing_required_baseline:
    raise ValueError(f"Chapter 5 prerequisite closure is missing: {missing_required_baseline}")

generated_ids: set[str] = set()


def add(record: dict[str, Any]) -> None:
    record_id = record["id"]
    if record_id in baseline_ids or record_id in generated_ids:
        raise ValueError(f"stable-ID collision while adding Penn Chapter 5: {record_id}")
    generated_ids.add(record_id)
    records.append(record)


source_text = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
target_text = (ROOT / TARGET_PATH).read_text(encoding="utf-8")
wrapper_text = (ROOT / WRAPPER_PATH).read_text(encoding="utf-8")
log_text = (ROOT / LOG_PATH).read_text(encoding="utf-8", errors="replace")
structure_report = json.loads((ROOT / STRUCTURE_REPORT_PATH).read_text(encoding="utf-8"))
solver_results = json.loads((ROOT / SOLVER_RESULTS_PATH).read_text(encoding="utf-8"))
visual_qa = json.loads((ROOT / VISUAL_QA_PATH).read_text(encoding="utf-8"))
rereview_text = (ROOT / REREVIEW_PATH).read_text(encoding="utf-8")
source_audit_text = (ROOT / SOURCE_AUDIT_PATH).read_text(encoding="utf-8")
proposal_records = [
    json.loads(line)
    for line in (ROOT / PROPOSED_LEDGER_PATH).read_text(encoding="utf-8").splitlines()
    if line
]
proposal_ids = [record.get("event_id") for record in proposal_records]
if proposal_ids != EXPECTED_PROPOSAL_IDS or len(set(proposal_ids)) != 12:
    raise ValueError("Penn Chapter 5 proposal event closure differs")

shared_ledger_records = [
    json.loads(line)
    for line in SHARED_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    if line
]
if len({record.get("event_id") for record in shared_ledger_records}) != len(shared_ledger_records):
    raise ValueError("shared adverse ledger contains duplicate event IDs")
if shared_ledger_records[-len(proposal_records) :] != proposal_records:
    raise ValueError("Penn Chapter 5 proposals are not the exact shared-ledger tail")

with COMPONENT_RIGHTS_PATH.open("r", encoding="utf-8", newline="") as handle:
    rights_rows = list(csv.DictReader(handle))
rights_by_component = {row["component_id"]: row for row in rights_rows}
required_component_ids = {
    "o015-penn-maple",
    "o015-penn-ch05-text",
    "o015-penn-ch05-figures",
    "o015-penn-id-unit-05",
    "o015-penn-id-wrapper-05",
    "o015-penn-local-bbl-05",
    "o015-penn-original-bridges-05",
    "o015-solver-validation-penn-05",
    "o015-structural-audit-penn-05",
    "o015-independent-rereview-penn-05",
    "o015-visual-qa-penn-05",
    "o015-backend-tooling",
}
if not required_component_ids.issubset(rights_by_component):
    raise ValueError("Chapter 5 component-rights row closure differs")
if rights_by_component["o015-penn-maple"]["status"] != "excluded":
    raise ValueError("Penn Maple component is not excluded")
if rights_by_component["o015-backend-tooling"]["path"] != (
    "qa/extend_backend_penn_ch05.py + qa/validate_backend_penn_ch05.py + earlier unit generators and validators"
):
    raise ValueError("Chapter 5 backend-tooling rights binding differs")

coverage_text = COVERAGE_OVERLAP_PATH.read_text(encoding="utf-8")
coverage_overlap_pass = all(
    phrase in coverage_text
    for phrase in (
        "Habring Chapters 3--9 and Penn Chapters 3--5 form an admitted optional numerical/modern-algorithm companion.",
        "Newton, globalization, and modified-Cholesky correction.",
        "O018 / D130 owns LP/MIP modelling",
        "Fourteen Penn Maple/legacy listing inputs encountered through Chapter 5 remain excluded",
        "No automatic Penn source-order expansion continues after the Chapter 5 preservation boundary.",
    )
)
if not coverage_overlap_pass:
    raise ValueError("Chapter 5 O018 non-overlap closure differs")

structure_gates = structure_report.get("gates", [])
audit_pass = (
    structure_report.get("status") == "PASS"
    and structure_report.get("failures") == []
    and len(structure_gates) == 17
    and all(gate.get("pass") is True for gate in structure_gates)
)
formula_inventory = structure_report.get("formula_inventory", {})
formula_pass = (
    len(formula_inventory.get("source", [])) == 35
    and len(formula_inventory.get("target", [])) == 35
    and [item.get("environment") for item in formula_inventory.get("source", [])]
    == [item.get("environment") for item in formula_inventory.get("target", [])]
)
solver_pass = (
    solver_results.get("status") == "PASS"
    and solver_results.get("failures") == []
    and len(solver_results.get("gates", [])) == 7
    and all(gate.get("pass") is True for gate in solver_results.get("gates", []))
)
visual_pass = (
    visual_qa.get("inspection", {}).get("result") == "pass"
    and visual_qa.get("pdf", {}).get("pages") == 15
    and visual_qa.get("pdf", {}).get("searchable_pages") == 15
    and visual_qa.get("pdf", {}).get("font_resources_without_tounicode") == 0
    and visual_qa.get("pdf", {}).get("canonical_and_repro_builds_byte_identical") is True
)
rereview_pass = all(
    phrase in rereview_text
    for phrase in (
        "Disposition: **PASS",
        "| Remaining after the narrow corrections below | 0 | 0 | 0 |",
        "No exercise, figure, theorem, proof, example, citation, formula environment",
    )
)
source_audit_pass = all(
    phrase in source_audit_text
    for phrase in (
        "Reader admission: PASS",
        "Twelve exact records `O015-PENN-ADV-0038` through",
        "The lawful complete Chapter 5 reader passes",
    )
)

if "CC BY-NC-SA 3.0 US" not in wrapper_text:
    raise ValueError("Penn Chapter 5 wrapper lacks the exact license notice")
if "tidak" not in wrapper_text.lower() or "mendukung" not in wrapper_text.lower():
    raise ValueError("Penn Chapter 5 wrapper lacks non-endorsement language")
if source_text.count(r"\lstinputlisting") != 5:
    raise ValueError("Penn Chapter 5 source must expose exactly five listing calls")
if r"\lstinputlisting" in target_text or "Code/" in target_text:
    raise ValueError("Penn Chapter 5 target retains an excluded code dependency")

output_match = re.search(r"Output written on .*?\((\d+) pages?", log_text, re.DOTALL)
pdf_pages = int(output_match.group(1)) if output_match else 0
build_blockers = [
    pattern for pattern in (
        "LaTeX Error",
        "Undefined control sequence",
        "There were undefined references",
        "Citation " + chr(96),
        "Overfull \\hbox",
        "Missing character",
        "Rerun to get cross-references right",
    ) if pattern in log_text
]
underfull_count = log_text.count("Underfull \\hbox")
build_pass = (
    pdf_pages == 15
    and not build_blockers
    and underfull_count == 1
    and "at lines 397--397" in log_text
)

if not all((
    audit_pass,
    formula_pass,
    solver_pass,
    visual_pass,
    rereview_pass,
    source_audit_pass,
    build_pass,
    coverage_overlap_pass,
)):
    raise ValueError("Penn Chapter 5 admission gates are not all closed")

admission_state = "admitted_reader"

unit = common("unit", UNIT_ID, "built")
unit.update({
    "edition_id": SOURCE_EDITION_ID,
    "source_edition_id": SOURCE_EDITION_ID,
    "target_edition_id": TARGET_EDITION_ID,
    "parent_id": ROOT_UNIT_ID,
    "unit_kind": "chapter",
    "order": 5,
    "source_local_id": "Section5",
    "source_local_label": "Newton's Method and Corrections",
    "target_local_label": "Metode Newton dan Koreksinya",
    "source_locator": f"{SOURCE_PATH}:1-317",
    "target_locator": f"{TARGET_PATH}:1-400",
    "rights_id": TARGET_RIGHTS_ID,
    "translation_state": "built",
    "admission_state": admission_state,
    "publication_state": "unpublished_working_edition",
    "next_source_order_unit": "Section6.tex:1",
})
add(unit)

rights_specs: list[dict[str, Any]] = [
    {
        "id": SOURCE_RIGHTS_ID,
        "status": "admitted",
        "component_id": "o015-penn-ch05-text",
        "path": SOURCE_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/lecture_notes/",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["attribution", "identify changes", "noncommercial use", "ShareAlike", "license link", "no implied endorsement"],
        "notes": "Complete frozen Chapter 5 source from editable archive v1.0.",
    },
    {
        "id": TARGET_RIGHTS_ID,
        "status": "derivative",
        "component_id": "o015-penn-id-unit-05",
        "path": TARGET_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/lecture_notes/",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["attribute Griffin, Miller, Mercer, and Penn source", "identify Indonesian translation and corrections", "noncommercial use", "ShareAlike", "license link", "no implied endorsement"],
        "notes": "Complete admitted Chapter 5 Indonesian derivative.",
    },
    {
        "id": "rights.o015-penn-ch05-wrapper",
        "status": "derivative",
        "component_id": "o015-penn-id-wrapper-05",
        "path": WRAPPER_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/lecture_notes/",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["retain attribution", "retain correction appendix", "retain non-endorsement", "retain ShareAlike"],
        "notes": "Standalone reader wrapper with four frozen prerequisite anchors.",
    },
    {
        "id": "rights.o015-penn-ch05-figures",
        "status": "admitted_with_source_level_notice",
        "component_id": "o015-penn-ch05-figures",
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
        "id": "rights.o015-penn-ch05-bibliography",
        "status": "adapted_with_caveat",
        "component_id": "o015-penn-local-bbl-05",
        "path": BIB_PATH,
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "CC BY-NC-SA 3.0 US",
        "authority_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": True,
        "required_handling": ["retain attribution", "identify bounded excerpt", "preserve opaque bundled bibliography evidence"],
        "notes": "Exact one-entry Bert99 excerpt; source bibliography databases are absent.",
    },
    {
        "id": "rights.o015-penn-ch05-bridges",
        "status": "project_authored_derivative_component",
        "component_id": "o015-penn-original-bridges-05",
        "path": TARGET_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "original bridge material inside CC BY-NC-SA 3.0 US derivative",
        "authority_url": TARGET_PATH,
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
        "translation_permitted": False,
        "required_handling": ["identify independent authorship", "do not claim code identity with Maple source", "retain ShareAlike derivative terms"],
        "notes": "Three independent pseudocode surfaces replace five excluded Maple listings.",
    },
    {
        "id": "rights.o015-penn-ch05-maple-excluded",
        "status": "excluded",
        "component_id": "o015-penn-maple",
        "path": "authority/penn-state/source/ClassNotes/Code",
        "source_authority_id": "o015-penn-math555-v1.0-source",
        "rights_expression": "unclear/external",
        "authority_url": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip",
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["do not translate", "do not redistribute as admitted code", "replace only with independently authored pseudocode"],
        "notes": "Five Chapter 5 Maple listings remain excluded and are frozen only as audit inputs.",
    },
    {
        "id": "rights.o015-penn-ch05-audit",
        "status": "project_local",
        "component_id": "o015-structural-audit-penn-05",
        "path": AUDIT_SOURCE_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": AUDIT_SOURCE_PATH,
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with report and source-audit receipt", "retain frozen authority hashes"],
        "notes": "Deterministic structure, formula, reference, asset, and rights-exclusion audit.",
    },
    {
        "id": "rights.o015-penn-ch05-solver",
        "status": "project_local",
        "component_id": "o015-solver-validation-penn-05",
        "path": SOLVER_SOURCE_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": SOLVER_SOURCE_PATH,
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship source with deterministic result", "use open runtime"],
        "notes": "Seven fail-closed open symbolic and numerical gates.",
    },
    {
        "id": "rights.o015-penn-ch05-rereview",
        "status": "project_local",
        "component_id": "o015-independent-rereview-penn-05",
        "path": REREVIEW_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local QA evidence",
        "authority_url": REREVIEW_PATH,
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["ship exact frozen-target review", "retain resolved finding counts"],
        "notes": "Independent rereview closes with P1=0, P2=0, P3=0.",
    },
    {
        "id": "rights.o015-penn-ch05-visual",
        "status": "project_local",
        "component_id": "o015-visual-qa-penn-05",
        "path": VISUAL_QA_PATH,
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local QA evidence",
        "authority_url": VISUAL_QA_PATH,
        "license_url": None,
        "translation_permitted": False,
        "required_handling": ["retain deterministic render identity", "do not claim tagged PDF"],
        "notes": "All-page visual and bounded accessibility receipt.",
    },
]
for spec in rights_specs:
    rights = common("rights", spec["id"], spec["status"])
    rights.update({key: value for key, value in spec.items() if key not in {"id", "status"}})
    add(rights)

for record_id, label, prerequisites, domain in CONCEPT_SPECS:
    concept = common("concept", record_id, "current")
    concept.update({"canonical_label": label, "prerequisite_ids": prerequisites, "domain": domain})
    add(concept)

for record_id, concept_id, source_term, preferred, segment_order in TERM_SPECS:
    term = common("term", record_id, "accepted")
    term.update({
        "concept_id": concept_id,
        "locale": "id-ID",
        "source_term": source_term,
        "preferred": preferred,
        "variants": [],
        "rejected_forms": [],
        "scope": "smooth numerical optimization, Newton methods, and numerical linear algebra",
        "register": "formal",
        "evidence_segment_ids": [f"d90.penn.v1.ch05.seg{segment_order:04d}"],
        "examples": [preferred],
        "rights_id": TARGET_RIGHTS_ID,
    })
    add(term)

target_lines = target_text.splitlines()
marker_pattern = re.compile(r"^% segment-id: (d90\.penn\.v1\.ch05\.seg\d{4})$")
markers = [
    (line_number, match.group(1))
    for line_number, line in enumerate(target_lines, start=1)
    if (match := marker_pattern.fullmatch(line))
]
expected_marker_ids = [f"d90.penn.v1.ch05.seg{order:04d}" for order in range(1, 8)]
if [item[1] for item in markers] != expected_marker_ids:
    raise ValueError("Chapter 5 target segment marker closure/order differs")

for index, (order, source_start, source_end, source_label, target_label, concept_ids) in enumerate(SEGMENT_SPECS):
    marker_line, record_id = markers[index]
    target_start = marker_line + 1
    target_end = len(target_lines) if index == len(markers) - 1 else markers[index + 1][0] - 2
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, source_start, source_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, target_start, target_end)
    segment = common("segment", record_id, "current")
    segment.update({
        "unit_id": UNIT_ID,
        "order": order,
        "source_local_id": f"Section5-lines-{source_start}-{source_end}",
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
            "qa.o015.penn-ch05.structure",
            "qa.o015.penn-ch05.formulas",
            "qa.o015.penn-ch05.corrections",
            "qa.o015.penn-ch05.solver",
            "qa.o015.penn-ch05.build",
            "qa.o015.penn-ch05.visual",
            "qa.o015.penn-ch05.rights",
            "qa.o015.penn-ch05.overlap",
        ],
    })
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
if len(source_exercises) != 5 or len(target_exercises) != 5:
    raise ValueError("Chapter 5 exercise closure differs")
for order, ((source_start, source_end), (target_start, target_end), concept_id) in enumerate(
    zip(source_exercises, target_exercises, EXERCISE_CONCEPTS), start=1
):
    segment_order = next(
        segment_order for segment_order, start, end, *_ in SEGMENT_SPECS
        if start <= source_start <= end
    )
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, source_start, source_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, target_start, target_end)
    surface = common("learning_surface", f"surface.penn.v1.ch05.exercise{order:02d}", "present")
    surface.update({
        "unit_id": UNIT_ID,
        "surface_type": "exercise_prompt",
        "presence": "present",
        "order": order,
        "source_local_id": f"exercise{order:02d}",
        "source_local_label": f"Source-order exercise {order}",
        "target_local_label": f"Latihan urutan sumber {order}",
        "related_segment_ids": [f"d90.penn.v1.ch05.seg{segment_order:04d}"],
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
    })
    add(surface)

source_algorithms = find_environment_spans(source_text, "cgalgorithm")
target_algorithms = find_environment_spans(target_text, "cgalgorithm")
if len(source_algorithms) != 5 or len(target_algorithms) != 5:
    raise ValueError("Chapter 5 algorithm environment closure differs")
for order, (record_id, concept_id, label, indices, excluded_files) in enumerate(ALGORITHM_SPECS, start=1):
    source_start = source_algorithms[indices[0]][0]
    source_end = source_algorithms[indices[-1]][1]
    target_start = target_algorithms[indices[0]][0]
    target_end = target_algorithms[indices[-1]][1]
    segment_order = next(
        segment_order for segment_order, start, end, *_ in SEGMENT_SPECS
        if start <= source_start <= end
    )
    source_bytes, source_digest = normalized_slice(SOURCE_PATH, source_start, source_end)
    target_bytes, target_digest = normalized_slice(TARGET_PATH, target_start, target_end)
    surface = common("learning_surface", record_id, "present")
    surface.update({
        "unit_id": UNIT_ID,
        "surface_type": "algorithm_pseudocode",
        "presence": "present",
        "order": order,
        "source_local_id": f"excluded-maple-algorithm-{order:02d}",
        "source_local_label": label,
        "target_local_label": label,
        "related_segment_ids": [f"d90.penn.v1.ch05.seg{segment_order:04d}"],
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
        "rights_id": "rights.o015-penn-ch05-bridges",
        "disposition": "independent_replacement_for_excluded_maple",
        "excluded_source_component_rights_id": "rights.o015-penn-ch05-maple-excluded",
        "excluded_source_input_paths": [
            f"authority/penn-state/source/ClassNotes/Code/{filename}"
            for filename in excluded_files
        ],
        "excluded_source_input_count": len(excluded_files),
    })
    add(surface)

for record_id, filename, concept_id, segment_order, description in ASSET_SPECS:
    source_relative = f"authority/penn-state/source/ClassNotes/Figures/{filename}"
    target_relative = f"source/id-ID/figures/{filename}"
    source_bytes, source_digest = file_info(source_relative)
    target_bytes, target_digest = file_info(target_relative)
    if (source_bytes, source_digest) != (target_bytes, target_digest):
        raise ValueError(f"Penn Chapter 5 figure is not byte-identical: {filename}")
    asset_record = common("asset", record_id, "current")
    asset_record.update({
        "asset_kind": "vector_pdf_figure",
        "source_edition_id": SOURCE_EDITION_ID,
        "target_edition_id": TARGET_EDITION_ID,
        "source_path": source_relative,
        "source_bytes": source_bytes,
        "source_sha256": source_digest,
        "target_path": target_relative,
        "target_bytes": target_bytes,
        "target_sha256": target_digest,
        "rights_id": "rights.o015-penn-ch05-figures",
        "related_segment_ids": [f"d90.penn.v1.ch05.seg{segment_order:04d}"],
        "concept_id": concept_id,
        "adaptation": "byte-identical source-archive copy; Indonesian caption is in the translated TeX",
        "accessibility_description": description,
    })
    add(asset_record)

for event in proposal_records:
    ranges = [
        (int(start), int(end))
        for start, end in re.findall(
            r"ClassNotes/Section5\.tex:(\d+)-(\d+)", event.get("source", "")
        )
    ]
    if not ranges:
        raise ValueError(f"{event['event_id']}: no Section5 source locator")
    affected = [
        f"d90.penn.v1.ch05.seg{order:04d}"
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
    correction.update({
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
        "proposal_artifact_id": "artifact.penn.proposed-ledger-ch05",
    })
    add(correction)

artifact_records = [
    artifact("artifact.penn.source-ch05", "source_tex", SOURCE_PATH, source_edition_id=SOURCE_EDITION_ID, rights_id=SOURCE_RIGHTS_ID),
    artifact("artifact.penn.target-ch05", "target_tex", TARGET_PATH, source_artifact_id="artifact.penn.source-ch05", target_edition_id=TARGET_EDITION_ID, rights_id=TARGET_RIGHTS_ID),
    artifact("artifact.penn.target-wrapper-ch05", "reader_wrapper_tex", WRAPPER_PATH, target_edition_id=TARGET_EDITION_ID, rights_id="rights.o015-penn-ch05-wrapper", input_artifact_ids=["artifact.penn.target-ch05", "artifact.penn.local-bibliography-ch05"]),
    artifact("artifact.penn.local-bibliography-ch05", "bounded_bibliography_excerpt", BIB_PATH, source_artifact_id="artifact.penn.authority-archive", target_edition_id=TARGET_EDITION_ID, rights_id="rights.o015-penn-ch05-bibliography"),
    artifact("artifact.penn.target-pdf-ch05", "reader_pdf", PDF_PATH, target_edition_id=TARGET_EDITION_ID, rights_id=TARGET_RIGHTS_ID, pages=pdf_pages, build_event_id="qa.o015.penn-ch05.build", accessibility="searchable 15-page id-ID PDF; untagged; all 137 font resources expose ToUnicode", input_artifact_ids=["artifact.penn.target-wrapper-ch05", "artifact.penn.target-ch05", "artifact.penn.local-bibliography-ch05"]),
    artifact("artifact.penn.build-log-ch05", "build_log", LOG_PATH, target_edition_id=TARGET_EDITION_ID, source_artifact_id="artifact.penn.target-wrapper-ch05"),
    artifact("artifact.penn.target-text-ch05", "qa_extract", TEXT_PATH, target_edition_id=TARGET_EDITION_ID, source_artifact_id="artifact.penn.target-pdf-ch05"),
    artifact("artifact.penn.audit-source-ch05", "qa_source", AUDIT_SOURCE_PATH, rights_id="rights.o015-penn-ch05-audit", toolchain="Python 3 standard library"),
    artifact("artifact.penn.structure-report-ch05", "qa_report", STRUCTURE_REPORT_PATH, source_artifact_id="artifact.penn.audit-source-ch05"),
    artifact("artifact.penn.proposed-ledger-ch05", "proposed_correction_ledger", PROPOSED_LEDGER_PATH, source_artifact_id="artifact.penn.source-ch05"),
    artifact("artifact.penn.solver-validator-ch05", "qa_source", SOLVER_SOURCE_PATH, rights_id="rights.o015-penn-ch05-solver", toolchain="Python / SymPy"),
    artifact("artifact.penn.solver-results-ch05", "qa_report", SOLVER_RESULTS_PATH, source_artifact_id="artifact.penn.solver-validator-ch05"),
    artifact("artifact.penn.visual-qa-ch05", "qa_report", VISUAL_QA_PATH, source_artifact_id="artifact.penn.target-pdf-ch05", rights_id="rights.o015-penn-ch05-visual"),
    artifact("artifact.penn.independent-rereview-ch05", "independent_review", REREVIEW_PATH, source_artifact_id="artifact.penn.target-ch05", rights_id="rights.o015-penn-ch05-rereview"),
    artifact("artifact.penn.source-audit-ch05", "admission_audit", SOURCE_AUDIT_PATH, source_artifact_id="artifact.penn.source-ch05", rights_id="rights.o015-penn-ch05-audit"),
    artifact("artifact.o015.backend-generator-penn-ch05", "qa_source", "qa/extend_backend_penn_ch05.py", toolchain="Python 3 standard library"),
    artifact("artifact.o015.backend-validator-penn-ch05", "backend_validator", "qa/validate_backend_penn_ch05.py", toolchain="Python 3 standard library"),
]
for record in artifact_records:
    add(record)

qa_specs: list[dict[str, Any]] = [
    {
        "id": "qa.o015.penn-ch05.source-freeze",
        "status": "pass",
        "event_type": "source",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.source-ch05", "artifact.penn.authority-archive", "artifact.penn.authority-pdf", "artifact.o015.source-authority"],
        "authority_id": "o015-penn-math555-v1.0-source",
        "source_sha256": FROZEN_FILES[SOURCE_PATH][1],
        "edition_distinction": "editable v1.0 is text authority; public v1.0.1 PDF is a correction witness",
    },
    {
        "id": "qa.o015.penn-ch05.structure",
        "status": "pass",
        "event_type": "topology",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.structure-report-ch05"],
        "segment_count": 7,
        "source_lines": 317,
        "target_lines": 400,
        "ordered_environment_count": 84,
        "label_count": 10,
    },
    {
        "id": "qa.o015.penn-ch05.formulas",
        "status": "pass",
        "event_type": "mathematics",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.structure-report-ch05", "artifact.penn.proposed-ledger-ch05"],
        "displayed_formula_surface_count": 35,
        "ordered_environment_sequence_preserved": True,
        "correction_event_count": 12,
    },
    {
        "id": "qa.o015.penn-ch05.corrections",
        "status": "pass",
        "event_type": "correction_ledger",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.proposed-ledger-ch05", "artifact.o015.adverse-ledger"],
        "event_ids": proposal_ids,
        "shared_ledger_state": "integrated",
        "shared_ledger_tail_exact": True,
        "collision_count": 0,
    },
    {
        "id": "qa.o015.penn-ch05.algorithms",
        "status": "pass",
        "event_type": "code_surface",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.target-ch05", "artifact.penn.structure-report-ch05"],
        "source_algorithm_environment_count": 5,
        "excluded_maple_listing_count": 5,
        "independent_replacement_count": 3,
        "retained_legacy_dependency_count": 0,
    },
    {
        "id": "qa.o015.penn-ch05.exercises",
        "status": "pass",
        "event_type": "learning_surface",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.structure-report-ch05"],
        "exercise_count": 5,
        "hint_count": 0,
        "answer_count": 0,
        "solution_count": 0,
    },
    {
        "id": "qa.o015.penn-ch05.solver",
        "status": "pass",
        "event_type": "computation",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.solver-results-ch05", "artifact.penn.solver-validator-ch05"],
        "gate_count": 7,
        "failed_gate_count": 0,
        "runtime": "Python / SymPy 1.13.1",
    },
    {
        "id": "qa.o015.penn-ch05.build",
        "status": "pass",
        "event_type": "build",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.target-pdf-ch05", "artifact.penn.build-log-ch05"],
        "pages": pdf_pages,
        "page_size": "A4",
        "errors": build_blockers,
        "accepted_underfull_caption_warning_count": underfull_count,
        "deterministic_rebuild": "byte-identical fixed-epoch builds",
    },
    {
        "id": "qa.o015.penn-ch05.visual",
        "status": "pass",
        "event_type": "visual",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.visual-qa-ch05", "artifact.penn.target-pdf-ch05"],
        "inspected_pages": [4, 5, 9, 10, 11, 12, 14],
        "all_page_contact_sheet_inspected": True,
        "blank_or_broken_page_count": 0,
    },
    {
        "id": "qa.o015.penn-ch05.accessibility",
        "status": "pass_with_limitation",
        "event_type": "accessibility",
        "result": "pass_with_limitation",
        "witness_artifact_ids": ["artifact.penn.visual-qa-ch05", "artifact.penn.target-pdf-ch05", "artifact.penn.target-text-ch05"],
        "checks": ["PDF language metadata is id-ID", "all 15 pages expose text", "all 137 font resources expose ToUnicode", "PDF has no forms or JavaScript"],
        "limitations": ["PDF is untagged", "semantic HTML and EPUB are not yet produced"],
    },
    {
        "id": "qa.o015.penn-ch05.math-rereview",
        "status": "pass",
        "event_type": "mathematics",
        "result": "pass",
        "witness_artifact_ids": ["artifact.penn.independent-rereview-ch05", "artifact.penn.structure-report-ch05", "artifact.penn.solver-results-ch05"],
        "remaining_defects": {"P1": 0, "P2": 0, "P3": 0},
        "resolved_findings": {"P2": 1, "P3": 3},
        "scope": "Independent complete source/target/proposal and computation rereview.",
    },
    {
        "id": "qa.o015.penn-ch05.language",
        "status": "not_recorded",
        "event_type": "language",
        "result": "not_recorded",
        "witness_artifact_ids": [],
        "gap": "No separate independent human/native-speaker Indonesian language-review receipt is recorded.",
    },
    {
        "id": "qa.o015.penn-ch05.rights",
        "status": "pass",
        "event_type": "rights",
        "result": "pass",
        "witness_artifact_ids": ["artifact.o015.component-rights", "artifact.penn.source-audit-ch05"],
        "component_ids": sorted(required_component_ids),
        "excluded_component_ids": ["o015-penn-maple"],
    },
    {
        "id": "qa.o015.penn-ch05.overlap",
        "status": "pass",
        "event_type": "coverage",
        "result": "pass",
        "witness_artifact_ids": ["artifact.o015.coverage-overlap", "artifact.penn.source-audit-ch05"],
        "excluded_lane": "O018",
        "next_source_order_cursor": "Section6.tex:1",
    },
]
for spec in qa_specs:
    qa = common("qa_event", spec["id"], spec["status"])
    qa.update({
        "unit_id": UNIT_ID,
        **{key: value for key, value in spec.items() if key not in {"id", "status"}},
    })
    add(qa)

relation_specs: list[tuple[str, str, str, str, str]] = [
    ("relation.penn.ch05.resource-contains-source-edition", "contains", RESOURCE_ID, SOURCE_EDITION_ID, "Frozen editable Penn work edition."),
    ("relation.penn.ch05.resource-contains-target-edition", "contains", RESOURCE_ID, TARGET_EDITION_ID, "Working Indonesian derivative edition."),
    ("relation.penn.ch05.source-edition-contains-unit", "contains", SOURCE_EDITION_ID, UNIT_ID, "Complete Section5 source unit."),
    ("relation.penn.ch05.target-edition-contains-unit", "contains", TARGET_EDITION_ID, UNIT_ID, "Complete Chapter 5 Indonesian reader unit."),
    ("relation.penn.ch05.work-contains-unit", "contains", ROOT_UNIT_ID, UNIT_ID, "Complete source-order Chapter 5."),
    ("relation.penn.ch05.ch04-precedes-ch05", "precedes", PREVIOUS_UNIT_ID, UNIT_ID, "Penn source-order continuation."),
    ("relation.penn.ch05.depends-on-gradient", "depends-on", UNIT_ID, "concept.gradient", "Gradient and Hessian calculus are prerequisites."),
    ("relation.penn.ch05.depends-on-line-search", "depends-on", UNIT_ID, "concept.penn.backtracking-line-search", "Safeguarded variable-step methods require Chapter 4 line search."),
    ("relation.penn.ch05.target-translates-source", "translates", "artifact.penn.target-ch05", "artifact.penn.source-ch05", "Complete contiguous id-ID translation."),
    ("relation.penn.ch05.wrapper-contains-target", "contains", "artifact.penn.target-wrapper-ch05", "artifact.penn.target-ch05", "Standalone licensed reader wrapper."),
    ("relation.penn.ch05.pdf-depends-on-wrapper", "depends-on", "artifact.penn.target-pdf-ch05", "artifact.penn.target-wrapper-ch05", "Deterministic reader build input."),
    ("relation.penn.ch05.pdf-depends-on-bibliography", "depends-on", "artifact.penn.target-pdf-ch05", "artifact.penn.local-bibliography-ch05", "Exact one-entry bibliography excerpt."),
    ("relation.penn.ch05.text-adapts-pdf", "adapts", "artifact.penn.target-text-ch05", "artifact.penn.target-pdf-ch05", "Searchability and accessibility witness."),
    ("relation.penn.ch05.bibliography-adapts-archive", "adapts", "artifact.penn.local-bibliography-ch05", "artifact.penn.authority-archive", "Exact Bert99 excerpt from bundled Math555.bbl."),
    ("relation.penn.ch05.structure-depends-on-audit", "depends-on", "artifact.penn.structure-report-ch05", "artifact.penn.audit-source-ch05", "Deterministic structural audit output."),
    ("relation.penn.ch05.solver-results-depend-on-validator", "depends-on", "artifact.penn.solver-results-ch05", "artifact.penn.solver-validator-ch05", "Deterministic open symbolic/numerical output."),
    ("relation.penn.ch05.visual-depends-on-pdf", "depends-on", "artifact.penn.visual-qa-ch05", "artifact.penn.target-pdf-ch05", "All-page render and inspection receipt."),
    ("relation.penn.ch05.rereview-depends-on-target", "depends-on", "artifact.penn.independent-rereview-ch05", "artifact.penn.target-ch05", "Frozen-target independent rereview."),
    ("relation.penn.ch05.source-audit-depends-on-structure", "depends-on", "artifact.penn.source-audit-ch05", "artifact.penn.structure-report-ch05", "Final reader admission source audit."),
    ("relation.penn.ch05.source-audit-depends-on-visual", "depends-on", "artifact.penn.source-audit-ch05", "artifact.penn.visual-qa-ch05", "Final admission visual evidence."),
]
for order in range(1, 8):
    relation_specs.append((
        f"relation.penn.ch05.contains-seg{order:04d}",
        "contains",
        UNIT_ID,
        f"d90.penn.v1.ch05.seg{order:04d}",
        "Ordered contiguous translation segment.",
    ))
for segment_order, concept_id in SEGMENT_DEFINITION_SPECS:
    suffix = concept_id.removeprefix("concept.penn.")
    relation_specs.append((
        f"relation.penn.ch05.seg{segment_order:04d}-defines-{suffix}",
        "defines",
        f"d90.penn.v1.ch05.seg{segment_order:04d}",
        concept_id,
        "Primary source-linked concept surface.",
    ))
for order, concept_id in enumerate(EXERCISE_CONCEPTS, start=1):
    relation_specs.append((
        f"relation.penn.ch05.exercise{order:02d}-exercises-{concept_id.removeprefix('concept.penn.')}",
        "exercises",
        f"surface.penn.v1.ch05.exercise{order:02d}",
        concept_id,
        "Source-order exercise prompt.",
    ))
for record_id, concept_id, label, _, _ in ALGORITHM_SPECS:
    relation_specs.append((
        f"relation.penn.ch05.{record_id.rsplit('.', 1)[-1]}-illustrates-{concept_id.removeprefix('concept.penn.')}",
        "illustrates",
        record_id,
        concept_id,
        label,
    ))
for asset_id, _, concept_id, _, description in ASSET_SPECS:
    relation_specs.append((
        f"relation.penn.ch05.{asset_id.rsplit('.', 1)[-1]}-illustrates-{concept_id.removeprefix('concept.penn.')}",
        "illustrates",
        asset_id,
        concept_id,
        description,
    ))

for record_id, relation_type, source_id, target_id, note in relation_specs:
    relation = common("relation", record_id, "current")
    relation.update({
        "relation_type": relation_type,
        "source_id": source_id,
        "target_id": target_id,
        "note": note,
    })
    add(relation)

final_by_id = {record["id"]: canonical_json(record) for record in records}
missing_baseline_ids = sorted(baseline_ids - set(final_by_id))
changed_baseline_ids = sorted(
    record_id for record_id in baseline_ids
    if final_by_id.get(record_id) != baseline_by_id[record_id]
)
if missing_baseline_ids or changed_baseline_ids:
    raise ValueError(
        "Chapter 5 extension changed the refreshed baseline: "
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
        writer.writerow([
            record["schema"],
            record["schema_version"],
            record["entity_type"],
            record["id"],
            canonical_json(record),
        ])

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
    "csv": {"bytes": file_info("backend/records.csv")[0], "sha256": file_info("backend/records.csv")[1]},
    "entity_counts": dict(sorted(Counter(record["entity_type"] for record in records).items())),
    "jsonl": {"bytes": file_info("backend/records.jsonl")[0], "sha256": file_info("backend/records.jsonl")[1]},
    "penn_ch05_added_entity_counts": dict(sorted(Counter(record["entity_type"] for record in added_records).items())),
    "penn_ch05_added_record_count": len(added_records),
    "penn_ch05_record_set_sha256": record_set_sha256(added_records),
    "record_count": len(records),
    "resource_edition_reuse_ids": [RESOURCE_ID, SOURCE_EDITION_ID, TARGET_EDITION_ID],
    "segment_count": 7,
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
