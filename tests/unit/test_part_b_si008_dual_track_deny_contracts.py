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
    SCHEMA_DIR / "part-b-si008-dual-track-deny-policy.schema.json",
    SCHEMA_DIR / "part-b-si008-dual-track-deny-record.schema.json",
    SCHEMA_DIR / "part-b-si008-dual-track-deny-manifest.schema.json",
    CONFIG_DIR / "part-b-si008-dual-track-deny-policy-v0.8.yaml",
    CONFIG_DIR / "part-b-si008-dual-track-deny-example-v0.8.yaml",
    CONFIG_DIR / "part-b-si008-dual-track-deny-manifest-v0.8.yaml",
    CONTRACT_DIR / "part-b-si008-dual-track-deny-boundary-v0.8.md",
    CONTRACT_DIR / "part-b-si008-dual-track-deny-v0.8.md",
    SCOPE_DIR / "part_b_si008_dual_track_deny.py",
    SCOPE_DIR / "part-b-si008-dual-track-deny-spec-issues.md",
    SCOPE_DIR / "part-b-b0-spec-issues.md",
    WRITING_DIR
    / "part-b-si008-dual-track-deny-implementation-plan-v0.8-20260724.md",
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

PART_B_STATUS = "OUTSIDE_AUTHORIZED_TRACK_DENY"
EXPERIMENT_STATUS = "MAY_PROCEED_UNDER_SEPARATE_AUTHORITY"
PB_SI_008_STATUS = "NOT_OPENED"


class PartBSI008DualTrackDenyContractTests(unittest.TestCase):
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

    def test_red_01_exact_dual_track_products_are_present(self) -> None:
        """RED-01: the approved dual-track gate product set is mandatory."""
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
        """RED-03: all examples are closed and canonically self-bound."""
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
                widened["global_llm_ban"] = True
                self.assertNotEqual(
                    list(validator.iter_errors(widened)),
                    [],
                )

    def test_red_04_three_frozen_states_are_simultaneous(self) -> None:
        """RED-04: Part B denial and experiment non-interference coexist."""
        self.require_product()
        for name, path in CONFIG_PATHS.items():
            with self.subTest(config=name):
                document = self.load_yaml(path)
                self.assertEqual(document["part_b_status"], PART_B_STATUS)
                self.assertEqual(
                    document["experiment_track_status"],
                    EXPERIMENT_STATUS,
                )
                self.assertEqual(
                    document["pb_si_008_status"],
                    PB_SI_008_STATUS,
                )

    def test_red_05_manifest_preserves_adjacent_denies(self) -> None:
        """RED-05: SI-008 cannot widen any adjacent execution authority."""
        self.require_product()
        manifest = self.load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest["holdout_release"], "DENY")
        self.assertEqual(manifest["pb_si_006_download"], "DENY")
        self.assertEqual(
            manifest["pb_b5_execution"],
            "NOT_ESTABLISHED",
        )
        self.assertEqual(manifest["pb_b8_si_004"], "OPEN")
        self.assertEqual(manifest["stop_authority"], "NONE")
        for field in (
            "part_b_evidence_authority",
            "part_b_claim_authority",
            "part_b_authority_grant",
            "part_b_pass_condition_authority",
            "llm_execution_authority",
            "experiment_artifact_access_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(manifest[field], False)

    def test_red_06_docs_define_separation_not_global_llm_ban(self) -> None:
        """RED-06: human-readable contracts preserve both tracks."""
        self.require_product()
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in PRODUCT_ARTIFACTS
            if path.suffix == ".md"
        ).upper()
        for required in (
            PART_B_STATUS,
            EXPERIMENT_STATUS,
            "PB-SI-008",
            "NOT_OPENED",
            "DUAL-TRACK SEPARATION",
            "NOT A GLOBAL LLM BAN",
            "NO REAL LLM CALL",
            "NO EXPERIMENT ARTIFACT READ",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertNotIn("LLM EXPERIMENTS MUST STOP", text)

    def test_red_07_runtime_source_has_no_llm_or_filesystem_io(self) -> None:
        """RED-07: gate evaluation cannot invoke or inspect experiment work."""
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

    def test_red_08_configs_carry_no_experiment_payload_or_result(self) -> None:
        """RED-08: product validity cannot depend on experiment artifacts."""
        self.require_product()
        forbidden_exact_keys = {
            "llm_output",
            "experiment_output",
            "experiment_result",
            "experiment_test_result",
            "experiment_path",
            "payload",
            "prompt",
            "model_response",
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
