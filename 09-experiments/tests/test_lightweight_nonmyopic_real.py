import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments" / "scripts" / "run_lightweight_nonmyopic_real.py"
MVP_SCRIPT = ROOT / "09-experiments" / "scripts" / "run_mvp.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MVP = load(MVP_SCRIPT, "run_mvp_for_depth2_tests")


def base_state():
    return {
        "coverage": {
            "stage_coverage": {"stage_a": 0.0, "stage_b": 0.0},
            "evidence_type_coverage": {"type_a": 0.0, "type_b": 0.0},
        },
        "budget": {"budget_total": 3.0, "budget_used": 0.0, "budget_remaining": 3.0},
        "actions_taken": [],
        "action_feedback": [],
        "unmatched_cti_node_ids": ["N1", "N2"],
    }


def action(action_id, stage, evidence_type, gain, recoverable, intended, target):
    return {
        "action_id": action_id,
        "action_type": "query",
        "acquisition_channel": "host",
        "cost": 1.0,
        "recoverable_claim_ids": recoverable,
        "intended_cti_node_ids": intended,
        "expected_stages": [stage] if stage else [],
        "expected_evidence_types": [evidence_type] if evidence_type else [],
        "expected_effects": {
            "expected_granularity_gain": gain,
            "expected_uncertainty_reduction": 0.2 if gain else 0.0,
            "expected_over_attribution_risk_reduction": 0.2 if gain else 0.0,
            "expected_coverage_delta": 0.3 if gain else 0.0,
        },
        "target": {"target_type": "node", "target_value": target},
    }


class LightweightNonmyopicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SCRIPT.exists():
            cls.module = load(SCRIPT, "run_lightweight_nonmyopic_real")
        else:
            cls.module = None

    def require_module(self):
        if self.module is None:
            self.skipTest("implementation module does not exist yet")
        return self.module

    def test_implementation_module_exists(self):
        self.assertTrue(SCRIPT.exists(), "Depth-2 public planner has not been implemented")

    def test_hidden_recovery_changes_do_not_change_selection(self):
        module = self.require_module()
        config = {"channel_reliability": {"host": 0.8}}
        actions = [
            action("A", "stage_a", "type_a", 0.8, ["secret-1"], ["N1"], "A"),
            action("B", "stage_b", "type_b", 0.7, ["secret-2"], ["N2"], "B"),
            MVP.make_stop_action("toy"),
        ]
        changed = copy.deepcopy(actions)
        changed[0]["recoverable_claim_ids"] = ["completely-different"]
        changed[1]["recoverable_claim_ids"] = []
        changed[0]["realized_recovery"] = ["forced-secret"]
        changed[1]["oracle_path"] = ["B"]

        first = module.select_depth2_public(config, base_state(), actions)
        second = module.select_depth2_public(config, base_state(), changed)
        self.assertEqual(first["action_id"], second["action_id"])

    def test_planner_channel_prior_override_keeps_execution_profile_fixed(self):
        module = self.require_module()
        execution = {"channel_reliability": {"host": 0.8}}

        planner_config, metadata = module.planner_config_for_channel_prior(
            execution, 0.75
        )

        self.assertEqual({"host": 0.8}, execution["channel_reliability"])
        self.assertEqual({"host": 0.6}, planner_config["channel_reliability"])
        self.assertEqual("planner_belief_only", metadata["channel_prior_scope"])
        self.assertEqual(1, metadata["execution_channel_profile_held_constant"])
        self.assertNotEqual(
            metadata["execution_channel_profile_sha256"],
            metadata["planner_channel_prior_sha256"],
        )

    def test_execute_cases_marks_only_depth2_as_channel_prior_consumer(self):
        module = self.require_module()
        case = next(
            (ROOT / "09-experiments" / "real_cases").glob("C12-*")
        )

        rows, _ = module.execute_cases(
            [case], channel_prior_multiplier=0.75
        )

        self.assertEqual(135, len(rows))
        consumed = {
            planner: {
                int(row["channel_prior_consumed_by_planner"])
                for row in rows
                if row["planner"] == planner
            }
            for planner in module.BASELINES
        }
        self.assertEqual({0}, consumed["project05_m2"])
        self.assertEqual({1}, consumed[module.PLANNER])
        self.assertEqual({0}, consumed["oracle_optimal"])
        self.assertEqual(
            {"planner_belief_only"},
            {row["channel_prior_scope"] for row in rows},
        )
        self.assertEqual(
            {1},
            {int(row["execution_channel_profile_held_constant"]) for row in rows},
        )

    def test_manifest_records_depth2_boundary_and_closed_writing_gate(self):
        module = self.require_module()
        case = next(
            (ROOT / "09-experiments" / "real_cases").glob("C12-*")
        )
        case_id = MVP.load_json(case / "case_config.json")["case_id"]
        rows = [
            {
                "case_id": case_id,
                "mask_strategy": "random",
                "mask_intensity": 0.2,
                "seed": 11,
            }
        ]
        manifest = module.evaluation_manifest(
            [case],
            rows,
            "test-depth2-manifest",
            channel_prior_multiplier=0.75,
            output_hashes={"results.csv": "a" * 64},
        )

        self.assertEqual("case_or_attack_chain", manifest["statistical_unit"]["independent"])
        self.assertTrue(manifest["statistical_unit"]["pseudoreplication_forbidden"])
        self.assertEqual(0.75, manifest["channel_prior_intervention"]["multiplier"])
        self.assertEqual([module.PLANNER], manifest["channel_prior_intervention"]["consumed_by_planners"])
        self.assertTrue(manifest["endpoint_boundary"]["runtime_allowlist_enforced"])
        self.assertEqual(64, len(manifest["endpoint_boundary"]["sha256"]))
        self.assertFalse(manifest["endpoint_boundary"]["realized_outcomes_visible"])
        self.assertTrue(manifest["endpoint_boundary"]["hidden_outcome_invariance_tested"])
        self.assertEqual({"results.csv": "a" * 64}, manifest["output_sha256"])
        self.assertEqual("legacy", manifest["cost_regime"])
        self.assertEqual(1, len(manifest["cost_profile_identity_by_case"]))
        self.assertFalse(manifest["all_experiments_complete"])
        self.assertFalse(manifest["paper_or_patent_updated"])

    def test_uniform_costs_are_applied_and_identified(self):
        module = self.require_module()
        case = next((ROOT / "09-experiments" / "real_cases").glob("C12-*"))
        rows, _ = module.execute_cases([case], cost_regime="uniform")
        self.assertEqual({"uniform"}, {row["cost_regime"] for row in rows})
        identities = module.cost_profile_identities([case], "uniform")
        identity = next(iter(identities.values()))
        self.assertEqual("uniform_frozen_exogenous_cost", identity["provenance"])

    def test_depth2_can_prefer_reliable_diverse_step_over_myopic_choice(self):
        module = self.require_module()
        config = {"channel_reliability": {"host": 1.0, "network": 0.1}}
        actions = [
            action("A", "stage_a", "type_a", 1.0, ["x"], ["N1"], "same"),
            action("B", "stage_b", "type_b", 0.75, ["y"], ["N2"], "different"),
            action("C", "stage_a", "type_a", 1.0, ["z"], ["N1"], "same"),
            MVP.make_stop_action("toy"),
        ]
        actions[0]["acquisition_channel"] = "network"
        actions[2]["acquisition_channel"] = "network"
        myopic = MVP.select_action(
            "project05_m2",
            config,
            [],
            actions,
            base_state(),
            set(),
            set(),
            [],
            11,
        )
        depth2 = module.select_depth2_public(config, base_state(), actions)

        self.assertIn(myopic["action_id"], {"A", "C"})
        self.assertEqual(depth2["action_id"], "B")

    def test_stop_wins_when_all_acquisition_values_are_negative(self):
        module = self.require_module()
        config = {"channel_reliability": {"host": 0.0}}
        actions = [
            action("A", "", "", 0.0, ["x"], [], "none"),
            MVP.make_stop_action("toy"),
        ]
        selected = module.select_depth2_public(config, base_state(), actions)
        self.assertEqual(selected["action_id"], MVP.STOP_ACTION_ID)

    def test_selection_does_not_mutate_state_or_actions(self):
        module = self.require_module()
        config = {"channel_reliability": {"host": 0.5}}
        state = base_state()
        actions = [
            action("A", "stage_a", "type_a", 0.8, ["x"], ["N1"], "A"),
            MVP.make_stop_action("toy"),
        ]
        expected_state = copy.deepcopy(state)
        expected_actions = copy.deepcopy(actions)
        module.select_depth2_public(config, state, actions)
        self.assertEqual(state, expected_state)
        self.assertEqual(actions, expected_actions)

    def test_compressed_trace_export_is_byte_reproducible(self):
        module = self.require_module()
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.json.gz"
            second = Path(temp) / "second.json.gz"
            traces = [{"run_id": "test", "trace": [{"event": "initial"}]}]
            module.write_traces(first, traces)
            module.write_traces(second, traces)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
