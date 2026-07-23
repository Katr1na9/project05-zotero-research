from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.cost.instrumentation import (
    CostInstrumentationError,
    CostTraceInstrumenter,
    DuplicateEventError,
    IncompleteMeasurementDeclarationError,
    MeasurementConflictError,
    MixedCurrencyError,
    PolicyBindingError,
)
from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "schemas" / "part-b-cost-trace.schema.json").read_text(
        encoding="utf-8"
    )
)
POLICY = yaml.safe_load(
    (ROOT / "configs" / "part-b-cost-instrumentation-policy-v0.8.yaml").read_text(
        encoding="utf-8"
    )
)


def value(row: dict[str, object]) -> Fraction | None:
    raw = row["value"]
    if raw is None:
        return None
    return Fraction(raw["numerator"], raw["denominator"])


def complete_events() -> list[dict[str, object]]:
    return [
        {
            "event_id": "EV-HUMAN-001",
            "event_type": "HUMAN_ACTIVITY",
            "duration_ns": 2_000_000_000,
        },
        {
            "event_id": "EV-WALL-001",
            "event_type": "EXECUTOR_WALL_INTERVAL",
            "start_ns": 1_000_000_000,
            "end_ns": 3_000_000_000,
        },
        {
            "event_id": "EV-WALL-002",
            "event_type": "EXECUTOR_WALL_INTERVAL",
            "start_ns": 1_500_000_000,
            "end_ns": 4_000_000_000,
        },
        {
            "event_id": "EV-CPU-001",
            "event_type": "CPU_ACCOUNTING",
            "cpu_delta_ns": 1_500_000_000,
        },
        {
            "event_id": "EV-MEM-001",
            "event_type": "MEMORY_INTEGRAL",
            "byte_nanoseconds": 3_000_000_000,
        },
        {
            "event_id": "EV-SCAN-001",
            "event_type": "SOURCE_SCAN",
            "bytes_scanned": 4096,
            "records_scanned": 18,
        },
        {
            "event_id": "EV-MONEY-001",
            "event_type": "BILLED_USAGE",
            "currency_code": "USD",
            "currency_microunits": 125,
        },
        {
            "event_id": "EV-AUTH-001",
            "event_type": "AUTHORIZATION_ACTIVITY",
            "duration_ns": 500_000_000,
        },
    ]


