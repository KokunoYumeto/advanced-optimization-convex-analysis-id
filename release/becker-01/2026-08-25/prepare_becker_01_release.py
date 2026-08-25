#!/usr/bin/env python3
"""Build and verify the bounded Becker-01 continuation bundle offline."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PACKAGE = HERE / "package"
ZIP_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_BECKER_01_2026.08.25.zip"
ZIP_PATH = HERE / ZIP_NAME
RECEIPT_PATH = HERE / "local-verification-becker-01.json"
FIXED_ZIP_TIMESTAMP = (2026, 8, 25, 0, 0, 0)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
COMMIT = "98ed6930084c435ba0f675f7646ced1f2fd8729e"
TREE = "f04670e3f7be3d4836c380fd8bd31883e0b992c9"
LICENSE_SHA256 = "c026320fa977e084507f66ce2d4de70f3955b39a590f5cdd6e10e690e7a13cac"
ARCHIVE = (
    PROJECT
    / "authority/becker/archive"
    / f"convex-optimization-class-{COMMIT}.zip"
)
ARCHIVE_LICENSE_ENTRY = f"convex-optimization-class-{COMMIT}/LICENSE"

COPY_MAP = [
    (
        "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.pdf",
        "output/pdf/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.pdf",
        "primary PDF reader",
        "application/pdf",
    ),
    (
        "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html",
        "output/html/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html",
        "responsive semantic HTML reader",
        "text/html",
    ),
    (
        "source/id-ID/becker-01-dualitas-lagrange-slater-kkt-id.tex",
        "source/id-ID/becker-01-dualitas-lagrange-slater-kkt-id.tex",
        "Indonesian translated body",
        "application/x-tex",
    ),
    (
        "source/id-ID/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex",
        "source/id-ID/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex",
        "Indonesian standalone reader wrapper",
        "application/x-tex",
    ),
    (
        "source/id-ID/macros-id.tex",
        "source/id-ID/macros-id.tex",
        "minimum shared Indonesian LaTeX macros",
        "application/x-tex",
    ),
    (
        "source/id-ID/shinybook.cls",
        "source/id-ID/shinybook.cls",
        "minimum shared LaTeX document class",
        "application/x-tex",
    ),
    (
        "source/en/becker-01-lagrange-slater-kkt-source.tex",
        "source/en/becker-01-lagrange-slater-kkt-source.tex",
        "exact extracted English source witness",
        "application/x-tex",
    ),
    (
        "qa/BECKER_01_SOURCE_BOUNDARY.json",
        "qa/BECKER_01_SOURCE_BOUNDARY.json",
        "source-boundary receipt",
        "application/json",
    ),
    (
        "authority/BECKER_AUTHORITY_FREEZE.md",
        "authority/becker/BECKER_AUTHORITY_FREEZE.md",
        "final Becker authority and editable-closure report",
        "text/markdown",
    ),
    (
        "qa/BECKER_01_INDEPENDENT_REREVIEW.md",
        "qa/BECKER_01_INDEPENDENT_REREVIEW.md",
        "independent final semantic rereview",
        "text/markdown",
    ),
    (
        "qa/BECKER_01_MATH_VALIDATION.json",
        "qa/BECKER_01_MATH_VALIDATION.json",
        "open mathematics validation receipt",
        "application/json",
    ),
    (
        "qa/BECKER_01_PDF_BUILD.json",
        "qa/BECKER_01_PDF_BUILD.json",
        "deterministic PDF build receipt",
        "application/json",
    ),
    (
        "qa/BECKER_01_PDF_VISUAL_QA.json",
        "qa/BECKER_01_PDF_VISUAL_QA.json",
        "PDF visual inspection receipt",
        "application/json",
    ),
    (
        "qa/BECKER_01_HTML_BUILD.json",
        "qa/BECKER_01_HTML_BUILD.json",
        "deterministic HTML build receipt",
        "application/json",
    ),
    (
        "qa/BECKER_01_BROWSER_VISUAL_QA.json",
        "qa/BECKER_01_BROWSER_VISUAL_QA.json",
        "responsive browser and visual QA receipt",
        "application/json",
    ),
    (
        "qa/BECKER_01_BACKEND_EXTENSION.json",
        "qa/BECKER_01_BACKEND_EXTENSION.json",
        "stable-ID backend extension receipt",
        "application/json",
    ),
]

AUTHORED_FILES = [
    (
        "README_BECKER_01.md",
        "reader-first documentation, scope, credits, rights, and caveats",
        "text/markdown",
    ),
    (
        "LICENSE_TRANSLATION_CC_BY-SA-4.0.md",
        "CC BY-SA 4.0 scope for translation, corrections, and new prose",
        "text/markdown",
    ),
]

QA_FILES = {
    "source_boundary": "qa/BECKER_01_SOURCE_BOUNDARY.json",
    "math": "qa/BECKER_01_MATH_VALIDATION.json",
    "pdf_build": "qa/BECKER_01_PDF_BUILD.json",
    "pdf_visual": "qa/BECKER_01_PDF_VISUAL_QA.json",
    "html_build": "qa/BECKER_01_HTML_BUILD.json",
    "browser": "qa/BECKER_01_BROWSER_VISUAL_QA.json",
    "backend": "qa/BECKER_01_BACKEND_EXTENSION.json",
}


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_identity(path: Path, record: dict, label: str) -> None:
    actual_bytes = path.stat().st_size
    actual_hash = digest_file(path)
    if actual_bytes != int(record["bytes"]) or actual_hash != record["sha256"]:
        raise RuntimeError(
            f"{label} identity mismatch: {actual_bytes}/{actual_hash} != "
            f"{record['bytes']}/{record['sha256']}"
        )


def validate_live_inputs() -> dict:
    reports = {key: load_json(PROJECT / rel) for key, rel in QA_FILES.items()}
    expected_results = {
        "source_boundary": "pass",
        "math": "PASS",
        "pdf_build": "pass",
        "pdf_visual": "pass",
        "html_build": "pass",
        "browser": "pass",
        "backend": "pass",
    }
    for key, expected in expected_results.items():
        observed = reports[key].get("result", reports[key].get("status"))
        if observed != expected:
            raise RuntimeError(f"QA gate {key} is {observed!r}, expected {expected!r}")

    pdf = PROJECT / "output/pdf/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.pdf"
    html = PROJECT / "output/html/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html"
    body = PROJECT / "source/id-ID/becker-01-dualitas-lagrange-slater-kkt-id.tex"
    wrapper = PROJECT / "source/id-ID/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex"
    witness = PROJECT / "source/en/becker-01-lagrange-slater-kkt-source.tex"

    assert_identity(pdf, reports["pdf_build"]["artifact"], "PDF/build receipt")
    assert_identity(pdf, reports["pdf_visual"]["artifact"], "PDF/visual receipt")
    assert_identity(html, reports["html_build"]["artifact"], "HTML/build receipt")
    assert_identity(html, reports["browser"]["artifact"], "HTML/browser receipt")

    math_inputs = {
        item["path"]: item for item in reports["math"]["inputs"].values()
    }
    assert_identity(
        body,
        math_inputs["source/id-ID/becker-01-dualitas-lagrange-slater-kkt-id.tex"],
        "Indonesian body/math receipt",
    )
    assert_identity(
        wrapper,
        math_inputs["source/id-ID/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex"],
        "wrapper/math receipt",
    )
    assert_identity(
        witness,
        reports["source_boundary"]["combined_witness"],
        "English witness/source-boundary receipt",
    )

    if reports["source_boundary"]["authority"]["commit"] != COMMIT:
        raise RuntimeError("Source-boundary commit differs from frozen Becker commit")
    if reports["backend"]["source_commit"] != COMMIT:
        raise RuntimeError("Backend receipt commit differs from frozen Becker commit")
    if not reports["pdf_build"].get("byte_identical_clean_builds"):
        raise RuntimeError("PDF is not recorded as byte-identical across clean builds")
    if not reports["html_build"].get("byte_identical_builds"):
        raise RuntimeError("HTML is not recorded as byte-identical across clean builds")
    if reports["browser"].get("console_warnings_or_errors") != 0:
        raise RuntimeError("Browser QA records console warnings or errors")

    return reports


def extract_exact_mit_notice() -> None:
    with zipfile.ZipFile(ARCHIVE, "r") as archive:
        data = archive.read(ARCHIVE_LICENSE_ENTRY)
    if len(data) != 1071 or digest_bytes(data) != LICENSE_SHA256:
        raise RuntimeError("Frozen archive root MIT notice does not match authority freeze")
    (PACKAGE / "LICENSE_BECKER_MIT.txt").write_bytes(data)


def copy_materials() -> None:
    for dest_rel, source_rel, _role, _media in COPY_MAP:
        destination = PACKAGE / PurePosixPath(dest_rel)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT / PurePosixPath(source_rel), destination)


def file_record(rel: str, role: str, media_type: str) -> dict:
    path = PACKAGE / PurePosixPath(rel)
    return {
        "bytes": path.stat().st_size,
        "media_type": media_type,
        "path": rel,
        "role": role,
        "sha256": digest_file(path),
    }


def build_manifest(reports: dict) -> dict:
    material = [
        file_record(dest, role, media)
        for dest, _source, role, media in COPY_MAP
    ]
    material.extend(file_record(dest, role, media) for dest, role, media in AUTHORED_FILES)
    material.append(
        file_record(
            "LICENSE_BECKER_MIT.txt",
            "exact root MIT notice from the frozen official archive",
            "text/plain",
        )
    )
    by_path = {item["path"]: item for item in material}
    reader_order = [
        by_path["D90-BECKER-01-dualitas-lagrange-slater-kkt-id.pdf"],
        by_path["D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html"],
    ]
    boundary = reports["source_boundary"]
    return {
        "schema": "o015-becker-01-compact-release-v1",
        "title": "Optimisasi Lanjut dan Analisis Konveks — Modul Becker 1: Dualitas Lagrange, Slater, dan KKT — Edisi Bahasa Indonesia",
        "release_date": "2026-08-25",
        "status": {
            "module": "complete at the admitted source boundary",
            "larger_course_edition": "partial",
        },
        "primary_reader": reader_order[0]["path"],
        "reader_order": [item["path"] for item in reader_order],
        "source_authority": {
            "repository": "https://github.com/stephenbeckr/convex-optimization-class",
            "commit": COMMIT,
            "tree": TREE,
            "source_path": boundary["authority"]["source_path"],
            "source_sha256": boundary["authority"]["source_sha256"],
            "typed_notes_credit": "Mitchell Krock",
            "repository_author": "Stephen Becker",
            "license": "MIT",
            "root_license_sha256": LICENSE_SHA256,
            "selected_ranges": boundary["selected_ranges"],
            "explicit_exclusions": boundary["explicit_exclusions"],
        },
        "rights": {
            "source_material_and_english_witness": "MIT; full notice in LICENSE_BECKER_MIT.txt",
            "indonesian_translation_corrections_connective_text_and_new_release_documentation": "CC BY-SA 4.0; scope in LICENSE_TRANSLATION_CC_BY-SA-4.0.md",
            "component_specific": True,
            "no_blanket_license_claim": True,
        },
        "credits": ["Stephen Becker", "Mitchell Krock"],
        "nonendorsement": "Independent edition; no endorsement by the authors, University of Colorado Boulder, or other source parties.",
        "model_provenance": MODEL,
        "accessibility": {
            "responsive_semantic_html": True,
            "pdf_searchable": True,
            "pdf_language": "id-ID",
            "pdf_tagged": False,
        },
        "qa": {
            "source_boundary": reports["source_boundary"].get("result"),
            "open_math_gates": reports["math"].get("gate_count"),
            "pdf_build": reports["pdf_build"].get("result"),
            "pdf_visual": reports["pdf_visual"].get("result"),
            "html_build": reports["html_build"].get("result"),
            "browser": reports["browser"].get("result"),
            "backend": reports["backend"].get("result"),
            "stable_id_namespace": reports["backend"].get("namespace"),
            "new_backend_records": reports["backend"].get("new_record_count"),
            "backend_dataset_packaged": False,
        },
        "files": sorted(material, key=lambda item: item["path"]),
        "excluded_from_compact_payload": [
            "164.5 MB official source archive (identity remains in authority evidence)",
            "full multi-megabyte backend dataset (maintained by the edition repository)",
            "build trees, caches, rendered QA images, credentials, and bulk provenance dumps",
        ],
        "sha256sums_scope": "every ZIP member except SHA256SUMS itself",
        "zip_identity_location": "local-verification-becker-01.json outside the ZIP",
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def safe_member(rel: str) -> bool:
    posix = PurePosixPath(rel)
    return (
        bool(rel)
        and "\\" not in rel
        and not posix.is_absolute()
        and ".." not in posix.parts
        and not rel.endswith("/")
        and rel != ZIP_NAME
    )


def build_zip(path: Path, ordered_members: list[str]) -> None:
    with zipfile.ZipFile(
        path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        allowZip64=True,
    ) as archive:
        for rel in ordered_members:
            if not safe_member(rel):
                raise RuntimeError(f"Unsafe ZIP member: {rel!r}")
            data = (PACKAGE / PurePosixPath(rel)).read_bytes()
            info = zipfile.ZipInfo(rel, FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_zip(ordered_members: list[str]) -> list[dict]:
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC/integrity test failed")
        if names != ordered_members:
            raise RuntimeError("ZIP entry order or inventory differs from the explicit list")
        if len(names) != len(set(names)):
            raise RuntimeError("ZIP contains duplicate entry names")
        entries = []
        for info in infos:
            if not safe_member(info.filename):
                raise RuntimeError(f"Unsafe ZIP entry: {info.filename!r}")
            if info.date_time != FIXED_ZIP_TIMESTAMP:
                raise RuntimeError(f"Non-fixed ZIP timestamp: {info.filename}")
            data = archive.read(info.filename)
            source = (PACKAGE / PurePosixPath(info.filename)).read_bytes()
            if data != source:
                raise RuntimeError(f"ZIP entry differs from package source: {info.filename}")
            entries.append(
                {
                    "bytes": len(data),
                    "compressed_bytes": info.compress_size,
                    "path": info.filename,
                    "sha256": digest_bytes(data),
                    "timestamp": "2026-08-25T00:00:00",
                }
            )
    return entries


def verify_checksums(ordered_without_sums: list[str]) -> None:
    lines = (PACKAGE / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    expected = [
        f"{digest_file(PACKAGE / PurePosixPath(rel))}  {rel}"
        for rel in ordered_without_sums
    ]
    if lines != expected:
        raise RuntimeError("SHA256SUMS content does not bind the expected members")


def verify_text_policy(ordered_members: list[str]) -> None:
    textual_suffixes = {".md", ".txt", ".tex", ".html", ".json", ""}
    forbidden = re.compile(r"(?<![A-Za-z0-9])TTP(?![A-Za-z0-9])|Translation and Transcription Project")
    for rel in ordered_members:
        path = PACKAGE / PurePosixPath(rel)
        if path.suffix.lower() not in textual_suffixes and path.name != "SHA256SUMS":
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        if forbidden.search(text):
            raise RuntimeError(f"Forbidden project-label prose found in {rel}")
    for rel in [
        "README_BECKER_01.md",
        "LICENSE_TRANSLATION_CC_BY-SA-4.0.md",
        "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html",
        "source/id-ID/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex",
    ]:
        if MODEL not in (PACKAGE / PurePosixPath(rel)).read_text(encoding="utf-8"):
            raise RuntimeError(f"Exact model marker absent from {rel}")


def main() -> None:
    reports = validate_live_inputs()
    copy_materials()
    extract_exact_mit_notice()

    for rel, _role, _media in AUTHORED_FILES:
        if not (PACKAGE / rel).is_file():
            raise RuntimeError(f"Authored release file is absent: {rel}")

    manifest = build_manifest(reports)
    manifest_path = PACKAGE / "release-manifest-becker-01.json"
    write_json(manifest_path, manifest)

    ordered_without_sums = [
        "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.pdf",
        "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html",
        "README_BECKER_01.md",
        "LICENSE_BECKER_MIT.txt",
        "LICENSE_TRANSLATION_CC_BY-SA-4.0.md",
        "source/id-ID/D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex",
        "source/id-ID/becker-01-dualitas-lagrange-slater-kkt-id.tex",
        "source/id-ID/macros-id.tex",
        "source/id-ID/shinybook.cls",
        "source/en/becker-01-lagrange-slater-kkt-source.tex",
        "qa/BECKER_01_SOURCE_BOUNDARY.json",
        "authority/BECKER_AUTHORITY_FREEZE.md",
        "qa/BECKER_01_INDEPENDENT_REREVIEW.md",
        "qa/BECKER_01_MATH_VALIDATION.json",
        "qa/BECKER_01_PDF_BUILD.json",
        "qa/BECKER_01_PDF_VISUAL_QA.json",
        "qa/BECKER_01_HTML_BUILD.json",
        "qa/BECKER_01_BROWSER_VISUAL_QA.json",
        "qa/BECKER_01_BACKEND_EXTENSION.json",
        "release-manifest-becker-01.json",
    ]
    sums = "".join(
        f"{digest_file(PACKAGE / PurePosixPath(rel))}  {rel}\n"
        for rel in ordered_without_sums
    )
    (PACKAGE / "SHA256SUMS").write_text(sums, encoding="utf-8", newline="\n")
    ordered_members = ordered_without_sums + ["SHA256SUMS"]

    verify_checksums(ordered_without_sums)
    verify_text_policy(ordered_members)

    temp_one = HERE / f".{ZIP_NAME}.run1.tmp"
    temp_two = HERE / f".{ZIP_NAME}.run2.tmp"
    for temp in (temp_one, temp_two):
        if temp.exists():
            temp.unlink()
        build_zip(temp, ordered_members)
    first_hash = digest_file(temp_one)
    second_hash = digest_file(temp_two)
    if temp_one.read_bytes() != temp_two.read_bytes() or first_hash != second_hash:
        raise RuntimeError("Two clean ZIP builds are not byte-identical")
    os.replace(temp_one, ZIP_PATH)
    temp_two.unlink()

    entries = verify_zip(ordered_members)
    receipt = {
        "schema": "o015-becker-01-local-release-verification-v1",
        "result": "pass",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release_directory": str(HERE),
        "package_directory": str(PACKAGE),
        "zip": {
            "path": str(ZIP_PATH),
            "bytes": ZIP_PATH.stat().st_size,
            "sha256": digest_file(ZIP_PATH),
            "entry_count": len(entries),
            "entries": entries,
            "fixed_timestamp": "2026-08-25T00:00:00",
            "byte_identical_two_builds": True,
            "compression": "ZIP_DEFLATED level 9",
            "contains_itself": False,
        },
        "verification": {
            "crc_test": "pass",
            "entry_order_matches_explicit_reader_first_inventory": True,
            "entry_bytes_match_package_tree": True,
            "sha256sums_verified": True,
            "unique_entry_names": True,
            "absolute_entries": 0,
            "parent_traversal_entries": 0,
            "backslash_entries": 0,
            "directory_entries": 0,
            "forbidden_project_label_occurrences_in_text_members": 0,
            "credentials_included": False,
            "network_used": False,
            "git_used": False,
        },
        "omissions": {
            "raw_official_archive": True,
            "full_backend_dataset": True,
            "build_trees_and_caches": True,
            "bulk_provenance_dumps": True,
        },
        "model_provenance": MODEL,
    }
    write_json(RECEIPT_PATH, receipt)
    print(
        json.dumps(
            {
                "result": "pass",
                "zip": str(ZIP_PATH),
                "bytes": ZIP_PATH.stat().st_size,
                "sha256": digest_file(ZIP_PATH),
                "entries": len(entries),
                "receipt": str(RECEIPT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
