from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
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
    "observation": SCHEMA_DIR / "part-b-observation-contract.schema.json",
    "cost": SCHEMA_DIR / "part-b-cost-contract.schema.json",
    "manifest": SCHEMA_DIR / "part-b-b0-manifest.schema.json",
}
CONFIG_PATHS = {
    "observation": CONFIG_DIR / "part-b-observation-contract-v0.8.yaml",
    "cost": CONFIG_DIR / "part-b-cost-contract-v0.8.yaml",
    "manifest": CONFIG_DIR / "part-b-b0-manifest-v0.8.yaml",
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


class PartBB0ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {name: load_json(path) for name, path in SCHEMA_PATHS.items()}
        cls.configs = {name: load_yaml(path) for name, path in CONFIG_PATHS.items()}

    def test_b0_schemas_are_valid_draft_2020_12(self) -> None:
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)

    def test_contract_artifacts_validate_and_hash_replay(self) -> None:
        for name, artifact in self.configs.items():
            with self.subTest(artifact=name):
                self.assertEqual(validate(artifact, self.schemas[name]), [])
                self.assertEqual(artifact["hash"], canonical_document_hash(artifact))

        manifest = self.configs["manifest"]
        self.assertEqual(
            manifest["bindings"]["observation_contract_hash"],
            self.configs["observation"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["cost_contract_hash"],
            self.configs["cost"]["hash"],
        )

        gamma = load_yaml(CONFIG_DIR / "gamma-kernel-v0.8.yaml")
        catalog = load_yaml(CONFIG_DIR / "action-catalog-kernel-v0.8.yaml")
        admission_policy = load_yaml(CONFIG_DIR / "admission-policy-kernel-v0.8.yaml")
        approval_manifest = load_yaml(
            CONFIG_DIR / "admission-policy-approval-kernel-v0.8.yaml"
        )
        self.assertEqual(manifest["bindings"]["kernel_gamma_hash"], gamma["hash"])
        self.assertEqual(manifest["bindings"]["kernel_catalog_hash"], catalog["hash"])
        self.assertEqual(
            manifest["bindings"]["admission_policy_hash"],
            admission_policy["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["approval_manifest_hash"],
            approval_manifest["hash"],
        )

    def test_stochastic_example_is_finite_exact_and_matches_registered_tv(self) -> None:
        contract = self.configs["observation"]
        self.assertFalse(contract["execution_authority"])
        self.assertEqual(contract["status"], "CONTRACT_DRAFT")

        for example in contract["contract_examples"]:
            worlds = example["finite_worlds"]
            outcomes = example["finite_outcomes"]
            rows = example["conditional_distribution"]
            self.assertEqual(set(rows), set(worlds))

            distributions: dict[str, dict[str, Fraction]] = {}
            for world, entries in rows.items():
                distribution = {
                    entry["outcome"]: Fraction(
                        entry["probability"]["numerator"],
                        entry["probability"]["denominator"],
                    )
                    for entry in entries
                }
                self.assertEqual(set(distribution), set(outcomes))
                self.assertEqual(sum(distribution.values()), Fraction(1, 1))
                distributions[world] = distribution

            left, right = worlds
            tv = sum(
                abs(distributions[left][outcome] - distributions[right][outcome])
                for outcome in outcomes
            ) / 2
            registered = Fraction(
                example["registered_delta_tv"]["numerator"],
                example["registered_delta_tv"]["denominator"],
            )
            self.assertEqual(tv, registered)

    def test_full_cost_dimensions_are_exact_and_feasibility_is_separate(self) -> None:
        cost = self.configs["cost"]
        self.assertEqual(
            [dimension["dimension_id"] for dimension in cost["dimensions"]],
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
        self.assertEqual(cost["feasibility_semantics"], "SEPARATE_NOT_HIGH_COST")
        self.assertFalse(cost["scalarization"]["enabled"])
        self.assertTrue(cost["scalarization"]["preregistration_required"])
        self.assertTrue(cost["measurement_policy"]["executor_trace_required"])

    def test_b0_manifest_has_no_execution_llm_or_stop_authority(self) -> None:
        manifest = self.configs["manifest"]
        self.assertEqual(manifest["status"], "B0_CONTRACT_ONLY")
        self.assertFalse(manifest["execution_authority"])
        self.assertEqual(manifest["llm_integration"], "FORBIDDEN")
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(manifest["authorized_slice"], "B0_PLANNING_AND_CONTRACTS")
        self.assertEqual(
            manifest["closed_slices"],
            ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
        )

    def test_b0_schema_fails_closed_on_authority_expansion(self) -> None:
        schema = self.schemas["manifest"]
        manifest = self.configs["manifest"]

        for field, value in (
            ("execution_authority", True),
            ("llm_integration", "ALLOWED"),
            ("stop_authority", "PLANNER"),
            ("authorized_slice", "B1_RUNTIME"),
        ):
            invalid = deepcopy(manifest)
            invalid[field] = value
            with self.subTest(field=field):
                self.assertTrue(validate(invalid, schema))

    def test_authority_and_plan_text_keep_b0_narrow(self) -> None:
        authority = (
            ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md"
        ).read_text(encoding="utf-8")
        plan = (
            ROOT / "08-writing" / "part-b-b0-implementation-plan-v0.8-20260723.md"
        ).read_text(encoding="utf-8")
        boundary = (
            ROOT / "contracts" / "part-b-b0-boundary-v0.8.md"
        ).read_text(encoding="utf-8")

        for text in (authority, plan, boundary):
            self.assertIn("B0_PLANNING_AND_CONTRACTS", text)
            self.assertIn("B1–B9", text)
            self.assertIn("LLM", text)
        self.assertIn("legacy `B0 no-acquisition`", plan)


if __name__ == "__main__":
    unittest.main()
