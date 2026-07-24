from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
CONFIG_DIR = ROOT / "configs"

SCHEMA_PATHS = {
    "policy": SCHEMA_DIR / "part-b-holdout-analysis-policy.schema.json",
    "preregistration": (
        SCHEMA_DIR / "part-b-holdout-preregistration.schema.json"
    ),
    "analysis_plan": (
        SCHEMA_DIR / "part-b-statistical-analysis-plan.schema.json"
    ),
    "analysis_envelope": (
        SCHEMA_DIR / "part-b-holdout-analysis-envelope.schema.json"
    ),
}
CONFIG_PATHS = {
    "policy": CONFIG_DIR / "part-b-holdout-analysis-policy-v0.8.yaml",
    "preregistration": (
        CONFIG_DIR / "part-b-holdout-preregistration-v0.8.yaml"
    ),
    "analysis_plan": (
        CONFIG_DIR / "part-b-statistical-analysis-plan-example-v0.8.yaml"
    ),
    "analysis_envelope": (
        CONFIG_DIR / "part-b-holdout-analysis-envelope-example-v0.8.yaml"
    ),
    "manifest": CONFIG_DIR / "part-b-b8-manifest-v0.8.yaml",
}

B3_POLICY_HASH = (
    "sha256:c64865166be067da37a6f4f5d745ce8dc0421dc342d88589c9bbce6142eb3278"
)
B4_PREREGISTRATION_HASH = (
    "sha256:c51ab64588441855a7ff8413e32695e4b168d6d2a2089674f2cdcd691959906d"
)
B4_ISOLATION_HASH = (
    "sha256:8e95dd5ae4ae87140de815101b26592e97432dbf64541474b8bcdacb386b5c1f"
)
B7_MANIFEST_HASH = (
    "sha256:28179580dc0e8c4dbc6f1a6cb1d5f0d4939a3ae7466c078e60f20fb16fffac49"
)
COST_DIMENSIONS = [
    "T_human",
    "T_wall",
    "T_CPU",
    "M_byte_sec",
    "D_scan",
    "N_record",
    "C_money",
    "T_auth",
]


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B8 artifact: {path.relative_to(ROOT)}"
        )
    return path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(require_file(path).read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(require_file(path).read_text(encoding="utf-8"))


def validation_errors(
    instance: dict[str, object], schema: dict[str, object]
) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


class PartBB8HoldoutAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        """Keep RED counting one missing-artifact failure per test method."""
        for path in (
            *SCHEMA_PATHS.values(),
            *CONFIG_PATHS.values(),
        ):
            require_file(path)

    def test_red_13_analysis_registry_is_finite_unique_and_holdout_only(
        self,
    ) -> None:
        """RED-13: B8 registers one finite, versioned HOLDOUT analysis domain."""
        preregistration = load_yaml(CONFIG_PATHS["preregistration"])
        self.assertEqual(
            preregistration["status"],
            "B8_CONTRACT_ONLY",
        )
        self.assertEqual(
            preregistration["authorized_slice"],
            "B8_HOLDOUT_ANALYSIS",
        )
        self.assertEqual(preregistration["partition_id"], "HOLDOUT")
        self.assertRegex(
            preregistration["preregistration_version"],
            r"^0\.8\.\d+$",
        )
        registry = preregistration["analysis_registry"]
        analysis_ids = registry["analysis_ids"]
        self.assertGreater(len(analysis_ids), 0)
        self.assertEqual(len(analysis_ids), len(set(analysis_ids)))
        self.assertEqual(
            preregistration["analysis_id"],
            analysis_ids[0],
        )
        self.assertIs(registry["finite_complete"], True)
        self.assertIs(registry["dynamic_analysis_addition"], False)

    def test_red_14_split_commitment_freezes_before_any_outcome_access(
        self,
    ) -> None:
        """RED-14: split identity is committed while labels/results stay sealed."""
        preregistration = load_yaml(CONFIG_PATHS["preregistration"])
        commitment = preregistration["split_commitment"]
        self.assertEqual(commitment["partition_id"], "HOLDOUT")
        self.assertRegex(
            commitment["split_fingerprint"],
            r"^sha256:[0-9a-f]{64}$",
        )
        self.assertIs(commitment["committed_before_label_access"], True)
        self.assertIs(commitment["committed_before_result_access"], True)
        self.assertIs(commitment["labels_included"], False)
        self.assertIs(commitment["results_included"], False)
        self.assertEqual(
            commitment["disclosure"],
            "IDENTIFIERS_AND_LABELS_SEALED",
        )

        freeze = preregistration["freeze"]
        self.assertEqual(
            freeze["freeze_state"],
            "FROZEN_BEFORE_ANY_HOLDOUT_ACCESS",
        )
        self.assertIs(freeze["labels_visible_at_freeze"], False)
        self.assertIs(freeze["results_visible_at_freeze"], False)
        for field in (
            "roster_mutation_after_freeze",
            "parameter_mutation_after_freeze",
            "endpoint_mutation_after_freeze",
            "estimand_mutation_after_freeze",
            "method_mutation_after_freeze",
        ):
            with self.subTest(field=field):
                self.assertIs(freeze[field], False)

    def test_red_15_b4_roster_is_replayed_without_new_methods(self) -> None:
        """RED-15: B8 cannot add, remove or rename a B4 baseline."""
        preregistration = load_yaml(CONFIG_PATHS["preregistration"])
        b4 = load_yaml(
            CONFIG_DIR / "part-b-baseline-preregistration-v0.8.yaml"
        )
        expected_ids = [item["baseline_id"] for item in b4["baselines"]]
        binding = preregistration["b4_roster_binding"]
        self.assertEqual(b4["hash"], B4_PREREGISTRATION_HASH)
        self.assertEqual(binding["registry_hash"], b4["hash"])
        self.assertEqual(binding["baseline_ids"], expected_ids)
        self.assertEqual(len(binding["baseline_ids"]), len(set(expected_ids)))
        self.assertIs(binding["no_new_methods"], True)
        self.assertIs(binding["roster_mutation"], False)

    def test_red_16_estimands_endpoints_units_directions_and_sesoi_freeze(
        self,
    ) -> None:
        """RED-16: all estimand semantics are outcome-blind and explicit."""
        plan = load_yaml(CONFIG_PATHS["analysis_plan"])
        estimands = [
            *plan["estimands"]["primary"],
            *plan["estimands"]["secondary"],
        ]
        self.assertGreater(len(plan["estimands"]["primary"]), 0)
        identifiers = [item["estimand_id"] for item in estimands]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for item in estimands:
            with self.subTest(estimand=item["estimand_id"]):
                self.assertTrue(item["endpoint_id"])
                self.assertTrue(item["analysis_unit"])
                self.assertTrue(item["effect_measure"])
                self.assertIn(
                    item["direction"],
                    ["LOWER_IS_BETTER", "HIGHER_IS_BETTER"],
                )
                self.assertIsNotNone(item["sesoi"])
                self.assertIs(item["frozen_before_holdout_access"], True)

    def test_red_17_alpha_confidence_and_multiplicity_are_predeclared(
        self,
    ) -> None:
        """RED-17: inferential error control cannot be chosen from results."""
        plan = load_yaml(CONFIG_PATHS["analysis_plan"])
        control = plan["error_control"]
        self.assertEqual(control["alpha"], "1/20")
        self.assertEqual(control["confidence_level"], "19/20")
        self.assertEqual(control["multiplicity_family"], "PRIMARY_ENDPOINTS")
        self.assertEqual(control["multiplicity_method"], "HOLM_STEP_DOWN")
        self.assertIs(control["adaptive_family_selection"], False)
        self.assertIs(control["outcome_dependent_method_selection"], False)

    def test_red_18_population_exclusions_and_missingness_freeze(self) -> None:
        """RED-18: populations and missingness cannot depend on outcomes."""
        plan = load_yaml(CONFIG_PATHS["analysis_plan"])
        population = plan["analysis_population"]
        self.assertEqual(population["unit"], "CASE")
        self.assertEqual(
            population["inclusion_rule"],
            "ALL_PREREGISTERED_HOLDOUT_CASES",
        )
        self.assertIs(population["exclusion_rules_frozen"], True)
        self.assertIs(population["post_outcome_exclusion"], False)

        missing = plan["missing_data"]
        self.assertEqual(
            missing["rule"],
            "NO_OUTCOME_DEPENDENT_IMPUTATION",
        )
        self.assertIs(missing["outcome_dependent_exclusion"], False)
        self.assertIs(missing["implicit_zero"], False)
        self.assertIs(missing["missing_as_loss"], False)

    def test_red_19_failure_channels_are_separate_and_unranked(self) -> None:
        """RED-19: failures and missingness never become loss, rank or UNSAT."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        self.assertEqual(
            policy["failure_semantics"],
            {
                "missing_outcome": "UNKNOWN_NO_RANK",
                "timeout": "UNKNOWN_NO_RANK",
                "resource_exhaustion": "UNKNOWN_NO_RANK",
                "infeasible": "SEPARATE_NO_RANK",
                "partial_result": "UNKNOWN_INCOMPLETE_NO_RANK",
                "analysis_not_executed": "CONTRACT_ONLY_NO_RESULT",
                "holdout_access_denied": "DENY_NO_ACCESS",
            },
        )
        flattened = " ".join(policy["failure_semantics"].values())
        for forbidden in ("UNSAT", "LOSS", "ZERO_COST"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, flattened)

    def test_red_20_randomness_ties_and_stopping_rules_are_frozen(self) -> None:
        """RED-20: no peeking, optional stopping or adaptive endpoint choice."""
        plan = load_yaml(CONFIG_PATHS["analysis_plan"])
        reproducibility = plan["reproducibility"]
        self.assertEqual(
            reproducibility["seed_policy"],
            "PREDECLARED_FIXED",
        )
        self.assertIsInstance(reproducibility["seed"], int)
        self.assertGreater(reproducibility["resampling_iterations"], 0)
        self.assertTrue(reproducibility["tie_break_rule"])

        stopping = plan["stopping_rule"]
        self.assertEqual(stopping["rule"], "FIXED_SINGLE_HOLDOUT_ANALYSIS")
        self.assertIs(stopping["optional_stopping"], False)
        self.assertIs(stopping["interim_peeking"], False)
        self.assertIs(stopping["adaptive_endpoint_selection"], False)
        self.assertIs(stopping["adaptive_sample_size"], False)

    def test_red_21_envelope_cross_binds_every_frozen_b8_input(self) -> None:
        """RED-21: an envelope cannot mix plans, policies or upstream states."""
        envelope = load_yaml(CONFIG_PATHS["analysis_envelope"])
        policy = load_yaml(CONFIG_PATHS["policy"])
        preregistration = load_yaml(CONFIG_PATHS["preregistration"])
        plan = load_yaml(CONFIG_PATHS["analysis_plan"])
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(
            envelope["analysis_id"],
            preregistration["analysis_id"],
        )
        self.assertEqual(
            envelope["bindings"],
            {
                "holdout_analysis_policy_hash": policy["hash"],
                "holdout_preregistration_hash": preregistration["hash"],
                "statistical_analysis_plan_hash": plan["hash"],
                "b8_manifest_hash": manifest["hash"],
                "b4_baseline_preregistration_hash": (
                    B4_PREREGISTRATION_HASH
                ),
                "b4_baseline_isolation_policy_hash": B4_ISOLATION_HASH,
                "b7_manifest_hash": B7_MANIFEST_HASH,
            },
        )

    def test_red_22_labels_results_and_statistics_are_absent(self) -> None:
        """RED-22: B8 examples describe plans, never holdout payloads."""
        access_boundary = {
            "holdout_data_loaded": False,
            "holdout_labels_loaded": False,
            "holdout_results_loaded": False,
            "statistics_computed": False,
        }
        for name in (
            "policy",
            "preregistration",
            "analysis_plan",
            "analysis_envelope",
        ):
            with self.subTest(artifact=name):
                document = load_yaml(CONFIG_PATHS[name])
                self.assertEqual(
                    document["access_boundary"],
                    access_boundary,
                )
                serialized = json.dumps(document, sort_keys=True)
                for forbidden_key in (
                    '"labels"',
                    '"outcomes"',
                    '"results"',
                    '"rankings"',
                    '"p_values"',
                    '"effect_estimates"',
                ):
                    self.assertNotIn(forbidden_key, serialized)

                injected = deepcopy(document)
                injected["results"] = [{"method": "forbidden"}]
                schema = load_json(SCHEMA_PATHS[name])
                self.assertNotEqual(
                    validation_errors(injected, schema),
                    [],
                )

    def test_red_23_release_gate_is_default_deny_and_fail_closed(self) -> None:
        """RED-23: a contract cannot itself release the sealed holdout."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        gate = policy["release_gate"]
        self.assertEqual(gate["default_decision"], "DENY")
        self.assertEqual(
            gate["required_conditions"],
            [
                "B4_REGISTRY_FROZEN",
                "B4_ISOLATION_BOUND",
                "SPLIT_COMMITMENT_FROZEN",
                "PER_SOURCE_AUTHORIZATION_APPROVED",
                "ANALYSIS_PLAN_FROZEN",
                "SEPARATE_EXECUTION_AUTHORIZATION_APPROVED",
            ],
        )
        self.assertEqual(gate["failure_behavior"], "FAIL_CLOSED_NO_ACCESS")
        self.assertIs(gate["contract_only_no_release"], True)

        widened = deepcopy(policy)
        widened["release_gate"]["default_decision"] = "ALLOW"
        self.assertNotEqual(
            validation_errors(widened, load_json(SCHEMA_PATHS["policy"])),
            [],
        )

    def test_red_24_holdout_feedback_cannot_cross_b4_boundaries(self) -> None:
        """RED-24: no B8 outcome may flow into any model or earlier split."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        b4 = load_yaml(
            CONFIG_DIR / "part-b-baseline-isolation-policy-v0.8.yaml"
        )
        isolation = policy["partition_isolation"]
        self.assertEqual(b4["hash"], B4_ISOLATION_HASH)
        self.assertEqual(isolation["b4_isolation_policy_hash"], b4["hash"])
        self.assertIs(isolation["mutually_disjoint"], True)
        for field in (
            "holdout_feedback_to_train",
            "holdout_feedback_to_tune",
            "holdout_feedback_to_evaluation",
            "holdout_feedback_to_planner",
            "holdout_feedback_to_any_model",
        ):
            with self.subTest(field=field):
                self.assertIs(isolation[field], False)
        self.assertIs(isolation["post_holdout_model_update"], False)

    def test_red_25_b7_provenance_does_not_authorize_a_holdout_source(
        self,
    ) -> None:
        """RED-25: B7 validity never closes the per-source PB-SI-006 gate."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        source = policy["source_boundary"]
        self.assertEqual(source["b7_manifest_hash"], B7_MANIFEST_HASH)
        self.assertEqual(source["pb_si_006_state"], "OPEN")
        self.assertIs(source["real_source_selected"], False)
        self.assertIs(source["real_source_authorized"], False)
        self.assertIs(source["per_source_authorization_required"], True)
        self.assertIs(source["abstract_contract_fixture_only"], True)

        serialized = json.dumps(
            [
                load_yaml(CONFIG_PATHS["preregistration"]),
                load_yaml(CONFIG_PATHS["analysis_plan"]),
                load_yaml(CONFIG_PATHS["analysis_envelope"]),
            ],
            sort_keys=True,
        )
        self.assertIsNone(
            re.search(r"(?:https?|s3|gs|ftp)://", serialized, re.IGNORECASE)
        )

    def test_red_26_no_execution_ranking_scalarization_claim_or_stop(
        self,
    ) -> None:
        """RED-26: B8 contracts emit no performance or certification result."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        plan = load_yaml(CONFIG_PATHS["analysis_plan"])
        policy = load_yaml(CONFIG_PATHS["policy"])

        cost = plan["cost_analysis"]
        self.assertEqual(cost["b3_policy_hash"], B3_POLICY_HASH)
        self.assertEqual(cost["dimensions"], COST_DIMENSIONS)
        self.assertIs(cost["scalarization_enabled"], False)
        self.assertIs(cost["outcome_dependent_metric_selection"], False)

        for field in (
            "statistical_analysis_execution_authority",
            "planner_execution_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(manifest[field], False)
                self.assertIs(policy[field], False)
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(policy["stop_authority"], "NONE")
        self.assertIs(
            manifest["proof_boundary"]["superiority_claim"],
            False,
        )

        b8_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b8-spec-issues.md"
        ).read_text(encoding="utf-8").upper()
        self.assertIn("PB-B5-SI-001", b8_issue)
        self.assertIn("OPEN", b8_issue)
        self.assertIn("B9", b8_issue)

        serialized = json.dumps(
            [manifest, policy, plan],
            sort_keys=True,
        )
        for forbidden in (
            "CERTIFIED_STOP",
            '"system_status"',
            '"certificate"',
            '"performance_ranking"',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
