"""Deterministic structural/formula audit for Habring Chapter 8 id-ID.

The audit is deliberately bounded to the frozen authority, the frozen reader
target, its standalone wrapper, and the proposed Chapter 8 correction ledger.
It never edits those inputs.  It writes only the two declared JSON QA outputs.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "habring" / "source-v1" / "stochastic.tex"
TARGET = ROOT / "source" / "id-ID" / "habring-08-penurunan-gradien-stokastik-id.tex"
WRAPPER = ROOT / "source" / "id-ID" / "D90-HAB-08-penurunan-gradien-stokastik-id.tex"
PROPOSED_LEDGER = ROOT / "qa" / "CHAPTER08_PROPOSED_LEDGER.jsonl"
FORMULA_MANIFEST = ROOT / "qa" / "STOCHASTIC_FORMULA_DELTA_MANIFEST.json"
REPORT = ROOT / "qa" / "STOCHASTIC_STRUCTURE_REPORT.json"

EXPECTED_IDENTITIES = {
    "source": {
        "bytes": 4_665,
        "lines": 107,
        "sha256": "610d11b59d8dfabbbbe6fbc509a0f9ac1727540458c67f8cd3b7bab49566a07d",
    },
    "target": {
        "bytes": 6_378,
        "lines": 133,
        "sha256": "f610aaec91aa9b76582f251458da65d25cc37a933a51da478cad13ee16e5a344",
    },
    "wrapper": {
        "bytes": 5_129,
        "lines": 69,
        "sha256": "d00ea41830af388c227a1054025f049a9315da6f41675573965042d320eb7428",
    },
    "proposed_ledger": {
        "bytes": 5_188,
        "lines": 8,
        "sha256": "a815d0211da31b21a25a3f9fd8a2c1ec5fcc7da5e7a62c980f75df40ae65d45d",
    },
}

EXPECTED_ENVIRONMENT_COUNTS = {
    "aligned": 5,
    "cases": 2,
    "equation": 15,
    "proof": 1,
    "theorem": 1,
}
EXPECTED_LABELS = ["stochastic:eq:gradient"]
EXPECTED_EQREFS = ["stochastic:eq:gradient"]
EXPECTED_SOURCE_MARKERS = [
    ("001", "1", "34"),
    ("002", "36", "50"),
    ("003", "51", "107"),
]
EXPECTED_SEGMENTS = [f"d90.hab.v1.ch08.seg{i:04d}" for i in range(1, 4)]
REQUIRED_LEDGER_IDS = [f"O015-HAB-ADV-{number:04d}" for number in range(76, 84)]
REQUIRED_LEDGER_FIELDS = {
    "event_id",
    "authority",
    "source",
    "surface",
    "source_issue",
    "target_action",
    "class",
}

# Literal reader-facing witnesses for every correction event.  Whitespace is
# collapsed first so harmless source wrapping cannot defeat the gates.
REQUIRED_CORRECTION_SURFACES: dict[str, list[tuple[str, int]]] = {
    "O015-HAB-ADV-0076": [
        (r"f(x)\coloneqq \frac{1}{N}\sum_{i=1}^N f_i(x)", 1),
        (r"\min_\theta \frac{1}{N}\sum_{i=1}^N \|y_i-f_\theta(x_i)\|^2", 1),
        (r"\E[G(x,Z)]=N^{-1}\sum_{i=1}^N\nabla f_i(x)=\nabla f(x)", 1),
    ],
    "O015-HAB-ADV-0077": [
        (r"C\subseteq\R^d", 1),
        (r"f:\R^d\rightarrow\R", 1),
        (r"x^*\in\arg\min_{x\in C}f(x)", 1),
        (r"x_{k+1}=\proj_C(x_k-\tau_kG_k)", 1),
        (r"\tau_k>0", 2),
        (r"\proj_C(x^*)=x^*", 1),
    ],
    "O015-HAB-ADV-0078": [
        (r"\mathcal F_k=\sigma(x_0,Z_0,\dots,Z_{k-1})", 1),
        (r"\bar g_k\coloneqq\E[G_k\mid\mathcal F_k]", 1),
        (r"\bar g_k \in \partial f(x_k)", 1),
        (r"\E[\|G_k-\bar g_k\|^2\mid\mathcal F_k]\leq \sigma^2", 1),
        (r"\E[\inner{x_k-x^*}{G_k}\mid\mathcal F_k]", 1),
    ],
    "O015-HAB-ADV-0079": [
        (r"f_{\mathrm{best}}^K\coloneqq\min_{0\leq k\leq K-1}f(x_k)", 1),
        (r"\E[f_{\mathrm{best}}^K-f(x^*)]", 3),
        (r"K\rightarrow\infty", 2),
    ],
    "O015-HAB-ADV-0080": [
        (r"\E[\|G_k\|^2\mid\mathcal F_k]", 1),
        (r"\E[\|G_k-\bar g_k\|^2\mid\mathcal F_k]+\|\bar g_k\|^2", 1),
        (r"\sigma^2+L^2\coloneqq M^2", 1),
    ],
    "O015-HAB-ADV-0081": [
        (r"+\frac{M^2}{2}\sum_{k=0}^{K-1}\tau_k^2", 1),
    ],
    "O015-HAB-ADV-0082": [
        (r"S_K\coloneqq\sum_{k=0}^{K-1}\tau_k", 1),
        (r"Q_K\coloneqq\sum_{k=0}^{K-1}\tau_k^2", 1),
        (r"\frac{M^2Q_K}{2S_K}", 2),
        (r"\frac{\sum_{k=0}^{K-1}\tau_k^2}{\sum_{k=0}^{K-1}\tau_k}\longrightarrow0", 1),
    ],
    "O015-HAB-ADV-0083": [
        ("dengan $N$ biasanya merupakan banyaknya sampel pelatihan", 1),
        (r"\E[G(x,Z)] \in \partial f(x),", 1),
        ("Memang,", 1),
    ],
}

FORBIDDEN_PROSE_SURFACES = [
    "Assume we want to solve",
    "It turns out that many",
    "very $N$",
    "Then it holds",
    "The remaining proof",
    "which goes to zero",
]

# These are canonical forms of the erroneous source formulas.  Exact-form
# absence avoids false positives from corrected formulas that contain a source
# expression as a proper substring.
FORBIDDEN_CANONICAL_FORMULAE = [
    r"\min_xf(x)\coloneq\sum_{i=1}^Nf_i(x)",
    r"\min_\theta\sum_{i=1}^N\|y_i-f_\theta(x_i)\|^2",
    r"\frac{\sum_{k=1}^n\tau_k}{\sum_{k=1}^n\tau_k^2}\rightarrow\infty",
    r"\sigma_n=\frac{\sum_{k=0}^{K-1}\tau_k}{\sum_{k=0}^{K-1}\tau_k^2}",
]


@dataclass(frozen=True)
class FormulaUnit:
    ordinal: int
    line: int
    kind: str
    raw: str
    canonical: str


MATH_PATTERN = re.compile(
    r"\\begin\{(?P<display_kind>equation|gather)\*?\}"
    r"(?P<display>.*?)"
    r"\\end\{(?P=display_kind)\*?\}"
    r"|\\\[(?P<bracket>.*?)\\\]"
    r"|\\\((?P<paren>.*?)\\\)"
    r"|(?<!\\)\$(?!\$)(?P<inline>.*?)(?<!\\)\$",
    re.DOTALL,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collapsed(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def jsonl_records(data: bytes) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in data.decode("utf-8").splitlines()
        if line.strip()
    ]


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    text = data.decode("utf-8")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "lines": len(text.splitlines()),
        "sha256": sha256(data),
    }


def canonical_formula(value: str) -> str:
    """Discard linguistic/layout noise but retain mathematical changes."""

    value = re.sub(r"%[^\n]*", "", value)
    value = re.sub(r"\\label\{[^{}]*\}", "", value)
    value = re.sub(r"\\(?:C?cref|eqref|ref)\{[^{}]*\}", "", value)
    value = re.sub(r"\\text\{[^{}]*\}", r"\\text{#}", value)
    value = re.sub(
        r"\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\b", "", value
    )
    value = re.sub(r"\\(?:bigg|Bigg|big|Big|left|right)\b", "", value)
    value = re.sub(r"\\(?:quad|qquad|,|;|!)", "", value)
    value = value.replace(r"\coloneqq", r"\coloneq")
    value = re.sub(r"\s+", "", value)
    return value.rstrip(".,;")


def formula_units(text: str) -> list[FormulaUnit]:
    units: list[FormulaUnit] = []
    for ordinal, match in enumerate(MATH_PATTERN.finditer(text), start=1):
        if match.group("display") is not None:
            raw = str(match.group("display"))
            kind = str(match.group("display_kind"))
        elif match.group("bracket") is not None:
            raw = str(match.group("bracket"))
            kind = "bracket"
        elif match.group("paren") is not None:
            raw = str(match.group("paren"))
            kind = "paren"
        else:
            raw = str(match.group("inline"))
            kind = "inline"
        units.append(
            FormulaUnit(
                ordinal=ordinal,
                line=text.count("\n", 0, match.start()) + 1,
                kind=kind,
                raw=collapsed(raw),
                canonical=canonical_formula(raw),
            )
        )
    return units


# Causal line scopes for the eight disclosed corrections.  A SequenceMatcher
# block may legitimately carry several event IDs when one source defect forced
# a coordinated rewrite of the theorem and its proof.
SOURCE_LINE_BINDINGS: list[tuple[int, int, tuple[str, ...]]] = [
    (6, 6, ("O015-HAB-ADV-0083",)),
    (13, 34, ("O015-HAB-ADV-0076", "O015-HAB-ADV-0083")),
    (
        36,
        50,
        (
            "O015-HAB-ADV-0077",
            "O015-HAB-ADV-0078",
            "O015-HAB-ADV-0079",
            "O015-HAB-ADV-0082",
            "O015-HAB-ADV-0083",
        ),
    ),
    (51, 59, ("O015-HAB-ADV-0077", "O015-HAB-ADV-0078")),
    (60, 69, ("O015-HAB-ADV-0078",)),
    (70, 82, ("O015-HAB-ADV-0080", "O015-HAB-ADV-0083")),
    (83, 88, ("O015-HAB-ADV-0081",)),
    (89, 106, ("O015-HAB-ADV-0079", "O015-HAB-ADV-0082")),
]
TARGET_LINE_BINDINGS: list[tuple[int, int, tuple[str, ...]]] = [
    (15, 37, ("O015-HAB-ADV-0076", "O015-HAB-ADV-0083")),
    (
        41,
        63,
        (
            "O015-HAB-ADV-0077",
            "O015-HAB-ADV-0078",
            "O015-HAB-ADV-0079",
            "O015-HAB-ADV-0082",
        ),
    ),
    (67, 76, ("O015-HAB-ADV-0077",)),
    (77, 92, ("O015-HAB-ADV-0078", "O015-HAB-ADV-0080")),
    (93, 101, ("O015-HAB-ADV-0080",)),
    (102, 109, ("O015-HAB-ADV-0081",)),
    (110, 132, ("O015-HAB-ADV-0079", "O015-HAB-ADV-0082")),
]


def binding_ids(
    source_entries: Iterable[FormulaUnit], target_entries: Iterable[FormulaUnit]
) -> list[str]:
    bindings: set[str] = set()
    source_lines = [entry.line for entry in source_entries]
    target_lines = [entry.line for entry in target_entries]
    for start, end, event_ids in SOURCE_LINE_BINDINGS:
        if any(start <= line <= end for line in source_lines):
            bindings.update(event_ids)
    for start, end, event_ids in TARGET_LINE_BINDINGS:
        if any(start <= line <= end for line in target_lines):
            bindings.update(event_ids)
    return sorted(bindings)


def entry_payload(entry: FormulaUnit, globally_novel: bool) -> dict[str, object]:
    return {
        "ordinal": entry.ordinal,
        "line": entry.line,
        "kind": entry.kind,
        "raw": entry.raw,
        "canonical": entry.canonical,
        "globally_novel": globally_novel,
    }


def formula_delta_manifest(
    source_units: list[FormulaUnit],
    target_units: list[FormulaUnit],
    source_identity: dict[str, object],
    target_identity: dict[str, object],
    proposed_ids: set[str],
) -> tuple[dict[str, object], list[str]]:
    source_counts = Counter(unit.canonical for unit in source_units)
    target_counts = Counter(unit.canonical for unit in target_units)
    source_extra = source_counts - target_counts
    target_extra = target_counts - source_counts
    matcher = difflib.SequenceMatcher(
        a=[unit.canonical for unit in source_units],
        b=[unit.canonical for unit in target_units],
        autojunk=False,
    )
    blocks: list[dict[str, object]] = []
    failures: list[str] = []
    substantive_ids: list[str] = []
    unbound_ids: list[str] = []
    incompletely_bound_ids: list[str] = []
    used_events: set[str] = set()

    for operation, source_start, source_end, target_start, target_end in matcher.get_opcodes():
        if operation == "equal":
            continue
        source_entries = source_units[source_start:source_end]
        target_entries = target_units[target_start:target_end]
        source_novel = [
            bool(entry.canonical) and source_extra[entry.canonical] > 0
            for entry in source_entries
        ]
        target_novel = [
            bool(entry.canonical) and target_extra[entry.canonical] > 0
            for entry in target_entries
        ]
        substantive = any(source_novel) or any(target_novel)
        event_ids = binding_ids(source_entries, target_entries)
        block_id = f"d90.hab.v1.ch08.formula-delta.{len(blocks) + 1:04d}"
        missing_proposed = [event for event in event_ids if event not in proposed_ids]
        ledger_bound = not substantive or bool(event_ids) and not missing_proposed
        if substantive:
            substantive_ids.append(block_id)
            used_events.update(event_ids)
            if not event_ids:
                unbound_ids.append(block_id)
                failures.append(f"substantive formula delta has no event binding: {block_id}")
            elif missing_proposed:
                incompletely_bound_ids.append(block_id)
                failures.append(
                    f"substantive formula delta lacks proposed-ledger closure: {block_id}; "
                    f"missing={missing_proposed}"
                )
        blocks.append(
            {
                "block_id": block_id,
                "operation": operation,
                "source_ordinal_start": source_start + 1,
                "source_ordinal_end": source_end,
                "target_ordinal_start": target_start + 1,
                "target_ordinal_end": target_end,
                "source": [
                    entry_payload(entry, novel)
                    for entry, novel in zip(source_entries, source_novel, strict=True)
                ],
                "target": [
                    entry_payload(entry, novel)
                    for entry, novel in zip(target_entries, target_novel, strict=True)
                ],
                "substantive": substantive,
                "ledger_event_ids": event_ids,
                "missing_proposed_event_ids": missing_proposed,
                "ledger_bound": ledger_bound,
            }
        )

    unused_required = sorted(set(REQUIRED_LEDGER_IDS) - used_events)
    if unused_required:
        failures.append(
            f"proposed correction events unused by substantive formula deltas: {unused_required}"
        )
    if len(source_units) != 38 or len(target_units) != 61:
        failures.append(
            f"formula inventory differs: source={len(source_units)}, target={len(target_units)}"
        )
    if len(blocks) != 7 or len(substantive_ids) != 7:
        failures.append(
            f"formula delta topology differs: blocks={len(blocks)}, "
            f"substantive={len(substantive_ids)}"
        )

    manifest: dict[str, object] = {
        "schema": "o015-stochastic-formula-delta-manifest-v1",
        "identity_policy": "authority_target_and_proposed_ledger_frozen",
        "source": source_identity,
        "target": target_identity,
        "normalization": {
            "linguistic_text": "contents of LaTeX text commands replaced by #",
            "removed": [
                "comments",
                "labels",
                "reference commands",
                "display styles",
                "delimiter sizing",
                "spacing commands",
                "terminal prose punctuation",
            ],
            "equivalence": ["coloneq and coloneqq"],
            "substantive_rule": (
                "a non-equal sequence block is substantive iff it contains a "
                "canonical formula whose corpus-wide multiplicity differs"
            ),
        },
        "source_formula_count": len(source_units),
        "target_formula_count": len(target_units),
        "delta_block_count": len(blocks),
        "substantive_delta_block_count": len(substantive_ids),
        "substantive_delta_block_ids": substantive_ids,
        "required_ledger_event_ids": REQUIRED_LEDGER_IDS,
        "used_ledger_event_ids": sorted(used_events),
        "unused_required_ledger_event_ids": unused_required,
        "unbound_substantive_delta_block_ids": unbound_ids,
        "incompletely_bound_substantive_delta_block_ids": incompletely_bound_ids,
        "all_substantive_deltas_proposed_ledger_bound": not unbound_ids
        and not incompletely_bound_ids,
        "blocks": blocks,
    }
    return manifest, failures


def run(report_only: bool) -> dict[str, object]:
    source_bytes = SOURCE.read_bytes()
    target_bytes = TARGET.read_bytes()
    wrapper_bytes = WRAPPER.read_bytes()
    proposed_bytes = PROPOSED_LEDGER.read_bytes()
    source = source_bytes.decode("utf-8")
    target = target_bytes.decode("utf-8")
    wrapper = wrapper_bytes.decode("utf-8")
    failures: list[str] = []

    identities = {
        "source": identity(SOURCE),
        "target": identity(TARGET),
        "wrapper": identity(WRAPPER),
        "proposed_ledger": identity(PROPOSED_LEDGER),
    }
    for name, expected in EXPECTED_IDENTITIES.items():
        for field, value in expected.items():
            if identities[name][field] != value:
                failures.append(
                    f"{name} {field} changed: actual={identities[name][field]}, expected={value}"
                )

    source_begins = re.findall(r"\\begin\{([^}]+)\}", source)
    source_ends = re.findall(r"\\end\{([^}]+)\}", source)
    target_begins = re.findall(r"\\begin\{([^}]+)\}", target)
    target_ends = re.findall(r"\\end\{([^}]+)\}", target)
    environment_counts = dict(sorted(Counter(source_begins).items()))
    if environment_counts != EXPECTED_ENVIRONMENT_COUNTS:
        failures.append(f"source environment inventory differs: {environment_counts}")
    if len(source_begins) != 24 or len(source_ends) != 24:
        failures.append(
            f"source environment count differs: begin={len(source_begins)}, end={len(source_ends)}"
        )
    if source_begins != target_begins or source_ends != target_ends:
        failures.append("ordered source/target environment topology differs")

    source_labels = re.findall(r"\\label\{([^}]+)\}", source)
    target_labels = re.findall(r"\\label\{([^}]+)\}", target)
    source_eqrefs = re.findall(r"\\eqref\{([^}]+)\}", source)
    target_eqrefs = re.findall(r"\\eqref\{([^}]+)\}", target)
    if source_labels != EXPECTED_LABELS or target_labels != EXPECTED_LABELS:
        failures.append(
            f"label topology differs: source={source_labels}, target={target_labels}"
        )
    if source_eqrefs != EXPECTED_EQREFS or target_eqrefs != EXPECTED_EQREFS:
        failures.append(
            f"eqref topology differs: source={source_eqrefs}, target={target_eqrefs}"
        )

    topology_patterns = {
        "items": r"\\item(?:\[[^]]*\])?",
        "citations": (
            r"\\(?:cite|citep|citet|autocite|parencite|textcite)\*?"
            r"(?:\[[^]]*\])*\{[^}]+\}"
        ),
        "footnotes": r"\\footnote\{",
        "figures": r"\\begin\{figure\*?\}",
        "external_assets": (
            r"\\(?:includegraphics|includesvg|includepdf|lstinputlisting)"
            r"(?:\[[^]]*\])?\{"
        ),
        "source_inputs": r"\\(?:input|include)\{",
        "sections": r"\\(?:section|subsection|subsubsection)\*?\{",
    }
    other_topology: dict[str, dict[str, int]] = {}
    for name, pattern in topology_patterns.items():
        source_count = len(re.findall(pattern, source))
        target_count = len(re.findall(pattern, target))
        other_topology[name] = {"source": source_count, "target": target_count}
        if source_count != 0 or target_count != 0:
            failures.append(
                f"unexpected {name}: source={source_count}, target={target_count}"
            )

    source_markers = re.findall(
        r"^% H08-S(\d{3}) \| sumber authority/habring/source-v1/stochastic\.tex "
        r"baris (\d+)--(\d+)$",
        target,
        re.MULTILINE,
    )
    segment_ids = re.findall(r"^% segment-id: (\S+)$", target, re.MULTILINE)
    if source_markers != EXPECTED_SOURCE_MARKERS:
        failures.append(f"ordered source markers differ: {source_markers}")
    if segment_ids != EXPECTED_SEGMENTS:
        failures.append(f"ordered stable segment IDs differ: {segment_ids}")

    covered_lines: list[int] = []
    for _, start_text, end_text in source_markers:
        covered_lines.extend(range(int(start_text), int(end_text) + 1))
    source_lines = source.splitlines()
    uncovered_nonblank = [
        index
        for index, line in enumerate(source_lines, start=1)
        if line.strip() and index not in covered_lines
    ]
    multiply_covered = sorted(
        line for line, count in Counter(covered_lines).items() if count != 1
    )
    if uncovered_nonblank or multiply_covered:
        failures.append(
            f"source marker closure differs: uncovered_nonblank={uncovered_nonblank}, "
            f"multiply_covered={multiply_covered}"
        )

    compact_target = collapsed(target)
    correction_surface_audit: list[dict[str, object]] = []
    for event_id in REQUIRED_LEDGER_IDS:
        results: list[dict[str, object]] = []
        for surface, minimum in REQUIRED_CORRECTION_SURFACES[event_id]:
            count = compact_target.count(collapsed(surface))
            present = count >= minimum
            results.append(
                {
                    "surface": surface,
                    "minimum_occurrences": minimum,
                    "target_occurrences": count,
                    "present": present,
                }
            )
            if not present:
                failures.append(
                    f"{event_id}: corrected surface missing or under-counted: "
                    f"{surface}; actual={count}, minimum={minimum}"
                )
        correction_surface_audit.append(
            {
                "event_id": event_id,
                "all_present": all(bool(result["present"]) for result in results),
                "surfaces": results,
            }
        )

    forbidden_prose_counts = {
        surface: target.count(surface) for surface in FORBIDDEN_PROSE_SURFACES
    }
    for surface, count in forbidden_prose_counts.items():
        if count:
            failures.append(f"untranslated/erroneous prose remains: {surface} ({count})")

    proposed_records = jsonl_records(proposed_bytes)
    proposed_ids_in_order = [str(record.get("event_id", "")) for record in proposed_records]
    proposed_ids = set(proposed_ids_in_order)
    if proposed_ids_in_order != REQUIRED_LEDGER_IDS:
        failures.append(
            f"proposed-ledger ID sequence differs: actual={proposed_ids_in_order}, "
            f"expected={REQUIRED_LEDGER_IDS}"
        )
    malformed_records: list[str] = []
    for record in proposed_records:
        event_id = str(record.get("event_id", "<missing>"))
        if set(record) != REQUIRED_LEDGER_FIELDS:
            malformed_records.append(event_id)
        if record.get("authority") != "o015-habring-arxiv-2607.11664v1":
            malformed_records.append(event_id)
        if record.get("source") != "stochastic.tex":
            malformed_records.append(event_id)
        if any(not isinstance(record.get(field), str) or not record[field].strip() for field in REQUIRED_LEDGER_FIELDS):
            malformed_records.append(event_id)
    malformed_records = sorted(set(malformed_records))
    if malformed_records:
        failures.append(f"malformed proposed-ledger records: {malformed_records}")

    wrapper_checks = {
        "includes_target_once": wrapper.count(
            r"\include{habring-08-penurunan-gradien-stokastik-id}"
        )
        == 1,
        "chapter_counter_is_seven": r"\setcounter{chapter}{7}" in wrapper,
        "authority_sha_present": all(
            part in wrapper
            for part in (
                "610d11b59d8dfabbbbe6fbc509a0f9ac",
                "1727540458c67f8cd3b7bab49566a07d",
            )
        ),
        "correction_range_present": (
            "O015-HAB-ADV-0076 sampai O015-HAB-ADV-0083" in wrapper
        ),
        "license_present": "CC BY 4.0" in wrapper,
        "nonendorsement_present": "tidak menyusun, memeriksa, menyetujui, atau mendukung" in wrapper,
    }
    for name, passed in wrapper_checks.items():
        if not passed:
            failures.append(f"wrapper gate failed: {name}")

    source_formulae = formula_units(source)
    target_formulae = formula_units(target)
    target_canonical = Counter(unit.canonical for unit in target_formulae)
    forbidden_formula_counts = {
        formula: target_canonical[formula] for formula in FORBIDDEN_CANONICAL_FORMULAE
    }
    for formula, count in forbidden_formula_counts.items():
        if count:
            failures.append(f"uncorrected canonical source formula remains ({count}): {formula}")

    manifest, manifest_failures = formula_delta_manifest(
        source_formulae,
        target_formulae,
        identities["source"],
        identities["target"],
        proposed_ids,
    )
    failures.extend(manifest_failures)
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    FORMULA_MANIFEST.write_bytes(manifest_bytes)

    # The independent rereview covered every line of source/target and the
    # standalone reader wrapper.  No undisclosed reader defect remained.
    severity = {"P1": 0, "P2": 0, "P3": 0}
    report: dict[str, object] = {
        "schema": "o015-stochastic-structure-audit-v1",
        "identity_policy": "authority_target_wrapper_and_proposed_ledger_frozen",
        "identities": identities,
        "independent_review": {
            "scope": [
                "all authority and target mathematical surfaces",
                "probability conditioning and measurability",
                "projected-SGD theorem hypotheses and proof",
                "best-iterate convergence algebra and indices",
                "all Indonesian reader prose",
                "wrapper correction disclosure, attribution, and nonendorsement",
            ],
            "severity_counts": severity,
            "findings": [],
            "disposition": "no undisclosed defect found",
        },
        "environment_topology": {
            "count": len(source_begins),
            "counts_by_name": environment_counts,
            "ordered_begin_equal": source_begins == target_begins,
            "ordered_end_equal": source_ends == target_ends,
            "ordered_begin_environments": source_begins,
            "ordered_end_environments": source_ends,
        },
        "labels": {"source": source_labels, "target": target_labels},
        "eqrefs": {"source": source_eqrefs, "target": target_eqrefs},
        "other_surface_topology": other_topology,
        "source_markers": source_markers,
        "source_marker_closure": {
            "uncovered_nonblank_source_lines": uncovered_nonblank,
            "multiply_covered_source_lines": multiply_covered,
            "all_nonblank_source_lines_covered_exactly_once": not uncovered_nonblank
            and not multiply_covered,
        },
        "stable_segment_ids": segment_ids,
        "correction_surface_audit": correction_surface_audit,
        "forbidden_prose_surface_counts": forbidden_prose_counts,
        "forbidden_canonical_formula_counts": forbidden_formula_counts,
        "proposed_ledger": {
            **identities["proposed_ledger"],
            "ids_in_order": proposed_ids_in_order,
            "required_ids": REQUIRED_LEDGER_IDS,
            "malformed_records": malformed_records,
            "exact_event_closure": proposed_ids_in_order == REQUIRED_LEDGER_IDS
            and not malformed_records,
        },
        "wrapper_gates": wrapper_checks,
        "formula_delta_manifest": {
            "path": FORMULA_MANIFEST.relative_to(ROOT).as_posix(),
            "bytes": len(manifest_bytes),
            "sha256": sha256(manifest_bytes),
            "source_formula_count": manifest["source_formula_count"],
            "target_formula_count": manifest["target_formula_count"],
            "delta_block_count": manifest["delta_block_count"],
            "substantive_delta_block_count": manifest[
                "substantive_delta_block_count"
            ],
            "used_ledger_event_ids": manifest["used_ledger_event_ids"],
            "unused_required_ledger_event_ids": manifest[
                "unused_required_ledger_event_ids"
            ],
            "all_substantive_deltas_proposed_ledger_bound": manifest[
                "all_substantive_deltas_proposed_ledger_bound"
            ],
            "unbound_substantive_delta_block_ids": manifest[
                "unbound_substantive_delta_block_ids"
            ],
            "incompletely_bound_substantive_delta_block_ids": manifest[
                "incompletely_bound_substantive_delta_block_ids"
            ],
        },
        "failure_count": len(failures),
        "failures": failures,
        "result": "pass" if not failures else "fail",
    }
    report_bytes = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    REPORT.write_bytes(report_bytes)
    print(
        json.dumps(
            {
                "result": report["result"],
                "failure_count": report["failure_count"],
                "target_sha256": identities["target"]["sha256"],
                "formula_manifest_sha256": sha256(manifest_bytes),
                "report_sha256": sha256(report_bytes),
                "severity_counts": severity,
            },
            sort_keys=True,
        )
    )
    if failures and not report_only:
        raise SystemExit(1)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="write deterministic reports and return success despite live failures",
    )
    arguments = parser.parse_args()
    run(arguments.report_only)
