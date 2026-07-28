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
    part_b_b5_si002_evaluator_execution_capability_identity as identity,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "schemas"
    / "part-b-b5-si002-evaluator-execution-capability-identity.schema.json"
)
POLICY_PATH = (
    ROOT
    / "configs"
    / (
        "part-b-b5-si002-evaluator-execution-capability-"
        "identity-policy-v0.1.yaml"
    )
)
RECORD_PATH = (
    ROOT
    / "configs"
    / (
        "part-b-b5-si002-evaluator-execution-capability-"
        "identity-record-v0.1.yaml"
    )
)
MODULE_PATH = (
    ROOT
    / "src"
    / "scope"
    / "part_b_b5_si002_evaluator_execution_capability_identity.py"
)

ACCEPTED_RED_PINS = [
    (
        "docs/kernel/part-b-b5-si002-evaluator-execution-capability-"
        "identity-owner-go-authorization-v0.1-20260728.json",
        "95836fd33051ff6b4e0030aaae59325dd1b72788d567837ca987cec54fefbf8a",
    ),
    (
        "docs/kernel/part-b-b5-si002-evaluator-execution-capability-"
        "identity-red-design-v0.1-20260728.json",
        "a185061941581b44a8559770b0b1b99d39fe6ee2c4683a623319864349d852c7",
    ),
    (
        "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-part-b-b5-"
        "si002-evaluator-execution-capability-identity-red-review-"
        "packet-v0.1-20260728.json",
        "6a6f7e3c1051e48d66c74d684e91ca43c6a04b08c58a5448316ae14c87ad3b58",
    ),
]

PRIMARY_PIN_TABLE = [
    (
        "docs/kernel/part-b-b5-si002-evaluation-execution-authority-"
        "flip-prerequisite-gap-green-owner-acceptance-v0.1-20260728.json",
        "69e350764c99ea752675b8848894ac876ce5f1bf4eec791f7850b14dd49802fd",
    ),
    (
        "configs/part-b-b5-si002-evaluation-execution-authority-"
        "flip-prerequisite-gap-record-v0.1.yaml",
        "9066ca092e6d0cf6888e3846a85b3656d574bf590b856da7e993ba69a0d1d5f3",
    ),
    (
        "configs/part-b-b5-si002-evaluation-execution-authority-"
        "boundary-record-v0.1.yaml",
        "df8a28daeb194a99019dc348e45a51d0906da8b8db9fda154f4c7a0848b923a5",
    ),
    (
        "configs/part-b-b5-si002-local-bounded-evaluation-harness-"
        "runner-invocation-record-v0.1.yaml",
        "bdbb4a6aea269503eb127bbbc949517ee995f042d09a3810e8af96bfbe30b851",
    ),
    (
        "configs/part-b-b5-si002-bounded-evaluation-harness-"
        "record-v0.1.yaml",
        "24c2d212c133f4ba921cb46547be0868523e4dcda42bb3e59fa3f7a49bf0d421",
    ),
    (
        "src/planner/twin_p10_readonly_wiring.py",
        "1e1434e40191469f17f255905f4021fb273a323672604f0a017afe0384b5b4f9",
    ),
    (
        "src/planner/deterministic_depth1.py",
        "ada6a8065e71fda58dde7e2b71ca19d7aded9a39f4cf5f67fb20d6fc5d7e38ff",
    ),
    (
        "tests/unit/fixtures/kernel_a17_p1e_twin_p10_readonly_wiring_v0.1.json",
        "1191ba71a41c19131d7368df65ac8d345d8865af1aec59e300f7435d7536ddee",
    ),
    (
        "tests/unit/fixtures/kernel_a17_p1e_depth1_planner_v0.1.json",
        "1154c5dec1073e0f42efa734212a6658d9fd9c4492016bbfd484ed7a502d088b",
    ),
    (
        "tests/unit/fixtures/part_b_b5_si002_local_bounded_evaluation_"
        "harness_runner_invocation/synthetic-fixed-case-v0.1.json",
        "5587569a376a087cd648ae8bee00081fc10a5d48b17c63087407542d4412e086",
    ),
]

