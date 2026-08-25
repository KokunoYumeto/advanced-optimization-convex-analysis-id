#!/usr/bin/env python3
"""Verify the exact frozen Becker Douglas--Rachford source boundary."""

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
WITNESS = ROOT / "source" / "en" / "becker-02-douglas-rachford-source.tex"
REPORT = ROOT / "qa" / "BECKER_02_SOURCE_BOUNDARY.json"

EXPECTED_SOURCE_BYTES = 130_911
EXPECTED_SOURCE_LINES = 2_992
EXPECTED_SOURCE_SHA256 = (
    "dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8"
)
FIRST_LINE = 2750
LAST_LINE = 2797
EXPECTED_SLICE_BYTES = 1_285
EXPECTED_SLICE_SHA256 = (
    "386f1f0f94f6433eebdd6d07e10f3ffe28ffa8650e392cb0158a389e01452cf2"
)
BEGIN_MARKER = b"% BEGIN douglas-rachford | frozen lines 2750-2797\n"
END_MARKER = b"% END douglas-rachford\n"
EXPECTED_WITNESS_BYTES = 1_358
EXPECTED_WITNESS_SHA256 = (
    "fdc368741a0a88eb9d21c69d655ac6ce1b44571c2d49c6a3302e3efc4673594b"
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
            "Douglas--Rachford slice identity mismatch: "
            f"bytes={len(payload)}, sha256={payload_hash}"
        )
    if payload.count(b"\n") != LAST_LINE - FIRST_LINE + 1:
        raise RuntimeError("Douglas--Rachford slice physical-line mismatch")

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
            "Existing Becker-02 witness does not match the exact frozen slice: "
            f"bytes={len(observed_witness)}, sha256={observed_witness_hash}"
        )
    interior = observed_witness[len(BEGIN_MARKER) : -len(END_MARKER)]
    if interior != payload:
        raise RuntimeError("Witness interior is not byte-identical to the donor slice")

    report = {
        "schema": "o015-becker-02-source-boundary-v1",
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
                "id": "douglas-rachford",
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
                "lines": "before 2750",
                "reason": "Adjacent ADMM and other earlier course material are outside this bounded Douglas--Rachford unit.",
            },
            {
                "lines": "2798 onward",
                "reason": "The following primal-dual-methods subsection is a separate unit and is not imported.",
            },
        ],
        "lp_material_imported": False,
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
