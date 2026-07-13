import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ROOT / "09-experiments"
CASE_DIR = EXPERIMENTS / "real_cases" / "C12-witfoo-precinct6-f10c7270"
SCREEN = (
    EXPERIMENTS
    / "results"
    / "c12_witfoo_screen_v0.1"
    / "candidate_index.json"
)
EVENT_AUDIT = (
    EXPERIMENTS
    / "results"
    / "c12_witfoo_event_audit_v0.1"
    / "audit.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_run_mvp():
    path = EXPERIMENTS / "scripts" / "run_mvp.py"
    spec = importlib.util.spec_from_file_location("c12_run_mvp_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RUN_MVP = load_run_mvp()


class C12OperationalCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load(CASE_DIR / "case_config.json")
        cls.claims = load(CASE_DIR / "evidence_claims.json")
        cls.actions = load(CASE_DIR / "acquisition_actions.json")
        cls.report = load(CASE_DIR / "motif_report.json")
        cls.screen = load(SCREEN)
        cls.audit = load(EVENT_AUDIT)

    def test_c12_is_a_separate_g1_operational_stress_case(self):
        self.assertEqual("G1_technique", self.config["target_granularity"])
        self.assertEqual("G1_technique", self.config["support_ceiling"])
        self.assertEqual(
            "natural_operational_production_soc_parameter_locked_stress_case",
            self.config["holdout_role"],
        )
        self.assertEqual(5, len(self.claims))
        self.assertEqual(4, len(self.actions))

    def test_actor_campaign_node_remains_a_natural_gap(self):
        node = next(
            item
            for item in self.config["cti_nodes"]
            if item["node_id"] == "N04_actor_campaign_attribution"
        )
        self.assertEqual([], node["required_claim_ids"])
        self.assertIn("No actor label", node["natural_gap"])
        self.assertIn(
            "N04_actor_campaign_attribution",
            self.config["natural_incompleteness"]["unsupported_nodes"],
        )

    def test_vendor_attack_labels_are_not_compiled_as_gold(self):
        for claim in self.claims:
            with self.subTest(claim=claim["claim_id"]):
                self.assertEqual([], claim["mapped_tactic"])
                self.assertEqual([], claim["mapped_technique"])
        context = next(item for item in self.claims if item["claim_id"] == "C12-EC-005")
        self.assertEqual("context", context["evidence_strength"])
        self.assertIn("vendor_oracle", context["tags"])

    def test_event_gate_rejects_product_label_only_multisource_cases(self):
        gates = {
            item["incident_id"]: item["lead_recoverability_pass"]
            for item in self.audit["candidate_gates"]
        }
        self.assertEqual(2, sum(gates.values()))
        self.assertTrue(gates["f10c7270-1228-11ed-99ed-adca11e4059c"])
        self.assertFalse(gates["3390a1e0-02ef-11ee-800b-d36f3c94df97"])
        self.assertEqual(
            "f10c7270-1228-11ed-99ed-adca11e4059c",
            self.audit["decision"]["selected_primary_incident_id"],
        )

    def test_graph_projection_is_not_treated_as_raw_telemetry(self):
        selected = next(
            item
            for item in self.audit["graphml_audits"]
            if item["incident_id"] == "f10c7270-1228-11ed-99ed-adca11e4059c"
        )
        self.assertTrue(selected["projection_only"])
        self.assertEqual(0, selected["telemetry_edge_count"])
        self.assertEqual({"INCIDENT_LINK": 49}, selected["edge_types"])

    def test_all_actions_preserve_intended_recoverable_inequality(self):
        leaking = [
            action["action_id"]
            for action in self.actions
            if RUN_MVP.intended_equals_recoverable_or(self.config, action)
        ]
        self.assertEqual([], leaking)

    def test_screen_and_compile_indices_are_frozen(self):
        selected = next(
            item
            for item in self.screen["candidates"]
            if item["incident_id"] == "f10c7270-1228-11ed-99ed-adca11e4059c"
        )
        self.assertEqual(11888, selected["source_record_index_1based"])
        self.assertEqual("PASS", self.report["event_source_gate"])


if __name__ == "__main__":
    unittest.main()
