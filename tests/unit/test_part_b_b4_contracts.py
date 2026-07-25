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
    "preregistration": (
        SCHEMA_DIR / "part-b-baseline-preregistration.schema.json"
    ),
    "isolation_policy": (
        SCHEMA_DIR / "part-b-baseline-isolation-policy.schema.json"
    ),
    "manifest": SCHEMA_DIR / "part-b-b4-manifest.schema.json",
}
CONFIG_PATHS = {
    "preregistration": (
        CONFIG_DIR / "part-b-baseline-preregistration-v0.8.yaml"
    ),
    "isolation_policy": (
        CONFIG_DIR / "part-b-baseline-isolation-policy-v0.8.yaml"
    ),
    "manifest": CONFIG_DIR / "part-b-b4-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b4-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-b4-baseline-preregistration-v0.8.md",
    ROOT / "contracts" / "part-b-b4-baseline-isolation-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b0-spec-issues.md",
    ROOT / "src" / "scope" / "part-b-b4-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b4-implementation-plan-v0.8-20260723.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)

FROZEN_BINDINGS = {
    "b2_manifest_hash": (
        "sha256:6d6f67d9722eff1b2e1aa75277b0c390"
        "dc485751067728a347ae89c77f83faed"
    ),
    "pb_si_003_decision_hash": (
        "sha256:1a9668ef8c968c968e14587778d261b023"
        "dff60a0234e4e67251051ec07e5919"
    ),
    "b3_cost_instrumentation_policy_hash": (
        "sha256:c64865166be067da37a6f4f5d745ce8dc"
        "0421dc342d88589c9bbce6142eb3278"
    ),
    "b3_manifest_hash": (
        "sha256:9403004d25c1428beeb85f04c6d65eeb0"
        "2759d6881ede67390a2d97f2b9c82fb"
    ),
}
FROZEN_PATHS = {
    "b2_manifest_hash": CONFIG_DIR / "part-b-b2-manifest-v0.8.yaml",
    "pb_si_003_decision_hash": (
        CONFIG_DIR / "part-b-b2-world-pair-delta-decision-v0.8.yaml"
    ),
    "b3_cost_instrumentation_policy_hash": (
        CONFIG_DIR / "part-b-cost-instrumentation-policy-v0.8.yaml"
    ),
    "b3_manifest_hash": CONFIG_DIR / "part-b-b3-manifest-v0.8.yaml",
}


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B4 artifact: {path.relative_to(ROOT)}"
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


class PartBB4ContractTests(unittest.TestCase):
    def test_red_01_required_contract_artifacts_exist(self) -> None:
        """RED-01: three schemas and three contract configs must exist."""
        for path in (*SCHEMA_PATHS.values(), *CONFIG_PATHS.values()):
            with self.subTest(path=path.relative_to(ROOT)):
                require_file(path)

    def test_red_02_schemas_are_draft_2020_12_and_fail_closed(self) -> None:
        """RED-02: schemas reject unknown fields and authority expansion."""
        schemas = {
            name: load_json(path) for name, path in SCHEMA_PATHS.items()
        }
        configs = {
            name: load_yaml(path) for name, path in CONFIG_PATHS.items()
        }

        for name, schema in schemas.items():
            with self.subTest(schema=name):
                self.assertEqual(
                    schema["$schema"],
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertIs(schema.get("additionalProperties"), False)
                Draft202012Validator.check_schema(schema)
                self.assertEqual(validate(configs[name], schema), [])

                unknown = deepcopy(configs[name])
                unknown["unexpected_authority"] = True
                self.assertTrue(validate(unknown, schema))

        nested_unknown = deepcopy(configs["manifest"])
        nested_unknown["bindings"]["unexpected_hash"] = "sha256:" + ("0" * 64)
        self.assertTrue(validate(nested_unknown, schemas["manifest"]))

        for field in (
            "execution_authority",
            "sampling_authority",
            "planner_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            expanded = deepcopy(configs["manifest"])
            expanded[field] = True
            with self.subTest(authority=field):
                self.assertTrue(validate(expanded, schemas["manifest"]))

        expanded = deepcopy(configs["manifest"])
        expanded["stop_authority"] = "B4_BASELINE_PREREG"
        self.assertTrue(validate(expanded, schemas["manifest"]))

    def test_red_09_manifest_has_no_runtime_or_claim_authority(self) -> None:
        """RED-09: B4 is preregistration-only; B5-B9 remain closed."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest["status"], "B4_CONTRACT_ONLY")
        self.assertEqual(
            manifest["authorized_slice"],
            "B4_BASELINE_PREREG",
        )
        for field in (
            "execution_authority",
            "sampling_authority",
            "planner_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            with self.subTest(authority=field):
                self.assertIs(manifest[field], False)
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(manifest["llm_integration"], "FORBIDDEN")
        self.assertEqual(
            manifest["closed_slices"],
            ["B5", "B6", "B7", "B8", "B9"],
        )

    def test_red_10_manifest_preserves_all_frozen_b2_b3_hashes(self) -> None:
        """RED-10: B4 references B2/B3 without changing frozen hashes."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        for binding_name, expected_hash in FROZEN_BINDINGS.items():
            with self.subTest(binding=binding_name):
                frozen = load_yaml(FROZEN_PATHS[binding_name])
                self.assertEqual(frozen["hash"], expected_hash)
                self.assertEqual(
                    manifest["bindings"][binding_name],
                    expected_hash,
                )

        preregistration = load_yaml(CONFIG_PATHS["preregistration"])
        isolation = load_yaml(CONFIG_PATHS["isolation_policy"])
        self.assertEqual(
            manifest["bindings"]["baseline_preregistration_hash"],
            preregistration["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["baseline_isolation_policy_hash"],
            isolation["hash"],
        )

    def test_red_11_hashes_replay_and_tampering_fails_closed(self) -> None:
        """RED-11: missing, wrong and stale hashes cannot pass validation."""
        schemas = {
            name: load_json(path) for name, path in SCHEMA_PATHS.items()
        }
        configs = {
            name: load_yaml(path) for name, path in CONFIG_PATHS.items()
        }

        for name, artifact in configs.items():
            with self.subTest(artifact=name, condition="replay"):
                self.assertEqual(
                    artifact["hash"],
                    canonical_document_hash(artifact),
                )

            missing_hash = deepcopy(artifact)
            missing_hash.pop("hash")
            with self.subTest(artifact=name, condition="missing_hash"):
                self.assertTrue(validate(missing_hash, schemas[name]))

            wrong_hash = deepcopy(artifact)
            wrong_hash["hash"] = "sha256:" + ("0" * 64)
            with self.subTest(artifact=name, condition="wrong_hash"):
                self.assertNotEqual(
                    wrong_hash["hash"],
                    canonical_document_hash(wrong_hash),
                )

            stale_hash = deepcopy(artifact)
            stale_hash["status"] = f"{artifact['status']}_TAMPERED"
            with self.subTest(artifact=name, condition="tampered_artifact"):
                self.assertNotEqual(
                    stale_hash["hash"],
                    canonical_document_hash(stale_hash),
                )

    def test_red_12_documents_preserve_the_b4_boundary(self) -> None:
        """RED-12: docs forbid execution, sampling and authority expansion."""
        texts: dict[Path, str] = {}
        for path in DOCUMENT_PATHS:
            texts[path] = require_file(path).read_text(encoding="utf-8")

        boundary = texts[
            ROOT / "contracts" / "part-b-b4-boundary-v0.8.md"
        ]
        for token in (
            "B4_BASELINE_PREREG",
            "execution_authority=false",
            "sampling_authority=false",
            "planner_authority=false",
            "scalarization_authority=false",
            "performance_claim_authority=false",
            "stop_authority=NONE",
            "NO_BASELINE_EXECUTION",
            "NO_DATA_ACQUISITION",
            "NO_CONNECTOR_DOWNLOAD",
            "NO_STOCHASTIC_SAMPLER",
        ):
            with self.subTest(boundary_token=token):
                self.assertIn(token, boundary)

        corpus = "\n".join(texts.values())
        for token in (
            "ORACLE_EVALUATION_ONLY",
            "PB-SI-005",
            "B5",
            "B6",
            "B7",
            "B8",
            "B9",
            "LLM",
            "09-experiments",
            "CERTIFIED_STOP",
        ):
            with self.subTest(corpus_token=token):
                self.assertIn(token, corpus)


if __name__ == "__main__":
    unittest.main()
