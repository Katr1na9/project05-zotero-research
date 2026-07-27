"""Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation."""

from __future__ import annotations

from copy import deepcopy
import unittest

from src.scope.part_b_si008_dual_track_deny import (
    evaluate_dual_track_request,
)
from src.scope.part_b_si008_named_open_path_a_evidence_candidacy import (
    ALLOW_DECISION,
    HARD_BAN,
    NAMED_TARGET_ID,
    REFERENCE_PAIRS,
    evaluate_si008_named_open_request,
)


class PartBSI008NamedOpenEvidenceCandidacyRuntimeTests(
    unittest.TestCase
):
    def named_request(self, reference_kind, **overrides):
        pair = REFERENCE_PAIRS[reference_kind]
        request = {
            "request_id": "PB-SI008-NAMED-001",
            "request_kind": "PROMOTE_TO_PART_B_NAMED_TARGET",
            "promotion_target": "EVIDENCE",
            "reference_kind": reference_kind,
            "named_target_id": NAMED_TARGET_ID,
            "source_schema_version": pair["source_schema_version"],
            "source_schema_sha256": pair["source_schema_sha256"],
            "consumer_contract_id": pair["consumer_contract_id"],
            "consumer_contract_sha256": pair[
                "consumer_contract_sha256"
            ],
            "package_sha256": "a" * 64,
            "structural_validation_receipt_sha256": "b" * 64,
            "record_class": "public_evidence_declaration",
            "claim_id": None,
            "claim_id_state": "not_minted",
            "admission_state": "not_admitted",
            "structural_validation_status": (
                "PASS_STRUCTURAL_ONLY_NO_INGESTION_AUTHORITY"
            ),
            "requested_authority_scope": (
                "EVIDENCE_STRUCTURAL_CANDIDACY_ONLY"
            ),
            "reference_access_mode": (
                "CLASSIFY_DECLARED_REFERENCE_ONLY_NO_DEREFERENCE"
            ),
        }
        request.update(overrides)
        return request

    def evaluate(self, request):
        return evaluate_si008_named_open_request(request)

    def test_green_08_exact_v0_1_pair_allows_named_candidacy_only(self):
        request = self.named_request(
            "PATH_A_EVIDENCE_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE"
        )
        result = self.evaluate(request)
        self._assert_qualified_allow(result)

    def test_green_09_exact_v0_2_pair_allows_named_candidacy_only(self):
        request = self.named_request(
            "PATH_A_EVIDENCE_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE"
        )
        result = self.evaluate(request)
        self._assert_qualified_allow(result)

    def test_green_10_claim_authority_and_pass_condition_are_denied(self):
        for target in ("CLAIM", "AUTHORITY", "PASS_CONDITION"):
            with self.subTest(target=target):
                request = self.named_request(
                    "PATH_A_EVIDENCE_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE",
                    promotion_target=target,
                )
                result = self.evaluate(request)
                self.assertEqual("DENY", result["decision"])
                self.assertEqual(
                    "SI008-NAMED-002_PROMOTION_TARGET_NOT_AUTHORIZED",
                    result["reason_code"],
                )
                self._assert_no_elevation(result)

    def test_green_11_wrong_missing_unknown_or_mismatched_request_denies(self):
        base = self.named_request(
            "PATH_A_EVIDENCE_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE"
        )
        missing = deepcopy(base)
        missing.pop("package_sha256")
        unknown = deepcopy(base)
        unknown["extra"] = "DENY"
        cases = (
            {
                **base,
                "source_schema_sha256": "0" * 64,
            },
            {
                **base,
                "package_sha256": "A" * 64,
            },
            {
                **base,
                "reference_kind": "*",
            },
            {
                **base,
                "claim_id": "pkg_minted_forbidden",
            },
            {
                **base,
                "structural_validation_status": "PASS",
            },
            missing,
            unknown,
        )
        for request in cases:
            with self.subTest(request=request):
                result = self.evaluate(request)
                self.assertEqual("DENY", result["decision"])
                self.assertEqual(
                    "SI008-NAMED-003_REQUEST_NOT_QUALIFIED",
                    result["reason_code"],
                )
                self._assert_no_elevation(result)

    def test_green_12_legacy_promotion_delegates_and_stays_not_opened(self):
        request = {
            "request_id": "SI008-LEGACY-PROMOTION",
            "request_kind": "PROMOTE_TO_PART_B",
            "promotion_target": "EVIDENCE",
            "reference_kind": "LLM_OUTPUT_REFERENCE",
        }
        expected = evaluate_dual_track_request(deepcopy(request))
        actual = self.evaluate(request)
        self.assertEqual(expected, actual)
        self.assertEqual("DENY", actual["part_b_decision"])
        self.assertEqual("NOT_OPENED", actual["pb_si_008_status"])

    def test_green_13_experiment_only_request_is_not_interfered_with(self):
        request = {
            "request_id": "SI008-LEGACY-EXPERIMENT",
            "request_kind": "EXPERIMENT_TRACK_ONLY",
            "promotion_target": "NONE",
            "reference_kind": "ABSTRACT_EXPERIMENT_REFERENCE",
        }
        expected = evaluate_dual_track_request(deepcopy(request))
        actual = self.evaluate(request)
        self.assertEqual(expected, actual)
        self.assertEqual(
            "NO_PART_B_ADMISSION_REQUEST",
            actual["part_b_decision"],
        )
        self.assertEqual("NOT_OPENED", actual["pb_si_008_status"])
        self.assertEqual(
            "MAY_PROCEED_UNDER_SEPARATE_AUTHORITY",
            actual["experiment_track_status"],
        )

    def test_green_14_same_named_request_replays_same_record_and_hash(self):
        request = self.named_request(
            "PATH_A_EVIDENCE_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE"
        )
        before = deepcopy(request)
        first = self.evaluate(request)
        second = self.evaluate(deepcopy(request))
        self.assertEqual(first, second)
        self.assertEqual(first["record_hash"], second["record_hash"])
        self.assertEqual(first["hash"], second["hash"])
        self.assertEqual(before, request)

    def test_green_15_named_records_never_dereference_or_emit_authority(self):
        allowed = self.evaluate(
            self.named_request(
                "PATH_A_EVIDENCE_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE"
            )
        )
        denied = self.evaluate(
            self.named_request(
                "PATH_A_EVIDENCE_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE",
                source_schema_version="unknown",
            )
        )
        for result in (allowed, denied):
            with self.subTest(decision=result["decision"]):
                self.assertFalse(result["package_dereferenced"])
                self.assertFalse(
                    result["validation_receipt_dereferenced"]
                )
                self.assertFalse(result["experiment_artifact_accessed"])
                self.assertFalse(result["llm_invoked"])
                self._assert_no_elevation(result)

    def _assert_qualified_allow(self, result):
        self.assertEqual(ALLOW_DECISION, result["decision"])
        self.assertEqual(
            "OPENED_FOR_NAMED_TARGET_ONLY",
            result["pb_si_008_status"],
        )
        self.assertEqual(
            "NAMED_TARGET_EVIDENCE_CANDIDACY_ONLY_NO_ADMISSION",
            result["part_b_status"],
        )
        self.assertEqual(NAMED_TARGET_ID, result["named_target_id"])
        self.assertTrue(result["reference_qualified"])
        self.assertTrue(
            result[
                "named_evidence_candidacy_classification_authority"
            ]
        )
        self._assert_no_elevation(result)

    def _assert_no_elevation(self, result):
        for field in (
            "allow_is_admission",
            "allow_is_part_b_pass",
            "part_b_evidence_authority",
            "part_b_claim_authority",
            "part_b_authority_grant",
            "part_b_pass_condition_authority",
            "path_b_write_authority",
            "production_registration_authority",
            "mint_authority",
            "admission_authority",
            "kernel_or_e_case_write_authority",
            "certificate_authority",
        ):
            self.assertFalse(result[field])
        self.assertEqual("DENY", result["holdout_release"])
        self.assertEqual("DENY", result["pb_si_006_download"])
        self.assertEqual("NOT_ESTABLISHED", result["pb_b5_execution"])
        self.assertEqual("NONE", result["stop_authority"])
        self.assertEqual("NOT_AUTHORIZED", result["certified_stop"])
        self.assertEqual(HARD_BAN, result["hard_ban"])


if __name__ == "__main__":
    unittest.main()
