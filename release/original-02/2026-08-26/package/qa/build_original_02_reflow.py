#!/usr/bin/env python3
"""Configure the proven Original-01 reflow engine for O015 Original-02."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve()
BASE = SCRIPT.with_name("build_original_02_reflow_engine.py")
SPEC = importlib.util.spec_from_file_location("o015_original_reflow_base", BASE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load reflow engine: {BASE}")
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)


def configure() -> None:
    root = ENGINE.ROOT
    source = root / "source" / "id-ID"
    lab = root / "labs" / "original-02"
    temporary = root / "tmp" / "original-02-reflow"

    ENGINE.SCRIPT = SCRIPT
    ENGINE.SOURCE_DIR = source
    ENGINE.WRAPPER = (
        source
        / "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
    )
    ENGINE.BODY = (
        source
        / "original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
    )
    ENGINE.LAB_DIR = lab
    ENGINE.LAB_SCRIPT = lab / "monotone-splitting-lab.py"
    ENGINE.LAB_JSON = lab / "results.json"
    ENGINE.LAB_CSV = lab / "results.csv"
    ENGINE.LAB_SVG = lab / "residual.svg"
    ENGINE.LAB_FILES = (
        ENGINE.LAB_SCRIPT,
        ENGINE.LAB_JSON,
        ENGINE.LAB_CSV,
        ENGINE.LAB_SVG,
    )

    ENGINE.TMP_DIR = temporary
    ENGINE.COMBINED_TEX = temporary / "original-02-reflow.tex"
    ENGINE.EPUB_CSS = temporary / "original-02-reflow.css"
    ENGINE.HTML_RUNS = (
        temporary / "html-run-1.html",
        temporary / "html-run-2.html",
    )
    ENGINE.EPUB_RUNS = (
        temporary / "epub-run-1.epub",
        temporary / "epub-run-2.epub",
    )
    basename = (
        "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id"
    )
    ENGINE.HTML_OUTPUT = root / "output" / "html" / f"{basename}.html"
    ENGINE.EPUB_OUTPUT = root / "output" / "epub" / f"{basename}.epub"
    ENGINE.HTML_REPORT = root / "qa" / "ORIGINAL_02_HTML_BUILD.json"
    ENGINE.EPUB_REPORT = root / "qa" / "ORIGINAL_02_EPUB_BUILD.json"

    ENGINE.TITLE = (
        "Optimisasi Lanjut dan Analisis Konveks — Tranche Asli 2: "
        "Ketaksamaan Variasional, Operator Monoton, Resolven, dan Pemisahan"
    )
    ENGINE.AUTHOR = "Lapisan penyelesaian kursus mandiri"
    ENGINE.UNIT_ID = "d90.orig.v1.tr02.unit"
    ENGINE.EDITION_ID = "d90.orig.v1.tr02.edition.id-ID"
    ENGINE.IDENTIFIER = "urn:uuid:a491c8e6-b5bf-5b0e-885f-2528a580e6af"
    ENGINE.FIXED_DATE = "2026-08-26"
    ENGINE.FIXED_MODIFIED = "2026-08-26T00:00:00Z"
    ENGINE.SOURCE_DATE_EPOCH = "1787702400"
    ENGINE.RIGHTS = (
        "Mixed rights: new Original-02 content CC BY-SA 4.0; "
        "shinybook.cls and macros-id.tex CC BY 4.0"
    )
    ENGINE.LAB_ALT = (
        "Grafik skala logaritmik residu inklusi terhadap iterasi untuk "
        "maju-mundur stabil, maju-mundur diagnostik di luar rentang teorema, "
        "dan Douglas-Rachford; seluruh nilai tersedia dalam tabel, CSV, dan JSON."
    )

    ENGINE.LAB_MEDIA_TYPES = {
        "monotone-splitting-lab.py": "text/x-python",
        "results.json": "application/json",
        "results.csv": "text/csv",
        "residual.svg": "image/svg+xml",
    }
    ENGINE.EPUB_LAB_ANCHORS = {
        "monotone-splitting-lab.py": "kode-program-python-lengkap",
        "results.json": "hasil-json-lengkap",
        "results.csv": "hasil-csv-lengkap",
        "residual.svg": "grafik-residu-inklusi",
    }
    ENGINE.REQUIRED_MARKERS = (
        "Tentang tranche ini",
        "Ketaksamaan Variasional, Operator Monoton, Resolven, dan Pemisahan",
        "Kemonotonan dan kemaksimalan",
        "Ketaksamaan variasional sebagai inklusi monoton",
        "Eksistensi konstruktif bagi VI monoton kuat",
        "Resolven operator monoton maksimal",
        "Metode titik proksimal",
        "Pemisahan maju–mundur",
        "Perbaikan ekstragradien untuk operator monoton Lipschitz",
        "Pemisahan Douglas–Rachford dan limit bayangan",
        "Mengapa kemonotonan saja tidak cukup untuk langkah maju",
        "Laboratorium 2",
        "Tugas laboratorium",
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
    ENGINE.MATH_MACROS = r"""
