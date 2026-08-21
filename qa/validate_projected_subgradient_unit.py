#!/usr/bin/env python3
"""Deterministic open-solver checks for Habring Chapter 4 (id-ID)."""

from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "qa" / "PROJECTED_SUBGRADIENT_SOLVER_RESULTS.json"
TOL = 2.0e-7


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def projection_checks() -> dict[str, float | int]:
    rng = np.random.default_rng(20260821)
    lo = np.array([0.0, -0.5])
    hi = np.array([1.0, 0.5])
    max_violation = 0.0
    max_nonexpansive = 0.0
    for _ in range(512):
        x1 = rng.normal(size=2) * 2.0
        x2 = rng.normal(size=2) * 2.0
        y = rng.uniform(lo, hi)
        p1 = np.clip(x1, lo, hi)
        p2 = np.clip(x2, lo, hi)
        max_violation = max(max_violation, float(np.dot(x1 - p1, y - p1)))
        max_nonexpansive = max(
            max_nonexpansive,
            float(np.linalg.norm(p1 - p2) - np.linalg.norm(x1 - x2)),
        )
    require(max_violation <= TOL, "projection variational inequality failed")
    require(max_nonexpansive <= TOL, "projection nonexpansiveness failed")
    return {
        "samples": 512,
        "max_variational_inequality_residual": max_violation,
        "max_nonexpansiveness_residual": max_nonexpansive,
    }


def abs_objective(x: np.ndarray) -> float:
    return float(abs(x[0] - 2.0) + abs(x[1] + 1.0))


def abs_subgradient(_: np.ndarray) -> np.ndarray:
    # On C=[-1,1]x[-0.5,0.5], both signs are fixed.
    return np.array([-1.0, 1.0])


def projected_step(x: np.ndarray, tau: float, g: np.ndarray) -> np.ndarray:
    return np.clip(x - tau * g, np.array([-1.0, -0.5]), np.array([1.0, 0.5]))


def polyak_and_general_checks() -> dict[str, object]:
    x_star = np.array([1.0, -0.5])
    f_star = abs_objective(x_star)
    lipschitz_bound = float(np.sqrt(2.0))
    x = np.array([-1.0, 0.5])
    initial_distance = float(np.linalg.norm(x - x_star))
    gaps: list[float] = []
    max_fundamental_residual = 0.0
    max_polyak_rate_residual = 0.0

    for k in range(1, 129):
        g = abs_subgradient(x)
        gap = abs_objective(x) - f_star
        tau = gap / float(np.dot(g, g)) if gap > 0.0 else 0.0
        next_x = projected_step(x, tau, g)
        lhs = float(np.dot(next_x - x_star, next_x - x_star))
        rhs = (
            float(np.dot(x - x_star, x - x_star))
            - 2.0 * tau * gap
            + tau * tau * float(np.dot(g, g))
        )
        max_fundamental_residual = max(max_fundamental_residual, lhs - rhs)
        gaps.append(gap)
        best_gap = min(gaps)
        bound = lipschitz_bound * initial_distance / np.sqrt(k)
        max_polyak_rate_residual = max(max_polyak_rate_residual, best_gap - bound)
        x = next_x

    require(max_fundamental_residual <= TOL, "Polyak fundamental inequality failed")
    require(max_polyak_rate_residual <= TOL, "Polyak best-iterate rate failed")
    require(abs_objective(x) - f_star <= TOL, "Polyak iterates did not reach the optimum")

    nonzero_optimal_subgradient = abs_subgradient(x_star)
    stationary = projected_step(x_star, 0.0, nonzero_optimal_subgradient)
    require(np.linalg.norm(nonzero_optimal_subgradient) > 0.0, "demonstration subgradient is zero")
    require(np.array_equal(stationary, x_star), "zero-gap Polyak step should stagnate")

    x = np.array([-1.0, 0.5])
    initial_distance_sq = float(np.dot(x - x_star, x - x_star))
    weighted_gap_sum = 0.0
    tau_sum = 0.0
    tau_sq_sum = 0.0
    best_gap = float("inf")
    max_general_bound_residual = 0.0
    for k in range(1, 1001):
        tau = k ** -0.5
        g = abs_subgradient(x)
        gap = abs_objective(x) - f_star
        best_gap = min(best_gap, gap)
        tau_sum += tau
        tau_sq_sum += tau * tau
        weighted_gap_sum += tau * gap
        bound = (initial_distance_sq + lipschitz_bound**2 * tau_sq_sum) / (2.0 * tau_sum)
        max_general_bound_residual = max(max_general_bound_residual, best_gap - bound)
        x = projected_step(x, tau, g)

    require(max_general_bound_residual <= TOL, "general step-size bound failed")
    return {
        "objective": "abs(x1-2)+abs(x2+1) over [-1,1]x[-0.5,0.5]",
        "x_star": x_star.tolist(),
        "f_star": f_star,
        "selected_subgradient_norm_bound": lipschitz_bound,
        "polyak_iterations": 128,
        "polyak_final_gap": abs_objective(x_star) - f_star,
        "max_fundamental_residual": max_fundamental_residual,
        "max_polyak_rate_residual": max_polyak_rate_residual,
        "nonzero_subgradient_at_constrained_optimum": nonzero_optimal_subgradient.tolist(),
        "strict_decrease_counterexample": "g is nonzero at x_star, but the objective gap and Polyak step are zero",
        "general_schedule": "tau_k=k^(-1/2)",
        "general_iterations": 1000,
        "general_ratio": tau_sum / tau_sq_sum,
        "max_general_bound_residual": max_general_bound_residual,
    }


