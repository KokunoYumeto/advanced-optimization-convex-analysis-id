#!/usr/bin/env python3
"""Build deterministic integrated HTML and EPUB 3 readers for O015/D90.

The script reads the admitted canonical TeX bodies in their frozen order, but
does not modify them.  It produces a page-filling standalone semantic HTML
reader and a normalized EPUB 3 package.  Component rights remain separate.
"""

from __future__ import annotations

import base64
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
TMP_DIR = ROOT / "tmp" / "integrated-readers"
COMBINED_TEX = TMP_DIR / "D90-O015-integrated-reader-id.tex"
EPUB_CSS = TMP_DIR / "integrated-reader.css"
HTML_FIRST = TMP_DIR / "integrated-reader.first.html"
HTML_SECOND = TMP_DIR / "integrated-reader.second.html"
EPUB_FIRST = TMP_DIR / "integrated-reader.first.epub"
EPUB_SECOND = TMP_DIR / "integrated-reader.second.epub"
OUTPUT_HTML = ROOT / "output" / "html" / "D90-O015-optimisasi-lanjut-analisis-konveks-id.html"
OUTPUT_EPUB = ROOT / "output" / "epub" / "D90-O015-optimisasi-lanjut-analisis-konveks-id.epub"
REPORT_PATH = ROOT / "qa" / "INTEGRATED_READERS_BUILD.json"
BIBLIOGRAPHY = SOURCE_DIR / "references-integrated-id.bib"

TITLE = "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia"
IDENTIFIER = "urn:uuid:81057e39-68c8-5b34-8d59-f53deae44ec2"
FIXED_MODIFIED = "2026-08-27T00:00:00Z"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Tulang Punggung: Optimisasi Konveks",
        (
            "habring-01-prasyarat-id.tex",
            "habring-02-konveksitas-id.tex",
            "habring-03-subgradien-id.tex",
            "habring-04-metode-subgradien-terproyeksi-id.tex",
            "habring-05-metode-gradien-proksimal-id.tex",
            "habring-06-akselerasi-id.tex",
            "habring-07-dualitas-id.tex",
            "habring-08-penurunan-gradien-stokastik-id.tex",
            "habring-09-transportasi-optimal-id.tex",
        ),
    ),
    (
        "Suplemen Terbatas: Dualitas dan Reduksi Varians",
        (
            "becker-01-dualitas-lagrange-slater-kkt-id.tex",
            "becker-03-reduksi-varians-id.tex",
        ),
    ),
    (
        "Metode Stokastik Komposit",
        ("original-01-metode-stokastik-komposit-cermin-minibatch-id.tex",),
    ),
    (
        "Suplemen Terbatas: Douglas--Rachford",
        ("becker-02-pemisahan-douglas-rachford-id.tex",),
    ),
    (
        "Operator Monoton dan Pemisahan",
        ("original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex",),
    ),
    (
        "Asesmen dan Penutupan Kursus",
        ("original-03-penutupan-kursus-id.tex",),
    ),
)

ORIGINAL_03_MODULES = tuple(
    f"original-03/{index:02d}-{slug}-id.tex"
    for index, slug in enumerate(
        (
            "peta-asesmen",
            "diagnostik-prasyarat",
            "set-soal-dasar-konveks",
            "set-soal-metode-proksimal",
            "set-soal-dualitas-kkt",
            "set-soal-metode-stokastik",
            "set-soal-operator-monoton",
            "set-soal-transportasi-dan-sintesis",
            "rubrik-pembuktian",
            "ujian-tengah",
            "ujian-akhir",
            "laboratorium-globalisasi-newton",
            "laboratorium-transportasi-entropik",
            "proyek-kapstone-masalah-invers-komposit",
        )
    )
)

SOURCE_PATHS = tuple(
    SOURCE_DIR / name
    for _, names in GROUPS
    for name in names
) + tuple(SOURCE_DIR / name for name in ORIGINAL_03_MODULES)

ENVIRONMENTS = ("defn", "theorem", "lemma", "cor", "prop", "example", "exercise", "rem", "proof")

