#!/usr/bin/env python3
"""Deterministic open-computation lab for O015 Original-02.

The frozen two-dimensional inclusion combines a strongly monotone linear map
with a nonzero skew part and the subdifferential of the l1 norm.  It compares
forward-backward inside and outside its proved step range with
Douglas-Rachford splitting.  NumPy supplies the open linear solver; an explicit
nine-pattern active-set enumeration supplies an independent reference point.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "results.json"
CSV_PATH = OUT_DIR / "results.csv"
SVG_PATH = OUT_DIR / "residual.svg"

MU = 1.00
OMEGA = 1.50
LAMBDA = 0.25
B_VECTOR = np.array([1.20, -0.70], dtype=np.float64)
X0 = np.array([2.50, -2.00], dtype=np.float64)
Y0 = np.array([2.50, -2.00], dtype=np.float64)
FB_STABLE_GAMMA = 0.40
FB_DIAGNOSTIC_GAMMA = 0.90
DR_GAMMA = 0.70
ITERATIONS = 200
CHECKPOINTS = (0, 1, 2, 5, 10, 20, 40, 80, 120, 200)
SKEW_GAMMA = 0.60
SKEW_STEPS = 30
SKEW_X0 = np.array([1.25, -0.75], dtype=np.float64)

MATRIX = np.array([[MU, -OMEGA], [OMEGA, MU]], dtype=np.float64)
BETA = MU / (MU * MU + OMEGA * OMEGA)
FB_UPPER_BOUND = 2.0 * BETA


def soft_threshold(x: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(x) * np.maximum(np.abs(x) - threshold, 0.0)


def active_set_reference() -> tuple[np.ndarray, tuple[int, int], np.ndarray]:
    """Enumerate sign/zero patterns and return the unique inclusion solution."""
    candidates: list[tuple[np.ndarray, tuple[int, int], np.ndarray]] = []
    for s0 in (-1, 0, 1):
        for s1 in (-1, 0, 1):
            pattern = (s0, s1)
            active = [index for index, sign in enumerate(pattern) if sign]
            zero = [index for index, sign in enumerate(pattern) if not sign]
            x = np.zeros(2, dtype=np.float64)
            if active:
                block = MATRIX[np.ix_(active, active)]
                rhs = B_VECTOR[active] - LAMBDA * np.array(
                    [pattern[index] for index in active], dtype=np.float64
                )
                x[active] = np.linalg.solve(block, rhs)
            if any(x[index] * pattern[index] <= 1e-12 for index in active):
                continue
            residual = MATRIX @ x - B_VECTOR
            if any(abs(residual[index]) > LAMBDA + 1e-11 for index in zero):
                continue
            if any(
                abs(residual[index] + LAMBDA * pattern[index]) > 1e-10
                for index in active
            ):
                continue
            subgradient = np.empty(2, dtype=np.float64)
            for index in range(2):
                if pattern[index]:
                    subgradient[index] = float(pattern[index])
                else:
                    subgradient[index] = -residual[index] / LAMBDA
            candidates.append((x, pattern, subgradient))
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one active-set solution, found {len(candidates)}")
    return candidates[0]


REFERENCE, REFERENCE_PATTERN, REFERENCE_SUBGRADIENT = active_set_reference()


def fixed_point_residual(x: np.ndarray, gamma: float) -> float:
    mapped = soft_threshold(
        x - gamma * (MATRIX @ x - B_VECTOR), gamma * LAMBDA
    )
    return float(np.linalg.norm(x - mapped))


def inclusion_residual(x: np.ndarray) -> float:
    """Tolerance-adjusted distance from zero to Mx-b + lambda*partial ||x||_1."""
    affine = MATRIX @ x - B_VECTOR
    certificate = np.empty(2, dtype=np.float64)
    for index, value in enumerate(x):
        if value > 1e-12:
            certificate[index] = affine[index] + LAMBDA
        elif value < -1e-12:
            certificate[index] = affine[index] - LAMBDA
        else:
            certificate[index] = math.copysign(
                max(abs(affine[index]) - LAMBDA, 0.0), affine[index]
            )
    return float(np.linalg.norm(certificate))


def observation(method: str, iteration: int, x: np.ndarray, gamma: float) -> dict:
    return {
        "method": method,
        "iteration": iteration,
        "x1": float(x[0]),
        "x2": float(x[1]),
        "norm": float(np.linalg.norm(x)),
        "error_to_reference": float(np.linalg.norm(x - REFERENCE)),
        "fixed_point_residual": fixed_point_residual(x, gamma),
        "inclusion_residual": inclusion_residual(x),
    }


def run_forward_backward(name: str, gamma: float) -> list[dict]:
    x = X0.copy()
    rows = []
    for iteration in range(ITERATIONS + 1):
        if iteration in CHECKPOINTS:
            rows.append(observation(name, iteration, x, gamma))
        if iteration < ITERATIONS:
            x = soft_threshold(
                x - gamma * (MATRIX @ x - B_VECTOR), gamma * LAMBDA
            )
    return rows


def resolvent_linear(v: np.ndarray, gamma: float) -> np.ndarray:
    return np.linalg.solve(
        np.eye(2, dtype=np.float64) + gamma * MATRIX,
        v + gamma * B_VECTOR,
    )


def run_douglas_rachford() -> list[dict]:
    y = Y0.copy()
    rows = []
    for iteration in range(ITERATIONS + 1):
        shadow = soft_threshold(y, DR_GAMMA * LAMBDA)
        if iteration in CHECKPOINTS:
            rows.append(
                observation("douglas_rachford", iteration, shadow, DR_GAMMA)
            )
        if iteration < ITERATIONS:
            reflected = 2.0 * shadow - y
            other = resolvent_linear(reflected, DR_GAMMA)
            y = y + other - shadow
    return rows


def skew_diagnostic() -> dict:
    """Compare exact and numerical contraction factors for the unit rotation."""
    rotation = np.array([[0.0, -1.0], [1.0, 0.0]], dtype=np.float64)
    identity = np.eye(2, dtype=np.float64)
    forward_map = identity - SKEW_GAMMA * rotation
    extragradient_map = (
        (1.0 - SKEW_GAMMA * SKEW_GAMMA) * identity
        - SKEW_GAMMA * rotation
    )
    resolvent_map = np.linalg.inv(identity + SKEW_GAMMA * rotation)
    exact = {
        "forward": math.sqrt(1.0 + SKEW_GAMMA * SKEW_GAMMA),
        "extragradient": math.sqrt(
            1.0 - SKEW_GAMMA * SKEW_GAMMA + SKEW_GAMMA**4
        ),
        "resolvent": 1.0 / math.sqrt(1.0 + SKEW_GAMMA * SKEW_GAMMA),
    }
    maps = {
        "forward": forward_map,
        "extragradient": extragradient_map,
        "resolvent": resolvent_map,
    }
    methods = {}
    initial_norm = float(np.linalg.norm(SKEW_X0))
    for name, operator in maps.items():
        x = SKEW_X0.copy()
        first = operator @ x
        numerical_factor = float(np.linalg.norm(first) / initial_norm)
        for _ in range(SKEW_STEPS):
            x = operator @ x
        methods[name] = {
            "exact_one_step_factor": exact[name],
            "numerical_one_step_factor": numerical_factor,
            "factor_absolute_error": abs(numerical_factor - exact[name]),
            "final_norm": float(np.linalg.norm(x)),
            "exact_final_norm": initial_norm * exact[name] ** SKEW_STEPS,
        }
        if methods[name]["factor_absolute_error"] > 1e-14:
            raise RuntimeError(f"Skew one-step identity failed for {name}")
        if abs(methods[name]["final_norm"] - methods[name]["exact_final_norm"]) > (
            1e-12 * max(1.0, methods[name]["exact_final_norm"])
        ):
            raise RuntimeError(f"Skew multi-step identity failed for {name}")
    if not methods["forward"]["exact_one_step_factor"] > 1.0:
        raise RuntimeError("Frozen skew forward map is not expansive")
    if not methods["extragradient"]["exact_one_step_factor"] < 1.0:
        raise RuntimeError("Frozen skew extragradient map is not contractive")
    if not methods["resolvent"]["exact_one_step_factor"] < 1.0:
        raise RuntimeError("Frozen skew resolvent map is not contractive")
    return {
        "gamma": SKEW_GAMMA,
        "steps": SKEW_STEPS,
        "initial": SKEW_X0.tolist(),
        "initial_norm": initial_norm,
        "methods": methods,
        "interpretation": (
            "For the monotone 1-Lipschitz skew map, the plain forward step "
            "expands while extragradient and the resolvent contract."
        ),
    }


def make_svg(rows: list[dict]) -> str:
    width, height = 900, 520
    left, right, top, bottom = 88, 35, 42, 74
    plot_w = width - left - right
    plot_h = height - top - bottom
    colors = {
        "forward_backward_stable": "#1f77b4",
        "forward_backward_outside_range": "#c03d3e",
        "douglas_rachford": "#2b8a3e",
    }
    labels = {
        "forward_backward_stable": "Maju--mundur: langkah diterima",
        "forward_backward_outside_range": "Maju--mundur: di luar jaminan",
        "douglas_rachford": "Douglas--Rachford",
    }
    grouped = {
        method: [row for row in rows if row["method"] == method]
        for method in colors
    }
    positive = [
        max(float(row["inclusion_residual"]), 1e-16)
        for row in rows
        if math.isfinite(float(row["inclusion_residual"]))
    ]
    log_min = min(-14.0, math.floor(math.log10(min(positive))))
    log_max = max(1.0, math.ceil(math.log10(max(positive))))

    def point(iteration: int, residual: float) -> tuple[float, float]:
        x = left + plot_w * iteration / ITERATIONS
        value = min(max(math.log10(max(residual, 1e-16)), log_min), log_max)
        y = top + plot_h * (log_max - value) / (log_max - log_min)
        return x, y

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Residu inklusi operator monoton</title>',
        '<desc id="desc">Perbandingan residu maju--mundur dengan langkah diterima, langkah di luar jaminan, dan Douglas--Rachford.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width/2}" y="24" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#182235">Residu inklusi terhadap iterasi</text>',
    ]
    for exponent in range(int(log_min), int(log_max) + 1, 2):
        y = point(0, 10.0**exponent)[1]
        parts.append(
            f'<line x1="{left}" x2="{left+plot_w}" y1="{y:.2f}" y2="{y:.2f}" stroke="#d8dee8" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#536176">10^{exponent}</text>'
        )
    for iteration in (0, 50, 100, 150, 200):
        x = point(iteration, 1.0)[0]
        parts.append(
            f'<line x1="{x:.2f}" x2="{x:.2f}" y1="{top}" y2="{top+plot_h}" stroke="#eef1f5" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{top+plot_h+24}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#536176">{iteration}</text>'
        )
    parts.extend(
        [
            f'<line x1="{left}" x2="{left}" y1="{top}" y2="{top+plot_h}" stroke="#182235" stroke-width="1.5"/>',
            f'<line x1="{left}" x2="{left+plot_w}" y1="{top+plot_h}" y2="{top+plot_h}" stroke="#182235" stroke-width="1.5"/>',
            f'<text x="{left+plot_w/2}" y="{height-24}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#182235">Iterasi</text>',
            f'<text x="22" y="{top+plot_h/2}" transform="rotate(-90 22 {top+plot_h/2})" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#182235">Residu inklusi (skala log)</text>',
        ]
    )
    for method, method_rows in grouped.items():
        points = " ".join(
            f'{point(int(row["iteration"]), float(row["inclusion_residual"]))[0]:.2f},{point(int(row["iteration"]), float(row["inclusion_residual"]))[1]:.2f}'
            for row in method_rows
        )
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{colors[method]}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        for row in method_rows:
            x, y = point(int(row["iteration"]), float(row["inclusion_residual"]))
            parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.2" fill="{colors[method]}"/>'
            )
    legend_x, legend_y = left + 18, top + 18
    parts.append(
        f'<rect x="{legend_x-10}" y="{legend_y-15}" width="345" height="82" rx="5" fill="#ffffff" fill-opacity="0.92" stroke="#cbd5e1"/>'
    )
    for index, method in enumerate(colors):
        y = legend_y + 24 * index
        parts.append(
            f'<line x1="{legend_x}" x2="{legend_x+26}" y1="{y}" y2="{y}" stroke="{colors[method]}" stroke-width="3"/>'
        )
        parts.append(
            f'<text x="{legend_x+36}" y="{y+4}" font-family="Arial, sans-serif" font-size="12" fill="#182235">{labels[method]}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    if not FB_STABLE_GAMMA < FB_UPPER_BOUND:
        raise RuntimeError("Frozen stable step is outside the proved range")
    if not FB_DIAGNOSTIC_GAMMA > FB_UPPER_BOUND:
        raise RuntimeError("Frozen diagnostic step is not outside the proved range")
    reference_residual = inclusion_residual(REFERENCE)
    if reference_residual > 1e-11:
        raise RuntimeError(f"Active-set reference residual too large: {reference_residual}")

    rows = (
        run_forward_backward("forward_backward_stable", FB_STABLE_GAMMA)
        + run_forward_backward(
            "forward_backward_outside_range", FB_DIAGNOSTIC_GAMMA
        )
        + run_douglas_rachford()
    )
    final = {row["method"]: row for row in rows if row["iteration"] == ITERATIONS}
    if final["forward_backward_stable"]["inclusion_residual"] > 1e-10:
        raise RuntimeError("Stable forward-backward did not reach the frozen tolerance")
    if final["douglas_rachford"]["inclusion_residual"] > 1e-10:
        raise RuntimeError("Douglas-Rachford did not reach the frozen tolerance")
    outside_initial = next(
        row
        for row in rows
        if row["method"] == "forward_backward_outside_range"
        and row["iteration"] == 0
    )
    if not (
        final["forward_backward_outside_range"]["inclusion_residual"]
        > outside_initial["inclusion_residual"]
    ):
        raise RuntimeError("Outside-range diagnostic did not exhibit residual growth")

    resolvent_probe = np.array([0.7, -1.1], dtype=np.float64)
    resolved = resolvent_linear(resolvent_probe, DR_GAMMA)
    resolvent_identity_error = float(
        np.linalg.norm(
            resolved
            + DR_GAMMA * (MATRIX @ resolved - B_VECTOR)
            - resolvent_probe
        )
    )
    if resolvent_identity_error > 1e-12:
        raise RuntimeError("Linear resolvent identity failed")
    skew = skew_diagnostic()

    payload = {
        "schema": "o015-original-02-monotone-splitting-lab-v1",
        "result": "pass",
        "parameters": {
            "mu": MU,
            "omega": OMEGA,
            "lambda": LAMBDA,
            "b": B_VECTOR.tolist(),
            "x0": X0.tolist(),
            "y0": Y0.tolist(),
            "iterations": ITERATIONS,
            "checkpoints": list(CHECKPOINTS),
            "forward_backward_stable_gamma": FB_STABLE_GAMMA,
            "forward_backward_diagnostic_gamma": FB_DIAGNOSTIC_GAMMA,
            "douglas_rachford_gamma": DR_GAMMA,
        },
        "theory": {
            "beta": BETA,
            "forward_backward_upper_bound": FB_UPPER_BOUND,
            "stable_step_inside_open_interval": True,
            "diagnostic_step_outside_proved_interval": True,
        },
        "reference": {
            "method": "complete_active_set_enumeration",
            "pattern": list(REFERENCE_PATTERN),
            "x": REFERENCE.tolist(),
            "subgradient": REFERENCE_SUBGRADIENT.tolist(),
            "inclusion_residual": reference_residual,
        },
        "resolvent_probe": {
            "input": resolvent_probe.tolist(),
            "output": resolved.tolist(),
            "identity_error": resolvent_identity_error,
        },
        "pure_skew_diagnostic": skew,
        "final": final,
        "rows": rows,
        "interpretation": {
            "accepted_methods": [
                "forward_backward_stable",
                "douglas_rachford",
            ],
            "diagnostic_only": "forward_backward_outside_range",
            "claim_boundary": (
                "The outside-range trace is a frozen counterdiagnostic, not a "
                "claim that every step outside the sufficient interval diverges."
            ),
        },
        "dependencies": {
            "python": "standard library",
            "numpy": np.__version__,
        },
        "upstream_contact": False,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    fieldnames = list(rows[0].keys())
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    SVG_PATH.write_text(make_svg(rows), encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "result": "pass",
                "beta": BETA,
                "forward_backward_upper_bound": FB_UPPER_BOUND,
                "reference": REFERENCE.tolist(),
                "final_residuals": {
                    method: values["inclusion_residual"]
                    for method, values in final.items()
                },
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
