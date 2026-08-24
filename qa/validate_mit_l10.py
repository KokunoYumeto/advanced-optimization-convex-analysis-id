#!/usr/bin/env python3
"""Fail-closed validation for MIT 6.253 Lecture 6, PDF pages 64-85."""

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
WITNESS = ROOT / "source/en/mit-10-lecture-6-closed-intersections-hyperplanes-semantic-witness.md"
TARGET = ROOT / "source/id-ID/mit-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.md"
CSS = ROOT / "source/id-ID/mit-l10.css"
PREAMBLE = ROOT / "source/id-ID/mit-l10-preamble.tex"
PDF_FILTER = ROOT / "source/id-ID/mit-l10-pdf-filter.lua"
BEFORE_BODY = ROOT / "source/id-ID/mit-l10-before-body.html"
AFTER_BODY = ROOT / "source/id-ID/mit-l10-after-body.html"
BUILDER = ROOT / "qa/build_mit_l10.py"
HTML = ROOT / "output/html/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.html"
PDF = ROOT / "output/pdf/D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.pdf"
VISUAL_QA = ROOT / "qa/MIT_L10_VISUAL_QA.json"
BROWSER_QA = ROOT / "qa/MIT_L10_BROWSER_QA.json"
REREVIEW = ROOT / "qa/MIT_L10_INDEPENDENT_REREVIEW.md"
REPORT = ROOT / "qa/MIT_L10_VALIDATION.json"

MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
LICENSE = "CC BY-NC-SA 4.0"
SOURCE_PAGES = tuple(range(64, 86))
DELIMITER_PAGE = 86

# items, stable display wrappers, figure blocks, semantic panels, source heading
PAGE_COUNTS = {
    64: (4, 0, 0, 0, "LECTURE 6"),
    65: (2, 2, 1, 1, "ROLE OF CLOSED SET INTERSECTIONS I"),
    66: (2, 1, 1, 1, "ROLE OF CLOSED SET INTERSECTIONS II"),
    67: (3, 1, 1, 1, "CLOSURE UNDER LINEAR TRANSFORMATION"),
    68: (6, 2, 0, 0, "ROLE OF CLOSED SET INTERSECTIONS III"),
    69: (3, 2, 1, 2, "PARTIAL MINIMIZATION: VISUALIZATION"),
    70: (3, 1, 1, 2, "PARTIAL MINIMIZATION THEOREM"),
    71: (6, 0, 0, 0, "MORE REFINED ANALYSIS - A SUMMARY"),
    72: (4, 3, 1, 1, "ASYMPTOTIC SEQUENCES"),
    73: (5, 0, 1, 2, "RETRACTIVE SEQUENCES"),
    74: (2, 0, 1, 1, "SET INTERSECTION THEOREM I"),
    75: (3, 5, 0, 0, "SET INTERSECTION THEOREM II"),
    76: (4, 2, 1, 2, "NEED TO ASSUME THAT X IS RETRACTIVE"),
    77: (2, 4, 0, 0, "LINEAR AND QUADRATIC PROGRAMMING"),
    78: (3, 2, 1, 1, "CLOSURE UNDER LINEAR TRANSFORMATION"),
    79: (3, 1, 1, 2, "NEED TO ASSUME THAT X IS RETRACTIVE"),
    80: (3, 6, 0, 0, "CLOSEDNESS OF VECTOR SUMS"),
    81: (3, 2, 1, 1, "HYPERPLANES"),
    82: (2, 1, 2, 4, "VISUALIZATION"),
    83: (2, 2, 1, 1, "SUPPORTING HYPERPLANE THEOREM"),
    84: (2, 3, 0, 0, "SEPARATING HYPERPLANE THEOREM"),
    85: (3, 1, 1, 2, "STRICT SEPARATION THEOREM"),
}

FIGURE_PANELS = {
    "d90-mit-l10-p065-f001": 1,
    "d90-mit-l10-p066-f001": 1,
    "d90-mit-l10-p067-f001": 1,
    "d90-mit-l10-p069-f001": 2,
    "d90-mit-l10-p070-f001": 2,
    "d90-mit-l10-p072-f001": 1,
    "d90-mit-l10-p073-f001": 2,
    "d90-mit-l10-p074-f001": 1,
    "d90-mit-l10-p076-f001": 2,
    "d90-mit-l10-p078-f001": 1,
    "d90-mit-l10-p079-f001": 2,
    "d90-mit-l10-p081-f001": 1,
    "d90-mit-l10-p082-f001": 2,
    "d90-mit-l10-p082-f002": 2,
    "d90-mit-l10-p083-f001": 1,
    "d90-mit-l10-p085-f001": 2,
}

