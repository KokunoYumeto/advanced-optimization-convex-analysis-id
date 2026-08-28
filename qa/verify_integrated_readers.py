#!/usr/bin/env python3
"""Deep deterministic QA for the integrated O015/D90 HTML and EPUB readers."""

from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

import build_integrated_readers as build


ROOT = build.ROOT
HTML_PATH = build.OUTPUT_HTML
EPUB_PATH = build.OUTPUT_EPUB
REPORT_PATH = ROOT / "qa" / "INTEGRATED_READERS_VALIDATION.json"
EPUBCHECK_JAR = ROOT / "tmp" / "tools" / "epubcheck-5.3.0" / "epubcheck.jar"

EXPECTED_ORDER_MARKERS = (
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

PROFILE_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/](?:Users|Documents|AppData)[\\/]", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"/Users/", re.IGNORECASE),
    re.compile(r"\\Users\\", re.IGNORECASE),
)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def ordered_positions(text: str, markers: tuple[str, ...]) -> tuple[list[int], list[str]]:
    positions: list[int] = []
    missing: list[str] = []
    cursor = 0
    for marker in markers:
        position = text.find(marker, cursor)
        if position < 0:
            missing.append(marker)
            positions.append(-1)
        else:
            positions.append(position)
            cursor = position + len(marker)
    return positions, missing


def source_contract() -> dict[str, object]:
    info = build.collect_source_info()
    labels: list[str] = info["labels"]  # type: ignore[assignment]
    normalized = [build.epub_fragment(label) for label in labels]
    if len(normalized) != len(set(normalized)):
        collisions = [key for key, count in Counter(normalized).items() if count > 1]
        raise RuntimeError(f"Label normalization collisions: {collisions}")
    first_labels = [
        info["first_label_by_file"][path.relative_to(ROOT).as_posix()]
        for path in build.SOURCE_PATHS
        if path.relative_to(ROOT).as_posix() in info["first_label_by_file"]
    ]
    return {
        "labels": normalized,
        "raw_labels": labels,
        "first_labels": [build.epub_fragment(label) for label in first_labels],
        "environment_counts": info["environment_counts"],
        "file_count": len(build.SOURCE_PATHS),
    }


def strip_markup(text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text))


def environment_counts(text: str) -> dict[str, int]:
    return {
        env: len(re.findall(rf'class="[^"]*\b{env}\b[^"]*"', text, re.IGNORECASE))
        for env in build.ENVIRONMENTS
    }


def math_metrics(text: str) -> dict[str, int]:
    math_count = len(re.findall(r"<math\b", text, re.IGNORECASE))
    annotation_count = len(
        re.findall(
            r'<annotation\b[^>]*encoding="application/x-tex"',
            text,
            re.IGNORECASE,
        )
    )
    display_count = len(re.findall(r'<math\b[^>]*display="block"', text, re.IGNORECASE))
    return {
        "mathml_count": math_count,
        "tex_annotation_count": annotation_count,
        "display_mathml_count": display_count,
    }


def raw_tex_outside_annotations(text: str) -> list[str]:
    stripped = re.sub(
        r"<annotation\b[^>]*>.*?</annotation>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    markers = (
        r"\begin{tikzpicture}",
        r"\end{tikzpicture}",
        r"\includegraphics",
        r"\begin{psmallmatrix}",
        r"\end{psmallmatrix}",
        r"\resizebox",
        r"\Needspace",
        r"\gls{",
    )
    return [marker for marker in markers if marker in stripped]


