from __future__ import annotations

from copy import deepcopy
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
from src.scope.part_b_b5_si002_bounded_evaluation_harness_contract import (
    AUTHORITY_CEILING,
    BOUNDED_EVALUATION_CONFIG_CONTENT_SHA256,
    BOUNDED_EVALUATION_CONTRACT_HASH,
    BOUNDED_EVALUATION_SCHEMA_CONTENT_SHA256,
    D1_ADMISSION_EVIDENCE_HASH,
    D1_ADMISSION_RECORD_HASH,
    FROZEN_FAILURE_SEMANTICS,
    FROZEN_RESOURCE_CAPS,
    IMPLEMENTATION_ID,
    IMPLEMENTATION_IDENTITY_HASH,
    RECORD_SCOPE,
    REQUEST_KIND,
    evaluate_bounded_evaluation_harness_contract,
)


ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATH = (
    ROOT
    / "schemas"
    / "part-b-b5-si002-bounded-evaluation-harness-contract.schema.json"
)
IDENTITY_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-si002-bounded-evaluation-harness-identity-v0.1.yaml"
)
POLICY_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-si002-bounded-evaluation-harness-policy-v0.1.yaml"
)
RECORD_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-si002-bounded-evaluation-harness-record-v0.1.yaml"
)
MODULE_PATH = (
    ROOT
    / "src"
    / "scope"
    / "part_b_b5_si002_bounded_evaluation_harness_contract.py"
)

CASE_BINDING = {
    "case_id": "SI002-SYNTHETIC-CONTRACT-001",
    "origin": "SYNTHETIC_DECLARATION_ONLY",
    "contains_hidden_ground_truth": False,
    "contains_holdout": False,
    "dereference": False,
}

EXPECTED_RECORD_FIELDS = {
    "schema_version",
    "record_class",
    "record_version",
    "request_hash",
    "harness_contract_identity_hash",
    "implementation_id",
    "implementation_identity_hash",
    "d1_admission_record_hash",
    "bounded_evaluation_contract_hash",
    "decision",
    "reason_codes",
    "record_scope",
    "declared_resource_limits_hash",
    "failure_semantics_hash",
    "planner_execution_authority",
    "evaluation_execution_authority",
    "stop_authority",
    "hash",
}

RED_FAIL_CLOSED_MATRIX = {
    "B5-SI002-FC-001": (
        "LOCAL_BOUNDED_EVALUATION_HARNESS_CONTRACT_VALID"
    ),
    "B5-SI002-FC-002": "DENY_UNKNOWN_IMPLEMENTATION",
    "B5-SI002-FC-003": "DENY_UNKNOWN_IMPLEMENTATION",
    "B5-SI002-FC-004": "DENY_LEGACY_IMPLEMENTATION",
    "B5-SI002-FC-005": "DENY_MISSING_EVIDENCE",
    "B5-SI002-FC-006": "DENY_HASH_MISMATCH",
    "B5-SI002-FC-007": "DENY_INVALID_RESOURCE_LIMITS",
    "B5-SI002-FC-008": "DENY_NON_CONTRACT_INPUT",
    "B5-SI002-FC-009": "DENY_AUTHORITY_REQUEST",
    "B5-SI002-FC-010": "DENY_AUTHORITY_REQUEST",
    "B5-SI002-FC-011": "UNKNOWN_NO_RANK",
    "B5-SI002-FC-012": "UNKNOWN_NO_RANK",
    "B5-SI002-FC-013": "SEPARATE_NO_ACTION",
    "B5-SI002-FC-014": "FAIL_CLOSED_NO_RANK",
    "B5-SI002-FC-015": "DENY_NON_CONTRACT_INPUT",
    "B5-SI002-FC-016": "DENY_NON_CONTRACT_INPUT",
    "B5-SI002-FC-017": "DENY_AUTHORITY_REQUEST",
    "B5-SI002-FC-018": "DENY_AUTHORITY_REQUEST",
    "B5-SI002-FC-019": (
        "DENY_NON_SUBSTITUTE_NO_AUTHORITY_ELEVATION"
    ),
    "B5-SI002-FC-020": "DENY_SI_003_REMAINS_OPEN",
}

