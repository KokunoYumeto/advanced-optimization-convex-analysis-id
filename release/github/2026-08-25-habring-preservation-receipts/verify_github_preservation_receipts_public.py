#!/usr/bin/env python3
"""Anonymous exact-byte verification of the O015 preservation-receipts commit."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "github-preservation-receipts-public-readback.json"
OWNER = "KokunoYumeto"
REPOSITORY = "advanced-optimization-convex-analysis-id"
COMMIT = "90062e1d78f41011ba350c88f07ebef44de80365"
TREE = "24865fc6929518c29a419305e96aba955d60aa44"
PARENT = "46d5753e853397e013d21b01872d789f7ee07a63"
EXPECTED_COUNT = 39
USER_AGENT = "o015-habring-preservation-receipts-anonymous-readback"


def git_text(*args: str) -> str:
    """Run one exact, bounded, read-only Git query."""
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def git_bytes(commit: str, path: str) -> bytes:
    """Read one named blob from one immutable commit."""
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout


def fetch(url: str, accept: str) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.status, response.read()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_changes() -> list[tuple[str, str]]:
    output = git_text(
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "--no-renames",
        "-r",
        COMMIT,
    )
    changes: list[tuple[str, str]] = []
    for line in output.splitlines():
        status, separator, path = line.partition("\t")
        if not separator or status not in {"A", "M"} or not path:
            raise RuntimeError(f"unexpected changed-path record: {line!r}")
        changes.append((status, path))
    changes.sort(key=lambda item: item[1])
    if len(changes) != EXPECTED_COUNT or len({path for _, path in changes}) != EXPECTED_COUNT:
        raise RuntimeError(f"changed-file inventory mismatch: {len(changes)}")
    return changes


def main() -> None:
    resolved = git_text("rev-parse", f"{COMMIT}^{{commit}}")
    if resolved != COMMIT:
        raise RuntimeError("local exact-commit resolution mismatch")
    local_tree = git_text("show", "-s", "--format=%T", COMMIT)
    local_parent = git_text("show", "-s", "--format=%P", COMMIT)
    if local_tree != TREE or local_parent != PARENT:
        raise RuntimeError("local tree or parent mismatch")

    changes = local_changes()
    local_paths = [path for _, path in changes]

    api_url = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/commits/{COMMIT}"
    api_status, api_bytes = fetch(api_url, "application/vnd.github+json")
    api = json.loads(api_bytes.decode("utf-8"))
    if api_status != 200 or api.get("sha") != COMMIT:
        raise RuntimeError("public commit API identity mismatch")
    api_tree = api.get("commit", {}).get("tree", {}).get("sha")
    api_parents = [entry.get("sha") for entry in api.get("parents", [])]
    if api_tree != TREE or api_parents != [PARENT]:
        raise RuntimeError("public tree or parent mismatch")
    api_files = api.get("files", [])
    api_path_status = {
        entry.get("filename"): entry.get("status") for entry in api_files
    }
    expected_api_status = {
        path: {"A": "added", "M": "modified"}[status]
        for status, path in changes
    }
    if len(api_files) != EXPECTED_COUNT or api_path_status != expected_api_status:
        raise RuntimeError("public commit API changed-path inventory mismatch")

    patch_url = f"https://github.com/{OWNER}/{REPOSITORY}/commit/{COMMIT}.patch"
    patch_status, patch = fetch(patch_url, "text/plain")
    first_line = patch.splitlines()[0].decode("ascii", errors="replace") if patch else ""
    if patch_status != 200 or not first_line.startswith(f"From {COMMIT} "):
        raise RuntimeError("public immutable commit-patch identity mismatch")
    patch_paths = sorted(
        match.group(1).decode("utf-8")
        for match in re.finditer(br"^diff --git a/(.+?) b/[^\r\n]+$", patch, re.MULTILINE)
    )
    if patch_paths != local_paths:
        raise RuntimeError("public immutable patch path inventory mismatch")

    files = []
    for status, path in changes:
        expected = git_bytes(COMMIT, path)
        encoded = urllib.parse.quote(path, safe="/")
        raw_url = (
            f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/"
            f"{COMMIT}/{encoded}"
        )
        raw_status, public = fetch(raw_url, "application/octet-stream")
        if raw_status != 200 or public != expected:
            raise RuntimeError(f"public byte mismatch: {path}")
        files.append(
            {
                "bytes": len(public),
                "change_type": {"A": "added", "M": "modified"}[status],
                "http_status": raw_status,
                "path": path,
                "public_byte_identity": "pass",
                "sha256": digest(public),
            }
        )

    verifier_bytes = Path(__file__).read_bytes()
    receipt = {
        "all_changed_files_read_back": True,
        "all_changed_paths_match_commit_api": True,
        "all_changed_paths_match_immutable_patch": True,
        "branch": "main",
        "changed_file_count": len(files),
        "commit": COMMIT,
        "commit_api": {
            "http_status": api_status,
            "sha256": digest(api_bytes),
            "url": api_url,
        },
        "commit_patch": {
            "first_line_commit_match": True,
            "http_status": patch_status,
            "path_count": len(patch_paths),
            "sha256": digest(patch),
            "url": patch_url,
        },
        "files": files,
        "git_queries": "read_only_and_bounded_to_the_exact_commit_and_its_named_paths",
        "parent": PARENT,
        "repository": f"https://github.com/{OWNER}/{REPOSITORY}",
        "result": "pass",
        "schema": "o015-github-habring-preservation-receipts-public-readback-v1",
        "scope": (
            "Durable Habring-v1 GitHub/Zenodo/Figshare preservation receipts, "
            "control closure, and Becker pre-admission cursor; no new translation "
            "or final-course claim."
        ),
        "tree": TREE,
        "upstream_contact": False,
        "verifier": {
            "bytes": len(verifier_bytes),
            "path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "sha256": digest(verifier_bytes),
        },
    }
    RECEIPT.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "commit": COMMIT,
                "files": len(files),
                "receipt_bytes": RECEIPT.stat().st_size,
                "receipt_sha256": digest(RECEIPT.read_bytes()),
                "result": "pass",
                "tree": TREE,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
