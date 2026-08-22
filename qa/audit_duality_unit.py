"""Bounded structural and formula-delta audit for Habring Chapter 7 id-ID.

The authority identity is frozen.  The target, proposed ledger, and integrated
ledger identities are intentionally derived on every invocation because the
translation can still be under review.  This script never edits the source or
target; it writes only the two QA artifacts declared below.
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
SOURCE = ROOT / "authority" / "habring" / "source-v1" / "duality.tex"
TARGET = ROOT / "source" / "id-ID" / "habring-07-dualitas-id.tex"
PROPOSED_LEDGER = ROOT / "qa" / "CHAPTER07_PROPOSED_LEDGER.jsonl"
INTEGRATED_LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
FORMULA_MANIFEST = ROOT / "qa" / "DUALITY_FORMULA_DELTA_MANIFEST.json"
REPORT = ROOT / "qa" / "DUALITY_STRUCTURE_REPORT.json"

EXPECTED_SOURCE_BYTES = 30_761
EXPECTED_SOURCE_LINES = 597
EXPECTED_SOURCE_SHA256 = (
    "0b112dee2582813cec5629c02df1dda329f690f944b60f4694b1c5762129bea9"
)
EXPECTED_TARGET_BYTES = 35_428
EXPECTED_TARGET_LINES = 632
EXPECTED_TARGET_SHA256 = (
    "11e9ad614f7ac4e3107e78bc3bed03a6d4acfe22f2a65fca26433b0ae3209fd9"
)
EXPECTED_ENVIRONMENT_COUNT = 148
EXPECTED_ENVIRONMENT_COUNTS = {
    "aligned": 27,
    "bmatrix": 4,
    "cases": 7,
    "defn": 1,
    "enumerate": 3,
    "equation": 79,
    "example": 1,
    "lemma": 8,
    "proof": 12,
    "rem": 2,
    "theorem": 4,
}

EXPECTED_SOURCE_LABELS = [
    "chapter:duality",
    "duality:lemma:subdiff_conjugate",
    "duality:item1",
    "duality:item2",
    "duality:item3",
    "duality:thm:Moreau:id",
    "duality:eq:fenchel_duality",
    "duality:eq:fenchel_rocka",
    "duality:qe:problem",
    "duality:qe:saddlepoint",
    "duality:eq:AH",
    "duality:eq:pdhg",
    "duality:eq:pdhg2",
    "eq:admm1",
    "eq:admm2",
    "duality:eq:admm_algo",
    "duality:eq:admm3",
    "duality:eq:proof_admm1",
    "duality:eq:proof_admm2",
    "duality:eq:proof_admm3",
    "duality:eq:proof_admm4",
    "duality:eq:proof_admm5",
    "duality:eq:proof_admm6",
    "duality:eq:proof_admm6",
]
EXPECTED_TARGET_LABELS = [
    *EXPECTED_SOURCE_LABELS[:-1],
    "duality:eq:proof_admm7",
]

EXPECTED_REFS = [
    "duality:item1",
    "duality:item2",
    "duality:item1",
    "duality:item2",
    "duality:item1",
    "duality:item2",
    "duality:item1",
    "duality:item3",
    "duality:item1",
]
EXPECTED_CREFS = [
    "duality:lemma:subdiff_conjugate",
    "duality:lemma:subdiff_conjugate",
    "duality:thm:Moreau:id",
]
EXPECTED_CAPITAL_CREFS = ["duality:eq:fenchel_duality"]
EXPECTED_SOURCE_EQREFS = [
    "duality:eq:fenchel_rocka",
    "duality:qe:problem",
    "duality:qe:saddlepoint",
    "duality:qe:saddlepoint",
    "duality:eq:AH",
    "duality:eq:pdhg2",
    "duality:eq:pdhg",
    "eq:admm1",
    "eq:admm2",
    "duality:eq:admm3",
    "duality:eq:admm_algo",
    "duality:eq:admm_algo",
    "duality:eq:proof_admm2",
    "duality:eq:proof_admm1",
    "duality:eq:proof_admm3",
    "duality:eq:proof_admm4",
    "duality:eq:proof_admm5",
    "duality:eq:proof_admm5",
    "duality:eq:proof_admm1",
    "duality:eq:proof_admm3",
    "duality:eq:proof_admm6",
]
EXPECTED_TARGET_EQREFS = [
    *EXPECTED_SOURCE_EQREFS[:-1],
    "duality:eq:proof_admm7",
]
EXPECTED_CITATIONS = ["beck2017first", "chambolle2011first"]

EXPECTED_SEGMENTS = [f"d90.hab.v1.ch07.seg{i:04d}" for i in range(1, 12)]
EXPECTED_SOURCE_MARKERS = [
    ("001", "1", "24"),
    ("002", "25", "60"),
    ("003", "61", "141"),
    ("004", "142", "186"),
    ("005", "187", "247"),
    ("006", "248", "277"),
    ("007", "278", "335"),
    ("008", "336", "394"),
    ("009", "395", "432"),
    ("010", "433", "502"),
    ("011", "503", "597"),
]

REQUIRED_LEDGER_IDS = [
    f"O015-HAB-ADV-{number:04d}" for number in range(50, 76)
]

# Literal reader-facing witnesses.  Whitespace is collapsed before counting,
# so wrapping changes do not weaken the mathematical checks.
REQUIRED_CORRECTION_SURFACES: dict[str, list[tuple[str, int]]] = {
    "O015-HAB-ADV-0050": [
        (r"f^*(x^*) = \sup_{x\in C}\inner{x^*}{x}", 1),
        (r"$f^* = \|\emptyarg\|$ setelah identifikasi $V^{**}\cong V$", 1),
    ],
    "O015-HAB-ADV-0051": [
        (r"andaikan bahwa $\partial f(\hat x) \neq \emptyset$", 1),
        ("interior relatif domain efektif", 1),
        (r"f^*(g)", 1),
        ("fungsi-fungsi afin kontinu", 1),
    ],
    "O015-HAB-ADV-0052": [
        (r"\inner{x^*}{x-x} + f(x)", 1),
        (r"\leq \frac{c}{\epsilon}<0", 2),
    ],
    "O015-HAB-ADV-0053": [
        (r"Misalkan $f\in\Gamma_0(V)$. Maka", 1),
        ("kedua pemetaan proksimal terdefinisi dengan baik dan bernilai tunggal", 1),
    ],
    "O015-HAB-ADV-0054": [
        (
            r"\Gc(x,y) = (f(x) + g(Kx)) - (-f^*(-K^*y) - g^*(y)).",
            1,
        ),
    ],
    "O015-HAB-ADV-0055": [
        (r"\prox_{\sigma g^*}(y_k+\sigma K(2x_{k+1}-x_k))", 1),
        (r"y^+ =& \arg\min_y", 1),
        (r"g^*(y^+) + \frac{1}{2\sigma}|y-y^+|^2", 1),
    ],
    "O015-HAB-ADV-0056": [
        (r"X_N = \frac{1}{N}\sum_{k=1}^{N}x_k", 1),
        (r"Y_N = \frac{1}{N}\sum_{k=1}^{N}y_k", 1),
        (r"\sum_{k=0}^{N-1} \Lc(x_{k+1},y) - \Lc(x,y_{k+1})", 1),
    ],
    "O015-HAB-ADV-0057": [
        (r"y_{k+1} = \arg\min_{y} g(y)", 1),
        (r"0 \in \partial g(y_{k+1}) + B^* \lambda_k", 1),
        (r"B^*\lambda_{k+1} \in -\partial g(y_{k+1})", 1),
        (r"0\in\partial_y L_0(x_{k+1},y_{k+1},\lambda_{k+1})", 1),
    ],
    "O015-HAB-ADV-0058": [
        (
            r"A(x^* - x_{k+1}) = z - By^* - (r_{k+1} + z - By_{k+1}) = -r_{k+1} + B(y_{k+1}-y^*)",
            1,
        ),
    ],
    "O015-HAB-ADV-0059": [
        (
            r"\|r_{k+1}\|^2 + \|B(y_{k+1}-y_k)\|^2 - 2\inner{r_{k+1}}{B(y_{k+1}-y_k)}",
            1,
        ),
        (r"\inner{r_{k+1}}{B(y_{k+1}-y_k)} \leq 0", 1),
        (
            r"V(y_{k+1},\lambda_{k+1}) + \gamma\|r_{k+1}\|^2 + \gamma\|B(y_{k+1}-y_k)\|^2",
            1,
        ),
        (r"\sum_{k=1}^{K-1}\gamma\big(\|r_{k+1}\|^2", 1),
        (r"V(y_{1},\lambda_{1})", 1),
    ],
    "O015-HAB-ADV-0060": [
        (
            r"p_{k+1}-p^*\leq -\gamma\inner{-r_{k+1} + B(y_{k+1}-y^*)}{B(y_{k+1}-y_k)} - \inner{r_{k+1}}{\lambda_{k+1}}",
            1,
        ),
    ],
    "O015-HAB-ADV-0061": [
        (r"\label{duality:eq:proof_admm7}", 1),
        (r"\eqref{duality:eq:proof_admm7}", 1),
    ],
    "O015-HAB-ADV-0062": [
        ("bikonjugat", 2),
        ("fungsional Lyapunov", 2),
    ],
    "O015-HAB-ADV-0063": [
        ("semua ruang vektor dipahami sebagai ruang Hilbert riil berdimensi hingga", 1),
        ("Dual yang digunakan adalah dual kontinu", 1),
        ("melalui representasi Riesz", 1),
    ],
    "O015-HAB-ADV-0064": [
        (r"Misalkan $f:V\rightarrow(-\infty,+\infty]$ proper", 1),
        (r"\Gamma_0(H)", 1),
        (r"H\rightarrow(-\infty,+\infty]", 1),
    ],
    "O015-HAB-ADV-0065": [
        ("minoran konveks semikontinu bawah terbesar", 1),
        ("selama keluarga minoran proper di bawah tidak kosong", 1),
        (r"Jika $\{\ell\in\Gamma(V):\ell\leq f\}\neq\emptyset$, maka", 1),
        (r"supremum pada ruas kanan dipahami sebagai fungsi yang identik $-\infty$", 1),
        (r"Fungsi ini tidak termasuk dalam $\Gamma(V)$", 1),
    ],
    "O015-HAB-ADV-0066": [
        ("syarat kualifikasi bagi aturan jumlah dan rantai subdiferensial", 1),
        ("kaidah Fermat pada peminimum", 1),
    ],
    "O015-HAB-ADV-0067": [
        (r"\min_x \sup_y \Lc(x,y)", 1),
        (r"\min_{x,y}\sup_{\lambda} L_\gamma", 1),
        ("hipotesis dualitas kuat dan ketercapaian primal--dual", 1),
        (r"\sup_{y'}\Lc(x,y') - \inf_{x'}\Lc(x',y)", 1),
    ],
    "O015-HAB-ADV-0068": [
        (
            r"\prox_{\sigma g^*}(y)=y-\sigma\prox_{g/\sigma}(y/\sigma)",
            1,
        ),
        (r"untuk $\sigma>0$", 1),
    ],
    "O015-HAB-ADV-0069": [
        ("Misalkan $X$ dan $Y$ ruang Hilbert riil berdimensi hingga", 1),
        (r"$f\in\Gamma_0(X)$, $g\in\Gamma_0(Y)$", 1),
        (r"$K:X\rightarrow Y$ linear terbatas, serta $\tau,\sigma>0$", 1),
        (r"$\tau\sigma\leq \|K\|^{-2}$", 1),
        ("untuk $K=0$, syarat ini dipahami otomatis terpenuhi", 1),
        (r"Untuk $N\geq1$", 1),
    ],
    "O015-HAB-ADV-0070": [
        (r"$f,g\in\Gamma_0(\R^d)$", 1),
        (r"$A,B:\R^d\rightarrow\R^m$ linear, dan $z\in\R^m$", 1),
        (r"Ambil $\gamma>0$", 1),
        ("kedua submasalah minimisasi dalam algoritme ADMM di atas mencapai minimumnya", 1),
        ("pilih sembarang peminimum tersebut", 1),
        (r"Dengan $r_k\coloneq Ax_k+By_k-z$, berlaku $r_k\rightarrow0$", 1),
        (r"$B(y_{k+1}-y_k)\rightarrow0$", 1),
        (r"suatu titik pelana dari $L_0(x,y,\lambda)$", 1),
    ],
    "O015-HAB-ADV-0071": [
        (r"$C\subset V$ tak kosong dan konveks", 1),
    ],
    "O015-HAB-ADV-0072": [
        (r"Karena $f$ proper, pilih $\bar x\in\dom(f)$", 1),
        (r"memasukkan $(\bar x,t)\in\epi(f)$", 1),
        (r"membiarkan $t\rightarrow\infty$, diperoleh $\alpha\geq 0$", 1),
    ],
    "O015-HAB-ADV-0073": [
        (r"Jika $K=0$, suku campuran dalam setiap tanda kurung siku lenyap", 1),
        (r"Jika $K\neq0$, nonnegativitas mengikuti", 1),
        (r"pilihan $\delta = \frac{1}{\tau\|K\|}$", 1),
    ],
    "O015-HAB-ADV-0074": [
        (
            r"Misalkan $X$ dan $Y$ ruang Hilbert riil berdimensi hingga, $f\in\Gamma_0(X)$, $g\in\Gamma_0(Y)$, $K:X\rightarrow Y$ linear terbatas, serta $\tau,\sigma>0$. Aturan pembaruan",
            1,
        ),
    ],
    "O015-HAB-ADV-0075": [
        (r"Untuk fungsi proper $f$ dengan $f^*$ proper", 1),
        (r"Misalkan $f$ dan $f^*$ proper", 1),
        (r"Jika $\{\ell\in\Gamma(V):\ell\leq f\}\neq\emptyset$, maka", 1),
        ("supremum pada ruas kanan", 1),
        (r"tidak dinotasikan sebagai $f^{**}$", 1),
    ],
}

FORBIDDEN_TARGET_SURFACES = [
    r"f:V\rightarrow[-\infty,\infty]",
    r"f:V\rightarrow [-\infty,\infty]",
    r"f,g:\R^d\rightarrow [-\infty,\infty]",
    r"f^*(y) - g^*(-K^*y)",
    r"\prox_{\sigma f}(y_k+\sigma K(2x_{k+1}-x_k))",
    r"y^+ =& \arg\min_x",
    r"y_{k+1} = \arg\min_{x} g(y)",
    r"\nabla g(y_{k+1})",
    r"+ 2\inner{r_{k+1}}{B(y_{k+1}-y_k)}",
    r"\inner{r_{k+1}}{B(y_{k+1}-y_k)} = \inner{r_{k+1}}{B(y_{k+1}-y_k)}",
    r"Dengan memasukkan $x=x_0$ dan mengambil $t$ cukup besar",
    "bijonjugate",
    "strictly negativ",
    "taing",
    "to proof",
    "primal und dual",
    "by by",
    "impliey",
    "Lyapunv",
    "reqrite",
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


def jsonl_records(data: bytes) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in data.decode("utf-8").splitlines()
        if line.strip()
    ]


def collapsed(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def canonical_formula(value: str) -> str:
    """Remove linguistic/layout noise while preserving mathematical changes."""

    value = re.sub(r"%[^\n]*", "", value)
    value = re.sub(r"\\label\{[^{}]*\}", "", value)
    value = re.sub(r"\\(?:C?cref|eqref|ref)\{[^{}]*\}", "", value)
    value = re.sub(r"\\text\{[^{}]*\}", r"\\text{#}", value)
    value = re.sub(r"\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\b", "", value)
    value = re.sub(r"\\(?:bigg|Bigg|big|Big|left|right)\b", "", value)
    value = re.sub(r"\\(?:quad|qquad|,|;|!)", "", value)
    value = value.replace(r"\coloneqq", r"\coloneq")
    value = re.sub(r"\s+", "", value)

    # Layout-only wrapper used to keep one long proof line inside the text block.
    resize = re.fullmatch(
        r"\\resizebox\{[^{}]*\}\{[^{}]*\}\{\$?(.*)\$?\}", value, re.DOTALL
    )
    if resize:
        value = resize.group(1)
    return value.rstrip(".,;")


def formula_units(text: str) -> list[FormulaUnit]:
    units: list[FormulaUnit] = []
    for ordinal, match in enumerate(MATH_PATTERN.finditer(text), start=1):
        if match.group("display") is not None:
            raw = match.group("display")
            kind = match.group("display_kind")
        elif match.group("bracket") is not None:
            raw = match.group("bracket")
            kind = "bracket"
        elif match.group("paren") is not None:
            raw = match.group("paren")
            kind = "paren"
        else:
            raw = match.group("inline")
            kind = "inline"
        units.append(
            FormulaUnit(
                ordinal=ordinal,
                line=text.count("\n", 0, match.start()) + 1,
                kind=str(kind),
                raw=collapsed(raw),
                canonical=canonical_formula(raw),
            )
        )
    return units


# A source line interval binds mathematical changes to the correction event
# responsible for that surface.  Target-only additions are bound by the anchor
# patterns below.  Multiple bindings on one SequenceMatcher block are expected.
SOURCE_LINE_BINDINGS: list[tuple[int, int, tuple[str, ...]]] = [
    (1, 6, ("O015-HAB-ADV-0063",)),
    (7, 17, ("O015-HAB-ADV-0064",)),
    (18, 24, ("O015-HAB-ADV-0050",)),
    (25, 60, ("O015-HAB-ADV-0051",)),
    (61, 132, ("O015-HAB-ADV-0052",)),
    (61, 70, ("O015-HAB-ADV-0075",)),
    (92, 100, ("O015-HAB-ADV-0072",)),
    (133, 141, ("O015-HAB-ADV-0065", "O015-HAB-ADV-0075")),
    (178, 186, ("O015-HAB-ADV-0053", "O015-HAB-ADV-0064")),
    (188, 247, ("O015-HAB-ADV-0064", "O015-HAB-ADV-0066")),
    (248, 277, ("O015-HAB-ADV-0054", "O015-HAB-ADV-0067")),
    (278, 335, ("O015-HAB-ADV-0055", "O015-HAB-ADV-0069")),
    (336, 394, ("O015-HAB-ADV-0055", "O015-HAB-ADV-0056", "O015-HAB-ADV-0069")),
    (397, 432, ("O015-HAB-ADV-0057", "O015-HAB-ADV-0067", "O015-HAB-ADV-0070")),
    (433, 495, ("O015-HAB-ADV-0057", "O015-HAB-ADV-0062", "O015-HAB-ADV-0070")),
    (496, 502, ("O015-HAB-ADV-0058",)),
    (503, 589, ("O015-HAB-ADV-0059",)),
    (590, 597, ("O015-HAB-ADV-0060", "O015-HAB-ADV-0061")),
]

# Target-only formula insertions have no source line with which to bind.  These
# exact frozen reader ranges bind the five late rereview events without using
# generic one-token patterns such as ``f`` or ``K=0``.
TARGET_LINE_BINDINGS: list[tuple[int, int, tuple[str, ...]]] = [
    (63, 68, ("O015-HAB-ADV-0075",)),
    (99, 99, ("O015-HAB-ADV-0072",)),
    (143, 148, ("O015-HAB-ADV-0065", "O015-HAB-ADV-0075")),
    (355, 355, ("O015-HAB-ADV-0074",)),
    (405, 405, ("O015-HAB-ADV-0073",)),
]

TARGET_FORMULA_BINDINGS: dict[str, list[str]] = {
    "O015-HAB-ADV-0050": [r"\\inner\{x\^\*\}\{x\}", r"f\^\*=\\\|\\emptyarg\\\|"],
    "O015-HAB-ADV-0051": [r"f\^\*\(g\)"],
    "O015-HAB-ADV-0052": [r"f\^\{\*\*\}\(x\)", r"\\frac\{c\}\{\\epsilon\}<0"],
    "O015-HAB-ADV-0053": [r"\\prox_f\(x\)\+\\prox_\{f\^\*\}\(x\)"],
    "O015-HAB-ADV-0054": [r"f\^\*\(-K\^\*y\).*g\^\*\(y\)"],
    "O015-HAB-ADV-0055": [r"\\prox_\{\\sigmag\^\*\}", r"\\arg\\min_y", r"\\frac\{1\}\{2\\sigma\}\|y-y\^\+\|\^2"],
    "O015-HAB-ADV-0056": [r"X_N=\\frac\{1\}\{N\}\\sum_\{k=1\}\^\{N\}x_k", r"x_\{k\+1\}.*y_\{k\+1\}"],
    "O015-HAB-ADV-0057": [r"\\partialg\(y_\{k\+1\}\)", r"\\partial_yL_0"],
    "O015-HAB-ADV-0058": [r"A\(x\^\*-x_\{k\+1\}\).*B\(y_\{k\+1\}-y\^\*\)"],
    "O015-HAB-ADV-0059": [r"-2\\inner\{r_\{k\+1\}\}", r"\\gamma\\\|r_\{k\+1\}\\\|\^2", r"V\(y_\{1\},\\lambda_\{1\}\)"],
    "O015-HAB-ADV-0060": [r"p_\{k\+1\}-p\^\*.*-\\gamma\\inner"],
    "O015-HAB-ADV-0063": [r"V\^\*\\congV", r"\\Gamma_0\(H\)"],
    "O015-HAB-ADV-0064": [r"\(-\\infty,\+\\infty\]", r"\\Gamma_0"],
    "O015-HAB-ADV-0065": [r"\\Gamma\(V\)", r"-\\infty"],
    "O015-HAB-ADV-0067": [r"\\sup_y", r"\\sup_\{\\lambda\}"],
    "O015-HAB-ADV-0068": [r"\\prox_\{\\sigmag\^\*\}\(y\)=y-\\sigma\\prox_\{g/\\sigma\}"],
    "O015-HAB-ADV-0069": [r"X_N", r"Y_N", r"N\\geq1", r"\\tau,\\sigma>0"],
    "O015-HAB-ADV-0070": [r"A,B:\\R\^d\\rightarrow\\R\^m", r"r_k\\rightarrow0", r"B\(y_\{k\+1\}-y_k\)\\rightarrow0"],
}


def binding_ids(source_entries: Iterable[FormulaUnit], target_entries: Iterable[FormulaUnit]) -> list[str]:
    bindings: set[str] = set()
    source_lines = [entry.line for entry in source_entries]
    for start, end, event_ids in SOURCE_LINE_BINDINGS:
        if any(start <= line <= end for line in source_lines):
            bindings.update(event_ids)
    target_lines = [entry.line for entry in target_entries]
    for start, end, event_ids in TARGET_LINE_BINDINGS:
        if any(start <= line <= end for line in target_lines):
            bindings.update(event_ids)
    target_formulae = "\n".join(entry.canonical for entry in target_entries)
    for event_id, patterns in TARGET_FORMULA_BINDINGS.items():
        if any(re.search(pattern, target_formulae) for pattern in patterns):
            bindings.add(event_id)
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
    substantive_block_ids: list[str] = []
    unbound_block_ids: list[str] = []
    incompletely_bound_block_ids: list[str] = []

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
        block_id = f"d90.hab.v1.ch07.formula-delta.{len(blocks) + 1:04d}"
        missing_proposed = [event for event in event_ids if event not in proposed_ids]
        missing_integrated = [event for event in event_ids if event not in integrated_ids]
        ledger_bound = (
            not substantive
            or bool(event_ids)
            and not missing_proposed
            and not missing_integrated
        )
        if substantive:
            substantive_block_ids.append(block_id)
            if not event_ids:
                unbound_block_ids.append(block_id)
                failures.append(f"substantive formula delta has no ledger binding: {block_id}")
            elif missing_proposed or missing_integrated:
                incompletely_bound_block_ids.append(block_id)
                failures.append(
                    f"substantive formula delta lacks live ledger closure: {block_id}; "
                    f"missing proposed={missing_proposed}, integrated={missing_integrated}"
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
                "missing_integrated_event_ids": missing_integrated,
                "ledger_bound": ledger_bound,
            }
        )

    manifest: dict[str, object] = {
        "schema": "o015-duality-formula-delta-manifest-v1",
        "identity_policy": "authority_and_final_target_frozen_ledgers_derived_live",
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
                "layout-only resizebox wrapper",
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
        "substantive_delta_block_count": len(substantive_block_ids),
        "substantive_delta_block_ids": substantive_block_ids,
        "unbound_substantive_delta_block_ids": unbound_block_ids,
        "incompletely_bound_substantive_delta_block_ids": incompletely_bound_block_ids,
        "all_substantive_deltas_ledger_bound": not unbound_block_ids
        and not incompletely_bound_block_ids,
        "blocks": blocks,
    }
    return manifest, failures


def run(report_only: bool) -> dict[str, object]:
    source_bytes = SOURCE.read_bytes()
    target_bytes = TARGET.read_bytes()
    proposed_bytes = PROPOSED_LEDGER.read_bytes()
    integrated_bytes = INTEGRATED_LEDGER.read_bytes()
    source = source_bytes.decode("utf-8")
    target = target_bytes.decode("utf-8")
    failures: list[str] = []

    source_identity = {
        "path": SOURCE.relative_to(ROOT).as_posix(),
        "bytes": len(source_bytes),
        "lines": len(source.splitlines()),
        "sha256": sha256(source_bytes),
    }
    target_identity = {
        "path": TARGET.relative_to(ROOT).as_posix(),
        "bytes": len(target_bytes),
        "lines": len(target.splitlines()),
        "sha256": sha256(target_bytes),
        "expected_sha256": EXPECTED_TARGET_SHA256,
        "identity_policy": "final_target_frozen_after_independent_rereview",
    }
    if source_identity["bytes"] != EXPECTED_SOURCE_BYTES:
        failures.append(f"authority byte count changed: {source_identity['bytes']}")
    if source_identity["lines"] != EXPECTED_SOURCE_LINES:
        failures.append(f"authority line count changed: {source_identity['lines']}")
    if source_identity["sha256"] != EXPECTED_SOURCE_SHA256:
        failures.append(f"authority SHA changed: {source_identity['sha256']}")
    if target_identity["bytes"] != EXPECTED_TARGET_BYTES:
        failures.append(f"target byte count changed: {target_identity['bytes']}")
    if target_identity["lines"] != EXPECTED_TARGET_LINES:
        failures.append(f"target line count changed: {target_identity['lines']}")
    if target_identity["sha256"] != EXPECTED_TARGET_SHA256:
        failures.append(f"target SHA changed: {target_identity['sha256']}")

    source_begins = re.findall(r"\\begin\{([^}]+)\}", source)
    source_ends = re.findall(r"\\end\{([^}]+)\}", source)
    target_begins = re.findall(r"\\begin\{([^}]+)\}", target)
    target_ends = re.findall(r"\\end\{([^}]+)\}", target)
    environment_counts = dict(sorted(Counter(source_begins).items()))
    if len(source_begins) != EXPECTED_ENVIRONMENT_COUNT:
        failures.append(f"source begin-environment count differs: {len(source_begins)}")
    if len(source_ends) != EXPECTED_ENVIRONMENT_COUNT:
        failures.append(f"source end-environment count differs: {len(source_ends)}")
    if environment_counts != EXPECTED_ENVIRONMENT_COUNTS:
        failures.append(f"source environment inventory differs: {environment_counts}")
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
        failures.append("duplicate target label remains")

    reference_patterns = {
        "ref": r"\\ref\{([^}]+)\}",
        "cref": r"\\cref\{([^}]+)\}",
        "Cref": r"\\Cref\{([^}]+)\}",
        "eqref": r"\\eqref\{([^}]+)\}",
    }
    source_references = {
        name: re.findall(pattern, source) for name, pattern in reference_patterns.items()
    }
    target_references = {
        name: re.findall(pattern, target) for name, pattern in reference_patterns.items()
    }
    expected_source_references = {
        "ref": EXPECTED_REFS,
        "cref": EXPECTED_CREFS,
        "Cref": EXPECTED_CAPITAL_CREFS,
        "eqref": EXPECTED_SOURCE_EQREFS,
    }
    expected_target_references = {
        **expected_source_references,
        "eqref": EXPECTED_TARGET_EQREFS,
    }
    if source_references != expected_source_references:
        failures.append(f"source reference topology differs: {source_references}")
    if target_references != expected_target_references:
        failures.append(f"target reference topology differs: {target_references}")

    citation_pattern = re.compile(
        r"\\(?:cite|citep|citet|autocite|parencite|textcite)\*?"
        r"(?:\[[^]]*\])*\{([^}]+)\}"
    )
    source_citations = citation_pattern.findall(source)
    target_citations = citation_pattern.findall(target)
    if source_citations != EXPECTED_CITATIONS or target_citations != EXPECTED_CITATIONS:
        failures.append(
            f"citation topology differs: source={source_citations}, target={target_citations}"
        )

    source_items = re.findall(r"\\item(?:\[([^]]*)\])?", source)
    target_items = re.findall(r"\\item(?:\[([^]]*)\])?", target)
    if len(source_items) != 9 or target_items != source_items:
        failures.append(
            f"item topology differs: source_count={len(source_items)}, "
            f"target_count={len(target_items)}"
        )

    topology_counts: dict[str, dict[str, int]] = {}
    for name, pattern, expected in (
        ("footnotes", r"\\footnote\{", 1),
        ("figure_environments", r"\\begin\{figure\*?\}", 0),
        (
            "external_assets",
            r"\\(?:includegraphics|includesvg|includepdf|lstinputlisting)"
            r"(?:\[[^]]*\])?\{",
            0,
        ),
        ("source_inputs", r"\\(?:input|include)\{", 0),
    ):
        source_count = len(re.findall(pattern, source))
        target_count = len(re.findall(pattern, target))
        topology_counts[name] = {"source": source_count, "target": target_count}
        if source_count != expected or target_count != expected:
            failures.append(
                f"{name} topology differs: source={source_count}, "
                f"target={target_count}, expected={expected}"
            )

    source_markers = re.findall(
        r"^% H07-S(\d{3}) \| sumber authority/habring/source-v1/duality\.tex "
        r"baris (\d+)--(\d+)$",
        target,
        re.MULTILINE,
    )
    if source_markers != EXPECTED_SOURCE_MARKERS:
        failures.append(f"ordered H07 source markers differ: {source_markers}")
    segment_ids = re.findall(r"^% segment-id: (\S+)$", target, re.MULTILINE)
    if segment_ids != EXPECTED_SEGMENTS:
        failures.append(f"ordered stable segment IDs differ: {segment_ids}")

    compact_target = collapsed(target)
    surface_audit: list[dict[str, object]] = []
    for event_id in REQUIRED_LEDGER_IDS:
        requirements = REQUIRED_CORRECTION_SURFACES[event_id]
        event_result: list[dict[str, object]] = []
        for surface, minimum in requirements:
            count = compact_target.count(collapsed(surface))
            present = count >= minimum
            event_result.append(
                {
                    "surface": surface,
                    "minimum_occurrences": minimum,
                    "target_occurrences": count,
                    "present": present,
                }
            )
            if not present:
                failures.append(
                    f"{event_id}: corrected surface missing/under-counted: {surface}; "
                    f"actual={count}, minimum={minimum}"
                )
        surface_audit.append(
            {
                "event_id": event_id,
                "all_present": all(bool(item["present"]) for item in event_result),
                "surfaces": event_result,
            }
        )

    forbidden_counts = {
        surface: compact_target.count(collapsed(surface))
        for surface in FORBIDDEN_TARGET_SURFACES
    }
    for surface, count in forbidden_counts.items():
        if count:
            failures.append(f"forbidden unresolved target surface remains: {surface} ({count})")

    proposed_records = jsonl_records(proposed_bytes)
    integrated_records = jsonl_records(integrated_bytes)
    proposed_by_id = {record["event_id"]: record for record in proposed_records}
    integrated_by_id = {record["event_id"]: record for record in integrated_records}
    required_set = set(REQUIRED_LEDGER_IDS)
    proposed_ids = set(proposed_by_id)
    integrated_ids = set(integrated_by_id)
    missing_proposed = sorted(required_set - proposed_ids)
    extra_proposed = sorted(proposed_ids - required_set)
    missing_integrated = sorted(required_set - integrated_ids)
    differing_integrated = sorted(
        event_id
        for event_id in required_set & integrated_ids & proposed_ids
        if integrated_by_id[event_id] != proposed_by_id[event_id]
    )
    if missing_proposed or extra_proposed:
        failures.append(
            f"Chapter 7 proposed-ledger closure differs: missing={missing_proposed}, "
            f"extra={extra_proposed}"
        )
    if missing_integrated:
        failures.append(f"Chapter 7 records not integrated: {missing_integrated}")
    if differing_integrated:
        failures.append(
            f"integrated Chapter 7 records differ from proposal: {differing_integrated}"
        )

    source_formulae = formula_units(source)
    target_formulae = formula_units(target)
    manifest, manifest_failures = formula_delta_manifest(
        source_formulae,
        target_formulae,
        source_identity,
        target_identity,
        proposed_ids,
        integrated_ids,
    )
    failures.extend(manifest_failures)
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    FORMULA_MANIFEST.write_bytes(manifest_bytes)

    report: dict[str, object] = {
        "schema": "o015-duality-structure-audit-v1",
        "identity_policy": "authority_and_final_target_frozen_ledgers_derived_live",
        "source": source_identity,
        "target": target_identity,
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
            "source_duplicate": "duality:eq:proof_admm6",
            "target_unique_remap": "duality:eq:proof_admm7",
            "only_final_duplicate_remapped": target_labels == EXPECTED_TARGET_LABELS,
            "target_unique": len(target_labels) == len(set(target_labels)),
        },
        "references": {
            "source": source_references,
            "target": target_references,
        },
        "citations": {"source": source_citations, "target": target_citations},
        "item_topology": {"source": source_items, "target": target_items},
        "other_surface_topology": topology_counts,
        "source_markers": source_markers,
        "stable_segment_ids": segment_ids,
        "correction_surface_audit": surface_audit,
        "forbidden_target_surface_counts": forbidden_counts,
        "proposed_ledger": {
            "path": PROPOSED_LEDGER.relative_to(ROOT).as_posix(),
            "bytes": len(proposed_bytes),
            "sha256": sha256(proposed_bytes),
            "required_ids": REQUIRED_LEDGER_IDS,
            "missing_ids": missing_proposed,
            "extra_ids": extra_proposed,
        },
        "integrated_ledger": {
            "path": INTEGRATED_LEDGER.relative_to(ROOT).as_posix(),
            "bytes": len(integrated_bytes),
            "sha256": sha256(integrated_bytes),
            "missing_required_ids": missing_integrated,
            "records_differing_from_proposal": differing_integrated,
            "exact_required_records_match_proposal": not missing_integrated
            and not differing_integrated,
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
            "all_substantive_deltas_ledger_bound": manifest[
                "all_substantive_deltas_ledger_bound"
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
                "target_sha256": target_identity["sha256"],
                "formula_manifest_sha256": sha256(manifest_bytes),
                "report_sha256": sha256(report_bytes),
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
        help="write reports and return success even when the live target is incomplete",
    )
    arguments = parser.parse_args()
    run(arguments.report_only)
