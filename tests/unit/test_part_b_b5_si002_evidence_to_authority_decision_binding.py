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
    part_b_b5_si002_evidence_to_authority_decision_binding as binding,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "part-b-b5-si002-evidence-to-authority-decision-binding.schema.json"
POLICY_PATH = ROOT / "configs" / "part-b-b5-si002-evidence-to-authority-decision-binding-policy-v0.1.yaml"
RECORD_PATH = ROOT / "configs" / "part-b-b5-si002-evidence-to-authority-decision-binding-record-v0.1.yaml"
MODULE_PATH = ROOT / "src" / "scope" / "part_b_b5_si002_evidence_to_authority_decision_binding.py"
RED_DESIGN_PATH = ROOT / "docs" / "kernel" / "part-b-b5-si002-evidence-to-authority-decision-binding-red-design-v0.1-20260729.json"

ACCEPTED_RED_PINS = {
    "docs/kernel/part-b-b5-si002-evidence-to-authority-decision-binding-owner-go-authorization-v0.1-20260729.json": "0b1a2b2823c946a15eca0f2abbb7fadd142b6a2cbf9bd6d846c73e6e710b204a",
    "docs/kernel/part-b-b5-si002-evidence-to-authority-decision-binding-red-design-v0.1-20260729.json": "3d3f43e04ac49ad41271b2bafda8f1daa477c0bd7ab5ecaf48934c5c36e4af5d",
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-part-b-b5-si002-evidence-to-authority-decision-binding-red-review-packet-v0.1-20260729.json": "92b04b3560d38af35ef556fa6fa17fa6f9c3ea8cbf0dcca70f62c9c8768fcccf",
}

PRIMARY_PINS = {
    "docs/kernel/part-b-b5-si002-evaluator-execution-capability-identity-green-owner-acceptance-v0.1-20260728.json": "2f97fffe9a3fc41a7c5243e096b83a83a31bee8e755572784038ed473ac5ed7d",
    "configs/part-b-b5-si002-evaluator-execution-capability-identity-record-v0.1.yaml": "cc3f169f9b0c365659b6f897ee9ae76d3941f2fe143e480422fcf4f77b7c4c43",
    "docs/kernel/part-b-b5-si002-evaluator-execution-evidence-record-green-owner-acceptance-v0.1-20260728.json": "d3e51ff1ab5d94bd3c9b4c5e67bc0bfa26dd99f4aa3a520968a89f528a010478",
    "configs/part-b-b5-si002-evaluator-execution-evidence-record-v0.1.yaml": "ac8f979267c83e522d024ac9458ffa345c6f1565beb516c97ff69b59b81115a4",
    "docs/kernel/part-b-b5-si002-actual-evaluator-invocation-green-owner-acceptance-v0.1-20260729.json": "a24c93b164fd454418e538091dd90be9970b7fc48ae199b6fd063c220e796c61",
    "schemas/part-b-b5-si002-actual-evaluator-invocation.schema.json": "17a8f6a43621ec144e30cb1c5c97eef09d2deb9e4890c7ee43b441a316bd69b8",
    "configs/part-b-b5-si002-actual-evaluator-invocation-policy-v0.1.yaml": "2ff0c7bea3999c2ecf56d006fe426421943aa22af4c225a5c00cd7acece14c29",
    "configs/part-b-b5-si002-actual-evaluator-invocation-record-v0.1.yaml": "09cdda105a76cf465cf7e7d36f992e43dfdea692491538ab92261993d1ee631f",
    "src/scope/part_b_b5_si002_actual_evaluator_invocation.py": "c86ecb08b7a0e723bfd26daba165d87c538a55de4a7ccf0bfc2e5c6190c6ca1e",
    "configs/part-b-b5-si002-bounded-evaluation-harness-record-v0.1.yaml": "24c2d212c133f4ba921cb46547be0868523e4dcda42bb3e59fa3f7a49bf0d421",
    "configs/part-b-b5-si002-local-bounded-evaluation-harness-runner-invocation-record-v0.1.yaml": "bdbb4a6aea269503eb127bbbc949517ee995f042d09a3810e8af96bfbe30b851",
    "configs/part-b-b5-si002-evaluation-execution-authority-boundary-record-v0.1.yaml": "df8a28daeb194a99019dc348e45a51d0906da8b8db9fda154f4c7a0848b923a5",
    "configs/part-b-b5-si002-evaluation-execution-authority-flip-prerequisite-gap-record-v0.1.yaml": "9066ca092e6d0cf6888e3846a85b3656d574bf590b856da7e993ba69a0d1d5f3",
    "docs/kernel/part-b-b5-si002-evaluation-execution-authority-flip-prerequisite-gap-green-owner-acceptance-v0.1-20260728.json": "69e350764c99ea752675b8848894ac876ce5f1bf4eec791f7850b14dd49802fd",
}

