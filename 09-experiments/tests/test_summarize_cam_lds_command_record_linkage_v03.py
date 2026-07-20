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
    / "summarize_cam_lds_command_record_linkage_v03.py"
)
SPEC = importlib.util.spec_from_file_location("summarize_cam_linkage_v03", SCRIPT_PATH)
SUMMARIZER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SUMMARIZER)
HASH = "a" * 64


def valid_audit():
    anchors = []
    for index in range(2):
        digit = str(index + 1)
        anchors.append(
            {
                "anchor_id": digit * 64,
                "mapping_commitment": str(index + 3) * 64,
                "metadata_source_fields": ["commands[].cmd"],
                "record_hit_count": 1,
                "cross_case_hit_count": 1,
                "records": [
                    {
                        "case_id": "C021-final-blind",
                        "archive_id": "5" * 64,
                        "archive_member_id": "6" * 64,
                        "record_ordinal": index + 1,
                        "line_number": index + 7,
                        "record_sha256": str(index + 7) * 64,
                        "record_hash_basis": "raw_log_line",
                        "matched_field_names": ["COMMAND"],
                    }
                ],
            }
        )
    return {
        "audit_id": "project05-cam-lds-command-record-linkage-audit-v0.3",
        "status": "complete",
        "scope": "isolated curator",
        "eligible_case_count": 1,
        "comparison_case_count": 0,
        "maximum_records_per_anchor": 5,
        "minimum_distinct_mapping_commitments": 2,
        "case_reports": [
            {
                "case_id": "C021-final-blind",
                "archive_sha256": "b" * 64,
                "archive_member_count": 20,
                "mapped_command_member_count": 1,
                "mapped_command_object_count": 2,
                "json_member_count": 1,
                "log_member_count": 1,
                "parsed_record_count": 10,
                "structured_command_record_count": 4,
                "candidate_command_anchor_count": 2,
                "rare_unambiguous_anchor_count": 2,
                "distinct_anchored_mapping_count": 2,
                "source_native_mapping_gate_passed": True,
                "command_record_anchor_gate_passed": True,
                "minimum_chain_mapping_gate_passed": True,
                "automatic_case_bundle_ready": True,
                "source_specific_blockers": [],
                "rare_anchors": anchors,
            }
        ],
        "automatic_case_bundle_ready_count": 1,
        "command_values_disclosed": False,
        "telemetry_values_disclosed": False,
        "anchor_values_disclosed": False,
        "attack_mapping_values_disclosed": False,
        "record_snippets_disclosed": False,
        "ground_truth_opened": False,
        "cost_values_opened": False,
        "model_outputs_opened": False,
        "planner_or_model_executed": False,
        "one_shot_evaluation_consumed": False,
    }


class CamLdsLinkageSummaryTests(unittest.TestCase):
    def summarize(self, audit):
        return SUMMARIZER.summarize_private_audit(
            audit,
            private_audit_sha256=HASH,
        )

    def test_valid_audit_returns_only_counts_hashes_gates_and_blockers(self):
        summary = self.summarize(valid_audit())
        self.assertEqual(1, summary["automatic_case_bundle_ready_count"])
        self.assertFalse(summary["record_locators_returned"])
        self.assertFalse(summary["mapping_commitments_returned"])
        serialized = json.dumps(summary)
        for forbidden in (
            '"rare_anchors":',
            '"mapping_commitment":',
            '"record_sha256":',
            '"matched_field_names":',
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertFalse(summary["one_shot_evaluation_consumed"])

    def test_extra_private_field_is_rejected(self):
        audit = valid_audit()
        audit["case_reports"][0]["rare_anchors"][0]["records"][0][
            "snippet"
        ] = "forbidden"
        with self.assertRaisesRegex(ValueError, "exact allowlist"):
            self.summarize(audit)

    def test_true_boundary_flag_is_rejected(self):
        audit = valid_audit()
        audit["command_values_disclosed"] = True
        with self.assertRaisesRegex(ValueError, "must remain false"):
            self.summarize(audit)

    def test_single_distinct_mapping_cannot_pass_chain_gate(self):
        audit = valid_audit()
        case = audit["case_reports"][0]
        case["rare_anchors"][1]["mapping_commitment"] = case["rare_anchors"][0][
            "mapping_commitment"
        ]
        with self.assertRaisesRegex(ValueError, "distinct_anchored_mapping_count"):
            self.summarize(audit)

    def test_blockers_must_match_failed_gates(self):
        audit = valid_audit()
        audit["case_reports"][0]["source_specific_blockers"] = [
            "no_source_native_attack_mapping"
        ]
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            self.summarize(audit)

    def test_input_is_not_mutated(self):
        audit = valid_audit()
        before = copy.deepcopy(audit)
        self.summarize(audit)
        self.assertEqual(before, audit)


if __name__ == "__main__":
    unittest.main()
