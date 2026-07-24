from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATHS = {
    "identity": (
        ROOT
        / "schemas"
        / "part-b-b5-planner-implementation-identity.schema.json"
    ),
    "evidence": (
        ROOT / "schemas" / "part-b-b5-planner-admission-evidence.schema.json"
    ),
    "record": (
        ROOT / "schemas" / "part-b-b5-planner-admission-record.schema.json"
    ),
    "policy": (
        ROOT / "schemas" / "part-b-b5-planner-admission-policy.schema.json"
    ),
    "manifest": (
        ROOT / "schemas" / "part-b-b5-planner-admission-manifest.schema.json"
    ),
}
CONFIG_PATHS = {
    "identity": (
        ROOT
        / "configs"
        / "part-b-b5-planner-implementation-identity-example-v0.8.yaml"
    ),
    "evidence": (
        ROOT
        / "configs"
        / "part-b-b5-planner-admission-evidence-example-v0.8.yaml"
    ),
    "record": (
        ROOT
        / "configs"
        / "part-b-b5-planner-admission-record-example-v0.8.yaml"
    ),
    "policy": (
        ROOT / "configs" / "part-b-b5-planner-admission-policy-v0.8.yaml"
    ),
    "manifest": (
        ROOT / "configs" / "part-b-b5-planner-admission-manifest-v0.8.yaml"
    ),
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b5-planner-admission-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-b5-planner-admission-evidence-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b5-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b5-planner-admission-implementation-plan-v0.8-20260724.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)
RUNTIME_PATH = (
    ROOT / "src" / "scope" / "part_b_b5_planner_admission.py"
)

PRODUCT_PATHS = (
    *SCHEMA_PATHS.values(),
    *CONFIG_PATHS.values(),
    DOCUMENT_PATHS[0],
    DOCUMENT_PATHS[1],
    DOCUMENT_PATHS[3],
    RUNTIME_PATH,
)

B5_INTERFACE_POLICY_PATH = (
    ROOT / "configs" / "part-b-planner-interface-policy-v0.8.yaml"
)
B5_MANIFEST_PATH = ROOT / "configs" / "part-b-b5-manifest-v0.8.yaml"
B5_INTERFACE_POLICY_HASH = (
    "sha256:b0c9f9971d13efcfeabb39f829592b9502831ba1b94e8de54e3941ba7dd1c343"
)
B5_MANIFEST_HASH = (
    "sha256:bbe8bde7e6ab4695fc6a03233a8c45f5d205c77b3bed6f2816a89c8f7616c069"
)

LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"
REQUIRED_EVIDENCE_SLOTS = {
    "dependency",
    "parameter",
    "feature_provenance",
    "runtime_conformance",
}
FORBIDDEN_AUTHORITIES = (
    "planner_execution_authority",
    "evaluation_execution_authority",
    "sampling_authority",
    "production_capture_authority",
    "scalarization_authority",
    "performance_claim_authority",
    "superiority_claim_authority",
    "holdout_release_authority",
    "certificate_authority",
)


def require_product(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            "missing approved B5 planner-admission artifact: "
            f"{path.relative_to(ROOT)}"
        )
    return path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(require_product(path).read_text(encoding="utf-8"))


