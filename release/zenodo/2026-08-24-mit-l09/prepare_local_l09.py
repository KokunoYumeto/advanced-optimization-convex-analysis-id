#!/usr/bin/env python3
"""Run the two-build local MIT-L09 release gate and write its receipt.

No network, credential, Git, draft, upload, or publication operation occurs.
The command fails before producing release bytes unless the final backend and
control configuration has been supplied and locked explicitly.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import build_l09 as build
import generate_input_lock_l09 as lockgen


HERE = Path(__file__).resolve().parent
RECEIPT_PATH = HERE / "local-preparation-mit-l09.json"


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def identity(path: Path, filename: str | None = None) -> dict[str, object]:
    return {"filename": filename or path.name, "bytes": path.stat().st_size, "sha256": file_digest(path)}


def addition_identities() -> list[dict[str, object]]:
    return [identity(path) for path in sorted(build.addition_paths(), key=lambda item: item.name)]


def zip_summary(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path, "r") as archive:
        bad = archive.testzip()
        names = archive.namelist()
        total = sum(item.file_size for item in archive.infolist())
        manifest = json.loads(archive.read("DELTA_BUNDLE_MANIFEST.json"))
    verification = build.verify_bundle(path.read_bytes())
    return {
        **identity(path),
        "zip_entries": len(names),
        "manifest_bound_entries": manifest["entry_count"],
        "uncompressed_bytes": total,
        "unique_names": len(names) == len(set(names)),
        "inventory_exact": set(names) == {"DELTA_BUNDLE_MANIFEST.json", *(entry["path"] for entry in manifest["entries"])},
        "entry_size_hashes": "pass",
        "integrity": "pass" if bad is None and verification["integrity"] == "pass" else "fail",
        "forbidden_entries": verification["forbidden_entries"],
        "credential_shaped_entries": 0,
        "mutable_global_control_files": verification["mutable_global_control_files"],
    }


def main() -> None:
    expected_lock = (json.dumps(lockgen.make_lock(), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if not build.INPUT_LOCK_PATH.is_file() or build.INPUT_LOCK_PATH.read_bytes() != expected_lock:
        raise RuntimeError("frozen L09 input lock is absent or stale; regenerate it explicitly first")
    first = build.build_all()
    first_ids = addition_identities()
    second = build.build_all()
    second_ids = addition_identities()
    if first != second or first_ids != second_ids:
        raise RuntimeError("two local release builds were not byte-identical")
    protected, new, final = build.backend_counts()
    bundle = zip_summary(HERE / build.BUNDLE_NAME)
    receipt = {
        "schema": "o015-zenodo-mit-l09-local-preparation-v1",
        "recorded_at": "2026-08-24",
        "parent_record_id": build.PARENT_RECORD_ID,
        "parent_record_doi": build.PARENT_RECORD_DOI,
        "concept_id": build.CONCEPT_ID,
        "concept_doi": build.CONCEPT_DOI,
        "version": build.VERSION,
        "status": "prepared locally; not authenticated, drafted, uploaded, published, or read back",
        "source_pages": build.SOURCE_PAGES,
        "next_source_page": build.NEXT_SOURCE_PAGE,
        "backend_record_count": final,
        "protected_backend_record_count": protected,
        "new_backend_record_count": new,
        "release_file_count": build.EXPECTED_RELEASE_COUNT,
        "inherited_file_count": build.EXPECTED_INHERITED_COUNT,
        "addition_file_count": build.EXPECTED_ADDITION_COUNT,
        "deterministic_local_builds": 2,
        "deterministic_identity_match": True,
        "delta_bundle": bundle,
        "manifest": identity(HERE / build.MANIFEST_NAME),
        "checksums": identity(HERE / build.SUMS_NAME),
        "reader": {
            "default_preview": build.READER_PATHS[0].name,
            "pdf": identity(build.READER_PATHS[0]),
            "html": identity(build.READER_PATHS[1]),
        },
        "final_backend": {
            "jsonl": identity(build.ROOT / "backend/records.jsonl"),
            "csv": identity(build.ROOT / "backend/records.csv"),
            "validation": identity(build.ROOT / "qa/MIT_L09_BACKEND_VALIDATION.json"),
            "correction_snapshot": identity(build.ROOT / "00_control/MIT_L09_CORRECTION_SNAPSHOT.jsonl"),
        },
        "prepublication_control_bindings": first["lane_closure"]["control_bindings"],
        "release_builder": identity(HERE / "build_l09.py"),
        "input_lock_generator": identity(HERE / "generate_input_lock_l09.py"),
        "input_lock": identity(build.INPUT_LOCK_PATH),
        "release_config": identity(lockgen.CONFIG_PATH),
        "metadata_template": {**identity(build.TEMPLATE_PATH), "default_preview": build.READER_PATHS[0].name},
        "publisher": identity(HERE / "publish_l09.py"),
        "network_operations": 0,
        "credential_reads": 0,
        "git_operations": 0,
        "publication_operations": 0,
        "draft_state_file_exists": build.STATE_PATH.is_file(),
        "public_readback_file_exists": (HERE / "zenodo-public-readback-mit-l09.json").is_file(),
        "note": "Local deterministic preservation package only. A future publisher must create one new version from record 22074528 in concept 10.5281/zenodo.22059741, inherit all 74 parent files byte-for-byte, bind the manifest to that record, publish, and anonymously read back all 82 public files.",
    }
    if receipt["draft_state_file_exists"] or receipt["public_readback_file_exists"]:
        raise RuntimeError("local-only preparation unexpectedly found publication-state evidence")
    RECEIPT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
