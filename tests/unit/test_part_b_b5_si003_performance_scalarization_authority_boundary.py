from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash
from src.scope import part_b_b5_si003_performance_scalarization_authority_boundary as boundary


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "part-b-b5-si003-performance-scalarization-authority-boundary.schema.json"
POLICY_PATH = ROOT / "configs" / "part-b-b5-si003-performance-scalarization-authority-boundary-policy-v0.1.yaml"
RECORD_PATH = ROOT / "configs" / "part-b-b5-si003-performance-scalarization-authority-boundary-record-v0.1.yaml"
GREEN_GO_PATH = ROOT / "docs" / "kernel" / "part-b-b5-si003-performance-scalarization-authority-boundary-green-authorization-v0.1-20260729.json"
RED_DESIGN_PATH = ROOT / "docs" / "kernel" / "part-b-b5-si003-performance-scalarization-authority-boundary-red-design-v0.1-20260729.json"
MODULE_PATH = ROOT / "src" / "scope" / "part_b_b5_si003_performance_scalarization_authority_boundary.py"

RED_PINS = {
    "docs/kernel/part-b-b5-si003-performance-scalarization-authority-boundary-owner-go-authorization-v0.1-20260729.json": "fa17377fb9934381e5eb66b79db6fd127e98f794aebc6194c8d5c81d83c14aa7",
    "docs/kernel/part-b-b5-si003-performance-scalarization-authority-boundary-red-design-v0.1-20260729.json": "4eb2e53154d611efc3a996c3642103184962386d4f3d302cbd6b726cc0cf2c6e",
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-part-b-b5-si003-performance-scalarization-authority-boundary-red-review-packet-v0.1-20260729.json": "809d8e47c9ec387309d44bf0a5c648ee0233fd4b7de5f46d7c9913015bb86bc8",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SI003PerformanceScalarizationAuthorityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema)
        cls.policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        cls.record = yaml.safe_load(RECORD_PATH.read_text(encoding="utf-8"))
        cls.green_go = json.loads(GREEN_GO_PATH.read_text(encoding="utf-8"))
        cls.red = json.loads(RED_DESIGN_PATH.read_text(encoding="utf-8"))

    def authority(self) -> dict[str, object]:
        return deepcopy(boundary.EXPECTED_AUTHORITY)

    def request(self) -> dict[str, object]:
        return deepcopy(boundary.EXPECTED_REQUEST)

    def evaluate(self, request: object | None = None, authority: object | None = None) -> dict[str, object]:
        return boundary.evaluate_si003_performance_scalarization_authority_boundary(
            self.request() if request is None else request,
            explicit_owner_boundary_authority=self.authority() if authority is None else authority,
        )

    def assert_denied(self, record: dict[str, object], decision: str) -> None:
        self.assertEqual(record["decision"], decision)
        self.assertFalse(record["si003_closed"])
        self.assertTrue(record["evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["scalarization_authority"])
        self.assertFalse(record["performance_claim_authority"])
        self.assertFalse(record["superiority_claim_authority"])
        self.assertFalse(record["part_b_pass"])
        self.assertFalse(record["path_b_write_authority"])
        self.assertEqual(record["stop_authority"], "NONE")
        self.assertFalse(record["full_m3_star"])
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.validator.validate(record)

    def test_schema_and_closed_world_shapes(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        for value in (self.authority(), self.request(), self.record):
            self.validator.validate(value)
            extra = dict(value)
            extra["unexpected"] = True
            self.assertTrue(list(self.validator.iter_errors(extra)))
        self.assertEqual((6, 22, 24), (len(self.authority()), len(self.request()), len(self.record)))

    def test_catalog_policy_record_and_green_go_hash_replay(self) -> None:
        self.assertEqual(boundary.AUTHORITY_FIELD_CATALOG_HASH, canonical_value_hash(list(boundary.AUTHORITY_FIELDS)))
        self.assertEqual(boundary.REQUEST_FIELD_CATALOG_HASH, canonical_value_hash(list(boundary.REQUEST_FIELDS)))
        self.assertEqual(boundary.RECORD_FIELD_CATALOG_HASH, canonical_value_hash(list(boundary.RECORD_FIELDS)))
        self.assertEqual(list(boundary.DECISION_ENUM), self.policy["decision_enum"])
        self.assertEqual(boundary.REASON_CODES, self.policy["reason_codes"])
        self.assertEqual(self.policy["hash"], canonical_document_hash(self.policy))
        self.assertEqual(self.record["hash"], canonical_document_hash(self.record))
        self.assertEqual(file_sha256(GREEN_GO_PATH), boundary.GREEN_GO_CONTENT_SHA256)
        self.assertEqual(self.green_go["decision"], boundary.GREEN_GO_DECISION)

    def test_positive_boundary_record_keeps_si003_open_and_claims_false(self) -> None:
        record = self.evaluate()
        self.assertEqual(record, self.record)
        self.assertEqual(record["decision"], boundary.POSITIVE_DECISION)
        self.assertTrue(record["evaluation_execution_authority"])
        self.assertFalse(record["si003_closed"])
        self.assertFalse(record["scalarization_authority"])
        self.assertFalse(record["performance_claim_authority"])
        self.assertFalse(record["superiority_claim_authority"])
        self.assertEqual(record["contract_claim_ceiling"], "CONTRACT_CONSISTENCY_ONLY")

    def test_authority_gate_is_exact_and_precedes_request(self) -> None:
        authorities: list[object] = [{}, [], "bad"]
        for field in boundary.AUTHORITY_FIELDS:
            bad = self.authority()
            bad[field] = "wrong"
            authorities.append(bad)
        extra = self.authority()
        extra["unexpected"] = False
        authorities.append(extra)
        for authority in authorities:
            self.assert_denied(self.evaluate(request={"raw_payload": object()}, authority=authority), boundary.DENY_EXPLICIT_OWNER_BOUNDARY_AUTHORITY)

    def test_red_fail_closed_matrix_18_of_18_is_enum_closed(self) -> None:
        def changed(field: str, value: object) -> dict[str, object]:
            request = self.request()
            request[field] = value
            return request

        cases = [
            ("FC-001", boundary.DENY_UNKNOWN_IMPLEMENTATION, changed("implementation_id", "*")),
            ("FC-002", boundary.DENY_WRONG_ISSUE, changed("issue_id", "wrong")),
            ("FC-003", boundary.DENY_SI003_STATE, changed("pb_b5_si_003_state", "CLOSED")),
            ("FC-004", boundary.DENY_SI003_CLOSE_REQUEST, changed("pb_b5_si_003_close_requested", True)),
            ("FC-005", boundary.DENY_FLIP_BINDING_MISMATCH, changed("flip_record_hash", "sha256:" + "0" * 64)),
            ("FC-006", boundary.DENY_POST_FLIP_EVAL_AUTHORITY_MISMATCH, changed("evaluation_execution_authority", False)),
            ("FC-007", boundary.DENY_PLANNER_SCOPE, changed("planner_execution_authority", True)),
            ("FC-008", boundary.DENY_SCALARIZATION_SCOPE, changed("scalarization_authority", True)),
            ("FC-009", boundary.DENY_PERFORMANCE_CLAIM_SCOPE, changed("performance_claim_authority", True)),
            ("FC-010", boundary.DENY_SUPERIORITY_SCOPE, changed("superiority_claim_authority", True)),
            ("FC-011", boundary.DENY_RESOURCE_VECTOR_MODEL, changed("resource_vector_model", "SCALAR")),
            ("FC-012", boundary.DENY_CLAIM_CEILING, changed("contract_claim_ceiling", "PERFORMANCE")),
            ("FC-013", boundary.DENY_RED_GO_REUSED_AS_CLOSE_GO, changed("this_red_go_reused_as_close_go", True)),
            ("FC-014", boundary.DENY_SELF_ASSERTED_CLOSE_GO, changed("later_separate_owner_si003_close_go_present", True)),
            ("FC-015", boundary.DENY_PART_B_OR_PATH_B_OR_STOP_SCOPE, changed("part_b_pass_requested", True)),
            ("FC-016", boundary.DENY_B6_B9_SCOPE, changed("b6_execution_requested", True)),
            ("FC-017", boundary.DENY_EXTRA_INPUT, changed("production_registration_enabled", True)),
            ("FC-018", boundary.DENY_PROTECTED_BYTE_MUTATION, changed("mutate_protected_bytes", True)),
        ]
        expected = {case["case_id"]: case["expected"] for case in self.red["fail_closed_matrix_preview"]}
        self.assertEqual(18, len(cases))
        self.assertEqual(18, len(expected))
        self.assertFalse([value for value in expected.values() if value not in boundary.DECISION_ENUM])
        for case_id, decision, request in cases:
            with self.subTest(case_id=case_id):
                self.assertEqual(decision, expected[case_id])
                self.assert_denied(self.evaluate(request=request), decision)

    def test_red_primary_and_protected_pins_match(self) -> None:
        for relative, expected in RED_PINS.items():
            self.assertEqual(file_sha256(ROOT / relative), expected)
        primary = self.red["pinned_artifact_table"]
        protected = self.red["protected_zero_drift"]
        self.assertEqual((10, 8), (len(primary), len(protected)))
        for entry in [*primary, *protected]:
            self.assertEqual(file_sha256(ROOT / entry["path"]), entry["content_sha256"])

    def test_pure_validator_imports_no_runtime(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for token in (
            "from src.planner", "import src.planner", "twin_p10_readonly_wiring",
            "si002_explicit_owner_evaluation_execution_authority_flip import",
            "actual_evaluator_invocation import", "subprocess", "Popen(",
        ):
            self.assertNotIn(token, source)

    def test_hard_boundaries(self) -> None:
        self.assertEqual(boundary.HARD_BAN, self.policy["hard_ban"])
        self.assertTrue(boundary.EVALUATION_EXECUTION_AUTHORITY)
        self.assertFalse(boundary.PLANNER_EXECUTION_AUTHORITY)
        self.assertFalse(boundary.SCALARIZATION_AUTHORITY)
        self.assertFalse(boundary.PERFORMANCE_CLAIM_AUTHORITY)
        self.assertFalse(boundary.SUPERIORITY_CLAIM_AUTHORITY)
        self.assertFalse(boundary.PRODUCTION_REGISTRATION_ENABLED)


if __name__ == "__main__":
    unittest.main()
