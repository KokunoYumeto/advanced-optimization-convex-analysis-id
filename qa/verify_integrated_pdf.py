#!/usr/bin/env python3
"""Deterministically validate and render the integrated D90 PDF.

This gate proves live-input binding, PDF structure/searchability, embedded-font
properties, safe actions, attachment inventory, page geometry, and a complete
all-page render inventory.  Human-independent visual judgment is recorded in
a separate receipt after the generated contact sheets are inspected.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import pdfplumber
from PIL import Image, ImageDraw, ImageOps
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "output" / "pdf" / "D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf"
BUILD = ROOT / "qa" / "2026-08-27-integrated-pdf-build.json"
REPORT = ROOT / "qa" / "INTEGRATED_PDF_VALIDATION.json"
VISUAL = ROOT / "qa" / "INTEGRATED_PDF_VISUAL_QA.json"
RENDER_DIR = ROOT / "tmp" / "pdfs" / "integrated-final-render"
CONTACT_DIR = ROOT / "tmp" / "pdfs" / "integrated-final-contact-sheets"
RENDER_PREFIX = RENDER_DIR / "page"
EXPECTED_PAGES = 141
EXPECTED_ATTACHMENTS = {"latex-align-css.html", "latex-list-css.html"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def resolve(value):
    return value.get_object() if hasattr(value, "get_object") else value


def outline_count(items) -> int:
    total = 0
    for item in items:
        if isinstance(item, list):
            total += outline_count(item)
        else:
            total += 1
    return total


def clean_exact_directory(path: Path) -> None:
    resolved = path.resolve()
    allowed_parent = (ROOT / "tmp" / "pdfs").resolve()
    require(resolved.parent == allowed_parent, f"refusing unexpected render path: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def font_inventory() -> tuple[list[dict[str, object]], str]:
    completed = subprocess.run(
        ["pdffonts", str(PDF)],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    rows: list[dict[str, object]] = []
    pattern = re.compile(
        r"^(?P<prefix>.+?)\s+(?P<embedded>yes|no)\s+(?P<subset>yes|no)\s+"
        r"(?P<unicode>yes|no)\s+(?P<object>\d+)\s+(?P<generation>\d+)\s*$"
    )
    for line in completed.stdout.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        prefix = match.group("prefix").split()
        rows.append(
            {
                "name": prefix[0],
                "embedded": match.group("embedded") == "yes",
                "subset": match.group("subset") == "yes",
                "unicode_map": match.group("unicode") == "yes",
                "object": int(match.group("object")),
            }
        )
    require(rows, "pdffonts returned no parseable font rows")
    require(all(row["embedded"] for row in rows), "one or more PDF fonts are not embedded")
    require(any(row["unicode_map"] for row in rows), "no PDF font exposes a Unicode map")
    return rows, completed.stdout


def attachment_inventory(root) -> list[dict[str, object]]:
    array = resolve(root.get("/AF") or [])
    rows: list[dict[str, object]] = []
    for reference in array:
        spec = resolve(reference)
        name = str(spec.get("/UF") or spec.get("/F"))
        embedded = resolve(resolve(spec["/EF"])["/F"])
        data = embedded.get_data()
        lower = data.lower()
        require(b"c:/users/" not in lower and b"c:\\users\\" not in lower,
                f"profile locator in embedded attachment {name}")
        rows.append(
            {
                "filename": name,
                "relationship": str(spec.get("/AFRelationship")),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    require({row["filename"] for row in rows} == EXPECTED_ATTACHMENTS,
            f"unexpected associated-file inventory: {rows}")
    return rows


def render_pages() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    clean_exact_directory(RENDER_DIR)
    clean_exact_directory(CONTACT_DIR)
    subprocess.run(
        ["pdftoppm", "-png", "-r", "120", str(PDF), str(RENDER_PREFIX)],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pages = sorted(RENDER_DIR.glob("page-*.png"))
    require(len(pages) == EXPECTED_PAGES, f"rendered {len(pages)} pages, expected {EXPECTED_PAGES}")

    page_rows: list[dict[str, object]] = []
    thumbs: list[tuple[int, Image.Image]] = []
    for number, path in enumerate(pages, start=1):
        with Image.open(path) as opened:
            image = opened.convert("RGB")
        require(image.size == (993, 1404), f"unexpected render geometry on page {number}: {image.size}")
        gray = ImageOps.grayscale(image)
        ink = ImageOps.invert(gray)
        bbox = ink.getbbox()
        require(bbox is not None, f"fully blank rendered page {number}")
        histogram = ink.histogram()
        nonwhite = sum(histogram[1:])
        require(nonwhite > 5000, f"implausibly empty rendered page {number}: {nonwhite}")
        page_rows.append(
            {
                "page": number,
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "pixels": list(image.size),
                "content_bbox": list(bbox),
                "ink_intensity_sum": nonwhite,
            }
        )
        thumb = image.copy()
        thumb.thumbnail((300, 424), Image.Resampling.LANCZOS)
        thumbs.append((number, thumb))

    contact_rows: list[dict[str, object]] = []
    for start in range(0, len(thumbs), 12):
        group = thumbs[start : start + 12]
        sheet = Image.new("RGB", (984, 1880), "white")
        draw = ImageDraw.Draw(sheet)
        for slot, (number, thumb) in enumerate(group):
            column = slot % 3
            row = slot // 3
            x = 18 + column * 322
            y = 18 + row * 465
            draw.text((x, y), f"Halaman {number}", fill="black")
            sheet.paste(thumb, (x, y + 22))
        end = group[-1][0]
        path = CONTACT_DIR / f"pages-{group[0][0]:03d}-{end:03d}.png"
        sheet.save(path, format="PNG", optimize=True)
        contact_rows.append({**identity(path), "pages": [group[0][0], end]})
    return page_rows, contact_rows


def main() -> None:
    require(PDF.is_file(), f"missing integrated PDF: {PDF}")
    require(BUILD.is_file(), f"missing integrated build receipt: {BUILD}")
    build = json.loads(BUILD.read_text(encoding="utf-8"))
    require(build.get("status") == "pass", "integrated PDF build receipt does not pass")
    require(build.get("byte_identical") is True, "integrated PDF builds are not byte-identical")
    require(build["final"]["sha256"] == sha256(PDF), "build receipt does not bind final PDF")
    require(build["final"]["bytes"] == PDF.stat().st_size, "build receipt PDF byte count differs")
    stale_inputs: list[str] = []
    for row in build.get("declared_inputs", []):
        path = ROOT / row["path"]
        if not path.is_file() or path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            stale_inputs.append(row["path"])
    require(not stale_inputs, f"build receipt has stale live inputs: {stale_inputs}")

    raw = PDF.read_bytes().lower()
    require(b"c:/users/" not in raw and b"c:\\users\\" not in raw,
            "profile locator appears in raw PDF bytes")

    reader = PdfReader(str(PDF))
    require(len(reader.pages) == EXPECTED_PAGES, f"PDF has {len(reader.pages)} pages")
    root = reader.trailer["/Root"]
    require(root.get("/Lang") == "id-ID", f"unexpected /Lang: {root.get('/Lang')!r}")
    mark = resolve(root.get("/MarkInfo"))
    require(mark and bool(mark.get("/Marked")), "PDF is not marked")
    structure = resolve(root.get("/StructTreeRoot"))
    require(structure, "PDF has no structure tree")
    for key in ("/K", "/ParentTree", "/RoleMap", "/ClassMap", "/IDTree", "/Namespaces"):
        require(structure.get(key) is not None, f"structure tree lacks {key}")
    parent_tree = resolve(structure["/ParentTree"])
    require(parent_tree.get("/Nums") is not None or parent_tree.get("/Kids") is not None,
            "structure ParentTree has no number-tree content")
    struct_parents = [page.get("/StructParents") for page in reader.pages]
    require(all(value is not None for value in struct_parents), "a page lacks /StructParents")
    require(len({int(value) for value in struct_parents}) == EXPECTED_PAGES,
            "page /StructParents values are not unique")
    tabs = sum(page.get("/Tabs") == "/S" for page in reader.pages)
    require(tabs == EXPECTED_PAGES, f"/Tabs /S appears on {tabs}/{EXPECTED_PAGES} pages")
    require(root.get("/AcroForm") is None, "unexpected AcroForm in reader PDF")
    names = resolve(root.get("/Names") or {})
    require(names.get("/JavaScript") is None and names.get("/EmbeddedFiles") is None,
            "unexpected JavaScript or generic embedded-file name tree")
    open_action = resolve(root.get("/OpenAction") or {})
    require(not open_action or open_action.get("/S") == "/GoTo", "unsafe document open action")
    for page_number, page in enumerate(reader.pages, start=1):
        require(page.get("/AA") is None, f"page {page_number} has additional actions")
        for annotation_ref in page.get("/Annots") or []:
            annotation = resolve(annotation_ref)
            action = resolve(annotation.get("/A") or {})
            require(action.get("/S") not in {"/JavaScript", "/Launch", "/SubmitForm", "/ImportData"},
                    f"unsafe annotation action on page {page_number}")

    metadata = reader.metadata or {}
    require(metadata.get("/Creator") == "OpenAI Codex gpt-5.6-sol, Ultra",
            "exact model provenance missing from PDF metadata")
    require("Bahasa Indonesia" in str(metadata.get("/Title")), "Indonesian edition title missing")
    require(outline_count(reader.outline) >= 14, "implausibly small outline tree")
    attachments = attachment_inventory(root)
    fonts, font_console = font_inventory()

    page_text_rows: list[dict[str, object]] = []
    all_text: list[str] = []
    with pdfplumber.open(PDF) as document:
        for number, page in enumerate(document.pages, start=1):
            text = page.extract_text() or ""
            require(abs(float(page.width) - 595.276) < 0.05, f"page {number} width is not A4")
            require(abs(float(page.height) - 841.89) < 0.05, f"page {number} height is not A4")
            require(len(page.chars) >= 30, f"page {number} has implausibly little searchable text")
            page_text_rows.append(
                {"page": number, "characters": len(page.chars), "extracted_text_characters": len(text)}
            )
            all_text.append(text)
    joined = "\n".join(all_text)
    require(len(joined) >= 300000, f"implausibly short extracted text: {len(joined)}")
    for sentinel in (
        "Asesmen, Laboratorium, dan Proyek Penutup",
        "Ujian tengah kumulatif",
        "Ujian akhir kumulatif",
        "Laboratorium 3: kegagalan lokal dan globalisasi Newton",
        "Laboratorium 4: Sinkhorn log-domain dan sertifikat transportasi",
        "Proyek kapstone: masalah invers komposit yang tahan pencilan",
    ):
        require(sentinel in joined, f"missing source-order sentinel: {sentinel}")

    rendered_pages, contact_sheets = render_pages()
    require(VISUAL.is_file(), f"missing integrated visual-QA receipt: {VISUAL}")
    visual = json.loads(VISUAL.read_text(encoding="utf-8"))
    require(visual.get("status") == "pass", "integrated visual-QA receipt does not pass")
    require(visual.get("artifact", {}).get("sha256") == sha256(PDF),
            "integrated visual-QA receipt does not bind the final PDF")
    require(visual.get("artifact", {}).get("pages") == EXPECTED_PAGES,
            "integrated visual-QA receipt page count differs")
    require(visual.get("method", {}).get("all_pages_inspected") is True,
            "integrated visual-QA receipt does not attest all-page inspection")
    expected_contacts = [
        (row["pages"], row["bytes"], row["sha256"])
        for row in contact_sheets
    ]
    observed_contacts = [
        (row["pages"], row["bytes"], row["sha256"])
        for row in visual.get("contact_sheets", [])
    ]
    require(observed_contacts == expected_contacts,
            "integrated visual-QA contact-sheet identities differ")
    report = {
        "schema": "o015.integrated-pdf-validation.v1",
        "date": "2026-08-28",
        "status": "pass",
        "artifact": {**identity(PDF), "pages": EXPECTED_PAGES},
        "build_receipt": identity(BUILD),
        "verifier": identity(Path(__file__).resolve()),
        "live_input_bindings": len(build.get("declared_inputs", [])),
        "pdf": {
            "language": str(root.get("/Lang")),
            "marked": True,
            "structure_tree": True,
            "parent_tree": True,
            "id_tree": True,
            "role_map": True,
            "class_map": True,
            "namespace_count": len(resolve(structure["/Namespaces"])),
            "unique_page_struct_parents": len(set(int(value) for value in struct_parents)),
            "tabs_s_pages": tabs,
            "outline_entries": outline_count(reader.outline),
            "searchable_text_characters": len(joined),
            "a4_pages": EXPECTED_PAGES,
            "unsafe_actions": 0,
            "form_fields": 0,
            "associated_files": attachments,
        },
        "fonts": {
            "count": len(fonts),
            "all_embedded": all(row["embedded"] for row in fonts),
            "unicode_mapped": sum(bool(row["unicode_map"]) for row in fonts),
            "without_unicode_map": sum(not bool(row["unicode_map"]) for row in fonts),
            "rows": fonts,
            "pdffonts_output_sha256": hashlib.sha256(font_console.encode("utf-8")).hexdigest(),
        },
        "page_text": page_text_rows,
        "render": {
            "tool": "Poppler pdftoppm",
            "dpi": 120,
            "pages": rendered_pages,
            "contact_sheets": contact_sheets,
            "all_pages_rendered": True,
            "visual_judgment_receipt": identity(VISUAL),
            "visual_judgment_pending": False,
        },
        "accessibility_disposition": (
            "Tagged, marked, searchable id-ID PDF with explicit structure and reading-order data. "
            "No PDF/UA conformance claim is made because no pinned conformance validator is available; "
            "semantic HTML and EPUB remain the primary reflow surfaces."
        ),
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": "pass", "pdf": identity(PDF), "contact_sheets": len(contact_sheets)}))


if __name__ == "__main__":
    main()
