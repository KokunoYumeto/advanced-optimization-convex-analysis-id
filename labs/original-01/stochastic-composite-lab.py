#!/usr/bin/env python3
"""Deterministic open-computation lab for O015 original tranche 1.

The experiment compares proximal SGD, proximal minibatch SGD, and Prox-SAGA
on an L1-regularized least-squares problem under a common component-gradient
evaluation budget. It writes accessible CSV/JSON results and a redundant SVG
plot. No network access or proprietary solver is required.

Original lab code and documentation: CC BY-SA 4.0
https://creativecommons.org/licenses/by-sa/4.0/
Produced by OpenAI Codex gpt-5.6-sol, Ultra, on the repository user's
instructions. Python, NumPy, and Matplotlib are unbundled runtime dependencies;
their own licenses remain unchanged. Cited researchers did not author this code.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "o015-original-01-20260825"
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
RESULT_JSON = HERE / "results.json"
RESULT_CSV = HERE / "results.csv"
RESULT_SVG = HERE / "objective-gap.svg"

SEED = 20260825
N = 320
D = 40
TRUE_NONZERO = 8
NOISE_STD = 0.08
LAMBDA = 0.03
EPOCHS = 12
BATCH_SIZE = 16
REFERENCE_MAX_ITER = 50000
REFERENCE_TOL = 1e-11


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def soft_threshold(z: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(z) * np.maximum(np.abs(z) - threshold, 0.0)


def objective(a: np.ndarray, y: np.ndarray, x: np.ndarray) -> float:
    residual = a @ x - y
    return float(0.5 * residual @ residual / len(y) + LAMBDA * np.abs(x).sum())


def full_gradient(a: np.ndarray, y: np.ndarray, x: np.ndarray) -> np.ndarray:
    return a.T @ (a @ x - y) / len(y)


def component_gradient(
    a: np.ndarray, y: np.ndarray, x: np.ndarray, index: int
) -> np.ndarray:
    return a[index] * (a[index] @ x - y[index])


def prox_gradient_mapping_norm(
    a: np.ndarray, y: np.ndarray, x: np.ndarray, step: float
) -> float:
    mapped = soft_threshold(x - step * full_gradient(a, y, x), step * LAMBDA)
    return float(np.linalg.norm((x - mapped) / step))


def reference_fista(
    a: np.ndarray, y: np.ndarray, smooth_lipschitz: float
) -> tuple[np.ndarray, dict[str, float | int]]:
    step = 1.0 / smooth_lipschitz
    x = np.zeros(D)
    z = x.copy()
    t = 1.0
    mapping = math.inf
    iteration = 0
    for iteration in range(1, REFERENCE_MAX_ITER + 1):
        x_next = soft_threshold(
            z - step * full_gradient(a, y, z), step * LAMBDA
        )
        t_next = 0.5 * (1.0 + math.sqrt(1.0 + 4.0 * t * t))
        z = x_next + ((t - 1.0) / t_next) * (x_next - x)
        x = x_next
        t = t_next
        if iteration % 25 == 0:
            mapping = prox_gradient_mapping_norm(a, y, x, step)
            if mapping <= REFERENCE_TOL:
                break
    return x, {
        "iterations": iteration,
        "step": step,
        "mapping_norm": mapping,
        "objective": objective(a, y, x),
    }


def checkpoint(
    rows: list[dict[str, float | int | str]],
    method: str,
    evaluations: int,
    epoch: float,
    a: np.ndarray,
    y: np.ndarray,
    x: np.ndarray,
    optimum: float,
    mapping_step: float,
    direction_variance: float,
) -> None:
    value = objective(a, y, x)
    rows.append(
        {
            "method": method,
            "component_gradient_evaluations": evaluations,
            "epochs": epoch,
            "objective": value,
            "objective_gap": max(value - optimum, 0.0),
            "prox_gradient_mapping_norm": prox_gradient_mapping_norm(
                a, y, x, mapping_step
            ),
            "nonzero_coordinates": int(np.count_nonzero(np.abs(x) > 1e-8)),
            "direction_variance_trace": direction_variance,
        }
    )


def empirical_direction_variance(
    a: np.ndarray, y: np.ndarray, x: np.ndarray
) -> float:
    gradients = a * (a @ x - y)[:, None]
    centered = gradients - gradients.mean(axis=0)
    return float(np.mean(np.sum(centered * centered, axis=1)))


def run_prox_sgd(
    a: np.ndarray,
    y: np.ndarray,
    optimum: float,
    component_lipschitz: float,
    mapping_step: float,
) -> list[dict[str, float | int | str]]:
    rng = np.random.default_rng(SEED + 1)
    x = np.zeros(D)
    step = 0.75 / component_lipschitz
    rows: list[dict[str, float | int | str]] = []
    budget = EPOCHS * N
    checkpoint(
        rows,
        "prox_sgd_b1",
        0,
        0.0,
        a,
        y,
        x,
        optimum,
        mapping_step,
        empirical_direction_variance(a, y, x),
    )
    for evaluation in range(1, budget + 1):
        i = int(rng.integers(N))
        gradient = component_gradient(a, y, x, i)
        x = soft_threshold(x - step * gradient, step * LAMBDA)
        if evaluation % N == 0:
            checkpoint(
                rows,
                "prox_sgd_b1",
                evaluation,
                evaluation / N,
                a,
                y,
                x,
                optimum,
                mapping_step,
                empirical_direction_variance(a, y, x),
            )
    return rows


def run_prox_minibatch(
    a: np.ndarray,
    y: np.ndarray,
    optimum: float,
    component_lipschitz: float,
    mapping_step: float,
) -> list[dict[str, float | int | str]]:
    rng = np.random.default_rng(SEED + 2)
    x = np.zeros(D)
    step = 0.75 / component_lipschitz
    rows: list[dict[str, float | int | str]] = []
    budget = EPOCHS * N
    checkpoint(
        rows,
        f"prox_minibatch_b{BATCH_SIZE}",
        0,
        0.0,
        a,
        y,
        x,
        optimum,
        mapping_step,
        empirical_direction_variance(a, y, x) / BATCH_SIZE,
    )
    evaluations = 0
    while evaluations + BATCH_SIZE <= budget:
        indices = rng.integers(N, size=BATCH_SIZE)
        residual = a[indices] @ x - y[indices]
        gradient = a[indices].T @ residual / BATCH_SIZE
        x = soft_threshold(x - step * gradient, step * LAMBDA)
        evaluations += BATCH_SIZE
        if evaluations % N == 0:
            checkpoint(
                rows,
                f"prox_minibatch_b{BATCH_SIZE}",
                evaluations,
                evaluations / N,
                a,
                y,
                x,
                optimum,
                mapping_step,
                empirical_direction_variance(a, y, x) / BATCH_SIZE,
            )
    return rows


def run_prox_saga(
    a: np.ndarray,
    y: np.ndarray,
    optimum: float,
    component_lipschitz: float,
    mapping_step: float,
) -> list[dict[str, float | int | str]]:
    rng = np.random.default_rng(SEED + 3)
    x = np.zeros(D)
    table = a * (a @ x - y)[:, None]
    table_mean = table.mean(axis=0)
    step = 1.0 / (3.0 * component_lipschitz)
    rows: list[dict[str, float | int | str]] = []
    budget = EPOCHS * N
    evaluations = N
    checkpoint(
        rows,
        "prox_saga",
        evaluations,
        evaluations / N,
        a,
        y,
        x,
        optimum,
        mapping_step,
        0.0,
    )
    while evaluations < budget:
        i = int(rng.integers(N))
        fresh = component_gradient(a, y, x, i)
        estimate = fresh - table[i] + table_mean
        old = table[i].copy()
        x = soft_threshold(x - step * estimate, step * LAMBDA)
        table[i] = fresh
        table_mean += (fresh - old) / N
        evaluations += 1
        if evaluations % N == 0:
            current_components = a * (a @ x - y)[:, None]
            differences = current_components - table
            centered = differences - differences.mean(axis=0)
            saga_variance = float(np.mean(np.sum(centered * centered, axis=1)))
            checkpoint(
                rows,
                "prox_saga",
                evaluations,
                evaluations / N,
                a,
                y,
                x,
                optimum,
                mapping_step,
                saga_variance,
            )
    return rows


def write_svg(rows: list[dict[str, float | int | str]]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    methods = sorted({str(row["method"]) for row in rows})
    for method in methods:
        subset = [row for row in rows if row["method"] == method]
        x = [int(row["component_gradient_evaluations"]) for row in subset]
        y = [max(float(row["objective_gap"]), 1e-16) for row in subset]
        ax.semilogy(x, y, marker="o", linewidth=1.5, markersize=3.5, label=method)
    ax.set_xlabel("Evaluasi gradien komponen")
    ax.set_ylabel("Kesenjangan objektif (skala log)")
    ax.set_title("Regresi renggang: biaya oracle yang sama")
    ax.grid(True, which="both", alpha=0.28)
    ax.legend()
    fig.savefig(
        RESULT_SVG,
        format="svg",
        metadata={
            "Title": "Kesenjangan objektif terhadap evaluasi gradien komponen",
            "Date": "2026-08-25T00:00:00Z",
            "Description": (
                "Grafik redundan; seluruh nilai tersedia dalam results.csv dan "
                "results.json."
            ),
        },
    )
    plt.close(fig)


def main() -> None:
    rng = np.random.default_rng(SEED)
    a = rng.normal(size=(N, D)) / math.sqrt(D)
    true_x = np.zeros(D)
    support = rng.choice(D, size=TRUE_NONZERO, replace=False)
    true_x[support] = rng.normal(loc=0.0, scale=2.0, size=TRUE_NONZERO)
    y = a @ true_x + NOISE_STD * rng.normal(size=N)

    smooth_lipschitz = float(np.linalg.norm(a, ord=2) ** 2 / N)
    component_lipschitz = float(np.max(np.sum(a * a, axis=1)))
    reference_x, reference = reference_fista(a, y, smooth_lipschitz)
    optimum = float(reference["objective"])
    mapping_step = 1.0 / smooth_lipschitz

    rows = []
    rows.extend(
        run_prox_sgd(a, y, optimum, component_lipschitz, mapping_step)
    )
    rows.extend(
        run_prox_minibatch(a, y, optimum, component_lipschitz, mapping_step)
    )
    rows.extend(
        run_prox_saga(a, y, optimum, component_lipschitz, mapping_step)
    )

    fieldnames = [
        "method",
        "component_gradient_evaluations",
        "epochs",
        "objective",
        "objective_gap",
        "prox_gradient_mapping_norm",
        "nonzero_coordinates",
        "direction_variance_trace",
    ]
    with RESULT_CSV.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    final_rows = {
        method: max(
            (row for row in rows if row["method"] == method),
            key=lambda row: int(row["component_gradient_evaluations"]),
        )
        for method in sorted({str(row["method"]) for row in rows})
    }
    payload = {
        "schema": "o015-original-01-stochastic-composite-lab-v1",
        "result": "pass",
        "configuration": {
            "seed": SEED,
            "samples": N,
            "dimension": D,
            "true_nonzero_coordinates": TRUE_NONZERO,
            "noise_standard_deviation": NOISE_STD,
            "l1_regularization": LAMBDA,
            "epochs": EPOCHS,
            "component_gradient_budget": EPOCHS * N,
            "minibatch_size": BATCH_SIZE,
            "sampling": "with replacement for SGD/minibatch/SAGA index draws",
        },
        "problem": {
            "objective": "0.5/N * ||A x - y||_2^2 + lambda * ||x||_1",
            "smooth_lipschitz": smooth_lipschitz,
            "max_component_lipschitz": component_lipschitz,
            "reference": reference,
            "reference_nonzero_coordinates": int(
                np.count_nonzero(np.abs(reference_x) > 1e-8)
            ),
        },
        "final_rows": final_rows,
        "row_count": len(rows),
        "csv": {"path": RESULT_CSV.name},
        "svg": {
            "path": RESULT_SVG.name,
            "redundant_with_accessible_tables": True,
        },
        "dependencies": {
            "python": __import__("sys").version.split()[0],
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "network_access": False,
        "upstream_contact": False,
    }
    RESULT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_svg(rows)

    # Bind generated outputs after every file exists. The JSON deliberately
    # omits its own hash to avoid a self-reference cycle.
    payload["csv"].update(
        {"bytes": RESULT_CSV.stat().st_size, "sha256": sha256(RESULT_CSV)}
    )
    payload["svg"].update(
        {"bytes": RESULT_SVG.stat().st_size, "sha256": sha256(RESULT_SVG)}
    )
    RESULT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "result": "pass",
                "rows": len(rows),
                "reference_mapping_norm": reference["mapping_norm"],
                "json_bytes": RESULT_JSON.stat().st_size,
                "json_sha256": sha256(RESULT_JSON),
                "csv_bytes": RESULT_CSV.stat().st_size,
                "csv_sha256": sha256(RESULT_CSV),
                "svg_bytes": RESULT_SVG.stat().st_size,
                "svg_sha256": sha256(RESULT_SVG),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
