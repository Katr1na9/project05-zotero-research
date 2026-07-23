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
    "federation": SCHEMA_DIR / "part-b-federation-contract.schema.json",
    "conformance": SCHEMA_DIR / "part-b-adapter-conformance.schema.json",
    "manifest": SCHEMA_DIR / "part-b-b1-manifest.schema.json",
}
CONFIG_PATHS = {
    "federation": CONFIG_DIR / "part-b-federation-contract-v0.8.yaml",
    "conformance": CONFIG_DIR / "part-b-adapter-conformance-v0.8.yaml",
    "manifest": CONFIG_DIR / "part-b-b1-manifest-v0.8.yaml",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(instance: dict[str, object], schema: dict[str, object]) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


def walk_values(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)


class PartBB1ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {name: load_json(path) for name, path in SCHEMA_PATHS.items()}
        cls.configs = {name: load_yaml(path) for name, path in CONFIG_PATHS.items()}

    def test_b1_schemas_are_valid_draft_2020_12(self) -> None:
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                self.assertEqual(
                    schema["$schema"],
                    "https://json-schema.org/draft/2020-12/schema",
                )
                Draft202012Validator.check_schema(schema)

    def test_non_executable_artifacts_validate_and_hash_replay(self) -> None:
        for name, artifact in self.configs.items():
            with self.subTest(artifact=name):
                self.assertEqual(validate(artifact, self.schemas[name]), [])
                self.assertEqual(artifact["hash"], canonical_document_hash(artifact))

        manifest = self.configs["manifest"]
        b0_manifest = load_yaml(CONFIG_DIR / "part-b-b0-manifest-v0.8.yaml")
        self.assertEqual(
            manifest["bindings"]["federation_contract_hash"],
            self.configs["federation"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["adapter_conformance_hash"],
            self.configs["conformance"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["b0_manifest_hash"],
            b0_manifest["hash"],
        )

    def test_manifest_locks_b1_to_contract_only_authority(self) -> None:
        manifest = self.configs["manifest"]
        self.assertEqual(manifest["status"], "B1_CONTRACT_ONLY")
        self.assertEqual(manifest["authorized_slice"], "B1_FEDERATION_SCHEMAS")
        self.assertFalse(manifest["execution_authority"])
        self.assertEqual(manifest["llm_integration"], "FORBIDDEN")
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(
            manifest["closed_slices"],
            ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
        )
        self.assertTrue(
            all(value is False for value in manifest["runtime_authority"].values())
        )

    def test_schemas_fail_closed_on_authority_or_runtime_expansion(self) -> None:
        manifest = self.configs["manifest"]
        manifest_schema = self.schemas["manifest"]
        mutations = (
            ("execution_authority", True),
            ("llm_integration", "ALLOWED"),
            ("stop_authority", "ADAPTER"),
            ("authorized_slice", "B1_FEDERATION_RUNTIME"),
        )
        for field, value in mutations:
            invalid = deepcopy(manifest)
            invalid[field] = value
            with self.subTest(manifest_field=field):
                self.assertTrue(validate(invalid, manifest_schema))

        for field in self.configs["manifest"]["runtime_authority"]:
            invalid = deepcopy(manifest)
            invalid["runtime_authority"][field] = True
            with self.subTest(runtime_authority=field):
                self.assertTrue(validate(invalid, manifest_schema))

        invalid_federation = deepcopy(self.configs["federation"])
        invalid_federation["runtime_endpoint"] = "local-runtime"
        self.assertTrue(validate(invalid_federation, self.schemas["federation"]))

        invalid_conformance = deepcopy(self.configs["conformance"])
        invalid_conformance["connector_endpoint"] = "local-connector"
        self.assertTrue(validate(invalid_conformance, self.schemas["conformance"]))

    def test_semantic_family_domain_is_finite_versioned_and_unique(self) -> None:
        federation = self.configs["federation"]
        self.assertEqual(federation["domain_kind"], "FINITE_REGISTERED_FAMILIES")
        families = federation["semantic_families"]
        self.assertGreaterEqual(len(families), 2)
        self.assertLessEqual(len(families), 9)

        family_ids = [family["family_id"] for family in families]
        self.assertEqual(len(family_ids), len(set(family_ids)))
        for family in families:
            self.assertRegex(family["family_version"], r"^\d+\.\d+\.\d+$")
            self.assertTrue(family["source_schema_ids"])
            self.assertEqual(
                len(family["source_schema_ids"]),
                len(set(family["source_schema_ids"])),
            )

    def test_examples_contain_no_execution_or_retrieval_material(self) -> None:
        forbidden_keys = {
            "credential",
            "credentials",
            "secret",
            "token",
            "password",
            "download",
            "download_command",
            "endpoint",
            "runtime_endpoint",
            "connector_endpoint",
            "oracle",
            "hidden_ground_truth",
            "random_seed",
            "sampling_command",
        }
        forbidden_text = ("http://", "https://", "curl ", "wget ")

        for artifact_name, artifact in self.configs.items():
            for key, value in walk_values(artifact):
                with self.subTest(artifact=artifact_name, key=key):
                    self.assertNotIn(key.lower(), forbidden_keys)
                if isinstance(value, str):
                    lowered = value.lower()
                    self.assertFalse(
                        any(token in lowered for token in forbidden_text),
                        f"{artifact_name} contains retrieval material: {value}",
                    )

    def test_authority_plan_and_boundary_text_keep_b1_narrow(self) -> None:
        paths = (
            ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
            ROOT / "08-writing" / "part-b-b1-implementation-plan-v0.8-20260723.md",
            ROOT / "contracts" / "part-b-b1-boundary-v0.8.md",
            ROOT / "contracts" / "part-b-b1-adapter-conformance-v0.8.md",
            ROOT / "src" / "scope" / "part-b-b1-spec-issues.md",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("B1_FEDERATION_SCHEMAS", text)
                self.assertIn("B2–B9", text)
                self.assertIn("LLM", text)
                self.assertIn("CERTIFIED_STOP", text)


if __name__ == "__main__":
    unittest.main()
