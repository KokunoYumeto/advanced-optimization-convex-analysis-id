#!/usr/bin/env python3
"""Anonymous exact-byte readback for the bounded MIT L08 content commit."""

from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "github-public-readback.json"
OWNER = "KokunoYumeto"
REPOSITORY = "advanced-optimization-convex-analysis-id"
COMMIT = "024fd4eaf185b44250ab4ed41eb46afb660b4fbd"
TREE = "03a703dcac06356b7439ada876175ed80664525d"
PARENT = "08482b8630367b858e741d32a5376b9f1ddada66"
USER_AGENT = "o015-l08-anonymous-public-readback"
EXPECTED_CHANGED_FILES = 42


def fetch(url: str, accept: str = "application/vnd.github+json") -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={"Accept": accept, "User-Agent": USER_AGENT},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.status, response.read()


def git_bytes(path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{COMMIT}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return result.stdout


def changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", COMMIT],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    )
    return sorted(line for line in result.stdout.splitlines() if line)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    patch_url = f"https://github.com/{OWNER}/{REPOSITORY}/commit/{COMMIT}.patch"
    patch_status, patch_bytes = fetch(patch_url, "text/plain")
    first_line = patch_bytes.splitlines()[0].decode("ascii", errors="replace") if patch_bytes else ""
    if patch_status != 200 or not first_line.startswith(f"From {COMMIT} "):
        raise RuntimeError("public immutable commit-patch identity mismatch")

    paths = changed_paths()
    if len(paths) != EXPECTED_CHANGED_FILES or len(set(paths)) != EXPECTED_CHANGED_FILES:
        raise RuntimeError(f"public changed-file inventory mismatch: {len(paths)}")

    rows = []
    for path in paths:
        expected = git_bytes(path)
        encoded = urllib.parse.quote(path, safe="/")
        raw_url = f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/{COMMIT}/{encoded}"
        status, public = fetch(raw_url, "application/octet-stream")
        if status != 200 or public != expected:
            raise RuntimeError(f"public byte mismatch: {path}")
        rows.append(
            {
                "bytes": len(public),
                "http_status": status,
                "path": path,
                "public_byte_identity": "pass",
                "sha256": digest(public),
            }
        )

    receipt = {
        "all_changed_files_read_back": True,
        "branch": "main",
        "changed_file_count": len(rows),
        "commit": COMMIT,
        "commit_patch": {
            "commit": COMMIT,
            "first_line_commit_match": True,
            "http_status": patch_status,
            "sha256": digest(patch_bytes),
            "url": patch_url,
        },
        "files": rows,
        "parent": PARENT,
        "repository": f"https://github.com/{OWNER}/{REPOSITORY}",
        "result": "pass",
        "schema": "o015-github-mit-l08-public-readback-v1",
        "scope": "MIT L08 complete Lecture 4 pages 39-49, exact reader/source/QA/backend/control and prepared Zenodo release bytes; page 50 is not claimed.",
        "tree": TREE,
        "upstream_contact": False,
    }
    HERE.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "result": "pass",
                "files": len(rows),
                "bytes": RECEIPT.stat().st_size,
                "sha256": digest(RECEIPT.read_bytes()),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
