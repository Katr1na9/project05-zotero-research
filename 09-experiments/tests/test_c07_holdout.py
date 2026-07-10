import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
C07_DIR = EXPERIMENT_DIR / "real_cases" / "C07-darpa-e5-theia-0515"
R04_PATH = EXPERIMENT_DIR / "real_data" / "darpa_tc_e5" / "ground_truth" / "R04.json"
RUN_MVP_PATH = EXPERIMENT_DIR / "scripts" / "run_mvp.py"
SPEC = importlib.util.spec_from_file_location("run_mvp", RUN_MVP_PATH)
run_mvp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_mvp)


class C07HoldoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = cls.load(C07_DIR / "case_config.json")
        cls.claims = cls.load(C07_DIR / "evidence_claims.json")
        cls.actions = cls.load(C07_DIR / "acquisition_actions.json")
        cls.motif_report = cls.load(C07_DIR / "motif_report.json")
        cls.r04 = cls.load(R04_PATH)

    @staticmethod
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_r04_is_a_true_holdout_with_a_real_trace_boundary(self):
        self.assertFalse(self.config["development_only"])
        self.assertEqual("true_cross_engagement_holdout", self.config["holdout_role"])
        self.assertEqual("ground_truth_and_raw_window_validated", self.r04["evidence_readiness"])
        self.assertEqual(256297, self.r04["raw_validation"]["event_rows_in_locked_window"])
        self.assertIn(
            "189.141.204.211:80 C2 endpoint",
            self.r04["raw_validation"]["trace_unconfirmed_report_observables"],
        )

    def test_every_c07_claim_has_an_observed_representative_uuid(self):
        motifs = self.motif_report["motifs"]
        self.assertEqual(5, self.motif_report["motifs_observed"])
        for claim in self.claims:
            motif = motifs[claim["claim_id"]]
            self.assertEqual("observed", motif["status"])
            self.assertIn("real_pidsmaker", claim["tags"])
            self.assertNotIn("real_cdm", claim["tags"])
            self.assertIn(
                claim["source_pointer"]["record_id"],
                motif["representative_event_uuids"],
            )

    def test_network_evidence_has_a_reliable_host_forensics_fallback(self):
        actions = {action["action_id"]: action for action in self.actions}
        network = actions["C07-AA-001"]
        fallback = actions["C07-AA-002"]
        self.assertEqual(["C07-EC-001"], network["recoverable_claim_ids"])
        self.assertEqual(network["recoverable_claim_ids"], fallback["recoverable_claim_ids"])
        self.assertEqual(
            ["N01_firefox_c2", "N02_binfmt_elevation"],
            network["intended_cti_node_ids"],
        )
        self.assertEqual(network["intended_cti_node_ids"], fallback["intended_cti_node_ids"])
        self.assertFalse(
            run_mvp.intended_equals_recoverable_or(self.config, network)
        )
        self.assertFalse(
            run_mvp.intended_equals_recoverable_or(self.config, fallback)
        )
        self.assertLess(
            self.config["channel_reliability"]["network_telemetry"],
            self.config["channel_reliability"]["host_forensics"],
        )

    def test_m3a_selection_does_not_read_c07_hidden_recovery_outcomes(self):
        hidden = {"C07-EC-001", "C07-EC-002", "C07-EC-003"}
        visible = {
            claim["claim_id"]
            for claim in self.claims
            if claim["claim_id"] not in hidden
        }
        state = run_mvp.build_state(
            self.config,
            self.claims,
            self.actions,
            "c07-information-boundary",
            0,
            "discriminative",
            0.6,
            11,
            visible,
            hidden,
            set(),
            [],
            0.0,
        )
        changed = deepcopy(self.actions)
        for action in changed:
            action["recoverable_claim_ids"] = ["unobservable-counterfactual"]

        first = run_mvp.select_action(
            "project05_m3a_gap_compat",
            self.config,
            self.claims,
            self.actions,
            state,
            visible,
            hidden,
            [],
            11,
        )
        second = run_mvp.select_action(
            "project05_m3a_gap_compat",
            self.config,
            self.claims,
            changed,
            state,
            visible,
            hidden,
            [],
            11,
        )
        self.assertEqual(first["action_id"], second["action_id"])
        self.assertNotEqual("C07-AA-005", first["action_id"])


if __name__ == "__main__":
    unittest.main()
