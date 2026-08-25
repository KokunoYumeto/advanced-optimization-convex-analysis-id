#!/usr/bin/env python3
"""Publish and anonymously verify Figshare v3 for the Habring-only reader."""

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
ZENODO_CONCEPT_DOI = "10.5281/zenodo.22059741"
PRIOR_DOI = "10.6084/m9.figshare.33314733.v2"
CREDENTIAL = Path.home() / "Documents" / "TOKENS" / "Figshare Token.md"
HERE = Path(__file__).resolve().parent
TASK_CAP = 500_000_000
PROJECT_CAP = 20_000_000_000

PDF_NAME = "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.pdf"
HTML_NAME = "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.html"
EPUB_NAME = "D90-HAB-01-09-catatan-kuliah-optimisasi-konveks-id.epub"
ZIP_NAME = "D90-HAB-01-09-sumber-id.zip"
LICENSE_NAME = "LICENSE_CC_BY_4.0.txt"
MANIFEST_NAME = "FIGSHARE_MANIFEST.json"
SUMS_NAME = "SHA256SUMS"
EXPECTED_FILES = [
    HERE / PDF_NAME,
    HERE / HTML_NAME,
    HERE / EPUB_NAME,
    HERE / ZIP_NAME,
    HERE / LICENSE_NAME,
    HERE / MANIFEST_NAME,
    HERE / SUMS_NAME,
]

TITLE = "Optimisasi Konveks — Catatan Kuliah, Edisi Bahasa Indonesia (Habring v1; Lengkap)"
DESCRIPTION = """<p><strong>Edisi Bahasa Indonesia lengkap untuk prakata dan sembilan bab sumber Habring v1.</strong> Berkas utama adalah pembaca PDF 139 halaman untuk Andreas Habring, <em>Lecture Notes: Convex Optimization</em>, arXiv:2607.11664v1.</p>
<p>Permukaan pembaca meliputi PDF yang dapat dicari dan memiliki navigasi bab, HTML mandiri yang reflowable, serta EPUB 3. Paket sumber ringkas memuat TeX yang dapat disunting, seluruh aset Habring yang diperlukan, perangkat pembangunan ulang, manifest hak komponen, dan identitas sumber berwenang. Urutan, rumus, bukti, latihan, rujukan silang, serta aset sumber dipertahankan; perubahan penerjemahan, deskripsi akses, perbaikan TeX, dan koreksi matematis yang dapat ditentukan diidentifikasi sebagai perubahan edisi.</p>
<p>Seluruh berkas pada item ini hanya memuat edisi turunan Habring dan tersedia berdasarkan Creative Commons Attribution 4.0 International (CC BY 4.0). Kelas khusus dan tujuh gambar raster diwarisi dari submission CC BY 4.0 tetapi tidak memuat pemberitahuan terpisah atau sumber pembangkit; caveat komponen tersebut dipertahankan di paket sumber. Tidak ada byte dari komponen MIT, Penn, Royer, atau Becker pada item ini.</p>
<p>Status mutu: pembangunan PDF, HTML, dan EPUB bersifat deterministik pada toolchain yang dicatat; audit struktur, formula, navigasi, visual, reflow, tautan internal, aset, dan komputasi yang relevan telah lulus. PDF mendeklarasikan <code>id-ID</code> tetapi belum bertag semantik; HTML dan EPUB menyediakan permukaan reflowable.</p>
<p>Status cakupan: spine Habring v1 telah lengkap. Buku kuliah O015 yang lebih besar tetap parsial karena suplemen terstruktur dan lapisan asli yang tidak tumpang tindih dikelola serta dipreservasi secara terpisah.</p>
<p>Provenans produksi: OpenAI Codex gpt-5.6-sol, Ultra, atas instruksi pengguna. Seluruh kredit penulis dan sumber dipertahankan.</p>
<p>Ini adalah terjemahan/adaptasi mandiri. Andreas Habring, TU Graz, arXiv, dan institusi terkait tidak menyusun, memeriksa, menyetujui, mensponsori, atau mendukung edisi ini.</p>"""
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
        "convex optimization",
        "convex analysis",
        "nonsmooth optimization",
        "subgradient methods",
        "proximal gradient methods",
        "stochastic gradient descent",
        "optimal transport",
        "open educational resources",
        "complete Habring spine",
        "partial O015 coursebook",
    ],
    "related_materials": RELATED,
    "is_metadata_record": False,
    "metadata_reason": METADATA_REASON,
    "resource_title": "",
    "resource_doi": "",
}


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def credential_token() -> str:
    raw = CREDENTIAL.read_text(encoding="utf-8")
    patterns = (
        r"figshare_pat_[A-Za-z0-9._-]+",
        r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])",
    )
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            return match.group(0)
    raise RuntimeError("No Figshare credential-shaped value found")


