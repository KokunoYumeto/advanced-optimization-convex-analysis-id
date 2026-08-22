"""Structural, formula-surface, and correction audit for Habring Chapter 5 id-ID."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "habring" / "source-v1" / "proximal_gradient.tex"
TARGET = ROOT / "source" / "id-ID" / "habring-05-metode-gradien-proksimal-id.tex"
REPORT = ROOT / "qa" / "PROXIMAL_GRADIENT_STRUCTURE_REPORT.json"
LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"

EXPECTED_SOURCE_SHA256 = "59d5694742f0e2f9f46da0c1418b5fe0ff18521c49078ed29c843b6e8c701f6e"
EXPECTED_TARGET_SHA256 = "1292f09d375ff0e0ff12e7c87e673596400bb94f228db70d49f9a517b1678691"
EXPECTED_FORMULA_DELTA_MANIFEST_SHA256 = "3b910b86e304b2ba472df7fbf642db5928824ee999b551cc60f287b2c5705a3c"
EXPECTED_ENVIRONMENT_COUNT = 78
EXPECTED_SEGMENTS = [f"d90.hab.v1.ch05.seg{i:04d}" for i in range(1, 9)]
EXPECTED_SOURCE_LABELS = [
    "proximal:eq:problem",
    "proximal:eq:intro",
    "proximal:eq:prox_proof",
    "proximal:eq:composite",
    "proximal:eq:prox_grad",
    "proximal:eq:moreau_diff",
    "proximal:eq:moreau_diff2",
    "proximal:eq:moreau_diff2",
    "proximal_gradient:lemma:Lsmoothness",
]
EXPECTED_TARGET_LABELS = [
    "proximal:eq:problem",
    "proximal:eq:intro",
    "proximal:eq:prox_proof",
    "proximal:eq:composite",
    "proximal:eq:prox_grad",
    "proximal:eq:moreau_diff",
    "proximal:eq:moreau_diff2",
    "proximal:eq:moreau_diff2_bound",
    "proximal_gradient:lemma:Lsmoothness",
]
REQUIRED_LEDGER_IDS = {f"O015-HAB-ADV-{number:04d}" for number in range(28, 39)}
REQUIRED_CORRECTION_SURFACES = [
    r"f:\R^d\rightarrow(-\infty,\infty]",
    r"\tau_k>0",
    r"q_x(\bar y)",
    r"\min_{y\in\R^d}q_x(y)",
    r"Untuk suatu \(\tau>0\) yang tetap",
    r"\Longleftrightarrow",
    r"\coloneqq\inf_{y\in\R^d}",
    r"\bigl\|x-\prox_{\tau f}(x)\bigr\|^2",
    r"tak kosong, tertutup, dan konveks",
    r"x_i<-\tau",
    r"\R^{d_1}\times\cdots\times\R^{d_m}\cong\R^d",
    r"\gamma\geq0",
    r"\in\partial f(p(x))",
    r"\operatorname{sign}(x_i)\max\{|x_i|-\tau,0\}",
    r"0<\tau_{\min}\leq\tau_k\leq L^{-1}",
    r"\frac{\|x_0-x^*\|^2}{2\tau_{\min}n}",
]
FORBIDDEN_UNRESOLVED_SURFACES = [
    r"\cref{preliminaries:thm:direct_method}",
    r"\cref{convexity:thm:minimum}",
]
PROMPT_DISPOSITIONS = [
    {
        "source_surface": "Therefore, (why?)",
        "target_surface": "Oleh karena itu (mengapa?)",
        "disposition": "retained_as_informal_reasoning_prompt",
    },
    {
        "source_surface": "Exercise.",
        "target_surface": (
            "Latihan. Terapkan lemma keberadaan dan keunikan proks pada "
            r"\(\tau f\), lalu substitusikan peminim unik tersebut ke dalam definisi infimum."
        ),
        "disposition": "retained_and_scaffolded_as_self_study_exercise",
    },
    {
        "source_surface": "Projection, 1 norm, 2 norm",
        "target_surface": "Verifikasikan ketiga rumus ini langsung dari kondisi optimalitas proks.",
        "disposition": "completed_placeholder_and_retained_verification_prompt",
    },
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
    if len(source_begins) != EXPECTED_ENVIRONMENT_COUNT:
        failures.append(f"source environment count differs: {len(source_begins)}")
    if len(source_ends) != EXPECTED_ENVIRONMENT_COUNT:
        failures.append(f"source end-environment count differs: {len(source_ends)}")
    if source_begins != target_begins:
        failures.append("ordered begin-environment topology differs")
    if source_ends != target_ends:
        failures.append("ordered end-environment topology differs")

    source_labels = re.findall(r"\\label\{([^}]+)\}", source)
    target_labels = re.findall(r"\\label\{([^}]+)\}", target)
    if source_labels != EXPECTED_SOURCE_LABELS:
        failures.append(f"source label sequence differs: {source_labels}")
    if target_labels != EXPECTED_TARGET_LABELS:
        failures.append(f"target label sequence differs: {target_labels}")
    if len(target_labels) != len(set(target_labels)):
        failures.append("duplicate target label")
    remapped_labels = [
        {
            "source_ordinal": 8,
            "source": "proximal:eq:moreau_diff2",
            "target": "proximal:eq:moreau_diff2_bound",
            "reason": "unique remap of the source's second duplicate label",
        }
    ]

    segments = re.findall(r"^% segment-id: (\S+)$", target, re.MULTILINE)
    if segments != EXPECTED_SEGMENTS:
        failures.append(f"segment sequence differs: {segments}")

    source_citations = re.findall(r"\\cite\{([^}]+)\}", source)
    target_citations = re.findall(r"\\cite\{([^}]+)\}", target)
    if source_citations != ["beck2017first"] or target_citations != ["beck2017first"]:
        failures.append(
            f"citation sequence differs: source={source_citations}, target={target_citations}"
        )

    forbidden_surface_counts: dict[str, dict[str, int]] = {}
    for name, pattern in {
        "figures": r"\\includegraphics(?:\[[^]]*\])?\{",
        "footnotes": r"\\footnote\{",
        "inputs": r"\\(?:input|include)\{",
    }.items():
        source_count = len(re.findall(pattern, source))
        target_count = len(re.findall(pattern, target))
        forbidden_surface_counts[name] = {"source": source_count, "target": target_count}
        if source_count or target_count:
            failures.append(
                f"unexpected {name} surface: source={source_count}, target={target_count}"
            )

    source_unnumbered = len(re.findall(r"\\\[", source))
    target_unnumbered = len(re.findall(r"\\\[", target))
    if source_unnumbered != 1 or target_unnumbered != 1:
        failures.append(
            "unnumbered-display count differs from one per source and target: "
            f"source={source_unnumbered}, target={target_unnumbered}"
        )

    for surface in REQUIRED_CORRECTION_SURFACES:
        if surface not in target:
            failures.append(f"required corrected surface missing: {surface}")
    for surface in FORBIDDEN_UNRESOLVED_SURFACES:
        if surface in target:
            failures.append(f"unresolved standalone dependency remains: {surface}")

    prompt_audit: list[dict[str, object]] = []
    for prompt in PROMPT_DISPOSITIONS:
        source_occurrences = source.count(prompt["source_surface"])
        target_occurrences = target.count(prompt["target_surface"])
        prompt_audit.append(
            {
                **prompt,
                "source_occurrences": source_occurrences,
                "target_occurrences": target_occurrences,
            }
        )
        if source_occurrences != 1 or target_occurrences != 1:
            failures.append(
                "prompt disposition surface mismatch: "
                f"{prompt['disposition']} source={source_occurrences}, target={target_occurrences}"
            )

    ledger_ids = {
        json.loads(line)["event_id"]
        for line in LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    missing_ledger = sorted(REQUIRED_LEDGER_IDS - ledger_ids)
    if missing_ledger:
        failures.append(f"missing Chapter 5 correction records: {missing_ledger}")

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
        "schema": "o015-proximal-gradient-structure-audit-v1",
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
        "environment_topology_equal": (
            source_begins == target_begins and source_ends == target_ends
        ),
        "source_labels": source_labels,
        "target_labels": target_labels,
        "label_remaps": remapped_labels,
        "segments": segments,
        "citations": {"source": source_citations, "target": target_citations},
        "forbidden_surface_counts": forbidden_surface_counts,
        "unnumbered_display_count": {
            "source": source_unnumbered,
            "target": target_unnumbered,
        },
        "informal_prompt_count": {
            "source": len(PROMPT_DISPOSITIONS),
            "target_dispositions": len(prompt_audit),
        },
        "informal_prompt_dispositions": prompt_audit,
        "formula_surface_count": {"source": len(source_math), "target": len(target_math)},
        "formula_delta_count": len(deltas),
        "formula_delta_manifest_sha256": manifest_sha,
        "formula_deltas": deltas,
        "correction_ledger_ids": sorted(REQUIRED_LEDGER_IDS),
        "required_correction_surface_count": len(REQUIRED_CORRECTION_SURFACES),
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
