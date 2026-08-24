#!/usr/bin/env python3
"""Build the MIT 6.253 complete-notes Lecture 4 boundary (PDF pages 39-49)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/id-ID/mit-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.md"
CSS = ROOT / "source/id-ID/mit-l08.css"
PREAMBLE = ROOT / "source/id-ID/mit-l08-preamble.tex"
PDF_FILTER = ROOT / "source/id-ID/mit-l08-pdf-filter.lua"
BEFORE_BODY = ROOT / "source/id-ID/mit-l08-before-body.html"
AFTER_BODY = ROOT / "source/id-ID/mit-l08-after-body.html"
HTML_NAME = "D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.html"
PDF_NAME = "D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.pdf"


def file_record(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def run(command: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        raise RuntimeError(completed.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--html-output", type=Path)
    parser.add_argument("--pdf-output", type=Path)
    args = parser.parse_args()
    if args.output_root is None and (args.html_output is None or args.pdf_output is None):
        parser.error("provide --output-root or both --html-output and --pdf-output")
    if args.output_root is not None and (args.html_output is not None or args.pdf_output is not None):
        parser.error("--output-root cannot be combined with --html-output/--pdf-output")
    if args.output_root is not None:
        output_root = args.output_root.resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        html = output_root / HTML_NAME
        pdf = output_root / PDF_NAME
    else:
        html = args.html_output.resolve()
        pdf = args.pdf_output.resolve()
        html.parent.mkdir(parents=True, exist_ok=True)
        pdf.parent.mkdir(parents=True, exist_ok=True)

    required = (SOURCE, CSS, PREAMBLE, PDF_FILTER, BEFORE_BODY, AFTER_BODY)
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing L08 build inputs: {missing}")

    env = os.environ.copy()
    env.update({"SOURCE_DATE_EPOCH": "1787529600", "FORCE_SOURCE_DATE": "1", "TZ": "UTC"})
    common = [
        "pandoc",
        str(SOURCE),
        "--from=markdown+fenced_divs+yaml_metadata_block",
        "--standalone",
        "--toc",
        "--number-sections",
        "--metadata=lang:id-ID",
    ]
    run(
        common
        + [
            "--to=html5",
            "--section-divs",
            "--mathml",
            f"--css={CSS}",
            f"--include-before-body={BEFORE_BODY}",
            f"--include-after-body={AFTER_BODY}",
            "--embed-resources",
            "--output",
            str(html),
        ],
        env,
    )
    run(
        common
        + [
            "--pdf-engine=lualatex",
            "--shift-heading-level-by=-1",
            f"--lua-filter={PDF_FILTER}",
            f"--include-in-header={PREAMBLE}",
            "--variable=fontsize:10pt",
            "--variable=linestretch:1.0",
            "--output",
            str(pdf),
        ],
        env,
    )
    print(
        json.dumps(
            {
                "html": file_record(html),
                "pdf": file_record(pdf),
                "source": file_record(SOURCE),
                "result": "pass",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
