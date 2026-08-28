#!/usr/bin/env python3
"""Build the deterministic, reader-first O015 integrated release payload.

This script is offline and bounded to explicit project-relative inputs.  It
creates the four generated Zenodo additions plus a local verification receipt;
the three readers and two backend exports remain byte-identical source files.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ZIP_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_INTEGRATED_RELEASE_2026.08.28.zip"
RIGHTS_NAME = "RIGHTS_AND_PROVENANCE_INTEGRATED.md"
MANIFEST_NAME = "release-manifest-integrated-zenodo.json"
SUMS_NAME = "SHA256SUMS-integrated"
VERIFY_NAME = "local-verification-integrated.json"
FIXED_ZIP_TIME = (2026, 8, 28, 0, 0, 0)

READERS = [
    ("D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf", "output/pdf/D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf"),
    ("D90-O015-optimisasi-lanjut-analisis-konveks-id.html", "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html"),
    ("D90-O015-optimisasi-lanjut-analisis-konveks-id.epub", "output/epub/D90-O015-optimisasi-lanjut-analisis-konveks-id.epub"),
]
BACKENDS = [
    ("backend-records-2026.08.28-integrated.jsonl", "backend/records.jsonl"),
    ("backend-records-2026.08.28-integrated.csv", "backend/records.csv"),
]
QA_FILES = [
    "qa/2026-08-27-integrated-pdf-build.json",
    "qa/INTEGRATED_BROWSER_QA.json",
    "qa/INTEGRATED_PDF_VALIDATION.json",
    "qa/INTEGRATED_PDF_VISUAL_QA.json",
    "qa/INTEGRATED_READERS_BUILD.json",
    "qa/INTEGRATED_READERS_VALIDATION.json",
    "qa/INTEGRATED_REFLOW_INDEPENDENT.json",
    "qa/INTEGRATED_RIGHTS_RELEASE_QA.json",
    "qa/ORIGINAL_03_BACKEND_BUILD.json",
    "qa/ORIGINAL_03_BACKEND_VALIDATION.json",
    "qa/ORIGINAL_03_COURSE_CLOSURE.json",
    "qa/build_integrated_pdf.py",
    "qa/build_integrated_readers.py",
    "qa/extend_backend_original_03.py",
    "qa/validate_backend_original_03.py",
    "qa/verify_integrated_pdf.py",
    "qa/verify_integrated_readers.py",
    "qa/verify_integrated_reflow_independent.py",
    "qa/verify_integrated_rights_release.py",
    "qa/verify_original_03_course_closure.py",
]
LAB_FILES = [
    f"labs/original-03/{name}"
    for name in (
        "globalisasi-newton.py",
        "globalisasi-newton-results.json",
        "globalisasi-newton-results.csv",
        "globalisasi-newton.svg",
        "transportasi-entropik.py",
        "transportasi-entropik-results.json",
        "transportasi-entropik-results.csv",
        "transportasi-entropik.svg",
        "kapstone-invers-komposit.py",
        "kapstone-invers-komposit-results.json",
        "kapstone-invers-komposit-results.csv",
        "kapstone-invers-komposit.svg",
    )
]
CONTROL_FILES = [
    "README.md",
    "RIGHTS.md",
    "PROVENANCE.md",
    "00_control/SOURCE_AUTHORITY.json",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/ADVERSE_LEDGER.jsonl",
    "00_control/BUILD_AND_QA.md",
    "backend/backend_schema.json",
    "backend/records.jsonl",
    "backend/records.csv",
]

PROFILE = re.compile(rb"(?i)(?:file:/+)?[a-z]:[\\/]+users[\\/]+[^\\/\x00-\x20\"']+[\\/]")
SECRET_PATTERNS = [
    re.compile(rb"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._~+/-]{20,}"),
    re.compile(rb"(?i)(?:access[_ -]?token|api[_ -]?key|github[_ -]?token|zenodo[_ -]?token)\s*[:=]\s*[\"']?[A-Za-z0-9._~+/-]{20,}"),
    re.compile(rb"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})"),
    re.compile(rb"(?i)new[ _-]+zenodo[ _-]+token\.md"),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path_for(relative: str) -> Path:
    candidate = (ROOT / relative).resolve()
    candidate.relative_to(ROOT.resolve())
    if not candidate.is_file():
        raise FileNotFoundError(relative)
    return candidate


def identity(relative: str) -> dict[str, object]:
    data = path_for(relative).read_bytes()
    return {"path": relative, "bytes": len(data), "sha256": sha(data)}


def source_inputs() -> list[str]:
    pdf = json.loads(path_for("qa/2026-08-27-integrated-pdf-build.json").read_text(encoding="utf-8"))
    readers = json.loads(path_for("qa/INTEGRATED_READERS_BUILD.json").read_text(encoding="utf-8"))
    items = [item["path"] for item in pdf["declared_inputs"]]
    items.extend(item["path"] for item in readers["inputs"])
    return sorted(dict.fromkeys(items))


def scan(name: str, data: bytes) -> list[str]:
    findings: list[str] = []
    if PROFILE.search(data):
        findings.append(f"profile_locator:{name}")
    for index, pattern in enumerate(SECRET_PATTERNS, start=1):
        if pattern.search(data):
            findings.append(f"credential_pattern_{index}:{name}")
    return findings


def rights_note() -> bytes:
    rights = path_for("RIGHTS.md").read_text(encoding="utf-8").rstrip()
    provenance = path_for("PROVENANCE.md").read_text(encoding="utf-8").rstrip()
    text = (
        "# Rights and provenance — integrated O015/D90 edition\n\n"
        "This release has no blanket license. The following two controlling "
        "records are reproduced verbatim from the release candidate.\n\n"
        f"{rights}\n\n---\n\n{provenance}\n"
    )
    return text.encode("utf-8")


def bundle_bytes(inputs: list[str], note: bytes) -> tuple[bytes, list[dict[str, object]]]:
    members: list[tuple[str, bytes]] = []
    for relative in inputs:
        members.append((relative.replace("\\", "/"), path_for(relative).read_bytes()))
    members.append((RIGHTS_NAME, note))
    members.sort(key=lambda item: item[0])
    inventory = [
        {"path": name, "bytes": len(data), "sha256": sha(data)}
        for name, data in members
    ]
    manifest = json.dumps(
        {
            "schema": "o015-integrated-compact-bundle-v1",
            "date": "2026-08-28",
            "entry_count_excluding_manifest": len(inventory),
            "entries": inventory,
            "rights": "per component; no blanket license",
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    members.append(("BUNDLE_MANIFEST.json", manifest))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members, key=lambda item: item[0]):
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return out.getvalue(), inventory


def main() -> int:
    rights = rights_note()
    inputs = sorted(dict.fromkeys(source_inputs() + LAB_FILES + QA_FILES + CONTROL_FILES))
    first, bundle_inventory = bundle_bytes(inputs, rights)
    second, _ = bundle_bytes(inputs, rights)
    if first != second:
        raise RuntimeError("deterministic ZIP comparison failed")

    findings: list[str] = []
    for relative in inputs:
        findings.extend(scan(relative, path_for(relative).read_bytes()))
    findings.extend(scan(RIGHTS_NAME, rights))
    findings.extend(scan(ZIP_NAME, first))
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC verification failed")
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("duplicate ZIP member")
        for name in names:
            findings.extend(scan(f"{ZIP_NAME}!{name}", archive.read(name)))
    if findings:
        raise RuntimeError("privacy/credential scan failed without writing outputs")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / RIGHTS_NAME).write_bytes(rights)
    (OUT / ZIP_NAME).write_bytes(first)

    additions: list[dict[str, object]] = []
    roles = [
        "default_preview_and_fixed_layout_reader",
        "primary_reflow_reader",
        "portable_reflow_reader",
    ]
    for order, ((filename, relative), role) in enumerate(zip(READERS, roles), start=1):
        item = identity(relative)
        additions.append({"order": order, "filename": filename, "source_path": relative, "role": role, "bytes": item["bytes"], "sha256": item["sha256"]})
    additions.append({"order": 4, "filename": ZIP_NAME, "source_path": f"release/final/2026-08-28/{ZIP_NAME}", "role": "compact_source_labs_backend_qa_bundle", "bytes": len(first), "sha256": sha(first)})
    for order, (filename, relative) in enumerate(BACKENDS, start=5):
        item = identity(relative)
        additions.append({"order": order, "filename": filename, "source_path": relative, "role": "current_machine_readable_backend" if order == 5 else "current_tabular_backend", "bytes": item["bytes"], "sha256": item["sha256"]})
    additions.append({"order": 7, "filename": RIGHTS_NAME, "source_path": f"release/final/2026-08-28/{RIGHTS_NAME}", "role": "exact_component_rights_source_change_model_nonendorsement_note", "bytes": len(rights), "sha256": sha(rights)})

    manifest = {
        "schema": "o015-integrated-zenodo-release-manifest-v1",
        "date": "2026-08-28",
        "parent_record_id": "22104724",
        "concept_id": "22059741",
        "reader_first": True,
        "default_preview": READERS[0][0],
        "inherited_policy": {
            "parent_file_count": 99,
            "omit_from_new_version_only": [
                f"release-manifest-mit-l{number}.json"
                for number in ("03", "04-l05", "06", "07", "08", "09", "10", "11")
            ],
            "inherited_unchanged_count": 91,
            "addition_count": 9,
            "expected_new_version_file_count": 100,
            "historical_public_bytes_remain_available": True,
        },
        "additions_with_frozen_identity": additions,
        "generated_additions": [MANIFEST_NAME, SUMS_NAME],
        "bundle": {
            "entry_count": len(bundle_inventory) + 1,
            "payload_entry_count": len(bundle_inventory),
            "deterministic_two_builds_identical": True,
        },
        "rights": "mixed; rights apply per file and source relation; no blanket license",
    }
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    (OUT / MANIFEST_NAME).write_bytes(manifest_bytes)

    sums_items = [(item["filename"], item["sha256"]) for item in additions]
    sums_items.append((MANIFEST_NAME, sha(manifest_bytes)))
    sums_bytes = "".join(f"{digest}  {name}\n" for name, digest in sums_items).encode("utf-8")
    (OUT / SUMS_NAME).write_bytes(sums_bytes)

    verification = {
        "schema": "o015-integrated-local-release-verification-v1",
        "date": "2026-08-28",
        "result": "pass",
        "network_used": False,
        "git_used": False,
        "credential_accessed": False,
        "browser_used": False,
        "deterministic_zip_builds": 2,
        "deterministic_zip_byte_identical": True,
        "zip_test": "pass",
        "zip_entries": len(bundle_inventory) + 1,
        "privacy_or_credential_findings": [],
        "frozen_artifact_count_before_final_generated_manifest_and_checksums": 7,
        "planned_zenodo_addition_count": 9,
        "frozen_artifact_bytes": sum(int(item["bytes"]) for item in additions),
        "frozen_artifacts": additions,
        "publisher_generated_additions": [MANIFEST_NAME, SUMS_NAME],
        "publisher_rebuilds_generated_manifest_and_checksums_after_release_input_freeze": True,
    }
    verify_bytes = json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    (OUT / VERIFY_NAME).write_bytes(verify_bytes)
    print(json.dumps({"result": "pass", "zip_bytes": len(first), "zip_sha256": sha(first), "zip_entries": len(bundle_inventory) + 1, "addition_count": 9, "frozen_artifact_bytes": verification["frozen_artifact_bytes"], "verification": VERIFY_NAME}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
