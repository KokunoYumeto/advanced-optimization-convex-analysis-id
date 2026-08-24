#!/usr/bin/env python3
"""Fail-closed reader validation for MIT 6.253 Lecture 2, PDF pages 20-28."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterator

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT / "authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"
CENSUS = ROOT / "00_control/MIT_L06_LECTURE_2_PAGES_020-028_BOUNDARY_CENSUS.md"
WITNESS = ROOT / "source/en/mit-06-lecture-2-convex-foundations-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-06-kuliah-2-landasan-konveks-id.md"
CSS = ROOT / "source/id-ID/mit-l06.css"
PREAMBLE = ROOT / "source/id-ID/mit-l06-preamble.tex"
PDF_FILTER = ROOT / "source/id-ID/mit-l06-pdf-filter.lua"
BEFORE_BODY = ROOT / "source/id-ID/mit-l06-before-body.html"
AFTER_BODY = ROOT / "source/id-ID/mit-l06-after-body.html"
HTML = ROOT / "output/html/D90-MIT-06-kuliah-2-landasan-konveks-id.html"
PDF = ROOT / "output/pdf/D90-MIT-06-kuliah-2-landasan-konveks-id.pdf"
BUILDER = ROOT / "qa/build_mit_l06.py"
BROWSER_QA = ROOT / "qa/MIT_L06_BROWSER_QA.json"
VISUAL_QA = ROOT / "qa/MIT_L06_VISUAL_QA.json"
REREVIEW = ROOT / "qa/MIT_L06_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L06_VALIDATION.json"

MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
LICENSE_URI = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
PAGE_COUNTS = {
    20: (4, 0, 0, 0, "LECTURE 2"),
    21: (6, 4, 1, 0, "SOME MATH CONVENTIONS"),
    22: (3, 3, 2, 1, "CONVEX SETS"),
    23: (2, 0, 1, 1, "CONVEX FUNCTIONS"),
    24: (5, 0, 2, 1, "EXTENDED REAL-VALUED FUNCTIONS"),
    25: (4, 3, 1, 1, "CLOSEDNESS AND SEMICONTINUITY I"),
    26: (3, 4, 2, 0, "CLOSEDNESS AND SEMICONTINUITY II"),
    27: (3, 0, 0, 1, "PROPER AND IMPROPER CONVEX FUNCTIONS"),
    28: (2, 3, 3, 0, "RECOGNIZING CONVEX FUNCTIONS"),
}
PAGE_TEXT_SHA256 = {
    20: "5abd5fe7dee510eda6bfd683928d0c1e166d4f0fdf9a5c254371e152c21771a2",
    21: "23a0470c2ed9f1863f6fe10dc94122033b5e453a2dd41c33ede2f75f4ea42089",
    22: "57b10e80d12a6ff7413cfa6bb426f39fb9e05999abf55c4ee6e4001b9e7291b5",
    23: "8108fb7eee4a4d68c31773cd7cda8edb0d2be6b1bde30faa3ef18284f7ed246e",
    24: "1a3e5ff5f45dc7c12aacc6d98694fe74094134b9f73c1b8fc476924bd255fd9e",
    25: "8ac931a9adaa5310118c79931050e629cfdc0ce7d29d5e5ed1731fbc27dceed2",
    26: "cbe98d957ab8491d5ca06f96eab748f3da6e67b7b05fd500470eb4b16e82ba43",
    27: "9ebd0cd52cd11d1e6e1804ea8ef15a783c5c1d62d6c1dedd9f45ae1cb7b038c7",
    28: "ef86e6eac19001b1fc98a35d1b12b6c15734cb655228f0deaea6f33f592b2823",
    29: "c15536202c7266b03878d0c26e7eb7f16fd66914dc8f1e3130a6bda4331a2a86",
}
EXPECTED = {
    SOURCE_PDF: (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    CENSUS: (9_962, "fc0cb5b863652aa810ed765f247a248be1510cd61f240277b896e605a41b3ea4"),
    WITNESS: (15_594, "a8094ad892a90a20d271e961504fb418b1ea241859b072cf5ba56317783b809a"),
    TARGET: (17_772, "a9e8b353adddc4919b6244e27df4365a33e74d4b034b9d99fff6eb3f93e0b23e"),
    CSS: (2_777, "6b17b29f419896e8a53000316cf9c52a393168032f811f4346b295ca6e7a045c"),
    PREAMBLE: (1_499, "a561a9dccaf4997e1a82064bf09ad20baf07f85e50441f1b11cfbd31c3993f6a"),
    PDF_FILTER: (302, "2a39c4aeb5b6587e4ff7db483f130cb88c8fdbc74f9e83f8fd939d37f6e75421"),
    BEFORE_BODY: (96, "86eb76132a49810cb5316e2fef333c61318ab9062a74cb1f0c6b018ee49f7c63"),
    AFTER_BODY: (175, "3d3f8d0250a87e2b34cb8fc39b32f4b63f2d2a2ad16f13be20a751b13a0f6020"),
    BUILDER: (4_037, "c4ff8f99a7c265ee8314a9a98abfdab12d85a1826852c4512720ecf4ab44f8af"),
    HTML: (70_446, "94275af59592c64e7c8ae55fc384b721b2863a22ee328c33dc3b1d5a1e0af9a6"),
    PDF: (74_235, "84ce42542ed58e102c736dacc02b69cf16ab264a577d689d2fe5f7a24ba37d75"),
    BROWSER_QA: (1_584, "b98ac5b2ea7df5b5d7b1263595b777269db1acc9c996fe7135a338366fb2d64d"),
    VISUAL_QA: (2_342, "9643896538a3704626d100c3775e3329bf082feda0e981977593f7ff6d25c680"),
    REREVIEW: (4_104, "dab732ea3b5096ee9d186775aca9064781e0026e15ea8943c2c8e637e6a64afb"),
}
EXPECTED_RENDER = [
    "20d3ece52164fb4eb819cbfa3bc011f8879e8a53d214c2d4ba86033f74cefabd",
    "55ef1185f2d236220bc7cbe573b1fac5ca47f3d79a8a20dfcd715cb3602ff14e",
    "c5f98c13023a7dfc52f9b75b86c2558ac10de887835b7d3929de657316c904f1",
    "4b5ac1a5bde3091a3d2039af3b2d573ad8a31130ff1bfd1601d0bebd792a1794",
]


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
    data = subprocess.run(
        ["pandoc", str(path), "--from=markdown+fenced_divs+yaml_metadata_block", "--to=json"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return json.loads(data.decode("utf-8"))


def div_records(document: dict[str, Any], class_name: str) -> list[dict[str, Any]]:
    records = []
    for node in walk(document):
        if node.get("t") != "Div":
            continue
        identifier, classes, attrs = node["c"][0]
        if class_name in classes:
            records.append({"id": identifier, "attrs": dict(attrs), "blocks": node["c"][1]})
    return records


def source_topology(path: Path) -> dict[str, Any]:
    document = ast(path)
    pages = div_records(document, "source-page")
    items = div_records(document, "source-item")
    displays = div_records(document, "source-display")
    figures = div_records(document, "source-figure")
    nested_by_page: Counter[int] = Counter()
    for item in items:
        list_nodes = [node for node in walk(item["blocks"]) if node.get("t") in {"BulletList", "OrderedList"}]
        list_lengths = [len(node["c"]) if node["t"] == "BulletList" else len(node["c"][1]) for node in list_nodes]
        nested_by_page[int(item["attrs"]["data-source-page"])] += sum(list_lengths) - 1
    ordered = []
    for node in walk(document):
        if node.get("t") == "OrderedList":
            start, style, delimiter = node["c"][0]
            ordered.append((start, style["t"], delimiter["t"], len(node["c"][1])))
    display_math = [
        re.sub(r"\s+", "", node["c"][1].strip()).replace(r"\text{atau}", r"\text{or}")
        for node in walk(document)
        if node.get("t") == "Math" and node["c"][0]["t"] == "DisplayMath"
    ]
    return {
        "pages": pages,
        "items": items,
        "displays": displays,
        "figures": figures,
        "nested_by_page": nested_by_page,
        "ordered": ordered,
        "display_math": display_math,
        "document": document,
    }


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.links: list[str] = []
        self.lang = ""
        self.main = 0
        self.images = 0
        self.media = 0
        self.math = 0
        self.display_math = 0
        self.headings: Counter[str] = Counter()
        self.skip_target = ""
        self.source_pages = 0
        self.source_items = 0
        self.source_figures = 0
        self.source_displays = 0
        self.ordered: Counter[str] = Counter()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        if tag == "html":
            self.lang = values.get("lang", "")
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "a":
            href = values.get("href", "")
            if href.startswith("#"):
                self.fragments.append(href[1:])
            elif href:
                self.links.append(href)
            if "skip-link" in classes:
                self.skip_target = href
        if tag == "main":
            self.main += 1
        if tag == "img":
            self.images += 1
        if tag in {"img", "video", "audio", "canvas", "iframe", "object", "embed"}:
            self.media += 1
        if tag == "math":
            self.math += 1
            self.display_math += values.get("display") == "block"
        if tag == "ol":
            self.ordered[values.get("type", "1")] += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings[tag] += 1
        self.source_pages += "source-page" in classes
        self.source_items += "source-item" in classes
        self.source_figures += "source-figure" in classes
        self.source_displays += "source-display" in classes


def pdf_uris(reader: PdfReader) -> set[str]:
    uris: set[str] = set()
    for page in reader.pages:
        for annotation_ref in page.get("/Annots") or []:
            action = annotation_ref.get_object().get("/A") or {}
            uri = action.get("/URI")
            if uri:
                uris.add(str(uri))
    return uris


def image_rows(path: Path, first: int | None = None, last: int | None = None) -> list[str]:
    command = ["pdfimages", "-list"]
    if first is not None:
        command += ["-f", str(first)]
    if last is not None:
        command += ["-l", str(last)]
    command.append(str(path))
    listing = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [line for line in listing.splitlines() if re.match(r"^\s*\d+\s+\d+\s+", line)]


def main() -> int:
    errors: list[str] = []
    for path, expected in EXPECTED.items():
        check(path.is_file(), f"missing required file: {path.relative_to(ROOT)}", errors)
        if path.is_file():
            check((path.stat().st_size, digest(path)) == expected, f"identity mismatch: {path.relative_to(ROOT)}", errors)

    source_text_hashes: dict[str, str] = {}
    target_top: dict[str, Any] = {}
    witness_top: dict[str, Any] = {}
    parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    reader: PdfReader | None = None
    rebuilds: list[tuple[str, str]] = []
    render_hashes: list[str] = []

    if not errors:
        source_reader = PdfReader(SOURCE_PDF)
        check(len(source_reader.pages) == 340, "authority PDF page count is not 340", errors)
        for page in range(20, 30):
            raw = subprocess.run(
                ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(page), "-l", str(page), str(SOURCE_PDF), "-"],
                cwd=ROOT,
                capture_output=True,
                check=True,
            ).stdout
            actual_hash = hashlib.sha256(raw).hexdigest()
            source_text_hashes[str(page)] = actual_hash
            check(actual_hash == PAGE_TEXT_SHA256[page], f"authority page {page} text fingerprint differs", errors)
            text = raw.decode("utf-8")
            if page in PAGE_COUNTS:
                check(PAGE_COUNTS[page][4] in text, f"authority page {page} heading differs", errors)
            else:
                check("LECTURE 3" in text and "LECTURE OUTLINE" in text, "page 29 is not the clean Lecture 3 delimiter", errors)
        check(len(image_rows(SOURCE_PDF, 20, 28)) == 4, "authority pages 20-28 raster image inventory differs", errors)
        check(not image_rows(PDF), "output PDF contains a raster image XObject", errors)

        target_text = TARGET.read_text(encoding="utf-8")
        witness_text = WITNESS.read_text(encoding="utf-8")
        normalized_target = re.sub(r"\s+", " ", target_text)
        normalized_witness = re.sub(r"\s+", " ", witness_text)
        for phrase in (
            MODEL,
            "CC BY-NC-SA 4.0",
            LICENSE_URI,
            "Athena Scientific",
            "Tidak ada byte, potongan, atau tata letak grafik sumber",
            "O015-MIT-SEM-0005",
            "O015-MIT-SEM-0006",
            "Tinjauan bahasa manusia/penutur asli belum tercatat",
            "Mengenali Fungsi Konveks",
        ):
            check(phrase in normalized_target, f"target lacks {phrase!r}", errors)
        for phrase in (MODEL, "CC BY-NC-SA 4.0", "Athena Scientific", "LECTURE 2", "RECOGNIZING CONVEX FUNCTIONS"):
            check(phrase in normalized_witness, f"witness lacks {phrase!r}", errors)
        check("![" not in target_text and "![" not in witness_text, "semantic source embeds an image", errors)

        target_top = source_topology(TARGET)
        witness_top = source_topology(WITNESS)
        for label, top, prefix in (("target", target_top, "d90"), ("witness", witness_top, "src")):
            expected_pages = [(str(page - 19), str(page), f"{prefix}-mit-l06-p{page:03d}") for page in PAGE_COUNTS]
            actual_pages = [(record["attrs"]["data-source-order"], record["attrs"]["data-source-page"], record["id"]) for record in top["pages"]]
            check(actual_pages == expected_pages, f"{label} page map differs", errors)
            expected_items = [(page, order, f"{prefix}-mit-l06-p{page:03d}-i{order:03d}") for page, counts in PAGE_COUNTS.items() for order in range(1, counts[0] + 1)]
            actual_items = [(int(record["attrs"]["data-source-page"]), int(record["attrs"]["data-source-order"]), record["id"]) for record in top["items"]]
            check(actual_items == expected_items, f"{label} item map differs", errors)
            expected_displays = [(page, order, f"{prefix}-mit-l06-p{page:03d}-d{order:03d}") for page, counts in PAGE_COUNTS.items() for order in range(1, counts[2] + 1)]
            actual_displays = [(int(record["attrs"]["data-source-page"]), int(record["attrs"]["data-display-order"]), record["id"]) for record in top["displays"]]
            check(actual_displays == expected_displays, f"{label} display map differs", errors)
            figure_pages = [page for page, counts in PAGE_COUNTS.items() if counts[3]]
            expected_figures = [(page, f"{prefix}-mit-l06-p{page:03d}-f001") for page in figure_pages]
            actual_figures = [(int(record["attrs"]["data-source-page"]), record["id"]) for record in top["figures"]]
            check(actual_figures == expected_figures, f"{label} figure map differs", errors)
            ids = [record["id"] for key in ("pages", "items", "displays", "figures") for record in top[key]]
            check(len(ids) == len(set(ids)), f"duplicate {label} stable IDs", errors)
            for page, counts in PAGE_COUNTS.items():
                actual = (
                    sum(int(record["attrs"]["data-source-page"]) == page for record in top["items"]),
                    top["nested_by_page"][page],
                    sum(int(record["attrs"]["data-source-page"]) == page for record in top["displays"]),
                    sum(int(record["attrs"]["data-source-page"]) == page for record in top["figures"]),
                )
                check(actual == counts[:4], f"{label} topology differs on source page {page}: {actual}", errors)
            check((len(top["items"]), sum(top["nested_by_page"].values()), len(top["displays"]), len(top["figures"])) == (32, 17, 12, 5), f"{label} total topology differs", errors)
        check(target_top["display_math"] == witness_top["display_math"], "target display formula sequence differs from witness", errors)
        check(target_top["ordered"].count((1, "LowerRoman", "TwoParens", 3)) == 1, "target lacks one coherent (i)-(iii) list", errors)
        check(target_top["ordered"].count((1, "LowerAlpha", "TwoParens", 3)) == 1, "target lacks one coherent (a)-(c) list", errors)

        html_text = HTML.read_text(encoding="utf-8")
        parser.feed(html_text)
        duplicate_ids = sorted(identifier for identifier, count in Counter(parser.ids).items() if count > 1)
        unresolved = sorted(set(parser.fragments) - set(parser.ids))
        check(parser.lang == "id-ID" and parser.main == 1, "HTML language or main landmark differs", errors)
        check(parser.headings == Counter({"h2": 10, "h1": 1}), f"HTML heading topology differs: {parser.headings}", errors)
        check((parser.source_pages, parser.source_items, parser.source_figures, parser.source_displays) == (9, 32, 5, 12), "HTML source topology differs", errors)
        check(parser.math == 153 and parser.display_math == 12, "HTML MathML topology differs", errors)
        check(parser.ordered == Counter({"i": 1, "a": 1}), f"HTML ordered-list topology differs: {parser.ordered}", errors)
        check(parser.images == 0 and parser.media == 0 and "data:image" not in html_text, "HTML contains an image or embedded media surface", errors)
        check(parser.skip_target == "#d90-mit-l06-p020", f"skip-link target differs: {parser.skip_target}", errors)
        check(not duplicate_ids and not unresolved, f"HTML ID closure differs: duplicate={duplicate_ids}, unresolved={unresolved}", errors)
        check(LICENSE_URI in parser.links, "HTML lacks the exact component license URI", errors)

        browser = json.loads(BROWSER_QA.read_text(encoding="utf-8"))
        check(browser.get("result") == "pass" and browser.get("browser_available") is True, "browser QA is not a live pass", errors)
        check(browser.get("html", {}).get("sha256") == digest(HTML), "browser QA does not bind canonical HTML", errors)
        browser_top = browser.get("topology", {})
        check((browser_top.get("source_pages"), browser_top.get("source_items"), browser_top.get("source_figures"), browser_top.get("source_displays")) == (9, 32, 5, 12), "browser topology differs", errors)
        check(browser_top.get("ordered_items") == {"lower_roman": 3, "lower_alpha": 3}, "browser ordered-item topology differs", errors)
        check(browser_top.get("duplicate_ids") == 0 and browser_top.get("unresolved_fragments") == 0, "browser ID closure differs", errors)
        for viewport in ("desktop", "mobile"):
            measurement = browser.get(viewport, {})
            check(measurement.get("scroll_width") == measurement.get("client_width"), f"{viewport} width measurement differs", errors)
            check(measurement.get("horizontal_overflow") is False, f"{viewport} has horizontal overflow", errors)
            check(measurement.get("console_warnings_or_errors") == [], f"{viewport} console is not clean", errors)
        check(browser.get("mobile", {}).get("toc_columns") == 1 and browser.get("mobile", {}).get("display_math_overflow") is False, "mobile reflow details differ", errors)

        visual = json.loads(VISUAL_QA.read_text(encoding="utf-8"))
        check(visual.get("result") == "pass", "visual QA is not pass", errors)
        check(visual.get("surface", {}).get("sha256") == digest(PDF), "visual QA does not bind canonical PDF", errors)
        check([entry.get("sha256") for entry in visual.get("render", {}).get("files", [])] == EXPECTED_RENDER, "visual receipt render hashes differ", errors)
        rereview = REREVIEW.read_text(encoding="utf-8")
        check("P1=0, P2=0, P3=0" in rereview, "rereview does not close severity counts", errors)
        check(all(value in rereview for value in (digest(TARGET), digest(HTML), digest(PDF))), "rereview lacks canonical bindings", errors)

        reader = PdfReader(PDF)
        root = reader.trailer["/Root"]
        check(len(reader.pages) == 4, f"PDF page count {len(reader.pages)} != 4", errors)
        check(root.get("/Lang") == "id-ID", f"PDF /Lang differs: {root.get('/Lang')}", errors)
        check("/StructTreeRoot" not in root, "PDF unexpectedly claims tagged structure", errors)
        check(not reader.is_encrypted, "PDF is encrypted", errors)
        check((reader.metadata or {}).get("/Producer") == f"{MODEL} - user-directed production assistance", "PDF producer provenance differs", errors)
        check(LICENSE_URI in pdf_uris(reader), "PDF lacks the exact component license URI", errors)
        fonts: dict[str, bool] = {}
        for page in reader.pages:
            check(abs(float(page.mediabox.width) - 595.276) < 0.02 and abs(float(page.mediabox.height) - 841.89) < 0.02, "PDF page is not A4", errors)
            for name, ref in page.get("/Resources", {}).get("/Font", {}).items():
                fonts[str(name)] = bool(ref.get_object().get("/ToUnicode"))
        check(bool(fonts) and all(fonts.values()), f"PDF ToUnicode coverage differs: {fonts}", errors)
        searchable = subprocess.run(["pdftotext", str(PDF), "-"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
        for phrase in ("Kuliah 2 - Garis Besar Kuliah", "Beberapa Konvensi Matematika", "Ketertutupan dan Semikontinuitas II", "Fungsi Konveks Proper dan Tak Proper", "Mengenali Fungsi Konveks", "Halaman sumber 28"):
            check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)

        with tempfile.TemporaryDirectory(prefix="mit-l06-determinism-", dir=ROOT / "tmp/pdfs") as temp:
            temp_root = Path(temp)
            for label in ("a", "b"):
                out = temp_root / label
                html = out / HTML.name
                pdf = out / PDF.name
                subprocess.run(
                    [sys.executable, str(BUILDER), "--html-output", str(html), "--pdf-output", str(pdf)],
                    cwd=ROOT,
                    capture_output=True,
                    check=True,
                )
                rebuilds.append((digest(html), digest(pdf)))
            expected_pair = (digest(HTML), digest(PDF))
            check(rebuilds[0] == rebuilds[1] == expected_pair, f"deterministic rebuilds differ: {rebuilds}", errors)

        with tempfile.TemporaryDirectory(prefix="mit-l06-render-check-", dir=ROOT / "tmp/pdfs") as temp:
            prefix = Path(temp) / "page"
            subprocess.run(["pdftoppm", "-r", "160", "-png", str(PDF), str(prefix)], cwd=ROOT, capture_output=True, check=True)
            render_hashes = [digest(path) for path in sorted(Path(temp).glob("page-*.png"))]
            check(render_hashes == EXPECTED_RENDER, f"fresh render hashes differ: {render_hashes}", errors)

    result = "pass" if not errors else "fail"
    report = {
        "schema": "o015-mit-l06-validation-v1",
        "recorded_at": "2026-08-23T21:05:00Z",
        "result": result,
        "boundary": {
            "source_pdf_pages": list(range(20, 29)),
            "next_source_page": 29,
            "next_heading": "LECTURE 3 - LECTURE OUTLINE",
            "source_items": 32,
            "nested_items": 17,
            "source_displays": 12,
            "source_figures": 5,
            "copied_source_graphics": 0,
        },
        "files": {path.stem.lower().replace("-", "_"): identity(path) for path in EXPECTED},
        "source_page_text_sha256": source_text_hashes,
        "formula_sequence_match": bool(target_top and witness_top and target_top["display_math"] == witness_top["display_math"]),
        "build": {
            "command": "python qa/build_mit_l06.py --html-output <html> --pdf-output <pdf>",
            "deterministic_rebuilds": 2,
            "rebuild_hashes": rebuilds,
            "html_sha256": digest(HTML) if HTML.exists() else None,
            "pdf_sha256": digest(PDF) if PDF.exists() else None,
        },
        "html": {
            "lang": parser.lang,
            "headings": dict(sorted(parser.headings.items())),
            "source_pages": parser.source_pages,
            "source_items": parser.source_items,
            "source_figures": parser.source_figures,
            "source_displays": parser.source_displays,
            "math_nodes": parser.math,
            "display_math_nodes": parser.display_math,
            "images": parser.images,
            "media_or_embeds": parser.media,
            "duplicate_ids": duplicate_ids,
            "unresolved_fragments": unresolved,
        },
        "pdf": {
            "pages": len(reader.pages) if reader else None,
            "page_size": "A4",
            "searchable": True,
            "tagged": False,
            "images": 0,
            "render_sha256": render_hashes,
        },
        "rights": {
            "component": "MIT OCW 6.253 complete-notes",
            "license": "CC BY-NC-SA 4.0",
            "license_uri": LICENSE_URI,
            "athena_source_figures_omitted": 5,
            "non_endorsement": True,
        },
        "model_identification": MODEL,
        "human_native_speaker_review": False,
        "errors": errors,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