IMAGE_DESCRIPTIONS = {
    "sets.png": (
        "Baris atas menampilkan beberapa himpunan konveks yang memuat seluruh ruas "
        "garis di antara tiap dua titiknya. Baris bawah menampilkan himpunan tak "
        "konveks dengan lekukan atau komponen terpisah."
    ),
    "balls.png": (
        "Bola satuan dua dimensi untuk beberapa nilai p: bentuk berubah dari belah "
        "ketupat melalui lingkaran menuju persegi; kasus p sama dengan satu per dua "
        "melengkung ke dalam dan tidak konveks."
    ),
    "convex_fct.png": (
        "Perbandingan grafik satu dimensi: fungsi konveks berbentuk mangkuk dengan "
        "minimum teratur dan fungsi tak konveks dengan beberapa lekukan serta minimum lokal."
    ),
    "gradient.png": (
        "Parabola halus dengan sebuah garis singgung putus-putus pada titik yang "
        "ditandai; kemiringan garis merupakan gradien."
    ),
    "subgradient.png": (
        "Grafik berbentuk V dengan tiga garis pendukung melalui titik tak mulus; "
        "kemiringan masing-masing garis merupakan subgradien yang sah."
    ),
}

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
\newcommand{\linop}{\mathcal{L}}
\newcommand{\Rnn}{\mathbb{R}^{n\times n}}
\newcommand{\Cnn}{\mathbb{C}^{n\times n}}
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
\newcommand{\spann}{\operatorname{span}}
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
\newcommand{\ie}{\textit{yaitu}}
\newcommand{\eg}{\textit{misalnya}}
\newcommand{\cf}{\textit{bandingkan}}
""" + "\n".join(
    rf"\newcommand{{\cal{letter}}}{{\mathcal{{{letter}}}}}" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
)

INTRO = r"""
\section*{Tentang edisi terpadu ini}
\hypertarget{tentang-edisi-terpadu}{}
\begin{quote}
\textbf{Status dan hak komponen.} Pembaca ini menyatukan bahan yang sudah
diterima ke dalam satu urutan kursus tanpa mengubah kepemilikan atau lisensi
masing-masing komponen. Tulang punggung terstruktur adalah terjemahan lengkap
catatan Andreas Habring, arXiv:2607.11664v1, berdasarkan Creative Commons
Attribution 4.0 International (CC BY 4.0). Tiga suplemen terbatas dari catatan
Stephen Becker yang diketik Mitchell Krock digunakan berdasarkan Lisensi MIT.
Bab penghubung, asesmen, solusi, laboratorium, dan proyek yang ditulis khusus
untuk edisi ini tersedia berdasarkan Creative Commons Attribution-ShareAlike
4.0 International (CC BY-SA 4.0). Tidak ada klaim lisensi payung.

Edisi Bahasa Indonesia ini mandiri dan bukan edisi resmi atau dukungan Habring,
Becker, Krock, institusi mereka, ataupun penyedia sumber pendamping. Materi MIT
OpenCourseWare, Clément Royer, dan Penn State tetap menjadi pembaca pendamping
terpisah. Materi O018 tentang program linear atau bilangan bulat, simpleks,
sensitivitas LP, dan optimisasi jaringan berada di luar cakupan.

