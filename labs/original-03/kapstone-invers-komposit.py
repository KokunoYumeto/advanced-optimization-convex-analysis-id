#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-4.0
# Independent computation component for the Bahasa Indonesia D90 edition.
"""Deterministic capstone for a robust composite inverse problem.

The matched-budget solvers are accelerated proximal gradient (FISTA) and
primal-dual hybrid gradient (PDHG). Both use exactly one A and one A.T product
per iteration. A feasible dual rescaling supplies a rigorous lower bound.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
JSON_PATH = HERE / "kapstone-invers-komposit-results.json"
CSV_PATH = HERE / "kapstone-invers-komposit-results.csv"
SVG_PATH = HERE / "kapstone-invers-komposit.svg"

SEED = 20260826
OBSERVATIONS = 72
UNKNOWN_DIMENSION = 48
OUTLIER_COUNT = 8
DELTA = 0.08
LAMBDA = 0.055
MATCHED_ITERATIONS = 1800
TRACE_STRIDE = 10


def huber(values: np.ndarray) -> np.ndarray:
    absolute = np.abs(values)
    return np.where(
        absolute <= DELTA,
        0.5 * values * values,
        DELTA * (absolute - 0.5 * DELTA),
    )


def objective(matrix: np.ndarray, data: np.ndarray, point: np.ndarray) -> float:
    residual = matrix @ point - data
    return float(np.sum(huber(residual)) + LAMBDA * np.linalg.norm(point, 1))


def smooth_gradient(matrix: np.ndarray, data: np.ndarray, point: np.ndarray) -> np.ndarray:
    residual = matrix @ point - data
    return matrix.T @ np.clip(residual, -DELTA, DELTA)


def soft_threshold(values: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(values) * np.maximum(np.abs(values) - threshold, 0.0)


def feasible_dual(
    matrix: np.ndarray,
    data: np.ndarray,
    candidate: np.ndarray,
) -> tuple[np.ndarray, float, float]:
    clipped = np.clip(candidate, -DELTA, DELTA)
    stationarity = float(np.linalg.norm(matrix.T @ clipped, np.inf))
    scale = min(1.0, LAMBDA / max(stationarity, 1.0e-300))
    dual = scale * clipped
    lower_bound = float(-data @ dual - 0.5 * (dual @ dual))
    feasibility = max(
        float(np.max(np.abs(dual))) - DELTA,
        float(np.linalg.norm(matrix.T @ dual, np.inf)) - LAMBDA,
        0.0,
    )
    return dual, lower_bound, feasibility


def fista(
    matrix: np.ndarray,
    data: np.ndarray,
    truth: np.ndarray,
    lipschitz: float,
) -> tuple[np.ndarray, list[dict[str, object]]]:
    step = 0.99 / lipschitz
    point = np.zeros(matrix.shape[1])
    extrapolated = point.copy()
    momentum = 1.0
    trace: list[dict[str, object]] = []
    for iteration in range(1, MATCHED_ITERATIONS + 1):
        gradient = smooth_gradient(matrix, data, extrapolated)
        next_point = soft_threshold(extrapolated - step * gradient, step * LAMBDA)
        next_momentum = 0.5 * (1.0 + math.sqrt(1.0 + 4.0 * momentum * momentum))
        candidate = next_point + ((momentum - 1.0) / next_momentum) * (next_point - point)
        # Gradient restart uses only already available vectors, so it does not
        # add an A or A.T application to the matched core oracle budget.
        if float((extrapolated - next_point) @ (next_point - point)) > 0.0:
            extrapolated = next_point.copy()
            next_momentum = 1.0
        else:
            extrapolated = candidate
        point = next_point
        momentum = next_momentum
        if iteration == 1 or iteration % TRACE_STRIDE == 0 or iteration == MATCHED_ITERATIONS:
            residual = matrix @ point - data
            _, lower, dual_feasibility = feasible_dual(matrix, data, residual)
            value = objective(matrix, data, point)
            mapping = (
                point
                - soft_threshold(
                    point - step * smooth_gradient(matrix, data, point),
                    step * LAMBDA,
                )
            ) / step
            trace.append(
                {
                    "solver": "FISTA-restart",
                    "iteration": iteration,
                    "matrix_vector_products": 2 * iteration,
                    "objective": value,
                    "dual_lower_bound": lower,
                    "certified_gap": value - lower,
                    "dual_feasibility_violation": dual_feasibility,
                    "gradient_mapping_norm": float(np.linalg.norm(mapping)),
                    "relative_recovery_error": float(
                        np.linalg.norm(point - truth) / np.linalg.norm(truth)
                    ),
                }
            )
    return point, trace


def pdhg(
    matrix: np.ndarray,
    data: np.ndarray,
    truth: np.ndarray,
    operator_norm: float,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, object]]]:
    tau = 0.99 / operator_norm
    sigma = 0.99 / operator_norm
    point = np.zeros(matrix.shape[1])
    extrapolated = point.copy()
    dual = np.zeros(matrix.shape[0])
    trace: list[dict[str, object]] = []
    for iteration in range(1, MATCHED_ITERATIONS + 1):
        dual = np.clip(
            (dual + sigma * (matrix @ extrapolated - data)) / (1.0 + sigma),
            -DELTA,
            DELTA,
        )
        next_point = soft_threshold(point - tau * (matrix.T @ dual), tau * LAMBDA)
        extrapolated = next_point + (next_point - point)
        point = next_point
        if iteration == 1 or iteration % TRACE_STRIDE == 0 or iteration == MATCHED_ITERATIONS:
            _, lower, dual_feasibility = feasible_dual(matrix, data, dual)
            value = objective(matrix, data, point)
            trace.append(
                {
                    "solver": "PDHG-referensi",
                    "iteration": iteration,
                    "matrix_vector_products": 2 * iteration,
                    "objective": value,
                    "dual_lower_bound": lower,
                    "certified_gap": value - lower,
                    "dual_feasibility_violation": dual_feasibility,
                    "gradient_mapping_norm": "",
                    "relative_recovery_error": float(
                        np.linalg.norm(point - truth) / np.linalg.norm(truth)
                    ),
                }
            )
    return point, dual, trace


def write_csv(traces: list[dict[str, object]]) -> None:
    fields = [
        "solver",
        "iteration",
        "matrix_vector_products",
        "objective",
        "dual_lower_bound",
        "certified_gap",
        "dual_feasibility_violation",
        "gradient_mapping_norm",
        "relative_recovery_error",
    ]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(traces)


def write_svg(traces: list[dict[str, object]]) -> None:
    width, height = 760, 420
    left, right, top, bottom = 76, 25, 28, 58
    plot_width, plot_height = width - left - right, height - top - bottom
    grouped = {
        name: [item for item in traces if item["solver"] == name]
        for name in ("FISTA-restart", "PDHG-referensi")
    }
    lower_bound = max(float(item["dual_lower_bound"]) for item in traces)
    log_gaps = [
        math.log10(max(float(item["objective"]) - lower_bound, 1.0e-14))
        for item in traces
    ]
    ymin, ymax = min(log_gaps), max(log_gaps)
    span = max(ymax - ymin, 1.0)
    colors = {"FISTA-restart": "#245da8", "PDHG-referensi": "#23835b"}
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Konvergensi proyek kapstone invers komposit</title>',
        '<desc id="desc">Celah objektif terhadap batas bawah dual untuk FISTA monoton dan PDHG dengan anggaran perkalian matriks yang sama.</desc>',
        '<rect width="100%" height="100%" fill="white" />',
        f'<line x1="{left}" y1="{top+plot_height}" x2="{left+plot_width}" y2="{top+plot_height}" stroke="#222" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_height}" stroke="#222" />',
        f'<text x="{width/2:.1f}" y="{height-14}" text-anchor="middle" font-family="sans-serif" font-size="14">Perkalian matriks-vektor</text>',
        f'<text x="18" y="{height/2:.1f}" transform="rotate(-90 18 {height/2:.1f})" text-anchor="middle" font-family="sans-serif" font-size="14">log10 celah terhadap batas dual</text>',
    ]
    for index, (name, rows) in enumerate(grouped.items()):
        points = []
        for item in rows:
            x = left + plot_width * int(item["matrix_vector_products"]) / (2 * MATCHED_ITERATIONS)
            value = math.log10(max(float(item["objective"]) - lower_bound, 1.0e-14))
            y = top + plot_height * (ymax - value) / span
            points.append(f"{x:.2f},{y:.2f}")
        elements.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[name]}" stroke-width="2" />')
        legend_y = 30 + 22 * index
        elements.append(f'<line x1="500" y1="{legend_y}" x2="526" y2="{legend_y}" stroke="{colors[name]}" stroke-width="3" />')
        elements.append(f'<text x="534" y="{legend_y+5}" font-family="sans-serif" font-size="12">{name}</text>')
    elements.append("</svg>\n")
    SVG_PATH.write_text("\n".join(elements), encoding="utf-8", newline="\n")


def file_record(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": path.name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def main() -> None:
    rng = np.random.default_rng(SEED)
    matrix = rng.normal(0.0, 1.0, size=(OBSERVATIONS, UNKNOWN_DIMENSION))
    matrix /= float(np.linalg.svd(matrix, compute_uv=False)[0])
    operator_norm = float(np.linalg.svd(matrix, compute_uv=False)[0])
    lipschitz = operator_norm * operator_norm

    truth = np.zeros(UNKNOWN_DIMENSION)
    support = np.array([3, 8, 14, 19, 27, 33, 39, 44])
    truth[support] = np.array([1.4, -1.0, 0.75, 1.15, -1.25, 0.9, -0.8, 1.05])
    clean_data = matrix @ truth
    data = clean_data + rng.normal(0.0, 0.012, size=OBSERVATIONS)
    outliers = np.sort(rng.choice(OBSERVATIONS, size=OUTLIER_COUNT, replace=False))
    outlier_signs = rng.choice(np.array([-1.0, 1.0]), size=OUTLIER_COUNT)
    data[outliers] += outlier_signs * rng.uniform(0.65, 1.05, size=OUTLIER_COUNT)

    fista_point, fista_trace = fista(matrix, data, truth, lipschitz)
    pdhg_point, pdhg_dual, pdhg_trace = pdhg(matrix, data, truth, operator_norm)
    traces = sorted(
        fista_trace + pdhg_trace,
        key=lambda item: (str(item["solver"]), int(item["iteration"])),
    )

    fista_objective = objective(matrix, data, fista_point)
    pdhg_objective = objective(matrix, data, pdhg_point)
    fista_residual = matrix @ fista_point - data
    _, fista_lower, fista_dual_violation = feasible_dual(matrix, data, fista_residual)
    _, pdhg_lower, pdhg_dual_violation = feasible_dual(matrix, data, pdhg_dual)
    best_lower = max(fista_lower, pdhg_lower)
    step = 0.99 / lipschitz
    fista_mapping = (
        fista_point
        - soft_threshold(
            fista_point - step * smooth_gradient(matrix, data, fista_point),
            step * LAMBDA,
        )
    ) / step
    least_squares = np.linalg.lstsq(matrix, data, rcond=None)[0]
    fista_error = float(np.linalg.norm(fista_point - truth) / np.linalg.norm(truth))
    pdhg_error = float(np.linalg.norm(pdhg_point - truth) / np.linalg.norm(truth))
    least_squares_error = float(np.linalg.norm(least_squares - truth) / np.linalg.norm(truth))
    matched_difference = abs(fista_objective - pdhg_objective)
    pdhg_stability = (0.99 / operator_norm) ** 2 * operator_norm**2

    certificates = {
        "fixed_data_dimensions": matrix.shape == (OBSERVATIONS, UNKNOWN_DIMENSION),
        "fixed_outlier_count": len(outliers) == OUTLIER_COUNT,
        "huber_gradient_lipschitz_bound_positive": lipschitz > 0.0,
        "fista_step_below_inverse_lipschitz": step * lipschitz < 1.0,
        "pdhg_step_product_strictly_below_one": pdhg_stability < 1.0,
        "matched_matrix_vector_budget": (
            fista_trace[-1]["matrix_vector_products"]
            == pdhg_trace[-1]["matrix_vector_products"]
            == 2 * MATCHED_ITERATIONS
        ),
        "matched_budget_objectives_agree": matched_difference <= 2.0e-5,
        "fista_gradient_mapping_small": float(np.linalg.norm(fista_mapping)) <= 2.0e-5,
        "fista_dual_certificate_feasible": fista_dual_violation <= 1.0e-12,
        "pdhg_dual_certificate_feasible": pdhg_dual_violation <= 1.0e-12,
        "fista_certified_gap_small": fista_objective - best_lower <= 2.0e-4,
        "pdhg_certified_gap_small": pdhg_objective - best_lower <= 2.0e-4,
        "robust_solution_improves_on_least_squares": max(fista_error, pdhg_error) < least_squares_error,
    }
    failed = [name for name, passed in certificates.items() if not passed]
    if failed:
        diagnostics = {
            "failed": failed,
            "matched_difference": matched_difference,
            "fista_mapping": float(np.linalg.norm(fista_mapping)),
            "fista_gap": fista_objective - best_lower,
            "pdhg_gap": pdhg_objective - best_lower,
            "errors": [fista_error, pdhg_error, least_squares_error],
        }
        raise RuntimeError(f"Sertifikat kapstone gagal: {diagnostics}")

    write_csv(traces)
    write_svg(traces)
    report = {
        "schema": "o015-original-03-kapstone-invers-komposit-v1",
        "result": "pass",
        "seed": SEED,
        "configuration": {
            "observations": OBSERVATIONS,
            "unknown_dimension": UNKNOWN_DIMENSION,
            "outlier_count": OUTLIER_COUNT,
            "huber_delta": DELTA,
            "l1_weight": LAMBDA,
            "matched_iterations": MATCHED_ITERATIONS,
            "matched_matrix_vector_products_per_solver": 2 * MATCHED_ITERATIONS,
            "operator_norm": operator_norm,
            "smooth_gradient_lipschitz_bound": lipschitz,
            "pdhg_tau_sigma_norm_squared": pdhg_stability,
        },
        "fixed_instance": {
            "support": support.tolist(),
            "truth": truth.tolist(),
            "outlier_indices": outliers.tolist(),
            "matrix_sha256": hashlib.sha256(matrix.astype("<f8").tobytes()).hexdigest(),
            "data_sha256": hashlib.sha256(data.astype("<f8").tobytes()).hexdigest(),
        },
        "matched_budget_summary": {
            "fista_objective": fista_objective,
            "pdhg_objective": pdhg_objective,
            "absolute_objective_difference": matched_difference,
            "best_feasible_dual_lower_bound": best_lower,
            "fista_certified_gap": fista_objective - best_lower,
            "pdhg_certified_gap": pdhg_objective - best_lower,
            "fista_gradient_mapping_norm": float(np.linalg.norm(fista_mapping)),
            "fista_relative_recovery_error": fista_error,
            "pdhg_relative_recovery_error": pdhg_error,
            "least_squares_relative_recovery_error": least_squares_error,
        },
        "seven_milestones": [
            {"id": 1, "name": "instans sintetik dan audit pencilan", "passed": True},
            {"id": 2, "name": "model Huber-l1 konveks", "passed": True},
            {"id": 3, "name": "batas Lipschitz dan langkah FISTA", "passed": True},
            {"id": 4, "name": "proksimal soft-threshold dan gradien terpotong", "passed": True},
            {"id": 5, "name": "dual Huber dan syarat stabilitas PDHG", "passed": True},
            {"id": 6, "name": "perbandingan anggaran perkalian matriks yang sama", "passed": True},
            {"id": 7, "name": "celah primal-dual dan mutu rekonstruksi", "passed": True},
        ],
        "certificates": certificates,
        "artifacts": [CSV_PATH.name, SVG_PATH.name],
    }
    JSON_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    outputs = [file_record(path) for path in (JSON_PATH, CSV_PATH, SVG_PATH)]
    print(json.dumps({"result": "pass", "outputs": outputs}, sort_keys=True))


if __name__ == "__main__":
    main()
