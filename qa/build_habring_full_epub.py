#!/usr/bin/env python3
"""Build and deeply validate a deterministic EPUB 3 Habring Chapters 1--9 reader."""

from __future__ import annotations

import hashlib
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source" / "id-ID"
TMP_DIR = ROOT / "tmp" / "habring-epub"
COMBINED_TEX = TMP_DIR / "D90-HAB-01-09-id.tex"
EPUB_CSS = TMP_DIR / "habring-epub.css"
RAW_EPUB = TMP_DIR / "D90-HAB-01-09-id.raw.epub"
FIRST_EPUB = TMP_DIR / "D90-HAB-01-09-id.first.epub"
SECOND_EPUB = TMP_DIR / "D90-HAB-01-09-id.second.epub"
OUTPUT_EPUB = (
    ROOT
    / "output"
    / "epub"
    / "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub"
)
REPORT_PATH = ROOT / "qa" / "HABRING_FULL_EPUB_BUILD.json"

CHAPTERS = [
    SOURCE_DIR / "habring-01-prasyarat-id.tex",
    SOURCE_DIR / "habring-02-konveksitas-id.tex",
    SOURCE_DIR / "habring-03-subgradien-id.tex",
    SOURCE_DIR / "habring-04-metode-subgradien-terproyeksi-id.tex",
    SOURCE_DIR / "habring-05-metode-gradien-proksimal-id.tex",
    SOURCE_DIR / "habring-06-akselerasi-id.tex",
    SOURCE_DIR / "habring-07-dualitas-id.tex",
    SOURCE_DIR / "habring-08-penurunan-gradien-stokastik-id.tex",
    SOURCE_DIR / "habring-09-transportasi-optimal-id.tex",
]

TITLE = "Optimisasi Konveks — Edisi Bahasa Indonesia"
IDENTIFIER = "urn:uuid:4c6d1b13-674d-5f27-91b1-9f401d8c8f90"
FIXED_MODIFIED = "2026-08-25T00:00:00Z"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

INTRO = r"""
\begin{quote}
\textbf{Status pembaca.} Edisi Bahasa Indonesia ini memuat terjemahan lengkap
sembilan bab dari Andreas Habring, \emph{Lecture Notes: Convex Optimization},
arXiv:2607.11664v1. Ini adalah karya turunan mandiri, bukan edisi resmi atau
dukungan penulis sumber maupun TU Graz. Rumus, bukti, latihan, gambar yang
diizinkan, dan urutan sumber dipertahankan; koreksi yang dapat ditentukan
ditandai dan direkam dalam ledger edisi.

Sumber dan terjemahan tersedia berdasarkan Creative Commons Attribution 4.0
International (CC BY 4.0). Provenans produksi: OpenAI Codex gpt-5.6-sol, Ultra,
atas instruksi pengguna repositori; seluruh kredit penulis dan sumber tetap
dipertahankan.
\end{quote}
"""

MATH_MACROS = r"""
\newcommand{\half}{\frac{1}{2}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\R}{\mathbb{R}}
\newcommand{\Rb}{\overline{\mathbb{R}}}
\newcommand{\bR}{\overline{\mathbb{R}}}
\newcommand{\F}{\mathbb{F}}
\newcommand{\1}{\mathbf{1}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\setto}{\rightrightarrows}
\newcommand{\equivalent}{\Leftrightarrow}
\newcommand{\eps}{\varepsilon}
\newcommand{\supp}{\operatorname{supp}}
\newcommand{\dom}{\operatorname{dom}}
\newcommand{\ker}{\operatorname{ker}}
\newcommand{\conv}{\operatorname{conv}}
\newcommand{\rg}{\operatorname{rg}}
\newcommand{\graph}{\operatorname{graph}}
\newcommand{\tr}{\operatorname{tr}}
\newcommand{\epi}{\operatorname{epi}}
\newcommand{\span}{\operatorname{span}}
\newcommand{\sign}{\operatorname{sign}}
\newcommand{\Id}{\operatorname{Id}}
\newcommand{\prox}{\operatorname{prox}}
\newcommand{\proj}{\operatorname{proj}}
\newcommand{\norm}[1]{\left\lVert #1\right\rVert}
\newcommand{\abs}[1]{\left|#1\right|}
\newcommand{\inner}[2]{\left\langle #1,#2\right\rangle}
\newcommand{\dual}[1]{\left\langle #1\right\rangle}
\newcommand{\setof}[2]{\left\{#1\;\middle|\;#2\right\}}
\newcommand{\wkto}{\rightharpoonup}
\newcommand{\Exp}{\mathbb{E}}
\newcommand{\Var}{\mathbb{V}}
\newcommand{\Cov}{\operatorname{Cov}}
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\emptyarg}{\,\cdot\,}
\newcommand{\dd}{\mathrm{d}}
\newcommand{\Oc}{\mathcal{O}}
\newcommand{\Lc}{\mathcal{L}}
\newcommand{\Gc}{\mathcal{G}}
\newcommand{\Ic}{\mathcal{I}}
\newcommand{\Pc}{\mathcal{P}}
\newcommand{\Mc}{\mathcal{M}}
\newcommand{\diag}{\operatorname{diag}}
"""

