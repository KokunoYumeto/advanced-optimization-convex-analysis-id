#!/usr/bin/env python3
"""Fail-closed reader validation for MIT 6.253 Lecture 3, PDF pages 29-38."""

from __future__ import annotations

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
CENSUS = ROOT / "00_control/MIT_L07_LECTURE_3_PAGES_029-038_BOUNDARY_CENSUS.md"
WITNESS = ROOT / "source/en/mit-07-lecture-3-differentiable-convex-functions-caratheodory-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.md"
CSS = ROOT / "source/id-ID/mit-l07.css"
PREAMBLE = ROOT / "source/id-ID/mit-l07-preamble.tex"
PDF_FILTER = ROOT / "source/id-ID/mit-l07-pdf-filter.lua"
BEFORE_BODY = ROOT / "source/id-ID/mit-l07-before-body.html"
AFTER_BODY = ROOT / "source/id-ID/mit-l07-after-body.html"
HTML = ROOT / "output/html/D90-MIT-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.html"
PDF = ROOT / "output/pdf/D90-MIT-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.pdf"
BUILDER = ROOT / "qa/build_mit_l07.py"
VISUAL_QA = ROOT / "qa/MIT_L07_VISUAL_QA.json"
BROWSER_QA = ROOT / "qa/MIT_L07_BROWSER_QA.json"
REREVIEW = ROOT / "qa/MIT_L07_INDEPENDENT_REREVIEW.md"
ADVERSE_LEDGER = ROOT / "00_control/ADVERSE_LEDGER.jsonl"
REPORT = ROOT / "qa/MIT_L07_VALIDATION.json"

MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
LICENSE_URI = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
PAGE_COUNTS = {
    29: (3, 0, 0, 0, "LECTURE 3"),
    30: (1, 2, 1, 1, "DIFFERENTIABLE CONVEX FUNCTIONS"),
    31: (0, 0, 0, 1, "PROOF IDEAS"),
    32: (1, 0, 3, 0, "OPTIMALITY CONDITION"),
    33: (1, 2, 3, 0, "PROJECTION THEOREM"),
    34: (1, 3, 2, 0, "TWICE DIFFERENTIABLE CONVEX FNS"),
    35: (6, 3, 0, 0, "CONVEX AND AFFINE HULLS"),
    36: (1, 2, 0, 1, "CARATHEODORY'S THEOREM"),
    37: (0, 2, 2, 1, "PROOF OF CARATHEODORY'S THEOREM"),
    38: (2, 0, 2, 0, "AN APPLICATION OF CARATHEODORY"),
}
PAGE_TEXT_SHA256 = {
    29: "c15536202c7266b03878d0c26e7eb7f16fd66914dc8f1e3130a6bda4331a2a86",
    30: "9d98e3ccc8484700cfb18da53d957f3e76baec9eafdce7c7f32a8830cf403085",
    31: "6e0c1295f1123cf1f21a00eaa7a56dffdae5687012636037ad4af3b135fa6a88",
    32: "839ab088b6e14506263f00c7c16f1ef7305e4b064a056206b39676a1f9381b4d",
    33: "0fd72c6f78ea30001a3090e3d53b852b29e61ad6892bcc44150934d20417c085",
    34: "7c31d76eb0766e97a33bec9c2e788bbdb1a22019a3058ad13e00babb8ecfaeaf",
    35: "cd5b3f0e30c9fa5662ba24784ff87ea2dc73cf909f406cdab776791688812604",
    36: "2b49f0fe0cd826f7abd9fee09cf1491ac082e7601b6b5c9573e9da508fb82872",
    37: "1eef14b9a3c143879b7567e2c4ea128562251801f0dd006688dafbb564c0425c",
    38: "2861b4fec0e91b47654e551a8336f4805b20befd1cad2aa5e1035ca500145c5f",
    39: "7eea461ea346ad1d4f43be4350ca2597d2efe0270b41967307600a521de03b05",
}
EXPECTED = {
    SOURCE_PDF: (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    CENSUS: (11_013, "3c7400bdd092cffe358e852e5304091bfd53b10fb36d366f558e1b0f9c8bee2f"),
    WITNESS: (13_879, "ab9fb12728b53c0369094a347827aa40d74332b811976b8e0733caf245bce18b"),
    TARGET: (16_518, "b1554fcb455bb43ecd72aa4c4e0f70d6d502c885009ba5e6a799e639e69441dd"),
    CSS: (2_777, "4f5bb04dc8f30c5e383fc901dea1817168446ad6f6761e21a8dfdd9fb961ab1b"),
    PREAMBLE: (1_499, "11dc4cdb79b1b1cffba021c2571451edac343a8763769552e9d1cb846ca1b6e0"),
    PDF_FILTER: (302, "2a39c4aeb5b6587e4ff7db483f130cb88c8fdbc74f9e83f8fd939d37f6e75421"),
    BEFORE_BODY: (96, "1e979724f5ee0f65feda5442d9307df710a3f2d8203f5d7051b390dc42ce61b7"),
    AFTER_BODY: (176, "ce35e12f0a05dda23a0f55e9b5dfb1f26e5f4c8d3b1c7439ac401227366580b9"),
    BUILDER: (4_115, "d777599f7529449c5c10a130afd32a1e67338ae7edf19b0dca00fdbd91724d01"),
    HTML: (77_399, "cc3b4f665d5f0b4cb9e26245ec0cce71658c6c0b3e5e07cee3fcabfb43df5e13"),
    PDF: (75_885, "2c7b4defaa56578f628c048dc4f17ee06b61f2bc33122b172af5539a5dae2eec"),
    VISUAL_QA: (2_472, "1caf7ebc941616122adade72ecc7efbf68e9b8a9499290f0782bf2e11e0cadd2"),
    BROWSER_QA: (2_468, "f29fdb2086693efe892ac0a0d346fa19c7d57de8371d7ccc0317edaf6e8bf9d7"),
    REREVIEW: (4_136, "d5f0bfc23b7a9b74d30570de9b2bd058c0ded84b51414b7b0b929349764ea86d"),
}
EXPECTED_RENDER = [
    "e132994bcafed753b1c2043d1435ac52ef4d245cde9f0cdbea9dd65ed7cb5c5e",
    "1e5e4dbde11e20c6734d13b35d96f27a4bc2c4dfcbe85d704d865ac730f4f1a8",
    "d049d80f54193b24512261e5764f89dd8f88392d6ef99e2d9bc7d9c66f76da99",
    "21b087239f1967147b7a065be06a31f0b6608e17b7d10f603bf009aaa386f39d",
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


def div_records(value: Any, class_name: str) -> list[dict[str, Any]]:
    records = []
    for node in walk(value):
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
    for page in pages:
        page_number = int(page["attrs"]["data-source-page"])
        page_items = div_records(page["blocks"], "source-item")
        nested_count = 0
        if page_items:
            for item in page_items:
                list_item_count = 0
                for node in walk(item["blocks"]):
                    if node.get("t") == "BulletList":
                        list_item_count += len(node["c"])
                    elif node.get("t") == "OrderedList":
                        list_item_count += len(node["c"][1])
                # Every stable source-item has one outer list item. Count only
                # subordinate items inside it; later proof labels are prose.
                nested_count += max(0, list_item_count - 1)
        else:
            # Page 37 is a proof continuation with labeled parts (a) and (b)
            # but no top-level source-item wrapper. In that topology the page's
            # ordered-list entries themselves are the two nested items.
            for node in walk(page["blocks"]):
                if node.get("t") == "BulletList":
                    nested_count += len(node["c"])
                elif node.get("t") == "OrderedList":
                    nested_count += len(node["c"][1])
        nested_by_page[page_number] = nested_count
    display_math = [
        re.sub(r"\s+", "", node["c"][1].strip())
        for node in walk(document)
        if node.get("t") == "Math" and node["c"][0]["t"] == "DisplayMath"
    ]
    return {
        "pages": pages,
        "items": items,
        "displays": displays,
        "figures": figures,
        "nested_by_page": nested_by_page,
        "display_math": display_math,
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
        self.ordered_depth = 0
        self.ordered_items = 0

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
            self.ordered_depth += 1
        if tag == "li" and self.ordered_depth:
            self.ordered_items += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings[tag] += 1
        self.source_pages += "source-page" in classes
        self.source_items += "source-item" in classes
        self.source_figures += "source-figure" in classes
        self.source_displays += "source-display" in classes

    def handle_endtag(self, tag: str) -> None:
        if tag == "ol":
            self.ordered_depth -= 1


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


def adverse_events() -> dict[str, dict[str, Any]]:
    events: dict[str, dict[str, Any]] = {}
    for line in ADVERSE_LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        event_id = event.get("event_id")
        if event_id in {"O015-MIT-SEM-0007", "O015-MIT-SEM-0008"}:
            events[event_id] = event
    return events


def main() -> int:
    errors: list[str] = []
    for path, expected in EXPECTED.items():
        check(path.is_file(), f"missing required file: {path.relative_to(ROOT)}", errors)
        if path.is_file():
            check((path.stat().st_size, digest(path)) == expected, f"identity mismatch: {path.relative_to(ROOT)}", errors)
    check(ADVERSE_LEDGER.is_file(), "missing adverse ledger", errors)

    source_text_hashes: dict[str, str] = {}
    target_top: dict[str, Any] = {}
    witness_top: dict[str, Any] = {}
    parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    reader: PdfReader | None = None
    rebuilds: list[tuple[str, str]] = []
    render_hashes: list[str] = []
    events: dict[str, dict[str, Any]] = {}

    if not errors:
        source_reader = PdfReader(SOURCE_PDF)
        check(len(source_reader.pages) == 340, "authority PDF page count is not 340", errors)
        for page in range(29, 40):
            raw = subprocess.run(
                ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(page), "-l", str(page), str(SOURCE_PDF), "-"],
                cwd=ROOT,
                capture_output=True,
                check=True,
            ).stdout
            actual_hash = hashlib.sha256(raw).hexdigest()
            source_text_hashes[str(page)] = actual_hash
            check(actual_hash == PAGE_TEXT_SHA256[page], f"authority page {page} text fingerprint differs", errors)
            text = raw.decode("utf-8").replace("\u2019", "'")
            if page in PAGE_COUNTS:
                check(PAGE_COUNTS[page][4] in text, f"authority page {page} heading differs", errors)
            else:
                check("LECTURE 4" in text and "LECTURE OUTLINE" in text, "page 39 is not the clean Lecture 4 delimiter", errors)
        check(len(image_rows(SOURCE_PDF, 29, 38)) == 5, "authority pages 29-38 raster image inventory differs", errors)
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
            "O015-MIT-SEM-0007",
            "O015-MIT-SEM-0008",
            "Tinjauan bahasa manusia/penutur asli belum tercatat",
            "Penerapan Teorema Caratheodory",
            "titik peminimum tunggal",
        ):
            check(phrase in normalized_target, f"target lacks {phrase!r}", errors)
        for phrase in (MODEL, "CC BY-NC-SA 4.0", "Athena Scientific", "LECTURE 3", "AN APPLICATION OF CARATHEODORY", "unique minimum of"):
            check(phrase in normalized_witness, f"witness lacks {phrase!r}", errors)
        check(target_text.count(r"f:\mathbb{R}^n\to\mathbb{R}") == 3, "target does not contain exactly three corrected function-type arrows", errors)
        check(witness_text.count(r"f:\mathbb{R}^n\mapsto\mathbb{R}") == 3, "witness does not preserve exactly three printed mapsto declarations", errors)
        check("![" not in target_text and "![" not in witness_text, "semantic source embeds an image", errors)

        events = adverse_events()
        check(set(events) == {"O015-MIT-SEM-0007", "O015-MIT-SEM-0008"}, "required adverse events are absent or duplicated", errors)
        if "O015-MIT-SEM-0007" in events:
            event = events["O015-MIT-SEM-0007"]
            check(event.get("authority") == "o015-mit-ocw-6.253-spring-2012", "event 0007 authority differs", errors)
            check("pages 30, 32, and 34" in event.get("source", "") and "right arrows" in event.get("target_action", ""), "event 0007 binding differs", errors)
        if "O015-MIT-SEM-0008" in events:
            event = events["O015-MIT-SEM-0008"]
            check(event.get("authority") == "o015-mit-ocw-6.253-spring-2012", "event 0008 authority differs", errors)
            check("page 33" in event.get("source", "") and "unique minimizing point" in event.get("target_action", ""), "event 0008 binding differs", errors)

        target_top = source_topology(TARGET)
        witness_top = source_topology(WITNESS)
        for label, top, prefix in (("target", target_top, "d90"), ("witness", witness_top, "src")):
            expected_pages = [(str(page - 28), str(page), f"{prefix}-mit-l07-p{page:03d}") for page in PAGE_COUNTS]
            actual_pages = [(record["attrs"]["data-source-order"], record["attrs"]["data-source-page"], record["id"]) for record in top["pages"]]
            check(actual_pages == expected_pages, f"{label} page map differs", errors)
            expected_items = [(page, order, f"{prefix}-mit-l07-p{page:03d}-i{order:03d}") for page, counts in PAGE_COUNTS.items() for order in range(1, counts[0] + 1)]
            actual_items = [(int(record["attrs"]["data-source-page"]), int(record["attrs"]["data-source-order"]), record["id"]) for record in top["items"]]
            check(actual_items == expected_items, f"{label} item map differs", errors)
            expected_displays = [(page, order, f"{prefix}-mit-l07-p{page:03d}-d{order:03d}") for page, counts in PAGE_COUNTS.items() for order in range(1, counts[2] + 1)]
            actual_displays = [(int(record["attrs"]["data-source-page"]), int(record["attrs"]["data-display-order"]), record["id"]) for record in top["displays"]]
            check(actual_displays == expected_displays, f"{label} display map differs", errors)
            figure_pages = [page for page, counts in PAGE_COUNTS.items() if counts[3]]
            expected_figures = [(page, f"{prefix}-mit-l07-p{page:03d}-f001") for page in figure_pages]
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
            check((len(top["items"]), sum(top["nested_by_page"].values()), len(top["displays"]), len(top["figures"])) == (16, 14, 13, 4), f"{label} total topology differs", errors)
        check(target_top["display_math"] == witness_top["display_math"], "target display formula sequence differs from witness", errors)

        html_text = HTML.read_text(encoding="utf-8")
        parser.feed(html_text)
        duplicate_ids = sorted(identifier for identifier, count in Counter(parser.ids).items() if count > 1)
        unresolved = sorted(set(parser.fragments) - set(parser.ids))
        check(parser.lang == "id-ID" and parser.main == 1, "HTML language or main landmark differs", errors)
        check(parser.headings == Counter({"h2": 11, "h1": 1}), f"HTML heading topology differs: {parser.headings}", errors)
        check((parser.source_pages, parser.source_items, parser.source_figures, parser.source_displays) == (10, 16, 4, 13), "HTML source topology differs", errors)
        check(parser.math == 195 and parser.display_math == 13, "HTML MathML topology differs", errors)
        check(parser.ordered_items == 11, f"HTML ordered nested-item count differs: {parser.ordered_items}", errors)
        check(parser.images == 0 and parser.media == 0 and "data:image" not in html_text, "HTML contains an image or embedded media surface", errors)
        check(parser.skip_target == "#d90-mit-l07-p029", f"skip-link target differs: {parser.skip_target}", errors)
        check(not duplicate_ids and not unresolved, f"HTML ID closure differs: duplicate={duplicate_ids}, unresolved={unresolved}", errors)
        check(LICENSE_URI in parser.links, "HTML lacks the exact component license URI", errors)

        browser = json.loads(BROWSER_QA.read_text(encoding="utf-8"))
        check(browser.get("result") == "pass", "browser QA is not pass", errors)
        check(browser.get("surface", {}).get("sha256") == digest(HTML), "browser QA does not bind canonical HTML", errors)
        for viewport in ("desktop", "mobile"):
            metrics = browser.get(viewport, {})
            check(
                metrics.get("horizontal_overflow") is False
                and metrics.get("math_overflow_count") == 0
                and metrics.get("document_client_width") == metrics.get("document_scroll_width"),
                f"browser {viewport} reflow gate differs",
                errors,
            )
        browser_semantic = browser.get("semantic_surface", {})
        check(
            (
                browser_semantic.get("main_landmarks"),
                browser_semantic.get("source_pages"),
                browser_semantic.get("source_items"),
                browser_semantic.get("source_displays"),
                browser_semantic.get("source_figures"),
                browser_semantic.get("math_nodes"),
                browser_semantic.get("display_math_nodes"),
            )
            == (1, 10, 16, 13, 4, 195, 13),
            "browser semantic topology differs",
            errors,
        )
        skip = browser.get("skip_link", {})
        check(
            skip.get("tag") == "A"
            and skip.get("href") == "#d90-mit-l07-p029"
            and skip.get("target_exists") is True
            and skip.get("tab_index") == 0
            and skip.get("aria_disabled") is None
            and skip.get("pointer_activation_hash") == "#d90-mit-l07-p029",
            "browser skip-link semantics differ",
            errors,
        )
        check(browser.get("console_warnings_or_errors") == [], "browser console findings are not empty", errors)

        visual = json.loads(VISUAL_QA.read_text(encoding="utf-8"))
        check(visual.get("result") == "pass", "visual QA is not pass", errors)
        check(visual.get("surface", {}).get("sha256") == digest(PDF), "visual QA does not bind canonical PDF", errors)
        check([entry.get("sha256") for entry in visual.get("render", {}).get("files", [])] == EXPECTED_RENDER, "visual receipt render hashes differ", errors)
        check(visual.get("render", {}).get("pages") == 4, "visual receipt page count differs", errors)

        rereview_text = REREVIEW.read_text(encoding="utf-8")
        for phrase in (
            "P1=0, P2=0, P3=0",
            "Human/native-speaker Indonesian review remains unrecorded",
            "O015-MIT-SEM-0007",
            "O015-MIT-SEM-0008",
            digest(WITNESS),
            digest(TARGET),
            digest(HTML),
            digest(PDF),
        ):
            check(phrase in rereview_text, f"independent rereview lacks {phrase!r}", errors)

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
        for phrase in ("Kuliah 3 - Garis Besar Kuliah", "Fungsi Konveks Terdiferensialkan", "Syarat Optimalitas", "Teorema Proyeksi", "Selubung Konveks dan Afin", "Bukti Teorema Caratheodory", "Penerapan Teorema Caratheodory", "Halaman sumber 38"):
            check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)

        (ROOT / "tmp/pdfs").mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="mit-l07-determinism-", dir=ROOT / "tmp/pdfs") as temp:
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

        with tempfile.TemporaryDirectory(prefix="mit-l07-render-check-", dir=ROOT / "tmp/pdfs") as temp:
            prefix = Path(temp) / "page"
            subprocess.run(["pdftoppm", "-r", "160", "-png", str(PDF), str(prefix)], cwd=ROOT, capture_output=True, check=True)
            render_hashes = [digest(path) for path in sorted(Path(temp).glob("page-*.png"))]
            check(render_hashes == EXPECTED_RENDER, f"fresh render hashes differ: {render_hashes}", errors)

    result = "pass" if not errors else "fail"
    report = {
        "schema": "o015-mit-l07-validation-v1",
        "recorded_at": "2026-08-24T01:28:42Z",
        "result": result,
        "boundary": {
            "source_pdf_pages": list(range(29, 39)),
            "next_source_page": 39,
            "next_heading": "LECTURE 4 - LECTURE OUTLINE",
            "source_items": 16,
            "nested_items": 14,
            "source_displays": 13,
            "source_figures": 4,
            "source_figure_panels": 6,
            "copied_source_graphics": 0,
        },
        "files": {path.stem.lower().replace("-", "_"): identity(path) for path in EXPECTED if path.exists()},
        "source_page_text_sha256": source_text_hashes,
        "formula_sequence_match": bool(target_top and witness_top and target_top["display_math"] == witness_top["display_math"]),
        "adverse_event_bindings": {key: events.get(key, {}) for key in ("O015-MIT-SEM-0007", "O015-MIT-SEM-0008")},
        "build": {
            "command": "python qa/build_mit_l07.py --html-output <html> --pdf-output <pdf>",
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
            "source_figure_panels": 6,
            "source_displays": parser.source_displays,
            "math_nodes": parser.math,
            "display_math_nodes": parser.display_math,
            "ordered_nested_items": parser.ordered_items,
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
            "athena_source_figure_blocks_omitted": 4,
            "athena_source_figure_panels_omitted": 6,
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
