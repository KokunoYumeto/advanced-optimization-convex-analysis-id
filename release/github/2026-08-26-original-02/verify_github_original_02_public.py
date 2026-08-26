#!/usr/bin/env python3
"""Strict anonymous public readback for the Original-02 GitHub checkpoint.

This verifier never invokes Git and never authenticates.  It binds a caller-
supplied (or manifest-frozen) full commit SHA to the public ``main`` branch,
requires the commit's changed-path set to equal the literal manifest exactly,
then compares every public raw byte with the corresponding local file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import Request, urlopen

try:  # The desktop runtime may provide this for stricter certificate stores.
    import truststore

    truststore.inject_into_ssl()
except Exception:
    pass


HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = HERE / "github-explicit-paths-original-02.json"
OUT = HERE / "github-public-readback-original-02.json"
EXPECTED_SCHEMA = "o015-github-original-02-explicit-paths-v1"
RESULT_SCHEMA = "o015-github-original-02-public-readback-v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, accept: str) -> bytes:
    last: Exception | None = None
    for attempt in range(3):
        try:
            request = Request(
                url,
                headers={
                    "Accept": accept,
                    "User-Agent": "Codex-Original-02-public-readback/1.0",
                },
            )
            with urlopen(request, timeout=90) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status} for {url}")
                return response.read()
        except Exception as exc:  # bounded retry for transient public transport failures
            last = exc
            if attempt < 2:
                time.sleep(1)
    raise RuntimeError(str(last))


def read_manifest() -> tuple[dict, list[str]]:
    if not MANIFEST_PATH.is_file():
        raise RuntimeError(f"required manifest missing: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema") != EXPECTED_SCHEMA:
        raise RuntimeError("manifest schema mismatch")
    groups = manifest.get("path_groups")
    if not isinstance(groups, dict) or not groups:
        raise RuntimeError("manifest path_groups must be a non-empty object")

    paths: list[str] = []
    for group, values in groups.items():
        if not isinstance(group, str) or not isinstance(values, list) or not values:
            raise RuntimeError(f"invalid or empty manifest group: {group!r}")
        if any(not isinstance(value, str) for value in values):
            raise RuntimeError(f"non-string path in manifest group: {group}")
        if values != sorted(values):
            raise RuntimeError(f"manifest group is not lexically sorted: {group}")
        paths.extend(values)

    if len(paths) != len(set(paths)):
        raise RuntimeError("manifest contains duplicate paths")
    if len(paths) != manifest.get("required_path_count"):
        raise RuntimeError(
            f"manifest path count mismatch: declared={manifest.get('required_path_count')} actual={len(paths)}"
        )
    for value in paths:
        pure = PurePosixPath(value)
        if (
            pure.is_absolute()
            or "\\" in value
            or value.startswith("./")
            or any(part in {"", ".", ".."} for part in pure.parts)
        ):
            raise RuntimeError(f"unsafe or non-canonical manifest path: {value!r}")
    if manifest.get("post_commit_receipt") in set(paths):
        raise RuntimeError("post-commit receipt must not be part of its own verified commit")
    return manifest, paths


def local_identity(relative: str) -> tuple[Path, bytes, dict[str, object]]:
    path = ROOT.joinpath(*PurePosixPath(relative).parts)
    resolved_root = ROOT.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"manifest path escapes repository root: {relative}") from exc
    if not path.is_file():
        raise FileNotFoundError(relative)
    data = path.read_bytes()
    return path, data, {"bytes": len(data), "sha256": sha256(data)}


def write_result(result: dict) -> None:
    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify one manifest-exact Original-02 GitHub commit anonymously."
    )
    parser.add_argument(
        "--commit",
        help="full 40-hex public commit SHA; required unless public_commit is frozen in the manifest",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest, required_paths = read_manifest()
    repository = manifest.get("repository")
    if not isinstance(repository, dict):
        raise RuntimeError("manifest repository object missing")
    owner = repository.get("owner")
    repo = repository.get("name")
    branch = repository.get("branch")
    if not all(isinstance(value, str) and value for value in (owner, repo, branch)):
        raise RuntimeError("manifest repository identity incomplete")

    manifest_commit = manifest.get("public_commit")
    if manifest_commit is not None and not isinstance(manifest_commit, str):
        raise RuntimeError("manifest public_commit must be null or a full SHA string")
    target = (args.commit or manifest_commit or "").lower()
    if not SHA40.fullmatch(target):
        raise RuntimeError(
            "public commit identity absent or invalid; pass --commit with the exact full 40-hex public SHA"
        )
    if args.commit and manifest_commit and target != manifest_commit.lower():
        raise RuntimeError("CLI commit conflicts with manifest-frozen public_commit")

    failures: list[dict[str, object]] = []
    local: dict[str, tuple[bytes, dict[str, object]]] = {}
    for relative in required_paths:
        try:
            _, data, identity = local_identity(relative)
            local[relative] = (data, identity)
        except Exception as exc:
            failures.append({"kind": "local_missing_or_unsafe", "path": relative, "detail": str(exc)})

    api_root = f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
    raw_root = f"https://raw.githubusercontent.com/{quote(owner, safe='')}/{quote(repo, safe='')}/{target}"
    commit_obj: dict = {}
    branch_obj: dict = {}
    if not failures:
        try:
            commit_files: list[dict] = []
            for page in range(1, 5):
                page_obj = json.loads(
                    fetch(
                        f"{api_root}/commits/{target}?per_page=100&page={page}",
                        "application/vnd.github+json",
                    ).decode("utf-8")
                )
                if page == 1:
                    commit_obj = page_obj
                page_files = page_obj.get("files") if isinstance(page_obj, dict) else None
                if not isinstance(page_files, list):
                    raise RuntimeError(f"commit page {page} has no file list")
                commit_files.extend(page_files)
                if len(page_files) < 100:
                    break
            else:
                raise RuntimeError("commit file list exceeds the bounded four-page audit")
            commit_obj["files"] = commit_files
            branch_obj = json.loads(
                fetch(
                    f"{api_root}/branches/{quote(branch, safe='')}",
                    "application/vnd.github+json",
                ).decode("utf-8")
            )
        except Exception as exc:
            failures.append({"kind": "public_identity_fetch", "detail": str(exc)})

    entries = commit_obj.get("files") if isinstance(commit_obj, dict) else None
    entries = entries if isinstance(entries, list) else []
    public_sha = commit_obj.get("sha") if isinstance(commit_obj, dict) else None
    branch_sha = ((branch_obj.get("commit") or {}).get("sha")) if isinstance(branch_obj, dict) else None
    parents = commit_obj.get("parents") if isinstance(commit_obj, dict) else None
    parents = parents if isinstance(parents, list) else []
    if commit_obj:
        if public_sha != target:
            failures.append({"kind": "commit_identity", "expected": target, "actual": public_sha})
        if branch_sha != target:
            failures.append({"kind": "branch_head_identity", "expected": target, "actual": branch_sha})
        if len(parents) != 1:
            failures.append({"kind": "parent_topology", "expected": 1, "actual": len(parents)})
        if not entries:
            failures.append({"kind": "commit_files", "detail": "empty public file list"})

    commit_paths = [entry.get("filename", "") for entry in entries if isinstance(entry, dict)]
    required_set = set(required_paths)
    commit_set = set(commit_paths)
    if len(commit_paths) != len(commit_set):
        failures.append({"kind": "duplicate_commit_paths"})
    for path in sorted(required_set - commit_set):
        failures.append({"kind": "required_path_absent_from_commit", "path": path})
    for path in sorted(commit_set - required_set):
        failures.append({"kind": "unexpected_path_in_commit", "path": path})
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append({"kind": "malformed_commit_file_entry"})
            continue
        status = entry.get("status")
        if status not in {"added", "modified"}:
            failures.append(
                {"kind": "disallowed_commit_file_status", "path": entry.get("filename"), "status": status}
            )
        if entry.get("previous_filename") is not None:
            failures.append({"kind": "rename_not_permitted", "path": entry.get("filename")})

    records: list[dict[str, object]] = []
    aggregate = 0
    entries_by_path = {
        entry.get("filename"): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("filename"), str)
    }
    if not any(item["kind"] in {"public_identity_fetch", "commit_identity"} for item in failures):
        for relative in required_paths:
            if relative not in local or relative not in entries_by_path:
                continue
            local_data, local_meta = local[relative]
            raw_url = f"{raw_root}/{quote(relative, safe='/')}"
            try:
                public_data = fetch(raw_url, "application/octet-stream")
            except Exception as exc:
                failures.append({"kind": "public_fetch", "path": relative, "detail": str(exc)})
                continue
            public_meta = {"bytes": len(public_data), "sha256": sha256(public_data)}
            match = public_data == local_data
            entry = entries_by_path[relative]
            records.append(
                {
                    "path": relative,
                    "status": entry.get("status"),
                    "bytes": public_meta["bytes"],
                    "local_bytes": local_meta["bytes"],
                    "sha256": public_meta["sha256"],
                    "local_sha256": local_meta["sha256"],
                    "blob_sha": entry.get("sha"),
                    "raw_url": raw_url,
                    "match": match,
                }
            )
            aggregate += len(public_data)
            if not match:
                failures.append({"kind": "byte_mismatch", "path": relative})

    manifest_bytes = MANIFEST_PATH.read_bytes()
    result = {
        "schema": RESULT_SCHEMA,
        "result": "pass" if not failures else "fail",
        "repository": f"https://github.com/{owner}/{repo}",
        "branch": branch,
        "commit": public_sha,
        "requested_commit": target,
        "branch_head": branch_sha,
        "tree": ((commit_obj.get("commit") or {}).get("tree") or {}).get("sha") if commit_obj else None,
        "parent": (parents[0] or {}).get("sha") if len(parents) == 1 else None,
        "commit_message": (commit_obj.get("commit") or {}).get("message") if commit_obj else None,
        "manifest": {
            "path": MANIFEST_PATH.relative_to(ROOT).as_posix(),
            "bytes": len(manifest_bytes),
            "sha256": sha256(manifest_bytes),
            "required_path_count": len(required_paths),
        },
        "commit_path_count": len(commit_paths),
        "verified_file_count": len(records),
        "aggregate_public_bytes": aggregate,
        "files": records,
        "failures": failures,
        "authenticated": False,
        "git_invoked": False,
        "upstream_contact": False,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    write_result(result)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "result",
                    "commit",
                    "branch_head",
                    "tree",
                    "commit_path_count",
                    "verified_file_count",
                    "aggregate_public_bytes",
                    "failures",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(2)
