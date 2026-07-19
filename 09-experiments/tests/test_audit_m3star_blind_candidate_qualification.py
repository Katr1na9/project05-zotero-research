import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "audit_m3star_blind_candidate_qualification.py"
)
POOL = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "candidate-qualification-pool-v0.1.json"
)


def load_auditor():
    spec = importlib.util.spec_from_file_location(
        "audit_m3star_blind_candidate_qualification", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


AUDITOR = load_auditor()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def complete_report(pool, qualified_total: int):
    remaining = qualified_total
    source_results = []
    cases = []
    case_index = 0
    for quota in pool["source_quotas"]:
        qualified = min(quota["candidate_upper_bound"], remaining)
        remaining -= qualified
        not_qualified = quota["candidate_upper_bound"] - qualified
        source_results.append(
            {
                "source_id": quota["source_id"],
                "risk_tier": quota["risk_tier"],
                "planned_candidate_upper_bound": quota["candidate_upper_bound"],
                "qualified_count": qualified,
                "not_qualified_count": not_qualified,
                "attrition_reason_counts": (
                    {"upper_bound_not_instantiated": not_qualified}
                    if not_qualified
                    else {}
                ),
                "all_available_official_artifacts_audited": True,
            }
        )
        for _ in range(qualified):
            case_index += 1
            cases.append(
                {
                    "qualification_case_id": f"QB-{case_index:03d}",
                    "source_id": quota["source_id"],
                    "source_cluster_id": f"cluster-{quota['source_id']}",
                    "source_release_id": f"release-{quota['source_id']}",
                    "source_artifact_sha256": digest(
                        f"artifact-{quota['source_id']}-{case_index}"
                    ),
                    "scenario_family_sha256": digest(f"scenario-{case_index}"),
                    "attack_chain_definition_sha256": digest(f"chain-{case_index}"),
                    "campaign_execution_sha256": digest(f"execution-{case_index}"),
                    "telemetry_capture_sha256": digest(f"capture-{case_index}"),
                    "original_telemetry_present": True,
                    "multi_stage_attack_chain_present": True,
                    "full_campaign_time_window_included": True,
                    "all_in_scope_campaign_hosts_combined": True,
                    "not_a_host_slice": True,
                    "not_a_time_slice": True,
                    "not_a_mask_variant": True,
                    "not_a_parameter_only_variant": True,
                    "not_used_in_model_development": True,
                    "cost_measurement_scope_supported": True,
                    "ground_truth_sealed": True,
                    "cost_values_sealed_from_model_development": True,
                    "ground_truth_seal_id": f"gt-seal-{case_index:03d}",
                    "cost_measurement_seal_id": f"cost-seal-{case_index:03d}",
                }
            )
    assert remaining == 0
    return {
        "report_id": "curator-qualification-test",
        "status": "curator_qualification_complete",
        "report_created_utc": "2026-07-19T09:00:00Z",
        "candidate_pool_id": pool["pool_id"],
        "candidate_pool_sha256": AUDITOR.sha256(POOL),
        "candidate_upper_bound_audited": 102,
        "curation_and_seal_separation": {
            "curation_team_id": "independent-curator",
            "model_development_team_id": pool["model_development_team_id"],
            "ground_truth_custodian_id": "independent-ground-truth-custodian",
            "teams_are_disjoint": True,
            "curator_blind_to_model_outputs": True,
            "model_developers_blind_to_candidate_payloads": True,
            "ground_truth_custodian_distinct_from_curator_and_model_developer": True,
        },
        "non_consuming_disclosure_boundary": {
            "telemetry_contents_returned_to_model_development": False,
            "labels_returned_to_model_development": False,
            "ground_truth_returned_to_model_development": False,
            "attack_narratives_returned_to_model_development": False,
            "cost_values_returned_to_model_development": False,
            "model_outputs_opened_during_qualification": False,
        },
        "source_artifact_hash_ledger_id": "hash-ledger-test",
        "source_results": source_results,
        "reported_qualified_count": qualified_total,
        "qualified_cases": cases,
        "all_qualified_cases_retained": True,
        "qualification_rules_changed_after_access": False,
        "case_selection_used_model_outputs": False,
    }


class BlindCandidateQualificationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = AUDITOR.load_json(POOL)

    def test_frozen_pool_exactly_matches_matrix_a_and_b_upper_bound(self):
        quotas = AUDITOR.validate_pool(self.pool)
        self.assertEqual(18, len(quotas))
        self.assertEqual(102, sum(item["count"] for item in quotas.values()))
        self.assertEqual(
            11,
            sum(item["count"] for item in quotas.values() if item["risk_tier"] == "A"),
        )
        self.assertEqual(
            91,
            sum(item["count"] for item in quotas.values() if item["risk_tier"] == "B"),
        )

    def test_no_curator_report_defers_search_decision(self):
        audit = AUDITOR.build_waiting_report(self.pool, POOL)
        self.assertEqual("awaiting_independent_curator_report", audit["status"])
        self.assertIsNone(audit["actual_qualified_case_count"])
        self.assertIsNone(audit["source_search_required"])
        self.assertTrue(audit["source_discovery_paused"])
        self.assertFalse(audit["ground_truth_opened"])

    def test_102_qualified_stops_search_and_meets_current_count_gate(self):
        audit = AUDITOR.validate_qualification_report(
            complete_report(self.pool, 102), self.pool, POOL
        )
        self.assertEqual(102, audit["actual_qualified_case_count"])
        self.assertFalse(audit["source_search_required"])
        self.assertTrue(audit["current_protocol_count_gate_met"])
        self.assertFalse(audit["protocol_amendment_required_before_preflight"])

    def test_85_qualified_stops_search_but_requires_count_gate_amendment(self):
        audit = AUDITOR.validate_qualification_report(
            complete_report(self.pool, 85), self.pool, POOL
        )
        self.assertFalse(audit["source_search_required"])
        self.assertFalse(audit["current_protocol_count_gate_met"])
        self.assertTrue(audit["protocol_amendment_required_before_preflight"])
        self.assertEqual(
            "stop_search_and_amend_count_gate_use_all_qualified",
            audit["decision_basis"],
        )

    def test_78_qualified_resumes_search_for_one_more_qualified_case(self):
        audit = AUDITOR.validate_qualification_report(
            complete_report(self.pool, 78), self.pool, POOL
        )
        self.assertTrue(audit["source_search_required"])
        self.assertTrue(audit["all_qualified_cases_to_be_retained"])
        self.assertEqual(
            1, audit["additional_qualified_cases_required_to_reach_power_minimum"]
        )
        self.assertEqual("resume_source_discovery_below_79", audit["decision_basis"])

    def test_role_overlap_is_rejected(self):
        report = complete_report(self.pool, 79)
        report["curation_and_seal_separation"]["curation_team_id"] = (
            report["curation_and_seal_separation"]["model_development_team_id"]
        )
        with self.assertRaisesRegex(ValueError, "identities must be distinct"):
            AUDITOR.validate_qualification_report(report, self.pool, POOL)

    def test_duplicate_telemetry_capture_is_rejected(self):
        report = complete_report(self.pool, 79)
        report["qualified_cases"][1]["telemetry_capture_sha256"] = report[
            "qualified_cases"
        ][0]["telemetry_capture_sha256"]
        with self.assertRaisesRegex(ValueError, "Duplicate qualified-case"):
            AUDITOR.validate_qualification_report(report, self.pool, POOL)

    def test_attrition_reason_count_must_exhaust_not_qualified_count(self):
        report = complete_report(self.pool, 78)
        item = next(
            result
            for result in report["source_results"]
            if result["not_qualified_count"] > 0
        )
        item["attrition_reason_counts"] = {}
        with self.assertRaisesRegex(ValueError, "attrition reasons do not sum"):
            AUDITOR.validate_qualification_report(report, self.pool, POOL)

    def test_curator_template_is_non_consuming_and_has_all_sources(self):
        template = AUDITOR.build_curator_template(self.pool, POOL)
        self.assertEqual("curator_qualification_in_progress", template["status"])
        self.assertEqual(18, len(template["source_results"]))
        self.assertFalse(
            template["non_consuming_disclosure_boundary"][
                "ground_truth_returned_to_model_development"
            ]
        )


if __name__ == "__main__":
    unittest.main()
