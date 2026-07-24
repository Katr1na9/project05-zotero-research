from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
CONFIG_DIR = ROOT / "configs"

SCHEMA_PATHS = {
    "policy": SCHEMA_DIR / "part-b-holdout-analysis-policy.schema.json",
    "preregistration": (
        SCHEMA_DIR / "part-b-holdout-preregistration.schema.json"
    ),
    "analysis_plan": (
        SCHEMA_DIR / "part-b-statistical-analysis-plan.schema.json"
    ),
    "analysis_envelope": (
        SCHEMA_DIR / "part-b-holdout-analysis-envelope.schema.json"
    ),
    "manifest": SCHEMA_DIR / "part-b-b8-manifest.schema.json",
}
CONFIG_PATHS = {
    "policy": CONFIG_DIR / "part-b-holdout-analysis-policy-v0.8.yaml",
    "preregistration": (
        CONFIG_DIR / "part-b-holdout-preregistration-v0.8.yaml"
    ),
    "analysis_plan": (
        CONFIG_DIR / "part-b-statistical-analysis-plan-example-v0.8.yaml"
    ),
    "analysis_envelope": (
        CONFIG_DIR / "part-b-holdout-analysis-envelope-example-v0.8.yaml"
    ),
    "manifest": CONFIG_DIR / "part-b-b8-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b8-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-b8-holdout-analysis-v0.8.md",
    ROOT / "contracts" / "part-b-b8-statistical-preregistration-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b8-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b8-implementation-plan-v0.8-20260724.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)

B7_CONFIG_BINDINGS = {
    "b7_connector_policy_hash": (
        CONFIG_DIR / "part-b-connector-contract-policy-v0.8.yaml"
    ),
    "b7_descriptor_example_hash": (
        CONFIG_DIR / "part-b-connector-descriptor-example-v0.8.yaml"
    ),
    "b7_source_authorization_example_hash": (
        CONFIG_DIR / "part-b-source-authorization-example-v0.8.yaml"
    ),
    "b7_provenance_envelope_example_hash": (
        CONFIG_DIR / "part-b-provenance-envelope-example-v0.8.yaml"
    ),
    "b7_manifest_hash": CONFIG_DIR / "part-b-b7-manifest-v0.8.yaml",
}


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B8 artifact: {path.relative_to(ROOT)}"
        )
    return path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(require_file(path).read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(require_file(path).read_text(encoding="utf-8"))


def validate(instance: dict[str, object], schema: dict[str, object]) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


def walk(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def expected_b1_b7_bindings() -> dict[str, str]:
    b7_manifest = load_yaml(CONFIG_DIR / "part-b-b7-manifest-v0.8.yaml")
    inherited = dict(b7_manifest["bindings"])
    for binding_key, path in B7_CONFIG_BINDINGS.items():
        document = load_yaml(path)
        document_hash = document.get("hash")
        if document_hash != canonical_document_hash(document):
            raise AssertionError(
                f"upstream B7 hash does not replay: {path.relative_to(ROOT)}"
            )
        inherited[binding_key] = document_hash
    return inherited


class PartBB8ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        """Keep RED counting one missing-artifact failure per test method."""
        for path in (
            *SCHEMA_PATHS.values(),
            *CONFIG_PATHS.values(),
            *DOCUMENT_PATHS,
        ):
            require_file(path)

    def test_red_01_required_b8_artifacts_exist(self) -> None:
        """RED-01: the exact sixteen non-test B8 artifacts are mandatory."""
        paths = (
            *SCHEMA_PATHS.values(),
            *CONFIG_PATHS.values(),
            *DOCUMENT_PATHS,
        )
        missing = [
            str(path.relative_to(ROOT)) for path in paths if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved B8 artifacts: " + ", ".join(missing),
        )

    def test_red_02_schemas_are_closed_draft_2020_12_contracts(self) -> None:
        """RED-02: every B8 Schema is valid and rejects top-level widening."""
        for name, path in SCHEMA_PATHS.items():
            with self.subTest(schema=name):
                schema = load_json(path)
                Draft202012Validator.check_schema(schema)
                self.assertEqual(
                    schema.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertEqual(schema.get("type"), "object")
                self.assertFalse(schema.get("additionalProperties", True))

    def test_red_03_configs_validate_and_unknown_fields_fail_closed(self) -> None:
        """RED-03: examples validate and undeclared B8 authority is rejected."""
        for name in SCHEMA_PATHS:
            with self.subTest(artifact=name):
                schema = load_json(SCHEMA_PATHS[name])
                instance = load_yaml(CONFIG_PATHS[name])
                self.assertEqual(validate(instance, schema), [])
                expanded = deepcopy(instance)
                expanded["unexpected_b8_authority"] = True
                self.assertNotEqual(validate(expanded, schema), [])

    def test_red_04_hashes_replay_and_tampering_is_visible(self) -> None:
        """RED-04: every B8 config is self-bound by canonical SHA-256."""
        for name, path in CONFIG_PATHS.items():
            with self.subTest(artifact=name):
                document = load_yaml(path)
                self.assertEqual(
                    document.get("hash"),
                    canonical_document_hash(document),
                )

                missing = deepcopy(document)
                missing.pop("hash")
                self.assertNotEqual(validate(missing, load_json(SCHEMA_PATHS[name])), [])

                wrong = deepcopy(document)
                wrong["hash"] = "sha256:" + ("0" * 64)
                self.assertNotEqual(
                    wrong["hash"],
                    canonical_document_hash(wrong),
                )

                tampered = deepcopy(document)
                tampered["schema_version"] = "0.8.0-tampered"
                self.assertNotEqual(
                    document.get("hash"),
                    canonical_document_hash(tampered),
                )

    def test_red_05_b1_b7_hashes_are_exact_read_only_bindings(self) -> None:
        """RED-05: policy and manifest replay all approved B1-B7 hashes."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        policy = load_yaml(CONFIG_PATHS["policy"])
        expected = expected_b1_b7_bindings()
        self.assertEqual(policy.get("bindings"), expected)
        self.assertEqual(manifest.get("bindings"), expected)

    def test_red_06_manifest_grants_contract_authority_only(self) -> None:
        """RED-06: B8 freezes contracts but cannot access or analyze data."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest.get("status"), "B8_CONTRACT_ONLY")
        self.assertEqual(
            manifest.get("authorized_slice"), "B8_HOLDOUT_ANALYSIS"
        )
        for field in (
            "holdout_preregistration_contract_authority",
            "statistical_analysis_contract_authority",
            "analysis_envelope_contract_authority",
        ):
            with self.subTest(contract_authority=field):
                self.assertIs(manifest.get(field), True)
        for field in (
            "holdout_data_access_authority",
            "holdout_label_access_authority",
            "holdout_result_access_authority",
            "statistical_analysis_execution_authority",
            "source_selection_authority",
            "source_authorization_authority",
            "connector_execution_authority",
            "retrieval_authority",
            "download_authority",
            "planner_execution_authority",
            "sampling_authority",
            "evaluation_execution_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(manifest.get(field), False)
        self.assertEqual(manifest.get("stop_authority"), "NONE")

    def test_red_07_b9_and_every_runtime_remain_closed(self) -> None:
        """RED-07: opening B8 contracts does not open B9 or a runtime."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        policy = load_yaml(CONFIG_PATHS["policy"])
        self.assertEqual(manifest.get("closed_slices"), ["B9"])
        self.assertEqual(manifest.get("llm_integration"), "FORBIDDEN")
        self.assertEqual(
            policy.get("runtime_boundary"),
            {
                "holdout_data_access": False,
                "holdout_label_access": False,
                "holdout_result_access": False,
                "statistical_analysis_execution": False,
                "network_access": False,
                "connector_execution": False,
                "data_retrieval": False,
                "data_download": False,
                "sampling": False,
                "planner_execution": False,
                "evaluation_execution": False,
            },
        )

    def test_red_08_b4_isolation_and_sealed_holdout_are_unchanged(self) -> None:
        """RED-08: B8 contracts inherit B4 isolation without unsealing data."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        b4 = load_yaml(
            CONFIG_DIR / "part-b-baseline-isolation-policy-v0.8.yaml"
        )
        isolation = policy["partition_isolation"]
        self.assertEqual(
            isolation["b4_isolation_policy_hash"],
            b4["hash"],
        )
        self.assertEqual(isolation["partition_order"], b4["partition_order"])
        self.assertEqual(isolation["active_partition"], "HOLDOUT")
        self.assertIs(isolation["mutually_disjoint"], True)
        self.assertIs(isolation["holdout_visible_before_final_freeze"], False)
        self.assertIs(isolation["evaluation_feedback_to_training"], False)
        self.assertIs(isolation["holdout_feedback_to_any_model"], False)
        self.assertIs(isolation["contract_unseals_holdout"], False)

    def test_red_09_pb_si_006_remains_open(self) -> None:
        """RED-09: B8 cannot select or authorize an external holdout source."""
        b8_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b8-spec-issues.md"
        ).read_text(encoding="utf-8")
        b0_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b0-spec-issues.md"
        ).read_text(encoding="utf-8")
        combined = (b0_issue + "\n" + b8_issue).upper()
        self.assertIn("PB-SI-006", combined)
        self.assertIn("OPEN", combined)
        self.assertIn("PER-SOURCE", combined)
        self.assertIn("SEPARATE AUTHORIZATION", combined)
        self.assertNotIn("PB-SI-006: CLOSED", combined)

    def test_red_10_pb_b5_si_001_remains_open(self) -> None:
        """RED-10: B8 cannot admit or execute a Planner implementation."""
        b8_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b8-spec-issues.md"
        ).read_text(encoding="utf-8")
        b5_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b5-spec-issues.md"
        ).read_text(encoding="utf-8")
        combined = (b5_issue + "\n" + b8_issue).upper()
        self.assertIn("PB-B5-SI-001", combined)
        self.assertIn("OPEN", combined)
        self.assertIn("NOT ESTABLISHED", combined)
        self.assertIn("LEGACY M3* EXECUTION AUTHORITY: NONE", combined)
        self.assertNotIn("PLANNER EXECUTION AUTHORITY: GRANTED", combined)

    def test_red_11_examples_contain_no_holdout_or_access_material(self) -> None:
        """RED-11: inert examples carry no labels, results, source or secret."""
        url_pattern = re.compile(r"(?:https?|s3|gs|ftp)://", re.IGNORECASE)
        path_pattern = re.compile(
            r"(?:[a-z]:\\\\|/var/|/home/|/data/|09-experiments/)",
            re.IGNORECASE,
        )
        forbidden_exact_keys = {
            "labels",
            "outcomes",
            "results",
            "rankings",
            "scores",
            "p_values",
            "effect_estimates",
            "url",
            "uri",
            "endpoint",
            "host",
            "port",
            "credential",
            "credentials",
            "token",
            "secret",
            "api_key",
            "query",
            "command",
            "download_path",
            "dataset_path",
            "payload",
        }
        for name, path in CONFIG_PATHS.items():
            with self.subTest(artifact=name):
                document = load_yaml(path)
                for key, value in walk(document):
                    self.assertNotIn(key.lower(), forbidden_exact_keys)
                    if isinstance(value, str):
                        self.assertIsNone(url_pattern.search(value))
                        self.assertIsNone(path_pattern.search(value))

    def test_red_12_b8_proves_contract_consistency_only(self) -> None:
        """RED-12: B8 validation is not analysis or external validity."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(
            manifest.get("proof_boundary"),
            {
                "contract_consistency_only": True,
                "preregistration_contract_validated": True,
                "holdout_split_validated": False,
                "holdout_data_access": False,
                "holdout_label_access": False,
                "holdout_result_access": False,
                "statistical_analysis_execution": False,
                "external_validity": False,
                "performance_validity": False,
                "superiority_claim": False,
            },
        )
        text = "\n".join(
            require_file(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        ).upper()
        for required in (
            "B8_HOLDOUT_ANALYSIS",
            "CONTRACT ONLY",
            "CONTRACT_CONSISTENCY_ONLY",
            "NO HOLDOUT LABEL",
            "NO HOLDOUT RESULT",
            "NO STATISTICAL EXECUTION",
            "PB-SI-006",
            "PB-B5-SI-001",
            "B9",
            "CERTIFIED_STOP",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
