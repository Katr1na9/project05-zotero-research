import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
C08_DIR = EXPERIMENT_DIR / "real_cases" / "C08-darpa-e5-clearscope-0515"
R05_PATH = EXPERIMENT_DIR / "real_data" / "darpa_tc_e5" / "ground_truth" / "R05.json"
RUN_MVP_PATH = EXPERIMENT_DIR / "scripts" / "run_mvp.py"
SPEC = importlib.util.spec_from_file_location("run_mvp", RUN_MVP_PATH)
run_mvp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_mvp)


class C08HoldoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = cls.load(C08_DIR / "case_config.json")
        cls.claims = cls.load(C08_DIR / "evidence_claims.json")
        cls.actions = cls.load(C08_DIR / "acquisition_actions.json")
        cls.motif_report = cls.load(C08_DIR / "motif_report.json")
        cls.r05 = cls.load(R05_PATH)

    @staticmethod
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_r05_is_a_second_true_holdout_with_a_real_trace_boundary(self):
        self.assertFalse(self.config["development_only"])
        self.assertEqual(
            "true_cross_engagement_second_holdout",
            self.config["holdout_role"],
        )
        self.assertEqual(
            "ground_truth_and_raw_window_validated",
            self.r05["evidence_readiness"],
        )
        self.assertEqual(694872, self.r05["raw_validation"]["event_rows_in_locked_window"])
        self.assertIn(
            "77.138.117.150:80 Micro APT C2 endpoint",
            self.r05["raw_validation"]["trace_unconfirmed_report_observables"],
        )

    def test_every_c08_claim_has_an_observed_representative_uuid(self):
        motifs = self.motif_report["motifs"]
        self.assertEqual(4, self.motif_report["motifs_observed"])
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
        network = actions["C08-AA-001"]
        fallback = actions["C08-AA-002"]
        self.assertEqual(["C08-EC-001"], network["recoverable_claim_ids"])
        self.assertEqual(network["recoverable_claim_ids"], fallback["recoverable_claim_ids"])
        self.assertEqual(
            ["N01_appstarter_c2", "N02_elevate_msm"],
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

    def test_screencap_claim_is_not_forced_after_elevate(self):
        elevate = self.motif_report["motifs"]["C08-EC-002"]
        screencap = self.motif_report["motifs"]["C08-EC-003"]
        self.assertLess(
            screencap["first_timestamp_nanos"],
            elevate["first_timestamp_nanos"],
        )
        edge_targets = {
            (edge["source"], edge["target"]) for edge in self.config["cti_edges"]
        }
        self.assertIn(("N01_appstarter_c2", "N02_elevate_msm"), edge_targets)
        self.assertIn(("N01_appstarter_c2", "N03_screencap"), edge_targets)
        self.assertNotIn(("N02_elevate_msm", "N03_screencap"), edge_targets)

    def test_m3a_selection_does_not_read_c08_hidden_recovery_outcomes(self):
        hidden = {"C08-EC-001", "C08-EC-002", "C08-EC-003"}
        visible = {
            claim["claim_id"]
            for claim in self.claims
            if claim["claim_id"] not in hidden
        }
        state = run_mvp.build_state(
            self.config,
            self.claims,
            self.actions,
            "c08-information-boundary",
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
        self.assertNotEqual("C08-AA-005", first["action_id"])


if __name__ == "__main__":
    unittest.main()
