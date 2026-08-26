#!/usr/bin/env python3
"""Independently validate Original-02 EPUB conformance.

The validator is deliberately fail-closed.  It checks the current build
receipt, the ZIP/OPF closure, native MathML and OPF-property congruence,
language/accessibility metadata, internal references, and byte-identical lab
resources before accepting EPUBCheck 5.3.0 with warnings promoted to failure.
Only the sanitized receipt and a transient EPUBCheck JSON file are written,
both inside ``qa``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
EPUB = ROOT / "output" / "epub" / (
    "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-"
    "resolven-pemisahan-id.epub"
)
BUILD_RECEIPT = ROOT / "qa" / "ORIGINAL_02_EPUB_BUILD.json"
REPORT = ROOT / "qa" / "ORIGINAL_02_EPUB_CONFORMANCE.json"
CHECK_JSON = ROOT / "qa" / ".ORIGINAL_02_EPUBCHECK_5_3_0.tmp.json"
DEFAULT_JAR = ROOT / "tmp" / "tools" / "epubcheck-5.3.0" / "epubcheck.jar"

EXPECTED_SCHEMA = "o015-original-02-epub-build-v1"
EXPECTED_MATHML = 295
EXPECTED_RIGHTS = (
    "Mixed rights: new Original-02 content CC BY-SA 4.0; "
    "shinybook.cls and macros-id.tex CC BY 4.0"
)
LAB_MEDIA_TYPES = {
    "monotone-splitting-lab.py": "text/x-python",
    "results.json": "application/json",
    "results.csv": "text/csv",
    "residual.svg": "image/svg+xml",
}
LAB_FILES = tuple(
    ROOT / "labs" / "original-02" / name for name in LAB_MEDIA_TYPES
)

OFFICIAL_RELEASE = "https://github.com/w3c/epubcheck/releases/tag/v5.3.0"
OFFICIAL_ZIP = (
    "https://github.com/w3c/epubcheck/releases/download/v5.3.0/"
    "epubcheck-5.3.0.zip"
)
OFFICIAL_ZIP_BYTES = 33_071_108
OFFICIAL_ZIP_SHA256 = (
    "6c07e68584b2e2ce2f89fe06e1246dfead3eb36b46b340e7d93524f29dcff6c5"
)

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
MATHML_TAG = "{http://www.w3.org/1998/Math/MathML}math"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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


def receipt_locator(path: Path) -> str:
    """Describe a tool without recording an absolute machine-local path."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return f"<external-tool>/{resolved.name}"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child(parent: ET.Element, name: str) -> ET.Element:
    matches = [node for node in parent if local_name(node.tag) == name]
    require(len(matches) == 1, f"Expected one {name} child, found {len(matches)}")
    return matches[0]


def normalized_member(base_member: str, href: str) -> str:
    """Resolve a local EPUB href and reject absolute or escaping paths."""

    parsed = urlsplit(href)
    require(not parsed.scheme and not parsed.netloc, f"Expected local href: {href}")
    path = unquote(parsed.path)
    require(path and not path.startswith("/"), f"Invalid package href: {href}")
    require("\\" not in path, f"Backslash in package href: {href}")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(base_member), path))
    require(
        resolved not in {"", ".", ".."} and not resolved.startswith("../"),
        f"Package href escapes its root: {href}",
    )
    return resolved


def resolve_reference(base_member: str, href: str) -> str:
    parsed = urlsplit(href)
    if not parsed.path:
        return base_member
    return normalized_member(base_member, href)


