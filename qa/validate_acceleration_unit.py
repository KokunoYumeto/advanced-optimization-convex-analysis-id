#!/usr/bin/env python3
"""Deterministic open numerical checks for Habring Chapter 6 (acceleration).

The checks cover the corrected mathematical surfaces used by the Indonesian
reader:

* Gelfand's spectral-radius formula, including a separate rho(A)=0 branch;
* Polyak heavy-ball stability and optimal parameters on SPD quadratics; and
* the source-indexed FISTA recurrence and its Lyapunov O(1/k^2) estimate on a
  convex quadratic plus an l1 term.

Only NumPy and SciPy are used.  A failed assertion is written to the result
JSON and causes a nonzero process exit status.
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.optimize import LinearConstraint, minimize


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "qa" / "ACCELERATION_SOLVER_RESULTS.json"
SEED = 20260822

ANALYTIC_TOL = 5.0e-10
SPECTRAL_LIMIT_TOL = 1.5e-2
ROOT_MATCH_TOL = 5.0e-8
SOLVER_TOL = 7.5e-7
INEQUALITY_TOL = 2.0e-9
RECURRENCE_TOL = 1.0e-11
RATE_TOL = 2.5e-2


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def positive_part(value: float) -> float:
    return max(float(value), 0.0)


def spectral_radius(matrix: np.ndarray) -> float:
    return float(np.max(np.abs(np.linalg.eigvals(matrix))))


def matrix_power_root(matrix: np.ndarray, exponent: int) -> tuple[float, float]:
    """Return (||A^n||_2, ||A^n||_2^(1/n)), including the exact-zero case."""

    power_norm = float(np.linalg.norm(np.linalg.matrix_power(matrix, exponent), ord=2))
    if power_norm == 0.0:
        return 0.0, 0.0
    return power_norm, float(np.exp(np.log(power_norm) / exponent))


def gelfand_checks() -> dict[str, Any]:
    """Sample Gelfand behavior for four representative real matrices.

    The nilpotent case is deliberately handled without any normalization by
    rho(A), repairing the division-by-zero gap in the source proof's displayed
    estimate when rho(A)=0.
    """

    similarity = np.array(
        [[1.0, 2.0, -1.0], [0.0, 1.0, 1.0], [1.0, 0.0, 1.0]],
        dtype=float,
    )
    diagonalizable = (
        similarity
        @ np.diag(np.array([0.82, -0.37, 0.12]))
        @ np.linalg.inv(similarity)
    )
    defective_jordan = np.array(
        [[0.90, 1.0, 0.0], [0.0, 0.90, 1.0], [0.0, 0.0, 0.90]],
        dtype=float,
    )
    nilpotent = np.array(
        [
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=float,
    )
    radius = 0.73
    angle = 0.61
    rotation_block = radius * np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=float,
    )
    complex_pair_real_matrix = np.zeros((3, 3), dtype=float)
    complex_pair_real_matrix[:2, :2] = rotation_block
    complex_pair_real_matrix[2, 2] = 0.20

    cases: list[tuple[str, np.ndarray, list[int], float, str]] = [
        (
            "diagonalizable_nonnormal",
            diagonalizable,
            [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024],
            0.82,
            "A=S diag(0.82,-0.37,0.12) S^{-1}",
        ),
        (
            "defective_jordan",
            defective_jordan,
            [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048],
            0.90,
            "size-three Jordan block with eigenvalue 0.90",
        ),
        (
            "nilpotent_shift",
            nilpotent,
            [1, 2, 3, 4, 8, 16],
            0.0,
            "size-four nilpotent Jordan shift",
        ),
        (
            "real_matrix_complex_pair",
            complex_pair_real_matrix,
            [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024],
            radius,
            "real rotation-scaling block with eigenvalues 0.73 exp(+/-0.61 i)",
        ),
    ]

    output: dict[str, Any] = {}
    max_nonzero_limit_error = 0.0
    for name, matrix, exponents, expected_radius, description in cases:
        computed_radius = spectral_radius(matrix)
        require(
            abs(computed_radius - expected_radius) <= ANALYTIC_TOL,
            f"{name}: unexpected spectral radius",
        )
        samples: list[dict[str, float | int]] = []
        for exponent in exponents:
            power_norm, root_norm = matrix_power_root(matrix, exponent)
            samples.append(
                {
                    "n": exponent,
                    "matrix_power_2_norm": power_norm,
                    "nth_root_of_norm": root_norm,
                    "absolute_error_to_rho": abs(root_norm - computed_radius),
                }
            )

        if computed_radius == 0.0:
            # No rho^{-k}, ||A^n||/rho^n, or relative error is formed here.
            zero_exponents = [
                int(sample["n"])
                for sample in samples
                if float(sample["matrix_power_2_norm"]) == 0.0
            ]
            require(zero_exponents, "nilpotent case never reached an exact zero power")
            require(min(zero_exponents) == 4, "nilpotency index should be four")
            require(
                all(float(sample["matrix_power_2_norm"]) == 0.0 for sample in samples[3:]),
                "nilpotent powers should remain zero from n=4 onward",
            )
            limit_evidence = {
                "rho_zero_branch": True,
                "normalization_by_rho": "not formed (rho(A)=0)",
                "nilpotency_index": 4,
                "first_sampled_zero_power": min(zero_exponents),
                "final_nth_root": float(samples[-1]["nth_root_of_norm"]),
                "limit_check": "exactly zero from the nilpotency index onward",
            }
        else:
            final_error = float(samples[-1]["absolute_error_to_rho"])
            max_nonzero_limit_error = max(max_nonzero_limit_error, final_error)
            require(
                final_error <= SPECTRAL_LIMIT_TOL,
                f"{name}: finite-horizon nth-root norm is not close to rho(A)",
            )
            require(
                float(samples[-1]["matrix_power_2_norm"])
                < float(samples[0]["matrix_power_2_norm"]),
                f"{name}: stable powers did not decay over the sampled horizon",
            )
            limit_evidence = {
                "rho_zero_branch": False,
                "normalization_by_rho": "not needed for numerical limit check",
                "final_nth_root": float(samples[-1]["nth_root_of_norm"]),
                "final_absolute_error_to_rho": final_error,
                "limit_tolerance": SPECTRAL_LIMIT_TOL,
            }

        output[name] = {
            "description": description,
            "matrix": matrix.tolist(),
            "eigenvalues": [
                {"real": float(value.real), "imag": float(value.imag)}
                for value in np.linalg.eigvals(matrix)
            ],
            "spectral_radius": computed_radius,
            "samples": samples,
            "limit_evidence": limit_evidence,
            "result": "PASS",
        }

    return {
        "formula": "lim_{n->infinity} ||A^n||_2^(1/n) = rho(A)",
        "zero_radius_correction": (
            "When rho(A)=0, finite-dimensional A is nilpotent; verify A^m=0 "
            "directly instead of dividing by rho(A)."
        ),
        "max_final_absolute_error_for_nonzero_radius_cases": max_nonzero_limit_error,
        "cases": output,
        "result": "PASS",
    }


def companion_roots(eta: float, tau: float, beta: float) -> np.ndarray:
    coefficient = 1.0 + beta - tau * eta
    return np.roots(np.array([1.0, -coefficient, beta], dtype=float))


def heavy_ball_case(
    name: str,
    hessian: np.ndarray,
    eigenvalues: np.ndarray,
    tau: float,
    beta: float,
    x_previous: np.ndarray,
    x_current: np.ndarray,
    expected_optimal_q: float | None,
) -> dict[str, Any]:
    dimension = hessian.shape[0]
    identity = np.eye(dimension)
    transition = np.block(
        [
            [(1.0 + beta) * identity - tau * hessian, -beta * identity],
            [identity, np.zeros_like(identity)],
        ]
    )

    modal_roots = [companion_roots(float(eta), tau, beta) for eta in eigenvalues]
    modal_root_radii = np.array(
        [abs(root) for roots in modal_roots for root in roots], dtype=float
    )
    transition_root_radii = np.abs(np.linalg.eigvals(transition))
    sorted_radius_error = float(
        np.max(
            np.abs(
                np.sort(modal_root_radii)
                - np.sort(np.asarray(transition_root_radii, dtype=float))
            )
        )
    )
    require(
        sorted_radius_error <= ROOT_MATCH_TOL,
        f"{name}: modal roots disagree with the block companion matrix",
    )

    rho = float(np.max(modal_root_radii))
    stability_limit = 2.0 * (1.0 + beta) / float(eigenvalues[-1])
    require(0.0 <= beta < 1.0, f"{name}: beta is outside [0,1)")
    require(0.0 < tau < stability_limit, f"{name}: tau violates the stability interval")
    require(rho < 1.0, f"{name}: companion spectral radius is not below one")

    if expected_optimal_q is not None:
        max_q_error = float(np.max(np.abs(modal_root_radii - expected_optimal_q)))
        require(
            max_q_error <= ROOT_MATCH_TOL,
            "optimal heavy-ball modal root moduli do not equal q",
        )
    else:
        max_q_error = None

    iterations = 320
    state = np.concatenate([x_current, x_previous])
    initial_state = state.copy()
    state_norms = [float(np.linalg.norm(state))]
    iterate_errors = [float(np.linalg.norm(x_current))]
    max_transition_residual = 0.0
    for _ in range(iterations):
        next_x = (
            ((1.0 + beta) * identity - tau * hessian) @ state[:dimension]
            - beta * state[dimension:]
        )
        next_state = np.concatenate([next_x, state[:dimension]])
        max_transition_residual = max(
            max_transition_residual,
            float(np.linalg.norm(next_state - transition @ state)),
        )
        state = next_state
        state_norms.append(float(np.linalg.norm(state)))
        iterate_errors.append(float(np.linalg.norm(state[:dimension])))

    require(
        max_transition_residual <= RECURRENCE_TOL,
        f"{name}: heavy-ball recurrence and transition matrix disagree",
    )
    require(
        state_norms[-1] < 1.0e-6 * state_norms[0],
        f"{name}: iterates did not exhibit stable geometric decay",
    )

    delta = min(2.0e-2, 0.5 * (1.0 - rho))
    geometric_rate = rho + delta
    require(rho < geometric_rate < 1.0, f"{name}: invalid geometric envelope rate")
    power = np.eye(2 * dimension)
    power_bound_constant = 0.0
    for iteration in range(iterations + 1):
        power_bound_constant = max(
            power_bound_constant,
            float(np.linalg.norm(power, ord=2)) / (geometric_rate**iteration),
        )
        power = transition @ power

    envelope = np.array(
        [
            power_bound_constant
            * float(np.linalg.norm(initial_state))
            * geometric_rate**iteration
            for iteration in range(iterations + 1)
        ]
    )
    signed_envelope_residuals = np.asarray(state_norms) - envelope
    max_envelope_signed_residual = float(np.max(signed_envelope_residuals))
    require(
        max_envelope_signed_residual <= RECURRENCE_TOL,
        f"{name}: computed (rho+delta)^k power envelope failed",
    )

    empirical_final_root_rate = float(
        np.exp(
            np.log(state_norms[-1] / state_norms[0]) / iterations
        )
    )
    require(
        empirical_final_root_rate <= rho + RATE_TOL,
        f"{name}: finite-horizon iterate root rate is inconsistent with rho",
    )

    modal_records = []
    for eta, roots in zip(eigenvalues, modal_roots, strict=True):
        modal_records.append(
            {
                "hessian_eigenvalue_eta": float(eta),
                "polynomial": (
                    "lambda^2-(1+beta-tau*eta)*lambda+beta=0"
                ),
                "roots": [
                    {"real": float(root.real), "imag": float(root.imag)}
                    for root in roots
                ],
                "root_moduli": [float(abs(root)) for root in roots],
            }
        )

    return {
        "case": name,
        "beta": beta,
        "tau": tau,
        "stability_condition": "0<=beta<1 and 0<tau<2(1+beta)/L",
        "stability_limit_2(1+beta)/L": stability_limit,
        "stability_margin": stability_limit - tau,
        "companion_matrix_formula": (
            "H=[[ (1+beta)I-tau*Q, -beta*I ], [ I, 0 ]]"
        ),
        "modal_roots": modal_records,
        "companion_spectral_radius": spectral_radius(transition),
        "max_modal_root_radius": rho,
        "max_sorted_modal_vs_companion_root_modulus_error": sorted_radius_error,
        "expected_optimal_q": expected_optimal_q,
        "max_optimal_q_modulus_error": max_q_error,
        "iterations": iterations,
        "initial_state_norm": state_norms[0],
        "final_state_norm": state_norms[-1],
        "initial_iterate_error": iterate_errors[0],
        "final_iterate_error": iterate_errors[-1],
        "max_transition_recurrence_residual": max_transition_residual,
        "geometric_envelope": {
            "delta": delta,
            "rate_rho_plus_delta": geometric_rate,
            "power_bound_constant": power_bound_constant,
            "formula": "||s_k|| <= c(delta)||s_0||(rho(H)+delta)^k",
            "max_signed_residual": max_envelope_signed_residual,
            "max_violation": positive_part(max_envelope_signed_residual),
        },
        "finite_horizon_root_rate": empirical_final_root_rate,
        "result": "PASS",
    }


def heavy_ball_checks(rng: np.random.Generator) -> dict[str, Any]:
    eigenvalues = np.array([1.0, 3.0, 7.0, 12.0, 18.0, 25.0], dtype=float)
    raw_basis = rng.normal(size=(eigenvalues.size, eigenvalues.size))
    orthogonal, _ = np.linalg.qr(raw_basis)
    hessian = orthogonal @ np.diag(eigenvalues) @ orthogonal.T
    observed_eigenvalues = np.linalg.eigvalsh(hessian)
    max_hessian_eigenvalue_error = float(
        np.max(np.abs(observed_eigenvalues - eigenvalues))
    )
    require(
        max_hessian_eigenvalue_error <= ANALYTIC_TOL,
        "constructed SPD spectrum is not preserved",
    )

    mu = float(eigenvalues[0])
    lipschitz_constant = float(eigenvalues[-1])
    optimal_q = (
        np.sqrt(lipschitz_constant) - np.sqrt(mu)
    ) / (
        np.sqrt(lipschitz_constant) + np.sqrt(mu)
    )
    optimal_tau = 4.0 / (
        np.sqrt(lipschitz_constant) + np.sqrt(mu)
    ) ** 2
    optimal_beta = optimal_q**2

    x_previous = np.array([2.0, -1.5, 0.75, 2.5, -0.8, 1.2], dtype=float)
    x_current = np.array([1.7, -1.1, 0.9, 2.1, -0.4, 1.0], dtype=float)

    cases = [
        heavy_ball_case(
            "general_admissible",
            hessian,
            eigenvalues,
            tau=0.060,
            beta=0.35,
            x_previous=x_previous,
            x_current=x_current,
            expected_optimal_q=None,
        ),
        heavy_ball_case(
            "beta_zero_gradient_descent_edge",
            hessian,
            eigenvalues,
            tau=0.060,
            beta=0.0,
            x_previous=x_previous,
            x_current=x_current,
            expected_optimal_q=None,
        ),
        heavy_ball_case(
            "optimal_parameters",
            hessian,
            eigenvalues,
            tau=float(optimal_tau),
            beta=float(optimal_beta),
            x_previous=x_previous,
            x_current=x_current,
            expected_optimal_q=float(optimal_q),
        ),
    ]

    beta_zero = cases[1]
    max_beta_zero_zero_root = max(
        min(float(modulus) for modulus in modal["root_moduli"])
        for modal in beta_zero["modal_roots"]
    )
    require(
        max_beta_zero_zero_root <= ANALYTIC_TOL,
        "beta=0 companion polynomial should contain a zero root",
    )

    return {
        "problem": "min_x 0.5*x^T Q*x with Q symmetric positive definite",
        "hessian_Q": hessian.tolist(),
        "prescribed_eigenvalues": eigenvalues.tolist(),
        "numpy_eigvalsh": observed_eigenvalues.tolist(),
        "mu": mu,
        "L": lipschitz_constant,
        "max_constructed_spectrum_error": max_hessian_eigenvalue_error,
        "optimal_parameter_formulas": {
            "q": "(sqrt(L)-sqrt(mu))/(sqrt(L)+sqrt(mu))",
            "tau": "4/(sqrt(L)+sqrt(mu))^2",
            "beta": "q^2",
        },
        "optimal_q": float(optimal_q),
        "optimal_tau": float(optimal_tau),
        "optimal_beta": float(optimal_beta),
        "cases": cases,
        "beta_zero_edge_contains_exact_zero_root": True,
        "max_beta_zero_minimum_modal_root_modulus": max_beta_zero_zero_root,
        "result": "PASS",
    }


def soft_threshold(vector: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(vector) * np.maximum(np.abs(vector) - threshold, 0.0)


def fista_checks(rng: np.random.Generator) -> dict[str, Any]:
    """Validate FISTA against proximal gradient on a coupled quadratic+l1 model."""

    hessian = np.array(
        [
            [5.0, 3.0, 0.0, 0.0, 0.0],
            [3.0, 5.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 10.0, 6.0, 0.0],
            [0.0, 0.0, 6.0, 10.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    exact_eigenvalues = np.array([1.0, 2.0, 4.0, 8.0, 16.0], dtype=float)
    observed_eigenvalues = np.linalg.eigvalsh(hessian)
    require(
        np.max(np.abs(observed_eigenvalues - exact_eigenvalues)) <= ANALYTIC_TOL,
        "quadratic Hessian does not have the declared exact spectrum",
    )
    lipschitz_constant = 16.0
    tau = 1.0 / lipschitz_constant
    lam = 0.35

    # Construct a known exact optimizer through the composite KKT condition
    # Q*x_star-b+lambda*s=0, with s_i=sign(x_i) off zero and |s_i|<1 at zero.
    x_star = np.array([1.1, -0.7, 0.0, 0.8, 0.0], dtype=float)
    kkt_subgradient = np.array([1.0, -1.0, 0.40, 1.0, -0.65], dtype=float)
    linear_term = hessian @ x_star + lam * kkt_subgradient

    def smooth_value(x: np.ndarray) -> float:
        return 0.5 * float(x @ hessian @ x) - float(linear_term @ x)

    def smooth_gradient(x: np.ndarray) -> np.ndarray:
        return hessian @ x - linear_term

    def objective(x: np.ndarray) -> float:
        return smooth_value(x) + lam * float(np.abs(x).sum())

    def prox_grad_at(x: np.ndarray, step_size: float) -> np.ndarray:
        return soft_threshold(
            x - step_size * smooth_gradient(x),
            step_size * lam,
        )

    exact_objective = objective(x_star)
    kkt_vector = smooth_gradient(x_star) + lam * kkt_subgradient
    nonzero = np.abs(x_star) > 0.0
    zero = ~nonzero
    max_nonzero_kkt_residual = float(np.max(np.abs(kkt_vector[nonzero])))
    max_zero_subgradient_excess = float(
        np.max(np.maximum(np.abs(smooth_gradient(x_star)[zero]) - lam, 0.0))
    )
    exact_gradient_mapping_norm = float(
        np.linalg.norm((x_star - prox_grad_at(x_star, tau)) / tau)
    )
    require(max_nonzero_kkt_residual <= ANALYTIC_TOL, "known optimum KKT residual failed")
    require(max_zero_subgradient_excess <= ANALYTIC_TOL, "known zero-coordinate KKT failed")
    require(exact_gradient_mapping_norm <= ANALYTIC_TOL, "known optimum is not fixed by prox-grad")

    dimension = x_star.size
    constraint_matrix = np.zeros((2 * dimension, 2 * dimension), dtype=float)
    for coordinate in range(dimension):
        constraint_matrix[coordinate, coordinate] = -1.0
        constraint_matrix[coordinate, dimension + coordinate] = 1.0
        constraint_matrix[dimension + coordinate, coordinate] = 1.0
        constraint_matrix[dimension + coordinate, dimension + coordinate] = 1.0
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
        np.concatenate([np.zeros(dimension), np.ones(dimension)]),
        jac=epigraph_jacobian,
        method="SLSQP",
        bounds=[(None, None)] * dimension + [(0.0, None)] * dimension,
        constraints=[epigraph_constraint],
        options={"ftol": 1.0e-14, "maxiter": 10000, "disp": False},
    )
    require(reference.success, f"independent SLSQP epigraph solve failed: {reference.message}")
    slsqp_x = np.asarray(reference.x[:dimension], dtype=float)
    slsqp_inf_error = float(np.linalg.norm(slsqp_x - x_star, ord=np.inf))
    slsqp_objective_gap = abs(float(reference.fun) - exact_objective)
    require(slsqp_inf_error <= SOLVER_TOL, "SLSQP optimizer disagrees with exact KKT optimizer")
    require(slsqp_objective_gap <= SOLVER_TOL, "SLSQP objective disagrees with exact optimum")

    # Deterministic sample test of the exact fundamental prox-grad inequality.
    sample_pairs = [(rng.normal(size=dimension), rng.normal(size=dimension)) for _ in range(256)]
    sample_pairs.extend(
        [
            (x_star.copy(), np.zeros(dimension)),
            (np.zeros(dimension), x_star.copy()),
            (
                np.array([3.0, -2.0, 1.0, -1.0, 2.0]),
                np.array([-1.0, 0.5, 2.0, 1.5, -0.5]),
            ),
        ]
    )
    max_fundamental_signed_residual = -float("inf")
    max_prox_kkt_residual = 0.0
    step_sizes = [tau, 0.80 * tau]
    for step_size in step_sizes:
        require(step_size <= 1.0 / lipschitz_constant, "sample step exceeds 1/L")
        for x, y in sample_pairs:
            prox = prox_grad_at(y, step_size)
            ell_f = (
                smooth_value(x)
                - smooth_value(y)
                - float((x - y) @ smooth_gradient(y))
            )
            lhs = objective(x) - objective(prox)
            rhs = (
                float(np.dot(x - prox, x - prox)) / (2.0 * step_size)
                - float(np.dot(x - y, x - y)) / (2.0 * step_size)
                + ell_f
            )
            max_fundamental_signed_residual = max(
                max_fundamental_signed_residual,
                rhs - lhs,
            )

            prox_subgradient = np.zeros(dimension)
            prox_nonzero = np.abs(prox) > 1.0e-13
            prox_subgradient[prox_nonzero] = np.sign(prox[prox_nonzero])
            residual_vector = (
                (prox - y) / step_size
                + smooth_gradient(y)
                + lam * prox_subgradient
            )
            if np.any(~prox_nonzero):
                zero_coordinates = ~prox_nonzero
                residual_vector[zero_coordinates] = np.maximum(
                    np.abs(
                        (prox[zero_coordinates] - y[zero_coordinates]) / step_size
                        + smooth_gradient(y)[zero_coordinates]
                    )
                    - lam,
                    0.0,
                )
            max_prox_kkt_residual = max(
                max_prox_kkt_residual,
                float(np.linalg.norm(residual_vector, ord=np.inf)),
            )

    require(
        max_fundamental_signed_residual <= INEQUALITY_TOL,
        "fundamental prox-grad inequality failed",
    )
    require(max_prox_kkt_residual <= ANALYTIC_TOL, "prox step KKT residual failed")

    x_initial = np.array([3.0, -2.4, 2.1, -1.6, 4.2], dtype=float)
    iterations = 320

    # Source indexing: x_0=x_1, t_1=1; the loop produces x_{k+1}.
    fista_x: list[np.ndarray] = [x_initial.copy(), x_initial.copy()]
    t_values = np.zeros(iterations + 1, dtype=float)
    t_values[1] = 1.0
    beta_values = np.zeros(iterations, dtype=float)
    max_t_identity_residual = 0.0
    min_t_lower_bound_margin = float("inf")
    for k in range(1, iterations):
        t_values[k + 1] = 0.5 * (
            1.0 + np.sqrt(1.0 + 4.0 * t_values[k] ** 2)
        )
        beta_values[k] = (t_values[k] - 1.0) / t_values[k + 1]
        y_k = fista_x[k] + beta_values[k] * (fista_x[k] - fista_x[k - 1])
        fista_x.append(prox_grad_at(y_k, tau))
        max_t_identity_residual = max(
            max_t_identity_residual,
            abs(t_values[k + 1] ** 2 - t_values[k + 1] - t_values[k] ** 2),
        )
        min_t_lower_bound_margin = min(
            min_t_lower_bound_margin,
            t_values[k] - (k + 1.0) / 2.0,
            t_values[k + 1] - (k + 2.0) / 2.0,
        )

    require(max_t_identity_residual <= RECURRENCE_TOL, "FISTA t recursion identity failed")
    require(min_t_lower_bound_margin >= -RECURRENCE_TOL, "t_k >= (k+1)/2 failed")

    fista_values = np.array([objective(x) for x in fista_x], dtype=float)
    fista_gaps = fista_values - exact_objective
    energies = np.zeros(iterations + 1, dtype=float)
    for k in range(1, iterations + 1):
        momentum_point = (
            x_star
            - t_values[k] * fista_x[k]
            + (t_values[k] - 1.0) * fista_x[k - 1]
        )
        energies[k] = (
            t_values[k] ** 2 * fista_gaps[k]
            + float(momentum_point @ momentum_point) / (2.0 * tau)
        )

    energy_differences = energies[2:] - energies[1:-1]
    max_energy_signed_increase = float(np.max(energy_differences))
    require(
        max_energy_signed_increase <= INEQUALITY_TOL,
        "FISTA Lyapunov energy is not nonincreasing",
    )

    initial_energy = float(energies[1])
    max_t_bound_signed_residual = -float("inf")
    max_explicit_bound_signed_residual = -float("inf")
    for k in range(1, iterations + 1):
        t_bound = initial_energy / (t_values[k] ** 2)
        explicit_bound = 4.0 * initial_energy / ((k + 1.0) ** 2)
        max_t_bound_signed_residual = max(
            max_t_bound_signed_residual,
            float(fista_gaps[k] - t_bound),
        )
        max_explicit_bound_signed_residual = max(
            max_explicit_bound_signed_residual,
            float(fista_gaps[k] - explicit_bound),
        )
    require(
        max_t_bound_signed_residual <= INEQUALITY_TOL,
        "FISTA E_1/t_k^2 bound failed",
    )
    require(
        max_explicit_bound_signed_residual <= INEQUALITY_TOL,
        "corrected explicit O(1/k^2) bound failed",
    )

    pg_x = x_initial.copy()
    pg_values = [objective(pg_x)]
    for _ in range(1, iterations + 1):
        pg_x = prox_grad_at(pg_x, tau)
        pg_values.append(objective(pg_x))
    pg_values_array = np.asarray(pg_values, dtype=float)
    pg_gaps = pg_values_array - exact_objective

    # Compare by equal numbers of prox-gradient evaluations.  Under the source
    # indexing, FISTA x_{m+1} and ordinary proximal gradient's m-th iterate
    # have each used m evaluations of grad f and prox_{tau g}.
    milestones = [1, 2, 5, 10, 20, 40, 80, 160, 319]
    comparison = [
        {
            "prox_grad_evaluations": evaluations,
            "fista_source_index": evaluations + 1,
            "proximal_gradient_iteration": evaluations,
            "fista_gap": float(fista_gaps[evaluations + 1]),
            "proximal_gradient_gap": float(pg_gaps[evaluations]),
            "fista_to_pg_gap_ratio": (
                float(fista_gaps[evaluations + 1] / pg_gaps[evaluations])
                if pg_gaps[evaluations] > 1.0e-15
                else None
            ),
        }
        for evaluations in milestones
    ]

    comparison_evaluations = 40
    require(
        fista_gaps[comparison_evaluations + 1] < pg_gaps[comparison_evaluations],
        "FISTA did not improve on proximal gradient at the declared equal-work comparison",
    )

    return {
        "problem": "min_x 0.5*x^T Q*x-b^T*x+lambda*||x||_1",
        "hessian_Q": hessian.tolist(),
        "linear_term_b": linear_term.tolist(),
        "lambda": lam,
        "exact_hessian_eigenvalues": exact_eigenvalues.tolist(),
        "numpy_eigvalsh": observed_eigenvalues.tolist(),
        "L_exact": lipschitz_constant,
        "step_size_tau": tau,
        "tau_times_L": tau * lipschitz_constant,
        "step_condition": "tau <= 1/L",
        "exact_optimum_construction": (
            "b=Q*x_star+lambda*s with valid s in partial ||x_star||_1"
        ),
        "exact_x_star": x_star.tolist(),
        "exact_objective": exact_objective,
        "max_nonzero_coordinate_kkt_residual": max_nonzero_kkt_residual,
        "max_zero_coordinate_subgradient_excess": max_zero_subgradient_excess,
        "exact_optimum_gradient_mapping_norm": exact_gradient_mapping_norm,
        "independent_reference": {
            "solver": "scipy.optimize.minimize(method='SLSQP') with l1 epigraph variables (x,u)",
            "success": bool(reference.success),
            "message": str(reference.message),
            "iterations": int(reference.nit),
            "x": slsqp_x.tolist(),
            "objective": float(reference.fun),
            "inf_error_to_exact_x_star": slsqp_inf_error,
            "absolute_objective_gap": slsqp_objective_gap,
        },
        "fundamental_prox_grad_inequality": {
            "formula": (
                "F(x)-F(P_tau(y)) >= ||x-P_tau(y)||^2/(2*tau) "
                "- ||x-y||^2/(2*tau) + ell_f(x,y)"
            ),
            "step_sizes": step_sizes,
            "sample_pairs_per_step_size": len(sample_pairs),
            "max_signed_residual_rhs_minus_lhs": max_fundamental_signed_residual,
            "max_violation": positive_part(max_fundamental_signed_residual),
            "max_prox_step_kkt_residual": max_prox_kkt_residual,
        },
        "fista": {
            "indexing": "x_0=x_1, t_1=1; step k produces x_{k+1}",
            "t_recursion": "t_{k+1}=(1+sqrt(1+4*t_k^2))/2",
            "beta_recursion": "beta_k=(t_k-1)/t_{k+1}",
            "max_t_identity_residual": max_t_identity_residual,
            "min_t_lower_bound_margin": min_t_lower_bound_margin,
            "energy": (
                "E_k=t_k^2*(F(x_k)-F*)+"
                "||x*-t_k*x_k+(t_k-1)*x_{k-1}||^2/(2*tau)"
            ),
            "initial_energy_E1": initial_energy,
            "max_energy_signed_increase": max_energy_signed_increase,
            "max_energy_monotonicity_violation": positive_part(max_energy_signed_increase),
            "corrected_bound": (
                "F(x_k)-F* <= E_1/t_k^2 <= 4*E_1/(k+1)^2, k>=1"
            ),
            "max_E1_over_tk_squared_signed_residual": max_t_bound_signed_residual,
            "max_E1_over_tk_squared_violation": positive_part(max_t_bound_signed_residual),
            "max_explicit_O1_over_k2_signed_residual": max_explicit_bound_signed_residual,
            "max_explicit_O1_over_k2_violation": positive_part(
                max_explicit_bound_signed_residual
            ),
            "iterations": iterations,
            "final_objective": float(fista_values[-1]),
            "final_gap": float(fista_gaps[-1]),
        },
        "proximal_gradient": {
            "iterations": iterations,
            "final_objective": float(pg_values_array[-1]),
            "final_gap": float(pg_gaps[-1]),
        },
        "comparison": {
            "work_alignment": (
                "FISTA x_{m+1} and proximal-gradient iterate m each use m "
                "gradient/prox evaluations"
            ),
            "milestones": comparison,
            "declared_equal_work_evaluations": comparison_evaluations,
            "fista_gap_at_equal_work": float(fista_gaps[comparison_evaluations + 1]),
            "proximal_gradient_gap_at_equal_work": float(
                pg_gaps[comparison_evaluations]
            ),
        },
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
        "schema": "o015-acceleration-solver-check-v1",
        "result": "FAIL",
        "scope": "Habring Chapter 6: acceleration",
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "reproducibility": {
            "numpy_rng": "numpy.random.Generator(PCG64)",
            "seed": SEED,
            "network_or_proprietary_solver": False,
        },
        "tolerances": {
            "analytic": ANALYTIC_TOL,
            "spectral_limit": SPECTRAL_LIMIT_TOL,
            "root_match": ROOT_MATCH_TOL,
            "independent_solver": SOLVER_TOL,
            "inequality": INEQUALITY_TOL,
            "recurrence": RECURRENCE_TOL,
            "finite_horizon_rate": RATE_TOL,
        },
        "checks": {},
    }
    try:
        rng = np.random.default_rng(SEED)
        report["checks"]["gelfand_spectral_radius"] = gelfand_checks()
        report["checks"]["heavy_ball_spd_quadratics"] = heavy_ball_checks(rng)
        report["checks"]["fista_quadratic_l1"] = fista_checks(rng)
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
