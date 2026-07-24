from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
CONFIG_DIR = ROOT / "configs"

SCHEMA_PATHS = {
    "policy": SCHEMA_DIR / "part-b-source-selection-policy.schema.json",
    "record": SCHEMA_DIR / "part-b-source-selection-record.schema.json",
    "manifest": SCHEMA_DIR / "part-b-si006-manifest.schema.json",
}
CONFIG_PATHS = {
    "policy": CONFIG_DIR / "part-b-source-selection-policy-v0.8.yaml",
    "record": CONFIG_DIR / "part-b-source-selection-example-v0.8.yaml",
    "manifest": CONFIG_DIR / "part-b-si006-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-si006-source-selection-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-si006-source-selection-v0.8.md",
    ROOT / "src" / "scope" / "part-b-si006-source-selection-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-si006-source-selection-implementation-plan-v0.8-20260724.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
    ROOT / "src" / "scope" / "part-b-b0-spec-issues.md",
)
RUNTIME_PATH = ROOT / "src" / "scope" / "part_b_si006_source_selection.py"

PRODUCT_PATHS = (
    *SCHEMA_PATHS.values(),
    *CONFIG_PATHS.values(),
    DOCUMENT_PATHS[0],
    DOCUMENT_PATHS[1],
    RUNTIME_PATH,
    DOCUMENT_PATHS[2],
    DOCUMENT_PATHS[3],
    DOCUMENT_PATHS[4],
    DOCUMENT_PATHS[5],
)

FROZEN_BINDINGS = {
    "b1_adapter_conformance_hash": (
        "configs/part-b-adapter-conformance-v0.8.yaml",
        "sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a",
    ),
    "b7_connector_policy_hash": (
        "configs/part-b-connector-contract-policy-v0.8.yaml",
        "sha256:43c6270078e03ac1764d16c41871a97a09df3a626c060ceebdecc06682b064c3",
    ),
    "b7_manifest_hash": (
        "configs/part-b-b7-manifest-v0.8.yaml",
        "sha256:28179580dc0e8c4dbc6f1a6cb1d5f0d4939a3ae7466c078e60f20fb16fffac49",
    ),
}


def require_product(test: unittest.TestCase, path: Path) -> Path:
    if not path.is_file():
        test.fail(
            "missing approved SI-006 source-selection artifact: "
            f"{path.relative_to(ROOT).as_posix()}"
        )
    return path


def load_json(test: unittest.TestCase, path: Path) -> dict[str, object]:
    return json.loads(require_product(test, path).read_text(encoding="utf-8"))


def load_yaml(test: unittest.TestCase, path: Path) -> dict[str, object]:
    return yaml.safe_load(
        require_product(test, path).read_text(encoding="utf-8")
    )


def validation_errors(
    instance: dict[str, object], schema: dict[str, object]
) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


