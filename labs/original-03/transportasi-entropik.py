#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-4.0
# Independent computation component for the Bahasa Indonesia D90 edition.
"""Deterministic log-domain Sinkhorn laboratory with numerical certificates."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
JSON_PATH = HERE / "transportasi-entropik-results.json"
CSV_PATH = HERE / "transportasi-entropik-results.csv"
SVG_PATH = HERE / "transportasi-entropik.svg"

SEED = 20260826
EPSILON = 0.12
TOLERANCE = 5.0e-13
MAX_ITERATIONS = 20000
SCALING_FACTOR = 7.0
UNDERFLOW_OFFSET = 1000.0


def logsumexp(values: np.ndarray, axis: int) -> np.ndarray:
    """Stable NumPy-only log-sum-exp for the two matrix axes used here."""
    maximum = np.max(values, axis=axis, keepdims=True)
    result = maximum + np.log(np.sum(np.exp(values - maximum), axis=axis, keepdims=True))
    return np.squeeze(result, axis=axis)


def sinkhorn_log(
    source_mass: np.ndarray,
    target_mass: np.ndarray,
    cost: np.ndarray,
    epsilon: float,
) -> dict[str, object]:
    log_a = np.log(source_mass)
    log_b = np.log(target_mass)
    f = np.zeros_like(source_mass)
    g = np.zeros_like(target_mass)
    history: list[tuple[int, float]] = []
    plan = np.empty_like(cost)
    log_plan = np.empty_like(cost)
    for iteration in range(1, MAX_ITERATIONS + 1):
        f = epsilon * (
            log_a - logsumexp((g[None, :] - cost) / epsilon, axis=1)
        )
        g = epsilon * (
            log_b - logsumexp((f[:, None] - cost) / epsilon, axis=0)
        )
        log_plan = (f[:, None] + g[None, :] - cost) / epsilon
        plan = np.exp(log_plan)
        residual = max(
            float(np.max(np.abs(plan.sum(axis=1) - source_mass))),
            float(np.max(np.abs(plan.sum(axis=0) - target_mass))),
        )
        if iteration == 1 or iteration % 25 == 0 or residual <= TOLERANCE:
            history.append((iteration, residual))
        if residual <= TOLERANCE:
            break
    else:
        raise RuntimeError("Sinkhorn log-domain tidak mencapai toleransi marginal")

    primal = float(
        np.sum(cost * plan)
        + epsilon * np.sum(plan * (log_plan - 1.0))
    )
    dual = float(source_mass @ f + target_mass @ g - epsilon * np.sum(plan))
    return {
        "plan": plan,
        "log_plan": log_plan,
        "f": f,
        "g": g,
        "iterations": iteration,
        "marginal_residual": residual,
        "primal": primal,
        "dual": dual,
        "primal_dual_gap": primal - dual,
        "history": history,
    }


def validate(
    source_mass: np.ndarray,
    target_mass: np.ndarray,
    cost: np.ndarray,
    baseline: dict[str, object],
    scaled: dict[str, object],
    shifted: dict[str, object],
) -> dict[str, object]:
    plan = np.asarray(baseline["plan"])
    scaled_plan = np.asarray(scaled["plan"])
    shifted_plan = np.asarray(shifted["plan"])
    naive_shifted_kernel = np.exp(-(cost + UNDERFLOW_OFFSET) / EPSILON)
    row_residual = float(np.max(np.abs(plan.sum(axis=1) - source_mass)))
    column_residual = float(np.max(np.abs(plan.sum(axis=0) - target_mass)))
    scale_difference = float(np.max(np.abs(plan - scaled_plan)))
    shift_difference = float(np.max(np.abs(plan - shifted_plan)))
    minimum_plan_entry = float(np.min(plan))
    certificates = {
        "source_marginal": row_residual <= 1.0e-10,
        "target_marginal": column_residual <= 1.0e-10,
        "strict_numeric_positivity": minimum_plan_entry > 0.0,
        "primal_dual_agreement": abs(float(baseline["primal_dual_gap"])) <= 1.0e-10,
        "simultaneous_cost_epsilon_scaling_invariance": scale_difference <= 1.0e-10,
        "additive_cost_shift_invariance": shift_difference <= 1.0e-9,
        "naive_shifted_kernel_underflows_completely": int(np.count_nonzero(naive_shifted_kernel == 0.0)) == cost.size,
        "log_domain_shifted_problem_still_converges": float(shifted["marginal_residual"]) <= 1.0e-10,
    }
    failed = [name for name, passed in certificates.items() if not passed]
    if failed:
        raise RuntimeError(f"Sertifikat transportasi entropik gagal: {failed}")
    return {
        "certificates": certificates,
        "row_marginal_residual": row_residual,
        "column_marginal_residual": column_residual,
        "minimum_plan_entry": minimum_plan_entry,
        "primal_dual_gap": float(baseline["primal_dual_gap"]),
        "scaled_plan_max_abs_difference": scale_difference,
        "shifted_plan_max_abs_difference": shift_difference,
        "naive_shifted_kernel_zero_count": int(np.count_nonzero(naive_shifted_kernel == 0.0)),
        "naive_shifted_kernel_entry_count": int(cost.size),
    }


def write_csv(
    source_points: np.ndarray,
    target_points: np.ndarray,
    source_mass: np.ndarray,
    target_mass: np.ndarray,
    cost: np.ndarray,
    baseline: dict[str, object],
    scaled: dict[str, object],
    shifted: dict[str, object],
) -> None:
    plan = np.asarray(baseline["plan"])
    scaled_plan = np.asarray(scaled["plan"])
    shifted_plan = np.asarray(shifted["plan"])
    log_plan = np.asarray(baseline["log_plan"])
    fields = [
        "source_index",
        "target_index",
        "source_point",
        "target_point",
        "source_mass",
        "target_mass",
        "cost",
        "plan",
        "log_plan",
        "scaled_plan",
        "shifted_plan",
    ]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for i in range(cost.shape[0]):
            for j in range(cost.shape[1]):
                writer.writerow(
                    {
                        "source_index": i,
                        "target_index": j,
                        "source_point": float(source_points[i]),
                        "target_point": float(target_points[j]),
                        "source_mass": float(source_mass[i]),
                        "target_mass": float(target_mass[j]),
                        "cost": float(cost[i, j]),
                        "plan": float(plan[i, j]),
                        "log_plan": float(log_plan[i, j]),
                        "scaled_plan": float(scaled_plan[i, j]),
                        "shifted_plan": float(shifted_plan[i, j]),
                    }
                )


def write_svg(plan: np.ndarray) -> None:
    rows, columns = plan.shape
    cell = 48
    left, top = 78, 52
    width = left + columns * cell + 32
    height = top + rows * cell + 62
    maximum = float(np.max(plan))
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Matriks kopling Sinkhorn log-domain</title>',
        '<desc id="desc">Peta panas massa transportasi optimal terentropi; nilai numerik lengkap tersedia dalam CSV dan JSON.</desc>',
        '<rect width="100%" height="100%" fill="white" />',
        '<text x="18" y="24" font-family="sans-serif" font-size="16">Massa kopling</text>',
    ]
    for i in range(rows):
        elements.append(f'<text x="{left-12}" y="{top+i*cell+30}" text-anchor="end" font-family="sans-serif" font-size="12">a{i}</text>')
        for j in range(columns):
            fraction = float(plan[i, j]) / maximum if maximum else 0.0
            shade = int(round(248 - 170 * math_sqrt(fraction)))
            fill = f"rgb({shade},{min(252, shade+20)},{255})"
            x, y = left + j * cell, top + i * cell
            elements.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="#667" />')
            elements.append(f'<text x="{x+cell/2:.1f}" y="{y+cell/2+4:.1f}" text-anchor="middle" font-family="sans-serif" font-size="9">{plan[i,j]:.2g}</text>')
    for j in range(columns):
        elements.append(f'<text x="{left+j*cell+cell/2:.1f}" y="{top+rows*cell+22}" text-anchor="middle" font-family="sans-serif" font-size="12">b{j}</text>')
    elements.append("</svg>\n")
    SVG_PATH.write_text("\n".join(elements), encoding="utf-8", newline="\n")


def math_sqrt(value: float) -> float:
    return float(np.sqrt(max(value, 0.0)))


def file_record(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": path.name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def serializable_run(run: dict[str, object]) -> dict[str, object]:
    return {
        "iterations": int(run["iterations"]),
        "marginal_residual": float(run["marginal_residual"]),
        "primal": float(run["primal"]),
        "dual": float(run["dual"]),
        "primal_dual_gap": float(run["primal_dual_gap"]),
        "history": [[int(k), float(value)] for k, value in run["history"]],
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    source_points = np.sort(rng.uniform(-1.0, 1.0, size=6))
    target_points = np.sort(rng.uniform(-1.0, 1.0, size=7))
    source_mass = rng.uniform(0.7, 1.3, size=source_points.size)
    target_mass = rng.uniform(0.7, 1.3, size=target_points.size)
    source_mass /= source_mass.sum()
    target_mass /= target_mass.sum()
    cost = (source_points[:, None] - target_points[None, :]) ** 2

    baseline = sinkhorn_log(source_mass, target_mass, cost, EPSILON)
    scaled = sinkhorn_log(
        source_mass,
        target_mass,
        SCALING_FACTOR * cost,
        SCALING_FACTOR * EPSILON,
    )
    shifted = sinkhorn_log(
        source_mass,
        target_mass,
        cost + UNDERFLOW_OFFSET,
        EPSILON,
    )
    validation = validate(source_mass, target_mass, cost, baseline, scaled, shifted)
    write_csv(
        source_points,
        target_points,
        source_mass,
        target_mass,
        cost,
        baseline,
        scaled,
        shifted,
    )
    write_svg(np.asarray(baseline["plan"]))
    report = {
        "schema": "o015-original-03-transportasi-entropik-v1",
        "result": "pass",
        "seed": SEED,
        "configuration": {
            "epsilon": EPSILON,
            "tolerance": TOLERANCE,
            "maximum_iterations": MAX_ITERATIONS,
            "scaling_factor": SCALING_FACTOR,
            "underflow_cost_offset": UNDERFLOW_OFFSET,
            "source_size": int(source_points.size),
            "target_size": int(target_points.size),
        },
        "data": {
            "source_points": source_points.tolist(),
            "target_points": target_points.tolist(),
            "source_mass": source_mass.tolist(),
            "target_mass": target_mass.tolist(),
        },
        "runs": {
            "baseline": serializable_run(baseline),
            "simultaneously_scaled_cost_and_epsilon": serializable_run(scaled),
            "additively_shifted_cost": serializable_run(shifted),
        },
        "validation": validation,
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
