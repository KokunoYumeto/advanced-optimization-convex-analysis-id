#!/usr/bin/env python3
"""Fail-closed deterministic mathematical QA for O015 Original-02.

The validator binds the live chapter, laboratory, accepted PDF/HTML/EPUB
readers, their receipts, and the reader builders by byte identity.  It checks
the mathematical inventory and corrected claim surfaces, evaluates exact
rational witnesses for every algorithmic family in the chapter, and executes
two isolated copies of the laboratory in temporary directories.  The accepted
source, laboratory outputs, builders, and readers are never mutated.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Sequence


sys.dont_write_bytecode = True
for _variable in (
    "BLIS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_variable] = "1"

import numpy as np
import numpy._core._multiarray_umath as np_core
import pypdf
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Path(__file__).resolve()
REPORT = ROOT / "qa" / "ORIGINAL_02_MATH_VALIDATION.json"

SOURCE = (
    ROOT
    / "source"
    / "id-ID"
    / "original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
)
WRAPPER = (
    ROOT
    / "source"
    / "id-ID"
    / "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
)
MACROS = ROOT / "source" / "id-ID" / "macros-id.tex"
CLASS = ROOT / "source" / "id-ID" / "shinybook.cls"
LAB = ROOT / "labs" / "original-02" / "monotone-splitting-lab.py"
LAB_JSON = ROOT / "labs" / "original-02" / "results.json"
LAB_CSV = ROOT / "labs" / "original-02" / "results.csv"
LAB_SVG = ROOT / "labs" / "original-02" / "residual.svg"

BASENAME = (
    "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id"
)
PDF = ROOT / "output" / "pdf" / f"{BASENAME}.pdf"
HTML = ROOT / "output" / "html" / f"{BASENAME}.html"
EPUB = ROOT / "output" / "epub" / f"{BASENAME}.epub"

PDF_ENGINE = ROOT / "qa" / "build_original_02_pdf_engine.py"
PDF_BUILDER = ROOT / "qa" / "build_original_02_pdf.py"
REFLOW_ENGINE = ROOT / "qa" / "build_original_02_reflow_engine.py"
REFLOW_BUILDER = ROOT / "qa" / "build_original_02_reflow.py"
PDF_RECEIPT = ROOT / "qa" / "ORIGINAL_02_PDF_BUILD.json"
HTML_RECEIPT = ROOT / "qa" / "ORIGINAL_02_HTML_BUILD.json"
EPUB_RECEIPT = ROOT / "qa" / "ORIGINAL_02_EPUB_BUILD.json"


# These identities bind this validator to the corrected, accepted live bytes.
EXPECTED_IDENTITIES: dict[str, tuple[int, str]] = {
    "source/id-ID/original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex": (
        28028,
        "0f58d7785f281dd4e10ab3630d2f22a62b388ca98fd50b0e972e1cc89d847367",
    ),
    "source/id-ID/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex": (
        5476,
        "cf8dd0e4cc31d8409bb2d8f27e1a6373adf728ba93702aa01e1a398d73a65db3",
    ),
    "source/id-ID/macros-id.tex": (
        4465,
        "135642edfaffb7ec15e02e330dde76e694abe957da5f1a401c8563f9d885c1c2",
    ),
    "source/id-ID/shinybook.cls": (
        10133,
        "83514a06b2884dcaa02575bb3409d2f8cc9cf2fc6e6aef344b442d424850f2c0",
    ),
    "labs/original-02/monotone-splitting-lab.py": (
        17904,
        "1d13f436644216104036be248ebb3ff0b1a9e45c856aef9229f17a5f26f3e119",
    ),
    "labs/original-02/results.json": (
        13503,
        "bc39d3363f02b904a27245bfe090cbf2153238a5a18ba8bf7cccbe1352672e81",
    ),
    "labs/original-02/results.csv": (
        4228,
        "da8d09cce727c98b408fe719735574977266de1b58f95a742dcb60c5d163e243",
    ),
    "labs/original-02/residual.svg": (
        9538,
        "c7bdeeed813cf36999ae2748362e547fc23de2d5ae15c6131e3fc73edeba6fd5",
    ),
    f"output/pdf/{BASENAME}.pdf": (
        453811,
        "0dee2b2c16f0f0868b2c0813462fce6ecc02ad2b71174eb4c622f23988771284",
    ),
    f"output/html/{BASENAME}.html": (
        190403,
        "ed60085e7ccbfcafa6675dc8bc4ebd728eaaf7c27ca24d35d5dbec7b742f529a",
    ),
    f"output/epub/{BASENAME}.epub": (
        48701,
        "dcde3d4e1a2070626fb86d3994667ce57095e5f8849b67ce3ebecaa145b54a86",
    ),
    "qa/build_original_02_pdf_engine.py": (
        9055,
        "d9310945db995c99c4ec352fa5c2d1a4c4d2cc72fdc437e20ab82131dd93b2e0",
    ),
    "qa/build_original_02_pdf.py": (
        2562,
        "c255b0aedf864fbadf6d58817080b4c484a263ca71741774980852f4ef057088",
    ),
    "qa/build_original_02_reflow_engine.py": (
        76168,
        "bcc5cdbd7957e0e3829fe397057f4d78a4fb9f8a4df3b6a27e54ec7252e2c8ad",
    ),
    "qa/build_original_02_reflow.py": (
        7294,
        "0cfde97b2ed274813ab8a014867187ff9d3c38a3f928353d9c9bac327d953f1e",
    ),
    "qa/ORIGINAL_02_PDF_BUILD.json": (
        6073,
        "d734ea6ecb0effdbcf710a682e9acab5996de7b502af774499d0410b2867d51a",
    ),
    "qa/ORIGINAL_02_HTML_BUILD.json": (
        6289,
        "c3564fa0ee594207bae55ecd06f6ff0b4137350a685aeadac51dc14775ebaee5",
    ),
    "qa/ORIGINAL_02_EPUB_BUILD.json": (
        7697,
        "f2f0a2782f194ffadb96e5f09a0c7a8eac68809d786f9cd68f34eb1498fe12c6",
    ),
}

EXPECTED_SEGMENTS = [
    f"d90.orig.v1.tr02.seg{index:04d}" for index in range(1, 9)
]
EXPECTED_ENVIRONMENTS = {
    "defn": 3,
    "theorem": 6,
    "prop": 3,
    "cor": 1,
    "exercise": 6,
    "proof": 10,
}


gates: list[dict[str, Any]] = []


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return f"<external-runtime>/{path.resolve().name}"


def file_identity(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": display_path(path),
        "bytes": len(data),
        "lines": len(data.splitlines()),
        "sha256": sha256_bytes(data),
    }


def bytes_identity(data: bytes) -> dict[str, Any]:
    return {"bytes": len(data), "sha256": sha256_bytes(data)}


def record(name: str, passed: bool, details: dict[str, Any]) -> None:
    gates.append({"gate": name, "pass": bool(passed), "details": details})


def compact_tex(value: str) -> str:
    return re.sub(r"\s+", "", value)


Vector = tuple[Fraction, ...]
Matrix = tuple[Vector, ...]


def vector(values: Iterable[int | Fraction]) -> Vector:
    return tuple(Fraction(value) for value in values)


def add(left: Sequence[Fraction], right: Sequence[Fraction]) -> Vector:
    return tuple(a + b for a, b in zip(left, right, strict=True))


def subtract(left: Sequence[Fraction], right: Sequence[Fraction]) -> Vector:
    return tuple(a - b for a, b in zip(left, right, strict=True))


def scale(scalar: Fraction, value: Sequence[Fraction]) -> Vector:
    return tuple(scalar * item for item in value)


def dot(left: Sequence[Fraction], right: Sequence[Fraction]) -> Fraction:
    return sum((a * b for a, b in zip(left, right, strict=True)), Fraction())


def norm_squared(value: Sequence[Fraction]) -> Fraction:
    return dot(value, value)


def matvec(matrix: Sequence[Sequence[Fraction]], value: Sequence[Fraction]) -> Vector:
    return tuple(dot(row, value) for row in matrix)


def solve2(matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]) -> Vector:
    a, b = matrix[0]
    c, d = matrix[1]
    determinant = a * d - b * c
    if determinant == 0:
        raise ZeroDivisionError("Singular exact 2x2 system")
    return (
        (d * rhs[0] - b * rhs[1]) / determinant,
        (-c * rhs[0] + a * rhs[1]) / determinant,
    )


def affine_resolvent(
    matrix: Matrix, offset: Vector, value: Vector, gamma: Fraction
) -> Vector:
    system = (
        (1 + gamma * matrix[0][0], gamma * matrix[0][1]),
        (gamma * matrix[1][0], 1 + gamma * matrix[1][1]),
    )
    rhs = add(value, scale(gamma, offset))
    return solve2(system, rhs)


def soft_scalar(value: Fraction, threshold: Fraction) -> Fraction:
    if value > threshold:
        return value - threshold
    if value < -threshold:
        return value + threshold
    return Fraction()


def soft_vector(value: Vector, threshold: Fraction) -> Vector:
    return tuple(soft_scalar(item, threshold) for item in value)


def normalized_visible_text(raw: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", raw)
    unescaped = html.unescape(without_tags)
    normalized = unicodedata.normalize("NFKC", unescaped)
    return re.sub(r"\s+", " ", normalized).strip()


def run_lab_copy(tag: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"o015-original02-{tag}-") as temporary:
        run_dir = Path(temporary)
        script = run_dir / LAB.name
        shutil.copyfile(LAB, script)
        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONHASHSEED": "0",
                "PYTHONIOENCODING": "utf-8",
            }
        )
        completed = subprocess.run(
            [sys.executable, "-B", str(script)],
            cwd=run_dir,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
        outputs: dict[str, bytes] = {}
        for name in ("results.json", "results.csv", "residual.svg"):
            output = run_dir / name
            if output.is_file():
                outputs[name] = output.read_bytes()
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "script": script.read_bytes(),
            "outputs": outputs,
        }


def parsed_csv_rows(data: bytes) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with io.StringIO(data.decode("utf-8"), newline="") as stream:
        for raw in csv.DictReader(stream):
            row: dict[str, Any] = {
                "method": raw["method"],
                "iteration": int(raw["iteration"]),
            }
            for field in (
                "x1",
                "x2",
                "norm",
                "error_to_reference",
                "fixed_point_residual",
                "inclusion_residual",
            ):
                row[field] = float(raw[field])
            rows.append(row)
    return rows


def exact_active_set_candidates(
    matrix: Matrix, offset: Vector, regularization: Fraction
) -> list[tuple[Vector, tuple[int, int], Vector]]:
    candidates: list[tuple[Vector, tuple[int, int], Vector]] = []
    for first in (-1, 0, 1):
        for second in (-1, 0, 1):
            pattern = (first, second)
            active = [index for index, sign in enumerate(pattern) if sign]
            point = [Fraction(), Fraction()]
            if len(active) == 1:
                index = active[0]
                point[index] = (
                    offset[index] - regularization * pattern[index]
                ) / matrix[index][index]
            elif len(active) == 2:
                rhs = tuple(
                    offset[index] - regularization * pattern[index]
                    for index in range(2)
                )
                point[:] = solve2(matrix, rhs)
            exact_point = tuple(point)
            if any(exact_point[index] * pattern[index] <= 0 for index in active):
                continue
            residual = subtract(matvec(matrix, exact_point), offset)
            zero = [index for index, sign in enumerate(pattern) if not sign]
            if any(abs(residual[index]) > regularization for index in zero):
                continue
            if any(
                residual[index] + regularization * pattern[index] != 0
                for index in active
            ):
                continue
            subgradient = tuple(
                Fraction(pattern[index])
                if pattern[index]
                else -residual[index] / regularization
                for index in range(2)
            )
            candidates.append((exact_point, pattern, subgradient))
    return candidates


def main() -> int:
    expected_paths = {relative: ROOT / relative for relative in EXPECTED_IDENTITIES}
    missing = [relative for relative, path in expected_paths.items() if not path.is_file()]
    record(
        "required_live_inputs_tools_and_readers_present",
        not missing,
        {"required_count": len(expected_paths), "missing": missing},
    )
    if missing:
        return write_report({}, {}, {})

    initial_identities = {
        relative: file_identity(path) for relative, path in expected_paths.items()
    }
    tool_paths = {
        "validator": VALIDATOR,
        "python_executable": Path(sys.executable),
        "numpy_package": Path(np.__file__),
        "numpy_core_extension": Path(np_core.__file__),
        "pypdf_package": Path(pypdf.__file__),
    }
    initial_tool_identities = {
        name: file_identity(path) for name, path in tool_paths.items()
    }
    identity_mismatches: dict[str, Any] = {}
    for relative, (expected_bytes, expected_hash) in EXPECTED_IDENTITIES.items():
        observed = initial_identities[relative]
        if observed["bytes"] != expected_bytes or observed["sha256"] != expected_hash:
            identity_mismatches[relative] = {
                "expected": {"bytes": expected_bytes, "sha256": expected_hash},
                "observed": {
                    "bytes": observed["bytes"],
                    "sha256": observed["sha256"],
                },
            }
    record(
        "exact_input_tool_and_reader_identity_binding",
        not identity_mismatches,
        {
            "bound_file_count": len(EXPECTED_IDENTITIES),
            "mismatches": identity_mismatches,
        },
    )

    source_text = SOURCE.read_text(encoding="utf-8")
    lab_text = LAB.read_text(encoding="utf-8")
    compact_source = compact_tex(source_text)

    segments = re.findall(r"% segment-id:\s*(\S+)", source_text)
    labels = re.findall(r"\\label\{([^}]+)\}", source_text)
    environment_counts = {
        environment: len(
            re.findall(r"\\begin\{" + re.escape(environment) + r"\}", source_text)
        )
        for environment in EXPECTED_ENVIRONMENTS
    }
    hint_count = source_text.count(r"\textbf{Petunjuk bertahap.}")
    solution_count = source_text.count(r"\textbf{Solusi lengkap.}")
    inventory_ok = (
        segments == EXPECTED_SEGMENTS
        and len(segments) == len(set(segments)) == 8
        and len(labels) == len(set(labels)) == 53
        and environment_counts == EXPECTED_ENVIRONMENTS
        and hint_count == 6
        and solution_count == 6
    )
    record(
        "source_inventory_exact",
        inventory_ok,
        {
            "segment_ids": segments,
            "segment_id_count": len(segments),
            "label_count": len(labels),
            "unique_label_count": len(set(labels)),
            "environment_counts": environment_counts,
            "hint_count": hint_count,
            "complete_solution_count": solution_count,
        },
    )

    required_source_fragments = {
        "vi_inequality": r"\inner{F(x^*)}{y-x^*}\geq0",
        "vi_inclusion": r"0\in F(x^*)+N_C(x^*)",
        "vi_projection": r"x^*=P_C\bigl(x^*-\gamma F(x^*)\bigr)",
        "contraction_range": r"0<\gamma<\frac{2\mu}{L^2}",
        "contraction_factor": r"q=\sqrt{1-2\gamma\mu+\gamma^2L^2}<1",
        "resolvent": r"J_{\gamma A}=(I+\gamma A)^{-1}",
        "reflected_resolvent": r"R_{\gamma A}=2J_{\gamma A}-I",
        "firmness": r"\norm{J_{\gamma A}x-J_{\gamma A}y}^2\leq\inner{J_{\gamma A}x-J_{\gamma A}y}{x-y}",
        "ppa": r"x_{k+1}=J_{\gamma A}x_k",
        "ppa_fejer": r"\norm{x_{k+1}-z}^2+\norm{x_{k+1}-x_k}^2\leq\norm{x_k-z}^2",
        "cocoercivity": r"\inner{Bx-By}{x-y}\geq\beta\norm{Bx-By}^2",
        "forward_backward": r"T_{\mathrm{FB}}=J_{\gamma A}(I-\gamma B)",
        "forward_backward_range": r"0<\gamma<2\beta",
        "averaged_parameter": r"2\beta/(4\beta-\gamma)\in(0,1)",
        "extragradient_first": r"y_k=P_C\bigl(x_k-\gamma F(x_k)\bigr)",
        "extragradient_second": r"x_{k+1}=P_C\bigl(x_k-\gamma F(y_k)\bigr)",
        "extragradient_range": r"0<\gamma<\frac1L",
        "extragradient_fejer": r"-(1-\gamma L)\bigl(\norm{x_k-y_k}^2+\norm{y_k-x_{k+1}}^2\bigr)",
        "douglas_rachford_order": r"\frac12\bigl(I+R_{\gamma A}R_{\gamma B}\bigr)=I-J_{\gamma B}+J_{\gamma A}(2J_{\gamma B}-I)",
        "douglas_rachford_shadow": r"x_k=J_{\gamma B}y_k",
        "skew_forward_factor": r"\norm{x_{k+1}}^2=(1+\gamma^2\omega^2)\norm{x_k}^2",
        "skew_resolvent_factor": r"\frac{1}{\sqrt{1+\gamma^2\omega^2}}\norm{x_k}",
        "lab_beta": r"\beta=\frac{\mu}{\mu^2+\omega^2}",
    }
    missing_surfaces = [
        name
        for name, fragment in required_source_fragments.items()
        if compact_tex(fragment) not in compact_source
    ]
    record(
        "chapter_math_claim_surfaces_exact",
        not missing_surfaces,
        {
            "required_count": len(required_source_fragments),
            "missing": missing_surfaces,
        },
    )

    minty_premise = re.search(
        r"Untuk\s+operator\s+monoton\s+\$A\$,\s+teorema\s+Minty",
        source_text,
    ) is not None
    mu_le_l = r"$0<\mu\leq L$" in source_text
    corrected_title = r"\begin{exercise}[Dari VI ke kerucut normal]" in source_text
    record(
        "corrected_minty_contraction_and_terminology_surfaces",
        minty_premise and mu_le_l and corrected_title,
        {
            "minty_monotonicity_premise": minty_premise,
            "mu_le_L_hypothesis": mu_le_l,
            "kerucut_normal_word_order": corrected_title,
        },
    )

    required_lab_fragments = {
        "beta": "BETA = MU / (MU * MU + OMEGA * OMEGA)",
        "upper_bound": "FB_UPPER_BOUND = 2.0 * BETA",
        "soft_threshold": "np.sign(x) * np.maximum(np.abs(x) - threshold, 0.0)",
        "fixed_point_map": "x - gamma * (MATRIX @ x - B_VECTOR), gamma * LAMBDA",
        "linear_resolvent_system": "np.eye(2, dtype=np.float64) + gamma * MATRIX",
        "linear_resolvent_rhs": "v + gamma * B_VECTOR",
        "dr_shadow_scale": "soft_threshold(y, DR_GAMMA * LAMBDA)",
        "dr_residual_scale": 'observation("douglas_rachford", iteration, shadow, DR_GAMMA)',
        "dr_update": "y = y + other - shadow",
        "semantic_growth_baseline": 'row["method"] == "forward_backward_outside_range"',
        "active_set": "for s0 in (-1, 0, 1):",
    }
    missing_lab_surfaces = [
        name for name, fragment in required_lab_fragments.items() if fragment not in lab_text
    ]
    stale_positional_baseline = "rows[2 * len(CHECKPOINTS)]" in lab_text
    record(
        "live_lab_formula_and_correction_surfaces",
        not missing_lab_surfaces and not stale_positional_baseline,
        {
            "required_count": len(required_lab_fragments),
            "missing": missing_lab_surfaces,
            "stale_positional_baseline_present": stale_positional_baseline,
        },
    )

    # The O018 vocabulary is allowed only inside the explicit boundary paragraph.
    boundary_pattern = re.compile(
        r"Bab ini tidak memakai .*? dari O018\.", re.DOTALL
    )
    boundaries = boundary_pattern.findall(source_text)
    source_without_boundary = boundary_pattern.sub("", source_text)
    forbidden_o018 = (
        "branch-and-bound",
        "bilangan bulat",
        "integer programming",
        "mixed-integer",
        "pemrograman linear",
        "simpleks",
        "LP/MIP",
        "sensitivitas LP",
        "aliran jaringan",
        "optimisasi diskret",
    )
    unexpected_o018 = [
        term
        for term in forbidden_o018
        if term.casefold() in source_without_boundary.casefold()
        or term.casefold() in lab_text.casefold()
    ]
    o018_ok = (
        len(boundaries) == 1
        and source_text.casefold().count("o018") == 1
        and "tidak mengimpor" in boundaries[0]
        and not unexpected_o018
    )
    record(
        "o018_nonoverlap_boundary",
        o018_ok,
        {
            "boundary_paragraph_count": len(boundaries),
            "O018_occurrence_count": source_text.casefold().count("o018"),
            "unexpected_terms_outside_boundary": unexpected_o018,
            "lab_O018_occurrence_count": lab_text.casefold().count("o018"),
        },
    )

    # VI, normal cone, and projection equivalence: exact scalar witnesses.
    vi_details: list[dict[str, Any]] = []
    vi_ok = True
    for a, b in ((Fraction(2), Fraction(-3)), (Fraction(3), Fraction()), (Fraction(2), Fraction(5))):
        solution = max(b / a, Fraction())
        value = a * solution - b
        normal = -value
        inclusion = (solution > 0 and normal == 0) or (solution == 0 and normal <= 0)
        tests = (Fraction(), Fraction(1, 2), Fraction(2), Fraction(5), solution)
        inequality = all(value * (test - solution) >= 0 for test in tests)
        gamma = Fraction(1, 3)
        projection = max(solution - gamma * value, Fraction())
        case_ok = inclusion and inequality and projection == solution
        vi_ok = vi_ok and case_ok
        vi_details.append(
            {
                "a": str(a),
                "b": str(b),
                "solution": str(solution),
                "F_at_solution": str(value),
                "normal_cone_witness": str(normal),
                "projection": str(projection),
                "pass": case_ok,
            }
        )
    record(
        "vi_normal_cone_projection_signs_exact",
        vi_ok,
        {"arithmetic": "fractions.Fraction", "cases": vi_details},
    )

    # The corrected Minty premise is essential: this matrix is not monotone,
    # although det(I+gamma A)=1-2gamma+2gamma^2 is positive for every gamma.
    minty_counterexample_discriminant = Fraction(-4)
    minty_inner_product = Fraction(-1)
    record(
        "minty_monotonicity_premise_logically_necessary",
        minty_premise
        and minty_inner_product < 0
        and minty_counterexample_discriminant < 0,
        {
            "counterexample_matrix": [[-1, -1], [1, -1]],
            "inner_Ah_h_for_h_1_0": str(minty_inner_product),
            "determinant_polynomial": "1 - 2*gamma + 2*gamma^2",
            "discriminant": str(minty_counterexample_discriminant),
        },
    )

    # Strongly monotone linear-skew contraction identity.
    contraction_matrix: Matrix = (
        vector((2, -1)),
        vector((1, 2)),
    )
    contraction_mu = Fraction(2)
    contraction_l_squared = Fraction(5)
    contraction_gamma = Fraction(1, 2)
    q_squared = (
        1
        - 2 * contraction_gamma * contraction_mu
        + contraction_gamma**2 * contraction_l_squared
    )
    contraction_details: list[dict[str, Any]] = []
    contraction_ok = (
        contraction_mu**2 <= contraction_l_squared
        and 0 < contraction_gamma < 2 * contraction_mu / contraction_l_squared
        and 0 <= q_squared < 1
    )
    for displacement in (vector((1, 0)), vector((2, -3)), vector((-4, 5))):
        forward = subtract(
            displacement,
            scale(contraction_gamma, matvec(contraction_matrix, displacement)),
        )
        observed = norm_squared(forward)
        expected = q_squared * norm_squared(displacement)
        contraction_ok = contraction_ok and observed == expected
        contraction_details.append(
            {
                "h": [str(item) for item in displacement],
                "observed_squared_norm": str(observed),
                "q_squared_times_norm": str(expected),
            }
        )
    record(
        "strong_monotonicity_contraction_identity_exact",
        contraction_ok,
        {
            "mu": str(contraction_mu),
            "L_squared": str(contraction_l_squared),
            "gamma": str(contraction_gamma),
            "upper_bound": str(2 * contraction_mu / contraction_l_squared),
            "q_squared": str(q_squared),
            "checks": contraction_details,
        },
    )

    # Resolvent identity, firm nonexpansiveness, reflected nonexpansiveness,
    # and the proximal-point Fejer inequality, all in exact arithmetic.
    zero = vector((0, 0))
    resolvent_gamma = Fraction(1, 3)
    resolvent_pairs = (
        (vector((3, -2)), vector((-1, 4))),
        (vector((1, 0)), vector((0, 0))),
        (vector((-5, 2)), vector((2, -3))),
    )
    resolvent_checks: list[dict[str, Any]] = []
    resolvent_ok = True
    for first, second in resolvent_pairs:
        p = affine_resolvent(contraction_matrix, zero, first, resolvent_gamma)
        q = affine_resolvent(contraction_matrix, zero, second, resolvent_gamma)
        p_identity = add(p, scale(resolvent_gamma, matvec(contraction_matrix, p)))
        q_identity = add(q, scale(resolvent_gamma, matvec(contraction_matrix, q)))
        output_difference = subtract(p, q)
        input_difference = subtract(first, second)
        firm_slack = dot(output_difference, input_difference) - norm_squared(output_difference)
        reflection_difference = subtract(
            scale(2, output_difference), input_difference
        )
        reflected_slack = norm_squared(input_difference) - norm_squared(reflection_difference)
        case_ok = (
            p_identity == first
            and q_identity == second
            and firm_slack >= 0
            and reflected_slack >= 0
        )
        resolvent_ok = resolvent_ok and case_ok
        resolvent_checks.append(
            {
                "firm_slack": str(firm_slack),
                "reflected_nonexpansive_slack": str(reflected_slack),
                "pass": case_ok,
            }
        )

    ppa_point = vector((3, -2))
    ppa_slacks: list[str] = []
    initial_ppa_norm = norm_squared(ppa_point)
    for _ in range(8):
        next_point = affine_resolvent(
            contraction_matrix, zero, ppa_point, resolvent_gamma
        )
        slack = (
            norm_squared(ppa_point)
            - norm_squared(next_point)
            - norm_squared(subtract(next_point, ppa_point))
        )
        ppa_slacks.append(str(slack))
        resolvent_ok = resolvent_ok and slack >= 0
        ppa_point = next_point
    resolvent_ok = resolvent_ok and norm_squared(ppa_point) < initial_ppa_norm
    record(
        "resolvent_firmness_reflection_and_ppa_fejer_exact",
        resolvent_ok,
        {
            "gamma": str(resolvent_gamma),
            "pair_checks": resolvent_checks,
            "ppa_fejer_slacks": ppa_slacks,
            "ppa_initial_squared_norm": str(initial_ppa_norm),
            "ppa_eighth_squared_norm": str(norm_squared(ppa_point)),
        },
    )

    # Frozen linear-skew inclusion, cocoercivity, FB ranges, and fixed point.
    lab_matrix: Matrix = (
        vector((1, Fraction(-3, 2))),
        vector((Fraction(3, 2), 1)),
    )
    lab_offset = vector((Fraction(6, 5), Fraction(-7, 10)))
    regularization = Fraction(1, 4)
    beta = Fraction(4, 13)
    stable_gamma = Fraction(2, 5)
    diagnostic_gamma = Fraction(9, 10)
    upper_bound = 2 * beta
    reference = vector((Fraction(11, 130), Fraction(-15, 26)))
    reference_sign = vector((1, -1))
    affine_at_reference = subtract(matvec(lab_matrix, reference), lab_offset)
    inclusion_at_reference = add(
        affine_at_reference, scale(regularization, reference_sign)
    )
    fb_checks: list[dict[str, Any]] = []
    fb_ok = (
        stable_gamma < upper_bound < diagnostic_gamma
        and inclusion_at_reference == zero
    )
    for displacement in (vector((1, 0)), vector((2, -3)), vector((-4, 5))):
        image = matvec(lab_matrix, displacement)
        left = dot(image, displacement)
        right = beta * norm_squared(image)
        fb_ok = fb_ok and left == right
        fb_checks.append(
            {"h": [str(item) for item in displacement], "left": str(left), "right": str(right)}
        )
    fixed_points: dict[str, list[str]] = {}
    for name, gamma in (
        ("stable", stable_gamma),
        ("outside", diagnostic_gamma),
    ):
        forward_argument = subtract(reference, scale(gamma, affine_at_reference))
        mapped = soft_vector(forward_argument, gamma * regularization)
        fixed_points[name] = [str(item) for item in mapped]
        fb_ok = fb_ok and mapped == reference
    stable_forward_factor_squared = (
        1 - 2 * stable_gamma + stable_gamma**2 * Fraction(13, 4)
    )
    diagnostic_forward_factor_squared = (
        1 - 2 * diagnostic_gamma + diagnostic_gamma**2 * Fraction(13, 4)
    )
    fb_ok = (
        fb_ok
        and stable_forward_factor_squared < 1
        and diagnostic_forward_factor_squared > 1
    )
    record(
        "cocoercivity_forward_backward_ranges_and_fixed_point_exact",
        fb_ok,
        {
            "beta": str(beta),
            "upper_bound": str(upper_bound),
            "stable_gamma": str(stable_gamma),
            "diagnostic_gamma": str(diagnostic_gamma),
            "stable_forward_factor_squared": str(stable_forward_factor_squared),
            "diagnostic_forward_factor_squared": str(diagnostic_forward_factor_squared),
            "cocoercivity_checks": fb_checks,
            "mapped_reference": fixed_points,
        },
    )

    # Pure skew forward/extragradient/resolvent factors and Fejer inequality.
    skew: Matrix = (vector((0, -1)), vector((1, 0)))
    skew_gamma = Fraction(3, 5)
    skew_point = vector((Fraction(5, 4), Fraction(-3, 4)))
    skew_image = matvec(skew, skew_point)
    skew_forward = subtract(skew_point, scale(skew_gamma, skew_image))
    extragradient_y = skew_forward
    extragradient_next = subtract(
        skew_point, scale(skew_gamma, matvec(skew, extragradient_y))
    )
    extragradient_closed = subtract(
        scale(1 - skew_gamma**2, skew_point), scale(skew_gamma, skew_image)
    )
    skew_resolvent = affine_resolvent(skew, zero, skew_point, skew_gamma)
    forward_factor_squared = Fraction(1) + skew_gamma**2
    extragradient_factor_squared = (
        1 - skew_gamma**2 + skew_gamma**4
    )
    resolvent_factor_squared = 1 / (1 + skew_gamma**2)
    fejer_right = norm_squared(skew_point) - (1 - skew_gamma) * (
        norm_squared(subtract(skew_point, extragradient_y))
        + norm_squared(subtract(extragradient_y, extragradient_next))
    )
    extragradient_ok = (
        norm_squared(skew_forward)
        == forward_factor_squared * norm_squared(skew_point)
        and extragradient_next == extragradient_closed
        and norm_squared(extragradient_next)
        == extragradient_factor_squared * norm_squared(skew_point)
        and norm_squared(skew_resolvent)
        == resolvent_factor_squared * norm_squared(skew_point)
        and norm_squared(extragradient_next) <= fejer_right
        and forward_factor_squared > 1
        and extragradient_factor_squared < 1
        and resolvent_factor_squared < 1
    )
    record(
        "extragradient_and_skew_factors_exact",
        extragradient_ok,
        {
            "gamma": str(skew_gamma),
            "forward_factor_squared": str(forward_factor_squared),
            "extragradient_factor_squared": str(extragradient_factor_squared),
            "resolvent_factor_squared": str(resolvent_factor_squared),
            "extragradient_squared_norm": str(norm_squared(extragradient_next)),
            "fejer_right_hand_side": str(fejer_right),
            "fejer_slack": str(fejer_right - norm_squared(extragradient_next)),
        },
    )

    # Exact active-set solution and Douglas--Rachford order/scaling.
    candidates = exact_active_set_candidates(lab_matrix, lab_offset, regularization)
    dr_gamma = Fraction(7, 10)
    dual_element = scale(regularization, reference_sign)
    dr_fixed = add(reference, scale(dr_gamma, dual_element))
    dr_shadow = soft_vector(dr_fixed, dr_gamma * regularization)
    dr_reflected = subtract(scale(2, dr_shadow), dr_fixed)
    dr_other = affine_resolvent(lab_matrix, lab_offset, dr_reflected, dr_gamma)
    dr_next = add(dr_fixed, subtract(dr_other, dr_shadow))
    dr_ok = (
        candidates == [(reference, (1, -1), reference_sign)]
        and dr_shadow == reference
        and dr_other == reference
        and dr_next == dr_fixed
    )
    record(
        "active_set_reference_and_douglas_rachford_order_scaling_exact",
        dr_ok,
        {
            "active_set_candidate_count": len(candidates),
            "reference": [str(item) for item in reference],
            "pattern": [1, -1],
            "subgradient": [str(item) for item in reference_sign],
            "gamma": str(dr_gamma),
            "fixed_y": [str(item) for item in dr_fixed],
            "J_gamma_B_y": [str(item) for item in dr_shadow],
            "J_gamma_A_reflection": [str(item) for item in dr_other],
            "T_DR_y": [str(item) for item in dr_next],
        },
    )

    # Verify reader receipts against live reader and input bytes.
    receipt_specs = (
        ("pdf", PDF_RECEIPT, PDF),
        ("html", HTML_RECEIPT, HTML),
        ("epub", EPUB_RECEIPT, EPUB),
    )
    receipt_details: dict[str, Any] = {}
    receipts_ok = True
    for name, receipt_path, artifact_path in receipt_specs:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        artifact_identity = file_identity(artifact_path)
        artifact = receipt.get("artifact", {})
        input_failures: list[str] = []
        for declared in receipt.get("inputs", []):
            declared_path = ROOT / declared.get("path", "")
            if not declared_path.is_file():
                input_failures.append(f"missing:{declared.get('path')}")
                continue
            actual = file_identity(declared_path)
            if (
                actual["bytes"] != declared.get("bytes")
                or actual["sha256"] != declared.get("sha256")
            ):
                input_failures.append(f"identity:{declared.get('path')}")
        inventory = receipt.get("source_inventory")
        inventory_ok_for_reader = True
        if name in {"html", "epub"}:
            expected_reader_environments = {
                **EXPECTED_ENVIRONMENTS,
                "lemma": 0,
            }
            inventory_ok_for_reader = (
                inventory is not None
                and inventory.get("segment_ids") == EXPECTED_SEGMENTS
                and inventory.get("source_label_count") == 53
                and inventory.get("environment_counts")
                == expected_reader_environments
                and inventory.get("staged_hint_count") == 6
                and inventory.get("complete_solution_count") == 6
            )
        reader_ok = (
            receipt.get("result") == "pass"
            and artifact.get("path") == display_path(artifact_path)
            and artifact.get("bytes") == artifact_identity["bytes"]
            and artifact.get("sha256") == artifact_identity["sha256"]
            and not input_failures
            and inventory_ok_for_reader
        )
        receipts_ok = receipts_ok and reader_ok
        receipt_details[name] = {
            "pass": reader_ok,
            "artifact": artifact_identity,
            "declared_input_count": len(receipt.get("inputs", [])),
            "input_failures": input_failures,
            "source_inventory_verified": inventory_ok_for_reader,
        }
    record(
        "accepted_reader_receipts_and_input_closure",
        receipts_ok,
        receipt_details,
    )

    html_raw = HTML.read_text(encoding="utf-8")
    html_visible = normalized_visible_text(html_raw)
    with zipfile.ZipFile(EPUB, "r") as archive:
        epub_names = archive.namelist()
        epub_xhtml = "\n".join(
            archive.read(name).decode("utf-8")
            for name in epub_names
            if name.endswith(".xhtml")
        )
        epub_embedded: dict[str, bool] = {}
        for live in (LAB, LAB_JSON, LAB_CSV, LAB_SVG):
            matches = [
                name for name in epub_names if name.endswith(f"/lab/{live.name}")
            ]
            epub_embedded[live.name] = (
                len(matches) == 1 and archive.read(matches[0]) == live.read_bytes()
            )
    epub_visible = normalized_visible_text(epub_xhtml)
    pdf_reader = PdfReader(str(PDF))
    pdf_visible = unicodedata.normalize(
        "NFKC", "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
    )
    pdf_compact = re.sub(r"\s+", "", pdf_visible)
    html_compact = re.sub(r"\s+", "", html_visible)
    epub_compact = re.sub(r"\s+", "", epub_visible)
    rendered_checks = {
        "pdf_minty": "Untukoperatormonoton" in pdf_compact
        and "monotonmaksimaljikadanhanyajika" in pdf_compact,
        "pdf_mu_le_L": "dengan0<μ≤L" in pdf_compact,
        "pdf_terminology": "DariVIkekerucutnormal" in pdf_compact,
        "html_minty": "Untuk operator monoton" in html_visible
        and "teorema Minty" in html_visible,
        "html_mu_le_L": r"dengan \(0<\mu\leq L\)" in html_visible,
        "html_terminology": "Dari VI ke kerucut normal" in html_visible,
        "epub_minty": "Untuk operator monoton" in epub_visible
        and "teorema Minty" in epub_visible,
        "epub_mu_le_L": "dengan0<μ≤L" in epub_compact,
        "epub_terminology": "Dari VI ke kerucut normal" in epub_visible,
        "epub_lab_bytes": all(epub_embedded.values()),
    }
    record(
        "corrected_claims_present_in_all_accepted_readers",
        all(rendered_checks.values()) and len(pdf_reader.pages) == 16,
        {
            "checks": rendered_checks,
            "pdf_pages": len(pdf_reader.pages),
            "epub_embedded_lab": epub_embedded,
            "segment_ids_present_in_html": all(
                segment in html_raw for segment in EXPECTED_SEGMENTS
            ),
            "segment_ids_present_in_epub": all(
                segment in epub_xhtml for segment in EXPECTED_SEGMENTS
            ),
        },
    )

    # Two isolated full laboratory executions; compare both with live outputs.
    replay_one = run_lab_copy("run1")
    replay_two = run_lab_copy("run2")
    expected_output_names = {"results.json", "results.csv", "residual.svg"}
    replay_outputs_present = (
        set(replay_one["outputs"]) == expected_output_names
        and set(replay_two["outputs"]) == expected_output_names
    )
    replay_byte_identical = replay_outputs_present and all(
        replay_one["outputs"][name] == replay_two["outputs"][name]
        for name in expected_output_names
    )
    live_outputs = {
        "results.json": LAB_JSON.read_bytes(),
        "results.csv": LAB_CSV.read_bytes(),
        "residual.svg": LAB_SVG.read_bytes(),
    }
    replay_matches_live = replay_outputs_present and all(
        replay_one["outputs"][name] == live_outputs[name]
        for name in expected_output_names
    )
    replay_ok = (
        replay_one["returncode"] == 0
        and replay_two["returncode"] == 0
        and replay_one["script"] == LAB.read_bytes()
        and replay_two["script"] == LAB.read_bytes()
        and replay_byte_identical
        and replay_matches_live
    )
    record(
        "lab_two_clean_replays_byte_identical_and_match_live",
        replay_ok,
        {
            "runs": 2,
            "returncodes": [replay_one["returncode"], replay_two["returncode"]],
            "script_copy_exact": replay_one["script"] == LAB.read_bytes()
            and replay_two["script"] == LAB.read_bytes(),
            "byte_identical_between_runs": replay_byte_identical,
            "byte_identical_to_live_outputs": replay_matches_live,
            "outputs": {
                name: bytes_identity(replay_one["outputs"][name])
                for name in sorted(replay_one["outputs"])
            },
            "stdout_sha256": [
                sha256_bytes(replay_one["stdout"]),
                sha256_bytes(replay_two["stdout"]),
            ],
            "stderr": [
                replay_one["stderr"].decode("utf-8", errors="replace"),
                replay_two["stderr"].decode("utf-8", errors="replace"),
            ],
        },
    )

    replay_payload = json.loads(replay_one["outputs"]["results.json"])
    replay_csv = parsed_csv_rows(replay_one["outputs"]["results.csv"])
    svg_root = ET.fromstring(replay_one["outputs"]["residual.svg"])
    svg_polylines = sum(1 for node in svg_root.iter() if node.tag.endswith("polyline"))
    svg_circles = sum(1 for node in svg_root.iter() if node.tag.endswith("circle"))
    output_structure_ok = (
        replay_payload.get("schema") == "o015-original-02-monotone-splitting-lab-v1"
        and replay_payload.get("result") == "pass"
        and replay_payload.get("rows") == replay_csv
        and len(replay_csv) == 30
        and svg_polylines == 3
        and svg_circles == 30
    )
    record(
        "lab_json_csv_svg_structural_consistency",
        output_structure_ok,
        {
            "row_count_json": len(replay_payload.get("rows", [])),
            "row_count_csv": len(replay_csv),
            "svg_polyline_count": svg_polylines,
            "svg_circle_count": svg_circles,
            "json_csv_rows_exact": replay_payload.get("rows") == replay_csv,
        },
    )

    expected_parameters = {
        "mu": 1.0,
        "omega": 1.5,
        "lambda": 0.25,
        "b": [1.2, -0.7],
        "x0": [2.5, -2.0],
        "y0": [2.5, -2.0],
        "iterations": 200,
        "checkpoints": [0, 1, 2, 5, 10, 20, 40, 80, 120, 200],
        "forward_backward_stable_gamma": 0.4,
        "forward_backward_diagnostic_gamma": 0.9,
        "douglas_rachford_gamma": 0.7,
    }
    expected_final_residuals = {
        "forward_backward_stable": {
            "fixed_point_residual": 2.401779625492033e-15,
            "inclusion_residual": 5.821000005975887e-15,
            "error_to_reference": 3.1780134079895106e-15,
        },
        "forward_backward_outside_range": {
            "fixed_point_residual": 6.49792884459655e26,
            "inclusion_residual": 7.219920938440611e26,
            "error_to_reference": 4.004891561283648e26,
        },
        "douglas_rachford": {
            "fixed_point_residual": 2.7755575615628914e-16,
            "inclusion_residual": 4.002966042486721e-16,
            "error_to_reference": 1.8875832159447664e-16,
        },
    }
    final_payload = replay_payload.get("final", {})
    observed_final_residuals = {
        method: {
            field: final_payload.get(method, {}).get(field)
            for field in expected
        }
        for method, expected in expected_final_residuals.items()
    }
    skew_payload = replay_payload.get("pure_skew_diagnostic", {})
    skew_methods = skew_payload.get("methods", {})
    expected_skew_factors = {
        "forward": math.sqrt(1.0 + 0.6**2),
        "extragradient": math.sqrt(1.0 - 0.6**2 + 0.6**4),
        "resolvent": 1.0 / math.sqrt(1.0 + 0.6**2),
    }
    observed_skew_factors = {
        method: skew_methods.get(method, {}).get("exact_one_step_factor")
        for method in expected_skew_factors
    }
    outside_initial = next(
        row
        for row in replay_payload.get("rows", [])
        if row.get("method") == "forward_backward_outside_range"
        and row.get("iteration") == 0
    )
    numeric_ok = (
        replay_payload.get("parameters") == expected_parameters
        and replay_payload.get("theory")
        == {
            "beta": 4.0 / 13.0,
            "forward_backward_upper_bound": 8.0 / 13.0,
            "stable_step_inside_open_interval": True,
            "diagnostic_step_outside_proved_interval": True,
        }
        and observed_final_residuals == expected_final_residuals
        and observed_skew_factors == expected_skew_factors
        and replay_payload.get("reference", {}).get("pattern") == [1, -1]
        and replay_payload.get("reference", {}).get("subgradient") == [1.0, -1.0]
        and abs(replay_payload.get("reference", {}).get("x", [0.0])[0] - 11.0 / 130.0)
        <= 1e-15
        and abs(replay_payload.get("reference", {}).get("x", [0.0, 0.0])[1] + 15.0 / 26.0)
        <= 1e-15
        and replay_payload.get("reference", {}).get("inclusion_residual", math.inf)
        <= 2e-15
        and replay_payload.get("resolvent_probe", {}).get("identity_error", math.inf)
        <= 1e-14
        and final_payload["forward_backward_stable"]["inclusion_residual"] < 1e-10
        and final_payload["douglas_rachford"]["inclusion_residual"] < 1e-10
        and final_payload["forward_backward_outside_range"]["inclusion_residual"]
        > outside_initial["inclusion_residual"]
        and skew_methods["forward"]["exact_one_step_factor"] > 1.0
        and skew_methods["extragradient"]["exact_one_step_factor"] < 1.0
        and skew_methods["resolvent"]["exact_one_step_factor"] < 1.0
        and all(
            skew_methods[method]["factor_absolute_error"] <= 1e-14
            for method in expected_skew_factors
        )
    )
    record(
        "lab_exact_ranges_residuals_reference_and_factors",
        numeric_ok,
        {
            "parameters": replay_payload.get("parameters"),
            "theory": replay_payload.get("theory"),
            "reference": replay_payload.get("reference"),
            "resolvent_probe": replay_payload.get("resolvent_probe"),
            "final_residuals": observed_final_residuals,
            "outside_initial_inclusion_residual": outside_initial[
                "inclusion_residual"
            ],
            "skew_factors": observed_skew_factors,
        },
    )

    final_identities = {
        relative: file_identity(path) for relative, path in expected_paths.items()
    }
    final_tool_identities = {
        name: file_identity(path) for name, path in tool_paths.items()
    }
    stable_inputs = initial_identities == final_identities
    stable_tools = initial_tool_identities == final_tool_identities
    record(
        "inputs_and_execution_tools_stable_during_validation",
        stable_inputs and stable_tools,
        {
            "inputs_stable": stable_inputs,
            "tools_stable": stable_tools,
            "input_sha256": {
                relative: identity["sha256"]
                for relative, identity in final_identities.items()
            },
            "tool_sha256": {
                name: identity["sha256"]
                for name, identity in final_tool_identities.items()
            },
        },
    )

    tool_versions = {
        "python": ".".join(str(part) for part in sys.version_info[:3]),
        "numpy": np.__version__,
        "pypdf": pypdf.__version__,
    }
    return write_report(final_identities, final_tool_identities, tool_versions)


def write_report(
    input_identities: dict[str, Any],
    tool_identities: dict[str, Any],
    tool_versions: dict[str, str],
) -> int:
    failures = [gate["gate"] for gate in gates if not gate["pass"]]
    payload = {
        "schema": "o015-original-02-open-math-validation-v1",
        "result": "pass" if not failures else "fail",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "scope": {
            "unit": "Original 02: variational inequalities, monotone operators, resolvents, and splitting",
            "source_mutated_by_validator": False,
            "accepted_lab_outputs_mutated_by_validator": False,
            "accepted_readers_mutated_by_validator": False,
            "lab_replay": "two full executions in disposable temporary directories",
            "network_access": False,
            "upstream_contact": False,
            "numerical_witnesses_are_not_proofs": True,
        },
        "determinism": {
            "exact_arithmetic": "fractions.Fraction",
            "lab_runs": 2,
            "lab_outputs_required_byte_identical": [
                "results.json",
                "results.csv",
                "residual.svg",
            ],
            "thread_limits": {
                variable: os.environ.get(variable)
                for variable in (
                    "BLIS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                )
            },
            "json": "UTF-8, LF, sorted keys, two-space indentation",
        },
        "expected_identity_binding": {
            relative: {"bytes": size, "sha256": digest}
            for relative, (size, digest) in EXPECTED_IDENTITIES.items()
        },
        "inputs": input_identities,
        "tools": {
            "versions": tool_versions,
            "identities": tool_identities,
        },
        "gate_count": len(gates),
        "gates": gates,
    }
    REPORT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "gate_count": len(gates),
                "failures": failures,
                "report": file_identity(REPORT),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
