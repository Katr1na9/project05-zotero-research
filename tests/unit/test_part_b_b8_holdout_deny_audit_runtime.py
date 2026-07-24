from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"
SCHEMA_DIR = ROOT / "schemas"
SCOPE_DIR = ROOT / "src" / "scope"

PRODUCT_ARTIFACTS = (
    SCHEMA_DIR / "part-b-b8-holdout-deny-audit-policy.schema.json",
    SCHEMA_DIR / "part-b-b8-holdout-deny-audit-record.schema.json",
    SCHEMA_DIR / "part-b-b8-holdout-deny-audit-manifest.schema.json",
    CONFIG_DIR / "part-b-b8-holdout-deny-audit-policy-v0.8.yaml",
    CONFIG_DIR / "part-b-b8-holdout-deny-audit-example-v0.8.yaml",
    CONFIG_DIR / "part-b-b8-holdout-deny-audit-manifest-v0.8.yaml",
    ROOT / "contracts" / "part-b-b8-holdout-deny-audit-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-b8-holdout-deny-audit-v0.8.md",
    SCOPE_DIR / "part_b_b8_holdout_deny_audit.py",
    SCOPE_DIR / "part-b-b8-holdout-deny-audit-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b8-holdout-deny-audit-implementation-plan-v0.8-20260724.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)


class PartBB8HoldoutDenyAuditRuntimeTests(unittest.TestCase):
    def require_product(self) -> None:
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_ARTIFACTS
            if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved artifact/module: " + ", ".join(missing),
        )

    def evaluate(self, request: dict[str, object]) -> dict[str, object]:
        self.require_product()
        from src.scope.part_b_b8_holdout_deny_audit import (
            evaluate_holdout_request,
        )

        return evaluate_holdout_request(request)

    def test_red_09_same_request_replays_same_audit_record(self) -> None:
        """RED-09: DENY audit records are deterministic and hashable."""
        request = {"operation": "release_holdout", "case_id": "ABSTRACT-001"}
        first = self.evaluate(request)
        second = self.evaluate(deepcopy(request))
        self.assertEqual(first, second)
        self.assertEqual(first["decision"], "DENY")
        self.assertRegex(first["audit_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_red_10_release_request_can_never_become_allow(self) -> None:
        """RED-10: release remains DENY even when a caller asks for ALLOW."""
        for requested in (None, "ALLOW", True):
            with self.subTest(requested=requested):
                request = {
                    "operation": "release_holdout",
                    "requested_decision": requested,
                }
                result = self.evaluate(request)
                self.assertEqual(result["decision"], "DENY")
                self.assertEqual(result["release_decision"], "DENY")
                self.assertEqual(
                    result["reason_code"],
                    "B8-DENY-001_RELEASE_NOT_AUTHORIZED",
                )

    def test_red_11_label_and_result_access_fail_closed(self) -> None:
        """RED-11: labels/results cannot be read through the audit stub."""
        for operation, reason in (
            ("read_holdout_labels", "B8-DENY-002_LABEL_ACCESS_DENIED"),
            ("read_holdout_results", "B8-DENY-003_RESULT_ACCESS_DENIED"),
            ("read_holdout_data", "B8-DENY-004_DATA_ACCESS_DENIED"),
        ):
            with self.subTest(operation=operation):
                result = self.evaluate({"operation": operation})
                self.assertEqual(result["decision"], "DENY")
                self.assertEqual(result["reason_code"], reason)

    def test_red_12_statistical_execution_is_denied(self) -> None:
        """RED-12: audit cannot run statistics or emit an analysis result."""
        result = self.evaluate({"operation": "run_statistical_analysis"})
        self.assertEqual(result["decision"], "DENY")
        self.assertEqual(
            result["reason_code"],
            "B8-DENY-005_STATISTICAL_EXECUTION_DENIED",
        )
        self.assertNotIn("result", result)
        self.assertNotIn("statistics", result)

    def test_red_13_authority_fields_are_absent_or_false(self) -> None:
        """RED-13: the result exposes no data-plane authority."""
        result = self.evaluate({"operation": "release_holdout"})
        for field in (
            "holdout_data_access_authority",
            "holdout_label_access_authority",
            "holdout_result_access_authority",
            "statistical_analysis_execution_authority",
            "release_authority",
            "stop_authority",
        ):
            with self.subTest(field=field):
                self.assertIn(field, result)
                self.assertIn(result[field], (False, "NONE", "DENY"))

    def test_red_14_missing_and_unknown_request_fields_fail_closed(self) -> None:
        """RED-14: malformed requests cannot widen the audit surface."""
        for request in ({}, {"operation": "release_holdout", "unknown": True}):
            with self.subTest(request=request):
                result = self.evaluate(request)
                self.assertEqual(result["decision"], "DENY")
                self.assertIn(
                    result["reason_code"],
                    {
                        "B8-DENY-006_REQUEST_INVALID",
                        "B8-DENY-007_UNKNOWN_FIELD",
                    },
                )

    def test_red_15_upstream_hashes_are_not_mutated_by_audit(self) -> None:
        """RED-15: audit requests cannot rewrite frozen B8 identities."""
        result = self.evaluate(
            {
                "operation": "release_holdout",
                "bindings": {
                    "b8_manifest_hash": "sha256:" + ("0" * 64),
                },
            }
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertEqual(
            result["reason_code"],
            "B8-DENY-008_BINDING_MISMATCH",
        )

    def test_red_16_no_stop_or_claim_authority_is_emitted(self) -> None:
        """RED-16: DENY audit cannot emit STOP, certificate or claims."""
        result = self.evaluate({"operation": "release_holdout"})
        serialized = json.dumps(result, sort_keys=True)
        self.assertEqual(result["decision"], "DENY")
        self.assertEqual(result["stop_authority"], "NONE")
        for forbidden in (
            "CERTIFIED_STOP",
            '"system_status"',
            '"certificate"',
            '"performance_claim":',
            '"superiority_claim"',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
