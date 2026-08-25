#!/usr/bin/env python3
"""Publish one additive Habring-spine version and verify all public bytes.

Credentials are accepted only through the ``ZENODO_TOKEN`` process environment
variable. The script never reads a token file and never serializes credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from urllib.parse import quote, unquote

import requests

import build_habring_spine as build


HERE = Path(__file__).resolve().parent
API = "https://zenodo.org/api"
STATE_PATH = build.STATE_PATH
READBACK_PATH = build.READBACK_PATH


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def token() -> str:
    value = os.environ.get("ZENODO_TOKEN", "").strip()
    if len(value) < 20:
        raise RuntimeError("ZENODO_TOKEN is absent from the process environment")
    return value


def session(*, authenticated: bool = True) -> requests.Session:
    client = requests.Session()
    client.headers.update({"User-Agent": "o015-habring-spine-publisher/1"})
    if authenticated:
        client.headers.update({"Authorization": f"Bearer {token()}"})
    return client


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def state() -> dict:
    if not STATE_PATH.is_file():
        raise RuntimeError("no bound Zenodo draft state exists")
    value = read_json(STATE_PATH)
    if (
        value.get("schema") != "o015-zenodo-habring-spine-draft-receipt-v1"
        or value.get("parent_record_id") != build.PARENT_RECORD_ID
        or value.get("parent_record_doi") != build.PARENT_RECORD_DOI
        or value.get("concept_id") != build.CONCEPT_ID
        or value.get("concept_doi") != build.CONCEPT_DOI
        or value.get("version") != build.VERSION
    ):
        raise RuntimeError("draft state belongs to a different lineage or version")
    return value


def draft_id() -> str:
    return str(state()["draft_id"])


def save_state(record: dict) -> dict:
    identifier = str(record.get("id"))
    if not identifier.isdigit():
        raise RuntimeError("Zenodo response lacks a numeric record id")
    doi = record.get("pids", {}).get("doi", {}).get("identifier") or record.get("metadata", {}).get("doi")
    status = record.get("status") or ("published" if record.get("is_published") else "draft")
    receipt = {
        "schema": "o015-zenodo-habring-spine-draft-receipt-v1",
        "status": status,
        "draft_id": identifier,
        "draft_doi": doi,
        "title": record.get("metadata", {}).get("title"),
        "version": build.VERSION,
        "parent_record_id": build.PARENT_RECORD_ID,
        "parent_record_doi": build.PARENT_RECORD_DOI,
        "concept_id": build.CONCEPT_ID,
        "concept_doi": build.CONCEPT_DOI,
    }
    STATE_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def template_payload() -> dict:
    template = read_json(build.TEMPLATE_PATH)
    return {"access": template["access"], "files": template["files"], "metadata": template["metadata"]}


def contributor_name(item: dict) -> str | None:
    person = item.get("person_or_org")
    if isinstance(person, dict):
        return person.get("name")
    return item.get("name")


def validate_organization_and_model(metadata: dict) -> None:
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    contributors = metadata.get("contributors", [])
    if not isinstance(contributors, list):
        raise RuntimeError("remote metadata contributors have an unexpected shape")
    ttp = [item for item in contributors if isinstance(item, dict) and contributor_name(item) == "TTP"]
    if (
        serialized.count("TTP") != 1
        or len(ttp) != 1
        or "TTP" in title
        or "TTP" in description
        or serialized.count(build.MODEL_ID) != 1
    ):
        raise RuntimeError("remote metadata organization/model gate failed")


def validate_metadata_shape(metadata: dict) -> None:
    """Validate the native InvenioRDM metadata shape used by draft endpoints."""
    expected = build.validate_template()
    for key in ("title", "description", "version", "publication_date"):
        if metadata.get(key) != expected.get(key):
            raise RuntimeError(f"remote metadata differs for {key}")
    # Zenodo enriches vocabulary-backed objects in draft responses (for
    # example, resource_type gains a localized title).  Compare their stable
    # identifiers rather than requiring byte-identical response decoration.
    if language_ids(metadata) != language_ids(expected):
        raise RuntimeError("remote metadata differs for languages")
    if resource_type_id(metadata.get("resource_type")) != resource_type_id(expected.get("resource_type")):
        raise RuntimeError("remote metadata differs for resource_type")
    validate_organization_and_model(metadata)


def language_ids(metadata: dict) -> list[str]:
    if "languages" in metadata:
        languages = metadata.get("languages")
        if not isinstance(languages, list):
            raise RuntimeError("remote metadata languages have an unexpected shape")
        values: list[str] = []
        for item in languages:
            identifier = item.get("id") if isinstance(item, dict) else item
            if not isinstance(identifier, str) or not identifier:
                raise RuntimeError("remote metadata contains an invalid language identifier")
            values.append(identifier)
        return values
    language = metadata.get("language")
    if not isinstance(language, str) or not language:
        raise RuntimeError("remote metadata lacks a language identifier")
    return [language]


def resource_type_id(value: object) -> str:
    if isinstance(value, str) and value:
        return value
    if not isinstance(value, dict):
        raise RuntimeError("remote metadata resource type has an unexpected shape")
    identifier = value.get("id")
    if isinstance(identifier, str) and identifier:
        return identifier
    legacy_type = value.get("type")
    legacy_subtype = value.get("subtype")
    if not isinstance(legacy_type, str) or not legacy_type:
        raise RuntimeError("remote metadata lacks a resource-type identifier")
    if legacy_subtype is None or legacy_subtype == "":
        return legacy_type
    if not isinstance(legacy_subtype, str):
        raise RuntimeError("remote metadata resource subtype has an unexpected shape")
    return f"{legacy_type}-{legacy_subtype}"


def validate_public_metadata_shape(metadata: dict) -> None:
    """Validate public metadata in either native or legacy Zenodo form."""
    expected = build.validate_template()
    for key in ("title", "description", "version", "publication_date"):
        if metadata.get(key) != expected.get(key):
            raise RuntimeError(f"public metadata differs for {key}")
    if language_ids(metadata) != language_ids(expected):
        raise RuntimeError("public metadata differs for languages")
    if resource_type_id(metadata.get("resource_type")) != resource_type_id(expected.get("resource_type")):
        raise RuntimeError("public metadata differs for resource_type")
    validate_organization_and_model(metadata)


def record_id(record: dict) -> str:
    identifier = str(record.get("id", ""))
    if not identifier.isdigit():
        raise RuntimeError("public record lacks a numeric record id")
    return identifier


def concept_id(record: dict) -> str:
    candidates: list[str] = []
    legacy = record.get("conceptrecid")
    if legacy is not None:
        candidates.append(str(legacy))
    parent = record.get("parent")
    if isinstance(parent, dict) and parent.get("id") is not None:
        candidates.append(str(parent["id"]))
    candidates = [item for item in candidates if item]
    if not candidates or len(set(candidates)) != 1 or not candidates[0].isdigit():
        raise RuntimeError("public record has missing or contradictory concept identity")
    return candidates[0]


def record_doi(record: dict) -> str | None:
    pids = record.get("pids")
    if isinstance(pids, dict):
        doi = pids.get("doi")
        if isinstance(doi, dict) and isinstance(doi.get("identifier"), str):
            return doi["identifier"]
    for candidate in (record.get("doi"), record.get("metadata", {}).get("doi")):
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def concept_doi(record: dict) -> str | None:
    candidate = record.get("conceptdoi")
    if isinstance(candidate, str) and candidate:
        return candidate
    parent = record.get("parent")
    if isinstance(parent, dict):
        pids = parent.get("pids")
        if isinstance(pids, dict):
            doi = pids.get("doi")
            if isinstance(doi, dict) and isinstance(doi.get("identifier"), str):
                return doi["identifier"]
    return None


def get_json_with_retry(client: requests.Session, url: str, *, label: str) -> dict:
    response: requests.Response | None = None
    for attempt in range(1, 5):
        response = client.get(url, timeout=60)
        if response.status_code != 429 and response.status_code < 500:
            response.raise_for_status()
            value = response.json()
            if not isinstance(value, dict):
                raise RuntimeError(f"{label} returned a non-object JSON value")
            return value
        if attempt < 4:
            time.sleep(attempt * 2)
    if response is None:
        raise RuntimeError(f"{label} lookup did not execute")
    response.raise_for_status()
    raise RuntimeError(f"{label} lookup failed")


def verify_public_latest(client: requests.Session, record: dict) -> bool:
    if record.get("status") != "published":
        raise RuntimeError("required public record is not published")
    identifier = record_id(record)
    versions = record.get("versions")
    has_native_flag = isinstance(versions, dict) and "is_latest" in versions
    if has_native_flag and versions.get("is_latest") is not True:
        raise RuntimeError("required public record is not the latest version")
    latest_link = record.get("links", {}).get("latest")
    if latest_link is not None:
        if not isinstance(latest_link, str) or not latest_link:
            raise RuntimeError("public latest-version link has an unexpected shape")
        latest = get_json_with_retry(client, latest_link, label="latest-version")
        if (
            record_id(latest) != identifier
            or latest.get("status") != "published"
            or concept_id(latest) != concept_id(record)
        ):
            raise RuntimeError("public latest-version link resolves to a different record")
    elif not has_native_flag:
        raise RuntimeError("public record exposes no latest-version proof")
    return True


def flatten_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in flatten_strings(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in flatten_strings(nested)]
    return []


def public_default_preview(record: dict) -> str:
    files = record.get("files")
    if isinstance(files, dict) and "default_preview" in files:
        preview = files.get("default_preview")
        if preview != build.PDF_PATH.name:
            raise RuntimeError("public default preview differs from the complete Habring PDF")
        return preview
    thumbnails = record.get("links", {}).get("thumbnails")
    urls = flatten_strings(thumbnails)
    if not urls or any(build.PDF_PATH.name not in unquote(url) for url in urls):
        raise RuntimeError("legacy public thumbnail links do not prove the default Habring PDF")
    return build.PDF_PATH.name


def public_entries(record: dict) -> dict[str, dict]:
    files = record.get("files")
    entries = files.get("entries", []) if isinstance(files, dict) else files
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise RuntimeError("unexpected public-file inventory shape")
    if any(not isinstance(item, dict) for item in entries):
        raise RuntimeError("public-file inventory contains a non-object entry")
    result = {item.get("key") or item.get("filename"): item for item in entries}
    if None in result or len(result) != len(entries):
        raise RuntimeError("public-file inventory has duplicate or missing names")
    return result


def remote_entries(client: requests.Session, record_id: str | None = None) -> dict[str, dict]:
    record_id = record_id or draft_id()
    response = client.get(f"{API}/records/{record_id}/draft/files", timeout=60)
    response.raise_for_status()
    data = response.json()
    entries = data.get("entries", data) if isinstance(data, dict) else data
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise RuntimeError("unexpected draft-file inventory shape")
    result = {item.get("key"): item for item in entries}
    if None in result or len(result) != len(entries):
        raise RuntimeError("draft-file inventory has duplicate or missing keys")
    return result


def download_entry(client: requests.Session, item: dict) -> bytes:
    links = item.get("links", {})
    url = links.get("content") or links.get("self") or links.get("download")
    if not url:
        raise RuntimeError("remote file entry lacks a download link")
    response = client.get(url, timeout=300)
    response.raise_for_status()
    return response.content


def verify_expected_bytes(client: requests.Session, entries: dict[str, dict], expected: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    verified: list[dict[str, object]] = []
    for name in sorted(expected):
        if name not in entries:
            raise RuntimeError(f"missing remote file: {name}")
        payload = download_entry(client, entries[name])
        if len(payload) != expected[name]["bytes"] or digest(payload) != expected[name]["sha256"]:
            raise RuntimeError(f"remote SHA-256 identity drift: {name}")
        verified.append({"filename": name, "bytes": len(payload), "sha256": digest(payload), "public_byte_identity": "pass"})
    return verified


def verify_parent_public() -> dict:
    client = session(authenticated=False)
    record = get_json_with_retry(
        client,
        f"{API}/records/{build.PARENT_RECORD_ID}",
        label="parent-record",
    )
    if record_id(record) != build.PARENT_RECORD_ID:
        raise RuntimeError("parent lookup returned a different record")
    if record_doi(record) != build.PARENT_RECORD_DOI:
        raise RuntimeError("required parent DOI differs from the frozen lineage")
    if concept_id(record) != build.CONCEPT_ID:
        raise RuntimeError("required parent belongs to a different concept")
    live_concept_doi = concept_doi(record)
    if live_concept_doi is not None and live_concept_doi != build.CONCEPT_DOI:
        raise RuntimeError("required parent concept DOI differs from the frozen lineage")
    verify_public_latest(client, record)
    entries = public_entries(record)
    expected = build.inherited_inventory()
    if set(entries) != set(expected):
        raise RuntimeError("live parent namespace differs from the frozen 98-file readback")
    for name, item in entries.items():
        if item.get("size") != expected[name]["bytes"]:
            raise RuntimeError(f"live parent size drift: {name}")
    return record


def get_draft(client: requests.Session, record_id: str | None = None) -> dict:
    response = client.get(f"{API}/records/{record_id or draft_id()}/draft", timeout=60)
    response.raise_for_status()
    record = response.json()
    if str(record.get("id")) != str(record_id or draft_id()):
        raise RuntimeError("draft lookup returned a different record")
    return record


def prune_superseded_additions(
    client: requests.Session,
    record_id: str,
    entries: dict[str, dict],
) -> dict[str, dict]:
    """Converge only the known failed eight-file attempt to the two-file plan."""
    inherited = set(build.inherited_inventory())
    planned = {path.name for path in build.addition_paths()}
    unexpected = set(entries) - inherited - planned
    unknown = unexpected - build.SUPERSEDED_ADDITION_NAMES
    if unknown:
        raise RuntimeError(f"draft contains unknown filenames; refusing deletion: {sorted(unknown)}")
    endpoint = f"{API}/records/{record_id}/draft/files"
    for name in sorted(unexpected):
        response = client.delete(f"{endpoint}/{quote(name, safe='')}", timeout=60)
        if response.status_code not in (200, 204, 404):
            response.raise_for_status()
    reconciled = remote_entries(client, record_id)
    if set(reconciled) - inherited - planned:
        raise RuntimeError("superseded draft additions remain after bounded deletion")
    return reconciled


def ensure_inherited_imported(client: requests.Session, record_id: str) -> dict[str, dict]:
    inherited = set(build.inherited_inventory())
    entries = remote_entries(client, record_id)
    if inherited.issubset(entries):
        return prune_superseded_additions(client, record_id, entries)
    if entries:
        raise RuntimeError("draft has a partial namespace before files-import")
    client.post(f"{API}/records/{record_id}/draft/actions/files-import", timeout=300).raise_for_status()
    for _ in range(90):
        entries = remote_entries(client, record_id)
        if inherited.issubset(entries):
            return prune_superseded_additions(client, record_id, entries)
        time.sleep(1)
    raise RuntimeError("files-import did not expose all 98 inherited files")


def assert_namespace(entries: dict[str, dict], *, require_additions: bool) -> None:
    inherited = set(build.inherited_inventory())
    additions = {path.name for path in build.addition_paths()}
    actual = set(entries)
    unexpected = actual - inherited - additions
    missing_inherited = inherited - actual
    missing_additions = additions - actual if require_additions else set()
    if unexpected or missing_inherited or missing_additions:
        raise RuntimeError(
            f"draft namespace mismatch: unexpected={sorted(unexpected)}, "
            f"missing_inherited={sorted(missing_inherited)}, missing_additions={sorted(missing_additions)}"
        )


def prepare() -> dict:
    build.validate_local_release()
    client = session()
    if STATE_PATH.is_file():
        current = state()
        if current.get("status") == "published":
            raise RuntimeError("this version is already published")
        verify_parent_public()
        record_id = str(current["draft_id"])
        get_draft(client, record_id)
    else:
        verify_parent_public()
        response = client.post(f"{API}/records/{build.PARENT_RECORD_ID}/versions", timeout=60)
        if response.status_code == 409:
            raise RuntimeError("Zenodo reports an existing new-version draft; refusing an unbound duplicate")
        response.raise_for_status()
        record_id = str(response.json()["id"])
        save_state(response.json())
    ensure_inherited_imported(client, record_id)
    response = client.put(f"{API}/records/{record_id}/draft", json=template_payload(), timeout=60)
    response.raise_for_status()
    validate_metadata_shape(response.json()["metadata"])
    return save_state(response.json())


def upload_one(client: requests.Session, endpoint: str, path: Path, existing: dict[str, dict]) -> None:
    old = existing.get(path.name)
    expected_md5 = f"md5:{file_digest(path, 'md5')}"
    if old and old.get("status") == "completed" and old.get("size") == path.stat().st_size and old.get("checksum") == expected_md5:
        return
    if old:
        client.delete(f"{endpoint}/{quote(path.name, safe='')}", timeout=60).raise_for_status()
    registration = client.post(endpoint, json=[{"key": path.name}], timeout=60)
    if not registration.ok:
        raise RuntimeError(
            f"Zenodo file registration failed for {path.name!r}: "
            f"HTTP {registration.status_code}: {registration.text[:1000]}"
        )
    with path.open("rb") as stream:
        client.put(f"{endpoint}/{quote(path.name, safe='')}/content", data=stream, headers={"Content-Type": "application/octet-stream"}, timeout=300).raise_for_status()
    client.post(f"{endpoint}/{quote(path.name, safe='')}/commit", timeout=60).raise_for_status()


def upload() -> dict:
    build.validate_local_release()
    if state().get("status") == "published":
        raise RuntimeError("version is already published; refusing upload mutation")
    client = session()
    draft = get_draft(client)
    validate_metadata_shape(draft["metadata"])
    existing = ensure_inherited_imported(client, draft_id())
    assert_namespace(existing, require_additions=False)
    endpoint = f"{API}/records/{draft_id()}/draft/files"
    order = {
        build.PDF_PATH.name: 0,
        build.COMPLETE_BUNDLE_NAME: 1,
    }
    for path in sorted(build.addition_paths(), key=lambda item: (order[item.name], item.name)):
        upload_one(client, endpoint, path, existing)
        existing = remote_entries(client)
    updated = client.put(f"{API}/records/{draft_id()}/draft", json=template_payload(), timeout=60)
    updated.raise_for_status()
    validate_metadata_shape(updated.json()["metadata"])
    validate_draft()
    return {"result": "pass", "draft_id": draft_id(), "addition_count": build.EXPECTED_ADDITION_COUNT}


def validate_draft() -> dict:
    build.validate_local_release()
    client = session()
    draft = get_draft(client)
    validate_metadata_shape(draft["metadata"])
    entries = remote_entries(client)
    assert_namespace(entries, require_additions=True)
    expected = build.local_inventory()
    for path in build.addition_paths():
        item = entries[path.name]
        if item.get("status") != "completed" or item.get("size") != path.stat().st_size or item.get("checksum") != f"md5:{file_digest(path, 'md5')}":
            raise RuntimeError(f"remote addition metadata gate failed: {path.name}")
    verify_expected_bytes(client, entries, expected)
    return draft


def readback(*, wait_for_publication: bool = False) -> dict:
    build.validate_local_release()
    client = session(authenticated=False)
    attempts = 12 if wait_for_publication else 1
    response: requests.Response | None = None
    for attempt in range(1, attempts + 1):
        response = client.get(f"{API}/records/{draft_id()}", timeout=60)
        if response.status_code == 200 and response.json().get("status") == "published":
            break
        if attempt == attempts:
            response.raise_for_status()
            raise RuntimeError("published record was not anonymously visible before the readback deadline")
        time.sleep(min(2 * attempt, 10))
    if response is None:
        raise RuntimeError("anonymous readback did not execute")
    record = response.json()
    if not isinstance(record, dict) or not isinstance(record.get("metadata"), dict):
        raise RuntimeError("anonymous public record has an unexpected shape")
    if record_id(record) != draft_id():
        raise RuntimeError("anonymous readback returned a different record")
    if concept_id(record) != build.CONCEPT_ID:
        raise RuntimeError("anonymous readback belongs to a different concept")
    live_concept_doi = concept_doi(record)
    if live_concept_doi is not None and live_concept_doi != build.CONCEPT_DOI:
        raise RuntimeError("anonymous readback concept DOI differs from the frozen lineage")
    live_record_doi = record_doi(record)
    if live_record_doi is None:
        raise RuntimeError("anonymous readback lacks a record DOI")
    bound_record_doi = state().get("draft_doi")
    if bound_record_doi is not None and live_record_doi != bound_record_doi:
        raise RuntimeError("anonymous readback DOI differs from the bound draft DOI")
    validate_public_metadata_shape(record["metadata"])
    is_latest = verify_public_latest(client, record)
    default_preview = public_default_preview(record)
    entries = public_entries(record)
    expected = build.local_inventory()
    if set(entries) != set(expected) or len(entries) != build.EXPECTED_RELEASE_COUNT:
        raise RuntimeError("anonymous public 100-file inventory mismatch")
    verified = verify_expected_bytes(client, entries, expected)
    inherited_names = set(build.inherited_inventory())
    for item in verified:
        item["disposition"] = "inherited_unchanged" if item["filename"] in inherited_names else "habring_spine_addition"
    serialized = json.dumps(record["metadata"], ensure_ascii=False)
    comprehensive_bundle_verification = build.verify_comprehensive_bundle(
        download_entry(client, entries[build.COMPLETE_BUNDLE_NAME])
    )
    receipt = {
        "schema": "o015-zenodo-habring-spine-public-readback-v2",
        "result": "pass",
        "record_id": draft_id(),
        "record_doi": live_record_doi,
        "record_url": record.get("links", {}).get("self_html") or record.get("links", {}).get("record_html"),
        "concept_id": build.CONCEPT_ID,
        "concept_doi": build.CONCEPT_DOI,
        "parent_record_id": build.PARENT_RECORD_ID,
        "parent_record_doi": build.PARENT_RECORD_DOI,
        "status": record.get("status"),
        "is_latest": is_latest,
        "default_preview": default_preview,
        "title": record["metadata"]["title"],
        "version": record["metadata"]["version"],
        "files": verified,
        "file_count": len(verified),
        "inherited_file_count": sum(item["disposition"] == "inherited_unchanged" for item in verified),
        "addition_file_count": sum(item["disposition"] == "habring_spine_addition" for item in verified),
        "inherited_identity": "pass",
        "ttp_metadata_mentions": serialized.count("TTP"),
        "model_provenance_mentions": serialized.count(build.MODEL_ID),
        "comprehensive_bundle_verification": comprehensive_bundle_verification,
        "source_backend_bundle_verification": comprehensive_bundle_verification["source_backend_bundle_verification"],
    }
    if (
        receipt["status"] != "published"
        or receipt["is_latest"] is not True
        or receipt["default_preview"] != build.PDF_PATH.name
        or receipt["file_count"] != build.EXPECTED_RELEASE_COUNT
        or receipt["inherited_file_count"] != build.EXPECTED_INHERITED_COUNT
        or receipt["addition_file_count"] != build.EXPECTED_ADDITION_COUNT
        or receipt["ttp_metadata_mentions"] != 1
        or receipt["model_provenance_mentions"] != 1
    ):
        raise RuntimeError("anonymous public state/identity gate failed")
    READBACK_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def reconcile_ambiguous_publish(record_id: str) -> dict | None:
    client = session(authenticated=False)
    for attempt in range(1, 5):
        response = client.get(f"{API}/records/{record_id}", timeout=60)
        if response.status_code == 200 and response.json().get("status") == "published":
            return response.json()
        if response.status_code not in (404, 429) and response.status_code < 500:
            response.raise_for_status()
        if attempt < 4:
            time.sleep(attempt * 2)
    return None


def publish() -> dict:
    current = state()
    if current.get("status") == "published":
        return readback(wait_for_publication=True)
    validate_draft()
    record_id = draft_id()
    try:
        response = session().post(f"{API}/records/{record_id}/draft/actions/publish", timeout=120)
        response.raise_for_status()
        published = response.json()
    except (requests.RequestException, ValueError):
        published = reconcile_ambiguous_publish(record_id)
        if published is None:
            raise
    validate_metadata_shape(published["metadata"])
    save_state(published)
    return readback(wait_for_publication=True)


def release() -> dict:
    if STATE_PATH.is_file() and state().get("status") == "published":
        return readback(wait_for_publication=True)
    prepare()
    upload()
    return publish()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "upload", "validate", "publish", "readback", "release"))
    args = parser.parse_args()
    action = {
        "prepare": prepare,
        "upload": upload,
        "validate": validate_draft,
        "publish": publish,
        "readback": readback,
        "release": release,
    }[args.action]
    print(json.dumps(action(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
