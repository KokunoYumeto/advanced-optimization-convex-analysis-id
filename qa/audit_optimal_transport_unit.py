"""Deterministic admission audit for Habring Chapter 9 in Indonesian.

The audit is deliberately bounded to the frozen Chapter 9 authority, frozen
reader target, standalone wrapper, proposed correction ledger, and live
integrated adverse ledger.  It never edits those inputs.  It writes only the
two declared JSON QA outputs.

Report-only mode admits a structurally complete unit while the twelve proposed
correction records are still awaiting integration.  Strict mode additionally
requires byte-exact integration of those records into the adverse ledger.
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
SOURCE = ROOT / "authority" / "habring" / "source-v1" / "optimal_transport.tex"
TARGET = (
    ROOT / "source" / "id-ID" / "habring-09-transportasi-optimal-id.tex"
)
WRAPPER = (
    ROOT
    / "source"
    / "id-ID"
    / "D90-HAB-09-transportasi-optimal-id.tex"
)
LOCAL_BIBLIOGRAPHY = ROOT / "source" / "id-ID" / "references-ot-id.bib"
PROPOSED_LEDGER = ROOT / "qa" / "CHAPTER09_PROPOSED_LEDGER.jsonl"
INTEGRATED_LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
FORMULA_MANIFEST = ROOT / "qa" / "OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json"
REPORT = ROOT / "qa" / "OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json"

EXPECTED_IDENTITIES = {
    "source": {
        "bytes": 15_378,
        "lines": 264,
        "sha256": "719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba",
    },
    "target": {
        "bytes": 21_252,
        "lines": 352,
        "sha256": "45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd",
    },
    "wrapper": {
        "bytes": 6_822,
        "lines": 87,
        "sha256": "1e308a2bed0d1a6f5cdcff09cce932674cf32842a135bc88a5a34bc96c483ff6",
    },
    "local_bibliography": {
        "bytes": 306,
        "lines": 9,
        "sha256": "93611c4b6a753478c51c601e59ef6cd3e290677e2e2d25b104d5d3b74df03126",
    },
    "proposed_ledger": {
        "bytes": 8_840,
        "lines": 12,
        "sha256": "643fde3fbe1409732ef2df8fdef52465e4df7a583fd9bbeb2137a6122f548add",
    },
}

EXPECTED_ENVIRONMENT_COUNT = 47
EXPECTED_ENVIRONMENT_COUNTS = {
    "aligned": 7,
    "cases": 3,
    "defn": 4,
    "enumerate": 1,
    "equation": 22,
    "figure": 1,
    "lemma": 1,
    "proof": 3,
    "quote": 1,
    "rem": 1,
    "theorem": 2,
    "tikzpicture": 1,
}
EXPECTED_LABELS = [
    "ot:fig:ot",
    "ot:eq:monge",
    "ot:eq:K_ot",
    "ot:eq:duality",
    "ot:eq:disc_entropic",
]
EXPECTED_SOURCE_EQREFS = [
    "ot:eq:K_ot",
    "ot:eq:monge",
    "ot:eq:K_ot",
    "ot:eq:K_ot",
    "ot:eq:K_ot",
    "ot:eq:duality",
    "ot:eq:K_ot",
    "ot:eq:disc_entropic",
]
EXPECTED_TARGET_EQREFS = [
    *EXPECTED_SOURCE_EQREFS,
    "ot:eq:disc_entropic",
]
EXPECTED_CREFS = ["chapter:duality"]
EXPECTED_SOURCE_CITATIONS = [
    ("villani2009optimal", "Theorem 4.1"),
]
EXPECTED_TARGET_CITATIONS = [
    ("villani2009optimal", "Theorem 4.1"),
    ("villani2009optimal", "Theorem 5.10"),
]
EXPECTED_SOURCE_MARKERS = [
    ("001", "1", "15"),
    ("002", "16", "75"),
    ("003", "77", "110"),
    ("004", "112", "130"),
    ("005", "131", "141"),
    ("006", "142", "190"),
    ("007", "192", "226"),
    ("008", "229", "256"),
    ("009", "257", "264"),
]
EXPECTED_SEGMENTS = [
    f"d90.hab.v1.ch09.seg{number:04d}" for number in range(1, 10)
]
REQUIRED_LEDGER_IDS = [
    f"O015-HAB-ADV-{number:04d}" for number in range(84, 96)
]
WRAPPER_LEDGER_EVENT = {
    "event_id": "O015-HAB-ADV-0096",
    "authority": "o015-habring-arxiv-2607.11664v1",
    "source": "references.bib",
    "surface": "Villani bibliography author metadata and rendered name",
    "source_issue": (
        "The frozen bibliography records the sole-authored book as "
        + chr(96)
        + "Villani, Cédric and others"
        + chr(96)
        + "; BibLaTeX consequently renders the visible citation and "
        "bibliography name as "
        + chr(96)
        + "Villani andothers"
        + chr(96)
        + ", while the publisher's primary metadata identifies Cédric "
        "Villani as the sole author."
    ),
    "target_action": (
        "Kept the frozen authority file unchanged, supplied a unit-local "
        "corrected bibliography entry naming Cédric Villani as sole author "
        "and adding the publisher DOI, and bound the standalone wrapper to "
        "that corrected metadata."
    ),
    "class": "determined_bibliographic_metadata_and_rendering_correction",
}
REQUIRED_LEDGER_FIELDS = {
    "event_id",
    "authority",
    "source",
    "surface",
    "source_issue",
    "target_action",
    "class",
}

# Reader-facing witnesses for every disclosed correction.  Whitespace is
# collapsed before counting, so line wrapping cannot weaken the gates.
REQUIRED_CORRECTION_SURFACES: dict[str, list[tuple[str, int]]] = {
    "O015-HAB-ADV-0084": [
        (r"$(X,\Sigma_X)$ dan $(Y,\Sigma_Y)$ adalah ruang terukur", 1),
        (r"$T:X\rightarrow Y$ terukur", 1),
        (r"untuk setiap $A\in\Sigma_Y$", 2),
        (r"ruang hasil kali terukur $X\times Y$", 1),
    ],
    "O015-HAB-ADV-0085": [
        (r"$\Mc_+(X)$ dan $\Mc_+(Y)$", 1),
        (r"ukuran bertanda $\mu$ pada $X$", 1),
        (r"ukuran tak negatif bernilai dalam $[0,\infty)$", 1),
        (r"suatu aljabar-$\sigma$", 1),
    ],
    "O015-HAB-ADV-0086": [
        (
            r"\inf_{\substack{T:X\rightarrow Y\ \mathrm{terukur}\\T_\sharp\alpha=\beta}}",
            1,
        ),
        (r"\inf\emptyset\coloneqq+\infty", 1),
        ("fungsi biaya terukur yang terbatas dari bawah", 2),
    ],
    "O015-HAB-ADV-0087": [
        (r"$Y\subseteq\R^q$", 1),
        (
            r"Hal ini khususnya menyiratkan bahwa $\beta$ tidak mempunyai massa titik.",
            1,
        ),
    ],
    "O015-HAB-ADV-0088": [
        ("ruang Polish yang dilengkapi aljabar-$\\sigma$ Borelnya", 1),
        ("keluarga kopling dengan kedua marginal tetap juga ketat", 1),
        ("teorema Prokhorov", 1),
        (r"Himpunan $\Pi(\alpha,\beta)$ tertutup", 1),
    ],
    "O015-HAB-ADV-0089": [
        (r"Misalkan $(X,d)$ ruang metrik Polish", 1),
        (
            r"$\Pc_p(X)\coloneqq\{\mu\in\Pc(X):\int d(x,x_0)^p\dd\mu(x)<\infty\}$",
            1,
        ),
        (r"biaya $c(x,y)=d(x,y)^p$", 1),
        ("metrik pada ruang ukuran probabilitas bermomen ke-$p$ hingga", 1),
    ],
    "O015-HAB-ADV-0090": [
        (r"$c:X\times Y\rightarrow[0,\infty]$ semikontinu bawah", 1),
        (r"$C_b(X)$ dan $C_b(Y)$", 1),
        (r"\phi(x)+\psi(y)\leq c(x,y)\ \forall(x,y)", 2),
    ],
    "O015-HAB-ADV-0091": [
        (
            "Ukuran Borel hingga yang berbeda pada ruang Polish dapat dipisahkan",
            1,
        ),
        (r"\inf_{\gamma\in\Mc_+(X\times Y)}", 3),
        (r"\cite[Theorem 5.10]{villani2009optimal}", 1),
        ("skalakan massa Dirac pada titik pelanggaran", 1),
    ],
    "O015-HAB-ADV-0092": [
        (r"$a=(a_1,\dots,a_n)\in\Delta_n$", 1),
        (r"$b=(b_1,\dots,b_m)\in\Delta_m$", 1),
        (r"$P\1_m=a$ dan $P^\top\1_n=b$", 1),
        (
            r"P\1_m=a,\quad P^\top\1_n=b,\quad P_{i,j}\geq0",
            1,
        ),
    ],
    "O015-HAB-ADV-0093": [
        (r"$C\in\R^{n\times m}$", 2),
        (r"$0\log0=0$", 1),
        (r"$E(P)=+\infty$", 1),
        (r"Untuk $\epsilon>0$", 1),
        (r"\min_{P\in\R_+^{n\times m}}", 1),
    ],
    "O015-HAB-ADV-0094": [
        (r"$Q=ab^\top$ layak", 1),
        ("bersifat konveks ketat", 2),
        (
            r"\frac{\dd}{\dd t}h(tQ_{i,j})=Q_{i,j}\log(tQ_{i,j})",
            1,
        ),
        (r"$P_{i,j}>0$ untuk semua $i,j$", 1),
        (
            r"Vektor penskalaan $(u,v)$ unik hingga transformasi $(u,v)\mapsto(tu,t^{-1}v)$",
            1,
        ),
    ],
    "O015-HAB-ADV-0095": [
        (r"Pilih $v_0\in\R_{++}^m$", 1),
        (r"$k=0,1,2,\dots$", 1),
        ("semua penyebut dan iterat tetap positif", 1),
        ("konvergen ke rencana unik", 1),
        (r"ambiguitas perkalian $(u,v)\mapsto(tu,t^{-1}v)$", 1),
    ],
}

FORBIDDEN_TARGET_SURFACES = [
    "We can no formally introduce",
    r"\min_{T:X\rightarrow Y} \int c(x,T(x))",
    r"\Mc_+(\alpha,\beta)",
    r"for some $a_i\in \Delta_n$",
    r"\diag(v)K^t u\1",
    r"where we update for $k=1,2,\dots$",
    "finite $p$-th.",
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
    """Remove linguistic and layout noise while retaining mathematics."""

    value = re.sub(r"%[^\n]*", "", value)
    value = re.sub(r"\\label\{[^{}]*\}", "", value)
    value = re.sub(r"\\(?:C?cref|eqref|ref)\{[^{}]*\}", "", value)
    value = re.sub(r"\\text\{[^{}]*\}", r"\\text{#}", value)
    value = re.sub(
        r"\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\b",
        "",
        value,
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


# Causal scopes for disclosed mathematical changes.  SequenceMatcher may place
# several adjacent formula changes in one block, so union bindings are normal.
SOURCE_LINE_BINDINGS: list[tuple[int, int, tuple[str, ...]]] = [
    (1, 15, ("O015-HAB-ADV-0084", "O015-HAB-ADV-0085")),
    (16, 75, ("O015-HAB-ADV-0084",)),
    (
        77,
        110,
        (
            "O015-HAB-ADV-0084",
            "O015-HAB-ADV-0086",
            "O015-HAB-ADV-0087",
        ),
    ),
    (112, 130, ("O015-HAB-ADV-0088", "O015-HAB-ADV-0089")),
    (131, 141, ("O015-HAB-ADV-0090",)),
    (142, 190, ("O015-HAB-ADV-0091",)),
    (192, 226, ("O015-HAB-ADV-0092", "O015-HAB-ADV-0093")),
    (229, 256, ("O015-HAB-ADV-0094",)),
    (257, 264, ("O015-HAB-ADV-0095",)),
]
TARGET_LINE_BINDINGS: list[tuple[int, int, tuple[str, ...]]] = [
    (1, 17, ("O015-HAB-ADV-0084", "O015-HAB-ADV-0085")),
    (18, 82, ("O015-HAB-ADV-0084",)),
    (
        85,
        123,
        (
            "O015-HAB-ADV-0084",
            "O015-HAB-ADV-0086",
            "O015-HAB-ADV-0087",
        ),
    ),
    (126, 146, ("O015-HAB-ADV-0088", "O015-HAB-ADV-0089")),
    (149, 163, ("O015-HAB-ADV-0090",)),
    (166, 230, ("O015-HAB-ADV-0091",)),
    (233, 272, ("O015-HAB-ADV-0092", "O015-HAB-ADV-0093")),
    (275, 332, ("O015-HAB-ADV-0094",)),
    (336, 352, ("O015-HAB-ADV-0095",)),
]


def binding_ids(
    source_entries: Iterable[FormulaUnit],
    target_entries: Iterable[FormulaUnit],
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
    integrated_ids: set[str],
) -> tuple[dict[str, object], list[str], list[str]]:
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
    content_failures: list[str] = []
    strict_failures: list[str] = []
    substantive_ids: list[str] = []
    unbound_ids: list[str] = []
    proposal_incomplete_ids: list[str] = []
    integration_incomplete_ids: list[str] = []
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
        block_id = f"d90.hab.v1.ch09.formula-delta.{len(blocks) + 1:04d}"
        missing_proposed = [event for event in event_ids if event not in proposed_ids]
        missing_integrated = [
            event for event in event_ids if event not in integrated_ids
        ]
        proposed_bound = (
            not substantive or bool(event_ids) and not missing_proposed
        )
        integrated_bound = (
            not substantive or bool(event_ids) and not missing_integrated
        )
        if substantive:
            substantive_ids.append(block_id)
            used_events.update(event_ids)
            if not event_ids:
                unbound_ids.append(block_id)
                content_failures.append(
                    f"substantive formula delta has no correction disposition: {block_id}"
                )
            elif missing_proposed:
                proposal_incomplete_ids.append(block_id)
                content_failures.append(
                    f"substantive formula delta lacks proposed-ledger closure: "
                    f"{block_id}; missing={missing_proposed}"
                )
            if missing_integrated:
                integration_incomplete_ids.append(block_id)
                strict_failures.append(
                    f"substantive formula delta lacks integrated-ledger closure: "
                    f"{block_id}; missing={missing_integrated}"
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
                    for entry, novel in zip(
                        source_entries, source_novel, strict=True
                    )
                ],
                "target": [
                    entry_payload(entry, novel)
                    for entry, novel in zip(
                        target_entries, target_novel, strict=True
                    )
                ],
                "substantive": substantive,
                "disposition": (
                    "correction-ledger-bound"
                    if substantive
                    else "sequence-only-no-corpus-wide-formula-change"
                ),
                "ledger_event_ids": event_ids,
                "missing_proposed_event_ids": missing_proposed,
                "missing_integrated_event_ids": missing_integrated,
                "proposed_ledger_bound": proposed_bound,
                "integrated_ledger_bound": integrated_bound,
                "strict_ledger_bound": proposed_bound and integrated_bound,
            }
        )

    if len(source_units) != 162 or len(target_units) != 232:
        content_failures.append(
            f"formula inventory differs: source={len(source_units)}, "
            f"target={len(target_units)}"
        )
    if len(blocks) != 35 or len(substantive_ids) != 34:
        content_failures.append(
            f"formula delta topology differs: blocks={len(blocks)}, "
            f"substantive={len(substantive_ids)}"
        )

    unused_events = sorted(set(REQUIRED_LEDGER_IDS) - used_events)
    manifest: dict[str, object] = {
        "schema": "o015-optimal-transport-formula-delta-manifest-v1",
        "identity_policy": (
            "authority_and_final_target_frozen_ledgers_derived_live"
        ),
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
        "unused_required_ledger_event_ids": unused_events,
        "unbound_substantive_delta_block_ids": unbound_ids,
        "proposal_incomplete_substantive_delta_block_ids": proposal_incomplete_ids,
        "integration_incomplete_substantive_delta_block_ids": (
            integration_incomplete_ids
        ),
        "all_substantive_deltas_proposed_ledger_bound": (
            not unbound_ids and not proposal_incomplete_ids
        ),
        "all_substantive_deltas_integrated_ledger_bound": (
            not unbound_ids and not integration_incomplete_ids
        ),
        "blocks": blocks,
    }
    return manifest, content_failures, strict_failures


def run(report_only: bool) -> dict[str, object]:
    source_bytes = SOURCE.read_bytes()
    target_bytes = TARGET.read_bytes()
    wrapper_bytes = WRAPPER.read_bytes()
    local_bibliography_bytes = LOCAL_BIBLIOGRAPHY.read_bytes()
    proposed_bytes = PROPOSED_LEDGER.read_bytes()
    integrated_bytes = INTEGRATED_LEDGER.read_bytes()
    source = source_bytes.decode("utf-8")
    target = target_bytes.decode("utf-8")
    wrapper = wrapper_bytes.decode("utf-8")
    local_bibliography = local_bibliography_bytes.decode("utf-8")
    content_failures: list[str] = []
    strict_only_failures: list[str] = []

    identities = {
        "source": identity(SOURCE),
        "target": identity(TARGET),
        "wrapper": identity(WRAPPER),
        "local_bibliography": identity(LOCAL_BIBLIOGRAPHY),
        "proposed_ledger": identity(PROPOSED_LEDGER),
    }
    for name, expected in EXPECTED_IDENTITIES.items():
        for field, expected_value in expected.items():
            actual_value = identities[name][field]
            if actual_value != expected_value:
                content_failures.append(
                    f"{name} {field} changed: actual={actual_value}, "
                    f"expected={expected_value}"
                )

    source_begins = re.findall(r"\\begin\{([^}]+)\}", source)
    source_ends = re.findall(r"\\end\{([^}]+)\}", source)
    target_begins = re.findall(r"\\begin\{([^}]+)\}", target)
    target_ends = re.findall(r"\\end\{([^}]+)\}", target)
    environment_counts = dict(sorted(Counter(source_begins).items()))
    if len(source_begins) != EXPECTED_ENVIRONMENT_COUNT:
        content_failures.append(
            f"source begin-environment count differs: {len(source_begins)}"
        )
    if len(source_ends) != EXPECTED_ENVIRONMENT_COUNT:
        content_failures.append(
            f"source end-environment count differs: {len(source_ends)}"
        )
    if environment_counts != EXPECTED_ENVIRONMENT_COUNTS:
        content_failures.append(
            f"source environment inventory differs: {environment_counts}"
        )
    if source_begins != target_begins:
        content_failures.append("ordered begin-environment topology differs")
    if source_ends != target_ends:
        content_failures.append("ordered end-environment topology differs")

    source_labels = re.findall(r"\\label\{([^}]+)\}", source)
    target_labels = re.findall(r"\\label\{([^}]+)\}", target)
    if source_labels != EXPECTED_LABELS or target_labels != EXPECTED_LABELS:
        content_failures.append(
            f"label topology differs: source={source_labels}, "
            f"target={target_labels}"
        )
    if len(target_labels) != len(set(target_labels)):
        content_failures.append("duplicate target label remains")

    reference_patterns = {
        "ref": r"\\ref\{([^}]+)\}",
        "cref": r"\\cref\{([^}]+)\}",
        "Cref": r"\\Cref\{([^}]+)\}",
        "eqref": r"\\eqref\{([^}]+)\}",
    }
    source_references = {
        name: re.findall(pattern, source)
        for name, pattern in reference_patterns.items()
    }
    target_references = {
        name: re.findall(pattern, target)
        for name, pattern in reference_patterns.items()
    }
    expected_source_references = {
        "ref": [],
        "cref": EXPECTED_CREFS,
        "Cref": [],
        "eqref": EXPECTED_SOURCE_EQREFS,
    }
    expected_target_references = {
        **expected_source_references,
        "eqref": EXPECTED_TARGET_EQREFS,
    }
    if source_references != expected_source_references:
        content_failures.append(
            f"source reference topology differs: {source_references}"
        )
    if target_references != expected_target_references:
        content_failures.append(
            f"target reference topology differs: {target_references}"
        )

    citation_pattern = re.compile(
        r"\\(?:cite|citep|citet|autocite|parencite|textcite)\*?"
        r"(?:\[([^]]*)\])*\{([^}]+)\}"
    )
    source_citations = [
        (key, note) for note, key in citation_pattern.findall(source)
    ]
    target_citations = [
        (key, note) for note, key in citation_pattern.findall(target)
    ]
    if source_citations != EXPECTED_SOURCE_CITATIONS:
        content_failures.append(
            f"source citation topology differs: {source_citations}"
        )
    if target_citations != EXPECTED_TARGET_CITATIONS:
        content_failures.append(
            f"target citation topology differs: {target_citations}"
        )

    source_items = re.findall(r"\\item(?:\[([^]]*)\])?", source)
    target_items = re.findall(r"\\item(?:\[([^]]*)\])?", target)
    if len(source_items) != 2 or target_items != source_items:
        content_failures.append(
            f"item topology differs: source={source_items}, target={target_items}"
        )

    topology_expected = {
        "footnotes": (r"\\footnote\{", 3, 3),
        "glossary_surfaces": (r"\\gls\{ot\}", 14, 14),
        "figure_environments": (r"\\begin\{figure\*?\}", 1, 1),
        "tikz_environments": (r"\\begin\{tikzpicture\}", 1, 1),
        "sections": (
            r"\\(?:section|subsection|subsubsection)\*?\{",
            3,
            3,
        ),
        "abbreviations": (r"\\newabbreviation\{ot\}", 1, 1),
        "external_assets": (
            r"\\(?:includegraphics|includesvg|includepdf|lstinputlisting)"
            r"(?:\[[^]]*\])?\{",
            0,
            0,
        ),
        "source_inputs": (r"\\(?:input|include)\{", 0, 0),
    }
    topology_counts: dict[str, dict[str, int]] = {}
    for name, (pattern, expected_source, expected_target) in topology_expected.items():
        source_count = len(re.findall(pattern, source))
        target_count = len(re.findall(pattern, target))
        topology_counts[name] = {
            "source": source_count,
            "target": target_count,
        }
        if (
            source_count != expected_source
            or target_count != expected_target
        ):
            content_failures.append(
                f"{name} topology differs: source={source_count}, "
                f"target={target_count}, expected={expected_source}/"
                f"{expected_target}"
            )

    tikz_patterns = {
        "draw": r"\\draw",
        "node": r"\\node",
        "filldraw": r"\\filldraw",
        "foreach": r"\\foreach",
        "pgfmathsetmacro": r"\\pgfmathsetmacro",
        "plot": r"\bplot\b",
    }
    tikz_topology: dict[str, dict[str, int]] = {}
    for name, pattern in tikz_patterns.items():
        source_count = len(re.findall(pattern, source))
        target_count = len(re.findall(pattern, target))
        tikz_topology[name] = {
            "source": source_count,
            "target": target_count,
        }
        if source_count != target_count:
            content_failures.append(
                f"TikZ {name} topology differs: source={source_count}, "
                f"target={target_count}"
            )
    resize_counts = {
        "source": source.count(r"\resizebox"),
        "target": target.count(r"\resizebox"),
    }
    if resize_counts != {"source": 0, "target": 1}:
        content_failures.append(
            f"layout-only TikZ resize disposition differs: {resize_counts}"
        )

    source_markers = re.findall(
        r"^% H09-S(\d{3}) \| sumber "
        r"authority/habring/source-v1/optimal_transport\.tex "
        r"baris (\d+)--(\d+)$",
        target,
        re.MULTILINE,
    )
    segment_ids = re.findall(
        r"^% segment-id: (\S+)$", target, re.MULTILINE
    )
    if source_markers != EXPECTED_SOURCE_MARKERS:
        content_failures.append(
            f"ordered H09 source markers differ: {source_markers}"
        )
    if segment_ids != EXPECTED_SEGMENTS:
        content_failures.append(
            f"ordered stable segment IDs differ: {segment_ids}"
        )

    covered_lines: list[int] = []
    for _, start_text, end_text in source_markers:
        start = int(start_text)
        end = int(end_text)
        covered_lines.extend(range(start, end + 1))
    source_lines = source.splitlines()
    uncovered_nonblank = [
        number
        for number, line in enumerate(source_lines, start=1)
        if line.strip() and number not in covered_lines
    ]
    multiply_covered = sorted(
        number
        for number, count in Counter(covered_lines).items()
        if count != 1
    )
    out_of_bounds = sorted(
        number
        for number in set(covered_lines)
        if number < 1 or number > len(source_lines)
    )
    if uncovered_nonblank or multiply_covered or out_of_bounds:
        content_failures.append(
            "source-line closure differs: "
            f"uncovered_nonblank={uncovered_nonblank}, "
            f"multiply_covered={multiply_covered}, "
            f"out_of_bounds={out_of_bounds}"
        )

    compact_target = collapsed(target)
    surface_audit: list[dict[str, object]] = []
    for event_id in REQUIRED_LEDGER_IDS:
        event_surfaces: list[dict[str, object]] = []
        for surface, minimum in REQUIRED_CORRECTION_SURFACES[event_id]:
            count = compact_target.count(collapsed(surface))
            present = count >= minimum
            event_surfaces.append(
                {
                    "surface": surface,
                    "minimum_occurrences": minimum,
                    "target_occurrences": count,
                    "present": present,
                }
            )
            if not present:
                content_failures.append(
                    f"{event_id}: corrected surface missing or under-counted: "
                    f"{surface}; actual={count}, minimum={minimum}"
                )
        surface_audit.append(
            {
                "event_id": event_id,
                "all_present": all(
                    bool(item["present"]) for item in event_surfaces
                ),
                "surfaces": event_surfaces,
            }
        )

    forbidden_counts = {
        surface: compact_target.count(collapsed(surface))
        for surface in FORBIDDEN_TARGET_SURFACES
    }
    for surface, count in forbidden_counts.items():
        if count:
            content_failures.append(
                f"forbidden unresolved target surface remains: "
                f"{surface} ({count})"
            )

    wrapper_checks = {
        "includes_target_once": wrapper.count(
            r"\include{habring-09-transportasi-optimal-id}"
        )
        == 1,
        "chapter_counter_is_eight": r"\setcounter{chapter}{8}" in wrapper,
        "standalone_duality_anchor": (
            r"\refstepcounter{chapter}\label{chapter:duality}" in wrapper
        ),
        "bibliography_is_frozen_source": (
            r"\addbibresource{references-ot-id.bib}"
            in wrapper
        ),
        "authority_hash_disclosed": (
            "719df724b368126cc7540dffd461dc33" in wrapper
            and "aba7d5b5b6060132181086dfa17649ba" in wrapper
        ),
        "arxiv_authority_disclosed": "arXiv:2607.11664v1" in wrapper,
        "correction_range_disclosed": (
            "O015-HAB-ADV-0084 sampai O015-HAB-ADV-0096" in wrapper
        ),
        "thirteen_correction_items": len(
            re.findall(r"\\item(?:\[[^]]*\])?", wrapper)
        )
        == 13,
        "bibliography_correction_disclosed": (
            "C\\'edric Villani" in wrapper
            and "and others" in wrapper
            and "andothers" in wrapper
        ),
        "license_present": "CC BY 4.0" in wrapper,
        "nonendorsement_present": (
            "tidak menyusun, memeriksa, menyetujui, atau mendukung" in wrapper
        ),
        "language_metadata_present": "pdflang={id-ID}" in wrapper,
        "title_preserved": (
            r"\title{Optimisasi Konveks}" in wrapper
            and "Unit 9: Transportasi Optimal" in wrapper
        ),
        "ttp_absent": "TTP" not in wrapper
        and "Translation and Transcription Project" not in wrapper,
    }
    for name, passed in wrapper_checks.items():
        if not passed:
            content_failures.append(f"wrapper gate failed: {name}")

    local_bibliography_checks = {
        "single_expected_entry": (
            len(re.findall(r"(?m)^@", local_bibliography)) == 1
            and "@book{villani2009optimal," in local_bibliography
        ),
        "sole_author_corrected": (
            r"author    = {Villani, C{\'e}dric}" in local_bibliography
        ),
        "source_and_others_removed": "and others" not in local_bibliography,
        "publisher_doi_present": (
            "doi       = {10.1007/978-3-540-71050-9}" in local_bibliography
        ),
    }
    for name, passed in local_bibliography_checks.items():
        if not passed:
            content_failures.append(
                f"local bibliography gate failed: {name}"
            )

    proposed_records = jsonl_records(proposed_bytes)
    integrated_records = jsonl_records(integrated_bytes)
    proposed_ids_in_order = [
        str(record.get("event_id")) for record in proposed_records
    ]
    integrated_ids_in_order = [
        str(record.get("event_id")) for record in integrated_records
    ]
    proposed_by_id = {
        str(record["event_id"]): record for record in proposed_records
    }
    integrated_by_id = {
        str(record["event_id"]): record for record in integrated_records
    }
    proposed_ids = set(proposed_by_id)
    integrated_ids = set(integrated_by_id)
    required_set = set(REQUIRED_LEDGER_IDS)
    missing_proposed = sorted(required_set - proposed_ids)
    extra_proposed = sorted(proposed_ids - required_set)
    duplicate_proposed = sorted(
        event_id
        for event_id, count in Counter(proposed_ids_in_order).items()
        if count != 1
    )
    malformed_proposed = [
        str(record.get("event_id"))
        for record in proposed_records
        if set(record) != REQUIRED_LEDGER_FIELDS
    ]
    if proposed_ids_in_order != REQUIRED_LEDGER_IDS:
        content_failures.append(
            f"proposed-ledger event order differs: {proposed_ids_in_order}"
        )
    if missing_proposed or extra_proposed or duplicate_proposed:
        content_failures.append(
            "Chapter 9 proposed-ledger closure differs: "
            f"missing={missing_proposed}, extra={extra_proposed}, "
            f"duplicates={duplicate_proposed}"
        )
    if malformed_proposed:
        content_failures.append(
            f"Chapter 9 proposed-ledger field sets differ: {malformed_proposed}"
        )

    duplicate_integrated = sorted(
        event_id
        for event_id, count in Counter(integrated_ids_in_order).items()
        if count != 1
    )
    if duplicate_integrated:
        content_failures.append(
            f"integrated adverse ledger contains duplicate IDs: "
            f"{duplicate_integrated}"
        )
    missing_integrated = sorted(required_set - integrated_ids)
    differing_integrated = sorted(
        event_id
        for event_id in required_set & integrated_ids & proposed_ids
        if integrated_by_id[event_id] != proposed_by_id[event_id]
    )
    if missing_integrated:
        strict_only_failures.append(
            f"Chapter 9 records not integrated: {missing_integrated}"
        )
    if differing_integrated:
        strict_only_failures.append(
            "integrated Chapter 9 records differ from proposal: "
            f"{differing_integrated}"
        )
    wrapper_event_actual = integrated_by_id.get(
        str(WRAPPER_LEDGER_EVENT["event_id"])
    )
    wrapper_event_present = wrapper_event_actual is not None
    wrapper_event_exact = wrapper_event_actual == WRAPPER_LEDGER_EVENT
    if not wrapper_event_present:
        strict_only_failures.append(
            "wrapper bibliography correction event not integrated: "
            "O015-HAB-ADV-0096"
        )
    elif not wrapper_event_exact:
        strict_only_failures.append(
            "integrated O015-HAB-ADV-0096 differs from the audited "
            "wrapper bibliography correction"
        )

    source_formulae = formula_units(source)
    target_formulae = formula_units(target)
    manifest, manifest_content_failures, manifest_strict_failures = (
        formula_delta_manifest(
            source_formulae,
            target_formulae,
            identities["source"],
            identities["target"],
            proposed_ids,
            integrated_ids,
        )
    )
    content_failures.extend(manifest_content_failures)
    strict_only_failures.extend(manifest_strict_failures)
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    FORMULA_MANIFEST.write_bytes(manifest_bytes)

    strict_failures = content_failures + strict_only_failures
    active_failures = content_failures if report_only else strict_failures
    if report_only:
        result = "pass_report_only" if not content_failures else "fail_report_only"
    else:
        result = "pass" if not strict_failures else "fail"

    report: dict[str, object] = {
        "schema": "o015-optimal-transport-structure-audit-v1",
        "mode": "report-only" if report_only else "strict",
        "identity_policy": (
            "authority_target_wrapper_and_proposed_ledger_frozen_"
            "integrated_ledger_derived_live"
        ),
        "source": identities["source"],
        "target": identities["target"],
        "wrapper": identities["wrapper"],
        "local_bibliography": {
            **identities["local_bibliography"],
            "gates": local_bibliography_checks,
        },
        "environment_topology": {
            "count": len(source_begins),
            "counts_by_name": environment_counts,
            "ordered_begin_equal": source_begins == target_begins,
            "ordered_end_equal": source_ends == target_ends,
            "ordered_begin_environments": source_begins,
            "ordered_end_environments": source_ends,
        },
        "labels": {
            "source": source_labels,
            "target": target_labels,
            "target_unique": len(target_labels) == len(set(target_labels)),
        },
        "references": {
            "source": source_references,
            "target": target_references,
            "intentional_added_target_eqref": "ot:eq:disc_entropic",
        },
        "citations": {
            "source": source_citations,
            "target": target_citations,
            "intentional_added_target_citation": [
                "villani2009optimal",
                "Theorem 5.10",
            ],
        },
        "item_topology": {
            "source": source_items,
            "target": target_items,
        },
        "other_surface_topology": topology_counts,
        "tikz_topology": {
            "commands": tikz_topology,
            "layout_only_resizebox": resize_counts,
        },
        "source_markers": source_markers,
        "stable_segment_ids": segment_ids,
        "source_line_closure": {
            "source_line_count": len(source_lines),
            "covered_line_count": len(set(covered_lines)),
            "uncovered_nonblank_lines": uncovered_nonblank,
            "multiply_covered_lines": multiply_covered,
            "out_of_bounds_lines": out_of_bounds,
            "complete_nonblank_closure": not uncovered_nonblank
            and not multiply_covered
            and not out_of_bounds,
        },
        "correction_surface_audit": surface_audit,
        "forbidden_target_surface_counts": forbidden_counts,
        "wrapper_gates": wrapper_checks,
        "proposed_ledger": {
            **identities["proposed_ledger"],
            "required_ids": REQUIRED_LEDGER_IDS,
            "ids_in_order": proposed_ids_in_order,
            "missing_ids": missing_proposed,
            "extra_ids": extra_proposed,
            "duplicate_ids": duplicate_proposed,
            "malformed_field_sets": malformed_proposed,
        },
        "integrated_ledger": {
            "path": INTEGRATED_LEDGER.relative_to(ROOT).as_posix(),
            "bytes": len(integrated_bytes),
            "lines": len(integrated_bytes.decode("utf-8").splitlines()),
            "sha256": sha256(integrated_bytes),
            "record_count": len(integrated_records),
            "duplicate_ids": duplicate_integrated,
            "missing_required_ids": missing_integrated,
            "records_differing_from_proposal": differing_integrated,
            "exact_required_records_match_proposal": (
                not missing_integrated and not differing_integrated
            ),
            "wrapper_bibliography_event_id": "O015-HAB-ADV-0096",
            "wrapper_bibliography_event_present": wrapper_event_present,
            "wrapper_bibliography_event_exact": wrapper_event_exact,
        },
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
            "all_substantive_deltas_proposed_ledger_bound": manifest[
                "all_substantive_deltas_proposed_ledger_bound"
            ],
            "all_substantive_deltas_integrated_ledger_bound": manifest[
                "all_substantive_deltas_integrated_ledger_bound"
            ],
            "unbound_substantive_delta_block_ids": manifest[
                "unbound_substantive_delta_block_ids"
            ],
            "proposal_incomplete_substantive_delta_block_ids": manifest[
                "proposal_incomplete_substantive_delta_block_ids"
            ],
            "integration_incomplete_substantive_delta_block_ids": manifest[
                "integration_incomplete_substantive_delta_block_ids"
            ],
        },
        "content_failure_count": len(content_failures),
        "content_failures": content_failures,
        "strict_only_failure_count": len(strict_only_failures),
        "strict_only_failures": strict_only_failures,
        "strict_ready": not strict_failures,
        "failure_count": len(active_failures),
        "failures": active_failures,
        "result": result,
    }
    report_bytes = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    REPORT.write_bytes(report_bytes)
    print(
        json.dumps(
            {
                "result": result,
                "mode": report["mode"],
                "failure_count": report["failure_count"],
                "content_failure_count": report["content_failure_count"],
                "strict_only_failure_count": report[
                    "strict_only_failure_count"
                ],
                "strict_ready": report["strict_ready"],
                "target_sha256": identities["target"]["sha256"],
                "formula_manifest_sha256": sha256(manifest_bytes),
                "report_sha256": sha256(report_bytes),
            },
            sort_keys=True,
        )
    )
    if active_failures and not report_only:
        raise SystemExit(1)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-only",
        action="store_true",
        help=(
            "validate frozen content and proposals without requiring the "
            "Chapter 9 records to be integrated yet"
        ),
    )
    arguments = parser.parse_args()
    run(arguments.report_only)