def validate_browser_metrics(path: Path | None, failures: list[str]) -> dict[str, object]:
    if path is None:
        return {"performed": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("schema") == "o015-integrated-browser-qa-v1", "unexpected browser QA schema", failures)
    for name, minimum_ratio in (("desktop", 0.72), ("mobile", 0.94)):
        view = data.get(name, {})
        require(not view.get("horizontal_overflow", True), f"{name} viewport has horizontal page overflow", failures)
        require(view.get("main_width_ratio", 0) >= minimum_ratio, f"{name} main content does not fill the viewport", failures)
        require(abs(view.get("left_gutter", 999) - view.get("right_gutter", -999)) <= 2.5, f"{name} main content is not centered", failures)
        require(view.get("main_landmarks") == 1, f"{name} must expose one main landmark", failures)
        require(view.get("toc_landmarks") == 1, f"{name} must expose one TOC landmark", failures)
        require(view.get("skip_target_valid") is True, f"{name} skip link target is invalid", failures)
        require(view.get("mathml_count", 0) >= 600, f"{name} browser rendered implausibly few MathML nodes", failures)
    require(data.get("keyboard", {}).get("first_focus_is_skip_link") is True, "keyboard Tab did not reveal/focus the skip link", failures)
    require(data.get("keyboard", {}).get("skip_link_visible") is True, "focused skip link is not visible", failures)
    return data


