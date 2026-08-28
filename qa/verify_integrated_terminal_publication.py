#!/usr/bin/env python3
"""Headless terminal verification for the complete integrated D90 release."""

from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GITHUB_RECEIPT = ROOT / "release/github/2026-08-28-integrated-final/github-public-readback-integrated-final.json"
ZENODO_RECEIPT = ROOT / "release/zenodo/2026-08-28-integrated-final/zenodo-public-readback-integrated.json"
CLOSURE_RECEIPT = ROOT / "release/zenodo/2026-08-28-integrated-final/zenodo-draft-closure-integrated.json"
OUTPUT = ROOT / "qa/INTEGRATED_TERMINAL_PUBLICATION_AUDIT.json"

COMMIT = "b57225d46631680b3755edcd23975916e84a8b6c"
TREE = "aa8663945724e998b03b74481ef290550bb2dc59"
PARENT = "74780b65dcf9954bdf915aecbf57cd17fd6b43ea"
RECORD = "22142120"
DOI = "10.5281/zenodo.22142120"
CONCEPT = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
PRIMARY = "D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf"
PRIMARY_SHA256 = "9deefecf469c9f2aace26bc8ccdedc552debbe9874ae035badaf5cffee0f80e5"
PRIMARY_BYTES = 1_671_254


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": sha_bytes(data)}


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"non-object JSON: {path}")
    return value


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Codex-D90-terminal-verifier/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError(f"non-object response: {url}")
    return value


def main() -> int:
    github = read_json(GITHUB_RECEIPT)
    zenodo = read_json(ZENODO_RECEIPT)
    closure = read_json(CLOSURE_RECEIPT)

    if (
        github.get("result") != "pass"
        or github.get("commit") != COMMIT
        or github.get("tree") != TREE
        or github.get("parent") != PARENT
        or github.get("commit_path_count") != 87
        or github.get("aggregate_bytes") != 15_858_259
        or github.get("browser_used") is not False
        or github.get("credential_material_recorded") is not False
    ):
        raise RuntimeError("GitHub receipt is not the exact terminal release receipt")
    if (
        zenodo.get("result") != "pass"
        or str(zenodo.get("record_id")) != RECORD
        or zenodo.get("record_doi") != DOI
        or str(zenodo.get("concept_id")) != CONCEPT
        or zenodo.get("concept_doi") != CONCEPT_DOI
        or zenodo.get("status") != "published"
        or zenodo.get("is_latest") is not True
        or zenodo.get("default_preview") != PRIMARY
        or zenodo.get("file_count") != 100
        or zenodo.get("inherited_file_count") != 91
        or zenodo.get("addition_file_count") != 9
        or any(item.get("public_byte_identity") != "pass" for item in zenodo.get("files", []))
        or zenodo.get("credential_material_recorded") is not False
    ):
        raise RuntimeError("Zenodo readback is not the exact terminal release receipt")
    if (
        closure.get("result") != "pass"
        or str(closure.get("record_id")) != RECORD
        or closure.get("authenticated_draft_lookup_status") != 404
        or closure.get("concept_open_draft_count") != 0
        or closure.get("authenticated_pagination_complete") is not True
        or closure.get("authenticated_records_scanned") != 260
        or closure.get("credential_material_recorded") is not False
    ):
        raise RuntimeError("Zenodo draft closure is incomplete")

    advertised = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-remote",
            "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id.git",
            "refs/heads/main",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.split()
    if not advertised or advertised[0] != COMMIT:
        raise RuntimeError("public GitHub main no longer resolves to the release commit")

    record = get_json(f"https://zenodo.org/api/records/{RECORD}")
    metadata = record.get("metadata", {})
    relations = metadata.get("relations", {}).get("version", [])
    is_latest = any(item.get("is_last") is True for item in relations if isinstance(item, dict))
    files = record.get("files", [])
    if (
        str(record.get("id")) != RECORD
        or record.get("doi") != DOI
        or str(record.get("conceptrecid")) != CONCEPT
        or record.get("status") != "published"
        or metadata.get("access_right") != "open"
        or not is_latest
        or not isinstance(files, list)
        or len(files) != 100
    ):
        raise RuntimeError("live Zenodo identity/access/latest state mismatch")
    expected_files = {item["filename"]: item for item in zenodo["files"]}
    live_files = {item.get("key"): item for item in files}
    if set(live_files) != set(expected_files):
        raise RuntimeError("live Zenodo file namespace differs from the readback receipt")
    if any(live_files[name].get("size") != expected_files[name]["bytes"] for name in live_files):
        raise RuntimeError("live Zenodo file-size inventory differs from the readback receipt")

    file_state = get_json(f"https://zenodo.org/api/records/{RECORD}/files")
    if file_state.get("default_preview") != PRIMARY:
        raise RuntimeError("live Zenodo default preview changed")

    raw_url = (
        "https://raw.githubusercontent.com/KokunoYumeto/"
        f"advanced-optimization-convex-analysis-id/{COMMIT}/output/pdf/{PRIMARY}"
    )
    request = urllib.request.Request(raw_url, headers={"User-Agent": "Codex-D90-terminal-verifier/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        primary = response.read()
    if len(primary) != PRIMARY_BYTES or sha_bytes(primary) != PRIMARY_SHA256:
        raise RuntimeError("public GitHub primary PDF identity mismatch")

    receipt_bytes = GITHUB_RECEIPT.read_bytes() + ZENODO_RECEIPT.read_bytes() + CLOSURE_RECEIPT.read_bytes()
    if b"C:\\Users\\" in receipt_bytes or b"Bearer " in receipt_bytes or b"Authorization" in receipt_bytes:
        raise RuntimeError("receipt privacy/credential scan failed")

    result = {
        "schema": "o015-integrated-terminal-publication-audit-v1",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": "pass",
        "course_status": "complete",
        "github": {
            "repository": "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id",
            "branch": "main",
            "commit": COMMIT,
            "tree": TREE,
            "path_count": 87,
            "aggregate_bytes": 15_858_259,
            "anonymous_main_match": True,
            "primary_pdf_sha256": PRIMARY_SHA256,
        },
        "zenodo": {
            "record_url": f"https://zenodo.org/records/{RECORD}",
            "record_doi": DOI,
            "concept_doi": CONCEPT_DOI,
            "status": "published",
            "is_latest": True,
            "record_access": "public",
            "files_access": "public",
            "file_count": 100,
            "default_preview": PRIMARY,
            "open_draft_count": 0,
        },
        "receipts": [identity(GITHUB_RECEIPT), identity(ZENODO_RECEIPT), identity(CLOSURE_RECEIPT)],
        "browser_used": False,
        "credential_material_recorded": False,
        "required_work_remaining": [],
        "terminal_condition_satisfied": True,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": "pass", "output": OUTPUT.relative_to(ROOT).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
