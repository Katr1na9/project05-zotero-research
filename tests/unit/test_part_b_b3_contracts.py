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
    "policy": SCHEMA_DIR / "part-b-cost-instrumentation-policy.schema.json",
    "manifest": SCHEMA_DIR / "part-b-b3-manifest.schema.json",
    "trace": SCHEMA_DIR / "part-b-cost-trace.schema.json",
}
CONFIG_PATHS = {
    "policy": CONFIG_DIR / "part-b-cost-instrumentation-policy-v0.8.yaml",
    "manifest": CONFIG_DIR / "part-b-b3-manifest-v0.8.yaml",
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


class PartBB3ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {name: load_json(path) for name, path in SCHEMA_PATHS.items()}
        cls.configs = {name: load_yaml(path) for name, path in CONFIG_PATHS.items()}

    def test_schemas_are_valid_and_configs_replay_hashes(self) -> None:
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)

        for name, config in self.configs.items():
            with self.subTest(config=name):
                self.assertEqual(validate(config, self.schemas[name]), [])
                self.assertEqual(config["hash"], canonical_document_hash(config))

    def test_manifest_binds_frozen_b0_cost_contract_and_b3_policy(self) -> None:
        manifest = self.configs["manifest"]
        b0_cost = load_yaml(CONFIG_DIR / "part-b-cost-contract-v0.8.yaml")
        b2_manifest = load_yaml(CONFIG_DIR / "part-b-b2-manifest-v0.8.yaml")
        self.assertEqual(
            b0_cost["hash"],
            "sha256:b6d36c40f7b52c12733dbe75cbcba6058e952f23d67e2155bd73196f6bcfaf53",
        )
        self.assertEqual(
            manifest["bindings"]["b0_cost_contract_hash"],
            b0_cost["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["b2_manifest_hash"],
            b2_manifest["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["cost_instrumentation_policy_hash"],
            self.configs["policy"]["hash"],
        )

    def test_authority_is_instrumentation_only(self) -> None:
        manifest = self.configs["manifest"]
        self.assertEqual(manifest["authorized_slice"], "B3_COST_INSTRUMENTATION")
        self.assertTrue(manifest["instrumentation_authority"])
        self.assertFalse(manifest["action_execution_authority"])
        self.assertFalse(manifest["sampling_authority"])
        self.assertFalse(manifest["scalarization_authority"])
        self.assertFalse(manifest["performance_claim_authority"])
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(
            manifest["closed_slices"],
            ["B4", "B5", "B6", "B7", "B8", "B9"],
        )

    def test_policy_freezes_eight_dimensions_and_missingness(self) -> None:
        policy = self.configs["policy"]
        self.assertEqual(
            [row["dimension_id"] for row in policy["dimensions"]],
            [
                "T_human",
                "T_wall",
                "T_CPU",
                "M_byte_sec",
                "D_scan",
                "N_record",
                "C_money",
                "T_auth",
            ],
        )
        self.assertEqual(
            policy["missingness"]["missing_measurement"],
            "UNKNOWN_NOT_ZERO",
        )
        self.assertEqual(
            policy["feasibility"]["semantics"],
            "SEPARATE_NOT_HIGH_COST",
        )
        self.assertEqual(
            policy["currency"]["mixed_currency_behavior"],
            "FAIL_CLOSED_NO_IMPLICIT_FX",
        )
        self.assertEqual(policy["scalarization"]["enabled"], False)

    def test_schemas_reject_authority_expansion(self) -> None:
        manifest = self.configs["manifest"]
        for field in (
            "action_execution_authority",
            "sampling_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            invalid = deepcopy(manifest)
            invalid[field] = True
            with self.subTest(field=field):
                self.assertTrue(validate(invalid, self.schemas["manifest"]))

        invalid = deepcopy(manifest)
        invalid["stop_authority"] = "B3"
        self.assertTrue(validate(invalid, self.schemas["manifest"]))

    def test_docs_keep_claim_and_sampling_boundaries_closed(self) -> None:
        paths = (
            ROOT / "contracts" / "part-b-b3-boundary-v0.8.md",
            ROOT / "contracts" / "part-b-b3-cost-instrumentation-v0.8.md",
            ROOT / "src" / "scope" / "part-b-b0-spec-issues.md",
            ROOT / "src" / "scope" / "part-b-b3-spec-issues.md",
            ROOT
            / "08-writing"
            / "part-b-b3-implementation-plan-v0.8-20260723.md",
            ROOT
            / "08-writing"
            / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
        )
        required = (
            "B3_COST_INSTRUMENTATION",
            "UNKNOWN_NOT_ZERO",
            "SEPARATE_NOT_HIGH_COST",
            "sampling_authority=false",
            "performance_claim_authority=false",
            "scalarization_authority=false",
            "CERTIFIED_STOP",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in required:
                with self.subTest(path=path.name, token=token):
                    self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
