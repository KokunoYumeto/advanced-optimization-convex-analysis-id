#!/usr/bin/env python3
"""Create/update and verify the O015 CC0 Figshare metadata/link record.

The underlying Zenodo release has mixed per-component licensing. Figshare's
article schema exposes one scalar license and its public license registry does
not contain CC BY-NC-SA 3.0 US, so this route deliberately publishes no work
files. Only the Figshare metadata is CC0; the linked Zenodo bytes retain their
component-specific rights.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import requests


API = "https://api.figshare.com/v2"
PROJECT_ID = 280296
COLLECTION_ID = 8668413
OWNER_AUTHOR_ID = 21544022
ZENODO_RECORD_DOI = "10.5281/zenodo.22059742"
ZENODO_CONCEPT_DOI = "10.5281/zenodo.22059741"
ZENODO_RECORD_URL = "https://zenodo.org/records/22059742"
CREDENTIAL = Path(r"C:\Users\Floris\Documents\TOKENS\Figshare Token.md")

TITLE = (
    "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia: "
    "Checkpoint Sembilan Unit (Belum Lengkap)"
)

DESCRIPTION = """<p><strong>Rekaman metadata/link CC0 untuk checkpoint Bahasa Indonesia yang belum lengkap.</strong> Berkas karya tidak diduplikasi di Figshare karena rilis sebenarnya memakai hak per komponen yang tidak dapat diwakili secara benar oleh satu kolom lisensi artikel Figshare: komponen turunan Andreas Habring adalah CC BY 4.0, sedangkan komponen turunan Christopher Griffin/Penn adalah CC BY-NC-SA 3.0 United States. Lisensi CC0 pada rekaman ini hanya berlaku untuk metadata Figshare ini.</p>
<p>Checkpoint yang ditautkan berisi sembilan unit yang telah diterima: Habring Bab 3–9 dan Penn Bab 3–4. Sembilan PDF pembaca, bundel sumber/backend, catatan hak, manifest rilis, dan checksum tersedia di <a href="https://doi.org/10.5281/zenodo.22059742">Zenodo versi 10.5281/zenodo.22059742</a>; versi mendatang dipertahankan dalam <a href="https://doi.org/10.5281/zenodo.22059741">garis keturunan konsep 10.5281/zenodo.22059741</a>.</p>
<p>Label mutu pada batas ini: audit struktur dan matematika lulus; validasi komputasi terbuka yang relevan lulus; pembangunan PDF deterministik dan pemeriksaan visual lulus; semua PDF dapat dicari dan mendeklarasikan <code>id-ID</code>. Korpus masih belum lengkap: PDF belum bertag, tinjauan manusia/penutur asli Bahasa Indonesia belum tercatat, HTML/EPUB semantik, lapisan latihan/solusi sistematis, permukaan interaktif, dan unit Penn berikutnya masih terbuka. Ini adalah terjemahan/adaptasi independen dan tidak menyiratkan dukungan penulis sumber atau institusinya.</p>"""

METADATA_REASON = (
    "The release uses mixed CC BY 4.0 and CC BY-NC-SA 3.0 US component "
    "rights. Figshare offers one article license but not the Penn license, "
    "so this is a CC0 metadata/link record only; authoritative files, "
    "rights, manifest, and hashes are at Zenodo."
)

PAYLOAD = {
    "title": TITLE,
    "description": DESCRIPTION,
    "defined_type": "online resource",
    "license": 2,
    "authors": [{"id": OWNER_AUTHOR_ID}],
    "categories": [26095],
    "keywords": [
        "Bahasa Indonesia",
        "id-ID",
        "advanced optimization",
        "convex analysis",
        "open educational resources",
        "partial edition",
        "metadata record",
    ],
    "related_materials": [
        {
            "identifier": ZENODO_RECORD_DOI,
            "identifier_type": "DOI",
            "relation": "IsMetadataFor",
            "title": (
                "Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa "
                "Indonesia (id-ID): Checkpoint Sembilan Unit (Belum Lengkap)"
            ),
            "is_linkout": True,
        },
        {
            "identifier": ZENODO_CONCEPT_DOI,
            "identifier_type": "DOI",
            "relation": "IsMetadataFor",
            "title": "Zenodo concept lineage for the Indonesian edition",
            "is_linkout": False,
        },
    ],
}


def token() -> str:
    raw = CREDENTIAL.read_text(encoding="utf-8")
    patterns = [
        r"figshare_pat_[A-Za-z0-9._-]+",
        r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            return match.group(0)
    raise RuntimeError("No Figshare credential-shaped value found")


def session(authenticated: bool = True) -> requests.Session:
    client = requests.Session()
    client.headers["Accept"] = "application/json"
    if authenticated:
        client.headers["Authorization"] = f"token {token()}"
    return client


def response_json(response: requests.Response) -> dict | list:
    response.raise_for_status()
    if not response.content:
        return {}
    return response.json()


def article_id_from_response(response: requests.Response) -> int:
    payload = response_json(response)
    candidates: list[str] = []
    if isinstance(payload, dict):
        for key in ("id", "location", "url", "entity_id"):
            if payload.get(key) is not None:
                candidates.append(str(payload[key]))
    location = response.headers.get("Location")
    if location:
        candidates.append(location)
    for candidate in candidates:
        match = re.search(r"(?:articles/)?(\d+)/?$", candidate)
        if match:
            return int(match.group(1))
    raise RuntimeError(f"Cannot determine created article id from {payload!r}")


def private_project_articles(client: requests.Session) -> list[dict]:
    data = response_json(
        client.get(
            f"{API}/account/projects/{PROJECT_ID}/articles",
            params={"page_size": 1000},
            timeout=60,
        )
    )
    if not isinstance(data, list):
        raise RuntimeError("Unexpected private project article response")
    return data


def private_article(client: requests.Session, article_id: int) -> dict:
    data = response_json(
        client.get(f"{API}/account/articles/{article_id}", timeout=60)
    )
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected private article response")
    return data


def related_dois(article: dict) -> set[str]:
    result: set[str] = set()
    for item in article.get("related_materials", []) or []:
        identifier = str(item.get("identifier", "")).lower()
        if identifier:
            result.add(identifier.removeprefix("https://doi.org/"))
    return result


def find_existing(client: requests.Session) -> tuple[int | None, list[dict]]:
    articles = private_project_articles(client)
    matches: list[dict] = []
    for summary in articles:
        article_id = int(summary["id"])
        details = private_article(client, article_id)
        if (
            details.get("title") == TITLE
            or ZENODO_RECORD_DOI.lower() in related_dois(details)
            or ZENODO_CONCEPT_DOI.lower() in related_dois(details)
        ):
            matches.append(details)
    if len(matches) > 1:
        raise RuntimeError(
            "Multiple project entries match this exact work; refusing to create/update"
        )
    return (int(matches[0]["id"]) if matches else None), articles


def assert_metadata_route() -> list[dict]:
    licenses = response_json(requests.get(f"{API}/licenses", timeout=60))
    if not isinstance(licenses, list):
        raise RuntimeError("Unexpected Figshare license registry response")
    by_name = {item["name"]: item for item in licenses}
    if by_name.get("CC0", {}).get("value") != 2:
        raise RuntimeError("Figshare CC0 license identity changed")
    if "CC BY-NC-SA 3.0 United States" in by_name:
        raise RuntimeError(
            "Exact-license registry changed; re-evaluate whether a file mirror is lawful"
        )
    return licenses


def create_or_update() -> int:
    assert_metadata_route()
    client = session()
    article_id, _ = find_existing(client)
    created = article_id is None
    if article_id is None:
        response = client.post(
            f"{API}/account/projects/{PROJECT_ID}/articles",
            json=PAYLOAD,
            timeout=60,
        )
        article_id = article_id_from_response(response)

    details = private_article(client, article_id)
    needs_update = not all(
        [
            details.get("title") == TITLE,
            details.get("description") == DESCRIPTION,
            details.get("defined_type_name") == "online resource",
            details.get("license", {}).get("value") == 2,
            details.get("is_metadata_record") is True,
            details.get("metadata_reason") == METADATA_REASON,
            related_dois(details)
            == {ZENODO_RECORD_DOI.lower(), ZENODO_CONCEPT_DOI.lower()},
        ]
    )
    if needs_update:
        update = dict(PAYLOAD)
        update["is_metadata_record"] = True
        update["metadata_reason"] = METADATA_REASON
        response_json(
            client.patch(
                f"{API}/account/articles/{article_id}",
                json=update,
                timeout=60,
            )
        )

    details = private_article(client, article_id)
    if details.get("files"):
        raise RuntimeError("Metadata-only Figshare article unexpectedly has files")
    if details.get("license", {}).get("name") != "CC0":
        raise RuntimeError("Figshare metadata record is not CC0")
    if not details.get("is_metadata_record"):
        raise RuntimeError("Figshare article is not marked as metadata-only")

    if created or needs_update or details.get("status") != "public":
        response_json(
            client.post(
                f"{API}/account/articles/{article_id}/publish",
                timeout=120,
            )
        )

    collection_articles = response_json(
        client.get(
            f"{API}/account/collections/{COLLECTION_ID}/articles",
            params={"page_size": 1000},
            timeout=60,
        )
    )
    collection_ids = {int(item["id"]) for item in collection_articles}
    collection_changed = article_id not in collection_ids
    if collection_changed:
        response_json(
            client.post(
                f"{API}/account/collections/{COLLECTION_ID}/articles",
                json={"articles": [article_id]},
                timeout=60,
            )
        )
        response_json(
            client.post(
                f"{API}/account/collections/{COLLECTION_ID}/publish",
                timeout=120,
            )
        )
    return article_id


def anonymous_verify(article_id: int) -> dict:
    client = session(authenticated=False)
    article = response_json(client.get(f"{API}/articles/{article_id}", timeout=60))
    project_articles = response_json(
        client.get(
            f"{API}/projects/{PROJECT_ID}/articles",
            params={"page_size": 1000},
            timeout=60,
        )
    )
    collection_articles = response_json(
        client.get(
            f"{API}/collections/{COLLECTION_ID}/articles",
            params={"page_size": 1000},
            timeout=60,
        )
    )
    collection = response_json(
        client.get(f"{API}/collections/{COLLECTION_ID}", timeout=60)
    )

    project_ids = {int(item["id"]) for item in project_articles}
    collection_ids = {int(item["id"]) for item in collection_articles}
    public_title_matches = [
        item for item in project_articles if item.get("title") == TITLE
    ]
    exact_related_dois = related_dois(article)
    no_ttp_text = " ".join(
        str(article.get(key, ""))
        for key in ("title", "description", "metadata_reason")
    )
    checks = {
        "public": article.get("status") == "public" and article.get("is_public") is True,
        "title": article.get("title") == TITLE,
        "description": article.get("description") == DESCRIPTION,
        "online_resource": article.get("defined_type_name") == "online resource",
        "metadata_only": article.get("is_metadata_record") is True,
        "no_files": len(article.get("files", [])) == 0,
        "cc0_metadata": (
            article.get("license", {}).get("name") == "CC0"
            and article.get("license", {}).get("value") == 2
        ),
        "metadata_reason_exact": article.get("metadata_reason") == METADATA_REASON,
        "related_dois_exact": exact_related_dois
        == {ZENODO_RECORD_DOI.lower(), ZENODO_CONCEPT_DOI.lower()},
        "no_ttp_prose": "TTP" not in no_ttp_text,
        "project_member": article_id in project_ids,
        "project_title_unique": (
            len(public_title_matches) == 1
            and int(public_title_matches[0]["id"]) == article_id
        ),
        "collection_member": article_id in collection_ids,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Anonymous Figshare verification failed: {checks}")
    return {
        "schema": "o015-figshare-metadata-readback-v1",
        "article_id": article_id,
        "title": article["title"],
        "doi": article.get("doi"),
        "public_url": article.get("figshare_url") or article.get("url_public_html"),
        "status": article.get("status"),
        "version": article.get("version"),
        "defined_type": article.get("defined_type_name"),
        "license": article.get("license"),
        "is_metadata_record": article.get("is_metadata_record"),
        "metadata_reason": article.get("metadata_reason"),
        "files": article.get("files", []),
        "related_materials": article.get("related_materials", []),
        "project_id": PROJECT_ID,
        "collection_id": COLLECTION_ID,
        "collection_doi": collection.get("doi"),
        "collection_version": collection.get("version"),
        "checks": checks,
    }


def main() -> None:
    raise RuntimeError(
        "Retired after article 33314733 became a reader-first CC BY 4.0 work item. "
        "Use release/figshare/2026-08-22-reader/publish_reader.py; this historical "
        "metadata-only route must never revert the live article."
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["inspect", "publish", "readback"])
    parser.add_argument("--article-id", type=int)
    args = parser.parse_args()

    if args.action == "inspect":
        assert_metadata_route()
        client = session()
        article_id, articles = find_existing(client)
        print(
            json.dumps(
                {
                    "matching_article_id": article_id,
                    "project_article_count": len(articles),
                    "route": "CC0 metadata/link only; no work files",
                },
                indent=2,
            )
        )
        return

    if args.action == "publish":
        article_id = create_or_update()
    else:
        if args.article_id is None:
            client = session()
            article_id, _ = find_existing(client)
            if article_id is None:
                raise RuntimeError("No matching Figshare article exists")
        else:
            article_id = args.article_id

    receipt = anonymous_verify(article_id)
    receipt_path = Path(__file__).resolve().parent / "figshare-public-readback.json"
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
