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
CONTRACT_DIR = ROOT / "contracts"
SCOPE_DIR = ROOT / "src" / "scope"
WRITING_DIR = ROOT / "08-writing"

PRODUCT_ARTIFACTS = (
    SCHEMA_DIR / "part-b-b8-holdout-deny-audit-policy.schema.json",
    SCHEMA_DIR / "part-b-b8-holdout-deny-audit-record.schema.json",
    SCHEMA_DIR / "part-b-b8-holdout-deny-audit-manifest.schema.json",
    CONFIG_DIR / "part-b-b8-holdout-deny-audit-policy-v0.8.yaml",
    CONFIG_DIR / "part-b-b8-holdout-deny-audit-example-v0.8.yaml",
    CONFIG_DIR / "part-b-b8-holdout-deny-audit-manifest-v0.8.yaml",
    CONTRACT_DIR / "part-b-b8-holdout-deny-audit-boundary-v0.8.md",
    CONTRACT_DIR / "part-b-b8-holdout-deny-audit-v0.8.md",
    SCOPE_DIR / "part_b_b8_holdout_deny_audit.py",
    SCOPE_DIR / "part-b-b8-holdout-deny-audit-spec-issues.md",
    WRITING_DIR
    / "part-b-b8-holdout-deny-audit-implementation-plan-v0.8-20260724.md",
    WRITING_DIR / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)

SCHEMA_PATHS = {
    "policy": PRODUCT_ARTIFACTS[0],
    "record": PRODUCT_ARTIFACTS[1],
    "manifest": PRODUCT_ARTIFACTS[2],
}
SCHEMA_FOR_CONFIG = {
    "policy": "policy",
    "example": "record",
    "manifest": "manifest",
}
CONFIG_PATHS = {
    "policy": PRODUCT_ARTIFACTS[3],
    "example": PRODUCT_ARTIFACTS[4],
    "manifest": PRODUCT_ARTIFACTS[5],
}

UPSTREAM_B8 = {
    "holdout_analysis_policy_hash": CONFIG_DIR
    / "part-b-holdout-analysis-policy-v0.8.yaml",
    "holdout_preregistration_hash": CONFIG_DIR
    / "part-b-holdout-preregistration-v0.8.yaml",
    "holdout_analysis_envelope_hash": CONFIG_DIR
    / "part-b-holdout-analysis-envelope-example-v0.8.yaml",
    "b8_manifest_hash": CONFIG_DIR / "part-b-b8-manifest-v0.8.yaml",
}