def inspect_package() -> dict[str, object]:
    require(EPUB.is_file(), f"EPUB not found: {EPUB}")

    with zipfile.ZipFile(EPUB) as package:
        infos = package.infolist()
        names = [info.filename for info in infos]
        require(infos, "EPUB has no members")
        require(len(names) == len(set(names)), "EPUB contains duplicate member names")
        require(names[0] == "mimetype", "mimetype is not the first EPUB member")
        require(
            infos[0].compress_type == zipfile.ZIP_STORED,
            "mimetype member is compressed",
        )
        require(
            package.read("mimetype") == b"application/epub+zip",
            "Unexpected mimetype payload",
        )

        container_member = "META-INF/container.xml"
        require(container_member in names, "META-INF/container.xml is absent")
        container = ET.fromstring(package.read(container_member))
        rootfiles = [
            node for node in container.iter() if local_name(node.tag) == "rootfile"
        ]
        require(len(rootfiles) == 1, f"Expected one rootfile, found {len(rootfiles)}")
        rootfile = rootfiles[0].attrib.get("full-path", "")
        require(rootfile in names, f"Declared OPF rootfile is absent: {rootfile}")
        require(
            rootfiles[0].attrib.get("media-type") == "application/oebps-package+xml",
            "Unexpected rootfile media type",
        )

        opf = ET.fromstring(package.read(rootfile))
        require(opf.attrib.get(XML_LANG) == "id-ID", "OPF xml:lang is not id-ID")
        metadata = child(opf, "metadata")
        manifest = child(opf, "manifest")
        spine = child(opf, "spine")

        manifest_nodes = [node for node in manifest if local_name(node.tag) == "item"]
        item_ids = [node.attrib.get("id", "") for node in manifest_nodes]
        require(all(item_ids), "Manifest item without an id")
        require(len(item_ids) == len(set(item_ids)), "Duplicate manifest item id")

        items: dict[str, dict[str, object]] = {}
        members_to_ids: dict[str, str] = {}
        for node in manifest_nodes:
            item_id = node.attrib["id"]
            href = node.attrib.get("href", "")
            require(href and not urlsplit(href).fragment, f"Invalid manifest href: {href}")
            member = normalized_member(rootfile, href)
            require(member not in members_to_ids, f"Duplicate manifest target: {member}")
            properties = set(node.attrib.get("properties", "").split())
            items[item_id] = {
                "href": href,
                "member": member,
                "media_type": node.attrib.get("media-type", ""),
                "properties": properties,
            }
            members_to_ids[member] = item_id

        manifest_members = set(members_to_ids)
        package_members = {name for name in names if not name.endswith("/")}
        missing_members = sorted(manifest_members - package_members)
        require(not missing_members, f"Manifest members absent from ZIP: {missing_members}")

        infrastructure = {
            "mimetype",
            rootfile,
            container_member,
        } | {name for name in package_members if name.startswith("META-INF/")}
        unmanifested = sorted(package_members - manifest_members - infrastructure)
        require(not unmanifested, f"Unmanifested package resources: {unmanifested}")

        dc_languages = [
            "".join(node.itertext()).strip()
            for node in metadata
            if local_name(node.tag) == "language"
        ]
        require(dc_languages == ["id-ID"], f"Unexpected dc:language: {dc_languages}")

        rights = [
            "".join(node.itertext()).strip()
            for node in metadata
            if local_name(node.tag) == "rights"
        ]
        require(rights == [EXPECTED_RIGHTS], f"Unexpected rights metadata: {rights}")

        meta_values: dict[str, list[str]] = {}
        for node in metadata:
            prop = node.attrib.get("property") if local_name(node.tag) == "meta" else None
            if prop:
                meta_values.setdefault(prop, []).append("".join(node.itertext()).strip())

        features = set(meta_values.get("schema:accessibilityFeature", []))
        required_features = {
            "MathML",
            "alternativeText",
            "readingOrder",
            "structuralNavigation",
            "tableOfContents",
        }
        require(
            required_features <= features,
            f"Missing accessibility features: {sorted(required_features - features)}",
        )
        require(
            meta_values.get("schema:accessMode") == ["textual"],
            "Accessibility mode is not exactly textual",
        )
        require(
            meta_values.get("schema:accessModeSufficient") == ["textual"],
            "Accessibility mode sufficient is not exactly textual",
        )
        require(
            meta_values.get("schema:accessibilityHazard") == ["none"],
            "Accessibility hazard metadata is not exactly none",
        )
        summaries = meta_values.get("schema:accessibilitySummary", [])
        require(len(summaries) == 1, "Expected exactly one accessibility summary")
        require(
            all(token in summaries[0] for token in ("MathML", "CSV/JSON")),
            "Accessibility summary omits MathML or CSV/JSON redundancy",
        )

        xhtml_items = {
            str(data["member"]): data
            for data in items.values()
            if data["media_type"] == "application/xhtml+xml"
        }
        require(xhtml_items, "Manifest contains no XHTML items")

        nav_items = [
            (member, data)
            for member, data in xhtml_items.items()
            if "nav" in data["properties"]
        ]
        require(len(nav_items) == 1, f"Expected one nav item, found {len(nav_items)}")
        nav_member, nav_item = nav_items[0]
        expected_nav = posixpath.join(posixpath.dirname(rootfile), "nav.xhtml")
        require(nav_member == expected_nav, f"Navigation member is not nav.xhtml: {nav_member}")
        require(
            nav_item["properties"] == {"nav", "mathml"},
            f"nav.xhtml properties must be exactly 'nav mathml': {nav_item['properties']}",
        )

        spine_idrefs = [
            node.attrib.get("idref", "")
            for node in spine
            if local_name(node.tag) == "itemref"
        ]
        require(all(spine_idrefs), "Spine itemref without idref")
        require(len(spine_idrefs) == len(set(spine_idrefs)), "Duplicate spine idref")
        unknown_spine = sorted(set(spine_idrefs) - set(items))
        require(not unknown_spine, f"Unknown spine idrefs: {unknown_spine}")
        non_xhtml_spine = [
            item_id
            for item_id in spine_idrefs
            if items[item_id]["media_type"] != "application/xhtml+xml"
        ]
        require(not non_xhtml_spine, f"Non-XHTML spine items: {non_xhtml_spine}")
        require("nav" in set(spine_idrefs), "nav.xhtml is absent from the reading spine")

        identifiers: dict[str, set[str]] = {}
        references: list[tuple[str, str, str]] = []
        math_by_member: dict[str, int] = {}
        languages: set[tuple[str | None, str | None]] = set()
        image_alt_count = 0
        direct_lab_links: list[str] = []

        for member in sorted(xhtml_items):
            document = ET.fromstring(package.read(member))
            languages.add((document.attrib.get("lang"), document.attrib.get(XML_LANG)))
            ids = [node.attrib["id"] for node in document.iter() if "id" in node.attrib]
            require(len(ids) == len(set(ids)), f"Duplicate ID in {member}")
            identifiers[member] = set(ids)

            member_math = sum(1 for node in document.iter() if node.tag == MATHML_TAG)
            math_by_member[member] = member_math
            claims_mathml = "mathml" in xhtml_items[member]["properties"]
            require(
                claims_mathml == (member_math > 0),
                f"OPF MathML property/content mismatch for {member}: "
                f"property={claims_mathml}, surfaces={member_math}",
            )

            for node in document.iter():
                if local_name(node.tag) == "img" and node.attrib.get("alt", "").strip():
                    image_alt_count += 1
                for attribute in ("href", "src"):
                    value = node.attrib.get(attribute)
                    if value:
                        references.append((member, attribute, value))
                        parsed = urlsplit(value)
                        if attribute == "href" and not parsed.scheme and parsed.path:
                            target = resolve_reference(member, value)
                            lab_prefix = posixpath.join(posixpath.dirname(rootfile), "lab") + "/"
                            if target.startswith(lab_prefix):
                                direct_lab_links.append(f"{member}: {value}")

        require(languages == {("id-ID", "id-ID")}, f"Unexpected XHTML languages: {languages}")
        mathml_count = sum(math_by_member.values())
        require(
            mathml_count == EXPECTED_MATHML,
            f"Expected {EXPECTED_MATHML} MathML surfaces, found {mathml_count}",
        )
        require(math_by_member[nav_member] > 0, "nav.xhtml claims MathML but contains none")
        require(image_alt_count >= 1, "No non-empty XHTML image alt text found")
        require(not direct_lab_links, f"Direct non-spine lab links remain: {direct_lab_links}")

        manifest_mathml_members = sorted(
            member
            for member, data in xhtml_items.items()
            if "mathml" in data["properties"]
        )
        actual_mathml_members = sorted(
            member for member, count in math_by_member.items() if count > 0
        )
        require(
            manifest_mathml_members == actual_mathml_members,
            "Manifested MathML XHTML set differs from actual MathML XHTML set",
        )

        missing_targets: list[str] = []
        unresolved_fragments: list[str] = []
        for base, attribute, href in references:
            parsed = urlsplit(href)
            if parsed.scheme or href.startswith("//"):
                continue
            target = resolve_reference(base, href)
            if target not in package_members:
                missing_targets.append(f"{base} [{attribute}]: {href}")
                continue
            if parsed.fragment:
                fragment = unquote(parsed.fragment)
                if target not in identifiers or fragment not in identifiers[target]:
                    unresolved_fragments.append(f"{base} [{attribute}]: {href}")
        require(not missing_targets, f"Missing local reference targets: {missing_targets[:10]}")
        require(
            not unresolved_fragments,
            f"Unresolved internal fragments: {unresolved_fragments[:10]}",
        )

        opf_dir = posixpath.dirname(rootfile)
        expected_lab_members = {
            posixpath.join(opf_dir, "lab", source.name) for source in LAB_FILES
        }
        actual_lab_members = {
            member for member in manifest_members if member.startswith(opf_dir + "/lab/")
        }
        require(
            actual_lab_members == expected_lab_members,
            f"Unexpected packaged lab closure: {sorted(actual_lab_members)}",
        )

        lab_rows: list[dict[str, object]] = []
        for source in LAB_FILES:
            require(source.is_file(), f"Local lab resource is absent: {source}")
            member = posixpath.join(opf_dir, "lab", source.name)
            item = items[members_to_ids[member]]
            expected_media_type = LAB_MEDIA_TYPES[source.name]
            require(
                item["media_type"] == expected_media_type,
                f"Unexpected media type for {source.name}: {item['media_type']}",
            )
            payload = package.read(member)
            require(payload == source.read_bytes(), f"Packaged lab bytes differ: {source.name}")
            lab_rows.append(
                {
                    "source": source.relative_to(ROOT).as_posix(),
                    "member": member,
                    "media_type": expected_media_type,
                    "bytes": len(payload),
                    "sha256": sha256_bytes(payload),
                }
            )

        return {
            "member_count": len(infos),
            "manifest_item_count": len(items),
            "manifested_member_count": len(manifest_members),
            "mimetype_first_and_uncompressed": True,
            "rootfile": rootfile,
            "spine_item_count": len(spine_idrefs),
            "xhtml_count": len(xhtml_items),
            "all_xhtml_language": "id-ID",
            "mathml_surfaces": mathml_count,
            "mathml_manifest_members": manifest_mathml_members,
            "mathml_property_content_congruence": True,
            "nav_member": nav_member,
            "nav_properties": sorted(nav_item["properties"]),
            "nav_mathml_surfaces": math_by_member[nav_member],
            "images_with_alt": image_alt_count,
            "duplicate_ids": 0,
            "missing_local_targets": 0,
            "unresolved_internal_fragments": 0,
            "direct_non_spine_lab_links": 0,
            "unmanifested_package_resources": 0,
            "packaged_lab_resources": lab_rows,
            "accessibility": {
                "access_modes": meta_values.get("schema:accessMode", []),
                "access_mode_sufficient": meta_values.get(
                    "schema:accessModeSufficient", []
                ),
                "features": sorted(features),
                "hazards": meta_values.get("schema:accessibilityHazard", []),
                "summary": summaries[0],
            },
            "rights_metadata": rights[0],
        }


