#!/usr/bin/env python3
"""Download the compact PIDSMaker E3 PostgreSQL dumps with resume support."""

from __future__ import annotations

import argparse
import os
import shutil
import urllib.request
from pathlib import Path


DATASETS = {
    "cadets_e3": "1DGcGBhpavNmXTnCDd_s4NWBNh2n4-6nd",
    "fivedirections_e3": "17YHqUMbuNwP05iaOaifxvcQc2oC9pJbZ",
}
TOKEN_ENV = "PIDSMaker_GOOGLE_ACCESS_TOKEN"
API_URL = "https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
# Guard against a hung connection blocking the download indefinitely.
DOWNLOAD_TIMEOUT_SECONDS = 300


def resolve_access_token() -> str:
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not token:
        raise RuntimeError(
            f"Set {TOKEN_ENV} to a Google Drive read-only OAuth access token."
        )
    return token


def build_request(
    dataset: str,
    target: Path,
    access_token: str,
) -> urllib.request.Request:
    file_id = DATASETS[dataset]
    headers = {"Authorization": f"Bearer {access_token}"}
    if target.exists() and target.stat().st_size:
        headers["Range"] = f"bytes={target.stat().st_size}-"
    return urllib.request.Request(
        API_URL.format(file_id=file_id),
        headers=headers,
    )


def download_dataset(
    dataset: str,
    output_dir: Path,
    access_token: str,
) -> Path:
    if dataset not in DATASETS:
        raise ValueError(f"Unsupported dataset: {dataset}")

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{dataset}.dump"
    request = build_request(dataset, target, access_token)
    resume_offset = target.stat().st_size if target.exists() else 0

    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
        is_partial = getattr(response, "status", None) == 206
        mode = "ab" if resume_offset and is_partial else "wb"
        with target.open(mode) as handle:
            shutil.copyfileobj(response, handle, length=1024 * 1024)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "datasets",
        nargs="*",
        choices=sorted(DATASETS),
        default=sorted(DATASETS),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "real_data"
        / "darpa_tc_e3"
        / "raw"
        / "pidsmaker",
    )
    args = parser.parse_args()

    token = resolve_access_token()
    for dataset in args.datasets:
        target = download_dataset(dataset, args.output_dir, token)
        print(f"Downloaded {dataset} to {target}")


if __name__ == "__main__":
    main()
