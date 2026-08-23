#!/usr/bin/env python3
"""Build the deterministic additive MIT-L03 Zenodo checkpoint."""

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
PREVIOUS_READBACK = HERE.parent / "2026-08-23-mit-l02-correction" / "zenodo-public-readback-mit-l02-correction.json"
STATE_PATH = HERE / "zenodo-draft-mit-l03.json"
FIXED_ZIP_TIME = (2026, 8, 23, 0, 0, 0)

PARENT_RECORD_ID = "22071030"
PARENT_RECORD_DOI = "10.5281/zenodo.22071030"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.23-mit-l03"
BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.23_MIT_L03_DELTA.zip"
MANIFEST_NAME = "release-manifest-mit-l03.json"
SUMS_NAME = "SHA256SUMS-mit-l03"
EXPECTED_INHERITED_COUNT = 32
EXPECTED_ADDITION_COUNT = 8


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


def inherited_inventory() -> dict[str, dict[str, object]]:
    data = json.loads(PREVIOUS_READBACK.read_text(encoding="utf-8"))
    if str(data.get("record_id")) != PARENT_RECORD_ID or data.get("record_doi") != PARENT_RECORD_DOI or data.get("status") != "published":
        raise RuntimeError("prior public readback does not identify the required parent")
    result = {item["filename"]: {"filename": item["filename"], "bytes": item["bytes"], "sha256": item["sha256"]} for item in data.get("files", [])}
    if len(result) != EXPECTED_INHERITED_COUNT or data.get("file_count") != EXPECTED_INHERITED_COUNT:
        raise RuntimeError("prior public readback does not contain exactly 32 unique files")
    return result


