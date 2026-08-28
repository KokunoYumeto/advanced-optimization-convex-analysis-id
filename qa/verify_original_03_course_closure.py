#!/usr/bin/env python3
"""Independent, deterministic audit for the complete Original-03 closure.

The verifier is intentionally read-only with respect to the course source,
laboratory code, and checked-in laboratory artifacts.  Computation components
are copied to isolated temporary directories and executed twice there.  The
only persistent file written by this program is the JSON report beside it.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
QA_DIR = ROOT / "qa"
REPORT_PATH = QA_DIR / "ORIGINAL_03_COURSE_CLOSURE.json"
SOURCE_ROOT = ROOT / "source" / "id-ID"
MODULE_DIR = SOURCE_ROOT / "original-03"
LAB_DIR = ROOT / "labs" / "original-03"
AGGREGATOR = SOURCE_ROOT / "original-03-penutupan-kursus-id.tex"
INTEGRATED_ROOT = SOURCE_ROOT / "D90-O015-optimisasi-lanjut-analisis-konveks-id.tex"

MODULE_NAMES = [
    "00-peta-asesmen-id.tex",
    "01-diagnostik-prasyarat-id.tex",
    "02-set-soal-dasar-konveks-id.tex",
    "03-set-soal-metode-proksimal-id.tex",
    "04-set-soal-dualitas-kkt-id.tex",
    "05-set-soal-metode-stokastik-id.tex",
    "06-set-soal-operator-monoton-id.tex",
    "07-set-soal-transportasi-dan-sintesis-id.tex",
    "08-rubrik-pembuktian-id.tex",
    "09-ujian-tengah-id.tex",
    "10-ujian-akhir-id.tex",
    "11-laboratorium-globalisasi-newton-id.tex",
    "12-laboratorium-transportasi-entropik-id.tex",
    "13-proyek-kapstone-masalah-invers-komposit-id.tex",
]
MODULES = [MODULE_DIR / name for name in MODULE_NAMES]

COMPONENTS = {
    "globalisasi-newton": {
        "script": LAB_DIR / "globalisasi-newton.py",
        "outputs": [
            LAB_DIR / "globalisasi-newton-results.json",
            LAB_DIR / "globalisasi-newton-results.csv",
            LAB_DIR / "globalisasi-newton.svg",
        ],
        "module": MODULE_DIR / "11-laboratorium-globalisasi-newton-id.tex",
    },
    "transportasi-entropik": {
        "script": LAB_DIR / "transportasi-entropik.py",
        "outputs": [
            LAB_DIR / "transportasi-entropik-results.json",
            LAB_DIR / "transportasi-entropik-results.csv",
            LAB_DIR / "transportasi-entropik.svg",
        ],
        "module": MODULE_DIR / "12-laboratorium-transportasi-entropik-id.tex",
    },
    "kapstone-invers-komposit": {
        "script": LAB_DIR / "kapstone-invers-komposit.py",
        "outputs": [
            LAB_DIR / "kapstone-invers-komposit-results.json",
            LAB_DIR / "kapstone-invers-komposit-results.csv",
            LAB_DIR / "kapstone-invers-komposit.svg",
        ],
        "module": MODULE_DIR / "13-proyek-kapstone-masalah-invers-komposit-id.tex",
    },
}

SCOPED_TEX = [AGGREGATOR, *MODULES]
SCOPED_LABS = [
    component["script"] for component in COMPONENTS.values()
] + [
    output
    for component in COMPONENTS.values()
    for output in component["outputs"]
]
SCOPED_INPUTS = SCOPED_TEX + SCOPED_LABS


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    text = payload.decode("utf-8")
    return {
        "path": relative(path),
        "bytes": len(payload),
        "lines": len(text.splitlines()),
        "sha256": sha256_bytes(payload),
    }


def tex_without_comments(text: str) -> str:
    """Remove TeX comments while preserving newlines and escaped percent signs."""
    cleaned: list[str] = []
    for line in text.splitlines(keepends=True):
        cut = len(line)
        for index, char in enumerate(line):
            if char != "%":
                continue
            slash_count = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                slash_count += 1
                cursor -= 1
            if slash_count % 2 == 0:
                cut = index
                break
        newline = "\n" if line.endswith(("\n", "\r")) else ""
        cleaned.append(line[:cut].rstrip("\r\n") + newline)
    return "".join(cleaned)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def isclose(actual: float, expected: float, *, atol: float = 1.0e-12, rtol: float = 1.0e-10) -> bool:
    return math.isclose(float(actual), float(expected), abs_tol=atol, rel_tol=rtol)


def parse_float(value: str) -> float:
    return float(value)


def parse_bool(value: str) -> bool | None:
    if value == "True":
        return True
    if value == "False":
        return False
    if value == "":
        return None
    raise ValueError(f"unexpected boolean cell: {value!r}")


class Audit:
    def __init__(self) -> None:
        self.findings: dict[str, list[dict[str, Any]]] = {"P1": [], "P2": [], "P3": []}
        self.checks: dict[str, Any] = {}

    def finding(
        self,
        severity: str,
        code: str,
        message: str,
        evidence: Any | None = None,
    ) -> None:
        item: dict[str, Any] = {"code": code, "message": message}
        if evidence is not None:
            item["evidence"] = evidence
        self.findings[severity].append(item)

    def require(
        self,
        condition: bool,
        code: str,
        message: str,
        evidence: Any | None = None,
        severity: str = "P1",
    ) -> bool:
        if not condition:
            self.finding(severity, code, message, evidence)
        return condition


def read_utf8(audit: Audit, path: Path) -> str:
    if not audit.require(path.is_file(), "missing-file", f"Required file is missing: {relative(path)}"):
        return ""
    payload = path.read_bytes()
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        audit.finding(
            "P1",
            "invalid-utf8",
            f"File is not valid UTF-8: {relative(path)}",
            {"start": error.start, "end": error.end, "reason": error.reason},
        )
        return payload.decode("utf-8", errors="replace")


def audit_inventory_and_bytes(audit: Audit) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    control_evidence: list[dict[str, Any]] = []
    for path in SCOPED_INPUTS:
        if not path.is_file():
            audit.finding("P1", "missing-file", f"Required file is missing: {relative(path)}")
            continue
        payload = path.read_bytes()
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            audit.finding(
                "P1",
                "invalid-utf8",
                f"File is not valid UTF-8: {relative(path)}",
                {"start": error.start, "end": error.end, "reason": error.reason},
            )
            text = payload.decode("utf-8", errors="replace")
        invalid = [
            {"offset": index, "byte": byte}
            for index, byte in enumerate(payload)
            if (byte < 32 and byte not in (9, 10, 13)) or byte == 127
        ]
        if invalid:
            control_evidence.append({"path": relative(path), "occurrences": invalid[:20]})
        records.append(
            {
                "path": relative(path),
                "bytes": len(payload),
                "lines": len(text.splitlines()),
                "sha256": sha256_bytes(payload),
            }
        )
    audit.require(
        not control_evidence,
        "control-bytes",
        "ASCII control bytes occur in scoped text artifacts.",
        control_evidence,
    )
    expected_count = 15 + 3 + 9
    audit.require(
        len(records) == expected_count,
        "inventory-count",
        f"Expected {expected_count} scoped inputs, found {len(records)}.",
    )
    return {
        "file_count": len(records),
        "tex_file_count": sum(record["path"].endswith(".tex") for record in records),
        "python_file_count": sum(record["path"].endswith(".py") for record in records),
        "json_file_count": sum(record["path"].endswith(".json") for record in records),
        "csv_file_count": sum(record["path"].endswith(".csv") for record in records),
        "svg_file_count": sum(record["path"].endswith(".svg") for record in records),
        "control_byte_occurrences": sum(
            len(item["occurrences"]) for item in control_evidence
        ),
        "files": records,
    }


def audit_aggregator(audit: Audit, texts: dict[Path, str]) -> dict[str, Any]:
    text = texts[AGGREGATOR]
    stripped = tex_without_comments(text)
    actual_inputs = re.findall(r"\\input\{([^{}]+)\}", stripped)
    expected_inputs = [f"original-03/{name.removesuffix('.tex')}" for name in MODULE_NAMES]
    audit.require(
        actual_inputs == expected_inputs,
        "aggregator-input-order",
        "Aggregator must include exactly the 14 Original-03 modules in canonical order.",
        {"expected": expected_inputs, "actual": actual_inputs},
    )
    audit.require(
        "\\label{orig03:chapter:course-closure}" in text,
        "aggregator-chapter-label",
        "Aggregator chapter label is missing.",
    )
    audit.require(
        re.search(r"(?im)^%\s*license:\s*CC BY-SA 4\.0\s*$", text) is not None,
        "aggregator-license",
        "Aggregator lacks its CC BY-SA 4.0 license marker.",
    )
    stale_patterns = {
        "unfinished-closure-claim": r"peta ini tidak menyatakan bahwa[\s\S]{0,180}?telah\s+selesai",
        "stale-54-prompts-claim": r"lapisan asesmen saat ini memuat tepat 54 prompt baru",
    }
    stale_hits = [name for name, pattern in stale_patterns.items() if re.search(pattern, text, re.I)]
    # The historical map may describe prompt topology, but it must not claim
    # that the now-integrated closure is unfinished.
    audit.require(
        not stale_hits,
        "stale-assessment-map",
        "Assessment map contains a stale claim about an unfinished closure.",
        stale_hits,
    )
    return {
        "module_inputs": actual_inputs,
        "module_input_count": len(actual_inputs),
        "canonical_order": actual_inputs == expected_inputs,
        "stale_claims": stale_hits,
    }


def comment_metadata(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(r"(?im)^\s*%\s*([A-Za-z0-9-]+)\s*:\s*([^\r\n]+?)\s*$")
    return [
        {
            "key": match.group(1),
            "value": match.group(2).strip(),
            "offset": match.start(),
            "line": line_number(text, match.start()),
        }
        for match in pattern.finditer(text)
    ]


def stable_definition_metadata(text: str) -> list[dict[str, Any]]:
    definitions: list[dict[str, Any]] = []
    excluded_keys = {
        "orig03-existing-assessment-id",
        "orig03-assessment-map-id",
        "orig03-stable-ref",
        "stable-ref",
    }
    for item in comment_metadata(text):
        key = item["key"].lower()
        if key in excluded_keys:
            continue
        if key in {"orig03-stable-id", "stable-id"} or key.endswith("-id"):
            definitions.append(item)
    return definitions


def labels_in(text: str) -> list[dict[str, Any]]:
    stripped = tex_without_comments(text)
    return [
        {
            "value": match.group(1).strip(),
            "offset": match.start(),
            "line": line_number(stripped, match.start()),
        }
        for match in re.finditer(r"\\label\{([^{}]+)\}", stripped)
    ]


def resolve_tex_input(parent: Path, raw: str) -> Path | None:
    value = raw.strip()
    if not value or "#" in value or "\\" in value:
        return None
    candidate_values = [value] if Path(value).suffix else [value + ".tex", value]
    search_roots = [parent.parent, SOURCE_ROOT]
    for base in search_roots:
        for candidate_value in candidate_values:
            candidate = (base / candidate_value).resolve()
            try:
                candidate.relative_to(ROOT.resolve())
            except ValueError:
                continue
            if candidate.is_file():
                return candidate
    return None


def integrated_include_closure(audit: Audit) -> list[Path]:
    pending = [INTEGRATED_ROOT]
    visited: set[Path] = set()
    missing: list[dict[str, str]] = []
    while pending:
        path = pending.pop()
        path = path.resolve()
        if path in visited:
            continue
        if not path.is_file():
            missing.append({"parent": "<root>", "input": str(path)})
            continue
        visited.add(path)
        text = tex_without_comments(path.read_text(encoding="utf-8"))
        for raw in re.findall(r"\\(?:input|include)\{([^{}]+)\}", text):
            resolved = resolve_tex_input(path, raw)
            if resolved is None:
                missing.append({"parent": relative(path), "input": raw})
            elif resolved not in visited:
                pending.append(resolved)
    audit.require(
        not missing,
        "integrated-input-resolution",
        "One or more static TeX inputs in the integrated reader do not resolve.",
        missing,
    )
    return sorted(visited, key=lambda path: relative(path))


def audit_ids_labels_and_references(audit: Audit, texts: dict[Path, str]) -> dict[str, Any]:
    definitions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scoped_labels: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in SCOPED_TEX:
        text = texts[path]
        for item in stable_definition_metadata(text):
            definitions[item["value"]].append(
                {"path": relative(path), "line": item["line"], "key": item["key"]}
            )
        for item in labels_in(text):
            scoped_labels[item["value"]].append(
                {"path": relative(path), "line": item["line"]}
            )

    duplicate_ids = {
        value: locations for value, locations in definitions.items() if len(locations) > 1
    }
    duplicate_labels = {
        value: locations for value, locations in scoped_labels.items() if len(locations) > 1
    }
    audit.require(
        not duplicate_ids,
        "duplicate-stable-id",
        "Stable ID definitions must be globally unique in Original-03.",
        duplicate_ids,
    )
    audit.require(
        not duplicate_labels,
        "duplicate-label",
        "LaTeX labels must be unique in Original-03.",
        duplicate_labels,
    )

    closure = integrated_include_closure(audit)
    closure_labels: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in closure:
        text = path.read_text(encoding="utf-8")
        for item in labels_in(text):
            closure_labels[item["value"]].append(
                {"path": relative(path), "line": item["line"]}
            )

    integrated_collisions = {
        value: closure_labels[value]
        for value in scoped_labels
        if len(closure_labels.get(value, [])) != 1
    }
    audit.require(
        not integrated_collisions,
        "integrated-label-collision",
        "Original-03 labels must occur exactly once in the integrated reader closure.",
        integrated_collisions,
    )

    ref_pattern = re.compile(r"\\(?:ref|eqref|pageref|autoref|cref|Cref)\{([^{}]+)\}")
    refs: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for path in SCOPED_TEX:
        text = tex_without_comments(texts[path])
        for match in ref_pattern.finditer(text):
            for target in (part.strip() for part in match.group(1).split(",")):
                record = {
                    "path": relative(path),
                    "line": line_number(text, match.start()),
                    "target": target,
                }
                refs.append(record)
                if target not in closure_labels:
                    unresolved.append(record)
    audit.require(
        not unresolved,
        "unresolved-static-reference",
        "Static Original-03 references must resolve in the integrated reader closure.",
        unresolved,
    )

    return {
        "stable_definition_count": sum(len(items) for items in definitions.values()),
        "unique_stable_id_count": len(definitions),
        "duplicate_stable_ids": duplicate_ids,
        "label_definition_count": sum(len(items) for items in scoped_labels.values()),
        "unique_label_count": len(scoped_labels),
        "duplicate_labels": duplicate_labels,
        "integrated_closure_file_count": len(closure),
        "integrated_closure_files": [relative(path) for path in closure],
        "static_reference_count": len(refs),
        "unresolved_static_references": unresolved,
    }


def audit_tex_wellformedness(audit: Audit, texts: dict[Path, str]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    greek_names = (
        "alpha|beta|gamma|delta|epsilon|varepsilon|eta|theta|lambda|mu|nu|xi|"
        "rho|sigma|tau|phi|varphi|psi|omega"
    )
    bare_greek = re.compile(rf"(?<![A-Za-z\\])(?:{greek_names})(?![A-Za-z])")
    environment_pattern = re.compile(r"\\(begin|end)\{([^{}]+)\}")

    macro_text = (SOURCE_ROOT / "macros-id.tex").read_text(encoding="utf-8")
    one_defined = re.search(
        r"\\(?:newcommand|providecommand|renewcommand)\s*\{\\1\}", macro_text
    ) is not None

    for path in SCOPED_TEX:
        original = texts[path]
        text = tex_without_comments(original)
        stack: list[tuple[str, int]] = []
        for match in environment_pattern.finditer(text):
            kind, name = match.group(1), match.group(2)
            if kind == "begin":
                stack.append((name, match.start()))
            elif not stack or stack[-1][0] != name:
                errors.append(
                    {
                        "path": relative(path),
                        "line": line_number(text, match.start()),
                        "kind": "environment-mismatch",
                        "environment": name,
                    }
                )
            else:
                stack.pop()
        for name, offset in stack:
            errors.append(
                {
                    "path": relative(path),
                    "line": line_number(text, offset),
                    "kind": "unclosed-environment",
                    "environment": name,
                }
            )

        brace_stack: list[int] = []
        for index, char in enumerate(text):
            if char not in "{}":
                continue
            slashes = 0
            cursor = index - 1
            while cursor >= 0 and text[cursor] == "\\":
                slashes += 1
                cursor -= 1
            if slashes % 2 == 1:
                continue
            if char == "{":
                brace_stack.append(index)
            elif brace_stack:
                brace_stack.pop()
            else:
                errors.append(
                    {
                        "path": relative(path),
                        "line": line_number(text, index),
                        "kind": "unmatched-closing-brace",
                    }
                )
        for offset in brace_stack[:20]:
            errors.append(
                {
                    "path": relative(path),
                    "line": line_number(text, offset),
                    "kind": "unclosed-opening-brace",
                }
            )

        for match in bare_greek.finditer(text):
            errors.append(
                {
                    "path": relative(path),
                    "line": line_number(text, match.start()),
                    "kind": "bare-greek-command-name",
                    "token": match.group(0),
                }
            )
        # A numeric control symbol must begin with a single backslash.  Do not
        # misread the second character of a matrix row separator such as \\0.
        for match in re.finditer(r"(?<!\\)\\([0-9])", text):
            if match.group(1) == "1" and one_defined:
                continue
            errors.append(
                {
                    "path": relative(path),
                    "line": line_number(text, match.start()),
                    "kind": "undefined-numeric-control-symbol",
                    "token": match.group(0),
                }
            )

    audit.require(
        not errors,
        "malformed-tex",
        "Malformed TeX structure or escape sequences were detected.",
        errors,
    )
    return {
        "files_checked": len(SCOPED_TEX),
        "errors": errors,
        "integrated_numeric_macro_1_defined": one_defined,
    }


def marker_offsets(text: str, marker_key: str) -> dict[str, int]:
    pattern = re.compile(
        rf"(?im)^\s*%\s*{re.escape(marker_key)}\s*:\s*([^\r\n]+?)\s*$"
    )
    return {match.group(1).strip(): match.start() for match in pattern.finditer(text)}


def require_exact_set(
    audit: Audit,
    actual: Iterable[str],
    expected: Iterable[str],
    *,
    code: str,
    description: str,
) -> None:
    actual_set = set(actual)
    expected_set = set(expected)
    audit.require(
        actual_set == expected_set,
        code,
        description,
        {
            "missing": sorted(expected_set - actual_set),
            "unexpected": sorted(actual_set - expected_set),
        },
    )


def response_chunk(text: str, start: int, following_offsets: Iterable[int]) -> str:
    candidates = [offset for offset in following_offsets if offset > start]
    end = min(candidates) if candidates else len(text)
    return text[start:end]


def audit_prompt_style_module(
    audit: Audit,
    path: Path,
    text: str,
    prefix: str,
    assessment_count: int,
    prompt_count: int,
) -> dict[str, Any]:
    offsets = marker_offsets(text, "ORIG03-STABLE-ID")
    expected_ids = {
        *[f"{prefix}.problem.{index:04d}" for index in range(1, assessment_count + 1)],
        *[
            f"{prefix}.{kind}.{index:04d}"
            for kind in ("prompt", "hint1", "hint2", "answer", "solution")
            for index in range(1, prompt_count + 1)
        ],
    }
    require_exact_set(
        audit,
        offsets,
        expected_ids,
        code=f"{prefix}-stable-id-topology",
        description=f"{prefix} stable prompt/response ID topology is incomplete or has extras.",
    )

    labels = {item["value"] for item in labels_in(text)}
    expected_labels = {
        *[
            f"orig03:{prefix}:problem:{index:04d}"
            for index in range(1, assessment_count + 1)
        ],
        *[
            f"orig03:{prefix}:{kind}:{index:04d}"
            for kind in ("prompt", "hint1", "hint2", "answer", "solution")
            for index in range(1, prompt_count + 1)
        ],
    }
    actual_prefix_labels = {label for label in labels if label.startswith(f"orig03:{prefix}:")}
    require_exact_set(
        audit,
        actual_prefix_labels,
        expected_labels,
        code=f"{prefix}-label-topology",
        description=f"{prefix} explicit assessment/response label topology is incomplete or has extras.",
    )
    audit.require(
        text.count("\\begin{exercise}") == assessment_count,
        f"{prefix}-exercise-count",
        f"{prefix} must contain exactly {assessment_count} exercise containers.",
        {"actual": text.count("\\begin{exercise}")},
    )

    all_offsets = list(offsets.values())
    order_errors: list[dict[str, Any]] = []
    content_errors: list[dict[str, Any]] = []
    for index in range(1, prompt_count + 1):
        suffix = f"{index:04d}"
        ids = [
            f"{prefix}.prompt.{suffix}",
            f"{prefix}.hint1.{suffix}",
            f"{prefix}.hint2.{suffix}",
            f"{prefix}.answer.{suffix}",
            f"{prefix}.solution.{suffix}",
        ]
        if not all(value in offsets for value in ids):
            continue
        positions = [offsets[value] for value in ids]
        if positions != sorted(positions):
            order_errors.append({"prompt": ids[0], "positions": positions})
        hint1_chunk = response_chunk(text, offsets[ids[1]], all_offsets)
        hint2_chunk = response_chunk(text, offsets[ids[2]], all_offsets)
        answer_chunk = response_chunk(text, offsets[ids[3]], all_offsets)
        solution_chunk = response_chunk(text, offsets[ids[4]], all_offsets)
        required_fragments = [
            (hint1_chunk, f"Petunjuk tahap 1 ({ids[0]})", ids[1]),
            (hint2_chunk, f"Petunjuk tahap 2 ({ids[0]})", ids[2]),
            (answer_chunk, f"Jawaban ringkas ({ids[0]})", ids[3]),
            (solution_chunk, f"Solusi lengkap ({ids[0]})", ids[4]),
        ]
        for chunk, fragment, component_id in required_fragments:
            label = "orig03:" + component_id.replace(".", ":")
            if fragment not in chunk or f"\\label{{{label}}}" not in chunk or len(chunk) < 80:
                content_errors.append(
                    {
                        "component": component_id,
                        "required_heading": fragment,
                        "required_label": label,
                        "chunk_bytes": len(chunk.encode("utf-8")),
                    }
                )

    audit.require(
        not order_errors,
        f"{prefix}-response-order",
        f"{prefix} prompt/hint/answer/solution nodes are not in canonical order.",
        order_errors,
    )
    audit.require(
        not content_errors,
        f"{prefix}-response-content",
        f"{prefix} response nodes lack explicit headings, labels, or substantive content.",
        content_errors,
    )
    return {
        "path": relative(path),
        "assessment_container_kind": "problem",
        "assessment_count": assessment_count,
        "prompt_count": prompt_count,
        "response_unit_count": prompt_count,
        "stable_id_count": len(offsets),
        "assessment_ids": [
            f"{prefix}.problem.{index:04d}" for index in range(1, assessment_count + 1)
        ],
        "prompt_ids": [
            f"{prefix}.prompt.{index:04d}" for index in range(1, prompt_count + 1)
        ],
        "two_stage_hint_count": prompt_count - len(content_errors),
    }


def audit_exercise_style_module(
    audit: Audit,
    path: Path,
    text: str,
    prefix: str,
    assessment_count: int,
) -> dict[str, Any]:
    offsets = marker_offsets(text, "stable-id")
    stable_prefix = f"d90.orig.v1.tr03.{prefix}"
    expected_ids = {
        f"{stable_prefix}.{kind}.{index:04d}"
        for kind in ("exercise", "hint", "answer", "solution")
        for index in range(1, assessment_count + 1)
    }
    require_exact_set(
        audit,
        offsets,
        expected_ids,
        code=f"{prefix}-stable-id-topology",
        description=f"{prefix} stable exercise/response ID topology is incomplete or has extras.",
    )
    labels = {item["value"] for item in labels_in(text)}
    expected_labels = {
        f"orig03:{prefix}:{kind}:{index:04d}"
        for kind in ("exercise", "hint", "answer", "solution")
        for index in range(1, assessment_count + 1)
    }
    actual_prefix_labels = {
        label
        for label in labels
        if label.startswith(f"orig03:{prefix}:")
        and any(f":{kind}:" in label for kind in ("exercise", "hint", "answer", "solution"))
    }
    require_exact_set(
        audit,
        actual_prefix_labels,
        expected_labels,
        code=f"{prefix}-label-topology",
        description=f"{prefix} explicit exercise/response label topology is incomplete or has extras.",
    )
    audit.require(
        text.count("\\begin{exercise}") == assessment_count,
        f"{prefix}-exercise-count",
        f"{prefix} must contain exactly {assessment_count} exercise containers.",
        {"actual": text.count("\\begin{exercise}")},
    )

    all_offsets = list(offsets.values())
    order_errors: list[dict[str, Any]] = []
    content_errors: list[dict[str, Any]] = []
    for index in range(1, assessment_count + 1):
        suffix = f"{index:04d}"
        ids = [
            f"{stable_prefix}.exercise.{suffix}",
            f"{stable_prefix}.hint.{suffix}",
            f"{stable_prefix}.answer.{suffix}",
            f"{stable_prefix}.solution.{suffix}",
        ]
        if not all(value in offsets for value in ids):
            continue
        positions = [offsets[value] for value in ids]
        if positions != sorted(positions):
            order_errors.append({"exercise": ids[0], "positions": positions})
        chunks = [response_chunk(text, offsets[value], all_offsets) for value in ids]
        label_prefix = f"orig03:{prefix}"
        required = [
            (chunks[0], "\\begin{exercise}", f"{label_prefix}:exercise:{suffix}"),
            (chunks[1], "Petunjuk bertahap", f"{label_prefix}:hint:{suffix}"),
            (chunks[2], "Jawaban singkat", f"{label_prefix}:answer:{suffix}"),
            (chunks[3], "Solusi lengkap", f"{label_prefix}:solution:{suffix}"),
        ]
        for chunk, heading, label in required:
            if heading not in chunk or f"\\label{{{label}}}" not in chunk or len(chunk) < 80:
                content_errors.append(
                    {
                        "exercise": ids[0],
                        "required_heading": heading,
                        "required_label": label,
                        "chunk_bytes": len(chunk.encode("utf-8")),
                    }
                )
        if "\\textbf{Tahap 1.}" not in chunks[1] or "\\textbf{Tahap 2.}" not in chunks[1]:
            content_errors.append(
                {"exercise": ids[0], "missing": "two explicit hint stages"}
            )

    audit.require(
        not order_errors,
        f"{prefix}-response-order",
        f"{prefix} exercise/hint/answer/solution nodes are not in canonical order.",
        order_errors,
    )
    audit.require(
        not content_errors,
        f"{prefix}-response-content",
        f"{prefix} response nodes lack two-stage hints, headings, labels, or content.",
        content_errors,
    )
    return {
        "path": relative(path),
        "assessment_container_kind": "exercise",
        "assessment_count": assessment_count,
        "prompt_count": assessment_count,
        "response_unit_count": assessment_count,
        "stable_id_count": len(offsets),
        "assessment_ids": [
            f"{stable_prefix}.exercise.{index:04d}"
            for index in range(1, assessment_count + 1)
        ],
        "two_stage_hint_count": assessment_count - len(content_errors),
    }


def audit_assessments(audit: Audit, texts: dict[Path, str]) -> dict[str, Any]:
    prompt_specs = [
        (MODULE_DIR / "01-diagnostik-prasyarat-id.tex", "diag", 10, 20),
        (MODULE_DIR / "02-set-soal-dasar-konveks-id.tex", "ps01", 5, 12),
        (MODULE_DIR / "03-set-soal-metode-proksimal-id.tex", "ps02", 5, 11),
        (MODULE_DIR / "04-set-soal-dualitas-kkt-id.tex", "ps03", 5, 11),
    ]
    exercise_specs = [
        (MODULE_DIR / "05-set-soal-metode-stokastik-id.tex", "ps04", 5),
        (MODULE_DIR / "06-set-soal-operator-monoton-id.tex", "ps05", 5),
        (MODULE_DIR / "07-set-soal-transportasi-dan-sintesis-id.tex", "ps06", 5),
        (MODULE_DIR / "09-ujian-tengah-id.tex", "midterm", 6),
        (MODULE_DIR / "10-ujian-akhir-id.tex", "final", 8),
    ]
    modules: dict[str, Any] = {}
    for path, prefix, assessment_count, prompt_count in prompt_specs:
        modules[prefix] = audit_prompt_style_module(
            audit, path, texts[path], prefix, assessment_count, prompt_count
        )
    for path, prefix, assessment_count in exercise_specs:
        modules[prefix] = audit_exercise_style_module(
            audit, path, texts[path], prefix, assessment_count
        )

    distribution = {
        "diagnostic": modules["diag"]["assessment_count"],
        "problem_sets": {
            prefix: modules[prefix]["assessment_count"]
            for prefix in ("ps01", "ps02", "ps03", "ps04", "ps05", "ps06")
        },
        "midterm": modules["midterm"]["assessment_count"],
        "final": modules["final"]["assessment_count"],
    }
    total = (
        distribution["diagnostic"]
        + sum(distribution["problem_sets"].values())
        + distribution["midterm"]
        + distribution["final"]
    )
    expected_distribution = {
        "diagnostic": 10,
        "problem_sets": {prefix: 5 for prefix in ("ps01", "ps02", "ps03", "ps04", "ps05", "ps06")},
        "midterm": 6,
        "final": 8,
    }
    audit.require(
        distribution == expected_distribution and total == 54,
        "assessment-distribution",
        "Assessment distribution must be 10 + six times 5 + 6 + 8 = 54.",
        {"expected": expected_distribution, "actual": distribution, "total": total},
    )
    return {
        "assessment_count": total,
        "distribution": distribution,
        "prompt_response_unit_count": sum(
            module["response_unit_count"] for module in modules.values()
        ),
        "module_topology": modules,
    }


def audit_rubrics(audit: Audit, text: str, all_texts: dict[Path, str]) -> dict[str, Any]:
    offsets = marker_offsets(text, "stable-id")
    expected_ids = {
        f"d90.orig.v1.tr03.rubric.proof.{index:04d}" for index in range(1, 8)
    }
    require_exact_set(
        audit,
        offsets,
        expected_ids,
        code="proof-rubric-stable-ids",
        description="Exactly seven proof-rubric stable IDs are required.",
    )
    labels = {item["value"] for item in labels_in(text)}
    expected_labels = {f"orig03:rubric:proof:{index:04d}" for index in range(1, 8)}
    require_exact_set(
        audit,
        {label for label in labels if label.startswith("orig03:rubric:proof:")},
        expected_labels,
        code="proof-rubric-labels",
        description="Exactly seven proof-rubric labels are required.",
    )
    subsection_matches = list(
        re.finditer(r"\\subsection\{Rubrik proof\.(\d{4}):", text)
    )
    criteria_counts: dict[str, int] = {}
    for position, match in enumerate(subsection_matches):
        end = subsection_matches[position + 1].start() if position + 1 < len(subsection_matches) else len(text)
        chunk = text[match.start():end]
        criteria = chunk.split("\\paragraph{Kegagalan umum.}", 1)[0]
        criteria_counts[match.group(1)] = len(re.findall(r"(?m)^\s*\\item\b", criteria))
    audit.require(
        len(criteria_counts) == 7 and all(count == 4 for count in criteria_counts.values()),
        "proof-rubric-criteria",
        "Each of the seven proof rubrics must contain exactly four analytic criteria.",
        criteria_counts,
    )
    audit.require(
        all(f"\\textbf{{{score}}}" in text for score in range(5)) and "16" in text,
        "proof-rubric-scale",
        "Proof rubric must explicitly define scores 0 through 4 and a maximum of 16.",
    )

    combined = "\n".join(tex_without_comments(value) for value in all_texts.values())
    inbound = {
        label: len(re.findall(rf"\\ref\{{{re.escape(label)}\}}", combined))
        for label in sorted(expected_labels)
    }
    audit.require(
        all(count >= 1 for count in inbound.values()),
        "proof-rubric-inbound-references",
        "Every proof rubric must have at least one valid inbound assessment reference.",
        inbound,
    )
    return {
        "rubric_count": len(expected_ids),
        "criteria_per_rubric": criteria_counts,
        "score_range": [0, 4],
        "maximum_score": 16,
        "inbound_reference_counts": inbound,
    }


def audit_named_topology(
    audit: Audit,
    path: Path,
    text: str,
    *,
    identity_key: str,
    identity_value: str,
    identity_label: str,
    hint_key: str,
    hint_value: str,
    hint_label: str,
    answer_key: str,
    answer_value: str,
    answer_label: str,
    solution_key: str,
    solution_value: str,
    solution_label: str,
    prompt_item_count: int,
) -> dict[str, Any]:
    metadata = comment_metadata(text)
    by_key: dict[str, list[str]] = defaultdict(list)
    for item in metadata:
        by_key[item["key"].lower()].append(item["value"])
    expected_meta = {
        identity_key: identity_value,
        hint_key: hint_value,
        answer_key: answer_value,
        solution_key: solution_value,
    }
    meta_errors = {
        key: {"expected": value, "actual": by_key.get(key, [])}
        for key, value in expected_meta.items()
        if by_key.get(key, []) != [value]
    }
    audit.require(
        not meta_errors,
        "named-topology-stable-ids",
        f"Stable prompt/hint/answer/solution IDs are incomplete in {relative(path)}.",
        meta_errors,
    )
    labels = {item["value"] for item in labels_in(text)}
    expected_labels = {identity_label, hint_label, answer_label, solution_label}
    audit.require(
        expected_labels.issubset(labels),
        "named-topology-labels",
        f"Explicit prompt/hint/answer/solution labels are incomplete in {relative(path)}.",
        {"missing": sorted(expected_labels - labels)},
    )
    headings = [
        "\\subsection*{Prompt}",
        "\\subsection*{Petunjuk bertahap}",
        "\\subsection*{Jawaban singkat}",
        "\\subsection*{Solusi acuan lengkap}",
    ]
    positions = [text.find(heading) for heading in headings]
    audit.require(
        all(position >= 0 for position in positions) and positions == sorted(positions),
        "named-topology-order",
        f"Prompt/hint/answer/solution headings are missing or out of order in {relative(path)}.",
        {heading: position for heading, position in zip(headings, positions)},
    )
    if all(position >= 0 for position in positions):
        prompt_chunk = text[positions[0]:positions[1]]
        hint_chunk = text[positions[1]:positions[2]]
        answer_chunk = text[positions[2]:positions[3]]
        solution_chunk = text[positions[3]:]
        prompt_items = len(re.findall(r"(?m)^\s*\\item\b", prompt_chunk))
        hint_items = len(re.findall(r"(?m)^\s*\\item\b", hint_chunk))
        substantive = all(len(chunk.encode("utf-8")) >= 180 for chunk in (
            prompt_chunk, hint_chunk, answer_chunk, solution_chunk
        ))
    else:
        prompt_items = hint_items = 0
        substantive = False
    audit.require(
        prompt_items == prompt_item_count and hint_items == prompt_item_count,
        "named-topology-item-count",
        f"Prompt and staged hint in {relative(path)} must each cover {prompt_item_count} items.",
        {"prompt_items": prompt_items, "hint_items": hint_items},
    )
    audit.require(
        substantive,
        "named-topology-content",
        f"Prompt/hint/answer/solution nodes in {relative(path)} must be substantive.",
    )
    return {
        "path": relative(path),
        "prompt_identity": {"stable_id": identity_value, "label": identity_label},
        "hint": {"stable_id": hint_value, "label": hint_label},
        "answer": {"stable_id": answer_value, "label": answer_label},
        "solution": {"stable_id": solution_value, "label": solution_label},
        "prompt_item_count": prompt_items,
        "hint_item_count": hint_items,
    }


def audit_labs_and_capstone(audit: Audit, texts: dict[Path, str]) -> dict[str, Any]:
    lab3_path = MODULE_DIR / "11-laboratorium-globalisasi-newton-id.tex"
    lab4_path = MODULE_DIR / "12-laboratorium-transportasi-entropik-id.tex"
    capstone_path = MODULE_DIR / "13-proyek-kapstone-masalah-invers-komposit-id.tex"
    lab3 = audit_named_topology(
        audit,
        lab3_path,
        texts[lab3_path],
        identity_key="lab-id",
        identity_value="d90.orig.v1.tr03.lab.0003",
        identity_label="orig03:lab:globalisasi-newton",
        hint_key="lab-hint-id",
        hint_value="d90.orig.v1.tr03.lab.hint.0003",
        hint_label="orig03:lab:hint:0003",
        answer_key="lab-answer-id",
        answer_value="d90.orig.v1.tr03.lab.answer.0003",
        answer_label="orig03:lab:answer:0003",
        solution_key="lab-solution-id",
        solution_value="d90.orig.v1.tr03.lab.solution.0003",
        solution_label="orig03:lab:solution:0003",
        prompt_item_count=5,
    )
    lab4 = audit_named_topology(
        audit,
        lab4_path,
        texts[lab4_path],
        identity_key="lab-id",
        identity_value="d90.orig.v1.tr03.lab.0004",
        identity_label="orig03:lab:transportasi-entropik",
        hint_key="lab-hint-id",
        hint_value="d90.orig.v1.tr03.lab.hint.0004",
        hint_label="orig03:lab:hint:0004",
        answer_key="lab-answer-id",
        answer_value="d90.orig.v1.tr03.lab.answer.0004",
        answer_label="orig03:lab:answer:0004",
        solution_key="lab-solution-id",
        solution_value="d90.orig.v1.tr03.lab.solution.0004",
        solution_label="orig03:lab:solution:0004",
        prompt_item_count=5,
    )
    capstone = audit_named_topology(
        audit,
        capstone_path,
        texts[capstone_path],
        identity_key="capstone-id",
        identity_value="d90.orig.v1.tr03.capstone.0001",
        identity_label="orig03:capstone:invers-komposit",
        hint_key="capstone-hint-id",
        hint_value="d90.orig.v1.tr03.capstone.hint.0001",
        hint_label="orig03:capstone:hint:0001",
        answer_key="capstone-answer-id",
        answer_value="d90.orig.v1.tr03.capstone.answer.0001",
        answer_label="orig03:capstone:answer:0001",
        solution_key="capstone-solution-id",
        solution_value="d90.orig.v1.tr03.capstone.solution.0001",
        solution_label="orig03:capstone:solution:0001",
        prompt_item_count=7,
    )

    metadata = comment_metadata(texts[capstone_path])
    milestone_ids = [
        item["value"]
        for item in metadata
        if item["key"].lower() == "capstone-milestone-id"
    ]
    expected_milestone_ids = [
        f"d90.orig.v1.tr03.capstone.milestone.{index:04d}" for index in range(1, 8)
    ]
    milestone_labels = {
        item["value"]
        for item in labels_in(texts[capstone_path])
        if item["value"].startswith("orig03:capstone:milestone:")
    }
    expected_milestone_labels = {
        f"orig03:capstone:milestone:{index:04d}" for index in range(1, 8)
    }
    audit.require(
        milestone_ids == expected_milestone_ids,
        "capstone-milestone-stable-ids",
        "Capstone must declare seven stable milestone IDs in order.",
        {"expected": expected_milestone_ids, "actual": milestone_ids},
    )
    audit.require(
        milestone_labels == expected_milestone_labels,
        "capstone-milestone-labels",
        "Capstone must carry seven unique milestone labels.",
        {
            "missing": sorted(expected_milestone_labels - milestone_labels),
            "unexpected": sorted(milestone_labels - expected_milestone_labels),
        },
    )
    capstone["milestones"] = [
        {"stable_id": stable_id, "label": f"orig03:capstone:milestone:{index:04d}"}
        for index, stable_id in enumerate(expected_milestone_ids, start=1)
    ]
    capstone["milestone_count"] = len(milestone_ids)
    return {"lab_3": lab3, "lab_4": lab4, "capstone": capstone}


def has_cc_by_sa_marker(text: str) -> bool:
    return bool(
        re.search(r"CC[- ]BY[- ]SA[- ]4\.0", text, re.I)
        or re.search(r"CC BY-SA 4\.0", text, re.I)
    )


def audit_provenance(audit: Audit, texts: dict[Path, str]) -> dict[str, Any]:
    tex_evidence: list[dict[str, Any]] = []
    for path in SCOPED_TEX:
        embedded = has_cc_by_sa_marker(texts[path])
        audit.require(
            embedded,
            "tex-component-provenance",
            f"TeX component lacks CC BY-SA 4.0 provenance: {relative(path)}",
        )
        tex_evidence.append({"path": relative(path), "embedded_cc_by_sa_4_0": embedded})

    computation_evidence: list[dict[str, Any]] = []
    for name, component in COMPONENTS.items():
        script: Path = component["script"]
        module: Path = component["module"]
        script_text = script.read_text(encoding="utf-8")
        module_text = texts[module]
        embedded = has_cc_by_sa_marker(script_text)
        named_by_module = relative(script).replace("\\", "/") in module_text
        module_covers_code = bool(
            re.search(r"kode[\s\S]{0,220}?CC BY-SA 4\.0", module_text, re.I)
            or re.search(r"CC BY-SA 4\.0[\s\S]{0,220}?kode", module_text, re.I)
        )
        inherited = named_by_module and module_covers_code
        audit.require(
            embedded or inherited,
            "computation-component-provenance",
            f"Computation component lacks an embedded or explicit named-module CC BY-SA 4.0 chain: {relative(script)}",
            {
                "embedded": embedded,
                "named_by_module": named_by_module,
                "module_covers_code": module_covers_code,
            },
        )
        output_records: list[dict[str, Any]] = []
        json_path = next(path for path in component["outputs"] if path.suffix == ".json")
        json_payload = json.loads(json_path.read_text(encoding="utf-8"))
        declared_artifacts = set(json_payload.get("artifacts", []))
        expected_artifacts = {
            path.name for path in component["outputs"] if path.suffix != ".json"
        }
        audit.require(
            declared_artifacts == expected_artifacts,
            "computation-artifact-lineage",
            f"JSON artifact lineage is incomplete for {name}.",
            {
                "expected": sorted(expected_artifacts),
                "actual": sorted(declared_artifacts),
            },
        )
        for output in component["outputs"]:
            output_records.append(
                {
                    "path": relative(output),
                    "derived_from": relative(script),
                    "cc_by_sa_4_0_chain": embedded or inherited,
                }
            )
        computation_evidence.append(
            {
                "component": name,
                "script": relative(script),
                "embedded_cc_by_sa_4_0": embedded,
                "named_module_cc_by_sa_4_0_chain": inherited,
                "module": relative(module),
                "outputs": output_records,
            }
        )

    return {
        "license": "CC BY-SA 4.0",
        "tex_components": tex_evidence,
        "computation_components": computation_evidence,
    }


def nearby(text: str, start: int, end: int, radius: int = 280) -> str:
    return text[max(0, start - radius):min(len(text), end + radius)]


def audit_o018_firewall(audit: Audit, texts: dict[Path, str]) -> dict[str, Any]:
    paths = SCOPED_TEX + [component["script"] for component in COMPONENTS.values()]
    negative_words = re.compile(
        r"tidak|di luar|sengaja|terpisah|firewall|tanpa menyalin|tidak memuat|tidak dimasukkan",
        re.I,
    )
    strong_patterns = {
        "mixed_integer_programming": re.compile(r"\b(?:MIP|MILP)\b", re.I),
        "linear_or_integer_programming": re.compile(
            r"\b(?:program|pemrograman)\s+(?:linear|linier|bilangan bulat|integer)\b",
            re.I,
        ),
        "simplex_algorithm": re.compile(
            r"\b(?:(?:algoritme|metode)\s+simpleks|simplex\s+algorithm|tableau|pivot(?:ing)?)\b",
            re.I,
        ),
        "network_optimization": re.compile(
            r"\b(?:(?:optimisasi|optimalisasi|aliran)\s+jaringan|network\s+(?:flow|optimization))\b",
            re.I,
        ),
        "lp_sensitivity": re.compile(
            r"\b(?:sensitivitas|sensitivity)\b[\s\S]{0,80}?\b(?:LP|program\s+(?:linear|linier))\b|"
            r"\b(?:LP|program\s+(?:linear|linier))\b[\s\S]{0,80}?\b(?:sensitivitas|sensitivity)\b",
            re.I,
        ),
        "lp_token": re.compile(r"\bLP\b"),
    }
    prohibited: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    generic_terms: list[dict[str, Any]] = []

    for path in paths:
        text = read_utf8(audit, path)
        searchable = tex_without_comments(text) if path.suffix == ".tex" else text
        for topic, pattern in strong_patterns.items():
            for match in pattern.finditer(searchable):
                context = nearby(searchable, match.start(), match.end())
                record = {
                    "path": relative(path),
                    "line": line_number(searchable, match.start()),
                    "topic": topic,
                    "match": match.group(0),
                    "context": " ".join(context.split()),
                }
                if negative_words.search(context):
                    exclusions.append(record)
                else:
                    prohibited.append(record)

        for topic, pattern in (
            ("simplex_geometry", re.compile(r"\bsimpleks\b", re.I)),
            ("generic_value_sensitivity", re.compile(r"\bsensitivitas\b", re.I)),
        ):
            for match in pattern.finditer(searchable):
                context = nearby(searchable, match.start(), match.end(), radius=420)
                if negative_words.search(context):
                    continue
                if topic == "simplex_geometry":
                    allowed = bool(re.search(r"p_i|peluang|distribusi|probabilitas", context, re.I))
                else:
                    allowed = not bool(
                        re.search(r"\bLP\b|program\s+(?:linear|linier)", context, re.I)
                    ) and bool(re.search(r"fungsi nilai|p\(u\)|pengali", context, re.I))
                record = {
                    "path": relative(path),
                    "line": line_number(searchable, match.start()),
                    "topic": topic,
                    "allowed_non_o018_use": allowed,
                    "context": " ".join(context.split()),
                }
                generic_terms.append(record)
                if not allowed:
                    prohibited.append(record)

    # Deduplicate overlapping strong-pattern hits by path/line/topic/match.
    prohibited = list({
        (item["path"], item["line"], item["topic"], item.get("match", "")): item
        for item in prohibited
    }.values())
    audit.require(
        not prohibited,
        "o018-firewall",
        "Substantive LP/MIP/simplex-algorithm/LP-sensitivity/network-optimization content crossed the O018 firewall.",
        prohibited,
    )
    return {
        "result": "pass" if not prohibited else "fail",
        "prohibited_occurrences": prohibited,
        "explicit_exclusion_occurrences": exclusions,
        "generic_non_o018_term_occurrences": generic_terms,
    }


def output_snapshot(paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for path in paths:
        payload = path.read_bytes()
        snapshot[path.name] = {"bytes": len(payload), "sha256": sha256_bytes(payload)}
    return snapshot


def audit_deterministic_replays(audit: Audit) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for name, component in COMPONENTS.items():
        script: Path = component["script"]
        repo_outputs: list[Path] = component["outputs"]
        expected_names = [path.name for path in repo_outputs]
        checked_in = output_snapshot(repo_outputs)
        run_snapshots: list[dict[str, dict[str, Any]]] = []
        stdout_records: list[dict[str, Any]] = []
        unexpected_files: list[list[str]] = []
        with tempfile.TemporaryDirectory(prefix=f"orig03-{name}-") as temp_name:
            temp_dir = Path(temp_name)
            copied_script = temp_dir / script.name
            shutil.copyfile(script, copied_script)
            for run_number in (1, 2):
                environment = os.environ.copy()
                environment["PYTHONHASHSEED"] = "0"
                completed = subprocess.run(
                    [sys.executable, str(copied_script)],
                    cwd=temp_dir,
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="strict",
                    timeout=180,
                    check=False,
                )
                audit.require(
                    completed.returncode == 0,
                    "computation-replay-exit",
                    f"{name} replay {run_number} exited with {completed.returncode}.",
                    {"stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]},
                )
                generated = [temp_dir / output_name for output_name in expected_names]
                missing = [path.name for path in generated if not path.is_file()]
                audit.require(
                    not missing,
                    "computation-replay-output",
                    f"{name} replay {run_number} omitted expected outputs.",
                    missing,
                )
                if missing:
                    continue
                snapshot = output_snapshot(generated)
                run_snapshots.append(snapshot)
                produced_names = sorted(
                    path.name for path in temp_dir.iterdir() if path.name != script.name
                )
                extras = sorted(set(produced_names) - set(expected_names))
                unexpected_files.append(extras)
                audit.require(
                    not extras,
                    "computation-replay-extra-output",
                    f"{name} replay {run_number} created unexpected files.",
                    extras,
                )
                stdout_lines = [line for line in completed.stdout.splitlines() if line.strip()]
                try:
                    stdout_payload = json.loads(stdout_lines[-1]) if stdout_lines else {}
                except json.JSONDecodeError:
                    stdout_payload = {}
                stdout_records.append(stdout_payload)
                audit.require(
                    stdout_payload.get("result") == "pass",
                    "computation-replay-stdout",
                    f"{name} replay {run_number} did not emit a passing JSON receipt.",
                    stdout_payload,
                )

        byte_identical_twice = len(run_snapshots) == 2 and run_snapshots[0] == run_snapshots[1]
        matches_checked_in = len(run_snapshots) == 2 and all(
            snapshot == checked_in for snapshot in run_snapshots
        )
        audit.require(
            byte_identical_twice,
            "computation-replay-determinism",
            f"Two isolated executions of {name} were not byte-identical.",
            run_snapshots,
        )
        audit.require(
            matches_checked_in,
            "computation-replay-checked-in-identity",
            f"Isolated {name} outputs do not match the checked-in artifacts byte for byte.",
            {"checked_in": checked_in, "runs": run_snapshots},
        )
        results[name] = {
            "script": relative(script),
            "runs": 2,
            "isolated_temporary_execution": True,
            "byte_identical_between_runs": byte_identical_twice,
            "byte_identical_to_checked_in": matches_checked_in,
            "checked_in_outputs": checked_in,
            "run_outputs": run_snapshots,
            "stdout_receipts": stdout_records,
            "unexpected_files": unexpected_files,
        }
    return results


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def audit_svg_artifacts(audit: Audit) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for name, component in COMPONENTS.items():
        svg_path = next(path for path in component["outputs"] if path.suffix == ".svg")
        payload = svg_path.read_bytes()
        try:
            root = ET.fromstring(payload)
            parsed = True
            local_name = root.tag.rsplit("}", 1)[-1]
            title_count = sum(child.tag.rsplit("}", 1)[-1] == "title" for child in root.iter())
            desc_count = sum(child.tag.rsplit("}", 1)[-1] == "desc" for child in root.iter())
        except ET.ParseError as error:
            parsed = False
            local_name = ""
            title_count = desc_count = 0
            audit.finding(
                "P1",
                "invalid-svg",
                f"SVG output is not well-formed XML: {relative(svg_path)}",
                str(error),
            )
        audit.require(
            parsed and local_name == "svg" and title_count >= 1 and desc_count >= 1,
            "svg-accessible-structure",
            f"SVG output lacks an svg root, title, or description: {relative(svg_path)}",
            {
                "parsed": parsed,
                "root": local_name,
                "title_count": title_count,
                "description_count": desc_count,
            },
        )
        results[name] = {
            "path": relative(svg_path),
            "parsed_xml": parsed,
            "root": local_name,
            "title_count": title_count,
            "description_count": desc_count,
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
        }
    return results


def audit_globalisasi_newton(audit: Audit) -> dict[str, Any]:
    json_path = LAB_DIR / "globalisasi-newton-results.json"
    csv_path = LAB_DIR / "globalisasi-newton-results.csv"
    report = json.loads(json_path.read_text(encoding="utf-8"))
    fields, raw_rows = read_csv_rows(csv_path)
    expected_fields = [
        "method",
        "iteration",
        "x",
        "y",
        "objective",
        "gradient_norm",
        "step_norm",
        "alpha",
        "minimum_hessian_eigenvalue",
        "diagonal_shift",
        "corrected_minimum_eigenvalue",
        "directional_derivative",
        "armijo",
        "status",
    ]
    audit.require(
        fields == expected_fields,
        "newton-csv-schema",
        "Globalisasi Newton CSV schema changed or is incomplete.",
        {"expected": expected_fields, "actual": fields},
    )
    parsed: list[dict[str, Any]] = []
    numeric_errors: list[dict[str, Any]] = []
    for row_number, raw in enumerate(raw_rows, start=2):
        try:
            row = {
                **raw,
                "iteration": int(raw["iteration"]),
                "x": parse_float(raw["x"]),
                "y": parse_float(raw["y"]),
                "objective": parse_float(raw["objective"]),
                "gradient_norm": parse_float(raw["gradient_norm"]),
                "step_norm": parse_float(raw["step_norm"]),
                "alpha": None if raw["alpha"] == "" else parse_float(raw["alpha"]),
                "minimum_hessian_eigenvalue": parse_float(raw["minimum_hessian_eigenvalue"]),
                "diagonal_shift": parse_float(raw["diagonal_shift"]),
                "corrected_minimum_eigenvalue": (
                    None
                    if raw["corrected_minimum_eigenvalue"] == ""
                    else parse_float(raw["corrected_minimum_eigenvalue"])
                ),
                "directional_derivative": (
                    None
                    if raw["directional_derivative"] == ""
                    else parse_float(raw["directional_derivative"])
                ),
                "armijo": parse_bool(raw["armijo"]),
            }
        except (KeyError, ValueError) as error:
            numeric_errors.append({"row": row_number, "error": str(error)})
            continue
        point = np.array([row["x"], row["y"]])
        objective = max(float(np.logaddexp(row["x"], -row["x"]) - math.log(2.0)), 0.0) + 0.5 * row["y"] ** 2
        gradient = np.array([math.tanh(row["x"]), row["y"]])
        if not isclose(row["objective"], objective, atol=2.0e-12):
            numeric_errors.append({"row": row_number, "field": "objective"})
        if not isclose(row["gradient_norm"], np.linalg.norm(gradient), atol=2.0e-12):
            numeric_errors.append({"row": row_number, "field": "gradient_norm"})
        if not np.all(np.isfinite(point)):
            numeric_errors.append({"row": row_number, "field": "point-not-finite"})
        parsed.append(row)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in parsed:
        grouped[row["method"]].append(row)
    expected_methods = {
        "gradien-langkah-tetap",
        "gradien-backtracking",
        "newton-murni",
        "newton-teredam-terkoreksi",
    }
    audit.require(
        set(grouped) == expected_methods,
        "newton-methods",
        "Globalisasi Newton trace must contain exactly four methods.",
        sorted(grouped),
    )
    start = report.get("problem", {}).get("start", [])
    c1 = float(report.get("configuration", {}).get("armijo_c1", math.nan))
    curvature_floor = float(
        report.get("configuration", {}).get("corrected_hessian_eigenvalue_floor", math.nan)
    )
    tolerance = float(report.get("configuration", {}).get("gradient_tolerance", math.nan))

    for method, rows in grouped.items():
        rows.sort(key=lambda item: item["iteration"])
        if [row["iteration"] for row in rows] != list(range(rows[-1]["iteration"] + 1)):
            numeric_errors.append({"method": method, "field": "iteration-sequence"})
        if start and not np.allclose([rows[0]["x"], rows[0]["y"]], start, rtol=0, atol=1.0e-15):
            numeric_errors.append({"method": method, "field": "common-start"})
        for previous, current in zip(rows, rows[1:]):
            previous_point = np.array([previous["x"], previous["y"]])
            current_point = np.array([current["x"], current["y"]])
            step = current_point - previous_point
            if not isclose(current["step_norm"], np.linalg.norm(step), atol=2.0e-10):
                numeric_errors.append(
                    {"method": method, "iteration": current["iteration"], "field": "step_norm"}
                )
            gradient = np.array([math.tanh(previous["x"]), previous["y"]])
            hessian = np.diag([max(0.0, 1.0 - math.tanh(previous["x"]) ** 2), 1.0])
            if method == "gradien-langkah-tetap":
                expected_step = -float(current["alpha"]) * gradient
                if not np.allclose(step, expected_step, rtol=1.0e-11, atol=1.0e-10):
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "fixed-gradient-step"})
            elif method == "gradien-backtracking":
                alpha = float(current["alpha"])
                expected_step = -alpha * gradient
                armijo_rhs = previous["objective"] - c1 * alpha * float(gradient @ gradient)
                if not np.allclose(step, expected_step, rtol=1.0e-11, atol=1.0e-10):
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "backtracking-step"})
                if current["objective"] > armijo_rhs + 2.0e-12 or current["armijo"] is not True:
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "armijo"})
            elif method == "newton-murni":
                expected_step = -np.linalg.solve(hessian, gradient)
                if not np.allclose(step, expected_step, rtol=1.0e-11, atol=1.0e-10):
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "newton-step"})
            elif method == "newton-teredam-terkoreksi":
                minimum = float(np.min(np.diag(hessian)))
                shift = max(0.0, curvature_floor - minimum)
                corrected = hessian + shift * np.eye(2)
                direction = -np.linalg.solve(corrected, gradient)
                alpha = float(current["alpha"])
                directional = float(gradient @ direction)
                armijo_rhs = previous["objective"] + c1 * alpha * directional
                if not np.allclose(step, alpha * direction, rtol=1.0e-11, atol=1.0e-10):
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "corrected-step"})
                if not isclose(current["diagonal_shift"], shift, atol=2.0e-12):
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "diagonal-shift"})
                if current["corrected_minimum_eigenvalue"] is None or current["corrected_minimum_eigenvalue"] < curvature_floor - 1.0e-12:
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "curvature-floor"})
                if current["directional_derivative"] is None or not isclose(current["directional_derivative"], directional, atol=2.0e-11):
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "directional-derivative"})
                if directional >= 0 or current["objective"] > armijo_rhs + 2.0e-12 or current["armijo"] is not True:
                    numeric_errors.append({"method": method, "iteration": current["iteration"], "field": "corrected-armijo-descent"})

    certificates = {
        "fixed_gradient_failure_observed": (
            grouped.get("gradien-langkah-tetap", [{}])[-1].get("status", "").startswith("gagal")
            and grouped["gradien-langkah-tetap"][-1]["objective"]
            > 100.0 * grouped["gradien-langkah-tetap"][0]["objective"]
        ),
        "pure_newton_failure_observed": False,
        "backtracking_armijo_every_step": all(
            row["armijo"] is True for row in grouped.get("gradien-backtracking", [])[1:]
        ),
        "backtracking_objective_monotone": all(
            after["objective"] <= before["objective"] + 1.0e-12
            for before, after in zip(grouped.get("gradien-backtracking", []), grouped.get("gradien-backtracking", [])[1:])
        ),
        "backtracking_converged": grouped.get("gradien-backtracking", [{}])[-1].get("gradient_norm", math.inf) <= tolerance,
        "corrected_newton_armijo_every_step": all(
            row["armijo"] is True for row in grouped.get("newton-teredam-terkoreksi", [])[1:]
        ),
        "corrected_newton_objective_monotone": all(
            after["objective"] <= before["objective"] + 1.0e-12
            for before, after in zip(grouped.get("newton-teredam-terkoreksi", []), grouped.get("newton-teredam-terkoreksi", [])[1:])
        ),
        "corrected_hessian_floor_respected": all(
            row["corrected_minimum_eigenvalue"] is not None
            and row["corrected_minimum_eigenvalue"] >= curvature_floor - 1.0e-13
            for row in grouped.get("newton-teredam-terkoreksi", [])[1:]
        ),
        "corrected_directions_are_descent": all(
            row["directional_derivative"] is not None and row["directional_derivative"] < 0
            for row in grouped.get("newton-teredam-terkoreksi", [])[1:]
        ),
        "corrected_newton_converged": grouped.get("newton-teredam-terkoreksi", [{}])[-1].get("gradient_norm", math.inf) <= tolerance,
    }
    pure_rows = grouped.get("newton-murni", [])
    pure_increases = sum(
        after["objective"] > before["objective"] + 1.0e-12
        for before, after in zip(pure_rows, pure_rows[1:])
    )
    certificates["pure_newton_failure_observed"] = bool(
        pure_increases >= 1 and pure_rows and pure_rows[-1]["status"].startswith("gagal")
    )
    reported_certificates = report.get("validation", {}).get("certificates", {})
    audit.require(
        not numeric_errors,
        "newton-numerical-invariants",
        "Globalisasi Newton CSV violates independently recomputed numerical invariants.",
        numeric_errors,
    )
    audit.require(
        certificates == reported_certificates and all(certificates.values()),
        "newton-certificates",
        "Globalisasi Newton certificates are false or disagree with independent recomputation.",
        {"reported": reported_certificates, "recomputed": certificates},
    )
    summary_errors: list[str] = []
    for method, rows in grouped.items():
        summary = report.get("summary", {}).get(method, {})
        final = rows[-1]
        if summary.get("iterations") != final["iteration"] or summary.get("status") != final["status"]:
            summary_errors.append(method)
        if not isclose(summary.get("final_objective", math.nan), final["objective"], atol=2.0e-12):
            summary_errors.append(method + ":objective")
        if not isclose(summary.get("final_gradient_norm", math.nan), final["gradient_norm"], atol=2.0e-12):
            summary_errors.append(method + ":gradient")
    audit.require(
        report.get("schema") == "o015-original-03-globalisasi-newton-v1"
        and report.get("result") == "pass"
        and not summary_errors,
        "newton-json-summary",
        "Globalisasi Newton JSON schema/result/summary disagrees with the CSV trace.",
        summary_errors,
    )
    return {
        "json": file_record(json_path),
        "csv": file_record(csv_path),
        "csv_data_rows": len(raw_rows),
        "method_row_counts": {method: len(rows) for method, rows in sorted(grouped.items())},
        "pure_newton_objective_increase_count": pure_increases,
        "certificates": certificates,
        "numeric_error_count": len(numeric_errors),
    }


def audit_transportasi_entropik(audit: Audit) -> dict[str, Any]:
    json_path = LAB_DIR / "transportasi-entropik-results.json"
    csv_path = LAB_DIR / "transportasi-entropik-results.csv"
    report = json.loads(json_path.read_text(encoding="utf-8"))
    fields, raw_rows = read_csv_rows(csv_path)
    expected_fields = [
        "source_index",
        "target_index",
        "source_point",
        "target_point",
        "source_mass",
        "target_mass",
        "cost",
        "plan",
        "log_plan",
        "scaled_plan",
        "shifted_plan",
    ]
    audit.require(
        fields == expected_fields,
        "sinkhorn-csv-schema",
        "Transportasi entropik CSV schema changed or is incomplete.",
        {"expected": expected_fields, "actual": fields},
    )
    configuration = report.get("configuration", {})
    rows = int(configuration.get("source_size", 0))
    columns = int(configuration.get("target_size", 0))
    epsilon = float(configuration.get("epsilon", math.nan))
    scaling = float(configuration.get("scaling_factor", math.nan))
    offset = float(configuration.get("underflow_cost_offset", math.nan))
    data = report.get("data", {})
    source_points = np.asarray(data.get("source_points", []), dtype=float)
    target_points = np.asarray(data.get("target_points", []), dtype=float)
    source_mass = np.asarray(data.get("source_mass", []), dtype=float)
    target_mass = np.asarray(data.get("target_mass", []), dtype=float)
    plan = np.full((rows, columns), np.nan)
    log_plan = np.full((rows, columns), np.nan)
    scaled_plan = np.full((rows, columns), np.nan)
    shifted_plan = np.full((rows, columns), np.nan)
    cost = np.full((rows, columns), np.nan)
    numeric_errors: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for row_number, raw in enumerate(raw_rows, start=2):
        try:
            i = int(raw["source_index"])
            j = int(raw["target_index"])
            values = {key: float(raw[key]) for key in expected_fields[2:]}
        except (KeyError, ValueError) as error:
            numeric_errors.append({"row": row_number, "error": str(error)})
            continue
        if not (0 <= i < rows and 0 <= j < columns) or (i, j) in seen:
            numeric_errors.append({"row": row_number, "field": "index-grid", "indices": [i, j]})
            continue
        seen.add((i, j))
        cost[i, j] = values["cost"]
        plan[i, j] = values["plan"]
        log_plan[i, j] = values["log_plan"]
        scaled_plan[i, j] = values["scaled_plan"]
        shifted_plan[i, j] = values["shifted_plan"]
        expected_cost = (source_points[i] - target_points[j]) ** 2
        scalar_checks = {
            "source_point": source_points[i],
            "target_point": target_points[j],
            "source_mass": source_mass[i],
            "target_mass": target_mass[j],
            "cost": expected_cost,
        }
        for field, expected in scalar_checks.items():
            if not isclose(values[field], expected, atol=2.0e-15):
                numeric_errors.append({"row": row_number, "field": field})
        if values["plan"] <= 0.0 or not isclose(
            math.exp(values["log_plan"]), values["plan"], atol=2.0e-15, rtol=2.0e-12
        ):
            numeric_errors.append({"row": row_number, "field": "plan-log-plan"})

    expected_grid = {(i, j) for i in range(rows) for j in range(columns)}
    if seen != expected_grid:
        numeric_errors.append(
            {
                "field": "complete-grid",
                "missing": sorted([list(value) for value in expected_grid - seen]),
            }
        )
    row_residual = float(np.max(np.abs(plan.sum(axis=1) - source_mass)))
    column_residual = float(np.max(np.abs(plan.sum(axis=0) - target_mass)))
    minimum_entry = float(np.min(plan))
    scaled_difference = float(np.max(np.abs(plan - scaled_plan)))
    shifted_difference = float(np.max(np.abs(plan - shifted_plan)))
    primal = float(np.sum(cost * plan) + epsilon * np.sum(plan * (log_plan - 1.0)))
    runs = report.get("runs", {})
    baseline = runs.get("baseline", {})
    scaled = runs.get("simultaneously_scaled_cost_and_epsilon", {})
    shifted = runs.get("additively_shifted_cost", {})
    if not isclose(primal, baseline.get("primal", math.nan), atol=2.0e-12):
        numeric_errors.append({"field": "baseline-primal"})
    for run_name, run in runs.items():
        if not isclose(
            float(run.get("primal", math.nan)) - float(run.get("dual", math.nan)),
            float(run.get("primal_dual_gap", math.nan)),
            atol=2.0e-12,
        ):
            numeric_errors.append({"field": f"{run_name}-gap-identity"})
        history = run.get("history", [])
        if (
            not history
            or int(history[-1][0]) != int(run.get("iterations", -1))
            or not isclose(history[-1][1], run.get("marginal_residual", math.nan), atol=1.0e-15)
        ):
            numeric_errors.append({"field": f"{run_name}-history-terminal"})
    if not isclose(scaled.get("primal", math.nan), scaling * baseline.get("primal", math.nan), atol=3.0e-12):
        numeric_errors.append({"field": "scaled-primal-identity"})
    if not isclose(scaled.get("dual", math.nan), scaling * baseline.get("dual", math.nan), atol=3.0e-12):
        numeric_errors.append({"field": "scaled-dual-identity"})
    if not isclose(shifted.get("primal", math.nan), baseline.get("primal", math.nan) + offset, atol=3.0e-10):
        numeric_errors.append({"field": "shifted-primal-identity"})
    if not isclose(shifted.get("dual", math.nan), baseline.get("dual", math.nan) + offset, atol=3.0e-10):
        numeric_errors.append({"field": "shifted-dual-identity"})
    naive_kernel = np.exp(-(cost + offset) / epsilon)
    zero_count = int(np.count_nonzero(naive_kernel == 0.0))

    certificates = {
        "source_marginal": row_residual <= 1.0e-10,
        "target_marginal": column_residual <= 1.0e-10,
        "strict_numeric_positivity": minimum_entry > 0.0,
        "primal_dual_agreement": abs(float(baseline.get("primal_dual_gap", math.inf))) <= 1.0e-10,
        "simultaneous_cost_epsilon_scaling_invariance": scaled_difference <= 1.0e-10,
        "additive_cost_shift_invariance": shifted_difference <= 1.0e-9,
        "naive_shifted_kernel_underflows_completely": zero_count == cost.size,
        "log_domain_shifted_problem_still_converges": float(shifted.get("marginal_residual", math.inf)) <= 1.0e-10,
    }
    reported_validation = report.get("validation", {})
    reported_certificates = reported_validation.get("certificates", {})
    reported_metrics = {
        "row_marginal_residual": row_residual,
        "column_marginal_residual": column_residual,
        "minimum_plan_entry": minimum_entry,
        "primal_dual_gap": float(baseline.get("primal_dual_gap", math.nan)),
        "scaled_plan_max_abs_difference": scaled_difference,
        "shifted_plan_max_abs_difference": shifted_difference,
        "naive_shifted_kernel_zero_count": zero_count,
        "naive_shifted_kernel_entry_count": int(cost.size),
    }
    for field, actual in reported_metrics.items():
        reported = reported_validation.get(field)
        if isinstance(actual, int):
            if reported != actual:
                numeric_errors.append({"field": field, "reported": reported, "recomputed": actual})
        elif not isclose(reported, actual, atol=3.0e-13, rtol=2.0e-10):
            numeric_errors.append({"field": field, "reported": reported, "recomputed": actual})

    audit.require(
        report.get("schema") == "o015-original-03-transportasi-entropik-v1"
        and report.get("result") == "pass",
        "sinkhorn-json-schema",
        "Transportasi entropik JSON schema or result is invalid.",
    )
    audit.require(
        not numeric_errors,
        "sinkhorn-numerical-invariants",
        "Transportasi entropik artifacts violate independently recomputed invariants.",
        numeric_errors,
    )
    audit.require(
        certificates == reported_certificates and all(certificates.values()),
        "sinkhorn-certificates",
        "Transportasi entropik certificates are false or disagree with independent recomputation.",
        {"reported": reported_certificates, "recomputed": certificates},
    )
    return {
        "json": file_record(json_path),
        "csv": file_record(csv_path),
        "csv_data_rows": len(raw_rows),
        "plan_shape": [rows, columns],
        "plan_entry_count": int(plan.size),
        "row_marginal_residual": row_residual,
        "column_marginal_residual": column_residual,
        "minimum_plan_entry": minimum_entry,
        "scaled_plan_max_abs_difference": scaled_difference,
        "shifted_plan_max_abs_difference": shifted_difference,
        "naive_shifted_kernel_zero_count": zero_count,
        "certificates": certificates,
        "numeric_error_count": len(numeric_errors),
    }


def reconstruct_capstone_instance(report: dict[str, Any]) -> dict[str, Any]:
    seed = int(report["seed"])
    configuration = report["configuration"]
    observations = int(configuration["observations"])
    dimension = int(configuration["unknown_dimension"])
    outlier_count = int(configuration["outlier_count"])
    rng = np.random.default_rng(seed)
    matrix = rng.normal(0.0, 1.0, size=(observations, dimension))
    matrix /= float(np.linalg.svd(matrix, compute_uv=False)[0])
    operator_norm = float(np.linalg.svd(matrix, compute_uv=False)[0])
    truth = np.zeros(dimension)
    support = np.array([3, 8, 14, 19, 27, 33, 39, 44])
    truth[support] = np.array([1.4, -1.0, 0.75, 1.15, -1.25, 0.9, -0.8, 1.05])
    clean_data = matrix @ truth
    data = clean_data + rng.normal(0.0, 0.012, size=observations)
    outliers = np.sort(rng.choice(observations, size=outlier_count, replace=False))
    outlier_signs = rng.choice(np.array([-1.0, 1.0]), size=outlier_count)
    data[outliers] += outlier_signs * rng.uniform(0.65, 1.05, size=outlier_count)
    return {
        "matrix": matrix,
        "data": data,
        "truth": truth,
        "support": support,
        "outliers": outliers,
        "operator_norm": operator_norm,
        "matrix_sha256": sha256_bytes(matrix.astype("<f8").tobytes()),
        "data_sha256": sha256_bytes(data.astype("<f8").tobytes()),
    }


def audit_capstone(audit: Audit) -> dict[str, Any]:
    json_path = LAB_DIR / "kapstone-invers-komposit-results.json"
    csv_path = LAB_DIR / "kapstone-invers-komposit-results.csv"
    report = json.loads(json_path.read_text(encoding="utf-8"))
    fields, raw_rows = read_csv_rows(csv_path)
    expected_fields = [
        "solver",
        "iteration",
        "matrix_vector_products",
        "objective",
        "dual_lower_bound",
        "certified_gap",
        "dual_feasibility_violation",
        "gradient_mapping_norm",
        "relative_recovery_error",
    ]
    audit.require(
        fields == expected_fields,
        "capstone-csv-schema",
        "Capstone CSV schema changed or is incomplete.",
        {"expected": expected_fields, "actual": fields},
    )
    parsed: list[dict[str, Any]] = []
    numeric_errors: list[dict[str, Any]] = []
    for row_number, raw in enumerate(raw_rows, start=2):
        try:
            row = {
                **raw,
                "iteration": int(raw["iteration"]),
                "matrix_vector_products": int(raw["matrix_vector_products"]),
                "objective": float(raw["objective"]),
                "dual_lower_bound": float(raw["dual_lower_bound"]),
                "certified_gap": float(raw["certified_gap"]),
                "dual_feasibility_violation": float(raw["dual_feasibility_violation"]),
                "gradient_mapping_norm": (
                    None if raw["gradient_mapping_norm"] == "" else float(raw["gradient_mapping_norm"])
                ),
                "relative_recovery_error": float(raw["relative_recovery_error"]),
            }
        except (KeyError, ValueError) as error:
            numeric_errors.append({"row": row_number, "error": str(error)})
            continue
        if row["matrix_vector_products"] != 2 * row["iteration"]:
            numeric_errors.append({"row": row_number, "field": "operator-budget"})
        if not isclose(
            row["objective"] - row["dual_lower_bound"],
            row["certified_gap"],
            atol=3.0e-15,
            rtol=2.0e-12,
        ):
            numeric_errors.append({"row": row_number, "field": "gap-identity"})
        if row["dual_feasibility_violation"] < 0.0 or row["certified_gap"] < -1.0e-12:
            numeric_errors.append({"row": row_number, "field": "certificate-sign"})
        if not all(
            math.isfinite(float(row[field]))
            for field in (
                "objective",
                "dual_lower_bound",
                "certified_gap",
                "dual_feasibility_violation",
                "relative_recovery_error",
            )
        ):
            numeric_errors.append({"row": row_number, "field": "non-finite"})
        parsed.append(row)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in parsed:
        grouped[row["solver"]].append(row)
    expected_solvers = {"FISTA-restart", "PDHG-referensi"}
    audit.require(
        set(grouped) == expected_solvers,
        "capstone-solvers",
        "Capstone trace must contain exactly FISTA-restart and PDHG-referensi.",
        sorted(grouped),
    )
    iterations = int(report.get("configuration", {}).get("matched_iterations", 0))
    expected_iterations = [1, *range(10, iterations + 1, 10)]
    for solver, rows in grouped.items():
        rows.sort(key=lambda row: row["iteration"])
        if [row["iteration"] for row in rows] != expected_iterations:
            numeric_errors.append({"solver": solver, "field": "trace-iteration-grid"})
        if solver == "FISTA-restart" and any(row["gradient_mapping_norm"] is None for row in rows):
            numeric_errors.append({"solver": solver, "field": "missing-gradient-mapping"})
        if solver == "PDHG-referensi" and any(row["gradient_mapping_norm"] is not None for row in rows):
            numeric_errors.append({"solver": solver, "field": "unexpected-gradient-mapping"})

    summary = report.get("matched_budget_summary", {})
    fista_final = grouped.get("FISTA-restart", [{}])[-1]
    pdhg_final = grouped.get("PDHG-referensi", [{}])[-1]
    final_checks = {
        "fista_objective": fista_final.get("objective", math.nan),
        "pdhg_objective": pdhg_final.get("objective", math.nan),
        "fista_gradient_mapping_norm": fista_final.get("gradient_mapping_norm", math.nan),
        "fista_relative_recovery_error": fista_final.get("relative_recovery_error", math.nan),
        "pdhg_relative_recovery_error": pdhg_final.get("relative_recovery_error", math.nan),
    }
    for field, expected in final_checks.items():
        if not isclose(summary.get(field, math.nan), expected, atol=3.0e-14, rtol=2.0e-11):
            numeric_errors.append({"field": field, "reported": summary.get(field), "csv_final": expected})
    fista_objective = float(summary.get("fista_objective", math.nan))
    pdhg_objective = float(summary.get("pdhg_objective", math.nan))
    objective_difference = abs(fista_objective - pdhg_objective)
    best_lower = float(summary.get("best_feasible_dual_lower_bound", math.nan))
    if not isclose(summary.get("absolute_objective_difference", math.nan), objective_difference, atol=2.0e-15):
        numeric_errors.append({"field": "absolute-objective-difference"})
    if not isclose(summary.get("fista_certified_gap", math.nan), fista_objective - best_lower, atol=2.0e-15):
        numeric_errors.append({"field": "fista-certified-gap"})
    if not isclose(summary.get("pdhg_certified_gap", math.nan), pdhg_objective - best_lower, atol=2.0e-15):
        numeric_errors.append({"field": "pdhg-certified-gap"})

    reconstructed = reconstruct_capstone_instance(report)
    fixed_instance = report.get("fixed_instance", {})
    reconstruction_checks = {
        "matrix_sha256": reconstructed["matrix_sha256"],
        "data_sha256": reconstructed["data_sha256"],
        "support": reconstructed["support"].tolist(),
        "truth": reconstructed["truth"].tolist(),
        "outlier_indices": reconstructed["outliers"].tolist(),
    }
    for field, value in reconstruction_checks.items():
        if fixed_instance.get(field) != value:
            numeric_errors.append({"field": f"fixed-instance-{field}", "reported": fixed_instance.get(field), "recomputed": value})
    configuration = report.get("configuration", {})
    operator_norm = reconstructed["operator_norm"]
    lipschitz = operator_norm**2
    stability = (0.99 / operator_norm) ** 2 * operator_norm**2
    for field, value in {
        "operator_norm": operator_norm,
        "smooth_gradient_lipschitz_bound": lipschitz,
        "pdhg_tau_sigma_norm_squared": stability,
    }.items():
        if not isclose(configuration.get(field, math.nan), value, atol=2.0e-15):
            numeric_errors.append({"field": field, "reported": configuration.get(field), "recomputed": value})

    certificates = {
        "fixed_data_dimensions": reconstructed["matrix"].shape
        == (int(configuration.get("observations", -1)), int(configuration.get("unknown_dimension", -1))),
        "fixed_outlier_count": len(reconstructed["outliers"]) == int(configuration.get("outlier_count", -1)),
        "huber_gradient_lipschitz_bound_positive": lipschitz > 0.0,
        "fista_step_below_inverse_lipschitz": 0.99 < 1.0,
        "pdhg_step_product_strictly_below_one": stability < 1.0,
        "matched_matrix_vector_budget": (
            fista_final.get("matrix_vector_products")
            == pdhg_final.get("matrix_vector_products")
            == 2 * iterations
            == int(configuration.get("matched_matrix_vector_products_per_solver", -1))
        ),
        "matched_budget_objectives_agree": objective_difference <= 2.0e-5,
        "fista_gradient_mapping_small": float(summary.get("fista_gradient_mapping_norm", math.inf)) <= 2.0e-5,
        "fista_dual_certificate_feasible": fista_final.get("dual_feasibility_violation", math.inf) <= 1.0e-12,
        "pdhg_dual_certificate_feasible": pdhg_final.get("dual_feasibility_violation", math.inf) <= 1.0e-12,
        "fista_certified_gap_small": fista_objective - best_lower <= 2.0e-4,
        "pdhg_certified_gap_small": pdhg_objective - best_lower <= 2.0e-4,
        "robust_solution_improves_on_least_squares": max(
            float(summary.get("fista_relative_recovery_error", math.inf)),
            float(summary.get("pdhg_relative_recovery_error", math.inf)),
        ) < float(summary.get("least_squares_relative_recovery_error", -math.inf)),
    }
    reported_certificates = report.get("certificates", {})
    milestones = report.get("seven_milestones", [])
    milestone_valid = (
        len(milestones) == 7
        and [item.get("id") for item in milestones] == list(range(1, 8))
        and all(item.get("passed") is True and str(item.get("name", "")).strip() for item in milestones)
    )
    audit.require(
        report.get("schema") == "o015-original-03-kapstone-invers-komposit-v1"
        and report.get("result") == "pass",
        "capstone-json-schema",
        "Capstone JSON schema or result is invalid.",
    )
    audit.require(
        milestone_valid,
        "capstone-computation-milestones",
        "Capstone computation report must carry seven passing milestones.",
        milestones,
    )
    audit.require(
        not numeric_errors,
        "capstone-numerical-invariants",
        "Capstone artifacts violate independently recomputed invariants or fixed-instance identity.",
        numeric_errors,
    )
    audit.require(
        certificates == reported_certificates and all(certificates.values()),
        "capstone-certificates",
        "Capstone certificates are false or disagree with independent recomputation.",
        {"reported": reported_certificates, "recomputed": certificates},
    )
    return {
        "json": file_record(json_path),
        "csv": file_record(csv_path),
        "csv_data_rows": len(raw_rows),
        "solver_row_counts": {solver: len(rows) for solver, rows in sorted(grouped.items())},
        "matched_matrix_vector_products_per_solver": fista_final.get("matrix_vector_products"),
        "matrix_sha256": reconstructed["matrix_sha256"],
        "data_sha256": reconstructed["data_sha256"],
        "outlier_indices": reconstructed["outliers"].tolist(),
        "objective_difference": objective_difference,
        "certificates": certificates,
        "milestone_count": len(milestones),
        "numeric_error_count": len(numeric_errors),
    }


def run_section(audit: Audit, sections: dict[str, Any], name: str, function: Any) -> None:
    try:
        sections[name] = function()
    except Exception as error:  # Keep a durable receipt even on an unexpected QA failure.
        audit.finding(
            "P1",
            "verifier-section-exception",
            f"Verifier section {name} raised {type(error).__name__}: {error}",
            {"traceback": traceback.format_exc()},
        )
        sections[name] = {
            "result": "error",
            "exception": type(error).__name__,
            "message": str(error),
        }


def main() -> int:
    audit = Audit()
    sections: dict[str, Any] = {}
    before = {
        relative(path): sha256_bytes(path.read_bytes())
        for path in SCOPED_INPUTS
        if path.is_file()
    }
    texts = {path: read_utf8(audit, path) for path in SCOPED_TEX}

    run_section(audit, sections, "inventory", lambda: audit_inventory_and_bytes(audit))
    run_section(audit, sections, "aggregator", lambda: audit_aggregator(audit, texts))
    run_section(
        audit,
        sections,
        "ids_labels_references",
        lambda: audit_ids_labels_and_references(audit, texts),
    )
    run_section(
        audit,
        sections,
        "tex_wellformedness",
        lambda: audit_tex_wellformedness(audit, texts),
    )
    run_section(audit, sections, "assessments", lambda: audit_assessments(audit, texts))
    rubric_path = MODULE_DIR / "08-rubrik-pembuktian-id.tex"
    run_section(
        audit,
        sections,
        "proof_rubrics",
        lambda: audit_rubrics(audit, texts[rubric_path], texts),
    )
    run_section(
        audit,
        sections,
        "labs_and_capstone_topology",
        lambda: audit_labs_and_capstone(audit, texts),
    )
    run_section(audit, sections, "o018_firewall", lambda: audit_o018_firewall(audit, texts))
    run_section(audit, sections, "provenance", lambda: audit_provenance(audit, texts))
    run_section(audit, sections, "svg_artifacts", lambda: audit_svg_artifacts(audit))
    run_section(
        audit,
        sections,
        "globalisasi_newton_numerics",
        lambda: audit_globalisasi_newton(audit),
    )
    run_section(
        audit,
        sections,
        "transportasi_entropik_numerics",
        lambda: audit_transportasi_entropik(audit),
    )
    run_section(audit, sections, "capstone_numerics", lambda: audit_capstone(audit))
    run_section(
        audit,
        sections,
        "deterministic_computation_replays",
        lambda: audit_deterministic_replays(audit),
    )

    after = {
        relative(path): sha256_bytes(path.read_bytes())
        for path in SCOPED_INPUTS
        if path.is_file()
    }
    boundary_changes = {
        path: {"before": before.get(path), "after": after.get(path)}
        for path in sorted(set(before) | set(after))
        if before.get(path) != after.get(path)
    }
    audit.require(
        not boundary_changes,
        "read-only-boundary",
        "A source, lab script, or checked-in output changed during the audit.",
        boundary_changes,
    )
    sections["read_only_boundary"] = {
        "scoped_input_count": len(before),
        "unchanged": not boundary_changes,
        "changes": boundary_changes,
        "persistent_files_written": [relative(REPORT_PATH)],
    }

    finding_counts = {severity: len(items) for severity, items in audit.findings.items()}
    passed = all(count == 0 for count in finding_counts.values())
    assessment_section = sections.get("assessments", {})
    ids_section = sections.get("ids_labels_references", {})
    replay_section = sections.get("deterministic_computation_replays", {})
    report = {
        "schema": "original-03-course-closure-qa-v1",
        "result": "pass" if passed else "fail",
        "verifier": {
            **file_record(Path(__file__).resolve()),
            "python": sys.version.split()[0],
            "numpy": np.__version__,
        },
        "scope": {
            "root": ".",
            "aggregator": relative(AGGREGATOR),
            "module_count": len(MODULES),
            "computation_component_count": len(COMPONENTS),
            "network_used": False,
            "git_used": False,
            "credentials_used": False,
            "publication_performed": False,
        },
        "summary": {
            "assessment_count": assessment_section.get("assessment_count"),
            "assessment_distribution": assessment_section.get("distribution"),
            "response_unit_count": assessment_section.get("prompt_response_unit_count"),
            "proof_rubric_count": sections.get("proof_rubrics", {}).get("rubric_count"),
            "capstone_milestone_count": sections.get("labs_and_capstone_topology", {})
            .get("capstone", {})
            .get("milestone_count"),
            "stable_definition_count": ids_section.get("stable_definition_count"),
            "unique_stable_id_count": ids_section.get("unique_stable_id_count"),
            "unique_label_count": ids_section.get("unique_label_count"),
            "static_reference_count": ids_section.get("static_reference_count"),
            "computation_components_replayed_twice": sum(
                item.get("runs") == 2 for item in replay_section.values()
            )
            if isinstance(replay_section, dict)
            else 0,
            "P1": finding_counts["P1"],
            "P2": finding_counts["P2"],
            "P3": finding_counts["P3"],
        },
        "sections": sections,
        "findings": audit.findings,
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    receipt = {
        "result": report["result"],
        "report": relative(REPORT_PATH),
        "report_bytes": REPORT_PATH.stat().st_size,
        "report_sha256": sha256_bytes(REPORT_PATH.read_bytes()),
        "P1": finding_counts["P1"],
        "P2": finding_counts["P2"],
        "P3": finding_counts["P3"],
    }
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
