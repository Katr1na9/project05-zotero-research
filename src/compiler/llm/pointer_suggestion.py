"""Catalog-bounded, suggestion-only pointer handling."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


_IDENTITY_FIELDS = ("record_id", "source_id", "content_hash")


class PointerSuggestionError(ValueError):
    """Raised when a proposed pointer is incomplete or outside the catalog."""


def suggest_pointer(
    candidates: Iterable[Mapping[str, Any]],
    visible_pointer_catalog: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return only local producer states, never a trusted binding transition."""

    catalog = tuple(visible_pointer_catalog)
    catalog_identities = {
        _validated_identity(entry, "visible pointer catalog") for entry in catalog
    }
    proposed = tuple(candidates)
    if not proposed:
        return {"status": "unbound"}

    verified = []
    for candidate in proposed:
        identity = _validated_identity(candidate, "pointer candidate")
        if identity not in catalog_identities:
            raise PointerSuggestionError(
                "pointer candidate is not present in the visible pointer catalog"
            )
        verified.append(identity)

    record_ids = _unique_in_order(identity[0] for identity in verified)
    if len(record_ids) < 2:
        return {"status": "unbound"}
    return {"status": "ambiguous", "candidates": record_ids}


def _validated_identity(value: Mapping[str, Any], label: str) -> tuple[str, str, str]:
    if not isinstance(value, Mapping):
        raise PointerSuggestionError(f"{label} must be a mapping")
    if set(value) != set(_IDENTITY_FIELDS):
        raise PointerSuggestionError(f"{label} has incomplete pointer identity")
    identity = tuple(value[field] for field in _IDENTITY_FIELDS)
    if any(not isinstance(part, str) or not part for part in identity):
        raise PointerSuggestionError(f"{label} has incomplete pointer identity")
    return identity  # type: ignore[return-value]


def _unique_in_order(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))
