#!/usr/bin/env python3
"""Fail-closed reader validation for MIT 6.253 Lecture 5, PDF pages 50-63."""

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
CENSUS = ROOT / "00_control/MIT_L09_LECTURE_5_BOUNDARY_CENSUS.md"
CORRECTIONS = ROOT / "00_control/MIT_L09_CORRECTION_SNAPSHOT.jsonl"
WITNESS = ROOT / "source/en/mit-09-lecture-5-recession-minima-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-09-kuliah-5-resesi-dan-minimum-id.md"
CSS = ROOT / "source/id-ID/mit-l09.css"
PREAMBLE = ROOT / "source/id-ID/mit-l09-preamble.tex"
PDF_FILTER = ROOT / "source/id-ID/mit-l09-pdf-filter.lua"
BEFORE_BODY = ROOT / "source/id-ID/mit-l09-before-body.html"
AFTER_BODY = ROOT / "source/id-ID/mit-l09-after-body.html"
HTML = ROOT / "output/html/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.html"
PDF = ROOT / "output/pdf/D90-MIT-09-kuliah-5-resesi-dan-minimum-id.pdf"
BUILDER = ROOT / "qa/build_mit_l09.py"
VISUAL_QA = ROOT / "qa/MIT_L09_VISUAL_QA.json"
BROWSER_QA = ROOT / "qa/MIT_L09_BROWSER_QA.json"
REREVIEW = ROOT / "qa/MIT_L09_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L09_VALIDATION.json"

MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
LICENSE_URI = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
FENCE = chr(96) * 3

