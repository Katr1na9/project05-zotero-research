from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
CONFIG_DIR = ROOT / "configs"

POLICY_SCHEMA_PATH = (
    SCHEMA_DIR / "part-b-closed-loop-evaluation-policy.schema.json"
)
EPISODE_SCHEMA_PATH = (
    SCHEMA_DIR / "part-b-closed-loop-episode.schema.json"
)
FEEDBACK_SCHEMA_PATH = (
    SCHEMA_DIR / "part-b-closed-loop-feedback-envelope.schema.json"
)
PREREGISTRATION_SCHEMA_PATH = (
    SCHEMA_DIR / "part-b-closed-loop-preregistration.schema.json"
)

POLICY_PATH = (
    CONFIG_DIR / "part-b-closed-loop-evaluation-policy-v0.8.yaml"
)
EPISODE_PATH = (
    CONFIG_DIR / "part-b-closed-loop-episode-example-v0.8.yaml"
)
FEEDBACK_PATH = (
    CONFIG_DIR / "part-b-closed-loop-feedback-example-v0.8.yaml"
)
PREREGISTRATION_PATH = (
    CONFIG_DIR / "part-b-closed-loop-preregistration-v0.8.yaml"
)

B2_CATALOG_HASH = (
    "sha256:200f0ccd89525bcbda89ea77101cdcab7fda675888938ee106e389a1a8beeab5"
)
B2_TV_POLICY_HASH = (
    "sha256:b25ed05fdbd9780c1d0de1889e7651220e8a2fc9ce6a86fcdf4720926a31d3e8"
)
B2_DECISION_HASH = (
    "sha256:1a9668ef8c968c968e14587778d261b023dff60a0234e4e67251051ec07e5919"
)
B3_POLICY_HASH = (
    "sha256:c64865166be067da37a6f4f5d745ce8dc0421dc342d88589c9bbce6142eb3278"
)
B4_ISOLATION_HASH = (
    "sha256:8e95dd5ae4ae87140de815101b26592e97432dbf64541474b8bcdacb386b5c1f"
)
B5_PUBLIC_STATE_HASH = (
    "sha256:42efd17661a1335f3c84c2c4efbea4de8107087d099dc987a902d20ded50deae"
)
B5_DECISION_HASH = (
    "sha256:144cd24c0d6e3906ee31d25cdcc629f20901648d58204ee030f397daca23da6d"
)
B5_INTERFACE_POLICY_HASH = (
    "sha256:b0c9f9971d13efcfeabb39f829592b9502831ba1b94e8de54e3941ba7dd1c343"
)
B5_BOUNDED_EVALUATION_HASH = (
    "sha256:9c1cae4643b95f7e2c87b6398cd096db1836ca3533cca67a1842dd037ec66858"
)

