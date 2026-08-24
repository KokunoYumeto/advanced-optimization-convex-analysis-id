#!/usr/bin/env python3
"""Build the complete reader-first Habring Chapters 1--9 Indonesian PDF."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp" / "pdfs"
OUTPUT = (
    ROOT
    / "output"
    / "pdf"
    / "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf"
)
COVER = TMP / "D90-HAB-01-09-cover-id.pdf"
FIRST = TMP / "D90-HAB-01-09-first-id.pdf"
REPORT = ROOT / "qa" / "HABRING_FULL_READER_BUILD.json"

UNITS = [
    (
        "Prakata, Bab 1 - Prasyarat, dan Bab 2 - Kekonveksan",
        "D90-HAB-01-02-prasyarat-dan-konveksitas-id.pdf",
    ),
    ("Bab 3 - Subgradien", "D90-HAB-03-subgradien-id.pdf"),
    (
        "Bab 4 - Metode Subgradien Terproyeksi",
        "D90-HAB-04-metode-subgradien-terproyeksi-id.pdf",
    ),
    (
        "Bab 5 - Metode Gradien Proksimal",
        "D90-HAB-05-metode-gradien-proksimal-id.pdf",
    ),
    ("Bab 6 - Akselerasi", "D90-HAB-06-akselerasi-id.pdf"),
    ("Bab 7 - Dualitas", "D90-HAB-07-dualitas-id.pdf"),
    (
        "Bab 8 - Penurunan Gradien Stokastik",
        "D90-HAB-08-penurunan-gradien-stokastik-id.pdf",
    ),
    (
        "Bab 9 - Selingan tentang Transportasi Optimal",
        "D90-HAB-09-transportasi-optimal-id.pdf",
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def register_fonts() -> tuple[str, str]:
    regular = Path(r"C:\Windows\Fonts\arial.ttf")
    bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    italic = Path(r"C:\Windows\Fonts\ariali.ttf")
    bold_italic = Path(r"C:\Windows\Fonts\arialbi.ttf")
    if all(path.is_file() for path in (regular, bold, italic, bold_italic)):
        pdfmetrics.registerFont(TTFont("Arial", str(regular)))
        pdfmetrics.registerFont(TTFont("Arial-Bold", str(bold)))
        pdfmetrics.registerFont(TTFont("Arial-Italic", str(italic)))
        pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(bold_italic)))
        pdfmetrics.registerFontFamily(
            "Arial",
            normal="Arial",
            bold="Arial-Bold",
            italic="Arial-Italic",
            boldItalic="Arial-BoldItalic",
        )
        return "Arial", "Arial-Bold"
    return "Helvetica", "Helvetica-Bold"


def build_cover() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    regular, bold = register_fonts()
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleID",
        parent=styles["Title"],
        fontName=bold,
        fontSize=22,
        leading=27,
        spaceAfter=10 * mm,
        textColor="#17243A",
    )
    subtitle = ParagraphStyle(
        "SubtitleID",
        parent=styles["Heading2"],
        fontName=bold,
        fontSize=13,
        leading=17,
        spaceAfter=5 * mm,
        textColor="#2B527E",
    )
    body = ParagraphStyle(
        "BodyID",
        parent=styles["BodyText"],
        fontName=regular,
        fontSize=10.3,
        leading=14.5,
        spaceAfter=3.5 * mm,
        textColor="#1E2633",
    )
    item = ParagraphStyle(
        "ItemID",
        parent=body,
        leftIndent=6 * mm,
        firstLineIndent=-4 * mm,
        spaceAfter=1.7 * mm,
    )
    story = [
        Paragraph("Optimisasi Konveks", title),
        Paragraph("Catatan Kuliah - Edisi Bahasa Indonesia", subtitle),
        Paragraph(
            "Terjemahan lengkap sembilan bab dari Andreas Habring, "
            "<i>Lecture Notes: Convex Optimization</i>, arXiv:2607.11664v1. "
            "Ini adalah karya turunan mandiri, bukan edisi resmi dan bukan "
            "dukungan penulis sumber maupun TU Graz.",
            body,
        ),
        Paragraph("Isi pembaca", subtitle),
    ]
    for title_text, _ in UNITS:
        story.append(Paragraph(f"- {title_text}", item))
    story.extend(
        [
            Spacer(1, 3 * mm),
            Paragraph("Hak, perubahan, dan akses", subtitle),
            Paragraph(
                "Karya sumber dan terjemahan/adaptasi ini tersedia berdasarkan "
                "Creative Commons Attribution 4.0 International (CC BY 4.0). "
                "Koreksi matematis dan perubahan penerjemahan diungkapkan dalam "
                "catatan unit serta ledger edisi.",
                body,
            ),
            Paragraph(
                "PDF ini dapat dicari dan mendeklarasikan bahasa id-ID, tetapi "
                "belum bertanda semantik. Pembaca HTML yang dapat direflow "
                "disediakan sebagai permukaan akses tambahan.",
                body,
            ),
            Paragraph(
                "Provenans produksi: OpenAI Codex gpt-5.6-sol, Ultra, atas "
                "instruksi pengguna repositori; seluruh kredit sumber dan "
                "penulis tetap dipertahankan.",
                body,
            ),
        ]
    )
    doc = SimpleDocTemplate(
        str(COVER),
        pagesize=A4,
        rightMargin=24 * mm,
        leftMargin=24 * mm,
        topMargin=24 * mm,
        bottomMargin=21 * mm,
        title="Optimisasi Konveks - Catatan Kuliah - Edisi Bahasa Indonesia",
        author="Andreas Habring; terjemahan/adaptasi mandiri",
        subject="Pembaca lengkap sembilan bab, CC BY 4.0",
        creator="Deterministic ReportLab build",
        invariant=True,
        pageCompression=1,
    )
    doc.build(story)


def assemble(destination: Path) -> dict[str, object]:
    inputs = [(title, ROOT / "output" / "pdf" / name) for title, name in UNITS]
    missing = [str(path) for _, path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing reader inputs: " + ", ".join(missing))
    build_cover()
    writer = PdfWriter()
    writer.append(str(COVER), import_outline=False)
    starts: list[tuple[str, int]] = []
    cursor = 1
    for title, path in inputs:
        starts.append((title, cursor))
        reader = PdfReader(str(path))
        writer.append(reader, import_outline=False)
        cursor += len(reader.pages)
    writer.add_outline_item("Halaman pengantar", 0)
    for title, page_index in starts:
        writer.add_outline_item(title, page_index)
    writer.add_metadata(
        {
            "/Title": "Optimisasi Konveks - Catatan Kuliah - Edisi Bahasa Indonesia",
            "/Author": "Andreas Habring; terjemahan/adaptasi mandiri",
            "/Subject": "Pembaca lengkap sembilan bab, CC BY 4.0",
            "/Keywords": "Bahasa Indonesia, optimisasi konveks, analisis konveks, CC BY 4.0",
            "/Creator": "Deterministic pypdf/ReportLab build",
            "/Producer": "pypdf",
        }
    )
    writer._root_object.update(
        {NameObject("/Lang"): TextStringObject("id-ID")}
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as stream:
        writer.write(stream)
    reader = PdfReader(str(destination))
    return {
        "path": destination.relative_to(ROOT).as_posix(),
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "pages": len(reader.pages),
        "catalog_lang": str(reader.trailer["/Root"].get("/Lang")),
        "encrypted": reader.is_encrypted,
        "outline_entries": 1 + len(starts),
        "components": [
            {
                "title": title,
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "pages": len(PdfReader(str(path)).pages),
            }
            for title, path in inputs
        ],
    }


def main() -> None:
    first = assemble(FIRST)
    final = assemble(OUTPUT)
    if FIRST.read_bytes() != OUTPUT.read_bytes():
        raise RuntimeError(
            "Two full-reader builds differ: "
            f"{first['sha256']} != {final['sha256']}"
        )
    report = {
        "schema": "o015-habring-full-reader-build-v1",
        "result": "pass",
        "artifact": final,
        "determinism": {"builds": 2, "byte_identical": True},
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    FIRST.unlink(missing_ok=True)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
