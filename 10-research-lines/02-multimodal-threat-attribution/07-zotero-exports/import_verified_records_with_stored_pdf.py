#!/usr/bin/env python3
"""Import verified records and legal local PDFs into the selected Zotero collection."""

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
from pathlib import Path
from typing import Any


BASE = "http://127.0.0.1:23119"


def request(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> tuple[int, bytes]:
    request_headers = {"User-Agent": "project05-zotero-research/0.2"}
    request_headers.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=request_headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.read()


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def selected_collection() -> dict[str, Any]:
    _, payload = request(
        f"{BASE}/connector/getSelectedCollection",
        method="POST",
        body=b"{}",
        headers={
            "Content-Type": "application/json",
            "X-Zotero-Connector-API-Version": "3",
        },
    )
    return json.loads(payload.decode("utf-8"))


def exact_existing(title: str) -> dict[str, Any] | None:
    params = urllib.parse.urlencode(
        {"q": title, "qmode": "titleCreatorYear", "itemType": "-attachment", "limit": 100}
    )
    _, payload = request(
        f"{BASE}/api/users/0/items?{params}",
        headers={"Zotero-API-Version": "3"},
    )
    target = normalize_title(title)
    for item in json.loads(payload.decode("utf-8")):
        data = item.get("data", item)
        if normalize_title(str(data.get("title", ""))) == target:
            return item
    return None


def creator(name: str) -> dict[str, str]:
    if not re.search(r"\s", name) or re.search(r"[\u3400-\u9fff]", name):
        return {"creatorType": "author", "name": name}
    first, last = name.rsplit(" ", 1)
    return {"creatorType": "author", "firstName": first, "lastName": last}


def connector_item(record: dict[str, Any], connector_id: str) -> dict[str, Any]:
    allowed = {
        "itemType",
        "title",
        "date",
        "publicationTitle",
        "proceedingsTitle",
        "bookTitle",
        "volume",
        "issue",
        "pages",
        "DOI",
        "url",
        "language",
        "repository",
        "archive",
        "archiveLocation",
        "publisher",
        "place",
    }
    item = {key: value for key, value in record.items() if key in allowed and value}
    item["id"] = connector_id
    item["creators"] = [creator(name) for name in record.get("authors", [])]
    item["extra"] = (
        f"P05-L2 corpus: {record['corpus_id']}\n"
        f"Reading status: {record['reading_status']}"
    )
    tags = record.get("tags", [])
    item["tags"] = [{"tag": tag} for tag in dict.fromkeys(tags)]
    item["attachments"] = []
    return item


def save(record: dict[str, Any], manifest_dir: Path) -> None:
    session_id = f"p05-l2-second-{uuid.uuid4().hex}"
    connector_id = f"item-{uuid.uuid4().hex}"
    item = connector_item(record, connector_id)
    payload = json.dumps(
        {"sessionID": session_id, "items": [item], "uri": record.get("url", "")}
    ).encode("utf-8")
    status, _ = request(
        f"{BASE}/connector/saveItems",
        method="POST",
        body=payload,
        headers={
            "Content-Type": "application/json",
            "X-Zotero-Connector-API-Version": "3",
        },
    )
    if status not in {200, 201}:
        raise RuntimeError(f"saveItems returned HTTP {status}")

    pdf_path = record.get("pdf_path")
    if not pdf_path:
        return
    path = (manifest_dir / pdf_path).resolve()
    pdf = path.read_bytes()
    if not pdf.startswith(b"%PDF-"):
        raise RuntimeError(f"Not a PDF: {path}")
    metadata = json.dumps(
        {
            "sessionID": session_id,
            "parentItemID": connector_id,
            "title": "Full Text PDF",
            "url": record.get("pdf_url") or record.get("url", ""),
        },
        ensure_ascii=True,
    )
    status, _ = request(
        f"{BASE}/connector/saveAttachment",
        method="POST",
        body=pdf,
        headers={
            "Content-Type": "application/pdf",
            "Content-Length": str(len(pdf)),
            "X-Metadata": metadata,
            "X-Zotero-Connector-API-Version": "3",
        },
        timeout=240,
    )
    if status not in {200, 201}:
        raise RuntimeError(f"saveAttachment returned HTTP {status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--expected-collection", required=True)
    parser.add_argument("--delay", type=float, default=0.35)
    args = parser.parse_args()

    target = selected_collection()
    if target.get("name") != args.expected_collection:
        raise RuntimeError(
            f"Selected collection is {target.get('name')!r}, expected {args.expected_collection!r}"
        )

    records = json.loads(args.manifest.read_text(encoding="utf-8"))
    report: list[dict[str, Any]] = []
    for record in records:
        try:
            existing = exact_existing(record["title"])
            if existing:
                report.append(
                    {
                        "corpus_id": record["corpus_id"],
                        "title": record["title"],
                        "status": "existing-skipped",
                        "zotero_key": existing.get("key"),
                    }
                )
                continue
            if not args.yes:
                report.append(
                    {
                        "corpus_id": record["corpus_id"],
                        "title": record["title"],
                        "status": "would-import",
                        "with_pdf": bool(record.get("pdf_path")),
                    }
                )
                continue
            save(record, args.manifest.parent)
            time.sleep(args.delay)
            saved = exact_existing(record["title"])
            report.append(
                {
                    "corpus_id": record["corpus_id"],
                    "title": record["title"],
                    "status": "imported-with-stored-pdf"
                    if record.get("pdf_path")
                    else "imported-metadata-only",
                    "zotero_key": saved.get("key") if saved else None,
                }
            )
        except Exception as exc:
            report.append(
                {
                    "corpus_id": record["corpus_id"],
                    "title": record.get("title"),
                    "status": "error",
                    "error": str(exc),
                }
            )
    print(json.dumps({"selected_collection": target, "records": report}, ensure_ascii=False, indent=2))
    return 1 if any(row["status"] == "error" for row in report) else 0


if __name__ == "__main__":
    sys.exit(main())
