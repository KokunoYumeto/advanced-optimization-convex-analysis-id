#!/usr/bin/env python3
"""Prepare, add, validate, publish, and read back the MIT-L01 Zenodo version.

The prior sixteen files are immutable inherited objects.  This publisher is
allowed to create, replace, or resume only the eight collision-proof additions.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import requests

import build_checkpoint as build


HERE = Path(__file__).resolve().parent
API = "https://zenodo.org/api"
CREDENTIAL = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
TEMPLATE_PATH = HERE / "zenodo-record-mit-l01.json"
READBACK_PATH = HERE / "zenodo-public-readback-mit-l01.json"
EXPECTED_TITLE = "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia (id-ID): Checkpoint MIT 6.253 L01 (Belum Lengkap)"


def token() -> str:
    raw = CREDENTIAL.read_text(encoding="utf-8")
    match = re.search(r"zenodo_pat_[A-Za-z0-9_-]+", raw)
    if not match:
        match = re.search(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])", raw)
    if not match:
        raise RuntimeError("No Zenodo credential-shaped value found")
    return match.group(0)


def session(authenticated: bool = True) -> requests.Session:
    result = requests.Session()
    result.headers["Accept"] = "application/vnd.inveniordm.v1+json"
    result.headers["User-Agent"] = "O015-id-ID-MIT-L01-preservation/1.0"
    if authenticated:
        result.headers["Authorization"] = f"Bearer {token()}"
    return result


def file_digest(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def digest(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def draft_doi(record: dict) -> str:
    identifier = record.get("pids", {}).get("doi", {}).get("identifier")
    return str(identifier or f"10.5281/zenodo.{record['id']}")


def save_state(record: dict) -> dict:
    receipt = {
        "schema": "o015-zenodo-mit-l01-draft-receipt-v1",
        "parent_record_id": build.PARENT_RECORD_ID,
        "parent_record_doi": build.PARENT_RECORD_DOI,
        "concept_id": build.CONCEPT_ID,
        "concept_doi": build.CONCEPT_DOI,
        "draft_id": str(record["id"]),
        "draft_doi": draft_doi(record),
        "status": record.get("status"),
        "title": record.get("metadata", {}).get("title"),
        "version": record.get("metadata", {}).get("version"),
    }
    build.STATE_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


def state() -> dict:
    if not build.STATE_PATH.is_file():
        raise RuntimeError("No local MIT-L01 draft receipt; run prepare first")
    data = json.loads(build.STATE_PATH.read_text(encoding="utf-8"))
    if (
        data.get("parent_record_id") != build.PARENT_RECORD_ID
        or data.get("concept_id") != build.CONCEPT_ID
        or data.get("version") != build.VERSION
    ):
        raise RuntimeError("Local draft receipt belongs to a different lineage/version")
    return data


def draft_id() -> str:
    return str(state()["draft_id"])


def get_draft(client: requests.Session, record_id: str | None = None) -> dict:
    response = client.get(f"{API}/records/{record_id or draft_id()}/draft", timeout=60)
    response.raise_for_status()
    return response.json()


def normalize_entries(entries: object) -> dict[str, dict]:
    if isinstance(entries, dict):
        values = entries.values()
    elif isinstance(entries, list):
        values = entries
    else:
        values = []
    result = {str(item["key"]): item for item in values}
    if len(result) != len(list(values)) if not isinstance(entries, dict) else len(result) != len(entries):
        raise RuntimeError("Remote file inventory has duplicate keys")
    return result


def public_entries(record: dict) -> dict[str, dict]:
    return normalize_entries(record.get("files", {}).get("entries", []))


def remote_entries(client: requests.Session) -> dict[str, dict]:
    response = client.get(f"{API}/records/{draft_id()}/draft/files", timeout=60)
    response.raise_for_status()
    return normalize_entries(response.json().get("entries", []))


def validate_metadata_shape(metadata: dict) -> None:
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    if title != EXPECTED_TITLE or metadata.get("version") != build.VERSION:
        raise RuntimeError("MIT-L01 title/version metadata mismatch")
    if metadata.get("publication_date") != "2026-08-23":
        raise RuntimeError("MIT-L01 publication date mismatch")
    if "TTP" in title or "TTP" in description or serialized.count("TTP") != 1:
        raise RuntimeError("Expected one organizational TTP entry and no title/description mention")
    if serialized.count("OpenAI Codex gpt-5.6-sol, Ultra") != 1:
        raise RuntimeError("Exact model provenance must occur once")
    lowered = description.lower()
    required_text = ["belum lengkap", "halaman 2-5", "halaman 6-13", "keenam belas", "royer", "pembekuan sumber"]
    if any(item not in lowered for item in required_text):
        raise RuntimeError("Coverage, inheritance, or Royer source-freeze caveat is absent")
    rights = [item.get("id") or item.get("title", {}).get("en", "") for item in metadata.get("rights", [])]
    if "cc-by-nc-sa-4.0" not in rights or "cc-by-4.0" not in rights:
        raise RuntimeError("MIT or Habring machine-readable component right is absent")
    if not any("3.0 United States" in item for item in rights) or not any("Royer source-freeze" in item for item in rights):
        raise RuntimeError("Penn or Royer component-specific right is absent")
    ttp = [
        item for item in metadata.get("contributors", [])
        if item.get("person_or_org", {}).get("name") == "TTP"
    ]
    if len(ttp) != 1 or ttp[0].get("person_or_org", {}).get("type") != "organizational":
        raise RuntimeError("TTP must be exactly one organizational contributor")


def download_entry(client: requests.Session, item: dict) -> bytes:
    link = item.get("links", {}).get("content")
    if not link:
        raise RuntimeError(f"No content link for remote file {item.get('key')}")
    response = client.get(link, headers={"Accept": "*/*"}, timeout=300)
    response.raise_for_status()
    return response.content


def verify_expected_bytes(client: requests.Session, entries: dict[str, dict], expected: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    verified = []
    for name in sorted(expected):
        if name not in entries:
            raise RuntimeError(f"Missing remote file: {name}")
        item = entries[name]
        data = download_entry(client, item)
        identity = expected[name]
        if len(data) != identity["bytes"] or digest(data) != identity["sha256"]:
            raise RuntimeError(f"Remote SHA-256 identity drift: {name}")
        verified.append({"filename": name, "bytes": len(data), "sha256": digest(data), "public_byte_identity": "pass"})
    return verified


def allowed_names() -> tuple[set[str], set[str]]:
    inherited = set(build.inherited_inventory())
    additions = {path.name for path in build.addition_paths()}
    if inherited & additions or len(inherited) != 16 or len(additions) != 8:
        raise RuntimeError("Local inherited/addition namespace gate failed")
    return inherited, additions


def assert_draft_namespace(entries: dict[str, dict], require_all_additions: bool) -> None:
    inherited, additions = allowed_names()
    actual = set(entries)
    unexpected = actual - inherited - additions
    missing_inherited = inherited - actual
    missing_additions = additions - actual if require_all_additions else set()
    if unexpected or missing_inherited or missing_additions:
        raise RuntimeError(
            f"Draft namespace mismatch: unexpected={sorted(unexpected)}, "
            f"missing_inherited={sorted(missing_inherited)}, missing_additions={sorted(missing_additions)}"
        )


def verify_parent_public() -> dict:
    client = session(authenticated=False)
    response = client.get(f"{API}/records/{build.PARENT_RECORD_ID}", timeout=60)
    response.raise_for_status()
    record = response.json()
    if record.get("status") != "published":
        raise RuntimeError("Required parent is not published")
    concept = str(record.get("parent", {}).get("id") or "")
    if concept and concept != build.CONCEPT_ID:
        raise RuntimeError("Required parent concept mismatch")
    entries = public_entries(record)
    if set(entries) != set(build.inherited_inventory()):
        raise RuntimeError("Parent public inventory differs from the frozen sixteen-file readback")
    verify_expected_bytes(client, entries, build.inherited_inventory())
    return record


def verify_draft_inherited(client: requests.Session, entries: dict[str, dict] | None = None) -> None:
    entries = entries or remote_entries(client)
    assert_draft_namespace(entries, require_all_additions=False)
    verify_expected_bytes(client, entries, build.inherited_inventory())


def prepare() -> dict:
    build.validate_local_release(require_draft_binding=False)
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    validate_metadata_shape(template["metadata"])
    client = session()

    if build.STATE_PATH.is_file():
        receipt = state()
        try:
            existing = get_draft(client, str(receipt["draft_id"]))
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                public = session(authenticated=False).get(f"{API}/records/{receipt['draft_id']}", timeout=60)
                if public.status_code == 200 and public.json().get("status") == "published":
                    return save_state(public.json())
            raise
        response = client.put(f"{API}/records/{receipt['draft_id']}/draft", json=template, timeout=60)
        response.raise_for_status()
        updated = response.json()
        validate_metadata_shape(updated["metadata"])
        saved = save_state(updated)
        verify_draft_inherited(client)
        return saved

    verify_parent_public()
    response = client.post(f"{API}/records/{build.PARENT_RECORD_ID}/versions", timeout=60)
    response.raise_for_status()
    created = response.json()
    response = client.put(f"{API}/records/{created['id']}/draft", json=template, timeout=60)
    response.raise_for_status()
    updated = response.json()
    validate_metadata_shape(updated["metadata"])
    saved = save_state(updated)
    verify_draft_inherited(client)
    return saved


def upload_one(client: requests.Session, endpoint: str, path: Path, existing: dict[str, dict]) -> None:
    name = path.name
    old = existing.get(name)
    expected_md5 = f"md5:{file_digest(path, 'md5')}"
    if old and old.get("status") == "completed" and old.get("size") == path.stat().st_size and old.get("checksum") == expected_md5:
        print(f"SKIP_ADDITION\t{name}\t{path.stat().st_size}\t{file_digest(path, 'sha256')}")
        return
    if old:
        response = client.delete(f"{endpoint}/{name}", timeout=60)
        response.raise_for_status()
    response = client.post(endpoint, json=[{"key": name}], timeout=60)
    response.raise_for_status()
    with path.open("rb") as stream:
        response = client.put(
            f"{endpoint}/{name}/content",
            data=stream,
            headers={"Content-Type": "application/octet-stream"},
            timeout=300,
        )
    response.raise_for_status()
    response = client.post(f"{endpoint}/{name}/commit", timeout=60)
    response.raise_for_status()
    print(f"UPLOAD_ADDITION\t{name}\t{path.stat().st_size}\t{file_digest(path, 'sha256')}")


def upload() -> dict:
    build.validate_local_release(require_draft_binding=True)
    client = session()
    draft = get_draft(client)
    validate_metadata_shape(draft["metadata"])
    if draft.get("status") not in {"draft", "new_version_draft"}:
        raise RuntimeError(f"Unexpected draft status: {draft.get('status')}")
    existing = remote_entries(client)
    assert_draft_namespace(existing, require_all_additions=False)
    verify_draft_inherited(client, existing)
    endpoint = f"{API}/records/{draft_id()}/draft/files"
    for path in sorted(build.addition_paths(), key=lambda item: item.name):
        upload_one(client, endpoint, path, existing)
        existing = remote_entries(client)
        assert_draft_namespace(existing, require_all_additions=False)
    validated = validate_draft()
    return {"id": str(validated["id"]), "status": validated["status"], "result": "pass", "additions": 8}


def validate_draft() -> dict:
    build.validate_local_release(require_draft_binding=True)
    client = session()
    draft = get_draft(client)
    validate_metadata_shape(draft["metadata"])
    if draft.get("status") not in {"draft", "new_version_draft"}:
        raise RuntimeError(f"Unexpected draft status: {draft.get('status')}")
    if draft_doi(draft) != state()["draft_doi"]:
        raise RuntimeError("Draft DOI changed from local receipt")
    entries = remote_entries(client)
    assert_draft_namespace(entries, require_all_additions=True)
    expected = build.local_inventory()
    for name, path in {path.name: path for path in build.addition_paths()}.items():
        item = entries[name]
        if (
            item.get("status") != "completed"
            or item.get("size") != path.stat().st_size
            or item.get("checksum") != f"md5:{file_digest(path, 'md5')}"
        ):
            raise RuntimeError(f"Remote addition gate failed: {name}")
    verify_expected_bytes(client, entries, expected)
    return draft


def publish() -> dict:
    validate_draft()
    client = session()
    response = client.post(f"{API}/records/{draft_id()}/draft/actions/publish", timeout=120)
    response.raise_for_status()
    published = response.json()
    save_state(published)
    return published


def anonymous_readback() -> dict:
    build.validate_local_release(require_draft_binding=True)
    client = session(authenticated=False)
    response = client.get(f"{API}/records/{draft_id()}", timeout=60)
    response.raise_for_status()
    record = response.json()
    validate_metadata_shape(record["metadata"])
    entries = public_entries(record)
    expected = build.local_inventory()
    if set(entries) != set(expected) or len(entries) != 24:
        raise RuntimeError("Anonymous public 24-file inventory mismatch")
    verified = verify_expected_bytes(client, entries, expected)
    bundle_payload = download_entry(client, entries[build.BUNDLE_NAME])
    bundle_verification = build.verify_bundle_bytes(bundle_payload)
    inherited_names = set(build.inherited_inventory())
    for item in verified:
        item["disposition"] = "inherited_unchanged" if item["filename"] in inherited_names else "mit_l01_addition"
    metadata = record["metadata"]
    serialized = json.dumps(metadata, ensure_ascii=False)
    record_doi = record.get("pids", {}).get("doi", {}).get("identifier") or metadata.get("doi")
    receipt = {
        "schema": "o015-zenodo-mit-l01-public-readback-v1",
        "record_id": draft_id(),
        "record_doi": record_doi,
        "record_url": record["links"]["self_html"],
        "concept_id": build.CONCEPT_ID,
        "concept_doi": build.CONCEPT_DOI,
        "parent_record_id": build.PARENT_RECORD_ID,
        "status": record.get("status"),
        "title": metadata["title"],
        "version": metadata["version"],
        "publication_date": metadata["publication_date"],
        "resource_type": metadata["resource_type"]["id"],
        "creator_names": [item["person_or_org"]["name"] for item in metadata["creators"]],
        "contributor_names": [item["person_or_org"]["name"] for item in metadata.get("contributors", [])],
        "ttp_metadata_mentions": serialized.count("TTP"),
        "model_provenance_mentions": serialized.count("OpenAI Codex gpt-5.6-sol, Ultra"),
        "files": verified,
        "file_count": len(verified),
        "inherited_file_count": sum(item["disposition"] == "inherited_unchanged" for item in verified),
        "addition_file_count": sum(item["disposition"] == "mit_l01_addition" for item in verified),
        "inherited_identity": "pass",
        "delta_bundle_verification": bundle_verification,
    }
    if (
        receipt["status"] != "published"
        or receipt["record_doi"] != state()["draft_doi"]
        or receipt["file_count"] != 24
        or receipt["inherited_file_count"] != 16
        or receipt["addition_file_count"] != 8
        or receipt["ttp_metadata_mentions"] != 1
        or receipt["model_provenance_mentions"] != 1
    ):
        raise RuntimeError("Anonymous public state/identity gate failed")
    READBACK_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "upload", "validate", "publish", "readback"])
    args = parser.parse_args()
    if args.action == "prepare":
        result = prepare()
    elif args.action == "upload":
        result = upload()
    elif args.action == "validate":
        draft = validate_draft()
        result = {"id": str(draft["id"]), "status": draft["status"], "result": "pass", "file_count": 24}
    elif args.action == "publish":
        published = publish()
        result = {"id": str(published["id"]), "status": published.get("status"), "doi": draft_doi(published)}
    else:
        result = anonymous_readback()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
