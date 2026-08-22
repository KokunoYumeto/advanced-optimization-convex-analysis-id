#!/usr/bin/env python3
"""Build the deterministic nine-unit Zenodo checkpoint bundle and manifests."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIXED_ZIP_TIME = (2026, 8, 22, 0, 0, 0)
BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.22.zip"

PDF_NAMES = [
    "D90-HAB-03-subgradien-id.pdf",
    "D90-HAB-04-metode-subgradien-terproyeksi-id.pdf",
    "D90-HAB-05-metode-gradien-proksimal-id.pdf",
    "D90-HAB-06-akselerasi-id.pdf",
    "D90-HAB-07-dualitas-id.pdf",
    "D90-HAB-08-penurunan-gradien-stokastik-id.pdf",
    "D90-HAB-09-transportasi-optimal-id.pdf",
    "D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.pdf",
    "D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf",
]

SOURCE_FILES = [
    "D90-HAB-03-subgradien-id.tex",
    "D90-HAB-04-metode-subgradien-terproyeksi-id.tex",
    "D90-HAB-05-metode-gradien-proksimal-id.tex",
    "D90-HAB-06-akselerasi-id.tex",
    "D90-HAB-07-dualitas-id.tex",
    "D90-HAB-08-penurunan-gradien-stokastik-id.tex",
    "D90-HAB-09-transportasi-optimal-id.tex",
    "D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.tex",
    "D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex",
    "habring-03-subgradien-id.tex",
    "habring-04-metode-subgradien-terproyeksi-id.tex",
    "habring-05-metode-gradien-proksimal-id.tex",
    "habring-06-akselerasi-id.tex",
    "habring-07-dualitas-id.tex",
    "habring-08-penurunan-gradien-stokastik-id.tex",
    "habring-09-transportasi-optimal-id.tex",
    "penn-03-pendakian-gradien-dan-pencarian-garis-id.tex",
    "penn-04-pencarian-garis-hampiran-dan-konvergensi-id.tex",
    "macros-id.tex",
    "shinybook.cls",
    "references-ot-id.bib",
    "references-penn-ch03-id.bbl",
    "references-penn-ch04-id.bbl",
]

HABRING_FIGURES = ["gradient.png", "subgradient.png"]
PENN_FIGURES = [
    "ConvergenceFailure.pdf",
    "DichotomousSearch.pdf",
    "GoldenRatioProof.pdf",
    "GoldenSectionFail.pdf",
    "GradientAscentOut.pdf",
    "NonConcave.pdf",
    "ThreeDCos.pdf",
    "WolfeConditionsIllustrated.pdf",
    "WolfePhiOfT.pdf",
]

STATIC_PATHS = [
    "README.md",
    "RIGHTS.md",
    "backend/backend_schema.json",
    "backend/records.jsonl",
    "backend/records.csv",
    "authority/habring/source-v1/references.bib",
    "authority/habring/CC-BY-4.0-legalcode.txt",
    "authority/penn-state/CC-BY-NC-SA-3.0-US-legalcode.html",
]

CONTROL_FILES = [
    "ADVERSE_LEDGER.jsonl",
    "BUILD_AND_QA.md",
    "CHAPTER05_SOURCE_AUDIT.md",
    "CHAPTER06_SOURCE_AUDIT.md",
    "CHAPTER07_SOURCE_AUDIT.md",
    "CHAPTER08_SOURCE_AUDIT.md",
    "CHAPTER09_SOURCE_AUDIT.md",
    "COMPONENT_RIGHTS.csv",
    "COVERAGE_OVERLAP.md",
    "CURRENT_CURSOR.md",
    "CURRENT_GOAL_AND_WORKFLOW.md",
    "CURRENT_STATE.md",
    "DECISION_LOG.md",
    "PENN_CH03_SOURCE_AUDIT.md",
    "PENN_CH04_SOURCE_AUDIT.md",
    "PUBLICATION_RECEIPTS.md",
    "SOURCE_AUTHORITY.json",
]

# This allow-list is deliberately limited to the nine admitted units.  In
# particular, Penn Chapter 5 and later candidate evidence must not leak into
# this checkpoint merely because production continues while the bundle builds.
QA_ALLOWED_PREFIXES = (
    "ACCELERATION_",
    "CHAPTER06_",
    "CHAPTER07_",
    "CHAPTER08_",
    "CHAPTER09_",
    "D90-HAB-",
    "D90-PENN-03-",
    "D90-PENN-04-",
    "DUALITY_",
    "OPTIMAL_TRANSPORT_",
    "PENN_CH03_",
    "PENN_CH04_",
    "PROJECTED_SUBGRADIENT_",
    "PROXIMAL_GRADIENT_",
    "STOCHASTIC_",
    "SUBGRADIENT_",
)

QA_ALLOWED_NAMES = {
    "audit_acceleration_unit.py",
    "audit_duality_unit.py",
    "audit_optimal_transport_unit.py",
    "audit_penn_ch03_unit.py",
    "audit_penn_ch04_candidate.py",
    "audit_projected_subgradient_unit.py",
    "audit_proximal_gradient_unit.py",
    "audit_stochastic_unit.py",
    "audit_subgradient_unit.py",
    "extend_backend_ch04.py",
    "extend_backend_ch05.py",
    "extend_backend_ch06.py",
    "extend_backend_ch07.py",
    "extend_backend_ch08.py",
    "extend_backend_ch09.py",
    "extend_backend_penn_ch03.py",
    "extend_backend_penn_ch04.py",
    "validate_acceleration_unit.py",
    "validate_backend_penn_ch03.py",
    "validate_backend_penn_ch04.py",
    "validate_duality_unit.py",
    "validate_optimal_transport_unit.py",
    "validate_penn_ch03_unit.py",
    "validate_penn_ch04_math.py",
    "validate_projected_subgradient_unit.py",
    "validate_proximal_gradient_unit.py",
    "validate_stochastic_unit.py",
    "validate_subgradient_unit.py",
}

UNADMITTED_PENN_TOKENS = tuple(
    token
    for chapter in range(5, 12)
    for token in (f"penn_ch{chapter:02d}", f"penn-{chapter:02d}")
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metadata(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def selected_paths() -> list[Path]:
    paths = [ROOT / item for item in STATIC_PATHS]
    paths.extend(ROOT / "source" / "id-ID" / item for item in SOURCE_FILES)
    paths.extend(
        ROOT / "source" / "id-ID" / "figures" / item
        for item in HABRING_FIGURES
    )
    paths.extend(
        ROOT / "source" / "id-ID" / "Figures" / item
        for item in PENN_FIGURES
    )
    paths.extend(ROOT / "00_control" / item for item in CONTROL_FILES)

    for path in sorted(path for path in (ROOT / "qa").iterdir() if path.is_file()):
        if path.name in QA_ALLOWED_NAMES or path.name.startswith(QA_ALLOWED_PREFIXES):
            paths.append(path)

    unique = {path.resolve(): path for path in paths}
    ordered = sorted(unique.values(), key=lambda item: item.relative_to(ROOT).as_posix())
    missing = [str(path) for path in ordered if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing release inputs:\n" + "\n".join(missing))
    leaked = [
        path.relative_to(ROOT).as_posix()
        for path in ordered
        if any(
            token in path.relative_to(ROOT).as_posix().lower()
            for token in UNADMITTED_PENN_TOKENS
        )
    ]
    if leaked:
        raise RuntimeError("Unadmitted Penn candidate leaked into bundle:\n" + "\n".join(leaked))
    return ordered


def add_bytes(archive: zipfile.ZipFile, arcname: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, payload)


def add_file(archive: zipfile.ZipFile, path: Path, arcname: str) -> None:
    add_bytes(archive, arcname, path.read_bytes())


def build_bundle() -> tuple[Path, list[dict[str, object]]]:
    inputs = selected_paths()
    inventory = [metadata(path) for path in inputs]
    internal_manifest = {
        "schema": "o015-zenodo-source-bundle-v1",
        "version": "2026.08.22",
        "checkpoint": "nine admitted units: Habring Chapters 3-9; Penn Chapters 3-4",
        "complete_corpus": False,
        "entries": inventory,
    }
    manifest_bytes = (
        json.dumps(internal_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    bundle = HERE / BUNDLE_NAME
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        add_file(archive, HERE / "README_RELEASE.md", "README_RELEASE.md")
        add_bytes(archive, "SOURCE_BUNDLE_MANIFEST.json", manifest_bytes)
        for path in inputs:
            add_file(archive, path, path.relative_to(ROOT).as_posix())

    with zipfile.ZipFile(bundle, "r") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP integrity failure at {bad}")
        names = archive.namelist()
        expected = 2 + len(inputs)
        if len(names) != expected or len(set(names)) != expected:
            raise RuntimeError("ZIP entry count/uniqueness failure")
    return bundle, inventory


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    bundle, bundle_inventory = build_bundle()
    upload_paths = [ROOT / "output" / "pdf" / name for name in PDF_NAMES]
    upload_paths.extend(
        [
            bundle,
            HERE / "README_RELEASE.md",
            HERE / "README.md",
            HERE / "RIGHTS.md",
        ]
    )
    missing = [str(path) for path in upload_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing upload files:\n" + "\n".join(missing))

    release_manifest = {
        "schema": "o015-zenodo-checkpoint-release-v1",
        "version": "2026.08.22",
        "publication_date": "2026-08-22",
        "zenodo_record_id": "22059742",
        "zenodo_record_doi": "10.5281/zenodo.22059742",
        "zenodo_concept_id": "22059741",
        "zenodo_concept_doi": "10.5281/zenodo.22059741",
        "title": "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia",
        "complete_corpus": False,
        "admitted_units": [
            "Habring Chapter 3",
            "Habring Chapter 4",
            "Habring Chapter 5",
            "Habring Chapter 6",
            "Habring Chapter 7",
            "Habring Chapter 8",
            "Habring Chapter 9",
            "Penn Chapter 3",
            "Penn Chapter 4",
        ],
        "uploads": [
            {
                "filename": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in upload_paths
        ],
        "source_bundle_entries": len(bundle_inventory) + 2,
        "rights_notice": (
            "Component-specific: Habring-derived material CC BY 4.0; "
            "Griffin/Penn-derived material CC BY-NC-SA 3.0 United States; "
            "see RIGHTS.md and 00_control/COMPONENT_RIGHTS.csv."
        ),
    }
    manifest_path = HERE / "release-manifest.json"
    manifest_path.write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    checksum_paths = upload_paths + [manifest_path]
    sums = "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_paths)
    sums_path = HERE / "SHA256SUMS"
    sums_path.write_text(sums, encoding="ascii", newline="\n")

    result = {
        "bundle": metadata(bundle),
        "bundle_entries": len(bundle_inventory) + 2,
        "release_manifest": metadata(manifest_path),
        "sha256sums": metadata(sums_path),
        "upload_file_count": len(upload_paths) + 2,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
