#!/usr/bin/env python3
"""Verify the exact public GitHub commit for the integrated D90 release.

The verifier is browser-free. It uses bounded commit-object queries, anonymous
Git smart-HTTP ref resolution, and immutable raw-file downloads for exactly the
paths in the explicit manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST_RELATIVE = "release/github/2026-08-28-integrated-final/github-explicit-paths-integrated-final.json"
RECEIPT = HERE / "github-public-readback-integrated-final.json"
REPOSITORY = "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id.git"
OWNER = "KokunoYumeto"
NAME = "advanced-optimization-convex-analysis-id"
BRANCH = "main"
PRIMARY = "output/pdf/D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf"


def run_git(*args: str) -> bytes:
    process = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process.stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def committed_bytes(commit: str, relative: str) -> bytes:
    return run_git("show", f"{commit}:{relative}")


def public_bytes(commitish: str, relative: str) -> bytes:
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in relative.split("/"))
    url = f"https://raw.githubusercontent.com/{OWNER}/{NAME}/{commitish}/{encoded}"
    request = urllib.request.Request(url, headers={"User-Agent": "Codex-public-byte-verifier/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"raw download status {response.status}: {relative}")
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    commit = run_git("rev-parse", f"{args.commit}^{{commit}}").decode().strip()
    if commit != args.commit:
        raise RuntimeError("commit did not resolve to the exact requested object")
    manifest = json.loads(committed_bytes(commit, MANIFEST_RELATIVE).decode("utf-8"))
    groups = manifest["path_groups"]
    expected = [item for values in groups.values() for item in values]
    if len(expected) != len(set(expected)):
        raise RuntimeError("duplicate explicit path")
    if len(expected) != manifest["required_path_count"]:
        raise RuntimeError("manifest path count mismatch")

    parent_lines = run_git("rev-list", "--parents", "-n", "1", commit).decode().strip().split()
    if len(parent_lines) != 2:
        raise RuntimeError("release commit must have exactly one parent")
    parent = parent_lines[1]
    if parent != manifest["expected_parent"]:
        raise RuntimeError("release commit parent differs from explicit manifest")
    tree = run_git("rev-parse", f"{commit}^{{tree}}").decode().strip()
    rows = []
    for line in run_git("diff-tree", "--no-commit-id", "--name-status", "--no-renames", "-r", commit).decode("utf-8").splitlines():
        status, relative = line.split("\t", 1)
        rows.append((status, relative))
    actual = [relative for _, relative in rows]
    status_by_path = {relative: status for status, relative in rows}
    if set(actual) != set(expected) or len(actual) != len(expected):
        raise RuntimeError("commit path set differs from explicit manifest")
    if any(status not in {"A", "M"} for status, _ in rows):
        raise RuntimeError("release commit contains a delete, rename, or unexpected status")

    advertised = run_git("ls-remote", REPOSITORY, f"refs/heads/{BRANCH}").decode().strip().split()
    if len(advertised) < 2 or advertised[0] != commit:
        raise RuntimeError("public main does not resolve to the release commit")

    files = []
    total = 0
    for relative in expected:
        local = committed_bytes(commit, relative)
        remote = public_bytes(commit, relative)
        if remote != local:
            raise RuntimeError(f"immutable raw-byte mismatch: {relative}")
        total += len(local)
        files.append({"path": relative, "status": status_by_path[relative], "bytes": len(local), "sha256": sha(local)})

    primary_commit = committed_bytes(commit, PRIMARY)
    primary_main = public_bytes(BRANCH, PRIMARY)
    if primary_main != primary_commit:
        raise RuntimeError("public main primary reader differs from immutable commit")

    receipt = {
        "schema": "o015-github-integrated-final-public-readback-v1",
        "date": "2026-08-28",
        "result": "pass",
        "repository": f"https://github.com/{OWNER}/{NAME}",
        "branch": BRANCH,
        "commit": commit,
        "parent": parent,
        "tree": tree,
        "commit_path_count": len(files),
        "aggregate_bytes": total,
        "only_added_or_modified": True,
        "anonymous_smart_http_ref_match": True,
        "immutable_raw_byte_failures": 0,
        "primary_main_reader_matches_commit": True,
        "credential_material_recorded": False,
        "browser_used": False,
        "files": files,
    }
    if args.write:
        RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("result", "commit", "parent", "tree", "commit_path_count", "aggregate_bytes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