\newcommand{\R}{\mathbb{R}}
\newcommand{\norm}[1]{\left\lVert #1\right\rVert}
\newcommand{\inner}[2]{\left\langle #1,#2\right\rangle}
\newcommand{\prox}{\operatorname{prox}}
\newcommand{\dom}{\operatorname{dom}}
\newcommand{\graph}{\operatorname{gra}}
"""

    ENGINE.EXPECTED_SEGMENTS = tuple(
        f"d90.orig.v1.tr02.seg{index:04d}" for index in range(1, 9)
    )
    ENGINE.EXPECTED_ENVIRONMENT_COUNTS = {
        "defn": 3,
        "theorem": 6,
        "lemma": 0,
        "cor": 1,
        "prop": 3,
        "exercise": 6,
        "proof": 10,
    }
    ENGINE.ENVIRONMENTS = (
        "defn",
        "theorem",
        "lemma",
        "cor",
        "prop",
        "exercise",
        "proof",
    )
    ENGINE.ENVIRONMENT_NAMES = {
        "defn": "Definisi",
        "theorem": "Teorema",
        "lemma": "Lemma",
        "cor": "Korolari",
        "prop": "Proposisi",
        "exercise": "Latihan",
    }
    box_selector = ".theorem, .lemma, .cor, .prop, .exercise, .proof"
    extended_selector = ".defn, .theorem, .lemma, .cor, .prop, .exercise, .proof"
    ENGINE.HTML_CSS = ENGINE.HTML_CSS.replace(box_selector, extended_selector)
    ENGINE.EPUB_CSS_TEXT = ENGINE.EPUB_CSS_TEXT.replace(
        box_selector, extended_selector
    )
    ENGINE.EQUATION_LABEL_PREFIX = "orig02:eq:"
    ENGINE.RAW_REFERENCE_PREFIX = "orig02:"
    ENGINE.COURSE_MARKER = (
        "Ketaksamaan Variasional, Operator Monoton, Resolven, dan Pemisahan"
    )
    ENGINE.HTML_SCHEMA = "o015-original-02-html-build-v1"
    ENGINE.EPUB_SCHEMA = "o015-original-02-epub-build-v1"
    ENGINE.APPENDIX_LABEL = "orig02:appendix:lab-complete"
    ENGINE.LAB_GRAPH_SECTION_TITLE = "Grafik residu inklusi"
    ENGINE.LAB_GRAPH_INCLUDE_PATH = "labs/original-02/residual.svg"
    ENGINE.LAB_GRAPH_CAPTION = (
        "Residu inklusi terhadap iterasi untuk tiga jejak pemisahan. Seluruh "
        "nilai tersedia dalam tabel data lengkap, CSV, dan JSON."
    )
    ENGINE.LAB_GRAPH_LABEL = "lab-inclusion-residual"
    ENGINE.CSV_EXPECTED_ROWS = 31
    ENGINE.CSV_EXPECTED_COLUMNS = 8
    ENGINE.CSV_CAPTION = "Seluruh 30 baris hasil laboratorium monotone-splitting"
    ENGINE.EXPECTED_HINT_COUNT = 6
    ENGINE.EXPECTED_SOLUTION_COUNT = 6
    ENGINE.REQUIRED_BODY_MARKER = "Jalankan konfigurasi beku dan cocokkan"
    ENGINE.HTML_MATH_DUPLICATION = 1
    ENGINE.EPUB_MATH_DUPLICATION = 1


if __name__ == "__main__":
    configure()
    ENGINE.main()
