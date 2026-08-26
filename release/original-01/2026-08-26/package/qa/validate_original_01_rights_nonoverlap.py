#!/usr/bin/env python3
"""Validate Original-01 component rights, provenance, and O018 non-overlap.

This is a deterministic, bounded admission check over exact live files.  It
does not attempt to replace a legal opinion or infer authorship from lexical
similarity; it verifies the explicit component boundary and scope evidence on
which this edition actually relies.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
RECEIPT = PROJECT / "qa/ORIGINAL_01_RIGHTS_NONOVERLAP.json"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"

EXPECTED = {
    "source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex": (27431, "db677ca6bab274a5db3e356fc996cef3bb00fb67770a90984460aa265fabcf26"),
    "source/id-ID/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex": (5311, "d632765baf270a7a7c1b39f051d83c1d76dd3ccc04457fb1b4b92088ffdd9322"),
    "source/id-ID/shinybook.cls": (10133, "83514a06b2884dcaa02575bb3409d2f8cc9cf2fc6e6aef344b442d424850f2c0"),
    "source/id-ID/macros-id.tex": (4465, "135642edfaffb7ec15e02e330dde76e694abe957da5f1a401c8563f9d885c1c2"),
    "authority/habring/source-v1/shinybook.cls": (10133, "83514a06b2884dcaa02575bb3409d2f8cc9cf2fc6e6aef344b442d424850f2c0"),
    "authority/habring/source-v1/macros.tex": (4017, "690ef578d545947425a851187ac0b5f45a1a326892a682bcd9d286abb72f924a"),
    "authority/habring/CC-BY-4.0-legalcode.txt": (18657, "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411"),
    "labs/original-01/stochastic-composite-lab.py": (13655, "21a0df89524b34916d1f659636bf8f92a5730efb7e263e0fbd7393e6f2c936fd"),
    "labs/original-01/results.json": (2432, "86ff701a51d091ee74c110917cb1888c6e7448489207e6ee1372753bd1e4c447"),
    "labs/original-01/results.csv": (4189, "61a6591ad7d1b41230a086482314448871f3697954d4c84133a7a5f4f775d37c"),
    "labs/original-01/objective-gap.svg": (86616, "87c772d901ee734356981ee35f19fc3c3ae47fea6f11528edbee6d015a3f2830"),
    "output/pdf/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf": (486032, "7fafa5aff08ee02f6b79c8dcea7b4bf509570958f94dc94ae51fc9e66b9f6bca"),
    "output/html/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html": (353245, "052155a1edc7f8f81a84e5445e1408c3ffdef6e42899677bf80f6300bc7558a4"),
    "output/epub/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub": (64322, "d3aaea87c928c825aac37310b3143e43c375f2ebb0ab4fe37bd0e34bfeab1f08"),
}

QA = {
    "qa/ORIGINAL_01_PDF_BUILD.json": "3a40f7be6da3ba76bd8ab7354da50af8f68c02b436882e61617fb077328c6fe0",
    "qa/ORIGINAL_01_PDF_VISUAL_QA.json": "49fa45dce663b5719f72295865497dd93e5e9f80fc78ef7ead89c0d29c6f1ae5",
    "qa/ORIGINAL_01_MATH_VALIDATION.json": "17e9510f9cb1562bbaee822c4b9381e8ff828aced798ca91723b2b6bc732751e",
    "qa/ORIGINAL_01_HTML_BUILD.json": "989ebdfe80076fe0b9405815f98f2dfe4cda19405f03c515fb6fc52e9c4f2753",
    "qa/ORIGINAL_01_HTML_BROWSER_QA.json": "22a4c01477c1b6cfcb59885bf0018eee9cb3656fc3dc3635f7c54afa77c4e0cd",
    "qa/ORIGINAL_01_EPUB_BUILD.json": "e95c686006d920774a2d0a080410d4348e58d4e2d197cbf8593b326a3285334e",
    "qa/ORIGINAL_01_EPUB_CONFORMANCE.json": "e1c9b411c9990df28b37a4dcb2d9111058a842768a3af13010397a700033d40c",
    "qa/ORIGINAL_01_BACKEND_VALIDATION.json": "c3d1961503dd77c3b9fea4b35556cc4916cef04ce663c58fca518622218bb561",
    "qa/ORIGINAL_01_INDEPENDENT_REREVIEW.json": "c3ae6f9298ef9e2ecc26a6dd23534d2d197ddc1f8ad2f8c676412e2ec0c258e0",
}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity(rel: str) -> dict:
    path = PROJECT / rel
    return {"path": rel, "bytes": path.stat().st_size, "sha256": sha_file(path)}


def require(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def main() -> None:
    failures: list[str] = []
    live = {}
    for rel, wanted in EXPECTED.items():
        got = identity(rel)
        live[rel] = got
        require((got["bytes"], got["sha256"]) == wanted, f"identity:{rel}", failures)

    qa = {}
    for rel, wanted_sha in QA.items():
        got = identity(rel)
        report = json.loads((PROJECT / rel).read_text(encoding="utf-8"))
        qa[rel] = got
        require(got["sha256"] == wanted_sha, f"qa_identity:{rel}", failures)
        require(report.get("result", report.get("status")) in {"pass", "PASS"}, f"qa_result:{rel}", failures)
        if rel.endswith("ORIGINAL_01_INDEPENDENT_REREVIEW.json"):
            counts = report.get("finding_counts", {}).get("remaining_after_corrections", {})
            require(counts == {"P1": 0, "P2": 0, "P3": 0}, "independent_rereview_clean", failures)

    body = (PROJECT / "source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex").read_text(encoding="utf-8")
    wrapper = (PROJECT / "source/id-ID/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex").read_text(encoding="utf-8")
    lab = (PROJECT / "labs/original-01/stochastic-composite-lab.py").read_text(encoding="utf-8")
    html = (PROJECT / "output/html/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html").read_text(encoding="utf-8")
    class_live = (PROJECT / "source/id-ID/shinybook.cls").read_bytes()
    class_authority = (PROJECT / "authority/habring/source-v1/shinybook.cls").read_bytes()
    macros_live = (PROJECT / "source/id-ID/macros-id.tex").read_bytes()
    macros_authority = (PROJECT / "authority/habring/source-v1/macros.tex").read_bytes()

    rights_markers = [
        "CC BY-SA 4.0",
        "CC BY 4.0",
        "Andreas Habring",
        "Christian Clason",
        MODEL,
        "tidak menyiratkan",
    ]
    for marker in rights_markers:
        require(marker in wrapper, f"wrapper_marker:{marker}", failures)
    require("CC BY-SA 4.0" in lab and MODEL in lab, "lab_rights_and_model", failures)
    require(class_live == class_authority, "exact_habring_class_copy", failures)
    require(macros_live != macros_authority, "macros_is_disclosed_adaptation_not_exact_copy", failures)
    require("Nama lingkungan dilokalkan" in macros_live.decode("utf-8"), "macro_localization_marker", failures)

    reference_markers = [
        "ditulis secara mandiri",
        "saksi verifikasi",
        "Andreas Habring",
        "Cl\\'ement W. Royer",
        "Lorenzo Rosasco",
        "Amir Beck",
        "Aaron Defazio",
    ]
    for marker in reference_markers:
        require(marker in body or marker in wrapper, f"reference_boundary:{marker}", failures)

    o018_markers = [
        "LP/MIP",
        "simpleks sebagai algoritma pemrograman linear",
        "dualitas LP",
        "sensitivitas",
        "jaringan",
        "optimisasi diskret",
        "himpunan probabilitas",
    ]
    for marker in o018_markers:
        require(marker in body, f"o018_boundary:{marker}", failures)

    forbidden_project_labels = ("Translation and Transcription Project", "TTP")
    for label in forbidden_project_labels:
        for name, text in (("body", body), ("wrapper", wrapper), ("html", html), ("lab", lab)):
            require(label not in text, f"forbidden_project_label:{label}:{name}", failures)

    rights_rows = list(csv.DictReader((PROJECT / "00_control/COMPONENT_RIGHTS.csv").open(encoding="utf-8", newline="")))
    rights_ids = {row["component_id"] for row in rights_rows}
    required_rights_ids = {
        "o015-original-01-chapter",
        "o015-original-01-wrapper",
        "o015-original-01-lab",
        "o015-original-01-readers",
        "o015-original-01-tooling",
    }
    require(required_rights_ids <= rights_ids, "component_rights_rows", failures)

    coverage = (PROJECT / "00_control/COVERAGE_OVERLAP.md").read_text(encoding="utf-8")
    require("Original-01 stochastic composite, mirror, and minibatch closure admitted" in coverage, "coverage_admission", failures)
    require("No O018 content is admitted" in coverage, "coverage_o018_exclusion", failures)

    ledger_lines = (PROJECT / "00_control/ADVERSE_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
    ledger = [json.loads(line) for line in ledger_lines if line.strip()]
    event_ids = {item["event_id"] for item in ledger}
    required_events = {f"O015-ORIG-ADV-{number:04d}" for number in range(1, 10)}
    require(required_events <= event_ids, "adverse_events_0001_0008", failures)

    authority = json.loads((PROJECT / "00_control/SOURCE_AUTHORITY.json").read_text(encoding="utf-8"))
    admission = authority.get("current_original_completion_admission", {})
    require(admission.get("status") == "original_tranche_1_locally_admitted_publication_pending", "source_authority_status", failures)
    require(admission.get("overlap", {}).get("o018_imported") is False, "source_authority_o018", failures)
    require(admission.get("rights", {}).get("new_substantive_content_and_lab") == "CC BY-SA 4.0", "source_authority_new_rights", failures)
    require(admission.get("rights", {}).get("habring_shinybook_and_macro_scaffold") == "CC BY 4.0", "source_authority_scaffold_rights", failures)

    backend = json.loads((PROJECT / "qa/ORIGINAL_01_BACKEND_VALIDATION.json").read_text(encoding="utf-8"))
    require(backend["protected_baseline"].get("record_count", backend["protected_baseline"].get("records")) == 3585, "backend_protected_count", failures)
    require(backend["admission"]["new_records"] == 358, "backend_added_count", failures)
    require(backend["admission"]["final_records"] == 3943, "backend_final_count", failures)
    require(backend["protected_baseline"].get("record_bytes_and_relative_order_stable", backend["protected_baseline"].get("record_bytes_and_relative_order_stable")), "backend_prior_stability", failures)

    report = {
        "schema": "o015-original-01-rights-nonoverlap-v1",
        "date": "2026-08-26",
        "result": "pass" if not failures else "fail",
        "failures": failures,
        "scope": "Exact Original-01 rights/provenance and O015/O018 boundary; bounded deterministic evidence, not a legal opinion or an authorship classifier.",
        "component_rights": {
            "new_substantive_chapter_and_lab": "CC BY-SA 4.0",
            "habring_exact_class_and_adapted_macro_scaffold": "CC BY 4.0",
            "class_exact_authority_match": class_live == class_authority,
            "macro_is_localized_adaptation": macros_live != macros_authority,
            "required_control_rows": sorted(required_rights_ids),
        },
        "reference_boundary": {
            "mathematical_witnesses_only": True,
            "copied_reference_prose_layout_exercises_figures_solutions_or_code_claimed": False,
            "nonendorsement_visible": True,
            "model_provenance": MODEL,
        },
        "o018_nonoverlap": {
            "imported": False,
            "simplex_use": "probability simplex only",
            "l1_use": "stochastic composite numerical diagnostic only",
            "excluded": ["LP/MIP", "simplex/tableau algorithms", "finite-LP duality/sensitivity", "network/discrete optimization", "OR solver workflow"],
        },
        "repairs_bound": sorted(required_events),
        "live_files": live,
        "passing_qa_receipts": qa,
        "backend": {"protected_records": 3585, "added_records": 358, "final_records": 3943},
        "upstream_contact": False,
    }
    RECEIPT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if failures:
        raise SystemExit(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print(json.dumps({"result": "pass", "receipt": str(RECEIPT), "checks": 40 + len(EXPECTED) + len(QA), "files": len(live)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
