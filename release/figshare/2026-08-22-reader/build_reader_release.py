#!/usr/bin/env python3
"""Build the deterministic reader-first Figshare payload and source package."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIXED_ZIP_TIME = (2026, 8, 22, 0, 0, 0)
PDF = ROOT / "output" / "pdf" / "D90-HAB-03-09-modul-pendamping-id.pdf"
ZIP_NAME = "D90-HAB-03-09-sumber-id.zip"
LICENSE_NAME = "LICENSE_CC_BY_4.0.txt"
MANIFEST_NAME = "FIGSHARE_MANIFEST.json"
SUMS_NAME = "SHA256SUMS"
EXPECTED_PDF_SHA256 = "6cd291cc447999b7cd72622e8c2003b837cf4f21ea5de0fcb7094913e20acd87"
EXPECTED_PDF_BYTES = 3_090_098

SOURCE_FILES = [
    *(f"source/id-ID/D90-HAB-{chapter:02d}-{slug}.tex" for chapter, slug in [
        (3, "subgradien-id"),
        (4, "metode-subgradien-terproyeksi-id"),
        (5, "metode-gradien-proksimal-id"),
        (6, "akselerasi-id"),
        (7, "dualitas-id"),
        (8, "penurunan-gradien-stokastik-id"),
        (9, "transportasi-optimal-id"),
    ]),
    *(f"source/id-ID/habring-{chapter:02d}-{slug}.tex" for chapter, slug in [
        (3, "subgradien-id"),
        (4, "metode-subgradien-terproyeksi-id"),
        (5, "metode-gradien-proksimal-id"),
        (6, "akselerasi-id"),
        (7, "dualitas-id"),
        (8, "penurunan-gradien-stokastik-id"),
        (9, "transportasi-optimal-id"),
    ]),
    "source/id-ID/macros-id.tex",
    "source/id-ID/shinybook.cls",
    "source/id-ID/references-ot-id.bib",
    "source/id-ID/figures/gradient.png",
    "source/id-ID/figures/subgradient.png",
    "authority/habring/source-v1/references.bib",
    "qa/build_habring_companion_reader.py",
]

README_SOURCE = """# Modul Pendamping Habring Bab 3-9 - sumber Bahasa Indonesia

This compact source package rebuilds the seven standalone Indonesian Habring
Chapter 3-9 readers and their combined 103-page reader-first PDF. It contains
only the Habring-derived module; no Penn or other mixed-license work is present.

Authority: Andreas Habring, *Lecture Notes: Convex Optimization*,
arXiv:2607.11664v1, DOI 10.48550/arXiv.2607.11664. The immutable arXiv v1
submission is licensed under Creative Commons Attribution 4.0 International.
This is an independent Indonesian translation/adaptation with identified
changes and corrections; it is not reviewed, approved, sponsored, or endorsed
by Andreas Habring, TU Graz, arXiv, or their institutions.

The custom class and two raster figures are exact components of the CC BY 4.0
arXiv submission but carry no separate embedded notices. The source preface
credits Christian Clason's template and Thomas Pock's lecture slides. Those
submission-level provenance caveats are retained in
`COMPONENT_RIGHTS_HABRING.csv`.

## Rebuild

Verified local toolchain:

- MiKTeX 26.5 / pdfTeX 1.40.29;
- latexmk 4.88 and Biber 2.21;
- Python with `pypdf==6.10.0` and `reportlab==4.4.9`;
- Windows Arial fonts for byte-identical cover reproduction.

Install the two Python packages from `requirements-reader.txt`, then run from
the extracted package root:

```powershell
powershell -ExecutionPolicy Bypass -File .\\BUILD_MODULE.ps1
```

The script builds each unit with fixed source-date settings, places the seven
PDFs in `output/pdf`, and runs `qa/build_habring_companion_reader.py`. The
admitted combined reader has 103 A4 pages, `/Lang id-ID`, eight outline entries,
all fonts embedded with Unicode maps, no encryption or JavaScript, and SHA-256
`6cd291cc447999b7cd72622e8c2003b837cf4f21ea5de0fcb7094913e20acd87`.
On a different TeX/font platform, semantic content and pagination should be
checked even if PDF bytes differ.

