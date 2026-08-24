#!/usr/bin/env python3
"""Validate the final Habring PDF readers after deterministic assembly."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "qa" / "HABRING_PDF_NAVIGATION_QA.json"
PDFS = [
    ROOT / "output" / "pdf" / "D90-HAB-01-02-prasyarat-dan-konveksitas-id.pdf",
    ROOT / "output" / "pdf" / "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def flatten_outline(items: list[Any]) -> list[Any]:
    result: list[Any] = []
    for item in items:
        if isinstance(item, list):
            result.extend(flatten_outline(item))
        else:
            result.append(item)
    return result


def inspect(path: Path) -> dict[str, Any]:
    reader = PdfReader(str(path))
    named = reader.named_destinations
    subtype_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    unresolved: list[dict[str, Any]] = []
    invalid_rectangles: list[dict[str, Any]] = []
    page_sizes: set[tuple[float, float]] = set()
    searchable_pages = 0

    for page_index, page in enumerate(reader.pages):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        page_sizes.add((round(width, 3), round(height, 3)))
        if (page.extract_text() or "").strip():
            searchable_pages += 1

        for raw_annotation in page.get("/Annots") or []:
            annotation = raw_annotation.get_object()
            subtype = str(annotation.get("/Subtype", "missing"))
            subtype_counts[subtype] += 1
            rectangle = annotation.get("/Rect")
            if rectangle is not None:
                coords = [float(value) for value in rectangle]
                if (
                    len(coords) != 4
                    or coords[0] < -0.1
                    or coords[1] < -0.1
                    or coords[2] > width + 0.1
                    or coords[3] > height + 0.1
                    or coords[0] > coords[2]
                    or coords[1] > coords[3]
                ):
                    invalid_rectangles.append(
                        {"page": page_index + 1, "rectangle": coords}
                    )

            action = annotation.get("/A")
            destination = annotation.get("/Dest")
            if action is not None:
                action = action.get_object()
                action_kind = str(action.get("/S", "missing"))
                action_counts[action_kind] += 1
                if action_kind == "/GoTo":
                    destination = action.get("/D")
            elif destination is not None:
                action_counts["/Dest"] += 1

            if isinstance(destination, str) and destination not in named:
                unresolved.append(
                    {"page": page_index + 1, "destination": destination}
                )

    outline = flatten_outline(reader.outline)
    outline_failures: list[dict[str, Any]] = []
    for item in outline:
        try:
            target = reader.get_destination_page_number(item)
        except Exception as error:  # pragma: no cover - diagnostic path
            outline_failures.append({"title": str(item), "error": str(error)})
            continue
        if target < 0 or target >= len(reader.pages):
            outline_failures.append({"title": str(item), "page_index": target})

    failures: list[str] = []
    if reader.is_encrypted:
        failures.append("encrypted")
    if str(reader.trailer["/Root"].get("/Lang")) != "id-ID":
        failures.append("catalog language is not id-ID")
    if searchable_pages != len(reader.pages):
        failures.append("one or more pages lacks searchable text")
    if page_sizes != {(595.276, 841.89)}:
        failures.append(f"unexpected page sizes: {sorted(page_sizes)}")
    if unresolved:
        failures.append("unresolved named link destinations")
    if invalid_rectangles:
        failures.append("annotation rectangle outside its page")
    if outline_failures:
        failures.append("invalid outline destination")

    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "pages": len(reader.pages),
        "catalog_lang": str(reader.trailer["/Root"].get("/Lang")),
        "encrypted": reader.is_encrypted,
        "page_sizes_points": [list(size) for size in sorted(page_sizes)],
        "searchable_pages": searchable_pages,
        "named_destination_count": len(named),
        "annotation_subtypes": dict(sorted(subtype_counts.items())),
        "annotation_actions": dict(sorted(action_counts.items())),
        "outline_entry_count": len(outline),
        "unresolved_destinations": unresolved,
        "invalid_annotation_rectangles": invalid_rectangles,
        "outline_failures": outline_failures,
        "failures": failures,
        "result": "pass" if not failures else "fail",
    }


def main() -> None:
    artifacts = [inspect(path) for path in PDFS]
    report = {
        "schema": "o015-habring-pdf-navigation-qa-v1",
        "artifacts": artifacts,
        "result": "pass" if all(item["result"] == "pass" for item in artifacts) else "fail",
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["result"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
