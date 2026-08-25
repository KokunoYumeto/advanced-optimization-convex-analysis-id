#!/usr/bin/env python3
"""Deterministic open mathematical checks for Becker-03 SAGA material."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any


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


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "source" / "id-ID" / "becker-03-reduksi-varians-id.tex"
WRAPPER = ROOT / "source" / "id-ID" / "D90-BECKER-03-reduksi-varians-id.tex"
WITNESS = ROOT / "source" / "en" / "becker-03-variance-reduction-source.tex"
BOUNDARY = ROOT / "qa" / "BECKER_03_SOURCE_BOUNDARY.json"
PDF_REPORT = ROOT / "qa" / "BECKER_03_PDF_BUILD.json"
HTML_REPORT = ROOT / "qa" / "BECKER_03_HTML_BUILD.json"
PRIMARY_PAPER = ROOT / "authority" / "becker" / "related" / "saga-arxiv-1407.0202v3.pdf"
VALIDATOR = Path(__file__).resolve()
REPORT = ROOT / "qa" / "BECKER_03_MATH_VALIDATION.json"

PINNED_STACK = {"python": "3.13.9", "numpy": "2.4.4"}
PRIMARY_PAPER_BYTES = 516_033
PRIMARY_PAPER_SHA256 = "b0177cd77447c7469ca31bdfbe7773f604320a9878a46b777c899d9b6fc37c7e"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_identity(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "lines": len(data.splitlines()),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def receipt_artifact_ok(receipt: dict[str, Any], expected_schema: str) -> bool:
    artifact = receipt.get("artifact", {})
    path_value = artifact.get("path")
    if not isinstance(path_value, str):
        return False
    artifact_path = ROOT / Path(path_value)
    return (
        receipt.get("schema") == expected_schema
        and receipt.get("result") == "pass"
        and receipt.get("byte_identical_clean_builds") is True
        and receipt.get("canonical_copy_exact_match") is True
        and artifact_path.is_file()
        and artifact_path.stat().st_size == artifact.get("bytes")
        and sha256_file(artifact_path) == artifact.get("sha256")
    )


gates: list[dict[str, Any]] = []


def record(name: str, passed: bool, details: dict[str, Any]) -> None:
    gates.append({"gate": name, "pass": bool(passed), "details": details})


required_files = [
    TARGET,
    WRAPPER,
    WITNESS,
    BOUNDARY,
    PDF_REPORT,
    HTML_REPORT,
    PRIMARY_PAPER,
]
missing_files = [
    path.relative_to(ROOT).as_posix() for path in required_files if not path.is_file()
]
if missing_files:
    raise FileNotFoundError("Missing Becker-03 validation inputs: " + ", ".join(missing_files))

observed_stack = {
    "python": ".".join(str(part) for part in sys.version_info[:3]),
    "numpy": np.__version__,
}
record(
    "pinned_open_python_stack",
    observed_stack == PINNED_STACK,
    {"pinned": PINNED_STACK, "observed": observed_stack},
)

target_text = TARGET.read_text(encoding="utf-8")
wrapper_text = WRAPPER.read_text(encoding="utf-8")
boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
pdf_receipt = json.loads(PDF_REPORT.read_text(encoding="utf-8"))
html_receipt = json.loads(HTML_REPORT.read_text(encoding="utf-8"))

required_target_surfaces = {
    "finite_sum": r"f(x)=\frac{1}{N}\sum_{i=1}^{N}f_i(x)",
    "consistent_initialization": r"\phi_i^0=x_0",
    "uniform_index": r"J_k\sim\operatorname{Unif}\{1,\dots,N\}",
    "saga_estimator": r"\nabla f_{J_k}(x_k)-g_{J_k}^k+\bar g_k",
    "old_table_update_order": "Sesudah $v_k$ dihitung dari tabel lama",
    "stored_gradient_uses_xk": r"\nabla f_i(x_k),&i=J_k",
    "conditional_unbiasedness": r"\E[v_k\mid\mathcal F_k]=\nabla f(x_k)",
    "variance_identity": r"\norm{a_i^k-\bar a_k}_2^2",
    "strong_rate_factor": r"\min\left\{\frac{1}{4N},\frac{\mu}{3L}\right\}",
    "strong_rate_constant": r"\frac{2N}{3L}\bigl(f(x_0)-f(x^*)\bigr)",
    "average_iterate": r"\bar x_k=\frac1k\sum_{r=1}^{k}x_r",
    "convex_rate": r"\frac{4N}{k}",
    "complete_solutions": r"\textbf{Solusi lengkap.}",
}
missing_target_surfaces = [
    name for name, fragment in required_target_surfaces.items() if fragment not in target_text
]
record(
    "live_target_mathematical_surfaces",
    not missing_target_surfaces,
    {"required_count": len(required_target_surfaces), "missing": missing_target_surfaces},
)

required_wrapper_surfaces = {
    "source_commit": "98ed6930084c435ba0f675f7646ced1f2fd8729e",
    "source_license": "Lisensi MIT",
    "translation_license": "CC BY-SA 4.0",
    "source_credit": "Mitchell Krock",
    "saga_credit": "Aaron Defazio",
    "model_marker": "OpenAI Codex gpt-5.6-sol, Ultra",
}
missing_wrapper_surfaces = [
    name for name, fragment in required_wrapper_surfaces.items() if fragment not in wrapper_text
]
record(
    "live_wrapper_provenance_surfaces",
    not missing_wrapper_surfaces,
    {"required_count": len(required_wrapper_surfaces), "missing": missing_wrapper_surfaces},
)

expected_ranges = [
    (
        2971,
        2988,
        900,
        "b81634bf07565fcf8d2774bea7b96e565e5fdd76cf5e782c5e4eb6fb3268c5ed",
    )
]
observed_ranges = [
    (item["first_line"], item["last_line"], item["bytes"], item["sha256"])
    for item in boundary.get("selected_ranges", [])
]
boundary_ok = (
    boundary.get("schema") == "o015-becker-03-source-boundary-v1"
    and boundary.get("result") == "pass"
    and boundary.get("upstream_contact") is False
    and boundary.get("outside_range_material_imported") is False
    and boundary.get("document_terminator_imported") is False
    and boundary.get("authority", {}).get("commit")
    == "98ed6930084c435ba0f675f7646ced1f2fd8729e"
    and boundary.get("authority", {}).get("source_sha256")
    == "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8"
    and boundary.get("combined_witness", {}).get("sha256")
    == "66f243b97cd379b73d217c6a3e424db688f8ace246852cb24f78108c53186607"
    and boundary.get("combined_witness", {}).get("exact_expected_byte_match") is True
    and boundary.get("combined_witness", {}).get("interior_exact_source_slice_match") is True
    and observed_ranges == expected_ranges
)
record(
    "admitted_source_boundary",
    boundary_ok,
    {
        "selected_ranges": observed_ranges,
        "outside_range_material_imported": boundary.get("outside_range_material_imported"),
        "document_terminator_imported": boundary.get("document_terminator_imported"),
    },
)

primary_identity = file_identity(PRIMARY_PAPER)
record(
    "primary_saga_result_witness",
    primary_identity["bytes"] == PRIMARY_PAPER_BYTES
    and primary_identity["sha256"] == PRIMARY_PAPER_SHA256,
    {
        **primary_identity,
        "authority": "arXiv:1407.0202v3, Defazio--Bach--Lacoste-Julien, page 2 and supplement",
        "source_url": "https://arxiv.org/pdf/1407.0202v3",
        "formula_scope": "noncomposite specialization; gradient at an unconstrained differentiable minimizer is zero",
    },
)

target_path = TARGET.relative_to(ROOT).as_posix()
wrapper_path = WRAPPER.relative_to(ROOT).as_posix()


def receipt_input_hash(receipt: dict[str, Any], path: str) -> Any:
    matches = [item.get("sha256") for item in receipt.get("inputs", []) if item.get("path") == path]
    return matches[0] if len(matches) == 1 else None


pdf_ok = receipt_artifact_ok(pdf_receipt, "o015-becker-03-pdf-build-v1")
html_ok = receipt_artifact_ok(html_receipt, "o015-becker-03-html-build-v1")
build_receipts_current = (
    pdf_ok
    and html_ok
    and receipt_input_hash(pdf_receipt, target_path) == sha256_file(TARGET)
    and receipt_input_hash(pdf_receipt, wrapper_path) == sha256_file(WRAPPER)
    and receipt_input_hash(html_receipt, target_path) == sha256_file(TARGET)
    and receipt_input_hash(html_receipt, wrapper_path) == sha256_file(WRAPPER)
)
record(
    "current_deterministic_build_receipts",
    build_receipts_current,
    {"pdf_receipt_current": pdf_ok, "html_receipt_current": html_ok},
)

# Exact conditional expectation and variance identity on a rational finite sum.
component_a = [Fraction(1), Fraction(2), Fraction(3), Fraction(4)]
component_b = [Fraction(-2), Fraction(0), Fraction(1), Fraction(3)]
memory_points = [Fraction(-1), Fraction(1), Fraction(2), Fraction(4)]
x_value = Fraction(7, 3)
gradients = [a * (x_value - b) for a, b in zip(component_a, component_b)]
stored = [a * (phi - b) for a, b, phi in zip(component_a, component_b, memory_points)]
mean_gradient = sum(gradients, Fraction()) / len(gradients)
mean_stored = sum(stored, Fraction()) / len(stored)
estimators = [gradient - old + mean_stored for gradient, old in zip(gradients, stored)]
mean_estimator = sum(estimators, Fraction()) / len(estimators)
differences = [gradient - old for gradient, old in zip(gradients, stored)]
mean_difference = sum(differences, Fraction()) / len(differences)
variance_direct = sum((value - mean_gradient) ** 2 for value in estimators) / len(estimators)
variance_identity = sum((value - mean_difference) ** 2 for value in differences) / len(differences)
record(
    "conditional_unbiasedness_and_variance_identity",
    mean_estimator == mean_gradient and variance_direct == variance_identity,
    {
        "component_estimators": [str(item) for item in estimators],
        "full_gradient": str(mean_gradient),
        "estimator_mean": str(mean_estimator),
        "direct_variance": str(variance_direct),
        "identity_variance": str(variance_identity),
    },
)

# Exact old-table update: one replacement and the incremental mean agree.
chosen = 2
new_gradient = gradients[chosen]
updated = list(stored)
updated[chosen] = new_gradient
full_recomputed_mean = sum(updated, Fraction()) / len(updated)
incremental_mean = mean_stored + (new_gradient - stored[chosen]) / len(stored)
record(
    "stored_gradient_replacement_and_incremental_mean",
    full_recomputed_mean == incremental_mean
    and r"\nabla f_i(x_k),&i=J_k" in target_text
    and r"\nabla f_i(x_{k+1}),&i=J_k" not in target_text,
    {
        "chosen_zero_based_index": chosen,
        "old_mean": str(mean_stored),
        "full_recomputed_mean": str(full_recomputed_mean),
        "incremental_mean": str(incremental_mean),
        "replacement_point": "x_k",
    },
)

# Exact reproduction of the learner-facing quadratic exercise.
exercise_estimators = [Fraction(5, 2), Fraction(3, 2)]
exercise_mean = sum(exercise_estimators, Fraction()) / 2
exercise_variance = sum((item - exercise_mean) ** 2 for item in exercise_estimators) / 2
sgd_estimators = [Fraction(1), Fraction(3)]
sgd_mean = sum(sgd_estimators, Fraction()) / 2
sgd_variance = sum((item - sgd_mean) ** 2 for item in sgd_estimators) / 2
next_iterates = [Fraction(2) - Fraction(1, 10) * item for item in exercise_estimators]
record(
    "quadratic_exercise_exact_values",
    exercise_mean == 2
    and exercise_variance == Fraction(1, 4)
    and sgd_mean == 2
    and sgd_variance == 1
    and next_iterates == [Fraction(7, 4), Fraction(37, 20)],
    {
        "saga_estimators": [str(item) for item in exercise_estimators],
        "saga_mean": str(exercise_mean),
        "saga_variance": str(exercise_variance),
        "sgd_variance": str(sgd_variance),
        "next_iterates": [str(item) for item in next_iterates],
    },
)

# Exhaustive finite-horizon witness for the cited adaptive strong-convexity bound.
# f1=(x-1)^2/2, f2=(x+1)^2/2, f=x^2/2+1/2, L=mu=1.
states: dict[tuple[Fraction, Fraction, Fraction], Fraction] = {
    (Fraction(2), Fraction(1), Fraction(3)): Fraction(1)
}
expected_squared_errors: list[Fraction] = [Fraction(4)]
step = Fraction(1, 3)
for _ in range(8):
    next_states: dict[tuple[Fraction, Fraction, Fraction], Fraction] = defaultdict(Fraction)
    for (x_state, g1, g2), probability in states.items():
        table_mean = (g1 + g2) / 2
        component_gradients = (x_state - 1, x_state + 1)
        for index, current_gradient in enumerate(component_gradients):
            old = (g1, g2)[index]
            estimator = current_gradient - old + table_mean
            next_x = x_state - step * estimator
            next_table = [g1, g2]
            next_table[index] = current_gradient
            next_states[(next_x, next_table[0], next_table[1])] += probability / 2
    states = dict(next_states)
    expected_squared_errors.append(
        sum(probability * x_state * x_state for (x_state, _, _), probability in states.items())
    )
rho = Fraction(7, 8)
c_zero = Fraction(20, 3)
bounds = [rho**k * c_zero for k in range(len(expected_squared_errors))]
record(
    "strongly_convex_rate_numerical_witness",
    all(error <= bound for error, bound in zip(expected_squared_errors, bounds)),
    {
        "label": "finite exact numerical witness, not a proof",
        "N": 2,
        "L": "1",
        "mu": "1",
        "step": str(step),
        "rate_factor": str(rho),
        "C0": str(c_zero),
        "expected_squared_errors": [str(item) for item in expected_squared_errors],
        "theoretical_bounds": [str(item) for item in bounds],
    },
)

averaging_values = [Fraction(5, 2), Fraction(-1, 3), Fraction(7, 4), Fraction(2)]
average_direct = sum(averaging_values, Fraction()) / len(averaging_values)
average_incremental = Fraction()
for index, value in enumerate(averaging_values, start=1):
    average_incremental += (value - average_incremental) / index
record(
    "averaged_iterate_identity",
    average_direct == average_incremental,
    {
        "iterates": [str(item) for item in averaging_values],
        "direct_average": str(average_direct),
        "incremental_average": str(average_incremental),
    },
)

failures = [item["gate"] for item in gates if not item["pass"]]
payload = {
    "schema": "o015-becker-03-open-math-validation-v1",
    "result": "pass" if not failures else "fail",
    "status": "PASS" if not failures else "FAIL",
    "failures": failures,
    "scope": {
        "unit": "Becker module 3: variance reduction for SAA",
        "numerical_witnesses_are_not_proofs": True,
        "theorem_source": "Defazio, Bach, Lacoste-Julien, arXiv:1407.0202v3",
        "upstream_contact": False,
    },
    "determinism": {
        "pinned_stack": PINNED_STACK,
        "observed_stack": observed_stack,
        "randomness": "none; all sampled-index paths are enumerated exactly",
        "arithmetic": "fractions.Fraction for all algorithmic checks",
        "json": "UTF-8, LF, sorted keys, two-space indentation",
    },
    "inputs": {
        "target": file_identity(TARGET),
        "wrapper": file_identity(WRAPPER),
        "witness": file_identity(WITNESS),
        "source_boundary": file_identity(BOUNDARY),
        "pdf_build_receipt": file_identity(PDF_REPORT),
        "html_build_receipt": file_identity(HTML_REPORT),
        "primary_saga_paper": primary_identity,
        "validator": file_identity(VALIDATOR),
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
            "failures": failures,
            "gate_count": len(gates),
            "report": REPORT.relative_to(ROOT).as_posix(),
            "report_sha256": sha256_file(REPORT),
        },
        indent=2,
        sort_keys=True,
    )
)
raise SystemExit(0 if not failures else 1)
