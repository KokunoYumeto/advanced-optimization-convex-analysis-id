#!/usr/bin/env python3
"""Deterministic open-solver checks for Habring Chapter 5 (id-ID).

The checks exercise the concrete proximal mappings and the corrected
forward-backward convergence statements used in the Indonesian reader.
No proprietary solver or network service is required.
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.optimize import LinearConstraint, minimize, minimize_scalar


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "qa" / "PROXIMAL_GRADIENT_SOLVER_RESULTS.json"
SEED = 20260821

ANALYTIC_TOL = 5.0e-9
SOLVER_TOL = 3.0e-6
FINITE_DIFFERENCE_TOL = 2.0e-6
ALGORITHM_TOL = 3.0e-7
GRADIENT_MAPPING_TOL = 3.0e-6


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def positive_part(value: float) -> float:
    return max(0.0, float(value))


def projection_prox_checks(rng: np.random.Generator) -> dict[str, Any]:
    """Check prox of a box indicator by VI tests and independent SLSQP solves."""

    lo = np.array([-1.0, -0.25, -2.0, 0.0])
    hi = np.array([0.5, 1.75, 0.8, 2.5])
    samples = [rng.normal(size=4) * 3.0 for _ in range(64)]
    samples.extend(
        [
            np.zeros(4),
            lo.copy(),
            hi.copy(),
            np.array([-4.0, 0.4, 2.0, -1.0]),
        ]
    )

    max_feasibility_violation = 0.0
    max_variational_inequality_residual = 0.0
    max_slsqp_inf_error = 0.0
    max_slsqp_objective_gap = 0.0
    solver_iterations = 0

    for sample_index, x in enumerate(samples):
        prox = np.clip(x, lo, hi)
        max_feasibility_violation = max(
            max_feasibility_violation,
            float(np.max(np.maximum(lo - prox, prox - hi))),
        )
        for _ in range(12):
            feasible_test_point = rng.uniform(lo, hi)
            # Projection characterization: <x-Px,z-Px> <= 0 for z in C.
            residual = float(np.dot(x - prox, feasible_test_point - prox))
            max_variational_inequality_residual = max(
                max_variational_inequality_residual,
                residual,
            )

        if sample_index < 20:
            result = minimize(
                lambda y: 0.5 * float(np.dot(y - x, y - x)),
                0.5 * (lo + hi),
                jac=lambda y: y - x,
                method="SLSQP",
                bounds=list(zip(lo, hi, strict=True)),
                options={"ftol": 1.0e-13, "maxiter": 1000},
            )
            require(result.success, f"projection SLSQP failed: {result.message}")
            solver_iterations += int(result.nit)
            max_slsqp_inf_error = max(
                max_slsqp_inf_error,
                float(np.linalg.norm(result.x - prox, ord=np.inf)),
            )
            analytic_value = 0.5 * float(np.dot(prox - x, prox - x))
            max_slsqp_objective_gap = max(
                max_slsqp_objective_gap,
                abs(float(result.fun) - analytic_value),
            )

    require(max_feasibility_violation <= ANALYTIC_TOL, "box prox is infeasible")
    require(
        max_variational_inequality_residual <= ANALYTIC_TOL,
        "box projection variational inequality failed",
    )
    require(max_slsqp_inf_error <= SOLVER_TOL, "box prox disagrees with SLSQP")

    return {
        "mapping": "prox of the indicator of [lo,hi], implemented by coordinate clipping",
        "lo": lo.tolist(),
        "hi": hi.tolist(),
        "samples": len(samples),
        "variational_test_points_per_sample": 12,
        "independent_slsqp_cases": 20,
        "independent_solver": "scipy.optimize.minimize(method='SLSQP')",
        "solver_iterations_total": solver_iterations,
        "max_feasibility_violation": max_feasibility_violation,
        "max_variational_inequality_residual": max_variational_inequality_residual,
        "max_slsqp_inf_error": max_slsqp_inf_error,
        "max_slsqp_objective_gap": max_slsqp_objective_gap,
        "result": "PASS",
    }


def prox_l1(x: np.ndarray, tau: float, lam: float) -> np.ndarray:
    threshold = tau * lam
    return np.sign(x) * np.maximum(np.abs(x) - threshold, 0.0)


def l1_soft_threshold_checks(rng: np.random.Generator) -> dict[str, Any]:
    tau = 0.4
    lam = 0.7
    threshold = tau * lam
    vectors = [rng.normal(size=5) * 1.7 for _ in range(48)]
    vectors.extend(
        [
            np.zeros(5),
            np.array([threshold, -threshold, 0.5 * threshold, -2.0 * threshold, 2.0]),
            np.array([4.0, -3.0, 0.1, -0.2, 0.0]),
        ]
    )

    max_optimality_residual = 0.0
    max_slsqp_inf_error = 0.0
    max_slsqp_objective_gap = 0.0
    solver_iterations = 0

    dimension = 5
    linear_matrix = np.zeros((2 * dimension, 2 * dimension))
    for i in range(dimension):
        linear_matrix[i, i] = -1.0
        linear_matrix[i, dimension + i] = 1.0
        linear_matrix[dimension + i, i] = 1.0
        linear_matrix[dimension + i, dimension + i] = 1.0
    epigraph_constraint = LinearConstraint(
        linear_matrix,
        np.zeros(2 * dimension),
        np.full(2 * dimension, np.inf),
    )

    for sample_index, x in enumerate(vectors):
        prox = prox_l1(x, tau, lam)
        nonzero = np.abs(prox) > 1.0e-14
        if np.any(nonzero):
            residual = np.max(
                np.abs((prox[nonzero] - x[nonzero]) + threshold * np.sign(prox[nonzero]))
            )
            max_optimality_residual = max(max_optimality_residual, float(residual))
        if np.any(~nonzero):
            zero_residual = np.max(np.maximum(np.abs(x[~nonzero]) - threshold, 0.0))
            max_optimality_residual = max(max_optimality_residual, float(zero_residual))

        if sample_index < 18:
            initial_y = 0.25 * x
            initial_u = np.abs(initial_y) + 0.25
            initial = np.concatenate([initial_y, initial_u])

            def objective(z: np.ndarray) -> float:
                delta = z[:dimension] - x
                return 0.5 * float(np.dot(delta, delta)) + threshold * float(
                    np.sum(z[dimension:])
                )

            def jacobian(z: np.ndarray) -> np.ndarray:
                return np.concatenate(
                    [z[:dimension] - x, np.full(dimension, threshold)]
                )

            result = minimize(
                objective,
                initial,
                jac=jacobian,
                method="SLSQP",
                bounds=[(None, None)] * dimension + [(0.0, None)] * dimension,
                constraints=[epigraph_constraint],
                options={"ftol": 1.0e-13, "maxiter": 2000},
            )
            require(result.success, f"l1 epigraph SLSQP failed: {result.message}")
            solver_iterations += int(result.nit)
            max_slsqp_inf_error = max(
                max_slsqp_inf_error,
                float(np.linalg.norm(result.x[:dimension] - prox, ord=np.inf)),
            )
            analytic_value = (
                0.5 * float(np.dot(prox - x, prox - x))
                + threshold * float(np.abs(prox).sum())
            )
            max_slsqp_objective_gap = max(
                max_slsqp_objective_gap,
                abs(float(result.fun) - analytic_value),
            )

    require(max_optimality_residual <= ANALYTIC_TOL, "soft threshold KKT check failed")
    require(max_slsqp_inf_error <= SOLVER_TOL, "soft threshold disagrees with SLSQP")

    return {
        "mapping": "prox_{tau*lambda*||.||_1}, coordinatewise soft thresholding",
        "tau": tau,
        "lambda": lam,
        "threshold": threshold,
        "samples": len(vectors),
        "independent_slsqp_cases": 18,
        "independent_solver": "SLSQP epigraph variables (y,u), u>=+/-y",
        "solver_iterations_total": solver_iterations,
        "max_kkt_residual": max_optimality_residual,
        "max_slsqp_inf_error": max_slsqp_inf_error,
        "max_slsqp_objective_gap": max_slsqp_objective_gap,
        "result": "PASS",
    }


def prox_l2(x: np.ndarray, tau: float, lam: float) -> np.ndarray:
    threshold = tau * lam
    norm = float(np.linalg.norm(x))
    if norm == 0.0 or norm <= threshold:
        return np.zeros_like(x)
    return (1.0 - threshold / norm) * x


def l2_vector_shrinkage_checks(rng: np.random.Generator) -> dict[str, Any]:
    tau = 0.35
    lam = 0.9
    threshold = tau * lam
    vectors = [rng.normal(size=6) * 1.5 for _ in range(48)]
    direction = np.array([1.0, -2.0, 0.5, 1.5, -0.25, 0.75])
    direction /= np.linalg.norm(direction)
    vectors.extend(
        [
            np.zeros(6),
            0.5 * threshold * direction,
            threshold * direction,
            2.0 * threshold * direction,
        ]
    )

    max_optimality_residual = 0.0
    max_scalar_solver_radius_error = 0.0
    max_scalar_solver_objective_gap = 0.0
    zero_convention_exact = bool(
        np.array_equal(prox_l2(np.zeros(6), tau, lam), np.zeros(6))
    )

    for x in vectors:
        prox = prox_l2(x, tau, lam)
        prox_norm = float(np.linalg.norm(prox))
        x_norm = float(np.linalg.norm(x))
        if prox_norm > 1.0e-14:
            residual = float(
                np.linalg.norm((prox - x) + threshold * prox / prox_norm)
            )
        else:
            residual = positive_part(x_norm - threshold)
        max_optimality_residual = max(max_optimality_residual, residual)

        upper = max(x_norm, threshold) + 2.0
        scalar_result = minimize_scalar(
            lambda radius: 0.5 * (radius - x_norm) ** 2 + threshold * radius,
            bounds=(0.0, upper),
            method="bounded",
            options={"xatol": 1.0e-14, "maxiter": 1000},
        )
        require(scalar_result.success, "l2 radial scalar minimization failed")
        max_scalar_solver_radius_error = max(
            max_scalar_solver_radius_error,
            abs(float(scalar_result.x) - prox_norm),
        )
        analytic_value = 0.5 * (prox_norm - x_norm) ** 2 + threshold * prox_norm
        max_scalar_solver_objective_gap = max(
            max_scalar_solver_objective_gap,
            abs(float(scalar_result.fun) - analytic_value),
        )

    require(zero_convention_exact, "l2 prox zero-vector convention failed")
    require(max_optimality_residual <= ANALYTIC_TOL, "l2 shrinkage KKT check failed")
    require(
        max_scalar_solver_radius_error <= SOLVER_TOL,
        "l2 shrinkage disagrees with independent radial solve",
    )

    return {
        "mapping": "prox_{tau*lambda*||.||_2}, vector shrinkage",
        "tau": tau,
        "lambda": lam,
        "threshold": threshold,
        "samples": len(vectors),
        "zero_input_returns_exact_zero": zero_convention_exact,
        "independent_solver": "scipy.optimize.minimize_scalar on the radial objective",
        "max_kkt_residual": max_optimality_residual,
        "max_scalar_solver_radius_error": max_scalar_solver_radius_error,
        "max_scalar_solver_objective_gap": max_scalar_solver_objective_gap,
        "result": "PASS",
    }


def moreau_envelope_gradient_checks(rng: np.random.Generator) -> dict[str, Any]:
    """Finite-difference the l1 Moreau envelope against (x-prox)/tau."""

    tau = 0.37
    lam = 0.8
    finite_difference_step = 2.0e-6
    points = [rng.normal(size=5) * 1.4 for _ in range(64)]
    points.extend(
        [
            np.zeros(5),
            np.array([0.1, -0.2, 0.7, -1.1, 2.0]),
            np.array([0.5 * tau * lam, -1.5 * tau * lam, 1.0, -2.0, 0.0]),
        ]
    )

    def envelope(x: np.ndarray) -> float:
        prox = prox_l1(x, tau, lam)
        return (
            0.5 / tau * float(np.dot(x - prox, x - prox))
            + lam * float(np.abs(prox).sum())
        )

    max_finite_difference_error = 0.0
    max_gradient_formula_residual = 0.0
    for x in points:
        prox = prox_l1(x, tau, lam)
        analytic_gradient = (x - prox) / tau
        finite_difference_gradient = np.zeros_like(x)
        for coordinate in range(x.size):
            offset = np.zeros_like(x)
            offset[coordinate] = finite_difference_step
            finite_difference_gradient[coordinate] = (
                envelope(x + offset) - envelope(x - offset)
            ) / (2.0 * finite_difference_step)
        max_finite_difference_error = max(
            max_finite_difference_error,
            float(
                np.linalg.norm(
                    finite_difference_gradient - analytic_gradient,
                    ord=np.inf,
                )
            ),
        )
        # For the soft-threshold prox, the formula also equals clipping to [-lambda,lambda].
        clipped_gradient = np.clip(x / tau, -lam, lam)
        max_gradient_formula_residual = max(
            max_gradient_formula_residual,
            float(np.linalg.norm(analytic_gradient - clipped_gradient, ord=np.inf)),
        )

    require(
        max_finite_difference_error <= FINITE_DIFFERENCE_TOL,
        "Moreau gradient finite-difference check failed",
    )
    require(
        max_gradient_formula_residual <= ANALYTIC_TOL,
        "Moreau gradient formula disagrees with the Huber derivative",
    )

    return {
        "function": "lambda*||.||_1",
        "tau": tau,
        "lambda": lam,
        "samples": len(points),
        "finite_difference_scheme": "centered coordinate differences",
        "finite_difference_step": finite_difference_step,
        "gradient_formula": "(x-prox_{tau*f}(x))/tau",
        "max_finite_difference_inf_error": max_finite_difference_error,
        "max_huber_gradient_formula_residual": max_gradient_formula_residual,
        "result": "PASS",
    }


def proximal_gradient_checks() -> dict[str, Any]:
    """Validate descent, telescoping, and O(1/n) on a quadratic+l1 problem."""

    matrix = np.array(
        [
            [1.2, -0.4, 0.3, 0.0],
            [0.5, 1.1, -0.2, 0.4],
            [-0.3, 0.2, 1.4, -0.5],
            [0.7, 0.0, 0.6, 1.0],
            [0.0, -0.8, 0.5, 1.3],
            [1.1, 0.3, -0.7, 0.2],
            [-0.6, 0.9, 0.0, 0.8],
        ],
        dtype=float,
    )
    data = np.array([1.0, -0.4, 0.7, 1.3, -0.8, 0.2, 0.5])
    lam = 0.18
    dimension = matrix.shape[1]

    hessian = matrix.T @ matrix
    eigenvalues = np.linalg.eigvalsh(hessian)
    lipschitz_constant = float(eigenvalues[-1])
    tau = 0.95 / lipschitz_constant
    require(tau <= 1.0 / lipschitz_constant, "chosen step exceeds 1/L")

    def smooth_value(x: np.ndarray) -> float:
        residual = matrix @ x - data
        return 0.5 * float(np.dot(residual, residual))

    def smooth_gradient(x: np.ndarray) -> np.ndarray:
        return matrix.T @ (matrix @ x - data)

    def objective(x: np.ndarray) -> float:
        return smooth_value(x) + lam * float(np.abs(x).sum())

    # Independent reference optimum: SLSQP epigraph variables z=(x,u),
    # with u_i >= x_i and u_i >= -x_i.
    constraint_matrix = np.zeros((2 * dimension, 2 * dimension))
    for i in range(dimension):
        constraint_matrix[i, i] = -1.0
        constraint_matrix[i, dimension + i] = 1.0
        constraint_matrix[dimension + i, i] = 1.0
        constraint_matrix[dimension + i, dimension + i] = 1.0
    epigraph_constraint = LinearConstraint(
        constraint_matrix,
        np.zeros(2 * dimension),
        np.full(2 * dimension, np.inf),
    )

    def epigraph_objective(z: np.ndarray) -> float:
        return smooth_value(z[:dimension]) + lam * float(np.sum(z[dimension:]))

    def epigraph_jacobian(z: np.ndarray) -> np.ndarray:
        return np.concatenate(
            [smooth_gradient(z[:dimension]), np.full(dimension, lam)]
        )

    reference = minimize(
        epigraph_objective,
        np.concatenate([np.zeros(dimension), np.ones(dimension) * 0.25]),
        jac=epigraph_jacobian,
        method="SLSQP",
        bounds=[(None, None)] * dimension + [(0.0, None)] * dimension,
        constraints=[epigraph_constraint],
        options={"ftol": 1.0e-14, "maxiter": 5000, "disp": False},
    )
    require(reference.success, f"reference SLSQP failed: {reference.message}")
    x_star = reference.x[:dimension]
    f_star = objective(x_star)
    epigraph_gap = abs(float(reference.fun) - f_star)

    def step(x: np.ndarray) -> np.ndarray:
        return prox_l1(x - tau * smooth_gradient(x), tau, lam)

    def gradient_mapping(x: np.ndarray) -> np.ndarray:
        return (x - step(x)) / tau

    reference_mapping_norm = float(np.linalg.norm(gradient_mapping(x_star)))
    require(
        reference_mapping_norm <= GRADIENT_MAPPING_TOL,
        "gradient mapping does not vanish at the SLSQP optimum",
    )

    x = np.array([2.2, -1.7, 0.9, 2.5])
    initial_x = x.copy()
    initial_distance_squared = float(np.dot(x - x_star, x - x_star))
    iterations = 512
    best_gap = float("inf")
    max_descent_signed_residual = -float("inf")
    max_telescoping_signed_residual = -float("inf")
    max_last_value_bound_signed_residual = -float("inf")
    max_best_value_bound_signed_residual = -float("inf")
    max_monotonicity_signed_residual = -float("inf")
    objective_values = [objective(x)]

    for iteration in range(1, iterations + 1):
        next_x = step(x)
        current_value = objective(x)
        next_value = objective(next_x)
        mapping = (x - next_x) / tau

        descent_residual = (
            next_value
            - current_value
            + 0.5 * tau * float(np.dot(mapping, mapping))
        )
        telescoping_residual = (
            next_value
            - f_star
            - (
                float(np.dot(x - x_star, x - x_star))
                - float(np.dot(next_x - x_star, next_x - x_star))
            )
            / (2.0 * tau)
        )
        gap = next_value - f_star
        best_gap = min(best_gap, gap)
        value_bound = initial_distance_squared / (2.0 * tau * iteration)

        max_descent_signed_residual = max(
            max_descent_signed_residual,
            descent_residual,
        )
        max_telescoping_signed_residual = max(
            max_telescoping_signed_residual,
            telescoping_residual,
        )
        max_last_value_bound_signed_residual = max(
            max_last_value_bound_signed_residual,
            gap - value_bound,
        )
        max_best_value_bound_signed_residual = max(
            max_best_value_bound_signed_residual,
            best_gap - value_bound,
        )
        max_monotonicity_signed_residual = max(
            max_monotonicity_signed_residual,
            next_value - current_value,
        )
        objective_values.append(next_value)
        x = next_x

    require(
        max_descent_signed_residual <= ALGORITHM_TOL,
        "per-step forward-backward descent inequality failed",
    )
    require(
        max_telescoping_signed_residual <= ALGORITHM_TOL,
        "per-step telescoping inequality failed",
    )
    require(
        max_last_value_bound_signed_residual <= ALGORITHM_TOL,
        "corrected O(1/n) last-value bound failed",
    )
    require(
        max_best_value_bound_signed_residual <= ALGORITHM_TOL,
        "corrected O(1/n) best-value bound failed",
    )
    require(
        max_monotonicity_signed_residual <= ALGORITHM_TOL,
        "proximal-gradient objective is not monotone",
    )

    final_mapping_norm = float(np.linalg.norm(gradient_mapping(x)))
    final_gap = objective(x) - f_star
    require(final_mapping_norm <= GRADIENT_MAPPING_TOL, "final gradient mapping is too large")

    return {
        "problem": "min_x 0.5*||A*x-b||_2^2 + lambda*||x||_1",
        "matrix_A": matrix.tolist(),
        "vector_b": data.tolist(),
        "lambda": lam,
        "hessian_eigenvalues_from_numpy_eigvalsh": eigenvalues.tolist(),
        "L_exact_for_this_quadratic": lipschitz_constant,
        "step_size_tau": tau,
        "tau_times_L": tau * lipschitz_constant,
        "step_condition": "tau <= 1/L",
        "reference_solver": "scipy.optimize.minimize(method='SLSQP') epigraph variables (x,u)",
        "reference_solver_status": str(reference.message),
        "reference_solver_iterations": int(reference.nit),
        "reference_x_star": x_star.tolist(),
        "reference_objective": f_star,
        "reference_epigraph_objective_gap": epigraph_gap,
        "reference_gradient_mapping_norm": reference_mapping_norm,
        "initial_x": initial_x.tolist(),
        "initial_objective": objective_values[0],
        "initial_distance_squared_to_reference": initial_distance_squared,
        "iterations": iterations,
        "final_x": x.tolist(),
        "final_objective": objective_values[-1],
        "final_objective_gap": final_gap,
        "final_gradient_mapping_norm": final_mapping_norm,
        "descent_inequality": "F(x_{k+1}) <= F(x_k) - (tau/2)||T_tau(x_k)||^2",
        "telescoping_inequality": (
            "F(x_{k+1})-F* <= "
            "(||x_k-x*||^2-||x_{k+1}-x*||^2)/(2*tau)"
        ),
        "value_bound": (
            "min_{1<=j<=n}(F(x_j)-F*) <= F(x_n)-F* <= "
            "||x_0-x*||^2/(2*tau*n)"
        ),
        "max_descent_signed_residual": max_descent_signed_residual,
        "max_descent_violation": positive_part(max_descent_signed_residual),
        "max_telescoping_signed_residual": max_telescoping_signed_residual,
        "max_telescoping_violation": positive_part(max_telescoping_signed_residual),
        "max_last_value_bound_signed_residual": max_last_value_bound_signed_residual,
        "max_last_value_bound_violation": positive_part(
            max_last_value_bound_signed_residual
        ),
        "max_best_value_bound_signed_residual": max_best_value_bound_signed_residual,
        "max_best_value_bound_violation": positive_part(
            max_best_value_bound_signed_residual
        ),
        "max_monotonicity_signed_residual": max_monotonicity_signed_residual,
        "max_monotonicity_violation": positive_part(max_monotonicity_signed_residual),
        "result": "PASS",
    }


def write_report(report: dict[str, Any]) -> None:
    RESULT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    report: dict[str, Any] = {
        "schema": "o015-proximal-gradient-solver-check-v1",
        "result": "FAIL",
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "reproducibility": {
            "numpy_rng": "numpy.random.Generator(PCG64)",
            "seed": SEED,
        },
        "tolerances": {
            "analytic": ANALYTIC_TOL,
            "independent_solver": SOLVER_TOL,
            "finite_difference": FINITE_DIFFERENCE_TOL,
            "algorithm_inequality": ALGORITHM_TOL,
            "gradient_mapping": GRADIENT_MAPPING_TOL,
        },
        "checks": {},
    }
    try:
        rng = np.random.default_rng(SEED)
        report["checks"]["projection_prox"] = projection_prox_checks(rng)
        report["checks"]["l1_soft_thresholding"] = l1_soft_threshold_checks(rng)
        report["checks"]["l2_vector_shrinkage"] = l2_vector_shrinkage_checks(rng)
        report["checks"]["moreau_envelope_gradient"] = moreau_envelope_gradient_checks(rng)
        report["checks"]["proximal_gradient"] = proximal_gradient_checks()
        report["result"] = "PASS"
    except Exception as error:
        report["failure"] = f"{type(error).__name__}: {error}"
        write_report(report)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    write_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
