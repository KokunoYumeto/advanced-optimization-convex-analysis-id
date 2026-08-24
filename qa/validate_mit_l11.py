#!/usr/bin/env python3
"""Fail-closed validation for MIT 6.253 Lecture 7, PDF pages 86-97."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterator

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT / "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
WITNESS = ROOT / "source/en/mit-11-lecture-7-separation-conjugacy-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-11-kuliah-7-pemisahan-dan-konjugasi-id.md"
CSS = ROOT / "source/id-ID/mit-l11.css"
PREAMBLE = ROOT / "source/id-ID/mit-l11-preamble.tex"
PDF_FILTER = ROOT / "source/id-ID/mit-l11-pdf-filter.lua"
BEFORE_BODY = ROOT / "source/id-ID/mit-l11-before-body.html"
AFTER_BODY = ROOT / "source/id-ID/mit-l11-after-body.html"
BUILDER = ROOT / "qa/build_mit_l11.py"
HTML = ROOT / "output/html/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.html"
PDF = ROOT / "output/pdf/D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.pdf"
VISUAL_QA = ROOT / "qa/MIT_L11_VISUAL_QA.json"
BROWSER_QA = ROOT / "qa/MIT_L11_BROWSER_QA.json"
REREVIEW = ROOT / "qa/MIT_L11_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L11_VALIDATION.json"

MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
LICENSE = "CC BY-NC-SA 4.0"
SOURCE_PAGES = tuple(range(86, 98))
DELIMITER_PAGE = 98

# items, stable display wrappers, figure blocks, semantic panels, source heading
PAGE_COUNTS = {
    86: (6, 0, 0, 0, "LECTURE 7"),
    87: (3, 1, 1, 3, "ADDITIONAL THEOREMS"),
    88: (3, 2, 1, 2, "PROPER POLYHEDRAL SEPARATION"),
    89: (4, 0, 1, 2, "NONVERTICAL HYPERPLANES"),
    90: (4, 1, 0, 0, "NONVERTICAL HYPERPLANE THEOREM"),
    91: (2, 2, 1, 1, "CONJUGATE CONVEX FUNCTIONS"),
    92: (1, 1, 1, 6, "EXAMPLES"),
    93: (5, 3, 0, 0, "CONJUGATE OF CONJUGATE"),
    94: (1, 2, 1, 1, "CONJUGACY THEOREM - VISUALIZATION"),
    95: (1, 4, 0, 0, "CONJUGACY THEOREM"),
    96: (3, 1, 1, 1, "PROOF OF CONJUGACY THEOREM (A), (C)"),
    97: (3, 4, 0, 0, "A COUNTEREXAMPLE"),
}

FIGURE_PANELS = {
    "d90-mit-l11-p087-f001": 3,
    "d90-mit-l11-p088-f001": 2,
    "d90-mit-l11-p089-f001": 2,
    "d90-mit-l11-p091-f001": 1,
    "d90-mit-l11-p092-f001": 6,
    "d90-mit-l11-p094-f001": 1,
    "d90-mit-l11-p096-f001": 1,
}

EVENT_BINDINGS = (
    ("d90-mit-l11-p088-n001", "88", "O015-MIT-SEM-0034"),
    ("d90-mit-l11-p089-n001", "89", "O015-MIT-SEM-0035"),
    ("d90-mit-l11-p090-n001", "90", "O015-MIT-SEM-0036"),
    ("d90-mit-l11-p091-n001", "91", "O015-MIT-SEM-0037"),
    ("d90-mit-l11-p091-n002", "91,95", "O015-MIT-SEM-0040"),
    ("d90-mit-l11-p092-n001", "92", "O015-MIT-SEM-0031"),
    ("d90-mit-l11-p093-n001", "93", "O015-MIT-SEM-0038"),
    ("d90-mit-l11-p094-n001", "94", "O015-MIT-SEM-0039"),
    ("d90-mit-l11-p096-n001", "96", "O015-MIT-SEM-0032"),
    ("d90-mit-l11-p097-n001", "97", "O015-MIT-SEM-0033"),
)
EVENT_IDS = tuple(f"O015-MIT-SEM-{number:04d}" for number in range(31, 41))

PAGE_TEXT = {
    86: (258, "5bb20e6003c022244d8baeae9365ca1e85571b9021b7ebbca76bfb0068ac4288"),
    87: (934, "6d34b9c20adbcab3d9b94f51255e380495c884082496d49333063ffa56b0d7a6"),
    88: (918, "2f2b8d01a7f09944b217e000a71b24dd0b77258159ef40a5f697dbd5eaa16fe4"),
    89: (980, "7a386ae891bcf77999b700d0561b5d9b05b61ddc2742c5aeeaf6ec6a7d3597ff"),
    90: (1_148, "f998269d35b74761acae48995eaf7e10c461e1b7d030105a3c3fea2a8465d7b1"),
    91: (871, "21fec334f9e91b1d6b25fe29c80078d1c650ca0dbb05e6696e2065b8b101f70e"),
    92: (1_150, "f670d867bbc0bcf5f2fb85148b6aef06f5d32961c8ab1985d392e2d59a006f47"),
    93: (740, "7abcde78433beca5672e4b117c096e3a69cd8e9a4f0d37705b6c3f380dd83bca"),
    94: (1_185, "e09d900a215c55ae6f3b96f1b66d312c0b73fc372df5908cbaf6ab0cc09701c4"),
    95: (841, "77d25710689b28c92637366a852b0adc2a9dd1cbaefd60675961a4f3cbecfa11"),
    96: (1_370, "d9768a6d5c70120083db44722b2430942a6bfcded41baa053bd58dbc0cb59f0e"),
    97: (539, "d91b7761241b77874e9a3b2a85b8e702a068a0583b70946f52ad64089ff53c1f"),
    98: (247, "089e122ba925acf0cb958abb5cc7a1949a0074e421f1317d94d5567e07a53247"),
}
COMBINED_TEXT = (10_934, "d47d9562b3f7987cb39372915cfcf3ee0904e67d432f00f3ef7beaa84be84564")

EXPECTED = {
    SOURCE_PDF: (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    WITNESS: (23_801, "625efb8801d24c270d2bf851bf1c7fb27cb307146742d7cbddc00b5cb5873c8c"),
    TARGET: (25_023, "f908901609e1a1e6091734b55ba63b980f491dd5a5e4e813621816cbceb1c32b"),
    CSS: (2_976, "7f1418005edaf4d9d263d528af630357f24c55abb930be9b27f9ac9d170c522e"),
    PREAMBLE: (1_891, "b26fea2b2410ab3a9aea8102784e2532436f9062a95ed1a0c2b3a27bf69c89f1"),
    PDF_FILTER: (888, "fdb42ee5c762b91e9a38cb2425ff6cf322f97476e72cb2b99b8a0dc49912c750"),
    BEFORE_BODY: (96, "c02ee74ffa764e276af676187a9391e17dcb6703526625db3bd9667fc5ef910c"),
    AFTER_BODY: (170, "07c10aa60b71a729577ae7bf3add87057986aef55128b71591ca9e02169af80b"),
    BUILDER: (4_058, "84d246ac5c11a84dc43e3ea33f9b553a5df01c5e3765633b03500ca941abf8f1"),
}
EXPECTED_BUILD = {
    "html": (96_216, "19dd1f9aeb65e951089a4501fefa65761448f86f21ee7024ccfde9a71e5b988d"),
    "pdf": (89_771, "82d39fa34f8e743204ba88b3b91f50d4a549bb7b0b79e529ed0bec1a51f16bc8"),
}
FORMULA_SHA256 = {
    "witness": "bc3004045a0901dc03b2f4ae8bbaf9f8cb92846654df5c4a8137522d8da04bc4",
    "target": "c3bcd768f0f82ec64a6af7843f28c21a588bfb5390bca74ce1881d7d5e839d9b",
}
MATH_NODES = {"witness": 186, "target": 204}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def ast(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["pandoc", str(path), "--from=markdown+fenced_divs+yaml_metadata_block", "--to=json"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    if result.stderr:
        raise RuntimeError(f"pandoc AST warning for {path.name}: {result.stderr.decode('utf-8', 'replace')}")
    return json.loads(result.stdout.decode("utf-8"))


def div_records(document: Any, class_name: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in walk(document):
        if node.get("t") != "Div":
            continue
        identifier, classes, attrs = node["c"][0]
        if class_name in classes:
            records.append({"id": identifier, "attrs": dict(attrs), "blocks": node["c"][1]})
    return records


def source_topology(path: Path, correction_class: str) -> dict[str, Any]:
    document = ast(path)
    display_math = [
        re.sub(r"\s+", "", node["c"][1].strip())
        for node in walk(document)
        if node.get("t") == "Math" and node["c"][0]["t"] == "DisplayMath"
    ]
    correction_records = div_records(document, correction_class)
    return {
        "pages": div_records(document, "source-page"),
        "items": div_records(document, "source-item"),
        "displays": div_records(document, "source-display"),
        "figures": div_records(document, "source-figure"),
        "corrections": correction_records,
        "display_math": display_math,
        "math_nodes": sum(node.get("t") == "Math" for node in walk(document)),
        "images": sum(node.get("t") == "Image" for node in walk(document)),
        "code_blocks": sum(node.get("t") == "CodeBlock" for node in walk(document)),
        "tables": sum(node.get("t") == "Table" for node in walk(document)),
        "links": sum(node.get("t") == "Link" for node in walk(document)),
        "disallowed_divs": [
            node["c"][0][0]
            for node in walk(document)
            if node.get("t") == "Div"
            and set(node["c"][0][1]) & {"exercise", "hint", "answer", "solution", "code", "interactive"}
        ],
    }


def expected_pages() -> list[tuple[str, str, str]]:
    return [(str(order), str(page), f"d90-mit-l11-p{page:03d}") for order, page in enumerate(SOURCE_PAGES, 1)]


def expected_items() -> list[tuple[int, int, str]]:
    return [
        (page, order, f"d90-mit-l11-p{page:03d}-i{order:03d}")
        for page in SOURCE_PAGES
        for order in range(1, PAGE_COUNTS[page][0] + 1)
    ]


def expected_displays() -> list[tuple[int, int, str]]:
    return [
        (page, order, f"d90-mit-l11-p{page:03d}-d{order:03d}")
        for page in SOURCE_PAGES
        for order in range(1, PAGE_COUNTS[page][1] + 1)
    ]


def expected_figures() -> list[tuple[int, str]]:
    return [(int(re.search(r"p(\d{3})", identifier).group(1)), identifier) for identifier in FIGURE_PANELS]


def correction_binding(record: dict[str, Any]) -> tuple[str, str, str]:
    attrs = record["attrs"]
    locator = attrs.get("data-source-page") or attrs.get("data-source-pages") or ""
    return record["id"], locator, attrs.get("data-correction-event", "")


def validate_topology(label: str, top: dict[str, Any], errors: list[str]) -> None:
    actual_pages = [
        (record["attrs"].get("data-source-order"), record["attrs"].get("data-source-page"), record["id"])
        for record in top["pages"]
    ]
    check(actual_pages == expected_pages(), f"{label} source-page/order map differs", errors)
    actual_items = [
        (int(record["attrs"].get("data-source-page", -1)), int(record["attrs"].get("data-source-order", -1)), record["id"])
        for record in top["items"]
    ]
    check(actual_items == expected_items(), f"{label} source-item map differs", errors)
    actual_displays = [
        (int(record["attrs"].get("data-source-page", -1)), int(record["attrs"].get("data-display-order", -1)), record["id"])
        for record in top["displays"]
    ]
    check(actual_displays == expected_displays(), f"{label} source-display map differs", errors)
    actual_figures = [(int(record["attrs"].get("data-source-page", -1)), record["id"]) for record in top["figures"]]
    check(actual_figures == expected_figures(), f"{label} source-figure map differs", errors)
    check(
        all(record["attrs"].get("data-figure-disposition") == "omitted-source-graphic" for record in top["figures"]),
        f"{label} source-figure rights disposition differs",
        errors,
    )
    for record in top["figures"]:
        check(
            int(record["attrs"].get("data-panel-count", -1)) == FIGURE_PANELS.get(record["id"]),
            f"{label} panel count differs for {record['id']}",
            errors,
        )
    check(
        [correction_binding(record) for record in top["corrections"]] == list(EVENT_BINDINGS),
        f"{label} correction traversal/binding differs",
        errors,
    )
    identifiers = [
        record["id"]
        for key in ("pages", "items", "displays", "figures", "corrections")
        for record in top[key]
    ]
    check(len(identifiers) == len(set(identifiers)), f"duplicate {label} semantic ID", errors)
    check(
        (len(top["pages"]), len(top["items"]), len(top["displays"]), len(top["figures"]), sum(FIGURE_PANELS.values()))
        == (12, 36, 21, 7, 16),
        f"{label} total topology differs",
        errors,
    )
    check(len(top["corrections"]) == 10, f"{label} correction count differs", errors)
    check(Counter(binding[2] for binding in map(correction_binding, top["corrections"])) == Counter(EVENT_IDS), f"{label} correction set differs", errors)
    check(len(top["display_math"]) == 21, f"{label} display-formula count differs", errors)
    formula_hash = hashlib.sha256("\n".join(top["display_math"]).encode("utf-8")).hexdigest()
    check(formula_hash == FORMULA_SHA256[label], f"{label} display-formula sequence differs", errors)
    check(top["math_nodes"] == MATH_NODES[label], f"{label} math-node count differs", errors)
    check(top["images"] == 0, f"{label} contains an image node", errors)
    check(top["code_blocks"] == 0 and top["tables"] == 0 and top["links"] == 0, f"{label} contains code, table, or link surfaces", errors)
    check(not top["disallowed_divs"], f"{label} contains exercise/solution/code/interactive surfaces", errors)


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.links: list[str] = []
        self.lang = ""
        self.main_ids: list[str] = []
        self.skip_target = ""
        self.source_pages: list[str] = []
        self.source_items: list[str] = []
        self.source_displays: list[str] = []
        self.source_figures: list[str] = []
        self.images = 0
        self.media = 0
        self.interactive = 0
        self.math = 0
        self.display_math = 0
        self.headings: Counter[str] = Counter()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        identifier = values.get("id", "")
        if tag == "html":
            self.lang = values.get("lang", "")
        if identifier:
            self.ids.append(identifier)
        if tag == "a":
            href = values.get("href", "")
            if href.startswith("#"):
                self.fragments.append(href[1:])
            elif href:
                self.links.append(href)
            if "skip-link" in classes:
                self.skip_target = href
        if tag == "main":
            self.main_ids.append(identifier)
        if tag == "img":
            self.images += 1
        if tag in {"img", "picture", "svg", "image", "video", "audio", "canvas", "iframe", "object", "embed"}:
            self.media += 1
        if tag in {"button", "input", "select", "textarea", "form"}:
            self.interactive += 1
        if tag == "math":
            self.math += 1
            self.display_math += values.get("display") == "block"
        if re.fullmatch(r"h[1-6]", tag):
            self.headings[tag] += 1
        if "source-page" in classes:
            self.source_pages.append(identifier)
        if "source-item" in classes:
            self.source_items.append(identifier)
        if "source-display" in classes:
            self.source_displays.append(identifier)
        if "source-figure" in classes:
            self.source_figures.append(identifier)


def validate_html(path: Path, errors: list[str]) -> tuple[SurfaceParser, list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    parser = SurfaceParser()
    parser.feed(text)
    duplicates = sorted(identifier for identifier, count in Counter(parser.ids).items() if count > 1)
    unresolved = sorted(set(parser.fragments) - set(parser.ids))
    check(parser.lang == "id-ID" and parser.main_ids == ["main-content"], "HTML language or main landmark differs", errors)
    check(parser.headings == Counter({"h1": 1, "h2": 12}), f"HTML heading topology differs: {parser.headings}", errors)
    check(parser.source_pages == [record[2] for record in expected_pages()], "HTML source-page ID order differs", errors)
    check(parser.source_items == [record[2] for record in expected_items()], "HTML source-item ID order differs", errors)
    check(parser.source_displays == [record[2] for record in expected_displays()], "HTML source-display ID order differs", errors)
    check(parser.source_figures == [record[1] for record in expected_figures()], "HTML source-figure ID order differs", errors)
    check(parser.math == 204 and parser.display_math == 21, "HTML MathML topology differs", errors)
    check(parser.images == 0 and parser.media == 0 and parser.interactive == 0, "HTML contains image, media, embed, or form surfaces", errors)
    lowered = text.lower()
    check(not any(token in lowered for token in ("data:image", "<script", "<picture", "<svg", "<iframe")), "HTML contains embedded source-image or active content", errors)
    check(parser.skip_target == "#d90-mit-l11-p086", f"HTML skip-link target differs: {parser.skip_target}", errors)
    check(not duplicates and not unresolved, f"HTML ID closure differs: duplicate={duplicates}, unresolved={unresolved}", errors)
    check(not parser.links, f"HTML contains unexpected external links: {parser.links}", errors)
    check("Kuliah 7: Pemisahan, Hiperbidang Nonvertikal, dan Konjugasi" in text, "HTML title differs", errors)
    return parser, duplicates, unresolved


def image_rows(path: Path) -> list[str]:
    result = subprocess.run(["pdfimages", "-list", str(path)], cwd=ROOT, capture_output=True, text=True, check=True)
    return [line for line in result.stdout.splitlines() if re.match(r"^\s*\d+\s+\d+\s+", line)]


def pdf_uris(reader: PdfReader) -> set[str]:
    uris: set[str] = set()
    for page in reader.pages:
        annotations = page.get("/Annots")
        for annotation_ref in annotations.get_object() if annotations else []:
            annotation = annotation_ref.get_object()
            action = annotation.get("/A") or {}
            if hasattr(action, "get_object"):
                action = action.get_object()
            if action.get("/URI"):
                uris.add(str(action["/URI"]))
    return uris


def validate_pdf(path: Path, errors: list[str]) -> dict[str, Any]:
    reader = PdfReader(path)
    root = reader.trailer["/Root"]
    check(len(reader.pages) == 6, f"PDF page count {len(reader.pages)} != 6", errors)
    check(str(root.get("/Lang") or "") == "id-ID", f"PDF /Lang differs: {root.get('/Lang')}", errors)
    check(not reader.is_encrypted, "PDF is encrypted", errors)
    check((reader.metadata or {}).get("/Producer") == f"{MODEL} - user-directed production assistance", "PDF producer provenance differs", errors)
    names_ref = root.get("/Names")
    names = names_ref.get_object() if names_ref else {}
    check("/EmbeddedFiles" not in names, "PDF contains an embedded file", errors)
    check("/JavaScript" not in names and "/AA" not in root, "PDF catalog contains active content", errors)
    open_action = root.get("/OpenAction")
    if open_action is not None and hasattr(open_action, "get_object"):
        open_action = open_action.get_object()
    check(not isinstance(open_action, dict) or open_action.get("/S") != "/JavaScript", "PDF open action is JavaScript", errors)
    check(not (reader.get_fields() or {}), "PDF exposes form fields", errors)
    fonts: dict[str, bool] = {}
    page_sizes: list[list[float]] = []
    extracted: list[str] = []
    active_annotations: list[str] = []
    for page_number, page in enumerate(reader.pages, 1):
        page_sizes.append([round(float(page.mediabox.width), 3), round(float(page.mediabox.height), 3)])
        check(abs(float(page.mediabox.width) - 595.276) < 0.02 and abs(float(page.mediabox.height) - 841.89) < 0.02, f"PDF page {page_number} is not A4", errors)
        resources = page.get("/Resources") or {}
        if hasattr(resources, "get_object"):
            resources = resources.get_object()
        font_map = resources.get("/Font") or {}
        if hasattr(font_map, "get_object"):
            font_map = font_map.get_object()
        for name, ref in font_map.items():
            fonts[str(name)] = bool(ref.get_object().get("/ToUnicode"))
        extracted.append(page.extract_text() or "")
        annotations = page.get("/Annots")
        for annotation_ref in annotations.get_object() if annotations else []:
            annotation = annotation_ref.get_object()
            action = annotation.get("/A") or {}
            if hasattr(action, "get_object"):
                action = action.get_object()
            if action.get("/S") == "/JavaScript" or annotation.get("/AA"):
                active_annotations.append(f"page-{page_number}")
    check(bool(fonts) and all(fonts.values()), f"PDF ToUnicode coverage differs: {fonts}", errors)
    check(not active_annotations, f"PDF contains active annotations: {active_annotations}", errors)
    output_images = image_rows(path)
    check(not output_images, "output PDF contains a raster source-image XObject", errors)
    searchable = "\n".join(extracted)
    for phrase in (
        "Kuliah 7 - Garis Besar Kuliah",
        "Teorema Tambahan",
        "Teorema Hiperbidang Nonvertikal",
        "Fungsi Konjugat Konveks",
        "Bukti Teorema Konjugasi",
        "Sebuah Kontra-Contoh",
        "Halaman sumber 97.",
    ):
        check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)
    page_chars = [len(re.sub(r"\s+", "", text)) for text in extracted]
    total_chars = sum(page_chars)
    check(total_chars >= 12_000, f"searchable PDF text is unexpectedly short: {total_chars}", errors)
    check(len(page_chars) == 6 and min(page_chars, default=0) >= 700, f"PDF has an unfilled or text-empty page: {page_chars}", errors)
    return {
        "pages": len(reader.pages),
        "page_size_points": page_sizes,
        "lang": str(root.get("/Lang") or ""),
        "searchable_text_chars": total_chars,
        "searchable_chars_per_page": page_chars,
        "page_filled": len(page_chars) == 6 and min(page_chars, default=0) >= 700,
        "encrypted": reader.is_encrypted,
        "tagged": "/StructTreeRoot" in root,
        "images": len(output_images),
        "to_unicode_all_fonts": bool(fonts) and all(fonts.values()),
        "uri_annotations": sorted(pdf_uris(reader)),
    }


def validate_visual(path: Path, errors: list[str]) -> dict[str, Any]:
    visual = json.loads(path.read_text(encoding="utf-8"))
    check(visual.get("schema") == "o015-mit-l11-visual-qa-v1", "visual QA schema differs", errors)
    check(visual.get("result") == "pass", "visual QA is not pass", errors)
    artifact = visual.get("artifact") or {}
    check(
        artifact.get("path") == PDF.relative_to(ROOT).as_posix()
        and (artifact.get("bytes"), artifact.get("sha256")) == EXPECTED_BUILD["pdf"],
        "visual QA does not bind deterministic PDF",
        errors,
    )
    structure = visual.get("pdf_structure") or {}
    check(
        structure.get("lang") == "id-ID"
        and structure.get("tagged") is False
        and structure.get("encrypted") is False
        and structure.get("form_fields") == 0
        and structure.get("javascript") is False
        and structure.get("embedded_files") is False
        and structure.get("image_xobjects") == 0
        and structure.get("link_annotations") == 12
        and "semantic HTML is the accessible checkpoint surface" in structure.get("accessibility_disposition", "")
        and "tagged PDF" in structure.get("accessibility_disposition", ""),
        "visual QA PDF structure differs",
        errors,
    )
    searchability = visual.get("searchability") or {}
    check(
        searchability.get("pdftotext_layout_chars", 0) >= 18_000
        and bool(re.fullmatch(r"[0-9a-f]{64}", searchability.get("pdftotext_layout_sha256", "")))
        and searchability.get("title_found") is True
        and searchability.get("corrected_proof_found") is True
        and searchability.get("counterexample_found") is True
        and searchability.get("to_unicode_text_available") is True,
        "visual QA searchability evidence differs",
        errors,
    )
    inspection = visual.get("inspection") or {}
    check(
        inspection.get("all_pages_inspected_at_original_render_resolution") is True
        and inspection.get("reader_pages") == 6
        and inspection.get("page_size") == "A4"
        and inspection.get("front_matter_is_a_deliberate_complete_first_page") is True
        and inspection.get("lecture_outline_starts_intact_on_page_2") is True
        and inspection.get("page_96_concluding_inequality_and_contradiction_are_kept_together") is True
        and inspection.get("closing_counterexample_is_not_split") is True,
        "visual QA page-inspection declaration differs",
        errors,
    )
    for key in (
        "clipping",
        "overlap",
        "truncated_text",
        "orphaned_outline_items",
        "isolated_proof_conclusions",
        "broken_glyphs",
        "unreadable_formulas",
        "source_graphic_bytes",
    ):
        check(inspection.get(key) == 0, f"visual QA {key} differs", errors)

    render = visual.get("render") or {}
    declared_pages = render.get("pages") or []
    check(render.get("dpi") == 160, "visual QA render DPI differs", errors)
    check(
        [row.get("page") for row in declared_pages] == list(range(1, 7))
        and all(isinstance(row.get("bytes"), int) and row["bytes"] > 0 for row in declared_pages)
        and all(bool(re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", ""))) for row in declared_pages),
        "visual QA render inventory differs",
        errors,
    )
    with tempfile.TemporaryDirectory(prefix="o015-mit-l11-visual-evidence-") as temp:
        output_prefix = Path(temp) / "page"
        subprocess.run(
            ["pdftoppm", "-png", "-r", "160", str(PDF), str(output_prefix)],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        rendered = []
        for page_number, rendered_path in enumerate(
            sorted(Path(temp).glob("page-*.png"), key=lambda item: int(re.search(r"(\d+)$", item.stem).group(1))),
            1,
        ):
            rendered.append({
                "page": page_number,
                "bytes": rendered_path.stat().st_size,
                "sha256": digest(rendered_path),
            })
    check(rendered == declared_pages, "visual QA render hashes do not reproduce", errors)
    return visual


def validate_browser(path: Path, errors: list[str]) -> dict[str, Any]:
    browser = json.loads(path.read_text(encoding="utf-8"))
    check(browser.get("schema") == "o015-mit-l11-browser-qa-v1", "browser QA schema differs", errors)
    check(browser.get("result") == "pass", "browser QA is not pass", errors)
    artifact = browser.get("artifact") or {}
    check(
        artifact.get("path") == HTML.relative_to(ROOT).as_posix()
        and (artifact.get("bytes"), artifact.get("sha256")) == EXPECTED_BUILD["html"],
        "browser QA does not bind deterministic HTML",
        errors,
    )
    semantics = browser.get("semantics") or {}
    check(
        semantics.get("lang") == "id-ID"
        and semantics.get("main_landmarks") == 1
        and semantics.get("source_pages") == 12
        and semantics.get("source_items") == 36
        and semantics.get("source_figures") == 7
        and semantics.get("source_displays") == 21
        and semantics.get("edition_corrections") == 10
        and semantics.get("mathml_nodes") == 204
        and semantics.get("display_mathml_nodes") == 21
        and semantics.get("duplicate_ids") == []
        and semantics.get("unresolved_fragments") == []
        and semantics.get("interactive_controls_or_embeds") == 0
        and semantics.get("images") == 0,
        "browser semantic-structure evidence differs",
        errors,
    )
    navigation = browser.get("navigation") or {}
    check(
        navigation.get("skip_link_href") == "#d90-mit-l11-p086"
        and navigation.get("target_exists") is True
        and navigation.get("click_resolved_hash") == "#d90-mit-l11-p086"
        and isinstance(navigation.get("target_top_after_activation_px"), (int, float))
        and 0 <= navigation["target_top_after_activation_px"] <= 32,
        "browser navigation evidence differs",
        errors,
    )
    desktop = browser.get("desktop") or {}
    check(
        desktop.get("viewport") == {"width": 1280, "height": 720}
        and desktop.get("document_scroll_width") == 1265
        and desktop.get("horizontal_overflow") is False
        and desktop.get("visual_inspection") == "pass",
        "browser desktop evidence differs",
        errors,
    )
    mobile = browser.get("mobile") or {}
    check(
        mobile.get("viewport") == {"width": 390, "height": 844}
        and mobile.get("document_scroll_width") == mobile.get("body_scroll_width") == 375
        and 360 <= mobile.get("main_width", 0) <= 375
        and mobile.get("source_page_width") == mobile.get("main_width")
        and mobile.get("horizontal_overflow") is False
        and mobile.get("overflowing_elements") == []
        and mobile.get("wide_math_containers") == []
        and mobile.get("toc_columns") == 1
        and mobile.get("visual_inspection") == "pass",
        "browser mobile evidence differs",
        errors,
    )
    check(browser.get("console_findings") == [], "browser console findings are nonempty", errors)
    return browser


def validate_rereview(path: Path, errors: list[str]) -> dict[str, Any]:
    before = len(errors)
    text = path.read_text(encoding="utf-8")
    check(
        "**Independent rereview result: PASS.**" in text,
        "independent rereview is not PASS",
        errors,
    )
    check(
        all(f"**P{level}: 0**" in text for level in (1, 2, 3))
        and "No actionable findings remain" in text,
        "independent rereview does not close severity counts",
        errors,
    )
    for bound in (SOURCE_PDF, WITNESS, TARGET):
        check(digest(bound) in text, f"independent rereview lacks {bound.name} binding", errors)
    for event_id in EVENT_IDS:
        check(event_id in text, f"independent rereview lacks {event_id}", errors)
    return {"disposition": "pass" if len(errors) == before else "fail", **identity(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=("provisional", "strict-final"))
    args = parser.parse_args()

    errors: list[str] = []
    for path, expected in EXPECTED.items():
        check(path.is_file(), f"missing required file: {path.relative_to(ROOT)}", errors)
        if path.is_file():
            check((path.stat().st_size, digest(path)) == expected, f"identity mismatch: {path.relative_to(ROOT)}", errors)

    evidence_paths = {"visual": VISUAL_QA, "browser": BROWSER_QA, "rereview": REREVIEW}
    evidence: dict[str, Any] = {
        "stage": args.stage,
        "required_for_strict_final": ["visual", "browser", "rereview"],
        **{
            name: ({"status": "present", **identity(path)} if path.is_file() else {"status": "not_present"})
            for name, path in evidence_paths.items()
        },
    }
    if args.stage == "strict-final":
        for name, path in evidence_paths.items():
            check(path.is_file(), f"strict-final evidence missing: {name}", errors)

    source_text_records: dict[str, dict[str, Any]] = {}
    combined_record: dict[str, Any] = {}
    topologies: dict[str, dict[str, Any]] = {}
    html_parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    pdf_observed: dict[str, Any] = {}
    rebuilds: list[dict[str, tuple[int, str]]] = []
    canonical: dict[str, Any] = {"status": "not_checked"}

    if not errors or args.stage == "provisional":
        try:
            source_reader = PdfReader(SOURCE_PDF)
            metadata = source_reader.metadata or {}
            check(len(source_reader.pages) == 340, "authority PDF page count is not 340", errors)
            check(not source_reader.is_encrypted, "authority PDF is encrypted", errors)
            check(metadata.get("/Title") == "6.253 Convex Analysis and Optimization, Complete Lecture Notes", "authority PDF title differs", errors)
            check(metadata.get("/Author") == "Bertsekas, Dimitri", "authority PDF author differs", errors)
            for page in range(86, 99):
                raw = subprocess.run(
                    ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(page), "-l", str(page), str(SOURCE_PDF), "-"],
                    cwd=ROOT,
                    capture_output=True,
                    check=True,
                ).stdout
                observed = (len(raw), hashlib.sha256(raw).hexdigest())
                source_text_records[str(page)] = {"bytes": observed[0], "sha256": observed[1]}
                check(observed == PAGE_TEXT[page], f"authority page {page} text fingerprint differs", errors)
                text = raw.decode("utf-8", "replace")
                if page in PAGE_COUNTS:
                    check(PAGE_COUNTS[page][4] in text, f"authority page {page} heading differs", errors)
                else:
                    check("LECTURE 8" in text and "LECTURE OUTLINE" in text, "page 98 is not the clean Lecture 8 delimiter", errors)
            combined = subprocess.run(
                ["pdftotext", "-layout", "-enc", "UTF-8", "-f", "86", "-l", "97", str(SOURCE_PDF), "-"],
                cwd=ROOT,
                capture_output=True,
                check=True,
            ).stdout
            combined_record = {"bytes": len(combined), "sha256": hashlib.sha256(combined).hexdigest()}
            check((combined_record["bytes"], combined_record["sha256"]) == COMBINED_TEXT, "authority pages 86-97 combined fingerprint differs", errors)
            for source_page_number, page in enumerate(source_reader.pages[85:98], 86):
                annotations = page.get("/Annots")
                check(not (annotations.get_object() if annotations else []), f"authority page {source_page_number} contains an annotation", errors)
            check(not (source_reader.get_fields() or {}), "authority PDF exposes form fields", errors)
            source_root = source_reader.trailer["/Root"]
            source_names_ref = source_root.get("/Names")
            source_names = source_names_ref.get_object() if source_names_ref else {}
            check("/JavaScript" not in source_names and "/AA" not in source_root, "authority PDF contains active content", errors)

            witness_text = WITNESS.read_text(encoding="utf-8")
            target_text = TARGET.read_text(encoding="utf-8")
            for label, text in (("witness", witness_text), ("target", target_text)):
                check(MODEL in text and text.count(MODEL) == 1, f"{label} model identification differs", errors)
                check(LICENSE in text, f"{label} license statement differs", errors)
                lowered = text.lower()
                check("![" not in text and "<img" not in lowered and "data:image" not in lowered, f"{label} embeds source-image bytes", errors)
                check(not any(token in lowered for token in ("<script", "<iframe", "<form", "<input", "<button")), f"{label} contains active or interactive markup", errors)
            check("no endorsement by the source author, MIT, or MIT OpenCourseWare" in witness_text, "witness nonendorsement differs", errors)
            check("tanpa dukungan tersirat" in target_text and "bukan penulis sumber, pemberi lisensi, atau wakil MIT" in target_text, "target nonendorsement differs", errors)
            check("Seven figure blocks containing sixteen separately meaningful panels" in witness_text, "witness figure-panel disclosure differs", errors)
            check("Tujuh blok gambar dengan enam belas panel" in target_text, "target figure-panel disclosure differs", errors)
            check("tidak mempunyai latihan peserta didik, petunjuk, jawaban, solusi latihan, kode, data, tautan, anotasi, widget, media, atau permukaan interaktif" in target_text, "target zero-surface disclosure differs", errors)

            topologies = {
                "witness": source_topology(WITNESS, "source-defect-notice"),
                "target": source_topology(TARGET, "edition-correction"),
            }
            for label, topology in topologies.items():
                validate_topology(label, topology, errors)
            for key in ("pages", "items", "displays", "figures", "corrections"):
                check(
                    [record["id"] for record in topologies["witness"][key]] == [record["id"] for record in topologies["target"][key]],
                    f"witness-target {key} stable-ID order differs",
                    errors,
                )

            with tempfile.TemporaryDirectory(prefix="o015-mit-l11-validation-") as temp:
                temp_root = Path(temp)
                for label in ("a", "b"):
                    out = temp_root / label
                    out.mkdir()
                    html = out / HTML.name
                    pdf = out / PDF.name
                    built = subprocess.run(
                        [sys.executable, str(BUILDER), "--html-output", str(html), "--pdf-output", str(pdf)],
                        cwd=ROOT,
                        capture_output=True,
                        check=True,
                    )
                    check(not built.stderr, f"builder {label} emitted warnings: {built.stderr.decode('utf-8', 'replace')}", errors)
                    build_record = json.loads(built.stdout.decode("utf-8"))
                    check(build_record.get("result") == "pass", f"builder {label} did not report pass", errors)
                    rebuilds.append({"html": (html.stat().st_size, digest(html)), "pdf": (pdf.stat().st_size, digest(pdf))})
                check(len(rebuilds) == 2 and rebuilds[0] == rebuilds[1] == EXPECTED_BUILD, f"deterministic rebuild identities differ: {rebuilds}", errors)
                html_parser, duplicate_ids, unresolved = validate_html(temp_root / "a" / HTML.name, errors)
                pdf_observed = validate_pdf(temp_root / "a" / PDF.name, errors)

            if HTML.exists() != PDF.exists():
                canonical = {"status": "incomplete_pair"}
                errors.append("canonical L11 output pair is incomplete")
            elif HTML.exists() and PDF.exists():
                canonical = {"status": "bound", "html": identity(HTML), "pdf": identity(PDF)}
                check((HTML.stat().st_size, digest(HTML)) == EXPECTED_BUILD["html"], "canonical HTML differs from deterministic build", errors)
                check((PDF.stat().st_size, digest(PDF)) == EXPECTED_BUILD["pdf"], "canonical PDF differs from deterministic build", errors)
                validate_html(HTML, errors)
                validate_pdf(PDF, errors)

            if args.stage == "strict-final" and all(path.is_file() for path in evidence_paths.values()):
                before = len(errors)
                visual = validate_visual(VISUAL_QA, errors)
                evidence["visual"] = {"status": "validated" if len(errors) == before else "invalid", "result": visual.get("result"), **identity(VISUAL_QA)}
                before = len(errors)
                browser = validate_browser(BROWSER_QA, errors)
                evidence["browser"] = {"status": "validated" if len(errors) == before else "invalid", "result": browser.get("result"), **identity(BROWSER_QA)}
                rereview = validate_rereview(REREVIEW, errors)
                evidence["rereview"] = {"status": "validated" if rereview["disposition"] == "pass" else "invalid", **rereview}
        except Exception as exc:
            errors.append(f"validation exception: {type(exc).__name__}: {exc}")

    result = "pass" if not errors else "fail"
    release_ready = (
        args.stage == "strict-final"
        and result == "pass"
        and canonical.get("status") == "bound"
        and all(evidence.get(name, {}).get("status") == "validated" for name in ("visual", "browser", "rereview"))
    )
    report = {
        "schema": "o015-mit-l11-validation-v1",
        "validation_epoch": "2026-08-24",
        "stage": args.stage,
        "result": result,
        "release_ready": release_ready,
        "boundary": {
            "source_pdf_pages": list(SOURCE_PAGES),
            "next_source_page": DELIMITER_PAGE,
            "next_heading": "LECTURE 8 - LECTURE OUTLINE",
            "source_pages": 12,
            "source_items": 36,
            "source_display_wrappers": 21,
            "display_formula_blocks": 21,
            "source_figures": 7,
            "source_figure_panels": 16,
            "copied_source_graphics": 0,
            "exercises": 0,
            "hints": 0,
            "answers": 0,
            "solutions": 0,
            "code_surfaces": 0,
            "interactive_surfaces": 0,
        },
        "files": [identity(path) for path in EXPECTED if path.exists()],
        "authority": {
            "source_page_text": source_text_records,
            "combined_pages_86_97": combined_record,
        },
        "topology": {
            "page_counts": {
                str(page): {
                    "items": row[0],
                    "display_wrappers": row[1],
                    "figure_blocks": row[2],
                    "figure_panels": row[3],
                    "heading": row[4],
                }
                for page, row in PAGE_COUNTS.items()
            },
            "figure_panel_map": FIGURE_PANELS,
        },
        "formula_inventory": {
            label: {
                "display_blocks": len(topology.get("display_math", [])),
                "sequence_sha256": hashlib.sha256("\n".join(topology.get("display_math", [])).encode("utf-8")).hexdigest() if topology else None,
                "intentional_cross_language_difference": True,
            }
            for label, topology in topologies.items()
        },
        "correction_bindings": [
            {"notice_id": notice_id, "source_page_locator": locator, "event_id": event_id}
            for notice_id, locator, event_id in EVENT_BINDINGS
        ],
        "build": {
            "command": "python qa/build_mit_l11.py --html-output <html> --pdf-output <pdf>",
            "deterministic_rebuilds": 2,
            "rebuild_identities": rebuilds,
            "expected": EXPECTED_BUILD,
            "canonical": canonical,
        },
        "evidence": evidence,
        "html": {
            "lang": html_parser.lang,
            "main_ids": html_parser.main_ids,
            "headings": dict(sorted(html_parser.headings.items())),
            "source_pages": len(html_parser.source_pages),
            "source_items": len(html_parser.source_items),
            "source_displays": len(html_parser.source_displays),
            "source_figures": len(html_parser.source_figures),
            "math_nodes": html_parser.math,
            "display_math_nodes": html_parser.display_math,
            "images": html_parser.images,
            "media_or_embeds": html_parser.media,
            "form_controls": html_parser.interactive,
            "duplicate_ids": duplicate_ids,
            "unresolved_fragments": unresolved,
        },
        "pdf": pdf_observed,
        "rights": {
            "component": "MIT OCW 6.253 complete-notes, Lecture 7",
            "license": LICENSE,
            "athena_source_figure_blocks_omitted": 7,
            "athena_source_figure_panels_omitted": 16,
            "copied_source_image_bytes": 0,
            "non_endorsement": True,
        },
        "model_identification": MODEL,
        "errors": errors,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
