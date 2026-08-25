#!/usr/bin/env python3
"""Freeze the admitted Habring-spine release inputs without network or Git.

The script writes only the adjacent final config and input-lock files. It
fails closed if a key artifact differs from the admitted 2026-08-25 boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEMPLATE_PATH = HERE / "release-config-habring-spine.template.json"
CONFIG_PATH = HERE / "release-config-habring-spine.json"
LOCK_PATH = HERE / "release-input-lock-habring-spine.json"

CONTROL_PATHS = [
    "00_control/CURRENT_GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/CURRENT_CURSOR.md",
    "00_control/SOURCE_AUTHORITY.json",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/DECISION_LOG.md",
    "00_control/ADVERSE_LEDGER.jsonl",
    "00_control/BUILD_AND_QA.md",
    "00_control/PUBLICATION_RECEIPTS.md",
]

MATERIAL_PATHS = [
    "authority/habring/2607.11664v1-source.tar",
    "authority/habring/CC-BY-4.0-legalcode.txt",
    "backend/backend_schema.json",
    "backend/records.jsonl",
    "backend/records.csv",
    "output/pdf/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf",
    "output/html/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html",
    "output/epub/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub",
    "source/id-ID/shinybook.cls",
    "source/id-ID/macros-id.tex",
    "source/id-ID/D90-HAB-01-02-prasyarat-dan-konveksitas-id.tex",
    "source/id-ID/D90-HAB-03-subgradien-id.tex",
    "source/id-ID/D90-HAB-04-metode-subgradien-terproyeksi-id.tex",
    "source/id-ID/D90-HAB-05-metode-gradien-proksimal-id.tex",
    "source/id-ID/D90-HAB-06-akselerasi-id.tex",
    "source/id-ID/D90-HAB-07-dualitas-id.tex",
    "source/id-ID/D90-HAB-08-penurunan-gradien-stokastik-id.tex",
    "source/id-ID/D90-HAB-09-transportasi-optimal-id.tex",
    "source/id-ID/habring-01-prasyarat-id.tex",
    "source/id-ID/habring-02-konveksitas-id.tex",
    "source/id-ID/habring-03-subgradien-id.tex",
    "source/id-ID/habring-04-metode-subgradien-terproyeksi-id.tex",
    "source/id-ID/habring-05-metode-gradien-proksimal-id.tex",
    "source/id-ID/habring-06-akselerasi-id.tex",
    "source/id-ID/habring-07-dualitas-id.tex",
    "source/id-ID/habring-08-penurunan-gradien-stokastik-id.tex",
    "source/id-ID/habring-09-transportasi-optimal-id.tex",
    "source/id-ID/figures/balls.png",
    "source/id-ID/figures/convex_fct.png",
    "source/id-ID/figures/discontinuous_function.png",
    "source/id-ID/figures/gradient.png",
    "source/id-ID/figures/lsc_function.png",
    "source/id-ID/figures/sets.png",
    "source/id-ID/figures/subgradient.png",
    "qa/audit_habring_ch01_ch02.py",
    "qa/build_habring_ch01_ch02.py",
    "qa/build_habring_full_reader.py",
    "qa/build_habring_full_html.py",
    "qa/build_habring_full_epub.py",
    "qa/extend_backend_habring_ch01_ch02.py",
    "qa/validate_backend_habring_ch01_ch02.py",
    "qa/validate_habring_ch01_ch02_math.py",
    "qa/validate_habring_pdf_navigation.py",
    "qa/HABRING_CH01_CH02_PROPOSED_LEDGER.jsonl",
    "qa/HABRING_CH02_PROPOSED_LEDGER.jsonl",
    "qa/HABRING_CH01_CH02_STRUCTURE_REPORT.json",
    "qa/HABRING_CH01_CH02_BUILD.json",
    "qa/HABRING_CH01_CH02_SOLVER_RESULTS.json",
    "qa/HABRING_FULL_READER_BUILD.json",
    "qa/HABRING_FULL_HTML_BUILD.json",
    "qa/HABRING_FULL_HTML_BROWSER_QA.json",
    "qa/HABRING_FULL_EPUB_BUILD.json",
    "qa/HABRING_PDF_NAVIGATION_QA.json",
    "qa/HABRING_PDF_VISUAL_QA.json",
    "qa/HABRING_CH01_CH02_BACKEND_VALIDATION.json",
]

QA_REPORTS = {
    "qa/HABRING_CH01_CH02_STRUCTURE_REPORT.json": "o015-habring-ch01-ch02-structure-audit-v1",
    "qa/HABRING_CH01_CH02_BUILD.json": "o015-habring-ch01-ch02-build-v1",
    "qa/HABRING_CH01_CH02_SOLVER_RESULTS.json": "o015-habring-ch01-ch02-open-math-validation-v1",
    "qa/HABRING_FULL_READER_BUILD.json": "o015-habring-full-reader-build-v1",
    "qa/HABRING_FULL_HTML_BUILD.json": "o015-habring-full-html-build-v1",
    "qa/HABRING_FULL_HTML_BROWSER_QA.json": "o015-habring-full-html-browser-qa-v1",
    "qa/HABRING_FULL_EPUB_BUILD.json": "o015-habring-full-epub-build-v1",
    "qa/HABRING_PDF_NAVIGATION_QA.json": "o015-habring-pdf-navigation-qa-v1",
    "qa/HABRING_PDF_VISUAL_QA.json": "o015-habring-pdf-visual-qa-v1",
    "qa/HABRING_CH01_CH02_BACKEND_VALIDATION.json": "o015-habring-ch01-ch02-backend-validation-v1",
}

KEY_IDENTITIES = {
    "authority/habring/2607.11664v1-source.tar": (230116, "d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748"),
    "source/id-ID/habring-01-prasyarat-id.tex": (31009, "6ed957c8bf654608e8d572b2f0368478a4dc185ba51c150ea9dee36bb62868e7"),
    "source/id-ID/habring-02-konveksitas-id.tex": (42828, "99a992f36756cb64f82d21cfcaf68fdaee8b8dd61ef2b007322d9d2623989f22"),
    "source/id-ID/D90-HAB-01-02-prasyarat-dan-konveksitas-id.tex": (5357, "301d45dc305ee86f439ed1056a62b47199f3439d88ba66436f127a5cee0e35b2"),
    "output/pdf/D90-HAB-01-02-prasyarat-dan-konveksitas-id.pdf": (720624, "5fc51737b0ec2d2342e93c0a53a997cd1f81a3df2d15415ef5fdd9c2c4a9dbdf"),
    "output/pdf/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf": (3779312, "da2b421b97efce4e3d7b8cf6be9938d17b7768b9c6bcb4846b09b9c692b34c41"),
    "output/html/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html": (1669938, "717ee81912a8b903acc87e5c59d830aa1d8c78abdda6e0c869d66b9a7bcde3a4"),
    "output/epub/D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub": (231700, "c630e25db3cbbfa6f6afa7213e526c47586b6e7b44f709095ea5a3881756fd41"),
    "backend/records.jsonl": (2408339, "21f19a4c56276b0abb677c58d9deb23d512e033b7a0f26c241ed9feb72891667"),
    "backend/records.csv": (2875457, "f3561b09cf15ae2bdd5fc84ee7d464abc720be04d92715200002518e63f4ee2f"),
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def validate_live_boundary() -> None:
    missing = [relative for relative in MATERIAL_PATHS + CONTROL_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError("missing Habring release inputs:\n" + "\n".join(missing))
    for relative, (size, sha256) in KEY_IDENTITIES.items():
        observed = identity(ROOT / relative)
        if observed != {"bytes": size, "sha256": sha256}:
            raise RuntimeError(f"admitted key identity drift: {relative}: {observed}")
    for relative, schema in QA_REPORTS.items():
        report = read_json(ROOT / relative)
        if report.get("schema") != schema or report.get("result") != "pass":
            raise RuntimeError(f"QA report has not closed with the expected schema/pass: {relative}")
        if report.get("failures") not in (None, []):
            raise RuntimeError(f"QA report contains failures: {relative}")
    backend = read_json(ROOT / "qa/HABRING_CH01_CH02_BACKEND_VALIDATION.json")
    canonical = backend.get("canonical_backend", {})
    protected = backend.get("protected_baseline", {})
    admission = backend.get("admission", {})
    if (
        canonical.get("records") != 3096
        or protected.get("records") != 2472
        or protected.get("record_bytes_and_relative_order_stable") is not True
        or admission.get("new_records") != 624
        or len(admission.get("correction_event_ids", [])) != 65
        or admission.get("correction_event_ids", [None])[0] != "O015-HAB-ADV-0097"
        or admission.get("correction_event_ids", [None])[-1] != "O015-HAB-ADV-0161"
    ):
        raise RuntimeError("backend report does not prove the admitted 2472+624=3096 transition")
    if sum(1 for _ in (ROOT / "backend/records.jsonl").open("rb")) != 3096:
        raise RuntimeError("canonical JSONL line count is not 3096")


def make_config() -> dict:
    validate_live_boundary()
    config = read_json(TEMPLATE_PATH)
    config["backend"]["jsonl"] = identity(ROOT / "backend/records.jsonl")
    config["backend"]["csv"] = identity(ROOT / "backend/records.csv")
    config["backend"]["validation"] = identity(ROOT / "qa/HABRING_CH01_CH02_BACKEND_VALIDATION.json")
    config["controls"] = {relative: identity(ROOT / relative) for relative in CONTROL_PATHS}
    return config


def make_lock(config: dict | None = None) -> dict:
    config = config or make_config()
    files = {relative: identity(ROOT / relative) for relative in sorted(set(MATERIAL_PATHS + CONTROL_PATHS))}
    return {
        "schema": "o015-habring-spine-release-input-lock-v1",
        "boundary": config["boundary"],
        "backend_record_count": 3096,
        "protected_backend_record_count": 2472,
        "new_backend_record_count": 624,
        "material_file_count": len(MATERIAL_PATHS),
        "control_file_count": len(CONTROL_PATHS),
        "release_packaging": {
            "inherited_file_count": config["expected_inherited_file_count"],
            "addition_file_count": config["expected_addition_file_count"],
            "release_file_count": config["expected_release_file_count"],
            "public_additions_in_order": config["public_additions_in_order"],
        },
        "files": files,
    }


def payload(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", dir=HERE, delete=False) as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
        staged = Path(handle.name)
    try:
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify existing config and lock without rewriting")
    args = parser.parse_args()
    config = make_config()
    lock = make_lock(config)
    config_bytes = payload(config)
    lock_bytes = payload(lock)
    if args.check:
        if not CONFIG_PATH.is_file() or CONFIG_PATH.read_bytes() != config_bytes:
            raise RuntimeError("final Habring release config is absent or stale")
        if not LOCK_PATH.is_file() or LOCK_PATH.read_bytes() != lock_bytes:
            raise RuntimeError("final Habring input lock is absent or stale")
    else:
        atomic_write(CONFIG_PATH, config_bytes)
        atomic_write(LOCK_PATH, lock_bytes)
    print(json.dumps({
        "result": "pass",
        "config": {"path": str(CONFIG_PATH), "bytes": len(config_bytes), "sha256": hashlib.sha256(config_bytes).hexdigest()},
        "input_lock": {"path": str(LOCK_PATH), "bytes": len(lock_bytes), "sha256": hashlib.sha256(lock_bytes).hexdigest()},
        "locked_files": len(lock["files"]),
        "network_operations": 0,
        "credential_reads": 0,
        "git_operations": 0,
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
