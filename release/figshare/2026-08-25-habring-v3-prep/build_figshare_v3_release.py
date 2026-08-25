#!/usr/bin/env python3
"""Build and verify the deterministic Figshare v3 Habring-only payload."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ZIP_EPOCH = (2026, 8, 25, 0, 0, 0)
TASK_CAP = 500_000_000

PDF_NAME = "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf"
HTML_NAME = "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html"
EPUB_NAME = "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub"
SOURCE_ZIP_NAME = "D90-HAB-01-09-sumber-id.zip"
LICENSE_NAME = "LICENSE_CC_BY_4.0.txt"
MANIFEST_NAME = "FIGSHARE_MANIFEST.json"
SUMS_NAME = "SHA256SUMS"
RECEIPT_NAME = "PREPARATION_RECEIPT.json"

ARTIFACTS = {
    PDF_NAME: {
        "source": ROOT / "output" / "pdf" / PDF_NAME,
        "bytes": 3_779_312,
        "sha256": "da2b421b97efce4e3d7b8cf6be9938d17b7768b9c6bcb4846b09b9c692b34c41",
        "role": "primary reader (PDF, 139 A4 pages)",
    },
    HTML_NAME: {
        "source": ROOT / "output" / "html" / HTML_NAME,
        "bytes": 1_669_938,
        "sha256": "717ee81912a8b903acc87e5c59d830aa1d8c78abdda6e0c869d66b9a7bcde3a4",
        "role": "reflowable standalone HTML reader",
    },
    EPUB_NAME: {
        "source": ROOT / "output" / "epub" / EPUB_NAME,
        "bytes": 231_700,
        "sha256": "c630e25db3cbbfa6f6afa7213e526c47586b6e7b44f709095ea5a3881756fd41",
        "role": "EPUB 3 reader",
    },
}

WRAPPERS = [
    "source/id-ID/D90-HAB-01-02-prasyarat-dan-konveksitas-id.tex",
    "source/id-ID/D90-HAB-03-subgradien-id.tex",
    "source/id-ID/D90-HAB-04-metode-subgradien-terproyeksi-id.tex",
    "source/id-ID/D90-HAB-05-metode-gradien-proksimal-id.tex",
    "source/id-ID/D90-HAB-06-akselerasi-id.tex",
    "source/id-ID/D90-HAB-07-dualitas-id.tex",
    "source/id-ID/D90-HAB-08-penurunan-gradien-stokastik-id.tex",
    "source/id-ID/D90-HAB-09-transportasi-optimal-id.tex",
]

CHAPTERS = [
    "source/id-ID/habring-01-prasyarat-id.tex",
    "source/id-ID/habring-02-konveksitas-id.tex",
    "source/id-ID/habring-03-subgradien-id.tex",
    "source/id-ID/habring-04-metode-subgradien-terproyeksi-id.tex",
    "source/id-ID/habring-05-metode-gradien-proksimal-id.tex",
    "source/id-ID/habring-06-akselerasi-id.tex",
    "source/id-ID/habring-07-dualitas-id.tex",
    "source/id-ID/habring-08-penurunan-gradien-stokastik-id.tex",
    "source/id-ID/habring-09-transportasi-optimal-id.tex",
]

SUPPORT = [
    "source/id-ID/macros-id.tex",
    "source/id-ID/shinybook.cls",
    "source/id-ID/references-ot-id.bib",
    "authority/habring/source-v1/references.bib",
    "source/id-ID/figures/balls.png",
    "source/id-ID/figures/convex_fct.png",
    "source/id-ID/figures/discontinuous_function.png",
    "source/id-ID/figures/gradient.png",
    "source/id-ID/figures/lsc_function.png",
    "source/id-ID/figures/sets.png",
    "source/id-ID/figures/subgradient.png",
    "qa/build_habring_ch01_ch02.py",
    "qa/build_habring_full_reader.py",
    "qa/build_habring_full_html.py",
    "qa/build_habring_full_epub.py",
]

README_SOURCE = """# Optimisasi Konveks — sumber edisi Bahasa Indonesia

