from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority/penn-state/source/ClassNotes/Section4.tex"
TARGET = ROOT / "source/id-ID/penn-04-pencarian-garis-hampiran-dan-konvergensi-id.tex"
LEDGER = ROOT / "qa/PENN_CH04_PROPOSED_LEDGER.jsonl"
REPORT = ROOT / "qa/PENN_CH04_STRUCTURE_REPORT.json"
FORMULA_MANIFEST = ROOT / "qa/PENN_CH04_FORMULA_DELTA_MANIFEST.json"
SOURCE_AUTHORITY = ROOT / "00_control/SOURCE_AUTHORITY.json"
OVERLAP_CONTROL = ROOT / "00_control/COVERAGE_OVERLAP.md"
PUBLIC_PDF = ROOT / "authority/penn-state/Math555.pdf"

EXPECTED_IDENTITIES = {
    "source": {
        "bytes": 34684,
        "lines": 469,
        "sha256": "76113034709b5914fa920076f2e882ccf30157e78ce5bdf4593a5d39af1886d5",
    },
    "target": {
        "bytes": 33313,
        "lines": 613,
        "sha256": "c5c0f09d38454177e61c2a97c9beef07771d5f4f715cc7a4a81a871ff54ced8f",
    },
    "proposed_ledger": {
        "bytes": 10055,
        "lines": 13,
        "sha256": "fa9c5c0b097b7349a959ca6c1c9c797fc0ed2ea61e91148badec62bb239b7bbd",
    },
    "public_pdf": {
        "bytes": 4776722,
        "sha256": "f7b99401af875333f3becb591eebf61fac81280768537c20b8a1264d578cb4ff",
    },
}

SEGMENTS = [
    ("P04-S001", "d90.penn.v1.ch04.seg0001", 1, 74),
    ("P04-S002", "d90.penn.v1.ch04.seg0002", 75, 124),
    ("P04-S003", "d90.penn.v1.ch04.seg0003", 125, 206),
    ("P04-S004", "d90.penn.v1.ch04.seg0004", 207, 243),
    ("P04-S005", "d90.penn.v1.ch04.seg0005", 244, 331),
    ("P04-S006", "d90.penn.v1.ch04.seg0006", 332, 363),
    ("P04-S007", "d90.penn.v1.ch04.seg0007", 364, 469),
]

EXPECTED_ENVIRONMENT_COUNTS = {
    "algorithm": 1,
    "bmatrix": 1,
    "cases": 1,
    "cgalgorithm": 2,
    "corollary": 2,
    "definition": 3,
    "displaymath": 12,
    "enumerate*": 1,
    "equation": 49,
    "example": 3,
    "exercise": 4,
    "figure": 5,
    "gather*": 1,
    "lemma": 2,
    "multline": 4,
    "proof": 4,
    "remark": 13,
    "theorem": 4,
}

EXPECTED_LABELS = [
    "eqn:Armijo",
    "fig:ThreeDCos",
    "fig:Phi",
    "fig:WolfeIllustration",
    "lem:WolfeConditions",
    "alg:BackTrace",
    "sec:Convergence",
    "def:GradientRelated",
    "thm:GenConverge",
    "eqn:Lim1",
    "eqn:Lim2",
    "eqn:Lim3",
    "eqn:Lim4",
    "eqn:Lim5",
    "cor:MinArmijo",
    "cor:SymmetricPDConverge",
    "fig:GradDescentFailure",
    "eqn:GradRecurse",
    "lem:Kantorovich",
    "thm:GradientAscentConverge",
    "eqn:FinalEqnGradAscentConverge",
    "alg:GradientAscent",
    "fig:GradientAscent",
    "ex:GradientAscent",
    "eqn:Necessary",
    "eqn:Superlinear",
    "thm:Superlinear",
    "eqn:kbar1",
    "eqn:kbar2",
    "eqn:kbar3",
    "eqn:FinalKbar",
    "eqn:LittleO1",
]

EXPECTED_SOURCE_REF_SEQUENCE_SHA256 = "b8d7d9a3ab4e770cb00bb2edbe2452fb02d313c73b839e5d23b6b78c04ce2c30"
EXPECTED_TARGET_REF_SEQUENCE_SHA256 = "a580820b58f4a387dd089e6faa0ae21c5e701e718b3387e7acf7498959bc627a"
EXPECTED_ENV_SEQUENCE_SHA256 = "aa053b4ce21055fb6adcf491e9cf547d168d9c00df417aefd9ca5aaee49b650d"