The combined PDF is not semantically tagged and no independent human/native-
speaker Indonesian review is claimed. Exact determined source corrections are
listed in `CORRECTIONS_HABRING.jsonl`.
"""

REQUIREMENTS = """pypdf==6.10.0
reportlab==4.4.9
"""

BUILD_MODULE = r"""$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$moduleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir = Join-Path $moduleRoot 'source\id-ID'
$buildRoot = Join-Path $moduleRoot 'build'
$outputDir = Join-Path $moduleRoot 'output\pdf'
New-Item -ItemType Directory -Force -Path $buildRoot, $outputDir | Out-Null

$env:SOURCE_DATE_EPOCH = '1783900800'
$env:FORCE_SOURCE_DATE = '1'
$env:TZ = 'UTC'

$units = @(
    'D90-HAB-03-subgradien-id.tex',
    'D90-HAB-04-metode-subgradien-terproyeksi-id.tex',
    'D90-HAB-05-metode-gradien-proksimal-id.tex',
    'D90-HAB-06-akselerasi-id.tex',
    'D90-HAB-07-dualitas-id.tex',
    'D90-HAB-08-penurunan-gradien-stokastik-id.tex',
    'D90-HAB-09-transportasi-optimal-id.tex'
)

Push-Location $sourceDir
try {
    foreach ($unit in $units) {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($unit)
        $unitBuild = Join-Path $buildRoot $stem
        New-Item -ItemType Directory -Force -Path $unitBuild | Out-Null
        & latexmk -gg -pdf -interaction=nonstopmode -halt-on-error -file-line-error "-outdir=$unitBuild" $unit
        if ($LASTEXITCODE -ne 0) { throw "latexmk failed for $unit" }
        Copy-Item -LiteralPath (Join-Path $unitBuild ($stem + '.pdf')) -Destination (Join-Path $outputDir ($stem + '.pdf')) -Force
    }
}
finally {
    Pop-Location
}

