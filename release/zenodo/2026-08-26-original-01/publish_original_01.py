#!/usr/bin/env python3
"""Publish and anonymously verify the Original-01 Zenodo checkpoint.

This publisher is bound to the existing O015 concept and its published
Becker-03 parent. It carries no credential in state or receipts, never
creates a second concept, and fails closed if the inherited namespace or the
requested replacement set differs from the frozen public inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import truststore

truststore.inject_into_ssl()
import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
API = "https://zenodo.org/api"
TOKEN_FILE = Path(r"C:\Users\Floris\Documents\Obsidian notes\New zenodo token.md")
PARENT_RECORD_ID = "22102236"
PARENT_RECORD_DOI = "10.5281/zenodo.22102236"
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.26-original-01-stochastic-composite-mirror-minibatch"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
PRIMARY_PDF = "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf"
PARENT_READBACK = ROOT / "release/zenodo/2026-08-25-becker-03/zenodo-public-readback-becker-03.json"
STATE_PATH = HERE / "zenodo-draft-original-01.json"
READBACK_PATH = HERE / "zenodo-public-readback-original-01.json"
CLOSURE_PATH = HERE / "zenodo-draft-closure-original-01.json"
MANIFEST_PATH = HERE / "release-manifest-original-01-zenodo.json"
SUMS_PATH = HERE / "SHA256SUMS-original-01"
RIGHTS_PATH = ROOT / "release/original-01/2026-08-26/package/RIGHTS_AND_PROVENANCE_ORIGINAL_01.md"
PACKAGE_PATH = ROOT / "release/original-01/2026-08-26/ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_ORIGINAL_01_2026.08.26.zip"

CORE_ADDITIONS = {
    PRIMARY_PDF: ROOT / "output/pdf/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.pdf",
    "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html": ROOT / "output/html/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html",
    "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub": ROOT / "output/epub/D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub",
    PACKAGE_PATH.name: PACKAGE_PATH,
    "backend-records-2026.08.26-original-01.jsonl": ROOT / "backend/records.jsonl",
    "backend-records-2026.08.26-original-01.csv": ROOT / "backend/records.csv",
    RIGHTS_PATH.name: RIGHTS_PATH,
}

EXPECTED_LOCAL = {
    PRIMARY_PDF: (486032, "7fafa5aff08ee02f6b79c8dcea7b4bf509570958f94dc94ae51fc9e66b9f6bca"),
    "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html": (353245, "052155a1edc7f8f81a84e5445e1408c3ffdef6e42899677bf80f6300bc7558a4"),
    "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub": (64322, "d3aaea87c928c825aac37310b3143e43c375f2ebb0ab4fe37bd0e34bfeab1f08"),
    PACKAGE_PATH.name: (721697, "8f175c21f404e20fccef2b42c2eaa1ccdf1599cfc89c189d1b912d3a0d3c454a"),
    "backend-records-2026.08.26-original-01.jsonl": (2941125, "d829eb7641e04aff41529be436818514d88dc3b2961d2d23fbc12d1d6b9fc35f"),
    "backend-records-2026.08.26-original-01.csv": (3537781, "4fd14cad8d08b0e551bf8ce8d306fc8ee11751a9b66e1717b7f1a3c16a822ab4"),
}

REPLACED_PARENT_FILES = {
    "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_BECKER_02_2026.08.25.zip",
    "release-manifest-becker-02-zenodo.json",
    "README_RELEASE_MIT_L03.md",
    "README_RELEASE_MIT_L04_L05.md",
    "README_RELEASE_MIT_L06.md",
    "README_RELEASE_MIT_L07.md",
    "README_RELEASE_MIT_L08.md",
    "README_RELEASE_MIT_L09.md",
    "backend-records-2026.08.25-becker-03.jsonl",
    "backend-records-2026.08.25-becker-03.csv",
}

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha_file(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value

def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": sha_file(path)}

def token() -> str:
    value = os.environ.get("ZENODO_TOKEN", "").strip()
    if len(value) >= 20:
        return value
    if not TOKEN_FILE.is_file():
        raise RuntimeError("ZENODO_TOKEN is absent and configured credential file is unavailable")
    text = TOKEN_FILE.read_text(encoding="utf-8")
    candidates: list[str] = []
    for line in text.splitlines():
        for match in re.finditer(r"(?i)(?:token|access[ -]?token|api[ -]?key)\s*[:=]\s*([A-Za-z0-9._-]{20,})", line):
            candidates.append(match.group(1))
    if not candidates:
        candidates = re.findall(r"(?<![A-Za-z0-9])[A-Za-z0-9._-]{20,}(?![A-Za-z0-9])", text)
    if not candidates:
        raise RuntimeError("no usable token found in configured credential file")
    return candidates[0]

def session(authenticated: bool = True) -> requests.Session:
    client = requests.Session()
    client.headers.update({"User-Agent": "o015-original-01-publisher/1"})
    if authenticated:
        client.headers.update({"Authorization": f"Bearer {token()}"})
    return client

def get_json(client: requests.Session, url: str, label: str, **kwargs) -> dict:
    response = None
    for attempt in range(1, 6):
        response = client.get(url, timeout=120, **kwargs)
        if response.status_code != 429 and response.status_code < 500:
            response.raise_for_status()
            value = response.json()
            if not isinstance(value, dict):
                raise RuntimeError(f"{label} returned non-object JSON")
            return value
        if attempt < 5:
            time.sleep(min(attempt * 2, 10))
    assert response is not None
    response.raise_for_status()
    raise RuntimeError(f"{label} failed")

def record_id(record: dict) -> str:
    return str(record.get("id"))

def record_doi(record: dict) -> str | None:
    return record.get("pids", {}).get("doi", {}).get("identifier") or record.get("doi") or record.get("metadata", {}).get("doi")

def concept_id(record: dict) -> str | None:
    parent = record.get("parent")
    if isinstance(parent, dict) and parent.get("id") is not None:
        return str(parent["id"])
    value = record.get("conceptrecid")
    return str(value) if value is not None else None

def public_entries(record: dict) -> dict[str, dict]:
    files = record.get("files")
    entries = files.get("entries", []) if isinstance(files, dict) else files
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise RuntimeError("unexpected public file inventory")
    result = {item.get("key") or item.get("filename"): item for item in entries}
    if None in result or len(result) != len(entries):
        raise RuntimeError("duplicate/missing public file keys")
    return result

def parent_inventory() -> dict[str, dict[str, object]]:
    receipt = read_json(PARENT_READBACK)
    if receipt.get("result") != "pass" or str(receipt.get("record_id")) != PARENT_RECORD_ID or receipt.get("record_doi") != PARENT_RECORD_DOI or receipt.get("concept_doi") != CONCEPT_DOI or receipt.get("file_count") != 100:
        raise RuntimeError("frozen Becker-03 receipt does not bind required parent")
    entries = {item["filename"]: {"bytes": item["bytes"], "sha256": item["sha256"]} for item in receipt["files"]}
    if len(entries) != 100:
        raise RuntimeError("parent receipt file count is not 100")
    return entries

def inherited_inventory() -> dict[str, dict[str, object]]:
    return {name: value for name, value in parent_inventory().items() if name not in REPLACED_PARENT_FILES}

def addition_paths() -> dict[str, Path]:
    return {**CORE_ADDITIONS, MANIFEST_PATH.name: MANIFEST_PATH, SUMS_PATH.name: SUMS_PATH}

def expected_inventory() -> dict[str, dict[str, object]]:
    return {**inherited_inventory(), **{name: identity(path) for name, path in addition_paths().items()}}

def metadata_payload() -> dict:
    description = (
        "<p>Checkpoint reader-first Bahasa Indonesia untuk <em>Optimisasi Lanjut dan Analisis Konveks</em>. "
        "Tranche Original-01 menutup metode proksimal stokastik komposit, varians minibatch dengan dan tanpa "
        "penggantian, penurunan cermin stokastik dalam geometri Bregman, serta jembatan Prox-SAGA yang dibatasi "
        "secara eksplisit. Edisi kursus yang lebih besar tetap parsial.</p>"
        "<p>Versi ini membawa PDF, HTML, dan EPUB pembaca, enam latihan dengan petunjuk bertahap dan solusi lengkap, "
        "laboratorium deterministik, serta paket sumber ringkas. Dua build bersih untuk setiap pembaca, 17 pemeriksaan "
        "matematika terbuka, EPUBCheck 5.3.0 tanpa fatal/error/warning/usage, QA visual semua 16 halaman PDF, reflow "
        "desktop/tablet/ponsel, pemeriksaan hak/non-overlap, rereview independen P1=P2=P3=0, dan backend 3.943 "
        "rekaman lulus. Backend mempertahankan 3.585 rekaman sebelumnya dan menambahkan 358 rekaman Original-01; "
        "pasangan backend Becker-03 yang digantikan dan delapan alat bantu rilis lama tidak diulang hanya dalam versi "
        "ini, sedangkan versi Zenodo terdahulu tetap tidak berubah.</p>"
        "<p>Hak berlaku per komponen. Materi substantif dan laboratorium baru berlisensi CC BY-SA 4.0. "
        "Kelas <em>shinybook.cls</em> yang disalin persis dan adaptasi <em>macros-id.tex</em> berasal dari Andreas "
        "Habring, arXiv:2607.11664v1, dengan bukti lisensi tingkat kiriman CC BY 4.0; keduanya tidak dilisensikan "
        "ulang sebagai CC BY-SA. Saksi matematis Royer, Becker, Rosasco–Villa–Vũ, Beck–Teboulle, dan "
        "Defazio–Bach–Lacoste-Julien hanya dipakai untuk verifikasi; tidak ada prosa, tata letak, gambar, latihan, "
        "solusi, atau kode mereka yang didistribusikan. Tidak ada lisensi menyeluruh untuk campuran berkas ini, dan "
        "edisi mandiri ini tidak menyiratkan tinjauan, persetujuan, sponsor, atau dukungan pihak sumber.</p>"
        "<p>Variational inequalities, operator monoton maksimal, resolven dan splitting, asesmen kumulatif, "
        "capstone, dan penutupan PDF bertag masih terbuka. HTML dan EPUB adalah permukaan reflow pilihan; PDF dapat "
        "dicari tetapi belum bertag. Provenans produksi: "
        f"{MODEL}, atas instruksi pengguna repositori.</p>"
    )
    metadata = {
        "title": "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia (id-ID): Tranche Asli 1; Kursus Parsial",
        "publication_date": "2026-08-26",
        "publisher": "Zenodo",
        "version": VERSION,
        "resource_type": {"id": "publication-other"},
        "languages": [{"id": "ind"}],
        "description": description,
        "creators": [
            {"person_or_org": {"family_name": "Habring", "given_name": "Andreas", "name": "Habring, Andreas", "type": "personal"}},
            {"person_or_org": {"family_name": "Becker", "given_name": "Stephen", "name": "Becker, Stephen", "type": "personal"}},
            {"person_or_org": {"family_name": "Griffin", "given_name": "Christopher", "name": "Griffin, Christopher", "type": "personal"}},
        ],
        "contributors": [
            {"person_or_org": {"family_name": "Royer", "given_name": "Clément W.", "name": "Royer, Clément W.", "type": "personal"}, "role": {"id": "other"}},
            {"person_or_org": {"family_name": "Krock", "given_name": "Mitchell", "name": "Krock, Mitchell", "type": "personal"}, "role": {"id": "other"}},
            {"person_or_org": {"name": "TTP", "type": "organizational"}, "role": {"id": "other"}},
        ],
        "rights": [
            {"title": {"en": "Mixed-license record — rights apply per file and source relation"}, "description": {"en": "No blanket license is asserted; consult the bundled rights note and component ledger."}, "link": "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id/blob/main/00_control/COMPONENT_RIGHTS.csv"},
            {"id": "cc-by-sa-4.0"},
            {"id": "cc-by-4.0"},
        ],
        "related_identifiers": [
            {"identifier": "10.48550/arXiv.2607.11664", "relation_type": {"id": "isderivedfrom"}, "resource_type": {"id": "publication-book"}, "scheme": "doi"},
            {"identifier": "https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id", "relation_type": {"id": "isdocumentedby"}, "resource_type": {"id": "software"}, "scheme": "url"},
            {"identifier": "https://github.com/stephenbeckr/convex-optimization-class/tree/98ed6930084c435ba0f675f7646ced1f2fd8729e", "relation_type": {"id": "isderivedfrom"}, "resource_type": {"id": "software"}, "scheme": "url"},
        ],
        "subjects": [{"subject": value} for value in ("Bahasa Indonesia", "id-ID", "convex analysis", "convex optimization", "stochastic optimization", "mirror descent", "variance reduction", "open educational resources")],
    }
    return {"access": {"files": "public", "record": "public"}, "files": {"enabled": True, "default_preview": PRIMARY_PDF}, "metadata": metadata}

def validate_metadata(metadata: dict) -> None:
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = str(metadata.get("title", ""))
    description = str(metadata.get("description", ""))
    if "TTP" in title or "TTP" in description or serialized.count("TTP") != 1:
        raise RuntimeError("metadata organization policy failed")
    if serialized.count(MODEL) != 1 or metadata.get("version") != VERSION:
        raise RuntimeError("metadata provenance/version policy failed")
    for marker in ("CC BY-SA 4.0", "3.943", "P1=P2=P3=0", "edisi kursus yang lebih besar tetap parsial"):
        if marker.casefold() not in description.casefold():
            raise RuntimeError(f"metadata description lacks {marker!r}")

def build_local() -> dict:
    for name, path in CORE_ADDITIONS.items():
        if not path.is_file():
            raise RuntimeError(f"missing local addition: {path}")
        expected = EXPECTED_LOCAL.get(name)
        if expected and (path.stat().st_size, sha_file(path)) != expected:
            raise RuntimeError(f"local identity mismatch: {name}")
    if "TTP" in RIGHTS_PATH.read_text(encoding="utf-8"):
        raise RuntimeError("rights note contains forbidden organization label")
    parent = parent_inventory()
    inherited = inherited_inventory()
    additions = {name: identity(path) for name, path in CORE_ADDITIONS.items()}
    manifest = {
        "schema": "o015-zenodo-original-01-release-manifest-v1",
        "title": metadata_payload()["metadata"]["title"],
        "publication_date": "2026-08-26",
        "status": "partial",
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "parent_public_readback": {"path": str(PARENT_READBACK), "bytes": PARENT_READBACK.stat().st_size, "sha256": sha_file(PARENT_READBACK)},
        "source": {"canonical_spine": "Andreas Habring arXiv:2607.11664v1", "source_tar_sha256": "d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748", "license": "CC BY 4.0"},
        "boundary": {"unit_id": "d90.orig.v1.tr01.unit", "segments": 8, "equations": 40, "exercises": 6, "hints": 6, "complete_solutions": 6, "next_cursor": "variational inequalities, maximal monotone operators, resolvents, and splitting"},
        "backend": {"protected_records": 3585, "added_records": 358, "records": 3943, "jsonl_sha256": additions["backend-records-2026.08.26-original-01.jsonl"]["sha256"], "csv_sha256": additions["backend-records-2026.08.26-original-01.csv"]["sha256"]},
        "rights": {"new_substantive_layer": "CC BY-SA 4.0", "Habring_scaffold": "CC BY 4.0 submission-level evidence", "component_specific": True, "blanket_license_claim": False},
        "replaced_parent_files": sorted(REPLACED_PARENT_FILES),
        "retained_parent_file_count": len(inherited),
        "additions_before_manifest_and_sums": additions,
        "expected_public_file_count": len(inherited) + len(CORE_ADDITIONS) + 2,
        "model_provenance": MODEL,
        "upstream_contact": False,
    }
    write_json(MANIFEST_PATH, manifest)
    additions_with_manifest = {**CORE_ADDITIONS, MANIFEST_PATH.name: MANIFEST_PATH}
    SUMS_PATH.write_text("".join(f"{sha_file(path)}  {name}\n" for name, path in sorted(additions_with_manifest.items())), encoding="utf-8", newline="\n")
    expected = expected_inventory()
    if len(parent) != 100 or len(inherited) != 90 or len(expected) != 99:
        raise RuntimeError(f"namespace arithmetic mismatch: parent={len(parent)} inherited={len(inherited)} final={len(expected)}")
    validate_metadata(metadata_payload()["metadata"])
    return {"result": "pass", "parent_files": len(parent), "retained_files": len(inherited), "addition_files": len(addition_paths()), "expected_public_files": len(expected), "manifest": identity(MANIFEST_PATH), "checksums": identity(SUMS_PATH)}

def verify_parent_public() -> dict:
    record = get_json(session(False), f"{API}/records/{PARENT_RECORD_ID}", "parent")
    if record_id(record) != PARENT_RECORD_ID or record_doi(record) != PARENT_RECORD_DOI or concept_id(record) != CONCEPT_ID or record.get("status") != "published":
        raise RuntimeError("live parent lineage mismatch")
    entries = public_entries(record)
    expected = parent_inventory()
    if set(entries) != set(expected) or len(entries) != 100:
        raise RuntimeError("live parent namespace drift")
    for name, item in entries.items():
        if item.get("size") != expected[name]["bytes"]:
            raise RuntimeError(f"live parent size drift: {name}")
    return record

def remote_file_entries(client: requests.Session, record: str) -> dict[str, dict]:
    value = get_json(client, f"{API}/records/{record}/draft/files", "draft-files")
    entries = value.get("entries", value)
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise RuntimeError("unexpected draft file response")
    result = {item.get("key"): item for item in entries}
    if None in result or len(result) != len(entries):
        raise RuntimeError("duplicate/missing draft file keys")
    return result

def save_state(record: dict) -> dict:
    identifier = record_id(record)
    if not identifier.isdigit():
        raise RuntimeError("Zenodo response lacks numeric record id")
    value = {"schema": "o015-zenodo-original-01-draft-v1", "status": record.get("status") or ("published" if record.get("is_published") else "draft"), "draft_id": identifier, "draft_doi": record_doi(record), "version": VERSION, "parent_record_id": PARENT_RECORD_ID, "parent_record_doi": PARENT_RECORD_DOI, "concept_id": CONCEPT_ID, "concept_doi": CONCEPT_DOI}
    write_json(STATE_PATH, value)
    return value

def state() -> dict:
    value = read_json(STATE_PATH)
    if value.get("schema") != "o015-zenodo-original-01-draft-v1" or value.get("version") != VERSION or value.get("concept_id") != CONCEPT_ID:
        raise RuntimeError("state belongs to another release")
    return value

def ensure_namespace(client: requests.Session, record: str) -> dict[str, dict]:
    entries = remote_file_entries(client, record)
    parent_names = set(parent_inventory())
    inherited_names = set(inherited_inventory())
    addition_names = set(addition_paths())
    if not entries:
        response = client.post(f"{API}/records/{record}/draft/actions/files-import", timeout=300)
        response.raise_for_status()
        for _ in range(120):
            entries = remote_file_entries(client, record)
            if parent_names.issubset(entries):
                break
            time.sleep(1)
    actual = set(entries)
    if (actual - parent_names - addition_names) or (inherited_names - actual):
        raise RuntimeError("draft cannot be safely resumed before pruning")
    endpoint = f"{API}/records/{record}/draft/files"
    for name in sorted(REPLACED_PARENT_FILES & actual):
        response = client.delete(f"{endpoint}/{quote(name, safe='')}", timeout=60)
        if response.status_code not in (200, 204):
            response.raise_for_status()
    entries = remote_file_entries(client, record)
    actual = set(entries)
    if (actual - inherited_names - addition_names) or (inherited_names - actual) or (actual & REPLACED_PARENT_FILES):
        raise RuntimeError("bounded parent pruning did not converge")
    return entries

def create_or_recover(client: requests.Session) -> str:
    if STATE_PATH.is_file():
        current = state()
        record = str(current["draft_id"])
        if current.get("status") == "published":
            return record
        draft = get_json(client, f"{API}/records/{record}/draft", "existing-draft")
        if record_id(draft) != record or draft.get("status") == "published":
            raise RuntimeError("saved state does not identify an editable draft")
        return record
    response = client.post(f"{API}/records/{PARENT_RECORD_ID}/versions", timeout=120)
    if response.status_code == 409:
        raise RuntimeError("an unrecorded open version draft exists; refusing to create a duplicate")
    response.raise_for_status()
    record = str(response.json().get("id"))
    if not record.isdigit() or record == PARENT_RECORD_ID:
        raise RuntimeError("version endpoint returned an unsafe record id")
    draft = get_json(client, f"{API}/records/{record}/draft", "new-draft")
    save_state(draft)
    return record

def prepare() -> dict:
    local = build_local()
    verify_parent_public()
    client = session(True)
    record = create_or_recover(client)
    ensure_namespace(client, record)
    response = client.put(f"{API}/records/{record}/draft", json=metadata_payload(), timeout=120)
    response.raise_for_status()
    updated = response.json()
    validate_metadata(updated["metadata"])
    save_state(updated)
    return {**local, "draft_id": record}

def upload_one(client: requests.Session, record: str, name: str, path: Path, existing: dict[str, dict]) -> None:
    endpoint = f"{API}/records/{record}/draft/files"
    old = existing.get(name)
    expected_md5 = f"md5:{sha_file(path, 'md5')}"
    if old and old.get("status") == "completed" and old.get("size") == path.stat().st_size and old.get("checksum") == expected_md5:
        return
    if old:
        client.delete(f"{endpoint}/{quote(name, safe='')}", timeout=60).raise_for_status()
    client.post(endpoint, json=[{"key": name}], timeout=60).raise_for_status()
    with path.open("rb") as stream:
        client.put(f"{endpoint}/{quote(name, safe='')}/content", data=stream, headers={"Content-Type": "application/octet-stream"}, timeout=600).raise_for_status()
    client.post(f"{endpoint}/{quote(name, safe='')}/commit", timeout=60).raise_for_status()

def upload() -> dict:
    local = build_local()
    current = state()
    if current.get("status") == "published":
        raise RuntimeError("release is already published")
    client = session(True)
    record = str(current["draft_id"])
    draft = get_json(client, f"{API}/records/{record}/draft", "draft")
    validate_metadata(draft["metadata"])
    existing = ensure_namespace(client, record)
    order = [PRIMARY_PDF, "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.html", "D90-ORIG-01-metode-stokastik-komposit-cermin-minibatch-id.epub", PACKAGE_PATH.name, "backend-records-2026.08.26-original-01.jsonl", "backend-records-2026.08.26-original-01.csv", RIGHTS_PATH.name, MANIFEST_PATH.name, SUMS_PATH.name]
    additions = addition_paths()
    for name in order:
        upload_one(client, record, name, additions[name], existing)
        existing = remote_file_entries(client, record)
    response = client.put(f"{API}/records/{record}/draft", json=metadata_payload(), timeout=120)
    response.raise_for_status()
    validate_metadata(response.json()["metadata"])
    return {**local, "result": "pass", "draft_id": record, "file_count": len(expected_inventory())}

def validate_draft() -> dict:
    build_local()
    current = state()
    record = str(current["draft_id"])
    client = session(True)
    draft = get_json(client, f"{API}/records/{record}/draft", "draft")
    validate_metadata(draft["metadata"])
    entries = remote_file_entries(client, record)
    expected = expected_inventory()
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("draft namespace differs from exact 99-file plan")
    for name, path in addition_paths().items():
        item = entries[name]
        if item.get("status") != "completed" or item.get("size") != path.stat().st_size or item.get("checksum") != f"md5:{sha_file(path, 'md5')}":
            raise RuntimeError(f"draft addition mismatch: {name}")
    return {"result": "pass", "draft_id": record, "file_count": 99, "all_additions_completed": True}

def publish() -> dict:
    current = state()
    record = str(current["draft_id"])
    if current.get("status") == "published":
        return readback()
    validate_draft()
    response = session(True).post(f"{API}/records/{record}/draft/actions/publish", timeout=180)
    if response.status_code not in (200, 201, 202, 409):
        response.raise_for_status()
    for attempt in range(1, 16):
        candidate = session(False).get(f"{API}/records/{record}", timeout=120)
        if candidate.status_code == 200 and candidate.json().get("status") == "published":
            published = candidate.json()
            save_state(published)
            return readback()
        if candidate.status_code not in (404, 429) and 400 <= candidate.status_code < 500:
            candidate.raise_for_status()
        if attempt < 15:
            time.sleep(min(attempt * 2, 12))
    raise RuntimeError("published record did not become anonymously visible")

def download(client: requests.Session, item: dict) -> bytes:
    url = item.get("links", {}).get("content") or item.get("links", {}).get("download") or item.get("links", {}).get("self")
    if not url:
        raise RuntimeError("public file lacks a content URL")
    response = None
    for attempt in range(1, 9):
        response = client.get(url, timeout=600)
        if response.status_code != 429 and response.status_code < 500:
            response.raise_for_status()
            return response.content
        if attempt < 8:
            time.sleep(min(2 ** attempt, 20))
    assert response is not None
    response.raise_for_status()
    raise RuntimeError("public file download retry budget exhausted")

def readback() -> dict:
    build_local()
    current = state()
    record = str(current["draft_id"])
    client = session(False)
    public = get_json(client, f"{API}/records/{record}", "published-record")
    if record_id(public) != record or public.get("status") != "published" or concept_id(public) != CONCEPT_ID or record_doi(public) is None:
        raise RuntimeError("public record identity/status mismatch")
    metadata = public.get("metadata", {})
    validate_metadata(metadata)
    entries = public_entries(public)
    expected = expected_inventory()
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("public namespace differs from exact 99-file plan")
    inherited = inherited_inventory()
    verified: list[dict] = []
    for index, name in enumerate(sorted(expected)):
        if index:
            time.sleep(0.35)
        payload = download(client, entries[name])
        wanted = expected[name]
        if len(payload) != wanted["bytes"] or sha_bytes(payload) != wanted["sha256"]:
            raise RuntimeError(f"public byte identity mismatch: {name}")
        verified.append({"filename": name, "bytes": len(payload), "sha256": sha_bytes(payload), "disposition": "inherited_unchanged" if name in inherited else "original_01_addition", "public_byte_identity": "pass"})
    file_state = get_json(client, f"{API}/records/{record}/files", "public-file-state")
    preview = file_state.get("default_preview")
    if preview != PRIMARY_PDF:
        raise RuntimeError(f"public default preview is {preview!r}, expected {PRIMARY_PDF!r}")
    serialized = json.dumps(metadata, ensure_ascii=False)
    receipt = {"schema": "o015-zenodo-original-01-public-readback-v1", "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "result": "pass", "record_id": record, "record_doi": record_doi(public), "record_url": public.get("links", {}).get("self_html") or public.get("links", {}).get("record_html"), "concept_id": CONCEPT_ID, "concept_doi": CONCEPT_DOI, "parent_record_id": PARENT_RECORD_ID, "parent_record_doi": PARENT_RECORD_DOI, "status": public.get("status"), "is_latest": public.get("versions", {}).get("is_latest", True), "default_preview": preview, "default_preview_source": f"{API}/records/{record}/files", "title": metadata.get("title"), "version": metadata.get("version"), "file_count": len(verified), "inherited_file_count": sum(x["disposition"] == "inherited_unchanged" for x in verified), "addition_file_count": sum(x["disposition"] == "original_01_addition" for x in verified), "removed_parent_files": sorted(REPLACED_PARENT_FILES), "files": verified, "metadata_ttp_mentions": serialized.count("TTP"), "model_provenance_mentions": serialized.count(MODEL), "credential_material_recorded": False, "upstream_contact": False}
    if receipt["file_count"] != 99 or receipt["inherited_file_count"] != 90 or receipt["addition_file_count"] != 9 or receipt["metadata_ttp_mentions"] != 1 or receipt["model_provenance_mentions"] != 1:
        raise RuntimeError("public release gate arithmetic/metadata check failed")
    write_json(READBACK_PATH, receipt)
    return receipt

def closure() -> dict:
    current = state()
    if current.get("status") != "published":
        raise RuntimeError("cannot close an unpublished record")
    record = str(current["draft_id"])
    client = session(True)
    direct = client.get(f"{API}/records/{record}/draft", timeout=120)
    if direct.status_code != 404:
        raise RuntimeError(f"published record still exposes a draft: HTTP {direct.status_code}")
    response = client.get(f"{API}/user/records", params={"size": 100, "sort": "mostrecent"}, timeout=120)
    response.raise_for_status()
    hits = response.json().get("hits", {}).get("hits", [])
    drafts = [str(x.get("id")) for x in hits if isinstance(x, dict) and x.get("status") == "draft" and concept_id(x) == CONCEPT_ID]
    if drafts:
        raise RuntimeError(f"concept lineage still has open drafts: {drafts}")
    result = {"schema": "o015-zenodo-original-01-draft-closure-v1", "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "result": "pass", "record_id": record, "record_doi": current.get("draft_doi"), "concept_id": CONCEPT_ID, "concept_doi": CONCEPT_DOI, "authenticated_draft_lookup_status": 404, "concept_open_draft_count": 0, "credential_material_recorded": False}
    write_json(CLOSURE_PATH, result)
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "prepare", "upload", "validate", "publish", "readback", "release", "closure"))
    action = parser.parse_args().action
    if action == "build":
        result = build_local()
    elif action == "prepare":
        result = prepare()
    elif action == "upload":
        result = upload()
    elif action == "validate":
        result = validate_draft()
    elif action == "publish":
        result = publish()
    elif action == "readback":
        result = readback()
    elif action == "closure":
        result = closure()
    else:
        prepare()
        upload()
        result = publish()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
