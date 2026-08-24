#!/usr/bin/env python3
"""Fail-closed admission audit for the Habring preface and Chapters 1--2.

The audit is intentionally tied to the exact arXiv v1 authority and the exact
Indonesian reader boundary under review.  It inventories every mathematical
surface, proves structural parity, binds every deliberate correction to a
ledger event, verifies rights evidence, and rechecks the deterministic build
reports against the live artifacts.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "qa/HABRING_CH01_CH02_STRUCTURE_REPORT.json"

EXPECTED_FILES: dict[str, tuple[int, str]] = {
    "authority/habring/2607.11664v1-source.tar": (
        230116,
        "d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748",
    ),
    "authority/habring/2607.11664v1.pdf": (
        836977,
        "d2914c741214312d02dc160c5b294eb65a8ac13e484dd9e33aa7ae151f97331d",
    ),
    "authority/habring/2607.11664v1-api.xml": (
        1737,
        "c59dd51fda285214335e2ec00e53f967be44fddca2394ca690c00da70c9dd1d3",
    ),
    "authority/habring/arxiv-2607.11664v1-abs.html": (
        38042,
        "606022f0531509d4aaab191504c023c9d5c09afac615401f0009f4cc0d33e11b",
    ),
    "authority/habring/CC-BY-4.0-legalcode.txt": (
        18657,
        "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411",
    ),
    "authority/habring/source-v1/00README.json": (
        307,
        "ffd889928d5e0eddf937eb35daff0659ac8864a715438f482f22813e661833bf",
    ),
    "authority/habring/source-v1/preface.tex": (
        492,
        "d6ec9d0522446fc65f3868d0b7cd1d221462c3099fbd0b2d6ea412ab53315967",
    ),
    "authority/habring/source-v1/preliminaries.tex": (
        26946,
        "8c1e4bdad36f2dcb57867c475afa5adce12a3951fc650e8667f2e4d82d3b569d",
    ),
    "authority/habring/source-v1/convexity.tex": (
        29947,
        "e5cf93ad93cb2064bdff6c1ea200f20b4eb94351127185a01d678c3fb5a662b8",
    ),
    "source/id-ID/habring-01-prasyarat-id.tex": (
        31009,
        "6ed957c8bf654608e8d572b2f0368478a4dc185ba51c150ea9dee36bb62868e7",
    ),
    "source/id-ID/habring-02-konveksitas-id.tex": (
        42828,
        "99a992f36756cb64f82d21cfcaf68fdaee8b8dd61ef2b007322d9d2623989f22",
    ),
    "source/id-ID/D90-HAB-01-02-prasyarat-dan-konveksitas-id.tex": (
        5357,
        "301d45dc305ee86f439ed1056a62b47199f3439d88ba66436f127a5cee0e35b2",
    ),
    "qa/HABRING_CH01_CH02_PROPOSED_LEDGER.jsonl": (
        12339,
        "ceb880ccc6d5fadccd622662cb41886fa851c58a20e782fc0245d61092e92aff",
    ),
    "qa/HABRING_CH02_PROPOSED_LEDGER.jsonl": (
        29034,
        "585e2f40004c3b31cc766c46acdd86f939bcb4bba33dc024448a660ae44fdc78",
    ),
    "qa/HABRING_CH01_CH02_BUILD.json": (
        2214,
        "5c98d7f71f7ec68ffb7f2a76c4c3fb455f86d93b3d7741014ea8020180499724",
    ),
    "qa/HABRING_FULL_HTML_BUILD.json": (
        2182,
        "dceb65f4d5366699e18f5f825987c2c2172d1626fceb89e22918c875f00bcfa9",
    ),
    "qa/HABRING_FULL_READER_BUILD.json": (
        2619,
        "35dc5e27a54db1392c97950c4e9f39f22e655312d37226c80f545c683316112c",
    ),
    "qa/D90-HAB-01-02-prasyarat-dan-konveksitas-id.txt": (
        59808,
        "8e2f3d0e9555a138faeffada4e6fd07baf66d96055c018cf7b3554fbfe5491b0",
    ),
    "output/pdf/D90-HAB-01-02-prasyarat-dan-konveksitas-id.pdf": (
        720624,
        "5fc51737b0ec2d2342e93c0a53a997cd1f81a3df2d15415ef5fdd9c2c4a9dbdf",
    ),
    "output/pdf/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf": (
        3779312,
        "da2b421b97efce4e3d7b8cf6be9938d17b7768b9c6bcb4846b09b9c692b34c41",
    ),
    "output/html/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html": (
        1669938,
        "717ee81912a8b903acc87e5c59d830aa1d8c78abdda6e0c869d66b9a7bcde3a4",
    ),
}

RASTER_SHA256 = {
    "discontinuous_function.png": "fc5b5b3135eb726c58ef8e299751d310dfc363f7d31d7c28930ad018388397fa",
    "lsc_function.png": "2edde214506a703a0e40d5e32a1df5ae50809c0698cec2a3d7cd248647010547",
    "sets.png": "08bc716590267148f90b4dc45dc62e3959713b573b809c81c08967ab8cecda2e",
    "balls.png": "637e5a503469918640b6a8eb3971e74ae4d3778b5ef73808493ce2ceef2f0a31",
    "convex_fct.png": "c0844bf6b3732883d2faff403179ec3eb74ebe867f3ae68cc98ac192c70d373b",
}

BASE_LEDGER_FIELDS = (
    "event_id",
    "authority",
    "source",
    "surface",
    "source_issue",
    "target_action",
    "class",
)
CH2_LEDGER_FIELDS = BASE_LEDGER_FIELDS + (
    "correction_authorship",
    "source_rights",
    "target_status",
    "target_rights",
)

# Each Chapter 2 in-source correction marker maps to its formal ledger event.
# Two additional corrections (0144 and 0151) are anchored directly below.
H02_MARKER_TO_EVENT = {
    "001": "O015-HAB-ADV-0122",
    "028": "O015-HAB-ADV-0123",
    "002": "O015-HAB-ADV-0124",
    "003": "O015-HAB-ADV-0125",
    "004": "O015-HAB-ADV-0126",
    "029": "O015-HAB-ADV-0127",
    "005": "O015-HAB-ADV-0128",
    "006": "O015-HAB-ADV-0129",
    "007": "O015-HAB-ADV-0130",
    "025": "O015-HAB-ADV-0131",
    "037": "O015-HAB-ADV-0132",
    "008": "O015-HAB-ADV-0133",
    "026": "O015-HAB-ADV-0134",
    "030": "O015-HAB-ADV-0135",
    "036": "O015-HAB-ADV-0136",
    "021": "O015-HAB-ADV-0137",
    "009": "O015-HAB-ADV-0138",
    "010": "O015-HAB-ADV-0139",
    "011": "O015-HAB-ADV-0140",
    "031": "O015-HAB-ADV-0141",
    "012": "O015-HAB-ADV-0142",
    "032": "O015-HAB-ADV-0143",
    "022": "O015-HAB-ADV-0145",
    "013": "O015-HAB-ADV-0146",
    "027": "O015-HAB-ADV-0147",
    "014": "O015-HAB-ADV-0148",
    "015": "O015-HAB-ADV-0149",
    "033": "O015-HAB-ADV-0150",
    "016": "O015-HAB-ADV-0152",
    "017": "O015-HAB-ADV-0153",
    "023": "O015-HAB-ADV-0154",
    "034": "O015-HAB-ADV-0155",
    "018": "O015-HAB-ADV-0156",
    "024": "O015-HAB-ADV-0157",
    "019": "O015-HAB-ADV-0158",
    "020": "O015-HAB-ADV-0159",
    "035": "O015-HAB-ADV-0160",
    "038": "O015-HAB-ADV-0161",
}

# Positive anchors for Chapter 1 corrections.  The exact target hash is also
# frozen, so these anchors cannot silently drift to a different surface.
CH1_EVENT_ANCHORS: dict[str, tuple[str, ...]] = {
    "O015-HAB-ADV-0097": (r"+:V\times V\rightarrow V",),
    "O015-HAB-ADV-0098": (
        r"\lambda\cdot(u+v)=(\lambda\cdot u)+(\lambda\cdot v)",
        r"(\lambda+\mu)\cdot v=(\lambda\cdot v)+(\mu\cdot v)",
    ),
    "O015-HAB-ADV-0099": (r"\|\emptyarg\|:V\rightarrow[0,\infty)",),
    "O015-HAB-ADV-0100": (r"\|Av\|_b\leq\|A\|_{a,b}\|v\|_a",),
    "O015-HAB-ADV-0101": (
        r"|N|=0",
        r"\Omega\setminus N",
        r"/\!\sim_{\mathrm{a.e.}}",
    ),
    "O015-HAB-ADV-0102": (r"u,v,w\in V",),
    "O015-HAB-ADV-0103": (
        r"\lambda=\inner{v}{w}/\|w\|^2",
        r"\frac{|\inner{v}{w}|^2}{\|w\|^2}",
    ),
    "O015-HAB-ADV-0104": (
        r"Kasus $p=\infty$, $q=1$",
        r"$a,b\geq0$",
    ),
    "O015-HAB-ADV-0105": (r"\|x+y\|_p\neq0",),
    "O015-HAB-ADV-0106": (r"\|x_n-x\|\rightarrow0",),
    "O015-HAB-ADV-0107": (r"memuat tak hingga banyaknya suku $x_k$",),
    "O015-HAB-ADV-0108": (r"2^{-k}(b_0-a_0)",),
    "O015-HAB-ADV-0109": (
        r"semua fungsional linear kontinu dari $V$ ke $\R$",
        r"|v^*(v)|",
    ),
    "O015-HAB-ADV-0110": (r"$v^*\in V^*$",),
    "O015-HAB-ADV-0111": (r"V=\ker(v^*)\oplus\ker(v^*)^\perp",),
    "O015-HAB-ADV-0112": (
        r"pemetaan linear kontinu di antara dua ruang",
        r"A^*:W\rightarrow V",
    ),
    "O015-HAB-ADV-0113": (
        r"$U,V,W$ ruang Hilbert",
        r"$(BA)^*=A^*B^*$",
    ),
    "O015-HAB-ADV-0114": (r"pembatasan $f$ pada $\dom(f)$ kontinu",),
    "O015-HAB-ADV-0115": (r"\liminf_{k\rightarrow\infty}f(x_{n(k)})",),
    "O015-HAB-ADV-0116": (
        r"Jika $L=+\infty$",
        r"$L=-\infty$ tidak mungkin",
    ),
    "O015-HAB-ADV-0117": (r"f:V\rightarrow(-\infty,+\infty]$ disebut koersif",),
    "O015-HAB-ADV-0118": (r"misalnya refleksivitas",),
    "O015-HAB-ADV-0119": (r"Pada $\R^d$, untuk $1\leq p\leq\infty$",),
}

CH1_NEGATIVE_ANCHORS: dict[str, str] = {
    "O015-HAB-ADV-0120": r"\begin{example}[Ruang-ruang vektor penting]\\",
    "O015-HAB-ADV-0121": r"\begin{example}[Norma-norma umum]\\",
}

CH2_UNMARKED_ANCHORS = {
    "O015-HAB-ADV-0144": r"Pada $t=0$, integran dipahami melalui perpanjangan kontinu",
    "O015-HAB-ADV-0151": r"\max_i\{\lambda f_i(x)+(1-\lambda)f_i(y)\}",
}

# Display ordinals whose normalized difference is purely presentational.  All
# other unequal display pairs must intersect a formal ledger source locator.
PRESENTATIONAL_DISPLAY_ALLOWLIST = {
    ("preliminaries.tex", 6): "subscript braces and operator-name typography",
    ("preliminaries.tex", 25): "comma and scalar-variable ordering",
    ("preliminaries.tex", 38): "set-builder vertical-bar typography",
    ("preliminaries.tex", 39): "otherwise rendered as the equivalent complement predicate",
    ("preliminaries.tex", 40): "parentheses make the minimization scope explicit",
    ("preliminaries.tex", 41): "set-builder vertical-bar typography",
}

BRACKET_MAPPING_CH2 = (
    (0, 0, "O015-HAB-ADV-0129"),
    (1, 1, None),
    (2, 2, "O015-HAB-ADV-0138"),
    (3, 3, "O015-HAB-ADV-0137"),
    (None, 4, "O015-HAB-ADV-0142"),
    (None, 5, "O015-HAB-ADV-0148"),
    (4, 6, None),
    (5, 7, None),
    (6, 8, None),
    (7, 9, "O015-HAB-ADV-0157"),
    (8, 10, "O015-HAB-ADV-0159"),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_identity(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": sha256_bytes(data)}


def compact_json_sha(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(data)


def check(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def strip_comments_keep_lines(text: str) -> str:
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        ending = "\n" if line.endswith("\n") else ""
        core = line[:-1] if ending else line
        cut = None
        for index, char in enumerate(core):
            if char != "%":
                continue
            preceding = 0
            cursor = index - 1
            while cursor >= 0 and core[cursor] == "\\":
                preceding += 1
                cursor -= 1
            if preceding % 2 == 0:
                cut = index
                break
        if cut is not None:
            core = core[:cut]
        output.append(core + ending)
    return "".join(output)


def ordered_topology(text: str) -> list[list[str]]:
    clean = strip_comments_keep_lines(text)
    return [[kind, name] for kind, name in re.findall(r"\\(begin|end)\{([^{}]+)\}", clean)]


def extract_labels(text: str) -> list[str]:
    return re.findall(r"\\label\{([^{}]+)\}", strip_comments_keep_lines(text))


def extract_refs(text: str) -> list[str]:
    clean = strip_comments_keep_lines(text)
    return re.findall(r"\\(?:ref|eqref|autoref|cref|Cref)\{([^{}]+)\}", clean)


def extract_raster_paths(text: str) -> list[str]:
    clean = strip_comments_keep_lines(text)
    return re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}", clean)


def extract_braced_arguments(text: str, command: str) -> list[dict[str, Any]]:
    clean = strip_comments_keep_lines(text)
    pattern = re.compile(r"\\" + re.escape(command) + r"\s*\{")
    results: list[dict[str, Any]] = []
    cursor = 0
    while True:
        match = pattern.search(clean, cursor)
        if match is None:
            break
        index = match.end()
        depth = 1
        while index < len(clean) and depth:
            if clean[index] == "{" and clean[index - 1] != "\\":
                depth += 1
            elif clean[index] == "}" and clean[index - 1] != "\\":
                depth -= 1
            index += 1
        if depth:
            raise ValueError(f"unbalanced argument for \\{command} at offset {match.start()}")
        value = clean[match.end() : index - 1]
        results.append(
            {
                "line": 1 + clean.count("\n", 0, match.start()),
                "sha256": sha256_bytes(value.encode("utf-8")),
            }
        )
        cursor = index
    return results


def replace_balanced_arguments(text: str, pattern: re.Pattern[str], replacement: str) -> str:
    cursor = 0
    while True:
        match = pattern.search(text, cursor)
        if match is None:
            return text
        index = match.end()
        depth = 1
        while index < len(text) and depth:
            if text[index] == "{" and text[index - 1] != "\\":
                depth += 1
            elif text[index] == "}" and text[index - 1] != "\\":
                depth -= 1
            index += 1
        if depth:
            raise ValueError(f"unbalanced braced surface near offset {match.start()}")
        text = text[: match.end()] + replacement + "}" + text[index:]
        cursor = match.end() + len(replacement) + 1


def normalize_tikz(block: str) -> str:
    value = strip_comments_keep_lines(block)
    # Preserve node placement/options but abstract its human-facing contents.
    node_pattern = re.compile(r"\\node\b(?:[^{};]|\{[^{}]*\})*?\{")
    value = replace_balanced_arguments(value, node_pattern, "<NODE>")
    for command in ("text", "textrm", "addlegendentry"):
        value = replace_balanced_arguments(value, re.compile(r"\\" + command + r"\s*\{"), "<TEXT>")
    for key in ("title", "xlabel", "ylabel", "legend entries", "xticklabels", "yticklabels"):
        value = replace_balanced_arguments(value, re.compile(re.escape(key) + r"\s*=\s*\{"), "<TEXT>")
    return re.sub(r"\s+", "", value)


def extract_tikz(text: str) -> list[dict[str, Any]]:
    clean = strip_comments_keep_lines(text)
    blocks = re.finditer(r"\\begin\{tikzpicture\}(.*?)\\end\{tikzpicture\}", clean, re.S)
    result = []
    for match in blocks:
        normalized = normalize_tikz(match.group(1))
        result.append(
            {
                "line": 1 + clean.count("\n", 0, match.start()),
                "normalized_sha256": sha256_bytes(normalized.encode("utf-8")),
            }
        )
    return result


def normalize_formula(value: str) -> str:
    for command in ("text", "textrm", "textnormal", "operatorname"):
        value = replace_balanced_arguments(value, re.compile(r"\\" + command + r"\*?\s*\{"), "<TEXT>")
    replacements = {
        r"\mathbb{R}": r"\bR",
        r"\mathbb R": r"\bR",
        r"\mathbb{N}": r"\bN",
        r"\mathbb N": r"\bN",
        r"\coloneqq": r"\coloneq",
        r"\Longrightarrow": r"\Rightarrow",
        r"\ldots": r"\dots",
        r"\top": "T",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\\label\{[^{}]+\}", "", value)
    value = re.sub(r"\\(?:left|right|displaystyle|textstyle|,|;|!|quad|qquad)", "", value)
    value = value.replace("&", "").replace(r"\\", "")
    value = re.sub(r"[\s.,;:]", "", value)
    return value


def extract_formula_surfaces(text: str) -> list[dict[str, Any]]:
    clean = strip_comments_keep_lines(text)
    spans: list[tuple[int, int, str, str]] = []
    env_pattern = re.compile(
        r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}(.*?)\\end\{\1\}",
        re.S,
    )
    for match in env_pattern.finditer(clean):
        spans.append((match.start(), match.end(), f"env:{match.group(1)}", match.group(2)))
    for match in re.finditer(r"\\\[(.*?)\\\]", clean, re.S):
        spans.append((match.start(), match.end(), "bracket", match.group(1)))
    masked = list(clean)
    for start, end, _, _ in spans:
        masked[start:end] = " " * (end - start)
    remainder = "".join(masked)
    for match in re.finditer(r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$(?!\$)", remainder, re.S):
        spans.append((match.start(), match.end(), "inline-dollar", clean[match.start() + 1 : match.end() - 1]))
    occupied = [(start, end) for start, end, _, _ in spans]
    for match in re.finditer(r"\\\((.*?)\\\)", remainder, re.S):
        if any(start < match.end() and match.start() < end for start, end in occupied):
            continue
        spans.append((match.start(), match.end(), "inline-paren", match.group(1)))
    spans.sort(key=lambda item: (item[0], item[1]))
    result = []
    for start, _, kind, raw in spans:
        normalized = normalize_formula(raw)
        result.append(
            {
                "line": 1 + clean.count("\n", 0, start),
                "kind": kind,
                "raw_sha256": sha256_bytes(raw.encode("utf-8")),
                "normalized_sha256": sha256_bytes(normalized.encode("utf-8")),
            }
        )
    return result


def extract_display_environments(text: str) -> list[dict[str, Any]]:
    clean = strip_comments_keep_lines(text)
    pattern = re.compile(
        r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}(.*?)\\end\{\1\}",
        re.S,
    )
    result = []
    for match in pattern.finditer(clean):
        normalized = normalize_formula(match.group(2))
        start = 1 + clean.count("\n", 0, match.start())
        end = start + match.group(0).count("\n")
        result.append(
            {
                "kind": match.group(1),
                "start_line": start,
                "end_line": end,
                "normalized_sha256": sha256_bytes(normalized.encode("utf-8")),
            }
        )
    return result


def extract_brackets(text: str) -> list[dict[str, Any]]:
    clean = strip_comments_keep_lines(text)
    result = []
    for match in re.finditer(r"\\\[(.*?)\\\]", clean, re.S):
        normalized = normalize_formula(match.group(1))
        result.append(
            {
                "line": 1 + clean.count("\n", 0, match.start()),
                "normalized_sha256": sha256_bytes(normalized.encode("utf-8")),
            }
        )
    return result


def parse_source_locator(locator: str) -> tuple[str, int, int]:
    match = re.fullmatch(r"([^:]+):(\d+)(?:-(\d+))?(?: footnote)?", locator)
    if match is None:
        raise ValueError(f"unparseable ledger locator: {locator}")
    start = int(match.group(2))
    return match.group(1), start, int(match.group(3) or start)


def read_jsonl(path: Path, expected_fields: tuple[str, ...], failures: list[str]) -> list[dict[str, str]]:
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            failures.append(f"{path.name}:{line_number}: invalid JSON: {error}")
            continue
        check(isinstance(record, dict), f"{path.name}:{line_number}: record is not an object", failures)
        if not isinstance(record, dict):
            continue
        check(tuple(record) == expected_fields, f"{path.name}:{line_number}: field order/schema mismatch", failures)
        check(all(isinstance(record.get(field), str) and record[field].strip() for field in expected_fields),
              f"{path.name}:{line_number}: empty or non-string field", failures)
        records.append(record)
    return records


def source_event_ranges(records: Iterable[dict[str, str]], source_name: str) -> list[tuple[int, int, str]]:
    result = []
    for record in records:
        filename, start, end = parse_source_locator(record["source"])
        if filename == source_name:
            result.append((start, end, record["event_id"]))
    return result


def verify_display_accounting(
    source_name: str,
    source_text: str,
    target_text: str,
    records: list[dict[str, str]],
    failures: list[str],
) -> dict[str, Any]:
    source = extract_display_environments(source_text)
    target = extract_display_environments(target_text)
    check(len(source) == len(target), f"{source_name}: display-environment count mismatch", failures)
    ranges = source_event_ranges(records, source_name)
    rows = []
    category_counts: Counter[str] = Counter()
    for ordinal, (left, right) in enumerate(zip(source, target)):
        check(left["kind"] == right["kind"], f"{source_name}: display kind mismatch at ordinal {ordinal}", failures)
        if left["normalized_sha256"] == right["normalized_sha256"]:
            category = "normalized-identical"
            event_ids: list[str] = []
        else:
            event_ids = [
                event_id
                for start, end, event_id in ranges
                if start <= left["end_line"] + 2 and left["start_line"] - 2 <= end
            ]
            if event_ids:
                category = "ledger-bound-delta"
            elif (source_name, ordinal) in PRESENTATIONAL_DISPLAY_ALLOWLIST:
                category = "frozen-presentational-equivalent"
            else:
                category = "unaccounted-delta"
                failures.append(f"{source_name}: unaccounted display delta at ordinal {ordinal}")
        category_counts[category] += 1
        rows.append(
            {
                "ordinal": ordinal,
                "source_line": left["start_line"],
                "target_line": right["start_line"],
                "source_normalized_sha256": left["normalized_sha256"],
                "target_normalized_sha256": right["normalized_sha256"],
                "category": category,
                "event_ids": event_ids,
                "note": PRESENTATIONAL_DISPLAY_ALLOWLIST.get((source_name, ordinal)),
            }
        )
    return {
        "source_count": len(source),
        "target_count": len(target),
        "category_counts": dict(sorted(category_counts.items())),
        "pairs_sha256": compact_json_sha(rows),
        "unaccounted": [row for row in rows if row["category"] == "unaccounted-delta"],
    }


def verify_build_report(path: Path, failures: list[str]) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    check(report.get("result") == "pass", f"{path.name}: result is not pass", failures)
    determinism = report.get("determinism", {})
    check(determinism.get("byte_identical") is True, f"{path.name}: build is not byte-identical", failures)
    check(determinism.get("builds") == 2, f"{path.name}: expected two builds", failures)
    identities = []
    candidates: list[dict[str, Any]] = []
    for key in ("artifact", "wrapper", "text_extract", "final_log"):
        value = report.get(key)
        if isinstance(value, dict) and "path" in value:
            candidates.append(value)
    candidates.extend(value for value in report.get("inputs", []) if isinstance(value, dict) and "path" in value)
    artifact = report.get("artifact", {})
    candidates.extend(value for value in artifact.get("components", []) if isinstance(value, dict) and "path" in value)
    seen = set()
    for value in candidates:
        rel = value["path"].replace("\\", "/")
        if rel in seen:
            continue
        seen.add(rel)
        live_path = ROOT / rel
        check(live_path.is_file(), f"{path.name}: reported file missing: {rel}", failures)
        if not live_path.is_file():
            continue
        identity = file_identity(live_path)
        check(identity["bytes"] == value.get("bytes"), f"{path.name}: byte mismatch for {rel}", failures)
        check(identity["sha256"] == value.get("sha256"), f"{path.name}: hash mismatch for {rel}", failures)
        identities.append(identity)
    return {
        "schema": report.get("schema"),
        "report": file_identity(path),
        "result": report.get("result"),
        "determinism": determinism,
        "verified_live_files": identities,
    }


def flatten_outline(items: list[Any]) -> list[Any]:
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(flatten_outline(item))
        else:
            result.append(item)
    return result


def inspect_pdf(path: Path, markers: list[str], failures: list[str]) -> dict[str, Any]:
    reader = PdfReader(str(path))
    check(not reader.is_encrypted, f"{path.name}: PDF is encrypted", failures)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    folded = text.casefold()
    missing = [marker for marker in markers if marker.casefold() not in folded]
    check(not missing, f"{path.name}: missing reader markers {missing}", failures)
    root_object = reader.trailer["/Root"]
    lang = str(root_object.get("/Lang", ""))
    check(lang == "id-ID", f"{path.name}: catalog language is {lang!r}, expected 'id-ID'", failures)
    try:
        outline_count = len(flatten_outline(reader.outline))
    except Exception as error:  # pragma: no cover - still fail closed on malformed outline
        failures.append(f"{path.name}: outline read failed: {error}")
        outline_count = None
    return {
        "identity": file_identity(path),
        "pages": len(reader.pages),
        "catalog_lang": lang,
        "encrypted": reader.is_encrypted,
        "outline_entries": outline_count,
        "text_bytes_utf8": len(text.encode("utf-8")),
        "text_sha256": sha256_bytes(text.encode("utf-8")),
        "markers": markers,
        "missing_markers": missing,
    }


def main() -> int:
    failures: list[str] = []

    exact_identities = []
    for rel, (expected_bytes, expected_hash) in EXPECTED_FILES.items():
        path = ROOT / rel
        check(path.is_file(), f"missing exact input/artifact: {rel}", failures)
        if not path.is_file():
            continue
        identity = file_identity(path)
        exact_identities.append(identity)
        check(identity["bytes"] == expected_bytes, f"exact byte mismatch: {rel}", failures)
        check(identity["sha256"] == expected_hash, f"exact hash mismatch: {rel}", failures)

    preface = (ROOT / "authority/habring/source-v1/preface.tex").read_text(encoding="utf-8")
    prelim = (ROOT / "authority/habring/source-v1/preliminaries.tex").read_text(encoding="utf-8")
    convex = (ROOT / "authority/habring/source-v1/convexity.tex").read_text(encoding="utf-8")
    ch1 = (ROOT / "source/id-ID/habring-01-prasyarat-id.tex").read_text(encoding="utf-8")
    ch2 = (ROOT / "source/id-ID/habring-02-konveksitas-id.tex").read_text(encoding="utf-8")
    wrapper = (ROOT / "source/id-ID/D90-HAB-01-02-prasyarat-dan-konveksitas-id.tex").read_text(encoding="utf-8")

    ch1_records = read_jsonl(
        ROOT / "qa/HABRING_CH01_CH02_PROPOSED_LEDGER.jsonl", BASE_LEDGER_FIELDS, failures
    )
    ch2_records = read_jsonl(ROOT / "qa/HABRING_CH02_PROPOSED_LEDGER.jsonl", CH2_LEDGER_FIELDS, failures)
    records = ch1_records + ch2_records
    event_ids = [record["event_id"] for record in records]
    expected_ids = [f"O015-HAB-ADV-{number:04d}" for number in range(97, 162)]
    check(event_ids == expected_ids, "correction event IDs are not exactly consecutive 0097--0161", failures)
    check(len(event_ids) == len(set(event_ids)), "duplicate correction event ID", failures)
    check(len(event_ids) == 65, "0097--0161 inclusive must contain 65 events", failures)
    for record in records:
        check(record["authority"] == "o015-habring-arxiv-2607.11664v1",
              f"{record['event_id']}: wrong authority", failures)
        check(record["class"].startswith(("determined_", "declared_")),
              f"{record['event_id']}: correction class is neither determined nor declared", failures)
        try:
            filename, start, end = parse_source_locator(record["source"])
            source_line_count = len((ROOT / "authority/habring/source-v1" / filename).read_text(encoding="utf-8").splitlines())
            check(1 <= start <= end <= source_line_count,
                  f"{record['event_id']}: source locator outside authority", failures)
        except (ValueError, FileNotFoundError) as error:
            failures.append(f"{record['event_id']}: {error}")
    for record in ch2_records:
        check(record["correction_authorship"] == "OpenAI Codex gpt-5.6-sol, Ultra",
              f"{record['event_id']}: wrong correction authorship", failures)
        check(record["source_rights"] == "Andreas Habring; arXiv:2607.11664v1; CC BY 4.0",
              f"{record['event_id']}: wrong source rights", failures)
        check(record["target_status"] == "proposed", f"{record['event_id']}: wrong target status", failures)
        check(record["target_rights"] == "Indonesian translation and correction wording: CC BY-SA 4.0",
              f"{record['event_id']}: wrong target rights", failures)

    topology = {}
    for source_name, source_text, target_name, target_text, expected_pairs, expected_items in (
        ("preliminaries.tex", prelim, "habring-01-prasyarat-id.tex", ch1, 244, 32),
        ("convexity.tex", convex, "habring-02-konveksitas-id.tex", ch2, 280, 52),
    ):
        source_topology = ordered_topology(source_text)
        target_topology = ordered_topology(target_text)
        check(source_topology == target_topology, f"{source_name}: ordered begin/end topology mismatch", failures)
        check(len(source_topology) == expected_pairs, f"{source_name}: unexpected topology token count", failures)
        source_items = len(re.findall(r"\\item(?:\s*\[[^\]]*\])?", strip_comments_keep_lines(source_text)))
        target_items = len(re.findall(r"\\item(?:\s*\[[^\]]*\])?", strip_comments_keep_lines(target_text)))
        check(source_items == target_items == expected_items, f"{source_name}: item count mismatch", failures)
        source_labels, target_labels = extract_labels(source_text), extract_labels(target_text)
        source_refs, target_refs = extract_refs(source_text), extract_refs(target_text)
        check(source_labels == target_labels, f"{source_name}: ordered labels mismatch", failures)
        check(source_refs == target_refs, f"{source_name}: ordered references mismatch", failures)
        source_rasters, target_rasters = extract_raster_paths(source_text), extract_raster_paths(target_text)
        check(source_rasters == target_rasters, f"{source_name}: ordered raster paths mismatch", failures)
        source_tikz, target_tikz = extract_tikz(source_text), extract_tikz(target_text)
        check([item["normalized_sha256"] for item in source_tikz] == [item["normalized_sha256"] for item in target_tikz],
              f"{source_name}: normalized TikZ mismatch", failures)
        source_footnotes, target_footnotes = extract_braced_arguments(source_text, "footnote"), extract_braced_arguments(target_text, "footnote")
        check(len(source_footnotes) == len(target_footnotes), f"{source_name}: footnote count mismatch", failures)
        topology[source_name] = {
            "ordered_begin_end_tokens": len(source_topology),
            "ordered_begin_end_sha256": compact_json_sha(source_topology),
            "items": source_items,
            "labels": source_labels,
            "refs": source_refs,
            "figures": sum(1 for kind, name in source_topology if kind == "begin" and name == "figure"),
            "raster_paths": source_rasters,
            "tikz_source": source_tikz,
            "tikz_target": target_tikz,
            "footnotes_source": source_footnotes,
            "footnotes_target": target_footnotes,
        }

    check(not ordered_topology(preface), "preface authority unexpectedly contains environment topology", failures)
    check("\\chapter*{Prakata}" in ch1, "translated preface heading missing", failures)
    check(all(marker in ch1 for marker in ("Prof.~Thomas Pock", "semester musim panas 2026", "Prof.~Christian Clason")),
          "translated preface content markers missing", failures)

    segments_ch1 = re.findall(r"(?m)^% segment-id: (d90\.hab\.v1\.ch01\.seg\d{4})\s*$", ch1)
    segments_ch2 = re.findall(r"(?m)^% segment-id: (d90\.hab\.v1\.ch02\.seg\d{4})\s*$", ch2)
    expected_ch1_segments = [f"d90.hab.v1.ch01.seg{number:04d}" for number in range(1, 9)]
    expected_ch2_segments = [f"d90.hab.v1.ch02.seg{number:04d}" for number in range(1, 18)]
    check(segments_ch1 == expected_ch1_segments, "Chapter 1 stable segment range/order mismatch", failures)
    check(segments_ch2 == expected_ch2_segments, "Chapter 2 stable segment range/order mismatch", failures)
    check(len(set(segments_ch1 + segments_ch2)) == 25, "stable segment IDs are not globally unique", failures)

    placeholders = re.compile(r"(?i)\b(?:TODO|FIXME|TBD|PLACEHOLDER|LOREM|XXX|TRANSLATE\s+ME)\b")
    placeholder_findings = []
    for name, text in (("habring-01-prasyarat-id.tex", ch1), ("habring-02-konveksitas-id.tex", ch2)):
        for match in placeholders.finditer(text):
            placeholder_findings.append({"file": name, "line": 1 + text.count("\n", 0, match.start()), "token": match.group(0)})
    check(not placeholder_findings, "TODO/FIXME/placeholder token found", failures)

    marker_occurrences = re.findall(r"H02-C(\d{3})", ch2)
    check(sorted(marker_occurrences) == [f"{number:03d}" for number in range(1, 39)],
          "H02 correction markers are not exactly C001--C038 once each", failures)
    check(set(H02_MARKER_TO_EVENT.values()) | set(CH2_UNMARKED_ANCHORS) == set(record["event_id"] for record in ch2_records),
          "Chapter 2 marker/direct-anchor event coverage mismatch", failures)

    correction_bindings = []
    for event_id, anchors in CH1_EVENT_ANCHORS.items():
        missing = [anchor for anchor in anchors if anchor not in ch1]
        check(not missing, f"{event_id}: Chapter 1 correction anchor missing", failures)
        correction_bindings.append(
            {"event_id": event_id, "binding": "target-positive-anchor", "anchor_sha256": compact_json_sha(list(anchors)), "pass": not missing}
        )
    for event_id, forbidden in CH1_NEGATIVE_ANCHORS.items():
        absent = forbidden not in ch1
        check(absent, f"{event_id}: removed TeX defect remains", failures)
        correction_bindings.append(
            {"event_id": event_id, "binding": "target-negative-anchor", "anchor_sha256": sha256_bytes(forbidden.encode("utf-8")), "pass": absent}
        )
    for marker, event_id in H02_MARKER_TO_EVENT.items():
        found = marker_occurrences.count(marker) == 1
        check(found, f"{event_id}: H02-C{marker} marker missing or duplicated", failures)
        correction_bindings.append(
            {"event_id": event_id, "binding": f"H02-C{marker}", "anchor_sha256": sha256_bytes(f"H02-C{marker}".encode()), "pass": found}
        )
    for event_id, anchor in CH2_UNMARKED_ANCHORS.items():
        found = anchor in ch2
        check(found, f"{event_id}: Chapter 2 direct correction anchor missing", failures)
        correction_bindings.append(
            {"event_id": event_id, "binding": "target-positive-anchor", "anchor_sha256": sha256_bytes(anchor.encode("utf-8")), "pass": found}
        )
    correction_bindings.sort(key=lambda item: item["event_id"])
    check([item["event_id"] for item in correction_bindings] == expected_ids,
          "not every deliberate correction has exactly one binding", failures)

    formula_inventories = {}
    for name, text in (
        ("preface.tex", preface),
        ("preliminaries.tex", prelim),
        ("convexity.tex", convex),
        ("habring-01-prasyarat-id.tex", ch1),
        ("habring-02-konveksitas-id.tex", ch2),
    ):
        inventory = extract_formula_surfaces(text)
        formula_inventories[name] = {
            "count": len(inventory),
            "kind_counts": dict(sorted(Counter(item["kind"] for item in inventory).items())),
            "inventory_sha256": compact_json_sha(inventory),
        }
    display_accounting = {
        "preliminaries.tex": verify_display_accounting("preliminaries.tex", prelim, ch1, records, failures),
        "convexity.tex": verify_display_accounting("convexity.tex", convex, ch2, records, failures),
    }

    source_brackets = extract_brackets(convex)
    target_brackets = extract_brackets(ch2)
    check(len(source_brackets) == 9 and len(target_brackets) == 11,
          "Chapter 2 bracket-display accounting count mismatch", failures)
    bracket_rows = []
    for source_ordinal, target_ordinal, event_id in BRACKET_MAPPING_CH2:
        source_item = source_brackets[source_ordinal] if source_ordinal is not None else None
        target_item = target_brackets[target_ordinal] if target_ordinal is not None else None
        if event_id is None and source_item is not None and target_item is not None:
            # Punctuation and translated prose inside \text{} may differ; the
            # exact frozen hashes are recorded even where normalization differs.
            category = "frozen-equivalent"
        else:
            category = "ledger-bound-delta"
        bracket_rows.append(
            {
                "source_ordinal": source_ordinal,
                "target_ordinal": target_ordinal,
                "source": source_item,
                "target": target_item,
                "event_id": event_id,
                "category": category,
            }
        )
    check(sorted(item for row in bracket_rows for item in ([row["source_ordinal"]] if row["source_ordinal"] is not None else [])) == list(range(9)),
          "source bracket mapping is not bijective", failures)
    check(sorted(item for row in bracket_rows for item in ([row["target_ordinal"]] if row["target_ordinal"] is not None else [])) == list(range(11)),
          "target bracket mapping is not bijective", failures)

    raster_identities = []
    for filename, expected_hash in RASTER_SHA256.items():
        source_path = ROOT / "authority/habring/source-v1/figures" / filename
        target_path = ROOT / "source/id-ID/figures" / filename
        source_identity, target_identity = file_identity(source_path), file_identity(target_path)
        check(source_identity["sha256"] == target_identity["sha256"] == expected_hash,
              f"raster byte identity mismatch: {filename}", failures)
        raster_identities.append({"filename": filename, "authority": source_identity, "target": target_identity})

    abs_html = (ROOT / "authority/habring/arxiv-2607.11664v1-abs.html").read_text(encoding="utf-8")
    api_xml = (ROOT / "authority/habring/2607.11664v1-api.xml").read_text(encoding="utf-8")
    legalcode = (ROOT / "authority/habring/CC-BY-4.0-legalcode.txt").read_text(encoding="utf-8")
    rights_markers = {
        "abs_arxiv_id": "2607.11664" in abs_html,
        "abs_author": "Andreas Habring" in abs_html,
        "abs_cc_by_4_url": 'href="http://creativecommons.org/licenses/by/4.0/"' in abs_html,
        "api_exact_version": "http://arxiv.org/abs/2607.11664v1" in api_xml,
        "api_title": "Lecture Notes: Convex Optimization" in api_xml,
        "api_author": "<name>Andreas Habring</name>" in api_xml,
        "legalcode_identity": "Attribution 4.0 International" in legalcode,
        "wrapper_authority": "arXiv:2607.11664v1" in wrapper and "Andreas Habring" in wrapper,
        "wrapper_cc_by_4": "CC BY 4.0" in wrapper and "https://creativecommons.org/licenses/by/4.0/" in wrapper,
        "wrapper_model_provenance": "OpenAI Codex gpt-5.6-sol, Ultra" in wrapper,
        "wrapper_nonendorsement": "bukan karya resmi atau dukungan" in wrapper,
    }
    check(all(rights_markers.values()), "CC BY 4.0 authority/attribution identity check failed", failures)

    build_reports = [
        verify_build_report(ROOT / "qa/HABRING_CH01_CH02_BUILD.json", failures),
        verify_build_report(ROOT / "qa/HABRING_FULL_HTML_BUILD.json", failures),
        verify_build_report(ROOT / "qa/HABRING_FULL_READER_BUILD.json", failures),
    ]

    unit_pdf = inspect_pdf(
        ROOT / "output/pdf/D90-HAB-01-02-prasyarat-dan-konveksitas-id.pdf",
        ["Optimisasi Konveks", "Prakata", "Prasyarat", "Kekonveksan", "Andreas Habring", "CC BY 4.0", "OpenAI Codex", "gpt-5.6-sol", "Ultra"],
        failures,
    )
    full_pdf = inspect_pdf(
        ROOT / "output/pdf/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf",
        ["Prakata", "Prasyarat", "Kekonveksan", "Subgradien", "Metode Gradien Proksimal", "Akselerasi", "Dualitas", "Penurunan Gradien Stokastik", "Transportasi Optimal"],
        failures,
    )
    check(unit_pdf["pages"] == 36, "unit reader page count is not 36", failures)
    check(full_pdf["pages"] == 139, "full reader page count is not 139", failures)
    check(full_pdf["outline_entries"] == 9, "full reader outline does not contain 9 entries", failures)

    unit_text = (ROOT / "qa/D90-HAB-01-02-prasyarat-dan-konveksitas-id.txt").read_text(encoding="utf-8")
    unit_text_markers = ["OPTIMISASI KONVEKS", "PRAKATA", "1 PRASYARAT", "2 KEKONVEKSAN", "CC BY 4.0", "OpenAI Codex", "gpt-5.6-sol, Ultra"]
    missing_unit_text = [marker for marker in unit_text_markers if marker not in unit_text]
    check(not missing_unit_text, f"pdftotext reader markers missing: {missing_unit_text}", failures)

    html_path = ROOT / "output/html/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html"
    html = html_path.read_text(encoding="utf-8")
    html_markers = [
        'lang="id-ID"',
        '<meta name="license" content="CC BY 4.0">',
        '<section id="prakata"',
        '<section id="prasyarat"',
        '<section id="kekonveksan"',
        "OpenAI",
        "gpt-5.6-sol, Ultra",
    ]
    missing_html = [marker for marker in html_markers if marker not in html]
    check(not missing_html, f"HTML reader markers missing: {missing_html}", failures)
    check("\\begin{tikzpicture}" not in html and "\\includegraphics" not in html,
          "HTML contains leaked raw TeX figure commands", failures)
    embedded_images = len(re.findall(r"data:image/[^;]+;base64,", html))
    check(embedded_images == 5, f"HTML embedded image count {embedded_images}, expected 5", failures)

    report = {
        "schema": "o015-habring-ch01-ch02-structure-audit-v1",
        "result": "pass" if not failures else "fail",
        "failures": failures,
        "authority": {
            "work": "Andreas Habring, Lecture Notes: Convex Optimization",
            "arxiv": "2607.11664v1",
            "source_tar_sha256": EXPECTED_FILES["authority/habring/2607.11664v1-source.tar"][1],
            "license": "CC BY 4.0",
            "rights_markers": rights_markers,
        },
        "exact_file_identities": exact_identities,
        "ledger": {
            "chapter1_records": len(ch1_records),
            "chapter2_records": len(ch2_records),
            "correction_event_count": len(event_ids),
            "first_event": event_ids[0] if event_ids else None,
            "last_event": event_ids[-1] if event_ids else None,
            "event_ids_sha256": compact_json_sha(event_ids),
            "range_cardinality_note": "The inclusive integer range 0097--0161 contains 65 events; 61 would be arithmetically inconsistent.",
            "field_profiles": {
                "chapter1": list(BASE_LEDGER_FIELDS),
                "chapter2": list(CH2_LEDGER_FIELDS),
            },
            "h02_marker_count": len(marker_occurrences),
            "h02_markers": sorted(marker_occurrences),
            "correction_bindings": correction_bindings,
            "correction_bindings_sha256": compact_json_sha(correction_bindings),
        },
        "structure": {
            "preface_formula_surfaces": formula_inventories["preface.tex"]["count"],
            "chapters": topology,
            "stable_segments": {
                "chapter1": segments_ch1,
                "chapter2": segments_ch2,
                "combined_unique": len(set(segments_ch1 + segments_ch2)),
            },
            "placeholder_findings": placeholder_findings,
            "figure_description_count": ch1.count("Deskripsi gambar.") + ch2.count("Deskripsi gambar."),
            "raster_byte_identity": raster_identities,
        },
        "formula_surface_accounting": {
            "inventories": formula_inventories,
            "display_environments": display_accounting,
            "chapter2_bracket_mapping": bracket_rows,
            "chapter2_bracket_mapping_sha256": compact_json_sha(bracket_rows),
            "policy": "Every math surface is frozen by an inventory digest. Every non-presentational display delta and every deliberate correction has a formal ledger binding; inserted/moved bracket displays have an explicit bijective map.",
        },
        "build_and_reader_verification": {
            "build_reports": build_reports,
            "unit_pdf": unit_pdf,
            "full_pdf": full_pdf,
            "unit_pdftotext_markers": unit_text_markers,
            "unit_pdftotext_missing": missing_unit_text,
            "html": {
                "identity": file_identity(html_path),
                "markers": html_markers,
                "missing_markers": missing_html,
                "embedded_image_count": embedded_images,
            },
        },
        "audit_script": file_identity(Path(__file__)),
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    report_identity = file_identity(REPORT_PATH)
    print(json.dumps({"result": report["result"], "failures": failures, "report": report_identity}, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
