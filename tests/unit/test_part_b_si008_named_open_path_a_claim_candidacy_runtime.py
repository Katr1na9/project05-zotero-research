"""Runtime tests for the additive PB-SI-008 Path A CLAIM candidacy gate.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or
unrestricted Part B elevation.
"""

from __future__ import annotations

from copy import deepcopy
import importlib
from pathlib import Path
import unittest

from src.scope.part_b_si008_dual_track_deny import (
    evaluate_dual_track_request,
)
from src.scope.part_b_si008_named_open_path_a_evidence_candidacy import (
    evaluate_si008_named_open_request,
)


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = (
    ROOT
    / "src"
    / "scope"
    / "part_b_si008_named_open_path_a_claim_candidacy.py"
)
HARD_BAN = (
    "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, "
    "or unrestricted Part B elevation."
)
CLAIM_TARGET_ID = "PATH_A_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1"
EVIDENCE_TARGET_ID = (
    "PATH_A_EVIDENCE_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1"
)
CLAIM_PAIRS = {
    "PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE": {
        "source_schema_version": "claim-ir-external-evidence-v0.1",
        "source_schema_sha256": (
            "9abc23e2258298038e137dbbe38168867"
            "d07108fa27719aa68c1c2b752ae2a7c"
        ),
        "consumer_contract_id": (
            "shared-claim-ir-consumer-contract-evidence-candidate-"
            "effective-v0.2"
        ),
        "consumer_contract_sha256": (
            "fe5222b9b4e0ddaf990761b34bdfc500"
            "4f45f55d3e2155b09388fb9596a1e504"
        ),
    },
    "PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE": {
        "source_schema_version": "claim-ir-external-evidence-v0.2",
        "source_schema_sha256": (
            "e246c44b7513a5bc2f3410a2739a53bd"
            "1f40dad3e767036bb1af3158c9e02ac6"
        ),
        "consumer_contract_id": (
            "shared-claim-ir-consumer-contract-evidence-candidate-"
            "effective-v0.3"
        ),
        "consumer_contract_sha256": (
            "7662762d045381921b8f94a39753d0c4"
            "91322b3a41d473226cc5fe3f4688457c"
        ),
    },
}
EVIDENCE_PAIRS = {
    "PATH_A_EVIDENCE_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE": {
        **CLAIM_PAIRS["PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE"],
    },
    "PATH_A_EVIDENCE_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE": {
        **CLAIM_PAIRS["PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE"],
    },
}


