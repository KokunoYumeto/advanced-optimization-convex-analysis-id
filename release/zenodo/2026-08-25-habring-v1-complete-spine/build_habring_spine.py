#!/usr/bin/env python3
"""Build the deterministic, additive Habring-v1 Zenodo checkpoint locally."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import freeze_inputs_habring_spine as freeze


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS_READBACK = HERE.parent / "2026-08-24-mit-l11" / "zenodo-public-readback-mit-l11.json"
TEMPLATE_PATH = HERE / "zenodo-record-habring-spine.json"
CONFIG_PATH = HERE / "release-config-habring-spine.json"
INPUT_LOCK_PATH = HERE / "release-input-lock-habring-spine.json"
STATE_PATH = HERE / "zenodo-draft-habring-spine.json"
READBACK_PATH = HERE / "zenodo-public-readback-habring-spine.json"

PARENT_RECORD_ID = "22086656"
PARENT_RECORD_DOI = "10.5281/zenodo.22086656"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.25-habring-v1-complete-spine"
MODEL_ID = "OpenAI Codex gpt-5.6-sol, Ultra"
FORBIDDEN_ORG_EXPANSION = "Translation and Transcription Project"
STATUS = "partial"
FIXED_ZIP_TIME = (2026, 8, 25, 0, 0, 0)

BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.25_HABRING_V1.zip"
COMPLETE_BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_COMPLETE_RELEASE_2026.08.25_HABRING_V1.zip"
MANIFEST_NAME = "release-manifest-habring-spine.json"
SUMS_NAME = "SHA256SUMS-habring-spine"
EXPECTED_INHERITED_COUNT = 98
EXPECTED_ADDITION_COUNT = 2
EXPECTED_RELEASE_COUNT = 100
PUBLIC_ADDITIONS_IN_ORDER = [
    "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf",
    COMPLETE_BUNDLE_NAME,
]
SUPERSEDED_ADDITION_NAMES = {
    "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html",
    "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub",
    BUNDLE_NAME,
    "LICENSE_HABRING_CC_BY_4.0.md",
    "README_HABRING_SPINE.md",
    MANIFEST_NAME,
    SUMS_NAME,
}

PDF_PATH = ROOT / "output/pdf/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf"
HTML_PATH = ROOT / "output/html/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html"
EPUB_PATH = ROOT / "output/epub/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub"
LICENSE_PATH = HERE / "LICENSE_HABRING_CC_BY_4.0.md"
README_PATH = HERE / "README_HABRING_SPINE.md"

BUNDLE_ROOT_PATHS = [relative for relative in freeze.MATERIAL_PATHS if not relative.startswith("output/")]
BUNDLE_LOCAL_PATHS = [
    (INPUT_LOCK_PATH, "release/release-input-lock-habring-spine.json"),
    (LICENSE_PATH, "release/LICENSE_HABRING_CC_BY_4.0.md"),
    (README_PATH, "release/README_HABRING_SPINE.md"),
]

COMPONENT_RIGHTS = {
    "new_habring_v1_spine_and_adaptation": "CC BY 4.0",
    "inherited_mit_components": "CC BY-NC-SA 4.0",
    "inherited_griffin_penn_components": "CC BY-NC-SA 3.0 United States",
    "inherited_royer_source_freeze": "CC BY-NC 4.0",
    "project_build_qa_backend_and_boundary_evidence": "component-specific; no blanket reuse grant asserted",
}


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def identity(path: Path, filename: str | None = None) -> dict[str, object]:
    return {"filename": filename or path.name, "bytes": path.stat().st_size, "sha256": file_digest(path)}


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", dir=HERE, delete=False) as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
        staged = Path(handle.name)
    try:
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def config() -> dict:
    expected = freeze.make_config()
    if not CONFIG_PATH.is_file() or CONFIG_PATH.read_bytes() != freeze.payload(expected):
        raise RuntimeError("final release config is absent or stale; rerun the input freezer")
    value = read_json(CONFIG_PATH)
    if (
        value.get("schema") != "o015-habring-spine-release-config-v1"
        or value.get("parent_record_id") != PARENT_RECORD_ID
        or value.get("parent_record_doi") != PARENT_RECORD_DOI
        or value.get("concept_id") != CONCEPT_ID
        or value.get("concept_doi") != CONCEPT_DOI
        or value.get("expected_inherited_file_count") != EXPECTED_INHERITED_COUNT
        or value.get("expected_addition_file_count") != EXPECTED_ADDITION_COUNT
        or value.get("expected_release_file_count") != EXPECTED_RELEASE_COUNT
        or value.get("public_additions_in_order") != PUBLIC_ADDITIONS_IN_ORDER
        or value.get("status") != STATUS
    ):
        raise RuntimeError("release config lineage/count/status gate failed")
    return value


def input_lock() -> dict:
    cfg = config()
    expected = freeze.make_lock(cfg)
    if not INPUT_LOCK_PATH.is_file() or INPUT_LOCK_PATH.read_bytes() != freeze.payload(expected):
        raise RuntimeError("release input lock is absent or stale; rerun the input freezer")
    return expected


def inherited_inventory() -> dict[str, dict[str, object]]:
    data = read_json(PREVIOUS_READBACK)
    if (
        str(data.get("record_id")) != PARENT_RECORD_ID
        or data.get("record_doi") != PARENT_RECORD_DOI
        or str(data.get("concept_id")) != CONCEPT_ID
        or data.get("concept_doi") != CONCEPT_DOI
        or data.get("status") != "published"
        or data.get("result") != "pass"
        or data.get("inherited_identity") != "pass"
    ):
        raise RuntimeError("frozen L11 readback does not prove the required parent")
    items = data.get("files", [])
    result = {
        item["filename"]: {"filename": item["filename"], "bytes": item["bytes"], "sha256": item["sha256"]}
        for item in items
    }
    if (
        len(items) != EXPECTED_INHERITED_COUNT
        or len(result) != EXPECTED_INHERITED_COUNT
        or data.get("file_count") != EXPECTED_INHERITED_COUNT
        or any(item.get("public_byte_identity") != "pass" for item in items)
    ):
        raise RuntimeError("parent readback does not prove exactly 98 unique public files")
    return result


def validate_template() -> dict:
    template = read_json(TEMPLATE_PATH)
    metadata = template.get("metadata", {})
    if template.get("files", {}).get("default_preview") != PDF_PATH.name:
        raise RuntimeError("metadata must make the complete Habring PDF the default preview")
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    ttp = [item for item in metadata.get("contributors", []) if item.get("person_or_org", {}).get("name") == "TTP"]
    if (
        serialized.count("TTP") != 1
        or len(ttp) != 1
        or ttp[0].get("person_or_org", {}).get("type") != "organizational"
        or "TTP" in title
        or "TTP" in description
        or FORBIDDEN_ORG_EXPANSION.casefold() in serialized.casefold()
        or metadata.get("version") != VERSION
        or serialized.count(MODEL_ID) != 1
    ):
        raise RuntimeError("metadata organization/title/model provenance gate failed")
    lowered = description.casefold()
    for required in (
        "prakata dan bab 1-9",
        "parsial",
        "98 berkas induk",
        "tepat delapan berkas",
        "cc by 4.0",
        "3.096",
        "enam puluh lima koreksi",
        "becker",
        "pdf belum bertag",
    ):
        if required not in lowered:
            raise RuntimeError(f"metadata description lacks {required!r}")
    return metadata


def validate_docs() -> None:
    combined = LICENSE_PATH.read_text(encoding="utf-8") + "\n" + README_PATH.read_text(encoding="utf-8")
    if "TTP" in combined or FORBIDDEN_ORG_EXPANSION.casefold() in combined.casefold():
        raise RuntimeError("release documents must not add the organization label or expansion")
    lowered = combined.casefold()
    for required in (
        "cc by 4.0",
        "prakata",
        "bab 1–9",
        "139 halaman",
        "3.096",
        "o015-hab-adv-0097",
        "o015-hab-adv-0161",
        "parsial",
        "becker",
        "tidak menyiratkan",
    ):
        if required not in lowered:
            raise RuntimeError(f"release documents lack {required!r}")


def zip_entry(name: str, data: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info, data


def bundle_source_entries() -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []
    for relative in BUNDLE_ROOT_PATHS:
        entries.append((relative, (ROOT / relative).read_bytes()))
    for path, archive_name in BUNDLE_LOCAL_PATHS:
        entries.append((archive_name, path.read_bytes()))
    names = [name for name, _ in entries]
    if len(names) != len(set(names)) or any(".." in Path(name).parts or Path(name).is_absolute() for name in names):
        raise RuntimeError("bundle contains duplicate or unsafe names")
    forbidden = [name for name in names if re.search(r"(?i)(token|credential|\.git(?:/|$)|cache|tmp|render)", name)]
    if forbidden:
        raise RuntimeError(f"bundle contains forbidden paths: {forbidden}")
    return sorted(entries, key=lambda item: item[0])


def make_bundle_bytes() -> bytes:
    source_entries = bundle_source_entries()
    manifest = {
        "schema": "o015-habring-spine-source-backend-bundle-v1",
        "authority": {
            "work": "Andreas Habring, Lecture Notes: Convex Optimization",
            "arxiv": "2607.11664v1",
            "source_tar_sha256": "d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748",
            "license": "CC BY 4.0",
        },
        "coverage": "complete Habring v1 preface and chapters 1-9 in id-ID",
        "larger_o015_status": "partial",
        "backend": {"protected_records": 2472, "new_records": 624, "records": 3096},
        "model_provenance": MODEL_ID,
        "entry_count": len(source_entries),
        "entries": [
            {"path": name, "bytes": len(data), "sha256": digest_bytes(data)} for name, data in source_entries
        ],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        info, data = zip_entry("BUNDLE_MANIFEST.json", canonical_json(manifest))
        archive.writestr(info, data, compresslevel=9)
        for name, data in source_entries:
            info, payload = zip_entry(name, data)
            archive.writestr(info, payload, compresslevel=9)
    return buffer.getvalue()


def verify_bundle(data: bytes) -> dict[str, object]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        bad = archive.testzip()
        names = archive.namelist()
        if not names or names[0] != "BUNDLE_MANIFEST.json" or len(names) != len(set(names)):
            raise RuntimeError("bundle order/uniqueness gate failed")
        manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))
        expected_names = {"BUNDLE_MANIFEST.json", *(entry["path"] for entry in manifest["entries"])}
        if set(names) != expected_names or manifest.get("entry_count") != len(manifest.get("entries", [])):
            raise RuntimeError("bundle manifest inventory gate failed")
        for item in manifest["entries"]:
            payload = archive.read(item["path"])
            if len(payload) != item["bytes"] or digest_bytes(payload) != item["sha256"]:
                raise RuntimeError(f"bundle member identity gate failed: {item['path']}")
        if bad is not None:
            raise RuntimeError(f"ZIP CRC gate failed: {bad}")
    return {
        "integrity": "pass",
        "entries": len(names),
        "manifest_bound_entries": manifest["entry_count"],
        "unique_names": True,
        "forbidden_entries": 0,
        "mutable_global_control_files": 0,
    }


def packaged_material_paths() -> list[Path]:
    """Substantive continuation files nested in the one public release ZIP."""
    return [HTML_PATH, EPUB_PATH, HERE / BUNDLE_NAME, LICENSE_PATH, README_PATH]


def packaged_paths() -> list[Path]:
    return packaged_material_paths() + [HERE / MANIFEST_NAME, HERE / SUMS_NAME]


def addition_paths() -> list[Path]:
    """The only two new Zenodo file slots used by this checkpoint."""
    return [PDF_PATH, HERE / COMPLETE_BUNDLE_NAME]


def make_manifest() -> dict:
    cfg = config()
    lock = input_lock()
    bundle_path = HERE / BUNDLE_NAME
    bundle_check = verify_bundle(bundle_path.read_bytes())
    qa = {
        name: identity(ROOT / name)
        for name in freeze.QA_REPORTS
    }
    controls = cfg["controls"]
    return {
        "schema": "o015-zenodo-additive-checkpoint-v2",
        "title": "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia",
        "version": VERSION,
        "publication_date": "2026-08-25",
        "status": STATUS,
        "complete_corpus": False,
        "canonical_editable_spine": "Andreas Habring, arXiv:2607.11664v1",
        "admitted_boundary": "complete Habring v1 preface and chapters 1-9 in id-ID",
        "component_status": "Habring v1 spine complete; larger O015 coursebook partial",
        "next_boundary": "bounded Becker subset freeze/build/dedup; finite original closure follows",
        "default_preview": PDF_PATH.name,
        "semantic_html_primary": True,
        "epub3_available": True,
        "reader_pdf_tagged": False,
        "human_native_speaker_review": False,
        "model_provenance": MODEL_ID,
        "rights_notice": "Rights are component-specific; no umbrella license replaces inherited component rights.",
        "component_rights": COMPONENT_RIGHTS,
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "zenodo_concept_id": CONCEPT_ID,
        "zenodo_concept_doi": CONCEPT_DOI,
        "inherited_file_count": EXPECTED_INHERITED_COUNT,
        "addition_file_count": EXPECTED_ADDITION_COUNT,
        "release_file_count": EXPECTED_RELEASE_COUNT,
        "public_additions_in_order": [
            {**identity(PDF_PATH), "role": "primary_reader_and_default_preview"},
            {
                "filename": COMPLETE_BUNDLE_NAME,
                "role": "deterministic_comprehensive_continuation_bundle",
                "identity_recorded_outside_bundle": True,
            },
        ],
        "comprehensive_bundle": {
            "filename": COMPLETE_BUNDLE_NAME,
            "member_count": 7,
            "members": [path.name for path in packaged_paths()],
            "contains_itself": False,
            "identity_location": "local preparation receipt and public readback receipt",
        },
        "packaged_material_files": [identity(path) for path in packaged_material_paths()],
        "generated_packaged_files": [MANIFEST_NAME, SUMS_NAME],
        "source_backend_bundle_verification": bundle_check,
        "lane_closure": {
            "coverage": "preface and chapters 1-9",
            "reader": {
                "pdf": identity(PDF_PATH),
                "html": identity(HTML_PATH),
                "epub": identity(EPUB_PATH),
                "pdf_pages": 139,
            },
            "backend": {
                "protected_records": 2472,
                "new_records": 624,
                "records": 3096,
                "jsonl": identity(ROOT / "backend/records.jsonl"),
                "csv": identity(ROOT / "backend/records.csv"),
            },
            "correction_events": {"count": 65, "first": "O015-HAB-ADV-0097", "last": "O015-HAB-ADV-0161"},
            "qa": qa,
            "control_bindings": controls,
            "input_lock": identity(INPUT_LOCK_PATH),
            "result": "pass",
        },
        "metadata_template": identity(TEMPLATE_PATH),
    }


def make_sums() -> bytes:
    # This checksum file binds every other member of the comprehensive ZIP.
    # The visible PDF identity is recorded in the manifest, avoiding any
    # self-reference through the outer ZIP or this checksum file.
    paths = packaged_material_paths() + [HERE / MANIFEST_NAME]
    return "".join(f"{file_digest(path)}  {path.name}\n" for path in sorted(paths, key=lambda item: item.name)).encode("ascii")


def comprehensive_entries() -> list[tuple[str, bytes]]:
    paths = [
        README_PATH,
        LICENSE_PATH,
        HTML_PATH,
        EPUB_PATH,
        HERE / BUNDLE_NAME,
        HERE / MANIFEST_NAME,
        HERE / SUMS_NAME,
    ]
    entries = [(path.name, path.read_bytes()) for path in paths]
    names = [name for name, _ in entries]
    if (
        len(names) != len(set(names))
        or COMPLETE_BUNDLE_NAME in names
        or any(".." in Path(name).parts or Path(name).is_absolute() for name in names)
    ):
        raise RuntimeError("comprehensive bundle contains duplicate, recursive, or unsafe names")
    return entries


def make_comprehensive_bundle_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in comprehensive_entries():
            info, payload = zip_entry(name, data)
            archive.writestr(info, payload, compresslevel=9)
    return buffer.getvalue()


def verify_comprehensive_bundle(data: bytes) -> dict[str, object]:
    expected_entries = comprehensive_entries()
    expected_names = [name for name, _ in expected_entries]
    expected_bytes = {name: payload for name, payload in expected_entries}
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        bad = archive.testzip()
        names = archive.namelist()
        if names != expected_names or len(names) != len(set(names)) or COMPLETE_BUNDLE_NAME in names:
            raise RuntimeError("comprehensive bundle order/uniqueness/non-recursion gate failed")
        for name in names:
            payload = archive.read(name)
            if payload != expected_bytes[name]:
                raise RuntimeError(f"comprehensive bundle member identity drift: {name}")
        manifest = json.loads(archive.read(MANIFEST_NAME))
        if (
            manifest.get("schema") != "o015-zenodo-additive-checkpoint-v2"
            or manifest.get("addition_file_count") != EXPECTED_ADDITION_COUNT
            or manifest.get("release_file_count") != EXPECTED_RELEASE_COUNT
            or manifest.get("comprehensive_bundle", {}).get("filename") != COMPLETE_BUNDLE_NAME
            or manifest.get("comprehensive_bundle", {}).get("contains_itself") is not False
        ):
            raise RuntimeError("comprehensive bundle manifest/count gate failed")
        checksum_lines = archive.read(SUMS_NAME).decode("ascii").splitlines()
        checksum_map: dict[str, str] = {}
        for line in checksum_lines:
            parts = line.split("  ", 1)
            if len(parts) != 2 or len(parts[0]) != 64 or parts[1] in checksum_map:
                raise RuntimeError("comprehensive bundle checksum syntax/uniqueness gate failed")
            checksum_map[parts[1]] = parts[0]
        checksum_members = [path.name for path in packaged_material_paths()] + [MANIFEST_NAME]
        expected_checksums = {name: digest_bytes(archive.read(name)) for name in checksum_members}
        if checksum_map != expected_checksums:
            raise RuntimeError("comprehensive bundle inner SHA-256 inventory gate failed")
        source_verification = verify_bundle(archive.read(BUNDLE_NAME))
        if bad is not None:
            raise RuntimeError(f"comprehensive ZIP CRC gate failed: {bad}")
    return {
        "integrity": "pass",
        "entries": len(expected_names),
        "unique_names": True,
        "recursive_entries": 0,
        "checksum_bound_entries": len(expected_checksums),
        "source_backend_bundle_verification": source_verification,
    }


def build_all() -> dict:
    input_lock()
    validate_template()
    validate_docs()
    inherited = inherited_inventory()
    bundle = make_bundle_bytes()
    verify_bundle(bundle)
    atomic_write(HERE / BUNDLE_NAME, bundle)
    manifest = make_manifest()
    atomic_write(HERE / MANIFEST_NAME, canonical_json(manifest))
    atomic_write(HERE / SUMS_NAME, make_sums())
    comprehensive = make_comprehensive_bundle_bytes()
    verify_comprehensive_bundle(comprehensive)
    atomic_write(HERE / COMPLETE_BUNDLE_NAME, comprehensive)
    additions = addition_paths()
    names = [path.name for path in additions]
    if len(additions) != EXPECTED_ADDITION_COUNT or len(names) != len(set(names)):
        raise RuntimeError("addition count/uniqueness gate failed")
    collisions = set(names) & set(inherited)
    if collisions:
        raise RuntimeError(f"additive release would replace inherited files: {sorted(collisions)}")
    if len(inherited) + len(additions) != EXPECTED_RELEASE_COUNT:
        raise RuntimeError("release inventory count gate failed")
    return manifest


def local_inventory() -> dict[str, dict[str, object]]:
    inherited = inherited_inventory()
    additions = {path.name: identity(path) for path in addition_paths()}
    if set(inherited) & set(additions):
        raise RuntimeError("local additions collide with inherited namespace")
    return {**inherited, **additions}


def validate_local_release() -> dict[str, object]:
    build_all()
    inventory = local_inventory()
    if len(inventory) != EXPECTED_RELEASE_COUNT:
        raise RuntimeError("local release inventory is not 100 files")
    source_bundle = verify_bundle((HERE / BUNDLE_NAME).read_bytes())
    comprehensive_bundle = verify_comprehensive_bundle((HERE / COMPLETE_BUNDLE_NAME).read_bytes())
    return {
        "result": "pass",
        "inherited_files": EXPECTED_INHERITED_COUNT,
        "addition_files": EXPECTED_ADDITION_COUNT,
        "release_files": EXPECTED_RELEASE_COUNT,
        "default_preview": PDF_PATH.name,
        "bundle": {**identity(HERE / COMPLETE_BUNDLE_NAME), **comprehensive_bundle},
        "source_backend_bundle": {**identity(HERE / BUNDLE_NAME), **source_bundle},
        "manifest": identity(HERE / MANIFEST_NAME),
        "checksums": identity(HERE / SUMS_NAME),
    }


if __name__ == "__main__":
    print(json.dumps(validate_local_release(), ensure_ascii=False, indent=2, sort_keys=True))
