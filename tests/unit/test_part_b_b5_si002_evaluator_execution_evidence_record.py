from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash, canonical_value_hash
from src.scope import (
    part_b_b5_si002_evaluator_execution_evidence_record as evidence,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "schemas"
    / "part-b-b5-si002-evaluator-execution-evidence-record.schema.json"
)
POLICY_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-si002-evaluator-execution-evidence-record-policy-v0.1.yaml"
)
RECORD_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-si002-evaluator-execution-evidence-record-v0.1.yaml"
)
MODULE_PATH = (
    ROOT
    / "src"
    / "scope"
    / "part_b_b5_si002_evaluator_execution_evidence_record.py"
)

ACCEPTED_RED_PINS = [
    (
        "docs/kernel/part-b-b5-si002-evaluator-execution-evidence-record-"
        "owner-go-authorization-v0.1-20260728.json",
        "5579dd009f7060a43caca65cb9bcddc72d8f95c3cdbbd6cc0ffe7f186d3e7789",
    ),
    (
        "docs/kernel/part-b-b5-si002-evaluator-execution-evidence-record-"
        "red-design-v0.1-20260728.json",
        "4b1d258ff4f418c6b1c8693a411531e01e8d7c66ad91d9519445f65d09f5c3d1",
    ),
    (
        "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-part-b-b5-si002-"
        "evaluator-execution-evidence-record-red-review-packet-"
        "v0.1-20260728.json",
        "41d29db1d40e1950481f344e3df21fc4af1e95337e188a96caefd4cc091447d2",
    ),
]

PRIMARY_PIN_TABLE = [
    (
        "docs/kernel/part-b-b5-si002-evaluator-execution-capability-"
        "identity-green-owner-acceptance-v0.1-20260728.json",
        "2f97fffe9a3fc41a7c5243e096b83a83a31bee8e755572784038ed473ac5ed7d",
    ),
    (
        "schemas/part-b-b5-si002-evaluator-execution-capability-"
        "identity.schema.json",
        "19d25891130dab160e30b6af8cafe137d23cce14960d280d73334804acff4d0e",
    ),
    (
        "configs/part-b-b5-si002-evaluator-execution-capability-"
        "identity-policy-v0.1.yaml",
        "f760a4d7e5b891264f5696614bae11e631052d1c21dc2fde9dd18268cb65160f",
    ),
    (
        "configs/part-b-b5-si002-evaluator-execution-capability-"
        "identity-record-v0.1.yaml",
        "cc3f169f9b0c365659b6f897ee9ae76d3941f2fe143e480422fcf4f77b7c4c43",
    ),
    (
        "src/scope/part_b_b5_si002_evaluator_execution_"
        "capability_identity.py",
        "afcf07b5538d1d4f950488411dcbe6a0fe91f8d96f2403aa68157b5e3bf09349",
    ),
    (
        "configs/part-b-b5-si002-bounded-evaluation-harness-"
        "record-v0.1.yaml",
        "24c2d212c133f4ba921cb46547be0868523e4dcda42bb3e59fa3f7a49bf0d421",
    ),
    (
        "configs/part-b-b5-si002-local-bounded-evaluation-harness-"
        "runner-invocation-record-v0.1.yaml",
        "bdbb4a6aea269503eb127bbbc949517ee995f042d09a3810e8af96bfbe30b851",
    ),
    (
        "configs/part-b-b5-si002-evaluation-execution-authority-"
        "boundary-record-v0.1.yaml",
        "df8a28daeb194a99019dc348e45a51d0906da8b8db9fda154f4c7a0848b923a5",
    ),
    (
        "configs/part-b-b5-si002-evaluation-execution-authority-"
        "flip-prerequisite-gap-record-v0.1.yaml",
        "9066ca092e6d0cf6888e3846a85b3656d574bf590b856da7e993ba69a0d1d5f3",
    ),
    (
        "docs/kernel/part-b-b5-si002-evaluator-execution-capability-"
        "identity-green-design-v0.1-20260728.json",
        "1a783ca59380c2a5d35334793f4549f1f23be0ad805df45480c107ef86116791",
    ),
]

