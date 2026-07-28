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
from src.scope import (
    part_b_b5_si002_local_bounded_evaluation_harness_runner_invocation
    as invocation,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "schemas"
    / (
        "part-b-b5-si002-local-bounded-evaluation-harness-"
        "runner-invocation.schema.json"
    )
)
POLICY_PATH = (
    ROOT
    / "configs"
    / (
        "part-b-b5-si002-local-bounded-evaluation-harness-"
        "runner-invocation-policy-v0.1.yaml"
    )
)
RECORD_PATH = (
    ROOT
    / "configs"
    / (
        "part-b-b5-si002-local-bounded-evaluation-harness-"
        "runner-invocation-record-v0.1.yaml"
    )
)
FIXTURE_PATH = (
    ROOT
    / "tests"
    / "unit"
    / "fixtures"
    / "part_b_b5_si002_local_bounded_evaluation_harness_runner_invocation"
    / "synthetic-fixed-case-v0.1.json"
)
MODULE_PATH = (
    ROOT
    / "src"
    / "scope"
    / (
        "part_b_b5_si002_local_bounded_evaluation_harness_"
        "runner_invocation.py"
    )
)

ACCEPTED_RED_PINS = {
    (
        "docs/kernel/part-b-b5-si002-harness-runner-invocation-"
        "owner-go-authorization-v0.1-20260728.json"
    ): "82db453eb72cad79e686f274496374a713e992ec05a7066186267f08d994caef",
    (
        "docs/kernel/part-b-b5-si002-harness-runner-invocation-"
        "red-design-v0.1-20260728.json"
    ): "b269df49acc47fe723bc25bda702264c65d6df17ebdde682a7bc34bf46e1f437",
    (
        "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-"
        "part-b-b5-si002-harness-runner-invocation-"
        "red-review-packet-v0.1-20260728.json"
    ): "c2392aee1ef7db690613ffb0a8b34a21725e295b3c36f049ca559ea1d8c9e861",
}

PROTECTED_PINS = {
    "src/planner/deterministic_depth1.py": (
        "ada6a8065e71fda58dde7e2b71ca19d7"
        "aded9a39f4cf5f67fb20d6fc5d7e38ff"
    ),
    "src/planner/twin_p10_readonly_wiring.py": (
        "1e1434e40191469f17f255905f4021fb"
        "273a323672604f0a017afe0384b5b4f9"
    ),
    "src/scope/part_b_b5_planner_admission.py": (
        "c6af7e4cbfa9bd98fbc525887456cb2d"
        "faefa19362f4104c5147d1f3943d0be1"
    ),
    "src/scope/part_b_b5_si002_bounded_evaluation_harness_contract.py": (
        "6ec634666aaa4fc02ad009abf33a6f314"
        "1119f74792e50bb0724dc8a828c947b"
    ),
    "configs/part-b-b5-planner-admission-policy-v0.8.yaml": (
        "61496f051f4a7450846928f39ddce7d6"
        "d32f1bb0cd7075dcba721eccbc539550"
    ),
    "configs/part-b-b5-planner-admission-manifest-v0.8.yaml": (
        "463dc34d1b8bed057e3c7629b9645a7d"
        "e6a52a59e635398ea3e4f922ce9a4913"
    ),
    "configs/part-b-bounded-evaluation-v0.8.yaml": (
        "42195a832ee1e88922433aa17d407da7"
        "8825a8b6bafe94cea5bd804c880890c8"
    ),
    "schemas/part-b-bounded-evaluation.schema.json": (
        "a6e6466f00a34bc469b1fe9264004a14"
        "c8906f5b9bb1b4634f88c5a39f20e44e"
    ),
    (
        "schemas/part-b-b5-si002-bounded-evaluation-"
        "harness-contract.schema.json"
    ): "7de56a5598450c567702957c11bac7bfc9b6eb13ef2a272fd3a5dddef68443e0",
    (
        "configs/part-b-b5-si002-bounded-evaluation-"
        "harness-identity-v0.1.yaml"
    ): "3c6df2df7dce5b00d26c468d6aea0fc8991ade19c649aedc3b93188a247ee1b8",
    (
        "configs/part-b-b5-si002-bounded-evaluation-"
        "harness-policy-v0.1.yaml"
    ): "4263369a1a5fd6f2bdd39ba58cbff1392ecbb90678766f23f39ac3954a364035",
    (
        "configs/part-b-b5-si002-bounded-evaluation-"
        "harness-record-v0.1.yaml"
    ): "24c2d212c133f4ba921cb46547be0868523e4dcda42bb3e59fa3f7a49bf0d421",
}

