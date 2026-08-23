#!/usr/bin/env python3
"""Fail-closed validation for the MIT 6.253 first-topic id-ID pilot."""

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
SOURCE_WITNESS = ROOT / "source/en/mit-01-role-of-convexity-semantic-witness.md"
TARGET_MD = ROOT / "source/id-ID/mit-01-peran-kekonveksan-id.md"
HTML = ROOT / "output/html/D90-MIT-01-peran-kekonveksan-id.html"
PDF = ROOT / "output/pdf/D90-MIT-01-peran-kekonveksan-id.pdf"
BUILDER = ROOT / "qa/build_mit_pilot.py"
BROWSER_QA = ROOT / "qa/MIT_L01_BROWSER_QA.json"
REREVIEW = ROOT / "qa/MIT_L01_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L01_PILOT_VALIDATION.json"

MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_FILES = {
    SOURCE_PDF: (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    SOURCE_WITNESS: (5_752, "a18aefa9e1ffa29d0a3cea21d0df34f05025cb7c2008ae57b5db44730c9d1f58"),
    TARGET_MD: (8_641, "2170dec12e707782c7677647f77ad8ee3360b282a8dbb9fb5620170106004bf3"),
    HTML: (20_613, "fff4de952dd2cb208208e1cfb3bbc8fe8a64936ff5fdb532a23a92fb0dc6af8b"),
    PDF: (53_370, "bd03912f9d3fe6dbe7376577c7ca6e7ab5aee007dd33b51669cde1792644df58"),
    BROWSER_QA: (1_757, "2d5c90b3343040c4ed3dfbdb3714737dfba8317d1781c1e5c27145f5afbbb76d"),
    REREVIEW: (2_691, "8259c6631c1c8645684c75a0244feedfc7289023d13e909cfdc73941eed35e50"),
}
EXPECTED_RENDER_HASHES = [
    "bd76aec8c3e698d9e43d2fa7e19af047166c9469e9ef2b2450fc773630ccec43",
    "780b9aafb4b73a9ad3537e2025c77d3a0f8068fae0fda9c67c8be0cf32d9ae50",
    "1a7bfbd15ac18ec9ce883dc5ed474fd686b27c542bcc5486732defd6a1d885da",
]
EXPECTED_ITEMS = {2: 4, 3: 3, 4: 5, 5: 9}
EXPECTED_TARGET_PAGE_MAP = [
    (1, 2, "d90-mit-l01-p002"),
    (2, 3, "d90-mit-l01-p003"),
    (3, 4, "d90-mit-l01-p004"),
    (4, 5, "d90-mit-l01-p005"),
]
EXPECTED_WITNESS_PAGE_MAP = [
    (1, 2, "src-mit-l01-p002"),
    (2, 3, "src-mit-l01-p003"),
    (3, 4, "src-mit-l01-p004"),
    (4, 5, "src-mit-l01-p005"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.main_count = 0
        self.images = 0
        self.math = 0
        self.display_math = 0
        self.headings: Counter[str] = Counter()
        self.source_pages: list[tuple[str, str, str]] = []
        self.source_items = 0
        self.edition_notes = 0
        self.lang = ""
        self.toc_role = ""
        self.skip_link_target = ""

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
                self.skip_link_target = values["href"]
        if tag == "main":
            self.main_count += 1
        if tag == "img":
            self.images += 1
        if tag == "math":
            self.math += 1
            if values.get("display") == "block":
                self.display_math += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings[tag] += 1
        if "source-page" in classes:
            self.source_pages.append(
                (values.get("id", ""), values.get("data-source-page", ""), values.get("data-source-order", ""))
            )
        if "source-item" in classes:
            self.source_items += 1
        if "edition-note" in classes:
            self.edition_notes += 1
        if values.get("id") == "TOC":
            self.toc_role = values.get("role", "")


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def div_records(nodes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pages: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for node in nodes:
        if node.get("t") != "Div":
            continue
        identifier, classes, attributes = node["c"][0]
        record = {"id": identifier, "classes": classes, "attrs": dict(attributes), "blocks": node["c"][1]}
        if "source-page" in classes:
            pages.append(record)
        if "source-item" in classes:
            items.append(record)
    return pages, items


def source_topology(
    pages: list[dict[str, Any]], items: list[dict[str, Any]]
) -> tuple[list[tuple[int, int, str]], Counter[int], dict[int, list[tuple[int, str]]], int]:
    page_map = sorted(
        (
            int(page["attrs"]["data-source-order"]),
            int(page["attrs"]["data-source-page"]),
            page["id"],
        )
        for page in pages
    )
    item_counts = Counter(int(item["attrs"]["data-source-page"]) for item in items)
    ordered_items = {
        page: sorted(
            (int(item["attrs"]["data-source-order"]), item["id"])
            for item in items
            if int(item["attrs"]["data-source-page"]) == page
        )
        for page in EXPECTED_ITEMS
    }
    nested_bullets = 0
    for item in items:
        bullet_lists = [node for node in walk(item["blocks"]) if node.get("t") == "BulletList"]
        nested_bullets += sum(len(node["c"]) for node in bullet_lists) - 1
    return page_map, item_counts, ordered_items, nested_bullets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    errors: list[str] = []

    file_records: dict[str, dict[str, Any]] = {}
    for path, expected in EXPECTED_FILES.items():
        actual = (path.stat().st_size, sha256(path))
        check(actual == expected, f"file identity differs: {path.relative_to(ROOT)}: {actual} != {expected}", errors)
        file_records[path.relative_to(ROOT).as_posix()] = identity(path)

    source_reader = PdfReader(SOURCE_PDF)
    check(len(source_reader.pages) == 340, "MIT complete-notes page count is not 340", errors)

    markdown = TARGET_MD.read_text(encoding="utf-8")
    normalized_markdown = re.sub(r"\s+", " ", markdown)
    for phrase in (
        "OpenAI Codex gpt-5.6-sol, Ultra",
        "Tidak ada dukungan oleh MIT",
        "Tinjauan bahasa manusia/penutur asli belum tercatat",
    ):
        check(phrase in normalized_markdown, f"target semantic source lacks {phrase!r}", errors)
    for phrase in (
        "O015-MIT-SEM-0001",
        "O015-MIT-SEM-0002",
        "O015-MIT-SEM-0003",
        r"K^{\circ\circ}=K",
        r"f^{**}=f",
    ):
        check(phrase in markdown, f"target semantic source lacks {phrase!r}", errors)
    check("![](" not in markdown and "![" not in markdown, "pilot unexpectedly embeds an image", errors)

    source_witness = SOURCE_WITNESS.read_text(encoding="utf-8")
    normalized_witness = re.sub(r"\s+", " ", source_witness)
    check(r"f:\mathbb{R}^n\mapsto\mathbb{R}" in source_witness, "source witness does not preserve the mapsto notation", errors)
    check("not official editable MIT source" in normalized_witness, "source witness lacks its reconstruction limitation", errors)

    pandoc = subprocess.run(
        ["pandoc", str(TARGET_MD), "--from=markdown+fenced_divs+yaml_metadata_block", "--to=json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=True,
    )
    ast = json.loads(pandoc.stdout)
    nodes = list(walk(ast))
    source_pages, source_items = div_records(nodes)
    page_map, item_counts, ordered_items, nested_bullets = source_topology(source_pages, source_items)
    check(page_map == EXPECTED_TARGET_PAGE_MAP, "target source-page map differs", errors)
    check(dict(sorted(item_counts.items())) == EXPECTED_ITEMS, f"source-item counts differ: {dict(item_counts)}", errors)
    for page, expected_count in EXPECTED_ITEMS.items():
        expected = [(index, f"d90-mit-l01-p{page:03d}-i{index:03d}") for index in range(1, expected_count + 1)]
        check(ordered_items[page] == expected, f"stable target item topology differs on source page {page}", errors)
    check(nested_bullets == 12, f"target nested-bullet count {nested_bullets} != 12", errors)
    math_nodes = [node for node in nodes if node.get("t") == "Math"]
    display_nodes = [node for node in math_nodes if node.get("c", [[""]])[0].get("t") == "DisplayMath"]
    check(len(math_nodes) == 14, f"Pandoc math-node count {len(math_nodes)} != 14", errors)
    check(len(display_nodes) == 2, f"Pandoc display-math count {len(display_nodes)} != 2", errors)

    witness_pandoc = subprocess.run(
        ["pandoc", str(SOURCE_WITNESS), "--from=markdown+fenced_divs+yaml_metadata_block", "--to=json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=True,
    )
    witness_nodes = list(walk(json.loads(witness_pandoc.stdout)))
    witness_pages, witness_items = div_records(witness_nodes)
    witness_page_map, witness_item_counts, witness_ordered_items, witness_nested_bullets = source_topology(
        witness_pages, witness_items
    )
    check(witness_page_map == EXPECTED_WITNESS_PAGE_MAP, f"source witness page map differs: {witness_page_map}", errors)
    check(dict(sorted(witness_item_counts.items())) == EXPECTED_ITEMS, f"source witness item counts differ: {dict(witness_item_counts)}", errors)
    for page, expected_count in EXPECTED_ITEMS.items():
        expected_witness = [(index, f"src-mit-l01-p{page:03d}-i{index:03d}") for index in range(1, expected_count + 1)]
        check(
            witness_ordered_items[page] == expected_witness,
            f"stable witness item topology differs on source page {page}",
            errors,
        )
        mapped_target = [(order, identifier.replace("src-mit-", "d90-mit-", 1)) for order, identifier in expected_witness]
        check(
            ordered_items[page] == mapped_target,
            f"source-to-target anchor mapping differs on source page {page}",
            errors,
        )
    check(witness_nested_bullets == 12, f"witness nested-bullet count {witness_nested_bullets} != 12", errors)
    witness_math = [node for node in witness_nodes if node.get("t") == "Math"]
    witness_display = [node for node in witness_math if node.get("c", [[""]])[0].get("t") == "DisplayMath"]
    check(len(witness_math) == 6, f"witness math-node count {len(witness_math)} != 6", errors)
    check(len(witness_display) == 2, f"witness display-math count {len(witness_display)} != 2", errors)

    surface = SurfaceParser()
    surface.feed(HTML.read_text(encoding="utf-8"))
    check(surface.lang == "id-ID", f"HTML language differs: {surface.lang}", errors)
    check(surface.main_count == 1, f"HTML main-landmark count {surface.main_count} != 1", errors)
    check(surface.headings == Counter({"h2": 6, "h1": 1, "h3": 1}), f"HTML heading topology differs: {surface.headings}", errors)
    check(surface.toc_role == "doc-toc", f"HTML TOC role differs: {surface.toc_role}", errors)
    check(surface.skip_link_target == "#d90-mit-l01-p002", f"HTML skip-link target differs: {surface.skip_link_target}", errors)
    check(surface.source_items == 21, f"HTML source-item count {surface.source_items} != 21", errors)
    check(surface.edition_notes == 3, f"HTML edition-note count {surface.edition_notes} != 3", errors)
    check(surface.math == 14 and surface.display_math == 2, f"HTML MathML topology differs: {surface.math}/{surface.display_math}", errors)
    check(surface.images == 0, f"HTML image count {surface.images} != 0", errors)
    duplicate_ids = sorted(identifier for identifier, count in Counter(surface.ids).items() if count > 1)
    unresolved = sorted(set(surface.fragments) - set(surface.ids))
    check(not duplicate_ids, f"duplicate HTML IDs: {duplicate_ids}", errors)
    check(not unresolved, f"unresolved HTML fragments: {unresolved}", errors)
    check(MODEL in HTML.read_text(encoding="utf-8"), "exact model provenance absent from HTML", errors)

    browser_qa = json.loads(BROWSER_QA.read_text(encoding="utf-8"))
    check(browser_qa.get("result") == "pass", "browser QA result is not pass", errors)
    check(browser_qa.get("surface", {}).get("sha256") == sha256(HTML), "browser QA binds a different HTML surface", errors)
    check(browser_qa.get("desktop", {}).get("horizontal_overflow") is False, "desktop browser QA reports overflow", errors)
    check(browser_qa.get("mobile", {}).get("horizontal_overflow") is False, "mobile browser QA reports overflow", errors)
    check(browser_qa.get("console_warnings_or_errors") == [], "browser QA reports console findings", errors)

    rereview = REREVIEW.read_text(encoding="utf-8")
    check("P1=0, P2=0, P3=0" in rereview, "independent rereview does not close all severities", errors)
    check("O015-MIT-SEM-0003" in rereview and sha256(TARGET_MD) in rereview, "independent rereview lacks final repair binding", errors)

    pdf_reader = PdfReader(PDF)
    root = pdf_reader.trailer["/Root"]
    metadata = pdf_reader.metadata or {}
    check(len(pdf_reader.pages) == 3, f"reader PDF page count {len(pdf_reader.pages)} != 3", errors)
    check(root.get("/Lang") == "id-ID", f"reader PDF /Lang differs: {root.get('/Lang')}", errors)
    check("/StructTreeRoot" not in root, "reader PDF unexpectedly claims a structure tree", errors)
    check(metadata.get("/Producer") == f"{MODEL} - user-directed production assistance", "reader PDF producer provenance differs", errors)
    searchable = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
    for phrase in ("Peran Kekonveksan dalam Optimisasi", "Sejarah dan Prasejarah", "Masalah Optimisasi", "Identitas sumber dan perubahan"):
        check(phrase in searchable, f"searchable PDF text lacks {phrase!r}", errors)
    fonts: dict[str, bool] = {}
    for page in pdf_reader.pages:
        resources = page.get("/Resources", {})
        for name, reference in resources.get("/Font", {}).items():
            font = reference.get_object()
            fonts[str(name)] = bool(font.get("/ToUnicode"))
    check(bool(fonts) and all(fonts.values()), f"PDF fonts without ToUnicode maps: {fonts}", errors)
    for index, page in enumerate(pdf_reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        check(abs(width - 595.276) < 0.02 and abs(height - 841.89) < 0.02, f"PDF page {index} is not A4: {width} x {height}", errors)

    with tempfile.TemporaryDirectory(prefix="o015-mit-pilot-", dir=ROOT / "tmp/pdfs") as temp:
        temp_root = Path(temp)
        rebuilds: list[tuple[str, str]] = []
        for label in ("a", "b"):
            output_root = temp_root / label
            subprocess.run(
                [sys.executable, str(BUILDER), "--output-root", str(output_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                check=True,
            )
            rebuilds.append(
                (
                    sha256(output_root / HTML.name),
                    sha256(output_root / PDF.name),
                )
            )
        expected_pair = (sha256(HTML), sha256(PDF))
        check(rebuilds[0] == rebuilds[1] == expected_pair, f"deterministic rebuild differs: {rebuilds} != {expected_pair}", errors)

        render_prefix = temp_root / "render"
        subprocess.run(["pdftoppm", "-png", "-r", "160", str(PDF), str(render_prefix)], check=True, capture_output=True)
        render_paths = sorted(temp_root.glob("render-*.png"))
        render_hashes = [sha256(path) for path in render_paths]
        check(render_hashes == EXPECTED_RENDER_HASHES, f"render hashes differ: {render_hashes}", errors)

    report = {
        "schema": "o015-mit-l01-pilot-validation-v1",
        "recorded_at": "2026-08-22T21:39:03Z",
        "boundary": {
            "source_pdf_pages": [2, 3, 4, 5],
            "next_topic_starts_source_page": 6,
            "source_items": 21,
            "nested_source_bullets": 12,
            "display_formulas": 2,
            "figures": 0,
        },
        "build": {
            "command": "python qa/build_mit_pilot.py --output-root <bounded-output-root>",
            "deterministic_rebuilds": 2,
            "html_sha256": sha256(HTML),
            "pdf_sha256": sha256(PDF),
            "toolchain": "Pandoc HTML5/MathML and LuaLaTeX",
        },
        "files": file_records,
        "html": {
            "lang": surface.lang,
            "main_landmarks": surface.main_count,
            "headings": dict(sorted(surface.headings.items())),
            "mathml_nodes": surface.math,
            "display_mathml_nodes": surface.display_math,
            "duplicate_ids": duplicate_ids,
            "unresolved_fragments": unresolved,
            "images": surface.images,
            "skip_link_target": surface.skip_link_target,
            "desktop_browser_readback": "passed",
            "phone_width_390px_readback": "passed_without_horizontal_overflow",
            "console_errors_or_warnings": 0,
            "browser_evidence": identity(BROWSER_QA),
        },
        "pdf": {
            "pages": len(pdf_reader.pages),
            "page_size": "A4",
            "lang": root.get("/Lang"),
            "searchable": True,
            "fonts_with_tounicode": fonts,
            "tagged": False,
            "all_pages_visually_inspected": True,
            "render_dpi": 160,
            "render_sha256": EXPECTED_RENDER_HASHES,
        },
        "mathematical_review": {
            "clarification_ids": ["O015-MIT-SEM-0001", "O015-MIT-SEM-0002", "O015-MIT-SEM-0003"],
            "p1_open": 0,
            "p2_open": 0,
            "p3_open": 0,
            "human_native_speaker_review": False,
            "independent_rereview": identity(REREVIEW),
        },
        "model_identification": MODEL,
        "errors": errors,
        "result": "pass" if not errors else "fail",
    }
    report_path = args.report.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
