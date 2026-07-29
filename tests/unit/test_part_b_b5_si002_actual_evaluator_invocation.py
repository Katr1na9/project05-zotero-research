from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)
from src.scope import part_b_b5_si002_actual_evaluator_invocation as invocation


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "part-b-b5-si002-actual-evaluator-invocation.schema.json"
POLICY_PATH = ROOT / "configs" / "part-b-b5-si002-actual-evaluator-invocation-policy-v0.1.yaml"
RECORD_PATH = ROOT / "configs" / "part-b-b5-si002-actual-evaluator-invocation-record-v0.1.yaml"
FIXTURE_PATH = (
    ROOT / "tests" / "unit" / "fixtures"
    / "part_b_b5_si002_actual_evaluator_invocation"
    / "synthetic-fixed-case-v0.1.json"
)
MODULE_PATH = ROOT / "src" / "scope" / "part_b_b5_si002_actual_evaluator_invocation.py"

ACCEPTED_RED_PINS = {
    "docs/kernel/part-b-b5-si002-actual-evaluator-invocation-owner-go-authorization-v0.1-20260729.json": "fc3f3c75f5105524d0460d714531e7b7bf752fdffb7ef623683d6d9c4ff4b99a",
    "docs/kernel/part-b-b5-si002-actual-evaluator-invocation-red-design-v0.1-20260729.json": "9651e523830d09536a9897bf824fec3a98c8a33c78c59f710fd353bcde61bb9f",
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-part-b-b5-si002-actual-evaluator-invocation-red-review-packet-v0.1-20260729.json": "52c259d84c0024ab361ef0f1dad8da8aae9b930b5c0f7c044943e56f1ad7b546",
}

