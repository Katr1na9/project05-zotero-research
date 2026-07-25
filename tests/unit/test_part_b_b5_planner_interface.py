from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
CONFIG_DIR = ROOT / "configs"

PUBLIC_STATE_SCHEMA_PATH = (
    SCHEMA_DIR / "part-b-planner-public-state.schema.json"
)
DECISION_SCHEMA_PATH = SCHEMA_DIR / "part-b-planner-decision.schema.json"
PUBLIC_STATE_PATH = (
    CONFIG_DIR / "part-b-planner-public-state-example-v0.8.yaml"
)
DECISION_PATH = (
    CONFIG_DIR / "part-b-planner-decision-example-v0.8.yaml"
)
POLICY_PATH = CONFIG_DIR / "part-b-planner-interface-policy-v0.8.yaml"
BOUNDED_EVALUATION_PATH = (
    CONFIG_DIR / "part-b-bounded-evaluation-v0.8.yaml"
)

FORBIDDEN_PUBLIC_STATE_FIELDS = (
    "oracle_label",
    "hidden_ground_truth",
    "holdout_label",
    "realized_action_outcome",
    "evaluator_world",
    "certificate",
    "system_status",
)
FORBIDDEN_DECISION_FIELDS = (
    "action_payload",
    "predicted_world",
    "confidence",
    "oracle_label",
    "hidden_ground_truth",
    "certificate",
    "system_status",
)
ORDERED_PUBLIC_ID_FIELDS = (
    "public_claim_ids",
    "admitted_evidence_ids",
    "unresolved_predicate_ids",
    "feasible_action_ids",
)


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B5 artifact: {path.relative_to(ROOT)}"
        )
    return path


