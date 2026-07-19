import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "source-candidate-matrix-v0.1.json"
)


class FinalBlindSourceCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_included_source_sum_matches_summary(self):
        sources = [
            source
            for source in self.matrix["sources"]
            if source.get("included_in_current_public_artifact_upper_bound", True)
        ]
        summary = self.matrix["summary"]
        candidate_total = sum(
            source["conservative_unique_chain_upper_bound"] for source in sources
        )
        hash_bound_total = sum(source["hash_bound_intake_cases"] for source in sources)
        target = summary["frozen_operational_target"]

        self.assertEqual(
            candidate_total,
            summary[
                "current_public_metadata_candidate_upper_bound_before_download_hashing_and_overlap_audit"
            ],
        )
        self.assertEqual(
            hash_bound_total,
            summary["current_hash_bound_intake_case_count"],
        )
        self.assertEqual(max(target - candidate_total, 0), summary["current_candidate_gap_to_target"])
        self.assertEqual(
            max(candidate_total - target, 0),
            summary["current_candidate_surplus_over_target"],
        )

    def test_windows_apt_repeated_runs_and_masked_definitions_do_not_expand_n(self):
        source = next(
            source
            for source in self.matrix["sources"]
            if source["source_id"] == "windows-apt-2025"
        )

        self.assertEqual(
            source["paper_reported_scenario_definitions"]
            * source["repeated_executions_per_scenario"],
            source["reported_attack_sessions"],
        )
        self.assertEqual(
            source["paper_reported_scenario_definitions"]
            - source["subset_masked_scenario_definitions_withheld"],
            source["conservative_unique_chain_upper_bound"],
        )

    def test_paper_only_source_is_excluded_from_current_public_artifact_total(self):
        source = next(
            source
            for source in self.matrix["sources"]
            if source["source_id"] == "multi-source-attack-logs-2026"
        )

        self.assertFalse(source["included_in_current_public_artifact_upper_bound"])
        self.assertEqual(
            source["conservative_unique_chain_upper_bound"],
            self.matrix["summary"]["paper_only_additional_scenario_upper_bound"],
        )


if __name__ == "__main__":
    unittest.main()
