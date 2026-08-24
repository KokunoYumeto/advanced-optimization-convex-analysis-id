#!/usr/bin/env python3
"""Anonymous exact-byte readback for one supplied MIT-L10 evidence commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "github-evidence-public-readback.json"
OWNER = "KokunoYumeto"
REPOSITORY = "advanced-optimization-convex-analysis-id"
USER_AGENT = "o015-l10-evidence-anonymous-readback"


def git_text(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, check=True, text=True, encoding="utf-8"
    ).stdout.strip()


def git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, check=True
    ).stdout


def fetch(url: str, accept: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.status, response.read()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("commit")
    parser.add_argument("parent")
    parser.add_argument("expected_count", type=int)
    args = parser.parse_args()
    commit = args.commit.lower()
    parent_expected = args.parent.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not re.fullmatch(r"[0-9a-f]{40}", parent_expected):
        raise RuntimeError("commit and parent must be exact 40-hex identities")
    if args.expected_count <= 0 or git_text("rev-parse", f"{commit}^{{commit}}") != commit:
        raise RuntimeError("commit/count arguments are not exact final values")
    tree = git_text("show", "-s", "--format=%T", commit)
    parent = git_text("show", "-s", "--format=%P", commit)
    if parent != parent_expected:
        raise RuntimeError("supplied evidence commit does not have the expected parent")
    paths = sorted(
        line
        for line in git_text("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()
        if line
    )
    if len(paths) != args.expected_count or len(paths) != len(set(paths)):
        raise RuntimeError(f"changed-file inventory mismatch: {len(paths)}")

    patch_url = f"https://github.com/{OWNER}/{REPOSITORY}/commit/{commit}.patch"
    patch_status, patch = fetch(patch_url, "text/plain")
    first_line = patch.splitlines()[0].decode("ascii", errors="replace") if patch else ""
    if patch_status != 200 or not first_line.startswith(f"From {commit} "):
        raise RuntimeError("public immutable commit-patch identity mismatch")

    files = []
    for path in paths:
        expected = git_bytes(commit, path)
        encoded = urllib.parse.quote(path, safe="/")
        status, public = fetch(
            f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/{commit}/{encoded}",
            "application/octet-stream",
        )
        if status != 200 or public != expected:
            raise RuntimeError(f"public byte mismatch: {path}")
        files.append(
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
        "changed_file_count": len(files),
        "commit": commit,
        "commit_patch": {
            "first_line_commit_match": True,
            "http_status": patch_status,
            "sha256": digest(patch),
            "url": patch_url,
        },
        "files": files,
        "parent": parent,
        "repository": f"https://github.com/{OWNER}/{REPOSITORY}",
        "result": "pass",
        "schema": "o015-github-mit-l10-evidence-public-readback-v1",
        "tree": tree,
        "upstream_contact": False,
    }
    RECEIPT.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "bytes": RECEIPT.stat().st_size,
                "files": len(files),
                "result": "pass",
                "sha256": digest(RECEIPT.read_bytes()),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
