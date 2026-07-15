import importlib.util
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location(
    "run_xgboost",
    SCRIPT_DIR / "run_xgboost.py",
)
run_xgboost = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_xgboost)


class XGBoostModelTests(unittest.TestCase):
    def test_new_runs_refuse_nonempty_output_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / "existing.txt").write_text("frozen", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                run_xgboost.require_empty_output(output)

    def test_embedded_legacy_cost_profiles_cover_selected_cases(self):
        experiment_dir = SCRIPT_DIR.parent
        _, test_dirs = run_xgboost.selected_case_dirs(
            experiment_dir / "examples",
            experiment_dir / "real_cases",
            test_prefixes=("C07-", "C08-", "C09-", "C10-", "C11-", "C12-"),
        )
        profiles = run_xgboost.embedded_cost_profiles(test_dirs)
        self.assertEqual(6, len(profiles))
        for identity in profiles.values():
            self.assertEqual(64, len(identity["sha256"]))
            self.assertEqual(
                "case_embedded_legacy_exogenous_cost",
                identity["provenance"],
            )

    def test_manifest_locks_train_test_boundary_and_writing_gate(self):
        experiment_dir = SCRIPT_DIR.parent
        train_dirs, test_dirs = run_xgboost.selected_case_dirs(
            experiment_dir / "examples",
            experiment_dir / "real_cases",
            test_prefixes=("C07-", "C08-", "C09-", "C10-", "C11-", "C12-"),
        )
        manifest = run_xgboost.evaluation_manifest(
            train_dirs,
            test_dirs,
            "test-xgboost-manifest",
            output_hashes={"results.csv": "a" * 64},
        )
        self.assertEqual(6, manifest["independent_test_case_count"])
        self.assertFalse(
            set(manifest["train_case_ids"]) & set(manifest["test_case_ids"])
        )
        self.assertEqual("case_or_attack_chain", manifest["statistical_unit"]["independent"])
        self.assertEqual(6, len(manifest["cost_profile_identity_by_case"]))
        self.assertTrue(manifest["endpoint_boundary"]["runtime_allowlist_enforced"])
        self.assertFalse(manifest["endpoint_boundary"]["runtime_labels_visible"])
        self.assertEqual(64, len(manifest["endpoint_boundary"]["sha256"]))
        self.assertEqual({"results.csv": "a" * 64}, manifest["output_sha256"])
        self.assertFalse(manifest["all_experiments_complete"])
        self.assertFalse(manifest["paper_or_patent_updated"])

    def test_uniform_costs_cover_training_and_test_without_mutating_cases(self):
        experiment_dir = SCRIPT_DIR.parent
        train_dirs, test_dirs = run_xgboost.selected_case_dirs(
            experiment_dir / "examples",
            experiment_dir / "real_cases",
            test_prefixes=("C07-", "C08-", "C09-", "C10-", "C11-", "C12-"),
        )
        identities = run_xgboost.cost_profile_identities(test_dirs, "uniform")
        self.assertEqual(6, len(identities))
        self.assertEqual(
            {"uniform_frozen_exogenous_cost"},
            {identity["provenance"] for identity in identities.values()},
        )
        rows = run_xgboost.build_rows_for_cost_regime(train_dirs[:1], "uniform")
        self.assertEqual({1.0}, {row["cost"] for row in rows})

    def test_manifest_accepts_cli_relative_case_paths(self):
        experiment_dir = SCRIPT_DIR.parent
        train_dirs, test_dirs = run_xgboost.selected_case_dirs(
            experiment_dir / "examples",
            experiment_dir / "real_cases",
            test_prefixes=("C07-", "C08-", "C09-", "C10-", "C11-", "C12-"),
        )
        workspace = experiment_dir.parent
        relative_train = [path.relative_to(workspace) for path in train_dirs]
        relative_test = [path.relative_to(workspace) for path in test_dirs]
        manifest = run_xgboost.evaluation_manifest(
            relative_train,
            relative_test,
            "relative-path-test",
            output_hashes={"results.csv": "a" * 64},
        )
        self.assertEqual(36, len(manifest["input_sha256"]))

    def test_c10_extension_is_opt_in(self):
        experiment_dir = SCRIPT_DIR.parent
        examples_root = experiment_dir / "examples"
        real_cases_root = experiment_dir / "real_cases"

        train, original_test = run_xgboost.selected_case_dirs(
            examples_root,
            real_cases_root,
        )
        extended_train, extended_test = run_xgboost.selected_case_dirs(
            examples_root,
            real_cases_root,
            include_c10=True,
        )

        self.assertEqual(6, len(train))
        self.assertEqual(train, extended_train)
        self.assertEqual(3, len(original_test))
        self.assertEqual(4, len(extended_test))
        self.assertFalse(any(path.name.startswith("C10-") for path in original_test))
        self.assertTrue(any(path.name.startswith("C10-") for path in extended_test))

    def test_frozen_parameters_are_stable(self):
        self.assertEqual(3, run_xgboost.FROZEN_PARAMS["max_depth"])
        self.assertEqual(0.05, run_xgboost.FROZEN_PARAMS["eta"])
        self.assertEqual(11, run_xgboost.FROZEN_PARAMS["seed"])
        self.assertEqual(150, run_xgboost.FROZEN_BOOST_ROUNDS)

    def test_learns_a_separable_public_feature(self):
        rows = []
        for value, label in [(0.0, 0), (0.1, 0), (0.9, 1), (1.0, 1)] * 16:
            rows.append({"gap": value, "label": label, "group_id": str(len(rows))})

        model = run_xgboost.train_xgboost(
            rows,
            ["gap"],
            "label",
            params={**run_xgboost.FROZEN_PARAMS, "min_child_weight": 0.0},
            boost_rounds=20,
        )

        low = run_xgboost.predict_probability(model, {"gap": 0.0})
        high = run_xgboost.predict_probability(model, {"gap": 1.0})
        self.assertLess(low, 0.25)
        self.assertGreater(high, 0.75)
        self.assertGreater(high - low, 0.5)

    def test_feature_contract_excludes_hidden_outcomes(self):
        forbidden = {
            "recoverable_claim_ids",
            "hidden_claim_ids",
            "actual_recovered_claims",
            "oracle_path",
        }

        self.assertFalse(forbidden & set(run_xgboost.FEATURE_COLUMNS))


class XGBoostPolicyTests(unittest.TestCase):
    def test_selector_uses_public_features_not_hidden_recovery(self):
        config = {
            "case_id": "T-XGB",
            "budget_total": 4,
            "cti_nodes": [{"node_id": "N1", "critical": True}],
        }
        state = {
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {"local_log": 0.0},
            },
            "unmatched_cti_node_ids": ["N1"],
            "budget": {"budget_remaining": 4},
            "actions_taken": [],
            "action_feedback": [],
        }
        actions = [
            self.action("A-low", 2, [], [], 0.1),
            self.action("A-high", 2, ["N1"], ["SECRET"], 1.0),
        ]
        rows = []
        for action, label in [(actions[0], 0), (actions[1], 1)] * 32:
            row = run_xgboost.run_m3b.feature_row(config, state, action)
            row.update({"label": label, "group_id": str(len(rows))})
            rows.append(row)
        model = run_xgboost.train_xgboost(
            rows,
            run_xgboost.FEATURE_COLUMNS,
            "label",
            params={**run_xgboost.FROZEN_PARAMS, "min_child_weight": 0.0},
            boost_rounds=30,
        )

        first = run_xgboost.select_xgboost_action(config, state, actions, model, 0.1)
        changed = deepcopy(actions)
        changed[0]["recoverable_claim_ids"] = ["DIFFERENT"]
        changed[1]["recoverable_claim_ids"] = []
        changed[0]["actual_recovered_claims"] = ["FORCED"]
        changed[1]["oracle_path"] = ["A-low"]
        second = run_xgboost.select_xgboost_action(config, state, changed, model, 0.1)

        self.assertEqual("A-high", first["action_id"])
        self.assertEqual(first["action_id"], second["action_id"])

    def test_logistic_selector_uses_the_same_runtime_allowlist(self):
        config = {
            "case_id": "T-LOG",
            "budget_total": 4,
            "cti_nodes": [{"node_id": "N1", "critical": True}],
            "channel_reliability": {"other": 1.0},
        }
        state = {
            "coverage": {
                "cti_node_coverage": 0.0,
                "cti_edge_coverage": 0.0,
                "critical_gap_count": 1,
                "stage_coverage": {"execution": 0.0},
                "evidence_type_coverage": {"local_log": 0.0},
            },
            "unmatched_cti_node_ids": ["N1"],
            "budget": {"budget_remaining": 4},
            "actions_taken": [],
            "action_feedback": [],
        }
        actions = [
            self.action("A-low", 2, [], [], 0.1),
            self.action("A-high", 2, ["N1"], ["SECRET"], 1.0),
        ]
        rows = []
        for action, label in [(actions[0], 0), (actions[1], 1)] * 32:
            row = run_xgboost.run_m3b.feature_row(config, state, action)
            row.update({"label": label, "group_id": str(len(rows))})
            rows.append(row)
        model = run_xgboost.run_m3b.train_logistic_baseline(
            rows, run_xgboost.FEATURE_COLUMNS, "label"
        )
        first = run_xgboost.select_logistic_action(config, state, actions, model, 0.1)
        changed = deepcopy(actions)
        changed[0]["recoverable_claim_ids"] = ["FORCED"]
        changed[1]["recoverable_claim_ids"] = []
        changed[0]["oracle_path"] = ["A-low"]
        second = run_xgboost.select_logistic_action(config, state, changed, model, 0.1)
        self.assertEqual(first["action_id"], second["action_id"])

    @staticmethod
    def action(action_id, cost, intended_nodes, recoverable, gain):
        return {
            "action_id": action_id,
            "action_type": "extend_log_window",
            "cost": cost,
            "target": {"target_type": "process", "target_value": action_id},
            "intended_cti_node_ids": intended_nodes,
            "recoverable_claim_ids": recoverable,
            "expected_stages": ["execution"],
            "expected_evidence_types": ["local_log"],
            "expected_effects": {
                "expected_granularity_gain": gain,
                "expected_uncertainty_reduction": gain,
                "expected_over_attribution_risk_reduction": gain,
                "expected_conflict_resolution": 0,
                "expected_coverage_delta": gain,
            },
        }


if __name__ == "__main__":
    unittest.main()