class PartBB8HoldoutDenyAuditContractTests(unittest.TestCase):
    def require_product(self) -> None:
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_ARTIFACTS
            if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved artifact/module: " + ", ".join(missing),
        )

    def load_yaml(self, path: Path) -> dict[str, object]:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def load_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_red_01_exact_deny_audit_products_are_present(self) -> None:
        """RED-01: the approved DENY-audit product set is mandatory."""
        self.require_product()

    def test_red_02_schemas_are_closed_draft_2020_12(self) -> None:
        """RED-02: policy, record and manifest reject schema widening."""
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

    def test_red_03_configs_validate_and_hash_replay(self) -> None:
        """RED-03: examples are schema-valid and self-bound by SHA-256."""
        self.require_product()
        for name, path in CONFIG_PATHS.items():
            with self.subTest(config=name):
                document = self.load_yaml(path)
                schema = self.load_json(
                    SCHEMA_PATHS[SCHEMA_FOR_CONFIG[name]]
                )
                self.assertEqual(
                    sorted(
                        Draft202012Validator(schema).iter_errors(document),
                        key=lambda error: list(error.absolute_path),
                    ),
                    [],
                )
                self.assertEqual(
                    document.get("hash"),
                    canonical_document_hash(document),
                )
                expanded = deepcopy(document)
                expanded["unexpected_authority"] = True
                self.assertNotEqual(
                    list(Draft202012Validator(schema).iter_errors(expanded)),
                    [],
                )

    def test_red_04_b8_inputs_are_read_only_hash_bindings(self) -> None:
        """RED-04: the audit binds B8 artifacts without rewriting them."""
        self.require_product()
        policy = self.load_yaml(CONFIG_PATHS["policy"])
        manifest = self.load_yaml(CONFIG_PATHS["manifest"])
        expected = {
            key: self.load_yaml(path)["hash"]
            for key, path in UPSTREAM_B8.items()
        }
        self.assertEqual(policy["bindings"], expected)
        self.assertEqual(manifest["bindings"], expected)
        for path in UPSTREAM_B8.values():
            document = self.load_yaml(path)
            self.assertEqual(document["hash"], canonical_document_hash(document))

    def test_red_05_manifest_is_deny_only(self) -> None:
        """RED-05: no holdout access or execution authority is granted."""
        self.require_product()
        manifest = self.load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(
            manifest["authorized_slice"],
            "B8_HOLDOUT_DENY_AUDIT",
        )
        self.assertEqual(
            manifest["status"],
            "B8_HOLDOUT_DENY_AUDIT",
        )
        self.assertEqual(
            manifest["claim_ceiling"],
            "HOLDOUT_DENY_AUDIT_ONLY",
        )
        self.assertEqual(manifest["default_decision"], "DENY")
        self.assertEqual(manifest["release_decision"], "DENY")
        for field in (
            "holdout_data_access_authority",
            "holdout_label_access_authority",
            "holdout_result_access_authority",
            "statistical_analysis_execution_authority",
            "performance_claim_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(manifest[field], False)
        self.assertEqual(manifest["stop_authority"], "NONE")

    def test_red_06_upstream_gates_remain_open_or_deny(self) -> None:
        """RED-06: this audit cannot close adjacent execution gates."""
        self.require_product()
        policy = self.load_yaml(CONFIG_PATHS["policy"])
        manifest = self.load_yaml(CONFIG_PATHS["manifest"])
        gates = {
            **policy["open_gates"],
            **manifest["open_gates"],
        }
        self.assertEqual(gates["PB-B8-SI-001"], "OPEN")
        self.assertEqual(gates["PB-B8-SI-002"], "OPEN")
        self.assertEqual(gates["PB-B8-SI-003"], "OPEN")
        self.assertEqual(gates["PB-B8-SI-004"], "OPEN")
        self.assertEqual(gates["PB-SI-006"], "DENY")
        self.assertEqual(gates["PB-B5-SI-001"], "NOT_ESTABLISHED")
        self.assertEqual(gates["CERTIFIED_STOP"], "NONE")

    def test_red_07_examples_contain_no_holdout_payload_or_authority(self) -> None:
        """RED-07: audit examples contain no labels, results or data access."""
        self.require_product()
        forbidden_keys = {
            "holdout_data",
            "labels",
            "results",
            "statistics",
            "p_values",
            "effect_estimates",
            "scores",
            "rankings",
            "dataset_path",
            "endpoint",
            "credential",
            "token",
        }
        for name, path in CONFIG_PATHS.items():
            with self.subTest(config=name):
                document = self.load_yaml(path)
                serialized = json.dumps(document, sort_keys=True).lower()
                for key in forbidden_keys:
                    self.assertNotIn(f'"{key}"', serialized)
                self.assertEqual(
                    document["access_boundary"],
                    {
                        "holdout_data_loaded": False,
                        "holdout_labels_loaded": False,
                        "holdout_results_loaded": False,
                        "statistics_computed": False,
                    },
                )

    def test_red_08_docs_cap_claims_at_deny_audit_only(self) -> None:
        """RED-08: documentation cannot describe release or certification."""
        self.require_product()
        text = "\n".join(
            path.read_text(encoding="utf-8") for path in PRODUCT_ARTIFACTS
            if path.suffix in {".md", ".py"}
        ).upper()
        for required in (
            "HOLDOUT_DENY_AUDIT_ONLY",
            "DEFAULT_DECISION=DENY",
            "NO HOLDOUT LABEL",
            "NO HOLDOUT RESULT",
            "NO STATISTICAL",
            "PB-B8-SI-004",
            "CERTIFIED_STOP",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertNotIn("RELEASE AUTHORITY=GRANTED", text)
        self.assertNotIn("SUPERIORITY CLAIM=ALLOWED", text)


if __name__ == "__main__":
    unittest.main()