PROTECTED_ZERO_DRIFT_PINS = [
    (
        "src/planner/twin_p10_readonly_wiring.py",
        "1e1434e40191469f17f255905f4021fb273a323672604f0a017afe0384b5b4f9",
    ),
    (
        "src/planner/deterministic_depth1.py",
        "ada6a8065e71fda58dde7e2b71ca19d7aded9a39f4cf5f67fb20d6fc5d7e38ff",
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
    "B5-SI002-EVAL-CAP-ID-FC-001": identity.POSITIVE_DECISION,
    "B5-SI002-EVAL-CAP-ID-FC-002": identity.DENY_UNKNOWN_IMPLEMENTATION,
    "B5-SI002-EVAL-CAP-ID-FC-003": identity.DENY_UNKNOWN_CAPABILITY_ID,
    "B5-SI002-EVAL-CAP-ID-FC-004": identity.DENY_UNKNOWN_CAPABILITY_ID,
    "B5-SI002-EVAL-CAP-ID-FC-005": identity.DENY_LEGACY_IMPLEMENTATION,
    "B5-SI002-EVAL-CAP-ID-FC-006": (
        identity.DENY_CAPABILITY_SURFACE_MISMATCH
    ),
    "B5-SI002-EVAL-CAP-ID-FC-007": (
        identity.DENY_CAPABILITY_SURFACE_MISMATCH
    ),
    "B5-SI002-EVAL-CAP-ID-FC-008": identity.DENY_HASH_MISMATCH,
    "B5-SI002-EVAL-CAP-ID-FC-009": identity.DENY_HASH_MISMATCH,
    "B5-SI002-EVAL-CAP-ID-FC-010": identity.DENY_HASH_MISMATCH,
    "B5-SI002-EVAL-CAP-ID-FC-011": identity.DENY_MISSING_CHAIN_BINDING,
    "B5-SI002-EVAL-CAP-ID-FC-012": identity.DENY_MISSING_CHAIN_BINDING,
    "B5-SI002-EVAL-CAP-ID-FC-013": identity.DENY_MISSING_CHAIN_BINDING,
    "B5-SI002-EVAL-CAP-ID-FC-014": identity.DENY_MISSING_CHAIN_BINDING,
    "B5-SI002-EVAL-CAP-ID-FC-015": identity.DENY_NONDETERMINISTIC_INPUT,
    "B5-SI002-EVAL-CAP-ID-FC-016": (
        identity.DENY_EXECUTION_OR_EVIDENCE_REQUEST
    ),
    "B5-SI002-EVAL-CAP-ID-FC-017": identity.DENY_AUTHORITY_REQUEST,
    "B5-SI002-EVAL-CAP-ID-FC-018": identity.DENY_CATALOG_SCOPE_OVERREACH,
    "B5-SI002-EVAL-CAP-ID-FC-019": identity.DENY_SI003_OR_PART_B_SCOPE,
    "B5-SI002-EVAL-CAP-ID-FC-020": (
        identity.DENY_LLM_FAMILY_OR_NON_CONTRACT_INPUT
    ),
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBB5SI002EvaluatorCapabilityIdentityTests(unittest.TestCase):
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
            "request_kind": identity.REQUEST_KIND,
            "request_version": "0.1.0",
            "requested_scope": identity.REQUESTED_SCOPE,
            "implementation_id": identity.IMPLEMENTATION_ID,
            "evaluator_capability_id": identity.EVALUATOR_CAPABILITY_ID,
            "evaluator_capability_identity_hash": (
                identity.EVALUATOR_CAPABILITY_IDENTITY_HASH
            ),
            "evaluator_capability_class": (
                identity.EVALUATOR_CAPABILITY_CLASS
            ),
            "capability_profile": identity.CAPABILITY_PROFILE,
            "candidate_module_path": identity.CANDIDATE_MODULE_PATH,
            "candidate_entrypoint": identity.CANDIDATE_ENTRYPOINT,
            "candidate_module_content_sha256": (
                identity.CANDIDATE_MODULE_CONTENT_SHA256
            ),
            "deterministic_dependency_module_path": (
                identity.DETERMINISTIC_DEPENDENCY_MODULE_PATH
            ),
            "deterministic_dependency_content_sha256": (
                identity.DETERMINISTIC_DEPENDENCY_CONTENT_SHA256
            ),
            "twin_fixture_path": identity.TWIN_FIXTURE_PATH,
            "twin_fixture_content_sha256": (
                identity.TWIN_FIXTURE_CONTENT_SHA256
            ),
            "p1e_fixture_path": identity.P1E_FIXTURE_PATH,
            "p1e_fixture_content_sha256": (
                identity.P1E_FIXTURE_CONTENT_SHA256
            ),
            "si002_invocation_fixture_path": (
                identity.SI002_INVOCATION_FIXTURE_PATH
            ),
            "si002_invocation_fixture_content_sha256": (
                identity.SI002_INVOCATION_FIXTURE_CONTENT_SHA256
            ),
            "matching_rule_profile": identity.MATCHING_RULE_PROFILE,
            "deterministic_only": True,
            "si002_contract_record_hash": identity.SI002_CONTRACT_RECORD_HASH,
            "si002_contract_record_content_sha256": (
                identity.SI002_CONTRACT_RECORD_CONTENT_SHA256
            ),
            "si002_invocation_record_hash": (
                identity.SI002_INVOCATION_RECORD_HASH
            ),
            "si002_invocation_record_content_sha256": (
                identity.SI002_INVOCATION_RECORD_CONTENT_SHA256
            ),
            "si002_boundary_record_hash": (
                identity.SI002_BOUNDARY_RECORD_HASH
            ),
            "si002_boundary_record_content_sha256": (
                identity.SI002_BOUNDARY_RECORD_CONTENT_SHA256
            ),
            "si002_gap_catalog_record_hash": (
                identity.SI002_GAP_CATALOG_RECORD_HASH
            ),
            "si002_gap_catalog_record_content_sha256": (
                identity.SI002_GAP_CATALOG_RECORD_CONTENT_SHA256
            ),
            "si002_gap_catalog_acceptance_content_sha256": (
                identity.SI002_GAP_CATALOG_ACCEPTANCE_CONTENT_SHA256
            ),
            "actual_evaluator_invocation": False,
            "evaluation_execution_authority": False,
            "planner_execution_authority": False,
            "production_registration_enabled": False,
            "pb_b5_si_003_state": identity.SI003_STATE,
        }

    def evaluate(
        self, request: dict[str, object] | None = None
    ) -> dict[str, object]:
        return identity.evaluate_si002_evaluator_execution_capability_identity(
            self.positive_request() if request is None else request
        )

    def assert_record(
        self, record: dict[str, object], decision: str
    ) -> None:
        self.assertEqual(decision, record["decision"])
        self.assertEqual(identity.RECORD_FIELDS, set(record))
        self.assertEqual(28, len(record))
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.assertEqual([], list(self.validator.iter_errors(record)))
        self.assertEqual(
            "NONE_IDENTITY_RECORD_ONLY", record["authority_effect"]
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
        if decision == identity.POSITIVE_DECISION:
            self.assertTrue(record["capability_identity_contract_valid"])
            self.assertEqual(
                identity.CATALOG_PREREQUISITE,
                record["catalog_prerequisite_addressed"],
            )
        else:
            self.assertFalse(record["capability_identity_contract_valid"])
            self.assertEqual("NONE", record["catalog_prerequisite_addressed"])

    def test_green_01_schema_validates_policy_request_and_record(
        self,
    ) -> None:
        request = self.positive_request()
        self.assertEqual(identity.REQUEST_FIELDS, set(request))
        self.assertEqual(36, len(request))
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
            identity.EVALUATOR_CAPABILITY_IDENTITY_HASH,
            canonical_value_hash(self.policy["identity_basis"]),
        )
        self.assertEqual(
            identity.EVALUATOR_CAPABILITY_IDENTITY_HASH,
            canonical_value_hash(identity.IDENTITY_BASIS),
        )

    def test_green_03_positive_record_exact_and_deterministic(
        self,
    ) -> None:
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first, second)
        self.assertEqual(first, self.expected_record)
        self.assert_record(first, identity.POSITIVE_DECISION)

    def test_green_04_only_catalog_class_2_is_addressed(self) -> None:
        effect = self.policy["catalog_prerequisite_effect"]
        self.assertEqual(
            identity.CATALOG_PREREQUISITE,
            effect["catalog_prerequisite_addressed"],
        )
        for class_number in (1, 3, 4, 5):
            self.assertEqual(
                "MISSING", effect[f"catalog_class_{class_number}_status"]
            )
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
            "deterministic_depth1(",
            "invoke_local_bounded_evaluation_harness_for_test_only_record(",
            "evaluate_si002_evaluation_execution_authority_boundary(",
            "evaluate_si002_evaluation_execution_authority_"
            "flip_prerequisite_gap_catalog(",
            "subprocess.",
            "os.system(",
        ):
            with self.subTest(forbidden_call=forbidden_call):
                self.assertNotIn(forbidden_call, source)
        self.assertFalse(identity.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(identity.ACTUAL_EVALUATOR_INVOCATION)
        self.assertFalse(identity.EVALUATION_EXECUTION_AUTHORITY)
        self.assertFalse(identity.PLANNER_EXECUTION_AUTHORITY)
        self.assertIn("must not be inferred", identity.HARD_BAN)

    def test_green_06_fail_closed_matrix_is_exactly_20(self) -> None:
        self.assertEqual(20, len(RED_FAIL_CLOSED_MATRIX))
        self.assertEqual(
            {
                f"B5-SI002-EVAL-CAP-ID-FC-{index:03d}"
                for index in range(1, 21)
            },
            set(RED_FAIL_CLOSED_MATRIX),
        )
        schema_decisions = set(self.schema["$defs"]["decision"]["enum"])
        self.assertTrue(
            set(RED_FAIL_CLOSED_MATRIX.values()) <= schema_decisions
        )

    def test_green_07_non_mapping_raises_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            identity.evaluate_si002_evaluator_execution_capability_identity(
                []
            )

    def test_fc_001_exact_identity_valid_no_execution_no_flip(self) -> None:
        self.assert_record(
            self.evaluate(),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-CAP-ID-FC-001"],
        )

    def test_fc_002_unknown_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "unknown_d1"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-CAP-ID-FC-002"],
        )

    def test_fc_003_unknown_capability_id_denies(self) -> None:
        request = self.positive_request()
        request["evaluator_capability_id"] = "unknown_evaluator"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-CAP-ID-FC-003"],
        )

    def test_fc_004_wildcard_fallback_or_multiple_ids_denies(
        self,
    ) -> None:
        for value in ("*", "part_b_b5_*", [identity.EVALUATOR_CAPABILITY_ID]):
            with self.subTest(value=value):
                request = self.positive_request()
                request["evaluator_capability_id"] = value
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-004"
                    ],
                )

    def test_fc_005_legacy_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = identity.LEGACY_IMPLEMENTATION_ID
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-CAP-ID-FC-005"],
        )

    def test_fc_006_candidate_module_path_mismatch_denies(self) -> None:
        request = self.positive_request()
        request["candidate_module_path"] = "src/planner/other.py"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-CAP-ID-FC-006"],
        )

    def test_fc_007_entrypoint_or_profile_mismatch_denies(self) -> None:
        for field in ("candidate_entrypoint", "capability_profile"):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "wrong"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-007"
                    ],
                )

    def test_fc_008_module_or_identity_hash_mismatch_denies(self) -> None:
        for field in (
            "candidate_module_content_sha256",
            "evaluator_capability_identity_hash",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "0" * 64
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-008"
                    ],
                )

    def test_fc_009_dependency_path_or_hash_mismatch_denies(
        self,
    ) -> None:
        for field in (
            "deterministic_dependency_module_path",
            "deterministic_dependency_content_sha256",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "wrong"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-009"
                    ],
                )

    def test_fc_010_fixture_path_or_hash_mismatch_denies(self) -> None:
        for field in (
            "twin_fixture_path",
            "twin_fixture_content_sha256",
            "p1e_fixture_path",
            "p1e_fixture_content_sha256",
            "si002_invocation_fixture_path",
            "si002_invocation_fixture_content_sha256",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "wrong"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-010"
                    ],
                )

    def assert_missing_or_mismatched_chain_denies(
        self, fields: tuple[str, ...], case_id: str
    ) -> None:
        for field in fields:
            for mode in ("missing", "mismatch"):
                with self.subTest(field=field, mode=mode):
                    request = self.positive_request()
                    if mode == "missing":
                        request.pop(field)
                    else:
                        request[field] = "wrong"
                    self.assert_record(
                        self.evaluate(request),
                        RED_FAIL_CLOSED_MATRIX[case_id],
                    )

    def test_fc_011_contract_binding_missing_or_mismatch_denies(
        self,
    ) -> None:
        self.assert_missing_or_mismatched_chain_denies(
            (
                "si002_contract_record_hash",
                "si002_contract_record_content_sha256",
            ),
            "B5-SI002-EVAL-CAP-ID-FC-011",
        )

    def test_fc_012_invocation_binding_missing_or_mismatch_denies(
        self,
    ) -> None:
        self.assert_missing_or_mismatched_chain_denies(
            (
                "si002_invocation_record_hash",
                "si002_invocation_record_content_sha256",
            ),
            "B5-SI002-EVAL-CAP-ID-FC-012",
        )

    def test_fc_013_boundary_binding_missing_or_mismatch_denies(
        self,
    ) -> None:
        self.assert_missing_or_mismatched_chain_denies(
            (
                "si002_boundary_record_hash",
                "si002_boundary_record_content_sha256",
            ),
            "B5-SI002-EVAL-CAP-ID-FC-013",
        )

    def test_fc_014_gap_catalog_binding_missing_or_mismatch_denies(
        self,
    ) -> None:
        self.assert_missing_or_mismatched_chain_denies(
            (
                "si002_gap_catalog_record_hash",
                "si002_gap_catalog_record_content_sha256",
                "si002_gap_catalog_acceptance_content_sha256",
            ),
            "B5-SI002-EVAL-CAP-ID-FC-014",
        )

    def test_fc_015_nondeterministic_or_hidden_gt_denies(self) -> None:
        for field, value in (
            ("deterministic_only", False),
            ("matching_rule_profile", "RANDOMIZED"),
            ("random_seed", 7),
            ("probability_model", "learned"),
            ("learning_model", "online"),
            ("hidden_ground_truth", "forbidden"),
            ("oracle_label", "forbidden"),
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = value
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-015"
                    ],
                )

    def test_fc_016_execution_or_evidence_request_denies(self) -> None:
        for field in (
            "actual_evaluator_invocation",
            "evaluator_execution_requested",
            "evaluator_evidence_requested",
            "evaluator_execution_evidence",
            "actual_evaluator_invocation_evidence",
            "evaluation_result",
            "runner_execution_requested",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-016"
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
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-017"
                    ],
                )

    def test_fc_018_catalog_class_overreach_denies(self) -> None:
        for field in (
            "owner_flip_go_status",
            "evaluator_execution_evidence_status",
            "actual_evaluator_invocation_evidence_status",
            "evidence_to_authority_binding_status",
            "prerequisites_satisfied",
            "all_flip_prerequisites_satisfied",
            "authority_flip_eligible",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "SATISFIED"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-EVAL-CAP-ID-FC-018"
                    ],
                )

    def test_fc_019_si003_part_b_write_or_stop_denies(self) -> None:
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
                        "B5-SI002-EVAL-CAP-ID-FC-019"
                    ],
                )
        request = self.positive_request()
        request["pb_b5_si_003_state"] = "CLOSED"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-EVAL-CAP-ID-FC-019"],
        )

    def test_fc_020_llm_hidden_production_or_partial_denies(
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
                        "B5-SI002-EVAL-CAP-ID-FC-020"
                    ],
                )
                self.assertNotEqual(
                    identity.POSITIVE_DECISION, record["decision"]
                )
                self.assertFalse(
                    record["capability_identity_contract_valid"]
                )
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
