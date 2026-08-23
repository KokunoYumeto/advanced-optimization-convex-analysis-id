#!/usr/bin/env python3
"""Validate the bounded O015 Indonesian terminology-QA transaction."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "backend/backend_schema.json").read_text(encoding="utf-8"))
JSONL = ROOT / "backend/records.jsonl"
CSV = ROOT / "backend/records.csv"

EXPECTED_COUNT = 1300
EXPECTED_ENTITY_COUNTS = {
    "artifact": 152,
    "asset": 19,
    "concept": 140,
    "correction": 142,
    "course": 1,
    "edition": 4,
    "learning_surface": 72,
    "program": 1,
    "qa_event": 105,
    "relation": 382,
    "resource": 2,
    "rights": 57,
    "segment": 84,
    "term": 127,
    "unit": 12,
}

EXPECTED_FILES = {
    "source/id-ID/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex": (
        8012,
        "aa0f05ba886ec8f338e388ea612659ce3e45a959180d303c8b2046e094be4f92",
    ),
    "source/id-ID/D90-PENN-05-metode-newton-dan-koreksi-id.tex": (
        7227,
        "7de8bc61dc3f59999ac6414df90ef6925d5a7d4665f79d71998c8f0e45839c14",
    ),
    "source/id-ID/penn-06-metode-arah-konjugat-id.tex": (
        30634,
        "5be39001823792d99fcbfb9d8cb55d8b98db77bd76d426dbbf1ae57e99bf8c46",
    ),
    "output/pdf/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf": (
        847337,
        "18e7162f8d1e55a050ee96a6ba05a2ffaa0d5cb578f96e264152666a79dc83a8",
    ),
    "output/pdf/D90-PENN-05-metode-newton-dan-koreksi-id.pdf": (
        2691773,
        "dad34c7cb363197da1ae87117b22b2dde21d6d183997745cd3ffff62245c0b96",
    ),
    "build/penn-unit-04-id/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.log": (
        27652,
        "5fd0e4c57d30c21a35316ce108386f7e07fef866140d766f0ea3185bbbf3066c",
    ),
    "build/penn-unit-05-id/D90-PENN-05-metode-newton-dan-koreksi-id.log": (
        27150,
        "377549051f61dcee9dcebcc72821c76c4c3f659119313f84552923895bcf3d3c",
    ),
    "qa/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.txt": (
        26415,
        "080ae5b96f03d537a74b0336ff1a1c4ad0158bd3487c8f98679d1f6b5f0070dd",
    ),
    "qa/D90-PENN-05-metode-newton-dan-koreksi-id.txt": (
        29192,
        "9870de7de7be5d34afe2ba7842e69200193542dc7a83cc99d6193cf8967e4da1",
    ),
    "qa/PENN_CH04_VISUAL_QA.json": (
        2019,
        "0f39bf33ef16e7df90df3f24902ee9a90b64bdcb7139b0e6c0f4713a5eae1f95",
    ),
    "qa/PENN_CH05_VISUAL_QA.json": (
        2862,
        "16c326fb91270c83c83ee7f29a091638aa8eed6210f91af48a11d3974a9f255e",
    ),
    "authority/comparator/indonesian-terminology/caturiyati-lestari-2011/landing.html": (
        21286,
        "088f79135da630d7230e7e7d656163bd4e47d4aff1a569235e10532b8d9bd620",
    ),
    "authority/comparator/indonesian-terminology/caturiyati-lestari-2011/M-45-Caturiyati.pdf": (
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


errors: list[str] = []
records = [
    json.loads(line)
    for line in JSONL.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
by_id = {record["id"]: record for record in records}

if len(by_id) != len(records):
    errors.append("duplicate record IDs")
if len(records) != EXPECTED_COUNT:
    errors.append(f"record count {len(records)} != {EXPECTED_COUNT}")
counts = dict(sorted(Counter(record["entity_type"] for record in records).items()))
if counts != EXPECTED_ENTITY_COUNTS:
    errors.append(f"entity counts differ: {counts}")

rank = {entity: index for index, entity in enumerate(SCHEMA["entity_order"])}
if records != sorted(records, key=lambda record: (rank[record["entity_type"]], record["id"])):
    errors.append("JSONL record order is not canonical")

with CSV.open(encoding="utf-8", newline="") as handle:
    rows = list(csv.reader(handle))
if not rows or rows[0] != SCHEMA["csv_columns"]:
    errors.append("CSV header differs from schema")
elif len(rows) != len(records) + 1:
    errors.append("CSV row count differs from JSONL")
else:
    for index, (row, record) in enumerate(zip(rows[1:], records), start=2):
        expected = [
            record["schema"],
            record["schema_version"],
            record["entity_type"],
            record["id"],
            canonical_json(record),
        ]
        if row != expected:
            errors.append(f"CSV/JSONL mismatch at row {index}")
            break

required_common = SCHEMA["required_common"]
for record in records:
    for field in required_common:
        if field not in record:
            errors.append(f"{record.get('id')}: missing common field {field}")
    for field in SCHEMA["required_by_entity"].get(record["entity_type"], []):
        if field not in record:
            errors.append(f"{record['id']}: missing required field {field}")

reference_fields = set(SCHEMA["reference_fields"])
for record in records:
    for field, value in record.items():
        if field not in reference_fields:
            continue
        values = value if isinstance(value, list) else [value]
        for target in values:
            if isinstance(target, str) and target not in by_id:
                errors.append(f"{record['id']}: unresolved {field} -> {target}")

for relative, expected in EXPECTED_FILES.items():
    actual = file_info(relative)
    if actual != expected:
        errors.append(f"file identity mismatch: {relative}: {actual} != {expected}")

for relative in (
    "source/id-ID/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex",
    "source/id-ID/D90-PENN-05-metode-newton-dan-koreksi-id.tex",
    "source/id-ID/penn-06-metode-arah-konjugat-id.tex",
):
    text = (ROOT / relative).read_text(encoding="utf-8")
    if re.search(r"\b[Pp]ertidaksamaan\b", text):
        errors.append(f"unpropagated pertidaksamaan remains in {relative}")

for relative in (
    "build/penn-unit-04-id/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.log",
    "build/penn-unit-05-id/D90-PENN-05-metode-newton-dan-koreksi-id.log",
):
    text = (ROOT / relative).read_text(encoding="utf-8", errors="replace")
    for forbidden in (
        "undefined references",
        "LaTeX Warning: Citation",
        "LaTeX Warning: Reference",
        "Overfull \\hbox",
        "Fatal error",
        "Emergency stop",
    ):
        if forbidden in text:
            errors.append(f"{relative}: build log contains {forbidden!r}")

for relative, pages in (
    ("output/pdf/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf", 17),
    ("output/pdf/D90-PENN-05-metode-newton-dan-koreksi-id.pdf", 15),
):
    completed = subprocess.run(
        ["pdfinfo", str(ROOT / relative)], capture_output=True, text=True, check=True
    )
    info = completed.stdout
    if f"Pages:           {pages}" not in info:
        errors.append(f"{relative}: page count differs")
    if "Page size:       595.276 x 841.89 pts (A4)" not in info:
        errors.append(f"{relative}: not A4")
    if "Encrypted:       no" not in info:
        errors.append(f"{relative}: encryption state differs")

term_expectations = {
    "term.convex-optimization": ("optimisasi konveks", ["optimasi konveks"]),
    "term.terminology-affine": ("afin", ["affine"]),
    "term.terminology-feasible": ("layak", []),
    "term.terminology-inequality": ("ketaksamaan", ["pertidaksamaan"]),
    "term.terminology-objective-function": (
        "fungsi tujuan",
        ["fungsi objektif", "objektif", "fungsi biaya"],
    ),
    "term.supporting-hyperplane": (
        "hiperbidang pendukung",
        ["bidang hiper penyokong", "bidang hiper pendukung"],
    ),
}
for record_id, (preferred, variants) in term_expectations.items():
    record = by_id.get(record_id)
    if not record or record.get("preferred") != preferred or record.get("variants") != variants:
        errors.append(f"{record_id}: terminology decision differs")

model = "OpenAI Codex gpt-5.6-sol, Ultra"
for relative in ("README.md", "PROVENANCE.md"):
    if model not in (ROOT / relative).read_text(encoding="utf-8"):
        errors.append(f"exact model identification absent from {relative}")
if by_id.get("artifact.o015.model-provenance", {}).get("model_identification") != model:
    errors.append("backend model identification differs")

qa_event = by_id.get("qa.o015.terminology-qa-20260822", {})
if qa_event.get("result") != "pass_with_non_arxiv_fallback":
    errors.append("terminology QA event result differs")

report = {
    "csv": {"bytes": len(CSV.read_bytes()), "sha256": sha256(CSV.read_bytes())},
    "entity_counts": counts,
    "errors": errors,
    "jsonl": {"bytes": len(JSONL.read_bytes()), "sha256": sha256(JSONL.read_bytes())},
    "record_count": len(records),
    "result": "pass" if not errors else "fail",
}
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
raise SystemExit(0 if not errors else 1)
