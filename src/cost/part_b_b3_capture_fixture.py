"""Deterministic synthetic B3 capture fixture.

This adapter is deliberately local and synthetic.  It consumes caller-supplied
integer events, delegates the eight-dimensional aggregation to the frozen B3
instrumenter, and wraps the resulting trace with explicit non-production
provenance.  It never reads an operating-system counter, billing connector,
clock, holdout, or production adapter.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Final

import yaml

from src.cost.instrumentation import CostTraceInstrumenter
from src.ir.canonical_hash import (
    canonical_document_hash,
    has_valid_document_hash,
)


FROZEN_B3_POLICY_PATH: Final = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "part-b-cost-instrumentation-policy-v0.8.yaml"
)
FROZEN_B3_POLICY_HASH: Final = (
    "sha256:c64865166be067da37a6f4f5d745ce8dc0421dc342d88589c9bbce6142eb3278"
)
DIMENSION_ORDER: Final = (
    "T_human",
    "T_wall",
    "T_CPU",
    "M_byte_sec",
    "D_scan",
    "N_record",
    "C_money",
    "T_auth",
)


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _required_string(
    value: object,
    label: str,
) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _load_frozen_b3_policy() -> dict[str, object]:
    if not FROZEN_B3_POLICY_PATH.is_file():
        raise ValueError("frozen B3 instrumentation policy is missing")
    document = yaml.safe_load(
        FROZEN_B3_POLICY_PATH.read_text(encoding="utf-8")
    )
    if not isinstance(document, dict) or not has_valid_document_hash(document):
        raise ValueError("frozen B3 instrumentation policy hash does not replay")
    if document.get("hash") != FROZEN_B3_POLICY_HASH:
        raise ValueError("frozen B3 instrumentation policy hash is not approved")
    return document


def _validate_policy(policy: Mapping[str, object]) -> None:
    if not has_valid_document_hash(policy):
        raise ValueError("capture fixture policy hash does not replay")
    expected = {
        "status": "B3_CAPTURE_FIXTURE_LOCAL_ONLY",
        "authorized_slice": "B3_COST_INSTRUMENTATION_FIXTURE_ONLY",
        "fixture_capture_authority": True,
        "production_adapter_authority": False,
        "real_os_access": False,
        "billing_connector_access": False,
        "action_execution_authority": False,
        "holdout_release_authority": False,
        "scalarization_authority": False,
        "performance_claim_authority": False,
        "superiority_claim_authority": False,
        "stop_authority": "NONE",
        "b3_policy_hash": FROZEN_B3_POLICY_HASH,
        "b3_trace_schema_path": "schemas/part-b-cost-trace.schema.json",
    }
    for field, expected_value in expected.items():
        if policy.get(field) != expected_value:
            raise ValueError(f"capture fixture policy.{field} is not frozen")

    dimensions = policy.get("dimensions")
    if not isinstance(dimensions, Sequence) or isinstance(
        dimensions, (str, bytes)
    ):
        raise ValueError("capture fixture policy dimensions are invalid")
    if tuple(
        row.get("dimension_id")
        for row in dimensions
        if isinstance(row, Mapping)
    ) != DIMENSION_ORDER:
        raise ValueError("capture fixture policy dimension order is not frozen")
    missingness = _mapping(policy.get("missingness"), "missingness")
    if missingness.get("missing_measurement") != "UNKNOWN_NOT_ZERO":
        raise ValueError("capture fixture missingness is not UNKNOWN_NOT_ZERO")
    if missingness.get("implicit_zero_forbidden") is not True:
        raise ValueError("implicit zero is not forbidden")
    currency = _mapping(policy.get("currency"), "currency")
    if currency.get("mixed_currency_behavior") != "FAIL_CLOSED_NO_IMPLICIT_FX":
        raise ValueError("capture fixture currency policy is not fail-closed")
    if currency.get("fx_normalization_authority") is not False:
        raise ValueError("capture fixture cannot hold FX authority")
    scalarization = _mapping(policy.get("scalarization"), "scalarization")
    if scalarization.get("enabled") is not False:
        raise ValueError("capture fixture scalarization must remain disabled")


def _validate_fixture(
    fixture: Mapping[str, object],
    policy_hash: str,
) -> None:
    if not has_valid_document_hash(fixture):
        raise ValueError("capture fixture hash does not replay")
    expected = {
        "fixture_id": "part-b-b3-capture-fixture-v0.8",
        "source_kind": "FIXTURE_SYNTHETIC",
        "measurement_class": "NOT_PRODUCTION_MEASUREMENT",
        "b3_policy_hash": policy_hash,
        "real_os_access": False,
        "billing_connector_access": False,
        "production_adapter_authority": False,
        "catalog_ceiling_eligible": False,
    }
    for field, expected_value in expected.items():
        if fixture.get(field) != expected_value:
            raise ValueError(f"capture fixture.{field} is not frozen")
    if not isinstance(fixture.get("events"), Sequence) or isinstance(
        fixture.get("events"), (str, bytes)
    ):
        raise ValueError("capture fixture events must be an array")


def capture_fixture(
    *,
    policy: Mapping[str, object],
    fixture: Mapping[str, object],
    trace_id: str,
    attempt_id: str,
    action_id: str,
    events: Sequence[Mapping[str, object]],
    unknown_dimensions: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Aggregate synthetic events and return a non-production result wrapper."""

    policy = _mapping(policy, "policy")
    fixture = _mapping(fixture, "fixture")
    _validate_policy(policy)
    frozen_b3_policy = _load_frozen_b3_policy()
    _validate_fixture(fixture, frozen_b3_policy["hash"])
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        raise ValueError("events must be an array")

    instrumenter = CostTraceInstrumenter(frozen_b3_policy)
    trace = instrumenter.aggregate(
        trace_id=_required_string(trace_id, "trace_id"),
        attempt_id=_required_string(attempt_id, "attempt_id"),
        action_id=_required_string(action_id, "action_id"),
        events=events,
        unknown_dimensions=unknown_dimensions,
    ).to_dict()

    result: dict[str, object] = {
        "schema_version": "0.8.0",
        "trace": trace,
        "provenance": {
            "source_kind": "FIXTURE_SYNTHETIC",
            "measurement_class": "NOT_PRODUCTION_MEASUREMENT",
            "real_os_access": False,
            "billing_connector_access": False,
            "production_adapter_authority": False,
        },
        "fixture_hash": fixture["hash"],
        "b3_policy_hash": frozen_b3_policy["hash"],
        "scalarization_authority": False,
        "performance_claim_authority": False,
        "production_capture_authority": False,
        "real_adapter_authority": False,
        "holdout_release_authority": False,
        "stop_authority": "NONE",
    }
    result["hash"] = canonical_document_hash(result)
    return deepcopy(result)


__all__ = ["capture_fixture"]
