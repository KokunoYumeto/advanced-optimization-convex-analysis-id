#!/usr/bin/env python3
"""Build the deterministic additive MIT-L06 Zenodo checkpoint.

The builder is intentionally fail-closed.  It accepts only the frozen final
L06 reader/QA/backend identities and requires the durable controls to describe
the admitted pages 20--28 boundary, 1,714-record backend, and page-29 cursor.
It performs no network operation.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS_READBACK = HERE.parent / "2026-08-23-mit-l04-l05" / "zenodo-public-readback-mit-l04-l05.json"
STATE_PATH = HERE / "zenodo-draft-mit-l06.json"
TEMPLATE_PATH = HERE / "zenodo-record-mit-l06.json"
INPUT_LOCK_PATH = HERE / "release-input-lock-mit-l06.json"
FIXED_ZIP_TIME = (2026, 8, 23, 0, 0, 0)

PARENT_RECORD_ID = "22072071"
PARENT_RECORD_DOI = "10.5281/zenodo.22072071"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.23-mit-l06-p20-28"
MODEL_ID = "OpenAI Codex gpt-5.6-sol, Ultra"
STATUS = "partial"
SOURCE_PAGES = list(range(20, 29))
NEXT_SOURCE_PAGE = 29

BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.23_MIT_L06_DELTA.zip"
MANIFEST_NAME = "release-manifest-mit-l06.json"
SUMS_NAME = "SHA256SUMS-mit-l06"
EXPECTED_INHERITED_COUNT = 50
EXPECTED_ADDITION_COUNT = 8
EXPECTED_RELEASE_COUNT = EXPECTED_INHERITED_COUNT + EXPECTED_ADDITION_COUNT

READER_PATHS = [
    ROOT / "output/pdf/D90-MIT-06-kuliah-2-landasan-konveks-id.pdf",
    ROOT / "output/html/D90-MIT-06-kuliah-2-landasan-konveks-id.html",
]
RELEASE_DOCS = ["README_MIT_L06.md", "README_RELEASE_MIT_L06.md", "LICENSE_MIT_L06.md"]

# Compact continuation closure, not a repository or authority snapshot.
BUNDLE_ROOT_PATHS = [
    "PROVENANCE.md",
    "README.md",
    "RIGHTS.md",
    "backend/backend_schema.json",
    "backend/records.jsonl",
    "backend/records.csv",
    "source/en/mit-06-lecture-2-convex-foundations-semantic-witness.md",
    "source/id-ID/mit-06-kuliah-2-landasan-konveks-id.md",
    "source/id-ID/mit-l06.css",
    "source/id-ID/mit-l06-preamble.tex",
    "source/id-ID/mit-l06-pdf-filter.lua",
    "source/id-ID/mit-l06-before-body.html",
    "source/id-ID/mit-l06-after-body.html",
    "qa/build_mit_l06.py",
    "qa/validate_mit_l06.py",
    "qa/MIT_L06_VALIDATION.json",
    "qa/MIT_L06_BROWSER_QA.json",
    "qa/MIT_L06_VISUAL_QA.json",
    "qa/MIT_L06_INDEPENDENT_REREVIEW.md",
    "qa/extend_backend_mit_l06.py",
    "qa/validate_backend_mit_l06.py",
    "qa/MIT_L06_BACKEND_VALIDATION.json",
    "00_control/MIT_L06_LECTURE_2_PAGES_020-028_BOUNDARY_CENSUS.md",
    "00_control/MIT_L06_CORRECTION_SNAPSHOT.jsonl",
    "00_control/ADVERSE_LEDGER.jsonl",
    "00_control/BUILD_AND_QA.md",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/CURRENT_CURSOR.md",
    "00_control/CURRENT_GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/DECISION_LOG.md",
    "00_control/PUBLICATION_RECEIPTS.md",
    "00_control/SOURCE_AUTHORITY.json",
    "authority/mit-ocw-6.253/official-pages/CC-BY-NC-SA-4.0-legalcode.txt",
]

COMPONENT_RIGHTS = {
    "new_mit_reader_semantic_source_and_adaptation": "CC BY-NC-SA 4.0",
    "new_project_build_qa_backend_and_control": "project-local tooling and evidence; no blanket reuse grant asserted",
    "athena_scientific_graphics": "permission-only; zero source graphic bytes or layouts redistributed",
    "inherited_habring_components": "CC BY 4.0",
    "inherited_griffin_penn_components": "CC BY-NC-SA 3.0 United States",
    "inherited_royer_source_freeze": "CC BY-NC 4.0",
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


def require_identity(path: Path, expected: dict, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if expected.get("bytes") != path.stat().st_size or expected.get("sha256") != file_digest(path):
        raise RuntimeError(f"{label} differs from its frozen final identity: {path}")


def inherited_inventory() -> dict[str, dict[str, object]]:
    data = read_json(PREVIOUS_READBACK)
    if (
        str(data.get("record_id")) != PARENT_RECORD_ID
        or data.get("record_doi") != PARENT_RECORD_DOI
        or str(data.get("concept_id")) != CONCEPT_ID
        or data.get("concept_doi") != CONCEPT_DOI
        or data.get("status") != "published"
    ):
        raise RuntimeError("frozen readback does not identify parent record 22072071 in the required concept")
    files = data.get("files", [])
    result = {
        item["filename"]: {"filename": item["filename"], "bytes": item["bytes"], "sha256": item["sha256"]}
        for item in files
    }
    if (
        len(files) != EXPECTED_INHERITED_COUNT
        or len(result) != EXPECTED_INHERITED_COUNT
        or data.get("file_count") != EXPECTED_INHERITED_COUNT
        or data.get("inherited_identity") != "pass"
        or any(item.get("public_byte_identity") != "pass" for item in files)
    ):
        raise RuntimeError("parent readback does not prove exactly 50 unique public files")
    return result


def validate_template() -> dict:
    template = read_json(TEMPLATE_PATH)
    metadata = template.get("metadata", {})
    if template.get("files", {}).get("default_preview") != READER_PATHS[0].name:
        raise RuntimeError("metadata template must make the L06 PDF the default preview")
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    ttp = [
        item for item in metadata.get("contributors", [])
        if item.get("person_or_org", {}).get("name") == "TTP"
    ]
    if (
        serialized.count("TTP") != 1
        or len(ttp) != 1
        or ttp[0].get("person_or_org", {}).get("type") != "organizational"
        or "TTP" in title
        or "TTP" in description
    ):
        raise RuntimeError("metadata may contain TTP only once as the organizational contributor")
    if metadata.get("version") != VERSION or serialized.count(MODEL_ID) != 1:
        raise RuntimeError("metadata version/model provenance gate failed")
    lowered = description.lower()
    for required in ("halaman 20-28", "halaman 29", "belum lengkap", "50 berkas induk", "cc by-nc-sa 4.0"):
        if required not in lowered:
            raise RuntimeError(f"metadata description lacks {required!r}")
    return metadata


def validate_release_docs() -> None:
    combined = "\n".join((HERE / name).read_text(encoding="utf-8") for name in RELEASE_DOCS)
    if "TTP" in combined:
        raise RuntimeError("release documents must not add a TTP mention")
    lowered = combined.lower()
    for required in ("halaman 20", "halaman 29", "belum lengkap", "cc by-nc-sa 4.0", "athena"):
        if required not in lowered:
            raise RuntimeError(f"release documents lack {required!r}")


def validate_input_lock() -> dict:
    lock = read_json(INPUT_LOCK_PATH)
    if (
        lock.get("schema") != "o015-mit-l06-release-input-lock-v1"
        or lock.get("boundary", {}).get("source_pages") != SOURCE_PAGES
        or lock.get("boundary", {}).get("next_source_page") != NEXT_SOURCE_PAGE
        or lock.get("backend_record_count") != 1714
    ):
        raise RuntimeError("L06 release input lock has a different boundary or backend count")
    files = lock.get("files", {})
    if not isinstance(files, dict) or len(files) != 22:
        raise RuntimeError("L06 input lock must bind exactly 22 final files")
    for relative, expected in files.items():
        require_identity(ROOT / relative, expected, f"input lock {relative}")
    return lock


def _contains_page(text: str, page: int) -> bool:
    return re.search(rf"(?:page|pages|halaman)\s*`?{page}\b", text, flags=re.IGNORECASE) is not None


def _contains_boundary(text: str) -> bool:
    return re.search(r"20\s*(?:-|–|—|--)\s*28", text) is not None


def validate_controls() -> dict[str, dict[str, object]]:
    controls = {
        relative: (ROOT / relative).read_text(encoding="utf-8")
        for relative in (
            "00_control/BUILD_AND_QA.md",
            "00_control/COMPONENT_RIGHTS.csv",
            "00_control/COVERAGE_OVERLAP.md",
            "00_control/CURRENT_CURSOR.md",
            "00_control/CURRENT_GOAL_AND_WORKFLOW.md",
            "00_control/CURRENT_STATE.md",
            "00_control/DECISION_LOG.md",
            "00_control/PUBLICATION_RECEIPTS.md",
            "00_control/SOURCE_AUTHORITY.json",
        )
    }
    normalized = {name: text.lower() for name, text in controls.items()}
    for relative in (
        "00_control/CURRENT_CURSOR.md",
        "00_control/CURRENT_GOAL_AND_WORKFLOW.md",
        "00_control/CURRENT_STATE.md",
    ):
        text = normalized[relative]
        if "l06" not in text or not _contains_page(text, 29):
            raise RuntimeError(f"{relative} has not advanced the admitted L06 cursor to page 29")
    for relative in ("00_control/CURRENT_GOAL_AND_WORKFLOW.md", "00_control/CURRENT_STATE.md"):
        if re.search(r"1[.,]?714", normalized[relative]) is None:
            raise RuntimeError(f"{relative} has not recorded the final 1,714-record backend")
    build_text = normalized["00_control/BUILD_AND_QA.md"]
    if re.search(r"mit[\s_-]*l06", build_text) is None:
        raise RuntimeError("BUILD_AND_QA has no final MIT-L06 section")
    for required in (
        "84ce42542ed58e102c736dacc02b69cf16ab264a577d689d2fe5f7a24ba37d75",
        "9ad375756d2ee3159acf760f5d68084d2921e665cf993e2aaa6514f1e710337e",
        "247fd848a4b4d0c3960ee82d48b7648304215ca69dddf1736305734106615c4c",
    ):
        if required not in build_text:
            raise RuntimeError(f"BUILD_AND_QA has no final L06 binding for {required}")
    for relative in ("00_control/COVERAGE_OVERLAP.md", "00_control/DECISION_LOG.md"):
        text = normalized[relative]
        if "l06" not in text or not _contains_boundary(text):
            raise RuntimeError(f"{relative} has not recorded the complete pages 20-28 boundary")
    rights = normalized["00_control/COMPONENT_RIGHTS.csv"]
    if "l06" not in rights or "cc by-nc-sa 4.0" not in rights or "athena" not in rights:
        raise RuntimeError("COMPONENT_RIGHTS lacks the final L06 license/Athena exclusion")
    authority = normalized["00_control/SOURCE_AUTHORITY.json"]
    if "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181" not in authority:
        raise RuntimeError("SOURCE_AUTHORITY lacks the frozen MIT complete-notes PDF identity")
    if PARENT_RECORD_ID not in controls["00_control/PUBLICATION_RECEIPTS.md"]:
        raise RuntimeError("PUBLICATION_RECEIPTS does not preserve the required parent checkpoint")
    return {relative: identity(ROOT / relative, relative) for relative in sorted(controls)}


def validate_lane_closure() -> dict[str, object]:
    lock = validate_input_lock()
    content = read_json(ROOT / "qa/MIT_L06_VALIDATION.json")
    backend = read_json(ROOT / "qa/MIT_L06_BACKEND_VALIDATION.json")
    if (
        content.get("result") != "pass"
        or content.get("errors") != []
        or content.get("model_identification") != MODEL_ID
        or content.get("boundary", {}).get("source_pdf_pages") != SOURCE_PAGES
        or content.get("boundary", {}).get("next_source_page") != NEXT_SOURCE_PAGE
        or content.get("boundary", {}).get("copied_source_graphics") != 0
        or content.get("human_native_speaker_review") is not False
        or content.get("pdf", {}).get("searchable") is not True
        or content.get("pdf", {}).get("tagged") is not False
        or content.get("rights", {}).get("license") != "CC BY-NC-SA 4.0"
        or content.get("rights", {}).get("athena_source_figures_omitted") != 5
    ):
        raise RuntimeError("final L06 content validation closure failed")
    if (
        content.get("build", {}).get("html_sha256") != lock["files"]["output/html/D90-MIT-06-kuliah-2-landasan-konveks-id.html"]["sha256"]
        or content.get("build", {}).get("pdf_sha256") != lock["files"]["output/pdf/D90-MIT-06-kuliah-2-landasan-konveks-id.pdf"]["sha256"]
        or content.get("build", {}).get("deterministic_rebuilds") != 2
        or content.get("formula_sequence_match") is not True
    ):
        raise RuntimeError("L06 deterministic reader identities/formula sequence are not final")
    for item in content.get("files", {}).values():
        path = item.get("path")
        if not path:
            raise RuntimeError("content receipt contains an unbound file identity")
        require_identity(ROOT / path, item, f"content receipt {path}")

    if (
        backend.get("result") != "pass"
        or backend.get("errors") != []
        or backend.get("backend", {}).get("record_count") != 1714
        or backend.get("admission", {}).get("new_record_count") != 109
        or backend.get("protected_baseline", {}).get("preserved_record_count") != 1605
        or backend.get("admission", {}).get("segment_ids") != [f"d90.mit.ocw-6.253.l06.p{page:03d}" for page in SOURCE_PAGES]
        or backend.get("admission", {}).get("copied_source_graphics") != 0
        or backend.get("independent_validation", {}).get("required_consecutive_processes") != 2
        or backend.get("independent_validation", {}).get("receipt_is_deterministic") is not True
    ):
        raise RuntimeError("final L06 backend validation closure failed")
    for kind, relative in (("jsonl", "backend/records.jsonl"), ("csv", "backend/records.csv")):
        if backend.get("backend", {}).get(kind) != lock["files"][relative]:
            raise RuntimeError(f"backend receipt and release lock disagree for {kind}")
    for item in backend.get("canonical_identities", {}).values():
        path = item.get("path")
        if not path:
            raise RuntimeError("backend receipt contains an unbound canonical identity")
        require_identity(ROOT / path, item, f"backend canonical identity {path}")
    controls = validate_controls()
    return {
        "result": "pass",
        "source_pages": SOURCE_PAGES,
        "next_source_page": NEXT_SOURCE_PAGE,
        "content_validation": identity(ROOT / "qa/MIT_L06_VALIDATION.json"),
        "backend_validation": identity(ROOT / "qa/MIT_L06_BACKEND_VALIDATION.json"),
        "backend": {
            "record_count": 1714,
            "jsonl": identity(ROOT / "backend/records.jsonl"),
            "csv": identity(ROOT / "backend/records.csv"),
        },
        "input_lock": identity(INPUT_LOCK_PATH),
        "controls": controls,
        "human_native_speaker_review": False,
        "reader_pdf_tagged": False,
        "athena_source_graphic_bytes": 0,
    }


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def bundle_inputs() -> list[tuple[str, Path]]:
    pairs = [(relative, ROOT / relative) for relative in BUNDLE_ROOT_PATHS]
    pairs.extend((f"release-notes/{name}", HERE / name) for name in RELEASE_DOCS)
    pairs.append(("release-notes/release-input-lock-mit-l06.json", INPUT_LOCK_PATH))
    pairs.sort(key=lambda pair: pair[0])
    if len({name for name, _ in pairs}) != len(pairs):
        raise RuntimeError("duplicate bundle entry name")
    missing = [f"{name}: {path}" for name, path in pairs if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing bundle inputs:\n" + "\n".join(missing))
    forbidden: list[str] = []
    binary_suffixes = (".zip", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg", ".mpl")
    for name, path in pairs:
        lowered = name.lower().replace("\\", "/")
        segments = lowered.split("/")
        if (
            any(segment in {".git", "__pycache__", "cache", ".cache", ".pytest_cache", ".mypy_cache", "tmp", "temp"} for segment in segments)
            or lowered.endswith(binary_suffixes)
            or "course-archive" in lowered
            or "downloads/" in lowered
            or "credential" in lowered
            or "token" in lowered
        ):
            forbidden.append(name)
        payload = path.read_bytes()
        if re.search(rb"zenodo_pat_[A-Za-z0-9_-]+", payload):
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
            or manifest.get("backend_record_count") != 1714
        ):
            raise RuntimeError("delta ZIP boundary/rights/status/model/backend gate failed")
        return {"entries": len(names), "manifest_entries_verified": len(entries), "integrity": "pass", "forbidden_entries": 0}


def build_bundle(lane_closure: dict[str, object]) -> tuple[Path, dict[str, object]]:
    pairs = bundle_inputs()
    entries = [{"path": name, "bytes": path.stat().st_size, "sha256": file_digest(path)} for name, path in pairs]
    inner = {
        "schema": "o015-mit-l06-delta-bundle-v1",
        "version": VERSION,
        "scope": "MIT 6.253 complete-notes Lecture 2, pages 20-28; compact semantic source, build, QA, backend, control, and license closure",
        "status": STATUS,
        "complete_corpus": False,
        "source_pages": SOURCE_PAGES,
        "next_source_page": NEXT_SOURCE_PAGE,
        "next_source_heading": "LECTURE 3 - LECTURE OUTLINE",
        "backend_record_count": 1714,
        "component_rights": COMPONENT_RIGHTS,
        "model_provenance": MODEL_ID,
        "human_native_speaker_review": False,
        "semantic_html_primary": True,
        "reader_pdf_tagged": False,
        "authority_pdf_bytes": 0,
        "source_image_bytes": 0,
        "lane_closure": lane_closure,
        "entry_count": len(entries),
        "entries": entries,
    }
    manifest_bytes = (json.dumps(inner, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    destination = HERE / BUNDLE_NAME
    with tempfile.NamedTemporaryFile(prefix=".mit-l06-delta-", suffix=".zip", dir=HERE, delete=False) as handle:
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
    if len(paths) != 6 or len({path.name for path in paths}) != 6:
        raise RuntimeError("expected six unique pre-manifest additions")
    return paths


def addition_paths() -> list[Path]:
    paths = addition_material_paths() + [HERE / MANIFEST_NAME, HERE / SUMS_NAME]
    if len(paths) != EXPECTED_ADDITION_COUNT or len({path.name for path in paths}) != EXPECTED_ADDITION_COUNT:
        raise RuntimeError("expected exactly eight unique additions")
    collisions = set(path.name for path in paths) & set(inherited_inventory())
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
        "admitted_boundary": "MIT 6.253 complete-notes Lecture 2, PDF pages 20-28, L06",
        "next_boundary": "MIT 6.253 complete-notes PDF page 29, Lecture 3",
        "backend_record_count": 1714,
        "component_rights": COMPONENT_RIGHTS,
        "rights_notice": "Rights are component-specific; no umbrella license replaces inherited component rights.",
        "human_native_speaker_review": False,
        "semantic_html_primary": True,
        "reader_pdf_tagged": False,
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
        or manifest.get("next_boundary") != "MIT 6.253 complete-notes PDF page 29, Lecture 3"
        or manifest.get("component_rights") != COMPONENT_RIGHTS
        or manifest.get("complete_corpus") is not False
        or manifest.get("status") != STATUS
        or manifest.get("model_provenance") != MODEL_ID
        or manifest.get("backend_record_count") != 1714
    ):
        raise RuntimeError("release manifest boundary/count/rights/status/model/backend gate failed")
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
    if checksum_inventory() != expected_checksums:
        raise RuntimeError("checksum inventory or byte identities differ")
    return {
        "result": "pass",
        "release_files": EXPECTED_RELEASE_COUNT,
        "inherited_files": EXPECTED_INHERITED_COUNT,
        "addition_files": EXPECTED_ADDITION_COUNT,
        "source_pages": SOURCE_PAGES,
        "next_source_page": NEXT_SOURCE_PAGE,
        "backend_record_count": 1714,
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


def build_all() -> dict[str, object]:
    HERE.mkdir(parents=True, exist_ok=True)
    validate_template()
    validate_release_docs()
    closure = validate_lane_closure()
    _, verification = build_bundle(closure)
    build_release_metadata(verification, closure)
    return validate_local_release()


def main() -> None:
    print(json.dumps(build_all(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
