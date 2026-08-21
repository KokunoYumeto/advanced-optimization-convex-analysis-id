"""Structural and formula-surface audit for Habring Chapter 3 id-ID."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "habring" / "source-v1" / "subgradient.tex"
TARGET = ROOT / "source" / "id-ID" / "habring-03-subgradien-id.tex"
REPORT = ROOT / "qa" / "SUBGRADIENT_STRUCTURE_REPORT.json"
LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"

EXPECTED_SOURCE_SHA256 = "c3b447ee9ea5d8dbf98333b927ad5b7408d1d66884c3b7d5590251dfc47c5405"
EXPECTED_TARGET_SHA256 = "d04ff82898c157f56924c6c08fd204bcd97625f060847fd8a0b6f7a2b90b0a5c"
EXPECTED_EXTRA_LABELS = {"d90-hab:ch:subgradien"}
EXPECTED_SEGMENTS = [f"d90.hab.v1.ch03.seg{i:04d}" for i in range(1, 12)]

# Exact canonical digest of every non-equal formula block after sequence
# alignment. This admits insertions/deletions required by determined source
# corrections without shifting every later formula index. Locale-only text
# inside \text{...} is normalized before alignment.
EXPECTED_MATH_DELTA_MANIFEST_SHA256 = "c979be4ecb19687c87ef590feda4d5ba8f083a945a0e0cda98236d8d7581b681"

# One independently reviewed disposition for each non-equal SequenceMatcher
# block, in report order. Named mathematical changes resolve to durable adverse
# ledger IDs; the remaining labels are expressly non-semantic typography,
# punctuation, or notation normalizations.
EXPECTED_MATH_DELTA_DISPOSITIONS: tuple[tuple[str, ...], ...] = (
    ("O015-HAB-ADV-0018",),
    ("O015-HAB-ADV-0001",),
    ("editorial_punctuation_only",),
    ("editorial_punctuation_only",),
    ("O015-HAB-ADV-0002",),
    ("O015-HAB-ADV-0002",),
    ("O015-HAB-ADV-0002",),
    ("O015-HAB-ADV-0002",),
    ("O015-HAB-ADV-0014",),
    ("O015-HAB-ADV-0003",),
    ("notation_normalization_only",),
    ("O015-HAB-ADV-0018",),
    ("notation_normalization_only",),
    ("notation_normalization_only",),
    ("O015-HAB-ADV-0004",),
    ("O015-HAB-ADV-0004",),
    ("O015-HAB-ADV-0005",),
    ("editorial_punctuation_only",),
    ("O015-HAB-ADV-0006",),
    ("proof_exposition_only",),
    ("O015-HAB-ADV-0008",),
    ("O015-HAB-ADV-0017",),
    ("editorial_punctuation_only",),
    ("math_mode_typography_only",),
    ("math_mode_typography_only",),
    ("O015-HAB-ADV-0015",),
    ("math_mode_typography_only",),
    ("notation_normalization_only",),
    ("math_mode_typography_only",),
    ("O015-HAB-ADV-0007",),
    ("O015-HAB-ADV-0007",),
    ("O015-HAB-ADV-0007",),
    ("O015-HAB-ADV-0015", "O015-HAB-ADV-0008"),
    ("notation_normalization_only",),
    ("O015-HAB-ADV-0016",),
    ("O015-HAB-ADV-0016",),
    ("O015-HAB-ADV-0016",),
    ("O015-HAB-ADV-0016",),
    ("O015-HAB-ADV-0008",),
    ("notation_normalization_only",),
    ("notation_normalization_only",),
    ("O015-HAB-ADV-0010",),
    ("O015-HAB-ADV-0010",),
    ("editorial_punctuation_only",),
    ("O015-HAB-ADV-0011",),
    ("O015-HAB-ADV-0012",),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_formula(value: str) -> str:
    value = re.sub(r"\\text\{[^{}]*\}", r"\\text{#}", value)
    value = re.sub(r"\s+", "", value)
    return value


def formula_surfaces(text: str) -> list[str]:
    pattern = re.compile(
        r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$"
        r"|\\\[(.*?)\\\]"
        r"|\\\((.*?)\\\)"
        r"|\\begin\{(equation|gather)\*?\}(.*?)\\end\{\4\*?\}",
        re.DOTALL,
    )
    surfaces: list[str] = []
    for match in pattern.finditer(text):
        value = match.group(1) or match.group(2) or match.group(3) or match.group(5)
        surfaces.append(normalized_formula(value))
    return surfaces


def run(report_only: bool) -> dict[str, object]:
    source_bytes = SOURCE.read_bytes()
    target_bytes = TARGET.read_bytes()
    source_sha = sha256_bytes(source_bytes)
    target_sha = sha256_bytes(target_bytes)
    source = source_bytes.decode("utf-8")
    target = target_bytes.decode("utf-8")

    failures: list[str] = []
    if source_sha != EXPECTED_SOURCE_SHA256:
        failures.append(f"authority SHA changed: {source_sha}")
    if target_sha != EXPECTED_TARGET_SHA256:
        failures.append(f"target SHA changed: {target_sha}")

    source_begins = re.findall(r"\\begin\{([^}]+)\}", source)
    target_begins = re.findall(r"\\begin\{([^}]+)\}", target)
    source_ends = re.findall(r"\\end\{([^}]+)\}", source)
    target_ends = re.findall(r"\\end\{([^}]+)\}", target)
    if source_begins != target_begins:
        failures.append("ordered begin-environment topology differs")
    if source_ends != target_ends:
        failures.append("ordered end-environment topology differs")

    source_labels = re.findall(r"\\label\{([^}]+)\}", source)
    target_labels = re.findall(r"\\label\{([^}]+)\}", target)
    if set(target_labels) - set(source_labels) != EXPECTED_EXTRA_LABELS:
        failures.append("unexpected target-only labels")
    if set(source_labels) - set(target_labels):
        failures.append("source label missing in target")
    if len(target_labels) != len(set(target_labels)):
        failures.append("duplicate target label")

    source_graphics = re.findall(
        r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", source
    )
    target_graphics = re.findall(
        r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", target
    )
    if source_graphics != target_graphics:
        failures.append("figure reference order differs")
    missing_graphics = [
        name
        for name in target_graphics
        if not (TARGET.parent / f"{name}.png").is_file()
    ]
    if missing_graphics:
        failures.append(f"missing figure assets: {missing_graphics}")

    segments = re.findall(r"^% segment-id: (\S+)$", target, re.MULTILINE)
    if segments != EXPECTED_SEGMENTS:
        failures.append("stable segment ID sequence differs")

    source_math = formula_surfaces(source)
    target_math = formula_surfaces(target)
    matcher = difflib.SequenceMatcher(a=source_math, b=target_math, autojunk=False)
    math_deltas: list[dict[str, object]] = []
    for operation, source_start, source_end, target_start, target_end in matcher.get_opcodes():
        if operation == "equal":
            continue
        math_deltas.append(
            {
                "operation": operation,
                "source_start": source_start + 1,
                "source_end": source_end,
                "target_start": target_start + 1,
                "target_end": target_end,
                "source": source_math[source_start:source_end],
                "target": target_math[target_start:target_end],
            }
        )
    if len(math_deltas) != len(EXPECTED_MATH_DELTA_DISPOSITIONS):
        failures.append(
            "formula-delta disposition count differs: "
            f"{len(math_deltas)} != {len(EXPECTED_MATH_DELTA_DISPOSITIONS)}"
        )
    ledger_ids = {
        json.loads(line)["event_id"]
        for line in LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    for index, block in enumerate(math_deltas):
        dispositions = (
            EXPECTED_MATH_DELTA_DISPOSITIONS[index]
            if index < len(EXPECTED_MATH_DELTA_DISPOSITIONS)
            else ("missing_disposition",)
        )
        block["dispositions"] = list(dispositions)
        for disposition in dispositions:
            for correction_id in re.findall(r"O015-HAB-ADV-\d{4}", disposition):
                if correction_id not in ledger_ids:
                    failures.append(
                        f"formula-delta disposition references missing {correction_id}"
                    )
    math_delta_manifest = json.dumps(
        math_deltas,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    math_delta_manifest_sha = sha256_bytes(math_delta_manifest)
    if math_delta_manifest_sha != EXPECTED_MATH_DELTA_MANIFEST_SHA256:
        failures.append(
            "formula-delta manifest changed: " + math_delta_manifest_sha
        )

    report: dict[str, object] = {
        "schema": "o015-subgradient-structure-audit-v1",
        "source": {
            "path": SOURCE.relative_to(ROOT).as_posix(),
            "bytes": len(source_bytes),
            "sha256": source_sha,
        },
        "target": {
            "path": TARGET.relative_to(ROOT).as_posix(),
            "bytes": len(target_bytes),
            "sha256": target_sha,
        },
        "environment_count": len(source_begins),
        "environment_counts": dict(sorted(Counter(source_begins).items())),
        "environment_topology_equal": source_begins == target_begins,
        "labels": {
            "source": source_labels,
            "target": target_labels,
        },
        "figures": target_graphics,
        "segments": segments,
        "formula_surface_count": {
            "source": len(source_math),
            "target": len(target_math),
        },
        "formula_delta_manifest_sha256": math_delta_manifest_sha,
        "formula_deltas": math_deltas,
        "failures": failures,
        "result": "pass" if not failures else "fail",
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if failures and not report_only:
        raise SystemExit(1)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    run(report_only=args.report_only)
