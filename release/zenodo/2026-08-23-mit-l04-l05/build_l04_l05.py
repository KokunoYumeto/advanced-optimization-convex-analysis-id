#!/usr/bin/env python3
"""Build the deterministic consolidated MIT-L04/L05 Zenodo checkpoint."""

from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS_READBACK = HERE.parent / "2026-08-23-mit-l03" / "zenodo-public-readback-mit-l03.json"
STATE_PATH = HERE / "zenodo-draft-mit-l04-l05.json"
TEMPLATE_PATH = HERE / "zenodo-record-mit-l04-l05.json"
FIXED_ZIP_TIME = (2026, 8, 23, 0, 0, 0)

PARENT_RECORD_ID = "22071175"
PARENT_RECORD_DOI = "10.5281/zenodo.22071175"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.23-mit-p15-19"
MODEL_ID = "OpenAI Codex gpt-5.6-sol, Ultra"
STATUS = "partial / finishing"
SOURCE_PAGES = [15, 16, 17, 18, 19]
NEXT_SOURCE_PAGE = 20

BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.23_MIT_L04_L05_DELTA.zip"
MANIFEST_NAME = "release-manifest-mit-l04-l05.json"
SUMS_NAME = "SHA256SUMS-mit-l04-l05"
EXPECTED_INHERITED_COUNT = 40
EXPECTED_ADDITION_COUNT = 10
EXPECTED_RELEASE_COUNT = EXPECTED_INHERITED_COUNT + EXPECTED_ADDITION_COUNT

READER_PATHS = [
    ROOT / "output/pdf/D90-MIT-04-kebangkitan-era-algoritmik-id.pdf",
    ROOT / "output/html/D90-MIT-04-kebangkitan-era-algoritmik-id.html",
    ROOT / "output/pdf/D90-MIT-05-orientasi-kursus-id.pdf",
    ROOT / "output/html/D90-MIT-05-orientasi-kursus-id.html",
]
RELEASE_DOCS = ["README_MIT_L04_L05.md", "README_RELEASE_MIT_L04_L05.md", "RIGHTS_MIT_L04_L05.md"]

# This is deliberately a bounded continuation capsule, not a workspace snapshot.
BUNDLE_ROOT_PATHS = [
    "PROVENANCE.md",
    "README.md",
    "RIGHTS.md",
    "backend/backend_schema.json",
    "backend/records.jsonl",
    "backend/records.csv",
    "source/en/mit-04-rise-algorithmic-era-semantic-witness.md",
    "source/en/mit-05-course-orientation-semantic-witness.md",
    "source/id-ID/mit-04-kebangkitan-era-algoritmik-id.md",
    "source/id-ID/mit-05-orientasi-kursus-id.md",
    "source/id-ID/mit-l02.css",
    "source/id-ID/mit-l05.css",
    "source/id-ID/mit-l04-preamble.tex",
    "source/id-ID/mit-l05-preamble.tex",
    "source/id-ID/mit-l03-pdf-filter.lua",
    "source/id-ID/mit-l04-before-body.html",
    "source/id-ID/mit-l05-before-body.html",
    "source/id-ID/mit-l03-after-body.html",
    "qa/build_mit_l04.py",
    "qa/validate_mit_l04.py",
    "qa/MIT_L04_VALIDATION.json",
    "qa/MIT_L04_BROWSER_QA.json",
    "qa/MIT_L04_VISUAL_QA.json",
    "qa/MIT_L04_INDEPENDENT_REREVIEW.md",
    "qa/extend_backend_mit_l04.py",
    "qa/validate_backend_mit_l04.py",
    "qa/MIT_L04_BACKEND_VALIDATION.json",
    "qa/build_mit_l05.py",
    "qa/validate_mit_l05.py",
    "qa/MIT_L05_VALIDATION.json",
    "qa/MIT_L05_BROWSER_QA.json",
    "qa/MIT_L05_VISUAL_QA.json",
    "qa/MIT_L05_INDEPENDENT_REREVIEW.md",
    "qa/extend_backend_mit_l05.py",
    "qa/validate_backend_mit_l05.py",
    "qa/MIT_L05_BACKEND_VALIDATION.json",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/BUILD_AND_QA.md",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/CURRENT_CURSOR.md",
    "00_control/CURRENT_GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/DECISION_LOG.md",
    "00_control/INDONESIAN_TERMINOLOGY_QA_20260822.md",
    "00_control/MIT_L05_CORRECTION_SNAPSHOT.jsonl",
    "00_control/MIT_L05_P16_19_BOUNDARY_CENSUS.md",
    "00_control/PUBLICATION_RECEIPTS.md",
    "00_control/SOURCE_AUTHORITY.json",
    "authority/mit-ocw-6.253/official-pages/CC-BY-NC-SA-4.0-legalcode.txt",
]