def client(*, authenticated: bool) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {"Accept": "application/json", "User-Agent": "O015-id-ID-Habring/3.0"}
    )
    if authenticated:
        session.headers["Authorization"] = f"token {credential_token()}"
    return session


def request(
    session: requests.Session, method: str, url: str, **kwargs: Any
) -> requests.Response:
    retry_codes = {409, 429, 500, 502, 503, 504}
    timeout = kwargs.pop("timeout", 120)
    for attempt in range(6):
        response = session.request(method, url, timeout=timeout, **kwargs)
        if response.status_code == 403:
            try:
                error_code = response.json().get("code")
            except (TypeError, ValueError):
                error_code = None
            if error_code == "InactiveAccount":
                raise RuntimeError(
                    "Figshare authenticated API reports InactiveAccount; "
                    "publication is unavailable until the account is re-enabled"
                )
            response.raise_for_status()
        if response.status_code not in retry_codes:
            response.raise_for_status()
            return response
        if attempt == 5:
            response.raise_for_status()
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def response_json(response: requests.Response) -> Any:
    return response.json() if response.content else {}


def api_get(session: requests.Session, path: str, **kwargs: Any) -> Any:
    return response_json(
        request(session, "GET", f"{API}/{path.lstrip('/')}", **kwargs)
    )


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


def private_article(session: requests.Session) -> dict:
    return api_get(session, f"account/articles/{ARTICLE_ID}")


def private_files(session: requests.Session) -> list[dict]:
    files = api_get(session, f"account/articles/{ARTICLE_ID}/files")
    if not isinstance(files, list):
        raise RuntimeError("Unexpected private file list")
    return files


def project_details(session: requests.Session) -> tuple[list[dict], int, int]:
    summaries = paged(session, f"account/projects/{PROJECT_ID}/articles")
    details = [
        api_get(session, f"account/articles/{int(item['id'])}") for item in summaries
    ]
    total_bytes = sum(
        int(file.get("size") or 0)
        for article in details
        for file in (article.get("files") or [])
    )
    total_files = sum(len(article.get("files") or []) for article in details)
    return details, total_bytes, total_files


def related_signature(article: dict) -> set[tuple[str, str]]:
    return {
        (
            str(item.get("identifier", ""))
            .lower()
            .removeprefix("https://doi.org/"),
            str(item.get("relation", "")),
        )
        for item in (article.get("related_materials") or [])
    }


def expected_related_signature() -> set[tuple[str, str]]:
    return {(item["identifier"].lower(), item["relation"]) for item in RELATED}


def verify_source_zip(payload: bytes | None = None) -> dict[str, int | str]:
    source: str | io.BytesIO
    source = io.BytesIO(payload) if payload is not None else str(HERE / ZIP_NAME)
    with zipfile.ZipFile(source, "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Habring source ZIP integrity failure")
        names = archive.namelist()
        if len(names) != len(set(names)) or "SOURCE_BUNDLE_MANIFEST.json" not in names:
            raise RuntimeError("Habring source ZIP inventory failure")
        if any(
            any(
                token in name.lower()
                for token in (
                    "mit-",
                    "penn",
                    "royer",
                    "becker",
                    "griffin",
                    "maple",
                    ".mpl",
                    "token",
                    ".git",
                )
            )
            for name in names
        ):
            raise RuntimeError("Forbidden non-Habring entry in source ZIP")
        text_suffixes = {
            ".bib",
            ".csv",
            ".json",
            ".md",
            ".ps1",
            ".py",
            ".tex",
            ".txt",
        }
        mixed_rights = [
            name
            for name in names
            if Path(name).suffix.lower() in text_suffixes
            and b"CC BY-SA" in archive.read(name)
        ]
        if mixed_rights:
            raise RuntimeError(
                f"Mixed CC BY-SA claim entered CC BY 4.0 package: {mixed_rights}"
            )
        manifest = json.loads(archive.read("SOURCE_BUNDLE_MANIFEST.json"))
        if (
            manifest.get("license") != "CC BY 4.0"
            or manifest.get("complete_habring_v1_spine") is not True
            or manifest.get("complete_o015_coursebook") is not False
            or manifest.get("model_provenance")
            != "OpenAI Codex gpt-5.6-sol, Ultra"
        ):
            raise RuntimeError("Source ZIP status/rights/provenance mismatch")
        for entry in manifest["entries"]:
            data = archive.read(entry["path"])
            if len(data) != entry["bytes"] or sha256_bytes(data) != entry["sha256"]:
                raise RuntimeError(f"Source ZIP inner-manifest mismatch: {entry['path']}")
        return {
            "entries": len(names),
            "manifest_entries_verified": len(manifest["entries"]),
            "integrity": "pass",
        }


