#!/usr/bin/env python3
"""Deterministically admit the MIT L01 pilot and Royer source closure.

The exact 1,300-record terminology-QA backend is the frozen baseline.  Nine
existing IDs are the complete mutation boundary: five curriculum-topology
records and three live control-artifact byte bindings.  Every other baseline
record is protected at canonical-record level.  Reruns remove and reconstruct
only this workflow's finite new-ID closure.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCHEMA_PATH = BACKEND / "backend_schema.json"
JSONL_PATH = BACKEND / "records.jsonl"
CSV_PATH = BACKEND / "records.csv"

RECORDED_AT = "2026-08-22T21:54:53Z"
WORKFLOW = "o015-mit-l01-royer-backend-v1"
RECORD_SCHEMA = "o015-modular-backend-record"
SCHEMA_VERSION = "1.0.0"

BASELINE_RECORD_COUNT = 1300
BASELINE_JSONL_BYTES = 953_701
BASELINE_JSONL_SHA256 = "315f1460a0f7e22256ffd95ed9d65b8bf81b987b58deb1a2b7ae719fdeb35a74"
BASELINE_CSV_BYTES = 1_143_371
BASELINE_CSV_SHA256 = "b0a417ce01ec076bbe57be40d9b3d1d2d1f3e75cf4688ce16350eb2916150b19"
BASELINE_RECORD_SET_SHA256 = "c7dbccfc8d408f6d3daf9f77e5429d0a65391c16b8832bf2e7b562764dce0cb6"
BASELINE_ID_SET_SHA256 = "43e632affd2c3bacf20c3739980d7b15af017bf40d9f80b488e95f153d53124a"
IMMUTABLE_BASELINE_COUNT = 1291
IMMUTABLE_BASELINE_RECORD_SET_SHA256 = "e979fecf16dbc04f8b65c8ade1d52a1fada347584c90ee47825807b5800d3511"

COURSE_ID = "course.d90.advanced-optimization-convex-analysis"
MIT_RESOURCE_ID = "resource.mit.ocw-6.253-convex-analysis-optimization"
MIT_SOURCE_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION_ID = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION_ID = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT_UNIT_ID = "unit.mit.ocw-6.253.spring-2012"
MIT_L01_UNIT_ID = "unit.mit.ocw-6.253.l01"
ROYER_RESOURCE_ID = "resource.royer.stochastic-gradient"
ROYER_EDITION_ID = "edition.royer.stochastic-gradient.2023-2024"
ROYER_ROOT_UNIT_ID = "unit.royer.stochastic-gradient.2023-2024"
ROYER_NOTES_UNIT_ID = "unit.royer.stochastic-gradient.2023-2024.notes"
ROYER_LAB01_UNIT_ID = "unit.royer.stochastic-gradient.2023-2024.lab01"
ROYER_LAB02_UNIT_ID = "unit.royer.stochastic-gradient.2023-2024.lab02"

MIT_PDF = (
    "authority/mit-ocw-6.253/course-archive/static_resources/"
    "6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
)
MIT_WITNESS = "source/en/mit-01-role-of-convexity-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-01-peran-kekonveksan-id.md"
MIT_HTML = "output/html/D90-MIT-01-peran-kekonveksan-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-01-peran-kekonveksan-id.pdf"
MIT_REPORT = "qa/MIT_L01_PILOT_VALIDATION.json"
MIT_BROWSER_QA = "qa/MIT_L01_BROWSER_QA.json"
MIT_REREVIEW = "qa/MIT_L01_INDEPENDENT_REREVIEW.md"
MIT_AUDIT = "00_control/MIT_L01_PILOT_AUDIT.md"
SOURCE_FREEZE = "00_control/MIT_ROYER_SOURCE_FREEZE.json"

ALLOWED_EXISTING_IDS = {
    COURSE_ID,
    "unit.habring.v1",
    "unit.penn.v1",
    "relation.penn.course-contains-work",
    "relation.penn.habring-ch09-precedes-ch03",
    "artifact.o015.source-authority",
    "artifact.o015.component-rights",
    "artifact.o015.adverse-ledger",
    "artifact.habring.worklog-ch09",
}
CONTROL_REFRESH_PATHS = {
    "artifact.o015.source-authority": "00_control/SOURCE_AUTHORITY.json",
    "artifact.o015.component-rights": "00_control/COMPONENT_RIGHTS.csv",
    "artifact.o015.adverse-ledger": "00_control/ADVERSE_LEDGER.jsonl",
    "artifact.habring.worklog-ch09": "qa/CHAPTER09_WORKLOG.md",
}

# These are the exact canonical baseline records in the two frozen backend
# files.  They make the allowlist independently auditable on idempotent reruns.
ORIGINAL_ALLOWED_RECORDS: dict[str, dict[str, Any]] = {
    COURSE_ID: {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "course", "id": COURSE_ID,
        "recorded_at": "2026-08-21T10:54:38Z",
        "responsible_workflow": "o015-first-unit-backend-v1", "status": "active",
        "program_id": "program.d90.id-id", "role": "D90",
        "title": "Analisis Optimisasi Lanjut dan Konveks",
        "prerequisite_ids": ["concept.convex-function", "concept.epigraph", "concept.frechet-derivative", "concept.hilbert-space"],
        "scope_note": "O015 excludes LP/IP, simplex, finite-dimensional LP duality, and OR modeling already owned by O018.",
    },
    "unit.habring.v1": {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "unit", "id": "unit.habring.v1",
        "recorded_at": "2026-08-21T10:54:38Z",
        "responsible_workflow": "o015-first-unit-backend-v1", "status": "active",
        "edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "source_edition_id": "edition.habring.convex-optimization.arxiv-2607-11664v1",
        "target_edition_id": "edition.habring.convex-optimization.id-id.v1",
        "unit_kind": "work", "order": 1, "source_local_id": "work-root",
        "source_local_label": "Lecture Notes: Convex Optimization",
        "target_local_label": "Optimisasi Konveks", "rights_id": "rights.o015-habring-text",
    },
    "unit.penn.v1": {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "unit", "id": "unit.penn.v1",
        "recorded_at": "2026-08-22T18:05:00Z",
        "responsible_workflow": "o015-penn-ch03-backend-v1", "status": "provisional",
        "edition_id": "edition.penn.math555.source-v1-0",
        "source_edition_id": "edition.penn.math555.source-v1-0",
        "target_edition_id": "edition.penn.math555.id-id.v1",
        "unit_kind": "work", "order": 2, "source_local_id": "work-root",
        "source_local_label": "Nonlinear Programming",
        "target_local_label": "Pemrograman Nonlinear",
        "rights_id": "rights.o015-penn-ch03-source",
        "admission_state": "candidate_ready_for_root_admission",
    },
    "relation.penn.course-contains-work": {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "relation", "id": "relation.penn.course-contains-work",
        "recorded_at": "2026-08-22T18:05:00Z",
        "responsible_workflow": "o015-penn-ch03-backend-v1", "status": "current",
        "relation_type": "contains", "source_id": COURSE_ID, "target_id": "unit.penn.v1",
        "note": "Penn is the smooth numerical-optimization donor.",
    },
    "relation.penn.habring-ch09-precedes-ch03": {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "relation", "id": "relation.penn.habring-ch09-precedes-ch03",
        "recorded_at": "2026-08-22T18:05:00Z",
        "responsible_workflow": "o015-penn-ch03-backend-v1", "status": "current",
        "relation_type": "precedes", "source_id": "unit.habring.v1.ch09",
        "target_id": "unit.penn.v1.ch03",
        "note": "Production cursor crosses from the admitted Habring module to the Penn donor.",
    },
    "artifact.o015.adverse-ledger": {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "artifact", "id": "artifact.o015.adverse-ledger",
        "recorded_at": "2026-08-21T10:54:38Z",
        "responsible_workflow": "o015-first-unit-backend-v1", "status": "current",
        "artifact_kind": "control_evidence", "path": "00_control/ADVERSE_LEDGER.jsonl",
        "bytes": 93480, "sha256": "c8d87cd7958e9beba30372e1fc70df7fe992970db780d8757c061854fb9075f0",
        "hash_algorithm": "sha256-raw-bytes", "toolchain": "not applicable",
    },
    "artifact.o015.component-rights": {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "artifact", "id": "artifact.o015.component-rights",
        "recorded_at": "2026-08-21T10:54:38Z",
        "responsible_workflow": "o015-first-unit-backend-v1", "status": "current",
        "artifact_kind": "control_evidence", "path": "00_control/COMPONENT_RIGHTS.csv",
        "bytes": 23258, "sha256": "51e08f77f709a945c8e53948ee466d7d06e75e469ef7fef4d7d269fc895e37e9",
        "hash_algorithm": "sha256-raw-bytes", "toolchain": "not applicable",
    },
    "artifact.o015.source-authority": {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "artifact", "id": "artifact.o015.source-authority",
        "recorded_at": "2026-08-21T10:54:38Z",
        "responsible_workflow": "o015-first-unit-backend-v1", "status": "current",
        "artifact_kind": "control_evidence", "path": "00_control/SOURCE_AUTHORITY.json",
        "bytes": 6832, "sha256": "6a1e00cf4f5088c183ae2f3424743218e12d91c17511551250d17aed9dd6fa13",
        "hash_algorithm": "sha256-raw-bytes", "toolchain": "not applicable",
    },
    "artifact.habring.worklog-ch09": {
        "schema": RECORD_SCHEMA, "schema_version": SCHEMA_VERSION,
        "entity_type": "artifact", "id": "artifact.habring.worklog-ch09",
        "recorded_at": "2026-08-22T16:45:00Z",
        "responsible_workflow": "o015-habring-ch09-backend-v1", "status": "current",
        "artifact_kind": "qa_receipt", "path": "qa/CHAPTER09_WORKLOG.md",
        "bytes": 9661, "sha256": "0527b8b61dee2ffccd493e8331b7d57f592ba3ec9b5ef87226c15cb1a342e99e",
        "hash_algorithm": "sha256-raw-bytes", "source_artifact_id": "artifact.habring.source-ch09",
    },
}

FROZEN_FILES: dict[str, tuple[int, str]] = {
    SOURCE_FREEZE: (40468, "a0a4c53273b9358b90289182b185aca1370d89a9388779c77413ab852fbf99c5"),
    "authority/mit-ocw-6.253/official-pages/course.html": (43639, "dbb1042e841414f5eb16feb4c40ac7dce6a186a1b5e721d7c4265a4716523afc"),
    "authority/mit-ocw-6.253/official-pages/lecture-notes.html": (57489, "5f8ceddd312afb0fa86ff7a4daa89ed524a446e07e3a055e0eab829727cb8d77"),
    "authority/mit-ocw-6.253/official-pages/CC-BY-NC-SA-4.0-legalcode.txt": (20850, "e66c269d4819aaab34b49ef5220c4ddab6756f21bb5180761a4eb8561f2b7bbd"),
    "authority/mit-ocw-6.253/downloads/6.253-spring-2012.zip": (41452759, "32e241f7101943e285c8b56ca61ae117b647d67015ff8b1048ab598319d7389f"),
    "authority/mit-ocw-6.253/downloads/6.253-spring-2012.entries.sha256.tsv": (52632, "661f7293afd5a1e44742d7ea9a316c9c1474b6c94ede94c4044084a5f51f42a0"),
    MIT_PDF: (8030116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    "authority/mit-ocw-6.253/repository/6.253-spring-2012-58d7c86195f09dd8708b84dde28205d3199207dd.zip": (32975, "e0ded208972802866e0a5a733163c4792f487a2367ee008f7fb9a1f919853f28"),
    MIT_WITNESS: (5752, "a18aefa9e1ffa29d0a3cea21d0df34f05025cb7c2008ae57b5db44730c9d1f58"),
    MIT_TARGET: (8641, "2170dec12e707782c7677647f77ad8ee3360b282a8dbb9fb5620170106004bf3"),
    MIT_HTML: (20613, "fff4de952dd2cb208208e1cfb3bbc8fe8a64936ff5fdb532a23a92fb0dc6af8b"),
    MIT_READER_PDF: (53370, "bd03912f9d3fe6dbe7376577c7ca6e7ab5aee007dd33b51669cde1792644df58"),
    MIT_BROWSER_QA: (1757, "2d5c90b3343040c4ed3dfbdb3714737dfba8317d1781c1e5c27145f5afbbb76d"),
    MIT_REREVIEW: (2691, "8259c6631c1c8645684c75a0244feedfc7289023d13e909cfdc73941eed35e50"),
    MIT_AUDIT: (7917, "4daeed4cf4136fa5ea81f4049b342c48fb23c2a2e2f28cb133dc714bfcf14d10"),
    "qa/build_mit_pilot.py": (3025, "b109c24f01feb1f57193a05b56ae662902078c5fd63f457084379f7db66dac74"),
    "source/id-ID/mit-pilot.css": (2436, "3cccdb9d3fac8c41d5814732794373bcd0d03fc8496f2db29e6ec0c77391a715"),
    "source/id-ID/mit-pilot-preamble.tex": (1206, "9e5c41c6c64b46dbbe4b0ab5baffc40ce119251e32ddd3deaeefb15fe8fe1259"),
    "source/id-ID/mit-pilot-pdf-filter.lua": (290, "797fd15ea50a306de33e80a25dfe1b9a2cf202bf6cda69eb3619e05d3ace20b3"),
    "source/id-ID/mit-pilot-before-body.html": (101, "8ed7a8480d71a6faf13cb006cf0564eedbdc6b5f263e8bb09dd31ec4a865e916"),
    "source/id-ID/mit-pilot-after-body.html": (8, "c529a821ba488b08d7968807e395f22f820af99d41f82ffe77de18200d2007b0"),
    "authority/royer-stochastic-gradient/official-pages/teachSG.html": (6381, "7b03656d07edf4bdb7b524ff20a41d06511a23e0b75a04cdaff309ab0817f88c"),
    "authority/royer-stochastic-gradient/official-pages/CC-BY-NC-4.0-legalcode.txt": (19347, "41003d4a74749c0220e33dd415042164b5a1093ed401f36277234f772d22d3d0"),
    "authority/royer-stochastic-gradient/downloads/LectureNotesOML-SG.pdf": (684631, "3290c61e870ef807ae92c4ace309449ee46ab3aa544e033c100f4a005311dfd3"),
    "authority/royer-stochastic-gradient/downloads/SourcesLabSG01.zip": (382975, "88e18ea096b87bd12d182072bfbf6fd12ac73d666e16911a3f015ee9a574d461"),
    "authority/royer-stochastic-gradient/downloads/SourcesLabSG01.entries.sha256.tsv": (158, "679e9ee74402e08fa35d495ff324ccbcf0e55331934461ea2812507ef0bc5ea2"),
    "authority/royer-stochastic-gradient/downloads/SourcesLabSG02.zip": (371793, "0a0a908157dcf07f0dd3874c118e416dad3033a5f04f9cb37ae248b2f8feb623"),
    "authority/royer-stochastic-gradient/downloads/SourcesLabSG02.entries.sha256.tsv": (153, "f2964d38865ddf4d46dba15e98fff29ef5657b7ff4846aecd0a8605c0947b440"),
    "authority/royer-stochastic-gradient/labs/lab01/LabSG01-2324.ipynb": (591695, "a40429fd34995a055bf1421cde8cc0d7c6a44bbe971107460ab16548152e847b"),
    "authority/royer-stochastic-gradient/labs/lab02/LabSG02.ipynb": (529952, "b9a9f791b679307f1f3c0fa77c32cd238a303ea7e36f338f4bea463e9782c319"),
    "authority/royer-stochastic-gradient/downloads/boardSG01.pdf": (1932521, "e68fcd2d9bb7a2b712c128af6fe22bd2217b2c8d5cfbd8201dab98e8f2f4aa37"),
    "authority/royer-stochastic-gradient/downloads/boardSG02.pdf": (2293823, "3439ed737973d75280e5d7f384ec14083895009426e98a3145637eb932ad8554"),
    "authority/royer-stochastic-gradient/downloads/boardSG03.pdf": (2221564, "2539895172e6d88c6841b52775fbb253db9843ee69e6d2d54b57b9c4f7b4f99a"),
}


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), sha256(data)


def record_set_sha256(record_set: list[dict[str, Any]]) -> str:
    payload = "".join(
        canonical_json(record) + "\n"
        for record in sorted(record_set, key=lambda item: item["id"])
    ).encode("utf-8")
    return sha256(payload)


def id_set_sha256(record_set: list[dict[str, Any]]) -> str:
    return sha256(("\n".join(sorted(record["id"] for record in record_set)) + "\n").encode("utf-8"))


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


def artifact(record_id: str, kind: str, path: str, rights_id: str | None = None, **extra: Any) -> dict[str, Any]:
    size, digest = file_info(path)
    record = common("artifact", record_id, "current")
    record.update({
        "artifact_kind": kind, "path": path, "bytes": size, "sha256": digest,
        "hash_algorithm": "sha256-raw-bytes",
    })
    if rights_id is not None:
        record["rights_id"] = rights_id
    record.update(extra)
    return record


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.strip().startswith("::: {")
        and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
    ]
    if len(starts) != 1:
        raise ValueError(f"expected one fenced div #{anchor} in {relative}, found {len(starts)}")
    start = starts[0]
    depth = 0
    end = -1
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("::: {"):
            depth += 1
        elif stripped == ":::":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end < start:
        raise ValueError(f"unclosed fenced div #{anchor} in {relative}")
    data = ("\n".join(lines[start : end + 1]) + "\n").encode("utf-8")
    return start + 1, end + 1, len(data), sha256(data)


def desired_allowed_records() -> dict[str, dict[str, Any]]:
    desired = json.loads(json.dumps(ORIGINAL_ALLOWED_RECORDS, ensure_ascii=False))
    desired[COURSE_ID].update({
        "source_spine_unit_ids": [MIT_ROOT_UNIT_ID, "unit.habring.v1", "unit.penn.v1", ROYER_ROOT_UNIT_ID],
        "source_spine_note": "MIT is the selected primary theory spine; Habring supplies the modern convex/nonsmooth module; Penn supplies smooth numerical optimization; Royer supplies the stochastic-gradient component.",
    })
    desired["unit.habring.v1"].update({
        "order": 2,
        "curriculum_role": "modern_convex_and_nonsmooth_module",
    })
    desired["unit.penn.v1"].update({
        "status": "active", "order": 3,
        "admission_state": "admitted_smooth_numerical_optimization_donor",
        "curriculum_role": "smooth_numerical_optimization_donor",
    })
    desired["relation.penn.course-contains-work"]["note"] = (
        "Penn is the admitted smooth numerical-optimization donor and third source-spine work."
    )
    desired["relation.penn.habring-ch09-precedes-ch03"]["note"] = (
        "The source-spine topology continues from the Habring module to the admitted Penn numerical-optimization donor."
    )
    for record_id, path in CONTROL_REFRESH_PATHS.items():
        desired[record_id]["bytes"], desired[record_id]["sha256"] = file_info(path)
    return desired


def stage_backend(jsonl_bytes: bytes, csv_bytes: bytes) -> None:
    staged: list[Path] = []
    try:
        for destination, data in ((JSONL_PATH, jsonl_bytes), (CSV_PATH, csv_bytes)):
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.mit-l01-", suffix=".stage",
                dir=BACKEND, delete=False,
            ) as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append(Path(handle.name))
        if staged[0].read_bytes() != jsonl_bytes or staged[1].read_bytes() != csv_bytes:
            raise ValueError("staged backend readback differs before replacement")
        os.replace(staged[0], JSONL_PATH)
        staged.pop(0)
        os.replace(staged[0], CSV_PATH)
        staged.pop(0)
    finally:
        for path in staged:
            path.unlink(missing_ok=True)


def main() -> int:
    for relative, expected in FROZEN_FILES.items():
        actual = file_info(relative)
        if actual != expected:
            raise ValueError(f"frozen authority/pilot artifact differs: {relative}: {actual} != {expected}")

    freeze = json.loads((ROOT / SOURCE_FREEZE).read_text(encoding="utf-8"))
    if freeze.get("schema") != "o015-mit-royer-source-freeze-v1" or freeze.get("result") != "pass_with_declared_gaps":
        raise ValueError("MIT/Royer source freeze disposition differs")
    if freeze.get("selected_external_core") != {"expected_pages": 440, "mit_pages": 395, "pages": 440, "royer_pages": 45}:
        raise ValueError("selected external-core page closure differs")
    mit_freeze = freeze["mit_ocw_6_253"]
    royer_freeze = freeze["royer_stochastic_gradient"]
    if mit_freeze["pilot_boundary"]["pdf_pages"] != [2, 3, 4, 5] or mit_freeze["pilot_boundary"]["next_topic_starts_page"] != 6:
        raise ValueError("MIT pilot boundary differs")
    if royer_freeze["exercise_solution_closure"] != {
        "formal_exercises": 3, "hints": 0, "lab01": "substantially executed",
        "lab02": "not answer-complete: four unanswered discussion cells and an unimplemented optional Momentum/Adam section",
        "solutions": 3,
    }:
        raise ValueError("Royer learning-surface closure differs")

    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER_QA).read_text(encoding="utf-8"))
    if report.get("result") != "pass" or report.get("errors") != [] or browser.get("result") != "pass":
        raise ValueError("MIT pilot QA evidence is not passing")
    if report["mathematical_review"]["clarification_ids"] != [
        "O015-MIT-SEM-0001", "O015-MIT-SEM-0002", "O015-MIT-SEM-0003"
    ]:
        raise ValueError("MIT correction closure differs")
    for relative, item in report["files"].items():
        if file_info(relative) != (item["bytes"], item["sha256"]):
            raise ValueError(f"MIT pilot report binds stale bytes: {relative}")

    with (ROOT / "00_control/COMPONENT_RIGHTS.csv").open(encoding="utf-8", newline="") as handle:
        component_rows = list(csv.DictReader(handle))
    if len({row["component_id"] for row in component_rows}) != len(component_rows):
        raise ValueError("component-rights ledger has duplicate component IDs")
    components = {row["component_id"]: row for row in component_rows}
    controlled_components = [
        "o015-mit-6253", "o015-mit-teaching-closure", "o015-mit-athena-figures",
        "o015-mit-semantic-witness", "o015-mit-id-pilot", "o015-mit-pilot-build-qa",
        "o015-royer-notes", "o015-royer-lab01", "o015-royer-lab02", "o015-royer-supplements",
    ]
    missing_components = sorted(set(controlled_components) - set(components))
    if missing_components:
        raise ValueError(f"component-rights closure is missing: {missing_components}")

    incoming_jsonl = JSONL_PATH.read_bytes()
    incoming_csv = CSV_PATH.read_bytes()
    existing_records = [json.loads(line) for line in incoming_jsonl.decode("utf-8").splitlines() if line]
    records = [record for record in existing_records if record.get("responsible_workflow") != WORKFLOW]
    already_applied = len(records) != len(existing_records)
    if not already_applied:
        if (len(incoming_jsonl), sha256(incoming_jsonl)) != (BASELINE_JSONL_BYTES, BASELINE_JSONL_SHA256):
            raise ValueError("incoming JSONL is not the frozen 1,300-record baseline")
        if (len(incoming_csv), sha256(incoming_csv)) != (BASELINE_CSV_BYTES, BASELINE_CSV_SHA256):
            raise ValueError("incoming CSV is not the frozen 1,300-record baseline")
    if len(records) != BASELINE_RECORD_COUNT or len({record["id"] for record in records}) != BASELINE_RECORD_COUNT:
        raise ValueError("stripped baseline does not contain exactly 1,300 unique records")
    if id_set_sha256(records) != BASELINE_ID_SET_SHA256:
        raise ValueError("stripped baseline ID set differs")
    immutable = [record for record in records if record["id"] not in ALLOWED_EXISTING_IDS]
    if len(immutable) != IMMUTABLE_BASELINE_COUNT or record_set_sha256(immutable) != IMMUTABLE_BASELINE_RECORD_SET_SHA256:
        raise ValueError("a non-allowlisted baseline canonical record differs")

    desired = desired_allowed_records()
    incoming_by_id = {record["id"]: record for record in records}
    for record_id in sorted(ALLOWED_EXISTING_IDS):
        incoming = incoming_by_id.get(record_id)
        if incoming is None:
            raise ValueError(f"allowlisted baseline record is missing: {record_id}")
        if record_id in CONTROL_REFRESH_PATHS:
            normalized = json.loads(json.dumps(incoming, ensure_ascii=False))
            normalized["bytes"] = ORIGINAL_ALLOWED_RECORDS[record_id]["bytes"]
            normalized["sha256"] = ORIGINAL_ALLOWED_RECORDS[record_id]["sha256"]
            permitted_entry = canonical_json(normalized) == canonical_json(ORIGINAL_ALLOWED_RECORDS[record_id])
        else:
            permitted = {canonical_json(ORIGINAL_ALLOWED_RECORDS[record_id]), canonical_json(desired[record_id])}
            permitted_entry = canonical_json(incoming) in permitted
        if not permitted_entry:
            raise ValueError(f"allowlisted baseline record has unauthorized fields: {record_id}")
    records = [desired.get(record["id"], record) for record in records]
    refreshed_baseline_by_id = {record["id"]: canonical_json(record) for record in records}
    baseline_ids = set(refreshed_baseline_by_id)

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    new_records: list[dict[str, Any]] = []
    new_ids: set[str] = set()

    def add(record: dict[str, Any]) -> None:
        if record["id"] in baseline_ids or record["id"] in new_ids:
            raise ValueError(f"stable-ID collision: {record['id']}")
        new_ids.add(record["id"])
        new_records.append(record)

    rights_authority_urls = {
        "o015-mit-6253": "https://ocw.mit.edu/courses/6-253-convex-analysis-and-optimization-spring-2012/",
        "o015-mit-teaching-closure": "https://ocw.mit.edu/courses/6-253-convex-analysis-and-optimization-spring-2012/pages/lecture-notes/",
        "o015-mit-athena-figures": "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf",
        "o015-mit-semantic-witness": MIT_WITNESS,
        "o015-mit-id-pilot": MIT_TARGET,
        "o015-mit-pilot-build-qa": MIT_AUDIT,
        "o015-royer-notes": "https://www.lamsade.dauphine.fr/~croyer/teachSG.html",
        "o015-royer-lab01": "https://www.lamsade.dauphine.fr/~croyer/teachSG.html",
        "o015-royer-lab02": "https://www.lamsade.dauphine.fr/~croyer/teachSG.html",
        "o015-royer-supplements": "https://www.lamsade.dauphine.fr/~croyer/teachSG.html",
    }
    rights_ids: dict[str, str] = {}
    for component_id in controlled_components:
        prefix = "mit" if component_id.startswith("o015-mit") else "royer"
        suffix = component_id.removeprefix("o015-").replace("6253", "course")
        record_id = f"rights.o015-{suffix}"
        row = components[component_id]
        record = common("rights", record_id, row["status"])
        record.update({
            "component_id": component_id, "path": row["path"],
            "source_authority_id": row["source_authority"],
            "rights_expression": row["rights_expression"],
            "authority_url": rights_authority_urls[component_id],
            "component_ledger_status": row["status"],
            "component_ledger_required_handling": row["required_handling"],
            "required_handling": [item.strip() for item in row["required_handling"].split(";") if item.strip()],
            "notes": row["notes"], "component_family": prefix,
        })
        if "CC BY-NC-SA 4.0" in row["rights_expression"]:
            record["license_url"] = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
            record["translation_permitted"] = True
        elif "CC BY-NC 4.0" in row["rights_expression"]:
            record["license_url"] = "https://creativecommons.org/licenses/by-nc/4.0/"
            record["translation_permitted"] = True
        else:
            record["license_url"] = None
            record["translation_permitted"] = False
        add(record)
        rights_ids[component_id] = record_id

    tooling_rights_id = "rights.o015-mit-l01-backend-tooling"
    tooling_rights = common("rights", tooling_rights_id, "admitted")
    tooling_rights.update({
        "component_id": "o015-mit-l01-backend-tooling",
        "path": "qa/extend_backend_mit_l01.py + qa/validate_backend_mit_l01.py",
        "source_authority_id": "lane-authored",
        "rights_expression": "project-local validation code",
        "authority_url": "qa/extend_backend_mit_l01.py",
        "license_url": None, "translation_permitted": False,
        "required_handling": ["ship exact source", "retain deterministic generation and validation evidence"],
        "notes": "Bounded backend admission tooling; no blanket reuse grant is asserted.",
    })
    add(tooling_rights)

    mit_resource = common("resource", MIT_RESOURCE_ID, "selected_primary_authority")
    mit_resource.update({
        "title": "Convex Analysis and Optimization", "creator": "Dimitri P. Bertsekas",
        "source_language": "en", "term": "Spring 2012",
        "official_record": "https://ocw.mit.edu/courses/6-253-convex-analysis-and-optimization-spring-2012/",
        "official_lecture_notes": "https://ocw.mit.edu/courses/6-253-convex-analysis-and-optimization-spring-2012/pages/lecture-notes/",
        "rights_id": rights_ids["o015-mit-6253"],
        "authority_record_id": "o015-mit-ocw-6.253-spring-2012",
        "curriculum_role": "selected_primary_theory_and_algorithm_spine",
    })
    add(mit_resource)
    royer_resource = common("resource", ROYER_RESOURCE_ID, "selected_primary_component")
    royer_resource.update({
        "title": "Optimization for Machine Learning - Stochastic Gradient",
        "creator": "Clément W. Royer", "contributors": ["A. Gramfort", "Robert Gower"],
        "source_language": "en", "official_record": "https://www.lamsade.dauphine.fr/~croyer/teachSG.html",
        "rights_id": rights_ids["o015-royer-notes"],
        "authority_record_id": "o015-royer-stochastic-gradient-2023-2024",
        "curriculum_role": "selected_stochastic_gradient_component",
    })
    add(royer_resource)

    editions = [
        (MIT_SOURCE_EDITION_ID, "source_frozen", MIT_RESOURCE_ID, "immutable_pdf_source", "Spring 2012 complete notes", "en", rights_ids["o015-mit-teaching-closure"], {
            "authority_url": "https://ocw.mit.edu/courses/6-253-convex-analysis-and-optimization-spring-2012/pages/lecture-notes/",
            "source_pdf": {"path": MIT_PDF, "bytes": 8030116, "pages": 340, "sha256": FROZEN_FILES[MIT_PDF][1]},
            "editable_source_state": "mathematical_pdf_only",
        }),
        (MIT_WITNESS_EDITION_ID, "source_frozen", MIT_RESOURCE_ID, "project_semantic_transcription_witness", "pages-2-5-en-witness-v1", "en", rights_ids["o015-mit-semantic-witness"], {
            "source_edition_id": MIT_SOURCE_EDITION_ID, "source_artifact_id": "artifact.mit.complete-notes-pdf",
            "boundary_pages": [2, 3, 4, 5], "official_editable_source": False,
        }),
        (MIT_TARGET_EDITION_ID, "built", MIT_RESOURCE_ID, "derivative", "id-ID-pilot-v1", "id", rights_ids["o015-mit-id-pilot"], {
            "locale": "id-ID", "source_edition_id": MIT_WITNESS_EDITION_ID,
            "translation_state": "visually_checked", "publication_state": "unpublished_working_edition",
            "accessibility_primary_surface": MIT_HTML, "human_native_speaker_review": False,
        }),
        (ROYER_EDITION_ID, "source_frozen_with_declared_gaps", ROYER_RESOURCE_ID, "frozen_pdf_and_notebook_source", "2023-2024", "en", rights_ids["o015-royer-notes"], {
            "authority_url": "https://www.lamsade.dauphine.fr/~croyer/teachSG.html",
            "notes_pdf": {"path": "authority/royer-stochastic-gradient/downloads/LectureNotesOML-SG.pdf", "bytes": 684631, "pages": 45, "sha256": FROZEN_FILES["authority/royer-stochastic-gradient/downloads/LectureNotesOML-SG.pdf"][1]},
            "editable_source_state": "notebooks_present_but_environment_unpinned",
        }),
    ]
    for record_id, status, resource_id, kind, version, language, rights_id, extra in editions:
        record = common("edition", record_id, status)
        record.update({"resource_id": resource_id, "edition_kind": kind, "version": version, "language": language, "rights_id": rights_id, **extra})
        add(record)

    unit_specs = [
        (MIT_ROOT_UNIT_ID, "active", MIT_SOURCE_EDITION_ID, None, "work", 1, "course-root", "MIT OCW 6.253 Convex Analysis and Optimization", "Analisis Konveks dan Optimisasi", rights_ids["o015-mit-teaching-closure"], {"source_edition_id": MIT_SOURCE_EDITION_ID, "target_edition_id": MIT_TARGET_EDITION_ID, "curriculum_role": "selected_primary_theory_spine"}),
        (MIT_L01_UNIT_ID, "built", MIT_TARGET_EDITION_ID, MIT_ROOT_UNIT_ID, "lecture_topic", 1, "lecture-1-topic-1-pages-2-5", "Lecture 1 - The Role of Convexity in Optimization", "Kuliah 1 - Peran Kekonveksan dalam Optimisasi", rights_ids["o015-mit-id-pilot"], {"source_edition_id": MIT_WITNESS_EDITION_ID, "target_edition_id": MIT_TARGET_EDITION_ID, "source_pdf_pages": [2, 3, 4, 5], "next_source_page": 6, "translation_state": "visually_checked"}),
        (ROYER_ROOT_UNIT_ID, "active_with_declared_gaps", ROYER_EDITION_ID, None, "work", 4, "course-root", "Optimization for Machine Learning - Stochastic Gradient", "Komponen Gradien Stokastik", rights_ids["o015-royer-notes"], {"source_edition_id": ROYER_EDITION_ID, "curriculum_role": "selected_stochastic_gradient_component"}),
        (ROYER_NOTES_UNIT_ID, "source_frozen", ROYER_EDITION_ID, ROYER_ROOT_UNIT_ID, "lecture_notes", 1, "LectureNotesOML-SG.pdf", "Stochastic Gradient lecture notes", "Catatan Kuliah Gradien Stokastik", rights_ids["o015-royer-notes"], {"source_edition_id": ROYER_EDITION_ID, "source_pages": 45, "translation_state": "source_frozen"}),
        (ROYER_LAB01_UNIT_ID, "source_with_caveat", ROYER_EDITION_ID, ROYER_ROOT_UNIT_ID, "laboratory", 2, "LabSG01-2324.ipynb", "Stochastic Gradient Laboratory 1", "Laboratorium Gradien Stokastik 1", rights_ids["o015-royer-lab01"], {"source_edition_id": ROYER_EDITION_ID, "completion_state": "substantially_executed", "environment_pinned": False}),
        (ROYER_LAB02_UNIT_ID, "source_with_gap", ROYER_EDITION_ID, ROYER_ROOT_UNIT_ID, "laboratory", 3, "LabSG02.ipynb", "Stochastic Gradient Laboratory 2", "Laboratorium Gradien Stokastik 2", rights_ids["o015-royer-lab02"], {"source_edition_id": ROYER_EDITION_ID, "completion_state": "not_answer_complete", "environment_pinned": False, "unanswered_discussion_cells": 4, "optional_momentum_adam_implemented": False}),
    ]
    for record_id, status, edition_id, parent_id, kind, order, local_id, source_label, target_label, rights_id, extra in unit_specs:
        record = common("unit", record_id, status)
        record.update({"edition_id": edition_id, "unit_kind": kind, "order": order, "source_local_id": local_id, "source_local_label": source_label, "target_local_label": target_label, "rights_id": rights_id, **extra})
        if parent_id is not None:
            record["parent_id"] = parent_id
        add(record)

    segment_ids: list[str] = []
    page_item_counts = {2: 4, 3: 3, 4: 5, 5: 9}
    page_nested_bullets = {2: 0, 3: 8, 4: 4, 5: 0}
    for order, page in enumerate(range(2, 6), start=1):
        source_anchor = f"src-mit-l01-p{page:03d}"
        target_anchor = f"d90-mit-l01-p{page:03d}"
        source_start, source_end, source_bytes, source_hash = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_start, target_end, target_bytes, target_hash = fenced_div_slice(MIT_TARGET, target_anchor)
        record_id = f"d90.mit.ocw-6.253.l01.p{page:03d}"
        segment_ids.append(record_id)
        record = common("segment", record_id, "visually_checked")
        record.update({
            "unit_id": MIT_L01_UNIT_ID, "order": order,
            "source_edition_id": MIT_WITNESS_EDITION_ID, "target_edition_id": MIT_TARGET_EDITION_ID,
            "source_path": MIT_WITNESS, "source_line_start": source_start, "source_line_end": source_end,
            "source_bytes": source_bytes, "source_content_sha256": source_hash, "source_anchor": source_anchor,
            "target_path": MIT_TARGET, "target_line_start": target_start, "target_line_end": target_end,
            "target_bytes": target_bytes, "target_content_sha256": target_hash, "target_anchor": target_anchor,
            "hash_normalization": "sha256-utf8-lf-final-newline", "translation_state": "visually_checked",
            "rights_id": rights_ids["o015-mit-id-pilot"],
            "source_pdf_path": MIT_PDF, "source_pdf_page": page,
            "source_pdf_sha256": FROZEN_FILES[MIT_PDF][1], "source_pdf_pages_total": 340,
            "source_item_count": page_item_counts[page], "nested_source_bullet_count": page_nested_bullets[page],
            "anchor_mapping_rule": "replace src-mit- prefix with d90-mit- prefix",
        })
        add(record)

    surface_specs: list[tuple[str, str, str, str, dict[str, Any]]] = [
        ("surface.mit.ocw-6.253.complete-notes", MIT_ROOT_UNIT_ID, "lecture_notes", "present", {"count": 1, "pages": 340, "evidence_artifact_id": "artifact.o015.mit-royer-source-freeze"}),
        ("surface.mit.ocw-6.253.homework-prompts", MIT_ROOT_UNIT_ID, "exercise_set", "present", {"count": 5, "pages": 16, "evidence_artifact_id": "artifact.o015.mit-royer-source-freeze"}),
        ("surface.mit.ocw-6.253.homework-solutions", MIT_ROOT_UNIT_ID, "solution_set", "present", {"count": 5, "pages": 33, "evidence_artifact_id": "artifact.o015.mit-royer-source-freeze"}),
        ("surface.mit.ocw-6.253.midterm-solutions", MIT_ROOT_UNIT_ID, "exam_solution_set", "present_with_source_gap", {"count": 2, "pages": 6, "known_gap": "Spring 2012 midterm solution contains literal placeholder '(a) To be added.'", "evidence_artifact_id": "artifact.o015.mit-royer-source-freeze"}),
        ("surface.mit.l01.exercise-inventory", MIT_L01_UNIT_ID, "exercise", "absent", {"count": 0, "absence_evidence": MIT_AUDIT}),
        ("surface.mit.l01.hint-inventory", MIT_L01_UNIT_ID, "hint", "absent", {"count": 0, "absence_evidence": MIT_AUDIT}),
        ("surface.mit.l01.answer-inventory", MIT_L01_UNIT_ID, "answer", "absent", {"count": 0, "absence_evidence": MIT_AUDIT}),
        ("surface.mit.l01.solution-inventory", MIT_L01_UNIT_ID, "solution", "absent", {"count": 0, "absence_evidence": MIT_AUDIT}),
        ("surface.mit.l01.semantic-html", MIT_L01_UNIT_ID, "semantic_html_reader", "present", {"artifact_id": "artifact.mit.l01.target-html", "primary_accessible_surface": True, "lang": "id-ID"}),
        ("surface.mit.l01.reflowed-pdf", MIT_L01_UNIT_ID, "reflowed_pdf_reader", "present_with_limitation", {"artifact_id": "artifact.mit.l01.target-pdf", "pages": 3, "searchable": True, "tagged": False}),
        ("surface.royer.notes.reading", ROYER_NOTES_UNIT_ID, "lecture_notes", "present", {"count": 1, "pages": 45, "evidence_artifact_id": "artifact.royer.notes-pdf"}),
        ("surface.royer.notes.exercise-inventory", ROYER_NOTES_UNIT_ID, "exercise", "present", {"count": 3, "evidence_artifact_id": "artifact.o015.mit-royer-source-freeze"}),
        ("surface.royer.notes.solution-inventory", ROYER_NOTES_UNIT_ID, "solution", "present", {"count": 3, "evidence_artifact_id": "artifact.o015.mit-royer-source-freeze"}),
        ("surface.royer.notes.hint-inventory", ROYER_NOTES_UNIT_ID, "hint", "absent", {"count": 0, "evidence_artifact_id": "artifact.o015.mit-royer-source-freeze"}),
        ("surface.royer.lab01.notebook", ROYER_LAB01_UNIT_ID, "executable_notebook", "present_with_caveat", {"artifact_id": "artifact.royer.lab01-notebook", "cells": 55, "code_cells": 18, "code_cells_with_outputs": 12, "empty_code_cells": 0, "completion_state": "substantially_executed", "environment_pinned": False}),
        ("surface.royer.lab02.notebook", ROYER_LAB02_UNIT_ID, "executable_notebook", "incomplete", {"artifact_id": "artifact.royer.lab02-notebook", "cells": 53, "code_cells": 18, "code_cells_with_outputs": 6, "empty_code_cells": 4, "null_execution_count": 5, "unanswered_discussion_cells": 4, "optional_momentum_adam_implemented": False, "environment_pinned": False}),
        ("surface.royer.virtual-boards", ROYER_ROOT_UNIT_ID, "supplementary_virtual_board", "present", {"count": 3, "pages": 36, "counted_in_selected_core_pages": False, "evidence_artifact_id": "artifact.o015.mit-royer-source-freeze"}),
    ]
    for record_id, unit_id, surface_type, presence, extra in surface_specs:
        status = "source_absent" if presence == "absent" else "source_gap" if presence in {"incomplete", "present_with_source_gap"} else "present"
        record = common("learning_surface", record_id, status)
        record.update({"unit_id": unit_id, "surface_type": surface_type, "presence": presence, **extra})
        add(record)

    artifact_specs: list[tuple[str, str, str, str | None, dict[str, Any]]] = [
        ("artifact.o015.mit-royer-source-freeze", "source_freeze_manifest", SOURCE_FREEZE, None, {"result": "pass_with_declared_gaps"}),
        ("artifact.mit.ocw-course-page", "official_course_page", "authority/mit-ocw-6.253/official-pages/course.html", rights_ids["o015-mit-6253"], {}),
        ("artifact.mit.ocw-lecture-notes-page", "official_lecture_notes_page", "authority/mit-ocw-6.253/official-pages/lecture-notes.html", rights_ids["o015-mit-6253"], {}),
        ("artifact.mit.ocw-legalcode", "license_legalcode", "authority/mit-ocw-6.253/official-pages/CC-BY-NC-SA-4.0-legalcode.txt", rights_ids["o015-mit-6253"], {}),
        ("artifact.mit.ocw-course-archive", "official_course_archive", "authority/mit-ocw-6.253/downloads/6.253-spring-2012.zip", rights_ids["o015-mit-teaching-closure"], {"entries": 412, "files": 344, "uncompressed_bytes": 69160743}),
        ("artifact.mit.ocw-course-archive-manifest", "archive_entry_manifest", "authority/mit-ocw-6.253/downloads/6.253-spring-2012.entries.sha256.tsv", rights_ids["o015-mit-teaching-closure"], {"entries": 412}),
        ("artifact.mit.complete-notes-pdf", "authority_pdf", MIT_PDF, rights_ids["o015-mit-teaching-closure"], {"pages": 340, "pilot_pages": [2, 3, 4, 5]}),
        ("artifact.mit.ocw-repository-snapshot", "metadata_repository_archive", "authority/mit-ocw-6.253/repository/6.253-spring-2012-58d7c86195f09dd8708b84dde28205d3199207dd.zip", rights_ids["o015-mit-6253"], {"commit": "58d7c86195f09dd8708b84dde28205d3199207dd", "tree": "26d3136df9d5d7f564f0b1d068ec8d7a7c8818d6", "mathematical_tex_files": 0}),
        ("artifact.mit.l01.semantic-witness", "semantic_transcription_witness", MIT_WITNESS, rights_ids["o015-mit-semantic-witness"], {"source_pdf_pages": [2, 3, 4, 5], "official_editable_source": False}),
        ("artifact.mit.l01.target-source", "semantic_translation_source", MIT_TARGET, rights_ids["o015-mit-id-pilot"], {"locale": "id-ID", "correction_ids": ["O015-MIT-SEM-0001", "O015-MIT-SEM-0002", "O015-MIT-SEM-0003"]}),
        ("artifact.mit.l01.target-html", "semantic_html_reader", MIT_HTML, rights_ids["o015-mit-id-pilot"], {"locale": "id-ID", "math_format": "MathML"}),
        ("artifact.mit.l01.target-pdf", "reflowed_pdf_reader", MIT_READER_PDF, rights_ids["o015-mit-id-pilot"], {"locale": "id-ID", "pages": 3, "page_size": "A4", "tagged": False}),
        ("artifact.mit.l01.builder", "deterministic_builder", "qa/build_mit_pilot.py", rights_ids["o015-mit-pilot-build-qa"], {"toolchain": "Pandoc HTML5/MathML and LuaLaTeX"}),
        ("artifact.mit.l01.css", "html_stylesheet", "source/id-ID/mit-pilot.css", rights_ids["o015-mit-pilot-build-qa"], {}),
        ("artifact.mit.l01.pdf-preamble", "pdf_preamble", "source/id-ID/mit-pilot-preamble.tex", rights_ids["o015-mit-pilot-build-qa"], {}),
        ("artifact.mit.l01.pdf-filter", "pandoc_lua_filter", "source/id-ID/mit-pilot-pdf-filter.lua", rights_ids["o015-mit-pilot-build-qa"], {}),
        ("artifact.mit.l01.before-body", "html_include", "source/id-ID/mit-pilot-before-body.html", rights_ids["o015-mit-pilot-build-qa"], {}),
        ("artifact.mit.l01.after-body", "html_include", "source/id-ID/mit-pilot-after-body.html", rights_ids["o015-mit-pilot-build-qa"], {}),
        ("artifact.mit.l01.pilot-validator", "pilot_validator", "qa/validate_mit_pilot.py", rights_ids["o015-mit-pilot-build-qa"], {}),
        ("artifact.mit.l01.pilot-validation", "pilot_validation_report", MIT_REPORT, rights_ids["o015-mit-pilot-build-qa"], {"result": "pass"}),
        ("artifact.mit.l01.browser-qa", "browser_qa_report", MIT_BROWSER_QA, rights_ids["o015-mit-pilot-build-qa"], {"result": "pass"}),
        ("artifact.mit.l01.independent-rereview", "independent_semantic_rereview", MIT_REREVIEW, rights_ids["o015-mit-pilot-build-qa"], {"remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("artifact.mit.l01.pilot-audit", "admission_audit", MIT_AUDIT, rights_ids["o015-mit-pilot-build-qa"], {"result": "pass"}),
        ("artifact.royer.official-page", "official_course_page", "authority/royer-stochastic-gradient/official-pages/teachSG.html", rights_ids["o015-royer-notes"], {}),
        ("artifact.royer.legalcode", "license_legalcode", "authority/royer-stochastic-gradient/official-pages/CC-BY-NC-4.0-legalcode.txt", rights_ids["o015-royer-notes"], {}),
        ("artifact.royer.notes-pdf", "authority_pdf", "authority/royer-stochastic-gradient/downloads/LectureNotesOML-SG.pdf", rights_ids["o015-royer-notes"], {"pages": 45}),
        ("artifact.royer.lab01-archive", "laboratory_archive", "authority/royer-stochastic-gradient/downloads/SourcesLabSG01.zip", rights_ids["o015-royer-lab01"], {"entries": 1}),
        ("artifact.royer.lab01-archive-manifest", "archive_entry_manifest", "authority/royer-stochastic-gradient/downloads/SourcesLabSG01.entries.sha256.tsv", rights_ids["o015-royer-lab01"], {"entries": 1}),
        ("artifact.royer.lab01-notebook", "extracted_notebook", "authority/royer-stochastic-gradient/labs/lab01/LabSG01-2324.ipynb", rights_ids["o015-royer-lab01"], {"cells": 55}),
        ("artifact.royer.lab02-archive", "laboratory_archive", "authority/royer-stochastic-gradient/downloads/SourcesLabSG02.zip", rights_ids["o015-royer-lab02"], {"entries": 1}),
        ("artifact.royer.lab02-archive-manifest", "archive_entry_manifest", "authority/royer-stochastic-gradient/downloads/SourcesLabSG02.entries.sha256.tsv", rights_ids["o015-royer-lab02"], {"entries": 1}),
        ("artifact.royer.lab02-notebook", "extracted_notebook", "authority/royer-stochastic-gradient/labs/lab02/LabSG02.ipynb", rights_ids["o015-royer-lab02"], {"cells": 53}),
        ("artifact.royer.virtual-board-01", "supplementary_virtual_board", "authority/royer-stochastic-gradient/downloads/boardSG01.pdf", rights_ids["o015-royer-supplements"], {"pages": 10}),
        ("artifact.royer.virtual-board-02", "supplementary_virtual_board", "authority/royer-stochastic-gradient/downloads/boardSG02.pdf", rights_ids["o015-royer-supplements"], {"pages": 12}),
        ("artifact.royer.virtual-board-03", "supplementary_virtual_board", "authority/royer-stochastic-gradient/downloads/boardSG03.pdf", rights_ids["o015-royer-supplements"], {"pages": 14}),
        ("artifact.o015.backend-generator-mit-l01", "backend_generator", "qa/extend_backend_mit_l01.py", tooling_rights_id, {"toolchain": "Python 3 standard library"}),
        ("artifact.o015.backend-validator-mit-l01", "backend_validator", "qa/validate_backend_mit_l01.py", tooling_rights_id, {"toolchain": "Python 3 standard library plus pypdf"}),
    ]
    for record_id, kind, path, rights_id, extra in artifact_specs:
        add(artifact(record_id, kind, path, rights_id, **extra))

    adverse_events = {
        event["event_id"]: event
        for event in (
            json.loads(line)
            for line in (ROOT / "00_control/ADVERSE_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        )
    }
    correction_specs = [
        ("O015-MIT-SEM-0001", segment_ids[2], 4, "d90-mit-l01-note-dual-discrete", "determined_scope_clarification"),
        ("O015-MIT-SEM-0002", segment_ids[3], 5, "d90-mit-l01-note-self-dual", "determined_duality_involution_clarification"),
        ("O015-MIT-SEM-0003", segment_ids[2], 4, "d90-mit-l01-note-function-arrow", "determined_notation_correction"),
    ]
    for event_id, segment_id, page, target_anchor, correction_class in correction_specs:
        event = adverse_events.get(event_id)
        if event is None:
            raise ValueError(f"live adverse ledger lacks {event_id}")
        note_start, note_end, note_bytes, note_hash = fenced_div_slice(MIT_TARGET, target_anchor)
        record = common("correction", f"correction.{event_id.lower()}", "applied")
        record.update({
            "source_event_id": event_id, "source_edition_id": MIT_WITNESS_EDITION_ID,
            "affected_unit_ids": [MIT_L01_UNIT_ID], "affected_segment_ids": [segment_id],
            "source_path": MIT_WITNESS, "source_pdf_path": MIT_PDF, "source_pdf_page": page,
            "source_pdf_sha256": FROZEN_FILES[MIT_PDF][1], "surface": event["surface"],
            "source_issue": event["source_issue"], "target_action": event["target_action"],
            "correction_class": correction_class, "disposition": "applied",
            "target_path": MIT_TARGET, "target_anchor": target_anchor,
            "target_line_start": note_start, "target_line_end": note_end,
            "target_bytes": note_bytes, "target_content_sha256": note_hash,
            "hash_normalization": "sha256-utf8-lf-final-newline",
            "upstream_report_disposition": "not_submitted",
            "evidence_artifact_id": "artifact.o015.adverse-ledger",
            "evidence_event_ids": ["qa.o015.mit-l01.formulas-corrections", "qa.o015.mit-l01.math-rereview"],
        })
        add(record)

    qa_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("qa.o015.mit-l01.source-freeze", "source_freeze", "pass", {"witness_artifact_ids": ["artifact.o015.mit-royer-source-freeze", "artifact.o015.source-authority", "artifact.mit.complete-notes-pdf"], "authority_pdf_pages": 340, "pilot_pages": [2, 3, 4, 5], "next_topic_starts_page": 6}),
        ("qa.o015.mit-l01.semantic-reconstruction", "semantic_reconstruction", "pass", {"witness_artifact_ids": ["artifact.mit.l01.semantic-witness", "artifact.mit.l01.target-source", "artifact.mit.l01.pilot-validation"], "official_editable_source": False, "source_items": 21}),
        ("qa.o015.mit-l01.topology", "structure", "pass", {"witness_artifact_ids": ["artifact.mit.l01.pilot-validation", "artifact.mit.l01.pilot-audit"], "source_page_map": [[1, 2], [2, 3], [3, 4], [4, 5]], "item_counts": {"2": 4, "3": 3, "4": 5, "5": 9}, "nested_source_bullets": 12, "figures": 0}),
        ("qa.o015.mit-l01.formulas-corrections", "mathematics", "pass", {"witness_artifact_ids": ["artifact.mit.l01.pilot-validation", "artifact.o015.adverse-ledger"], "source_math_nodes": 6, "target_math_nodes": 14, "display_formulas": 2, "correction_event_ids": ["O015-MIT-SEM-0001", "O015-MIT-SEM-0002", "O015-MIT-SEM-0003"]}),
        ("qa.o015.mit-l01.build", "build", "pass", {"witness_artifact_ids": ["artifact.mit.l01.builder", "artifact.mit.l01.target-html", "artifact.mit.l01.target-pdf", "artifact.mit.l01.pilot-validation"], "deterministic_rebuilds": 2, "html_sha256": FROZEN_FILES[MIT_HTML][1], "pdf_sha256": FROZEN_FILES[MIT_READER_PDF][1], "toolchain": "Pandoc HTML5/MathML and LuaLaTeX"}),
        ("qa.o015.mit-l01.html", "html", "pass", {"witness_artifact_ids": ["artifact.mit.l01.target-html", "artifact.mit.l01.pilot-validation"], "lang": "id-ID", "main_landmarks": 1, "headings": {"h1": 1, "h2": 6, "h3": 1}, "mathml_nodes": 14, "display_mathml_nodes": 2, "images": 0, "duplicate_ids": [], "unresolved_fragments": []}),
        ("qa.o015.mit-l01.browser", "browser", "pass", {"witness_artifact_ids": ["artifact.mit.l01.browser-qa", "artifact.mit.l01.target-html"], "desktop_viewport": [1280, 720], "mobile_viewport": [390, 844], "horizontal_overflow": False, "display_math_overflow": False, "console_warnings_or_errors": []}),
        ("qa.o015.mit-l01.pdf", "pdf", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l01.target-pdf", "artifact.mit.l01.pilot-validation"], "pages": 3, "page_size": "A4", "lang": "id-ID", "searchable": True, "fonts_with_tounicode": True, "tagged": False, "all_pages_visually_inspected": True}),
        ("qa.o015.mit-l01.accessibility", "accessibility", "pass_with_limitation", {"witness_artifact_ids": ["artifact.mit.l01.target-html", "artifact.mit.l01.target-pdf", "artifact.mit.l01.browser-qa"], "primary_surface": "semantic_html", "html_reflow_passed": True, "pdf_searchable": True, "limitations": ["PDF is untagged", "independent human/native-speaker Indonesian review is not recorded"]}),
        ("qa.o015.mit-l01.math-rereview", "independent_mathematical_rereview", "pass", {"witness_artifact_ids": ["artifact.mit.l01.independent-rereview", "artifact.mit.l01.pilot-validation"], "remaining_defects": {"P1": 0, "P2": 0, "P3": 0}}),
        ("qa.o015.mit-l01.language", "language", "not_recorded", {"witness_artifact_ids": [], "human_native_speaker_review": False, "gap": "No independent human/native-speaker Indonesian language-review receipt is recorded."}),
        ("qa.o015.mit-l01.rights", "rights", "pass", {"witness_artifact_ids": ["artifact.o015.component-rights", "artifact.mit.l01.pilot-audit"], "component_ids": controlled_components[:6], "athena_figures_in_boundary": 0, "athena_component_status": "excluded"}),
        ("qa.o015.royer.source-freeze", "source_freeze", "pass_with_declared_gaps", {"witness_artifact_ids": ["artifact.o015.mit-royer-source-freeze", "artifact.royer.official-page", "artifact.royer.notes-pdf"], "notes_pages": 45, "mathematical_tex_source": False, "notebook_environment_pinned": False}),
        ("qa.o015.royer.learning-surfaces", "learning_surface_inventory", "pass_with_declared_gaps", {"witness_artifact_ids": ["artifact.o015.mit-royer-source-freeze", "artifact.royer.lab01-notebook", "artifact.royer.lab02-notebook"], "formal_exercises": 3, "solutions": 3, "hints": 0, "lab01": "substantially_executed", "lab02": "not_answer_complete", "lab02_unanswered_discussion_cells": 4, "optional_momentum_adam_implemented": False}),
        ("qa.o015.mit-royer.backend-integration", "backend_integrity", "pass", {"witness_artifact_ids": ["artifact.o015.backend-generator-mit-l01", "artifact.o015.backend-validator-mit-l01", "artifact.o015.source-authority", "artifact.o015.component-rights", "artifact.o015.adverse-ledger"], "baseline_record_count": BASELINE_RECORD_COUNT, "baseline_jsonl_sha256": BASELINE_JSONL_SHA256, "baseline_csv_sha256": BASELINE_CSV_SHA256, "allowed_existing_ids": sorted(ALLOWED_EXISTING_IDS)}),
    ]
    for record_id, event_type, result, extra in qa_specs:
        record = common("qa_event", record_id, "passed" if result == "pass" else result)
        record.update({"event_type": event_type, "result": result, **extra})
        if record_id.startswith("qa.o015.mit-l01"):
            record["unit_id"] = MIT_L01_UNIT_ID
        add(record)

    relation_specs: list[tuple[str, str, str, str, str]] = [
        ("relation.mit.course-contains-work", "contains", COURSE_ID, MIT_ROOT_UNIT_ID, "Selected primary theory spine."),
        ("relation.mit.work-contains-l01", "contains", MIT_ROOT_UNIT_ID, MIT_L01_UNIT_ID, "First admitted MIT topic boundary."),
        ("relation.mit.resource-contains-source-edition", "contains", MIT_RESOURCE_ID, MIT_SOURCE_EDITION_ID, "Frozen complete-notes PDF edition."),
        ("relation.mit.resource-contains-witness-edition", "contains", MIT_RESOURCE_ID, MIT_WITNESS_EDITION_ID, "Project-made English semantic witness edition."),
        ("relation.mit.resource-contains-target-edition", "contains", MIT_RESOURCE_ID, MIT_TARGET_EDITION_ID, "Working Indonesian semantic derivative."),
        ("relation.mit.source-edition-contains-work", "contains", MIT_SOURCE_EDITION_ID, MIT_ROOT_UNIT_ID, "Complete MIT source work."),
        ("relation.mit.witness-edition-contains-l01", "contains", MIT_WITNESS_EDITION_ID, MIT_L01_UNIT_ID, "Page-addressed English witness boundary."),
        ("relation.mit.target-edition-contains-l01", "contains", MIT_TARGET_EDITION_ID, MIT_L01_UNIT_ID, "Built id-ID pilot unit."),
        ("relation.mit.witness-adapts-authority-pdf", "adapts", "artifact.mit.l01.semantic-witness", "artifact.mit.complete-notes-pdf", "Semantic transcription of complete-notes pages 2-5."),
        ("relation.mit.target-translates-witness", "translates", "artifact.mit.l01.target-source", "artifact.mit.l01.semantic-witness", "Complete one-to-one page/item translation."),
        ("relation.mit.html-adapts-target", "adapts", "artifact.mit.l01.target-html", "artifact.mit.l01.target-source", "Deterministic semantic HTML build."),
        ("relation.mit.pdf-adapts-target", "adapts", "artifact.mit.l01.target-pdf", "artifact.mit.l01.target-source", "Deterministic reflowed PDF build."),
        ("relation.mit.browser-qa-depends-on-html", "depends-on", "artifact.mit.l01.browser-qa", "artifact.mit.l01.target-html", "Measured desktop/mobile browser evidence."),
        ("relation.mit.validation-depends-on-browser-qa", "depends-on", "artifact.mit.l01.pilot-validation", "artifact.mit.l01.browser-qa", "Validation binds browser evidence."),
        ("relation.mit.validation-depends-on-rereview", "depends-on", "artifact.mit.l01.pilot-validation", "artifact.mit.l01.independent-rereview", "Validation binds independent rereview."),
        ("relation.mit.audit-depends-on-validation", "depends-on", "artifact.mit.l01.pilot-audit", "artifact.mit.l01.pilot-validation", "Admission audit binds passing validator receipt."),
        ("relation.mit.l01-precedes-habring-ch03", "precedes", MIT_L01_UNIT_ID, "unit.habring.v1.ch03", "Selected source-spine order enters the modern Habring module."),
        ("relation.royer.course-contains-work", "contains", COURSE_ID, ROYER_ROOT_UNIT_ID, "Selected stochastic-gradient component."),
        ("relation.royer.resource-contains-edition", "contains", ROYER_RESOURCE_ID, ROYER_EDITION_ID, "Frozen 2023-2024 source closure."),
        ("relation.royer.edition-contains-work", "contains", ROYER_EDITION_ID, ROYER_ROOT_UNIT_ID, "Royer work root."),
        ("relation.royer.work-contains-notes", "contains", ROYER_ROOT_UNIT_ID, ROYER_NOTES_UNIT_ID, "Complete 45-page notes component."),
        ("relation.royer.work-contains-lab01", "contains", ROYER_ROOT_UNIT_ID, ROYER_LAB01_UNIT_ID, "Substantially executed unpinned notebook."),
        ("relation.royer.work-contains-lab02", "contains", ROYER_ROOT_UNIT_ID, ROYER_LAB02_UNIT_ID, "Notebook with declared answer gaps."),
        ("relation.royer.notes-depend-on-pdf", "depends-on", ROYER_NOTES_UNIT_ID, "artifact.royer.notes-pdf", "Exact authority notes bytes."),
        ("relation.royer.lab01-depends-on-notebook", "depends-on", ROYER_LAB01_UNIT_ID, "artifact.royer.lab01-notebook", "Exact extracted notebook."),
        ("relation.royer.lab02-depends-on-notebook", "depends-on", ROYER_LAB02_UNIT_ID, "artifact.royer.lab02-notebook", "Exact extracted notebook with declared gaps."),
        ("relation.royer.penn-ch05-precedes-notes", "precedes", "unit.penn.v1.ch05", ROYER_NOTES_UNIT_ID, "Source-spine order proceeds to the selected stochastic-gradient component."),
    ]
    for order, segment_id in enumerate(segment_ids, start=1):
        relation_specs.append((f"relation.mit.l01.contains-p{order + 1:03d}", "contains", MIT_L01_UNIT_ID, segment_id, "Ordered one-page semantic segment."))
    relation_triples: set[tuple[str, str, str]] = set()
    for record_id, relation_type, source_id, target_id, note in relation_specs:
        triple = (relation_type, source_id, target_id)
        if triple in relation_triples:
            raise ValueError(f"duplicate new relation triple: {triple}")
        relation_triples.add(triple)
        record = common("relation", record_id, "current")
        record.update({"relation_type": relation_type, "source_id": source_id, "target_id": target_id, "note": note})
        add(record)

    records.extend(new_records)
    if len({record["id"] for record in records}) != len(records):
        raise ValueError("duplicate record IDs after MIT/Royer extension")
    final_by_id = {record["id"]: canonical_json(record) for record in records}
    changed_immutable = sorted(
        record_id for record_id, before in refreshed_baseline_by_id.items()
        if record_id not in ALLOWED_EXISTING_IDS and final_by_id.get(record_id) != before
    )
    missing_baseline = sorted(baseline_ids - set(final_by_id))
    if changed_immutable or missing_baseline:
        raise ValueError(f"baseline preservation failed: changed={changed_immutable}; missing={missing_baseline}")

    by_id = {record["id"]: record for record in records}
    for record in records:
        for field in schema["required_common"] + schema["required_by_entity"].get(record["entity_type"], []):
            if field not in record:
                raise ValueError(f"{record['id']}: missing required field {field}")
        for field in schema["reference_fields"]:
            if field not in record:
                continue
            value = record[field]
            values = value if isinstance(value, list) else [value]
            for target in values:
                if isinstance(target, str) and target not in by_id:
                    raise ValueError(f"{record['id']}: unresolved {field} -> {target}")

    entity_rank = {entity_type: rank for rank, entity_type in enumerate(schema["entity_order"])}
    records.sort(key=lambda record: (entity_rank[record["entity_type"]], record["id"]))
    jsonl_bytes = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    csv_buffer = io.StringIO(newline="")
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(schema["csv_columns"])
    for record in records:
        writer.writerow([record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)])
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    stage_backend(jsonl_bytes, csv_bytes)

    desired_allowed = desired_allowed_records()
    changed_existing_ids = sorted(
        record_id for record_id in ALLOWED_EXISTING_IDS
        if canonical_json(desired_allowed[record_id]) != canonical_json(ORIGINAL_ALLOWED_RECORDS[record_id])
    )
    report_out = {
        "already_applied_on_entry": already_applied,
        "baseline": {
            "record_count": BASELINE_RECORD_COUNT,
            "jsonl": {"bytes": BASELINE_JSONL_BYTES, "sha256": BASELINE_JSONL_SHA256},
            "csv": {"bytes": BASELINE_CSV_BYTES, "sha256": BASELINE_CSV_SHA256},
            "immutable_record_count": IMMUTABLE_BASELINE_COUNT,
            "immutable_record_set_sha256": IMMUTABLE_BASELINE_RECORD_SET_SHA256,
        },
        "allowed_changed_existing_ids": changed_existing_ids,
        "new_record_count": len(new_records),
        "new_entity_counts": dict(sorted(Counter(record["entity_type"] for record in new_records).items())),
        "new_ids_sha256": sha256(("\n".join(sorted(new_ids)) + "\n").encode("utf-8")),
        "record_count": len(records),
        "entity_counts": dict(sorted(Counter(record["entity_type"] for record in records).items())),
        "jsonl": {"bytes": len(jsonl_bytes), "sha256": sha256(jsonl_bytes)},
        "csv": {"bytes": len(csv_bytes), "sha256": sha256(csv_bytes)},
        "staged_dual_file_replacement": "pass",
        "result": "pass",
    }
    print(json.dumps(report_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