class PartBB3CostInstrumentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instrumenter = CostTraceInstrumenter(POLICY)

    def test_complete_trace_aggregates_exact_eight_dimension_vector(self) -> None:
        trace = self.instrumenter.aggregate(
            trace_id="B3-TRACE-001",
            attempt_id="ATTEMPT-001",
            action_id="ACTION-001",
            events=complete_events(),
        ).to_dict()

        errors = list(Draft202012Validator(SCHEMA).iter_errors(trace))
        self.assertEqual(errors, [])
        self.assertEqual(trace["hash"], canonical_document_hash(trace))
        self.assertEqual(trace["status"], "COMPLETE")
        self.assertTrue(trace["complete"])
        self.assertEqual(trace["currency_code"], "USD")
        self.assertIsNone(trace["scalar_cost"])
        self.assertFalse(trace["performance_claim_authority"])

        dimensions = {row["dimension_id"]: row for row in trace["dimensions"]}
        self.assertEqual(value(dimensions["T_human"]), Fraction(2, 1))
        self.assertEqual(value(dimensions["T_wall"]), Fraction(3, 1))
        self.assertEqual(value(dimensions["T_CPU"]), Fraction(3, 2))
        self.assertEqual(value(dimensions["M_byte_sec"]), Fraction(3, 1))
        self.assertEqual(value(dimensions["D_scan"]), Fraction(4096, 1))
        self.assertEqual(value(dimensions["N_record"]), Fraction(18, 1))
        self.assertEqual(value(dimensions["C_money"]), Fraction(125, 1))
        self.assertEqual(value(dimensions["T_auth"]), Fraction(1, 2))

    def test_missing_dimensions_are_explicit_unknown_never_zero(self) -> None:
        trace = self.instrumenter.aggregate(
            trace_id="B3-TRACE-002",
            attempt_id="ATTEMPT-002",
            action_id="ACTION-002",
            events=[
                {
                    "event_id": "EV-WALL-001",
                    "event_type": "EXECUTOR_WALL_INTERVAL",
                    "start_ns": 0,
                    "end_ns": 1_000_000_000,
                }
            ],
            unknown_dimensions={
                "T_human": "SOURCE_UNAVAILABLE",
                "T_CPU": "INSTRUMENT_NOT_ENABLED",
                "M_byte_sec": "INSTRUMENT_NOT_ENABLED",
                "D_scan": "SOURCE_UNAVAILABLE",
                "N_record": "SOURCE_UNAVAILABLE",
                "C_money": "NOT_BILLED_TRACE_UNAVAILABLE",
                "T_auth": "SOURCE_UNAVAILABLE",
            },
        ).to_dict()

        self.assertEqual(trace["status"], "PARTIAL_UNKNOWN")
        self.assertFalse(trace["complete"])
        dimensions = {row["dimension_id"]: row for row in trace["dimensions"]}
        self.assertEqual(value(dimensions["T_wall"]), Fraction(1, 1))
        for dimension_id, row in dimensions.items():
            if dimension_id != "T_wall":
                self.assertEqual(row["measurement_status"], "UNKNOWN")
                self.assertIsNone(row["value"])
                self.assertNotEqual(row["value"], 0)

    def test_measured_zero_requires_and_preserves_source_provenance(self) -> None:
        events = complete_events()
        events[0]["duration_ns"] = 0
        trace = self.instrumenter.aggregate(
            trace_id="B3-TRACE-010",
            attempt_id="ATTEMPT-010",
            action_id="ACTION-010",
            events=events,
        ).to_dict()
        human = next(
            row for row in trace["dimensions"] if row["dimension_id"] == "T_human"
        )
        self.assertEqual(human["measurement_status"], "MEASURED")
        self.assertEqual(value(human), Fraction(0, 1))
        self.assertEqual(human["source_event_ids"], ["EV-HUMAN-001"])
        self.assertIsNone(human["missing_reason"])

    def test_undeclared_missing_dimension_fails_closed(self) -> None:
        with self.assertRaises(IncompleteMeasurementDeclarationError) as caught:
            self.instrumenter.aggregate(
                trace_id="B3-TRACE-003",
                attempt_id="ATTEMPT-003",
                action_id="ACTION-003",
                events=[],
            )
        self.assertEqual(
            caught.exception.code,
            "B3-COST-003_UNDECLARED_MISSING_DIMENSION",
        )

    def test_infeasible_is_not_encoded_as_high_cost(self) -> None:
        trace = self.instrumenter.aggregate(
            trace_id="B3-TRACE-004",
            attempt_id="ATTEMPT-004",
            action_id="ACTION-004",
            feasibility_status="INFEASIBLE",
            reason_codes=("AUTHORIZATION_DENIED",),
            events=[
                {
                    "event_id": "EV-AUTH-001",
                    "event_type": "AUTHORIZATION_ACTIVITY",
                    "duration_ns": 250_000_000,
                }
            ],
            unknown_dimensions={
                "T_human": "NOT_EXECUTED",
                "T_wall": "NOT_EXECUTED",
                "T_CPU": "NOT_EXECUTED",
                "M_byte_sec": "NOT_EXECUTED",
                "D_scan": "NOT_EXECUTED",
                "N_record": "NOT_EXECUTED",
                "C_money": "NOT_EXECUTED",
            },
        ).to_dict()

        self.assertEqual(trace["status"], "INFEASIBLE_WITH_PARTIAL_TRACE")
        self.assertEqual(trace["feasibility_status"], "INFEASIBLE")
        self.assertFalse(trace["complete"])
        auth = next(
            row for row in trace["dimensions"] if row["dimension_id"] == "T_auth"
        )
        self.assertEqual(value(auth), Fraction(1, 4))
        self.assertIsNone(trace["scalar_cost"])

    def test_mixed_currency_fails_closed_without_implicit_fx(self) -> None:
        events = complete_events()
        events.append(
            {
                "event_id": "EV-MONEY-002",
                "event_type": "BILLED_USAGE",
                "currency_code": "EUR",
                "currency_microunits": 10,
            }
        )
        with self.assertRaises(MixedCurrencyError) as caught:
            self.instrumenter.aggregate(
                trace_id="B3-TRACE-005",
                attempt_id="ATTEMPT-005",
                action_id="ACTION-005",
                events=events,
            )
        self.assertEqual(caught.exception.code, "B3-COST-005_MIXED_CURRENCY_NO_FX")

    def test_invalid_or_ambiguous_events_fail_closed(self) -> None:
        for mutation in (
            {"event_id": "EV-BAD-001", "event_type": "CPU_ACCOUNTING", "cpu_delta_ns": -1},
            {"event_id": "EV-BAD-002", "event_type": "CPU_ACCOUNTING", "cpu_delta_ns": True},
            {"event_id": "EV-BAD-003", "event_type": "UNKNOWN_EVENT", "value": 1},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaises(CostInstrumentationError):
                    self.instrumenter.aggregate(
                        trace_id="B3-TRACE-006",
                        attempt_id="ATTEMPT-006",
                        action_id="ACTION-006",
                        events=[mutation],
                    )

        duplicate = complete_events()
        duplicate.append(deepcopy(duplicate[0]))
        with self.assertRaises(DuplicateEventError) as caught:
            self.instrumenter.aggregate(
                trace_id="B3-TRACE-007",
                attempt_id="ATTEMPT-007",
                action_id="ACTION-007",
                events=duplicate,
            )
        self.assertEqual(caught.exception.code, "B3-COST-002_DUPLICATE_EVENT_ID")

        with self.assertRaises(MeasurementConflictError) as caught:
            self.instrumenter.aggregate(
                trace_id="B3-TRACE-011",
                attempt_id="ATTEMPT-011",
                action_id="ACTION-011",
                events=complete_events(),
                unknown_dimensions={"T_CPU": "INSTRUMENT_NOT_ENABLED"},
            )
        self.assertEqual(
            caught.exception.code,
            "B3-COST-004_MEASURED_UNKNOWN_CONFLICT",
        )

    def test_event_order_does_not_change_trace(self) -> None:
        forward = self.instrumenter.aggregate(
            trace_id="B3-TRACE-008",
            attempt_id="ATTEMPT-008",
            action_id="ACTION-008",
            events=complete_events(),
        ).to_dict()
        reverse = self.instrumenter.aggregate(
            trace_id="B3-TRACE-008",
            attempt_id="ATTEMPT-008",
            action_id="ACTION-008",
            events=list(reversed(complete_events())),
        ).to_dict()
        self.assertEqual(forward, reverse)

    def test_output_cannot_emit_system_or_certificate_state(self) -> None:
        trace = self.instrumenter.aggregate(
            trace_id="B3-TRACE-009",
            attempt_id="ATTEMPT-009",
            action_id="ACTION-009",
            events=complete_events(),
        ).to_dict()
        self.assertNotIn("system_status", trace)
        self.assertNotIn("certificate", trace)
        self.assertNotIn("CERTIFIED_STOP", json.dumps(trace))

    def test_policy_hash_or_dimension_tampering_fails_closed(self) -> None:
        bad_hash = deepcopy(POLICY)
        bad_hash["hash"] = "sha256:" + ("0" * 64)
        with self.assertRaises(PolicyBindingError) as caught:
            CostTraceInstrumenter(bad_hash)
        self.assertEqual(caught.exception.code, "B3-COST-006_POLICY_HASH_MISMATCH")

        changed_dimension = deepcopy(POLICY)
        changed_dimension["dimensions"][0]["unit"] = "minutes"
        changed_dimension["hash"] = canonical_document_hash(changed_dimension)
        with self.assertRaises(CostInstrumentationError):
            CostTraceInstrumenter(changed_dimension)

        changed_capture = deepcopy(POLICY)
        changed_capture["capture_boundary"]["clock_access"] = True
        changed_capture["hash"] = canonical_document_hash(changed_capture)
        with self.assertRaises(CostInstrumentationError):
            CostTraceInstrumenter(changed_capture)

        changed_binding = deepcopy(POLICY)
        changed_binding["b0_cost_contract_hash"] = "sha256:" + ("1" * 64)
        changed_binding["hash"] = canonical_document_hash(changed_binding)
        with self.assertRaises(CostInstrumentationError):
            CostTraceInstrumenter(changed_binding)


if __name__ == "__main__":
    unittest.main()
