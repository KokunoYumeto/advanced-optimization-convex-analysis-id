#!/usr/bin/env python3
"""Build and verify the compact Becker-03 variance-reduction release."""

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
ZIP_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_BECKER_03_2026.08.25.zip"
ZIP_PATH = HERE / ZIP_NAME
RECEIPT_PATH = HERE / "local-verification-becker-03.json"
STAMP = (2026, 8, 25, 0, 0, 0)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
COMMIT = "98ed6930084c435ba0f675f7646ced1f2fd8729e"
TREE = "f04670e3f7be3d4836c380fd8bd31883e0b992c9"
LICENSE_SHA256 = "c026320fa977e084507f66ce2d4de70f3955b39a590f5cdd6e10e690e7a13cac"
ARCHIVE = PROJECT / "authority/becker/archive" / f"convex-optimization-class-{COMMIT}.zip"
ARCHIVE_LICENSE = f"convex-optimization-class-{COMMIT}/LICENSE"
SAGA_PAPER = PROJECT / "authority/becker/related/saga-arxiv-1407.0202v3.pdf"
SAGA_PAPER_BYTES = 516033
SAGA_PAPER_SHA256 = "b0177cd77447c7469ca31bdfbe7773f604320a9878a46b777c899d9b6fc37c7e"

FILES = [
    ("D90-BECKER-03-reduksi-varians-id.pdf", "output/pdf/D90-BECKER-03-reduksi-varians-id.pdf", "primary PDF reader", "application/pdf"),
    ("D90-BECKER-03-reduksi-varians-id.html", "output/html/D90-BECKER-03-reduksi-varians-id.html", "responsive semantic HTML reader", "text/html"),
    ("source/id-ID/becker-03-reduksi-varians-id.tex", "source/id-ID/becker-03-reduksi-varians-id.tex", "Indonesian translated body", "application/x-tex"),
    ("source/id-ID/D90-BECKER-03-reduksi-varians-id.tex", "source/id-ID/D90-BECKER-03-reduksi-varians-id.tex", "standalone Indonesian reader wrapper", "application/x-tex"),
    ("source/id-ID/macros-id.tex", "source/id-ID/macros-id.tex", "shared Indonesian LaTeX macros", "application/x-tex"),
    ("source/id-ID/shinybook.cls", "source/id-ID/shinybook.cls", "shared LaTeX document class", "application/x-tex"),
    ("source/en/becker-03-variance-reduction-source.tex", "source/en/becker-03-variance-reduction-source.tex", "exact English source witness", "application/x-tex"),
    ("authority/BECKER_AUTHORITY_FREEZE.md", "authority/becker/BECKER_AUTHORITY_FREEZE.md", "authority and editable-closure report", "text/markdown"),
    ("qa/BECKER_03_SOURCE_BOUNDARY.json", "qa/BECKER_03_SOURCE_BOUNDARY.json", "source-boundary receipt", "application/json"),
    ("qa/BECKER_03_MATH_VALIDATION.json", "qa/BECKER_03_MATH_VALIDATION.json", "open mathematics validation", "application/json"),
    ("qa/BECKER_03_PDF_BUILD.json", "qa/BECKER_03_PDF_BUILD.json", "deterministic PDF build receipt", "application/json"),
    ("qa/BECKER_03_PDF_VISUAL_QA.json", "qa/BECKER_03_PDF_VISUAL_QA.json", "all-page PDF visual QA", "application/json"),
    ("qa/BECKER_03_HTML_BUILD.json", "qa/BECKER_03_HTML_BUILD.json", "deterministic HTML build receipt", "application/json"),
    ("qa/BECKER_03_HTML_BROWSER_QA.json", "qa/BECKER_03_HTML_BROWSER_QA.json", "desktop/tablet/phone browser QA", "application/json"),
    ("qa/BECKER_03_INDEPENDENT_REREVIEW.json", "qa/BECKER_03_INDEPENDENT_REREVIEW.json", "independent final rereview", "application/json"),
    ("qa/BECKER_03_BACKEND_EXTENSION.json", "qa/BECKER_03_BACKEND_EXTENSION.json", "stable-ID backend extension receipt", "application/json"),
    ("qa/BECKER_03_BACKEND_VALIDATION.json", "qa/BECKER_03_BACKEND_VALIDATION.json", "independent stable-ID validation", "application/json"),
]

