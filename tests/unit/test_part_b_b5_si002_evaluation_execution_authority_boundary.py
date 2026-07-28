from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash
from src.scope import (
    part_b_b5_si002_evaluation_execution_authority_boundary as boundary,
)


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    ROOT
    / "src/scope/"
    "part_b_b5_si002_evaluation_execution_authority_boundary.py"
)
SCHEMA_PATH = (
    ROOT
    / "schemas/"
    "part-b-b5-si002-evaluation-execution-authority-boundary.schema.json"
)
POLICY_PATH = (
    ROOT
    / "configs/"
    "part-b-b5-si002-evaluation-execution-authority-boundary-policy-v0.1.yaml"
)
RECORD_PATH = (
    ROOT
    / "configs/"
    "part-b-b5-si002-evaluation-execution-authority-boundary-record-v0.1.yaml"
)

ACCEPTED_RED_PINS = {
    (
        "docs/kernel/part-b-b5-si002-evaluation-execution-"
        "authority-boundary-owner-go-authorization-v0.1-20260728.json"
    ): "b29196a3001a30f0a98849edee90997e58e119af287baf1a7d241f683e2913a0",
    (
        "docs/kernel/part-b-b5-si002-evaluation-execution-"
        "authority-boundary-red-design-v0.1-20260728.json"
    ): "d0a7ee30c75f52417391cbd1633e7d9a1f01a9e89cde824f860f60687d98a995",
    (
        "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-"
        "part-b-b5-si002-evaluation-execution-authority-"
        "boundary-red-review-packet-v0.1-20260728.json"
    ): "aec6aaca4c4d1ca786c496962831126c41c0b42e8a1920c1e37ad6a528f128d9",
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
    (
        "src/scope/part_b_b5_si002_local_bounded_evaluation_"
        "harness_runner_invocation.py"
    ): "35a2cb52d19126d3934cc30e3989bfd1b8028d4542b614fbbaa649373aff863b",
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
    (
        "schemas/part-b-b5-si002-local-bounded-evaluation-"
        "harness-runner-invocation.schema.json"
    ): "ba04cb45d7c219c2cc5ae13d52a24b6c904004a1cca8b1342323279d7e1fa4eb",
    (
        "configs/part-b-b5-si002-local-bounded-evaluation-"
        "harness-runner-invocation-policy-v0.1.yaml"
    ): "0536a8a1b69c89af360df850be709bda1216296704ce872796420e553f9a1a9b",
    (
        "configs/part-b-b5-si002-local-bounded-evaluation-"
        "harness-runner-invocation-record-v0.1.yaml"
    ): "bdbb4a6aea269503eb127bbbc949517ee995f042d09a3810e8af96bfbe30b851",
    (
        "tests/unit/fixtures/part_b_b5_si002_local_bounded_"
        "evaluation_harness_runner_invocation/synthetic-fixed-case-v0.1.json"
    ): "5587569a376a087cd648ae8bee00081fc10a5d48b17c63087407542d4412e086",
}