Produksi edisi dan pemeriksaan deterministik menggunakan OpenAI Codex
gpt-5.6-sol, Ultra. Semua kredit pengarang sumber dan kontribusi manusia tetap
dipertahankan. HTML dan EPUB 3 ini adalah permukaan reflow utama; rumus disajikan
sebagai MathML dengan anotasi TeX sumber untuk sistem baca yang mendukungnya.
\end{quote}
"""

HTML_CSS = r"""
:root {
  color-scheme: light;
  --ink: #172033; --muted: #516078; --rule: #cbd6e4;
  --accent: #1d5f9f; --accent-2: #714493; --panel: #f4f7fb;
  --canvas: #eef3f8; --content-max: 96rem;
}
* { box-sizing: border-box; }
html { font-size: 100%; scroll-behavior: smooth; }
body {
  margin: 0; padding: 0; min-width: 0; max-width: none; overflow-x: clip;
  color: var(--ink); background: var(--canvas);
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1rem, .96rem + .18vw, 1.12rem); line-height: 1.66;
}
.skip-link {
  position: fixed; z-index: 1000; inset-block-start: .5rem; inset-inline-start: .5rem;
  transform: translateY(-180%); padding: .7rem 1rem; color: #fff;
  background: #102c4d; border-radius: .35rem;
}
.skip-link:focus { transform: translateY(0); }
a { color: #174f91; text-underline-offset: .15em; }
a:focus-visible, summary:focus-visible, [tabindex]:focus-visible {
  outline: .2rem solid #e09b22; outline-offset: .18rem; border-radius: .12rem;
}
header#title-block-header, nav#TOC, main#main-content, footer[role="contentinfo"] {
  width: min(calc(100% - 2rem), var(--content-max)); margin-inline: auto;
}
header#title-block-header {
  margin-block-start: 1rem; padding: clamp(1.4rem, 3vw, 3rem);
  background: #fff; border: 1px solid var(--rule); border-radius: .65rem .65rem 0 0;
}
nav#TOC {
  padding: 1rem clamp(1rem, 2.2vw, 2rem); background: #f8fbfe;
  border-inline: 1px solid var(--rule); border-block-end: 1px solid var(--rule);
}
nav#TOC ul { padding-inline-start: 1.35rem; }
main#main-content {
  padding: clamp(1rem, 3vw, 3rem); background: #fff;
  border-inline: 1px solid var(--rule);
}
footer[role="contentinfo"] {
  margin-block-end: 1rem; padding: 1rem clamp(1rem, 3vw, 3rem);
  color: var(--muted); background: #f8fbfe; border: 1px solid var(--rule);
  border-radius: 0 0 .65rem .65rem;
}
h1, h2, h3, h4, h5 { font-family: Arial, Helvetica, sans-serif; line-height: 1.2;
  color: #12233d; scroll-margin-top: 1rem; overflow-wrap: anywhere; }
h1 { margin-block-start: 2.7rem; font-size: clamp(1.9rem, 1.4rem + 1.8vw, 3rem); }
h2 { margin-block-start: 2.25rem; font-size: clamp(1.45rem, 1.2rem + .8vw, 2rem); }
h3 { margin-block-start: 1.7rem; }
p, li { max-width: 92ch; }
p { margin-inline: 0; }
section.level1, section.level2 { min-width: 0; }
.defn, .theorem, .lemma, .cor, .prop, .example, .exercise, .rem, .proof {
  width: 100%; max-width: 94ch; margin: 1.25rem 0; padding: .9rem 1rem;
  border-inline-start: .3rem solid var(--accent); background: var(--panel);
}
.example, .exercise { border-inline-start-color: var(--accent-2); }
.proof { border-inline-start-color: #65758c; background: #fafbfc; }
figure { width: 100%; margin: 1.5rem 0; padding: .8rem; text-align: center;
  border: 1px solid var(--rule); background: #fbfcfe; }
img { display: block; max-width: 100%; height: auto; margin-inline: auto; }
figcaption { margin-block-start: .65rem; color: var(--muted); font-size: .96rem; }
.long-description { max-width: 88ch; margin: .75rem auto 0; text-align: start; color: #33445b; }
math[display="block"], .math.display { display: block; max-width: 100%; overflow-x: auto;
  overflow-y: hidden; padding: .35rem 0; overscroll-behavior-inline: contain; }
.math.inline, math:not([display="block"]) { max-width: 100%; overflow-x: auto; vertical-align: middle; }
table { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; }
th, td { border: 1px solid var(--rule); padding: .45rem .6rem; }
pre { max-width: 100%; overflow-x: auto; padding: .8rem; background: #f4f7fb; }
code { overflow-wrap: anywhere; }
@media (max-width: 48rem) {
  header#title-block-header, nav#TOC, main#main-content, footer[role="contentinfo"] {
    width: calc(100% - .75rem);
  }
  header#title-block-header, main#main-content { padding: .9rem; }
  nav#TOC { padding: .8rem; }
  .defn, .theorem, .lemma, .cor, .prop, .example, .exercise, .rem, .proof {
    padding: .72rem .75rem;
  }
}
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
@media print {
  body { background: #fff; font-size: 10.5pt; }
  header#title-block-header, nav#TOC, main#main-content, footer[role="contentinfo"] {
    width: 100%; border: 0; }
  nav#TOC { break-after: page; } a { color: inherit; text-decoration: none; }
}
"""

EPUB_CSS_TEXT = r"""
@namespace epub "http://www.idpf.org/2007/ops";
html { color: #172033; background: #fff; }
body { margin: 4%; font-family: serif; line-height: 1.58; }
.skip-link { position: absolute; left: -10000px; }
.skip-link:focus { position: static; display: inline-block; padding: .5em; }
a:focus, summary:focus { outline: .18em solid #e09b22; outline-offset: .12em; }
h1, h2, h3, h4 { color: #12233d; font-family: sans-serif; line-height: 1.2; }
h1 { margin-top: 1.7em; }
nav[epub|type~="toc"] ol { padding-left: 1.3em; }
.defn, .theorem, .lemma, .cor, .prop, .example, .exercise, .rem, .proof {
  margin: 1.2em 0; padding: .75em .9em; border-left: .28em solid #1d5f9f;
  background: #f4f7fb;
}
.example, .exercise { border-left-color: #714493; }
.proof { border-left-color: #65758c; background: #fafbfc; }
figure { margin: 1.3em 0; padding: .5em; text-align: center; border: .08em solid #ccd5e2; }
img { display: block; max-width: 100%; height: auto; margin: 0 auto; }
figcaption { color: #506078; font-size: .95em; }
.long-description { text-align: left; color: #33445b; }
math[display="block"], .math.display { max-width: 100%; overflow-x: auto; }
table, pre { max-width: 100%; overflow-x: auto; }
th, td { border: .08em solid #ccd5e2; padding: .4em .55em; }
blockquote { margin: 1.2em 0; padding: .75em .9em; border-left: .28em solid #65758c; }
@media (max-width: 36em) { body { margin: 2.5%; } }
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bytes_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def epub_fragment(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"[^A-Za-z0-9_.:-]", "-", value)
    return value or "label"


def balanced_argument(text: str, command: str) -> str | None:
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
            escaped = cursor > 0 and text[cursor - 1] == "\\"
            if text[cursor] == "[" and not escaped:
                depth += 1
            elif text[cursor] == "]" and not escaped:
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
        escaped = cursor > 0 and text[cursor - 1] == "\\"
        if text[cursor] == "{" and not escaped:
            depth += 1
        elif text[cursor] == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return text[begin:cursor]
        cursor += 1
    return None


def replace_tikz_figures(source: str) -> tuple[str, int]:
    pattern = re.compile(r"\\begin\{figure\}(.*?)\\end\{figure\}", re.DOTALL)
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        block = match.group(0)
        if r"\begin{tikzpicture}" not in block:
            return block
        caption = balanced_argument(block, r"\caption")
        label = balanced_argument(block, r"\label")
        if not caption:
            raise RuntimeError("TikZ figure lacks a recoverable Indonesian caption")
        caption = caption.replace(r"\gls{ot}", "transportasi optimal")
        count += 1
        anchor = f"\\hypertarget{{{label}}}{{}}\n" if label else ""
        return (
            anchor
            + "\\begin{quote}\n"
            + "\\textbf{Deskripsi figur nonraster.} "
            + caption
            + "\n\\end{quote}"
        )

    result = pattern.sub(replace, source)
    if r"\begin{tikzpicture}" in result or r"\end{tikzpicture}" in result:
        raise RuntimeError("TikZ survived semantic fallback conversion")
    return result, count


def preprocess_source(source: str) -> tuple[str, int]:
    source = source.replace("\r\n", "\n")
    source = source.replace(r"\gls{ot}", "transportasi optimal")
    source = source.replace(r"\Gls{ot}", "Transportasi optimal")
    source = re.sub(r"\\Needspace\{[^{}]*\}", "", source)
    source = re.sub(r"\\needspace\{[^{}]*\}", "", source)
    source = source.replace(r"{figures/gradient}", r"{figures/gradient.png}")
    source = source.replace(r"{figures/subgradient}", r"{figures/subgradient.png}")
    # Pandoc's TeX-math reader supports smallmatrix but not the mathtools alias
    # psmallmatrix.  This reader-only normalization preserves the same compact
    # matrix semantics while avoiding a raw-TeX fallback surface.
    source = source.replace(r"\begin{psmallmatrix}", r"\begin{smallmatrix}")
    source = source.replace(r"\end{psmallmatrix}", r"\end{smallmatrix}")
    source, tikz_count = replace_tikz_figures(source)
    source = re.sub(
        r"\\resizebox\{0\.88\\linewidth\}\{!\}\{\$\\displaystyle(.*?)\$\}",
        r"\1",
        source,
        flags=re.DOTALL,
    )
    return source, tikz_count


def expand_original_03(aggregator: str) -> str:
    expanded = aggregator
    for relative in ORIGINAL_03_MODULES:
        module_name = relative.removesuffix(".tex")
        pattern = re.compile(rf"\\input\{{{re.escape(module_name)}\}}")
        matches = pattern.findall(expanded)
        if len(matches) != 1:
            raise RuntimeError(f"Expected one aggregator input for {module_name}, got {len(matches)}")
        module = (SOURCE_DIR / relative).read_text(encoding="utf-8")
        replacement = "\n% integrated-module: " + relative + "\n" + module
        expanded = pattern.sub(lambda _match: replacement, expanded, count=1)
    if re.search(r"\\input\{original-03/", expanded):
        raise RuntimeError("Unexpanded Original-03 input survived")
    return expanded


def collect_source_info() -> dict[str, object]:
    missing = [str(path) for path in (*SOURCE_PATHS, BIBLIOGRAPHY) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing admitted input: " + ", ".join(missing))
    texts = {path: path.read_text(encoding="utf-8") for path in SOURCE_PATHS}
    labels = [label for text in texts.values() for label in re.findall(r"\\label\{([^}]+)\}", text)]
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if duplicates:
        raise RuntimeError(f"Duplicate canonical TeX labels: {duplicates}")
    first_label_by_file = {}
    for path, text in texts.items():
        found = re.findall(r"\\label\{([^}]+)\}", text)
        if found:
            first_label_by_file[path.relative_to(ROOT).as_posix()] = found[0]
    environment_counts = {
        env: sum(len(re.findall(rf"\\begin\{{{env}\}}", text)) for text in texts.values())
        for env in ENVIRONMENTS
    }
    return {
        "texts": texts,
        "labels": labels,
        "first_label_by_file": first_label_by_file,
        "environment_counts": environment_counts,
    }


def build_combined_source(source_info: dict[str, object]) -> dict[str, object]:
    texts: dict[Path, str] = source_info["texts"]  # type: ignore[assignment]
    parts = [MATH_MACROS, INTRO]
    tikz_fallback_count = 0
    for group_index, (group_title, filenames) in enumerate(GROUPS, start=1):
        parts.append(
            f"\n\\part{{{group_title}}}\n"
            f"\\hypertarget{{integrated:part:{group_index:02d}}}{{}}\n"
        )
        for filename in filenames:
            path = SOURCE_DIR / filename
            source = texts[path]
            if filename == "original-03-penutupan-kursus-id.tex":
                source = expand_original_03(source)
            source, converted = preprocess_source(source)
            tikz_fallback_count += converted
            parts.extend((f"\n% integrated-source: {filename}\n", source))
    combined = "\n".join(parts).replace("\r\n", "\n") + "\n"
    if tikz_fallback_count != 6:
        raise RuntimeError(f"Expected six semantic TikZ figure fallbacks, got {tikz_fallback_count}")
    if r"\input{" in combined:
        raise RuntimeError("Unexpected unexpanded TeX input in integrated source")
    COMBINED_TEX.write_text(combined, encoding="utf-8", newline="\n")
    return {
        "tikz_figure_fallback_count": tikz_fallback_count,
        "combined_source_bytes": COMBINED_TEX.stat().st_size,
        "combined_source_sha256": sha256(COMBINED_TEX),
    }


def run(command: list[str], *, env: dict[str, str] | None = None) -> list[str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n"
            + completed.stdout
            + completed.stderr
        )
    return [line for line in completed.stderr.splitlines() if line.strip()]


def resource_path() -> str:
    return os.pathsep.join(
        (
            str(SOURCE_DIR),
            str(ROOT / "authority" / "habring" / "source-v1"),
            str(ROOT),
        )
    )


def pandoc_html(destination: Path) -> list[str]:
    warnings = run(
        [
            "pandoc",
            str(COMBINED_TEX),
            "--from=latex",
            "--to=html5",
            "--standalone",
            "--toc",
            "--toc-depth=3",
            "--section-divs",
            "--embed-resources",
            "--mathml",
            "--citeproc",
            f"--bibliography={BIBLIOGRAPHY}",
            f"--resource-path={resource_path()}",
            "--metadata=lang:id-ID",
            f"--metadata=title:{TITLE}",
            "--metadata=author:Andreas Habring; Stephen Becker; Mitchell Krock; edisi mandiri",
            f"--output={destination}",
        ]
    )
    patch_html(destination)
    return warnings


def data_uri_payload(uri: str) -> bytes:
    if not uri.startswith("data:") or "," not in uri:
        raise RuntimeError("Expected embedded data URI image")
    header, payload = uri.split(",", 1)
    if ";base64" not in header:
        raise RuntimeError("Expected base64-encoded embedded image")
    return base64.b64decode(payload)


def image_hash_registry() -> dict[str, tuple[str, str]]:
    result = {}
    for filename, description in IMAGE_DESCRIPTIONS.items():
        path = SOURCE_DIR / "figures" / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        result[sha256(path)] = (filename, description)
    return result


def normalize_math_and_ids(text: str) -> str:
    def math_block(match: re.Match[str]) -> str:
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
            raise RuntimeError(f"Math surface carries multiple labels: {labels}")
        if labels:
            fragment = html.escape(epub_fragment(labels[0]), quote=True)
            opening_end = block.find(">")
            opening = block[: opening_end + 1]
            if not re.search(r'\bid="[^"]+"', opening):
                block = block[:opening_end] + f' id="{fragment}"' + block[opening_end:]
        return block

    text = re.sub(r"<math\b.*?</math>", math_block, text, flags=re.DOTALL | re.IGNORECASE)

    def normalize_id(match: re.Match[str]) -> str:
        quote = match.group(1)
        identifier = html.unescape(match.group(2))
        return f'id={quote}{html.escape(epub_fragment(identifier), quote=True)}{quote}'

    text = re.sub(r'id=(["\'])(.*?)\1', normalize_id, text, flags=re.IGNORECASE)

    def normalize_href(match: re.Match[str]) -> str:
        quote = match.group(1)
        reference = html.unescape(match.group(2))
        parsed = urlsplit(reference)
        if parsed.scheme or reference.startswith("//") or not parsed.fragment:
            return match.group(0)
        before = reference.split("#", 1)[0]
        fragment = epub_fragment(unquote(parsed.fragment))
        return f'href={quote}{html.escape(before + "#" + fragment, quote=True)}{quote}'

    return re.sub(r'href=(["\'])(.*?)\1', normalize_href, text, flags=re.IGNORECASE)


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "</head>" not in text or "<body" not in text:
        raise RuntimeError("Pandoc HTML shell is incomplete")
    head = (
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="license" content="Component rights: Habring CC BY 4.0; Becker/Krock MIT License; original edition layer CC BY-SA 4.0">\n'
        '<meta name="generator" content="OpenAI Codex gpt-5.6-sol, Ultra">\n'
        "<style>\n"
        + HTML_CSS.strip()
        + "\n</style>\n"
    )
    text = text.replace("</head>", head + "</head>", 1)
    text = normalize_math_and_ids(text)
    registry = image_hash_registry()
    usage = {name: 0 for name in IMAGE_DESCRIPTIONS}
    description_index = 0

    def patch_figure(match: re.Match[str]) -> str:
        nonlocal description_index
        block = match.group(0)
        descriptions: list[tuple[str, str]] = []

        def patch_image(image_match: re.Match[str]) -> str:
            nonlocal description_index
            tag = image_match.group(0)
            src_match = re.search(r'\bsrc="([^"]+)"', tag, re.IGNORECASE)
            if not src_match:
                raise RuntimeError("HTML image lacks src")
            digest = bytes_sha(data_uri_payload(html.unescape(src_match.group(1))))
            if digest not in registry:
                raise RuntimeError(f"Unregistered embedded raster: {digest}")
            filename, description = registry[digest]
            usage[filename] += 1
            description_index += 1
            desc_id = f"longdesc-integrated-{description_index:02d}"
            alt = html.escape(description.split(".")[0] + ".", quote=True)
            if re.search(r'\balt="[^"]*"', tag, re.IGNORECASE):
                tag = re.sub(r'\balt="[^"]*"', f'alt="{alt}"', tag, count=1, flags=re.IGNORECASE)
            else:
                tag = tag[:-1] + f' alt="{alt}">'
            if re.search(r'\baria-describedby="[^"]*"', tag, re.IGNORECASE):
                tag = re.sub(
                    r'\baria-describedby="[^"]*"',
                    f'aria-describedby="{desc_id}"',
                    tag,
                    count=1,
                    flags=re.IGNORECASE,
                )
            else:
                tag = tag[:-1] + f' aria-describedby="{desc_id}">'
            descriptions.append((desc_id, description))
            return tag

        block = re.sub(r"<img\b[^>]*>", patch_image, block, flags=re.IGNORECASE)
        if descriptions:
            appended = "\n".join(
                f'<p class="long-description" id="{desc_id}"><strong>Deskripsi rinci:</strong> '
                f"{html.escape(description)}</p>"
                for desc_id, description in descriptions
            )
            # In HTML/EPUB the figcaption must be the first or last child of a
            # figure.  Insert the detailed description immediately before the
            # caption, so the caption remains the final child.
            caption_at = block.find("<figcaption")
            if caption_at >= 0:
                block = block[:caption_at] + appended + "\n" + block[caption_at:]
            else:
                block = block.replace("</figure>", appended + "\n</figure>", 1)
        return block

    text = re.sub(r"<figure\b.*?</figure>", patch_figure, text, flags=re.DOTALL | re.IGNORECASE)
    if any(count != 1 for count in usage.values()):
        raise RuntimeError(f"Every registered raster must appear exactly once: {usage}")
    if re.search(r"<img\b", re.sub(r"<figure\b.*?</figure>", "", text, flags=re.DOTALL | re.IGNORECASE), re.IGNORECASE):
        raise RuntimeError("Image outside a semantic figure")

    text = re.sub(
        r'<html\b([^>]*)\blang="[^"]*"',
        r'<html\1lang="id-ID"',
        text,
        count=1,
        flags=re.IGNORECASE,
    )
    text = text.replace("<body>", '<body>\n<a class="skip-link" href="#main-content">Langsung ke isi utama</a>', 1)
    text = text.replace('<header id="title-block-header">', '<header id="title-block-header" role="banner">', 1)
    text = text.replace('<nav id="TOC" role="doc-toc">', '<nav id="TOC" role="doc-toc" aria-label="Daftar isi">', 1)
    nav_end = text.find("</nav>")
    if nav_end < 0:
        raise RuntimeError("Integrated HTML lacks a table-of-contents navigation landmark")
    nav_end += len("</nav>")
    text = text[:nav_end] + '\n<main id="main-content" tabindex="-1">' + text[nav_end:]
    footer = (
        '</main>\n<footer role="contentinfo"><p>Hak komponen tetap terpisah: '
        'Habring—CC BY 4.0; Becker/Krock—Lisensi MIT; lapisan asli edisi—CC BY-SA 4.0. '
        'Edisi mandiri; tidak ada dukungan resmi.</p></footer>\n'
    )
    text = text.replace("</body>", footer + "</body>", 1)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


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
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)


def resolve_member(base: str, reference: str) -> str:
    parsed = urlsplit(html.unescape(reference))
    if parsed.scheme or reference.startswith("//"):
        return ""
    decoded = unquote(parsed.path)
    if not decoded:
        return base
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), decoded))


def patch_epub_xhtml(extracted: Path) -> dict[str, object]:
    registry = image_hash_registry()
    member_hashes = {
        path.resolve(): sha256(path)
        for path in extracted.rglob("*")
        if path.is_file()
    }
    usage = {name: 0 for name in IMAGE_DESCRIPTIONS}
    desc_index = 0
    xhtml_paths = sorted(extracted.rglob("*.xhtml"))
    for xhtml in xhtml_paths:
        text = xhtml.read_text(encoding="utf-8")
        text = re.sub(r'xml:lang="[^"]*"', 'xml:lang="id-ID"', text)
        text = re.sub(r'(?<!xml:)lang="[^"]*"', 'lang="id-ID"', text)
        text = normalize_math_and_ids(text)

        def patch_figure(match: re.Match[str]) -> str:
            nonlocal desc_index
            block = match.group(0)
            descriptions: list[tuple[str, str]] = []

            def patch_image(image_match: re.Match[str]) -> str:
                nonlocal desc_index
                tag = image_match.group(0)
                src_match = re.search(r'\bsrc="([^"]+)"', tag, re.IGNORECASE)
                if not src_match:
                    raise RuntimeError(f"EPUB image lacks src in {xhtml.name}")
                source = html.unescape(src_match.group(1))
                target = (xhtml.parent / PurePosixPath(unquote(urlsplit(source).path))).resolve()
                digest = member_hashes.get(target, "")
                if digest not in registry:
                    raise RuntimeError(f"Unregistered EPUB raster in {xhtml.name}: {source}")
                filename, description = registry[digest]
                usage[filename] += 1
                desc_index += 1
                desc_id = f"longdesc-integrated-{desc_index:02d}"
                alt = html.escape(description.split(".")[0] + ".", quote=True)
                if re.search(r'\balt="[^"]*"', tag, re.IGNORECASE):
                    tag = re.sub(r'\balt="[^"]*"', f'alt="{alt}"', tag, count=1, flags=re.IGNORECASE)
                else:
                    tag = tag[:-2] + f' alt="{alt}" />' if tag.endswith("/>") else tag[:-1] + f' alt="{alt}">'
                if re.search(r'\baria-describedby="[^"]*"', tag, re.IGNORECASE):
                    tag = re.sub(
                        r'\baria-describedby="[^"]*"', f'aria-describedby="{desc_id}"', tag,
                        count=1, flags=re.IGNORECASE,
                    )
                else:
                    tag = tag[:-2] + f' aria-describedby="{desc_id}" />' if tag.endswith("/>") else tag[:-1] + f' aria-describedby="{desc_id}">'
                descriptions.append((desc_id, description))
                return tag

            block = re.sub(r"<img\b[^>]*>", patch_image, block, flags=re.IGNORECASE)
            if descriptions:
                appended = "\n".join(
                    f'<p class="long-description" id="{desc_id}"><strong>Deskripsi rinci:</strong> '
                    f"{html.escape(description)}</p>"
                    for desc_id, description in descriptions
                )
                caption_at = block.find("<figcaption")
                if caption_at >= 0:
                    block = block[:caption_at] + appended + "\n" + block[caption_at:]
                else:
                    block = block.replace("</figure>", appended + "\n</figure>", 1)
            return block

        text = re.sub(r"<figure\b.*?</figure>", patch_figure, text, flags=re.DOTALL | re.IGNORECASE)
        is_nav = bool(re.search(r'<nav\b[^>]*epub:type="toc"', text, re.IGNORECASE))
        if is_nav:
            text = re.sub(
                r'(<nav\b[^>]*epub:type="toc"[^>]*)(>)',
                lambda m: m.group(1) + (' aria-label="Daftar isi"' if "aria-label=" not in m.group(1) else "") + m.group(2),
                text,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            body_match = re.search(r"<body\b[^>]*>", text, re.IGNORECASE)
            if not body_match:
                raise RuntimeError(f"XHTML body missing in {xhtml.name}")
            insert_at = body_match.end()
            text = text[:insert_at] + '\n<a class="skip-link" href="#main-content">Langsung ke isi utama</a>\n<main id="main-content" epub:type="bodymatter">' + text[insert_at:]
            text = text.replace("</body>", "</main>\n</body>", 1)
        xhtml.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    if any(count != 1 for count in usage.values()):
        raise RuntimeError(f"Every registered EPUB raster must appear exactly once: {usage}")
    return {"image_usage": usage, "xhtml_member_count": len(xhtml_paths)}


def repair_cross_document_links(extracted: Path) -> None:
    paths = sorted(extracted.rglob("*.xhtml"))
    member_for_path = {path: path.relative_to(extracted).as_posix() for path in paths}
    owners: dict[str, list[str]] = {}
    texts = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        texts[path] = text
        member = member_for_path[path]
        for identifier in re.findall(r'\bid="([^"]+)"', text):
            owners.setdefault(html.unescape(identifier), []).append(member)
    for path in paths:
        member = member_for_path[path]

        def retarget(match: re.Match[str]) -> str:
            quote = match.group(1)
            reference = html.unescape(match.group(2))
            parsed = urlsplit(reference)
            if parsed.scheme or reference.startswith("//") or not parsed.fragment:
                return match.group(0)
            target = resolve_member(member, reference)
            fragment = unquote(parsed.fragment)
            if target in owners.get(fragment, []):
                return match.group(0)
            candidates = owners.get(fragment, [])
            if len(candidates) != 1:
                return match.group(0)
            relative = posixpath.relpath(candidates[0], posixpath.dirname(member))
            return f'href={quote}{html.escape(relative + "#" + parsed.fragment, quote=True)}{quote}'

        text = re.sub(r'href=(["\'])(.*?)\1', retarget, texts[path], flags=re.IGNORECASE)
        path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def patch_opf_and_nav(extracted: Path) -> dict[str, object]:
    container = ET.fromstring((extracted / "META-INF" / "container.xml").read_bytes())
    rootfiles = container.findall(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
    if len(rootfiles) != 1:
        raise RuntimeError("EPUB container must identify exactly one OPF rootfile")
    rootfile = rootfiles[0].attrib["full-path"]
    opf_path = extracted / PurePosixPath(rootfile)
    text = opf_path.read_text(encoding="utf-8")
    text = re.sub(
        r'(<meta\b[^>]*property="dcterms:modified"[^>]*>)[^<]*(</meta>)',
        rf"\g<1>{FIXED_MODIFIED}\g<2>",
        text,
    )
    text = re.sub(
        r"<dc:rights\b[^>]*>.*?</dc:rights>",
        "<dc:rights>Hak komponen terpisah: Habring—CC BY 4.0; Becker/Krock—Lisensi MIT; lapisan asli edisi—CC BY-SA 4.0. Tidak ada lisensi payung.</dc:rights>",
        text,
        count=1,
        flags=re.DOTALL,
    )
    accessibility_values = (
        ("schema:accessMode", "textual"),
        ("schema:accessMode", "visual"),
        ("schema:accessModeSufficient", "textual"),
        ("schema:accessibilityFeature", "MathML"),
        ("schema:accessibilityFeature", "structuralNavigation"),
        ("schema:accessibilityFeature", "alternativeText"),
        ("schema:accessibilityHazard", "none"),
        (
            "schema:accessibilitySummary",
            "Pembaca reflow dengan struktur tajuk, navigasi, MathML beranotasi TeX, teks alternatif, dan deskripsi gambar rinci.",
        ),
    )
    additions = []
    for prop, value in accessibility_values:
        marker = rf'<meta\b[^>]*property="{re.escape(prop)}"[^>]*>\s*{re.escape(value)}\s*</meta>'
        if not re.search(marker, text, re.DOTALL):
            additions.append(f'<meta property="{prop}">{html.escape(value)}</meta>')
    if additions:
        text = text.replace("</metadata>", "\n".join(additions) + "\n</metadata>", 1)
    text = re.sub(r'xml:lang="[^"]*"', 'xml:lang="id-ID"', text)
    opf_path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")

    nav_candidates = []
    opf = ET.fromstring(opf_path.read_bytes())
    ns = {"opf": "http://www.idpf.org/2007/opf"}
    for item in opf.findall(".//opf:item", ns):
        if "nav" in item.attrib.get("properties", "").split():
            nav_candidates.append(opf_path.parent / PurePosixPath(item.attrib["href"]))
    if len(nav_candidates) != 1:
        raise RuntimeError(f"Expected one EPUB navigation document, got {nav_candidates}")
    nav_path = nav_candidates[0]
    nav = nav_path.read_text(encoding="utf-8")
    if 'epub:type="landmarks"' not in nav:
        first_content = next(
            path for path in sorted(extracted.rglob("*.xhtml")) if path != nav_path
        )
        href = posixpath.relpath(
            first_content.relative_to(extracted).as_posix(),
            posixpath.dirname(nav_path.relative_to(extracted).as_posix()),
        )
        landmarks = (
            '<nav epub:type="landmarks" aria-label="Penanda">\n'
            '<h1>Penanda</h1><ol><li>'
            f'<a epub:type="bodymatter" href="{html.escape(href, quote=True)}">Isi utama</a>'
            '</li></ol></nav>\n'
        )
        nav = nav.replace("</body>", landmarks + "</body>", 1)
    nav_path.write_text(nav.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    return {"rootfile": rootfile, "nav_path": nav_path.relative_to(extracted).as_posix()}


def normalized_zip(extracted: Path, destination: Path) -> None:
    files = sorted(
        (path for path in extracted.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(extracted).as_posix(),
    )
    mimetype = extracted / "mimetype"
    if not mimetype.is_file() or mimetype.read_bytes() != b"application/epub+zip":
        raise RuntimeError("Invalid EPUB mimetype member")
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


def pandoc_epub_raw(destination: Path) -> list[str]:
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = "1787788800"
    return run(
        [
            "pandoc",
            str(COMBINED_TEX),
            "--from=latex",
            "--to=epub3",
            "--toc",
            "--toc-depth=3",
            "--split-level=1",
            "--mathml",
            "--citeproc",
            f"--bibliography={BIBLIOGRAPHY}",
            f"--css={EPUB_CSS}",
            f"--resource-path={resource_path()}",
            "--metadata=lang:id-ID",
            f"--metadata=title:{TITLE}",
            "--metadata=author:Andreas Habring; Stephen Becker; Mitchell Krock; edisi mandiri",
            f"--metadata=identifier:{IDENTIFIER}",
            "--metadata=rights:Hak komponen terpisah: Habring—CC BY 4.0; Becker/Krock—Lisensi MIT; lapisan asli edisi—CC BY-SA 4.0.",
            "--metadata=publisher:Edisi Bahasa Indonesia mandiri",
            f"--output={destination}",
        ],
        env=env,
    )


def build_epub_once(destination: Path, index: int) -> dict[str, object]:
    raw = TMP_DIR / f"integrated-reader.raw-{index}.epub"
    extracted = TMP_DIR / f"epub-extract-{index}"
    warnings = pandoc_epub_raw(raw)
    safe_extract(raw, extracted)
    xhtml = patch_epub_xhtml(extracted)
    repair_cross_document_links(extracted)
    package = patch_opf_and_nav(extracted)
    normalized_zip(extracted, destination)
    return {"pandoc_warnings": warnings, **xhtml, **package}


def main() -> None:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir(parents=True)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_EPUB.parent.mkdir(parents=True, exist_ok=True)
    EPUB_CSS.write_text(EPUB_CSS_TEXT.strip() + "\n", encoding="utf-8", newline="\n")

    source_info = collect_source_info()
    combined_info = build_combined_source(source_info)

    html_warnings_1 = pandoc_html(HTML_FIRST)
    html_warnings_2 = pandoc_html(HTML_SECOND)
    if HTML_FIRST.read_bytes() != HTML_SECOND.read_bytes():
        raise RuntimeError("Two integrated HTML builds were not byte-identical")
    shutil.copyfile(HTML_SECOND, OUTPUT_HTML)

    epub_info_1 = build_epub_once(EPUB_FIRST, 1)
    epub_info_2 = build_epub_once(EPUB_SECOND, 2)
    if EPUB_FIRST.read_bytes() != EPUB_SECOND.read_bytes():
        raise RuntimeError("Two normalized integrated EPUB builds were not byte-identical")
    shutil.copyfile(EPUB_SECOND, OUTPUT_EPUB)

    report = {
        "schema": "o015-integrated-readers-build-v1",
        "result": "pass",
        "canonical_order": [name for _, names in GROUPS for name in names] + list(ORIGINAL_03_MODULES),
        "inputs": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in (*SOURCE_PATHS, BIBLIOGRAPHY)
        ],
        "source": {
            "file_count": len(SOURCE_PATHS),
            "label_count": len(source_info["labels"]),
            "environment_counts": source_info["environment_counts"],
            **combined_info,
        },
        "artifacts": {
            "html": {
                "path": OUTPUT_HTML.relative_to(ROOT).as_posix(),
                "bytes": OUTPUT_HTML.stat().st_size,
                "sha256": sha256(OUTPUT_HTML),
            },
            "epub": {
                "path": OUTPUT_EPUB.relative_to(ROOT).as_posix(),
                "bytes": OUTPUT_EPUB.stat().st_size,
                "sha256": sha256(OUTPUT_EPUB),
            },
        },
        "pandoc": {
            "version": subprocess.run(["pandoc", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0],
            "html_warnings_build_1": html_warnings_1,
            "html_warnings_build_2": html_warnings_2,
            "epub_warnings_build_1": epub_info_1["pandoc_warnings"],
            "epub_warnings_build_2": epub_info_2["pandoc_warnings"],
        },
        "epub_build": {
            "xhtml_member_count": epub_info_2["xhtml_member_count"],
            "image_usage": epub_info_2["image_usage"],
            "rootfile": epub_info_2["rootfile"],
            "nav_path": epub_info_2["nav_path"],
        },
        "determinism": {
            "html_builds": 2,
            "html_byte_identical": True,
            "epub_builds": 2,
            "epub_byte_identical": True,
            "epub_zip_timestamps": "1980-01-01T00:00:00",
            "epub_modified": FIXED_MODIFIED,
        },
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
