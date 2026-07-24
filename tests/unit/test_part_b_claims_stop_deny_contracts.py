from __future__ import annotations

import ast
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
CONTRACT_DIR = ROOT / "contracts"
SCOPE_DIR = ROOT / "src" / "scope"
WRITING_DIR = ROOT / "08-writing"

PRODUCT_ARTIFACTS = (
    SCHEMA_DIR / "part-b-claims-stop-deny-policy.schema.json",
    SCHEMA_DIR / "part-b-claims-stop-deny-record.schema.json",
    SCHEMA_DIR / "part-b-claims-stop-deny-manifest.schema.json",
    CONFIG_DIR / "part-b-claims-stop-deny-policy-v0.8.yaml",
    CONFIG_DIR / "part-b-claims-stop-deny-example-v0.8.yaml",
    CONFIG_DIR / "part-b-claims-stop-deny-manifest-v0.8.yaml",
    CONTRACT_DIR / "part-b-claims-stop-deny-boundary-v0.8.md",
    CONTRACT_DIR / "part-b-claims-stop-deny-v0.8.md",
    SCOPE_DIR / "part_b_claims_stop_deny.py",
    SCOPE_DIR / "part-b-claims-stop-deny-spec-issues.md",
    SCOPE_DIR / "part-b-b0-spec-issues.md",
    WRITING_DIR
    / "part-b-claims-stop-deny-implementation-plan-v0.8-20260724.md",
    WRITING_DIR / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)

SCHEMA_PATHS = {
    "policy": PRODUCT_ARTIFACTS[0],
    "record": PRODUCT_ARTIFACTS[1],
    "manifest": PRODUCT_ARTIFACTS[2],
}
CONFIG_PATHS = {
    "policy": PRODUCT_ARTIFACTS[3],
    "record": PRODUCT_ARTIFACTS[4],
    "manifest": PRODUCT_ARTIFACTS[5],
}

CLAIM_CEILING = "CONTRACT_CONSISTENCY_ONLY"
SLICE_STATUS = "CLAIMS_STOP_DENY_GATE_ONLY"
CERTIFIED_STOP_STATUS = "NOT_AUTHORIZED"


class PartBClaimsStopDenyContractTests(unittest.TestCase):
    def require_product(self) -> None:
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_ARTIFACTS
            if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved artifacts/module: " + ", ".join(missing),
        )

    def load_yaml(self, path: Path) -> dict[str, object]:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def load_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_red_01_exact_claims_stop_deny_products_are_present(self) -> None:
        """RED-01: the approved claims/STOP DENY product set is mandatory."""
        self.require_product()

    def test_red_02_schemas_are_closed_draft_2020_12(self) -> None:
        """RED-02: policy, record and manifest reject surface widening."""
        self.require_product()
        for name, path in SCHEMA_PATHS.items():
            with self.subTest(schema=name):
                schema = self.load_json(path)
                Draft202012Validator.check_schema(schema)
                self.assertEqual(
                    schema.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertEqual(schema.get("type"), "object")
                self.assertFalse(schema.get("additionalProperties", True))

    def test_red_03_configs_validate_hash_and_reject_unknown_fields(
        self,
    ) -> None:
        """RED-03: configs are closed and canonically self-bound."""
        self.require_product()
        for name, path in CONFIG_PATHS.items():
            with self.subTest(config=name):
                document = self.load_yaml(path)
                schema = self.load_json(SCHEMA_PATHS[name])
                validator = Draft202012Validator(schema)
                self.assertEqual(list(validator.iter_errors(document)), [])
                self.assertEqual(
                    document["hash"],
                    canonical_document_hash(document),
                )
                widened = deepcopy(document)
                widened["certified_stop_override"] = True
                self.assertNotEqual(
                    list(validator.iter_errors(widened)),
                    [],
                )

    def test_red_04_frozen_claim_and_stop_states_are_simultaneous(
        self,
    ) -> None:
        """RED-04: every product carries the exact DENY ceiling."""
        self.require_product()
        for name, path in CONFIG_PATHS.items():
            with self.subTest(config=name):
                document = self.load_yaml(path)
                self.assertEqual(
                    document["claim_ceiling_remainder"],
                    CLAIM_CEILING,
                )
                self.assertIs(document["scalarization_authority"], False)
                self.assertEqual(
                    document["scalarization_decision"],
                    "DENY",
                )
                self.assertIs(
                    document["performance_superiority_authority"],
                    False,
                )
                self.assertEqual(
                    document["performance_superiority_decision"],
                    "DENY",
                )
                self.assertEqual(document["stop_authority"], "NONE")
                self.assertEqual(
                    document["certified_stop"],
                    CERTIFIED_STOP_STATUS,
                )
                self.assertEqual(
                    document["slice_status"],
                    SLICE_STATUS,
                )

    def test_red_05_manifest_preserves_adjacent_denies(self) -> None:
        """RED-05: the gate cannot widen any adjacent execution track."""
        self.require_product()
        manifest = self.load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest["holdout_release"], "DENY")
        self.assertEqual(manifest["pb_si_006_download"], "DENY")
        self.assertEqual(manifest["pb_si_008"], "NOT_OPENED")
        self.assertEqual(
            manifest["pb_b5_execution"],
            "NOT_ESTABLISHED",
        )
        for field in (
            "certificate_issuance_authority",
            "level_certificate_authority",
            "part_a_stop_authority_extension",
            "sampler_result_stop_authority",
            "admission_result_stop_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(manifest[field], False)

    def test_red_06_docs_require_separate_highest_stringency_gate(
        self,
    ) -> None:
        """RED-06: human contracts state DENY and the future review gate."""
        self.require_product()
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in PRODUCT_ARTIFACTS
            if path.suffix == ".md"
        ).upper()
        for required in (
            CLAIM_CEILING,
            SLICE_STATUS,
            "SCALARIZED_RANKING",
            "PERFORMANCE_SUPERIORITY",
            "CERTIFICATE_ISSUED",
            "CERTIFIED_STOP",
            "NOT_AUTHORIZED",
            "SEPARATE HIGHEST-STRINGENCY AUTHORIZATION",
            "PART A KERNEL GAMMA UNCHANGED",
            "DENY GATE ONLY",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_red_07_runtime_has_no_network_llm_or_data_access(self) -> None:
        """RED-07: local classification performs no external or data I/O."""
        self.require_product()
        source = PRODUCT_ARTIFACTS[8].read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "openai",
                    "anthropic",
                    "requests",
                    "urllib",
                    "socket",
                    "subprocess",
                    "pathlib",
                }
            )
        )
        forbidden_calls = {
            "open",
            "read_text",
            "read_bytes",
            "iterdir",
            "glob",
            "rglob",
            "exists",
        }
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        } | {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
        }
        self.assertTrue(called.isdisjoint(forbidden_calls))

    def test_red_08_configs_have_no_weights_results_or_certificate(
        self,
    ) -> None:
        """RED-08: configuration cannot smuggle an empirical STOP basis."""
        self.require_product()
        forbidden_exact_keys = {
            "weights",
            "scalar_weights",
            "scalar_score",
            "ranking",
            "performance_result",
            "superiority_result",
            "certificate",
            "level_certificate",
            "system_status",
            "kernel_gamma",
            "holdout_result",
        }
        for name, path in CONFIG_PATHS.items():
            with self.subTest(config=name):
                serialized = json.dumps(
                    self.load_yaml(path),
                    sort_keys=True,
                ).lower()
                for forbidden in forbidden_exact_keys:
                    self.assertNotIn(f'"{forbidden}"', serialized)


if __name__ == "__main__":
    unittest.main()
