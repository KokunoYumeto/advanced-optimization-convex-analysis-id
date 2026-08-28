#!/usr/bin/env python3
"""Verify the bounded public evidence descendant without a browser."""

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
MANIFEST_RELATIVE = "release/github/2026-08-28-integrated-final/github-explicit-paths-integrated-final-evidence.json"
RECEIPT = HERE / "github-public-readback-integrated-final-evidence.json"
REPOSITORY = "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id.git"
OWNER = "KokunoYumeto"
NAME = "advanced-optimization-convex-analysis-id"
BRANCH = "main"
PRIMARY = "output/pdf/D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf"


def run_git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def committed_bytes(commit: str, relative: str) -> bytes:
    return run_git("show", f"{commit}:{relative}")


def public_bytes(commitish: str, relative: str) -> bytes:
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in relative.split("/"))
    request = urllib.request.Request(
        f"https://raw.githubusercontent.com/{OWNER}/{NAME}/{commitish}/{encoded}",
        headers={"User-Agent": "Codex-public-byte-verifier/1"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
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
    expected = [item for values in manifest["path_groups"].values() for item in values]
    if len(expected) != len(set(expected)) or len(expected) != manifest["required_path_count"]:
        raise RuntimeError("explicit evidence manifest is inconsistent")

    parent_line = run_git("rev-list", "--parents", "-n", "1", commit).decode().split()
    if len(parent_line) != 2 or parent_line[1] != manifest["expected_parent"]:
        raise RuntimeError("evidence commit parent mismatch")
    parent = parent_line[1]
    tree = run_git("rev-parse", f"{commit}^{{tree}}").decode().strip()
    rows = []
    for line in run_git("diff-tree", "--no-commit-id", "--name-status", "--no-renames", "-r", commit).decode().splitlines():
        status, relative = line.split("\t", 1)
        rows.append((status, relative))
    if {path for _, path in rows} != set(expected) or len(rows) != len(expected):
        raise RuntimeError("evidence commit path set differs from manifest")
    if any(status not in {"A", "M"} for status, _ in rows):
        raise RuntimeError("evidence commit contains a non-A/M status")

    advertised = run_git("ls-remote", REPOSITORY, f"refs/heads/{BRANCH}").decode().split()
    if not advertised or advertised[0] != commit:
        raise RuntimeError("public main does not resolve to evidence commit")

    status_by_path = {path: status for status, path in rows}
    files = []
    total = 0
    for relative in expected:
        local = committed_bytes(commit, relative)
        remote = public_bytes(commit, relative)
        if local != remote:
            raise RuntimeError(f"immutable public mismatch: {relative}")
        total += len(local)
        files.append({"path": relative, "status": status_by_path[relative], "bytes": len(local), "sha256": sha(local)})
    if public_bytes(BRANCH, PRIMARY) != committed_bytes(commit, PRIMARY):
        raise RuntimeError("public main primary PDF differs from evidence commit")

    receipt = {
        "schema": "o015-github-integrated-final-evidence-public-readback-v1",
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