PRIMARY_PINS = {
    "docs/kernel/part-b-b5-si002-evaluator-execution-capability-identity-green-owner-acceptance-v0.1-20260728.json": "2f97fffe9a3fc41a7c5243e096b83a83a31bee8e755572784038ed473ac5ed7d",
    "configs/part-b-b5-si002-evaluator-execution-capability-identity-record-v0.1.yaml": "cc3f169f9b0c365659b6f897ee9ae76d3941f2fe143e480422fcf4f77b7c4c43",
    "docs/kernel/part-b-b5-si002-evaluator-execution-evidence-record-green-owner-acceptance-v0.1-20260728.json": "d3e51ff1ab5d94bd3c9b4c5e67bc0bfa26dd99f4aa3a520968a89f528a010478",
    "schemas/part-b-b5-si002-evaluator-execution-evidence-record.schema.json": "fc24f3bea77f9cc0e14653b47669598050a6634f7cd7188354d1c5f7658112c9",
    "configs/part-b-b5-si002-evaluator-execution-evidence-record-policy-v0.1.yaml": "94ab49361faed1a11164fbf95e901786d33af2d06d26d46647a42a7ce007bdb9",
    "configs/part-b-b5-si002-evaluator-execution-evidence-record-v0.1.yaml": "ac8f979267c83e522d024ac9458ffa345c6f1565beb516c97ff69b59b81115a4",
    "src/scope/part_b_b5_si002_evaluator_execution_evidence_record.py": "7480de3ee3eab25b4a82c7c6cd2f788980ec1a32f196c34a2255d0bac561202e",
    "configs/part-b-b5-si002-bounded-evaluation-harness-record-v0.1.yaml": "24c2d212c133f4ba921cb46547be0868523e4dcda42bb3e59fa3f7a49bf0d421",
    "configs/part-b-b5-si002-local-bounded-evaluation-harness-runner-invocation-record-v0.1.yaml": "bdbb4a6aea269503eb127bbbc949517ee995f042d09a3810e8af96bfbe30b851",
    "configs/part-b-b5-si002-evaluation-execution-authority-boundary-record-v0.1.yaml": "df8a28daeb194a99019dc348e45a51d0906da8b8db9fda154f4c7a0848b923a5",
    "configs/part-b-b5-si002-evaluation-execution-authority-flip-prerequisite-gap-record-v0.1.yaml": "9066ca092e6d0cf6888e3846a85b3656d574bf590b856da7e993ba69a0d1d5f3",
    "docs/kernel/part-b-b5-si002-evaluation-execution-authority-flip-prerequisite-gap-green-owner-acceptance-v0.1-20260728.json": "69e350764c99ea752675b8848894ac876ce5f1bf4eec791f7850b14dd49802fd",
    "tests/unit/fixtures/kernel_a17_p1e_twin_p10_readonly_wiring_v0.1.json": "1191ba71a41c19131d7368df65ac8d345d8865af1aec59e300f7435d7536ddee",
    "tests/unit/fixtures/kernel_a17_p1e_depth1_planner_v0.1.json": "1154c5dec1073e0f42efa734212a6658d9fd9c4492016bbfd484ed7a502d088b",
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
    "docs/llm-editor/llm-editor-v0.8-l2-capacity-audit-metadata-only-v0.1-20260722.json": "711080b388af102a2d55fb1cc22853c0ed0cbdb738483d4d7de709f6459f9db6",
    "src/compiler/llm/kernel_readonly_experiment_matrix_runner.py": "1df1cf43c88289c6877b73ce934ccd6e429641c2a91774b1d59d820292522e0e",
    "docs/llm-editor/fixtures/kernel-readonly-experiment-matrix/project05-depth2-public-v0.1/matrix-result.json": "9cdfdb7fc87e9ac41ad58c8975ad6428202fd974ef8c9cf453d9a8e67611ff42",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBB5SI002ActualEvaluatorInvocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.validator = Draft202012Validator(cls.schema)
        cls.policy = load_yaml(POLICY_PATH)
        cls.expected_record = load_yaml(RECORD_PATH)
        cls.fixture = load_json(FIXTURE_PATH)

    def authority(self) -> dict[str, object]:
        return deepcopy(self.fixture["test_only_authority"])

    def positive_request(self) -> dict[str, object]:
        return deepcopy(self.fixture["invocation_request"])

    def invoke(
        self,
        request: object | None = None,
        authority: object | None = None,
    ) -> dict[str, object]:
        return invocation.invoke_si002_actual_evaluator_for_test_only_evidence_record(
            self.positive_request() if request is None else request,
            test_only_authority=(self.authority() if authority is None else authority),
        )

    def assert_denied(self, record: dict[str, object], decision: str) -> None:
        self.assertEqual(record["decision"], decision)
        self.assertFalse(record["invocation_contract_valid"])
        self.assertFalse(record["actual_evaluator_invocation"])
        self.assertFalse(record["evaluator_evidence_instance_present"])
        self.assertIsNone(record["evidence_record"])
        self.assertIsNone(record["evidence_record_hash"])
        self.assertEqual(record["catalog_prerequisite_addressed"], "NONE")
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["authority_flip_eligible"])
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.validator.validate(record)

    def test_schema_is_draft_2020_12_and_closed_world(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        self.validator.validate(self.authority())
        self.validator.validate(self.positive_request())
        record = self.invoke()
        self.validator.validate(record)
        self.validator.validate(record["evidence_record"])
        extra = dict(record)
        extra["unexpected"] = True
        self.assertTrue(list(self.validator.iter_errors(extra)))

    def test_policy_and_expected_record_hash_replay(self) -> None:
        self.assertEqual(
            self.policy["hash"],
            "sha256:b7877bf559de120fae0f2105a7a2932a13dd8692427a54b3d0e609e802b9a440",
        )
        self.assertEqual(self.policy["hash"], canonical_document_hash(self.policy))
        self.assertEqual(self.expected_record["hash"], canonical_document_hash(self.expected_record))

    def test_positive_record_matches_pinned_yaml_and_calls_once(self) -> None:
        original = invocation.twin_wiring.evaluate_twin_p10_fixed_case_for_depth1_candidacy
        with patch.object(
            invocation.twin_wiring,
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
            wraps=original,
        ) as evaluator:
            record = self.invoke()
        self.assertEqual(evaluator.call_count, 1)
        self.assertEqual(record, self.expected_record)
        self.assertEqual(record["decision"], invocation.POSITIVE_DECISION)
        self.assertTrue(record["actual_evaluator_invocation"])
        self.assertTrue(record["evaluator_evidence_instance_present"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["authority_flip_eligible"])
        self.assertFalse(record["production_registration_enabled"])

    def test_authority_failures_precede_callable(self) -> None:
        authorities: list[object] = [{}, [], "authority"]
        for field in tuple(self.authority()):
            bad = self.authority()
            bad[field] = "wrong"
            authorities.append(bad)
        bad_extra = self.authority()
        bad_extra["extra"] = False
        authorities.append(bad_extra)
        for authority in authorities:
            with self.subTest(authority=authority):
                with patch.object(
                    invocation.twin_wiring,
                    "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
                ) as evaluator:
                    record = self.invoke(authority=authority)
                evaluator.assert_not_called()
                self.assert_denied(record, invocation.DENY_TEST_ONLY_AUTHORITY)

    def test_evidence_shape_and_hash_bindings(self) -> None:
        record = self.invoke()
        evidence = record["evidence_record"]
        self.assertEqual(set(evidence), set(invocation.FUTURE_EVIDENCE_REQUIRED_FIELDS))
        self.assertEqual(len(evidence), 17)
        self.assertEqual(
            canonical_value_hash(list(invocation.FUTURE_EVIDENCE_REQUIRED_FIELDS)),
            invocation.FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH,
        )
        self.assertEqual(
            canonical_value_hash(list(invocation.FUTURE_EVIDENCE_HASH_BINDING_FIELDS)),
            invocation.FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH,
        )
        payload = dict(evidence)
        declared = payload.pop("evidence_hash")
        self.assertEqual(declared, canonical_value_hash(payload))
        self.assertEqual(record["evidence_record_hash"], declared)
        self.assertEqual(record["hash"], canonical_document_hash(record))

    def test_same_request_same_record_and_hash(self) -> None:
        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first, second)
        self.assertEqual(first["hash"], second["hash"])
        self.assertEqual(
            first["evaluator_invocation_attempt_id"],
            second["evaluator_invocation_attempt_id"],
        )

    def test_runner_record_is_not_reclassified(self) -> None:
        runner = load_yaml(
            ROOT / "configs"
            / "part-b-b5-si002-local-bounded-evaluation-harness-runner-invocation-record-v0.1.yaml"
        )
        self.assertTrue(runner["actual_runner_invocation"])
        self.assertFalse(runner["actual_evaluator_invocation"])
        self.assertNotEqual(runner["record_class"], self.expected_record["record_class"])

    def test_exact_red_primary_and_protected_pins(self) -> None:
        for group in (ACCEPTED_RED_PINS, PRIMARY_PINS, PROTECTED_PINS):
            for relative, expected in group.items():
                with self.subTest(relative=relative):
                    self.assertEqual(file_sha256(ROOT / relative), expected)

    def test_hard_ban_and_no_production_registration(self) -> None:
        self.assertEqual(self.fixture["hard_ban"], invocation.HARD_BAN)
        self.assertEqual(self.policy["hard_ban"], invocation.HARD_BAN)
        self.assertFalse(invocation.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(invocation.EVALUATION_EXECUTION_AUTHORITY)
        self.assertFalse(invocation.PLANNER_EXECUTION_AUTHORITY)
        self.assertFalse(invocation.AUTHORITY_FLIP_ELIGIBLE)

    def test_runtime_imports_only_accepted_callable_not_runner_or_d1_direct(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn("from src.planner import twin_p10_readonly_wiring", source)
        self.assertNotIn("from src.planner import deterministic_depth1", source)
        self.assertNotIn("import part_b_b5_si002_local_bounded", source)

    def test_fail_closed_matrix_27_of_27(self) -> None:
        positive = self.positive_request()
        cases: list[tuple[str, str, object, object, str | None]] = []
        cases.append(("001", invocation.POSITIVE_DECISION, positive, self.authority(), None))
        cases.append(("002", invocation.DENY_TEST_ONLY_AUTHORITY, positive, {}, None))
        bad_authority = self.authority(); bad_authority["owner_go_content_sha256"] = "0" * 64
        cases.append(("003", invocation.DENY_TEST_ONLY_AUTHORITY, positive, bad_authority, None))

        def changed(field: str, value: object) -> dict[str, object]:
            request = self.positive_request(); request[field] = value; return request

        cases.extend([
            ("004", invocation.DENY_UNKNOWN_IMPLEMENTATION, changed("implementation_id", "unknown"), self.authority(), None),
            ("005", invocation.DENY_UNKNOWN_CAPABILITY_ID, changed("evaluator_capability_id", "unknown"), self.authority(), None),
            ("006", invocation.DENY_UNKNOWN_CAPABILITY_ID, changed("evaluator_capability_id", "*"), self.authority(), None),
            ("007", invocation.DENY_LEGACY_IMPLEMENTATION, changed("implementation_id", invocation.LEGACY_IMPLEMENTATION_ID), self.authority(), None),
            ("008", invocation.DENY_MISSING_CLASS2_BINDING, changed("evaluator_capability_identity_record_hash", None), self.authority(), None),
            ("009", invocation.DENY_CLASS2_HASH_MISMATCH, changed("evaluator_capability_identity_hash", "sha256:" + "0" * 64), self.authority(), None),
            ("010", invocation.DENY_MISSING_CLASS3_BINDING, changed("evidence_contract_record_hash", None), self.authority(), None),
            ("011", invocation.DENY_CLASS3_HASH_MISMATCH, changed("evidence_contract_identity_hash", "sha256:" + "0" * 64), self.authority(), None),
            ("012", invocation.DENY_EVIDENCE_FIELD_CATALOG_MISMATCH, changed("future_evidence_required_field_count", 18), self.authority(), None),
            ("013", invocation.DENY_MISSING_SI002_CHAIN_BINDING, changed("si002_boundary_record_hash", None), self.authority(), None),
            ("014", invocation.DENY_SI002_CHAIN_HASH_MISMATCH, changed("si002_gap_catalog_record_hash", "sha256:" + "0" * 64), self.authority(), None),
            ("015", invocation.DENY_CALLABLE_IDENTITY_MISMATCH, changed("candidate_entrypoint", "wrong"), self.authority(), None),
            ("016", invocation.DENY_FIXTURE_IDENTITY_MISMATCH, changed("twin_fixture_content_sha256", "0" * 64), self.authority(), None),
            ("017", invocation.DENY_INVOCATION_MODE_OR_PRODUCTION_SCOPE, changed("invocation_mode", "PRODUCTION"), self.authority(), None),
            ("018", invocation.DENY_RUNNER_INVOCATION_RECLASSIFICATION, changed("test_only_runner_invocation_reclassified_as_evaluator_evidence", True), self.authority(), None),
            ("019", invocation.DENY_INVOCATION_MODE_OR_PRODUCTION_SCOPE, changed("requested_actual_evaluator_invocation", False), self.authority(), None),
            ("020", invocation.DENY_EVALUATOR_INVOCATION_FAILURE, positive, self.authority(), "raise"),
            ("021", invocation.DENY_EVALUATOR_OUTPUT_MISMATCH, positive, self.authority(), "bad_status"),
            ("022", invocation.DENY_EVALUATOR_OUTPUT_MISMATCH, positive, self.authority(), "bad_hash"),
            ("023", invocation.DENY_AUTHORITY_OR_BINDING_REQUEST, changed("evaluation_execution_authority", True), self.authority(), None),
            ("024", invocation.DENY_CATALOG_SCOPE_OVERREACH, changed("catalog_class_1_status", "ESTABLISHED"), self.authority(), None),
        ])
        raw_payload = self.positive_request(); raw_payload["raw_payload"] = {"hidden": True}
        cases.append(("025", invocation.DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT, raw_payload, self.authority(), None))
        cases.append(("026", invocation.DENY_SI003_OR_PART_B_SCOPE, changed("part_b_pass_requested", True), self.authority(), None))
        non_contract = self.positive_request(); non_contract["unexpected"] = True
        cases.append(("027", invocation.DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT, non_contract, self.authority(), None))
        self.assertEqual(len(cases), 27)

        for case_id, expected, request, authority, behavior in cases:
            with self.subTest(case_id=case_id):
                if behavior == "raise":
                    side_effect = TimeoutError("test-only timeout")
                    with patch.object(
                        invocation.twin_wiring,
                        "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
                        side_effect=side_effect,
                    ):
                        record = self.invoke(request=request, authority=authority)
                elif behavior == "bad_status":
                    with patch.object(
                        invocation.twin_wiring,
                        "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
                        return_value={"wiring_status": "WRONG", "decision_record": None},
                    ):
                        record = self.invoke(request=request, authority=authority)
                elif behavior == "bad_hash":
                    with patch.object(
                        invocation.twin_wiring,
                        "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
                        return_value={
                            "wiring_status": "CANDIDACY_SIDECAR_EMITTED_NO_TRACE_BINDING",
                            "decision_record": {"decision": "SELECT_ACTION"},
                        },
                    ):
                        record = self.invoke(request=request, authority=authority)
                else:
                    record = self.invoke(request=request, authority=authority)
                if expected == invocation.POSITIVE_DECISION:
                    self.assertEqual(record["decision"], expected)
                    self.validator.validate(record)
                else:
                    self.assert_denied(record, expected)

        red_design = load_json(
            ROOT / "docs" / "kernel"
            / "part-b-b5-si002-actual-evaluator-invocation-red-design-v0.1-20260729.json"
        )
        enum = red_design["future_invocation_decision_record_shape"]["decision_enum"]
        matrix = red_design["fail_closed_matrix"]
        self.assertEqual(len(enum), 23)
        self.assertEqual(len(matrix), 27)
        self.assertFalse([case for case in matrix if case["expected"] not in enum])
        self.assertEqual(set(enum), set(invocation.DECISION_ENUM))


if __name__ == "__main__":
    unittest.main()
