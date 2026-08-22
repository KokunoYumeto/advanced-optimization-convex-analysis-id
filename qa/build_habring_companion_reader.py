#!/usr/bin/env python3
"""Build the deterministic reader-first Habring Chapters 3--9 companion PDF."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject, TextStringObject
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp" / "pdfs"
OUTPUT = ROOT / "output" / "pdf" / "D90-HAB-03-09-modul-pendamping-id.pdf"
COVER = TMP / "D90-HAB-03-09-cover-id.pdf"

UNITS = [
    ("Bab 3 - Subgradien", "D90-HAB-03-subgradien-id.pdf"),
    ("Bab 4 - Metode Subgradien Terproyeksi", "D90-HAB-04-metode-subgradien-terproyeksi-id.pdf"),
    ("Bab 5 - Metode Gradien Proksimal", "D90-HAB-05-metode-gradien-proksimal-id.pdf"),
    ("Bab 6 - Akselerasi", "D90-HAB-06-akselerasi-id.pdf"),
    ("Bab 7 - Dualitas", "D90-HAB-07-dualitas-id.pdf"),
    ("Bab 8 - Penurunan Gradien Stokastik", "D90-HAB-08-penurunan-gradien-stokastik-id.pdf"),
    ("Bab 9 - Selingan tentang Transportasi Optimal", "D90-HAB-09-transportasi-optimal-id.pdf"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_cover() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    font_name = "Arial"
    bold_name = "Arial-Bold"
    arial = Path(r"C:\Windows\Fonts\arial.ttf")
    arial_bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    arial_italic = Path(r"C:\Windows\Fonts\ariali.ttf")
    arial_bold_italic = Path(r"C:\Windows\Fonts\arialbi.ttf")
    if all(path.is_file() for path in (arial, arial_bold, arial_italic, arial_bold_italic)):
        pdfmetrics.registerFont(TTFont(font_name, str(arial)))
        pdfmetrics.registerFont(TTFont(bold_name, str(arial_bold)))
        pdfmetrics.registerFont(TTFont("Arial-Italic", str(arial_italic)))
        pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(arial_bold_italic)))
        pdfmetrics.registerFontFamily(
            "Arial",
            normal=font_name,
            bold=bold_name,
            italic="Arial-Italic",
            boldItalic="Arial-BoldItalic",
        )
    else:
        font_name = "Helvetica"
        bold_name = "Helvetica-Bold"

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleID",
        parent=styles["Title"],
        fontName=bold_name,
        fontSize=22,
        leading=27,
        spaceAfter=12 * mm,
        textColor="#18233A",
    )
    subtitle = ParagraphStyle(
        "SubtitleID",
        parent=styles["Heading2"],
        fontName=bold_name,
        fontSize=13,
        leading=17,
        spaceAfter=6 * mm,
        textColor="#304A70",
    )
    body = ParagraphStyle(
        "BodyID",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=15,
        spaceAfter=4 * mm,
        textColor="#1E2633",
    )
    item = ParagraphStyle(
        "ItemID",
        parent=body,
        leftIndent=6 * mm,
        firstLineIndent=-4 * mm,
        spaceAfter=2 * mm,
    )

    story = [
        Paragraph("Optimisasi Lanjut dan Analisis Konveks", title),
        Paragraph("Modul pendamping Bahasa Indonesia - Habring Bab 3-9", subtitle),
        Paragraph(
            "Checkpoint pembaca koheren ini menghimpun tujuh unit yang telah "
            "diterjemahkan dan divalidasi. Ini adalah modul pendamping parsial, "
            "bukan korpus utama D90 yang lengkap dan bukan klaim peninjauan oleh "
            "penulis sumber atau institusinya.",
            body,
        ),
        Paragraph("Isi", subtitle),
    ]
    for chapter, _ in UNITS:
        story.append(Paragraph(f"- {chapter}", item))
    story.extend(
        [
            Spacer(1, 4 * mm),
            Paragraph("Hak dan atribusi", subtitle),
            Paragraph(
                "Terjemahan/adaptasi independen dari Andreas Habring, "
                "<i>Lecture Notes: Convex Optimization</i>, arXiv:2607.11664v1. "
                "Materi turunan dan halaman pengantar ini disediakan di bawah "
                "Creative Commons Attribution 4.0 International (CC BY 4.0). "
                "Perubahan terjemahan, koreksi, dan penyusunan modul dinyatakan "
                "dalam berkas sumber dan ledger proyek. Tidak ada dukungan atau "
                "persetujuan penulis sumber yang tersirat.",
                body,
            ),
            Paragraph(
                "Versi lengkap komponen, sumber, manifest, dan riwayat preservasi: "
                "https://doi.org/10.5281/zenodo.22059741",
                body,
            ),
            Paragraph(
                "Batas aksesibilitas: seluruh halaman dapat dicari dan dokumen "
                "mendeklarasikan bahasa id-ID, tetapi PDF belum bertanda semantik "
                "dan peninjauan manusia/penutur asli Bahasa Indonesia belum dicatat.",
                body,
            ),
        ]
    )

    doc = SimpleDocTemplate(
        str(COVER),
        pagesize=A4,
        rightMargin=24 * mm,
        leftMargin=24 * mm,
        topMargin=25 * mm,
        bottomMargin=22 * mm,
        title="Optimisasi Lanjut dan Analisis Konveks - Modul Pendamping Habring Bab 3-9",
        author="Independent Indonesian edition",
        subject="Reader-first partial companion module",
        creator="Deterministic ReportLab build",
        invariant=True,
        pageCompression=1,
    )
    doc.build(story)


def prune_unused_cover_font(page, writer: PdfWriter, font_key: str = "/F1") -> None:
    """Remove ReportLab's empty default-font preamble without harming fallback text."""

    content = ContentStream(page.get_contents(), writer)
    current_font: str | None = None
    font_is_used = False
    for operands, operator in content.operations:
        if operator == b"Tf":
            current_font = str(operands[0])
        elif operator in {b"Tj", b"TJ", b"'", b'"'} and current_font == font_key:
            font_is_used = True
            break
    if font_is_used:
        return

    content.operations = [
        (operands, operator)
        for operands, operator in content.operations
        if not (operator == b"Tf" and str(operands[0]) == font_key)
    ]
    page.replace_contents(content)
    resources = page["/Resources"].get_object()
    fonts = resources.get("/Font")
    if fonts is not None:
        fonts.get_object().pop(NameObject(font_key), None)