ASSETS = {
    "ThreeDCos.pdf": (234150, "e14dc949d3fd7cd7d0593f0352567aa9ac6e66423886113929df9c7feb2eace5"),
    "WolfePhiOfT.pdf": (16923, "221447efe0da804b341570bf3877c842199dd6052b7029eb70cf2edf1aab9a09"),
    "WolfeConditionsIllustrated.pdf": (163565, "b3d2c7c62a79e6bf74ec62089afc773f631f1c62d67e2f8bfd58fb4a078796ec"),
    "ConvergenceFailure.pdf": (11302, "fc5f89515414dcbc704e718e6de62b0bb15785b645bd669c98254dd058a16836"),
    "GradientAscentOut.pdf": (110472, "31cdba8ed1818564289fba9c2c279b48cd0bddc347097261ae8df572953eecc4"),
}

EXCLUDED_CODE = {
    "BackTrace.mpl": (361, 16, "cd0604aaa19b7ecbaef8358a9a6d9d3516b6f6aa9b068e983ff5a180c1b4a09d"),
    "GradientAscent-1.mpl": (1467, 43, "bd9c2521846c183de5c7b2d00af23c828742fb0c6c7301b16cb09794e0cdf8ec"),
    "GradientAscent-2.mpl": (866, 30, "a27c3ee087e55986ad6a938208e63b9ef0b29d101846be12dabc7f087a796824"),
}

EXPECTED_EVENT_IDS = [f"O015-PENN-ADV-{number:04d}" for number in range(25, 38)]

# Only these displayed surfaces contain determined mathematical changes. Other
# determined events are prose, hypothesis, code-replacement, or label-binding
# changes and are bound below to exact non-formula witnesses.
FORMULA_EVENT_BINDINGS = {
    4: ["O015-PENN-ADV-0025"],
    20: ["O015-PENN-ADV-0029"],
    21: ["O015-PENN-ADV-0029"],
    22: ["O015-PENN-ADV-0029"],
    23: ["O015-PENN-ADV-0029"],
    24: ["O015-PENN-ADV-0029"],
    25: ["O015-PENN-ADV-0029"],
    26: ["O015-PENN-ADV-0029"],
    27: ["O015-PENN-ADV-0030"],
    30: ["O015-PENN-ADV-0031"],
    31: ["O015-PENN-ADV-0032"],
    35: ["O015-PENN-ADV-0033"],
    44: ["O015-PENN-ADV-0033"],
    45: ["O015-PENN-ADV-0033"],
    46: ["O015-PENN-ADV-0035"],
    49: ["O015-PENN-ADV-0036"],
    50: ["O015-PENN-ADV-0036"],
    51: ["O015-PENN-ADV-0036"],
    53: ["O015-PENN-ADV-0036"],
    54: ["O015-PENN-ADV-0036"],
    55: ["O015-PENN-ADV-0036"],
    56: ["O015-PENN-ADV-0036"],
    57: ["O015-PENN-ADV-0036"],
    58: ["O015-PENN-ADV-0036"],
    59: ["O015-PENN-ADV-0036"],
    60: ["O015-PENN-ADV-0036"],
}

NON_FORMULA_EVENT_BINDINGS = {
    "O015-PENN-ADV-0026": "vector_path_and_curvature_prose",
    "O015-PENN-ADV-0027": "wolfe_hypotheses_and_backtracking_termination",
    "O015-PENN-ADV-0028": "independent_backtracking_pseudocode",
    "O015-PENN-ADV-0030": "corollary_hypotheses",
    "O015-PENN-ADV-0031": "constant_step_and_subsequence_limits",
    "O015-PENN-ADV-0033": "condition_factor_interpretation",
    "O015-PENN-ADV-0034": "independent_gradient_ascent_pseudocode",
    "O015-PENN-ADV-0035": "quadratic_conditioning_prose",
    "O015-PENN-ADV-0036": "newton_direction_and_uniform_proof_prose",
    "O015-PENN-ADV-0037": "owning_environment_label_binding",
}

