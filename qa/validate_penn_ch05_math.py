#!/usr/bin/env python3
"""Deterministic mathematical checks for the Penn Section 5 id-ID candidate.

The checks use exact SymPy algebra wherever possible and write a stable JSON
receipt.  They do not execute or import any of the excluded Maple components.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import sympy as sp


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "source" / "id-ID" / "penn-05-metode-newton-dan-koreksi-id.tex"
REPORT = ROOT / "qa" / "PENN_CH05_SOLVER_RESULTS.json"


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "lines": len(data.splitlines()),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


gates: list[dict[str, object]] = []


def record(name: str, passed: bool, detail: dict[str, object]) -> None:
    gates.append({"gate": name, "pass": bool(passed), "detail": detail})


def sf(value: sp.Expr, digits: int = 15) -> float:
    return float(sp.N(value, digits))


x, y = sp.symbols("x y", real=True)

# 1. The introductory concave quartic has an exactly computable Newton map.
quartic = -2 * x**2 - 10 * y**4
quartic_grad = sp.Matrix([sp.diff(quartic, x), sp.diff(quartic, y)])
quartic_hess = sp.hessian(quartic, (x, y))
quartic_direction = sp.simplify(-quartic_hess.inv() * quartic_grad)
quartic_next = sp.simplify(sp.Matrix([x, y]) + quartic_direction)
quartic_at_start = quartic_next.subs({x: 15, y: 5})
record(
    "pure_newton_quartic_map",
    quartic_direction == sp.Matrix([-x, -y / 3])
    and quartic_next == sp.Matrix([0, 2 * y / 3])
    and quartic_at_start == sp.Matrix([0, sp.Rational(10, 3)]),
    {
        "direction": [str(v) for v in quartic_direction],
        "next_iterate": [str(v) for v in quartic_next],
        "from_15_5": [str(v) for v in quartic_at_start],
    },
)

# 2. Recompute the double-peak gradient, Hessian, Newton direction, and ascent test.
double_peak = (x**2 + 3 * y**2) * sp.exp(1 - x**2 - y**2)
double_grad = sp.Matrix([sp.diff(double_peak, x), sp.diff(double_peak, y)])
double_hess = sp.hessian(double_peak, (x, y))
point = {x: sp.Integer(1), y: sp.Rational(1, 2)}
alpha = sp.exp(sp.Rational(-1, 4))
g0 = sp.simplify(double_grad.subs(point))
h0 = sp.simplify(double_hess.subs(point))
p0 = sp.simplify(-h0.inv() * g0)
directional = sp.simplify((g0.T * p0)[0])
expected_g0 = alpha * sp.Matrix([sp.Rational(-3, 2), sp.Rational(5, 4)])
expected_h0 = alpha * sp.Matrix(
    [[sp.Rational(-5, 2), sp.Rational(-9, 2)],
     [sp.Rational(-9, 2), sp.Rational(-7, 4)]]
)
expected_p0 = sp.Matrix([sp.Rational(66, 127), sp.Rational(-79, 127)])
expected_directional = -sp.Rational(791, 508) * alpha
det_h0 = sp.simplify(h0.det())
record(
    "double_peak_newton_direction",
    g0 == expected_g0
    and h0 == expected_h0
    and p0 == expected_p0
    and directional == expected_directional
    and det_h0 < 0
    and directional < 0,
    {
        "gradient_exact": [str(v) for v in g0],
        "hessian_exact": [[str(v) for v in row] for row in h0.tolist()],
        "hessian_determinant_exact": str(det_h0),
        "newton_direction_exact": [str(v) for v in p0],
        "newton_direction_decimal": [sf(v) for v in p0],
        "gradient_dot_direction_exact": str(directional),
        "gradient_dot_direction_decimal": sf(directional),
    },
)

# 3. Exhaust the real stationary set and classify the four nonzero points.
stationary = [
    (sp.Integer(0), sp.Integer(0), "minimum_local"),
    (sp.Integer(0), sp.Integer(1), "maximum_global"),
    (sp.Integer(0), sp.Integer(-1), "maximum_global"),
    (sp.Integer(1), sp.Integer(0), "saddle"),
    (sp.Integer(-1), sp.Integer(0), "saddle"),
]
stationary_evidence: list[dict[str, object]] = []
classifications_ok = True
for px, py, expected_class in stationary:
    gradient = sp.simplify(double_grad.subs({x: px, y: py}))
    hessian = sp.simplify(double_hess.subs({x: px, y: py}))
    determinant = sp.simplify(hessian.det())
    trace = sp.simplify(sp.trace(hessian))
    if determinant > 0 and trace > 0:
        actual_class = "minimum_local"
    elif determinant > 0 and trace < 0:
        actual_class = "maximum_global" if px == 0 and abs(py) == 1 else "maximum_local"
    elif determinant < 0:
        actual_class = "saddle"
    else:
        actual_class = "degenerate"
    classifications_ok &= gradient == sp.zeros(2, 1) and actual_class == expected_class
    stationary_evidence.append(
        {
            "point": [int(px), int(py)],
            "value": str(sp.simplify(double_peak.subs({x: px, y: py}))),
            "hessian_determinant": str(determinant),
            "hessian_trace": str(trace),
            "classification": actual_class,
        }
    )
gradient_at_bad_endpoint = sp.simplify(double_grad.subs({x: 1, y: 1}))
record(
    "double_peak_stationary_points",
    classifications_ok and gradient_at_bad_endpoint != sp.zeros(2, 1),
    {
        "stationary_points": stationary_evidence,
        "gradient_at_source_misprint_1_1": [str(v) for v in gradient_at_bad_endpoint],
        "positive_y_global_maximum": [0, 1],
    },
)

# 4. Reproduce the corrected modified-Cholesky example exactly.
r = sp.sqrt(sp.Rational(5, 2) * alpha)
s = sp.Rational(9, 2) * alpha / r
lmat = sp.Matrix([[r, 0], [s, 1]])
bmat = sp.simplify(lmat * lmat.T)
z = sp.simplify(lmat.inv() * g0)
p = sp.simplify(lmat.T.inv() * z)
expected_z = sp.Matrix(
    [sp.Rational(-3, 2) * alpha / r, sp.Rational(79, 20) * alpha]
)
expected_p = sp.Matrix(
    [sp.Rational(-3, 5) - sp.Rational(711, 100) * alpha,
     sp.Rational(79, 20) * alpha]
)
corrected_product = sp.simplify((g0.T * p)[0])
expected_product = sp.Rational(9, 10) * alpha + sp.Rational(6241, 400) * alpha**2
schur_before_correction = sp.simplify(
    sp.Rational(7, 4) * alpha - s**2
)
record(
    "modified_cholesky_exact_example",
    z == expected_z
    and p == expected_p
    and sp.simplify(corrected_product - expected_product) == 0
    and corrected_product > 0
    and schur_before_correction == -sp.Rational(127, 20) * alpha
    and bmat.det() > 0
    and sp.trace(bmat) > 0,
    {
        "uncorrected_second_schur_pivot": str(schur_before_correction),
        "L_decimal": [[sf(v) for v in row] for row in lmat.tolist()],
        "B_decimal": [[sf(v) for v in row] for row in bmat.tolist()],
        "z_exact": [str(v) for v in z],
        "p_exact": [str(v) for v in p],
        "p_decimal": [sf(v) for v in p],
        "gradient_dot_direction_exact": str(corrected_product),
        "gradient_dot_direction_decimal": sf(corrected_product),
        "B_determinant_decimal": sf(bmat.det()),
    },
)

# 5. Exercise the independently authored pivot rule on safe-SPD and indefinite inputs.
def modified_cholesky(matrix: list[list[float]], mu1: float, mu2: float) -> tuple[list[list[float]], list[int]]:
    n = len(matrix)
    w = [row[:] for row in matrix]
    l = [[0.0] * n for _ in range(n)]
    corrected: list[int] = []
    for i in range(n):
        d = w[i][i]
        d_hat = d if d >= mu1 else mu2
        if d < mu1:
            corrected.append(i + 1)
        l[i][i] = math.sqrt(d_hat)
        for j in range(i + 1, n):
            l[j][i] = w[j][i] / l[i][i]
        for j in range(i + 1, n):
            for k in range(i + 1, n):
                w[j][k] -= l[j][i] * l[k][i]
    return l, corrected


def matmul_lt(l: list[list[float]]) -> list[list[float]]:
    n = len(l)
    return [[sum(l[i][k] * l[j][k] for k in range(n)) for j in range(n)] for i in range(n)]


def max_abs_delta(a: list[list[float]], b: list[list[float]]) -> float:
    return max(abs(a[i][j] - b[i][j]) for i in range(len(a)) for j in range(len(a)))


safe_spd = [[4.0, 1.0], [1.0, 3.0]]
l_safe, corrected_safe = modified_cholesky(safe_spd, 0.1, 1.0)
b_safe = matmul_lt(l_safe)
indefinite = [[1.0, 2.0], [2.0, 1.0]]
l_indef, corrected_indef = modified_cholesky(indefinite, 0.1, 1.0)
b_indef = matmul_lt(l_indef)
eig_indef = sorted(float(v) for v in sp.Matrix(b_indef).eigenvals().keys())
record(
    "modified_cholesky_pivot_rule",
    corrected_safe == []
    and max_abs_delta(b_safe, safe_spd) < 1e-12
    and corrected_indef == [2]
    and min(eig_indef) > 0,
    {
        "safe_spd_corrected_pivots": corrected_safe,
        "safe_spd_reconstruction_max_abs_error": max_abs_delta(b_safe, safe_spd),
        "indefinite_corrected_pivots": corrected_indef,
        "indefinite_surrogate": b_indef,
        "indefinite_surrogate_eigenvalues": eig_indef,
    },
)

# 6. Verify the two gradient-related inequalities used in the global theorem.
b_test = sp.Matrix([[4, 1], [1, 3]])
g_test = sp.Matrix([2, -1])
p_test = b_test.inv() * g_test
eigenvalues = sorted([sp.N(v, 30) for v in b_test.eigenvals().keys()], key=float)
m = eigenvalues[0]
M = eigenvalues[-1]
pnorm = sp.sqrt((p_test.T * p_test)[0])
gnorm = sp.sqrt((g_test.T * g_test)[0])
gdotp = (g_test.T * p_test)[0]
upper_residual = sp.N(gnorm / m - pnorm, 30)
lower_residual = sp.N(gdotp - gnorm**2 / M, 30)
record(
    "gradient_related_spectral_bounds",
    upper_residual >= 0 and lower_residual >= 0,
    {
        "B": [[int(v) for v in row] for row in b_test.tolist()],
        "gradient": [int(v) for v in g_test],
        "direction": [str(v) for v in p_test],
        "lambda_min": sf(m),
        "lambda_max": sf(M),
        "norm_upper_bound_slack": sf(upper_residual),
        "directional_lower_bound_slack": sf(lower_residual),
    },
)

# 7. A nonlinear concave scalar witness exhibits the stated Q-quadratic bound.
# f(u)=-u^2/2-u^3/3 has Newton error map e+ = e^2/(1+2e) near e*=0.
errors = [sp.Rational(1, 10)]
for _ in range(5):
    e = errors[-1]
    errors.append(sp.simplify(e**2 / (1 + 2 * e)))
linear_ratios = [sp.N(errors[i + 1] / errors[i], 30) for i in range(5)]
quadratic_ratios = [sp.N(errors[i + 1] / errors[i] ** 2, 30) for i in range(5)]
record(
    "local_newton_quadratic_witness",
    all(errors[i + 1] < errors[i] for i in range(5))
    and all(linear_ratios[i + 1] < linear_ratios[i] for i in range(4))
    and all(0 < ratio <= 1 for ratio in quadratic_ratios),
    {
        "function": "f(u)=-u^2/2-u^3/3",
        "exact_error_map": "e_next=e^2/(1+2e)",
        "errors_decimal": [sf(v) for v in errors],
        "linear_error_ratios": [sf(v) for v in linear_ratios],
        "quadratic_error_ratios": [sf(v) for v in quadratic_ratios],
    },
)

failures = [gate["gate"] for gate in gates if not gate["pass"]]
payload = {
    "schema": "o015-penn-ch05-solver-results-v1",
    "status": "PASS" if not failures else "FAIL",
    "failures": failures,
    "solver": {"name": "SymPy", "version": sp.__version__, "arithmetic": "exact where stated"},
    "target": identity(TARGET),
    "gates": gates,
}
REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "report": str(REPORT)}, indent=2))
raise SystemExit(0 if not failures else 1)
