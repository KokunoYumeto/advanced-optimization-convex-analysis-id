#!/usr/bin/env python3
"""Verify every Becker-02 commit path through public GitHub URLs."""

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
OUT = HERE / "github-public-readback-becker-02.json"
OWNER = "KokunoYumeto"
REPO = "advanced-optimization-convex-analysis-id"
COMMIT = "2923d8b6e06f1ced65a91be4bd63e4766e1fb5b7"
TREE = "b44b2d044d015ead4913f332588170238549820f"
PARENT = "de9026a6e84f53bb3243b10827a7e708716cfd97"
PRIMARY = "output/pdf/D90-BECKER-02-pemisahan-douglas-rachford-id.pdf"
UA = "O015-public-byte-verifier/1.0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def fetch(url: str, attempts: int = 4) -> tuple[bytes, dict[str, str]]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read(), {key.lower(): value for key, value in response.headers.items()}
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Public fetch failed after {attempts} attempts: {url}: {last}")


def run_git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT, check=True, capture_output=True, text=True, encoding="utf-8").stdout


def changed_paths() -> list[tuple[str, str]]:
    rows = []
    for line in run_git("diff-tree", "--no-commit-id", "--name-status", "-r", PARENT, COMMIT).splitlines():
        fields = line.split("\t")
        if len(fields) != 2 or fields[0] not in {"A", "M"}:
            raise RuntimeError(f"Unsupported changed-path row: {line!r}")
        rows.append((fields[0], fields[1]))
    if len(rows) != len({path for _status, path in rows}):
        raise RuntimeError("Duplicate changed path")
    return rows


def main() -> None:
    identity = run_git("show", "-s", "--format=%H%n%T%n%P", COMMIT).splitlines()
    if identity != [COMMIT, TREE, PARENT]:
        raise RuntimeError(f"Local commit identity mismatch: {identity}")

    public_commit_url = f"https://github.com/{OWNER}/{REPO}/commit/{COMMIT}"
    commit_html, _ = fetch(public_commit_url)
    if COMMIT.encode("ascii") not in commit_html:
        raise RuntimeError("Public commit page does not expose the expected immutable commit")
    patch, _ = fetch(public_commit_url + ".patch")

    records = []
    for status, rel in changed_paths():
        local = (PROJECT / rel).read_bytes()
        url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{COMMIT}/{urllib.parse.quote(rel, safe='/')}"
        public, headers = fetch(url)
        if public != local:
            raise RuntimeError(f"Public immutable bytes differ: {rel}")
        tree_blob = run_git("ls-tree", COMMIT, "--", rel).strip().split()
        if len(tree_blob) < 3 or tree_blob[2] != blob_sha1(local):
            raise RuntimeError(f"Local tree/blob identity mismatch: {rel}")
        records.append({
            "status": status,
            "path": rel,
            "bytes": len(local),
            "sha256": sha256(local),
            "git_blob_sha1": blob_sha1(local),
            "immutable_raw_url": url,
            "etag": headers.get("etag"),
            "exact_match": True,
        })

    main_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/{urllib.parse.quote(PRIMARY, safe='/')}"
    main_bytes, _ = fetch(main_url)
    if main_bytes != (PROJECT / PRIMARY).read_bytes():
        raise RuntimeError("Public main does not expose the committed Becker-02 primary PDF")

    receipt = {
        "schema": "o015-becker-02-github-public-readback-v1",
        "result": "pass",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repository": f"https://github.com/{OWNER}/{REPO}",
        "branch": "main",
        "commit": COMMIT,
        "tree": TREE,
        "parent": PARENT,
        "public_commit_url": public_commit_url,
        "public_commit_page_contains_full_sha": True,
        "public_patch": {"url": public_commit_url + ".patch", "bytes": len(patch), "sha256": sha256(patch)},
        "changed_paths": len(records),
        "aggregate_bytes": sum(item["bytes"] for item in records),
        "all_immutable_raw_paths_exact": True,
        "main_primary_pdf": {"path": PRIMARY, "url": main_url, "bytes": len(main_bytes), "sha256": sha256(main_bytes), "exact_match": True},
        "files": records,
        "authentication": "none; public HTTPS only",
        "credentials_recorded": False,
        "upstream_contact": False,
    }
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"result": "pass", "commit": COMMIT, "changed_paths": len(records), "aggregate_bytes": receipt["aggregate_bytes"], "receipt": str(OUT), "receipt_bytes": OUT.stat().st_size, "receipt_sha256": sha256(OUT.read_bytes())}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
