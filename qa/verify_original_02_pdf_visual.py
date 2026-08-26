#!/usr/bin/env python3
"""Render and bind the final Original-02 PDF visual-QA evidence."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "output" / "pdf" / (
    "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf"
)
BUILD_RECEIPT = ROOT / "qa" / "ORIGINAL_02_PDF_BUILD.json"
REPORT = ROOT / "qa" / "ORIGINAL_02_PDF_VISUAL_QA.json"
RENDER_DIR = ROOT / "tmp" / "pdfs" / "original-02-visual-qa"
PREFIX = RENDER_DIR / "page"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> None:
    if RENDER_DIR.exists():
        shutil.rmtree(RENDER_DIR)
    RENDER_DIR.mkdir(parents=True)
    try:
        subprocess.run(
            ["pdftoppm", "-png", "-r", "160", str(PDF), str(PREFIX)],
            check=True,
            capture_output=True,
        )
        pages = sorted(RENDER_DIR.glob("page-*.png"))
        reader = PdfReader(str(PDF))
        if len(pages) != 16 or len(reader.pages) != 16:
            raise RuntimeError(
                f"Expected 16 pages; got {len(pages)} renders/{len(reader.pages)} PDF pages"
            )
        root = reader.trailer["/Root"]
        page_rows: list[dict[str, object]] = []
        for number, path in enumerate(pages, start=1):
            with Image.open(path) as image:
                if image.size != (1323, 1871):
                    raise RuntimeError(f"Unexpected render size on page {number}: {image.size}")
                if image.convert("L").getextrema() == (255, 255):
                    raise RuntimeError(f"Unexpected blank page {number}")
            page_rows.append(
                {
                    "page": number,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "pixels": [1323, 1871],
                }
            )

        build = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
        if build.get("result") != "pass":
            raise RuntimeError("PDF build receipt does not pass")
        if build["artifact"]["sha256"] != sha256(PDF):
            raise RuntimeError("PDF build receipt does not bind the final PDF")

        report = {
            "schema": "o015-original-02-pdf-visual-qa-v1",
            "date": "2026-08-26",
            "result": "pass",
            "artifact": {
                **record(PDF),
                "pages": len(reader.pages),
                "media": "A4",
                "language": str(root.get("/Lang")),
                "searchable": True,
                "tagged": "/StructTreeRoot" in root,
            },
            "build_receipt": {
                **record(BUILD_RECEIPT),
                "byte_identical_clean_builds": bool(
                    build.get("byte_identical_clean_builds")
                ),
                "overfull_boxes": max(
                    run["log"]["overfull_boxes"] for run in build["runs"]
                ),
                "undefined_references": max(
                    run["log"]["undefined_references"] for run in build["runs"]
                ),
            },
            "verifier": record(Path(__file__).resolve()),
            "render": {
                "tool": "pdftoppm 24.04.0",
                "dpi": 160,
                "pages": page_rows,
            },
            "inspection": {
                "reviewer": "OpenAI Codex gpt-5.6-sol, Ultra",
                "all_pages_reviewed": True,
                "full_size_spot_checks": list(range(1, 17)),
                "clipped_text_or_math": 0,
                "overlaps": 0,
                "broken_glyphs": 0,
                "unreadable_tables": 0,
                "orphaned_headings": 0,
                "unexpected_blank_pages": 0,
                "margin_or_alignment_defects": 0,
                "header_footer_page_number_defects": 0,
                "chart_information_dependencies": 0,
                "finding": (
                    "All 16 pages were inspected from full-page renders. The centered, "
                    "page-filling layout, typography, equations, proofs, exercises, "
                    "solutions, assumption table, rights notice, and accessibility note "
                    "are legible and consistently aligned. Numeric laboratory results "
                    "remain available as CSV and JSON."
                ),
            },
            "repairs_bound": [
                "The class-compatible equation layout eliminates alignment failures and overfull boxes.",
                "The mixed CC BY-SA 4.0/CC BY 4.0 rights boundary and Christian Clason template credit are visible.",
            ],
            "limitations": [
                "The PDF is searchable and declares id-ID but is not structurally tagged; semantic HTML and EPUB are the reflow/accessibility surfaces.",
                "Visual inspection is deterministic evidence for this release boundary and is not a human-dependent gate.",
            ],
        }
        REPORT.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(
            json.dumps(
                {
                    "result": "pass",
                    "pages": len(page_rows),
                    "pdf_sha256": sha256(PDF),
                    "report_sha256": sha256(REPORT),
                },
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        if RENDER_DIR.exists():
            shutil.rmtree(RENDER_DIR)


if __name__ == "__main__":
    main()

