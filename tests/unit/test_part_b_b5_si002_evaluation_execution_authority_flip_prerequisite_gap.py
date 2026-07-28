from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import (
    canonical_document_hash,
    canonical_value_hash,
)
from src.scope import (
    part_b_b5_si002_evaluation_execution_authority_flip_prerequisite_gap
    as gap,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "schemas"
    / (
        "part-b-b5-si002-evaluation-execution-authority-flip-"
        "prerequisite-gap.schema.json"
    )
)
POLICY_PATH = (
    ROOT
    / "configs"
    / (
        "part-b-b5-si002-evaluation-execution-authority-flip-"
        "prerequisite-gap-policy-v0.1.yaml"
    )
)
RECORD_PATH = (
    ROOT
    / "configs"
    / (
        "part-b-b5-si002-evaluation-execution-authority-flip-"
        "prerequisite-gap-record-v0.1.yaml"
    )
)
MODULE_PATH = (
    ROOT
    / "src"
    / "scope"
    / (
        "part_b_b5_si002_evaluation_execution_authority_flip_"
        "prerequisite_gap.py"
    )
)

ACCEPTED_RED_PINS = {
    (
        "docs/kernel/part-b-b5-si002-evaluation-execution-authority-"
        "flip-prerequisite-gap-owner-go-authorization-v0.1-20260728.json"
    ): "fbe9540fb50f3a6193844bc6913fadc27bf11d373ff78454a9ca1fa892c451c6",
    (
        "docs/kernel/part-b-b5-si002-evaluation-execution-authority-"
        "flip-prerequisite-gap-red-design-v0.1-20260728.json"
    ): "dae6da53a735c3b9b9961dc17f59c9d7127b882592037861847636e8b7fefc37",
    (
        "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-part-b-b5-"
        "si002-evaluation-execution-authority-flip-prerequisite-gap-"
        "red-review-packet-v0.1-20260728.json"
    ): "a07b42a79c7466393cb29ebe26c1983fa5771b770957989e2985c63c0274933b",
}

CHAIN_ARTIFACT_PINS = {
    (
        "docs/kernel/part-b-b5-si002-evaluation-execution-authority-"
        "boundary-green-owner-acceptance-v0.1-20260728.json"
    ): "faf1df2bdd62352690cf9b7871d3c618d99c36ec84d29425c788a740d9226b8b",
    (
        "schemas/part-b-b5-si002-evaluation-execution-authority-"
        "boundary.schema.json"
    ): "d037a94b0d3bbc1288d71add4cc39bf03bb50a08f08844323e0ea4ea8641feae",
    (
        "configs/part-b-b5-si002-evaluation-execution-authority-"
        "boundary-policy-v0.1.yaml"
    ): "aedba3dc775a4cd50bea3d376c67b753821ae54a4f74ace1dd62bcca9b7428b4",
    (
        "configs/part-b-b5-si002-evaluation-execution-authority-"
        "boundary-record-v0.1.yaml"
    ): "df8a28daeb194a99019dc348e45a51d0906da8b8db9fda154f4c7a0848b923a5",
    (
        "docs/kernel/part-b-b5-si002-harness-runner-invocation-"
        "green-owner-acceptance-v0.1-20260728.json"
    ): "b57c59d4dc1186f9aa5ff2909a2bfff5e5af2f1beeffae4ed0b998b40421d2b8",
    (
        "configs/part-b-b5-si002-local-bounded-evaluation-harness-"
        "runner-invocation-policy-v0.1.yaml"
    ): "0536a8a1b69c89af360df850be709bda1216296704ce872796420e553f9a1a9b",
    (
        "configs/part-b-b5-si002-local-bounded-evaluation-harness-"
        "runner-invocation-record-v0.1.yaml"
    ): "bdbb4a6aea269503eb127bbbc949517ee995f042d09a3810e8af96bfbe30b851",
    (
        "docs/kernel/part-b-b5-si002-bounded-evaluation-harness-"
        "green-owner-acceptance-v0.1-20260728.json"
    ): "ccad3e5bf3d55614c1bf9b121f6b7f1e745562a2efb37291148799678bc37fb4",
    (
        "configs/part-b-b5-si002-bounded-evaluation-harness-"
        "policy-v0.1.yaml"
    ): "4263369a1a5fd6f2bdd39ba58cbff1392ecbb90678766f23f39ac3954a364035",
    (
        "configs/part-b-b5-si002-bounded-evaluation-harness-"
        "record-v0.1.yaml"
    ): "24c2d212c133f4ba921cb46547be0868523e4dcda42bb3e59fa3f7a49bf0d421",
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
    (
        "src/scope/part_b_b5_si002_bounded_evaluation_"
        "harness_contract.py"
    ): "6ec634666aaa4fc02ad009abf33a6f3141119f74792e50bb0724dc8a828c947b",
    (
        "src/scope/part_b_b5_si002_local_bounded_evaluation_"
        "harness_runner_invocation.py"
    ): "35a2cb52d19126d3934cc30e3989bfd1b8028d4542b614fbbaa649373aff863b",
    (
        "src/scope/part_b_b5_si002_evaluation_execution_"
        "authority_boundary.py"
    ): "a6c60358a935fbbe9cacd5d703f343a8dba6d177b5a26442749a270ebb76e5cf",
}

