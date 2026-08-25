#!/usr/bin/env python3
"""Build, publish, and anonymously verify the Becker-02 Zenodo checkpoint.

Credentials are accepted only through the ZENODO_TOKEN process environment
variable. No credential value is serialized, printed, copied, or placed in a
URL. The replacement namespace is explicit and fail-closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

import requests


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
API = "https://zenodo.org/api"
PARENT_RECORD_ID = "22096817"
PARENT_RECORD_DOI = "10.5281/zenodo.22096817"
PARENT_VERSION = "checkpoint-2026.08.25-becker-01-lagrange-slater-kkt"
PARENT_TITLE = (
    "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia (id-ID): "
    "Dualitas Lagrange, Slater, dan KKT; Kursus Parsial"
)
CONCEPT_ID = "22059741"
CONCEPT_DOI = "10.5281/zenodo.22059741"
VERSION = "checkpoint-2026.08.25-becker-02-douglas-rachford"
MODEL_ID = "OpenAI Codex gpt-5.6-sol, Ultra"
FORBIDDEN_ORG_EXPANSION = "Translation and Transcription Project"
GITHUB_COMMIT = "2923d8b6e06f1ced65a91be4bd63e4766e1fb5b7"
GITHUB_TREE = "b44b2d044d015ead4913f332588170238549820f"
PRIMARY_PDF = "D90-BECKER-02-pemisahan-douglas-rachford-id.pdf"

PARENT_READBACK = (
    ROOT
    / "release"
    / "zenodo"
    / "2026-08-25-becker-01"
    / "zenodo-public-readback-becker-01.json"
)
STATE_PATH = HERE / "zenodo-draft-becker-02.json"
READBACK_PATH = HERE / "zenodo-public-readback-becker-02.json"
DRAFT_CLOSURE_PATH = HERE / "zenodo-draft-closure-becker-02.json"
PREVIEW_REPAIR_PATH = HERE / "zenodo-default-preview-repair-becker-02.json"
MANIFEST_PATH = HERE / "release-manifest-becker-02-zenodo.json"
SUMS_PATH = HERE / "SHA256SUMS-becker-02"
RIGHTS_PATH = HERE / "RIGHTS_AND_PROVENANCE_BECKER_02.md"

CORE_PUBLIC_PATHS = {
    "D90-BECKER-02-pemisahan-douglas-rachford-id.pdf": ROOT
    / "output/pdf/D90-BECKER-02-pemisahan-douglas-rachford-id.pdf",
    "D90-BECKER-02-pemisahan-douglas-rachford-id.html": ROOT
    / "output/html/D90-BECKER-02-pemisahan-douglas-rachford-id.html",
    "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_BECKER_02_2026.08.25.zip": ROOT
    / "release/becker-02/2026-08-25/ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_BECKER_02_2026.08.25.zip",
    "backend-records-2026.08.25-becker-02.jsonl": ROOT / "backend/records.jsonl",
    "backend-records-2026.08.25-becker-02.csv": ROOT / "backend/records.csv",
    RIGHTS_PATH.name: RIGHTS_PATH,
}

EXPECTED_LOCAL = {
    "D90-BECKER-02-pemisahan-douglas-rachford-id.pdf": (
        458915,
        "32e26d96a0878ad2a5e798a099759eb4351cbe728a2d2b912757ebc402e49794",
    ),
    "D90-BECKER-02-pemisahan-douglas-rachford-id.html": (
        18370,
        "ff42d60d3bdce967341f69932a07cb85af868b3f4bb02a10f8beb627198719fe",
    ),
    "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_BECKER_02_2026.08.25.zip": (
        482742,
        "b97f1ea849f1edb5a46422bda94e06e4217405a8642217f3d4a7ed740f0c5f6e",
    ),
    "backend-records-2026.08.25-becker-02.jsonl": (
        2623909,
        "6943678e867b5f72a509e1dbc57dcdbc61c79cc7ced3828fc3b8da999dff3ae6",
    ),
    "backend-records-2026.08.25-becker-02.csv": (
        3142537,
        "4e3249844a4948f02522c300ff69d313cabda2768d23f7f6f674b9c25ae08f97",
    ),
}

SUPERSEDED_DELTA_ZIPS = {
    "backend-records-2026.08.25-becker-01.jsonl",
    "backend-records-2026.08.25-becker-01.csv",
    "README_RELEASE_MIT_L01.md",
    "SHA256SUMS-mit-l01",
    "release-manifest-mit-l01.json",
    "README_RELEASE_MIT_L02.md",
    "SHA256SUMS-mit-l02",
    "release-manifest-mit-l02.json",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def identity(path: Path) -> dict[str, object]:
    return {
        "bytes": path.stat().st_size,
        "sha256": file_digest(path),
    }


def parent_inventory() -> dict[str, dict[str, object]]:
    receipt = read_json(PARENT_READBACK)
    if (
        receipt.get("result") != "pass"
        or receipt.get("record_id") != PARENT_RECORD_ID
        or receipt.get("record_doi") != PARENT_RECORD_DOI
        or receipt.get("concept_doi") != CONCEPT_DOI
        or receipt.get("file_count") != 99
    ):
        raise RuntimeError("frozen parent readback does not bind the required lineage")
    entries = {
        item["filename"]: {"bytes": item["bytes"], "sha256": item["sha256"]}
        for item in receipt["files"]
    }
    if len(entries) != 99 or not SUPERSEDED_DELTA_ZIPS.issubset(entries):
        raise RuntimeError("frozen parent inventory or bounded deletion set mismatch")
    return entries


def inherited_inventory() -> dict[str, dict[str, object]]:
    return {
        name: value
        for name, value in parent_inventory().items()
        if name not in SUPERSEDED_DELTA_ZIPS
    }


def metadata_payload() -> dict:
    description = (
        "<p>Checkpoint reader-first Bahasa Indonesia untuk <em>Optimisasi Lanjut dan Analisis Konveks</em>. "
        "Kursus yang lebih besar tetap parsial. Versi ini menambahkan modul nonduplikatif Pemisahan "
        "Douglas–Rachford dari repositori Stephen Becker pada commit 98ed6930084c435ba0f675f7646ced1f2fd8729e, "
        "dengan catatan ketik Mitchell Krock, sambil mempertahankan tulang punggung Habring v1 lengkap dan "
        "pembaca pendamping terdahulu.</p>"
        "<p>Modul mempertahankan tepat baris 2750–2797 dan mengecualikan materi program linear serta bagian ADMM "
        "yang bersebelahan. Tujuh koreksi matematis dan editorial diumumkan. Dua build PDF/HTML deterministik, delapan "
        "uji matematika terbuka, reflow desktop/tablet/seluler, inspeksi semua sembilan halaman PDF, rereview independen, "
        "dan backend lulus. Backend mempertahankan 3.320 rekaman sebelumnya dan menambahkan 110 rekaman, menjadi 3.430. "
        "Dua backend lama dan enam berkas metadata rilis MIT awal diganti hanya pada versi baru ini oleh PDF/HTML Becker-02, "
        "paket kelanjutan ringkas, backend mutakhir, catatan hak, manifest, dan checksum; versi Zenodo terdahulu tetap tak berubah.</p>"
        "<p>Hak berlaku per komponen. Sumber Becker berlisensi MIT dan dikreditkan kepada Stephen Becker serta Mitchell "
        "Krock, dengan kredit donor Bauschke–Combettes serta Lions–Mercier dipertahankan. Terjemahan, kata-kata koreksi, dan "
        "teks penghubung independen berlisensi CC BY-SA 4.0. Berkas warisan mempertahankan hak masing-masing: Habring "
        "CC BY 4.0, MIT OCW CC BY-NC-SA 4.0, Griffin/Penn CC BY-NC-SA 3.0 United States, dan Royer CC BY-NC 4.0. "
        "Tidak ada lisensi menyeluruh untuk seluruh rekaman campuran ini. Edisi independen ini tidak menyiratkan "
        "tinjauan, persetujuan, sponsor, atau dukungan oleh penulis maupun institusi sumber.</p>"
        "<p>Variasi-reduksi yang rigor, metode stokastik proksimal/cermin/minibatch, ketaksamaan "
        "variasional dan operator monoton maksimal/resolven, latihan, petunjuk, solusi lengkap, laboratorium, kapstone, "
        "dan penutupan aksesibilitas bertag masih terbuka. Bantuan produksi dan QA: "
        f"{MODEL_ID}, atas arahan pengguna repositori.</p>"
    )
    metadata = {
        "title": "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia (id-ID): Pemisahan Douglas–Rachford; Kursus Parsial",
        "publication_date": "2026-08-25",
        "publisher": "Zenodo",
        "version": VERSION,
        "resource_type": {"id": "publication-other"},
        "languages": [{"id": "ind"}],
        "description": description,
        "creators": [
            {"person_or_org": {"family_name": "Habring", "given_name": "Andreas", "name": "Habring, Andreas", "type": "personal"}},
            {"person_or_org": {"family_name": "Becker", "given_name": "Stephen", "name": "Becker, Stephen", "type": "personal"}},
            {"person_or_org": {"family_name": "Bertsekas", "given_name": "Dimitri P.", "name": "Bertsekas, Dimitri P.", "type": "personal"}},
            {"person_or_org": {"family_name": "Griffin", "given_name": "Christopher", "name": "Griffin, Christopher", "type": "personal"}},
        ],
        "contributors": [
            {"person_or_org": {"family_name": "Krock", "given_name": "Mitchell", "name": "Krock, Mitchell", "type": "personal"}, "role": {"id": "other"}},
            {"person_or_org": {"family_name": "Royer", "given_name": "Clément W.", "name": "Royer, Clément W.", "type": "personal"}, "role": {"id": "other"}},
            {"person_or_org": {"family_name": "Miller", "given_name": "Simon", "name": "Miller, Simon", "type": "personal"}, "role": {"id": "other"}},
            {"person_or_org": {"family_name": "Mercer", "given_name": "Douglas", "name": "Mercer, Douglas", "type": "personal"}, "role": {"id": "other"}},
            {"person_or_org": {"name": "TTP", "type": "organizational"}, "role": {"id": "other"}},
        ],
        "rights": [
            {
                "title": {"en": "Mixed-license record — rights apply per file and source relation"},
                "description": {"en": "No blanket license is asserted for this mixed-source record; consult RIGHTS_AND_PROVENANCE_BECKER_02.md and the component ledger."},
                "link": f"https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id/blob/{GITHUB_COMMIT}/00_control/COMPONENT_RIGHTS.csv",
            },
            {"id": "cc-by-sa-4.0"},
            {"id": "cc-by-4.0"},
            {"id": "cc-by-nc-sa-4.0"},
            {
                "title": {"en": "MIT License — Becker source components only"},
                "description": {"en": "Applies to the bounded source text from Stephen Becker's repository; translation and correction wording are separate."},
                "link": "https://opensource.org/license/mit",
            },
            {
                "title": {"en": "CC BY-NC-SA 3.0 United States — inherited Griffin/Penn components only"},
                "description": {"en": "Applies only to inherited Griffin/Penn-derived files."},
                "link": "https://creativecommons.org/licenses/by-nc-sa/3.0/us/",
            },
            {
                "title": {"en": "CC BY-NC 4.0 — inherited Royer components only"},
                "description": {"en": "Applies only to inherited Royer source-freeze components."},
                "link": "https://creativecommons.org/licenses/by-nc/4.0/",
            },
        ],
        "related_identifiers": [
            {"identifier": "10.48550/arXiv.2607.11664", "relation_type": {"id": "isderivedfrom"}, "resource_type": {"id": "publication-book"}, "scheme": "doi"},
            {"identifier": f"https://github.com/stephenbeckr/convex-optimization-class/tree/98ed6930084c435ba0f675f7646ced1f2fd8729e", "relation_type": {"id": "isderivedfrom"}, "resource_type": {"id": "software"}, "scheme": "url"},
            {"identifier": "https://ocw.mit.edu/courses/6-253-convex-analysis-and-optimization-spring-2012/", "relation_type": {"id": "isderivedfrom"}, "resource_type": {"id": "publication-other"}, "scheme": "url"},
            {"identifier": "https://sites.psu.edu/griffinch/files/2023/06/Math555_SRC.zip", "relation_type": {"id": "isderivedfrom"}, "resource_type": {"id": "publication-book"}, "scheme": "url"},
            {"identifier": "https://www.lamsade.dauphine.fr/~croyer/teachSG.html", "relation_type": {"id": "references"}, "resource_type": {"id": "publication-other"}, "scheme": "url"},
        ],
        "subjects": [
            {"subject": value}
            for value in (
                "Bahasa Indonesia", "id-ID", "convex analysis", "convex optimization",
                "Douglas-Rachford splitting", "proximal operator", "operator splitting",
                "open educational resources", "mathematical translation", "AI-assisted translation",
            )
        ],
    }
    return {
        "access": {"files": "public", "record": "public"},
        "files": {"enabled": True, "default_preview": PRIMARY_PDF},
        "metadata": metadata,
    }


def validate_metadata(metadata: dict) -> None:
    serialized = json.dumps(metadata, ensure_ascii=False)
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    contributors = metadata.get("contributors", [])
    ttp = []
    for item in contributors:
        person_or_org = item.get("person_or_org")
        if isinstance(person_or_org, dict):
            name = person_or_org.get("name")
            organizational = person_or_org.get("type") == "organizational"
        else:
            # Zenodo's live API flattens contributor entities and exposes the
            # contribution role as ``type``. The submitted payload is checked
            # separately above; accept only its exact normalized Other row.
            name = item.get("name")
            organizational = item.get("type") == "Other"
        if name == "TTP":
            ttp.append((item, organizational))
    if (
        "TTP" in title
        or "TTP" in description
        or FORBIDDEN_ORG_EXPANSION.casefold() in serialized.casefold()
        or serialized.count("TTP") != 1
        or len(ttp) != 1
        or not ttp[0][1]
        or serialized.count(MODEL_ID) != 1
        or metadata.get("version") != VERSION
    ):
        raise RuntimeError("metadata title/organization/model gate failed")
    for required in (
        "kursus yang lebih besar tetap parsial",
        "mitchell krock",
        "cc by-sa 4.0",
        "tidak ada lisensi menyeluruh",
        "3.430",
        "enam berkas metadata rilis mit",
    ):
        if required not in description.casefold():
            raise RuntimeError(f"metadata description lacks {required!r}")


def build_local() -> dict:
    parent = parent_inventory()
    inherited = inherited_inventory()
    if len(parent) != 99 or len(inherited) != 91:
        raise RuntimeError("parent/replacement arithmetic mismatch")
    for name, path in CORE_PUBLIC_PATHS.items():
        if not path.is_file():
            raise RuntimeError(f"missing addition: {path}")
        if name in EXPECTED_LOCAL:
            expected_bytes, expected_sha = EXPECTED_LOCAL[name]
            if path.stat().st_size != expected_bytes or file_digest(path) != expected_sha:
                raise RuntimeError(f"frozen local identity mismatch: {name}")
    rights_text = RIGHTS_PATH.read_text(encoding="utf-8")
    if FORBIDDEN_ORG_EXPANSION.casefold() in rights_text.casefold() or "TTP" in rights_text:
        raise RuntimeError("release rights note contains forbidden organization prose")
    additions = {
        name: {"bytes": path.stat().st_size, "sha256": file_digest(path)}
        for name, path in sorted(CORE_PUBLIC_PATHS.items())
    }
    manifest = {
        "schema": "o015-zenodo-becker-02-release-manifest-v1",
        "publication_date": "2026-08-25",
        "status": "partial",
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "github": {"commit": GITHUB_COMMIT, "tree": GITHUB_TREE},
        "authority": {
            "repository": "https://github.com/stephenbeckr/convex-optimization-class",
            "commit": "98ed6930084c435ba0f675f7646ced1f2fd8729e",
            "tree": "f04670e3f7be3d4836c380fd8bd31883e0b992c9",
            "license": "MIT",
            "typed_notes_credit": "Mitchell Krock",
        },
        "boundary": {
            "ranges": ["2750-2797"],
            "english_witness_sha256": "fdc368741a0a88eb9d21c69d655ac6ce1b44571c2d49c6a3302e3efc4673594b",
            "excluded_adjacent_material": [
                "ADMM material beginning after line 2797",
                "all O018 linear-programming material",
            ],
            "corrections": "O015-BECKER-ADV-0013 through O015-BECKER-ADV-0019",
        },
        "backend": {
            "protected_records": 3320,
            "added_records": 110,
            "records": 3430,
            "jsonl_sha256": EXPECTED_LOCAL["backend-records-2026.08.25-becker-02.jsonl"][1],
            "csv_sha256": EXPECTED_LOCAL["backend-records-2026.08.25-becker-02.csv"][1],
        },
        "rights": "mixed; per file and source relation; no blanket license",
        "replaced_parent_files": sorted(SUPERSEDED_DELTA_ZIPS),
        "retained_parent_files": inherited,
        "additions_before_manifest_and_sums": additions,
        "expected_public_file_count": 99,
        "model_provenance": MODEL_ID,
    }
    write_json(MANIFEST_PATH, manifest)
    sums_lines = [
        f"{file_digest(path)}  {name}"
        for name, path in sorted({**CORE_PUBLIC_PATHS, MANIFEST_PATH.name: MANIFEST_PATH}.items())
    ]
    SUMS_PATH.write_text("\n".join(sums_lines) + "\n", encoding="utf-8", newline="\n")
    validate_metadata(metadata_payload()["metadata"])
    expected = {**inherited, **addition_inventory()}
    paths = addition_paths()
    if len(paths) != 8 or len(expected) != 99 or set(expected) != set(inherited) | set(paths):
        raise RuntimeError("final 99-file namespace arithmetic mismatch")
    return {
        "result": "pass",
        "parent_files": len(parent),
        "removed_files": len(SUPERSEDED_DELTA_ZIPS),
        "retained_files": len(inherited),
        "addition_files": len(paths),
        "expected_public_files": len(expected),
        "manifest": identity(MANIFEST_PATH),
        "checksums": identity(SUMS_PATH),
        "addition_bytes": sum(path.stat().st_size for path in paths.values()),
    }


def addition_paths() -> dict[str, Path]:
    return {
        **CORE_PUBLIC_PATHS,
        MANIFEST_PATH.name: MANIFEST_PATH,
        SUMS_PATH.name: SUMS_PATH,
    }


def addition_inventory() -> dict[str, dict[str, object]]:
    if not MANIFEST_PATH.is_file() or not SUMS_PATH.is_file():
        raise RuntimeError("run build before computing addition inventory")
    return {
        name: {"bytes": path.stat().st_size, "sha256": file_digest(path)}
        for name, path in sorted(addition_paths().items())
    }


def expected_inventory() -> dict[str, dict[str, object]]:
    return {**inherited_inventory(), **addition_inventory()}


def token() -> str:
    value = os.environ.get("ZENODO_TOKEN", "").strip()
    if len(value) < 20:
        raise RuntimeError("ZENODO_TOKEN is absent from the process environment")
    return value


def session(*, authenticated: bool = True) -> requests.Session:
    client = requests.Session()
    client.headers.update({"User-Agent": "o015-becker-02-publisher/1"})
    if authenticated:
        client.headers.update({"Authorization": f"Bearer {token()}"})
    return client


def state() -> dict:
    value = read_json(STATE_PATH)
    if (
        value.get("schema") != "o015-zenodo-becker-02-draft-v1"
        or value.get("parent_record_id") != PARENT_RECORD_ID
        or value.get("concept_doi") != CONCEPT_DOI
        or value.get("version") != VERSION
    ):
        raise RuntimeError("draft state belongs to a different release")
    return value


def save_state(record: dict) -> dict:
    identifier = str(record.get("id"))
    if not identifier.isdigit():
        raise RuntimeError("Zenodo response lacks numeric record id")
    doi = record.get("pids", {}).get("doi", {}).get("identifier") or record.get("metadata", {}).get("doi")
    status = record.get("status") or ("published" if record.get("is_published") else "draft")
    receipt = {
        "schema": "o015-zenodo-becker-02-draft-v1",
        "status": status,
        "draft_id": identifier,
        "draft_doi": doi,
        "version": VERSION,
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
    }
    write_json(STATE_PATH, receipt)
    return receipt


def draft_id() -> str:
    return str(state()["draft_id"])


def get_json_retry(client: requests.Session, url: str, label: str) -> dict:
    response = None
    for attempt in range(1, 5):
        response = client.get(url, timeout=60)
        if response.status_code != 429 and response.status_code < 500:
            response.raise_for_status()
            value = response.json()
            if not isinstance(value, dict):
                raise RuntimeError(f"{label} returned non-object JSON")
            return value
        if attempt < 4:
            time.sleep(attempt * 2)
    if response is None:
        raise RuntimeError(f"{label} request did not run")
    response.raise_for_status()
    raise RuntimeError(f"{label} failed")


def record_id(record: dict) -> str:
    return str(record.get("id"))


def concept_id(record: dict) -> str | None:
    parent = record.get("parent")
    if isinstance(parent, dict) and parent.get("id") is not None:
        return str(parent["id"])
    value = record.get("conceptrecid")
    return str(value) if value is not None else None


def record_doi(record: dict) -> str | None:
    return (
        record.get("pids", {}).get("doi", {}).get("identifier")
        or record.get("doi")
        or record.get("metadata", {}).get("doi")
    )


def concept_doi(record: dict) -> str | None:
    value = record.get("conceptdoi")
    if isinstance(value, str) and value:
        return value
    parent = record.get("parent")
    if isinstance(parent, dict):
        return parent.get("pids", {}).get("doi", {}).get("identifier")
    return None


def verify_latest(client: requests.Session, record: dict) -> bool:
    if record.get("status") != "published":
        raise RuntimeError("record is not published")
    versions = record.get("versions")
    if isinstance(versions, dict) and "is_latest" in versions and versions["is_latest"] is not True:
        raise RuntimeError("record is not latest")
    latest_link = record.get("links", {}).get("latest")
    if latest_link:
        latest = get_json_retry(client, latest_link, "latest-version")
        if record_id(latest) != record_id(record) or concept_id(latest) != concept_id(record):
            raise RuntimeError("latest-version link mismatch")
    elif not (isinstance(versions, dict) and versions.get("is_latest") is True):
        raise RuntimeError("record exposes no latest-version proof")
    return True


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


def remote_file_state(client: requests.Session, record: str) -> dict:
    response = client.get(f"{API}/records/{record}/draft/files", timeout=60)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("unexpected draft file-state response")
    return data


def remote_entries(client: requests.Session, record: str) -> dict[str, dict]:
    data = remote_file_state(client, record)
    entries = data.get("entries", data) if isinstance(data, dict) else data
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        raise RuntimeError("unexpected draft file inventory")
    result = {item.get("key"): item for item in entries}
    if None in result or len(result) != len(entries):
        raise RuntimeError("duplicate/missing draft file keys")
    return result


def download(client: requests.Session, item: dict) -> bytes:
    links = item.get("links", {})
    url = links.get("content") or links.get("self") or links.get("download")
    if not url:
        raise RuntimeError("file entry lacks content link")
    response = None
    for attempt in range(1, 9):
        response = client.get(url, timeout=300)
        if response.status_code != 429 and response.status_code < 500:
            response.raise_for_status()
            return response.content
        if attempt == 8:
            break
        delay = min(2**attempt, 30)
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                delay = max(delay, min(float(retry_after), 30))
            except ValueError:
                pass
        reset = response.headers.get("X-RateLimit-Reset")
        if reset:
            try:
                delay = max(delay, min(float(reset) - time.time() + 1, 30))
            except ValueError:
                pass
        time.sleep(max(delay, 1))
    if response is None:
        raise RuntimeError("file download did not run")
    response.raise_for_status()
    raise RuntimeError("file download retry budget exhausted")


def verify_bytes(client: requests.Session, entries: dict[str, dict], expected: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    verified = []
    for index, name in enumerate(sorted(expected)):
        if index:
            time.sleep(1.1)
        if name not in entries:
            raise RuntimeError(f"missing remote file: {name}")
        payload = download(client, entries[name])
        if len(payload) != expected[name]["bytes"] or digest(payload) != expected[name]["sha256"]:
            raise RuntimeError(f"remote identity drift: {name}")
        verified.append({"filename": name, "bytes": len(payload), "sha256": digest(payload), "public_byte_identity": "pass"})
    return verified


def verify_parent_public() -> dict:
    record = get_json_retry(session(authenticated=False), f"{API}/records/{PARENT_RECORD_ID}", "parent")
    if (
        record_id(record) != PARENT_RECORD_ID
        or record_doi(record) != PARENT_RECORD_DOI
        or concept_id(record) != CONCEPT_ID
        or concept_doi(record) not in (None, CONCEPT_DOI)
    ):
        raise RuntimeError("live parent lineage mismatch")
    verify_latest(session(authenticated=False), record)
    entries = public_entries(record)
    expected = parent_inventory()
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("live parent namespace drift")
    for name, item in entries.items():
        if item.get("size") != expected[name]["bytes"]:
            raise RuntimeError(f"live parent size drift: {name}")
    return record


def validate_live_draft_identity(value: dict, record: str) -> dict:
    if not isinstance(value, dict) or record_id(value) != str(record):
        raise RuntimeError("draft lookup returned another record")
    if str(record) == PARENT_RECORD_ID:
        raise RuntimeError("refusing to mutate the immutable parent record")
    if value.get("status") == "published" or value.get("is_published") is True:
        raise RuntimeError("draft endpoint exposed a published record")
    if concept_id(value) != CONCEPT_ID or concept_doi(value) not in (None, CONCEPT_DOI):
        raise RuntimeError("live draft belongs to another concept lineage")
    metadata = value.get("metadata")
    if not isinstance(metadata, dict):
        raise RuntimeError("live draft lacks metadata")
    marker = (metadata.get("title"), metadata.get("version"))
    allowed = {
        (PARENT_TITLE, None),
        (PARENT_TITLE, PARENT_VERSION),
        (metadata_payload()["metadata"]["title"], VERSION),
    }
    if marker not in allowed:
        raise RuntimeError("live draft title/version is not the parent or Becker-02 release")
    return value


def get_draft(client: requests.Session, record: str) -> dict:
    response = client.get(f"{API}/records/{record}/draft", timeout=60)
    response.raise_for_status()
    return validate_live_draft_identity(response.json(), record)


def find_unbound_lineage_draft(client: requests.Session) -> dict:
    """Recover the one exact new-version draft after an interrupted create."""
    response = client.get(f"{API}/user/records", params={"size": 100, "sort": "mostrecent"}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    hits = payload.get("hits", {}).get("hits", []) if isinstance(payload, dict) else []
    candidates = []
    for item in hits:
        if (
            isinstance(item, dict)
            and item.get("status") == "draft"
            and concept_id(item) == CONCEPT_ID
            and record_id(item) != PARENT_RECORD_ID
        ):
            try:
                candidates.append(validate_live_draft_identity(item, record_id(item)))
            except RuntimeError:
                continue
    if len(candidates) != 1:
        raise RuntimeError(
            f"expected one recoverable Becker-02 lineage draft, found {len(candidates)}"
        )
    return get_draft(client, record_id(candidates[0]))


def ensure_imported_and_pruned(client: requests.Session, record: str) -> dict[str, dict]:
    entries = remote_entries(client, record)
    parent_names = set(parent_inventory())
    inherited_names = set(inherited_inventory())
    addition_names = set(addition_paths())
    if not entries:
        response = client.post(f"{API}/records/{record}/draft/actions/files-import", timeout=300)
        response.raise_for_status()
        for _ in range(90):
            entries = remote_entries(client, record)
            if parent_names.issubset(entries):
                break
            time.sleep(1)
    actual = set(entries)
    unexpected = actual - parent_names - addition_names
    missing_inherited = inherited_names - actual
    if unexpected or missing_inherited:
        raise RuntimeError(
            "draft cannot be resumed safely: "
            f"unexpected={sorted(unexpected)}, missing_inherited={sorted(missing_inherited)}"
        )
    endpoint = f"{API}/records/{record}/draft/files"
    for name in sorted(SUPERSEDED_DELTA_ZIPS & actual):
        response = client.delete(f"{endpoint}/{quote(name, safe='')}", timeout=60)
        if response.status_code not in (200, 204):
            response.raise_for_status()
    entries = remote_entries(client, record)
    actual = set(entries)
    unexpected = actual - inherited_names - addition_names
    missing_inherited = inherited_names - actual
    if unexpected or missing_inherited or actual & SUPERSEDED_DELTA_ZIPS:
        raise RuntimeError(
            "bounded deletion/resume did not converge: "
            f"unexpected={sorted(unexpected)}, missing_inherited={sorted(missing_inherited)}, "
            f"superseded_remaining={sorted(actual & SUPERSEDED_DELTA_ZIPS)}"
        )
    return entries


def upload_one(client: requests.Session, record: str, name: str, path: Path, existing: dict[str, dict]) -> None:
    endpoint = f"{API}/records/{record}/draft/files"
    old = existing.get(name)
    expected_md5 = f"md5:{file_digest(path, 'md5')}"
    if old and old.get("status") == "completed" and old.get("size") == path.stat().st_size and old.get("checksum") == expected_md5:
        return
    if old:
        client.delete(f"{endpoint}/{quote(name, safe='')}", timeout=60).raise_for_status()
    registration = client.post(endpoint, json=[{"key": name}], timeout=60)
    registration.raise_for_status()
    with path.open("rb") as stream:
        client.put(
            f"{endpoint}/{quote(name, safe='')}/content",
            data=stream,
            headers={"Content-Type": "application/octet-stream"},
            timeout=300,
        ).raise_for_status()
    client.post(f"{endpoint}/{quote(name, safe='')}/commit", timeout=60).raise_for_status()


def prepare() -> dict:
    local = build_local()
    verify_parent_public()
    client = session()
    if STATE_PATH.is_file():
        current = state()
        if current.get("status") == "published":
            raise RuntimeError("release is already published")
        record = draft_id()
        get_draft(client, record)
    else:
        response = client.post(f"{API}/records/{PARENT_RECORD_ID}/versions", timeout=60)
        if response.status_code == 409:
            recovered = find_unbound_lineage_draft(client)
            record = record_id(recovered)
            save_state(recovered)
        else:
            response.raise_for_status()
            record = str(response.json()["id"])
            save_state(get_draft(client, record))
    ensure_imported_and_pruned(client, record)
    response = client.put(f"{API}/records/{record}/draft", json=metadata_payload(), timeout=60)
    response.raise_for_status()
    updated = validate_live_draft_identity(response.json(), record)
    validate_metadata(updated["metadata"])
    save_state(updated)
    return {**local, "draft": state()}


def upload() -> dict:
    build_local()
    if state().get("status") == "published":
        raise RuntimeError("release already published")
    client = session()
    record = draft_id()
    draft = get_draft(client, record)
    validate_metadata(draft["metadata"])
    existing = remote_entries(client, record)
    inherited_names = set(inherited_inventory())
    addition_names = set(addition_paths())
    unexpected = set(existing) - inherited_names - addition_names
    missing_inherited = inherited_names - set(existing)
    if unexpected or missing_inherited:
        raise RuntimeError(
            "draft upload cannot resume safely: "
            f"unexpected={sorted(unexpected)}, missing_inherited={sorted(missing_inherited)}"
        )
    order = {
        "D90-BECKER-02-pemisahan-douglas-rachford-id.pdf": 0,
        "D90-BECKER-02-pemisahan-douglas-rachford-id.html": 1,
        "ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_BECKER_02_2026.08.25.zip": 2,
        "backend-records-2026.08.25-becker-02.jsonl": 3,
        "backend-records-2026.08.25-becker-02.csv": 4,
        RIGHTS_PATH.name: 5,
        MANIFEST_PATH.name: 6,
        SUMS_PATH.name: 7,
    }
    for name, path in sorted(addition_paths().items(), key=lambda item: order[item[0]]):
        upload_one(client, record, name, path, existing)
        existing = remote_entries(client, record)
    response = client.put(f"{API}/records/{record}/draft", json=metadata_payload(), timeout=60)
    response.raise_for_status()
    validate_metadata(response.json()["metadata"])
    validate_draft()
    return {"result": "pass", "draft_id": record, "addition_count": 8, "file_count": 99}


def validate_draft() -> dict:
    build_local()
    client = session()
    record = draft_id()
    draft = get_draft(client, record)
    validate_metadata(draft["metadata"])
    if metadata_payload().get("files", {}).get("default_preview") != PRIMARY_PDF:
        raise RuntimeError("local publication payload lacks the Becker-02 PDF preview")
    entries = remote_entries(client, record)
    file_state = remote_file_state(client, record)
    expected = expected_inventory()
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("draft namespace differs from exact 99-file plan")
    for name, path in addition_paths().items():
        item = entries[name]
        if item.get("status") != "completed" or item.get("size") != path.stat().st_size or item.get("checksum") != f"md5:{file_digest(path, 'md5')}":
            raise RuntimeError(f"draft addition metadata mismatch: {name}")
    if file_state.get("default_preview") != PRIMARY_PDF:
        raise RuntimeError("draft file state lacks the exact Becker-02 preview request")
    draft_preview = observed_preview(draft)
    if draft_preview != PRIMARY_PDF:
        # Zenodo can retain the inherited thumbnail while a new-version draft
        # is open even after accepting the requested default_preview. Permit
        # only a known PDF in the exact 99-file namespace; publish() then
        # performs the bounded same-record repair and anonymous proof.
        if draft_preview not in expected or not str(draft_preview).lower().endswith(".pdf"):
            raise RuntimeError("draft exposes neither the requested nor a bounded inherited PDF preview")
    verify_bytes(client, entries, expected)
    return {
        "result": "pass",
        "draft_id": record,
        "file_count": 99,
        "all_draft_bytes": "pass",
        "draft_preview": draft_preview,
        "post_publication_preview_repair_required": draft_preview != PRIMARY_PDF,
    }


def public_file_state(client: requests.Session, record: str) -> dict:
    value = get_json_retry(client, f"{API}/records/{record}/files", "public-file-state")
    entries = value.get("entries")
    if not isinstance(entries, list):
        raise RuntimeError("public file-state endpoint lacks an entry list")
    return value


def public_default_preview(client: requests.Session, record: str) -> str:
    preview = public_file_state(client, record).get("default_preview")
    if preview != PRIMARY_PDF:
        raise RuntimeError("public file-state does not select the Becker-02 PDF")
    return preview


def observed_preview(record: dict) -> str | None:
    files = record.get("files")
    if isinstance(files, dict) and isinstance(files.get("default_preview"), str):
        return files["default_preview"]
    strings: list[str] = []
    stack = [record.get("links", {}).get("thumbnails")]
    while stack:
        value = stack.pop()
        if isinstance(value, str):
            strings.append(unquote(value))
        elif isinstance(value, dict):
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    if strings:
        known_pdfs = {
            name
            for name in expected_inventory()
            if name.lower().endswith(".pdf")
        }
        matches = {
            name
            for name in known_pdfs
            if all(name in value for value in strings)
        }
        if len(matches) == 1:
            return matches.pop()
    return None


def repair_default_preview(record: dict) -> dict:
    """Repair only the same published record; never create another version."""
    identifier = record_id(record)
    before = public_file_state(session(authenticated=False), identifier).get("default_preview")
    if before == PRIMARY_PDF:
        return record
    if (
        identifier != draft_id()
        or concept_id(record) != CONCEPT_ID
        or concept_doi(record) not in (None, CONCEPT_DOI)
        or record_doi(record) is None
        or record.get("status") != "published"
    ):
        raise RuntimeError("refusing preview repair outside the published Becker-02 lineage")
    expected = expected_inventory()
    public = public_entries(record)
    if set(public) != set(expected) or len(public) != 99:
        raise RuntimeError("refusing preview repair because the public namespace differs")
    for name, item in public.items():
        if item.get("size") != expected[name]["bytes"]:
            raise RuntimeError(f"refusing preview repair after size drift: {name}")

    client = session()
    opened = client.post(f"{API}/records/{identifier}/draft", timeout=60)
    if opened.status_code == 409:
        draft = get_draft(client, identifier)
    else:
        opened.raise_for_status()
        draft = opened.json()
    if record_id(draft) != identifier:
        raise RuntimeError("same-record edit returned another record")
    entries = remote_entries(client, identifier)
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("same-record edit changed the file namespace")
    for name, item in entries.items():
        if item.get("size") != expected[name]["bytes"]:
            raise RuntimeError(f"same-record edit changed file size: {name}")

    response = client.put(f"{API}/records/{identifier}/draft", json=metadata_payload(), timeout=60)
    response.raise_for_status()
    updated = response.json()
    validate_metadata(updated["metadata"])
    file_state = remote_file_state(client, identifier)
    if file_state.get("default_preview") != PRIMARY_PDF:
        raise RuntimeError("same-record repair did not bind the Becker-02 preview request")
    try:
        response = client.post(f"{API}/records/{identifier}/draft/actions/publish", timeout=120)
        response.raise_for_status()
        published = response.json()
    except Exception:
        published = reconcile_publish(identifier)
        if published is None:
            raise
    if record_id(published) != identifier or record_doi(published) != record_doi(record):
        raise RuntimeError("preview repair changed the record identity or DOI")
    save_state(published)

    anonymous = None
    for attempt in range(1, 13):
        candidate = session(authenticated=False).get(f"{API}/records/{identifier}", timeout=60)
        if candidate.status_code == 200:
            value = candidate.json()
            visible_preview = public_file_state(session(authenticated=False), identifier).get("default_preview")
            if value.get("status") == "published" and visible_preview == PRIMARY_PDF:
                anonymous = value
                break
        elif candidate.status_code not in (404, 429) and candidate.status_code < 500:
            candidate.raise_for_status()
        if attempt < 12:
            time.sleep(min(attempt * 2, 10))
    if anonymous is None:
        raise RuntimeError("same-record preview repair is not anonymously visible")
    if set(public_entries(anonymous)) != set(expected):
        raise RuntimeError("preview repair altered the anonymous public namespace")
    write_json(
        PREVIEW_REPAIR_PATH,
        {
            "schema": "o015-zenodo-becker-02-default-preview-repair-v1",
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "result": "pass",
            "record_id": identifier,
            "record_doi": record_doi(anonymous),
            "concept_id": CONCEPT_ID,
            "concept_doi": CONCEPT_DOI,
            "operation": "same-record metadata edit and republish",
            "new_version_created": False,
            "file_bytes_changed": False,
            "file_count_before": 99,
            "file_count_after": 99,
            "default_preview_before": before,
            "default_preview_after": PRIMARY_PDF,
            "credential_material_recorded": False,
        },
    )
    return anonymous


def readback(wait: bool = False, repair_preview: bool = False) -> dict:
    build_local()
    client = session(authenticated=False)
    attempts = 12 if wait else 1
    response = None
    for attempt in range(1, attempts + 1):
        response = client.get(f"{API}/records/{draft_id()}", timeout=60)
        if response.status_code == 200 and response.json().get("status") == "published":
            break
        if attempt == attempts:
            response.raise_for_status()
            raise RuntimeError("published record not anonymously visible")
        time.sleep(min(2 * attempt, 10))
    if response is None:
        raise RuntimeError("anonymous readback did not run")
    record = response.json()
    if (
        record_id(record) != draft_id()
        or concept_id(record) != CONCEPT_ID
        or concept_doi(record) not in (None, CONCEPT_DOI)
        or record_doi(record) is None
    ):
        raise RuntimeError("public lineage identity mismatch")
    validate_metadata(record["metadata"])
    verify_latest(client, record)
    preview_state = public_file_state(client, draft_id()).get("default_preview")
    if repair_preview and preview_state != PRIMARY_PDF:
        record = repair_default_preview(record)
    preview = public_default_preview(client, draft_id())
    entries = public_entries(record)
    expected = expected_inventory()
    if set(entries) != set(expected) or len(entries) != 99:
        raise RuntimeError("anonymous public namespace mismatch")
    verified = verify_bytes(client, entries, expected)
    inherited_names = set(inherited_inventory())
    addition_names = set(addition_inventory())
    for item in verified:
        item["disposition"] = "inherited_unchanged" if item["filename"] in inherited_names else "becker_02_addition"
    serialized = json.dumps(record["metadata"], ensure_ascii=False)
    receipt = {
        "schema": "o015-zenodo-becker-02-public-readback-v1",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "pass",
        "record_id": draft_id(),
        "record_doi": record_doi(record),
        "record_url": record.get("links", {}).get("self_html") or record.get("links", {}).get("record_html"),
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "parent_record_id": PARENT_RECORD_ID,
        "parent_record_doi": PARENT_RECORD_DOI,
        "status": record.get("status"),
        "is_latest": True,
        "default_preview": preview,
        "default_preview_source": f"{API}/records/{draft_id()}/files",
        "legacy_thumbnail_cache_preview": observed_preview(record),
        "title": record["metadata"]["title"],
        "version": record["metadata"]["version"],
        "file_count": len(verified),
        "inherited_file_count": sum(item["disposition"] == "inherited_unchanged" for item in verified),
        "addition_file_count": sum(item["disposition"] == "becker_02_addition" for item in verified),
        "removed_parent_files": sorted(SUPERSEDED_DELTA_ZIPS),
        "removed_parent_file_count": len(SUPERSEDED_DELTA_ZIPS),
        "files": verified,
        "inherited_identity": "pass",
        "ttp_metadata_mentions": serialized.count("TTP"),
        "model_provenance_mentions": serialized.count(MODEL_ID),
        "credential_material_recorded": False,
        "upstream_contact": False,
    }
    if (
        receipt["status"] != "published"
        or receipt["file_count"] != 99
        or receipt["inherited_file_count"] != 91
        or receipt["addition_file_count"] != 8
        or receipt["ttp_metadata_mentions"] != 1
        or receipt["model_provenance_mentions"] != 1
        or set(expected) != inherited_names | addition_names
    ):
        raise RuntimeError("anonymous public release gate failed")
    write_json(READBACK_PATH, receipt)
    return receipt


def reconcile_publish(record: str) -> dict | None:
    client = session(authenticated=False)
    for attempt in range(1, 5):
        response = client.get(f"{API}/records/{record}", timeout=60)
        if response.status_code == 200 and response.json().get("status") == "published":
            return response.json()
        if response.status_code not in (404, 429) and response.status_code < 500:
            response.raise_for_status()
        if attempt < 4:
            time.sleep(attempt * 2)
    return None


def persist_if_already_published(record: str) -> dict | None:
    published = reconcile_publish(record)
    if published is None:
        return None
    if (
        record_id(published) != record
        or concept_id(published) != CONCEPT_ID
        or concept_doi(published) not in (None, CONCEPT_DOI)
        or record_doi(published) is None
    ):
        raise RuntimeError("reconciled public record belongs to another lineage")
    validate_metadata(published["metadata"])
    save_state(published)
    return published


def publish_open_edit_if_any(record: str) -> dict | None:
    """Close an equivalent same-record edit draft left by an ambiguous retry."""
    client = session()
    response = client.get(f"{API}/records/{record}/draft", timeout=60)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    if record_id(response.json()) != record:
        raise RuntimeError("open-edit lookup returned another record")
    validate_draft()
    publish_error: Exception | None = None
    try:
        response = client.post(f"{API}/records/{record}/draft/actions/publish", timeout=120)
        response.raise_for_status()
    except Exception as exc:
        publish_error = exc
    for attempt in range(1, 7):
        check = client.get(f"{API}/records/{record}/draft", timeout=60)
        if check.status_code == 404:
            break
        if check.status_code not in (429,) and check.status_code < 500:
            check.raise_for_status()
        if attempt < 6:
            time.sleep(attempt * 2)
    else:
        if publish_error is not None:
            raise publish_error
        raise RuntimeError("same-record edit remains open after publish")
    published = get_json_retry(session(authenticated=False), f"{API}/records/{record}", "republished-record")
    if (
        published.get("status") != "published"
        or record_id(published) != record
        or concept_id(published) != CONCEPT_ID
        or record_doi(published) is None
    ):
        raise RuntimeError("same-record edit publication identity gate failed")
    validate_metadata(published["metadata"])
    save_state(published)
    return published


def publish() -> dict:
    current = state()
    record = str(current["draft_id"])
    if current.get("status") == "published":
        return readback(wait=True, repair_preview=True)
    if persist_if_already_published(record) is not None:
        return readback(wait=True, repair_preview=True)
    try:
        validate_draft()
        response = session().post(f"{API}/records/{record}/draft/actions/publish", timeout=120)
        response.raise_for_status()
        published = response.json()
        validate_metadata(published["metadata"])
        save_state(published)
        return readback(wait=True, repair_preview=True)
    except Exception:
        published = persist_if_already_published(record)
        if published is None:
            raise
        return readback(wait=True, repair_preview=True)


def release() -> dict:
    if STATE_PATH.is_file():
        current = state()
        if current.get("status") == "published":
            publish_open_edit_if_any(str(current["draft_id"]))
            return readback(wait=True, repair_preview=True)
        if persist_if_already_published(str(current["draft_id"])) is not None:
            return readback(wait=True, repair_preview=True)
    prepare()
    upload()
    return publish()


def verify_draft_closure() -> dict:
    current = state()
    if current.get("status") != "published" or not current.get("draft_doi"):
        raise RuntimeError("published Becker-02 state is not available")
    record = str(current["draft_id"])
    client = session()
    direct = client.get(f"{API}/records/{record}/draft", timeout=60)
    if direct.status_code != 404:
        raise RuntimeError(f"published record still exposes an edit draft: HTTP {direct.status_code}")
    response = client.get(f"{API}/user/records", params={"size": 100, "sort": "mostrecent"}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    hits = payload.get("hits", {}).get("hits", []) if isinstance(payload, dict) else []
    lineage_drafts = [
        str(item.get("id"))
        for item in hits
        if isinstance(item, dict)
        and item.get("status") == "draft"
        and concept_id(item) == CONCEPT_ID
    ]
    if lineage_drafts:
        raise RuntimeError(f"concept lineage still exposes draft records: {lineage_drafts}")
    receipt = {
        "schema": "o015-zenodo-becker-02-draft-closure-v1",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "pass",
        "record_id": record,
        "record_doi": current["draft_doi"],
        "concept_id": CONCEPT_ID,
        "concept_doi": CONCEPT_DOI,
        "authenticated_draft_lookup_status": 404,
        "concept_open_draft_count": 0,
        "credential_material_recorded": False,
    }
    write_json(DRAFT_CLOSURE_PATH, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "prepare", "upload", "validate", "publish", "readback", "release", "closure"))
    args = parser.parse_args()
    result = {
        "build": build_local,
        "prepare": prepare,
        "upload": upload,
        "validate": validate_draft,
        "publish": publish,
        "readback": readback,
        "release": release,
        "closure": verify_draft_closure,
    }[args.action]()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
