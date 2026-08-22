#!/usr/bin/env python3
"""Deterministic mathematical validator for the Habring Chapter 8 id-ID unit.

The validator uses only Python's standard library.  It pins the exact authority
and translated target, checks the textual surfaces on which the corrected
argument depends, and then exercises the stochastic-subgradient identities and
best-iterate estimate with exact rational arithmetic wherever possible.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Callable


QA_DIR = Path(__file__).resolve().parent
ROOT = QA_DIR.parent
AUTHORITY = ROOT / "authority" / "habring" / "source-v1" / "stochastic.tex"
TARGET = (
    ROOT
    / "source"
    / "id-ID"
    / "habring-08-penurunan-gradien-stokastik-id.tex"
)
OUTPUT = QA_DIR / "STOCHASTIC_SOLVER_RESULTS.json"

EXPECTED_AUTHORITY_SHA256 = (
    "610d11b59d8dfabbbbe6fbc509a0f9ac1727540458c67f8cd3b7bab49566a07d"
)
EXPECTED_TARGET_SHA256 = (
    "f610aaec91aa9b76582f251458da65d25cc37a933a51da478cad13ee16e5a344"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def qtext(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def qrecord(value: Fraction) -> dict[str, object]:
    return {
        "exact": qtext(value),
        "decimal": float(value),
    }


def vector_record(vector: tuple[Fraction, ...]) -> dict[str, object]:
    return {
        "exact": [qtext(value) for value in vector],
        "decimal": [float(value) for value in vector],
    }


def vector_sum(vectors: tuple[tuple[Fraction, ...], ...]) -> tuple[Fraction, ...]:
    return tuple(sum((vector[j] for vector in vectors), Fraction(0)) for j in range(len(vectors[0])))


def vector_scale(scale: Fraction, vector: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    return tuple(scale * value for value in vector)


def project_interval(value: Fraction, lower: Fraction, upper: Fraction) -> Fraction:
    return min(upper, max(lower, value))


def sign_subgradient(value: Fraction) -> Fraction:
    if value > 0:
        return Fraction(1)
    if value < 0:
        return Fraction(-1)
    return Fraction(0)


def harmonic_step(k: int) -> Fraction:
    return Fraction(1, k + 1)


def shifted_harmonic_step(k: int) -> Fraction:
    return Fraction(2, k + 2)


def exact_best_iterate_case(
    schedule_name: str,
    schedule: Callable[[int], Fraction],
    K: int,
) -> dict[str, object]:
    """Enumerate the two-point oracle exactly through x_{K-1}."""

    lower = Fraction(-1)
    upper = Fraction(1)
    x0 = Fraction(1)
    noise_values = (Fraction(-1, 2), Fraction(1, 2))
    noise_probability = Fraction(1, 2)
    sigma2 = Fraction(1, 4)
    lipschitz2 = Fraction(1)
    moment_bound = sigma2 + lipschitz2

    # State is (current iterate, best objective value through current iterate).
    states: dict[tuple[Fraction, Fraction], Fraction] = {
        (x0, abs(x0)): Fraction(1)
    }
    expected_gaps: list[Fraction] = []

    for k in range(K):
        expected_gap = sum(
            (probability * abs(x) for (x, _best), probability in states.items()),
            Fraction(0),
        )
        expected_gaps.append(expected_gap)
        if k == K - 1:
            break

        tau = schedule(k)
        next_states: dict[tuple[Fraction, Fraction], Fraction] = {}
        for (x, best), probability in states.items():
            conditional_mean = sign_subgradient(x)
            for noise in noise_values:
                oracle = conditional_mean + noise
                next_x = project_interval(x - tau * oracle, lower, upper)
                next_best = min(best, abs(next_x))
                key = (next_x, next_best)
                next_states[key] = next_states.get(key, Fraction(0)) + probability * noise_probability
        states = next_states

    expected_best = sum(
        (probability * best for (_x, best), probability in states.items()),
        Fraction(0),
    )
    steps = [schedule(k) for k in range(K)]
    S_K = sum(steps, Fraction(0))
    Q_K = sum((tau * tau for tau in steps), Fraction(0))
    weighted_expected_gap = sum(
        (steps[k] * expected_gaps[k] for k in range(K)), Fraction(0)
    ) / S_K
    theorem_bound = (x0 * x0 + moment_bound * Q_K) / (2 * S_K)

    passed = (
        sum(states.values(), Fraction(0)) == 1
        and expected_best <= weighted_expected_gap
        and weighted_expected_gap <= theorem_bound
    )
    return {
        "schedule": schedule_name,
        "K": K,
        "terminal_state_count": len(states),
        "probability_mass": qrecord(sum(states.values(), Fraction(0))),
        "S_K": qrecord(S_K),
        "Q_K": qrecord(Q_K),
        "Q_K_over_S_K": qrecord(Q_K / S_K),
        "expected_best_gap": qrecord(expected_best),
        "weighted_expected_gap": qrecord(weighted_expected_gap),
        "theorem_bound": qrecord(theorem_bound),
        "bound_margin": qrecord(theorem_bound - expected_best),
        "passed": passed,
    }


def main() -> int:
    authority_bytes = AUTHORITY.read_bytes()
    target_bytes = TARGET.read_bytes()
    authority_text = authority_bytes.decode("utf-8")
    target_text = target_bytes.decode("utf-8")

    gates: list[dict[str, object]] = []

    def gate(identifier: str, passed: bool, detail: str) -> None:
        gates.append({"id": identifier, "passed": bool(passed), "detail": detail})

    authority_sha = sha256(authority_bytes)
    target_sha = sha256(target_bytes)
    gate(
        "surface.authority.sha256",
        authority_sha == EXPECTED_AUTHORITY_SHA256,
        authority_sha,
    )
    gate(
        "surface.target.sha256",
        target_sha == EXPECTED_TARGET_SHA256,
        target_sha,
    )

    authority_surfaces = {
        "unnormalized_finite_sum": r"\min_x f(x)\coloneqq \sum_{i=1}^N f_i(x)",
        "unscaled_component_oracle": r"G(x,z) \coloneqq \nabla f_z(x)",
        "extra_Q_K_term": r"\frac{(\sigma^2 + L^2)\sum_{k=0}^{K-1}\tau_k^2}{\sigma_n}",
    }
    for name, surface in authority_surfaces.items():
        gate(
            f"surface.authority.{name}",
            surface in authority_text,
            "required authority defect witness present",
        )

    target_surfaces = {
        "normalized_finite_sum": r"\min_x f(x)\coloneqq \frac{1}{N}\sum_{i=1}^N f_i(x)",
        "normalized_unbiased_identity": r"\E[G(x,Z)]=N^{-1}\sum_{i=1}^N\nabla f_i(x)=\nabla f(x)",
        "closed_convex_constraint": r"C\subseteq\R^d$ tak kosong, tertutup, dan konveks",
        "projected_iteration": r"x_{k+1}=\proj_C(x_k-\tau_kG_k)",
        "filtration": r"\mathcal F_k=\sigma(x_0,Z_0,\dots,Z_{k-1})",
        "conditional_mean": r"\bar g_k\coloneqq\E[G_k\mid\mathcal F_k]",
        "conditional_variance": r"\E[\|G_k-\bar g_k\|^2\mid\mathcal F_k]\leq \sigma^2<\infty",
        "best_iterate": r"f_{\mathrm{best}}^K\coloneqq\min_{0\leq k\leq K-1}f(x_k)",
        "S_K": r"S_K\coloneqq\sum_{k=0}^{K-1}\tau_k",
        "Q_K": r"Q_K\coloneqq\sum_{k=0}^{K-1}\tau_k^2",
        "correct_variance_term": r"\frac{M^2Q_K}{2S_K}",
    }
    for name, surface in target_surfaces.items():
        gate(
            f"surface.target.{name}",
            surface in target_text,
            "required corrected target surface present",
        )
    gate(
        "surface.target.segment_markers",
        target_text.count("% segment-id: d90.hab.v1.ch08.seg") == 3,
        f"count={target_text.count('% segment-id: d90.hab.v1.ch08.seg')}",
    )
    gate(
        "surface.target.excludes_extra_Q_K_algebra",
        authority_surfaces["extra_Q_K_term"] not in target_text,
        "authority's erroneous extra-Q_K term absent",
    )

    # Exact finite-sum unbiasedness check in R^2.
    component_gradients = (
        (Fraction(1), Fraction(3)),
        (Fraction(-2), Fraction(5)),
        (Fraction(7), Fraction(-1)),
        (Fraction(2), Fraction(-3)),
    )
    N = len(component_gradients)
    gradient_sum = vector_sum(component_gradients)
    uniform_oracle_mean = vector_scale(Fraction(1, N), gradient_sum)
    normalized_objective_gradient = vector_scale(Fraction(1, N), gradient_sum)
    scaled_sum_oracle_mean = vector_scale(Fraction(N), uniform_oracle_mean)
    normalized_unbiased = uniform_oracle_mean == normalized_objective_gradient
    missing_factor_detected = (
        uniform_oracle_mean != gradient_sum
        and scaled_sum_oracle_mean == gradient_sum
    )
    gate(
        "math.finite_sum.normalized_unbiasedness",
        normalized_unbiased,
        f"mean={uniform_oracle_mean}, normalized gradient={normalized_objective_gradient}",
    )
    gate(
        "negative_control.finite_sum.missing_factor_N",
        missing_factor_detected,
        f"naive mean={uniform_oracle_mean}, sum gradient={gradient_sum}, N={N}",
    )

    # Conditional oracle checks for f(x)=|x| with epsilon in {-1/2,+1/2}.
    conditional_cases: list[dict[str, object]] = []
    conditional_pass = True
    for state_name, x in (
        ("positive_state", Fraction(2)),
        ("negative_state", Fraction(-3)),
        ("origin_state", Fraction(0)),
    ):
        g = sign_subgradient(x)
        outputs = (g - Fraction(1, 2), g + Fraction(1, 2))
        mean = sum(outputs, Fraction(0)) / 2
        variance = sum(((value - mean) ** 2 for value in outputs), Fraction(0)) / 2
        second_moment = sum((value * value for value in outputs), Fraction(0)) / 2
        identity_rhs = variance + mean * mean
        subgradient_valid = (g == sign_subgradient(x)) and (x != 0 or abs(g) <= 1)
        case_pass = (
            mean == g
            and variance == Fraction(1, 4)
            and second_moment == identity_rhs
            and second_moment <= Fraction(5, 4)
            and subgradient_valid
        )
        conditional_pass = conditional_pass and case_pass
        conditional_cases.append(
            {
                "state": state_name,
                "x": qrecord(x),
                "oracle_outputs": [qrecord(value) for value in outputs],
                "conditional_mean": qrecord(mean),
                "conditional_variance": qrecord(variance),
                "conditional_second_moment": qrecord(second_moment),
                "variance_plus_mean_squared": qrecord(identity_rhs),
                "mean_is_subgradient": subgradient_valid,
                "passed": case_pass,
            }
        )
    gate(
        "math.conditional_mean_variance_second_moment",
        conditional_pass,
        "three filtration states enumerated exactly",
    )

    # Projection and one-step recurrence, with one active projection branch.
    x = Fraction(4, 5)
    x_star = Fraction(0)
    tau = Fraction(3, 2)
    oracle_outputs = (Fraction(1, 2), Fraction(3, 2))
    outcome_records: list[dict[str, object]] = []
    projection_pass = True
    expected_projected_distance = Fraction(0)
    expected_unprojected_distance = Fraction(0)
    for oracle in oracle_outputs:
        unprojected = x - tau * oracle
        projected = project_interval(unprojected, Fraction(-1), Fraction(1))
        projected_distance = (projected - x_star) ** 2
        unprojected_distance = (unprojected - x_star) ** 2
        expanded_distance = (
            (x - x_star) ** 2
            - 2 * tau * (x - x_star) * oracle
            + tau * tau * oracle * oracle
        )
        outcome_pass = (
            unprojected_distance == expanded_distance
            and projected_distance <= unprojected_distance
        )
        projection_pass = projection_pass and outcome_pass
        expected_projected_distance += projected_distance / 2
        expected_unprojected_distance += unprojected_distance / 2
        outcome_records.append(
            {
                "oracle": qrecord(oracle),
                "unprojected_iterate": qrecord(unprojected),
                "projected_iterate": qrecord(projected),
                "projected_distance_squared": qrecord(projected_distance),
                "unprojected_distance_squared": qrecord(unprojected_distance),
                "expanded_distance_squared": qrecord(expanded_distance),
                "passed": outcome_pass,
            }
        )
    recurrence_rhs = (
        (x - x_star) ** 2
        - 2 * tau * (abs(x) - abs(x_star))
        + tau * tau * Fraction(5, 4)
    )
    recurrence_pass = (
        projection_pass
        and expected_unprojected_distance == recurrence_rhs
        and expected_projected_distance <= recurrence_rhs
    )
    gate(
        "math.projection_and_one_step_recurrence",
        recurrence_pass,
        f"projected E[D+]={qtext(expected_projected_distance)}, rhs={qtext(recurrence_rhs)}",
    )

    # Exact best-iterate verification for two schedules and several horizons.
    best_iterate_cases: list[dict[str, object]] = []
    for schedule_name, schedule in (
        ("harmonic_1_over_k_plus_1", harmonic_step),
        ("shifted_harmonic_2_over_k_plus_2", shifted_harmonic_step),
    ):
        for K in (1, 2, 4, 8, 12):
            best_iterate_cases.append(exact_best_iterate_case(schedule_name, schedule, K))
    best_iterate_pass = all(case["passed"] for case in best_iterate_cases)
    gate(
        "math.projected_stochastic_best_iterate_bound",
        best_iterate_pass,
        f"exact cases={len(best_iterate_cases)}",
    )

    # The authority's extra Q_K changes Q_K/S_K into Q_K^2/S_K.
    # For tau_k=(k+1)^(-1/5), the correct term decays like K^(-1/5),
    # whereas the erroneous term grows like K^(2/5).
    alpha = Fraction(1, 5)
    S_exponent = 1 - alpha
    Q_exponent = 1 - 2 * alpha
    correct_exponent = Q_exponent - S_exponent
    erroneous_exponent = 2 * Q_exponent - S_exponent
    asymptotic_negative_control = correct_exponent < 0 < erroneous_exponent

    extra_Q_numeric: list[dict[str, object]] = []
    for K in (100, 1_000, 10_000, 100_000):
        S = math.fsum((k ** -0.2 for k in range(1, K + 1)))
        Q = math.fsum((k ** -0.4 for k in range(1, K + 1)))
        extra_Q_numeric.append(
            {
                "K": K,
                "S_K": S,
                "Q_K": Q,
                "correct_Q_K_over_S_K": Q / S,
                "erroneous_Q_K_squared_over_S_K": Q * Q / S,
            }
        )
    numeric_negative_control = (
        extra_Q_numeric[-1]["correct_Q_K_over_S_K"]
        < extra_Q_numeric[0]["correct_Q_K_over_S_K"]
        and extra_Q_numeric[-1]["erroneous_Q_K_squared_over_S_K"]
        > extra_Q_numeric[0]["erroneous_Q_K_squared_over_S_K"]
    )
    gate(
        "negative_control.source_extra_Q_K_convergence",
        asymptotic_negative_control and numeric_negative_control,
        "correct exponent=-1/5; erroneous exponent=2/5",
    )

    passed = all(item["passed"] for item in gates)
    result = {
        "schema": "d90.stochastic-validator.v1",
        "status": "PASS" if passed else "FAIL",
        "deterministic": True,
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
            "exact_best_iterate_case_count": len(best_iterate_cases),
        },
        "gates": gates,
        "finite_sum_unbiasedness": {
            "N": N,
            "component_gradients": [vector_record(vector) for vector in component_gradients],
            "uniform_component_oracle_mean": vector_record(uniform_oracle_mean),
            "normalized_objective_gradient": vector_record(normalized_objective_gradient),
            "unnormalized_sum_gradient": vector_record(gradient_sum),
            "N_scaled_oracle_mean": vector_record(scaled_sum_oracle_mean),
            "normalized_unbiasedness_passed": normalized_unbiased,
            "missing_factor_negative_control_detected": missing_factor_detected,
        },
        "conditional_oracle": {
            "function": "f(x)=abs(x)",
            "L_squared": qrecord(Fraction(1)),
            "sigma_squared": qrecord(Fraction(1, 4)),
            "M_squared": qrecord(Fraction(5, 4)),
            "cases": conditional_cases,
        },
        "projection_one_step": {
            "constraint": "[-1,1]",
            "x_k": qrecord(x),
            "x_star": qrecord(x_star),
            "tau_k": qrecord(tau),
            "outcomes": outcome_records,
            "expected_projected_distance_squared": qrecord(expected_projected_distance),
            "expected_unprojected_distance_squared": qrecord(expected_unprojected_distance),
            "recurrence_rhs": qrecord(recurrence_rhs),
            "recurrence_margin": qrecord(recurrence_rhs - expected_projected_distance),
            "passed": recurrence_pass,
        },
        "best_iterate_bound": {
            "model": "f(x)=abs(x), C=[-1,1], x0=1, epsilon=+-1/2 uniformly",
            "cases": best_iterate_cases,
            "passed": best_iterate_pass,
        },
        "extra_Q_K_negative_control": {
            "schedule": "tau_k=(k+1)^(-1/5)",
            "S_K_asymptotic_exponent": qtext(S_exponent),
            "Q_K_asymptotic_exponent": qtext(Q_exponent),
            "correct_Q_K_over_S_K_exponent": qtext(correct_exponent),
            "erroneous_Q_K_squared_over_S_K_exponent": qtext(erroneous_exponent),
            "numeric_witnesses": extra_Q_numeric,
            "passed": asymptotic_negative_control and numeric_negative_control,
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