RED_FAIL_CLOSED_MATRIX = {
    "B5-SI002-FLIP-GAP-FC-001": gap.POSITIVE_DECISION,
    "B5-SI002-FLIP-GAP-FC-002": gap.DENY_UNKNOWN,
    "B5-SI002-FLIP-GAP-FC-003": gap.DENY_UNKNOWN,
    "B5-SI002-FLIP-GAP-FC-004": gap.DENY_LEGACY,
    "B5-SI002-FLIP-GAP-FC-005": gap.DENY_MISSING,
    "B5-SI002-FLIP-GAP-FC-006": gap.DENY_MISSING,
    "B5-SI002-FLIP-GAP-FC-007": gap.DENY_MISSING,
    "B5-SI002-FLIP-GAP-FC-008": gap.DENY_MISMATCH,
    "B5-SI002-FLIP-GAP-FC-009": gap.DENY_MISMATCH,
    "B5-SI002-FLIP-GAP-FC-010": gap.DENY_MISMATCH,
    "B5-SI002-FLIP-GAP-FC-011": gap.DENY_UNVERIFIED,
    "B5-SI002-FLIP-GAP-FC-012": gap.DENY_UNVERIFIED,
    "B5-SI002-FLIP-GAP-FC-013": gap.DENY_UNVERIFIED,
    "B5-SI002-FLIP-GAP-FC-014": gap.DENY_SILENT_FLIP,
    "B5-SI002-FLIP-GAP-FC-015": gap.DENY_UNVERIFIED,
    "B5-SI002-FLIP-GAP-FC-016": gap.DENY_SILENT_FLIP,
    "B5-SI002-FLIP-GAP-FC-017": gap.DENY_AUTHORITY,
    "B5-SI002-FLIP-GAP-FC-018": gap.DENY_SI003_OPEN,
    "B5-SI002-FLIP-GAP-FC-019": gap.DENY_NON_SUBSTITUTE,
    "B5-SI002-FLIP-GAP-FC-020": gap.DENY_NON_CONTRACT,
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBB5SI002AuthorityFlipPrerequisiteGapTests(unittest.TestCase):
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
            "request_kind": gap.REQUEST_KIND,
            "request_version": "0.1.0",
            "requested_scope": gap.REQUESTED_SCOPE,
            "implementation_id": gap.IMPLEMENTATION_ID,
            "implementation_identity_hash": (
                gap.IMPLEMENTATION_IDENTITY_HASH
            ),
            "si002_contract_record_hash": (
                gap.SI002_CONTRACT_RECORD_HASH
            ),
            "si002_contract_record_content_sha256": (
                gap.SI002_CONTRACT_RECORD_CONTENT_SHA256
            ),
            "si002_invocation_record_hash": (
                gap.SI002_INVOCATION_RECORD_HASH
            ),
            "si002_invocation_record_content_sha256": (
                gap.SI002_INVOCATION_RECORD_CONTENT_SHA256
            ),
            "si002_boundary_record_hash": (
                gap.SI002_BOUNDARY_RECORD_HASH
            ),
            "si002_boundary_record_content_sha256": (
                gap.SI002_BOUNDARY_RECORD_CONTENT_SHA256
            ),
            "si002_boundary_acceptance_content_sha256": (
                gap.SI002_BOUNDARY_ACCEPTANCE_CONTENT_SHA256
            ),
            "owner_flip_go_status": "MISSING",
            "evaluator_capability_identity_status": "MISSING",
            "evaluator_execution_evidence_status": "MISSING",
            "actual_evaluator_invocation_evidence_status": "MISSING",
            "evidence_to_authority_binding_status": "MISSING",
            "missing_prerequisite_count": 5,
            "actual_runner_invocation_record_fact": True,
            "actual_evaluator_invocation": False,
            "evaluation_execution_authority": False,
            "planner_execution_authority": False,
            "pb_b5_si_003_state": gap.SI003_STATE,
        }

    def evaluate(
        self, request: dict[str, object] | None = None
    ) -> dict[str, object]:
        return (
            gap.evaluate_si002_evaluation_execution_authority_flip_prerequisite_gap_catalog(
                self.positive_request() if request is None else request
            )
        )

    def assert_record(
        self, record: dict[str, object], decision: str
    ) -> None:
        self.assertEqual(decision, record["decision"])
        self.assertEqual(gap.RECORD_FIELDS, set(record))
        self.assertEqual(22, len(record))
        self.assertEqual(record["hash"], canonical_document_hash(record))
        self.assertEqual(
            "NONE_GAP_CATALOG_RECORD_ONLY", record["authority_effect"]
        )
        self.assertEqual(5, record["missing_prerequisite_count"])
        self.assertEqual(
            list(gap.MISSING_PREREQUISITE_IDS),
            record["missing_prerequisite_ids"],
        )
        self.assertFalse(record["prerequisites_satisfied"])
        self.assertTrue(record["actual_runner_invocation_record_fact"])
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
        request = self.positive_request()
        self.assertEqual(gap.REQUEST_FIELDS, set(request))
        self.assertEqual(24, len(request))
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
            self.policy["catalog_hash"],
            canonical_value_hash(self.policy["prerequisite_catalog"]),
        )
        self.assertEqual(gap.CATALOG_HASH, self.policy["catalog_hash"])

    def test_green_03_positive_record_exact_and_deterministic(
        self,
    ) -> None:
        first = self.evaluate()
        second = self.evaluate()
        self.assertEqual(first, second)
        self.assertEqual(first, self.expected_record)
        self.assert_record(first, gap.POSITIVE_DECISION)

    def test_green_04_catalog_is_exactly_five_missing_entries(
        self,
    ) -> None:
        entries = self.policy["prerequisite_catalog"]
        self.assertEqual(5, len(entries))
        self.assertEqual(list(gap.PREREQUISITE_CATALOG), entries)
        self.assertEqual(
            ["MISSING"] * 5,
            [entry["current_status"] for entry in entries],
        )
        self.assertFalse(
            self.policy["authority_ceiling"]["prerequisites_satisfied"]
        )

    def test_green_05_pure_no_invocation_or_authority_flip(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "from src.planner",
            "import src.planner",
            "twin_p10_readonly_wiring",
            "part_b_b5_si002_bounded_evaluation_harness_contract",
            "part_b_b5_si002_local_bounded_evaluation_harness_runner",
            "part_b_b5_si002_evaluation_execution_authority_boundary",
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy(",
            "invoke_local_bounded_evaluation_harness_for_test_only_record(",
            "evaluate_si002_evaluation_execution_authority_boundary(",
            "import subprocess",
            "Popen(",
            "os.system(",
            "time.perf_counter(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertFalse(gap.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(gap.ACTUAL_EVALUATOR_INVOCATION)
        self.assertFalse(gap.EVALUATION_EXECUTION_AUTHORITY)
        self.assertFalse(gap.PLANNER_EXECUTION_AUTHORITY)
        self.assertFalse(
            gap.AUTHORITY_CEILING["prerequisites_satisfied"]
        )
        self.assertIn("must not be inferred", gap.HARD_BAN)

    def test_green_06_fail_closed_matrix_is_exactly_20(self) -> None:
        self.assertEqual(20, len(RED_FAIL_CLOSED_MATRIX))
        self.assertEqual(
            {
                f"B5-SI002-FLIP-GAP-FC-{index:03d}"
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

    def test_fc_001_exact_catalog_valid_no_flip(self) -> None:
        self.assert_record(
            self.evaluate(),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-001"],
        )

    def test_fc_002_unknown_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "unknown_d1"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-002"],
        )

    def test_fc_003_wildcard_or_fallback_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "part_b_b5_*"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-003"],
        )

    def test_fc_004_legacy_implementation_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = gap.LEGACY_IMPLEMENTATION_ID
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-004"],
        )

    def test_fc_005_missing_contract_binding_denies(self) -> None:
        request = self.positive_request()
        request.pop("si002_contract_record_hash")
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-005"],
        )

    def test_fc_006_missing_invocation_binding_denies(self) -> None:
        request = self.positive_request()
        request.pop("si002_invocation_record_hash")
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-006"],
        )

    def test_fc_007_missing_boundary_binding_denies(self) -> None:
        request = self.positive_request()
        request.pop("si002_boundary_record_hash")
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-007"],
        )

    def test_fc_008_contract_hash_or_content_mismatch_denies(
        self,
    ) -> None:
        for field in (
            "si002_contract_record_hash",
            "si002_contract_record_content_sha256",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "0" * 64
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-FLIP-GAP-FC-008"
                    ],
                )

    def test_fc_009_invocation_hash_or_content_mismatch_denies(
        self,
    ) -> None:
        for field in (
            "si002_invocation_record_hash",
            "si002_invocation_record_content_sha256",
            "actual_runner_invocation_record_fact",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = False
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-FLIP-GAP-FC-009"
                    ],
                )

    def test_fc_010_boundary_hash_content_or_acceptance_denies(
        self,
    ) -> None:
        for field in (
            "si002_boundary_record_hash",
            "si002_boundary_record_content_sha256",
            "si002_boundary_acceptance_content_sha256",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "0" * 64
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-FLIP-GAP-FC-010"
                    ],
                )

    def test_fc_011_owner_flip_go_claim_denies(self) -> None:
        request = self.positive_request()
        request["owner_flip_go_status"] = "PRESENT"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-011"],
        )

    def test_fc_012_capability_identity_claim_denies(self) -> None:
        request = self.positive_request()
        request["evaluator_capability_identity_status"] = "SATISFIED"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-012"],
        )

    def test_fc_013_execution_evidence_claim_denies(self) -> None:
        request = self.positive_request()
        request["evaluator_execution_evidence_status"] = "PRESENT"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-013"],
        )

    def test_fc_014_evaluator_invocation_claim_denies_silent_flip(
        self,
    ) -> None:
        for field, value in (
            ("actual_evaluator_invocation_evidence_status", "PRESENT"),
            ("actual_evaluator_invocation", True),
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = value
                self.assert_record(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-FLIP-GAP-FC-014"
                    ],
                )

    def test_fc_015_evidence_authority_binding_claim_denies(
        self,
    ) -> None:
        request = self.positive_request()
        request["evidence_to_authority_binding_status"] = "SATISFIED"
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-015"],
        )

    def test_fc_016_evaluation_authority_true_denies(self) -> None:
        request = self.positive_request()
        request["evaluation_execution_authority"] = True
        self.assert_record(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FLIP-GAP-FC-016"],
        )

    def test_fc_017_execution_authority_requests_deny(self) -> None:
        for field in (
            "planner_execution_authority",
            "evaluator_execution_requested",
            "runner_execution_requested",
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
                        "B5-SI002-FLIP-GAP-FC-017"
                    ],
                )

    def test_fc_018_si003_closure_or_performance_denies(self) -> None:
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
                        "B5-SI002-FLIP-GAP-FC-018"
                    ],
                )

    def test_fc_019_non_substitute_or_elevation_denies(self) -> None:
        for field in (
            "part_b_pass",
            "full_m3_star",
            "authority_elevation",
            "prerequisites_satisfied",
            "authority_flip_eligible",
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
                        "B5-SI002-FLIP-GAP-FC-019"
                    ],
                )

    def test_fc_020_extra_hidden_or_partial_positive_denies(
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
            "partial_positive_record_requested",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = "forbidden"
                record = self.evaluate(request)
                self.assert_record(
                    record,
                    RED_FAIL_CLOSED_MATRIX[
                        "B5-SI002-FLIP-GAP-FC-020"
                    ],
                )
                self.assertNotEqual(
                    gap.POSITIVE_DECISION, record["decision"]
                )
                self.assertFalse(record["prerequisites_satisfied"])
                self.assertFalse(record["evaluation_execution_authority"])

    def test_green_07_accepted_and_protected_pins_zero_drift(
        self,
    ) -> None:
        for relative, expected in {
            **ACCEPTED_RED_PINS,
            **CHAIN_ARTIFACT_PINS,
            **PROTECTED_PINS,
        }.items():
            with self.subTest(path=relative):
                self.assertEqual(file_sha256(ROOT / relative), expected)


if __name__ == "__main__":
    unittest.main()
