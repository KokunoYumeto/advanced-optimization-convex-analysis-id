#!/usr/bin/env python3
"""Deterministic mathematical and computational QA for Original 01.

The validator reads the live chapter, lab, and frozen lab outputs.  It never
invokes the lab's writing ``main`` function: the experiment is replayed in
memory so validation cannot mutate the learner-facing artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import itertools
import json
import math
import os
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Sequence


sys.dont_write_bytecode = True

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
SOURCE = (
    ROOT
    / "source"
    / "id-ID"
    / "original-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
)
LAB = ROOT / "labs" / "original-01" / "stochastic-composite-lab.py"
RESULT_JSON = ROOT / "labs" / "original-01" / "results.json"
RESULT_CSV = ROOT / "labs" / "original-01" / "results.csv"
RESULT_SVG = ROOT / "labs" / "original-01" / "objective-gap.svg"
VALIDATOR = Path(__file__).resolve()
REPORT = ROOT / "qa" / "ORIGINAL_01_MATH_VALIDATION.json"

EXPECTED_OUTPUT_IDENTITIES = {
    "results.json": {
        "bytes": 2432,
        "sha256": "86ff701a51d091ee74c110917cb1888c6e7448489207e6ee1372753bd1e4c447",
    },
    "results.csv": {
        "bytes": 4189,
        "sha256": "61a6591ad7d1b41230a086482314448871f3697954d4c84133a7a5f4f775d37c",
    },
    "objective-gap.svg": {
        "bytes": 86616,
        "sha256": "87c772d901ee734356981ee35f19fc3c3ae47fea6f11528edbee6d015a3f2830",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
        "sha256": sha256_bytes(data),
    }


def fraction_vector(values: Iterable[int | Fraction]) -> tuple[Fraction, ...]:
    return tuple(Fraction(value) for value in values)


def vector_add(
    left: Sequence[Fraction], right: Sequence[Fraction]
) -> tuple[Fraction, ...]:
    return tuple(a + b for a, b in zip(left, right))


def vector_scale(
    scalar: Fraction, vector: Sequence[Fraction]
) -> tuple[Fraction, ...]:
    return tuple(scalar * value for value in vector)


def vector_mean(vectors: Sequence[Sequence[Fraction]]) -> tuple[Fraction, ...]:
    count = Fraction(len(vectors))
    total = tuple(Fraction() for _ in vectors[0])
    for vector in vectors:
        total = vector_add(total, vector)
    return vector_scale(Fraction(1, count), total)


def dot(left: Sequence[Fraction], right: Sequence[Fraction]) -> Fraction:
    return sum((a * b for a, b in zip(left, right)), Fraction())


def squared_norm(vector: Sequence[Fraction]) -> Fraction:
    return dot(vector, vector)


def soft_fraction(value: Fraction, threshold: Fraction) -> Fraction:
    if value > threshold:
        return value - threshold
    if value < -threshold:
        return value + threshold
    return Fraction()


gates: list[dict[str, Any]] = []


def record(name: str, passed: bool, details: dict[str, Any]) -> None:
    gates.append({"gate": name, "pass": bool(passed), "details": details})


required_files = [SOURCE, LAB, RESULT_JSON, RESULT_CSV, RESULT_SVG]
missing_files = [
    path.relative_to(ROOT).as_posix() for path in required_files if not path.is_file()
]
if missing_files:
    raise FileNotFoundError(
        "Missing Original-01 validation inputs: " + ", ".join(missing_files)
    )

initial_input_identities = {path.name: file_identity(path) for path in required_files}
source_text = SOURCE.read_text(encoding="utf-8")
lab_text = LAB.read_text(encoding="utf-8")

required_source_surfaces = {
    "stochastic_proximal_one_step": r"\label{orig01:eq:spg-one-step}",
    "ergodic_proximal_rate": r"\label{orig01:eq:spg-ergodic-rate}",
    "proximal_tuning_domain": r"$R=\norm{x_0-x^*}>0$, $\sigma>0$",
    "iid_minibatch": r"\label{orig01:eq:minibatch}",
    "finite_population": r"\frac{N-b}{b(N-1)}V_N",
    "finite_population_domain": r"Andaikan $N\geq2$ dan $1\leq b\leq N$",
    "bregman_definition": r"\label{orig01:eq:bregman}",
    "mirror_one_step": r"\label{orig01:eq:mirror-one-step}",
    "mirror_rate": r"\label{orig01:eq:mirror-rate}",
    "mirror_horizon_domain": r"untuk $K\geq1$ definisikan",
    "mirror_well_posedness": r"hampir pasti mencapai peminim",
    "mirror_finite_comparator": r"D_h(x^*,x_0)<\infty",
    "entropy_update": r"\label{orig01:eq:exponentiated-update}",
    "entropy_boundary_convention": r"$0\log0=0$",
    "saga_estimator": r"v_k=\nabla f_{J_k}(x_k)-g_{J_k}^k+\bar g_k",
    "saga_unbiasedness": r"\E[v_k\mid\mathcal F_k]=\nabla f(x_k)",
    "prox_saga_bridge": r"\label{orig01:eq:prox-saga-bridge}",
    "lab_objective": r"\label{orig01:eq:lab-objective}",
}
missing_source_surfaces = [
    name for name, fragment in required_source_surfaces.items() if fragment not in source_text
]
record(
    "live_chapter_claim_surfaces",
    not missing_source_surfaces,
    {
        "required_count": len(required_source_surfaces),
        "missing": missing_source_surfaces,
    },
)

required_lab_surfaces = {
    "frozen_seed": "SEED = 20260825",
    "frozen_samples": "N = 320",
    "frozen_dimension": "D = 40",
    "frozen_lambda": "LAMBDA = 0.03",
    "frozen_epochs": "EPOCHS = 12",
    "frozen_batch": "BATCH_SIZE = 16",
    "soft_threshold": "def soft_threshold(",
    "reference_fista": "def reference_fista(",
    "sgd": "def run_prox_sgd(",
    "minibatch": "def run_prox_minibatch(",
    "prox_saga": "def run_prox_saga(",
    "saga_old_table_estimator": "estimate = fresh - table[i] + table_mean",
    "saga_table_replacement": "table[i] = fresh",
    "saga_mean_update": "table_mean += (fresh - old) / N",
}
missing_lab_surfaces = [
    name for name, fragment in required_lab_surfaces.items() if fragment not in lab_text
]
record(
    "live_lab_algorithm_surfaces",
    not missing_lab_surfaces,
    {"required_count": len(required_lab_surfaces), "missing": missing_lab_surfaces},
)


# Exact scalar composite-quadratic witnesses for the stochastic proximal
# one-step inequality.  The oracle laws are finite and enumerated exactly.
proximal_cases = [
    {
        "name": "asymmetric_noise_and_l1",
        "q": Fraction(2),
        "center": Fraction(-1, 2),
        "lambda": Fraction(1, 3),
        "xk": Fraction(5, 4),
        "tau": Fraction(1, 5),
        "noise": ((Fraction(-2), Fraction(1, 3)), (Fraction(1), Fraction(2, 3))),
        "comparators": (Fraction(-1, 3), Fraction(), Fraction(7, 6)),
    },
    {
        "name": "threshold_crossing",
        "q": Fraction(1, 2),
        "center": Fraction(3),
        "lambda": Fraction(5, 4),
        "xk": Fraction(-1),
        "tau": Fraction(3, 4),
        "noise": ((Fraction(-3, 2), Fraction(1, 2)), (Fraction(3, 2), Fraction(1, 2))),
        "comparators": (Fraction(1, 2), Fraction(), Fraction(-2)),
    },
    {
        "name": "smooth_quadratic",
        "q": Fraction(3, 2),
        "center": Fraction(-4, 3),
        "lambda": Fraction(),
        "xk": Fraction(2, 3),
        "tau": Fraction(1, 4),
        "noise": ((Fraction(-1), Fraction(2, 3)), (Fraction(2), Fraction(1, 3))),
        "comparators": (Fraction(-4, 3), Fraction(1, 5), Fraction(2)),
    },
]
proximal_details: list[dict[str, Any]] = []
proximal_ok = True
for case in proximal_cases:
    q = case["q"]
    center = case["center"]
    regularization = case["lambda"]
    xk = case["xk"]
    tau = case["tau"]
    noise = case["noise"]

    def scalar_objective(value: Fraction) -> Fraction:
        return q * (value - center) ** 2 / 2 + regularization * abs(value)

    gradient = q * (xk - center)
    probability_sum = sum((probability for _, probability in noise), Fraction())
    mean_noise = sum((value * probability for value, probability in noise), Fraction())
    variance = sum((value * value * probability for value, probability in noise), Fraction())
    outcomes = [
        (
            soft_fraction(
                xk - tau * (gradient + deviation), tau * regularization
            ),
            probability,
        )
        for deviation, probability in noise
    ]
    slacks: list[Fraction] = []
    for comparator in case["comparators"]:
        lhs = sum(
            (
                probability
                * (scalar_objective(outcome) - scalar_objective(comparator))
                for outcome, probability in outcomes
            ),
            Fraction(),
        )
        expected_distance = sum(
            (probability * (outcome - comparator) ** 2 for outcome, probability in outcomes),
            Fraction(),
        )
        rhs = (
            (xk - comparator) ** 2 - expected_distance
        ) / (2 * tau) + tau * variance
        slacks.append(rhs - lhs)
    case_ok = (
        probability_sum == 1
        and mean_noise == 0
        and 2 * q * tau <= 1
        and all(slack >= 0 for slack in slacks)
    )
    proximal_ok = proximal_ok and case_ok
    proximal_details.append(
        {
            "case": case["name"],
            "L": str(q),
            "tau": str(tau),
            "variance": str(variance),
            "outcomes": [str(value) for value, _ in outcomes],
            "inequality_slacks": [str(value) for value in slacks],
        }
    )
record(
    "stochastic_proximal_one_step_exact",
    proximal_ok,
    {
        "arithmetic": "fractions.Fraction",
        "case_count": len(proximal_cases),
        "cases": proximal_details,
    },
)


# IID minibatch variance is enumerated over every ordered batch.
iid_population = (
    fraction_vector((1, 2)),
    fraction_vector((-1, 0)),
    fraction_vector((2, -2)),
    fraction_vector((-2, 0)),
)
iid_mean = vector_mean(iid_population)
iid_variance = sum(
    (squared_norm(vector) for vector in iid_population), Fraction()
) / len(iid_population)
iid_details: list[dict[str, Any]] = []
iid_ok = iid_mean == fraction_vector((0, 0))
for batch_size in range(1, 5):
    batches = list(itertools.product(iid_population, repeat=batch_size))
    empirical = sum(
        (squared_norm(vector_mean(batch)) for batch in batches), Fraction()
    ) / len(batches)
    expected = iid_variance / batch_size
    iid_ok = iid_ok and empirical == expected
    iid_details.append(
        {
            "batch_size": batch_size,
            "ordered_batches": len(batches),
            "enumerated_variance": str(empirical),
            "sigma_squared_over_b": str(expected),
        }
    )
record(
    "iid_minibatch_variance_one_over_b_exact",
    iid_ok,
    {"single_sample_variance": str(iid_variance), "checks": iid_details},
)


# Without-replacement batches are enumerated over every subset for all b.
finite_population = (
    fraction_vector((2, -1)),
    fraction_vector((-1, 3)),
    fraction_vector((0, -2)),
    fraction_vector((4, 1)),
    fraction_vector((-5, -1)),
)
finite_mean = vector_mean(finite_population)
population_variance = sum(
    (squared_norm(vector) for vector in finite_population), Fraction()
) / len(finite_population)
finite_details: list[dict[str, Any]] = []
finite_ok = finite_mean == fraction_vector((0, 0))
population_size = len(finite_population)
for batch_size in range(1, population_size + 1):
    subsets = list(itertools.combinations(finite_population, batch_size))
    enumerated = sum(
        (squared_norm(vector_mean(subset)) for subset in subsets), Fraction()
    ) / len(subsets)
    correction = (
        Fraction(population_size - batch_size, batch_size * (population_size - 1))
        * population_variance
    )
    finite_ok = finite_ok and enumerated == correction
    finite_details.append(
        {
            "batch_size": batch_size,
            "subsets": len(subsets),
            "enumerated_variance": str(enumerated),
            "finite_population_formula": str(correction),
        }
    )
record(
    "finite_population_correction_exact",
    finite_ok,
    {
        "N": population_size,
        "V_N": str(population_variance),
        "checks": finite_details,
    },
)


# Exact Bregman three-point identity for a non-diagonal positive-definite
# quadratic generator, plus the Euclidean mirror one-step inequality.
hessian = (
    fraction_vector((2, 1)),
    fraction_vector((1, 3)),
)


def matvec(
    matrix: Sequence[Sequence[Fraction]], vector: Sequence[Fraction]
) -> tuple[Fraction, ...]:
    return tuple(dot(row, vector) for row in matrix)


def generator(value: Sequence[Fraction]) -> Fraction:
    return dot(value, matvec(hessian, value)) / 2


def generator_gradient(value: Sequence[Fraction]) -> tuple[Fraction, ...]:
    return matvec(hessian, value)


def bregman(
    first: Sequence[Fraction], second: Sequence[Fraction]
) -> Fraction:
    displacement = tuple(a - b for a, b in zip(first, second))
    return generator(first) - generator(second) - dot(
        generator_gradient(second), displacement
    )


bregman_x = fraction_vector((3, -2))
bregman_y = fraction_vector((1, 4))
bregman_z = fraction_vector((-2, 1))
gradient_difference = tuple(
    a - b
    for a, b in zip(generator_gradient(bregman_y), generator_gradient(bregman_z))
)
three_point_left = dot(
    gradient_difference,
    tuple(a - b for a, b in zip(bregman_x, bregman_y)),
)
three_point_right = (
    bregman(bregman_x, bregman_z)
    - bregman(bregman_x, bregman_y)
    - bregman(bregman_y, bregman_z)
)

mirror_x = fraction_vector((-1, 2))
mirror_xk = fraction_vector((3, -1))
mirror_gradient = fraction_vector((2, -3))
mirror_tau = Fraction(2, 5)
mirror_next = tuple(
    value - mirror_tau * gradient
    for value, gradient in zip(mirror_xk, mirror_gradient)
)


def euclidean_bregman(
    first: Sequence[Fraction], second: Sequence[Fraction]
) -> Fraction:
    return squared_norm(tuple(a - b for a, b in zip(first, second))) / 2


mirror_left = mirror_tau * dot(
    mirror_gradient,
    tuple(a - b for a, b in zip(mirror_xk, mirror_x)),
)
mirror_right = (
    euclidean_bregman(mirror_x, mirror_xk)
    - euclidean_bregman(mirror_x, mirror_next)
    + mirror_tau**2 * squared_norm(mirror_gradient) / 2
)
record(
    "bregman_three_point_and_mirror_step_exact",
    three_point_left == three_point_right and mirror_left <= mirror_right,
    {
        "three_point_left": str(three_point_left),
        "three_point_right": str(three_point_right),
        "euclidean_mirror_left": str(mirror_left),
        "euclidean_mirror_right": str(mirror_right),
    },
)


# Exponentiated-gradient update on an interior simplex.  The log-domain
# implementation is algebraically identical to the displayed formula and
# also checks the KKT constant shared by every coordinate.
simplex = np.array([0.1, 0.2, 0.3, 0.4], dtype=float)
entropy_gradient = np.array([1.5, -2.0, 0.25, 4.0], dtype=float)
entropy_tau = 0.7
log_weights = np.log(simplex) - entropy_tau * entropy_gradient
log_weights -= float(np.max(log_weights))
entropy_next = np.exp(log_weights)
entropy_next /= float(np.sum(entropy_next))
kkt_values = entropy_tau * entropy_gradient + np.log(entropy_next / simplex)
entropy_ok = (
    bool(np.all(np.isfinite(entropy_next)))
    and bool(np.all(entropy_next > 0.0))
    and math.isclose(float(np.sum(entropy_next)), 1.0, rel_tol=0.0, abs_tol=2e-15)
    and float(np.max(kkt_values) - np.min(kkt_values)) <= 2e-14
)
record(
    "entropy_simplex_update_normalization_and_positivity",
    entropy_ok,
    {
        "input_sum": float(np.sum(simplex)),
        "output": [float(value) for value in entropy_next],
        "output_sum": float(np.sum(entropy_next)),
        "minimum_coordinate": float(np.min(entropy_next)),
        "kkt_constant_spread": float(np.max(kkt_values) - np.min(kkt_values)),
    },
)


# Arithmetic in the tuned theorem bounds and their variance-series corollary.
prox_R = 3.0
prox_sigma = 2.0
prox_b = 8
prox_K = 16
prox_tau = prox_R * math.sqrt(prox_b / (2.0 * prox_sigma**2 * prox_K))
prox_distance_term = prox_R**2 / (2.0 * prox_tau * prox_K)
prox_variance_term = prox_tau * prox_sigma**2 / prox_b
prox_claimed = math.sqrt(2.0) * prox_R * prox_sigma / math.sqrt(prox_b * prox_K)

mirror_alpha = 2.0
mirror_distance = 4.0
mirror_M = 2.0
mirror_K = 4
mirror_tuned_tau = math.sqrt(
    2.0 * mirror_alpha * mirror_distance / (mirror_M**2 * mirror_K)
)
mirror_bound = mirror_distance / (mirror_K * mirror_tuned_tau) + (
    mirror_M**2 * mirror_tuned_tau / (2.0 * mirror_alpha)
)
mirror_claimed = mirror_M * math.sqrt(
    2.0 * mirror_distance / (mirror_alpha * mirror_K)
)

oracle_budget = 128
oracle_values = [
    math.sqrt(2.0) * prox_R * prox_sigma / math.sqrt(b * (oracle_budget // b))
    for b in (1, 2, 4, 8, 16)
]
geometric_C = Fraction(5)
geometric_rho = Fraction(2, 3)
geometric_K = 6
finite_geometric_sum = sum(
    (geometric_C * geometric_rho**k for k in range(geometric_K)), Fraction()
)
geometric_upper_bound = geometric_C / (1 - geometric_rho)
theorem_arithmetic_ok = (
    math.isclose(prox_distance_term, prox_variance_term, rel_tol=0.0, abs_tol=1e-15)
    and math.isclose(
        prox_distance_term + prox_variance_term,
        prox_claimed,
        rel_tol=0.0,
        abs_tol=1e-15,
    )
    and math.isclose(mirror_bound, mirror_claimed, rel_tol=0.0, abs_tol=1e-15)
    and max(oracle_values) - min(oracle_values) <= 1e-15
    and finite_geometric_sum <= geometric_upper_bound
)
record(
    "theorem_bound_arithmetic",
    theorem_arithmetic_ok,
    {
        "proximal": {
            "tau": prox_tau,
            "distance_term": prox_distance_term,
            "variance_term": prox_variance_term,
            "sum": prox_distance_term + prox_variance_term,
            "claimed_tuned_bound": prox_claimed,
        },
        "mirror": {
            "tau": mirror_tuned_tau,
            "evaluated_bound": mirror_bound,
            "claimed_tuned_bound": mirror_claimed,
        },
        "fixed_oracle_budget_values": oracle_values,
        "finite_geometric_sum": str(finite_geometric_sum),
        "infinite_geometric_upper_bound": str(geometric_upper_bound),
    },
)


# Static exact SAGA estimator expectation/variance identity for an arbitrary
# current-gradient vector and an arbitrary old table.
saga_gradients = tuple(
    Fraction(value) for value in (Fraction(5, 2), Fraction(-1, 3), Fraction(7, 4), 4)
)
saga_table = tuple(
    Fraction(value) for value in (-1, 2, Fraction(1, 2), Fraction(5, 3))
)
saga_full_gradient = sum(saga_gradients, Fraction()) / len(saga_gradients)
saga_table_mean = sum(saga_table, Fraction()) / len(saga_table)
saga_estimators = tuple(
    current - old + saga_table_mean
    for current, old in zip(saga_gradients, saga_table)
)
saga_estimator_mean = sum(saga_estimators, Fraction()) / len(saga_estimators)
saga_differences = tuple(
    current - old for current, old in zip(saga_gradients, saga_table)
)
saga_difference_mean = sum(saga_differences, Fraction()) / len(saga_differences)
saga_direct_variance = sum(
    ((value - saga_full_gradient) ** 2 for value in saga_estimators), Fraction()
) / len(saga_estimators)
saga_identity_variance = sum(
    ((value - saga_difference_mean) ** 2 for value in saga_differences), Fraction()
) / len(saga_differences)
record(
    "prox_saga_estimator_unbiasedness_exact",
    saga_estimator_mean == saga_full_gradient
    and saga_direct_variance == saga_identity_variance,
    {
        "component_estimators": [str(value) for value in saga_estimators],
        "full_gradient": str(saga_full_gradient),
        "estimator_mean": str(saga_estimator_mean),
        "direct_variance": str(saga_direct_variance),
        "centered_difference_variance": str(saga_identity_variance),
    },
)


# Enumerate all 3^4 sampled-index paths for a scalar composite quadratic.
# This is an exact finite witness of the stated Prox-SAGA variance-sum bridge.
saga_a = (Fraction(1), Fraction(2), Fraction(3))
saga_centers = (Fraction(-1), Fraction(1, 2), Fraction(2))
saga_lambda = Fraction(1, 7)
saga_x0 = Fraction(3, 2)
saga_tau = Fraction(1, 5)
saga_horizon = 4
saga_N = len(saga_a)
saga_L = sum(saga_a, Fraction()) / saga_N


def component_quadratic_gradient(index: int, value: Fraction) -> Fraction:
    return saga_a[index] * (value - saga_centers[index])


def composite_quadratic_objective(value: Fraction) -> Fraction:
    smooth = sum(
        (
            coefficient * (value - center) ** 2 / 2
            for coefficient, center in zip(saga_a, saga_centers)
        ),
        Fraction(),
    ) / saga_N
    return smooth + saga_lambda * abs(value)


linear_term = sum(
    (coefficient * center for coefficient, center in zip(saga_a, saga_centers)),
    Fraction(),
) / saga_N
saga_optimum = soft_fraction(linear_term, saga_lambda) / saga_L
saga_initial_table = tuple(
    component_quadratic_gradient(index, saga_x0) for index in range(saga_N)
)
saga_states: dict[
    tuple[Fraction, tuple[Fraction, ...], Fraction], Fraction
] = {(saga_x0, saga_initial_table, Fraction()): Fraction(1)}
expected_conditional_variances: list[Fraction] = []
unbiased_on_every_reached_state = True
state_counts = [len(saga_states)]
for _iteration in range(saga_horizon):
    next_states: dict[
        tuple[Fraction, tuple[Fraction, ...], Fraction], Fraction
    ] = defaultdict(Fraction)
    expected_variance = Fraction()
    for (x_state, table_state, iterate_sum), state_probability in saga_states.items():
        current = tuple(
            component_quadratic_gradient(index, x_state) for index in range(saga_N)
        )
        full_gradient = sum(current, Fraction()) / saga_N
        table_mean = sum(table_state, Fraction()) / saga_N
        estimators = tuple(
            fresh - old + table_mean for fresh, old in zip(current, table_state)
        )
        estimator_mean = sum(estimators, Fraction()) / saga_N
        unbiased_on_every_reached_state = (
            unbiased_on_every_reached_state and estimator_mean == full_gradient
        )
        conditional_variance = sum(
            ((estimate - full_gradient) ** 2 for estimate in estimators), Fraction()
        ) / saga_N
        expected_variance += state_probability * conditional_variance
        for index, estimate in enumerate(estimators):
            next_x = soft_fraction(
                x_state - saga_tau * estimate, saga_tau * saga_lambda
            )
            next_table = list(table_state)
            next_table[index] = current[index]
            next_key = (next_x, tuple(next_table), iterate_sum + next_x)
            next_states[next_key] += state_probability / saga_N
    expected_conditional_variances.append(expected_variance)
    saga_states = dict(next_states)
    state_counts.append(len(saga_states))

saga_expected_gap = sum(
    (
        probability
        * (
            composite_quadratic_objective(iterate_sum / saga_horizon)
            - composite_quadratic_objective(saga_optimum)
        )
        for (_x, _table, iterate_sum), probability in saga_states.items()
    ),
    Fraction(),
)
saga_variance_sum = sum(expected_conditional_variances, Fraction())
saga_bridge_rhs = (saga_x0 - saga_optimum) ** 2 / (
    2 * saga_tau * saga_horizon
) + saga_tau * saga_variance_sum / saga_horizon
saga_bridge_ok = (
    2 * saga_L * saga_tau <= 1
    and unbiased_on_every_reached_state
    and sum(saga_states.values(), Fraction()) == 1
    and saga_expected_gap <= saga_bridge_rhs
)
record(
    "prox_saga_variance_sum_bridge_exact",
    saga_bridge_ok,
    {
        "label": "finite exact witness, not a replacement for the chapter proof",
        "N": saga_N,
        "K": saga_horizon,
        "L": str(saga_L),
        "tau": str(saga_tau),
        "x_star": str(saga_optimum),
        "reached_state_counts": state_counts,
        "expected_conditional_variances": [
            str(value) for value in expected_conditional_variances
        ],
        "variance_sum": str(saga_variance_sum),
        "expected_ergodic_objective_gap": str(saga_expected_gap),
        "stated_bridge_right_hand_side": str(saga_bridge_rhs),
        "slack": str(saga_bridge_rhs - saga_expected_gap),
    },
)


def load_lab_module() -> ModuleType:
    module_name = "_original_01_stochastic_composite_lab_validation"
    specification = importlib.util.spec_from_file_location(module_name, LAB)
    if specification is None or specification.loader is None:
        raise ImportError(f"Cannot load lab module from {LAB}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


lab = load_lab_module()
result_payload = json.loads(RESULT_JSON.read_text(encoding="utf-8"))

with RESULT_CSV.open("r", encoding="utf-8", newline="") as stream:
    raw_csv_rows = list(csv.DictReader(stream))

float_fields = (
    "epochs",
    "objective",
    "objective_gap",
    "prox_gradient_mapping_norm",
    "direction_variance_trace",
)
integer_fields = ("component_gradient_evaluations", "nonzero_coordinates")
csv_rows: list[dict[str, float | int | str]] = []
for raw_row in raw_csv_rows:
    normalized: dict[str, float | int | str] = {"method": raw_row["method"]}
    normalized.update({field: int(raw_row[field]) for field in integer_fields})
    normalized.update({field: float(raw_row[field]) for field in float_fields})
    csv_rows.append(normalized)


def reconstruct_problem() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(lab.SEED)
    matrix = rng.normal(size=(lab.N, lab.D)) / math.sqrt(lab.D)
    true_x = np.zeros(lab.D)
    support = rng.choice(lab.D, size=lab.TRUE_NONZERO, replace=False)
    true_x[support] = rng.normal(
        loc=0.0, scale=2.0, size=lab.TRUE_NONZERO
    )
    observations = matrix @ true_x + lab.NOISE_STD * rng.normal(size=lab.N)
    return matrix, observations


matrix, observations = reconstruct_problem()
smooth_lipschitz = float(np.linalg.norm(matrix, ord=2) ** 2 / lab.N)
component_lipschitz = float(np.max(np.sum(matrix * matrix, axis=1)))
reference_x, recomputed_reference = lab.reference_fista(
    matrix, observations, smooth_lipschitz
)
recomputed_optimum = float(recomputed_reference["objective"])
mapping_step = 1.0 / smooth_lipschitz
recomputed_rows: list[dict[str, float | int | str]] = []
recomputed_rows.extend(
    lab.run_prox_sgd(
        matrix,
        observations,
        recomputed_optimum,
        component_lipschitz,
        mapping_step,
    )
)
recomputed_rows.extend(
    lab.run_prox_minibatch(
        matrix,
        observations,
        recomputed_optimum,
        component_lipschitz,
        mapping_step,
    )
)
recomputed_rows.extend(
    lab.run_prox_saga(
        matrix,
        observations,
        recomputed_optimum,
        component_lipschitz,
        mapping_step,
    )
)

recomputed_final_rows = {
    method: max(
        (row for row in recomputed_rows if row["method"] == method),
        key=lambda row: int(row["component_gradient_evaluations"]),
    )
    for method in sorted({str(row["method"]) for row in recomputed_rows})
}
configuration = {
    "seed": lab.SEED,
    "samples": lab.N,
    "dimension": lab.D,
    "true_nonzero_coordinates": lab.TRUE_NONZERO,
    "noise_standard_deviation": lab.NOISE_STD,
    "l1_regularization": lab.LAMBDA,
    "epochs": lab.EPOCHS,
    "component_gradient_budget": lab.EPOCHS * lab.N,
    "minibatch_size": lab.BATCH_SIZE,
    "sampling": "with replacement for SGD/minibatch/SAGA index draws",
}
configuration_canonical = json.dumps(
    configuration, ensure_ascii=False, sort_keys=True, separators=(",", ":")
).encode("utf-8")
observed_stack = {
    "python": ".".join(str(part) for part in sys.version_info[:3]),
    "numpy": np.__version__,
    "matplotlib": lab.matplotlib.__version__,
}

problem_payload = result_payload.get("problem", {})
reference_payload = problem_payload.get("reference", {})
lab_replay_ok = (
    recomputed_rows == csv_rows
    and result_payload.get("configuration") == configuration
    and result_payload.get("row_count") == len(recomputed_rows)
    and result_payload.get("final_rows") == recomputed_final_rows
    and problem_payload.get("smooth_lipschitz") == smooth_lipschitz
    and problem_payload.get("max_component_lipschitz") == component_lipschitz
    and reference_payload == recomputed_reference
    and problem_payload.get("reference_nonzero_coordinates")
    == int(np.count_nonzero(np.abs(reference_x) > 1e-8))
    and result_payload.get("dependencies") == observed_stack
)
record(
    "lab_in_memory_replay_and_output_consistency",
    lab_replay_ok,
    {
        "rows_recomputed": len(recomputed_rows),
        "rows_in_csv": len(csv_rows),
        "configuration_sha256": sha256_bytes(configuration_canonical),
        "reference_recomputed": recomputed_reference,
        "csv_rows_exact_match": recomputed_rows == csv_rows,
        "json_final_rows_exact_match": result_payload.get("final_rows")
        == recomputed_final_rows,
        "observed_stack": observed_stack,
    },
)


# Independent monotone proximal-gradient reference.  This specifically avoids
# assuming that the accelerated FISTA trajectory itself must be monotone.
monotone_x = np.zeros(lab.D)
monotone_values = [lab.objective(matrix, observations, monotone_x)]
monotone_mapping = math.inf
monotone_iteration = 0
largest_objective_increase = -math.inf
for monotone_iteration in range(1, lab.REFERENCE_MAX_ITER + 1):
    next_x = lab.soft_threshold(
        monotone_x
        - mapping_step * lab.full_gradient(matrix, observations, monotone_x),
        mapping_step * lab.LAMBDA,
    )
    next_value = lab.objective(matrix, observations, next_x)
    largest_objective_increase = max(
        largest_objective_increase, next_value - monotone_values[-1]
    )
    monotone_values.append(next_value)
    monotone_x = next_x
    monotone_mapping = lab.prox_gradient_mapping_norm(
        matrix, observations, monotone_x, mapping_step
    )
    if monotone_mapping <= lab.REFERENCE_TOL:
        break
monotone_reference_ok = (
    largest_objective_increase <= 1e-14
    and monotone_mapping <= lab.REFERENCE_TOL
    and math.isclose(
        monotone_values[-1], recomputed_optimum, rel_tol=0.0, abs_tol=2e-15
    )
)
record(
    "monotone_proximal_gradient_reference_recomputation",
    monotone_reference_ok,
    {
        "iterations": monotone_iteration,
        "objective": monotone_values[-1],
        "mapping_norm": monotone_mapping,
        "tolerance": lab.REFERENCE_TOL,
        "largest_objective_increase": largest_objective_increase,
        "fista_reported_objective": recomputed_optimum,
    },
)


rows_by_method = {
    method: [row for row in recomputed_rows if row["method"] == method]
    for method in sorted({str(row["method"]) for row in recomputed_rows})
}
initial_saga_row = rows_by_method["prox_saga"][0]
initial_saga_variance = float(initial_saga_row["direction_variance_trace"])
initial_saga_table = matrix * (matrix @ np.zeros(lab.D) - observations)[:, None]
initial_saga_estimators = (
    matrix * (matrix @ np.zeros(lab.D) - observations)[:, None]
    - initial_saga_table
    + initial_saga_table.mean(axis=0)
)
initialized_table_variance = float(
    np.mean(
        np.sum(
            (
                initial_saga_estimators
                - initial_saga_estimators.mean(axis=0)
            )
            ** 2,
            axis=1,
        )
    )
)
record(
    "saga_initialized_table_direction_variance",
    initial_saga_variance == 0.0 and initialized_table_variance <= 1e-28,
    {
        "checkpoint_component_gradient_evaluations": int(
            initial_saga_row["component_gradient_evaluations"]
        ),
        "reported_direction_variance_trace": initial_saga_variance,
        "independently_recomputed_direction_variance_trace": initialized_table_variance,
        "reason": "At x_0 every stored component gradient equals the fresh component gradient, so every SAGA estimator equals the table mean.",
    },
)
expected_budget = lab.EPOCHS * lab.N
expected_evaluations = {
    "prox_sgd_b1": list(range(0, expected_budget + 1, lab.N)),
    f"prox_minibatch_b{lab.BATCH_SIZE}": list(
        range(0, expected_budget + 1, lab.N)
    ),
    "prox_saga": list(range(lab.N, expected_budget + 1, lab.N)),
}
observed_evaluations = {
    method: [int(row["component_gradient_evaluations"]) for row in rows]
    for method, rows in rows_by_method.items()
}
budget_ok = (
    observed_evaluations == expected_evaluations
    and all(
        int(rows[-1]["component_gradient_evaluations"]) == expected_budget
        for rows in rows_by_method.values()
    )
    and len(rows_by_method["prox_saga"]) == lab.EPOCHS
    and len(rows_by_method["prox_sgd_b1"]) == lab.EPOCHS + 1
    and len(rows_by_method[f"prox_minibatch_b{lab.BATCH_SIZE}"])
    == lab.EPOCHS + 1
)
record(
    "component_gradient_budget_accounting",
    budget_ok,
    {
        "budget_per_method": expected_budget,
        "saga_initial_table_cost": lab.N,
        "minibatch_cost_per_update": lab.BATCH_SIZE,
        "observed_checkpoint_evaluations": observed_evaluations,
    },
)


output_identities = {
    RESULT_JSON.name: file_identity(RESULT_JSON),
    RESULT_CSV.name: file_identity(RESULT_CSV),
    RESULT_SVG.name: file_identity(RESULT_SVG),
}
json_csv_metadata = result_payload.get("csv", {})
json_svg_metadata = result_payload.get("svg", {})
source_hash_abbreviations_ok = all(
    fragment in source_text
    for fragment in (
        r"86ff701a\ldots c447",
        r"61a6591a\ldots 5d37",
        r"87c772d9\ldots 2830",
    )
)
output_hashes_ok = (
    all(
        output_identities[name]["bytes"] == expected["bytes"]
        and output_identities[name]["sha256"] == expected["sha256"]
        for name, expected in EXPECTED_OUTPUT_IDENTITIES.items()
    )
    and json_csv_metadata.get("bytes") == output_identities[RESULT_CSV.name]["bytes"]
    and json_csv_metadata.get("sha256")
    == output_identities[RESULT_CSV.name]["sha256"]
    and json_svg_metadata.get("bytes") == output_identities[RESULT_SVG.name]["bytes"]
    and json_svg_metadata.get("sha256")
    == output_identities[RESULT_SVG.name]["sha256"]
    and source_hash_abbreviations_ok
)
record(
    "frozen_lab_output_hash_identities",
    output_hashes_ok,
    {
        "identities": output_identities,
        "json_binds_csv": json_csv_metadata.get("sha256")
        == output_identities[RESULT_CSV.name]["sha256"],
        "json_binds_svg": json_svg_metadata.get("sha256")
        == output_identities[RESULT_SVG.name]["sha256"],
        "chapter_abbreviations_match": source_hash_abbreviations_ok,
    },
)


expected_final_values = {
    "prox_sgd_b1": {
        "objective_gap": 0.04916907597666503,
        "prox_gradient_mapping_norm": 0.021155328208993934,
        "nonzero_coordinates": 33,
    },
    "prox_minibatch_b16": {
        "objective_gap": 0.002570744875912634,
        "prox_gradient_mapping_norm": 0.009863014116815592,
        "nonzero_coordinates": 10,
    },
    "prox_saga": {
        "objective_gap": 2.0444369530636664e-09,
        "prox_gradient_mapping_norm": 9.866567454031472e-06,
        "nonzero_coordinates": 5,
    },
}
terminal_values_ok = recomputed_reference["objective"] == 0.31517396778742246
for method, expected in expected_final_values.items():
    observed = recomputed_final_rows[method]
    terminal_values_ok = terminal_values_ok and all(
        observed[field] == value for field, value in expected.items()
    )
record(
    "chapter_terminal_values_match_live_computation",
    terminal_values_ok,
    {
        "reference_objective": recomputed_reference["objective"],
        "reference_mapping_norm": recomputed_reference["mapping_norm"],
        "terminal_values": {
            method: {
                field: recomputed_final_rows[method][field]
                for field in expected_final_values[method]
            }
            for method in expected_final_values
        },
    },
)


final_input_identities = {path.name: file_identity(path) for path in required_files}
record(
    "inputs_stable_during_validation",
    initial_input_identities == final_input_identities,
    {
        "initial_sha256": {
            name: identity["sha256"]
            for name, identity in initial_input_identities.items()
        },
        "final_sha256": {
            name: identity["sha256"] for name, identity in final_input_identities.items()
        },
    },
)

failures = [item["gate"] for item in gates if not item["pass"]]
payload = {
    "schema": "o015-original-01-open-math-validation-v1",
    "result": "pass" if not failures else "fail",
    "status": "PASS" if not failures else "FAIL",
    "failures": failures,
    "scope": {
        "unit": "Original 01: stochastic composite, mirror, minibatch, and Prox-SAGA",
        "source_mutated_by_validator": False,
        "lab_outputs_mutated_by_validator": False,
        "lab_replay": "in memory; lab main() was not invoked",
        "numerical_witnesses_are_not_proofs": True,
        "network_access": False,
        "upstream_contact": False,
    },
    "determinism": {
        "observed_stack": observed_stack,
        "exact_arithmetic": "fractions.Fraction for finite mathematical witnesses",
        "randomness": "all mathematical samples enumerated; lab uses frozen seeds",
        "json": "UTF-8, LF, sorted keys, two-space indentation",
    },
    "inputs": {
        "chapter": file_identity(SOURCE),
        "lab": file_identity(LAB),
        "lab_results_json": file_identity(RESULT_JSON),
        "lab_results_csv": file_identity(RESULT_CSV),
        "lab_results_svg": file_identity(RESULT_SVG),
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
