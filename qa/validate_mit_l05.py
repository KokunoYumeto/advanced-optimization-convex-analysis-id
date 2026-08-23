#!/usr/bin/env python3
"""Fail-closed validation for MIT 6.253 complete-notes pages 16-19."""

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
WITNESS = ROOT / "source/en/mit-05-course-orientation-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-05-orientasi-kursus-id.md"
CSS = ROOT / "source/id-ID/mit-l05.css"
HTML = ROOT / "output/html/D90-MIT-05-orientasi-kursus-id.html"
PDF = ROOT / "output/pdf/D90-MIT-05-orientasi-kursus-id.pdf"
BUILDER = ROOT / "qa/build_mit_l05.py"
BROWSER_QA = ROOT / "qa/MIT_L05_BROWSER_QA.json"
VISUAL_QA = ROOT / "qa/MIT_L05_VISUAL_QA.json"
REREVIEW = ROOT / "qa/MIT_L05_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L05_VALIDATION.json"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
SOURCE_URIS = {
    "http://www.athenasc.com/convexduality.html",
    "http://www.stanford.edu/~boyd/cvxbook/",
}

EXPECTED = {
    SOURCE_PDF: (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    WITNESS: (7_120, "3acbde47074da0429419e5c702785ee0490efa5e43f2b07cbac497f0d480492f"),
    TARGET: (8_702, "65cb7fec2d6b1aeda69837e10568f2410a9f4bded2b835b8dac59a9b516444cc"),
    CSS: (2_636, "d8d8417c4d2f9e01852cd30bc97552f377da3a6d1f9bbee25c25d47e16ce9645"),
    HTML: (16_029, "424d854bb1e83e841a15d0073aad3db6bab0585ca6d587fd14a3b5cfb4274d83"),
    PDF: (46_785, "2af9e4dc8e999969f03817350451c4b21f3c764564eee64327d15b48483313c0"),
    BUILDER: (3_598, "e73c411cb4e1619b326af78b2cc8e72c4fcc80bc9e404b7077ece948bf8c6df8"),
    BROWSER_QA: (1_271, "24b775fb6afc271a16a62097151175852a4a01eb1c41605a196258e19f01d342"),
    VISUAL_QA: (1_544, "d32b4e66cf7c1fd4f9fa06c75f88bfb80404caeefe894ba92396c548d126af04"),
    REREVIEW: (3_066, "c1c358c32f245ca4ef1c15efe3ed4d319f9bdef758319bce04f501bb525f7fb9"),
}
EXPECTED_RENDER = [
    "8eb2b8ef60b5bd96f63f4d8523b406106cce198370481eb4c93224412440f3d7",
    "162ec00ed10f6b95a3b31c8456fcc44c69f82972758827e979a8b5aca933f7fe",
    "f351a2a526ae555f5d487121b0d20d43e458775cfbf7ddb6dc90371d4697869f",
]
SOURCE_TOPOLOGY = {
    16: ("METHODOLOGICAL TRENDS", 3, 7),
    17: ("COURSE OUTLINE", 3, 12),
    18: ("WHAT TO EXPECT FROM THIS COURSE", 4, 7),
    19: ("A NOTE ON THESE SLIDES", 6, 0),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def ast_nodes(path: Path) -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["pandoc", str(path), "--from=markdown+fenced_divs+yaml_metadata_block", "--to=json"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return list(walk(json.loads(completed.stdout.decode("utf-8"))))


def div_records(nodes: list[dict[str, Any]], class_name: str) -> list[dict[str, Any]]:
    records = []
    for node in nodes:
        if node.get("t") != "Div":
            continue
        identifier, classes, attrs = node["c"][0]
        if class_name in classes:
            records.append(
                {
                    "id": identifier,
                    "classes": classes,
                    "attrs": dict(attrs),
                    "blocks": node["c"][1],
                }
            )
    return records


def topology(path: Path) -> dict[str, Any]:
    nodes = ast_nodes(path)
    pages = div_records(nodes, "source-page")
    items = div_records(nodes, "source-item")
    figures = div_records(nodes, "source-figure")
    nested = 0
    for item in items:
        lists = [node for node in walk(item["blocks"]) if node.get("t") == "BulletList"]
        nested += max(0, sum(len(node["c"]) for node in lists) - 1)
    links = []
    for node in nodes:
        if node.get("t") == "Link":
            links.append(node["c"][2][0])
    return {
        "pages": pages,
        "items": items,
        "figures": figures,
        "nested": nested,
        "math": [node for node in nodes if node.get("t") == "Math"],
        "links": links,
        "pages_order": sorted(
            (
                int(record["attrs"]["data-source-order"]),
                int(record["attrs"]["data-source-page"]),
                record["id"],
            )
            for record in pages
        ),
        "items_order": sorted(
            (
                int(record["attrs"]["data-source-page"]),
                int(record["attrs"]["data-source-order"]),
                record["id"],
            )
            for record in items
        ),
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
        self.math = 0
        self.headings: Counter[str] = Counter()
        self.skip_target = ""
        self.source_pages = 0
        self.source_items = 0
        self.source_figures = 0

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
        if tag == "math":
            self.math += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings[tag] += 1
        self.source_pages += "source-page" in classes
        self.source_items += "source-item" in classes
        self.source_figures += "source-figure" in classes


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def pdf_uris(reader: PdfReader) -> list[str]:
    uris: list[str] = []
    for page in reader.pages:
        for annotation_ref in page.get("/Annots") or []:
            annotation = annotation_ref.get_object()
            action = annotation.get("/A") or {}
            uri = action.get("/URI")
            if uri:
                uris.append(str(uri))
    return uris


def main() -> int:
    errors: list[str] = []
    for path, expected in EXPECTED.items():
        check(path.exists(), f"missing required file: {path.relative_to(ROOT)}", errors)
        if path.exists():
            check(
                (path.stat().st_size, digest(path)) == expected,
                f"identity mismatch: {path.relative_to(ROOT)}",
                errors,
            )

    source_texts: dict[str, str] = {}
    target_top: dict[str, Any] = {}
    witness_top: dict[str, Any] = {}
    parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    reader: PdfReader | None = None
    browser: dict[str, Any] = {}
    if not errors:
        source_reader = PdfReader(SOURCE_PDF)
        check(len(source_reader.pages) == 340, "authority PDF page count is not 340", errors)
        for page, (heading, top_count, nested_count) in SOURCE_TOPOLOGY.items():
            text = subprocess.run(
                ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(SOURCE_PDF), "-"],
                capture_output=True,
                check=True,
            ).stdout.decode("utf-8")
            source_texts[str(page)] = text
            check(heading in text, f"authority page {page} lacks heading {heading!r}", errors)
            check(text.count("•") == top_count, f"authority page {page} top-level count differs", errors)
            check(text.count("−") == nested_count, f"authority page {page} nested count differs", errors)
        successor = subprocess.run(
            ["pdftotext", "-layout", "-f", "20", "-l", "20", str(SOURCE_PDF), "-"],
            capture_output=True,
            check=True,
        ).stdout.decode("utf-8")
        check("LECTURE 2" in successor and "LECTURE OUTLINE" in successor, "page 20 is not the expected clean successor", errors)
        image_listing = subprocess.run(
            ["pdfimages", "-list", "-f", "16", "-l", "19", str(SOURCE_PDF)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        image_rows = [line for line in image_listing.splitlines() if re.match(r"^\s*\d+\s+\d+\s+", line)]
        check(not image_rows, f"authority pages 16-19 unexpectedly have image rows: {image_rows}", errors)
        source_page_17_uris = set()
        for annotation_ref in source_reader.pages[16].get("/Annots") or []:
            action = annotation_ref.get_object().get("/A") or {}
            if action.get("/URI"):
                source_page_17_uris.add(str(action["/URI"]))
        check(source_page_17_uris == SOURCE_URIS, f"source page 17 URI closure differs: {source_page_17_uris}", errors)

        target_text = TARGET.read_text(encoding="utf-8")
        witness_text = WITNESS.read_text(encoding="utf-8")
        normalized_target = re.sub(r"\s+", " ", target_text)
        normalized_witness = re.sub(r"\s+", " ", witness_text)
        for phrase in (
            MODEL,
            "CC BY-NC-SA 4.0",
            "Tren Metodologis",
            "Garis Besar Kursus",
            "Apa yang Dapat Diharapkan dari Kursus Ini",
            "Catatan tentang Slide Ini",
            "Vanderbergue",
            "Vandenberghe",
            "Metode subgradien/inkremental",
            "Aproksimasi polihedral/metode bidang potong",
            "metode gradien terekstrapolasi",
            "O015-MIT-SEM-0004",
            "Kuliah 2",
        ):
            check(phrase in normalized_target, f"target lacks {phrase!r}", errors)
        for phrase in (
            MODEL,
            "CC BY-NC-SA 4.0",
            "METHODOLOGICAL TRENDS",
            "COURSE OUTLINE",
            "WHAT TO EXPECT FROM THIS COURSE",
            "A NOTE ON THESE SLIDES",
            "Vanderbergue",
            "Vandenberghe",
            "LECTURE 2",
        ):
            check(phrase in normalized_witness, f"witness lacks {phrase!r}", errors)
        check("![" not in target_text and "![" not in witness_text, "semantic source embeds an image", errors)
        check("not official editable MIT source" in normalized_witness, "witness lacks reconstruction limitation", errors)
        check("TTP" not in normalized_target and "TTP" not in normalized_witness, "forbidden TTP mention in L05 source", errors)

        target_top = topology(TARGET)
        witness_top = topology(WITNESS)
        expected_target_pages = [(i - 15, i, f"d90-mit-l05-p{i:03d}") for i in range(16, 20)]
        expected_witness_pages = [(i - 15, i, f"src-mit-l05-p{i:03d}") for i in range(16, 20)]
        check(target_top["pages_order"] == expected_target_pages, f"target page map differs: {target_top['pages_order']}", errors)
        check(witness_top["pages_order"] == expected_witness_pages, f"witness page map differs: {witness_top['pages_order']}", errors)
        expected_target_items = []
        expected_witness_items = []
        for page, count in ((16, 3), (17, 3), (18, 4), (19, 6)):
            expected_target_items.extend((page, i, f"d90-mit-l05-p{page:03d}-i{i:03d}") for i in range(1, count + 1))
            expected_witness_items.extend((page, i, f"src-mit-l05-p{page:03d}-i{i:03d}") for i in range(1, count + 1))
        check(target_top["items_order"] == expected_target_items, "target item map differs", errors)
        check(witness_top["items_order"] == expected_witness_items, "witness item map differs", errors)
        for label, top in (("target", target_top), ("witness", witness_top)):
            check(len(top["pages"]) == 4 and len(top["items"]) == 16 and len(top["figures"]) == 0, f"{label} div closure differs", errors)
            check(top["nested"] == 26 and not top["math"], f"{label} list/math topology differs", errors)
            ids = [record["id"] for record in top["pages"] + top["items"] + top["figures"]]
            check(len(ids) == len(set(ids)), f"duplicate {label} stable IDs", errors)
        check(SOURCE_URIS <= set(target_top["links"]), "target does not preserve both source URIs", errors)
        check(set(witness_top["links"]) == SOURCE_URIS, "witness URI closure differs", errors)

        html_text = HTML.read_text(encoding="utf-8")
        parser.feed(html_text)
        duplicate_ids = sorted(identifier for identifier, count in Counter(parser.ids).items() if count > 1)
        unresolved = sorted(set(parser.fragments) - set(parser.ids))
        check(parser.lang == "id-ID", f"HTML lang is {parser.lang!r}", errors)
        check(parser.main == 1, f"HTML main count {parser.main} != 1", errors)
        check(parser.headings == Counter({"h1": 1, "h2": 6}), f"HTML headings differ: {parser.headings}", errors)
        check(parser.source_pages == 4 and parser.source_items == 16 and parser.source_figures == 0, "HTML semantic topology differs", errors)
        check(parser.images == 0 and parser.math == 0, "HTML has image or math surface", errors)
        check(parser.skip_target == "#d90-mit-l05-p016", f"skip link target differs: {parser.skip_target}", errors)
        check(not duplicate_ids and not unresolved, f"HTML ID closure differs: duplicate={duplicate_ids}, unresolved={unresolved}", errors)
        check(SOURCE_URIS <= set(parser.links), "HTML does not preserve both source URIs", errors)
        check(re.sub(r"\s+", " ", html_text).count(MODEL) == 1, "exact model provenance must occur once in HTML", errors)

        browser = json.loads(BROWSER_QA.read_text(encoding="utf-8"))
        check(browser.get("result") == "pass", "browser QA is not pass", errors)
        check(browser.get("browser_available") is True, "browser QA does not record a live browser", errors)
        check(browser.get("html", {}).get("sha256") == digest(HTML), "browser QA does not bind canonical HTML", errors)
        browser_topology = browser.get("topology", {})
        check(browser_topology.get("source_pages") == 4 and browser_topology.get("source_items") == 16 and browser_topology.get("source_figures") == 0, "browser topology differs", errors)
        check(set(browser_topology.get("unique_source_uris", [])) == SOURCE_URIS, "browser URI closure differs", errors)
        check(browser_topology.get("duplicate_ids") == 0 and browser_topology.get("unresolved_fragments") == 0, "browser ID closure differs", errors)
        check(browser_topology.get("skip_link") == "#d90-mit-l05-p016", "browser skip-link target differs", errors)
        for viewport in ("desktop", "mobile"):
            measurement = browser.get(viewport, {})
            check(measurement.get("scroll_width") == measurement.get("client_width"), f"{viewport} width measurement differs", errors)
            check(measurement.get("horizontal_overflow") is False, f"{viewport} has horizontal overflow", errors)
            check(measurement.get("console_warnings_or_errors") == [], f"{viewport} console is not clean", errors)

        visual = json.loads(VISUAL_QA.read_text(encoding="utf-8"))
        check(visual.get("result") == "pass", "visual QA is not pass", errors)
        check(visual.get("surface", {}).get("sha256") == digest(PDF), "visual QA does not bind canonical PDF", errors)
        check([entry.get("sha256") for entry in visual.get("render", {}).get("files", [])] == EXPECTED_RENDER, "visual render hashes differ", errors)

        rereview_text = REREVIEW.read_text(encoding="utf-8")
        check("P1=0, P2=0, P3=0" in rereview_text, "rereview does not close severity counts", errors)
        check(digest(TARGET) in rereview_text and digest(PDF) in rereview_text, "rereview lacks canonical bindings", errors)

        reader = PdfReader(PDF)
        root = reader.trailer["/Root"]
        check(len(reader.pages) == 3, f"PDF pages {len(reader.pages)} != 3", errors)
        check(root.get("/Lang") == "id-ID", f"PDF /Lang differs: {root.get('/Lang')}", errors)
        check("/StructTreeRoot" not in root, "PDF unexpectedly claims tagged structure", errors)
        check((reader.metadata or {}).get("/Producer") == f"{MODEL} - user-directed production assistance", "PDF producer provenance differs", errors)
        searchable = "\n".join(page.extract_text() or "" for page in reader.pages)
        for phrase in ("Tren Metodologis", "Garis Besar Kursus", "Persyaratan", "Catatan tentang Slide Ini", "Vanderbergue", "Vandenberghe"):
            check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)
        output_uris = set(pdf_uris(reader))
        check(SOURCE_URIS <= output_uris, f"PDF URI closure differs: {output_uris}", errors)
        fonts: dict[str, bool] = {}
        for page in reader.pages:
            for name, ref in page.get("/Resources", {}).get("/Font", {}).items():
                fonts[str(name)] = bool(ref.get_object().get("/ToUnicode"))
            check(abs(float(page.mediabox.width) - 595.276) < 0.02 and abs(float(page.mediabox.height) - 841.89) < 0.02, "PDF page is not A4", errors)
        check(bool(fonts) and all(fonts.values()), f"PDF ToUnicode coverage differs: {fonts}", errors)

        with tempfile.TemporaryDirectory(prefix="o015-mit-l05-", dir=ROOT / "tmp/pdfs") as temp:
            temp_root = Path(temp)
            rebuilds = []
            for label in ("a", "b"):
                out = temp_root / label
                html = out / HTML.name
                pdf = out / PDF.name
                subprocess.run(
                    [sys.executable, str(BUILDER), "--html-output", str(html), "--pdf-output", str(pdf)],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                )
                rebuilds.append((digest(html), digest(pdf)))
            expected_pair = (digest(HTML), digest(PDF))
            check(rebuilds[0] == rebuilds[1] == expected_pair, f"deterministic rebuilds differ: {rebuilds}", errors)

        render_hashes = [digest(path) for path in sorted((ROOT / "tmp/pdfs/mit-l05-final-visual").glob("page-*.png"))]
        check(render_hashes == EXPECTED_RENDER, f"render hashes differ: {render_hashes}", errors)

    result = "pass" if not errors else "fail"
    page_text_hashes = {
        page: hashlib.sha256(text.encode("utf-8")).hexdigest()
        for page, text in sorted(source_texts.items())
    }
    report = {
        "schema": "o015-mit-l05-validation-v2",
        "recorded_at": "2026-08-23T21:30:00Z",
        "boundary": {
            "source_pdf_pages": [16, 17, 18, 19],
            "next_source_page": 20,
            "next_heading": "LECTURE 2",
            "source_headings": [record[0] for record in SOURCE_TOPOLOGY.values()],
            "source_items": 16,
            "nested_bullets": 26,
            "source_figures": 0,
            "source_displays": 0,
            "inline_math_surfaces": 0,
            "source_uris": sorted(SOURCE_URIS),
        },
        "files": {
            "source_pdf": identity(SOURCE_PDF),
            "witness": identity(WITNESS),
            "target": identity(TARGET),
            "css": identity(CSS),
            "html": identity(HTML),
            "pdf": identity(PDF),
            "builder": identity(BUILDER),
            "browser_qa": identity(BROWSER_QA),
            "visual_qa": identity(VISUAL_QA),
            "rereview": identity(REREVIEW),
        },
        "source_page_text_sha256": page_text_hashes,
        "build": {
            "command": "python qa/build_mit_l05.py --html-output <html> --pdf-output <pdf>",
            "deterministic_rebuilds": 2,
            "toolchain": "Pandoc HTML5 and LuaLaTeX",
            "html_sha256": digest(HTML) if HTML.exists() else None,
            "pdf_sha256": digest(PDF) if PDF.exists() else None,
        },
        "html": {
            "lang": parser.lang,
            "headings": dict(sorted(parser.headings.items())),
            "source_pages": parser.source_pages,
            "source_items": parser.source_items,
            "source_figures": parser.source_figures,
            "images": parser.images,
            "math": parser.math,
            "duplicate_ids": duplicate_ids,
            "unresolved_fragments": unresolved,
        },
        "pdf": {
            "pages": len(reader.pages) if reader else None,
            "page_size": "A4",
            "searchable": True,
            "tagged": False,
            "render_sha256": EXPECTED_RENDER,
        },
        "rights": {
            "component": "MIT OCW 6.253 complete-notes",
            "license": "CC BY-NC-SA 4.0",
            "source_graphics": 0,
            "non_endorsement": True,
        },
        "model_identification": MODEL,
        "human_native_speaker_review": False,
        "browser_measurement": browser.get("result") if browser else None,
        "errors": errors,
        "result": result,
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