# item, nested item, display, figure block, figure panel, example, source title
PAGE_COUNTS = {
    50: (4, 0, 0, 0, 0, 0, "LECTURE 5"),
    51: (3, 0, 1, 1, 1, 0, "RECESSION CONE OF A CONVEX SET"),
    52: (1, 5, 2, 0, 0, 0, "RECESSION CONE THEOREM"),
    53: (1, 0, 2, 1, 1, 0, "PROOF OF PART (B)"),
    54: (5, 0, 2, 1, 1, 0, "LINEALITY SPACE"),
    55: (3, 2, 0, 1, 1, 0, "DIRECTIONS OF RECESSION OF A FN"),
    56: (1, 2, 2, 0, 0, 0, "RECESSION CONE OF LEVEL SETS"),
    57: (2, 0, 0, 1, 6, 0, "DESCENT BEHAVIOR OF A CONVEX FN"),
    58: (3, 3, 2, 1, 1, 1, "RECESSION CONE OF A CONVEX FUNCTION"),
    59: (5, 0, 4, 0, 0, 0, "RECESSION FUNCTION"),
    60: (4, 2, 0, 1, 1, 0, "LOCAL AND GLOBAL MINIMA"),
    61: (3, 3, 0, 0, 0, 0, "EXISTENCE OF OPTIMAL SOLUTIONS"),
    62: (1, 0, 3, 0, 0, 0, "EXISTENCE OF SOLUTIONS - CONVEX CASE"),
    63: (5, 0, 1, 0, 0, 1, "EXISTENCE OF SOLUTION, SUM OF FNS"),
}
PAGE_TEXT_BYTES = {
    50: 289,
    51: 628,
    52: 761,
    53: 1_111,
    54: 980,
    55: 968,
    56: 665,
    57: 1_667,
    58: 902,
    59: 942,
    60: 876,
    61: 809,
    62: 1_048,
    63: 852,
    64: 305,
}
PAGE_TEXT_SHA256 = {
    50: "595b3d566a6d820573632a5dc853afb2c0cf8474fab8693a57d84ff33335ae63",
    51: "29ea48091d0c0854adeefc2cee9ff13514e0d0f8e764102e4cef02cd43346a4c",
    52: "8c6f781da342b06c073fc28c3c3e709e6806da27fc41b7af41bb1a75bdc4b00e",
    53: "d3d5afc97dd3e68df351ea9c9bf650ef22211e423973655d5e5bf7e9730c8166",
    54: "7f38485ab8f3487a4048bacc110fa6a137c39f3bfd034fcda3133c39b378594c",
    55: "b0e4296e764c3f5599b607b8a4ec4847627c349db28c45fa9ae534a3a34aa2fa",
    56: "d6a4b532b62933feb3f40d77eb4abadc212bd984a1ed0c27da756677bcc4c147",
    57: "a34def3e962e6d71573a7a45dc48ac594c792bcbc87d77d1720daaa9f1e4d6ac",
    58: "6203cc3ebafa733f38fa3c753f5c99af25620209cb4beeaa2f88ff9ed122e947",
    59: "ca166a557ed87c168774a5ecc542aef74009fa53a199b0ab700633b3c56cc363",
    60: "218eb580f08974fa64649727fd0a03e1425967c58e097ac43b2713329450c10e",
    61: "a96ceb4046bb0bc9b5aa3f3afbab02ed758a9a377afc99249f8f188ce20bce1f",
    62: "62f283dd5015d2ea7a9302a225d7813d7f0a399330d0cbf8ae3b236d4239ad91",
    63: "c404f9420102103e3ff43757dcdeecf99a9ddf4947c0d5f08c27ee17166fe314",
    64: "20de895948a7967b9f1a52b44d4a6d4fafa26b8744b23ef9bb459aa566d69766",
}
PAGE_RENDER = {
    50: (21_450, "5dceaf64ba215ff48af8175a2249d5cc11246aca4e1d3964539c323cff5f95a2"),
    51: (56_137, "b66a1dea301d7ba61d1abb544feeba31172617f6db8997f8d19258cf6dd5dedf"),
    52: (48_320, "54053898ab67c83fa74fc713a421ca1308d8e23b612bf60f9a5b23f36417674f"),
    53: (50_988, "72b29cb179a539b9d3f973efc6bdc9a22dacc68c3081e500b26f9fe57ca4c9e2"),
    54: (60_911, "2e03eb3734ffaf54a20e789d5affec335bdbd0db3486551d7907162120a9ee07"),
    55: (45_344, "6614da5d3cc2d9435f2bfa8c983340451c6a0ae736c894e26e142b91fcb37c00"),
    56: (39_493, "3ed8df60ebea27f3ef26c8c86ded32c7ffb4f73f008bcb8d8ed7151ee5d40498"),
    57: (47_145, "2dbd1d5483caabaf9865eb5924cd030cb41d286e7ed23e1ffa02f4e771911951"),
    58: (66_756, "4643b578e2f2e6d3d00b3be73413b47ddfffb7bc0d284f4970c44823b393990f"),
    59: (47_022, "fe6b81f453ac1bff8bfc6c0b338d01e29e2a9d6acb0a53e3d3c1ead70aca0adb"),
    60: (55_850, "68be066aa2204a4456402c1bb3d7d566af90cc0353ad7854222e88e5a4eda64e"),
    61: (51_495, "c4f424c4994aeceeda78449be3465641ebb169756e77fc0433a1c16505b212ff"),
    62: (58_017, "1a6e724fcd9122a3a0cb93266ecda17d23c73a3bce690ada94ad2da92bb6604e"),
    63: (52_338, "083a06d31cac9f55addfbd7b29376cdc83f10f8e355eea98e8269174b10d6acc"),
    64: (22_214, "d6b1afd9ad69d163f84bb668668f146e5706ed6ba118db5969ab4d3bbd2a3d88"),
}
COMBINED_TEXT = (12_498, "712fa8c6845fd057981d18b7f3064937e6867e5ce0d9c48612af37730ba58798")
EXPECTED = {
    SOURCE_PDF: (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    CENSUS: (19_753, "e4357023e0c2a6d4478adb904e9fec2789bc616f56bfba07d05789f74cc0cd85"),
    CORRECTIONS: (5_506, "e5ef98e4218d768cd51053e08d55c5ef44a44afa26237be652152eecd1052acc"),
    WITNESS: (25_798, "5a262868b3d9091dd62123a2d1679e876f957cb640f104ad998a519214ced8ff"),
    TARGET: (28_712, "a84e4173125a8f8606d14793bd5779efa82da1ae5a549e8a78422ac83af001d9"),
    CSS: (2_777, "4f5bb04dc8f30c5e383fc901dea1817168446ad6f6761e21a8dfdd9fb961ab1b"),
    PREAMBLE: (1_891, "bd118f2181817e73328b501db17d1e78914d334d0287633cab0ab33a092046bd"),
    PDF_FILTER: (499, "b8f11b413c30aaccaa0e014821e4e8fc32eb322a10734d092ee5ccdd46f8f9be"),
    BEFORE_BODY: (96, "b415e2359bd3bb339735144477c01321013f61972769bc4771cccc6c624e923a"),
    AFTER_BODY: (170, "8cf22b6016b2185e801cef6226143e6f4a184cbeb93598f4b790d8ce8e78501f"),
    BUILDER: (4_043, "f7ebf13f3e075cc5ede3cb53764e77002278a0c5e443545919955d0b4c6cf3c6"),
}
EXPECTED_BUILD = {
    "html": (118_805, "1dcbb699a620a00c05e39ca6c28d6e40c408b1b70bdc2a4678d634654ed771c9"),
    "pdf": (101_797, "34b8b184a90a5da04ac421b6b8d73840cef4b43bb43a49b01fdc65c1b1e04721"),
}
EXPECTED_RENDER = [
    {"page": 1, "bytes": 390_688, "sha256": "ad84266e87ac00fa9fb0b4fe065b356d1de842f0604c5f49e23d3ba2be370392"},
    {"page": 2, "bytes": 475_603, "sha256": "916cb6786287e71dca7baf23b718554da4d180d5d21ece954e65f166f0b89537"},
    {"page": 3, "bytes": 331_236, "sha256": "b0e234f6d900a7d21ec334f8ff527653b1a1109fc6024be7a12cf7ee1f36f07c"},
    {"page": 4, "bytes": 417_013, "sha256": "b52d9e42042439a8744f4ecb6ebd20e67334a25ba2b6ebe05a98b3c7eccc560a"},
    {"page": 5, "bytes": 355_029, "sha256": "d76d06a3b1d143cdbd6108c63ef7776911747408673fc20833acde0f7925b3df"},
    {"page": 6, "bytes": 474_325, "sha256": "54ad562b68c07cfcaf6a7f3b6cd4bf6fafc457fd8ef1ca9698816d1b1d28d8a1"},
    {"page": 7, "bytes": 135_923, "sha256": "680989bab8aa21cd182dd6acd76582ea52def5d96b24ed7e9405b4dbca571a94"},
]
EVENT_IDS = tuple(f"O015-MIT-SEM-{number:04d}" for number in range(12, 20))
EVENT_CLASSES = {
    "O015-MIT-SEM-0012": "determined_notation_correction",
    "O015-MIT-SEM-0013": "determined_monotonicity_reversal_correction",
    "O015-MIT-SEM-0014": "determined_symbol_correction",
    "O015-MIT-SEM-0015": "determined_set_builder_correction",
    "O015-MIT-SEM-0016": "determined_missing_quantifier_correction",
    "O015-MIT-SEM-0017": "determined_missing_hypothesis_correction",
    "O015-MIT-SEM-0018": "determined_notation_clarification",
    "O015-MIT-SEM-0019": "determined_semantic_terminology_correction",
}


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
        r"^\s{2,}(?:-\s+|\*{0,2}\((?:[a-z]|\d+)\)\*{0,2}\s+)",
        flags=re.MULTILINE,
    )
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        counts[int(match.group(1))] = len(marker.findall(text[match.end() : end]))
    return counts


