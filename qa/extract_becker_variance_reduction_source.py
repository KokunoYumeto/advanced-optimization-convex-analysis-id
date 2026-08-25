#!/usr/bin/env python3
"""Verify the exact frozen Becker variance-reduction source boundary."""

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
WITNESS = ROOT / "source" / "en" / "becker-03-variance-reduction-source.tex"
REPORT = ROOT / "qa" / "BECKER_03_SOURCE_BOUNDARY.json"

EXPECTED_SOURCE_BYTES = 130_911
EXPECTED_SOURCE_LINES = 2_992
EXPECTED_SOURCE_SHA256 = (
    "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8"
)
FIRST_LINE = 2971
LAST_LINE = 2988
EXPECTED_SLICE_BYTES = 900
EXPECTED_SLICE_SHA256 = (
    "b81634bf07565fcf8d2774bea7b96e565e5fdd76cf5e782c5e4eb6fb3268c5ed"
)
BEGIN_MARKER = b"% BEGIN variance-reduction | frozen lines 2971-2988\n"
END_MARKER = b"% END variance-reduction\n"
EXPECTED_WITNESS_BYTES = 977
EXPECTED_WITNESS_SHA256 = (
    "66f243b97cd379b73d217c6a3e424db688f8ace246852cb24f78108c53186607"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Frozen source is missing: {SOURCE}")
    raw = SOURCE.read_bytes()
    source_hash = sha256_bytes(raw)
    if len(raw) != EXPECTED_SOURCE_BYTES or source_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            "Frozen APPM5720Notes.tex identity mismatch: "
            f"bytes={len(raw)}, sha256={source_hash}"
        )
    if b"\r" in raw:
        raise RuntimeError("Frozen source is no longer LF-normalized")
    raw.decode("utf-8", errors="strict")
    lines = raw.splitlines(keepends=True)
    if len(lines) != EXPECTED_SOURCE_LINES:
        raise RuntimeError(f"Unexpected source line count: {len(lines)}")
    if any(not line.endswith(b"\n") for line in lines):
        raise RuntimeError("Every frozen physical line must end in LF")

    payload = b"".join(lines[FIRST_LINE - 1 : LAST_LINE])
    payload_hash = sha256_bytes(payload)
    if len(payload) != EXPECTED_SLICE_BYTES or payload_hash != EXPECTED_SLICE_SHA256:
        raise RuntimeError(
            "Variance-reduction slice identity mismatch: "
            f"bytes={len(payload)}, sha256={payload_hash}"
        )
    if payload.count(b"\n") != LAST_LINE - FIRST_LINE + 1:
        raise RuntimeError("Variance-reduction slice physical-line mismatch")

    expected_witness = BEGIN_MARKER + payload + END_MARKER
    expected_witness_hash = sha256_bytes(expected_witness)
    if (
        len(expected_witness) != EXPECTED_WITNESS_BYTES
        or expected_witness_hash != EXPECTED_WITNESS_SHA256
    ):
        raise RuntimeError("Internal expected-witness identity mismatch")

    witness_state = "verified_existing"
    if not WITNESS.exists():
        WITNESS.parent.mkdir(parents=True, exist_ok=True)
        WITNESS.write_bytes(expected_witness)
        witness_state = "created_from_verified_slice"
    observed_witness = WITNESS.read_bytes()
    observed_witness_hash = sha256_bytes(observed_witness)
    if observed_witness != expected_witness:
        raise RuntimeError(
            "Existing Becker-03 witness does not match the exact frozen slice: "
            f"bytes={len(observed_witness)}, sha256={observed_witness_hash}"
        )
    interior = observed_witness[len(BEGIN_MARKER) : -len(END_MARKER)]
    if interior != payload:
        raise RuntimeError("Witness interior is not byte-identical to the donor slice")

    report = {
        "schema": "o015-becker-03-source-boundary-v1",
        "result": "pass",
        "authority": {
            "repository": "https://github.com/stephenbeckr/convex-optimization-class",
            "commit": COMMIT,
            "source_path": SOURCE.relative_to(ROOT).as_posix(),
            "source_local_path": "TypedNotes/APPM5720Notes.tex",
            "source_bytes": len(raw),
            "source_lines": len(lines),
            "source_sha256": source_hash,
            "license": "MIT",
            "typed_notes_credit": "Mitchell Krock",
        },
        "selected_ranges": [
            {
                "id": "variance-reduction",
                "first_line": FIRST_LINE,
                "last_line": LAST_LINE,
                "line_count": LAST_LINE - FIRST_LINE + 1,
                "bytes": len(payload),
                "sha256": payload_hash,
                "line_endings": "LF",
                "final_newline": True,
            }
        ],
        "combined_witness": {
            "path": WITNESS.relative_to(ROOT).as_posix(),
            "bytes": len(observed_witness),
            "sha256": observed_witness_hash,
            "state": witness_state,
            "exact_expected_byte_match": True,
            "interior_exact_source_slice_match": True,
            "begin_marker": BEGIN_MARKER.decode("ascii").rstrip("\n"),
            "end_marker": END_MARKER.decode("ascii").rstrip("\n"),
        },
        "explicit_exclusions": [
            {
                "lines": "before 2971",
                "reason": "Earlier stochastic-gradient material is outside this bounded variance-reduction unit.",
            },
            {
                "lines": "2989 onward",
                "reason": "Only the document terminator and trailing blank lines follow; none is imported.",
            },
        ],
        "outside_range_material_imported": False,
        "document_terminator_imported": False,
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