def verify_build_receipt(package_result: dict[str, object]) -> dict[str, object]:
    require(BUILD_RECEIPT.is_file(), f"Build receipt not found: {BUILD_RECEIPT}")
    build = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    require(build.get("schema") == EXPECTED_SCHEMA, "Unexpected O2 EPUB build schema")
    require(build.get("result") == "pass", "O2 EPUB build receipt is not a pass")

    artifact = build.get("artifact", {})
    expected_artifact = record(EPUB)
    for key in ("path", "bytes", "sha256"):
        require(
            artifact.get(key) == expected_artifact[key],
            f"Build receipt artifact {key} does not bind the current EPUB",
        )
    require(
        artifact.get("mathml_count") == EXPECTED_MATHML,
        "Build receipt MathML count is not 295",
    )
    require(
        artifact.get("manifest_resource_closure") is True,
        "Build receipt does not assert manifest resource closure",
    )
    require(
        artifact.get("packaged_lab_bytes_exact") is True,
        "Build receipt does not assert exact packaged lab bytes",
    )
    require(
        artifact.get("packaged_lab_resource_count") == len(LAB_FILES),
        "Build receipt lab resource count differs",
    )
    require(
        artifact.get("xhtml_member_count") == package_result["xhtml_count"],
        "Build receipt XHTML count differs from package",
    )
    require(
        artifact.get("manifest_item_count") == package_result["manifest_item_count"],
        "Build receipt manifest count differs from package",
    )
    require(
        artifact.get("zip_entry_count") == package_result["member_count"],
        "Build receipt ZIP entry count differs from package",
    )
    require(
        artifact.get("navigation_math_duplication_count")
        == package_result["nav_mathml_surfaces"],
        "Build receipt navigation MathML count differs from package",
    )

    runs = build.get("runs", [])
    require(len(runs) == 2, f"Expected two deterministic EPUB runs, found {len(runs)}")
    expected_lab_members = {
        source.name: row["member"]
        for source, row in zip(
            LAB_FILES,
            package_result["packaged_lab_resources"],
            strict=True,
        )
    }
    for index, run in enumerate(runs, start=1):
        require(
            run.get("mathml_manifest_item_count")
            == len(package_result["mathml_manifest_members"]),
            f"Build run {index} MathML manifest count differs from package",
        )
        require(
            run.get("packaged_lab_members") == expected_lab_members,
            f"Build run {index} packaged lab member map differs from package",
        )

    inputs = {
        row.get("path"): row
        for row in build.get("inputs", [])
        if isinstance(row, dict) and row.get("path")
    }
    for source in LAB_FILES:
        current = record(source)
        receipt_row = inputs.get(current["path"])
        require(receipt_row is not None, f"Lab absent from build inputs: {current['path']}")
        for key in ("bytes", "sha256"):
            require(
                receipt_row.get(key) == current[key],
                f"Build input binding differs for {current['path']} ({key})",
            )

    determinism = build.get("determinism", {})
    require(
        determinism.get("byte_identical") is True
        and determinism.get("canonical_copy_exact_match") is True,
        "Build receipt does not prove a byte-identical canonical EPUB",
    )
    return record(BUILD_RECEIPT)


