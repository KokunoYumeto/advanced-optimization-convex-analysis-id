from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
OWNER = "KokunoYumeto"
REPOSITORY = "advanced-optimization-convex-analysis-id"
COMMIT = "7ff680f4079499c08f3b29780105f58279f519d5"
TREE = "a36c6a880f483681575c4b946d53a4ee0e493bf5"
PARENT = "42e9c6a4bd98d0583335382d33355ff70e1bedde"
EXPECTED_CHANGED_FILES = 62
OUT = Path(__file__).with_name("github-public-readback-becker-01.json")
USER_AGENT = "o015-public-readback/1.0"


def get(url: str, accept: str = "application/vnd.github+json") -> tuple[int, bytes]:
    request = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=90) as response:
        return response.status, response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    api_url = (
        f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/commits/{COMMIT}"
        "?per_page=100&page=1"
    )
    api_status, api_bytes = get(api_url)
    record = json.loads(api_bytes)
    if api_status != 200 or record.get("sha") != COMMIT:
        raise RuntimeError("public commit identity mismatch")
    if record.get("commit", {}).get("tree", {}).get("sha") != TREE:
        raise RuntimeError("public tree mismatch")
    parents = [item.get("sha") for item in record.get("parents", [])]
    if parents != [PARENT]:
        raise RuntimeError(f"public parent mismatch: {parents}")

    files = record.get("files", [])
    if len(files) != EXPECTED_CHANGED_FILES:
        raise RuntimeError(f"changed-file count mismatch: {len(files)}")

    verified: list[dict[str, object]] = []
    aggregate_bytes = 0
    for item in sorted(files, key=lambda value: value["filename"]):
        path = item["filename"]
        if item.get("status") not in {"added", "modified"}:
            raise RuntimeError(f"unexpected status for {path}: {item.get('status')}")
        local_path = ROOT / Path(path)
        if not local_path.is_file():
            raise RuntimeError(f"missing local committed path: {path}")
        local = local_path.read_bytes()
        raw_path = "/".join(quote(part, safe="") for part in path.split("/"))
        raw_url = (
            f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/"
            f"{COMMIT}/{raw_path}"
        )
        raw_status, public = get(raw_url, "application/octet-stream")
        if raw_status != 200 or public != local:
            raise RuntimeError(f"public byte mismatch: {path}")
        aggregate_bytes += len(public)
        verified.append(
            {
                "path": path,
                "status": item["status"],
                "bytes": len(public),
                "sha256": sha256(public),
                "public_byte_identity": "pass",
            }
        )

    patch_url = f"https://github.com/{OWNER}/{REPOSITORY}/commit/{COMMIT}.patch"
    patch_status, patch_bytes = get(patch_url, "text/plain")
    if patch_status != 200 or not patch_bytes.startswith(f"From {COMMIT} ".encode()):
        raise RuntimeError("immutable patch identity mismatch")

    latest_status, latest_bytes = get(
        f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/commits/main"
    )
    latest = json.loads(latest_bytes)
    if latest_status != 200 or latest.get("sha") != COMMIT:
        raise RuntimeError("public main does not point to Becker-01 commit")

    receipt = {
        "schema": "o015-github-becker-01-public-readback-v1",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "pass",
        "repository": f"https://github.com/{OWNER}/{REPOSITORY}",
        "branch": "main",
        "commit": COMMIT,
        "tree": TREE,
        "parent": PARENT,
        "main_points_to_commit": True,
        "changed_file_count": len(verified),
        "aggregate_bytes": aggregate_bytes,
        "files": verified,
        "commit_api": {
            "http_status": api_status,
            "bytes": len(api_bytes),
            "sha256": sha256(api_bytes),
        },
        "commit_patch": {
            "http_status": patch_status,
            "bytes": len(patch_bytes),
            "sha256": sha256(patch_bytes),
            "first_line_commit_match": True,
        },
        "credential_material_recorded": False,
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
                "tree": TREE,
                "changed_file_count": len(verified),
                "aggregate_bytes": aggregate_bytes,
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