FORBIDDEN_EPISODE_FIELDS = (
    "oracle_label",
    "hidden_ground_truth",
    "holdout_label",
    "evaluator_world",
    "realized_action_outcome",
    "action_payload",
    "certificate",
    "system_status",
)
FORBIDDEN_FEEDBACK_FIELDS = (
    "oracle_label",
    "hidden_ground_truth",
    "holdout_label",
    "evaluator_world",
    "action_payload",
    "raw_observation_payload",
    "claim_ir",
    "modality",
    "truth_status",
    "epistemic_role",
    "certification_authority",
    "certificate",
    "system_status",
)


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B6 artifact: {path.relative_to(ROOT)}"
        )
    return path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(require_file(path).read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(require_file(path).read_text(encoding="utf-8"))


def validate(instance: dict[str, object], schema: dict[str, object]) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


def step_conforms(step: dict[str, object]) -> bool:
    public_state = step["public_state_reference"]
    decision = step["decision_reference"]
    selected = decision["selected_action_id"]
    if decision["public_state_hash"] != public_state["public_state_hash"]:
        return False
    if selected is None:
        return decision["decision_status"] == "NO_ACTION"
    return (
        decision["decision_status"] == "SELECT_ACTION"
        and selected in public_state["feasible_action_ids"]
    )


class PartBB6ClosedLoopEvaluationTests(unittest.TestCase):
    def test_red_13_episode_domain_is_finite_unique_and_ordered(self) -> None:
        """RED-13: a contract episode is finite and canonically ordered."""
        schema = load_json(EPISODE_SCHEMA_PATH)
        episode = load_yaml(EPISODE_PATH)
        self.assertEqual(validate(episode, schema), [])
        steps = episode["steps"]
        self.assertGreaterEqual(len(steps), 1)
        self.assertEqual(len(steps), episode["finite_step_count"])
        indices = [step["step_index"] for step in steps]
        self.assertEqual(indices, list(range(len(steps))))
        self.assertEqual(len(indices), len(set(indices)))
        self.assertEqual(
            episode["sequence"],
            [
                "PUBLIC_STATE_REFERENCE",
                "ACTION_ID_DECISION_REFERENCE",
                "FEEDBACK_ENVELOPE_REFERENCE",
            ],
        )

    def test_red_14_episode_reads_only_b5_public_state(self) -> None:
        """RED-14: no hidden evaluator state enters the Planner input."""
        schema = load_json(EPISODE_SCHEMA_PATH)
        episode = load_yaml(EPISODE_PATH)
        policy = load_yaml(POLICY_PATH)
        self.assertEqual(
            policy["bindings"]["b5_planner_public_state_example_hash"],
            B5_PUBLIC_STATE_HASH,
        )
        self.assertEqual(
            policy["bindings"]["b5_planner_interface_policy_hash"],
            B5_INTERFACE_POLICY_HASH,
        )
        for step in episode["steps"]:
            self.assertEqual(
                step["public_state_reference"]["public_state_hash"],
                B5_PUBLIC_STATE_HASH,
            )
        for field in FORBIDDEN_EPISODE_FIELDS:
            invalid = deepcopy(episode)
            invalid[field] = "FORBIDDEN"
            with self.subTest(field=field):
                self.assertTrue(validate(invalid, schema))

    def test_red_15_decision_is_action_id_only_and_state_bound(self) -> None:
        """RED-15: decisions carry no action payload or side channel."""
        episode = load_yaml(EPISODE_PATH)
        policy = load_yaml(POLICY_PATH)
        self.assertEqual(
            policy["bindings"]["b5_planner_decision_example_hash"],
            B5_DECISION_HASH,
        )
        for step in episode["steps"]:
            decision = step["decision_reference"]
            self.assertEqual(
                set(decision),
                {
                    "decision_id",
                    "decision_hash",
                    "public_state_hash",
                    "decision_status",
                    "selected_action_id",
                },
            )
            self.assertEqual(decision["decision_hash"], B5_DECISION_HASH)
            self.assertTrue(step_conforms(step))

    def test_red_16_unknown_action_or_stale_state_fails_closed(self) -> None:
        """RED-16: action membership and state identity are mandatory."""
        episode = load_yaml(EPISODE_PATH)
        policy = load_yaml(POLICY_PATH)
        enforcement = policy["decision_enforcement"]
        self.assertEqual(
            enforcement["unknown_action_behavior"],
            "FAIL_CLOSED_ACTION_NOT_FEASIBLE",
        )
        self.assertEqual(
            enforcement["state_hash_mismatch_behavior"],
            "FAIL_CLOSED_STATE_BINDING_MISMATCH",
        )

        unknown = deepcopy(episode["steps"][0])
        unknown["decision_reference"][
            "selected_action_id"
        ] = "ACTION-NOT-IN-PUBLIC-STATE"
        self.assertFalse(step_conforms(unknown))

        stale = deepcopy(episode["steps"][0])
        stale["decision_reference"]["public_state_hash"] = (
            "sha256:" + ("0" * 64)
        )
        self.assertFalse(step_conforms(stale))

    def test_red_17_feedback_is_closed_and_cross_bound(self) -> None:
        """RED-17: feedback references one exact case, step and decision."""
        schema = load_json(FEEDBACK_SCHEMA_PATH)
        feedback = load_yaml(FEEDBACK_PATH)
        episode = load_yaml(EPISODE_PATH)
        self.assertEqual(validate(feedback, schema), [])
        step = episode["steps"][feedback["step_index"]]
        self.assertEqual(feedback["case_id"], episode["case_id"])
        self.assertEqual(feedback["episode_id"], episode["episode_id"])
        self.assertEqual(
            feedback["public_state_hash"],
            step["public_state_reference"]["public_state_hash"],
        )
        self.assertEqual(
            feedback["decision_hash"],
            step["decision_reference"]["decision_hash"],
        )
        self.assertEqual(
            feedback["selected_action_id"],
            step["decision_reference"]["selected_action_id"],
        )
        self.assertEqual(
            step["feedback_reference"]["feedback_hash"],
            feedback["hash"],
        )

    def test_red_18_feedback_cannot_launder_payload_or_authority(self) -> None:
        """RED-18: feedback is a reference envelope, not Claim IR."""
        schema = load_json(FEEDBACK_SCHEMA_PATH)
        feedback = load_yaml(FEEDBACK_PATH)
        self.assertEqual(
            feedback["observation_reference"]["source"],
            "EVALUATOR_SUPPLIED_REFERENCE_ONLY",
        )
        self.assertEqual(
            feedback["observation_reference"]["availability"],
            "NOT_EXECUTED_CONTRACT_EXAMPLE",
        )
        self.assertTrue(
            feedback["observation_reference"]["pointer"].startswith(
                "contract://"
            )
        )
        self.assertIs(feedback["claim_ir_ownership"], False)
        self.assertIs(feedback["modality_change_allowed"], False)
        for field in FORBIDDEN_FEEDBACK_FIELDS:
            invalid = deepcopy(feedback)
            invalid[field] = "FORBIDDEN"
            with self.subTest(field=field):
                self.assertTrue(validate(invalid, schema))

    def test_red_19_b2_is_referenced_but_never_sampled(self) -> None:
        """RED-19: B6 cannot execute B2 contract examples."""
        policy = load_yaml(POLICY_PATH)
        stochastic = policy["stochastic_observation_boundary"]
        self.assertEqual(
            stochastic["catalog_hash"],
            B2_CATALOG_HASH,
        )
        self.assertEqual(
            stochastic["tv_policy_hash"],
            B2_TV_POLICY_HASH,
        )
        self.assertEqual(
            stochastic["world_pair_delta_decision_hash"],
            B2_DECISION_HASH,
        )
        self.assertEqual(
            stochastic["input_semantics"],
            "EVALUATOR_SUPPLIED_OBSERVATION_REFERENCE_ONLY",
        )
        self.assertIs(stochastic["sampling_authority"], False)
        self.assertIs(stochastic["distribution_estimation_authority"], False)
        self.assertIs(stochastic["catalog_examples_executable"], False)

    def test_red_20_b3_cost_stays_unscalarized_and_infeasibility_separate(
        self,
    ) -> None:
        """RED-20: B6 preserves the eight-dimensional cost boundary."""
        policy = load_yaml(POLICY_PATH)
        cost = policy["cost_boundary"]
        self.assertEqual(
            cost["instrumentation_policy_hash"],
            B3_POLICY_HASH,
        )
        self.assertEqual(
            cost["representation"],
            "B3_EIGHT_DIMENSION_VECTOR_ONLY",
        )
        self.assertIs(cost["scalarization_enabled"], False)
        self.assertEqual(
            cost["missing_measurement"],
            "UNKNOWN_NOT_ZERO",
        )
        self.assertIs(cost["infeasible_as_high_cost"], False)
        self.assertEqual(
            cost["infeasibility_semantics"],
            "SEPARATE_NO_ACTION",
        )

    def test_red_21_unknown_failures_and_partition_feedback_stay_separate(
        self,
    ) -> None:
        """RED-21: unknown is not ranked and feedback cannot leak."""
        policy = load_yaml(POLICY_PATH)
        failures = policy["failure_semantics"]
        self.assertEqual(failures["timeout"], "UNKNOWN_NO_RANK")
        self.assertEqual(
            failures["resource_exhaustion"],
            "UNKNOWN_NO_RANK",
        )
        self.assertEqual(failures["infeasible"], "SEPARATE_NO_ACTION")
        self.assertEqual(failures["unknown"], "FAIL_CLOSED_NO_RANK")
        self.assertEqual(
            policy["bindings"]["b5_bounded_evaluation_hash"],
            B5_BOUNDED_EVALUATION_HASH,
        )

        feedback = policy["feedback_isolation"]
        self.assertEqual(
            feedback["b4_isolation_policy_hash"],
            B4_ISOLATION_HASH,
        )
        self.assertIs(feedback["evaluation_to_train"], False)
        self.assertIs(feedback["evaluation_to_tune"], False)
        self.assertIs(feedback["holdout_to_any_model"], False)
        self.assertIs(feedback["historical_result_access"], False)

    def test_red_22_b6_proves_contract_consistency_only(self) -> None:
        """RED-22: no execution, rank, superiority, certificate or STOP."""
        policy = load_yaml(POLICY_PATH)
        preregistration = load_yaml(PREREGISTRATION_PATH)
        preregistration_schema = load_json(PREREGISTRATION_SCHEMA_PATH)
        self.assertEqual(
            validate(preregistration, preregistration_schema),
            [],
        )
        claims = policy["claim_boundary"]
        self.assertEqual(
            claims["evidence_level"],
            "CONTRACT_CONSISTENCY_ONLY",
        )
        for field in (
            "implementation_validation",
            "evaluation_execution_authority",
            "ranking_authority",
            "performance_validity",
            "superiority_claim",
            "certificate_authority",
            "system_status_authority",
            "certified_stop_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(claims[field], False)
        self.assertEqual(
            preregistration["allowed_contract_metrics"],
            [
                "INTERFACE_CONFORMANCE",
                "FEEDBACK_BOUNDARY_CONFORMANCE",
                "FAILURE_CHANNEL_COUNTS",
                "UNSCALARIZED_RESOURCE_VECTOR_SHAPE",
            ],
        )


if __name__ == "__main__":
    unittest.main()
