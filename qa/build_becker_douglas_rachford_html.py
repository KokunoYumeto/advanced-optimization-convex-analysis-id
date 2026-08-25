#!/usr/bin/env python3
"""Build the isolated responsive semantic HTML reader for Becker-02."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
BODY = ROOT / "source" / "id-ID" / "becker-02-pemisahan-douglas-rachford-id.tex"
WRAPPER = (
    ROOT
    / "source"
    / "id-ID"
    / "D90-BECKER-02-pemisahan-douglas-rachford-id.tex"
)
WITNESS = ROOT / "source" / "en" / "becker-02-douglas-rachford-source.tex"
EXTRACTOR = ROOT / "qa" / "extract_becker_douglas_rachford_source.py"
SOURCE_REPORT = ROOT / "qa" / "BECKER_02_SOURCE_BOUNDARY.json"
TMP = ROOT / "tmp" / "becker-02-html"
COMBINED = TMP / "becker-02-combined.tex"
RUN1 = TMP / "run1.html"
RUN2 = TMP / "run2.html"
OUTPUT = (
    ROOT
    / "output"
    / "html"
    / "D90-BECKER-02-pemisahan-douglas-rachford-id.html"
)
REPORT = ROOT / "qa" / "BECKER_02_HTML_BUILD.json"

PREAMBLE = r"""
\newcommand{\R}{\mathbb{R}}
\newcommand{\norm}[1]{\left\lVert #1\right\rVert}
\newcommand{\prox}{\operatorname{prox}}
"""

INTRO = r"""
\begin{quote}
\textbf{Status pembaca.} Modul ini menerjemahkan tepat baris 2750--2797 dari
Stephen Becker, \emph{convex-optimization-class}, commit
\texttt{98ed6930084c435ba0f675f7646ced1f2fd8729e}; catatan ketik sumber
mengreditkan Mitchell Krock. Catatan donor mengreditkan Bauschke dan Combettes
serta Lions dan Mercier. Materi program linear dan bagian ADMM yang
bersebelahan tidak diimpor. Materi donor mempertahankan Lisensi MIT;
terjemahan, koreksi, dan penghubung mandiri tersedia berdasarkan CC BY-SA 4.0.
Ini bukan edisi resmi atau dukungan pihak sumber.

Provenans produksi: OpenAI Codex gpt-5.6-sol, Ultra, atas instruksi pengguna
repositori; seluruh kredit penulis dan kontributor manusia tetap dipertahankan.
\end{quote}
"""

OUTRO = r"""
\section*{Perubahan dan batas sumber}
Edisi menormalkan notasi subdiferensial, membetulkan tanda dual Fenchel,
memulihkan faktor $\rho$ dalam derivasi titik tetap, memperjelas bukti limit
bayangan, dan menyatakan hubungan ADMM sebagai pemisahan Douglas--Rachford pada
masalah dual yang sesuai. Salah eja nama Mercier dibetulkan. Tidak ada isi di
luar baris 2750--2797 yang diterjemahkan ke dalam unit ini.

\section*{Atribusi, lisensi, dan nondukungan}
Sumber: Stephen Becker, repositori \emph{convex-optimization-class}; catatan
ketik \emph{APPM5720Notes} oleh Mitchell Krock; commit
\texttt{98ed6930084c435ba0f675f7646ced1f2fd8729e};
\url{https://github.com/stephenbeckr/convex-optimization-class}. Catatan donor
menyatakan bahwa bagian ini mengikuti Bauschke dan Combettes, edisi kedua
(2017), \S20.3, serta mengatribusi analisis Douglas--Rachford kepada Lions dan
Mercier (1979). Materi donor berada di bawah Lisensi MIT. Terjemahan, koreksi,
dan penghubung mandiri tersedia berdasarkan Creative Commons
Attribution-ShareAlike 4.0 International,
\url{https://creativecommons.org/licenses/by-sa/4.0/}. Stephen Becker,
Mitchell Krock, Bauschke, Combettes, Lions, Mercier, dan University of Colorado
Boulder tidak menyusun, memeriksa, menyetujui, atau mendukung edisi ini.

\section*{Pemberitahuan Lisensi MIT sumber}
\begin{verbatim}
MIT License

Copyright (c) 2017 Stephen Becker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
\end{verbatim}
"""

CSS = r"""
:root { color-scheme:light; --ink:#172033; --muted:#506078; --rule:#ccd5e2;
  --accent:#315f99; --panel:#f4f7fb; --max:76rem; }
* { box-sizing:border-box; }
html { font-size:100%; scroll-behavior:smooth; }
body { margin:0; width:100%; max-width:none; overflow-x:clip; color:var(--ink);
  background:#fff; font-family:Georgia,"Times New Roman",serif;
  font-size:clamp(1rem,.96rem + .18vw,1.12rem); line-height:1.64; }
main#reader { width:min(calc(100% - 2.2rem),var(--max)); margin-inline:auto;
  padding:0 0 3rem; }
header#title-block-header { padding:3rem 0 1.5rem; border-bottom:1px solid var(--rule); }
h1,h2,h3,h4 { max-width:76ch; margin-inline:auto;
  font-family:Arial,Helvetica,sans-serif; line-height:1.2; color:#12233d;
  scroll-margin-top:1rem; }
h1 { margin-top:2.7rem; font-size:clamp(1.9rem,1.4rem + 1.8vw,3rem); }
header#title-block-header h1 { font-size:clamp(1.9rem,1.35rem + 1.55vw,2.65rem); }
h2 { margin-top:2.3rem; font-size:clamp(1.45rem,1.2rem + .8vw,2rem); }
h3 { margin-top:1.8rem; }
a { color:#174f91; text-underline-offset:.14em; }
nav#TOC { margin:1.5rem auto 2.5rem; padding:1rem 1.3rem;
  background:var(--panel); border:1px solid var(--rule); border-radius:.45rem; }
nav#TOC ul { padding-left:1.35rem; }
p,blockquote,pre { max-width:72ch; margin-inline:auto; }
ol,ul { width:min(100%,76ch); margin-inline:auto; }
li { max-width:72ch; }
.definition,.theorem,.example,.proof,div[class*="theorem"],div[class*="definition"] {
  max-width:76ch; margin:1.25rem auto; padding:.85rem 1rem;
  border-left:.28rem solid var(--accent); background:var(--panel); }
.proof { border-left-color:#65758c; background:#fafbfc; }
blockquote { padding:.8rem 1rem; background:var(--panel); border-left:.28rem solid var(--accent); }
.math.display,mjx-container[display="true"] { display:block; width:100%; max-width:100%;
  overflow-x:auto; overflow-y:hidden; padding:.35rem 0; }
.math.inline { display:inline; max-width:none; overflow:visible; vertical-align:baseline; }
pre { overflow-x:auto; padding:1rem; background:#f7f8fa; border:1px solid var(--rule); }
@media (max-width:48rem) { main#reader { width:calc(100% - 1.2rem); }
  .definition,.theorem,.example,.proof,div[class*="theorem"],div[class*="definition"] {
    padding:.7rem .75rem; }
}
"""

MATHJAX_CONFIG = r"""
<script>
window.MathJax = {tex: {tags:'ams', macros: {
  R:'\\mathbb{R}', norm:['\\left\\lVert #1\\right\\rVert',1],
  prox:'\\operatorname{prox}'
}}};
</script>
"""


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


def clean_tmp() -> None:
    TMP.resolve().relative_to((ROOT / "tmp").resolve())
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)


def build_source() -> None:
    body = BODY.read_text(encoding="utf-8")
    body = body.replace(r"\begin{defn}", r"\begin{definition}")
    body = body.replace(r"\end{defn}", r"\end{definition}")
    COMBINED.write_text(
        PREAMBLE + "\n" + INTRO + "\n" + body + "\n" + OUTRO,
        encoding="utf-8",
        newline="\n",
    )


def run_pandoc(destination: Path) -> dict[str, object]:
    command = [
        "pandoc",
        str(COMBINED),
        "--from=latex",
        "--to=html5",
        "--standalone",
        "--toc",
        "--toc-depth=3",
        "--section-divs",
        "--mathjax=https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
        "--metadata=lang:id-ID",
        "--metadata=title:Optimisasi Lanjut dan Analisis Konveks - Modul Becker 2: Pemisahan Douglas-Rachford",
        "--metadata=author:Stephen Becker; catatan ketik Mitchell Krock; terjemahan mandiri",
        f"--output={destination}",
    ]
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
        raise RuntimeError(completed.stdout + completed.stderr)
    html = destination.read_text(encoding="utf-8")
    additions = (
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="license" content="MIT; CC BY-SA 4.0">\n'
        + "<style>\n"
        + CSS
        + "\n</style>\n"
    )
    if "</head>" not in html or "<body>" not in html or "</body>" not in html:
        raise RuntimeError("Pandoc output lacks required document elements")
    mathjax_pattern = (
        r'<script\b[^>]*\bsrc="https://cdn\.jsdelivr\.net/npm/'
        r'mathjax@3/es5/tex-mml-chtml\.js"'
    )
    if not re.search(mathjax_pattern, html):
        raise RuntimeError("Pandoc output lacks the pinned MathJax script")
    html = re.sub(
        mathjax_pattern,
        lambda match: MATHJAX_CONFIG + "\n" + match.group(0),
        html,
        count=1,
    )
    html = html.replace("</head>", additions + "</head>", 1)
    html = html.replace("<body>", '<body>\n<main id="reader">', 1)
    html = html.replace("</body>", "</main>\n</body>", 1)

    def anchor_display(match: re.Match[str]) -> str:
        attributes, payload = match.group(1), match.group(2)
        label = re.search(r"\\label\{([^}]+)\}", payload)
        if not label or re.search(r'\bid="', attributes):
            return match.group(0)
        return f'<span{attributes} id="{label.group(1)}">{payload}</span>'

    html = re.sub(
        r'<span([^>]*class="math display"[^>]*)>(.*?)</span>',
        anchor_display,
        html,
        flags=re.DOTALL,
    )
    reference_text = {
        "becker:eq:dr-prox-definition": "definisi operator proksimal",
        "becker:eq:dr-iteration": "iterasi Douglas--Rachford",
        "becker:eq:dr-primal": "masalah primal",
        "becker:eq:dr-sum-rule": "aturan jumlah",
    }
    for label, readable in reference_text.items():
        html = re.sub(
            rf'(<a\s+href="#{re.escape(label)}"[^>]*>).*?(</a>)',
            rf"\1{readable}\2",
            html,
            flags=re.DOTALL,
        )
    destination.write_text(html, encoding="utf-8", newline="\n")
    return {
        "command": command,
        "console_sha256": hashlib.sha256(
            (completed.stdout + completed.stderr).encode("utf-8")
        ).hexdigest(),
        "artifact": file_record(destination),
    }


def validate(path: Path) -> dict[str, object]:
    html = path.read_text(encoding="utf-8")
    lower = html.casefold()
    required = [
        'lang="id-ID"'.casefold(),
        'name="viewport"',
        '<main id="reader">',
        '<nav id="TOC"'.casefold(),
        "pemisahan douglas",
        "bauschke dan combettes",
        "lions dan mercier",
        "konjugat fenchel",
        "limit bayangan",
        "hubungan dengan admm",
        "mit license",
        "cc by-sa 4.0",
        "openai codex gpt-5.6-sol, ultra",
    ]
    failures = [f"missing marker: {item}" for item in required if item not in lower]
    prose_only = re.sub(
        r'<span[^>]*class="math (?:display|inline)"[^>]*>.*?</span>',
        "",
        html,
        flags=re.DOTALL,
    )
    if re.search(r"\\begin\{|\\end\{", prose_only):
        failures.append("raw LaTeX environment leaked into HTML prose")
    ids = re.findall(r'\bid="([^"]+)"', html)
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        failures.append(f"duplicate ids: {duplicates}")
    fragments = re.findall(r'<a[^>]+href="#([^"]+)"', html)
    missing_fragments = sorted(set(fragments) - set(ids))
    if missing_fragments:
        failures.append(f"missing fragments: {missing_fragments}")
    if re.search(r"\bttp\b", lower):
        failures.append("forbidden TTP prose marker")
    if failures:
        raise RuntimeError("HTML validation failed: " + repr(failures))
    return {
        "h1_count": len(re.findall(r"<h1\b", html)),
        "h2_count": len(re.findall(r"<h2\b", html)),
        "h3_count": len(re.findall(r"<h3\b", html)),
        "main_count": len(re.findall(r'<main\b', html)),
        "nav_count": len(re.findall(r'<nav\b', html)),
        "section_count": len(re.findall(r'<section\b', html)),
        "math_inline_count": html.count('class="math inline"'),
        "math_display_count": html.count('class="math display"'),
        "ids": len(ids),
        "fragment_links": len(fragments),
        "required_markers": required,
        "failures": failures,
    }


def pandoc_version() -> str:
    completed = subprocess.run(
        ["pandoc", "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return completed.stdout.splitlines()[0]


def main() -> None:
    subprocess.run([sys.executable, os.fspath(EXTRACTOR)], cwd=ROOT, check=True)
    inputs = [BODY, WRAPPER, WITNESS, EXTRACTOR, SOURCE_REPORT, SCRIPT]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing Becker-02 HTML inputs: " + ", ".join(missing))
    if "OpenAI Codex gpt-5.6-sol, Ultra" not in WRAPPER.read_text(encoding="utf-8"):
        raise RuntimeError("Expected live Becker-02 model marker is missing")
    input_records = [file_record(path) for path in inputs]

    clean_tmp()
    build_source()
    run1 = run_pandoc(RUN1)
    run2 = run_pandoc(RUN2)
    if input_records != [file_record(path) for path in inputs]:
        raise RuntimeError("Becker-02 HTML inputs changed during the clean builds")
    if RUN1.read_bytes() != RUN2.read_bytes():
        raise RuntimeError("Two clean Becker-02 HTML builds are not byte-identical")
    validation = validate(RUN1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(RUN1, OUTPUT)
    if OUTPUT.read_bytes() != RUN1.read_bytes():
        raise RuntimeError("Canonical Becker-02 HTML differs from validated build")
    report = {
        "schema": "o015-becker-02-html-build-v1",
        "result": "pass",
        "byte_identical_clean_builds": True,
        "canonical_copy_exact_match": True,
        "tool_versions": {"pandoc": pandoc_version()},
        "inputs": input_records,
        "intermediate": file_record(COMBINED),
        "runs": [run1, run2],
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
