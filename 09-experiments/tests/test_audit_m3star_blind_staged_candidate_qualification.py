import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "audit_m3star_blind_staged_candidate_qualification.py"
)
SCHEMA = (
    REPO_ROOT
    / "09-experiments"
    / "data_schema"
    / "m3star_blind_staged_candidate_qualification.schema.json"
)
AMENDMENT = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "staged-acquisition-protocol-amendment-v0.2.json"
)
TEMPLATE = (
    AMENDMENT.parent
    / "curator-staged-candidate-qualification-report.template.json"
)


def load_auditor():
    spec = importlib.util.spec_from_file_location(
        "audit_m3star_blind_staged_candidate_qualification", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


AUDITOR = load_auditor()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_case(case_index: int, source_id: str, candidate_key):
    key = candidate_key or "aggregate"
    return {
        "qualification_case_id": f"QB-{case_index:03d}",
        "source_id": source_id,
        "candidate_key": candidate_key,
        "source_cluster_id": f"cluster-{source_id}-{key}",
        "source_release_id": f"release-{source_id}-{key}",
        "source_artifact_sha256": digest(
            f"artifact-{source_id}-{key}-{case_index}"
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


def checkpoint_report(amendment, phase_1_qualified: int, sequential_statuses=()):
    if not 0 <= phase_1_qualified <= 81:
        raise ValueError("phase_1_qualified outside Phase-1 bounds")
    remaining = phase_1_qualified
    cases = []
    phase_1_results = []
    case_index = 0
    for allocation in amendment["phases"][0]["allocations"]:
        planned = allocation["slots"]
        qualified = min(planned, remaining)
        remaining -= qualified
        not_qualified = planned - qualified
        phase_1_results.append(
            {
                "source_id": allocation["source_id"],
                "candidate_key": allocation.get("candidate_key"),
                "planned_candidate_slots": planned,
                "qualified_count": qualified,
                "not_qualified_count": not_qualified,
                "attrition_reason_counts": (
                    {"upper_bound_not_instantiated": not_qualified}
                    if not_qualified
                    else {}
                ),
                "all_planned_slots_audited": True,
            }
        )
        for _ in range(qualified):
            case_index += 1
            cases.append(
                make_case(
                    case_index,
                    allocation["source_id"],
                    allocation.get("candidate_key"),
                )
            )
    assert remaining == 0

    sequence = []
    frozen = [
        (phase["phase"], index, candidate)
        for phase in amendment["phases"][1:]
        for index, candidate in enumerate(phase["candidate_order"], start=1)
    ]
    for status, (phase, index, candidate) in zip(sequential_statuses, frozen):
        qualified = status == "qualified"
        sequence.append(
            {
                "phase": phase,
                "phase_candidate_index": index,
                "source_id": candidate["source_id"],
                "candidate_key": candidate["candidate_key"],
                "qualification_status": status,
                "attrition_reason": (
                    None if qualified else "incomplete_campaign_boundary"
                ),
            }
        )
        if qualified:
            case_index += 1
            cases.append(
                make_case(
                    case_index,
                    candidate["source_id"],
                    candidate["candidate_key"],
                )
            )

    sequential_qualified = sum(status == "qualified" for status in sequential_statuses)
    sequential_not_qualified = len(sequential_statuses) - sequential_qualified
    audited = 81 + len(sequential_statuses)
    qualified = phase_1_qualified + sequential_qualified
    not_qualified = 81 - phase_1_qualified + sequential_not_qualified
    return {
        "report_id": "curator-staged-checkpoint-test",
        "status": "curator_staged_qualification_checkpoint",
        "report_created_utc": "2026-07-19T10:00:00Z",
        "amendment_id": amendment["amendment_id"],
        "amendment_sha256": AUDITOR.sha256(AMENDMENT),
        "curation_and_seal_separation": {
            "curation_team_id": "independent-curator",
            "model_development_team_id": "project05-model-development",
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
        "phase_1_source_results": phase_1_results,
        "sequential_candidate_results": sequence,
        "audited_candidate_count": audited,
        "reported_qualified_count": qualified,
        "reported_not_qualified_count": not_qualified,
        "unaudited_reserve_count": 95 - audited,
        "qualified_cases": cases,
        "all_qualified_cases_retained": True,
        "qualification_rules_changed_after_access": False,
        "case_selection_used_model_outputs": False,
        "stage_transition_used_only_permitted_fields": True,
        "within_case_conditions_counted_as_independent_cases": False,
    }


class BlindStagedCandidateQualificationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.amendment = AUDITOR.load_json(AMENDMENT)

    def test_frozen_amendment_has_81_plus_8_plus_6_slots_and_hash_anchors(self):
        plan = AUDITOR.validate_amendment(self.amendment)
        self.assertEqual(81, sum(item[2] for item in AUDITOR.EXPECTED_PHASE_1))
        self.assertEqual(14, len(plan["sequential_candidates"]))
        self.assertEqual(
            95,
            sum(item[2] for item in AUDITOR.EXPECTED_PHASE_1)
            + len(plan["sequential_candidates"]),
        )
        self.assertEqual(
            self.amendment["staged_qualification_contract"]["schema_sha256"],
            AUDITOR.sha256(SCHEMA),
        )
        self.assertEqual(
            self.amendment["staged_qualification_contract"]["auditor_sha256"],
            AUDITOR.sha256(SCRIPT),
        )

    def test_schema_is_valid_json_and_freezes_95_slot_bounds(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(95, schema["properties"]["audited_candidate_count"]["maximum"])
        self.assertEqual(14, schema["properties"]["unaudited_reserve_count"]["maximum"])
        self.assertFalse(
            schema["properties"][
                "within_case_conditions_counted_as_independent_cases"
            ]["const"]
        )

    def test_waiting_report_does_not_claim_any_audited_or_failed_slot(self):
        audit = AUDITOR.build_waiting_report(self.amendment, AMENDMENT)
        self.assertEqual("awaiting_independent_curator_phase_1_report", audit["status"])
        self.assertEqual(0, audit["audited_candidate_count"])
        self.assertIsNone(audit["actual_not_qualified_count"])
        self.assertEqual(95, audit["unaudited_reserve_count"])

    def test_phase_1_with_79_qualified_stops_and_leaves_14_reserve_slots(self):
        audit = AUDITOR.validate_qualification_report(
            checkpoint_report(self.amendment, 79), self.amendment, AMENDMENT
        )
        self.assertEqual("qualification_complete", audit["status"])
        self.assertEqual("stop_after_phase_1_minimum_reached", audit["decision_basis"])
        self.assertEqual(81, audit["audited_candidate_count"])
        self.assertEqual(79, audit["independent_case_count"])
        self.assertEqual(2, audit["actual_not_qualified_count"])
        self.assertEqual(14, audit["unaudited_reserve_count"])
        self.assertFalse(audit["unaudited_reserve_slots_counted_as_failures"])
        self.assertEqual(45, audit["within_case_repeated_conditions"])
        self.assertFalse(audit["within_case_conditions_inflate_independent_n"])

    def test_phase_1_with_78_qualified_requests_first_phase_2_candidate(self):
        audit = AUDITOR.validate_qualification_report(
            checkpoint_report(self.amendment, 78), self.amendment, AMENDMENT
        )
        self.assertEqual("qualification_checkpoint_continue_acquisition", audit["status"])
        self.assertIsNone(audit["source_search_required"])
        self.assertEqual(3, audit["actual_not_qualified_count"])
        self.assertEqual(14, audit["unaudited_reserve_count"])
        self.assertEqual("russellmitchell", audit["next_frozen_candidate"]["candidate_key"])

    def test_first_phase_2_candidate_reaching_79_stops_immediately(self):
        audit = AUDITOR.validate_qualification_report(
            checkpoint_report(self.amendment, 78, ["qualified"]),
            self.amendment,
            AMENDMENT,
        )
        self.assertEqual("qualification_complete", audit["status"])
        self.assertEqual(82, audit["audited_candidate_count"])
        self.assertEqual(13, audit["unaudited_reserve_count"])
        self.assertEqual(
            "stop_at_first_sequential_candidate_reaching_79",
            audit["decision_basis"],
        )

    def test_extra_candidate_after_reaching_79_is_rejected(self):
        report = checkpoint_report(
            self.amendment, 78, ["qualified", "not_qualified"]
        )
        with self.assertRaisesRegex(ValueError, "continued after the 79-case"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_non_prefix_candidate_result_is_rejected(self):
        report = checkpoint_report(self.amendment, 70, ["not_qualified"])
        report["sequential_candidate_results"][0]["candidate_key"] = "santos"
        with self.assertRaisesRegex(ValueError, "exact frozen-order prefix"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_phase_3_cannot_begin_before_all_phase_2_candidates(self):
        report = checkpoint_report(self.amendment, 70, ["not_qualified"])
        report["sequential_candidate_results"][0].update(
            {
                "phase": 3,
                "phase_candidate_index": 1,
                "source_id": "apt-sandworm-dataset",
                "candidate_key": "campaign",
            }
        )
        with self.assertRaisesRegex(ValueError, "exact frozen-order prefix"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_all_95_below_79_is_the_only_below_minimum_completion(self):
        audit = AUDITOR.validate_qualification_report(
            checkpoint_report(self.amendment, 60, ["not_qualified"] * 14),
            self.amendment,
            AMENDMENT,
        )
        self.assertEqual("qualification_complete", audit["status"])
        self.assertEqual(95, audit["audited_candidate_count"])
        self.assertEqual(0, audit["unaudited_reserve_count"])
        self.assertTrue(audit["source_search_required"])
        self.assertEqual(
            "resume_metadata_only_source_discovery_after_95_below_79",
            audit["decision_basis"],
        )

    def test_report_cannot_count_unaudited_reserve_as_not_qualified(self):
        report = checkpoint_report(self.amendment, 78)
        report["reported_not_qualified_count"] += report["unaudited_reserve_count"]
        with self.assertRaisesRegex(ValueError, "reported_not_qualified_count"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_within_case_conditions_cannot_inflate_independent_sample_size(self):
        report = checkpoint_report(self.amendment, 79)
        report["within_case_conditions_counted_as_independent_cases"] = True
        with self.assertRaisesRegex(ValueError, "must be false"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_duplicate_qualified_telemetry_capture_is_rejected(self):
        report = checkpoint_report(self.amendment, 79)
        report["qualified_cases"][1]["telemetry_capture_sha256"] = report[
            "qualified_cases"
        ][0]["telemetry_capture_sha256"]
        with self.assertRaisesRegex(ValueError, "Duplicate qualified-case"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_role_overlap_is_rejected(self):
        report = checkpoint_report(self.amendment, 79)
        report["curation_and_seal_separation"]["curation_team_id"] = (
            "project05-model-development"
        )
        with self.assertRaisesRegex(ValueError, "identities must be distinct"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_unapproved_top_level_disclosure_field_is_rejected(self):
        report = checkpoint_report(self.amendment, 79)
        report["telemetry_excerpt"] = "must-never-cross-the-boundary"
        with self.assertRaisesRegex(ValueError, "disclosure-safe contract"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_unapproved_case_ground_truth_field_is_rejected(self):
        report = checkpoint_report(self.amendment, 79)
        report["qualified_cases"][0]["ground_truth_label"] = "sealed"
        with self.assertRaisesRegex(ValueError, "disclosure-safe contract"):
            AUDITOR.validate_qualification_report(report, self.amendment, AMENDMENT)

    def test_phase_2_order_drift_is_rejected_even_before_any_report(self):
        amendment = copy.deepcopy(self.amendment)
        order = amendment["phases"][1]["candidate_order"]
        order[0], order[1] = order[1], order[0]
        with self.assertRaisesRegex(ValueError, "Phase-2 candidate order"):
            AUDITOR.validate_amendment(amendment)

    def test_template_contains_all_phase_1_allocations_but_no_claimed_outcomes(self):
        template = AUDITOR.build_curator_template(self.amendment, AMENDMENT)
        self.assertEqual(template, AUDITOR.load_json(TEMPLATE))
        self.assertEqual(12, len(template["phase_1_source_results"]))
        self.assertEqual([], template["sequential_candidate_results"])
        self.assertIsNone(template["audited_candidate_count"])
        self.assertFalse(
            template["within_case_conditions_counted_as_independent_cases"]
        )


if __name__ == "__main__":
    unittest.main()
