#!/usr/bin/env python3
"""Build and verify the compact, reader-first Original-02 release.

The release is intentionally fail-closed.  It is not emitted until every
final Original-02 receipt exists, passes, binds the exact current bytes, and
the independent rereview has no open finding.  The package carries the three
reader surfaces, resumable source, lab, compact backend schema, and the
builders, validators, and receipts needed to reproduce the admitted boundary.
The full backend and authority witnesses remain in the edition repository.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PACKAGE = HERE / "package"
ZIP_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_ORIGINAL_02_2026.08.26.zip"
ZIP_PATH = HERE / ZIP_NAME
RECEIPT_PATH = HERE / "local-verification-original-02.json"
STAMP = (2026, 8, 26, 0, 0, 0)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
MAX_BYTES = 500_000_000


# These identities are the frozen, already-passing Original-02 core at the
# release-tooling boundary.  A later change must pass the substantive gates
# again and deliberately update this map; the packager never blesses drift.
FROZEN_CORE: dict[str, tuple[int, str]] = {
    "output/pdf/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf": (453811, "0dee2b2c16f0f0868b2c0813462fce6ecc02ad2b71174eb4c622f23988771284"),
    "output/html/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html": (190403, "ed60085e7ccbfcafa6675dc8bc4ebd728eaaf7c27ca24d35d5dbec7b742f529a"),
    "output/epub/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub": (48701, "dcde3d4e1a2070626fb86d3994667ce57095e5f8849b67ce3ebecaa145b54a86"),
    "source/id-ID/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex": (5476, "cf8dd0e4cc31d8409bb2d8f27e1a6373adf728ba93702aa01e1a398d73a65db3"),
    "source/id-ID/original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex": (28028, "0f58d7785f281dd4e10ab3630d2f22a62b388ca98fd50b0e972e1cc89d847367"),
    "source/id-ID/macros-id.tex": (4465, "135642edfaffb7ec15e02e330dde76e694abe957da5f1a401c8563f9d885c1c2"),
    "source/id-ID/shinybook.cls": (10133, "83514a06b2884dcaa02575bb3409d2f8cc9cf2fc6e6aef344b442d424850f2c0"),
    "labs/original-02/monotone-splitting-lab.py": (17904, "1d13f436644216104036be248ebb3ff0b1a9e45c856aef9229f17a5f26f3e119"),
    "labs/original-02/results.json": (13503, "bc39d3363f02b904a27245bfe090cbf2153238a5a18ba8bf7cccbe1352672e81"),
    "labs/original-02/results.csv": (4228, "da8d09cce727c98b408fe719735574977266de1b58f95a742dcb60c5d163e243"),
    "labs/original-02/residual.svg": (9538, "c7bdeeed813cf36999ae2748362e547fc23de2d5ae15c6131e3fc73edeba6fd5"),
    "backend/backend_schema.json": (3092, "1166cbffe6016044430fe003e4981b1a3a537be7c115f0b646168a1936ab5ad0"),
    "qa/ORIGINAL_02_MATH_VALIDATION.json": (26577, "c20d9a3b32bf5dc61e4c1e6c147dc2ea0004c0f06c767481352f739e4b8aa7e4"),
    "qa/ORIGINAL_02_PDF_BUILD.json": (6073, "d734ea6ecb0effdbcf710a682e9acab5996de7b502af774499d0410b2867d51a"),
    "qa/ORIGINAL_02_PDF_VISUAL_QA.json": (5685, "e41dcb44f270ecc483b2e2ab1c231ff88c99aaf1ff6fd926805d0764fb530c04"),
    "qa/ORIGINAL_02_HTML_BUILD.json": (6289, "c3564fa0ee594207bae55ecd06f6ff0b4137350a685aeadac51dc14775ebaee5"),
    "qa/ORIGINAL_02_HTML_BROWSER_QA.json": (4247, "24f7dd83724fc860b775715f72cd967a24f097cb8041686f8918154d08cd3891"),
    "qa/ORIGINAL_02_EPUB_BUILD.json": (7697, "f2f0a2782f194ffadb96e5f09a0c7a8eac68809d786f9cd68f34eb1498fe12c6"),
    "qa/ORIGINAL_02_EPUB_CONFORMANCE.json": (4066, "4ba00a859ae31066373581d19df7e01432e0b515e6e7687746637755693ba85e"),
    "qa/build_original_02_pdf_engine.py": (9055, "d9310945db995c99c4ec352fa5c2d1a4c4d2cc72fdc437e20ab82131dd93b2e0"),
    "qa/build_original_02_pdf.py": (2562, "c255b0aedf864fbadf6d58817080b4c484a263ca71741774980852f4ef057088"),
    "qa/build_original_02_reflow_engine.py": (76168, "bcc5cdbd7957e0e3829fe397057f4d78a4fb9f8a4df3b6a27e54ec7252e2c8ad"),
    "qa/build_original_02_reflow.py": (7294, "0cfde97b2ed274813ab8a014867187ff9d3c38a3f928353d9c9bac327d953f1e"),
    "qa/validate_original_02_math.py": (49667, "5b9cc66b6560b210715a0b6c6bd8b31943dd91d3764b3cb1ffb86e908d2662a1"),
    "qa/verify_original_02_pdf_visual.py": (5963, "4d1231e0b8ab29ae5fa296389eae9b6226f8f9bbff1ca7d3d59227dc9b368c9b"),
    "qa/verify_original_02_epub.py": (25107, "57aa0ee9d1a81edf0ee12113e4a2b8c25eeba40e06ba411849f11bc492d91245"),
}


# The first three members are the visible readers, in release order.
MATERIAL = [
    ("D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf", "output/pdf/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf", "primary PDF reader", "application/pdf"),
    ("D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html", "output/html/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html", "responsive semantic HTML reader", "text/html"),
    ("D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub", "output/epub/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub", "reflow EPUB reader", "application/epub+zip"),
    ("README_ORIGINAL_02.md", None, "reader-first scope and continuation guide", "text/markdown"),
    ("RIGHTS_AND_PROVENANCE_ORIGINAL_02.md", None, "component rights and provenance", "text/markdown"),
    ("LICENSE_ORIGINAL_CC_BY-SA-4.0.md", None, "license note for new Original-02 material", "text/markdown"),
    ("LICENSE_HABRING_SCAFFOLD_CC_BY-4.0.md", None, "license note for Habring scaffold", "text/markdown"),
    ("source/id-ID/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex", "source/id-ID/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex", "standalone Indonesian reader wrapper", "application/x-tex"),
    ("source/id-ID/original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex", "source/id-ID/original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex", "independent Indonesian substantive chapter", "application/x-tex"),
    ("source/id-ID/macros-id.tex", "source/id-ID/macros-id.tex", "localized macro scaffold", "application/x-tex"),
    ("source/id-ID/shinybook.cls", "source/id-ID/shinybook.cls", "Habring document-class scaffold", "application/x-tex"),
    ("labs/original-02/monotone-splitting-lab.py", "labs/original-02/monotone-splitting-lab.py", "open computation lab", "text/x-python"),
    ("labs/original-02/results.json", "labs/original-02/results.json", "machine-readable lab results", "application/json"),
    ("labs/original-02/results.csv", "labs/original-02/results.csv", "tabular lab results", "text/csv"),
    ("labs/original-02/residual.svg", "labs/original-02/residual.svg", "lab chart with text alternative in readers", "image/svg+xml"),
    ("backend/backend_schema.json", "backend/backend_schema.json", "stable-ID backend schema", "application/json"),
    ("qa/ORIGINAL_02_MATH_VALIDATION.json", "qa/ORIGINAL_02_MATH_VALIDATION.json", "open mathematics validation", "application/json"),
    ("qa/ORIGINAL_02_PDF_BUILD.json", "qa/ORIGINAL_02_PDF_BUILD.json", "deterministic PDF build receipt", "application/json"),
    ("qa/ORIGINAL_02_PDF_VISUAL_QA.json", "qa/ORIGINAL_02_PDF_VISUAL_QA.json", "all-page PDF visual QA", "application/json"),
    ("qa/ORIGINAL_02_HTML_BUILD.json", "qa/ORIGINAL_02_HTML_BUILD.json", "deterministic HTML build receipt", "application/json"),
    ("qa/ORIGINAL_02_HTML_BROWSER_QA.json", "qa/ORIGINAL_02_HTML_BROWSER_QA.json", "desktop and phone browser QA", "application/json"),
    ("qa/ORIGINAL_02_EPUB_BUILD.json", "qa/ORIGINAL_02_EPUB_BUILD.json", "deterministic EPUB build receipt", "application/json"),
    ("qa/ORIGINAL_02_EPUB_CONFORMANCE.json", "qa/ORIGINAL_02_EPUB_CONFORMANCE.json", "EPUB and EPUBCheck conformance", "application/json"),
    ("qa/ORIGINAL_02_BACKEND_BUILD.json", "qa/ORIGINAL_02_BACKEND_BUILD.json", "stable-ID backend extension receipt", "application/json"),
    ("qa/ORIGINAL_02_BACKEND_VALIDATION.json", "qa/ORIGINAL_02_BACKEND_VALIDATION.json", "independent stable-ID backend validation", "application/json"),
    ("qa/ORIGINAL_02_RIGHTS_NONOVERLAP.json", "qa/ORIGINAL_02_RIGHTS_NONOVERLAP.json", "rights and O018 non-overlap gate", "application/json"),
    ("qa/ORIGINAL_02_INDEPENDENT_REREVIEW.json", "qa/ORIGINAL_02_INDEPENDENT_REREVIEW.json", "independent final rereview", "application/json"),
    ("qa/build_original_02_pdf_engine.py", "qa/build_original_02_pdf_engine.py", "isolated PDF build engine", "text/x-python"),
    ("qa/build_original_02_pdf.py", "qa/build_original_02_pdf.py", "Original-02 PDF build wrapper", "text/x-python"),
    ("qa/build_original_02_reflow_engine.py", "qa/build_original_02_reflow_engine.py", "isolated HTML/EPUB reflow engine", "text/x-python"),
    ("qa/build_original_02_reflow.py", "qa/build_original_02_reflow.py", "Original-02 HTML/EPUB build wrapper", "text/x-python"),
    ("qa/validate_original_02_math.py", "qa/validate_original_02_math.py", "mathematics validator", "text/x-python"),
    ("qa/verify_original_02_pdf_visual.py", "qa/verify_original_02_pdf_visual.py", "PDF visual validator", "text/x-python"),
    ("qa/verify_original_02_epub.py", "qa/verify_original_02_epub.py", "EPUB validator", "text/x-python"),
    ("qa/extend_backend_original_02.py", "qa/extend_backend_original_02.py", "backend extension generator", "text/x-python"),
    ("qa/validate_backend_original_02.py", "qa/validate_backend_original_02.py", "backend validator", "text/x-python"),
    ("qa/validate_original_02_rights_nonoverlap.py", "qa/validate_original_02_rights_nonoverlap.py", "rights/non-overlap validator", "text/x-python"),
]

REPORT_PATHS = {
    "math": "qa/ORIGINAL_02_MATH_VALIDATION.json",
    "pdf_build": "qa/ORIGINAL_02_PDF_BUILD.json",
    "pdf_visual": "qa/ORIGINAL_02_PDF_VISUAL_QA.json",
    "html_build": "qa/ORIGINAL_02_HTML_BUILD.json",
    "browser": "qa/ORIGINAL_02_HTML_BROWSER_QA.json",
    "epub_build": "qa/ORIGINAL_02_EPUB_BUILD.json",
    "epub_conformance": "qa/ORIGINAL_02_EPUB_CONFORMANCE.json",
    "backend_build": "qa/ORIGINAL_02_BACKEND_BUILD.json",
    "backend": "qa/ORIGINAL_02_BACKEND_VALIDATION.json",
    "rights": "qa/ORIGINAL_02_RIGHTS_NONOVERLAP.json",
    "rereview": "qa/ORIGINAL_02_INDEPENDENT_REREVIEW.json",
}

MANIFEST_NAME = "release-manifest-original-02.json"
SUMS_NAME = "SHA256SUMS"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, Any]:
    return {"path": path.relative_to(PROJECT).as_posix(), "bytes": path.stat().st_size, "sha256": sha_file(path)}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_exists(path: Path, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label}: missing file {path}")


def assert_report_pass(path: Path, label: str) -> dict[str, Any]:
    assert_exists(path, f"{label} release gate not ready")
    report = load_json(path)
    result = str(report.get("result", report.get("status", ""))).lower()
    if result != "pass":
        raise RuntimeError(f"{label}: non-passing result {result!r}")
    failures = report.get("failures")
    if failures not in (None, []):
        raise RuntimeError(f"{label}: failures are present: {failures!r}")
    errors = report.get("errors")
    if errors not in (None, []):
        raise RuntimeError(f"{label}: errors are present: {errors!r}")
    return report


def normalized_rel(value: Any) -> str:
    return str(value).replace("\\", "/").lstrip("./")


def dictionaries(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from dictionaries(child)
    elif isinstance(value, list):
        for child in value:
            yield from dictionaries(child)


def report_binds(report: dict[str, Any], rel: str, expected: dict[str, Any] | None = None) -> bool:
    current = expected or identity(PROJECT / PurePosixPath(rel))
    for node in dictionaries(report):
        if normalized_rel(node.get("path", "")) != rel:
            continue
        if node.get("bytes") == current["bytes"] and str(node.get("sha256", "")).lower() == current["sha256"]:
            return True
    return False


def require_binding(report: dict[str, Any], rel: str, label: str) -> None:
    if not report_binds(report, rel):
        raise RuntimeError(f"{label} does not bind exact current identity for {rel}")


def validate_frozen_core() -> None:
    for rel, (expected_bytes, expected_sha) in FROZEN_CORE.items():
        path = PROJECT / PurePosixPath(rel)
        assert_exists(path, f"frozen core {rel}")
        got = (path.stat().st_size, sha_file(path))
        if got != (expected_bytes, expected_sha):
            raise RuntimeError(
                f"Frozen Original-02 identity drift at {rel}: "
                f"expected {expected_bytes}/{expected_sha}, got {got[0]}/{got[1]}"
            )


def all_zero(value: Any) -> bool:
    if isinstance(value, dict):
        return all(all_zero(child) for child in value.values())
    if isinstance(value, list):
        return all(all_zero(child) for child in value)
    return value in (0, None, [], {})


def validate_inputs() -> dict[str, dict[str, Any]]:
    validate_frozen_core()
    reports = {
        key: assert_report_pass(PROJECT / PurePosixPath(rel), key)
        for key, rel in REPORT_PATHS.items()
    }

    expected_schemas = {
        "backend_build": "o015-original-02-backend-extension-v1",
        "backend": "o015-original-02-backend-validation-v1",
        "rights": "o015-original-02-rights-nonoverlap-v1",
    }
    for key, schema in expected_schemas.items():
        if reports[key].get("schema") != schema:
            raise RuntimeError(f"{key}: unexpected schema {reports[key].get('schema')!r}")

    # Each reader is bound both by its deterministic build and by the
    # independent surface/conformance check.
    binding_sets = {
        "pdf_build": [
            "output/pdf/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf",
            "qa/build_original_02_pdf_engine.py",
            "qa/build_original_02_pdf.py",
        ],
        "pdf_visual": [
            "output/pdf/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf",
            "qa/ORIGINAL_02_PDF_BUILD.json",
        ],
        "html_build": [
            "output/html/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html",
            "qa/build_original_02_reflow_engine.py",
            "qa/build_original_02_reflow.py",
        ],
        "browser": [
            "output/html/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html",
            "qa/ORIGINAL_02_HTML_BUILD.json",
        ],
        "epub_build": [
            "output/epub/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub",
            "qa/build_original_02_reflow_engine.py",
            "qa/build_original_02_reflow.py",
        ],
        "epub_conformance": [
            "output/epub/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub",
            "qa/ORIGINAL_02_EPUB_BUILD.json",
        ],
    }
    for report_key, paths in binding_sets.items():
        for rel in paths:
            require_binding(reports[report_key], rel, report_key)

    epub_counts = reports["epub_conformance"].get("epubcheck", {}).get("counts", {})
    if any(int(epub_counts.get(key, 0)) for key in ("fatal", "error", "warning", "usage")):
        raise RuntimeError(f"EPUBCheck reported nonzero counts: {epub_counts}")

    backend_build = reports["backend_build"]
    backend = reports["backend"]
    schema_bytes, schema_sha = FROZEN_CORE["backend/backend_schema.json"]
    schema_identity = backend_build.get("schema_identity", {})
    if (schema_identity.get("bytes"), schema_identity.get("sha256")) != (schema_bytes, schema_sha):
        raise RuntimeError("Backend build does not bind the frozen backend schema")
    schema_constraint = backend.get("schema_constraint", {})
    if (schema_constraint.get("schema_bytes"), schema_constraint.get("schema_sha256")) != (schema_bytes, schema_sha):
        raise RuntimeError("Backend validation does not bind the frozen backend schema")
    for rel in ("qa/extend_backend_original_02.py", "qa/validate_backend_original_02.py"):
        require_binding(backend_build, rel, "backend build")
    require_binding(backend, REPORT_PATHS["backend_build"], "backend validation")
    admission = backend.get("admission", {})
    if admission.get("canonical_backend_written") is not True:
        raise RuntimeError("Backend validation does not prove canonical admission")
    if admission.get("namespace") != "d90.orig.v1.tr02.*":
        raise RuntimeError(f"Unexpected Original-02 namespace: {admission.get('namespace')!r}")
    if admission.get("final_records", 0) < 3943 or admission.get("new_records", 0) <= 0:
        raise RuntimeError(f"Backend admission is incomplete: {admission}")

    rights = reports["rights"]
    require_binding(rights, REPORT_PATHS["backend"], "rights/non-overlap")
    for rel in (
        "source/id-ID/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex",
        "source/id-ID/original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex",
        "output/pdf/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf",
        "output/html/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html",
        "output/epub/D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub",
    ):
        require_binding(rights, rel, "rights/non-overlap")
    if rights.get("o018_nonoverlap", {}).get("imported") is not False:
        raise RuntimeError("Rights gate does not prove the O018 exclusion")
    boundary = rights.get("reference_boundary", {})
    if boundary.get("mathematical_witnesses_only") is not True:
        raise RuntimeError("Rights gate does not prove the witness-only boundary")
    if boundary.get("model_provenance") != MODEL:
        raise RuntimeError("Rights gate does not bind the exact model marker")
    if rights.get("upstream_contact") is not False:
        raise RuntimeError("Rights gate indicates upstream contact")

    rereview = reports["rereview"]
    counts = rereview.get("finding_counts", {}).get("remaining_after_corrections")
    if counts is not None and not all_zero(counts):
        raise RuntimeError(f"Independent rereview has open findings: {counts}")
    for key in ("open_findings", "unresolved_findings", "remaining_findings"):
        if key in rereview and not all_zero(rereview[key]):
            raise RuntimeError(f"Independent rereview has open findings in {key}: {rereview[key]!r}")

    # The final rereview is the release-time exact-byte lock for every
    # packaged project file except its own receipt and the authored package
    # notes.  This also catches any post-gate script drift.
    rereview_bound = [
        source
        for _dest, source, _role, _media in MATERIAL
        if source is not None and source != REPORT_PATHS["rereview"]
    ]
    for rel in rereview_bound:
        require_binding(rereview, rel, "independent rereview")

    for dest, source, _role, _media in MATERIAL:
        if source is not None:
            assert_exists(PROJECT / PurePosixPath(source), dest)
    return reports


def package_path(rel: str) -> Path:
    return PACKAGE / PurePosixPath(rel)


def member_record(rel: str, role: str, media: str) -> dict[str, Any]:
    path = package_path(rel)
    return {
        "path": rel,
        "role": role,
        "media_type": media,
        "bytes": path.stat().st_size,
        "sha256": sha_file(path),
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def safe_member(rel: str) -> bool:
    path = PurePosixPath(rel)
    return (
        bool(rel)
        and "\\" not in rel
        and not path.is_absolute()
        and ".." not in path.parts
        and not rel.endswith("/")
    )


def prepare_package(reports: dict[str, dict[str, Any]]) -> list[str]:
    authored = {
        rel: package_path(rel).read_bytes()
        for rel, source, _role, _media in MATERIAL
        if source is None
    }
    if PACKAGE.parent != HERE or PACKAGE.name != "package":
        raise RuntimeError("Unsafe package directory")
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    PACKAGE.mkdir(parents=True)
    for rel, data in authored.items():
        package_path(rel).parent.mkdir(parents=True, exist_ok=True)
        package_path(rel).write_bytes(data)
    for dest, source, _role, _media in MATERIAL:
        if source is None:
            continue
        target = package_path(dest)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT / PurePosixPath(source), target)

    material = [
        member_record(dest, role, media)
        for dest, _source, role, media in MATERIAL
    ]
    reports_summary = {
        key: {
            "path": rel,
            "bytes": (PROJECT / PurePosixPath(rel)).stat().st_size,
            "sha256": sha_file(PROJECT / PurePosixPath(rel)),
            "result": "pass",
        }
        for key, rel in REPORT_PATHS.items()
    }
    admission = reports["backend"]["admission"]
    manifest = {
        "schema": "o015-original-02-compact-release-v1",
        "title": "Optimisasi Lanjut dan Analisis Konveks — Tranche Asli 2: Ketaksamaan Variasional, Operator Monoton, Resolven, dan Pemisahan — Edisi Bahasa Indonesia",
        "release_date": "2026-08-26",
        "status": {
            "tranche": "complete at the exact admitted Original-02 scope",
            "larger_course_edition": "partial",
            "next_cursor": "course-wide cumulative assessment, remaining laboratories, capstone, and full-edition accessibility closure",
        },
        "primary_reader": "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf",
        "reader_order": [
            "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf",
            "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html",
            "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub",
        ],
        "scope": {
            "unit_id": "d90.orig.v1.tr02.unit",
            "segments": 8,
            "source_labels": 53,
            "source_math_surfaces": 294,
            "numbered_display_environments": 45,
            "exercises": 6,
            "hints": 6,
            "complete_solutions": 6,
            "lab": "one deterministic open-computation monotone-splitting lab",
            "stable_id_namespace": admission["namespace"],
        },
        "source_and_component_rights": {
            "new_substantive_layer": "CC BY-SA 4.0",
            "habring_source": {
                "author": "Andreas Habring",
                "title": "Lecture Notes: Convex Optimization",
                "arxiv_version": "2607.11664v1",
                "source_tar_path": "authority/habring/2607.11664v1-source.tar",
                "source_tar_bytes": 230116,
                "source_tar_sha256": "d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748",
                "license": "CC BY 4.0",
            },
            "habring_scaffold": "shinybook.cls exact copy and macros-id.tex localized adaptation; submission-level CC BY 4.0 evidence; class has no separate embedded notice",
            "new_layer_and_scaffold_licenses_are_separate": True,
            "no_blanket_license_claim": True,
        },
        "reference_boundary": {
            "mathematical_witnesses": [
                "Andreas Habring",
                "Christian Clason",
                "Stephen Becker",
                "Mitchell Krock",
                "George J. Minty",
                "R. Tyrrell Rockafellar",
                "Pierre-Louis Lions",
                "Bertrand Mercier",
            ],
            "witness_bytes_packaged": False,
            "third_party_prose_layout_figures_exercises_solutions_or_code_packaged_as_new_material": False,
            "non_endorsement": "Independent edition; no named author, institution, repository, publisher, or source party is represented as endorsing it.",
        },
        "provenance": {
            "human_credits_retained": True,
            "model": MODEL,
        },
        "qa": reports_summary,
        "files": material,
        "backend_policy": {
            "full_dataset_packaged": False,
            "final_records": admission["final_records"],
            "new_records": admission["new_records"],
            "final_id_set_sha256": admission["final_id_set_sha256"],
            "final_id_order_sha256": admission["final_id_order_sha256"],
            "final_record_set_sha256": admission["final_record_set_sha256"],
            "final_line_sequence_sha256": admission["final_line_sequence_sha256"],
            "records_jsonl": admission["jsonl"],
            "records_csv": admission["csv"],
            "reason": "The full backend remains in the repository; this compact package carries its schema, generator, validator, and passing receipts with protected-baseline and exact reconstruction evidence.",
        },
        "excluded": [
            "full backend records.jsonl and records.csv",
            "official Habring source tar and legal-code witness",
            "Becker source and translated companion bytes",
            "mathematical witness PDFs and articles",
            "build trees, caches, rendered QA images, credentials, and raw provenance dumps",
        ],
        "sha256sums_scope": "every ZIP member except SHA256SUMS itself",
        "upstream_contact": False,
    }
    write_json(package_path(MANIFEST_NAME), manifest)
    ordered = [item[0] for item in MATERIAL] + [MANIFEST_NAME]
    sums = "".join(f"{sha_file(package_path(rel))}  {rel}\n" for rel in ordered)
    package_path(SUMS_NAME).write_text(sums, encoding="utf-8", newline="\n")
    members = ordered + [SUMS_NAME]
    if len(members) != 39:
        raise RuntimeError(f"Expected 39 package members, got {len(members)}")
    total_uncompressed = sum(package_path(rel).stat().st_size for rel in members)
    if total_uncompressed > MAX_BYTES:
        raise RuntimeError(
            f"Compact release tree exceeds the {MAX_BYTES}-byte payload cap: "
            f"{total_uncompressed}"
        )
    return members


def text_policy(members: list[str]) -> None:
    short_forbidden = "TT" + "P"
    long_forbidden = "Translation and " + "Transcription Project"
    forbidden = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(short_forbidden)}(?![A-Za-z0-9])|"
        rf"{re.escape(long_forbidden)}"
    )
    for rel in members:
        path = package_path(rel)
        if path.suffix.lower() in {".md", ".txt", ".tex", ".html", ".json"} or path.name == SUMS_NAME:
            text = path.read_text(encoding="utf-8")
            if forbidden.search(text):
                raise RuntimeError(f"Forbidden umbrella-label prose in {rel}")
    for rel in (
        "README_ORIGINAL_02.md",
        "RIGHTS_AND_PROVENANCE_ORIGINAL_02.md",
        "LICENSE_ORIGINAL_CC_BY-SA-4.0.md",
        "LICENSE_HABRING_SCAFFOLD_CC_BY-4.0.md",
    ):
        if package_path(rel).read_text(encoding="utf-8").count(MODEL) != 1:
            raise RuntimeError(f"Exact model marker is not present exactly once in {rel}")


def build_zip(path: Path, members: list[str]) -> None:
    with zipfile.ZipFile(
        path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        allowZip64=True,
    ) as archive:
        for rel in members:
            if not safe_member(rel):
                raise RuntimeError(f"Unsafe ZIP member {rel!r}")
            info = zipfile.ZipInfo(rel, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(
                info,
                package_path(rel).read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def verify_zip(members: list[str]) -> list[dict[str, Any]]:
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC test failed")
        infos = archive.infolist()
        if [item.filename for item in infos] != members:
            raise RuntimeError("ZIP inventory or reader-first order mismatch")
        if len(infos) != len({item.filename for item in infos}):
            raise RuntimeError("ZIP contains duplicate member names")
        entries = []
        for info in infos:
            if not safe_member(info.filename) or info.date_time != STAMP:
                raise RuntimeError(f"Unsafe or nondeterministic ZIP entry {info.filename}")
            data = archive.read(info.filename)
            if data != package_path(info.filename).read_bytes():
                raise RuntimeError(f"ZIP entry differs from package tree: {info.filename}")
            entries.append(
                {
                    "path": info.filename,
                    "bytes": len(data),
                    "compressed_bytes": info.compress_size,
                    "crc32": f"{info.CRC:08x}",
                    "sha256": sha_bytes(data),
                    "timestamp": "2026-08-26T00:00:00",
                }
            )
    sums = package_path(SUMS_NAME).read_text(encoding="utf-8").splitlines()
    expected = [
        f"{sha_file(package_path(rel))}  {rel}"
        for rel in members[:-1]
    ]
    if sums != expected:
        raise RuntimeError("SHA256SUMS mismatch")
    return entries


def main() -> None:
    # All gates precede package-tree mutation.  Missing backend, rights, or
    # rereview receipts therefore cannot emit a manifest, checksum file, ZIP,
    # or verification receipt.
    reports = validate_inputs()
    members = prepare_package(reports)
    text_policy(members)
    run1 = HERE / f".{ZIP_NAME}.run1.tmp"
    run2 = HERE / f".{ZIP_NAME}.run2.tmp"
    for path in (run1, run2):
        if path.exists():
            path.unlink()
        build_zip(path, members)
    if run1.read_bytes() != run2.read_bytes():
        raise RuntimeError("Two ZIP builds are not byte-identical")
    os.replace(run1, ZIP_PATH)
    run2.unlink()
    if ZIP_PATH.stat().st_size > MAX_BYTES:
        raise RuntimeError("Compact release exceeds the 500,000,000-byte cap")
    entries = verify_zip(members)
    receipt = {
        "schema": "o015-original-02-local-release-verification-v1",
        "result": "pass",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release_directory": HERE.relative_to(PROJECT).as_posix(),
        "package_directory": PACKAGE.relative_to(PROJECT).as_posix(),
        "zip": {
            "path": ZIP_PATH.relative_to(PROJECT).as_posix(),
            "bytes": ZIP_PATH.stat().st_size,
            "sha256": sha_file(ZIP_PATH),
            "entry_count": len(entries),
            "entries": entries,
            "fixed_timestamp": "2026-08-26T00:00:00",
            "byte_identical_two_builds": True,
            "compression": "ZIP_DEFLATED level 9",
            "contains_itself": False,
        },
        "verification": {
            "all_final_receipts_pass": True,
            "frozen_core_identities_match": True,
            "final_receipt_identity_bindings_match": True,
            "independent_rereview_has_no_open_findings": True,
            "crc_test": "pass",
            "entry_order_matches_explicit_39_member_reader_first_inventory": True,
            "entry_bytes_match_package_tree": True,
            "sha256sums_verified": True,
            "unique_entry_names": True,
            "absolute_entries": 0,
            "parent_traversal_entries": 0,
            "backslash_entries": 0,
            "directory_entries": 0,
            "forbidden_umbrella_label_occurrences_in_text_members": 0,
            "credentials_included": False,
            "network_used": False,
            "git_used": False,
            "payload_cap_bytes": MAX_BYTES,
        },
        "omissions": {
            "full_backend_dataset": True,
            "official_habring_source_tar_and_legalcode": True,
            "becker_and_mathematical_witness_bytes": True,
            "build_trees_caches_rendered_images_credentials_raw_provenance": True,
        },
        "model_provenance": MODEL,
    }
    write_json(RECEIPT_PATH, receipt)
    print(
        json.dumps(
            {
                "result": "pass",
                "zip": ZIP_PATH.relative_to(PROJECT).as_posix(),
                "bytes": ZIP_PATH.stat().st_size,
                "sha256": sha_file(ZIP_PATH),
                "entries": len(entries),
                "receipt": RECEIPT_PATH.relative_to(PROJECT).as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