ACCEPTED_RED_PINS = {
    (
        "docs/kernel/part-b-b5-si002-bounded-evaluation-runner-"
        "owner-go-authorization-v0.1-20260728.json"
    ): "e3ee8b663b1286689289cfbd580764f2b83786f6126637e2bd98e801d343f502",
    (
        "docs/kernel/part-b-b5-si002-bounded-evaluation-runner-"
        "red-design-v0.1-20260728.json"
    ): "1aa722b65a4bb4f5cbcaf66d7858c319605d82c9ebf36ac9b946fc18d7076e38",
    (
        "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-part-b-b5-"
        "si002-bounded-evaluation-runner-red-review-packet-"
        "v0.1-20260728.json"
    ): "df3668b17191c1ab7d01752e103bba84d659c3f008f028fad2c4737dc482446b",
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
    "configs/part-b-b5-planner-admission-policy-v0.8.yaml": (
        "61496f051f4a7450846928f39ddce7d6"
        "d32f1bb0cd7075dcba721eccbc539550"
    ),
    "configs/part-b-b5-planner-admission-manifest-v0.8.yaml": (
        "463dc34d1b8bed057e3c7629b9645a7d"
        "e6a52a59e635398ea3e4f922ce9a4913"
    ),
    "configs/part-b-b5-d1-conformance-implementation-identity-v0.1.yaml": (
        "7d2eaa638e378c9c3f50319753ad3a22"
        "fef9d86c86531ac3f69dca529f795990"
    ),
    "configs/part-b-b5-d1-conformance-admission-evidence-v0.1.yaml": (
        "b44ca2c90e604d621e3cbbe79b311dd1"
        "860ba0ddd5b8b33bbc57892f1a704ebb"
    ),
    "configs/part-b-b5-d1-conformance-admission-record-v0.1.yaml": (
        "c97f5682d219d5898a2edce6ae959a97"
        "98bbaca88ccecf49bdb7e783a9db6ecb"
    ),
    "configs/part-b-b5-d1-conformance-admission-manifest-v0.1.yaml": (
        "19fb231a2a328fb9e8d2b0e0415a08ea"
        "18d1338b25600725d43771c9c2c44bbd"
    ),
    "configs/part-b-bounded-evaluation-v0.8.yaml": (
        "42195a832ee1e88922433aa17d407da7"
        "8825a8b6bafe94cea5bd804c880890c8"
    ),
    "schemas/part-b-bounded-evaluation.schema.json": (
        "a6e6466f00a34bc469b1fe9264004a14"
        "c8906f5b9bb1b4634f88c5a39f20e44e"
    ),
}


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rehash_document(document: dict[str, object]) -> None:
    document["hash"] = canonical_document_hash(document)


