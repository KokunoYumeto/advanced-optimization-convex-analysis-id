from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "qa/PENN_CH04_SOLVER_RESULTS.json"
TARGET = ROOT / "source/id-ID/penn-04-pencarian-garis-hampiran-dan-konvergensi-id.tex"
LEDGER = ROOT / "qa/PENN_CH04_PROPOSED_LEDGER.jsonl"
TOL = 2.0e-12

EXPECTED_TARGET = {
    "bytes": 33313,
    "lines": 613,
    "sha256": "c5c0f09d38454177e61c2a97c9beef07771d5f4f715cc7a4a81a871ff54ced8f",
}
EXPECTED_LEDGER = {
    "bytes": 10055,
    "lines": 13,
    "sha256": "fa9c5c0b097b7349a959ca6c1c9c797fc0ed2ea61e91148badec62bb239b7bbd",
}


def gate(results: list[dict[str, object]], name: str, passed: bool, detail: dict[str, object]) -> None:
    results.append({"gate": name, "pass": bool(passed), "detail": detail})


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "lines": len(data.splitlines()),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def radial_f(point: np.ndarray) -> float:
    radius_sq = float(point @ point)
    return math.exp(-radius_sq / 10.0) * math.cos(radius_sq)


def radial_grad(point: np.ndarray) -> np.ndarray:
    radius_sq = float(point @ point)
    factor = math.exp(-radius_sq / 10.0)
    return factor * (-0.2 * math.cos(radius_sq) - 2.0 * math.sin(radius_sq)) * point


def armijo_backtrack(
    function,
    gradient,
    point: np.ndarray,
    direction: np.ndarray,
    t0: float,
    beta: float,
    sigma: float,
) -> tuple[float, int]:
    initial = float(function(point))
    slope = float(gradient(point) @ direction)
    step = t0
    iterations = 0
    while float(function(point + step * direction)) < initial + sigma * step * slope:
        step *= beta
        iterations += 1
        if iterations > 100:
            raise RuntimeError("bounded backtracking guard exceeded")
    return step, iterations