def validate_html(contract: dict[str, object], failures: list[str]) -> dict[str, object]:
    if not HTML_PATH.is_file():
        failures.append(f"missing HTML artifact: {HTML_PATH}")
        return {}
    text = HTML_PATH.read_text(encoding="utf-8")
    plain = strip_markup(text)
    ids = re.findall(r'\bid="([^"]+)"', text)
    id_counts = Counter(html.unescape(identifier) for identifier in ids)
    duplicate_ids = sorted(key for key, count in id_counts.items() if count > 1)
    labels: list[str] = contract["labels"]  # type: ignore[assignment]
    bad_labels = {label: id_counts.get(label, 0) for label in labels if id_counts.get(label, 0) != 1}
    hrefs = [html.unescape(value) for value in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', text, re.IGNORECASE)]
    missing_fragments = sorted(
        {
            unquote(urlsplit(reference).fragment)
            for reference in hrefs
            if not urlsplit(reference).scheme
            and urlsplit(reference).fragment
            and unquote(urlsplit(reference).fragment) not in id_counts
        }
    )
    images = re.findall(r"<img\b[^>]*>", text, re.IGNORECASE)
    image_failures = []
    longdesc_targets = set(re.findall(r'class="long-description"\s+id="([^"]+)"', text, re.IGNORECASE))
    for tag in images:
        src = re.search(r'\bsrc="([^"]+)"', tag, re.IGNORECASE)
        alt = re.search(r'\balt="([^"]*)"', tag, re.IGNORECASE)
        desc = re.search(r'\baria-describedby="([^"]+)"', tag, re.IGNORECASE)
        if not src or not html.unescape(src.group(1)).startswith("data:image/png;base64,"):
            image_failures.append("nonembedded/non-PNG image")
        if not alt or not html.unescape(alt.group(1)).strip():
            image_failures.append("missing image alt")
        if not desc or html.unescape(desc.group(1)) not in longdesc_targets:
            image_failures.append("missing image long-description target")
    metrics = math_metrics(text)
    output_env = environment_counts(text)
    marker_positions, missing_markers = ordered_positions(plain, EXPECTED_ORDER_MARKERS)
    source_order_positions = [text.find(f'id="{label}"') for label in contract["first_labels"]]  # type: ignore[index]

    require(text.lstrip().lower().startswith("<!doctype html>"), "HTML5 doctype missing", failures)
    require(bool(re.search(r'<html\b[^>]*\blang="id-ID"', text, re.IGNORECASE)), "HTML language is not id-ID", failures)
    require('name="viewport"' in text, "HTML viewport metadata missing", failures)
    require(len(re.findall(r'<header\b[^>]*role="banner"', text, re.IGNORECASE)) == 1, "HTML banner landmark missing", failures)
    require(len(re.findall(r'<nav\b[^>]*role="doc-toc"', text, re.IGNORECASE)) == 1, "HTML TOC landmark missing", failures)
    require(len(re.findall(r'<main\b[^>]*id="main-content"', text, re.IGNORECASE)) == 1, "HTML main landmark missing", failures)
    require(len(re.findall(r'<footer\b[^>]*role="contentinfo"', text, re.IGNORECASE)) == 1, "HTML contentinfo landmark missing", failures)
    require('<a class="skip-link" href="#main-content">' in text, "HTML keyboard skip link missing", failures)
    require(":focus-visible" in text and ".skip-link:focus" in text, "HTML visible-focus styling missing", failures)
    require("@media (max-width: 48rem)" in text, "HTML narrow-screen reflow rule missing", failures)
    require("--content-max: 96rem" in text, "HTML wide page-filling layout contract missing", failures)
    require(not duplicate_ids, f"HTML duplicate IDs: {duplicate_ids[:20]}", failures)
    require(not bad_labels, f"HTML source labels not preserved exactly once: {dict(list(bad_labels.items())[:20])}", failures)
    require(not missing_fragments, f"HTML unresolved internal fragments: {missing_fragments[:20]}", failures)
    require(len(images) == 5, f"HTML expected five source raster uses, got {len(images)}", failures)
    require(not image_failures, f"HTML image accessibility failures: {image_failures}", failures)
    require(metrics["mathml_count"] >= 600, f"HTML has implausibly few MathML surfaces: {metrics}", failures)
    require(metrics["tex_annotation_count"] == metrics["mathml_count"], f"HTML MathML/TeX annotation mismatch: {metrics}", failures)
    require(metrics["display_mathml_count"] >= 300, f"HTML has implausibly few display formulas: {metrics}", failures)
    require(output_env == contract["environment_counts"], f"HTML environment topology mismatch: source={contract['environment_counts']} output={output_env}", failures)
    require(not missing_markers, f"HTML canonical reading-order markers missing/out of order: {missing_markers}", failures)
    require(all(position >= 0 for position in source_order_positions), "HTML is missing one or more first-label order sentinels", failures)
    require(source_order_positions == sorted(source_order_positions), "HTML canonical source order is not preserved", failures)
    require(not raw_tex_outside_annotations(text), f"HTML raw TeX leak: {raw_tex_outside_annotations(text)}", failures)
    require(all(not pattern.search(text) for pattern in PROFILE_PATTERNS), "HTML contains a local profile/path locator", failures)
    require(not re.search(r"\bTTP\b|Translation and Transcription Project", plain), "HTML contains forbidden umbrella prose", failures)
    for marker in ("CC BY 4.0", "Lisensi MIT", "CC BY-SA 4.0", "Tidak ada klaim lisensi payung", "bukan edisi resmi", "OpenAI Codex gpt-5.6-sol, Ultra"):
        require(marker in plain, f"HTML rights/provenance marker missing: {marker}", failures)
    require(not re.search(r'<(?:script|link)\b[^>]*(?:src|href)="https?://', text, re.IGNORECASE), "HTML has an external runtime resource dependency", failures)
    return {
        "path": HTML_PATH.relative_to(ROOT).as_posix(),
        "bytes": HTML_PATH.stat().st_size,
        "sha256": build.sha256(HTML_PATH),
        "id_count": len(ids),
        "source_label_count": len(labels),
        "preserved_source_label_count": len(labels) - len(bad_labels),
        "internal_link_count": sum(1 for href in hrefs if urlsplit(href).fragment),
        "unresolved_internal_fragments": missing_fragments,
        "image_count": len(images),
        "long_description_count": len(longdesc_targets),
        "environment_counts": output_env,
        "canonical_order_marker_count": len(marker_positions) - len(missing_markers),
        "source_order_sentinel_count": len(source_order_positions),
        **metrics,
    }


def member_for_href(base: str, reference: str) -> str:
    parsed = urlsplit(html.unescape(reference))
    if parsed.scheme or reference.startswith("//"):
        return ""
    if not parsed.path:
        return base
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), unquote(parsed.path)))