PAGE_TEXT_BYTES = {
    64: 305, 65: 755, 66: 475, 67: 965, 68: 910, 69: 1_945,
    70: 1_513, 71: 1_112, 72: 1_069, 73: 2_411, 74: 835,
    75: 807, 76: 499, 77: 831, 78: 789, 79: 910, 80: 1_031,
    81: 1_022, 82: 1_039, 83: 1_060, 84: 678, 85: 1_066, 86: 258,
}
PAGE_TEXT_SHA256 = {
    64: "20de895948a7967b9f1a52b44d4a6d4fafa26b8744b23ef9bb459aa566d69766",
    65: "8f1ff52d8836347306cd5ded9b99ba4d8964841c30f828060fae1f8aa6f1cbc9",
    66: "7aec3ccd2d206e47ca17a43af4ebd5dc06167876fc09b8bee5c7b40c4fd78c72",
    67: "5fc61ff7296ddd9f6eddecf264b0638e72927a59aca18d39411575f23fdf64d7",
    68: "075bca44978a265e4a4a8042b623badbbeb33a7e76f648f7200d1de054f56f36",
    69: "ad18e9e2c5f9e7d79603ee7dabfdef10a313fc4dd5642be1ec1474f7614c91e3",
    70: "03d1c139fae4114c6da1fba6dae2727b73bbb4cdd332f455e9f394a5735a72bc",
    71: "f294a1ad7666dd7d32ab07837d09c7e2c91db1a15e47785d0d4404419da8602b",
    72: "f9145741d2ec8ba0080ea3f3b07d65fe379d1d1ec2da8fb7741f3859948c97ed",
    73: "50634a8e27552c7b979fe1d625ad88d2d3c8ce73c171aa634dda0a7e26ad2ee3",
    74: "601c73fefa720d380b1256fe9bf9048871edc7470d4d1e05b8b6b4892e0e059e",
    75: "36b06d4aac95db9909e5456d5255fe265fc87ecd217ff15f1992b4ce3c5c91a4",
    76: "006594efff92e05d584f5fdd84985666954115cb2014a22693b94fd63a605e5c",
    77: "d836071d3246d8770b4cfbcd136ac2fbc18aea6e3e9db2c364a98c77d6b74408",
    78: "1a94d1d370c339f4dd85915e59a22271ead94a99dbe4efd16aec73a67052240f",
    79: "3717eadc0f974ab696df07473de5a06093cd8732d99c2ad9c1156cf957cb3a38",
    80: "7ea1a965b93442fba7a9c38c64f1cf5f5f1443e4579c7a53c9a86a7b3753db5e",
    81: "d47ae183028625f9f4b51d7bcfdbe014b6db6dc786f7b1562aadbcfea1d94388",
    82: "21079640c14d2ccac9de7b3a9eca42946a3edd000a0a1dc22ff095fb1c3dd046",
    83: "c97129a0d2f9db7dd39406b88b5ce47d093887d07249e09d116a9e06df5e2be7",
    84: "a5b150f63b7d82d8c95bb6e4a72e30553618097af388ee71ae015ae03b9b59c7",
    85: "6845670f547011e8741dd33eb672bcf5efcd19ad692159b320dc1e1bc0152a94",
    86: "5bb20e6003c022244d8baeae9365ca1e85571b9021b7ebbca76bfb0068ac4288",
}
PAGE_RENDER = {
    64: (22_214, "d6b1afd9ad69d163f84bb668668f146e5706ed6ba118db5969ab4d3bbd2a3d88"),
    65: (72_334, "1014b04d87ee140285d5db730d6d2d18c9d67af90307a3f00e3f86e45fdcc0a4"),
    66: (40_536, "6067ec8115c7aea67aabe45125674661ca3e6dfa982d1574151714841a0318dd"),
    67: (63_190, "10315deeaf28ba84b556178ad5f015ee76064c2e13bd1ccadd40c6f5bc61ee4c"),
    68: (51_905, "f706e3cade9b6c34d9778f0364fdcde24a27001f1c0d976c07dbe9eda3eb10bf"),
    69: (77_738, "a198bdbae5940ae58221d20974723118fcafb024be040d3502b2aada3945fe02"),
    70: (84_924, "12b349bff8363d3bd70ccb14447435752022bbe3a3d2768b963345e191dc369d"),
    71: (62_373, "365f3a078471b9ac4209b4a08938e66c7ced97694369cd16e17a3603ef35ac1c"),
    72: (46_856, "c82c9a78c380c513dd7aa74c50ecd8ecdcd65ddef93ed4ed11d113ac22be3fdf"),
    73: (75_559, "fc799131084ba2c09dfca469527f2bdb7c96501bb1bdba2de57bf55e313bbe85"),
    74: (42_995, "2d423f547e06d4a4dfc5e1446b66dea22b620e59e6941e8ce22d73038f22000b"),
    75: (54_651, "1d06d4027c3fc925a9ec26529bfbd0b505909334b2089b925bb0358ae4b44ded"),
    76: (39_687, "ea0a1151e1d3beb61a15017abdabecded91ed8e615f4d7d52efbec85d630c5b3"),
    77: (41_703, "8eab1d666df2aa6e00830dfae1c296bbd3a1e829ad79c13dddc52dd7bff4591f"),
    78: (56_017, "15e982a0e49f82a08d4aaaaf736457f39d85a1075ea2e1dac8f2694a2277a1bd"),
    79: (41_363, "4cf1adafeb79bba2155be9e6188e66f852a2923aa759f2d0b78f8ab35697dbd2"),
    80: (53_320, "4a33f549d629e04371b1fabb7904e34d072e13f08e1cd00323b01b209fc133ab"),
    81: (59_503, "eb34333530e16e14261bccf2e2013e7b8e6ed8d13a13ba7c992496addd334402"),
    82: (50_966, "a9b8371ec7a165fa68a3d940e9822e6a5ab3968898daa254a4aa3e1ee46c56b5"),
    83: (73_654, "7b8962e81876001cc32f5073723e554f27d319d966bb537ea56c48c5eab894b7"),
    84: (42_339, "fa094229c5ee5eeeee84cdd806e94cd135d2e49d0f9a8042ce44d4f8a86b733f"),
    85: (65_818, "61673f835fbae6adf2894eefc10a375519a0970330cf5ea38835fb83b3ae8acc"),
    86: (21_720, "3480b3e1a2f9ea11078d7ffd2f1ccf2191bfb27d6d841a69f83b1148db65621b"),
}
COMBINED_TEXT = (22_027, "b7c9ca707a3b269340716b8d7edf60d757a0cae7d812cb307d81d5eaef71bbf6")

