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
SOURCE_DIR = MATRIX.parent / "sources"
NEW_SOURCE_EVIDENCE = (
    SOURCE_DIR / "official-source-evidence-linux-robotdog-ainception-v0.1.json"
)
ATTACKMATE_EVIDENCE = (
    SOURCE_DIR / "official-source-evidence-attackmate-locked-shields-v0.1.json"
)


class FinalBlindSourceCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.new_source_evidence = json.loads(
            NEW_SOURCE_EVIDENCE.read_text(encoding="utf-8")
        )
        cls.attackmate_evidence = json.loads(
            ATTACKMATE_EVIDENCE.read_text(encoding="utf-8")
        )

    def test_included_source_sum_matches_summary(self):
        sources = [
            source
            for source in self.matrix["sources"]
            if source.get("included_in_current_metadata_upper_bound", True)
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

    def test_risk_tier_sums_expose_artifact_and_boundary_attrition(self):
        included = [
            source
            for source in self.matrix["sources"]
            if source.get("included_in_current_metadata_upper_bound", True)
        ]
        summary = self.matrix["summary"]
        tier_totals = {
            tier: sum(
                source["conservative_unique_chain_upper_bound"]
                for source in included
                if source["candidate_risk_tier"] == tier
            )
            for tier in ("A", "B", "C")
        }

        self.assertEqual(
            tier_totals["A"],
            summary["tier_a_high_confidence_candidate_upper_bound"],
        )
        self.assertEqual(
            tier_totals["B"],
            summary["tier_b_boundary_or_overlap_risk_candidate_upper_bound"],
        )
        self.assertEqual(
            tier_totals["C"],
            summary["tier_c_unverified_authoritative_artifact_candidate_upper_bound"],
        )
        self.assertEqual(
            tier_totals["A"] + tier_totals["B"],
            summary["current_authoritative_artifact_verified_candidate_upper_bound"],
        )
        self.assertEqual(
            max(
                summary["current_authoritative_artifact_verified_candidate_upper_bound"]
                - summary["frozen_operational_target"],
                0,
            ),
            summary["authoritative_artifact_verified_candidate_surplus_over_target"],
        )
        self.assertEqual(
            max(
                summary["frozen_operational_target"]
                - summary["tier_a_high_confidence_candidate_upper_bound"],
                0,
            ),
            summary["tier_a_gap_to_operational_target"],
        )

    def test_new_sources_do_not_expand_variants_or_date_partitions(self):
        sources = {source["source_id"]: source for source in self.matrix["sources"]}

        ainception = sources["ainception-storylines"]
        self.assertEqual(15, ainception["reported_attack_sessions"])
        self.assertEqual(3, ainception["reported_storyline_definitions"])
        self.assertEqual(3, ainception["conservative_unique_chain_upper_bound"])
        self.assertEqual("A", ainception["candidate_risk_tier"])

        robotdog = sources["attackmate-robotdog"]
        self.assertEqual(1, robotdog["conservative_unique_chain_upper_bound"])
        self.assertEqual("B", robotdog["candidate_risk_tier"])

        linux_apt = sources["linux-apt-dataset-2024"]
        self.assertEqual(17, linux_apt["dated_csv_partitions"])
        self.assertEqual(5, linux_apt["reported_apt_or_payload_categories"])
        self.assertEqual(0, linux_apt["conservative_unique_chain_upper_bound"])

    def test_source_evidence_stays_non_consuming_and_matches_matrix_summary(self):
        boundary = self.new_source_evidence["inspection_boundary"]
        self.assertFalse(boundary["candidate_ground_truth_opened"])
        self.assertFalse(boundary["candidate_labels_opened"])
        self.assertFalse(boundary["candidate_costs_opened"])
        self.assertFalse(boundary["candidate_model_outputs_opened"])
        self.assertFalse(boundary["telemetry_or_log_payloads_opened"])
        self.assertFalse(boundary["source_archives_downloaded"])

        delta = self.new_source_evidence["count_delta"]
        summary = self.matrix["summary"]
        self.assertEqual(
            delta["updated_public_metadata_upper_bound"],
            summary[
                "current_public_metadata_candidate_upper_bound_before_download_hashing_and_overlap_audit"
            ],
        )
        self.assertEqual(
            delta["authoritative_artifact_verified_upper_bound"],
            summary["current_authoritative_artifact_verified_candidate_upper_bound"],
        )
        self.assertEqual(
            delta["tier_a_high_confidence_upper_bound"],
            summary["tier_a_high_confidence_candidate_upper_bound"],
        )

    def test_attackmate_new_record_replaces_instead_of_expanding_old_version(self):
        attackmate = self.attackmate_evidence["attackmate_evaluation_data"]
        self.assertNotEqual(attackmate["zenodo_record"], attackmate["prior_zenodo_record"])
        self.assertEqual(17639279, attackmate["shared_concept_record"])
        self.assertTrue(
            attackmate["new_record_replaces_prior_version_without_new_scenario_credit"]
        )
        self.assertEqual(3, attackmate["conservative_upper_bound"])

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

    def test_paper_only_source_is_excluded_from_current_metadata_total(self):
        source = next(
            source
            for source in self.matrix["sources"]
            if source["source_id"] == "multi-source-attack-logs-2026"
        )

        self.assertFalse(source["included_in_current_metadata_upper_bound"])
        self.assertEqual(
            source["conservative_unique_chain_upper_bound"],
            self.matrix["summary"]["paper_only_additional_scenario_upper_bound"],
        )


if __name__ == "__main__":
    unittest.main()