def build_reader() -> dict[str, object]:
    inputs = [(title, ROOT / "output" / "pdf" / name) for title, name in UNITS]
    missing = [str(path) for _, path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing reader inputs: " + ", ".join(missing))
    build_cover()

    writer = PdfWriter()
    writer.append(str(COVER), import_outline=False)
    prune_unused_cover_font(writer.pages[0], writer)
    starts: list[tuple[str, int]] = []
    page_cursor = 1
    for title, path in inputs:
        starts.append((title, page_cursor))
        reader = PdfReader(str(path))
        writer.append(reader, import_outline=False)
        page_cursor += len(reader.pages)

    writer.add_outline_item("Halaman pengantar", 0)
    for title, page_index in starts:
        writer.add_outline_item(title, page_index)
    writer.add_metadata(
        {
            "/Title": "Optimisasi Lanjut dan Analisis Konveks - Modul Pendamping Habring Bab 3-9",
            "/Author": "Andreas Habring; independent Indonesian translation/adaptation",
            "/Subject": "Coherent partial reader checkpoint, CC BY 4.0",
            "/Keywords": "Bahasa Indonesia, convex optimization, nonsmooth optimization, CC BY 4.0",
            "/Creator": "Deterministic pypdf/ReportLab build",
            "/Producer": "pypdf",
        }
    )
    writer.root_object[NameObject("/Lang")] = TextStringObject("id-ID")
    writer.page_mode = "/UseOutlines"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("wb") as stream:
        writer.write(stream)

    check = PdfReader(str(OUTPUT))
    expected_pages = 1 + sum(len(PdfReader(str(path)).pages) for _, path in inputs)
    if len(check.pages) != expected_pages:
        raise RuntimeError("Merged reader page count differs")
    return {
        "output": OUTPUT.relative_to(ROOT).as_posix(),
        "bytes": OUTPUT.stat().st_size,
        "sha256": sha256(OUTPUT),
        "pages": len(check.pages),
        "encrypted": check.is_encrypted,
        "language": str(check.trailer["/Root"].get("/Lang")),
        "outline_count": len(check.outline),
        "components": [
            {
                "title": title,
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for title, path in inputs
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build_reader(), ensure_ascii=False, indent=2, sort_keys=True))
