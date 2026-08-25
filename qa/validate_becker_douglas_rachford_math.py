#!/usr/bin/env python3
"""Deterministic open mathematical checks for Becker-02 Douglas--Rachford."""

from __future__ import annotations

import hashlib
import json
import os
import sys
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
TARGET = ROOT / "source" / "id-ID" / "becker-02-pemisahan-douglas-rachford-id.tex"
WRAPPER = (
    ROOT
    / "source"
    / "id-ID"
    / "D90-BECKER-02-pemisahan-douglas-rachford-id.tex"
)
WITNESS = ROOT / "source" / "en" / "becker-02-douglas-rachford-source.tex"
BOUNDARY = ROOT / "qa" / "BECKER_02_SOURCE_BOUNDARY.json"
PDF_REPORT = ROOT / "qa" / "BECKER_02_PDF_BUILD.json"
HTML_REPORT = ROOT / "qa" / "BECKER_02_HTML_BUILD.json"
VALIDATOR = Path(__file__).resolve()
REPORT = ROOT / "qa" / "BECKER_02_MATH_VALIDATION.json"

PINNED_STACK = {"python": "3.13.9", "numpy": "2.4.4"}
TOLERANCES = {
    "iteration_abs": 2.0e-13,
    "fixed_point_abs": 2.0e-13,
    "objective_abs": 2.0e-13,
    "subgradient_abs": 2.0e-13,
}


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


def max_abs(vector: np.ndarray) -> float:
    return float(np.max(np.abs(vector))) if vector.size else 0.0


def soft_threshold(vector: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(vector) * np.maximum(np.abs(vector) - threshold, 0.0)


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


required_files = [TARGET, WRAPPER, WITNESS, BOUNDARY, PDF_REPORT, HTML_REPORT]
missing_files = [path.relative_to(ROOT).as_posix() for path in required_files if not path.is_file()]
if missing_files:
    raise FileNotFoundError("Missing Becker-02 validation inputs: " + ", ".join(missing_files))

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
    "proper_gamma_zero": r"fungsi konveks proper dan semikontinu",
    "subdifferential_sum_rule": r"\partial(f+g)=\partial f+\partial g",
    "fenchel_dual_max_signs": r"-f^*(-u)-g^*(u)",
    "fenchel_dual_min_signs": r"f^*(-u)+g^*(u)",
    "proximal_resolvent_scale": r"(I+\rho\partial h)^{-1}(v)",
    "dr_x_update": r"x_k&=\prox_{\rho g}(y_k)",
    "dr_z_update": r"z_k&=\prox_{\rho f}(2x_k-y_k)",
    "dr_relaxed_update": r"y_{k+1}&=y_k+\lambda(z_k-x_k)",
    "relaxation_range": r"\lambda\in(0,2)",
    "fixed_point_g_inclusion": r"\frac{\bar y-\bar x}{\rho}\in\partial g(\bar x)",
    "fixed_point_f_inclusion": r"\frac{\bar x-\bar y}{\rho}\in\partial f(\bar x)",
    "admm_dual_scope": r"masalah dual yang sesuai",
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
    "inherited_bauschke_combettes_credit": "Bauschke dan Combettes",
    "inherited_lions_mercier_credit": "Lions dan Mercier",
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
        2750,
        2797,
        1285,
        "386f1f0f94f6433eebdd6d07e10f3ffe28ffa8650e392cb0158a389e01452cf2",
    )
]
observed_ranges = [
    (item["first_line"], item["last_line"], item["bytes"], item["sha256"])
    for item in boundary.get("selected_ranges", [])
]
boundary_ok = (
    boundary.get("schema") == "o015-becker-02-source-boundary-v1"
    and boundary.get("result") == "pass"
    and boundary.get("upstream_contact") is False
    and boundary.get("lp_material_imported") is False
    and boundary.get("authority", {}).get("commit")
    == "98ed6930084c435ba0f675f7646ced1f2fd8729e"
    and boundary.get("authority", {}).get("source_sha256")
    == "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8"
    and boundary.get("combined_witness", {}).get("sha256")
    == "fdc368741a0a88eb9d21c69d655ac6ce1b44571c2d49c6a3302e3efc4673594b"
    and boundary.get("combined_witness", {}).get("exact_expected_byte_match") is True
    and boundary.get("combined_witness", {}).get("interior_exact_source_slice_match")
    is True
    and observed_ranges == expected_ranges
)
record(
    "admitted_source_boundary",
    boundary_ok,
    {
        "commit": boundary.get("authority", {}).get("commit"),
        "source_sha256": boundary.get("authority", {}).get("source_sha256"),
        "combined_witness_sha256": boundary.get("combined_witness", {}).get("sha256"),
        "selected_ranges": observed_ranges,
        "lp_material_imported": boundary.get("lp_material_imported"),
    },
)

