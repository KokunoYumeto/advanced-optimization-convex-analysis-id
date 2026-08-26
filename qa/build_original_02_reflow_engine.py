#!/usr/bin/env python3
"""Build and validate deterministic HTML and EPUB 3 readers for Original 01.

The builder consumes the live wrapper, chapter, and four laboratory artifacts.
It performs two clean builds of each deliverable, compares the resulting bytes,
and writes separate deterministic QA receipts for the canonical HTML and EPUB.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import html
import io
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ENGINE_SCRIPT = Path(__file__).resolve()
SCRIPT = ENGINE_SCRIPT
SOURCE_DIR = ROOT / "source" / "id-ID"
WRAPPER = SOURCE_DIR / "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
BODY = SOURCE_DIR / "original-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
LAB_DIR = ROOT / "labs" / "original-01"
LAB_SCRIPT = LAB_DIR / "stochastic-composite-lab.py"
LAB_JSON = LAB_DIR / "results.json"
LAB_CSV = LAB_DIR / "results.csv"
LAB_SVG = LAB_DIR / "objective-gap.svg"
LAB_FILES = (LAB_SCRIPT, LAB_JSON, LAB_CSV, LAB_SVG)

TMP_DIR = ROOT / "tmp" / "original-01-reflow"
COMBINED_TEX = TMP_DIR / "original-01-reflow.tex"
EPUB_CSS = TMP_DIR / "original-01-reflow.css"
HTML_RUNS = (TMP_DIR / "html-run-1.html", TMP_DIR / "html-run-2.html")
EPUB_RUNS = (TMP_DIR / "epub-run-1.epub", TMP_DIR / "epub-run-2.epub")
HTML_OUTPUT = ROOT / "output" / "html" / "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html"
EPUB_OUTPUT = ROOT / "output" / "epub" / "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub"
HTML_REPORT = ROOT / "qa" / "ORIGINAL_01_HTML_BUILD.json"
EPUB_REPORT = ROOT / "qa" / "ORIGINAL_01_EPUB_BUILD.json"

TITLE = (
    "Optimisasi Lanjut dan Analisis Konveks — Tranche Asli 1: "
    "Metode Stokastik Komposit, Cermin, dan Minibatch"
)
AUTHOR = "Lapisan penyelesaian kursus mandiri"
UNIT_ID = "d90.orig.v1.tr01.unit"
EDITION_ID = "d90.orig.v1.tr01.edition.id-ID"
IDENTIFIER = "urn:uuid:ddc408f0-c3df-58f4-a759-0a1c0bb2ea8a"
FIXED_DATE = "2026-08-25"
FIXED_MODIFIED = "2026-08-25T00:00:00Z"
SOURCE_DATE_EPOCH = "1787616000"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"
RIGHTS = (
    "Mixed rights: new Original-01 content CC BY-SA 4.0; "
    "shinybook.cls and macros-id.tex CC BY 4.0"
)
LAB_ALT = (
    "Grafik logaritmik kesenjangan objektif terhadap jumlah evaluasi gradien "
    "komponen untuk Proks-SGD, Proks-minibatch, dan Prox-SAGA; seluruh nilai "
    "tersedia dalam tabel data lengkap, CSV, dan JSON."
)

ENVIRONMENTS = ("theorem", "lemma", "cor", "prop", "exercise", "proof")
ENVIRONMENT_NAMES = {
    "theorem": "Teorema",
    "lemma": "Lemma",
    "cor": "Korolari",
    "prop": "Proposisi",
    "exercise": "Latihan",
}
LAB_MEDIA_TYPES = {
    "stochastic-composite-lab.py": "text/x-python",
    "results.json": "application/json",
    "results.csv": "text/csv",
    "objective-gap.svg": "image/svg+xml",
}
EPUB_LAB_ANCHORS = {
    "stochastic-composite-lab.py": "kode-program-python-lengkap",
    "results.json": "hasil-json-lengkap",
    "results.csv": "hasil-csv-lengkap",
    "objective-gap.svg": "grafik-kesenjangan-objektif",
}
REQUIRED_MARKERS = (
    "Tentang tranche ini",
    "Metode Stokastik Komposit, Cermin, dan Minibatch",
    "Gradien proksimal stokastik",
    "Ketaksamaan satu langkah",
    "Batas ergodik proksimal stokastik",
    "Koreksi populasi hingga",
    "Penurunan cermin stokastik",
    "Ketaksamaan tiga titik stokastik",
    "Batas ergodik cermin stokastik",
    "Simpleks dan pembaruan eksponensial",
    "Penghubung varians untuk Prox-SAGA",
    "Laboratorium 1",
    "Tugas laboratorium",
    "konfigurasi beku yang dicatat pada berkas hasil",
    "Latihan, petunjuk, dan solusi lengkap",
    "Petunjuk bertahap",
    "Solusi lengkap",
    "Peta asumsi dan batas klaim",
    "Rujukan matematis dan saksi verifikasi",
    "Lampiran laboratorium lengkap",
    "Kode program Python lengkap",
    "Hasil JSON lengkap",
    "Hasil CSV lengkap",
    "Hak, atribusi, dan nondukungan",
    "Catatan aksesibilitas",
    "Creative Commons Attribution-ShareAlike 4.0 International",
    "Creative Commons Attribution 4.0 International",
    "Christian Clason",
    "OpenAI Codex gpt-5.6-sol, Ultra",
)

EXPECTED_SEGMENTS = tuple(f"d90.orig.v1.tr01.seg{index:04d}" for index in range(1, 9))
EXPECTED_ENVIRONMENT_COUNTS = {
    "theorem": 2,
    "lemma": 2,
    "cor": 1,
    "prop": 2,
    "exercise": 6,
    "proof": 7,
}
EQUATION_LABEL_PREFIX = "orig01:eq:"
RAW_REFERENCE_PREFIX = "orig01:"
COURSE_MARKER = "Metode Stokastik Komposit, Cermin, dan Minibatch"
HTML_SCHEMA = "o015-original-01-html-build-v1"
EPUB_SCHEMA = "o015-original-01-epub-build-v1"
APPENDIX_LABEL = "orig01:appendix:lab-complete"
LAB_GRAPH_SECTION_TITLE = "Grafik kesenjangan objektif"
LAB_GRAPH_INCLUDE_PATH = "labs/original-01/objective-gap.svg"
LAB_GRAPH_CAPTION = (
    "Kesenjangan objektif terhadap evaluasi gradien komponen. Seluruh "
    "nilai tersedia dalam tabel data lengkap, CSV, dan JSON."
)
LAB_GRAPH_LABEL = "lab-objective-gap"
CSV_EXPECTED_ROWS = 39
CSV_EXPECTED_COLUMNS = 8
CSV_CAPTION = "Seluruh 38 baris hasil laboratorium dengan biaya oracle tetap"
EXPECTED_HINT_COUNT = 6
EXPECTED_SOLUTION_COUNT = 6
REQUIRED_BODY_MARKER = "konfigurasi\n    beku yang dicatat pada berkas hasil"
HTML_MATH_DUPLICATION = 0
EPUB_MATH_DUPLICATION = 0

MATH_MACROS = r"""
\newcommand{\R}{\mathbb{R}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\norm}[1]{\left\lVert #1\right\rVert}
\newcommand{\inner}[2]{\left\langle #1,#2\right\rangle}
\newcommand{\prox}{\operatorname{prox}}
\newcommand{\dom}{\operatorname{dom}}
\newcommand{\Oc}{\mathcal{O}}
"""

HTML_CSS = r"""
:root {
  color-scheme: light;
  --ink: #182235;
  --muted: #536176;
  --rule: #cbd5e1;
  --accent: #285b91;
  --panel: #f4f7fb;
  --proof: #fafbfc;
  --max: 76rem;
}
* { box-sizing: border-box; }
html { font-size: 100%; scroll-behavior: smooth; }
body {
  margin: 0;
  width: 100%;
  max-width: none;
  overflow-x: clip;
  color: var(--ink);
  background: #fff;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1rem, .96rem + .18vw, 1.12rem);
  line-height: 1.64;
  overflow-wrap: break-word;
}
.skip-link {
  position: fixed;
  z-index: 100;
  top: .35rem;
  left: .35rem;
  padding: .6rem .8rem;
  color: #fff;
  background: #123d69;
  transform: translateY(-180%);
}
.skip-link:focus { transform: translateY(0); }
main#reader {
  width: min(calc(100% - 2.2rem), var(--max));
  min-width: 0;
  margin-inline: auto;
  padding: 0 0 3rem;
}
header#title-block-header {
  padding: 3rem 0 1.4rem;
  border-bottom: 1px solid var(--rule);
}
h1, h2, h3, h4 {
  max-width: 72ch;
  margin-inline: auto;
  color: #10243e;
  font-family: Arial, Helvetica, sans-serif;
  line-height: 1.2;
  scroll-margin-top: 1rem;
}
h1 { margin-top: 2.6rem; font-size: clamp(1.9rem, 1.35rem + 1.65vw, 2.9rem); }
header#title-block-header h1 { margin-top: 0; }
h2 { margin-top: 2.25rem; font-size: clamp(1.42rem, 1.18rem + .8vw, 2rem); }
h3 { margin-top: 1.75rem; font-size: clamp(1.18rem, 1.08rem + .35vw, 1.45rem); }
p, blockquote, pre, figure, .table-scroll { max-width: 72ch; margin-inline: auto; }
ol, ul { width: min(100%, 72ch); margin-inline: auto; padding-left: 1.6rem; }
li { max-width: 68ch; }
a { color: #174f91; text-underline-offset: .14em; }
nav#TOC {
  max-width: 72ch;
  margin: 1.5rem auto 2.5rem;
  padding: 1rem 1.25rem;
  border: 1px solid var(--rule);
  border-radius: .45rem;
  background: var(--panel);
}
nav#TOC ul { width: auto; }
.theorem, .lemma, .cor, .prop, .exercise, .proof {
  max-width: 72ch;
  margin: 1.25rem auto;
  padding: .85rem 1rem;
  border-left: .3rem solid var(--accent);
  background: var(--panel);
}
.exercise { border-left-color: #76509a; }
.proof { border-left-color: #65758c; background: var(--proof); }
blockquote {
  padding: .8rem 1rem;
  border-left: .3rem solid var(--accent);
  background: var(--panel);
}
.math-scroll, .math.display {
  display: block;
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding: .35rem 0;
  overscroll-behavior-inline: contain;
}
.math-scroll > mjx-container[display="true"] {
  overflow: visible;
}
.math.inline { display: inline; max-width: none; overflow: visible; padding: 0; }
.table-scroll {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  margin-block: 1.25rem;
  border: 1px solid var(--rule);
  overscroll-behavior-inline: contain;
}
table { width: 100%; min-width: 38rem; border-collapse: collapse; background: #fff; }
caption { padding: .75rem; font-weight: 700; text-align: left; }
th, td { padding: .45rem .6rem; border: 1px solid var(--rule); text-align: left; vertical-align: top; }
thead th { background: #eaf0f7; }
pre {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  padding: 1rem;
  border: 1px solid var(--rule);
  background: #f7f8fa;
  font-size: .88rem;
  line-height: 1.45;
  white-space: pre;
}
figure { margin-block: 1.5rem; }
img, svg { display: block; max-width: 100%; height: auto; margin-inline: auto; }
figcaption { color: var(--muted); font-size: .95rem; }
.lab-downloads code { overflow-wrap: anywhere; }
#reader-footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--rule); color: var(--muted); }
@media (max-width: 48rem) {
  main#reader { width: calc(100% - 1.1rem); }
  .theorem, .lemma, .cor, .prop, .exercise, .proof { padding: .7rem .72rem; }
  table { min-width: 34rem; }
}
@media print {
  .skip-link { display: none; }
  .math-scroll, .math.display, .table-scroll, pre { overflow: visible; }
}
"""

EPUB_CSS_TEXT = r"""
@namespace epub "http://www.idpf.org/2007/ops";
html { color: #182235; background: #fff; }
body { margin: 5%; max-width: 100%; font-family: serif; line-height: 1.55; overflow-wrap: break-word; }
main { display: block; max-width: 100%; }
h1, h2, h3, h4 { color: #10243e; font-family: sans-serif; line-height: 1.2; }
h1 { margin-top: 1.8em; }
a { color: #174f91; }
nav[epub|type~="toc"] ol { padding-left: 1.3em; }
.theorem, .lemma, .cor, .prop, .exercise, .proof {
  margin: 1.2em 0; padding: .75em .9em; border-left: .28em solid #285b91; background: #f4f7fb;
}
.exercise { border-left-color: #76509a; }
.proof { border-left-color: #65758c; background: #fafbfc; }
blockquote { margin: 1.2em 0; padding: .75em .9em; border-left: .28em solid #65758c; }
.math-scroll {
  display: block; width: 100%; max-width: 100%; overflow-x: auto; overflow-y: hidden;
}
.table-scroll { display: block; width: 100%; max-width: 100%; overflow-x: auto; margin: 1.2em 0; }
table { min-width: 36em; border-collapse: collapse; }
caption { padding: .6em; font-weight: bold; text-align: left; }
th, td { padding: .4em .52em; border: 1px solid #cbd5e1; text-align: left; vertical-align: top; }
thead th { background: #eaf0f7; }
pre { display: block; max-width: 100%; overflow-x: auto; padding: .8em; border: 1px solid #cbd5e1; background: #f7f8fa; white-space: pre; }
figure { margin: 1.4em auto; text-align: center; }
img, svg { display: block; max-width: 100%; height: auto; margin: 0 auto; }
figcaption { color: #536176; font-size: .95em; }
.lab-downloads code { overflow-wrap: anywhere; }
"""

MATHJAX_CONFIG = r"""<script>
window.MathJax = {
  tex: {
    tags: 'ams',
    macros: {
      R: '\\mathbb{R}', E: '\\mathbb{E}',
      norm: ['\\left\\lVert #1\\right\\rVert', 1],
      inner: ['\\left\\langle #1,#2\\right\\rangle', 2],
      prox: '\\operatorname{prox}', dom: '\\operatorname{dom}', Oc: '\\mathcal{O}'
    }
  },
  options: {enableMenu: true}
};
</script>"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def file_record(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def receipt_command(command: list[str]) -> list[str]:
    """Return a POSIX command trace with the local project root redacted."""

    root = ROOT.resolve().as_posix()
    return [
        re.sub(
            re.escape(root),
            "<project-root>",
            str(argument).replace("\\", "/"),
            flags=re.IGNORECASE,
        )
        for argument in command
    ]


def clean_tmp() -> None:
    resolved = TMP_DIR.resolve()
    expected_parent = (ROOT / "tmp").resolve()
    if resolved.parent != expected_parent or resolved.name != TMP_DIR.name:
        raise RuntimeError(f"Refusing to clean unexpected temporary path: {resolved}")
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir(parents=True)


def remove_tmp() -> None:
    resolved = TMP_DIR.resolve()
    expected_parent = (ROOT / "tmp").resolve()
    if resolved.parent != expected_parent or resolved.name != TMP_DIR.name:
        raise RuntimeError(f"Refusing to remove unexpected temporary path: {resolved}")
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)


def balanced_argument(text: str, command: str) -> str:
    start = text.find(command)
    if start < 0:
        raise RuntimeError(f"Required wrapper command not found: {command}")
    cursor = start + len(command)
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor >= len(text) or text[cursor] != "{":
        raise RuntimeError(f"Command lacks braced argument: {command}")
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
    raise RuntimeError(f"Unbalanced braced argument: {command}")


def plain_tex_title(value: str) -> str:
    result = value.replace("~", " ")
    result = re.sub(r"\\(?:emph|textbf|texttt)\{([^{}]*)\}", r"\1", result)
    result = result.replace(r"\'e", "é").replace(r"\^o", "ô")
    result = result.replace("--", "–")
    result = re.sub(r"\\[A-Za-z]+", "", result)
    result = result.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", result).strip()


def source_analysis(wrapper: str, body: str) -> dict[str, object]:
    segments = re.findall(r"^%\s*segment-id:\s*(\S+)\s*$", body, re.MULTILINE)
    if tuple(segments) != EXPECTED_SEGMENTS:
        raise RuntimeError(f"Unexpected segment inventory: {segments}")
    labels = re.findall(r"\\label\{([^}]+)\}", body)
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if duplicates:
        raise RuntimeError(f"Duplicate source labels: {duplicates}")
    environment_counts = {
        env: len(re.findall(rf"\\begin\{{{env}\}}", body)) for env in ENVIRONMENTS
    }
    if environment_counts != EXPECTED_ENVIRONMENT_COUNTS:
        raise RuntimeError(f"Unexpected theorem-family inventory: {environment_counts}")
    unescaped_dollars = len(re.findall(r"(?<!\\)\$", body))
    if unescaped_dollars % 2:
        raise RuntimeError("Odd number of inline-math dollar delimiters")
    display_math = sum(
        len(re.findall(rf"\\begin\{{{environment}\}}", body))
        for environment in ("equation", "multline")
    )
    math_surfaces = unescaped_dollars // 2 + display_math
    reference_text: dict[str, str] = {}
    for match in re.finditer(
        r"\\(chapter|section|subsection)\*?\{([^{}]+)\}\s*\\label\{([^}]+)\}",
        body,
        flags=re.DOTALL,
    ):
        reference_text[match.group(3)] = plain_tex_title(match.group(2))
    named_environments = tuple(env for env in ENVIRONMENTS if env != "proof")
    named_pattern = "|".join(re.escape(env) for env in named_environments)
    for match in re.finditer(
        rf"\\begin\{{({named_pattern})\}}"
        r"(?:\[([^\]]+)\])?(.*?)\\end\{\1\}",
        body,
        flags=re.DOTALL,
    ):
        label = re.search(r"\\label\{([^}]+)\}", match.group(3))
        if label:
            title = plain_tex_title(match.group(2) or ENVIRONMENT_NAMES[match.group(1)])
            reference_text[label.group(1)] = title
    equation_labels = re.findall(
        r"\\label\{(" + re.escape(EQUATION_LABEL_PREFIX) + r"[^}]+)\}", body
    )
    numbered_equations = re.finditer(
        r"\\begin\{(equation|multline)\}(.*?)\\end\{\1\}",
        body,
        flags=re.DOTALL,
    )
    for number, block in enumerate(numbered_equations, 1):
        for label in re.findall(
            r"\\label\{(" + re.escape(EQUATION_LABEL_PREFIX) + r"[^}]+)\}",
            block.group(2),
        ):
            reference_text[label] = f"({number})"
    missing_reference_names = sorted(set(labels) - set(reference_text))
    if missing_reference_names:
        raise RuntimeError(f"Source labels lack deterministic reader names: {missing_reference_names}")
    if body.count(r"\textbf{Petunjuk bertahap.}") != EXPECTED_HINT_COUNT:
        raise RuntimeError("Unexpected staged-hint count")
    if body.count(r"\textbf{Solusi lengkap.}") != EXPECTED_SOLUTION_COUNT:
        raise RuntimeError("Unexpected complete-solution count")
    if REQUIRED_BODY_MARKER and REQUIRED_BODY_MARKER not in body:
        raise RuntimeError("The required laboratory wording is absent from the live source")
    if UNIT_ID not in wrapper or EDITION_ID not in wrapper:
        raise RuntimeError("Wrapper unit or edition identity is missing")
    return {
        "segments": segments,
        "labels": labels,
        "equation_labels": equation_labels,
        "environment_counts": environment_counts,
        "math_surfaces": math_surfaces,
        "reference_text": reference_text,
        "hint_count": EXPECTED_HINT_COUNT,
        "solution_count": EXPECTED_SOLUTION_COUNT,
    }


def explicit_environment_titles(body: str) -> str:
    named_pattern = "|".join(
        re.escape(env) for env in ENVIRONMENTS if env != "proof"
    )
    pattern = re.compile(
        rf"\\begin\{{({named_pattern})\}}\[([^\]]+)\]"
    )

    def replace(match: re.Match[str]) -> str:
        environment = match.group(1)
        title = match.group(2)
        return (
            f"\\begin{{{environment}}}"
            f"\\textbf{{{ENVIRONMENT_NAMES[environment]} ({title}).}}\\par\n"
        )

    return pattern.sub(replace, body)


def inject_segment_targets(body: str, segments: list[str]) -> str:
    result = body
    for segment in segments:
        marker = f"% segment-id: {segment}"
        replacement = marker + f"\n\\hypertarget{{{segment}}}{{}}"
        if result.count(marker) != 1:
            raise RuntimeError(f"Segment marker is not unique: {segment}")
        result = result.replace(marker, replacement, 1)
    return result


def verbatim_block(payload: str) -> str:
    if r"\end{verbatim}" in payload:
        raise RuntimeError("Laboratory payload contains a verbatim terminator")
    return "\\begin{verbatim}\n" + payload.rstrip("\r\n") + "\n\\end{verbatim}\n"


def build_combined_source(wrapper: str, body: str, analysis: dict[str, object]) -> None:
    front_match = re.search(
        r"(\\chapter\*\{Tentang tranche ini\}.*?)(?=\\tableofcontents)",
        wrapper,
        flags=re.DOTALL,
    )
    back_match = re.search(
        r"\\backmatter\s*(.*?)(?=\\end\{document\})",
        wrapper,
        flags=re.DOTALL,
    )
    if not front_match or not back_match:
        raise RuntimeError("Could not recover wrapper frontmatter/backmatter")
    publishers = balanced_argument(wrapper, r"\publishers")
    publishers = publishers.replace(r"\small", "").strip()
    transformed_body = inject_segment_targets(
        explicit_environment_titles(body), analysis["segments"]  # type: ignore[arg-type]
    )
    appendix = (
        r"""
\chapter{Lampiran laboratorium lengkap}
\label{orig01:appendix:lab-complete}
Lampiran ini membawa kode dan keluaran beku laboratorium ke permukaan baca
reflow. Empat berkas asli disertakan sebagai unduhan byte-identik pada HTML
dan sebagai sumber daya termanifestasi pada EPUB; tautan EPUB menuju
representasi lengkap di dalam pembaca. Tabel dan grafik bersifat redundan:
data lengkap tetap tersedia dalam CSV dan JSON.

\section{Grafik kesenjangan objektif}
\begin{figure}
\centering
\includegraphics{labs/original-01/objective-gap.svg}
\caption{Kesenjangan objektif terhadap evaluasi gradien komponen. Seluruh
nilai tersedia dalam tabel data lengkap, CSV, dan JSON.}
\label{lab-objective-gap}
\end{figure}

\section{Tabel data lengkap}
\hypertarget{lab-csv-table}{}
Tabel berikut memuat semua baris hasil eksperimen dengan tajuk kolom yang
dapat ditelusuri oleh teknologi bantu.

\section{Berkas laboratorium byte-identik}
\hypertarget{lab-assets}{}
Daftar berikut diikat oleh ukuran byte dan SHA-256. Pada HTML tautannya
mengunduh berkas byte-identik; pada EPUB tautannya menuju representasi lengkap
di dalam pembaca, sementara salinan byte-identik tetap termanifestasi.

\section{Kode program Python lengkap}
"""
        + verbatim_block(LAB_SCRIPT.read_text(encoding="utf-8"))
        + r"""
\section{Hasil JSON lengkap}
"""
        + verbatim_block(LAB_JSON.read_text(encoding="utf-8"))
        + r"""
\section{Hasil CSV lengkap}
"""
        + verbatim_block(LAB_CSV.read_text(encoding="utf-8"))
    )
    appendix = (
        appendix.replace(
            r"\label{orig01:appendix:lab-complete}",
            f"\\label{{{APPENDIX_LABEL}}}",
        )
        .replace(r"\section{Grafik kesenjangan objektif}", f"\\section{{{LAB_GRAPH_SECTION_TITLE}}}")
        .replace(r"\includegraphics{labs/original-01/objective-gap.svg}", f"\\includegraphics{{{LAB_GRAPH_INCLUDE_PATH}}}")
        .replace(
            "Kesenjangan objektif terhadap evaluasi gradien komponen. Seluruh\n"
            "  nilai tersedia dalam tabel data lengkap, CSV, dan JSON.",
            LAB_GRAPH_CAPTION,
        )
        .replace(r"\label{lab-objective-gap}", f"\\label{{{LAB_GRAPH_LABEL}}}")
    )
    publisher_notice = (
        "\\begin{quote}\n\\textbf{Pernyataan edisi.} "
        + publishers
        + "\n\\end{quote}\n"
    )
    combined = "\n".join(
        (
            MATH_MACROS.strip(),
            publisher_notice.strip(),
            front_match.group(1).strip(),
            transformed_body.strip(),
            appendix.strip(),
            back_match.group(1).strip(),
        )
    ) + "\n"
    COMBINED_TEX.write_text(combined.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def pandoc_version() -> str:
    completed = subprocess.run(
        ["pandoc", "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.splitlines()[0]


def environment() -> dict[str, str]:
    result = os.environ.copy()
    result["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    result["TZ"] = "UTC"
    return result


def run_command(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    console = completed.stdout + completed.stderr
    if completed.returncode:
        raise RuntimeError(console)
    return {
        "command": receipt_command(command),
        "console_sha256": sha256_bytes(console.encode("utf-8")),
        "warnings": [line for line in completed.stderr.splitlines() if line.strip()],
    }


def csv_table_xhtml() -> str:
    rows = list(csv.reader(io.StringIO(LAB_CSV.read_text(encoding="utf-8"))))
    if len(rows) != CSV_EXPECTED_ROWS or len(rows[0]) != CSV_EXPECTED_COLUMNS:
        raise RuntimeError(f"Unexpected laboratory CSV shape: {len(rows)} x {len(rows[0])}")
    head = "".join(f'<th scope="col">{html.escape(cell)}</th>' for cell in rows[0])
    body_rows = []
    for row in rows[1:]:
        body_rows.append(
            "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
        )
    return (
        '<table class="lab-results-table">'
        f'<caption>{html.escape(CSV_CAPTION)}</caption>'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
    )


def lab_download_list_html(data_uri: bool, base_member: str = "", lab_members: dict[str, str] | None = None) -> str:
    items: list[str] = []
    for path in LAB_FILES:
        name = path.name
        payload = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        media_type = LAB_MEDIA_TYPES[name]
        if data_uri:
            href = f"data:{media_type};base64,{base64.b64encode(payload).decode('ascii')}"
            extra = f' download="{html.escape(name, quote=True)}"'
        else:
            if lab_members is None or name not in lab_members:
                raise RuntimeError(f"Missing packaged laboratory member: {name}")
            href = "#" + EPUB_LAB_ANCHORS[name]
            extra = ""
        items.append(
            '<li><a data-lab-path="'
            + html.escape(relative, quote=True)
            + '" href="'
            + html.escape(href, quote=True)
            + '"'
            + extra
            + "><code>"
            + html.escape(name)
            + "</code></a> — "
            + f"{len(payload)} byte; SHA-256 <code>{sha256_bytes(payload)}</code></li>"
        )
    return '<ul class="lab-downloads">' + "".join(items) + "</ul>"


def insert_after_anchor(document: str, identifier: str, payload: str) -> str:
    pattern = re.compile(
        rf'(<(?P<tag>[A-Za-z0-9]+)\b[^>]*\bid="{re.escape(identifier)}"[^>]*>.*?</(?P=tag)>)',
        flags=re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(document)
    if not match:
        raise RuntimeError(f"Generated reader lacks insertion anchor: {identifier}")
    return document[: match.end()] + "\n" + payload + document[match.end() :]


def readable_references(document: str, reference_text: dict[str, str]) -> str:
    pattern = re.compile(
        r'<a\b(?P<attrs>[^>]*\bdata-reference="(?P<label>[^"]+)"[^>]*)>.*?</a>',
        flags=re.DOTALL | re.IGNORECASE,
    )

    def replace(match: re.Match[str]) -> str:
        label = html.unescape(match.group("label"))
        if label not in reference_text:
            raise RuntimeError(f"No readable reference text for {label}")
        return f'<a{match.group("attrs")}>{html.escape(reference_text[label])}</a>'

    return pattern.sub(replace, document)


def add_table_scrollers(document: str) -> str:
    document = re.sub(
        r"<th\b(?![^>]*\bscope=)([^>]*)>",
        r'<th scope="col"\1>',
        document,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"(<table\b.*?</table>)",
        r'<div class="table-scroll" role="region" tabindex="0" aria-label="Tabel dapat digulir horizontal">\1</div>',
        document,
        flags=re.DOTALL | re.IGNORECASE,
    )


def patch_html(path: Path, analysis: dict[str, object]) -> None:
    document = path.read_text(encoding="utf-8")
    if "</head>" not in document or "<body>" not in document or "</body>" not in document:
        raise RuntimeError("Pandoc HTML output lacks document boundaries")
    document = re.sub(r'<html\b[^>]*\blang="[^"]*"', '<html lang="id-ID"', document, count=1)
    metadata = (
        f'<meta name="license" content="{html.escape(RIGHTS, quote=True)}" />\n'
        f'<meta name="unit-id" content="{UNIT_ID}" />\n'
        f'<meta name="edition-id" content="{EDITION_ID}" />\n'
        f"<style>\n{HTML_CSS.strip()}\n</style>\n"
    )
    document = document.replace("</head>", metadata + "</head>", 1)
    script_pattern = re.compile(
        rf'(?=<script\b[^>]*\bsrc="{re.escape(MATHJAX_URL)}")', re.IGNORECASE
    )
    if len(script_pattern.findall(document)) != 1:
        raise RuntimeError("Pinned MathJax script was not emitted exactly once")
    document = script_pattern.sub(MATHJAX_CONFIG + "\n", document, count=1)
    document = document.replace(
        "<body>",
        '<body>\n<a class="skip-link" href="#reader-content">Langsung ke isi utama</a>\n'
        '<main id="reader" role="main" aria-labelledby="reader-title">\n'
        '<span id="reader-content"></span>',
        1,
    )
    document = document.replace(
        "</body>",
        f'<footer id="reader-footer"><p><code>{UNIT_ID}</code> · {html.escape(RIGHTS)}</p></footer>\n'
        "</main>\n</body>",
        1,
    )
    document = re.sub(
        r'(<header\b[^>]*id="title-block-header"[^>]*>\s*<h1)([^>]*)>',
        r'\1\2 id="reader-title">',
        document,
        count=1,
        flags=re.DOTALL | re.IGNORECASE,
    )
    document = re.sub(
        r'<nav\b([^>]*\bid="TOC"[^>]*)>',
        r'<nav\1 aria-label="Daftar isi">',
        document,
        count=1,
        flags=re.IGNORECASE,
    )
    document = document.replace("<em>Proof.</em>", "<em>Bukti.</em>")

    def anchor_display(match: re.Match[str]) -> str:
        attributes, payload = match.group(1), match.group(2)
        source = html.unescape(payload)
        labels = re.findall(r"\\label\{([^}]+)\}", source)
        if len(set(labels)) > 1:
            raise RuntimeError(f"Display math contains multiple labels: {labels}")
        if labels and not re.search(r'\bid="', attributes):
            attributes += f' id="{html.escape(labels[0], quote=True)}"'
        if "math-scroll" not in attributes:
            attributes = re.sub(
                r'class="([^"]*)"', r'class="\1 math-scroll"', attributes, count=1
            )
        if not re.search(r'\btabindex=', attributes):
            attributes += ' tabindex="0" aria-label="Rumus matematika; dapat digulir horizontal"'
        return f"<span{attributes}>{payload}</span>"

    document = re.sub(
        r'<span([^>]*class="[^"]*\bmath\s+display\b[^"]*"[^>]*)>(.*?)</span>',
        anchor_display,
        document,
        flags=re.DOTALL | re.IGNORECASE,
    )
    document = readable_references(document, analysis["reference_text"])  # type: ignore[arg-type]
    document = insert_after_anchor(document, "lab-csv-table", csv_table_xhtml())
    document = insert_after_anchor(document, "lab-assets", lab_download_list_html(True))
    image_payload = LAB_SVG.read_bytes()
    image_uri = "data:image/svg+xml;base64," + base64.b64encode(image_payload).decode("ascii")

    def bind_image(match: re.Match[str]) -> str:
        tag = match.group(0)
        tag = re.sub(r'\bsrc="[^"]+"', f'src="{image_uri}"', tag, count=1)
        if re.search(r'\balt="[^"]*"', tag):
            tag = re.sub(r'\balt="[^"]*"', f'alt="{html.escape(LAB_ALT, quote=True)}"', tag, count=1)
        else:
            tag = tag[:-2] + f' alt="{html.escape(LAB_ALT, quote=True)}" />' if tag.endswith("/>") else tag[:-1] + f' alt="{html.escape(LAB_ALT, quote=True)}">'
        return tag

    images = re.findall(r"<img\b[^>]*>", document, flags=re.IGNORECASE)
    if len(images) != 1:
        raise RuntimeError(f"Expected one HTML chart image, found {len(images)}")
    document = re.sub(r"<img\b[^>]*>", bind_image, document, count=1, flags=re.IGNORECASE)
    document = add_table_scrollers(document)
    path.write_text(document.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def run_html_build(destination: Path, analysis: dict[str, object]) -> dict[str, object]:
    command = [
        "pandoc",
        str(COMBINED_TEX),
        "--from=latex",
        "--to=html5",
        "--standalone",
        "--toc",
        "--toc-depth=3",
        "--section-divs",
        f"--mathjax={MATHJAX_URL}",
        f"--resource-path={ROOT}",
        "--metadata=lang:id-ID",
        f"--metadata=title:{TITLE}",
        f"--metadata=author:{AUTHOR}",
        f"--metadata=date:{FIXED_DATE}",
        f"--output={destination}",
    ]
    run = run_command(command)
    patch_html(destination, analysis)
    run["artifact"] = file_record(destination)
    return run


def visible_text(document: str) -> str:
    without_script = re.sub(r"<(script|style)\b.*?</\1>", " ", document, flags=re.DOTALL | re.IGNORECASE)
    without_tags = re.sub(r"<[^>]+>", " ", without_script)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def validate_common_reader(document: str, analysis: dict[str, object], *, epub: bool) -> dict[str, object]:
    failures: list[str] = []
    plain = visible_text(document)
    normalized = plain.casefold()
    for marker in REQUIRED_MARKERS:
        if marker.casefold() not in normalized:
            failures.append(f"missing content marker: {marker}")
    hint_markers = len(
        re.findall(r"<strong>\s*Petunjuk bertahap\.\s*</strong>", document, flags=re.IGNORECASE)
    )
    solution_markers = len(
        re.findall(r"<strong>\s*Solusi lengkap\.\s*</strong>", document, flags=re.IGNORECASE)
    )
    if hint_markers != analysis["hint_count"]:
        failures.append("staged hint count differs from source")
    if solution_markers != analysis["solution_count"]:
        failures.append("complete-solution marker count differs from source")
    ids = re.findall(r'\bid="([^"]+)"', document)
    duplicate_ids = sorted({identifier for identifier in ids if ids.count(identifier) > 1})
    if duplicate_ids:
        failures.append(f"duplicate ids: {duplicate_ids}")
    required_ids = list(analysis["segments"]) + list(analysis["labels"])
    missing_ids = [identifier for identifier in required_ids if ids.count(identifier) != 1]
    if missing_ids:
        failures.append(f"source ids not preserved exactly once: {missing_ids}")
    class_counts = {
        env: len(re.findall(rf'class="[^"]*\b{env}\b[^"]*"', document))
        for env in ENVIRONMENTS
    }
    if class_counts != analysis["environment_counts"]:
        failures.append(
            f"theorem-family class counts differ: source={analysis['environment_counts']}, output={class_counts}"
        )
    if re.search(r">\s*\[" + re.escape(RAW_REFERENCE_PREFIX) + r"[^<]+\]\s*<", document):
        failures.append("raw source-label reference text remains")
    if epub:
        math_count = len(re.findall(r"<math\b", document, flags=re.IGNORECASE))
    else:
        math_count = len(
            re.findall(r'class="[^"]*\bmath\s+(?:inline|display)\b[^"]*"', document)
        )
    expected_math_count = analysis["math_surfaces"] + (
        EPUB_MATH_DUPLICATION if epub else HTML_MATH_DUPLICATION
    )
    if math_count != expected_math_count:
        failures.append(
            "math surface count differs: "
            f"source={analysis['math_surfaces']}, "
            f"expected_output={expected_math_count}, output={math_count}"
        )
    preless = re.sub(r"<pre\b.*?</pre>", "", document, flags=re.DOTALL | re.IGNORECASE)
    if epub:
        preless = re.sub(r"<math\b.*?</math>", "", preless, flags=re.DOTALL | re.IGNORECASE)
    else:
        preless = re.sub(
            r'<span\b[^>]*class="[^"]*\bmath\b[^"]*"[^>]*>.*?</span>',
            "",
            preless,
            flags=re.DOTALL | re.IGNORECASE,
        )
    if re.search(r"\\begin\{|\\end\{", html.unescape(preless)):
        failures.append("raw LaTeX environment leaked outside math/code")
    if failures:
        raise RuntimeError("Reader validation failed:\n- " + "\n- ".join(failures))
    return {
        "visible_text_characters": len(plain),
        "h1_count": len(re.findall(r"<h1\b", document, flags=re.IGNORECASE)),
        "h2_count": len(re.findall(r"<h2\b", document, flags=re.IGNORECASE)),
        "h3_count": len(re.findall(r"<h3\b", document, flags=re.IGNORECASE)),
        "math_surface_count": math_count,
        "source_math_surface_count": analysis["math_surfaces"],
        "navigation_math_duplication_count": expected_math_count
        - analysis["math_surfaces"],
        "source_label_count": len(analysis["labels"]),
        "preserved_source_label_count": len(analysis["labels"]),
        "segment_id_count": len(analysis["segments"]),
        "preserved_segment_id_count": len(analysis["segments"]),
        "environment_class_counts": class_counts,
        "staged_hint_count": analysis["hint_count"],
        "complete_solution_count": analysis["solution_count"],
        "failures": [],
    }


def validate_html(path: Path, analysis: dict[str, object]) -> dict[str, object]:
    document = path.read_text(encoding="utf-8")
    failures: list[str] = []
    if not re.search(r'<html\b[^>]*\blang="id-ID"', document):
        failures.append("document language is not id-ID")
    if document.count('<main id="reader"') != 1:
        failures.append("reader main landmark is not unique")
    if not re.search(r'<nav\b[^>]*\bid="TOC"[^>]*\baria-label="Daftar isi"', document):
        failures.append("labeled table-of-contents nav is missing")
    if document.count(f'src="{MATHJAX_URL}"') != 1:
        failures.append("exact pinned MathJax URL is not present once")
    external_sources = re.findall(r'\b(?:src|poster)="(https?://[^"]+)"', document)
    if external_sources != [MATHJAX_URL]:
        failures.append(f"unexpected external rendering dependencies: {external_sources}")
    if ".math-scroll" not in document or "overflow-x: auto" not in document:
        failures.append("local formula overflow CSS is missing")
    if "body {" not in document or "overflow-x: clip" not in document:
        failures.append("page-wide overflow containment is missing")
    tables = len(re.findall(r"<table\b", document, flags=re.IGNORECASE))
    scrollers = len(re.findall(r'class="table-scroll"', document))
    if tables != scrollers:
        failures.append(f"not every table has a local overflow region: tables={tables}, regions={scrollers}")
    downloads = re.findall(
        r'<a\b[^>]*data-lab-path="([^"]+)"[^>]*href="data:([^;]+);base64,([^"]+)"',
        document,
        flags=re.DOTALL,
    )
    if len(downloads) != len(LAB_FILES):
        failures.append(f"expected four embedded lab downloads, got {len(downloads)}")
    else:
        source_by_relative = {path.relative_to(ROOT).as_posix(): path for path in LAB_FILES}
        for relative, media_type, encoded in downloads:
            relative = html.unescape(relative)
            if relative not in source_by_relative:
                failures.append(f"unexpected embedded lab path: {relative}")
                continue
            payload = base64.b64decode(html.unescape(encoded))
            source = source_by_relative[relative]
            if payload != source.read_bytes() or media_type != LAB_MEDIA_TYPES[source.name]:
                failures.append(f"embedded lab bytes/media type differ: {relative}")
    image = re.search(r'<img\b[^>]*src="data:image/svg\+xml;base64,([^"]+)"[^>]*>', document)
    if not image or base64.b64decode(image.group(1)) != LAB_SVG.read_bytes():
        failures.append("embedded laboratory SVG is not byte-identical")
    if html.escape(LAB_ALT, quote=True) not in document:
        failures.append("laboratory chart alternative text is missing")
    fragments = re.findall(r'<a\b[^>]*href="#([^"]+)"', document, flags=re.IGNORECASE)
    ids = set(re.findall(r'\bid="([^"]+)"', document))
    unresolved = sorted({html.unescape(fragment) for fragment in fragments} - ids)
    if unresolved:
        failures.append(f"unresolved HTML fragments: {unresolved}")
    if failures:
        raise RuntimeError("HTML validation failed:\n- " + "\n- ".join(failures))
    common = validate_common_reader(document, analysis, epub=False)
    return {
        **common,
        "main_landmark_count": 1,
        "toc_navigation_count": 1,
        "table_count": tables,
        "local_table_overflow_region_count": scrollers,
        "embedded_lab_download_count": len(downloads),
        "embedded_lab_bytes_exact": True,
        "embedded_svg_bytes_exact": True,
        "mathjax_url": MATHJAX_URL,
        "external_rendering_dependencies": [MATHJAX_URL],
        "unresolved_internal_fragments": [],
        "responsive_single_column": True,
        "formula_overflow_local": True,
    }


def safe_extract(archive: Path, destination: Path) -> None:
    if destination.exists():
        resolved = destination.resolve()
        if resolved.parent != TMP_DIR.resolve():
            raise RuntimeError(f"Refusing to replace unexpected extraction directory: {resolved}")
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            target = (destination / PurePosixPath(info.filename)).resolve()
            if target != root and root not in target.parents:
                raise RuntimeError(f"Unsafe EPUB member path: {info.filename}")
        package.extractall(destination)


def container_rootfile(extracted: Path) -> str:
    container = extracted / "META-INF" / "container.xml"
    root = ET.fromstring(container.read_bytes())
    nodes = root.findall(
        ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
    )
    if len(nodes) != 1:
        raise RuntimeError(f"Expected one EPUB rootfile, found {len(nodes)}")
    rootfile = nodes[0].attrib.get("full-path", "")
    if not rootfile or not (extracted / PurePosixPath(rootfile)).is_file():
        raise RuntimeError(f"EPUB rootfile is absent: {rootfile}")
    return rootfile


def package_lab_resources(extracted: Path, rootfile: str) -> dict[str, str]:
    opf_path = extracted / PurePosixPath(rootfile)
    opf_dir = opf_path.parent
    package_dir = opf_dir / "lab"
    package_dir.mkdir()
    members: dict[str, str] = {}
    manifest_lines: list[str] = []
    for index, source in enumerate(LAB_FILES, 1):
        target = package_dir / source.name
        shutil.copyfile(source, target)
        if target.read_bytes() != source.read_bytes():
            raise RuntimeError(f"Packaged laboratory copy differs: {source}")
        member = target.relative_to(extracted).as_posix()
        members[source.name] = member
        manifest_lines.append(
            f'<item id="lab-resource-{index}" href="lab/{html.escape(source.name, quote=True)}" '
            f'media-type="{LAB_MEDIA_TYPES[source.name]}" />'
        )
    opf = opf_path.read_text(encoding="utf-8")
    metadata_closing = re.search(r"</(?P<prefix>[A-Za-z0-9_.-]+:)?metadata>", opf)
    if not metadata_closing:
        raise RuntimeError("OPF metadata closing tag was not found")
    metadata_prefix = metadata_closing.group("prefix") or ""
    accessibility_payload = "\n".join(
        (
            f'<{metadata_prefix}meta property="schema:accessibilityFeature">MathML</{metadata_prefix}meta>',
            f'<{metadata_prefix}meta property="schema:accessibilitySummary">Pembaca reflow berbahasa Indonesia dengan MathML, navigasi struktural, teks alternatif, serta tabel CSV/JSON yang menggandakan informasi grafik; PDF pendamping tidak bertag.</{metadata_prefix}meta>',
        )
    )
    opf = (
        opf[: metadata_closing.start()]
        + accessibility_payload
        + opf[metadata_closing.start() :]
    )
    closing = re.search(r"</(?P<prefix>[A-Za-z0-9_.-]+:)?manifest>", opf)
    if not closing:
        raise RuntimeError("OPF manifest closing tag was not found")
    prefix = closing.group("prefix") or ""
    manifest_payload = "\n".join(
        line.replace("<item ", f"<{prefix}item ", 1) for line in manifest_lines
    ) + "\n"
    opf = opf[: closing.start()] + manifest_payload + opf[closing.start() :]
    opf_path.write_text(opf.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    return members


def epub_fragment(value: str) -> str:
    fragment = re.sub(r"\s+", "-", value.strip())
    fragment = re.sub(r"[^A-Za-z0-9_.:-]", "-", fragment)
    return fragment or "label"


def patch_epub_xhtml(
    extracted: Path,
    rootfile: str,
    lab_members: dict[str, str],
    analysis: dict[str, object],
) -> None:
    image_count = 0
    table_injected = False
    downloads_injected = False
    for xhtml_path in sorted(extracted.rglob("*.xhtml")):
        member = xhtml_path.relative_to(extracted).as_posix()
        document = xhtml_path.read_text(encoding="utf-8")
        document = re.sub(r'xml:lang="[^"]*"', 'xml:lang="id-ID"', document)
        document = re.sub(r'(?<!xml:)lang="[^"]*"', 'lang="id-ID"', document)

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
                raise RuntimeError(f"MathML surface contains multiple labels in {member}: {labels}")
            if labels:
                opening_end = block.find(">")
                opening = block[: opening_end + 1]
                if not re.search(r'\bid="', opening):
                    block = block[:opening_end] + f' id="{html.escape(epub_fragment(labels[0]), quote=True)}"' + block[opening_end:]
            block = re.sub(
                r'<annotation\b[^>]*encoding="application/x-tex"[^>]*>.*?</annotation>',
                "",
                block,
                flags=re.DOTALL | re.IGNORECASE,
            )
            if re.search(r'<math\b[^>]*\bdisplay="block"', block, flags=re.IGNORECASE):
                return (
                    '<span class="math-scroll" tabindex="0" '
                    'aria-label="Rumus matematika; dapat digulir horizontal">'
                    + block
                    + "</span>"
                )
            return block

        document = re.sub(r"<math\b.*?</math>", normalize_math, document, flags=re.DOTALL | re.IGNORECASE)

        def normalize_id(match: re.Match[str]) -> str:
            quote, identifier = match.group(1), html.unescape(match.group(2))
            return f'id={quote}{html.escape(epub_fragment(identifier), quote=True)}{quote}'

        document = re.sub(r'id=(["\'])(.*?)\1', normalize_id, document, flags=re.IGNORECASE)

        def normalize_href(match: re.Match[str]) -> str:
            quote, reference = match.group(1), html.unescape(match.group(2))
            parsed = urlsplit(reference)
            if parsed.scheme or reference.startswith("//") or not parsed.fragment:
                return match.group(0)
            prefix = reference.split("#", 1)[0]
            normalized = epub_fragment(unquote(parsed.fragment))
            return f'href={quote}{html.escape(prefix + "#" + normalized, quote=True)}{quote}'

        document = re.sub(r'href=(["\'])(.*?)\1', normalize_href, document, flags=re.IGNORECASE)
        document = readable_references(document, analysis["reference_text"])  # type: ignore[arg-type]
        document = document.replace("<em>Proof.</em>", "<em>Bukti.</em>")
        if "lab-csv-table" in document:
            if table_injected:
                raise RuntimeError("Laboratory table anchor appeared in multiple XHTML members")
            document = insert_after_anchor(document, "lab-csv-table", csv_table_xhtml())
            table_injected = True
        if "lab-assets" in document:
            if downloads_injected:
                raise RuntimeError("Laboratory asset anchor appeared in multiple XHTML members")
            document = insert_after_anchor(
                document,
                "lab-assets",
                lab_download_list_html(False, member, lab_members),
            )
            downloads_injected = True

        def bind_image(match: re.Match[str]) -> str:
            nonlocal image_count
            image_count += 1
            tag = match.group(0)
            if re.search(r'\balt="[^"]*"', tag):
                return re.sub(
                    r'\balt="[^"]*"',
                    f'alt="{html.escape(LAB_ALT, quote=True)}"',
                    tag,
                    count=1,
                )
            if tag.endswith("/>"):
                return tag[:-2] + f' alt="{html.escape(LAB_ALT, quote=True)}" />'
            return tag[:-1] + f' alt="{html.escape(LAB_ALT, quote=True)}">'

        document = re.sub(r"<img\b[^>]*>", bind_image, document, flags=re.IGNORECASE)
        document = add_table_scrollers(document)
        is_navigation = bool(
            re.search(r'<nav\b[^>]*(?:epub:type="toc"|role="doc-toc")', document, flags=re.IGNORECASE)
        )
        if is_navigation:
            document = re.sub(
                r'<nav\b([^>]*(?:epub:type="toc"|role="doc-toc")[^>]*)>',
                r'<nav\1 aria-label="Daftar isi">',
                document,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            body_open = re.search(r"<body\b[^>]*>", document, flags=re.IGNORECASE)
            if not body_open or "</body>" not in document:
                raise RuntimeError(f"XHTML body boundary missing in {member}")
            document = document[: body_open.end()] + '\n<main epub:type="bodymatter">' + document[body_open.end() :]
            document = document.replace("</body>", "</main>\n</body>", 1)
        xhtml_path.write_text(document.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    if image_count != 1:
        raise RuntimeError(f"Expected one EPUB chart image use, found {image_count}")
    if not table_injected or not downloads_injected:
        raise RuntimeError("Laboratory table or download list was not injected")


def repair_cross_document_fragments(extracted: Path) -> None:
    paths = sorted(extracted.rglob("*.xhtml"))
    members = {path: path.relative_to(extracted).as_posix() for path in paths}
    owners: dict[str, list[str]] = {}
    texts: dict[Path, str] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        texts[path] = text
        member = members[path]
        for identifier in re.findall(r'\bid="([^"]+)"', text):
            owners.setdefault(html.unescape(identifier), []).append(member)
    for path in paths:
        member = members[path]

        def retarget(match: re.Match[str]) -> str:
            quote, reference = match.group(1), html.unescape(match.group(2))
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


def normalize_epub_metadata(extracted: Path) -> None:
    for path in sorted(extracted.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".xml", ".opf", ".ncx"}:
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r'(<meta\b[^>]*property="dcterms:modified"[^>]*>)[^<]*(</meta>)',
            rf"\g<1>{FIXED_MODIFIED}\g<2>",
            text,
        )
        text = re.sub(r'xml:lang="[^"]*"', 'xml:lang="id-ID"', text)
        path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def declare_epub_mathml_properties(extracted: Path, rootfile: str) -> int:
    """Make each XHTML manifest declaration agree with its actual MathML use."""
    opf_path = extracted / PurePosixPath(rootfile)
    opf = opf_path.read_text(encoding="utf-8")
    declared = 0

    def patch_item(match: re.Match[str]) -> str:
        nonlocal declared
        tag = match.group(0)
        media = re.search(r'\bmedia-type=(["\'])(.*?)\1', tag, flags=re.IGNORECASE)
        href_match = re.search(r'\bhref=(["\'])(.*?)\1', tag, flags=re.IGNORECASE)
        if not media or not href_match or media.group(2) != "application/xhtml+xml":
            return tag
        href = html.unescape(href_match.group(2))
        member = resolve_member(rootfile, href)
        target = extracted / PurePosixPath(member)
        if not target.is_file():
            raise RuntimeError(f"Cannot inspect manifested XHTML resource: {href}")
        contains_mathml = bool(re.search(rb"<math\b", target.read_bytes(), flags=re.IGNORECASE))
        properties_match = re.search(r'\bproperties=(["\'])(.*?)\1', tag, flags=re.IGNORECASE)
        properties = properties_match.group(2).split() if properties_match else []
        properties = [value for value in properties if value != "mathml"]
        if contains_mathml:
            properties.append("mathml")
            declared += 1
        if properties_match:
            quote = properties_match.group(1)
            replacement = f'properties={quote}{" ".join(properties)}{quote}'
            return tag[: properties_match.start()] + replacement + tag[properties_match.end() :]
        if not properties:
            return tag
        insertion = f' properties="{" ".join(properties)}"'
        closing = tag.rfind("/>")
        if closing < 0:
            closing = tag.rfind(">")
        if closing < 0:
            raise RuntimeError(f"Malformed OPF manifest item: {tag}")
        return tag[:closing] + insertion + tag[closing:]

    opf = re.sub(
        r"<(?:[A-Za-z0-9_.-]+:)?item\b[^>]*?/?>",
        patch_item,
        opf,
        flags=re.IGNORECASE,
    )
    opf_path.write_text(opf.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    return declared


def normalized_zip(extracted: Path, destination: Path) -> None:
    files = sorted(
        (path for path in extracted.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(extracted).as_posix(),
    )
    mimetype = extracted / "mimetype"
    if not mimetype.is_file() or mimetype.read_bytes() != b"application/epub+zip":
        raise RuntimeError("EPUB mimetype payload is missing or invalid")
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


def run_epub_build(destination: Path, index: int, analysis: dict[str, object]) -> dict[str, object]:
    raw = TMP_DIR / f"epub-raw-{index}.epub"
    extracted = TMP_DIR / f"epub-extract-{index}"
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
        f"--resource-path={ROOT}",
        "--metadata=lang:id-ID",
        f"--metadata=title:{TITLE}",
        f"--metadata=author:{AUTHOR}",
        f"--metadata=date:{FIXED_DATE}",
        f"--metadata=identifier:{IDENTIFIER}",
        f"--metadata=rights:{RIGHTS}",
        "--metadata=publisher:Edisi mandiri",
        f"--output={raw}",
    ]
    run = run_command(command)
    safe_extract(raw, extracted)
    rootfile = container_rootfile(extracted)
    lab_members = package_lab_resources(extracted, rootfile)
    patch_epub_xhtml(extracted, rootfile, lab_members, analysis)
    repair_cross_document_fragments(extracted)
    normalize_epub_metadata(extracted)
    run["mathml_manifest_item_count"] = declare_epub_mathml_properties(extracted, rootfile)
    normalized_zip(extracted, destination)
    run["artifact"] = file_record(destination)
    run["packaged_lab_members"] = lab_members
    return run


def resolve_member(base: str, reference: str) -> str:
    parsed = urlsplit(html.unescape(reference))
    if parsed.scheme or reference.startswith("//"):
        return ""
    decoded = unquote(parsed.path)
    if not decoded:
        return base
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), decoded))


def validate_epub(path: Path, analysis: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if not infos or infos[0].filename != "mimetype":
            failures.append("mimetype is not the first ZIP member")
        elif infos[0].compress_type != zipfile.ZIP_STORED:
            failures.append("mimetype is compressed")
        if archive.read("mimetype") != b"application/epub+zip":
            failures.append("mimetype payload is invalid")
        if len(names) != len(set(names)):
            failures.append("duplicate ZIP member names")
        unsafe = [
            name
            for name in names
            if name.startswith(("/", "\\")) or ".." in PurePosixPath(name).parts
        ]
        if unsafe:
            failures.append(f"unsafe ZIP member paths: {unsafe}")
        nonfixed = [info.filename for info in infos if info.date_time != ZIP_EPOCH]
        if nonfixed:
            failures.append(f"non-normalized ZIP timestamps: {nonfixed}")
        members = {name: archive.read(name) for name in names if not name.endswith("/")}

    xml_names = [
        name
        for name in members
        if PurePosixPath(name).suffix.lower() in {".xml", ".opf", ".ncx", ".xhtml", ".svg"}
    ]
    parsed: dict[str, ET.Element] = {}
    for name in xml_names:
        try:
            parsed[name] = ET.fromstring(members[name])
        except ET.ParseError as exc:
            failures.append(f"XML parse failure in {name}: {exc}")
    container = "META-INF/container.xml"
    rootfile = ""
    if container not in parsed:
        failures.append("container.xml is missing or invalid")
    else:
        rootfiles = parsed[container].findall(
            ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
        )
        if len(rootfiles) != 1:
            failures.append(f"container rootfile count is {len(rootfiles)}")
        else:
            rootfile = rootfiles[0].attrib.get("full-path", "")
            if rootfile not in members:
                failures.append(f"container rootfile is absent: {rootfile}")

    manifest: dict[str, tuple[str, str, str]] = {}
    manifest_members: set[str] = set()
    nav_members: list[str] = []
    spine_ids: list[str] = []
    spine_members: list[str] = []
    if rootfile in parsed:
        package = parsed[rootfile]
        ns = {
            "opf": "http://www.idpf.org/2007/opf",
            "dc": "http://purl.org/dc/elements/1.1/",
        }
        if not package.attrib.get("version", "").startswith("3"):
            failures.append(f"package is not EPUB 3: {package.attrib.get('version')}")
        metadata = package.find("opf:metadata", ns)
        if metadata is None:
            failures.append("OPF metadata is missing")
        else:
            def dc_values(local: str) -> list[str]:
                return [
                    "".join(node.itertext()).strip()
                    for node in metadata.findall(f"dc:{local}", ns)
                ]

            if dc_values("title") != [TITLE]:
                failures.append(f"unexpected dc:title: {dc_values('title')}")
            if dc_values("language") != ["id-ID"]:
                failures.append(f"unexpected dc:language: {dc_values('language')}")
            if dc_values("rights") != [RIGHTS]:
                failures.append(f"unexpected dc:rights: {dc_values('rights')}")
            identifiers = metadata.findall("dc:identifier", ns)
            fixed_nodes = [node for node in identifiers if "".join(node.itertext()).strip() == IDENTIFIER]
            unique = package.attrib.get("unique-identifier", "")
            if len(fixed_nodes) != 1 or fixed_nodes[0].attrib.get("id") != unique:
                failures.append("fixed identifier does not own package unique-identifier")
            modified = [
                "".join(node.itertext()).strip()
                for node in metadata.findall("opf:meta", ns)
                if node.attrib.get("property") == "dcterms:modified"
            ]
            if modified != [FIXED_MODIFIED]:
                failures.append(f"nonfixed dcterms:modified: {modified}")
        manifest_node = package.find("opf:manifest", ns)
        if manifest_node is None:
            failures.append("OPF manifest is missing")
        else:
            for item in manifest_node.findall("opf:item", ns):
                item_id = item.attrib.get("id", "")
                href = item.attrib.get("href", "")
                media_type = item.attrib.get("media-type", "")
                properties = item.attrib.get("properties", "")
                manifest[item_id] = (href, media_type, properties)
                member = resolve_member(rootfile, href)
                if member not in members:
                    failures.append(f"manifest resource is absent: {item_id} -> {href}")
                else:
                    manifest_members.add(member)
                if "nav" in properties.split():
                    nav_members.append(member)
                if media_type == "application/xhtml+xml" and member in members:
                    contains_mathml = bool(
                        re.search(rb"<math\b", members[member], flags=re.IGNORECASE)
                    )
                    declares_mathml = "mathml" in properties.split()
                    if contains_mathml != declares_mathml:
                        failures.append(
                            "MathML manifest-property mismatch: "
                            f"{item_id} -> {href} (contains={contains_mathml}, "
                            f"declared={declares_mathml})"
                        )
            if len(nav_members) != 1:
                failures.append(f"expected one EPUB navigation document, got {nav_members}")
        spine = package.find("opf:spine", ns)
        if spine is None:
            failures.append("OPF spine is missing")
        else:
            for itemref in spine.findall("opf:itemref", ns):
                item_id = itemref.attrib.get("idref", "")
                spine_ids.append(item_id)
                if item_id not in manifest:
                    failures.append(f"spine idref is absent from manifest: {item_id}")
                else:
                    href, media_type, _ = manifest[item_id]
                    if media_type != "application/xhtml+xml":
                        failures.append(f"non-XHTML spine item: {item_id} ({media_type})")
                    spine_members.append(resolve_member(rootfile, href))
            if not spine_ids or len(spine_ids) != len(set(spine_ids)):
                failures.append(f"empty or duplicate spine idrefs: {spine_ids}")
        allowed_unmanifested = {
            "mimetype",
            "META-INF/container.xml",
            "META-INF/com.apple.ibooks.display-options.xml",
            rootfile,
        }
        unmanifested = sorted(set(members) - manifest_members - allowed_unmanifested)
        if unmanifested:
            failures.append(f"unmanifested package resources: {unmanifested}")

    expected_lab_members = {
        (PurePosixPath(rootfile).parent / "lab" / source.name).as_posix(): source
        for source in LAB_FILES
    }
    for member, source in expected_lab_members.items():
        if member not in members or members[member] != source.read_bytes():
            failures.append(f"packaged laboratory bytes differ: {member}")
        matching = [
            item
            for item in manifest.values()
            if resolve_member(rootfile, item[0]) == member
            and item[1] == LAB_MEDIA_TYPES[source.name]
        ]
        if len(matching) != 1:
            failures.append(f"laboratory resource manifest mismatch: {member}")

    xhtml_names = sorted(name for name in members if name.endswith(".xhtml"))
    all_xhtml = "\n".join(members[name].decode("utf-8") for name in xhtml_names)
    try:
        common = validate_common_reader(all_xhtml, analysis, epub=True)
    except RuntimeError as exc:
        failures.append(str(exc))
        common = {}
    ids_by_member: dict[str, set[str]] = {}
    unresolved: list[str] = []
    image_count = 0
    alt_count = 0
    main_count = 0
    for name in xhtml_names:
        text = members[name].decode("utf-8")
        opening = re.search(r"<html\b[^>]*>", text, flags=re.IGNORECASE)
        if not opening or 'lang="id-ID"' not in opening.group(0) or 'xml:lang="id-ID"' not in opening.group(0):
            failures.append(f"XHTML language is not id-ID in {name}")
        ids_by_member[name] = set(re.findall(r'\bid="([^"]+)"', text))
        is_nav = name in nav_members
        if not is_nav:
            count = len(re.findall(r'<main\b[^>]*epub:type="bodymatter"', text))
            main_count += count
            if count != 1:
                failures.append(f"content XHTML lacks one main landmark: {name}")
        for tag in re.findall(r"<img\b[^>]*>", text, flags=re.IGNORECASE):
            image_count += 1
            alt = re.search(r'\balt="([^"]*)"', tag)
            if alt and html.unescape(alt.group(1)).strip():
                alt_count += 1
            else:
                failures.append(f"image lacks alternative text in {name}")
        for attribute, reference in re.findall(r'\b(href|src)="([^"]+)"', text, flags=re.IGNORECASE):
            reference = html.unescape(reference)
            parsed_ref = urlsplit(reference)
            if parsed_ref.scheme or reference.startswith("//"):
                continue
            target = resolve_member(name, reference)
            if parsed_ref.path and target not in members:
                unresolved.append(f"{name}: {attribute}={reference}")
                continue
            if parsed_ref.fragment:
                target_member = target if parsed_ref.path else name
                if target_member not in ids_by_member:
                    continue
                if unquote(parsed_ref.fragment) not in ids_by_member[target_member]:
                    unresolved.append(f"{name}: missing fragment {reference}")
    # Recheck fragments after every member's id inventory is known.
    unresolved = []
    for name in xhtml_names:
        text = members[name].decode("utf-8")
        for attribute, reference in re.findall(r'\b(href|src)="([^"]+)"', text, flags=re.IGNORECASE):
            reference = html.unescape(reference)
            parsed_ref = urlsplit(reference)
            if parsed_ref.scheme or reference.startswith("//"):
                continue
            target = resolve_member(name, reference)
            if parsed_ref.path and target not in members:
                unresolved.append(f"{name}: {attribute}={reference}")
            elif parsed_ref.fragment:
                target_member = target if parsed_ref.path else name
                if unquote(parsed_ref.fragment) not in ids_by_member.get(target_member, set()):
                    unresolved.append(f"{name}: missing fragment {reference}")
    if unresolved:
        failures.append(f"unresolved EPUB references: {unresolved[:20]}")
    if image_count != 1 or alt_count != 1 or html.escape(LAB_ALT, quote=True) not in all_xhtml:
        failures.append(f"chart image/alternative mismatch: images={image_count}, alts={alt_count}")
    if "<annotation" in all_xhtml:
        failures.append("TeX source annotations remain in EPUB MathML")
    if re.search(r'<span\b[^>]*class="[^"]*\bmath\s+(?:inline|display)\b', all_xhtml):
        failures.append("non-MathML formula spans remain in EPUB")
    css_members = [member for member, payload in members.items() if member.endswith(".css")]
    if len(css_members) != 1 or b".math-scroll" not in members[css_members[0]]:
        failures.append(f"EPUB formula overflow CSS mismatch: {css_members}")
    if len(nav_members) == 1 and nav_members[0] in parsed:
        nav = parsed[nav_members[0]]
        ns_x = {"x": "http://www.w3.org/1999/xhtml"}
        toc_navs = [
            node
            for node in nav.findall(".//x:nav", ns_x)
            if node.attrib.get("{http://www.idpf.org/2007/ops}type") == "toc"
            or "doc-toc" in node.attrib.get("role", "")
        ]
        if len(toc_navs) != 1:
            failures.append(f"EPUB TOC navigation count is {len(toc_navs)}")
        else:
            nav_link_count = len(toc_navs[0].findall(".//x:a", ns_x))
            if nav_link_count < 12:
                failures.append(f"EPUB navigation has too few links: {nav_link_count}")
    else:
        nav_link_count = 0
    spine_texts = [visible_text(members[name].decode("utf-8")) for name in spine_members if name in members]
    spine_joined = "\n".join(spine_texts)
    ordered_markers = [
        "Tentang tranche ini",
        COURSE_MARKER,
        "Lampiran laboratorium lengkap",
        "Hak, atribusi, dan nondukungan",
        "Catatan aksesibilitas",
    ]
    positions: list[int] = []
    cursor = 0
    for marker in ordered_markers:
        position = spine_joined.find(marker, cursor)
        positions.append(position)
        if position >= 0:
            cursor = position + len(marker)
    if any(position < 0 for position in positions):
        failures.append(f"spine reading order markers are missing/out of order: {positions}")
    if failures:
        raise RuntimeError("EPUB validation failed:\n- " + "\n- ".join(failures))
    return {
        **common,
        "zip_entry_count": len(members),
        "xml_member_count": len(xml_names),
        "xhtml_member_count": len(xhtml_names),
        "manifest_item_count": len(manifest),
        "manifest_resource_closure": True,
        "spine_item_count": len(spine_ids),
        "spine_reading_order_verified": True,
        "navigation_document_count": len(nav_members),
        "navigation_link_count": nav_link_count,
        "content_main_landmark_count": main_count,
        "mathml_count": common["math_surface_count"],
        "raw_tex_annotation_count": 0,
        "packaged_lab_resource_count": len(expected_lab_members),
        "packaged_lab_bytes_exact": True,
        "raster_or_vector_image_use_count": image_count,
        "nonempty_image_alt_count": alt_count,
        "unresolved_internal_references": [],
        "xml_parse_failures": [],
        "mimetype_first_uncompressed": True,
        "fixed_zip_timestamps": True,
        "formula_overflow_local": True,
    }


def stable_inputs() -> list[dict[str, object]]:
    paths = list(dict.fromkeys([WRAPPER, BODY, *LAB_FILES, ENGINE_SCRIPT, SCRIPT]))
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing Original-01 reflow inputs: " + ", ".join(missing))
    return [file_record(path) for path in paths]


def main() -> None:
    inputs_before = stable_inputs()
    wrapper = WRAPPER.read_text(encoding="utf-8")
    body = BODY.read_text(encoding="utf-8")
    analysis = source_analysis(wrapper, body)
    clean_tmp()
    build_combined_source(wrapper, body, analysis)
    EPUB_CSS.write_text(EPUB_CSS_TEXT.strip() + "\n", encoding="utf-8", newline="\n")

    html_runs = [run_html_build(destination, analysis) for destination in HTML_RUNS]
    if HTML_RUNS[0].read_bytes() != HTML_RUNS[1].read_bytes():
        raise RuntimeError("Two clean HTML builds are not byte-identical")
    html_validation = validate_html(HTML_RUNS[0], analysis)

    epub_runs = [
        run_epub_build(destination, index, analysis)
        for index, destination in enumerate(EPUB_RUNS, 1)
    ]
    if EPUB_RUNS[0].read_bytes() != EPUB_RUNS[1].read_bytes():
        raise RuntimeError("Two clean normalized EPUB builds are not byte-identical")
    epub_validation = validate_epub(EPUB_RUNS[0], analysis)

    if inputs_before != stable_inputs():
        raise RuntimeError("Original-01 source/wrapper/lab/builder inputs changed during clean builds")
    HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    EPUB_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HTML_RUNS[0], HTML_OUTPUT)
    shutil.copyfile(EPUB_RUNS[0], EPUB_OUTPUT)
    if HTML_OUTPUT.read_bytes() != HTML_RUNS[0].read_bytes():
        raise RuntimeError("Canonical HTML differs from validated clean build")
    if EPUB_OUTPUT.read_bytes() != EPUB_RUNS[0].read_bytes():
        raise RuntimeError("Canonical EPUB differs from validated clean build")

    shared = {
        "result": "pass",
        "inputs": inputs_before,
        "combined_source": {
            "bytes": COMBINED_TEX.stat().st_size,
            "sha256": sha256(COMBINED_TEX),
        },
        "source_inventory": {
            "segment_ids": analysis["segments"],
            "source_label_count": len(analysis["labels"]),
            "equation_label_count": len(analysis["equation_labels"]),
            "math_surface_count": analysis["math_surfaces"],
            "environment_counts": analysis["environment_counts"],
            "staged_hint_count": analysis["hint_count"],
            "complete_solution_count": analysis["solution_count"],
        },
        "tool_versions": {
            "pandoc": pandoc_version(),
            "python": sys.version.split()[0],
        },
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "upstream_contact": False,
    }
    html_report = {
        "schema": HTML_SCHEMA,
        **shared,
        "artifact": {**file_record(HTML_OUTPUT), **html_validation},
        "runs": html_runs,
        "determinism": {
            "builds": 2,
            "byte_identical": True,
            "canonical_copy_exact_match": True,
            "run_sha256": [sha256(path) for path in HTML_RUNS],
        },
    }
    epub_report = {
        "schema": EPUB_SCHEMA,
        **shared,
        "artifact": {**file_record(EPUB_OUTPUT), **epub_validation},
        "runs": epub_runs,
        "determinism": {
            "builds": 2,
            "byte_identical": True,
            "canonical_copy_exact_match": True,
            "run_sha256": [sha256(path) for path in EPUB_RUNS],
            "zip_entry_order": "mimetype first; remaining files sorted lexicographically",
            "zip_timestamps": "1980-01-01T00:00:00",
            "opf_modified": FIXED_MODIFIED,
        },
    }
    HTML_REPORT.write_text(
        json.dumps(html_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    EPUB_REPORT.write_text(
        json.dumps(epub_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "result": "pass",
                "html": file_record(HTML_OUTPUT),
                "epub": file_record(EPUB_OUTPUT),
                "html_receipt": file_record(HTML_REPORT),
                "epub_receipt": file_record(EPUB_REPORT),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    remove_tmp()


if __name__ == "__main__":
    main()
