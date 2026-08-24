#!/usr/bin/env python3
"""Fail-closed Zenodo publisher and anonymous readback for MIT L10.

Importing this module performs no network or credential operation.  Every
mutation first runs the deterministic local release gate.  Draft creation or
upload alone is never reported as publication; successful publication is
followed by anonymous exact-byte readback of all 90 files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import requests

import build_l10 as build


HERE = Path(__file__).resolve().parent
API = "https://zenodo.org/api"
CREDENTIAL = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
TEMPLATE_PATH = HERE / "zenodo-record-mit-l10.json"
STATE_PATH = HERE / "zenodo-draft-mit-l10.json"
READBACK_PATH = HERE / "zenodo-public-readback-mit-l10.json"
EXPECTED_TITLE = "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia (id-ID): Checkpoint MIT 6.253 Kuliah 6, Halaman 64-85 (Belum Lengkap)"


def token() -> str:
    raw = CREDENTIAL.read_text(encoding="utf-8")
    match = re.search(r"zenodo_pat_[A-Za-z0-9_-]+", raw) or re.search(
        r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])", raw
    )
    if not match:
        raise RuntimeError("No Zenodo credential-shaped value found")
    return match.group(0)


def session(authenticated: bool = True) -> requests.Session:
    client = requests.Session()
    client.headers["Accept"] = "application/vnd.inveniordm.v1+json"
    client.headers["User-Agent"] = "O015-id-ID-MIT-L10-preservation/1.0"
    if authenticated:
        client.headers["Authorization"] = f"Bearer {token()}"
    return client


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def draft_doi(record: dict) -> str:
    return str(record.get("pids", {}).get("doi", {}).get("identifier") or f"10.5281/zenodo.{record['id']}")


def save_state(record: dict) -> dict:
    receipt = {
        "schema": "o015-zenodo-mit-l10-draft-receipt-v1",
        "parent_record_id": build.PARENT_RECORD_ID,
        "parent_record_doi": build.PARENT_RECORD_DOI,
        "concept_id": build.CONCEPT_ID,
        "concept_doi": build.CONCEPT_DOI,
        "draft_id": str(record["id"]),
        "draft_doi": draft_doi(record),
        "status": record.get("status"),
        "title": record.get("metadata", {}).get("title"),
        "version": build.VERSION,
    }
    STATE_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


def state() -> dict:
    if not STATE_PATH.is_file():
        raise RuntimeError("No local MIT-L10 draft receipt; run prepare first")
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if (
        data.get("schema") != "o015-zenodo-mit-l10-draft-receipt-v1"
        or data.get("parent_record_id") != build.PARENT_RECORD_ID
        or data.get("parent_record_doi") != build.PARENT_RECORD_DOI
        or data.get("concept_id") != build.CONCEPT_ID
        or data.get("concept_doi") != build.CONCEPT_DOI
        or data.get("version") != build.VERSION
    ):
        raise RuntimeError("local draft receipt belongs to a different lineage/version")
    return data


def draft_id() -> str:
    return str(state()["draft_id"])


def normalize_entries(entries: object) -> dict[str, dict]:
    values = entries.values() if isinstance(entries, dict) else entries if isinstance(entries, list) else []
    values = list(values)
    result = {str(item["key"]): item for item in values}
    if len(result) != len(values):
        raise RuntimeError("remote file inventory has duplicate keys")
    return result


def public_entries(record: dict) -> dict[str, dict]:
    return normalize_entries(record.get("files", {}).get("entries", []))


def get_draft(client: requests.Session, record_id: str | None = None) -> dict:
    response = client.get(f"{API}/records/{record_id or draft_id()}/draft", timeout=60)
    response.raise_for_status()
    record = response.json()
    if str(record.get("parent", {}).get("id")) != build.CONCEPT_ID:
        raise RuntimeError("remote draft belongs to a different concept lineage")
    return record


def remote_entries(client: requests.Session, record_id: str | None = None) -> dict[str, dict]:
    response = client.get(f"{API}/records/{record_id or draft_id()}/draft/files", timeout=60)
    response.raise_for_status()
    return normalize_entries(response.json().get("entries", []))


def validate_metadata_shape(metadata: dict) -> None:
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    if title != EXPECTED_TITLE or metadata.get("version") != build.VERSION or metadata.get("publication_date") != "2026-08-24":
        raise RuntimeError("MIT-L10 title/version/date metadata mismatch")
    if (
        "TTP" in title
        or "TTP" in description
        or serialized.count("TTP") != 1
        or build.FORBIDDEN_ORG_EXPANSION.casefold() in serialized.casefold()
    ):
        raise RuntimeError("organizational metadata must contain one short contributor entry and no expansion")
    if serialized.count(build.MODEL_ID) != 1:
        raise RuntimeError("exact model provenance must occur once")
    lowered = description.lower()
    for required in (
        "halaman 64-85",
        "halaman 86",
        "belum lengkap",
        "82 berkas induk",
        "tepat delapan berkas",
        "cc by-nc-sa 4.0",
        "16 blok relasi gambar",
        "o015-mit-sem-0030",
    ):
        if required not in lowered:
            raise RuntimeError(f"description lacks {required!r}")
    rights = [item.get("id") or item.get("title", {}).get("en", "") for item in metadata.get("rights", [])]
    if (
        "cc-by-nc-sa-4.0" not in rights
        or "cc-by-4.0" not in rights
        or not any("3.0 United States" in item for item in rights)
        or not any("Royer source" in item for item in rights)
    ):
        raise RuntimeError("component-specific rights metadata is incomplete")
    ttp = [item for item in metadata.get("contributors", []) if item.get("person_or_org", {}).get("name") == "TTP"]
    if len(ttp) != 1 or ttp[0].get("person_or_org", {}).get("type") != "organizational":
        raise RuntimeError("the short organization entry must occur exactly once as a contributor")


def validate_record_shape(record: dict, require_preview: bool = True) -> None:
    if str(record.get("parent", {}).get("id")) != build.CONCEPT_ID:
        raise RuntimeError("remote record belongs to a different concept lineage")
    validate_metadata_shape(record.get("metadata", {}))
    if require_preview and record.get("files", {}).get("default_preview") != build.READER_PATHS[0].name:
        raise RuntimeError("remote record does not make the L10 PDF its default preview")


def template_payload(include_preview: bool) -> dict:
    payload = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    validate_metadata_shape(payload["metadata"])
    if payload.get("files", {}).get("default_preview") != build.READER_PATHS[0].name:
        raise RuntimeError("local metadata template lacks the required L10 PDF preview")
    if not include_preview:
        payload["files"] = {"enabled": True}
    return payload


def download_entry(client: requests.Session, item: dict) -> bytes:
    link = item.get("links", {}).get("content")
    if not link:
        raise RuntimeError(f"no content link for remote file {item.get('key')}")
    for attempt in range(1, 5):
        try:
            response = client.get(link, headers={"Accept": "*/*"}, timeout=300)
            if response.status_code >= 500 and attempt < 4:
                time.sleep(attempt * 2)
                continue
            response.raise_for_status()
            return response.content
        except requests.RequestException:
            if attempt == 4:
                raise
            time.sleep(attempt * 2)
    raise RuntimeError(f"download failed for {item.get('key')}")


def verify_expected_bytes(
    client: requests.Session,
    entries: dict[str, dict],
    expected: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    verified = []
    for name in sorted(expected):
        if name not in entries:
            raise RuntimeError(f"missing remote file: {name}")
        payload = download_entry(client, entries[name])
        if len(payload) != expected[name]["bytes"] or digest(payload) != expected[name]["sha256"]:
            raise RuntimeError(f"remote SHA-256 identity drift: {name}")
        verified.append(
            {
                "filename": name,
                "bytes": len(payload),
                "sha256": digest(payload),
                "public_byte_identity": "pass",
            }
        )
    return verified


def verify_parent_public() -> dict:
    client = session(authenticated=False)
    response: requests.Response | None = None
    for attempt in range(1, 5):
        response = client.get(f"{API}/records/{build.PARENT_RECORD_ID}", timeout=60)
        if response.status_code < 500 or attempt == 4:
            response.raise_for_status()
            break
        time.sleep(attempt * 2)
    if response is None:
        raise RuntimeError("parent lookup did not execute")
    record = response.json()
    if record.get("status") != "published":
        raise RuntimeError("required parent is not published")
    latest_link = record.get("links", {}).get("latest")
    if record.get("versions", {}).get("is_latest") is not True or not latest_link:
        raise RuntimeError("required parent is not proved to be the latest public version")
    latest_response = client.get(latest_link, timeout=60)
    latest_response.raise_for_status()
    latest = latest_response.json()
    if str(latest.get("id")) != build.PARENT_RECORD_ID or latest.get("status") != "published":
        raise RuntimeError("concept latest-version resolution does not equal required parent 22076259")
    if str(latest.get("parent", {}).get("id")) != build.CONCEPT_ID:
        raise RuntimeError("resolved parent belongs to a different concept")
    entries = public_entries(record)
    expected = build.inherited_inventory()
    if set(entries) != set(expected):
        raise RuntimeError("parent inventory differs from the frozen 82-file readback")
    for name, item in entries.items():
        if item.get("size") != expected[name]["bytes"]:
            raise RuntimeError(f"parent public size drift: {name}")
    return record


def ensure_inherited_imported(client: requests.Session, record_id: str) -> dict[str, dict]:
    inherited = set(build.inherited_inventory())
    additions = {path.name for path in build.addition_paths()}
    entries = remote_entries(client, record_id)
    if inherited.issubset(set(entries)):
        if set(entries) - inherited - additions:
            raise RuntimeError("draft contains an unexpected filename")
        return entries
    if entries:
        raise RuntimeError("draft has a partial/unexpected namespace before files-import")
    client.post(f"{API}/records/{record_id}/draft/actions/files-import", timeout=300).raise_for_status()
    for _ in range(90):
        entries = remote_entries(client, record_id)
        if inherited.issubset(set(entries)):
            if set(entries) - inherited - additions:
                raise RuntimeError("files-import exposed an unexpected filename")
            return entries
        time.sleep(1)
    raise RuntimeError("files-import did not expose all 82 inherited files")


def assert_namespace(entries: dict[str, dict], require_additions: bool) -> None:
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


def bind_local_release() -> None:
    build.build_all()
    build.validate_local_release(require_draft_binding=True)


def prepare() -> dict:
    build.build_all()
    client = session()
    if STATE_PATH.is_file():
        receipt = state()
        if receipt.get("status") == "published":
            raise RuntimeError("this version is already published; refusing another draft")
        verify_parent_public()
        record_id = str(receipt["draft_id"])
        get_draft(client, record_id)
        updated = client.put(f"{API}/records/{record_id}/draft", json=template_payload(False), timeout=60)
        updated.raise_for_status()
        validate_metadata_shape(updated.json()["metadata"])
        save_state(updated.json())
        ensure_inherited_imported(client, record_id)
        bind_local_release()
        return state()
    verify_parent_public()
    response = client.post(f"{API}/records/{build.PARENT_RECORD_ID}/versions", timeout=60)
    if response.status_code == 409:
        raise RuntimeError("Zenodo reports an existing new-version draft; refusing an unbound duplicate")
    response.raise_for_status()
    created = response.json()
    save_state(created)
    record_id = str(created["id"])
    ensure_inherited_imported(client, record_id)
    updated = client.put(f"{API}/records/{record_id}/draft", json=template_payload(False), timeout=60)
    updated.raise_for_status()
    validate_metadata_shape(updated.json()["metadata"])
    saved = save_state(updated.json())
    bind_local_release()
    return saved


def upload_one(client: requests.Session, endpoint: str, path: Path, existing: dict[str, dict]) -> None:
    old = existing.get(path.name)
    md5 = f"md5:{file_digest(path, 'md5')}"
    if old and old.get("status") == "completed" and old.get("size") == path.stat().st_size and old.get("checksum") == md5:
        return
    if old:
        client.delete(f"{endpoint}/{path.name}", timeout=60).raise_for_status()
    client.post(endpoint, json=[{"key": path.name}], timeout=60).raise_for_status()
    with path.open("rb") as stream:
        client.put(
            f"{endpoint}/{path.name}/content",
            data=stream,
            headers={"Content-Type": "application/octet-stream"},
            timeout=300,
        ).raise_for_status()
    client.post(f"{endpoint}/{path.name}/commit", timeout=60).raise_for_status()


def validate_draft() -> dict:
    if state().get("status") == "published":
        raise RuntimeError("version is already published; draft validation is no longer applicable")
    build.validate_local_release(require_draft_binding=True)
    client = session()
    draft = get_draft(client)
    validate_record_shape(draft)
    entries = remote_entries(client)
    assert_namespace(entries, True)
    expected = build.local_inventory()
    for name, path in {path.name: path for path in build.addition_paths()}.items():
        item = entries[name]
        if (
            item.get("status") != "completed"
            or item.get("size") != path.stat().st_size
            or item.get("checksum") != f"md5:{file_digest(path, 'md5')}"
        ):
            raise RuntimeError(f"remote addition gate failed: {name}")
    verify_expected_bytes(client, entries, expected)
    return draft


def upload() -> dict:
    if state().get("status") == "published":
        raise RuntimeError("version is already published; refusing an upload mutation")
    build.validate_local_release(require_draft_binding=True)
    client = session()
    draft = get_draft(client)
    validate_metadata_shape(draft["metadata"])
    existing = remote_entries(client)
    assert_namespace(existing, False)
    endpoint = f"{API}/records/{draft_id()}/draft/files"
    order = {build.READER_PATHS[0].name: 0, build.READER_PATHS[1].name: 1}
    for path in sorted(build.addition_paths(), key=lambda item: (order.get(item.name, 2), item.name)):
        upload_one(client, endpoint, path, existing)
        existing = remote_entries(client)
    updated = client.put(f"{API}/records/{draft_id()}/draft", json=template_payload(True), timeout=60)
    updated.raise_for_status()
    validate_record_shape(updated.json())
    validate_draft()
    return {"result": "pass", "draft_id": draft_id(), "addition_count": build.EXPECTED_ADDITION_COUNT}


def readback(wait_for_publication: bool = False) -> dict:
    build.validate_local_release(require_draft_binding=True)
    client = session(authenticated=False)
    response: requests.Response | None = None
    attempts = 12 if wait_for_publication else 1
    for attempt in range(1, attempts + 1):
        response = client.get(f"{API}/records/{draft_id()}", timeout=60)
        if response.status_code == 200 and response.json().get("status") == "published":
            break
        if attempt == attempts:
            response.raise_for_status()
            raise RuntimeError("published record was not anonymously visible before the readback deadline")
        time.sleep(min(2 * attempt, 10))
    if response is None:
        raise RuntimeError("public readback did not execute")
    record = response.json()
    validate_record_shape(record)
    entries = public_entries(record)
    expected = build.local_inventory()
    if set(entries) != set(expected) or len(entries) != build.EXPECTED_RELEASE_COUNT:
        raise RuntimeError("anonymous public 90-file inventory mismatch")
    verified = verify_expected_bytes(client, entries, expected)
    inherited_names = set(build.inherited_inventory())
    for item in verified:
        item["disposition"] = "inherited_unchanged" if item["filename"] in inherited_names else "mit_l10_addition"
    serialized = json.dumps(record["metadata"], ensure_ascii=False)
    receipt = {
        "schema": "o015-zenodo-mit-l10-public-readback-v1",
        "result": "pass",
        "record_id": draft_id(),
        "record_doi": record.get("pids", {}).get("doi", {}).get("identifier") or record.get("metadata", {}).get("doi"),
        "record_url": record.get("links", {}).get("self_html"),
        "concept_id": build.CONCEPT_ID,
        "concept_doi": build.CONCEPT_DOI,
        "parent_record_id": build.PARENT_RECORD_ID,
        "parent_record_doi": build.PARENT_RECORD_DOI,
        "status": record.get("status"),
        "is_latest": record.get("versions", {}).get("is_latest"),
        "default_preview": record.get("files", {}).get("default_preview"),
        "title": record["metadata"]["title"],
        "version": record["metadata"]["version"],
        "publication_date": record["metadata"]["publication_date"],
        "resource_type": record["metadata"]["resource_type"]["id"],
        "creator_names": [item["person_or_org"]["name"] for item in record["metadata"]["creators"]],
        "contributor_names": [item["person_or_org"]["name"] for item in record["metadata"].get("contributors", [])],
        "ttp_metadata_mentions": serialized.count("TTP"),
        "model_provenance_mentions": serialized.count(build.MODEL_ID),
        "files": verified,
        "file_count": len(verified),
        "inherited_file_count": sum(item["disposition"] == "inherited_unchanged" for item in verified),
        "addition_file_count": sum(item["disposition"] == "mit_l10_addition" for item in verified),
        "inherited_identity": "pass",
        "delta_bundle_verification": build.verify_bundle(download_entry(client, entries[build.BUNDLE_NAME])),
    }
    if (
        receipt["result"] != "pass"
        or receipt["status"] != "published"
        or receipt["is_latest"] is not True
        or receipt["default_preview"] != build.READER_PATHS[0].name
        or receipt["file_count"] != build.EXPECTED_RELEASE_COUNT
        or receipt["inherited_file_count"] != build.EXPECTED_INHERITED_COUNT
        or receipt["addition_file_count"] != build.EXPECTED_ADDITION_COUNT
        or receipt["ttp_metadata_mentions"] != 1
        or receipt["model_provenance_mentions"] != 1
    ):
        raise RuntimeError("anonymous public state/identity gate failed")
    READBACK_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


def reconcile_ambiguous_publish(record_id: str) -> dict | None:
    client = session(authenticated=False)
    for attempt in range(1, 5):
        response = client.get(f"{API}/records/{record_id}", timeout=60)
        if response.status_code == 200 and response.json().get("status") == "published":
            candidate = response.json()
            validate_record_shape(candidate)
            return candidate
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
    validate_record_shape(published)
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