EXPECTED = {
    SOURCE_PDF: (8_030_116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    WITNESS: (43_575, "0dfe2c694fad607cef6c37ea7e84a0da359cedee6dc0bf023010f9c8a647c455"),
    TARGET: (45_994, "be2dd29422f5e14ce26315258e772143335475cc2ee9c0d6bfc25f2ff05c8a53"),
    CSS: (2_777, "4f5bb04dc8f30c5e383fc901dea1817168446ad6f6761e21a8dfdd9fb961ab1b"),
    PREAMBLE: (1_891, "1c5ab84e02e17f496ca92317fb4e3f41af7db68cf28a824a0d66b79dcff58da9"),
    PDF_FILTER: (499, "b8f11b413c30aaccaa0e014821e4e8fc32eb322a10734d092ee5ccdd46f8f9be"),
    BEFORE_BODY: (96, "28fd996a682c048cbab72782e3b79db0dbd9a64bbf413e5cceac7ac6f9b43959"),
    AFTER_BODY: (170, "dfee18fa0613fb71101cb324ae01297420c1f196f2e0bf5c7ae4a84d9902a9bc"),
    BUILDER: (4_082, "56cffed47a05122b9ab4936ee35c72f13582a7e7e6bf9773510a99bf02556a1b"),
}
EXPECTED_BUILD = {
    "html": (169_871, "2c3e0e72e535b181880b4e52cbc112c7d2fc393b8f5636e091ff517ed76f2038"),
    "pdf": (133_787, "3b01d57e8e8a7d7887f36cfdc205d1b68d1d007a152bd8e0cd75479628e1abc0"),
}
FORMULA_SHA256 = {
    "witness": "dffe1c5c11ae71f1a5153c80fe69a06ed1f076e1b18bb0e1e71b05cbe50a9a9d",
    "target": "c07e128c43fe5a68fbb92be88df16557a7bbff2ce8f09a02c8a82225f90b1103",
}
EVENT_IDS = tuple(f"O015-MIT-SEM-{number:04d}" for number in range(20, 31))
EXPECTED_EVENT_COUNTS = {
    "witness": Counter({event_id: (2 if event_id == "O015-MIT-SEM-0021" else 1) for event_id in EVENT_IDS}),
    "target": Counter({event_id: (2 if event_id in {"O015-MIT-SEM-0021", "O015-MIT-SEM-0022"} else 1) for event_id in EVENT_IDS}),
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


def source_topology(path: Path) -> dict[str, Any]:
    document = ast(path)
    display_math = [
        re.sub(r"\s+", "", node["c"][1].strip())
        for node in walk(document)
        if node.get("t") == "Math" and node["c"][0]["t"] == "DisplayMath"
    ]
    return {
        "pages": div_records(document, "source-page"),
        "items": div_records(document, "source-item"),
        "displays": div_records(document, "source-display"),
        "figures": div_records(document, "source-figure"),
        "display_math": display_math,
        "code_blocks": sum(node.get("t") == "CodeBlock" for node in walk(document)),
        "tables": sum(node.get("t") == "Table" for node in walk(document)),
        "disallowed_divs": [
            node["c"][0][0]
            for node in walk(document)
            if node.get("t") == "Div"
            and set(node["c"][0][1]) & {"exercise", "hint", "answer", "solution", "code", "interactive"}
        ],
        "correction_attrs": [
            dict(node["c"][0][2]).get("data-correction-event")
            for node in walk(document)
            if node.get("t") == "Div" and dict(node["c"][0][2]).get("data-correction-event")
        ],
    }


def expected_pages() -> list[tuple[str, str, str]]:
    return [(str(order), str(page), f"d90-mit-l10-p{page:03d}") for order, page in enumerate(SOURCE_PAGES, 1)]


def expected_items() -> list[tuple[int, int, str]]:
    return [
        (page, order, f"d90-mit-l10-p{page:03d}-i{order:03d}")
        for page in SOURCE_PAGES
        for order in range(1, PAGE_COUNTS[page][0] + 1)
    ]


def expected_displays() -> list[tuple[int, int, str]]:
    return [
        (page, order, f"d90-mit-l10-p{page:03d}-d{order:03d}")
        for page in SOURCE_PAGES
        for order in range(1, PAGE_COUNTS[page][1] + 1)
    ]


def expected_figures() -> list[tuple[int, str]]:
    return [(int(re.search(r"p(\d{3})", identifier).group(1)), identifier) for identifier in FIGURE_PANELS]


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
        f"{label} figure disposition differs",
        errors,
    )
    for record in top["figures"]:
        declared = record["attrs"].get("data-panel-count")
        if declared:
            check(int(declared) == FIGURE_PANELS[record["id"]], f"{label} panel attribute differs for {record['id']}", errors)
    identifiers = [record["id"] for key in ("pages", "items", "displays", "figures") for record in top[key]]
    check(len(identifiers) == len(set(identifiers)), f"duplicate {label} stable IDs", errors)
    check(
        (len(top["pages"]), len(top["items"]), len(top["displays"]), len(top["figures"]), sum(FIGURE_PANELS.values()))
        == (22, 70, 41, 16, 24),
        f"{label} total topology differs",
        errors,
    )
    check(len(top["display_math"]) == 41, f"{label} display-formula count differs", errors)
    formula_hash = hashlib.sha256("\n".join(top["display_math"]).encode("utf-8")).hexdigest()
    check(formula_hash == FORMULA_SHA256[label], f"{label} display-formula sequence differs", errors)
    check(top["code_blocks"] == 0 and top["tables"] == 0, f"{label} contains code blocks or tables", errors)
    check(not top["disallowed_divs"], f"{label} contains exercise/solution/code/interactive surfaces", errors)
    check(Counter(top["correction_attrs"]) == EXPECTED_EVENT_COUNTS[label], f"{label} correction attribute bindings differ", errors)


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
    check(parser.headings == Counter({"h2": 22, "h1": 1}), f"HTML heading topology differs: {parser.headings}", errors)
    check(parser.source_pages == [record[2] for record in expected_pages()], "HTML source-page ID order differs", errors)
    check(parser.source_items == [record[2] for record in expected_items()], "HTML source-item ID order differs", errors)
    check(parser.source_displays == [record[2] for record in expected_displays()], "HTML source-display ID order differs", errors)
    check(parser.source_figures == [record[1] for record in expected_figures()], "HTML source-figure ID order differs", errors)
    check(parser.math == 394 and parser.display_math == 41, "HTML MathML topology differs", errors)
    check(parser.images == 0 and parser.media == 0 and parser.interactive == 0, "HTML contains image, media, embed, or form surfaces", errors)
    lowered = text.lower()
    check(not any(token in lowered for token in ("data:image", "<script", "<picture", "<svg", "<iframe")), "HTML contains embedded source-image or active content", errors)
    check(parser.skip_target == "#d90-mit-l10-p064", f"HTML skip-link target differs: {parser.skip_target}", errors)
    check(not duplicates and not unresolved, f"HTML ID closure differs: duplicate={duplicates}, unresolved={unresolved}", errors)
    check("Kuliah 6: Irisan Himpunan Tertutup, Ketertutupan, dan Hiperbidang" in text, "HTML title differs", errors)
    return parser, duplicates, unresolved


def pdf_uris(reader: PdfReader) -> set[str]:
    uris: set[str] = set()
    for page in reader.pages:
        for annotation_ref in page.get("/Annots") or []:
            action = annotation_ref.get_object().get("/A") or {}
            if action.get("/URI"):
                uris.add(str(action["/URI"]))
    return uris


def image_rows(path: Path, first: int | None = None, last: int | None = None) -> list[str]:
    command = ["pdfimages", "-list"]
    if first is not None:
        command += ["-f", str(first)]
    if last is not None:
        command += ["-l", str(last)]
    command.append(str(path))
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    return [line for line in result.stdout.splitlines() if re.match(r"^\s*\d+\s+\d+\s+", line)]


def validate_pdf(path: Path, errors: list[str]) -> tuple[PdfReader, dict[str, Any]]:
    reader = PdfReader(path)
    root = reader.trailer["/Root"]
    check(len(reader.pages) == 10, f"PDF page count {len(reader.pages)} != 10", errors)
    check(root.get("/Lang") == "id-ID", f"PDF /Lang differs: {root.get('/Lang')}", errors)
    check(not reader.is_encrypted, "PDF is encrypted", errors)
    check((reader.metadata or {}).get("/Producer") == f"{MODEL} - user-directed production assistance", "PDF producer provenance differs", errors)
    names = root.get("/Names") or {}
    check("/EmbeddedFiles" not in names, "PDF contains an embedded file", errors)
    open_action = root.get("/OpenAction")
    action_kind = open_action.get("/S") if isinstance(open_action, dict) else None
    check("/JavaScript" not in names and action_kind != "/JavaScript" and "/AA" not in root, "PDF contains scripted active content", errors)
    check(not (reader.get_fields() or {}), "PDF exposes form fields", errors)
    fonts: dict[str, bool] = {}
    page_sizes: list[list[float]] = []
    extracted: list[str] = []
    for page in reader.pages:
        page_sizes.append([round(float(page.mediabox.width), 3), round(float(page.mediabox.height), 3)])
        check(abs(float(page.mediabox.width) - 595.276) < 0.02 and abs(float(page.mediabox.height) - 841.89) < 0.02, "PDF page is not A4", errors)
        for name, ref in page.get("/Resources", {}).get("/Font", {}).items():
            fonts[str(name)] = bool(ref.get_object().get("/ToUnicode"))
        extracted.append(page.extract_text() or "")
    check(bool(fonts) and all(fonts.values()), f"PDF ToUnicode coverage differs: {fonts}", errors)
    output_images = image_rows(path)
    check(not output_images, "output PDF contains a raster source-image XObject", errors)
    searchable = "\n".join(extracted)
    for phrase in (
        "Kuliah 6 - Garis Besar Kuliah",
        "Minimisasi Parsial",
        "Barisan Retraktif",
        "Pemrograman Linear dan Kuadratik",
        "Ketertutupan Jumlah Vektor",
        "Teorema Pemisahan Ketat",
        "Halaman sumber 85.",
    ):
        check(phrase in searchable, f"searchable PDF lacks {phrase!r}", errors)
    page_chars = [len(re.sub(r"\s+", "", text)) for text in extracted]
    total_chars = sum(page_chars)
    check(total_chars >= 22_000, f"searchable PDF text is unexpectedly short: {total_chars}", errors)
    check(len(page_chars) == 10 and min(page_chars, default=0) >= 1_400, f"PDF has an unfilled or text-empty page: {page_chars}", errors)
    return reader, {
        "pages": len(reader.pages),
        "page_size_points": page_sizes,
        "lang": str(root.get("/Lang") or ""),
        "searchable_text_chars": total_chars,
        "searchable_chars_per_page": page_chars,
        "page_filled": len(page_chars) == 10 and min(page_chars, default=0) >= 1_400,
        "encrypted": reader.is_encrypted,
        "tagged": "/StructTreeRoot" in root,
        "images": len(output_images),
        "to_unicode_all_fonts": bool(fonts) and all(fonts.values()),
        "uri_annotations": sorted(pdf_uris(reader)),
    }


def numeric_suffix(path: Path) -> int:
    match = re.search(r"(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def render_authority(output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["mutool", "draw", "-F", "png", "-c", "gray", "-r", "96", "-o", str(output_dir / "authority-%d.png"), str(SOURCE_PDF), "64-86"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return [
        {"page": numeric_suffix(path), "bytes": path.stat().st_size, "sha256": digest(path)}
        for path in sorted(output_dir.glob("authority-*.png"), key=numeric_suffix)
    ]


def render_output(path: Path, output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "160", "-png", str(path), str(output_dir / "page")], cwd=ROOT, capture_output=True, check=True)
    return [
        {"page": index, "bytes": item.stat().st_size, "sha256": digest(item)}
        for index, item in enumerate(sorted(output_dir.glob("page-*.png"), key=numeric_suffix), 1)
    ]


