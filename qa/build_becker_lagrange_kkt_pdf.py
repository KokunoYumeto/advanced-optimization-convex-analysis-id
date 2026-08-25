#!/usr/bin/env python3
"""Build and validate the deterministic Becker Lagrange-Slater-KKT PDF."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source" / "id-ID"
WRAPPER = SOURCE_DIR / "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.tex"
BODY = SOURCE_DIR / "becker-01-dualitas-lagrange-slater-kkt-id.tex"
MACROS = SOURCE_DIR / "macros-id.tex"
CLASS = SOURCE_DIR / "shinybook.cls"
SOURCE_REPORT = ROOT / "qa" / "BECKER_01_SOURCE_BOUNDARY.json"
BUILD_ROOT = ROOT / "build" / "becker-01" / "determinism"
OUTPUT = (
    ROOT
    / "output"
    / "pdf"
    / "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.pdf"
)
REPORT = ROOT / "qa" / "BECKER_01_PDF_BUILD.json"
JOB = WRAPPER.stem
SOURCE_DATE_EPOCH = "1782268665"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_descendant(path: Path, parent: Path) -> None:
    path.resolve().relative_to(parent.resolve())


def clean_build_dir(path: Path) -> None:
    ensure_descendant(path, BUILD_ROOT)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def run_build(path: Path) -> dict[str, object]:
    clean_build_dir(path)
    env = os.environ.copy()
    env.update(
        {
            "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
            "FORCE_SOURCE_DATE": "1",
            "MIKTEX_ENABLE_INSTALLER": "0",
        }
    )
    command = [
        "pdflatex",
        "--disable-installer",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-output-directory={path}",
        WRAPPER.name,
    ]
    consoles: list[str] = []
    for pass_number in (1, 2):
        completed = subprocess.run(
            command,
            cwd=SOURCE_DIR,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        consoles.append(completed.stdout + completed.stderr)
        if completed.returncode:
            raise RuntimeError(
                f"pdflatex pass {pass_number} failed:\n{consoles[-1][-8000:]}"
            )

    pdf = path / f"{JOB}.pdf"
    log = path / f"{JOB}.log"
    if not pdf.is_file() or not log.is_file():
        raise RuntimeError("pdflatex did not create the expected PDF/log")
    log_text = log.read_text(encoding="utf-8", errors="replace")
    forbidden = {
        "overfull_boxes": len(re.findall(r"Overfull \\hbox", log_text)),
        "undefined_references": len(
            re.findall(r"undefined references?|Reference .* undefined", log_text, re.I)
        ),
        "fatal_errors": len(re.findall(r"Fatal error|Emergency stop", log_text, re.I)),
    }
    if any(forbidden.values()):
        raise RuntimeError(f"strict TeX log gate failed: {forbidden}")
    return {
        "directory": path.relative_to(ROOT).as_posix(),
        "command": command,
        "passes": 2,
        "pdf": {
            "bytes": pdf.stat().st_size,
            "sha256": sha256(pdf),
        },
        "log": {
            "bytes": log.stat().st_size,
            "sha256": sha256(log),
            **forbidden,
        },
        "console_sha256": [
            hashlib.sha256(item.encode("utf-8")).hexdigest() for item in consoles
        ],
    }


def validate_pdf(path: Path) -> dict[str, object]:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise RuntimeError("Reader PDF is encrypted")
    if len(reader.pages) < 10:
        raise RuntimeError("Unexpectedly short reader")
    root = reader.trailer["/Root"]
    if str(root.get("/Lang")) != "id-ID":
        raise RuntimeError("PDF does not declare id-ID")
    text_result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True,
        check=True,
    )
    text = text_result.stdout.decode("utf-8", errors="replace")
    required = [
        "dualitas lagrange",
        "kondisi slater",
        "dualitas lemah",
        "interpretasi titik pelana",
        "karush-kuhn-tucker",
        "proyeksi pada bola",
        "pemberitahuan lisensi mit",
        "openai codex gpt-5.6-sol, ultra",
    ]
    searchable = text.casefold()
    missing = [marker for marker in required if marker not in searchable]
    if missing:
        raise RuntimeError(f"searchable-text markers missing: {missing}")
    media_boxes = {
        tuple(round(float(value), 3) for value in page.mediabox)
        for page in reader.pages
    }
    if media_boxes != {(0.0, 0.0, 595.276, 841.89)}:
        raise RuntimeError(f"non-A4 media boxes: {sorted(media_boxes)}")
    return {
        "pages": len(reader.pages),
        "encrypted": reader.is_encrypted,
        "language": str(root.get("/Lang")),
        "media_boxes": [list(item) for item in sorted(media_boxes)],
        "searchable_text_bytes": len(text_result.stdout),
        "required_markers": required,
        "missing_markers": missing,
        "tagged": "/StructTreeRoot" in root,
    }


def main() -> None:
    subprocess.run(
        [sys.executable, os.fspath(ROOT / "qa" / "extract_becker_lagrange_kkt_source.py")],
        cwd=ROOT,
        check=True,
    )
    inputs = [WRAPPER, BODY, MACROS, CLASS, SOURCE_REPORT]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing build inputs: " + ", ".join(missing))

    run1 = run_build(BUILD_ROOT / "run1")
    run2 = run_build(BUILD_ROOT / "run2")
    pdf1 = BUILD_ROOT / "run1" / f"{JOB}.pdf"
    pdf2 = BUILD_ROOT / "run2" / f"{JOB}.pdf"
    if pdf1.read_bytes() != pdf2.read_bytes():
        raise RuntimeError("Two clean fixed-epoch PDF builds are not byte-identical")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf1, OUTPUT)
    validation = validate_pdf(OUTPUT)
    report = {
        "schema": "o015-becker-01-pdf-build-v1",
        "result": "pass",
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "byte_identical_clean_builds": True,
        "runs": [run1, run2],
        "inputs": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in inputs
        ],
        "artifact": {
            "path": OUTPUT.relative_to(ROOT).as_posix(),
            "bytes": OUTPUT.stat().st_size,
            "sha256": sha256(OUTPUT),
            **validation,
        },
        "upstream_contact": False,
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
