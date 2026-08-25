#!/usr/bin/env python3
"""Build the responsive semantic HTML reader for Becker supplement 1."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BODY = ROOT / "source" / "id-ID" / "becker-01-dualitas-lagrange-slater-kkt-id.tex"
TMP = ROOT / "tmp" / "becker-01-html"
COMBINED = TMP / "becker-01-combined.tex"
FIRST = TMP / "becker-01-first.html"
OUTPUT = ROOT / "output" / "html" / "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html"
REPORT = ROOT / "qa" / "BECKER_01_HTML_BUILD.json"

PREAMBLE = r"""
\newcommand{\R}{\mathbb{R}}
\newcommand{\norm}[1]{\left\lVert #1\right\rVert}
\newcommand{\prox}{\operatorname{prox}}
\newcommand{\emptyarg}{\,\cdot\,}
"""

INTRO = r"""
\begin{quote}
\textbf{Status pembaca.} Modul ini menerjemahkan lima rentang terpilih dari
Stephen Becker, \emph{convex-optimization-class}, commit
\texttt{98ed6930084c435ba0f675f7646ced1f2fd8729e}; catatan ketik sumber
mengreditkan Mitchell Krock. Bagian program-linear yang bersebelahan dikeluarkan
agar tidak menduplikasi O018. Materi donor mempertahankan Lisensi MIT;
terjemahan, koreksi, dan penghubung mandiri tersedia berdasarkan CC BY-SA 4.0.
Ini bukan edisi resmi atau dukungan pihak sumber.

Provenans produksi: OpenAI Codex gpt-5.6-sol, Ultra, atas instruksi pengguna
repositori; seluruh kredit penulis dan kontributor manusia tetap dipertahankan.
\end{quote}
"""

OUTRO = r"""
\section*{Perubahan dan batas sumber}
Edisi membetulkan batas penjumlahan Lagrangian, orientasi nilai primal pada
dualitas lemah, hipotesis Slater dan KKT, definisi titik pelana, skala penalti
norma satu, relasi Moreau untuk proyeksi bola norma satu, serta syarat
ketunggalan sistem KKT kuadratik. Rentang program-linear 1322-1397,
1406-1413, dan 1727-1730 tidak masuk O015. Rincian beridentitas sumber ada
dalam ledger dan manifest edisi.

\section*{Atribusi, lisensi, dan nondukungan}
Sumber: Stephen Becker, repositori \emph{convex-optimization-class}; catatan
ketik \emph{APPM5720Notes} oleh Mitchell Krock; commit
\texttt{98ed6930084c435ba0f675f7646ced1f2fd8729e};
\url{https://github.com/stephenbeckr/convex-optimization-class}. Materi donor
menyatakan bahwa bagian dualitas mengikuti Bab~5 Boyd dan Vandenberghe
(B\&V), merujuk ke \S5.3 untuk ilustrasi, dan mengaitkan satu interpretasi
geometri dengan Bertsekas; kredit turunan tersebut dipertahankan. Materi donor
berada di bawah Lisensi MIT. Terjemahan, koreksi, dan penghubung mandiri
tersedia berdasarkan Creative Commons Attribution-ShareAlike 4.0 International,
\url{https://creativecommons.org/licenses/by-sa/4.0/}. Stephen Becker,
Mitchell Krock, dan University of Colorado Boulder tidak menyusun, memeriksa,
menyetujui, atau mendukung edisi ini.

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
body { margin:0; padding:0; width:100%; max-width:none; overflow-x:clip;
  color:var(--ink); background:#fff;
  font-family:Georgia,"Times New Roman",serif;
  font-size:clamp(1rem,.96rem + .18vw,1.12rem); line-height:1.64; }
body > header, body > nav, body > main, body > section, body > div,
body > h1, body > h2, body > p, body > blockquote, body > pre {
  width:min(calc(100% - 2.2rem),var(--max)); margin-inline:auto; }
header#title-block-header { padding:3rem 0 1.5rem; border-bottom:1px solid var(--rule); }
h1,h2,h3,h4 { max-width:76ch; margin-inline:auto;
  font-family:Arial,Helvetica,sans-serif; line-height:1.2; color:#12233d;
  scroll-margin-top:1rem; }
h1 { margin-top:2.7rem; font-size:clamp(1.9rem,1.4rem + 1.8vw,3rem); }
header#title-block-header h1 {
  font-size:clamp(1.9rem,1.35rem + 1.55vw,2.65rem); }
h2 { margin-top:2.3rem; font-size:clamp(1.45rem,1.2rem + .8vw,2rem); }
h3 { margin-top:1.8rem; }
a { color:#174f91; text-underline-offset:.14em; }
nav#TOC { margin:1.5rem auto 2.5rem; padding:1rem 1.3rem;
  background:var(--panel); border:1px solid var(--rule); border-radius:.45rem; }
nav#TOC ul { padding-left:1.35rem; }
p, blockquote, pre { max-width:72ch; }
ol,ul { width:min(100%,76ch); margin-inline:auto; }
li { max-width:72ch; }
.definition,.theorem,.example,.proof,div[class*="theorem"],div[class*="definition"] {
  max-width:76ch; margin:1.25rem auto; padding:.85rem 1rem;
  border-left:.28rem solid var(--accent); background:var(--panel); }
.proof { border-left-color:#65758c; background:#fafbfc; }
blockquote { padding:.8rem 1rem; background:var(--panel); border-left:.28rem solid var(--accent); }
.math.display, mjx-container[display="true"] { display:block; width:100%; max-width:100%;
  overflow-x:auto; overflow-y:hidden; padding:.35rem 0; }
.math.inline { display:inline; max-width:none; overflow:visible;
  vertical-align:baseline; }
pre { overflow-x:auto; padding:1rem; background:#f7f8fa; border:1px solid var(--rule); }
@media (max-width:48rem) { body > header, body > nav, body > main, body > section,
  body > div, body > h1, body > h2, body > p, body > blockquote, body > pre {
  width:min(calc(100% - 1.2rem),var(--max)); }
  .definition,.theorem,.example,.proof,div[class*="theorem"],div[class*="definition"] {
    padding:.7rem .75rem; }
}
"""

MATHJAX_CONFIG = r"""
<script>
window.MathJax = {tex: {tags:'ams', macros: {
  R:'\\mathbb{R}', norm:['\\left\\lVert #1\\right\\rVert',1],
  prox:'\\operatorname{prox}', emptyarg:'\\,\\cdot\\,'
}}};
</script>
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_source() -> None:
    body = BODY.read_text(encoding="utf-8")
    body = body.replace(r"\begin{defn}", r"\begin{definition}")
    body = body.replace(r"\end{defn}", r"\end{definition}")
    COMBINED.write_text(
        PREAMBLE + "\n" + INTRO + "\n" + body + "\n" + OUTRO,
        encoding="utf-8",
        newline="\n",
    )


def run_pandoc(destination: Path) -> None:
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
        "--metadata=title:Optimisasi Lanjut dan Analisis Konveks - Modul Becker 1",
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
    if "</head>" not in html:
        raise RuntimeError("Pandoc output lacks a head element")
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

    # Pandoc preserves LaTeX equation labels inside MathJax source but emits
    # external references to those labels without corresponding HTML anchors.
    # Mirror each equation label onto its containing display span so every
    # generated fragment is resolvable while MathJax keeps native numbering.
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
        "becker:eq:primal": "primal",
        "becker:eq:lagrangian": "di atas",
        "becker:eq:weak-duality": "ketaksamaan dualitas lemah",
    }
    for label, readable in reference_text.items():
        html = re.sub(
            rf'(<a\s+href="#{re.escape(label)}"[^>]*>).*?(</a>)',
            rf'\1{readable}\2',
            html,
            flags=re.DOTALL,
        )
    destination.write_text(html, encoding="utf-8", newline="\n")


def validate(path: Path) -> dict[str, object]:
    html = path.read_text(encoding="utf-8")
    lower = html.casefold()
    required = [
        'lang="id-ID"'.casefold(),
        'name="viewport"',
        "dualitas lagrange",
        "kondisi slater",
        "karush-kuhn-tucker",
        "proyeksi pada bola",
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
        failures.append("raw LaTeX environment leaked into HTML")
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
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "h1_count": len(re.findall(r"<h1\b", html)),
        "h2_count": len(re.findall(r"<h2\b", html)),
        "math_inline_count": html.count('class="math inline"'),
        "math_display_count": html.count('class="math display"'),
        "ids": len(ids),
        "fragment_links": len(fragments),
        "failures": failures,
    }


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    build_source()
    run_pandoc(FIRST)
    run_pandoc(OUTPUT)
    if FIRST.read_bytes() != OUTPUT.read_bytes():
        raise RuntimeError("Two HTML builds are not byte-identical")
    artifact = validate(OUTPUT)
    report = {
        "schema": "o015-becker-01-html-build-v1",
        "result": "pass",
        "byte_identical_builds": True,
        "inputs": [
            {
                "path": BODY.relative_to(ROOT).as_posix(),
                "bytes": BODY.stat().st_size,
                "sha256": sha256(BODY),
            }
        ],
        "artifact": {"path": OUTPUT.relative_to(ROOT).as_posix(), **artifact},
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