def verify_local_payload() -> dict:
    missing = [str(path) for path in EXPECTED_FILES if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing Figshare payloads:\n" + "\n".join(missing))
    if len({path.name for path in EXPECTED_FILES}) != 7:
        raise RuntimeError("Expected seven unique Figshare filenames")
    total = sum(path.stat().st_size for path in EXPECTED_FILES)
    if total > TASK_CAP:
        raise RuntimeError(f"Task payload exceeds 500 MB: {total}")

    manifest = json.loads((HERE / MANIFEST_NAME).read_text(encoding="utf-8"))
    if manifest.get("upload_order") != [path.name for path in EXPECTED_FILES]:
        raise RuntimeError("Manifest upload order differs")
    if (
        manifest.get("license") != "CC BY 4.0"
        or manifest.get("complete_habring_v1_spine") is not True
        or manifest.get("complete_o015_coursebook") is not False
        or manifest.get("model_provenance")
        != "OpenAI Codex gpt-5.6-sol, Ultra"
    ):
        raise RuntimeError("Manifest rights/status/provenance mismatch")

    sums = (HERE / SUMS_NAME).read_text(encoding="ascii").splitlines()
    if len(sums) != 6:
        raise RuntimeError("SHA256SUMS must bind the six non-self files")
    for line in sums:
        expected_hash, name = line.split("  ", 1)
        path = next((item for item in EXPECTED_FILES if item.name == name), None)
        if path is None or file_hash(path, "sha256") != expected_hash:
            raise RuntimeError(f"SHA256SUMS mismatch: {name}")

    pdf = PdfReader(str(HERE / PDF_NAME))
    if (
        len(pdf.pages) != 139
        or pdf.is_encrypted
        or str(pdf.trailer["/Root"].get("/Lang")) != "id-ID"
        or len(pdf.outline) != 9
        or file_hash(HERE / PDF_NAME, "sha256")
        != "da2b421b97efce4e3d7b8cf6be9938d17b7768b9c6bcb4846b09b9c692b34c41"
    ):
        raise RuntimeError("Primary PDF identity/structure failure")

    html_text = (HERE / HTML_NAME).read_text(encoding="utf-8")
    html_search = " ".join(html_text.split())
    if (
        "OpenAI Codex gpt-5.6-sol, Ultra" not in html_search
        or "CC BY 4.0" not in html_search
        or file_hash(HERE / HTML_NAME, "sha256")
        != "717ee81912a8b903acc87e5c59d830aa1d8c78abdda6e0c869d66b9a7bcde3a4"
    ):
        raise RuntimeError("HTML identity/provenance failure")

    if file_hash(HERE / EPUB_NAME, "sha256") != "c630e25db3cbbfa6f6afa7213e526c47586b6e7b44f709095ea5a3881756fd41":
        raise RuntimeError("EPUB identity failure")
    with zipfile.ZipFile(HERE / EPUB_NAME, "r") as archive:
        if archive.testzip() is not None or len(archive.namelist()) != 24:
            raise RuntimeError("EPUB closure failure")

    zip_receipt = verify_source_zip()
    if file_hash(HERE / LICENSE_NAME, "sha256") != "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411":
        raise RuntimeError("CC BY 4.0 legal-code identity failure")
    return {
        "file_count": 7,
        "total_bytes": total,
        "files": [
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "md5": file_hash(path, "md5"),
                "sha256": file_hash(path, "sha256"),
            }
            for path in EXPECTED_FILES
        ],
        "source_zip": zip_receipt,
    }


