"""Structural, formula-surface, and correction audit for Habring Chapter 4 id-ID."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "habring" / "source-v1" / "projected_subgradient_method.tex"
TARGET = ROOT / "source" / "id-ID" / "habring-04-metode-subgradien-terproyeksi-id.tex"
REPORT = ROOT / "qa" / "PROJECTED_SUBGRADIENT_STRUCTURE_REPORT.json"
LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"

EXPECTED_SOURCE_SHA256 = "44ac28a0f0b67fed4855f7ed91089fab52f77804115f2a06201bff98437bd8da"
EXPECTED_TARGET_SHA256 = "29fdc330007009bd765a17ca1dcd0cf130ff802312ebb402bf03413da5f96a7d"
EXPECTED_FORMULA_DELTA_MANIFEST_SHA256 = "d0453330d42781afffe1e1b7ad3d5a663533509f43a754f9958785b9646171b4"
EXPECTED_SEGMENTS = [f"d90.hab.v1.ch04.seg{i:04d}" for i in range(1, 9)]
EXPECTED_LABELS = [
    "subgradient:eq:projectedSG",
    "lemma:subgradient:fundamental",
    "eq:subgradient:fundamental",
    "subgradient:eq:strongly",
]
REQUIRED_LEDGER_IDS = {f"O015-HAB-ADV-{number:04d}" for number in range(19, 28)}
REQUIRED_CORRECTION_SURFACES = [
    r"f:V\rightarrow\R",
    r"\proj_C:V&\rightarrow C",
    r"x^*\in\arg\min_{x\in C}f(x)",
    r"\tau_k\geq0",
    r"N (f_{\mathrm{best}}^N)^2",
    r"\tau_k>0",
    r"\frac{2L^2}{\mu(n-1)}",
    r"\|x_n-x^*\|\leq2L/[\mu\sqrt{n-1}]",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_formula(value: str) -> str:
    value = re.sub(r"\\text\{[^{}]*\}", r"\\text{#}", value)
    return re.sub(r"\s+", "", value)


def formulas(text: str) -> list[str]:
    pattern = re.compile(
        r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$"
        r"|\\\[(.*?)\\\]"
        r"|\\\((.*?)\\\)"
        r"|\\begin\{(equation|gather)\*?\}(.*?)\\end\{\4\*?\}",
        re.DOTALL,
    )
    result: list[str] = []
    for match in pattern.finditer(text):
        value = match.group(1) or match.group(2) or match.group(3) or match.group(5)
        result.append(normalized_formula(value))
    return result


def run(report_only: bool) -> dict[str, object]:
    source_bytes = SOURCE.read_bytes()
    target_bytes = TARGET.read_bytes()
    source = source_bytes.decode("utf-8")
    target = target_bytes.decode("utf-8")
    failures: list[str] = []

    source_sha = sha256(source_bytes)
    target_sha = sha256(target_bytes)
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

    labels = re.findall(r"\\label\{([^}]+)\}", target)
    if labels != EXPECTED_LABELS:
        failures.append(f"label sequence differs: {labels}")
    if len(labels) != len(set(labels)):
        failures.append("duplicate target label")

    segments = re.findall(r"^% segment-id: (\S+)$", target, re.MULTILINE)
    if segments != EXPECTED_SEGMENTS:
        failures.append(f"segment sequence differs: {segments}")
    if target.count(r"\footnote{") != 3 or source.count(r"\footnote{") != 3:
        failures.append("footnote count differs from the three-source-footnote surface")
    citations = re.findall(r"\\cite\{([^}]+)\}", target)
    if citations != ["beck2017first"]:
        failures.append(f"citation sequence differs: {citations}")
    if re.search(r"\\includegraphics", target):
        failures.append("unexpected figure surface in figure-free source chapter")

    for surface in REQUIRED_CORRECTION_SURFACES:
        if surface not in target:
            failures.append(f"required corrected surface missing: {surface}")

    ledger_ids = {
        json.loads(line)["event_id"]
        for line in LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    missing_ledger = sorted(REQUIRED_LEDGER_IDS - ledger_ids)
    if missing_ledger:
        failures.append(f"missing Chapter 4 correction records: {missing_ledger}")

    source_math = formulas(source)
    target_math = formulas(target)
    matcher = difflib.SequenceMatcher(a=source_math, b=target_math, autojunk=False)
    deltas: list[dict[str, object]] = []
    for operation, source_start, source_end, target_start, target_end in matcher.get_opcodes():
        if operation == "equal":
            continue
        deltas.append(
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
    manifest = json.dumps(
        deltas, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    manifest_sha = sha256(manifest)
    if manifest_sha != EXPECTED_FORMULA_DELTA_MANIFEST_SHA256:
        failures.append(f"formula-delta manifest changed: {manifest_sha}")

    report: dict[str, object] = {
        "schema": "o015-projected-subgradient-structure-audit-v1",
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
        "labels": labels,
        "segments": segments,
        "footnotes": target.count(r"\footnote{"),
        "citations": citations,
        "figures": [],
        "informal_exercise_prompts": 2,
        "formula_surface_count": {"source": len(source_math), "target": len(target_math)},
        "formula_delta_count": len(deltas),
        "formula_delta_manifest_sha256": manifest_sha,
        "formula_deltas": deltas,
        "correction_ledger_ids": sorted(REQUIRED_LEDGER_IDS),
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
    run(args.report_only)
