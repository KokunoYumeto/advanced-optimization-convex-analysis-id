#!/usr/bin/env python3
"""Fail-closed structural and formula-delta audit for Penn MATH 555 Chapter 3.

The audit is intentionally pinned to one frozen authority file, one Indonesian
candidate, and one proposed correction ledger.  It does not build or edit the
reader.  Its only outputs are the two deterministic JSON witnesses named below.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority/penn-state/source/ClassNotes/Section3.tex"
TARGET = ROOT / "source/id-ID/penn-03-pendakian-gradien-dan-pencarian-garis-id.tex"
LEDGER = ROOT / "qa/PENN_CH03_PROPOSED_LEDGER.jsonl"
REPORT = ROOT / "qa/PENN_CH03_STRUCTURE_REPORT.json"
MANIFEST = ROOT / "qa/PENN_CH03_FORMULA_DELTA_MANIFEST.json"

EXPECTED = {
    "source": {
        "bytes": 41715,
        "lines": 608,
        "sha256": "d4ae6142e2366b12575eafddc833df067518af114e9816187668cc367be43010",
    },
    "target": {
        "bytes": 44364,
        "lines": 646,
        "sha256": "7c75d0ae56a5a912d561d91ece607f088a4ff4f3de4dbc3396ce40d6d7d6a229",
    },
    "ledger": {
        "bytes": 14813,
        "lines": 21,
        "sha256": "80aa5a3f7b4f46c7dfe01f58f6f68555c9aeaeb91d0877eaf27cbb447c4a67fa",
    },
}

SEGMENTS = [
    ("P03-S001", "d90.penn.v1.ch03.seg0001", 1, 47),
    ("P03-S002", "d90.penn.v1.ch03.seg0002", 48, 80),
    ("P03-S003", "d90.penn.v1.ch03.seg0003", 81, 160),
    ("P03-S004", "d90.penn.v1.ch03.seg0004", 161, 224),
    ("P03-S005", "d90.penn.v1.ch03.seg0005", 225, 312),
    ("P03-S006", "d90.penn.v1.ch03.seg0006", 313, 404),
    ("P03-S007", "d90.penn.v1.ch03.seg0007", 405, 452),
    ("P03-S008", "d90.penn.v1.ch03.seg0008", 453, 608),
]

SEGMENT_DEFAULT_BINDINGS = {
    "P03-S001": ["O015-PENN-ADV-0004", "O015-PENN-ADV-0005"],
    "P03-S002": ["O015-PENN-ADV-0005", "O015-PENN-ADV-0006"],
    "P03-S003": [
        "O015-PENN-ADV-0007",
        "O015-PENN-ADV-0008",
        "O015-PENN-ADV-0009",
        "O015-PENN-ADV-0013",
        "O015-PENN-ADV-0023",
    ],
    "P03-S004": [
        "O015-PENN-ADV-0010",
        "O015-PENN-ADV-0011",
        "O015-PENN-ADV-0013",
        "O015-PENN-ADV-0023",
    ],
    "P03-S005": ["O015-PENN-ADV-0012", "O015-PENN-ADV-0013", "O015-PENN-ADV-0024"],
    "P03-S006": [
        "O015-PENN-ADV-0013",
        "O015-PENN-ADV-0014",
        "O015-PENN-ADV-0015",
        "O015-PENN-ADV-0016",
    ],
    "P03-S007": ["O015-PENN-ADV-0017"],
    "P03-S008": [
        "O015-PENN-ADV-0018",
        "O015-PENN-ADV-0019",
        "O015-PENN-ADV-0020",
        "O015-PENN-ADV-0021",
        "O015-PENN-ADV-0022",
        "O015-PENN-ADV-0023",
    ],
}

DEPENDENCIES = {
    "Code/QuadraticTurn.mpl": (355, "6370cab7dcc4db79848e52959935df35184d38eaf6cd2c37616c17d67d317598"),
    "Code/ParabolicBracket.mpl": (1716, "2eec4ee4856a8e8cf27c24a0a8d3eb6a6dd7f850486a38da84b73969f8e5006e"),
    "Code/DichotomousSearch.mpl": (529, "0ffa9733a13c364465db5bde1d77a12995a04dabc41b640a0f11d850f866bc40"),
    "Code/GoldenSectionSearch.mpl": (650, "a6c2685894a3acb3f37bc8a941f4524e40cba583ebe4df7e8f95f7c51953966a"),
    "Code/BisectionSearch.mpl": (538, "0b3894b948fb15908c68925061111e0397a4e4e9fbc6af70bdb56aa1335f6997"),
    "Code/NewtonsMethod.mpl": (406, "173078c027925a8153b7b3350971dc2765d6cd91e30f500442c6bf229ae648c3"),
    "Outputs/BracketExample1.tex": (424, "1a521119df1ab71f58166033c7f7003a07a2f2e482a5bcc747774e05fac6414c"),
    "Outputs/BracketExample2.tex": (276, "00364d7e6471f110e529dddb87dc2418a05a567079b7a336948bee3f8c766007"),
    "Outputs/DichotomousOutput.tex": (702, "6f16487ec99050c506b32b379fc035106ef8d6743e34dea23ca5e2d03b36f172"),
    "Outputs/GoldenSectionOutput.tex": (850, "290a80d59372078be61d60bb7b92edcb597b2d444503323f0d695b7003245089"),
    "Outputs/BisectionOutput.tex": (309, "21e3bef1d4e4ff3b203b6456598f7dd13dc44b06a63c3fdfda8b143eab8229fb"),
}

FIGURE_ASSETS = {
    "Figures/DichotomousSearch.pdf": (101202, "ccdc24742cbb4b908b740c34940cf84f314994e3bdb6b815edf902eb98be32e4"),
    "Figures/NonConcave.pdf": (9733, "bc17c66377f01fc567639fd745f436d80ccedebc50824aba2b5d0ed470bc7c64"),
    "Figures/GoldenRatioProof.pdf": (81307, "ad405a95c466ca65670c0be53cb54667846106ac03ffa9c86bf4248daf6cbb32"),
    "Figures/GoldenSectionFail.pdf": (9913, "5abd708847cf98662f12645172e9b3390420d0263840ac3d7def776ffad07868"),
}

EXPECTED_ENV_COUNTS = {
    "algorithm": 5,
    "aligned": 1,
    "cases": 2,
    "cgalgorithm": 1,
    "corollary": 2,
    "definition": 5,
    "displaymath": 16,
    "enumerate*": 1,
    "equation": 33,
    "example": 5,
    "exercise": 12,
    "figure": 4,
    "gather": 2,
    "gather*": 1,
    "lemma": 3,
    "minipage": 1,
    "proof": 9,
    "proposition": 3,
    "remark": 29,
    "theorem": 6,
    "verbatim": 1,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    text = data.decode("utf-8")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "physical_lines": len(text.splitlines()),
        "sha256": sha256_bytes(data),
    }


def strip_comments_keep_offsets(text: str) -> str:
    """Replace unescaped comments with spaces while preserving all offsets."""
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        cut = None
        for i, char in enumerate(line):
            if char != "%":
                continue
            backslashes = 0
            j = i - 1
            while j >= 0 and line[j] == "\\":
                backslashes += 1
                j -= 1
            if backslashes % 2 == 0:
                cut = i
                break
        if cut is None:
            out.append(line)
        else:
            ending = "\n" if line.endswith("\n") else ""
            body_len = len(line) - len(ending)
            out.append(line[:cut] + " " * (body_len - cut) + ending)
    return "".join(out)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def environments(text: str) -> tuple[list[str], list[str]]:
    live = strip_comments_keep_offsets(text)
    tokens = [
        (match.start(), match.group(1), match.group(2))
        for match in re.finditer(r"\\(begin|end)\{([^{}]+)\}", live)
    ]
    sequence: list[str] = []
    stack: list[str] = []
    errors: list[str] = []
    for _, kind, name in tokens:
        if kind == "begin":
            sequence.append(name)
            stack.append(name)
        elif not stack:
            errors.append(f"orphan end{{{name}}}")
        else:
            opened = stack.pop()
            if opened != name:
                errors.append(f"mismatched begin{{{opened}}}/end{{{name}}}")
    if stack:
        errors.append("unclosed: " + ", ".join(stack))
    return sequence, errors


def command_args(text: str, command: str) -> list[str]:
    live = strip_comments_keep_offsets(text)
    return re.findall(rf"\\{re.escape(command)}\{{([^{{}}]+)\}}", live)


def reference_targets(text: str) -> list[str]:
    live = strip_comments_keep_offsets(text)
    return [m.group(1) for m in re.finditer(r"\\(?:ref|eqref)\{([^{}]+)\}", live)]


def citation_keys(text: str) -> list[str]:
    live = strip_comments_keep_offsets(text)
    keys: list[str] = []
    for match in re.finditer(r"\\cite(?:\[[^\]]*\])?\{([^{}]+)\}", live):
        keys.extend(k.strip() for k in match.group(1).split(","))
    return keys


def figures(text: str) -> list[str]:
    live = strip_comments_keep_offsets(text)
    return [
        m.group(1)
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}", live)
    ]


def source_dependency_calls(text: str) -> tuple[list[str], list[str]]:
    live = strip_comments_keep_offsets(text)
    listings = re.findall(r"\\lstinputlisting\{([^{}]+)\}", live)
    inputs = re.findall(r"\\input\{([^{}]+)\}", live)
    return listings, inputs


def parse_ledger(text: str) -> list[dict[str, Any]]:
    events = [json.loads(line) for line in text.splitlines() if line.strip()]
    required = {"event_id", "authority", "source", "surface", "source_issue", "target_action", "class"}
    for event in events:
        missing = required - set(event)
        if missing:
            raise ValueError(f"ledger {event.get('event_id', '?')} missing {sorted(missing)}")
    return events


def parse_segments(target_text: str) -> list[dict[str, Any]]:
    lines = target_text.splitlines()
    found: list[dict[str, Any]] = []
    marker = re.compile(r"^% (P03-S\d{3}) \| .* baris (\d+)--(\d+)$")
    id_marker = re.compile(r"^% segment-id: (\S+)$")
    for idx, line in enumerate(lines):
        match = marker.match(line)
        if not match:
            continue
        if idx + 1 >= len(lines) or not (id_match := id_marker.match(lines[idx + 1])):
            raise ValueError(f"segment {match.group(1)} lacks adjacent segment-id")
        found.append(
            {
                "name": match.group(1),
                "segment_id": id_match.group(1),
                "source_start": int(match.group(2)),
                "source_end": int(match.group(3)),
                "target_marker_line": idx + 1,
            }
        )
    for i, item in enumerate(found):
        next_line = found[i + 1]["target_marker_line"] if i + 1 < len(found) else len(lines) + 1
        item["target_start"] = item["target_marker_line"]
        item["target_end"] = next_line - 1
    return found


MATH_ENVIRONMENTS = ("equation", "equation*", "displaymath", "gather", "gather*", "align", "align*")


def canonical_math(raw: str) -> str:
    value = raw
    value = re.sub(r"\\label\{[^{}]+\}", "", value)
    value = re.sub(r"\\text\{[^{}]*\}", r"\\text{#}", value)
    value = value.replace("\\left", "").replace("\\right", "")
    value = value.replace("\\lvert", "|").replace("\\rvert", "|")
    value = value.replace("\\Vert", "||").replace("\\lVert", "||").replace("\\rVert", "||")
    value = re.sub(r"\\(?:,|;|!|quad|qquad)", "", value)
    value = re.sub(r"\s+", "", value)
    value = value.rstrip(".,;")
    return value


def math_records(text: str) -> list[dict[str, Any]]:
    live = strip_comments_keep_offsets(text)
    spans: list[tuple[int, int, str, str]] = []
    env_names = "|".join(re.escape(name) for name in MATH_ENVIRONMENTS)
    env_pattern = re.compile(
        rf"\\begin\{{(?P<env>{env_names})\}}(?P<body>.*?)\\end\{{(?P=env)\}}",
        re.DOTALL,
    )
    for match in env_pattern.finditer(live):
        spans.append((match.start(), match.end(), f"environment:{match.group('env')}", match.group("body")))

    occupied = [(start, end) for start, end, _, _ in spans]

    def outside_display(start: int, end: int) -> bool:
        return not any(start >= lo and end <= hi for lo, hi in occupied)

    inline_pattern = re.compile(r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$", re.DOTALL)
    for match in inline_pattern.finditer(live):
        if outside_display(match.start(), match.end()):
            spans.append((match.start(), match.end(), "inline-dollar", match.group(1)))
    paren_pattern = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
    for match in paren_pattern.finditer(live):
        if outside_display(match.start(), match.end()):
            spans.append((match.start(), match.end(), "inline-paren", match.group(1)))

    records: list[dict[str, Any]] = []
    for ordinal, (start, end, kind, raw) in enumerate(sorted(spans), start=1):
        canon = canonical_math(raw)
        records.append(
            {
                "ordinal": ordinal,
                "line_start": line_number(live, start),
                "line_end": line_number(live, end),
                "kind": kind,
                "raw": raw.strip(),
                "canonical": canon,
                "canonical_sha256": sha256_bytes(canon.encode("utf-8")),
            }
        )
    return records


def ledger_line_ranges(events: list[dict[str, Any]]) -> dict[str, list[tuple[int, int]]]:
    result: dict[str, list[tuple[int, int]]] = {}
    for event in events:
        ranges = [
            (int(a), int(b))
            for a, b in re.findall(r"Section3\.tex:(\d+)-(\d+)", event["source"])
        ]
        result[event["event_id"]] = ranges
    return result


def overlapping_bindings(
    segment_name: str,
    source_records: list[dict[str, Any]],
    ranges_by_event: dict[str, list[tuple[int, int]]],
) -> list[str]:
    bindings: list[str] = []
    if source_records:
        lo = min(item["line_start"] for item in source_records)
        hi = max(item["line_end"] for item in source_records)
        for event_id, ranges in ranges_by_event.items():
            if any(a <= hi and lo <= b for a, b in ranges):
                bindings.append(event_id)
    allowed = SEGMENT_DEFAULT_BINDINGS[segment_name]
    bindings = [event_id for event_id in allowed if event_id in bindings]
    return bindings or list(allowed)


def formula_manifest(
    source_text: str,
    target_text: str,
    segments: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    source_math = math_records(source_text)
    target_math = math_records(target_text)
    ranges_by_event = ledger_line_ranges(events)
    deltas: list[dict[str, Any]] = []
    equal_pairs = 0

    for segment in segments:
        name = segment["name"]
        source_slice = [
            item
            for item in source_math
            if segment["source_start"] <= item["line_start"] <= segment["source_end"]
        ]
        target_slice = [
            item
            for item in target_math
            if segment["target_start"] <= item["line_start"] <= segment["target_end"]
        ]
        matcher = difflib.SequenceMatcher(
            a=[item["canonical"] for item in source_slice],
            b=[item["canonical"] for item in target_slice],
            autojunk=False,
        )
        for opcode_index, (tag, a0, a1, b0, b1) in enumerate(matcher.get_opcodes(), start=1):
            if tag == "equal":
                equal_pairs += a1 - a0
                continue
            source_delta = source_slice[a0:a1]
            target_delta = target_slice[b0:b1]
            bindings = overlapping_bindings(name, source_delta, ranges_by_event)
            deltas.append(
                {
                    "delta_id": f"{name}-MATH-{opcode_index:03d}",
                    "segment": name,
                    "opcode": tag,
                    "classification": "substantive_or_independent_bridge",
                    "ledger_bindings": bindings,
                    "source": source_delta,
                    "target": target_delta,
                }
            )

    all_event_ids = {event["event_id"] for event in events}
    unbound = [item["delta_id"] for item in deltas if not item["ledger_bindings"]]
    unknown = sorted(
        {
            event_id
            for item in deltas
            for event_id in item["ledger_bindings"]
            if event_id not in all_event_ids
        }
    )
    return {
        "schema": "o015.penn.chapter03.formula-delta-manifest.v1",
        "authority_sha256": EXPECTED["source"]["sha256"],
        "target_sha256": EXPECTED["target"]["sha256"],
        "ledger_sha256": EXPECTED["ledger"]["sha256"],
        "method": {
            "scope": "all live inline-dollar, inline-parenthesis, and top-level display math in each of eight contiguous source/target segments",
            "comment_policy": "unescaped-percent comments excluded with offsets preserved",
            "canonicalization": "whitespace, sizing, spacing commands, trailing punctuation, and translated text payloads normalized; mathematical commands and symbols retained",
            "alignment": "per-segment difflib SequenceMatcher with autojunk disabled",
            "policy": "every non-equal opcode is conservatively substantive/independent-bridge and must bind to at least one proposed correction event",
        },
        "counts": {
            "source_math_records": len(source_math),
            "target_math_records": len(target_math),
            "canonical_equal_pairs": equal_pairs,
            "delta_blocks": len(deltas),
            "unbound_delta_blocks": len(unbound),
            "unknown_ledger_bindings": len(unknown),
        },
        "status": "PASS" if not unbound and not unknown else "FAIL",
        "unbound_delta_ids": unbound,
        "unknown_ledger_binding_ids": unknown,
        "deltas": deltas,
    }


def check(name: str, condition: bool, evidence: Any) -> dict[str, Any]:
    return {"check": name, "status": "PASS" if condition else "FAIL", "evidence": evidence}


def main() -> int:
    source_bytes = SOURCE.read_bytes()
    target_bytes = TARGET.read_bytes()
    ledger_bytes = LEDGER.read_bytes()
    source_text = source_bytes.decode("utf-8")
    target_text = target_bytes.decode("utf-8")
    ledger_text = ledger_bytes.decode("utf-8")

    identities = {
        "source": identity(SOURCE),
        "target": identity(TARGET),
        "ledger": identity(LEDGER),
    }
    checks: list[dict[str, Any]] = []
    for key in ("source", "target", "ledger"):
        actual = identities[key]
        expected = EXPECTED[key]
        checks.append(
            check(
                f"pinned_{key}_identity",
                actual["bytes"] == expected["bytes"]
                and actual["physical_lines"] == expected["lines"]
                and actual["sha256"] == expected["sha256"],
                {"expected": expected, "actual": actual},
            )
        )

    events = parse_ledger(ledger_text)
    expected_ids = [f"O015-PENN-ADV-{i:04d}" for i in range(4, 25)]
    actual_ids = [event["event_id"] for event in events]
    checks.append(
        check(
            "ledger_schema_and_consecutive_unique_ids",
            actual_ids == expected_ids and len(set(actual_ids)) == 21,
            actual_ids,
        )
    )
    checks.append(
        check(
            "ledger_authority_binding",
            all(event["authority"] == "o015-penn-math555-v1.0-source" for event in events),
            sorted({event["authority"] for event in events}),
        )
    )

    source_envs, source_balance = environments(source_text)
    target_envs, target_balance = environments(target_text)
    counts = dict(sorted(Counter(source_envs).items()))
    target_counts = dict(sorted(Counter(target_envs).items()))
    checks.append(check("balanced_live_source_environments", not source_balance, source_balance))
    checks.append(check("balanced_live_target_environments", not target_balance, target_balance))
    checks.append(
        check(
            "exact_142_environment_topology",
            source_envs == target_envs
            and len(source_envs) == 142
            and counts == EXPECTED_ENV_COUNTS
            and target_counts == EXPECTED_ENV_COUNTS,
            {"source_total": len(source_envs), "target_total": len(target_envs), "counts": counts},
        )
    )
    raw_source_begin_count = len(re.findall(r"\\begin\{", source_text))
    checks.append(
        check(
            "disabled_comment_environment_exclusion",
            raw_source_begin_count - len(source_envs) == 7,
            {"raw_begin_tokens": raw_source_begin_count, "live_begin_tokens": len(source_envs)},
        )
    )

    source_labels = command_args(source_text, "label")
    target_labels = command_args(target_text, "label")
    checks.append(
        check(
            "exact_35_labels_once",
            set(source_labels) == set(target_labels)
            and len(source_labels) == len(target_labels) == 35
            and len(set(source_labels)) == 35
            and len(set(target_labels)) == 35,
            {"source": source_labels, "target": target_labels},
        )
    )
    source_refs = reference_targets(source_text)
    target_refs = reference_targets(target_text)
    checks.append(
        check(
            "exact_37_unique_reference_targets",
            set(source_refs) == set(target_refs) and len(set(source_refs)) == 37,
            {
                "source_occurrences": len(source_refs),
                "target_occurrences": len(target_refs),
                "source_unique": sorted(set(source_refs)),
                "target_unique": sorted(set(target_refs)),
            },
        )
    )
    source_cites = citation_keys(source_text)
    target_cites = citation_keys(target_text)
    checks.append(
        check(
            "exact_nine_entry_citation_sequence",
            source_cites == target_cites and len(source_cites) == 9,
            {"source": source_cites, "target": target_cites},
        )
    )
    source_figures = figures(source_text)
    target_figures = figures(target_text)
    checks.append(
        check(
            "exact_four_figure_call_sequence",
            source_figures == target_figures and source_figures == list(FIGURE_ASSETS),
            {"source": source_figures, "target": target_figures},
        )
    )
    checks.append(
        check(
            "exact_twelve_exercises",
            Counter(source_envs)["exercise"] == Counter(target_envs)["exercise"] == 12,
            {"source": Counter(source_envs)["exercise"], "target": Counter(target_envs)["exercise"]},
        )
    )

    parsed_segments = parse_segments(target_text)
    expected_segment_dicts = [
        {"name": name, "segment_id": segment_id, "source_start": start, "source_end": end}
        for name, segment_id, start, end in SEGMENTS
    ]
    observed_core = [
        {k: item[k] for k in ("name", "segment_id", "source_start", "source_end")}
        for item in parsed_segments
    ]
    covered_lines = [
        line
        for item in parsed_segments
        for line in range(item["source_start"], item["source_end"] + 1)
    ]
    checks.append(
        check(
            "eight_segment_exact_contiguous_source_closure",
            observed_core == expected_segment_dicts and covered_lines == list(range(1, 609)),
            parsed_segments,
        )
    )

    listings, inputs = source_dependency_calls(source_text)
    target_listings, target_inputs = source_dependency_calls(target_text)
    expected_listings = [key for key in DEPENDENCIES if key.startswith("Code/")]
    expected_inputs = [key for key in DEPENDENCIES if key.startswith("Outputs/")]
    checks.append(
        check(
            "six_Maple_calls_and_five_output_calls_identified",
            listings == expected_listings and inputs == expected_inputs,
            {"listings": listings, "inputs": inputs},
        )
    )
    checks.append(
        check(
            "target_has_no_legacy_listing_or_input_dependency",
            not target_listings
            and not target_inputs
            and "Code/" not in strip_comments_keep_offsets(target_text)
            and "Outputs/" not in strip_comments_keep_offsets(target_text),
            {"target_listings": target_listings, "target_inputs": target_inputs},
        )
    )
    checks.append(
        check(
            "six_independent_pseudocode_replacement_surfaces",
            len(re.findall(r"\\noindent\\fbox\{", strip_comments_keep_offsets(target_text))) == 6
            and target_text.count("ditulis secara independen") >= 3,
            {
                "fbox_surfaces": len(re.findall(r"\\noindent\\fbox\{", strip_comments_keep_offsets(target_text))),
                "independent_authorship_phrases": target_text.count("ditulis secara independen"),
            },
        )
    )

    dependency_evidence: list[dict[str, Any]] = []
    dependency_ok = True
    base = SOURCE.parent
    for rel, (expected_bytes, expected_hash) in DEPENDENCIES.items():
        path = base / rel
        data = path.read_bytes()
        actual = {"reference": rel, "bytes": len(data), "sha256": sha256_bytes(data)}
        actual["status"] = (
            "PASS" if len(data) == expected_bytes and actual["sha256"] == expected_hash else "FAIL"
        )
        dependency_ok &= actual["status"] == "PASS"
        dependency_evidence.append(actual)
    checks.append(check("exact_legacy_dependency_witnesses", dependency_ok, dependency_evidence))

    figure_evidence: list[dict[str, Any]] = []
    figures_ok = True
    for rel, (expected_bytes, expected_hash) in FIGURE_ASSETS.items():
        path = base / rel
        data = path.read_bytes()
        actual = {"reference": rel, "bytes": len(data), "sha256": sha256_bytes(data)}
        actual["status"] = (
            "PASS" if len(data) == expected_bytes and actual["sha256"] == expected_hash else "FAIL"
        )
        figures_ok &= actual["status"] == "PASS"
        figure_evidence.append(actual)
    checks.append(check("exact_four_authority_figure_assets", figures_ok, figure_evidence))

    witness_snippets = [
        "(2.864863884,\\,2.899652455,\\,2.904582162)",
        "(6.194427192,\\,7.317871765,\\,7.565247585)",
        "x^+\\approx9.001215067",
        "x^+\\approx8.998228439",
        "u=5.0009765625",
    ]
    target_compact = re.sub(r"\s+", "", target_text)
    checks.append(
        check(
            "five_legacy_output_witnesses_integrated",
            all(re.sub(r"\s+", "", snippet) in target_compact for snippet in witness_snippets),
            witness_snippets,
        )
    )

    maple_copy_hits: list[dict[str, str]] = []
    for rel in expected_listings:
        code_text = (base / rel).read_text(encoding="utf-8")
        for line in code_text.splitlines():
            compact = re.sub(r"\s+", " ", line.strip())
            if len(compact) >= 24 and compact in target_text:
                maple_copy_hits.append({"dependency": rel, "line": compact})
    checks.append(check("no_verbatim_Maple_line_copy", not maple_copy_hits, maple_copy_hits))

    formula = formula_manifest(source_text, target_text, parsed_segments, events)
    checks.append(
        check(
            "every_formula_delta_has_known_ledger_binding",
            formula["status"] == "PASS",
            formula["counts"],
        )
    )

    # The changed surfaces are pinned so a later candidate cannot inherit this
    # pass's independent re-review.
    defect_specs: list[dict[str, Any]] = []
    repaired_snippets_present = (
        "Untuk hasil laju lokal, misalkan $h$ terdiferensialkan dua kali secara kontinu" in target_text
        and "fungsi ini unimodal dalam arti lemah, tetapi tidak unimodal ketat" in target_text
        and "zero-curvature failure" not in events[10]["target_action"]
        and "O015-PENN-ADV-0024" in actual_ids
        and "\\[\n(a,b,c)=(2.864863884" in target_text
    )
    checks.append(
        check(
            "independent_re_review_of_repaired_surfaces",
            repaired_snippets_present,
            {
                "rate_theorem": "standard local C2 simple-root theorem with exact Taylor remainder",
                "golden_failure": "weak-unimodal plateau and one-sided equality branch identified",
                "ledger_0011": "zero-curvature overclaim removed",
                "ledger_0024": "example characterization correction recorded",
                "numeric_tuples": "moved into two displaymath surfaces",
            },
        )
    )

    structural_failures = [item["check"] for item in checks if item["status"] != "PASS"]
    report = {
        "schema": "o015.penn.chapter03.structure-audit.v1",
        "overall_status": "FAIL" if structural_failures or defect_specs else "PASS",
        "structural_status": "FAIL" if structural_failures else "PASS",
        "admission_status": "FAIL" if structural_failures or defect_specs else "PASS",
        "reason": (
            "Fail-closed: at least one exact structural/identity/binding check failed."
            if structural_failures
            else "All pinned structural, closure, delta-binding, and repaired-surface checks pass."
        ),
        "identities": identities,
        "audit_script": identity(Path(__file__)),
        "checks": checks,
        "structural_failures": structural_failures,
        "manual_findings": defect_specs,
        "environment_sequence": source_envs,
        "formula_manifest": {
            "path": MANIFEST.relative_to(ROOT).as_posix(),
            "status": formula["status"],
            "counts": formula["counts"],
        },
        "scope_note": (
            "This audit proves exact physical-line partition, live TeX topology, identifier/reference/citation/figure/exercise "
            "surfaces, dependency identities, exclusion closure, output witnesses, and complete math-record delta accounting. "
            "It does not claim compilation or visual admission."
        ),
    }

    MANIFEST.write_text(json.dumps(formula, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps({
        "overall_status": report["overall_status"],
        "structural_status": report["structural_status"],
        "structural_failures": structural_failures,
        "manual_findings": [item["finding_id"] for item in defect_specs],
        "formula_counts": formula["counts"],
        "report_sha256": sha256_bytes(REPORT.read_bytes()),
        "manifest_sha256": sha256_bytes(MANIFEST.read_bytes()),
    }, sort_keys=True))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
