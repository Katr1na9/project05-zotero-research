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
    "catalog": SCHEMA_DIR / "part-b-stochastic-observation-catalog.schema.json",
    "tv_policy": SCHEMA_DIR / "part-b-stochastic-tv-policy.schema.json",
    "manifest": SCHEMA_DIR / "part-b-b2-manifest.schema.json",
}
CONFIG_PATHS = {
    "catalog": CONFIG_DIR / "part-b-stochastic-observation-catalog-v0.8.yaml",
    "tv_policy": CONFIG_DIR / "part-b-stochastic-tv-policy-v0.8.yaml",
    "manifest": CONFIG_DIR / "part-b-b2-manifest-v0.8.yaml",
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


class PartBB2ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {name: load_json(path) for name, path in SCHEMA_PATHS.items()}
        cls.configs = {name: load_yaml(path) for name, path in CONFIG_PATHS.items()}

    def test_b2_schemas_are_valid_draft_2020_12(self) -> None:
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                self.assertEqual(
                    schema["$schema"],
                    "https://json-schema.org/draft/2020-12/schema",
                )
                Draft202012Validator.check_schema(schema)

    def test_contract_only_artifacts_validate_and_hash_replay(self) -> None:
        for name, artifact in self.configs.items():
            with self.subTest(artifact=name):
                self.assertEqual(validate(artifact, self.schemas[name]), [])
                self.assertEqual(artifact["hash"], canonical_document_hash(artifact))

        manifest = self.configs["manifest"]
        b0_manifest = load_yaml(CONFIG_DIR / "part-b-b0-manifest-v0.8.yaml")
        b1_manifest = load_yaml(CONFIG_DIR / "part-b-b1-manifest-v0.8.yaml")
        self.assertEqual(
            manifest["bindings"]["b0_manifest_hash"],
            b0_manifest["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["b1_manifest_hash"],
            b1_manifest["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["stochastic_catalog_hash"],
            self.configs["catalog"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["tv_policy_hash"],
            self.configs["tv_policy"]["hash"],
        )

    def test_manifest_locks_execution_and_sampling_authority_false(self) -> None:
        manifest = self.configs["manifest"]
        self.assertEqual(manifest["status"], "B2_CONTRACT_ONLY")
        self.assertEqual(
            manifest["authorized_slice"],
            "B2_STOCHASTIC_OBSERVATION",
        )
        self.assertFalse(manifest["execution_authority"])
        self.assertFalse(manifest["sampling_authority"])
        self.assertEqual(
            manifest["pb_si_003_state"],
            "OPEN_BLOCKS_STOCHASTIC_EXECUTION",
        )
        self.assertEqual(manifest["llm_integration"], "FORBIDDEN")
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(
            manifest["closed_slices"],
            ["B3", "B4", "B5", "B6", "B7", "B8", "B9"],
        )
        self.assertTrue(
            all(value is False for value in manifest["runtime_authority"].values())
        )

    def test_schemas_fail_closed_on_authority_expansion(self) -> None:
        manifest = self.configs["manifest"]
        manifest_schema = self.schemas["manifest"]
        mutations = (
            ("execution_authority", True),
            ("sampling_authority", True),
            ("pb_si_003_state", "CLOSED"),
            ("llm_integration", "ALLOWED"),
            ("stop_authority", "STOCHASTIC_MODEL"),
            ("authorized_slice", "B2_STOCHASTIC_RUNTIME"),
        )
        for field, value in mutations:
            invalid = deepcopy(manifest)
            invalid[field] = value
            with self.subTest(manifest_field=field):
                self.assertTrue(validate(invalid, manifest_schema))

        for field in manifest["runtime_authority"]:
            invalid = deepcopy(manifest)
            invalid["runtime_authority"][field] = True
            with self.subTest(runtime_authority=field):
                self.assertTrue(validate(invalid, manifest_schema))

        invalid_catalog = deepcopy(self.configs["catalog"])
        invalid_catalog["sampling_authority"] = True
        self.assertTrue(validate(invalid_catalog, self.schemas["catalog"]))

        invalid_policy = deepcopy(self.configs["tv_policy"])
        invalid_policy["execution_authority"] = True
        self.assertTrue(validate(invalid_policy, self.schemas["tv_policy"]))

    def test_examples_contain_no_runtime_sampling_or_retrieval_material(self) -> None:
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
            "sample_count",
            "system_status",
            "level_certificate",
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
                        f"{artifact_name} contains runtime material: {value}",
                    )
                    self.assertNotEqual(value, "CERTIFIED_STOP")

    def test_frozen_b0_and_b1_artifact_hashes_remain_unchanged(self) -> None:
        b0_observation = load_yaml(
            CONFIG_DIR / "part-b-observation-contract-v0.8.yaml"
        )
        b1_manifest = load_yaml(CONFIG_DIR / "part-b-b1-manifest-v0.8.yaml")
        self.assertEqual(
            b0_observation["hash"],
            "sha256:f5db6035452236fb6e316b8e9a5ada7e2a7cbce07c0eedc3b3e7c890bc4fd7d9",
        )
        self.assertEqual(
            b1_manifest["hash"],
            "sha256:cecc07466d0aec0dbc7b4d95127651546ba7eb895f98a56d7e37c6f753850f6e",
        )

    def test_authority_plan_and_contract_text_keep_b2_narrow(self) -> None:
        paths = (
            ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
            ROOT / "08-writing" / "part-b-b2-implementation-plan-v0.8-20260723.md",
            ROOT / "contracts" / "part-b-b2-boundary-v0.8.md",
            ROOT / "contracts" / "part-b-b2-stochastic-observation-v0.8.md",
            ROOT / "src" / "scope" / "part-b-b2-spec-issues.md",
        )
        required = (
            "B2_STOCHASTIC_OBSERVATION",
            "execution_authority=false",
            "sampling_authority=false",
            "PB-SI-003",
            "OPEN",
            "LLM",
            "CERTIFIED_STOP",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in required:
                with self.subTest(path=path.name, token=token):
                    self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
