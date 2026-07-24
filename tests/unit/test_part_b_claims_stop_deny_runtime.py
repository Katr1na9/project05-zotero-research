from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PRODUCT_ARTIFACTS = (
    ROOT / "schemas" / "part-b-claims-stop-deny-policy.schema.json",
    ROOT / "schemas" / "part-b-claims-stop-deny-record.schema.json",
    ROOT / "schemas" / "part-b-claims-stop-deny-manifest.schema.json",
    ROOT / "configs" / "part-b-claims-stop-deny-policy-v0.8.yaml",
    ROOT / "configs" / "part-b-claims-stop-deny-example-v0.8.yaml",
    ROOT / "configs" / "part-b-claims-stop-deny-manifest-v0.8.yaml",
    ROOT / "contracts" / "part-b-claims-stop-deny-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-claims-stop-deny-v0.8.md",
    ROOT / "src" / "scope" / "part_b_claims_stop_deny.py",
    ROOT / "src" / "scope" / "part-b-claims-stop-deny-spec-issues.md",
    ROOT / "src" / "scope" / "part-b-b0-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-claims-stop-deny-implementation-plan-v0.8-20260724.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)

CLAIM_CEILING = "CONTRACT_CONSISTENCY_ONLY"
SLICE_STATUS = "CLAIMS_STOP_DENY_GATE_ONLY"
CERTIFIED_STOP_STATUS = "NOT_AUTHORIZED"


class PartBClaimsStopDenyRuntimeTests(unittest.TestCase):
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
        from src.scope.part_b_claims_stop_deny import (
            evaluate_claim_authority_request,
        )

        return evaluate_claim_authority_request(request)

    def assert_frozen_states(self, result: dict[str, object]) -> None:
        self.assertEqual(
            result["claim_ceiling_remainder"],
            CLAIM_CEILING,
        )
        self.assertIs(result["scalarization_authority"], False)
        self.assertEqual(result["scalarization_decision"], "DENY")
        self.assertIs(
            result["performance_superiority_authority"],
            False,
        )
        self.assertEqual(
            result["performance_superiority_decision"],
            "DENY",
        )
        self.assertEqual(result["stop_authority"], "NONE")
        self.assertEqual(
            result["certified_stop"],
            CERTIFIED_STOP_STATUS,
        )
        self.assertEqual(result["slice_status"], SLICE_STATUS)

    def test_red_09_contract_consistency_request_has_no_elevation(
        self,
    ) -> None:
        """RED-09: contract checking is not a claim or STOP request."""
        self.require_product()
        result = self.evaluate(
            {
                "request_id": "CLAIMS-STOP-001",
                "request_kind": "CONTRACT_CONSISTENCY_CHECK",
                "promotion_target": "NONE",
                "basis_kind": "CONTRACT_ONLY",
            }
        )
        self.assert_frozen_states(result)
        self.assertEqual(
            result["decision"],
            "NO_CLAIM_OR_STOP_AUTHORIZATION_REQUEST",
        )
        self.assertEqual(
            result["reason_code"],
            "CLAIMS-STOP-000_NO_ELEVATION_REQUEST",
        )

    def test_red_10_all_claim_and_stop_elevations_are_denied(self) -> None:
        """RED-10: ranking, superiority, certificates and STOP all deny."""
        self.require_product()
        for target in (
            "SCALARIZED_RANKING",
            "PERFORMANCE_SUPERIORITY",
            "CERTIFICATE_ISSUED",
            "CERTIFIED_STOP",
        ):
            with self.subTest(target=target):
                result = self.evaluate(
                    {
                        "request_id": f"CLAIMS-STOP-{target}",
                        "request_kind": "PROMOTE_CLAIM_AUTHORITY",
                        "promotion_target": target,
                        "basis_kind": "CONTRACT_ONLY",
                    }
                )
                self.assert_frozen_states(result)
                self.assertEqual(result["decision"], "DENY")
                self.assertEqual(
                    result["reason_code"],
                    "CLAIMS-STOP-001_ELEVATION_DENIED",
                )

    def test_red_11_stub_sampler_and_admission_are_never_stop_proof(
        self,
    ) -> None:
        """RED-11: local slice outputs cannot become stopping evidence."""
        self.require_product()
        for basis in (
            "B2_SAMPLER_STUB",
            "B3_CAPTURE_FIXTURE",
            "B5_ADMISSION_RECORD",
        ):
            with self.subTest(basis=basis):
                result = self.evaluate(
                    {
                        "request_id": f"CLAIMS-STOP-{basis}",
                        "request_kind": "PROMOTE_CLAIM_AUTHORITY",
                        "promotion_target": "CERTIFIED_STOP",
                        "basis_kind": basis,
                    }
                )
                self.assert_frozen_states(result)
                self.assertEqual(result["decision"], "DENY")
                self.assertIs(result["basis_accepted_for_stop"], False)

    def test_red_12_missing_and_unknown_fields_fail_closed(self) -> None:
        """RED-12: the local request surface is closed."""
        self.require_product()
        for request in (
            {},
            {
                "request_id": "CLAIMS-STOP-UNKNOWN",
                "request_kind": "CONTRACT_CONSISTENCY_CHECK",
                "promotion_target": "NONE",
                "basis_kind": "CONTRACT_ONLY",
                "unexpected": True,
            },
        ):
            with self.subTest(request=request):
                result = self.evaluate(request)
                self.assert_frozen_states(result)
                self.assertEqual(result["decision"], "DENY")
                self.assertIn(
                    result["reason_code"],
                    {
                        "CLAIMS-STOP-002_REQUEST_INVALID",
                        "CLAIMS-STOP-003_UNKNOWN_FIELD",
                    },
                )

    def test_red_13_same_request_replays_same_record_and_hash(self) -> None:
        """RED-13: local DENY records are deterministic."""
        self.require_product()
        request = {
            "request_id": "CLAIMS-STOP-REPLAY",
            "request_kind": "PROMOTE_CLAIM_AUTHORITY",
            "promotion_target": "PERFORMANCE_SUPERIORITY",
            "basis_kind": "B3_CAPTURE_FIXTURE",
        }
        first = self.evaluate(request)
        second = self.evaluate(deepcopy(request))
        self.assertEqual(first, second)
        self.assertRegex(first["record_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_red_14_adjacent_authorities_remain_denied(self) -> None:
        """RED-14: SI-006, SI-008, B5 and holdout boundaries persist."""
        self.require_product()
        result = self.evaluate(
            {
                "request_id": "CLAIMS-STOP-BOUNDARY",
                "request_kind": "PROMOTE_CLAIM_AUTHORITY",
                "promotion_target": "CERTIFICATE_ISSUED",
                "basis_kind": "B5_ADMISSION_RECORD",
            }
        )
        self.assert_frozen_states(result)
        self.assertEqual(result["holdout_release"], "DENY")
        self.assertEqual(result["pb_si_006_download"], "DENY")
        self.assertEqual(result["pb_si_008"], "NOT_OPENED")
        self.assertEqual(
            result["pb_b5_execution"],
            "NOT_ESTABLISHED",
        )

    def test_red_15_no_claim_certificate_or_system_stop_is_emitted(
        self,
    ) -> None:
        """RED-15: denial emits no authority-bearing payload."""
        self.require_product()
        result = self.evaluate(
            {
                "request_id": "CLAIMS-STOP-NO-EMIT",
                "request_kind": "PROMOTE_CLAIM_AUTHORITY",
                "promotion_target": "CERTIFIED_STOP",
                "basis_kind": "B2_SAMPLER_STUB",
            }
        )
        self.assert_frozen_states(result)
        self.assertIs(result["certificate_issued"], False)
        self.assertIs(result["scalarization_applied"], False)
        self.assertIs(result["superiority_claim_issued"], False)
        serialized = json.dumps(result, sort_keys=True)
        for forbidden in (
            '"certificate":',
            '"level_certificate":',
            '"scalar_weights":',
            '"scalar_score":',
            '"system_status":',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)

    def test_red_16_no_io_and_part_a_stop_semantics_are_unchanged(
        self,
    ) -> None:
        """RED-16: local gate cannot call I/O or mutate Part A STOP."""
        self.require_product()
        result = self.evaluate(
            {
                "request_id": "CLAIMS-STOP-NO-IO",
                "request_kind": "PROMOTE_CLAIM_AUTHORITY",
                "promotion_target": "SCALARIZED_RANKING",
                "basis_kind": "CONTRACT_ONLY",
            }
        )
        self.assert_frozen_states(result)
        self.assertIs(result["network_io"], False)
        self.assertIs(result["llm_invoked"], False)
        self.assertIs(result["holdout_artifact_accessed"], False)
        self.assertIs(result["part_a_kernel_gamma_changed"], False)
        self.assertIs(
            result["part_a_certified_stop_semantics_changed"],
            False,
        )
        self.assertIs(result["kernel_stop_path_invoked"], False)


if __name__ == "__main__":
    unittest.main()
