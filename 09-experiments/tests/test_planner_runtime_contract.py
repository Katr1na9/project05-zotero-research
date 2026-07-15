import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
ADAPTER_PATH = EXP / "scripts" / "planner_runtime_adapter.py"
CONTRACT_PATH = EXP / "governance" / "contracts" / "planner-runtime-contract-v0.1.json"
SCHEMA_PATH = EXP / "data_schema" / "planner_runtime_contract.schema.json"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PlannerRuntimeContractTests(unittest.TestCase):
    def test_contract_schema_and_frozen_feature_columns(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(contract)))
        self.assertFalse(contract["ml_feature_contract"]["labels_runtime_visible"])
        self.assertTrue(contract["leakage_controls"]["runtime_allowlist_required"])

    def test_runtime_view_recursively_removes_hidden_and_realized_fields(self):
        adapter = load(ADAPTER_PATH, "planner_runtime_adapter_test")
        config = {
            "case_id": "T",
            "budget_total": 3,
            "cti_nodes": [{"node_id": "N1", "stage": "s", "critical": True, "required_claim_ids": ["secret"]}],
            "channel_reliability": {"host": 0.8},
            "target_case_outcome_prior": {"winner": "secret"},
        }
        state = {
            "coverage": {"cti_node_coverage": 0.0, "cti_edge_coverage": 0.0, "critical_gap_count": 1},
            "budget": {"budget_total": 3, "budget_used": 0, "budget_remaining": 3},
            "unmatched_cti_node_ids": ["N1"],
            "actions_taken": [],
            "action_feedback": [{"action_id": "old", "action_type": "query", "recovered_count": 0, "channel_up": 0, "recovered_claim_ids": ["secret"]}],
            "hidden_claim_ids": ["secret"],
            "mask_strategy": "secret",
        }
        actions = [{
            "action_id": "A",
            "action_type": "query",
            "acquisition_channel": "host",
            "target": {"target_type": "node", "target_value": "N1", "hidden": "secret"},
            "cost": 1,
            "intended_cti_node_ids": ["N1"],
            "expected_stages": ["s"],
            "expected_evidence_types": ["host"],
            "expected_effects": {"expected_granularity_gain": 0.2, "realized_recovery": ["secret"]},
            "recoverable_claim_ids": ["secret"],
        }]
        view = adapter.build_runtime_view(config, state, actions)
        contract = adapter.load_contract()["document"]
        forbidden = set(contract["planner_visibility"]["recursive_forbidden_keys"])
        self.assertEqual([], adapter.recursive_key_hits(view, forbidden))
        self.assertNotIn("required_claim_ids", view["config"]["cti_nodes"][0])
        self.assertNotIn("recoverable_claim_ids", view["actions"][0])
        self.assertNotIn("realized_recovery", view["actions"][0]["expected_effects"])
        self.assertEqual(
            [{"action_id": "old", "action_type": "query", "recovered_count": 0}],
            view["state"]["action_feedback"],
        )


if __name__ == "__main__":
    unittest.main()