AUTHORED = [
    ("README_BECKER_03.md", "reader-first scope, credits, rights, and caveats", "text/markdown"),
    ("LICENSE_TRANSLATION_CC_BY-SA-4.0.md", "CC BY-SA 4.0 scope for new Indonesian material", "text/markdown"),
]

REPORTS = {
    "boundary": "qa/BECKER_03_SOURCE_BOUNDARY.json",
    "math": "qa/BECKER_03_MATH_VALIDATION.json",
    "pdf": "qa/BECKER_03_PDF_BUILD.json",
    "pdf_visual": "qa/BECKER_03_PDF_VISUAL_QA.json",
    "html": "qa/BECKER_03_HTML_BUILD.json",
    "browser": "qa/BECKER_03_HTML_BROWSER_QA.json",
    "rereview": "qa/BECKER_03_INDEPENDENT_REREVIEW.json",
    "backend": "qa/BECKER_03_BACKEND_EXTENSION.json",
    "backend_validation": "qa/BECKER_03_BACKEND_VALIDATION.json",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_identity(path: Path, record: dict, label: str) -> None:
    got = (path.stat().st_size, sha_file(path))
    wanted = (int(record["bytes"]), record["sha256"])
    if got != wanted:
        raise RuntimeError(f"{label}: {got} != {wanted}")


def validate_inputs() -> dict[str, dict]:
    reports = {name: load_json(PROJECT / rel) for name, rel in REPORTS.items()}
    for name, report in reports.items():
        observed = report.get("result", report.get("status"))
        if observed not in {"pass", "PASS"}:
            raise RuntimeError(f"QA report {name} is not passing: {observed!r}")

    pdf = PROJECT / "output/pdf/D90-BECKER-03-reduksi-varians-id.pdf"
    html = PROJECT / "output/html/D90-BECKER-03-reduksi-varians-id.html"
    body = PROJECT / "source/id-ID/becker-03-reduksi-varians-id.tex"
    wrapper = PROJECT / "source/id-ID/D90-BECKER-03-reduksi-varians-id.tex"
    witness = PROJECT / "source/en/becker-03-variance-reduction-source.tex"
    backend_jsonl = PROJECT / "backend/records.jsonl"
    backend_csv = PROJECT / "backend/records.csv"

    assert_identity(pdf, reports["pdf"]["artifact"], "PDF/build")
    assert_identity(pdf, reports["pdf_visual"]["artifact"], "PDF/visual")
    assert_identity(html, reports["html"]["artifact"], "HTML/build")
    assert_identity(html, reports["browser"]["artifact"], "HTML/browser")
    assert_identity(witness, reports["boundary"]["combined_witness"], "witness/boundary")
    math_inputs = reports["math"]["inputs"]
    assert_identity(body, math_inputs["target"], "body/math")
    assert_identity(wrapper, math_inputs["wrapper"], "wrapper/math")
    assert_identity(SAGA_PAPER, math_inputs["primary_saga_paper"], "SAGA paper/math")
    if (SAGA_PAPER.stat().st_size, sha_file(SAGA_PAPER)) != (SAGA_PAPER_BYTES, SAGA_PAPER_SHA256):
        raise RuntimeError("Primary SAGA result witness identity mismatch")

    rereview_sources = {item["path"]: item for item in reports["rereview"]["live_sources"]}
    for path in (body, wrapper, witness):
        rel = path.relative_to(PROJECT).as_posix()
        if rel not in rereview_sources:
            raise RuntimeError(f"Independent rereview omitted {rel}")
        assert_identity(path, rereview_sources[rel], f"{rel}/rereview")

    boundary = reports["boundary"]
    if boundary["authority"]["commit"] != COMMIT:
        raise RuntimeError("Source boundary is not bound to the frozen Becker commit")
    if not boundary["combined_witness"]["interior_exact_source_slice_match"]:
        raise RuntimeError("English witness does not match the exact frozen source slice")
    selected = boundary["selected_ranges"]
    if len(selected) != 1 or (selected[0]["first_line"], selected[0]["last_line"], selected[0]["bytes"]) != (2971, 2988, 900):
        raise RuntimeError("Unexpected Becker-03 source boundary")
    if boundary["outside_range_material_imported"] or boundary["document_terminator_imported"]:
        raise RuntimeError("Source-boundary exclusion failed")
    if reports["backend"]["protected_baseline"]["record_count"] != 3430:
        raise RuntimeError("Backend baseline is not the exact 3,430-record Becker-02 state")
    if reports["backend"]["new_record_count"] != 155 or reports["backend"]["new_entity_counts"].get("relation") != 82:
        raise RuntimeError("Backend does not contain the exact 155-record Becker-03 closure")
    if reports["backend_validation"]["admission"]["final_records"] != 3585:
        raise RuntimeError("Backend final count is not 3,585")
    if not reports["backend_validation"]["protected_baseline"]["record_bytes_and_relative_order_stable"]:
        raise RuntimeError("Protected backend records are not byte/order stable")
    assert_identity(backend_jsonl, reports["backend"]["jsonl"], "backend JSONL/extension")
    assert_identity(backend_csv, reports["backend"]["csv"], "backend CSV/extension")
    assert_identity(backend_jsonl, reports["backend_validation"]["admission"]["jsonl"], "backend JSONL/validation")
    assert_identity(backend_csv, reports["backend_validation"]["admission"]["csv"], "backend CSV/validation")
    if reports["rereview"]["findings"] != {"P1": 0, "P2": 0, "P3": 0}:
        raise RuntimeError("Independent rereview is not clean")
    return reports


def file_record(rel: str, role: str, media: str) -> dict:
    path = PACKAGE / PurePosixPath(rel)
    return {
        "bytes": path.stat().st_size,
        "media_type": media,
        "path": rel,
        "role": role,
        "sha256": sha_file(path),
    }


def safe_member(rel: str) -> bool:
    path = PurePosixPath(rel)
    return bool(rel) and "\\" not in rel and not path.is_absolute() and ".." not in path.parts and not rel.endswith("/")


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def prepare_package(reports: dict[str, dict]) -> list[str]:
    authored_bytes = {rel: (PACKAGE / rel).read_bytes() for rel, _role, _media in AUTHORED}
    if PACKAGE.parent != HERE or PACKAGE.name != "package":
        raise RuntimeError("Unsafe package directory")
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    PACKAGE.mkdir(parents=True)
    for rel, data in authored_bytes.items():
        (PACKAGE / rel).write_bytes(data)
    for dest, source, _role, _media in FILES:
        target = PACKAGE / PurePosixPath(dest)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT / PurePosixPath(source), target)
    with zipfile.ZipFile(ARCHIVE, "r") as archive:
        license_data = archive.read(ARCHIVE_LICENSE)
    if len(license_data) != 1071 or sha_bytes(license_data) != LICENSE_SHA256:
        raise RuntimeError("Frozen MIT notice identity mismatch")
    (PACKAGE / "LICENSE_BECKER_MIT.txt").write_bytes(license_data)

    material = [file_record(dest, role, media) for dest, _source, role, media in FILES]
    material += [file_record(dest, role, media) for dest, role, media in AUTHORED]
    material.append(file_record("LICENSE_BECKER_MIT.txt", "exact root MIT notice", "text/plain"))
    boundary = reports["boundary"]
    manifest = {
        "schema": "o015-becker-03-compact-release-v1",
        "title": "Optimisasi Lanjut dan Analisis Konveks — Modul Becker 3: Reduksi Varians untuk SAA — Edisi Bahasa Indonesia",
        "release_date": "2026-08-25",
        "status": {"module": "complete at the exact admitted source boundary", "larger_course_edition": "partial"},
        "primary_reader": "D90-BECKER-03-reduksi-varians-id.pdf",
        "reader_order": ["D90-BECKER-03-reduksi-varians-id.pdf", "D90-BECKER-03-reduksi-varians-id.html"],
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
        "result_witness": {
            "citation": "Aaron Defazio, Francis Bach, and Simon Lacoste-Julien, SAGA (2014), arXiv:1407.0202v3",
            "local_sha256": SAGA_PAPER_SHA256,
            "redistributed_in_package": False,
            "use": "primary check of mathematical hypotheses and rate constants; no prose or layout copied",
        },
        "rights": {
            "source_material_and_english_witness": "MIT; full notice in LICENSE_BECKER_MIT.txt",
            "indonesian_translation_corrections_connective_text_exercises_solutions_and_new_documentation": "CC BY-SA 4.0",
            "component_specific": True,
            "no_blanket_license_claim": True,
        },
        "credits": ["Stephen Becker", "Mitchell Krock", "Aaron Defazio", "Francis Bach", "Simon Lacoste-Julien"],
        "corrections": "O015-BECKER-ADV-0020 through O015-BECKER-ADV-0024",
        "nonendorsement": "Independent edition; no endorsement by named authors, University of Colorado Boulder, or other source parties.",
        "model_provenance": MODEL,
        "accessibility": {"responsive_semantic_html": True, "pdf_searchable": True, "pdf_language": "id-ID", "pdf_tagged": False},
        "qa": {
            "source_boundary": "pass",
            "open_math_gates": reports["math"]["gate_count"],
            "pdf_build": "pass",
            "pdf_visual": "pass",
            "html_build": "pass",
            "browser": "pass",
            "independent_rereview": "P1=0/P2=0/P3=0",
            "backend": "pass",
            "stable_id_namespace": reports["backend"]["namespace"],
            "new_backend_records": reports["backend"]["new_record_count"],
            "backend_dataset_packaged": False,
        },
        "files": sorted(material, key=lambda item: item["path"]),
        "excluded_from_compact_payload": [
            "164.5 MB official archive; frozen identity remains in authority evidence",
            "516,033-byte SAGA paper witness; local evidence only and not redistributed",
            "full multi-megabyte backend dataset; maintained in the edition repository",
            "build trees, caches, rendered QA images, credentials, and bulk provenance dumps",
        ],
        "sha256sums_scope": "every ZIP member except SHA256SUMS itself",
        "zip_identity_location": "local-verification-becker-03.json outside the ZIP",
        "upstream_contact": False,
    }
    write_json(PACKAGE / "release-manifest-becker-03.json", manifest)
    ordered = [
        "D90-BECKER-03-reduksi-varians-id.pdf",
        "D90-BECKER-03-reduksi-varians-id.html",
        "README_BECKER_03.md",
        "LICENSE_BECKER_MIT.txt",
        "LICENSE_TRANSLATION_CC_BY-SA-4.0.md",
        "source/id-ID/D90-BECKER-03-reduksi-varians-id.tex",
        "source/id-ID/becker-03-reduksi-varians-id.tex",
        "source/id-ID/macros-id.tex",
        "source/id-ID/shinybook.cls",
        "source/en/becker-03-variance-reduction-source.tex",
        "authority/BECKER_AUTHORITY_FREEZE.md",
        "qa/BECKER_03_SOURCE_BOUNDARY.json",
        "qa/BECKER_03_MATH_VALIDATION.json",
        "qa/BECKER_03_PDF_BUILD.json",
        "qa/BECKER_03_PDF_VISUAL_QA.json",
        "qa/BECKER_03_HTML_BUILD.json",
        "qa/BECKER_03_HTML_BROWSER_QA.json",
        "qa/BECKER_03_INDEPENDENT_REREVIEW.json",
        "qa/BECKER_03_BACKEND_EXTENSION.json",
        "qa/BECKER_03_BACKEND_VALIDATION.json",
        "release-manifest-becker-03.json",
    ]
    sums = "".join(f"{sha_file(PACKAGE / PurePosixPath(rel))}  {rel}\n" for rel in ordered)
    (PACKAGE / "SHA256SUMS").write_text(sums, encoding="utf-8", newline="\n")
    return ordered + ["SHA256SUMS"]