Paket sumber ringkas ini membangun ulang edisi Bahasa Indonesia lengkap untuk
prakata dan Bab 1–9 Andreas Habring, *Lecture Notes: Convex Optimization*,
arXiv:2607.11664v1. Cakupan spine Habring v1 sudah lengkap; buku kuliah O015
yang lebih besar masih parsial karena suplemen terstruktur dan lapisan asli
yang tidak tumpang tindih dikelola secara terpisah. Paket ini tidak memuat byte
dari komponen MIT, Penn, Royer, atau Becker.

Sumber berwenang adalah paket arXiv v1 berukuran 230116 byte dengan SHA-256
`d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748`,
tersedia di <https://arxiv.org/e-print/2607.11664v1>. Karya sumber, terjemahan,
adaptasi, materi pengantar, dan perangkat pembangunan dalam paket ini tersedia
berdasarkan Creative Commons Attribution 4.0 International (CC BY 4.0). Atribusi,
tautan lisensi, identifikasi perubahan, dan non-endorsement harus dipertahankan.
Kelas khusus dan tujuh gambar raster diwarisi dari submission CC BY 4.0, tetapi
tidak memuat pemberitahuan terpisah atau sumber pembangkit; rincian ini
dipertahankan di `COMPONENT_RIGHTS_HABRING.csv`.

Perubahan meliputi penerjemahan Bahasa Indonesia, pelokalan istilah dan label,
deskripsi akses untuk gambar, perbaikan TeX, serta koreksi matematis yang dapat
ditentukan. Segmen sumber stabil dan catatan unit mempertahankan keterlacakan.
Ini adalah edisi mandiri: Andreas Habring, TU Graz, arXiv, dan institusi terkait
tidak menyusun, memeriksa, menyetujui, mensponsori, atau mendukung edisi ini.

Provenans produksi: OpenAI Codex gpt-5.6-sol, Ultra, atas instruksi pengguna.
Seluruh kredit penulis dan sumber dipertahankan.

## Membangun ulang

Prasyarat yang diverifikasi pada checkpoint ini:

- MiKTeX 26.5 / pdfTeX 1.40.29, latexmk 4.88, Biber 2.21;
- Pandoc 3.9.0.2;
- Python dengan `pypdf==6.10.0` dan `reportlab==4.4.9`;
- font Arial Windows untuk reproduksi byte-identik halaman sampul.

Dari akar hasil ekstraksi, jalankan:

```powershell
powershell -ExecutionPolicy Bypass -File .\\BUILD_ALL_READERS.ps1
```

Hasil checkpoint yang diakui:

- PDF 139 halaman: SHA-256 `da2b421b97efce4e3d7b8cf6be9938d17b7768b9c6bcb4846b09b9c692b34c41`;
- HTML mandiri dan reflowable: SHA-256 `717ee81912a8b903acc87e5c59d830aa1d8c78abdda6e0c869d66b9a7bcde3a4`;
- EPUB 3: SHA-256 `c630e25db3cbbfa6f6afa7213e526c47586b6e7b44f709095ea5a3881756fd41`.

PDF dapat dicari, tidak terenkripsi, mendeklarasikan `id-ID`, dan memiliki
navigasi bab, tetapi belum bertag semantik. HTML dan EPUB menyediakan permukaan
reflowable. Tidak ada klaim peninjauan oleh penulis sumber atau institusinya.
"""

BUILD_ALL = r"""$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir = Join-Path $bundleRoot 'source\id-ID'
$buildRoot = Join-Path $bundleRoot 'build'
$outputPdf = Join-Path $bundleRoot 'output\pdf'
New-Item -ItemType Directory -Force -Path $buildRoot, $outputPdf | Out-Null

$env:SOURCE_DATE_EPOCH = '1783900800'
$env:FORCE_SOURCE_DATE = '1'
$env:TZ = 'UTC'

& python (Join-Path $bundleRoot 'qa\build_habring_ch01_ch02.py')
if ($LASTEXITCODE -ne 0) { throw 'Bab 1-2 gagal dibangun' }

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
        if ($LASTEXITCODE -ne 0) { throw "latexmk gagal untuk $unit" }
        Copy-Item -LiteralPath (Join-Path $unitBuild ($stem + '.pdf')) -Destination (Join-Path $outputPdf ($stem + '.pdf')) -Force
    }
}
finally {
    Pop-Location
}

