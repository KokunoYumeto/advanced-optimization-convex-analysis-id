#!/usr/bin/env python3
"""Offline, fail-closed rights/release audit for the D90 integrated edition.

The verifier is intentionally bounded to the current integrated candidate,
the controlling rights/provenance files, and the latest checked-in GitHub and
Zenodo publication evidence.  It performs no network, Git, or release action.
It writes only ``qa/INTEGRATED_RIGHTS_RELEASE_QA.json``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTPUT = HERE / "INTEGRATED_RIGHTS_RELEASE_QA.json"

MASTER = "source/id-ID/D90-O015-optimisasi-lanjut-analisis-konveks-id.tex"
BUILD_RECEIPT = "qa/INTEGRATED_READERS_BUILD.json"
VALIDATION_RECEIPT = "qa/INTEGRATED_READERS_VALIDATION.json"
PDF_RELATIVE = "output/pdf/D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf"
PDF_BUILD_RECEIPT = "qa/2026-08-27-integrated-pdf-build.json"
PDF_VALIDATION_RECEIPT = "qa/INTEGRATED_PDF_VALIDATION.json"
PDF_VISUAL_RECEIPT = "qa/INTEGRATED_PDF_VISUAL_QA.json"
BROWSER_RECEIPT = "qa/INTEGRATED_BROWSER_QA.json"
ORIGINAL03_CLOSURE_RECEIPT = "qa/ORIGINAL_03_COURSE_CLOSURE.json"
ORIGINAL03_BACKEND_BUILD_RECEIPT = "qa/ORIGINAL_03_BACKEND_BUILD.json"
ORIGINAL03_BACKEND_VALIDATION_RECEIPT = "qa/ORIGINAL_03_BACKEND_VALIDATION.json"

ORIGINAL01_HISTORICAL_RELEASE_IDENTITY = {
    "bytes": 27_431,
    "sha256": "db677ca6bab274a5db3e356fc996cef3bb00fb67770a90984460aa265fabcf26",
}

CORE_EVIDENCE = [
    "00_control/SOURCE_AUTHORITY.json",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/ADVERSE_LEDGER.jsonl",
    "README.md",
    "RIGHTS.md",
    "PROVENANCE.md",
    MASTER,
    BUILD_RECEIPT,
    VALIDATION_RECEIPT,
    PDF_BUILD_RECEIPT,
    PDF_VALIDATION_RECEIPT,
    PDF_VISUAL_RECEIPT,
    BROWSER_RECEIPT,
    ORIGINAL03_CLOSURE_RECEIPT,
    ORIGINAL03_BACKEND_BUILD_RECEIPT,
    ORIGINAL03_BACKEND_VALIDATION_RECEIPT,
]

ROUTE_EVIDENCE = [
    "release/github/2026-08-26-original-02/github-explicit-paths-original-02.json",
    "release/github/2026-08-26-original-02/github-public-readback-original-02.json",
    "release/github/2026-08-26-original-02/verify_github_original_02_public.py",
    "release/zenodo/2026-08-26-original-02/publish_original_02.py",
    "release/zenodo/2026-08-26-original-02/repair_original_02_privacy.py",
    "release/zenodo/2026-08-26-original-02/metadata-original-02.template.json",
    "release/zenodo/2026-08-26-original-02/zenodo-public-readback-original-02.json",
    "release/zenodo/2026-08-26-original-02/zenodo-privacy-readback-original-02.json",
    "release/zenodo/2026-08-26-original-02/zenodo-draft-closure-original-02.json",
    "release/zenodo/2026-08-26-original-02/zenodo-privacy-closure-original-02.json",
]

EXPECTED_MASTER_INPUTS = [
    "habring-01-prasyarat-id",
    "habring-02-konveksitas-id",
    "habring-03-subgradien-id",
    "habring-04-metode-subgradien-terproyeksi-id",
    "habring-05-metode-gradien-proksimal-id",
    "habring-06-akselerasi-id",
    "habring-07-dualitas-id",
    "habring-08-penurunan-gradien-stokastik-id",
    "habring-09-transportasi-optimal-id",
    "becker-01-dualitas-lagrange-slater-kkt-id",
    "becker-03-reduksi-varians-id",
    "original-01-metode-stokastik-komposit-cermin-minibatch-id",
    "becker-02-pemisahan-douglas-rachford-id",
    "original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id",
    "original-03-penutupan-kursus-id",
]

COMPANION_INPUT_MARKERS = ("mit-", "royer", "penn-")
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
GITHUB_REPOSITORY = "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id"
GITHUB_BRANCH = "main"
ZENODO_PARENT_RECORD_ID = "22104724"
ZENODO_PARENT_RECORD_DOI = "10.5281/zenodo.22104724"
ZENODO_CONCEPT_ID = "22059741"
ZENODO_CONCEPT_DOI = "10.5281/zenodo.22059741"

PROFILE_LOCATOR = re.compile(
    r"(?i)(?:file:/+)?[a-z]:[\\/]+users[\\/]+[^\\/\x00-\x20\"']+[\\/]"
)
CREDENTIAL_PATTERNS = {
    "authorization_bearer": re.compile(
        rb"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._~+/-]{20,}"
    ),
    "credential_assignment": re.compile(
        rb"(?i)(?:access[_ -]?token|api[_ -]?key|github[_ -]?token|zenodo[_ -]?token)"
        rb"\s*[:=]\s*[\"']?[A-Za-z0-9._~+/-]{20,}"
    ),
    "credential_query": re.compile(
        rb"(?i)(?:access_token|api_key|auth_token)=[A-Za-z0-9._~+/-]{20,}"
    ),
    "known_secret_prefix": re.compile(
        rb"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})"
    ),
    "credential_file_locator": re.compile(rb"(?i)new[ _-]+zenodo[ _-]+token\.md"),
}

MAX_ARCHIVE_DEPTH = 2
MAX_ARCHIVE_MEMBER_BYTES = 100_000_000
MAX_ARCHIVE_TOTAL_BYTES = 750_000_000


def rel_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def root_path(relative: str) -> Path:
    candidate = (ROOT / relative).resolve()
    candidate.relative_to(ROOT.resolve())
    return candidate


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(relative: str) -> dict[str, Any]:
    path = root_path(relative)
    return {
        "path": relative,
        "exists": path.is_file(),
        **(
            {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
            if path.is_file()
            else {}
        ),
    }


def load_json(relative: str) -> dict[str, Any]:
    value = json.loads(root_path(relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected a JSON object: {relative}")
    return value


def load_text(relative: str) -> str:
    return root_path(relative).read_text(encoding="utf-8", errors="replace")


def normalized_range_text(value: str) -> str:
    """Normalize typographic/doubled dashes without weakening exact ranges."""
    return value.replace("\u2013", "-").replace("\u2014", "-").replace("--", "-")


def recursive_identity_index(value: Any, found: dict[str, list[dict[str, Any]]]) -> None:
    if isinstance(value, dict):
        path = value.get("path")
        digest = value.get("sha256")
        size = value.get("bytes")
        if isinstance(path, str) and isinstance(digest, str):
            found.setdefault(path, []).append({"bytes": size, "sha256": digest})
        for child in value.values():
            recursive_identity_index(child, found)
    elif isinstance(value, list):
        for child in value:
            recursive_identity_index(child, found)


def receipt_binds_current_identity(
    value: Any, relative: str, current: dict[str, Any]
) -> bool:
    index: dict[str, list[dict[str, Any]]] = {}
    recursive_identity_index(value, index)
    return any(
        candidate.get("bytes") == current.get("bytes")
        and candidate.get("sha256") == current.get("sha256")
        for candidate in index.get(relative, [])
    )


def recursive_backend_identity_index(value: Any, found: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        required = {"jsonl_bytes", "jsonl_sha256", "csv_bytes", "csv_sha256"}
        if required.issubset(value):
            found.append(
                {
                    "records": value.get("records"),
                    "jsonl_bytes": value.get("jsonl_bytes"),
                    "jsonl_sha256": value.get("jsonl_sha256"),
                    "csv_bytes": value.get("csv_bytes"),
                    "csv_sha256": value.get("csv_sha256"),
                }
            )
        for child in value.values():
            recursive_backend_identity_index(child, found)
    elif isinstance(value, list):
        for child in value:
            recursive_backend_identity_index(child, found)


def json_status_passes(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for key in ("result", "status", "overall_result", "overall_status"):
        if str(value.get(key, "")).casefold() in {"pass", "passed", "ok", "success"}:
            return True
    return False


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    result: str,
    summary: str,
    evidence: Iterable[str] = (),
    details: Any | None = None,
) -> None:
    item: dict[str, Any] = {
        "check_id": check_id,
        "result": result,
        "summary": summary,
        "evidence": list(evidence),
    }
    if details is not None:
        item["details"] = details
    checks.append(item)


def contradiction(
    contradictions: list[dict[str, Any]],
    contradiction_id: str,
    summary: str,
    evidence: Iterable[str],
    deterministic_remedy: str,
) -> None:
    contradictions.append(
        {
            "contradiction_id": contradiction_id,
            "severity": "release_blocking",
            "summary": summary,
            "evidence": list(evidence),
            "deterministic_remedy": deterministic_remedy,
        }
    )


def privacy_hits_in_bytes(data: bytes, location: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    profile_count = 0
    for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
        text = data.decode(encoding, errors="ignore")
        profile_count += sum(1 for _ in PROFILE_LOCATOR.finditer(text))
    if profile_count:
        hits.append(
            {
                "location": location,
                "pattern": "windows_user_profile_locator",
                "count": profile_count,
            }
        )
    for name, pattern in CREDENTIAL_PATTERNS.items():
        count = len(pattern.findall(data))
        if count:
            hits.append({"location": location, "pattern": name, "count": count})
    return hits


def pdf_stream_hits(data: bytes, location: str) -> tuple[list[dict[str, Any]], bool]:
    if not data.startswith(b"%PDF-"):
        return [], False
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return [], False
    hits: list[dict[str, Any]] = []
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            hits.extend(
                privacy_hits_in_bytes(
                    text.encode("utf-8", errors="ignore"),
                    f"{location}!pdf-page-{page_number}",
                )
            )
    except Exception:
        return [], False
    return hits, True


def scan_payload(
    data: bytes,
    location: str,
    *,
    depth: int = 0,
) -> tuple[list[dict[str, Any]], dict[str, int | bool]]:
    hits = privacy_hits_in_bytes(data, location)
    pdf_hits, pdf_scanned = pdf_stream_hits(data, location)
    hits.extend(pdf_hits)
    stats: dict[str, int | bool] = {
        "archive_entries": 0,
        "archive_uncompressed_bytes": 0,
        "pdf_decoded": pdf_scanned,
    }
    if depth >= MAX_ARCHIVE_DEPTH or not zipfile.is_zipfile(io.BytesIO(data)):
        return hits, stats
    total = 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            member = info.filename
            hits.extend(
                privacy_hits_in_bytes(
                    member.encode("utf-8", errors="ignore"),
                    f"{location}!archive-entry-name",
                )
            )
            if info.is_dir():
                continue
            if info.file_size > MAX_ARCHIVE_MEMBER_BYTES:
                raise RuntimeError("archive member exceeds bounded privacy limit")
            total += info.file_size
            if total > MAX_ARCHIVE_TOTAL_BYTES:
                raise RuntimeError("archive exceeds bounded privacy limit")
            payload = archive.read(info)
            child_hits, child_stats = scan_payload(
                payload,
                f"{location}!{member}",
                depth=depth + 1,
            )
            hits.extend(child_hits)
            stats["archive_entries"] = int(stats["archive_entries"]) + 1 + int(
                child_stats["archive_entries"]
            )
            stats["archive_uncompressed_bytes"] = int(
                stats["archive_uncompressed_bytes"]
            ) + len(payload) + int(child_stats["archive_uncompressed_bytes"])
            stats["pdf_decoded"] = bool(stats["pdf_decoded"]) or bool(
                child_stats["pdf_decoded"]
            )
    return hits, stats


def unique_existing(paths: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for relative in paths:
        normalized = Path(relative).as_posix()
        if normalized in seen or normalized == rel_path(OUTPUT):
            continue
        seen.add(normalized)
        if root_path(normalized).is_file():
            result.append(normalized)
    return result


def scan_privacy(paths: list[str]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    archive_entries = 0
    archive_bytes = 0
    pdf_decoded_files = 0
    total_bytes = 0
    identities: list[dict[str, Any]] = []
    for relative in paths:
        path = root_path(relative)
        try:
            data = path.read_bytes()
            total_bytes += len(data)
            identities.append(
                {"path": relative, "bytes": len(data), "sha256": sha256_bytes(data)}
            )
            file_hits, stats = scan_payload(data, relative)
            hits.extend(file_hits)
            archive_entries += int(stats["archive_entries"])
            archive_bytes += int(stats["archive_uncompressed_bytes"])
            pdf_decoded_files += int(bool(stats["pdf_decoded"]))
        except Exception as error:
            failures.append({"path": relative, "error_type": type(error).__name__})
    return {
        "result": "pass" if not hits and not failures else "fail",
        "credential_material_recorded": False,
        "profile_or_credential_hit_count": sum(int(item["count"]) for item in hits),
        "hit_files": sorted({str(item["location"]).split("!", 1)[0] for item in hits}),
        "hits": hits,
        "scan_failures": failures,
        "file_count": len(paths),
        "aggregate_file_bytes": total_bytes,
        "archive_entries_scanned": archive_entries,
        "archive_uncompressed_bytes_scanned": archive_bytes,
        "pdf_decoded_file_count": pdf_decoded_files,
        "files": identities,
        "patterns": [
            "generic Windows user-profile locator",
            "authorization bearer value",
            "labeled access-token/API-key assignment",
            "credential-bearing URL query",
            "known provider secret prefix",
            "credential-file locator",
        ],
    }


def main() -> int:
    missing_evidence = [
        relative
        for relative in CORE_EVIDENCE + ROUTE_EVIDENCE
        if not root_path(relative).is_file()
    ]
    if missing_evidence:
        raise RuntimeError("required bounded evidence is missing")

    authority = load_json("00_control/SOURCE_AUTHORITY.json")
    build = load_json(BUILD_RECEIPT)
    validation = load_json(VALIDATION_RECEIPT)
    coverage = load_text("00_control/COVERAGE_OVERLAP.md")
    ledger = load_text("00_control/ADVERSE_LEDGER.jsonl")
    readme = load_text("README.md")
    rights = load_text("RIGHTS.md")
    provenance = load_text("PROVENANCE.md")
    master = load_text(MASTER)
    html = load_text("output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html")

    with root_path("00_control/COMPONENT_RIGHTS.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        rights_rows = list(csv.DictReader(stream))
    rights_by_id = {row["component_id"]: row for row in rights_rows}

    all_master_inputs = re.findall(r"\\input\{([^}]+)\}", master)
    master_inputs = [item for item in all_master_inputs if item != "o015-accessibility-id"]
    architecture = authority["selection_architecture"]
    canonical = architecture["canonical_structured_source_spine"]
    becker_target = architecture["bounded_structured_supplement_target"]
    companions = architecture["preserved_companions"]

    checks: list[dict[str, Any]] = []
    contradictions: list[dict[str, Any]] = []

    master_order_ok = master_inputs == EXPECTED_MASTER_INPUTS
    add_check(
        checks,
        "integrated_master_component_order",
        "pass" if master_order_ok else "fail",
        "The integrated master has the exact Habring/Becker/Original reader order."
        if master_order_ok
        else "The integrated master input order differs from the frozen expected order.",
        [MASTER],
        {
            "content_inputs": master_inputs,
            "preamble_inputs": [
                item for item in all_master_inputs if item not in master_inputs
            ],
            "expected": EXPECTED_MASTER_INPUTS,
        },
    )

    companions_absent = not any(
        any(marker in item.casefold() for marker in COMPANION_INPUT_MARKERS)
        for item in master_inputs
    )
    companion_control_ok = companions == [
        "o015-mit-ocw-6.253-spring-2012",
        "o015-royer-stochastic-gradient-2023-2024",
        "o015-penn-math555-v1.0-source",
    ]
    add_check(
        checks,
        "companions_remain_separate",
        "pass" if companions_absent and companion_control_ok else "fail",
        "MIT OCW, Royer, and Penn are preserved companion authorities and are not inputs to the integrated master.",
        [MASTER, "00_control/SOURCE_AUTHORITY.json", "00_control/COVERAGE_OVERLAP.md"],
        {"master_companion_inputs": [], "preserved_companions": companions},
    )

    habring_derivative_paths = [
        f"source/id-ID/habring-{chapter:02d}-{slug}"
        for chapter, slug in (
            (1, "prasyarat-id.tex"),
            (2, "konveksitas-id.tex"),
            (3, "subgradien-id.tex"),
            (4, "metode-subgradien-terproyeksi-id.tex"),
            (5, "metode-gradien-proksimal-id.tex"),
            (6, "akselerasi-id.tex"),
            (7, "dualitas-id.tex"),
            (8, "penurunan-gradien-stokastik-id.tex"),
            (9, "transportasi-optimal-id.tex"),
        )
    ]
    habring_rights_bindings = {
        expected: any(
            expected in row.get("path", "").split(" + ")
            and row.get("source_authority") == "o015-habring-arxiv-2607.11664v1"
            and row.get("rights_expression") == "CC BY 4.0"
            and row.get("status") == "derivative"
            for row in rights_rows
        )
        for expected in habring_derivative_paths
    }
    habring_control_ok = (
        canonical.get("authority_id") == "o015-habring-arxiv-2607.11664v1"
        and canonical.get("license") == "CC BY 4.0"
        and master_inputs[:9] == EXPECTED_MASTER_INPUTS[:9]
        and all(habring_rights_bindings.values())
    )
    habring_root_stale = (
        "Chapter 3--9" in rights
        or "MIT OpenCourseWare primary spine" in rights
        or "Modern convex-optimization companion: Andreas Habring" in provenance
    )
    add_check(
        checks,
        "habring_cc_by_4_exact_scope",
        "fail" if habring_root_stale else ("pass" if habring_control_ok else "fail"),
        "The controlling authority and master bind the complete Habring v1 spine to CC BY 4.0, but root rights/provenance still describe an obsolete partial/companion role."
        if habring_root_stale
        else "The complete Habring v1 spine is exactly scoped to CC BY 4.0.",
        [
            "00_control/SOURCE_AUTHORITY.json",
            "00_control/COMPONENT_RIGHTS.csv",
            MASTER,
            "RIGHTS.md",
            "PROVENANCE.md",
        ],
        {
            "authority_id": canonical.get("authority_id"),
            "authority_license": canonical.get("license"),
            "integrated_chapter_rights_bindings": habring_rights_bindings,
        },
    )
    if habring_root_stale:
        contradiction(
            contradictions,
            "C01_STALE_HABRING_AND_COMPANION_ROLES",
            "RIGHTS.md still calls MIT the primary spine and covers only Habring Chapters 3–9; PROVENANCE.md calls Habring a companion, contrary to the controlling Habring-v1 architecture.",
            ["RIGHTS.md", "PROVENANCE.md", "00_control/SOURCE_AUTHORITY.json", MASTER],
            "Reconcile root rights/provenance with the complete Habring preface/Chapters 1–9 CC BY 4.0 spine and identify MIT/Royer/Penn only as separate companions.",
        )

    becker_expected_rows = {
        "o015-becker-01-id-source",
        "o015-becker-02-id-source",
        "o015-becker-03-id-source",
    }
    becker_rows_present = becker_expected_rows.issubset(rights_by_id)
    becker_master_ok = [item for item in master_inputs if item.startswith("becker-")] == [
        "becker-01-dualitas-lagrange-slater-kkt-id",
        "becker-03-reduksi-varians-id",
        "becker-02-pemisahan-douglas-rachford-id",
    ]
    normalized_coverage = normalized_range_text(coverage)
    becker_exact_ranges = (
        "1263-1321",
        "1398-1405",
        "1414-1499",
        "1652-1726",
        "1731-1743",
        "2750-2797",
        "2971-2988",
    )
    becker_lines_ok = all(
        marker in normalized_coverage
        for marker in (
            *becker_exact_ranges,
        )
    )
    becker_stale_row = "variance reduction remains gated" in rights_by_id.get(
        "o015-becker-bounded-supplement-target", {}
    ).get("notes", "")
    becker_rights_bindings = {
        component_id: (
            component_id in rights_by_id
            and rights_by_id[component_id].get("source_authority")
            == "o015-becker-convex-optimization-class-98ed693"
            and "MIT upstream" in rights_by_id[component_id].get("rights_expression", "")
            and "CC BY-SA 4.0" in rights_by_id[component_id].get("rights_expression", "")
            and rights_by_id[component_id].get("status") == "admitted_derivative"
        )
        for component_id in becker_expected_rows
    }
    becker_witness_rights = {
        component_id: (
            component_id in rights_by_id
            and rights_by_id[component_id].get("rights_expression") == "MIT"
            and rights_by_id[component_id].get("status") == "admitted_source_witness"
        )
        for component_id in (
            "o015-becker-01-english-witness",
            "o015-becker-02-english-witness",
            "o015-becker-03-english-witness",
        )
    }
    root_becker_missing = not (
        "Stephen Becker" in rights
        and "Mitchell Krock" in rights
        and "Stephen Becker" in provenance
        and "Mitchell Krock" in provenance
        and "MIT" in rights
        and "CC BY-SA 4.0" in rights
    )
    def reader_discloses_bounded_becker_dual_layer(text: str) -> bool:
        plain = re.sub(r"<[^>]+>", " ", text)
        compact = re.sub(r"\s+", " ", plain).casefold()
        return all(
            marker in compact
            for marker in (
                "stephen becker",
                "mitchell krock",
                "tiga suplemen terbatas",
                "lisensi mit",
                "cc by-sa 4.0",
                "tidak ada klaim lisensi payung",
            )
        )

    # The exact commit and donor-line closure is mandatory in the controlling
    # authority/coverage/component-rights evidence above.  The human-facing
    # reader must identify the bounded Becker/Krock donor, MIT donor rights,
    # the separately licensed independent layer, and the no-blanket-license
    # boundary; duplicating every source-control line range in the title-page
    # rights paragraph is not itself a rights requirement.
    becker_reader_dual_layer_scope = all(
        reader_discloses_bounded_becker_dual_layer(text) for text in (master, html)
    )
    output_becker_underdisclosed = not becker_reader_dual_layer_scope
    becker_control_ok = (
        becker_target.get("license") == "MIT"
        and becker_target.get("commit")
        == "98ed6930084c435ba0f675f7646ced1f2fd8729e"
        and becker_rows_present
        and becker_master_ok
        and becker_lines_ok
        and all(becker_rights_bindings.values())
        and all(becker_witness_rights.values())
    )
    add_check(
        checks,
        "becker_krock_mit_exact_scope",
        "fail"
        if becker_stale_row or root_becker_missing or output_becker_underdisclosed
        else ("pass" if becker_control_ok else "fail"),
        "The donor commit and three nonduplicative ranges are frozen under MIT, but the current metadata is internally inconsistent or incomplete about Becker/Krock and the independent translation/correction layer.",
        [
            "00_control/SOURCE_AUTHORITY.json",
            "00_control/COMPONENT_RIGHTS.csv",
            "00_control/COVERAGE_OVERLAP.md",
            "RIGHTS.md",
            "PROVENANCE.md",
            MASTER,
            "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html",
        ],
        {
            "commit": becker_target.get("commit"),
            "admitted_ranges": [
                "1263-1321",
                "1398-1405",
                "1414-1499",
                "1652-1726",
                "1731-1743",
                "2750-2797",
                "2971-2988",
            ],
            "upstream_rights": "MIT",
            "independent_wording_rights": "CC BY-SA 4.0",
            "component_rights_bindings": becker_rights_bindings,
            "source_witness_rights": becker_witness_rights,
            "exact_commit_and_ranges_in_controls": (
                becker_target.get("commit")
                == "98ed6930084c435ba0f675f7646ced1f2fd8729e"
                and becker_lines_ok
            ),
            "bounded_donor_and_dual_rights_in_master_html": becker_reader_dual_layer_scope,
        },
    )
    if becker_stale_row:
        contradiction(
            contradictions,
            "C02_STALE_BECKER_03_GATE_ROW",
            "The bounded-supplement summary row says Becker-03 remains gated, while later component rows, SOURCE_AUTHORITY, and COVERAGE_OVERLAP say it is admitted and public.",
            ["00_control/COMPONENT_RIGHTS.csv", "00_control/SOURCE_AUTHORITY.json", "00_control/COVERAGE_OVERLAP.md"],
            "Replace the stale bounded-supplement summary with the exact admitted three-module state while retaining the excluded ranges and donor limitations.",
        )
    if root_becker_missing or output_becker_underdisclosed:
        contradiction(
            contradictions,
            "C03_BECKER_ROOT_AND_READER_DISCLOSURE_INCOMPLETE",
            "Root rights/provenance omit Becker/Krock, and integrated reader metadata states only the MIT donor layer without exactly scoping the independent CC BY-SA 4.0 translation/correction wording.",
            ["RIGHTS.md", "PROVENANCE.md", "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html"],
            "Add exact donor, typed-note, range, change, MIT-notice, independent-wording, and non-endorsement disclosures to the root and integrated reader metadata.",
        )

    original_source_paths = {
        "Original-01": "source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex",
        "Original-02": "source/id-ID/original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.tex",
        "Original-03": "source/id-ID/original-03-penutupan-kursus-id.tex",
    }
    original_source_independence = {
        name: (
            any(
                marker in load_text(relative).casefold()
                for marker in ("ditulis secara mandiri", "authorship: independent")
            )
        )
        for name, relative in original_source_paths.items()
    }
    original_component_rights_bindings = {
        name: any(
            relative in row.get("path", "").split(" + ")
            and row.get("source_authority") == "lane-authored"
            and row.get("rights_expression") == "CC BY-SA 4.0"
            and row.get("status") == "admitted_original"
            for row in rights_rows
        )
        for name, relative in original_source_paths.items()
    }
    # Original-01/02 predate the integrated master and carry their exact
    # CC BY-SA identity in the component ledger and enclosing reader rights
    # block rather than repeating a license line inside every TeX module.
    # Require both per-module independent-authorship disclosure and a matching
    # admitted component-rights row, so this remains fail closed.
    original_source_disclosures = {
        name: original_source_independence[name]
        and original_component_rights_bindings[name]
        for name in original_source_paths
    }
    original03_rows = [
        row for row in rights_rows if row["component_id"].startswith("o015-original-03")
    ]
    original03_authority_mentions = "original_03" in json.dumps(
        authority, ensure_ascii=False
    ).casefold()
    original03_control_missing = (
        not original03_rows
        or not original03_authority_mentions
        or not original_component_rights_bindings["Original-03"]
    )
    root_original03_missing = not all(
        any(marker in text.casefold() for marker in ("original-03", "original 03"))
        and "CC BY-SA 4.0" in text
        for text in (readme, rights, provenance)
    )
    ledger_original03_missing = "O015-ORIG-03" not in ledger and "original-03" not in ledger.casefold()
    original_master_ok = [item for item in master_inputs if item.startswith("original-")] == [
        "original-01-metode-stokastik-komposit-cermin-minibatch-id",
        "original-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id",
        "original-03-penutupan-kursus-id",
    ]
    add_check(
        checks,
        "original_01_02_03_cc_by_sa_scope",
        "fail"
        if (
            original03_control_missing
            or root_original03_missing
            or not all(original_source_disclosures.values())
            or not all(original_component_rights_bindings.values())
        )
        else ("pass" if original_master_ok else "fail"),
        "The master declares the three-part independent layer CC BY-SA 4.0, but Original-03 has no controlling authority/component-rights admission and root metadata still names only Original-01/02.",
        [
            MASTER,
            "00_control/SOURCE_AUTHORITY.json",
            "00_control/COMPONENT_RIGHTS.csv",
            "00_control/ADVERSE_LEDGER.jsonl",
            "README.md",
            "RIGHTS.md",
            "PROVENANCE.md",
        ],
        {
            "master_original_inputs": [
                item for item in master_inputs if item.startswith("original-")
            ],
            "original_03_component_rows": len(original03_rows),
            "original_03_authority_record": original03_authority_mentions,
            "original_03_ledger_mentions": not ledger_original03_missing,
            "source_independence": original_source_independence,
            "source_independence_and_component_cc_by_sa": original_source_disclosures,
            "component_rights_bindings": original_component_rights_bindings,
        },
    )
    if (
        original03_control_missing
        or root_original03_missing
        or not all(original_source_disclosures.values())
        or not all(original_component_rights_bindings.values())
    ):
        contradiction(
            contradictions,
            "C04_ORIGINAL_03_UNCONTROLLED_RIGHTS_SCOPE",
            "Original-03 is included in the integrated master and self-declares CC BY-SA 4.0, but it has no SOURCE_AUTHORITY or COMPONENT_RIGHTS admission; root README/RIGHTS/PROVENANCE do not cover it.",
            [MASTER, "00_control/SOURCE_AUTHORITY.json", "00_control/COMPONENT_RIGHTS.csv", "README.md", "RIGHTS.md", "PROVENANCE.md"],
            "Add exact Original-03 source/lab/reader/backend identities, independent-authorship boundary, CC BY-SA 4.0 scope, mathematical-witness boundary, O018 exclusion, model provenance, and non-endorsement to the controlling files.",
        )

    original03_closure = load_json(ORIGINAL03_CLOSURE_RECEIPT)
    original03_backend_build = load_json(ORIGINAL03_BACKEND_BUILD_RECEIPT)
    original03_backend_validation = load_json(ORIGINAL03_BACKEND_VALIDATION_RECEIPT)
    original03_build_input_mismatches: list[dict[str, Any]] = []
    for item in original03_backend_build.get("inputs", []):
        current = identity(item["path"])
        if (
            current.get("bytes") != item.get("bytes")
            or current.get("sha256") != item.get("sha256")
        ):
            original03_build_input_mismatches.append(
                {
                    "path": item["path"],
                    "receipt": {
                        "bytes": item.get("bytes"),
                        "sha256": item.get("sha256"),
                    },
                    "current": current,
                }
            )
    original03_summary = original03_closure.get("summary", {})
    original03_closure_counts_ok = (
        original03_summary.get("P1") == 0
        and original03_summary.get("P2") == 0
        and original03_summary.get("P3") == 0
        and original03_summary.get("assessment_count") == 54
        and original03_summary.get("proof_rubric_count") == 7
        and original03_summary.get("capstone_milestone_count") == 7
        and original03_summary.get("computation_components_replayed_twice") == 3
    )
    original03_backend = original03_backend_validation.get("backend", {})
    original03_backend_current = {
        "jsonl": identity("backend/records.jsonl"),
        "csv": identity("backend/records.csv"),
    }
    original03_backend_identity_ok = (
        original03_backend.get("records") == 4_877
        and original03_backend_current["jsonl"].get("bytes")
        == original03_backend.get("jsonl", {}).get("bytes")
        and original03_backend_current["jsonl"].get("sha256")
        == original03_backend.get("jsonl", {}).get("sha256")
        and original03_backend_current["csv"].get("bytes")
        == original03_backend.get("csv", {}).get("bytes")
        and original03_backend_current["csv"].get("sha256")
        == original03_backend.get("csv", {}).get("sha256")
        and original03_backend.get("jsonl_csv_lossless_equality") is True
    )
    original03_qa_ready = (
        json_status_passes(original03_closure)
        and json_status_passes(original03_backend_build)
        and json_status_passes(original03_backend_validation)
        and original03_closure_counts_ok
        and not original03_build_input_mismatches
        and original03_backend_identity_ok
    )
    add_check(
        checks,
        "original_03_course_closure_and_backend",
        "pass" if original03_qa_ready else "fail",
        "Original-03 has a passing zero-defect course-closure audit, byte-current source/lab inputs, and a lossless 4,877-record backend."
        if original03_qa_ready
        else "Original-03 closure, source/lab binding, or final 4,877-record backend evidence is missing, stale, or failing.",
        [
            ORIGINAL03_CLOSURE_RECEIPT,
            ORIGINAL03_BACKEND_BUILD_RECEIPT,
            ORIGINAL03_BACKEND_VALIDATION_RECEIPT,
            "backend/records.jsonl",
            "backend/records.csv",
        ],
        {
            "closure_receipt_passes": json_status_passes(original03_closure),
            "closure_counts_match": original03_closure_counts_ok,
            "closure_summary": original03_summary,
            "backend_build_receipt_passes": json_status_passes(
                original03_backend_build
            ),
            "backend_validation_receipt_passes": json_status_passes(
                original03_backend_validation
            ),
            "build_input_mismatches": original03_build_input_mismatches,
            "backend_identity_matches_current_4877_records": original03_backend_identity_ok,
            "current_backend": original03_backend_current,
        },
    )
    if not original03_qa_ready:
        contradiction(
            contradictions,
            "C04A_ORIGINAL_03_CLOSURE_OR_BACKEND_NOT_BOUND",
            "The release candidate is not yet bound to a passing Original-03 course-closure audit and the exact final 4,877-record backend.",
            [
                ORIGINAL03_CLOSURE_RECEIPT,
                ORIGINAL03_BACKEND_BUILD_RECEIPT,
                ORIGINAL03_BACKEND_VALIDATION_RECEIPT,
            ],
            "Repair the exact failing Original-03 source/lab/assessment/backend evidence, rerun deterministic closure and backend validation, and preserve byte-current passing receipts.",
        )

    current_cursor = authority.get("current_production_cursor", {})
    current_cursor_text = json.dumps(current_cursor, ensure_ascii=False).casefold()
    partial_markers = {
        "source_authority_cursor": current_cursor.get("state"),
        # Historical checkpoint prose may remain as provenance. Only the
        # current/top status surfaces and live production cursor are gates.
        "source_authority_current_cursor_is_partial": any(
            marker in current_cursor_text
            for marker in (
                "closure_next",
                "build cumulative assessment",
                "additional nonduplicative open-computation labs",
                "build the capstone",
            )
        ),
        "coverage_current_status_is_partial": any(
            marker in coverage[:5000].casefold()
            for marker in (
                "the original layer still must close",
                "the overall o015 course remains partial",
            )
        ),
        "readme_current_status_is_partial": any(
            marker in readme[:8000].casefold()
            for marker in (
                "secara keseluruhan belum selesai",
                "status tetap parsial",
            )
        ),
    }
    controls_still_partial = any(
        partial_markers[key]
        for key in (
            "source_authority_current_cursor_is_partial",
            "coverage_current_status_is_partial",
            "readme_current_status_is_partial",
        )
    )
    add_check(
        checks,
        "final_integrated_state_reconciled",
        "fail" if controls_still_partial else "pass",
        "The integrated source contains assessment, labs, capstone, and final readers, while controlling/root metadata still says those exact layers are unfinished.",
        [MASTER, "00_control/SOURCE_AUTHORITY.json", "00_control/COVERAGE_OVERLAP.md", "README.md"],
        partial_markers,
    )
    if controls_still_partial:
        contradiction(
            contradictions,
            "C05_CONTROLS_STILL_DECLARE_COURSE_PARTIAL",
            "SOURCE_AUTHORITY, COVERAGE_OVERLAP, and README still direct production to cumulative assessment/labs/capstone/integrated readers even though those layers are now present in the integrated source.",
            ["00_control/SOURCE_AUTHORITY.json", "00_control/COVERAGE_OVERLAP.md", "README.md", MASTER],
            "Reconcile the production cursor and completion statements to the exact admitted Original-03 and integrated artifact identities without erasing historical partial-checkpoint statements.",
        )

    authority_index: dict[str, list[dict[str, Any]]] = {}
    recursive_identity_index(authority, authority_index)
    original01_relative = "source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex"
    original01_actual = identity(original01_relative)
    original01_authority = authority_index.get(original01_relative, [])
    original01_current_match = any(
        item.get("bytes") == original01_actual.get("bytes")
        and item.get("sha256") == original01_actual.get("sha256")
        for item in original01_authority
    )
    original01_historical_match = any(
        item.get("bytes") == ORIGINAL01_HISTORICAL_RELEASE_IDENTITY["bytes"]
        and item.get("sha256")
        == ORIGINAL01_HISTORICAL_RELEASE_IDENTITY["sha256"]
        for item in original01_authority
    )
    original01_versioned_match = (
        original01_current_match
        and original01_historical_match
        and original01_actual.get("sha256")
        != ORIGINAL01_HISTORICAL_RELEASE_IDENTITY["sha256"]
    )
    add_check(
        checks,
        "original_01_authority_identity_current",
        "pass" if original01_versioned_match else "fail",
        "The immutable Original-01 public-release identity and the current integrated descendant are both preserved as distinct controlling identities."
        if original01_versioned_match
        else "Original-01 authority metadata does not preserve both the immutable public-release identity and the distinct current integrated descendant.",
        [original01_relative, "00_control/SOURCE_AUTHORITY.json"],
        {
            "current_actual": original01_actual,
            "expected_historical_public_release": ORIGINAL01_HISTORICAL_RELEASE_IDENTITY,
            "current_identity_recorded": original01_current_match,
            "historical_identity_preserved": original01_historical_match,
            "authority_identities": original01_authority,
        },
    )
    if not original01_versioned_match:
        contradiction(
            contradictions,
            "C06_ORIGINAL_01_AUTHORITY_IDENTITY_DRIFT",
            "SOURCE_AUTHORITY does not yet preserve both the immutable historical Original-01 public-release identity and the distinct current integrated descendant identity.",
            [original01_relative, "00_control/SOURCE_AUTHORITY.json", BUILD_RECEIPT],
            "Preserve the 27,431-byte historical release identity, add the explicit 27,425-byte integrated-descendant identity, disclose the bounded typography/accessibility correction, and bind dependent integrated artifacts to the descendant bytes.",
        )

    integrated_build_receipts: list[tuple[str, dict[str, Any]]] = [
        (BUILD_RECEIPT, build)
    ]
    if root_path(PDF_BUILD_RECEIPT).is_file():
        integrated_build_receipts.append(
            (PDF_BUILD_RECEIPT, load_json(PDF_BUILD_RECEIPT))
        )
    build_input_mismatches: list[dict[str, Any]] = []
    build_input_missing: list[str] = []
    for receipt_path, receipt in integrated_build_receipts:
        declared_inputs = receipt.get("inputs", receipt.get("declared_inputs", []))
        for item in declared_inputs:
            relative = item["path"]
            current = identity(relative)
            if not current.get("exists"):
                build_input_missing.append(relative)
            elif current.get("bytes") != item.get("bytes") or current.get(
                "sha256"
            ) != item.get("sha256"):
                build_input_mismatches.append(
                    {
                        "receipt_path": receipt_path,
                        "path": relative,
                        "receipt": {
                            "bytes": item.get("bytes"),
                            "sha256": item.get("sha256"),
                        },
                        "current": {
                            "bytes": current.get("bytes"),
                            "sha256": current.get("sha256"),
                        },
                    }
                )
    build_inputs_current = not build_input_mismatches and not build_input_missing
    add_check(
        checks,
        "integrated_reader_inputs_current",
        "pass" if build_inputs_current else "fail",
        "All integrated-reader input identities still match the build receipt."
        if build_inputs_current
        else "One or more current source identities differ from the integrated-reader build receipt.",
        [item[0] for item in integrated_build_receipts],
        {
            "receipts_checked": [item[0] for item in integrated_build_receipts],
            "mismatches": build_input_mismatches,
            "missing": sorted(set(build_input_missing)),
        },
    )
    if not build_inputs_current:
        contradiction(
            contradictions,
            "C07_INTEGRATED_BUILD_INPUT_DRIFT",
            "The checked-in integrated HTML/EPUB receipt does not bind every current source input byte-for-byte.",
            [
                *[item[0] for item in integrated_build_receipts],
                *[item["path"] for item in build_input_mismatches],
            ],
            "Freeze the intended source bytes and regenerate every affected integrated PDF/HTML/EPUB build plus validation receipt before release.",
        )

    artifact_mismatches: list[dict[str, Any]] = []
    for name, item in build.get("artifacts", {}).items():
        current = identity(item["path"])
        if current.get("bytes") != item.get("bytes") or current.get("sha256") != item.get(
            "sha256"
        ):
            artifact_mismatches.append(
                {
                    "kind": name,
                    "path": item["path"],
                    "receipt": {"bytes": item.get("bytes"), "sha256": item.get("sha256")},
                    "current": current,
                }
            )
    reader_receipts_pass = json_status_passes(build) and json_status_passes(validation)
    add_check(
        checks,
        "integrated_html_epub_artifact_identity",
        "pass" if not artifact_mismatches and reader_receipts_pass else "fail",
        "Current integrated HTML/EPUB bytes match passing build and validation receipts."
        if not artifact_mismatches and reader_receipts_pass
        else "Current integrated reader artifacts differ from their receipt or a reader receipt does not pass.",
        [BUILD_RECEIPT, VALIDATION_RECEIPT],
        {
            "mismatches": artifact_mismatches,
            "build_receipt_passes": json_status_passes(build),
            "validation_receipt_passes": json_status_passes(validation),
        },
    )

    browser_receipt = load_json(BROWSER_RECEIPT)
    html_relative = "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html"
    html_identity = identity(html_relative)
    browser_viewports = {
        str(item.get("name")): item
        for item in browser_receipt.get("viewports", [])
        if isinstance(item, dict)
    }
    browser_viewport_contract = all(
        name in browser_viewports
        and browser_viewports[name].get("width") == width
        and browser_viewports[name].get("root_horizontal_overflow_pixels") == 0
        and browser_viewports[name].get("escaped_visible_elements") == 0
        and float(browser_viewports[name].get("main", {}).get("viewport_ratio", 0))
        >= 0.90
        for name, width in (("desktop", 1440), ("tablet", 768), ("phone", 390))
    )
    browser_findings = browser_receipt.get("visual_findings", {})
    browser_findings_ok = all(
        browser_findings.get(key) == 0
        for key in (
            "clipped_text_or_math",
            "page_level_horizontal_overflow",
            "escaped_content",
            "broken_images",
            "uncontained_wide_formulas",
            "uncontained_wide_tables",
            "title_or_author_overflow",
            "unreadable_body_text",
        )
    )
    browser_common = browser_receipt.get("common", {})
    browser_ready = (
        json_status_passes(browser_receipt)
        and receipt_binds_current_identity(
            browser_receipt, html_relative, html_identity
        )
        and browser_receipt.get("method", {}).get("local_server_stopped_after_review")
        is True
        and browser_receipt.get("method", {}).get(
            "viewport_override_reset_after_review"
        )
        is True
        and browser_viewport_contract
        and browser_findings_ok
        and browser_common.get("language") == "id-ID"
        and browser_common.get("missing_internal_targets") == 0
        and browser_common.get("broken_images") == 0
        and int(browser_common.get("native_mathml_surfaces", 0)) > 0
    )
    add_check(
        checks,
        "integrated_browser_release_surface",
        "pass" if browser_ready else "fail",
        "The current integrated HTML is byte-bound to a passing live desktop/tablet/phone browser review with page-filling layout and locally contained wide content."
        if browser_ready
        else "The current integrated HTML lacks a byte-current passing live browser receipt or fails its responsive/reflow contract.",
        [html_relative, BROWSER_RECEIPT],
        {
            "html": html_identity,
            "receipt_passes": json_status_passes(browser_receipt),
            "binds_current_html": receipt_binds_current_identity(
                browser_receipt, html_relative, html_identity
            ),
            "viewport_contract_passes": browser_viewport_contract,
            "visual_findings_pass": browser_findings_ok,
            "viewports": browser_viewports,
        },
    )
    if not browser_ready:
        contradiction(
            contradictions,
            "C07A_INTEGRATED_BROWSER_NOT_RELEASE_BOUND",
            "The primary reflow reader is not yet bound to passing live browser evidence at desktop, tablet, and phone widths.",
            [html_relative, BROWSER_RECEIPT],
            "Rerun the integrated HTML in a real browser at 1440, 768, and 390 CSS pixels; require no page overflow or escaped content, contained wide math/tables, readable page-filling geometry, then record the exact artifact bytes in a passing receipt.",
        )

    pdf_relative = PDF_RELATIVE
    pdf_identity = identity(pdf_relative)
    pdf_receipt_paths = sorted(
        rel_path(path)
        for path in HERE.glob("*.json")
        if path.resolve() != OUTPUT.resolve()
        and "integrated" in path.name.casefold()
        and "pdf" in path.name.casefold()
    )
    pdf_receipts = []
    for relative in pdf_receipt_paths:
        try:
            receipt = load_json(relative)
            pdf_receipts.append(
                {
                    "path": relative,
                    "passes": json_status_passes(receipt),
                    "binds_current_pdf": receipt_binds_current_identity(
                        receipt, pdf_relative, pdf_identity
                    ),
                    "visual_judgment_pending": bool(
                        re.search(
                            r'"visual_judgment_pending"\s*:\s*true',
                            json.dumps(receipt, ensure_ascii=False),
                            flags=re.IGNORECASE,
                        )
                    ),
                    **identity(relative),
                }
            )
        except Exception:
            pdf_receipts.append(
                {
                    "path": relative,
                    "passes": False,
                    "binds_current_pdf": False,
                    "visual_judgment_pending": True,
                    **identity(relative),
                }
            )
    passing_bound_pdf_receipts = [
        item
        for item in pdf_receipts
        if item["passes"] and item["binds_current_pdf"]
    ]
    pdf_build_bound = any(
        item["path"] == PDF_BUILD_RECEIPT for item in passing_bound_pdf_receipts
    )
    pdf_validation_bound = any(
        item["path"] == PDF_VALIDATION_RECEIPT
        for item in passing_bound_pdf_receipts
    )
    pdf_visual_bound = any(
        item["path"] == PDF_VISUAL_RECEIPT
        and not item["visual_judgment_pending"]
        for item in passing_bound_pdf_receipts
    )
    pdf_build_receipt = load_json(PDF_BUILD_RECEIPT)
    pdf_builds = pdf_build_receipt.get("builds", [])
    pdf_build_content_ok = (
        pdf_build_receipt.get("byte_identical") is True
        and len(pdf_builds) == 2
        and all(
            build_item.get("pdf", {}).get("bytes") == pdf_identity.get("bytes")
            and build_item.get("pdf", {}).get("sha256")
            == pdf_identity.get("sha256")
            and build_item.get("pages") == 141
            and build_item.get("lang") == "id-ID"
            and build_item.get("marked") is True
            and build_item.get("struct_tree") is True
            and build_item.get("tabs_s_pages") == 141
            and all(value == 0 for value in build_item.get("log_findings", {}).values())
            for build_item in pdf_builds
        )
    )
    pdf_validation_receipt = load_json(PDF_VALIDATION_RECEIPT)
    pdf_validation_properties = pdf_validation_receipt.get("pdf", {})
    pdf_render = pdf_validation_receipt.get("render", {})
    pdf_validation_content_ok = (
        pdf_validation_properties.get("a4_pages") == 141
        and pdf_validation_properties.get("language") == "id-ID"
        and pdf_validation_properties.get("marked") is True
        and pdf_validation_properties.get("structure_tree") is True
        and pdf_validation_properties.get("parent_tree") is True
        and pdf_validation_properties.get("tabs_s_pages") == 141
        and pdf_validation_properties.get("unsafe_actions") == 0
        and pdf_validation_properties.get("form_fields") == 0
        and int(pdf_validation_properties.get("searchable_text_characters", 0)) > 0
        and pdf_validation_receipt.get("fonts", {}).get("all_embedded") is True
        and pdf_render.get("all_pages_rendered") is True
        and len(pdf_render.get("pages", [])) == 141
        and pdf_render.get("visual_judgment_pending") is False
    )
    pdf_visual_receipt = load_json(PDF_VISUAL_RECEIPT)
    pdf_visual_findings = pdf_visual_receipt.get("findings", {})
    pdf_visual_content_ok = (
        pdf_visual_receipt.get("method", {}).get("all_pages_rendered") is True
        and pdf_visual_receipt.get("method", {}).get("all_pages_inspected") is True
        and pdf_visual_receipt.get("artifact", {}).get("pages") == 141
        and len(pdf_visual_receipt.get("contact_sheets", [])) == 12
        and all(value == 0 for value in pdf_visual_findings.values())
    )
    pdf_ready = (
        bool(pdf_identity.get("exists"))
        and pdf_build_bound
        and pdf_validation_bound
        and pdf_visual_bound
        and pdf_build_content_ok
        and pdf_validation_content_ok
        and pdf_visual_content_ok
    )
    add_check(
        checks,
        "integrated_pdf_release_surface",
        "pass" if pdf_ready else "fail",
        "The integrated PDF exists and is bound by passing build, validation, and completed visual receipts."
        if pdf_ready
        else "The integrated PDF is missing, receipt-drifted, or still lacks completed build/validation/visual binding.",
        [pdf_relative, *pdf_receipt_paths],
        {
            "pdf": pdf_identity,
            "build_bound": pdf_build_bound,
            "validation_bound": pdf_validation_bound,
            "visual_receipt_bound": pdf_visual_bound,
            "deterministic_build_content_passes": pdf_build_content_ok,
            "validation_accessibility_content_passes": pdf_validation_content_ok,
            "all_page_visual_content_passes": pdf_visual_content_ok,
            "receipts": pdf_receipts,
        },
    )
    if not pdf_ready:
        contradiction(
            contradictions,
            "C08_INTEGRATED_PDF_NOT_RELEASE_BOUND",
            "The reader-first release cannot name a verified integrated PDF as default preview from the current files.",
            [pdf_relative, *pdf_receipt_paths],
            "Build the integrated PDF, freeze its identity in passing build/validation/visual/accessibility receipts, then rerun this verifier.",
        )

    current_backend = {
        "jsonl": identity("backend/records.jsonl"),
        "csv": identity("backend/records.csv"),
    }
    backend_authority_identities: list[dict[str, Any]] = []
    recursive_backend_identity_index(authority, backend_authority_identities)
    backend_identity_match = any(
        current_backend["jsonl"].get("bytes") == candidate.get("jsonl_bytes")
        and current_backend["jsonl"].get("sha256") == candidate.get("jsonl_sha256")
        and current_backend["csv"].get("bytes") == candidate.get("csv_bytes")
        and current_backend["csv"].get("sha256") == candidate.get("csv_sha256")
        for candidate in backend_authority_identities
    )
    backend_record_count = sum(1 for _ in root_path("backend/records.jsonl").open("rb"))
    readme_backend_current = any(
        marker in readme
        for marker in (
            str(backend_record_count),
            f"{backend_record_count:,}",
            f"{backend_record_count:,}".replace(",", "."),
        )
    )
    backend_validation_current = (
        json_status_passes(original03_backend_validation)
        and original03_backend_identity_ok
        and backend_record_count == 4_877
    )
    backend_control_current = (
        backend_identity_match
        and readme_backend_current
        and backend_validation_current
    )
    add_check(
        checks,
        "integrated_backend_control_identity",
        "pass" if backend_control_current else "fail",
        "The current backend identity is recorded in controlling authority metadata."
        if backend_control_current
        else "The current backend has advanced beyond the last backend identity recorded in SOURCE_AUTHORITY/README.",
        ["backend/records.jsonl", "backend/records.csv", "00_control/SOURCE_AUTHORITY.json", "README.md"],
        {
            "current": current_backend,
            "current_record_count": backend_record_count,
            "authority_backend_identities": backend_authority_identities,
            "readme_states_current_record_count": readme_backend_current,
            "passing_validation_binds_current_4877_records": backend_validation_current,
        },
    )
    if not backend_control_current:
        contradiction(
            contradictions,
            "C09_BACKEND_AUTHORITY_AND_DISCOVERY_STALE",
            "The current integrated backend bytes/record count are not represented by the last controlling Original-02 backend identity and README discovery statement.",
            ["backend/records.jsonl", "backend/records.csv", "00_control/SOURCE_AUTHORITY.json", "README.md"],
            "Record the final integrated backend count and exact identities in controlling/discovery metadata and retain its passing deterministic validation receipt.",
        )

    master_compact = re.sub(r"\s+", " ", master)
    html_compact = re.sub(r"\s+", " ", html)
    disclosure_markers = {
        "habring_source": all(
            "arXiv:2607.11664v1" in text for text in (master, html, provenance)
        ),
        "habring_license": all("CC BY 4.0" in text for text in (master, html, rights)),
        "becker_krock_source": all(
            "Stephen Becker" in text and "Mitchell Krock" in text
            for text in (master, html)
        ),
        "becker_commit_ranges_and_dual_rights": (
            becker_control_ok and becker_reader_dual_layer_scope
        ),
        "original_cc_by_sa_and_independence": all(
            original_source_disclosures.values()
        )
        and "CC BY-SA 4.0" in master
        and "CC BY-SA 4.0" in html,
        "model": MODEL in master and MODEL in html and MODEL in provenance,
        "changes": "Perubahan substantif dan koreksi" in master_compact
        and "koreksi" in html_compact.casefold()
        and "ADVERSE_LEDGER.jsonl" in provenance,
        "nonendorsement": any(
            marker in master_compact.casefold()
            for marker in (
                "bukan karya resmi atau dukungan",
                "bukan edisi resmi atau dukungan",
            )
        )
        and any(
            marker in html_compact.casefold()
            for marker in (
                "bukan karya resmi atau dukungan",
                "bukan edisi resmi atau dukungan",
            )
        )
        and "no endorsement" in provenance.casefold(),
        "no_blanket_license": "tidak ada klaim lisensi payung"
        in master_compact.casefold()
        and "tidak ada klaim lisensi payung" in html_compact.casefold()
        and "no blanket license" in rights.casefold()
        and "no blanket license" in provenance.casefold(),
        "companions": all(name in master for name in ("MIT OpenCourseWare", "Clément", "Penn State")),
        "o018": "Materi O018" in master,
    }
    disclosure_pass = all(disclosure_markers.values())
    add_check(
        checks,
        "integrated_frontmatter_source_model_change_nonendorsement",
        "pass" if disclosure_pass else "fail",
        "The integrated source and current readers carry source, model, change, non-endorsement, companion, and O018 disclosures.",
        [MASTER, "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html", "PROVENANCE.md"],
        disclosure_markers,
    )

    o018_markers = {
        "master_exclusion": "Materi O018" in master and "di luar cakupan" in master,
        "coverage_boundary": all(
            marker in coverage
            for marker in (
                "LP/MIP modelling",
                "simplex and tableau mechanics",
                "LP sensitivity",
                "network/discrete optimization",
            )
        ),
        "becker_lp_ranges_excluded": all(
            marker in coverage for marker in ("1322–1397", "1406–1413", "1727–1730")
        ),
        "companions_not_integrated": companions_absent,
        "original_01_probability_simplex_only": "simpleks} di sini hanya menunjuk himpunan probabilitas"
        in load_text("source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex"),
    }
    add_check(
        checks,
        "o018_nonoverlap",
        "pass" if all(o018_markers.values()) else "fail",
        "The integrated boundary excludes O018 LP/MIP/simplex-tableau/sensitivity/network curriculum; probability-simplex and general KKT uses remain in continuous convex analysis.",
        [MASTER, "00_control/COVERAGE_OVERLAP.md", "00_control/COMPONENT_RIGHTS.csv"],
        o018_markers,
    )

    old_metadata = load_json(
        "release/zenodo/2026-08-26-original-02/metadata-original-02.template.json"
    )["metadata"]
    old_title = old_metadata.get("title", "")
    old_creators = json.dumps(old_metadata.get("creators", []), ensure_ascii=False)
    old_contributors = json.dumps(old_metadata.get("contributors", []), ensure_ascii=False)
    ttp_markers = {
        "integrated_master_title": "TTP" not in re.search(
            r"\\title\{([^}]+)\}", master
        ).group(1),
        "integrated_master_author": "TTP" not in re.search(
            r"\\author\{(.+?)\}\s*\\date", master, flags=re.DOTALL
        ).group(1),
        "integrated_html_title": "TTP" not in re.search(
            r"<title>(.*?)</title>", html, flags=re.DOTALL | re.IGNORECASE
        ).group(1),
        "prior_zenodo_title": "TTP" not in old_title,
        "prior_zenodo_creators": "TTP" not in old_creators,
        "prior_zenodo_contributor_only": "TTP" in old_contributors,
    }
    add_check(
        checks,
        "no_ttp_title_or_lead_creator",
        "pass" if all(ttp_markers.values()) else "fail",
        "TTP is absent from title and lead creator surfaces; the established Zenodo role is contributor/other only.",
        [MASTER, "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html", "release/zenodo/2026-08-26-original-02/metadata-original-02.template.json"],
        ttp_markers,
    )

    github_paths = load_json(
        "release/github/2026-08-26-original-02/github-explicit-paths-original-02.json"
    )
    github_receipt = load_json(
        "release/github/2026-08-26-original-02/github-public-readback-original-02.json"
    )
    zenodo_receipt = load_json(
        "release/zenodo/2026-08-26-original-02/zenodo-public-readback-original-02.json"
    )
    privacy_receipt = load_json(
        "release/zenodo/2026-08-26-original-02/zenodo-privacy-readback-original-02.json"
    )
    zenodo_closure = load_json(
        "release/zenodo/2026-08-26-original-02/zenodo-privacy-closure-original-02.json"
    )
    github_verifier_script = load_text(
        "release/github/2026-08-26-original-02/verify_github_original_02_public.py"
    )
    prior_version_publisher_script = load_text(
        "release/zenodo/2026-08-26-original-02/publish_original_02.py"
    )
    current_record_repair_script = load_text(
        "release/zenodo/2026-08-26-original-02/repair_original_02_privacy.py"
    )
    expected_github_repository = {
        "owner": "KokunoYumeto",
        "name": "advanced-optimization-convex-analysis-id",
        "branch": GITHUB_BRANCH,
    }
    github_route_ok = (
        github_paths["repository"] == expected_github_repository
        and github_receipt.get("repository") == expected_github_repository
        and github_receipt.get("result") == "pass"
    )
    github_script_route_ok = all(
        marker in github_verifier_script
        for marker in (
            'MANIFEST_PATH = HERE / "github-explicit-paths-original-02.json"',
            "raw.githubusercontent.com",
            'branch = repository.get("branch")',
        )
    )
    prior_zenodo_version_pattern_ok = all(
        marker in prior_version_publisher_script
        for marker in (
            'CONCEPT_ID = "22059741"',
            'CONCEPT_DOI = "10.5281/zenodo.22059741"',
            "never creates a new concept",
            'f"{API}/records/{PARENT_RECORD_ID}/versions"',
        )
    )
    current_zenodo_record_anchor_ok = all(
        marker in current_record_repair_script
        for marker in (
            'RECORD_ID = "22104724"',
            'RECORD_DOI = "10.5281/zenodo.22104724"',
            'CONCEPT_ID = "22059741"',
            'CONCEPT_DOI = "10.5281/zenodo.22059741"',
            "never creates a new version or concept",
        )
    )
    zenodo_route_ok = (
        str(zenodo_receipt.get("record_id")) == ZENODO_PARENT_RECORD_ID
        and zenodo_receipt.get("record_doi") == ZENODO_PARENT_RECORD_DOI
        and str(zenodo_receipt.get("concept_id")) == ZENODO_CONCEPT_ID
        and zenodo_receipt.get("concept_doi") == ZENODO_CONCEPT_DOI
        and zenodo_receipt.get("result") == "pass"
        and privacy_receipt.get("result") == "pass"
        and privacy_receipt.get("file_count") == 99
        and privacy_receipt.get("profile_locator_hits_in_public_additions") == 0
        and zenodo_closure.get("concept_open_draft_count") == 0
    )
    route = {
        "result": "pass"
        if (
            github_route_ok
            and github_script_route_ok
            and zenodo_route_ok
            and prior_zenodo_version_pattern_ok
            and current_zenodo_record_anchor_ok
        )
        else "fail",
        "offline_evidence_only": True,
        "network_accessed": False,
        "github": {
            "repository": GITHUB_REPOSITORY,
            "branch": GITHUB_BRANCH,
            "latest_verified_commit": github_receipt.get("commit"),
            "latest_receipt_result": github_receipt.get("result"),
            "anonymous_verifier_route_matches": github_script_route_ok,
            "create_replacement_repository": False,
        },
        "zenodo": {
            "version_source_record_id": ZENODO_PARENT_RECORD_ID,
            "version_source_record_doi": ZENODO_PARENT_RECORD_DOI,
            "concept_id": ZENODO_CONCEPT_ID,
            "concept_doi": ZENODO_CONCEPT_DOI,
            "create_new_concept": False,
            "use_existing_record_version_action": True,
            "latest_receipt_result": zenodo_receipt.get("result"),
            "latest_receipt_file_count": zenodo_receipt.get("file_count"),
            "latest_record_privacy_result": privacy_receipt.get("result"),
            "latest_record_profile_locator_hits": privacy_receipt.get(
                "profile_locator_hits_in_public_additions"
            ),
            "last_verified_open_draft_count": zenodo_closure.get(
                "concept_open_draft_count"
            ),
            "fresh_remote_state_must_be_rechecked_by_publication_preflight": True,
            "prior_version_script_proves_existing_record_version_pattern": prior_zenodo_version_pattern_ok,
            "prior_version_script_is_not_current_execution_authority": True,
            "current_record_repair_script_proves_latest_record_and_concept_anchor": current_zenodo_record_anchor_ok,
        },
    }
    add_check(
        checks,
        "existing_github_and_zenodo_route",
        route["result"],
        "Checked-in exact-byte receipts bind the existing GitHub repository/main branch and Zenodo concept; the next release must be a new version of record 22104724, never a duplicate concept.",
        ROUTE_EVIDENCE,
        route,
    )

    original03_receipts = sorted(
        rel_path(path)
        for path in HERE.glob("ORIGINAL_03*.json")
        if path.resolve() != OUTPUT.resolve()
    )
    original03_labs: list[str] = []
    original03_backend_build_path = "qa/ORIGINAL_03_BACKEND_BUILD.json"
    if root_path(original03_backend_build_path).is_file():
        original03_build = load_json(original03_backend_build_path)
        original03_labs = [
            item["path"]
            for item in original03_build.get("inputs", [])
            if str(item.get("path", "")).startswith("labs/original-03/")
        ]
    integrated_qa_receipts = sorted(
        rel_path(path)
        for path in HERE.glob("*.json")
        if path.resolve() != OUTPUT.resolve()
        and "integrated" in path.name.casefold()
    )
    source_paths = [MASTER] + [
        item["path"] for item in build.get("inputs", []) if root_path(item["path"]).is_file()
    ]
    deliverable_paths = [
        pdf_relative,
        "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html",
        "output/epub/D90-O015-optimisasi-lanjut-analisis-konveks-id.epub",
    ]
    privacy_candidate_paths = unique_existing(
        [
            "README.md",
            "RIGHTS.md",
            "PROVENANCE.md",
            "00_control/SOURCE_AUTHORITY.json",
            "00_control/COMPONENT_RIGHTS.csv",
            "00_control/COVERAGE_OVERLAP.md",
            "00_control/ADVERSE_LEDGER.jsonl",
            *deliverable_paths,
            *source_paths,
            *original03_labs,
            "backend/backend_schema.json",
            "backend/records.jsonl",
            "backend/records.csv",
            *integrated_qa_receipts,
            *original03_receipts,
            "release/github/2026-08-26-original-02/github-public-readback-original-02.json",
            "release/zenodo/2026-08-26-original-02/zenodo-public-readback-original-02.json",
            "release/zenodo/2026-08-26-original-02/zenodo-privacy-readback-original-02.json",
            "release/zenodo/2026-08-26-original-02/zenodo-privacy-closure-original-02.json",
        ]
    )
    privacy = scan_privacy(privacy_candidate_paths)
    add_check(
        checks,
        "candidate_privacy_and_credential_scan",
        privacy["result"],
        "No user-profile locator, credential value, token value, credential-bearing query, or credential-file locator was found in the bounded candidate deliverables/source/labs/backend/QA/public receipts."
        if privacy["result"] == "pass"
        else "The bounded candidate privacy scan found a sensitive locator/value or could not scan a candidate.",
        privacy_candidate_paths,
        {
            key: value
            for key, value in privacy.items()
            if key not in {"files"}
        },
    )

    zenodo_additions = [
        {
            "order": 1,
            "filename": "D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf",
            "source_path": pdf_relative,
            "role": "default_preview_and_fixed_layout_reader",
            "current": pdf_identity,
        },
        {
            "order": 2,
            "filename": "D90-O015-optimisasi-lanjut-analisis-konveks-id.html",
            "source_path": "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html",
            "role": "primary_reflow_reader",
            "current": identity(
                "output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html"
            ),
        },
        {
            "order": 3,
            "filename": "D90-O015-optimisasi-lanjut-analisis-konveks-id.epub",
            "source_path": "output/epub/D90-O015-optimisasi-lanjut-analisis-konveks-id.epub",
            "role": "portable_reflow_reader",
            "current": identity(
                "output/epub/D90-O015-optimisasi-lanjut-analisis-konveks-id.epub"
            ),
        },
        {
            "order": 4,
            "filename": "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_INTEGRATED_RELEASE_2026.08.28.zip",
            "source_path": None,
            "role": "compact_source_labs_backend_qa_bundle",
            "current": {"exists": False},
        },
        {
            "order": 5,
            "filename": "backend-records-2026.08.28-integrated.jsonl",
            "source_path": "backend/records.jsonl",
            "role": "current_machine_readable_backend",
            "current": current_backend["jsonl"],
        },
        {
            "order": 6,
            "filename": "backend-records-2026.08.28-integrated.csv",
            "source_path": "backend/records.csv",
            "role": "current_tabular_backend",
            "current": current_backend["csv"],
        },
        {
            "order": 7,
            "filename": "RIGHTS_AND_PROVENANCE_INTEGRATED.md",
            "source_path": None,
            "role": "exact_component_rights_source_change_model_nonendorsement_note",
            "current": {"exists": False},
        },
        {
            "order": 8,
            "filename": "release-manifest-integrated-zenodo.json",
            "source_path": None,
            "role": "exact_release_inventory_and_inherited_dispositions",
            "current": {"exists": False},
        },
        {
            "order": 9,
            "filename": "SHA256SUMS-integrated",
            "source_path": None,
            "role": "release_checksums",
            "current": {"exists": False},
        },
    ]
    omitted_from_new_version_only = [
        "release-manifest-mit-l03.json",
        "release-manifest-mit-l04-l05.json",
        "release-manifest-mit-l06.json",
        "release-manifest-mit-l07.json",
        "release-manifest-mit-l08.json",
        "release-manifest-mit-l09.json",
        "release-manifest-mit-l10.json",
        "release-manifest-mit-l11.json",
    ]
    parent_filenames = {
        str(item.get("filename"))
        for item in privacy_receipt.get("files", [])
        if isinstance(item, dict) and item.get("filename")
    }
    addition_filenames = [item["filename"] for item in zenodo_additions]
    parent_file_count = int(privacy_receipt.get("file_count", len(parent_filenames)))
    expected_new_version_file_count = (
        parent_file_count - len(omitted_from_new_version_only) + len(addition_filenames)
    )
    inherited_file_policy_ok = (
        parent_file_count == 99
        and set(omitted_from_new_version_only).issubset(parent_filenames)
        and not (set(addition_filenames) & parent_filenames)
        and expected_new_version_file_count == 100
        and all(
            not name.startswith(("D90-", "LICENSE", "RIGHTS", "README"))
            for name in omitted_from_new_version_only
        )
    )
    add_check(
        checks,
        "zenodo_inherited_file_policy",
        "pass" if inherited_file_policy_ok else "fail",
        "The 99-file parent inventory can preserve every reader/license/rights file, omit only eight redundant historical manifests from the new version, and add nine integrated files for an exact 100-file version.",
        [
            "release/zenodo/2026-08-26-original-02/zenodo-privacy-readback-original-02.json"
        ],
        {
            "parent_file_count": parent_file_count,
            "all_omissions_exist_in_parent": set(
                omitted_from_new_version_only
            ).issubset(parent_filenames),
            "addition_name_collisions": sorted(
                set(addition_filenames) & parent_filenames
            ),
            "expected_new_version_file_count": expected_new_version_file_count,
        },
    )
    release_file_plan = {
        "status": "conditional_after_release_blockers_resolved",
        "reader_first": True,
        "zenodo_additions_in_order": zenodo_additions,
        "parent_file_count": parent_file_count,
        "inherited_policy": {
            "preserve_all_reader_license_and_rights_files": True,
            "omit_from_new_version_only": omitted_from_new_version_only,
            "omission_reason": "Eight redundant historical MIT per-version manifests remain immutable and downloadable in earlier concept versions; omitting only these eight allows nine integrated additions within the 100-file cap.",
            "historical_public_bytes_remain_available": True,
            "inherited_unchanged_count": parent_file_count
            - len(omitted_from_new_version_only),
            "addition_count": len(addition_filenames),
            "expected_new_version_file_count": expected_new_version_file_count,
        },
        "github_reader_first_commit_paths": unique_existing(
            [
                *deliverable_paths,
                MASTER,
                *[item["path"] for item in build.get("inputs", [])],
                *original03_labs,
                "README.md",
                "RIGHTS.md",
                "PROVENANCE.md",
                "00_control/SOURCE_AUTHORITY.json",
                "00_control/COMPONENT_RIGHTS.csv",
                "00_control/COVERAGE_OVERLAP.md",
                "00_control/ADVERSE_LEDGER.jsonl",
                "backend/backend_schema.json",
                "backend/records.jsonl",
                "backend/records.csv",
                *integrated_qa_receipts,
                *original03_receipts,
                "qa/verify_integrated_rights_release.py",
                "qa/INTEGRATED_RIGHTS_RELEASE_QA.json",
            ]
        ),
        "required_generated_files_not_created_by_this_audit": [
            "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_INTEGRATED_RELEASE_2026.08.28.zip",
            "RIGHTS_AND_PROVENANCE_INTEGRATED.md",
            "release-manifest-integrated-zenodo.json",
            "SHA256SUMS-integrated",
        ],
    }

    description = (
        "<p>Edisi terintegrasi Bahasa Indonesia untuk D90, <em>Optimisasi Lanjut dan Analisis Konveks</em>. "
        "Tulang punggung adalah terjemahan lengkap prakata dan Bab 1–9 Andreas Habring, arXiv:2607.11664v1, "
        "berdasarkan CC BY 4.0.</p>"
        "<p>Suplemen Becker memakai hanya commit 98ed6930084c435ba0f675f7646ced1f2fd8729e dari catatan Stephen Becker "
        "yang diketik Mitchell Krock, berdasarkan Lisensi MIT: Becker-01 baris 1263–1321, 1398–1405, 1414–1499, "
        "1652–1726, dan 1731–1743; Becker-02 baris 2750–2797; Becker-03 baris 2971–2988. Rentang LP pada "
        "1322–1397, 1406–1413, dan 1727–1730 serta materi bersebelahan tetap dikecualikan. Lisensi MIT berlaku "
        "pada donor Becker; terjemahan, koreksi, penghubung, latihan, petunjuk, dan solusi yang ditulis mandiri "
        "berlisensi CC BY-SA 4.0.</p>"
        "<p>Original-01, Original-02, dan Original-03—termasuk asesmen kumulatif, rubrik pembuktian, solusi, "
        "laboratorium, dan capstone—merupakan lapisan mandiri CC BY-SA 4.0. MIT OpenCourseWare 6.253, Clément "
        "Royer, dan Penn State tetap pembaca pendamping terpisah dengan hak masing-masing dan tidak dimasukkan "
        "ke buku terintegrasi. Materi O018 tentang LP/MIP, algoritma simpleks/tableau, sensitivitas LP, dan "
        "optimisasi jaringan tetap di luar cakupan.</p>"
        f"<p>Perubahan dan koreksi diungkapkan dalam ledger edisi. Bantuan produksi dan QA: {MODEL}, atas "
        "instruksi pengguna repositori. Sistem bukan penulis sumber, pemberi lisensi, atau wakil institusi. "
        "Edisi ini tidak menyiratkan tinjauan, persetujuan, sponsor, atau dukungan oleh penulis maupun institusi "
        "sumber. Tidak ada lisensi menyeluruh untuk rekaman campuran; hak berlaku per berkas dan hubungan sumber.</p>"
        "<p>PDF adalah permukaan pratinjau tetap; HTML dan EPUB adalah permukaan reflow pilihan. Berkas warisan "
        "pada konsep Zenodo mempertahankan hak masing-masing dan delapan manifest historis yang tidak diulang "
        "pada versi ini tetap tersedia pada versi konsep terdahulu.</p>"
    )
    zenodo_metadata_payload = {
        "access": {"record": "public", "files": "public"},
        "files": {
            "enabled": True,
            "default_preview": "D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf",
        },
        "metadata": {
            "title": "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia (id-ID): Edisi Terintegrasi D90",
            "publication_date": "2026-08-28",
            "publisher": "Zenodo",
            "version": "d90-integrated-2026.08.28",
            "resource_type": {"id": "publication-book"},
            "languages": [{"id": "ind"}],
            "description": description,
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Habring",
                        "given_name": "Andreas",
                        "name": "Habring, Andreas",
                        "type": "personal",
                    }
                },
                {
                    "person_or_org": {
                        "family_name": "Becker",
                        "given_name": "Stephen",
                        "name": "Becker, Stephen",
                        "type": "personal",
                    }
                },
            ],
            "contributors": [
                {
                    "person_or_org": {
                        "family_name": "Krock",
                        "given_name": "Mitchell",
                        "name": "Krock, Mitchell",
                        "type": "personal",
                    },
                    "role": {"id": "other"},
                },
                {
                    "person_or_org": {"name": "TTP", "type": "organizational"},
                    "role": {"id": "other"},
                },
            ],
            "rights": [
                {
                    "title": {
                        "en": "Mixed-license record — rights apply per file and source relation"
                    },
                    "description": {
                        "en": "No blanket license is asserted; consult the integrated rights/provenance note and component ledger."
                    },
                    "link": "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id/blob/main/00_control/COMPONENT_RIGHTS.csv",
                },
                {"id": "cc-by-4.0"},
                {"id": "cc-by-sa-4.0"},
                {
                    "title": {"en": "MIT License — bounded Becker source components only"},
                    "description": {
                        "en": "Applies only to the exact admitted Becker donor ranges; independent translation and correction wording are separate."
                    },
                    "link": "https://opensource.org/license/mit",
                },
                {
                    "title": {"en": "Inherited companion rights remain per component"},
                    "description": {
                        "en": "Inherited MIT OCW, Penn, and Royer files remain separately licensed and are not part of the integrated book."
                    },
                    "link": "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id/blob/main/RIGHTS.md",
                },
            ],
            "related_identifiers": [
                {
                    "identifier": "10.48550/arXiv.2607.11664",
                    "relation_type": {"id": "isderivedfrom"},
                    "resource_type": {"id": "publication-book"},
                    "scheme": "doi",
                },
                {
                    "identifier": "https://github.com/stephenbeckr/convex-optimization-class/tree/98ed6930084c435ba0f675f7646ced1f2fd8729e",
                    "relation_type": {"id": "isderivedfrom"},
                    "resource_type": {"id": "software"},
                    "scheme": "url",
                },
                {
                    "identifier": GITHUB_REPOSITORY,
                    "relation_type": {"id": "isdocumentedby"},
                    "resource_type": {"id": "software"},
                    "scheme": "url",
                },
            ],
            "subjects": [
                {"subject": "Bahasa Indonesia"},
                {"subject": "id-ID"},
                {"subject": "convex analysis"},
                {"subject": "convex optimization"},
                {"subject": "nonsmooth optimization"},
                {"subject": "stochastic optimization"},
                {"subject": "variational inequalities"},
                {"subject": "monotone operators"},
                {"subject": "operator splitting"},
                {"subject": "optimal transport"},
                {"subject": "open educational resources"},
            ],
        },
    }
    recommended_title = zenodo_metadata_payload["metadata"]["title"]
    recommended_creators = json.dumps(
        zenodo_metadata_payload["metadata"]["creators"], ensure_ascii=False
    )
    if "TTP" in recommended_title or "TTP" in recommended_creators:
        raise RuntimeError("recommended metadata violates the no-TTP title/lead boundary")

    failed_checks = [item["check_id"] for item in checks if item["result"] == "fail"]
    overall = "pass" if not failed_checks and not contradictions else "fail"
    report: dict[str, Any] = {
        "schema": "o015-integrated-rights-release-qa-v1",
        "audit_date": date.today().isoformat(),
        "result": overall,
        "release_ready": overall == "pass",
        "publication_recommended_now": overall == "pass",
        "network_accessed": False,
        "git_accessed": False,
        "credential_accessed": False,
        "scope": "D90 integrated rights/provenance/nonoverlap/privacy/release-route audit",
        "checks": checks,
        "failed_checks": failed_checks,
        "contradictions": contradictions,
        "privacy": privacy,
        "route": route,
        "recommended_release_file_plan": release_file_plan,
        "recommended_zenodo_metadata_payload": zenodo_metadata_payload,
        "metadata_payload_use_gate": "Use only after every release-blocking contradiction is deterministically reconciled and this verifier returns pass.",
        "evidence_identities": [identity(relative) for relative in CORE_EVIDENCE + ROUTE_EVIDENCE]
        + [identity("qa/verify_integrated_rights_release.py")],
    }

    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if PROFILE_LOCATOR.search(serialized):
        raise RuntimeError("refusing to write a receipt containing a user-profile locator")
    for pattern in CREDENTIAL_PATTERNS.values():
        if pattern.search(serialized.encode("utf-8")):
            raise RuntimeError("refusing to write a receipt containing credential material")
    temporary = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    os.replace(temporary, OUTPUT)
    print(
        json.dumps(
            {
                "result": overall,
                "report": rel_path(OUTPUT),
                "failed_checks": failed_checks,
                "contradiction_count": len(contradictions),
                "privacy_result": privacy["result"],
                "route_result": route["result"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        failure = {
            "schema": "o015-integrated-rights-release-qa-v1",
            "result": "fail",
            "release_ready": False,
            "publication_recommended_now": False,
            "network_accessed": False,
            "git_accessed": False,
            "credential_accessed": False,
            "error_type": type(error).__name__,
        }
        serialized_failure = json.dumps(
            failure, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"
        temporary = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
        temporary.write_text(serialized_failure, encoding="utf-8", newline="\n")
        os.replace(temporary, OUTPUT)
        print(serialized_failure, file=sys.stderr)
        raise SystemExit(2)
