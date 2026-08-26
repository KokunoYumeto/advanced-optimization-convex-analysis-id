#!/usr/bin/env python3
"""Validate Original-01 EPUB conformance and emit a sanitized receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
EPUB = ROOT / "output" / "epub" / (
    "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub"
)
BUILD_RECEIPT = ROOT / "qa" / "ORIGINAL_01_EPUB_BUILD.json"
REPORT = ROOT / "qa" / "ORIGINAL_01_EPUB_CONFORMANCE.json"
DEFAULT_JAR = ROOT / "tmp" / "tools" / "epubcheck-5.3.0" / "epubcheck.jar"
CHECK_JSON = ROOT / "build" / "original-01" / "epubcheck-5.3.0.json"
RIGHTS = (
    "Mixed rights: new Original-01 content CC BY-SA 4.0; "
    "shinybook.cls and macros-id.tex CC BY 4.0"
)
LAB_FILES = (
    ROOT / "labs" / "original-01" / "stochastic-composite-lab.py",
    ROOT / "labs" / "original-01" / "results.json",
    ROOT / "labs" / "original-01" / "results.csv",
    ROOT / "labs" / "original-01" / "objective-gap.svg",
)
OFFICIAL_RELEASE = (
    "https://github.com/w3c/epubcheck/releases/tag/v5.3.0"
)
OFFICIAL_ZIP = (
    "https://github.com/w3c/epubcheck/releases/download/v5.3.0/"
    "epubcheck-5.3.0.zip"
)
OFFICIAL_ZIP_BYTES = 33_071_108
OFFICIAL_ZIP_SHA256 = (
    "6c07e68584b2e2ce2f89fe06e1246dfead3eb36b46b340e7d93524f29dcff6c5"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def record(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def resolve_member(base: str, href: str) -> str:
    path = unquote(urlsplit(href).path)
    return str(PurePosixPath(base).parent.joinpath(path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epubcheck-jar", type=Path, default=DEFAULT_JAR)
    args = parser.parse_args()
    jar = args.epubcheck_jar.resolve()
    if not jar.is_file():
        raise FileNotFoundError(f"EPUBCheck jar not found: {jar}")

    CHECK_JSON.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "java",
            "-jar",
            str(jar),
            str(EPUB),
            "--failonwarnings",
            "--json",
            str(CHECK_JSON),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        assessment = json.loads(CHECK_JSON.read_text(encoding="utf-8"))
    finally:
        CHECK_JSON.unlink(missing_ok=True)
    checker = assessment["checker"]
    counts = {
        "fatal": int(checker["nFatal"]),
        "error": int(checker["nError"]),
        "warning": int(checker["nWarning"]),
        "usage": int(checker["nUsage"]),
    }
    if completed.returncode != 0 or any(counts.values()):
        raise RuntimeError(
            f"EPUBCheck failed: exit={completed.returncode}, counts={counts}"
        )
    if checker["checkerVersion"] != "5.3.0":
        raise RuntimeError(f"Unexpected EPUBCheck version: {checker['checkerVersion']}")

    with zipfile.ZipFile(EPUB) as package:
        infos = package.infolist()
        if not infos or infos[0].filename != "mimetype":
            raise RuntimeError("mimetype is not the first EPUB member")
        if infos[0].compress_type != zipfile.ZIP_STORED:
            raise RuntimeError("mimetype member is compressed")
        if package.read("mimetype") != b"application/epub+zip":
            raise RuntimeError("Unexpected mimetype payload")

        container = ET.fromstring(package.read("META-INF/container.xml"))
        rootfiles = [node for node in container.iter() if local_name(node.tag) == "rootfile"]
        if len(rootfiles) != 1:
            raise RuntimeError(f"Expected one rootfile, found {len(rootfiles)}")
        rootfile = rootfiles[0].attrib["full-path"]
        opf = ET.fromstring(package.read(rootfile))
        manifest = next(node for node in opf.iter() if local_name(node.tag) == "manifest")
        metadata = next(node for node in opf.iter() if local_name(node.tag) == "metadata")
        items = {
            node.attrib["id"]: node.attrib
            for node in manifest
            if local_name(node.tag) == "item"
        }

        rights = [
            "".join(node.itertext()).strip()
            for node in metadata
            if local_name(node.tag) == "rights"
        ]
        if rights != [RIGHTS]:
            raise RuntimeError(f"Unexpected rights metadata: {rights}")
        meta_values: dict[str, list[str]] = {}
        for node in metadata:
            if local_name(node.tag) == "meta" and node.attrib.get("property"):
                meta_values.setdefault(node.attrib["property"], []).append(
                    "".join(node.itertext()).strip()
                )
        features = set(meta_values.get("schema:accessibilityFeature", []))
        required_features = {
            "MathML",
            "alternativeText",
            "readingOrder",
            "structuralNavigation",
            "tableOfContents",
        }
        if not required_features <= features:
            raise RuntimeError(
                f"Missing accessibility features: {sorted(required_features - features)}"
            )
        summaries = meta_values.get("schema:accessibilitySummary", [])
        if len(summaries) != 1 or "MathML" not in summaries[0]:
            raise RuntimeError("Accessibility summary is absent or incomplete")

        opf_dir = PurePosixPath(rootfile).parent
        xhtml_members = sorted(
            str(opf_dir / item["href"])
            for item in items.values()
            if item.get("media-type") == "application/xhtml+xml"
        )
        identifiers: dict[str, set[str]] = {}
        hrefs: list[tuple[str, str]] = []
        mathml_count = 0
        image_alt_count = 0
        direct_lab_links: list[str] = []
        languages: set[tuple[str | None, str | None]] = set()
        for member in xhtml_members:
            document = ET.fromstring(package.read(member))
            languages.add(
                (
                    document.attrib.get("lang"),
                    document.attrib.get("{http://www.w3.org/XML/1998/namespace}lang"),
                )
            )
            ids = {node.attrib["id"] for node in document.iter() if "id" in node.attrib}
            identifiers[member] = ids
            if len(ids) != sum(1 for node in document.iter() if "id" in node.attrib):
                raise RuntimeError(f"Duplicate ID in {member}")
            for node in document.iter():
                if local_name(node.tag) == "math":
                    mathml_count += 1
                if local_name(node.tag) == "img" and node.attrib.get("alt", "").strip():
                    image_alt_count += 1
                href = node.attrib.get("href")
                if href:
                    hrefs.append((member, href))
                    if "/lab/" in href or href.startswith("../lab/"):
                        direct_lab_links.append(f"{member}: {href}")
        if languages != {("id-ID", "id-ID")}:
            raise RuntimeError(f"Unexpected XHTML languages: {languages}")
        if mathml_count != 249:
            raise RuntimeError(f"Expected 249 MathML surfaces, found {mathml_count}")
        if image_alt_count < 1:
            raise RuntimeError("No non-empty image alt text found")
        if direct_lab_links:
            raise RuntimeError(f"Direct non-spine lab links remain: {direct_lab_links}")

        unresolved: list[str] = []
        for base, href in hrefs:
            parsed = urlsplit(href)
            if parsed.scheme or href.startswith("//") or not parsed.fragment:
                continue
            target = resolve_member(base, href) if parsed.path else base
            if target not in identifiers or unquote(parsed.fragment) not in identifiers[target]:
                unresolved.append(f"{base}: {href}")
        if unresolved:
            raise RuntimeError(f"Unresolved internal fragments: {unresolved[:10]}")

        lab_rows: list[dict[str, object]] = []
        for source in LAB_FILES:
            member = str(opf_dir / "lab" / source.name)
            payload = package.read(member)
            if payload != source.read_bytes():
                raise RuntimeError(f"Packaged lab bytes differ: {source.name}")
            lab_rows.append(
                {
                    "member": member,
                    "bytes": len(payload),
                    "sha256": sha256_bytes(payload),
                }
            )

    build = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    if build.get("result") != "pass" or build["artifact"]["sha256"] != sha256(EPUB):
        raise RuntimeError("EPUB build receipt does not bind the final EPUB")
    report = {
        "schema": "o015-original-01-epub-conformance-v1",
        "date": "2026-08-26",
        "result": "pass",
        "artifact": record(EPUB),
        "build_receipt": record(BUILD_RECEIPT),
        "verifier": record(Path(__file__).resolve()),
        "epubcheck": {
            "version": checker["checkerVersion"],
            "exit_code": completed.returncode,
            "fail_on_warnings": True,
            "counts": counts,
            "official_release": OFFICIAL_RELEASE,
            "official_distribution": {
                "url": OFFICIAL_ZIP,
                "bytes": OFFICIAL_ZIP_BYTES,
                "sha256": OFFICIAL_ZIP_SHA256,
            },
        },
        "package": {
            "member_count": len(infos),
            "mimetype_first_and_uncompressed": True,
            "rootfile": rootfile,
            "xhtml_count": len(xhtml_members),
            "all_xhtml_language": "id-ID",
            "mathml_surfaces": mathml_count,
            "images_with_alt": image_alt_count,
            "duplicate_ids": 0,
            "unresolved_internal_fragments": 0,
            "direct_non_spine_lab_links": 0,
            "packaged_lab_resources": lab_rows,
        },
        "accessibility_metadata": {
            "access_modes": meta_values.get("schema:accessMode", []),
            "access_mode_sufficient": meta_values.get(
                "schema:accessModeSufficient", []
            ),
            "features": sorted(features),
            "hazards": meta_values.get("schema:accessibilityHazard", []),
            "summary": summaries[0],
        },
        "rights_metadata": rights[0],
        "limitations": [
            "EPUBCheck proves EPUB conformance, not behavioral equivalence across every reading system.",
            "The PDF companion is untagged; EPUB and HTML are the preferred reflow surfaces.",
        ],
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "result": "pass",
                "epub_sha256": sha256(EPUB),
                "report_sha256": sha256(REPORT),
                "mathml_surfaces": mathml_count,
                "epubcheck_counts": counts,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
