from __future__ import annotations

from fractions import Fraction
import importlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"
TRACE_SCHEMA_PATH = ROOT / "schemas" / "part-b-cost-trace.schema.json"
POLICY_PATH = CONFIG_DIR / "part-b-b3-capture-fixture-policy-v0.8.yaml"
FIXTURE_PATH = CONFIG_DIR / "part-b-b3-capture-fixture-v0.8.yaml"
RUNTIME_MODULE = "src.cost.part_b_b3_capture_fixture"


SYNTHETIC_EVENTS = [
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


def require_product(test_case: unittest.TestCase, path: Path) -> Path:
    if not path.is_file():
        test_case.fail(
            "missing approved B3 capture fixture artifact: "
            f"{path.relative_to(ROOT)}"
        )
    return path


def load_yaml(test_case: unittest.TestCase, path: Path) -> dict[str, object]:
    product = require_product(test_case, path)
    return yaml.safe_load(product.read_text(encoding="utf-8"))


def fraction_value(row: dict[str, object]) -> Fraction | None:
    raw = row["value"]
    if raw is None:
        return None
    return Fraction(raw["numerator"], raw["denominator"])


class PartBB3CaptureFixtureRuntimeTests(unittest.TestCase):
    def require_api(self):
        try:
            return importlib.import_module(RUNTIME_MODULE)
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(
                "missing approved B3 capture fixture module: "
                f"{RUNTIME_MODULE} ({exc})"
            )

    def inputs(self):
        api = self.require_api()
        policy = load_yaml(self, POLICY_PATH)
        fixture = load_yaml(self, FIXTURE_PATH)
        return api, policy, fixture

    def capture(
        self,
        *,
        events: list[dict[str, object]] | None = None,
        unknown_dimensions: dict[str, str] | None = None,
    ) -> dict[str, object]:
        api, policy, fixture = self.inputs()
        return api.capture_fixture(
            policy=policy,
            fixture=fixture,
            trace_id="B3-TRACE-901",
            attempt_id="ATTEMPT-901",
            action_id="ACTION-901",
            events=list(SYNTHETIC_EVENTS if events is None else events),
            unknown_dimensions=unknown_dimensions,
        )

    def test_red_08_fixed_synthetic_events_produce_eight_dimension_trace(self):
        """RED-08: fixed fixture events map to the existing B3 trace contract."""
        result = self.capture()
        trace = result["trace"]
        schema = json.loads(
            TRACE_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual(
            list(Draft202012Validator(schema).iter_errors(trace)),
            [],
        )
        dimensions = {row["dimension_id"]: row for row in trace["dimensions"]}
        self.assertEqual(fraction_value(dimensions["T_human"]), Fraction(2, 1))
        self.assertEqual(fraction_value(dimensions["T_wall"]), Fraction(3, 1))
        self.assertEqual(fraction_value(dimensions["T_CPU"]), Fraction(3, 2))
        self.assertEqual(
            fraction_value(dimensions["M_byte_sec"]),
            Fraction(3, 1),
        )
        self.assertEqual(fraction_value(dimensions["D_scan"]), Fraction(4096, 1))
        self.assertEqual(fraction_value(dimensions["N_record"]), Fraction(18, 1))
        self.assertEqual(fraction_value(dimensions["C_money"]), Fraction(125, 1))
        self.assertEqual(fraction_value(dimensions["T_auth"]), Fraction(1, 2))

    def test_red_09_identical_inputs_replay_identical_trace_and_hash(self):
        """RED-09: the same synthetic input is byte-for-value reproducible."""
        left = self.capture()
        right = self.capture()
        self.assertEqual(left, right)
        self.assertEqual(left["trace"], right["trace"])
        self.assertEqual(left["hash"], canonical_document_hash(left))
        self.assertEqual(left["trace"]["hash"], canonical_document_hash(left["trace"]))

    def test_red_10_provenance_is_fixture_synthetic_not_production(self):
        """RED-10: provenance prevents synthetic output from becoming measurement."""
        result = self.capture()
        self.assertEqual(result["provenance"]["source_kind"], "FIXTURE_SYNTHETIC")
        self.assertEqual(
            result["provenance"]["measurement_class"],
            "NOT_PRODUCTION_MEASUREMENT",
        )
        self.assertFalse(result["provenance"]["real_os_access"])
        self.assertFalse(result["provenance"]["billing_connector_access"])
        self.assertFalse(result["provenance"]["production_adapter_authority"])

    def test_red_11_missing_dimensions_are_unknown_not_zero(self):
        """RED-11: absent fixture dimensions remain explicit UNKNOWN_NOT_ZERO."""
        unknown = {
            "T_human": "SOURCE_UNAVAILABLE",
            "T_CPU": "INSTRUMENT_NOT_ENABLED",
            "M_byte_sec": "INSTRUMENT_NOT_ENABLED",
            "D_scan": "SOURCE_UNAVAILABLE",
            "N_record": "SOURCE_UNAVAILABLE",
            "C_money": "NOT_BILLED_TRACE_UNAVAILABLE",
            "T_auth": "SOURCE_UNAVAILABLE",
        }
        result = self.capture(
            events=[
                {
                    "event_id": "EV-WALL-ONLY",
                    "event_type": "EXECUTOR_WALL_INTERVAL",
                    "start_ns": 0,
                    "end_ns": 1_000_000_000,
                }
            ],
            unknown_dimensions=unknown,
        )
        dimensions = {row["dimension_id"]: row for row in result["trace"]["dimensions"]}
        self.assertEqual(fraction_value(dimensions["T_wall"]), Fraction(1, 1))
        for dimension_id, row in dimensions.items():
            if dimension_id != "T_wall":
                self.assertEqual(row["measurement_status"], "UNKNOWN")
                self.assertIsNone(row["value"])
                self.assertNotEqual(row["value"], 0)
                self.assertIsInstance(row["missing_reason"], str)

    def test_red_12_mixed_currency_fails_closed_without_fx(self):
        """RED-12: no implicit foreign-exchange normalization is available."""
        mixed = list(SYNTHETIC_EVENTS)
        mixed.append(
            {
                "event_id": "EV-MONEY-EUR",
                "event_type": "BILLED_USAGE",
                "currency_code": "EUR",
                "currency_microunits": 10,
            }
        )
        with self.assertRaises(ValueError):
            self.capture(events=mixed)

    def test_red_13_result_has_no_scalarization_or_performance_claim(self):
        """RED-13: fixture capture emits a vector, never a scalar claim."""
        result = self.capture()
        trace = result["trace"]
        self.assertIsNone(trace["scalar_cost"])
        self.assertFalse(trace["performance_claim_authority"])
        self.assertFalse(result["scalarization_authority"])
        self.assertFalse(result["performance_claim_authority"])
        self.assertNotIn("superiority_claim", result)

    def test_red_14_event_order_does_not_change_trace_identity(self):
        """RED-14: event ordering is deterministic and does not alter hashes."""
        forward = self.capture(events=list(SYNTHETIC_EVENTS))
        reverse = self.capture(events=list(reversed(SYNTHETIC_EVENTS)))
        self.assertEqual(forward, reverse)

    def test_red_15_fixture_result_has_no_execution_or_stop_power(self):
        """RED-15: local capture cannot execute, admit, hold out, or STOP."""
        result = self.capture()
        self.assertFalse(result["production_capture_authority"])
        self.assertFalse(result["real_adapter_authority"])
        self.assertFalse(result["holdout_release_authority"])
        self.assertEqual(result["stop_authority"], "NONE")
        encoded = json.dumps(result, sort_keys=True)
        for forbidden in (
            "system_status",
            "certificate",
            "CERTIFIED_STOP",
            "planner_action",
            "holdout_result",
            "performance_claim_result",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, result)
                self.assertNotIn(forbidden, encoded)


if __name__ == "__main__":
    unittest.main()
