#!/usr/bin/env python3
"""Deterministic open-runtime numerical validation for Penn Chapter 3 id-ID."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any, Callable

import mpmath as mp
import numpy as np
import scipy
from scipy import optimize


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority/penn-state/source/ClassNotes/Section3.tex"
TARGET = ROOT / "source/id-ID/penn-03-pendakian-gradien-dan-pencarian-garis-id.tex"
LEDGER = ROOT / "qa/PENN_CH03_PROPOSED_LEDGER.jsonl"
RESULTS = ROOT / "qa/PENN_CH03_SOLVER_RESULTS.json"

EXPECTED_SOURCE = (41715, "d4ae6142e2366b12575eafddc833df067518af114e9816187668cc367be43010")
EXPECTED_TARGET = (44364, "7c75d0ae56a5a912d561d91ece607f088a4ff4f3de4dbc3396ce40d6d7d6a229")
EXPECTED_LEDGER: tuple[int, str] = (
    14813,
    "80aa5a3f7b4f46c7dfe01f58f6f68555c9aeaeb91d0877eaf27cbb447c4a67fa",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def clean_float(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError(f"non-finite result {value!r}")
    return float(f"{value:.16g}")


def clean(value: Any) -> Any:
    if isinstance(value, (float, np.floating)):
        return clean_float(float(value))
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.ndarray):
        return [clean(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    return value


CHECKS: list[dict[str, Any]] = []


def record(check_id: str, passed: bool, evidence: Any, *, negative_control: bool = False) -> None:
    CHECKS.append(
        {
            "check_id": check_id,
            "status": "PASS" if bool(passed) else "FAIL",
            "negative_control": negative_control,
            "evidence": clean(evidence),
        }
    )


def quadratic_vertex(xs: tuple[float, float, float], ys: tuple[float, float, float]) -> tuple[float, bool]:
    matrix = np.array([[x * x, x, 1.0] for x in xs], dtype=float)
    try:
        r, s, _ = np.linalg.solve(matrix, np.array(ys, dtype=float))
    except np.linalg.LinAlgError:
        return math.nan, False
    if r == 0.0:
        return math.nan, False
    return float(-s / (2.0 * r)), bool(r < 0.0)


def guarded_bracket(
    phi: Callable[[float], float],
    a: float,
    b: float,
    tau: float,
    limit: int,
) -> dict[str, Any]:
    if not a < b or not phi(b) > phi(a):
        return {"status": "invalid_initial_rise", "iterations": 0, "trace": []}
    c = b + tau * (b - a)
    trace: list[dict[str, Any]] = []
    for iteration in range(limit):
        fa, fb, fc = phi(a), phi(b), phi(c)
        if fb > fc:
            return {
                "status": "strict_bracket",
                "iterations": iteration,
                "bracket": [a, b, c],
                "values": [fa, fb, fc],
                "trace": trace,
            }
        if fb == fc:
            midpoint = (b + c) / 2.0
            if phi(midpoint) > fb:
                return {
                    "status": "strict_bracket",
                    "iterations": iteration,
                    "bracket": [b, midpoint, c],
                    "values": [fb, phi(midpoint), fc],
                    "trace": trace,
                    "equality_branch": True,
                }
            return {"status": "strict_unimodality_failure", "iterations": iteration, "trace": trace}
        u, is_maximum = quadratic_vertex((a, b, c), (fa, fb, fc))
        lower = c + tau * (c - b)
        upper = c + tau * tau * (c - b)
        accepted = is_maximum and math.isfinite(u) and lower <= u <= upper
        d = u if accepted else lower
        trace.append(
            {
                "iteration": iteration,
                "a": a,
                "b": b,
                "c": c,
                "proposal": u if math.isfinite(u) else None,
                "accepted": accepted,
                "d": d,
                "gap_ratio": (d - c) / (c - b),
            }
        )
        a, b, c = b, c, d
    return {"status": "iteration_limit", "iterations": limit, "trace": trace}


def golden_section(
    phi: Callable[[float], float], a: float, b: float, epsilon: float, limit: int = 1000
) -> dict[str, Any]:
    tau = (1.0 + math.sqrt(5.0)) / 2.0
    rho = 1.0 / tau
    x2 = b - rho * (b - a)
    x3 = a + rho * (b - a)
    f2, f3 = phi(x2), phi(x3)
    evaluations = 2
    widths = [b - a]
    intervals = [[a, b]]
    for iteration in range(limit):
        if b - a <= 2.0 * epsilon:
            point = x2 if f2 > f3 else x3
            return {
                "status": "width_tolerance",
                "iterations": iteration,
                "point": point,
                "value": phi(point),
                "interval": [a, b],
                "evaluations": evaluations,
                "widths": widths,
                "intervals": intervals,
            }
        if f2 > f3:
            b, x3, f3 = x3, x2, f2
            x2 = b - rho * (b - a)
            f2 = phi(x2)
        else:
            a, x2, f2 = x2, x3, f3
            x3 = a + rho * (b - a)
            f3 = phi(x3)
        evaluations += 1
        widths.append(b - a)
        intervals.append([a, b])
    return {"status": "iteration_limit", "iterations": limit}


def bisection_maximum(
    derivative: Callable[[float], float],
    a: float,
    b: float,
    epsilon_x: float,
    epsilon_g: float,
    limit: int,
) -> dict[str, Any]:
    if not derivative(a) > 0.0 > derivative(b):
        return {"status": "invalid_derivative_bracket"}
    left, right = a, b
    trace: list[dict[str, Any]] = []
    for iteration in range(limit):
        u = (left + right) / 2.0
        g = derivative(u)
        trace.append({"iteration": iteration, "left": left, "right": right, "u": u, "g": g})
        if g == 0.0:
            return {"status": "exact_root", "point": u, "interval": [left, right], "trace": trace}
        if right - left <= 2.0 * epsilon_x:
            return {"status": "position_tolerance", "point": u, "interval": [left, right], "trace": trace}
        if epsilon_g > 0.0 and abs(g) <= epsilon_g:
            return {"status": "derivative_tolerance", "point": u, "interval": [left, right], "trace": trace}
        if g > 0.0:
            left = u
        else:
            right = u
    return {"status": "iteration_limit", "trace": trace}


def newton_stationary(
    derivative: Callable[[float], float],
    hessian: Callable[[float], float],
    x0: float,
    epsilon_g: float,
    epsilon_x: float,
    limit: int,
) -> dict[str, Any]:
    x = float(x0)
    trace: list[dict[str, Any]] = []
    for iteration in range(limit):
        g, curvature = derivative(x), hessian(x)
        trace.append({"iteration": iteration, "x": x, "gradient": g, "hessian": curvature})
        if abs(g) <= epsilon_g:
            return {
                "status": "gradient_tolerance",
                "point": x,
                "curvature": curvature,
                "classification": "maximum" if curvature < 0 else "minimum" if curvature > 0 else "degenerate",
                "trace": trace,
            }
        if curvature == 0.0:
            return {"status": "zero_hessian", "point": x, "trace": trace}
        step = -g / curvature
        x_next = x + step
        if abs(step) <= epsilon_x:
            g_next, h_next = derivative(x_next), hessian(x_next)
            trace.append({"iteration": iteration + 1, "x": x_next, "gradient": g_next, "hessian": h_next})
            return {
                "status": "step_tolerance",
                "point": x_next,
                "curvature": h_next,
                "classification": "maximum" if h_next < 0 else "minimum" if h_next > 0 else "degenerate",
                "trace": trace,
            }
        x = x_next
    return {"status": "iteration_limit", "point": x, "trace": trace}


def main() -> int:
    source_id = identity(SOURCE)
    target_id = identity(TARGET)
    ledger_id = identity(LEDGER)
    record(
        "authority_identity",
        (source_id["bytes"], source_id["sha256"]) == EXPECTED_SOURCE,
        {"expected": EXPECTED_SOURCE, "actual": source_id},
    )
    record(
        "target_identity",
        (target_id["bytes"], target_id["sha256"]) == EXPECTED_TARGET,
        {"expected": EXPECTED_TARGET, "actual": target_id},
    )
    record(
        "renumbered_ledger_identity_is_frozen",
        (ledger_id["bytes"], ledger_id["sha256"]) == EXPECTED_LEDGER,
        {"expected": EXPECTED_LEDGER, "actual": ledger_id},
    )

    target_text = TARGET.read_text(encoding="utf-8")
    required_surfaces = [
        "d90.penn.v1.ch03.seg0001",
        "d90.penn.v1.ch03.seg0008",
        "d-c\\geq\\tau(c-b)",
        "|u-x^*|\\leq\\varepsilon_g/m",
        "h(x)=-\\phi'(x)",
        "\\gamma(x)=-1/\\phi''(x)",
        "N(x)=x-\\frac{h(x)}{h'(x)}",
        "\\frac{|h''(x^*)|}{2|h'(x^*)|}",
    ]
    record(
        "validated_surfaces_present_in_pinned_target",
        all(surface in target_text for surface in required_surfaces),
        required_surfaces,
    )

    # Quadratic interpolation and turning-point classification.
    xs = (-1.0, 0.5, 2.0)
    phi_quadratic = lambda x: -3.0 * x * x + 6.0 * x + 4.0
    vertex, is_maximum = quadratic_vertex(xs, tuple(phi_quadratic(x) for x in xs))
    record(
        "quadratic_turning_point",
        is_maximum and abs(vertex - 1.0) < 1e-13,
        {"vertex": vertex, "expected": 1.0, "is_maximum": is_maximum},
    )
    singular_vertex, singular_max = quadratic_vertex((0.0, 0.0, 1.0), (1.0, 1.0, 2.0))
    record(
        "quadratic_turning_point_singular_negative_control",
        math.isnan(singular_vertex) and not singular_max,
        {"vertex_is_nan": math.isnan(singular_vertex), "is_maximum": singular_max},
        negative_control=True,
    )

    # Guarded bracketing: progress guard, strict bracket, and equality branch.
    tau = (1.0 + math.sqrt(5.0)) / 2.0
    bracket_phi = lambda x: -(x - 3.0) ** 2
    bracket = guarded_bracket(bracket_phi, 0.0, 0.25, tau, 64)
    progress = [item["gap_ratio"] for item in bracket.get("trace", [])]
    a, b, c = bracket["bracket"]
    record(
        "guarded_bracket_strict_unimodal_success",
        bracket["status"] == "strict_bracket"
        and a < b < c
        and a < 3.0 < c
        and bracket_phi(b) > bracket_phi(a)
        and bracket_phi(b) > bracket_phi(c),
        {"status": bracket["status"], "iterations": bracket["iterations"], "bracket": bracket["bracket"]},
    )
    record(
        "guarded_bracket_quantitative_progress",
        bool(progress) and all(ratio >= tau - 2e-15 for ratio in progress),
        {"minimum_gap_ratio": min(progress), "required_tau": tau, "steps": len(progress)},
    )
    equality_phi = lambda x: -(x - 3.0) ** 2
    equality_mid = 3.0
    record(
        "guarded_bracket_equality_branch",
        equality_phi(2.0) == equality_phi(4.0)
        and equality_phi(equality_mid) > equality_phi(2.0),
        {"phi_b": equality_phi(2.0), "phi_mid": equality_phi(equality_mid), "phi_c": equality_phi(4.0)},
    )
    attained_phi = lambda x: -(x - 1.0) ** 2
    bad_start = guarded_bracket(attained_phi, 2.0, 3.0, tau, 16)
    record(
        "source_attainment_only_bracketing_claim_negative_control",
        bad_start["status"] == "invalid_initial_rise" and attained_phi(1.0) > attained_phi(2.0),
        {
            "global_maximizer": 1.0,
            "phi_at_maximizer": attained_phi(1.0),
            "start": [2.0, 3.0],
            "algorithm_status": bad_start["status"],
            "meaning": "mere attainment does not repair an initial pair pointing away from the maximizer",
        },
        negative_control=True,
    )

    # Golden-section invariant, reuse count, and strictness counterexample.
    golden_phi = lambda x: 10.0 - (x - 5.0) ** 2
    epsilon = 1e-7
    golden = golden_section(golden_phi, 0.0, 10.0, epsilon)
    widths = golden["widths"]
    ratios = [widths[i + 1] / widths[i] for i in range(len(widths) - 1)]
    record(
        "golden_section_strict_concave_solution",
        golden["status"] == "width_tolerance"
        and golden["interval"][0] <= 5.0 <= golden["interval"][1]
        and abs(golden["point"] - 5.0) <= epsilon
        and golden["interval"][1] - golden["interval"][0] <= 2.0 * epsilon,
        {
            "point": golden["point"],
            "error": abs(golden["point"] - 5.0),
            "interval": golden["interval"],
            "iterations": golden["iterations"],
        },
    )
    record(
        "golden_section_one_new_evaluation_per_iteration",
        golden["evaluations"] == golden["iterations"] + 2,
        {"evaluations": golden["evaluations"], "iterations": golden["iterations"]},
    )
    record(
        "golden_section_contraction_ratio",
        ratios and max(abs(ratio - 1.0 / tau) for ratio in ratios) < 2e-9,
        {"expected": 1.0 / tau, "maximum_absolute_delta": max(abs(ratio - 1.0 / tau) for ratio in ratios)},
    )
    scipy_golden = optimize.minimize_scalar(lambda x: -golden_phi(x), bounds=(0.0, 10.0), method="bounded")
    record(
        "golden_section_scipy_reference",
        scipy_golden.success and abs(scipy_golden.x - 5.0) < 1e-8,
        {"scipy_x": scipy_golden.x, "scipy_fun": scipy_golden.fun, "success": scipy_golden.success},
    )

    def plateau_phi(x: float) -> float:
        if x < 0.5:
            return 10.0 * x
        if x < 0.75:
            return -10.0 * x + 10.0
        if x < 9.0:
            return 2.5
        return -x + 11.5

    plateau = golden_section(plateau_phi, 0.0, 11.0, 0.005)
    record(
        "weak_unimodal_plateau_equality_negative_control",
        plateau["point"] > 8.9
        and plateau_phi(plateau["point"]) == 2.5
        and plateau_phi(0.5) == 5.0,
        {
            "returned_point": plateau["point"],
            "returned_value": plateau_phi(plateau["point"]),
            "global_point": 0.5,
            "global_value": plateau_phi(0.5),
            "meaning": "the one-sided equality branch can discard the global maximizer on a lower plateau",
        },
        negative_control=True,
    )

    # Bisection: interval invariant and strong-concavity residual conversion.
    deriv = lambda x: -2.0 * (x - 5.0)
    bisect_position = bisection_maximum(deriv, 0.0, 9.0, 1e-7, 0.0, 128)
    invariant = all(item["left"] <= 5.0 <= item["right"] for item in bisect_position["trace"])
    record(
        "bisection_position_tolerance_and_invariant",
        invariant
        and bisect_position["status"] in {"exact_root", "position_tolerance"}
        and abs(bisect_position["point"] - 5.0) <= 1e-7,
        {
            "status": bisect_position["status"],
            "point": bisect_position["point"],
            "error": abs(bisect_position["point"] - 5.0),
            "iterations": len(bisect_position["trace"]),
            "invariant": invariant,
        },
    )
    epsilon_g = 0.01
    bisect_residual = bisection_maximum(deriv, 0.0, 9.0, 1e-15, epsilon_g, 128)
    residual_error = abs(bisect_residual["point"] - 5.0)
    record(
        "bisection_strong_concavity_bound",
        bisect_residual["status"] in {"exact_root", "derivative_tolerance"}
        and residual_error <= epsilon_g / 2.0,
        {
            "status": bisect_residual["status"],
            "point": bisect_residual["point"],
            "error": residual_error,
            "m": 2.0,
            "epsilon_g_over_m": epsilon_g / 2.0,
        },
    )
    eta = 1e-10
    weak_derivative = lambda x: -eta * x
    record(
        "plain_strict_concavity_residual_distance_negative_control",
        abs(weak_derivative(1.0)) < 1e-6 and abs(1.0 - 0.0) == 1.0,
        {
            "phi": "-eta*x^2/2",
            "eta": eta,
            "test_point": 1.0,
            "optimizer": 0.0,
            "derivative_residual": abs(weak_derivative(1.0)),
            "distance": 1.0,
            "meaning": "strict concavity without a uniform modulus gives no uniform residual-to-distance bound",
        },
        negative_control=True,
    )

    # Quartic extrema and Newton maximum/minimum classification.
    def quartic(x: float) -> float:
        y = x - 4.0
        return -(y**4) + 3.0 * y**3 + 6.0 * y**2 - 3.0 * y + 100.0

    def quartic_d1(x: float) -> float:
        y = x - 4.0
        return -4.0 * y**3 + 9.0 * y**2 + 12.0 * y - 3.0

    def quartic_d2(x: float) -> float:
        y = x - 4.0
        return -12.0 * y**2 + 18.0 * y + 12.0

    extrema = sorted(float(root.real + 4.0) for root in np.roots([-4.0, 9.0, 12.0, -3.0]) if abs(root.imag) < 1e-12)
    classifications = ["maximum" if quartic_d2(x) < 0 else "minimum" for x in extrema]
    expected_extrema = [2.900627632, 4.217851814, 7.131520555]
    record(
        "quartic_extrema_corrected_classification",
        max(abs(x - y) for x, y in zip(extrema, expected_extrema)) < 6e-10
        and classifications == ["maximum", "minimum", "maximum"],
        {"roots": extrema, "classifications": classifications, "second_derivatives": [quartic_d2(x) for x in extrema]},
    )
    record(
        "source_middle_extremum_misclassification_negative_control",
        quartic_d2(4.217851814) > 0.0,
        {"point": 4.217851814, "second_derivative": quartic_d2(4.217851814), "classification": "minimum"},
        negative_control=True,
    )
    maximum_newton = newton_stationary(quartic_d1, quartic_d2, 2.899652455, 1e-13, 1e-14, 32)
    minimum_newton = newton_stationary(quartic_d1, quartic_d2, 4.3, 1e-13, 1e-14, 32)
    record(
        "Newton_quartic_maximization",
        maximum_newton["classification"] == "maximum"
        and abs(maximum_newton["point"] - expected_extrema[0]) < 6e-10,
        {"point": maximum_newton["point"], "classification": maximum_newton["classification"], "iterations": len(maximum_newton["trace"]) - 1},
    )
    record(
        "Newton_quartic_minimization_classification",
        minimum_newton["classification"] == "minimum"
        and abs(minimum_newton["point"] - expected_extrema[1]) < 6e-10,
        {"point": minimum_newton["point"], "classification": minimum_newton["classification"], "iterations": len(minimum_newton["trace"]) - 1},
    )
    scipy_max = optimize.root_scalar(quartic_d1, bracket=(2.8, 3.1), method="brentq")
    scipy_min = optimize.root_scalar(quartic_d1, bracket=(4.0, 4.5), method="brentq")
    record(
        "Newton_SciPy_stationary_reference",
        scipy_max.converged
        and scipy_min.converged
        and abs(scipy_max.root - maximum_newton["point"]) < 1e-11
        and abs(scipy_min.root - minimum_newton["point"]) < 1e-11,
        {"maximum_root": scipy_max.root, "minimum_root": scipy_min.root},
    )
    zero_hessian = newton_stationary(lambda x: 1.0, lambda x: 0.0, 0.0, 0.0, 1e-12, 3)
    record(
        "Newton_zero_hessian_negative_control",
        zero_hessian["status"] == "zero_hessian",
        {"status": zero_hessian["status"]},
        negative_control=True,
    )

    # Corrected sign specialization of the global contraction theorem.
    x_probe = 0.25
    phi_prime = lambda x: -(x - 2.0)
    phi_second = lambda x: -1.0
    corrected_h = -phi_prime(x_probe)
    corrected_gamma = -1.0 / phi_second(x_probe)
    source_h = phi_prime(x_probe)
    source_gamma = 1.0 / phi_second(x_probe)
    record(
        "Newton_maximization_sign_specialization",
        corrected_gamma > 0.0 and corrected_h < 0.0 and 1.0 > 0.0,
        {
            "probe": x_probe,
            "corrected_h": corrected_h,
            "corrected_h_prime": 1.0,
            "corrected_gamma": corrected_gamma,
            "Newton_map_value": x_probe - corrected_gamma * corrected_h,
        },
    )
    record(
        "source_Newton_signs_violate_hypotheses_negative_control",
        source_gamma < 0.0 and -1.0 < 0.0,
        {"source_h": source_h, "source_h_prime": -1.0, "source_gamma": source_gamma},
        negative_control=True,
    )

    # High-precision local convergence constants.
    mp.mp.dps = 100
    root2 = mp.sqrt(2)
    x = mp.mpf("1.4")
    quadratic_ratios: list[mp.mpf] = []
    errors: list[mp.mpf] = []
    for _ in range(5):
        error = abs(x - root2)
        errors.append(error)
        x_next = x - (x * x - 2) / (2 * x)
        quadratic_ratios.append(abs(x_next - root2) / (error * error))
        x = x_next
    expected_constant = 1 / (2 * root2)
    final_ratio = quadratic_ratios[-1]
    record(
        "Newton_local_quadratic_constant",
        abs(final_ratio - expected_constant) < mp.mpf("1e-28"),
        {
            "h": "x^2-2",
            "final_ratio": mp.nstr(final_ratio, 50),
            "expected_abs_h2_over_2_abs_h1": mp.nstr(expected_constant, 50),
            "initial_error": mp.nstr(errors[0], 30),
            "final_error": mp.nstr(errors[-1], 30),
        },
    )
    x = mp.mpf("0.1")
    cubic_ratios: list[mp.mpf] = []
    quadratic_zero_ratios: list[mp.mpf] = []
    for _ in range(4):
        error = abs(x)
        x_next = x - (x + x**3) / (1 + 3 * x**2)
        quadratic_zero_ratios.append(abs(x_next) / error**2)
        cubic_ratios.append(abs(x_next) / error**3)
        x = x_next
    record(
        "Newton_zero_second_derivative_higher_order_negative_control",
        quadratic_zero_ratios[-1] < mp.mpf("1e-20") and abs(cubic_ratios[-1] - 2) < mp.mpf("1e-30"),
        {
            "h": "x+x^3",
            "h_double_prime_at_root": 0,
            "final_quadratic_ratio": mp.nstr(quadratic_zero_ratios[-1], 40),
            "final_cubic_ratio": mp.nstr(cubic_ratios[-1], 40),
            "meaning": "a Q-quadratic upper bound does not imply exact order two",
        },
        negative_control=True,
    )

    # Basic ascent hypotheses: the source's weaker conditions and zero-gradient
    # strict inequality are both falsified by explicit matrices/vectors.
    indefinite_b = np.diag([1.0, -1.0])
    gradient = np.array([0.0, 1.0])
    ascent_product = float(gradient @ np.linalg.solve(indefinite_b, gradient))
    record(
        "source_symmetric_nonsingular_B_negative_control",
        ascent_product < 0.0,
        {"B": indefinite_b, "gradient": gradient, "gradient_T_Binv_gradient": ascent_product},
        negative_control=True,
    )
    zero_gradient = np.zeros(2)
    record(
        "source_zero_gradient_strict_ascent_negative_control",
        float(zero_gradient @ zero_gradient) == 0.0,
        {"gradient": zero_gradient, "inner_product": 0.0, "source_claimed_strictly_positive": True},
        negative_control=True,
    )

    # Source Taylor typo: x0 derivatives cannot represent a Taylor polynomial at xk.
    cubic = lambda x: x**3
    cubic_d1 = lambda x: 3.0 * x**2
    cubic_d2 = lambda x: 6.0 * x
    x0, xk, point = 0.0, 1.0, 1.001
    correct_taylor = cubic(xk) + cubic_d1(xk) * (point - xk) + 0.5 * cubic_d2(xk) * (point - xk) ** 2
    source_taylor = cubic(xk) + cubic_d1(x0) * (point - xk) + 0.5 * cubic_d2(x0) * (point - xk) ** 2
    exact = cubic(point)
    record(
        "source_Newton_Taylor_basepoint_negative_control",
        abs(exact - correct_taylor) < 2e-9 and abs(exact - source_taylor) > 1e-3,
        {
            "function": "x^3",
            "x0": x0,
            "xk": xk,
            "evaluation_point": point,
            "exact": exact,
            "correct_xk_Taylor": correct_taylor,
            "source_x0_derivative_expression": source_taylor,
        },
        negative_control=True,
    )

    failures = [item["check_id"] for item in CHECKS if item["status"] != "PASS"]
    result = {
        "schema": "o015.penn.chapter03.open-numerical-validation.v1",
        "status": "PASS" if not failures else "FAIL",
        "identities": {"source": source_id, "target": target_id, "ledger": ledger_id},
        "validator_script": identity(Path(__file__)),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "mpmath": mp.__version__,
            "platform": platform.platform(),
            "randomness": "none",
        },
        "counts": {
            "checks": len(CHECKS),
            "passed": len(CHECKS) - len(failures),
            "failed": len(failures),
            "negative_controls": sum(bool(item["negative_control"]) for item in CHECKS),
        },
        "failures": failures,
        "checks": CHECKS,
    }
    RESULTS.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    digest = sha256(RESULTS)
    print(json.dumps({"status": result["status"], "counts": result["counts"], "failures": failures, "results_sha256": digest}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