target_path = TARGET.relative_to(ROOT).as_posix()
wrapper_path = WRAPPER.relative_to(ROOT).as_posix()
target_hash = sha256_file(TARGET)
wrapper_hash = sha256_file(WRAPPER)


def receipt_input_hash(receipt: dict[str, Any], path: str) -> Any:
    matches = [item.get("sha256") for item in receipt.get("inputs", []) if item.get("path") == path]
    return matches[0] if len(matches) == 1 else None


pdf_ok = receipt_artifact_ok(pdf_receipt, "o015-becker-02-pdf-build-v1")
html_ok = receipt_artifact_ok(html_receipt, "o015-becker-02-html-build-v1")
build_receipts_current = (
    pdf_ok
    and html_ok
    and receipt_input_hash(pdf_receipt, target_path) == target_hash
    and receipt_input_hash(pdf_receipt, wrapper_path) == wrapper_hash
    and receipt_input_hash(html_receipt, target_path) == target_hash
    and receipt_input_hash(html_receipt, wrapper_path) == wrapper_hash
)
record(
    "current_deterministic_build_receipts",
    build_receipts_current,
    {
        "target_sha256": target_hash,
        "wrapper_sha256": wrapper_hash,
        "pdf_receipt_current": pdf_ok,
        "html_receipt_current": html_ok,
        "pdf_artifact": pdf_receipt.get("artifact"),
        "html_artifact": html_receipt.get("artifact"),
    },
)

# Exact quadratic witness for the corrected Fenchel dual signs.
a = Fraction(2)
b = Fraction(3)
c = Fraction(5)
x_star = b * c / (a + b)
u_star = b * (x_star - c)
primal_value = a * x_star * x_star / 2 + b * (x_star - c) ** 2 / 2
f_conjugate_minus_u = u_star * u_star / (2 * a)
g_conjugate_u = c * u_star + u_star * u_star / (2 * b)
dual_max_value = -f_conjugate_minus_u - g_conjugate_u
dual_min_value = f_conjugate_minus_u + g_conjugate_u
wrong_min_quadratic_coefficient = -Fraction(1, 2 * a) + Fraction(1, 2 * b)
record(
    "fenchel_dual_signs_and_strong_duality",
    x_star == 3
    and u_star == -6
    and primal_value == 15
    and dual_max_value == primal_value
    and dual_min_value == -primal_value
    and wrong_min_quadratic_coefficient < 0,
    {
        "problem": "minimize (a/2)x^2 + (b/2)(x-c)^2",
        "a": str(a),
        "b": str(b),
        "c": str(c),
        "x_star": str(x_star),
        "u_star": str(u_star),
        "primal_value": str(primal_value),
        "correct_dual_max_value": str(dual_max_value),
        "equivalent_dual_min_value": str(dual_min_value),
        "donor_wrong_min_form_quadratic_coefficient": str(
            wrong_min_quadratic_coefficient
        ),
        "donor_wrong_min_form_is_unbounded_below": True,
    },
)

# Exact relaxed Douglas--Rachford iteration on the same scalar quadratics.
rho = Fraction(2, 3)
relaxation = Fraction(3, 2)
y_value = Fraction(11)
y_fixed = Fraction(-1)
scalar_records: list[dict[str, Any]] = []
previous_error = abs(y_value - y_fixed)
monotone = True
for index in range(30):
    x_value = (y_value + rho * b * c) / (1 + rho * b)
    z_value = (2 * x_value - y_value) / (1 + rho * a)
    residual = z_value - x_value
    next_y = y_value + relaxation * residual
    next_error = abs(next_y - y_fixed)
    monotone = monotone and next_error < previous_error
    if index in (0, 1, 2, 29):
        scalar_records.append(
            {
                "iteration": index,
                "y": str(y_value),
                "x": str(x_value),
                "z": str(z_value),
                "z_minus_x": str(residual),
                "next_y": str(next_y),
            }
        )
    y_value = next_y
    previous_error = next_error

x_limit = (y_value + rho * b * c) / (1 + rho * b)
z_limit = (2 * x_limit - y_value) / (1 + rho * a)
contraction = Fraction(2, 7)
record(
    "relaxed_douglas_rachford_scalar_iteration",
    Fraction(0) < relaxation < Fraction(2)
    and monotone
    and contraction == Fraction(2, 7)
    and float(abs(y_value - y_fixed)) <= TOLERANCES["iteration_abs"]
    and float(abs(x_limit - x_star)) <= TOLERANCES["iteration_abs"]
    and float(abs(z_limit - x_limit)) <= TOLERANCES["fixed_point_abs"],
    {
        "rho": str(rho),
        "lambda": str(relaxation),
        "affine_error_contraction": str(contraction),
        "iterations": 30,
        "selected_records": scalar_records,
        "final_y": str(y_value),
        "fixed_y": str(y_fixed),
        "final_y_abs_error": float(abs(y_value - y_fixed)),
        "final_shadow_x": str(x_limit),
        "primal_x_star": str(x_star),
        "final_shadow_abs_error": float(abs(x_limit - x_star)),
        "final_fixed_point_residual_abs": float(abs(z_limit - x_limit)),
    },
)