& python (Join-Path $bundleRoot 'qa\build_habring_full_reader.py')
if ($LASTEXITCODE -ne 0) { throw 'Pembaca PDF lengkap gagal dibangun' }
& python (Join-Path $bundleRoot 'qa\build_habring_full_html.py')
if ($LASTEXITCODE -ne 0) { throw 'Pembaca HTML lengkap gagal dibangun' }
& python (Join-Path $bundleRoot 'qa\build_habring_full_epub.py')
if ($LASTEXITCODE -ne 0) { throw 'Pembaca EPUB lengkap gagal dibangun' }

Get-FileHash -Algorithm SHA256 -LiteralPath @(
    (Join-Path $bundleRoot 'output\pdf\D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf'),
    (Join-Path $bundleRoot 'output\html\D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html'),
    (Join-Path $bundleRoot 'output\epub\D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub')
)
"""

REQUIREMENTS = """pypdf==6.10.0
reportlab==4.4.9
"""

CHANGES = """# Perubahan terhadap sumber arXiv v1

Edisi ini menerjemahkan prakata dan seluruh sembilan bab ke Bahasa Indonesia,
melokalkan judul dan label, menambahkan identitas segmen stabil, menyediakan
deskripsi akses untuk gambar, serta memperbaiki kesalahan TeX dan matematika
yang dapat ditentukan tanpa mengubah maksud matematis. Urutan, rumus, bukti,
latihan, rujukan silang, dan aset sumber dipertahankan sejauh berlaku.

Setiap wrapper mencantumkan identitas sumber, lisensi, perubahan, dan
non-endorsement. Berkas bab memuat penanda segmen yang mengikatnya ke sumber
arXiv v1. Rincian hak komponen tersedia di `COMPONENT_RIGHTS_HABRING.csv`.

