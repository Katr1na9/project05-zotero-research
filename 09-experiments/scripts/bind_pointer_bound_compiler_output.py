#!/usr/bin/env python3
"""Validate pointer-free model output and bind a trusted evidence pointer.

The model is never allowed to emit or modify a pointer.  This module is the
only transition from constrained model output to the legacy strict compiler
shape.  It performs no repair, coercion, fuzzy matching, or label lookup.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


DECISIONS = ("supported", "unsupported_by_bound_pointer")
MODEL_OUTPUT_KEYS = {"support_decision", "edge_fields"}
EDGE_FIELD_KEYS = {
    "subject_type",
    "subject_value",
    "predicate",
    "object_type",
    "object_value",
}
POINTER_KEYS = {"artifact_id", "record_id", "record_sha256"}
FORBIDDEN_MODEL_KEYS = {"pointer", "source_pointer", "normalized_edge"}


class PointerBindingError(ValueError):
    """Raised when constrained output or its trusted pointer is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest().upper()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_pointer(pointer: Any) -> dict[str, str]:
    if not isinstance(pointer, dict) or set(pointer) != POINTER_KEYS:
        raise PointerBindingError("invalid_bound_pointer_schema")
    if not all(isinstance(pointer[key], str) and pointer[key] for key in POINTER_KEYS):
        raise PointerBindingError("invalid_bound_pointer_value")
    return copy.deepcopy(pointer)


def validate_model_output(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != MODEL_OUTPUT_KEYS:
        raise PointerBindingError("invalid_pointer_free_top_level_schema")
    if FORBIDDEN_MODEL_KEYS & set(value):
        raise PointerBindingError("model_output_contains_forbidden_pointer_field")
    decision = value.get("support_decision")
    edge_fields = value.get("edge_fields")
    if decision not in DECISIONS:
        raise PointerBindingError("invalid_support_decision")
    if decision == "unsupported_by_bound_pointer":
        if edge_fields is not None:
            raise PointerBindingError("unsupported_edge_fields_must_be_null")
        return {
            "support_decision": decision,
            "edge_fields": None,
        }
    if not isinstance(edge_fields, dict) or set(edge_fields) != EDGE_FIELD_KEYS:
        raise PointerBindingError("invalid_pointer_free_edge_schema")
    if not all(
        isinstance(edge_fields[key], str) and edge_fields[key]
        for key in EDGE_FIELD_KEYS
    ):
        raise PointerBindingError("invalid_pointer_free_edge_value")
    if FORBIDDEN_MODEL_KEYS & set(edge_fields):
        raise PointerBindingError("edge_fields_contains_forbidden_pointer_field")
    return {
        "support_decision": decision,
        "edge_fields": copy.deepcopy(edge_fields),
    }


def bind_pointer(model_output: Any, bound_pointer: Any) -> dict[str, Any]:
    """Return the strict legacy shape after deterministic pointer binding."""

    output = validate_model_output(model_output)
    pointer = validate_pointer(bound_pointer)
    if output["support_decision"] == "unsupported_by_bound_pointer":
        normalized_edge = None
    else:
        normalized_edge = {
            **copy.deepcopy(output["edge_fields"]),
            "source_pointer": copy.deepcopy(pointer),
        }
    bound = {
        "support_decision": output["support_decision"],
        "normalized_edge": normalized_edge,
        "pointer": copy.deepcopy(pointer),
    }
    assert_binding_invariants(bound, pointer)
    return bound


def assert_binding_invariants(bound: Any, expected_pointer: Any) -> None:
    pointer = validate_pointer(expected_pointer)
    if not isinstance(bound, dict) or set(bound) != {
        "support_decision",
        "normalized_edge",
        "pointer",
    }:
        raise PointerBindingError("invalid_bound_top_level_schema")
    if bound["pointer"] != pointer:
        raise PointerBindingError("top_level_pointer_binding_mismatch")
    decision = bound["support_decision"]
    edge = bound["normalized_edge"]
    if decision == "unsupported_by_bound_pointer":
        if edge is not None:
            raise PointerBindingError("unsupported_bound_edge_must_be_null")
        return
    if decision != "supported" or not isinstance(edge, dict):
        raise PointerBindingError("invalid_bound_supported_edge")
    if set(edge) != EDGE_FIELD_KEYS | {"source_pointer"}:
        raise PointerBindingError("invalid_bound_edge_schema")
    if edge["source_pointer"] != pointer:
        raise PointerBindingError("edge_pointer_binding_mismatch")
    if canonical_sha256(bound["pointer"]) != canonical_sha256(
        edge["source_pointer"]
    ):
        raise PointerBindingError("bound_pointer_sha256_mismatch")


def model_output_from_bound_gold(example: dict[str, Any]) -> dict[str, Any]:
    """Build private scoring/training target; never call this in admission."""

    decision = example["support_decision"]
    if decision == "unsupported_by_bound_pointer":
        return {"support_decision": decision, "edge_fields": None}
    edge = copy.deepcopy(example["normalized_edge"])
    if not isinstance(edge, dict):
        raise PointerBindingError("supported_gold_edge_is_missing")
    if edge.pop("source_pointer", None) != example["pointer"]:
        raise PointerBindingError("gold_pointer_identity_mismatch")
    return validate_model_output(
        {"support_decision": decision, "edge_fields": edge}
    )


def main() -> int:
    raise SystemExit(
        "library-only module: use the hash-locked pointer-bound runner"
    )


if __name__ == "__main__":
    main()