# Nonsmooth vector witness: f=tau*||.||_1 and g=||.-c||^2/2.
c_vector = np.array([3.0, -1.0, 0.25])
tau = 1.0
rho_float = 0.75
lambda_float = 1.5
y_vector = np.array([5.0, -4.0, 2.0])
x_expected = soft_threshold(c_vector, tau)
residual_history: list[float] = []
for _index in range(200):
    x_vector = (y_vector + rho_float * c_vector) / (1.0 + rho_float)
    z_vector = soft_threshold(2.0 * x_vector - y_vector, rho_float * tau)
    residual_history.append(max_abs(z_vector - x_vector))
    y_vector = y_vector + lambda_float * (z_vector - x_vector)
x_vector = (y_vector + rho_float * c_vector) / (1.0 + rho_float)
z_vector = soft_threshold(2.0 * x_vector - y_vector, rho_float * tau)
u_from_g = (y_vector - x_vector) / rho_float
minus_u_from_f = (x_vector - y_vector) / rho_float
subgradient = (c_vector - x_vector) / tau
nonzero = np.abs(x_vector) > TOLERANCES["subgradient_abs"]
subgradient_ok = (
    max_abs(subgradient[nonzero] - np.sign(x_vector[nonzero]))
    <= TOLERANCES["subgradient_abs"]
    and max_abs(subgradient[~nonzero]) <= 1.0 + TOLERANCES["subgradient_abs"]
)
objective = 0.5 * float((x_vector - c_vector) @ (x_vector - c_vector)) + tau * float(
    np.abs(x_vector).sum()
)
expected_objective = 3.03125
record(
    "nonsmooth_fixed_point_shadow_and_subgradients",
    max_abs(x_vector - x_expected) <= TOLERANCES["iteration_abs"]
    and max_abs(z_vector - x_vector) <= TOLERANCES["fixed_point_abs"]
    and max_abs(u_from_g - (x_vector - c_vector))
    <= TOLERANCES["subgradient_abs"]
    and max_abs(minus_u_from_f - tau * subgradient)
    <= TOLERANCES["subgradient_abs"]
    and subgradient_ok
    and abs(objective - expected_objective) <= TOLERANCES["objective_abs"],
    {
        "problem": "minimize tau*||x||_1 + ||x-c||^2/2",
        "c": c_vector.tolist(),
        "tau": tau,
        "rho": rho_float,
        "lambda": lambda_float,
        "iterations": 200,
        "expected_primal_solution": x_expected.tolist(),
        "shadow_x": x_vector.tolist(),
        "reflected_prox_z": z_vector.tolist(),
        "fixed_point_y": y_vector.tolist(),
        "final_shadow_max_abs_error": max_abs(x_vector - x_expected),
        "final_z_minus_x_max_abs": max_abs(z_vector - x_vector),
        "u_in_partial_g": u_from_g.tolist(),
        "minus_u_in_partial_f": minus_u_from_f.tolist(),
        "l1_subgradient": subgradient.tolist(),
        "subgradient_conditions_pass": subgradient_ok,
        "objective": objective,
        "expected_objective": expected_objective,
        "first_residual": residual_history[0],
        "last_residual": residual_history[-1],
    },
)

failures = [item["gate"] for item in gates if not item["pass"]]
payload = {
    "schema": "o015-becker-02-open-math-validation-v1",
    "result": "pass" if not failures else "fail",
    "status": "PASS" if not failures else "FAIL",
    "failures": failures,
    "scope": {
        "unit": "Becker module 2: Douglas--Rachford splitting",
        "numerical_witnesses_are_not_proofs": True,
        "upstream_contact": False,
    },
    "determinism": {
        "pinned_stack": PINNED_STACK,
        "observed_stack": observed_stack,
        "thread_environment": {
            name: os.environ[name]
            for name in sorted(
                (
                    "BLIS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                )
            )
        },
        "randomness": "none",
        "json": "UTF-8, LF, sorted keys, two-space indentation",
    },
    "tolerances": TOLERANCES,
    "inputs": {
        "target": file_identity(TARGET),
        "wrapper": file_identity(WRAPPER),
        "witness": file_identity(WITNESS),
        "source_boundary": file_identity(BOUNDARY),
        "pdf_build_receipt": file_identity(PDF_REPORT),
        "html_build_receipt": file_identity(HTML_REPORT),
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
