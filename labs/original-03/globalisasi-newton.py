#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-4.0
# Independent computation component for the Bahasa Indonesia D90 edition.
"""Deterministic laboratory for globalization of gradient and Newton methods.

The script writes exactly three sibling artifacts: compact JSON, CSV, and SVG.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
JSON_PATH = HERE / "globalisasi-newton-results.json"
CSV_PATH = HERE / "globalisasi-newton-results.csv"
SVG_PATH = HERE / "globalisasi-newton.svg"

SEED = 20260826
MAX_ITERATIONS = 100
GRADIENT_TOLERANCE = 1.0e-8
ARMIJO_C1 = 1.0e-4
BACKTRACK_FACTOR = 0.5
INITIAL_STEP = 2.5
CURVATURE_FLOOR = 0.25


def objective(point: np.ndarray) -> float:
    x, y = (float(value) for value in point)
    log_cosh = max(float(np.logaddexp(x, -x) - math.log(2.0)), 0.0)
    return float(log_cosh + 0.5 * y * y)


def gradient(point: np.ndarray) -> np.ndarray:
    x, y = (float(value) for value in point)
    return np.array([math.tanh(x), y], dtype=float)


def hessian(point: np.ndarray) -> np.ndarray:
    x = float(point[0])
    sech_squared = max(0.0, 1.0 - math.tanh(x) ** 2)
    return np.diag([sech_squared, 1.0])


def row(
    method: str,
    iteration: int,
    point: np.ndarray,
    step_norm: float,
    alpha: float | None,
    min_eigenvalue: float,
    shift: float,
    armijo: bool | None,
    status: str,
) -> dict[str, object]:
    return {
        "method": method,
        "iteration": iteration,
        "x": float(point[0]),
        "y": float(point[1]),
        "objective": objective(point),
        "gradient_norm": float(np.linalg.norm(gradient(point))),
        "step_norm": float(step_norm),
        "alpha": alpha,
        "minimum_hessian_eigenvalue": float(min_eigenvalue),
        "diagonal_shift": float(shift),
        "armijo": armijo,
        "status": status,
    }


def fixed_gradient(start: np.ndarray) -> list[dict[str, object]]:
    method = "gradien-langkah-tetap"
    start_minimum = float(np.min(np.diag(hessian(start))))
    trace = [row(method, 0, start, 0.0, None, start_minimum, 0.0, None, "mulai")]
    point = start.copy()
    for iteration in range(1, MAX_ITERATIONS + 1):
        direction = -gradient(point)
        step = INITIAL_STEP * direction
        point = point + step
        status = "berjalan"
        if not np.all(np.isfinite(point)) or np.linalg.norm(point) > 1.0e6:
            status = "gagal-langkah-tetap"
        trace.append(
            row(
                method,
                iteration,
                point,
                float(np.linalg.norm(step)),
                INITIAL_STEP,
                float(np.min(np.diag(hessian(point)))),
                0.0,
                None,
                status,
            )
        )
        if status != "berjalan":
            break
    return trace


def backtracking_gradient(start: np.ndarray) -> list[dict[str, object]]:
    method = "gradien-backtracking"
    start_minimum = float(np.min(np.diag(hessian(start))))
    trace = [row(method, 0, start, 0.0, None, start_minimum, 0.0, None, "mulai")]
    point = start.copy()
    for iteration in range(1, MAX_ITERATIONS + 1):
        grad = gradient(point)
        if np.linalg.norm(grad) <= GRADIENT_TOLERANCE:
            trace[-1]["status"] = "konvergen"
            break
        direction = -grad
        directional = float(grad @ direction)
        alpha = INITIAL_STEP
        current = objective(point)
        for _ in range(80):
            candidate = point + alpha * direction
            if objective(candidate) <= current + ARMIJO_C1 * alpha * directional:
                break
            alpha *= BACKTRACK_FACTOR
        else:
            raise RuntimeError("Backtracking gradien tidak menemukan langkah Armijo")
        step = alpha * direction
        point = candidate
        status = (
            "konvergen"
            if np.linalg.norm(gradient(point)) <= GRADIENT_TOLERANCE
            else "berjalan"
        )
        trace.append(
            row(
                method,
                iteration,
                point,
                float(np.linalg.norm(step)),
                alpha,
                float(np.min(np.diag(hessian(point)))),
                0.0,
                True,
                status,
            )
        )
        if status == "konvergen":
            break
    return trace


def pure_newton(start: np.ndarray) -> list[dict[str, object]]:
    method = "newton-murni"
    start_minimum = float(np.min(np.diag(hessian(start))))
    trace = [row(method, 0, start, 0.0, None, start_minimum, 0.0, None, "mulai")]
    point = start.copy()
    for iteration in range(1, 12):
        grad = gradient(point)
        matrix = hessian(point)
        minimum = float(np.min(np.diag(matrix)))
        if minimum <= 1.0e-14:
            trace[-1]["status"] = "gagal-hessian-hampir-singular"
            break
        direction = -np.linalg.solve(matrix, grad)
        if np.linalg.norm(direction) > 1.0e8:
            trace[-1]["status"] = "gagal-ledakan-langkah"
            break
        candidate = point + direction
        status = (
            "kenaikan-objektif"
            if objective(candidate) > objective(point)
            else "berjalan"
        )
        point = candidate
        trace.append(
            row(
                method,
                iteration,
                point,
                float(np.linalg.norm(direction)),
                1.0,
                float(np.min(np.diag(hessian(point)))),
                0.0,
                False,
                status,
            )
        )
        if np.linalg.norm(gradient(point)) <= GRADIENT_TOLERANCE:
            trace[-1]["status"] = "konvergen"
            break
    return trace


def corrected_damped_newton(start: np.ndarray) -> list[dict[str, object]]:
    method = "newton-teredam-terkoreksi"
    start_minimum = float(np.min(np.diag(hessian(start))))
    trace = [row(method, 0, start, 0.0, None, start_minimum, 0.0, None, "mulai")]
    point = start.copy()
    for iteration in range(1, MAX_ITERATIONS + 1):
        grad = gradient(point)
        if np.linalg.norm(grad) <= GRADIENT_TOLERANCE:
            trace[-1]["status"] = "konvergen"
            break
        matrix = hessian(point)
        minimum = float(np.min(np.diag(matrix)))
        shift = max(0.0, CURVATURE_FLOOR - minimum)
        corrected = matrix + shift * np.eye(2)
        direction = -np.linalg.solve(corrected, grad)
        directional = float(grad @ direction)
        if directional >= 0.0:
            raise RuntimeError("Koreksi Hessian gagal menghasilkan arah turun")
        alpha = 1.0
        current = objective(point)
        for _ in range(80):
            candidate = point + alpha * direction
            if objective(candidate) <= current + ARMIJO_C1 * alpha * directional:
                break
            alpha *= BACKTRACK_FACTOR
        else:
            raise RuntimeError("Newton teredam tidak menemukan langkah Armijo")
        step = alpha * direction
        point = candidate
        status = (
            "konvergen"
            if np.linalg.norm(gradient(point)) <= GRADIENT_TOLERANCE
            else "berjalan"
        )
        trace.append(
            row(
                method,
                iteration,
                point,
                float(np.linalg.norm(step)),
                alpha,
                float(np.min(np.diag(matrix))),
                shift,
                True,
                status,
            )
        )
        trace[-1]["corrected_minimum_eigenvalue"] = float(
            np.min(np.linalg.eigvalsh(corrected))
        )
        trace[-1]["directional_derivative"] = directional
        if status == "konvergen":
            break
    return trace


def monotone(trace: list[dict[str, object]], tolerance: float = 1.0e-12) -> bool:
    values = [float(item["objective"]) for item in trace]
    return all(after <= before + tolerance for before, after in zip(values, values[1:]))


def validate(traces: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    fixed = traces["gradien-langkah-tetap"]
    backtracking = traces["gradien-backtracking"]
    pure = traces["newton-murni"]
    corrected = traces["newton-teredam-terkoreksi"]
    pure_increases = sum(
        float(after["objective"]) > float(before["objective"]) + 1.0e-12
        for before, after in zip(pure, pure[1:])
    )
    corrected_rows = [item for item in corrected[1:] if "corrected_minimum_eigenvalue" in item]
    certificates = {
        "fixed_gradient_failure_observed": (
            str(fixed[-1]["status"]).startswith("gagal")
            and float(fixed[-1]["objective"]) > 100.0 * float(fixed[0]["objective"])
        ),
        "pure_newton_failure_observed": (
            pure_increases >= 1
            and str(pure[-1]["status"]).startswith("gagal")
        ),
        "backtracking_armijo_every_step": all(item["armijo"] is True for item in backtracking[1:]),
        "backtracking_objective_monotone": monotone(backtracking),
        "backtracking_converged": float(backtracking[-1]["gradient_norm"]) <= GRADIENT_TOLERANCE,
        "corrected_newton_armijo_every_step": all(item["armijo"] is True for item in corrected[1:]),
        "corrected_newton_objective_monotone": monotone(corrected),
        "corrected_hessian_floor_respected": all(
            float(item["corrected_minimum_eigenvalue"]) >= CURVATURE_FLOOR - 1.0e-13
            for item in corrected_rows
        ),
        "corrected_directions_are_descent": all(
            float(item["directional_derivative"]) < 0.0 for item in corrected_rows
        ),
        "corrected_newton_converged": float(corrected[-1]["gradient_norm"]) <= GRADIENT_TOLERANCE,
    }
    failed = [name for name, passed in certificates.items() if not passed]
    if failed:
        raise RuntimeError(f"Sertifikat globalisasi gagal: {failed}")
    return {
        "certificates": certificates,
        "pure_newton_objective_increase_count": pure_increases,
        "tolerance": GRADIENT_TOLERANCE,
    }


def write_csv(traces: dict[str, list[dict[str, object]]]) -> None:
    fields = [
        "method",
        "iteration",
        "x",
        "y",
        "objective",
        "gradient_norm",
        "step_norm",
        "alpha",
        "minimum_hessian_eigenvalue",
        "diagonal_shift",
        "corrected_minimum_eigenvalue",
        "directional_derivative",
        "armijo",
        "status",
    ]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for method in sorted(traces):
            for item in traces[method]:
                writer.writerow(item)


def svg_polyline(points: list[tuple[float, float]], color: str) -> str:
    encoded = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline points="{encoded}" fill="none" stroke="{color}" stroke-width="2" />'


def write_svg(traces: dict[str, list[dict[str, object]]]) -> None:
    width, height = 760, 420
    left, right, top, bottom = 72, 24, 28, 58
    plot_width, plot_height = width - left - right, height - top - bottom
    all_logs = [
        math.log10(max(float(item["objective"]), 1.0e-16))
        for trace in traces.values()
        for item in trace
    ]
    ymin, ymax = min(all_logs), max(all_logs)
    span = max(ymax - ymin, 1.0)
    max_iteration = max(int(item["iteration"]) for trace in traces.values() for item in trace)
    colors = {
        "gradien-langkah-tetap": "#b33a3a",
        "gradien-backtracking": "#2b6cb0",
        "newton-murni": "#9c6b18",
        "newton-teredam-terkoreksi": "#23835b",
    }
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Perbandingan globalisasi metode gradien dan Newton</title>',
        '<desc id="desc">Kurva logaritma objektif memperlihatkan kegagalan langkah tetap dan Newton murni serta pemulihan oleh backtracking dan koreksi Hessian.</desc>',
        '<rect width="100%" height="100%" fill="white" />',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#222" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#222" />',
        f'<text x="{width/2:.1f}" y="{height-14}" text-anchor="middle" font-family="sans-serif" font-size="14">Iterasi</text>',
        f'<text x="18" y="{height/2:.1f}" transform="rotate(-90 18 {height/2:.1f})" text-anchor="middle" font-family="sans-serif" font-size="14">log10 objektif</text>',
    ]
    for index, (method, trace) in enumerate(traces.items()):
        points = []
        for item in trace:
            x = left + plot_width * int(item["iteration"]) / max(max_iteration, 1)
            log_value = math.log10(max(float(item["objective"]), 1.0e-16))
            y = top + plot_height * (ymax - log_value) / span
            points.append((x, y))
        elements.append(svg_polyline(points, colors[method]))
        legend_y = 28 + 20 * index
        elements.append(f'<line x1="430" y1="{legend_y}" x2="455" y2="{legend_y}" stroke="{colors[method]}" stroke-width="3" />')
        elements.append(f'<text x="462" y="{legend_y+5}" font-family="sans-serif" font-size="12">{method}</text>')
    elements.append("</svg>\n")
    SVG_PATH.write_text("\n".join(elements), encoding="utf-8", newline="\n")


def file_record(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": path.name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def main() -> None:
    rng = np.random.default_rng(SEED)
    start = np.array([3.0, 2.0], dtype=float) + rng.normal(0.0, 1.0e-3, size=2)
    traces = {
        "gradien-langkah-tetap": fixed_gradient(start),
        "gradien-backtracking": backtracking_gradient(start),
        "newton-murni": pure_newton(start),
        "newton-teredam-terkoreksi": corrected_damped_newton(start),
    }
    validation = validate(traces)
    write_csv(traces)
    write_svg(traces)
    summary = {
        name: {
            "iterations": int(trace[-1]["iteration"]),
            "status": trace[-1]["status"],
            "final_objective": trace[-1]["objective"],
            "final_gradient_norm": trace[-1]["gradient_norm"],
        }
        for name, trace in traces.items()
    }
    report = {
        "schema": "o015-original-03-globalisasi-newton-v1",
        "result": "pass",
        "seed": SEED,
        "problem": {
            "objective": "log(cosh(x)) + y^2/2",
            "start": start.tolist(),
            "known_minimizer": [0.0, 0.0],
            "known_minimum": 0.0,
        },
        "configuration": {
            "maximum_iterations": MAX_ITERATIONS,
            "gradient_tolerance": GRADIENT_TOLERANCE,
            "fixed_and_initial_gradient_step": INITIAL_STEP,
            "armijo_c1": ARMIJO_C1,
            "backtrack_factor": BACKTRACK_FACTOR,
            "corrected_hessian_eigenvalue_floor": CURVATURE_FLOOR,
        },
        "summary": summary,
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
