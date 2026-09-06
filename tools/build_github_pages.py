#!/usr/bin/env python3
"""Build and verify the D90 GitHub Pages reader site.

The 17 reader documents are pinned byte-for-byte to the open Zenodo record
22543810.  ``--sync`` anonymously downloads those exact files; every run
checks their recorded size/MD5, computes SHA-256, verifies the universal
navigation contract, and regenerates the deterministic landing page and
manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
READERS = DOCS / "readers"
MANIFEST = DOCS / "reader-manifest.json"
INDEX = DOCS / "index.html"

RECORD_ID = 22543810
RECORD_DOI = "https://doi.org/10.5281/zenodo.22543810"
PROGRAM_ID = "https://kokunoyumeto.github.io/program-matematika-indonesia/id/#course-D90"
PROGRAM_EN = "https://kokunoyumeto.github.io/program-matematika-indonesia/en/#course-D90"
ORIGINAL = "https://arxiv.org/pdf/2607.11664"
NAV_ID = "program-matematika-global-nav-v1"

# Public Zenodo API facts frozen from record 22543810 on 2026-09-06.
EXPECTED = {
    "D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html": (31279, "d871527c242fd31415dc3998eeb981c4"),
    "D90-BECKER-02-pemisahan-douglas-rachford-id.html": (19518, "f09c604bd1e40b775cfa1f0e386cd27e"),
    "D90-BECKER-03-reduksi-varians-id.html": (25470, "2f1c8a8fd5df32692d5314021d694544"),
    "D90-MIT-01-peran-kekonveksan-id.html": (21761, "6939277c930af9bba038471f84c2e8e6"),
    "D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.html": (39344, "b5e5d7f2fe74d7b72680018073f4f9e6"),
    "D90-MIT-03-pandangan-modern-optimisasi-konveks-id.html": (10910, "5394b94c767074de80548041351b9d56"),
    "D90-MIT-04-kebangkitan-era-algoritmik-id.html": (11123, "e6c68abfcf814e570b70bbd3faa70894"),
    "D90-MIT-05-orientasi-kursus-id.html": (17177, "ff54cc6bd58fd89ff0834faec85e24c7"),
    "D90-MIT-06-kuliah-2-landasan-konveks-id.html": (71594, "09e6869922dfe7b45d1e38505193542c"),
    "D90-MIT-07-kuliah-3-fungsi-konveks-terdiferensial-caratheodory-id.html": (78547, "7005a3cb16cfd09b06ad61fcdfab65a8"),
    "D90-MIT-08-kuliah-4-interior-relatif-penutupan-kontinuitas-id.html": (115046, "a582cf52976a92f0894a12b538d7fb3b"),
    "D90-MIT-09-kuliah-5-resesi-dan-minimum-id.html": (119953, "1275a608f428c4c9e2ec7b566cdbad79"),
    "D90-MIT-10-kuliah-6-irisan-tertutup-dan-hiperbidang-id.html": (171019, "994bc63bf76e1f38acf4e761a9f25f1b"),
    "D90-MIT-11-kuliah-7-pemisahan-dan-konjugasi-id.html": (97364, "3fa1af7bc70448719c20fe1dc217bb10"),
    "D90-O015-optimisasi-lanjut-analisis-konveks-id.html": (2486743, "7f25d5e60a8a8fd7738b8985f59fc240"),
    "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html": (354393, "d741013444dc7409c7b626cfd03798aa"),
    "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html": (191551, "83a204787e206a3d1b6f54a64626bba6"),
}


def digest(data: bytes, algorithm: str) -> str:
    return hashlib.new(algorithm, data).hexdigest()


def source_url(name: str) -> str:
    quoted = urllib.parse.quote(name, safe="")
    return f"https://zenodo.org/api/records/{RECORD_ID}/files/{quoted}/content"


def download(name: str) -> bytes:
    request = urllib.request.Request(
        source_url(name), headers={"User-Agent": "d90-github-pages-builder/1.0"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise RuntimeError(f"{name}: HTTP {response.status}")
        return response.read()


def validate_reader(name: str, data: bytes) -> dict[str, object]:
    expected_bytes, expected_md5 = EXPECTED[name]
    if len(data) != expected_bytes:
        raise RuntimeError(f"{name}: {len(data)} bytes, expected {expected_bytes}")
    actual_md5 = digest(data, "md5")
    if actual_md5 != expected_md5:
        raise RuntimeError(f"{name}: MD5 {actual_md5}, expected {expected_md5}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"{name}: not UTF-8") from error
    if text.count(f'id="{NAV_ID}"') != 1:
        raise RuntimeError(f"{name}: universal navigation is not present exactly once")
    for required in (PROGRAM_ID, PROGRAM_EN, ORIGINAL):
        if text.count(required) != 1:
            raise RuntimeError(f"{name}: required link is not present exactly once: {required}")
    title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if not title_match:
        raise RuntimeError(f"{name}: missing title")
    title = html.unescape(re.sub(r"\s+", " ", title_match.group(1))).strip()
    return {
        "filename": name,
        "bytes": len(data),
        "md5": actual_md5,
        "sha256": digest(data, "sha256"),
        "title": title,
        "source_url": source_url(name),
        "reader_url": f"readers/{urllib.parse.quote(name)}",
    }


def group_name(filename: str) -> str:
    if filename.startswith("D90-O015"):
        return "Pembaca terpadu / Integrated reader"
    if filename.startswith("D90-ORIG"):
        return "Materi asli D90 / D90 original modules"
    if filename.startswith("D90-MIT"):
        return "Catatan MIT / MIT lecture sequence"
    return "Modul Becker / Becker modules"


def render_index(entries: list[dict[str, object]]) -> bytes:
    groups: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        groups.setdefault(group_name(str(entry["filename"])), []).append(entry)
    sections = []
    for heading, items in groups.items():
        cards = "\n".join(
            """<li><a href="{url}">{title}</a><span>{size:,} bytes</span></li>""".format(
                url=html.escape(str(item["reader_url"]), quote=True),
                title=html.escape(str(item["title"])),
                size=int(item["bytes"]),
            )
            for item in items
        )
        sections.append(f"<section><h2>{html.escape(heading)}</h2><ul>{cards}</ul></section>")
    body = "\n".join(sections)
    document = f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Pembaca HTML D90 untuk Optimisasi Lanjut dan Analisis Konveks.">
  <title>D90 — Optimisasi Lanjut dan Analisis Konveks</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #172033; background: #f4f7fb; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; line-height: 1.55; }}
    a {{ color: #174ea6; text-underline-offset: .16em; }}
    a:focus-visible {{ outline: .2rem solid #f59e0b; outline-offset: .2rem; }}
    main {{ width: min(92vw, 78rem); margin: 2rem auto 5rem; }}
    header {{ padding: clamp(1.5rem, 5vw, 4rem); border-radius: 1rem; color: #f8fafc; background: linear-gradient(135deg, #172554, #075985); }}
    h1 {{ max-width: 20ch; margin: 0; font-size: clamp(2rem, 5vw, 4rem); line-height: 1.05; }}
    header p {{ max-width: 65ch; font-size: 1.08rem; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: .65rem; margin-top: 1.2rem; }}
    .meta a {{ padding: .55rem .75rem; border-radius: .4rem; color: #082f49; background: #e0f2fe; font-weight: 700; }}
    section {{ margin-top: 1.5rem; padding: 1.2rem 1.4rem; border: 1px solid #cbd5e1; border-radius: .85rem; background: white; }}
    ul {{ display: grid; gap: .65rem; margin: 0; padding: 0; list-style: none; }}
    li {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: .5rem 1rem; padding: .7rem; border-radius: .5rem; background: #f8fafc; }}
    li a {{ font-weight: 700; }}
    li span {{ color: #526075; font-size: .88rem; }}
    #program-matematika-global-nav-v1 {{ box-sizing: border-box; width: 100%; margin: 0; padding: .85rem 1rem; display: flex; flex-wrap: wrap; align-items: center; gap: .65rem; background: #0f172a; color: #f8fafc; border-bottom: 4px solid #38bdf8; font: 600 1rem/1.4 system-ui, sans-serif; }}
    #program-matematika-global-nav-v1 a {{ padding: .45rem .7rem; border-radius: .35rem; color: #082f49; background: #bae6fd; }}
  </style>
</head>
<body>
<nav id="{NAV_ID}" aria-label="Navigasi program matematika / Mathematics program navigation">
  <strong>Program Matematika / Mathematics Program</strong>
  <a lang="id" href="{PROGRAM_ID}">Bahasa Indonesia</a>
  <a lang="en" href="{PROGRAM_EN}">English</a>
  <a href="{ORIGINAL}">Sumber asli / Authoritative original</a>
</nav>
<main>
  <header>
    <h1>Optimisasi Lanjut dan Analisis Konveks</h1>
    <p>Advanced Optimization and Convex Analysis — D90</p>
    <p>Semua 17 pembaca HTML dapat dibuka langsung, dicari, diperbesar, dan diunduh dari repositori ini. Each reader is directly browsable, searchable, zoomable, and downloadable.</p>
    <div class="meta">
      <a href="{RECORD_DOI}">Arsip Zenodo / Zenodo archive</a>
      <a href="https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id">Kode sumber / Source repository</a>
    </div>
  </header>
  {body}
</main>
</body>
</html>
"""
    return document.encode("utf-8")