def run_epubcheck(failures: list[str]) -> dict[str, object]:
    if not EPUBCHECK_JAR.is_file():
        failures.append(f"EPUBCheck jar missing: {EPUBCHECK_JAR}")
        return {"performed": False}
    completed = subprocess.run(
        ["java", "-jar", str(EPUBCHECK_JAR), str(EPUB_PATH)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = completed.stdout + completed.stderr
    output = output.replace(str(ROOT), "<PROJECT_ROOT>")
    output = output.replace(ROOT.as_posix(), "<PROJECT_ROOT>")
    if completed.returncode:
        failures.append(f"EPUBCheck failed with exit {completed.returncode}: {output[-3000:]}")
    return {
        "performed": True,
        "jar_sha256": build.sha256(EPUBCHECK_JAR),
        "exit_code": completed.returncode,
        "message_count": len([line for line in output.splitlines() if line.strip()]),
        "output": output.strip(),
    }


def validate_epub(contract: dict[str, object], failures: list[str]) -> dict[str, object]:
    if not EPUB_PATH.is_file():
        failures.append(f"missing EPUB artifact: {EPUB_PATH}")
        return {}
    with zipfile.ZipFile(EPUB_PATH) as archive:
        bad_member = archive.testzip()
        infos = archive.infolist()
        names = [info.filename for info in infos]
        members = {name: archive.read(name) for name in names if not name.endswith("/")}
    require(bad_member is None, f"EPUB ZIP CRC failure: {bad_member}", failures)
    require(bool(infos) and infos[0].filename == "mimetype", "EPUB mimetype is not first", failures)
    require(bool(infos) and infos[0].compress_type == zipfile.ZIP_STORED, "EPUB mimetype is compressed", failures)
    require(members.get("mimetype") == b"application/epub+zip", "EPUB mimetype payload invalid", failures)
    require(len(names) == len(set(names)), "EPUB duplicate ZIP member names", failures)
    require(all(info.date_time == build.ZIP_EPOCH for info in infos), "EPUB ZIP timestamps are not normalized", failures)
    unsafe = [name for name in names if name.startswith(("/", "\\")) or ".." in PurePosixPath(name).parts]
    require(not unsafe, f"EPUB unsafe member names: {unsafe}", failures)

    xml_names = [name for name in members if PurePosixPath(name).suffix.lower() in {".xml", ".opf", ".ncx", ".xhtml"}]
    parsed: dict[str, ET.Element] = {}
    parse_failures = []
    for name in xml_names:
        try:
            parsed[name] = ET.fromstring(members[name])
        except ET.ParseError as exc:
            parse_failures.append(f"{name}: {exc}")
    require(not parse_failures, f"EPUB XML parse failures: {parse_failures}", failures)

    container_name = "META-INF/container.xml"
    require(container_name in parsed, "EPUB container.xml missing", failures)
    rootfile = ""
    if container_name in parsed:
        rootfiles = parsed[container_name].findall(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
        require(len(rootfiles) == 1, f"EPUB container rootfile count is {len(rootfiles)}", failures)
        if len(rootfiles) == 1:
            rootfile = rootfiles[0].attrib.get("full-path", "")
            require(rootfile in parsed, f"EPUB OPF rootfile missing: {rootfile}", failures)

    manifest: dict[str, tuple[str, str, str]] = {}
    manifest_members: set[str] = set()
    spine_ids: list[str] = []
    nav_members: list[str] = []
    metadata_values: dict[str, object] = {}
    if rootfile in parsed:
        opf = parsed[rootfile]
        ns = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
        require(opf.attrib.get("version", "").startswith("3"), f"EPUB OPF is not version 3: {opf.attrib.get('version')}", failures)
        metadata = opf.find("opf:metadata", ns)
        require(metadata is not None, "EPUB OPF metadata missing", failures)
        if metadata is not None:
            def dc(local: str) -> list[str]:
                return ["".join(node.itertext()).strip() for node in metadata.findall(f"dc:{local}", ns)]

            title = dc("title")
            language = dc("language")
            identifiers = dc("identifier")
            rights = " ".join(dc("rights"))
            creators = dc("creator")
            properties = [
                (node.attrib.get("property", ""), "".join(node.itertext()).strip())
                for node in metadata.findall("opf:meta", ns)
            ]
            metadata_values = {
                "title": title,
                "language": language,
                "identifiers": identifiers,
                "rights": rights,
                "creators": creators,
                "properties": properties,
            }
            require(title == [build.TITLE], f"EPUB title mismatch: {title}", failures)
            require(language == ["id-ID"], f"EPUB language mismatch: {language}", failures)
            require(build.IDENTIFIER in identifiers, "EPUB fixed identifier missing", failures)
            for marker in ("Habring—CC BY 4.0", "Becker/Krock—Lisensi MIT", "lapisan asli edisi—CC BY-SA 4.0", "Tidak ada lisensi payung"):
                require(marker in rights, f"EPUB rights marker missing: {marker}", failures)
            required_accessibility = {
                ("schema:accessMode", "textual"),
                ("schema:accessMode", "visual"),
                ("schema:accessModeSufficient", "textual"),
                ("schema:accessibilityFeature", "MathML"),
                ("schema:accessibilityFeature", "structuralNavigation"),
                ("schema:accessibilityFeature", "alternativeText"),
                ("schema:accessibilityHazard", "none"),
            }
            require(required_accessibility.issubset(set(properties)), "EPUB accessibility metadata incomplete", failures)
            modified = [value for prop, value in properties if prop == "dcterms:modified"]
            require(modified == [build.FIXED_MODIFIED], f"EPUB modified timestamp mismatch: {modified}", failures)
        manifest_node = opf.find("opf:manifest", ns)
        require(manifest_node is not None, "EPUB OPF manifest missing", failures)
        if manifest_node is not None:
            for item in manifest_node.findall("opf:item", ns):
                item_id = item.attrib.get("id", "")
                href = item.attrib.get("href", "")
                media = item.attrib.get("media-type", "")
                properties = item.attrib.get("properties", "")
                manifest[item_id] = (href, media, properties)
                target = member_for_href(rootfile, href)
                require(target in members, f"EPUB manifest target missing: {item_id} -> {href}", failures)
                if target in members:
                    manifest_members.add(target)
                if "nav" in properties.split():
                    nav_members.append(target)
        spine = opf.find("opf:spine", ns)
        require(spine is not None, "EPUB OPF spine missing", failures)
        if spine is not None:
            for itemref in spine.findall("opf:itemref", ns):
                item_id = itemref.attrib.get("idref", "")
                spine_ids.append(item_id)
                require(item_id in manifest, f"EPUB spine id absent from manifest: {item_id}", failures)
        allowed_unmanifested = {"mimetype", "META-INF/container.xml", rootfile, "META-INF/com.apple.ibooks.display-options.xml"}
        unmanifested = sorted(set(members) - manifest_members - allowed_unmanifested)
        require(not unmanifested, f"EPUB unmanifested resources: {unmanifested}", failures)

    require(len(nav_members) == 1, f"EPUB navigation document count is {len(nav_members)}", failures)
    xhtml_names = sorted(name for name in members if name.endswith(".xhtml"))
    xhtml_text = {name: members[name].decode("utf-8") for name in xhtml_names}
    all_xhtml = "\n".join(xhtml_text.values())
    plain = strip_markup(all_xhtml)
    metrics = math_metrics(all_xhtml)
    output_env = environment_counts(all_xhtml)

    ids_by_member: dict[str, set[str]] = {}
    global_id_counts: Counter[str] = Counter()
    nonnav_members = [name for name in xhtml_names if name not in nav_members]
    for name, text in xhtml_text.items():
        opening = re.search(r"<html\b[^>]*>", text, re.IGNORECASE)
        require(bool(opening and 'lang="id-ID"' in opening.group(0) and 'xml:lang="id-ID"' in opening.group(0)), f"EPUB XHTML language mismatch in {name}", failures)
        identifiers = set(re.findall(r'\bid="([^"]+)"', text))
        id_list = re.findall(r'\bid="([^"]+)"', text)
        require(len(id_list) == len(identifiers), f"EPUB duplicate ID within {name}", failures)
        ids_by_member[name] = identifiers
        global_id_counts.update(identifiers)
        if name in nonnav_members:
            require(len(re.findall(r'<main\b[^>]*epub:type="bodymatter"', text, re.IGNORECASE)) == 1, f"EPUB main landmark missing in {name}", failures)
            require('<a class="skip-link" href="#main-content">' in text, f"EPUB skip link missing in {name}", failures)

    labels: list[str] = contract["labels"]  # type: ignore[assignment]
    bad_labels = {label: global_id_counts.get(label, 0) for label in labels if global_id_counts.get(label, 0) != 1}
    require(not bad_labels, f"EPUB source labels not preserved exactly once: {dict(list(bad_labels.items())[:20])}", failures)

    unresolved = []
    internal_link_count = 0
    image_count = 0
    image_alt_count = 0
    image_longdesc_count = 0
    for name, text in xhtml_text.items():
        for tag in re.findall(r"<img\b[^>]*>", text, re.IGNORECASE):
            image_count += 1
            src = re.search(r'\bsrc="([^"]+)"', tag, re.IGNORECASE)
            alt = re.search(r'\balt="([^"]*)"', tag, re.IGNORECASE)
            desc = re.search(r'\baria-describedby="([^"]+)"', tag, re.IGNORECASE)
            if alt and html.unescape(alt.group(1)).strip():
                image_alt_count += 1
            if desc and html.unescape(desc.group(1)) in ids_by_member[name]:
                image_longdesc_count += 1
            if not src or member_for_href(name, html.unescape(src.group(1))) not in members:
                unresolved.append(f"{name}: image {src.group(1) if src else '<missing>'}")
        for attribute, reference in re.findall(r'\b(href|src)="([^"]+)"', text, re.IGNORECASE):
            reference = html.unescape(reference)
            parsed_ref = urlsplit(reference)
            if parsed_ref.scheme or reference.startswith("//"):
                continue
            target = member_for_href(name, reference)
            if parsed_ref.path and target not in members:
                unresolved.append(f"{name}: {attribute}={reference}")
                continue
            if parsed_ref.fragment:
                fragment_member = target if parsed_ref.path else name
                fragment = unquote(parsed_ref.fragment)
                if fragment_member not in ids_by_member or fragment not in ids_by_member[fragment_member]:
                    unresolved.append(f"{name}: missing fragment {reference}")
                else:
                    internal_link_count += 1
    require(not unresolved, f"EPUB unresolved internal references: {unresolved[:30]}", failures)
    require(image_count == 5, f"EPUB expected five raster uses, got {image_count}", failures)
    require(image_alt_count == image_count, f"EPUB image alt coverage {image_alt_count}/{image_count}", failures)
    require(image_longdesc_count == image_count, f"EPUB image long-description coverage {image_longdesc_count}/{image_count}", failures)

    nav_link_count = 0
    landmark_count = 0
    if len(nav_members) == 1 and nav_members[0] in parsed:
        nav_root = parsed[nav_members[0]]
        nsx = {"x": "http://www.w3.org/1999/xhtml"}
        navs = nav_root.findall(".//x:nav", nsx)
        toc = [node for node in navs if node.attrib.get("{http://www.idpf.org/2007/ops}type") == "toc"]
        landmarks = [node for node in navs if node.attrib.get("{http://www.idpf.org/2007/ops}type") == "landmarks"]
        require(len(toc) == 1, f"EPUB TOC nav count is {len(toc)}", failures)
        require(len(landmarks) == 1, f"EPUB landmarks nav count is {len(landmarks)}", failures)
        if toc:
            nav_link_count = len(toc[0].findall(".//x:a", nsx))
        landmark_count = len(landmarks)
        require(nav_link_count >= 25, f"EPUB TOC has too few links: {nav_link_count}", failures)

    marker_positions, missing_markers = ordered_positions(plain, EXPECTED_ORDER_MARKERS)
    require(not missing_markers, f"EPUB canonical reading-order markers missing/out of order: {missing_markers}", failures)
    spine_members = [member_for_href(rootfile, manifest[item_id][0]) for item_id in spine_ids if item_id in manifest]
    spine_text = "\n".join(xhtml_text.get(name, "") for name in spine_members)
    source_positions = [spine_text.find(f'id="{label}"') for label in contract["first_labels"]]  # type: ignore[index]
    require(all(position >= 0 for position in source_positions), "EPUB spine is missing first-label order sentinels", failures)
    require(source_positions == sorted(source_positions), "EPUB spine does not preserve canonical source order", failures)
    require(metrics["mathml_count"] >= 600, f"EPUB has implausibly few MathML surfaces: {metrics}", failures)
    require(metrics["tex_annotation_count"] == metrics["mathml_count"], f"EPUB MathML/TeX annotation mismatch: {metrics}", failures)
    require(metrics["display_mathml_count"] >= 300, f"EPUB has implausibly few display formulas: {metrics}", failures)
    require(output_env == contract["environment_counts"], f"EPUB environment topology mismatch: source={contract['environment_counts']} output={output_env}", failures)
    require(not raw_tex_outside_annotations(all_xhtml), f"EPUB raw TeX leak: {raw_tex_outside_annotations(all_xhtml)}", failures)
    require(all(not pattern.search(text) for pattern in PROFILE_PATTERNS for text in xhtml_text.values()), "EPUB contains a local profile/path locator", failures)
    require(not re.search(r"\bTTP\b|Translation and Transcription Project", plain), "EPUB contains forbidden umbrella prose", failures)
    for marker in ("CC BY 4.0", "Lisensi MIT", "CC BY-SA 4.0", "Tidak ada klaim lisensi payung", "bukan edisi resmi", "OpenAI Codex gpt-5.6-sol, Ultra"):
        require(marker in plain, f"EPUB rights/provenance marker missing: {marker}", failures)

    math_manifest_failures = []
    for item_id, (href, _media, properties) in manifest.items():
        member = member_for_href(rootfile, href)
        if member in xhtml_text and "<math" in xhtml_text[member] and "mathml" not in properties.split():
            math_manifest_failures.append(member)
    require(not math_manifest_failures, f"EPUB MathML documents lack manifest property: {math_manifest_failures}", failures)
    epubcheck = run_epubcheck(failures)
    return {
        "path": EPUB_PATH.relative_to(ROOT).as_posix(),
        "bytes": EPUB_PATH.stat().st_size,
        "sha256": build.sha256(EPUB_PATH),
        "zip_entry_count": len(members),
        "xml_member_count": len(xml_names),
        "xhtml_member_count": len(xhtml_names),
        "manifest_item_count": len(manifest),
        "spine_item_count": len(spine_ids),
        "navigation_link_count": nav_link_count,
        "landmarks_nav_count": landmark_count,
        "source_label_count": len(labels),
        "preserved_source_label_count": len(labels) - len(bad_labels),
        "internal_link_count": internal_link_count,
        "unresolved_internal_references": unresolved,
        "image_count": image_count,
        "nonempty_image_alt_count": image_alt_count,
        "image_long_description_count": image_longdesc_count,
        "environment_counts": output_env,
        "canonical_order_marker_count": len(marker_positions) - len(missing_markers),
        "source_order_sentinel_count": len(source_positions),
        "metadata": metadata_values,
        "epubcheck": epubcheck,
        **metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser-metrics", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures: list[str] = []
    contract = source_contract()
    html_result = validate_html(contract, failures)
    epub_result = validate_epub(contract, failures)
    browser_result = validate_browser_metrics(args.browser_metrics, failures)
    report = {
        "schema": "o015-integrated-readers-validation-v1",
        "result": "pass" if not failures else "fail",
        "source_contract": {
            "file_count": contract["file_count"],
            "label_count": len(contract["labels"]),
            "environment_counts": contract["environment_counts"],
        },
        "html": html_result,
        "epub": epub_result,
        "browser": browser_result,
        "failures": failures,
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
