from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PRODUCT_ARTIFACTS = (
    ROOT / "schemas" / "part-b-si008-dual-track-deny-policy.schema.json",
    ROOT / "schemas" / "part-b-si008-dual-track-deny-record.schema.json",
    ROOT / "schemas" / "part-b-si008-dual-track-deny-manifest.schema.json",
    ROOT / "configs" / "part-b-si008-dual-track-deny-policy-v0.8.yaml",
    ROOT / "configs" / "part-b-si008-dual-track-deny-example-v0.8.yaml",
    ROOT / "configs" / "part-b-si008-dual-track-deny-manifest-v0.8.yaml",
    ROOT / "contracts" / "part-b-si008-dual-track-deny-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-si008-dual-track-deny-v0.8.md",
    ROOT / "src" / "scope" / "part_b_si008_dual_track_deny.py",
    ROOT / "src" / "scope" / "part-b-si008-dual-track-deny-spec-issues.md",
    ROOT / "src" / "scope" / "part-b-b0-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-si008-dual-track-deny-implementation-plan-v0.8-20260724.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)

PART_B_STATUS = "OUTSIDE_AUTHORIZED_TRACK_DENY"
EXPERIMENT_STATUS = "MAY_PROCEED_UNDER_SEPARATE_AUTHORITY"
PB_SI_008_STATUS = "NOT_OPENED"


class PartBSI008DualTrackDenyRuntimeTests(unittest.TestCase):
    def require_product(self) -> None:
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_ARTIFACTS
            if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved artifacts/module: " + ", ".join(missing),
        )

    def evaluate(self, request: dict[str, object]) -> dict[str, object]:
        self.require_product()
        from src.scope.part_b_si008_dual_track_deny import (
            evaluate_dual_track_request,
        )

        return evaluate_dual_track_request(request)

    def assert_frozen_states(self, result: dict[str, object]) -> None:
        self.assertEqual(result["part_b_status"], PART_B_STATUS)
        self.assertEqual(
            result["experiment_track_status"],
            EXPERIMENT_STATUS,
        )
        self.assertEqual(
            result["pb_si_008_status"],
            PB_SI_008_STATUS,
        )

    def test_red_09_experiment_only_request_is_not_interfered_with(
        self,
    ) -> None:
        """RED-09: a non-promotion experiment request remains separate."""
        result = self.evaluate(
            {
                "request_id": "SI008-REQ-001",
                "request_kind": "EXPERIMENT_TRACK_ONLY",
                "promotion_target": "NONE",
                "reference_kind": "ABSTRACT_EXPERIMENT_REFERENCE",
            }
        )
        self.assert_frozen_states(result)
        self.assertEqual(
            result["part_b_decision"],
            "NO_PART_B_ADMISSION_REQUEST",
        )
        self.assertEqual(
            result["experiment_track_decision"],
            "NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED",
        )
        self.assertIs(result["experiment_artifact_accessed"], False)
        self.assertIs(result["llm_invoked"], False)

    def test_red_10_evidence_claim_authority_and_pass_elevation_deny(
        self,
    ) -> None:
        """RED-10: every Part B promotion target fails closed."""
        for target in ("EVIDENCE", "CLAIM", "AUTHORITY", "PASS_CONDITION"):
            with self.subTest(target=target):
                result = self.evaluate(
                    {
                        "request_id": f"SI008-{target}",
                        "request_kind": "PROMOTE_TO_PART_B",
                        "promotion_target": target,
                        "reference_kind": "LLM_OUTPUT_REFERENCE",
                    }
                )
                self.assert_frozen_states(result)
                self.assertEqual(result["part_b_decision"], "DENY")
                self.assertEqual(
                    result["reason_code"],
                    "SI008-DUAL-001_PART_B_ELEVATION_DENIED",
                )

    def test_red_11_output_and_path_references_are_never_read(self) -> None:
        """RED-11: references are classified, never dereferenced."""
        for reference_kind in (
            "LLM_OUTPUT_REFERENCE",
            "EXPERIMENT_PATH_REFERENCE",
        ):
            with self.subTest(reference_kind=reference_kind):
                result = self.evaluate(
                    {
                        "request_id": f"SI008-{reference_kind}",
                        "request_kind": "PROMOTE_TO_PART_B",
                        "promotion_target": "EVIDENCE",
                        "reference_kind": reference_kind,
                    }
                )
                self.assert_frozen_states(result)
                self.assertEqual(result["part_b_decision"], "DENY")
                self.assertIs(result["experiment_artifact_accessed"], False)
                self.assertIs(result["llm_invoked"], False)

    def test_red_12_missing_and_unknown_fields_fail_closed(self) -> None:
        """RED-12: malformed requests deny Part B without stopping experiments."""
        for request in (
            {},
            {
                "request_id": "SI008-UNKNOWN",
                "request_kind": "EXPERIMENT_TRACK_ONLY",
                "promotion_target": "NONE",
                "reference_kind": "ABSTRACT_EXPERIMENT_REFERENCE",
                "unexpected": True,
            },
        ):
            with self.subTest(request=request):
                result = self.evaluate(request)
                self.assert_frozen_states(result)
                self.assertEqual(result["part_b_decision"], "DENY")
                self.assertIn(
                    result["reason_code"],
                    {
                        "SI008-DUAL-002_REQUEST_INVALID",
                        "SI008-DUAL-003_UNKNOWN_FIELD",
                    },
                )
                self.assertNotEqual(
                    result["experiment_track_status"],
                    "STOPPED",
                )

    def test_red_13_same_request_replays_same_record_and_hash(self) -> None:
        """RED-13: local gate records are deterministic."""
        request = {
            "request_id": "SI008-REPLAY",
            "request_kind": "PROMOTE_TO_PART_B",
            "promotion_target": "CLAIM",
            "reference_kind": "LLM_OUTPUT_REFERENCE",
        }
        first = self.evaluate(request)
        second = self.evaluate(deepcopy(request))
        self.assertEqual(first, second)
        self.assertRegex(first["record_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_red_14_adjacent_authorities_remain_deny_or_open(self) -> None:
        """RED-14: the dual-track gate cannot widen adjacent tracks."""
        result = self.evaluate(
            {
                "request_id": "SI008-BOUNDARY",
                "request_kind": "PROMOTE_TO_PART_B",
                "promotion_target": "AUTHORITY",
                "reference_kind": "LLM_OUTPUT_REFERENCE",
            }
        )
        self.assert_frozen_states(result)
        self.assertEqual(result["holdout_release"], "DENY")
        self.assertEqual(result["pb_si_006_download"], "DENY")
        self.assertEqual(
            result["pb_b5_execution"],
            "NOT_ESTABLISHED",
        )
        self.assertEqual(result["pb_b8_si_004"], "OPEN")
        self.assertEqual(result["stop_authority"], "NONE")

    def test_red_15_part_b_deny_is_not_experiment_failure(self) -> None:
        """RED-15: Part B refusal never reports an experiment failure."""
        result = self.evaluate(
            {
                "request_id": "SI008-SEPARATION",
                "request_kind": "PROMOTE_TO_PART_B",
                "promotion_target": "PASS_CONDITION",
                "reference_kind": "EXPERIMENT_PATH_REFERENCE",
            }
        )
        self.assert_frozen_states(result)
        self.assertEqual(result["part_b_decision"], "DENY")
        self.assertEqual(
            result["experiment_track_decision"],
            "NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED",
        )
        self.assertNotIn("experiment_failure", result)
        self.assertNotIn("experiment_stop", result)

    def test_red_16_no_claim_certificate_or_stop_is_emitted(self) -> None:
        """RED-16: SI-008 DENY carries no Part A or Part B authority."""
        result = self.evaluate(
            {
                "request_id": "SI008-NO-STOP",
                "request_kind": "PROMOTE_TO_PART_B",
                "promotion_target": "CLAIM",
                "reference_kind": "LLM_OUTPUT_REFERENCE",
            }
        )
        self.assert_frozen_states(result)
        serialized = json.dumps(result, sort_keys=True)
        self.assertEqual(result["stop_authority"], "NONE")
        for forbidden in (
            "CERTIFIED_STOP",
            '"certificate"',
            '"performance_claim":',
            '"system_status"',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