def validate_index(data: bytes, entries: list[dict[str, object]]) -> None:
    text = data.decode("utf-8")
    if text.count(f'id="{NAV_ID}"') != 1:
        raise RuntimeError("index: universal navigation is not present exactly once")
    for required in (PROGRAM_ID, PROGRAM_EN, ORIGINAL):
        if text.count(required) != 1:
            raise RuntimeError(f"index: required link is not present exactly once: {required}")
    for entry in entries:
        if text.count(str(entry["reader_url"])) != 1:
            raise RuntimeError(f"index: reader link is not present exactly once: {entry['filename']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync", action="store_true", help="download pinned reader bytes from Zenodo")
    args = parser.parse_args()

    READERS.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    for name in sorted(EXPECTED):
        path = READERS / name
        if args.sync:
            data = download(name)
            path.write_bytes(data)
        elif not path.is_file():
            raise RuntimeError(f"missing reader: {path}")
        data = path.read_bytes()
        entries.append(validate_reader(name, data))

    extras = sorted(path.name for path in READERS.glob("*.html") if path.name not in EXPECTED)
    if extras:
        raise RuntimeError(f"unexpected reader HTML files: {extras}")

    index_data = render_index(entries)
    INDEX.write_bytes(index_data)
    validate_index(index_data, entries)
    (DOCS / ".nojekyll").write_bytes(b"")

    manifest = {
        "schema": "d90-github-pages-reader-manifest-v1",
        "source_record_id": RECORD_ID,
        "source_record_doi": RECORD_DOI,
        "reader_count": len(entries),
        "navigation_contract": {
            "nav_id": NAV_ID,
            "required_links": [PROGRAM_ID, PROGRAM_EN, ORIGINAL],
            "required_occurrences_per_html": 1,
        },
        "landing": {
            "path": "docs/index.html",
            "bytes": len(index_data),
            "sha256": digest(index_data, "sha256"),
        },
        "readers": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "pass",
                "reader_count": len(entries),
                "reader_bytes": sum(int(entry["bytes"]) for entry in entries),
                "manifest_sha256": digest(MANIFEST.read_bytes(), "sha256"),
                "index_sha256": digest(index_data, "sha256"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