Provenans produksi: OpenAI Codex gpt-5.6-sol, Ultra, atas instruksi pengguna.
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory_item(name: str, data: bytes) -> dict[str, object]:
    return {"path": name, "bytes": len(data), "sha256": sha256_bytes(data)}


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def authority_subset() -> bytes:
    path = ROOT / "00_control" / "SOURCE_AUTHORITY.json"
    authority = json.loads(path.read_text(encoding="utf-8"))
    matches = [
        item
        for item in authority["authorities"]
        if item.get("authority_id") == "o015-habring-arxiv-2607.11664v1"
    ]
    if len(matches) != 1:
        raise RuntimeError("Habring authority record is not unique")
    subset = {
        "schema": "o015-habring-source-authority-subset-v2",
        "lane": authority.get("lane"),
        "role": authority.get("role"),
        "authority": matches[0],
    }
    return (json.dumps(subset, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def rights_subset() -> bytes:
    source = ROOT / "00_control" / "COMPONENT_RIGHTS.csv"
    with source.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    if not rows:
        raise RuntimeError("Empty component-rights ledger")
    selected = [rows[0]] + [
        row
        for row in rows[1:]
        if any("habring" in cell.lower() for cell in row)
    ]
    if len(selected) < 10:
        raise RuntimeError("Habring component-rights subset is unexpectedly small")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(selected)
    return buffer.getvalue().encode("utf-8")


def static_source_files() -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for relative in [*WRAPPERS, *CHAPTERS, *SUPPORT]:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        result[relative] = path.read_bytes()
    result[LICENSE_NAME] = (
        ROOT / "authority" / "habring" / "CC-BY-4.0-legalcode.txt"
    ).read_bytes()
    result.update(
        {
            "README_SOURCE.md": README_SOURCE.encode("utf-8"),
            "BUILD_ALL_READERS.ps1": BUILD_ALL.encode("utf-8"),
            "requirements-reader.txt": REQUIREMENTS.encode("ascii"),
            "CHANGES.md": CHANGES.encode("utf-8"),
            "SOURCE_AUTHORITY_HABRING.json": authority_subset(),
            "COMPONENT_RIGHTS_HABRING.csv": rights_subset(),
        }
    )
    forbidden = [
        name
        for name in result
        if any(
            token in name.lower()
            for token in (
                "mit-",
                "penn",
                "royer",
                "becker",
                "griffin",
                "maple",
                ".mpl",
                "token",
                ".git",
            )
        )
    ]
    if forbidden:
        raise RuntimeError(f"Forbidden non-Habring source path: {forbidden}")
    text_suffixes = {".bib", ".csv", ".json", ".md", ".ps1", ".py", ".tex", ".txt"}
    mixed_rights = [
        name
        for name, data in result.items()
        if Path(name).suffix.lower() in text_suffixes and b"CC BY-SA" in data
    ]
    if mixed_rights:
        raise RuntimeError(f"Mixed CC BY-SA claim entered CC BY 4.0 package: {mixed_rights}")
    return result


def build_source_zip() -> tuple[Path, list[dict[str, object]]]:
    static = static_source_files()
    inventory = [inventory_item(name, static[name]) for name in sorted(static)]
    internal_manifest = {
        "schema": "o015-habring-complete-source-bundle-v2",
        "language": "id-ID",
        "source": "Andreas Habring, Lecture Notes: Convex Optimization, arXiv:2607.11664v1",
        "source_tar_sha256": "d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748",
        "license": "CC BY 4.0",
        "status": "complete Habring v1 spine; larger O015 coursebook partial",
        "complete_habring_v1_spine": True,
        "complete_o015_coursebook": False,
        "model_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
        "entries": inventory,
    }
    manifest_bytes = (
        json.dumps(internal_manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    destination = HERE / SOURCE_ZIP_NAME
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name in sorted(static):
            add_bytes(archive, name, static[name])
        add_bytes(archive, "SOURCE_BUNDLE_MANIFEST.json", manifest_bytes)

    with zipfile.ZipFile(destination, "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Source ZIP integrity failure")
        names = archive.namelist()
        if len(names) != len(static) + 1 or len(set(names)) != len(names):
            raise RuntimeError("Source ZIP entry count or uniqueness failure")
        parsed = json.loads(archive.read("SOURCE_BUNDLE_MANIFEST.json"))
        for entry in parsed["entries"]:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or sha256_bytes(data) != entry["sha256"]:
                raise RuntimeError(f"Source ZIP manifest mismatch: {entry['path']}")
    return destination, inventory


def verify_primary_artifacts() -> None:
    for name, expected in ARTIFACTS.items():
        source = expected["source"]
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.stat().st_size != expected["bytes"] or sha256(source) != expected["sha256"]:
            raise RuntimeError(f"Admitted artifact identity changed: {name}")

    pdf = PdfReader(str(ARTIFACTS[PDF_NAME]["source"]))
    if (
        len(pdf.pages) != 139
        or pdf.is_encrypted
        or str(pdf.trailer["/Root"].get("/Lang")) != "id-ID"
        or len(pdf.outline) != 9
    ):
        raise RuntimeError("Primary PDF structure gate failed")

    html_text = ARTIFACTS[HTML_NAME]["source"].read_text(encoding="utf-8")
    html_search = " ".join(html_text.split())
    for marker in (
        "OpenAI Codex gpt-5.6-sol, Ultra",
        "CC BY 4.0",
        "Andreas Habring",
    ):
        if marker not in html_search:
            raise RuntimeError(f"HTML provenance marker missing: {marker}")
    semantic_html = re.sub(
        r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>",
        " ",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if re.search(
        r"(?i)(?:\bTTP\b|Translation and Transcription Project)", semantic_html
    ):
        raise RuntimeError("Forbidden umbrella prose in HTML reader")

    with zipfile.ZipFile(ARTIFACTS[EPUB_NAME]["source"], "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("EPUB ZIP integrity failure")
        names = archive.namelist()
        if len(names) != 24 or names[0] != "mimetype":
            raise RuntimeError("EPUB closure/order gate failed")
        if archive.read("mimetype") != b"application/epub+zip":
            raise RuntimeError("EPUB mimetype gate failed")
        concatenated = b"\n".join(
            archive.read(name)
            for name in names
            if name.endswith((".xhtml", ".opf"))
        )
        epub_search = b" ".join(concatenated.split())
        for marker in (
            b"OpenAI Codex gpt-5.6-sol, Ultra",
            b"Andreas Habring",
        ):
            if marker not in epub_search:
                raise RuntimeError(f"EPUB provenance marker missing: {marker!r}")


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    verify_primary_artifacts()
    for name, expected in ARTIFACTS.items():
        shutil.copyfile(expected["source"], HERE / name)

    license_source = (
        ROOT / "authority" / "habring" / "CC-BY-4.0-legalcode.txt"
    )
    shutil.copyfile(license_source, HERE / LICENSE_NAME)
    source_zip, source_entries = build_source_zip()

    payloads = []
    for name in (PDF_NAME, HTML_NAME, EPUB_NAME):
        path = HERE / name
        payloads.append(
            {
                "filename": name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "role": ARTIFACTS[name]["role"],
            }
        )
    payloads.extend(
        [
            {
                "filename": source_zip.name,
                "bytes": source_zip.stat().st_size,
                "sha256": sha256(source_zip),
                "role": "compact resumable Habring source package",
            },
            {
                "filename": LICENSE_NAME,
                "bytes": (HERE / LICENSE_NAME).stat().st_size,
                "sha256": sha256(HERE / LICENSE_NAME),
                "role": "exact CC BY 4.0 legal code",
            },
        ]
    )
    upload_order = [
        PDF_NAME,
        HTML_NAME,
        EPUB_NAME,
        SOURCE_ZIP_NAME,
        LICENSE_NAME,
        MANIFEST_NAME,
        SUMS_NAME,
    ]
    manifest = {
        "schema": "o015-figshare-habring-v3-release-v2",
        "article_id": 33314733,
        "prior_doi": "10.6084/m9.figshare.33314733.v2",
        "project_id": 280296,
        "collection_id": 8668413,
        "language": "id-ID",
        "license": "CC BY 4.0",
        "status": "complete Habring v1 spine; larger O015 coursebook partial",
        "complete_habring_v1_spine": True,
        "complete_o015_coursebook": False,
        "model_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
        "upload_order": upload_order,
        "payloads": payloads,
        "source_bundle_entries": len(source_entries) + 1,
        "exclusions": [
            "MIT bytes",
            "Penn bytes",
            "Royer bytes",
            "Becker bytes",
            "raw provenance dumps",
            "build caches",
            "duplicate unit PDFs",
            "credentials",
        ],
    }
    manifest_path = HERE / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    sums_path = HERE / SUMS_NAME
    bound = [HERE / name for name in upload_order[:-1]]
    sums_path.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in bound),
        encoding="ascii",
        newline="\n",
    )

    upload_paths = [HERE / name for name in upload_order]
    total = sum(path.stat().st_size for path in upload_paths)
    if total > TASK_CAP:
        raise RuntimeError(f"Figshare task payload exceeds 500 MB: {total}")
    receipt = {
        "schema": "o015-figshare-habring-v3-preparation-v1",
        "result": "pass",
        "article_id": 33314733,
        "prior_doi": "10.6084/m9.figshare.33314733.v2",
        "upload_order": upload_order,
        "files": [
            {
                "filename": path.name,
                "bytes": path.stat().st_size,
                "md5": hashlib.md5(path.read_bytes()).hexdigest(),
                "sha256": sha256(path),
            }
            for path in upload_paths
        ],
        "file_count": len(upload_paths),
        "total_upload_bytes": total,
        "task_cap_bytes": TASK_CAP,
        "source_zip_entries": len(source_entries) + 1,
        "checks": {
            "reader_first": upload_order[0] == PDF_NAME,
            "pdf_structure": True,
            "html_provenance": True,
            "epub_structure": True,
            "source_zip_integrity": True,
            "exact_cc_by_4_0_license": sha256(HERE / LICENSE_NAME)
            == "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411",
            "payload_cap": total <= TASK_CAP,
            "no_credentials": True,
            "no_non_habring_components": True,
            "no_ttp_title_or_lead": True,
        },
    }
    receipt_path = HERE / RECEIPT_NAME
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
