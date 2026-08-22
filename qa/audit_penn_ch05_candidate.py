from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority/penn-state/source/ClassNotes/Section5.tex"
TARGET = ROOT / "source/id-ID/penn-05-metode-newton-dan-koreksi-id.tex"
LEDGER = ROOT / "qa/PENN_CH05_PROPOSED_LEDGER.jsonl"
REPORT = ROOT / "qa/PENN_CH05_STRUCTURE_REPORT.json"

EXPECTED_SOURCE = {
    "bytes": 22371,
    "lines": 317,
    "sha256": "15186b99be0913d83046e3e32eaf7a378d3a4fccd222219984b091ddf7f9a428",
}

SEGMENTS = [
    ("P05-S001", "d90.penn.v1.ch05.seg0001", 1, 38),
    ("P05-S002", "d90.penn.v1.ch05.seg0002", 39, 74),
    ("P05-S003", "d90.penn.v1.ch05.seg0003", 75, 148),
    ("P05-S004", "d90.penn.v1.ch05.seg0004", 149, 178),
    ("P05-S005", "d90.penn.v1.ch05.seg0005", 179, 206),
    ("P05-S006", "d90.penn.v1.ch05.seg0006", 207, 277),
    ("P05-S007", "d90.penn.v1.ch05.seg0007", 278, 317),
]

FIGURES = {
    "NewtonsMethod.pdf": (123281, "94c86e8eaf669f51dfe4d63f3b6799c84fb7b2d4fc781c304541aa40bc0442b6"),
    "DoublePeak.pdf": (2138564, "0091677ffedeaed91d4746edd03439ebb586a02900c86b9d7b9693205019e6fa"),
    "GaussModifiedNewtonsMethod.pdf": (56347, "d59d49782969f5c55a49fde4ffc65e919019e5df06ebd70009457a1b508422c2"),
    "ModifiedNewton.pdf": (56339, "7b5a76196e5b535447bc39162d1f11d63e65a021381108f06ac85ab7738bc28f"),
}