def article_metadata_matches(article: dict) -> bool:
    prose = str(article.get("title", "")) + "\n" + str(
        article.get("description", "")
    )
    forbidden = re.search(
        r"(?i)(?:\bTTP\b|Translation and Transcription Project)", prose
    )
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
            [int(item["id"]) for item in article.get("authors", [])]
            == [OWNER_AUTHOR_ID],
            [int(item["id"]) for item in article.get("categories", [])] == [26095],
            article.get("keywords") == PAYLOAD["keywords"],
            related_signature(article) == expected_related_signature(),
            forbidden is None,
        ]
    )


def files_match(files: list[dict]) -> bool:
    if [item.get("name") for item in files] != [path.name for path in EXPECTED_FILES]:
        return False
    for item, path in zip(files, EXPECTED_FILES, strict=True):
        supplied = str(item.get("supplied_md5") or "").lower()
        computed = str(item.get("computed_md5") or supplied).lower()
        if (
            int(item.get("size") or 0) != path.stat().st_size
            or supplied != file_hash(path, "md5")
            or computed != file_hash(path, "md5")
        ):
            return False
    return True


def preflight(*, write: bool = True) -> dict:
    local = verify_local_payload()
    session = client(authenticated=True)
    licenses = api_get(session, "licenses")
    by_name = {item["name"]: item for item in licenses}
    if by_name.get("CC BY 4.0", {}).get("value") != 1:
        raise RuntimeError("Figshare CC BY 4.0 identity changed")

    article = private_article(session)
    details, project_bytes, project_file_count = project_details(session)
    project_ids = [int(item["id"]) for item in details]
    if project_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Target article is not unique in the private project")
    target_bytes = sum(int(item.get("size") or 0) for item in article.get("files", []))
    projected = project_bytes - target_bytes + local["total_bytes"]
    if projected >= PROJECT_CAP:
        raise RuntimeError(f"Projected Figshare project cap failed: {projected}")

    public = client(authenticated=False)
    public_article = api_get(public, f"articles/{ARTICLE_ID}")
    if int(public_article.get("version") or 0) < 2:
        raise RuntimeError("Expected public Figshare v2 baseline is absent")
    if str(public_article.get("doi") or "").lower() != PRIOR_DOI.lower():
        raise RuntimeError("Public Figshare baseline DOI does not match the frozen lineage")
    public_project_ids = [
        int(item["id"]) for item in paged(public, f"projects/{PROJECT_ID}/articles")
    ]
    if public_project_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Target article is not unique in the public project")
    collection_ids = [
        int(item["id"])
        for item in paged(public, f"collections/{COLLECTION_ID}/articles")
    ]
    if collection_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Target article is not unique in the public collection")

    result = {
        "schema": "o015-figshare-habring-v3-preflight-v1",
        "article_id": ARTICLE_ID,
        "public_version": public_article.get("version"),
        "public_doi": public_article.get("doi"),
        "private_status": article.get("status"),
        "private_file_count": len(article.get("files") or []),
        "project_article_count": len(project_ids),
        "project_file_count": project_file_count,
        "project_current_bytes": project_bytes,
        "project_projected_bytes": projected,
        "project_cap_bytes": PROJECT_CAP,
        "collection_article_count": len(collection_ids),
        "local_payload": local,
        "license_registry": {"name": "CC BY 4.0", "value": 1, "verified": True},
    }
    if write:
        (HERE / "figshare-v3-preflight.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


def upload_file(session: requests.Session, path: Path) -> None:
    response = request(
        session,
        "POST",
        f"{API}/account/articles/{ARTICLE_ID}/files",
        json={
            "name": path.name,
            "md5": file_hash(path, "md5"),
            "size": path.stat().st_size,
        },
    )
    created = response_json(response)
    location = created.get("location") or response.headers.get("Location")
    if not location:
        raise RuntimeError(f"No Figshare file location for {path.name}")
    info = response_json(request(session, "GET", location))
    file_id = int(info["id"])
    upload_url = info["upload_url"]
    upload_session = requests.Session()
    upload_session.headers["User-Agent"] = "O015-id-ID-Habring/3.0"
    upload_info = response_json(request(upload_session, "GET", upload_url))
    with path.open("rb") as stream:
        for part in upload_info["parts"]:
            stream.seek(int(part["startOffset"]))
            data = stream.read(
                int(part["endOffset"]) - int(part["startOffset"]) + 1
            )
            request(
                upload_session,
                "PUT",
                f"{upload_url}/{part['partNo']}",
                data=data,
                headers={"Content-Type": "application/octet-stream"},
                timeout=300,
            )
    request(
        session,
        "POST",
        f"{API}/account/articles/{ARTICLE_ID}/files/{file_id}",
    )
    print(f"UPLOAD\t{path.name}\t{path.stat().st_size}\t{file_hash(path, 'sha256')}")


def prepare_and_upload() -> dict:
    baseline = preflight(write=True)
    session = client(authenticated=True)
    article = private_article(session)
    if not article_metadata_matches(article):
        if article.get("metadata_reason") != METADATA_REASON:
            request(
                session,
                "PATCH",
                f"{API}/account/articles/{ARTICLE_ID}",
                json={"is_metadata_record": True, "metadata_reason": METADATA_REASON},
            )
        request(
            session,
            "PATCH",
            f"{API}/account/articles/{ARTICLE_ID}",
            json=PAYLOAD,
        )
        if not article_metadata_matches(private_article(session)):
            raise RuntimeError("Private Figshare metadata did not reach target")

    current_files = private_files(session)
    if not files_match(current_files):
        for item in current_files:
            request(
                session,
                "DELETE",
                f"{API}/account/articles/{ARTICLE_ID}/files/{int(item['id'])}",
            )
            print(f"DELETE_STALE\t{item['name']}")
        for path in EXPECTED_FILES:
            upload_file(session, path)
    else:
        for path in EXPECTED_FILES:
            print(f"SKIP\t{path.name}\t{path.stat().st_size}\t{file_hash(path, 'sha256')}")
    validate_private(session)
    return baseline


def validate_private(session: requests.Session | None = None) -> dict:
    session = session or client(authenticated=True)
    local = verify_local_payload()
    article = private_article(session)
    if not article_metadata_matches(article):
        raise RuntimeError("Private Figshare metadata validation failed")
    files = private_files(session)
    if not files_match(files):
        raise RuntimeError("Private Figshare file identity/order validation failed")
    _, project_bytes, project_file_count = project_details(session)
    if project_bytes >= PROJECT_CAP:
        raise RuntimeError(f"Figshare project cap failed: {project_bytes}")
    return {
        "status": article.get("status"),
        "version": article.get("version"),
        "file_count": len(files),
        "project_file_count": project_file_count,
        "project_bytes": project_bytes,
        "task_bytes": local["total_bytes"],
    }


def public_files_match(article: dict) -> bool:
    files = article.get("files") or []
    if [item.get("name") for item in files] != [path.name for path in EXPECTED_FILES]:
        return False
    return all(
        int(item.get("size") or 0) == path.stat().st_size
        and str(item.get("supplied_md5") or "").lower() == file_hash(path, "md5")
        for item, path in zip(files, EXPECTED_FILES, strict=True)
    )


def public_article_matches(article: dict) -> bool:
    return article_metadata_matches(article) and public_files_match(article)


def publish() -> dict:
    prepare_and_upload()
    session = client(authenticated=True)
    gate = validate_private(session)
    public = client(authenticated=False)
    article = api_get(public, f"articles/{ARTICLE_ID}")
    if not public_article_matches(article):
        request(
            session,
            "POST",
            f"{API}/account/articles/{ARTICLE_ID}/publish",
            timeout=180,
        )
    for _ in range(20):
        time.sleep(2)
        article = api_get(public, f"articles/{ARTICLE_ID}")
        if public_article_matches(article):
            break
    if not public_article_matches(article) or int(article.get("version") or 0) < 3:
        raise RuntimeError("Published Figshare v3 did not expose exact payload")

    private_collection = paged(
        session, f"account/collections/{COLLECTION_ID}/articles"
    )
    private_ids = [int(item["id"]) for item in private_collection]
    if private_ids.count(ARTICLE_ID) == 0:
        request(
            session,
            "POST",
            f"{API}/account/collections/{COLLECTION_ID}/articles",
            json={"articles": [ARTICLE_ID]},
        )
    elif private_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Target article duplicated in private collection")

    public_ids = [
        int(item["id"])
        for item in paged(public, f"collections/{COLLECTION_ID}/articles")
    ]
    if public_ids.count(ARTICLE_ID) != 1:
        request(
            session,
            "POST",
            f"{API}/account/collections/{COLLECTION_ID}/publish",
            timeout=180,
        )
        for _ in range(20):
            time.sleep(2)
            public_ids = [
                int(item["id"])
                for item in paged(public, f"collections/{COLLECTION_ID}/articles")
            ]
            if public_ids.count(ARTICLE_ID) == 1:
                break
    if public_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Published collection membership failed")
    return {
        "private_gate": gate,
        "public_version": article.get("version"),
        "public_doi": article.get("doi"),
    }


def anonymous_readback() -> dict:
    local = verify_local_payload()
    public = client(authenticated=False)
    article = api_get(public, f"articles/{ARTICLE_ID}")
    if (
        not public_article_matches(article)
        or article.get("status") != "public"
        or article.get("is_public") is not True
        or int(article.get("version") or 0) < 3
    ):
        raise RuntimeError("Anonymous Figshare metadata/version gate failed")

    verified = []
    source_zip_receipt = None
    for item, path in zip(article["files"], EXPECTED_FILES, strict=True):
        response = request(
            public,
            "GET",
            item["download_url"],
            headers={"Accept": "*/*"},
            timeout=300,
        )
        data = response.content
        local_md5 = file_hash(path, "md5")
        if (
            len(data) != path.stat().st_size
            or hashlib.md5(data).hexdigest() != local_md5
            or sha256_bytes(data) != file_hash(path, "sha256")
        ):
            raise RuntimeError(f"Anonymous Figshare byte mismatch: {path.name}")
        verified.append(
            {
                "filename": path.name,
                "bytes": len(data),
                "md5": local_md5,
                "sha256": sha256_bytes(data),
                "public_byte_identity": "pass",
            }
        )
        if path.name == ZIP_NAME:
            source_zip_receipt = verify_source_zip(data)
        elif path.name == PDF_NAME:
            pdf = PdfReader(io.BytesIO(data))
            if (
                len(pdf.pages) != 139
                or pdf.is_encrypted
                or str(pdf.trailer["/Root"].get("/Lang")) != "id-ID"
                or len(pdf.outline) != 9
            ):
                raise RuntimeError("Anonymous PDF structure gate failed")
        elif path.name == EPUB_NAME:
            with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
                if archive.testzip() is not None or len(archive.namelist()) != 24:
                    raise RuntimeError("Anonymous EPUB closure gate failed")

    versions = api_get(public, f"articles/{ARTICLE_ID}/versions")
    version_numbers = sorted(int(item["version"]) for item in versions)
    if 2 not in version_numbers or int(article["version"]) not in version_numbers:
        raise RuntimeError("Figshare version-history gate failed")
    project_ids = [
        int(item["id"]) for item in paged(public, f"projects/{PROJECT_ID}/articles")
    ]
    collection_ids = [
        int(item["id"])
        for item in paged(public, f"collections/{COLLECTION_ID}/articles")
    ]
    if project_ids.count(ARTICLE_ID) != 1 or collection_ids.count(ARTICLE_ID) != 1:
        raise RuntimeError("Public project/collection uniqueness gate failed")
    collection = api_get(public, f"collections/{COLLECTION_ID}")

    private = client(authenticated=True)
    _, project_bytes, project_file_count = project_details(private)
    if project_bytes >= PROJECT_CAP:
        raise RuntimeError("Post-publication Figshare project cap failed")
    receipt = {
        "schema": "o015-figshare-habring-v3-public-readback-v1",
        "article_id": ARTICLE_ID,
        "title": article["title"],
        "doi": article.get("doi"),
        "version": article.get("version"),
        "public_url": article.get("figshare_url")
        or article.get("url_public_html"),
        "status": article.get("status"),
        "license": article.get("license"),
        "is_metadata_record": article.get("is_metadata_record"),
        "related_materials": article.get("related_materials"),
        "files": verified,
        "file_count": len(verified),
        "primary_file": verified[0]["filename"],
        "source_zip_verification": source_zip_receipt,
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
            "complete_habring_spine": True,
            "larger_coursebook_partial": True,
            "no_ttp_title_or_lead": True,
            "no_non_habring_payload": True,
            "model_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
        },
    }
    (HERE / "figshare-v3-public-readback.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=["local", "inspect", "upload", "validate", "publish", "readback"]
    )
    args = parser.parse_args()
    if args.action == "local":
        result = verify_local_payload()
    elif args.action == "inspect":
        result = preflight(write=True)
    elif args.action == "upload":
        result = prepare_and_upload()
    elif args.action == "validate":
        result = validate_private()
    elif args.action == "publish":
        result = publish()
    else:
        result = anonymous_readback()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
