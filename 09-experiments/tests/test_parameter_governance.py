import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MVP = load_module(EXP / "scripts" / "run_mvp.py", "parameter_governance_mvp")
GOV = load_module(
    EXP / "scripts" / "run_parameter_governance.py", "parameter_governance_runner"
)


class ParameterGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.governance = json.loads(
            (EXP / "governance" / "parameter-governance-v0.1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.source_profile = json.loads(
            (
                EXP
                / "governance"
                / "profiles"
                / "corroboration-source-groups-v0.1.json"
            ).read_text(encoding="utf-8")
        )
        cls.action_profile = json.loads(
            (
                EXP
                / "governance"
                / "profiles"
                / "action-priors-development-derived-v0.1.json"
            ).read_text(encoding="utf-8")
        )

    def test_threshold_grid_has_all_40_locked_combinations(self):
        variants = GOV.threshold_variants(self.governance)
        self.assertEqual(40, len(variants))
        self.assertEqual(40, len({tuple(sorted(row.items())) for row in variants}))

    def test_v02_governance_locks_channel_belief_environment_separation(self):
        path = EXP / "governance" / "parameter-governance-v0.2.json"
        governance = json.loads(path.read_text(encoding="utf-8"))
        sensitivity = governance["expert_prior_sensitivity"]
        self.assertEqual("planner_belief_only", sensitivity["channel_prior_scope"])
        self.assertEqual(
            "frozen_case_config",
            sensitivity["execution_channel_reliability_source"],
        )
        self.assertTrue(
            sensitivity[
                "environment_realization_held_constant_across_prior_variants"
            ]
        )
        self.assertEqual(path, GOV.DEFAULT_GOVERNANCE)
        self.assertEqual(
            "parameter_governance_v0.2", GOV.DEFAULT_OUTPUT.name
        )

    def test_k_of_n_preserves_or_and_endpoints(self):
        case = next((EXP / "real_cases").glob("C11-*"))
        config = MVP.load_json(case / "case_config.json")
        claims = MVP.load_json(case / "evidence_claims.json")
        visible = {claim["claim_id"] for claim in claims}
        for semantics, k in (("OR", 1), ("AND", 99)):
            old = dict(config, node_coverage_semantics=semantics)
            new = dict(
                config,
                node_coverage_semantics="K_OF_N",
                node_coverage_k=k,
                corroboration_unit="claim",
            )
            self.assertEqual(
                MVP.covered_node_ids(old, visible),
                MVP.covered_node_ids(new, visible),
            )

    def test_source_group_mapping_does_not_call_same_provider_independent(self):
        collapsed = {
            row["node_id"]
            for row in self.source_profile["node_audit"]
            if row["claim_count_overstates_source_groups"]
        }
        self.assertEqual(
            {"N01_perimeter_activity", "N02_privileged_identity_activity"},
            collapsed,
        )
        self.assertIn("must not be described", self.source_profile["independence_boundary"])

    def test_alpha_default_is_exact_frozen_score(self):
        action = {
            "action_id": "A",
            "action_type": "other",
            "cost": 2,
            "expected_effects": {"expected_granularity_gain": 1},
            "expected_stages": [],
            "expected_evidence_types": [],
        }
        state = {
            "coverage": {
                "critical_gap_count": 0,
                "stage_coverage": {},
                "evidence_type_coverage": {},
            },
            "budget": {"budget_remaining": 5},
            "actions_taken": [],
            "action_feedback": [],
        }
        self.assertEqual(
            MVP.m2_action_score(action, state, [action]),
            MVP.m2_action_score(action, state, [action], cost_coefficient=0.75),
        )

    def test_alpha_scan_uses_separate_pairable_variants(self):
        case = next((EXP / "real_cases").glob("C11-*"))
        rows = GOV.run_alpha_scan([case], self.governance)
        variants = {row["governance_variant"] for row in rows}
        self.assertEqual(
            variants,
            {
                "m2_alpha_0p00",
                "m2_alpha_0p25",
                "m2_alpha_0p50",
                "m2_alpha_0p75",
                "m2_alpha_1p00",
                "m2_alpha_1p50",
                "m2_alpha_2p00",
            },
        )
        for variant in variants:
            selected = [
                row for row in rows if row["governance_variant"] == variant
            ]
            self.assertEqual(len(selected), 90)
            self.assertEqual(
                {row["planner"] for row in selected},
                {"project05_m2", "oracle_optimal"},
            )

    def test_cost_scan_runs_only_runnable_legacy_and_uniform_arms(self):
        case = next((EXP / "real_cases").glob("C11-*"))
        rows = GOV.run_cost_scan(
            [case], ("project05_m2", "oracle_optimal")
        )
        self.assertEqual(
            {row["governance_variant"] for row in rows},
            {"legacy", "uniform"},
        )
        self.assertEqual(len(rows), 180)
        for row in rows:
            self.assertEqual(len(row["cost_profile_sha256"]), 64)
            self.assertNotIn(row["cost_regime"], {"rubric", "measured"})

    def test_paired_stability_reports_cases_as_independent_units(self):
        rows = []
        for case_id in ("C1", "C2"):
            for seed in (1, 2):
                baseline_success = 1
                candidate_success = int(not (case_id == "C2" and seed == 2))
                for variant, success, cost, action in (
                    ("baseline", baseline_success, 2.0, "A"),
                    ("candidate", candidate_success, 1.0, "B"),
                ):
                    rows.append(
                        {
                            "case_id": case_id,
                            "mask_strategy": "random",
                            "mask_intensity": 0.4,
                            "seed": seed,
                            "planner": "project05_m2",
                            "governance_variant": variant,
                            "reached_target": success,
                            "cost_to_target": cost if success else "",
                            "budget_used": cost,
                            "final_node_coverage": 0.5,
                            "actions_taken": action,
                            "ceiling_violation": 0,
                        }
                    )
        stability = GOV.paired_stability(rows, "baseline")
        candidate = stability["by_planner"]["project05_m2"]["candidate"]
        self.assertEqual(stability["analysis_unit"], "case_or_attack_chain")
        self.assertEqual(
            candidate["overall_repeated_measure_summary"]["success_flip_rate"],
            0.25,
        )
        independent = candidate["independent_case_summary"]
        self.assertEqual(independent["independent_case_count"], 2)
        self.assertEqual(independent["cases_with_success_loss"], 1)
        self.assertIn("not_reported", stability["inferential_statistics"])

    def test_action_prior_training_and_application_are_disjoint(self):
        train = set(self.action_profile["training_scope"]["case_ids"])
        test = set(self.action_profile["application_scope"]["case_ids"])
        self.assertFalse(train & test)
        self.assertEqual(6, len(train))
        self.assertEqual(6, len(test))
        self.assertEqual(31, len(self.action_profile["actions"]))
        self.assertIn("No C07-C12", self.action_profile["leakage_boundary"])

    def test_channel_prior_sensitivity_keeps_execution_environment_fixed(self):
        case = next((EXP / "real_cases").glob("C07-*"))
        config = MVP.load_json(case / "case_config.json")
        actions = MVP.load_json(case / "acquisition_actions.json")
        original_reliability = dict(config["channel_reliability"])
        entries, channels = GOV.action_prior_maps(self.action_profile)

        updated_config, _ = GOV.apply_action_priors(
            config,
            actions,
            entries,
            channels,
            expert_multiplier=1.0,
            channel_multiplier=0.75,
        )

        self.assertEqual(original_reliability, config["channel_reliability"])
        self.assertEqual(
            original_reliability,
            updated_config["channel_reliability"],
            "A planner-prior perturbation must not alter realized channel uptime",
        )
        self.assertEqual(
            0.375,
            updated_config["planner_channel_reliability"]["network_telemetry"],
        )

    def test_builtin_w6_scan_records_belief_only_channel_intervention(self):
        case = next((EXP / "real_cases").glob("C07-*"))
        rows = GOV.run_action_prior_scan(
            [case],
            ("project05_m2",),
            self.governance,
            self.action_profile,
            "a" * 64,
        )
        selected = {
            (
                row["governance_variant"],
                row["mask_strategy"],
                str(row["mask_intensity"]),
                str(row["seed"]),
            ): row
            for row in rows
        }
        outcome_fields = (
            "reached_target",
            "budget_used",
            "actions_taken",
            "recovered_claims",
            "final_granularity",
        )
        condition_keys = {
            key[1:] for key in selected if key[0] == "dev_measured_base"
        }
        for condition in condition_keys:
            baseline = selected[("dev_measured_base", *condition)]
            lowered = selected[("dev_measured_channel_x0.75", *condition)]
            self.assertEqual(
                baseline["execution_channel_profile_sha256"],
                lowered["execution_channel_profile_sha256"],
            )
            self.assertNotEqual(
                baseline["planner_channel_prior_sha256"],
                lowered["planner_channel_prior_sha256"],
            )
            self.assertEqual("planner_belief_only", lowered["channel_prior_scope"])
            self.assertEqual(0, lowered["channel_prior_consumed_by_planner"])
            self.assertEqual(1, lowered["execution_channel_profile_held_constant"])
            self.assertEqual(
                tuple(baseline[field] for field in outcome_fields),
                tuple(lowered[field] for field in outcome_fields),
            )

    def test_external_actor_accuracy_is_not_fabricated(self):
        rows = [
            {
                "reached_target": 1,
                "ceiling_violation": 0,
                "oracle_reachable": 1,
                "premature_stop": 0,
                "justified_degrade_stop": 0,
            }
        ]
        metrics = GOV.evidence_limited_endpoints(rows)
        self.assertIsNone(metrics["external_actor_accuracy"])
        self.assertIn("not_identifiable", metrics["external_actor_accuracy_status"])


if __name__ == "__main__":
    unittest.main()