COMPONENT_RIGHTS = {
    "new_mit_readers_and_semantic_sources": "CC BY-NC-SA 4.0",
    "new_project_build_qa_backend_and_control": "project-local tooling and evidence; no blanket reuse grant asserted",
    "inherited_habring_components": "CC BY 4.0",
    "inherited_griffin_penn_components": "CC BY-NC-SA 3.0 United States",
    "inherited_royer_source_freeze": "CC BY-NC 4.0",
}


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
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


def inherited_inventory() -> dict[str, dict[str, object]]:
    data = read_json(PREVIOUS_READBACK)
    if (
        str(data.get("record_id")) != PARENT_RECORD_ID
        or data.get("record_doi") != PARENT_RECORD_DOI
        or str(data.get("concept_id")) != CONCEPT_ID
        or data.get("concept_doi") != CONCEPT_DOI
        or data.get("status") != "published"
    ):
        raise RuntimeError("prior public readback does not identify the required parent and concept")
    files = data.get("files", [])
    result = {
        item["filename"]: {
            "filename": item["filename"],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
        }
        for item in files
    }
    if (
        len(files) != EXPECTED_INHERITED_COUNT
        or len(result) != EXPECTED_INHERITED_COUNT
        or data.get("file_count") != EXPECTED_INHERITED_COUNT
        or data.get("inherited_identity") != "pass"
        or any(item.get("public_byte_identity") != "pass" for item in files)
    ):
        raise RuntimeError("prior public readback does not prove exactly 40 unique public files")
    return result


def validate_template() -> dict:
    template = read_json(TEMPLATE_PATH)
    metadata = template.get("metadata", {})
    serialized = json.dumps(metadata, ensure_ascii=False)
    contributors = [
        item
        for item in metadata.get("contributors", [])
        if item.get("person_or_org", {}).get("name") == "TTP"
    ]
    if (
        serialized.count("TTP") != 1
        or len(contributors) != 1
        or contributors[0].get("person_or_org", {}).get("type") != "organizational"
        or "TTP" in metadata.get("title", "")
        or "TTP" in metadata.get("description", "")
    ):
        raise RuntimeError("metadata must contain only the existing single organizational contributor entry")
    if metadata.get("version") != VERSION or serialized.count(MODEL_ID) != 1:
        raise RuntimeError("metadata version/model provenance gate failed")
    lowered = metadata.get("description", "").lower()
    for required in ("halaman 15-19", "halaman 20", "belum lengkap", "induk", "cc by-nc-sa 4.0"):
        if required not in lowered:
            raise RuntimeError(f"metadata description lacks {required!r}")
    return metadata


def validate_release_docs() -> None:
    combined = "\n".join((HERE / name).read_text(encoding="utf-8") for name in RELEASE_DOCS)
    if "TTP" in combined:
        raise RuntimeError("release documents must not add a TTP mention")
    lowered = combined.lower()
    for required in ("halaman 15-19", "halaman 20", "belum lengkap", "cc by-nc-sa 4.0"):
        if required not in lowered:
            raise RuntimeError(f"release documents lack {required!r}")


