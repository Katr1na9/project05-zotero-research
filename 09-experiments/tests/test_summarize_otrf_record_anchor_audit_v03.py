import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "summarize_otrf_record_anchor_audit_v03.py"
)
SPEC = importlib.util.spec_from_file_location("summarize_otrf_anchor_v03", SCRIPT_PATH)
SUMMARIZER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SUMMARIZER)
HASH = "a" * 64


def valid_audit():
    return {
        "audit_id": "project05-otrf-high-precision-record-anchor-audit-v0.3",
        "status": "complete",
        "scope": "isolated curator",
        "eligible_case_count": 1,
        "comparison_scenario_count": 2,
        "max_records_per_anchor": 5,
        "case_reports": [
            {
                "case_id": "C013-final-blind",
                "metadata_sha256": "b" * 64,
                "source_artifact_sha256": ["c" * 64],
                "parsed_record_count": 10,
                "structured_tool_count": 1,
                "attack_mapping_count": 2,
                "candidate_anchor_count": 1,
                "rare_anchor_count": 1,
                "record_anchor_gate_passed": True,
                "explicit_mapping_linkage_present": False,
                "automatic_case_bundle_ready": False,
                "source_specific_blockers": [
                    "no_explicit_tool_to_attack_mapping_linkage"
                ],
                "rare_anchors": [
                    {
                        "anchor_id": "d" * 64,
                        "metadata_source_fields": ["simulation.tools[].name"],
                        "record_hit_count": 1,
                        "cross_scenario_hit_count": 1,
                        "records": [
                            {
                                "case_id": "C013-final-blind",
                                "artifact_id": "e" * 64,
                                "archive_member_id": "f" * 64,
                                "record_ordinal": 3,
                                "line_number": 7,
                                "record_sha256": "1" * 64,
                                "record_hash_basis": "raw_jsonl_line",
                                "matched_field_names": ["Event.Message"],
                            }
                        ],
                    }
                ],
            }
        ],
        "automatic_case_bundle_ready_count": 0,
        "payload_values_disclosed": False,
        "anchor_values_disclosed": False,
        "snippets_disclosed": False,
        "timestamps_or_host_values_disclosed": False,
        "attack_label_values_disclosed": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened": False,
        "planner_or_model_executed": False,
        "one_shot_evaluation_consumed": False,
    }


class OtrfRecordAnchorSummaryTests(unittest.TestCase):
    def summarize(self, audit):
        return SUMMARIZER.summarize_private_audit(
            audit,
            private_audit_sha256=HASH,
        )

    def test_valid_private_audit_is_reduced_to_counts_hashes_and_gates(self):
        summary = self.summarize(valid_audit())
        self.assertEqual(1, summary["record_anchor_gate_pass_count"])
        self.assertEqual(0, summary["mapping_linkage_gate_pass_count"])
        self.assertEqual(0, summary["automatic_case_bundle_ready_count"])
        self.assertFalse(summary["record_locators_returned"])
        serialized = json.dumps(summary)
        self.assertNotIn("rare_anchors", serialized)
        self.assertNotIn("matched_field_names", serialized)
        self.assertNotIn("record_sha256", serialized)
        self.assertFalse(summary["one_shot_evaluation_consumed"])

    def test_unallowlisted_nested_field_is_rejected_not_silently_removed(self):
        audit = valid_audit()
        audit["case_reports"][0]["rare_anchors"][0]["records"][0][
            "snippet"
        ] = "forbidden"
        with self.assertRaisesRegex(ValueError, "exact allowlist"):
            self.summarize(audit)

    def test_true_boundary_flag_is_rejected(self):
        audit = valid_audit()
        audit["one_shot_evaluation_consumed"] = True
        with self.assertRaisesRegex(ValueError, "must remain false"):
            self.summarize(audit)

    def test_inconsistent_automatic_readiness_is_rejected(self):
        audit = valid_audit()
        audit["case_reports"][0]["automatic_case_bundle_ready"] = True
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            self.summarize(audit)

    def test_blocker_set_must_exactly_follow_failed_gates(self):
        audit = valid_audit()
        audit["case_reports"][0]["source_specific_blockers"] = []
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            self.summarize(audit)

    def test_private_audit_is_not_mutated(self):
        audit = valid_audit()
        before = copy.deepcopy(audit)
        self.summarize(audit)
        self.assertEqual(before, audit)


if __name__ == "__main__":
    unittest.main()
