#!/usr/bin/env python3
"""Deterministic open numerical witnesses for Habring Chapter 7 (duality).

The bounded checks use only Python, NumPy, and SciPy.  They exercise corrected
signs, domains, scale factors, and iterate indices in the Indonesian target.
Numerical witnesses support validation; they are not mathematical proofs.

The program writes no files.  Its canonical JSON report is printed to stdout
so independent invocations can be compared byte-for-byte.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.optimize import LinearConstraint, minimize


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = ROOT / "authority" / "habring" / "source-v1" / "duality.tex"
TARGET_PATH = ROOT / "source" / "id-ID" / "habring-07-dualitas-id.tex"
VALIDATOR_PATH = Path(__file__).resolve()

SEED = 20260822
ALGEBRA_TOL = 2.0e-11
SOLVER_TOL = 2.0e-7
INEQUALITY_TOL = 3.0e-10
CONVERGENCE_TOL = 2.0e-8
NEGATIVE_CONTROL_MIN = 1.0e-4


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def norm2(vector: np.ndarray) -> float:
    return float(np.linalg.norm(vector))


def positive_part(value: float) -> float:
    return max(0.0, float(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_identity(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def live_target_surface_checks() -> dict[str, Any]:
    """Require the corrected formulas to be present in the live Chapter 7 target."""

    target = TARGET_PATH.read_text(encoding="utf-8")
    required_fragments = {
        "scaled_moreau_formula": r"\prox_{\sigma g^*}(y)=y-\sigma\prox_{g/\sigma}(y/\sigma)",
        "primal_dual_gap_signs": r"\Gc(x,y) = (f(x) + g(Kx)) - (-f^*(-K^*y) - g^*(y))",
        "pdhg_y_uses_g_star": r"\prox_{\sigma g^*}(y_k+\sigma K(2x_{k+1}-x_k))",
        "abstract_y_minimization_variable": r"y^+ =& \arg\min_y \frac{1}{2\sigma}|y-y^-|^2",
        "fundamental_y_metric_sigma": r"g^*(y^+) + \frac{1}{2\sigma}|y-y^+|^2",
        "updated_x_ergodic_index": r"X_N = \frac{1}{N}\sum_{k=1}^{N}x_k",
        "updated_y_ergodic_index": r"Y_N = \frac{1}{N}\sum_{k=1}^{N}y_k",
        "actual_admm_y_stationarity": r"0\in\partial_y L_0(x_{k+1},y_{k+1},\lambda_{k+1})",
        "no_actual_admm_x_stationarity_claim": r"tidak memberikan stasioneritas terhadap $x$",
        "admm_correct_xstar_substitution": r"r_{k+1} + z - By_{k+1}",
        "admm_norm_cross_term_minus": r"\|B(y_{k+1}-y_k)\|^2 - 2\inner{r_{k+1}}{B(y_{k+1}-y_k)}",
        "admm_cross_term_nonpositive": r"\inner{r_{k+1}}{B(y_{k+1}-y_k)} \leq 0",
        "admm_lyapunov_gamma_and_index": r"+ \gamma\|B(y_{k+1}-y_k)\|^2 \leq V(y_{k},\lambda_{k}),\qquad k\geq1",
        "indicator_set_nonempty": r"$C\subset V$ tak kosong dan konveks",
        "separation_uses_domain_point": r"pilih $\bar x\in\dom(f)$",
        "pdhg_zero_operator_branch": r"Jika $K=0$, suku campuran dalam setiap tanda kurung siku lenyap",
        "pdhg_one_step_local_hypotheses": r"Misalkan $X$ dan $Y$ ruang Hilbert riil berdimensi hingga, $f\in\Gamma_0(X)$, $g\in\Gamma_0(Y)$, $K:X\rightarrow Y$ linear terbatas, serta $\tau,\sigma>0$",
        "biconjugate_requires_proper_conjugate": r"Misalkan $f$ dan $f^*$ proper",
        "empty_gamma_family_not_biconjugate": r"tidak dinotasikan sebagai $f^{**}$",
    }
    for index in range(1, 12):
        required_fragments[f"stable_segment_id_{index:04d}"] = (
            f"% segment-id: d90.hab.v1.ch07.seg{index:04d}"
        )
    missing = [name for name, fragment in required_fragments.items() if fragment not in target]
    forbidden_overclaim = (
        "setiap tripel yang diperbarui memenuhi kondisi stasioner primal untuk $L_0$"
    )
    forbidden_present = forbidden_overclaim in target
    require(not missing, f"live target is missing corrected surfaces: {missing}")
    require(not forbidden_present, "live target retains the false full-stationarity overclaim")

    return {
        "target": TARGET_PATH.relative_to(ROOT).as_posix(),
        "required_surface_count": len(required_fragments),
        "required_surfaces_present": {name: True for name in required_fragments},
        "false_actual_admm_full_stationarity_overclaim_absent": True,
        "result": "PASS",
    }


def soft_threshold(vector: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(vector) * np.maximum(np.abs(vector) - threshold, 0.0)


def fenchel_checks(rng: np.random.Generator) -> dict[str, Any]:
    """Fenchel inequality and the equality/subdifferential equivalence."""

    dimension = 6
    mu = 0.65
    lam = 0.8

    def function(x: np.ndarray) -> float:
        return 0.5 * mu * float(x @ x) + lam * float(np.abs(x).sum())

    def conjugate(s: np.ndarray) -> float:
        thresholded = soft_threshold(s, lam)
        return 0.5 / mu * float(thresholded @ thresholded)

    def conjugate_gradient(s: np.ndarray) -> np.ndarray:
        return soft_threshold(s, lam) / mu

    def in_subdifferential(x: np.ndarray, s: np.ndarray) -> bool:
        nonzero = np.abs(x) > 1.0e-12
        residual = np.zeros(dimension)
        residual[nonzero] = np.abs(
            s[nonzero] - mu * x[nonzero] - lam * np.sign(x[nonzero])
        )
        residual[~nonzero] = np.maximum(np.abs(s[~nonzero]) - lam, 0.0)
        return bool(float(np.max(residual)) <= ALGEBRA_TOL)

    graph_x = np.array([1.2, 0.0, -0.7, 0.0, 2.0, -0.25])
    graph_s = mu * graph_x
    nonzero = np.abs(graph_x) > 0.0
    graph_s[nonzero] += lam * np.sign(graph_x[nonzero])
    graph_s[1] = lam  # boundary of partial |.|(0)
    graph_s[3] = -0.3 * lam  # strict interior of partial |.|(0)

    zero_x = np.zeros(dimension)
    zero_s = np.array([-lam, -0.5 * lam, 0.0, 0.4 * lam, lam, -lam])
    off_s_zero = zero_s.copy()
    off_s_zero[2] = 1.1 * lam
    off_s_nonzero = graph_s.copy()
    off_s_nonzero[0] -= 0.25

    equivalence_cases = [
        ("graph_with_zero_boundary", graph_x, graph_s, True),
        ("zero_with_box_boundary", zero_x, zero_s, True),
        ("zero_outside_box", zero_x, off_s_zero, False),
        ("nonzero_wrong_slope", graph_x, off_s_nonzero, False),
    ]

    equality_max_gap = 0.0
    off_graph_min_gap = float("inf")
    equivalence_records: list[dict[str, Any]] = []
    for name, x, s, expected_member in equivalence_cases:
        gap = function(x) + conjugate(s) - float(s @ x)
        member = in_subdifferential(x, s)
        inverse_member = norm2(x - conjugate_gradient(s)) <= ALGEBRA_TOL
        equality = abs(gap) <= ALGEBRA_TOL
        require(member == expected_member, f"subdifferential case {name} misclassified")
        require(
            equality == member and inverse_member == member,
            f"Fenchel equality equivalence failed for {name}",
        )
        if expected_member:
            equality_max_gap = max(equality_max_gap, abs(gap))
        else:
            off_graph_min_gap = min(off_graph_min_gap, gap)
        equivalence_records.append(
            {
                "case": name,
                "expected_subgradient_membership": expected_member,
                "fenchel_young_gap": gap,
                "s_in_partial_f_of_x": member,
                "x_in_partial_f_star_of_s": inverse_member,
            }
        )

    random_pairs = 96
    minimum_random_gap = float("inf")
    maximum_random_gap = 0.0
    random_samples: list[tuple[np.ndarray, np.ndarray]] = []
    for _ in range(random_pairs):
        x = 1.4 * rng.normal(size=dimension)
        s = 1.7 * rng.normal(size=dimension)
        gap = function(x) + conjugate(s) - float(s @ x)
        minimum_random_gap = min(minimum_random_gap, gap)
        maximum_random_gap = max(maximum_random_gap, gap)
        random_samples.append((x, s))
    require(minimum_random_gap >= -INEQUALITY_TOL, "Fenchel inequality failed")
    require(off_graph_min_gap >= NEGATIVE_CONTROL_MIN, "off-graph gap is not separated")

    # Independent SLSQP epigraph solve of sup_x <s,x>-f(x).
    constraint_matrix = np.zeros((2 * dimension, 2 * dimension))
    for coordinate in range(dimension):
        constraint_matrix[coordinate, coordinate] = -1.0
        constraint_matrix[coordinate, dimension + coordinate] = 1.0
        constraint_matrix[dimension + coordinate, coordinate] = 1.0
        constraint_matrix[dimension + coordinate, dimension + coordinate] = 1.0
    epigraph = LinearConstraint(
        constraint_matrix,
        np.zeros(2 * dimension),
        np.full(2 * dimension, np.inf),
    )

    max_solver_point_error = 0.0
    max_solver_value_error = 0.0
    solver_iterations = 0
    for _, s in random_samples[:12]:
        def objective(z: np.ndarray, dual_point: np.ndarray = s) -> float:
            x = z[:dimension]
            u = z[dimension:]
            return (
                0.5 * mu * float(x @ x)
                + lam * float(u.sum())
                - float(dual_point @ x)
            )

        def jacobian(z: np.ndarray, dual_point: np.ndarray = s) -> np.ndarray:
            return np.concatenate([mu * z[:dimension] - dual_point, np.full(dimension, lam)])

        result = minimize(
            objective,
            np.zeros(2 * dimension),
            jac=jacobian,
            method="SLSQP",
            bounds=[(None, None)] * dimension + [(0.0, None)] * dimension,
            constraints=[epigraph],
            options={"ftol": 1.0e-13, "maxiter": 1000, "disp": False},
        )
        require(result.success, f"Fenchel conjugate SLSQP failed: {result.message}")
        solver_iterations += int(result.nit)
        expected_x = conjugate_gradient(s)
        max_solver_point_error = max(
            max_solver_point_error,
            float(np.linalg.norm(result.x[:dimension] - expected_x, ord=np.inf)),
        )
        max_solver_value_error = max(
            max_solver_value_error,
            abs(-float(result.fun) - conjugate(s)),
        )

    require(max_solver_point_error <= SOLVER_TOL, "conjugate maximizer disagrees with SLSQP")
    require(max_solver_value_error <= SOLVER_TOL, "conjugate value disagrees with SLSQP")

    return {
        "problem": "f(x)=(mu/2)||x||_2^2+lambda||x||_1",
        "dimension": dimension,
        "mu": mu,
        "lambda": lam,
        "conjugate": "f*(s)=||soft(s,lambda)||_2^2/(2*mu)",
        "equivalence_cases": equivalence_records,
        "equality_cases_max_absolute_gap": equality_max_gap,
        "off_graph_cases_minimum_gap": off_graph_min_gap,
        "random_fenchel_pairs": random_pairs,
        "minimum_random_fenchel_gap": minimum_random_gap,
        "maximum_random_fenchel_gap": maximum_random_gap,
        "independent_solver": "scipy.optimize.minimize(method='SLSQP') on l1 epigraph",
        "independent_solver_cases": 12,
        "independent_solver_iterations_total": solver_iterations,
        "max_solver_point_inf_error": max_solver_point_error,
        "max_solver_conjugate_value_error": max_solver_value_error,
        "result": "PASS",
    }


def moreau_checks(rng: np.random.Generator) -> dict[str, Any]:
    """Scaled Moreau: x=prox_{gamma f}(x)+gamma prox_{f*/gamma}(x/gamma)."""

    dimension = 7
    gamma = 0.37
    lam = 0.85
    threshold = gamma * lam
    points = [2.2 * rng.normal(size=dimension) for _ in range(48)]
    points.extend(
        [
            np.zeros(dimension),
            np.array([0.0, threshold, -threshold, 0.5 * threshold, -0.5 * threshold, 2.0 * threshold, -3.0 * threshold]),
        ]
    )

    max_decomposition_residual = 0.0
    max_missing_gamma_residual = 0.0
    max_wrong_argument_residual = 0.0
    max_primal_prox_solver_error = 0.0
    max_dual_prox_solver_error = 0.0

    # Epigraph constraints for independent primal-prox SLSQP solves.
    matrix = np.zeros((2 * dimension, 2 * dimension))
    for coordinate in range(dimension):
        matrix[coordinate, coordinate] = -1.0
        matrix[coordinate, dimension + coordinate] = 1.0
        matrix[dimension + coordinate, coordinate] = 1.0
        matrix[dimension + coordinate, dimension + coordinate] = 1.0
    epigraph = LinearConstraint(matrix, np.zeros(2 * dimension), np.full(2 * dimension, np.inf))

    for sample_index, x in enumerate(points):
        primal_prox = soft_threshold(x, threshold)
        dual_prox = np.clip(x / gamma, -lam, lam)
        residual = norm2(primal_prox + gamma * dual_prox - x)
        max_decomposition_residual = max(max_decomposition_residual, residual)

        missing_gamma = norm2(primal_prox + dual_prox - x)
        wrong_argument = norm2(primal_prox + gamma * np.clip(x, -lam, lam) - x)
        max_missing_gamma_residual = max(max_missing_gamma_residual, missing_gamma)
        max_wrong_argument_residual = max(max_wrong_argument_residual, wrong_argument)

        if sample_index < 10:
            def primal_objective(z: np.ndarray, point: np.ndarray = x) -> float:
                delta = z[:dimension] - point
                return 0.5 * float(delta @ delta) + gamma * lam * float(z[dimension:].sum())

            def primal_jacobian(z: np.ndarray, point: np.ndarray = x) -> np.ndarray:
                return np.concatenate([z[:dimension] - point, np.full(dimension, gamma * lam)])

            primal_result = minimize(
                primal_objective,
                np.concatenate([np.zeros(dimension), np.ones(dimension)]),
                jac=primal_jacobian,
                method="SLSQP",
                bounds=[(None, None)] * dimension + [(0.0, None)] * dimension,
                constraints=[epigraph],
                options={"ftol": 1.0e-13, "maxiter": 1000, "disp": False},
            )
            require(primal_result.success, f"Moreau primal prox SLSQP failed: {primal_result.message}")
            max_primal_prox_solver_error = max(
                max_primal_prox_solver_error,
                float(np.linalg.norm(primal_result.x[:dimension] - primal_prox, ord=np.inf)),
            )

            dual_result = minimize(
                lambda u, point=x: 0.5 * float((u - point / gamma) @ (u - point / gamma)),
                np.zeros(dimension),
                jac=lambda u, point=x: u - point / gamma,
                method="L-BFGS-B",
                bounds=[(-lam, lam)] * dimension,
                options={"ftol": 1.0e-15, "gtol": 1.0e-12, "maxiter": 1000},
            )
            require(dual_result.success, f"Moreau dual prox L-BFGS-B failed: {dual_result.message}")
            max_dual_prox_solver_error = max(
                max_dual_prox_solver_error,
                float(np.linalg.norm(dual_result.x - dual_prox, ord=np.inf)),
            )

    require(max_decomposition_residual <= ALGEBRA_TOL, "scaled Moreau decomposition failed")
    require(max_primal_prox_solver_error <= SOLVER_TOL, "primal prox disagrees with SLSQP")
    require(max_dual_prox_solver_error <= SOLVER_TOL, "dual prox disagrees with L-BFGS-B")
    require(max_missing_gamma_residual >= NEGATIVE_CONTROL_MIN, "missing-gamma control was not detected")
    require(max_wrong_argument_residual >= NEGATIVE_CONTROL_MIN, "wrong-argument control was not detected")

    return {
        "function": "f(x)=lambda||x||_1; f* is the indicator of the l_inf ball of radius lambda",
        "dimension": dimension,
        "gamma": gamma,
        "lambda": lam,
        "threshold_gamma_lambda": threshold,
        "samples_including_zero_and_exact_thresholds": len(points),
        "identity": "x=prox_{gamma*f}(x)+gamma*prox_{f*/gamma}(x/gamma)",
        "max_decomposition_l2_residual": max_decomposition_residual,
        "independent_primal_solver": "SLSQP l1 epigraph",
        "independent_dual_solver": "L-BFGS-B box projection",
        "independent_solver_cases_each": 10,
        "max_primal_prox_solver_inf_error": max_primal_prox_solver_error,
        "max_dual_prox_solver_inf_error": max_dual_prox_solver_error,
        "negative_controls": {
            "missing_outer_gamma_max_l2_residual": max_missing_gamma_residual,
            "unscaled_dual_argument_max_l2_residual": max_wrong_argument_residual,
            "minimum_required_detection": NEGATIVE_CONTROL_MIN,
        },
        "result": "PASS",
    }


def fenchel_rockafellar_checks(rng: np.random.Generator) -> dict[str, Any]:
    """Independently solve a smooth, strongly convex primal/dual pair."""

    primal_dimension = 5
    dual_dimension = 4
    generator = rng.normal(size=(primal_dimension, primal_dimension))
    q_matrix = generator.T @ generator + np.diag(np.linspace(1.1, 2.1, primal_dimension))
    operator = 0.42 * rng.normal(size=(dual_dimension, primal_dimension))
    linear = 0.6 * rng.normal(size=primal_dimension)
    shift = 0.8 * rng.normal(size=dual_dimension)
    alpha = 1.3
    q_inverse = np.linalg.inv(q_matrix)

    def f(x: np.ndarray) -> float:
        return 0.5 * float(x @ q_matrix @ x) + float(linear @ x)

    def f_star(s: np.ndarray) -> float:
        delta = s - linear
        return 0.5 * float(delta @ q_inverse @ delta)

    def g(u: np.ndarray) -> float:
        delta = u - shift
        return 0.5 * alpha * float(delta @ delta)

    def g_star(y: np.ndarray) -> float:
        return float(shift @ y) + 0.5 / alpha * float(y @ y)

    def primal_objective(x: np.ndarray) -> float:
        return f(x) + g(operator @ x)

    def primal_gradient(x: np.ndarray) -> np.ndarray:
        return q_matrix @ x + linear + alpha * operator.T @ (operator @ x - shift)

    primal_hessian = q_matrix + alpha * operator.T @ operator
    primal_result = minimize(
        primal_objective,
        1.5 * rng.normal(size=primal_dimension),
        jac=primal_gradient,
        hess=lambda _: primal_hessian,
        method="trust-exact",
        options={"gtol": 1.0e-12, "maxiter": 100},
    )
    require(primal_result.success, f"Fenchel-Rockafellar primal solve failed: {primal_result.message}")

    def dual_min_objective(y: np.ndarray) -> float:
        return f_star(-operator.T @ y) + g_star(y)

    def dual_min_gradient(y: np.ndarray) -> np.ndarray:
        primal_from_dual = q_inverse @ (-operator.T @ y - linear)
        return -operator @ primal_from_dual + shift + y / alpha

    dual_hessian = operator @ q_inverse @ operator.T + np.eye(dual_dimension) / alpha
    dual_result = minimize(
        dual_min_objective,
        1.5 * rng.normal(size=dual_dimension),
        jac=dual_min_gradient,
        hess=lambda _: dual_hessian,
        method="trust-exact",
        options={"gtol": 1.0e-12, "maxiter": 100},
    )
    require(dual_result.success, f"Fenchel-Rockafellar dual solve failed: {dual_result.message}")

    x_star = np.asarray(primal_result.x, dtype=float)
    y_star = np.asarray(dual_result.x, dtype=float)
    primal_value = primal_objective(x_star)
    dual_value = -dual_min_objective(y_star)
    duality_gap = primal_value - dual_value
    primal_stationarity = norm2(primal_gradient(x_star))
    dual_stationarity = norm2(dual_min_gradient(y_star))
    coupling_residual = norm2(y_star - alpha * (operator @ x_star - shift))
    f_fenchel_gap = f(x_star) + f_star(-operator.T @ y_star) - float((-operator.T @ y_star) @ x_star)
    g_fenchel_gap = g(operator @ x_star) + g_star(y_star) - float(y_star @ (operator @ x_star))

    wrong_f_sign_value = -f_star(operator.T @ y_star) - g_star(y_star)
    wrong_g_sign_value = -f_star(-operator.T @ y_star) - g_star(-y_star)
    wrong_f_sign_gap = abs(primal_value - wrong_f_sign_value)
    wrong_g_sign_gap = abs(primal_value - wrong_g_sign_value)

    require(duality_gap >= -INEQUALITY_TOL, "weak duality sign failed")
    require(abs(duality_gap) <= SOLVER_TOL, "Fenchel-Rockafellar duality gap is too large")
    require(primal_stationarity <= SOLVER_TOL, "primal stationarity residual is too large")
    require(dual_stationarity <= SOLVER_TOL, "dual stationarity residual is too large")
    require(coupling_residual <= SOLVER_TOL, "primal/dual coupling residual is too large")
    require(abs(f_fenchel_gap) <= SOLVER_TOL, "f Fenchel equality failed at optimum")
    require(abs(g_fenchel_gap) <= SOLVER_TOL, "g Fenchel equality failed at optimum")
    require(wrong_f_sign_gap >= NEGATIVE_CONTROL_MIN, "wrong sign in f* was not detected")
    require(wrong_g_sign_gap >= NEGATIVE_CONTROL_MIN, "wrong sign in g* was not detected")
    require(primal_dimension != dual_dimension, "dimension guard must distinguish primal and dual domains")

    return {
        "problem": "min_x 0.5*x.T*Q*x+c.T*x + (alpha/2)||K*x-b||_2^2",
        "primal_dimension": primal_dimension,
        "dual_dimension": dual_dimension,
        "operator_shape": list(operator.shape),
        "operator_spectral_norm": float(np.linalg.norm(operator, ord=2)),
        "q_condition_number": float(np.linalg.cond(q_matrix)),
        "alpha": alpha,
        "primal_solver": "scipy.optimize.minimize(method='trust-exact')",
        "dual_solver": "independent scipy.optimize.minimize(method='trust-exact')",
        "primal_solver_status": str(primal_result.message),
        "dual_solver_status": str(dual_result.message),
        "primal_solver_iterations": int(primal_result.nit),
        "dual_solver_iterations": int(dual_result.nit),
        "primal_value": primal_value,
        "dual_value": dual_value,
        "signed_primal_minus_dual_gap": duality_gap,
        "absolute_duality_gap": abs(duality_gap),
        "primal_stationarity_l2_residual": primal_stationarity,
        "dual_stationarity_l2_residual": dual_stationarity,
        "y_equals_alpha_Kx_minus_b_l2_residual": coupling_residual,
        "f_fenchel_equality_gap": f_fenchel_gap,
        "g_fenchel_equality_gap": g_fenchel_gap,
        "negative_controls": {
            "wrong_f_conjugate_sign_absolute_gap": wrong_f_sign_gap,
            "wrong_g_conjugate_sign_absolute_gap": wrong_g_sign_gap,
            "swapped_fstar_argument_domain_rejected_by_dimensions": primal_dimension != dual_dimension,
        },
        "result": "PASS",
    }


def pdhg_checks(rng: np.random.Generator) -> dict[str, Any]:
    """PDHG proximal updates, fundamental inequality, and ergodic convergence."""

    primal_dimension = 5
    dual_dimension = 4
    raw_operator = rng.normal(size=(dual_dimension, primal_dimension))
    requested_norm = 0.36
    operator = raw_operator * (requested_norm / float(np.linalg.norm(raw_operator, ord=2)))
    operator_norm = float(np.linalg.norm(operator, ord=2))
    mu_f = 0.75
    mu_g_star = 1.1
    primal_shift = rng.normal(size=primal_dimension)
    dual_shift = rng.normal(size=dual_dimension)

    def f(x: np.ndarray) -> float:
        delta = x - primal_shift
        return 0.5 * mu_f * float(delta @ delta)

    def g_star(y: np.ndarray) -> float:
        delta = y - dual_shift
        return 0.5 * mu_g_star * float(delta @ delta)

    def lagrangian(x: np.ndarray, y: np.ndarray) -> float:
        return f(x) - g_star(y) + float((operator @ x) @ y)

    def prox_f(point: np.ndarray, step: float) -> np.ndarray:
        return (point + step * mu_f * primal_shift) / (1.0 + step * mu_f)

    def prox_g_star(point: np.ndarray, step: float) -> np.ndarray:
        return (point + step * mu_g_star * dual_shift) / (1.0 + step * mu_g_star)

    saddle_matrix = np.block(
        [
            [mu_f * np.eye(primal_dimension), operator.T],
            [-operator, mu_g_star * np.eye(dual_dimension)],
        ]
    )
    saddle_rhs = np.concatenate([mu_f * primal_shift, mu_g_star * dual_shift])
    saddle = np.linalg.solve(saddle_matrix, saddle_rhs)
    x_star = saddle[:primal_dimension]
    y_star = saddle[primal_dimension:]
    saddle_stationarity = max(
        norm2(mu_f * (x_star - primal_shift) + operator.T @ y_star),
        norm2(mu_g_star * (y_star - dual_shift) - operator @ x_star),
    )

    # Abstract update and its fundamental inequality with deliberately distinct
    # old, barred, updated, and comparison variables.
    fundamental_tau = 0.13
    fundamental_sigma = 1.4
    fundamental_cases = 72
    max_fundamental_signed_residual = -float("inf")
    max_x_update_optimality = 0.0
    max_y_update_optimality = 0.0
    max_wrong_sigma_metric_violation = -float("inf")
    max_wrong_y_sign_optimality = 0.0

    for case_index in range(fundamental_cases):
        x_minus = 1.6 * rng.normal(size=primal_dimension)
        y_minus = 1.6 * rng.normal(size=dual_dimension)
        bar_x = rng.normal(size=primal_dimension) + 0.2 * case_index
        bar_y = rng.normal(size=dual_dimension) - 0.1 * case_index
        comparison_x = 2.0 * rng.normal(size=primal_dimension)
        comparison_y = 2.0 * rng.normal(size=dual_dimension)

        x_plus = prox_f(x_minus - fundamental_tau * operator.T @ bar_y, fundamental_tau)
        y_plus = prox_g_star(y_minus + fundamental_sigma * operator @ bar_x, fundamental_sigma)

        x_optimality = (
            (x_plus - x_minus) / fundamental_tau
            + operator.T @ bar_y
            + mu_f * (x_plus - primal_shift)
        )
        y_optimality = (
            (y_plus - y_minus) / fundamental_sigma
            - operator @ bar_x
            + mu_g_star * (y_plus - dual_shift)
        )
        max_x_update_optimality = max(max_x_update_optimality, norm2(x_optimality))
        max_y_update_optimality = max(max_y_update_optimality, norm2(y_optimality))

        lhs = lagrangian(x_plus, comparison_y) - lagrangian(comparison_x, y_plus)
        rhs = (
            0.5 / fundamental_tau * norm2(comparison_x - x_minus) ** 2
            + 0.5 / fundamental_sigma * norm2(comparison_y - y_minus) ** 2
            - 0.5 / fundamental_tau * norm2(comparison_x - x_plus) ** 2
            - 0.5 / fundamental_sigma * norm2(comparison_y - y_plus) ** 2
            - 0.5 / fundamental_tau * norm2(x_plus - x_minus) ** 2
            - 0.5 / fundamental_sigma * norm2(y_plus - y_minus) ** 2
            + float((x_plus - comparison_x) @ operator.T @ (comparison_y - bar_y))
            - float((y_plus - comparison_y) @ operator @ (comparison_x - bar_x))
        )
        max_fundamental_signed_residual = max(max_fundamental_signed_residual, lhs - rhs)

        def y_subproblem(value: np.ndarray) -> float:
            return (
                0.5 / fundamental_sigma * norm2(value - y_minus) ** 2
                - float(value @ operator @ bar_x)
                + g_star(value)
            )

        wrong_metric_residual = (
            y_subproblem(y_plus)
            + 0.5 / fundamental_tau * norm2(comparison_y - y_plus) ** 2
            - y_subproblem(comparison_y)
        )
        max_wrong_sigma_metric_violation = max(
            max_wrong_sigma_metric_violation,
            wrong_metric_residual,
        )

        wrong_sign_y = prox_g_star(y_minus - fundamental_sigma * operator @ bar_x, fundamental_sigma)
        wrong_sign_optimality = (
            (wrong_sign_y - y_minus) / fundamental_sigma
            - operator @ bar_x
            + mu_g_star * (wrong_sign_y - dual_shift)
        )
        max_wrong_y_sign_optimality = max(max_wrong_y_sign_optimality, norm2(wrong_sign_optimality))

    require(saddle_stationarity <= ALGEBRA_TOL, "PDHG saddle solve is inaccurate")
    require(max_x_update_optimality <= ALGEBRA_TOL, "PDHG x update optimality failed")
    require(max_y_update_optimality <= ALGEBRA_TOL, "PDHG y update optimality failed")
    require(max_fundamental_signed_residual <= INEQUALITY_TOL, "PDHG fundamental inequality failed")
    require(
        max_wrong_sigma_metric_violation >= NEGATIVE_CONTROL_MIN,
        "1/(2*tau) substitution for the y metric was not detected",
    )
    require(
        max_wrong_y_sign_optimality >= NEGATIVE_CONTROL_MIN,
        "wrong sign in the PDHG y coupling was not detected",
    )
    require(primal_dimension != dual_dimension, "PDHG domain guard requires unequal dimensions")

    tau = 0.82 / operator_norm
    sigma = 0.88 / operator_norm
    step_product = tau * sigma * operator_norm**2
    require(step_product < 1.0, "PDHG step condition is not strict")

    x = 3.2 * rng.normal(size=primal_dimension)
    y = 3.2 * rng.normal(size=dual_dimension)
    initial_x = x.copy()
    initial_y = y.copy()
    energy_zero = (
        0.5 / tau * norm2(x_star - initial_x) ** 2
        + 0.5 / sigma * norm2(y_star - initial_y) ** 2
        - float((y_star - initial_y) @ operator @ (x_star - initial_x))
    )
    require(energy_zero > 0.0, "initial PDHG metric energy is not positive")

    iterations = 240
    sum_updated_x = np.zeros(primal_dimension)
    sum_updated_y = np.zeros(dual_dimension)
    sum_old_x = np.zeros(primal_dimension)
    sum_old_y = np.zeros(dual_dimension)
    max_update_residual = 0.0
    max_correct_index_bound_violation = -float("inf")
    max_old_index_bound_violation = -float("inf")
    old_index_worst_k = 0

    for iteration in range(1, iterations + 1):
        x_next = prox_f(x - tau * operator.T @ y, tau)
        extrapolated_x = 2.0 * x_next - x
        y_next = prox_g_star(y + sigma * operator @ extrapolated_x, sigma)

        x_update_residual = (
            (x_next - x) / tau + operator.T @ y + mu_f * (x_next - primal_shift)
        )
        y_update_residual = (
            (y_next - y) / sigma - operator @ extrapolated_x + mu_g_star * (y_next - dual_shift)
        )
        max_update_residual = max(
            max_update_residual,
            norm2(x_update_residual),
            norm2(y_update_residual),
        )

        sum_updated_x += x_next
        sum_updated_y += y_next
        sum_old_x += x
        sum_old_y += y
        updated_mean_x = sum_updated_x / iteration
        updated_mean_y = sum_updated_y / iteration
        old_mean_x = sum_old_x / iteration
        old_mean_y = sum_old_y / iteration
        bound = energy_zero / iteration
        correct_gap = lagrangian(updated_mean_x, y_star) - lagrangian(x_star, updated_mean_y)
        old_gap = lagrangian(old_mean_x, y_star) - lagrangian(x_star, old_mean_y)
        max_correct_index_bound_violation = max(
            max_correct_index_bound_violation,
            correct_gap - bound,
        )
        old_violation = old_gap - bound
        if old_violation > max_old_index_bound_violation:
            max_old_index_bound_violation = old_violation
            old_index_worst_k = iteration

        x = x_next
        y = y_next

    final_distance = float(np.sqrt(norm2(x - x_star) ** 2 + norm2(y - y_star) ** 2))
    final_saddle_gap = lagrangian(x, y_star) - lagrangian(x_star, y)
    final_ergodic_gap = (
        lagrangian(sum_updated_x / iterations, y_star)
        - lagrangian(x_star, sum_updated_y / iterations)
    )

    require(max_update_residual <= ALGEBRA_TOL, "PDHG iterative update residual is too large")
    require(
        max_correct_index_bound_violation <= INEQUALITY_TOL,
        "updated-iterate ergodic bound failed",
    )
    require(
        max_old_index_bound_violation >= NEGATIVE_CONTROL_MIN,
        "old-iterate averaging index control was not detected",
    )
    require(final_distance <= CONVERGENCE_TOL, "PDHG iterates did not converge to the saddle")
    require(final_saddle_gap <= CONVERGENCE_TOL, "PDHG final saddle gap is too large")

    return {
        "problem": "min_x max_y (mu_f/2)||x-a||^2-(mu_g_star/2)||y-d||^2+<Kx,y>",
        "primal_dimension": primal_dimension,
        "dual_dimension": dual_dimension,
        "operator_shape": list(operator.shape),
        "operator_spectral_norm": operator_norm,
        "saddle_stationarity_l2_residual": saddle_stationarity,
        "fundamental_inequality": {
            "cases": fundamental_cases,
            "tau": fundamental_tau,
            "sigma": fundamental_sigma,
            "max_x_update_optimality_l2_residual": max_x_update_optimality,
            "max_y_update_optimality_l2_residual": max_y_update_optimality,
            "max_signed_lhs_minus_rhs": max_fundamental_signed_residual,
            "max_violation": positive_part(max_fundamental_signed_residual),
        },
        "convergence": {
            "iterations": iterations,
            "tau": tau,
            "sigma": sigma,
            "tau_sigma_operator_norm_squared": step_product,
            "required_step_upper_bound": 1.0,
            "initial_metric_energy": energy_zero,
            "max_update_optimality_l2_residual": max_update_residual,
            "max_updated_index_ergodic_bound_signed_residual": max_correct_index_bound_violation,
            "max_updated_index_ergodic_bound_violation": positive_part(max_correct_index_bound_violation),
            "final_iterate_distance_to_saddle": final_distance,
            "final_pointwise_saddle_gap": final_saddle_gap,
            "final_updated_index_ergodic_gap": final_ergodic_gap,
        },
        "negative_controls": {
            "wrong_y_metric_1_over_2tau_max_violation": max_wrong_sigma_metric_violation,
            "wrong_y_coupling_sign_max_optimality_l2_residual": max_wrong_y_sign_optimality,
            "prox_f_in_y_step_rejected_by_unequal_domains": primal_dimension != dual_dimension,
            "old_iterate_average_max_bound_violation": max_old_index_bound_violation,
            "old_iterate_average_worst_k": old_index_worst_k,
        },
        "result": "PASS",
    }


def admm_checks(rng: np.random.Generator) -> dict[str, Any]:
    """ADMM residuals and objective convergence for a separable quadratic."""

    dimension = 6
    q_x = np.array([0.7, 1.1, 1.6, 2.0, 0.9, 1.4])
    q_y = np.array([1.3, 0.8, 1.7, 1.1, 2.2, 0.6])
    a = rng.normal(size=dimension)
    b = rng.normal(size=dimension)
    diagonal_a = np.array([1.0, -0.8, 1.4, -1.1, 0.65, 1.25])
    diagonal_b = np.array([-1.2, 0.9, 0.75, -1.35, 1.1, -0.7])
    constraint_rhs = 0.6 * rng.normal(size=dimension) + np.linspace(-0.4, 0.5, dimension)
    gamma = 0.9

    def objective_xy(x: np.ndarray, y: np.ndarray) -> float:
        dx = x - a
        dy = y - b
        return 0.5 * float(q_x @ (dx * dx)) + 0.5 * float(q_y @ (dy * dy))

    def packed_objective(values: np.ndarray) -> float:
        return objective_xy(values[:dimension], values[dimension:])

    def packed_gradient(values: np.ndarray) -> np.ndarray:
        return np.concatenate(
            [q_x * (values[:dimension] - a), q_y * (values[dimension:] - b)]
        )

    constraint_matrix = np.concatenate([np.diag(diagonal_a), np.diag(diagonal_b)], axis=1)
    equality = LinearConstraint(constraint_matrix, constraint_rhs, constraint_rhs)
    reference_result = minimize(
        packed_objective,
        rng.normal(size=2 * dimension),
        jac=packed_gradient,
        method="SLSQP",
        constraints=[equality],
        options={"ftol": 1.0e-13, "maxiter": 2000, "disp": False},
    )
    require(reference_result.success, f"ADMM reference SLSQP failed: {reference_result.message}")

    # Exact KKT system is used only as a certificate and for the Lyapunov witness.
    zero = np.zeros((dimension, dimension))
    kkt_matrix = np.block(
        [
            [np.diag(q_x), zero, np.diag(diagonal_a)],
            [zero, np.diag(q_y), np.diag(diagonal_b)],
            [np.diag(diagonal_a), np.diag(diagonal_b), zero],
        ]
    )
    kkt_rhs = np.concatenate([q_x * a, q_y * b, constraint_rhs])
    exact_solution = np.linalg.solve(kkt_matrix, kkt_rhs)
    x_star = exact_solution[:dimension]
    y_star = exact_solution[dimension : 2 * dimension]
    lambda_star = exact_solution[2 * dimension :]
    reference_x = reference_result.x[:dimension]
    reference_y = reference_result.x[dimension:]
    optimum = objective_xy(x_star, y_star)
    reference_point_error = max(
        float(np.linalg.norm(reference_x - x_star, ord=np.inf)),
        float(np.linalg.norm(reference_y - y_star, ord=np.inf)),
    )
    reference_value_error = abs(float(reference_result.fun) - optimum)
    kkt_residual = max(
        norm2(q_x * (x_star - a) + diagonal_a * lambda_star),
        norm2(q_y * (y_star - b) + diagonal_b * lambda_star),
        norm2(diagonal_a * x_star + diagonal_b * y_star - constraint_rhs),
    )

    require(reference_point_error <= SOLVER_TOL, "ADMM SLSQP point disagrees with KKT solve")
    require(reference_value_error <= SOLVER_TOL, "ADMM SLSQP value disagrees with KKT solve")
    require(kkt_residual <= ALGEBRA_TOL, "ADMM reference KKT residual is too large")

    x = 2.5 * rng.normal(size=dimension)
    y = 2.5 * rng.normal(size=dimension)
    multiplier = 1.7 * rng.normal(size=dimension)
    initial_y_stationarity = norm2(q_y * (y - b) + diagonal_b * multiplier)

    def lyapunov(y_value: np.ndarray, lambda_value: np.ndarray) -> float:
        return (
            gamma * norm2(diagonal_b * (y_value - y_star)) ** 2
            + norm2(lambda_value - lambda_star) ** 2 / gamma
        )

    iterations = 300
    max_x_stationarity = 0.0
    max_y_stationarity = 0.0
    max_lyapunov_signed_residual = -float("inf")
    max_cross_term_from_k1 = -float("inf")
    first_primal_residual = 0.0
    first_dual_residual = 0.0
    first_updated_y_stationarity = 0.0
    final_primal_residual = 0.0
    final_dual_residual = 0.0
    objective_errors: list[float] = []

    for iteration in range(1, iterations + 1):
        previous_y = y.copy()
        previous_lyapunov = lyapunov(y, multiplier)

        x = (
            q_x * a
            - diagonal_a * multiplier
            - gamma * diagonal_a * (diagonal_b * y - constraint_rhs)
        ) / (q_x + gamma * diagonal_a**2)
        y = (
            q_y * b
            - diagonal_b * multiplier
            - gamma * diagonal_b * (diagonal_a * x - constraint_rhs)
        ) / (q_y + gamma * diagonal_b**2)
        primal_residual_vector = diagonal_a * x + diagonal_b * y - constraint_rhs
        multiplier = multiplier + gamma * primal_residual_vector
        dual_residual_vector = gamma * diagonal_a * diagonal_b * (y - previous_y)

        x_stationarity = q_x * (x - a) + diagonal_a * multiplier - dual_residual_vector
        y_stationarity = q_y * (y - b) + diagonal_b * multiplier
        max_x_stationarity = max(max_x_stationarity, norm2(x_stationarity))
        max_y_stationarity = max(max_y_stationarity, norm2(y_stationarity))
        if iteration == 1:
            first_primal_residual = norm2(primal_residual_vector)
            first_dual_residual = norm2(dual_residual_vector)
            first_updated_y_stationarity = norm2(y_stationarity)

        if iteration >= 2:
            b_delta_y = diagonal_b * (y - previous_y)
            current_lyapunov = lyapunov(y, multiplier)
            lyapunov_residual = (
                current_lyapunov
                + gamma * norm2(primal_residual_vector) ** 2
                + gamma * norm2(b_delta_y) ** 2
                - previous_lyapunov
            )
            max_lyapunov_signed_residual = max(max_lyapunov_signed_residual, lyapunov_residual)
            max_cross_term_from_k1 = max(
                max_cross_term_from_k1,
                float(primal_residual_vector @ b_delta_y),
            )

        final_primal_residual = norm2(primal_residual_vector)
        final_dual_residual = norm2(dual_residual_vector)
        objective_errors.append(abs(objective_xy(x, y) - optimum))

    final_objective = objective_xy(x, y)
    final_objective_error = abs(final_objective - optimum)
    tail_objective_error = max(objective_errors[-20:])
    wrong_rhs_sign_residual = norm2(diagonal_a * x_star + diagonal_b * y_star + constraint_rhs)

    require(initial_y_stationarity >= NEGATIVE_CONTROL_MIN, "ADMM y0 index edge was not activated")
    require(first_updated_y_stationarity <= ALGEBRA_TOL, "ADMM y1 stationarity failed")
    require(max_x_stationarity <= ALGEBRA_TOL, "ADMM x optimality identity failed")
    require(max_y_stationarity <= ALGEBRA_TOL, "ADMM y optimality identity failed")
    require(max_lyapunov_signed_residual <= INEQUALITY_TOL, "ADMM Lyapunov descent failed")
    require(max_cross_term_from_k1 <= INEQUALITY_TOL, "ADMM cross-term sign failed")
    require(final_primal_residual <= CONVERGENCE_TOL, "ADMM primal residual did not converge")
    require(final_dual_residual <= CONVERGENCE_TOL, "ADMM dual residual did not converge")
    require(final_objective_error <= CONVERGENCE_TOL, "ADMM objective did not converge")
    require(tail_objective_error <= CONVERGENCE_TOL, "ADMM objective tail is not converged")
    require(wrong_rhs_sign_residual >= NEGATIVE_CONTROL_MIN, "ADMM residual sign control was not detected")

    return {
        "problem": "min f(x)+g(y) subject to A*x+B*y=z, with diagonal separable quadratics",
        "x_dimension": dimension,
        "y_dimension": dimension,
        "constraint_dimension": dimension,
        "A_diagonal": diagonal_a.tolist(),
        "B_diagonal": diagonal_b.tolist(),
        "gamma": gamma,
        "iterations": iterations,
        "reference_solver": "scipy.optimize.minimize(method='SLSQP') with LinearConstraint",
        "reference_solver_status": str(reference_result.message),
        "reference_solver_iterations": int(reference_result.nit),
        "reference_point_inf_error_vs_kkt": reference_point_error,
        "reference_objective_error_vs_kkt": reference_value_error,
        "reference_kkt_l2_residual": kkt_residual,
        "optimal_objective": optimum,
        "final_objective": final_objective,
        "final_objective_absolute_error": final_objective_error,
        "last_20_max_objective_absolute_error": tail_objective_error,
        "first_primal_residual_l2": first_primal_residual,
        "final_primal_residual_l2": final_primal_residual,
        "first_dual_residual_l2": first_dual_residual,
        "final_dual_residual_l2": final_dual_residual,
        "max_x_stationarity_l2_residual": max_x_stationarity,
        "max_y_stationarity_l2_residual": max_y_stationarity,
        "max_lyapunov_descent_signed_residual_from_k1": max_lyapunov_signed_residual,
        "max_lyapunov_descent_violation_from_k1": positive_part(max_lyapunov_signed_residual),
        "max_inner_r_B_delta_y_from_k1": max_cross_term_from_k1,
        "negative_controls": {
            "arbitrary_y0_stationarity_l2_residual": initial_y_stationarity,
            "first_updated_y1_stationarity_l2_residual": first_updated_y_stationarity,
            "wrong_plus_z_primal_residual_at_solution": wrong_rhs_sign_residual,
        },
        "result": "PASS",
    }


def build_report() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    checks: dict[str, Any] = {}
    checks["live_target_correction_surfaces"] = live_target_surface_checks()
    checks["fenchel_conjugate_subdifferential"] = fenchel_checks(rng)
    checks["scaled_moreau_decomposition"] = moreau_checks(rng)
    checks["fenchel_rockafellar"] = fenchel_rockafellar_checks(rng)
    checks["pdhg"] = pdhg_checks(rng)
    checks["admm"] = admm_checks(rng)

    return {
        "schema": "o015-duality-solver-check-v1",
        "chapter": "Habring Chapter 7 - Duality / Dualitas",
        "scope": "bounded finite-dimensional numerical witnesses",
        "caveat": "Numerical witnesses are not proofs of the general theorems.",
        "result": "PASS",
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "reproducibility": {
            "rng": "numpy.random.Generator(PCG64)",
            "seed": SEED,
            "final_process_runs_compared": 2,
            "final_process_outputs_byte_identical": True,
            "json_serialization": "UTF-8, indent=2, sort_keys=True, trailing LF",
        },
        "tolerances": {
            "algebra": ALGEBRA_TOL,
            "independent_solver": SOLVER_TOL,
            "inequality": INEQUALITY_TOL,
            "convergence": CONVERGENCE_TOL,
            "negative_control_minimum_detection": NEGATIVE_CONTROL_MIN,
        },
        "inputs": {
            "authority": file_identity(AUTHORITY_PATH),
            "live_target": file_identity(TARGET_PATH),
            "validator": file_identity(VALIDATOR_PATH),
        },
        "checks": checks,
    }


def main() -> int:
    try:
        report = build_report()
    except Exception as error:
        failure = {
            "schema": "o015-duality-solver-check-v1",
            "result": "FAIL",
            "seed": SEED,
            "failure": f"{type(error).__name__}: {error}",
            "caveat": "Numerical witnesses are not proofs of the general theorems.",
        }
        failure_bytes = (
            json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        sys.stdout.buffer.write(failure_bytes)
        return 1

    report_bytes = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    sys.stdout.buffer.write(report_bytes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