class PartBSI006SourceSelectionContractTests(unittest.TestCase):
    def test_red_01_exact_source_selection_product_set_is_required(
        self,
    ) -> None:
        """RED-01: GREEN requires exactly the approved contract products."""
        for path in PRODUCT_PATHS:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                require_product(self, path)

    def test_red_02_schemas_are_closed_and_examples_validate(self) -> None:
        """RED-02: selection contracts are closed draft-2020-12 schemas."""
        schemas = {
            name: load_json(self, path) for name, path in SCHEMA_PATHS.items()
        }
        for name, schema in schemas.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)
                self.assertEqual(
                    schema.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertIs(schema.get("additionalProperties"), False)

        for name, path in CONFIG_PATHS.items():
            with self.subTest(config=name):
                document = load_yaml(self, path)
                self.assertEqual(validation_errors(document, schemas[name]), [])
                widened = deepcopy(document)
                widened["undeclared_retrieval_authority"] = True
                self.assertNotEqual(
                    validation_errors(widened, schemas[name]), []
                )

    def test_red_03_hashes_replay_and_bind_frozen_b1_b7(self) -> None:
        """RED-03: selection identities bind, but never rewrite, B1/B7."""
        documents = {
            name: load_yaml(self, path) for name, path in CONFIG_PATHS.items()
        }
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertEqual(
                    document.get("hash"),
                    canonical_document_hash(document),
                )

        manifest = documents["manifest"]
        policy = documents["policy"]
        record = documents["record"]
        for binding_name, (path, expected_hash) in FROZEN_BINDINGS.items():
            with self.subTest(binding=binding_name):
                upstream = yaml.safe_load(
                    (ROOT / path).read_text(encoding="utf-8")
                )
                self.assertEqual(upstream["hash"], expected_hash)
                self.assertEqual(
                    canonical_document_hash(upstream), expected_hash
                )
                self.assertEqual(
                    manifest["bindings"][binding_name], expected_hash
                )
                self.assertEqual(policy["bindings"][binding_name], expected_hash)
        self.assertEqual(
            manifest["artifacts"]["selection_policy_hash"], policy["hash"]
        )
        self.assertEqual(
            manifest["artifacts"]["selection_example_hash"], record["hash"]
        )

    def test_red_04_record_separates_pointer_modality_role_and_authority(
        self,
    ) -> None:
        """RED-04: provenance and epistemic dimensions stay independent."""
        record = load_yaml(self, CONFIG_PATHS["record"])
        pointer = record["source_pointer"]
        self.assertTrue(pointer["source_id"])
        self.assertTrue(pointer["record_id"])
        self.assertRegex(pointer["content_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertIn(pointer["range"]["kind"], {"ROWS", "BYTES"})
        self.assertLess(pointer["range"]["start"], pointer["range"]["end"])
        self.assertEqual(pointer["range"]["end_semantics"], "EXCLUSIVE")
        self.assertEqual(
            pointer["range_semantics"],
            f"{pointer['range']['kind']}_HALF_OPEN",
        )
        self.assertIn("modality", record)
        self.assertIn("truth_status", record)
        self.assertIn("epistemic_role", record)
        self.assertIn("certification_authority", record)
        self.assertIs(record["certification_authority"]["allowed"], False)
        self.assertEqual(record["certification_authority"]["levels"], [])
        self.assertIsNone(
            record["certification_authority"]["basis_rule_id"]
        )

    def test_red_05_example_source_is_abstract_and_not_authorized(self) -> None:
        """RED-05: a fixture identifier cannot imply a real-source grant."""
        record = load_yaml(self, CONFIG_PATHS["record"])
        source_id = record["source_pointer"]["source_id"]
        self.assertTrue(source_id.startswith("abstract-"))
        self.assertEqual(
            record["source_status"],
            "ABSTRACT_CONTRACT_FIXTURE_NOT_AUTHORIZED",
        )
        self.assertEqual(record["selection_decision"], "SELECTED_CONTRACT_ONLY")
        self.assertEqual(record["source_authorization"], "NOT_AUTHORIZED")
        corpus = json.dumps(record, sort_keys=True).lower()
        for forbidden in (
            "http://",
            "https://",
            "api_key",
            "access_token",
            "credential",
            "holdout_label",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, corpus)

    def test_red_06_selection_is_not_retrieval_download_or_execution(
        self,
    ) -> None:
        """RED-06: selecting an abstract record grants no data-plane power."""
        manifest = load_yaml(self, CONFIG_PATHS["manifest"])
        policy = load_yaml(self, CONFIG_PATHS["policy"])
        self.assertEqual(
            manifest["status"], "SI006_SOURCE_SELECTION_CONTRACT_ONLY"
        )
        self.assertTrue(manifest["source_selection_contract_authority"])
        self.assertTrue(manifest["local_selection_evaluation_authority"])
        for field in (
            "source_authorization_authority",
            "retrieval_authority",
            "download_authority",
            "credential_use_authority",
            "connector_execution_authority",
            "planner_execution_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(manifest[field], False)
        self.assertEqual(manifest["holdout_release"], "DENY")
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(
            policy["selection_boundary"]["selection_semantics"],
            "CONTRACT_RECORD_ONLY_NOT_SOURCE_AUTHORIZATION",
        )

    def test_red_07_world_and_adapter_conformance_are_explicit(self) -> None:
        """RED-07: world semantics and adapter conformance cannot be guessed."""
        record = load_yaml(self, CONFIG_PATHS["record"])
        world = record["world_semantics"]
        self.assertIn(world["mode"], {"OPEN_WORLD", "CLOSED_BOUNDED"})
        if world["mode"] == "OPEN_WORLD":
            self.assertEqual(
                world["zero_hit_semantics"], "UNKNOWN_NOT_ABSENCE"
            )
            self.assertIsNone(world["completeness_attestation"])
        else:
            self.assertEqual(
                world["zero_hit_semantics"],
                "ABSENCE_ONLY_WITH_COMPLETE_ATTESTATION",
            )
            self.assertIsNotNone(world["completeness_attestation"])

        conformance = record["adapter_conformance"]
        self.assertEqual(
            conformance["contract_id"], "part-b-adapter-conformance-v0.8"
        )
        self.assertEqual(
            conformance["contract_hash"],
            FROZEN_BINDINGS["b1_adapter_conformance_hash"][1],
        )
        self.assertEqual(conformance["decision"], "CONFORMANT")
        self.assertFalse(conformance["pointer_ownership_transferred"])

    def test_red_08_si_and_adjacent_gates_remain_narrowly_closed(self) -> None:
        """RED-08: PB-SI-006 closes only the local selection-contract subset."""
        manifest = load_yaml(self, CONFIG_PATHS["manifest"])
        self.assertEqual(
            manifest["pb_si_006_state"],
            "SELECTION_CONTRACT_ONLY_DOWNLOAD_DENY",
        )
        self.assertEqual(manifest["pb_b7_si_001_state"], "OPEN_DEFAULT_DENY")
        self.assertEqual(manifest["pb_b7_si_002_state"], "OPEN_DEFAULT_DENY")
        self.assertEqual(
            manifest["pb_b5_si_001_state"],
            "EXECUTION_NOT_ESTABLISHED",
        )
        self.assertEqual(manifest["holdout_release"], "DENY")
        self.assertEqual(manifest["stop_authority"], "NONE")

        corpus = "\n".join(
            require_product(self, path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        )
        for token in (
            "PB-SI-006",
            "SELECTION_CONTRACT_ONLY_DOWNLOAD_DENY",
            "PB-B7-SI-001",
            "PB-B7-SI-002",
            "OPEN",
            "download_authority=false",
            "retrieval_authority=false",
            "connector_execution_authority=false",
            "holdout",
            "DENY",
            "CERTIFIED_STOP",
            "NONE",
        ):
            with self.subTest(token=token):
                self.assertIn(token, corpus)


if __name__ == "__main__":
    unittest.main()
