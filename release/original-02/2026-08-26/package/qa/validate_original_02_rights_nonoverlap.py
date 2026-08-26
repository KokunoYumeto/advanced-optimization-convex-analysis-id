#!/usr/bin/env python3
"""Validate Original-02 rights, provenance, and O018 non-overlap.

This is a bounded, deterministic admission gate over exact live O015 files.
It verifies the explicit component-rights and scope claims used by the edition;
it is neither a legal opinion nor a lexical authorship classifier.  Missing
backend or control admission evidence is a hard prerequisite failure, never an
implicit pass.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


PROJECT = Path(__file__).resolve().parents[1]
RECEIPT = PROJECT / "qa" / "ORIGINAL_02_RIGHTS_NONOVERLAP.json"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
RIGHTS = (
    "Mixed rights: new Original-02 content CC BY-SA 4.0; "
    "shinybook.cls and macros-id.tex CC BY 4.0"
)

BODY = "source/id-ID/original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
WRAPPER = "source/id-ID/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
PDF = "output/pdf/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf"
HTML = "output/html/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html"
EPUB = "output/epub/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub"
LAB_SCRIPT = "labs/original-02/monotone-splitting-lab.py"
BACKEND_RECEIPT = "qa/ORIGINAL_02_BACKEND_VALIDATION.json"

EXPECTED = {
    BODY: (28028, "0f58d7785f281dd4e10ab3630d2f22a62b388ca98fd50b0e972e1cc89d847367"),
    WRAPPER: (5476, "cf8dd0e4cc31d8409bb2d8f27e1a6373adf728ba93702aa01e1a398d73a65db3"),
    "source/id-ID/shinybook.cls": (10133, "83514a06b2884dcaa02575bb3409d2f8cc9cf2fc6e6aef344b442d424850f2c0"),
    "source/id-ID/macros-id.tex": (4465, "135642edfaffb7ec15e02e330dde76e694abe957da5f1a401c8563f9d885c1c2"),
    "authority/habring/source-v1/shinybook.cls": (10133, "83514a06b2884dcaa02575bb3409d2f8cc9cf2fc6e6aef344b442d424850f2c0"),
    "authority/habring/source-v1/macros.tex": (4017, "690ef578d545947425a851187ac0b5f45a1a326892a682bcd9d286abb72f924a"),
    "authority/habring/CC-BY-4.0-legalcode.txt": (18657, "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411"),
    "source/en/becker-02-douglas-rachford-source.tex": (1358, "fdc368741a0a88eb9d21c69d655ac6ce1b44571c2d49c6a3302e3efc4673594b"),
    "source/id-ID/becker-02-pemisahan-douglas-rachford-id.tex": (4915, "2d0e7d64d8226954640013caecd1cacfb3c60d2ae75a27f130f97e900a20464a"),
    "source/id-ID/D90-BECKER-02-pemisahan-douglas-rachford-id.tex": (7134, "23fd130a5e644801ccb2374450ec07744c9e68dff003c295f3b127d9a9b90955"),
    LAB_SCRIPT: (17904, "1d13f436644216104036be248ebb3ff0b1a9e45c856aef9229f17a5f26f3e119"),
    "labs/original-02/results.json": (13503, "bc39d3363f02b904a27245bfe090cbf2153238a5a18ba8bf7cccbe1352672e81"),
    "labs/original-02/results.csv": (4228, "da8d09cce727c98b408fe719735574977266de1b58f95a742dcb60c5d163e243"),
    "labs/original-02/residual.svg": (9538, "c7bdeeed813cf36999ae2748362e547fc23de2d5ae15c6131e3fc73edeba6fd5"),
    PDF: (453811, "0dee2b2c16f0f0868b2c0813462fce6ecc02ad2b71174eb4c622f23988771284"),
    HTML: (190403, "ed60085e7ccbfcafa6675dc8bc4ebd728eaaf7c27ca24d35d5dbec7b742f529a"),
    EPUB: (48701, "dcde3d4e1a2070626fb86d3994667ce57095e5f8849b67ce3ebecaa145b54a86"),
}

QA = {
    "qa/ORIGINAL_02_PDF_BUILD.json": {
        "sha256": "d734ea6ecb0effdbcf710a682e9acab5996de7b502af774499d0410b2867d51a",
        "schema": "o015-original-02-pdf-build-v1",
        "artifact": PDF,
    },
    "qa/ORIGINAL_02_PDF_VISUAL_QA.json": {
        "sha256": "e41dcb44f270ecc483b2e2ab1c231ff88c99aaf1ff6fd926805d0764fb530c04",
        "schema": "o015-original-02-pdf-visual-qa-v1",
        "artifact": PDF,
    },
    "qa/ORIGINAL_02_HTML_BUILD.json": {
        "sha256": "c3564fa0ee594207bae55ecd06f6ff0b4137350a685aeadac51dc14775ebaee5",
        "schema": "o015-original-02-html-build-v1",
        "artifact": HTML,
    },
    "qa/ORIGINAL_02_HTML_BROWSER_QA.json": {
        "sha256": "24f7dd83724fc860b775715f72cd967a24f097cb8041686f8918154d08cd3891",
        "schema": "o015-original-02-html-browser-qa-v1",
        "artifact": HTML,
    },
    "qa/ORIGINAL_02_EPUB_BUILD.json": {
        "sha256": "f2f0a2782f194ffadb96e5f09a0c7a8eac68809d786f9cd68f34eb1498fe12c6",
        "schema": "o015-original-02-epub-build-v1",
        "artifact": EPUB,
    },
    "qa/ORIGINAL_02_EPUB_CONFORMANCE.json": {
        "sha256": "4ba00a859ae31066373581d19df7e01432e0b515e6e7687746637755693ba85e",
        "schema": "o015-original-02-epub-conformance-v1",
        "artifact": EPUB,
    },
    "qa/ORIGINAL_02_MATH_VALIDATION.json": {
        "sha256": "c20d9a3b32bf5dc61e4c1e6c147dc2ea0004c0f06c767481352f739e4b8aa7e4",
        "schema": "o015-original-02-open-math-validation-v1",
        "artifact": None,
    },
}

REQUIRED_O2_RIGHTS = {
    "o015-original-02-chapter": {
        "path": BODY,
        "rights": ("CC BY-SA 4.0",),
        "status": ("admitted_original",),
        "handling": ("independent", "non-endorsement", "O018"),
    },
    "o015-original-02-wrapper": {
        "path": WRAPPER,
        "rights": ("CC BY-SA 4.0", "CC BY 4.0"),
        "status": ("admitted_mixed_source",),
        "handling": ("Habring", "Christian Clason", "non-endorsement"),
    },
    "o015-original-02-lab": {
        "path": "labs/original-02/",
        "rights": ("CC BY-SA 4.0",),
        "status": ("admitted_original",),
        "handling": ("frozen", "outputs"),
    },
    "o015-original-02-readers": {
        "path": "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id",
        "rights": ("CC BY-SA 4.0", "CC BY 4.0"),
        "status": ("admitted_mixed_derivative",),
        "handling": ("partial-course", "non-endorsement", "model"),
    },
    "o015-original-02-tooling": {
        "path": "original_02",
        "rights": ("project-local",),
        "status": ("admitted",),
        "handling": ("scripts", "receipts"),
    },
}

LAB_FILES = (
    LAB_SCRIPT,
    "labs/original-02/results.json",
    "labs/original-02/results.csv",
    "labs/original-02/residual.svg",
)


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity(rel: str) -> dict[str, object]:
    path = PROJECT / rel
    return {
        "path": rel,
        "bytes": path.stat().st_size,
        "sha256": sha_file(path),
    }


def tool_locator(path: str) -> str:
    """Return a public-safe locator for a locally discovered executable."""

    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(PROJECT.resolve()).as_posix()
    except ValueError:
        return f"<external-tool>/{resolved.name}"


def require(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def pass_value(report: dict[str, object]) -> bool:
    value = report.get("result", report.get("status"))
    return value in {"pass", "PASS"}


def normalized_whitespace(text: str) -> str:
    return " ".join(text.split())


def bind_artifact(
    report: dict[str, object],
    artifact_rel: str,
    label: str,
    failures: list[str],
) -> None:
    artifact = report.get("artifact")
    require(isinstance(artifact, dict), f"{label}:artifact_missing", failures)
    if not isinstance(artifact, dict):
        return
    expected = identity(artifact_rel)
    for key in ("path", "bytes", "sha256"):
        require(
            artifact.get(key) == expected[key],
            f"{label}:artifact_{key}",
            failures,
        )


def visible_epub_text(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as package:
        for name in sorted(package.namelist()):
            if name.endswith(".xhtml"):
                document = ET.fromstring(package.read(name))
                chunks.append(" ".join(text.strip() for text in document.itertext() if text.strip()))
    return "\n".join(chunks)


def visible_pdf_text(path: Path, failures: list[str]) -> tuple[str, str | None]:
    executable = shutil.which("pdftotext")
    require(executable is not None, "prerequisite:pdftotext_not_found", failures)
    if executable is None:
        return "", None
    completed = subprocess.run(
        [executable, "-enc", "UTF-8", str(path), "-"],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    require(completed.returncode == 0, "pdf_text_extraction_failed", failures)
    return completed.stdout, tool_locator(executable)


def verify_qa(failures: list[str]) -> dict[str, dict[str, object]]:
    bound: dict[str, dict[str, object]] = {}
    parsed: dict[str, dict[str, object]] = {}
    for rel, spec in QA.items():
        path = PROJECT / rel
        require(path.is_file(), f"prerequisite:qa_missing:{rel}", failures)
        if not path.is_file():
            continue
        got = identity(rel)
        bound[rel] = got
        require(got["sha256"] == spec["sha256"], f"qa_identity:{rel}", failures)
        report = json.loads(path.read_text(encoding="utf-8"))
        parsed[rel] = report
        require(report.get("schema") == spec["schema"], f"qa_schema:{rel}", failures)
        require(pass_value(report), f"qa_result:{rel}", failures)
        if spec["artifact"]:
            bind_artifact(report, str(spec["artifact"]), rel, failures)
        if "upstream_contact" in report:
            require(report["upstream_contact"] is False, f"upstream_contact:{rel}", failures)

    visual = parsed.get("qa/ORIGINAL_02_PDF_VISUAL_QA.json", {})
    inspection = visual.get("inspection", {})
    require(inspection.get("all_pages_reviewed") is True, "pdf_visual:all_pages", failures)
    for key in (
        "broken_glyphs",
        "chart_information_dependencies",
        "clipped_text_or_math",
        "header_footer_page_number_defects",
        "margin_or_alignment_defects",
        "orphaned_headings",
        "overlaps",
        "unexpected_blank_pages",
        "unreadable_tables",
    ):
        require(inspection.get(key) == 0, f"pdf_visual:{key}", failures)
    require(inspection.get("reviewer") == MODEL, "pdf_visual:model", failures)

    browser = parsed.get("qa/ORIGINAL_02_HTML_BROWSER_QA.json", {})
    runtime = browser.get("runtime_console", {})
    require(runtime.get("errors") == 0, "html_browser:runtime_errors", failures)
    require(runtime.get("warnings") == 0, "html_browser:runtime_warnings", failures)
    viewports = browser.get("viewports", [])
    require(len(viewports) == 3, "html_browser:viewport_count", failures)
    for index, viewport in enumerate(viewports):
        require(viewport.get("page_horizontal_overflow") is False, f"html_browser:overflow:{index}", failures)
        require(viewport.get("bad_local_overflow_policy_count") == 0, f"html_browser:policy:{index}", failures)

    epub = parsed.get("qa/ORIGINAL_02_EPUB_CONFORMANCE.json", {})
    counts = epub.get("epubcheck", {}).get("counts", {})
    require(counts == {"error": 0, "fatal": 0, "usage": 0, "warning": 0}, "epubcheck:counts", failures)
    package = epub.get("package", {})
    require(package.get("mathml_surfaces") == 295, "epubcheck:mathml_count", failures)
    require(package.get("mathml_property_content_congruence") is True, "epubcheck:opf_mathml_congruence", failures)
    require(package.get("rights_metadata") == RIGHTS, "epubcheck:rights", failures)

    math = parsed.get("qa/ORIGINAL_02_MATH_VALIDATION.json", {})
    require(math.get("gate_count") == 20, "math_validation:gate_count", failures)
    require(math.get("failures") == [], "math_validation:failures", failures)
    require(math.get("status") == "PASS", "math_validation:status", failures)
    return bound


def verify_backend(failures: list[str]) -> dict[str, object] | None:
    path = PROJECT / BACKEND_RECEIPT
    require(
        path.is_file(),
        f"prerequisite:backend_receipt_missing:{BACKEND_RECEIPT}",
        failures,
    )
    if not path.is_file():
        return None

    report = json.loads(path.read_text(encoding="utf-8"))
    require(report.get("schema") == "o015-original-02-backend-validation-v1", "backend:schema", failures)
    require(report.get("result") == "pass", "backend:result", failures)
    require(report.get("errors", []) == [], "backend:errors", failures)
    admission = report.get("admission", {})
    protected = report.get("protected_baseline", {})
    deterministic = report.get("deterministic_regeneration", {})
    independent = report.get("independent_validation", {})
    topology = report.get("source_and_topology", {})
    require(admission.get("canonical_backend_written") is True, "backend:canonical_written", failures)
    require(admission.get("namespace") == "d90.orig.v1.tr02.*", "backend:namespace", failures)
    require(protected.get("record_bytes_and_relative_order_stable") is True, "backend:protected_stability", failures)
    require(deterministic.get("input_dataset_match") is True, "backend:deterministic_input", failures)
    require(
        deterministic.get("runs_completed") == deterministic.get("runs_required")
        and isinstance(deterministic.get("runs_completed"), int)
        and deterministic.get("runs_completed") >= 2,
        "backend:deterministic_runs",
        failures,
    )
    require(
        independent.get("passes_completed") == independent.get("passes_required")
        and isinstance(independent.get("passes_completed"), int)
        and independent.get("passes_completed") >= 2,
        "backend:independent_passes",
        failures,
    )

    protected_count = protected.get("records", protected.get("record_count"))
    added_count = admission.get("new_records")
    final_count = admission.get("final_records")
    require(
        all(isinstance(value, int) for value in (protected_count, added_count, final_count))
        and added_count > 0
        and final_count == protected_count + added_count,
        "backend:record_arithmetic",
        failures,
    )

    source = topology.get("source", {})
    expected_body = identity(BODY)
    for key in ("path", "bytes", "sha256"):
        require(source.get(key) == expected_body[key], f"backend:source_{key}", failures)
    require(topology.get("unit_id") == "d90.orig.v1.tr02.unit", "backend:unit_id", failures)

    for fmt in ("jsonl", "csv"):
        rel = f"backend/records.{fmt}"
        target = PROJECT / rel
        require(target.is_file(), f"backend:canonical_missing:{rel}", failures)
        if target.is_file():
            current = identity(rel)
            claimed = admission.get(fmt, {})
            require(claimed.get("bytes") == current["bytes"], f"backend:{fmt}_bytes", failures)
            require(claimed.get("sha256") == current["sha256"], f"backend:{fmt}_sha256", failures)

    lab = report.get("lab", {})
    require(lab.get("result") == "pass", "backend:lab_result", failures)
    require(lab.get("upstream_contact") is False, "backend:lab_upstream", failures)
    lab_artifacts = lab.get("artifacts", {})
    for rel in LAB_FILES:
        current = identity(rel)
        claimed = lab_artifacts.get(rel, {})
        require(claimed.get("bytes") == current["bytes"], f"backend:lab_bytes:{rel}", failures)
        require(claimed.get("sha256") == current["sha256"], f"backend:lab_sha256:{rel}", failures)

    return {
        "receipt": identity(BACKEND_RECEIPT),
        "protected_records": protected_count,
        "added_records": added_count,
        "final_records": final_count,
        "jsonl": admission.get("jsonl"),
        "csv": admission.get("csv"),
    }


def verify_controls(failures: list[str]) -> dict[str, object]:
    rights_path = PROJECT / "00_control" / "COMPONENT_RIGHTS.csv"
    rows = list(csv.DictReader(rights_path.open(encoding="utf-8", newline="")))
    by_id = {row.get("component_id", ""): row for row in rows}

    for component_id, expected in REQUIRED_O2_RIGHTS.items():
        row = by_id.get(component_id)
        require(
            row is not None,
            f"prerequisite:component_rights_row_missing:{component_id}",
            failures,
        )
        if row is None:
            continue
        require(str(expected["path"]) in row.get("path", ""), f"component_rights:path:{component_id}", failures)
        for marker in expected["rights"]:
            require(marker in row.get("rights_expression", ""), f"component_rights:rights:{component_id}:{marker}", failures)
        require(row.get("status") in expected["status"], f"component_rights:status:{component_id}", failures)
        combined = " ".join((row.get("required_handling", ""), row.get("notes", "")))
        for marker in expected["handling"]:
            require(marker.lower() in combined.lower(), f"component_rights:handling:{component_id}:{marker}", failures)

    habring_class = by_id.get("o015-habring-class", {})
    habring_macros = by_id.get("o015-habring-macros", {})
    require("CC BY 4.0" in habring_class.get("rights_expression", ""), "component_rights:habring_class", failures)
    require("Christian Clason" in " ".join(habring_class.values()), "component_rights:clason_credit", failures)
    require("CC BY 4.0" in habring_macros.get("rights_expression", ""), "component_rights:habring_macros", failures)

    becker = by_id.get("o015-becker-02-id-source", {})
    require("MIT" in becker.get("rights_expression", ""), "component_rights:becker_mit", failures)
    require("CC BY-SA 4.0" in becker.get("rights_expression", ""), "component_rights:becker_translation", failures)

    coverage_path = PROJECT / "00_control" / "COVERAGE_OVERLAP.md"
    coverage = coverage_path.read_text(encoding="utf-8")
    section_start = coverage.find("## Original-02")
    require(section_start >= 0, "prerequisite:coverage_original_02_section_missing", failures)
    coverage_section = ""
    if section_start >= 0:
        next_section = coverage.find("\n## ", section_start + 4)
        coverage_section = coverage[section_start : next_section if next_section >= 0 else None]
        normalized_section = " ".join(coverage_section.lower().split())
        semantic_markers = {
            "variational_inequality": ("variational inequalities", "ketaksamaan variasional"),
            "maximal_monotone": ("maximal monotone", "operator monoton maksimal"),
            "resolvent": ("resolvent", "resolven"),
            "splitting": ("splitting", "pemisahan"),
            "habring": ("habring",),
            "becker_02": ("becker-02",),
            "o018": ("o018",),
            "lp_mip": ("lp/mip",),
            "simplex_tableau": ("simplex/tableau", "simpleks/tableau"),
            "duality": ("duality", "dualitas"),
            "sensitivity": ("sensitivity", "sensitivitas"),
            "network_discrete": ("network/discrete optimization", "optimisasi jaringan/diskret"),
        }
        for label, alternatives in semantic_markers.items():
            require(
                any(marker in normalized_section for marker in alternatives),
                f"coverage_original_02:{label}",
                failures,
            )

    return {
        "component_rights_path": "00_control/COMPONENT_RIGHTS.csv",
        "required_o2_rows": sorted(REQUIRED_O2_RIGHTS),
        "present_o2_rows": sorted(set(REQUIRED_O2_RIGHTS) & set(by_id)),
        "coverage_path": "00_control/COVERAGE_OVERLAP.md",
        "coverage_section_present": section_start >= 0,
    }


def main() -> None:
    failures: list[str] = []
    live: dict[str, dict[str, object]] = {}
    for rel, wanted in EXPECTED.items():
        path = PROJECT / rel
        require(path.is_file(), f"identity_missing:{rel}", failures)
        if not path.is_file():
            continue
        got = identity(rel)
        live[rel] = got
        require((got["bytes"], got["sha256"]) == wanted, f"identity:{rel}", failures)

    body = (PROJECT / BODY).read_text(encoding="utf-8")
    wrapper = (PROJECT / WRAPPER).read_text(encoding="utf-8")
    lab = (PROJECT / LAB_SCRIPT).read_text(encoding="utf-8")
    html = (PROJECT / HTML).read_text(encoding="utf-8")
    epub_text = visible_epub_text(PROJECT / EPUB)
    pdf_text, pdftotext_path = visible_pdf_text(PROJECT / PDF, failures)
    normalized_source_text = normalized_whitespace(body + "\n" + wrapper)

    class_live = (PROJECT / "source/id-ID/shinybook.cls").read_bytes()
    class_authority = (PROJECT / "authority/habring/source-v1/shinybook.cls").read_bytes()
    macros_live = (PROJECT / "source/id-ID/macros-id.tex").read_bytes()
    macros_authority = (PROJECT / "authority/habring/source-v1/macros.tex").read_bytes()
    require(class_live == class_authority, "exact_habring_class_copy", failures)
    require(macros_live != macros_authority, "macro_must_be_disclosed_adaptation", failures)
    require(b"Nama lingkungan dilokalkan" in macros_live, "macro_localization_marker", failures)

    for marker in (
        "Teks dan laboratorium baru: CC BY-SA 4.0",
        "kelas dan makro: CC BY 4.0",
        "Andreas Habring",
        "Christian Clason",
        "salinan persis",
        "adaptasi Indonesia",
        "tidak dilisensikan ulang sebagai CC BY-SA",
    ):
        require(marker in wrapper, f"wrapper_rights:{marker}", failures)
    require(
        "Seluruh teks substantif dan kode laboratorium baru tersedia\nberdasarkan CC BY-SA 4.0" in wrapper,
        "wrapper_substantive_and_lab_cc_by_sa",
        failures,
    )

    for marker in (
        "Modul Becker mempertahankan hak MIT pada byte sumbernya",
        "tidak ada byte donor yang masuk ke lapisan asli ini",
        "tanpa mengulang modul proksimal konkret yang telah diterima",
    ):
        require(marker in wrapper, f"becker_separate_reference:{marker}", failures)
    require("\\input{becker" not in (body + wrapper).lower(), "becker_not_input_into_original_02", failures)

    for marker in (
        "ditulis secara mandiri",
        "saksi konsistensi",
        "Tidak ada prosa, tata letak, gambar, latihan, solusi, atau kode dari sumber tersebut yang disalin",
        "Saksi verifikasi yang dirujuk",
        "Penyebutan mereka hanya untuk atribusi matematika dan provenans",
    ):
        require(marker in normalized_source_text, f"witness_boundary:{marker}", failures)

    for marker in (
        "tidak memakai \\emph{simpleks} sebagai algoritma pemrograman linear",
        "tidak mengimpor LP/MIP",
        "dualitas atau sensitivitas\nLP",
        "jaringan",
        "optimisasi diskret dari O018",
    ):
        require(marker in body, f"o018_explicit_boundary:{marker}", failures)
    for forbidden in (
        "tableau simplex",
        "metode tableau",
        "metode simpleks",
        "branch-and-bound",
        "cabang-dan-batas",
        "pemrograman bilangan bulat",
        "aliran maksimum",
        "network flow",
        "dual simplex",
    ):
        require(forbidden.lower() not in body.lower(), f"o018_forbidden_topic:{forbidden}", failures)

    nonendorsement = (
        "Tidak seorang pun dari mereka maupun\ninstitusinya menyusun, memeriksa, "
        "menyetujui, mensponsori, atau mendukung edisi\nini"
    )
    require(nonendorsement in wrapper, "nonendorsement_exact", failures)

    for surface_name, text in (
        ("wrapper", wrapper),
        ("html", html),
        ("pdf", pdf_text),
        ("epub", epub_text),
    ):
        require(text.count(MODEL) == 1, f"model_marker_exactly_once:{surface_name}", failures)
        require("Translation and Transcription Project" not in text, f"forbidden_project_label:expanded:{surface_name}", failures)
        require("TTP" not in text, f"forbidden_project_label:TTP:{surface_name}", failures)
    for surface_name, text in (("body", body), ("lab", lab)):
        require("Translation and Transcription Project" not in text, f"forbidden_project_label:expanded:{surface_name}", failures)
        require("TTP" not in text, f"forbidden_project_label:TTP:{surface_name}", failures)

    require(f'<meta name="license" content="{RIGHTS}"' in html, "html_rights_metadata", failures)
    for marker in ("Andreas Habring", "Christian Clason", "Stephen Becker", "tidak menyiratkan"):
        require(marker in pdf_text, f"pdf_visible_rights:{marker}", failures)
        require(marker in epub_text, f"epub_visible_rights:{marker}", failures)

    tree = ast.parse(lab, filename=LAB_SCRIPT)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    require(
        imported_roots <= {"__future__", "csv", "json", "math", "pathlib", "numpy"},
        f"lab_unexpected_imports:{sorted(imported_roots)}",
        failures,
    )
    results = json.loads((PROJECT / "labs/original-02/results.json").read_text(encoding="utf-8"))
    require(results.get("upstream_contact") is False, "lab_results_upstream_contact", failures)
    require('"upstream_contact": False' in lab, "lab_source_upstream_contact", failures)

    qa_bound = verify_qa(failures)
    backend = verify_backend(failures)
    controls = verify_controls(failures)

    prerequisite_failures = sorted(
        failure for failure in failures if failure.startswith("prerequisite:")
    )
    report = {
        "schema": "o015-original-02-rights-nonoverlap-v1",
        "date": "2026-08-26",
        "result": "pass" if not failures else "fail",
        "failures": failures,
        "prerequisites_missing": prerequisite_failures,
        "scope": (
            "Exact Original-02 rights/provenance and O015/O018 boundary; "
            "bounded deterministic evidence, not a legal opinion or an "
            "authorship classifier."
        ),
        "component_rights": {
            "new_substantive_chapter_and_lab": "CC BY-SA 4.0",
            "habring_exact_class_and_adapted_macro_scaffold": "CC BY 4.0",
            "class_exact_authority_match": class_live == class_authority,
            "macro_is_localized_adaptation": macros_live != macros_authority,
            "becker_02": "separately licensed referenced companion; no donor byte claimed imported",
            "controls": controls,
        },
        "reference_boundary": {
            "mathematical_witnesses_only": True,
            "copied_reference_prose_layout_exercises_figures_solutions_or_code_claimed": False,
            "nonendorsement_visible": True,
            "model_provenance": MODEL,
            "model_marker_exactly_once_per_reader": True,
            "ttp_text_present": False,
        },
        "o018_nonoverlap": {
            "imported": False,
            "excluded": [
                "LP/MIP",
                "simplex/tableau algorithms",
                "finite-LP duality/sensitivity",
                "network/discrete optimization",
                "general OR solver workflow",
            ],
        },
        "upstream_contact": False,
        "pdf_text_extractor": pdftotext_path,
        "live_files": live,
        "passing_qa_receipts": qa_bound,
        "backend": backend,
    }
    RECEIPT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary = {
        "result": report["result"],
        "receipt": RECEIPT.relative_to(PROJECT).as_posix(),
        "failure_count": len(failures),
        "prerequisites_missing": prerequisite_failures,
        "validator_sha256": sha_file(Path(__file__).resolve()),
        "receipt_sha256": sha_file(RECEIPT),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
