#!/usr/bin/env python3
"""Build and verify the compact, reader-first Original-01 release.

The package is deliberately a bounded preservation payload.  It carries the
three reader surfaces, resumable source, lab, compact backend schema, and all
deterministic gate receipts, while the full backend and authority witnesses
remain in the edition repository.  ZIP member order, timestamps, and bytes are
fixed so two clean builds can be compared byte-for-byte.
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


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PACKAGE = HERE / "package"
ZIP_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_ORIGINAL_01_2026.08.26.zip"
ZIP_PATH = HERE / ZIP_NAME
RECEIPT_PATH = HERE / "local-verification-original-01.json"
STAMP = (2026, 8, 26, 0, 0, 0)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
MAX_BYTES = 500_000_000


# The first three members are the human-facing readers.  Keep this order
# explicit: it is part of the release contract and is checked in the receipt.
MATERIAL = [
    ("D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf", "output/pdf/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf", "primary PDF reader", "application/pdf"),
    ("D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html", "output/html/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html", "responsive semantic HTML reader", "text/html"),
    ("D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub", "output/epub/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub", "reflow EPUB reader", "application/epub+zip"),
    ("README_ORIGINAL_01.md", None, "reader-first scope and continuation guide", "text/markdown"),
    ("RIGHTS_AND_PROVENANCE_ORIGINAL_01.md", None, "component rights and provenance", "text/markdown"),
    ("LICENSE_ORIGINAL_CC_BY-SA-4.0.md", None, "license note for new material", "text/markdown"),
    ("LICENSE_HABRING_SCAFFOLD_CC_BY-4.0.md", None, "license note for Habring scaffold", "text/markdown"),
    ("source/id-ID/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex", "source/id-ID/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex", "standalone Indonesian reader wrapper", "application/x-tex"),
    ("source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex", "source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex", "independent Indonesian substantive chapter", "application/x-tex"),
    ("source/id-ID/macros-id.tex", "source/id-ID/macros-id.tex", "localized macro scaffold", "application/x-tex"),
    ("source/id-ID/shinybook.cls", "source/id-ID/shinybook.cls", "Habring document-class scaffold", "application/x-tex"),
    ("labs/original-01/stochastic-composite-lab.py", "labs/original-01/stochastic-composite-lab.py", "open computation lab", "text/x-python"),
    ("labs/original-01/results.json", "labs/original-01/results.json", "machine-readable lab results", "application/json"),
    ("labs/original-01/results.csv", "labs/original-01/results.csv", "tabular lab results", "text/csv"),
    ("labs/original-01/objective-gap.svg", "labs/original-01/objective-gap.svg", "lab chart with text alternative in readers", "image/svg+xml"),
    ("backend/backend_schema.json", "backend/backend_schema.json", "stable-ID backend schema", "application/json"),
    ("qa/ORIGINAL_01_MATH_VALIDATION.json", "qa/ORIGINAL_01_MATH_VALIDATION.json", "open mathematics validation", "application/json"),
    ("qa/ORIGINAL_01_PDF_BUILD.json", "qa/ORIGINAL_01_PDF_BUILD.json", "deterministic PDF build receipt", "application/json"),
    ("qa/ORIGINAL_01_PDF_VISUAL_QA.json", "qa/ORIGINAL_01_PDF_VISUAL_QA.json", "all-page PDF visual QA", "application/json"),
    ("qa/ORIGINAL_01_HTML_BUILD.json", "qa/ORIGINAL_01_HTML_BUILD.json", "deterministic HTML build receipt", "application/json"),
    ("qa/ORIGINAL_01_HTML_BROWSER_QA.json", "qa/ORIGINAL_01_HTML_BROWSER_QA.json", "desktop/tablet/phone browser QA", "application/json"),
    ("qa/ORIGINAL_01_EPUB_BUILD.json", "qa/ORIGINAL_01_EPUB_BUILD.json", "deterministic EPUB build receipt", "application/json"),
    ("qa/ORIGINAL_01_EPUB_CONFORMANCE.json", "qa/ORIGINAL_01_EPUB_CONFORMANCE.json", "EPUB and EPUBCheck conformance", "application/json"),
    ("qa/ORIGINAL_01_BACKEND_VALIDATION.json", "qa/ORIGINAL_01_BACKEND_VALIDATION.json", "stable-ID backend validation", "application/json"),
    ("qa/ORIGINAL_01_RIGHTS_NONOVERLAP.json", "qa/ORIGINAL_01_RIGHTS_NONOVERLAP.json", "rights and O018 non-overlap gate", "application/json"),
    ("qa/ORIGINAL_01_INDEPENDENT_REREVIEW.json", "qa/ORIGINAL_01_INDEPENDENT_REREVIEW.json", "independent final rereview", "application/json"),
    ("qa/build_original_01_pdf.py", "qa/build_original_01_pdf.py", "PDF builder", "text/x-python"),
    ("qa/build_original_01_reflow.py", "qa/build_original_01_reflow.py", "HTML/EPUB builder", "text/x-python"),
    ("qa/validate_original_01_math.py", "qa/validate_original_01_math.py", "mathematics validator", "text/x-python"),
    ("qa/verify_original_01_pdf_visual.py", "qa/verify_original_01_pdf_visual.py", "PDF visual validator", "text/x-python"),
    ("qa/verify_original_01_epub.py", "qa/verify_original_01_epub.py", "EPUB validator", "text/x-python"),
    ("qa/extend_backend_original_01.py", "qa/extend_backend_original_01.py", "backend extension generator", "text/x-python"),
    ("qa/validate_backend_original_01.py", "qa/validate_backend_original_01.py", "backend validator", "text/x-python"),
    ("qa/validate_original_01_rights_nonoverlap.py", "qa/validate_original_01_rights_nonoverlap.py", "rights/non-overlap validator", "text/x-python"),
]
MANIFEST_NAME = "release-manifest-original-01.json"
SUMS_NAME = "SHA256SUMS"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def identity(path: Path) -> dict:
    return {"bytes": path.stat().st_size, "sha256": sha_file(path)}


def assert_exists(path: Path, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label}: missing file {path}")


def assert_report_pass(path: Path, label: str) -> dict:
    report = load_json(path)
    result = report.get("result", report.get("status"))
    # The math report predates the explicit result field; its empty failure
    # list is the deterministic pass signal.
    if result not in {None, "pass", "PASS"}:
        raise RuntimeError(f"{label}: non-passing result {result!r}")
    if report.get("failures") not in (None, []):
        raise RuntimeError(f"{label}: failures are present")
    return report


def validate_inputs() -> dict[str, dict]:
    required_reports = {
        "math": "qa/ORIGINAL_01_MATH_VALIDATION.json",
        "pdf_build": "qa/ORIGINAL_01_PDF_BUILD.json",
        "pdf_visual": "qa/ORIGINAL_01_PDF_VISUAL_QA.json",
        "html_build": "qa/ORIGINAL_01_HTML_BUILD.json",
        "browser": "qa/ORIGINAL_01_HTML_BROWSER_QA.json",
        "epub_build": "qa/ORIGINAL_01_EPUB_BUILD.json",
        "epub_conformance": "qa/ORIGINAL_01_EPUB_CONFORMANCE.json",
        "backend": "qa/ORIGINAL_01_BACKEND_VALIDATION.json",
        "rights": "qa/ORIGINAL_01_RIGHTS_NONOVERLAP.json",
        "rereview": "qa/ORIGINAL_01_INDEPENDENT_REREVIEW.json",
    }
    reports = {
        key: assert_report_pass(PROJECT / rel, key) for key, rel in required_reports.items()
    }
    if reports["rereview"].get("result") != "pass":
        raise RuntimeError("Independent final rereview is not a pass")
    counts = reports["rereview"].get("finding_counts", {}).get("remaining_after_corrections", {})
    if counts != {"P1": 0, "P2": 0, "P3": 0}:
        raise RuntimeError(f"Independent rereview has open findings: {counts}")
    if reports["browser"].get("result") != "pass":
        raise RuntimeError("Browser QA is not a pass")
    if reports["rights"].get("result") != "pass":
        raise RuntimeError("Rights/non-overlap gate is not a pass")
    if reports["epub_conformance"].get("epubcheck", {}).get("counts"):
        counts = reports["epub_conformance"]["epubcheck"]["counts"]
        if any(counts.get(key, 0) for key in ("fatal", "error", "warning", "usage")):
            raise RuntimeError(f"EPUBCheck reported nonzero counts: {counts}")
    if reports["backend"].get("admission", {}).get("final_records") != 3943:
        raise RuntimeError("Backend does not contain the admitted 3,943-record closure")
    for dest, source, _role, _media in MATERIAL:
        if source is not None:
            assert_exists(PROJECT / source, dest)
    for rel in ("backend/backend_schema.json", "source/id-ID/macros-id.tex", "source/id-ID/shinybook.cls"):
        assert_exists(PROJECT / rel, rel)
    return reports


def package_path(rel: str) -> Path:
    return PACKAGE / PurePosixPath(rel)


def member_record(rel: str, role: str, media: str) -> dict:
    path = package_path(rel)
    return {
        "path": rel,
        "role": role,
        "media_type": media,
        "bytes": path.stat().st_size,
        "sha256": sha_file(path),
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def safe_member(rel: str) -> bool:
    path = PurePosixPath(rel)
    return bool(rel) and "\\" not in rel and not path.is_absolute() and ".." not in path.parts and not rel.endswith("/")


def prepare_package(reports: dict[str, dict]) -> list[str]:
    # The authored notes live in package/ so they can be reviewed beside the
    # generated tree.  Read them before recreating that exact task-local dir.
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

    material = [member_record(dest, role, media) for dest, _source, role, media in MATERIAL]
    reports_summary = {
        key: {
            "path": f"qa/ORIGINAL_01_{key.upper()}.json" if key not in {"pdf_build", "pdf_visual", "html_build", "epub_build", "epub_conformance"} else None,
            "result": "pass",
        }
        for key in reports
    }
    reports_summary.update({
        "math": {"path": "qa/ORIGINAL_01_MATH_VALIDATION.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_MATH_VALIDATION.json")},
        "pdf_build": {"path": "qa/ORIGINAL_01_PDF_BUILD.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_PDF_BUILD.json")},
        "pdf_visual": {"path": "qa/ORIGINAL_01_PDF_VISUAL_QA.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_PDF_VISUAL_QA.json")},
        "html_build": {"path": "qa/ORIGINAL_01_HTML_BUILD.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_HTML_BUILD.json")},
        "browser": {"path": "qa/ORIGINAL_01_HTML_BROWSER_QA.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_HTML_BROWSER_QA.json")},
        "epub_build": {"path": "qa/ORIGINAL_01_EPUB_BUILD.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_EPUB_BUILD.json")},
        "epub_conformance": {"path": "qa/ORIGINAL_01_EPUB_CONFORMANCE.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_EPUB_CONFORMANCE.json")},
        "backend": {"path": "qa/ORIGINAL_01_BACKEND_VALIDATION.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_BACKEND_VALIDATION.json")},
        "rights": {"path": "qa/ORIGINAL_01_RIGHTS_NONOVERLAP.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_RIGHTS_NONOVERLAP.json")},
        "rereview": {"path": "qa/ORIGINAL_01_INDEPENDENT_REREVIEW.json", "sha256": sha_file(PROJECT / "qa/ORIGINAL_01_INDEPENDENT_REREVIEW.json")},
    })
    manifest = {
        "schema": "o015-original-01-compact-release-v1",
        "title": "Optimisasi Lanjut dan Analisis Konveks — Tranche Asli 1: Metode Stokastik Komposit, Cermin, dan Minibatch — Edisi Bahasa Indonesia",
        "release_date": "2026-08-26",
        "status": {
            "tranche": "complete at the exact admitted Original-01 scope",
            "larger_course_edition": "partial",
            "next_cursor": "variational inequalities, maximal monotone operators, resolvents, and splitting",
        },
        "primary_reader": "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf",
        "reader_order": [
            "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf",
            "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html",
            "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub",
        ],
        "scope": {
            "unit_id": "d90.orig.v1.tr01.unit",
            "segments": 8,
            "equations": 40,
            "exercises": 6,
            "hints": 6,
            "complete_solutions": 6,
            "lab": "one deterministic open-computation stochastic-composite lab",
            "stable_id_namespace": reports["backend"].get("admission", {}).get("namespace", "d90.orig.v1.tr01.*"),
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
            "separate_component_licenses": True,
            "no_blanket_license_claim": True,
        },
        "provenance": {
            "mathematical_sources": "Habring, Royer, Becker, and published stochastic-optimization references are verification witnesses only; no third-party prose, layout, figure, exercise, solution, or code is redistributed",
            "human_credits_retained": True,
            "non_endorsement": "Independent edition; no named author, institution, or source party is represented as endorsing it.",
            "model": MODEL,
        },
        "qa": reports_summary,
        "files": material,
        "backend_policy": {
            "full_dataset_packaged": False,
            "reason": "The full backend remains in the repository; this compact package carries its schema and a passing validation receipt with protected baseline and exact ID-set/order hashes.",
        },
        "excluded": [
            "full backend records.jsonl and records.csv",
            "official Habring source tar and legal-code witness",
            "mathematical witness PDFs",
            "build trees, caches, rendered QA images, credentials, and bulk provenance dumps",
        ],
        "sha256sums_scope": "every ZIP member except SHA256SUMS itself",
        "upstream_contact": False,
    }
    write_json(package_path(MANIFEST_NAME), manifest)
    ordered = [item[0] for item in MATERIAL] + [MANIFEST_NAME]
    sums = "".join(f"{sha_file(package_path(rel))}  {rel}\n" for rel in ordered)
    package_path(SUMS_NAME).write_text(sums, encoding="utf-8", newline="\n")
    members = ordered + [SUMS_NAME]
    if len(members) != 36:
        raise RuntimeError(f"Expected 36 package members, got {len(members)}")
    return members


def text_policy(members: list[str]) -> None:
    forbidden = re.compile(r"(?<![A-Za-z0-9])TTP(?![A-Za-z0-9])|Translation and Transcription Project")
    for rel in members:
        path = package_path(rel)
        if path.suffix.lower() in {".md", ".txt", ".tex", ".html", ".json"} or path.name == SUMS_NAME:
            text = path.read_text(encoding="utf-8")
            if forbidden.search(text):
                raise RuntimeError(f"Forbidden project-label prose in {rel}")
    for rel in ("README_ORIGINAL_01.md", "RIGHTS_AND_PROVENANCE_ORIGINAL_01.md", "LICENSE_ORIGINAL_CC_BY-SA-4.0.md", "LICENSE_HABRING_SCAFFOLD_CC_BY-4.0.md"):
        if MODEL not in package_path(rel).read_text(encoding="utf-8"):
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
            archive.writestr(info, package_path(rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


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
            if data != package_path(info.filename).read_bytes():
                raise RuntimeError(f"ZIP entry differs from package tree: {info.filename}")
            entries.append({
                "path": info.filename,
                "bytes": len(data),
                "compressed_bytes": info.compress_size,
                "sha256": sha_bytes(data),
                "timestamp": "2026-08-26T00:00:00",
            })
    sums = package_path(SUMS_NAME).read_text(encoding="utf-8").splitlines()
    expected = [f"{sha_file(package_path(rel))}  {rel}" for rel in members[:-1]]
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
    if ZIP_PATH.stat().st_size > MAX_BYTES:
        raise RuntimeError("Compact release exceeds the 500,000,000-byte payload cap")
    entries = verify_zip(members)
    receipt = {
        "schema": "o015-original-01-local-release-verification-v1",
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
            "fixed_timestamp": "2026-08-26T00:00:00",
            "byte_identical_two_builds": True,
            "compression": "ZIP_DEFLATED level 9",
            "contains_itself": False,
        },
        "verification": {
            "crc_test": "pass",
            "entry_order_matches_explicit_36_member_reader_first_inventory": True,
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
            "payload_cap_bytes": MAX_BYTES,
        },
        "omissions": {
            "full_backend_dataset": True,
            "official_habring_source_tar_and_legalcode": True,
            "mathematical_witness_pdfs": True,
            "build_trees_caches_rendered_images_credentials": True,
        },
        "model_provenance": MODEL,
    }
    write_json(RECEIPT_PATH, receipt)
    print(json.dumps({"result": "pass", "zip": str(ZIP_PATH), "bytes": ZIP_PATH.stat().st_size, "sha256": sha_file(ZIP_PATH), "entries": len(entries), "receipt": str(RECEIPT_PATH)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