def explicit_example_counts(path: Path) -> Counter[int]:
    text = path.read_text(encoding="utf-8")
    starts = list(
        re.finditer(
            r'^::: \{\.source-page\s+#[^\s}]+[^\n]*data-source-page="(\d+)"[^\n]*\}\s*$',
            text,
            flags=re.MULTILINE,
        )
    )
    pattern = re.compile(
        r"^\s*-\s+(?:\*\*)?(?:Example(?::| of application:)|Contoh(?::| penerapan:))",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    counts: Counter[int] = Counter()
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        counts[int(match.group(1))] = len(pattern.findall(text[match.end() : end]))
    return counts


def panel_labels(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(
        r"^\s*(?:-\s+)?\*\*Panel \(([a-f])\)(?::|\.)\*\*",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )


def source_topology(path: Path) -> dict[str, Any]:
    document = ast(path)
    examples_by_page = explicit_example_counts(path)
    return {
        "pages": div_records(document, "source-page"),
        "items": div_records(document, "source-item"),
        "displays": div_records(document, "source-display"),
        "figures": div_records(document, "source-figure"),
        "nested_by_page": nested_counts(path),
        "examples_by_page": examples_by_page,
        "examples": sum(examples_by_page.values()),
        "panel_labels": panel_labels(path),
        "display_math": [
            re.sub(r"\s+", "", node["c"][1].strip())
            for node in walk(document)
            if node.get("t") == "Math" and node["c"][0]["t"] == "DisplayMath"
        ],
        "code_blocks": sum(node.get("t") == "CodeBlock" for node in walk(document)),
        "tables": sum(node.get("t") == "Table" for node in walk(document)),
        "disallowed_divs": [
            node["c"][0][0]
            for node in walk(document)
            if node.get("t") == "Div"
            and set(node["c"][0][1])
            & {"exercise", "hint", "answer", "solution", "code", "interactive"}
        ],
    }


def expected_pages() -> list[tuple[str, str, str]]:
    return [
        (str(order), str(page), f"d90-mit-l09-p{page:03d}")
        for order, page in enumerate(PAGE_COUNTS, start=1)
    ]


def expected_items() -> list[tuple[int, int, str]]:
    return [
        (page, order, f"d90-mit-l09-p{page:03d}-i{order:03d}")
        for page, counts in PAGE_COUNTS.items()
        for order in range(1, counts[0] + 1)
    ]


def expected_displays() -> list[tuple[int, int, str]]:
    return [
        (page, order, f"d90-mit-l09-p{page:03d}-d{order:03d}")
        for page, counts in PAGE_COUNTS.items()
        for order in range(1, counts[2] + 1)
    ]


def expected_figures() -> list[tuple[int, str]]:
    return [
        (page, f"d90-mit-l09-p{page:03d}-f001")
        for page, counts in PAGE_COUNTS.items()
        if counts[3]
    ]


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.links: list[str] = []
        self.lang = ""
        self.main_ids: list[str] = []
        self.images = 0
        self.media = 0
        self.interactive = 0
        self.math = 0
        self.display_math = 0
        self.headings: Counter[str] = Counter()
        self.skip_target = ""
        self.source_pages: list[str] = []
        self.source_items: list[str] = []
        self.source_figures: list[str] = []
        self.source_displays: list[str] = []
        self.ordered_depth = 0
        self.ordered_items = 0

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
        if "source-page" in classes:
            self.source_pages.append(identifier)
        if "source-item" in classes:
            self.source_items.append(identifier)
        if "source-figure" in classes:
            self.source_figures.append(identifier)
        if "source-display" in classes:
            self.source_displays.append(identifier)

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


def numeric_suffix(path: Path) -> int:
    match = re.search(r"(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def render_output(path: Path, output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "page"
    subprocess.run(
        ["pdftoppm", "-r", "160", "-png", str(path), str(prefix)],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    records: list[dict[str, Any]] = []
    for page_number, item in enumerate(
        sorted(output_dir.glob("page-*.png"), key=numeric_suffix),
        start=1,
    ):
        records.append(
            {"page": page_number, "bytes": item.stat().st_size, "sha256": digest(item)}
        )
    return records


def render_authority(output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    template = output_dir / "authority-%d.png"
    subprocess.run(
        [
            "mutool",
            "draw",
            "-F",
            "png",
            "-c",
            "gray",
            "-r",
            "96",
            "-o",
            str(template),
            str(SOURCE_PDF),
            "50-64",
        ],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    records: list[dict[str, Any]] = []
    for item in sorted(output_dir.glob("authority-*.png"), key=numeric_suffix):
        page = numeric_suffix(item)
        records.append(
            {"page": page, "bytes": item.stat().st_size, "sha256": digest(item)}
        )
    return records


def correction_events() -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    events: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for line in CORRECTIONS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        event_id = event.get("event_id")
        counts[event_id] += 1
        events[event_id] = event
    return events, counts


def validate_topology(
    label: str,
    top: dict[str, Any],
    errors: list[str],
) -> None:
    actual_pages = [
        (record["attrs"].get("data-source-order"), record["attrs"].get("data-source-page"), record["id"])
        for record in top["pages"]
    ]
    check(actual_pages == expected_pages(), f"{label} page map differs", errors)
    actual_items = [
        (
            int(record["attrs"].get("data-source-page", -1)),
            int(record["attrs"].get("data-source-order", -1)),
            record["id"],
        )
        for record in top["items"]
    ]
    check(actual_items == expected_items(), f"{label} item map differs", errors)
    actual_displays = [
        (
            int(record["attrs"].get("data-source-page", -1)),
            int(record["attrs"].get("data-display-order", -1)),
            record["id"],
        )
        for record in top["displays"]
    ]
    check(actual_displays == expected_displays(), f"{label} display map differs", errors)
    actual_figures = [
        (int(record["attrs"].get("data-source-page", -1)), record["id"])
        for record in top["figures"]
    ]
    check(actual_figures == expected_figures(), f"{label} figure map differs", errors)
    check(
        all(
            record["attrs"].get("data-figure-disposition") == "omitted-source-graphic"
            for record in top["figures"]
        ),
        f"{label} figure disposition differs",
        errors,
    )
    panel_by_page: Counter[int] = Counter()
    for record in top["figures"]:
        page = int(record["attrs"].get("data-source-page", -1))
        panel_count = record["attrs"].get("data-panel-count")
        expected_panel_count = PAGE_COUNTS.get(page, (0, 0, 0, 0, 0))[4]
        if expected_panel_count == 6:
            check(panel_count == "6", f"{label} six-panel figure attribute differs", errors)
            panel_by_page[page] += int(panel_count or 0)
        else:
            check(panel_count in (None, "", "1"), f"{label} one-panel figure attribute differs", errors)
            panel_by_page[page] += int(panel_count or 1)
    ids = [
        record["id"]
        for key in ("pages", "items", "displays", "figures")
        for record in top[key]
    ]
    check(len(ids) == len(set(ids)), f"duplicate {label} stable IDs", errors)
    for page, counts in PAGE_COUNTS.items():
        actual = (
            sum(int(record["attrs"]["data-source-page"]) == page for record in top["items"]),
            top["nested_by_page"][page],
            sum(int(record["attrs"]["data-source-page"]) == page for record in top["displays"]),
            sum(int(record["attrs"]["data-source-page"]) == page for record in top["figures"]),
            panel_by_page[page],
            top["examples_by_page"][page],
        )
        check(actual == counts[:6], f"{label} topology differs on source page {page}: {actual}", errors)
    check(
        (
            len(top["items"]),
            sum(top["nested_by_page"].values()),
            len(top["displays"]),
            len(top["figures"]),
            sum(counts[4] for counts in PAGE_COUNTS.values()),
            top["examples"],
        )
        == (41, 17, 19, 7, 12, 2),
        f"{label} total topology differs",
        errors,
    )
    check(top["panel_labels"] == list("abcdef"), f"{label} six-panel description differs", errors)
    check(len(top["display_math"]) == 19, f"{label} display-math count differs", errors)
    check(top["code_blocks"] == 0, f"{label} contains a code block", errors)
    check(top["tables"] == 0, f"{label} contains a table", errors)
    check(not top["disallowed_divs"], f"{label} contains disallowed learning surfaces", errors)


def validate_html(path: Path, errors: list[str]) -> tuple[SurfaceParser, list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    parser = SurfaceParser()
    parser.feed(text)
    duplicate_ids = sorted(identifier for identifier, count in Counter(parser.ids).items() if count > 1)
    unresolved = sorted(set(parser.fragments) - set(parser.ids))
    check(parser.lang == "id-ID" and parser.main_ids == ["main-content"], "HTML language or main landmark differs", errors)
    check(parser.headings == Counter({"h2": 15, "h1": 1}), f"HTML heading topology differs: {parser.headings}", errors)
    check(
        parser.source_pages == [record[2] for record in expected_pages()],
        "HTML source-page ID order differs",
        errors,
    )
    check(
        parser.source_items == [record[2] for record in expected_items()],
        "HTML source-item ID order differs",
        errors,
    )
    check(
        parser.source_displays == [record[2] for record in expected_displays()],
        "HTML source-display ID order differs",
        errors,
    )
    check(
        parser.source_figures == [record[1] for record in expected_figures()],
        "HTML source-figure ID order differs",
        errors,
    )
    check(parser.math == 294 and parser.display_math == 19, "HTML MathML topology differs", errors)
    check(parser.ordered_items == 12, f"HTML ordered-list item count differs: {parser.ordered_items}", errors)
    check(parser.images == 0 and parser.media == 0 and parser.interactive == 0, "HTML contains image, media, or form controls", errors)
    lowered = text.lower()
    check("data:image" not in lowered and "<svg" not in lowered and "<picture" not in lowered, "HTML contains copied or embedded image content", errors)
    check(parser.skip_target == "#d90-mit-l09-p050", f"skip-link target differs: {parser.skip_target}", errors)
    check(not duplicate_ids and not unresolved, f"HTML ID closure differs: duplicate={duplicate_ids}, unresolved={unresolved}", errors)
    check(LICENSE_URI in parser.links, "HTML lacks the exact component license URI", errors)
    return parser, duplicate_ids, unresolved


def validate_pdf(
    path: Path,
    errors: list[str],
) -> tuple[PdfReader, int, dict[str, Any]]:
    reader = PdfReader(path)
    root = reader.trailer["/Root"]
    check(len(reader.pages) == 7, f"PDF page count {len(reader.pages)} != 7", errors)
    check(root.get("/Lang") == "id-ID", f"PDF /Lang differs: {root.get('/Lang')}", errors)
    check("/StructTreeRoot" not in root, "PDF unexpectedly claims tagged structure", errors)
    check(not reader.is_encrypted, "PDF is encrypted", errors)
    check(
        (reader.metadata or {}).get("/Producer") == f"{MODEL} - user-directed production assistance",
        "PDF producer provenance differs",
        errors,
    )
    check(LICENSE_URI in pdf_uris(reader), "PDF lacks the exact component license URI", errors)
    names = root.get("/Names") or {}
    check("/EmbeddedFiles" not in names, "PDF contains an embedded file", errors)
    fonts: dict[str, bool] = {}
    page_sizes: list[list[float]] = []
    for page in reader.pages:
        page_size = [
            round(float(page.mediabox.width), 3),
            round(float(page.mediabox.height), 3),
        ]
        page_sizes.append(page_size)
        check(
            abs(float(page.mediabox.width) - 595.276) < 0.02
            and abs(float(page.mediabox.height) - 841.89) < 0.02,
            "PDF page is not A4",
            errors,
        )
        for name, ref in page.get("/Resources", {}).get("/Font", {}).items():
            fonts[str(name)] = bool(ref.get_object().get("/ToUnicode"))
    check(bool(fonts) and all(fonts.values()), f"PDF ToUnicode coverage differs: {fonts}", errors)
    output_image_rows = image_rows(path)
    check(not output_image_rows, "output PDF contains a raster image XObject", errors)
    searchable = subprocess.run(
        ["pdftotext", str(path), "-"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    for phrase in (
        "Kuliah 5 - Garis Besar Kuliah",
        "Kerucut Resesi Himpunan Konveks",
        "Teorema Kerucut Resesi",
        "Perilaku Penurunan Fungsi Konveks",
        "Titik Peminimum Lokal dan Global",
        "Keberadaan Solusi untuk Jumlah Fungsi",
        "Halaman sumber 63.",
    ):
        check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)
    searchable_chars = len(re.sub(r"\s+", "", searchable))
    check(searchable_chars >= 10_000, f"searchable PDF text is unexpectedly short: {searchable_chars}", errors)
    observed = {
        "pages": len(reader.pages),
        "page_size_points": page_sizes,
        "lang": str(root.get("/Lang") or ""),
        "searchable": searchable_chars >= 10_000,
        "searchable_text_chars": searchable_chars,
        "encrypted": reader.is_encrypted,
        "tagged": "/StructTreeRoot" in root,
        "images": len(output_image_rows),
        "to_unicode_all_fonts": bool(fonts) and all(fonts.values()),
    }
    return reader, searchable_chars, observed


def validate_visual_evidence(
    path: Path,
    build_pdf: tuple[int, str],
    render_records: list[dict[str, Any]],
    pdf_pages: int,
    errors: list[str],
) -> dict[str, Any]:
    visual = json.loads(path.read_text(encoding="utf-8"))
    inspection = visual.get("inspection")
    pdf_record = visual.get("pdf", {})
    check(
        (pdf_record.get("bytes"), pdf_record.get("sha256")) == build_pdf,
        "visual QA does not bind the deterministic PDF",
        errors,
    )
    if inspection is not None:
        check(inspection.get("result") == "pass", "visual QA is not pass", errors)
        check(
            inspection.get("pages_inspected") == list(range(1, pdf_pages + 1)),
            "visual QA page inventory differs",
            errors,
        )
        check(inspection.get("render_dpi") == 160, "visual QA render DPI differs", errors)
        for key in ("black_boxes", "clipped_content", "formula_damage", "malformed_lists", "missing_glyphs", "overlap"):
            check(inspection.get(key) == 0, f"visual QA {key} differs", errors)
        render_entries = visual.get("renders", [])
    else:
        check(visual.get("result") == "pass", "visual QA is not pass", errors)
        check(pdf_record.get("pages") == pdf_pages, "visual QA PDF page count differs", errors)
        check(
            pdf_record.get("media_box_points") == [595.276, 841.89]
            and pdf_record.get("language") == "id-ID"
            and pdf_record.get("encrypted") is False
            and pdf_record.get("tagged") is False
            and pdf_record.get("raster_images") == 0,
            "visual QA PDF conformance fields differ",
            errors,
        )
        render_section = visual.get("render", {})
        check(
            render_section.get("engine") == "Poppler pdftoppm"
            and render_section.get("dpi") == 160
            and render_section.get("all_pages_inspected") is True,
            "visual QA render declaration differs",
            errors,
        )
        expected_defects = {
            "clipped_text",
            "overlap",
            "broken_glyphs",
            "unreadable_formulas",
            "margin_violations",
            "orphaned_headings",
            "inconsistent_running_headers",
            "incorrect_page_numbers",
            "copied_source_images",
        }
        defects = visual.get("defects", {})
        check(
            set(defects) == expected_defects
            and all(defects.get(key) == 0 for key in expected_defects),
            "visual QA defect inventory differs",
            errors,
        )
        render_entries = render_section.get("pages", [])
    observed_renders = [
        {"page": entry.get("page"), "bytes": entry.get("bytes"), "sha256": entry.get("sha256")}
        for entry in render_entries
    ]
    check(observed_renders == render_records, "visual QA render identities differ", errors)
    return visual


def validate_browser_evidence(
    path: Path,
    build_html: tuple[int, str],
    errors: list[str],
) -> dict[str, Any]:
    browser = json.loads(path.read_text(encoding="utf-8"))
    check(browser.get("result") == "pass", "browser QA is not pass", errors)
    if "surface" in browser:
        html_record = browser.get("html", {})
        check(
            (html_record.get("bytes"), html_record.get("sha256")) == build_html
            and html_record.get("title") == "Kuliah 5: Kerucut Resesi dan Titik Peminimum"
            and html_record.get("language") == "id-ID",
            "browser QA does not bind the deterministic HTML",
            errors,
        )
        surface = browser.get("surface", {})
        check(
            (
                surface.get("main_landmarks"),
                surface.get("skip_link_href"),
                surface.get("skip_target_exists"),
                surface.get("ids"),
                surface.get("duplicate_ids"),
                surface.get("broken_internal_fragments"),
                surface.get("source_pages"),
                surface.get("source_items"),
                surface.get("source_displays"),
                surface.get("source_figures"),
                surface.get("figure_panels"),
                surface.get("mathml_nodes"),
                surface.get("images"),
                surface.get("forms"),
            )
            == (1, "#d90-mit-l09-p050", True, 116, 0, 0, 14, 41, 19, 7, 12, 294, 0, 0),
            "browser semantic surface differs",
            errors,
        )
        desktop = browser.get("desktop", {})
        check(
            desktop.get("viewport") == [1280, 720]
            and desktop.get("document_client_width") == desktop.get("document_scroll_width")
            and desktop.get("document_client_width") == desktop.get("body_scroll_width")
            and desktop.get("horizontal_overflow") == 0
            and desktop.get("uncontained_math_overflow") == 0
            and desktop.get("console_warnings_or_errors") == 0
            and desktop.get("visual_result") == "pass",
            "browser desktop reflow or closure gate differs",
            errors,
        )
        mobile = browser.get("mobile", {})
        check(
            mobile.get("viewport") == [390, 844]
            and mobile.get("document_client_width") == mobile.get("document_scroll_width")
            and mobile.get("document_client_width") == mobile.get("body_scroll_width")
            and mobile.get("horizontal_overflow") == 0
            and mobile.get("raw_math_surfaces_wider_than_their_inline_box") == 4
            and mobile.get("contained_scrollable_math_surfaces") == 4
            and mobile.get("uncontained_math_overflow") == 0
            and mobile.get("toc_columns") == 1
            and mobile.get("console_warnings_or_errors") == 0
            and mobile.get("visual_result") == "pass",
            "browser mobile reflow or containment gate differs",
            errors,
        )
    else:
        build = browser.get("build", {})
        check(
            (build.get("html_bytes"), build.get("html_sha256")) == build_html,
            "browser QA does not bind the deterministic HTML",
            errors,
        )
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
                == (14, 41, 19, 7),
                f"browser {viewport} semantic topology differs",
                errors,
            )
    return browser


def validate_rereview_evidence(path: Path, errors: list[str]) -> dict[str, Any]:
    error_count = len(errors)
    text = path.read_text(encoding="utf-8")
    check(
        bool(
            re.search(
                r"(?:Disposition|Result):\s*\*\*PASS\*\*",
                text,
                flags=re.IGNORECASE,
            )
        ),
        "independent rereview is not PASS",
        errors,
    )
    check(
        bool(re.search(r"P1\s*=\s*0.*P2\s*=\s*0.*P3\s*=\s*0", text, flags=re.IGNORECASE | re.DOTALL)),
        "independent rereview does not close severity counts",
        errors,
    )
    for bound_path in (SOURCE_PDF, CENSUS, CORRECTIONS, WITNESS, TARGET):
        check(digest(bound_path) in text, f"independent rereview lacks {bound_path.name} binding", errors)
    check(
        EVENT_IDS[0] in text and EVENT_IDS[-1] in text,
        "independent rereview lacks the correction-range binding",
        errors,
    )
    return {
        "disposition": "pass" if len(errors) == error_count else "fail",
        **identity(path),
    }


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

    source_text_hashes: dict[str, str] = {}
    source_text_bytes: dict[str, int] = {}
    combined_text_record: dict[str, Any] = {}
    source_render_records: list[dict[str, Any]] = []
    target_top: dict[str, Any] = {}
    witness_top: dict[str, Any] = {}
    events: dict[str, dict[str, Any]] = {}
    event_counts: Counter[str] = Counter()
    parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    reader: PdfReader | None = None
    searchable_chars: int | None = None
    pdf_observed: dict[str, Any] = {}
    rebuilds: list[dict[str, tuple[int, str]]] = []
    render_records: list[list[dict[str, Any]]] = []
    canonical: dict[str, Any] = {"status": "not_present_yet"}
    evidence_paths = {
        "visual": VISUAL_QA,
        "browser": BROWSER_QA,
        "rereview": REREVIEW,
    }
    present = {name: path.is_file() for name, path in evidence_paths.items()}
    if all(present.values()):
        evidence_stage = "strict-final"
    elif any(present.values()):
        evidence_stage = "partial-evidence"
    else:
        evidence_stage = "construction"
    evidence: dict[str, Any] = {
        "stage": evidence_stage,
        "strict_when_present": True,
        "required_for_strict_final": ["visual", "browser", "rereview"],
        **{
            name: (
                {"status": "present", **identity(evidence_paths[name])}
                if is_present
                else {"status": "not_present_yet"}
            )
            for name, is_present in present.items()
        },
    }
    if any(present.values()) and not all(present.values()):
        errors.append(
            "optional QA evidence bundle is incomplete; visual, browser, and rereview "
            "must all be present once final evidence staging begins"
        )

    if not errors:
        try:
            source_reader = PdfReader(SOURCE_PDF)
            metadata = source_reader.metadata or {}
            check(len(source_reader.pages) == 340, "authority PDF page count is not 340", errors)
            check(not source_reader.is_encrypted, "authority PDF is encrypted", errors)
            check(
                metadata.get("/Title") == "6.253 Convex Analysis and Optimization, Complete Lecture Notes",
                "authority PDF title differs",
                errors,
            )
            check(metadata.get("/Author") == "Bertsekas, Dimitri", "authority PDF author differs", errors)
            for page in range(50, 65):
                raw = subprocess.run(
                    [
                        "pdftotext",
                        "-layout",
                        "-enc",
                        "UTF-8",
                        "-f",
                        str(page),
                        "-l",
                        str(page),
                        str(SOURCE_PDF),
                        "-",
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    check=True,
                ).stdout
                actual_hash = hashlib.sha256(raw).hexdigest()
                source_text_hashes[str(page)] = actual_hash
                source_text_bytes[str(page)] = len(raw)
                check(
                    (len(raw), actual_hash) == (PAGE_TEXT_BYTES[page], PAGE_TEXT_SHA256[page]),
                    f"authority page {page} text fingerprint differs",
                    errors,
                )
                text = raw.decode("utf-8").replace("\u2019", "'")
                if page in PAGE_COUNTS:
                    check(PAGE_COUNTS[page][6] in text, f"authority page {page} heading differs", errors)
                else:
                    check(
                        "LECTURE 6" in text and "LECTURE OUTLINE" in text,
                        "page 64 is not the clean Lecture 6 delimiter",
                        errors,
                    )
            combined = subprocess.run(
                [
                    "pdftotext",
                    "-layout",
                    "-enc",
                    "UTF-8",
                    "-f",
                    "50",
                    "-l",
                    "63",
                    str(SOURCE_PDF),
                    "-",
                ],
                cwd=ROOT,
                capture_output=True,
                check=True,
            ).stdout
            combined_text_record = {
                "bytes": len(combined),
                "sha256": hashlib.sha256(combined).hexdigest(),
            }
            check(
                (combined_text_record["bytes"], combined_text_record["sha256"])
                == COMBINED_TEXT,
                "authority pages 50-63 combined text fingerprint differs",
                errors,
            )

            authority_rows = image_rows(SOURCE_PDF, 50, 63)
            parsed_rows = [row.split() for row in authority_rows]
            substantive = [
                (int(row[0]), int(row[3]), int(row[4]))
                for row in parsed_rows
                if len(row) >= 5 and int(row[3]) > 1 and int(row[4]) > 1
            ]
            stencils = [
                int(row[0])
                for row in parsed_rows
                if len(row) >= 5 and int(row[3]) == 1 and int(row[4]) == 1
            ]
            check(
                substantive
                == [
                    (51, 510, 453),
                    (53, 819, 702),
                    (54, 657, 519),
                    (57, 1380, 1689),
                    (58, 528, 492),
                    (60, 729, 477),
                ],
                "authority substantive image inventory differs",
                errors,
            )
            check(stencils == [53] * 5 + [60] * 3, "authority stencil inventory differs", errors)
            check(len(authority_rows) == 14, "authority image-row count differs", errors)
            for page in source_reader.pages[49:64]:
                check(not (page.get("/Annots") or []), "authority pages 50-64 contain an annotation", errors)
            check(not (source_reader.get_fields() or {}), "authority PDF exposes form fields", errors)
            source_root = source_reader.trailer["/Root"]
            check("/OpenAction" not in source_root, "authority PDF has an open action", errors)
            check("/JavaScript" not in (source_root.get("/Names") or {}), "authority PDF has a JavaScript name tree", errors)

            census_text = CENSUS.read_text(encoding="utf-8")
            for phrase in (
                "PDF pages **50-63**",
                "page 64",
                "**41**",
                "**17**",
                "**19**",
                "**7 / 12**",
                "**2**",
                "Exercises:** 0",
                "Hints, answers, or exercise solutions:** 0",
                "Interactive elements:** 0",
            ):
                check(phrase in census_text, f"boundary census lacks {phrase!r}", errors)
            for event_id in EVENT_IDS:
                check(event_id in census_text, f"boundary census lacks {event_id}", errors)

            events, event_counts = correction_events()
            check(
                set(events) == set(EVENT_IDS)
                and len(event_counts) == 8
                and all(event_counts[event_id] == 1 for event_id in EVENT_IDS),
                "correction snapshot event set is absent, duplicated, or extended",
                errors,
            )
            for event_id, expected_class in EVENT_CLASSES.items():
                event = events.get(event_id, {})
                check(event.get("authority") == "o015-mit-ocw-6.253-spring-2012", f"{event_id} authority differs", errors)
                check(event.get("class") == expected_class, f"{event_id} class differs", errors)
                check("mit-09-lecture-5" in event.get("source", ""), f"{event_id} source binding differs", errors)
                for key in ("surface", "source_issue", "target_action"):
                    check(bool(event.get(key)), f"{event_id} lacks {key}", errors)

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
                "Tinjauan bahasa manusia/penutur asli belum tercatat",
                "tak-menaik",
                r"R_f=\{d\mid(d,0)\in R_{\operatorname{epi}(f)}\}",
                r"untuk suatu $\epsilon>0$",
                r"$X\cap\operatorname{dom}(f)\neq\varnothing$",
                "himpunan sublevel terkendala",
                "titik peminimum tunggal",
            ):
                check(phrase in normalized_target, f"target lacks {phrase!r}", errors)
            for phrase in (
                MODEL,
                "CC BY-NC-SA 4.0",
                "Permission-restricted source figure pixels and layout are omitted",
                "Lecture 5 - Lecture outline",
                "Existence of solution, sum of functions",
                "monotonically nondecreasing",
                "$y$ is a direction of recession",
                r"R_f=\{(d,0)\in R_{\operatorname{epi}(f)}\}",
                r"level sets of $f\cap X$",
                "set of minima",
            ):
                check(phrase in normalized_witness, f"witness lacks {phrase!r}", errors)
            check(
                target_text.count(MODEL) == 1 and witness_text.count(MODEL) == 1,
                "model identification count differs",
                errors,
            )
            for event_id in EVENT_IDS:
                check(witness_text.count(event_id) == 1, f"witness correction binding count differs for {event_id}", errors)
                check(target_text.count(event_id) == 2, f"target correction disclosure count differs for {event_id}", errors)
            type_mapsto = re.compile(r"\\mapsto\s*\(-\\infty,\\infty\]")
            type_arrow = re.compile(r"\\to\s*\(-\\infty,\\infty\]")
            check(
                len(type_mapsto.findall(witness_text)) == 7
                and not type_arrow.findall(witness_text),
                "witness function-type arrow inventory differs",
                errors,
            )
            check(
                len(type_arrow.findall(target_text)) == 7
                and not type_mapsto.findall(target_text),
                "target function-type arrow inventory differs",
                errors,
            )
            check("![" not in target_text and "![" not in witness_text, "semantic source embeds an image", errors)
            check(FENCE not in target_text and FENCE not in witness_text, "semantic source contains a code fence", errors)

            target_top = source_topology(TARGET)
            witness_top = source_topology(WITNESS)
            validate_topology("target", target_top, errors)
            validate_topology("witness", witness_top, errors)
            for key in ("pages", "items", "displays", "figures"):
                check(
                    [record["id"] for record in target_top[key]]
                    == [record["id"] for record in witness_top[key]],
                    f"witness-target {key} stable-ID order differs",
                    errors,
                )
            check(
                target_top["nested_by_page"] == witness_top["nested_by_page"],
                "witness-target nested topology differs",
                errors,
            )

            (ROOT / "tmp/pdfs").mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="mit-l09-validation-", dir=ROOT / "tmp/pdfs") as temp:
                temp_root = Path(temp)
                source_render_records = render_authority(temp_root / "authority-render")
                expected_source_renders = [
                    {"page": page, "bytes": expected[0], "sha256": expected[1]}
                    for page, expected in PAGE_RENDER.items()
                ]
                check(
                    source_render_records == expected_source_renders,
                    "authority page render fingerprints differ",
                    errors,
                )
                for label in ("a", "b"):
                    out = temp_root / label
                    html = out / HTML.name
                    pdf = out / PDF.name
                    subprocess.run(
                        [
                            sys.executable,
                            str(BUILDER),
                            "--html-output",
                            str(html),
                            "--pdf-output",
                            str(pdf),
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        check=True,
                    )
                    build_identity = {
                        "html": (html.stat().st_size, digest(html)),
                        "pdf": (pdf.stat().st_size, digest(pdf)),
                    }
                    rebuilds.append(build_identity)
                    render_records.append(render_output(pdf, temp_root / f"render-{label}"))
                check(
                    len(rebuilds) == 2
                    and rebuilds[0] == rebuilds[1] == EXPECTED_BUILD,
                    f"deterministic rebuild identities differ: {rebuilds}",
                    errors,
                )
                check(
                    len(render_records) == 2
                    and render_records[0] == render_records[1] == EXPECTED_RENDER,
                    f"deterministic render identities differ: {render_records}",
                    errors,
                )
                parser, duplicate_ids, unresolved = validate_html(temp_root / "a" / HTML.name, errors)
                reader, searchable_chars, pdf_observed = validate_pdf(
                    temp_root / "a" / PDF.name,
                    errors,
                )

                if HTML.exists() != PDF.exists():
                    canonical = {"status": "incomplete_pair"}
                    errors.append("canonical L09 output pair is incomplete")
                elif HTML.exists() and PDF.exists():
                    canonical = {
                        "status": "bound",
                        "html": identity(HTML),
                        "pdf": identity(PDF),
                    }
                    check(
                        (HTML.stat().st_size, digest(HTML)) == rebuilds[0]["html"],
                        "canonical HTML identity differs from deterministic build",
                        errors,
                    )
                    check(
                        (PDF.stat().st_size, digest(PDF)) == rebuilds[0]["pdf"],
                        "canonical PDF identity differs from deterministic build",
                        errors,
                    )

                if present["visual"]:
                    evidence["visual"]["status"] = "invalid"
                    error_count = len(errors)
                    visual = validate_visual_evidence(
                        VISUAL_QA,
                        rebuilds[0]["pdf"],
                        render_records[0],
                        len(reader.pages),
                        errors,
                    )
                    evidence["visual"] = {
                        "status": "validated" if len(errors) == error_count else "invalid",
                        "result": visual.get("result") or visual.get("inspection", {}).get("result"),
                        **identity(VISUAL_QA),
                    }
                if present["browser"]:
                    evidence["browser"]["status"] = "invalid"
                    error_count = len(errors)
                    browser = validate_browser_evidence(BROWSER_QA, rebuilds[0]["html"], errors)
                    evidence["browser"] = {
                        "status": "validated" if len(errors) == error_count else "invalid",
                        "result": browser.get("result"),
                        **identity(BROWSER_QA),
                    }
                if present["rereview"]:
                    evidence["rereview"]["status"] = "invalid"
                    rereview = validate_rereview_evidence(REREVIEW, errors)
                    evidence["rereview"] = {
                        "status": "validated" if rereview["disposition"] == "pass" else "invalid",
                        **rereview,
                    }
        except Exception as exc:  # Fail closed while still emitting the receipt.
            errors.append(f"validation exception: {type(exc).__name__}: {exc}")

    result = "pass" if not errors else "fail"
    release_ready = (
        result == "pass"
        and canonical.get("status") == "bound"
        and evidence.get("stage") == "strict-final"
        and all(
            evidence.get(name, {}).get("status") == "validated"
            for name in ("visual", "browser", "rereview")
        )
    )
    report = {
        "schema": "o015-mit-l09-validation-v1",
        "validation_epoch": "2026-08-24",
        "result": result,
        "release_ready": release_ready,
        "boundary": {
            "source_pdf_pages": list(range(50, 64)),
            "next_source_page": 64,
            "next_heading": "LECTURE 6 - LECTURE OUTLINE",
            "source_items": 41,
            "nested_items": 17,
            "source_displays": 19,
            "source_figures": 7,
            "source_figure_panels": 12,
            "examples": 2,
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
            "source_page_text_bytes": source_text_bytes,
            "source_page_text_sha256": source_text_hashes,
            "combined_pages_50_63": combined_text_record,
            "expected_combined_pages_50_63": {
                "bytes": COMBINED_TEXT[0],
                "sha256": COMBINED_TEXT[1],
            },
            "render_fingerprints": source_render_records,
            "substantive_image_xobjects": 6,
            "ancillary_stencil_occurrences": 8,
        },
        "formula_inventory": {
            "target_display_blocks": len(target_top.get("display_math", [])),
            "witness_display_blocks": len(witness_top.get("display_math", [])),
            "target_sequence_sha256": hashlib.sha256(
                "\n".join(target_top.get("display_math", [])).encode("utf-8")
            ).hexdigest()
            if target_top
            else None,
            "witness_sequence_sha256": hashlib.sha256(
                "\n".join(witness_top.get("display_math", [])).encode("utf-8")
            ).hexdigest()
            if witness_top
            else None,
        },
        "correction_bindings": {event_id: events.get(event_id, {}) for event_id in EVENT_IDS},
        "build": {
            "command": "python qa/build_mit_l09.py --html-output <html> --pdf-output <pdf>",
            "deterministic_rebuilds": 2,
            "rebuild_identities": rebuilds,
            "render_identities": render_records,
            "expected": EXPECTED_BUILD,
            "expected_render_identities": EXPECTED_RENDER,
            "canonical": canonical,
        },
        "evidence": evidence,
        "html": {
            "lang": parser.lang,
            "main_ids": parser.main_ids,
            "headings": dict(sorted(parser.headings.items())),
            "source_pages": len(parser.source_pages),
            "source_items": len(parser.source_items),
            "source_displays": len(parser.source_displays),
            "source_figures": len(parser.source_figures),
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
            **pdf_observed,
            "render_identities": render_records[0] if render_records else [],
        },
        "rights": {
            "component": "MIT OCW 6.253 complete-notes",
            "license": "CC BY-NC-SA 4.0",
            "license_uri": LICENSE_URI,
            "athena_source_figure_blocks_omitted": 7,
            "athena_source_figure_panels_omitted": 12,
            "non_endorsement": True,
        },
        "model_identification": MODEL,
        "human_native_speaker_review": False,
        "errors": errors,
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