def validate_visual(path: Path, build_pdf: tuple[int, str], renders: list[dict[str, Any]], errors: list[str]) -> dict[str, Any]:
    visual = json.loads(path.read_text(encoding="utf-8"))
    check(visual.get("result") == "pass" or (visual.get("inspection") or {}).get("result") == "pass", "visual QA is not pass", errors)
    if "artifact" in visual and "pdf_structure" in visual:
        artifact = visual.get("artifact", {})
        check(
            artifact.get("path") == PDF.relative_to(ROOT).as_posix()
            and (artifact.get("bytes"), artifact.get("sha256")) == build_pdf,
            "visual QA artifact does not bind deterministic PDF",
            errors,
        )
        structure = visual.get("pdf_structure", {})
        check(
            structure.get("pages") == 10
            and structure.get("page_size") == "A4"
            and structure.get("encrypted") is False
            and structure.get("forms") is False
            and structure.get("javascript") is False
            and structure.get("tagged") is False
            and structure.get("searchable") is True
            and structure.get("embedded_unicode_fonts") is True,
            "visual QA PDF-structure declaration differs",
            errors,
        )
        extraction = visual.get("text_extraction", {})
        check(
            extraction.get("bytes", 0) >= 38_000
            and extraction.get("characters", 0) >= 35_000
            and extraction.get("replacement_characters") == 0
            and extraction.get("nul_characters") == 0
            and extraction.get("title_present") is True
            and extraction.get("final_theorem_present") is True,
            "visual QA searchable-text evidence differs",
            errors,
        )
        render = visual.get("render", {})
        check(
            render.get("dpi") == 160
            and render.get("pages_rendered") == 10
            and render.get("pages_inspected") == list(range(1, 11))
            and render.get("page_75_proof_displays_checked_on_reader_page") == 6
            and render.get("visual_result") == "pass",
            "visual QA page-inspection declaration differs",
            errors,
        )
        for key in (
            "clipped_text",
            "overlapping_elements",
            "broken_glyphs",
            "unreadable_math",
            "margin_or_header_footer_defects",
        ):
            check(render.get(key) == 0, f"visual QA {key} differs", errors)
        check(len(renders) == 10, "validator render inventory is not ten pages", errors)
        return visual
    pdf_record = visual.get("pdf", {})
    check((pdf_record.get("bytes"), pdf_record.get("sha256")) == build_pdf, "visual QA does not bind deterministic PDF", errors)
    inspection = visual.get("inspection") or {}
    if inspection:
        check(inspection.get("pages_inspected") == list(range(1, 11)), "visual QA page inventory differs", errors)
        for key in ("black_boxes", "clipped_content", "formula_damage", "malformed_lists", "missing_glyphs", "overlap"):
            check(inspection.get(key) == 0, f"visual QA {key} differs", errors)
        entries = visual.get("renders", [])
    else:
        render = visual.get("render", {})
        check(render.get("all_pages_inspected") is True and render.get("dpi") == 160, "visual QA render declaration differs", errors)
        defects = visual.get("defects", {})
        check(bool(defects) and all(value == 0 for value in defects.values()), "visual QA defect inventory differs", errors)
        entries = render.get("pages", [])
    observed = [{"page": row.get("page"), "bytes": row.get("bytes"), "sha256": row.get("sha256")} for row in entries]
    check(observed == renders, "visual QA render identities differ", errors)
    return visual