def run_epubcheck(jar: Path) -> dict[str, object]:
    jar = jar.resolve()
    if not jar.is_file():
        raise FileNotFoundError(
            "Internal EPUB/package/build checks passed, but EPUBCheck 5.3.0 "
            f"jar was not found at: {jar}. Supply --epubcheck-jar with an "
            "existing local EPUBCheck 5.3.0 jar."
        )

    CHECK_JSON.unlink(missing_ok=True)
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
        require(CHECK_JSON.is_file(), "EPUBCheck did not emit its JSON assessment")
        assessment = json.loads(CHECK_JSON.read_text(encoding="utf-8"))
    finally:
        CHECK_JSON.unlink(missing_ok=True)

    checker = assessment.get("checker", {})
    counts = {
        "fatal": int(checker.get("nFatal", -1)),
        "error": int(checker.get("nError", -1)),
        "warning": int(checker.get("nWarning", -1)),
        "usage": int(checker.get("nUsage", -1)),
    }
    require(
        completed.returncode == 0 and not any(counts.values()),
        f"EPUBCheck failed: exit={completed.returncode}, counts={counts}",
    )
    require(
        checker.get("checkerVersion") == "5.3.0",
        f"Unexpected EPUBCheck version: {checker.get('checkerVersion')}",
    )
    return {
        "version": checker["checkerVersion"],
        "jar_path": receipt_locator(jar),
        "jar_bytes": jar.stat().st_size,
        "jar_sha256": sha256(jar),
        "exit_code": completed.returncode,
        "fail_on_warnings": True,
        "counts": counts,
        "official_release": OFFICIAL_RELEASE,
        "official_distribution": {
            "url": OFFICIAL_ZIP,
            "bytes": OFFICIAL_ZIP_BYTES,
            "sha256": OFFICIAL_ZIP_SHA256,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epubcheck-jar", type=Path, default=DEFAULT_JAR)
    args = parser.parse_args()

    REPORT.unlink(missing_ok=True)
    CHECK_JSON.unlink(missing_ok=True)
    package_result = inspect_package()
    build_record = verify_build_receipt(package_result)
    epubcheck = run_epubcheck(args.epubcheck_jar)

    report = {
        "schema": "o015-original-02-epub-conformance-v1",
        "date": "2026-08-26",
        "result": "pass",
        "artifact": record(EPUB),
        "build_receipt": build_record,
        "verifier": record(Path(__file__).resolve()),
        "epubcheck": epubcheck,
        "package": package_result,
        "limitations": [
            "EPUBCheck proves EPUB conformance, not identical behavior in every reading system.",
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
                "mathml_surfaces": package_result["mathml_surfaces"],
                "mathml_manifest_members": package_result[
                    "mathml_manifest_members"
                ],
                "epubcheck_counts": epubcheck["counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
