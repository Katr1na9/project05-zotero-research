#!/usr/bin/env python3
"""Import deduplicated arXiv records with stored PDFs into selected Zotero collection."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ZOTERO_BASE = "http://127.0.0.1:23119"
ARXIV_API = "https://export.arxiv.org/api/query?id_list={}"
ARXIV_PDF = "https://arxiv.org/pdf/{}"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def http(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 90,
) -> tuple[int, bytes]:
    request_headers = {"User-Agent": "project05-zotero-research/0.1"}
    request_headers.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=request_headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.read()


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return " ".join(element.text.split())


def fetch_arxiv(arxiv_id: str) -> dict[str, Any]:
    _, payload = http(ARXIV_API.format(urllib.parse.quote(arxiv_id)))
    root = ET.fromstring(payload)
    entry = root.find(f"{ATOM}entry")
    if entry is None:
        raise RuntimeError(f"No arXiv metadata for {arxiv_id}")

    authors = [text(author.find(f"{ATOM}name")) for author in entry.findall(f"{ATOM}author")]
    published = text(entry.find(f"{ATOM}published"))
    primary = entry.find(f"{ARXIV}primary_category")
    category = primary.attrib.get("term", "") if primary is not None else ""
    return {
        "arxiv_id": arxiv_id,
        "title": text(entry.find(f"{ATOM}title")),
        "abstract": text(entry.find(f"{ATOM}summary")),
        "authors": [name for name in authors if name],
        "published": published,
        "category": category,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": ARXIV_PDF.format(arxiv_id),
    }


def zotero_search(title: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "q": title,
            "qmode": "titleCreatorYear",
            "itemType": "-attachment",
            "limit": 100,
        }
    )
    _, payload = http(
        f"{ZOTERO_BASE}/api/users/0/items?{params}",
        headers={"Zotero-API-Version": "3"},
    )
    return json.loads(payload.decode("utf-8"))


def exact_existing(title: str) -> dict[str, Any] | None:
    target = normalize_title(title)
    for item in zotero_search(title):
        data = item.get("data", item)
        if normalize_title(str(data.get("title", ""))) == target:
            return item
    return None


def split_name(name: str) -> dict[str, str]:
    parts = name.rsplit(" ", 1)
    if len(parts) == 1:
        return {"creatorType": "author", "name": name}
    return {
        "creatorType": "author",
        "firstName": parts[0],
        "lastName": parts[1],
    }


def save_item_with_pdf(meta: dict[str, Any], corpus_id: str, pdf: bytes) -> None:
    session_id = f"p05-l2-{uuid.uuid4().hex}"
    connector_id = f"item-{uuid.uuid4().hex}"
    date = meta["published"][:10]
    item = {
        "id": connector_id,
        "itemType": "preprint",
        "title": meta["title"],
        "abstractNote": meta["abstract"],
        "creators": [split_name(name) for name in meta["authors"]],
        "date": date,
        "repository": "arXiv",
        "archive": "arXiv",
        "archiveLocation": meta["arxiv_id"],
        "url": meta["url"],
        "language": "en",
        "extra": f"arXiv: {meta['arxiv_id']}\nP05-L2 corpus: {corpus_id}",
        "tags": [
            {"tag": "p05-l2-collision"},
            {"tag": "must-read"},
            {"tag": "llm"},
            {"tag": "attack-investigation"},
            {"tag": "evidence-grounding"},
        ],
        "attachments": [],
    }
    save_payload = json.dumps(
        {"sessionID": session_id, "items": [item], "uri": meta["url"]}
    ).encode("utf-8")
    status, _ = http(
        f"{ZOTERO_BASE}/connector/saveItems",
        method="POST",
        body=save_payload,
        headers={
            "Content-Type": "application/json",
            "X-Zotero-Connector-API-Version": "3",
        },
    )
    if status != 201:
        raise RuntimeError(f"saveItems returned HTTP {status}")

    attachment_meta = json.dumps(
        {
            "sessionID": session_id,
            "parentItemID": connector_id,
            "title": "Full Text PDF",
            "url": meta["pdf_url"],
        },
        ensure_ascii=True,
    )
    status, _ = http(
        f"{ZOTERO_BASE}/connector/saveAttachment",
        method="POST",
        body=pdf,
        headers={
            "Content-Type": "application/pdf",
            "Content-Length": str(len(pdf)),
            "X-Metadata": attachment_meta,
            "X-Zotero-Connector-API-Version": "3",
        },
        timeout=180,
    )
    if status != 201:
        raise RuntimeError(f"saveAttachment returned HTTP {status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--yes", action="store_true", help="Write to selected Zotero collection")
    parser.add_argument("--delay", type=float, default=0.4)
    args = parser.parse_args()

    records = json.loads(args.manifest.read_text(encoding="utf-8"))
    report: list[dict[str, Any]] = []
    for record in records:
        corpus_id = record["corpus_id"]
        arxiv_id = record["arxiv_id"]
        try:
            meta = fetch_arxiv(arxiv_id)
            existing = exact_existing(meta["title"])
            if existing:
                data = existing.get("data", existing)
                report.append(
                    {
                        "corpus_id": corpus_id,
                        "arxiv_id": arxiv_id,
                        "title": meta["title"],
                        "status": "existing-skipped",
                        "zotero_key": existing.get("key") or data.get("key"),
                    }
                )
                continue

            if not args.yes:
                report.append(
                    {
                        "corpus_id": corpus_id,
                        "arxiv_id": arxiv_id,
                        "title": meta["title"],
                        "status": "would-import",
                    }
                )
                continue

            _, pdf = http(meta["pdf_url"], timeout=180)
            if not pdf.startswith(b"%PDF-"):
                raise RuntimeError("Downloaded content is not a PDF")
            save_item_with_pdf(meta, corpus_id, pdf)
            time.sleep(args.delay)
            saved = exact_existing(meta["title"])
            report.append(
                {
                    "corpus_id": corpus_id,
                    "arxiv_id": arxiv_id,
                    "title": meta["title"],
                    "status": "imported-with-stored-pdf",
                    "zotero_key": saved.get("key") if saved else None,
                }
            )
        except Exception as exc:
            report.append(
                {
                    "corpus_id": corpus_id,
                    "arxiv_id": arxiv_id,
                    "status": "error",
                    "error": str(exc),
                }
            )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if any(row["status"] == "error" for row in report) else 0


if __name__ == "__main__":
    sys.exit(main())