def main() -> int:
    results: list[dict[str, object]] = []

    target_id = identity(TARGET)
    ledger_id = identity(LEDGER)
    gate(
        results,
        "pinned_target_identity",
        all(target_id[key] == value for key, value in EXPECTED_TARGET.items()),
        {"expected": EXPECTED_TARGET, "actual": target_id},
    )
    gate(
        results,
        "pinned_proposed_ledger_identity",
        all(ledger_id[key] == value for key, value in EXPECTED_LEDGER.items()),
        {"expected": EXPECTED_LEDGER, "actual": ledger_id},
    )
    ledger_records = [
        json.loads(line)
        for line in LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected_ids = [f"O015-PENN-ADV-{number:04d}" for number in range(25, 38)]
    required_fields = {
        "event_id", "authority", "source", "surface",
        "source_issue", "target_action", "class",
    }
    ledger_ids = [record.get("event_id") for record in ledger_records]
    ledger_schema_ok = (
        ledger_ids == expected_ids
        and len(set(ledger_ids)) == 13
        and all(set(record) == required_fields for record in ledger_records)
        and all(record["authority"] == "o015-penn-math555-v1.0-source" for record in ledger_records)
        and "undefined sigma" in ledger_records[5]["source_issue"]
        and "sigma one" in ledger_records[5]["target_action"]
    )
    gate(
        results,
        "proposed_ledger_schema_event_range_and_sigma_repair",
        ledger_schema_ok,
        {"event_ids": ledger_ids, "record_count": len(ledger_records)},
    )
    target_text = TARGET.read_text(encoding="utf-8")
    semantic_fragments = {
        "shifted_chain_rule": r"\phi'(\delta)=\nabla f(\mathbf{x}_k+\delta\mathbf{p}_k)^T\mathbf{p}_k",
        "capture_neighborhood": r"lingkungan terbuka yang memuat $\mathbf{x}^*$",
        "uniform_B_bounds": r"m\mathbf{I}\preceq\mathbf{B}_k\preceq M\mathbf{I}",
        "correct_example_matrix": r"\mathbf{Q}=\begin{bmatrix}-4&0\\0&-20\end{bmatrix}",
        "uniform_newton_bound": r"E_k\geq\left(\frac12-\sigma_1\right)\mu+o(1)>0",
    }
    fragment_results = {name: fragment in target_text for name, fragment in semantic_fragments.items()}
    layout_and_exclusion_ok = (
        target_text.count(r"\begin{cgalgorithm}[htbp]") == 2
        and r"\begin{cgalgorithm}[p]" not in target_text
        and r"\lstinputlisting" not in target_text
        and "Code/" not in target_text
    )
    gate(
        results,
        "audited_semantic_fragments_layout_and_code_exclusion",
        all(fragment_results.values()) and layout_and_exclusion_ok,
        {"semantic_fragments": fragment_results, "layout_and_exclusion": layout_and_exclusion_ok},
    )

    x0 = np.array([1.0, 1.0])
    p0 = radial_grad(x0)
    sigma1 = 0.15
    sigma2 = 0.5
    step, shrink_count = armijo_backtrack(radial_f, radial_grad, x0, p0, 1.0, 0.5, sigma1)
    phi0 = radial_f(x0)
    phi_step = radial_f(x0 + step * p0)
    dphi0 = float(radial_grad(x0) @ p0)
    dphi_step = float(radial_grad(x0 + step * p0) @ p0)
    armijo_margin = phi_step - phi0 - sigma1 * step * dphi0
    curvature_margin = sigma2 * dphi0 - dphi_step
    gate(
        results,
        "wolfe_ascent_signs",
        dphi0 > 0.0 and armijo_margin >= -TOL and curvature_margin >= -TOL,
        {
            "step": step,
            "shrink_count": shrink_count,
            "phi_prime_zero": dphi0,
            "phi_prime_step": dphi_step,
            "armijo_margin": armijo_margin,
            "curvature_margin": curvature_margin,
        },
    )
    fd_step = 1.0e-6
    finite_difference = (
        radial_f(x0 + (step + fd_step) * p0)
        - radial_f(x0 + (step - fd_step) * p0)
    ) / (2.0 * fd_step)
    chain_rule_error = abs(finite_difference - dphi_step)
    gate(
        results,
        "shifted_line_restriction_chain_rule",
        chain_rule_error < 1.0e-9 and abs(dphi_step - float(radial_grad(x0 + step * p0) @ p0)) < TOL,
        {
            "step": step,
            "finite_difference": finite_difference,
            "shifted_gradient_dot_direction": dphi_step,
            "absolute_error": chain_rule_error,
        },
    )

    def recurrence(value: float) -> float:
        if value > 1.0:
            derivative = -0.4 - 1.6 * value
        elif value < -1.0:
            derivative = 0.4 - 1.6 * value
        else:
            derivative = -2.0 * value
        return value + derivative

    iterative = [-2.0]
    for _ in range(12):
        iterative.append(recurrence(iterative[-1]))
    closed = [
        ((-1.0) ** n) * ((3.0 / 5.0) ** n) * iterative[0]
        + ((-1.0) ** (n + 1)) * (1.0 - (3.0 / 5.0) ** n)
        for n in range(len(iterative))
    ]
    recurrence_error = max(abs(a - b) for a, b in zip(iterative, closed))
    gate(
        results,
        "failure_recurrence_indexing",
        recurrence_error < TOL
        and all((value < 0.0) if n % 2 == 0 else (value > 0.0) for n, value in enumerate(iterative)),
        {
            "maximum_closed_form_error": recurrence_error,
            "last_even_or_odd_pair": [iterative[-2], iterative[-1]],
        },
    )

    rng = np.random.default_rng(55504)
    kantorovich_margins: list[float] = []
    ascent_margins: list[float] = []
    for dimension in (2, 3, 5, 8):
        orthogonal, _ = np.linalg.qr(rng.normal(size=(dimension, dimension)))
        eigenvalues = np.linspace(1.0, float(dimension + 3), dimension)
        positive = orthogonal @ np.diag(eigenvalues) @ orthogonal.T
        negative = -positive
        for _ in range(10):
            vector = rng.normal(size=dimension)
            ratio = float((vector @ vector) ** 2 / ((vector @ positive @ vector) * (vector @ np.linalg.solve(positive, vector))))
            lower = float(4.0 * eigenvalues[0] * eigenvalues[-1] / (eigenvalues[0] + eigenvalues[-1]) ** 2)
            kantorovich_margins.append(ratio - lower)

            gradient = negative @ vector
            delta = float(-(gradient @ gradient) / (gradient @ negative @ gradient))
            next_vector = vector + delta * gradient
            objective = float(0.5 * vector @ negative @ vector)
            next_objective = float(0.5 * next_vector @ negative @ next_vector)
            lam1 = -eigenvalues[0]
            lamn = -eigenvalues[-1]
            rho = abs((lamn - lam1) / (lamn + lam1))
            ascent_margins.append(next_objective - rho * rho * objective)
    gate(
        results,
        "kantorovich_and_exact_ascent_bound",
        min(kantorovich_margins) >= -TOL and min(ascent_margins) >= -TOL,
        {
            "minimum_kantorovich_margin": min(kantorovich_margins),
            "minimum_ascent_bound_margin": min(ascent_margins),
            "witness_count": len(kantorovich_margins),
        },
    )

    endpoint_q = np.diag([-4.0, -20.0])
    endpoint_x = np.array([1.0, 0.0])
    endpoint_g = endpoint_q @ endpoint_x
    endpoint_delta = float(-(endpoint_g @ endpoint_g) / (endpoint_g @ endpoint_q @ endpoint_g))
    endpoint_next = endpoint_x + endpoint_delta * endpoint_g
    endpoint_factor = float(
        1.0
        - (endpoint_g @ endpoint_g) ** 2
        / ((endpoint_g @ endpoint_q @ endpoint_g) * (endpoint_g @ np.linalg.solve(endpoint_q, endpoint_g)))
    )
    gate(
        results,
        "kantorovich_zero_residual_endpoint",
        np.linalg.norm(endpoint_next) < TOL and abs(endpoint_factor) < TOL,
        {
            "delta": endpoint_delta,
            "next_point_norm": float(np.linalg.norm(endpoint_next)),
            "residual_factor": endpoint_factor,
        },
    )

    hessian = np.diag([-4.0, -20.0])
    spectral_condition = float(abs(hessian[1, 1]) / abs(hessian[0, 0]))
    convergence_factor = float((spectral_condition - 1.0) / (spectral_condition + 1.0))
    gate(
        results,
        "quadratic_example_scaling",
        np.array_equal(hessian, np.diag([-4.0, -20.0]))
        and abs(spectral_condition - 5.0) < TOL
        and abs(convergence_factor - 2.0 / 3.0) < TOL,
        {
            "Q": hessian.tolist(),
            "spectral_condition_number": spectral_condition,
            "convergence_factor": convergence_factor,
        },
    )

    m_bound = 0.75
    M_bound = 6.0
    scaling_margins: list[float] = []
    direction_norm_margins: list[float] = []
    for dimension in (2, 4, 7):
        rotation, _ = np.linalg.qr(rng.normal(size=(dimension, dimension)))
        spectrum = np.linspace(m_bound, M_bound, dimension)
        scaling = rotation @ np.diag(spectrum) @ rotation.T
        for _ in range(12):
            gradient = rng.normal(size=dimension)
            direction = np.linalg.solve(scaling, gradient)
            scaling_margins.append(float(gradient @ direction - (gradient @ gradient) / M_bound))
            direction_norm_margins.append(float(np.linalg.norm(gradient) / m_bound - np.linalg.norm(direction)))
    gate(
        results,
        "uniform_spd_scaling_is_gradient_related",
        min(scaling_margins) >= -TOL and min(direction_norm_margins) >= -TOL,
        {
            "m": m_bound,
            "M": M_bound,
            "witness_count": len(scaling_margins),
            "minimum_directional_margin": min(scaling_margins),
            "minimum_norm_bound_margin": min(direction_norm_margins),
        },
    )

    def concave(value: float) -> float:
        return -0.5 * value * value - 0.25 * value**4

    def concave_grad(value: float) -> float:
        return -value - value**3

    def concave_hess(value: float) -> float:
        return -1.0 - 3.0 * value * value

    x = 0.8
    errors = [abs(x)]
    accepted_units: list[bool] = []
    for _ in range(8):
        direction = -concave_grad(x) / concave_hess(x)
        lhs = concave(x + direction) - concave(x)
        rhs = 0.1 * concave_grad(x) * direction
        accepted_units.append(lhs >= rhs - TOL)
        x += direction
        errors.append(abs(x))
    superlinear_ratios = [errors[index + 1] / errors[index] for index in range(2, 6) if errors[index] > 1.0e-14]
    gate(
        results,
        "newton_direction_and_superlinear_witness",
        all(accepted_units[2:])
        and superlinear_ratios[-1] < superlinear_ratios[0]
        and errors[-1] < 1.0e-12,
        {
            "errors": errors,
            "unit_step_accepted": accepted_units,
            "selected_superlinear_ratios": superlinear_ratios,
        },
    )

    failures = [item["gate"] for item in results if not item["pass"]]
    payload = {
        "schema": "o015-penn-ch04-open-numerical-validation-v2-final",
        "status": "PASS" if not failures else "FAIL",
        "inputs": {"target": target_id, "proposed_ledger": ledger_id},
        "runtime": {"python": "stdlib", "numpy": np.__version__},
        "gates": results,
        "failures": failures,
    }
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    RESULT.write_text(serialized, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "failures": failures,
                "sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
            },
            indent=2,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
