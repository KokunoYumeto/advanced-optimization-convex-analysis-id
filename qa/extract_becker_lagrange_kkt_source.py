#!/usr/bin/env python3
"""Freeze the exact non-O018 Becker source slices for the first supplement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "98ed6930084c435ba0f675f7646ced1f2fd8729e"
SOURCE = (
    ROOT
    / "authority"
    / "becker"
    / "extract"
    / f"convex-optimization-class-{COMMIT}"
    / "TypedNotes"
    / "APPM5720Notes.tex"
)
OUTPUT = ROOT / "source" / "en" / "becker-01-lagrange-slater-kkt-source.tex"
REPORT = ROOT / "qa" / "BECKER_01_SOURCE_BOUNDARY.json"
EXPECTED_SOURCE_SHA256 = (
    "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8"
)

# The broader audit candidates included adjacent LP-duality exposition.  O018
# owns that material, so the first O015 unit uses the exact disjoint subranges.
RANGES = [
    ("lagrangian-weak-duality", 1263, 1321),
    ("slater-statement", 1398, 1405),
    ("slater-geometry-and-saddle", 1414, 1499),
    ("kkt-core", 1652, 1726),
    ("equality-qp-kkt-system", 1731, 1743),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    raw = SOURCE.read_bytes()
    if sha256_bytes(raw) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Frozen APPM5720Notes.tex identity mismatch")
    text = raw.decode("utf-8")
    if "\r" in text:
        raise RuntimeError("Frozen source is no longer LF-normalized")
    lines = text.splitlines()
    # The file ends with three whitespace-only physical lines after
    # ``\\end{document}``; retain the exact 2,992-line physical topology.
    if len(lines) != 2992:
        raise RuntimeError(f"Unexpected source line count: {len(lines)}")

    parts: list[str] = []
    records: list[dict[str, object]] = []
    for stable_id, first, last in RANGES:
        payload = "\n".join(lines[first - 1 : last]) + "\n"
        encoded = payload.encode("utf-8")
        parts.extend(
            [
                f"% BEGIN {stable_id} | frozen lines {first}-{last}",
                payload.rstrip("\n"),
                f"% END {stable_id}",
                "",
            ]
        )
        records.append(
            {
                "id": stable_id,
                "first_line": first,
                "last_line": last,
                "line_count": last - first + 1,
                "bytes": len(encoded),
                "sha256": sha256_bytes(encoded),
            }
        )

    output_text = "\n".join(parts).rstrip() + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output_text, encoding="utf-8", newline="\n")
    report = {
        "schema": "o015-becker-01-source-boundary-v1",
        "result": "pass",
        "authority": {
            "repository": "https://github.com/stephenbeckr/convex-optimization-class",
            "commit": COMMIT,
            "source_path": "TypedNotes/APPM5720Notes.tex",
            "source_bytes": len(raw),
            "source_lines": len(lines),
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "license": "MIT",
            "typed_notes_credit": "Mitchell Krock",
        },
        "selected_ranges": records,
        "combined_witness": {
            "path": OUTPUT.relative_to(ROOT).as_posix(),
            "bytes": OUTPUT.stat().st_size,
            "sha256": sha256_bytes(OUTPUT.read_bytes()),
        },
        "explicit_exclusions": [
            {
                "lines": "1322-1397",
                "reason": "LP-duality examples and mnemonic material belong to O018; one malformed adjacent example is also excluded rather than silently repaired into O015.",
            },
            {
                "lines": "1406-1413",
                "reason": "The LP-specific strong-duality aside belongs to O018.",
            },
            {
                "lines": "1727-1730",
                "reason": "The LP complementary-slackness example belongs to O018; the general KKT statement remains included.",
            },
        ],
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