PROTECTED_ZERO_DRIFT_PINS = [
    (
        "src/planner/deterministic_depth1.py",
        "ada6a8065e71fda58dde7e2b71ca19d7aded9a39f4cf5f67fb20d6fc5d7e38ff",
    ),
    (
        "src/planner/twin_p10_readonly_wiring.py",
        "1e1434e40191469f17f255905f4021fb273a323672604f0a017afe0384b5b4f9",
    ),
    (
        "src/scope/part_b_b5_planner_admission.py",
        "c6af7e4cbfa9bd98fbc525887456cb2dfaefa19362f4104c5147d1f3943d0be1",
    ),
    (
        "src/scope/part_b_b5_si002_bounded_evaluation_harness_contract.py",
        "6ec634666aaa4fc02ad009abf33a6f3141119f74792e50bb0724dc8a828c947b",
    ),
    (
        "src/scope/part_b_b5_si002_local_bounded_evaluation_"
        "harness_runner_invocation.py",
        "35a2cb52d19126d3934cc30e3989bfd1b8028d4542b614fbbaa649373aff863b",
    ),
    (
        "src/scope/part_b_b5_si002_evaluation_execution_authority_boundary.py",
        "a6c60358a935fbbe9cacd5d703f343a8dba6d177b5a26442749a270ebb76e5cf",
    ),
    (
        "src/scope/part_b_b5_si002_evaluation_execution_authority_"
        "flip_prerequisite_gap.py",
        "c97d813817c4dbf7a789a187de65aad594ef9f93787280c7cb10a24e52afd793",
    ),
    (
        "docs/llm-editor/llm-editor-v0.8-l2-capacity-audit-"
        "metadata-only-v0.1-20260722.json",
        "711080b388af102a2d55fb1cc22853c0ed0cbdb738483d4d7de709f6459f9db6",
    ),
    (
        "src/compiler/llm/kernel_readonly_experiment_matrix_runner.py",
        "1df1cf43c88289c6877b73ce934ccd6e429641c2a91774b1d59d820292522e0e",
    ),
    (
        "docs/llm-editor/fixtures/kernel-readonly-experiment-matrix/"
        "project05-depth2-public-v0.1/matrix-result.json",
        "9cdfdb7fc87e9ac41ad58c8975ad6428202fd974ef8c9cf453d9a8e67611ff42",
    ),
]