def validate_browser(path: Path, build_html: tuple[int, str], errors: list[str]) -> dict[str, Any]:
    browser = json.loads(path.read_text(encoding="utf-8"))
    check(browser.get("result") == "pass", "browser QA is not pass", errors)
    if "artifact" in browser and "structure" in browser:
        artifact = browser.get("artifact", {})
        check(
            artifact.get("path") == HTML.relative_to(ROOT).as_posix()
            and (artifact.get("bytes"), artifact.get("sha256")) == build_html,
            "browser QA artifact does not bind deterministic HTML",
            errors,
        )
        structure = browser.get("structure", {})
        check(
            structure.get("document_language") == "id-ID"
            and structure.get("main_id") == "main-content"
            and structure.get("source_pages") == 22
            and structure.get("source_items") == 70
            and structure.get("source_figures") == 16
            and structure.get("source_displays") == 41
            and structure.get("math_nodes") == 394
            and structure.get("duplicate_ids") == 0
            and structure.get("broken_fragment_targets") == 0
            and structure.get("skip_link_href") == "#d90-mit-l10-p064"
            and structure.get("skip_link_target_exists") is True
            and structure.get("unexpected_controls") == 0
            and structure.get("images") == 0
            and structure.get("audio_or_video") == 0
            and structure.get("console_entries") == 0,
            "browser semantic-structure evidence differs",
            errors,
        )
        desktop = browser.get("desktop", {})
        check(
            desktop.get("viewport_css_px") == [1280, 800]
            and desktop.get("document_scroll_width") == desktop.get("document_client_width")
            and desktop.get("viewport_overflow") is False
            and desktop.get("visual_result") == "pass",
            "browser desktop reflow evidence differs",
            errors,
        )
        mobile = browser.get("mobile", {})
        check(
            mobile.get("viewport_css_px") == [390, 844]
            and mobile.get("document_scroll_width") == mobile.get("document_client_width")
            and mobile.get("viewport_overflow") is False
            and mobile.get("wide_math_blocks") == ["d90-mit-l10-p065-d002", "d90-mit-l10-p077-d002"]
            and "overflow-x:auto" in mobile.get("wide_math_containment", "")
            and "neither widens the body or document" in mobile.get("wide_math_containment", "")
            and mobile.get("visual_result") == "pass",
            "browser mobile reflow/containment evidence differs",
            errors,
        )
    elif "surface" in browser:
        html_record = browser.get("html", {})
        check((html_record.get("bytes"), html_record.get("sha256")) == build_html, "browser QA does not bind deterministic HTML", errors)
        surface = browser.get("surface", {})
        check(
            (surface.get("source_pages"), surface.get("source_items"), surface.get("source_displays"), surface.get("source_figures"), surface.get("figure_panels"), surface.get("mathml_nodes"), surface.get("images"), surface.get("forms"))
            == (22, 70, 41, 16, 24, 394, 0, 0),
            "browser semantic surface differs",
            errors,
        )
        for viewport in ("desktop", "mobile"):
            metrics = browser.get(viewport, {})
            check(metrics.get("horizontal_overflow") in (0, False) and metrics.get("uncontained_math_overflow") in (0, False) and metrics.get("console_warnings_or_errors") in (0, []), f"browser {viewport} reflow differs", errors)
    else:
        build = browser.get("build", {})
        check((build.get("html_bytes"), build.get("html_sha256")) == build_html, "browser QA does not bind deterministic HTML", errors)
        for viewport in ("desktop", "mobile"):
            metrics = browser.get(viewport, {})
            check(
                metrics.get("horizontal_overflow") is False
                and metrics.get("broken_fragments") == []
                and metrics.get("duplicate_ids") == []
                and metrics.get("console_warnings_or_errors") == []
                and (metrics.get("source_pages"), metrics.get("source_items"), metrics.get("source_displays"), metrics.get("source_figures")) == (22, 70, 41, 16),
                f"browser {viewport} closure differs",
                errors,
            )
    return browser


