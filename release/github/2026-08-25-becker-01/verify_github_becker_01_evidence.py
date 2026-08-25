from __future__ import annotations

import base64
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OWNER = "KokunoYumeto"
REPOSITORY = "advanced-optimization-convex-analysis-id"
COMMIT = "18d5799e27d0f70d36001082465d5fa0fd48cb39"
TREE = "37da43821d7d1b354d8c8a28c2cdbc089c9f6236"
PARENT = "7ff680f4079499c08f3b29780105f58279f519d5"
EXPECTED_CHANGED_FILES = 17
OUT = Path(__file__).with_name("github-public-readback-becker-01-evidence.json")


def run_bytes(args: list[str]) -> bytes:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def gh_json(endpoint: str) -> tuple[dict, bytes]:
    raw = run_bytes(["gh", "api", endpoint])
    return json.loads(raw), raw


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    record, api_bytes = gh_json(
        f"repos/{OWNER}/{REPOSITORY}/commits/{COMMIT}?per_page=100&page=1"
    )
    if record.get("sha") != COMMIT:
        raise RuntimeError("public commit identity mismatch")
    if record.get("commit", {}).get("tree", {}).get("sha") != TREE:
        raise RuntimeError("public tree mismatch")
    if [item.get("sha") for item in record.get("parents", [])] != [PARENT]:
        raise RuntimeError("public parent mismatch")
    files = record.get("files", [])
    if len(files) != EXPECTED_CHANGED_FILES:
        raise RuntimeError(f"changed-file count mismatch: {len(files)}")

    verified: list[dict[str, object]] = []
    aggregate_bytes = 0
    for item in sorted(files, key=lambda value: value["filename"]):
        path = item["filename"]
        if item.get("status") not in {"added", "modified"}:
            raise RuntimeError(f"unexpected status for {path}: {item.get('status')}")
        committed = run_bytes(["git", "show", f"{COMMIT}:{path}"])
        blob, _ = gh_json(
            f"repos/{OWNER}/{REPOSITORY}/git/blobs/{item['sha']}"
        )
        if blob.get("encoding") != "base64":
            raise RuntimeError(f"unexpected blob encoding for {path}")
        public = base64.b64decode(blob["content"].replace("\n", ""), validate=True)
        if public != committed:
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

    latest, _ = gh_json(f"repos/{OWNER}/{REPOSITORY}/commits/main")
    if latest.get("sha") != COMMIT:
        raise RuntimeError("public main does not point to evidence commit")

    receipt = {
        "schema": "o015-github-becker-01-evidence-readback-v1",
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
            "bytes": len(api_bytes),
            "sha256": sha256(api_bytes),
        },
        "credential_transport": "GitHub CLI keyring session",
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
