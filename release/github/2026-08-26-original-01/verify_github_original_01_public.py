#!/usr/bin/env python3
"""Anonymous, exact-byte readback for the Original-01 GitHub checkpoint.

The verifier is intentionally commit-scoped. It asks the public GitHub API for
one known commit, rejects any changed path outside this tranche and its durable
controls, then downloads every changed path from raw.githubusercontent.com and
compares it with the local byte identity. No credential or authenticated API
route is used.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

try:  # The desktop runtime may provide this for stricter certificate stores.
    import truststore

    truststore.inject_into_ssl()
except Exception:
    pass


OWNER = "KokunoYumeto"
REPO = "advanced-optimization-convex-analysis-id"
COMMIT = "ec90fc78b5f974f845d04f2e1c59069e5eacefe3"
API_ROOT = f"https://api.github.com/repos/{OWNER}/{REPO}"
RAW_ROOT = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{COMMIT}"
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().with_name("github-public-readback-original-01.json")

EXACT = {
    "00_control/ADVERSE_LEDGER.jsonl",
    "00_control/BUILD_AND_QA.md",
    "00_control/COMPONENT_RIGHTS.csv",
    "00_control/COVERAGE_OVERLAP.md",
    "00_control/CURRENT_CURSOR.md",
    "00_control/CURRENT_STATE.md",
    "00_control/DECISION_LOG.md",
    "00_control/PUBLICATION_RECEIPTS.md",
    "00_control/SOURCE_AUTHORITY.json",
    "backend/records.csv",
    "backend/records.jsonl",
    "source/id-ID/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.tex",
    "source/id-ID/original-01-metode-stokastik-komposit-cermin-minibatch-id.tex",
    "output/epub/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub",
    "output/html/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html",
    "output/pdf/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf",
}
QA_SCRIPTS = {
    "qa/build_original_01_pdf.py",
    "qa/build_original_01_reflow.py",
    "qa/extend_backend_original_01.py",
    "qa/validate_backend_original_01.py",
    "qa/validate_original_01_math.py",
    "qa/validate_original_01_rights_nonoverlap.py",
    "qa/verify_original_01_epub.py",
    "qa/verify_original_01_pdf_visual.py",
}


def allowed(path: str) -> bool:
    return (
        path in EXACT
        or path.startswith("labs/original-01/")
        or path.startswith("qa/ORIGINAL_01_")
        or path in QA_SCRIPTS
        or path.startswith("release/original-01/2026-08-26/")
        or path.startswith("release/zenodo/2026-08-26-original-01/")
    )


def fetch(url: str, accept: str) -> bytes:
    last = None
    for attempt in range(3):
        try:
            req = Request(
                url,
                headers={
                    "Accept": accept,
                    "User-Agent": "Codex-Original-01-public-readback/1.0",
                },
            )
            with urlopen(req, timeout=60) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status} for {url}")
                return response.read()
        except Exception as exc:  # bounded retry for transient public transport errors
            last = exc
            if attempt < 2:
                time.sleep(1)
    raise RuntimeError(str(last))


def main() -> int:
    commit_obj = json.loads(
        fetch(f"{API_ROOT}/commits/{COMMIT}", "application/vnd.github+json").decode("utf-8")
    )
    files = commit_obj.get("files", [])
    paths = [entry.get("filename", "") for entry in files]
    failures: list[dict[str, str]] = []
    if commit_obj.get("sha") != COMMIT:
        failures.append({"kind": "commit_identity", "detail": str(commit_obj.get("sha"))})
    if not files:
        failures.append({"kind": "commit_files", "detail": "empty public file list"})
    for path in paths:
        if not allowed(path):
            failures.append({"kind": "unexpected_path", "path": path})

    records = []
    aggregate = 0
    for entry in files:
        path = entry["filename"]
        local_path = ROOT / Path(path)
        if not local_path.is_file():
            failures.append({"kind": "local_missing", "path": path})
            continue
        local = local_path.read_bytes()
        raw_url = f"{RAW_ROOT}/{quote(path, safe='/')}"
        try:
            public = fetch(raw_url, "application/octet-stream")
        except Exception as exc:
            failures.append({"kind": "public_fetch", "path": path, "detail": str(exc)})
            continue
        local_sha = hashlib.sha256(local).hexdigest()
        public_sha = hashlib.sha256(public).hexdigest()
        rec = {
            "path": path,
            "status": entry.get("status"),
            "bytes": len(public),
            "local_bytes": len(local),
            "sha256": public_sha,
            "local_sha256": local_sha,
            "blob_sha": entry.get("sha"),
            "raw_url": raw_url,
            "match": public == local,
        }
        records.append(rec)
        aggregate += len(public)
        if public != local:
            failures.append({"kind": "byte_mismatch", "path": path})

    result = {
        "schema": "o015-github-original-01-public-readback-v1",
        "result": "pass" if not failures else "fail",
        "repository": f"https://github.com/{OWNER}/{REPO}",
        "branch": "main",
        "commit": commit_obj.get("sha"),
        "tree": (commit_obj.get("commit") or {}).get("tree", {}).get("sha"),
        "parent": ((commit_obj.get("parents") or [{}])[0]).get("sha"),
        "commit_message": ((commit_obj.get("commit") or {}).get("message")),
        "file_count": len(records),
        "aggregate_public_bytes": aggregate,
        "files": records,
        "failures": failures,
        "authenticated": False,
        "upstream_contact": False,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("result", "commit", "tree", "file_count", "aggregate_public_bytes", "failures")}, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
