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
from src.scope.part_b_b5_planner_admission import evaluate_admission


ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATH = (
    ROOT / "schemas" / "part-b-b5-d1-conformance-admission.schema.json"
)
GENERIC_RECORD_SCHEMA_PATH = (
    ROOT / "schemas" / "part-b-b5-planner-admission-record.schema.json"
)
POLICY_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-d1-conformance-admission-policy-v0.1.yaml"
)
IDENTITY_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-d1-conformance-implementation-identity-v0.1.yaml"
)
EVIDENCE_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-d1-conformance-admission-evidence-v0.1.yaml"
)
RECORD_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-d1-conformance-admission-record-v0.1.yaml"
)
MANIFEST_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-d1-conformance-admission-manifest-v0.1.yaml"
)

OLD_POLICY_PATH = (
    ROOT / "configs" / "part-b-b5-planner-admission-policy-v0.8.yaml"
)
OLD_IDENTITY_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-planner-implementation-identity-example-v0.8.yaml"
)
OLD_EVIDENCE_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-planner-admission-evidence-example-v0.8.yaml"
)

IMPLEMENTATION_ID = (
    "part_b_b5_m3_kernel_d1_twin_readonly_conformance_v0.1"
)
LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"
HARD_BAN = (
    "Path A / Kernel design GREEN must not be inferred as L2 PASS, "
    "Part B PASS, or unrestricted Part B elevation."
)

ADDITIVE_PATHS = (
    POLICY_PATH,
    IDENTITY_PATH,
    EVIDENCE_PATH,
    RECORD_PATH,
    MANIFEST_PATH,
)

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
    "schemas/part-b-b5-planner-admission-record.schema.json": (
        "0c198b090d3e85dcb0d29b3c95922684"
        "1c6c8847661a7ce55f2f68a93d804257"
    ),
    "src/actions/selection.py": (
        "16f26fa8ca5fa0fe39a9b901b8b13a09"
        "9f5527ed0c21f77718fd57763f847a83"
    ),
    "src/executor/deterministic.py": (
        "4e5ec71edc536bfef70fe19f86a723ac"
        "57b4ab5370bc845fa074ad2d107ba32a"
    ),
    "src/cli/kernel_e2e.py": (
        "8a7807c32d70e98ac5a36bda3a56f227"
        "9ebffbe23e0d2c6a11286bdba9208d60"
    ),
    "tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/resource_trace.jsonl": (
        "2c3e5da8692070fb44e594666e337bcca"
        "6c4d3d09ad8662eabcbd1ee45c92318"
    ),
}

ACCEPTED_RED_PINS = {
    (
        "docs/kernel/part-b-b5-d1-conformance-admission-"
        "owner-go-authorization-v0.1-20260728.json"
    ): "f2578ccfabdfbe5b232024239a111fd7d7c0bce7b2da19167b5e63b3144a280c",
    (
        "docs/kernel/part-b-b5-d1-conformance-admission-"
        "red-design-v0.1-20260728.json"
    ): "169b1fa785013a15a470264c914bf9a9cce293e4cb4732873ea8fb3df0899931",
    (
        "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-"
        "part-b-b5-d1-conformance-admission-red-review-packet-"
        "v0.1-20260728.json"
    ): "db4f8b1b6f5b4cb6fb59c62bce1e731b8b6570209be00b88fd77d09ae0589082",
}

