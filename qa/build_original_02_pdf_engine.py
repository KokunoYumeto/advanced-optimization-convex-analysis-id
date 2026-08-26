#!/usr/bin/env python3
"""Build and validate the deterministic O015 original-tranche-01 PDF."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
ENGINE_SCRIPT = Path(__file__).resolve()
SCRIPT = ENGINE_SCRIPT
SOURCE = ROOT / "source" / "id-ID"
WRAPPER = SOURCE / "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
BODY = SOURCE / "original-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
MACROS = SOURCE / "macros-id.tex"
CLASS = SOURCE / "shinybook.cls"
LAB = ROOT / "labs" / "original-01" / "stochastic-composite-lab.py"
LAB_JSON = ROOT / "labs" / "original-01" / "results.json"
LAB_CSV = ROOT / "labs" / "original-01" / "results.csv"
LAB_SVG = ROOT / "labs" / "original-01" / "objective-gap.svg"
BUILD_ROOT = ROOT / "build" / "original-01" / "pdf-determinism"
OUTPUT = ROOT / "output" / "pdf" / "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf"
REPORT = ROOT / "qa" / "ORIGINAL_01_PDF_BUILD.json"
JOB = WRAPPER.stem
SOURCE_DATE_EPOCH = "1787616000"
MIN_PAGES = 15
MAX_PAGES = 50
TITLE_MARKERS = ("Tranche Asli 1", "Minibatch")
SCHEMA = "o015-original-01-pdf-build-v1"
REQUIRED_MARKERS = (
    "gradien proksimal stokastik",
    "koreksi populasi hingga",
    "penurunan cermin stokastik",
    "divergensi bregman",
    "pembaruan eksponensial",
    "penghubung varians untuk prox-saga",
    "laboratorium 1",
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


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def record(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def receipt_command(command: list[str]) -> list[str]:
    """Return a public-safe command trace without machine-local root paths."""

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


def clean(path: Path) -> None:
    path.resolve().relative_to(BUILD_ROOT.resolve())
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def version(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    lines = (completed.stdout + completed.stderr).strip().splitlines()
    if not lines:
        raise RuntimeError(f"Version probe returned no output: {command}")
    return lines[0]


def run_build(destination: Path) -> dict[str, object]:
    clean(destination)
    environment = os.environ.copy()
    environment.update(
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
        f"-output-directory={destination}",
        WRAPPER.name,
    ]
    console_hashes = []
    for pass_number in (1, 2):
        completed = subprocess.run(
            command,
            cwd=SOURCE,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        console = completed.stdout + completed.stderr
        console_hashes.append(hashlib.sha256(console.encode()).hexdigest())
        if completed.returncode:
            raise RuntimeError(
                f"pdflatex pass {pass_number} failed:\n{console[-10000:]}"
            )
    pdf = destination / f"{JOB}.pdf"
    log = destination / f"{JOB}.log"
    if not pdf.is_file() or not log.is_file():
        raise RuntimeError("Expected PDF/log was not created")
    log_text = log.read_text(encoding="utf-8", errors="replace")
    findings = {
        "overfull_boxes": len(re.findall(r"Overfull \\hbox", log_text)),
        "undefined_references": len(
            re.findall(r"undefined references?|Reference .* undefined", log_text, re.I)
        ),
        "fatal_errors": len(re.findall(r"Fatal error|Emergency stop", log_text, re.I)),
    }
    if any(findings.values()):
        raise RuntimeError(f"Strict TeX log gate failed: {findings}")
    return {
        "directory": destination.relative_to(ROOT).as_posix(),
        "command": receipt_command(command),
        "passes": 2,
        "pdf": record(pdf),
        "log": {**record(log), **findings},
        "console_sha256": console_hashes,
    }


def validate_pdf(path: Path) -> dict[str, object]:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise RuntimeError("PDF is encrypted")
    if not MIN_PAGES <= len(reader.pages) <= MAX_PAGES:
        raise RuntimeError(f"Unexpected page count: {len(reader.pages)}")
    root = reader.trailer["/Root"]
    if str(root.get("/Lang")) != "id-ID":
        raise RuntimeError("PDF lacks /Lang id-ID")
    boxes = {
        tuple(round(float(value), 3) for value in page.mediabox)
        for page in reader.pages
    }
    if boxes != {(0.0, 0.0, 595.276, 841.89)}:
        raise RuntimeError(f"Non-A4 media boxes: {boxes}")
    extracted = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
    ).stdout
    searchable = re.sub(
        r"\s+", " ", extracted.decode("utf-8", errors="replace").casefold()
    )
    required = list(REQUIRED_MARKERS)
    missing = [marker for marker in required if marker not in searchable]
    if missing:
        raise RuntimeError(f"Searchable text lacks markers: {missing}")
    metadata = reader.metadata or {}
    title = str(metadata.get("/Title", ""))
    if any(marker not in title for marker in TITLE_MARKERS):
        raise RuntimeError(f"Unexpected title metadata: {title!r}")
    return {
        "pages": len(reader.pages),
        "encrypted": False,
        "language": str(root.get("/Lang")),
        "title": title,
        "media_boxes": [list(item) for item in sorted(boxes)],
        "searchable_text_bytes": len(extracted),
        "required_markers": required,
        "missing_markers": missing,
        "tagged": "/StructTreeRoot" in root,
    }


def main() -> None:
    inputs = [
        WRAPPER,
        BODY,
        MACROS,
        CLASS,
        LAB,
        LAB_JSON,
        LAB_CSV,
        LAB_SVG,
        ENGINE_SCRIPT,
        SCRIPT,
    ]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing build inputs: {missing}")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    if "OpenAI Codex gpt-5.6-sol, Ultra" not in wrapper:
        raise RuntimeError("Model provenance marker is missing")
    before = [record(path) for path in inputs]
    run1 = run_build(BUILD_ROOT / "run1")
    run2 = run_build(BUILD_ROOT / "run2")
    if before != [record(path) for path in inputs]:
        raise RuntimeError("Inputs changed during deterministic builds")
    pdf1 = BUILD_ROOT / "run1" / f"{JOB}.pdf"
    pdf2 = BUILD_ROOT / "run2" / f"{JOB}.pdf"
    if pdf1.read_bytes() != pdf2.read_bytes():
        raise RuntimeError("Two clean fixed-epoch PDFs differ")
    validation = validate_pdf(pdf1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf1, OUTPUT)
    if OUTPUT.read_bytes() != pdf1.read_bytes():
        raise RuntimeError("Canonical output copy differs")
    report = {
        "schema": SCHEMA,
        "result": "pass",
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "byte_identical_clean_builds": True,
        "canonical_copy_exact_match": True,
        "tool_versions": {
            "pdflatex": version(["pdflatex", "--version"]),
            "pdftotext": version(["pdftotext", "-v"]),
            "pypdf": __import__("pypdf").__version__,
        },
        "runs": [run1, run2],
        "inputs": before,
        "artifact": {**record(OUTPUT), **validation},
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
