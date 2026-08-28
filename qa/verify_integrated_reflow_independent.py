#!/usr/bin/env python3
"""Independent, offline QA for the integrated O015 HTML and EPUB readers.

This verifier intentionally does not import the production builder or its
companion verifier.  It binds the live admitted sources to the build receipt,
checks the retained two-build evidence, and inspects the final HTML and EPUB
bytes directly.  It writes one self-contained JSON receipt.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
QA_DIR = ROOT / "qa"
BUILD_SCRIPT = QA_DIR / "build_integrated_readers.py"
PRIMARY_VERIFIER = QA_DIR / "verify_integrated_readers.py"
BUILD_REPORT = QA_DIR / "INTEGRATED_READERS_BUILD.json"
PRIMARY_REPORT = QA_DIR / "INTEGRATED_READERS_VALIDATION.json"
RECEIPT = QA_DIR / "INTEGRATED_REFLOW_INDEPENDENT.json"

HTML_PATH = ROOT / "output" / "html" / "D90-O015-optimisasi-lanjut-analisis-konveks-id.html"
EPUB_PATH = ROOT / "output" / "epub" / "D90-O015-optimisasi-lanjut-analisis-konveks-id.epub"
TMP_DIR = ROOT / "tmp" / "integrated-readers"
COMBINED_TEX = TMP_DIR / "D90-O015-integrated-reader-id.tex"
HTML_FIRST = TMP_DIR / "integrated-reader.first.html"
HTML_SECOND = TMP_DIR / "integrated-reader.second.html"
EPUB_FIRST = TMP_DIR / "integrated-reader.first.epub"
EPUB_SECOND = TMP_DIR / "integrated-reader.second.epub"
EPUB_CSS_INTERMEDIATE = TMP_DIR / "integrated-reader.css"
EPUBCHECK_JAR = ROOT / "tmp" / "tools" / "epubcheck-5.3.0" / "epubcheck.jar"

TITLE = "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia"
IDENTIFIER = "urn:uuid:81057e39-68c8-5b34-8d59-f53deae44ec2"
FIXED_MODIFIED = "2026-08-27T00:00:00Z"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

MAIN_BODIES = (
    "habring-01-prasyarat-id.tex",
    "habring-02-konveksitas-id.tex",
    "habring-03-subgradien-id.tex",
    "habring-04-metode-subgradien-terproyeksi-id.tex",
    "habring-05-metode-gradien-proksimal-id.tex",
    "habring-06-akselerasi-id.tex",
    "habring-07-dualitas-id.tex",
    "habring-08-penurunan-gradien-stokastik-id.tex",
    "habring-09-transportasi-optimal-id.tex",
    "becker-01-dualitas-lagrange-slater-kkt-id.tex",
    "becker-03-reduksi-varians-id.tex",
    "original-01-metode-stokastik-komposit-cermin-minibatch-id.tex",
    "becker-02-pemisahan-douglas-rachford-id.tex",
    "original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex",
    "original-03-penutupan-kursus-id.tex",
)

ORIGINAL_03_MODULES = (
    "original-03/00-peta-asesmen-id.tex",
    "original-03/01-diagnostik-prasyarat-id.tex",
    "original-03/02-set-soal-dasar-konveks-id.tex",
    "original-03/03-set-soal-metode-proksimal-id.tex",
    "original-03/04-set-soal-dualitas-kkt-id.tex",
    "original-03/05-set-soal-metode-stokastik-id.tex",
    "original-03/06-set-soal-operator-monoton-id.tex",
    "original-03/07-set-soal-transportasi-dan-sintesis-id.tex",
    "original-03/08-rubrik-pembuktian-id.tex",
    "original-03/09-ujian-tengah-id.tex",
    "original-03/10-ujian-akhir-id.tex",
    "original-03/11-laboratorium-globalisasi-newton-id.tex",
    "original-03/12-laboratorium-transportasi-entropik-id.tex",
    "original-03/13-proyek-kapstone-masalah-invers-komposit-id.tex",
)

CANONICAL_ORDER = MAIN_BODIES + ORIGINAL_03_MODULES
SOURCE_RELATIVES = tuple(f"source/id-ID/{name}" for name in CANONICAL_ORDER)
BIBLIOGRAPHY_RELATIVE = "source/id-ID/references-integrated-id.bib"
EXPECTED_INPUTS = SOURCE_RELATIVES + (BIBLIOGRAPHY_RELATIVE,)
ENVIRONMENTS = ("defn", "theorem", "lemma", "cor", "prop", "example", "exercise", "rem", "proof")

ORDER_MARKERS = (
    "Prasyarat",
    "Kekonveksan",
    "Subgradien",
    "Penurunan subgradien terproyeksi",
    "Metode gradien proksimal",
    "Akselerasi",
    "Dualitas",
    "Penurunan Gradien Stokastik",
    "Selingan tentang Transportasi Optimal",
    "Dualitas Lagrange, kondisi Slater, dan kondisi KKT",
    "Reduksi Varians untuk SAA",
    "Metode Stokastik Komposit, Cermin, dan Minibatch",
    "Pemisahan Douglas–Rachford",
    "Ketaksamaan Variasional, Operator Monoton, Resolven, dan Pemisahan",
    "Asesmen, Laboratorium, dan Proyek Penutup",
    "Peta asesmen dan kontrak topologi",
    "Diagnostik prasyarat",
    "Set soal I: dasar konveks",
    "Set soal II: metode proksimal",
    "Set soal III: dualitas dan kondisi KKT",
    "Set soal IV: metode stokastik",
    "Set soal V: operator monoton dan metode pemisahan",
    "Set soal VI: transportasi optimal dan sintesis",
    "Rubrik analitik untuk pembuktian",
    "Ujian tengah kumulatif",
    "Ujian akhir kumulatif",
    "Laboratorium 3: kegagalan lokal dan globalisasi Newton",
    "Laboratorium 4: Sinkhorn log-domain dan sertifikat transportasi",
    "Proyek kapstone: masalah invers komposit yang tahan pencilan",
)

FIGURES = (
    "sets.png",
    "balls.png",
    "convex_fct.png",
    "gradient.png",
    "subgradient.png",
)

VIEWPORT_PROFILES = (
    {"name": "desktop", "width": 1440, "height": 900},
    {"name": "tablet", "width": 834, "height": 1112},
    {"name": "phone", "width": 390, "height": 844},
)

PROFILE_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/](?:Users|Documents|AppData)[\\/]", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"/Users/", re.IGNORECASE),
    re.compile(r"\\Users\\", re.IGNORECASE),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fact(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def load_json(path: Path, failures: list[str]) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        failures.append(f"cannot read {path.relative_to(ROOT).as_posix()}: {exc}")
        return {}
    if not isinstance(value, dict):
        failures.append(f"JSON root is not an object: {path.relative_to(ROOT).as_posix()}")
        return {}
    return value


def epub_fragment(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"[^A-Za-z0-9_.:-]", "-", value)
    return value or "label"


def strip_markup(text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def ordered_positions(text: str, markers: tuple[str, ...]) -> tuple[list[int], list[str]]:
    positions: list[int] = []
    missing: list[str] = []
    cursor = 0
    for marker in markers:
        position = text.find(marker, cursor)
        positions.append(position)
        if position < 0:
            missing.append(marker)
        else:
            cursor = position + len(marker)
    return positions, missing


def heading_metrics(text: str) -> dict[str, object]:
    matches = re.findall(r"<h([1-6])\b[^>]*>(.*?)</h\1>", text, flags=re.DOTALL | re.IGNORECASE)
    levels = [int(level) for level, _ in matches]
    empty = [index for index, (_level, body) in enumerate(matches, start=1) if not strip_markup(body)]
    jumps = [
        {"from_index": index, "from_level": current, "to_level": following}
        for index, (current, following) in enumerate(zip(levels, levels[1:]), start=1)
        if following > current + 1
    ]
    return {
        "count": len(matches),
        "counts_by_level": {f"h{level}": levels.count(level) for level in range(1, 7)},
        "empty_count": len(empty),
        "empty_indices": empty[:20],
        "upward_level_jump_count": len(jumps),
        "upward_level_jumps": jumps[:30],
    }


def math_metrics(text: str) -> dict[str, int]:
    openings = re.findall(r"<math\b[^>]*>", text, flags=re.IGNORECASE)
    return {
        "mathml_count": len(openings),
        "mathml_namespace_count": sum(
            1 for opening in openings if 'xmlns="http://www.w3.org/1998/Math/MathML"' in opening
        ),
        "tex_annotation_count": len(
            re.findall(r'<annotation\b[^>]*encoding="application/x-tex"', text, flags=re.IGNORECASE)
        ),
        "display_mathml_count": len(
            re.findall(r'<math\b[^>]*display="block"', text, flags=re.IGNORECASE)
        ),
    }


def css_rule(css: str, selector_fragment: str) -> str:
    declarations: list[str] = []
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css, flags=re.DOTALL):
        if selector_fragment.lower() in match.group(1).lower():
            declarations.append(re.sub(r"\s+", " ", match.group(2)).strip().lower())
    return "; ".join(declarations)


def declaration_has(declaration: str, property_name: str, value_pattern: str) -> bool:
    return bool(
        re.search(
            rf"(?:^|;)\s*{re.escape(property_name)}\s*:\s*{value_pattern}\s*(?:;|$)",
            declaration,
            flags=re.IGNORECASE,
        )
    )


def source_contract(build_report: dict[str, object], failures: list[str]) -> dict[str, object]:
    manifest_inputs = build_report.get("inputs", [])
    if not isinstance(manifest_inputs, list):
        manifest_inputs = []
        failures.append("build report inputs is not a list")
    input_by_path = {
        str(item.get("path")): item
        for item in manifest_inputs
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    require(tuple(input_by_path) == EXPECTED_INPUTS, "build input inventory/order differs from the 29 admitted TeX sources plus bibliography", failures)
    require(build_report.get("canonical_order") == list(CANONICAL_ORDER), "build canonical order differs from the independent 15+14 contract", failures)

    stale_inputs: list[dict[str, object]] = []
    current_inputs: list[dict[str, object]] = []
    texts: dict[str, str] = {}
    for relative in EXPECTED_INPUTS:
        path = ROOT / PurePosixPath(relative)
        if not path.is_file():
            stale_inputs.append({"path": relative, "reason": "missing"})
            continue
        current = fact(path)
        current_inputs.append(current)
        expected = input_by_path.get(relative, {})
        if current["bytes"] != expected.get("bytes") or current["sha256"] != expected.get("sha256"):
            stale_inputs.append(
                {
                    "path": relative,
                    "reason": "bytes-or-hash-mismatch",
                    "manifest_bytes": expected.get("bytes"),
                    "current_bytes": current["bytes"],
                    "manifest_sha256": expected.get("sha256"),
                    "current_sha256": current["sha256"],
                }
            )
        if relative.endswith(".tex"):
            try:
                texts[relative] = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                failures.append(f"cannot decode admitted TeX source {relative}: {exc}")
    require(not stale_inputs, f"build report is stale against live sources: {stale_inputs}", failures)

    labels: list[str] = []
    first_labels: list[str] = []
    for relative in SOURCE_RELATIVES:
        found = re.findall(r"\\label\{([^}]+)\}", texts.get(relative, ""))
        labels.extend(found)
        if found:
            first_labels.append(epub_fragment(found[0]))
        else:
            failures.append(f"admitted source has no reading-order label sentinel: {relative}")
    normalized_labels = [epub_fragment(label) for label in labels]
    duplicates = sorted(label for label, count in Counter(labels).items() if count > 1)
    normalized_duplicates = sorted(label for label, count in Counter(normalized_labels).items() if count > 1)
    require(not duplicates, f"duplicate canonical TeX labels: {duplicates[:20]}", failures)
    require(not normalized_duplicates, f"label normalization collisions: {normalized_duplicates[:20]}", failures)

    environment_counts = {
        env: sum(len(re.findall(rf"\\begin\{{{env}\}}", text)) for text in texts.values())
        for env in ENVIRONMENTS
    }
    source_summary = build_report.get("source", {})
    require(isinstance(source_summary, dict), "build report source summary is not an object", failures)
    if isinstance(source_summary, dict):
        require(source_summary.get("file_count") == 29, "build report source file_count is not 29", failures)
        require(source_summary.get("label_count") == len(labels), "build report label_count differs from live sources", failures)
        require(source_summary.get("environment_counts") == environment_counts, "build report environment counts differ from live sources", failures)

    aggregator_relative = "source/id-ID/original-03-penutupan-kursus-id.tex"
    aggregator = texts.get(aggregator_relative, "")
    module_inputs = tuple(re.findall(r"\\input\{(original-03/[^}]+)\}", aggregator))
    expected_module_stems = tuple(module.removesuffix(".tex") for module in ORIGINAL_03_MODULES)
    require(module_inputs == expected_module_stems, "Original-03 aggregator does not include all 14 modules exactly once in canonical order", failures)

    correction_source = texts.get("source/id-ID/original-03/05-set-soal-metode-stokastik-id.tex", "")
    require(r"0=\eta g+\eta s^+" in correction_source, "live Original-03 module 05 lacks the stabilized +\\eta correction", failures)

    combined: dict[str, object] = {"present": COMBINED_TEX.is_file()}
    if COMBINED_TEX.is_file():
        combined.update(fact(COMBINED_TEX))
        combined_text = COMBINED_TEX.read_text(encoding="utf-8")
        body_markers = tuple(re.findall(r"^% integrated-source: (.+)$", combined_text, flags=re.MULTILINE))
        module_markers = tuple(re.findall(r"^% integrated-module: (.+)$", combined_text, flags=re.MULTILINE))
        require(body_markers == MAIN_BODIES, "combined TeX does not contain all 15 body markers in canonical order", failures)
        require(module_markers == ORIGINAL_03_MODULES, "combined TeX does not contain all 14 Original-03 module markers in canonical order", failures)
        require(r"0=\eta g+\eta s^+" in combined_text, "combined TeX does not contain the stabilized +\\eta correction", failures)
        require(not re.search(r"\\input\{original-03/", combined_text), "combined TeX retains an unexpanded Original-03 input", failures)
        if isinstance(source_summary, dict):
            require(combined.get("bytes") == source_summary.get("combined_source_bytes"), "combined TeX size differs from build report", failures)
            require(combined.get("sha256") == source_summary.get("combined_source_sha256"), "combined TeX hash differs from build report", failures)
        combined["body_marker_count"] = len(body_markers)
        combined["module_marker_count"] = len(module_markers)
    else:
        failures.append("retained combined TeX build evidence is missing")

    return {
        "main_body_count": len(MAIN_BODIES),
        "original_03_module_count": len(ORIGINAL_03_MODULES),
        "tex_file_count": len(SOURCE_RELATIVES),
        "bibliography_count": 1,
        "manifest_input_count": len(manifest_inputs),
        "live_inputs_bound": not stale_inputs,
        "stale_inputs": stale_inputs,
        "inputs": current_inputs,
        "label_count": len(labels),
        "first_label_count": len(first_labels),
        "first_labels": first_labels,
        "environment_counts": environment_counts,
        "aggregator_module_order": list(module_inputs),
        "stabilized_module_05_correction_present": r"0=\eta g+\eta s^+" in correction_source,
        "combined_source": combined,
        "normalized_labels": normalized_labels,
    }


def deterministic_evidence(build_report: dict[str, object], failures: list[str]) -> dict[str, object]:
    paths = {
        "html_first": HTML_FIRST,
        "html_second": HTML_SECOND,
        "epub_first": EPUB_FIRST,
        "epub_second": EPUB_SECOND,
    }
    evidence: dict[str, object] = {}
    for name, path in paths.items():
        if path.is_file():
            evidence[name] = fact(path)
        else:
            failures.append(f"retained deterministic build evidence missing: {path.relative_to(ROOT).as_posix()}")
            evidence[name] = {"path": path.relative_to(ROOT).as_posix(), "missing": True}

    html_equal = HTML_FIRST.is_file() and HTML_SECOND.is_file() and HTML_FIRST.read_bytes() == HTML_SECOND.read_bytes()
    epub_equal = EPUB_FIRST.is_file() and EPUB_SECOND.is_file() and EPUB_FIRST.read_bytes() == EPUB_SECOND.read_bytes()
    require(html_equal, "retained HTML builds are not byte-identical", failures)
    require(epub_equal, "retained EPUB builds are not byte-identical", failures)
    require(HTML_SECOND.is_file() and HTML_PATH.is_file() and HTML_SECOND.read_bytes() == HTML_PATH.read_bytes(), "final HTML differs from retained second deterministic build", failures)
    require(EPUB_SECOND.is_file() and EPUB_PATH.is_file() and EPUB_SECOND.read_bytes() == EPUB_PATH.read_bytes(), "final EPUB differs from retained second deterministic build", failures)

    claims = build_report.get("determinism", {})
    require(isinstance(claims, dict), "build determinism claim is not an object", failures)
    if isinstance(claims, dict):
        require(claims.get("html_builds") == 2 and claims.get("html_byte_identical") is True, "build report lacks two-build HTML determinism claim", failures)
        require(claims.get("epub_builds") == 2 and claims.get("epub_byte_identical") is True, "build report lacks two-build EPUB determinism claim", failures)
        require(claims.get("epub_zip_timestamps") == "1980-01-01T00:00:00", "build report ZIP epoch claim differs", failures)
        require(claims.get("epub_modified") == FIXED_MODIFIED, "build report fixed modified timestamp differs", failures)

    return {
        "html_builds": 2,
        "html_byte_identical": html_equal,
        "html_final_matches_second": HTML_SECOND.is_file() and HTML_PATH.is_file() and HTML_SECOND.read_bytes() == HTML_PATH.read_bytes(),
        "epub_builds": 2,
        "epub_byte_identical": epub_equal,
        "epub_final_matches_second": EPUB_SECOND.is_file() and EPUB_PATH.is_file() and EPUB_SECOND.read_bytes() == EPUB_PATH.read_bytes(),
        "evidence": evidence,
    }


def source_image_hashes(failures: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for filename in FIGURES:
        path = ROOT / "source" / "id-ID" / "figures" / filename
        if not path.is_file():
            failures.append(f"source raster missing: {path.relative_to(ROOT).as_posix()}")
            continue
        result[filename] = sha256(path)
    require(len(set(result.values())) == len(FIGURES), "source raster hashes are not one-to-one", failures)
    return result


def validate_html(
    source: dict[str, object],
    build_report: dict[str, object],
    primary_report: dict[str, object],
    image_hashes: dict[str, str],
    failures: list[str],
) -> dict[str, object]:
    if not HTML_PATH.is_file():
        failures.append(f"HTML artifact missing: {HTML_PATH.relative_to(ROOT).as_posix()}")
        return {}
    text = HTML_PATH.read_text(encoding="utf-8")
    plain = strip_markup(text)
    current = fact(HTML_PATH)
    build_artifacts = build_report.get("artifacts", {})
    expected = build_artifacts.get("html", {}) if isinstance(build_artifacts, dict) else {}
    require(isinstance(expected, dict) and current["bytes"] == expected.get("bytes") and current["sha256"] == expected.get("sha256"), "HTML size/hash differs from build report", failures)
    primary_html = primary_report.get("html", {})
    require(isinstance(primary_html, dict) and current["bytes"] == primary_html.get("bytes") and current["sha256"] == primary_html.get("sha256"), "HTML size/hash differs from primary validation report", failures)

    ids = [html.unescape(value) for value in re.findall(r'\bid="([^"]+)"', text)]
    id_counts = Counter(ids)
    duplicate_ids = sorted(identifier for identifier, count in id_counts.items() if count > 1)
    require(not duplicate_ids, f"HTML duplicate IDs: {duplicate_ids[:20]}", failures)

    labels = source.get("normalized_labels", [])
    bad_labels = {label: id_counts.get(label, 0) for label in labels if id_counts.get(label, 0) != 1}
    require(not bad_labels, f"HTML does not preserve each canonical source label exactly once: {dict(list(bad_labels.items())[:20])}", failures)

    hrefs = [html.unescape(value) for value in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', text, flags=re.IGNORECASE)]
    unresolved_fragments: list[str] = []
    unresolved_paths: list[str] = []
    for reference in hrefs:
        parsed = urlsplit(reference)
        if parsed.scheme or reference.startswith("//"):
            continue
        if parsed.path:
            unresolved_paths.append(reference)
        if parsed.fragment and unquote(parsed.fragment) not in id_counts:
            unresolved_fragments.append(reference)
    require(not unresolved_paths, f"standalone HTML has unresolved relative hyperlink paths: {unresolved_paths[:20]}", failures)
    require(not unresolved_fragments, f"HTML has unresolved internal fragments: {unresolved_fragments[:20]}", failures)

    images = re.findall(r"<img\b[^>]*>", text, flags=re.IGNORECASE)
    embedded_hashes: list[str] = []
    image_failures: list[str] = []
    for index, tag in enumerate(images, start=1):
        src_match = re.search(r'\bsrc="([^"]+)"', tag, flags=re.IGNORECASE)
        alt_match = re.search(r'\balt="([^"]*)"', tag, flags=re.IGNORECASE)
        desc_match = re.search(r'\baria-describedby="([^"]+)"', tag, flags=re.IGNORECASE)
        if not src_match or not html.unescape(src_match.group(1)).startswith("data:image/png;base64,"):
            image_failures.append(f"image {index} is not an embedded PNG")
        else:
            try:
                payload = base64.b64decode(html.unescape(src_match.group(1)).split(",", 1)[1], validate=True)
                embedded_hashes.append(sha256_bytes(payload))
            except (ValueError, base64.binascii.Error) as exc:
                image_failures.append(f"image {index} data URI is invalid: {exc}")
        if not alt_match or not html.unescape(alt_match.group(1)).strip():
            image_failures.append(f"image {index} has empty alt text")
        if not desc_match or html.unescape(desc_match.group(1)) not in id_counts:
            image_failures.append(f"image {index} lacks a resolvable aria-describedby target")
    require(len(images) == 5, f"HTML expected five raster uses, got {len(images)}", failures)
    require(not image_failures, f"HTML image accessibility/integrity failures: {image_failures}", failures)
    require(Counter(embedded_hashes) == Counter(image_hashes.values()), "HTML embedded raster bytes do not match the five admitted source images exactly once", failures)

    metrics = math_metrics(text)
    require(metrics["mathml_count"] == 4535, f"HTML MathML count changed: {metrics}", failures)
    require(metrics["mathml_namespace_count"] == metrics["mathml_count"], f"HTML contains non-native/unnamespaced MathML: {metrics}", failures)
    require(metrics["tex_annotation_count"] == metrics["mathml_count"], f"HTML MathML/TeX annotation mismatch: {metrics}", failures)
    require(metrics["display_mathml_count"] == 729, f"HTML display MathML count changed: {metrics}", failures)
    require(not re.search(r"mathjax|katex", text, flags=re.IGNORECASE), "HTML contains a MathJax/KaTeX runtime surface instead of native-only MathML", failures)
    require(r"0=\eta g+\eta s^+" in text, "HTML does not contain the stabilized +\\eta TeX annotation", failures)

    heading = heading_metrics(text)
    require(heading["count"] >= 200 and heading["empty_count"] == 0, f"HTML heading topology is implausible: {heading}", failures)
    require(text.lstrip().lower().startswith("<!doctype html>"), "HTML5 doctype missing", failures)
    require(bool(re.search(r'<html\b[^>]*\blang="id-ID"', text, flags=re.IGNORECASE)), "HTML language is not id-ID", failures)
    require('name="viewport"' in text, "HTML viewport metadata missing", failures)
    require(len(re.findall(r'<header\b[^>]*role="banner"', text, flags=re.IGNORECASE)) == 1, "HTML banner landmark count is not one", failures)
    require(len(re.findall(r'<nav\b[^>]*role="doc-toc"', text, flags=re.IGNORECASE)) == 1, "HTML TOC landmark count is not one", failures)
    require(len(re.findall(r'<main\b[^>]*id="main-content"', text, flags=re.IGNORECASE)) == 1, "HTML main landmark count is not one", failures)
    require(len(re.findall(r'<footer\b[^>]*role="contentinfo"', text, flags=re.IGNORECASE)) == 1, "HTML contentinfo landmark count is not one", failures)
    require('<a class="skip-link" href="#main-content">' in text, "HTML skip link missing", failures)

    marker_positions, missing_markers = ordered_positions(plain, ORDER_MARKERS)
    require(not missing_markers, f"HTML semantic order markers missing/out of order: {missing_markers}", failures)
    first_labels = source.get("first_labels", [])
    first_positions = [text.find(f'id="{label}"') for label in first_labels]
    require(all(position >= 0 for position in first_positions), "HTML is missing one or more source order label sentinels", failures)
    require(first_positions == sorted(first_positions), "HTML source bodies/modules are not in canonical order", failures)

    styles = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", text, flags=re.DOTALL | re.IGNORECASE))
    body_rule = css_rule(styles, "body")
    math_rule = css_rule(styles, 'math[display="block"]')
    inline_math_rule = css_rule(styles, ".math.inline")
    table_rule = css_rule(styles, "table")
    pre_rule = css_rule(styles, "pre")
    image_rule = css_rule(styles, "img")
    static_reflow = {
        "viewport_meta": 'name="viewport"' in text,
        "content_max_96rem": bool(re.search(r"--content-max\s*:\s*96rem", styles)),
        "narrow_breakpoint_48rem": bool(re.search(r"@media\s*\(max-width\s*:\s*48rem\)", styles)),
        "page_overflow_clipped": declaration_has(body_rule, "overflow-x", r"clip"),
        "display_math_local_scroll": declaration_has(math_rule, "max-width", r"100%") and declaration_has(math_rule, "overflow-x", r"auto"),
        "inline_math_local_scroll": declaration_has(inline_math_rule, "max-width", r"100%") and declaration_has(inline_math_rule, "overflow-x", r"auto"),
        "table_local_scroll": declaration_has(table_rule, "max-width", r"100%") and declaration_has(table_rule, "overflow-x", r"auto"),
        "pre_local_scroll": declaration_has(pre_rule, "max-width", r"100%") and declaration_has(pre_rule, "overflow-x", r"auto"),
        "images_fluid": declaration_has(image_rule, "max-width", r"100%") and declaration_has(image_rule, "height", r"auto"),
    }
    require(all(static_reflow.values()), f"HTML static reflow contract incomplete: {static_reflow}", failures)

    runtime_dependencies: list[str] = []
    for tag, attribute in (("script", "src"), ("link", "href"), ("img", "src"), ("source", "src"), ("iframe", "src"), ("object", "data"), ("audio", "src"), ("video", "src")):
        for reference in re.findall(rf"<{tag}\b[^>]*\b{attribute}=\"([^\"]+)\"", text, flags=re.IGNORECASE):
            decoded = html.unescape(reference)
            parsed = urlsplit(decoded)
            if parsed.scheme in {"http", "https"} or decoded.startswith("//"):
                runtime_dependencies.append(f"{tag}.{attribute}={decoded}")
    if re.search(r"@import\s+(?:url\()?\s*['\"]?https?://|url\(\s*['\"]?https?://", styles, flags=re.IGNORECASE):
        runtime_dependencies.append("remote CSS import/url")
    require(not runtime_dependencies, f"HTML has external runtime dependencies: {runtime_dependencies}", failures)
    require(all(not pattern.search(text) for pattern in PROFILE_PATTERNS), "HTML contains a local profile/path locator", failures)

    return {
        **current,
        "doctype_html5": text.lstrip().lower().startswith("<!doctype html>"),
        "language": "id-ID",
        "landmarks": {"banner": 1, "toc": 1, "main": 1, "contentinfo": 1},
        "headings": heading,
        "id_count": len(ids),
        "duplicate_ids": duplicate_ids,
        "source_label_count": len(labels),
        "source_labels_preserved_exactly_once": len(labels) - len(bad_labels),
        "canonical_order_marker_count": len(marker_positions) - len(missing_markers),
        "source_order_sentinel_count": len(first_positions),
        "internal_link_count": sum(1 for href in hrefs if urlsplit(href).fragment),
        "unresolved_internal_fragments": unresolved_fragments,
        "image_count": len(images),
        "nonempty_alt_count": len(images) - sum(1 for failure in image_failures if "alt" in failure),
        "long_description_target_count": len(set(re.findall(r'class="long-description"\s+id="([^"]+)"', text, flags=re.IGNORECASE))),
        "embedded_source_image_hashes": embedded_hashes,
        "math": metrics,
        "static_reflow": static_reflow,
        "external_runtime_dependencies": runtime_dependencies,
        "stabilized_module_05_correction_present": r"0=\eta g+\eta s^+" in text,
    }


def resolve_member(base: str, reference: str) -> str:
    parsed = urlsplit(html.unescape(reference))
    if parsed.scheme or reference.startswith("//"):
        return ""
    if not parsed.path:
        return base
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), unquote(parsed.path)))


def run_epubcheck(failures: list[str], limitations: list[str]) -> dict[str, object]:
    if not EPUBCHECK_JAR.is_file() or not shutil.which("java"):
        limitations.append("EPUBCheck was not locally available")
        return {"performed": False, "jar_present": EPUBCHECK_JAR.is_file(), "java_present": bool(shutil.which("java"))}
    completed = subprocess.run(
        ["java", "-jar", str(EPUBCHECK_JAR), str(EPUB_PATH)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (completed.stdout + completed.stderr).replace(str(ROOT), "<PROJECT_ROOT>").replace(ROOT.as_posix(), "<PROJECT_ROOT>").strip()
    require(completed.returncode == 0, f"EPUBCheck failed with exit {completed.returncode}: {output[-3000:]}", failures)
    require("0 fatals / 0 errors / 0 warnings" in output, f"EPUBCheck did not report a clean zero-finding result: {output[-1000:]}", failures)
    return {
        "performed": True,
        "jar_sha256": sha256(EPUBCHECK_JAR),
        "exit_code": completed.returncode,
        "output": output,
    }


def validate_epub(
    source: dict[str, object],
    build_report: dict[str, object],
    primary_report: dict[str, object],
    image_hashes: dict[str, str],
    failures: list[str],
    limitations: list[str],
) -> dict[str, object]:
    if not EPUB_PATH.is_file():
        failures.append(f"EPUB artifact missing: {EPUB_PATH.relative_to(ROOT).as_posix()}")
        return {}
    current = fact(EPUB_PATH)
    build_artifacts = build_report.get("artifacts", {})
    expected = build_artifacts.get("epub", {}) if isinstance(build_artifacts, dict) else {}
    require(isinstance(expected, dict) and current["bytes"] == expected.get("bytes") and current["sha256"] == expected.get("sha256"), "EPUB size/hash differs from build report", failures)
    primary_epub = primary_report.get("epub", {})
    require(isinstance(primary_epub, dict) and current["bytes"] == primary_epub.get("bytes") and current["sha256"] == primary_epub.get("sha256"), "EPUB size/hash differs from primary validation report", failures)

    with zipfile.ZipFile(EPUB_PATH) as archive:
        bad_crc = archive.testzip()
        infos = archive.infolist()
        names = [info.filename for info in infos]
        members = {name: archive.read(name) for name in names if not name.endswith("/")}
        archive_comment = archive.comment
    require(bad_crc is None, f"EPUB ZIP CRC failure: {bad_crc}", failures)
    require(bool(infos) and infos[0].filename == "mimetype", "EPUB mimetype is not the first ZIP entry", failures)
    require(bool(infos) and infos[0].compress_type == zipfile.ZIP_STORED, "EPUB mimetype entry is compressed", failures)
    require(bool(infos) and infos[0].extra == b"", "EPUB mimetype entry has an extra field", failures)
    require(members.get("mimetype") == b"application/epub+zip", "EPUB mimetype payload is invalid", failures)
    require(len(names) == len(set(names)), "EPUB has duplicate ZIP member names", failures)
    require(all(info.date_time == ZIP_EPOCH for info in infos), "EPUB ZIP timestamps are not normalized to the fixed epoch", failures)
    require(all(not (info.flag_bits & 0x1) for info in infos), "EPUB contains encrypted ZIP entries", failures)
    require(archive_comment == b"", "EPUB ZIP archive comment is not empty", failures)
    unsafe = [name for name in names if name.startswith(("/", "\\")) or ".." in PurePosixPath(name).parts]
    require(not unsafe, f"EPUB has unsafe member names: {unsafe}", failures)

    xml_names = [name for name in members if PurePosixPath(name).suffix.lower() in {".xml", ".opf", ".ncx", ".xhtml"}]
    parsed: dict[str, ET.Element] = {}
    parse_failures: list[str] = []
    for name in xml_names:
        try:
            parsed[name] = ET.fromstring(members[name])
        except ET.ParseError as exc:
            parse_failures.append(f"{name}: {exc}")
    require(not parse_failures, f"EPUB XML parse failures: {parse_failures}", failures)

    container_name = "META-INF/container.xml"
    require(container_name in parsed, "EPUB container.xml missing or unparsable", failures)
    rootfile = ""
    if container_name in parsed:
        rootfiles = parsed[container_name].findall(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
        require(len(rootfiles) == 1, f"EPUB container rootfile count is {len(rootfiles)}", failures)
        if len(rootfiles) == 1:
            rootfile = rootfiles[0].attrib.get("full-path", "")
            require(rootfile in parsed, f"EPUB rootfile target missing/unparsable: {rootfile}", failures)

    manifest: dict[str, tuple[str, str, str]] = {}
    manifest_members: set[str] = set()
    nav_members: list[str] = []
    spine_ids: list[str] = []
    metadata_values: dict[str, object] = {}
    if rootfile in parsed:
        opf = parsed[rootfile]
        ns = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
        require(opf.attrib.get("version", "").startswith("3"), f"EPUB OPF is not version 3: {opf.attrib.get('version')}", failures)
        metadata = opf.find("opf:metadata", ns)
        require(metadata is not None, "EPUB metadata block missing", failures)
        if metadata is not None:
            def dc(local: str) -> list[str]:
                return ["".join(node.itertext()).strip() for node in metadata.findall(f"dc:{local}", ns)]

            properties = [
                (node.attrib.get("property", ""), "".join(node.itertext()).strip())
                for node in metadata.findall("opf:meta", ns)
            ]
            metadata_values = {
                "title": dc("title"),
                "language": dc("language"),
                "identifier": dc("identifier"),
                "creators": dc("creator"),
                "rights": dc("rights"),
                "properties": properties,
            }
            require(metadata_values["title"] == [TITLE], f"EPUB title mismatch: {metadata_values['title']}", failures)
            require(metadata_values["language"] == ["id-ID"], f"EPUB language mismatch: {metadata_values['language']}", failures)
            require(IDENTIFIER in metadata_values["identifier"], "EPUB fixed identifier missing", failures)
            rights = " ".join(metadata_values["rights"])
            for marker in ("Habring—CC BY 4.0", "Becker/Krock—Lisensi MIT", "lapisan asli edisi—CC BY-SA 4.0", "Tidak ada lisensi payung"):
                require(marker in rights, f"EPUB rights marker missing: {marker}", failures)
            required_accessibility = {
                ("schema:accessMode", "textual"),
                ("schema:accessMode", "visual"),
                ("schema:accessModeSufficient", "textual"),
                ("schema:accessibilityFeature", "MathML"),
                ("schema:accessibilityFeature", "readingOrder"),
                ("schema:accessibilityFeature", "structuralNavigation"),
                ("schema:accessibilityFeature", "tableOfContents"),
                ("schema:accessibilityFeature", "alternativeText"),
                ("schema:accessibilityHazard", "none"),
            }
            require(required_accessibility.issubset(set(properties)), "EPUB accessibility metadata is incomplete", failures)
            modified = [value for prop, value in properties if prop == "dcterms:modified"]
            require(modified == [FIXED_MODIFIED], f"EPUB modified timestamp mismatch: {modified}", failures)

        manifest_node = opf.find("opf:manifest", ns)
        require(manifest_node is not None, "EPUB manifest missing", failures)
        duplicate_manifest_ids: list[str] = []
        if manifest_node is not None:
            for item in manifest_node.findall("opf:item", ns):
                item_id = item.attrib.get("id", "")
                if item_id in manifest:
                    duplicate_manifest_ids.append(item_id)
                href = item.attrib.get("href", "")
                media_type = item.attrib.get("media-type", "")
                properties = item.attrib.get("properties", "")
                manifest[item_id] = (href, media_type, properties)
                target = resolve_member(rootfile, href)
                require(target in members, f"EPUB manifest target missing: {item_id} -> {href}", failures)
                if target in members:
                    manifest_members.add(target)
                if "nav" in properties.split():
                    nav_members.append(target)
                require("remote-resources" not in properties.split(), f"EPUB manifest declares remote resources: {item_id}", failures)
        require(not duplicate_manifest_ids, f"EPUB duplicate manifest IDs: {duplicate_manifest_ids}", failures)

        spine = opf.find("opf:spine", ns)
        require(spine is not None, "EPUB spine missing", failures)
        if spine is not None:
            for itemref in spine.findall("opf:itemref", ns):
                item_id = itemref.attrib.get("idref", "")
                spine_ids.append(item_id)
                require(item_id in manifest, f"EPUB spine id absent from manifest: {item_id}", failures)
        require(len(spine_ids) == len(set(spine_ids)), "EPUB spine repeats an idref", failures)
        allowed_unmanifested = {"mimetype", "META-INF/container.xml", rootfile, "META-INF/com.apple.ibooks.display-options.xml"}
        unmanifested = sorted(set(members) - manifest_members - allowed_unmanifested)
        require(not unmanifested, f"EPUB unmanifested resources: {unmanifested}", failures)

    require(len(nav_members) == 1, f"EPUB navigation document count is {len(nav_members)}", failures)
    xhtml_names = sorted(name for name in members if name.endswith(".xhtml"))
    xhtml_text = {name: members[name].decode("utf-8") for name in xhtml_names}
    all_xhtml = "\n".join(xhtml_text.values())
    ids_by_member: dict[str, set[str]] = {}
    global_id_counts: Counter[str] = Counter()
    heading_by_member: dict[str, dict[str, object]] = {}
    nonnav_members = [name for name in xhtml_names if name not in nav_members]
    for name, text in xhtml_text.items():
        opening = re.search(r"<html\b[^>]*>", text, flags=re.IGNORECASE)
        require(bool(opening and 'lang="id-ID"' in opening.group(0) and 'xml:lang="id-ID"' in opening.group(0)), f"EPUB XHTML language mismatch in {name}", failures)
        id_list = [html.unescape(value) for value in re.findall(r'\bid="([^"]+)"', text)]
        require(len(id_list) == len(set(id_list)), f"EPUB duplicate ID within {name}", failures)
        ids_by_member[name] = set(id_list)
        global_id_counts.update(id_list)
        heading_by_member[name] = heading_metrics(text)
        require(heading_by_member[name]["empty_count"] == 0, f"EPUB contains empty headings in {name}", failures)
        if name in nonnav_members:
            require(len(re.findall(r'<main\b[^>]*epub:type="bodymatter"', text, flags=re.IGNORECASE)) == 1, f"EPUB bodymatter main landmark count is not one in {name}", failures)
            require('<a class="skip-link" href="#main-content">' in text, f"EPUB skip link missing in {name}", failures)

    labels = source.get("normalized_labels", [])
    bad_labels = {label: global_id_counts.get(label, 0) for label in labels if global_id_counts.get(label, 0) != 1}
    require(not bad_labels, f"EPUB does not preserve each canonical label exactly once: {dict(list(bad_labels.items())[:20])}", failures)

    unresolved: list[str] = []
    external_runtime_dependencies: list[str] = []
    internal_link_count = 0
    image_count = 0
    image_alt_count = 0
    image_longdesc_count = 0
    media_hashes: list[str] = []
    for name, text in xhtml_text.items():
        for tag in re.findall(r"<img\b[^>]*>", text, flags=re.IGNORECASE):
            image_count += 1
            src_match = re.search(r'\bsrc="([^"]+)"', tag, flags=re.IGNORECASE)
            alt_match = re.search(r'\balt="([^"]*)"', tag, flags=re.IGNORECASE)
            desc_match = re.search(r'\baria-describedby="([^"]+)"', tag, flags=re.IGNORECASE)
            if alt_match and html.unescape(alt_match.group(1)).strip():
                image_alt_count += 1
            if desc_match and html.unescape(desc_match.group(1)) in ids_by_member[name]:
                image_longdesc_count += 1
            if src_match:
                target = resolve_member(name, html.unescape(src_match.group(1)))
                if target in members:
                    media_hashes.append(sha256_bytes(members[target]))
                else:
                    unresolved.append(f"{name}: image={src_match.group(1)}")
            else:
                unresolved.append(f"{name}: image missing src")
        for attribute, reference in re.findall(r'\b(href|src)="([^"]+)"', text, flags=re.IGNORECASE):
            reference = html.unescape(reference)
            parsed_reference = urlsplit(reference)
            if parsed_reference.scheme or reference.startswith("//"):
                if attribute == "src":
                    external_runtime_dependencies.append(f"{name}: {attribute}={reference}")
                continue
            target = resolve_member(name, reference)
            if parsed_reference.path and target not in members:
                unresolved.append(f"{name}: {attribute}={reference}")
                continue
            if parsed_reference.fragment:
                target_member = target if parsed_reference.path else name
                fragment = unquote(parsed_reference.fragment)
                if target_member not in ids_by_member or fragment not in ids_by_member[target_member]:
                    unresolved.append(f"{name}: missing fragment {reference}")
                else:
                    internal_link_count += 1
        for tag, attribute in (("link", "href"), ("object", "data"), ("iframe", "src")):
            for reference in re.findall(
                rf"<{tag}\b[^>]*\b{attribute}=\"([^\"]+)\"",
                text,
                flags=re.IGNORECASE,
            ):
                parsed_reference = urlsplit(html.unescape(reference))
                if parsed_reference.scheme in {"http", "https"} or reference.startswith("//"):
                    external_runtime_dependencies.append(f"{name}: {tag}.{attribute}={reference}")
    require(not unresolved, f"EPUB unresolved internal references: {unresolved[:30]}", failures)
    require(not external_runtime_dependencies, f"EPUB XHTML has external runtime dependencies: {external_runtime_dependencies}", failures)
    require(image_count == 5, f"EPUB expected five raster uses, got {image_count}", failures)
    require(image_alt_count == image_count, f"EPUB image alt coverage is {image_alt_count}/{image_count}", failures)
    require(image_longdesc_count == image_count, f"EPUB image long-description coverage is {image_longdesc_count}/{image_count}", failures)
    require(Counter(media_hashes) == Counter(image_hashes.values()), "EPUB raster bytes do not match the five admitted source images exactly once", failures)

    navigation_link_count = 0
    landmark_nav_count = 0
    nav_unresolved: list[str] = []
    if len(nav_members) == 1 and nav_members[0] in parsed:
        nav_name = nav_members[0]
        nav_root = parsed[nav_name]
        nsx = {"x": "http://www.w3.org/1999/xhtml"}
        navs = nav_root.findall(".//x:nav", nsx)
        toc = [node for node in navs if node.attrib.get("{http://www.idpf.org/2007/ops}type") == "toc"]
        landmarks = [node for node in navs if node.attrib.get("{http://www.idpf.org/2007/ops}type") == "landmarks"]
        require(len(toc) == 1, f"EPUB TOC nav count is {len(toc)}", failures)
        require(len(landmarks) == 1, f"EPUB landmarks nav count is {len(landmarks)}", failures)
        landmark_nav_count = len(landmarks)
        if toc:
            anchors = toc[0].findall(".//x:a", nsx)
            navigation_link_count = len(anchors)
            for anchor in anchors:
                href = anchor.attrib.get("href", "")
                target = resolve_member(nav_name, href)
                parsed_href = urlsplit(href)
                if target not in members:
                    nav_unresolved.append(href)
                elif parsed_href.fragment and unquote(parsed_href.fragment) not in ids_by_member.get(target, set()):
                    nav_unresolved.append(href)
        require(navigation_link_count >= 75, f"EPUB TOC has too few links: {navigation_link_count}", failures)
        require(not nav_unresolved, f"EPUB navigation has unresolved targets: {nav_unresolved[:20]}", failures)

    metrics = math_metrics(all_xhtml)
    require(metrics["mathml_count"] == 4535, f"EPUB MathML count changed: {metrics}", failures)
    require(metrics["mathml_namespace_count"] == metrics["mathml_count"], f"EPUB contains non-native/unnamespaced MathML: {metrics}", failures)
    require(metrics["tex_annotation_count"] == metrics["mathml_count"], f"EPUB MathML/TeX annotation mismatch: {metrics}", failures)
    require(metrics["display_mathml_count"] == 729, f"EPUB display MathML count changed: {metrics}", failures)
    require(not re.search(r"mathjax|katex", all_xhtml, flags=re.IGNORECASE), "EPUB contains a MathJax/KaTeX runtime surface", failures)
    require(r"0=\eta g+\eta s^+" in all_xhtml, "EPUB does not contain the stabilized +\\eta TeX annotation", failures)
    math_manifest_failures: list[str] = []
    for item_id, (href, _media_type, properties) in manifest.items():
        member = resolve_member(rootfile, href)
        if member in xhtml_text and "<math" in xhtml_text[member] and "mathml" not in properties.split():
            math_manifest_failures.append(f"{item_id}:{member}")
    require(not math_manifest_failures, f"EPUB MathML documents lack manifest property: {math_manifest_failures}", failures)

    plain = strip_markup(all_xhtml)
    marker_positions, missing_markers = ordered_positions(plain, ORDER_MARKERS)
    require(not missing_markers, f"EPUB semantic order markers missing/out of order: {missing_markers}", failures)
    spine_members = [resolve_member(rootfile, manifest[item_id][0]) for item_id in spine_ids if item_id in manifest]
    require(all(member in xhtml_text for member in spine_members), f"EPUB spine contains non-XHTML/missing members: {spine_members}", failures)
    spine_text = "\n".join(xhtml_text.get(member, "") for member in spine_members)
    first_positions = [spine_text.find(f'id="{label}"') for label in source.get("first_labels", [])]
    require(all(position >= 0 for position in first_positions), "EPUB spine misses one or more source order sentinels", failures)
    require(first_positions == sorted(first_positions), "EPUB spine does not preserve canonical source body/module order", failures)

    css_members = [resolve_member(rootfile, href) for href, media_type, _properties in manifest.values() if media_type == "text/css"]
    css_text = "\n".join(members[name].decode("utf-8") for name in css_members if name in members)
    math_rule = css_rule(css_text, 'math[display="block"]')
    table_rule = css_rule(css_text, "table")
    image_rule = css_rule(css_text, "img")
    static_reflow = {
        "narrow_breakpoint_36em": bool(re.search(r"@media\s*\(max-width\s*:\s*36em\)", css_text)),
        "display_math_local_scroll": declaration_has(math_rule, "max-width", r"100%") and declaration_has(math_rule, "overflow-x", r"auto"),
        "table_and_pre_local_scroll": declaration_has(table_rule, "max-width", r"100%") and declaration_has(table_rule, "overflow-x", r"auto"),
        "images_fluid": declaration_has(image_rule, "max-width", r"100%") and declaration_has(image_rule, "height", r"auto"),
    }
    require(all(static_reflow.values()), f"EPUB static reflow contract incomplete: {static_reflow}", failures)
    require(all(not pattern.search(text) for pattern in PROFILE_PATTERNS for text in xhtml_text.values()), "EPUB contains a local profile/path locator", failures)

    epubcheck = run_epubcheck(failures, limitations)
    return {
        **current,
        "zip": {
            "entry_count": len(infos),
            "crc_clean": bad_crc is None,
            "mimetype_first": bool(infos) and infos[0].filename == "mimetype",
            "mimetype_stored": bool(infos) and infos[0].compress_type == zipfile.ZIP_STORED,
            "mimetype_extra_field_empty": bool(infos) and infos[0].extra == b"",
            "fixed_timestamps": all(info.date_time == ZIP_EPOCH for info in infos),
            "duplicate_member_count": len(names) - len(set(names)),
            "unsafe_members": unsafe,
        },
        "rootfile": rootfile,
        "manifest_item_count": len(manifest),
        "spine_item_count": len(spine_ids),
        "spine_members": spine_members,
        "xhtml_member_count": len(xhtml_names),
        "xml_member_count": len(xml_names),
        "navigation_document_count": len(nav_members),
        "navigation_link_count": navigation_link_count,
        "landmarks_nav_count": landmark_nav_count,
        "unresolved_navigation_targets": nav_unresolved,
        "headings_by_member": heading_by_member,
        "source_label_count": len(labels),
        "source_labels_preserved_exactly_once": len(labels) - len(bad_labels),
        "canonical_order_marker_count": len(marker_positions) - len(missing_markers),
        "source_order_sentinel_count": len(first_positions),
        "internal_link_count": internal_link_count,
        "unresolved_internal_references": unresolved,
        "image_count": image_count,
        "nonempty_alt_count": image_alt_count,
        "long_description_count": image_longdesc_count,
        "media_source_image_hashes": media_hashes,
        "math": metrics,
        "metadata": metadata_values,
        "static_reflow": static_reflow,
        "external_runtime_dependencies": external_runtime_dependencies,
        "stabilized_module_05_correction_present": r"0=\eta g+\eta s^+" in all_xhtml,
        "epubcheck": epubcheck,
    }


def executable_version(command: list[str]) -> dict[str, object]:
    try:
        completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"available": False, "error": str(exc)}
    lines = (completed.stdout + completed.stderr).splitlines()
    return {"available": completed.returncode == 0, "exit_code": completed.returncode, "first_line": lines[0] if lines else ""}


def main() -> None:
    failures: list[str] = []
    limitations: list[str] = []

    for path in (BUILD_SCRIPT, PRIMARY_VERIFIER, BUILD_REPORT, PRIMARY_REPORT):
        require(path.is_file(), f"required audit input missing: {path.relative_to(ROOT).as_posix()}", failures)

    build_report = load_json(BUILD_REPORT, failures) if BUILD_REPORT.is_file() else {}
    primary_report = load_json(PRIMARY_REPORT, failures) if PRIMARY_REPORT.is_file() else {}
    require(build_report.get("schema") == "o015-integrated-readers-build-v1", "unexpected integrated build report schema", failures)
    require(build_report.get("result") == "pass", "integrated build report is not pass", failures)
    require(primary_report.get("schema") == "o015-integrated-readers-validation-v1", "unexpected primary validation report schema", failures)
    require(primary_report.get("result") == "pass", "primary integrated validation report is not pass", failures)
    require(primary_report.get("failures") == [], "primary integrated validation report contains failures", failures)

    source = source_contract(build_report, failures)
    deterministic = deterministic_evidence(build_report, failures)
    images = source_image_hashes(failures)
    html_result = validate_html(source, build_report, primary_report, images, failures)
    epub_result = validate_epub(source, build_report, primary_report, images, failures, limitations)

    # Browser-backed measurements were attempted by the orchestrating audit, but
    # the in-app browser rejected the local file URL under its URL safety policy
    # and explicitly prohibited alternate/workaround browser surfaces.  Static
    # responsive contracts are checked above; rendered geometry is not claimed.
    viewport_limitation = (
        "Rendered desktop/tablet/phone geometry was not measured: the in-app browser "
        "URL safety policy rejected the local file URL and prohibited workaround or "
        "alternate browser surfaces. Static responsive/overflow contracts passed."
    )
    limitations.append(viewport_limitation)
    rendered_viewports = {
        "performed": False,
        "profiles": list(VIEWPORT_PROFILES),
        "page_overflow_measurement": "not_performed",
        "wide_math_scroll_measurement": "not_performed",
        "static_html_contract_passed": bool(html_result.get("static_reflow")) and all(html_result.get("static_reflow", {}).values()),
        "static_epub_contract_passed": bool(epub_result.get("static_reflow")) and all(epub_result.get("static_reflow", {}).values()),
        "reason": viewport_limitation,
    }

    script_facts = {path.name: fact(path) for path in (BUILD_SCRIPT, PRIMARY_VERIFIER) if path.is_file()}
    report_facts = {path.name: fact(path) for path in (BUILD_REPORT, PRIMARY_REPORT) if path.is_file()}
    source_receipt = dict(source)
    source_receipt.pop("normalized_labels", None)

    result = "fail" if failures else "pass_with_limitations" if limitations else "pass"
    receipt = {
        "schema": "o015-integrated-reflow-independent-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": result,
        "scope": "Independent offline binding and structural/reflow audit of the integrated HTML and EPUB readers",
        "authority": {
            "production_scripts": script_facts,
            "production_reports": report_facts,
            "build_report_schema": build_report.get("schema"),
            "build_report_result": build_report.get("result"),
            "primary_validation_schema": primary_report.get("schema"),
            "primary_validation_result": primary_report.get("result"),
        },
        "toolchain": {
            "python": sys.version.split()[0],
            "pandoc": executable_version(["pandoc", "--version"]),
            "java": executable_version(["java", "-version"]),
        },
        "source_contract": source_receipt,
        "deterministic_build": deterministic,
        "html": html_result,
        "epub": epub_result,
        "rendered_viewports": rendered_viewports,
        "failures": failures,
        "limitations": limitations,
    }
    RECEIPT.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