def require_identity(path: Path, record: dict, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if record.get("bytes") != path.stat().st_size or record.get("sha256") != file_digest(path):
        raise RuntimeError(f"{label} identity differs from its validation report")


def validate_lane_closure() -> dict[str, object]:
    expected = {
        "l04": {
            "report": ROOT / "qa/MIT_L04_VALIDATION.json",
            "backend": ROOT / "qa/MIT_L04_BACKEND_VALIDATION.json",
            "pages": [15],
            "next": 16,
            "html": READER_PATHS[1],
            "pdf": READER_PATHS[0],
        },
        "l05": {
            "report": ROOT / "qa/MIT_L05_VALIDATION.json",
            "backend": ROOT / "qa/MIT_L05_BACKEND_VALIDATION.json",
            "pages": [16, 17, 18, 19],
            "next": 20,
            "html": READER_PATHS[3],
            "pdf": READER_PATHS[2],
        },
    }
    result: dict[str, object] = {}
    backend_reports: dict[str, dict] = {}
    for lane, spec in expected.items():
        report = read_json(spec["report"])
        boundary = report.get("boundary", {})
        if (
            report.get("result") != "pass"
            or report.get("model_identification") != MODEL_ID
            or boundary.get("source_pdf_pages") != spec["pages"]
            or boundary.get("next_source_page") != spec["next"]
            or report.get("human_native_speaker_review") is not False
        ):
            raise RuntimeError(f"{lane} content validation closure failed")
        require_identity(spec["html"], report.get("files", {}).get("html", {}), f"{lane} HTML")
        require_identity(spec["pdf"], report.get("files", {}).get("pdf", {}), f"{lane} PDF")
        if report.get("pdf", {}).get("tagged") is not False or report.get("pdf", {}).get("searchable") is not True:
            raise RuntimeError(f"{lane} PDF limitation/searchability gate failed")

        backend = read_json(spec["backend"])
        if backend.get("result") != "pass":
            raise RuntimeError(f"{lane} backend validation is not pass")
        backend_reports[lane] = backend
        if lane == "l05":
            require_identity(ROOT / "backend/records.jsonl", backend.get("backend", {}).get("jsonl", {}), "final L05 backend JSONL")
            require_identity(ROOT / "backend/records.csv", backend.get("backend", {}).get("csv", {}), "final L05 backend CSV")
            snapshot = ROOT / "00_control/MIT_L05_CORRECTION_SNAPSHOT.jsonl"
            require_identity(snapshot, backend.get("canonical_identities", {}).get("ledger_snapshot", {}), "L05 correction snapshot")
            snapshot_lines = snapshot.read_text(encoding="utf-8").splitlines()
            if len(snapshot_lines) != 1 or json.loads(snapshot_lines[0]).get("event_id") != "O015-MIT-SEM-0004":
                raise RuntimeError("L05 correction snapshot is not the exact one-event closure")
        result[lane] = {
            "content_validation": identity(spec["report"]),
            "backend_validation": identity(spec["backend"]),
            "source_pages": spec["pages"],
            "next_source_page": spec["next"],
            "result": "pass",
        }
    l04_backend = backend_reports["l04"].get("backend", {})
    l05_baseline = backend_reports["l05"].get("protected_baseline", {})
    for kind in ("jsonl", "csv"):
        baseline_identity = l05_baseline.get(kind, {}).get("expected", l05_baseline.get(kind, {}))
        if baseline_identity.get("bytes") != l04_backend.get(kind, {}).get("bytes") or baseline_identity.get("sha256") != l04_backend.get(kind, {}).get("sha256"):
            raise RuntimeError(f"L05 protected {kind} baseline does not bind the admitted L04 backend")
    return result


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def bundle_inputs() -> list[tuple[str, Path]]:
    pairs = [(relative, ROOT / relative) for relative in BUNDLE_ROOT_PATHS]
    pairs.extend((f"release-notes/{name}", HERE / name) for name in RELEASE_DOCS)
    pairs.sort(key=lambda pair: pair[0])
    if len({name for name, _ in pairs}) != len(pairs):
        raise RuntimeError("duplicate bundle entry name")
    missing = [f"{name}: {path}" for name, path in pairs if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing bundle inputs:\n" + "\n".join(missing))

    forbidden: list[str] = []
    forbidden_suffixes = (
        ".zip", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg", ".mpl",
    )
    for name, path in pairs:
        lowered = name.lower().replace("\\", "/")
        segments = lowered.split("/")
        if (
            any(segment in {".git", "__pycache__", "cache", ".cache", ".pytest_cache", ".mypy_cache", "tmp", "temp"} for segment in segments)
            or lowered.endswith(forbidden_suffixes)
            or "course-archive" in lowered
            or "downloads/" in lowered
            or "credential" in lowered
            or "token" in lowered
        ):
            forbidden.append(name)
        payload = path.read_bytes()
        if b"zenodo_pat_" in payload:
            forbidden.append(f"credential-shaped content: {name}")
    if forbidden:
        raise RuntimeError("forbidden bundle inputs:\n" + "\n".join(forbidden))
    return pairs


def verify_bundle(payload: bytes) -> dict[str, object]:
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("delta ZIP integrity failure")
        names = archive.namelist()
        if len(names) != len(set(names)) or "DELTA_BUNDLE_MANIFEST.json" not in names:
            raise RuntimeError("delta ZIP uniqueness/manifest gate failed")
        manifest = json.loads(archive.read("DELTA_BUNDLE_MANIFEST.json"))
        entries = manifest.get("entries", [])
        expected_names = {"DELTA_BUNDLE_MANIFEST.json", *(entry["path"] for entry in entries)}
        if set(names) != expected_names or manifest.get("entry_count") != len(entries):
            raise RuntimeError("delta ZIP inventory differs from internal manifest")
        for entry in entries:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or digest_bytes(data) != entry["sha256"]:
                raise RuntimeError(f"delta ZIP hash mismatch: {entry['path']}")
        forbidden = [name for name in names if name.lower().endswith((".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"))]
        if forbidden:
            raise RuntimeError(f"binary authority/image/archive payload leaked into delta ZIP: {forbidden}")
        if (
            manifest.get("source_pages") != SOURCE_PAGES
            or manifest.get("next_source_page") != NEXT_SOURCE_PAGE
            or manifest.get("complete_corpus") is not False
            or manifest.get("status") != STATUS
            or manifest.get("component_rights") != COMPONENT_RIGHTS
            or manifest.get("model_provenance") != MODEL_ID
            or manifest.get("authority_pdf_bytes") != 0
            or manifest.get("source_image_bytes") != 0
        ):
            raise RuntimeError("delta ZIP boundary/rights/status/model gate failed")
        return {
            "entries": len(names),
            "manifest_entries_verified": len(entries),
            "integrity": "pass",
            "forbidden_entries": 0,
        }


def build_bundle(lane_closure: dict[str, object]) -> tuple[Path, dict[str, object]]:
    pairs = bundle_inputs()
    entries = [{"path": name, "bytes": path.stat().st_size, "sha256": file_digest(path)} for name, path in pairs]
    inner = {
        "schema": "o015-mit-l04-l05-delta-bundle-v1",
        "version": VERSION,
        "scope": "MIT 6.253 complete-notes pages 15-19; compact L04/L05 source, build, QA, backend, control, and license closure",
        "status": STATUS,
        "complete_corpus": False,
        "source_pages": SOURCE_PAGES,
        "next_source_page": NEXT_SOURCE_PAGE,
        "next_source_heading": "LECTURE 2",
        "component_rights": COMPONENT_RIGHTS,
        "model_provenance": MODEL_ID,
        "human_native_speaker_review": False,
        "semantic_html_primary": True,
        "reader_pdfs_tagged": False,
        "authority_pdf_bytes": 0,
        "source_image_bytes": 0,
        "lane_closure": lane_closure,
        "entry_count": len(entries),
        "entries": entries,
    }
    manifest_bytes = (json.dumps(inner, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    destination = HERE / BUNDLE_NAME
    with tempfile.NamedTemporaryFile(prefix=".mit-l04-l05-delta-", suffix=".zip", dir=HERE, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            add_bytes(archive, "DELTA_BUNDLE_MANIFEST.json", manifest_bytes)
            for name, path in pairs:
                add_bytes(archive, name, path.read_bytes())
        verification = verify_bundle(temporary.read_bytes())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination, verification


def addition_material_paths() -> list[Path]:
    paths = [*READER_PATHS, HERE / BUNDLE_NAME, *(HERE / name for name in RELEASE_DOCS)]
    if len(paths) != 8 or len({path.name for path in paths}) != 8:
        raise RuntimeError("expected eight unique pre-manifest additions")
    return paths


def addition_paths() -> list[Path]:
    paths = addition_material_paths() + [HERE / MANIFEST_NAME, HERE / SUMS_NAME]
    if len(paths) != EXPECTED_ADDITION_COUNT or len({path.name for path in paths}) != EXPECTED_ADDITION_COUNT:
        raise RuntimeError("expected exactly ten unique additions")
    inherited_names = set(inherited_inventory())
    collisions = set(path.name for path in paths) & inherited_names
    if collisions:
        raise RuntimeError(f"new additions collide with inherited filenames: {sorted(collisions)}")
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing additive release files:\n" + "\n".join(missing))
    return paths


def draft_identity() -> tuple[str | None, str | None]:
    if not STATE_PATH.is_file():
        return None, None
    data = read_json(STATE_PATH)
    return str(data["draft_id"]), str(data["draft_doi"])


def build_release_metadata(bundle_verification: dict[str, object], lane_closure: dict[str, object]) -> None:
    record_id, record_doi = draft_identity()
    material = [identity(path) for path in sorted(addition_material_paths(), key=lambda path: path.name)]
    manifest = {
        "schema": "o015-zenodo-additive-checkpoint-v1",
        "version": VERSION,
        "publication_date": "2026-08-23",
        "title": "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia",
        "status": STATUS,
        "complete_corpus": False,
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "zenodo_concept_id": CONCEPT_ID,
        "zenodo_concept_doi": CONCEPT_DOI,
        "zenodo_record_id": record_id,
        "zenodo_record_doi": record_doi,
        "release_file_count": EXPECTED_RELEASE_COUNT,
        "inherited_file_count": EXPECTED_INHERITED_COUNT,
        "addition_file_count": EXPECTED_ADDITION_COUNT,
        "addition_material_files": material,
        "generated_addition_files": [MANIFEST_NAME, SUMS_NAME],
        "delta_bundle_verification": bundle_verification,
        "lane_closure": lane_closure,
        "admitted_source_pages": SOURCE_PAGES,
        "admitted_boundary": "MIT 6.253 complete-notes PDF pages 15-19, L04 and L05",
        "next_boundary": "MIT 6.253 complete-notes PDF page 20, LECTURE 2",
        "component_rights": COMPONENT_RIGHTS,
        "rights_notice": "Rights are component-specific; no umbrella license replaces inherited component rights.",
        "human_native_speaker_review": False,
        "semantic_html_primary": True,
        "reader_pdfs_tagged": False,
        "model_provenance": MODEL_ID,
        "metadata_template": identity(TEMPLATE_PATH),
    }
    manifest_path = HERE / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    values = {name: item["sha256"] for name, item in inherited_inventory().items()}
    values.update({path.name: file_digest(path) for path in addition_material_paths()})
    values[MANIFEST_NAME] = file_digest(manifest_path)
    if len(values) != EXPECTED_RELEASE_COUNT - 1:
        raise RuntimeError("checksum inventory count mismatch")
    (HERE / SUMS_NAME).write_text(
        "".join(f"{values[name]}  {name}\n" for name in sorted(values)),
        encoding="ascii",
        newline="\n",
    )


def checksum_inventory() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in (HERE / SUMS_NAME).read_text(encoding="ascii").splitlines():
        digest, separator, name = line.partition("  ")
        if separator != "  " or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise RuntimeError(f"malformed checksum line: {line!r}")
        if name in result:
            raise RuntimeError(f"duplicate checksum filename: {name}")
        result[name] = digest
    return result


def validate_local_release(require_draft_binding: bool = False) -> dict[str, object]:
    validate_template()
    validate_release_docs()
    lane_closure = validate_lane_closure()
    bundle_result = verify_bundle((HERE / BUNDLE_NAME).read_bytes())
    manifest = read_json(HERE / MANIFEST_NAME)
    if (
        manifest.get("release_file_count") != EXPECTED_RELEASE_COUNT
        or manifest.get("inherited_file_count") != EXPECTED_INHERITED_COUNT
        or manifest.get("addition_file_count") != EXPECTED_ADDITION_COUNT
        or manifest.get("admitted_source_pages") != SOURCE_PAGES
        or manifest.get("next_boundary") != "MIT 6.253 complete-notes PDF page 20, LECTURE 2"
        or manifest.get("component_rights") != COMPONENT_RIGHTS
        or manifest.get("complete_corpus") is not False
        or manifest.get("status") != STATUS
        or manifest.get("model_provenance") != MODEL_ID
    ):
        raise RuntimeError("release manifest boundary/count/rights/status/model gate failed")
    expected_material = [identity(path) for path in sorted(addition_material_paths(), key=lambda path: path.name)]
    if manifest.get("addition_material_files") != expected_material:
        raise RuntimeError("release manifest material identities differ")
    if manifest.get("lane_closure") != lane_closure or manifest.get("delta_bundle_verification") != bundle_result:
        raise RuntimeError("release manifest QA/bundle closure differs")
    if require_draft_binding:
        record_id, record_doi = draft_identity()
        if manifest.get("zenodo_record_id") != record_id or manifest.get("zenodo_record_doi") != record_doi:
            raise RuntimeError("release manifest is not bound to the prepared draft")

    paths = addition_paths()
    expected_checksums = {name: item["sha256"] for name, item in inherited_inventory().items()}
    expected_checksums.update({path.name: file_digest(path) for path in paths if path.name != SUMS_NAME})
    actual_checksums = checksum_inventory()
    if actual_checksums != expected_checksums:
        raise RuntimeError("checksum inventory or byte identities differ")
    return {
        "result": "pass",
        "release_files": EXPECTED_RELEASE_COUNT,
        "inherited_files": EXPECTED_INHERITED_COUNT,
        "addition_files": EXPECTED_ADDITION_COUNT,
        "source_pages": SOURCE_PAGES,
        "next_source_page": NEXT_SOURCE_PAGE,
        "status": STATUS,
        "model_provenance": MODEL_ID,
        "delta_bundle": identity(HERE / BUNDLE_NAME),
        "delta_bundle_verification": bundle_result,
        "manifest": identity(HERE / MANIFEST_NAME),
        "checksums": identity(HERE / SUMS_NAME),
        "lane_closure": lane_closure,
    }


def local_inventory() -> dict[str, dict[str, object]]:
    result = dict(inherited_inventory())
    for path in addition_paths():
        result[path.name] = identity(path)
    if len(result) != EXPECTED_RELEASE_COUNT:
        raise RuntimeError("local release inventory count mismatch")
    return result


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    validate_template()
    validate_release_docs()
    lane_closure = validate_lane_closure()
    _, verification = build_bundle(lane_closure)
    build_release_metadata(verification, lane_closure)
    print(json.dumps(validate_local_release(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