class PartBSI008NamedOpenPathAClaimCandidacyRuntimeTests(
    unittest.TestCase
):
    def gate(self):
        self.assertTrue(
            RUNTIME_PATH.is_file(),
            "CLAIM named-open successor runtime must be implemented",
        )
        return importlib.import_module(
            "src.scope.part_b_si008_named_open_path_a_claim_candidacy"
        )

    def claim_request(self, reference_kind, **overrides):
        pair = CLAIM_PAIRS[reference_kind]
        request = {
            "request_id": "PB-SI008-NAMED-CLAIM-001",
            "request_kind": "PROMOTE_TO_PART_B_NAMED_TARGET",
            "promotion_target": "CLAIM",
            "reference_kind": reference_kind,
            "named_target_id": CLAIM_TARGET_ID,
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
                "CLAIM_STRUCTURAL_CANDIDACY_ONLY"
            ),
            "reference_access_mode": (
                "CLASSIFY_DECLARED_REFERENCE_ONLY_NO_DEREFERENCE"
            ),
        }
        request.update(overrides)
        return request

    def evidence_request(self, reference_kind, **overrides):
        pair = EVIDENCE_PAIRS[reference_kind]
        request = {
            "request_id": "PB-SI008-NAMED-EVIDENCE-001",
            "request_kind": "PROMOTE_TO_PART_B_NAMED_TARGET",
            "promotion_target": "EVIDENCE",
            "reference_kind": reference_kind,
            "named_target_id": EVIDENCE_TARGET_ID,
            "source_schema_version": pair["source_schema_version"],
            "source_schema_sha256": pair["source_schema_sha256"],
            "consumer_contract_id": pair["consumer_contract_id"],
            "consumer_contract_sha256": pair[
                "consumer_contract_sha256"
            ],
            "package_sha256": "c" * 64,
            "structural_validation_receipt_sha256": "d" * 64,
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
        return self.gate().evaluate_si008_named_open_claim_request(request)

    def test_green_01_both_exact_claim_pairs_allow_candidacy_only(self):
        for reference_kind in CLAIM_PAIRS:
            with self.subTest(reference_kind=reference_kind):
                result = self.evaluate(self.claim_request(reference_kind))
                self.assertEqual(
                    "ALLOW_NAMED_CLAIM_CANDIDACY_ONLY",
                    result["decision"],
                )
                self.assertEqual(
                    "OPENED_FOR_NAMED_TARGET_ONLY_EVIDENCE_AND_CLAIM",
                    result["pb_si_008_status"],
                )
                self.assertEqual(
                    "NAMED_TARGET_CLAIM_CANDIDACY_ONLY_NO_MINT_NO_ADMISSION",
                    result["part_b_status"],
                )
                self.assertEqual(CLAIM_TARGET_ID, result["named_target_id"])
                self.assertEqual("CLAIM", result["allowed_promotion_target"])
                self.assertTrue(result["reference_qualified"])
                self.assertTrue(
                    result[
                        "named_claim_candidacy_classification_authority"
                    ]
                )
                self._assert_no_elevation(result)

    def test_green_02_exact_evidence_requests_return_delegate_records(self):
        for reference_kind in EVIDENCE_PAIRS:
            with self.subTest(reference_kind=reference_kind):
                request = self.evidence_request(reference_kind)
                expected = evaluate_si008_named_open_request(
                    deepcopy(request)
                )
                actual = self.evaluate(request)
                self.assertEqual(expected, actual)
                self.assertEqual(
                    "ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY",
                    actual["decision"],
                )
                self.assertNotIn(
                    "named_claim_candidacy_classification_authority",
                    actual,
                )

    def test_green_03_legacy_requests_return_dual_track_records(self):
        requests = (
            {
                "request_id": "SI008-LEGACY-PROMOTION",
                "request_kind": "PROMOTE_TO_PART_B",
                "promotion_target": "CLAIM",
                "reference_kind": "LLM_OUTPUT_REFERENCE",
            },
            {
                "request_id": "SI008-LEGACY-EXPERIMENT",
                "request_kind": "EXPERIMENT_TRACK_ONLY",
                "promotion_target": "NONE",
                "reference_kind": "ABSTRACT_EXPERIMENT_REFERENCE",
            },
        )
        for request in requests:
            with self.subTest(request_kind=request["request_kind"]):
                expected = evaluate_dual_track_request(deepcopy(request))
                actual = self.evaluate(request)
                self.assertEqual(expected, actual)
                self.assertEqual("NOT_OPENED", actual["pb_si_008_status"])
        self.assertEqual(
            "MAY_PROCEED_UNDER_SEPARATE_AUTHORITY",
            self.evaluate(requests[1])["experiment_track_status"],
        )

    def test_green_04_authority_and_pass_condition_fail_closed(self):
        for target in ("AUTHORITY", "PASS_CONDITION"):
            with self.subTest(target=target):
                request = self.claim_request(
                    "PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE",
                    promotion_target=target,
                )
                result = self.evaluate(request)
                self.assertEqual("DENY", result["decision"])
                self.assertEqual(
                    "SI008-NAMED-CLAIM-002_PROMOTION_TARGET_NOT_AUTHORIZED",
                    result["reason_code"],
                )
                self._assert_no_elevation(result)

    def test_green_05_wrong_pair_state_wildcard_and_cross_target_deny(self):
        base = self.claim_request(
            "PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE"
        )
        cases = (
            {**base, "source_schema_sha256": "0" * 64},
            {
                **base,
                "consumer_contract_sha256": (
                    CLAIM_PAIRS[
                        "PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE"
                    ]["consumer_contract_sha256"]
                ),
            },
            {**base, "reference_kind": "*"},
            {**base, "claim_id": "claim_minted_forbidden"},
            {
                **base,
                "claim_id_state": "minted",
            },
            {
                **base,
                "admission_state": "admitted",
            },
            {
                **base,
                "promotion_target": "EVIDENCE",
            },
            {
                **base,
                "named_target_id": EVIDENCE_TARGET_ID,
            },
            {
                **base,
                "reference_kind": (
                    "PATH_A_EVIDENCE_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE"
                ),
            },
            {
                **base,
                "source_schema_version": "claim-ir-external-v0.1",
                "source_schema_sha256": (
                    "5bffd7e2cf0da224422ea0d8679c18ff"
                    "eed4bbc0546bbfcd92c3137fce73419e"
                ),
                "consumer_contract_id": (
                    "shared-claim-ir-consumer-contract-effective-v0.1"
                ),
                "consumer_contract_sha256": (
                    "a2a176fdeb2b93205a7f5e11c7c09623"
                    "6e2dc582d1c31f8f4a1534866c008d63"
                ),
            },
        )
        for request in cases:
            with self.subTest(request=request):
                result = self.evaluate(request)
                self.assertEqual("DENY", result["decision"])
                self.assertFalse(result["reference_qualified"])
                self._assert_no_elevation(result)

    def test_green_06_missing_extra_bad_digest_and_nonmapping_deny(self):
        base = self.claim_request(
            "PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE"
        )
        missing = deepcopy(base)
        missing.pop("package_sha256")
        extra = deepcopy(base)
        extra["wildcard"] = "*"
        cases = (
            missing,
            extra,
            {**base, "package_sha256": "A" * 64},
            {
                **base,
                "structural_validation_receipt_sha256": "short",
            },
            ["not", "a", "mapping"],
            None,
        )
        for request in cases:
            with self.subTest(request=request):
                result = self.evaluate(request)
                self.assertEqual("DENY", result["decision"])
                self.assertEqual(
                    "SI008-NAMED-CLAIM-003_REQUEST_NOT_QUALIFIED",
                    result["reason_code"],
                )
                self._assert_no_elevation(result)

    def test_green_07_same_request_replays_and_input_is_not_mutated(self):
        request = self.claim_request(
            "PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE"
        )
        before = deepcopy(request)
        first = self.evaluate(request)
        second = self.evaluate(deepcopy(request))
        self.assertEqual(first, second)
        self.assertEqual(first["record_id"], second["record_id"])
        self.assertEqual(first["record_hash"], second["record_hash"])
        self.assertEqual(first["hash"], second["hash"])
        self.assertEqual(before, request)

    def test_green_08_claim_records_never_dereference_or_emit_authority(self):
        allowed = self.evaluate(
            self.claim_request(
                "PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE"
            )
        )
        denied = self.evaluate(
            self.claim_request(
                "PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE",
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

    def test_green_09_runtime_exports_closed_world_and_registration_false(self):
        gate = self.gate()
        self.assertEqual(18, len(gate.NAMED_REQUEST_FIELDS))
        self.assertEqual(set(CLAIM_PAIRS), set(gate.CLAIM_REFERENCE_PAIRS))
        self.assertEqual(CLAIM_TARGET_ID, gate.NAMED_TARGET_ID)
        self.assertFalse(gate.PRODUCTION_REGISTRATION_ENABLED)
        self.assertEqual(HARD_BAN, gate.HARD_BAN)

    def _assert_no_elevation(self, result):
        for field in (
            "allow_is_mint",
            "allow_is_admission",
            "allow_is_part_b_pass",
            "allow_is_write_authority",
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
