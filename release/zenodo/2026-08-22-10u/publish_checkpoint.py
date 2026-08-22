#!/usr/bin/env python3
"""Create, upload, publish, and anonymously verify the ten-unit Zenodo version."""

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


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PARENT_RECORD_ID = "22059742"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
API = "https://zenodo.org/api"
CREDENTIAL = Path(r"C:\Users\Floris\Documents\Obsidian notes\New zenodo token.md")
BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.22_10U.zip"
STATE_PATH = HERE / "zenodo-draft.json"
EXPECTED_TITLE = "Optimisasi Lanjut dan Analisis Konveks - Edisi Bahasa Indonesia (id-ID): Checkpoint Sepuluh Unit (Belum Lengkap)"
EXPECTED_VERSION = "checkpoint-2026.08.22-10u"
EXPECTED_BUNDLE_ENTRIES = 152

PDF_NAMES = [
    "D90-HAB-03-subgradien-id.pdf",
    "D90-HAB-04-metode-subgradien-terproyeksi-id.pdf",
    "D90-HAB-05-metode-gradien-proksimal-id.pdf",
    "D90-HAB-06-akselerasi-id.pdf",
    "D90-HAB-07-dualitas-id.pdf",
    "D90-HAB-08-penurunan-gradien-stokastik-id.pdf",
    "D90-HAB-09-transportasi-optimal-id.pdf",
    "D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.pdf",
    "D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf",
    "D90-PENN-05-metode-newton-dan-koreksi-id.pdf",
]

UNADMITTED_PENN_TOKENS = tuple(
    token
    for chapter in range(6, 12)
    for token in (f"penn_ch{chapter:02d}", f"penn-{chapter:02d}")
)


def token() -> str:
    raw = CREDENTIAL.read_text(encoding="utf-8")
    match = re.search(r"zenodo_pat_[A-Za-z0-9_-]+", raw)
    if not match:
        match = re.search(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])", raw)
    if not match:
        raise RuntimeError("No Zenodo credential-shaped value found")
    return match.group(0)


def digest(data: bytes, name: str) -> str:
    return hashlib.new(name, data).hexdigest()


def file_digest(path: Path, name: str) -> str:
    hasher = hashlib.new(name)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def upload_paths() -> list[Path]:
    paths = [ROOT / "output" / "pdf" / name for name in PDF_NAMES]
    paths.extend(
        [
            HERE / BUNDLE_NAME,
            HERE / "README_RELEASE.md",
            HERE / "README.md",
            HERE / "RIGHTS.md",
            HERE / "release-manifest.json",
            HERE / "SHA256SUMS",
        ]
    )
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing upload files:\n" + "\n".join(missing))
    if len(paths) != 16 or len({path.name for path in paths}) != 16:
        raise RuntimeError("Expected exactly 16 uniquely named upload files")
    return paths


def session(authenticated: bool = True) -> requests.Session:
    result = requests.Session()
    result.headers["Accept"] = "application/vnd.inveniordm.v1+json"
    result.headers["User-Agent"] = "O015-id-ID-preservation/1.0"
    if authenticated:
        result.headers["Authorization"] = f"Bearer {token()}"
    return result


def state() -> dict:
    if not STATE_PATH.is_file():
        raise RuntimeError("No local draft receipt; run prepare first")
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if data.get("parent_record_id") != PARENT_RECORD_ID or data.get("concept_id") != CONCEPT_ID:
        raise RuntimeError("Local draft receipt belongs to a different lineage")
    return data


def draft_id() -> str:
    return str(state()["draft_id"])


def draft_doi(record: dict) -> str:
    identifier = record.get("pids", {}).get("doi", {}).get("identifier")
    return str(identifier or f"10.5281/zenodo.{record['id']}")