def validate_rereview(path: Path, errors: list[str]) -> dict[str, Any]:
    before = len(errors)
    text = path.read_text(encoding="utf-8")
    check(
        bool(re.search(r"(?:Disposition|Result):\s*\*\*PASS\b[^*\r\n]*\*\*", text, flags=re.IGNORECASE)),
        "independent rereview is not PASS",
        errors,
    )
    check(
        bool(re.search(r"P1\s*=\s*0.*P2\s*=\s*0.*P3\s*=\s*0", text, flags=re.IGNORECASE | re.DOTALL))
        or "no open P1, P2, or P3 findings" in text,
        "independent rereview does not close severity counts",
        errors,
    )
    for bound in (SOURCE_PDF, WITNESS, TARGET):
        check(digest(bound) in text, f"independent rereview lacks {bound.name} binding", errors)
    check(EVENT_IDS[0] in text and EVENT_IDS[-1] in text, "independent rereview lacks correction-range binding", errors)
    return {"disposition": "pass" if len(errors) == before else "fail", **identity(path)}


def main() -> int:
    errors: list[str] = []
    for path, expected in EXPECTED.items():
        check(path.is_file(), f"missing required file: {path.relative_to(ROOT)}", errors)
        if path.is_file():
            check((path.stat().st_size, digest(path)) == expected, f"identity mismatch: {path.relative_to(ROOT)}", errors)

    evidence_paths = {"visual": VISUAL_QA, "browser": BROWSER_QA, "rereview": REREVIEW}
    present = {name: path.is_file() for name, path in evidence_paths.items()}
    if all(present.values()):
        stage = "strict-final"
    elif any(present.values()):
        stage = "partial-evidence"
    else:
        stage = "construction"
    evidence: dict[str, Any] = {
        "stage": stage,
        "strict_when_present": True,
        "required_for_strict_final": ["visual", "browser", "rereview"],
        **{name: ({"status": "present", **identity(path)} if present[name] else {"status": "not_present_yet"}) for name, path in evidence_paths.items()},
    }

    source_text_bytes: dict[str, int] = {}
    source_text_hashes: dict[str, str] = {}
    combined_record: dict[str, Any] = {}
    authority_renders: list[dict[str, Any]] = []
    topologies: dict[str, dict[str, Any]] = {}
    parser = SurfaceParser()
    duplicate_ids: list[str] = []
    unresolved: list[str] = []
    pdf_observed: dict[str, Any] = {}
    rebuilds: list[dict[str, tuple[int, str]]] = []
    output_renders: list[list[dict[str, Any]]] = []
    canonical: dict[str, Any] = {"status": "not_present_yet"}

    if not errors:
        try:
            source_reader = PdfReader(SOURCE_PDF)
            metadata = source_reader.metadata or {}
            check(len(source_reader.pages) == 340, "authority PDF page count is not 340", errors)
            check(not source_reader.is_encrypted, "authority PDF is encrypted", errors)
            check(metadata.get("/Title") == "6.253 Convex Analysis and Optimization, Complete Lecture Notes", "authority PDF title differs", errors)
            check(metadata.get("/Author") == "Bertsekas, Dimitri", "authority PDF author differs", errors)
            for page in range(64, 87):
                raw = subprocess.run(
                    ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(page), "-l", str(page), str(SOURCE_PDF), "-"],
                    cwd=ROOT,
                    capture_output=True,
                    check=True,
                ).stdout
                observed = (len(raw), hashlib.sha256(raw).hexdigest())
                source_text_bytes[str(page)] = observed[0]
                source_text_hashes[str(page)] = observed[1]
                check(observed == (PAGE_TEXT_BYTES[page], PAGE_TEXT_SHA256[page]), f"authority page {page} text fingerprint differs", errors)
                text = raw.decode("utf-8", "replace")
                if page in PAGE_COUNTS:
                    check(PAGE_COUNTS[page][4] in text, f"authority page {page} heading differs", errors)
                else:
                    check("LECTURE 7" in text and "LECTURE OUTLINE" in text, "page 86 is not the clean Lecture 7 delimiter", errors)
            combined = subprocess.run(
                ["pdftotext", "-layout", "-enc", "UTF-8", "-f", "64", "-l", "85", str(SOURCE_PDF), "-"],
                cwd=ROOT,
                capture_output=True,
                check=True,
            ).stdout
            combined_record = {"bytes": len(combined), "sha256": hashlib.sha256(combined).hexdigest()}
            check((combined_record["bytes"], combined_record["sha256"]) == COMBINED_TEXT, "authority pages 64-85 combined fingerprint differs", errors)
            for page in source_reader.pages[63:86]:
                check(not (page.get("/Annots") or []), "authority pages 64-86 contain an annotation", errors)
            check(not (source_reader.get_fields() or {}), "authority PDF exposes form fields", errors)
            root = source_reader.trailer["/Root"]
            check("/OpenAction" not in root and "/JavaScript" not in (root.get("/Names") or {}), "authority PDF contains active content", errors)

            witness_text = WITNESS.read_text(encoding="utf-8")
            target_text = TARGET.read_text(encoding="utf-8")
            for label, text in (("witness", witness_text), ("target", target_text)):
                event_counts = Counter(re.findall(r"O015-MIT-SEM-\d{4}", text))
                check(event_counts == EXPECTED_EVENT_COUNTS[label], f"{label} correction-ID inventory differs", errors)
                check(MODEL in text and text.count(MODEL) == 1, f"{label} model identification differs", errors)
                check(LICENSE in text, f"{label} license statement differs", errors)
                check("![" not in text and "<img" not in text.lower() and "data:image" not in text.lower(), f"{label} embeds source-image bytes", errors)
                check(not any(token in text.lower() for token in ("<script", "<iframe", "<form", "<input", "<button")), f"{label} contains active or interactive markup", errors)
            check("no endorsement by the source author, MIT, or MIT OpenCourseWare" in witness_text, "witness nonendorsement differs", errors)
            check("tanpa dukungan tersirat" in target_text and "bukan penulis sumber, pemberi lisensi, atau wakil MIT" in target_text, "target nonendorsement differs", errors)
            check("Sixteen figure blocks containing twenty-four separately meaningful panels" in witness_text, "witness figure-panel census disclosure differs", errors)
            check("Enam belas blok gambar dengan dua puluh empat panel" in target_text, "target figure-panel census disclosure differs", errors)
            check("tidak mempunyai latihan, petunjuk, jawaban, solusi latihan, kode, tautan, atau permukaan interaktif" in target_text, "target zero-learning-surface disclosure differs", errors)

            topologies = {"witness": source_topology(WITNESS), "target": source_topology(TARGET)}
            for label, topology in topologies.items():
                validate_topology(label, topology, errors)
            for key in ("pages", "items", "displays", "figures"):
                check([row["id"] for row in topologies["witness"][key]] == [row["id"] for row in topologies["target"][key]], f"witness-target {key} stable-ID order differs", errors)

            (ROOT / "tmp/pdfs").mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="mit-l10-validation-", dir=ROOT / "tmp/pdfs") as temp:
                temp_root = Path(temp)
                authority_renders = render_authority(temp_root / "authority")
                expected_authority = [{"page": page, "bytes": value[0], "sha256": value[1]} for page, value in PAGE_RENDER.items()]
                check(authority_renders == expected_authority, "authority page render fingerprints differ", errors)
                for label in ("a", "b"):
                    out = temp_root / label
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
                    output_renders.append(render_output(pdf, temp_root / f"render-{label}"))
                check(len(rebuilds) == 2 and rebuilds[0] == rebuilds[1] == EXPECTED_BUILD, f"deterministic rebuild identities differ: {rebuilds}", errors)
                check(len(output_renders) == 2 and output_renders[0] == output_renders[1], "deterministic PDF render identities differ", errors)
                parser, duplicate_ids, unresolved = validate_html(temp_root / "a" / HTML.name, errors)
                _, pdf_observed = validate_pdf(temp_root / "a" / PDF.name, errors)

                if HTML.exists() != PDF.exists():
                    canonical = {"status": "incomplete_pair"}
                    errors.append("canonical L10 output pair is incomplete")
                elif HTML.exists() and PDF.exists():
                    canonical = {"status": "bound", "html": identity(HTML), "pdf": identity(PDF)}
                    check((HTML.stat().st_size, digest(HTML)) == EXPECTED_BUILD["html"], "canonical HTML differs from deterministic build", errors)
                    check((PDF.stat().st_size, digest(PDF)) == EXPECTED_BUILD["pdf"], "canonical PDF differs from deterministic build", errors)

                if stage == "strict-final" and present["visual"]:
                    before = len(errors)
                    visual = validate_visual(VISUAL_QA, EXPECTED_BUILD["pdf"], output_renders[0], errors)
                    evidence["visual"] = {"status": "validated" if len(errors) == before else "invalid", "result": visual.get("result") or (visual.get("inspection") or {}).get("result"), **identity(VISUAL_QA)}
                if stage == "strict-final" and present["browser"]:
                    before = len(errors)
                    browser = validate_browser(BROWSER_QA, EXPECTED_BUILD["html"], errors)
                    evidence["browser"] = {"status": "validated" if len(errors) == before else "invalid", "result": browser.get("result"), **identity(BROWSER_QA)}
                if stage == "strict-final" and present["rereview"]:
                    rereview = validate_rereview(REREVIEW, errors)
                    evidence["rereview"] = {"status": "validated" if rereview["disposition"] == "pass" else "invalid", **rereview}
        except Exception as exc:
            errors.append(f"validation exception: {type(exc).__name__}: {exc}")

    result = "pass" if not errors else "fail"
    release_ready = result == "pass" and canonical.get("status") == "bound" and stage == "strict-final" and all(evidence.get(name, {}).get("status") == "validated" for name in ("visual", "browser", "rereview"))
    report = {
        "schema": "o015-mit-l10-validation-v1",
        "validation_epoch": "2026-08-24",
        "result": result,
        "release_ready": release_ready,
        "boundary": {
            "source_pdf_pages": list(SOURCE_PAGES),
            "next_source_page": DELIMITER_PAGE,
            "next_heading": "LECTURE 7 - LECTURE OUTLINE",
            "source_pages": 22,
            "source_items": 70,
            "source_display_wrappers": 41,
            "display_formula_blocks": 41,
            "source_figures": 16,
            "source_figure_panels": 24,
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
            "combined_pages_64_85": combined_record,
            "render_fingerprints": authority_renders,
        },
        "topology": {
            "page_counts": {str(page): {"items": row[0], "display_wrappers": row[1], "figure_blocks": row[2], "figure_panels": row[3], "heading": row[4]} for page, row in PAGE_COUNTS.items()},
            "figure_panel_map": FIGURE_PANELS,
        },
        "formula_inventory": {
            label: {"display_blocks": len(topology.get("display_math", [])), "sequence_sha256": hashlib.sha256("\n".join(topology.get("display_math", [])).encode("utf-8")).hexdigest() if topology else None}
            for label, topology in topologies.items()
        },
        "correction_ids": list(EVENT_IDS),
        "build": {
            "command": "python qa/build_mit_l10.py --html-output <html> --pdf-output <pdf>",
            "deterministic_rebuilds": 2,
            "rebuild_identities": rebuilds,
            "render_identities": output_renders,
            "expected": EXPECTED_BUILD,
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
            "images": parser.images,
            "media_or_embeds": parser.media,
            "form_controls": parser.interactive,
            "duplicate_ids": duplicate_ids,
            "unresolved_fragments": unresolved,
        },
        "pdf": {**pdf_observed, "render_identities": output_renders[0] if output_renders else []},
        "rights": {
            "component": "MIT OCW 6.253 complete-notes, Lecture 6",
            "license": LICENSE,
            "athena_source_figure_blocks_omitted": 16,
            "athena_source_figure_panels_omitted": 24,
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
