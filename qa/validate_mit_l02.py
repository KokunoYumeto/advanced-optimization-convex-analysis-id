#!/usr/bin/env python3
"""Fail-closed validation for the MIT 6.253 pages 6-13 id-ID boundary."""

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
WITNESS = ROOT / "source/en/mit-02-duality-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-02-dualitas-dan-perilaku-pengecualian-id.md"
HTML = ROOT / "output/html/D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.html"
PDF = ROOT / "output/pdf/D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.pdf"
BUILDER = ROOT / "qa/build_mit_l02.py"
BROWSER_QA = ROOT / "qa/MIT_L02_BROWSER_QA.json"
REREVIEW = ROOT / "qa/MIT_L02_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L02_VALIDATION.json"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"

EXPECTED_SOURCE = (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181")
EXPECTED_TARGET = (12_895, "b3e26c12a934b023b7b7ad4933082e6b50d68cd09c948d079a6a01df6b478917")
EXPECTED_HTML = (38_196, "d722e7bebc5b5f1c0a9d4c1980b747564897521ea7632be0ab0e3433b26ec007")
EXPECTED_PDF = (67_749, "06b9c6ce9eaac8f78149e7a881ebdff6ef5c8692d9040c5dec8929a2e646d89b")
EXPECTED_RENDER = [
    "66dcaae358dc8da1c7b2d1d0745ddea5bda9113868d525814bf432388be835d3",
    "10984f5d9295a05833ae515a9554c9d5e34d69a3a9b9e53922ac7ece8a95565c",
    "dff5b98d050a30cb628d5a237e05b105af736b45f7b1d7e1532764ff1e9b0fc8",
    "aab9b297270c462c6a4f3c32469c4724392da9e5575b5202c74f15e71856af04",
    "97af195909cc0b500715e974a7b4ca6b0fc2067377bf004b3e2661068091a845",
]
EXPECTED_ITEMS = {6: 3, 7: 3, 8: 2, 9: 1, 10: 4, 11: 2, 12: 0, 13: 4}
EXPECTED_FIGURES = {6: 1, 7: 1, 8: 1, 9: 1, 10: 0, 11: 1, 12: 1, 13: 1}


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
    result = subprocess.run(
        ["pandoc", str(path), "--from=markdown+fenced_divs+yaml_metadata_block", "--to=json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
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
        self.math = 0
        self.display_math = 0
        self.headings: Counter[str] = Counter()
        self.lang = ""
        self.skip_target = ""
        self.source_pages = 0
        self.source_items = 0
        self.source_figures = 0
        self.source_displays = 0

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
            self.math += 1
            self.display_math += values.get("display") == "block"
        if re.fullmatch(r"h[1-6]", tag):
            self.headings[tag] += 1
        self.source_pages += "source-page" in classes
        self.source_items += "source-item" in classes
        self.source_figures += "source-figure" in classes
        self.source_displays += "source-display" in classes


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def topology(path: Path) -> dict[str, Any]:
    nodes = ast_nodes(path)
    pages = div_records(nodes, "source-page")
    items = div_records(nodes, "source-item")
    figures = div_records(nodes, "source-figure")
    displays = div_records(nodes, "source-display")
    pages_order = sorted((int(x["attrs"]["data-source-order"]), int(x["attrs"]["data-source-page"]), x["id"]) for x in pages)
    item_counts = Counter(int(x["attrs"]["data-source-page"]) for x in items)
    figure_counts = Counter(int(x["attrs"]["data-source-page"]) for x in figures)
    item_ids = sorted(x["id"] for x in items)
    figure_ids = sorted(x["id"] for x in figures)
    nested_lists = 0
    for item in items:
        lists = [node for node in walk(item["blocks"]) if node.get("t") == "BulletList"]
        nested_lists += max(0, sum(len(node["c"]) for node in lists) - 1)
    return {
        "nodes": nodes,
        "pages": pages,
        "items": items,
        "figures": figures,
        "displays": displays,
        "pages_order": pages_order,
        "item_counts": dict(sorted(item_counts.items())),
        "figure_counts": dict(sorted(figure_counts.items())),
        "item_ids": item_ids,
        "figure_ids": figure_ids,
        "nested_lists": nested_lists,
        "math": [n for n in nodes if n.get("t") == "Math"],
    }


def main() -> int:
    errors: list[str] = []
    for path, expected in ((SOURCE_PDF, EXPECTED_SOURCE), (TARGET, EXPECTED_TARGET), (HTML, EXPECTED_HTML), (PDF, EXPECTED_PDF)):
        check(path.exists(), f"missing required file: {path.relative_to(ROOT)}", errors)
        if path.exists():
            check((path.stat().st_size, digest(path)) == expected, f"identity mismatch: {path.relative_to(ROOT)}", errors)

    if not errors:
        source_reader = PdfReader(SOURCE_PDF)
        check(len(source_reader.pages) == 340, "authority PDF page count is not 340", errors)
        source_text = subprocess.run(["pdftotext", "-layout", "-f", "6", "-l", "13", str(SOURCE_PDF), "-"], capture_output=True, text=True, encoding="utf-8", check=True).stdout
        for phrase in ("DUALITY", "FENCHEL DUALITY", "EXCEPTIONAL BEHAVIOR", "C1", "C2"):
            check(phrase in source_text, f"authority pages 6-13 lack {phrase!r}", errors)

        target_text = TARGET.read_text(encoding="utf-8")
        witness_text = WITNESS.read_text(encoding="utf-8")
        normalized_target = re.sub(r"\s+", " ", target_text)
        for phrase in (MODEL, "CC BY-NC-SA 4.0", "Athena Scientific", "digunakan atas izin dihilangkan", "C_1", "C_2", r"\min_x", r"\max_y"):
            check(phrase in normalized_target, f"target lacks {phrase!r}", errors)
        check("![](" not in target_text and "![" not in target_text, "target embeds an image", errors)
        check("not official editable MIT source" in re.sub(r"\s+", " ", witness_text), "witness lacks reconstruction limitation", errors)
        check(target_text.count('data-figure-disposition="omitted-source-graphic"') == 7, "figure-rights dispositions differ", errors)

        target_top = topology(TARGET)
        witness_top = topology(WITNESS)
        expected_pages = [(i, p, f"d90-mit-l02-p{p:03d}") for i, p in enumerate(range(6, 14), 1)]
        expected_witness_pages = [(i, p, f"src-mit-l02-p{p:03d}") for i, p in enumerate(range(6, 14), 1)]
        check(target_top["pages_order"] == expected_pages, f"target page map differs: {target_top['pages_order']}", errors)
        check(witness_top["pages_order"] == expected_witness_pages, "witness page map differs", errors)
        check({page: target_top["item_counts"].get(page, 0) for page in EXPECTED_ITEMS} == EXPECTED_ITEMS, f"target item counts differ: {target_top['item_counts']}", errors)
        check({page: witness_top["item_counts"].get(page, 0) for page in EXPECTED_ITEMS} == EXPECTED_ITEMS, f"witness item counts differ: {witness_top['item_counts']}", errors)
        check({page: target_top["figure_counts"].get(page, 0) for page in EXPECTED_FIGURES} == EXPECTED_FIGURES, f"target figure counts differ: {target_top['figure_counts']}", errors)
        check({page: witness_top["figure_counts"].get(page, 0) for page in EXPECTED_FIGURES} == EXPECTED_FIGURES, "witness figure counts differ", errors)
        check(len(target_top["displays"]) == 1 and target_top["displays"][0]["id"] == "d90-mit-l02-p009-d001", "target display topology differs", errors)
        check(len(witness_top["displays"]) == 1 and witness_top["displays"][0]["id"] == "src-mit-l02-p009-d001", "witness display topology differs", errors)
        check(target_top["nested_lists"] == 7, f"target nested-list count {target_top['nested_lists']} != 7", errors)
        # The witness keeps one extra list node for the source's explanatory
        # continuation; the target's translated topology is the controlled 7.
        check(witness_top["nested_lists"] == 8, f"witness nested-list count {witness_top['nested_lists']} != 8", errors)
        check(len(target_top["math"]) == 61, f"target AST math count {len(target_top['math'])} != 61", errors)
        check(len(target_top["pages"]) == 8 and len(target_top["items"]) == 19 and len(target_top["figures"]) == 7, "target div closure differs", errors)
        all_target_ids = target_top["item_ids"] + target_top["figure_ids"] + [x["id"] for x in target_top["pages"]] + [x["id"] for x in target_top["displays"]]
        check(len(all_target_ids) == len(set(all_target_ids)), "duplicate target stable IDs", errors)

        parser = SurfaceParser()
        html_text = HTML.read_text(encoding="utf-8")
        parser.feed(html_text)
        duplicate_ids = sorted(x for x, count in Counter(parser.ids).items() if count > 1)
        unresolved = sorted(set(parser.fragments) - set(parser.ids))
        check(parser.lang == "id-ID", f"HTML lang is {parser.lang!r}", errors)
        check(parser.main == 1, f"HTML main count {parser.main} != 1", errors)
        check(parser.headings == Counter({"h1": 1, "h2": 10}), f"HTML headings differ: {parser.headings}", errors)
        check(parser.source_pages == 8 and parser.source_items == 19 and parser.source_figures == 7 and parser.source_displays == 1, "HTML semantic topology differs", errors)
        check(parser.math == 61 and parser.display_math == 6, f"HTML MathML topology differs: {parser.math}/{parser.display_math}", errors)
        check(parser.images == 0, f"HTML image count {parser.images} != 0", errors)
        check(parser.skip_target == "#d90-mit-l02-p006", f"skip link target differs: {parser.skip_target}", errors)
        check(not duplicate_ids and not unresolved, f"HTML ID closure differs: duplicate={duplicate_ids}, unresolved={unresolved}", errors)
        check(re.sub(r"\s+", " ", html_text).count(MODEL) == 1, "exact model provenance must occur once in HTML", errors)

        browser_qa = json.loads(BROWSER_QA.read_text(encoding="utf-8"))
        check(browser_qa.get("result") == "pass", "browser QA result is not pass", errors)
        check(browser_qa.get("surface", {}).get("sha256") == digest(HTML), "browser QA does not bind canonical HTML", errors)
        for mode in ("desktop", "mobile"):
            evidence = browser_qa.get(mode, {})
            check(evidence.get("horizontal_overflow") is False, f"{mode} reports horizontal overflow", errors)
            check(evidence.get("duplicate_ids") == 0 and evidence.get("bad_overflow_elements") == 0, f"{mode} structural QA differs", errors)
        check(browser_qa.get("console_warnings_or_errors") == [], "browser QA has console findings", errors)

        rereview_text = REREVIEW.read_text(encoding="utf-8")
        check("P1=0, P2=0, P3=0" in rereview_text, "rereview does not close severity counts", errors)
        check(digest(TARGET) in rereview_text and digest(PDF) in rereview_text, "rereview lacks canonical bindings", errors)

        reader = PdfReader(PDF)
        root = reader.trailer["/Root"]
        check(len(reader.pages) == 5, f"PDF pages {len(reader.pages)} != 5", errors)
        check(root.get("/Lang") == "id-ID", f"PDF /Lang differs: {root.get('/Lang')}", errors)
        check("/StructTreeRoot" not in root, "PDF unexpectedly claims tagged structure", errors)
        check((reader.metadata or {}).get("/Producer") == f"{MODEL} - user-directed production assistance", "PDF producer provenance differs", errors)
        searchable = "\n".join(page.extract_text() or "" for page in reader.pages)
        for phrase in ("Dualitas", "Dualitas Fenchel", "Perilaku Pengecualian", "Himpunan konveks"):
            check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)
        font_flags: dict[str, bool] = {}
        for page in reader.pages:
            for name, ref in page.get("/Resources", {}).get("/Font", {}).items():
                font_flags[str(name)] = bool(ref.get_object().get("/ToUnicode"))
            check(abs(float(page.mediabox.width) - 595.276) < 0.02 and abs(float(page.mediabox.height) - 841.89) < 0.02, "PDF page is not A4", errors)
        check(bool(font_flags) and all(font_flags.values()), f"PDF ToUnicode coverage differs: {font_flags}", errors)

        with tempfile.TemporaryDirectory(prefix="o015-mit-l02-", dir=ROOT / "tmp/pdfs") as temp:
            temp_root = Path(temp)
            rebuild_hashes = []
            for label in ("a", "b"):
                out = temp_root / label
                subprocess.run([sys.executable, str(BUILDER), "--output-root", str(out)], cwd=ROOT, check=True, capture_output=True, text=True)
                rebuild_hashes.append((digest(out / "D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.html"), digest(out / "D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.pdf")))
            expected_pair = (digest(HTML), digest(PDF))
            check(rebuild_hashes[0] == rebuild_hashes[1] == expected_pair, f"deterministic rebuilds differ: {rebuild_hashes}", errors)

        render_dir = ROOT / "tmp/pdfs/mit-l02-final-visual"
        render_hashes = [digest(path) for path in sorted(render_dir.glob("page-*.png"))]
        check(render_hashes == EXPECTED_RENDER, f"render hashes differ: {render_hashes}", errors)

    report = {
        "schema": "o015-mit-l02-validation-v1",
        "recorded_at": "2026-08-23T19:05:00Z",
        "boundary": {"source_pdf_pages": list(range(6, 14)), "next_topic_starts_source_page": 14, "source_items": 19, "source_figures": 7, "source_displays": 1, "nested_source_lists": 7, "target_math_nodes": 61},
        "files": {"source_pdf": identity(SOURCE_PDF), "witness": identity(WITNESS), "target": identity(TARGET), "html": identity(HTML), "pdf": identity(PDF), "browser_qa": identity(BROWSER_QA), "rereview": identity(REREVIEW)},
        "build": {"command": "python qa/build_mit_l02.py --output-root <bounded-output-root>", "deterministic_rebuilds": 2, "toolchain": "Pandoc HTML5/MathML and LuaLaTeX", "html_sha256": digest(HTML), "pdf_sha256": digest(PDF)},
        "html": {"lang": parser.lang if 'parser' in locals() else None, "headings": dict(sorted(parser.headings.items())) if 'parser' in locals() else {}, "mathml_nodes": parser.math if 'parser' in locals() else None, "source_pages": parser.source_pages if 'parser' in locals() else None, "source_items": parser.source_items if 'parser' in locals() else None, "source_figures": parser.source_figures if 'parser' in locals() else None, "duplicate_ids": duplicate_ids if 'duplicate_ids' in locals() else [], "unresolved_fragments": unresolved if 'unresolved' in locals() else []},
        "pdf": {"pages": len(reader.pages) if 'reader' in locals() else None, "page_size": "A4", "searchable": True, "tagged": False, "render_sha256": EXPECTED_RENDER},
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
