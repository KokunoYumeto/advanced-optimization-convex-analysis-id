#!/usr/bin/env python3
"""Fail-closed reader validation for MIT 6.253 Lecture 4, PDF pages 39-49."""

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
CENSUS = ROOT / "00_control/MIT_L08_LECTURE_4_BOUNDARY_CENSUS.md"
WITNESS = ROOT / "source/en/mit-08-lecture-4-relative-interior-closure-continuity-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.md"
CSS = ROOT / "source/id-ID/mit-l08.css"
PREAMBLE = ROOT / "source/id-ID/mit-l08-preamble.tex"
PDF_FILTER = ROOT / "source/id-ID/mit-l08-pdf-filter.lua"
BEFORE_BODY = ROOT / "source/id-ID/mit-l08-before-body.html"
AFTER_BODY = ROOT / "source/id-ID/mit-l08-after-body.html"
HTML = ROOT / "output/html/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.html"
PDF = ROOT / "output/pdf/D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.pdf"
BUILDER = ROOT / "qa/build_mit_l08.py"
VISUAL_QA = ROOT / "qa/MIT_L08_VISUAL_QA.json"
BROWSER_QA = ROOT / "qa/MIT_L08_BROWSER_QA.json"
ADVERSE_LEDGER = ROOT / "00_control/ADVERSE_LEDGER.jsonl"
REPORT = ROOT / "qa/MIT_L08_VALIDATION.json"

MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
LICENSE_URI = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
PAGE_COUNTS = {
    39: (4, 0, 0, 0, "LECTURE 4"),
    40: (5, 0, 0, 1, "RELATIVE INTERIOR"),
    41: (1, 2, 1, 1, "ADDITIONAL MAJOR RESULTS"),
    42: (2, 0, 1, 1, "OPTIMIZATION APPLICATION"),
    43: (4, 3, 0, 0, "CALCULUS OF REL. INTERIORS: SUMMARY"),
    44: (1, 5, 1, 1, "CLOSURE VS RELATIVE INTERIOR"),
    45: (1, 2, 1, 0, "LINEAR TRANSFORMATIONS"),
    46: (2, 2, 7, 0, "INTERSECTIONS AND VECTOR SUMS"),
    47: (1, 0, 6, 0, "CARTESIAN PRODUCT - GENERALIZATION"),
    48: (2, 0, 4, 1, "CONTINUITY OF CONVEX FUNCTIONS"),
    49: (4, 2, 5, 0, "CLOSURES OF FUNCTIONS"),
}
PAGE_TEXT_SHA256 = {
    39: "7eea461ea346ad1d4f43be4350ca2597d2efe0270b41967307600a521de03b05",
    40: "85ff891678a524893f8cbacc5bf4cdd6d4540883d8d125ce415778b5d621dba5",
    41: "0ea583c7109ed83a96c11d143aed939d5c18a07d5bdb74c537e22db1c3aa2939",
    42: "7120ed092593e2c64d5c8e52176ad37c646273e9c36a652a250d3710812d7c1c",
    43: "b71f771dd0b2736dc5d00bd36335bd9abcf2d1eccd5eb79df851804d2ac6fd75",
    44: "82c443c774d394a23127c0d66fd829f7f99a83e622e97a7b8e255db03c0d2d48",
    45: "c09764878d0d0d4f40ed91d6e5e5e32ddf432fc8e1fb84a5181f3aba365e1d47",
    46: "fd2317415e96c5b3cc51f944443b79f9a641725636fb482cbca3aa88e6d7f22c",
    47: "7f2b12088c43f11512cf5a5a8fe52beebc3c7b3a12051c5508fb8a25119eee34",
    48: "6c8b085e04ccf58dae618b1ec85941d2db0dac71061cb02a9280cefc4e19c186",
    49: "7b72fddf12936390ab46902418129de1fade11640cb7d65662277608b2f9d30a",
    50: "595b3d566a6d820573632a5dc853afb2c0cf8474fab8693a57d84ff33335ae63",
}
EXPECTED = {
    SOURCE_PDF: (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    CENSUS: (11_700, "20ef255184a6e31476b368bd8b1ad08c39ea2ab9f6fdc1fa2c53574471a95055"),
    WITNESS: (22_457, "db45c443fb4e978b6bb4681a228a279f83048b8210530f77ed772a82c5f324a4"),
    TARGET: (24_496, "b0c8b0418db9029441db23ad7deac1bed8a187ef9ae5ecd61ccfb56ce2a78758"),
    CSS: (2_777, "4f5bb04dc8f30c5e383fc901dea1817168446ad6f6761e21a8dfdd9fb961ab1b"),
    PREAMBLE: (1_499, "992ea616347c2719f9a42770a14efff6c8086bcff13c47308774b0333491575d"),
    PDF_FILTER: (499, "b8f11b413c30aaccaa0e014821e4e8fc32eb322a10734d092ee5ccdd46f8f9be"),
    BEFORE_BODY: (96, "d01225930c277dbd82aff342aa0addb5fb8b626dc734e4594dbdc86e481a1e8c"),
    AFTER_BODY: (170, "045428641fba6fc618c15fec3c5ca3558def4b0f946e1d53094eba4e4972794c"),
    BUILDER: (4_103, "310afb3855091dfda44f39dcce99d560d5805ea2eae2fdef6d3d09345e62ec4d"),
    VISUAL_QA: (1_380, "ee2d7378d90b51bc9ba167fee95fe7d56d2022d21145a6db8cba45a6dcd8fcfe"),
    BROWSER_QA: (1_258, "fae4f199316c1592256b46a5cc0a2099397ba9316d56cd00fda144c5fc83bcb8"),
}
EXPECTED_BUILD = {
    "html": (113_898, "b084dd10113b55e7789885d0ec303376c0bca58fdbb960b428ce1feac9e30c0a"),
    "pdf": (91_293, "b01517ee401e0b9f069e4f121f57e1bc3a482b9ceb69cba067c4371f11a47e62"),
}
EXPECTED_RENDER = [
    "cfe58afab4f8f8b0385b8d579a144c366d02fafe542541760c4399f22cffed2d",
    "9dd395c3e778a97196a039a66d778259ee52b46277f2aa03e2c5f4c7b91f8186",
    "63ccc60daf2a9b3bdd5b28c7b889b936efe46709bd5263ca2fb5033ee9437529",
    "94f49edb656d6c0305ed2ec9d4c24e5635a52027894d2dcf7ba9571b10a42988",
    "014aeef713579ea1e340cff84b042a9226b79cdce6badcdbb276b32db88c60d3",
    "721352d2d324f75b70ee8be7629bbfec4d0430272c9456940ae28cee06a51409",
]
EVENT_IDS = ("O015-MIT-SEM-0009", "O015-MIT-SEM-0010", "O015-MIT-SEM-0011")


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
    records: list[dict[str, Any]] = []
    for node in walk(value):
        if node.get("t") != "Div":
            continue
        identifier, classes, attrs = node["c"][0]
        if class_name in classes:
            records.append({"id": identifier, "attrs": dict(attrs), "blocks": node["c"][1]})
    return records


def nested_counts(path: Path) -> Counter[int]:
    text = path.read_text(encoding="utf-8")
    starts = list(
        re.finditer(
            r'^::: \{\.source-page\s+#[^\s}]+[^\n]*data-source-page="(\d+)"[^\n]*\}\s*$',
            text,
            flags=re.MULTILINE,
        )
    )
    counts: Counter[int] = Counter()
    marker = re.compile(
        r"^\s{2,}(?:-\s+|\*{0,2}\((?:[a-z]|i{1,3}|iv|v)\)\*{0,2}\s+)",
        flags=re.MULTILINE,
    )
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        counts[int(match.group(1))] = len(marker.findall(text[match.end() : end]))
    return counts


def source_topology(path: Path) -> dict[str, Any]:
    document = ast(path)
    return {
        "pages": div_records(document, "source-page"),
        "items": div_records(document, "source-item"),
        "displays": div_records(document, "source-display"),
        "figures": div_records(document, "source-figure"),
        "nested_by_page": nested_counts(path),
        "display_math": [
            re.sub(r"\s+", "", node["c"][1].strip())
            for node in walk(document)
            if node.get("t") == "Math" and node["c"][0]["t"] == "DisplayMath"
        ],
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
        self.interactive = 0
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
        if tag in {"button", "input", "select", "textarea"}:
            self.interactive += 1
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


def adverse_events() -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    events: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for line in ADVERSE_LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        event_id = event.get("event_id")
        if event_id in EVENT_IDS:
            counts[event_id] += 1
            events[event_id] = event
    return events, counts


def validate_html(path: Path, errors: list[str]) -> tuple[SurfaceParser, list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    parser = SurfaceParser()
    parser.feed(text)
    duplicate_ids = sorted(identifier for identifier, count in Counter(parser.ids).items() if count > 1)
    unresolved = sorted(set(parser.fragments) - set(parser.ids))
    check(parser.lang == "id-ID" and parser.main == 1, "HTML language or main landmark differs", errors)
    check(parser.headings == Counter({"h2": 12, "h1": 1}), f"HTML heading topology differs: {parser.headings}", errors)
    check(
        (parser.source_pages, parser.source_items, parser.source_displays, parser.source_figures) == (11, 27, 26, 5),
        "HTML source topology differs",
        errors,
    )
    check(parser.math == 247 and parser.display_math == 26, "HTML MathML topology differs", errors)
    check(parser.ordered_items == 10, f"HTML ordered-list item count differs: {parser.ordered_items}", errors)
    check(parser.images == 0 and parser.media == 0 and parser.interactive == 0, "HTML contains image, media, or form controls", errors)
    check("data:image" not in text, "HTML contains an embedded data image", errors)
    check(parser.skip_target == "#d90-mit-l08-p039", f"skip-link target differs: {parser.skip_target}", errors)
    check(not duplicate_ids and not unresolved, f"HTML ID closure differs: duplicate={duplicate_ids}, unresolved={unresolved}", errors)
    check(LICENSE_URI in parser.links, "HTML lacks the exact component license URI", errors)
    return parser, duplicate_ids, unresolved


def validate_pdf(path: Path, errors: list[str]) -> PdfReader:
    reader = PdfReader(path)
    root = reader.trailer["/Root"]
    check(len(reader.pages) == 6, f"PDF page count {len(reader.pages)} != 6", errors)
    check(root.get("/Lang") == "id-ID", f"PDF /Lang differs: {root.get('/Lang')}", errors)
    check("/StructTreeRoot" not in root, "PDF unexpectedly claims tagged structure", errors)
    check(not reader.is_encrypted, "PDF is encrypted", errors)
    check(
        (reader.metadata or {}).get("/Producer") == f"{MODEL} - user-directed production assistance",
        "PDF producer provenance differs",
        errors,
    )
    check(LICENSE_URI in pdf_uris(reader), "PDF lacks the exact component license URI", errors)
    fonts: dict[str, bool] = {}
    for page in reader.pages:
        check(
            abs(float(page.mediabox.width) - 595.276) < 0.02
            and abs(float(page.mediabox.height) - 841.89) < 0.02,
            "PDF page is not A4",
            errors,
        )
        for name, ref in page.get("/Resources", {}).get("/Font", {}).items():
            fonts[str(name)] = bool(ref.get_object().get("/ToUnicode"))
    check(bool(fonts) and all(fonts.values()), f"PDF ToUnicode coverage differs: {fonts}", errors)
    check(not image_rows(path), "output PDF contains a raster image XObject", errors)
    searchable = subprocess.run(
        ["pdftotext", str(path), "-"], cwd=ROOT, capture_output=True, check=True
    ).stdout.decode("utf-8")
    for phrase in (
        "Kuliah 4 - Garis Besar Kuliah",
        "Interior Relatif",
        "Hasil-Hasil Utama Tambahan",
        "Penerapan Optimisasi",
        "Ringkasan Kalkulus Interior Relatif",
        "Penutupan versus Interior Relatif",
        "Transformasi Linear",
        "Irisan dan Jumlah Vektor",
        "Produk Kartesius - Generalisasi",
        "Kontinuitas Fungsi Konveks",
        "Penutupan Fungsi",
        "Halaman sumber 49.",
    ):
        check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)
    return reader


def render(path: Path, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "page"
    subprocess.run(
        ["pdftoppm", "-r", "160", "-png", str(path), str(prefix)],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return [digest(item) for item in sorted(output_dir.glob("page-*.png"))]


def main() -> int:
    errors: list[str] = []
    for path, expected in EXPECTED.items():
        check(path.is_file(), f"missing required file: {path.relative_to(ROOT)}", errors)
        if path.is_file():
            check(
                (path.stat().st_size, digest(path)) == expected,
                f"identity mismatch: {path.relative_to(ROOT)}",
                errors,
            )
    check(ADVERSE_LEDGER.is_file(), "missing adverse ledger", errors)

    source_text_hashes: dict[str, str] = {}
    target_top: dict[str, Any] = {}
    witness_top: dict[str, Any] = {}
    events: dict[str, dict[str, Any]] = {}
    event_counts: Counter[str] = Counter()
    parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    reader: PdfReader | None = None
    rebuilds: list[dict[str, tuple[int, str]]] = []
    render_hashes: list[list[str]] = []
    canonical: dict[str, Any] = {"status": "not_present_yet"}

    if not errors:
        try:
            source_reader = PdfReader(SOURCE_PDF)
            check(len(source_reader.pages) == 340, "authority PDF page count is not 340", errors)
            for page in range(39, 51):
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
                    check("LECTURE 5" in text and "LECTURE OUTLINE" in text, "page 50 is not the clean Lecture 5 delimiter", errors)
            authority_rows = image_rows(SOURCE_PDF, 39, 49)
            substantive_rows = [
                row for row in authority_rows
                if len(row.split()) >= 5 and int(row.split()[3]) > 1 and int(row.split()[4]) > 1
            ]
            check(len(authority_rows) == 7 and len(substantive_rows) == 4, "authority pages 39-49 image inventory differs", errors)
            for page in source_reader.pages[38:50]:
                check(not (page.get("/Annots") or []), "authority pages 39-50 contain an annotation", errors)
            check(not (source_reader.get_fields() or {}), "authority PDF exposes form fields", errors)
            source_root = source_reader.trailer["/Root"]
            check("/OpenAction" not in source_root, "authority PDF has an open action", errors)
            check("/JavaScript" not in (source_root.get("/Names") or {}), "authority PDF has a JavaScript name tree", errors)

            census_text = CENSUS.read_text(encoding="utf-8")
            for phrase in ("PDF pages **39-49**", "page 50", "**27**", "**16**", "**26**", "**5 / 5**"):
                check(phrase in census_text, f"boundary census lacks {phrase!r}", errors)

            target_text = TARGET.read_text(encoding="utf-8")
            witness_text = WITNESS.read_text(encoding="utf-8")
            normalized_target = re.sub(r"\s+", " ", target_text)
            normalized_witness = re.sub(r"\s+", " ", witness_text)
            for phrase in (
                MODEL,
                "CC BY-NC-SA 4.0",
                LICENSE_URI,
                "Athena Scientific",
                "Tidak ada byte, potongan, atau tata letak gambar sumber",
                "O015-MIT-SEM-0009",
                "O015-MIT-SEM-0010",
                "O015-MIT-SEM-0011",
                "Tinjauan bahasa manusia/penutur asli belum tercatat",
                "Tanpa mengurangi keumuman",
                "Jika $x_k=0$",
                r"A^{-1}(\operatorname{ri}C)\neq\varnothing",
                "citra elipsoidal atau degenerat itu memuat bola relatif",
            ):
                check(phrase in normalized_target, f"target lacks {phrase!r}", errors)
            for phrase in (
                MODEL,
                "CC BY-NC-SA 4.0",
                "Athena Scientific",
                "LECTURE 4",
                "CLOSURES OF FUNCTIONS",
                "maps spheres onto spheres",
                "Possible missing qualification",
                "Possible omitted edge case",
            ):
                check(phrase in normalized_witness, f"witness lacks {phrase!r}", errors)
            check(target_text.count(MODEL) == 1 and witness_text.count(MODEL) == 1, "model identification count differs", errors)
            check(target_text.count(r"f:\mathbb{R}^n\to\mathbb{R}") == 2, "target real-valued type-arrow count differs", errors)
            check(target_text.count(r"f:X\to[-\infty,\infty]") == 3, "target extended-valued type-arrow count differs", errors)
            check(target_text.count(r"\operatorname{cl}f:\mathbb{R}^n\to[-\infty,\infty]") == 1, "target closure type-arrow count differs", errors)
            check(witness_text.count(r"f:\mathbb{R}^n\mapsto\mathbb{R}") == 2, "witness real-valued mapsto count differs", errors)
            check(witness_text.count(r"f:X\mapsto[-\infty,\infty]") == 3, "witness extended-valued mapsto count differs", errors)
            check(witness_text.count(r"\operatorname{cl}f:\mathbb{R}^n\mapsto[-\infty,\infty]") == 1, "witness closure mapsto count differs", errors)
            check("![" not in target_text and "![" not in witness_text, "semantic source embeds an image", errors)
            check("```" not in target_text and "```" not in witness_text, "semantic source contains a code fence", errors)

            events, event_counts = adverse_events()
            check(set(events) == set(EVENT_IDS) and all(event_counts[event_id] == 1 for event_id in EVENT_IDS), "required adverse events are absent or duplicated", errors)
            expected_event_classes = {
                "O015-MIT-SEM-0009": "determined_notation_correction",
                "O015-MIT-SEM-0010": "determined_missing_hypothesis_correction",
                "O015-MIT-SEM-0011": "determined_geometric_intuition_correction",
            }
            for event_id, expected_class in expected_event_classes.items():
                event = events.get(event_id, {})
                check(event.get("authority") == "o015-mit-ocw-6.253-spring-2012", f"{event_id} authority differs", errors)
                check(event.get("class") == expected_class, f"{event_id} class differs", errors)
                check("mit-08-lecture-4" in event.get("source", ""), f"{event_id} source binding differs", errors)

            target_top = source_topology(TARGET)
            witness_top = source_topology(WITNESS)
            for label, top in (("target", target_top), ("witness", witness_top)):
                expected_pages = [(str(page - 38), str(page), f"d90-mit-l08-p{page:03d}") for page in PAGE_COUNTS]
                actual_pages = [
                    (record["attrs"]["data-source-order"], record["attrs"]["data-source-page"], record["id"])
                    for record in top["pages"]
                ]
                check(actual_pages == expected_pages, f"{label} page map differs", errors)
                expected_items = [
                    (page, order, f"d90-mit-l08-p{page:03d}-i{order:03d}")
                    for page, counts in PAGE_COUNTS.items()
                    for order in range(1, counts[0] + 1)
                ]
                actual_items = [
                    (int(record["attrs"]["data-source-page"]), int(record["attrs"]["data-source-order"]), record["id"])
                    for record in top["items"]
                ]
                check(actual_items == expected_items, f"{label} item map differs", errors)
                expected_displays = [
                    (page, order, f"d90-mit-l08-p{page:03d}-d{order:03d}")
                    for page, counts in PAGE_COUNTS.items()
                    for order in range(1, counts[2] + 1)
                ]
                actual_displays = [
                    (int(record["attrs"]["data-source-page"]), int(record["attrs"]["data-display-order"]), record["id"])
                    for record in top["displays"]
                ]
                check(actual_displays == expected_displays, f"{label} display map differs", errors)
                figure_pages = [page for page, counts in PAGE_COUNTS.items() if counts[3]]
                expected_figures = [(page, f"d90-mit-l08-p{page:03d}-f001") for page in figure_pages]
                actual_figures = [
                    (int(record["attrs"]["data-source-page"]), record["id"])
                    for record in top["figures"]
                ]
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
                check(
                    (len(top["items"]), sum(top["nested_by_page"].values()), len(top["displays"]), len(top["figures"])) == (27, 16, 26, 5),
                    f"{label} total topology differs",
                    errors,
                )
                check(len(top["display_math"]) == 26, f"{label} display-math count differs", errors)

            (ROOT / "tmp/pdfs").mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="mit-l08-determinism-", dir=ROOT / "tmp/pdfs") as temp:
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
                    build_identity = {
                        "html": (html.stat().st_size, digest(html)),
                        "pdf": (pdf.stat().st_size, digest(pdf)),
                    }
                    rebuilds.append(build_identity)
                    render_hashes.append(render(pdf, temp_root / f"render-{label}"))
                check(rebuilds[0] == rebuilds[1] == EXPECTED_BUILD, f"deterministic rebuild identities differ: {rebuilds}", errors)
                check(render_hashes[0] == render_hashes[1] == EXPECTED_RENDER, f"deterministic render hashes differ: {render_hashes}", errors)
                parser, duplicate_ids, unresolved = validate_html(temp_root / "a" / HTML.name, errors)
                reader = validate_pdf(temp_root / "a" / PDF.name, errors)

            visual = json.loads(VISUAL_QA.read_text(encoding="utf-8"))
            inspection = visual.get("inspection", {})
            check(inspection.get("result") == "pass", "visual QA is not pass", errors)
            check(inspection.get("pages_inspected") == [1, 2, 3, 4, 5, 6], "visual QA page inventory differs", errors)
            for key in ("black_boxes", "clipped_content", "formula_damage", "malformed_lists", "missing_glyphs", "overlap"):
                check(inspection.get(key) == 0, f"visual QA {key} differs", errors)
            check(visual.get("pdf", {}).get("sha256") == EXPECTED_BUILD["pdf"][1], "visual QA does not bind deterministic PDF", errors)
            check([entry.get("sha256") for entry in visual.get("renders", [])] == EXPECTED_RENDER, "visual QA render hashes differ", errors)

            browser = json.loads(BROWSER_QA.read_text(encoding="utf-8"))
            check(browser.get("result") == "pass", "browser QA is not pass", errors)
            check(browser.get("build", {}).get("html_sha256") == EXPECTED_BUILD["html"][1], "browser QA does not bind deterministic HTML", errors)
            for viewport in ("desktop", "mobile"):
                metrics = browser.get(viewport, {})
                check(
                    metrics.get("horizontal_overflow") is False
                    and metrics.get("client_width") == metrics.get("document_width")
                    and metrics.get("math_overflow_ids") == []
                    and metrics.get("display_overflow_ids") == []
                    and metrics.get("broken_fragments") == []
                    and metrics.get("duplicate_ids") == []
                    and metrics.get("console_warnings_or_errors") == [],
                    f"browser {viewport} reflow or closure gate differs",
                    errors,
                )
                check(
                    (
                        metrics.get("source_pages"),
                        metrics.get("source_items"),
                        metrics.get("source_displays"),
                        metrics.get("source_figures"),
                    )
                    == (11, 27, 26, 5),
                    f"browser {viewport} semantic topology differs",
                    errors,
                )

            if HTML.exists() != PDF.exists():
                canonical = {"status": "incomplete_pair"}
                errors.append("canonical L08 output pair is incomplete")
            elif HTML.exists() and PDF.exists():
                canonical = {
                    "status": "bound",
                    "html": identity(HTML),
                    "pdf": identity(PDF),
                }
                check((HTML.stat().st_size, digest(HTML)) == EXPECTED_BUILD["html"], "canonical HTML identity differs from deterministic build", errors)
                check((PDF.stat().st_size, digest(PDF)) == EXPECTED_BUILD["pdf"], "canonical PDF identity differs from deterministic build", errors)
        except Exception as exc:  # Fail closed while still emitting the receipt.
            errors.append(f"validation exception: {type(exc).__name__}: {exc}")

    result = "pass" if not errors else "fail"
    report = {
        "schema": "o015-mit-l08-validation-v1",
        "validation_epoch": "2026-08-24",
        "result": result,
        "boundary": {
            "source_pdf_pages": list(range(39, 50)),
            "next_source_page": 50,
            "next_heading": "LECTURE 5 - LECTURE OUTLINE",
            "source_items": 27,
            "nested_items": 16,
            "source_displays": 26,
            "source_figures": 5,
            "source_figure_panels": 5,
            "copied_source_graphics": 0,
            "exercises": 0,
            "code_surfaces": 0,
            "interactive_surfaces": 0,
        },
        "files": [identity(path) for path in EXPECTED if path.exists()],
        "source_page_text_sha256": source_text_hashes,
        "formula_inventory": {
            "target_display_blocks": len(target_top.get("display_math", [])),
            "witness_display_blocks": len(witness_top.get("display_math", [])),
            "target_sequence_sha256": hashlib.sha256("\n".join(target_top.get("display_math", [])).encode("utf-8")).hexdigest() if target_top else None,
            "witness_sequence_sha256": hashlib.sha256("\n".join(witness_top.get("display_math", [])).encode("utf-8")).hexdigest() if witness_top else None,
        },
        "adverse_event_bindings": {event_id: events.get(event_id, {}) for event_id in EVENT_IDS},
        "build": {
            "command": "python qa/build_mit_l08.py --html-output <html> --pdf-output <pdf>",
            "deterministic_rebuilds": 2,
            "rebuild_identities": rebuilds,
            "render_sha256": render_hashes,
            "expected": EXPECTED_BUILD,
            "canonical": canonical,
        },
        "html": {
            "lang": parser.lang,
            "headings": dict(sorted(parser.headings.items())),
            "source_pages": parser.source_pages,
            "source_items": parser.source_items,
            "source_displays": parser.source_displays,
            "source_figures": parser.source_figures,
            "math_nodes": parser.math,
            "display_math_nodes": parser.display_math,
            "ordered_list_items": parser.ordered_items,
            "images": parser.images,
            "media_or_embeds": parser.media,
            "form_controls": parser.interactive,
            "duplicate_ids": duplicate_ids,
            "unresolved_fragments": unresolved,
        },
        "pdf": {
            "pages": len(reader.pages) if reader else None,
            "page_size": "A4",
            "searchable": True,
            "tagged": False,
            "images": 0,
            "render_sha256": render_hashes[0] if render_hashes else [],
        },
        "rights": {
            "component": "MIT OCW 6.253 complete-notes",
            "license": "CC BY-NC-SA 4.0",
            "license_uri": LICENSE_URI,
            "athena_source_figure_blocks_omitted": 5,
            "athena_source_figure_panels_omitted": 5,
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