RED_FAIL_CLOSED_MATRIX = {
    "B5-SI002-EVAL-EVIDENCE-FC-001": evidence.POSITIVE_DECISION,
    "B5-SI002-EVAL-EVIDENCE-FC-002": (
        evidence.DENY_UNKNOWN_IMPLEMENTATION
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-003": (
        evidence.DENY_UNKNOWN_CAPABILITY_ID
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-004": (
        evidence.DENY_UNKNOWN_CAPABILITY_ID
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-005": (
        evidence.DENY_LEGACY_IMPLEMENTATION
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-006": (
        evidence.DENY_MISSING_IDENTITY_BINDING
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-007": (
        evidence.DENY_IDENTITY_HASH_MISMATCH
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-008": (
        evidence.DENY_IDENTITY_HASH_MISMATCH
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-009": (
        evidence.DENY_EVIDENCE_CONTRACT_SURFACE_MISMATCH
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-010": (
        evidence.DENY_EVIDENCE_CONTRACT_HASH_MISMATCH
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-011": (
        evidence.DENY_EVIDENCE_FIELD_CATALOG_MISMATCH
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-012": (
        evidence.DENY_EVIDENCE_FIELD_CATALOG_MISMATCH
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-013": (
        evidence.DENY_MISSING_SI002_CHAIN_BINDING
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-014": (
        evidence.DENY_SI002_CHAIN_HASH_MISMATCH
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-015": (
        evidence.DENY_RUNNER_INVOCATION_RECLASSIFICATION
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-016": (
        evidence.DENY_ACTUAL_EVIDENCE_OR_INVOCATION
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-017": (
        evidence.DENY_AUTHORITY_REQUEST
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-018": (
        evidence.DENY_CATALOG_SCOPE_OVERREACH
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-019": (
        evidence.DENY_NONDETERMINISTIC_OR_PAYLOAD_INPUT
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-020": (
        evidence.DENY_SI003_OR_PART_B_SCOPE
    ),
    "B5-SI002-EVAL-EVIDENCE-FC-021": (
        evidence.DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT
    ),
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBB5SI002EvaluatorEvidenceRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)
        cls.policy = load_yaml(POLICY_PATH)
        cls.expected_record = load_yaml(RECORD_PATH)

    def positive_request(self) -> dict[str, object]:
        return {
            "schema_version": "0.8.0",
            "request_kind": evidence.REQUEST_KIND,
            "request_version": "0.1.0",
            "requested_scope": evidence.REQUESTED_SCOPE,
            "implementation_id": evidence.IMPLEMENTATION_ID,
            "evaluator_capability_id": evidence.EVALUATOR_CAPABILITY_ID,
            "evaluator_capability_identity_hash": (
                evidence.EVALUATOR_CAPABILITY_IDENTITY_HASH
            ),
            "evaluator_capability_identity_record_hash": (
                evidence.EVALUATOR_CAPABILITY_IDENTITY_RECORD_HASH
            ),
            "evaluator_capability_identity_record_content_sha256": (
                evidence.EVALUATOR_CAPABILITY_IDENTITY_RECORD_CONTENT_SHA256
            ),
            "evaluator_capability_identity_acceptance_content_sha256": (
                evidence.EVALUATOR_CAPABILITY_IDENTITY_ACCEPTANCE_CONTENT_SHA256
            ),
            "evidence_contract_id": evidence.EVIDENCE_CONTRACT_ID,
            "evidence_contract_identity_hash": (
                evidence.EVIDENCE_CONTRACT_IDENTITY_HASH
            ),
            "evidence_record_class": evidence.EVIDENCE_RECORD_CLASS,
            "evidence_origin_mode": evidence.EVIDENCE_ORIGIN_MODE,
            "evidence_binding_profile": evidence.EVIDENCE_BINDING_PROFILE,
            "future_evidence_required_fields_hash": (
                evidence.FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH
            ),
            "future_evidence_required_field_count": 17,
            "future_evidence_hash_binding_fields_hash": (
                evidence.FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH
            ),
            "future_evidence_hash_binding_field_count": 8,
            "si002_contract_record_hash": evidence.SI002_CONTRACT_RECORD_HASH,
            "si002_contract_record_content_sha256": (
                evidence.SI002_CONTRACT_RECORD_CONTENT_SHA256
            ),
            "si002_invocation_record_hash": (
                evidence.SI002_INVOCATION_RECORD_HASH
            ),
            "si002_invocation_record_content_sha256": (
                evidence.SI002_INVOCATION_RECORD_CONTENT_SHA256
            ),
            "si002_boundary_record_hash": (
                evidence.SI002_BOUNDARY_RECORD_HASH
            ),
            "si002_boundary_record_content_sha256": (
                evidence.SI002_BOUNDARY_RECORD_CONTENT_SHA256
            ),
            "si002_gap_catalog_record_hash": (
                evidence.SI002_GAP_CATALOG_RECORD_HASH
            ),
            "si002_gap_catalog_record_content_sha256": (
                evidence.SI002_GAP_CATALOG_RECORD_CONTENT_SHA256
            ),
            "si002_gap_catalog_acceptance_content_sha256": (
                evidence.SI002_GAP_CATALOG_ACCEPTANCE_CONTENT_SHA256
            ),
            "test_only_runner_invocation_record_hash": (
                evidence.TEST_ONLY_RUNNER_INVOCATION_RECORD_HASH
            ),
            "test_only_runner_invocation_reclassified_as_evaluator_evidence": (
                False
            ),
            "evaluator_evidence_instance_present": False,
            "actual_evaluator_invocation": False,
            "evaluation_execution_authority": False,
            "planner_execution_authority": False,
            "production_registration_enabled": False,
            "catalog_class_2_status": evidence.CLASS_2_STATUS,
            "catalog_class_1_status": evidence.MISSING_STATUS,
            "catalog_class_4_status": evidence.MISSING_STATUS,
            "catalog_class_5_status": evidence.MISSING_STATUS,
            "pb_b5_si_003_state": evidence.SI003_STATE,
        }

    def evaluate(
        self, request: dict[str, object] | None = None
    ) -> dict[str, object]:
        return (
            evidence.evaluate_si002_evaluator_execution_evidence_record_contract(
                self.positive_request() if request is None else request
            )
        )

    def assert_record(
        self, record: dict[str, object], decision: str
    ) -> None:
        self.assertEqual(decision, record["decision"])
        self.assertEqual(evidence.RECORD_FIELDS, set(record))
        self.assertEqual(31, len(record))
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.assertEqual([], list(self.validator.iter_errors(record)))
        self.assertEqual(
            "NONE_EVIDENCE_CONTRACT_RECORD_ONLY",
            record["authority_effect"],
        )
        self.assertFalse(record["evaluator_evidence_instance_present"])
        self.assertEqual(
            "ESTABLISHED", record["class_2_identity_status"]
        )
        self.assertFalse(record["other_catalog_prerequisites_satisfied"])
        self.assertFalse(record["all_flip_prerequisites_satisfied"])
        self.assertFalse(record["actual_evaluator_invocation"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["production_registration_enabled"])
        self.assertEqual(
            "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION",
            record["pb_b5_si_003_state"],
        )
        self.assertEqual("NONE", record["stop_authority"])
        if decision == evidence.POSITIVE_DECISION:
            self.assertTrue(record["evidence_record_contract_valid"])
            self.assertEqual(
                evidence.CATALOG_PREREQUISITE,
                record["catalog_prerequisite_addressed"],
            )
        else:
            self.assertFalse(record["evidence_record_contract_valid"])
            self.assertEqual("NONE", record["catalog_prerequisite_addressed"])

    def test_green_01_schema_validates_policy_request_and_record(
        self,
    ) -> None:
        request = self.positive_request()
        self.assertEqual(evidence.REQUEST_FIELDS, set(request))
        self.assertEqual(40, len(request))
        for document in (self.policy, request, self.expected_record):
            with self.subTest(discriminator=tuple(document)[:3]):
                self.assertEqual(
                    [], list(self.validator.iter_errors(document))
                )

    def test_green_02_canonical_hashes_replay(self) -> None:
        self.assertEqual(
            self.policy["hash"], canonical_document_hash(self.policy)
        )
        self.assertEqual(
            self.expected_record["hash"],
            canonical_document_hash(self.expected_record),
        )
        self.assertEqual(
            evidence.EVIDENCE_CONTRACT_IDENTITY_HASH,
            canonical_value_hash(
                self.policy["evidence_contract_identity_basis"]
            ),
        )
        self.assertEqual(
            evidence.FUTURE_EVIDENCE_REQUIRED_FIELDS_HASH,
            canonical_value_hash(
                self.policy["future_evidence_required_fields"]
            ),
        )
        self.assertEqual(
            evidence.FUTURE_EVIDENCE_HASH_BINDING_FIELDS_HASH,
            canonical_value_hash(
                self.policy["future_evidence_hash_binding_fields"]
            ),
        )

    def test_green_03_positive_record_exact_and_deterministic(
        self,
    ) -> None:
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first, second)
        self.assertEqual(first, self.expected_record)
        self.assert_record(first, evidence.POSITIVE_DECISION)

    def test_green_04_class3_contract_only_statuses_frozen(self) -> None:
        effect = self.policy["catalog_prerequisite_effect"]
        self.assertEqual(
            evidence.CATALOG_PREREQUISITE,
            effect["catalog_prerequisite_addressed"],
        )
        self.assertEqual("ESTABLISHED", effect["class_2_identity_status"])
        for class_number in (1, 4, 5):
            self.assertEqual(
                "MISSING", effect[f"class_{class_number}_status"]
            )
        self.assertFalse(effect["evaluator_evidence_instance_present"])
        self.assertFalse(effect["existing_gap_catalog_mutated"])
        self.assertFalse(effect["all_flip_prerequisites_satisfied"])

    def test_green_05_pure_validator_has_no_protected_calls(
        self,
    ) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        self.assertEqual(
            {"__future__", "collections.abc", "src.ir.canonical_hash"},
            imported_modules,
        )
        for forbidden_call in (
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy(",
            "evaluate_si002_evaluator_execution_capability_identity(",
            "invoke_local_bounded_evaluation_harness_for_test_only_record(",
            "deterministic_depth1(",
            "subprocess.",
            "os.system(",
        ):
            with self.subTest(forbidden_call=forbidden_call):
                self.assertNotIn(forbidden_call, source)
        self.assertFalse(evidence.EVALUATOR_EVIDENCE_INSTANCE_PRESENT)
        self.assertFalse(evidence.ACTUAL_EVALUATOR_INVOCATION)
        self.assertFalse(evidence.EVALUATION_EXECUTION_AUTHORITY)
        self.assertFalse(evidence.PLANNER_EXECUTION_AUTHORITY)
        self.assertFalse(evidence.PRODUCTION_REGISTRATION_ENABLED)
        self.assertIn("must not be inferred", evidence.HARD_BAN)

    def test_green_06_fail_closed_matrix_is_exactly_21(self) -> None:
        self.assertEqual(21, len(RED_FAIL_CLOSED_MATRIX))
        self.assertEqual(
            {
                f"B5-SI002-EVAL-EVIDENCE-FC-{index:03d}"
                for index in range(1, 22)
            },
            set(RED_FAIL_CLOSED_MATRIX),
        )
        schema_decisions = set(self.schema["$defs"]["decision"]["enum"])
        self.assertTrue(
            set(RED_FAIL_CLOSED_MATRIX.values()) <= schema_decisions
        )

    def test_green_07_non_mapping_raises_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            evidence.evaluate_si002_evaluator_execution_evidence_record_contract(
                []
            )

    def test_fc_001_exact_contract_valid_no_invocation_no_flip(
        self,
    ) -> None:
        self.assert_record(
            self.evaluate(),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-EVIDENCE-FC-001"],
        )

    def test_fc_002_unknown_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "unknown"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-EVIDENCE-FC-002"],
        )

    def test_fc_003_unknown_capability_id_denies(self) -> None:
        request = self.positive_request()
        request["evaluator_capability_id"] = "unknown"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-EVIDENCE-FC-003"],
        )

    def test_fc_004_wildcard_fallback_or_multiple_ids_denies(
        self,
    ) -> None:
        for value in ("*", "part_b_b5_*", [evidence.EVALUATOR_CAPABILITY_ID]):
            with self.subTest(value=value):
                request = self.positive_request()
                request["evaluator_capability_id"] = value
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-004"
                    ],
                )

    def test_fc_005_legacy_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = evidence.LEGACY_IMPLEMENTATION_ID
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-EVIDENCE-FC-005"],
        )

    def test_fc_006_missing_class2_identity_binding_denies(self) -> None:
        for field in (
            "evaluator_capability_identity_record_hash",
            "evaluator_capability_identity_record_content_sha256",
            "evaluator_capability_identity_acceptance_content_sha256",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request.pop(field)
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-006"
                    ],
                )

    def test_fc_007_class2_record_or_acceptance_mismatch_denies(
        self,
    ) -> None:
        for field in (
            "evaluator_capability_identity_record_hash",
            "evaluator_capability_identity_record_content_sha256",
            "evaluator_capability_identity_acceptance_content_sha256",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "wrong"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-007"
                    ],
                )

    def test_fc_008_capability_identity_hash_mismatch_denies(
        self,
    ) -> None:
        request = self.positive_request()
        request["evaluator_capability_identity_hash"] = "wrong"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-EVIDENCE-FC-008"],
        )

    def test_fc_009_contract_surface_mismatch_denies(self) -> None:
        for field in (
            "evidence_contract_id",
            "evidence_record_class",
            "evidence_origin_mode",
            "evidence_binding_profile",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "wrong"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-009"
                    ],
                )

    def test_fc_010_contract_identity_hash_mismatch_denies(self) -> None:
        request = self.positive_request()
        request["evidence_contract_identity_hash"] = "wrong"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-EVIDENCE-FC-010"],
        )

    def test_fc_011_required_field_catalog_mismatch_denies(
        self,
    ) -> None:
        for field in (
            "future_evidence_required_fields_hash",
            "future_evidence_required_field_count",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "wrong"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-011"
                    ],
                )

    def test_fc_012_hash_binding_catalog_mismatch_denies(
        self,
    ) -> None:
        for field in (
            "future_evidence_hash_binding_fields_hash",
            "future_evidence_hash_binding_field_count",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "wrong"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-012"
                    ],
                )

    def test_fc_013_missing_si002_chain_binding_denies(self) -> None:
        for field in (
            "si002_contract_record_hash",
            "si002_invocation_record_hash",
            "si002_boundary_record_hash",
            "si002_gap_catalog_record_hash",
            "test_only_runner_invocation_record_hash",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request.pop(field)
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-013"
                    ],
                )

    def test_fc_014_si002_chain_hash_mismatch_denies(self) -> None:
        for field in (
            "si002_contract_record_hash",
            "si002_contract_record_content_sha256",
            "si002_invocation_record_hash",
            "si002_invocation_record_content_sha256",
            "si002_boundary_record_hash",
            "si002_boundary_record_content_sha256",
            "si002_gap_catalog_record_hash",
            "si002_gap_catalog_record_content_sha256",
            "si002_gap_catalog_acceptance_content_sha256",
            "test_only_runner_invocation_record_hash",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "wrong"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-014"
                    ],
                )

    def test_fc_015_runner_reclassification_denies(self) -> None:
        request = self.positive_request()
        request[
            "test_only_runner_invocation_reclassified_as_evaluator_evidence"
        ] = True
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-EVIDENCE-FC-015"],
        )

    def test_fc_016_actual_evidence_or_invocation_denies(self) -> None:
        for field in (
            "evaluator_evidence_instance_present",
            "actual_evaluator_invocation",
            "evaluator_invocation_attempt_id",
            "evaluator_invocation_request_hash",
            "evaluator_input_hash",
            "evaluator_output_hash",
            "evidence_hash",
            "evidence_instance",
            "evaluation_result",
            "evaluator_execution_requested",
            "runner_execution_requested",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-016"
                    ],
                )

    def test_fc_017_authority_or_flip_request_denies(self) -> None:
        for field in (
            "evaluation_execution_authority",
            "planner_execution_authority",
            "authority_flip_requested",
            "evaluation_authority_requested",
            "planner_authority_requested",
            "explicit_owner_flip_go",
            "evidence_to_authority_binding",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-017"
                    ],
                )

    def test_fc_018_catalog_scope_overreach_denies(self) -> None:
        for field, value in (
            ("catalog_class_2_status", "MISSING"),
            ("catalog_class_1_status", "SATISFIED"),
            ("catalog_class_4_status", "SATISFIED"),
            ("catalog_class_5_status", "SATISFIED"),
            ("catalog_class_3_status", "SATISFIED"),
            ("prerequisites_satisfied", True),
            ("all_flip_prerequisites_satisfied", True),
            ("authority_flip_eligible", True),
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = value
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-018"
                    ],
                )

    def test_fc_019_nondeterministic_or_payload_input_denies(
        self,
    ) -> None:
        for field in (
            "random_seed",
            "randomized_observation_model",
            "probability_model",
            "learning_model",
            "hidden_ground_truth",
            "oracle_label",
            "evaluator_input",
            "evaluator_output",
            "evaluator_output_payload",
            "raw_evaluator_trace",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "forbidden"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-019"
                    ],
                )

    def test_fc_020_si003_part_b_write_or_stop_denies(self) -> None:
        for field in (
            "pb_b5_si_003_closed",
            "scalarization",
            "performance_claim",
            "superiority_claim",
            "part_b_pass",
            "full_m3_star",
            "b6_execution_requested",
            "b7_execution_requested",
            "b8_execution_requested",
            "b9_execution_requested",
            "path_b_write",
            "mint",
            "kernel_or_e_case_write",
            "certificate",
            "CERTIFIED_STOP",
            "stop_requested",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-020"
                    ],
                )
        request = self.positive_request()
        request["pb_b5_si_003_state"] = "CLOSED"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-EVIDENCE-FC-020"],
        )

    def test_fc_021_llm_hidden_production_or_partial_denies(
        self,
    ) -> None:
        for field, value in (
            ("llm_track_reopen", True),
            ("four_family_reopen", True),
            ("hidden_id", "forbidden"),
            ("raw_source", "forbidden"),
            ("source_uri", "forbidden"),
            ("partial_positive_record_requested", True),
            ("unexpected", "forbidden"),
            ("production_registration_enabled", True),
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = value
                record = self.evaluate(request)
                self.assert_record(
                    record,
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-EVIDENCE-FC-021"
                    ],
                )
                self.assertFalse(record["evidence_record_contract_valid"])
                self.assertEqual(
                    "NONE", record["catalog_prerequisite_addressed"]
                )

    def test_green_08_accepted_red_and_protected_pins_zero_drift(
        self,
    ) -> None:
        self.assertEqual(3, len(ACCEPTED_RED_PINS))
        self.assertEqual(10, len(PRIMARY_PIN_TABLE))
        self.assertEqual(10, len(PROTECTED_ZERO_DRIFT_PINS))
        for group in (
            ACCEPTED_RED_PINS,
            PRIMARY_PIN_TABLE,
            PROTECTED_ZERO_DRIFT_PINS,
        ):
            for relative, expected in group:
                with self.subTest(path=relative):
                    self.assertEqual(file_sha256(ROOT / relative), expected)


if __name__ == "__main__":
    unittest.main()
