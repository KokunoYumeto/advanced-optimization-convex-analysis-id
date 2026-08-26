#!/usr/bin/env python3
"""Fail-closed in-place privacy correction for Zenodo record 22104724.

The program is intentionally bound to one already-published record.  It
recovers that record's existing edit draft, requests the record's bounded file
modification action, replaces exactly three files, and republishes the same
record.  It never creates a new version or concept.  Run the four actions
separately:

    python repair_original_02_privacy.py preflight
    python repair_original_02_privacy.py repair
    python repair_original_02_privacy.py readback
    python repair_original_02_privacy.py closure

``preflight`` and ``readback`` are anonymous.  ``repair`` and ``closure`` read
the credential only at call time from ZENODO_TOKEN or the configured file below.
No credential value or local user-profile locator is written to a receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
import truststore


truststore.inject_into_ssl()

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
API = "https://zenodo.org/api"

RECORD_ID = "22104724"
RECORD_DOI = "10.5281/zenodo.22104724"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
EXPECTED_FILE_COUNT = 99
EXPECTED_ADDITION_COUNT = 9
DEFAULT_PREVIEW = (
    "D90-ORIG-02-ketaksamaan-variasional-operator-monoton-resolven-"
    "pemisahan-id.pdf"
)

ZIP_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_ORIGINAL_02_2026.08.26.zip"
MANIFEST_NAME = "release-manifest-original-02-zenodo.json"
SUMS_NAME = "SHA256SUMS-original-02"
REPAIR_NAMES = (ZIP_NAME, MANIFEST_NAME, SUMS_NAME)

OLD_SHA256 = {
    ZIP_NAME: "40768542571ba269b2b175e080a611a4626f92068510d5e26b95cb53da66a1eb",
    MANIFEST_NAME: "bcfaf700c0e7be6c1b31065bf4349c08ef094109bddcd9f1baef43f8af8f3728",
    SUMS_NAME: "68cf540f041cb54cd254c5b5a0337202dc2475feb1960e281d1e0d1b9d700c4d",
}

REPLACEMENTS = {
    ZIP_NAME: ROOT
    / "release"
    / "original-02"
    / "2026-08-26"
    / ZIP_NAME,
    MANIFEST_NAME: HERE / MANIFEST_NAME,
    SUMS_NAME: HERE / SUMS_NAME,
}
BASELINE_READBACK = HERE / "zenodo-public-readback-original-02.json"
RELEASE_INPUTS = HERE / "release-inputs-original-02.json"
LOCAL_PACKAGE_VERIFICATION = (
    ROOT / "release" / "original-02" / "2026-08-26" / "local-verification-original-02.json"
)

STATE_PATH = HERE / "zenodo-privacy-repair-state-original-02.json"
CORRECTION_PATH = HERE / "zenodo-privacy-correction-original-02.json"
READBACK_PATH = HERE / "zenodo-privacy-readback-original-02.json"
CLOSURE_PATH = HERE / "zenodo-privacy-closure-original-02.json"
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
PHASES = {
    "preflight_passed",
    "existing_draft_recovered",
    "unlock_request_started",
    "file_modification_unlocked",
    "replacement_zip_complete",
    "replacement_manifest_complete",
    "replacement_sums_complete",
    "three_files_replaced",
    "publish_requested",
    "published",
    "readback_passed",
    "closed",
}

# Match ordinary, JSON-escaped, forward-slash, and file-URI Windows profile
# locators without retaining or reporting the profile name itself.
PROFILE_LOCATOR_TEXT = re.compile(
    r"(?i)(?:file:/+)?[a-z]:[\\/]+users[\\/]+[^\\/\x00-\x20\"']+[\\/]"
)
MAX_ARCHIVE_ENTRY_BYTES = 100_000_000
MAX_ARCHIVE_TOTAL_BYTES = 750_000_000
MAX_ARCHIVE_DEPTH = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha_bytes(data: bytes, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    digest.update(data)
    return digest.hexdigest()


def sha_file(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def identity_bytes(data: bytes) -> dict[str, Any]:
    return {
        "bytes": len(data),
        "sha256": sha_bytes(data),
        "md5": sha_bytes(data, "md5"),
    }


def identity_file(path: Path) -> dict[str, Any]:
    return {
        "bytes": path.stat().st_size,
        "sha256": sha_file(path),
        "md5": sha_file(path, "md5"),
    }


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha_bytes(payload)


def read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"required {label} is missing")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"required {label} is not a JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if PROFILE_LOCATOR_TEXT.search(text):
        raise RuntimeError("refusing to write a receipt containing a user-profile locator")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def safe_error_text(error: BaseException) -> str:
    text = str(error)
    home = str(Path.home())
    if home:
        text = re.sub(re.escape(home), "<USER_PROFILE>", text, flags=re.IGNORECASE)
    text = PROFILE_LOCATOR_TEXT.sub("<USER_PROFILE_LOCATOR>/", text)
    return text[:1000]


def profile_hits_in_bytes(data: bytes, location: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
        try:
            text = data.decode(encoding, errors="ignore")
        except LookupError:
            continue
        count = sum(1 for _ in PROFILE_LOCATOR_TEXT.finditer(text))
        if count:
            hits.append({"location": location, "surface": encoding, "count": count})
    return hits


def safe_member_name(name: str) -> str:
    if PROFILE_LOCATOR_TEXT.search(name):
        return "<PROFILE_LOCATOR_ENTRY>"
    return name


def pdf_decoded_hits(data: bytes, location: str) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader
        from pypdf.generic import IndirectObject, StreamObject
    except ImportError as error:  # fail closed when a PDF surface cannot be decoded
        raise RuntimeError("pypdf is required for privacy scanning") from error

    reader = PdfReader(io.BytesIO(data), strict=False)
    hits: list[dict[str, Any]] = []
    metadata = "\n".join(str(value) for value in (reader.metadata or {}).values())
    count = sum(1 for _ in PROFILE_LOCATOR_TEXT.finditer(metadata))
    if count:
        hits.append({"location": location, "surface": "pdf_metadata", "count": count})

    seen: set[tuple[int, int]] = set()
    for generation, identifiers in reader.xref.items():
        for identifier in identifiers:
            key = (int(identifier), int(generation))
            if key in seen:
                continue
            seen.add(key)
            try:
                obj = reader.get_object(IndirectObject(identifier, generation, reader))
            except Exception:
                continue
            if not isinstance(obj, StreamObject):
                continue
            try:
                decoded = obj.get_data()
            except Exception:
                continue
            hits.extend(profile_hits_in_bytes(decoded, f"{location}!pdf_stream"))
    return hits


def scan_payload(
    data: bytes,
    location: str,
    *,
    depth: int = 0,
) -> list[dict[str, Any]]:
    hits = profile_hits_in_bytes(data, location)
    if data.startswith(b"%PDF-"):
        hits.extend(pdf_decoded_hits(data, location))

    if depth > MAX_ARCHIVE_DEPTH:
        raise RuntimeError("archive privacy scan exceeded maximum nesting depth")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return hits

    total = 0
    with archive:
        for info in archive.infolist():
            member = safe_member_name(info.filename)
            member_location = f"{location}!{member}"
            hits.extend(profile_hits_in_bytes(info.filename.encode("utf-8"), member_location))
            if info.is_dir():
                continue
            if info.file_size > MAX_ARCHIVE_ENTRY_BYTES:
                raise RuntimeError("archive entry exceeds bounded privacy-scan limit")
            total += info.file_size
            if total > MAX_ARCHIVE_TOTAL_BYTES:
                raise RuntimeError("archive exceeds bounded privacy-scan budget")
            payload = archive.read(info)
            hits.extend(scan_payload(payload, member_location, depth=depth + 1))
    return hits


def baseline() -> dict[str, Any]:
    value = read_json(BASELINE_READBACK, "baseline public readback")
    if (
        value.get("schema") != "o015-zenodo-original-02-public-readback-v1"
        or value.get("result") != "pass"
        or str(value.get("record_id")) != RECORD_ID
        or value.get("record_doi") != RECORD_DOI
        or str(value.get("concept_id")) != CONCEPT_ID
        or value.get("concept_doi") != CONCEPT_DOI
        or value.get("default_preview") != DEFAULT_PREVIEW
        or value.get("file_count") != EXPECTED_FILE_COUNT
        or value.get("addition_file_count") != EXPECTED_ADDITION_COUNT
    ):
        raise RuntimeError("baseline public readback identity gate failed")
    files = value.get("files")
    if not isinstance(files, list) or len(files) != EXPECTED_FILE_COUNT:
        raise RuntimeError("baseline public readback does not contain exactly 99 files")
    inventory: dict[str, dict[str, Any]] = {}
    additions: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("filename"), str):
            raise RuntimeError("baseline public readback has an invalid file entry")
        name = item["filename"]
        if name in inventory:
            raise RuntimeError("baseline public readback contains duplicate filenames")
        ident = {"bytes": item.get("bytes"), "sha256": item.get("sha256")}
        if not isinstance(ident["bytes"], int) or not re.fullmatch(
            r"[0-9a-f]{64}", str(ident["sha256"])
        ):
            raise RuntimeError("baseline public readback has an invalid identity")
        inventory[name] = ident
        if item.get("disposition") == "original_02_addition":
            additions.add(name)
    if len(inventory) != EXPECTED_FILE_COUNT or len(additions) != EXPECTED_ADDITION_COUNT:
        raise RuntimeError("baseline inventory arithmetic failed")
    if set(REPAIR_NAMES) - additions:
        raise RuntimeError("repair namespace is not wholly inside the nine additions")
    for name, wanted in OLD_SHA256.items():
        if inventory.get(name, {}).get("sha256") != wanted:
            raise RuntimeError(f"baseline old identity mismatch for {name}")
    value["inventory"] = inventory
    value["addition_names"] = additions
    return value


def parse_sums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\r\n]+)", raw)
        if not match or match.group(2) in result:
            raise RuntimeError("sanitized checksum file has invalid or duplicate entries")
        result[match.group(2)] = match.group(1)
    return result


def local_gate() -> dict[str, Any]:
    base = baseline()
    reasons: list[str] = []
    missing = [name for name, path in REPLACEMENTS.items() if not path.is_file()]
    if missing:
        return {
            "result": "wait",
            "state": "waiting_for_sanitized_replacements",
            "reasons": [f"missing:{name}" for name in missing],
            "credential_accessed": False,
        }

    identities = {name: identity_file(path) for name, path in REPLACEMENTS.items()}
    for name in REPAIR_NAMES:
        if identities[name]["sha256"] == OLD_SHA256[name]:
            reasons.append(f"still_has_contaminated_baseline_hash:{name}")

    privacy: dict[str, list[dict[str, Any]]] = {}
    for name, path in REPLACEMENTS.items():
        hits = scan_payload(path.read_bytes(), name)
        privacy[name] = hits
        if hits:
            reasons.append(f"profile_locator_detected:{name}:{sum(x['count'] for x in hits)}")

    try:
        manifest = read_json(REPLACEMENTS[MANIFEST_NAME], "sanitized Zenodo manifest")
        manifest_entries = manifest.get("additions_before_manifest_and_sums")
        expected_manifest_names = base["addition_names"] - {MANIFEST_NAME, SUMS_NAME}
        if not isinstance(manifest_entries, dict) or set(manifest_entries) != expected_manifest_names:
            reasons.append("manifest_addition_namespace_mismatch")
        else:
            for name in sorted(expected_manifest_names):
                wanted = (
                    identities[ZIP_NAME]
                    if name == ZIP_NAME
                    else base["inventory"][name]
                )
                found = manifest_entries[name]
                if (
                    not isinstance(found, dict)
                    or found.get("bytes") != wanted["bytes"]
                    or found.get("sha256") != wanted["sha256"]
                ):
                    reasons.append(f"manifest_identity_mismatch:{name}")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
        reasons.append("manifest_parse_or_identity_gate_failed")

    try:
        sums = parse_sums(REPLACEMENTS[SUMS_NAME])
        expected_sum_names = base["addition_names"] - {SUMS_NAME}
        if set(sums) != expected_sum_names:
            reasons.append("checksum_namespace_mismatch")
        else:
            for name in sorted(expected_sum_names):
                if name == ZIP_NAME:
                    wanted_sha = identities[ZIP_NAME]["sha256"]
                elif name == MANIFEST_NAME:
                    wanted_sha = identities[MANIFEST_NAME]["sha256"]
                else:
                    wanted_sha = base["inventory"][name]["sha256"]
                if sums[name] != wanted_sha:
                    reasons.append(f"checksum_identity_mismatch:{name}")
    except (OSError, UnicodeDecodeError, RuntimeError):
        reasons.append("checksum_parse_or_identity_gate_failed")

    try:
        inputs = read_json(RELEASE_INPUTS, "release input freeze")
        artifacts = inputs.get("artifacts")
        expected_artifact_names = base["addition_names"] - {MANIFEST_NAME, SUMS_NAME}
        if not isinstance(artifacts, dict) or set(artifacts) != expected_artifact_names:
            reasons.append("release_input_artifact_namespace_mismatch")
        else:
            for name in sorted(expected_artifact_names):
                wanted = identities[ZIP_NAME] if name == ZIP_NAME else base["inventory"][name]
                found = artifacts[name]
                if (
                    not isinstance(found, dict)
                    or found.get("bytes") != wanted["bytes"]
                    or found.get("sha256") != wanted["sha256"]
                ):
                    reasons.append(f"release_input_identity_mismatch:{name}")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
        reasons.append("release_input_parse_or_identity_gate_failed")

    try:
        package_receipt = read_json(LOCAL_PACKAGE_VERIFICATION, "local package verification")
        zip_receipt = package_receipt.get("zip")
        if (
            package_receipt.get("result") != "pass"
            or not isinstance(zip_receipt, dict)
            or zip_receipt.get("bytes") != identities[ZIP_NAME]["bytes"]
            or zip_receipt.get("sha256") != identities[ZIP_NAME]["sha256"]
        ):
            reasons.append("local_package_verification_identity_mismatch")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
        reasons.append("local_package_verification_gate_failed")

    if reasons:
        return {
            "result": "wait",
            "state": "waiting_for_sanitized_replacements",
            "reasons": sorted(set(reasons)),
            "local_files": {
                name: {"bytes": item["bytes"], "sha256": item["sha256"]}
                for name, item in identities.items()
            },
            "profile_locator_hits": {
                name: sum(hit["count"] for hit in hits) for name, hits in privacy.items()
            },
            "credential_accessed": False,
        }

    return {
        "result": "pass",
        "state": "sanitized_replacements_ready",
        "local_files": {
            name: {"bytes": item["bytes"], "sha256": item["sha256"]}
            for name, item in identities.items()
        },
        "profile_locator_hits": {name: 0 for name in REPAIR_NAMES},
        "credential_accessed": False,
    }


def token() -> str:
    value = os.environ.get("ZENODO_TOKEN", "").strip()
    if len(value) >= 20:
        return value
    if not TOKEN_FILE.is_file():
        raise RuntimeError("Zenodo credential is unavailable")
    text = TOKEN_FILE.read_text(encoding="utf-8")
    candidates: list[str] = []
    for line in text.splitlines():
        candidates.extend(
            match.group(1)
            for match in re.finditer(
                r"(?i)(?:token|access[ -]?token|api[ -]?key)\s*[:=]\s*"
                r"([A-Za-z0-9._-]{20,})",
                line,
            )
        )
    if not candidates:
        candidates = re.findall(
            r"(?<![A-Za-z0-9])[A-Za-z0-9._-]{20,}(?![A-Za-z0-9])", text
        )
    if not candidates:
        raise RuntimeError("no usable Zenodo credential found")
    return candidates[0]


def session(authenticated: bool) -> requests.Session:
    client = requests.Session()
    client.headers.update({"User-Agent": "o015-original-02-privacy-repair/1"})
    if authenticated:
        client.headers.update({"Authorization": f"Bearer {token()}"})
    return client


def get_json(client: requests.Session, url: str, label: str) -> dict[str, Any]:
    response: requests.Response | None = None
    for attempt in range(1, 6):
        response = client.get(url, timeout=120)
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


def record_id(record: dict[str, Any]) -> str:
    return str(record.get("id"))


def record_doi(record: dict[str, Any]) -> str | None:
    return (
        record.get("pids", {}).get("doi", {}).get("identifier")
        or record.get("doi")
        or record.get("metadata", {}).get("doi")
    )


def concept_id(record: dict[str, Any]) -> str | None:
    parent = record.get("parent")
    if isinstance(parent, dict) and parent.get("id") is not None:
        return str(parent["id"])
    value = record.get("conceptrecid")
    return str(value) if value is not None else None


def record_entries(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    files = record.get("files")
    entries = files.get("entries", []) if isinstance(files, dict) else files
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise RuntimeError("unexpected file inventory")
    result = {
        item.get("key") or item.get("filename"): item
        for item in entries
        if isinstance(item, dict)
    }
    if None in result or len(result) != len(entries):
        raise RuntimeError("duplicate or missing file key")
    return result


def download(client: requests.Session, item: dict[str, Any]) -> bytes:
    links = item.get("links", {})
    url = links.get("content") or links.get("download") or links.get("self")
    if not url:
        raise RuntimeError("public file lacks a content URL")
    response: requests.Response | None = None
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


def publication_age_days(record: dict[str, Any]) -> float:
    created = record.get("created")
    if not isinstance(created, str):
        raise RuntimeError("published record lacks a creation timestamp")
    stamp = datetime.fromisoformat(created.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds() / 86400
    if age < -0.01:
        raise RuntimeError("published record timestamp is in the future")
    return age


def expected_new_inventory(base: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected = {
        name: {"bytes": item["bytes"], "sha256": item["sha256"]}
        for name, item in base["inventory"].items()
    }
    for name, path in REPLACEMENTS.items():
        ident = identity_file(path)
        expected[name] = {"bytes": ident["bytes"], "sha256": ident["sha256"]}
    return expected


def public_snapshot(
    *,
    require_variant: str | None,
    require_privacy_clean: bool,
) -> dict[str, Any]:
    base = baseline()
    client = session(False)
    record = get_json(client, f"{API}/records/{RECORD_ID}", "published record")
    if (
        record_id(record) != RECORD_ID
        or record.get("status") != "published"
        or record_doi(record) != RECORD_DOI
        or concept_id(record) != CONCEPT_ID
    ):
        raise RuntimeError("published record DOI/concept/status identity mismatch")
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        raise RuntimeError("published record lacks metadata")
    if metadata.get("title") != base.get("title") or metadata.get("version") != base.get("version"):
        raise RuntimeError("published metadata title/version changed")

    entries = record_entries(record)
    if set(entries) != set(base["inventory"]) or len(entries) != EXPECTED_FILE_COUNT:
        raise RuntimeError("published namespace is not the exact baseline 99-file namespace")
    file_state = get_json(client, f"{API}/records/{RECORD_ID}/files", "public file state")
    if file_state.get("default_preview") != DEFAULT_PREVIEW:
        raise RuntimeError("published default preview changed")

    old_expected = base["inventory"]
    new_expected = expected_new_inventory(base)
    verified: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    transport: dict[str, dict[str, Any]] = {}
    for index, name in enumerate(sorted(entries)):
        if index:
            time.sleep(0.25)
        payload = download(client, entries[name])
        ident = identity_bytes(payload)
        payloads[name] = payload
        transport[name] = {
            "bytes": ident["bytes"],
            "md5": ident["md5"],
            "remote_checksum": entries[name].get("checksum"),
        }
        verified.append(
            {"filename": name, "bytes": ident["bytes"], "sha256": ident["sha256"]}
        )

    actual = {item["filename"]: item for item in verified}
    matches_old = all(
        actual[name]["bytes"] == old_expected[name]["bytes"]
        and actual[name]["sha256"] == old_expected[name]["sha256"]
        for name in actual
    )
    matches_new = all(
        actual[name]["bytes"] == new_expected[name]["bytes"]
        and actual[name]["sha256"] == new_expected[name]["sha256"]
        for name in actual
    )
    variant = "published_original" if matches_old else "privacy_corrected" if matches_new else None
    if variant is None:
        raise RuntimeError("published bytes match neither exact old nor exact corrected inventory")
    if require_variant is not None and variant != require_variant:
        raise RuntimeError(f"published inventory is {variant}, expected {require_variant}")

    privacy_hits: dict[str, list[dict[str, Any]]] = {}
    for name in sorted(base["addition_names"]):
        privacy_hits[name] = scan_payload(payloads[name], name)
    total_hits = sum(hit["count"] for hits in privacy_hits.values() for hit in hits)
    if require_privacy_clean and total_hits:
        raise RuntimeError("published additions still expose a Windows user-profile locator")

    return {
        "record": record,
        "metadata_sha256": canonical_json_sha256(metadata),
        "publication_age_days": publication_age_days(record),
        "variant": variant,
        "verified": verified,
        "transport": transport,
        "profile_locator_hits": total_hits,
        "profile_locator_hit_files": sorted(name for name, hits in privacy_hits.items() if hits),
        "default_preview": DEFAULT_PREVIEW,
    }


def preflight() -> dict[str, Any]:
    local = local_gate()
    if local["result"] != "pass":
        return {
            "schema": "o015-zenodo-original-02-privacy-preflight-v1",
            "checked_at_utc": utc_now(),
            **local,
        }
    public = public_snapshot(require_variant=None, require_privacy_clean=False)
    if public["publication_age_days"] > 30:
        raise RuntimeError("record is outside Zenodo's 30-day minor-file-correction window")
    if public["variant"] == "published_original":
        for name, wanted in OLD_SHA256.items():
            found = next(item for item in public["verified"] if item["filename"] == name)
            if found["sha256"] != wanted:
                raise RuntimeError(f"old public hash gate failed for {name}")
        state = "ready_for_in_place_minor_file_correction"
    else:
        state = "already_privacy_corrected"
    return {
        "schema": "o015-zenodo-original-02-privacy-preflight-v1",
        "checked_at_utc": utc_now(),
        "result": "pass",
        "state": state,
        "record_id": RECORD_ID,
        "record_doi": RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "file_count": EXPECTED_FILE_COUNT,
        "replacement_names": list(REPAIR_NAMES),
        "current_public_variant": public["variant"],
        "current_public_metadata_sha256": public["metadata_sha256"],
        "current_profile_locator_hits": public["profile_locator_hits"],
        "publication_age_days": round(public["publication_age_days"], 6),
        "local_files": local["local_files"],
        "credential_accessed": False,
    }


def save_state(value: dict[str, Any]) -> None:
    phase = value.get("phase")
    if phase not in PHASES:
        raise RuntimeError("refusing to write an unknown privacy-repair phase")
    payload = {
        "schema": "o015-zenodo-original-02-privacy-repair-state-v1",
        "record_id": RECORD_ID,
        "record_doi": RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "credential_material_recorded": False,
        **value,
    }
    write_json(STATE_PATH, payload)
    write_json(HERE / f"zenodo-privacy-phase-{phase}-original-02.json", payload)


def load_state() -> dict[str, Any]:
    value = read_json(STATE_PATH, "privacy repair state")
    if (
        value.get("schema") != "o015-zenodo-original-02-privacy-repair-state-v1"
        or str(value.get("record_id")) != RECORD_ID
        or value.get("record_doi") != RECORD_DOI
        or str(value.get("concept_id")) != CONCEPT_ID
        or value.get("concept_doi") != CONCEPT_DOI
    ):
        raise RuntimeError("privacy repair state belongs to another record or concept")
    return value


def normalized_md5(checksum: object) -> str | None:
    if not isinstance(checksum, str):
        return None
    return checksum.lower().removeprefix("md5:")


def draft_entries(client: requests.Session) -> dict[str, dict[str, Any]]:
    value = get_json(client, f"{API}/records/{RECORD_ID}/draft/files", "draft files")
    raw = value.get("entries", value)
    entries: list[dict[str, Any]] = []
    if isinstance(raw, dict):
        for key, item in raw.items():
            if not isinstance(item, dict):
                raise RuntimeError("draft file map contains a non-object entry")
            normalized = dict(item)
            normalized.setdefault("key", key)
            entries.append(normalized)
    elif isinstance(raw, list) and all(isinstance(item, dict) for item in raw):
        entries = raw
    else:
        raise RuntimeError("unexpected draft file inventory")
    result = {item.get("key"): item for item in entries}
    if None in result or len(result) != len(entries):
        raise RuntimeError("duplicate or missing draft file key")
    return result


def completed_identity(item: dict[str, Any]) -> tuple[int | None, str | None] | None:
    if item.get("status") != "completed":
        return None
    size = item.get("size")
    return (size if isinstance(size, int) else None, normalized_md5(item.get("checksum")))


def repair_phase_payload(
    phase: str,
    *,
    metadata_sha256: str,
    local: dict[str, Any],
    target_states: dict[str, str] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "phase": phase,
        "updated_at_utc": utc_now(),
        "baseline_metadata_sha256": metadata_sha256,
        "old_replacement_sha256": OLD_SHA256,
        "new_replacements": local["local_files"],
        "replacement_names": list(REPAIR_NAMES),
        "unchanged_file_count": EXPECTED_FILE_COUNT - len(REPAIR_NAMES),
        "new_version_created": False,
    }
    if target_states is not None:
        value["target_states"] = target_states
    return value


def assert_existing_draft(
    client: requests.Session,
    draft: dict[str, Any],
    *,
    metadata_sha256: str,
    old_expected: dict[str, dict[str, Any]],
    new_expected: dict[str, dict[str, Any]],
) -> dict[str, str]:
    if (
        record_id(draft) != RECORD_ID
        or draft.get("status") != "draft"
        or record_doi(draft) != RECORD_DOI
        or concept_id(draft) != CONCEPT_ID
    ):
        raise RuntimeError("existing edit draft changed record, DOI, concept, or status")
    metadata = draft.get("metadata")
    if not isinstance(metadata, dict) or canonical_json_sha256(metadata) != metadata_sha256:
        raise RuntimeError("existing edit draft metadata differs from public metadata")
    file_state = get_json(
        client,
        f"{API}/records/{RECORD_ID}/draft/files",
        "draft file state",
    )
    if file_state.get("default_preview") != DEFAULT_PREVIEW:
        raise RuntimeError("existing edit draft changed the default preview")

    entries = draft_entries(client)
    expected_names = set(old_expected)
    actual_names = set(entries)
    if actual_names - expected_names:
        raise RuntimeError("existing edit draft contains an unexpected filename")
    missing = expected_names - actual_names
    if missing - set(REPAIR_NAMES):
        raise RuntimeError("existing edit draft is missing a protected unchanged file")
    if not (EXPECTED_FILE_COUNT - len(REPAIR_NAMES) <= len(entries) <= EXPECTED_FILE_COUNT):
        raise RuntimeError("existing edit draft namespace is outside bounded repair state")

    protected_names = expected_names - set(REPAIR_NAMES)
    for name in sorted(protected_names):
        identity = completed_identity(entries[name])
        wanted = old_expected[name]
        if identity != (wanted["bytes"], wanted["md5"]):
            raise RuntimeError(f"protected unchanged draft byte identity differs: {name}")

    states: dict[str, str] = {}
    for name in REPAIR_NAMES:
        item = entries.get(name)
        if item is None:
            states[name] = "missing_after_partial_replacement"
            continue
        identity = completed_identity(item)
        old = old_expected[name]
        new = new_expected[name]
        if identity == (old["bytes"], old["md5"]):
            states[name] = "old"
        elif identity == (new["bytes"], new["md5"]):
            states[name] = "new"
        elif identity is None:
            states[name] = "incomplete_after_partial_replacement"
        else:
            raise RuntimeError(f"repair target has an unrecognized completed identity: {name}")
    return states


def replace_draft_file(
    client: requests.Session,
    name: str,
    path: Path,
    *,
    metadata_sha256: str,
    old_expected: dict[str, dict[str, Any]],
    new_expected: dict[str, dict[str, Any]],
) -> dict[str, str]:
    draft = get_json(client, f"{API}/records/{RECORD_ID}/draft", "repair draft")
    states = assert_existing_draft(
        client,
        draft,
        metadata_sha256=metadata_sha256,
        old_expected=old_expected,
        new_expected=new_expected,
    )
    if states[name] == "new":
        return states

    endpoint = f"{API}/records/{RECORD_ID}/draft/files"
    if name in draft_entries(client):
        response = client.delete(f"{endpoint}/{quote(name, safe='')}", timeout=120)
        if response.status_code not in (200, 204, 404):
            response.raise_for_status()
    client.post(endpoint, json=[{"key": name}], timeout=120).raise_for_status()
    with path.open("rb") as stream:
        client.put(
            f"{endpoint}/{quote(name, safe='')}/content",
            data=stream,
            headers={"Content-Type": "application/octet-stream"},
            timeout=600,
        ).raise_for_status()
    client.post(
        f"{endpoint}/{quote(name, safe='')}/commit", timeout=120
    ).raise_for_status()

    draft = get_json(client, f"{API}/records/{RECORD_ID}/draft", "repaired draft")
    states = assert_existing_draft(
        client,
        draft,
        metadata_sha256=metadata_sha256,
        old_expected=old_expected,
        new_expected=new_expected,
    )
    if states[name] != "new":
        raise RuntimeError(f"replacement did not converge to exact new bytes: {name}")
    return states


def repair() -> dict[str, Any]:
    gate = preflight()
    if gate.get("result") != "pass":
        raise RuntimeError("sanitized replacements are not ready; run preflight again later")
    local = local_gate()
    if local["result"] != "pass":
        raise RuntimeError("local replacement gate changed after preflight")

    if gate.get("state") == "already_privacy_corrected":
        save_state(
            repair_phase_payload(
                "published",
                metadata_sha256=str(gate["current_public_metadata_sha256"]),
                local=local,
                target_states={name: "new" for name in REPAIR_NAMES},
            )
        )
        return readback()

    public = public_snapshot(require_variant="published_original", require_privacy_clean=False)
    if public["publication_age_days"] > 30:
        raise RuntimeError("record is outside Zenodo's 30-day minor-file-correction window")
    baseline_metadata_sha = public["metadata_sha256"]
    old_expected: dict[str, dict[str, Any]] = {}
    for item in public["verified"]:
        transport = public["transport"][item["filename"]]
        old_expected[item["filename"]] = {
            "bytes": item["bytes"],
            "sha256": item["sha256"],
            "md5": transport["md5"],
        }
    new_expected = dict(old_expected)
    for name, path in REPLACEMENTS.items():
        new_expected[name] = identity_file(path)

    previous_phase: str | None = None
    if STATE_PATH.is_file():
        previous_phase = str(load_state().get("phase"))
    unlocked_or_later = {
        "file_modification_unlocked",
        "replacement_zip_complete",
        "replacement_manifest_complete",
        "replacement_sums_complete",
        "three_files_replaced",
        "publish_requested",
        "published",
        "readback_passed",
        "closed",
    }
    unlock_started_or_later = {"unlock_request_started", *unlocked_or_later}
    if previous_phase not in unlock_started_or_later:
        save_state(
            repair_phase_payload(
                "preflight_passed", metadata_sha256=baseline_metadata_sha, local=local
            )
        )
    client = session(True)
    draft = get_json(client, f"{API}/records/{RECORD_ID}/draft", "existing edit draft")
    states = assert_existing_draft(
        client,
        draft,
        metadata_sha256=baseline_metadata_sha,
        old_expected=old_expected,
        new_expected=new_expected,
    )
    if previous_phase not in unlock_started_or_later:
        save_state(
            repair_phase_payload(
                "existing_draft_recovered",
                metadata_sha256=baseline_metadata_sha,
                local=local,
                target_states=states,
            )
        )
    if all(state == "old" for state in states.values()) and previous_phase not in unlocked_or_later:
        endpoint = f"{API}/records/{RECORD_ID}/file-modification"
        link = draft.get("links", {}).get("file_modification")
        save_state(
            repair_phase_payload(
                "unlock_request_started",
                metadata_sha256=baseline_metadata_sha,
                local=local,
                target_states=states,
            )
        )
        if link == endpoint:
            # Zenodo's current record-management UI submits these explicit
            # (empty) Formik fields.  A bodyless POST is not the same request
            # and currently fails server-side with HTTP 500.
            response = client.post(
                endpoint,
                json={"reason": "", "comment": ""},
                timeout=180,
            )
            if response.status_code not in (200, 201, 202, 204, 409):
                response.raise_for_status()
                raise RuntimeError("unexpected file-modification action status")
        elif previous_phase != "unlock_request_started":
            raise RuntimeError("draft does not advertise the exact bounded file-modification action")
    # A missing, incomplete, or new repair target proves that the bounded file
    # modification transaction had already started before this invocation.
    draft = get_json(client, f"{API}/records/{RECORD_ID}/draft", "unlocked edit draft")
    states = assert_existing_draft(
        client,
        draft,
        metadata_sha256=baseline_metadata_sha,
        old_expected=old_expected,
        new_expected=new_expected,
    )
    save_state(
        repair_phase_payload(
            "file_modification_unlocked",
            metadata_sha256=baseline_metadata_sha,
            local=local,
            target_states=states,
        )
    )

    phase_by_name = {
        ZIP_NAME: "replacement_zip_complete",
        MANIFEST_NAME: "replacement_manifest_complete",
        SUMS_NAME: "replacement_sums_complete",
    }
    for name in REPAIR_NAMES:
        states = replace_draft_file(
            client,
            name,
            REPLACEMENTS[name],
            metadata_sha256=baseline_metadata_sha,
            old_expected=old_expected,
            new_expected=new_expected,
        )
        save_state(
            repair_phase_payload(
                phase_by_name[name],
                metadata_sha256=baseline_metadata_sha,
                local=local,
                target_states=states,
            )
        )

    final_draft = get_json(client, f"{API}/records/{RECORD_ID}/draft", "final repair draft")
    states = assert_existing_draft(
        client,
        final_draft,
        metadata_sha256=baseline_metadata_sha,
        old_expected=old_expected,
        new_expected=new_expected,
    )
    if any(state != "new" for state in states.values()):
        raise RuntimeError("not all three repair targets have exact new bytes")
    save_state(
        repair_phase_payload(
            "three_files_replaced",
            metadata_sha256=baseline_metadata_sha,
            local=local,
            target_states=states,
        )
    )

    response = client.post(
        f"{API}/records/{RECORD_ID}/draft/actions/publish", timeout=180
    )
    if response.status_code not in (200, 201, 202, 409):
        response.raise_for_status()
    save_state(
        repair_phase_payload(
            "publish_requested",
            metadata_sha256=baseline_metadata_sha,
            local=local,
            target_states=states,
        )
    )

    public_client = session(False)
    for attempt in range(1, 16):
        candidate = public_client.get(f"{API}/records/{RECORD_ID}", timeout=120)
        if candidate.status_code == 200:
            value = candidate.json()
            if value.get("status") == "published" and record_id(value) == RECORD_ID:
                entries = record_entries(value)
                replacement_bytes_visible = set(REPAIR_NAMES).issubset(entries)
                if replacement_bytes_visible:
                    for name in REPAIR_NAMES:
                        payload = download(public_client, entries[name])
                        wanted = identity_file(REPLACEMENTS[name])
                        if len(payload) != wanted["bytes"] or sha_bytes(payload) != wanted["sha256"]:
                            replacement_bytes_visible = False
                            break
                if replacement_bytes_visible:
                    break
        if candidate.status_code not in (404, 429) and 400 <= candidate.status_code < 500:
            candidate.raise_for_status()
        if attempt < 15:
            time.sleep(min(attempt * 2, 12))
    else:
        raise RuntimeError("in-place correction did not become anonymously visible")

    save_state(
        repair_phase_payload(
            "published",
            metadata_sha256=baseline_metadata_sha,
            local=local,
            target_states=states,
        )
    )
    readback_receipt = readback()
    correction = {
        "schema": "o015-zenodo-original-02-privacy-correction-v1",
        "corrected_at_utc": utc_now(),
        "result": "pass",
        "action": "records_api_same_record_file_modification",
        "file_modification_endpoint": "/api/records/22104724/file-modification",
        "publish_endpoint": "/api/records/22104724/draft/actions/publish",
        "record_id": RECORD_ID,
        "record_doi": RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "file_count": EXPECTED_FILE_COUNT,
        "unchanged_file_count": EXPECTED_FILE_COUNT - len(REPAIR_NAMES),
        "replaced_file_count": 3,
        "replaced_files": [
            {
                "filename": name,
                "old_sha256": OLD_SHA256[name],
                "new_bytes": local["local_files"][name]["bytes"],
                "new_sha256": local["local_files"][name]["sha256"],
            }
            for name in REPAIR_NAMES
        ],
        "metadata_sha256_before": baseline_metadata_sha,
        "metadata_sha256_after": readback_receipt["metadata_sha256"],
        "metadata_unchanged": True,
        "default_preview_unchanged": True,
        "doi_unchanged": True,
        "concept_unchanged": True,
        "new_version_created": False,
        "credential_material_recorded": False,
    }
    write_json(CORRECTION_PATH, correction)
    return correction


def readback() -> dict[str, Any]:
    local = local_gate()
    if local["result"] != "pass":
        raise RuntimeError("sanitized local replacements no longer pass")
    state = load_state()
    if state.get("phase") not in {"published", "readback_passed", "closed"}:
        raise RuntimeError("privacy repair state is not published")
    snapshot = public_snapshot(
        require_variant="privacy_corrected", require_privacy_clean=True
    )
    if snapshot["metadata_sha256"] != state.get("baseline_metadata_sha256"):
        raise RuntimeError("published metadata changed during file correction")
    base = baseline()
    additions = base["addition_names"]
    receipt = {
        "schema": "o015-zenodo-original-02-privacy-readback-v1",
        "verified_at_utc": utc_now(),
        "result": "pass",
        "record_id": RECORD_ID,
        "record_doi": RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "file_count": len(snapshot["verified"]),
        "addition_file_count": len(additions),
        "replaced_file_count": 3,
        "default_preview": snapshot["default_preview"],
        "metadata_sha256": snapshot["metadata_sha256"],
        "metadata_unchanged": True,
        "doi_unchanged": True,
        "concept_unchanged": True,
        "default_preview_unchanged": True,
        "profile_locator_hits_in_public_additions": 0,
        "archive_entries_scanned": True,
        "pdf_decoded_streams_scanned": True,
        "files": [
            {
                **item,
                "disposition": (
                    "privacy_replaced"
                    if item["filename"] in REPAIR_NAMES
                    else "addition_unchanged"
                    if item["filename"] in additions
                    else "inherited_unchanged"
                ),
                "public_byte_identity": "pass",
            }
            for item in snapshot["verified"]
        ],
        "credential_material_recorded": False,
    }
    if receipt["file_count"] != EXPECTED_FILE_COUNT:
        raise RuntimeError("corrected public readback does not contain exactly 99 files")
    write_json(READBACK_PATH, receipt)
    save_state(
        {
            **{key: value for key, value in state.items() if key not in {"schema"}},
            "phase": "readback_passed",
            "updated_at_utc": utc_now(),
        }
    )
    return receipt


def closure() -> dict[str, Any]:
    readback_receipt = read_json(READBACK_PATH, "privacy public readback")
    if (
        readback_receipt.get("schema") != "o015-zenodo-original-02-privacy-readback-v1"
        or readback_receipt.get("result") != "pass"
        or str(readback_receipt.get("record_id")) != RECORD_ID
        or readback_receipt.get("record_doi") != RECORD_DOI
        or str(readback_receipt.get("concept_id")) != CONCEPT_ID
        or readback_receipt.get("concept_doi") != CONCEPT_DOI
        or readback_receipt.get("file_count") != EXPECTED_FILE_COUNT
        or readback_receipt.get("profile_locator_hits_in_public_additions") != 0
    ):
        raise RuntimeError("privacy public readback is not a passing closure input")
    state = load_state()
    if state.get("phase") not in {"readback_passed", "closed"}:
        raise RuntimeError("privacy repair state has not passed anonymous readback")

    client = session(True)
    direct = client.get(f"{API}/records/{RECORD_ID}/draft", timeout=120)
    if direct.status_code != 404:
        if direct.status_code >= 400:
            direct.raise_for_status()
        raise RuntimeError("corrected same-record edit draft remains open")
    response = client.get(
        f"{API}/user/records", params={"size": 100, "sort": "mostrecent"}, timeout=120
    )
    response.raise_for_status()
    hits = response.json().get("hits", {}).get("hits", [])
    open_drafts = [
        str(item.get("id"))
        for item in hits
        if isinstance(item, dict)
        and item.get("status") == "draft"
        and concept_id(item) == CONCEPT_ID
    ]
    if open_drafts:
        raise RuntimeError("the existing concept still has an open draft")
    receipt = {
        "schema": "o015-zenodo-original-02-privacy-closure-v1",
        "verified_at_utc": utc_now(),
        "result": "pass",
        "record_id": RECORD_ID,
        "record_doi": RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "authenticated_draft_lookup_status": 404,
        "concept_open_draft_count": 0,
        "file_count": EXPECTED_FILE_COUNT,
        "replaced_file_count": 3,
        "new_version_created": False,
        "credential_material_recorded": False,
    }
    write_json(CLOSURE_PATH, receipt)
    save_state(
        {
            **{key: value for key, value in state.items() if key not in {"schema"}},
            "phase": "closed",
            "updated_at_utc": utc_now(),
        }
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "repair", "readback", "closure"))
    action = parser.parse_args().action
    try:
        if action == "preflight":
            result = preflight()
        elif action == "repair":
            result = repair()
        elif action == "readback":
            result = readback()
        else:
            result = closure()
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as error:
        print(
            json.dumps(
                {
                    "result": "fail",
                    "action": action,
                    "error": safe_error_text(error),
                    "credential_material_recorded": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
