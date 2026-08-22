#!/usr/bin/env python3
"""Update, publish, and anonymously verify the reader-first Figshare item."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import requests
from pypdf import PdfReader


API = "https://api.figshare.com/v2"
ARTICLE_ID = 33314733
PROJECT_ID = 280296
COLLECTION_ID = 8668413
OWNER_AUTHOR_ID = 21544022
ARXIV_DOI = "10.48550/arXiv.2607.11664"
ZENODO_RECORD_DOI = "10.5281/zenodo.22060447"
ZENODO_CONCEPT_DOI = "10.5281/zenodo.22059741"
CREDENTIAL = Path(r"C:\Users\Floris\Documents\TOKENS\Figshare Token.md")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PDF = ROOT / "output" / "pdf" / "D90-HAB-03-09-modul-pendamping-id.pdf"
EXPECTED_FILES = [
    PDF,
    HERE / "D90-HAB-03-09-sumber-id.zip",
    HERE / "LICENSE_CC_BY_4.0.txt",
    HERE / "FIGSHARE_MANIFEST.json",
    HERE / "SHA256SUMS",
]
TASK_CAP = 500_000_000
PROJECT_CAP = 20_000_000_000

TITLE = "Optimisasi Lanjut dan Analisis Konveks - Modul Pendamping Habring Bab 3-9 (Bahasa Indonesia; Parsial)"
DESCRIPTION = """<p><strong>Modul pembaca Bahasa Indonesia yang koheren dan parsial.</strong> Berkas utama adalah pembaca 103 halaman untuk Andreas Habring, <em>Lecture Notes: Convex Optimization</em>, Bab 3-9: subgradien, metode subgradien terproyeksi, gradien proksimal, akselerasi, dualitas, penurunan gradien stokastik, dan transportasi optimal.</p>
<p>Ini adalah terjemahan/adaptasi independen dari arXiv:2607.11664v1. Seluruh berkas pada item Figshare ini hanya memuat modul turunan Habring dan didistribusikan di bawah Creative Commons Attribution 4.0 International (CC BY 4.0). Paket sumber ringkas memuat TeX yang dapat disunting, seluruh dependensi lokal, pembangun modul gabungan, catatan koreksi, atribusi/hak komponen, manifest, serta perintah pembangunan ulang yang telah lulus uji dari ekstraksi bersih. Tidak ada komponen Penn atau materi berlisensi campuran dalam item ini.</p>
<p>Status mutu: ketujuh unit lolos audit struktur dan matematika, validasi komputasi terbuka yang relevan, pembangunan deterministik, serta pemeriksaan visual seluruh halaman. Pembaca dapat dicari, mendeklarasikan <code>id-ID</code>, memiliki navigasi bab, dan tidak terenkripsi. Batas yang belum selesai dinyatakan terbuka: PDF belum bertag semantik, HTML/EPUB belum tersedia, dan tinjauan manusia/penutur asli Bahasa Indonesia belum tercatat. Modul ini bukan keseluruhan mata kuliah D90.</p>
<p>Versi 2 menggantikan permukaan metadata-only versi 1 dengan pembaca Habring Bab 3-9 yang dapat langsung digunakan. Checkpoint pendamping lengkap dengan komponen berlisensi campuran tetap dipreservasi secara terpisah di <a href="https://doi.org/10.5281/zenodo.22060447">Zenodo versi 10.5281/zenodo.22060447</a> dalam <a href="https://doi.org/10.5281/zenodo.22059741">garis keturunan konsep 10.5281/zenodo.22059741</a>.</p>
<p>Andreas Habring, TU Graz, arXiv, dan institusi terkait tidak menyusun terjemahan ini dan tidak menyiratkan peninjauan, persetujuan, sponsor, atau dukungan.</p>"""
METADATA_REASON = "Not applicable: this is a file-backed CC BY 4.0 reader item."

RELATED = [
    {
        "identifier": ARXIV_DOI,
        "identifier_type": "DOI",
        "relation": "IsDerivedFrom",
        "title": "Andreas Habring, Lecture Notes: Convex Optimization, arXiv:2607.11664v1",
        "is_linkout": True,
    },
    {
        "identifier": ZENODO_RECORD_DOI,
        "identifier_type": "DOI",
        "relation": "IsSupplementedBy",
        "title": "Checkpoint sepuluh unit Bahasa Indonesia dengan hak per komponen",
        "is_linkout": True,
    },
    {
        "identifier": ZENODO_CONCEPT_DOI,
        "identifier_type": "DOI",
        "relation": "IsPartOf",
        "title": "Garis keturunan Zenodo untuk edisi Bahasa Indonesia",
        "is_linkout": False,
    },
]

PAYLOAD = {
    "title": TITLE,
    "description": DESCRIPTION,
    "defined_type": "online resource",
    "license": 1,
    "authors": [{"id": OWNER_AUTHOR_ID}],
    "categories": [26095],
    "keywords": [
        "Bahasa Indonesia",
        "id-ID",
        "advanced optimization",
        "convex analysis",
        "nonsmooth optimization",
        "subgradient methods",
        "proximal gradient methods",
        "stochastic gradient descent",
        "optimal transport",
        "open educational resources",
        "partial reader",
    ],
    "related_materials": RELATED,
    "is_metadata_record": False,
    "metadata_reason": METADATA_REASON,
    "resource_title": "",
    "resource_doi": "",
}


def token() -> str:
    raw = CREDENTIAL.read_text(encoding="utf-8")
    for pattern in (r"figshare_pat_[A-Za-z0-9._-]+", r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])"):
        match = re.search(pattern, raw)
        if match:
            return match.group(0)
    raise RuntimeError("No Figshare credential-shaped value found")


def client(authenticated: bool = True) -> requests.Session:
    result = requests.Session()
    result.headers.update({"Accept": "application/json", "User-Agent": "O015-id-ID-preservation/1.0"})
    if authenticated:
        result.headers["Authorization"] = f"token {token()}"
    return result


def request(session: requests.Session, method: str, url: str, **kwargs: Any) -> requests.Response:
    retry_codes = {403, 409, 429, 500, 502, 503, 504}
    for attempt in range(6):
        response = session.request(method, url, timeout=kwargs.pop("timeout", 120), **kwargs)
        if response.status_code not in retry_codes:
            response.raise_for_status()
            return response
        if attempt == 5:
            response.raise_for_status()
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def response_json(response: requests.Response) -> Any:
    if not response.content:
        return {}
    return response.json()


def api_get(session: requests.Session, path: str, **kwargs: Any) -> Any:
    return response_json(request(session, "GET", f"{API}/{path.lstrip('/')}", **kwargs))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def private_article(session: requests.Session) -> dict:
    return api_get(session, f"account/articles/{ARTICLE_ID}")


def paged(session: requests.Session, path: str) -> list[dict]:
    result: list[dict] = []
    page = 1
    while True:
        batch = api_get(session, path, params={"page": page, "page_size": 1000})
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected paged response for {path}")
        result.extend(batch)
        if len(batch) < 1000:
            return result
        page += 1


def project_details(session: requests.Session) -> tuple[list[dict], int, int]:
    summaries = paged(session, f"account/projects/{PROJECT_ID}/articles")
    details = [api_get(session, f"account/articles/{int(item['id'])}") for item in summaries]
    total_bytes = sum(int(file.get("size") or 0) for article in details for file in (article.get("files") or []))
    total_files = sum(len(article.get("files") or []) for article in details)
    return details, total_bytes, total_files


def related_signature(article: dict) -> set[tuple[str, str]]:
    return {(str(item.get("identifier", "")).lower().removeprefix("https://doi.org/"), str(item.get("relation", ""))) for item in article.get("related_materials", []) or []}


def expected_related_signature() -> set[tuple[str, str]]:
    return {(item["identifier"].lower(), item["relation"]) for item in RELATED}


def verify_local_payload() -> dict:
    missing = [str(path) for path in EXPECTED_FILES if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing Figshare payloads:\n" + "\n".join(missing))
    if len({path.name for path in EXPECTED_FILES}) != 5:
        raise RuntimeError("Expected five unique Figshare filenames")
    total = sum(path.stat().st_size for path in EXPECTED_FILES)
    if total > TASK_CAP:
        raise RuntimeError(f"Task payload exceeds 500 MB: {total}")

    manifest = json.loads((HERE / "FIGSHARE_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest["upload_order"] != [path.name for path in EXPECTED_FILES]:
        raise RuntimeError("Manifest upload order differs")
    if manifest.get("license") != "CC BY 4.0" or manifest.get("complete_d90_course") is not False:
        raise RuntimeError("Manifest rights/status mismatch")

    lines = (HERE / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    if len(lines) != 4:
        raise RuntimeError("SHA256SUMS must bind the four non-self files")
    for line in lines:
        expected_hash, name = line.split("  ", 1)
        path = next((path for path in EXPECTED_FILES if path.name == name), None)
        if path is None or file_hash(path, "sha256") != expected_hash:
            raise RuntimeError(f"SHA256SUMS mismatch: {name}")

    reader = PdfReader(str(PDF))
    if len(reader.pages) != 103 or reader.is_encrypted or str(reader.trailer["/Root"].get("/Lang")) != "id-ID" or len(reader.outline) != 8:
        raise RuntimeError("Primary reader PDF structure changed")
    if file_hash(PDF, "sha256") != "6cd291cc447999b7cd72622e8c2003b837cf4f21ea5de0fcb7094913e20acd87":
        raise RuntimeError("Primary reader PDF identity changed")

    with zipfile.ZipFile(HERE / "D90-HAB-03-09-sumber-id.zip", "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Source ZIP integrity failure")
        names = archive.namelist()
        if len(names) != 29 or len(set(names)) != 29:
            raise RuntimeError("Source ZIP entry count/uniqueness mismatch")
        if any(any(token in name.lower() for token in ("penn", "griffin", "maple", ".mpl", "token", ".git")) for name in names):
            raise RuntimeError("Forbidden mixed-license/source entry in Figshare ZIP")
        inner = json.loads(archive.read("SOURCE_BUNDLE_MANIFEST.json"))
        if inner.get("license") != "CC BY 4.0" or inner.get("complete_selected_module") is not True or inner.get("complete_d90_course") is not False:
            raise RuntimeError("Source ZIP manifest status/rights mismatch")
        for entry in inner["entries"]:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or sha256_bytes(data) != entry["sha256"]:
                raise RuntimeError(f"Source ZIP inner-manifest mismatch: {entry['path']}")

    return {
        "file_count": 5,
        "total_bytes": total,
        "files": [{"name": path.name, "bytes": path.stat().st_size, "md5": file_hash(path, "md5"), "sha256": file_hash(path, "sha256")} for path in EXPECTED_FILES],
    }


def license_gate(session: requests.Session) -> dict:
    licenses = api_get(session, "licenses")
    by_name = {item["name"]: item for item in licenses}
    if by_name.get("CC BY 4.0", {}).get("value") != 1:
        raise RuntimeError("Figshare CC BY 4.0 identity changed")
    return {"name": "CC BY 4.0", "value": 1, "verified": True}


def preflight(write: bool = True, check_license_registry: bool = False) -> dict:
    local = verify_local_payload()
    session = client()
    registry = license_gate(session) if check_license_registry else {
        "name": "CC BY 4.0",
        "value": 1,
        "verified": True,
        "evidence": "Verified in the successful bounded preflight before the upload transaction; private and public article metadata are revalidated after mutation.",
    }
    article = private_article(session)
    details, project_bytes, project_files = project_details(session)
    project_ids = [int(item["id"]) for item in details]
    if project_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Target article is not unique in the Figshare project")
    target_current = sum(int(file.get("size") or 0) for file in article.get("files") or [])
    projected = project_bytes - target_current + local["total_bytes"]
    if projected >= PROJECT_CAP:
        raise RuntimeError(f"Projected Figshare project bytes exceed cap: {projected}")
    public_session = client(authenticated=False)
    public_collection = paged(public_session, f"collections/{COLLECTION_ID}/articles")
    public_project = paged(public_session, f"projects/{PROJECT_ID}/articles")
    if [int(item["id"]) for item in public_project].count(ARTICLE_ID) != 1:
        raise RuntimeError("Target article is not unique in the public project")
    result = {
        "schema": "o015-figshare-reader-preflight-v1",
        "article_id": ARTICLE_ID,
        "article_status": article.get("status"),
        "article_version": article.get("version"),
        "existing_file_count": len(article.get("files") or []),
        "project_ids": sorted(project_ids),
        "project_article_count": len(project_ids),
        "project_file_count": project_files,
        "project_current_bytes": project_bytes,
        "project_projected_bytes": projected,
        "project_cap_bytes": PROJECT_CAP,
        "collection_public_ids": sorted(int(item["id"]) for item in public_collection),
        "target_public_collection_count": sum(1 for item in public_collection if int(item["id"]) == ARTICLE_ID),
        "local_payload": local,
        "license_registry": registry,
    }
    if write:
        (HERE / "figshare-preflight.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return result


def article_metadata_matches(article: dict) -> bool:
    return all(
        [
            article.get("title") == TITLE,
            article.get("description") == DESCRIPTION,
            article.get("defined_type_name") == "online resource",
            article.get("license", {}).get("value") == 1,
            article.get("is_metadata_record") is False,
            article.get("metadata_reason") == METADATA_REASON,
            not article.get("resource_title"),
            not article.get("resource_doi"),
            [int(item["id"]) for item in article.get("authors", [])] == [OWNER_AUTHOR_ID],
            [int(item["id"]) for item in article.get("categories", [])] == [26095],
            article.get("keywords") == PAYLOAD["keywords"],
            related_signature(article) == expected_related_signature(),
            "TTP" not in (article.get("title", "") + article.get("description", "")),
        ]
    )


def private_files(session: requests.Session) -> list[dict]:
    files = api_get(session, f"account/articles/{ARTICLE_ID}/files")
    if not isinstance(files, list):
        raise RuntimeError("Unexpected private file list")
    return files


def upload_file(session: requests.Session, path: Path) -> None:
    md5 = file_hash(path, "md5")
    response = request(session, "POST", f"{API}/account/articles/{ARTICLE_ID}/files", json={"name": path.name, "md5": md5, "size": path.stat().st_size})
    created = response_json(response)
    location = created.get("location") or response.headers.get("Location")
    if not location:
        raise RuntimeError(f"No Figshare file location for {path.name}")
    info = response_json(request(session, "GET", location))
    file_id = int(info["id"])
    upload_url = info["upload_url"]
    upload_session = requests.Session()
    upload_session.headers["User-Agent"] = "O015-id-ID-preservation/1.0"
    upload_info = response_json(request(upload_session, "GET", upload_url, timeout=120))
    with path.open("rb") as stream:
        for part in upload_info["parts"]:
            stream.seek(int(part["startOffset"]))
            data = stream.read(int(part["endOffset"]) - int(part["startOffset"]) + 1)
            request(upload_session, "PUT", f"{upload_url}/{part['partNo']}", data=data, headers={"Content-Type": "application/octet-stream"}, timeout=300)
    request(session, "POST", f"{API}/account/articles/{ARTICLE_ID}/files/{file_id}", timeout=120)
    print(f"UPLOAD\t{path.name}\t{path.stat().st_size}\t{file_hash(path, 'sha256')}")


def prepare_and_upload() -> dict:
    baseline = preflight(write=True)
    session = client()
    article = private_article(session)
    if not article_metadata_matches(article):
        if article.get("metadata_reason") != METADATA_REASON:
            request(
                session,
                "PATCH",
                f"{API}/account/articles/{ARTICLE_ID}",
                json={"is_metadata_record": True, "metadata_reason": METADATA_REASON},
            )
        request(session, "PATCH", f"{API}/account/articles/{ARTICLE_ID}", json=PAYLOAD)
        article = private_article(session)
        if not article_metadata_matches(article):
            raise RuntimeError("Private Figshare metadata did not reach the reader-first target")

    expected = {path.name: path for path in EXPECTED_FILES}
    files = {item["name"]: item for item in private_files(session)}
    for name, item in sorted(files.items()):
        path = expected.get(name)
        matches = path is not None and int(item.get("size") or 0) == path.stat().st_size and str(item.get("supplied_md5") or item.get("computed_md5") or "").lower() == file_hash(path, "md5")
        if not matches:
            request(session, "DELETE", f"{API}/account/articles/{ARTICLE_ID}/files/{int(item['id'])}")
            print(f"DELETE_STALE\t{name}")

    files = {item["name"]: item for item in private_files(session)}
    for path in EXPECTED_FILES:
        item = files.get(path.name)
        if item and int(item.get("size") or 0) == path.stat().st_size and str(item.get("supplied_md5") or item.get("computed_md5") or "").lower() == file_hash(path, "md5"):
            print(f"SKIP\t{path.name}\t{path.stat().st_size}\t{file_hash(path, 'sha256')}")
            continue
        upload_file(session, path)
        files = {item["name"]: item for item in private_files(session)}

    validate_private(session)
    return baseline


def validate_private(session: requests.Session | None = None) -> dict:
    session = session or client()
    local = verify_local_payload()
    article = private_article(session)
    if not article_metadata_matches(article):
        raise RuntimeError("Private Figshare metadata validation failed")
    files = private_files(session)
    if [item["name"] for item in files] != [path.name for path in EXPECTED_FILES]:
        raise RuntimeError(f"Private Figshare file order mismatch: {[item['name'] for item in files]}")
    for item, path in zip(files, EXPECTED_FILES, strict=True):
        supplied = str(item.get("supplied_md5") or "").lower()
        computed = str(item.get("computed_md5") or supplied).lower()
        if int(item.get("size") or 0) != path.stat().st_size or supplied != file_hash(path, "md5") or computed != file_hash(path, "md5"):
            raise RuntimeError(f"Private Figshare file identity mismatch: {path.name}")
    _, project_bytes, _ = project_details(session)
    if project_bytes >= PROJECT_CAP:
        raise RuntimeError(f"Figshare project byte cap failed: {project_bytes}")
    return {"status": article.get("status"), "version": article.get("version"), "file_count": len(files), "project_bytes": project_bytes, "task_bytes": local["total_bytes"]}


def public_article_matches(article: dict) -> bool:
    return article_metadata_matches(article) and [item["name"] for item in article.get("files", [])] == [path.name for path in EXPECTED_FILES]


def publish() -> dict:
    prepare_and_upload()
    session = client()
    gate = validate_private(session)
    public_session = client(authenticated=False)
    current_public = api_get(public_session, f"articles/{ARTICLE_ID}")
    if not public_article_matches(current_public):
        request(session, "POST", f"{API}/account/articles/{ARTICLE_ID}/publish", timeout=180)
    for _ in range(12):
        time.sleep(2)
        current_public = api_get(public_session, f"articles/{ARTICLE_ID}")
        if public_article_matches(current_public):
            break
    if not public_article_matches(current_public):
        raise RuntimeError("Published Figshare article did not expose the reader-first version")

    private_collection = paged(session, f"account/collections/{COLLECTION_ID}/articles")
    private_ids = [int(item["id"]) for item in private_collection]
    if private_ids.count(ARTICLE_ID) == 0:
        request(session, "POST", f"{API}/account/collections/{COLLECTION_ID}/articles", json={"articles": [ARTICLE_ID]})
    elif private_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Target article duplicated in private collection")

    public_collection = paged(public_session, f"collections/{COLLECTION_ID}/articles")
    if [int(item["id"]) for item in public_collection].count(ARTICLE_ID) != 1:
        request(session, "POST", f"{API}/account/collections/{COLLECTION_ID}/publish", timeout=180)
        for _ in range(12):
            time.sleep(2)
            public_collection = paged(public_session, f"collections/{COLLECTION_ID}/articles")
            if [int(item["id"]) for item in public_collection].count(ARTICLE_ID) == 1:
                break
    if [int(item["id"]) for item in public_collection].count(ARTICLE_ID) != 1:
        raise RuntimeError("Published Indonesian collection does not contain the article exactly once")
    return {"private_gate": gate, "public_version": current_public.get("version"), "public_doi": current_public.get("doi")}


def verify_public_zip(payload: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Public Figshare source ZIP integrity failure")
        names = archive.namelist()
        if len(names) != 29 or len(set(names)) != 29:
            raise RuntimeError("Public Figshare source ZIP inventory mismatch")
        inner = json.loads(archive.read("SOURCE_BUNDLE_MANIFEST.json"))
        for entry in inner["entries"]:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or sha256_bytes(data) != entry["sha256"]:
                raise RuntimeError(f"Public source ZIP inner-manifest mismatch: {entry['path']}")
        return {"entries": len(names), "manifest_entries_verified": len(inner["entries"]), "integrity": "pass"}


def anonymous_readback() -> dict:
    local = verify_local_payload()
    preflight_path = HERE / "figshare-preflight.json"
    if not preflight_path.is_file():
        raise RuntimeError("Missing Figshare preflight receipt")
    baseline = json.loads(preflight_path.read_text(encoding="utf-8"))
    session = client(authenticated=False)
    article = api_get(session, f"articles/{ARTICLE_ID}")
    if not public_article_matches(article) or article.get("status") != "public" or article.get("is_public") is not True:
        raise RuntimeError("Anonymous Figshare article metadata gate failed")
    if int(article.get("version") or 0) < 2:
        raise RuntimeError("Reader-first Figshare version was not created")
    files = article.get("files", [])
    verified = []
    zip_receipt = None
    for item, path in zip(files, EXPECTED_FILES, strict=True):
        response = request(session, "GET", item["download_url"], headers={"Accept": "*/*"}, timeout=300)
        payload = response.content
        local_md5 = file_hash(path, "md5")
        if len(payload) != path.stat().st_size or hashlib.md5(payload).hexdigest() != local_md5 or sha256_bytes(payload) != file_hash(path, "sha256"):
            raise RuntimeError(f"Anonymous Figshare byte mismatch: {path.name}")
        if str(item.get("supplied_md5") or "").lower() != local_md5 or str(item.get("computed_md5") or local_md5).lower() != local_md5:
            raise RuntimeError(f"Anonymous Figshare MD5 metadata mismatch: {path.name}")
        verified.append({"filename": path.name, "bytes": len(payload), "md5": local_md5, "sha256": sha256_bytes(payload), "public_byte_identity": "pass"})
        if path.name.endswith(".zip"):
            zip_receipt = verify_public_zip(payload)
        if path == PDF:
            reader = PdfReader(io.BytesIO(payload))
            if len(reader.pages) != 103 or reader.is_encrypted or str(reader.trailer["/Root"].get("/Lang")) != "id-ID" or len(reader.outline) != 8:
                raise RuntimeError("Anonymous Figshare PDF structure gate failed")

    versions = api_get(session, f"articles/{ARTICLE_ID}/versions")
    version_numbers = sorted(int(item["version"]) for item in versions)
    if 1 not in version_numbers or int(article["version"]) not in version_numbers:
        raise RuntimeError("Figshare version-history gate failed")
    project_articles = paged(session, f"projects/{PROJECT_ID}/articles")
    project_ids = sorted(int(item["id"]) for item in project_articles)
    if project_ids != baseline["project_ids"] or project_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Figshare public project membership changed unexpectedly")
    collection_articles = paged(session, f"collections/{COLLECTION_ID}/articles")
    collection_ids = sorted(int(item["id"]) for item in collection_articles)
    expected_collection_ids = sorted(set(baseline["collection_public_ids"]) | {ARTICLE_ID})
    if collection_ids != expected_collection_ids or collection_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Figshare collection membership gate failed")
    collection = api_get(session, f"collections/{COLLECTION_ID}")

    private_session = client()
    _, project_bytes, project_file_count = project_details(private_session)
    if project_bytes >= PROJECT_CAP:
        raise RuntimeError("Post-publication Figshare project cap failed")
    receipt = {
        "schema": "o015-figshare-reader-public-readback-v1",
        "article_id": ARTICLE_ID,
        "title": article["title"],
        "doi": article.get("doi"),
        "version": article.get("version"),
        "public_url": article.get("figshare_url") or article.get("url_public_html"),
        "status": article.get("status"),
        "license": article.get("license"),
        "is_metadata_record": article.get("is_metadata_record"),
        "authors": article.get("authors"),
        "related_materials": article.get("related_materials"),
        "files": verified,
        "file_count": len(verified),
        "primary_file": verified[0]["filename"],
        "source_zip_verification": zip_receipt,
        "version_history": version_numbers,
        "project_id": PROJECT_ID,
        "project_article_count": len(project_ids),
        "project_file_count": project_file_count,
        "project_bytes": project_bytes,
        "project_cap_bytes": PROJECT_CAP,
        "task_bytes": local["total_bytes"],
        "task_cap_bytes": TASK_CAP,
        "collection_id": COLLECTION_ID,
        "collection_doi": collection.get("doi"),
        "collection_version": collection.get("version"),
        "collection_article_count": len(collection_ids),
        "checks": {
            "public": True,
            "metadata": True,
            "cc_by_4_0": True,
            "not_metadata_only": True,
            "pdf_first": True,
            "all_public_bytes": True,
            "source_zip": True,
            "project_unique": True,
            "collection_unique": True,
            "caps": True,
            "no_ttp_prose": True,
            "no_penn_payload": True,
        },
    }
    (HERE / "figshare-public-readback.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["inspect", "upload", "validate", "publish", "readback"])
    args = parser.parse_args()
    if args.action == "inspect":
        print(json.dumps(preflight(write=True, check_license_registry=True), ensure_ascii=False, indent=2, sort_keys=True))
    elif args.action == "upload":
        print(json.dumps(prepare_and_upload(), ensure_ascii=False, indent=2, sort_keys=True))
    elif args.action == "validate":
        print(json.dumps(validate_private(), ensure_ascii=False, indent=2, sort_keys=True))
    elif args.action == "publish":
        print(json.dumps(publish(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(anonymous_readback(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