RED_FAIL_CLOSED_MATRIX = {
    "B5-SI002-INV-FC-001": invocation.POSITIVE_DECISION,
    "B5-SI002-INV-FC-002": invocation.DENY_TEST_AUTHORITY,
    "B5-SI002-INV-FC-003": invocation.DENY_UNKNOWN,
    "B5-SI002-INV-FC-004": invocation.DENY_UNKNOWN,
    "B5-SI002-INV-FC-005": invocation.DENY_LEGACY,
    "B5-SI002-INV-FC-006": invocation.DENY_MISSING,
    "B5-SI002-INV-FC-007": invocation.DENY_MISMATCH,
    "B5-SI002-INV-FC-008": invocation.DENY_NON_SYNTHETIC,
    "B5-SI002-INV-FC-009": invocation.DENY_NON_SYNTHETIC,
    "B5-SI002-INV-FC-010": invocation.DENY_AUTHORITY,
    "B5-SI002-INV-FC-011": invocation.DENY_AUTHORITY,
    "B5-SI002-INV-FC-012": invocation.DENY_AUTHORITY,
    "B5-SI002-INV-FC-013": invocation.DENY_AUTHORITY,
    "B5-SI002-INV-FC-014": invocation.DENY_NON_CONTRACT,
    "B5-SI002-INV-FC-015": invocation.DENY_NON_CONTRACT,
    "B5-SI002-INV-FC-016": invocation.DECISION_TIMEOUT,
    "B5-SI002-INV-FC-017": invocation.DECISION_RESOURCE,
    "B5-SI002-INV-FC-018": invocation.DECISION_INFEASIBLE,
    "B5-SI002-INV-FC-019": invocation.DECISION_UNKNOWN,
    "B5-SI002-INV-FC-020": invocation.DENY_MISMATCH,
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBB5SI002LocalHarnessRunnerInvocationTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.validator = Draft202012Validator(cls.schema)
        cls.policy = load_yaml(POLICY_PATH)
        cls.expected_record = load_yaml(RECORD_PATH)
        cls.fixture = load_json(FIXTURE_PATH)

    def authority(self) -> dict[str, object]:
        return {
            "authority_mode": invocation.AUTHORITY_MODE,
            "authorized_cell": invocation.AUTHORIZED_CELL,
            "owner_go_content_sha256": (
                invocation.OWNER_GO_CONTENT_SHA256
            ),
            "allowed_implementation_id": invocation.IMPLEMENTATION_ID,
            "synthetic_declaration_only": True,
            "production_registration_enabled": False,
            "planner_execution_authority": False,
            "evaluation_execution_authority": False,
        }

    def positive_request(self) -> dict[str, object]:
        return {
            "schema_version": "0.8.0",
            "request_kind": invocation.REQUEST_KIND,
            "request_version": "0.1.0",
            "implementation_id": invocation.IMPLEMENTATION_ID,
            "implementation_identity_hash": (
                invocation.IMPLEMENTATION_IDENTITY_HASH
            ),
            "d1_admission_record_hash": (
                invocation.D1_ADMISSION_RECORD_HASH
            ),
            "d1_admission_evidence_hash": (
                invocation.D1_ADMISSION_EVIDENCE_HASH
            ),
            "harness_contract_identity_hash": (
                invocation.HARNESS_CONTRACT_IDENTITY_HASH
            ),
            "si002_contract_record_hash": (
                invocation.SI002_CONTRACT_RECORD_HASH
            ),
            "si002_contract_record_content_sha256": (
                invocation.SI002_CONTRACT_RECORD_CONTENT_SHA256
            ),
            "si002_policy_content_sha256": (
                invocation.SI002_POLICY_CONTENT_SHA256
            ),
            "bounded_evaluation_contract_hash": (
                invocation.BOUNDED_EVALUATION_CONTRACT_HASH
            ),
            "declared_case_id": invocation.DECLARED_CASE_ID,
            "declared_case_binding_hash": (
                invocation.DECLARED_CASE_BINDING_HASH
            ),
            "declared_case_origin": invocation.DECLARED_CASE_ORIGIN,
            "synthetic_fixture_content_sha256": (
                invocation.SYNTHETIC_FIXTURE_CONTENT_SHA256
            ),
            "declared_resource_limits_hash": (
                invocation.DECLARED_RESOURCE_LIMITS_HASH
            ),
            "failure_semantics_hash": (
                invocation.FAILURE_SEMANTICS_HASH
            ),
            "invocation_mode": invocation.INVOCATION_MODE,
            "test_only_runner_invocation_requested": True,
            "production_evaluation_execution_requested": False,
            "planner_execution_authority": False,
            "evaluation_execution_authority": False,
            "stop_authority": "NONE",
        }

    def invoke(
        self,
        request: object | None = None,
        authority: object | None = None,
    ) -> dict[str, object]:
        return invocation.invoke_local_bounded_evaluation_harness_for_test_only_record(
            self.positive_request() if request is None else request,
            test_only_authority=(
                self.authority() if authority is None else authority
            ),
        )

    def assert_record(
        self,
        record: dict[str, object],
        decision: str,
    ) -> None:
        self.assertEqual(decision, record["decision"])
        self.assertEqual(set(record), invocation.RECORD_FIELDS)
        self.assertEqual(26, len(record))
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.assertFalse(record["actual_evaluator_invocation"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertEqual("NONE", record["stop_authority"])
        self.assertEqual([], list(self.validator.iter_errors(record)))

    def test_green_01_closed_world_schema_validates_all_artifacts(
        self,
    ) -> None:
        for document in (
            self.policy,
            self.fixture,
            self.positive_request(),
            self.expected_record,
        ):
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
            invocation.DECLARED_CASE_BINDING_HASH,
            canonical_value_hash(self.fixture["case_declaration"]),
        )
        self.assertEqual(
            invocation.SYNTHETIC_FIXTURE_CONTENT_SHA256,
            file_sha256(FIXTURE_PATH),
        )

    def test_green_03_positive_record_is_exact_and_deterministic(
        self,
    ) -> None:
        original = (
            invocation.twin_wiring
            .evaluate_twin_p10_fixed_case_for_depth1_candidacy
        )
        with patch.object(
            invocation.twin_wiring,
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
            wraps=original,
        ) as delegate:
            first = self.invoke()
        second = self.invoke()

        self.assertEqual(1, delegate.call_count)
        self.assertEqual(first, second)
        self.assertEqual(first, self.expected_record)
        self.assert_record(first, invocation.POSITIVE_DECISION)
        self.assertTrue(first["actual_runner_invocation"])
        self.assertFalse(first["actual_evaluator_invocation"])
        self.assertIsNotNone(first["delegated_decision_record_hash"])
        self.assertEqual(
            "NONE_RECORD_ONLY", self.policy["authority_effect"]
        )

    def test_green_04_delegate_only_and_no_direct_depth1_or_process(
        self,
    ) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "twin_wiring.evaluate_twin_p10_fixed_case_for_depth1_candidacy",
            source,
        )
        for forbidden in (
            "from src.planner import deterministic_depth1",
            "evaluate_depth1_planner_request(",
            "import subprocess",
            "Popen(",
            "os.system(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertFalse(invocation.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(invocation.PLANNER_EXECUTION_AUTHORITY)
        self.assertFalse(invocation.EVALUATION_EXECUTION_AUTHORITY)
        self.assertEqual(
            "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION",
            invocation.AUTHORITY_CEILING["pb_b5_si_003_state"],
        )
        self.assertIn("must not be inferred", invocation.HARD_BAN)

    def test_green_05_fail_closed_matrix_is_exactly_20(self) -> None:
        self.assertEqual(20, len(RED_FAIL_CLOSED_MATRIX))
        self.assertEqual(
            {
                f"B5-SI002-INV-FC-{index:03d}"
                for index in range(1, 21)
            },
            set(RED_FAIL_CLOSED_MATRIX),
        )

    def test_fc_001_positive_test_only_invocation_record(self) -> None:
        self.assert_record(
            self.invoke(), RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-001"]
        )

    def test_fc_002_authority_mismatch_fails_before_delegate(self) -> None:
        invalid_authorities = [
            {},
            {**self.authority(), "unexpected": True},
            {
                **self.authority(),
                "owner_go_content_sha256": "0" * 64,
            },
            {
                **self.authority(),
                "production_registration_enabled": True,
            },
            {
                **self.authority(),
                "evaluation_execution_authority": True,
            },
        ]
        for authority in invalid_authorities:
            with self.subTest(authority=authority), patch.object(
                invocation.twin_wiring,
                "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
            ) as delegate:
                record = self.invoke(authority=authority)
                delegate.assert_not_called()
                self.assert_record(
                    record,
                    RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-002"],
                )
                self.assertFalse(record["actual_runner_invocation"])

    def test_fc_003_unknown_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "unknown_d1"
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-003"],
        )

    def test_fc_004_wildcard_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "part_b_b5_*"
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-004"],
        )

    def test_fc_005_legacy_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "project05_m3star_h3_dual"
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-005"],
        )

    def test_fc_006_missing_si002_binding_denies(self) -> None:
        request = self.positive_request()
        request.pop("si002_contract_record_hash")
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-006"],
        )

    def test_fc_007_hash_mismatch_denies(self) -> None:
        request = self.positive_request()
        request["si002_contract_record_hash"] = "sha256:" + "0" * 64
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-007"],
        )

    def test_fc_008_non_synthetic_or_external_input_denies(
        self,
    ) -> None:
        request = self.positive_request()
        request["declared_case_origin"] = "RECORDED_EXTERNAL"
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-008"],
        )

    def test_fc_009_production_request_denies(self) -> None:
        request = self.positive_request()
        request["production_evaluation_execution_requested"] = True
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-009"],
        )

    def test_fc_010_evaluation_authority_flip_denies(self) -> None:
        request = self.positive_request()
        request["evaluation_execution_authority"] = True
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-010"],
        )

    def test_fc_011_planner_authority_flip_denies(self) -> None:
        request = self.positive_request()
        request["planner_execution_authority"] = True
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-011"],
        )

    def test_fc_012_write_mint_certificate_or_stop_denies(self) -> None:
        for field in (
            "path_b_write",
            "mint",
            "kernel_or_e_case_write",
            "certificate",
            "CERTIFIED_STOP",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.invoke(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-INV-FC-012"
                    ],
                )

    def test_fc_013_scalarization_or_performance_denies(self) -> None:
        request = self.positive_request()
        request["scalar_score"] = 1
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-013"],
        )

    def test_fc_014_extra_field_denies(self) -> None:
        request = self.positive_request()
        request["unexpected"] = True
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-014"],
        )

    def test_fc_015_hidden_or_oracle_material_denies(self) -> None:
        request = self.positive_request()
        request["hidden_ground_truth"] = "W-SUPPORT-H1"
        self.assert_record(
            self.invoke(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-015"],
        )

    def test_fc_016_timeout_is_unknown_no_rank(self) -> None:
        with patch.object(
            invocation.twin_wiring,
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
            side_effect=TimeoutError,
        ):
            record = self.invoke()
        self.assert_record(
            record, RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-016"]
        )
        self.assertTrue(record["actual_runner_invocation"])
        self.assertEqual(
            "TIMEOUT_UNKNOWN_NO_RANK",
            record["invocation_outcome_class"],
        )

    def test_fc_017_resource_exhaustion_is_unknown_no_rank(
        self,
    ) -> None:
        with patch.object(
            invocation.twin_wiring,
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
            side_effect=MemoryError,
        ):
            record = self.invoke()
        self.assert_record(
            record, RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-017"]
        )
        self.assertTrue(record["actual_runner_invocation"])
        self.assertEqual(
            "RESOURCE_EXHAUSTION_UNKNOWN_NO_RANK",
            record["invocation_outcome_class"],
        )

    def test_fc_018_infeasible_is_separate_no_action(self) -> None:
        delegated = {
            "wiring_status": "D1_NONSELECT_DECISION_RETURNED_FAIL_CLOSED",
            "decision_record": {
                "decision": "ABSTAIN",
                "reason_codes": ["P1E-013_NO_ELIGIBLE_ACTION"],
            },
        }
        with patch.object(
            invocation.twin_wiring,
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
            return_value=delegated,
        ):
            record = self.invoke()
        self.assert_record(
            record, RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-018"]
        )
        self.assertEqual(
            "INFEASIBLE_SEPARATE_NO_ACTION",
            record["invocation_outcome_class"],
        )

    def test_fc_019_unknown_delegate_is_no_rank(self) -> None:
        with patch.object(
            invocation.twin_wiring,
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
            return_value=None,
        ):
            record = self.invoke()
        self.assert_record(
            record, RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-019"]
        )
        self.assertEqual(
            "UNKNOWN_NO_RANK", record["invocation_outcome_class"]
        )

    def test_fc_020_pre_invocation_failure_has_no_partial_record(
        self,
    ) -> None:
        request = self.positive_request()
        request["synthetic_fixture_content_sha256"] = "0" * 64
        with patch.object(
            invocation.twin_wiring,
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy",
        ) as delegate:
            record = self.invoke(request)
        delegate.assert_not_called()
        self.assert_record(
            record, RED_FAIL_CLOSED_MATRIX["B5-SI002-INV-FC-020"]
        )
        self.assertFalse(record["actual_runner_invocation"])
        self.assertIsNone(record["delegated_decision_record_hash"])

    def test_green_06_accepted_red_and_protected_pins_zero_drift(
        self,
    ) -> None:
        for relative, expected in {
            **ACCEPTED_RED_PINS,
            **PROTECTED_PINS,
        }.items():
            with self.subTest(path=relative):
                self.assertEqual(file_sha256(ROOT / relative), expected)


if __name__ == "__main__":
    unittest.main()