RED_FAIL_CLOSED_MATRIX = {
    "B5-SI002-AUTH-BOUNDARY-FC-001": boundary.POSITIVE_DECISION,
    "B5-SI002-AUTH-BOUNDARY-FC-002": boundary.DENY_UNKNOWN,
    "B5-SI002-AUTH-BOUNDARY-FC-003": boundary.DENY_UNKNOWN,
    "B5-SI002-AUTH-BOUNDARY-FC-004": boundary.DENY_LEGACY,
    "B5-SI002-AUTH-BOUNDARY-FC-005": boundary.DENY_MISSING,
    "B5-SI002-AUTH-BOUNDARY-FC-006": boundary.DENY_MISSING,
    "B5-SI002-AUTH-BOUNDARY-FC-007": boundary.DENY_MISMATCH,
    "B5-SI002-AUTH-BOUNDARY-FC-008": boundary.DENY_MISMATCH,
    "B5-SI002-AUTH-BOUNDARY-FC-009": boundary.DENY_MISMATCH,
    "B5-SI002-AUTH-BOUNDARY-FC-010": boundary.DENY_SILENT_FLIP,
    "B5-SI002-AUTH-BOUNDARY-FC-011": boundary.DENY_SILENT_FLIP,
    "B5-SI002-AUTH-BOUNDARY-FC-012": boundary.DENY_AUTHORITY,
    "B5-SI002-AUTH-BOUNDARY-FC-013": boundary.DENY_SILENT_FLIP,
    "B5-SI002-AUTH-BOUNDARY-FC-014": boundary.DENY_AUTHORITY,
    "B5-SI002-AUTH-BOUNDARY-FC-015": boundary.DENY_AUTHORITY,
    "B5-SI002-AUTH-BOUNDARY-FC-016": boundary.DENY_AUTHORITY,
    "B5-SI002-AUTH-BOUNDARY-FC-017": boundary.DENY_SI003_OPEN,
    "B5-SI002-AUTH-BOUNDARY-FC-018": boundary.DENY_NON_SUBSTITUTE,
    "B5-SI002-AUTH-BOUNDARY-FC-019": boundary.DENY_NON_CONTRACT,
    "B5-SI002-AUTH-BOUNDARY-FC-020": boundary.DENY_NON_CONTRACT,
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBB5SI002EvaluationExecutionAuthorityBoundaryTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.validator = Draft202012Validator(cls.schema)
        cls.policy = load_yaml(POLICY_PATH)
        cls.expected_record = load_yaml(RECORD_PATH)

    def positive_request(self) -> dict[str, object]:
        return {
            "schema_version": "0.8.0",
            "request_kind": boundary.REQUEST_KIND,
            "request_version": "0.1.0",
            "requested_assessment_scope": (
                boundary.REQUESTED_ASSESSMENT_SCOPE
            ),
            "implementation_id": boundary.IMPLEMENTATION_ID,
            "implementation_identity_hash": (
                boundary.IMPLEMENTATION_IDENTITY_HASH
            ),
            "harness_contract_identity_hash": (
                boundary.HARNESS_CONTRACT_IDENTITY_HASH
            ),
            "si002_contract_record_hash": (
                boundary.SI002_CONTRACT_RECORD_HASH
            ),
            "si002_contract_record_content_sha256": (
                boundary.SI002_CONTRACT_RECORD_CONTENT_SHA256
            ),
            "si002_contract_policy_content_sha256": (
                boundary.SI002_CONTRACT_POLICY_CONTENT_SHA256
            ),
            "si002_invocation_record_hash": (
                boundary.SI002_INVOCATION_RECORD_HASH
            ),
            "si002_invocation_record_content_sha256": (
                boundary.SI002_INVOCATION_RECORD_CONTENT_SHA256
            ),
            "si002_invocation_policy_content_sha256": (
                boundary.SI002_INVOCATION_POLICY_CONTENT_SHA256
            ),
            "invocation_decision": boundary.INVOCATION_DECISION,
            "actual_runner_invocation": True,
            "actual_evaluator_invocation": False,
            "evaluation_execution_authority": False,
            "planner_execution_authority": False,
            "later_separate_owner_authority_flip_go_present": False,
        }

    def evaluate(
        self, request: dict[str, object] | None = None
    ) -> dict[str, object]:
        return boundary.evaluate_si002_evaluation_execution_authority_boundary(
            self.positive_request() if request is None else request
        )

    def assert_record(
        self, record: dict[str, object], decision: str
    ) -> None:
        self.assertEqual(decision, record["decision"])
        self.assertEqual(boundary.RECORD_FIELDS, set(record))
        self.assertEqual(20, len(record))
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.assertEqual(
            "NONE_BOUNDARY_RECORD_ONLY", record["authority_effect"]
        )
        self.assertTrue(record["actual_runner_invocation"])
        self.assertFalse(record["actual_evaluator_invocation"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertFalse(record["planner_execution_authority"])
        self.assertEqual(
            "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION",
            record["pb_b5_si_003_state"],
        )
        self.assertEqual("NONE", record["stop_authority"])
        self.assertEqual([], list(self.validator.iter_errors(record)))

    def test_green_01_schema_validates_policy_request_and_record(
        self,
    ) -> None:
        for document in (
            self.policy,
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

    def test_green_03_positive_record_exact_and_deterministic(
        self,
    ) -> None:
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first, second)
        self.assertEqual(first, self.expected_record)
        self.assert_record(first, boundary.POSITIVE_DECISION)

    def test_green_04_pure_no_invocation_or_authority_flip(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "from src.planner",
            "import src.planner",
            "twin_p10_readonly_wiring",
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy(",
            "evaluate_bounded_evaluation_harness_contract(",
            "invoke_local_bounded_evaluation_harness_for_test_only_record(",
            "import subprocess",
            "Popen(",
            "os.system(",
            "time.perf_counter(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertFalse(boundary.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(boundary.EVALUATION_EXECUTION_AUTHORITY)
        self.assertFalse(boundary.PLANNER_EXECUTION_AUTHORITY)
        self.assertFalse(
            boundary.AUTHORITY_CEILING[
                "evaluation_execution_authority"
            ]
        )
        self.assertEqual(
            "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION",
            boundary.AUTHORITY_CEILING["pb_b5_si_003_state"],
        )
        self.assertIn("must not be inferred", boundary.HARD_BAN)

    def test_green_05_fail_closed_matrix_is_exactly_20(self) -> None:
        self.assertEqual(20, len(RED_FAIL_CLOSED_MATRIX))
        self.assertEqual(
            {
                f"B5-SI002-AUTH-BOUNDARY-FC-{index:03d}"
                for index in range(1, 21)
            },
            set(RED_FAIL_CLOSED_MATRIX),
        )
        schema_decisions = set(
            self.schema["$defs"]["decision"]["enum"]
        )
        self.assertTrue(
            set(RED_FAIL_CLOSED_MATRIX.values()) <= schema_decisions
        )

    def test_fc_001_positive_boundary_valid_no_flip(self) -> None:
        self.assert_record(
            self.evaluate(),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-001"
            ],
        )

    def test_fc_002_unknown_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "unknown_d1"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-002"
            ],
        )

    def test_fc_003_wildcard_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "part_b_b5_*"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-003"
            ],
        )

    def test_fc_004_legacy_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = boundary.LEGACY_IMPLEMENTATION_ID
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-004"
            ],
        )

    def test_fc_005_missing_harness_binding_denies(self) -> None:
        request = self.positive_request()
        request.pop("harness_contract_identity_hash")
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-005"
            ],
        )

    def test_fc_006_missing_invocation_binding_denies(self) -> None:
        request = self.positive_request()
        request.pop("si002_invocation_record_hash")
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-006"
            ],
        )

    def test_fc_007_harness_hash_mismatch_denies(self) -> None:
        request = self.positive_request()
        request["si002_contract_record_hash"] = "sha256:" + "0" * 64
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-007"
            ],
        )

    def test_fc_008_invocation_hash_mismatch_denies(self) -> None:
        request = self.positive_request()
        request["si002_invocation_record_hash"] = "sha256:" + "0" * 64
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-008"
            ],
        )

    def test_fc_009_runner_fact_or_decision_mismatch_denies(
        self,
    ) -> None:
        for field, value in (
            ("actual_runner_invocation", False),
            ("invocation_decision", "UNKNOWN"),
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = value
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-AUTH-BOUNDARY-FC-009"
                    ],
                )

    def test_fc_010_unaccepted_evaluator_fact_denies_silent_flip(
        self,
    ) -> None:
        request = self.positive_request()
        request["actual_evaluator_invocation"] = True
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-010"
            ],
        )

    def test_fc_011_evaluation_authority_true_denies(self) -> None:
        request = self.positive_request()
        request["evaluation_execution_authority"] = True
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-011"
            ],
        )

    def test_fc_012_planner_authority_true_denies(self) -> None:
        request = self.positive_request()
        request["planner_execution_authority"] = True
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-012"
            ],
        )

    def test_fc_013_self_asserted_owner_flip_go_denies(self) -> None:
        request = self.positive_request()
        request["later_separate_owner_authority_flip_go_present"] = True
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-013"
            ],
        )

    def test_fc_014_path_b_mint_or_kernel_write_denies(self) -> None:
        for field in (
            "path_b_write",
            "mint",
            "kernel_or_e_case_write",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-AUTH-BOUNDARY-FC-014"
                    ],
                )

    def test_fc_015_certificate_stop_or_system_state_denies(
        self,
    ) -> None:
        for field in ("certificate", "CERTIFIED_STOP", "system_state"):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-AUTH-BOUNDARY-FC-015"
                    ],
                )

    def test_fc_016_b6_through_b9_execution_denies(self) -> None:
        for field in (
            "b6_execution_requested",
            "b7_execution_requested",
            "b8_execution_requested",
            "b9_execution_requested",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-AUTH-BOUNDARY-FC-016"
                    ],
                )

    def test_fc_017_si003_scalarization_or_performance_denies(
        self,
    ) -> None:
        for field in (
            "pb_b5_si_003_closed",
            "scalarization",
            "scalar_score",
            "performance_claim",
            "measured_performance",
            "rank",
            "superiority_claim",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-AUTH-BOUNDARY-FC-017"
                    ],
                )

    def test_fc_018_part_b_full_m3_or_elevation_denies(
        self,
    ) -> None:
        for field in (
            "part_b_pass",
            "full_m3_star",
            "authority_elevation",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-AUTH-BOUNDARY-FC-018"
                    ],
                )

    def test_fc_019_hidden_external_or_extra_input_denies(
        self,
    ) -> None:
        for field in (
            "unexpected",
            "hidden_id",
            "hidden_ground_truth",
            "oracle_label",
            "holdout_material",
            "raw_source",
            "source_uri",
            "production_registry_state",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "forbidden"
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-AUTH-BOUNDARY-FC-019"
                    ],
                )

    def test_fc_020_no_partial_positive_record_after_failure(
        self,
    ) -> None:
        request = self.positive_request()
        request["partial_positive_record_requested"] = True
        record = self.evaluate(request)
        self.assert_record(
            record,
            RED_FAIL_CLOSED_MATRIX[
                "B5-SI002-AUTH-BOUNDARY-FC-020"
            ],
        )
        self.assertNotEqual(boundary.POSITIVE_DECISION, record["decision"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertFalse(record["actual_evaluator_invocation"])

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
