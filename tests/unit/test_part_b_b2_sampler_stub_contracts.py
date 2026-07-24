from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]

CATALOG_PATH = (
    ROOT / "configs" / "part-b-stochastic-observation-catalog-v0.8.yaml"
)
EXACT_FINITE_DECISION_PATH = (
    ROOT / "configs" / "part-b-b2-world-pair-delta-decision-v0.8.yaml"
)

SCHEMA_PATHS = {
    "policy": ROOT / "schemas" / "part-b-b2-sampler-stub-policy.schema.json",
    "fixture": ROOT / "schemas" / "part-b-b2-sampler-stub-fixture.schema.json",
    "trace": ROOT / "schemas" / "part-b-b2-sampler-stub-trace.schema.json",
    "manifest": ROOT / "schemas" / "part-b-b2-sampler-stub-manifest.schema.json",
}
CONFIG_PATHS = {
    "policy": ROOT / "configs" / "part-b-b2-sampler-stub-policy-v0.8.yaml",
    "fixture": ROOT / "configs" / "part-b-b2-sampler-stub-fixture-v0.8.yaml",
    "manifest": ROOT / "configs" / "part-b-b2-sampler-stub-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b2-sampler-stub-boundary-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b2-sampler-stub-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b2-sampler-stub-implementation-plan-v0.8-20260724.md",
)
RUNTIME_PATH = ROOT / "src" / "executor" / "part_b_b2_sampler_stub.py"

PRODUCT_PATHS = (
    *SCHEMA_PATHS.values(),
    *CONFIG_PATHS.values(),
    *DOCUMENT_PATHS,
    RUNTIME_PATH,
)

CATALOG_HASH = (
    "sha256:200f0ccd89525bcbda89ea77101cdcab"
    "7fda675888938ee106e389a1a8beeab5"
)
EXACT_FINITE_DECISION_HASH = (
    "sha256:1a9668ef8c968c968e14587778d261b0"
    "23dff60a0234e4e67251051ec07e5919"
)
FORBIDDEN_AUTHORITIES = (
    "production_sampling_authority",
    "real_source_access_authority",
    "connector_execution_authority",
    "holdout_release_authority",
    "planner_execution_authority",
    "estimated_model_admission_authority",
    "certificate_authority",
)


def require_product(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            "missing approved B2 sampler stub artifact: "
            f"{path.relative_to(ROOT)}"
        )
    return path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(require_product(path).read_text(encoding="utf-8"))