def load_yaml(
    path: Path,
    *,
    product: bool = True,
) -> dict[str, object]:
    if product:
        path = require_product(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(
    instance: dict[str, object],
    schema: dict[str, object],
) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


class PartBB5PlannerAdmissionContractTests(unittest.TestCase):
    def test_red_01_exact_admission_skeleton_product_set_is_required(
        self,
    ) -> None:
        """RED-01: GREEN requires the approved admission skeleton product."""
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_PATHS
            if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved B5 planner-admission artifacts: "
            + ", ".join(missing),
        )

    def test_red_02_schemas_are_closed_and_examples_validate(self) -> None:
        """RED-02: every admission artifact is a closed 2020-12 contract."""
        schemas = {
            name: load_json(path) for name, path in SCHEMA_PATHS.items()
        }
        configs = {
            name: load_yaml(path) for name, path in CONFIG_PATHS.items()
        }

        for name, schema in schemas.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)
                self.assertEqual(
                    schema.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertIs(schema.get("additionalProperties"), False)
                self.assertEqual(validate(configs[name], schema), [])

                widened = deepcopy(configs[name])
                widened["undeclared_execution_authority"] = True
                self.assertTrue(validate(widened, schema))

    def test_red_03_hashes_replay_and_bind_frozen_b5_contracts(self) -> None:
        """RED-03: new evidence binds B5 without rewriting frozen hashes."""
        configs = {
            name: load_yaml(path) for name, path in CONFIG_PATHS.items()
        }
        for name, document in configs.items():
            with self.subTest(document=name):
                self.assertEqual(
                    document["hash"],
                    canonical_document_hash(document),
                )

        frozen_policy = load_yaml(
            B5_INTERFACE_POLICY_PATH,
            product=False,
        )
        frozen_manifest = load_yaml(B5_MANIFEST_PATH, product=False)
        self.assertEqual(frozen_policy["hash"], B5_INTERFACE_POLICY_HASH)
        self.assertEqual(frozen_manifest["hash"], B5_MANIFEST_HASH)

        bindings = configs["manifest"]["bindings"]
        self.assertEqual(
            bindings["b5_planner_interface_policy_hash"],
            B5_INTERFACE_POLICY_HASH,
        )
        self.assertEqual(
            bindings["b5_manifest_hash"],
            B5_MANIFEST_HASH,
        )
        self.assertEqual(
            bindings["implementation_identity_hash"],
            configs["identity"]["hash"],
        )
        self.assertEqual(
            bindings["admission_evidence_hash"],
            configs["evidence"]["hash"],
        )
        self.assertEqual(
            bindings["admission_policy_hash"],
            configs["policy"]["hash"],
        )
        self.assertEqual(
            bindings["admission_record_hash"],
            configs["record"]["hash"],
        )

    def test_red_04_identity_is_explicit_and_legacy_is_rejected(self) -> None:
        """RED-04: identity is hash-bound; legacy M3star stays unverified."""
        identity = load_yaml(CONFIG_PATHS["identity"])
        policy = load_yaml(CONFIG_PATHS["policy"])

        self.assertEqual(
            identity["implementation_kind"],
            "ADMISSION_SKELETON_NONEXECUTING",
        )
        self.assertFalse(identity["execution_requested"])
        self.assertNotEqual(
            identity["implementation_id"],
            LEGACY_IMPLEMENTATION_ID,
        )
        for field in (
            "source_tree_hash",
            "dependency_lock_hash",
            "parameter_manifest_hash",
            "feature_provenance_hash",
            "runtime_conformance_hash",
        ):
            with self.subTest(identity_hash=field):
                self.assertRegex(
                    identity["identity_hashes"][field],
                    r"^sha256:[0-9a-f]{64}$",
                )

        self.assertEqual(
            policy["legacy_rejections"][LEGACY_IMPLEMENTATION_ID],
            "NOT_ADMITTED_UNVERIFIED",
        )
        self.assertNotIn(
            LEGACY_IMPLEMENTATION_ID,
            policy["admissible_implementation_ids"],
        )

    def test_red_05_all_admission_evidence_slots_are_explicit(self) -> None:
        """RED-05: dependencies, parameters, features and runtime all bind."""
        identity = load_yaml(CONFIG_PATHS["identity"])
        evidence = load_yaml(CONFIG_PATHS["evidence"])

        self.assertEqual(
            evidence["implementation_id"],
            identity["implementation_id"],
        )
        self.assertEqual(
            evidence["implementation_identity_hash"],
            identity["hash"],
        )
        self.assertEqual(set(evidence["evidence_slots"]), REQUIRED_EVIDENCE_SLOTS)
        for slot_name, slot in evidence["evidence_slots"].items():
            with self.subTest(slot=slot_name):
                self.assertEqual(slot["status"], "VERIFIED")
                self.assertRegex(
                    slot["artifact_hash"],
                    r"^sha256:[0-9a-f]{64}$",
                )
                self.assertFalse(slot["grants_execution_authority"])

    def test_red_06_admit_deny_table_is_complete_and_fail_closed(self) -> None:
        """RED-06: every incomplete, stale or unknown identity is denied."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        rows = {
            row["condition"]: row["decision"]
            for row in policy["decision_table"]
        }
        self.assertEqual(
            rows,
            {
                "IDENTITY_AND_ALL_EVIDENCE_VERIFIED": (
                    "ADMITTED_CONFORMANCE_ONLY"
                ),
                "LEGACY_UNVERIFIED_ID": "DENY_NOT_ADMITTED_UNVERIFIED",
                "UNKNOWN_IMPLEMENTATION_ID": "DENY_UNKNOWN_IMPLEMENTATION",
                "EVIDENCE_INCOMPLETE": "DENY_EVIDENCE_INCOMPLETE",
                "EVIDENCE_HASH_MISMATCH": "DENY_EVIDENCE_HASH_MISMATCH",
                "RUNTIME_CONFORMANCE_FAILED": (
                    "DENY_RUNTIME_CONFORMANCE_FAILED"
                ),
            },
        )
        self.assertEqual(
            policy["unknown_implementation_behavior"],
            "FAIL_CLOSED_DENY_UNKNOWN_IMPLEMENTATION",
        )
        self.assertEqual(
            policy["admission_scope"],
            "INTERFACE_CONFORMANCE_ONLY",
        )

    def test_red_07_manifest_keeps_execution_and_claim_gates_closed(
        self,
    ) -> None:
        """RED-07: an admission record grants no execution or claim power."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(
            manifest["status"],
            "B5_ADMISSION_SKELETON_LOCAL_ONLY",
        )
        self.assertEqual(
            manifest["pb_b5_si_001_state"],
            "SKELETON_EVIDENCE_PATH_ESTABLISHED_EXECUTION_NOT_ESTABLISHED",
        )
        self.assertEqual(
            manifest["pb_b5_si_002_state"],
            "OPEN_BLOCKS_EVALUATION_EXECUTION",
        )
        self.assertEqual(
            manifest["pb_b5_si_003_state"],
            "OPEN_BLOCKS_PERFORMANCE_AND_SCALARIZATION",
        )
        self.assertEqual(manifest["pb_si_006_state"], "OPEN_DEFAULT_DENY")
        self.assertEqual(manifest["holdout_release"], "DENY")
        self.assertEqual(manifest["stop_authority"], "NONE")
        for field in FORBIDDEN_AUTHORITIES:
            with self.subTest(authority=field):
                self.assertIs(manifest[field], False)

    def test_red_08_documents_distinguish_admission_from_execution(self) -> None:
        """RED-08: issue progress cannot be narrated as Planner execution."""
        corpus = "\n".join(
            require_product(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        )
        for token in (
            "PB-B5-SI-001",
            "SKELETON_EVIDENCE_PATH_ESTABLISHED",
            "execution authority: NOT ESTABLISHED",
            "project05_m3star_h3_dual",
            "NOT_ADMITTED_UNVERIFIED",
            "PB-B5-SI-002",
            "PB-B5-SI-003",
            "PB-SI-006",
            "holdout release: DENY",
            "CERTIFIED_STOP",
            "CONTRACT_CONSISTENCY_ONLY",
            "NO_PERFORMANCE_OR_SUPERIORITY_CLAIM",
        ):
            with self.subTest(token=token):
                self.assertIn(token, corpus)


if __name__ == "__main__":
    unittest.main()