CSS = r"""
@namespace epub "http://www.idpf.org/2007/ops";
html { color: #172033; background: #fff; }
body { margin: 5%; font-family: serif; line-height: 1.55; }
h1, h2, h3, h4 { color: #12233d; font-family: sans-serif; line-height: 1.2; }
h1 { margin-top: 1.8em; }
a { color: #174f91; }
nav[epub|type~="toc"] ol { padding-left: 1.3em; }
.defn, .theorem, .lemma, .cor, .prop, .example, .exercise, .rem, .proof {
  margin: 1.2em 0; padding: .75em .9em; border-left: .28em solid #2b5d9a;
  background: #f4f7fb;
}
.example, .exercise { border-left-color: #7a4c9c; }
.proof { border-left-color: #65758c; background: #fafbfc; }
figure { margin: 1.4em auto; text-align: center; }
img { display: block; max-width: 100%; height: auto; margin: 0 auto; }
figcaption { color: #506078; font-size: .95em; }
.math.display { overflow-x: auto; }
table { border-collapse: collapse; max-width: 100%; }
th, td { border: 1px solid #ccd5e2; padding: .4em .55em; }
blockquote { margin: 1.2em 0; padding: .75em .9em; border-left: .28em solid #65758c; }
"""

IMAGE_ALTS = {
    "sets.png": (
        "Baris atas menampilkan himpunan konveks; baris bawah menampilkan "
        "himpunan tak konveks."
    ),
    "balls.png": (
        "Bola norma p untuk beberapa nilai p; kasus p sama dengan satu per dua "
        "tidak konveks."
    ),
    "convex_fct.png": (
        "Perbandingan grafik fungsi konveks dan fungsi tak konveks dalam satu dimensi."
    ),
    "gradient.png": "Gradien sebagai kemiringan garis singgung.",
    "subgradient.png": "Subgradien sebagai kemiringan garis pendukung.",
}

