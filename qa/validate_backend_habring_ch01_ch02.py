#!/usr/bin/env python3
"""Validate and deterministically regenerate the Habring Chapters 1--2 backend."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import extend_backend_habring_ch01_ch02 as gen


ROOT = Path(__file__).resolve().parents[1]
JSONL_PATH = ROOT / "backend" / "records.jsonl"
CSV_PATH = ROOT / "backend" / "records.csv"
RECEIPT_PATH = ROOT / "qa" / "HABRING_CH01_CH02_BACKEND_VALIDATION.json"
EXPECTED_NEW_COUNT = gen.EXPECTED_NEW_RECORD_COUNT
EXPECTED_ENTITY_COUNTS = gen.EXPECTED_ENTITY_COUNTS


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_info(relative: str) -> tuple[int, str]:
    data = (ROOT / relative).read_bytes()
    return len(data), digest(data)


def load_projection(
    jsonl_path: Path, csv_path: Path
) -> tuple[list[dict[str, Any]], bytes, bytes]:
    jsonl_raw = jsonl_path.read_bytes()
    csv_raw = csv_path.read_bytes()
    records = [json.loads(line) for line in jsonl_raw.decode("utf-8").splitlines() if line]
    rows = list(csv.DictReader(io.StringIO(csv_raw.decode("utf-8"))))
    if [json.loads(row["record_json"]) for row in rows] != records:
        raise ValueError("CSV record_json projection differs from JSONL")
    if len(rows) != len(records):
        raise ValueError("CSV row count differs from JSONL")
    for row, record in zip(rows, records, strict=True):
        if [row["schema"], row["schema_version"], row["entity_type"], row["id"]] != [
            record["schema"],
            record["schema_version"],
            record["entity_type"],
            record["id"],
        ]:
            raise ValueError(f"CSV projection columns differ for {record['id']}")
    return records, jsonl_raw, csv_raw


def validate_schema_and_references(records: list[dict[str, Any]]) -> None:
    schema = json.loads((ROOT / "backend" / "backend_schema.json").read_text(encoding="utf-8"))
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("backend contains duplicate IDs")
    all_ids = set(ids)
    pattern = re.compile(schema["id_pattern"])
    rank = {entity: index for index, entity in enumerate(schema["entity_order"])}
    expected_order = sorted(records, key=lambda item: (rank[item["entity_type"]], item["id"]))
    if records != expected_order:
        raise ValueError("backend entity/id order differs from canonical order")

    for record in records:
        if record.get("schema") != gen.RECORD_SCHEMA or record.get("schema_version") != gen.SCHEMA_VERSION:
            raise ValueError(f"record schema differs: {record.get('id')}")
        if not pattern.fullmatch(record["id"]):
            raise ValueError(f"invalid ID: {record['id']}")
        required = schema["required_common"] + schema["required_by_entity"].get(
            record["entity_type"], []
        )
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"{record['id']} missing fields {missing}")
        for field in schema.get("reference_fields", []):
            if field not in record:
                continue
            values = record[field] if isinstance(record[field], list) else [record[field]]
            for value in values:
                if value not in all_ids:
                    raise ValueError(f"{record['id']} has dangling {field}: {value}")


def canonical_record_map(records: list[dict[str, Any]]) -> dict[str, str]:
    return {record["id"]: gen.canonical_json(record) for record in records}


def validate_generated_projection(
    records: list[dict[str, Any]], jsonl_raw: bytes, csv_raw: bytes
) -> dict[str, Any]:
    baseline = [
        record
        for record in records
        if record.get("responsible_workflow") != gen.WORKFLOW
    ]
    new_records = [
        record
        for record in records
        if record.get("responsible_workflow") == gen.WORKFLOW
    ]
    stripped_jsonl = gen.strip_workflow_jsonl(jsonl_raw)
    stripped_csv = gen.strip_workflow_csv(csv_raw)
    gen.assert_raw_baseline(stripped_jsonl, stripped_csv, "validator-stripped dataset")
    if (
        len(baseline) != gen.BASELINE_RECORD_COUNT
        or gen.id_set_sha256(baseline) != gen.BASELINE_ID_SET_SHA256
        or gen.id_order_sha256(baseline) != gen.BASELINE_ID_ORDER_SHA256
        or gen.record_set_sha256(baseline) != gen.BASELINE_RECORD_SET_SHA256
    ):
        raise ValueError("protected baseline record identities differ")
    if len(new_records) != EXPECTED_NEW_COUNT:
        raise ValueError(f"new record count differs: {len(new_records)}")
    new_counts = Counter(record["entity_type"] for record in new_records)
    if new_counts != EXPECTED_ENTITY_COUNTS:
        raise ValueError(f"new entity topology differs: {dict(new_counts)}")

    gen.validate_frozen_identities()
    evidence = gen.load_build_evidence()
    expected = gen.generate_records(baseline, evidence)
    if canonical_record_map(expected) != canonical_record_map(new_records):
        expected_map = canonical_record_map(expected)
        actual_map = canonical_record_map(new_records)
        missing = sorted(expected_map.keys() - actual_map.keys())
        extra = sorted(actual_map.keys() - expected_map.keys())
        changed = sorted(
            record_id
            for record_id in expected_map.keys() & actual_map.keys()
            if expected_map[record_id] != actual_map[record_id]
        )
        raise ValueError(
            f"generated record projection differs; missing={missing}, extra={extra}, changed={changed}"
        )

    segment_records = [record for record in new_records if record["entity_type"] == "segment"]
    if [record["id"] for record in sorted(segment_records, key=lambda item: item["id"])] != sorted(
        gen.EXPECTED_SEGMENT_IDS["ch01"] + gen.EXPECTED_SEGMENT_IDS["ch02"]
    ):
        raise ValueError("25-segment stable-ID closure differs")
    for record in segment_records:
        source = gen.normalized_slice(
            record["source_path"], record["source_line_start"], record["source_line_end"]
        )
        target = gen.normalized_slice(
            record["target_path"], record["target_line_start"], record["target_line_end"]
        )
        if source != (record["source_content_bytes"], record["source_content_sha256"]):
            raise ValueError(f"source segment binding differs: {record['id']}")
        if target != (record["target_content_bytes"], record["target_content_sha256"]):
            raise ValueError(f"target segment binding differs: {record['id']}")

    surfaces = [record for record in new_records if record["entity_type"] == "learning_surface"]
    present = [record for record in surfaces if record["presence"] == "present"]
    absent = [record for record in surfaces if record["presence"] == "absent"]
    if len(present) != 219 or len(absent) != 6:
        raise ValueError("learning-surface closure differs from 219 present plus six absences")
    for record in present:
        current = gen.normalized_slice(
            record["target_path"], record["target_line_start"], record["target_line_end"]
        )
        if current != (record["target_content_bytes"], record["target_content_sha256"]):
            raise ValueError(f"surface slice binding differs: {record['id']}")

    corrections = [record for record in new_records if record["entity_type"] == "correction"]
    if [record["source_event_id"] for record in corrections] != gen.EXPECTED_CORRECTION_IDS:
        raise ValueError("correction record order/closure differs")
    for record in corrections:
        binding = record["ledger_binding"]
        raw = (ROOT / binding["path"]).read_bytes().splitlines(keepends=True)[binding["line"] - 1]
        if (len(raw), digest(raw)) != (binding["raw_line_bytes"], binding["raw_line_sha256"]):
            raise ValueError(f"correction ledger line differs: {record['id']}")

    artifacts = [record for record in new_records if record["entity_type"] == "artifact"]
    for record in artifacts:
        if file_info(record["path"]) != (record["bytes"], record["sha256"]):
            raise ValueError(f"artifact bytes differ: {record['id']}")
    assets = [record for record in new_records if record["entity_type"] == "asset"]
    if len(assets) != 5:
        raise ValueError("inherited asset count differs from five")
    for record in assets:
        if file_info(record["source_path"]) != (
            record["source_bytes"],
            record["source_sha256"],
        ):
            raise ValueError(f"asset source differs: {record['id']}")
        if file_info(record["target_path"]) != (
            record["target_bytes"],
            record["target_sha256"],
        ):
            raise ValueError(f"asset target differs: {record['id']}")
        if record["source_sha256"] != record["target_sha256"]:
            raise ValueError(f"asset is not an exact copy: {record['id']}")

    qa_events = [record for record in new_records if record["entity_type"] == "qa_event"]
    if len(qa_events) != 11 or any(record["result"] != "pass" for record in qa_events):
        raise ValueError("backend QA-event pass closure differs")
    if any(record.get("upstream_report_disposition") != "not_submitted" for record in corrections):
        raise ValueError("correction upstream disposition differs")

    return {
        "baseline": baseline,
        "new_records": new_records,
        "evidence": evidence,
        "entity_counts": new_counts,
    }


def deterministic_regeneration(
    jsonl_path: Path, csv_path: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    run_reports: list[dict[str, Any]] = []
    outputs: list[tuple[bytes, bytes]] = []
    with tempfile.TemporaryDirectory(prefix="o015-habring-backend-validate-") as temporary:
        temporary_root = Path(temporary)
        for run in (1, 2):
            output_dir = temporary_root / f"run-{run}"
            process = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / gen.GENERATOR),
                    "--input-jsonl",
                    str(jsonl_path),
                    "--input-csv",
                    str(csv_path),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(process.stdout)
            jsonl = (output_dir / "records.jsonl").read_bytes()
            csv_data = (output_dir / "records.csv").read_bytes()
            if report["jsonl"] != {"bytes": len(jsonl), "sha256": digest(jsonl)}:
                raise ValueError(f"generator run {run} JSONL report differs")
            if report["csv"] != {"bytes": len(csv_data), "sha256": digest(csv_data)}:
                raise ValueError(f"generator run {run} CSV report differs")
            run_reports.append(report)
            outputs.append((jsonl, csv_data))

    canonical = (jsonl_path.read_bytes(), csv_path.read_bytes())
    if outputs[0] != outputs[1]:
        raise ValueError("two deterministic regenerations differ")
    if outputs[0] != canonical:
        raise ValueError("deterministic regeneration differs from canonical backend")
    return run_reports, {
        "runs": 2,
        "byte_identical_between_runs": True,
        "byte_identical_to_canonical": True,
    }


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".stage",
            dir=path.parent,
            delete=False,
        ) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            staged = Path(handle.name)
        if staged.read_bytes() != data:
            raise ValueError("staged receipt readback differs")
        os.replace(staged, path)
        staged = None
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", type=Path, default=JSONL_PATH)
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--receipt", type=Path, default=RECEIPT_PATH)
    args = parser.parse_args()

    records, jsonl_raw, csv_raw = load_projection(args.jsonl, args.csv)
    validate_schema_and_references(records)
    validated = validate_generated_projection(records, jsonl_raw, csv_raw)
    regeneration_reports, regeneration = deterministic_regeneration(args.jsonl, args.csv)
    new_records = validated["new_records"]
    evidence = validated["evidence"]

    receipt = {
        "schema": "o015-habring-ch01-ch02-backend-validation-v1",
        "result": "pass",
        "workflow": gen.WORKFLOW,
        "recorded_at": gen.RECORDED_AT,
        "protected_baseline": {
            "records": gen.BASELINE_RECORD_COUNT,
            "jsonl": {"bytes": gen.BASELINE_JSONL[0], "sha256": gen.BASELINE_JSONL[1]},
            "csv": {"bytes": gen.BASELINE_CSV[0], "sha256": gen.BASELINE_CSV[1]},
            "record_bytes_and_relative_order_stable": True,
        },
        "admission": {
            "new_records": len(new_records),
            "entity_counts": dict(sorted(validated["entity_counts"].items())),
            "new_id_set_sha256": gen.id_set_sha256(new_records),
            "stable_segment_count": 25,
            "stable_segment_ids": gen.EXPECTED_SEGMENT_IDS["ch01"] + gen.EXPECTED_SEGMENT_IDS["ch02"],
            "present_learning_surfaces": 219,
            "formal_absence_surfaces": 6,
            "correction_event_ids": gen.EXPECTED_CORRECTION_IDS,
            "inherited_exact_copy_assets": 5,
        },
        "canonical_backend": {
            "records": len(records),
            "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
            "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
            "id_set_sha256": gen.id_set_sha256(records),
            "record_set_sha256": gen.record_set_sha256(records),
        },
        "reader_artifacts": {
            "unit_pdf": evidence["unit"]["artifact"],
            "full_html": evidence["html"]["artifact"],
            "full_reader_pdf": evidence["reader"]["artifact"],
            "full_epub": evidence["epub"]["artifact"],
        },
        "generation_runs": [
            {
                "run": index,
                "jsonl": report["jsonl"],
                "csv": report["csv"],
                "new_record_count": report["new_record_count"],
                "final_record_count": report["final_record_count"],
            }
            for index, report in enumerate(regeneration_reports, start=1)
        ],
        "deterministic_regeneration": regeneration,
        "checks": [
            "lossless CSV projection equals JSONL",
            "schema-required fields and every declared reference resolve",
            "all 2,472 baseline record bytes and their relative order are unchanged",
            "25 stable segments bind exact source and target line slices",
            "219 semantic/math surfaces bind exact target slices",
            "65 correction records bind exact lines in two correction snapshots",
            "five inherited raster assets are byte-identical to authority files",
            "all recorded artifact byte counts and SHA-256 values match live files",
            "two regenerated backend pairs are byte-identical to each other and canonical",
        ],
    }
    receipt_bytes = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    atomic_write(args.receipt, receipt_bytes)
    print(
        json.dumps(
            {
                "result": "pass",
                "record_count": len(records),
                "new_record_count": len(new_records),
                "jsonl": {"bytes": len(jsonl_raw), "sha256": digest(jsonl_raw)},
                "csv": {"bytes": len(csv_raw), "sha256": digest(csv_raw)},
                "receipt": {
                    "path": str(args.receipt),
                    "bytes": len(receipt_bytes),
                    "sha256": digest(receipt_bytes),
                },
                "deterministic_regeneration": regeneration,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
