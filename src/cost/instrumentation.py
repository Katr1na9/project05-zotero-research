"""Deterministic aggregation of evaluator-supplied B3 cost events.

This module does not execute an action, read a clock, sample an observation,
open a connector, rank a planner action, or emit a system state.  It accepts
already captured integer events and produces the frozen eight-dimensional cost
vector with exact-rational values and explicit UNKNOWN missingness.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
    has_valid_document_hash,
)


NANOSECONDS_PER_SECOND: Final = 1_000_000_000
APPROVED_B0_COST_CONTRACT_HASH: Final = (
    "sha256:b6d36c40f7b52c12733dbe75cbcba6058e952f23d67e2155bd73196f6bcfaf53"
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
UNITS: Final = {
    "T_human": "seconds",
    "T_wall": "seconds",
    "T_CPU": "cpu_seconds",
    "M_byte_sec": "byte_seconds",
    "D_scan": "bytes",
    "N_record": "records",
    "C_money": "currency_microunits",
    "T_auth": "seconds",
}
AGGREGATIONS: Final = {
    "T_human": "sum",
    "T_wall": "elapsed",
    "T_CPU": "sum",
    "M_byte_sec": "integral",
    "D_scan": "sum",
    "N_record": "sum",
    "C_money": "sum",
    "T_auth": "sum",
}
EVENT_DIMENSIONS: Final = {
    "HUMAN_ACTIVITY": ("T_human",),
    "EXECUTOR_WALL_INTERVAL": ("T_wall",),
    "CPU_ACCOUNTING": ("T_CPU",),
    "MEMORY_INTEGRAL": ("M_byte_sec",),
    "SOURCE_SCAN": ("D_scan", "N_record"),
    "BILLED_USAGE": ("C_money",),
    "AUTHORIZATION_ACTIVITY": ("T_auth",),
}
EVENT_FIELDS: Final = {
    "HUMAN_ACTIVITY": ("duration_ns",),
    "EXECUTOR_WALL_INTERVAL": ("start_ns", "end_ns"),
    "CPU_ACCOUNTING": ("cpu_delta_ns",),
    "MEMORY_INTEGRAL": ("byte_nanoseconds",),
    "SOURCE_SCAN": ("bytes_scanned", "records_scanned"),
    "BILLED_USAGE": ("currency_code", "currency_microunits"),
    "AUTHORIZATION_ACTIVITY": ("duration_ns",),
}
EXPECTED_POLICY_DIMENSIONS: Final = (
    ("T_human", "seconds", "sum", "HUMAN_ACTIVITY", ("duration_ns",)),
    (
        "T_wall",
        "seconds",
        "elapsed",
        "EXECUTOR_WALL_INTERVAL",
        ("start_ns", "end_ns"),
    ),
    ("T_CPU", "cpu_seconds", "sum", "CPU_ACCOUNTING", ("cpu_delta_ns",)),
    (
        "M_byte_sec",
        "byte_seconds",
        "integral",
        "MEMORY_INTEGRAL",
        ("byte_nanoseconds",),
    ),
    ("D_scan", "bytes", "sum", "SOURCE_SCAN", ("bytes_scanned",)),
    ("N_record", "records", "sum", "SOURCE_SCAN", ("records_scanned",)),
    (
        "C_money",
        "currency_microunits",
        "sum",
        "BILLED_USAGE",
        ("currency_code", "currency_microunits"),
    ),
    (
        "T_auth",
        "seconds",
        "sum",
        "AUTHORIZATION_ACTIVITY",
        ("duration_ns",),
    ),
)
EXPECTED_POLICY_SECTIONS: Final = {
    "capture_boundary": {
        "input": "EVALUATOR_SUPPLIED_INTEGER_EVENTS",
        "clock_access": False,
        "executor_hook": False,
        "external_connector": False,
        "event_order_semantics": "ORDER_INVARIANT_EVENT_ID_UNIQUE",
    },
    "exact_arithmetic": {
        "integer_input_required": True,
        "binary_float_input_allowed": False,
        "nanoseconds_per_second": NANOSECONDS_PER_SECOND,
        "output_encoding": "REDUCED_EXACT_RATIONAL",
    },
    "missingness": {
        "missing_measurement": "UNKNOWN_NOT_ZERO",
        "implicit_zero_forbidden": True,
        "explicit_reason_required": True,
        "complete_trace_rule": "ALL_EIGHT_DIMENSIONS_MEASURED",
    },
    "currency": {
        "code_format": "ISO_4217_UPPERCASE",
        "trace_currency_count": "ZERO_OR_ONE",
        "mixed_currency_behavior": "FAIL_CLOSED_NO_IMPLICIT_FX",
        "fx_normalization_authority": False,
    },
    "feasibility": {
        "semantics": "SEPARATE_NOT_HIGH_COST",
        "partial_trace_preserved": True,
        "infeasible_scalar_cost": None,
    },
    "scalarization": {
        "enabled": False,
        "weights": None,
        "normalization": None,
        "sensitivity_grid": None,
    },
}
MISSING_REASONS: Final = frozenset(
    {
        "SOURCE_UNAVAILABLE",
        "INSTRUMENT_NOT_ENABLED",
        "NOT_BILLED_TRACE_UNAVAILABLE",
        "NOT_EXECUTED",
        "TIMEOUT_UNKNOWN",
        "RESOURCE_EXHAUSTED_UNKNOWN",
    }
)
FEASIBILITY_STATUSES: Final = frozenset(
    {"EXECUTED", "INFEASIBLE", "FAILED", "NOT_EXECUTED"}
)


class CostInstrumentationError(ValueError):
    """Base class for fail-closed cost instrumentation errors."""

    code = "B3-COST-001_INVALID_EVENT"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code or type(self).code


class DuplicateEventError(CostInstrumentationError):
    """Two source events reused one event ID."""

    code = "B3-COST-002_DUPLICATE_EVENT_ID"


class IncompleteMeasurementDeclarationError(CostInstrumentationError):
    """A dimension had neither measurement events nor explicit UNKNOWN."""

    code = "B3-COST-003_UNDECLARED_MISSING_DIMENSION"


class MeasurementConflictError(CostInstrumentationError):
    """A dimension was declared both measured and UNKNOWN."""

    code = "B3-COST-004_MEASURED_UNKNOWN_CONFLICT"


class MixedCurrencyError(CostInstrumentationError):
    """A trace attempted to aggregate money across currencies."""

    code = "B3-COST-005_MIXED_CURRENCY_NO_FX"


class PolicyBindingError(CostInstrumentationError):
    """A policy identity, authority flag, or frozen section was invalid."""

    code = "B3-COST-006_POLICY_HASH_MISMATCH"


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise CostInstrumentationError(f"{field_name} must be a non-empty string")
    return value


def _nonnegative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CostInstrumentationError(
            f"{field_name} must be a non-negative integer"
        )
    return value


def _rational(value: Fraction | int) -> dict[str, int]:
    fraction = Fraction(value)
    return {
        "numerator": fraction.numerator,
        "denominator": fraction.denominator,
    }


def _string_tuple(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise CostInstrumentationError(f"{field_name} must be a string sequence")
    result = tuple(values)
    if any(not isinstance(value, str) or not value for value in result):
        raise CostInstrumentationError(
            f"{field_name} must contain non-empty strings"
        )
    if len(set(result)) != len(result):
        raise CostInstrumentationError(f"{field_name} must be unique")
    return result


def _normalize_event(raw: Mapping[str, object], index: int) -> dict[str, object]:
    if not isinstance(raw, Mapping):
        raise CostInstrumentationError(f"events[{index}] must be an object")
    event_id = _required_string(raw.get("event_id"), f"events[{index}].event_id")
    event_type = _required_string(
        raw.get("event_type"), f"events[{index}].event_type"
    )
    if event_type not in EVENT_FIELDS:
        raise CostInstrumentationError(f"unsupported event_type {event_type!r}")
    expected = {"event_id", "event_type", *EVENT_FIELDS[event_type]}
    if set(raw) != expected:
        raise CostInstrumentationError(
            f"event {event_id!r} fields must be exactly {sorted(expected)!r}"
        )

    normalized = {"event_id": event_id, "event_type": event_type}
    for field in EVENT_FIELDS[event_type]:
        value = raw[field]
        if field == "currency_code":
            currency = _required_string(value, f"event {event_id!r}.{field}")
            if len(currency) != 3 or not currency.isascii() or not currency.isupper():
                raise CostInstrumentationError(
                    f"event {event_id!r}.currency_code must be three uppercase ASCII letters"
                )
            normalized[field] = currency
        else:
            normalized[field] = _nonnegative_int(
                value, f"event {event_id!r}.{field}"
            )
    if event_type == "EXECUTOR_WALL_INTERVAL":
        if normalized["end_ns"] < normalized["start_ns"]:
            raise CostInstrumentationError(
                f"event {event_id!r}.end_ns precedes start_ns"
            )
    return normalized


@dataclass(frozen=True)
class CostTraceResult:
    """Immutable schema-ready B3 cost trace."""

    document: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        return deepcopy(dict(self.document))


class CostTraceInstrumenter:
    """Aggregate injected integer events into an exact eight-dimensional trace."""

    def __init__(self, policy: Mapping[str, object]) -> None:
        if not isinstance(policy, Mapping):
            raise PolicyBindingError("policy must be an object")
        frozen = deepcopy(dict(policy))
        if not has_valid_document_hash(frozen):
            raise PolicyBindingError("policy hash does not replay")
        if frozen.get("policy_id") != "part-b-cost-instrumentation-policy-v0.8":
            raise PolicyBindingError("policy ID is not frozen")
        if frozen.get("policy_version") != "0.8.0":
            raise PolicyBindingError("policy version is not frozen")
        if frozen.get("authorized_slice") != "B3_COST_INSTRUMENTATION":
            raise PolicyBindingError("policy is not a B3 policy")
        if frozen.get("b0_cost_contract_hash") != APPROVED_B0_COST_CONTRACT_HASH:
            raise PolicyBindingError("B0 cost-contract binding is not approved")
        if frozen.get("instrumentation_authority") is not True:
            raise PolicyBindingError("instrumentation authority is absent")
        for field in (
            "action_execution_authority",
            "sampling_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            if frozen.get(field) is not False:
                raise PolicyBindingError(f"{field} must remain false")
        if frozen.get("stop_authority") != "NONE":
            raise PolicyBindingError("B3 has no STOP authority")
        for section_name, expected in EXPECTED_POLICY_SECTIONS.items():
            if frozen.get(section_name) != expected:
                raise PolicyBindingError(
                    f"policy.{section_name} is not the frozen B3 contract"
                )
        raw_dimensions = frozen.get("dimensions")
        if not isinstance(raw_dimensions, Sequence) or isinstance(
            raw_dimensions, (str, bytes)
        ):
            raise PolicyBindingError("policy.dimensions must be a sequence")
        signatures: list[tuple[object, ...]] = []
        for index, row in enumerate(raw_dimensions):
            if not isinstance(row, Mapping):
                raise PolicyBindingError(
                    f"policy.dimensions[{index}] must be an object"
                )
            source_fields = row.get("source_fields")
            if not isinstance(source_fields, Sequence) or isinstance(
                source_fields, (str, bytes)
            ):
                raise PolicyBindingError(
                    f"policy.dimensions[{index}].source_fields must be a sequence"
                )
            signatures.append(
                (
                    row.get("dimension_id"),
                    row.get("unit"),
                    row.get("aggregation"),
                    row.get("event_type"),
                    tuple(source_fields),
                )
            )
        if tuple(signatures) != EXPECTED_POLICY_DIMENSIONS:
            raise PolicyBindingError(
                "policy dimension definitions are not the frozen B3 contract"
            )
        self._policy = frozen
        self._policy_hash = _required_string(frozen.get("hash"), "policy.hash")

    def aggregate(
        self,
        *,
        trace_id: str,
        attempt_id: str,
        action_id: str,
        events: Sequence[Mapping[str, object]],
        unknown_dimensions: Mapping[str, str] | None = None,
        feasibility_status: str = "EXECUTED",
        reason_codes: Sequence[str] = (),
    ) -> CostTraceResult:
        trace_id = _required_string(trace_id, "trace_id")
        attempt_id = _required_string(attempt_id, "attempt_id")
        action_id = _required_string(action_id, "action_id")
        if feasibility_status not in FEASIBILITY_STATUSES:
            raise CostInstrumentationError(
                f"unsupported feasibility_status {feasibility_status!r}"
            )
        frozen_reasons = tuple(sorted(_string_tuple(reason_codes, "reason_codes")))

        if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
            raise CostInstrumentationError("events must be a sequence")
        normalized_events = tuple(
            _normalize_event(event, index) for index, event in enumerate(events)
        )
        event_ids = [str(event["event_id"]) for event in normalized_events]
        if len(set(event_ids)) != len(event_ids):
            raise DuplicateEventError("event_id values must be unique")
        normalized_events = tuple(
            sorted(normalized_events, key=lambda event: str(event["event_id"]))
        )

        unknown = self._normalize_unknowns(unknown_dimensions or {})
        events_by_dimension: dict[str, list[dict[str, object]]] = {
            dimension_id: [] for dimension_id in DIMENSION_ORDER
        }
        for event in normalized_events:
            for dimension_id in EVENT_DIMENSIONS[str(event["event_type"])]:
                events_by_dimension[dimension_id].append(event)

        for dimension_id in DIMENSION_ORDER:
            has_events = bool(events_by_dimension[dimension_id])
            is_unknown = dimension_id in unknown
            if has_events and is_unknown:
                raise MeasurementConflictError(
                    f"{dimension_id} cannot be measured and UNKNOWN"
                )
            if not has_events and not is_unknown:
                raise IncompleteMeasurementDeclarationError(
                    f"{dimension_id} needs events or explicit UNKNOWN"
                )

        currency_code = self._currency_code(events_by_dimension["C_money"])
        dimensions = tuple(
            self._dimension_row(
                dimension_id,
                events_by_dimension[dimension_id],
                unknown.get(dimension_id),
            )
            for dimension_id in DIMENSION_ORDER
        )
        complete = all(
            row["measurement_status"] == "MEASURED" for row in dimensions
        )
        status = self._trace_status(feasibility_status, complete)
        source_payload = {
            "events": list(normalized_events),
            "unknown_dimensions": dict(sorted(unknown.items())),
            "feasibility_status": feasibility_status,
            "reason_codes": list(frozen_reasons),
        }
        document: dict[str, object] = {
            "schema_version": "0.8.0",
            "trace_id": trace_id,
            "attempt_id": attempt_id,
            "action_id": action_id,
            "policy_hash": self._policy_hash,
            "source_trace_hash": canonical_value_hash(source_payload),
            "status": status,
            "feasibility_status": feasibility_status,
            "reason_codes": list(frozen_reasons),
            "currency_code": currency_code,
            "complete": complete,
            "dimensions": list(dimensions),
            "scalar_cost": None,
            "performance_claim_authority": False,
        }
        document["hash"] = canonical_document_hash(document)
        return CostTraceResult(document)

    @staticmethod
    def _normalize_unknowns(
        raw: Mapping[str, str],
    ) -> dict[str, str]:
        if not isinstance(raw, Mapping):
            raise CostInstrumentationError("unknown_dimensions must be an object")
        unknown: dict[str, str] = {}
        for dimension_id, reason in raw.items():
            if dimension_id not in DIMENSION_ORDER:
                raise CostInstrumentationError(
                    f"unknown dimension {dimension_id!r}"
                )
            if reason not in MISSING_REASONS:
                raise CostInstrumentationError(
                    f"unsupported missing reason {reason!r}"
                )
            unknown[dimension_id] = reason
        return unknown

    @staticmethod
    def _currency_code(events: Sequence[Mapping[str, object]]) -> str | None:
        currencies = {
            _required_string(event.get("currency_code"), "currency_code")
            for event in events
        }
        if len(currencies) > 1:
            raise MixedCurrencyError(
                "mixed currencies require a separately approved FX contract"
            )
        return next(iter(currencies), None)

    @staticmethod
    def _trace_status(feasibility_status: str, complete: bool) -> str:
        if feasibility_status == "INFEASIBLE":
            return "INFEASIBLE_WITH_PARTIAL_TRACE"
        if feasibility_status == "FAILED":
            return "FAILED_WITH_PARTIAL_TRACE"
        if feasibility_status == "NOT_EXECUTED":
            return "NOT_EXECUTED_WITH_PARTIAL_TRACE"
        return "COMPLETE" if complete else "PARTIAL_UNKNOWN"

    def _dimension_row(
        self,
        dimension_id: str,
        events: Sequence[Mapping[str, object]],
        missing_reason: str | None,
    ) -> dict[str, object]:
        if not events:
            return {
                "dimension_id": dimension_id,
                "unit": UNITS[dimension_id],
                "aggregation": AGGREGATIONS[dimension_id],
                "measurement_status": "UNKNOWN",
                "value": None,
                "source_event_ids": [],
                "missing_reason": missing_reason,
            }

        event_ids = sorted(str(event["event_id"]) for event in events)
        if dimension_id in {"T_human", "T_auth"}:
            total = sum(int(event["duration_ns"]) for event in events)
            measured = Fraction(total, NANOSECONDS_PER_SECOND)
        elif dimension_id == "T_wall":
            start = min(int(event["start_ns"]) for event in events)
            end = max(int(event["end_ns"]) for event in events)
            measured = Fraction(end - start, NANOSECONDS_PER_SECOND)
        elif dimension_id == "T_CPU":
            total = sum(int(event["cpu_delta_ns"]) for event in events)
            measured = Fraction(total, NANOSECONDS_PER_SECOND)
        elif dimension_id == "M_byte_sec":
            total = sum(int(event["byte_nanoseconds"]) for event in events)
            measured = Fraction(total, NANOSECONDS_PER_SECOND)
        elif dimension_id == "D_scan":
            measured = Fraction(
                sum(int(event["bytes_scanned"]) for event in events), 1
            )
        elif dimension_id == "N_record":
            measured = Fraction(
                sum(int(event["records_scanned"]) for event in events), 1
            )
        elif dimension_id == "C_money":
            measured = Fraction(
                sum(int(event["currency_microunits"]) for event in events), 1
            )
        else:  # pragma: no cover - guarded by the frozen dimension order
            raise CostInstrumentationError(
                f"unsupported dimension {dimension_id!r}"
            )
        return {
            "dimension_id": dimension_id,
            "unit": UNITS[dimension_id],
            "aggregation": AGGREGATIONS[dimension_id],
            "measurement_status": "MEASURED",
            "value": _rational(measured),
            "source_event_ids": event_ids,
            "missing_reason": None,
        }
