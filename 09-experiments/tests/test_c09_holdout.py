import csv
import hashlib
import importlib.util
import json
import statistics
import unittest
from copy import deepcopy
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
C09_DIR = EXPERIMENT_DIR / "real_cases" / "C09-darpa-optc-sysclient0201-0923"
DATA_DIR = EXPERIMENT_DIR / "real_data" / "darpa_optc"
RESULT_DIR = EXPERIMENT_DIR / "results" / "c09_holdout_m3a"
R06_PATH = DATA_DIR / "ground_truth" / "R06.json"
EXTRACTED_PATH = DATA_DIR / "extracted" / "R06_sysclient0201_window.jsonl"
RUN_MVP_PATH = EXPERIMENT_DIR / "scripts" / "run_mvp.py"
SPEC = importlib.util.spec_from_file_location("run_mvp_c09", RUN_MVP_PATH)
run_mvp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_mvp)


class C09HoldoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = cls.load(C09_DIR / "case_config.json")
        cls.claims = cls.load(C09_DIR / "evidence_claims.json")
        cls.actions = cls.load(C09_DIR / "acquisition_actions.json")
        cls.motif_report = cls.load(C09_DIR / "motif_report.json")
        cls.r06 = cls.load(R06_PATH)
        cls.manifest = cls.load(DATA_DIR / "manifest.json")
        cls.extraction = cls.load(DATA_DIR / "derived" / "R06_extraction_summary.json")
        cls.summary = cls.load(
            RESULT_DIR / "c09-darpa-optc-sysclient0201-0923_mvp_summary.json"
        )

    @staticmethod
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_r06_is_the_third_true_holdout_with_a_verified_source(self):
        self.assertFalse(self.config["development_only"])
        self.assertEqual(
            "true_cross_engagement_third_holdout",
            self.config["holdout_role"],
        )
        self.assertEqual(
            "compiled_as_C09_event_backed_holdout",
            self.r06["evidence_readiness"],
        )
        self.assertEqual("phase1_c09_compiled_and_freeze_eval", self.manifest["phase"])
        source = next(
            source
            for source in self.manifest["sources"]
            if source["source_id"] == "optc_ecar_23sep19_aia_201_225_last"
        )
        self.assertEqual("available_local_verified", source["download_status"])
        self.assertEqual(2217842713, source["size_bytes"])
        self.assertEqual(
            "FAF181CBF7E4F00F9C912DA3EC2D7BC19667E0249CE7A297D0D2A7BE9BEE5FD7",
            source["sha256"],
        )

    def test_r06_extraction_uses_the_exact_locked_hostname(self):
        self.assertEqual("exact", self.extraction["hostname_match_mode"])
        self.assertEqual(
            ["SysClient0201.systemia.com"],
            self.extraction["hostnames"],
        )
        self.assertEqual(753973, self.extraction["rows_selected"])
        self.assertEqual(
            {"SysClient0201.systemia.com": 753973},
            self.extraction["selected_host_counts"],
        )

    def test_every_c09_claim_has_an_observed_representative_event(self):
        motifs = self.motif_report["motifs"]
        self.assertEqual(5, self.motif_report["motifs_observed"])
        self.assertEqual(753973, self.motif_report["events_scanned"])
        for claim in self.claims:
            motif = motifs[claim["claim_id"]]
            self.assertEqual("observed", motif["status"])
            self.assertIn("real_ecar", claim["tags"])
            self.assertIn(
                claim["source_pointer"]["record_id"],
                motif["representative_event_ids"],
            )

    def test_network_evidence_has_a_reliable_host_forensics_fallback(self):
        actions = {action["action_id"]: action for action in self.actions}
        network = actions["C09-AA-001"]
        fallback = actions["C09-AA-002"]
        self.assertEqual(["C09-EC-001"], network["recoverable_claim_ids"])
        self.assertEqual(network["recoverable_claim_ids"], fallback["recoverable_claim_ids"])
        self.assertEqual(network["intended_cti_node_ids"], fallback["intended_cti_node_ids"])
        self.assertFalse(run_mvp.intended_equals_recoverable_or(self.config, network))
        self.assertFalse(run_mvp.intended_equals_recoverable_or(self.config, fallback))
        self.assertLess(
            self.config["channel_reliability"]["network_telemetry"],
            self.config["channel_reliability"]["host_forensics"],
        )

    def test_m3a_selection_does_not_read_c09_hidden_recovery_outcomes(self):
        hidden = {"C09-EC-001", "C09-EC-002", "C09-EC-003", "C09-EC-004"}
        visible = {
            claim["claim_id"]
            for claim in self.claims
            if claim["claim_id"] not in hidden
        }
        state = run_mvp.build_state(
            self.config,
            self.claims,
            self.actions,
            "c09-information-boundary",
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
        self.assertNotEqual("C09-AA-006", first["action_id"])

    def test_csv_reproduces_frozen_primary_results(self):
        csv_path = RESULT_DIR / "c09-darpa-optc-sysclient0201-0923_mvp_results.csv"
        with csv_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        expected = {
            "oracle_optimal": (1.0, 4.1333, 0.0),
            "project05_m2": (1.0, 4.7556, 0.6222),
            "project05_m3a_gap_compat": (1.0, 5.2444, 1.1111),
        }
        for planner, (success_rate, mean_cost, mean_regret) in expected.items():
            with self.subTest(planner=planner):
                selected = [row for row in rows if row["planner"] == planner]
                successes = [row for row in selected if row["reached_target"] == "1"]
                costs = [float(row["cost_to_target"]) for row in successes]
                regrets = [
                    float(row["cost_regret_vs_oracle"])
                    for row in selected
                    if row["cost_regret_vs_oracle"]
                ]
                self.assertEqual(45, len(selected))
                self.assertEqual(success_rate, len(successes) / len(selected))
                self.assertAlmostEqual(mean_cost, statistics.mean(costs), places=4)
                self.assertAlmostEqual(mean_regret, statistics.mean(regrets), places=4)
                self.assertEqual(mean_cost, self.summary[planner]["mean_cost_to_target"])

    @unittest.skipUnless(EXTRACTED_PATH.is_file(), "requires local R06 window")
    def test_local_r06_window_contains_all_representative_event_ids(self):
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
        self.assertEqual(753973, rows)
        self.assertEqual({}, remaining)
        self.assertEqual(self.extraction["output_sha256"], hasher.hexdigest().upper())


if __name__ == "__main__":
    unittest.main()
