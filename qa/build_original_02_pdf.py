#!/usr/bin/env python3
"""Configure the proven O015 PDF engine for Original-02."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve()
BASE = SCRIPT.with_name("build_original_02_pdf_engine.py")
SPEC = importlib.util.spec_from_file_location("o015_original_pdf_base", BASE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load PDF engine: {BASE}")
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)


def configure() -> None:
    root = ENGINE.ROOT
    source = root / "source" / "id-ID"
    lab = root / "labs" / "original-02"
    basename = (
        "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id"
    )
    ENGINE.SOURCE = source
    ENGINE.SCRIPT = SCRIPT
    ENGINE.WRAPPER = source / f"{basename}.tex"
    ENGINE.BODY = (
        source
        / "original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex"
    )
    ENGINE.MACROS = source / "macros-id.tex"
    ENGINE.CLASS = source / "shinybook.cls"
    ENGINE.LAB = lab / "monotone-splitting-lab.py"
    ENGINE.LAB_JSON = lab / "results.json"
    ENGINE.LAB_CSV = lab / "results.csv"
    ENGINE.LAB_SVG = lab / "residual.svg"
    ENGINE.BUILD_ROOT = root / "tmp" / "pdfs" / "original-02-determinism"
    ENGINE.OUTPUT = root / "output" / "pdf" / f"{basename}.pdf"
    ENGINE.REPORT = root / "qa" / "ORIGINAL_02_PDF_BUILD.json"
    ENGINE.JOB = basename
    ENGINE.SOURCE_DATE_EPOCH = "1787702400"
    ENGINE.MIN_PAGES = 15
    ENGINE.MAX_PAGES = 40
    ENGINE.TITLE_MARKERS = ("Tranche Asli 2", "Resolven")
    ENGINE.SCHEMA = "o015-original-02-pdf-build-v1"
    ENGINE.REQUIRED_MARKERS = (
        "ketaksamaan variasional sebagai inklusi monoton",
        "eksistensi konstruktif bagi vi monoton kuat",
        "resolven operator monoton maksimal",
        "metode titik proksimal",
        "pemisahan maju",
        "perbaikan ekstragradien",
        "pemisahan douglas",
        "mengapa kemonotonan saja tidak cukup",
        "laboratorium 2",
        "petunjuk bertahap",
        "solusi lengkap",
        "peta asumsi dan batas klaim",
        "creative commons attribution-sharealike 4.0",
        "creative commons attribution 4.0 international",
        "shinybook.cls",
        "macros-id.tex",
        "christian clason",
        "tingkat kiriman arxiv",
        "tidak memuat pemberitahuan lisensi terpisah",
        "openai codex gpt-5.6-sol, ultra",
    )


if __name__ == "__main__":
    configure()
    ENGINE.main()
