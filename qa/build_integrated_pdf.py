#!/usr/bin/env python3
"""Build the integrated O015 PDF twice and require byte identity.

The builder is deliberately bounded to the canonical D90 tree.  It pins the
source date and timezone, builds in two clean task-local directories, and only
copies a PDF into output/pdf after both complete builds and structural checks
pass.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "id-ID"
TMP = ROOT / "tmp" / "pdfs"
OUTPUT = ROOT / "output" / "pdf"
QA = ROOT / "qa"
JOB = "D90-O015-optimisasi-lanjut-analisis-konveks-id"
MASTER = SOURCE / f"{JOB}.tex"
FINAL = OUTPUT / f"{JOB}.pdf"
RECEIPT = QA / "2026-08-27-integrated-pdf-build.json"
SOURCE_DATE_EPOCH = "1787702400"

INPUTS = [
    "D90-O015-optimisasi-lanjut-analisis-konveks-id.tex",
    "o015-accessibility-id.tex",
    "latex-lab-testphase-latest.sty",
    "macros-id.tex",
    "references-integrated-id.bib",
    "habring-01-prasyarat-id.tex",
    "habring-02-konveksitas-id.tex",
    "habring-03-subgradien-id.tex",
    "habring-04-metode-subgradien-terproyeksi-id.tex",
    "habring-05-metode-gradien-proksimal-id.tex",
    "habring-06-akselerasi-id.tex",
    "habring-07-dualitas-id.tex",
    "habring-08-penurunan-gradien-stokastik-id.tex",
    "habring-09-transportasi-optimal-id.tex",
    "becker-01-dualitas-lagrange-slater-kkt-id.tex",
    "becker-03-reduksi-varians-id.tex",
    "original-01-metode-stokastik-komposit-cermin-minibatch-id.tex",
    "becker-02-pemisahan-douglas-rachford-id.tex",
    "original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex",
    "original-03-penutupan-kursus-id.tex",
    "original-03/00-peta-asesmen-id.tex",
    "original-03/01-diagnostik-prasyarat-id.tex",
    "original-03/02-set-soal-dasar-konveks-id.tex",
    "original-03/03-set-soal-metode-proksimal-id.tex",
    "original-03/04-set-soal-dualitas-kkt-id.tex",
    "original-03/05-set-soal-metode-stokastik-id.tex",
    "original-03/06-set-soal-operator-monoton-id.tex",
    "original-03/07-set-soal-transportasi-dan-sintesis-id.tex",
    "original-03/08-rubrik-pembuktian-id.tex",
    "original-03/09-ujian-tengah-id.tex",
    "original-03/10-ujian-akhir-id.tex",
    "original-03/11-laboratorium-globalisasi-newton-id.tex",
    "original-03/12-laboratorium-transportasi-entropik-id.tex",
    "original-03/13-proyek-kapstone-masalah-invers-komposit-id.tex",
    "figures/discontinuous_function.png",
    "figures/lsc_function.png",
    "figures/sets.png",
    "figures/balls.png",
    "figures/convex_fct.png",
    "figures/gradient.png",
    "figures/subgradient.png",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path, relative_to: Path = ROOT) -> dict[str, object]:
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def run(command: list[str], cwd: Path, env: dict[str, str], console: Path) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    with console.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("$ " + " ".join(command) + "\n")
        stream.write(completed.stdout)
        if not completed.stdout.endswith("\n"):
            stream.write("\n")
    if completed.returncode:
        tail = "\n".join(completed.stdout.splitlines()[-80:])
        raise RuntimeError(
            f"command failed with exit {completed.returncode}: {command!r}\n{tail}"
        )


def clean_directory(path: Path) -> None:
    resolved = path.resolve()
    expected_parent = (TMP / "integrated-deterministic-builds").resolve()
    if resolved.parent != expected_parent:
        raise RuntimeError(f"refusing to clean unexpected path: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_once(label: str, env: dict[str, str]) -> dict[str, object]:
    build_root = TMP / "integrated-deterministic-builds"
    build_root.mkdir(parents=True, exist_ok=True)
    destination = build_root / label
    clean_directory(destination)
    console = destination / "build-console.txt"

    latex = [
        "lualatex",
        "--interaction=nonstopmode",
        "--halt-on-error",
        "--file-line-error",
        "-recorder",
        f"-output-directory={destination}",
        MASTER.name,
    ]
    run(latex, SOURCE, env, console)
    run(["biber", JOB], destination, env, console)
    for _ in range(2):
        run(latex, SOURCE, env, console)

    pdf = destination / f"{JOB}.pdf"
    log = destination / f"{JOB}.log"
    if not pdf.is_file() or not log.is_file():
        raise RuntimeError(f"missing build outputs in {destination}")

    log_text = log.read_text(encoding="utf-8", errors="replace")
    forbidden = {
        "fatal_error": r"Fatal error",
        "latex_error": r"(?:LaTeX|Package .+?) Error",
        "undefined_reference": r"(?:Reference|Citation) .+ undefined|There were undefined references",
        "multiply_defined": r"multiply defined|multiply-defined",
        "overfull_box": r"Overfull \\[hv]box",
        "duplicate_destination": r"duplicate destination",
        "rerun_needed": r"Rerun to get cross-references right|Please rerun LaTeX|Please \(re\)run Biber",
    }
    findings = {
        name: len(re.findall(pattern, log_text, flags=re.IGNORECASE))
        for name, pattern in forbidden.items()
    }
    if any(findings.values()):
        raise RuntimeError(f"forbidden log findings in {label}: {findings}")

    reader = PdfReader(str(pdf))
    root = reader.trailer["/Root"]
    metadata = reader.metadata or {}
    if len(reader.pages) < 130:
        raise RuntimeError(f"unexpectedly short integrated reader: {len(reader.pages)} pages")
    if root.get("/Lang") != "id-ID":
        raise RuntimeError(f"unexpected document language: {root.get('/Lang')!r}")
    if not root.get("/MarkInfo") or not root["/MarkInfo"].get("/Marked"):
        raise RuntimeError("PDF is not marked")
    if not root.get("/StructTreeRoot"):
        raise RuntimeError("PDF has no structure tree")
    tabs = sum(1 for page in reader.pages if page.get("/Tabs") == "/S")
    if tabs != len(reader.pages):
        raise RuntimeError(f"/Tabs /S only on {tabs}/{len(reader.pages)} pages")

    return {
        "label": label,
        "pdf": identity(pdf),
        "log": identity(log),
        "console": identity(console),
        "pages": len(reader.pages),
        "lang": root.get("/Lang"),
        "marked": bool(root["/MarkInfo"].get("/Marked")),
        "struct_tree": True,
        "tabs_s_pages": tabs,
        "title": metadata.get("/Title"),
        "creator": metadata.get("/Creator"),
        "creation_date": metadata.get("/CreationDate"),
        "log_findings": findings,
    }


def main() -> int:
    missing = [relative for relative in INPUTS if not (SOURCE / relative).is_file()]
    if missing:
        raise RuntimeError(f"missing declared integrated inputs: {missing}")

    env = os.environ.copy()
    env.update(
        {
            "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
            "FORCE_SOURCE_DATE": "1",
            "TZ": "UTC",
            "BIBINPUTS": str(SOURCE) + os.pathsep,
            "TEXINPUTS": str(SOURCE) + os.pathsep,
        }
    )
    first = build_once("a", env)
    second = build_once("b", env)
    if first["pdf"]["sha256"] != second["pdf"]["sha256"]:
        raise RuntimeError(
            "deterministic PDF builds differ: "
            f"{first['pdf']['sha256']} != {second['pdf']['sha256']}"
        )
    if first["pdf"]["bytes"] != second["pdf"]["bytes"]:
        raise RuntimeError("deterministic PDF sizes differ")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    source_pdf = TMP / "integrated-deterministic-builds" / "b" / f"{JOB}.pdf"
    temporary_final = FINAL.with_suffix(".pdf.tmp")
    shutil.copyfile(source_pdf, temporary_final)
    os.replace(temporary_final, FINAL)

    final_identity = identity(FINAL)
    if final_identity["sha256"] != second["pdf"]["sha256"]:
        raise RuntimeError("final PDF copy differs from admitted build")

    input_manifest = [identity(SOURCE / relative) for relative in INPUTS]
    receipt = {
        "schema": "o015.integrated-pdf-build.v1",
        "status": "pass",
        "source_date_epoch": int(SOURCE_DATE_EPOCH),
        "timezone": "UTC",
        "toolchain": {
            "latex": "LuaLaTeX with local latex-lab/tagpdf compatibility loader",
            "bibliography": "Biber",
            "claim": "tagged/searchable PDF; no PDF/UA conformance claim",
        },
        "declared_inputs": input_manifest,
        "builds": [first, second],
        "byte_identical": True,
        "final": final_identity,
    }
    RECEIPT.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": "pass", "final": final_identity, "pages": second["pages"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
