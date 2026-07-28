from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from src.planner import deterministic_depth1 as depth1
from src.planner import twin_p10_readonly_wiring as wiring


ROOT = Path(__file__).resolve().parents[2]
_DEFAULT = object()
FIXTURE_PATH = (
    ROOT
    / "tests"
    / "unit"
    / "fixtures"
    / "kernel_a17_p1e_twin_p10_readonly_wiring_v0.1.json"
)


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def rehash_caller_input(value):
    value["caller_input_hash"] = depth1.canonical_hash_without_field(
        value, "caller_input_hash"
    )
    return value


class KernelA17P1eTwinP10ReadonlyWiringTests(unittest.TestCase):
    def setUp(self):
        self.fixture = load_fixture()
        self.authority = deepcopy(self.fixture["test_only_authority"])
        self.none_input = deepcopy(self.fixture["caller_inputs"]["none"])

    def call(self, caller_input=_DEFAULT, authority=_DEFAULT):
        return wiring.evaluate_twin_p10_fixed_case_for_depth1_candidacy(
            self.none_input if caller_input is _DEFAULT else caller_input,
            test_only_authority=(
                self.authority if authority is _DEFAULT else authority
            ),
        )

    def test_exact_request_maps_to_unmodified_direct_gate_decision(self):
        expected_request = self.fixture["expected_request"]
        expected_decision = self.fixture["expected_decision"]
        original_gate = depth1.evaluate_depth1_planner_request
        input_before = deepcopy(self.none_input)
        authority_before = deepcopy(self.authority)

        with patch.object(
            wiring.depth1,
            "evaluate_depth1_planner_request",
            wraps=original_gate,
        ) as gate:
            result = self.call()

        self.assertEqual(1, gate.call_count)
        request = gate.call_args.args[0]
        direct = original_gate(deepcopy(request))
        self.assertEqual(set(request), depth1.REQUEST_FIELDS)
        self.assertEqual(expected_request["field_count"], len(request))
        self.assertEqual(
            expected_request["field_names"], sorted(request)
        )
        self.assertEqual(
            expected_request["request_hash"], request["request_hash"]
        )
        self.assertEqual(
            expected_request["world_ids"],
            request["finite_domain_binding"]["current_u_world_ids"],
        )
        self.assertEqual(
            expected_request["compiled_legal_worlds_hash"],
            request["finite_domain_binding"]["compiled_legal_worlds_hash"],
        )
        self.assertEqual(
            expected_request["allowed_action_ids"],
            request["p4_selection_binding"]["allowed_action_ids"],
        )
        self.assertEqual(
            expected_request["forbidden_action_ids"],
            request["p4_selection_binding"]["forbidden_action_ids"],
        )
        self.assertEqual(
            expected_request["partition_hashes"],
            [
                row["partition_hash"]
                for row in request["deterministic_outcome_partitions"]
            ],
        )
        self.assertEqual(
            expected_request["resource_budget_hash"],
            request["resource_budget_declaration"]["budget_hash"],
        )
        self.assertEqual(set(result), wiring.RESULT_FIELDS)
        self.assertEqual(8, len(result))
        self.assertEqual(
            wiring.STATUS_SIDECAR_NO_TRACE, result["wiring_status"]
        )
        self.assertEqual([], result["reason_codes"])
        self.assertEqual(direct, result["decision_record"])
        self.assertEqual(
            expected_decision["field_count"],
            len(result["decision_record"]),
        )
        self.assertIsNone(result["resource_trace_binding_receipt"])
        self.assertEqual(input_before, self.none_input)
        self.assertEqual(authority_before, self.authority)

    def test_select_action_hashes_tie_break_and_authority_ceiling(self):
        expected = self.fixture["expected_decision"]
        result = self.call()
        decision = result["decision_record"]

        self.assertEqual(expected["decision"], decision["decision"])
        self.assertEqual(
            expected["selected_action_id"], decision["selected_action_id"]
        )
        self.assertEqual(
            expected["tied_action_ids"],
            decision["tie_break"]["tied_action_ids"],
        )
        self.assertEqual(
            expected["tie_break_rule"], decision["tie_break"]["rule_id"]
        )
        self.assertEqual(expected["request_hash"], decision["request_hash"])
        self.assertEqual(expected["record_hash"], decision["record_hash"])
        self.assertEqual(
            expected["attempt_id"],
            decision["resource_trace_binding"]["attempt_id"],
        )
        self.assertIsNone(decision["probability_model"])
        self.assertIsNone(decision["planning_confidence"])
        self.assertTrue(
            all(value is False for value in decision["authority_ceiling"].values())
        )
        self.assertTrue(
            all(value is False for value in result["authority_ceiling"].values())
        )
        self.assertFalse(wiring.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(wiring.ACTION_EXECUTION_ENABLED)
        self.assertFalse(wiring.SYSTEM_STATE_AUTHORITY)
        self.assertFalse(wiring.STOP_AUTHORITY)
        self.assertIn("must not be inferred", wiring.HARD_BAN)

    def test_identical_input_produces_identical_sidecar(self):
        first = self.call()
        second = self.call(
            deepcopy(self.none_input), deepcopy(self.authority)
        )
        self.assertEqual(first, second)
        self.assertEqual(
            first["decision_record"]["record_hash"],
            second["decision_record"]["record_hash"],
        )

    def test_authority_fails_before_gate(self):
        invalid_authorities = {
            "missing": None,
            "empty": {},
            "extra": {**self.authority, "unexpected": True},
            "wrong_sha": {
                **self.authority,
                "owner_go_sha256": "0" * 64,
            },
            "registration_true": {
                **self.authority,
                "production_registration_enabled": True,
            },
            "integer_false": {
                **self.authority,
                "production_registration_enabled": 0,
            },
        }
        for name, authority in invalid_authorities.items():
            with self.subTest(name=name), patch.object(
                wiring.depth1, "evaluate_depth1_planner_request"
            ) as gate:
                result = self.call(authority=authority)
                gate.assert_not_called()
                self.assertEqual(
                    wiring.STATUS_DENY_AUTHORITY,
                    result["wiring_status"],
                )
                self.assertEqual(
                    [wiring.REASON_AUTHORITY], result["reason_codes"]
                )
                self.assertIsNone(result["decision_record"])
                self.assertIsNone(
                    result["resource_trace_binding_receipt"]
                )

    def test_closed_world_negative_matrix_fails_before_gate(self):
        cases = {}

        wrong_case = deepcopy(self.none_input)
        wrong_case["fixed_case_id"] = "TWIN-*"
        cases["wrong_case_or_wildcard"] = rehash_caller_input(wrong_case)

        observed = deepcopy(self.none_input)
        observed["observed_value"] = "H1"
        cases["observed_value_laundering"] = observed

        hidden = deepcopy(self.none_input)
        hidden["actual_world_id"] = "W-SUPPORT-H1"
        cases["hidden_oracle"] = hidden

        expanded = deepcopy(self.none_input)
        expanded["current_u_world_ids"] = [
            "W-ALTERNATIVE-H3",
            "W-SUPPORT-H1",
            "W-NEW",
        ]
        cases["current_u_expansion"] = expanded

        stop = deepcopy(self.none_input)
        stop["requested_result_scope"] = "CERTIFIED_STOP"
        cases["authority_or_stop"] = rehash_caller_input(stop)

        stale = deepcopy(self.none_input)
        stale["caller_input_hash"] = "sha256:" + "0" * 64
        cases["stale_hash"] = stale

        wrong_mode = deepcopy(self.none_input)
        wrong_mode["resource_trace_binding_mode"] = "*"
        cases["wildcard_mode"] = rehash_caller_input(wrong_mode)

        mismatched_attempt = deepcopy(self.none_input)
        mismatched_attempt["historical_resource_trace_attempt_id"] = (
            "ATTEMPT-001"
        )
        cases["attempt_in_none_mode"] = rehash_caller_input(
            mismatched_attempt
        )

        for name, caller_input in cases.items():
            with self.subTest(name=name), patch.object(
                wiring.depth1, "evaluate_depth1_planner_request"
            ) as gate:
                result = self.call(caller_input=caller_input)
                gate.assert_not_called()
                self.assertEqual(
                    wiring.STATUS_DENY_INPUT, result["wiring_status"]
                )
                self.assertEqual(
                    [wiring.REASON_INPUT], result["reason_codes"]
                )
                self.assertIsNone(result["decision_record"])

    def test_pin_mismatch_fails_before_gate(self):
        with patch.dict(
            wiring._EXPECTED_FILE_SHA256,
            {wiring._GAMMA_PATH: "0" * 64},
            clear=False,
        ), patch.object(
            wiring.depth1, "evaluate_depth1_planner_request"
        ) as gate:
            result = self.call()

        gate.assert_not_called()
        self.assertEqual(wiring.STATUS_DENY_INPUT, result["wiring_status"])
        self.assertEqual([wiring.REASON_INPUT], result["reason_codes"])
        self.assertIsNone(result["decision_record"])

    def test_observed_action_rows_are_not_parsed_as_partition_truth(self):
        original_load_jsonl = wiring._load_jsonl
        parsed_paths = []

        def recording_load_jsonl(path):
            parsed_paths.append(path)
            return original_load_jsonl(path)

        with patch.object(
            wiring, "_load_jsonl", side_effect=recording_load_jsonl
        ):
            result = self.call()

        self.assertEqual(
            wiring.STATUS_SIDECAR_NO_TRACE, result["wiring_status"]
        )
        self.assertIn(wiring._CASE_EVIDENCE_PATH, parsed_paths)
        self.assertNotIn(
            "tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/"
            "action_observations.jsonl",
            parsed_paths,
        )
        serialized = json.dumps(result["decision_record"])
        self.assertNotIn('"observed_value"', serialized)
        self.assertNotIn('"actual_world_id"', serialized)
        self.assertNotIn('"planning_confidence": {}', serialized)

    def test_nonselect_gate_decision_is_returned_unmodified_without_receipt(self):
        denied = depth1.evaluate_depth1_planner_request(
            {"requested_decision_scope": "CERTIFIED_STOP"}
        )
        self.assertEqual(depth1.DENY, denied["decision"])

        with patch.object(
            wiring.depth1,
            "evaluate_depth1_planner_request",
            return_value=denied,
        ):
            result = self.call()

        self.assertEqual(
            wiring.STATUS_D1_NONSELECT, result["wiring_status"]
        )
        self.assertEqual(denied, result["decision_record"])
        self.assertEqual(denied["reason_codes"], result["reason_codes"])
        self.assertIsNone(result["resource_trace_binding_receipt"])


if __name__ == "__main__":
    unittest.main()
