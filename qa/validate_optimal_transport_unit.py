#!/usr/bin/env python3
"""Deterministic numerical validator for Habring Chapter 9 (id-ID).

This validator pins the exact authority and translated target, checks the
textual correction surfaces that the mathematics relies on, and exercises a
rectangular finite optimal-transport problem with SciPy/HiGHS.  It also checks
a Wasserstein special case and a positive entropic plan computed by Sinkhorn
scaling.  Deliberate negative controls expose the authority's scalar/simplex,
untyped-dimension, transpose, and entropy-domain defects.

The output contains no timestamps or environment-dependent paths, so two runs
in the same frozen environment must produce byte-identical JSON.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.optimize import linprog


QA_DIR = Path(__file__).resolve().parent
ROOT = QA_DIR.parent
AUTHORITY = ROOT / "authority" / "habring" / "source-v1" / "optimal_transport.tex"
TARGET = ROOT / "source" / "id-ID" / "habring-09-transportasi-optimal-id.tex"
OUTPUT = QA_DIR / "OPTIMAL_TRANSPORT_SOLVER_RESULTS.json"

EXPECTED_AUTHORITY_SHA256 = (
    "719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba"
)
EXPECTED_TARGET_SHA256 = (
    "45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd"
)

ABS_TOL = 1.0e-10
SINKHORN_TOL = 1.0e-14
SINKHORN_MAX_ITERATIONS = 5_000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_float(value: float, zero_tolerance: float = 1.0e-15) -> float:
    """Return a stable ordinary float, normalizing numerical signed zeros."""

    number = float(value)
    if abs(number) < zero_tolerance:
        return 0.0
    return number


def array_record(array: np.ndarray) -> list[Any]:
    values = np.asarray(array, dtype=float)
    if values.ndim == 1:
        return [clean_float(value) for value in values]
    return [array_record(row) for row in values]


def maximum_absolute(array: np.ndarray) -> float:
    values = np.asarray(array, dtype=float)
    if values.size == 0:
        return 0.0
    return clean_float(np.max(np.abs(values)))


def equality_matrix(n: int, m: int) -> np.ndarray:
    """Return all n row-sum and m column-sum constraints for vec(P)."""

    rows: list[np.ndarray] = []
    for i in range(n):
        constraint = np.zeros((n, m), dtype=float)
        constraint[i, :] = 1.0
        rows.append(constraint.reshape(-1))
    for j in range(m):
        constraint = np.zeros((n, m), dtype=float)
        constraint[:, j] = 1.0
        rows.append(constraint.reshape(-1))
    return np.asarray(rows, dtype=float)


def solve_finite_ot(
    a: np.ndarray,
    b: np.ndarray,
    cost: np.ndarray,
) -> dict[str, Any]:
    """Solve a finite Kantorovich problem and verify its primal/dual pair."""

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    cost = np.asarray(cost, dtype=float)
    n, m = cost.shape
    if a.shape != (n,) or b.shape != (m,):
        raise ValueError("Marginal dimensions do not match the cost matrix")

    a_eq = equality_matrix(n, m)
    b_eq = np.concatenate((a, b))
    result = linprog(
        cost.reshape(-1),
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=(0.0, None),
        method="highs",
        options={"presolve": True},
    )
    if not result.success:
        raise RuntimeError(f"HiGHS failed: status={result.status}: {result.message}")

    plan = np.asarray(result.x, dtype=float).reshape(n, m)
    dual_multipliers = np.asarray(result.eqlin.marginals, dtype=float)
    dual_slack = cost.reshape(-1) - a_eq.T @ dual_multipliers
    primal_objective = float(np.sum(cost * plan))
    dual_objective = float(b_eq @ dual_multipliers)
    equality_residual = a_eq @ plan.reshape(-1) - b_eq
    row_residual = plan.sum(axis=1) - a
    column_residual = plan.sum(axis=0) - b
    complementarity = plan.reshape(-1) * dual_slack

    checks = {
        "solver_success": bool(result.success and result.status == 0),
        "total_mass_equality": bool(abs(float(a.sum() - b.sum())) <= ABS_TOL),
        "equality_residual": bool(maximum_absolute(equality_residual) <= ABS_TOL),
        "row_marginal_residual": bool(maximum_absolute(row_residual) <= ABS_TOL),
        "column_marginal_residual": bool(maximum_absolute(column_residual) <= ABS_TOL),
        "nonnegativity": bool(float(plan.min()) >= -ABS_TOL),
        "dual_feasibility": bool(float(dual_slack.min()) >= -ABS_TOL),
        "strong_duality": bool(abs(primal_objective - dual_objective) <= ABS_TOL),
        "complementarity": bool(maximum_absolute(complementarity) <= ABS_TOL),
    }
    return {
        "shape": [n, m],
        "a": array_record(a),
        "b": array_record(b),
        "cost": array_record(cost),
        "plan": array_record(plan),
        "primal_objective": clean_float(primal_objective),
        "dual_objective": clean_float(dual_objective),
        "duality_gap_absolute": clean_float(abs(primal_objective - dual_objective)),
        "dual_row_potentials": array_record(dual_multipliers[:n]),
        "dual_column_potentials": array_record(dual_multipliers[n:]),
        "dual_slack_minimum": clean_float(dual_slack.min()),
        "maximum_equality_residual": maximum_absolute(equality_residual),
        "maximum_row_residual": maximum_absolute(row_residual),
        "maximum_column_residual": maximum_absolute(column_residual),
        "minimum_plan_entry": clean_float(plan.min()),
        "maximum_complementarity_residual": maximum_absolute(complementarity),
        "checks": checks,
        "passed": all(checks.values()),
    }


def entropic_objective(cost: np.ndarray, plan: np.ndarray, epsilon: float) -> float:
    """Evaluate <C,P> + epsilon*sum P(log(P)-1) for a positive plan."""

    if np.any(plan <= 0.0):
        raise ValueError("The numerical entropic objective expects a positive plan")
    return float(np.sum(cost * plan) + epsilon * np.sum(plan * (np.log(plan) - 1.0)))


def sinkhorn_plan(
    a: np.ndarray,
    b: np.ndarray,
    cost: np.ndarray,
    epsilon: float,
) -> dict[str, Any]:
    """Compute and validate the positive entropic OT solution."""

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    cost = np.asarray(cost, dtype=float)
    n, m = cost.shape
    kernel = np.exp(-cost / epsilon)
    v = np.ones(m, dtype=float)
    residual = math.inf
    iterations = 0

    for iteration in range(1, SINKHORN_MAX_ITERATIONS + 1):
        u = a / (kernel @ v)
        v = b / (kernel.T @ u)
        plan = (u[:, None] * kernel) * v[None, :]
        residual = max(
            maximum_absolute(plan.sum(axis=1) - a),
            maximum_absolute(plan.sum(axis=0) - b),
        )
        iterations = iteration
        if residual <= SINKHORN_TOL:
            break

    factorized = (u[:, None] * kernel) * v[None, :]
    row_residual = plan.sum(axis=1) - a
    column_residual = plan.sum(axis=0) - b
    factorization_residual = plan - factorized

    # The target's convention is
    # C_ij + epsilon log(P_ij) + lambda_i + mu_j = 0.
    lambda_multiplier = -epsilon * np.log(u)
    mu_multiplier = -epsilon * np.log(v)
    stationarity = (
        cost
        + epsilon * np.log(plan)
        + lambda_multiplier[:, None]
        + mu_multiplier[None, :]
    )

    # A nonzero feasible 2x2 cycle supplies a strict-convexity witness.
    direction = np.zeros((n, m), dtype=float)
    delta = 0.25 * min(plan[0, 0], plan[0, 1], plan[1, 0], plan[1, 1])
    direction[0, 0] = delta
    direction[0, 1] = -delta
    direction[1, 0] = -delta
    direction[1, 1] = delta
    plan_plus = plan + direction
    plan_minus = plan - direction
    objective = entropic_objective(cost, plan, epsilon)
    objective_plus = entropic_objective(cost, plan_plus, epsilon)
    objective_minus = entropic_objective(cost, plan_minus, epsilon)
    midpoint_gap = 0.5 * (objective_plus + objective_minus) - objective
    local_hessian_minimum = float(epsilon / np.max(plan))

    # Scaling vectors are nonunique even though their product plan is unique.
    scaling_factor = 3.7
    scaled_u = scaling_factor * u
    scaled_v = v / scaling_factor
    scaled_plan = (scaled_u[:, None] * kernel) * scaled_v[None, :]
    scaling_plan_residual = scaled_plan - plan

    checks = {
        "converged": bool(iterations < SINKHORN_MAX_ITERATIONS and residual <= SINKHORN_TOL),
        "positive_inputs": bool(np.all(a > 0.0) and np.all(b > 0.0)),
        "finite_cost": bool(np.all(np.isfinite(cost))),
        "positive_kernel": bool(np.all(kernel > 0.0)),
        "positive_scalings": bool(np.all(u > 0.0) and np.all(v > 0.0)),
        "positive_plan": bool(np.all(plan > 0.0)),
        "row_marginal_residual": bool(maximum_absolute(row_residual) <= ABS_TOL),
        "column_marginal_residual": bool(maximum_absolute(column_residual) <= ABS_TOL),
        "factorization": bool(maximum_absolute(factorization_residual) <= ABS_TOL),
        "kkt_stationarity": bool(maximum_absolute(stationarity) <= ABS_TOL),
        "feasible_cycle": bool(
            maximum_absolute(direction.sum(axis=1)) <= ABS_TOL
            and maximum_absolute(direction.sum(axis=0)) <= ABS_TOL
            and np.all(plan_plus > 0.0)
            and np.all(plan_minus > 0.0)
        ),
        "strict_convexity_midpoint": bool(midpoint_gap > 1.0e-12),
        "unique_minimizer_cycle_witness": bool(
            objective_plus > objective + 1.0e-12
            and objective_minus > objective + 1.0e-12
            and local_hessian_minimum > 0.0
        ),
        "scaling_ambiguity_same_plan": bool(
            maximum_absolute(scaling_plan_residual) <= ABS_TOL
            and maximum_absolute(scaled_u - u) > 1.0e-6
            and maximum_absolute(scaled_v - v) > 1.0e-6
        ),
    }
    return {
        "shape": [n, m],
        "epsilon": epsilon,
        "iterations": iterations,
        "stopping_tolerance": SINKHORN_TOL,
        "maximum_iterations": SINKHORN_MAX_ITERATIONS,
        "kernel": array_record(kernel),
        "u": array_record(u),
        "v": array_record(v),
        "plan": array_record(plan),
        "minimum_plan_entry": clean_float(plan.min()),
        "maximum_row_residual": maximum_absolute(row_residual),
        "maximum_column_residual": maximum_absolute(column_residual),
        "maximum_factorization_residual": maximum_absolute(factorization_residual),
        "maximum_kkt_stationarity_residual": maximum_absolute(stationarity),
        "entropic_objective": clean_float(objective),
        "strict_convexity_witness": {
            "cycle_delta": clean_float(delta),
            "maximum_cycle_row_sum": maximum_absolute(direction.sum(axis=1)),
            "maximum_cycle_column_sum": maximum_absolute(direction.sum(axis=0)),
            "objective_at_plan": clean_float(objective),
            "objective_at_plan_plus_cycle": clean_float(objective_plus),
            "objective_at_plan_minus_cycle": clean_float(objective_minus),
            "midpoint_strict_convexity_gap": clean_float(midpoint_gap),
            "minimum_local_entropy_hessian_diagonal": clean_float(local_hessian_minimum),
        },
        "scaling_ambiguity_witness": {
            "factor": scaling_factor,
            "maximum_plan_residual": maximum_absolute(scaling_plan_residual),
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    authority_bytes = AUTHORITY.read_bytes()
    target_bytes = TARGET.read_bytes()
    authority_text = authority_bytes.decode("utf-8")
    target_text = target_bytes.decode("utf-8")
    authority_sha = sha256(authority_bytes)
    target_sha = sha256(target_bytes)

    gates: list[dict[str, Any]] = []

    def gate(identifier: str, passed: bool, detail: str) -> None:
        gates.append({"id": identifier, "passed": bool(passed), "detail": detail})

    gate("surface.authority.sha256", authority_sha == EXPECTED_AUTHORITY_SHA256, authority_sha)
    gate("surface.target.sha256", target_sha == EXPECTED_TARGET_SHA256, target_sha)

    authority_defect_surfaces = {
        "scalar_claimed_in_simplex": r"for some $a_i\in \Delta_n$",
        "untyped_rectangular_marginals": r"$P\1=a$, $P^t\1 = b$",
        "missing_constraint_separator": r"P\1=a,\;P^t\1 = b\; P_{i,j}\geq 0",
        "wrong_measure_cone_argument": r"\Mc_+(\alpha,\beta)",
        "entropy_over_full_real_space": r"\min_{P\in \R^{n\times m}}\inner{C}{P} + \epsilon E(P)",
        "malformed_transposed_marginal": r"\diag(v)K^t u\1 = b",
        "unparenthesized_sinkhorn_division": r"v_{k+1} = b\oslash K^t u_{k+1}",
        "unfinished_wasserstein_sentence": r"finite $p$-th.",
    }
    for name, surface in authority_defect_surfaces.items():
        gate(
            f"surface.authority.defect.{name}",
            surface in authority_text,
            "required frozen authority defect witness present",
        )

    target_correction_surfaces = {
        "measurable_monge_map": r"T:X\rightarrow Y\ \mathrm{terukur}",
        "empty_monge_convention": r"\inf\emptyset\coloneqq+\infty",
        "polish_tightness": r"Karena $\alpha$ dan $\beta$ ketat pada ruang Polish",
        "wasserstein_moment_space": r"\Pc_p(X)\coloneqq\{\mu\in\Pc(X):\int d(x,x_0)^p\dd\mu(x)<\infty\}",
        "wasserstein_metric_cost": r"\int d(x,y)^p\dd\gamma(x,y)",
        "bounded_continuous_dual_class": r"\phi\in C_b(X),\ \psi\in C_b(Y)",
        "correct_measure_cone": r"\Mc_+(X\times Y)",
        "vector_simplex_a": r"a=(a_1,\dots,a_n)\in\Delta_n",
        "vector_simplex_b": r"b=(b_1,\dots,b_m)\in\Delta_m",
        "typed_row_marginal": r"P\1_m=a",
        "typed_column_marginal": r"P^\top\1_n=b",
        "finite_entropic_cost": r"andaikan $C\in\R^{n\times m}$",
        "nonnegative_entropy_domain": r"\min_{P\in\R_+^{n\times m}}",
        "zero_log_zero_convention": r"$0\log0=0$",
        "extended_entropy_negative_domain": r"tetapkan $E(P)=+\infty$",
        "strict_convexity_argument": r"bersifat konveks ketat pada",
        "positive_plan_argument": r"$P_{i,j}>0$ untuk semua $i,j$",
        "positive_simplex_assumptions": r"$a\in\Delta_n^\circ$, $b\in\Delta_m^\circ$",
        "scaling_ambiguity": r"$(u,v)\mapsto(tu,t^{-1}v)$",
        "correct_sinkhorn_transpose": r"v_{k+1}=b\oslash(K^\top u_{k+1})",
        "positive_sinkhorn_initialization": r"v_0\in\R_{++}^m",
    }
    for name, surface in target_correction_surfaces.items():
        gate(
            f"surface.target.correction.{name}",
            surface in target_text,
            "required corrected target surface present",
        )
    segment_count = target_text.count("% segment-id: d90.hab.v1.ch09.seg")
    gate("surface.target.segment_markers", segment_count == 9, f"count={segment_count}")
    gate(
        "surface.target.excludes_wrong_measure_cone",
        authority_defect_surfaces["wrong_measure_cone_argument"] not in target_text,
        "authority's malformed measure-cone argument absent",
    )
    gate(
        "surface.target.excludes_full_real_entropy_domain",
        authority_defect_surfaces["entropy_over_full_real_space"] not in target_text,
        "authority's undefined full-real entropy domain absent",
    )

    # Nontrivial 3x4 finite OT instance: rectangularity is essential to the
    # dimension negative controls below.
    a = np.asarray([0.20, 0.50, 0.30], dtype=float)
    b = np.asarray([0.10, 0.25, 0.35, 0.30], dtype=float)
    cost = np.asarray(
        [
            [0.2, 1.3, 2.1, 0.7],
            [1.1, 0.1, 0.8, 1.9],
            [1.7, 0.9, 0.3, 1.2],
        ],
        dtype=float,
    )
    finite_ot = solve_finite_ot(a, b, cost)
    gate(
        "math.rectangular_finite_ot_primal_dual",
        bool(finite_ot["passed"]),
        (
            f"shape={finite_ot['shape']}; objective={finite_ot['primal_objective']}; "
            f"duality_gap={finite_ot['duality_gap_absolute']}"
        ),
    )

    # Wasserstein-2 on two finite one-dimensional measures.  Monotone coupling
    # gives W_2^2=3, while symmetry and identity are checked with the same LP.
    alpha_points = np.asarray([0.0, 2.0])
    alpha_weights = np.asarray([0.50, 0.50])
    beta_points = np.asarray([1.0, 3.0])
    beta_weights = np.asarray([0.25, 0.75])
    squared_distance = (alpha_points[:, None] - beta_points[None, :]) ** 2
    wasserstein_forward = solve_finite_ot(alpha_weights, beta_weights, squared_distance)
    wasserstein_reverse = solve_finite_ot(beta_weights, alpha_weights, squared_distance.T)
    wasserstein_identity = solve_finite_ot(
        alpha_weights,
        alpha_weights,
        (alpha_points[:, None] - alpha_points[None, :]) ** 2,
    )
    wasserstein_squared = float(wasserstein_forward["primal_objective"])
    wasserstein_value = math.sqrt(max(wasserstein_squared, 0.0))
    wasserstein_checks = {
        "forward_lp": bool(wasserstein_forward["passed"]),
        "reverse_lp": bool(wasserstein_reverse["passed"]),
        "identity_lp": bool(wasserstein_identity["passed"]),
        "known_squared_value": bool(abs(wasserstein_squared - 3.0) <= ABS_TOL),
        "known_value": bool(abs(wasserstein_value - math.sqrt(3.0)) <= ABS_TOL),
        "symmetry": bool(
            abs(
                float(wasserstein_forward["primal_objective"])
                - float(wasserstein_reverse["primal_objective"])
            )
            <= ABS_TOL
        ),
        "identity": bool(abs(float(wasserstein_identity["primal_objective"])) <= ABS_TOL),
        "finite_second_moments": bool(
            np.sum(alpha_weights * alpha_points**2) < math.inf
            and np.sum(beta_weights * beta_points**2) < math.inf
        ),
    }
    wasserstein_passed = all(wasserstein_checks.values())
    gate(
        "math.wasserstein_two_special_case",
        wasserstein_passed,
        f"W2_squared={wasserstein_squared}; W2={wasserstein_value}",
    )

    entropic = sinkhorn_plan(a, b, cost, epsilon=0.6)
    gate(
        "math.entropic_sinkhorn_positive_plan",
        bool(entropic["passed"]),
        (
            f"iterations={entropic['iterations']}; row_residual="
            f"{entropic['maximum_row_residual']}; column_residual="
            f"{entropic['maximum_column_residual']}"
        ),
    )

    # Negative control 1: a_i is a scalar, whereas Delta_n contains vectors.
    scalar_weight = a[0]
    vector_simplex_valid = bool(
        a.shape == (3,) and np.all(a >= 0.0) and abs(float(a.sum()) - 1.0) <= ABS_TOL
    )
    scalar_is_not_simplex_vector = bool(np.ndim(scalar_weight) == 0 and a.shape != np.shape(scalar_weight))
    scalar_simplex_negative_control = vector_simplex_valid and scalar_is_not_simplex_vector
    gate(
        "negative_control.source_scalar_simplex_dimension",
        scalar_simplex_negative_control,
        f"shape(a)={a.shape}; shape(a_i)={np.shape(scalar_weight)}",
    )

    # Negative control 2: an untyped all-ones vector is ambiguous for 3x4 P.
    primal_plan = np.asarray(finite_ot["plan"], dtype=float)
    correct_row_marginal = primal_plan @ np.ones(4)
    correct_column_marginal = primal_plan.T @ np.ones(3)
    wrong_row_raised = False
    wrong_column_raised = False
    try:
        _ = primal_plan @ np.ones(3)
    except ValueError:
        wrong_row_raised = True
    try:
        _ = primal_plan.T @ np.ones(4)
    except ValueError:
        wrong_column_raised = True
    dimension_negative_control = bool(
        np.allclose(correct_row_marginal, a, atol=ABS_TOL, rtol=0.0)
        and np.allclose(correct_column_marginal, b, atol=ABS_TOL, rtol=0.0)
        and wrong_row_raised
        and wrong_column_raised
    )
    gate(
        "negative_control.source_untyped_ones_rectangular",
        dimension_negative_control,
        "P is 3x4: row marginal needs 1_4 and column marginal needs 1_3",
    )

    # Negative control 3: appending an all-ones factor after K^T u collapses
    # the intended m-vector to a scalar instead of producing b in R^m.
    kernel = np.exp(-cost / 0.6)
    trial_u = np.asarray(entropic["u"], dtype=float)
    correct_transposed_vector = kernel.T @ trial_u
    malformed_expression = np.dot(correct_transposed_vector, np.ones(4))
    transpose_negative_control = bool(
        correct_transposed_vector.shape == (4,)
        and np.ndim(malformed_expression) == 0
        and np.shape(malformed_expression) != b.shape
    )
    gate(
        "negative_control.source_transpose_expression_dimension_collapse",
        transpose_negative_control,
        (
            f"shape(K^T u)={correct_transposed_vector.shape}; "
            f"shape((K^T u)^T 1_4)={np.shape(malformed_expression)}; shape(b)={b.shape}"
        ),
    )

    # Negative control 4: the naive expression is undefined at zero and on
    # negative entries; the target's extended-value definition handles both.
    zero_plan = np.asarray([[0.0, 0.5], [0.5, 0.0]])
    negative_plan = np.asarray([[-0.1, 0.6], [0.5, 0.0]])
    with np.errstate(divide="ignore", invalid="ignore"):
        naive_zero_entropy = float(np.sum(zero_plan * (np.log(zero_plan) - 1.0)))
        naive_negative_entropy = float(
            np.sum(negative_plan * (np.log(negative_plan) - 1.0))
        )
    positive_zero_entries = zero_plan[zero_plan > 0.0]
    extended_zero_entropy = float(
        np.sum(positive_zero_entries * (np.log(positive_zero_entries) - 1.0))
    )
    extended_negative_entropy = math.inf if np.any(negative_plan < 0.0) else 0.0
    entropy_domain_negative_control = bool(
        math.isnan(naive_zero_entropy)
        and math.isnan(naive_negative_entropy)
        and math.isfinite(extended_zero_entropy)
        and math.isinf(extended_negative_entropy)
    )
    gate(
        "negative_control.source_entropy_domain",
        entropy_domain_negative_control,
        "naive formula is NaN at zero/negative entries; target extension is finite/+infinity",
    )

    passed = all(item["passed"] for item in gates)
    result = {
        "schema": "d90.optimal-transport-validator.v1",
        "status": "PASS" if passed else "FAIL",
        "deterministic": True,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "linear_program_solver": "scipy.optimize.linprog(method='highs')",
        },
        "inputs": {
            "authority": {
                "path": AUTHORITY.relative_to(ROOT).as_posix(),
                "bytes": len(authority_bytes),
                "lines": len(authority_text.splitlines()),
                "sha256": authority_sha,
            },
            "target": {
                "path": TARGET.relative_to(ROOT).as_posix(),
                "bytes": len(target_bytes),
                "lines": len(target_text.splitlines()),
                "sha256": target_sha,
            },
        },
        "summary": {
            "gate_count": len(gates),
            "passed_gate_count": sum(1 for item in gates if item["passed"]),
            "failed_gate_count": sum(1 for item in gates if not item["passed"]),
            "finite_ot_shape": finite_ot["shape"],
            "sinkhorn_iterations": entropic["iterations"],
            "negative_control_count": 4,
        },
        "gates": gates,
        "rectangular_finite_ot": finite_ot,
        "wasserstein_two_special_case": {
            "p": 2,
            "alpha_points": array_record(alpha_points),
            "alpha_weights": array_record(alpha_weights),
            "beta_points": array_record(beta_points),
            "beta_weights": array_record(beta_weights),
            "squared_distance_cost": array_record(squared_distance),
            "forward": wasserstein_forward,
            "reverse": wasserstein_reverse,
            "identity": wasserstein_identity,
            "W2_squared": clean_float(wasserstein_squared),
            "W2": clean_float(wasserstein_value),
            "checks": wasserstein_checks,
            "passed": wasserstein_passed,
        },
        "entropic_sinkhorn": entropic,
        "negative_controls": {
            "scalar_simplex_dimension": {
                "vector_shape": list(a.shape),
                "scalar_shape": list(np.shape(scalar_weight)),
                "passed": scalar_simplex_negative_control,
            },
            "untyped_ones_rectangular": {
                "plan_shape": list(primal_plan.shape),
                "correct_row_ones_dimension": 4,
                "correct_column_ones_dimension": 3,
                "wrong_row_product_raised_value_error": wrong_row_raised,
                "wrong_column_product_raised_value_error": wrong_column_raised,
                "passed": dimension_negative_control,
            },
            "transpose_expression_dimension_collapse": {
                "correct_K_transpose_u_shape": list(correct_transposed_vector.shape),
                "malformed_postmultiplication_shape": list(np.shape(malformed_expression)),
                "required_b_shape": list(b.shape),
                "passed": transpose_negative_control,
            },
            "entropy_domain": {
                "naive_zero_entropy": "NaN" if math.isnan(naive_zero_entropy) else naive_zero_entropy,
                "naive_negative_entropy": (
                    "NaN" if math.isnan(naive_negative_entropy) else naive_negative_entropy
                ),
                "extended_zero_entropy": clean_float(extended_zero_entropy),
                "extended_negative_entropy": "Infinity",
                "passed": entropy_domain_negative_control,
            },
        },
    }

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{result['status']} gates={result['summary']['passed_gate_count']}/"
        f"{result['summary']['gate_count']} output={OUTPUT}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
