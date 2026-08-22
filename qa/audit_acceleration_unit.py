"""Structural, reference, formula-surface, and correction audit for Habring Chapter 6 id-ID."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "habring" / "source-v1" / "acceleration.tex"
TARGET = ROOT / "source" / "id-ID" / "habring-06-akselerasi-id.tex"
REPORT = ROOT / "qa" / "ACCELERATION_STRUCTURE_REPORT.json"
LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
PROPOSED_LEDGER = ROOT / "qa" / "CHAPTER06_PROPOSED_LEDGER.jsonl"

EXPECTED_SOURCE_SHA256 = "2ff1e10e9421c0fe01a09140e3e230cb2d3728c30c572bb6ca5513b229f1e605"
EXPECTED_TARGET_SHA256 = "b1e27d912bc94722ec1c33257598c074eec8a6f5bf81f43b8946f85b48f4c35a"
EXPECTED_PROPOSED_LEDGER_SHA256 = "1268b365b19c701a1b7f5c5c0c466c72f5ed7205e3303e09f1122403f593abac"
EXPECTED_FORMULA_DELTA_MANIFEST_SHA256 = "886d80e0a759977c0c176d9b97e595b4c3515ecd52446a8c8b714146a9be3f4a"
EXPECTED_ENVIRONMENT_COUNT = 99
EXPECTED_ENVIRONMENT_COUNTS = {
    "aligned": 17,
    "bmatrix": 8,
    "cases": 2,
    "cor": 1,
    "equation": 54,
    "lemma": 3,
    "pmatrix": 6,
    "proof": 6,
    "theorem": 2,
}
EXPECTED_LABELS = [
    "acceleration:eq:friction_ode",
    "acceleration:lemma:spectral_radius",
    "acceleration:cor:spectral_radius",
    "acceleration:eq:heavy_ball1",
    "eq:fista1",
    "eq:fista2",
    "eq:fista3",
]
EXPECTED_CREFS = [
    "acceleration:eq:friction_ode",
    "acceleration:lemma:spectral_radius",
    "acceleration:lemma:spectral_radius",
    "acceleration:cor:spectral_radius",
]
EXPECTED_EQREFS = [
    "acceleration:eq:heavy_ball1",
    "eq:fista1",
    "eq:fista2",
    "eq:fista3",
]
EXPECTED_SEGMENTS = [f"d90.hab.v1.ch06.seg{order:04d}" for order in range(1, 13)]
REQUIRED_LEDGER_IDS = [f"O015-HAB-ADV-{number:04d}" for number in range(39, 50)]

# Every correction event is tied to exact reader-facing surfaces.  Multiple
# surfaces are deliberate: a single keyword cannot witness a mathematical fix.
REQUIRED_CORRECTION_SURFACES: dict[str, list[str]] = {
    "O015-HAB-ADV-0039": [
        r"Untuk setiap \(L>0\), titik awal \(x_0\in\R^d\), bilangan bulat \(k\geq1\), dan \(d\geq2k+1\)",
        r"terdapat fungsi konveks \(f:\R^d\rightarrow\R\) yang bergradien \(L\)-Lipschitz dan mempunyai peminim \(x^*\)",
        r"\frac{3L\|x_0-x^*\|^2}{32(k+1)^2}",
    ],
    "O015-HAB-ADV-0040": [
        r"norma operator yang diinduksi oleh norma Euclidean",
        r"Kompleksifikasikan \(A\) ke operator pada \(\mathbb{C}^d\)",
        r"Jika ukuran blok Jordan terbesar adalah \(m\), maka \(N^m=0\)",
        r"Jika \(\rho(A)=0\), semua elemen diagonal nol",
        r"C_{\rho}\,n^{m-1}\rho(A)^{\,n-m+1}",
    ],
    "O015-HAB-ADV-0041": [
        r"Jika \(A^k\rightarrow0\), maka untuk setiap pasangan eigen kompleks",
        r"\max_{0\leq k<n}",
        r"Dengan memperbesar konstanta untuk indeks awal yang berhingga banyaknya",
    ],
    "O015-HAB-ADV-0042": [
        r"f\in C^2(U)",
        r"peminim stasioner lokal \(x^*\)",
        r"0<\mu\leq L",
        r"Gunakan parameter konstan \(\beta_k=\beta\) dan \(\tau_k=\tau\)",
        r"parameter yang meminimumkan radius spektral kasus terburuk dari model kuadratik atau linearisasi lokal",
    ],
    "O015-HAB-ADV-0043": [
        r"rekursi kedalaman dua dapat ditulis tepat sebagai",
        r"\nabla f(x^*+u_k)-\nabla f(x^*)",
        r"r_k\coloneqq",
        r"-\tau r_k",
    ],
    "O015-HAB-ADV-0044": [
        r"tanpa pernah membagi dengan \(\lambda\)",
        r"p_\eta(\lambda)",
        r"\lambda^2-(1+\beta-\tau\eta)\lambda+\beta=0",
        r"kriteria Schur--Jury",
        r"termasuk kasus \(\beta=0\)",
    ],
    "O015-HAB-ADV-0045": [
        r"Terdapat norma ekuivalen \(\|\cdot\|_\delta\)",
        r"bola kecil yang digunakan di atas tetap invarian",
        r"Batas bawah di atas membuktikan bahwa nilai maksimum tersebut tidak dapat diperkecil",
        r"\paragraph{Latihan verifikasi.}",
    ],
    "O015-HAB-ADV-0046": [
        r"f:\R^d\rightarrow\R",
        r"g:\R^d\rightarrow(-\infty,\infty]",
        r"\arg\min F\neq\emptyset",
        r"Dengan \(x_0=x_1\), \(t_1=1\), ukuran langkah tetap \(0<\tau\leq1/L\), dan \(k=1,2,\dots\)",
    ],
    "O015-HAB-ADV-0047": [
        r"Karena \(g\) konveks",
        r"\frac{L}{2}\|z-y\|^2",
        r"Dengan memasukkan definisi \(\phi\)",
        r"f(y)+\langle x-y,\nabla f(y)\rangle=f(x)-\ell_f(x,y)",
    ],
    "O015-HAB-ADV-0048": [
        r"Untuk setiap \(k\geq2\)",
        r"C=2\left(t_2^2\|x^*-x_1\|^2+",
        r"\|t_2(x^*-x_2)+(t_2-1)(x_1-x^*)\|^2\right)",
        r"Misalkan \(f:\R^d\rightarrow\R\) konveks, terdiferensialkan, dan bergradien \(L\)-Lipschitz dengan \(L>0\)",
    ],
    "O015-HAB-ADV-0049": [
        r"x(t-h)=x_{k-1}",
        r"mengizinkannya bergantung pada iterasi",
        r"menambahkan komponen searah dengan langkah sebelumnya",
        r"hasil dasar aljabar linear",
        r"metode ini sangat mirip dengan algoritma bola berat",
        r"Dengan memasukkan definisi \(\phi\)",
    ],
}

FORBIDDEN_TARGET_TYPO_SURFACES = [
    "x_{t-h}",
    "depdendent",
    "compontent",
    "linar",
    "tha maximizing",
    "follows from directly from",
    "there exist",
    "the the",
    "resebles",
    "Pugging",
    "constnat",
]

PROMPT_DISPOSITION = {
    "source_surface": (
        "% \\todo{@Alex: Exercise: prove local convergence from the "
        "linearization with hints! Prove optimal parameters with hints.}"
    ),
    "target_heading": r"\paragraph{Latihan verifikasi.}",
    "target_surface": (
        r"Verifikasikan kriteria Schur--Jury di atas langsung dari rumus akar, "
        r"termasuk kasus \(\beta=0\), dan turunkan kembali parameter kasus "
        r"terburuk dengan menyamakan perilaku pada \(\eta=\mu\) dan \(\eta=L\)."
    ),
    "disposition": "promoted_source_editorial_todo_to_rendered_self_study_verification_prompt",
}


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


def jsonl_records(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run(report_only: bool) -> dict[str, object]:
    source_bytes = SOURCE.read_bytes()
    target_bytes = TARGET.read_bytes()
    proposed_ledger_bytes = PROPOSED_LEDGER.read_bytes()
    source = source_bytes.decode("utf-8")
    target = target_bytes.decode("utf-8")
    failures: list[str] = []

    source_sha = sha256(source_bytes)
    target_sha = sha256(target_bytes)
    proposed_ledger_sha = sha256(proposed_ledger_bytes)
    if source_sha != EXPECTED_SOURCE_SHA256:
        failures.append(f"authority SHA changed: {source_sha}")
    if target_sha != EXPECTED_TARGET_SHA256:
        failures.append(f"target SHA changed: {target_sha}")
    if proposed_ledger_sha != EXPECTED_PROPOSED_LEDGER_SHA256:
        failures.append(f"proposed-ledger SHA changed: {proposed_ledger_sha}")

    source_begins = re.findall(r"\\begin\{([^}]+)\}", source)
    target_begins = re.findall(r"\\begin\{([^}]+)\}", target)
    source_ends = re.findall(r"\\end\{([^}]+)\}", source)
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
    if source_labels != EXPECTED_LABELS:
        failures.append(f"source label sequence differs: {source_labels}")
    if target_labels != EXPECTED_LABELS:
        failures.append(f"target label sequence differs: {target_labels}")
    if len(target_labels) != len(set(target_labels)):
        failures.append("duplicate target label")

    source_crefs = re.findall(r"\\cref\{([^}]+)\}", source)
    target_crefs = re.findall(r"\\cref\{([^}]+)\}", target)
    source_eqrefs = re.findall(r"\\eqref\{([^}]+)\}", source)
    target_eqrefs = re.findall(r"\\eqref\{([^}]+)\}", target)
    for side, kind, actual, expected in (
        ("source", "cref", source_crefs, EXPECTED_CREFS),
        ("target", "cref", target_crefs, EXPECTED_CREFS),
        ("source", "eqref", source_eqrefs, EXPECTED_EQREFS),
        ("target", "eqref", target_eqrefs, EXPECTED_EQREFS),
    ):
        if actual != expected:
            failures.append(f"{side} {kind} sequence differs: {actual}")

    segments = re.findall(r"^% segment-id: (\S+)$", target, re.MULTILINE)
    if segments != EXPECTED_SEGMENTS:
        failures.append(f"segment sequence differs: {segments}")

    absent_surface_patterns = {
        "citations": r"\\(?:cite|citep|citet|autocite|parencite|textcite)\*?(?:\[[^]]*\])*\{",
        "figures": r"\\begin\{figure\*?\}",
        "assets": r"\\(?:includegraphics|includesvg|includepdf|lstinputlisting)(?:\[[^]]*\])?\{",
        "footnotes": r"\\footnote\{",
        "inputs": r"\\(?:input|include)\{",
    }
    absent_surface_counts: dict[str, dict[str, int]] = {}
    for name, pattern in absent_surface_patterns.items():
        source_count = len(re.findall(pattern, source))
        target_count = len(re.findall(pattern, target))
        absent_surface_counts[name] = {"source": source_count, "target": target_count}
        if source_count or target_count:
            failures.append(
                f"unexpected {name} surface: source={source_count}, target={target_count}"
            )

    correction_surface_audit: list[dict[str, object]] = []
    for event_id in REQUIRED_LEDGER_IDS:
        surfaces = REQUIRED_CORRECTION_SURFACES[event_id]
        surface_counts = [target.count(surface) for surface in surfaces]
        correction_surface_audit.append(
            {
                "event_id": event_id,
                "required_surfaces": surfaces,
                "target_occurrences": surface_counts,
                "all_present": all(count >= 1 for count in surface_counts),
            }
        )
        for surface, count in zip(surfaces, surface_counts, strict=True):
            if count < 1:
                failures.append(f"{event_id}: required corrected surface missing: {surface}")

    forbidden_typo_counts = {
        surface: target.count(surface) for surface in FORBIDDEN_TARGET_TYPO_SURFACES
    }
    for surface, count in forbidden_typo_counts.items():
        if count:
            failures.append(f"source typo remains in target: {surface} ({count})")

    prompt_audit = {
        **PROMPT_DISPOSITION,
        "source_occurrences": source.count(PROMPT_DISPOSITION["source_surface"]),
        "target_heading_occurrences": target.count(PROMPT_DISPOSITION["target_heading"]),
        "target_surface_occurrences": target.count(PROMPT_DISPOSITION["target_surface"]),
    }
    if prompt_audit["source_occurrences"] != 1:
        failures.append(
            "source informal verification prompt count differs: "
            f"{prompt_audit['source_occurrences']}"
        )
    if prompt_audit["target_heading_occurrences"] != 1:
        failures.append(
            "target verification-prompt heading count differs: "
            f"{prompt_audit['target_heading_occurrences']}"
        )
    if prompt_audit["target_surface_occurrences"] != 1:
        failures.append(
            "target verification-prompt surface count differs: "
            f"{prompt_audit['target_surface_occurrences']}"
        )

    proposed_records = jsonl_records(PROPOSED_LEDGER)
    proposed_by_id = {record["event_id"]: record for record in proposed_records}
    integrated_records = jsonl_records(LEDGER)
    integrated_by_id = {record["event_id"]: record for record in integrated_records}
    missing_ledger = [event_id for event_id in REQUIRED_LEDGER_IDS if event_id not in integrated_by_id]
    differing_ledger = [
        event_id
        for event_id in REQUIRED_LEDGER_IDS
        if event_id in integrated_by_id
        and integrated_by_id[event_id] != proposed_by_id.get(event_id)
    ]
    if set(proposed_by_id) != set(REQUIRED_LEDGER_IDS):
        failures.append(
            f"proposed Chapter 6 ledger ID closure differs: {sorted(proposed_by_id)}"
        )
    if missing_ledger:
        failures.append(f"missing Chapter 6 correction records: {missing_ledger}")
    if differing_ledger:
        failures.append(f"integrated Chapter 6 correction records differ: {differing_ledger}")

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
        "schema": "o015-acceleration-structure-audit-v1",
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
        "proposed_ledger": {
            "path": PROPOSED_LEDGER.relative_to(ROOT).as_posix(),
            "bytes": len(proposed_ledger_bytes),
            "sha256": proposed_ledger_sha,
        },
        "integrated_ledger": {
            "path": LEDGER.relative_to(ROOT).as_posix(),
            "bytes": LEDGER.stat().st_size,
            "sha256": sha256(LEDGER.read_bytes()),
            "required_ids": REQUIRED_LEDGER_IDS,
            "missing_ids": missing_ledger,
            "differing_ids": differing_ledger,
            "exact_records_match_proposal": not missing_ledger and not differing_ledger,
        },
        "environment_count": len(source_begins),
        "environment_counts": environment_counts,
        "environment_topology_equal": (
            source_begins == target_begins and source_ends == target_ends
        ),
        "ordered_begin_environments": source_begins,
        "ordered_end_environments": source_ends,
        "source_labels": source_labels,
        "target_labels": target_labels,
        "segments": segments,
        "cross_references": {
            "source_cref": source_crefs,
            "target_cref": target_crefs,
            "source_eqref": source_eqrefs,
            "target_eqref": target_eqrefs,
            "cref_count": len(target_crefs),
            "eqref_count": len(target_eqrefs),
        },
        "absent_surface_counts": absent_surface_counts,
        "informal_prompt_count": {"source": 1, "target_dispositions": 1},
        "informal_prompt_disposition": prompt_audit,
        "correction_surface_audit": correction_surface_audit,
        "required_correction_event_count": len(REQUIRED_LEDGER_IDS),
        "required_correction_surface_count": sum(
            len(surfaces) for surfaces in REQUIRED_CORRECTION_SURFACES.values()
        ),
        "forbidden_target_typo_counts": forbidden_typo_counts,
        "formula_surface_count": {"source": len(source_math), "target": len(target_math)},
        "formula_delta_count": len(deltas),
        "formula_delta_manifest_bytes": len(manifest),
        "formula_delta_manifest_sha256": manifest_sha,
        "formula_deltas": deltas,
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