class PartBB5SI002BoundedEvaluationHarnessContractTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.validator = Draft202012Validator(cls.schema)
        cls.identity = load_yaml(IDENTITY_PATH)
        cls.policy = load_yaml(POLICY_PATH)
        cls.expected_record = load_yaml(RECORD_PATH)

    def positive_request(self) -> dict[str, object]:
        return {
            "schema_version": "0.8.0",
            "request_kind": REQUEST_KIND,
            "request_version": "0.1.0",
            "implementation_id": IMPLEMENTATION_ID,
            "implementation_identity_hash": (
                IMPLEMENTATION_IDENTITY_HASH
            ),
            "d1_admission_record_hash": D1_ADMISSION_RECORD_HASH,
            "d1_admission_evidence_hash": D1_ADMISSION_EVIDENCE_HASH,
            "bounded_evaluation_contract_hash": (
                BOUNDED_EVALUATION_CONTRACT_HASH
            ),
            "bounded_evaluation_config_content_sha256": (
                BOUNDED_EVALUATION_CONFIG_CONTENT_SHA256
            ),
            "bounded_evaluation_schema_content_sha256": (
                BOUNDED_EVALUATION_SCHEMA_CONTENT_SHA256
            ),
            "harness_contract_identity_hash": self.identity["hash"],
            "declared_case_binding_hash": canonical_value_hash(
                CASE_BINDING
            ),
            "declared_resource_limits_hash": canonical_value_hash(
                FROZEN_RESOURCE_CAPS
            ),
            "execution_requested": False,
            "evaluation_execution_authority": False,
            "planner_execution_authority": False,
        }

    def evaluate(
        self,
        request: dict[str, object] | None = None,
        *,
        identity: dict[str, object] | None = None,
        policy: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return evaluate_bounded_evaluation_harness_contract(
            self.positive_request() if request is None else request,
            identity=self.identity if identity is None else identity,
            policy=self.policy if policy is None else policy,
        )

    def rebound_identity(
        self,
        mutator: object,
    ) -> tuple[dict[str, object], dict[str, object]]:
        identity = deepcopy(self.identity)
        if not callable(mutator):
            raise TypeError("mutator must be callable")
        mutator(identity)
        rehash_document(identity)
        policy = deepcopy(self.policy)
        policy["expected_harness_contract_identity_hash"] = identity[
            "hash"
        ]
        rehash_document(policy)
        return identity, policy

    def assert_decision(
        self,
        record: dict[str, object],
        expected: str,
    ) -> None:
        self.assertEqual(record["decision"], expected)
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertEqual(record["stop_authority"], "NONE")
        self.assertEqual(record["hash"], canonical_document_hash(record))

    def test_green_01_closed_world_artifacts_and_request_validate(
        self,
    ) -> None:
        for document in (
            self.identity,
            self.policy,
            self.positive_request(),
            self.expected_record,
        ):
            with self.subTest(discriminator=tuple(document)[:3]):
                self.assertEqual(
                    list(self.validator.iter_errors(document)),
                    [],
                )

    def test_green_02_canonical_document_and_value_hashes_replay(
        self,
    ) -> None:
        self.assertEqual(
            self.identity["hash"],
            canonical_document_hash(self.identity),
        )
        self.assertEqual(
            self.policy["hash"],
            canonical_document_hash(self.policy),
        )
        self.assertEqual(
            self.expected_record["hash"],
            canonical_document_hash(self.expected_record),
        )
        self.assertEqual(
            canonical_value_hash(FROZEN_RESOURCE_CAPS),
            "sha256:6ad34ed5443dae8244dbf3e4b5ce829e"
            "cb31429f38f7d9dcc27898dcd87f7c81",
        )
        self.assertEqual(
            canonical_value_hash(FROZEN_FAILURE_SEMANTICS),
            "sha256:662294e36b8616d6eb94700b1b6f38dc"
            "758205eb4cbb42032ad184510d8e1c3e",
        )

    def test_green_03_positive_record_exact_and_deterministic(self) -> None:
        left = self.evaluate()
        right = self.evaluate()
        self.assertEqual(left, right)
        self.assertEqual(left, self.expected_record)
        self.assertEqual(set(left), EXPECTED_RECORD_FIELDS)
        self.assertEqual(
            left["record_scope"],
            "LOCAL_BOUNDED_EVALUATION_HARNESS_CONTRACT_OR_RECORD_ONLY",
        )

    def test_green_04_module_has_no_execution_dependencies(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "import subprocess",
            "import time",
            "import resource",
            "Popen(",
            "run(",
            "evaluate_admission(",
            "evaluate_depth1_planner_request(",
            "evaluate_twin_p10_fixed_case_for_depth1_candidacy(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_green_05_matrix_has_exact_20_cases(self) -> None:
        self.assertEqual(len(RED_FAIL_CLOSED_MATRIX), 20)
        self.assertEqual(
            set(RED_FAIL_CLOSED_MATRIX),
            {
                f"B5-SI002-FC-{index:03d}"
                for index in range(1, 21)
            },
        )

    def test_fc_001_exact_contract_is_valid_only(self) -> None:
        self.assert_decision(
            self.evaluate(),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-001"],
        )

    def test_fc_002_unknown_id_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "UNKNOWN-D1"
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-002"],
        )

    def test_fc_003_wildcard_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "part_b_b5_*"
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-003"],
        )

    def test_fc_004_legacy_id_denies(self) -> None:
        request = self.positive_request()
        request["implementation_id"] = "project05_m3star_h3_dual"
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-004"],
        )

    def test_fc_005_missing_evidence_denies(self) -> None:
        request = self.positive_request()
        request.pop("d1_admission_evidence_hash")
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-005"],
        )

    def test_fc_006_hash_mismatch_denies(self) -> None:
        request = self.positive_request()
        request["bounded_evaluation_contract_hash"] = (
            "sha256:" + ("0" * 64)
        )
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-006"],
        )

    def test_fc_007_invalid_resource_limits_deny(self) -> None:
        request = self.positive_request()
        request["declared_resource_limits_hash"] = (
            "sha256:" + ("0" * 64)
        )
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-007"],
        )

    def test_fc_008_retry_or_hidden_fallback_denies(self) -> None:
        def mutate(identity: dict[str, object]) -> None:
            semantics = identity["frozen_failure_semantics"]
            if not isinstance(semantics, dict):
                raise TypeError
            semantics["automatic_retry"] = True

        identity, policy = self.rebound_identity(mutate)
        request = self.positive_request()
        request["harness_contract_identity_hash"] = identity["hash"]
        self.assert_decision(
            self.evaluate(
                request,
                identity=identity,
                policy=policy,
            ),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-008"],
        )

    def test_fc_009_evaluation_execution_request_denies(self) -> None:
        request = self.positive_request()
        request["evaluation_execution_authority"] = True
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-009"],
        )

    def test_fc_010_planner_execution_request_denies(self) -> None:
        request = self.positive_request()
        request["planner_execution_authority"] = True
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-010"],
        )

    def test_fc_011_timeout_is_unknown_no_rank(self) -> None:
        self.assertEqual(
            self.policy["failure_semantics"]["timeout"],
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-011"],
        )
        self.assertFalse(
            self.policy["failure_semantics"]["timeout_as_unsat"]
        )

    def test_fc_012_resource_exhaustion_is_unknown_no_rank(
        self,
    ) -> None:
        self.assertEqual(
            self.policy["failure_semantics"]["resource_exhaustion"],
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-012"],
        )
        self.assertFalse(
            self.policy["failure_semantics"][
                "resource_exhaustion_as_zero_or_loss"
            ]
        )

    def test_fc_013_infeasible_is_separate_no_action(self) -> None:
        self.assertEqual(
            self.policy["failure_semantics"]["infeasible"],
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-013"],
        )
        self.assertFalse(
            self.policy["failure_semantics"]["infeasible_as_high_cost"]
        )

    def test_fc_014_unknown_failure_is_fail_closed_no_rank(
        self,
    ) -> None:
        self.assertEqual(
            self.policy["failure_semantics"]["unknown"],
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-014"],
        )

    def test_fc_015_hidden_or_holdout_material_denies(self) -> None:
        request = self.positive_request()
        request["hidden_ground_truth"] = "FORBIDDEN"
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-015"],
        )

    def test_fc_016_performance_or_scalarization_denies(self) -> None:
        request = self.positive_request()
        request["scalar_score"] = 0
        self.assert_decision(
            self.evaluate(request),
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-016"],
        )
        self.assertFalse(
            self.identity["authority_ceiling"][
                "performance_claim_authority"
            ]
        )
        self.assertFalse(
            self.identity["authority_ceiling"][
                "scalarization_authority"
            ]
        )

    def test_fc_017_write_mint_certificate_or_stop_denies(
        self,
    ) -> None:
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
                self.assert_decision(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-017"],
                )

    def test_fc_018_b6_through_b9_execution_denies(self) -> None:
        for field in (
            "b6_execution_requested",
            "b7_execution_requested",
            "b8_execution_requested",
            "b9_execution_requested",
        ):
            with self.subTest(field=field):
                request = self.positive_request()
                request[field] = True
                self.assert_decision(
                    self.evaluate(request),
                    RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-018"],
                )

    def test_fc_019_record_is_non_substitute_no_elevation(
        self,
    ) -> None:
        self.assertEqual(
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-019"],
            "DENY_NON_SUBSTITUTE_NO_AUTHORITY_ELEVATION",
        )
        record = self.evaluate()
        for forbidden in (
            "part_b_pass",
            "full_m3_star",
            "evaluation_result",
            "performance_metric",
            "system_state",
            "certificate",
            "CERTIFIED_STOP",
        ):
            self.assertNotIn(forbidden, record)
        self.assertEqual(record["record_scope"], RECORD_SCOPE)

    def test_fc_020_si003_remains_open(self) -> None:
        self.assertEqual(
            RED_FAIL_CLOSED_MATRIX["B5-SI002-FC-020"],
            "DENY_SI_003_REMAINS_OPEN",
        )
        self.assertEqual(
            AUTHORITY_CEILING["pb_b5_si_003_state"],
            "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION",
        )

        def mutate(identity: dict[str, object]) -> None:
            ceiling = identity["authority_ceiling"]
            if not isinstance(ceiling, dict):
                raise TypeError
            ceiling["pb_b5_si_003_state"] = "CLOSED"

        identity, policy = self.rebound_identity(mutate)
        request = self.positive_request()
        request["harness_contract_identity_hash"] = identity["hash"]
        self.assert_decision(
            self.evaluate(
                request,
                identity=identity,
                policy=policy,
            ),
            "DENY_AUTHORITY_REQUEST",
        )
        self.assertNotEqual(
            list(self.validator.iter_errors(identity)),
            [],
        )

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
