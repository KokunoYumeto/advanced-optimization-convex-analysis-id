#!/usr/bin/env python3
"""Upload, publish, and anonymously verify the O015 Zenodo checkpoint."""

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
DRAFT_ID = "22059742"
CONCEPT_ID = "22059741"
API = "https://zenodo.org/api"
CREDENTIAL = Path(r"C:\Users\Floris\Documents\Obsidian notes\New zenodo token.md")
BUNDLE_NAME = "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_SOURCE_BACKEND_2026.08.22.zip"

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
]

UNADMITTED_PENN_TOKENS = tuple(
    token
    for chapter in range(5, 12)
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
    if len(paths) != 15 or len({path.name for path in paths}) != 15:
        raise RuntimeError("Expected exactly 15 uniquely named upload files")
    return paths


def session(authenticated: bool = True) -> requests.Session:
    result = requests.Session()
    result.headers["Accept"] = "application/vnd.inveniordm.v1+json"
    if authenticated:
        result.headers["Authorization"] = f"Bearer {token()}"
    return result


def remote_entries(client: requests.Session) -> dict[str, dict]:
    response = client.get(f"{API}/records/{DRAFT_ID}/draft/files", timeout=60)
    response.raise_for_status()
    return {item["key"]: item for item in response.json().get("entries", [])}


def upload_all() -> None:
    client = session()
    endpoint = f"{API}/records/{DRAFT_ID}/draft/files"
    existing = remote_entries(client)
    for path in upload_paths():
        name = path.name
        local_md5 = file_digest(path, "md5")
        old = existing.get(name)
        if (
            old
            and old.get("status") == "completed"
            and old.get("size") == path.stat().st_size
            and old.get("checksum") == f"md5:{local_md5}"
        ):
            print(f"SKIP\t{name}\t{path.stat().st_size}\t{file_digest(path, 'sha256')}")
            continue
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
        print(f"UPLOAD\t{name}\t{path.stat().st_size}\t{file_digest(path, 'sha256')}")


def validate_draft() -> dict:
    client = session()
    response = client.get(f"{API}/records/{DRAFT_ID}/draft", timeout=60)
    response.raise_for_status()
    draft = response.json()
    metadata = draft["metadata"]
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata["title"]
    description = metadata["description"]
    if "TTP" in title or "TTP" in description:
        raise RuntimeError("TTP leaked into title or description")
    if serialized.count("TTP") != 1:
        raise RuntimeError("Expected exactly one TTP organization metadata entry")
    if "Belum Lengkap" not in title or "belum lengkap" not in description.lower():
        raise RuntimeError("Incomplete checkpoint is not explicit")
    right_labels = [item.get("id") or item.get("title", {}).get("en") for item in metadata["rights"]]
    if "cc-by-4.0" not in right_labels or not any("3.0 United States" in item for item in right_labels):
        raise RuntimeError("Mixed component rights are not explicit")

    expected = {path.name: path for path in upload_paths()}
    actual = remote_entries(client)
    if set(expected) != set(actual):
        raise RuntimeError(
            f"Remote file set mismatch: missing={sorted(set(expected)-set(actual))}, "
            f"extra={sorted(set(actual)-set(expected))}"
        )
    for name, path in expected.items():
        item = actual[name]
        if item.get("status") != "completed":
            raise RuntimeError(f"Remote file not committed: {name}")
        if item.get("size") != path.stat().st_size:
            raise RuntimeError(f"Remote byte count mismatch: {name}")
        if item.get("checksum") != f"md5:{file_digest(path, 'md5')}":
            raise RuntimeError(f"Remote MD5 mismatch: {name}")
    return draft


def publish() -> dict:
    draft = validate_draft()
    if draft.get("status") != "draft":
        raise RuntimeError(f"Unexpected pre-publication status: {draft.get('status')}")
    client = session()
    response = client.post(f"{API}/records/{DRAFT_ID}/draft/actions/publish", timeout=120)
    response.raise_for_status()
    return response.json()


def verify_bundle(payload: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"Public ZIP integrity failure: {bad}")
        names = archive.namelist()
        forbidden = [
            name
            for name in names
            if any(token in name.lower() for token in UNADMITTED_PENN_TOKENS)
            or "/.git/" in f"/{name.lower()}/"
            or name.lower().startswith("build/")
            or name.lower().startswith("tmp/")
            or "token" in name.lower()
            or name.lower().endswith(".mpl")
        ]
        if forbidden:
            raise RuntimeError(f"Forbidden public ZIP entries: {forbidden}")
        manifest = json.loads(archive.read("SOURCE_BUNDLE_MANIFEST.json"))
        for item in manifest["entries"]:
            data = archive.read(item["path"])
            if len(data) != item["bytes"] or digest(data, "sha256") != item["sha256"]:
                raise RuntimeError(f"Inner manifest mismatch: {item['path']}")
        if len(names) != len(manifest["entries"]) + 2:
            raise RuntimeError("Public ZIP entry count mismatch")
        return {
            "entries": len(names),
            "manifest_entries_verified": len(manifest["entries"]),
            "forbidden_entries": 0,
            "integrity": "pass",
        }


def anonymous_readback() -> dict:
    client = session(authenticated=False)
    response = client.get(f"{API}/records/{DRAFT_ID}", timeout=60)
    response.raise_for_status()
    record = response.json()
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
        response = client.get(
            item["links"]["content"],
            headers={"Accept": "*/*"},
            timeout=300,
        )
        response.raise_for_status()
        payload = response.content
        local = expected[name]
        public_sha = digest(payload, "sha256")
        local_sha = file_digest(local, "sha256")
        if len(payload) != local.stat().st_size or public_sha != local_sha:
            raise RuntimeError(f"Anonymous byte identity failure: {name}")
        verified.append(
            {
                "filename": name,
                "bytes": len(payload),
                "sha256": public_sha,
                "public_byte_identity": "pass",
            }
        )
        if name == BUNDLE_NAME:
            bundle_result = verify_bundle(payload)

    metadata = record["metadata"]
    serialized = json.dumps(metadata, ensure_ascii=False)
    receipt = {
        "schema": "o015-zenodo-public-readback-v1",
        "record_id": DRAFT_ID,
        "concept_id": CONCEPT_ID,
        "record_doi": record.get("pids", {}).get("doi", {}).get("identifier")
        or metadata.get("doi"),
        "record_url": record["links"]["self_html"],
        "concept_doi": f"10.5281/zenodo.{CONCEPT_ID}",
        "status": record.get("status"),
        "title": metadata["title"],
        "version": metadata["version"],
        "publication_date": metadata["publication_date"],
        "resource_type": metadata["resource_type"]["id"],
        "creator_names": [item["person_or_org"]["name"] for item in metadata["creators"]],
        "contributor_names": [
            item["person_or_org"]["name"] for item in metadata.get("contributors", [])
        ],
        "ttp_metadata_mentions": serialized.count("TTP"),
        "rights": [
            item.get("id") or item.get("title", {}).get("en")
            for item in metadata["rights"]
        ],
        "files": verified,
        "file_count": len(verified),
        "bundle_verification": bundle_result,
    }
    if receipt["status"] != "published" or receipt["file_count"] != 15:
        raise RuntimeError("Public record state/count gate failed")
    if receipt["record_doi"] != f"10.5281/zenodo.{DRAFT_ID}":
        raise RuntimeError("Public DOI gate failed")
    if receipt["ttp_metadata_mentions"] != 1:
        raise RuntimeError("Public TTP metadata gate failed")

    out = HERE / "zenodo-public-readback.json"
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["upload", "validate", "publish", "readback"])
    args = parser.parse_args()
    if args.action == "upload":
        upload_all()
    elif args.action == "validate":
        draft = validate_draft()
        print(json.dumps({"status": draft["status"], "result": "pass"}, indent=2))
    elif args.action == "publish":
        result = publish()
        print(json.dumps({"status": result.get("status"), "id": result.get("id")}, indent=2))
    else:
        print(json.dumps(anonymous_readback(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