def load_yaml(path: Path, *, product: bool = True) -> dict[str, object]:
    if product:
        path = require_product(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(instance: dict[str, object], schema: dict[str, object]) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


class PartBB2SamplerStubContractTests(unittest.TestCase):
    def test_red_01_exact_sampler_stub_product_set_is_required(self) -> None:
        """RED-01: GREEN needs the finite local-stub product, not ad hoc code."""
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_PATHS
            if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved B2 sampler stub artifacts: " + ", ".join(missing),
        )

    def test_red_02_schemas_are_closed_and_examples_validate(self) -> None:
        """RED-02: policy, fixture, trace and manifest are closed contracts."""
        schemas = {name: load_json(path) for name, path in SCHEMA_PATHS.items()}
        for name, schema in schemas.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)
                self.assertEqual(
                    schema.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertIs(schema.get("additionalProperties"), False)

        for name, path in CONFIG_PATHS.items():
            document = load_yaml(path)
            self.assertEqual(validate(document, schemas[name]), [])
            widened = deepcopy(document)
            widened["undeclared_runtime_authority"] = True
            self.assertTrue(validate(widened, schemas[name]))

    def test_red_03_hashes_replay_and_bind_only_frozen_b2_inputs(self) -> None:
        """RED-03: new identities replay without rewriting frozen B2 hashes."""
        documents = {
            name: load_yaml(path) for name, path in CONFIG_PATHS.items()
        }
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertEqual(
                    document.get("hash"),
                    canonical_document_hash(document),
                )

        manifest = documents["manifest"]
        self.assertEqual(
            manifest["bindings"]["stochastic_catalog_hash"],
            CATALOG_HASH,
        )
        self.assertEqual(
            manifest["bindings"]["exact_finite_decision_hash"],
            EXACT_FINITE_DECISION_HASH,
        )
        self.assertEqual(
            manifest["bindings"]["sampler_policy_hash"],
            documents["policy"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["fixture_hash"],
            documents["fixture"]["hash"],
        )

    def test_red_04_generator_and_seed_commitment_are_explicit(self) -> None:
        """RED-04: replay cannot depend on an implicit RNG or mutable seed."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        generator = policy["generator"]
        self.assertIsInstance(generator["algorithm"], str)
        self.assertTrue(generator["algorithm"])
        self.assertIsInstance(generator["version"], str)
        self.assertTrue(generator["version"])
        self.assertTrue(generator["deterministic_replay"])

        seed = policy["seed_commitment"]
        self.assertEqual(seed["commitment_algorithm"], "SHA256_CANONICAL_JSON")
        self.assertTrue(seed["required_before_sampling"])
        self.assertTrue(seed["post_hoc_change_forbidden"])
        self.assertEqual(seed["scope"], "LOCAL_FIXTURE_ONLY")

    def test_red_05_trial_resource_and_failure_policies_are_finite(self) -> None:
        """RED-05: finite budgets and non-sample failures are preregistered."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        budget = policy["trial_budget"]
        self.assertGreaterEqual(budget["minimum"], 1)
        self.assertLessEqual(budget["minimum"], budget["default"])
        self.assertLessEqual(budget["default"], budget["maximum"])
        self.assertIsInstance(budget["maximum"], int)
        self.assertLessEqual(budget["maximum"], 100_000)
        self.assertTrue(budget["adaptive_extension_forbidden"])

        resource = policy["resource_policy"]
        self.assertEqual(resource["budget_scope"], "PER_TRACE")
        self.assertTrue(resource["exhaustion_stops_trace"])
        self.assertFalse(resource["partial_trace_implies_success"])

        failures = policy["failure_semantics"]
        for failure in ("TIMEOUT", "RESOURCE_EXHAUSTED", "MODEL_INVALID"):
            self.assertEqual(failures[failure]["status"], "UNKNOWN")
            self.assertFalse(failures[failure]["sample_emitted"])
            self.assertFalse(failures[failure]["unsat"])
        self.assertEqual(failures["INFEASIBLE"]["status"], "INFEASIBLE")
        self.assertFalse(failures["INFEASIBLE"]["sample_emitted"])

    def test_red_06_fixture_is_catalog_only_and_never_ceiling_eligible(self) -> None:
        """RED-06: the stub can name only rows in the frozen B2 fixture catalog."""
        fixture = load_yaml(CONFIG_PATHS["fixture"])
        catalog = load_yaml(CATALOG_PATH, product=False)
        self.assertEqual(fixture["source_scope"], "FROZEN_B2_FIXTURE_CATALOG_ONLY")
        self.assertEqual(fixture["catalog_path"], str(CATALOG_PATH.relative_to(ROOT)))
        self.assertEqual(fixture["catalog_hash"], CATALOG_HASH)
        self.assertFalse(fixture["real_source_access"])
        self.assertFalse(fixture["catalog_ceiling_eligible"])

        catalog_domains = {
            entry["action_id"]: set(entry["finite_worlds"])
            for entry in catalog["entries"]
        }
        for case in fixture["allowed_cases"]:
            self.assertIn(case["action_id"], catalog_domains)
            self.assertTrue(
                set(case["world_ids"]).issubset(catalog_domains[case["action_id"]])
            )
            self.assertFalse(case["catalog_ceiling_eligible"])

    def test_red_07_manifest_and_docs_keep_every_adjacent_gate_closed(self) -> None:
        """RED-07: a local fixture stub does not open empirical or STOP authority."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest["status"], "B2_SAMPLER_STUB_LOCAL_ONLY")
        self.assertEqual(
            manifest["pb_b2_si_003_state"],
            "OPEN_BLOCKS_EMPIRICAL_MODEL_ADMISSION",
        )
        self.assertEqual(manifest["pb_si_006_state"], "OPEN_DEFAULT_DENY")
        self.assertEqual(manifest["pb_b5_si_001_state"], "OPEN_DEFAULT_DENY")
        self.assertEqual(manifest["holdout_release"], "DENY")
        self.assertEqual(manifest["stop_authority"], "NONE")
        for field in FORBIDDEN_AUTHORITIES:
            with self.subTest(authority=field):
                self.assertIs(manifest[field], False)

        corpus = "\n".join(
            require_product(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        )
        for token in (
            "PB-B2-SI-002",
            "PB-B2-SI-003",
            "PB-SI-006",
            "PB-B5-SI-001",
            "FROZEN_B2_FIXTURE_CATALOG_ONLY",
            "catalog_ceiling_eligible=false",
            "holdout release",
            "CERTIFIED_STOP",
        ):
            with self.subTest(token=token):
                self.assertIn(token, corpus)
        self.assertIn("OPEN", corpus)
        self.assertIn("DENY", corpus)


if __name__ == "__main__":
    unittest.main()
