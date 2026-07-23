"""Canonical JSON-document hashing for frozen Kernel v0.8 artifacts.

The contract removes exactly the top-level ``hash`` member, serializes the
remaining JSON-compatible value with sorted keys and compact separators, and
hashes the UTF-8 bytes.  It deliberately rejects values that JSON cannot
represent canonically; callers remain responsible for duplicate-key rejection
while parsing YAML/JSON source bytes.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import re


SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def canonical_json(value: object) -> str:
    """Return the approved compact, sort-key JSON representation."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("value is not canonical JSON data") from exc


def canonical_document_hash(document: Mapping[str, object]) -> str:
    """Hash a mapping after removing exactly its top-level ``hash`` key."""

    if not isinstance(document, Mapping):
        raise ValueError("canonical document must be an object")
    payload = dict(document)
    payload.pop("hash", None)
    encoded = canonical_json(payload).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def canonical_value_hash(value: object) -> str:
    """Hash any JSON-compatible value without excluding a field."""

    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def has_valid_document_hash(document: Mapping[str, object]) -> bool:
    """Return whether ``document.hash`` exactly replays from its content."""

    declared = document.get("hash")
    return (
        isinstance(declared, str)
        and SHA256_PATTERN.fullmatch(declared) is not None
        and declared == canonical_document_hash(document)
    )
