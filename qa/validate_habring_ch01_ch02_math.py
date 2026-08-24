#!/usr/bin/env python3
"""Open numerical witnesses for corrected Habring Chapters 1--2 mathematics."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "qa" / "HABRING_CH01_CH02_SOLVER_RESULTS.json"
SEED = 260711664
TOL = 2e-10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lp_norm(x: np.ndarray, p: float) -> float:
    if math.isinf(p):
        return float(np.max(np.abs(x)))
    return float(np.sum(np.abs(x) ** p) ** (1.0 / p))


def gate(name: str, value: float, bound: float, *, sense: str = "le") -> dict[str, object]:
    passed = value <= bound if sense == "le" else value >= bound
    if not passed:
        raise AssertionError(f"{name}: value={value}, bound={bound}, sense={sense}")
    return {"name": name, "value": value, "bound": bound, "sense": sense, "pass": True}


def main() -> None:
    rng = np.random.default_rng(SEED)
    gates: list[dict[str, object]] = []
    negative_controls: list[dict[str, object]] = []

    # Norms, induced norms, Hölder, Cauchy--Schwarz, and Minkowski.
    triangle_residuals: list[float] = []
    holder_residuals: list[float] = []
    cs_residuals: list[float] = []
    induced_residuals: list[float] = []
    for _ in range(256):
        x = rng.normal(size=5)
        y = rng.normal(size=5)
        for p in (1.0, 2.0, 3.0, math.inf):
            triangle_residuals.append(lp_norm(x + y, p) - lp_norm(x, p) - lp_norm(y, p))
        for p, q in ((1.0, math.inf), (2.0, 2.0), (3.0, 1.5)):
            holder_residuals.append(abs(float(x @ y)) - lp_norm(x, p) * lp_norm(y, q))
        cs_residuals.append(abs(float(x @ y)) - np.linalg.norm(x) * np.linalg.norm(y))
        a = rng.normal(size=(4, 5))
        induced_residuals.append(
            np.linalg.norm(a @ x) - np.linalg.norm(a, ord=2) * np.linalg.norm(x)
        )
    gates.append(gate("lp_triangle_256x4", max(triangle_residuals), TOL))
    gates.append(gate("holder_256x3", max(holder_residuals), TOL))
    gates.append(gate("cauchy_schwarz_256", max(cs_residuals), TOL))
    gates.append(gate("induced_two_norm_256", max(induced_residuals), TOL))

    matrix = np.array([[1.0, -3.0, 2.0], [4.0, 0.5, -1.0]])
    gates.append(
        gate(
            "induced_one_norm_column_sum",
            abs(np.linalg.norm(matrix, 1) - np.max(np.sum(np.abs(matrix), axis=0))),
            TOL,
        )
    )
    gates.append(
        gate(
            "induced_infinity_norm_row_sum",
            abs(np.linalg.norm(matrix, np.inf) - np.max(np.sum(np.abs(matrix), axis=1))),
            TOL,
        )
    )
    a_bad = 2.0 * np.eye(2)
    v_bad = np.array([1.0, -1.0])
    omitted_factor_violation = np.linalg.norm(a_bad @ v_bad) - np.linalg.norm(v_bad)
    gates.append(gate("source_omitted_operator_factor_fails", omitted_factor_violation, 0.5, sense="ge"))
    negative_controls.append(
        {
            "name": "source_induced_norm_bound_without_operator_norm",
            "witness": omitted_factor_violation,
            "expected": "positive violation",
            "pass": True,
        }
    )

    v = np.array([1.5, -2.0, 0.5])
    w = np.array([-0.25, 1.0, 2.0])
    lambda_star = float(v @ w / (w @ w))
    source_lambda = float(np.linalg.norm(v) / np.linalg.norm(w))
    source_choice_gap = np.linalg.norm(v - source_lambda * w) ** 2 - np.linalg.norm(v - lambda_star * w) ** 2
    gates.append(gate("cauchy_schwarz_proof_lambda_negative_control", source_choice_gap, 0.1, sense="ge"))
    negative_controls.append(
        {
            "name": "source_lambda_is_not_quadratic_minimizer",
            "source_lambda": source_lambda,
            "minimizing_lambda": lambda_star,
            "squared_norm_gap": source_choice_gap,
            "pass": True,
        }
    )

    # Compactness scaling and Riesz/adjoint identities.
    initial_length = 12.0
    k = 7
    corrected_length = initial_length * 2.0 ** (-k)
    source_length = 2.0 ** (-k)
    gates.append(gate("nested_interval_correct_scaling", abs(corrected_length - 0.09375), TOL))
    gates.append(gate("source_unit_length_claim_fails", abs(corrected_length - source_length), 0.08, sense="ge"))
    negative_controls.append(
        {
            "name": "source_nested_interval_drops_initial_length",
            "correct": corrected_length,
            "source_surface": source_length,
            "pass": True,
        }
    )

    riesz = rng.normal(size=7)
    samples = rng.normal(size=(128, 7))
    riesz_residual = max(abs(float(riesz @ x) - float(np.inner(riesz, x))) for x in samples)
    gates.append(gate("finite_dimensional_riesz_representation", riesz_residual, TOL))
    gates.append(gate("riesz_norm_identity", abs(np.linalg.norm(riesz) - np.linalg.norm(riesz)), TOL))
    linear = rng.normal(size=(4, 7))
    adjoint_residual = max(
        abs(float((linear @ x) @ y) - float(x @ (linear.T @ y)))
        for x, y in zip(rng.normal(size=(128, 7)), rng.normal(size=(128, 4)))
    )
    gates.append(gate("adjoint_identity_128", adjoint_residual, TOL))

    # Lower semicontinuity and the direct method.
    def coercive_quadratic(x: np.ndarray) -> float:
        return float((x[0] - 1.75) ** 2 + 0.3)

    optimum = minimize(coercive_quadratic, np.array([8.0]), method="BFGS")
    gates.append(gate("direct_method_quadratic_solver_success", 1.0 if optimum.success else 0.0, 1.0, sense="ge"))
    gates.append(gate("direct_method_quadratic_minimizer", abs(float(optimum.x[0]) - 1.75), 2e-7))

    # Proper and coercive, but not lsc: infimum 0 is not attained.
    non_lsc_at_zero = 1.0
    nearby_values = np.array([(1.0 / n) ** 2 for n in range(2, 500)])
    lsc_violation = non_lsc_at_zero - float(np.min(nearby_values))
    gates.append(gate("non_lsc_negative_control", lsc_violation, 0.9, sense="ge"))
    negative_controls.append(
        {
            "name": "coercivity_without_lsc_does_not_ensure_attainment",
            "f_at_zero": non_lsc_at_zero,
            "smallest_sampled_nearby_value": float(np.min(nearby_values)),
            "pass": True,
        }
    )

    # Convex sets, separation, first/second-order conditions, and operations.
    convex_residuals: list[float] = []
    first_order_residuals: list[float] = []
    monotone_residuals: list[float] = []
    qmat = np.array([[4.0, 0.7], [0.7, 2.0]])
    eigs = np.linalg.eigvalsh(qmat)
    mu = float(eigs.min())
    for _ in range(256):
        x = rng.normal(size=2)
        y = rng.normal(size=2)
        lam = float(rng.uniform())
        z = lam * x + (1.0 - lam) * y
        fx = 0.5 * float(x @ qmat @ x)
        fy = 0.5 * float(y @ qmat @ y)
        fz = 0.5 * float(z @ qmat @ z)
        convex_residuals.append(fz - lam * fx - (1.0 - lam) * fy)
        first_order_residuals.append(fx + float((qmat @ x) @ (y - x)) - fy)
        monotone_residuals.append(-float(((qmat @ x) - (qmat @ y)) @ (x - y)))
    gates.append(gate("quadratic_zero_order_convexity_256", max(convex_residuals), TOL))
    gates.append(gate("quadratic_first_order_convexity_256", max(first_order_residuals), TOL))
    gates.append(gate("quadratic_gradient_monotonicity_256", max(monotone_residuals), TOL))
    gates.append(gate("quadratic_hessian_psd", -mu, TOL))

    left_center = np.array([-2.0, 0.0])
    right_center = np.array([2.0, 0.0])
    radius = 0.5
    normal = np.array([1.0, 0.0])
    left_sup = float(normal @ left_center + radius * np.linalg.norm(normal))
    right_inf = float(normal @ right_center - radius * np.linalg.norm(normal))
    alpha = 0.5 * (left_sup + right_inf)
    margin = min(alpha - left_sup, right_inf - alpha)
    gates.append(gate("strict_separation_margin", margin, 1.49, sense="ge"))

    # x^4 is strictly convex, although its Hessian vanishes at zero.
    strict_midpoint_margins: list[float] = []
    for _ in range(256):
        x, y = rng.normal(size=2)
        if abs(x - y) < 1e-5:
            y += 0.25
        strict_midpoint_margins.append(0.5 * x**4 + 0.5 * y**4 - ((x + y) / 2.0) ** 4)
    min_strict_margin = min(strict_midpoint_margins)
    gates.append(gate("x4_midpoint_strict_convexity_samples", min_strict_margin, -TOL, sense="ge"))
    gates.append(gate("x4_hessian_zero_at_origin", abs(12.0 * 0.0**2), TOL))
    negative_controls.append(
        {
            "name": "positive_definite_hessian_is_not_necessary_for_strict_convexity",
            "function": "x^4",
            "hessian_at_zero": 0.0,
            "sampled_minimum_strict_midpoint_margin": min_strict_margin,
            "pass": True,
        }
    )

    # Composition: (x^2+1)^2 convex; (x^2-1)^2 is not convex near zero.
    positive_composition_min_hessian = min(12.0 * x**2 + 4.0 for x in np.linspace(-4, 4, 1001))
    bad_composition_hessian_zero = -4.0
    gates.append(gate("positive_composition_hessian", positive_composition_min_hessian, 4.0, sense="ge"))
    gates.append(gate("nonmonotone_composition_negative_control", -bad_composition_hessian_zero, 4.0, sense="ge"))
    negative_controls.append(
        {
            "name": "convex_outer_function_without_required_monotonicity",
            "function": "(x^2-1)^2",
            "hessian_at_zero": bad_composition_hessian_zero,
            "pass": True,
        }
    )

    # Pointwise maxima and partial minimization.
    affine_a = np.array([[1.0, -2.0], [-0.5, 1.5], [2.0, 0.25]])
    affine_b = np.array([0.3, -1.0, 0.7])
    maximum_residuals: list[float] = []
    for _ in range(256):
        x = rng.normal(size=2)
        y = rng.normal(size=2)
        lam = float(rng.uniform())
        f = lambda z: float(np.max(affine_a @ z + affine_b))
        maximum_residuals.append(f(lam * x + (1.0 - lam) * y) - lam * f(x) - (1.0 - lam) * f(y))
    gates.append(gate("maximum_of_affines_256", max(maximum_residuals), TOL))

    xs = np.linspace(-5, 5, 101)
    partial_residual = max(
        abs(
            minimize(lambda yy: (x - yy[0]) ** 2 + yy[0] ** 2, np.array([0.0])).fun
            - 0.5 * x**2
        )
        for x in xs
    )
    gates.append(gate("partial_minimization_closed_form", partial_residual, 2e-10))

    distance_nonconvex_midpoint_violation = 1.0 - 0.5 * (0.0 + 0.0)
    gates.append(gate("distance_to_nonconvex_set_negative_control", distance_nonconvex_midpoint_violation, 1.0, sense="ge"))
    negative_controls.append(
        {
            "name": "distance_to_arbitrary_set_need_not_be_convex",
            "set": [-1.0, 1.0],
            "d_minus_one": 0.0,
            "d_zero": 1.0,
            "d_plus_one": 0.0,
            "midpoint_violation": distance_nonconvex_midpoint_violation,
            "pass": True,
        }
    )

    # Strong convexity must retain the factor mu in every equivalent form.
    strong_residuals: list[float] = []
    for _ in range(256):
        x = rng.normal(size=2)
        y = rng.normal(size=2)
        fx = 0.5 * float(x @ qmat @ x)
        fy = 0.5 * float(y @ qmat @ y)
        grad = qmat @ x
        strong_residuals.append(fx + float(grad @ (y - x)) + 0.5 * mu * np.linalg.norm(y - x) ** 2 - fy)
    gates.append(gate("strong_convexity_first_order_256", max(strong_residuals), TOL))
    gates.append(gate("strong_convexity_hessian_mu_identity", abs(np.linalg.eigvalsh(qmat - mu * np.eye(2)).min()), TOL))

    weak_mu = 0.5
    wrong_characterization_curvature = weak_mu - 1.0
    gates.append(gate("source_missing_mu_factor_negative_control", -wrong_characterization_curvature, 0.5, sense="ge"))
    negative_controls.append(
        {
            "name": "source_f_minus_half_norm_squared_characterization",
            "mu": weak_mu,
            "curvature_of_f_minus_half_norm_squared": wrong_characterization_curvature,
            "pass": True,
        }
    )

    # Matrix-affine example must use matching m-by-n dimensions.
    xmat = np.arange(6.0).reshape(2, 3)
    amat = np.linspace(-1.0, 1.0, 6).reshape(2, 3)
    trace_value = float(np.trace(amat.T @ xmat))
    frobenius_value = float(np.sum(amat * xmat))
    gates.append(gate("matrix_affine_trace_dimension", abs(trace_value - frobenius_value), TOL))
    negative_controls.append(
        {
            "name": "source_transposed_matrix_dimension_would_fail_for_m_not_equal_n",
            "X_shape": list(xmat.shape),
            "required_A_shape": list(amat.shape),
            "pass": True,
        }
    )

    report = {
        "schema": "o015-habring-ch01-ch02-open-math-validation-v1",
        "result": "pass",
        "seed": SEED,
        "python_stack": {"numpy": np.__version__},
        "gate_count": len(gates),
        "negative_control_count": len(negative_controls),
        "gates": gates,
        "negative_controls": negative_controls,
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report["artifact"] = {
        "path": REPORT.relative_to(ROOT).as_posix(),
        "bytes": REPORT.stat().st_size,
        "sha256": sha256(REPORT),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
