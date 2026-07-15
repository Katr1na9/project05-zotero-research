import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments" / "scripts" / "run_afa_voi_baselines.py"
MVP_PATH = ROOT / "09-experiments" / "scripts" / "run_mvp.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MVP = load(MVP_PATH, "run_mvp_for_afa_tests")


def config():
    return {
        "case_id": "toy",
        "budget_total": 3,
        "channel_reliability": {"host": 1.0},
        "granularity_order": [
            "G0_unknown",
            "G1_technique",
            "G2_tactic_intent",
            "G3_campaign",
        ],
        "support_ceiling": "G3_campaign",
        "granularity_thresholds": {
            "g3_node_coverage": 0.5,
            "g3_edge_coverage": 0.5,
            "g2_node_coverage": 0.45,
            "g2_min_stages": 2,
            "g1_node_coverage": 0.15,
        },
        "cti_nodes": [
            {"node_id": "N1", "stage": "s1", "critical": True},
            {"node_id": "N2", "stage": "s2", "critical": True},
            {"node_id": "N3", "stage": "s1", "critical": False},
            {"node_id": "N4", "stage": "s2", "critical": False},
        ],
        "cti_edges": [{"edge_id": "E1", "source": "N1", "target": "N2"}],
    }


def state():
    return {
        "matched_cti_node_ids": [],
        "budget": {"budget_total": 3, "budget_used": 0, "budget_remaining": 3},
        "actions_taken": [],
        "action_feedback": [],
    }


def action(action_id, intended, recoverable, cost=1.0, channel="host"):
    return {
        "action_id": action_id,
        "action_type": "query",
        "acquisition_channel": channel,
        "cost": cost,
        "intended_cti_node_ids": intended,
        "recoverable_claim_ids": recoverable,
        "expected_effects": {},
        "expected_stages": [],
        "expected_evidence_types": [],
        "target": {"target_type": "node", "target_value": action_id},
    }


class AfaVoiBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load(SCRIPT, "run_afa_voi_baselines") if SCRIPT.exists() else None

    def require_module(self):
        if self.module is None:
            self.skipTest("AFA-VOI implementation does not exist yet")
        return self.module

    def test_module_exists(self):
        self.assertTrue(SCRIPT.exists(), "AFA-VOI baseline has not been implemented")

    def test_hidden_recovery_does_not_affect_selection(self):
        module = self.require_module()
        actions = [
            action("A", ["N3", "N4"], ["secret-a"]),
            action("B", ["N1"], ["secret-b"]),
            MVP.make_stop_action("toy"),
        ]
        changed = copy.deepcopy(actions)
        changed[0]["recoverable_claim_ids"] = []
        changed[1]["recoverable_claim_ids"] = ["different"]
        first = module.select_afa_voi("afa_voi_myopic", config(), state(), actions)
        second = module.select_afa_voi("afa_voi_myopic", config(), state(), changed)
        self.assertEqual(first["action_id"], second["action_id"])

    def test_planner_channel_prior_override_keeps_execution_profile_fixed(self):
        module = self.require_module()
        execution = config()
        execution["channel_reliability"] = {"host": 0.8}

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

    def test_execute_cases_marks_which_planners_consume_channel_belief(self):
        module = self.require_module()
        case = next(
            (ROOT / "09-experiments" / "real_cases").glob("C12-*")
        )

        rows, _ = module.execute_cases(
            [case], channel_prior_multiplier=0.75
        )

        self.assertEqual(180, len(rows))
        self.assertEqual(
            {"planner_belief_only"},
            {row["channel_prior_scope"] for row in rows},
        )
        self.assertEqual(
            {1},
            {int(row["execution_channel_profile_held_constant"]) for row in rows},
        )
        consumed = {
            planner: {
                int(row["channel_prior_consumed_by_planner"])
                for row in rows
                if row["planner"] == planner
            }
            for planner in module.PLANNERS
        }
        self.assertEqual({0}, consumed["project05_m2"])
        self.assertEqual({1}, consumed[module.MYOPIC])
        self.assertEqual({1}, consumed[module.ROLLOUT])
        self.assertEqual({0}, consumed["oracle_optimal"])
        self.assertEqual(
            1,
            len({row["execution_channel_profile_sha256"] for row in rows}),
        )
        self.assertEqual(
            1,
            len({row["planner_channel_prior_sha256"] for row in rows}),
        )
        self.assertNotEqual(
            rows[0]["execution_channel_profile_sha256"],
            rows[0]["planner_channel_prior_sha256"],
        )

    def test_manifest_records_hashes_statistical_unit_and_closed_writing_gate(self):
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
            "test-afa-manifest",
            channel_prior_multiplier=0.75,
            output_hashes={"results.csv": "a" * 64},
        )

        self.assertEqual("case_or_attack_chain", manifest["statistical_unit"]["independent"])
        self.assertTrue(manifest["statistical_unit"]["pseudoreplication_forbidden"])
        self.assertEqual(0.75, manifest["channel_prior_intervention"]["multiplier"])
        self.assertEqual("planner_belief_only", manifest["channel_prior_intervention"]["scope"])
        self.assertEqual({"results.csv": "a" * 64}, manifest["output_sha256"])
        self.assertEqual("legacy", manifest["cost_regime"])
        self.assertEqual(1, len(manifest["cost_profile_identity_by_case"]))
        self.assertEqual(64, len(manifest["runner_sha256"]))
        self.assertFalse(manifest["all_experiments_complete"])
        self.assertFalse(manifest["paper_or_patent_updated"])

    def test_uniform_costs_are_applied_and_identified(self):
        module = self.require_module()
        case = next((ROOT / "09-experiments" / "real_cases").glob("C12-*"))
        rows, _ = module.execute_cases([case], cost_regime="uniform")
        self.assertEqual({"uniform"}, {row["cost_regime"] for row in rows})
        self.assertEqual(1, len({row["cost_profile_sha256"] for row in rows}))
        identities = module.cost_profile_identities([case], "uniform")
        identity = next(iter(identities.values()))
        self.assertEqual("uniform_frozen_exogenous_cost", identity["provenance"])

    def test_non_greedy_rollout_can_select_complementary_plan_member(self):
        module = self.require_module()
        actions = [
            action("A", ["N3", "N4"], ["x"]),
            action("B", ["N1"], ["y"]),
            action("C", ["N2"], ["z"]),
            MVP.make_stop_action("toy"),
        ]
        myopic = module.select_afa_voi("afa_voi_myopic", config(), state(), actions)
        rollout = module.select_afa_voi("afa_voi_rollout_h3", config(), state(), actions)
        self.assertEqual(myopic["action_id"], "A")
        self.assertIn(rollout["action_id"], {"B", "C"})

    def test_stop_wins_when_no_public_value_is_available(self):
        module = self.require_module()
        actions = [action("A", [], ["hidden"], cost=1.0), MVP.make_stop_action("toy")]
        chosen = module.select_afa_voi("afa_voi_rollout_h3", config(), state(), actions)
        self.assertEqual(chosen["action_id"], MVP.STOP_ACTION_ID)

    def test_selection_does_not_mutate_inputs(self):
        module = self.require_module()
        current_state = state()
        actions = [action("A", ["N1"], ["x"]), MVP.make_stop_action("toy")]
        expected_state = copy.deepcopy(current_state)
        expected_actions = copy.deepcopy(actions)
        module.select_afa_voi("afa_voi_rollout_h3", config(), current_state, actions)
        self.assertEqual(current_state, expected_state)
        self.assertEqual(actions, expected_actions)


if __name__ == "__main__":
    unittest.main()
