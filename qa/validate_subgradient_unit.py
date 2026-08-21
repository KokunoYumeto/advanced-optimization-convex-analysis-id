"""Deterministic open-solver checks for the Indonesian Habring subgradient unit."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import LinearConstraint, linprog, minimize


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "qa" / "SUBGRADIENT_SOLVER_RESULTS.json"
TOL = 2.0e-7


def check_absolute_value_epigraph() -> dict[str, object]:
    # min |x - 1|, written as min t subject to t >= ±(x - 1).
    # Variable order: (x, t).
    result = linprog(
        c=np.array([0.0, 1.0]),
        A_ub=np.array([[1.0, -1.0], [-1.0, -1.0]]),
        b_ub=np.array([1.0, -1.0]),
        bounds=[(None, None), (0.0, None)],
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"HiGHS failed: {result.message}")
    x, t = (float(v) for v in result.x)
    if abs(x - 1.0) > TOL or abs(t) > TOL:
        raise AssertionError(f"unexpected epigraph optimum: x={x}, t={t}")
    # At x=1, ∂|x-1|=[-1,1], which contains zero.
    return {
        "solver": "scipy.optimize.linprog(method='highs')",
        "status": str(result.message),
        "x": x,
        "t": t,
        "objective": float(result.fun),
        "fermat_certificate": "0 in [-1, 1]",
    }


def check_l1_composite() -> dict[str, object]:
    # Validate the chapter's model 0.5||Ax-b||_2^2 + λ||x||_1.
    # Variable order: (x_1, x_2, t_1, t_2), with t_i >= |x_i|.
    A = np.diag([1.0, 2.0])
    b = np.array([2.0, 1.0])
    lam = 0.5

    def objective(z: np.ndarray) -> float:
        x = z[:2]
        t = z[2:]
        residual = A @ x - b
        return float(0.5 * residual @ residual + lam * np.sum(t))

    # x_i - t_i <= 0 and -x_i - t_i <= 0.
    matrix = np.array(
        [
            [1.0, 0.0, -1.0, 0.0],
            [-1.0, 0.0, -1.0, 0.0],
            [0.0, 1.0, 0.0, -1.0],
            [0.0, -1.0, 0.0, -1.0],
        ]
    )
    constraint = LinearConstraint(matrix, -np.inf, 0.0)
    result = minimize(
        objective,
        x0=np.array([1.0, 0.25, 1.0, 0.25]),
        method="SLSQP",
        constraints=[constraint],
        bounds=[(None, None), (None, None), (0.0, None), (0.0, None)],
        options={"ftol": 1.0e-12, "maxiter": 500},
    )
    if not result.success:
        raise RuntimeError(f"SLSQP failed: {result.message}")

    x = np.asarray(result.x[:2], dtype=float)
    t = np.asarray(result.x[2:], dtype=float)
    expected = np.array([1.5, 0.375])
    if np.max(np.abs(x - expected)) > 2.0e-6:
        raise AssertionError(f"unexpected l1-composite optimum: {x}")
    if np.max(np.abs(t - np.abs(x))) > 2.0e-6:
        raise AssertionError(f"epigraph variables are not tight: x={x}, t={t}")

    subgradient = np.sign(x)
    certificate = A.T @ (A @ x - b) + lam * subgradient
    if np.max(np.abs(certificate)) > 2.0e-6:
        raise AssertionError(f"subgradient certificate failed: {certificate}")

    return {
        "solver": "scipy.optimize.minimize(method='SLSQP')",
        "status": str(result.message),
        "x": x.tolist(),
        "t": t.tolist(),
        "expected_x": expected.tolist(),
        "objective": objective(result.x),
        "optimality_residual_inf": float(np.max(np.abs(certificate))),
        "certificate": "A.T @ (A @ x - b) + lambda * sign(x) = 0",
    }


def main() -> None:
    payload = {
        "schema": "o015-subgradient-solver-check-v1",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "checks": {
            "absolute_value_epigraph": check_absolute_value_epigraph(),
            "l1_composite": check_l1_composite(),
        },
        "result": "pass",
    }
    RESULT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
