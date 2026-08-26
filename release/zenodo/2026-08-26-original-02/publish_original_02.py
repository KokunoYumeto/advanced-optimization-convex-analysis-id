#!/usr/bin/env python3
"""Fail-closed Zenodo version publisher for the O015 Original-02 checkpoint.

This program is bound to the existing O015 Zenodo concept and the published
Original-01 parent.  It never creates a new concept, never stores credential
material, inherits parent bytes by Zenodo's version endpoint, and accepts only
the exact 99-file namespace frozen here.

The checked-in ``release-inputs-original-02.template.json`` is intentionally
not executable release authority.  A release operator must create
``release-inputs-original-02.json`` only after all artifacts and PASS receipts
exist, set ``frozen`` to true, and enter their exact byte/SHA-256 identities.
Every state-changing action calls the same local gate before contacting Zenodo.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
import truststore

truststore.inject_into_ssl()

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
API = "https://zenodo.org/api"
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"

PARENT_RECORD_ID = "22103674"
PARENT_RECORD_DOI = "10.5281/zenodo.22103674"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.26-original-02-variational-inequalities-maximal-monotone-resolvents-splitting"
TITLE = "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia (id-ID): Tranche Asli 2; Kursus Parsial"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
PRIMARY_PDF = "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.pdf"

PARENT_READBACK = HERE.parent / "2026-08-26-original-01" / "zenodo-public-readback-original-01.json"
INPUT_TEMPLATE_PATH = HERE / "release-inputs-original-02.template.json"
INPUT_PATH = HERE / "release-inputs-original-02.json"
METADATA_TEMPLATE_PATH = HERE / "metadata-original-02.template.json"
RIGHTS_TEMPLATE_PATH = HERE / "RIGHTS_AND_PROVENANCE_ORIGINAL_02.template.md"
MANIFEST_PATH = HERE / "release-manifest-original-02-zenodo.json"
SUMS_PATH = HERE / "SHA256SUMS-original-02"
STATE_PATH = HERE / "zenodo-draft-original-02.json"
READBACK_PATH = HERE / "zenodo-public-readback-original-02.json"
CLOSURE_PATH = HERE / "zenodo-draft-closure-original-02.json"

CORE_NAMES = {
    PRIMARY_PDF,
    "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html",
    "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub",
    "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_ORIGINAL_02_2026.08.26.zip",
    "backend-records-2026.08.26-original-02.jsonl",
    "backend-records-2026.08.26-original-02.csv",
    "RIGHTS_AND_PROVENANCE_ORIGINAL_02.md",
}

REQUIRED_RECEIPTS = {
    "pdf_build": "qa/ORIGINAL_02_PDF_BUILD.json",
    "pdf_visual_qa": "qa/ORIGINAL_02_PDF_VISUAL_QA.json",
    "html_build": "qa/ORIGINAL_02_HTML_BUILD.json",
    "html_browser_qa": "qa/ORIGINAL_02_HTML_BROWSER_QA.json",
    "epub_build": "qa/ORIGINAL_02_EPUB_BUILD.json",
    "epub_conformance": "qa/ORIGINAL_02_EPUB_CONFORMANCE.json",
    "mathematics": "qa/ORIGINAL_02_MATH_VALIDATION.json",
    "rights_and_nonoverlap": "qa/ORIGINAL_02_RIGHTS_NONOVERLAP.json",
    "backend_build": "qa/ORIGINAL_02_BACKEND_BUILD.json",
    "backend_validation": "qa/ORIGINAL_02_BACKEND_VALIDATION.json",
    "independent_rereview": "qa/ORIGINAL_02_INDEPENDENT_REREVIEW.json",
    "package_local_verification": "release/original-02/2026-08-26/local-verification-original-02.json",
}

# Parent 99 - these exact 9 + Original-02's exact 9 = next version 99.
REPLACED_PARENT_FILES = {
    "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_BECKER_03_2026.08.25.zip",
    "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_ORIGINAL_01_2026.08.26.zip",
    "RIGHTS_AND_PROVENANCE_ORIGINAL_01.md",
    "SHA256SUMS-becker-03",
    "SHA256SUMS-original-01",
    "backend-records-2026.08.26-original-01.csv",
    "backend-records-2026.08.26-original-01.jsonl",
    "release-manifest-becker-03-zenodo.json",
    "release-manifest-original-01-zenodo.json",
}

PLACEHOLDERS = {
    "{{ADDED_BACKEND_RECORDS}}": "added_backend_records",
    "{{BACKEND_RECORDS}}": "backend_records",
    "{{COMPLETE_SOLUTIONS}}": "complete_solutions",
    "{{EXERCISES}}": "exercises",
    "{{HINTS}}": "hints",
    "{{MATH_CHECKS}}": "math_checks",
    "{{PDF_PAGES}}": "pdf_pages",
    "{{PROTECTED_BACKEND_RECORDS}}": "protected_backend_records",
    "{{SEGMENTS}}": "segments",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": sha_file(path)}


def repository_locator(path: Path) -> str:
    """Return a stable repository-relative locator without a local username."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as error:
        raise RuntimeError(f"release evidence path is outside the repository: {path.name}") from error


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def root_path(relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise RuntimeError(f"release path must be repository-relative: {relative!r}")
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise RuntimeError(f"release path escapes repository root: {relative!r}") from error
    return path


def status_value(value: object) -> str | None:
    if isinstance(value, str):
        return value.casefold()
    return None


def receipt_passes(receipt: dict) -> bool:
    for key in ("result", "status", "overall_result", "overall_status"):
        if status_value(receipt.get(key)) in {"pass", "passed", "ok", "success"}:
            return True
    return False


def priority_counts(value: object, found: dict[str, int]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            folded = str(key).casefold().replace("_", "").replace("-", "")
            if folded in {"p1", "p2", "p3"} and isinstance(child, int):
                found[folded.upper()] = child
            priority_counts(child, found)
    elif isinstance(value, list):
        for child in value:
            priority_counts(child, found)


def parent_inventory() -> dict[str, dict[str, object]]:
    receipt = read_json(PARENT_READBACK)
    if (
        receipt.get("result") != "pass"
        or str(receipt.get("record_id")) != PARENT_RECORD_ID
        or receipt.get("record_doi") != PARENT_RECORD_DOI
        or str(receipt.get("concept_id")) != CONCEPT_ID
        or receipt.get("concept_doi") != CONCEPT_DOI
        or receipt.get("file_count") != 99
    ):
        raise RuntimeError("frozen Original-01 receipt does not bind the required parent")
    files = receipt.get("files")
    if not isinstance(files, list):
        raise RuntimeError("parent receipt lacks a file list")
    result = {
        item["filename"]: {"bytes": item["bytes"], "sha256": item["sha256"]}
        for item in files
    }
    if len(result) != 99 or len(files) != 99:
        raise RuntimeError("parent receipt namespace is not exactly 99 unique files")
    if not REPLACED_PARENT_FILES.issubset(result):
        missing = sorted(REPLACED_PARENT_FILES - set(result))
        raise RuntimeError(f"parent receipt lacks replacement targets: {missing}")
    return result


def inherited_inventory() -> dict[str, dict[str, object]]:
    result = {
        name: value
        for name, value in parent_inventory().items()
        if name not in REPLACED_PARENT_FILES
    }
    if len(result) != 90:
        raise RuntimeError(f"inherited inventory is {len(result)}, expected 90")
    return result


def template_check() -> dict:
    template = read_json(INPUT_TEMPLATE_PATH)
    if template.get("schema") != "o015-zenodo-original-02-release-inputs-v1":
        raise RuntimeError("release-input template schema mismatch")
    if template.get("frozen") is not False:
        raise RuntimeError("checked-in release-input template must remain unfrozen")
    artifacts = template.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != CORE_NAMES:
        raise RuntimeError("release-input template artifact namespace mismatch")
    receipts = template.get("receipts")
    if not isinstance(receipts, list):
        raise RuntimeError("release-input template lacks receipts")
    by_label = {item.get("label"): item for item in receipts if isinstance(item, dict)}
    if set(by_label) != set(REQUIRED_RECEIPTS) or len(by_label) != len(receipts):
        raise RuntimeError("release-input template receipt labels mismatch")
    for label, relative in REQUIRED_RECEIPTS.items():
        if by_label[label].get("path") != relative:
            raise RuntimeError(f"receipt path mismatch for {label}")
    raw_metadata = METADATA_TEMPLATE_PATH.read_text(encoding="utf-8")
    metadata_template = json.loads(raw_metadata)
    if not isinstance(metadata_template, dict):
        raise RuntimeError("metadata template must be an object")
    for placeholder in PLACEHOLDERS:
        if raw_metadata.count(placeholder) != 1:
            raise RuntimeError(f"metadata placeholder count is not one: {placeholder}")
    metadata = metadata_template.get("metadata", {})
    serialized = json.dumps(metadata, ensure_ascii=False)
    if metadata.get("title") != TITLE or metadata.get("version") != VERSION:
        raise RuntimeError("metadata template title/version mismatch")
    if "TTP" in str(metadata.get("title", "")) or "TTP" in str(metadata.get("description", "")):
        raise RuntimeError("organization label appears in title or description")
    if serialized.count("TTP") != 1 or "Translation and Transcription Project" in serialized:
        raise RuntimeError("metadata template organization policy failed")
    if serialized.count(MODEL) != 1:
        raise RuntimeError("metadata template model-provenance policy failed")
    rights = RIGHTS_TEMPLATE_PATH.read_text(encoding="utf-8")
    if "TTP" in rights or "Translation and Transcription Project" in rights:
        raise RuntimeError("rights template contains an organization label")
    for marker in ("CC BY-SA 4.0", "CC BY 4.0", "Tidak ada lisensi menyeluruh"):
        if marker.casefold() not in rights.casefold():
            raise RuntimeError(f"rights template lacks {marker!r}")
    parent = parent_inventory()
    inherited = inherited_inventory()
    return {
        "result": "pass",
        "network_contact": False,
        "publication_attempted": False,
        "parent_files": len(parent),
        "removed_parent_files": sorted(REPLACED_PARENT_FILES),
        "retained_parent_files": len(inherited),
        "planned_additions": 9,
        "expected_public_files": len(inherited) + 9,
        "release_input_is_intentionally_unfrozen": True,
        "metadata_template": identity(METADATA_TEMPLATE_PATH),
        "rights_template": identity(RIGHTS_TEMPLATE_PATH),
        "release_input_template": identity(INPUT_TEMPLATE_PATH),
    }


def frozen_inputs() -> dict:
    if not INPUT_PATH.is_file():
        raise RuntimeError(
            "release-input freeze is absent; copy the template only after all final artifacts "
            "and PASS receipts exist, then bind every exact identity"
        )
    value = read_json(INPUT_PATH)
    if (
        value.get("schema") != "o015-zenodo-original-02-release-inputs-v1"
        or value.get("frozen") is not True
        or value.get("publication_status") != "partial"
    ):
        raise RuntimeError("release-input freeze is not valid, true, and partial")
    facts = value.get("facts")
    if not isinstance(facts, dict) or set(facts) != set(PLACEHOLDERS.values()):
        raise RuntimeError("release facts do not exactly match the metadata contract")
    if any(not isinstance(facts[key], int) or facts[key] < 0 for key in facts):
        raise RuntimeError("all frozen release facts must be non-negative integers")
    if facts["protected_backend_records"] != 3943:
        raise RuntimeError("protected backend prefix is not Original-01's 3,943 records")
    if facts["added_backend_records"] != facts["backend_records"] - facts["protected_backend_records"]:
        raise RuntimeError("backend count arithmetic mismatch")
    if facts["exercises"] != 6 or facts["hints"] != 6 or facts["complete_solutions"] != 6 or facts["segments"] != 8:
        raise RuntimeError("frozen Original-02 topology facts mismatch")

    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != CORE_NAMES:
        raise RuntimeError("frozen artifact namespace mismatch")
    for name, item in artifacts.items():
        if not isinstance(item, dict):
            raise RuntimeError(f"invalid artifact entry: {name}")
        path = root_path(str(item.get("path", "")))
        expected_bytes = item.get("bytes")
        expected_sha = item.get("sha256")
        if not isinstance(expected_bytes, int) or expected_bytes <= 0 or not re.fullmatch(r"[0-9a-f]{64}", str(expected_sha)):
            raise RuntimeError(f"artifact identity is not frozen: {name}")
        if not path.is_file() or identity(path) != {"bytes": expected_bytes, "sha256": expected_sha}:
            raise RuntimeError(f"artifact identity mismatch: {name}")

    receipts = value.get("receipts")
    if not isinstance(receipts, list):
        raise RuntimeError("frozen receipt list missing")
    by_label = {item.get("label"): item for item in receipts if isinstance(item, dict)}
    if set(by_label) != set(REQUIRED_RECEIPTS) or len(by_label) != len(receipts):
        raise RuntimeError("frozen receipt labels mismatch")
    receipt_identities: dict[str, dict[str, object]] = {}
    rereview: dict | None = None
    for label, relative in REQUIRED_RECEIPTS.items():
        item = by_label[label]
        if item.get("path") != relative or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256"))):
            raise RuntimeError(f"receipt path/hash is not frozen: {label}")
        path = root_path(relative)
        if not path.is_file() or sha_file(path) != item["sha256"]:
            raise RuntimeError(f"receipt identity mismatch: {label}")
        receipt = read_json(path)
        if not receipt_passes(receipt):
            raise RuntimeError(f"receipt is not PASS: {label}")
        if label == "independent_rereview":
            rereview = receipt
        receipt_identities[label] = {"path": relative, **identity(path)}
    assert rereview is not None
    counts: dict[str, int] = {}
    priority_counts(rereview, counts)
    if counts != {"P1": 0, "P2": 0, "P3": 0}:
        raise RuntimeError(f"independent rereview is not explicitly P1=P2=P3=0: {counts}")

    jsonl_path = root_path(artifacts["backend-records-2026.08.26-original-02.jsonl"]["path"])
    csv_path = root_path(artifacts["backend-records-2026.08.26-original-02.csv"]["path"])
    with jsonl_path.open("r", encoding="utf-8") as stream:
        jsonl_records = sum(1 for line in stream if line.strip())
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        csv_records = max(sum(1 for _ in csv.reader(stream)) - 1, 0)
    if jsonl_records != facts["backend_records"] or csv_records != facts["backend_records"]:
        raise RuntimeError(
            f"backend physical counts mismatch: JSONL={jsonl_records}, CSV={csv_records}, "
            f"frozen={facts['backend_records']}"
        )
    return {**value, "_receipt_identities": receipt_identities}


def artifact_paths(inputs: dict) -> dict[str, Path]:
    return {
        name: root_path(item["path"])
        for name, item in inputs["artifacts"].items()
    }


def render_metadata(inputs: dict) -> dict:
    raw = METADATA_TEMPLATE_PATH.read_text(encoding="utf-8")
    for placeholder, fact in PLACEHOLDERS.items():
        raw = raw.replace(placeholder, str(inputs["facts"][fact]))
    if "{{" in raw or "}}" in raw:
        raise RuntimeError("unresolved metadata placeholder")
    payload = json.loads(raw)
    validate_metadata(payload.get("metadata", {}))
    if payload.get("files", {}).get("default_preview") != PRIMARY_PDF:
        raise RuntimeError("metadata default preview mismatch")
    return payload


def validate_metadata(metadata: dict) -> None:
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = str(metadata.get("title", ""))
    description = str(metadata.get("description", ""))
    if title != TITLE or metadata.get("version") != VERSION:
        raise RuntimeError("metadata title/version mismatch")
    if "TTP" in title or "TTP" in description or "Translation and Transcription Project" in serialized:
        raise RuntimeError("organization label appears outside its permitted contributor entry")
    if serialized.count("TTP") != 1:
        raise RuntimeError("metadata must contain exactly one organization-label mention")
    # The editable payload uses the current Records API shape, while Zenodo's
    # response normalizes contributors to the legacy flat shape
    # {"name": ..., "type": "Other"}.  Accept exactly those two witnessed
    # representations; the surrounding serialized-count checks still prove
    # that the organization label occurs once and nowhere in title/prose.
    organizations = [
        item
        for item in metadata.get("contributors", [])
        if (
            item.get("person_or_org", {}).get("type") == "organizational"
            and item.get("person_or_org", {}).get("name") == "TTP"
        )
        or (item.get("name") == "TTP" and item.get("type") == "Other")
    ]
    if len(organizations) != 1:
        raise RuntimeError("metadata lacks exactly one required organizational contributor")
    if serialized.count(MODEL) != 1:
        raise RuntimeError("metadata must contain the exact model marker once")
    for marker in (
        "parsial",
        "CC BY-SA 4.0",
        "CC BY 4.0",
        "P1=P2=P3=0",
        "Tidak ada lisensi menyeluruh",
    ):
        if marker.casefold() not in description.casefold():
            raise RuntimeError(f"metadata description lacks {marker!r}")


def addition_paths(inputs: dict) -> dict[str, Path]:
    return {
        **artifact_paths(inputs),
        MANIFEST_PATH.name: MANIFEST_PATH,
        SUMS_PATH.name: SUMS_PATH,
    }


def expected_inventory(inputs: dict) -> dict[str, dict[str, object]]:
    return {
        **inherited_inventory(),
        **{name: identity(path) for name, path in addition_paths(inputs).items()},
    }


def validate_rights(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "TTP" in text or "Translation and Transcription Project" in text:
        raise RuntimeError("final rights note contains an organization label")
    for marker in ("CC BY-SA 4.0", "CC BY 4.0"):
        if marker not in text:
            raise RuntimeError(f"final rights note lacks {marker!r}")
    lowered = text.casefold()
    if not any(
        marker in lowered
        for marker in (
            "tidak ada lisensi menyeluruh",
            "no blanket license",
            "kewajiban itu terpisah; satu lisensi tidak menghapus lisensi lainnya",
        )
    ):
        raise RuntimeError("final rights note lacks an explicit mixed-rights separation statement")


def build_local() -> dict:
    template_check()
    inputs = frozen_inputs()
    metadata = render_metadata(inputs)
    paths = artifact_paths(inputs)
    validate_rights(paths["RIGHTS_AND_PROVENANCE_ORIGINAL_02.md"])
    parent = parent_inventory()
    inherited = inherited_inventory()
    additions = {name: identity(path) for name, path in paths.items()}
    manifest = {
        "schema": "o015-zenodo-original-02-release-manifest-v1",
        "title": metadata["metadata"]["title"],
        "publication_date": "2026-08-26",
        "status": "partial",
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "parent_public_readback": {
            "path": repository_locator(PARENT_READBACK),
            **identity(PARENT_READBACK),
        },
        "release_input_freeze": {"path": repository_locator(INPUT_PATH), **identity(INPUT_PATH)},
        "metadata_template": {"path": repository_locator(METADATA_TEMPLATE_PATH), **identity(METADATA_TEMPLATE_PATH)},
        "rights_template": {"path": repository_locator(RIGHTS_TEMPLATE_PATH), **identity(RIGHTS_TEMPLATE_PATH)},
        "source": {
            "canonical_spine": "Andreas Habring arXiv:2607.11664v1",
            "source_tar_sha256": "d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748",
            "license": "CC BY 4.0",
        },
        "boundary": {
            "unit_id": "d90.orig.v1.tr02.unit",
            "topic": "ketaksamaan variasional, operator monoton maksimal, resolven, dan pemisahan operator",
            "segments": inputs["facts"]["segments"],
            "exercises": inputs["facts"]["exercises"],
            "hints": inputs["facts"]["hints"],
            "complete_solutions": inputs["facts"]["complete_solutions"],
            "course_status": "partial",
        },
        "backend": {
            "protected_records": inputs["facts"]["protected_backend_records"],
            "added_records": inputs["facts"]["added_backend_records"],
            "records": inputs["facts"]["backend_records"],
            "jsonl_sha256": additions["backend-records-2026.08.26-original-02.jsonl"]["sha256"],
            "csv_sha256": additions["backend-records-2026.08.26-original-02.csv"]["sha256"],
        },
        "rights": {
            "new_substantive_layer": "CC BY-SA 4.0",
            "Habring_scaffold": "CC BY 4.0 submission-level evidence",
            "component_specific": True,
            "blanket_license_claim": False,
        },
        "qa_receipts": inputs["_receipt_identities"],
        "replaced_parent_files": sorted(REPLACED_PARENT_FILES),
        "retained_parent_file_count": len(inherited),
        "additions_before_manifest_and_sums": additions,
        "expected_public_file_count": len(inherited) + len(paths) + 2,
        "model_provenance": MODEL,
        "credential_material_recorded": False,
        "upstream_contact": False,
    }
    write_json(MANIFEST_PATH, manifest)
    before_sums = {**paths, MANIFEST_PATH.name: MANIFEST_PATH}
    SUMS_PATH.write_text(
        "".join(f"{sha_file(path)}  {name}\n" for name, path in sorted(before_sums.items())),
        encoding="utf-8",
        newline="\n",
    )
    expected = expected_inventory(inputs)
    if len(parent) != 99 or len(inherited) != 90 or len(addition_paths(inputs)) != 9 or len(expected) != 99:
        raise RuntimeError(
            f"namespace arithmetic mismatch: parent={len(parent)}, inherited={len(inherited)}, "
            f"additions={len(addition_paths(inputs))}, final={len(expected)}"
        )
    return {
        "result": "pass",
        "publication_attempted": False,
        "parent_files": len(parent),
        "retained_files": len(inherited),
        "addition_files": len(addition_paths(inputs)),
        "expected_public_files": len(expected),
        "manifest": identity(MANIFEST_PATH),
        "checksums": identity(SUMS_PATH),
    }


def token() -> str:
    value = os.environ.get("ZENODO_TOKEN", "").strip()
    if len(value) >= 20:
        return value
    if not TOKEN_FILE.is_file():
        raise RuntimeError("ZENODO_TOKEN is absent and configured credential file is unavailable")
    text = TOKEN_FILE.read_text(encoding="utf-8")
    candidates: list[str] = []
    for line in text.splitlines():
        for match in re.finditer(
            r"(?i)(?:token|access[ -]?token|api[ -]?key)\s*[:=]\s*([A-Za-z0-9._-]{20,})",
            line,
        ):
            candidates.append(match.group(1))
    if not candidates:
        candidates = re.findall(r"(?<![A-Za-z0-9])[A-Za-z0-9._-]{20,}(?![A-Za-z0-9])", text)
    if not candidates:
        raise RuntimeError("no usable token found in configured credential file")
    return candidates[0]


def session(authenticated: bool = True) -> requests.Session:
    client = requests.Session()
    client.headers.update({"User-Agent": "o015-original-02-publisher/1"})
    if authenticated:
        client.headers.update({"Authorization": f"Bearer {token()}"})
    return client


def get_json(client: requests.Session, url: str, label: str, **kwargs) -> dict:
    response = None
    for attempt in range(1, 6):
        response = client.get(url, timeout=120, **kwargs)
        if response.status_code != 429 and response.status_code < 500:
            response.raise_for_status()
            value = response.json()
            if not isinstance(value, dict):
                raise RuntimeError(f"{label} returned non-object JSON")
            return value
        if attempt < 5:
            time.sleep(min(attempt * 2, 10))
    assert response is not None
    response.raise_for_status()
    raise RuntimeError(f"{label} failed")


def record_id(record: dict) -> str:
    return str(record.get("id"))


def record_doi(record: dict) -> str | None:
    return (
        record.get("pids", {}).get("doi", {}).get("identifier")
        or record.get("doi")
        or record.get("metadata", {}).get("doi")
    )


def concept_id(record: dict) -> str | None:
    parent = record.get("parent")
    if isinstance(parent, dict) and parent.get("id") is not None:
        return str(parent["id"])
    value = record.get("conceptrecid")
    return str(value) if value is not None else None


def public_entries(record: dict) -> dict[str, dict]:
    files = record.get("files")
    entries = files.get("entries", []) if isinstance(files, dict) else files
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise RuntimeError("unexpected public file inventory")
    result = {item.get("key") or item.get("filename"): item for item in entries}
    if None in result or len(result) != len(entries):
        raise RuntimeError("duplicate/missing public file keys")
    return result


def verify_parent_public() -> dict:
    record = get_json(session(False), f"{API}/records/{PARENT_RECORD_ID}", "parent")
    if (
        record_id(record) != PARENT_RECORD_ID
        or record_doi(record) != PARENT_RECORD_DOI
        or concept_id(record) != CONCEPT_ID
        or record.get("status") != "published"
    ):
        raise RuntimeError("live parent lineage mismatch")
    entries = public_entries(record)
    expected = parent_inventory()
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("live parent namespace drift")
    for name, item in entries.items():
        if item.get("size") != expected[name]["bytes"]:
            raise RuntimeError(f"live parent size drift: {name}")
    return record


def remote_file_entries(client: requests.Session, record: str) -> dict[str, dict]:
    value = get_json(client, f"{API}/records/{record}/draft/files", "draft-files")
    entries = value.get("entries", value)
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise RuntimeError("unexpected draft file response")
    result = {item.get("key"): item for item in entries}
    if None in result or len(result) != len(entries):
        raise RuntimeError("duplicate/missing draft file keys")
    return result


def save_state(record: dict) -> dict:
    identifier = record_id(record)
    if not identifier.isdigit():
        raise RuntimeError("Zenodo response lacks numeric record id")
    value = {
        "schema": "o015-zenodo-original-02-draft-v1",
        "status": record.get("status") or ("published" if record.get("is_published") else "draft"),
        "draft_id": identifier,
        "draft_doi": record_doi(record),
        "version": VERSION,
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
    }
    write_json(STATE_PATH, value)
    return value


def state() -> dict:
    value = read_json(STATE_PATH)
    if (
        value.get("schema") != "o015-zenodo-original-02-draft-v1"
        or value.get("version") != VERSION
        or value.get("parent_record_id") != PARENT_RECORD_ID
        or value.get("concept_id") != CONCEPT_ID
    ):
        raise RuntimeError("state belongs to another release")
    return value


def ensure_namespace(client: requests.Session, record: str, inputs: dict) -> dict[str, dict]:
    entries = remote_file_entries(client, record)
    parent_names = set(parent_inventory())
    inherited_names = set(inherited_inventory())
    addition_names = set(addition_paths(inputs))
    if not entries:
        response = client.post(f"{API}/records/{record}/draft/actions/files-import", timeout=300)
        response.raise_for_status()
        for _ in range(120):
            entries = remote_file_entries(client, record)
            if parent_names.issubset(entries):
                break
            time.sleep(1)
    actual = set(entries)
    if (actual - parent_names - addition_names) or (inherited_names - actual):
        raise RuntimeError("draft cannot be safely resumed before pruning")
    endpoint = f"{API}/records/{record}/draft/files"
    for name in sorted(REPLACED_PARENT_FILES & actual):
        response = client.delete(f"{endpoint}/{quote(name, safe='')}", timeout=60)
        if response.status_code not in (200, 204):
            response.raise_for_status()
    entries = remote_file_entries(client, record)
    actual = set(entries)
    if (
        (actual - inherited_names - addition_names)
        or (inherited_names - actual)
        or (actual & REPLACED_PARENT_FILES)
    ):
        raise RuntimeError("bounded parent pruning did not converge")
    return entries


def create_or_recover(client: requests.Session) -> str:
    if STATE_PATH.is_file():
        current = state()
        record = str(current["draft_id"])
        if current.get("status") == "published":
            return record
        draft = get_json(client, f"{API}/records/{record}/draft", "existing-draft")
        if record_id(draft) != record or draft.get("status") == "published":
            raise RuntimeError("saved state does not identify an editable draft")
        return record
    response = client.post(f"{API}/records/{PARENT_RECORD_ID}/versions", timeout=120)
    if response.status_code == 409:
        raise RuntimeError("an unrecorded open version draft exists; refusing to create a duplicate")
    response.raise_for_status()
    record = str(response.json().get("id"))
    if not record.isdigit() or record == PARENT_RECORD_ID:
        raise RuntimeError("version endpoint returned an unsafe record id")
    draft = get_json(client, f"{API}/records/{record}/draft", "new-draft")
    save_state(draft)
    return record


def prepare() -> dict:
    local = build_local()
    inputs = frozen_inputs()
    verify_parent_public()
    client = session(True)
    record = create_or_recover(client)
    ensure_namespace(client, record, inputs)
    response = client.put(f"{API}/records/{record}/draft", json=render_metadata(inputs), timeout=120)
    response.raise_for_status()
    updated = response.json()
    validate_metadata(updated["metadata"])
    save_state(updated)
    return {**local, "draft_id": record}


def upload_one(
    client: requests.Session,
    record: str,
    name: str,
    path: Path,
    existing: dict[str, dict],
) -> None:
    endpoint = f"{API}/records/{record}/draft/files"
    old = existing.get(name)
    expected_md5 = f"md5:{sha_file(path, 'md5')}"
    if (
        old
        and old.get("status") == "completed"
        and old.get("size") == path.stat().st_size
        and old.get("checksum") == expected_md5
    ):
        return
    if old:
        response = client.delete(f"{endpoint}/{quote(name, safe='')}", timeout=60)
        if response.status_code not in (200, 204):
            response.raise_for_status()
    client.post(endpoint, json=[{"key": name}], timeout=60).raise_for_status()
    with path.open("rb") as stream:
        client.put(
            f"{endpoint}/{quote(name, safe='')}/content",
            data=stream,
            headers={"Content-Type": "application/octet-stream"},
            timeout=600,
        ).raise_for_status()
    client.post(f"{endpoint}/{quote(name, safe='')}/commit", timeout=60).raise_for_status()


def upload() -> dict:
    local = build_local()
    inputs = frozen_inputs()
    current = state()
    if current.get("status") == "published":
        raise RuntimeError("release is already published")
    client = session(True)
    record = str(current["draft_id"])
    draft = get_json(client, f"{API}/records/{record}/draft", "draft")
    validate_metadata(draft["metadata"])
    existing = ensure_namespace(client, record, inputs)
    additions = addition_paths(inputs)
    order = [
        PRIMARY_PDF,
        "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.html",
        "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-pemisahan-id.epub",
        "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_ORIGINAL_02_2026.08.26.zip",
        "backend-records-2026.08.26-original-02.jsonl",
        "backend-records-2026.08.26-original-02.csv",
        "RIGHTS_AND_PROVENANCE_ORIGINAL_02.md",
        MANIFEST_PATH.name,
        SUMS_PATH.name,
    ]
    if set(order) != set(additions) or len(order) != 9:
        raise RuntimeError("upload order does not match exact addition namespace")
    for name in order:
        upload_one(client, record, name, additions[name], existing)
        existing = remote_file_entries(client, record)
    response = client.put(f"{API}/records/{record}/draft", json=render_metadata(inputs), timeout=120)
    response.raise_for_status()
    validate_metadata(response.json()["metadata"])
    return {**local, "result": "pass", "draft_id": record, "file_count": 99}


def validate_draft() -> dict:
    build_local()
    inputs = frozen_inputs()
    current = state()
    record = str(current["draft_id"])
    client = session(True)
    draft = get_json(client, f"{API}/records/{record}/draft", "draft")
    validate_metadata(draft["metadata"])
    entries = remote_file_entries(client, record)
    expected = expected_inventory(inputs)
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("draft namespace differs from exact 99-file plan")
    for name, path in addition_paths(inputs).items():
        item = entries[name]
        if (
            item.get("status") != "completed"
            or item.get("size") != path.stat().st_size
            or item.get("checksum") != f"md5:{sha_file(path, 'md5')}"
        ):
            raise RuntimeError(f"draft addition mismatch: {name}")
    return {"result": "pass", "draft_id": record, "file_count": 99, "all_additions_completed": True}


def publish() -> dict:
    current = state()
    record = str(current["draft_id"])
    if current.get("status") == "published":
        return readback()
    validate_draft()
    response = session(True).post(f"{API}/records/{record}/draft/actions/publish", timeout=180)
    if response.status_code not in (200, 201, 202, 409):
        response.raise_for_status()
    for attempt in range(1, 16):
        candidate = session(False).get(f"{API}/records/{record}", timeout=120)
        if candidate.status_code == 200 and candidate.json().get("status") == "published":
            published = candidate.json()
            save_state(published)
            return readback()
        if candidate.status_code not in (404, 429) and 400 <= candidate.status_code < 500:
            candidate.raise_for_status()
        if attempt < 15:
            time.sleep(min(attempt * 2, 12))
    raise RuntimeError("published record did not become anonymously visible")


def download(client: requests.Session, item: dict) -> bytes:
    url = (
        item.get("links", {}).get("content")
        or item.get("links", {}).get("download")
        or item.get("links", {}).get("self")
    )
    if not url:
        raise RuntimeError("public file lacks a content URL")
    response = None
    for attempt in range(1, 9):
        response = client.get(url, timeout=600)
        if response.status_code != 429 and response.status_code < 500:
            response.raise_for_status()
            return response.content
        if attempt < 8:
            time.sleep(min(2**attempt, 20))
    assert response is not None
    response.raise_for_status()
    raise RuntimeError("public file download retry budget exhausted")


def readback() -> dict:
    build_local()
    inputs = frozen_inputs()
    current = state()
    record = str(current["draft_id"])
    client = session(False)
    public = get_json(client, f"{API}/records/{record}", "published-record")
    if (
        record_id(public) != record
        or public.get("status") != "published"
        or concept_id(public) != CONCEPT_ID
        or record_doi(public) is None
    ):
        raise RuntimeError("public record identity/status mismatch")
    metadata = public.get("metadata", {})
    validate_metadata(metadata)
    entries = public_entries(public)
    expected = expected_inventory(inputs)
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("public namespace differs from exact 99-file plan")
    inherited = inherited_inventory()
    verified: list[dict] = []
    for index, name in enumerate(sorted(expected)):
        if index:
            time.sleep(0.35)
        payload = download(client, entries[name])
        wanted = expected[name]
        if len(payload) != wanted["bytes"] or sha_bytes(payload) != wanted["sha256"]:
            raise RuntimeError(f"public byte identity mismatch: {name}")
        verified.append(
            {
                "filename": name,
                "bytes": len(payload),
                "sha256": sha_bytes(payload),
                "disposition": "inherited_unchanged" if name in inherited else "original_02_addition",
                "public_byte_identity": "pass",
            }
        )
    file_state = get_json(client, f"{API}/records/{record}/files", "public-file-state")
    preview = file_state.get("default_preview")
    if preview != PRIMARY_PDF:
        raise RuntimeError(f"public default preview is {preview!r}, expected {PRIMARY_PDF!r}")
    serialized = json.dumps(metadata, ensure_ascii=False)
    receipt = {
        "schema": "o015-zenodo-original-02-public-readback-v1",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": "pass",
        "record_id": record,
        "record_doi": record_doi(public),
        "record_url": public.get("links", {}).get("self_html") or public.get("links", {}).get("record_html"),
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "status": public.get("status"),
        "is_latest": public.get("versions", {}).get("is_latest", True),
        "default_preview": preview,
        "default_preview_source": f"{API}/records/{record}/files",
        "title": metadata.get("title"),
        "version": metadata.get("version"),
        "file_count": len(verified),
        "inherited_file_count": sum(x["disposition"] == "inherited_unchanged" for x in verified),
        "addition_file_count": sum(x["disposition"] == "original_02_addition" for x in verified),
        "removed_parent_files": sorted(REPLACED_PARENT_FILES),
        "files": verified,
        "metadata_ttp_mentions": serialized.count("TTP"),
        "model_provenance_mentions": serialized.count(MODEL),
        "credential_material_recorded": False,
        "upstream_contact": False,
    }
    if (
        receipt["file_count"] != 99
        or receipt["inherited_file_count"] != 90
        or receipt["addition_file_count"] != 9
        or receipt["metadata_ttp_mentions"] != 1
        or receipt["model_provenance_mentions"] != 1
    ):
        raise RuntimeError("public release arithmetic/metadata gate failed")
    write_json(READBACK_PATH, receipt)
    return receipt


def closure() -> dict:
    current = state()
    if current.get("status") != "published":
        raise RuntimeError("cannot close an unpublished record")
    record = str(current["draft_id"])
    client = session(True)
    direct = client.get(f"{API}/records/{record}/draft", timeout=120)
    if direct.status_code != 404:
        raise RuntimeError(f"published record still exposes a draft: HTTP {direct.status_code}")
    response = client.get(
        f"{API}/user/records",
        params={"size": 100, "sort": "mostrecent"},
        timeout=120,
    )
    response.raise_for_status()
    hits = response.json().get("hits", {}).get("hits", [])
    drafts = [
        str(item.get("id"))
        for item in hits
        if isinstance(item, dict) and item.get("status") == "draft" and concept_id(item) == CONCEPT_ID
    ]
    if drafts:
        raise RuntimeError(f"concept lineage still has open drafts: {drafts}")
    result = {
        "schema": "o015-zenodo-original-02-draft-closure-v1",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": "pass",
        "record_id": record,
        "record_doi": current.get("draft_doi"),
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "authenticated_draft_lookup_status": 404,
        "concept_open_draft_count": 0,
        "credential_material_recorded": False,
    }
    write_json(CLOSURE_PATH, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=(
            "template-check",
            "build",
            "prepare",
            "upload",
            "validate",
            "publish",
            "readback",
            "closure",
            "release",
        ),
    )
    action = parser.parse_args().action
    if action == "template-check":
        result = template_check()
    elif action == "build":
        result = build_local()
    elif action == "prepare":
        result = prepare()
    elif action == "upload":
        result = upload()
    elif action == "validate":
        result = validate_draft()
    elif action == "publish":
        result = publish()
    elif action == "readback":
        result = readback()
    elif action == "closure":
        result = closure()
    else:
        prepare()
        upload()
        result = publish()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