PROTECTED_PINS = {
    "src/planner/deterministic_depth1.py": "ada6a8065e71fda58dde7e2b71ca19d7aded9a39f4cf5f67fb20d6fc5d7e38ff",
    "src/planner/twin_p10_readonly_wiring.py": "1e1434e40191469f17f255905f4021fb273a323672604f0a017afe0384b5b4f9",
    "src/scope/part_b_b5_planner_admission.py": "c6af7e4cbfa9bd98fbc525887456cb2dfaefa19362f4104c5147d1f3943d0be1",
    "src/scope/part_b_b5_si002_bounded_evaluation_harness_contract.py": "6ec634666aaa4fc02ad009abf33a6f3141119f74792e50bb0724dc8a828c947b",
    "src/scope/part_b_b5_si002_local_bounded_evaluation_harness_runner_invocation.py": "35a2cb52d19126d3934cc30e3989bfd1b8028d4542b614fbbaa649373aff863b",
    "src/scope/part_b_b5_si002_evaluation_execution_authority_boundary.py": "a6c60358a935fbbe9cacd5d703f343a8dba6d177b5a26442749a270ebb76e5cf",
    "src/scope/part_b_b5_si002_evaluation_execution_authority_flip_prerequisite_gap.py": "c97d813817c4dbf7a789a187de65aad594ef9f93787280c7cb10a24e52afd793",
    "src/scope/part_b_b5_si002_evaluator_execution_capability_identity.py": "afcf07b5538d1d4f950488411dcbe6a0fe91f8d96f2403aa68157b5e3bf09349",
    "src/scope/part_b_b5_si002_evaluator_execution_evidence_record.py": "7480de3ee3eab25b4a82c7c6cd2f788980ec1a32f196c34a2255d0bac561202e",
    "src/scope/part_b_b5_si002_actual_evaluator_invocation.py": "c86ecb08b7a0e723bfd26daba165d87c538a55de4a7ccf0bfc2e5c6190c6ca1e",
    "docs/llm-editor/llm-editor-v0.8-l2-capacity-audit-metadata-only-v0.1-20260722.json": "711080b388af102a2d55fb1cc22853c0ed0cbdb738483d4d7de709f6459f9db6",
    "src/compiler/llm/kernel_readonly_experiment_matrix_runner.py": "1df1cf43c88289c6877b73ce934ccd6e429641c2a91774b1d59d820292522e0e",
    "docs/llm-editor/fixtures/kernel-readonly-experiment-matrix/project05-depth2-public-v0.1/matrix-result.json": "9cdfdb7fc87e9ac41ad58c8975ad6428202fd974ef8c9cf453d9a8e67611ff42",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SI002EvidenceToAuthorityDecisionBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema)
        cls.policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        cls.expected_record = yaml.safe_load(RECORD_PATH.read_text(encoding="utf-8"))
        cls.red_design = json.loads(RED_DESIGN_PATH.read_text(encoding="utf-8"))

    def authority(self) -> dict[str, object]:
        return deepcopy(binding.EXPECTED_AUTHORITY)

    def positive_request(self) -> dict[str, object]:
        return deepcopy(binding.EXPECTED_REQUEST)

    def evaluate(
        self,
        request: object | None = None,
        authority: object | None = None,
    ) -> dict[str, object]:
        return binding.evaluate_si002_evidence_to_authority_decision_binding(
            self.positive_request() if request is None else request,
            test_only_authority=(self.authority() if authority is None else authority),
        )

    def assert_denied(self, record: dict[str, object], decision: str) -> None:
        self.assertEqual(record["decision"], decision)
        self.assertFalse(record["binding_contract_valid"])
        self.assertFalse(record["evidence_to_authority_decision_binding_established"])
        self.assertIsNone(record["bound_evidence_decision"])
        self.assertIsNone(record["bound_authority_decision"])
        self.assertEqual(record["catalog_prerequisite_addressed"], "NONE")
        self.assertEqual(record["class_5_status"], "MISSING")
        self.assertEqual(record["class_1_status"], "MISSING")
        self.assertFalse(record["actual_evaluator_invocation"])
        self.assertFalse(record["evaluator_evidence_instance_present"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["authority_flip_eligible"])
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.validator.validate(record)

    def test_schema_policy_request_authority_and_record_are_closed_world(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        for value in (self.authority(), self.positive_request(), self.policy, self.expected_record):
            with self.subTest(kind=next(iter(value))):
                self.validator.validate(value)
        for value in (self.authority(), self.positive_request(), self.expected_record):
            bad = dict(value)
            bad["unexpected"] = True
            self.assertTrue(list(self.validator.iter_errors(bad)))

    def test_field_catalog_identity_policy_and_record_hash_replay(self) -> None:
        self.assertEqual(5, len(binding.EXPECTED_AUTHORITY))
        self.assertEqual(52, len(binding.EXPECTED_REQUEST))
        self.assertEqual(38, len(self.expected_record))
        self.assertEqual(25, len(binding.DECISION_ENUM))
        self.assertEqual(binding.AUTHORITY_FIELD_CATALOG_HASH, canonical_value_hash(list(binding.AUTHORITY_FIELDS)))
        self.assertEqual(binding.REQUEST_FIELD_CATALOG_HASH, canonical_value_hash(list(binding.REQUEST_FIELDS)))
        self.assertEqual(binding.RECORD_FIELD_CATALOG_HASH, canonical_value_hash(list(binding.RECORD_FIELDS)))
        self.assertEqual(binding.BINDING_CONTRACT_IDENTITY_HASH, canonical_value_hash(binding.BINDING_IDENTITY_COMPONENTS))
        self.assertEqual(self.policy["hash"], canonical_document_hash(self.policy))
        self.assertEqual(self.expected_record["hash"], canonical_document_hash(self.expected_record))
        self.assertEqual(list(binding.DECISION_ENUM), self.policy["decision_enum"])
        self.assertEqual(binding.REASON_CODES, self.policy["reason_codes"])

    def test_positive_record_matches_pinned_yaml_and_keeps_authority_false(self) -> None:
        record = self.evaluate()
        self.assertEqual(record, self.expected_record)
        self.assertTrue(record["binding_contract_valid"])
        self.assertTrue(record["evidence_to_authority_decision_binding_established"])
        self.assertEqual(record["bound_authority_decision"], binding.BOUND_AUTHORITY_DECISION)
        self.assertEqual(record["class_5_status"], "ESTABLISHED_BINDING_SURFACE_ONLY")
        self.assertEqual(record["class_1_status"], "MISSING")
        self.assertFalse(record["all_flip_prerequisites_satisfied"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["authority_flip_eligible"])
        self.assertFalse(record["production_registration_enabled"])

    def test_same_request_same_record_and_hash(self) -> None:
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first, second)
        self.assertEqual(first["hash"], second["hash"])

    def test_authority_gate_is_exact_and_fail_closed(self) -> None:
        authorities: list[object] = [{}, [], "bad"]
        for field in binding.AUTHORITY_FIELDS:
            bad = self.authority()
            bad[field] = "wrong"
            authorities.append(bad)
        extra = self.authority()
        extra["unexpected"] = False
        authorities.append(extra)
        for authority in authorities:
            with self.subTest(authority=authority):
                self.assert_denied(self.evaluate(authority=authority), binding.DENY_TEST_ONLY_AUTHORITY)

    def test_fail_closed_matrix_32_of_32_and_enum_closed(self) -> None:
        def changed(field: str, value: object) -> dict[str, object]:
            request = self.positive_request()
            request[field] = value
            return request

        def missing(field: str) -> dict[str, object]:
            request = self.positive_request()
            request.pop(field)
            return request

        cases: list[tuple[str, str, object, object]] = [
            ("FC-001", binding.POSITIVE_DECISION, self.positive_request(), self.authority()),
            ("FC-002", binding.DENY_TEST_ONLY_AUTHORITY, self.positive_request(), {}),
            ("FC-003", binding.DENY_UNKNOWN_IMPLEMENTATION, changed("implementation_id", "unknown"), self.authority()),
            ("FC-004", binding.DENY_UNKNOWN_IMPLEMENTATION, changed("implementation_id", "*"), self.authority()),
            ("FC-005", binding.DENY_LEGACY_IMPLEMENTATION, changed("implementation_id", binding.LEGACY_IMPLEMENTATION_ID), self.authority()),
            ("FC-006", binding.DENY_UNKNOWN_CAPABILITY_ID, changed("evaluator_capability_id", "*"), self.authority()),
            ("FC-007", binding.DENY_MISSING_CLASS2_BINDING, missing("evaluator_capability_identity_hash"), self.authority()),
            ("FC-008", binding.DENY_CLASS2_HASH_MISMATCH, changed("evaluator_capability_identity_hash", "sha256:" + "0" * 64), self.authority()),
            ("FC-009", binding.DENY_MISSING_CLASS3_BINDING, missing("evidence_contract_identity_hash"), self.authority()),
            ("FC-010", binding.DENY_CLASS3_HASH_MISMATCH, changed("evidence_contract_identity_hash", "sha256:" + "0" * 64), self.authority()),
            ("FC-011", binding.DENY_MISSING_CLASS4_BINDING, missing("class_4_record_hash"), self.authority()),
            ("FC-012", binding.DENY_CLASS4_HASH_OR_DECISION_MISMATCH, changed("class_4_record_content_sha256", "0" * 64), self.authority()),
            ("FC-013", binding.DENY_CLASS4_HASH_OR_DECISION_MISMATCH, changed("class_4_positive_decision", "wrong"), self.authority()),
            ("FC-014", binding.DENY_CLASS4_HASH_OR_DECISION_MISMATCH, changed("class_4_evidence_hash", "sha256:" + "0" * 64), self.authority()),
            ("FC-015", binding.DENY_CLASS4_EVIDENCE_NOT_ACTUAL, changed("class_4_actual_evaluator_invocation", False), self.authority()),
            ("FC-016", binding.DENY_CLASS4_EVIDENCE_AUTHORITY_DRIFT, changed("class_4_evaluation_execution_authority", True), self.authority()),
            ("FC-017", binding.DENY_MISSING_SI002_CHAIN_BINDING, missing("si002_boundary_record_hash"), self.authority()),
            ("FC-018", binding.DENY_SI002_CHAIN_HASH_MISMATCH, changed("si002_gap_catalog_record_hash", "sha256:" + "0" * 64), self.authority()),
            ("FC-019", binding.DENY_BINDING_CONTRACT_IDENTITY_MISMATCH, changed("binding_contract_id", "*"), self.authority()),
            ("FC-020", binding.DENY_BINDING_CONTRACT_IDENTITY_MISMATCH, changed("binding_contract_identity_hash", "sha256:" + "0" * 64), self.authority()),
            ("FC-021", binding.DENY_BINDING_MODE_MISMATCH, changed("binding_mode", "wrong"), self.authority()),
            ("FC-022", binding.DENY_CLASS1_OWNER_FLIP_GO_PRESENT_OR_REQUESTED, changed("explicit_later_owner_flip_go_present", True), self.authority()),
            ("FC-023", binding.DENY_AUTHORITY_TRUE_OR_FLIP_ELIGIBLE, changed("evaluation_execution_authority", True), self.authority()),
            ("FC-024", binding.DENY_AUTHORITY_TRUE_OR_FLIP_ELIGIBLE, changed("planner_execution_authority", True), self.authority()),
            ("FC-025", binding.DENY_PRODUCTION_SCOPE, changed("production_registration_enabled", True), self.authority()),
            ("FC-026", binding.DENY_CATALOG_SCOPE_OVERREACH, changed("class_1_status", "ESTABLISHED"), self.authority()),
            ("FC-027", binding.DENY_RUNNER_RECLASSIFICATION, changed("test_only_runner_invocation_reclassified_as_class_4_or_5", True), self.authority()),
            ("FC-028", binding.DENY_SI003_OR_PART_B_SCOPE, changed("pb_b5_si_003_state", "CLOSED"), self.authority()),
            ("FC-029", binding.DENY_SI003_OR_PART_B_SCOPE, changed("part_b_pass_requested", True), self.authority()),
            ("FC-030", binding.DENY_SI003_OR_PART_B_SCOPE, changed("stop_requested", True), self.authority()),
            ("FC-031", binding.DENY_NONDETERMINISTIC_OR_HIDDEN_INPUT, changed("raw_payload", {"hidden": True}), self.authority()),
            ("FC-032", binding.DENY_NON_CONTRACT_INPUT, changed("unexpected", True), self.authority()),
        ]
        self.assertEqual(32, len(cases))
        red_matrix = self.red_design["fail_closed_matrix"]
        red_expected = {case["case_id"]: case["expected"] for case in red_matrix}
        self.assertEqual(32, len(red_expected))
        self.assertFalse([value for value in red_expected.values() if value not in binding.DECISION_ENUM])
        for case_id, expected, request, authority in cases:
            with self.subTest(case_id=case_id):
                self.assertEqual(expected, red_expected[case_id])
                record = self.evaluate(request=request, authority=authority)
                if expected == binding.POSITIVE_DECISION:
                    self.assertEqual(record, self.expected_record)
                    self.validator.validate(record)
                else:
                    self.assert_denied(record, expected)

    def test_class4_record_and_evidence_hash_replay_and_runner_not_reclassified(self) -> None:
        class4 = yaml.safe_load((ROOT / "configs/part-b-b5-si002-actual-evaluator-invocation-record-v0.1.yaml").read_text(encoding="utf-8"))
        self.assertEqual(class4["hash"], canonical_document_hash(class4))
        evidence = dict(class4["evidence_record"])
        declared = evidence.pop("evidence_hash")
        self.assertEqual(declared, canonical_value_hash(evidence))
        self.assertTrue(class4["actual_evaluator_invocation"])
        self.assertFalse(class4["evaluation_execution_authority"])
        runner = yaml.safe_load((ROOT / "configs/part-b-b5-si002-local-bounded-evaluation-harness-runner-invocation-record-v0.1.yaml").read_text(encoding="utf-8"))
        self.assertTrue(runner["actual_runner_invocation"])
        self.assertFalse(runner["actual_evaluator_invocation"])

    def test_pure_validator_imports_no_callable_runtime(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        forbidden = (
            "from src.planner", "import src.planner",
            "from src.scope.part_b_b5_si002_actual_evaluator_invocation",
            "from src.scope.part_b_b5_si002_local_bounded_evaluation_harness_runner_invocation",
            "import subprocess", "Popen(", "subprocess.run(",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_hard_ban_no_flip_no_production_and_si003_open(self) -> None:
        self.assertEqual(binding.HARD_BAN, self.policy["hard_ban"])
        self.assertFalse(binding.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(binding.EVALUATION_EXECUTION_AUTHORITY)
        self.assertFalse(binding.PLANNER_EXECUTION_AUTHORITY)
        self.assertFalse(binding.AUTHORITY_FLIP_ELIGIBLE)
        self.assertFalse(binding.EXPLICIT_LATER_OWNER_FLIP_GO_PRESENT)
        self.assertEqual(self.expected_record["pb_b5_si_003_state"], "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION")

    def test_accepted_red_primary_and_protected_pins_zero_drift(self) -> None:
        self.assertEqual(3, len(ACCEPTED_RED_PINS))
        self.assertEqual(14, len(PRIMARY_PINS))
        self.assertEqual(13, len(PROTECTED_PINS))
        for group in (ACCEPTED_RED_PINS, PRIMARY_PINS, PROTECTED_PINS):
            for relative, expected in group.items():
                with self.subTest(relative=relative):
                    self.assertEqual(file_sha256(ROOT / relative), expected)


if __name__ == "__main__":
    unittest.main()
