#!/usr/bin/env python3
"""Explicit hashing schemes for raw evidence and Git-managed text artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


RAW_BYTES_SHA256 = "raw_bytes_sha256"
UTF8_LF_NORMALIZED_SHA256 = "utf8_lf_normalized_sha256"


def file_sha256(path: Path, scheme: str) -> str:
    path = Path(path)
    if scheme == RAW_BYTES_SHA256:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    if scheme == UTF8_LF_NORMALIZED_SHA256:
        text = path.read_text(encoding="utf-8")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    raise ValueError(f"unsupported artifact hash scheme: {scheme}")