def load_json(path: Path) -> dict[str, object]:
    import json

    return json.loads(require_file(path).read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(require_file(path).read_text(encoding="utf-8"))


def validate(instance: dict[str, object], schema: dict[str, object]) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


def decision_conforms(
    public_state: dict[str, object],
    decision: dict[str, object],
) -> bool:
    if decision["public_state_hash"] != public_state["hash"]:
        return False
    selected = decision["selected_action_id"]
    if selected is None:
        return decision["decision_status"] != "SELECT_ACTION"
    return (
        decision["decision_status"] == "SELECT_ACTION"
        and selected in public_state["feasible_action_ids"]
    )


class PartBB5PlannerInterfaceTests(unittest.TestCase):
    def test_red_03_public_state_rejects_every_nonpublic_field(self) -> None:
        """RED-03: oracle, hidden, holdout and outcome state is forbidden."""
        schema = load_json(PUBLIC_STATE_SCHEMA_PATH)
        public_state = load_yaml(PUBLIC_STATE_PATH)
        self.assertEqual(validate(public_state, schema), [])

        for field in FORBIDDEN_PUBLIC_STATE_FIELDS:
            invalid = deepcopy(public_state)
            invalid[field] = "FORBIDDEN"
            with self.subTest(field=field):
                self.assertTrue(validate(invalid, schema))

    def test_red_04_public_state_domains_are_finite_unique_and_canonical(self) -> None:
        """RED-04: all public ID domains are finite canonical lists."""
        public_state = load_yaml(PUBLIC_STATE_PATH)
        self.assertGreaterEqual(public_state["decision_step"], 0)
        for field in ORDERED_PUBLIC_ID_FIELDS:
            values = public_state[field]
            with self.subTest(field=field):
                self.assertIsInstance(values, list)
                self.assertEqual(values, sorted(set(values)))

        self.assertGreaterEqual(len(public_state["feasible_action_ids"]), 1)
        for key, value in public_state["remaining_resource_bounds"].items():
            with self.subTest(resource_bound=key):
                self.assertIs(type(value), int)
                self.assertGreater(value, 0)
        self.assertEqual(
            public_state["hash"],
            canonical_document_hash(public_state),
        )

    def test_red_05_decision_is_action_id_only_and_state_bound(self) -> None:
        """RED-05: only a feasible action ID or explicit null may return."""
        schema = load_json(DECISION_SCHEMA_PATH)
        public_state = load_yaml(PUBLIC_STATE_PATH)
        decision = load_yaml(DECISION_PATH)
        policy = load_yaml(POLICY_PATH)

        self.assertEqual(validate(decision, schema), [])
        self.assertTrue(decision_conforms(public_state, decision))
        self.assertEqual(
            policy["decision_enforcement"]["unknown_action_behavior"],
            "FAIL_CLOSED_ACTION_NOT_FEASIBLE",
        )
        self.assertEqual(
            policy["decision_enforcement"]["state_hash_mismatch_behavior"],
            "FAIL_CLOSED_STATE_BINDING_MISMATCH",
        )

        unknown = deepcopy(decision)
        unknown["selected_action_id"] = "ACTION-NOT-IN-PUBLIC-STATE"
        self.assertFalse(decision_conforms(public_state, unknown))

        stale = deepcopy(decision)
        stale["public_state_hash"] = "sha256:" + ("0" * 64)
        self.assertFalse(decision_conforms(public_state, stale))

        no_action = deepcopy(decision)
        no_action["decision_status"] = "NO_ACTION"
        no_action["selected_action_id"] = None
        no_action["reason_code"] = "B5-DECISION-001_NO_ACTION"
        no_action["hash"] = canonical_document_hash(no_action)
        self.assertEqual(validate(no_action, schema), [])
        self.assertTrue(decision_conforms(public_state, no_action))

    def test_red_06_decision_rejects_payloads_predictions_and_stop(self) -> None:
        """RED-06: output has no payload, side channel or authority."""
        schema = load_json(DECISION_SCHEMA_PATH)
        decision = load_yaml(DECISION_PATH)

        for field in FORBIDDEN_DECISION_FIELDS:
            invalid = deepcopy(decision)
            invalid[field] = "FORBIDDEN"
            with self.subTest(field=field):
                self.assertTrue(validate(invalid, schema))

        for value in decision.values():
            self.assertNotEqual(value, "CERTIFIED_STOP")

    def test_red_11_bounded_evaluation_has_positive_finite_caps(self) -> None:
        """RED-11: every future evaluation envelope is explicitly bounded."""
        evaluation = load_yaml(BOUNDED_EVALUATION_PATH)
        self.assertEqual(
            evaluation["bound_semantics"],
            "FINITE_PREDECLARED_CONFORMANCE_ENVELOPE",
        )
        expected_bounds = {
            "max_public_state_bytes",
            "max_feasible_action_ids",
            "max_decision_wall_ms",
            "max_decision_cpu_ms",
            "max_memory_bytes",
            "max_decisions_per_case",
        }
        self.assertEqual(set(evaluation["bounds"]), expected_bounds)
        for name, value in evaluation["bounds"].items():
            with self.subTest(bound=name):
                self.assertIs(type(value), int)
                self.assertGreater(value, 0)
        self.assertIs(evaluation["auto_retry"], False)
        self.assertIs(evaluation["fallback_to_hidden_state"], False)
        self.assertEqual(
            evaluation["failure_semantics"]["timeout"],
            "UNKNOWN_NO_RANK",
        )
        self.assertEqual(
            evaluation["failure_semantics"]["resource_exhaustion"],
            "UNKNOWN_NO_RANK",
        )

    def test_red_12_infeasible_is_separate_from_cost(self) -> None:
        """RED-12: infeasibility can never be encoded as high cost."""
        evaluation = load_yaml(BOUNDED_EVALUATION_PATH)
        failures = evaluation["failure_semantics"]
        self.assertEqual(failures["infeasible"], "SEPARATE_NO_ACTION")
        self.assertEqual(failures["unknown"], "FAIL_CLOSED_NO_RANK")
        self.assertIs(
            evaluation["cost_semantics"]["infeasible_as_high_cost"],
            False,
        )
        self.assertEqual(
            evaluation["cost_semantics"]["missing_measurement"],
            "UNKNOWN_NOT_ZERO",
        )

    def test_red_13_cost_stays_vector_valued_without_superiority(self) -> None:
        """RED-13: B3 trace may be referenced but never scalarized."""
        evaluation = load_yaml(BOUNDED_EVALUATION_PATH)
        cost = evaluation["cost_semantics"]
        claims = evaluation["claim_boundary"]
        self.assertEqual(
            cost["representation"],
            "B3_EIGHT_DIMENSION_VECTOR_ONLY",
        )
        self.assertIs(cost["scalarization_enabled"], False)
        self.assertIs(claims["evaluation_execution_authority"], False)
        self.assertIs(claims["performance_claim_authority"], False)
        self.assertIs(claims["superiority_claim_authority"], False)
        self.assertEqual(
            evaluation["allowed_contract_metrics"],
            [
                "INTERFACE_CONFORMANCE",
                "FAILURE_CHANNEL_COUNTS",
                "UNSCALARIZED_RESOURCE_VECTOR_SHAPE",
            ],
        )

    def test_red_16_evaluation_isolation_and_history_bans_remain(self) -> None:
        """RED-16: B5 cannot leak evaluation or historical outcomes."""
        evaluation = load_yaml(BOUNDED_EVALUATION_PATH)
        isolation = evaluation["isolation_binding"]
        self.assertEqual(
            isolation["partitions"],
            ["TRAIN", "TUNE", "EVALUATION", "HOLDOUT"],
        )
        self.assertIs(isolation["evaluation_feedback_to_train"], False)
        self.assertIs(isolation["holdout_visible_before_final_freeze"], False)
        self.assertIs(isolation["historical_result_access"], False)
        self.assertEqual(
            isolation["forbidden_path_prefixes"],
            ["09-experiments/"],
        )


if __name__ == "__main__":
    unittest.main()