WITNESS_SPECS = {
    "O015-PENN-ADV-0025": {
        "source": [r"\phi'(\delta_k) = \nabla f(\mathbf{x}_k)^T\mathbf{p}_k"],
        "target": [r"\phi'(\delta)=\nabla f(\mathbf{x}_k+\delta\mathbf{p}_k)^T\mathbf{p}_k."],
    },
    "O015-PENN-ADV-0026": {
        "source": [r"f(x_0 + t\nabla f(x_0,y_0),y_0 + t\nabla f(x_0,y_0))", "is greater than some constant"],
        "target": [r"\phi(t)=f\!\left(\mathbf{x}_0+t\nabla f(\mathbf{x}_0)\right)", "tidak melebihi konstanta"],
    },
    "O015-PENN-ADV-0027": {
        "source": [r"Suppose $\mathbf{p}_k$ is an ascent direction", "The proof of Lemma"],
        "target": [r"Misalkan $f$ terdiferensialkan secara kontinu", "definisi turunan menyatakan bahwa ketaksamaan ini berlaku"],
    },
    "O015-PENN-ADV-0028": {
        "source": [r"\lstinputlisting{Code/BackTrace.mpl}"],
        "target": [r"\textbf{Masukan:} $\phi$, $t_0>0$, $\beta\in(0,1)$, $\sigma_1\in(0,1)$, dan $\phi'(0)>0$."],
    },
    "O015-PENN-ADV-0029": {
        "source": [r"Assume that $\delta_k$ is chosen to ensure the Armijo rule holds", r"\limsup_{k \to \infty, k\in K}\nabla f(\mathbf{x}_k)^T\mathbf{p}_k > 0"],
        "target": [r"setiap $\delta_k$ dipilih oleh Algoritma \ref{alg:BackTrace}", r"\nabla f(\mathbf{x}_k)^T\mathbf{p}_k\geq\eta", r"\nabla f(\mathbf{x}^+)^T\mathbf{p}^+ \leq\sigma_1"],
    },
    "O015-PENN-ADV-0030": {
        "source": [r"Assume that $\delta_k$ is chosen by maximizing $\phi(\delta_k)$", r"every matrix $\mathbf{B}_k$ is symmetric, positive definite", r"\sigma\hat{\delta}_k"],
        "target": [r"Andaikan suatu pemaksimum eksak berhingga $\delta_k$", r"m\mathbf{I}\preceq\mathbf{B}_k\preceq M\mathbf{I}", r"\sigma_1\hat\delta_k"],
    },
    "O015-PENN-ADV-0031": {
        "source": [r"fix a decreasing step length $\delta_k = 1$", r"x_{k+1} = (-1)^n"],
        "target": [r"tetapkan panjang langkah konstan $\delta_k=1$", r"x_n=(-1)^n", "subsekuens genap menuju $-1$ dan subsekuens ganjil menuju $1$"],
    },
    "O015-PENN-ADV-0032": {
        "source": [r"||\mathbf{p}_k|| \leq c||\nabla f(\mathbf{x}_k)"],
        "target": [r"\lVert\mathbf{p}_k\rVert\leq c\lVert\nabla f(\mathbf{x}_k)\rVert"],
    },
    "O015-PENN-ADV-0033": {
        "source": ["is called the \\textit{condition number}", r"0< 1 - \frac", r"\lambda_1^2 -2\lambda_1\lambda_2+\lambda_n^2"],
        "target": [r"\rho=\left|\frac{\lambda_n-\lambda_1}{\lambda_n+\lambda_1}\right|", r"0\leq 1-\frac", r"\lambda_1^2-2\lambda_1\lambda_n+\lambda_n^2"],
    },
    "O015-PENN-ADV-0034": {
        "source": [r"\lstinputlisting{Code/GradientAscent-1.mpl}", r"\lstinputlisting[firstnumber=40]{Code/GradientAscent-2.mpl}"],
        "target": [r"\textbf{PendakianGradien---bagian 1 dari 2}", r"\textbf{PendakianGradien---bagian 2 dari 2}"],
    },
    "O015-PENN-ADV-0035": {
        "source": [r"\mathbf{Q} = \begin{bmatrix}-2 & 0 \\ 0 & -10\end{bmatrix}"],
        "target": [r"\mathbf{Q}=\begin{bmatrix}-4&0\\0&-20\end{bmatrix}", r"bilangan kondisi spektralnya $\kappa=20/4=5$"],
    },
    "O015-PENN-ADV-0036": {
        "source": [r"\mathbf{p}_k = -\mathbf{H}^{-1}(\mathbf{x}^*)", r"\mathbf{H}(\mathbf{x}_k + t\mathbf{p}_k) \sim \mathbf{H}(\mathbf{x}^*)"],
        "target": [r"\mathbf{p}_k^{N}=-\mathbf{H}(\mathbf{x}_k)^{-1}\nabla f(\mathbf{x}_k)", "Konvergensi Hessian bersifat seragam", r"E_k\geq\left(\frac12-\sigma_1\right)\mu+o(1)>0"],
    },
    "O015-PENN-ADV-0037": {
        "source": [r"\end{equation} \label{def:GradientRelated} \end{definition}", r"\end{figure} \label{ex:GradientAscent} \end{example}"],
        "target": [r"\begin{definition}[Berkaitan dengan Gradien] \label{def:GradientRelated}", r"\begin{example} \label{ex:GradientAscent}"],
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict[str, int | str]:
    data = path.read_bytes()
    return {"bytes": len(data), "lines": len(data.splitlines()), "sha256": sha256_bytes(data)}


def identity_without_lines(path: Path) -> dict[str, int | str]:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": sha256_bytes(data)}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def strip_comments(text: str) -> str:
    output: list[str] = []
    for line in text.splitlines():
        cut = len(line)
        for index, char in enumerate(line):
            if char != "%":
                continue
            slashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                slashes += 1
                cursor -= 1
            if slashes % 2 == 0:
                cut = index
                break
        output.append(line[:cut])
    return "\n".join(output)


def captures(pattern: str, text: str) -> list[str]:
    return [match.group(1) for match in re.finditer(pattern, text, flags=re.DOTALL)]


def sequence_sha256(items: list[str]) -> str:
    payload = json.dumps(items, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


FORMULA_PATTERN = re.compile(
    r"\\begin\{(equation|displaymath|gather\*|multline)\}(.*?)\\end\{\1\}",
    flags=re.DOTALL,
)


def formula_inventory(text: str) -> list[dict[str, int | str]]:
    inventory: list[dict[str, int | str]] = []
    for index, match in enumerate(FORMULA_PATTERN.finditer(text), start=1):
        normalized = normalize_ws(match.group(2))
        inventory.append(
            {
                "index": index,
                "environment": match.group(1),
                "start_line": text.count("\n", 0, match.start()) + 1,
                "end_line": text.count("\n", 0, match.end()) + 1,
                "normalized_characters": len(normalized),
                "normalized_sha256": sha256_bytes(normalized.encode("utf-8")),
                "normalized_tex": normalized,
            }
        )
    return inventory


def environment_balance(text: str) -> dict[str, object]:
    stack: list[str] = []
    errors: list[dict[str, object]] = []
    for match in re.finditer(r"\\(begin|end)\{([^}]+)\}", text):
        action, name = match.groups()
        line = text.count("\n", 0, match.start()) + 1
        if action == "begin":
            stack.append(name)
        elif not stack:
            errors.append({"kind": "orphan_end", "environment": name, "line": line})
        else:
            opened = stack.pop()
            if opened != name:
                errors.append({"kind": "mismatched_end", "opened": opened, "closed": name, "line": line})
    if stack:
        errors.append({"kind": "unclosed", "environments": stack})
    return {"pass": not errors, "errors": errors}


def record_gate(gates: list[dict[str, object]], name: str, passed: bool, detail: object) -> None:
    gates.append({"gate": name, "pass": bool(passed), "detail": detail})


def locate_witness(text: str, needle: str) -> dict[str, object]:
    pattern = r"\s+".join(re.escape(part) for part in needle.split())
    match = re.search(pattern, text, flags=re.DOTALL)
    if match is None:
        return {"present": False, "needle": needle}
    excerpt = normalize_ws(match.group(0))
    return {
        "present": True,
        "start_line": text.count("\n", 0, match.start()) + 1,
        "end_line": text.count("\n", 0, match.end()) + 1,
        "normalized_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "excerpt": excerpt,
    }


def main() -> int:
    source_text = SOURCE.read_text(encoding="utf-8")
    target_text = TARGET.read_text(encoding="utf-8")
    source_live = strip_comments(source_text)
    target_live = strip_comments(target_text)
    source_id = identity(SOURCE)
    target_id = identity(TARGET)
    ledger_id = identity(LEDGER)
    gates: list[dict[str, object]] = []

    record_gate(gates, "source_identity", source_id == EXPECTED_IDENTITIES["source"], source_id)
    record_gate(gates, "target_identity", target_id == EXPECTED_IDENTITIES["target"], target_id)
    record_gate(gates, "proposed_ledger_identity", ledger_id == EXPECTED_IDENTITIES["proposed_ledger"], ledger_id)

    source_begin = captures(r"\\begin\{([^}]+)\}", source_live)
    target_begin = captures(r"\\begin\{([^}]+)\}", target_live)
    source_end = captures(r"\\end\{([^}]+)\}", source_live)
    target_end = captures(r"\\end\{([^}]+)\}", target_live)
    source_balance = environment_balance(source_live)
    target_balance = environment_balance(target_live)
    record_gate(
        gates,
        "balanced_environment_nesting",
        bool(source_balance["pass"])
        and bool(target_balance["pass"])
        and Counter(source_begin) == Counter(source_end)
        and Counter(target_begin) == Counter(target_end),
        {
            "source": {**source_balance, "begin": len(source_begin), "end": len(source_end)},
            "target": {**target_balance, "begin": len(target_begin), "end": len(target_end)},
        },
    )
    record_gate(
        gates,
        "exact_112_ordered_environment_topology",
        len(source_begin) == len(target_begin) == 112
        and source_begin == target_begin
        and dict(Counter(source_begin)) == EXPECTED_ENVIRONMENT_COUNTS
        and sequence_sha256(source_begin) == EXPECTED_ENV_SEQUENCE_SHA256,
        {
            "source_total": len(source_begin),
            "target_total": len(target_begin),
            "source_counts": dict(sorted(Counter(source_begin).items())),
            "target_counts": dict(sorted(Counter(target_begin).items())),
            "source_sequence_sha256": sequence_sha256(source_begin),
            "target_sequence_sha256": sequence_sha256(target_begin),
        },
    )

    source_labels = captures(r"\\label\{([^}]+)\}", source_live)
    target_labels = captures(r"\\label\{([^}]+)\}", target_live)
    record_gate(
        gates,
        "exact_32_label_closure",
        source_labels == EXPECTED_LABELS
        and Counter(target_labels) == Counter(EXPECTED_LABELS)
        and len(target_labels) == len(set(target_labels)) == 32,
        {"source_order": source_labels, "target_order": target_labels},
    )

    owner_patterns = {
        "def:GradientRelated": r"\\begin\{definition\}\[Berkaitan dengan Gradien\]\s*\\label\{def:GradientRelated\}",
        "thm:GenConverge": r"\\begin\{theorem\}\s*\\label\{thm:GenConverge\}",
        "lem:Kantorovich": r"\\begin\{lemma\}\[Ketaksamaan Kantorovich\]\s*\\label\{lem:Kantorovich\}",
        "thm:GradientAscentConverge": r"\\begin\{theorem\}\s*\\label\{thm:GradientAscentConverge\}",
        "ex:GradientAscent": r"\\begin\{example\}\s*\\label\{ex:GradientAscent\}",
        "thm:Superlinear": r"\\begin\{theorem\}\s*\\label\{thm:Superlinear\}",
    }
    owner_results = {name: bool(re.search(pattern, target_live)) for name, pattern in owner_patterns.items()}
    record_gate(gates, "owning_environment_label_binding", all(owner_results.values()), owner_results)

    ref_pattern = r"\\(?:ref|eqref|pageref)\{([^}]+)\}"
    source_refs = captures(ref_pattern, source_live)
    target_refs = captures(ref_pattern, target_live)
    record_gate(
        gates,
        "exact_reference_surface",
        len(source_refs) == 52
        and len(target_refs) == 48
        and len(set(source_refs)) == 35
        and len(set(target_refs)) == 36
        and not (set(source_refs) - set(target_refs))
        and set(target_refs) - set(source_refs) == {"thm:GenConverge"}
        and sequence_sha256(source_refs) == EXPECTED_SOURCE_REF_SEQUENCE_SHA256
        and sequence_sha256(target_refs) == EXPECTED_TARGET_REF_SEQUENCE_SHA256,
        {
            "source_calls": len(source_refs),
            "target_calls": len(target_refs),
            "source_unique": sorted(set(source_refs)),
            "target_unique": sorted(set(target_refs)),
            "missing_source_targets": sorted(set(source_refs) - set(target_refs)),
            "deliberate_added_targets": sorted(set(target_refs) - set(source_refs)),
            "source_sequence_sha256": sequence_sha256(source_refs),
            "target_sequence_sha256": sequence_sha256(target_refs),
        },
    )

    cite_pattern = r"\\cite(?:\[[^\]]*\])?\{([^}]+)\}"
    source_cites = captures(cite_pattern, source_live)
    target_cites = captures(cite_pattern, target_live)
    record_gate(gates, "exact_citation_sequence", source_cites == target_cites == ["Bert99"] * 4, {"source": source_cites, "target": target_cites})

    graphic_pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"
    expected_graphics = [f"Figures/{name}" for name in ASSETS]
    source_graphics = captures(graphic_pattern, source_live)
    target_graphics = captures(graphic_pattern, target_live)
    record_gate(gates, "exact_figure_call_sequence", source_graphics == target_graphics == expected_graphics, {"source": source_graphics, "target": target_graphics})

    source_exercises = len(re.findall(r"\\begin\{exercise\}", source_live))
    target_exercises = len(re.findall(r"\\begin\{exercise\}", target_live))
    record_gate(gates, "exact_exercise_surface", source_exercises == target_exercises == 4, {"source": source_exercises, "target": target_exercises})

    marker_pattern = re.compile(
        r"% (P04-S\d{3}) \| sumber authority/penn-state/source/ClassNotes/Section4\.tex baris (\d+)--(\d+)\n"
        r"% segment-id: ([a-z0-9.]+)"
    )
    parsed_segments = [(m.group(1), m.group(4), int(m.group(2)), int(m.group(3))) for m in marker_pattern.finditer(target_text)]
    covered_lines = [line for _, _, start, end in parsed_segments for line in range(start, end + 1)]
    record_gate(
        gates,
        "exact_seven_segment_partition",
        parsed_segments == SEGMENTS and covered_lines == list(range(1, 470)),
        {"parsed": parsed_segments, "covered_line_count": len(covered_lines), "first": min(covered_lines), "last": max(covered_lines)},
    )

    source_formulas = formula_inventory(source_live)
    target_formulas = formula_inventory(target_live)
    source_formula_types = [str(item["environment"]) for item in source_formulas]
    target_formula_types = [str(item["environment"]) for item in target_formulas]
    record_gate(
        gates,
        "exact_66_displayed_formula_sequence",
        len(source_formulas) == len(target_formulas) == 66 and source_formula_types == target_formula_types,
        {
            "source_count": len(source_formulas),
            "target_count": len(target_formulas),
            "type_counts": dict(sorted(Counter(source_formula_types).items())),
            "type_sequence_sha256": sequence_sha256(source_formula_types),
        },
    )

    formula_pairs: list[dict[str, object]] = []
    for source_formula, target_formula in zip(source_formulas, target_formulas):
        index = int(source_formula["index"])
        event_ids = FORMULA_EVENT_BINDINGS.get(index, [])
        formula_pairs.append(
            {
                "index": index,
                "environment": source_formula["environment"],
                "delta_class": "determined_delta" if event_ids else "translation_or_notational_reflow",
                "event_ids": event_ids,
                "source": {key: value for key, value in source_formula.items() if key not in {"index", "environment"}},
                "target": {key: value for key, value in target_formula.items() if key not in {"index", "environment"}},
            }
        )

    formula_event_ids = sorted({event for events in FORMULA_EVENT_BINDINGS.values() for event in events})
    invalid_formula_indices = sorted(index for index in FORMULA_EVENT_BINDINGS if index < 1 or index > 66)
    unknown_formula_events = sorted(set(formula_event_ids) - set(EXPECTED_EVENT_IDS))
    event_coverage = {
        event_id: {
            "formula_indices": sorted(index for index, events in FORMULA_EVENT_BINDINGS.items() if event_id in events),
            "non_formula_witness": NON_FORMULA_EVENT_BINDINGS.get(event_id),
        }
        for event_id in EXPECTED_EVENT_IDS
    }
    uncovered_events = sorted(event_id for event_id, binding in event_coverage.items() if not binding["formula_indices"] and not binding["non_formula_witness"])
    record_gate(
        gates,
        "formula_delta_event_binding",
        not invalid_formula_indices and not unknown_formula_events and not uncovered_events,
        {
            "determined_formula_indices": sorted(FORMULA_EVENT_BINDINGS),
            "invalid_formula_indices": invalid_formula_indices,
            "unknown_formula_events": unknown_formula_events,
            "uncovered_events": uncovered_events,
            "event_coverage": event_coverage,
        },
    )

    witness_results: dict[str, object] = {}
    witnesses_pass = True
    for event_id in EXPECTED_EVENT_IDS:
        spec = WITNESS_SPECS[event_id]
        source_results = [locate_witness(source_live, needle) for needle in spec["source"]]
        target_results = [locate_witness(target_live, needle) for needle in spec["target"]]
        event_pass = all(bool(item["present"]) for item in source_results + target_results)
        witnesses_pass = witnesses_pass and event_pass
        witness_results[event_id] = {"pass": event_pass, "source": source_results, "target": target_results}
    record_gate(gates, "exact_correction_witness_snippets", witnesses_pass, witness_results)

    ledger_records: list[dict[str, object]] = []
    ledger_parse_errors: list[dict[str, object]] = []
    for line_number, line in enumerate(LEDGER.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            ledger_parse_errors.append({"line": line_number, "error": "blank_record"})
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            ledger_parse_errors.append({"line": line_number, "error": str(exc)})
        else:
            ledger_records.append(record)
    ledger_ids = [record.get("event_id") for record in ledger_records]
    required_fields = {"event_id", "authority", "source", "surface", "source_issue", "target_action", "class"}
    ledger_schema_pass = (
        not ledger_parse_errors
        and ledger_ids == EXPECTED_EVENT_IDS
        and len(ledger_ids) == len(set(ledger_ids))
        and all(set(record) == required_fields for record in ledger_records)
        and all(all(isinstance(record[field], str) and record[field].strip() for field in required_fields) for record in ledger_records)
        and all(record["authority"] == "o015-penn-math555-v1.0-source" for record in ledger_records)
    )
    record_gate(gates, "exact_proposed_ledger_schema", ledger_schema_pass, {"count": len(ledger_records), "ids": ledger_ids, "parse_errors": ledger_parse_errors})

    asset_results: list[dict[str, object]] = []
    for name, (expected_bytes, expected_sha) in ASSETS.items():
        authority_path = ROOT / "authority/penn-state/source/ClassNotes/Figures" / name
        target_path = ROOT / "source/id-ID/figures" / name
        authority_id = identity_without_lines(authority_path)
        target_asset_id = identity_without_lines(target_path)
        passed = authority_id == target_asset_id == {"bytes": expected_bytes, "sha256": expected_sha}
        asset_results.append({"name": name, "pass": passed, "authority": authority_id, "target": target_asset_id})
    record_gate(gates, "exact_figure_asset_identity", all(item["pass"] for item in asset_results), asset_results)

    source_listing_calls = captures(r"\\lstinputlisting(?:\[[^\]]*\])?\{([^}]+)\}", source_live)
    excluded_results: list[dict[str, object]] = []
    copied_lines: list[dict[str, object]] = []
    for name, (expected_bytes, expected_lines, expected_sha) in EXCLUDED_CODE.items():
        path = ROOT / "authority/penn-state/source/ClassNotes/Code" / name
        code_id = identity(path)
        code_text = path.read_text(encoding="utf-8")
        normalized_target = normalize_ws(target_live)
        for line_number, line in enumerate(code_text.splitlines(), start=1):
            normalized_line = normalize_ws(line)
            if len(normalized_line) >= 24 and normalized_line in normalized_target:
                copied_lines.append({"file": name, "line": line_number, "text_sha256": sha256_bytes(normalized_line.encode("utf-8"))})
        expected = {"bytes": expected_bytes, "lines": expected_lines, "sha256": expected_sha}
        excluded_results.append({"name": name, "pass": code_id == expected, "identity": code_id})
    residue_fragments = [r"\lstinputlisting", r"\lstset", "Code/BackTrace.mpl", "Code/GradientAscent", ":= proc", "evalf(eval(", "nops("]
    residue = [fragment for fragment in residue_fragments if fragment in target_live]
    expected_listing_calls = ["Code/BackTrace.mpl", "Code/GradientAscent-1.mpl", "Code/GradientAscent-2.mpl"]
    record_gate(
        gates,
        "three_excluded_maple_inputs_no_listing_or_verbatim_copy",
        source_listing_calls == expected_listing_calls and all(item["pass"] for item in excluded_results) and not residue and not copied_lines,
        {"source_listing_calls": source_listing_calls, "excluded_inputs": excluded_results, "target_listing_or_syntax_residue": residue, "exact_normalized_code_lines_copied": copied_lines},
    )

    authority = json.loads(SOURCE_AUTHORITY.read_text(encoding="utf-8"))
    penn_records = [item for item in authority.get("authorities", []) if item.get("authority_id") == "o015-penn-math555-v1.0-source"]
    public_pdf_id = identity_without_lines(PUBLIC_PDF)
    authority_pdf_artifacts = [] if not penn_records else [item for item in penn_records[0].get("artifacts", []) if item.get("path") == "authority/penn-state/Math555.pdf"]
    edition_note = "" if not penn_records else str(penn_records[0].get("edition_note", ""))
    public_witness_pass = (
        len(penn_records) == 1
        and public_pdf_id == EXPECTED_IDENTITIES["public_pdf"]
        and len(authority_pdf_artifacts) == 1
        and authority_pdf_artifacts[0].get("edition") == "1.0.1"
        and authority_pdf_artifacts[0].get("bytes") == EXPECTED_IDENTITIES["public_pdf"]["bytes"]
        and authority_pdf_artifacts[0].get("sha256") == EXPECTED_IDENTITIES["public_pdf"]["sha256"]
        and "repaired closing delimiter in Equation (4.23)" in edition_note
    )
    record_gate(gates, "public_v1_0_1_correction_witness", public_witness_pass, {"pdf": public_pdf_id, "edition_note": edition_note, "artifact_records": authority_pdf_artifacts})

    overlap_text = OVERLAP_CONTROL.read_text(encoding="utf-8")
    overlap_required = (
        "Open Optimization Book 1 already owns LP/IP modeling, simplex and tableau mechanics, "
        "LP duality and complementary slackness, sensitivity analysis, graph/network/discrete algorithms, "
        "operations-research case studies, and introductory Excel/Python solver workflows."
    )
    forbidden_o018_terms = ["pemrograman linear", "pemrograman bilangan bulat", "metode simpleks", "tableau simpleks", "dualitas LP", "complementary slackness", "analisis sensitivitas", "algoritma jaringan"]
    o018_hits = [term for term in forbidden_o018_terms if term.casefold() in target_live.casefold()]
    chapter_scope = ["Aturan Armijo", "Syarat Kelengkungan", "Ketaksamaan Kantorovich", "Pendakian Gradien", "superlinear"]
    chapter_scope_hits = {term: term.casefold() in target_live.casefold() for term in chapter_scope}
    record_gate(
        gates,
        "o018_nonoverlap_boundary",
        overlap_required in normalize_ws(overlap_text) and not o018_hits and all(chapter_scope_hits.values()),
        {
            "control": {"path": rel(OVERLAP_CONTROL), **identity(OVERLAP_CONTROL)},
            "required_boundary_present": overlap_required in normalize_ws(overlap_text),
            "forbidden_o018_hits": o018_hits,
            "chapter_scope_hits": chapter_scope_hits,
        },
    )

    brace_detail = {"source_open": source_live.count("{"), "source_close": source_live.count("}"), "target_open": target_live.count("{"), "target_close": target_live.count("}")}
    record_gate(gates, "brace_balance", brace_detail["source_open"] == brace_detail["source_close"] and brace_detail["target_open"] == brace_detail["target_close"], brace_detail)

    forbidden_residue = {
        "old_chain_rule": r"\phi'(\delta_k) = \nabla f(\mathbf{x}_k)^T\mathbf{p}_k" in target_live,
        "old_recurrence_lhs": r"x_{k+1} = (-1)^n" in target_live,
        "malformed_capture_norm": r"c||\nabla f(\mathbf{x}_k)" in target_live,
        "old_lambda_2_expansion": r"\lambda_1^2 -2\lambda_1\lambda_2+\lambda_n^2" in target_live,
        "old_example_matrix": r"\begin{bmatrix}-2 & 0 \\ 0 & -10\end{bmatrix}" in target_live,
        "bare_newton_inverse": r"\mathbf{p}_k = -\mathbf{H}^{-1}(\mathbf{x}^*)" in target_live,
        "todo": "TODO" in target_live,
        "fixme": "FIXME" in target_live,
        "tbd": "TBD" in target_live,
    }
    record_gate(gates, "obsolete_formula_and_draft_residue_absent", not any(forbidden_residue.values()), forbidden_residue)

    failures = [str(item["gate"]) for item in gates if not item["pass"]]
    status = "PASS" if not failures else "FAIL"
    manifest_payload = {
        "schema": "o015-penn-ch04-formula-delta-manifest-v2",
        "status": status,
        "source": {"path": rel(SOURCE), **source_id},
        "target": {"path": rel(TARGET), **target_id},
        "proposed_ledger": {"path": rel(LEDGER), **ledger_id},
        "formula_pair_count": len(formula_pairs),
        "determined_formula_pair_count": len(FORMULA_EVENT_BINDINGS),
        "event_coverage": event_coverage,
        "pairs": formula_pairs,
        "failures": failures,
    }
    FORMULA_MANIFEST.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_id = identity(FORMULA_MANIFEST)

    if status == "PASS":
        remaining_defects: dict[str, object] = {"P1": 0, "P2": 0, "P3": 0, "classification": "all fail-closed gates passed"}
    else:
        remaining_defects = {"P1": None, "P2": None, "P3": None, "classification": "withheld because one or more gates failed"}
    report = {
        "schema": "o015-penn-ch04-structure-report-v2",
        "status": status,
        "source": {"path": rel(SOURCE), **source_id},
        "target": {"path": rel(TARGET), **target_id},
        "proposed_ledger": {"path": rel(LEDGER), **ledger_id},
        "formula_manifest": {"path": rel(FORMULA_MANIFEST), **manifest_id},
        "surface_summary": {
            "ordered_environments": len(source_begin),
            "displayed_formula_pairs": len(formula_pairs),
            "labels": len(target_labels),
            "source_reference_calls": len(source_refs),
            "target_reference_calls": len(target_refs),
            "citations": len(target_cites),
            "figures": len(target_graphics),
            "exercises": target_exercises,
            "segments": len(parsed_segments),
            "excluded_maple_inputs": len(source_listing_calls),
        },
        "gates": gates,
        "failures": failures,
        "remaining_defects": remaining_defects,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "failures": failures, "formula_pairs": len(formula_pairs), "report_sha256": sha256_bytes(REPORT.read_bytes()), "manifest_sha256": sha256_bytes(FORMULA_MANIFEST.read_bytes())}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