def text_policy(members: list[str]) -> None:
    forbidden = re.compile(r"(?<![A-Za-z0-9])TTP(?![A-Za-z0-9])|Translation and Transcription Project")
    for rel in members:
        path = PACKAGE / PurePosixPath(rel)
        if path.suffix.lower() in {".md", ".txt", ".tex", ".html", ".json"} or path.name == "SHA256SUMS":
            text = path.read_text(encoding="utf-8")
            if forbidden.search(text):
                raise RuntimeError(f"Forbidden project-label prose in {rel}")
    for rel in (
        "README_BECKER_03.md",
        "LICENSE_TRANSLATION_CC_BY-SA-4.0.md",
        "D90-BECKER-03-reduksi-varians-id.html",
        "source/id-ID/D90-BECKER-03-reduksi-varians-id.tex",
    ):
        if MODEL not in (PACKAGE / PurePosixPath(rel)).read_text(encoding="utf-8"):
            raise RuntimeError(f"Exact model marker absent from {rel}")


def build_zip(path: Path, members: list[str]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
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
                (PACKAGE / PurePosixPath(rel)).read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def verify_zip(members: list[str]) -> list[dict]:
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC test failed")
        infos = archive.infolist()
        if [item.filename for item in infos] != members or len(infos) != len(set(members)):
            raise RuntimeError("ZIP inventory/order/uniqueness mismatch")
        entries = []
        for info in infos:
            if not safe_member(info.filename) or info.date_time != STAMP:
                raise RuntimeError(f"Unsafe or nondeterministic ZIP entry {info.filename}")
            data = archive.read(info.filename)
            if data != (PACKAGE / PurePosixPath(info.filename)).read_bytes():
                raise RuntimeError(f"ZIP entry differs from package tree: {info.filename}")
            entries.append({
                "path": info.filename,
                "bytes": len(data),
                "compressed_bytes": info.compress_size,
                "sha256": sha_bytes(data),
                "timestamp": "2026-08-25T00:00:00",
            })
    sums = (PACKAGE / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    expected = [f"{sha_file(PACKAGE / PurePosixPath(rel))}  {rel}" for rel in members[:-1]]
    if sums != expected:
        raise RuntimeError("SHA256SUMS mismatch")
    return entries


def main() -> None:
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
    entries = verify_zip(members)
    receipt = {
        "schema": "o015-becker-03-local-release-verification-v1",
        "result": "pass",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release_directory": str(HERE),
        "package_directory": str(PACKAGE),
        "zip": {
            "path": str(ZIP_PATH),
            "bytes": ZIP_PATH.stat().st_size,
            "sha256": sha_file(ZIP_PATH),
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
            "primary_saga_paper": True,
            "full_backend_dataset": True,
            "build_trees_and_caches": True,
            "bulk_provenance_dumps": True,
        },
        "model_provenance": MODEL,
    }
    write_json(RECEIPT_PATH, receipt)
    print(json.dumps({
        "result": "pass",
        "zip": str(ZIP_PATH),
        "bytes": ZIP_PATH.stat().st_size,
        "sha256": sha_file(ZIP_PATH),
        "entries": len(entries),
        "receipt": str(RECEIPT_PATH),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