BUNDLE_ROOT_PATHS = [
    "PROVENANCE.md",
    "README.md",
    "RIGHTS.md",
    "backend/backend_schema.json",
    "backend/records.jsonl",
    "backend/records.csv",
    "source/en/mit-02-duality-semantic-witness.md",
    "source/en/mit-03-modern-view-semantic-witness.md",
    "source/id-ID/mit-02-dualitas-dan-perilaku-pengecualian-id.md",
    "source/id-ID/mit-l02.css",
    "source/id-ID/mit-l02-preamble.tex",
    "source/id-ID/mit-l02-pdf-filter.lua",
    "source/id-ID/mit-l02-before-body.html",
    "source/id-ID/mit-l02-after-body.html",
    "source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md",
    "source/id-ID/mit-l03-preamble.tex",
    "source/id-ID/mit-l03-pdf-filter.lua",
    "source/id-ID/mit-l03-before-body.html",
    "source/id-ID/mit-l03-after-body.html",
    "qa/build_mit_l02.py",
    "qa/validate_mit_l02.py",
    "qa/MIT_L02_VALIDATION.json",
    "qa/MIT_L02_BROWSER_QA.json",
    "qa/MIT_L02_INDEPENDENT_REREVIEW.md",
    "qa/extend_backend_mit_l02.py",
    "qa/validate_backend_mit_l02.py",
    "qa/MIT_L02_BACKEND_VALIDATION.json",
    "qa/build_mit_l03.py",
    "qa/validate_mit_l03.py",
    "qa/MIT_L03_VALIDATION.json",
    "qa/MIT_L03_BROWSER_QA.json",
    "qa/MIT_L03_INDEPENDENT_REREVIEW.md",
    "00_control/ADVERSE_LEDGER.jsonl",
    "00_control/BUILD_AND_QA.md",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/CURRENT_CURSOR.md",
    "00_control/CURRENT_GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/DECISION_LOG.md",
    "00_control/INDONESIAN_TERMINOLOGY_QA_20260822.md",
    "00_control/MIT_ROYER_SOURCE_FREEZE.json",
    "00_control/PUBLICATION_RECEIPTS.md",
    "00_control/SOURCE_AUTHORITY.json",
    "authority/mit-ocw-6.253/official-pages/CC-BY-NC-SA-4.0-legalcode.txt",
    "authority/royer-stochastic-gradient/official-pages/CC-BY-NC-4.0-legalcode.txt",
    "authority/habring/CC-BY-4.0-legalcode.txt",
    "authority/penn-state/CC-BY-NC-SA-3.0-US-legalcode.html",
]
RELEASE_DOCS = ["README_MIT_L03.md", "README_RELEASE_MIT_L03.md", "RIGHTS_MIT_L03.md"]


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
    for name, path in pairs:
        lowered = name.lower()
        if any(token in lowered for token in ("/.git/", "__pycache__", "/cache/", "/temp/", "/tmp/", "credential", "token")) or lowered.endswith((".zip", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".mpl")) or "course-archive" in lowered or "downloads/" in lowered:
            forbidden.append(name)
        if b"zenodo_pat_" in path.read_bytes():
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
        if set(names) != {"DELTA_BUNDLE_MANIFEST.json", *(entry["path"] for entry in entries)}:
            raise RuntimeError("delta ZIP inventory differs from internal manifest")
        for entry in entries:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or digest_bytes(data) != entry["sha256"]:
                raise RuntimeError(f"delta ZIP hash mismatch: {entry['path']}")
        forbidden = [name for name in names if name.lower().endswith((".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".mpl"))]
        if forbidden:
            raise RuntimeError(f"binary authority payload leaked into delta ZIP: {forbidden}")
        return {"entries": len(names), "manifest_entries_verified": len(entries), "integrity": "pass", "forbidden_entries": 0}


def build_bundle() -> tuple[Path, dict[str, object]]:
    pairs = bundle_inputs()
    entries = [{"path": name, "bytes": path.stat().st_size, "sha256": file_digest(path)} for name, path in pairs]
    inner = {"schema": "o015-mit-l03-delta-bundle-v1", "version": VERSION, "scope": "MIT 6.253 complete-notes pages 6-14 plus compact source, rights, QA, and backend closure", "complete_corpus": False, "next_boundary": "MIT complete-notes page 15", "athena_figure_bytes": 0, "entries": entries}
    manifest_bytes = (json.dumps(inner, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    destination = HERE / BUNDLE_NAME
    with tempfile.NamedTemporaryFile(prefix=".mit-l03-delta-", suffix=".zip", dir=HERE, delete=False) as handle:
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
    paths = [ROOT / "output/pdf/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.pdf", ROOT / "output/html/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.html", HERE / BUNDLE_NAME, *(HERE / name for name in RELEASE_DOCS)]
    if len(paths) != 6 or len({path.name for path in paths}) != 6:
        raise RuntimeError("expected six unique pre-manifest additions")
    return paths


def addition_paths() -> list[Path]:
    paths = addition_material_paths() + [HERE / MANIFEST_NAME, HERE / SUMS_NAME]
    if len(paths) != EXPECTED_ADDITION_COUNT or len({path.name for path in paths}) != EXPECTED_ADDITION_COUNT:
        raise RuntimeError("expected eight additions")
    if set(path.name for path in paths) & set(inherited_inventory()):
        raise RuntimeError("new addition collides with inherited filename")
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing additive release files:\n" + "\n".join(missing))
    return paths


def draft_identity() -> tuple[str | None, str | None]:
    if not STATE_PATH.is_file():
        return None, None
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return str(data["draft_id"]), str(data["draft_doi"])


def build_release_metadata(bundle_verification: dict[str, object]) -> None:
    record_id, record_doi = draft_identity()
    material = [identity(path) for path in sorted(addition_material_paths(), key=lambda path: path.name)]
    manifest = {"schema": "o015-zenodo-additive-checkpoint-v1", "version": VERSION, "publication_date": "2026-08-23", "title": "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia", "complete_corpus": False, "parent_record_id": PARENT_RECORD_ID, "parent_record_doi": PARENT_RECORD_DOI, "zenodo_concept_id": CONCEPT_ID, "zenodo_concept_doi": CONCEPT_DOI, "zenodo_record_id": record_id, "zenodo_record_doi": record_doi, "release_file_count": EXPECTED_INHERITED_COUNT + EXPECTED_ADDITION_COUNT, "inherited_file_count": EXPECTED_INHERITED_COUNT, "addition_file_count": EXPECTED_ADDITION_COUNT, "addition_material_files": material, "generated_addition_files": [MANIFEST_NAME, SUMS_NAME], "delta_bundle_verification": bundle_verification, "admitted_boundary": "MIT 6.253 complete-notes PDF page 14, Modern View of Convex Optimization", "next_boundary": "MIT 6.253 complete-notes PDF page 15", "rights_notice": "Component-specific: new MIT-derived reader CC BY-NC-SA 4.0; inherited components retain their own rights.", "model_provenance": "OpenAI Codex gpt-5.6-sol, Ultra"}
    manifest_path = HERE / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    values = {name: item["sha256"] for name, item in inherited_inventory().items()}
    values.update({path.name: file_digest(path) for path in addition_material_paths()})
    values[MANIFEST_NAME] = file_digest(manifest_path)
    if len(values) != EXPECTED_INHERITED_COUNT + EXPECTED_ADDITION_COUNT - 1:
        raise RuntimeError("checksum inventory count mismatch")
    (HERE / SUMS_NAME).write_text("".join(f"{values[name]}  {name}\n" for name in sorted(values)), encoding="ascii", newline="\n")


def validate_local_release(require_draft_binding: bool = False) -> dict[str, object]:
    bundle_result = verify_bundle((HERE / BUNDLE_NAME).read_bytes())
    manifest = json.loads((HERE / MANIFEST_NAME).read_text(encoding="utf-8"))
    if manifest.get("release_file_count") != 40 or manifest.get("addition_file_count") != 8:
        raise RuntimeError("release manifest count gate failed")
    if require_draft_binding:
        record_id, record_doi = draft_identity()
        if manifest.get("zenodo_record_id") != record_id or manifest.get("zenodo_record_doi") != record_doi:
            raise RuntimeError("release manifest is not bound to prepared draft")
    checksum_map = {}
    for line in (HERE / SUMS_NAME).read_text(encoding="ascii").splitlines():
        expected, name = line.split("  ", 1)
        checksum_map[name] = expected
    expected_names = set(inherited_inventory()) | {path.name for path in addition_paths()} - {SUMS_NAME}
    if set(checksum_map) != expected_names:
        raise RuntimeError("checksum inventory differs")
    return {"result": "pass", "release_files": 40, "inherited_files": 32, "addition_files": 8, "delta_bundle": identity(HERE / BUNDLE_NAME), "delta_bundle_verification": bundle_result, "manifest": identity(HERE / MANIFEST_NAME), "checksums": identity(HERE / SUMS_NAME)}


def local_inventory() -> dict[str, dict[str, object]]:
    result = dict(inherited_inventory())
    for path in addition_paths():
        result[path.name] = identity(path)
    if len(result) != EXPECTED_INHERITED_COUNT + EXPECTED_ADDITION_COUNT:
        raise RuntimeError("local release inventory count mismatch")
    return result


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    _, verification = build_bundle()
    build_release_metadata(verification)
    print(json.dumps(validate_local_release(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
