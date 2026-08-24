#!/usr/bin/env python3
"""Build the Habring Chapters 1--2 Indonesian reader reproducibly."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source" / "id-ID"
WRAPPER = SOURCE_DIR / "D90-HAB-01-02-prasyarat-dan-konveksitas-id.tex"
BUILD_DIR = ROOT / "build" / "habring-unit-01-02-id"
PDF_NAME = "D90-HAB-01-02-prasyarat-dan-konveksitas-id.pdf"
BUILD_PDF = BUILD_DIR / PDF_NAME
OUTPUT_PDF = ROOT / "output" / "pdf" / PDF_NAME
FIRST_PDF = ROOT / "tmp" / "pdfs" / f"{PDF_NAME}.first.pdf"
TEXT_PATH = ROOT / "qa" / "D90-HAB-01-02-prasyarat-dan-konveksitas-id.txt"
REPORT_PATH = ROOT / "qa" / "HABRING_CH01_CH02_BUILD.json"
SOURCE_DATE_EPOCH = "1783900800"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = completed.stdout + completed.stderr
    if completed.returncode:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n{output}"
        )
    return output


def latexmk(env: dict[str, str]) -> str:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    return run(
        [
            "latexmk",
            "-gg",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-outdir={BUILD_DIR}",
            WRAPPER.name,
        ],
        cwd=SOURCE_DIR,
        env=env,
    )


def set_language(pdf_path: Path) -> None:
    """Set the catalog language without disturbing deterministic page bytes."""

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer._root_object.update(
        {NameObject("/Lang"): TextStringObject("id-ID")}
    )
    temp = pdf_path.with_suffix(".lang.pdf")
    with temp.open("wb") as stream:
        writer.write(stream)
    temp.replace(pdf_path)


def main() -> None:
    required = [
        WRAPPER,
        SOURCE_DIR / "habring-01-prasyarat-id.tex",
        SOURCE_DIR / "habring-02-konveksitas-id.tex",
        SOURCE_DIR / "macros-id.tex",
        SOURCE_DIR / "shinybook.cls",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing build inputs: " + ", ".join(missing))

    env = os.environ.copy()
    env.update(
        {
            "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
            "FORCE_SOURCE_DATE": "1",
            "TZ": "UTC",
        }
    )
    FIRST_PDF.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    first_console = latexmk(env)
    if not BUILD_PDF.is_file():
        raise FileNotFoundError(BUILD_PDF)
    set_language(BUILD_PDF)
    shutil.copy2(BUILD_PDF, FIRST_PDF)
    first_sha = sha256(FIRST_PDF)

    second_console = latexmk(env)
    if not BUILD_PDF.is_file():
        raise FileNotFoundError(BUILD_PDF)
    set_language(BUILD_PDF)
    second_sha = sha256(BUILD_PDF)
    if first_sha != second_sha or FIRST_PDF.read_bytes() != BUILD_PDF.read_bytes():
        raise RuntimeError(
            f"Non-deterministic PDF build: first={first_sha}, second={second_sha}"
        )

    shutil.copy2(BUILD_PDF, OUTPUT_PDF)
    run(
        ["pdftotext", "-enc", "UTF-8", str(OUTPUT_PDF), str(TEXT_PATH)],
        cwd=ROOT,
        env=env,
    )
    reader = PdfReader(str(OUTPUT_PDF))
    lang = reader.trailer["/Root"].get("/Lang")
    page_sizes = sorted(
        {
            (
                round(float(page.mediabox.width), 3),
                round(float(page.mediabox.height), 3),
            )
            for page in reader.pages
        }
    )
    log_path = BUILD_DIR / WRAPPER.with_suffix(".log").name
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    forbidden_log_fragments = [
        "! LaTeX Error",
        "Undefined control sequence",
        "There were undefined references",
        "Citation `",
        "Rerun to get cross-references right",
        "Overfull \\hbox",
        "Overfull \\vbox",
    ]
    log_failures = [item for item in forbidden_log_fragments if item in log_text]
    if log_failures:
        raise RuntimeError("Forbidden final-log findings: " + repr(log_failures))

    report = {
        "schema": "o015-habring-ch01-ch02-build-v1",
        "result": "pass",
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "wrapper": {
            "path": WRAPPER.relative_to(ROOT).as_posix(),
            "bytes": WRAPPER.stat().st_size,
            "sha256": sha256(WRAPPER),
        },
        "inputs": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in required[1:]
        ],
        "artifact": {
            "path": OUTPUT_PDF.relative_to(ROOT).as_posix(),
            "bytes": OUTPUT_PDF.stat().st_size,
            "sha256": second_sha,
            "pages": len(reader.pages),
            "page_sizes_points": page_sizes,
            "catalog_lang": str(lang),
            "encrypted": reader.is_encrypted,
        },
        "determinism": {
            "builds": 2,
            "byte_identical": True,
            "first_sha256": first_sha,
            "second_sha256": second_sha,
        },
        "final_log": {
            "path": log_path.relative_to(ROOT).as_posix(),
            "bytes": log_path.stat().st_size,
            "sha256": sha256(log_path),
            "forbidden_findings": log_failures,
        },
        "text_extract": {
            "path": TEXT_PATH.relative_to(ROOT).as_posix(),
            "bytes": TEXT_PATH.stat().st_size,
            "sha256": sha256(TEXT_PATH),
        },
        "console_sha256": {
            "first": hashlib.sha256(first_console.encode("utf-8")).hexdigest(),
            "second": hashlib.sha256(second_console.encode("utf-8")).hexdigest(),
        },
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    FIRST_PDF.unlink(missing_ok=True)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
