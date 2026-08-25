#!/usr/bin/env python3
"""Verify every Becker-03 content-commit path through public GitHub URLs."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OUT = HERE / "github-public-readback-becker-03.json"
OWNER = "KokunoYumeto"
REPO = "advanced-optimization-convex-analysis-id"
COMMIT = "09cc7e554b87c735428fb8cf3320a3d499956894"
TREE = "babb37fc16f31f95fee3e34a9b941d23e25a564b"
PARENT = "64b60dae61096a265c6deec8e7defb21b1d917d5"
PRIMARY = "output/pdf/D90-BECKER-03-reduksi-varians-id.pdf"
EXPECTED_CHANGED_PATHS = 58
UA = "O015-public-byte-verifier/1.0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def fetch(url: str, attempts: int = 4) -> tuple[bytes, dict[str, str]]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": UA, "Cache-Control": "no-cache"},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read(), {
                    key.lower(): value for key, value in response.headers.items()
                }
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(
        f"Public fetch failed after {attempts} attempts: {url}: {last}"
    )


def run_git_text(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def run_git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT,
        check=True,
        capture_output=True,
    ).stdout


def changed_paths() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    output = run_git_text(
        "diff-tree", "--no-commit-id", "--name-status", "-r", PARENT, COMMIT
    )
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) != 2 or fields[0] not in {"A", "M"}:
            raise RuntimeError(f"Unsupported changed-path row: {line!r}")
        rows.append((fields[0], fields[1]))
    if len(rows) != EXPECTED_CHANGED_PATHS:
        raise RuntimeError(
            f"Changed-path count {len(rows)} != {EXPECTED_CHANGED_PATHS}"
        )
    if len(rows) != len({path for _status, path in rows}):
        raise RuntimeError("Duplicate changed path")
    return rows


def committed_bytes(rel: str) -> bytes:
    return run_git_bytes("show", f"{COMMIT}:{rel}")


def main() -> None:
    identity = run_git_text("show", "-s", "--format=%H%n%T%n%P", COMMIT).splitlines()
    if identity != [COMMIT, TREE, PARENT]:
        raise RuntimeError(f"Local commit identity mismatch: {identity}")

    public_commit_url = f"https://github.com/{OWNER}/{REPO}/commit/{COMMIT}"
    commit_html, _ = fetch(public_commit_url)
    if COMMIT.encode("ascii") not in commit_html:
        raise RuntimeError("Public commit page lacks the immutable commit SHA")
    api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{COMMIT}"
    api_bytes, api_headers = fetch(api_url)
    api_commit = json.loads(api_bytes.decode("utf-8"))
    api_identity = [
        api_commit.get("sha"),
        api_commit.get("commit", {}).get("tree", {}).get("sha"),
        *[item.get("sha") for item in api_commit.get("parents", [])],
    ]
    if api_identity != [COMMIT, TREE, PARENT]:
        raise RuntimeError(f"Public commit API identity mismatch: {api_identity}")

    records = []
    for status, rel in changed_paths():
        expected = committed_bytes(rel)
        encoded = urllib.parse.quote(rel, safe="/")
        url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{COMMIT}/{encoded}"
        public, headers = fetch(url)
        if public != expected:
            raise RuntimeError(f"Public immutable bytes differ: {rel}")
        tree_blob = run_git_text("ls-tree", COMMIT, "--", rel).strip().split()
        if len(tree_blob) < 3 or tree_blob[2] != blob_sha1(expected):
            raise RuntimeError(f"Commit tree/blob identity mismatch: {rel}")
        records.append(
            {
                "status": status,
                "path": rel,
                "bytes": len(expected),
                "sha256": sha256(expected),
                "git_blob_sha1": blob_sha1(expected),
                "immutable_raw_url": url,
                "etag": headers.get("etag"),
                "exact_match": True,
            }
        )

    primary_expected = committed_bytes(PRIMARY)
    main_url = (
        f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/"
        f"{urllib.parse.quote(PRIMARY, safe='/')}"
    )
    main_bytes, _ = fetch(main_url)
    if main_bytes != primary_expected:
        raise RuntimeError("Public main does not expose the committed Becker-03 PDF")

    receipt = {
        "schema": "o015-becker-03-github-public-readback-v1",
        "result": "pass",
        "verified_at_utc": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "repository": f"https://github.com/{OWNER}/{REPO}",
        "branch": "main",
        "commit": COMMIT,
        "tree": TREE,
        "parent": PARENT,
        "public_commit_url": public_commit_url,
        "public_commit_page_contains_full_sha": True,
        "public_commit_api": {
            "url": api_url,
            "bytes": len(api_bytes),
            "sha256": sha256(api_bytes),
            "etag": api_headers.get("etag"),
            "identity_exact": True,
        },
        "changed_paths": len(records),
        "aggregate_bytes": sum(item["bytes"] for item in records),
        "all_immutable_raw_paths_exact": True,
        "main_primary_pdf": {
            "path": PRIMARY,
            "url": main_url,
            "bytes": len(main_bytes),
            "sha256": sha256(main_bytes),
            "exact_match": True,
        },
        "files": records,
        "verification_source": "immutable committed bytes from git show COMMIT:path",
        "authentication": "none; public HTTPS only",
        "credentials_recorded": False,
        "upstream_contact": False,
    }
    OUT.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "result": "pass",
                "commit": COMMIT,
                "changed_paths": len(records),
                "aggregate_bytes": receipt["aggregate_bytes"],
                "receipt": str(OUT),
                "receipt_bytes": OUT.stat().st_size,
                "receipt_sha256": sha256(OUT.read_bytes()),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