def save_state(record: dict) -> dict:
    identity = {
        "schema": "o015-zenodo-draft-receipt-v1",
        "parent_record_id": PARENT_RECORD_ID,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "draft_id": str(record["id"]),
        "draft_doi": draft_doi(record),
        "status": record.get("status"),
        "title": record.get("metadata", {}).get("title"),
        "version": record.get("metadata", {}).get("version"),
    }
    STATE_PATH.write_text(json.dumps(identity, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return identity


def get_draft(client: requests.Session, record_id: str) -> dict:
    response = client.get(f"{API}/records/{record_id}/draft", timeout=60)
    response.raise_for_status()
    return response.json()


def validate_metadata_shape(metadata: dict) -> None:
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata["title"]
    description = metadata["description"]
    if title != EXPECTED_TITLE or metadata.get("version") != EXPECTED_VERSION:
        raise RuntimeError("Title/version metadata does not match the ten-unit checkpoint")
    if "TTP" in title or "TTP" in description:
        raise RuntimeError("TTP leaked into title or description")
    if serialized.count("TTP") != 1:
        raise RuntimeError("Expected exactly one TTP organization metadata entry")
    if "Belum Lengkap" not in title or "belum lengkap" not in description.lower():
        raise RuntimeError("Incomplete checkpoint is not explicit")
    if "sepuluh" not in description.lower() or "Bab 3-5" not in description:
        raise RuntimeError("Ten-unit/Penn Chapter 5 coverage is not explicit")
    if "MIT OpenCourseWare 6.253" not in description or "belum hadir" not in description:
        raise RuntimeError("Primary-course absence is not explicit")
    rights = [item.get("id") or item.get("title", {}).get("en", "") for item in metadata["rights"]]
    if "cc-by-4.0" not in rights or not any("3.0 United States" in item for item in rights):
        raise RuntimeError("Mixed component rights are not explicit")


def prepare() -> dict:
    template = json.loads((HERE / "zenodo-record.json").read_text(encoding="utf-8"))
    validate_metadata_shape(template["metadata"])
    client = session()

    if STATE_PATH.is_file():
        receipt = state()
        try:
            existing = get_draft(client, str(receipt["draft_id"]))
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                public = client.get(f"{API}/records/{receipt['draft_id']}", timeout=60)
                if public.status_code == 200 and public.json().get("status") == "published":
                    return save_state(public.json())
            raise
        response = client.put(f"{API}/records/{receipt['draft_id']}/draft", json=template, timeout=60)
        response.raise_for_status()
        updated = response.json()
        validate_metadata_shape(updated["metadata"])
        return save_state(updated)

    parent = session(authenticated=False).get(f"{API}/records/{PARENT_RECORD_ID}", timeout=60)
    parent.raise_for_status()
    parent_data = parent.json()
    if parent_data.get("status") != "published":
        raise RuntimeError("Version parent is not publicly published")
    parent_concept = str(parent_data.get("parent", {}).get("id") or "")
    if parent_concept and parent_concept != CONCEPT_ID:
        raise RuntimeError("Version parent concept mismatch")

    response = client.post(f"{API}/records/{PARENT_RECORD_ID}/versions", timeout=60)
    response.raise_for_status()
    created = response.json()
    response = client.put(f"{API}/records/{created['id']}/draft", json=template, timeout=60)
    response.raise_for_status()
    updated = response.json()
    validate_metadata_shape(updated["metadata"])
    return save_state(updated)


def remote_entries(client: requests.Session) -> dict[str, dict]:
    response = client.get(f"{API}/records/{draft_id()}/draft/files", timeout=60)
    response.raise_for_status()
    return {item["key"]: item for item in response.json().get("entries", [])}


def upload_all() -> None:
    client = session()
    endpoint = f"{API}/records/{draft_id()}/draft/files"
    expected_names = {path.name for path in upload_paths()}
    existing = remote_entries(client)
    for extra in sorted(set(existing) - expected_names):
        response = client.delete(f"{endpoint}/{extra}", timeout=60)
        response.raise_for_status()
        print(f"DELETE_INHERITED\t{extra}")

    existing = remote_entries(client)
    for path in upload_paths():
        name = path.name
        local_md5 = file_digest(path, "md5")
        old = existing.get(name)
        if old and old.get("status") == "completed" and old.get("size") == path.stat().st_size and old.get("checksum") == f"md5:{local_md5}":
            print(f"SKIP\t{name}\t{path.stat().st_size}\t{file_digest(path, 'sha256')}")
            continue
        if old:
            response = client.delete(f"{endpoint}/{name}", timeout=60)
            response.raise_for_status()
        response = client.post(endpoint, json=[{"key": name}], timeout=60)
        response.raise_for_status()
        with path.open("rb") as stream:
            response = client.put(f"{endpoint}/{name}/content", data=stream, headers={"Content-Type": "application/octet-stream"}, timeout=300)
        response.raise_for_status()
        response = client.post(f"{endpoint}/{name}/commit", timeout=60)
        response.raise_for_status()
        print(f"UPLOAD\t{name}\t{path.stat().st_size}\t{file_digest(path, 'sha256')}")


def verify_bundle(payload: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP integrity failure: {bad}")
        names = archive.namelist()
        forbidden = [
            name for name in names
            if any(token in name.lower() for token in UNADMITTED_PENN_TOKENS)
            or "/.git/" in f"/{name.lower()}/"
            or name.lower().startswith("build/")
            or name.lower().startswith("tmp/")
            or "token" in name.lower()
            or name.lower().endswith(".mpl")
            or name.endswith("PENN_CH05_SOURCE_AUDIT_DRAFT.md")
            or name.endswith("PENN_CH05_WORKLOG.md")
        ]
        if forbidden:
            raise RuntimeError(f"Forbidden ZIP entries: {forbidden}")
        if len(names) != EXPECTED_BUNDLE_ENTRIES or len(set(names)) != EXPECTED_BUNDLE_ENTRIES:
            raise RuntimeError("ZIP entry count/uniqueness mismatch")
        manifest = json.loads(archive.read("SOURCE_BUNDLE_MANIFEST.json"))
        if len(manifest["entries"]) != EXPECTED_BUNDLE_ENTRIES - 2:
            raise RuntimeError("Inner manifest count mismatch")
        for item in manifest["entries"]:
            data = archive.read(item["path"])
            if len(data) != item["bytes"] or digest(data, "sha256") != item["sha256"]:
                raise RuntimeError(f"Inner manifest mismatch: {item['path']}")
        return {
            "entries": len(names),
            "manifest_entries_verified": len(manifest["entries"]),
            "forbidden_entries": 0,
            "integrity": "pass",
        }


def validate_local_release() -> None:
    release_manifest = json.loads((HERE / "release-manifest.json").read_text(encoding="utf-8"))
    receipt = state()
    if release_manifest.get("zenodo_record_id") != receipt["draft_id"] or release_manifest.get("zenodo_record_doi") != receipt["draft_doi"]:
        raise RuntimeError("Release manifest is not bound to the prepared draft; rebuild checkpoint")
    if release_manifest.get("source_bundle_entries") != EXPECTED_BUNDLE_ENTRIES:
        raise RuntimeError("Release manifest bundle-entry count mismatch")
    lines = (HERE / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    expected_sum_names = {path.name for path in upload_paths() if path.name != "SHA256SUMS"}
    actual_sum_names = {line.split("  ", 1)[1] for line in lines}
    if actual_sum_names != expected_sum_names or len(lines) != 15:
        raise RuntimeError("SHA256SUMS inventory mismatch")
    for line in lines:
        expected_hash, name = line.split("  ", 1)
        path = next(path for path in upload_paths() if path.name == name)
        if file_digest(path, "sha256") != expected_hash:
            raise RuntimeError(f"SHA256SUMS mismatch: {name}")
    verify_bundle((HERE / BUNDLE_NAME).read_bytes())


def validate_draft() -> dict:
    validate_local_release()
    client = session()
    draft = get_draft(client, draft_id())
    validate_metadata_shape(draft["metadata"])
    if draft.get("status") not in {"draft", "new_version_draft"}:
        raise RuntimeError(f"Unexpected draft status: {draft.get('status')}")
    if draft_doi(draft) != state()["draft_doi"]:
        raise RuntimeError("Draft DOI changed from the local receipt")
    expected = {path.name: path for path in upload_paths()}
    actual = remote_entries(client)
    if set(expected) != set(actual):
        raise RuntimeError(f"Remote file set mismatch: missing={sorted(set(expected)-set(actual))}, extra={sorted(set(actual)-set(expected))}")
    for name, path in expected.items():
        item = actual[name]
        if item.get("status") != "completed" or item.get("size") != path.stat().st_size or item.get("checksum") != f"md5:{file_digest(path, 'md5')}":
            raise RuntimeError(f"Remote file gate failed: {name}")
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
    client = session(authenticated=False)
    response = client.get(f"{API}/records/{draft_id()}", timeout=60)
    response.raise_for_status()
    record = response.json()
    metadata = record["metadata"]
    validate_metadata_shape(metadata)
    expected = {path.name: path for path in upload_paths()}
    public_files = record.get("files", {}).get("entries", [])
    if isinstance(public_files, dict):
        public_files = list(public_files.values())
    if set(expected) != {item["key"] for item in public_files}:
        raise RuntimeError("Anonymous public file inventory mismatch")

    verified = []
    bundle_result = None
    for item in sorted(public_files, key=lambda value: value["key"]):
        name = item["key"]
        response = client.get(item["links"]["content"], headers={"Accept": "*/*"}, timeout=300)
        response.raise_for_status()
        payload = response.content
        path = expected[name]
        if len(payload) != path.stat().st_size or digest(payload, "sha256") != file_digest(path, "sha256"):
            raise RuntimeError(f"Anonymous public byte mismatch: {name}")
        verified.append({"filename": name, "bytes": len(payload), "sha256": digest(payload, "sha256"), "public_byte_identity": "pass"})
        if name == BUNDLE_NAME:
            bundle_result = verify_bundle(payload)

    serialized = json.dumps(metadata, ensure_ascii=False)
    record_doi = record.get("pids", {}).get("doi", {}).get("identifier") or metadata.get("doi")
    receipt = {
        "schema": "o015-zenodo-public-readback-v1",
        "record_id": draft_id(),
        "concept_id": CONCEPT_ID,
        "record_doi": record_doi,
        "record_url": record["links"]["self_html"],
        "concept_doi": CONCEPT_DOI,
        "status": record.get("status"),
        "title": metadata["title"],
        "version": metadata["version"],
        "publication_date": metadata["publication_date"],
        "resource_type": metadata["resource_type"]["id"],
        "creator_names": [item["person_or_org"]["name"] for item in metadata["creators"]],
        "contributor_names": [item["person_or_org"]["name"] for item in metadata.get("contributors", [])],
        "ttp_metadata_mentions": serialized.count("TTP"),
        "rights": [item.get("id") or item.get("title", {}).get("en") for item in metadata["rights"]],
        "files": verified,
        "file_count": len(verified),
        "bundle_verification": bundle_result,
    }
    if receipt["status"] != "published" or receipt["file_count"] != 16:
        raise RuntimeError("Public record state/count gate failed")
    if receipt["record_doi"] != state()["draft_doi"] or receipt["ttp_metadata_mentions"] != 1:
        raise RuntimeError("Public DOI/TTP gate failed")
    (HERE / "zenodo-public-readback.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "upload", "validate", "publish", "readback"])
    args = parser.parse_args()
    if args.action == "prepare":
        print(json.dumps(prepare(), ensure_ascii=False, indent=2, sort_keys=True))
    elif args.action == "upload":
        upload_all()
    elif args.action == "validate":
        draft = validate_draft()
        print(json.dumps({"status": draft["status"], "result": "pass", "id": str(draft["id"])}, indent=2))
    elif args.action == "publish":
        result = publish()
        print(json.dumps({"status": result.get("status"), "id": str(result.get("id")), "doi": draft_doi(result)}, indent=2))
    else:
        print(json.dumps(anonymous_readback(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