def strong_objective(x: np.ndarray, mu: float, lam: float, center: np.ndarray) -> float:
    return float(0.5 * mu * np.dot(x - center, x - center) + lam * np.abs(x).sum())


def strong_subgradient(x: np.ndarray, mu: float, lam: float, center: np.ndarray) -> np.ndarray:
    return mu * (x - center) + lam * np.sign(x)


def strong_convex_checks() -> dict[str, object]:
    mu = 2.0
    lam = 0.4
    center = np.array([1.5, -1.0])
    lo = np.array([-1.0, -0.5])
    hi = np.array([1.0, 0.5])

    # Independent epigraph formulation with variables (x1,x2,t1,t2).
    def epigraph_objective(z: np.ndarray) -> float:
        return float(0.5 * mu * np.dot(z[:2] - center, z[:2] - center) + lam * z[2:].sum())

    constraints = [
        {"type": "ineq", "fun": lambda z, i=i: z[2 + i] - z[i]}
        for i in range(2)
    ] + [
        {"type": "ineq", "fun": lambda z, i=i: z[2 + i] + z[i]}
        for i in range(2)
    ]
    solution = minimize(
        epigraph_objective,
        np.array([0.0, 0.0, 0.1, 0.1]),
        method="SLSQP",
        bounds=[(lo[0], hi[0]), (lo[1], hi[1]), (0.0, None), (0.0, None)],
        constraints=constraints,
        options={"ftol": 1.0e-13, "maxiter": 1000},
    )
    require(solution.success, f"SLSQP epigraph solve failed: {solution.message}")
    x_star = solution.x[:2]
    expected_x = np.array([1.0, -0.5])
    require(np.linalg.norm(x_star - expected_x, ord=np.inf) <= 2.0e-6, "wrong strong-convex optimum")
    f_star = strong_objective(x_star, mu, lam, center)

    # A valid uniform bound for the selected subgradient over the whole box.
    coordinate_bounds = np.array([5.4, 3.4])
    subgradient_bound = float(np.linalg.norm(coordinate_bounds))
    x = np.array([-0.5, 0.4])
    best_gap = float("inf")
    max_improved_residual = 0.0
    max_value_rate_residual = 0.0
    max_distance_rate_residual = 0.0

    for k in range(1, 257):
        g = strong_subgradient(x, mu, lam, center)
        require(np.linalg.norm(g) <= subgradient_bound + TOL, "selected subgradient exceeds L")
        tau = 2.0 / (mu * k)
        next_x = np.clip(x - tau * g, lo, hi)
        gap = strong_objective(x, mu, lam, center) - f_star
        lhs = float(np.dot(next_x - x_star, next_x - x_star))
        rhs = (
            (1.0 - mu * tau) * float(np.dot(x - x_star, x - x_star))
            - 2.0 * tau * gap
            + tau * tau * subgradient_bound**2
        )
        max_improved_residual = max(max_improved_residual, lhs - rhs)
        best_gap = min(best_gap, gap)
        if k >= 2:
            value_bound = 2.0 * subgradient_bound**2 / (mu * (k - 1))
            max_value_rate_residual = max(max_value_rate_residual, best_gap - value_bound)
        # next_x is x_{k+1}; its theorem bound has denominator k.
        distance_bound = 2.0 * subgradient_bound / (mu * np.sqrt(k))
        max_distance_rate_residual = max(
            max_distance_rate_residual,
            float(np.linalg.norm(next_x - x_star)) - distance_bound,
        )
        x = next_x

    require(max_improved_residual <= TOL, "strong-convex fundamental inequality failed")
    require(max_value_rate_residual <= TOL, "corrected 2L^2 value bound failed")
    require(max_distance_rate_residual <= TOL, "iterate-distance induction bound failed")
    return {
        "objective": "(mu/2)||x-c||^2+lambda||x||_1 over a box",
        "mu": mu,
        "lambda": lam,
        "center": center.tolist(),
        "solver": "scipy.optimize.minimize(method='SLSQP') epigraph formulation",
        "solver_status": solution.message,
        "x_star": x_star.tolist(),
        "expected_x": expected_x.tolist(),
        "f_star": f_star,
        "selected_subgradient_norm_bound": subgradient_bound,
        "iterations": 256,
        "max_improved_fundamental_residual": max_improved_residual,
        "max_corrected_value_rate_residual": max_value_rate_residual,
        "max_distance_rate_residual": max_distance_rate_residual,
    }


report = {
    "schema": "o015-projected-subgradient-solver-check-v1",
    "result": "pass",
    "python": platform.python_version(),
    "platform": platform.platform(),
    "numpy": np.__version__,
    "scipy": scipy.__version__,
    "checks": {
        "projection": projection_checks(),
        "polyak_and_general_steps": polyak_and_general_checks(),
        "strongly_convex": strong_convex_checks(),
    },
}
RESULT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
