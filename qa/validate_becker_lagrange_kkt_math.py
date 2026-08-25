#!/usr/bin/env python3
"""Deterministic open numerical checks for Becker module 1 (Lagrange/KKT).

The checks exercise only mathematical surfaces present in the admitted
Indonesian unit.  NumPy handles direct linear algebra and SciPy supplies
independent constrained-solver witnesses.  The witnesses support validation;
they are not substitutes for the proofs in the reader.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any


# Keep the numerical path single-threaded before importing NumPy/SciPy.
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
import scipy
from scipy.optimize import Bounds, LinearConstraint, minimize


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "source" / "id-ID" / "becker-01-dualitas-lagrange-slater-kkt-id.tex"
WRAPPER = ROOT / "source" / "id-ID" / "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex"
BOUNDARY = ROOT / "qa" / "BECKER_01_SOURCE_BOUNDARY.json"
VALIDATOR = Path(__file__).resolve()
REPORT = ROOT / "qa" / "BECKER_01_MATH_VALIDATION.json"

PINNED_STACK = {
    "python": "3.13.9",
    "numpy": "2.4.4",
    "scipy": "1.17.1",
}
TOLERANCES = {
    "algebra_abs": 5.0e-13,
    "eigenvalue_abs": 5.0e-12,
    "solver_abs": 2.0e-7,
    "solver_feasibility_abs": 2.0e-8,
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


gates: list[dict[str, Any]] = []


def record(name: str, passed: bool, details: dict[str, Any]) -> None:
    gates.append({"gate": name, "pass": bool(passed), "details": details})


observed_stack = {
    "python": ".".join(str(part) for part in sys.version_info[:3]),
    "numpy": np.__version__,
    "scipy": scipy.__version__,
}
record(
    "pinned_open_python_stack",
    observed_stack == PINNED_STACK,
    {"pinned": PINNED_STACK, "observed": observed_stack},
)


# Fail closed if the live unit or its admitted source boundary has changed.
target_text = TARGET.read_text(encoding="utf-8")
wrapper_text = WRAPPER.read_text(encoding="utf-8")
boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))

required_target_surfaces = {
    "weak_duality_direction": r"d^*\leq p^*",
    "sdp_sequence": r"X_\varepsilon=\begin{psmallmatrix}\varepsilon&1\\1&1/\varepsilon\end{psmallmatrix}",
    "penalty_coefficient": r"\frac{1}{2\lambda^*}\norm{x}_1",
    "moreau_identity": r"\prox_{\tau\norm{\emptyarg}_\infty}(y)",
    "positive_part_projection": r"\operatorname{sign}(y_i)\max\{|y_i|-\lambda,0\}",
    "qp_stationarity": r"Px^*+q+A^\top\nu^*=0",
    "qp_kkt_matrix": r"\begin{pmatrix}P&A^\top\\A&0\end{pmatrix}",
    "qp_uniqueness_scope": r"\ker(A)",
}
missing_target_surfaces = [
    name for name, fragment in required_target_surfaces.items() if fragment not in target_text
]
record(
    "live_target_mathematical_surfaces",
    not missing_target_surfaces,
    {
        "required_count": len(required_target_surfaces),
        "missing": missing_target_surfaces,
    },
)

required_wrapper_surfaces = {
    "source_commit": "98ed6930084c435ba0f675f7646ced1f2fd8729e",
    "source_license": "Lisensi MIT",
    "translation_license": "CC BY-SA 4.0",
    "source_credit": "Mitchell Krock",
}
missing_wrapper_surfaces = [
    name for name, fragment in required_wrapper_surfaces.items() if fragment not in wrapper_text
]
record(
    "live_wrapper_provenance_surfaces",
    not missing_wrapper_surfaces,
    {
        "required_count": len(required_wrapper_surfaces),
        "missing": missing_wrapper_surfaces,
    },
)

expected_ranges = [
    (1263, 1321, "caa06fcbf218428a7ae4d91be208607548273e913b55a441adf5b4538a91c677"),
    (1398, 1405, "f02825fce27c6d87f73b3f04c5918f21a30d9b44bf34ff3015d94692a8fb7331"),
    (1414, 1499, "aa8fc084cbb6dca65ddb526d3d69ec0e06432e408ac2383e07ca26986abc5452"),
    (1652, 1726, "88d7f14452d407c186a99c58dc14d281c916ec8f73b4e29ce7dc42a8fb489ba4"),
    (1731, 1743, "4626495d63c61fefcbf1295b2a0ed6854350e59ac0d6cfbcc73e93815df7afa6"),
]
observed_ranges = [
    (item["first_line"], item["last_line"], item["sha256"])
    for item in boundary.get("selected_ranges", [])
]
boundary_ok = (
    boundary.get("schema") == "o015-becker-01-source-boundary-v1"
    and boundary.get("result") == "pass"
    and boundary.get("upstream_contact") is False
    and boundary.get("authority", {}).get("commit")
    == "98ed6930084c435ba0f675f7646ced1f2fd8729e"
    and boundary.get("authority", {}).get("source_sha256")
    == "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8"
    and boundary.get("combined_witness", {}).get("sha256")
    == "20335c054393ea43d8912046b6dbfa07f6018f9e16b889e4cd0f66abc064d565"
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
        "upstream_contact": boundary.get("upstream_contact"),
    },
)


# 1. The concrete 2-by-2 semidefinite example in the reader.
c_sdp = np.array([[1.0, 0.0], [0.0, 0.0]])
a_sdp = np.array([[0.0, 1.0], [1.0, 0.0]])
epsilons = np.array([2.0 ** (-power) for power in range(13)], dtype=float)
sdp_records: list[dict[str, Any]] = []
max_constraint_residual = 0.0
max_objective_residual = 0.0
minimum_eigenvalue = float("inf")
objectives: list[float] = []
for epsilon in epsilons:
    x_sdp = np.array([[epsilon, 1.0], [1.0, 1.0 / epsilon]])
    constraint = float(np.sum(a_sdp * x_sdp))
    objective = float(np.sum(c_sdp * x_sdp))
    eigenvalues = np.linalg.eigvalsh(x_sdp)
    max_constraint_residual = max(max_constraint_residual, abs(constraint - 2.0))
    max_objective_residual = max(max_objective_residual, abs(objective - epsilon))
    minimum_eigenvalue = min(minimum_eigenvalue, float(eigenvalues[0]))
    objectives.append(objective)
    sdp_records.append(
        {
            "epsilon": float(epsilon),
            "objective": objective,
            "constraint_inner_product": constraint,
            "eigenvalues": [float(value) for value in eigenvalues],
        }
    )

sequence_ok = (
    max_constraint_residual <= TOLERANCES["algebra_abs"]
    and max_objective_residual <= TOLERANCES["algebra_abs"]
    and minimum_eigenvalue >= -TOLERANCES["eigenvalue_abs"]
    and all(objectives[index + 1] < objectives[index] for index in range(len(objectives) - 1))
    and max(
        abs(objectives[index + 1] / objectives[index] - 0.5)
        for index in range(len(objectives) - 1)
    )
    <= TOLERANCES["algebra_abs"]
    and objectives[-1] == 2.0 ** -12
)
record(
    "sdp_feasible_sequence_and_unattained_infimum",
    sequence_ok,
    {
        "C": c_sdp.tolist(),
        "A": a_sdp.tolist(),
        "constraint": "<A,X>=2",
        "sequence": sdp_records,
        "max_constraint_abs_residual": max_constraint_residual,
        "max_objective_abs_residual": max_objective_residual,
        "minimum_sequence_eigenvalue": minimum_eigenvalue,
        "objective_halving": True,
        "analytic_nonattainment": {
            "if_objective_a_is_zero_then_determinant": -1,
            "psd_requires_nonnegative_determinant": True,
            "conclusion": "objective 0 cannot be attained when X_12=1",
        },
    },
)

# With L(X,y)=<C,X>+y(2-<A,X>), the dual slack is C-yA and
# the dual objective is 2y.  det(C-yA)=-y^2, so PSD forces y=0.
dual_samples = np.array([-3.0, -1.0, -0.125, 0.0, 0.125, 1.0, 3.0])
dual_records: list[dict[str, Any]] = []
max_determinant_identity_residual = 0.0
for dual_y in dual_samples:
    slack = c_sdp - dual_y * a_sdp
    determinant = float(np.linalg.det(slack))
    eigenvalues = np.linalg.eigvalsh(slack)
    max_determinant_identity_residual = max(
        max_determinant_identity_residual, abs(determinant + dual_y**2)
    )
    dual_records.append(
        {
            "y": float(dual_y),
            "dual_objective_2y": float(2.0 * dual_y),
            "slack_determinant": determinant,
            "slack_eigenvalues": [float(value) for value in eigenvalues],
            "dual_feasible": bool(float(eigenvalues[0]) >= -TOLERANCES["eigenvalue_abs"]),
        }
    )
nonzero_samples_infeasible = all(
    not item["dual_feasible"] for item in dual_records if item["y"] != 0.0
)
zero_record = next(item for item in dual_records if item["y"] == 0.0)
dual_ok = (
    max_determinant_identity_residual <= TOLERANCES["algebra_abs"]
    and nonzero_samples_infeasible
    and zero_record["dual_feasible"]
    and zero_record["dual_objective_2y"] == 0.0
    and all(0.0 <= objective + TOLERANCES["algebra_abs"] for objective in objectives)
)
record(
    "sdp_dual_optimum_and_weak_duality",
    dual_ok,
    {
        "lagrangian_convention": "L(X,y)=<C,X>+y(2-<A,X>)",
        "dual": "maximize 2y subject to C-yA positive semidefinite",
        "analytic_slack_determinant": "-y^2; PSD therefore forces y=0",
        "sample_records": dual_records,
        "max_determinant_identity_abs_residual": max_determinant_identity_residual,
        "dual_optimum": 0.0,
        "smallest_checked_primal_objective": objectives[-1],
    },
)


# 2. Projection onto an l1 ball and the corrected Moreau identity.
y_l1 = np.array([3.0, -1.0, 0.5, -4.0, 2.0])
tau = 4.0
sorted_abs = np.sort(np.abs(y_l1))[::-1]
cumulative = np.cumsum(sorted_abs)
active = np.nonzero(
    sorted_abs - (cumulative - tau) / np.arange(1, y_l1.size + 1) > 0.0
)[0]
rho = int(active[-1] + 1)
lambda_star = float((cumulative[rho - 1] - tau) / rho)
projection = soft_threshold(y_l1, lambda_star)
expected_projection = np.array([4.0 / 3.0, 0.0, 0.0, -7.0 / 3.0, 1.0 / 3.0])
subgradient = (y_l1 - projection) / lambda_star
nonzero = np.abs(projection) > TOLERANCES["algebra_abs"]
subgradient_ok = (
    max_abs(subgradient[nonzero] - np.sign(projection[nonzero]))
    <= TOLERANCES["algebra_abs"]
    and max_abs(subgradient[~nonzero]) <= 1.0 + TOLERANCES["algebra_abs"]
)
projection_kkt_ok = (
    abs(lambda_star - 5.0 / 3.0) <= TOLERANCES["algebra_abs"]
    and max_abs(projection - expected_projection) <= TOLERANCES["algebra_abs"]
    and abs(float(np.abs(projection).sum()) - tau) <= TOLERANCES["algebra_abs"]
    and max_abs(projection - y_l1 + lambda_star * subgradient)
    <= TOLERANCES["algebra_abs"]
    and lambda_star >= 0.0
    and abs(lambda_star * (float(np.abs(projection).sum()) - tau))
    <= TOLERANCES["algebra_abs"]
    and subgradient_ok
)

n = y_l1.size
projection_matrix = np.zeros((2 * n + 1, 2 * n))
projection_lower = np.zeros(2 * n + 1)
projection_upper = np.full(2 * n + 1, np.inf)
for index in range(n):
    projection_matrix[index, index] = -1.0
    projection_matrix[index, n + index] = 1.0
    projection_matrix[n + index, index] = 1.0
    projection_matrix[n + index, n + index] = 1.0
projection_matrix[-1, n:] = 1.0
projection_lower[-1] = -np.inf
projection_upper[-1] = tau


def projection_objective(variable: np.ndarray) -> float:
    x_value = variable[:n]
    return 0.5 * float((x_value - y_l1) @ (x_value - y_l1))


def projection_gradient(variable: np.ndarray) -> np.ndarray:
    return np.concatenate((variable[:n] - y_l1, np.zeros(n)))


projection_solver = minimize(
    projection_objective,
    np.zeros(2 * n),
    jac=projection_gradient,
    method="SLSQP",
    bounds=Bounds(
        np.concatenate((np.full(n, -np.inf), np.zeros(n))),
        np.full(2 * n, np.inf),
    ),
    constraints=LinearConstraint(projection_matrix, projection_lower, projection_upper),
    options={"ftol": 1.0e-14, "maxiter": 1000, "disp": False},
)
projection_solver_x = projection_solver.x[:n]
projection_solver_error = max_abs(projection_solver_x - projection)
projection_solver_feasibility = max(
    0.0, float(np.abs(projection_solver_x).sum()) - tau
)
record(
    "l1_ball_projection_kkt_and_independent_solver",
    projection_kkt_ok
    and projection_solver.success
    and projection_solver_error <= TOLERANCES["solver_abs"]
    and projection_solver_feasibility <= TOLERANCES["solver_feasibility_abs"],
    {
        "y": y_l1.tolist(),
        "tau": tau,
        "active_coordinates": rho,
        "lambda": lambda_star,
        "projection": projection.tolist(),
        "projection_l1_norm": float(np.abs(projection).sum()),
        "subgradient": subgradient.tolist(),
        "stationarity_max_abs_residual": max_abs(
            projection - y_l1 + lambda_star * subgradient
        ),
        "complementarity_abs_residual": abs(
            lambda_star * (float(np.abs(projection).sum()) - tau)
        ),
        "scipy_slsqp": {
            "success": bool(projection_solver.success),
            "status": int(projection_solver.status),
            "iterations": int(projection_solver.nit),
            "solution": projection_solver_x.tolist(),
            "max_abs_solution_error": projection_solver_error,
            "feasibility_violation": projection_solver_feasibility,
        },
    },
)

# Independent epigraph solve of prox_{tau ||.||_infinity}(y).
prox_matrix = np.zeros((2 * n, n + 1))
for index in range(n):
    prox_matrix[index, index] = 1.0
    prox_matrix[index, -1] = -1.0
    prox_matrix[n + index, index] = -1.0
    prox_matrix[n + index, -1] = -1.0


def prox_inf_objective(variable: np.ndarray) -> float:
    z_value = variable[:n]
    return 0.5 * float((z_value - y_l1) @ (z_value - y_l1)) + tau * float(variable[-1])


def prox_inf_gradient(variable: np.ndarray) -> np.ndarray:
    return np.concatenate((variable[:n] - y_l1, np.array([tau])))


prox_initial = np.concatenate((np.zeros(n), np.array([float(np.max(np.abs(y_l1)))])))
prox_solver = minimize(
    prox_inf_objective,
    prox_initial,
    jac=prox_inf_gradient,
    method="SLSQP",
    bounds=Bounds(
        np.concatenate((np.full(n, -np.inf), np.array([0.0]))),
        np.full(n + 1, np.inf),
    ),
    constraints=LinearConstraint(
        prox_matrix, np.full(2 * n, -np.inf), np.zeros(2 * n)
    ),
    options={"ftol": 1.0e-14, "maxiter": 1000, "disp": False},
)
prox_inf = prox_solver.x[:n]
moreau_expected = y_l1 - projection
moreau_residual = max_abs(prox_inf - moreau_expected)
prox_epigraph_violation = max(
    0.0, float(np.max(np.abs(prox_inf))) - float(prox_solver.x[-1])
)
record(
    "corrected_moreau_identity",
    prox_solver.success
    and moreau_residual <= TOLERANCES["solver_abs"]
    and prox_epigraph_violation <= TOLERANCES["solver_feasibility_abs"],
    {
        "identity": "prox_{tau ||.||_infinity}(y) = y - projection_{B_1(tau)}(y)",
        "independent_prox_solution": prox_inf.tolist(),
        "y_minus_projection": moreau_expected.tolist(),
        "max_abs_identity_residual": moreau_residual,
        "epigraph_t": float(prox_solver.x[-1]),
        "epigraph_feasibility_violation": prox_epigraph_violation,
        "scipy_slsqp": {
            "success": bool(prox_solver.success),
            "status": int(prox_solver.status),
            "iterations": int(prox_solver.nit),
        },
    },
)


# 3. Equality-constrained convex QP: direct KKT solve and SciPy cross-check.
p_qp = np.diag([2.0, 3.0, 4.0])
a_qp = np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0]])
b_qp = np.array([1.0, 0.5])
expected_x = np.array([0.75, 0.25, 0.25])
expected_nu = np.array([-1.0, 0.5])
q_qp = -(p_qp @ expected_x + a_qp.T @ expected_nu)
r_qp = 1.25
kkt_matrix = np.block(
    [[p_qp, a_qp.T], [a_qp, np.zeros((a_qp.shape[0], a_qp.shape[0]))]]
)
kkt_rhs = np.concatenate((-q_qp, b_qp))
kkt_solution = np.linalg.solve(kkt_matrix, kkt_rhs)
x_qp = kkt_solution[: p_qp.shape[0]]
nu_qp = kkt_solution[p_qp.shape[0] :]
stationarity_residual = p_qp @ x_qp + q_qp + a_qp.T @ nu_qp
feasibility_residual = a_qp @ x_qp - b_qp


def qp_objective(x_value: np.ndarray) -> float:
    return 0.5 * float(x_value @ p_qp @ x_value) + float(q_qp @ x_value) + r_qp


def qp_gradient(x_value: np.ndarray) -> np.ndarray:
    return p_qp @ x_value + q_qp


qp_solver = minimize(
    qp_objective,
    np.zeros(3),
    jac=qp_gradient,
    method="SLSQP",
    constraints=LinearConstraint(a_qp, b_qp, b_qp),
    options={"ftol": 1.0e-14, "maxiter": 1000, "disp": False},
)
qp_solver_error = max_abs(qp_solver.x - x_qp)
qp_solver_feasibility = max_abs(a_qp @ qp_solver.x - b_qp)

# Evaluate the equality-dual function at nu*: x(nu)=-P^{-1}(q+A^T nu).
dual_minimizer = -np.linalg.solve(p_qp, q_qp + a_qp.T @ nu_qp)
primal_value = qp_objective(x_qp)
dual_value = qp_objective(dual_minimizer) + float(nu_qp @ (a_qp @ dual_minimizer - b_qp))
qp_ok = (
    max_abs(x_qp - expected_x) <= TOLERANCES["algebra_abs"]
    and max_abs(nu_qp - expected_nu) <= TOLERANCES["algebra_abs"]
    and max_abs(stationarity_residual) <= TOLERANCES["algebra_abs"]
    and max_abs(feasibility_residual) <= TOLERANCES["algebra_abs"]
    and abs(primal_value - dual_value) <= TOLERANCES["algebra_abs"]
    and np.linalg.matrix_rank(a_qp) == a_qp.shape[0]
    and float(np.min(np.linalg.eigvalsh(p_qp))) > 0.0
    and float(np.min(np.linalg.svd(kkt_matrix, compute_uv=False))) > 0.0
    and qp_solver.success
    and qp_solver_error <= TOLERANCES["solver_abs"]
    and qp_solver_feasibility <= TOLERANCES["solver_feasibility_abs"]
)
record(
    "equality_qp_kkt_solution_and_strong_duality",
    qp_ok,
    {
        "P": p_qp.tolist(),
        "q": q_qp.tolist(),
        "r": r_qp,
        "A": a_qp.tolist(),
        "b": b_qp.tolist(),
        "kkt_solution_x": x_qp.tolist(),
        "kkt_solution_nu": nu_qp.tolist(),
        "stationarity_max_abs_residual": max_abs(stationarity_residual),
        "feasibility_max_abs_residual": max_abs(feasibility_residual),
        "primal_value": primal_value,
        "dual_value": dual_value,
        "duality_gap_abs": abs(primal_value - dual_value),
        "P_min_eigenvalue": float(np.min(np.linalg.eigvalsh(p_qp))),
        "A_row_rank": int(np.linalg.matrix_rank(a_qp)),
        "KKT_min_singular_value": float(
            np.min(np.linalg.svd(kkt_matrix, compute_uv=False))
        ),
        "scipy_slsqp": {
            "success": bool(qp_solver.success),
            "status": int(qp_solver.status),
            "iterations": int(qp_solver.nit),
            "solution": qp_solver.x.tolist(),
            "max_abs_solution_error": qp_solver_error,
            "feasibility_max_abs_residual": qp_solver_feasibility,
        },
    },
)


# 4. The corrected penalty coefficient follows by exact positive scaling.
lambda_fraction = Fraction(7, 3)
l1_fraction = Fraction(11, 5)
residual_squared_fraction = Fraction(13, 4)
epsilon_squared_fraction = Fraction(2, 1)
lagrangian_value = l1_fraction + lambda_fraction * (
    residual_squared_fraction - epsilon_squared_fraction
)
scaled_lagrangian = lagrangian_value / (2 * lambda_fraction)
penalty_form = (
    Fraction(1, 2) * residual_squared_fraction
    + Fraction(1, 2) / lambda_fraction * l1_fraction
    - Fraction(1, 2) * epsilon_squared_fraction
)
record(
    "penalty_scaling_coefficient",
    scaled_lagrangian == penalty_form
    and Fraction(1, 2) / lambda_fraction == Fraction(3, 14),
    {
        "identity": "L/(2 lambda) = residual_squared/2 + l1/(2 lambda) - epsilon_squared/2",
        "lambda": str(lambda_fraction),
        "coefficient_1_over_2lambda": str(Fraction(1, 2) / lambda_fraction),
        "scaled_lagrangian_exact": str(scaled_lagrangian),
        "penalty_form_exact": str(penalty_form),
    },
)


failures = [item["gate"] for item in gates if not item["pass"]]
payload = {
    "schema": "o015-becker-01-open-math-validation-v1",
    "status": "PASS" if not failures else "FAIL",
    "failures": failures,
    "scope": {
        "unit": "Becker module 1: Lagrange duality, Slater, and KKT",
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
        "source_boundary": file_identity(BOUNDARY),
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