EXPECTED_RECORD_FIELDS = {
    "schema_version",
    "record_id",
    "record_version",
    "implementation_id",
    "implementation_identity_hash",
    "admission_evidence_hash",
    "policy_hash",
    "decision",
    "reason_codes",
    "admission_scope",
    "planner_execution_authority",
    "evaluation_execution_authority",
    "holdout_release_authority",
    "performance_claim_authority",
    "scalarization_authority",
    "stop_authority",
    "hash",
}


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBB5D1ConformanceAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.validator = Draft202012Validator(cls.schema)
        cls.generic_record_validator = Draft202012Validator(
            load_json(GENERIC_RECORD_SCHEMA_PATH)
        )
        cls.policy = load_yaml(POLICY_PATH)
        cls.identity = load_yaml(IDENTITY_PATH)
        cls.evidence = load_yaml(EVIDENCE_PATH)
        cls.expected_record = load_yaml(RECORD_PATH)
        cls.manifest = load_yaml(MANIFEST_PATH)
        cls.old_policy = load_yaml(OLD_POLICY_PATH)
        cls.old_identity = load_yaml(OLD_IDENTITY_PATH)
        cls.old_evidence = load_yaml(OLD_EVIDENCE_PATH)

    def schema_errors(self, document: object) -> list[object]:
        return list(self.validator.iter_errors(document))

    def evaluate(
        self,
        *,
        identity: dict[str, object] | None = None,
        evidence: dict[str, object] | None = None,
        policy: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return evaluate_admission(
            identity=self.identity if identity is None else identity,
            evidence=self.evidence if evidence is None else evidence,
            policy=self.policy if policy is None else policy,
        )

    def test_green_01_all_additive_artifacts_are_closed_world_valid(
        self,
    ) -> None:
        for path in ADDITIVE_PATHS:
            with self.subTest(path=path.relative_to(ROOT)):
                document = load_yaml(path)
                self.assertEqual(self.schema_errors(document), [])

    def test_green_02_all_canonical_hashes_replay(self) -> None:
        inputs = self.identity["identity_inputs"]
        identity_hashes = self.identity["identity_hashes"]
        expected = {
            "source_tree_hash": canonical_value_hash(
                inputs["source_tree"]
            ),
            "dependency_lock_hash": canonical_value_hash(
                inputs["dependency_lock"]
            ),
            "parameter_manifest_hash": canonical_value_hash(
                inputs["parameter_manifest"]
            ),
            "feature_provenance_hash": canonical_value_hash(
                inputs["feature_provenance"]
            ),
            "runtime_conformance_hash": canonical_value_hash(
                inputs["runtime_conformance"]
            ),
        }
        self.assertEqual(identity_hashes, expected)

        for path in ADDITIVE_PATHS:
            with self.subTest(path=path.relative_to(ROOT)):
                document = load_yaml(path)
                self.assertEqual(
                    document["hash"],
                    canonical_document_hash(document),
                )

    def test_green_03_exact_d1_identity_is_conformance_only(self) -> None:
        record = self.evaluate()
        self.assertEqual(record, self.expected_record)
        self.assertEqual(
            record["decision"],
            "ADMITTED_CONFORMANCE_ONLY",
        )
        self.assertEqual(
            record["admission_scope"],
            "INTERFACE_CONFORMANCE_ONLY",
        )
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertEqual(record["stop_authority"], "NONE")

    def test_green_04_record_exact_fields_and_generic_schema(self) -> None:
        record = self.evaluate()
        self.assertEqual(set(record), EXPECTED_RECORD_FIELDS)
        self.assertEqual(
            list(self.generic_record_validator.iter_errors(record)),
            [],
        )
        self.assertEqual(self.schema_errors(record), [])
        for forbidden in (
            "path_b_write_authority",
            "mint_authority",
            "kernel_or_e_case_write_authority",
            "certificate_authority",
            "system_state",
            "CERTIFIED_STOP",
            "full_m3_star",
            "part_b_pass",
        ):
            self.assertNotIn(forbidden, record)

    def test_green_05_four_slot_missing_and_extra_are_denied(
        self,
    ) -> None:
        missing = deepcopy(self.evidence)
        missing["evidence_slots"].pop("runtime_conformance")
        missing_record = self.evaluate(evidence=missing)
        self.assertEqual(
            missing_record["decision"],
            "DENY_EVIDENCE_INCOMPLETE",
        )
        self.assertNotEqual(self.schema_errors(missing), [])

        extra = deepcopy(self.evidence)
        extra["evidence_slots"]["unexpected"] = deepcopy(
            extra["evidence_slots"]["dependency"]
        )
        extra_record = self.evaluate(evidence=extra)
        self.assertEqual(
            extra_record["decision"],
            "DENY_EVIDENCE_INCOMPLETE",
        )
        self.assertNotEqual(self.schema_errors(extra), [])

    def test_green_06_four_slot_failed_and_mismatch_are_denied(
        self,
    ) -> None:
        runtime_failed = deepcopy(self.evidence)
        runtime_failed["evidence_slots"]["runtime_conformance"][
            "status"
        ] = "FAILED"
        self.assertEqual(
            self.evaluate(evidence=runtime_failed)["decision"],
            "DENY_RUNTIME_CONFORMANCE_FAILED",
        )

        dependency_failed = deepcopy(self.evidence)
        dependency_failed["evidence_slots"]["dependency"][
            "status"
        ] = "FAILED"
        self.assertEqual(
            self.evaluate(evidence=dependency_failed)["decision"],
            "DENY_EVIDENCE_INCOMPLETE",
        )

        mismatch = deepcopy(self.evidence)
        mismatch["evidence_slots"]["parameter"]["artifact_hash"] = (
            "sha256:" + ("0" * 64)
        )
        self.assertEqual(
            self.evaluate(evidence=mismatch)["decision"],
            "DENY_EVIDENCE_HASH_MISMATCH",
        )

    def test_green_07_identity_and_document_staleness_fail_preflight(
        self,
    ) -> None:
        stale_source = deepcopy(self.identity)
        stale_source["identity_inputs"]["source_tree"]["artifacts"][0][
            "content_sha256"
        ] = "0" * 64
        self.assertNotEqual(self.schema_errors(stale_source), [])
        self.assertNotEqual(
            canonical_document_hash(stale_source),
            stale_source["hash"],
        )

        stale_policy = deepcopy(self.policy)
        stale_policy["hash"] = "sha256:" + ("0" * 64)
        self.assertEqual(self.schema_errors(stale_policy), [])
        self.assertNotEqual(
            canonical_document_hash(stale_policy),
            stale_policy["hash"],
        )

    def test_green_08_cross_policy_replay_denies(self) -> None:
        new_under_old = self.evaluate(policy=self.old_policy)
        self.assertEqual(
            new_under_old["decision"],
            "DENY_UNKNOWN_IMPLEMENTATION",
        )

        old_under_new = evaluate_admission(
            identity=self.old_identity,
            evidence=self.old_evidence,
            policy=self.policy,
        )
        self.assertEqual(
            old_under_new["decision"],
            "DENY_UNKNOWN_IMPLEMENTATION",
        )

    def test_green_09_legacy_unknown_and_wildcard_deny(self) -> None:
        legacy_identity = deepcopy(self.identity)
        legacy_evidence = deepcopy(self.evidence)
        legacy_identity["implementation_id"] = LEGACY_IMPLEMENTATION_ID
        legacy_evidence["implementation_id"] = LEGACY_IMPLEMENTATION_ID
        legacy = self.evaluate(
            identity=legacy_identity,
            evidence=legacy_evidence,
        )
        self.assertEqual(
            legacy["decision"],
            "DENY_NOT_ADMITTED_UNVERIFIED",
        )

        for unknown_id in ("UNKNOWN-D1", "part_b_b5_*"):
            with self.subTest(implementation_id=unknown_id):
                unknown_identity = deepcopy(self.identity)
                unknown_evidence = deepcopy(self.evidence)
                unknown_identity["implementation_id"] = unknown_id
                unknown_evidence["implementation_id"] = unknown_id
                record = self.evaluate(
                    identity=unknown_identity,
                    evidence=unknown_evidence,
                )
                self.assertEqual(
                    record["decision"],
                    "DENY_UNKNOWN_IMPLEMENTATION",
                )
                self.assertNotEqual(
                    self.schema_errors(unknown_identity),
                    [],
                )

    def test_green_10_execution_write_and_stop_injection_reject(
        self,
    ) -> None:
        executable_identity = deepcopy(self.identity)
        executable_identity["execution_requested"] = True
        self.assertNotEqual(
            self.schema_errors(executable_identity),
            [],
        )

        authority_evidence = deepcopy(self.evidence)
        authority_evidence["evidence_slots"]["dependency"][
            "grants_execution_authority"
        ] = True
        self.assertNotEqual(
            self.schema_errors(authority_evidence),
            [],
        )

        write_manifest = deepcopy(self.manifest)
        write_manifest["path_b_write_authority"] = True
        self.assertNotEqual(self.schema_errors(write_manifest), [])

        stop_record = deepcopy(self.expected_record)
        stop_record["CERTIFIED_STOP"] = True
        self.assertNotEqual(self.schema_errors(stop_record), [])
        self.assertNotEqual(
            list(self.generic_record_validator.iter_errors(stop_record)),
            [],
        )

    def test_green_11_same_inputs_same_record_and_hash(self) -> None:
        left = self.evaluate()
        right = self.evaluate()
        self.assertEqual(left, right)
        self.assertEqual(left["record_id"], right["record_id"])
        self.assertEqual(left["hash"], right["hash"])

    def test_green_12_source_and_acceptance_pins_replay(self) -> None:
        source_tree = self.identity["identity_inputs"]["source_tree"]
        for artifact in source_tree["artifacts"]:
            with self.subTest(path=artifact["path"]):
                self.assertEqual(
                    file_sha256(ROOT / artifact["path"]),
                    artifact["content_sha256"],
                )
        for pin in source_tree["acceptance_pins"]:
            with self.subTest(path=pin["path"]):
                self.assertEqual(
                    file_sha256(ROOT / pin["path"]),
                    pin["content_sha256"],
                )

    def test_green_13_protected_and_red_pins_zero_drift(self) -> None:
        for relative, expected in {
            **PROTECTED_PINS,
            **ACCEPTED_RED_PINS,
        }.items():
            with self.subTest(path=relative):
                self.assertEqual(
                    file_sha256(ROOT / relative),
                    expected,
                )

    def test_green_14_manifest_ceiling_and_bindings(self) -> None:
        self.assertEqual(
            self.manifest["pb_b5_si_001_state"],
            "D1_CONFORMANCE_PATH_ESTABLISHED_EXECUTION_NOT_ESTABLISHED",
        )
        self.assertEqual(
            self.manifest["positive_decision"],
            "ADMITTED_CONFORMANCE_ONLY",
        )
        for field in (
            "planner_execution_authority",
            "evaluation_execution_authority",
            "sampling_authority",
            "production_capture_authority",
            "path_b_write_authority",
            "mint_authority",
            "path_b_admission_or_ingestion_authority",
            "kernel_or_e_case_write_authority",
            "holdout_release_authority",
            "performance_claim_authority",
            "scalarization_authority",
            "certificate_authority",
            "system_state_authority",
            "full_m3_star",
            "part_b_pass",
        ):
            self.assertIs(self.manifest[field], False)
        self.assertEqual(self.manifest["stop_authority"], "NONE")
        self.assertEqual(
            self.manifest["legacy_m3star_status"],
            "NOT_ADMITTED_UNVERIFIED",
        )
        self.assertEqual(
            self.manifest["legacy_m3star_decision"],
            "DENY_NOT_ADMITTED_UNVERIFIED",
        )
        self.assertEqual(
            self.manifest["bindings"]["implementation_identity_hash"],
            self.identity["hash"],
        )
        self.assertEqual(
            self.manifest["bindings"]["admission_evidence_hash"],
            self.evidence["hash"],
        )
        self.assertEqual(
            self.manifest["bindings"]["admission_policy_hash"],
            self.policy["hash"],
        )
        self.assertEqual(
            self.manifest["bindings"]["admission_record_hash"],
            self.expected_record["hash"],
        )

    def test_green_15_only_one_positive_decision_and_hard_ban(
        self,
    ) -> None:
        positive = [
            row["decision"]
            for row in self.policy["decision_table"]
            if not row["decision"].startswith("DENY_")
        ]
        self.assertEqual(positive, ["ADMITTED_CONFORMANCE_ONLY"])
        self.assertEqual(
            self.policy["admissible_implementation_ids"],
            [IMPLEMENTATION_ID],
        )
        self.assertFalse(self.policy["wildcards"])
        self.assertFalse(self.policy["fallback"])

        red_design = load_json(
            ROOT
            / "docs"
            / "kernel"
            / "part-b-b5-d1-conformance-admission-red-design-"
            "v0.1-20260728.json"
        )
        self.assertEqual(red_design["authority"]["hard_ban"], HARD_BAN)


if __name__ == "__main__":
    unittest.main()