& python (Join-Path $moduleRoot 'qa\build_habring_companion_reader.py')
if ($LASTEXITCODE -ne 0) { throw 'Combined reader build failed' }
Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $outputDir 'D90-HAB-03-09-modul-pendamping-id.pdf')
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def item(data: bytes, path: str) -> dict[str, object]:
    return {"path": path, "bytes": len(data), "sha256": sha256_bytes(data)}


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def generated_provenance() -> dict[str, bytes]:
    authority = json.loads((ROOT / "00_control" / "SOURCE_AUTHORITY.json").read_text(encoding="utf-8"))
    matches = [entry for entry in authority["authorities"] if entry["authority_id"] == "o015-habring-arxiv-2607.11664v1"]
    if len(matches) != 1:
        raise RuntimeError("Habring source-authority record is not unique")
    authority_subset = {
        "schema": "o015-habring-source-authority-subset-v1",
        "lane": authority["lane"],
        "role": authority["role"],
        "frozen_on": authority["frozen_on"],
        "authority": matches[0],
    }

    correction_lines = []
    for line in (ROOT / "00_control" / "ADVERSE_LEDGER.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if str(record.get("event_id", "")).startswith("O015-HAB-ADV-"):
            correction_lines.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))

    rights_source = ROOT / "00_control" / "COMPONENT_RIGHTS.csv"
    with rights_source.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    selected = [rows[0]] + [row for row in rows[1:] if "habring" in row[0].lower() or "habring" in row[1].lower()]
    rights_buffer = io.StringIO(newline="")
    writer = csv.writer(rights_buffer, lineterminator="\n")
    writer.writerows(selected)

    return {
        "README_SOURCE.md": README_SOURCE.encode("utf-8"),
        "requirements-reader.txt": REQUIREMENTS.encode("ascii"),
        "BUILD_MODULE.ps1": BUILD_MODULE.encode("utf-8"),
        "CORRECTIONS_HABRING.jsonl": ("\n".join(correction_lines) + "\n").encode("utf-8"),
        "COMPONENT_RIGHTS_HABRING.csv": rights_buffer.getvalue().encode("utf-8"),
        "SOURCE_AUTHORITY_HABRING.json": (json.dumps(authority_subset, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    }


def build_source_zip() -> tuple[Path, list[dict[str, object]]]:
    static: dict[str, bytes] = {}
    for relative in SOURCE_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        static[relative] = path.read_bytes()
    static[LICENSE_NAME] = (ROOT / "authority" / "habring" / "CC-BY-4.0-legalcode.txt").read_bytes()
    static.update(generated_provenance())

    forbidden = [name for name in static if any(token in name.lower() for token in ("penn", "griffin", "maple", ".mpl", "token", ".git"))]
    if forbidden:
        raise RuntimeError(f"Non-Habring or forbidden source entered the Figshare package: {forbidden}")

    inventory = [item(static[name], name) for name in sorted(static)]
    internal = {
        "schema": "o015-habring-reader-source-bundle-v1",
        "status": "coherent partial companion module",
        "coverage": "Habring Chapters 3-9 only",
        "language": "id-ID",
        "license": "CC BY 4.0",
        "source": "Andreas Habring, Lecture Notes: Convex Optimization, arXiv:2607.11664v1",
        "complete_selected_module": True,
        "complete_d90_course": False,
        "entries": inventory,
    }
    manifest_bytes = (json.dumps(internal, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    bundle = HERE / ZIP_NAME
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(static):
            add_bytes(archive, name, static[name])
        add_bytes(archive, "SOURCE_BUNDLE_MANIFEST.json", manifest_bytes)

    with zipfile.ZipFile(bundle, "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Source ZIP integrity failure")
        names = archive.namelist()
        if len(names) != len(static) + 1 or len(set(names)) != len(names):
            raise RuntimeError("Source ZIP entry count/uniqueness failure")
        parsed = json.loads(archive.read("SOURCE_BUNDLE_MANIFEST.json"))
        for entry in parsed["entries"]:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or sha256_bytes(data) != entry["sha256"]:
                raise RuntimeError(f"Source ZIP manifest mismatch: {entry['path']}")
    return bundle, inventory


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    if not PDF.is_file() or PDF.stat().st_size != EXPECTED_PDF_BYTES or sha256(PDF) != EXPECTED_PDF_SHA256:
        raise RuntimeError("Combined Habring reader identity changed")

    license_path = HERE / LICENSE_NAME
    license_path.write_bytes((ROOT / "authority" / "habring" / "CC-BY-4.0-legalcode.txt").read_bytes())
    bundle, source_entries = build_source_zip()
    manifest = {
        "schema": "o015-figshare-reader-release-v1",
        "article_id": 33314733,
        "project_id": 280296,
        "collection_id": 8668413,
        "status": "coherent partial companion module; Habring Chapters 3-9 complete",
        "complete_d90_course": False,
        "license": "CC BY 4.0",
        "upload_order": [PDF.name, bundle.name, license_path.name, MANIFEST_NAME, SUMS_NAME],
        "payloads": [
            {"filename": PDF.name, "bytes": PDF.stat().st_size, "sha256": sha256(PDF), "role": "primary reader"},
            {"filename": bundle.name, "bytes": bundle.stat().st_size, "sha256": sha256(bundle), "role": "compact resumable source"},
            {"filename": license_path.name, "bytes": license_path.stat().st_size, "sha256": sha256(license_path), "role": "exact license"},
        ],
        "source_bundle_entries": len(source_entries) + 1,
    }
    manifest_path = HERE / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    sums_path = HERE / SUMS_NAME
    sums_paths = [PDF, bundle, license_path, manifest_path]
    sums_path.write_text("".join(f"{sha256(path)}  {path.name}\n" for path in sums_paths), encoding="ascii", newline="\n")
    total = sum(path.stat().st_size for path in [PDF, bundle, license_path, manifest_path, sums_path])
    if total > 500_000_000:
        raise RuntimeError(f"Figshare task payload exceeds 500 MB: {total}")
    print(json.dumps({
        "pdf": {"bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
        "source_zip": {"bytes": bundle.stat().st_size, "sha256": sha256(bundle), "entries": len(source_entries) + 1},
        "license": {"bytes": license_path.stat().st_size, "sha256": sha256(license_path)},
        "manifest": {"bytes": manifest_path.stat().st_size, "sha256": sha256(manifest_path)},
        "checksums": {"bytes": sums_path.stat().st_size, "sha256": sha256(sums_path)},
        "total_upload_bytes": total,
        "cap_bytes": 500_000_000,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
