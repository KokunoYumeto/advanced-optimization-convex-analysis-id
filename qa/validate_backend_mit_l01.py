#!/usr/bin/env python3
"""Independently validate the MIT L01 and Royer backend admission."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
JSONL = BACKEND / "records.jsonl"
CSV = BACKEND / "records.csv"
SCHEMA_PATH = BACKEND / "backend_schema.json"
WORKFLOW = "o015-mit-l01-royer-backend-v1"

BASELINE_COUNT = 1300
BASELINE_JSONL = (953_701, "315f1460a0f7e22256ffd95ed9d65b8bf81b987b58deb1a2b7ae719fdeb35a74")
BASELINE_CSV = (1_143_371, "b0a417ce01ec076bbe57be40d9b3d1d2d1f3e75cf4688ce16350eb2916150b19")
BASELINE_ID_SET_SHA256 = "43e632affd2c3bacf20c3739980d7b15af017bf40d9f80b488e95f153d53124a"
IMMUTABLE_BASELINE_COUNT = 1291
IMMUTABLE_BASELINE_RECORD_SET_SHA256 = "e979fecf16dbc04f8b65c8ade1d52a1fada347584c90ee47825807b5800d3511"

COURSE_ID = "course.d90.advanced-optimization-convex-analysis"
MIT_RESOURCE = "resource.mit.ocw-6.253-convex-analysis-optimization"
MIT_SOURCE_EDITION = "edition.mit.ocw-6.253.spring-2012.complete-notes"
MIT_WITNESS_EDITION = "edition.mit.ocw-6.253.spring-2012.semantic-witness-en"
MIT_TARGET_EDITION = "edition.mit.ocw-6.253.id-id.pilot-v1"
MIT_ROOT = "unit.mit.ocw-6.253.spring-2012"
MIT_L01 = "unit.mit.ocw-6.253.l01"
ROYER_RESOURCE = "resource.royer.stochastic-gradient"
ROYER_EDITION = "edition.royer.stochastic-gradient.2023-2024"
ROYER_ROOT = "unit.royer.stochastic-gradient.2023-2024"
ROYER_NOTES = "unit.royer.stochastic-gradient.2023-2024.notes"
ROYER_LAB01 = "unit.royer.stochastic-gradient.2023-2024.lab01"
ROYER_LAB02 = "unit.royer.stochastic-gradient.2023-2024.lab02"

MIT_PDF = (
    "authority/mit-ocw-6.253/course-archive/static_resources/"
    "6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
)
MIT_WITNESS = "source/en/mit-01-role-of-convexity-semantic-witness.md"
MIT_TARGET = "source/id-ID/mit-01-peran-kekonveksan-id.md"
MIT_HTML = "output/html/D90-MIT-01-peran-kekonveksan-id.html"
MIT_READER_PDF = "output/pdf/D90-MIT-01-peran-kekonveksan-id.pdf"
MIT_REPORT = "qa/MIT_L01_PILOT_VALIDATION.json"
MIT_BROWSER = "qa/MIT_L01_BROWSER_QA.json"
MIT_REREVIEW = "qa/MIT_L01_INDEPENDENT_REREVIEW.md"
MIT_AUDIT = "00_control/MIT_L01_PILOT_AUDIT.md"

ALLOWED_EXISTING_IDS = {
    COURSE_ID, "unit.habring.v1", "unit.penn.v1",
    "relation.penn.course-contains-work", "relation.penn.habring-ch09-precedes-ch03",
    "artifact.o015.source-authority", "artifact.o015.component-rights",
    "artifact.o015.adverse-ledger", "artifact.habring.worklog-ch09",
}
ORIGINAL_CANONICAL_SHA256 = {
    COURSE_ID: "64ee908a1f069095015eb224002f7a3631d63b1d7488b834b971c42ed0e7e6af",
    "unit.habring.v1": "49016034ee6b6750295ff5bfd012c0dce22582cbfe3885bee9565ee6dde642f9",
    "unit.penn.v1": "169bd6c9fd4689784d01776a4d9c832f7f91079f8097f0ea5a0c72e23cfa451f",
    "relation.penn.course-contains-work": "10b24a1fd214ea72f0330603381ad846f86a4e73cb161f9556106f3b84c1f978",
    "relation.penn.habring-ch09-precedes-ch03": "104d21539390cf23267fc3ed6869691a9f895e37dd9710204dc364f940293d8c",
    "artifact.o015.adverse-ledger": "a66b07e649378c11ea63bcc18dea37698e95956c24f42353d2c0f5bdd61ec382",
    "artifact.o015.component-rights": "131d06981e010c6b48447c5ca80cebe751b0067a3902d03f6cdb86cb0fe22241",
    "artifact.o015.source-authority": "0c06b06a2940f18b9c0065da64d7ded5374930b71f03452af2282de92fb01837",
    "artifact.habring.worklog-ch09": "300fd57fba6a7f0f9f24513b543f47ce9581039c7952d8900220b714ae0d43ef",
}
ORIGINAL_ARTIFACT_IDENTITIES = {
    "artifact.o015.adverse-ledger": (93480, "c8d87cd7958e9beba30372e1fc70df7fe992970db780d8757c061854fb9075f0"),
    "artifact.o015.component-rights": (23258, "51e08f77f709a945c8e53948ee466d7d06e75e469ef7fef4d7d269fc895e37e9"),
    "artifact.o015.source-authority": (6832, "6a1e00cf4f5088c183ae2f3424743218e12d91c17511551250d17aed9dd6fa13"),
    "artifact.habring.worklog-ch09": (9661, "0527b8b61dee2ffccd493e8331b7d57f592ba3ec9b5ef87226c15cb1a342e99e"),
}

EXPECTED_BY_ENTITY: dict[str, set[str]] = {
    "resource": {MIT_RESOURCE, ROYER_RESOURCE},
    "edition": {MIT_SOURCE_EDITION, MIT_WITNESS_EDITION, MIT_TARGET_EDITION, ROYER_EDITION},
    "unit": {MIT_ROOT, MIT_L01, ROYER_ROOT, ROYER_NOTES, ROYER_LAB01, ROYER_LAB02},
    "segment": {f"d90.mit.ocw-6.253.l01.p{page:03d}" for page in range(2, 6)},
    "learning_surface": {
        "surface.mit.ocw-6.253.complete-notes", "surface.mit.ocw-6.253.homework-prompts",
        "surface.mit.ocw-6.253.homework-solutions", "surface.mit.ocw-6.253.midterm-solutions",
        "surface.mit.l01.exercise-inventory", "surface.mit.l01.hint-inventory",
        "surface.mit.l01.answer-inventory", "surface.mit.l01.solution-inventory",
        "surface.mit.l01.semantic-html", "surface.mit.l01.reflowed-pdf",
        "surface.royer.notes.reading", "surface.royer.notes.exercise-inventory",
        "surface.royer.notes.solution-inventory", "surface.royer.notes.hint-inventory",
        "surface.royer.lab01.notebook", "surface.royer.lab02.notebook",
        "surface.royer.virtual-boards",
    },
    "rights": {
        "rights.o015-mit-course", "rights.o015-mit-teaching-closure",
        "rights.o015-mit-athena-figures", "rights.o015-mit-semantic-witness",
        "rights.o015-mit-id-pilot", "rights.o015-mit-pilot-build-qa",
        "rights.o015-royer-notes", "rights.o015-royer-lab01", "rights.o015-royer-lab02",
        "rights.o015-royer-supplements", "rights.o015-mit-l01-backend-tooling",
    },
    "correction": {f"correction.o015-mit-sem-{number:04d}" for number in range(1, 4)},
    "qa_event": {
        "qa.o015.mit-l01.source-freeze", "qa.o015.mit-l01.semantic-reconstruction",
        "qa.o015.mit-l01.topology", "qa.o015.mit-l01.formulas-corrections",
        "qa.o015.mit-l01.build", "qa.o015.mit-l01.html", "qa.o015.mit-l01.browser",
        "qa.o015.mit-l01.pdf", "qa.o015.mit-l01.accessibility",
        "qa.o015.mit-l01.math-rereview", "qa.o015.mit-l01.language",
        "qa.o015.mit-l01.rights", "qa.o015.royer.source-freeze",
        "qa.o015.royer.learning-surfaces", "qa.o015.mit-royer.backend-integration",
    },
    "artifact": {
        "artifact.o015.mit-royer-source-freeze", "artifact.mit.ocw-course-page",
        "artifact.mit.ocw-lecture-notes-page", "artifact.mit.ocw-legalcode",
        "artifact.mit.ocw-course-archive", "artifact.mit.ocw-course-archive-manifest",
        "artifact.mit.complete-notes-pdf", "artifact.mit.ocw-repository-snapshot",
        "artifact.mit.l01.semantic-witness", "artifact.mit.l01.target-source",
        "artifact.mit.l01.target-html", "artifact.mit.l01.target-pdf",
        "artifact.mit.l01.builder", "artifact.mit.l01.css", "artifact.mit.l01.pdf-preamble",
        "artifact.mit.l01.pdf-filter", "artifact.mit.l01.before-body", "artifact.mit.l01.after-body",
        "artifact.mit.l01.pilot-validator", "artifact.mit.l01.pilot-validation",
        "artifact.mit.l01.browser-qa", "artifact.mit.l01.independent-rereview",
        "artifact.mit.l01.pilot-audit", "artifact.royer.official-page",
        "artifact.royer.legalcode", "artifact.royer.notes-pdf",
        "artifact.royer.lab01-archive", "artifact.royer.lab01-archive-manifest",
        "artifact.royer.lab01-notebook", "artifact.royer.lab02-archive",
        "artifact.royer.lab02-archive-manifest", "artifact.royer.lab02-notebook",
        "artifact.royer.virtual-board-01", "artifact.royer.virtual-board-02",
        "artifact.royer.virtual-board-03", "artifact.o015.backend-generator-mit-l01",
        "artifact.o015.backend-validator-mit-l01",
    },
}

EXPECTED_RELATIONS: dict[str, tuple[str, str, str]] = {
    "relation.mit.course-contains-work": ("contains", COURSE_ID, MIT_ROOT),
    "relation.mit.work-contains-l01": ("contains", MIT_ROOT, MIT_L01),
    "relation.mit.resource-contains-source-edition": ("contains", MIT_RESOURCE, MIT_SOURCE_EDITION),
    "relation.mit.resource-contains-witness-edition": ("contains", MIT_RESOURCE, MIT_WITNESS_EDITION),
    "relation.mit.resource-contains-target-edition": ("contains", MIT_RESOURCE, MIT_TARGET_EDITION),
    "relation.mit.source-edition-contains-work": ("contains", MIT_SOURCE_EDITION, MIT_ROOT),
    "relation.mit.witness-edition-contains-l01": ("contains", MIT_WITNESS_EDITION, MIT_L01),
    "relation.mit.target-edition-contains-l01": ("contains", MIT_TARGET_EDITION, MIT_L01),
    "relation.mit.witness-adapts-authority-pdf": ("adapts", "artifact.mit.l01.semantic-witness", "artifact.mit.complete-notes-pdf"),
    "relation.mit.target-translates-witness": ("translates", "artifact.mit.l01.target-source", "artifact.mit.l01.semantic-witness"),
    "relation.mit.html-adapts-target": ("adapts", "artifact.mit.l01.target-html", "artifact.mit.l01.target-source"),
    "relation.mit.pdf-adapts-target": ("adapts", "artifact.mit.l01.target-pdf", "artifact.mit.l01.target-source"),
    "relation.mit.browser-qa-depends-on-html": ("depends-on", "artifact.mit.l01.browser-qa", "artifact.mit.l01.target-html"),
    "relation.mit.validation-depends-on-browser-qa": ("depends-on", "artifact.mit.l01.pilot-validation", "artifact.mit.l01.browser-qa"),
    "relation.mit.validation-depends-on-rereview": ("depends-on", "artifact.mit.l01.pilot-validation", "artifact.mit.l01.independent-rereview"),
    "relation.mit.audit-depends-on-validation": ("depends-on", "artifact.mit.l01.pilot-audit", "artifact.mit.l01.pilot-validation"),
    "relation.mit.l01-precedes-habring-ch03": ("precedes", MIT_L01, "unit.habring.v1.ch03"),
    "relation.royer.course-contains-work": ("contains", COURSE_ID, ROYER_ROOT),
    "relation.royer.resource-contains-edition": ("contains", ROYER_RESOURCE, ROYER_EDITION),
    "relation.royer.edition-contains-work": ("contains", ROYER_EDITION, ROYER_ROOT),
    "relation.royer.work-contains-notes": ("contains", ROYER_ROOT, ROYER_NOTES),
    "relation.royer.work-contains-lab01": ("contains", ROYER_ROOT, ROYER_LAB01),
    "relation.royer.work-contains-lab02": ("contains", ROYER_ROOT, ROYER_LAB02),
    "relation.royer.notes-depend-on-pdf": ("depends-on", ROYER_NOTES, "artifact.royer.notes-pdf"),
    "relation.royer.lab01-depends-on-notebook": ("depends-on", ROYER_LAB01, "artifact.royer.lab01-notebook"),
    "relation.royer.lab02-depends-on-notebook": ("depends-on", ROYER_LAB02, "artifact.royer.lab02-notebook"),
    "relation.royer.penn-ch05-precedes-notes": ("precedes", "unit.penn.v1.ch05", ROYER_NOTES),
}
for page in range(2, 6):
    EXPECTED_RELATIONS[f"relation.mit.l01.contains-p{page:03d}"] = (
        "contains", MIT_L01, f"d90.mit.ocw-6.253.l01.p{page:03d}"
    )
EXPECTED_BY_ENTITY["relation"] = set(EXPECTED_RELATIONS)
EXPECTED_NEW_IDS = set().union(*EXPECTED_BY_ENTITY.values())

BASELINE_ENTITY_COUNTS = {
    "artifact": 152, "asset": 19, "concept": 140, "correction": 142,
    "course": 1, "edition": 4, "learning_surface": 72, "program": 1,
    "qa_event": 105, "relation": 382, "resource": 2, "rights": 57,
    "segment": 84, "term": 127, "unit": 12,
}
EXPECTED_ENTITY_COUNTS = dict(BASELINE_ENTITY_COUNTS)
for entity_type, ids in EXPECTED_BY_ENTITY.items():
    EXPECTED_ENTITY_COUNTS[entity_type] = EXPECTED_ENTITY_COUNTS.get(entity_type, 0) + len(ids)


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), sha256(data)


def record_set_sha256(record_set: list[dict[str, Any]]) -> str:
    return sha256("".join(
        canonical_json(record) + "\n"
        for record in sorted(record_set, key=lambda item: item["id"])
    ).encode("utf-8"))


def id_set_sha256(record_set: list[dict[str, Any]]) -> str:
    return sha256(("\n".join(sorted(record["id"] for record in record_set)) + "\n").encode("utf-8"))


def canonical_record_sha256(record: dict[str, Any]) -> str:
    return sha256((canonical_json(record) + "\n").encode("utf-8"))


def fenced_div_slice(relative: str, anchor: str) -> tuple[int, int, int, str]:
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.strip().startswith("::: {")
        and re.search(rf"#{re.escape(anchor)}(?:\s|\}})", line)
    ]
    if len(starts) != 1:
        raise ValueError(f"expected one #{anchor} in {relative}, found {len(starts)}")
    start = starts[0]
    depth = 0
    for end in range(start, len(lines)):
        stripped = lines[end].strip()
        if stripped.startswith("::: {"):
            depth += 1
        elif stripped == ":::":
            depth -= 1
            if depth == 0:
                break
    else:
        raise ValueError(f"unclosed #{anchor} in {relative}")
    data = ("\n".join(lines[start : end + 1]) + "\n").encode("utf-8")
    return start + 1, end + 1, len(data), sha256(data)


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.main = 0
        self.images = 0
        self.math = 0
        self.display_math = 0
        self.edition_notes = 0
        self.headings: Counter[str] = Counter()
        self.lang = ""
        self.toc_role = ""
        self.skip_target = ""
        self.source_pages: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        if tag == "html": self.lang = values.get("lang", "")
        if values.get("id"): self.ids.append(values["id"])
        if tag == "a" and values.get("href", "").startswith("#"):
            self.fragments.append(values["href"][1:])
            if "skip-link" in classes: self.skip_target = values["href"]
        if tag == "main": self.main += 1
        if tag == "img": self.images += 1
        if tag == "math":
            self.math += 1
            if values.get("display") == "block": self.display_math += 1
        if re.fullmatch(r"h[1-6]", tag): self.headings[tag] += 1
        if "edition-note" in classes: self.edition_notes += 1
        if "source-page" in classes:
            self.source_pages.append((values.get("id", ""), values.get("data-source-page", ""), values.get("data-source-order", "")))
        if values.get("id") == "TOC": self.toc_role = values.get("role", "")


def normalize_allowed(record_id: str, record: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(record, ensure_ascii=False))
    if record_id == COURSE_ID:
        normalized.pop("source_spine_unit_ids", None)
        normalized.pop("source_spine_note", None)
    elif record_id == "unit.habring.v1":
        normalized["order"] = 1
        normalized.pop("curriculum_role", None)
    elif record_id == "unit.penn.v1":
        normalized["status"] = "provisional"
        normalized["order"] = 2
        normalized["admission_state"] = "candidate_ready_for_root_admission"
        normalized.pop("curriculum_role", None)
    elif record_id == "relation.penn.course-contains-work":
        normalized["note"] = "Penn is the smooth numerical-optimization donor."
    elif record_id == "relation.penn.habring-ch09-precedes-ch03":
        normalized["note"] = "Production cursor crosses from the admitted Habring module to the Penn donor."
    elif record_id in ORIGINAL_ARTIFACT_IDENTITIES:
        normalized["bytes"], normalized["sha256"] = ORIGINAL_ARTIFACT_IDENTITIES[record_id]
    return normalized


def main() -> int:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonl_bytes = JSONL.read_bytes()
    csv_bytes = CSV.read_bytes()
    check(jsonl_bytes.endswith(b"\n"), "JSONL lacks final LF")
    check(b"\r" not in jsonl_bytes, "JSONL contains CR bytes")
    raw_lines = jsonl_bytes.decode("utf-8").splitlines()
    records: list[dict[str, Any]] = []
    for index, line in enumerate(raw_lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"JSONL line {index} is invalid: {exc}")
            continue
        records.append(record)
        check(line == canonical_json(record), f"JSONL line {index} is not canonical serialization")
    by_id = {record.get("id"): record for record in records}
    check(len(by_id) == len(records), "duplicate record IDs")
    check(len(records) == BASELINE_COUNT + len(EXPECTED_NEW_IDS), f"record count {len(records)} differs")
    counts = dict(sorted(Counter(record.get("entity_type") for record in records).items()))
    check(counts == dict(sorted(EXPECTED_ENTITY_COUNTS.items())), f"entity counts differ: {counts}")

    new_actual = {record["id"] for record in records if record.get("responsible_workflow") == WORKFLOW}
    check(new_actual == EXPECTED_NEW_IDS, f"new-ID closure differs: missing={sorted(EXPECTED_NEW_IDS-new_actual)} extra={sorted(new_actual-EXPECTED_NEW_IDS)}")
    baseline = [record for record in records if record["id"] not in EXPECTED_NEW_IDS]
    check(len(baseline) == BASELINE_COUNT, "stripped baseline count differs")
    check(id_set_sha256(baseline) == BASELINE_ID_SET_SHA256, "stripped baseline ID-set hash differs")
    immutable = [record for record in baseline if record["id"] not in ALLOWED_EXISTING_IDS]
    check(len(immutable) == IMMUTABLE_BASELINE_COUNT, "immutable baseline count differs")
    check(record_set_sha256(immutable) == IMMUTABLE_BASELINE_RECORD_SET_SHA256, "immutable baseline canonical record set differs")

    for record_id in sorted(ALLOWED_EXISTING_IDS):
        record = by_id.get(record_id, {})
        check(canonical_record_sha256(normalize_allowed(record_id, record)) == ORIGINAL_CANONICAL_SHA256[record_id], f"{record_id}: differs beyond exact authorized fields")
    check(by_id.get(COURSE_ID, {}).get("source_spine_unit_ids") == [MIT_ROOT, "unit.habring.v1", "unit.penn.v1", ROYER_ROOT], "course source-spine order differs")
    check(by_id.get("unit.habring.v1", {}).get("order") == 2, "Habring root order differs")
    check(by_id.get("unit.penn.v1", {}).get("order") == 3 and by_id.get("unit.penn.v1", {}).get("status") == "active", "Penn root admission/order differs")

    rank = {entity: index for index, entity in enumerate(schema["entity_order"])}
    check(records == sorted(records, key=lambda record: (rank[record["entity_type"]], record["id"])), "JSONL order is not canonical")
    id_pattern = re.compile(schema["id_pattern"])
    for record in records:
        check(record.get("schema") == "o015-modular-backend-record", f"{record.get('id')}: record schema differs")
        check(record.get("schema_version") == "1.0.0", f"{record.get('id')}: schema version differs")
        check(bool(id_pattern.fullmatch(record.get("id", ""))), f"{record.get('id')}: invalid ID")
        check(record.get("entity_type") in rank, f"{record.get('id')}: unknown entity type")
        for field in schema["required_common"] + schema["required_by_entity"].get(record.get("entity_type"), []):
            check(field in record, f"{record.get('id')}: missing required field {field}")

    with CSV.open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.reader(handle))
    check(b"\r" not in csv_bytes, "CSV contains CR bytes")
    check(bool(csv_rows) and csv_rows[0] == schema["csv_columns"], "CSV header differs")
    check(len(csv_rows) == len(records) + 1, "CSV row count differs")
    if len(csv_rows) == len(records) + 1:
        for index, (row, record) in enumerate(zip(csv_rows[1:], records), start=2):
            expected = [record["schema"], record["schema_version"], record["entity_type"], record["id"], canonical_json(record)]
            if row != expected:
                errors.append(f"CSV/JSONL mismatch at row {index}")
                break

    target_types = {
        "affected_segment_ids": {"segment"}, "affected_unit_ids": {"unit"},
        "build_event_id": {"qa_event"}, "concept_id": {"concept"}, "concept_ids": {"concept"},
        "course_id": {"course"}, "edition_id": {"edition"}, "evidence_artifact_id": {"artifact"},
        "evidence_event_ids": {"qa_event"}, "input_artifact_ids": {"artifact", "asset"},
        "parent_id": {"unit"}, "prerequisite_ids": {"concept"}, "program_id": {"program"},
        "related_segment_ids": {"segment"}, "resource_id": {"resource"}, "rights_id": {"rights"},
        "source_edition_id": {"edition"}, "source_artifact_id": {"artifact"},
        "target_edition_id": {"edition"}, "unit_id": {"unit"}, "witness_artifact_ids": {"artifact"},
    }
    for record in records:
        for field in schema["reference_fields"]:
            if field not in record or field in {"source_id", "target_id"}:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for target in values:
                if not isinstance(target, str):
                    continue
                check(target in by_id, f"{record['id']}: unresolved {field} -> {target}")
                if target in by_id and field in target_types:
                    check(by_id[target]["entity_type"] in target_types[field], f"{record['id']}: {field} targets {by_id[target]['entity_type']}")

    all_artifact_mismatches: list[str] = []
    rehashed_artifact_ids = EXPECTED_BY_ENTITY["artifact"] | {
        record_id for record_id in ALLOWED_EXISTING_IDS if record_id.startswith("artifact.")
    }
    for record_id in sorted(rehashed_artifact_ids):
        record = by_id.get(record_id, {})
        if record.get("entity_type") != "artifact":
            all_artifact_mismatches.append(f"{record_id}: missing artifact record")
            continue
        relative = record.get("path", "")
        path = ROOT / relative
        if not path.is_file():
            all_artifact_mismatches.append(f"{record['id']}: missing {relative}")
        elif file_info(relative) != (record.get("bytes"), record.get("sha256")):
            all_artifact_mismatches.append(f"{record['id']}: identity differs")
    check(not all_artifact_mismatches, f"artifact rehash failures: {all_artifact_mismatches}")

    freeze = json.loads((ROOT / "00_control/MIT_ROYER_SOURCE_FREEZE.json").read_text(encoding="utf-8"))
    source_authority = json.loads((ROOT / "00_control/SOURCE_AUTHORITY.json").read_text(encoding="utf-8"))
    check(freeze.get("result") == "pass_with_declared_gaps", "source freeze result differs")
    check(freeze.get("selected_external_core") == {"expected_pages": 440, "mit_pages": 395, "pages": 440, "royer_pages": 45}, "selected external core differs")
    authority_ids = {item.get("authority_id") for item in source_authority.get("authorities", [])}
    check({"o015-mit-ocw-6.253-spring-2012", "o015-royer-stochastic-gradient-2023-2024"} <= authority_ids, "source authority lacks MIT/Royer records")
    for record_id in ("artifact.o015.source-authority", "artifact.o015.component-rights", "artifact.o015.adverse-ledger", "artifact.habring.worklog-ch09"):
        record = by_id.get(record_id, {})
        check(file_info(record.get("path", "")) == (record.get("bytes"), record.get("sha256")), f"{record_id}: live refresh differs")

    expected_page_fields = {
        2: (1, "src-mit-l01-p002", "d90-mit-l01-p002", 4, 0),
        3: (2, "src-mit-l01-p003", "d90-mit-l01-p003", 3, 8),
        4: (3, "src-mit-l01-p004", "d90-mit-l01-p004", 5, 4),
        5: (4, "src-mit-l01-p005", "d90-mit-l01-p005", 9, 0),
    }
    authority_pdf_hash = file_info(MIT_PDF)[1]
    for page, (order, source_anchor, target_anchor, items, nested) in expected_page_fields.items():
        record_id = f"d90.mit.ocw-6.253.l01.p{page:03d}"
        record = by_id.get(record_id, {})
        source_slice = fenced_div_slice(MIT_WITNESS, source_anchor)
        target_slice = fenced_div_slice(MIT_TARGET, target_anchor)
        check(record.get("order") == order and record.get("unit_id") == MIT_L01, f"{record_id}: order/unit differs")
        check((record.get("source_line_start"), record.get("source_line_end"), record.get("source_bytes"), record.get("source_content_sha256")) == source_slice, f"{record_id}: source slice differs")
        check((record.get("target_line_start"), record.get("target_line_end"), record.get("target_bytes"), record.get("target_content_sha256")) == target_slice, f"{record_id}: target slice differs")
        check(record.get("source_anchor") == source_anchor and record.get("target_anchor") == target_anchor, f"{record_id}: anchor map differs")
        check(record.get("source_pdf_path") == MIT_PDF and record.get("source_pdf_page") == page and record.get("source_pdf_sha256") == authority_pdf_hash, f"{record_id}: PDF page/hash binding differs")
        check(record.get("source_item_count") == items and record.get("nested_source_bullet_count") == nested, f"{record_id}: topology facts differ")

    witness_text = (ROOT / MIT_WITNESS).read_text(encoding="utf-8")
    target_text = (ROOT / MIT_TARGET).read_text(encoding="utf-8")
    for page, (_, source_anchor, target_anchor, item_count, _) in expected_page_fields.items():
        check(witness_text.count(f"#{source_anchor} ") == 1, f"witness page anchor {source_anchor} differs")
        check(target_text.count(f"#{target_anchor} ") == 1, f"target page anchor {target_anchor} differs")
        for item in range(1, item_count + 1):
            source_item = f"src-mit-l01-p{page:03d}-i{item:03d}"
            target_item = f"d90-mit-l01-p{page:03d}-i{item:03d}"
            check(witness_text.count(f"#{source_item} ") == 1, f"witness item anchor {source_item} differs")
            check(target_text.count(f"#{target_item} ") == 1, f"target item anchor {target_item} differs")

    surface = SurfaceParser()
    surface.feed((ROOT / MIT_HTML).read_text(encoding="utf-8"))
    duplicates = sorted(identifier for identifier, count in Counter(surface.ids).items() if count > 1)
    unresolved = sorted(set(surface.fragments) - set(surface.ids))
    check(surface.lang == "id-ID" and surface.main == 1, "HTML language/main landmark differs")
    check(surface.headings == Counter({"h2": 6, "h1": 1, "h3": 1}), f"HTML heading topology differs: {surface.headings}")
    check(surface.math == 14 and surface.display_math == 2, "HTML MathML topology differs")
    check(surface.images == 0 and surface.edition_notes == 3, "HTML image/edition-note counts differ")
    check(surface.toc_role == "doc-toc" and surface.skip_target == "#d90-mit-l01-p002", "HTML navigation semantics differ")
    check(not duplicates and not unresolved, f"HTML ID/fragment failures: {duplicates}/{unresolved}")
    check(sorted(surface.source_pages, key=lambda item: int(item[2])) == [(f"d90-mit-l01-p{page:03d}", str(page), str(page-1)) for page in range(2, 6)], "HTML source-page map differs")

    report = json.loads((ROOT / MIT_REPORT).read_text(encoding="utf-8"))
    browser = json.loads((ROOT / MIT_BROWSER).read_text(encoding="utf-8"))
    check(report.get("result") == "pass" and report.get("errors") == [], "pilot validation report fails")
    check(report.get("boundary") == {"display_formulas": 2, "figures": 0, "nested_source_bullets": 12, "next_topic_starts_source_page": 6, "source_items": 21, "source_pdf_pages": [2, 3, 4, 5]}, "pilot boundary facts differ")
    check(report.get("build", {}).get("deterministic_rebuilds") == 2, "deterministic build count differs")
    check(report.get("build", {}).get("html_sha256") == file_info(MIT_HTML)[1] and report.get("build", {}).get("pdf_sha256") == file_info(MIT_READER_PDF)[1], "build output hashes differ")
    check(report.get("html", {}).get("mathml_nodes") == 14 and report.get("html", {}).get("display_mathml_nodes") == 2, "reported HTML formula facts differ")
    check(browser.get("result") == "pass" and browser.get("surface", {}).get("sha256") == file_info(MIT_HTML)[1], "browser QA binding differs")
    check(browser.get("desktop", {}).get("horizontal_overflow") is False and browser.get("desktop", {}).get("display_math_overflow") is False, "desktop overflow reported")
    check(browser.get("mobile", {}).get("horizontal_overflow") is False and browser.get("console_warnings_or_errors") == [], "mobile/console browser facts differ")
    check(r"f:\mathbb{R}^n\mapsto\mathbb{R}" in witness_text, "witness does not preserve mapsto")
    for formula in (r"K^{\circ\circ}=K", r"f^{**}=f"):
        check(formula in target_text, f"target lacks formula {formula}")
    check(target_text.count("$$") == 4, "target display-formula fence count differs")

    adverse_records = [json.loads(line) for line in (ROOT / "00_control/ADVERSE_LEDGER.jsonl").read_text(encoding="utf-8").splitlines() if line]
    adverse_by_id = {record.get("event_id"): record for record in adverse_records}
    check(len(adverse_by_id) == len(adverse_records), "adverse ledger event IDs are not unique")
    correction_map = {
        "O015-MIT-SEM-0001": (4, "d90-mit-l01-note-dual-discrete", "d90.mit.ocw-6.253.l01.p004"),
        "O015-MIT-SEM-0002": (5, "d90-mit-l01-note-self-dual", "d90.mit.ocw-6.253.l01.p005"),
        "O015-MIT-SEM-0003": (4, "d90-mit-l01-note-function-arrow", "d90.mit.ocw-6.253.l01.p004"),
    }
    for event_id, (page, anchor, segment_id) in correction_map.items():
        record = by_id.get(f"correction.{event_id.lower()}", {})
        event = adverse_by_id.get(event_id, {})
        target_slice = fenced_div_slice(MIT_TARGET, anchor)
        check(record.get("source_event_id") == event_id and record.get("affected_segment_ids") == [segment_id], f"{event_id}: affected closure differs")
        check(record.get("source_pdf_page") == page and record.get("source_pdf_sha256") == authority_pdf_hash, f"{event_id}: source PDF binding differs")
        check(record.get("surface") == event.get("surface") and record.get("source_issue") == event.get("source_issue") and record.get("target_action") == event.get("target_action"), f"{event_id}: adverse-ledger semantics differ")
        check((record.get("target_line_start"), record.get("target_line_end"), record.get("target_bytes"), record.get("target_content_sha256")) == target_slice, f"{event_id}: correction slice differs")
        check(f'data-correction-id="{event_id}"' in target_text, f"{event_id}: target correction anchor missing")
    check(report.get("mathematical_review", {}).get("clarification_ids") == list(correction_map), "reported correction IDs differ")
    check(report.get("mathematical_review", {}).get("p1_open") == 0 and report.get("mathematical_review", {}).get("p2_open") == 0 and report.get("mathematical_review", {}).get("p3_open") == 0, "reported open mathematical defects differ")

    pdf = PdfReader(ROOT / MIT_READER_PDF)
    pdf_root = pdf.trailer["/Root"]
    check(len(pdf.pages) == 3, "reader PDF page count differs")
    check(pdf_root.get("/Lang") == "id-ID" and "/StructTreeRoot" not in pdf_root, "reader PDF language/tagging facts differ")
    searchable = "\n".join(page.extract_text() or "" for page in pdf.pages)
    for phrase in ("Peran Kekonveksan dalam Optimisasi", "Sejarah dan Prasejarah", "Masalah Optimisasi", "Identitas sumber dan perubahan"):
        check(phrase in searchable, f"reader PDF lacks searchable phrase {phrase!r}")
    fonts: dict[str, bool] = {}
    for page in pdf.pages:
        for name, reference in page.get("/Resources", {}).get("/Font", {}).items():
            fonts[str(name)] = bool(reference.get_object().get("/ToUnicode"))
        check(abs(float(page.mediabox.width) - 595.276) < 0.02 and abs(float(page.mediabox.height) - 841.89) < 0.02, "reader PDF is not A4")
    check(bool(fonts) and all(fonts.values()), f"reader PDF fonts lack ToUnicode: {fonts}")
    check(report.get("pdf", {}).get("tagged") is False and report.get("pdf", {}).get("searchable") is True and report.get("pdf", {}).get("all_pages_visually_inspected") is True, "reported PDF/accessibility facts differ")

    with (ROOT / "00_control/COMPONENT_RIGHTS.csv").open(encoding="utf-8", newline="") as handle:
        rights_rows = list(csv.DictReader(handle))
    rights_by_component = {row["component_id"]: row for row in rights_rows}
    controlled_mapping = {
        "rights.o015-mit-course": "o015-mit-6253",
        "rights.o015-mit-teaching-closure": "o015-mit-teaching-closure",
        "rights.o015-mit-athena-figures": "o015-mit-athena-figures",
        "rights.o015-mit-semantic-witness": "o015-mit-semantic-witness",
        "rights.o015-mit-id-pilot": "o015-mit-id-pilot",
        "rights.o015-mit-pilot-build-qa": "o015-mit-pilot-build-qa",
        "rights.o015-royer-notes": "o015-royer-notes",
        "rights.o015-royer-lab01": "o015-royer-lab01",
        "rights.o015-royer-lab02": "o015-royer-lab02",
        "rights.o015-royer-supplements": "o015-royer-supplements",
    }
    check(len(rights_by_component) == len(rights_rows), "component-rights IDs are not unique")
    for rights_id, component_id in controlled_mapping.items():
        record = by_id.get(rights_id, {})
        row = rights_by_component.get(component_id, {})
        check(record.get("component_id") == component_id, f"{rights_id}: component binding differs")
        for record_field, row_field in (("path", "path"), ("source_authority_id", "source_authority"), ("rights_expression", "rights_expression"), ("component_ledger_status", "status"), ("component_ledger_required_handling", "required_handling"), ("notes", "notes")):
            check(record.get(record_field) == row.get(row_field), f"{rights_id}: ledger field {record_field} differs")
    check(by_id.get("rights.o015-mit-athena-figures", {}).get("status") == "excluded", "Athena component is not excluded")
    check(surface.images == 0 and "![" not in target_text, "pilot introduces an image")
    component_ids = [by_id[rights_id]["component_id"] for rights_id in EXPECTED_BY_ENTITY["rights"]]
    check(len(component_ids) == len(set(component_ids)), "new rights records are not component-distinct")

    surface_expectations = {
        "surface.mit.l01.exercise-inventory": ("absent", 0),
        "surface.mit.l01.hint-inventory": ("absent", 0),
        "surface.mit.l01.answer-inventory": ("absent", 0),
        "surface.mit.l01.solution-inventory": ("absent", 0),
        "surface.royer.notes.exercise-inventory": ("present", 3),
        "surface.royer.notes.solution-inventory": ("present", 3),
        "surface.royer.notes.hint-inventory": ("absent", 0),
    }
    for record_id, (presence, count) in surface_expectations.items():
        check(by_id.get(record_id, {}).get("presence") == presence and by_id.get(record_id, {}).get("count") == count, f"{record_id}: inventory differs")
    lab01 = by_id.get("surface.royer.lab01.notebook", {})
    lab02 = by_id.get("surface.royer.lab02.notebook", {})
    check(lab01.get("completion_state") == "substantially_executed" and lab01.get("environment_pinned") is False and lab01.get("empty_code_cells") == 0, "Royer lab01 facts differ")
    check(lab02.get("presence") == "incomplete" and lab02.get("empty_code_cells") == 4 and lab02.get("unanswered_discussion_cells") == 4 and lab02.get("optional_momentum_adam_implemented") is False and lab02.get("environment_pinned") is False, "Royer lab02 gap facts differ")
    check(by_id.get("surface.mit.l01.semantic-html", {}).get("primary_accessible_surface") is True and by_id.get("surface.mit.l01.reflowed-pdf", {}).get("tagged") is False, "learning-surface accessibility facts differ")

    for relation_id, expected in EXPECTED_RELATIONS.items():
        record = by_id.get(relation_id, {})
        actual = (record.get("relation_type"), record.get("source_id"), record.get("target_id"))
        check(actual == expected, f"{relation_id}: relation triple differs: {actual}")
        if actual == expected:
            check(expected[1] in by_id and expected[2] in by_id, f"{relation_id}: unresolved endpoint")
    endpoint_pairs = {
        "contains": {("course", "unit"), ("unit", "unit"), ("unit", "segment"), ("resource", "edition"), ("edition", "unit")},
        "adapts": {("artifact", "artifact")}, "translates": {("artifact", "artifact")},
        "depends-on": {("artifact", "artifact"), ("unit", "artifact")},
        "precedes": {("unit", "unit")},
    }
    for relation_id in EXPECTED_RELATIONS:
        relation = by_id.get(relation_id, {})
        source = by_id.get(relation.get("source_id"), {})
        target = by_id.get(relation.get("target_id"), {})
        pair = (source.get("entity_type"), target.get("entity_type"))
        check(pair in endpoint_pairs.get(relation.get("relation_type"), set()), f"{relation_id}: invalid endpoint types {pair}")

    relation_triples = Counter(
        (record["relation_type"], record["source_id"], record["target_id"])
        for record in records if record.get("entity_type") == "relation"
    )
    duplicates_actual = {triple: count for triple, count in relation_triples.items() if count > 1}
    duplicates_expected = {
        ("contains", "resource.penn.math555-nonlinear-programming", "edition.penn.math555.id-id.v1"): 2,
        ("contains", "resource.penn.math555-nonlinear-programming", "edition.penn.math555.source-v1-0"): 2,
    }
    check(duplicates_actual == duplicates_expected, f"relation uniqueness differs: {duplicates_actual}")

    spine_orders = {MIT_ROOT: 1, "unit.habring.v1": 2, "unit.penn.v1": 3, ROYER_ROOT: 4}
    check(all(by_id.get(unit_id, {}).get("order") == order for unit_id, order in spine_orders.items()), "source-spine unit order differs")
    check(by_id.get("relation.penn.habring-ch09-precedes-ch03", {}).get("source_id") == "unit.habring.v1.ch09" and by_id.get("relation.penn.habring-ch09-precedes-ch03", {}).get("target_id") == "unit.penn.v1.ch03", "Habring-to-Penn topology differs")

    report_out = {
        "allowed_changed_existing_ids": sorted(ALLOWED_EXISTING_IDS),
        "artifact_records_rehashed": len(rehashed_artifact_ids),
        "baseline": {"record_count": BASELINE_COUNT, "jsonl": {"bytes": BASELINE_JSONL[0], "sha256": BASELINE_JSONL[1]}, "csv": {"bytes": BASELINE_CSV[0], "sha256": BASELINE_CSV[1]}},
        "csv": {"bytes": len(csv_bytes), "sha256": sha256(csv_bytes)},
        "entity_counts": counts,
        "errors": errors,
        "jsonl": {"bytes": len(jsonl_bytes), "sha256": sha256(jsonl_bytes)},
        "new_entity_counts": {entity: len(ids) for entity, ids in sorted(EXPECTED_BY_ENTITY.items())},
        "new_ids_sha256": sha256(("\n".join(sorted(EXPECTED_NEW_IDS)) + "\n").encode("utf-8")),
        "new_record_count": len(EXPECTED_NEW_IDS),
        "record_count": len(records),
        "result": "pass" if not errors else "fail",
    }
    print(json.dumps(report_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
