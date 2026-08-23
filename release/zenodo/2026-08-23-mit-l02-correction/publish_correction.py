#!/usr/bin/env python3
"""Prepare, upload, publish, and anonymously read back the MIT-L02 version."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import requests

import build_correction as build


HERE = Path(__file__).resolve().parent
API = "https://zenodo.org/api"
CREDENTIAL = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
TEMPLATE_PATH = HERE / "zenodo-record-mit-l02-correction.json"
STATE_PATH = HERE / "zenodo-draft-mit-l02-correction.json"
READBACK_PATH = HERE / "zenodo-public-readback-mit-l02-correction.json"
EXPECTED_TITLE = "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia (id-ID): Koreksi Checkpoint MIT 6.253 L02 (Belum Lengkap)"


def token() -> str:
    raw = CREDENTIAL.read_text(encoding="utf-8")
    match = re.search(r"zenodo_pat_[A-Za-z0-9_-]+", raw) or re.search(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])", raw)
    if not match:
        raise RuntimeError("No Zenodo credential-shaped value found")
    return match.group(0)


def session(authenticated: bool = True) -> requests.Session:
    client = requests.Session()
    client.headers["Accept"] = "application/vnd.inveniordm.v1+json"
    client.headers["User-Agent"] = "O015-id-ID-MIT-L02-preservation/1.0"
    if authenticated:
        client.headers["Authorization"] = f"Bearer {token()}"
    return client


def digest(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def file_digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def draft_doi(record: dict) -> str:
    return str(record.get("pids", {}).get("doi", {}).get("identifier") or f"10.5281/zenodo.{record['id']}")


def save_state(record: dict) -> dict:
    receipt = {"schema": "o015-zenodo-mit-l02-draft-receipt-v1", "parent_record_id": build.PARENT_RECORD_ID, "parent_record_doi": build.PARENT_RECORD_DOI, "concept_id": build.CONCEPT_ID, "concept_doi": build.CONCEPT_DOI, "draft_id": str(record["id"]), "draft_doi": draft_doi(record), "status": record.get("status"), "title": record.get("metadata", {}).get("title"), "version": record.get("metadata", {}).get("version")}
    STATE_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def state() -> dict:
    if not STATE_PATH.is_file():
        raise RuntimeError("No local MIT-L02 draft receipt; run prepare first")
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if data.get("parent_record_id") != build.PARENT_RECORD_ID or data.get("concept_id") != build.CONCEPT_ID or data.get("version") != build.VERSION:
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


def get_draft(client: requests.Session, record_id: str | None = None) -> dict:
    response = client.get(f"{API}/records/{record_id or draft_id()}/draft", timeout=60)
    response.raise_for_status()
    return response.json()


def remote_entries(client: requests.Session, record_id: str | None = None) -> dict[str, dict]:
    response = client.get(f"{API}/records/{record_id or draft_id()}/draft/files", timeout=60)
    response.raise_for_status()
    return normalize_entries(response.json().get("entries", []))


def public_entries(record: dict) -> dict[str, dict]:
    return normalize_entries(record.get("files", {}).get("entries", []))


def validate_metadata_shape(metadata: dict) -> None:
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    if title != EXPECTED_TITLE or metadata.get("version") != build.VERSION or metadata.get("publication_date") != "2026-08-23":
        raise RuntimeError("MIT-L02 correction title/version/date metadata mismatch")
    if "TTP" in title or "TTP" in description or serialized.count("TTP") != 1:
        raise RuntimeError("organizational metadata must contain one TTP entry and none in title/description")
    if serialized.count("OpenAI Codex gpt-5.6-sol, Ultra") != 1:
        raise RuntimeError("exact model provenance must occur once")
    lowered = description.lower()
    for required in ("halaman 6-13", "halaman 14", "belum lengkap", "induk", "koreksi", "cc by-nc-sa 4.0"):
        if required not in lowered:
            raise RuntimeError(f"description lacks {required!r}")
    rights = [item.get("id") or item.get("title", {}).get("en", "") for item in metadata.get("rights", [])]
    if "cc-by-nc-sa-4.0" not in rights or "cc-by-4.0" not in rights or not any("3.0 United States" in item for item in rights) or not any("Royer source" in item for item in rights):
        raise RuntimeError("component-specific rights metadata is incomplete")
    contributors = [item for item in metadata.get("contributors", []) if item.get("person_or_org", {}).get("name") == "TTP"]
    if len(contributors) != 1 or contributors[0].get("person_or_org", {}).get("type") != "organizational":
        raise RuntimeError("TTP must be exactly one organizational contributor")


def download_entry(client: requests.Session, item: dict) -> bytes:
    link = item.get("links", {}).get("content")
    if not link:
        raise RuntimeError(f"no content link for remote file {item.get('key')}")
    response = client.get(link, headers={"Accept": "*/*"}, timeout=300)
    response.raise_for_status()
    return response.content


def verify_expected_bytes(client: requests.Session, entries: dict[str, dict], expected: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    verified = []
    for name in sorted(expected):
        if name not in entries:
            raise RuntimeError(f"missing remote file: {name}")
        payload = download_entry(client, entries[name])
        if len(payload) != expected[name]["bytes"] or digest(payload) != expected[name]["sha256"]:
            raise RuntimeError(f"remote SHA-256 identity drift: {name}")
        verified.append({"filename": name, "bytes": len(payload), "sha256": digest(payload), "public_byte_identity": "pass"})
    return verified


def ensure_inherited_imported(client: requests.Session, record_id: str) -> dict[str, dict]:
    inherited = set(build.inherited_inventory())
    entries = remote_entries(client, record_id)
    if inherited.issubset(set(entries)):
        return entries
    if entries:
        raise RuntimeError("draft has a partial/unexpected namespace before files-import")
    response = client.post(f"{API}/records/{record_id}/draft/actions/files-import", timeout=300)
    response.raise_for_status()
    for _ in range(60):
        entries = remote_entries(client, record_id)
        if inherited.issubset(set(entries)):
            return entries
        time.sleep(1)
    raise RuntimeError("files-import did not expose all inherited files")


def assert_namespace(entries: dict[str, dict], require_additions: bool) -> None:
    inherited = set(build.inherited_inventory())
    additions = {path.name for path in build.addition_paths()}
    actual = set(entries)
    unexpected = actual - inherited - additions
    missing_inherited = inherited - actual
    missing_additions = additions - actual if require_additions else set()
    if unexpected or missing_inherited or missing_additions:
        raise RuntimeError(f"draft namespace mismatch: unexpected={sorted(unexpected)}, missing_inherited={sorted(missing_inherited)}, missing_additions={sorted(missing_additions)}")


def verify_parent_public() -> dict:
    client = session(authenticated=False)
    response = client.get(f"{API}/records/{build.PARENT_RECORD_ID}", timeout=60)
    response.raise_for_status()
    record = response.json()
    if record.get("status") != "published":
        raise RuntimeError("required parent is not published")
    entries = public_entries(record)
    expected = build.inherited_inventory()
    if set(entries) != set(expected):
        raise RuntimeError("parent inventory differs from the frozen 32-file readback")
    verify_expected_bytes(client, entries, expected)
    return record


def bind_manifest() -> None:
    verification = build.verify_bundle((HERE / build.BUNDLE_NAME).read_bytes())
    build.build_release_metadata(verification)


def prepare() -> dict:
    build.validate_local_release()
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    validate_metadata_shape(template["metadata"])
    client = session()
    if STATE_PATH.is_file():
        receipt = state()
        existing = get_draft(client, receipt["draft_id"])
        updated = client.put(f"{API}/records/{receipt['draft_id']}/draft", json=template, timeout=60)
        updated.raise_for_status()
        record = updated.json()
        validate_metadata_shape(record["metadata"])
        save_state(record)
        ensure_inherited_imported(client, str(receipt["draft_id"]))
        bind_manifest()
        return state()
    verify_parent_public()
    response = client.post(f"{API}/records/{build.PARENT_RECORD_ID}/versions", timeout=60)
    response.raise_for_status()
    created = response.json()
    ensure_inherited_imported(client, str(created["id"]))
    updated = client.put(f"{API}/records/{created['id']}/draft", json=template, timeout=60)
    updated.raise_for_status()
    record = updated.json()
    validate_metadata_shape(record["metadata"])
    saved = save_state(record)
    bind_manifest()
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
        client.put(f"{endpoint}/{path.name}/content", data=stream, headers={"Content-Type": "application/octet-stream"}, timeout=300).raise_for_status()
    client.post(f"{endpoint}/{path.name}/commit", timeout=60).raise_for_status()


def validate_draft() -> dict:
    build.validate_local_release(require_draft_binding=True)
    client = session()
    draft = get_draft(client)
    validate_metadata_shape(draft["metadata"])
    entries = remote_entries(client)
    assert_namespace(entries, True)
    expected = build.local_inventory()
    for name, path in {path.name: path for path in build.addition_paths()}.items():
        item = entries[name]
        if item.get("status") != "completed" or item.get("size") != path.stat().st_size or item.get("checksum") != f"md5:{file_digest(path, 'md5')}":
            raise RuntimeError(f"remote addition gate failed: {name}")
    verify_expected_bytes(client, entries, expected)
    return draft


def upload() -> dict:
    client = session()
    draft = get_draft(client)
    validate_metadata_shape(draft["metadata"])
    existing = remote_entries(client)
    assert_namespace(existing, False)
    endpoint = f"{API}/records/{draft_id()}/draft/files"
    for path in sorted(build.addition_paths(), key=lambda item: item.name):
        upload_one(client, endpoint, path, existing)
        existing = remote_entries(client)
    validate_draft()
    return {"result": "pass", "draft_id": draft_id(), "replacement_count": 3}


def publish() -> dict:
    validate_draft()
    response = session().post(f"{API}/records/{draft_id()}/draft/actions/publish", timeout=120)
    response.raise_for_status()
    return save_state(response.json())


def readback() -> dict:
    build.validate_local_release(require_draft_binding=True)
    client = session(authenticated=False)
    response = client.get(f"{API}/records/{draft_id()}", timeout=60)
    response.raise_for_status()
    record = response.json()
    validate_metadata_shape(record["metadata"])
    entries = public_entries(record)
    expected = build.local_inventory()
    if set(entries) != set(expected) or len(entries) != 32:
        raise RuntimeError("anonymous public 32-file inventory mismatch")
    verified = verify_expected_bytes(client, entries, expected)
    inherited_names = set(build.inherited_inventory())
    replacement_names = {path.name for path in build.addition_paths()}
    for item in verified:
        item["disposition"] = "replacement" if item["filename"] in replacement_names else "inherited_unchanged"
    bundle_payload = download_entry(client, entries[build.BUNDLE_NAME])
    receipt = {"schema": "o015-zenodo-mit-l02-correction-public-readback-v1", "record_id": draft_id(), "record_doi": record.get("pids", {}).get("doi", {}).get("identifier") or record.get("metadata", {}).get("doi"), "record_url": record.get("links", {}).get("self_html"), "concept_id": build.CONCEPT_ID, "concept_doi": build.CONCEPT_DOI, "parent_record_id": build.PARENT_RECORD_ID, "status": record.get("status"), "title": record["metadata"]["title"], "version": record["metadata"]["version"], "publication_date": record["metadata"]["publication_date"], "resource_type": record["metadata"]["resource_type"]["id"], "creator_names": [item["person_or_org"]["name"] for item in record["metadata"]["creators"]], "contributor_names": [item["person_or_org"]["name"] for item in record["metadata"].get("contributors", [])], "ttp_metadata_mentions": json.dumps(record["metadata"], ensure_ascii=False).count("TTP"), "model_provenance_mentions": json.dumps(record["metadata"], ensure_ascii=False).count("OpenAI Codex gpt-5.6-sol, Ultra"), "files": verified, "file_count": len(verified), "inherited_file_count": sum(item["disposition"] == "inherited_unchanged" for item in verified), "replacement_file_count": sum(item["disposition"] == "replacement" for item in verified), "inherited_identity": "pass", "delta_bundle_verification": build.verify_bundle(bundle_payload)}
    if receipt["status"] != "published" or receipt["file_count"] != 32 or receipt["inherited_file_count"] != 29 or receipt["replacement_file_count"] != 3 or receipt["ttp_metadata_mentions"] != 1 or receipt["model_provenance_mentions"] != 1:
        raise RuntimeError("anonymous public state/identity gate failed")
    READBACK_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "upload", "validate", "publish", "readback"))
    args = parser.parse_args()
    result = {"prepare": prepare, "upload": upload, "validate": validate_draft, "publish": publish, "readback": readback}[args.action]()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
