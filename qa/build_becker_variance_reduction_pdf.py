#!/usr/bin/env python3
"""Build and validate the isolated deterministic Becker-03 PDF."""

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
WRAPPER = SOURCE_DIR / "D90-BECKER-03-reduksi-varians-id.tex"
BODY = SOURCE_DIR / "becker-03-reduksi-varians-id.tex"
MACROS = SOURCE_DIR / "macros-id.tex"
CLASS = SOURCE_DIR / "shinybook.cls"
WITNESS = ROOT / "source" / "en" / "becker-03-variance-reduction-source.tex"
EXTRACTOR = ROOT / "qa" / "extract_becker_variance_reduction_source.py"
SOURCE_REPORT = ROOT / "qa" / "BECKER_03_SOURCE_BOUNDARY.json"
BUILD_ROOT = ROOT / "build" / "becker-03" / "determinism"
OUTPUT = (
    ROOT
    / "output"
    / "pdf"
    / "D90-BECKER-03-reduksi-varians-id.pdf"
)
REPORT = ROOT / "qa" / "BECKER_03_PDF_BUILD.json"
JOB = WRAPPER.stem
SOURCE_DATE_EPOCH = "1782268665"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def ensure_descendant(path: Path, parent: Path) -> None:
    path.resolve().relative_to(parent.resolve())


def clean_build_dir(path: Path) -> None:
    ensure_descendant(path, BUILD_ROOT)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def tool_version(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"Version probe failed: {command}")
    combined = (completed.stdout + completed.stderr).strip().splitlines()
    if not combined:
        raise RuntimeError(f"Version probe returned no output: {command}")
    return combined[0]


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
        console = completed.stdout + completed.stderr
        consoles.append(console)
        if completed.returncode:
            raise RuntimeError(
                f"pdflatex pass {pass_number} failed:\n{console[-8000:]}"
            )

    pdf = path / f"{JOB}.pdf"
    log = path / f"{JOB}.log"
    if not pdf.is_file() or not log.is_file():
        raise RuntimeError("pdflatex did not create the expected Becker-03 PDF/log")
    log_text = log.read_text(encoding="utf-8", errors="replace")
    forbidden = {
        "overfull_boxes": len(re.findall(r"Overfull \\hbox", log_text)),
        "undefined_references": len(
            re.findall(r"undefined references?|Reference .* undefined", log_text, re.I)
        ),
        "fatal_errors": len(re.findall(r"Fatal error|Emergency stop", log_text, re.I)),
    }
    if any(forbidden.values()):
        raise RuntimeError(f"Strict Becker-03 TeX log gate failed: {forbidden}")
    return {
        "directory": path.relative_to(ROOT).as_posix(),
        "command": command,
        "passes": 2,
        "pdf": file_record(pdf),
        "log": {**file_record(log), **forbidden},
        "console_sha256": [
            hashlib.sha256(item.encode("utf-8")).hexdigest() for item in consoles
        ],
    }


def validate_pdf(path: Path) -> dict[str, object]:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise RuntimeError("Becker-03 PDF is encrypted")
    if not 6 <= len(reader.pages) <= 24:
        raise RuntimeError(f"Unexpected Becker-03 page count: {len(reader.pages)}")
    root = reader.trailer["/Root"]
    if str(root.get("/Lang")) != "id-ID":
        raise RuntimeError("Becker-03 PDF does not declare id-ID")
    text_result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True,
        check=True,
    )
    text = text_result.stdout.decode("utf-8", errors="replace")
    required = [
        "reduksi varians",
        "aproksimasi rata-rata sampel",
        "penaksir saga",
        "peubah kontrol",
        "takbias bersyarat",
        "laju linear saga",
        "iterat rata-rata",
        "solusi lengkap",
        "defazio, bach, dan lacoste-julien",
        "pemberitahuan lisensi mit",
        "openai codex gpt-5.6-sol, ultra",
    ]
    searchable = text.casefold()
    missing = [marker for marker in required if marker not in searchable]
    if missing:
        raise RuntimeError(f"Searchable-text markers missing: {missing}")
    media_boxes = {
        tuple(round(float(value), 3) for value in page.mediabox)
        for page in reader.pages
    }
    if media_boxes != {(0.0, 0.0, 595.276, 841.89)}:
        raise RuntimeError(f"Non-A4 media boxes: {sorted(media_boxes)}")
    metadata = reader.metadata or {}
    title = str(metadata.get("/Title", ""))
    if "Becker 3" not in title or "Reduksi Varians" not in title:
        raise RuntimeError(f"Unexpected PDF title metadata: {title!r}")
    return {
        "pages": len(reader.pages),
        "encrypted": reader.is_encrypted,
        "language": str(root.get("/Lang")),
        "title": title,
        "media_boxes": [list(item) for item in sorted(media_boxes)],
        "searchable_text_bytes": len(text_result.stdout),
        "required_markers": required,
        "missing_markers": missing,
        "tagged": "/StructTreeRoot" in root,
    }


def main() -> None:
    subprocess.run([sys.executable, os.fspath(EXTRACTOR)], cwd=ROOT, check=True)
    inputs = [WRAPPER, BODY, MACROS, CLASS, WITNESS, EXTRACTOR, SOURCE_REPORT]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing Becker-03 PDF inputs: " + ", ".join(missing))
    wrapper_text = WRAPPER.read_text(encoding="utf-8")
    if "OpenAI Codex gpt-5.6-sol, Ultra" not in wrapper_text:
        raise RuntimeError("Expected live Becker-03 model marker is missing")
    input_records = [file_record(path) for path in inputs]

    run1 = run_build(BUILD_ROOT / "run1")
    run2 = run_build(BUILD_ROOT / "run2")
    if input_records != [file_record(path) for path in inputs]:
        raise RuntimeError("Becker-03 PDF inputs changed during the two clean builds")
    pdf1 = BUILD_ROOT / "run1" / f"{JOB}.pdf"
    pdf2 = BUILD_ROOT / "run2" / f"{JOB}.pdf"
    if pdf1.read_bytes() != pdf2.read_bytes():
        raise RuntimeError("Two clean fixed-epoch Becker-03 PDFs are not byte-identical")

    validation = validate_pdf(pdf1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf1, OUTPUT)
    if OUTPUT.read_bytes() != pdf1.read_bytes():
        raise RuntimeError("Canonical Becker-03 PDF copy differs from validated build")
    report = {
        "schema": "o015-becker-03-pdf-build-v1",
        "result": "pass",
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "byte_identical_clean_builds": True,
        "canonical_copy_exact_match": True,
        "tool_versions": {
            "pdflatex": tool_version(["pdflatex", "--version"]),
            "pdftotext": tool_version(["pdftotext", "-v"]),
            "pypdf": __import__("pypdf").__version__,
        },
        "runs": [run1, run2],
        "inputs": input_records,
        "artifact": {**file_record(OUTPUT), **validation},
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
