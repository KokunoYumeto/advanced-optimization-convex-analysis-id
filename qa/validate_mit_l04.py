#!/usr/bin/env python3
"""Fail-closed validation for the MIT 6.253 page-15 id-ID boundary."""

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
WITNESS = ROOT / "source/en/mit-04-rise-algorithmic-era-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-04-kebangkitan-era-algoritmik-id.md"
HTML = ROOT / "output/html/D90-MIT-04-kebangkitan-era-algoritmik-id.html"
PDF = ROOT / "output/pdf/D90-MIT-04-kebangkitan-era-algoritmik-id.pdf"
BUILDER = ROOT / "qa/build_mit_l04.py"
BROWSER_QA = ROOT / "qa/MIT_L04_BROWSER_QA.json"
VISUAL_QA = ROOT / "qa/MIT_L04_VISUAL_QA.json"
REREVIEW = ROOT / "qa/MIT_L04_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L04_VALIDATION.json"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"

EXPECTED_SOURCE = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
EXPECTED_WITNESS = (3_225, "1c6afe0318471c2680291c2968a348ff84ad3dbeb702218d1496412b3871c5f8")
EXPECTED_TARGET = (4_081, "98d4a0d31241e626e96b7929cb2cda135c8559d829326711f7dff436b8cdab0d")
EXPECTED_HTML = (9_975, "c7ee3ace683dd854ce99259536b58bc802cb17fdd189a32b403f9e87521ea81e")
EXPECTED_PDF = (36_971, "9056c6ba9fa3996f907d1dfd6147ef219aa7c88941582c78d01977e60ce8ef5f")
EXPECTED_RENDER = [
    "f5b6b4f40f499be3ffd87642422e3cdd126e1ba7839028066dee99ece81023bb",
    "161ac7c3fda20bda210e64153df5df76044e6052c6da14a7abaff76d3de42533",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


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
            records.append({"id": identifier, "classes": classes, "attrs": dict(attrs), "blocks": node["c"][1]})
    return records


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.main = 0
        self.images = 0
        self.mathml = 0
        self.display_math = 0
        self.headings: Counter[str] = Counter()
        self.lang = ""
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
        if tag == "a" and values.get("href", "").startswith("#"):
            self.fragments.append(values["href"][1:])
            if "skip-link" in classes:
                self.skip_target = values["href"]
        if tag == "main":
            self.main += 1
        if tag == "img":
            self.images += 1
        if tag == "math":
            self.mathml += 1
            if values.get("display") == "block":
                self.display_math += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings[tag] += 1
        self.source_pages += "source-page" in classes
        self.source_items += "source-item" in classes
        self.source_figures += "source-figure" in classes


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def topology(path: Path) -> dict[str, Any]:
    nodes = ast_nodes(path)
    pages = div_records(nodes, "source-page")
    items = div_records(nodes, "source-item")
    figures = div_records(nodes, "source-figure")
    nested_lists = 0
    item_math = 0
    for item in items:
        lists = [node for node in walk(item["blocks"]) if node.get("t") == "BulletList"]
        nested_lists += max(0, sum(len(node["c"]) for node in lists) - 1)
        item_math += sum(node.get("t") == "Math" for node in walk(item["blocks"]))
    return {
        "nodes": nodes,
        "pages": pages,
        "items": items,
        "figures": figures,
        "nested_lists": nested_lists,
        "item_math": item_math,
        "math": [n for n in nodes if n.get("t") == "Math"],
        "pages_order": sorted((int(x["attrs"]["data-source-order"]), int(x["attrs"]["data-source-page"]), x["id"]) for x in pages),
        "items_order": sorted((int(x["attrs"]["data-source-order"]), x["id"]) for x in items),
    }


def file_identity(path: Path, expected: tuple[int, str], errors: list[str]) -> None:
    check(path.exists(), f"missing required file: {path.relative_to(ROOT)}", errors)
    if path.exists():
        check((path.stat().st_size, digest(path)) == expected, f"identity mismatch: {path.relative_to(ROOT)}", errors)


def main() -> int:
    errors: list[str] = []
    for path, expected in (
        (SOURCE_PDF, EXPECTED_SOURCE),
        (WITNESS, EXPECTED_WITNESS),
        (TARGET, EXPECTED_TARGET),
        (HTML, EXPECTED_HTML),
        (PDF, EXPECTED_PDF),
        (BUILDER, (3_614, "733a186a8eb98bc418926ac2642b4e2b6093ef6432ba3471f4df9b9ffe00f9e7")),
        (BROWSER_QA, (1_125, "87a619e7df2a4226fe6f27307659b049e2176795b11488401dc05a6a34c86e56")),
        (VISUAL_QA, (1_275, "6da40ec0179d47143a4f99bea9a8e3e899d776773de6580afb1417085e8ff1bf")),
        (REREVIEW, (1_906, "39dc3005a3f16445eccdb73363719b3b03224efc573f7c8a45f9c73bc8a3b7d4")),
    ):
        file_identity(path, expected, errors)

    source_text = ""
    target_top: dict[str, Any] = {}
    witness_top: dict[str, Any] = {}
    parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    reader: PdfReader | None = None
    browser: dict[str, Any] = {}
    visual: dict[str, Any] = {}
    if not errors:
        source_text = subprocess.run(
            ["pdftotext", "-layout", "-f", "15", "-l", "15", str(SOURCE_PDF), "-"],
            capture_output=True,
            check=True,
        ).stdout.decode("utf-8")
        check(len(PdfReader(SOURCE_PDF).pages) == 340, "authority PDF page count is not 340", errors)
        for phrase in (
            "THE RISE OF THE ALGORITHMIC ERA",
            "Convex programs and LPs connect around",
            "Synergy of:",
            "New problem paradigms with rich applications",
            "Duality-based decomposition",
            "Conic programming",
            "Machine learning",
            "l1 regularization/Robust regression/Compressed",
        ):
            check(phrase in source_text, f"authority page 15 lacks {phrase!r}", errors)
        check(source_text.count("•") == 6, "authority top-level bullet count differs", errors)
        check(source_text.count("−") == 12, "authority nested bullet count differs", errors)
        image_listing = subprocess.run(["pdfimages", "-list", "-f", "15", "-l", "15", str(SOURCE_PDF)], capture_output=True, text=True, check=True).stdout
        image_rows = [line for line in image_listing.splitlines() if re.match(r"^\s*\d+\s+\d+\s+", line)]
        check(not image_rows, f"authority page 15 unexpectedly has image rows: {image_rows}", errors)
        xml = subprocess.run(["pdftohtml", "-f", "15", "-l", "15", "-xml", "-stdout", str(SOURCE_PDF), "-"], capture_output=True, text=True, check=True).stdout
        check("<image" not in xml and "<a href" not in xml, "authority page 15 has image/link surface", errors)

        target_text = TARGET.read_text(encoding="utf-8")
        witness_text = WITNESS.read_text(encoding="utf-8")
        normalized_target = re.sub(r"\s+", " ", target_text)
        normalized_witness = re.sub(r"\s+", " ", witness_text)
        for phrase in (MODEL, "CC BY-NC-SA 4.0", "Kebangkitan Era Algoritmik", "Algoritme", "Pemrograman konik", "Pemrograman semidefinit", "Mesin vektor pendukung", "penginderaan terkompresi"):
            check(phrase in normalized_target, f"target lacks {phrase!r}", errors)
        for phrase in (MODEL, "CC BY-NC-SA 4.0", "THE RISE OF THE ALGORITHMIC ERA", "Algorithms", "Semidefinite programming", "\\ell_1"):
            check(phrase in normalized_witness, f"witness lacks {phrase!r}", errors)
        check("![" not in target_text and "![" not in witness_text, "semantic source embeds an image", errors)
        check("not official editable MIT source" in normalized_witness, "witness lacks reconstruction limitation", errors)
        check("TTP" not in normalized_target and "TTP" not in normalized_witness, "forbidden TTP mention in page-15 source", errors)

        target_top = topology(TARGET)
        witness_top = topology(WITNESS)
        expected_target_pages = [(1, 15, "d90-mit-l04-p015")]
        expected_witness_pages = [(1, 15, "src-mit-l04-p015")]
        expected_target_items = [(i, f"d90-mit-l04-p015-i{i:03d}") for i in range(1, 7)]
        expected_witness_items = [(i, f"src-mit-l04-p015-i{i:03d}") for i in range(1, 7)]
        check(target_top["pages_order"] == expected_target_pages, f"target page map differs: {target_top['pages_order']}", errors)
        check(witness_top["pages_order"] == expected_witness_pages, f"witness page map differs: {witness_top['pages_order']}", errors)
        check(target_top["items_order"] == expected_target_items, f"target item map differs: {target_top['items_order']}", errors)
        check(witness_top["items_order"] == expected_witness_items, f"witness item map differs: {witness_top['items_order']}", errors)
        for label, top in (("target", target_top), ("witness", witness_top)):
            check(len(top["items"]) == 6 and len(top["figures"]) == 0, f"{label} div closure differs", errors)
            check(top["nested_lists"] == 12, f"{label} nested-list topology differs: {top['nested_lists']}", errors)
            check(top["item_math"] == 1, f"{label} source-item math count differs: {top['item_math']}", errors)
        target_ids = [x["id"] for x in target_top["pages"] + target_top["items"] + target_top["figures"]]
        witness_ids = [x["id"] for x in witness_top["pages"] + witness_top["items"] + witness_top["figures"]]
        check(len(target_ids) == len(set(target_ids)), "duplicate target stable IDs", errors)
        check(len(witness_ids) == len(set(witness_ids)), "duplicate witness stable IDs", errors)

        html_text = HTML.read_text(encoding="utf-8")
        parser.feed(html_text)
        duplicate_ids = sorted(x for x, count in Counter(parser.ids).items() if count > 1)
        unresolved = sorted(set(parser.fragments) - set(parser.ids))
        check(parser.lang == "id-ID", f"HTML lang is {parser.lang!r}", errors)
        check(parser.main == 1, f"HTML main count {parser.main} != 1", errors)
        check(parser.headings == Counter({"h1": 1, "h2": 3}), f"HTML headings differ: {parser.headings}", errors)
        check(parser.source_pages == 1 and parser.source_items == 6 and parser.source_figures == 0, "HTML semantic topology differs", errors)
        check(parser.images == 0 and parser.display_math == 0, "HTML has image/display-math surface", errors)
        check(parser.skip_target == "#d90-mit-l04-p015", f"skip link target differs: {parser.skip_target}", errors)
        check(not duplicate_ids and not unresolved, f"HTML ID closure differs: duplicate={duplicate_ids}, unresolved={unresolved}", errors)
        check(re.sub(r"\s+", " ", html_text).count(MODEL) == 1, "exact model provenance must occur once in HTML", errors)

        browser = json.loads(BROWSER_QA.read_text(encoding="utf-8"))
        check(browser.get("result") in {"pass", "pass_with_limitation"}, "browser QA is neither pass nor documented limitation", errors)
        check(browser.get("html", {}).get("sha256") == digest(HTML), "browser QA does not bind canonical HTML", errors)
        browser_topology = browser.get("static_checks", browser.get("topology", {}))
        check(browser_topology.get("source_items") == 6 and browser_topology.get("source_figures") == 0, "browser topology differs", errors)
        check(browser_topology.get("duplicate_ids") == 0 and browser_topology.get("unresolved_fragments") == 0, "browser ID closure differs", errors)
        check(browser.get("result") == "pass" or browser.get("limitation"), "browser result/limitation is not recorded", errors)

        visual = json.loads(VISUAL_QA.read_text(encoding="utf-8"))
        check(visual.get("result") == "pass", "visual QA is not pass", errors)
        check(visual.get("surface", {}).get("sha256") == digest(PDF), "visual QA does not bind canonical PDF", errors)
        check([entry.get("sha256") for entry in visual.get("render", {}).get("files", [])] == EXPECTED_RENDER, "visual render hashes differ", errors)

        rereview_text = REREVIEW.read_text(encoding="utf-8")
        check("P1=0, P2=0, P3=0" in rereview_text, "rereview does not close severity counts", errors)
        check(digest(TARGET) in rereview_text and digest(PDF) in rereview_text, "rereview lacks canonical bindings", errors)

        reader = PdfReader(PDF)
        root = reader.trailer["/Root"]
        check(len(reader.pages) == 2, f"PDF pages {len(reader.pages)} != 2", errors)
        check(root.get("/Lang") == "id-ID", f"PDF /Lang differs: {root.get('/Lang')}", errors)
        check("/StructTreeRoot" not in root, "PDF unexpectedly claims tagged structure", errors)
        check((reader.metadata or {}).get("/Producer") == f"{MODEL} - user-directed production assistance", "PDF producer provenance differs", errors)
        searchable = "\n".join(page.extract_text() or "" for page in reader.pages)
        for phrase in ("Kebangkitan Era Algoritmik", "Program konveks", "Dekomposisi berbasis dualitas", "Pemrograman konik", "Pembelajaran mesin", "ℓ", "penginderaan terkompresi"):
            check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)
        font_flags: dict[str, bool] = {}
        for page in reader.pages:
            for name, ref in page.get("/Resources", {}).get("/Font", {}).items():
                font_flags[str(name)] = bool(ref.get_object().get("/ToUnicode"))
            check(abs(float(page.mediabox.width) - 595.276) < 0.02 and abs(float(page.mediabox.height) - 841.89) < 0.02, "PDF page is not A4", errors)
        check(bool(font_flags) and all(font_flags.values()), f"PDF ToUnicode coverage differs: {font_flags}", errors)

        with tempfile.TemporaryDirectory(prefix="o015-mit-l04-", dir=ROOT / "tmp/pdfs") as temp:
            temp_root = Path(temp)
            rebuild_hashes = []
            for label in ("a", "b"):
                out = temp_root / label
                html = out / HTML.name
                pdf = out / PDF.name
                subprocess.run([sys.executable, str(BUILDER), "--html-output", str(html), "--pdf-output", str(pdf)], cwd=ROOT, check=True, capture_output=True)
                rebuild_hashes.append((digest(html), digest(pdf)))
            expected_pair = (digest(HTML), digest(PDF))
            check(rebuild_hashes[0] == rebuild_hashes[1] == expected_pair, f"deterministic rebuilds differ: {rebuild_hashes}", errors)

        render_dir = ROOT / "tmp/pdfs/mit-l04-final-visual"
        render_hashes = [digest(path) for path in sorted(render_dir.glob("page-*.png"))]
        check(render_hashes == EXPECTED_RENDER, f"render hashes differ: {render_hashes}", errors)

    overall = "pass_with_limitation" if not errors and browser.get("result") == "pass_with_limitation" else ("pass" if not errors else "fail")
    report = {
        "schema": "o015-mit-l04-validation-v1",
        "recorded_at": "2026-08-23T20:30:00Z",
        "boundary": {"source_pdf_pages": [15], "next_source_page": 16, "source_items": 6, "nested_bullets": 12, "source_figures": 0, "source_displays": 0, "inline_math_surfaces": 1},
        "files": {"source_pdf": identity(SOURCE_PDF), "witness": identity(WITNESS), "target": identity(TARGET), "html": identity(HTML), "pdf": identity(PDF), "builder": identity(BUILDER), "browser_qa": identity(BROWSER_QA), "visual_qa": identity(VISUAL_QA), "rereview": identity(REREVIEW)},
        "source_page_text_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest() if source_text else None,
        "build": {"command": "python qa/build_mit_l04.py --html-output <html> --pdf-output <pdf>", "deterministic_rebuilds": 2, "toolchain": "Pandoc HTML5/MathML and LuaLaTeX", "html_sha256": digest(HTML) if HTML.exists() else None, "pdf_sha256": digest(PDF) if PDF.exists() else None},
        "html": {"lang": parser.lang, "headings": dict(sorted(parser.headings.items())), "source_pages": parser.source_pages, "source_items": parser.source_items, "source_figures": parser.source_figures, "images": parser.images, "display_math": parser.display_math, "duplicate_ids": duplicate_ids, "unresolved_fragments": unresolved},
        "pdf": {"pages": len(reader.pages) if reader else None, "page_size": "A4", "searchable": True, "tagged": False, "render_sha256": EXPECTED_RENDER},
        "rights": {"component": "MIT OCW 6.253 complete-notes", "license": "CC BY-NC-SA 4.0", "source_graphics": 0, "non_endorsement": True},
        "model_identification": MODEL,
        "human_native_speaker_review": False,
        "browser_measurement": browser.get("result") if browser else None,
        "errors": errors,
        "result": overall,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