EXCLUDED_CODE = {
    "NewtonsMethodGeneral-1.mpl": (1668, "918e74995875169a7cdc7557903cfdcf89b090ab4b555d6fe1ebff2096d6bd84"),
    "NewtonsMethodGeneral-2.mpl": (568, "8ad5ff5bf7ed6a2f2e35727ef6a93ae6a9a08473ad579d104ec25ae638c6ce83"),
    "ModifiedCholesky.mpl": (513, "a52e4706ceeb9b21a4e68f78bf7d48aa96d4e9b5d1fa4c499762d6509ddfad89"),
    "ModifiedNewtonsMethod-1.mpl": (1499, "8392a10e803d4b5219eacefe52f85621bdb6ee1ad2d65e78c474f3697da0a6d0"),
    "ModifiedNewtonsMethod-2.mpl": (929, "5b14d0dcb525888022339740fda447dd7e15f7cbe00cd4547663350eaf0c6cd4"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict[str, int | str]:
    data = path.read_bytes()
    return {"bytes": len(data), "lines": len(data.splitlines()), "sha256": digest(data)}


def strip_comments(text: str) -> str:
    cleaned: list[str] = []
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
        cleaned.append(line[:cut])
    return "\n".join(cleaned)


def captures(pattern: str, text: str) -> list[str]:
    return [match.group(1) for match in re.finditer(pattern, text, flags=re.DOTALL)]


def environment_balance(text: str) -> dict[str, object]:
    stack: list[str] = []
    errors: list[dict[str, object]] = []
    for match in re.finditer(r"\\(begin|end)\s*\{([^}]+)\}", text):
        action, name = match.groups()
        if action == "begin":
            stack.append(name)
        elif not stack:
            errors.append({"kind": "orphan_end", "environment": name, "offset": match.start()})
        else:
            opened = stack.pop()
            if opened != name:
                errors.append(
                    {
                        "kind": "mismatched_end",
                        "opened": opened,
                        "closed": name,
                        "offset": match.start(),
                    }
                )
    if stack:
        errors.append({"kind": "unclosed", "environments": stack})
    return {"pass": not errors, "errors": errors}


def formula_inventory(text: str) -> list[dict[str, int | str]]:
    pattern = re.compile(
        r"\\begin\s*\{(equation|displaymath|gather\*|multline)\}(.*?)"
        r"\\end\s*\{\1\}",
        flags=re.DOTALL,
    )
    output: list[dict[str, int | str]] = []
    for index, match in enumerate(pattern.finditer(text), start=1):
        normalized = re.sub(r"\s+", " ", match.group(2)).strip()
        output.append(
            {
                "index": index,
                "environment": match.group(1),
                "normalized_characters": len(normalized),
                "normalized_sha256": digest(normalized.encode("utf-8")),
            }
        )
    return output


def add_gate(gates: list[dict[str, object]], name: str, passed: bool, detail: object) -> None:
    gates.append({"gate": name, "pass": bool(passed), "detail": detail})


def main() -> int:
    source_text = SOURCE.read_text(encoding="utf-8")
    target_text = TARGET.read_text(encoding="utf-8")
    source_live = strip_comments(source_text)
    target_live = strip_comments(target_text)
    gates: list[dict[str, object]] = []

    source_id = identity(SOURCE)
    target_id = identity(TARGET)
    add_gate(gates, "source_identity", source_id == EXPECTED_SOURCE, source_id)

    source_envs = captures(r"\\begin\s*\{([^}]+)\}", source_live)
    target_envs = captures(r"\\begin\s*\{([^}]+)\}", target_live)
    source_balance = environment_balance(source_live)
    target_balance = environment_balance(target_live)
    add_gate(gates, "source_environment_balance", bool(source_balance["pass"]), source_balance)
    add_gate(gates, "target_environment_balance", bool(target_balance["pass"]), target_balance)
    add_gate(
        gates,
        "ordered_environment_topology",
        source_envs == target_envs and len(source_envs) == 84,
        {
            "source_total": len(source_envs),
            "target_total": len(target_envs),
            "source_counts": dict(sorted(Counter(source_envs).items())),
            "target_counts": dict(sorted(Counter(target_envs).items())),
        },
    )

    source_labels = captures(r"\\label\{([^}]+)\}", source_live)
    target_labels = captures(r"\\label\{([^}]+)\}", target_live)
    add_gate(
        gates,
        "label_closure",
        Counter(source_labels) == Counter(target_labels) and len(target_labels) == len(set(target_labels)),
        {"source": source_labels, "target": target_labels},
    )

    ref_pattern = r"\\(?:ref|eqref|pageref)\{([^}]+)\}"
    source_refs = captures(ref_pattern, source_live)
    target_refs = captures(ref_pattern, target_live)
    add_gate(
        gates,
        "reference_surface",
        not (set(source_refs) - set(target_refs)),
        {
            "source_calls": len(source_refs),
            "target_calls": len(target_refs),
            "missing_source_targets": sorted(set(source_refs) - set(target_refs)),
            "added_targets": sorted(set(target_refs) - set(source_refs)),
        },
    )

    cite_pattern = r"\\cite(?:\[[^\]]*\])?\{([^}]+)\}"
    source_cites = captures(cite_pattern, source_live)
    target_cites = captures(cite_pattern, target_live)
    add_gate(gates, "citation_sequence", source_cites == target_cites == ["Bert99"], {"source": source_cites, "target": target_cites})

    graphic_pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"
    source_graphics = captures(graphic_pattern, source_live)
    target_graphics = captures(graphic_pattern, target_live)
    add_gate(gates, "figure_call_sequence", source_graphics == target_graphics, {"source": source_graphics, "target": target_graphics})

    source_exercises = len(re.findall(r"\\begin\s*\{exercise\}", source_live))
    target_exercises = len(re.findall(r"\\begin\s*\{exercise\}", target_live))
    add_gate(gates, "exercise_count", source_exercises == target_exercises == 5, {"source": source_exercises, "target": target_exercises})

    marker_pattern = re.compile(
        r"% (P05-S\d{3}) \| sumber authority/penn-state/source/ClassNotes/Section5\.tex baris (\d+)--(\d+)\n"
        r"% segment-id: ([a-z0-9.]+)"
    )
    parsed_segments = [
        (match.group(1), match.group(4), int(match.group(2)), int(match.group(3)))
        for match in marker_pattern.finditer(target_text)
    ]
    covered = [line for _, _, start, end in parsed_segments for line in range(start, end + 1)]
    add_gate(
        gates,
        "segment_partition",
        parsed_segments == SEGMENTS and covered == list(range(1, 318)),
        {"parsed": parsed_segments, "covered_line_count": len(covered)},
    )

    source_formulas = formula_inventory(source_live)
    target_formulas = formula_inventory(target_live)
    source_formula_types = [item["environment"] for item in source_formulas]
    target_formula_types = [item["environment"] for item in target_formulas]
    add_gate(
        gates,
        "formula_environment_sequence",
        source_formula_types == target_formula_types and len(source_formulas) == 35,
        {"source_count": len(source_formulas), "target_count": len(target_formulas), "types": source_formula_types},
    )

    required = {
        "newton_max_sign": r"\mathbf{B}_k=-\nabla^2f(\mathbf{x}_k)=-\mathbf{H}(\mathbf{x}_k)",
        "scalar_line_function": r"\phi(s)=F\!\left((1,0.5)^T+s\mathbf{p}_N\right)",
        "matrix_norm_unit_sphere": r"\max_{\lVert\mathbf{x}\rVert=1}\lVert\mathbf{M}\mathbf{x}\rVert",
        "local_invariance_modulus": r"q:=M\omega(\delta)<1",
        "correct_global_maximum": r"(x^*,y^*)=(0,1)",
        "pivot_square_root": r"L_{ii}\leftarrow\sqrt{\widehat d}",
        "named_surrogate": r"\mathbf{B}_k=\mathbf{L}\mathbf{L}^T",
        "correct_directional_product": r"\frac{9\alpha}{10}+\frac{6241\alpha^2}{400}",
        "uniform_surrogate_bounds": r"m\mathbf{I}\preceq\mathbf{B}_k\preceq M\mathbf{I}",
        "negative_hessian_pivots": r"-\mathbf{H}(\mathbf{x}^*)",
        "local_finite_termination_alternative": r"Iterasi itu mencapai $\mathbf{x}^*$ dalam sejumlah langkah hingga",
        "factorization_output_contract": r"(\mathbf{L},\mathbf{B},C)\leftarrow\textbf{CholeskyTermodifikasi}",
        "superlinear_finite_termination_alternative": r"algoritma mencapai $\mathbf{x}^*$ dalam sejumlah langkah hingga, atau",
    }
    required_results = {name: fragment in target_live for name, fragment in required.items()}
    add_gate(gates, "determined_repairs_present", all(required_results.values()), required_results)

    forbidden = {
        "legacy_listing": r"\lstinputlisting",
        "legacy_code_path": "Code/",
        "bad_matrix_norm": r"\max_{||\mathbf{x}||-1}",
        "bad_endpoint": r"(x^*,y^*)=(1,1)",
        "missing_inverse_direction": r"-s\mathbf{H}(1,0.5)\nabla F",
        "todo": "TODO",
        "fixme": "FIXME",
        "tbd": "TBD",
        "ambiguous_open_pseudocode_claim": "pseudokode terbuka",
        "ambiguous_open_reference_claim": "acuan terbuka",
    }
    forbidden_results = {name: fragment not in target_live for name, fragment in forbidden.items()}
    add_gate(gates, "residue_and_excluded_code", all(forbidden_results.values()), forbidden_results)

    records = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [record["event_id"] for record in records]
    expected_ids = [f"O015-PENN-ADV-{number:04d}" for number in range(38, 50)]
    fields = {"event_id", "authority", "source", "surface", "source_issue", "target_action", "class"}
    add_gate(
        gates,
        "proposed_ledger",
        ids == expected_ids and len(ids) == len(set(ids)) and all(set(record) == fields for record in records),
        {"count": len(records), "ids": ids},
    )

    figure_results: list[dict[str, object]] = []
    for name, (expected_bytes, expected_sha) in FIGURES.items():
        source_path = ROOT / "authority/penn-state/source/ClassNotes/Figures" / name
        target_path = ROOT / "source/id-ID/figures" / name
        source_asset = identity(source_path)
        target_asset = identity(target_path)
        passed = (
            source_asset["bytes"] == expected_bytes
            and source_asset["sha256"] == expected_sha
            and source_asset == target_asset
        )
        figure_results.append({"name": name, "pass": passed, "source": source_asset, "target": target_asset})
    add_gate(gates, "figure_asset_identity", all(item["pass"] for item in figure_results), figure_results)

    code_results: list[dict[str, object]] = []
    for name, (expected_bytes, expected_sha) in EXCLUDED_CODE.items():
        path = ROOT / "authority/penn-state/source/ClassNotes/Code" / name
        item = identity(path)
        passed = item["bytes"] == expected_bytes and item["sha256"] == expected_sha
        code_results.append({"name": name, "pass": passed, **item})
    add_gate(gates, "excluded_code_identity", all(item["pass"] for item in code_results), code_results)

    brace_detail = {
        "source_open": source_live.count("{"),
        "source_close": source_live.count("}"),
        "target_open": target_live.count("{"),
        "target_close": target_live.count("}"),
    }
    add_gate(
        gates,
        "brace_balance",
        brace_detail["source_open"] == brace_detail["source_close"]
        and brace_detail["target_open"] == brace_detail["target_close"],
        brace_detail,
    )

    failures = [gate["gate"] for gate in gates if not gate["pass"]]
    payload = {
        "schema": "o015-penn-ch05-structure-report-v1",
        "status": "PASS" if not failures else "FAIL",
        "source": {"path": str(SOURCE.relative_to(ROOT)).replace("\\", "/"), **source_id},
        "target": {"path": str(TARGET.relative_to(ROOT)).replace("\\", "/"), **target_id},
        "proposed_ledger": {"path": str(LEDGER.relative_to(ROOT)).replace("\\", "/"), **identity(LEDGER)},
        "formula_inventory": {"source": source_formulas, "target": target_formulas},
        "gates": gates,
        "failures": failures,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "failures": failures, "report": str(REPORT)}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
