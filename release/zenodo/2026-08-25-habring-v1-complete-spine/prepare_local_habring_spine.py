#!/usr/bin/env python3
"""Run two byte-identical offline builds and write a sanitized preparation receipt."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import build_habring_spine as build
import freeze_inputs_habring_spine as freeze


HERE = Path(__file__).resolve().parent
RECEIPT_PATH = HERE / "local-preparation-habring-spine.json"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"filename": path.name, "bytes": path.stat().st_size, "sha256": digest(path)}


def additions() -> list[dict[str, object]]:
    return [identity(path) for path in build.addition_paths()]


def bound_draft_state() -> dict[str, object] | None:
    if not build.STATE_PATH.is_file():
        return None
    value = json.loads(build.STATE_PATH.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("schema") != "o015-zenodo-habring-spine-draft-receipt-v1"
        or value.get("status") != "draft"
        or not str(value.get("draft_id", "")).isdigit()
        or value.get("parent_record_id") != build.PARENT_RECORD_ID
        or value.get("parent_record_doi") != build.PARENT_RECORD_DOI
        or value.get("concept_id") != build.CONCEPT_ID
        or value.get("concept_doi") != build.CONCEPT_DOI
        or value.get("version") != build.VERSION
    ):
        raise RuntimeError("local Zenodo state is not the expected bound unpublished draft")
    return {"draft_id": str(value["draft_id"]), "status": value["status"]}


def main() -> None:
    expected_config = freeze.payload(freeze.make_config())
    expected_lock = freeze.payload(freeze.make_lock())
    if not freeze.CONFIG_PATH.is_file() or freeze.CONFIG_PATH.read_bytes() != expected_config:
        raise RuntimeError("frozen config is absent or stale")
    if not freeze.LOCK_PATH.is_file() or freeze.LOCK_PATH.read_bytes() != expected_lock:
        raise RuntimeError("frozen input lock is absent or stale")
    first_manifest = build.build_all()
    first = additions()
    second_manifest = build.build_all()
    second = additions()
    if first_manifest != second_manifest or first != second:
        raise RuntimeError("two local builds were not byte-identical")
    validation = build.validate_local_release()
    with zipfile.ZipFile(HERE / build.COMPLETE_BUNDLE_NAME, "r") as archive:
        uncompressed = sum(item.file_size for item in archive.infolist())
    draft = bound_draft_state()
    if build.READBACK_PATH.is_file():
        raise RuntimeError("offline preparation found a public-readback receipt for this version")
    receipt = {
        "schema": "o015-zenodo-habring-spine-local-preparation-v2",
        "recorded_at": "2026-08-25",
        "status": "prepared locally; existing bound draft may be reconciled, but no network, upload, publication, or readback occurred in this preparation",
        "component_status": "Habring v1 spine complete; larger O015 coursebook partial",
        "parent_record_id": build.PARENT_RECORD_ID,
        "parent_record_doi": build.PARENT_RECORD_DOI,
        "concept_id": build.CONCEPT_ID,
        "concept_doi": build.CONCEPT_DOI,
        "version": build.VERSION,
        "deterministic_local_builds": 2,
        "deterministic_identity_match": True,
        "inherited_file_count": build.EXPECTED_INHERITED_COUNT,
        "addition_file_count": build.EXPECTED_ADDITION_COUNT,
        "release_file_count": build.EXPECTED_RELEASE_COUNT,
        "additions_in_upload_order": [
            identity(build.PDF_PATH),
            identity(HERE / build.COMPLETE_BUNDLE_NAME),
        ],
        "bundle": {
            **validation["bundle"],
            "uncompressed_bytes": uncompressed,
        },
        "source_backend_bundle": validation["source_backend_bundle"],
        "manifest": validation["manifest"],
        "checksums": validation["checksums"],
        "input_lock": identity(freeze.LOCK_PATH),
        "release_config": identity(freeze.CONFIG_PATH),
        "metadata_template": identity(build.TEMPLATE_PATH),
        "release_builder": identity(HERE / "build_habring_spine.py"),
        "input_freezer": identity(HERE / "freeze_inputs_habring_spine.py"),
        "publisher": identity(HERE / "publish_habring_spine.py"),
        "network_operations": 0,
        "credential_reads": 0,
        "git_operations": 0,
        "publication_operations": 0,
        "draft_state_file_exists": draft is not None,
        "bound_draft": draft,
        "public_readback_file_exists": build.READBACK_PATH.is_file(),
        "next_executable_action": "Run publish_habring_spine.py release under standing publication authorization; it must prune only the seven explicitly superseded loose additions from the bound draft, upload the PDF plus comprehensive ZIP, and retain an anonymous 100-file readback receipt.",
    }
    RECEIPT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
