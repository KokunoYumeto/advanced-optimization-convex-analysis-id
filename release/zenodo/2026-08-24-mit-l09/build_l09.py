#!/usr/bin/env python3
"""Build and verify the deterministic additive MIT-L09 preservation delta.

The builder is local and performs no network, credential, Git, publication, or
mutable-control operation.  It inherits exactly the 74 files proved by the L08
public readback and adds exactly eight collision-free L09 filenames.  It fails
before writing a bundle until ``release-config-mit-l09.json`` supplies final
backend and pre-publication control identities.
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

import generate_input_lock_l09 as lockgen


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS_READBACK = HERE.parent / "2026-08-24-mit-l08" / "zenodo-public-readback-mit-l08.json"
TEMPLATE_PATH = HERE / "zenodo-record-mit-l09.json"
INPUT_LOCK_PATH = HERE / "release-input-lock-mit-l09.json"
STATE_PATH = HERE / "zenodo-draft-mit-l09.json"
FIXED_ZIP_TIME = (2026, 8, 24, 0, 0, 0)

PARENT_RECORD_ID = "22074528"
PARENT_RECORD_DOI = "10.5281/zenodo.22074528"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.24-mit-l09-p50-63"
MODEL_ID = "OpenAI Codex gpt-5.6-sol, Ultra"
FORBIDDEN_ORG_EXPANSION = "Translation and Transcription Project"
STATUS = "partial"
SOURCE_PAGES = list(range(50, 64))
NEXT_SOURCE_PAGE = 64
NEXT_SOURCE_HEADING = "LECTURE 6 - LECTURE OUTLINE"

BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.24_MIT_L09_DELTA.zip"
MANIFEST_NAME = "release-manifest-mit-l09.json"
SUMS_NAME = "SHA256SUMS-mit-l09"
EXPECTED_INHERITED_COUNT = 74
EXPECTED_ADDITION_COUNT = 8
EXPECTED_RELEASE_COUNT = 82

READER_PATHS = [
    ROOT / "output/pdf/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.pdf",
    ROOT / "output/html/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.html",
]
RELEASE_DOCS = ["README_MIT_L09.md", "README_RELEASE_MIT_L09.md", "LICENSE_MIT_L09.md"]

BUNDLE_ROOT_PATHS = [
    "backend/backend_schema.json",
    "backend/records.jsonl",
    "backend/records.csv",
    "source/en/mit-09-lecture-5-recession-minima-semantic-witness.md",
    "source/id-ID/mit-09-kuliah-5-resesi-dan-minimum-id.md",
    "source/id-ID/mit-l09.css",
    "source/id-ID/mit-l09-preamble.tex",
    "source/id-ID/mit-l09-pdf-filter.lua",
    "source/id-ID/mit-l09-before-body.html",
    "source/id-ID/mit-l09-after-body.html",
    "qa/build_mit_l09.py",
    "qa/validate_mit_l09.py",
    "qa/MIT_L09_VALIDATION.json",
    "qa/MIT_L09_BROWSER_QA.json",
    "qa/MIT_L09_VISUAL_QA.json",
    "qa/MIT_L09_INDEPENDENT_REREVIEW.md",
    "qa/extend_backend_mit_l09.py",
    "qa/validate_backend_mit_l09.py",
    "qa/MIT_L09_BACKEND_VALIDATION.json",
    "00_control/MIT_L09_LECTURE_5_BOUNDARY_CENSUS.md",
    "00_control/MIT_L09_CORRECTION_SNAPSHOT.jsonl",
    "authority/mit-ocw-6.253/official-pages/CC-BY-NC-SA-4.0-legalcode.txt",
]

COMPONENT_RIGHTS = {
    "new_mit_reader_semantic_source_and_adaptation": "CC BY-NC-SA 4.0",
    "new_project_build_qa_backend_and_boundary_evidence": "project-local tooling and evidence; no blanket reuse grant asserted",
    "athena_scientific_graphics": "permission-only; zero source graphic bytes or layouts redistributed",
    "inherited_habring_components": "CC BY 4.0",
    "inherited_griffin_penn_components": "CC BY-NC-SA 3.0 United States",
    "inherited_royer_source_freeze": "CC BY-NC 4.0",
}


def controls_may_have_advanced() -> bool:
    """Allow post-publication control appendages without weakening draft gates."""
    if not STATE_PATH.is_file():
        return False
    state = read_json(STATE_PATH)
    if state.get("status") != "published":
        return False
    if (
        state.get("schema") != "o015-zenodo-mit-l09-draft-receipt-v1"
        or state.get("parent_record_id") != PARENT_RECORD_ID
        or state.get("parent_record_doi") != PARENT_RECORD_DOI
        or state.get("concept_id") != CONCEPT_ID
        or state.get("concept_doi") != CONCEPT_DOI
        or state.get("version") != VERSION
    ):
        raise RuntimeError("published-state receipt belongs to a different lineage/version")
    return True


def config() -> dict:
    return lockgen.load_config(verify_live_controls=not controls_may_have_advanced())


def backend_counts() -> tuple[int, int, int]:
    values = config()["backend"]
    return values["protected_record_count"], values["new_record_count"], values["record_count"]


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
        raise RuntimeError(f"{label} differs from its frozen identity: {path}")


def inherited_inventory() -> dict[str, dict[str, object]]:
    data = read_json(PREVIOUS_READBACK)
    if (
        str(data.get("record_id")) != PARENT_RECORD_ID
        or data.get("record_doi") != PARENT_RECORD_DOI
        or str(data.get("concept_id")) != CONCEPT_ID
        or data.get("concept_doi") != CONCEPT_DOI
        or data.get("status") != "published"
    ):
        raise RuntimeError("frozen readback does not identify the published L08 parent")
    items = data.get("files", [])
    result = {
        item["filename"]: {"filename": item["filename"], "bytes": item["bytes"], "sha256": item["sha256"]}
        for item in items
    }
    if (
        len(items) != EXPECTED_INHERITED_COUNT
        or len(result) != EXPECTED_INHERITED_COUNT
        or data.get("file_count") != EXPECTED_INHERITED_COUNT
        or data.get("inherited_identity") != "pass"
        or any(item.get("public_byte_identity") != "pass" for item in items)
    ):
        raise RuntimeError("L08 readback does not prove exactly 74 unique public parent files")
    return result


def validate_template() -> dict:
    template = read_json(TEMPLATE_PATH)
    metadata = template.get("metadata", {})
    if template.get("files", {}).get("default_preview") != READER_PATHS[0].name:
        raise RuntimeError("metadata template must make the L09 PDF the default preview")
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
    ):
        raise RuntimeError("metadata permits only one short organizational TTP contributor")
    if metadata.get("version") != VERSION or serialized.count(MODEL_ID) != 1:
        raise RuntimeError("metadata version/model provenance gate failed")
    lowered = description.lower()
    for required in (
        "halaman 50-63",
        "halaman 64",
        "belum lengkap",
        "74 berkas induk",
        "tepat delapan berkas",
        "cc by-nc-sa 4.0",
        "tujuh blok relasi gambar",
        "o015-mit-sem-0019",
    ):
        if required not in lowered:
            raise RuntimeError(f"metadata description lacks {required!r}")
    return metadata


def validate_release_docs() -> None:
    combined = "\n".join((HERE / name).read_text(encoding="utf-8") for name in RELEASE_DOCS)
    if "TTP" in combined or FORBIDDEN_ORG_EXPANSION.casefold() in combined.casefold():
        raise RuntimeError("release documents must not add an organization label or expansion")
    lowered = combined.lower()
    for required in (
        "halaman 50",
        "halaman 64",
        "belum lengkap",
        "cc by-nc-sa 4.0",
        "athena",
        "74 berkas",
        "delapan tambahan",
    ):
        if required not in lowered:
            raise RuntimeError(f"release documents lack {required!r}")


def validate_input_lock() -> dict:
    cfg = config()
    protected, new, final = backend_counts()
    lock = read_json(INPUT_LOCK_PATH)
    expected_paths = set(lockgen.MATERIAL_PATHS + lockgen.CONTROL_PATHS)
    if (
        lock.get("schema") != "o015-mit-l09-release-input-lock-v1"
        or lock.get("boundary", {}).get("source_pages") != SOURCE_PAGES
        or lock.get("boundary", {}).get("next_source_page") != NEXT_SOURCE_PAGE
        or lock.get("boundary", {}).get("next_source_heading") != NEXT_SOURCE_HEADING
        or lock.get("backend_record_count") != final
        or lock.get("protected_backend_record_count") != protected
        or lock.get("new_backend_record_count") != new
        or lock.get("material_file_count") != len(lockgen.MATERIAL_PATHS)
        or lock.get("control_file_count") != len(lockgen.CONTROL_PATHS)
    ):
        raise RuntimeError("L09 input lock has a different boundary, count, or backend transition")
    files = lock.get("files", {})
    if not isinstance(files, dict) or set(files) != expected_paths:
        raise RuntimeError("L09 input lock does not bind the exact material/control closure")
    advanced_controls = controls_may_have_advanced()
    for relative, expected in files.items():
        if advanced_controls and relative in lockgen.CONTROL_PATHS:
            continue
        require_identity(ROOT / relative, expected, f"input lock {relative}")
    if cfg["backend"]["jsonl"] != files["backend/records.jsonl"]:
        raise RuntimeError("config and lock disagree on backend JSONL")
    if cfg["backend"]["csv"] != files["backend/records.csv"]:
        raise RuntimeError("config and lock disagree on backend CSV")
    if cfg["backend"]["validation"] != files["qa/MIT_L09_BACKEND_VALIDATION.json"]:
        raise RuntimeError("config and lock disagree on backend validation")
    for relative in lockgen.CONTROL_PATHS:
        if cfg["controls"][relative] != files[relative]:
            raise RuntimeError(f"config and lock disagree on control {relative}")
    return lock


def validate_lane_closure() -> dict[str, object]:
    lock = validate_input_lock()
    files = lock["files"]
    protected, new, final = backend_counts()
    content = read_json(ROOT / "qa/MIT_L09_VALIDATION.json")
    browser = read_json(ROOT / "qa/MIT_L09_BROWSER_QA.json")
    visual = read_json(ROOT / "qa/MIT_L09_VISUAL_QA.json")
    backend = read_json(ROOT / "qa/MIT_L09_BACKEND_VALIDATION.json")
    rereview_path = ROOT / "qa/MIT_L09_INDEPENDENT_REREVIEW.md"
    rereview = rereview_path.read_text(encoding="utf-8")
    boundary = content.get("boundary", {})
    if (
        content.get("schema") != "o015-mit-l09-validation-v1"
        or content.get("result") != "pass"
        or content.get("errors") != []
        or content.get("release_ready") is not True
        or content.get("model_identification") != MODEL_ID
        or boundary.get("source_pdf_pages") != SOURCE_PAGES
        or boundary.get("next_source_page") != NEXT_SOURCE_PAGE
        or boundary.get("next_heading") != NEXT_SOURCE_HEADING
        or boundary.get("copied_source_graphics") != 0
        or boundary.get("source_items") != 41
        or boundary.get("nested_items") != 17
        or boundary.get("source_displays") != 19
        or boundary.get("source_figures") != 7
        or boundary.get("source_figure_panels") != 12
        or boundary.get("examples") != 2
        or any(boundary.get(key) != 0 for key in ("exercises", "hints", "answers", "solutions", "code_surfaces", "interactive_surfaces"))
        or content.get("human_native_speaker_review") is not False
        or content.get("pdf", {}).get("searchable") is not True
        or content.get("pdf", {}).get("tagged") is not False
        or content.get("rights", {}).get("license") != "CC BY-NC-SA 4.0"
        or content.get("rights", {}).get("athena_source_figure_blocks_omitted") != 7
        or content.get("rights", {}).get("athena_source_figure_panels_omitted") != 12
    ):
        raise RuntimeError("final L09 content validation closure failed")

    html_relative = READER_PATHS[1].relative_to(ROOT).as_posix()
    pdf_relative = READER_PATHS[0].relative_to(ROOT).as_posix()
    canonical = content.get("build", {}).get("canonical", {})
    if (
        canonical.get("status") != "bound"
        or canonical.get("html", {}).get("sha256") != files[html_relative]["sha256"]
        or canonical.get("pdf", {}).get("sha256") != files[pdf_relative]["sha256"]
        or content.get("build", {}).get("deterministic_rebuilds") != 2
        or content.get("formula_inventory", {}).get("witness_display_blocks") != 19
        or content.get("formula_inventory", {}).get("target_display_blocks") != 19
    ):
        raise RuntimeError("L09 deterministic reader/formula closure failed")
    for item in content.get("files", []):
        relative = item.get("path")
        if not relative:
            raise RuntimeError("content receipt contains an unbound file identity")
        require_identity(ROOT / relative, item, f"content receipt {relative}")

    html_lock = files[html_relative]
    pdf_lock = files[pdf_relative]
    if (
        browser.get("result") != "pass"
        or browser.get("html", {}).get("path") != html_relative
        or browser.get("html", {}).get("bytes") != html_lock["bytes"]
        or browser.get("html", {}).get("sha256") != html_lock["sha256"]
        or browser.get("desktop", {}).get("horizontal_overflow") != 0
        or browser.get("mobile", {}).get("horizontal_overflow") != 0
        or browser.get("desktop", {}).get("uncontained_math_overflow") != 0
        or browser.get("mobile", {}).get("uncontained_math_overflow") != 0
        or browser.get("desktop", {}).get("console_warnings_or_errors") != 0
        or browser.get("mobile", {}).get("console_warnings_or_errors") != 0
    ):
        raise RuntimeError("final L09 browser validation closure failed")
    if (
        visual.get("result") != "pass"
        or visual.get("pdf", {}).get("path") != pdf_relative
        or visual.get("pdf", {}).get("bytes") != pdf_lock["bytes"]
        or visual.get("pdf", {}).get("sha256") != pdf_lock["sha256"]
        or visual.get("pdf", {}).get("pages") != 7
        or visual.get("render", {}).get("all_pages_inspected") is not True
        or any(value != 0 for value in visual.get("defects", {}).values())
    ):
        raise RuntimeError("final L09 visual validation closure failed")

    witness_relative = "source/en/mit-09-lecture-5-recession-minima-semantic-witness.md"
    target_relative = "source/id-ID/mit-09-kuliah-5-resesi-dan-minimum-id.md"
    if (
        not re.search(r"P1\s*=\s*0\s*,\s*P2\s*=\s*0\s*,\s*P3\s*=\s*0", rereview)
        or files[witness_relative]["sha256"] not in rereview
        or files[target_relative]["sha256"] not in rereview
    ):
        raise RuntimeError("independent rereview does not bind a clean L09 disposition")

    expected_segments = [f"d90.mit.ocw-6.253.l09.p{page:03d}" for page in SOURCE_PAGES]
    if (
        backend.get("schema") != "o015-mit-l09-backend-validation-v1"
        or backend.get("result") != "pass"
        or backend.get("errors") != []
        or backend.get("final_backend", {}).get("record_count") != final
        or backend.get("admission", {}).get("new_record_count") != new
        or backend.get("admission", {}).get("expected_new_record_count") != new
        or backend.get("protected_baseline", {}).get("record_count") != protected
        or backend.get("protected_baseline", {}).get("raw_reconstruction_passed") is not True
        or backend.get("admission", {}).get("segment_ids") != expected_segments
        or backend.get("final_backend", {}).get("csv_projection_lossless") is not True
        or backend.get("final_backend", {}).get("references_closed") is not True
        or backend.get("independent_validation_runs_required") != 2
    ):
        raise RuntimeError("final L09 backend validation closure failed")
    for kind, relative in (("jsonl", "backend/records.jsonl"), ("csv", "backend/records.csv")):
        observed = backend.get("final_backend", {}).get(kind, {})
        expected = files[relative]
        if observed.get("bytes") != expected["bytes"] or observed.get("sha256") != expected["sha256"]:
            raise RuntimeError(f"backend receipt and release lock disagree for {kind}")
    correction = backend.get("correction_snapshot", {})
    correction_lock = files["00_control/MIT_L09_CORRECTION_SNAPSHOT.jsonl"]
    if correction.get("bytes") != correction_lock["bytes"] or correction.get("sha256") != correction_lock["sha256"]:
        raise RuntimeError("backend receipt and correction snapshot identity differ")

    controls = {
        relative: files[relative]
        for relative in sorted(lockgen.CONTROL_PATHS)
    }
    return {
        "result": "pass",
        "source_pages": SOURCE_PAGES,
        "next_source_page": NEXT_SOURCE_PAGE,
        "content_validation": identity(ROOT / "qa/MIT_L09_VALIDATION.json"),
        "browser_validation": identity(ROOT / "qa/MIT_L09_BROWSER_QA.json"),
        "visual_validation": identity(ROOT / "qa/MIT_L09_VISUAL_QA.json"),
        "independent_rereview": identity(rereview_path),
        "backend_validation": identity(ROOT / "qa/MIT_L09_BACKEND_VALIDATION.json"),
        "backend": {
            "record_count": final,
            "protected_record_count": protected,
            "new_record_count": new,
            "jsonl": identity(ROOT / "backend/records.jsonl"),
            "csv": identity(ROOT / "backend/records.csv"),
        },
        "control_bindings": controls,
        "input_lock": identity(INPUT_LOCK_PATH),
        "human_native_speaker_review": False,
        "reader_pdf_tagged": False,
        "athena_source_graphic_bytes": 0,
        "mutable_global_control_files_in_bundle": 0,
    }


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def bundle_inputs() -> list[tuple[str, Path]]:
    pairs = [(relative, ROOT / relative) for relative in BUNDLE_ROOT_PATHS]
    pairs.extend((f"release-notes/{name}", HERE / name) for name in RELEASE_DOCS)
    pairs.append(("release-notes/release-input-lock-mit-l09.json", INPUT_LOCK_PATH))
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
        if re.search(rb"zenodo_pat_[A-Za-z0-9_-]+", path.read_bytes()):
            forbidden.append(f"credential-shaped content: {name}")
    if forbidden:
        raise RuntimeError("forbidden bundle inputs:\n" + "\n".join(forbidden))
    return pairs


def verify_bundle(payload: bytes) -> dict[str, object]:
    protected, new, final = backend_counts()
    live_inputs = {name: path.read_bytes() for name, path in bundle_inputs()}
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
        if {entry["path"] for entry in entries} != set(live_inputs):
            raise RuntimeError("delta ZIP payload differs from the live input closure")
        for entry in entries:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or digest_bytes(data) != entry["sha256"]:
                raise RuntimeError(f"delta ZIP hash mismatch: {entry['path']}")
            if data != live_inputs[entry["path"]]:
                raise RuntimeError(f"delta ZIP payload differs from live input: {entry['path']}")
            if re.search(rb"zenodo_pat_[A-Za-z0-9_-]+", data):
                raise RuntimeError(f"credential-shaped content in delta ZIP: {entry['path']}")
        forbidden = [name for name in names if name.lower().endswith((".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"))]
        if forbidden:
            raise RuntimeError(f"binary authority/image/archive payload leaked into delta ZIP: {forbidden}")
        permitted_controls = {
            "00_control/MIT_L09_LECTURE_5_BOUNDARY_CENSUS.md",
            "00_control/MIT_L09_CORRECTION_SNAPSHOT.jsonl",
        }
        if any(name.startswith("00_control/") and name not in permitted_controls for name in names):
            raise RuntimeError("mutable global control file leaked into delta ZIP")
        if (
            manifest.get("source_pages") != SOURCE_PAGES
            or manifest.get("next_source_page") != NEXT_SOURCE_PAGE
            or manifest.get("complete_corpus") is not False
            or manifest.get("status") != STATUS
            or manifest.get("component_rights") != COMPONENT_RIGHTS
            or manifest.get("model_provenance") != MODEL_ID
            or manifest.get("authority_pdf_bytes") != 0
            or manifest.get("source_image_bytes") != 0
            or manifest.get("backend_record_count") != final
            or manifest.get("protected_backend_record_count") != protected
            or manifest.get("new_backend_record_count") != new
            or manifest.get("mutable_global_control_files") != 0
        ):
            raise RuntimeError("delta ZIP boundary/rights/status/model/backend gate failed")
        return {
            "entries": len(names),
            "manifest_entries_verified": len(entries),
            "integrity": "pass",
            "forbidden_entries": 0,
            "mutable_global_control_files": 0,
        }


def build_bundle(lane_closure: dict[str, object]) -> tuple[Path, dict[str, object]]:
    protected, new, final = backend_counts()
    pairs = bundle_inputs()
    entries = [{"path": name, "bytes": path.stat().st_size, "sha256": file_digest(path)} for name, path in pairs]
    inner = {
        "schema": "o015-mit-l09-delta-bundle-v1",
        "version": VERSION,
        "scope": "MIT 6.253 complete-notes Lecture 5, pages 50-63; compact semantic source, build, QA, backend, boundary evidence, and license closure",
        "status": STATUS,
        "complete_corpus": False,
        "source_pages": SOURCE_PAGES,
        "next_source_page": NEXT_SOURCE_PAGE,
        "next_source_heading": NEXT_SOURCE_HEADING,
        "backend_record_count": final,
        "protected_backend_record_count": protected,
        "new_backend_record_count": new,
        "component_rights": COMPONENT_RIGHTS,
        "model_provenance": MODEL_ID,
        "human_native_speaker_review": False,
        "semantic_html_primary": True,
        "reader_pdf_tagged": False,
        "authority_pdf_bytes": 0,
        "source_image_bytes": 0,
        "mutable_global_control_files": 0,
        "lane_closure": lane_closure,
        "entry_count": len(entries),
        "entries": entries,
    }
    manifest_bytes = (json.dumps(inner, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    destination = HERE / BUNDLE_NAME
    with tempfile.NamedTemporaryFile(prefix=".mit-l09-delta-", suffix=".zip", dir=HERE, delete=False) as handle:
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
    collisions = {path.name for path in paths} & set(inherited_inventory())
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
    if (
        data.get("schema") != "o015-zenodo-mit-l09-draft-receipt-v1"
        or data.get("parent_record_id") != PARENT_RECORD_ID
        or data.get("concept_id") != CONCEPT_ID
        or data.get("version") != VERSION
    ):
        raise RuntimeError("local draft receipt belongs to a different L09 lineage/version")
    return str(data["draft_id"]), str(data["draft_doi"])


def build_release_metadata(bundle_verification: dict[str, object], lane_closure: dict[str, object]) -> None:
    protected, new, final = backend_counts()
    record_id, record_doi = draft_identity()
    material = [identity(path) for path in sorted(addition_material_paths(), key=lambda path: path.name)]
    manifest = {
        "schema": "o015-zenodo-additive-checkpoint-v1",
        "version": VERSION,
        "publication_date": "2026-08-24",
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
        "admitted_boundary": "MIT 6.253 complete-notes Lecture 5, PDF pages 50-63, L09",
        "next_boundary": "MIT 6.253 complete-notes PDF page 64, Lecture 6",
        "backend_record_count": final,
        "protected_backend_record_count": protected,
        "new_backend_record_count": new,
        "component_rights": COMPONENT_RIGHTS,
        "rights_notice": "Rights are component-specific; no umbrella license replaces inherited component rights.",
        "human_native_speaker_review": False,
        "semantic_html_primary": True,
        "reader_pdf_tagged": False,
        "model_provenance": MODEL_ID,
        "metadata_template": identity(TEMPLATE_PATH),
        "default_preview": READER_PATHS[0].name,
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
    protected, new, final = backend_counts()
    manifest = read_json(HERE / MANIFEST_NAME)
    if (
        manifest.get("release_file_count") != EXPECTED_RELEASE_COUNT
        or manifest.get("inherited_file_count") != EXPECTED_INHERITED_COUNT
        or manifest.get("addition_file_count") != EXPECTED_ADDITION_COUNT
        or manifest.get("admitted_source_pages") != SOURCE_PAGES
        or manifest.get("next_boundary") != "MIT 6.253 complete-notes PDF page 64, Lecture 6"
        or manifest.get("component_rights") != COMPONENT_RIGHTS
        or manifest.get("complete_corpus") is not False
        or manifest.get("status") != STATUS
        or manifest.get("model_provenance") != MODEL_ID
        or manifest.get("backend_record_count") != final
        or manifest.get("protected_backend_record_count") != protected
        or manifest.get("new_backend_record_count") != new
        or manifest.get("default_preview") != READER_PATHS[0].name
    ):
        raise RuntimeError("release manifest boundary/count/rights/status/model/backend gate failed")
    expected_material = [identity(path) for path in sorted(addition_material_paths(), key=lambda path: path.name)]
    if manifest.get("addition_material_files") != expected_material:
        raise RuntimeError("release manifest material identities differ")
    if manifest.get("lane_closure") != lane_closure or manifest.get("delta_bundle_verification") != bundle_result:
        raise RuntimeError("release manifest QA/bundle closure differs")
    if require_draft_binding:
        record_id, record_doi = draft_identity()
        if not record_id or not record_doi:
            raise RuntimeError("release manifest cannot bind an absent prepared draft")
        if manifest.get("zenodo_record_id") != record_id or manifest.get("zenodo_record_doi") != record_doi:
            raise RuntimeError("release manifest is not bound to the prepared L09 draft")
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
        "backend_record_count": final,
        "status": STATUS,
        "model_provenance": MODEL_ID,
        "default_preview": READER_PATHS[0].name,
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