ENVIRONMENTS = ("defn", "theorem", "lemma", "cor", "prop", "example", "exercise", "rem", "proof")
REQUIRED_CHAPTER_MARKERS = (
    "Prasyarat",
    "Kekonveksan",
    "Subgradien",
    "Penurunan subgradien terproyeksi",
    "Metode gradien proksimal",
    "Akselerasi",
    "Dualitas",
    "Penurunan Gradien Stokastik",
    "Selingan tentang Transportasi Optimal",
)
TIKZ_FALLBACK_MARKERS = (
    "Kegagalan semikontinuitas bawah",
    "himpunan konveks tak beririsan",
    "ruas sekan yang menghubungkannya",
    "garis singgungnya pada titik",
    "Panel tengah menampilkan",
    "Peta T mengangkut",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def epub_fragment(source_label: str) -> str:
    """Map a TeX label to a standards-safe, stable HTML fragment."""
    fragment = re.sub(r"\s+", "-", source_label.strip())
    fragment = re.sub(r"[^A-Za-z0-9_.:-]", "-", fragment)
    return fragment or "label"


def balanced_argument(text: str, command: str) -> str | None:
    """Return the first balanced braced argument following command."""
    start = text.find(command)
    if start < 0:
        return None
    cursor = start + len(command)
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor < len(text) and text[cursor] == "[":
        depth = 1
        cursor += 1
        while cursor < len(text) and depth:
            if text[cursor] == "[" and text[cursor - 1] != "\\":
                depth += 1
            elif text[cursor] == "]" and text[cursor - 1] != "\\":
                depth -= 1
            cursor += 1
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
    if cursor >= len(text) or text[cursor] != "{":
        return None
    depth = 1
    begin = cursor + 1
    cursor += 1
    while cursor < len(text) and depth:
        char = text[cursor]
        escaped = cursor > 0 and text[cursor - 1] == "\\"
        if char == "{" and not escaped:
            depth += 1
        elif char == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return text[begin:cursor]
        cursor += 1
    return None


def replace_tikz_figures(source: str) -> tuple[str, int]:
    """Replace TikZ figure blocks with their semantic Indonesian caption."""
    pattern = re.compile(r"\\begin\{figure\}(.*?)\\end\{figure\}", re.DOTALL)
    replacements = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal replacements
        block = match.group(0)
        if r"\begin{tikzpicture}" not in block:
            return block
        caption = balanced_argument(block, r"\caption")
        label = balanced_argument(block, r"\label")
        if not caption:
            raise RuntimeError("TikZ figure lacks a recoverable caption")
        replacements += 1
        anchor = f"\\hypertarget{{{label}}}{{}}\n" if label else ""
        return (
            anchor
            + "\\begin{quote}\n"
            "\\textbf{Deskripsi figur nonraster.} "
            + caption
            + "\n\\end{quote}"
        )

    result = pattern.sub(replace, source)
    if r"\begin{tikzpicture}" in result or r"\end{tikzpicture}" in result:
        raise RuntimeError("TikZ survived semantic fallback conversion")
    return result, replacements


def build_combined_source() -> dict[str, object]:
    missing = [str(path) for path in CHAPTERS if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing translated chapters: " + ", ".join(missing))
    parts = [MATH_MACROS, INTRO]
    tikz_fallbacks = 0
    for path in CHAPTERS:
        chapter = path.read_text(encoding="utf-8")
        chapter, converted = replace_tikz_figures(chapter)
        tikz_fallbacks += converted
        chapter = re.sub(
            r"\\resizebox\{0\.88\\linewidth\}\{!\}\{\$\\displaystyle(.*?)\$\}",
            r"\1",
            chapter,
            flags=re.DOTALL,
        )
        chapter = chapter.replace(r"{figures/gradient}", r"{figures/gradient.png}")
        chapter = chapter.replace(r"{figures/subgradient}", r"{figures/subgradient.png}")
        parts.extend((f"\n% epub-source: {path.name}\n", chapter))
    combined = "\n".join(parts).replace("\r\n", "\n") + "\n"
    COMBINED_TEX.write_text(combined, encoding="utf-8", newline="\n")
    if tikz_fallbacks != 6:
        raise RuntimeError(f"Expected 6 TikZ figure fallbacks, found {tikz_fallbacks}")
    source_env_counts = {
        env: sum(
            len(re.findall(rf"\\begin\{{{env}\}}", path.read_text(encoding="utf-8")))
            for path in CHAPTERS
        )
        for env in ENVIRONMENTS
    }
    source_labels = [
        label
        for path in CHAPTERS
        for label in re.findall(
            r"\\label\{([^}]+)\}", path.read_text(encoding="utf-8")
        )
    ]
    duplicates = sorted({label for label in source_labels if source_labels.count(label) > 1})
    if duplicates:
        raise RuntimeError(f"Duplicate source labels prevent stable EPUB targets: {duplicates}")
    return {
        "tikz_figure_fallback_count": tikz_fallbacks,
        "source_environment_counts": source_env_counts,
        "source_labels": source_labels,
    }


def run_pandoc(destination: Path) -> list[str]:
    resource_path = os.pathsep.join(
        [str(SOURCE_DIR), str(ROOT / "authority" / "habring" / "source-v1")]
    )
    command = [
        "pandoc",
        str(COMBINED_TEX),
        "--from=latex",
        "--to=epub3",
        "--toc",
        "--toc-depth=3",
        "--split-level=1",
        "--mathml",
        f"--css={EPUB_CSS}",
        f"--resource-path={resource_path}",
        "--metadata=lang:id-ID",
        f"--metadata=title:{TITLE}",
        "--metadata=author:Andreas Habring; terjemahan/adaptasi mandiri",
        f"--metadata=identifier:{IDENTIFIER}",
        "--metadata=rights:Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "--metadata=publisher:Edisi turunan mandiri",
        f"--output={destination}",
    ]
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = "1787616000"
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode:
        raise RuntimeError(completed.stdout + completed.stderr)
    warnings = [line for line in completed.stderr.splitlines() if line.strip()]
    return warnings


def safe_extract(archive: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            target = (destination / PurePosixPath(info.filename)).resolve()
            if root != target and root not in target.parents:
                raise RuntimeError(f"Unsafe EPUB member path: {info.filename}")
        package.extractall(destination)


def package_media_by_source_name(extracted: Path) -> dict[str, Path]:
    source_hashes = {
        sha256(SOURCE_DIR / "figures" / name): name for name in IMAGE_ALTS
    }
    result: dict[str, Path] = {}
    for candidate in extracted.rglob("*"):
        if candidate.is_file() and candidate.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
            digest = sha256(candidate)
            if digest not in source_hashes:
                raise RuntimeError(
                    f"Unexpected raster/image resource in EPUB: {candidate.relative_to(extracted)}"
                )
            name = source_hashes[digest]
            if name in result:
                raise RuntimeError(f"Duplicate packaged image resource for {name}")
            result[name] = candidate
    if set(result) != set(IMAGE_ALTS):
        raise RuntimeError(
            f"Packaged image closure mismatch: got {sorted(result)}, expected {sorted(IMAGE_ALTS)}"
        )
    return result


def patch_xhtml(extracted: Path, packaged_images: dict[str, Path]) -> None:
    path_to_name = {
        path.resolve(): source_name for source_name, path in packaged_images.items()
    }
    image_usage = {name: 0 for name in IMAGE_ALTS}
    for xhtml in sorted(extracted.rglob("*.xhtml")):
        text = xhtml.read_text(encoding="utf-8")
        text = re.sub(r'xml:lang="[^"]*"', 'xml:lang="id-ID"', text)
        text = re.sub(r'(?<!xml:)lang="[^"]*"', 'lang="id-ID"', text)

        def normalize_math(match: re.Match[str]) -> str:
            block = match.group(0)
            annotations = re.findall(
                r'<annotation\b[^>]*encoding="application/x-tex"[^>]*>(.*?)</annotation>',
                block,
                flags=re.DOTALL | re.IGNORECASE,
            )
            labels: list[str] = []
            for annotation in annotations:
                labels.extend(re.findall(r"\\label\{([^}]+)\}", html.unescape(annotation)))
            if len(set(labels)) > 1:
                raise RuntimeError(
                    f"Math surface carries multiple labels in {xhtml.relative_to(extracted)}: {labels}"
                )
            if labels:
                escaped = html.escape(epub_fragment(labels[0]), quote=True)
                opening_end = block.find(">")
                opening = block[: opening_end + 1]
                if not re.search(r'\bid="[^"]+"', opening):
                    block = block[:opening_end] + f' id="{escaped}"' + block[opening_end:]
            # MathML is the portable EPUB formula surface. Removing TeX source
            # annotations prevents raw implementation markup from leaking into
            # reading systems while leaving the rendered formula intact.
            return re.sub(
                r'<annotation\b[^>]*encoding="application/x-tex"[^>]*>.*?</annotation>',
                "",
                block,
                flags=re.DOTALL | re.IGNORECASE,
            )

        text = re.sub(
            r"<math\b.*?</math>", normalize_math, text, flags=re.DOTALL | re.IGNORECASE
        )

        def normalize_id(match: re.Match[str]) -> str:
            quote = match.group(1)
            identifier = html.unescape(match.group(2))
            return f'id={quote}{html.escape(epub_fragment(identifier), quote=True)}{quote}'

        text = re.sub(r'id=(["\'])(.*?)\1', normalize_id, text, flags=re.IGNORECASE)

        def normalize_href_fragment(match: re.Match[str]) -> str:
            quote = match.group(1)
            reference = html.unescape(match.group(2))
            parsed = urlsplit(reference)
            if parsed.scheme or reference.startswith("//") or not parsed.fragment:
                return match.group(0)
            before_fragment = reference.split("#", 1)[0]
            normalized = epub_fragment(unquote(parsed.fragment))
            return f'href={quote}{html.escape(before_fragment + "#" + normalized, quote=True)}{quote}'

        text = re.sub(
            r'href=(["\'])(.*?)\1', normalize_href_fragment, text, flags=re.IGNORECASE
        )

        def bind_alt(match: re.Match[str]) -> str:
            tag = match.group(0)
            src_match = re.search(r'\bsrc="([^"]+)"', tag, re.IGNORECASE)
            if not src_match:
                raise RuntimeError(f"Image without src in {xhtml.relative_to(extracted)}")
            src = unquote(urlsplit(html.unescape(src_match.group(1))).path)
            target = (xhtml.parent / PurePosixPath(src)).resolve()
            if target not in path_to_name:
                raise RuntimeError(
                    f"Image reference does not resolve to registered raster: {src}"
                )
            source_name = path_to_name[target]
            image_usage[source_name] += 1
            alt = html.escape(IMAGE_ALTS[source_name], quote=True)
            if re.search(r'\balt="[^"]*"', tag, re.IGNORECASE):
                return re.sub(r'\balt="[^"]*"', f'alt="{alt}"', tag, count=1, flags=re.IGNORECASE)
            return tag[:-2] + f' alt="{alt}" />' if tag.endswith("/>") else tag[:-1] + f' alt="{alt}">'

        text = re.sub(r"<img\b[^>]*>", bind_alt, text, flags=re.IGNORECASE)
        xhtml.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    if any(count != 1 for count in image_usage.values()):
        raise RuntimeError(f"Every registered raster must be used exactly once: {image_usage}")


def repair_cross_document_fragment_links(extracted: Path) -> None:
    """Retarget fragment-only references after Pandoc splits the chapters."""
    xhtml_paths = sorted(extracted.rglob("*.xhtml"))
    member_for_path = {
        path: path.relative_to(extracted).as_posix() for path in xhtml_paths
    }
    fragment_owners: dict[str, list[str]] = {}
    text_by_path: dict[Path, str] = {}
    for path in xhtml_paths:
        text = path.read_text(encoding="utf-8")
        text_by_path[path] = text
        member = member_for_path[path]
        for identifier in re.findall(r'\bid="([^"]+)"', text):
            fragment_owners.setdefault(html.unescape(identifier), []).append(member)

    for path in xhtml_paths:
        member = member_for_path[path]
        text = text_by_path[path]

        def retarget(match: re.Match[str]) -> str:
            quote = match.group(1)
            reference = html.unescape(match.group(2))
            parsed = urlsplit(reference)
            if parsed.scheme or reference.startswith("//") or not parsed.fragment:
                return match.group(0)
            target = resolve_member(member, reference)
            fragment = unquote(parsed.fragment)
            if target in fragment_owners.get(fragment, []):
                return match.group(0)
            owners = fragment_owners.get(fragment, [])
            if len(owners) != 1:
                return match.group(0)
            relative = posixpath.relpath(owners[0], posixpath.dirname(member))
            new_reference = f"{relative}#{parsed.fragment}"
            return f'href={quote}{html.escape(new_reference, quote=True)}{quote}'

        text = re.sub(r'href=(["\'])(.*?)\1', retarget, text, flags=re.IGNORECASE)
        path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def normalize_xml_metadata(extracted: Path) -> None:
    for path in sorted(extracted.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".opf", ".xml", ".ncx"}:
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r'(<meta\b[^>]*property="dcterms:modified"[^>]*>)[^<]*(</meta>)',
            rf"\g<1>{FIXED_MODIFIED}\g<2>",
            text,
        )
        text = re.sub(r'xml:lang="[^"]*"', 'xml:lang="id-ID"', text)
        path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def normalized_zip(extracted: Path, destination: Path) -> None:
    files = sorted(
        (path for path in extracted.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(extracted).as_posix(),
    )
    mimetype = extracted / "mimetype"
    if not mimetype.is_file() or mimetype.read_bytes() != b"application/epub+zip":
        raise RuntimeError("EPUB mimetype file is missing or invalid")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as archive:
        info = zipfile.ZipInfo("mimetype", ZIP_EPOCH)
        info.compress_type = zipfile.ZIP_STORED
        info.create_system = 0
        info.external_attr = 0o100644 << 16
        archive.writestr(info, mimetype.read_bytes())
        for path in files:
            relative = path.relative_to(extracted).as_posix()
            if relative == "mimetype":
                continue
            info = zipfile.ZipInfo(relative, ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)


def build_once(destination: Path, build_index: int) -> dict[str, object]:
    raw = RAW_EPUB.with_name(f"{RAW_EPUB.stem}.{build_index}.epub")
    extracted = TMP_DIR / f"extract-{build_index}"
    warnings = run_pandoc(raw)
    safe_extract(raw, extracted)
    packaged_images = package_media_by_source_name(extracted)
    patch_xhtml(extracted, packaged_images)
    repair_cross_document_fragment_links(extracted)
    normalize_xml_metadata(extracted)
    normalized_zip(extracted, destination)
    return {
        "pandoc_warnings": warnings,
        "packaged_images": {
            name: {
                "path": path.relative_to(extracted).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for name, path in sorted(packaged_images.items())
        },
    }


def resolve_member(base: str, reference: str) -> str:
    parsed = urlsplit(html.unescape(reference))
    if parsed.scheme or reference.startswith("//"):
        return ""
    decoded = unquote(parsed.path)
    if not decoded:
        return base
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), decoded))


def validate_epub(path: Path, source_info: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if not infos or infos[0].filename != "mimetype":
            failures.append("mimetype is not the first ZIP entry")
        elif infos[0].compress_type != zipfile.ZIP_STORED:
            failures.append("mimetype entry is compressed")
        if archive.read("mimetype") != b"application/epub+zip":
            failures.append("invalid mimetype payload")
        if len(names) != len(set(names)):
            failures.append("duplicate ZIP member names")
        unsafe = [
            name for name in names
            if name.startswith(("/", "\\")) or ".." in PurePosixPath(name).parts
        ]
        if unsafe:
            failures.append(f"unsafe member paths: {unsafe}")
        nonfixed = [info.filename for info in infos if info.date_time != ZIP_EPOCH]
        if nonfixed:
            failures.append(f"non-normalized ZIP timestamps: {nonfixed}")
        if "META-INF/container.xml" not in names:
            failures.append("missing META-INF/container.xml")
        members = {name: archive.read(name) for name in names if not name.endswith("/")}

    xml_members = [
        name for name in members
        if PurePosixPath(name).suffix.lower() in {".xml", ".opf", ".ncx", ".xhtml"}
    ]
    parsed_xml: dict[str, ET.Element] = {}
    for name in xml_members:
        try:
            parsed_xml[name] = ET.fromstring(members[name])
        except ET.ParseError as exc:
            failures.append(f"XML parse failure in {name}: {exc}")

    container_name = "META-INF/container.xml"
    rootfile = ""
    if container_name in parsed_xml:
        rootfiles = parsed_xml[container_name].findall(
            ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
        )
        if len(rootfiles) != 1:
            failures.append(f"container must declare one rootfile, got {len(rootfiles)}")
        else:
            rootfile = rootfiles[0].attrib.get("full-path", "")
            if rootfile not in members:
                failures.append(f"container rootfile missing: {rootfile}")

    manifest: dict[str, tuple[str, str, str]] = {}
    manifest_members: set[str] = set()
    spine_ids: list[str] = []
    nav_items: list[str] = []
    if rootfile in parsed_xml:
        opf = parsed_xml[rootfile]
        ns = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
        package_version = opf.attrib.get("version", "")
        if not package_version.startswith("3"):
            failures.append(f"OPF is not EPUB 3: version={package_version}")
        metadata = opf.find("opf:metadata", ns)
        if metadata is None:
            failures.append("OPF metadata missing")
        else:
            def dc_values(local: str) -> list[str]:
                return ["".join(node.itertext()).strip() for node in metadata.findall(f"dc:{local}", ns)]

            if dc_values("title") != [TITLE]:
                failures.append(f"unexpected dc:title: {dc_values('title')}")
            if dc_values("language") != ["id-ID"]:
                failures.append(f"unexpected dc:language: {dc_values('language')}")
            if IDENTIFIER not in dc_values("identifier"):
                failures.append("fixed dc:identifier missing")
            unique_identifier = opf.attrib.get("unique-identifier", "")
            fixed_identifier_nodes = [
                node for node in metadata.findall("dc:identifier", ns)
                if "".join(node.itertext()).strip() == IDENTIFIER
            ]
            if (
                len(fixed_identifier_nodes) != 1
                or fixed_identifier_nodes[0].attrib.get("id") != unique_identifier
            ):
                failures.append("package unique-identifier does not resolve to the fixed identifier")
            rights = " ".join(dc_values("rights"))
            if "Creative Commons Attribution 4.0 International (CC BY 4.0)" not in rights:
                failures.append("exact CC BY 4.0 rights missing from OPF")
            modified = [
                "".join(node.itertext()).strip()
                for node in metadata.findall("opf:meta", ns)
                if node.attrib.get("property") == "dcterms:modified"
            ]
            if modified != [FIXED_MODIFIED]:
                failures.append(f"nonfixed dcterms:modified value: {modified}")
        manifest_node = opf.find("opf:manifest", ns)
        if manifest_node is None:
            failures.append("OPF manifest missing")
        else:
            for item in manifest_node.findall("opf:item", ns):
                item_id = item.attrib.get("id", "")
                href = item.attrib.get("href", "")
                media_type = item.attrib.get("media-type", "")
                properties = item.attrib.get("properties", "")
                manifest[item_id] = (href, media_type, properties)
                resolved = resolve_member(rootfile, href)
                if not resolved or resolved not in members:
                    failures.append(f"manifest resource missing: {item_id} -> {href}")
                else:
                    manifest_members.add(resolved)
                if "nav" in properties.split():
                    nav_items.append(resolved)
            if len(nav_items) != 1:
                failures.append(f"expected one navigation document, got {nav_items}")
        spine = opf.find("opf:spine", ns)
        if spine is None:
            failures.append("OPF spine missing")
        else:
            for itemref in spine.findall("opf:itemref", ns):
                item_id = itemref.attrib.get("idref", "")
                spine_ids.append(item_id)
                if item_id not in manifest:
                    failures.append(f"spine idref absent from manifest: {item_id}")
        if not spine_ids:
            failures.append("OPF spine is empty")
        allowed_nonmanifest = {
            "mimetype",
            "META-INF/container.xml",
            "META-INF/com.apple.ibooks.display-options.xml",
            rootfile,
        }
        unmanifested = sorted(set(members) - manifest_members - allowed_nonmanifest)
        if unmanifested:
            failures.append(f"unmanifested package resources: {unmanifested}")

    xhtml_names = sorted(name for name in members if name.endswith(".xhtml"))
    all_xhtml = b"\n".join(members[name] for name in xhtml_names).decode("utf-8")
    plainish = re.sub(r"<[^>]+>", " ", all_xhtml)
    plainish = html.unescape(re.sub(r"\s+", " ", plainish))
    for marker in REQUIRED_CHAPTER_MARKERS:
        if marker not in plainish:
            failures.append(f"missing chapter marker: {marker}")
    if len(re.findall(r"<h1\b", all_xhtml, re.IGNORECASE)) < 9:
        failures.append("fewer than nine h1 chapter surfaces")
    if "OpenAI Codex gpt-5.6-sol, Ultra" not in plainish:
        failures.append("exact model provenance marker missing")
    if "Creative Commons Attribution 4.0 International (CC BY 4.0)" not in plainish:
        failures.append("reader-first CC BY 4.0 notice missing")
    if re.search(r"\bTTP\b|Translation and Transcription Project", plainish):
        failures.append("TTP leaked into EPUB title or prose")
    raw_math_spans = re.findall(
        r'<span\b[^>]*class="[^"]*\bmath\b[^"]*"[^>]*>.*?</span>',
        all_xhtml,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if raw_math_spans:
        failures.append(f"raw non-MathML formula spans remain: {len(raw_math_spans)}")
    if "<annotation" in all_xhtml:
        failures.append("TeX source annotations remain in MathML")
    forbidden_tex = (
        r"\begin{tikzpicture}", r"\end{tikzpicture}", r"\includegraphics",
        r"\resizebox", r"\textwidth", r"\pgfmath", r"\draw[", r"\node[",
    )
    for marker in forbidden_tex:
        if marker in all_xhtml:
            failures.append(f"raw TikZ/TeX leaked into XHTML: {marker}")
    for marker in TIKZ_FALLBACK_MARKERS:
        visible = marker.replace(r"\circ", "∘")
        if marker not in plainish and visible not in plainish:
            failures.append(f"missing semantic TikZ fallback marker: {marker}")

    output_env_counts = {
        env: len(re.findall(rf'class="[^"]*\b{env}\b[^"]*"', all_xhtml))
        for env in ENVIRONMENTS
    }
    source_env_counts = source_info["source_environment_counts"]
    for env in ENVIRONMENTS:
        if output_env_counts[env] != source_env_counts[env]:
            failures.append(
                f"environment class mismatch for {env}: source={source_env_counts[env]}, "
                f"EPUB={output_env_counts[env]}"
            )

    ids_by_member: dict[str, set[str]] = {}
    internal_reference_count = 0
    image_alt_count = 0
    image_sources: list[str] = []
    unresolved: list[str] = []
    for name in xhtml_names:
        text = members[name].decode("utf-8")
        html_opening = re.search(r"<html\b[^>]*>", text, re.IGNORECASE)
        if (
            not html_opening
            or 'lang="id-ID"' not in html_opening.group(0)
            or 'xml:lang="id-ID"' not in html_opening.group(0)
        ):
            failures.append(f"XHTML language is not id-ID in {name}")
        ids_by_member[name] = set(re.findall(r'\bid="([^"]+)"', text))
    source_label_owners = {
        label: [
            member
            for member, identifiers in ids_by_member.items()
            if epub_fragment(label) in identifiers
        ]
        for label in source_info["source_labels"]
    }
    bad_source_labels = {
        label: owners for label, owners in source_label_owners.items() if len(owners) != 1
    }
    if bad_source_labels:
        failures.append(f"source labels not preserved exactly once: {bad_source_labels}")
    whitespace_ids = {
        member: sorted(identifier for identifier in identifiers if re.search(r"\s", identifier))
        for member, identifiers in ids_by_member.items()
        if any(re.search(r"\s", identifier) for identifier in identifiers)
    }
    if whitespace_ids:
        failures.append(f"HTML ids contain whitespace: {whitespace_ids}")
    for name in xhtml_names:
        text = members[name].decode("utf-8")
        for tag in re.findall(r"<img\b[^>]*>", text, re.IGNORECASE):
            src_match = re.search(r'\bsrc="([^"]+)"', tag, re.IGNORECASE)
            alt_match = re.search(r'\balt="([^"]*)"', tag, re.IGNORECASE)
            if not src_match:
                failures.append(f"image without src in {name}")
                continue
            source = html.unescape(src_match.group(1))
            image_sources.append(source)
            parsed = urlsplit(source)
            if parsed.scheme or source.startswith("//"):
                failures.append(f"external image dependency in {name}: {source}")
            target = resolve_member(name, source)
            if target not in members:
                failures.append(f"missing image resource in {name}: {source}")
            if not alt_match or not html.unescape(alt_match.group(1)).strip():
                failures.append(f"missing/empty image alt in {name}: {source}")
            else:
                image_alt_count += 1
        for attribute, reference in re.findall(r'\b(href|src)="([^"]+)"', text, re.IGNORECASE):
            reference = html.unescape(reference)
            parsed = urlsplit(reference)
            if parsed.scheme or reference.startswith("//"):
                continue
            target = resolve_member(name, reference)
            if parsed.path and target not in members:
                unresolved.append(f"{name}: {attribute}={reference}")
                continue
            if parsed.fragment:
                fragment_member = target if parsed.path else name
                if fragment_member not in ids_by_member:
                    if fragment_member not in members:
                        unresolved.append(f"{name}: {attribute}={reference}")
                    continue
                if unquote(parsed.fragment) not in ids_by_member[fragment_member]:
                    unresolved.append(f"{name}: missing fragment {reference}")
                else:
                    internal_reference_count += 1
    if unresolved:
        failures.append(f"unresolved internal references: {unresolved[:20]}")
    if len(image_sources) != 5 or image_alt_count != 5:
        failures.append(
            f"expected five raster uses with alt text, got images={len(image_sources)}, alts={image_alt_count}"
        )
    for expected_alt in IMAGE_ALTS.values():
        if all_xhtml.count(html.escape(expected_alt, quote=True)) != 1:
            failures.append(f"expected image alternative not present exactly once: {expected_alt}")

    nav_link_count = 0
    if len(nav_items) == 1 and nav_items[0] in parsed_xml:
        nav_root = parsed_xml[nav_items[0]]
        nav_namespace = {"x": "http://www.w3.org/1999/xhtml"}
        navs = nav_root.findall(".//x:nav", nav_namespace)
        toc_navs = [
            nav for nav in navs
            if nav.attrib.get("{http://www.idpf.org/2007/ops}type") == "toc"
            or "toc" in nav.attrib.get("role", "")
        ]
        if not toc_navs:
            failures.append("navigation document lacks EPUB TOC nav")
        else:
            nav_link_count = len(toc_navs[0].findall(".//x:a", nav_namespace))
            if nav_link_count < 9:
                failures.append(f"navigation TOC has too few links: {nav_link_count}")

    mathml_count = len(re.findall(r"<math\b", all_xhtml, re.IGNORECASE))
    if mathml_count < 100:
        failures.append(f"implausibly few MathML surfaces: {mathml_count}")
    if failures:
        raise RuntimeError("EPUB validation failed:\n- " + "\n- ".join(failures))
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "zip_entry_count": len(members),
        "xml_member_count": len(xml_members),
        "xhtml_member_count": len(xhtml_names),
        "manifest_item_count": len(manifest),
        "manifest_resource_closure": True,
        "spine_item_count": len(spine_ids),
        "navigation_link_count": nav_link_count,
        "chapter_h1_count": len(re.findall(r"<h1\b", all_xhtml, re.IGNORECASE)),
        "mathml_count": mathml_count,
        "internal_reference_count": internal_reference_count,
        "raster_image_count": len(image_sources),
        "nonempty_image_alt_count": image_alt_count,
        "source_label_count": len(source_info["source_labels"]),
        "preserved_source_label_count": len(source_info["source_labels"]),
        "environment_class_counts": output_env_counts,
        "tikz_figure_fallback_count": source_info["tikz_figure_fallback_count"],
        "external_image_dependencies": [],
        "unresolved_internal_references": [],
        "xml_parse_failures": [],
        "raw_math_span_count": 0,
        "raw_tex_annotation_count": 0,
        "failures": [],
    }


def main() -> None:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir(parents=True)
    OUTPUT_EPUB.parent.mkdir(parents=True, exist_ok=True)
    EPUB_CSS.write_text(CSS.strip() + "\n", encoding="utf-8", newline="\n")
    source_info = build_combined_source()
    first_info = build_once(FIRST_EPUB, 1)
    second_info = build_once(SECOND_EPUB, 2)
    if FIRST_EPUB.read_bytes() != SECOND_EPUB.read_bytes():
        raise RuntimeError("Two normalized EPUB builds were not byte-identical")
    shutil.copyfile(SECOND_EPUB, OUTPUT_EPUB)
    validation = validate_epub(OUTPUT_EPUB, source_info)
    if first_info["packaged_images"] != second_info["packaged_images"]:
        raise RuntimeError("Packaged raster identity differed between builds")
    report = {
        "schema": "o015-habring-full-epub-build-v1",
        "result": "pass",
        "artifact": {
            "path": OUTPUT_EPUB.relative_to(ROOT).as_posix(),
            **validation,
        },
        "inputs": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in CHAPTERS
        ],
        "source_environment_counts": source_info["source_environment_counts"],
        "packaged_images": second_info["packaged_images"],
        "pandoc": {
            "version": subprocess.run(
                ["pandoc", "--version"], capture_output=True, text=True, check=True
            ).stdout.splitlines()[0],
            "warnings_build_1": first_info["pandoc_warnings"],
            "warnings_build_2": second_info["pandoc_warnings"],
        },
        "determinism": {
            "builds": 2,
            "byte_identical": True,
            "zip_entry_order": "mimetype first; remaining entries sorted lexicographically",
            "zip_timestamps": "1980-01-01T00:00:00",
            "opf_modified": FIXED_MODIFIED,
        },
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    shutil.rmtree(TMP_DIR)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
