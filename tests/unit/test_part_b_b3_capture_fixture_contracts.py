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
    "policy": SCHEMA_DIR / "part-b-b3-capture-fixture-policy.schema.json",
    "fixture": SCHEMA_DIR / "part-b-b3-capture-fixture.schema.json",
    "result": SCHEMA_DIR / "part-b-b3-capture-fixture-result.schema.json",
    "manifest": SCHEMA_DIR / "part-b-b3-capture-fixture-manifest.schema.json",
}
CONFIG_PATHS = {
    "policy": CONFIG_DIR / "part-b-b3-capture-fixture-policy-v0.8.yaml",
    "fixture": CONFIG_DIR / "part-b-b3-capture-fixture-v0.8.yaml",
    "result": CONFIG_DIR / "part-b-b3-capture-fixture-result-example-v0.8.yaml",
    "manifest": CONFIG_DIR / "part-b-b3-capture-fixture-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b3-capture-fixture-boundary-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b3-capture-fixture-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b3-capture-fixture-implementation-plan-v0.8-20260724.md",
)
RUNTIME_PATH = ROOT / "src" / "cost" / "part_b_b3_capture_fixture.py"
PRODUCT_PATHS = (
    *SCHEMA_PATHS.values(),
    *CONFIG_PATHS.values(),
    *DOCUMENT_PATHS,
    RUNTIME_PATH,
)

FROZEN_B3_POLICY_PATH = (
    CONFIG_DIR / "part-b-cost-instrumentation-policy-v0.8.yaml"
)
FROZEN_B3_TRACE_SCHEMA_PATH = SCHEMA_DIR / "part-b-cost-trace.schema.json"


def require_product(test_case: unittest.TestCase, path: Path) -> Path:
    if not path.is_file():
        test_case.fail(
            "missing approved B3 capture fixture artifact: "
            f"{path.relative_to(ROOT)}"
        )
    return path


def load_json(test_case: unittest.TestCase, path: Path) -> dict[str, object]:
    product = require_product(test_case, path)
    return json.loads(product.read_text(encoding="utf-8"))


def load_yaml(test_case: unittest.TestCase, path: Path) -> dict[str, object]:
    product = require_product(test_case, path)
    return yaml.safe_load(product.read_text(encoding="utf-8"))


def validate(
    instance: dict[str, object], schema: dict[str, object]
) -> list[object]:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


class PartBB3CaptureFixtureContractTests(unittest.TestCase):
    def test_red_01_exact_capture_fixture_product_set_is_required(self) -> None:
        """RED-01: GREEN requires an approved synthetic-capture product set."""
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_PATHS
            if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved B3 capture fixture artifacts: " + ", ".join(missing),
        )

    def test_red_02_schemas_are_closed_and_examples_validate(self) -> None:
        """RED-02: all fixture contracts are closed draft-2020-12 schemas."""
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
                self.assertEqual(validate(document, schemas[name]), [])
                widened = deepcopy(document)
                widened["undeclared_production_authority"] = True
                self.assertTrue(validate(widened, schemas[name]))

    def test_red_03_hashes_replay_and_bind_frozen_b3_contract(self) -> None:
        """RED-03: fixture identities bind B3 without rewriting its contract."""
        documents = {
            name: load_yaml(self, path) for name, path in CONFIG_PATHS.items()
        }
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertEqual(
                    document.get("hash"),
                    canonical_document_hash(document),
                )

        frozen_policy = yaml.safe_load(
            FROZEN_B3_POLICY_PATH.read_text(encoding="utf-8")
        )
        manifest = documents["manifest"]
        self.assertEqual(
            manifest["bindings"]["b3_policy_hash"],
            frozen_policy["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["b3_trace_schema_path"],
            FROZEN_B3_TRACE_SCHEMA_PATH.relative_to(ROOT).as_posix(),
        )
        self.assertEqual(
            manifest["bindings"]["capture_fixture_policy_hash"],
            documents["policy"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["fixture_hash"],
            documents["fixture"]["hash"],
        )

    def test_red_04_fixture_provenance_is_explicitly_non_production(self) -> None:
        """RED-04: synthetic fixture output cannot be narrated as production."""
        fixture = load_yaml(self, CONFIG_PATHS["fixture"])
        self.assertEqual(fixture["source_kind"], "FIXTURE_SYNTHETIC")
        self.assertEqual(
            fixture["measurement_class"],
            "NOT_PRODUCTION_MEASUREMENT",
        )
        self.assertFalse(fixture["real_os_access"])
        self.assertFalse(fixture["billing_connector_access"])
        self.assertFalse(fixture["production_adapter_authority"])
        self.assertIsInstance(fixture["events"], list)
        self.assertGreater(len(fixture["events"]), 0)

    def test_red_05_policy_freezes_eight_dimensions_and_unknown_not_zero(self) -> None:
        """RED-05: the fixture uses the frozen B3 vector and explicit missingness."""
        policy = load_yaml(self, CONFIG_PATHS["policy"])
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
        self.assertTrue(policy["missingness"]["implicit_zero_forbidden"])
        self.assertEqual(
            policy["feasibility"]["semantics"],
            "SEPARATE_NOT_HIGH_COST",
        )

    def test_red_06_no_fx_scalarization_or_performance_authority(self) -> None:
        """RED-06: fixture capture cannot normalize, scalarize, or rank costs."""
        policy = load_yaml(self, CONFIG_PATHS["policy"])
        self.assertEqual(
            policy["currency"]["mixed_currency_behavior"],
            "FAIL_CLOSED_NO_IMPLICIT_FX",
        )
        self.assertFalse(policy["currency"]["fx_normalization_authority"])
        self.assertFalse(policy["scalarization"]["enabled"])
        self.assertIsNone(policy["scalarization"]["weights"])
        self.assertFalse(policy["performance_claim_authority"])
        self.assertFalse(policy["superiority_claim_authority"])

    def test_red_07_manifest_and_docs_keep_adjacent_gates_closed(self) -> None:
        """RED-07: this fixture path opens no production or STOP authority."""
        manifest = load_yaml(self, CONFIG_PATHS["manifest"])
        self.assertEqual(manifest["status"], "B3_CAPTURE_FIXTURE_LOCAL_ONLY")
        self.assertEqual(
            manifest["pb_b3_si_001_state"],
            "FIXTURE_PATH_ONLY_REAL_ADAPTER_OPEN",
        )
        self.assertEqual(manifest["pb_b3_si_002_state"], "OPEN")
        self.assertEqual(manifest["pb_b3_si_003_state"], "OPEN")
        self.assertEqual(manifest["pb_b3_si_004_state"], "OPEN")
        self.assertFalse(manifest["production_capture_authority"])
        self.assertFalse(manifest["real_adapter_authority"])
        self.assertFalse(manifest["scalarization_authority"])
        self.assertFalse(manifest["performance_claim_authority"])
        self.assertEqual(manifest["holdout_release"], "DENY")
        self.assertEqual(manifest["stop_authority"], "NONE")

        corpus = "\n".join(
            require_product(self, path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        )
        for token in (
            "FIXTURE_SYNTHETIC",
            "NOT_PRODUCTION_MEASUREMENT",
            "UNKNOWN_NOT_ZERO",
            "PB-B3-SI-001",
            "PB-B3-SI-002",
            "PB-B3-SI-003",
            "PB-B3-SI-004",
            "no FX",
            "scalarization",
            "CERTIFIED_STOP",
        ):
            with self.subTest(token=token):
                self.assertIn(token, corpus)
        self.assertIn("OPEN", corpus)
        self.assertIn("DENY", corpus)


if __name__ == "__main__":
    unittest.main()
