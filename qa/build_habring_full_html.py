#!/usr/bin/env python3
"""Build one reflowable, standalone Habring Chapters 1--9 HTML reader."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source" / "id-ID"
TMP_DIR = ROOT / "tmp" / "habring-html"
COMBINED_TEX = TMP_DIR / "D90-HAB-01-09-id.tex"
FIRST_HTML = TMP_DIR / "D90-HAB-01-09-id.first.html"
OUTPUT_HTML = (
    ROOT
    / "output"
    / "html"
    / "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html"
)
REPORT_PATH = ROOT / "qa" / "HABRING_FULL_HTML_BUILD.json"

CHAPTERS = [
    SOURCE_DIR / "habring-01-prasyarat-id.tex",
    SOURCE_DIR / "habring-02-konveksitas-id.tex",
    SOURCE_DIR / "habring-03-subgradien-id.tex",
    SOURCE_DIR / "habring-04-metode-subgradien-terproyeksi-id.tex",
    SOURCE_DIR / "habring-05-metode-gradien-proksimal-id.tex",
    SOURCE_DIR / "habring-06-akselerasi-id.tex",
    SOURCE_DIR / "habring-07-dualitas-id.tex",
    SOURCE_DIR / "habring-08-penurunan-gradien-stokastik-id.tex",
    SOURCE_DIR / "habring-09-transportasi-optimal-id.tex",
]

CSS = r"""
:root { color-scheme: light; --ink:#172033; --muted:#506078; --rule:#ccd5e2;
  --accent:#2b5d9a; --panel:#f4f7fb; --max:76rem; }
* { box-sizing:border-box; }
html { font-size:100%; scroll-behavior:smooth; }
body { margin:0; max-width:none; padding:0; overflow-x:clip; color:var(--ink); background:#fff; font-family:Georgia,"Times New Roman",serif;
  font-size:clamp(1rem,0.96rem + .18vw,1.12rem); line-height:1.64; }
body > header, body > nav, body > main, body > section, body > div, body > h1,
body > h2, body > p { width:min(calc(100% - 2.2rem),var(--max)); margin-inline:auto; }
header#title-block-header { padding:3rem 0 1.5rem; border-bottom:1px solid var(--rule); }
h1,h2,h3,h4 { max-width:76ch; margin-inline:auto; font-family:Arial,Helvetica,sans-serif; line-height:1.2; color:#12233d;
  scroll-margin-top:1rem; }
h1 { margin-top:2.7rem; font-size:clamp(1.9rem,1.4rem + 1.8vw,3rem); }
h2 { margin-top:2.3rem; font-size:clamp(1.45rem,1.2rem + .8vw,2rem); }
h3 { margin-top:1.8rem; }
a { color:#174f91; text-underline-offset:.14em; }
nav#TOC { margin:1.5rem auto 2.5rem; padding:1rem 1.3rem; background:var(--panel);
  border:1px solid var(--rule); border-radius:.45rem; }
nav#TOC ul { padding-left:1.35rem; }
p { max-width:72ch; margin-inline:auto; }
ol,ul { width:min(100%,76ch); margin-inline:auto; }
li { max-width:72ch; }
.defn,.theorem,.lemma,.cor,.prop,.example,.exercise,.rem,.proof {
  max-width:76ch; margin:1.25rem auto; padding:.85rem 1rem; border-left:.28rem solid var(--accent);
  background:var(--panel); break-inside:avoid; }
.example,.exercise { border-left-color:#7a4c9c; }
.proof { border-left-color:#65758c; background:#fafbfc; }
figure { margin:1.5rem auto; max-width:68rem; }
img { display:block; max-width:100%; height:auto; margin-inline:auto; }
figcaption { color:var(--muted); font-size:.95rem; text-align:center; }
.math.display { display:block; width:100%; max-width:100%; overflow-x:auto; overflow-y:hidden;
  padding:.35rem 0; overscroll-behavior-inline:contain; }
.math.inline { display:inline-block; max-width:100%; overflow-x:auto; overflow-y:hidden;
  vertical-align:middle; overscroll-behavior-inline:contain; }
mjx-container[display="true"] { max-width:100%; overflow-x:auto; overflow-y:hidden; }
table { display:block; overflow-x:auto; border-collapse:collapse; }
th,td { border:1px solid var(--rule); padding:.45rem .6rem; }
code { overflow-wrap:anywhere; }
@media (max-width:48rem) { body > header, body > nav, body > main, body > section,
  body > div, body > h1, body > h2, body > p { width:min(calc(100% - 1.2rem),var(--max)); }
  .defn,.theorem,.lemma,.cor,.prop,.example,.exercise,.rem,.proof { padding:.7rem .75rem; }
}
@media print { body { font-size:10.5pt; } nav#TOC { break-after:page; }
  a { color:inherit; text-decoration:none; } }
"""

MATHJAX_CONFIG = r"""
<script>
window.MathJax = {tex: {tags: 'ams', macros: {
  R: '\\mathbb{R}', N: '\\mathbb{N}', Z: '\\mathbb{Z}', Q: '\\mathbb{Q}',
  F: '\\mathbb{F}', bR: '\\overline{\\mathbb{R}}', Rb: '\\overline{\\mathbb{R}}',
  inner: ['\\left\\langle #1,#2\\right\\rangle', 2],
  norm: ['\\left\\lVert #1\\right\\rVert', 1],
  abs: ['\\left|#1\\right|', 1],
  dom: '\\operatorname{dom}', epi: '\\operatorname{epi}', conv: '\\operatorname{conv}',
  tr: '\\operatorname{tr}', prox: '\\operatorname{prox}', proj: '\\operatorname{proj}',
  sign: '\\operatorname{sign}', Id: '\\operatorname{Id}', dd: '\\mathrm{d}',
  emptyarg: '\\,\\cdot\\,', bigstar: '\\star', coloneqq: ':=', coloneq: ':=',
  eqqcolon: '=:', setto: '\\rightrightarrows', wkto: '\\rightharpoonup',
  Exp: '\\mathbb{E}', Var: '\\mathbb{V}', Cov: '\\operatorname{Cov}', Prob: '\\mathbb{P}'
}}};
</script>
"""

INTRO = r"""
\begin{quote}
\textbf{Status pembaca.} Edisi Bahasa Indonesia ini memuat terjemahan lengkap
sembilan bab dari Andreas Habring, \emph{Lecture Notes: Convex Optimization},
arXiv:2607.11664v1. Ini adalah karya turunan mandiri, bukan edisi resmi atau
dukungan penulis sumber maupun TU Graz. Rumus, bukti, latihan, gambar yang
diizinkan, dan urutan sumber dipertahankan; koreksi yang dapat ditentukan
ditandai dan direkam dalam ledger edisi.

Sumber dan terjemahan tersedia berdasarkan Creative Commons Attribution 4.0
International (CC BY 4.0). Provenans produksi: OpenAI Codex gpt-5.6-sol, Ultra,
atas instruksi pengguna repositori; seluruh kredit penulis dan sumber tetap
dipertahankan.
\end{quote}
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_combined_source() -> None:
    missing = [str(path) for path in CHAPTERS if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing translated chapters: " + ", ".join(missing))
    parts = [INTRO]
    for path in CHAPTERS:
        parts.append(f"\n% html-source: {path.name}\n")
        chapter = path.read_text(encoding="utf-8")
        # Pandoc does not perform TeX's extension search for these two legacy
        # image references; make the already-registered PNG component explicit.
        chapter = chapter.replace(
            r"{figures/gradient}", r"{figures/gradient.png}"
        ).replace(
            r"{figures/subgradient}", r"{figures/subgradient.png}"
        )
        parts.append(chapter)
    COMBINED_TEX.write_text(
        "\n".join(parts).replace("\r\n", "\n") + "\n",
        encoding="utf-8",
        newline="\n",
    )


def run_pandoc(destination: Path) -> None:
    resource_path = os.pathsep.join(
        [str(SOURCE_DIR), str(ROOT / "authority" / "habring" / "source-v1")]
    )
    command = [
        "pandoc",
        str(COMBINED_TEX),
        "--from=latex",
        "--to=html5",
        "--standalone",
        "--toc",
        "--toc-depth=3",
        "--section-divs",
        "--embed-resources",
        f"--resource-path={resource_path}",
        "--mathjax=https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
        "--metadata=lang:id-ID",
        "--metadata=title:Optimisasi Konveks — Edisi Bahasa Indonesia",
        "--metadata=author:Andreas Habring; terjemahan/adaptasi mandiri",
        f"--output={destination}",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode:
        raise RuntimeError(completed.stdout + completed.stderr)
    html = destination.read_text(encoding="utf-8")
    head_additions = (
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="license" content="CC BY 4.0">\n'
        + MATHJAX_CONFIG
        + "\n<style>\n"
        + CSS
        + "\n</style>\n"
    )
    if "</head>" not in html:
        raise RuntimeError("Pandoc output lacks </head>")
    html = html.replace("</head>", head_additions + "</head>", 1)

    # Pandoc preserves the source image order but cannot infer useful
    # alternatives from LaTeX captions. Bind explicit Indonesian alternatives
    # to the five raster surfaces that survive the LaTeX-to-HTML conversion.
    alt_texts = iter(
        [
            "Baris atas menampilkan himpunan konveks; baris bawah menampilkan himpunan tak konveks.",
            "Bola norma p untuk beberapa nilai p; kasus p sama dengan satu per dua tidak konveks.",
            "Perbandingan grafik fungsi konveks dan fungsi tak konveks dalam satu dimensi.",
            "Gradien sebagai kemiringan garis singgung.",
            "Subgradien sebagai kemiringan garis pendukung.",
        ]
    )

    def bind_alt(match: re.Match[str]) -> str:
        tag = match.group(0)
        existing = re.search(r'\balt="([^"]*)"', tag, re.IGNORECASE)
        if existing and existing.group(1).strip().lower() not in {"", "image"}:
            return tag
        try:
            alt = next(alt_texts)
        except StopIteration as exc:
            raise RuntimeError("Unexpected raster image without alternative text") from exc
        if existing:
            return (
                tag[: existing.start()]
                + f'alt="{alt}"'
                + tag[existing.end() :]
            )
        return tag[:-1] + f' alt="{alt}">'

    html = re.sub(r"<img\b[^>]*>", bind_alt, html, flags=re.IGNORECASE)

    # Pandoc leaves equation labels inside the TeX payload. Add the same
    # locale-neutral label as the HTML id on the display wrapper so every
    # source cross-reference has a real fragment target.
    def bind_equation_id(match: re.Match[str]) -> str:
        attrs, payload = match.group(1), match.group(2)
        labels = re.findall(r"\\label\{([^{}]+)\}", payload)
        if not labels or re.search(r"\bid=", attrs, re.IGNORECASE):
            return match.group(0)
        if len(set(labels)) != 1:
            raise RuntimeError(f"Ambiguous equation labels: {labels}")
        label = labels[0]
        return f'<span id="{label}" class="math display"{attrs}>{payload}</span>'

    html = re.sub(
        r'<span class="math display"([^>]*)>(.*?)</span>',
        bind_equation_id,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    destination.write_text(html, encoding="utf-8", newline="\n")


def validate(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    required = [
        '<html xmlns="http://www.w3.org/1999/xhtml" lang="id-ID"',
        'name="viewport"',
        "CC BY 4.0",
        "Prasyarat",
        "Kekonveksan",
        "Subgradien",
        "Penurunan subgradien terproyeksi",
        "Metode gradien proksimal",
        "Akselerasi",
        "Dualitas",
        "Penurunan Gradien Stokastik",
        "Transportasi Optimal",
    ]
    for marker in required:
        if marker not in text:
            failures.append(f"missing required marker: {marker}")
    if not re.search(
        r"OpenAI\s+Codex\s+gpt-5\.6-sol,\s+Ultra", text, re.IGNORECASE
    ):
        failures.append("missing exact model-provenance marker")
    if "\\begin{tikzpicture}" in text:
        failures.append("raw TikZ leaked into HTML")
    if re.search(r'<img\b(?![^>]*\balt=)[^>]*>', text, re.IGNORECASE):
        failures.append("image without alt attribute")
    ids = re.findall(r'\bid="([^"]+)"', text)
    duplicate_ids = sorted({item for item in ids if ids.count(item) > 1})
    if duplicate_ids:
        failures.append(f"duplicate ids: {duplicate_ids}")
    fragment_targets = re.findall(r'<a[^>]+\bhref="#([^"]+)"', text)
    missing_fragments = sorted(set(fragment_targets) - set(ids))
    if missing_fragments:
        failures.append(f"missing fragment targets: {missing_fragments}")
    external_images = re.findall(r'<img[^>]+src="(?!data:)([^"]+)"', text)
    if external_images:
        failures.append(f"nonembedded image sources: {external_images}")
    if failures:
        raise RuntimeError("HTML validation failed: " + repr(failures))
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "chapter_h1_count": len(re.findall(r"<h1\b", text)),
        "section_h2_count": len(re.findall(r"<h2\b", text)),
        "math_inline_count": text.count('class="math inline"'),
        "math_display_count": text.count('class="math display"'),
        "embedded_image_count": len(re.findall(r'<img[^>]+src="data:', text)),
        "failures": failures,
    }


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    build_combined_source()
    run_pandoc(FIRST_HTML)
    first = FIRST_HTML.read_bytes()
    run_pandoc(OUTPUT_HTML)
    if first != OUTPUT_HTML.read_bytes():
        raise RuntimeError("Two Habring HTML builds were not byte-identical")
    result = validate(OUTPUT_HTML)
    report = {
        "schema": "o015-habring-full-html-build-v1",
        "result": "pass",
        "artifact": {
            "path": OUTPUT_HTML.relative_to(ROOT).as_posix(),
            **result,
        },
        "inputs": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in CHAPTERS
        ],
        "determinism": {"builds": 2, "byte_identical": True},
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    FIRST_HTML.unlink(missing_ok=True)
    COMBINED_TEX.unlink(missing_ok=True)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
