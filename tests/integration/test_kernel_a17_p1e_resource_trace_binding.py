from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from src.planner import deterministic_depth1 as planner
from tests.unit.test_kernel_a17_p1e_depth1_planner import (
    FIXTURE_PATH,
    build_request,
    load_json,
)


ROOT = Path(__file__).resolve().parents[2]


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_trace_row(decision):
    fixture = load_json(FIXTURE_PATH)
    binding = decision["resource_trace_binding"]
    return {
        "attempt_id": binding["attempt_id"],
        "action_id": decision["selected_action_id"],
        "planner_decision_record_hash": decision["record_hash"],
        "resource_budget_hash": binding["resource_budget_hash"],
        "status": fixture["test_only_trace_seed"]["status"],
        "counts": deepcopy(fixture["test_only_trace_seed"]["counts"]),
        "resources": deepcopy(fixture["test_only_trace_seed"]["resources"]),
    }


class KernelA17P1eResourceTraceBindingTests(unittest.TestCase):
    def setUp(self):
        self.fixture = load_json(FIXTURE_PATH)
        self.request = build_request()
        self.decision = planner.evaluate_depth1_planner_request(self.request)
        self.assertEqual(planner.SELECT_ACTION, self.decision["decision"])
        self.trace_row = build_trace_row(self.decision)

    def test_decision_to_test_only_trace_receipt_matches_exactly(self):
        decision_before = deepcopy(self.decision)
        trace_before = deepcopy(self.trace_row)

        receipt = planner.validate_resource_trace_binding(
            self.decision, self.trace_row
        )

        self.assertEqual(set(receipt), planner.RECEIPT_FIELDS)
        self.assertEqual(
            "MATCH_TEST_ONLY_REPLAY", receipt["match_status"]
        )
        self.assertEqual([], receipt["reason_codes"])
        self.assertEqual(
            self.decision["record_hash"],
            receipt["planner_decision_record_hash"],
        )
        self.assertEqual(
            self.decision["resource_trace_binding"]["attempt_id"],
            receipt["attempt_id"],
        )
        self.assertEqual(
            self.decision["selected_action_id"], receipt["action_id"]
        )
        self.assertEqual(
            self.decision["resource_trace_binding"][
                "resource_budget_hash"
            ],
            receipt["resource_budget_hash"],
        )
        self.assertEqual(
            planner.canonical_hash_without_field(receipt, "receipt_hash"),
            receipt["receipt_hash"],
        )
        self.assertEqual(decision_before, self.decision)
        self.assertEqual(trace_before, self.trace_row)

    def test_receipt_is_deterministic_for_same_decision_and_trace(self):
        first = planner.validate_resource_trace_binding(
            self.decision, self.trace_row
        )
        second = planner.validate_resource_trace_binding(
            deepcopy(self.decision), deepcopy(self.trace_row)
        )
        self.assertEqual(first, second)
        self.assertEqual(first["receipt_hash"], second["receipt_hash"])

    def test_fail_closed_trace_mismatch_matrix(self):
        cases = []

        attempt = deepcopy(self.trace_row)
        attempt["attempt_id"] = "p1e-attempt:sha256:" + "0" * 64
        cases.append(
            (
                "attempt",
                self.decision,
                attempt,
                "P1E-018_TRACE_ATTEMPT_ID_MISMATCH",
            )
        )

        action = deepcopy(self.trace_row)
        action["action_id"] = "query_logon_origin_H3"
        cases.append(
            (
                "action",
                self.decision,
                action,
                "P1E-019_TRACE_ACTION_ID_MISMATCH",
            )
        )

        decision_hash = deepcopy(self.trace_row)
        decision_hash["planner_decision_record_hash"] = "sha256:" + "1" * 64
        cases.append(
            (
                "decision_hash",
                self.decision,
                decision_hash,
                "P1E-020_TRACE_DECISION_OR_BUDGET_HASH_MISMATCH",
            )
        )

        budget_hash = deepcopy(self.trace_row)
        budget_hash["resource_budget_hash"] = "sha256:" + "2" * 64
        cases.append(
            (
                "budget_hash",
                self.decision,
                budget_hash,
                "P1E-020_TRACE_DECISION_OR_BUDGET_HASH_MISMATCH",
            )
        )

        stale_decision = deepcopy(self.decision)
        stale_decision["selected_action_id"] = "query_logon_origin_H3"
        cases.append(
            (
                "stale_decision",
                stale_decision,
                self.trace_row,
                "P1E-020_TRACE_DECISION_OR_BUDGET_HASH_MISMATCH",
            )
        )

        malformed_trace = deepcopy(self.trace_row)
        malformed_trace["unexpected"] = True
        cases.append(
            (
                "malformed_trace",
                self.decision,
                malformed_trace,
                "P1E-018_TRACE_ATTEMPT_ID_MISMATCH",
            )
        )

        for name, decision, trace_row, expected_reason in cases:
            with self.subTest(name=name):
                decision_before = deepcopy(decision)
                trace_before = deepcopy(trace_row)
                receipt = planner.validate_resource_trace_binding(
                    decision, trace_row
                )
                self.assertEqual(
                    "DENY_TRACE_BINDING_MISMATCH",
                    receipt["match_status"],
                )
                self.assertIn(expected_reason, receipt["reason_codes"])
                self.assertEqual(decision_before, decision)
                self.assertEqual(trace_before, trace_row)

    def test_abstain_or_deny_decision_cannot_bind_trace(self):
        invalid_request = deepcopy(self.request)
        invalid_request["requested_decision_scope"] = "CERTIFIED_STOP"
        invalid_request["request_hash"] = (
            planner.canonical_hash_without_field(
                invalid_request, "request_hash"
            )
        )
        denied = planner.evaluate_depth1_planner_request(invalid_request)
        self.assertEqual(planner.DENY, denied["decision"])
        self.assertIsNone(denied["resource_trace_binding"])

        receipt = planner.validate_resource_trace_binding(
            denied, self.trace_row
        )
        self.assertEqual(
            "DENY_TRACE_BINDING_MISMATCH", receipt["match_status"]
        )
        self.assertIn(
            "P1E-020_TRACE_DECISION_OR_BUDGET_HASH_MISMATCH",
            receipt["reason_codes"],
        )

    def test_historical_resource_trace_bytes_have_zero_drift(self):
        pins = {
            "tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/"
            "resource_trace.jsonl": (
                "2c3e5da8692070fb44e594666e337bcca6c4d3d09"
                "ad8662eabcbd1ee45c92318"
            ),
            "tests/fixtures/TWIN-SUPPLY-CHAIN-002/expected/"
            "resource_trace.jsonl": (
                "102f43c3210208101f393580b6d4afe7573f9be0e0"
                "81edabb97d28f19b9efee5"
            ),
        }
        for path, expected in pins.items():
            with self.subTest(path=path):
                self.assertEqual(expected, file_sha256(ROOT / path))

    def test_binding_is_readonly_and_has_no_authority(self):
        serialized = json.dumps(
            {
                "decision": self.decision,
                "trace_row": self.trace_row,
                "fixture_authority_ceiling": self.fixture[
                    "authority_ceiling"
                ],
            }
        )
        self.assertEqual(
            0, self.trace_row["counts"]["execution_attempt_count"]
        )
        self.assertEqual(
            0, self.trace_row["counts"]["primitive_operation_count"]
        )
        self.assertTrue(
            all(
                value is False
                for value in self.decision["authority_ceiling"].values()
            )
        )
        self.assertTrue(
            all(
                value is False
                for value in self.fixture["authority_ceiling"].values()
            )
        )
        self.assertFalse(planner.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(planner.ACTION_EXECUTION_ENABLED)
        self.assertFalse(planner.SYSTEM_STATE_AUTHORITY)
        self.assertFalse(planner.STOP_AUTHORITY)
        self.assertNotIn("CERTIFIED_STOP", serialized)
        self.assertIn("must not be inferred", planner.HARD_BAN)


if __name__ == "__main__":
    unittest.main()
