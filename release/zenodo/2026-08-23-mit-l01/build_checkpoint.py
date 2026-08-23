#!/usr/bin/env python3
"""Build and validate the deterministic additive MIT-L01 Zenodo checkpoint."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = HERE.parent / "2026-08-22-10u"
PREVIOUS_READBACK = PREVIOUS / "zenodo-public-readback.json"
STATE_PATH = HERE / "zenodo-draft-mit-l01.json"
FIXED_ZIP_TIME = (2026, 8, 23, 0, 0, 0)

PARENT_RECORD_ID = "22060447"
PARENT_RECORD_DOI = "10.5281/zenodo.22060447"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.23-mit-l01"
BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.23_MIT_L01_DELTA.zip"
MANIFEST_NAME = "release-manifest-mit-l01.json"
SUMS_NAME = "SHA256SUMS-mit-l01"
EXPECTED_INHERITED_COUNT = 16
EXPECTED_ADDITION_COUNT = 8

OLD_PDF_NAMES = {
    "D90-HAB-03-subgradien-id.pdf",
    "D90-HAB-04-metode-subgradien-terproyeksi-id.pdf",
    "D90-HAB-05-metode-gradien-proksimal-id.pdf",
    "D90-HAB-06-akselerasi-id.pdf",
    "D90-HAB-07-dualitas-id.pdf",
    "D90-HAB-08-penurunan-gradien-stokastik-id.pdf",
    "D90-HAB-09-transportasi-optimal-id.pdf",
    "D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.pdf",
    "D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf",
    "D90-PENN-05-metode-newton-dan-koreksi-id.pdf",
}

PILOT_FIXED = {
    "output/html/D90-MIT-01-peran-kekonveksan-id.html": (20613, "fff4de952dd2cb208208e1cfb3bbc8fe8a64936ff5fdb532a23a92fb0dc6af8b"),
    "output/pdf/D90-MIT-01-peran-kekonveksan-id.pdf": (53370, "bd03912f9d3fe6dbe7376577c7ca6e7ab5aee007dd33b51669cde1792644df58"),
    "source/en/mit-01-role-of-convexity-semantic-witness.md": (5752, "a18aefa9e1ffa29d0a3cea21d0df34f05025cb7c2008ae57b5db44730c9d1f58"),
    "source/id-ID/mit-01-peran-kekonveksan-id.md": (8641, "2170dec12e707782c7677647f77ad8ee3360b282a8dbb9fb5620170106004bf3"),
    "qa/MIT_L01_PILOT_VALIDATION.json": (4167, "1e11642f8c1ab1ade013c4377f4dc0bc119ec0e89e6073eec787c7c341de0970"),
    "qa/MIT_L01_BROWSER_QA.json": (1757, "2d5c90b3343040c4ed3dfbdb3714737dfba8317d1781c1e5c27145f5afbbb76d"),
    "backend/records.jsonl": (1036556, "ebf44ca94323584e40b548ce36da560899e39a1e76ed2c993a0786b4ee7c4a2b"),
    "backend/records.csv": (1244072, "bc73abb3457cacc10423c1785a0db70a9007fdef8ac0a2be1de48d25d389fdf5"),
    "qa/extend_backend_mit_l01.py": (62794, "b206d3e64628ed8a98ba7a776bcc34c1d6bec19175ec59082950fe6d2e63cf79"),
    "qa/validate_backend_mit_l01.py": (39185, "be59f34bc8aa083f31a7f2a62a72aa20ab264167f6288d03b04247c8ef54d19e"),
}

BUNDLE_ROOT_PATHS = [
    "README.md",
    "RIGHTS.md",
    "PROVENANCE.md",
    "backend/backend_schema.json",
    "backend/records.jsonl",
    "backend/records.csv",
    "source/en/mit-01-role-of-convexity-semantic-witness.md",
    "source/id-ID/mit-01-peran-kekonveksan-id.md",
    "source/id-ID/mit-pilot.css",
    "source/id-ID/mit-pilot-preamble.tex",
    "source/id-ID/mit-pilot-pdf-filter.lua",
    "source/id-ID/mit-pilot-before-body.html",
    "source/id-ID/mit-pilot-after-body.html",
    "qa/build_mit_pilot.py",
    "qa/CHAPTER09_WORKLOG.md",
    "qa/validate_mit_pilot.py",
    "qa/MIT_L01_PILOT_VALIDATION.json",
    "qa/MIT_L01_BROWSER_QA.json",
    "qa/MIT_L01_INDEPENDENT_REREVIEW.md",
    "qa/freeze_mit_royer_authority.py",
    "qa/extend_backend_mit_l01.py",
    "qa/validate_backend_mit_l01.py",
    "00_control/ADVERSE_LEDGER.jsonl",
    "00_control/BUILD_AND_QA.md",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/CURRENT_CURSOR.md",
    "00_control/CURRENT_GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/DECISION_LOG.md",
    "00_control/INDONESIAN_TERMINOLOGY_QA_20260822.md",
    "00_control/MIT_L01_PILOT_AUDIT.md",
    "00_control/MIT_L02_BOUNDARY_CENSUS.md",
    "00_control/MIT_ROYER_SOURCE_AUDIT.md",
    "00_control/MIT_ROYER_SOURCE_FREEZE.json",
    "00_control/O015_PRIMARY_ARCHITECTURE_PIVOT_20260822.md",
    "00_control/PUBLICATION_RECEIPTS.md",
    "00_control/SOURCE_AUTHORITY.json",
    "authority/mit-ocw-6.253/official-pages/CC-BY-NC-SA-4.0-legalcode.txt",
    "authority/royer-stochastic-gradient/official-pages/CC-BY-NC-4.0-legalcode.txt",
    "authority/habring/CC-BY-4.0-legalcode.txt",
    "authority/penn-state/CC-BY-NC-SA-3.0-US-legalcode.html",
]

RELEASE_DOCS = [
    "README_RELEASE_MIT_L01.md",
    "README_MIT_L01.md",
    "RIGHTS_MIT_L01.md",
]


def digest_bytes(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def file_digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def identity(path: Path, filename: str | None = None) -> dict[str, object]:
    return {
        "filename": filename or path.name,
        "bytes": path.stat().st_size,
        "sha256": file_digest(path),
    }


def inherited_inventory() -> dict[str, dict[str, object]]:
    data = json.loads(PREVIOUS_READBACK.read_text(encoding="utf-8"))
    if (
        str(data.get("record_id")) != PARENT_RECORD_ID
        or data.get("record_doi") != PARENT_RECORD_DOI
        or data.get("concept_id") != CONCEPT_ID
        or data.get("status") != "published"
    ):
        raise RuntimeError("Prior public readback does not identify the required parent")
    entries = {
        item["filename"]: {
            "filename": item["filename"],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
        }
        for item in data.get("files", [])
    }
    if len(entries) != EXPECTED_INHERITED_COUNT or data.get("file_count") != EXPECTED_INHERITED_COUNT:
        raise RuntimeError("Prior public readback does not contain exactly sixteen unique files")
    return entries


def inherited_local_paths() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for name in inherited_inventory():
        result[name] = ROOT / "output" / "pdf" / name if name in OLD_PDF_NAMES else PREVIOUS / name
    return result


def verify_inherited_local() -> None:
    """Verify immutable prior-release files where the frozen release kept them.

    Reader PDFs live in mutable output paths and some have since been rebuilt.
    Their inherited authority is therefore the prior anonymous public-byte
    receipt, not the current working-tree PDF.  The publisher re-downloads and
    hashes all sixteen inherited draft/public objects before publication.
    """
    expected = inherited_inventory()
    for name, path in inherited_local_paths().items():
        if name in OLD_PDF_NAMES:
            continue
        if not path.is_file():
            raise FileNotFoundError(f"Missing frozen prior-release witness: {path}")
        actual = identity(path, name)
        if actual != expected[name]:
            raise RuntimeError(f"Inherited byte identity drift: {name}: {actual} != {expected[name]}")


def verify_fixed_pilot() -> None:
    for relative, expected in PILOT_FIXED.items():
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Missing fixed pilot artifact: {relative}")
        actual = (path.stat().st_size, file_digest(path))
        if actual != expected:
            raise RuntimeError(f"Fixed pilot artifact drift: {relative}: {actual} != {expected}")


def bundle_inputs() -> list[tuple[str, Path]]:
    pairs = [(relative, ROOT / relative) for relative in BUNDLE_ROOT_PATHS]
    pairs.extend((f"release-notes/{name}", HERE / name) for name in RELEASE_DOCS)
    pairs.sort(key=lambda item: item[0])
    if len({name for name, _ in pairs}) != len(pairs):
        raise RuntimeError("Duplicate delta ZIP entry name")
    missing = [f"{name}: {path}" for name, path in pairs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing delta ZIP inputs:\n" + "\n".join(missing))
    forbidden = []
    for name, path in pairs:
        lowered = name.lower()
        if (
            any(token in lowered for token in ("/.git/", "__pycache__", "/cache/", "/temp/", "/tmp/", "credential", "token"))
            or lowered.endswith((".zip", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".mpl"))
            or "course-archive" in lowered
            or "downloads/" in lowered
        ):
            forbidden.append(name)
        if b"zenodo_pat_" in path.read_bytes():
            forbidden.append(f"credential-shaped content: {name}")
    if forbidden:
        raise RuntimeError("Forbidden delta ZIP inputs:\n" + "\n".join(forbidden))
    return pairs


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def verify_bundle_bytes(payload: bytes) -> dict[str, object]:
    with zipfile.ZipFile(__import__("io").BytesIO(payload), "r") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"Delta ZIP integrity failure at {bad}")
        names = archive.namelist()
        if len(names) != len(set(names)) or "DELTA_BUNDLE_MANIFEST.json" not in names:
            raise RuntimeError("Delta ZIP uniqueness/manifest gate failed")
        manifest = json.loads(archive.read("DELTA_BUNDLE_MANIFEST.json"))
        entries = manifest.get("entries", [])
        if set(names) != {"DELTA_BUNDLE_MANIFEST.json", *(item["path"] for item in entries)}:
            raise RuntimeError("Delta ZIP inventory differs from its internal manifest")
        for item in entries:
            data = archive.read(item["path"])
            if len(data) != item["bytes"] or digest_bytes(data) != item["sha256"]:
                raise RuntimeError(f"Delta ZIP internal-manifest mismatch: {item['path']}")
        forbidden = [name for name in names if name.lower().endswith((".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".mpl"))]
        if forbidden:
            raise RuntimeError(f"Binary/bulk authority payload leaked into delta ZIP: {forbidden}")
        return {
            "entries": len(names),
            "manifest_entries_verified": len(entries),
            "integrity": "pass",
            "forbidden_entries": 0,
        }


def build_bundle() -> tuple[Path, dict[str, object]]:
    entries = []
    pairs = bundle_inputs()
    for name, path in pairs:
        entries.append({"path": name, "bytes": path.stat().st_size, "sha256": file_digest(path)})
    inner = {
        "schema": "o015-mit-l01-delta-bundle-v1",
        "version": VERSION,
        "scope": "MIT 6.253 complete-notes pages 2-5 plus compact authority, rights, QA, and backend closure",
        "complete_corpus": False,
        "next_boundary": "MIT complete-notes pages 6-13, Duality through Exceptional Behavior",
        "excluded_successor": "MIT complete-notes page 14, Modern View of Convex Optimization",
        "athena_figure_bytes": 0,
        "entries": entries,
    }
    manifest_bytes = (json.dumps(inner, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    destination = HERE / BUNDLE_NAME
    with tempfile.NamedTemporaryFile(prefix=".mit-l01-delta-", suffix=".zip", dir=HERE, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            add_bytes(archive, "DELTA_BUNDLE_MANIFEST.json", manifest_bytes)
            for name, path in pairs:
                add_bytes(archive, name, path.read_bytes())
        verification = verify_bundle_bytes(temporary.read_bytes())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination, verification


def addition_material_paths() -> list[Path]:
    paths = [
        ROOT / "output/html/D90-MIT-01-peran-kekonveksan-id.html",
        ROOT / "output/pdf/D90-MIT-01-peran-kekonveksan-id.pdf",
        HERE / BUNDLE_NAME,
        *(HERE / name for name in RELEASE_DOCS),
    ]
    if len(paths) != 6 or len({path.name for path in paths}) != 6:
        raise RuntimeError("Expected six unique pre-manifest additions")
    return paths


def addition_paths() -> list[Path]:
    paths = addition_material_paths() + [HERE / MANIFEST_NAME, HERE / SUMS_NAME]
    if len(paths) != EXPECTED_ADDITION_COUNT or len({path.name for path in paths}) != EXPECTED_ADDITION_COUNT:
        raise RuntimeError("Expected exactly eight collision-proof additions")
    if set(path.name for path in paths) & set(inherited_inventory()):
        raise RuntimeError("New addition collides with an inherited public filename")
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing additive release files:\n" + "\n".join(missing))
    return paths


def draft_identity() -> tuple[str | None, str | None]:
    if not STATE_PATH.is_file():
        return None, None
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return str(data["draft_id"]), str(data["draft_doi"])


def build_release_metadata(bundle_verification: dict[str, object]) -> None:
    inherited = [inherited_inventory()[name] for name in sorted(inherited_inventory())]
    material = [identity(path) for path in sorted(addition_material_paths(), key=lambda item: item.name)]
    record_id, record_doi = draft_identity()
    manifest = {
        "schema": "o015-zenodo-additive-checkpoint-v1",
        "version": VERSION,
        "publication_date": "2026-08-23",
        "title": "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia",
        "complete_corpus": False,
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "zenodo_concept_id": CONCEPT_ID,
        "zenodo_concept_doi": CONCEPT_DOI,
        "zenodo_record_id": record_id,
        "zenodo_record_doi": record_doi,
        "release_file_count": EXPECTED_INHERITED_COUNT + EXPECTED_ADDITION_COUNT,
        "inherited_file_count": EXPECTED_INHERITED_COUNT,
        "addition_file_count": EXPECTED_ADDITION_COUNT,
        "inherited_files": inherited,
        "addition_material_files": material,
        "generated_addition_files": [MANIFEST_NAME, SUMS_NAME],
        "delta_bundle_verification": bundle_verification,
        "admitted_boundary": "MIT 6.253 complete-notes PDF pages 2-5",
        "next_boundary": "MIT 6.253 complete-notes PDF pages 6-13, Duality through Exceptional Behavior",
        "excluded_successor": "MIT 6.253 complete-notes PDF page 14, Modern View of Convex Optimization",
        "rights_notice": (
            "Component-specific: new MIT-derived reader CC BY-NC-SA 4.0; inherited Habring-derived units CC BY 4.0; "
            "inherited Griffin/Penn-derived units CC BY-NC-SA 3.0 United States; Royer appears as a CC BY-NC 4.0 source-freeze component only."
        ),
        "model_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
    }
    manifest_path = HERE / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    checksum_values = {name: item["sha256"] for name, item in inherited_inventory().items()}
    checksum_values.update({path.name: file_digest(path) for path in addition_material_paths()})
    checksum_values[MANIFEST_NAME] = file_digest(manifest_path)
    if len(checksum_values) != 23:
        raise RuntimeError("Expected exactly 23 files in the non-self-referential checksum inventory")
    (HERE / SUMS_NAME).write_text(
        "".join(f"{checksum_values[name]}  {name}\n" for name in sorted(checksum_values)),
        encoding="ascii",
        newline="\n",
    )


def local_inventory() -> dict[str, dict[str, object]]:
    result = dict(inherited_inventory())
    for path in addition_paths():
        result[path.name] = identity(path)
    if len(result) != 24:
        raise RuntimeError("Expected exact 24-file additive inventory")
    return result


def validate_local_release(require_draft_binding: bool = False) -> dict[str, object]:
    verify_inherited_local()
    verify_fixed_pilot()
    bundle_result = verify_bundle_bytes((HERE / BUNDLE_NAME).read_bytes())
    manifest = json.loads((HERE / MANIFEST_NAME).read_text(encoding="utf-8"))
    if manifest.get("inherited_files") != [inherited_inventory()[name] for name in sorted(inherited_inventory())]:
        raise RuntimeError("Release manifest inherited identity drift")
    if manifest.get("release_file_count") != 24 or manifest.get("addition_file_count") != 8:
        raise RuntimeError("Release manifest count gate failed")
    if require_draft_binding:
        record_id, record_doi = draft_identity()
        if manifest.get("zenodo_record_id") != record_id or manifest.get("zenodo_record_doi") != record_doi:
            raise RuntimeError("Release manifest is not bound to the prepared draft; rerun build_checkpoint.py")
    checksum_lines = (HERE / SUMS_NAME).read_text(encoding="ascii").splitlines()
    checksum_map = {}
    for line in checksum_lines:
        expected_hash, name = line.split("  ", 1)
        if name in checksum_map:
            raise RuntimeError(f"Duplicate checksum filename: {name}")
        checksum_map[name] = expected_hash
    inventory = local_inventory()
    if set(checksum_map) != set(inventory) - {SUMS_NAME} or len(checksum_map) != 23:
        raise RuntimeError("SHA256SUMS-mit-l01 inventory gate failed")
    for name, expected_hash in checksum_map.items():
        actual_hash = (
            inherited_inventory()[name]["sha256"]
            if name in inherited_inventory()
            else file_digest(next(path for path in addition_paths() if path.name == name))
        )
        if actual_hash != expected_hash:
            raise RuntimeError(f"SHA256SUMS-mit-l01 mismatch: {name}")
    template = json.loads((HERE / "zenodo-record-mit-l01.json").read_text(encoding="utf-8"))["metadata"]
    serialized = json.dumps(template, ensure_ascii=False)
    if "TTP" in template["title"] or "TTP" in template["description"] or serialized.count("TTP") != 1:
        raise RuntimeError("Zenodo metadata TTP placement gate failed")
    if serialized.count("OpenAI Codex gpt-5.6-sol, Ultra") != 1:
        raise RuntimeError("Exact model provenance gate failed")
    return {
        "result": "pass",
        "release_files": len(inventory),
        "inherited_files": EXPECTED_INHERITED_COUNT,
        "addition_files": EXPECTED_ADDITION_COUNT,
        "delta_bundle": identity(HERE / BUNDLE_NAME),
        "delta_bundle_verification": bundle_result,
        "manifest": identity(HERE / MANIFEST_NAME),
        "checksums": identity(HERE / SUMS_NAME),
    }


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    verify_inherited_local()
    verify_fixed_pilot()
    _, bundle_verification = build_bundle()
    build_release_metadata(bundle_verification)
    print(json.dumps(validate_local_release(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
