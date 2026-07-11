import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
C10_DIR = EXPERIMENT_DIR / "real_cases" / "C10-darpa-optc-sysclient0351-0925"
DATA_DIR = EXPERIMENT_DIR / "real_data" / "darpa_optc"
RESULT_DIR = EXPERIMENT_DIR / "results" / "c10_holdout_m3a"
XGB_DIR = EXPERIMENT_DIR / "results" / "xgboost_c01_c06_train_c07_c10_test"
EXTRACTED_PATH = DATA_DIR / "extracted" / "R07_sysclient0351_window.jsonl"
RUN_MVP_PATH = EXPERIMENT_DIR / "scripts" / "run_mvp.py"
SPEC = importlib.util.spec_from_file_location("run_mvp_c10", RUN_MVP_PATH)
run_mvp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_mvp)


class C10HoldoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = cls.load(C10_DIR / "case_config.json")
        cls.claims = cls.load(C10_DIR / "evidence_claims.json")
        cls.actions = cls.load(C10_DIR / "acquisition_actions.json")
        cls.motif_report = cls.load(C10_DIR / "motif_report.json")
        cls.r07 = cls.load(DATA_DIR / "ground_truth" / "R07.json")
        cls.manifest = cls.load(DATA_DIR / "manifest.json")
        cls.extraction = cls.load(DATA_DIR / "derived" / "R07_extraction_summary.json")
        cls.mvp_summary = cls.load(
            RESULT_DIR / "c10-darpa-optc-sysclient0351-0925_mvp_summary.json"
        )
        cls.xgb_summary = cls.load(XGB_DIR / "xgboost_experiment_summary.json")

    @staticmethod
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_verified_source_and_exact_locked_extraction(self):
        source = next(
            item
            for item in self.manifest["sources"]
            if item["source_id"] == "optc_ecar_25sept_aia_351_375_last"
        )
        self.assertEqual("available_local_verified", source["download_status"])
        self.assertEqual(1610345177, source["size_bytes"])
        self.assertEqual(source["sha256"], self.extraction["input_sha256"][0])
        self.assertEqual("exact", self.extraction["hostname_match_mode"])
        self.assertEqual(["Sysclient0351.systemia.com"], self.extraction["hostnames"])
        self.assertEqual(27832841, self.extraction["rows_scanned"])
        self.assertEqual(37301, self.extraction["rows_selected"])
        self.assertEqual(0, self.extraction["rows_bad_json"])
        self.assertEqual(0, self.extraction["rows_bad_timestamp"])

    def test_all_attack_stages_and_benign_context_are_event_backed(self):
        self.assertEqual(5, self.motif_report["motifs_requested"])
        self.assertEqual(5, self.motif_report["motifs_observed"])
        self.assertEqual(37301, self.motif_report["events_scanned"])
        for claim in self.claims:
            motif = self.motif_report["motifs"][claim["claim_id"]]
            self.assertEqual("observed", motif["status"])
            self.assertIn("real_ecar", claim["tags"])
            self.assertIn(
                claim["source_pointer"]["record_id"],
                motif["representative_event_ids"],
            )

    def test_remote_thread_migration_matches_locked_ground_truth(self):
        migration = self.motif_report["motifs"]["C10-EC-004"]
        self.assertEqual(1, migration["matched_event_count"])
        self.assertEqual(
            ["789fe2c1-c59c-4ae6-933d-1bac24ff21e9"],
            migration["representative_event_ids"],
        )
        self.assertIn("PID 1932", self.r07["ground_truth_summary"])
        self.assertIn("PID 1256", self.r07["ground_truth_summary"])

    def test_action_intent_does_not_reveal_hidden_recovery(self):
        for action in self.actions:
            with self.subTest(action=action["action_id"]):
                self.assertFalse(
                    run_mvp.intended_equals_recoverable_or(self.config, action)
                )
        actions = {action["action_id"]: action for action in self.actions}
        self.assertEqual(
            actions["C10-AA-001"]["recoverable_claim_ids"],
            actions["C10-AA-002"]["recoverable_claim_ids"],
        )
        self.assertLess(
            self.config["channel_reliability"]["network_telemetry"],
            self.config["channel_reliability"]["host_forensics"],
        )

    def test_frozen_mvp_exposes_m3a_premature_stop(self):
        self.assertEqual(1.0, self.mvp_summary["oracle_optimal"]["success_rate"])
        self.assertEqual(1.0, self.mvp_summary["project05_m2"]["success_rate"])
        self.assertEqual(4.5556, self.mvp_summary["project05_m2"]["mean_cost_to_target"])
        self.assertEqual(0.8, self.mvp_summary["project05_m3a_gap_compat"]["success_rate"])
        self.assertEqual(
            0.2,
            self.mvp_summary["project05_m3a_gap_compat"]["premature_stop_rate"],
        )

    def test_xgboost_v02_keeps_training_fixed_and_adds_c10(self):
        self.assertEqual("project05-xgboost-action-value-v0.2-c10", self.xgb_summary["experiment_id"])
        self.assertEqual(6, len(self.xgb_summary["train_case_ids"]))
        self.assertEqual(1845, self.xgb_summary["train_row_count"])
        self.assertEqual(4, len(self.xgb_summary["test_case_ids"]))
        self.assertEqual(990, self.xgb_summary["test_row_count"])
        c10 = self.xgb_summary["policy_summary"]["by_case_planner"][self.config["case_id"]]
        self.assertEqual(1.0, c10["project05_xgboost_policy"]["success_rate"])
        self.assertEqual(5.0444, c10["project05_xgboost_policy"]["mean_cost_to_target"])
        self.assertEqual(5.4444, c10["project05_m3b_policy"]["mean_cost_to_target"])
        self.assertEqual(4.5556, c10["project05_m2"]["mean_cost_to_target"])

    @unittest.skipUnless(EXTRACTED_PATH.is_file(), "requires local R07 window")
    def test_local_window_contains_all_representative_event_ids(self):
        expected_ids = {
            event_id
            for motif in self.motif_report["motifs"].values()
            for event_id in motif["representative_event_ids"]
        }
        remaining = {event_id.encode(): event_id for event_id in expected_ids}
        hasher = hashlib.sha256()
        rows = 0
        with EXTRACTED_PATH.open("rb") as handle:
            for line in handle:
                hasher.update(line)
                rows += 1
                for needle, event_id in list(remaining.items()):
                    if needle in line and json.loads(line).get("id") == event_id:
                        remaining.pop(needle)
        self.assertEqual(37301, rows)
        self.assertEqual({}, remaining)
        self.assertEqual(self.extraction["output_sha256"], hasher.hexdigest().upper())


if __name__ == "__main__":
    unittest.main()
