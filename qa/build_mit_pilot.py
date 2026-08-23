#!/usr/bin/env python3
"""Build the MIT Lecture 1 semantic-source pilot as HTML and reflowed PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/id-ID/mit-01-peran-kekonveksan-id.md"
CSS = ROOT / "source/id-ID/mit-pilot.css"
PREAMBLE = ROOT / "source/id-ID/mit-pilot-preamble.tex"
PDF_FILTER = ROOT / "source/id-ID/mit-pilot-pdf-filter.lua"
BEFORE_BODY = ROOT / "source/id-ID/mit-pilot-before-body.html"
AFTER_BODY = ROOT / "source/id-ID/mit-pilot-after-body.html"
PDF_NAME = "D90-MIT-01-peran-kekonveksan-id.pdf"
HTML_NAME = "D90-MIT-01-peran-kekonveksan-id.html"


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
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    html = output_root / HTML_NAME
    pdf = output_root / PDF_NAME
    env = os.environ.copy()
    env.update(
        {
            "SOURCE_DATE_EPOCH": "1787356800",
            "FORCE_SOURCE_DATE": "1",
            "TZ": "UTC",
        }
    )

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
            "--variable=fontsize:11pt",
            "--variable=linestretch:1.04",
            "--output",
            str(pdf),
        ],
        env,
    )

    report = {
        "html": file_record(html),
        "pdf": file_record(pdf),
        "source": file_record(SOURCE),
        "result": "pass",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
