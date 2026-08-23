#!/usr/bin/env python3
"""Fail-closed validation for the MIT 6.253 page-14 id-ID boundary."""

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
WITNESS = ROOT / "source/en/mit-03-modern-view-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md"
HTML = ROOT / "output/html/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.html"
PDF = ROOT / "output/pdf/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.pdf"
BUILDER = ROOT / "qa/build_mit_l03.py"
BROWSER_QA = ROOT / "qa/MIT_L03_BROWSER_QA.json"
REREVIEW = ROOT / "qa/MIT_L03_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L03_VALIDATION.json"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_SOURCE = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
EXPECTED_WITNESS = (3_961, "ba74c799dfd1dfe87fc7be0695fd12d1780dadbff44d86f8ad6b7fc015171605")
EXPECTED_TARGET = (4_758, "24599f175ae5a40246d9677042a5c3d191802900562467d94eede8ef72837060")
EXPECTED_HTML = (9_762, "01785166246be0f1187353c64f228f341626951e7d20fef127a4b92ab7e96d90")
EXPECTED_PDF = (34_550, "3cc20409b71331564cbc5429ce72cd27ebe3cbdb072910d2483e0bdeee54a136")
EXPECTED_RENDER = [
    "1231d4a105c5f1478a257830c73aff3ab55b22e786f88d31091398ef6dfb34ba",
    "966b77bde6a9b2c172b56eba38d76e976457ccd77dabc02d77f559d0cb6254ba",
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
    result = subprocess.run(["pandoc", str(path), "--from=markdown+fenced_divs+yaml_metadata_block", "--to=json"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    return list(walk(json.loads(result.stdout)))


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
    for item in items:
        lists = [node for node in walk(item["blocks"]) if node.get("t") == "BulletList"]
        nested_lists += max(0, sum(len(node["c"]) for node in lists) - 1)
    return {
        "nodes": nodes,
        "pages": pages,
        "items": items,
        "figures": figures,
        "nested_lists": nested_lists,
        "math": [n for n in nodes if n.get("t") == "Math"],
        "pages_order": sorted((int(x["attrs"]["data-source-order"]), int(x["attrs"]["data-source-page"]), x["id"]) for x in pages),
    }


def main() -> int:
    errors: list[str] = []
    for path, expected in ((SOURCE_PDF, EXPECTED_SOURCE), (WITNESS, EXPECTED_WITNESS), (TARGET, EXPECTED_TARGET), (HTML, EXPECTED_HTML), (PDF, EXPECTED_PDF)):
        check(path.exists(), f"missing required file: {path.relative_to(ROOT)}", errors)
        if path.exists():
            check((path.stat().st_size, digest(path)) == expected, f"identity mismatch: {path.relative_to(ROOT)}", errors)

    source_text = ""
    target_top: dict[str, Any] = {}
    witness_top: dict[str, Any] = {}
    parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    reader: PdfReader | None = None
    if not errors:
        reader_source = PdfReader(SOURCE_PDF)
        check(len(reader_source.pages) == 340, "authority PDF page count is not 340", errors)
        source_text = subprocess.run(["pdftotext", "-layout", "-f", "14", "-l", "14", str(SOURCE_PDF), "-"], capture_output=True, text=True, encoding="utf-8", check=True).stdout
        for phrase in ("MODERN VIEW OF CONVEX OPTIMIZATION", "Traditional view", "Modern view", "Rockafellar", "Cutting plane", "Subgradient"):
            check(phrase in source_text, f"authority page 14 lacks {phrase!r}", errors)
        target_text = TARGET.read_text(encoding="utf-8")
        witness_text = WITNESS.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", target_text)
        for phrase in (MODEL, "CC BY-NC-SA 4.0", "Athena Scientific", "Simpleks", "Subgradien", "Bidang potong", "Titik interior", "Rockafellar"):
            check(phrase in normalized, f"target lacks {phrase!r}", errors)
        check("![" not in target_text, "target embeds an image", errors)
        check("not official editable MIT source" in re.sub(r"\s+", " ", witness_text), "witness lacks reconstruction limitation", errors)
        check(target_text.count('data-figure-disposition="omitted-source-graphic"') == 2, "figure-rights dispositions differ", errors)
        target_top = topology(TARGET)
        witness_top = topology(WITNESS)
        expected_target_pages = [(1, 14, "d90-mit-l03-p014")]
        expected_witness_pages = [(1, 14, "src-mit-l03-p014")]
        check(target_top["pages_order"] == expected_target_pages, f"target page map differs: {target_top['pages_order']}", errors)
        check(witness_top["pages_order"] == expected_witness_pages, f"witness page map differs: {witness_top['pages_order']}", errors)
        check(len(target_top["items"]) == 2 and len(target_top["figures"]) == 2, "target div closure differs", errors)
        check(len(witness_top["items"]) == 2 and len(witness_top["figures"]) == 2, "witness div closure differs", errors)
        check(target_top["nested_lists"] == 6 and witness_top["nested_lists"] == 6, f"nested-list topology differs: target={target_top['nested_lists']}, witness={witness_top['nested_lists']}", errors)
        check(len(target_top["math"]) == 0 and len(witness_top["math"]) == 0, "unexpected math nodes", errors)
        all_target_ids = [x["id"] for x in target_top["pages"] + target_top["items"] + target_top["figures"]]
        check(len(all_target_ids) == len(set(all_target_ids)), "duplicate target stable IDs", errors)

        html_text = HTML.read_text(encoding="utf-8")
        parser.feed(html_text)
        duplicate_ids = sorted(x for x, count in Counter(parser.ids).items() if count > 1)
        unresolved = sorted(set(parser.fragments) - set(parser.ids))
        check(parser.lang == "id-ID", f"HTML lang is {parser.lang!r}", errors)
        check(parser.main == 1, f"HTML main count {parser.main} != 1", errors)
        check(parser.headings == Counter({"h1": 1, "h2": 3}), f"HTML headings differ: {parser.headings}", errors)
        check(parser.source_pages == 1 and parser.source_items == 2 and parser.source_figures == 2, "HTML semantic topology differs", errors)
        check(parser.images == 0, f"HTML image count {parser.images} != 0", errors)
        check(parser.skip_target == "#d90-mit-l03-p014", f"skip link target differs: {parser.skip_target}", errors)
        check(not duplicate_ids and not unresolved, f"HTML ID closure differs: duplicate={duplicate_ids}, unresolved={unresolved}", errors)
        check(re.sub(r"\s+", " ", html_text).count(MODEL) == 1, "exact model provenance must occur once in HTML", errors)

        browser = json.loads(BROWSER_QA.read_text(encoding="utf-8"))
        check(browser.get("result") == "pass", "browser QA result is not pass", errors)
        check(browser.get("html", {}).get("sha256") == digest(HTML), "browser QA does not bind canonical HTML", errors)
        for mode in ("desktop", "mobile"):
            evidence = browser.get(mode, {})
            check(evidence.get("horizontal_overflow") is False, f"{mode} reports horizontal overflow", errors)
            check(evidence.get("duplicate_ids") == 0 and evidence.get("unresolved_fragments") == 0, f"{mode} structural QA differs", errors)
        check(browser.get("console_warnings_or_errors") == [], "browser QA has console findings", errors)

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
        for phrase in ("Pandangan Modern tentang Optimisasi Konveks", "Pandangan tradisional", "Pandangan modern", "Subgradien"):
            check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)
        font_flags: dict[str, bool] = {}
        for page in reader.pages:
            for name, ref in page.get("/Resources", {}).get("/Font", {}).items():
                font_flags[str(name)] = bool(ref.get_object().get("/ToUnicode"))
            check(abs(float(page.mediabox.width) - 595.276) < 0.02 and abs(float(page.mediabox.height) - 841.89) < 0.02, "PDF page is not A4", errors)
        check(bool(font_flags) and all(font_flags.values()), f"PDF ToUnicode coverage differs: {font_flags}", errors)

        with tempfile.TemporaryDirectory(prefix="o015-mit-l03-", dir=ROOT / "tmp/pdfs") as temp:
            temp_root = Path(temp)
            rebuild_hashes = []
            for label in ("a", "b"):
                out = temp_root / label
                html = out / HTML.name
                pdf = out / PDF.name
                subprocess.run([sys.executable, str(BUILDER), "--html-output", str(html), "--pdf-output", str(pdf)], cwd=ROOT, check=True, capture_output=True, text=True)
                rebuild_hashes.append((digest(html), digest(pdf)))
            expected_pair = (digest(HTML), digest(PDF))
            check(rebuild_hashes[0] == rebuild_hashes[1] == expected_pair, f"deterministic rebuilds differ: {rebuild_hashes}", errors)

        render_dir = ROOT / "tmp/pdfs/mit-l03-final-visual"
        render_hashes = [digest(path) for path in sorted(render_dir.glob("page-*.png"))]
        check(render_hashes == EXPECTED_RENDER, f"render hashes differ: {render_hashes}", errors)

    report = {
        "schema": "o015-mit-l03-validation-v1",
        "recorded_at": "2026-08-23T19:45:00Z",
        "boundary": {"source_pdf_pages": [14], "next_source_page": 15, "source_items": 2, "source_figures": 2, "nested_bullets": 6, "source_displays": 0},
        "files": {"source_pdf": identity(SOURCE_PDF), "witness": identity(WITNESS), "target": identity(TARGET), "html": identity(HTML), "pdf": identity(PDF), "browser_qa": identity(BROWSER_QA), "rereview": identity(REREVIEW)},
        "source_page_text_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest() if source_text else None,
        "build": {"command": "python qa/build_mit_l03.py --html-output <html> --pdf-output <pdf>", "deterministic_rebuilds": 2, "toolchain": "Pandoc HTML5/MathML and LuaLaTeX", "html_sha256": digest(HTML) if HTML.exists() else None, "pdf_sha256": digest(PDF) if PDF.exists() else None},
        "html": {"lang": parser.lang, "headings": dict(sorted(parser.headings.items())), "source_pages": parser.source_pages, "source_items": parser.source_items, "source_figures": parser.source_figures, "images": parser.images, "duplicate_ids": duplicate_ids, "unresolved_fragments": unresolved},
        "pdf": {"pages": len(reader.pages) if reader else None, "page_size": "A4", "searchable": True, "tagged": False, "render_sha256": EXPECTED_RENDER},
        "model_identification": MODEL,
        "human_native_speaker_review": False,
        "errors": errors,
        "result": "pass" if not errors else "fail",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
