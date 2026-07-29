from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash
from src.scope import (
    part_b_b5_si002_explicit_owner_evaluation_execution_authority_flip as flip,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "part-b-b5-si002-explicit-owner-evaluation-execution-authority-flip.schema.json"
POLICY_PATH = ROOT / "configs" / "part-b-b5-si002-explicit-owner-evaluation-execution-authority-flip-policy-v0.1.yaml"
RECORD_PATH = ROOT / "configs" / "part-b-b5-si002-explicit-owner-evaluation-execution-authority-flip-record-v0.1.yaml"
AUTHORIZATION_PATH = ROOT / "docs" / "kernel" / "part-b-b5-si002-explicit-owner-evaluation-execution-authority-flip-green-authorization-v0.1-20260729.json"
RED_DESIGN_PATH = ROOT / "docs" / "kernel" / "part-b-b5-si002-explicit-owner-flip-go-red-design-v0.1-20260729.json"
MODULE_PATH = ROOT / "src" / "scope" / "part_b_b5_si002_explicit_owner_evaluation_execution_authority_flip.py"

ACCEPTED_RED_PINS = {
    "docs/kernel/part-b-b5-si002-explicit-owner-flip-go-owner-go-authorization-v0.1-20260729.json": "e5b8febc62fb314772133d5a0edccaa6c704e8ebcb0c95259ecb2c4f0d5cc302",
    "docs/kernel/part-b-b5-si002-explicit-owner-flip-go-red-design-v0.1-20260729.json": "57a03130415b8927d324b04c1b2865b9a670f9b537598b8b964caf1edf338b75",
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-part-b-b5-si002-explicit-owner-flip-go-red-review-packet-v0.1-20260729.json": "2e0e98f86e7d55d003594459058e2c0dde10788135d43023c010760b1c3189ca",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SI002ExplicitOwnerEvaluationAuthorityFlipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema)
        cls.policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        cls.expected_record = yaml.safe_load(RECORD_PATH.read_text(encoding="utf-8"))
        cls.authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        cls.red_design = json.loads(RED_DESIGN_PATH.read_text(encoding="utf-8"))

    def authority(self) -> dict[str, object]:
        return deepcopy(flip.EXPECTED_AUTHORITY)

    def request(self) -> dict[str, object]:
        return deepcopy(flip.EXPECTED_REQUEST)

    def evaluate(self, request: object | None = None, authority: object | None = None) -> dict[str, object]:
        return flip.evaluate_si002_explicit_owner_evaluation_execution_authority_flip(
            self.request() if request is None else request,
            explicit_owner_flip_authority=self.authority() if authority is None else authority,
        )

    def assert_denied(self, record: dict[str, object], decision: str) -> None:
        self.assertEqual(record["decision"], decision)
        self.assertFalse(record["flip_contract_valid"])
        self.assertFalse(record["explicit_owner_flip_go_valid"])
        self.assertFalse(record["pre_flip_binding_satisfied"])
        self.assertFalse(record["flip_performed"])
        self.assertFalse(record["post_flip_evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertEqual(record["class_1_status"], "MISSING")
        self.assertFalse(record["all_flip_prerequisites_satisfied"])
        self.assertFalse(record["authority_flip_eligible_before"])
        self.assertFalse(record["authority_flip_eligible_after"])
        self.assertFalse(record["production_registration_enabled"])
        self.assertFalse(record["part_b_pass"])
        self.assertFalse(record["path_b_write_authority"])
        self.assertEqual(record["stop_authority"], "NONE")
        self.assertFalse(record["full_m3_star"])
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.validator.validate(record)

    def test_schema_and_closed_world_shapes(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        for value in (self.authority(), self.request(), self.expected_record):
            self.validator.validate(value)
            extra = dict(value)
            extra["unexpected"] = True
            self.assertTrue(list(self.validator.iter_errors(extra)))
        self.assertEqual(7, len(self.authority()))
        self.assertEqual(65, len(self.request()))
        self.assertEqual(44, len(self.expected_record))

    def test_catalog_identity_policy_authorization_and_record_hash_replay(self) -> None:
        self.assertEqual(flip.AUTHORITY_FIELD_CATALOG_HASH, canonical_value_hash(list(flip.AUTHORITY_FIELDS)))
        self.assertEqual(flip.REQUEST_FIELD_CATALOG_HASH, canonical_value_hash(list(flip.REQUEST_FIELDS)))
        self.assertEqual(flip.RECORD_FIELD_CATALOG_HASH, canonical_value_hash(list(flip.RECORD_FIELDS)))
        self.assertEqual(flip.FLIP_CONTRACT_IDENTITY_HASH, canonical_value_hash(flip.FLIP_IDENTITY_COMPONENTS))
        self.assertEqual(13, len(flip.FLIP_IDENTITY_COMPONENTS))
        self.assertEqual(25, len(flip.DECISION_ENUM))
        self.assertEqual(list(flip.DECISION_ENUM), self.policy["decision_enum"])
        self.assertEqual(flip.REASON_CODES, self.policy["reason_codes"])
        self.assertEqual(self.policy["hash"], canonical_document_hash(self.policy))
        self.assertEqual(self.expected_record["hash"], canonical_document_hash(self.expected_record))
        self.assertEqual(file_sha256(AUTHORIZATION_PATH), flip.EXPLICIT_OWNER_FLIP_GO_CONTENT_SHA256)
        self.assertNotEqual(flip.EXPLICIT_OWNER_FLIP_GO_CONTENT_SHA256, flip.RED_GO_CONTENT_SHA256)
        self.assertEqual(self.authorization["decision"], flip.EXPECTED_AUTHORITY["explicit_owner_flip_go_decision"])

    def test_positive_record_matches_yaml_and_records_only_evaluation_flip(self) -> None:
        record = self.evaluate()
        self.assertEqual(record, self.expected_record)
        self.assertTrue(record["flip_contract_valid"])
        self.assertTrue(record["explicit_owner_flip_go_valid"])
        self.assertTrue(record["pre_flip_binding_satisfied"])
        self.assertEqual(record["pre_flip_bound_authority_decision"], flip.PRE_FLIP_BOUND_AUTHORITY_DECISION)
        self.assertTrue(record["flip_performed"])
        self.assertFalse(record["pre_flip_evaluation_execution_authority"])
        self.assertTrue(record["post_flip_evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["production_registration_enabled"])
        self.assertEqual(record["pb_b5_si_003_state"], "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION")
        self.assertFalse(record["part_b_pass"])
        self.assertFalse(record["path_b_write_authority"])

    def test_same_request_and_go_same_record_and_hash(self) -> None:
        self.assertEqual(self.evaluate(), self.evaluate())

    def test_authority_gate_is_exact_before_request(self) -> None:
        bad_authorities: list[object] = [{}, [], "bad"]
        for field in flip.AUTHORITY_FIELDS:
            bad = self.authority()
            bad[field] = "wrong"
            bad_authorities.append(bad)
        extra = self.authority()
        extra["unexpected"] = False
        bad_authorities.append(extra)
        malformed_request = {"raw_payload": object()}
        for authority in bad_authorities:
            self.assert_denied(self.evaluate(request=malformed_request, authority=authority), flip.DENY_EXPLICIT_OWNER_FLIP_AUTHORITY)
        red_go = self.authority()
        red_go["explicit_owner_flip_go_content_sha256"] = flip.RED_GO_CONTENT_SHA256
        self.assert_denied(
            self.evaluate(request=malformed_request, authority=red_go), flip.DENY_RED_GO_REUSED_AS_FLIP_GO
        )

    def test_fail_closed_matrix_30_of_30_and_enum_closed(self) -> None:
        def changed(field: str, value: object) -> dict[str, object]:
            request = self.request()
            request[field] = value
            return request

        def missing(field: str) -> dict[str, object]:
            request = self.request()
            request.pop(field)
            return request

        cases: list[tuple[str, str, object, object]] = [
            ("FC-001", flip.POSITIVE_DECISION, self.request(), self.authority()),
            ("FC-002", flip.DENY_EXPLICIT_OWNER_FLIP_AUTHORITY, self.request(), {}),
            ("FC-003", flip.DENY_UNKNOWN_IMPLEMENTATION, changed("implementation_id", "*"), self.authority()),
            ("FC-004", flip.DENY_MISSING_CLASS2_BINDING, missing("evaluator_capability_identity_hash"), self.authority()),
            ("FC-005", flip.DENY_CLASS2_HASH_MISMATCH, changed("evaluator_capability_identity_hash", "sha256:" + "0" * 64), self.authority()),
            ("FC-006", flip.DENY_MISSING_CLASS3_BINDING, missing("evidence_contract_identity_hash"), self.authority()),
            ("FC-007", flip.DENY_CLASS3_HASH_MISMATCH, changed("evidence_contract_identity_hash", "sha256:" + "0" * 64), self.authority()),
            ("FC-008", flip.DENY_MISSING_CLASS4_BINDING, missing("class_4_record_hash"), self.authority()),
            ("FC-009", flip.DENY_CLASS4_HASH_OR_STATE_MISMATCH, changed("class_4_actual_evaluator_invocation", False), self.authority()),
            ("FC-010", flip.DENY_MISSING_CLASS5_BINDING, missing("class_5_record_hash"), self.authority()),
            ("FC-011", flip.DENY_CLASS5_HASH_OR_KEEP_FALSE_BINDING_MISMATCH, changed("class_5_bound_authority_decision", "wrong"), self.authority()),
            ("FC-012", flip.DENY_MISSING_SI002_CHAIN_BINDING, missing("si002_boundary_record_hash"), self.authority()),
            ("FC-013", flip.DENY_SI002_CHAIN_HASH_MISMATCH, changed("si002_gap_catalog_record_hash", "sha256:" + "0" * 64), self.authority()),
            ("FC-014", flip.DENY_MISSING_EXPLICIT_OWNER_FLIP_GO, missing("explicit_owner_flip_go_artifact_id"), self.authority()),
            ("FC-015", flip.DENY_EXPLICIT_OWNER_FLIP_GO_HASH_OR_DECISION_MISMATCH, changed("explicit_owner_flip_go_content_sha256", "0" * 64), self.authority()),
            ("FC-016", flip.DENY_EXPLICIT_OWNER_FLIP_GO_HASH_OR_DECISION_MISMATCH, changed("explicit_owner_flip_go_decision", "wrong"), self.authority()),
            ("FC-017", flip.DENY_EXPLICIT_OWNER_FLIP_GO_HASH_OR_DECISION_MISMATCH, changed("explicit_owner_flip_go_authority_base_commit", "0" * 40), self.authority()),
            ("FC-018", flip.DENY_RED_GO_REUSED_AS_FLIP_GO, changed("explicit_owner_flip_go_content_sha256", flip.RED_GO_CONTENT_SHA256), self.authority()),
            ("FC-019", flip.DENY_PRE_FLIP_BINDING_NOT_SATISFIED, changed("pre_flip_binding_satisfied", False), self.authority()),
            ("FC-020", flip.DENY_PRE_FLIP_AUTHORITY_NOT_FALSE, changed("pre_flip_evaluation_execution_authority", True), self.authority()),
            ("FC-021", flip.DENY_FLIP_TRANSITION_MISMATCH, changed("requested_transition", "wrong"), self.authority()),
            ("FC-022", flip.DENY_FLIP_TRANSITION_MISMATCH, changed("requested_post_flip_evaluation_execution_authority", False), self.authority()),
            ("FC-023", flip.DENY_PLANNER_EXECUTION_AUTHORITY_REQUEST, changed("requested_post_flip_planner_execution_authority", True), self.authority()),
            ("FC-024", flip.DENY_PRODUCTION_SCOPE, changed("production_registration_enabled", True), self.authority()),
            ("FC-025", flip.DENY_SI003_SCOPE, changed("pb_b5_si_003_close_requested", True), self.authority()),
            ("FC-026", flip.DENY_PART_B_PATH_B_OR_FULL_M3_SCOPE, changed("part_b_pass_requested", True), self.authority()),
            ("FC-027", flip.DENY_PART_B_PATH_B_OR_FULL_M3_SCOPE, changed("path_b_write_requested", True), self.authority()),
            ("FC-028", flip.DENY_STOP_OR_CERTIFICATE_SCOPE, changed("certificate_requested", True), self.authority()),
            ("FC-029", flip.DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT, changed("hidden_ground_truth", "x"), self.authority()),
            ("FC-030", flip.DENY_NONDETERMINISTIC_OR_NON_CONTRACT_INPUT, missing("schema_version"), self.authority()),
        ]
        red_expected = {case["case_id"]: case["expected"] for case in self.red_design["fail_closed_matrix"]}
        self.assertEqual(30, len(cases))
        self.assertEqual(30, len(red_expected))
        self.assertFalse([value for value in red_expected.values() if value not in flip.DECISION_ENUM])
        for case_id, expected, request, authority in cases:
            with self.subTest(case_id=case_id):
                self.assertEqual(expected, red_expected[case_id])
                record = self.evaluate(request=request, authority=authority)
                if expected == flip.POSITIVE_DECISION:
                    self.assertEqual(record, self.expected_record)
                    self.validator.validate(record)
                else:
                    self.assert_denied(record, expected)

        self.assert_denied(self.evaluate(request=changed("stop_requested", True)), flip.DENY_STOP_OR_CERTIFICATE_SCOPE)
    def test_red_primary_and_protected_pins_match_without_mutation(self) -> None:
        for relative, expected in ACCEPTED_RED_PINS.items():
            self.assertEqual(file_sha256(ROOT / relative), expected)
        primary = self.red_design["pinned_artifact_table"]
        protected = self.red_design["protected_zero_drift"]
        self.assertEqual(16, len(primary))
        self.assertEqual(14, len(protected))
        for entry in [*primary, *protected]:
            with self.subTest(path=entry["path"]):
                self.assertEqual(file_sha256(ROOT / entry["path"]), entry["content_sha256"])

    def test_pure_validator_imports_no_runtime_and_boundaries_remain_closed(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        forbidden = (
            "from src.planner", "import src.planner", "twin_p10_readonly_wiring",
            "actual_evaluator_invocation import", "runner_invocation import",
            "subprocess", "Popen(", "CERTIFIED_STOP",
        )
        for token in forbidden:
            self.assertNotIn(token, source)
        self.assertFalse(flip.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(flip.PLANNER_EXECUTION_AUTHORITY)
        self.assertEqual(flip.HARD_BAN, self.policy["hard_ban"])


if __name__ == "__main__":
    unittest.main()
